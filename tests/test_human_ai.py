import json,tempfile,unittest,datetime as dt
from pathlib import Path
from growthpilot.platform import Platform
from growthpilot.identity import Identity
from growthpilot.business_os import BusinessOS,UNITS
from growthpilot.business_runtime import BusinessRuntime,PLANS
from growthpilot.human_ai import HumanAI,target_hash
from growthpilot.role_access import create_account
from growthpilot.operating_plan import OperatingPlan,today
from growthpilot.core import Invalid,now

class HumanAITests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.s=Platform(self.root/'db');self.i=Identity(self.s);self.os=BusinessOS(self.s);self.h=HumanAI(self.s);self.runtime=BusinessRuntime(self.s)
  self.i.create('founder','Synthetic-Founder-Password','founder')
  self.f={'username':'founder','role':'founder','products':[]}
  self.cmo=self.account('CMO');self.ceo=self.account('CEO');self.cfo=self.account('CFO');self.other=self.account('CMO','vireoka')
  (self.root/'vanguard-snapshot.json').write_text(json.dumps({'schema_version':1,'source':'vanguard-gtm','complete':True,'captured_at':now(),'records':[]}))
 def tearDown(self):self.tmp.cleanup()
 def account(self,role,company='atmakosh'):
  name=company+'-'+role.lower();units=[u for u in UNITS if u['company_id']==company]
  create_account(self.i,dict(username=name,password='Synthetic-Role-Password',company=company,business_role=role,units=[u['id']for u in units]),self.f)
  return {'username':name,'role':'business','products':[p for u in units for p in u['product_ids']]}
 def case(self):
  return self.os.dispatch('create',dict(unit_id='weddingos',process='sales',title='Synthetic private opportunity',owner='founder',due_date=str(today()),reference='owner:synthetic'),self.f)
 def selector(self,role,process,facts):return dict(model='ministral-3:3b',choice=1,recommendation=PLANS[role][0],mode='bounded_role_selection')
 def job(self):
  self.case();self.runtime.control({'enabled':True},self.f);self.runtime.tick(self.selector)
  with self.s.db()as db:return self.s.rows(db,'business_agent_jobs')[0]
 def review(self,j,decision='approve',version=0):return dict(kind='job',target_id=j['id'],target_hash=target_hash(j),version=version,decision=decision,note='Reviewed exact synthetic evidence and its limitations.')
 def pair(self,enabled=False,version=0):return dict(unit_id='weddingos',role='CMO',enabled=enabled,version=version,note='President paused this role pending evidence review.')
 def task(self,consequential=False,actor=None):
  return self.h.create_task(dict(unit_id='weddingos',role='CMO',assignee=self.cmo['username'],title='Synthetic manual preparation',instructions='Review the synthetic source and prepare an evidence note.',acceptance='Provide a reference and verified outcome without external sending.',source='synthetic:task',consequential=consequential),actor or self.cmo)
 def action(self,t,action='complete',attest=True):return dict(id=t['id'],version=t['version'],action=action,source='synthetic:evidence',note='Verified the synthetic task evidence and recorded the result.',attest=attest)
 def override(self,c,action='hold',step=0):return dict(kind='case',id=c['id'],version=c['version'],action=action,step=step,note='President override with documented synthetic evidence.')
 def test_pair_scope_and_president_all(self):
  self.assertEqual(len(self.os.summary(self.f)['human_ai']['pairs']),35)
  d=self.os.summary(self.cmo)['human_ai'];self.assertEqual(len(d['pairs']),4)
  self.assertTrue(all(p['role']=='CMO'and p['company_id']=='atmakosh'for p in d['pairs']))
  self.assertNotIn(self.other['username'],str(d))
 def test_review_acceptance_does_not_execute_or_complete(self):
  j=self.job();before=self.s.snapshot();r=self.h.review(self.review(j),self.cmo)
  self.assertEqual(r['version'],1);self.assertEqual(self.os.summary(self.f)['cases'][0]['cursor'],0)
  for k in ('actions','campaigns','deliveries','products'):self.assertEqual(before[k],self.s.snapshot()[k])
  target=next(t for t in self.os.summary(self.cmo)['human_ai']['targets']if t['id']==j['id'])
  self.assertTrue(target['review_current']);self.assertFalse(target['review']['external_execution_authorized'])
 def test_cross_role_and_cross_company_decisions_denied(self):
  j=self.job()
  for u in (self.ceo,self.cfo,self.other):
   with self.assertRaises(PermissionError):self.h.review(self.review(j),u)
 def test_hash_and_version_required(self):
  j=self.job();v=self.review(j)
  with self.assertRaises(Invalid):self.h.review({**v,'target_hash':'wrong'},self.cmo)
  self.h.review(v,self.cmo)
  with self.assertRaises(Invalid):self.h.review(v,self.cmo)
 def test_stale_result_cannot_be_approved_by_president(self):
  j=self.job();c=self.os.summary(self.f)['cases'][0]
  self.os.dispatch('schedule',dict(id=c['id'],version=c['version'],owner='founder',due_date=str(today()+dt.timedelta(days=1))),self.f)
  with self.assertRaises(Invalid):self.h.review(self.review(j),self.f)
 def test_president_supersedes_locks_and_releases_review(self):
  j=self.job();self.h.review(self.review(j),self.cmo)
  self.h.review(self.review(j,'reject',1),self.f)
  with self.assertRaises(PermissionError):self.h.review(self.review(j,'approve',2),self.cmo)
  self.h.review(self.review(j,'release',2),self.f);self.h.review(self.review(j,'approve',3),self.cmo)
  self.assertTrue(self.s.verify_audit()['valid'])
 def test_revision_context_is_fixed_flags_and_old_review_stales(self):
  j=self.job();self.h.review(self.review(j),self.cmo)
  self.h.feedback(dict(job_id=j['id'],target_hash=target_hash(j),focus=2,note='PRIVATE FREE TEXT must remain in the scoped human record.'),self.cmo)
  seen=[]
  def selector(*args):seen.append(args);return self.selector(*args)
  self.assertEqual(self.runtime.tick(selector)['status'],'ready')
  self.assertTrue(seen[0][2]['human_requested_choice_2']);self.assertNotIn('PRIVATE FREE TEXT',str(seen))
  self.assertTrue(all(type(v)is bool for v in seen[0][2].values()))
  t=next(t for t in self.os.summary(self.cmo)['human_ai']['targets']if t['id']==j['id']);self.assertFalse(t['review_current'])
 def test_locked_review_prevents_human_revision(self):
  j=self.job();self.h.review(self.review(j),self.f)
  with self.assertRaises(PermissionError):self.h.feedback(dict(job_id=j['id'],target_hash=target_hash(j),focus=1,note='This attempted revision must not replace President review.'),self.cmo)
 def test_pair_pause_denies_role_and_inflight_result(self):
  self.case();self.runtime.control({'enabled':True},self.f)
  with self.assertRaises(PermissionError):self.h.pair_control(self.pair(),self.cmo)
  def selector(*a):self.h.pair_control(self.pair(),self.f);return self.selector(*a)
  self.assertEqual(self.runtime.tick(selector)['status'],'superseded')
  with self.assertRaises(Invalid):self.h.pair_control(self.pair(),self.f)
 def test_pair_pause_skips_weekly_pack(self):
  self.h.pair_control(self.pair(),self.f);p=OperatingPlan(self.s);p.prepare({'start_date':str(today())},self.f);p.control({'enabled':True,'approve_scope':True},self.f)
  for _ in range(35):p.tick()
  with self.s.db()as db:r=self.s.rows(db,'operating_reports')
  self.assertEqual(len(r),34);self.assertFalse(any(x['unit_id']=='weddingos'and x['role']=='CMO'for x in r))
 def test_manual_execution_requires_evidence_and_version(self):
  t=self.task()
  with self.assertRaises(Invalid):self.h.task_action(self.action(t,attest=False),self.cmo)
  r=self.h.task_action(self.action(t),self.cmo);self.assertEqual(r['version'],2)
  with self.assertRaises(Invalid):self.h.task_action(self.action(t),self.cmo)
  self.assertTrue(self.s.verify_audit()['valid'])
 def test_manual_cross_scope_and_president_only_actions(self):
  t=self.task()
  for u in (self.ceo,self.other):
   with self.assertRaises(PermissionError):self.h.task_action(self.action(t),u)
  with self.assertRaises(PermissionError):self.h.task_action(self.action(t,'hold'),self.cmo)
 def test_manual_consequential_requires_exact_president_authorization(self):
  t=self.task(True)
  with self.assertRaises(Invalid):self.h.task_action(self.action(t,'start'),self.cmo)
  t=self.h.task_action(self.action(t,'authorize'),self.f)
  t=self.h.task_action(self.action(t,'start'),self.cmo)
  self.h.task_action(self.action(t),self.cmo)
 def test_president_rejection_locks_and_reopen_preserves_evidence(self):
  t=self.task();t=self.h.task_action(self.action(t,'reject'),self.f)
  with self.assertRaises(PermissionError):self.h.task_action(self.action(t,'start'),self.cmo)
  t=self.h.task_action(self.action(t,'reopen'),self.f);self.h.task_action(self.action(t),self.cmo)
  with self.s.db()as db:task=self.s.get(db,'human_manual_tasks',t['id'])
  self.assertEqual(len(task['history']),3);self.assertEqual(task['status'],'completed')
 def test_president_hold_revokes_manual_authorization(self):
  t=self.task(True);t=self.h.task_action(self.action(t,'authorize'),self.f)
  t=self.h.task_action(self.action(t,'hold'),self.f);t=self.h.task_action(self.action(t,'reopen'),self.f)
  with self.assertRaises(Invalid):self.h.task_action(self.action(t,'complete'),self.cmo)
 def test_hold_blocks_human_case_and_worker(self):
  c=self.case();self.h.override(self.override(c),self.f)
  with self.assertRaises(PermissionError):self.os.dispatch('record',dict(id=c['id'],version=2,status='in_progress',source='synthetic:evidence',note='Human must not bypass the President hold.'),self.cmo)
  self.runtime.control({'enabled':True},self.f);self.assertEqual(self.runtime.tick(self.selector)['status'],'idle')
  self.assertEqual(self.os.summary(self.f)['cases'][0]['status'],'held')
 def test_case_override_scope_and_cannot_skip_evidence(self):
  c=self.case()
  with self.assertRaises(PermissionError):self.h.override(self.override(c),self.cmo)
  with self.assertRaises(Invalid):self.h.override(self.override(c,'reopen',2),self.f)
 def test_reopen_case_preserves_history_and_resets_dependencies(self):
  c=self.case();c=self.os.dispatch('record',dict(id=c['id'],version=1,status='complete',source='synthetic:evidence',note='Synthetic role work verified and accepted for testing.',attest=True),self.cmo)
  self.h.override(self.override(c,'reopen'),self.f)
  c=self.os.summary(self.f)['cases'][0];self.assertEqual(c['cursor'],0);self.assertTrue(all(s['status']=='pending'for s in c['steps']))
  self.assertEqual(c['history'][-1]['before']['cursor'],1);self.assertTrue(self.s.verify_audit()['valid'])
 def test_ceo_cannot_read_cfo_evidence_or_close_cross_role_case(self):
  c=self.case();c=self.os.dispatch('record',dict(id=c['id'],version=1,status='complete',source='synthetic:evidence',note='Synthetic first task verified for this role access test.',attest=True),self.cmo)
  c=self.os.dispatch('record',dict(id=c['id'],version=c['version'],status='complete',source='synthetic:evidence',note='Synthetic discovery task verified for this role access test.',attest=True),self.ceo)
  self.os.dispatch('record',dict(id=c['id'],version=c['version'],status='in_progress',source='private:ledger',note='PRIVATE CFO DATA must not leak to a CEO role account.'),self.cfo)
  d=self.os.summary(self.ceo);self.assertNotIn('PRIVATE CFO DATA',str(d));self.assertNotIn('finance',d['dashboard_tabs'])
  with self.assertRaises(PermissionError):self.os.dispatch('close',dict(id=c['id'],version=4,note='CEO cannot close work owned by the other roles.'),self.ceo)
 def test_report_review_and_source_change(self):
  p=OperatingPlan(self.s);p.prepare({'start_date':str(today())},self.f);p.control({'enabled':True,'approve_scope':True},self.f)
  for _ in range(35):p.tick()
  report=next(t for t in self.os.summary(self.cmo)['human_ai']['targets']if t['unit_id']=='weddingos')
  v=dict(kind='report',target_id=report['id'],target_hash=report['hash'],version=0,decision='approve',note='Reviewed the exact current preparation pack and evidence.')
  self.h.review(v,self.cmo);self.case()
  with self.assertRaises(Invalid):self.h.review({**v,'version':1},self.f)
if __name__=='__main__':unittest.main()
