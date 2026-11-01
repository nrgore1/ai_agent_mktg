import copy,datetime as dt,json,unittest
from tests import test_execution as execution_tests
from growthpilot.core import Invalid
from growthpilot.qualification import Qualification,CASES
from growthpilot.finance_snapshot import merge_actual_finance,PRESERVE

class QualificationTests(unittest.TestCase):
 setUp=execution_tests.ExecutionTests.setUp
 tearDown=execution_tests.ExecutionTests.tearDown
 task=execution_tests.ExecutionTests.task
 complete=execution_tests.ExecutionTests.complete
 def report(self):
  revision=self.e.prepare()['program']['revision']
  return {'run_id':'synthetic-wave-run-001','recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),'strategy_revision':revision,'source':'synthetic:test-report:never-real-readiness','products':[{'product_id':i,'wave':1 if i<=4 else 2 if i in(5,6,9)else 3,'source_version':'synthetic-image-sha-for-tests','environment':'isolated_deployed_image','note':'Synthetic test fixture only, not live product evidence.','cases':[{'key':key,'status':'passed','level':'sandbox_e2e','checks_passed':1,'checks_failed':0,'evidence':'Synthetic complete end-to-end evidence for a regression test.'}for key in CASES]}for i in range(1,18)]}
 def test_only_qualified_task_is_approved_and_commercial_data_unchanged(self):
  report=self.report();self.complete('identity');self.complete('health');self.complete('journey')
  before=self.s.snapshot();raw=self.path.read_bytes()
  result=Qualification(self.s).record(report)
  self.assertEqual(result['technical_approvals'],1);self.assertEqual(result['commercial_approvals'],0)
  self.assertEqual(result['products'][1]['decision'],'blocked_prerequisites')
  after=self.s.snapshot()
  for k in ('products','campaigns','actions','deliveries','events','leads'):self.assertEqual(before[k],after[k])
  self.assertEqual(raw,self.path.read_bytes());self.assertEqual(self.e.summary()['counts']['awaiting_approval'],51)
  self.assertTrue(self.s.verify_audit()['valid'])
 def test_component_success_cannot_auto_approve(self):
  report=self.report();self.complete('identity');self.complete('health');self.complete('journey')
  report['products'][0]['cases'][0].update(status='partial',level='offline_product_tests')
  self.assertEqual(Qualification(self.s).record(report)['technical_approvals'],0)
 def test_component_test_cannot_be_labelled_full_pass(self):
  r=self.report();r['products'][0]['cases'][0]['level']='offline_product_tests'
  with self.assertRaises(Invalid):Qualification(self.s).record(r)
 def test_failure_cannot_be_relabelled_pass(self):
  r=self.report();r['products'][0]['cases'][0]['checks_failed']=1
  with self.assertRaises(Invalid):Qualification(self.s).record(r)
 def test_failed_followup_reopens_previous_technical_completion(self):
  r=self.report();self.complete('identity');self.complete('health');self.complete('journey');Qualification(self.s).record(r)
  newer=copy.deepcopy(r);newer['run_id']='synthetic-wave-run-002';newer['recorded_at']=dt.datetime.now(dt.timezone.utc).isoformat();newer['products'][0]['cases'][0].update(status='failed',checks_failed=1)
  result=Qualification(self.s).record(newer);self.assertEqual(result['technical_approvals'],0)
  self.assertEqual(next(t for t in self.e.summary()['tasks']if t['id']==self.task('entitlements'))['status'],'blocked')
 def test_report_idempotency_and_conflict(self):
  r=self.report();q=Qualification(self.s);first=q.record(r);self.assertEqual(q.record(r),first)
  r['source']='synthetic:different-evidence-source'
  with self.assertRaises(Invalid):q.record(r)
 def test_missing_or_duplicate_product_rejected(self):
  r=self.report();r['products'][-1]=copy.deepcopy(r['products'][0])
  with self.assertRaises(Invalid):Qualification(self.s).record(r)
 def test_missing_category_rejected(self):
  r=self.report();r['products'][0]['cases'].pop()
  with self.assertRaises(Invalid):Qualification(self.s).record(r)
 def test_non_applicable_requires_source_and_rationale(self):
  r=self.report();r['products'][0]['cases'][0].update(status='not_applicable',level='not_run')
  with self.assertRaises(Invalid):Qualification(self.s).record(r)
 def test_stale_or_naive_time_rejected(self):
  r=self.report()
  for stamp in ('2020-01-01T00:00:00+00:00','2026-11-01T00:00:00'):
   r['recorded_at']=stamp
   with self.assertRaises(Invalid):Qualification(self.s).record(r)
 def test_wrong_revision_or_paused_rejected(self):
  r=self.report();wrong=copy.deepcopy(r);wrong['strategy_revision']='outdated'
  with self.assertRaises(Invalid):Qualification(self.s).record(wrong)
  self.s.pause(True)
  with self.assertRaises(Invalid):Qualification(self.s).record(r)
 def test_no_existing_program_rejected(self):
  r=self.report();self.path.unlink()
  with self.assertRaises(Invalid):Qualification(self.s).record(r)
 def test_older_run_cannot_override_newer_results(self):
  r=self.report();q=Qualification(self.s);q.record(r)
  r['run_id']='synthetic-older-run';r['recorded_at']=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=1)).isoformat()
  with self.assertRaises(Invalid):q.record(r)

class FinanceSnapshotTests(unittest.TestCase):
 def test_refresh_preserves_strategy_and_cost_evidence(self):
  existing={k:{'reference':'confirmed:'+k}for k in PRESERVE};existing['transactions']=['old']
  observed={'captured_at':'2026-11-01','product_status':[{'product_id':i}for i in range(1,18)],'transactions':['new']}
  before=copy.deepcopy(existing);merged=merge_actual_finance(existing,observed)
  for k in PRESERVE:self.assertEqual(merged[k],existing[k])
  self.assertEqual(merged['transactions'],['new']);merged['commercial_pricing_plan']['reference']='mutated'
  self.assertEqual(existing,before)
 def test_collector_cannot_overwrite_decisions(self):
  with self.assertRaises(Invalid):merge_actual_finance({}, {'commercial_pricing_plan':{}})
 def test_incomplete_status_envelope_rejected(self):
  with self.assertRaises(Invalid):merge_actual_finance({}, {'captured_at':'2026-11-01','product_status':[]})

if __name__=='__main__':unittest.main()
