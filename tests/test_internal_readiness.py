import copy,json,unittest
from tests import test_execution
from growthpilot.internal_readiness import set_scope,PRODUCTS,EXCLUDED,POLICY
from growthpilot.core import Invalid

class InternalReadinessTests(unittest.TestCase):
 setUp=test_execution.ExecutionTests.setUp
 tearDown=test_execution.ExecutionTests.tearDown
 task=test_execution.ExecutionTests.task
 complete=test_execution.ExecutionTests.complete
 def test_scope_is_not_a_pass_and_preserves_public_products(self):
  before=self.e.prepare();public=copy.deepcopy([t for t in before['tasks'] if t['product_id'] not in PRODUCTS])
  protected=self.s.snapshot()
  after=set_scope(self.e,'founder:2026-11-03:internal-scope-review')
  self.assertEqual(after['counts']['not_applicable'],20)
  self.assertEqual(after['counts']['completed'],before['counts']['completed'])
  self.assertEqual(public,[t for t in after['tasks'] if t['product_id'] not in PRODUCTS])
  for key in ('products','actions','campaigns','events','leads','deliveries'):self.assertEqual(protected[key],self.s.snapshot()[key])
  for t in after['tasks']:
   if t['product_id'] in PRODUCTS and t['key'] in EXCLUDED:
    self.assertEqual(t['status'],'not_applicable')
    self.assertTrue(t['history'][-1]['snapshot'])
   if t['product_id'] in PRODUCTS and t['key']=='entitlements':
    self.assertNotEqual(t['status'],'completed');self.assertIn('operator roles',t['acceptance'])
  self.assertFalse(after['commercial_execution_enabled'])
  self.assertTrue(self.s.verify_audit()['valid'])
 def test_scope_idempotent_and_survives_strategy_sync(self):
  self.e.prepare();first=set_scope(self.e,'founder:internal-review')
  second=set_scope(self.e,'founder:internal-review')
  self.assertEqual(first['tasks'],second['tasks']);self.assertEqual(first['internal_scopes'],second['internal_scopes'])
  self.e.prepare();self.assertEqual(self.e.summary()['counts']['not_applicable'],20)
  self.plan['offers'][0]['proposed_scope']='New proposal'
  self.path.write_text(json.dumps({'products':[],'actual_finance':{'commercial_pricing_plan':self.plan}}))
  self.e.prepare();d=self.e.summary()
  self.assertEqual(d['counts']['not_applicable'],20)
  self.assertEqual(len(d['internal_scopes']),5)
  a=next(a for a in d['artifacts'] if a['product_id']==10 and a['kind']=='experiment_spec')
  self.assertEqual(a['content']['scope'],'internal_only')
  self.assertNotIn('acquisition',a['content'])
 def test_cannot_turn_na_into_completion_or_use_public_health(self):
  self.e.prepare();set_scope(self.e,'founder:internal-review')
  for key in EXCLUDED:
   with self.assertRaises(Invalid):self.complete(key,10)
  with self.assertRaises(Invalid):self.e.record_health(10,{'url':None,'ok':True})
  with self.assertRaises(Invalid):self.complete('journey',10)
  with self.assertRaises(Invalid):self.e.transition({'id':self.task('identity',1),'status':'not_applicable'},'founder')
 def test_founder_authority_pause_and_stale_source(self):
  self.e.prepare()
  with self.assertRaises(Invalid):set_scope(self.e,'founder:internal-review','admin')
  with self.assertRaises(Invalid):set_scope(self.e,'short')
  self.plan['offers'][0]['proposed_scope']='New proposal'
  self.path.write_text(json.dumps({'products':[],'actual_finance':{'commercial_pricing_plan':self.plan}}))
  with self.assertRaises(Invalid):set_scope(self.e,'founder:internal-review')
 def test_old_public_health_is_invalidated(self):
  self.e.prepare();self.complete('health',10)
  d=set_scope(self.e,'founder:internal-review')
  t=next(t for t in d['tasks'] if t['id']==self.task('health',10))
  self.assertEqual(t['status'],'pending')
  self.assertEqual(t['history'][-1]['snapshot']['status'],'completed')

 def test_cost_collection_and_synthetic_journey_can_proceed_without_legal_completion(self):
  self.e.prepare();set_scope(self.e,'founder:internal-review')
  d=self.e.summary();rows={t['key']:t for t in d['tasks'] if t['product_id']==11}
  self.assertEqual(rows['metering']['effective_status'],'pending')
  self.assertEqual(rows['metering']['blocked_by'],[])
  self.assertEqual(rows['identity']['status'],'pending')
  self.complete('health',11)
  d=self.e.summary();rows={t['key']:t for t in d['tasks'] if t['product_id']==11}
  self.assertEqual(rows['journey']['effective_status'],'pending')
  self.assertEqual(rows['privacy']['effective_status'],'blocked')
  self.assertFalse(d['commercial_execution_enabled'])
 def test_policy_revision_preserves_verified_internal_runtime(self):
  self.e.prepare();set_scope(self.e,'founder:internal-review');self.complete('health',11)
  with self.s.db() as db:
   t=self.s.get(db,'execution_tasks',self.task('health',11));t['scope_policy']='internal-only-20261103-v1';self.s.save(db,'execution_tasks',t)
  d=set_scope(self.e,'founder:parallel-internal-work')
  t=next(t for t in d['tasks'] if t['id']==self.task('health',11))
  self.assertEqual(t['status'],'completed')
  self.assertEqual(t['scope_policy'],POLICY)
