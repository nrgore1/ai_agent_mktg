import datetime as dt,tempfile,unittest
from unittest.mock import patch
from growthpilot.platform import Platform
from growthpilot.identity import Identity
from growthpilot.business_os import BusinessOS,UNITS,ROLES
from growthpilot.operating_plan import OperatingPlan,role_for
from growthpilot.role_access import create_account
from growthpilot.core import Invalid

DAY=dt.date(2026,11,4)
FOUNDER={'username':'founder','role':'founder','products':list(range(1,18))}
class OperatingPlanTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Platform(self.tmp.name+'/test.db');self.i=Identity(self.s)
  self.i.create('founder','Synthetic-Founder-Password','founder',[])
  self.p=OperatingPlan(self.s);self.clock=patch('growthpilot.operating_plan.today',return_value=DAY);self.clock.start()
 def tearDown(self):self.clock.stop();self.tmp.cleanup()
 def start(self):
  self.p.prepare({'start_date':str(DAY)},FOUNDER);self.p.control({'enabled':True,'approve_scope':True},FOUNDER)
 def summary(self,user=FOUNDER):
  with self.s.db()as db:return self.p.summary(db,user)
 def role(self,role='CMO',company='atmakosh',units=None):
  units=units or ['weddingos'];name=company+'-'+role.lower()
  create_account(self.i,{'username':name,'password':'Synthetic-Role-Password','company':company,'business_role':role,'units':units},FOUNDER)
  pids=[p for u in UNITS if u['id']in units for p in u['product_ids']]
  return {'username':name,'role':'business','products':pids}
 def outcome(self,plan,phase=1,status='in_progress'):
  t=next(t for t in plan['tasks']if t['kind']=='outcome'and t['phase']==phase)
  return {'plan_id':plan['id'],'task_id':t['id'],'version':t['version'],'status':status,'source':'synthetic:acceptance-evidence','note':'Synthetic milestone acceptance evidence and limitations verified for testing.','attest':True}
 def test_35_scoped_plans_and_90_day_window(self):
  self.start();d=self.summary()
  self.assertEqual(len(d['plans']),35);self.assertEqual(d['program']['end_date'],'2027-02-01')
  self.assertEqual(sum(len(p['tasks'])for p in d['plans']),210)
  self.assertEqual({p['role']for p in d['plans']},set(ROLES))
  self.assertEqual(d['counts'],{'pending':210})
 def test_prepare_idempotent_no_silent_date_change(self):
  self.start();a=self.summary();r=self.p.prepare({'start_date':str(DAY)},FOUNDER)
  self.assertFalse(r['created']);self.assertEqual(a,self.summary())
  with self.assertRaises(Invalid):self.p.prepare({'start_date':'2026-11-05'},FOUNDER)
 def test_no_work_without_explicit_scope_or_when_paused(self):
  self.p.prepare({'start_date':str(DAY)},FOUNDER)
  self.assertEqual(self.p.tick()['status'],'paused')
  with self.assertRaises(Invalid):self.p.control({'enabled':True,'approve_scope':False},FOUNDER)
  self.p.control({'enabled':True,'approve_scope':True},FOUNDER)
  with patch.object(self.s,'paused',return_value=True):self.assertEqual(self.p.tick()['status'],'paused')
 def test_preparation_cannot_complete_outcomes_or_old_backlog(self):
  self.start();before=self.s.snapshot()
  with self.s.db()as db:original=self.s.rows(db,'execution_tasks');cases=self.s.rows(db,'business_cases')
  for _ in range(35):self.assertEqual(self.p.tick()['status'],'prepared')
  self.assertEqual(self.p.tick()['status'],'current')
  d=self.summary();self.assertEqual(d['counts'],{'completed':35,'pending':175})
  self.assertTrue(all(t['status']=='pending'for p in d['plans']for t in p['tasks']if t['kind']=='outcome'))
  with self.s.db()as db:self.assertEqual(self.s.rows(db,'execution_tasks'),original);self.assertEqual(self.s.rows(db,'business_cases'),cases)
  for k in ['products','channels','actions','campaigns','deliveries']:self.assertEqual(before[k],self.s.snapshot()[k])
  self.assertTrue(self.s.verify_audit()['valid'])
 def test_cadence_phase_boundary_and_end_are_bounded(self):
  self.start()
  for _ in range(35):self.p.tick()
  self.assertEqual(self.p.tick(DAY+dt.timedelta(days=1))['status'],'current')
  self.assertEqual(self.p.tick(DAY+dt.timedelta(days=7))['status'],'prepared')
  self.assertEqual(self.p.tick(DAY+dt.timedelta(days=30))['status'],'prepared')
  self.assertEqual(self.p.tick(DAY+dt.timedelta(days=90))['status'],'window_ended')
  self.assertEqual(self.p.tick(DAY-dt.timedelta(days=1))['status'],'not_started')
 def test_company_role_and_unit_isolation(self):
  user=self.role();self.start()
  for _ in range(35):self.p.tick()
  d=self.summary(user)
  self.assertEqual(len(d['plans']),1);self.assertEqual(d['plans'][0]['role'],'CMO');self.assertEqual(d['plans'][0]['unit_id'],'weddingos')
  self.assertTrue(all(r['role']=='CMO'and r['unit_id']=='weddingos'for r in d['reports']))
  self.assertNotIn('finance',d['reports'][0])
  other=next(p for p in self.summary()['plans']if p['unit_id']=='liqmint_individual')
  with self.assertRaises(PermissionError):self.p.record(self.outcome(other),user)
  with self.assertRaises(PermissionError):self.p.prepare({'start_date':str(DAY)},user)
  with self.assertRaises(PermissionError):self.p.control({'enabled':True,'approve_scope':True},user)
 def test_role_can_submit_but_not_approve(self):
  user=self.role();self.start();plan=self.summary(user)['plans'][0]
  data=self.outcome(plan)
  self.p.record(data,user)
  with self.assertRaises(Invalid):self.p.record(data,user)
  plan=self.summary(user)['plans'][0]
  with self.assertRaises(PermissionError):self.p.record(self.outcome(plan,status='completed'),user)
 def test_future_and_missing_acceptance_rejected(self):
  self.start();plan=self.summary()['plans'][0]
  with self.assertRaises(Invalid):self.p.record(self.outcome(plan,phase=2),FOUNDER)
  with self.assertRaises(Invalid):self.p.record(self.outcome(plan,status='completed'),FOUNDER)
  for _ in range(35):self.p.tick()
  plan=self.summary()['plans'][0];data=self.outcome(plan,status='completed');data['attest']=False
  with self.assertRaises(Invalid):self.p.record(data,FOUNDER)
 def test_founder_outcome_attestation_does_not_approve_product(self):
  self.start()
  for _ in range(35):self.p.tick()
  plan=self.summary()['plans'][0];self.p.record(self.outcome(plan,status='completed'),FOUNDER)
  self.assertEqual(self.summary()['counts']['completed'],36)
  with self.s.db()as db:self.assertEqual(self.s.rows(db,'execution_tasks'),[])
 def test_later_phase_cannot_skip_readiness_and_earlier_outcomes(self):
  self.start()
  for _ in range(35):self.p.tick()
  with patch('growthpilot.operating_plan.today',return_value=DAY+dt.timedelta(days=30)):
   for _ in range(35):self.p.tick()
   plan=self.summary()['plans'][0]
   with self.assertRaises(Invalid):self.p.record(self.outcome(plan,phase=2,status='completed'),FOUNDER)
 def test_disabled_owner_stops_worker(self):
  self.start()
  with self.s.db()as db:db.execute("UPDATE users SET enabled=0 WHERE id='founder'")
  self.assertEqual(self.p.tick()['status'],'owner_unavailable')
 def test_unmapped_products_are_founder_queue_only(self):
  user=self.role();self.start()
  with self.s.db()as db:self.s.save(db,'execution_tasks',{'id':'unmapped','product_id':14,'key':'identity','title':'Unknown product','status':'pending','priority':0,'acceptance':'Confirm identity','dependencies':[]})
  self.assertEqual(self.summary()['backlog'][0]['routing'],'founder_scope_mapping_required')
  self.assertEqual(self.summary(user)['backlog'],[])
 def test_unknown_injected_configuration_rejected(self):
  with self.assertRaises(Invalid):self.p.prepare({'start_date':str(DAY),'model_url':'https://external.invalid'},FOUNDER)
  self.start()
  with self.assertRaises(Invalid):self.p.control({'enabled':True,'approve_scope':True,'auto_approve':True},FOUNDER)
