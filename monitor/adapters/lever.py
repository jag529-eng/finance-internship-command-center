from __future__ import annotations
from .base import BaseAdapter, AdapterResult

class LeverAdapter(BaseAdapter):
    name = "Lever"
    def fetch(self, employer: dict) -> AdapterResult:
        site = employer["ats_site"]
        url = f"https://api.lever.co/v0/postings/{site}?mode=json"
        data = self.get_json(url)
        jobs=[]
        for j in data:
            lists=j.get("lists") or []
            desc="\n".join([j.get("descriptionPlain") or j.get("description") or ""]+[f"{x.get('text','')}: {x.get('content','')}" for x in lists])
            cats=j.get("categories") or {}
            loc=cats.get("location") or cats.get("allLocations") or "Unknown"
            if isinstance(loc,list): loc="; ".join(loc)
            jobs.append({
                "ats_id": str(j.get("id")),"title":j.get("text") or "","location":loc,"description":desc,
                "date_posted": None,"apply_url":j.get("applyUrl") or j.get("hostedUrl") or "","source_url":j.get("hostedUrl") or url,
                "departments":[cats.get("team")] if cats.get("team") else [],"commitment":cats.get("commitment") or ""
            })
        return AdapterResult(jobs=jobs, source_url=url)
