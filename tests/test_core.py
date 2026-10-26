import concurrent.futures, datetime as dt, tempfile, unittest
from growthpilot.core import Store, Invalid, digest
class Workflow(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.s=Store(self.tmp.name+'/test.db'); self.a=self.s.plan(1)['action']; self.id=self.a['id']
 def tearDown(self): self.tmp.cleanup()
 def approve(self): return self.s.transition(self.id,'approve',{'payload_hash':self.a['payload_hash']})
 def test_registries(self):
  state=self.s.snapshot(); self.assertEqual(len(state['products']),17); self.assertEqual(len(state['channels']),50)
 def test_requires_approval(self):
  with self.assertRaises(Invalid): self.s.transition(self.id,'execute',{})
 def test_rejection_blocks_execution(self):
  self.s.transition(self.id,'reject',{})
  with self.assertRaises(Invalid): self.s.transition(self.id,'execute',{})
 def test_revision_invalidates(self):
  self.approve(); a=self.s.transition(self.id,'revise',{'content':'Revised review text'})
  self.assertIsNone(a['approval']); self.assertEqual(a['version'],2)
  with self.assertRaises(Invalid): self.s.transition(self.id,'execute',{})
  with self.assertRaises(Invalid): self.approve()
 def test_expiration(self):
  a=self.approve(); a['approval']['expires_at']='2000-01-01T00:00:00+00:00'
  with self.s.db() as db: self.s.save(db,'actions',a)
  with self.assertRaises(Invalid): self.s.transition(self.id,'execute',{})
 def test_idempotent_concurrent(self):
  self.approve()
  with concurrent.futures.ThreadPoolExecutor(4) as pool: out=list(pool.map(lambda _:self.s.transition(self.id,'execute',{}),range(4)))
  self.assertEqual(len({x['receipt']['id'] for x in out}),1); self.assertEqual(len(self.s.snapshot()['events']),1)
 def test_failure_no_false_receipt(self):
  self.approve()
  with self.assertRaises(Invalid): self.s.transition(self.id,'execute',{'simulate_failure':True})
  self.assertIsNone(self.s.snapshot()['actions'][0]['receipt']); self.assertEqual(self.s.snapshot()['events'],[])
 def test_pause(self):
  self.approve(); self.s.pause(True)
  with self.assertRaises(Invalid): self.s.transition(self.id,'execute',{})
  with self.assertRaises(Invalid): self.s.plan(2)
 def test_product_isolation(self):
  self.s.create_record('leads',{'product_id':1,'name':'Customer','pipeline':'customer'})
  self.assertEqual(self.s.snapshot(2)['leads'],[])
 def test_unsupported_claim(self):
  a=self.s.transition(self.id,'revise',{'claims':['Guaranteed returns']}); self.a=a
  with self.assertRaises(Invalid): self.approve()
 def test_recipient_tampering(self):
  a=self.a; a['payload']['recipient']='unapproved@example.com'; a['payload_hash']=digest(a['payload'])
  with self.s.db() as db: self.s.save(db,'actions',a)
  with self.assertRaises(Invalid): self.approve()
 def test_budget_guard(self):
  a=self.a; a['payload']['cost_cents']=100
  with self.s.db() as db: self.s.save(db,'actions',a)
  with self.assertRaises(Invalid): self.approve()
 def test_due_schedule(self):
  self.s.create_record('schedules',{'product_id':2,'due_at':'2000-01-01T00:00:00+00:00'})
  self.assertEqual(self.s.tick()['processed'],1); self.assertEqual(self.s.tick()['processed'],0)
 def test_actuals_exclude_simulation(self):
  self.approve(); self.s.transition(self.id,'execute',{})
  self.assertEqual(self.s.snapshot()['metrics']['actual_conversions'],0)
 def test_evidence_required(self):
  self.a=self.s.transition(self.id,'revise',{'evidence':[]})
  with self.assertRaises(Invalid): self.approve()
if __name__=='__main__': unittest.main()
