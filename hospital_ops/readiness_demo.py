"""Reproducible synthetic readiness example, isolated from operational records."""
import json
from copy import deepcopy
from pathlib import Path
from .readiness import read,open_store,ingest,close_day,payload,expected


def create_demo(out='data/readiness-demo'):
    root=Path(__file__).resolve().parents[1];out=Path(out);out.mkdir(parents=True,exist_ok=True)
    p=read(root/'examples/readiness-profile.json')
    s=open_store(out/'readiness.sqlite',p)
    try:
        for day in ('2027-01-21','2027-01-22'):
            for m in expected(p,day):
                end=m['end'];hour,minute=map(int,end.split(':'));start=f'{hour:02d}:{max(0,minute-15):02d}'
                r=dict(version=2,id=day+'-'+m['key'],date=day,meetingKey=m['key'],startsAt=day+'T'+start+':00-05:00',endsAt=day+'T'+end+':00-05:00',status='processed',reviewerRole='Synthetic reviewer',sources=[dict(id='synthetic-source',type='transcript',status='available',reference='Synthetic fixture, not an operational source')],metrics=[],issues=[])
                ev=[dict(sourceId='synthetic-source',locator='Synthetic cue 1')]
                r['metrics']=[dict(field='census',value=250+(day.endswith('22'))*6,observedAt=r['endsAt'],appliesToDate=day,evidence=ev)]
                if m['key']=='plan_am':
                    r['metrics'].append(dict(field='or_cases',value=28,observedAt=r['endsAt'],appliesToDate=day,evidence=ev))
                    r['issues']=[dict(issueId='example-coverage',eventDate='2027-01-21',summary='Coverage concern documented for receiving unit.',severity='HIGH',state='active',owner='Unit lead',action='Confirm coverage',due='Next huddle',evidence=ev)]
                if day=='2027-01-22' and m['key']=='plan_pm':
                    r['issues']=[dict(issueId='example-coverage',eventDate='2027-01-21',summary='Coverage confirmed; earlier concern resolved.',severity='HIGH',state='cleared',owner='Unit lead',action='No further action stated',due='Completed',evidence=ev)]
                ingest(s,p,r,day+'T23:01:00-05:00')
            close_day(s,p,day,day+'T23:05:00-05:00')
        result=payload(s,p,'2027-01-22','2027-01-22T23:10:00-05:00')
        (out/'readiness.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        (out/'profile.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
        return str(out/'readiness.json')
    finally:s.close()


if __name__=='__main__': print(create_demo())
