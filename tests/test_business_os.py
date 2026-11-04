import datetime as dt
import tempfile
import unittest
from pathlib import Path
from growthpilot.platform import Platform
from growthpilot.identity import Identity
from growthpilot.business_os import BusinessOS, UNITS, PROCESSES
from growthpilot.core import Invalid

class BusinessTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store=Platform(Path(self.tmp.name)/'test.db');self.os=BusinessOS(self.store);self.ident=Identity(self.store)
  self.users={}
  for name,role,products in [('founder','founder',[]),('admin','admin',[]),('alice','operator',[4]),('bob','operator',[1]),('viewer','viewer',[4]),('partial','operator',[5])]:
   self.ident.create(name,'Long-Testing-Password-Only',role,products);self.users[name]={'username':name,'role':role,'products':products}
  self.f=self.users['founder'];self.a=self.users['alice'];self.b=self.users['bob']
 def tearDown(self):self.tmp.cleanup()
 def grant(self,name='alice',unit='weddingos',role='CMO',enabled=True):
  return self.os.dispatch('assign',dict(username=name,unit_id=unit,role=role,enabled=enabled),self.f)
 def create(self,user=None,unit='weddingos',process='sales'):
  user=user or self.f
  return self.os.dispatch('create',dict(unit_id=unit,process=process,title='Qualified customer opportunity',owner=user['username'],due_date='2026-12-01',reference='internal:test-fixture'),user)
 def record(self,c,user=None,status='complete',**kw):
  return self.os.dispatch('record',dict(id=c['id'],version=c['version'],status=status,source='test-report:fixture',note='Verified scoped evidence and recorded remaining limitations.',attest=True,**kw),user or self.f)
 def test_exact_entity_mapping(self):
  data=self.os.summary(self.f)
  self.assertEqual(len(data['units']),7);self.assertEqual(sum(u['company_id']=='vireoka' for u in UNITS),3)
  self.assertEqual(next(u for u in UNITS if u['id']=='memoire')['product_ids'],[5,7]);self.assertEqual(len(PROCESSES),10)
  self.assertFalse(data['external_execution']);self.assertTrue(all(u['metrics']['actual_revenue'] is None for u in data['units']))
 def test_unassigned_operator_sees_no_unit_data(self):
  self.create();d=self.os.summary(self.a);self.assertEqual(d['units'],[]);self.assertEqual(d['cases'],[]);self.assertEqual(d['users'],[])
 def test_role_assignment_cannot_expand_products(self):
  with self.assertRaises(Invalid):self.grant(unit='liqmint_individual')
  with self.assertRaises(Invalid):self.grant(name='partial',unit='memoire')
 def test_assignment_requires_founder(self):
  for user in [self.a,self.users['admin']]:
   with self.assertRaises(PermissionError):self.os.dispatch('assign',dict(username='alice',unit_id='weddingos',role='CMO',enabled=True),user)
 def test_cross_company_and_case_access_denied(self):
  self.grant();c=self.create(unit='liqmint_individual')
  with self.assertRaises(PermissionError):self.create(self.a,'liqmint_individual')
  with self.assertRaises(PermissionError):self.record(c,self.a)
  self.assertEqual(self.os.summary(self.a)['cases'],[])
 def test_role_handoff_requires_next_role(self):
  self.grant();c=self.create(self.a);c=self.record(c,self.a)
  with self.assertRaises(PermissionError):self.record(c,self.a)
  self.grant(role='CEO');c=self.record(c,self.a);self.assertEqual(c['cursor'],2)
 def test_viewer_read_only_even_with_assignment(self):
  self.grant(name='viewer');c=self.create();self.assertEqual(len(self.os.summary(self.users['viewer'])['cases']),1)
  with self.assertRaises(PermissionError):self.record(c,self.users['viewer'])
 def test_revocation_is_immediate(self):
  self.grant();self.create(self.a);self.grant(enabled=False);self.assertEqual(self.os.summary(self.a)['cases'],[])
 def test_tampered_fields_and_company_rejected(self):
  with self.assertRaises(Invalid):self.os.dispatch('create',{'unit_id':'weddingos','company_id':'vireoka'},self.f)
  c=self.create()
  with self.assertRaises(Invalid):self.record(c,execute=True)
 def test_invalid_due_and_owner(self):
  for field,value in [('due_date','tomorrow'),('owner','unknown-account'),('unit_id','fake')]:
   d=dict(unit_id='weddingos',process='sales',title='A test opportunity',owner='founder',due_date='2026-12-01',reference='source:test');d[field]=value
   with self.assertRaises(Invalid):self.os.dispatch('create',d,self.f)
 def test_evidence_attestation_required(self):
  c=self.create()
  with self.assertRaises(Invalid):self.os.dispatch('record',dict(id=c['id'],version=1,status='complete',source='source:test',note='Verified document and remaining limitations.',attest=False),self.f)
 def test_stale_version_and_replay_rejected(self):
  c=self.create();self.record(c)
  with self.assertRaises(Invalid):self.record(c)
 def test_review_exact_hash_founder_expiry_and_replay(self):
  c=self.create()
  for _ in range(4):c=self.record(c)
  s=c['steps'][3];self.assertEqual(s['status'],'awaiting_review');self.assertEqual(c['cursor'],3)
  d=dict(id=c['id'],version=c['version'],decision='accept',proposal_hash=s['proposal_hash'],note='Verified exact handoff and retained all external action gates.')
  with self.assertRaises(PermissionError):self.os.dispatch('review',d,self.users['admin'])
  with self.assertRaises(Invalid):self.os.dispatch('review',{**d,'proposal_hash':'tampered'},self.f)
  c=self.os.dispatch('review',d,self.f);self.assertEqual(c['cursor'],4)
  with self.assertRaises(Invalid):self.os.dispatch('review',d,self.f)
  c=self.record(c);self.assertEqual(self.os.summary(self.f)['cases'][0]['status'],'completed')
  self.assertEqual(len(c['history']),6);self.assertTrue(self.store.verify_audit()['valid'])
 def test_expired_review_requires_resubmission(self):
  c=self.create()
  for _ in range(4):c=self.record(c)
  c['steps'][3]['expires_at']='2000-01-01T00:00:00+00:00'
  with self.store.db() as db:self.store.save(db,'business_cases',c)
  with self.assertRaises(Invalid):self.os.dispatch('review',dict(id=c['id'],version=c['version'],proposal_hash=c['steps'][3]['proposal_hash'],decision='accept',note='Reviewed evidence with applicable conditions.'),self.f)
  new=self.record(c);self.assertNotEqual(new['steps'][3]['proposal_hash'],c['steps'][3]['proposal_hash'])
 def test_return_and_fresh_evidence_invalidate_approval(self):
  c=self.create()
  for _ in range(4):c=self.record(c)
  old=c['steps'][3]['proposal_hash'];c=self.os.dispatch('review',dict(id=c['id'],version=c['version'],proposal_hash=old,decision='return',note='Please resolve missing economic evidence first.'),self.f)
  self.assertEqual(c['cursor'],3);self.assertEqual(c['steps'][3]['status'],'blocked')
  c=self.record(c);self.assertNotEqual(c['steps'][3]['proposal_hash'],old);self.assertNotIn('decision',c['steps'][3])
 def test_pause_blocks_mutations_but_allows_revocation(self):
  self.grant();c=self.create();self.store.pause(True)
  with self.assertRaises(Invalid):self.record(c)
  with self.assertRaises(Invalid):self.create()
  self.grant(enabled=False);self.assertTrue(self.os.summary(self.f)['paused'])
 def test_product_events_not_created_by_workflow(self):
  before=self.store.snapshot();c=self.create()
  for _ in range(4):c=self.record(c)
  after=self.store.snapshot()
  for key in ['actions','events','campaigns','leads']:self.assertEqual(before[key],after[key])
 def test_metrics_respect_scope_and_do_not_count_simulated_revenue(self):
  self.grant();self.store.create_record('leads',dict(product_id=1,pipeline='customer',name='Other entity'))
  self.store.create_record('leads',dict(product_id=4,pipeline='customer',name='Wedding buyer'))
  d=self.os.summary(self.a);self.assertEqual(len(d['units']),1);self.assertEqual(d['units'][0]['metrics']['leads'],1);self.assertIsNone(d['units'][0]['metrics']['actual_margin'])
 def test_scope_survives_restart(self):
  self.grant();c=self.create(self.a);self.assertEqual(BusinessOS(Platform(self.store.path)).summary(self.a)['cases'][0]['id'],c['id'])
 def test_close_is_not_completion(self):
  c=self.create();self.os.dispatch('close',dict(id=c['id'],version=c['version'],note='Customer withdrew request before activation.'),self.f)
  self.assertEqual(self.os.summary(self.f)['cases'][0]['status'],'closed')
 def test_every_unit_and_process_has_a_workable_complete_path(self):
  for unit in UNITS:
   for process in PROCESSES:
    c=self.create(unit=unit['id'],process=process)
    while c['cursor']<len(c['steps']):
     c=self.record(c)
     if c['cursor']<len(c['steps']) and c['steps'][c['cursor']]['status']=='awaiting_review':
      c=self.os.dispatch('review',dict(id=c['id'],version=c['version'],proposal_hash=c['steps'][c['cursor']]['proposal_hash'],decision='accept',note='Verified synthetic fixture; external execution remains separate.'),self.f)
    self.assertEqual(c['cursor'],5)

if __name__=='__main__':unittest.main()
