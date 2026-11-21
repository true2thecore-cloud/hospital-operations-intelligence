import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from hospital_ops.core import Store, load_config, parse_vtt, staffing_date
from hospital_ops.render import render_report, issues_csv
from hospital_ops.demo import create_demo
from hospital_ops import graph

ROOT = Path(__file__).resolve().parent.parent
VTT = 'WEBVTT\n\n00:00:01.000 --> 00:00:05.000\n<v OR Charge>No call-outs. Review &amp; confirm.</v>\n'


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cfg = load_config(ROOT / 'config/site.example.json')
        self.store = Store(Path(self.temp.name) / 'test.sqlite', self.cfg)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def meeting(self, mid='am', kind='plan_ahead_am', time='09:00', day='2027-01-04'):
        return self.store.ingest_vtt(VTT, kind, day + 'T' + time + ':00Z', mid, mid, day + 'T' + time + ':00Z')

    def review(self, mid='am', rid='r1', state='active', at='2027-01-04T09:10:00Z', outcomes=None):
        return self.store.add_review({'id': rid, 'meetingId': mid, 'reviewerRole': 'Reviewer',
            'observations': [{'signal': key, 'state': state, 'summary': 'Confirmed in example.', 'cueIds': ['c1'], 'issueId': key} for key in ['staffing_shortage', 'bed_pressure']],
            'outcomes': outcomes or []}, at)

    def test_vtt_voice_multiline_and_entities(self):
        c = parse_vtt(VTT)[0]
        self.assertEqual(c['speaker'], 'OR Charge')
        self.assertIn('& confirm', c['text'])
        self.assertEqual(c['startMs'], 1000)

    def test_malformed_vtt_rejected(self):
        for value in ['hello', 'WEBVTT\n', VTT.replace('00:00:05.000', '00:00:00.000')]:
            with self.assertRaises(ValueError):
                parse_vtt(value)

    def test_mentions_are_not_confirmed(self):
        m = self.meeting()
        draft = self.store.draft_review(m['id'])
        self.assertTrue(draft['suggestedMentions'])
        self.assertEqual(draft['reviewTemplate']['observations'], [])
        self.assertEqual(self.store.report('2027-01-04', '2027-01-04T10:00:00Z')['warnings'], [])

    def test_ingest_is_idempotent(self):
        self.meeting()
        self.meeting()
        self.assertEqual(len(self.store.records('meeting')), 1)
        with self.assertRaises(ValueError):
            self.store.ingest_vtt(VTT + '\nChanged', 'plan_ahead_am', '2027-01-04T09:00:00Z', 'am', 'am', '2027-01-04T10:00:00Z')

    def test_review_evidence_validation(self):
        self.meeting()
        with self.assertRaises(ValueError):
            self.store.add_review({'id': 'bad', 'meetingId': 'am', 'reviewerRole': 'Reviewer', 'observations': [{'signal': 'staffing_shortage', 'state': 'active', 'summary': 'X', 'cueIds': ['missing'], 'issueId': 'a'}]}, '2027-01-04T09:10:00Z')

    def test_review_defaults_still_allow_duplicate_import(self):
        self.meeting()
        review = {'id': 'minimal', 'meetingId': 'am', 'reviewerRole': 'Reviewer', 'observations': [{'signal': 'staffing_shortage', 'state': 'active', 'summary': 'Example', 'cueIds': ['c1'], 'issueId': 'a'}]}
        first = self.store.add_review(review, '2027-01-04T09:10:00Z')
        again = self.store.add_review(review, '2027-01-04T09:20:00Z')
        self.assertEqual(first, again)
        self.assertEqual(len(self.store.records('review')), 1)

    def test_later_data_cannot_change_earlier_brief(self):
        self.meeting()
        self.review()
        before = self.store.report('2027-01-04', '2027-01-04T09:30:00Z')
        self.meeting('pm', 'plan_ahead_pm', '14:00')
        self.review('pm', 'r2', 'cleared', '2027-01-04T14:10:00Z')
        after = self.store.report('2027-01-04', '2027-01-04T09:30:00Z')
        self.assertEqual(before['warnings'], after['warnings'])
        self.assertEqual(before['issues'], after['issues'])
        self.assertEqual(self.store.report('2027-01-04', '2027-01-04T14:30:00Z')['warnings'], [])

    def test_unknown_is_not_no_event(self):
        self.meeting()
        self.review()
        h = self.store.cohort(self.cfg['rules'][0], '2027-01-05', '2027-01-05T10:00:00Z')
        self.assertEqual(h['matchedDays'], 0)
        self.assertEqual(h['unknownOutcomeDays'], 1)

    def test_outcome_requires_later_meeting_and_known_at_cutoff(self):
        self.meeting()
        o = [{'key': 'late_flow_delay', 'value': True, 'summary': 'Example delay', 'cueIds': ['c1']}]
        self.review(outcomes=o)
        self.assertIsNone(self.store.outcome('2027-01-04', 'late_flow_delay', '2027-01-04T09:10:00Z', '2027-01-05T00:00:00Z'))
        self.meeting('pm', 'plan_ahead_pm', '14:00')
        self.review('pm', 'pmr', at='2027-01-04T14:10:00Z', outcomes=o)
        self.assertTrue(self.store.outcome('2027-01-04', 'late_flow_delay', '2027-01-04T09:10:00Z', '2027-01-05T00:00:00Z'))

    def test_revision_keeps_prior_asof(self):
        self.meeting()
        self.review()
        self.review(rid='r2', state='cleared', at='2027-01-04T10:00:00Z')
        self.assertEqual(self.store.states('2027-01-04', '2027-01-04T09:30:00Z')['staffing_shortage'], 'active')
        self.assertEqual(self.store.states('2027-01-04', '2027-01-04T10:30:00Z')['staffing_shortage'], 'cleared')

    def test_different_dates_keep_open_issue(self):
        self.meeting()
        self.review()
        report = self.store.report('2027-01-05', '2027-01-05T10:00:00Z')
        self.assertEqual(len(report['issues']), 2)
        self.assertEqual(report['warnings'], [])  # carry-forward is not evidence of today's signal

    def test_friday_weekend_same_date_holiday(self):
        self.assertEqual(staffing_date('2027-01-22'), '2027-01-25')
        self.assertEqual(staffing_date('2027-01-23'), '2027-01-25')
        self.assertEqual(staffing_date('2027-01-22', holidays=['2027-01-25']), '2027-01-26')
        self.assertEqual(staffing_date('2027-01-22', 'same-date'), '2027-01-22')
        with self.assertRaises(ValueError):
            staffing_date('2027-02-30')

    def test_staffing_shape_and_stale_capture(self):
        p = {'version': 1, 'staffingDate': '2027-01-04', 'sourceSheet': '01-04-27', 'capturedUtc': '2027-01-04T09:00:00Z', 'values': [[''] * 12 for _ in range(46)]}
        self.store.add_snapshot('staffing', p, '2027-01-04T10:00:00Z')
        p['capturedUtc'] = '2027-01-04T08:00:00Z'
        self.store.add_snapshot('staffing', p, '2027-01-04T11:00:00Z')
        self.assertEqual(self.store.report('2027-01-04', '2027-01-04T12:00:00Z')['snapshots']['staffing']['payload']['capturedUtc'], '2027-01-04T09:00:00Z')
        p['values'].pop()
        with self.assertRaises(ValueError):
            self.store.add_snapshot('staffing', p)

    def test_synthetic_and_operational_cannot_mix(self):
        config = copy.deepcopy(self.cfg)
        config['datasetMode'] = 'synthetic'
        with self.assertRaises(ValueError):
            Store(Path(self.temp.name) / 'test.sqlite', config)

    def test_html_and_csv_escape(self):
        self.meeting()
        r = self.review()
        report = self.store.report('2027-01-04', '2027-01-04T10:00:00Z')
        report['issues'][0]['summary'] = '<script>alert(1)</script>'
        self.assertNotIn('<script>', render_report(report))
        report['issues'][0]['summary'] = '=HYPERLINK("bad")'
        self.assertIn("'=HYPERLINK", issues_csv(report))

    def test_graph_host_guard_and_idempotent_pull(self):
        with self.assertRaises(ValueError):
            graph.get('https://untrusted.example/transcripts')
        with patch.object(graph, 'get', side_effect=[json.dumps({'value': [{'id': 'one'}]}), VTT]):
            result = graph.pull(self.store, 'organizer-id', 'meeting-id', 'plan_ahead_am', '2026-01-04T09:00:00Z')
        self.assertEqual(result['status'], 'imported')

    def test_demo_end_to_end(self):
        out = Path(self.temp.name) / 'demo'
        create_demo(out)
        create_demo(out)  # repeated run does not append duplicates
        report = json.loads((out / 'brief.json').read_text())
        self.assertEqual(report['datasetMode'], 'synthetic')
        self.assertEqual(report['warnings'][0]['history']['matchedDays'], 11)
        self.assertEqual(report['warnings'][0]['history']['events'], 8)
        self.assertEqual(report['snapshots']['staffing']['payload']['staffingDate'], '2027-01-25')
        self.assertTrue((out / 'evaluation.json').exists())


if __name__ == '__main__':
    unittest.main()
