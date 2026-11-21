"""Configurable reviewed meeting metrics, immutable daily close and workbook payloads.

No model calls, email access, notifications or tenant authentication occur here.
"""
import argparse
import json
import math
import re
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from .core import Store, digest, instant, timestamp, utcnow


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def validate_profile(p):
    if p.get('version') != 2 or p.get('datasetMode') not in ('synthetic', 'operational'):
        raise ValueError('Use readiness version 2 and a valid datasetMode.')
    ZoneInfo(p['timezone'])
    datetime.strptime(p['closingTime'], '%H:%M')
    if not isinstance(p['transcriptDelayMinutes'], int) or not 0 <= p['transcriptDelayMinutes'] <= 1440:
        raise ValueError('Invalid transcript delay.')
    for group in ('meetings', 'fields'):
        keys = [x['key'] for x in p[group]]
        if len(keys) != len(set(keys)) or not all(re.fullmatch(r'[a-z][a-z0-9_]{0,47}', k) for k in keys):
            raise ValueError('Invalid or duplicate keys in ' + group)
    for m in p['meetings']:
        datetime.strptime(m['end'], '%H:%M')
        if not set(m['weekdays']) <= set(range(7)) or not m['weekdays']:
            raise ValueError('Weekdays use Monday=0 through Sunday=6.')
        if not set(m['fields']) <= {f['key'] for f in p['fields']}:
            raise ValueError('Meeting references unknown fields.')
    for f in p['fields']:
        if f['type'] not in ('number', 'text', 'boolean'):
            raise ValueError('Invalid field type.')
    if len(p['fields']) > 100:
        raise ValueError('Maximum 100 configured fields per workbook.')
    return p


def open_store(db, p):
    # Share the proven immutable store without changing the version-1 pipeline.
    cfg = dict(version=1, datasetMode=p['datasetMode'], siteLabel=p['siteLabel'],
               meetings=[], signals=[], outcomes=[], rules=[], minimumHistory=8,
               historyDays=90, watchRate=.6)
    s = Store(db, cfg)
    owner = s.db.execute("SELECT value FROM metadata WHERE key='readinessSite'").fetchone()
    if owner and owner[0] != p['siteKey']:
        s.close()
        raise ValueError('Database belongs to a different site.')
    with s.db:
        s.db.execute("INSERT OR IGNORE INTO metadata VALUES ('readinessSite',?)", (p['siteKey'],))
    return s


def evidence(items, sources):
    if not items:
        raise ValueError('Every metric and issue requires evidence.')
    available = {s['id'] for s in sources if s['status'] == 'available'}
    if any(e.get('sourceId') not in available or not str(e.get('locator', '')).strip() for e in items):
        raise ValueError('Evidence must identify an available source and cue/record locator.')


def ingest(s, p, value, now=None):
    r = deepcopy(value)
    now = timestamp(now or utcnow())
    if r.get('version') != 2 or not str(r.get('id', '')).strip():
        raise ValueError('Reviewed record needs version 2 and a stable ID.')
    if not r.get('reviewerRole') or r['reviewerRole'] == 'REPLACE_WITH_ROLE':
        raise ValueError('A reviewer must confirm the record before intake.')
    day = date.fromisoformat(r['date'])
    meeting = next((m for m in p['meetings'] if m['key'] == r['meetingKey']), None)
    if not meeting:
        raise ValueError('Unknown meeting key.')
    for key in ('startsAt', 'endsAt'):
        instant(r[key])
    if instant(r['endsAt']) < instant(r['startsAt']) or instant(r['endsAt']) > instant(now):
        raise ValueError('Meeting must have ended before intake.')
    if instant(r['startsAt']).astimezone(ZoneInfo(p['timezone'])).date() != day:
        raise ValueError('Meeting date does not match site local start date.')
    if r.get('status') not in ('processed', 'unavailable', 'not_held'):
        raise ValueError('Use processed, unavailable or not_held.')
    if r['status'] != 'processed' and (r.get('metrics') or r.get('issues') or not r.get('statusNote')):
        raise ValueError('Unavailable/not-held records require a reason and no extracted facts.')
    sources = r.get('sources', [])
    if len({x['id'] for x in sources}) != len(sources):
        raise ValueError('Duplicate source IDs.')
    for source in sources:
        if source['status'] not in ('available', 'pending', 'denied', 'missing', 'not_applicable'):
            raise ValueError('Invalid source status.')
        if source['status'] == 'available' and not source.get('reference'):
            raise ValueError('Available sources need a private evidence reference.')
    fields = {f['key']: f for f in p['fields']}
    metrics = r.get('metrics', [])
    if len({(m['field'], m['appliesToDate']) for m in metrics}) != len(metrics):
        raise ValueError('Duplicate field/date in one reviewed record.')
    for m in metrics:
        if m['field'] not in meeting['fields']:
            raise ValueError('Metric is not mapped to this meeting.')
        f, v = fields[m['field']], m['value']
        if f['type'] == 'number' and (type(v) not in (int, float) or not math.isfinite(v)):
            raise ValueError('Numeric metrics require finite numbers, not missing-data text.')
        if f['type'] == 'text' and not isinstance(v, str) or f['type'] == 'boolean' and type(v) is not bool:
            raise ValueError('Metric type mismatch.')
        if f['type'] == 'number' and (v < f.get('min', -math.inf) or v > f.get('max', math.inf)):
            raise ValueError('Metric outside configured bounds.')
        date.fromisoformat(m['appliesToDate'])
        if instant(m['observedAt']) > instant(now):
            raise ValueError('Observation is in the future.')
        evidence(m['evidence'], sources)
    old_issues = {i['issueId']: i for old in s.records('readiness') for i in old.get('issues', [])}
    if len({i['issueId'] for i in r.get('issues', [])}) != len(r.get('issues', [])):
        raise ValueError('Duplicate issue in one record.')
    for i in r.get('issues', []):
        if not i.get('issueId') or not i.get('summary') or i['severity'] not in ('HIGH', 'MEDIUM', 'LOW', 'UNKNOWN') or i['state'] not in ('active', 'cleared', 'unknown'):
            raise ValueError('Invalid issue.')
        if date.fromisoformat(i['eventDate']) > day:
            raise ValueError('Event date is when the concern arose, not a future staffing date.')
        if i['issueId'] in old_issues and i['eventDate'] != old_issues[i['issueId']]['eventDate']:
            raise ValueError('An existing issue cannot reset its event date.')
        for key in ('owner', 'action', 'due'):
            i.setdefault(key, 'Not stated')
        evidence(i['evidence'], sources)
    prior = next((x for x in s.records('readiness') if x['id'] == r['id']), None)
    if prior:
        if {k: v for k, v in prior.items() if k not in ('receivedAt', 'profileHash')} != r:
            raise ValueError('Changed record needs a new revision ID.')
        return prior
    r.update(receivedAt=now, profileHash=digest(p))
    s._put('readiness', r)
    return r


def visible(s, cutoff):
    return sorted([r for r in s.records('readiness') if instant(r['receivedAt']) <= instant(cutoff)],
                  key=lambda r: (instant(r['endsAt']), instant(r['receivedAt']), r['id']))


def current_records(s, cutoff):
    # Revision of the same meeting occurrence replaces its interpretation, not its stored evidence.
    selected = {}
    for r in sorted(visible(s, cutoff), key=lambda x: (instant(x['receivedAt']), x['id'])):
        selected[(r['date'], r['meetingKey'], timestamp(r['startsAt']))] = r
    return sorted(selected.values(), key=lambda r: (instant(r['endsAt']), instant(r['receivedAt']), r['id']))


def snapshot(s, p, day, cutoff):
    start = (date.fromisoformat(day) - timedelta(days=6)).isoformat()
    records = [r for r in current_records(s, cutoff) if r['date'] <= day]
    known, issues, peak, future = {}, {}, {}, []
    rank = {'UNKNOWN': 0, 'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
    for r in records:
        for m in r.get('metrics', []):
            item = dict(m, recordId=r['id'], meetingKey=r['meetingKey'])
            if m['appliesToDate'] > day:
                future.append(item)
                continue
            old = known.get(m['field'])
            if old is None or (m['appliesToDate'], instant(m['observedAt']), instant(r['receivedAt'])) >= (old['appliesToDate'], instant(old['observedAt']), instant(old['receivedAt'])):
                known[m['field']] = dict(item, receivedAt=r['receivedAt'])
        for i in r.get('issues', []):
            key = i['issueId']
            peak[key] = max(peak.get(key, 'UNKNOWN'), i['severity'], key=lambda x: rank[x])
            issues[key] = dict(i, recordId=r['id'], meetingKey=r['meetingKey'], updatedAt=r['endsAt'])
    seven = [dict(i, trackedSeverity=peak[k]) for k, i in issues.items()
             if start <= i['eventDate'] <= day and rank[peak[k]] >= 2]
    return dict(date=day, asOfUtc=timestamp(cutoff), metrics=known,
                sevenDayConcerns=sorted(seven, key=lambda i: (i['eventDate'], i['issueId']), reverse=True),
                openIssues=[i for i in issues.values() if i['state'] != 'cleared'],
                upcomingMetrics=future)


def expected(p, day):
    override = p.get('scheduleOverrides', {}).get(day)
    keys = override if override is not None else [m['key'] for m in p['meetings'] if date.fromisoformat(day).weekday() in m['weekdays']]
    if not set(keys) <= {m['key'] for m in p['meetings']}:
        raise ValueError('Unknown meeting in date override.')
    return [m for m in p['meetings'] if m['key'] in keys]


def close_day(s, p, day, now=None):
    existing = next((x for x in s.records('daily_close') if x['id'] == day), None)
    if existing:
        return existing
    now = timestamp(now or utcnow())
    zone = ZoneInfo(p['timezone'])
    due = datetime.fromisoformat(day + 'T' + p['closingTime']).replace(tzinfo=zone)
    records = [r for r in current_records(s, now) if r['date'] == day]
    for m in expected(p, day):
        gate = datetime.fromisoformat(day + 'T' + m['end']).replace(tzinfo=zone) + timedelta(minutes=p['transcriptDelayMinutes'])
        due = max(due, gate)
        matches = [r for r in records if r['meetingKey'] == m['key']]
        if not matches:
            raise ValueError('Closing waits for processed/unavailable/not-held record: ' + m['key'])
    for r in records:
        due = max(due, instant(r['endsAt']) + timedelta(minutes=p['transcriptDelayMinutes']))
        if r['status'] == 'processed' and any(x['status'] == 'pending' for x in r['sources']):
            raise ValueError('Closing waits for pending sources to be resolved or marked missing.')
    if instant(now) < due:
        raise ValueError('Closing time/transcript processing window has not passed.')
    snap = snapshot(s, p, day, now)
    result = dict(id=day, date=day, closedAt=now, profileHash=digest(p), snapshot=snap,
                  recordIds=[r['id'] for r in records],
                  coverage=[dict(meetingKey=r['meetingKey'], status=r['status'], note=r.get('statusNote', '')) for r in records])
    s._put('daily_close', result)
    return result


def lookback(s, p, day, schedule, cutoff):
    """Explicit dated sessions from a versioned OR block grid; no inferred surgeon identity."""
    if schedule.get('version') != 1:
        raise ValueError('Unsupported block schedule.')
    versions = sorted(schedule['versions'], key=lambda v: v['effectiveFrom'])
    for index, version in enumerate(versions):
        first, last = date.fromisoformat(version['effectiveFrom']), date.fromisoformat(version['effectiveTo'])
        if first > last or index and versions[index-1]['effectiveTo'] >= version['effectiveFrom']:
            raise ValueError('Block schedule versions overlap or have invalid effective dates.')
        for session in version['sessions']:
            if not first <= date.fromisoformat(session['date']) <= last or not session.get('surgeonKey') or not session.get('blockKey'):
                raise ValueError('Block session must have identity and a date inside its version.')
    current = [v for v in schedule['versions'] if v['effectiveFrom'] <= day <= v['effectiveTo']]
    if len(current) != 1:
        raise ValueError('Exactly one block schedule version must cover the target day.')
    sessions = [x for v in schedule['versions'] for x in v['sessions'] if v['effectiveFrom'] <= x['date'] <= v['effectiveTo']]
    targets = [x for x in current[0]['sessions'] if x['date'] == day]
    findings = []
    records = current_records(s, cutoff)
    for target in targets:
        previous = sorted([x for x in sessions if x['date'] < day and x['surgeonKey'] == target['surgeonKey']], key=lambda x: x['date'])
        d = date.fromisoformat(day)
        previous_month_end = d.replace(day=1) - timedelta(days=1)
        # Match weekday ordinal (e.g. third Friday), never silently substitute a different block.
        candidates = [x for x in previous if x['blockKey'] == target['blockKey'] and
                      x['date'][:7] == previous_month_end.strftime('%Y-%m') and
                      date.fromisoformat(x['date']).weekday() == d.weekday() and
                      (date.fromisoformat(x['date']).day - 1)//7 == (d.day - 1)//7]
        for mode, match in [('previous_session', previous[-1:] ), ('previous_month_block', candidates[-1:])]:
            for session in match:
                hits = [dict(i, recordId=r['id']) for r in records if r['date'] == session['date'] for i in r.get('issues', [])
                        if i.get('surgeonKey') == target['surgeonKey'] or i.get('blockKey') == target['blockKey']]
                findings.append(dict(mode=mode, target=target, prior=session, issues=hits,
                                     interpretation='Historical context only; no causal or predictive conclusion.'))
    return findings


def ev_text(items):
    return '; '.join(e['sourceId'] + ' @ ' + e['locator'] for e in items)


def payload(s, p, day, cutoff=None):
    cutoff = timestamp(cutoff or utcnow())
    snap = snapshot(s, p, day, cutoff)
    fields = p['fields']
    sheets = []
    def sheet(name, mode, headers, rows, keys=None):
        sheets.append(dict(name=name, mode=mode, headers=headers, rows=rows, keys=keys or []))
    metric_rows = []
    for f in fields:
        if not f.get('executive', True):
            continue
        m = snap['metrics'].get(f['key'])
        metric_rows.append([f['label'], m['value'] if m else 'Not stated', f.get('unit', ''),
                            m['appliesToDate'] if m else '', m['observedAt'] if m else '',
                            ev_text(m['evidence']) if m else 'No validated observation'])
    sheet('Executive Snapshot', 'refresh', ['Metric', 'Known value', 'Unit', 'Applies to', 'Observed at', 'Evidence'], metric_rows +
          [['', '', '', '', '', ''], ['SEVEN-DAY HIGH / MEDIUM EVENTS', '', '', '', '', ''],
           ['Event date', 'Concern', 'Severity', 'Status', 'Owner / action', 'Evidence']] +
          [[i['eventDate'], i['summary'], i['trackedSeverity'], i['state'], i['owner'] + ' / ' + i['action'], i['recordId'] + ' | ' + ev_text(i['evidence'])] for i in snap['sevenDayConcerns']])
    closed = sorted([r for r in s.records('daily_close') if instant(r['closedAt']) <= instant(cutoff)], key=lambda r:r['date'])
    # Stable field keys, not display labels, protect historical column mapping.
    headers = ['Date'] + [f['key'] for f in fields] + ['Concerns at close', 'Closed at', 'Source records', 'Metric provenance', 'Source coverage', 'Record hash']
    rows = []
    for r in closed:
        metrics = r['snapshot']['metrics']
        row = [r['date']] + [metrics[f['key']]['value'] if f['key'] in metrics else 'Not stated' for f in fields]
        row += ['; '.join(i['summary'] for i in r['snapshot']['openIssues']), r['closedAt'], '; '.join(r['recordIds']),
                json.dumps(metrics, ensure_ascii=False), json.dumps(r['coverage']), digest(r)]
        rows.append(row)
    sheet('Master Table', 'append', headers, rows, [r['date'] for r in closed])
    sheet('Hand-Off Review', 'refresh', ['Issue ID', 'Event date', 'Concern', 'Severity', 'State', 'Owner', 'Action', 'Due', 'Evidence'],
          [[i['issueId'], i['eventDate'], i['summary'], i['severity'], i['state'], i['owner'], i['action'], i['due'], i['recordId']] for i in snap['openIssues']])
    all_records = visible(s, cutoff)
    audits = [[r['id'] + ':' + x['id'], r['date'], r['meetingKey'], x['type'], x['status'], x.get('reference', ''), r['receivedAt'], r['reviewerRole']] for r in all_records for x in r['sources']]
    sheet('Source Audit Log', 'append', ['Audit ID', 'Date', 'Meeting', 'Source type', 'Status', 'Reference', 'Received', 'Reviewer'], audits, [r[0] for r in audits])
    history = [[r['id'] + ':' + i['issueId'], i['eventDate'], r['date'], r['meetingKey'], i['issueId'], i['summary'], i['severity'], i['state'], i['owner'], i['action'], ev_text(i['evidence'])] for r in all_records for i in r.get('issues', [])]
    sheet('Issue History', 'append', ['Revision key', 'Event date', 'Meeting date', 'Meeting', 'Issue ID', 'Concern', 'Severity', 'State', 'Owner', 'Action', 'Evidence'], history, [r[0] for r in history])
    for r in current_records(s, cutoff):
        name = r['date'] + ' ' + r['meetingKey'][:10] + ' ' + digest([r['meetingKey'], r['startsAt']])[:8]
        rs = [['Meeting', r['meetingKey'], r['startsAt'], r['status'], r['id'], r.get('statusNote', '')]]
        rs += [[m['field'], m['value'], m['appliesToDate'], m['observedAt'], '', ev_text(m['evidence'])] for m in r.get('metrics', [])]
        rs += [[i['issueId'], i['summary'], i['eventDate'], i['severity'] + ' / ' + i['state'], i['owner'] + ' / ' + i['action'], ev_text(i['evidence'])] for i in r.get('issues', [])]
        sheet(name[:31], 'refresh', ['Field / issue', 'Value / concern', 'Date / start', 'Observed / status', 'Record / action', 'Evidence / note'], rs)
    return dict(version=2, siteKey=p['siteKey'], siteLabel=p['siteLabel'], datasetMode=p['datasetMode'], date=day,
                asOfUtc=cutoff, profileHash=digest(p), snapshot=snap, sheets=sheets)


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--profile', default='config/readiness.example.json')
    a.add_argument('--db', default='data/readiness.sqlite')
    sub = a.add_subparsers(dest='command', required=True)
    sub.add_parser('validate')
    q = sub.add_parser('ingest'); q.add_argument('file')
    q = sub.add_parser('close'); q.add_argument('--date', required=True)
    q = sub.add_parser('export'); q.add_argument('--date', required=True); q.add_argument('--out', default='data/readiness.json'); q.add_argument('--as-of')
    q = sub.add_parser('lookback'); q.add_argument('--date', required=True); q.add_argument('--schedule', required=True)
    args = a.parse_args()
    p = validate_profile(read(args.profile))
    s = open_store(args.db, p)
    try:
        if args.command == 'validate': result = {'status': 'valid', 'siteKey': p['siteKey']}
        elif args.command == 'ingest': result = ingest(s, p, read(args.file))
        elif args.command == 'close': result = close_day(s, p, args.date)
        elif args.command == 'lookback': result = lookback(s, p, args.date, read(args.schedule), utcnow())
        else:
            result = payload(s, p, args.date, args.as_of)
            out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
            temp = out.with_suffix(out.suffix + '.tmp'); temp.write_text(json.dumps(result, indent=2), encoding='utf-8'); temp.replace(out)
            result = {'status': 'exported', 'file': str(out)}
        print(json.dumps(result, indent=2))
    finally:
        s.close()


if __name__ == '__main__':
    main()
