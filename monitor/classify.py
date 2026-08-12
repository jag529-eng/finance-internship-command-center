from __future__ import annotations
import re, html

FINANCE_TERMS = [
 "finance","financial","investment","banking","credit","wealth","asset management","equity research","valuation","transaction",
 "due diligence","treasury","fp&a","corporate development","investor relations","real estate","private equity","private credit",
 "venture capital","economic consulting","restructuring","deals advisory","strategy consulting","risk","underwriting"
]
INTERN_TERMS=["intern","internship","summer analyst","co-op","student"]
CATEGORY_RULES=[
 ("Investment Banking",["investment banking","m&a advisory","mergers & acquisitions","capital markets"]),
 ("Private Credit",["private credit","direct lending"]),("Private Equity",["private equity"]),("Venture Capital",["venture capital"]),
 ("Wealth Management",["wealth management","private wealth"]),("Asset Management",["asset management","investment management","investment analyst","public markets"]),
 ("Equity Research",["equity research","investment research","fundamental research"]),("Valuation",["valuation"]),
 ("Transaction Advisory",["transaction advisory","financial due diligence","deals advisory"]),("Restructuring",["restructuring"]),
 ("Corporate Development",["corporate development"]),("FP&A",["fp&a","financial planning"]),("Treasury",["treasury"]),
 ("Corporate Finance",["corporate finance","finance intern","financial analyst"]),("Economic Consulting",["economic consulting"]),
 ("Financial Consulting",["financial consulting","consulting intern"]),("Credit Analysis",["credit analyst","credit analysis","underwriting"]),
 ("Real Estate Finance",["real estate finance","real estate investment"]),("Investor Relations",["investor relations"]),("Risk",["risk"]),
]

def clean_text(s:str)->str:
    return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(s or ""))).strip()

def is_relevant(title:str, description:str, commitment:str="")->bool:
    text=f"{title} {description} {commitment}".lower()
    return any(t in text for t in INTERN_TERMS) and any(t in text for t in FINANCE_TERMS)

def category(title:str, description:str)->str:
    text=f"{title} {description}".lower()
    for cat,terms in CATEGORY_RULES:
        if any(t in text for t in terms): return cat
    return "Other Finance"

def gpa_policy(description:str)->dict:
    text=clean_text(description).lower()
    # Only record a numeric policy when GPA language and a nearby number are actually present.
    patterns=[
      ("hard",r"(?:minimum|required|must have|at least)[^\.]{0,45}?gpa[^\d]{0,12}([234](?:\.\d{1,2})?)"),
      ("hard",r"gpa[^\.]{0,30}?(?:minimum|required|of at least)[^\d]{0,12}([234](?:\.\d{1,2})?)"),
      ("hard",r"([234](?:\.\d{1,2})?)[^\.]{0,12}?gpa[^\.]{0,25}?(?:required|minimum|at least)"),
      ("preferred",r"(?:preferred|preference)[^\.]{0,45}?gpa[^\d]{0,12}([234](?:\.\d{1,2})?)"),
      ("preferred",r"gpa[^\.]{0,30}?preferred[^\d]{0,12}([234](?:\.\d{1,2})?)"),
      ("preferred",r"([234](?:\.\d{1,2})?)[^\.]{0,12}?gpa[^\.]{0,25}?preferred"),
    ]
    for typ,p in patterns:
        m=re.search(p,text,re.I)
        if m:return {"type":typ,"minimum":float(m.group(1)),"evidence":m.group(0)[:120]}
    if "gpa" not in text:return {"type":"none","minimum":None,"evidence":"No GPA language detected in posting text"}
    return {"type":"unknown","minimum":None,"evidence":"GPA mentioned, but no reliable hard/preferred numeric rule parsed"}

def grad_years(description:str)->list[int]:
    text=clean_text(description)
    years=sorted({int(y) for y in re.findall(r"\b20(?:2[6-9]|3[0-5])\b",text)})
    # Years can refer to program dates, so only return a set when graduation/student language is nearby.
    if not re.search(r"graduat|class of|degree|student",text,re.I): return []
    return years[:6]

def work_auth(description:str)->str:
    text=clean_text(description).lower()
    if re.search(r"will not sponsor|no sponsorship|not provide sponsorship|without sponsorship",text): return "No sponsorship"
    if "sponsorship" in text or "work authorization" in text:return "See posting"
    return "Unknown"

def career_seed(cat:str, description:str)->int:
    base={"Investment Banking":88,"Private Credit":88,"Private Equity":90,"Venture Capital":82,"Asset Management":84,"Equity Research":84,"Valuation":76,"Transaction Advisory":80,"Restructuring":88,"Corporate Development":83,"Corporate Finance":72,"FP&A":68,"Treasury":65,"Wealth Management":70,"Financial Consulting":76,"Economic Consulting":80,"Credit Analysis":74,"Real Estate Finance":75}.get(cat,65)
    text=clean_text(description).lower()
    for term in ["financial modeling","valuation","transaction","deal execution","underwriting","investment research","client exposure"]:
        if term in text: base+=2
    return max(0,min(100,base))
