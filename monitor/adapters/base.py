from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import requests

@dataclass
class AdapterResult:
    jobs: list[dict[str, Any]]
    source_url: str

class BaseAdapter:
    name = "base"
    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent":"FinanceInternshipCommandCenter/1.0 (+personal student job monitor; respectful rate limits)"})
    def get_json(self, url: str):
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
    def fetch(self, employer: dict) -> AdapterResult:
        raise NotImplementedError
