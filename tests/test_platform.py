import concurrent.futures, datetime as dt, json, os, sqlite3, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from growthpilot.platform import Platform
from growthpilot.identity import Identity
from growthpilot.core import Invalid, digest
from growthpilot.providers import research

class PlatformTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Platform(self.tmp.name+'/test.db');self.i=Identity(self.s)
 def tearDown(self):self.tmp.cleanup()
 def evidence(self,p=1):
  e=self.s.create_record('evidence',{'product_id':p,'source':'https://example.com/product','excerpt':'A source describing a product.'});return self.s.update('evidence',e['id'],{'status':'verified'})
 def test_identity_session_and_logout(self):
  self.i.create('owner','long-random-password-value','founder');session=self.i.login('owner','long-random-password-value','127.0.0.1');self.assertEqual(self.i.session(session['session'])['role'],'founder');self.i.logout(session['session']);self.assertIsNone(self.i.session(session['session']))
 def test_bad_password_and_limits_persist(self):
  self.i.create('owner','long-random-password-value','founder')
  for _ in range(8):self.assertIsNone(self.i.login('owner','wrong','127.0.0.1'))
  with self.assertRaises(Invalid):self.i.login('owner','long-random-password-value','127.0.0.1')
 def test_password_change_revokes_session(self):
  self.i.create('owner','long-random-password-value','founder');s=self.i.login('owner','long-random-password-value','local');self.i.change_password('owner','long-random-password-value','another-long-random-password');self.assertIsNone(self.i.session(s['session']))
 def test_expired_session_denied(self):
  self.i.create('owner','long-random-password-value');s=self.i.login('owner','long-random-password-value','local')
  with self.s.db() as db:db.execute("UPDATE sessions SET expires='2000-01-01T00:00:00+00:00'")
  self.assertIsNone(self.i.session(s['session']))
 def test_claim_requires_evidence(self):
  with self.assertRaises(Invalid):self.s.update('products',1,{'approved_claims':['Works']})
 def test_claim_cross_product_blocked(self):
  e=self.evidence(2)
  with self.assertRaises(Invalid):self.s.update('products',1,{'approved_claims':['Works'],'claim_evidence':{'Works':[e['id']]}})
 def test_verified_claim_accepted(self):
  e=self.evidence();p=self.s.update('products',1,{'approved_claims':['Works'],'claim_evidence':{'Works':[e['id']]}});self.assertEqual(p['approved_claims'],['Works'])
 def test_channel_rule_needs_source(self):
  with self.assertRaises(Invalid):self.s.update('channels',1,{'terms_status':'verified'})
 def test_negative_budget_blocked(self):
  with self.assertRaises(Invalid):self.s.update('products',1,{'budget_cents':-1})
 @patch.dict(os.environ,{"GROWTHPILOT_CONSENT_SECRET":"backup-test-key-only-"*3})
 def test_backup_restore(self):
  self.s.plan(1);backup=self.s.backup(Path(self.tmp.name)/'backups')
  with sqlite3.connect(Path(self.tmp.name)/'backups'/backup['file']) as db:self.assertEqual(db.execute("SELECT COUNT(*) FROM records WHERE kind='products'").fetchone()[0],17)
  self.assertEqual(backup['integrity'],'ok')
 def test_audit_tamper_detection(self):
  self.s.plan(1);self.assertTrue(self.s.verify_audit()['valid'])
  with self.s.db() as db:db.execute("UPDATE audit SET details='{}' WHERE seq=1")
  self.assertFalse(self.s.verify_audit()['valid'])
 def test_analytics_idempotency_and_scope(self):
  key=self.s.ingest_key(1,'test')['key'];d={'idempotency_key':'sale-1','type':'paid','count':1,'revenue_cents':1000,'utm_source':'test'}
  self.assertFalse(self.s.ingest(key,d)['duplicate']);self.assertTrue(self.s.ingest(key,d)['duplicate']);self.assertEqual(self.s.report()['revenue_cents'],1000)
  with self.assertRaises(Invalid):self.s.ingest(key,dict(d,product_id=2))
 def test_concurrent_ingestion_once(self):
  key=self.s.ingest_key(1,'test')['key'];d={'idempotency_key':'sale','type':'paid','count':1}
  with concurrent.futures.ThreadPoolExecutor(4) as p:list(p.map(lambda _:self.s.ingest(key,d),range(4)))
  self.assertEqual(self.s.report()['funnel']['paid'],1)
 def test_reports_exclude_simulation(self):
  self.s.create_record('events',{'product_id':1,'source':'simulation','type':'paid','count':100,'revenue_cents':100000});self.assertEqual(self.s.report()['revenue_cents'],0)
 def test_recurring_schedule(self):
  s=self.s.create_record('schedules',{'product_id':1,'due_at':'2000-01-01T00:00:00+00:00','recurrence_hours':24});self.s.tick()
  state=self.s.snapshot();self.assertEqual(state['schedules'][0]['status'],'scheduled');self.assertEqual(len(state['campaigns']),1);self.s.tick();self.assertEqual(len(self.s.snapshot()['campaigns']),1)
 def test_lease_recovery_and_slot_dedup(self):
  s=self.s.create_record('schedules',{'product_id':1,'due_at':'2000-01-01T00:00:00+00:00'});self.s.plan(1,slot=s['id']+':'+s['due_at'])
  with self.s.db() as db:s.update(status='running',lease_until='2000-01-01T00:00:00+00:00');self.s.save(db,'schedules',s)
  self.s.tick();self.assertEqual(len(self.s.snapshot()['campaigns']),1)
 def test_ssrf_private_blocked(self):
  for url in ['http://example.com','https://127.0.0.1','https://169.254.169.254','https://localhost']:
   with self.assertRaises(Invalid):research(url)
 def test_external_action_blocked_until_ready(self):
  c=self.s.plan(1)['campaign']
  with self.assertRaises(Invalid):self.s.external_action({'product_id':1,'campaign_id':c['id'],'connector':'github','kind':'publish'})
 def test_lead_management(self):
  lead=self.s.create_record('leads',{'product_id':1,'name':'Potential partner','pipeline':'partner'});lead=self.s.update('leads',lead['id'],{'stage':'qualified','owner':'founder','fit_score':80});self.assertEqual(lead['stage'],'qualified')
 def test_unknown_delivery_not_replayed(self):
  a=self.s.plan(1)['action']
  with self.s.db() as db:
   self.s.save(db,'actions',dict(a,status='executing'));db.execute('INSERT INTO deliveries VALUES(?,?,?,?,?,?,?,?)',('delivery',a['id'],'executing',a['payload_hash'],1,'2000-01-01T00:00:00+00:00',None,'2000'))
  with patch('growthpilot.providers.deliver') as deliver:self.s.process_delivery();deliver.assert_not_called()
  self.assertEqual(self.s.snapshot()['actions'][0]['status'],'unknown')
 def test_llm_missing_evidence_does_not_mutate(self):
  a=self.s.plan(1)['action']
  with self.assertRaises(Invalid):self.s.generate(a['id'])
  self.assertEqual(self.s.snapshot()['actions'][0]['version'],1)

class DeliveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Platform(self.tmp.name+'/q.db');self.env=patch.dict(os.environ,{'GROWTHPILOT_GITHUB_REPO':'owner/sandbox','GROWTHPILOT_ENABLE_LIVE':'true'});self.env.start()
  e=self.s.create_record('evidence',{'product_id':1,'source':'https://example.com','excerpt':'Documented claim'});self.s.update('evidence',e['id'],{'status':'verified'});self.s.update('products',1,{'readiness':'verified','approved_claims':['Documented claim'],'claim_evidence':{'Documented claim':[e['id']]}});self.s.update('channels',43,{'terms_status':'verified','rules_source':'https://docs.github.com/en/rest/issues/issues'})
  c=self.s.plan(1,'github.com')['campaign'];self.a=self.s.external_action({'product_id':1,'campaign_id':c['id'],'connector':'github','kind':'publish','channel':'github.com','destination':'https://github.com/owner/sandbox/issues','account':'owner','recipient':None,'content':'Documented claim','title':'Sandbox test','claims':['Documented claim'],'evidence':[{'id':e['id'],'source':e['source']}],'claims_reviewed':True})
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def approve(self):self.s.transition(self.a['id'],'approve',{'payload_hash':self.a['payload_hash']})
 def test_provider_not_called_before_approval(self):
  with patch('growthpilot.providers.deliver') as provider:
   with self.assertRaises(Invalid):self.s.enqueue(self.a['id'])
   self.s.process_delivery();provider.assert_not_called()
 def test_queue_delivery_once(self):
  self.approve();self.s.enqueue(self.a['id']);self.s.enqueue(self.a['id'])
  with patch('growthpilot.providers.deliver',return_value={'external_delivery':True,'provider_id':'test'}) as provider:self.s.process_delivery();self.s.process_delivery();self.assertEqual(provider.call_count,1)
  with self.s.db() as db:self.assertEqual(self.s.get(db,'actions',self.a['id'])['status'],'executed')
 def test_queue_pause(self):
  self.approve();self.s.enqueue(self.a['id']);self.s.pause(True)
  with patch('growthpilot.providers.deliver') as provider:self.s.process_delivery();provider.assert_not_called()
 def test_provider_failure_quarantine(self):
  self.approve();self.s.enqueue(self.a['id'])
  with patch('growthpilot.providers.deliver',side_effect=TimeoutError) as provider:self.s.process_delivery();self.s.process_delivery();self.assertEqual(provider.call_count,1)
  with self.s.db() as db:self.assertEqual(self.s.get(db,'actions',self.a['id'])['status'],'unknown')
 def test_queued_edit_blocked(self):
  self.approve();self.s.enqueue(self.a['id'])
  with self.assertRaises(Invalid):self.s.transition(self.a['id'],'revise',{'content':'Changed'})
if __name__=='__main__':unittest.main()
