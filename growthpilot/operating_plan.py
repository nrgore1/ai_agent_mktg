"""Ninety-day role plans. Automated preparation is distinct from business outcomes."""
import datetime as dt
from zoneinfo import ZoneInfo
from collections import Counter
from .core import Invalid, now, digest
from .business_os import BusinessOS, UNITS, ROLES
from .business_runtime import financial_evidence, vanguard_snapshot

TZ=ZoneInfo('America/New_York')
def today():return dt.datetime.now(TZ).date()
SCOPE='Founder-approved 2026-11-04: verified WeddingOS free tools, free JodiUSA, verified Memoire digital features; OraToPlus qualitative feedback until numeric gates pass; LiqMint Institutional manual evidence-review pilot preparation only; internal products remain private; unclear products remain discovery; provisional costs labelled; no Google Cloud. Existing evidence and action-authorization gates remain.'
# Each phase includes one automated preparation deliverable and one evidence-backed outcome.
OBJECTIVES={
 'CEO':[
 ('Set unit priorities and decision queue','Confirm accountable owners, ranked customer/partner opportunities and a scoped financing objective. Link genuine source records; do not claim a signed pilot or funding.'),
 ('Review pilot and financing progress','Review actual discovery/pilot evidence and financing diligence gaps; record continue, revise or stop decisions without signing commitments.'),
 ('Decide the next quarter','Compare observed results with objectives, choose supported expansion priorities and record unresolved risks and resource decisions.')],
 'CFO':[
 ('Build the evidence and allocation baseline','Tie out available expense/payment evidence and document missing revenue recognition, supplier, support and allocation records. Estimates remain explicitly provisional.'),
 ('Validate scoped offer economics','Reconcile an observed operating period and test offer/partner scenarios against the 75% operating-margin policy or documented funded-free exception. Do not label estimated margins actual.'),
 ('Prepare the quarter close and funding case','Produce source-linked company/unit economics, cash needs and unresolved reconciliation items; owner investment and equipment stay separate from recurring expense.')],
 'CMO':[
 ('Prepare the first qualified acquisition experiment','Define audience, verified value, exact draft, sender, destination, consent and attribution. A researched contact is not a permissioned recipient.'),
 ('Run only eligible acquisition experiments','Record actual authorized delivery, qualified leads and first-value outcomes, or explicitly record no delivery. Existing campaign controls authorize execution.'),
 ('Improve acquisition from observed results','Compare actual activation/conversion and objections by source. Recommend the next experiment; do not invent demand or claim number-one market status.')],
 'CTO':[
 ('Close the highest-risk readiness gap','Reproduce the first applicable P0 acceptance check, attach source/environment-specific evidence and put required product fixes on the separate product backlog.'),
 ('Validate complete operational workflows','Verify applicable signup/internal access, save/return, roles, limits, provider lifecycle and recovery; preserve numeric-grading and live-billing gates.'),
 ('Establish sustainable release operations','Review monitoring, rollback, recovery and recurring regression evidence; resolve remaining critical defects or document the exact dependency and owner.')],
 'COO':[
 ('Prepare the delivery and support baseline','Document onboarding/fulfillment steps, accountable owner, support route and data retention/recovery responsibilities. Verify supplier and delivery assumptions.'),
 ('Validate onboarding and partner delivery','Record real user/tenant or partner pilot feedback and scoped delivery evidence; keep synthetic tests separate from actual adoption.'),
 ('Improve retention and service quality','Review actual support, repeat use, recovery drills and supplier performance. Document improvements and unresolved operational dependencies.')]
}
ROLE_KEYS={
 'CEO':{'identity','partners'},
 'CFO':{'finance','metering','pricing'},
 'CMO':{'claims','campaign','experiment_spec'},
 'CTO':{'health','journey','entitlements','llama_backup','stt_backup','tts_backup'},
 'COO':{'privacy','provider_history_scope','external_retention_inventory','offsite_recovery_rollout','retained_data_review','jodiusa_owner_optin_acceptance'}
}
def role_for(task):
 return next((r for r,keys in ROLE_KEYS.items() if task['key'] in keys),'CTO')
def task_state(t,byid):
 return 'blocked' if t['status']=='pending' and any(byid.get(d,{}).get('status')!='completed' for d in t.get('dependencies',[])) else t['status']

class OperatingPlan:
 def __init__(self,store):self.s=store;self.os=BusinessOS(store)
 def _founder(self,user):
  if user.get('role')!='founder':raise PermissionError('Founder required')
 def prepare(self,data,user):
  self._founder(user)
  if set(data)!={'start_date'}:raise Invalid('Start date required')
  start=dt.date.fromisoformat(data['start_date'])
  if abs((start-today()).days)>31:raise Invalid('Choose a start within 31 days')
  with self.s.db() as db:
   if self.s.paused(db):raise Invalid('Operations paused')
   previous=self.s.rows(db,'operating_program')
   if previous:
    if previous[0]['start_date']!=str(start):raise Invalid('An existing plan cannot be silently rebased')
    return {'id':previous[0]['id'],'created':False}
   program={'id':'operating-90:'+str(start),'start_date':str(start),'end_date':str(start+dt.timedelta(days=89)),'timezone':'America/New_York','enabled':False,'scope':SCOPE,'scope_approved':False,'created_at':now(),'created_by':user['username']}
   self.s.save(db,'operating_program',program)
   for unit in UNITS:
    for role in ROLES:
     pid=digest([program['id'],unit['id'],role])
     tasks=[]
     for phase,(title,acceptance) in enumerate(OBJECTIVES[role]):
      begin=start+dt.timedelta(days=phase*30);end=begin+dt.timedelta(days=29)
      for kind in ('preparation','outcome'):
       tasks.append({'id':pid+':'+str(phase)+':'+kind,'phase':phase+1,'kind':kind,'title':('Prepare evidence: ' if kind=='preparation' else '')+title,'acceptance':'Produce a current, scoped evidence pack with source timestamps, blockers and next actions; this does not certify outcomes.' if kind=='preparation' else acceptance,'start_date':str(begin),'due_date':str(end),'status':'pending','version':1,'evidence':[]})
     self.s.save(db,'operating_plans',{'id':pid,'program_id':program['id'],'company_id':unit['company_id'],'unit_id':unit['id'],'role':role,'name':unit['name']+' / '+role,'accountable_human':'founder','tasks':tasks,'created_at':now()})
   self.s.audit(db,'operating_plan_prepared',program['id'],{'role_plans':35,'days':90,'external_actions':0},user['username'])
   return {'id':program['id'],'created':True}
 def control(self,data,user):
  self._founder(user)
  if set(data)!={'enabled','approve_scope'} or type(data['enabled']) is not bool or type(data['approve_scope']) is not bool:raise Invalid('Explicit control and scope decision required')
  if data['enabled'] and not data['approve_scope']:raise Invalid('Operating scope approval required')
  with self.s.db() as db:
   if self.s.paused(db):raise Invalid('Operations paused')
   programs=self.s.rows(db,'operating_program')
   if not programs:raise Invalid('Prepare plan first')
   p=programs[0];p.update(enabled=data['enabled'],scope_approved=p.get('scope_approved',False) or data['approve_scope'],updated_at=now(),updated_by=user['username'])
   self.s.save(db,'operating_program',p);self.s.audit(db,'operating_plan_control',p['id'],{'enabled':p['enabled'],'scope_approved':p['scope_approved'],'scope':SCOPE,'external_actions':0},user['username'])
   return {'enabled':p['enabled'],'scope_approved':p['scope_approved']}
 def _visible(self,db,user,p):
  unit=self.os._unit(p['unit_id'])
  return p['role'] in self.os._roles(db,user,unit)
 def summary(self,db,user):
  programs=self.s.rows(db,'operating_program');plans=[p for p in self.s.rows(db,'operating_plans') if self._visible(db,user,p)]
  ids={p['id']for p in plans};reports=[r for r in self.s.rows(db,'operating_reports')if r['plan_id'] in ids]
  tasks=self.s.rows(db,'execution_tasks');byid={t['id']:t for t in tasks}
  mappings={pid:u for u in UNITS for pid in u['product_ids']}
  unresolved=[]
  for t in tasks:
   status=task_state(t,byid)
   if status in ('completed','not_applicable'):continue
   unit=mappings.get(t['product_id']);role=role_for(t)
   if user.get('role') not in ('founder','admin') and (not unit or role not in self.os._roles(db,user,unit)):continue
   unresolved.append({'id':t['id'],'product_id':t['product_id'],'unit_id':unit['id'] if unit else None,'company_id':unit['company_id'] if unit else None,'role':role if unit else 'CEO','title':t['title'],'key':t['key'],'priority':t['priority'],'status':status,'acceptance':t['acceptance'],'source':'execution_tasks/'+t['id'],'routing':'mapped_unit' if unit else 'founder_scope_mapping_required','next_action':'Confirm product-to-company/unit mapping before delegation.' if not unit else 'Collect evidence for the existing acceptance criteria; retain dependencies and release controls.'})
  unresolved.sort(key=lambda t:(t['priority'],t['status']!='in_progress',t['product_id'],t['key']))
  return {'program':programs[0] if programs else None,'plans':plans,'reports':sorted(reports,key=lambda r:r['created_at'],reverse=True)[:105],'backlog':unresolved,'counts':dict(Counter(t['status']for p in plans for t in p['tasks'])),'external_execution':False,'note':'Preparation runs automatically at most weekly per role/unit. Milestones require evidence and founder review; this planner never approves or completes execution-backlog tasks.'}
 def _report(self,db,plan,week,phase):
  unit=self.os._unit(plan['unit_id']);role=plan['role']
  tasks=self.s.rows(db,'execution_tasks');byid={t['id']:t for t in tasks}
  scoped=[t for t in tasks if t['product_id'] in unit['product_ids'] and role_for(t)==role]
  rows=[{'id':t['id'],'title':t['title'],'status':task_state(t,byid),'acceptance':t['acceptance'],'updated_at':t.get('updated_at'),'evidence_count':len(t.get('evidence',[])),'source':'execution_tasks/'+t['id']} for t in scoped]
  cases=[c for c in self.s.rows(db,'business_cases')if c['unit_id']==unit['id'] and not c.get('closed') and c['cursor']<len(c['steps']) and c['steps'][c['cursor']]['role']==role]
  refs=[{'id':c['id'],'title':c['title'],'due_date':c['due_date'],'step':c['steps'][c['cursor']]['title'],'status':c['steps'][c['cursor']]['status'],'version':c['version']}for c in cases]
  result={'id':digest([plan['id'],week,phase]),'plan_id':plan['id'],'unit_id':unit['id'],'role':role,'week':week,'phase':phase,'created_at':now(),'mode':'deterministic_evidence_preparation','source_hash':digest([rows,refs]),'readiness':rows,'case_queue':refs,'acceptance':OBJECTIVES[role][phase-1][1],'constraints':unit['constraint'],'external_actions':0,'outcomes_verified':False,'next_actions':[]}
  for t in rows:
   if t['status']not in ('completed','not_applicable'):result['next_actions'].append({'reference':t['source'],'action':t['acceptance']})
  for c in refs:result['next_actions'].append({'reference':'business_cases/'+c['id'],'action':c['step']})
  if role=='CFO':
   finance=financial_evidence(__import__('pathlib').Path(self.s.path).parent,[unit])
   result['finance']={k:finance.get(k) for k in ('status','captured_at','stale','books_finalized','financial_reconciled','missing','units')}
  if role in ('CEO','CMO'):
   snapshot=vanguard_snapshot(__import__('pathlib').Path(self.s.path).parent)
   kinds={'customer','design_partner','champion'}if role=='CMO'else None
   relevant=[r for r in snapshot['records'] if r['unit_id']==unit['id'] and (kinds is None or r['kind']in kinds)]
   result['relationships']={'source_status':snapshot['status'],'captured_at':snapshot['captured_at'],'records':[{'source_ref':r['source_ref'],'stage':r['stage'],'kind':r['kind'],'next_step':r['next_step'],'marketing_eligible':False}for r in relevant][:20],'permission_inferred':False}
  if not result['next_actions']:result['next_actions']=[{'reference':'unit:'+unit['id'],'action':'Confirm baseline, source evidence and accountable owner; no verified outcome is inferred from an empty queue.'}]
  return result
 def tick(self,day=None):
  day=day or today()
  with self.s.db() as db:
   programs=self.s.rows(db,'operating_program')
   if not programs or not programs[0].get('enabled') or not programs[0].get('scope_approved') or self.s.paused(db):return {'status':'paused'}
   program=programs[0];start=dt.date.fromisoformat(program['start_date']);elapsed=(day-start).days
   if elapsed<0:return {'status':'not_started'}
   if elapsed>=90:return {'status':'window_ended','outcomes_completed':False}
   owner=db.execute('SELECT role,enabled FROM users WHERE id=?',(program['created_by'],)).fetchone()
   if not owner or not owner['enabled'] or owner['role']!='founder':return {'status':'owner_unavailable'}
   week=elapsed//7+1;phase=elapsed//30+1
   done={r['id']for r in self.s.rows(db,'operating_reports')}
   for plan in sorted(self.s.rows(db,'operating_plans'),key=lambda p:(p['company_id'],p['unit_id'],p['role'])):
    from .human_ai import active
    if not active(db,self.s,plan['unit_id'],plan['role']):continue
    rid=digest([plan['id'],week,phase])
    if rid in done:continue
    report=self._report(db,plan,week,phase)
    self.s.save(db,'operating_reports',report)
    task=next(t for t in plan['tasks']if t['phase']==phase and t['kind']=='preparation')
    task.update(status='completed',version=task['version']+1)
    task['evidence'].append({'source':'operating_reports/'+rid,'note':'Evidence pack generated and source-linked. No business outcome or execution-backlog task completed.','recorded_at':now()})
    self.s.save(db,'operating_plans',plan)
    self.s.audit(db,'operating_preparation_completed',rid,{'unit_id':plan['unit_id'],'role':plan['role'],'week':week,'phase':phase,'external_actions':0},'operating-plan-worker')
    return {'status':'prepared','plan_id':plan['id'],'report_id':rid}
   return {'status':'current','week':week}
 def record(self,data,user):
  if set(data)!={'plan_id','task_id','version','status','source','note','attest'}:raise Invalid('Exact milestone evidence fields required')
  if data['status'] not in ('in_progress','blocked','ready_for_review','completed'):raise Invalid('Invalid milestone state')
  if not isinstance(data['source'],str) or not 10<=len(data['source'])<=1000 or not isinstance(data['note'],str)or not 30<=len(data['note'])<=4000:raise Invalid('Evidence reference and detailed outcome required')
  with self.s.db() as db:
   if self.s.paused(db):raise Invalid('Operations paused')
   plan=self.s.get(db,'operating_plans',data['plan_id'])
   if user.get('role')=='viewer' or not self._visible(db,user,plan):raise PermissionError('Assigned role required')
   task=next((t for t in plan['tasks']if t['id']==data['task_id']),None)
   if not task or task['kind']!='outcome':raise Invalid('Only outcome milestones accept manual evidence')
   if type(data['version'])is not int or task['version']!=data['version']:raise Invalid('Milestone changed; refresh')
   if task['status']=='completed'and user.get('role')!='founder':raise PermissionError('President must reopen an approved milestone')
   if str(today())<task['start_date']:raise Invalid('Future phase is not active')
   if data['status']=='completed':
    self._founder(user)
    if data['attest']is not True:raise Invalid('Verified acceptance evidence attestation required')
    prep=next(t for t in plan['tasks']if t['phase']==task['phase']and t['kind']=='preparation')
    if prep['status']!='completed':raise Invalid('Prepare current phase evidence first')
    if task['phase']>1:
     unit=self.os._unit(plan['unit_id'])
     relevant=[t for t in self.s.rows(db,'execution_tasks') if t['product_id']in unit['product_ids'] and role_for(t)==plan['role']]
     if not relevant:raise Invalid('No mapped readiness evidence; confirm source and acceptance before completion')
     if any(t['status']not in ('completed','not_applicable')for t in relevant):raise Invalid('Applicable readiness or commercial gates remain open')
    if task['phase']>1 and not all(t['status']=='completed'for t in plan['tasks']if t['phase']<task['phase']and t['kind']=='outcome'):raise Invalid('Prior phase outcomes remain incomplete')
   task.update(status=data['status'],version=task['version']+1)
   task['evidence'].append({'source':data['source'],'note':data['note'],'actor':user['username'],'recorded_at':now(),'attest':data['attest']is True})
   if task['status']!='completed':
    for later in plan['tasks']:
     if later['kind']=='outcome' and later['phase']>task['phase'] and later['status']=='completed':
      later.update(status='blocked',version=later['version']+1)
      later['evidence'].append({'source':task['id'],'note':'Earlier outcome reopened; verify dependent outcome again.','recorded_at':now()})
   self.s.save(db,'operating_plans',plan);self.s.audit(db,'operating_milestone_recorded',task['id'],{'status':task['status'],'external_actions':0,'execution_backlog_changed':False},user['username'])
   return {'id':task['id'],'version':task['version']}
