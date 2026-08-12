from __future__ import annotations
import json, os, sys, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from adapters import ADAPTERS
from classify import is_relevant, category, gpa_policy, grad_years, work_auth, career_seed, clean_text

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; EMPLOYERS=DATA/'employers.json'; JOBS=DATA/'jobs.json'; HEALTH=DATA/'monitor_health.json'; STATE=DATA/'monitor_state.json'; ALERTS=DATA/'pending_alerts.json'
NOW=datetime.now(timezone.utc)

def load(path,default):
    try:return json.loads(path.read_text())
    except Exception:return default

def dump(path,obj): path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n")
def iso(dt=NOW): return dt.isoformat().replace('+00:00','Z')
def parse_dt(x):
    if not x:return None
    try:return datetime.fromisoformat(x.replace('Z','+00:00'))
    except:return None

def due(emp,state):
    last=parse_dt((state.get(emp['id']) or {}).get('last_check'))
    return not last or NOW-last>=timedelta(minutes=int(emp.get('check_interval_minutes',180)))
def stable_id(company,raw):
    key='|'.join([company,str(raw.get('ats_id') or ''),raw.get('title',''),raw.get('location',''),raw.get('apply_url','')])
    return hashlib.sha256(key.encode()).hexdigest()[:24]
def server_priority(job):
    # Deliberately profile-light for alerting. Full profile-aware score is recalculated locally in the browser.
    gpa=float(os.getenv('PROFILE_GPA') or '2.81'); fit=58; gp=job.get('gpa',{})
    if gp.get('type')=='hard' and gp.get('minimum') is not None: fit += 8 if gpa>=float(gp['minimum']) else -42
    elif gp.get('type')=='preferred' and gp.get('minimum') is not None: fit += 4 if gpa>=float(gp['minimum']) else -8
    elif gp.get('type')=='none': fit+=8
    loc=(job.get('location') or '').lower(); bonus=12 if 'new york' in loc else 8 if 'seattle' in loc else 5 if 'boston' in loc else 0
    career=job.get('career_value_seed',65)
    return max(0,min(100,round(fit*.46+career*.36+bonus+6)))

def main(force=False):
    employers=load(EMPLOYERS,[]); existing=load(JOBS,[]); state=load(STATE,{}); prev_health=load(HEALTH,{})
    byid={j['id']:j for j in existing}; seen_cycle=set(); sources=[]; new_ids=[]
    # retain manual/not-configured health summaries without pretending checks happened
    for emp in employers:
        adapter_cls=ADAPTERS.get(emp.get('ats'))
        if not adapter_cls or not (emp.get('ats_board_token') or emp.get('ats_site')):
            continue
        st=state.get(emp['id'],{})
        if not force and not due(emp,state):
            sources.append({"company":emp['company'],"ats":emp.get('ats'),"last_check":st.get('last_check'),"last_success":st.get('last_success'),"ok":st.get('ok',False),"error":st.get('error',''),"skipped_not_due":True})
            continue
        record={"company":emp['company'],"ats":emp.get('ats'),"last_check":iso(),"last_success":st.get('last_success'),"ok":False,"error":""}
        try:
            result=adapter_cls().fetch(emp); raw_relevant=[]
            for raw in result.jobs:
                desc=clean_text(raw.get('description',''))
                if not is_relevant(raw.get('title',''),desc,raw.get('commitment','')): continue
                jid=stable_id(emp['company'],raw); seen_cycle.add(jid); cat=category(raw.get('title',''),desc)
                job={
                  "id":jid,"company":emp['company'],"employer_id":emp['id'],"ats":emp.get('ats'),"ats_id":raw.get('ats_id'),
                  "title":raw.get('title',''),"category":cat,"description":desc,"location":raw.get('location') or 'Unknown',
                  "work_arrangement":"Unknown","internship_year":None,"eligible_graduation_years":grad_years(desc),
                  "date_posted":raw.get('date_posted'),"first_detected_at":byid.get(jid,{}).get('first_detected_at') or iso(),"last_seen_at":iso(),
                  "deadline":None,"apply_url":raw.get('apply_url'),"source_url":raw.get('source_url') or result.source_url,"salary":None,
                  "gpa":gpa_policy(desc),"work_authorization":work_auth(desc),"required_qualifications":"See original posting",
                  "preferred_qualifications":"See original posting","status":"Open","career_value_seed":career_seed(cat,desc),"monitoring_verified_at":iso()
                }
                if jid not in byid:new_ids.append(jid)
                byid[jid]=job;raw_relevant.append(job)
            record.update({"ok":True,"last_success":iso(),"jobs_detected":len(raw_relevant),"source_url":result.source_url})
            state[emp['id']]={"last_check":iso(),"last_success":iso(),"ok":True,"error":"","jobs_detected":len(raw_relevant),"source_url":result.source_url}
            emp['monitoring_status']='Configured + Healthy'
        except Exception as exc:
            record['error']=f"{type(exc).__name__}: {exc}"[:600]
            state[emp['id']]={"last_check":iso(),"last_success":st.get('last_success'),"ok":False,"error":record['error'],"jobs_detected":st.get('jobs_detected',0)}
            emp['monitoring_status']='Configured + Failing'
        sources.append(record)
    # Mark jobs from successfully checked employers removed only when that employer was actually checked successfully.
    successful={s['company'] for s in sources if s.get('ok') and not s.get('skipped_not_due')}
    for j in byid.values():
        if j['company'] in successful and j['id'] not in seen_cycle and j.get('status')=='Open':
            j['status']='Removed';j['removed_at']=iso()
    jobs=sorted(byid.values(),key=lambda j:j.get('first_detected_at') or '',reverse=True)
    alerts=[];threshold=int(os.getenv('ALERT_THRESHOLD','75'))
    for jid in new_ids:
        job=byid[jid];score=server_priority(job);job['server_alert_priority']=score
        if score>=threshold:alerts.append({"id":jid,"company":job['company'],"title":job['title'],"location":job['location'],"priority":score,"career_value":job['career_value_seed'],"detected":job['first_detected_at'],"deadline":job.get('deadline'),"apply_url":job['apply_url']})
    monitored=[e for e in employers if e.get('ats') in ADAPTERS and (e.get('ats_board_token') or e.get('ats_site'))]
    manual=[e for e in employers if e.get('monitoring_status')=='Manual Monitoring']
    failing=sum(1 for s in sources if not s.get('ok') and not s.get('skipped_not_due'))
    healthy=sum(1 for e in monitored if (state.get(e['id']) or {}).get('ok'))
    health={"last_cycle":iso(),"total_employers":len(employers),"actively_monitored":len(monitored),"healthy":healthy,"failing":failing,"manual":len(manual),"not_configured":len(employers)-len(monitored)-len(manual),"new_jobs_today":len(new_ids),"sources":sources}
    dump(EMPLOYERS,employers);dump(JOBS,jobs);dump(HEALTH,health);dump(STATE,state);dump(ALERTS,alerts)
    print(json.dumps({"checked":sum(1 for s in sources if not s.get('skipped_not_due')),"new_jobs":len(new_ids),"alerts":len(alerts),"healthy":healthy,"failing":failing}))
    return 1 if failing and not healthy else 0

if __name__=='__main__':
    sys.exit(main(force='--force' in sys.argv))
