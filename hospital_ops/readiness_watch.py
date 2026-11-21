"""Single-writer local readiness worker. Cloud connectors remain tenant configured."""
import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from .readiness import read, validate_profile, open_store, ingest, close_day, payload


def tick(s,p,inbox,out,now=None):
    now=now or datetime.now(ZoneInfo(p['timezone'])).isoformat()
    day=datetime.fromisoformat(now).astimezone(ZoneInfo(p['timezone'])).date()
    errors=[]
    for f in sorted(Path(inbox).glob('*.readiness.json')):
        try:
            if f.stat().st_size>2_000_000: raise ValueError('Intake file too large.')
            ingest(s,p,read(f),now)
        except (ValueError,KeyError,TypeError,OSError) as e: errors.append({'file':f.name,'error':str(e)})
    closing=[]
    # Explicit two-day catch-up only. Older dates require an operator close command.
    for d in (day-timedelta(days=1),day):
        try: close_day(s,p,d.isoformat(),now)
        except ValueError as e: closing.append({'date':d.isoformat(),'status':'waiting','reason':str(e)})
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for name,data in [('readiness.json',payload(s,p,day.isoformat(),now)),('readiness-status.json',dict(errors=errors,closing=closing))]:
        tmp=out/(name+'.tmp');tmp.write_text(json.dumps(data,indent=2),encoding='utf-8');tmp.replace(out/name)
    return dict(errors=errors,closing=closing)


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--profile',default='config/readiness.example.json');a.add_argument('--db',default='data/readiness.sqlite')
    a.add_argument('--inbox',required=True);a.add_argument('--out',required=True);a.add_argument('--interval',type=int,default=60);a.add_argument('--once',action='store_true')
    x=a.parse_args();p=validate_profile(read(x.profile));s=open_store(x.db,p)
    Path(x.inbox).mkdir(parents=True,exist_ok=True)
    try:
        while True:
            result=tick(s,p,x.inbox,x.out)
            print(json.dumps(result),flush=True)
            if x.once: break
            time.sleep(max(10,x.interval))
    except KeyboardInterrupt: pass
    finally: s.close()


if __name__=='__main__':main()
