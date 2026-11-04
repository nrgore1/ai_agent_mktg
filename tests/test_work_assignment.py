import tempfile,unittest,copy,datetime as dt
from pathlib import Path
from unittest.mock import patch
from growthpilot.platform import Platform
from growthpilot.identity import Identity
from growthpilot.role_access import create_account
from growthpilot.business_os import BusinessOS,UNITS
from growthpilot.operating_plan import OperatingPlan,today
from growthpilot.human_ai import HumanAI
from growthpilot.work_assignment import WorkAssignment,OWNER_ACTIONS
from growthpilot.core import Invalid

class WorkAssignmentTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Platform(Path(self.tmp.name)/'db');self.i=Identity(self.s);self.f={'username':'founder','role':'founder','products':[]};self.i.create('founder','Synthetic-Only-Password','founder')
  self.cmo={'username':'atmakosh.cmo','role':'business','products':[4]}
  create_account(self.i,dict(username='atmakosh.cmo',password='Synthetic-Role-Password',company='atmakosh',business_role='CMO',units=['weddingos']),self.f)
  self.p=OperatingPlan(self.s);self.p.prepare({'start_date':str(today())},self.f);self.p.control({'enabled':True,'approve_scope':True},self.f)
  self.a=WorkAssignment(self.s)
  with self.s.db()as db:
   for t in [dict(id='mapped',product_id=4,key='claims',title='Review verified claims',status='blocked',priority=0,acceptance='Verify each claim against source evidence and limitations.',dependencies=['missing'],evidence=[]),dict(id='unmapped',product_id=9,key='health',title='Private source discovery',status='pending',priority=0,acceptance='Confirm intended runtime and source version.',dependencies=[],evidence=[])]:
    self.s.save(db,'execution_tasks',t)
 def tearDown(self):self.tmp.cleanup()
 def assign(self):return self.a.assign({'source':'User authorized role assignment and current phase preparation.'},self.f)
 def rows(self,kind):
  with self.s.db()as db:return self.s.rows(db,kind)
 def test_assign_every_plan_and_remaining_backlog(self):
  r=self.assign();self.assertEqual(r['assigned_activities'],212);self.assertEqual(r['role_packets_prepared'],35)
  assignments=self.rows('work_assignments');self.assertEqual(len(assignments),212)
  mapped=next(a for a in assignments if a['source_id']=='mapped');self.assertEqual(mapped['human_assignee'],'atmakosh.cmo');self.assertEqual(mapped['ai_assignee'],'weddingos:CMO')
  un=next(a for a in assignments if a['source_id']=='unmapped');self.assertEqual(un['human_assignee'],'founder');self.assertEqual(un['routing'],'president_scope_required')
 def test_only_current_outcome_with_human_owner_starts(self):
  self.assign();plans=self.rows('operating_plans')
  active=[t for p in plans for t in p['tasks']if t['status']=='in_progress'];self.assertEqual(len(active),1);self.assertEqual(active[0]['phase'],1);self.assertEqual(active[0]['kind'],'outcome');self.assertFalse(active[0]['evidence'][0]['attest'])
  self.assertTrue(all(t['status']=='pending'for p in plans for t in p['tasks']if t['phase']>1))
 def test_preserves_backlog_status_and_external_records(self):
  before=self.s.snapshot();original=self.rows('execution_tasks');self.assign()
  for a,b in zip(original,self.rows('execution_tasks')):
   for k in a:self.assertEqual(a[k],b[k])
  for k in ('products','actions','campaigns','deliveries'):self.assertEqual(before[k],self.s.snapshot()[k])
  self.assertTrue(self.s.verify_audit()['valid'])
 def test_idempotent_preserves_human_decisions(self):
  self.assign();tasks=self.rows('human_manual_tasks');t=next(t for t in tasks if t['unit_id']=='weddingos')
  HumanAI(self.s).task_action(dict(id=t['id'],version=t['version'],action='reject',source='synthetic:evidence',note='President rejects this exact preparation for further review.',attest=False),self.f)
  before=self.rows('human_manual_tasks');self.assertFalse(self.assign()['created']);self.assertEqual(self.rows('human_manual_tasks'),before)
 def test_president_only_and_pause(self):
  with self.assertRaises(PermissionError):self.a.assign({'source':'Unauthorized scope assignment attempt'},self.cmo)
  self.s.pause(True)
  with self.assertRaises(Invalid):self.assign()
  self.assertEqual(self.rows('work_assignments'),[])
 def test_pair_pause_prevents_current_phase_start(self):
  HumanAI(self.s).pair_control(dict(unit_id='weddingos',role='CMO',enabled=False,version=0,note='President pauses preparation until the evidence review.'),self.f)
  r=self.assign();self.assertEqual(r['current_outcomes_started'],0);self.assertEqual(r['role_packets_prepared'],34)
 def test_role_scope_hides_president_queue_and_other_roles(self):
  self.assign();d=BusinessOS(self.s).summary(self.cmo)['human_ai']
  self.assertEqual(len(d['work_assignment']['assignments']),7);self.assertEqual(len(d['work_assignment']['reports']),1)
  self.assertTrue(all(t['unit_id']=='weddingos'and t['role']=='CMO'for t in d['manual_tasks']))
  self.assertNotIn('Confirm the home',str(d));self.assertFalse(any(a['source_id']=='unmapped'for a in d['work_assignment']['assignments']))
 def test_president_action_queue_is_exclusive_and_does_not_clear_source(self):
  self.assign();d=BusinessOS(self.s).summary(self.f)['human_ai'];tasks=[t for t in d['manual_tasks']if t['unit_id']=='portfolio'];self.assertEqual(len(tasks),len(OWNER_ACTIONS))
  t=tasks[0];v=dict(id=t['id'],version=t['version'],action='complete',source='synthetic:owner-evidence',note='Synthetic owner evidence verified for this preparation task.',attest=True)
  with self.assertRaises(PermissionError):HumanAI(self.s).task_action(v,self.cmo)
  HumanAI(self.s).task_action(v,self.f)
  self.assertEqual(next(t for t in self.rows('execution_tasks')if t['id']=='unmapped')['status'],'pending')
 def test_evidence_packet_records_missing_dependency_and_source_limits(self):
  self.assign();packet=next(r for r in self.rows('work_dispatch_reports')if r['unit_id']=='weddingos'and r['role']=='CMO')
  self.assertEqual(packet['prioritized_backlog'][0]['unmet_dependencies'],['missing']);self.assertFalse(packet['outcomes_verified']);self.assertEqual(packet['external_actions'],0)
 def test_case_reassignment_preserves_work_and_invalidates_old_version(self):
  case=BusinessOS(self.s).dispatch('create',dict(unit_id='weddingos',process='sales',title='Synthetic customer opportunity',owner='founder',due_date=str(today()),reference='synthetic:opportunity'),self.f)
  r=self.assign();self.assertEqual(r['cases_reassigned'],1)
  current=self.rows('business_cases')[0];self.assertEqual(current['owner'],'atmakosh.cmo');self.assertEqual(current['version'],2);self.assertEqual(current['steps'],case['steps']);self.assertEqual(current['cursor'],0)
  self.assertEqual(current['history'][-1]['previous_owner'],'founder')
 def test_future_program_does_not_start_or_prepare_current_work(self):
  # The source date remains authoritative; do not jump ahead into future phases.
  with patch('growthpilot.work_assignment.today',return_value=today()-dt.timedelta(days=1)):
   r=self.assign()
  self.assertEqual(r['role_packets_prepared'],0);self.assertEqual(r['current_outcomes_started'],0)
if __name__=='__main__':unittest.main()
