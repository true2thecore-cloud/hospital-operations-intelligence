"""Generate an entirely synthetic, reproducible demonstration."""
import json
from datetime import date, timedelta
from pathlib import Path
from .core import Store, load_config
from .render import render_report, issues_csv


def create_demo(out='data/demo'):
    root = Path(out)
    root.mkdir(parents=True, exist_ok=True)
    cfg = load_config(Path(__file__).resolve().parent.parent / 'config/site.example.json')
    cfg.update({'datasetMode': 'synthetic', 'siteLabel': 'Example Hospital'})
    (root / 'site.json').write_text(json.dumps(cfg, indent=2), encoding='utf-8')
    store = Store(root / 'operations.sqlite', cfg)
    days = []
    day = date(2027, 1, 4)
    while len(days) < 15:
        if day.weekday() < 5:
            days.append(day.isoformat())
        day += timedelta(days=1)
    for n, day in enumerate(days):
        pressured = n % 4 != 3
        delayed = pressured and n % 3 != 2
        am_text = 'A coverage gap is confirmed for the afternoon.' if pressured else 'All planned staffing coverage is confirmed.'
        bed_text = 'Two receiving beds are unavailable; PACU holds are expected.' if pressured else 'Receiving beds are available and no capacity constraint is reported.'
        vtt = f'WEBVTT\n\n00:00:01.000 --> 00:00:12.000\n<v OR Charge>{am_text}</v>\n\n00:00:13.000 --> 00:00:25.000\n<v PACU Charge>{bed_text}</v>\n\n00:00:26.000 --> 00:00:35.000\n<v SPD Lead>Required trays and late coverage are ready.</v>\n'
        mid = 'synthetic-' + day + '-am'
        store.ingest_vtt(vtt, 'plan_ahead_am', day + 'T09:00:00-05:00', 'Synthetic morning transcript', mid, day + 'T14:15:00Z')
        observations = []
        for signal, cue, summary in [('staffing_shortage', 'c1', am_text), ('bed_pressure', 'c2', bed_text), ('instrument_constraint', 'c3', 'Trays are ready.'), ('late_coverage', 'c3', 'Late coverage is confirmed.')]:
            observations.append({'signal': signal, 'state': 'active' if pressured and cue != 'c3' else 'cleared',
                'summary': summary, 'cueIds': [cue], 'issueId': 'synthetic-' + signal,
                'owner': 'OR Charge' if signal == 'staffing_shortage' else 'PACU Charge' if signal == 'bed_pressure' else 'Readiness Lead',
                'action': 'Confirm coverage and receiving plan at the afternoon meeting.' if pressured and cue != 'c3' else 'No follow-up stated.', 'due': day + ' 14:00 local'})
        store.add_review({'id': mid + '-review', 'meetingId': mid, 'reviewerRole': 'Example reviewer', 'observations': observations, 'outcomes': []}, day + 'T14:20:00Z')
        if n == len(days) - 1:
            (root / 'morning.vtt').write_text(vtt, encoding='utf-8')
            continue
        pm_text = 'A later flow delay occurred while the receiving plan was adjusted.' if delayed else 'No later flow delay occurred today.'
        pm_vtt = f'WEBVTT\n\n00:00:01.000 --> 00:00:15.000\n<v Operations Lead>{pm_text}</v>\n\n00:00:16.000 --> 00:00:25.000\n<v OR Charge>No next-day readiness issue was identified. Coverage is resolved.</v>\n'
        pid = 'synthetic-' + day + '-pm'
        store.ingest_vtt(pm_vtt, 'plan_ahead_pm', day + 'T14:00:00-05:00', 'Synthetic afternoon transcript', pid, day + 'T19:15:00Z')
        store.add_review({'id': pid + '-review', 'meetingId': pid, 'reviewerRole': 'Example reviewer', 'observations': [],
            'outcomes': [{'key': 'late_flow_delay', 'value': delayed, 'summary': pm_text, 'cueIds': ['c1']},
                         {'key': 'next_day_readiness_issue', 'value': False, 'summary': 'No readiness issue identified.', 'cueIds': ['c2']}]}, day + 'T19:20:00Z')
    day = days[-1]
    staffing = [[''] * 12 for _ in range(46)]
    staffing[0][:4] = ['EXAMPLE STAFFING', '2027-01-25', 'MONDAY', 'SYNTHETIC']
    staffing[2][:7] = ['Room', 'Start', 'RN', 'Shift', 'CST', 'Shift', 'First Assist']
    for row in range(3, 7):
        staffing[row][:7] = [str(row - 2), '07:00', 'Name RN ' + str(row - 2), '(10)', 'Name CST ' + str(row - 2), '(10)', 'Name First Assist']
    staffing[35][10:] = ['Late shift', 'Name RN']
    staffing[44][10:] = ['Late shift', 'Name CST']
    store.add_snapshot('staffing', {'version': 1, 'staffingDate': '2027-01-25', 'sourceSheet': '01-25-27', 'capturedUtc': day + 'T14:15:00Z', 'values': staffing}, day + 'T14:16:00Z')
    store.add_snapshot('handoff', {'version': 1, 'headers': ['ResponseId', 'SubmittedUtc', 'Reporter', 'CallOuts', 'EquipmentChecks', 'Comments'],
        'rows': [['example-1', day + 'T14:10:00Z', 'Charge RN', 'Yes', 'Yes', 'Coverage plan requires afternoon follow-up.']]}, day + 'T14:16:00Z')
    report = store.report(day, day + 'T14:30:00Z')
    for suffix, text in [('json', json.dumps(report, indent=2)), ('html', render_report(report)), ('csv', issues_csv(report))]:
        (root / ('brief.' + suffix)).write_text(text, encoding='utf-8')
    (root / 'evaluation.json').write_text(json.dumps(store.evaluate(day + 'T14:30:00Z'), indent=2), encoding='utf-8')
    store.close()
    return str(root / 'brief.html')
