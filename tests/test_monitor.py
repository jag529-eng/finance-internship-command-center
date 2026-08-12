import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'monitor'))
from classify import is_relevant, category, gpa_policy, grad_years
from adapters.greenhouse import GreenhouseAdapter

class FixtureGreenhouse(GreenhouseAdapter):
    def get_json(self,url):
        return json.loads((ROOT/'tests/fixtures/greenhouse_point72_sample.json').read_text())

def test_greenhouse_adapter():
    r=FixtureGreenhouse().fetch({'ats_board_token':'point72'})
    assert len(r.jobs)==1
    assert r.jobs[0]['ats_id']=='900001'
    assert 'New York' in r.jobs[0]['location']

def test_classification_and_gpa():
    j=FixtureGreenhouse().fetch({'ats_board_token':'point72'}).jobs[0]
    assert is_relevant(j['title'],j['description'])
    assert category(j['title'],j['description']) in {'Asset Management','Equity Research','Other Finance'}
    assert gpa_policy(j['description'])['type']=='none'

def test_hard_gpa_only_when_explicit():
    assert gpa_policy('Applicants must have a minimum GPA of 3.2.')['type']=='hard'
    assert gpa_policy('A 3.2 GPA is preferred.')['type']=='preferred'
    assert gpa_policy('Strong academic performance expected.')['type']=='none'
