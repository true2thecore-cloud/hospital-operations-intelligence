import copy
import json
import tempfile
import unittest
from pathlib import Path
from hospital_ops.readiness import read, validate_profile, open_store, ingest, snapshot, close_day, payload, lookback
from hospital_ops.configure import generate

ROOT=Path(__file__).resolve().parents[1]


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.p=read(ROOT/'examples/readiness-profile.json')
        self.p['meetings']=[m for m in self.p['meetings'] if m['key']=='plan_am']
        self.s=open_store(Path(self.temp.name)/'test.sqlite',self.p)
        self.r=read(ROOT/'templates/reviewed-meeting.example.json')
        self.now='2027-01-22T23:10:00-05:00'

    def tearDown(self): self.s.close();self.temp.cleanup()

    def add(self,r=None,now=None): return ingest(self.s,self.p,r or self.r,now or self.now)

    def test_duplicate_and_conflicting_revision(self):
        a=self.add();b=self.add(now='2027-01-23T05:00:00-05:00')
        self.assertEqual(a,b)
        bad=copy.deepcopy(self.r);bad['metrics'][0]['value']=30
        with self.assertRaisesRegex(ValueError,'new revision'): self.add(bad)

    def test_missing_evidence_and_wrong_type_rejected(self):
        bad=copy.deepcopy(self.r);bad['metrics'][0]['value']='Not stated'
        with self.assertRaisesRegex(ValueError,'finite'):self.add(bad)
        bad=copy.deepcopy(self.r);bad['issues'][0]['evidence'][0]['sourceId']='absent'
        with self.assertRaisesRegex(ValueError,'available source'):self.add(bad)

    def test_closing_waits_for_processing_and_time(self):
        with self.assertRaisesRegex(ValueError,'waits'):close_day(self.s,self.p,'2027-01-22',self.now)
        self.add(now='2027-01-22T10:31:00-05:00')
        with self.assertRaisesRegex(ValueError,'not passed'):close_day(self.s,self.p,'2027-01-22','2027-01-22T11:00:00-05:00')
        result=close_day(self.s,self.p,'2027-01-22',self.now)
        self.assertEqual(result['snapshot']['metrics']['or_cases']['value'],28)

    def test_close_is_immutable_after_late_revision(self):
        self.add();frozen=close_day(self.s,self.p,'2027-01-22',self.now)
        revised=copy.deepcopy(self.r);revised['id']='revision-2';revised['metrics'][0]['value']=31
        self.add(revised,'2027-01-23T05:00:00-05:00')
        again=close_day(self.s,self.p,'2027-01-22','2027-01-23T06:00:00-05:00')
        self.assertEqual(frozen,again)
        self.assertEqual(snapshot(self.s,self.p,'2027-01-23','2027-01-23T06:00:00-05:00')['metrics']['or_cases']['value'],31)
        self.assertEqual(len(self.s.records('daily_close')),1)

    def test_seven_calendar_days_resolved_remains_then_expires(self):
        self.add()
        revised=copy.deepcopy(self.r);revised['id']='resolved';revised['issues'][0]['state']='cleared'
        self.add(revised,'2027-01-23T05:00:00-05:00')
        snap=snapshot(self.s,self.p,'2027-01-28','2027-01-28T23:00:00-05:00')
        self.assertEqual(len(snap['sevenDayConcerns']),1);self.assertEqual(snap['sevenDayConcerns'][0]['state'],'cleared')
        self.assertEqual(snap['openIssues'],[])
        self.assertEqual(snapshot(self.s,self.p,'2027-01-29','2027-01-29T23:00:00-05:00')['sevenDayConcerns'],[])
        self.assertEqual(len(self.s.records('readiness')),2)

    def test_low_excluded_and_event_date_cannot_reset(self):
        self.r['issues'][0]['severity']='LOW';self.add()
        self.assertEqual(snapshot(self.s,self.p,'2027-01-22',self.now)['sevenDayConcerns'],[])
        bad=copy.deepcopy(self.r);bad['id']='other';bad['issues'][0]['eventDate']='2027-01-21'
        with self.assertRaisesRegex(ValueError,'reset'):self.add(bad)

    def test_resolved_same_day_remains_in_permanent_daily_concerns(self):
        self.r['issues'][0]['state']='cleared';self.add()
        closed=close_day(self.s,self.p,'2027-01-22',self.now)
        self.assertEqual(closed['snapshot']['openIssues'],[])
        self.assertEqual(len(closed['snapshot']['dailyConcerns']),1)
        master=next(v for v in payload(self.s,self.p,'2027-01-22',self.now)['sheets'] if v['name']=='Master Table')
        self.assertIn('[cleared]',master['rows'][0][len(self.p['fields'])+1])

    def test_unavailable_allows_close_and_weekend_not_expected(self):
        self.r.update(status='unavailable',statusNote='Transcript unavailable after review',metrics=[],issues=[],sources=[])
        self.add();self.assertEqual(close_day(self.s,self.p,'2027-01-22',self.now)['coverage'][0]['status'],'unavailable')
        self.assertEqual(close_day(self.s,self.p,'2027-01-23','2027-01-23T23:10:00-05:00')['coverage'],[])

    def test_pending_blocks_and_actual_late_end_extends_gate(self):
        self.r['sources'].append(dict(id='pending',type='email',status='pending'))
        self.add()
        with self.assertRaisesRegex(ValueError,'pending'):close_day(self.s,self.p,'2027-01-22',self.now)
        fixed=copy.deepcopy(self.r);fixed['id']='fixed';fixed['sources'].pop();fixed['endsAt']='2027-01-22T22:45:00-05:00'
        self.add(fixed)
        with self.assertRaisesRegex(ValueError,'not passed'):close_day(self.s,self.p,'2027-01-22',self.now)

    def test_future_volume_not_current_and_known_retains_timestamp(self):
        self.add()
        later=copy.deepcopy(self.r);later['id']='next-day';later['startsAt']='2027-01-22T11:00:00-05:00';later['endsAt']='2027-01-22T11:30:00-05:00'
        later['metrics'][0].update(appliesToDate='2027-01-25',value=45,observedAt='2027-01-22T11:05:00-05:00')
        self.add(later)
        snap=snapshot(self.s,self.p,'2027-01-22',self.now)
        self.assertEqual(snap['metrics']['or_cases']['value'],28)
        self.assertEqual(snap['upcomingMetrics'][0]['value'],45)
        self.assertEqual(snapshot(self.s,self.p,'2027-01-23','2027-01-23T12:00:00-05:00')['metrics']['or_cases']['appliesToDate'],'2027-01-22')

    def test_export_has_append_master_and_history(self):
        self.add();close_day(self.s,self.p,'2027-01-22',self.now)
        views={v['name']:v for v in payload(self.s,self.p,'2027-01-22',self.now)['sheets']}
        self.assertEqual(views['Master Table']['mode'],'append')
        self.assertEqual(len(views['Master Table']['rows']),1)
        self.assertEqual(views['Issue History']['keys'],[self.r['id']+':example-tray-01'])
        self.assertTrue(all(len(v['name'])<=31 for v in views.values()))

    def test_block_version_and_last_session(self):
        schedule=read(ROOT/'templates/block-schedule.example.json')
        result=lookback(self.s,self.p,'2027-02-19',schedule,'2027-02-19T06:00:00-05:00')
        self.assertEqual({x['mode'] for x in result},{'previous_session','previous_month_block'})
        self.assertEqual(result[0]['prior']['date'],'2027-01-15')
        self.assertEqual(result[0]['issues'],[])
        with self.assertRaisesRegex(ValueError,'Exactly one'):lookback(self.s,self.p,'2027-03-19',schedule,self.now)

    def test_setup_generates_profiles_and_refuses_overwrite(self):
        out=Path(self.temp.name)/'setup';generate(self.p,out)
        self.assertTrue((out/'plan_am-extraction.md').exists())
        validate_profile(read(out/'profile.json'))
        with self.assertRaisesRegex(ValueError,'empty'):generate(self.p,out)

    def test_asof_excludes_later_review(self):
        self.add()
        self.assertEqual(snapshot(self.s,self.p,'2027-01-22','2027-01-22T10:00:00-05:00')['metrics'],{})


if __name__=='__main__':unittest.main()
