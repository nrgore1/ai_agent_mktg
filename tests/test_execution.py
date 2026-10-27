import json,tempfile,unittest
from pathlib import Path
from growthpilot.platform import Platform
from growthpilot.execution import Execution,COMMERCIAL
from growthpilot.core import Invalid
from growthpilot.manager import stable

class ExecutionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Platform(self.tmp.name+'/test.db');self.e=Execution(self.s)
  self.plan={'id':'synthetic-plan','execution_enabled':False,'financial_reconciled':False,'offers':[{'product_id':i,'name':'Test '+str(i),'recommended_offer':'Unapproved price','partner_terms':'Pending approval','proposed_scope':'Synthetic scoped feature hypothesis','must_validate':'Verify implemented scope','launch_status':'Hold'} for i in range(1,18)]}
  self.path=Path(self.tmp.name)/'economics-source.json';self.path.write_text(json.dumps({'products':[],'actual_finance':{'commercial_pricing_plan':self.plan}}))
 def tearDown(self):self.tmp.cleanup()
 def task(self,key,pid=1):return stable('execution:'+str(pid)+':'+key)
 def complete(self,key,pid=1):return self.e.transition({'id':self.task(key,pid),'status':'completed','source':'synthetic:test-report:version-1','note':'Synthetic test evidence meeting all documented criteria; not a live product test.','attest_verified':True},'test_founder')
 def test_all_17_coverage_and_honest_preparation(self):
  before=self.s.snapshot();d=self.e.prepare()
  self.assertEqual(len(d['tasks']),238);self.assertEqual(len(d['artifacts']),51);self.assertEqual(d['counts']['completed'],51);self.assertEqual(d['counts']['awaiting_approval'],51)
  self.assertEqual({t['product_id'] for t in d['tasks']},set(range(1,18)));self.assertFalse(d['commercial_execution_enabled'])
  after=self.s.snapshot()
  for key in ('products','actions','campaigns','events','leads','deliveries'):self.assertEqual(before[key],after[key])
  self.assertTrue(self.s.verify_audit()['valid'])
 def test_missing_plan_does_not_create_old_pricing(self):
  self.path.unlink()
  with self.assertRaises(Invalid):self.e.prepare()
  self.assertEqual(self.e.summary()['tasks'],[])
 def test_duplicate_product_rejected(self):
  self.plan['offers'][-1]['product_id']=1;self.path.write_text(json.dumps({'products':[],'actual_finance':{'commercial_pricing_plan':self.plan}}))
  with self.assertRaises(Invalid):self.e.prepare()
 def test_idempotent_and_revision_invalidates_tests(self):
  self.e.prepare();self.complete('identity');self.e.prepare();self.assertEqual(len(self.e.summary()['tasks']),238)
  self.assertEqual(next(t for t in self.e.summary()['tasks'] if t['id']==self.task('identity'))['status'],'completed')
  self.plan['offers'][0]['proposed_scope']='Changed scope';self.path.write_text(json.dumps({'products':[],'actual_finance':{'commercial_pricing_plan':self.plan}}));self.assertTrue(self.e.summary()['source_changed'])
  with self.assertRaises(Invalid):self.complete('health')
  self.e.prepare();row=next(t for t in self.e.summary()['tasks'] if t['id']==self.task('identity'));self.assertEqual(row['status'],'pending');self.assertTrue(row['history'])
 def test_commercial_completion_forbidden(self):
  self.e.prepare()
  for key in COMMERCIAL:
   with self.assertRaises(Invalid):self.complete(key)
  self.assertEqual(self.e.summary()['counts']['awaiting_approval'],51)
 def test_dependencies_and_attestation(self):
  self.e.prepare()
  with self.assertRaises(Invalid):self.complete('journey')
  with self.assertRaises(Invalid):self.e.transition({'id':self.task('identity'),'status':'completed','source':'report-reference','note':'Sufficiently detailed test outcome and evidence reference.'},'test')
  self.complete('identity');self.complete('health');self.complete('journey');self.complete('entitlements')
  self.e.transition({'id':self.task('identity'),'status':'pending'},'test')
  rows={t['key']:t for t in self.e.summary()['tasks'] if t['product_id']==1}
  self.assertEqual(rows['journey']['status'],'pending');self.assertEqual(rows['entitlements']['status'],'pending')
 def test_paused_system_blocks_writes(self):
  self.e.prepare();self.s.pause(True)
  with self.assertRaises(Invalid):self.complete('identity')
  with self.assertRaises(Invalid):self.e.prepare()
 def test_probe_matches_configured_url_and_no_readiness_promotion(self):
  self.e.prepare();self.s.update('products',1,{'website':'https://example.com'})
  with self.assertRaises(Invalid):self.e.record_health(1,{'url':'https://other.example.com','ok':True})
  self.e.record_health(1,{'url':'https://example.com','ok':True,'status_code':200})
  d=self.e.summary();self.assertEqual(d['counts']['completed'],52);self.assertEqual(d['launch_verified_products'],0)
  self.assertEqual(next(p for p in self.s.snapshot()['products'] if p['id']==1)['readiness'],'requires_verification')

if __name__=='__main__':unittest.main()
