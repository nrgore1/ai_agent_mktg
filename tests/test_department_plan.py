import unittest,tempfile,datetime as dt,copy
from pathlib import Path
from unittest.mock import patch
from growthpilot.platform import Platform
from growthpilot.identity import Identity
from growthpilot.business_os import BusinessOS,UNITS
from growthpilot.operating_plan import OperatingPlan
from growthpilot.department_plan import DepartmentPlan,POLICY,reconcile_owners
from growthpilot.saas_roles import SAAS_ROLES
from growthpilot.human_ai import HumanAI
from growthpilot.user_management import dispatch,directory
from growthpilot.core import Invalid

DAY=dt.date(2026,11,4)
class DepartmentPlanTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Platform(Path(self.tmp.name)/'db');self.i=Identity(self.s);self.f={'username':'founder','role':'founder','products':[]};self.i.create('founder','Synthetic-Founder-Password','founder')
  self.clock=patch('growthpilot.operating_plan.today',return_value=DAY);self.clock.start();self.op=OperatingPlan(self.s);self.d=DepartmentPlan(self.s);self.h=HumanAI(self.s)
  self.op.prepare({'start_date':str(DAY)},self.f);self.op.control({'enabled':True,'approve_scope':True},self.f)
  with self.s.db()as db:
   for id,pid,key,status in [('mapped',4,'journey','blocked'),('done',4,'finance','completed'),('unmapped',9,'health','pending')]:
    self.s.save(db,'execution_tasks',dict(id=id,product_id=pid,key=key,title='Synthetic '+key,status=status,priority=0,acceptance='Verify actual scoped evidence and retain unresolved limitations.',dependencies=[],evidence=[]))
 def tearDown(self):self.clock.stop();self.tmp.cleanup()
 def rows(self,kind):
  with self.s.db()as db:return self.s.rows(db,kind)
 def prepare(self):return self.d.prepare({'source':'Owner authorized department plans, evidence preparation and scoped assignment.'},self.f)
 def plan(self,role='QA',unit='weddingos'):return next(p for p in self.rows('operating_plans')if p['role']==role and p['unit_id']==unit)
 def create(self,name='qa-person',role='QA',unit='weddingos',company='atmakosh'):
  dispatch(self.i,'create',dict(username=name,password='Synthetic-Role-Password',display_name=name,company=company,roles=[role],units=[unit],note='Authorized synthetic scoped staff account for role-plan testing.'),self.f)
  return {'username':name,'role':'business','products':next(u for u in UNITS if u['id']==unit)['product_ids']}
 def manual(self,role='QA',phase=1):
  p=self.plan(role);t=next(t for t in p['tasks']if t['kind']=='outcome'and t['phase']==phase)
  return next(m for m in self.rows('human_manual_tasks')if m['id']==t['manual_task_id'])
 def action(self,m,action='complete',user=None):return self.h.task_action(dict(id=m['id'],version=m['version'],action=action,source='synthetic:reviewed-evidence',note='Verified the complete synthetic deliverable and recorded its scope and limitations.',attest=True),user or self.f)
 def outcome(self,role='QA',phase=1,status='completed',user=None):
  p=self.plan(role);t=next(t for t in p['tasks']if t['kind']=='outcome'and t['phase']==phase)
  return self.op.record(dict(plan_id=p['id'],task_id=t['id'],version=t['version'],status=status,source='synthetic:reviewed-acceptance',note='Verified current synthetic acceptance evidence, dependencies and limitations.',attest=True),user or self.f)
 def prepare_phase(self,role='QA',phase=1):
  with self.s.db()as db:
   p=self.plan_from_db(db,role);r=self.op._report(db,p,1,phase);self.s.save(db,'operating_reports',r)
   next(t for t in p['tasks']if t['kind']=='preparation'and t['phase']==phase)['status']='completed';self.s.save(db,'operating_plans',p)
 def plan_from_db(self,db,role):return next(p for p in self.s.rows(db,'operating_plans')if p['role']==role and p['unit_id']=='weddingos')
 def test_expansion_idempotence_and_original_evidence_preserved(self):
  plans=self.rows('operating_plans');backlog=self.rows('execution_tasks');result=self.prepare()
  self.assertEqual(result['plans_created'],105);self.assertEqual(result['activities_created'],630);self.assertEqual(result['phase_manual_tasks_created'],315);self.assertEqual(result['backlog_routed'],1)
  self.assertEqual(len(self.rows('operating_plans')),140);self.assertEqual(backlog,self.rows('execution_tasks'));self.assertEqual(plans,[p for p in self.rows('operating_plans')if not p.get('department_policy')]);self.assertFalse(self.prepare()['created'])
  self.assertTrue(all(t['status']=='pending'for p in self.rows('operating_plans')if p.get('department_policy')for t in p['tasks']));self.assertTrue(self.s.verify_audit()['valid'])
 def test_reuses_open_manual_and_keeps_executive_accountability(self):
  from growthpilot.work_assignment import WorkAssignment
  from growthpilot.role_access import create_account
  create_account(self.i,dict(username='existing-cto',password='Synthetic-Role-Password',company='atmakosh',business_role='CTO',units=['weddingos']),self.f)
  WorkAssignment(self.s).assign({'source':'Synthetic initial executive assignment and evidence handoff.'},self.f)
  old=next(m for m in self.rows('human_manual_tasks')if m['source']=='execution_tasks/mapped');backlog=copy.deepcopy(self.rows('execution_tasks'));self.prepare()
  matches=[m for m in self.rows('human_manual_tasks')if m['source']=='execution_tasks/mapped'];self.assertEqual(len(matches),1);self.assertEqual(matches[0]['id'],old['id']);self.assertEqual(matches[0]['role'],'QA');self.assertEqual(matches[0]['oversight_role'],'CTO');self.assertEqual(backlog,self.rows('execution_tasks'))
 def test_unique_owner_routes_and_revocation_returns_to_president(self):
  self.prepare();person=self.create();self.assertEqual(self.plan()['accountable_human'],person['username']);self.assertEqual(self.manual()['assignee'],person['username'])
  row=next(u for u in directory(self.i,self.f)['users']if u['username']==person['username']);dispatch(self.i,'disable',dict(username=row['username'],version=row['version'],note='Disable synthetic owner to test safe work fallback.'),self.f)
  self.assertEqual(self.plan()['accountable_human'],'founder');self.assertEqual(self.manual()['assignee'],'founder')
 def test_ambiguous_owner_requires_selection_and_scope_validation(self):
  self.prepare();a=self.create();b=self.create('second-qa');self.assertEqual(self.plan()['accountable_human'],'founder');p=self.plan()
  request=dict(plan_id=p['id'],version=p['owner_version'],username=a['username'],note='President selects one accountable owner from eligible people.')
  with self.assertRaises(PermissionError):self.d.owner(request,a)
  with self.assertRaises(PermissionError):self.d.owner({**request,'username':'atmakosh.cfo'},self.f)
  self.d.owner(request,self.f);self.assertEqual(self.plan()['accountable_human'],a['username'])
  with self.assertRaises(Invalid):self.d.owner(request,self.f)
 def test_all_roles_are_scoped_to_their_company_unit(self):
  self.prepare()
  for company,unit in [('atmakosh','weddingos'),('vireoka','liqmint_individual')]:
   for role in SAAS_ROLES:
    person=self.create(company+'-'+role,role,unit,company);d=BusinessOS(self.s).summary(person)
    self.assertEqual(len(d['department_program']['plans']),1);self.assertEqual(d['department_program']['plans'][0]['role'],role);self.assertEqual(d['department_program']['plans'][0]['unit_id'],unit)
    self.assertEqual(len(d['operating_plan']['backlog']),1 if role=='QA'and unit=='weddingos'else 0);self.assertEqual(d['department_program']['plans'][0]['candidate_owners'],[]);self.assertTrue(all(m['unit_id']==unit and m['role']==role for m in d['department_program']['manual_tasks']));self.assertIn('plan',d['dashboard_tabs'])
 def test_manual_completion_submits_but_only_president_accepts(self):
  self.prepare();u=self.create();self.prepare_phase();self.action(self.manual(),user=u);self.assertEqual(next(t for t in self.plan()['tasks']if t['kind']=='outcome'and t['phase']==1)['status'],'ready_for_review')
  with self.assertRaises(PermissionError):self.outcome(user=u)
  self.outcome();self.assertEqual(next(t for t in self.plan()['tasks']if t['kind']=='outcome'and t['phase']==1)['status'],'completed');self.assertEqual(next(t for t in self.rows('execution_tasks')if t['id']=='mapped')['status'],'blocked')
 def test_no_acceptance_without_manual_or_preparation(self):
  self.prepare()
  with self.assertRaises(Invalid):self.outcome()
  self.action(self.manual())
  with self.assertRaises(Invalid):self.outcome()
 def test_future_phase_prior_phase_and_readiness_gates(self):
  self.prepare()
  with self.assertRaises(Invalid):self.action(self.manual(phase=2))
  with patch('growthpilot.operating_plan.today',return_value=DAY+dt.timedelta(days=30)):
   self.prepare_phase(phase=2);self.action(self.manual(phase=2))
   with self.assertRaises(Invalid):self.outcome(phase=2)
   with self.s.db()as db:
    task=self.s.get(db,'execution_tasks','mapped');task['status']='completed';self.s.save(db,'execution_tasks',task)
   with self.assertRaises(Invalid):self.outcome(phase=2)
   self.prepare_phase();self.action(self.manual());self.outcome();self.outcome(phase=2)
 def test_reopening_manual_invalidates_accepted_outcome(self):
  self.prepare();self.prepare_phase();self.action(self.manual());self.outcome();self.action(self.manual(),action='reopen')
  self.assertEqual(next(t for t in self.plan()['tasks']if t['kind']=='outcome'and t['phase']==1)['status'],'blocked')
 def test_auditor_stays_read_only_and_president_records_findings(self):
  self.prepare();auditor=self.create('auditor-person','AUDITOR');self.assertEqual(self.plan('AUDITOR')['accountable_human'],'auditor-person');self.assertEqual(self.manual('AUDITOR')['assignee'],'founder')
  with self.assertRaises(PermissionError):self.action(self.manual('AUDITOR'),user=auditor)
  with self.assertRaises(PermissionError):self.outcome('AUDITOR',status='in_progress',user=auditor)
  self.prepare_phase('AUDITOR');self.action(self.manual('AUDITOR'));self.outcome('AUDITOR')
 def test_weekly_department_preparation_is_not_an_ai_recommendation(self):
  self.prepare()
  for _ in range(141):result=self.op.tick()
  self.assertEqual(result['status'],'current');self.assertEqual(len(self.rows('operating_reports')),140)
  d=BusinessOS(self.s).summary(self.f);self.assertEqual(len(d['operating_plan']['reports']),140);self.assertEqual(len(d['human_ai']['targets']),35);self.assertEqual(d['department_program']['counts']['completed_outcomes'],0)
  self.assertTrue(all(t['status']=='pending'for p in self.rows('operating_plans')if p.get('department_policy')for t in p['tasks']if t['phase']>1 or t['kind']=='outcome'))
 def test_paused_and_nonpresident_cannot_expand(self):
  person=self.create()
  with self.assertRaises(PermissionError):self.d.prepare({'source':'No authority to expand the plan'},person)
  self.s.pause(True)
  with self.assertRaises(Invalid):self.prepare()
