from __future__ import annotations
from .base import BaseAdapter, AdapterResult

class GreenhouseAdapter(BaseAdapter):
    name = "Greenhouse"
    def fetch(self, employer: dict) -> AdapterResult:
        token = employer["ats_board_token"]
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        data = self.get_json(url)
        jobs=[]
        for j in data.get("jobs",[]):
            jobs.append({
                "ats_id": str(j.get("id")),
                "title": j.get("title") or "",
                "location": (j.get("location") or {}).get("name") or "Unknown",
                "description": j.get("content") or "",
                "date_posted": None,
                "source_updated_at": j.get("updated_at"),
                "apply_url": j.get("absolute_url") or "",
                "source_url": j.get("absolute_url") or url,
                "metadata": j.get("metadata") or [],
                "departments": [d.get("name") for d in j.get("departments",[]) if d.get("name")],
                "offices": [o.get("name") for o in j.get("offices",[]) if o.get("name")],
            })
        return AdapterResult(jobs=jobs, source_url=url)
