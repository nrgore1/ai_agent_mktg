"""Evidence preparation and accountable work routing; never release approval."""
import datetime as dt
from collections import Counter
from .core import Invalid,now,digest
from .business_os import BusinessOS,UNITS,ROLES
from .operating_plan import today,role_for,task_state
from .human_ai import active

POLICY='paired-execution-20261104'
OWNER_ACTIONS=[
 ('people','Activate the ten human role logins','Name the people covering CEO, CFO, CMO, CTO and COO for each company. Set temporary passwords privately through Accounts & integrations and have each person change the password. No password is requested in task evidence.','Record named accountable people and successful individual login handover.'),
 ('scope','Confirm the home of the ten additional portfolio products','Confirm the company, responsible unit and intended private/public scope for Charam, Atmasphere LLM, SDIS, One-Man Hedge Fund, Quantsys, SMDP Design, Stablecoin Pipeline, Vanguard GTM, Vireoka Website and Atmakosh Website. Internal products remain private; unclear products remain discovery.','Record explicit product-to-company/unit decisions before granting role access; this task does not apply those decisions automatically.'),
 ('publishing','Provide owned publishing accounts and the email footer address','Specify the exact social pages/accounts the business controls and the business mailing address for campaign footers. CMO must verify product-specific consent; imported or researched contacts are not permissioned recipients.','Record account names, an approved footer address and links to consent evidence; never credentials. No campaign is sent by completing this task.'),
 ('books','Supply remaining accounting evidence for CFO review','Provide locations of revenue/deferred-revenue records, supplier bills, partner payouts and owner/support time not already in the expense evidence. Existing approved allocations remain provisional; do not repeat the earlier allocation approval.','Link the missing records or explicitly confirm which do not exist, with reporting period and accountable reviewer.'),
 ('postmark','Arrange Postmark account-level retention capability','The retained provider-history gate says the account-level Data Removal API and suitable token are not configured. Have the account owner confirm current availability with Postmark. Provide only a protected secret location if configured; server tokens are insufficient.','Record provider confirmation, account retention settings and the authorized review owner. Do not delete provider records as part of this task.'),
 ('recovery','Confirm backup custody and monitored recovery alerts','Confirm the external-drive custodian, separate recovery-key escrow and monitored alert recipient. The drive repair and restore test already passed; recurring coverage and historical deletion continuity still need evidence.','Record custody/escrow locations without secrets, a monitored address, and the person responsible for recovery drills.'),
 ('jodibana','Review Jodibana operator demo and business settings','Name the reviewer and complete the operator/community demo plus business/tax/privacy and tenant opt-in acceptance review. Preserve free JodiUSA access. Live collection remains disabled until the existing launch gates pass.','Reference the actual owner review and unresolved concerns. This does not activate paid collection or waive provider tests.'),
 ('property','Identify TCompprop operational source records','Provide the system or file locations for properties, leases, maintenance and associated income/cost evidence. The existing TCompprop cases cannot validate unavailable sources.','Record source locations and an accountable operator, without credentials or unnecessary tenant personal data.')
]

class WorkAssignment:
 def __init__(self,store):self.s=store;self.os=BusinessOS(store)
 def _owner(self,db,unit,role):
  candidates=[]
  for a in self.s.rows(db,'business_assignments'):
   if a['unit_id']!=unit['id']or a['role']!=role or not a['enabled']:continue
   row=db.execute('SELECT id,role,products,enabled FROM users WHERE id=?',(a['username'],)).fetchone()
   if row and row['enabled']:
    import json
    if set(unit['product_ids']).issubset(json.loads(row['products'])):candidates.append(row['id'])
  return candidates[0]if len(candidates)==1 else None
 def _manual(self,db,key,unit,role,owner,title,instructions,acceptance,source,priority=1):
  id=digest([POLICY,'manual',key])
  old=next((r for r in self.s.rows(db,'human_manual_tasks')if r['id']==id),None)
  if old:return id,False
  row={'id':id,'unit_id':unit,'role':role,'assignee':owner,'title':title[:160],'instructions':instructions,'acceptance':acceptance,'source':source,'consequential':False,'status':'open','version':1,'created_at':now(),'created_by':'founder','history':[],'evidence':[],'authorization':None,'assignment_policy':POLICY,'priority':priority,'completion_scope':'Evidence preparation only; source readiness and external permissions are unchanged.'}
  self.s.save(db,'human_manual_tasks',row);return id,True
 def assign(self,data,user):
  if user.get('role')!='founder':raise PermissionError('President required')
  if set(data)!={'source'}or not isinstance(data['source'],str)or not 10<=len(data['source'])<=1000:raise Invalid('Assignment authorization source required')
  with self.s.db()as db:
   if self.s.paused(db):raise Invalid('Operations paused')
   programs=self.s.rows(db,'operating_program')
   if not programs or not programs[0].get('scope_approved')or not programs[0].get('enabled'):raise Invalid('Approved active operating plan required')
   existing=self.s.rows(db,'work_assignment_runs')
   if existing:return {'id':existing[0]['id'],'created':False}
   plans=[p for p in self.s.rows(db,'operating_plans')if p['role']in ROLES];backlog=self.s.rows(db,'execution_tasks');byid={t['id']:t for t in backlog}
   units={u['id']:u for u in UNITS};mapping={pid:u for u in UNITS for pid in u['product_ids']}
   products={p['id']:p['name']for p in self.s.rows(db,'products')}
   owners={(u['id'],r):self._owner(db,u,r)for u in UNITS for r in ROLES}
   prepared=0;started=0;manual=0;assigned=0;cases_reassigned=0
   current=str(today());stamp=now()
   for plan in plans:
    unit=units[plan['unit_id']];role=plan['role'];owner=owners[(unit['id'],role)]
    plan['accountable_human']=owner or user['username'];plan['ai_assignee']=unit['id']+':'+role
    for task in plan['tasks']:
     aid=digest([POLICY,'plan',task['id']])
     task.update(human_assignee=plan['accountable_human'],ai_assignee=plan['ai_assignee'],assignment_id=aid)
     self.s.save(db,'work_assignments',{'id':aid,'kind':'plan','source_id':task['id'],'plan_id':plan['id'],'unit_id':unit['id'],'company_id':unit['company_id'],'role':role,'human_assignee':plan['accountable_human'],'ai_assignee':plan['ai_assignee'],'routing':'paired'if owner else'president_owner_required','title':task['title'],'start_date':task['start_date'],'due_date':task['due_date'],'activity_kind':task['kind'],'assigned_at':stamp,'source':data['source']})
     assigned+=1
    self.s.save(db,'operating_plans',plan)
   for task in backlog:
    if task_state(task,byid)in ('completed','not_applicable'):continue
    unit=mapping.get(task['product_id']);role=role_for(task);owner=owners[(unit['id'],role)]if unit else None
    aid=digest([POLICY,'backlog',task['id']])
    row={'id':aid,'kind':'backlog','source_id':task['id'],'product_id':task['product_id'],'unit_id':unit['id']if unit else'portfolio','company_id':unit['company_id']if unit else None,'role':role if unit else'President','proposed_ai_role':role,'human_assignee':owner or user['username'],'ai_assignee':unit['id']+':'+role if unit else'held_pending_unit_mapping','routing':'paired'if unit and owner else'president_scope_required','title':products.get(task['product_id'],str(task['product_id']))+' - '+task['title'],'priority':task['priority'],'assigned_at':stamp,'source':data['source']}
    if unit and owner:
     dependencies=[byid[d]['title']if d in byid else d for d in task.get('dependencies',[])if byid.get(d,{}).get('status')not in ('completed','not_applicable')]
     instructions='Prepare the evidence or product-backlog handoff for this acceptance criterion. Preserve source status '+task['status']+'. '+('Unmet prerequisites: '+ '; '.join(dependencies)+'. 'if dependencies else'')+'Do not treat preparing this task as a passed test, approved offer or executed external action.'
     mid,created=self._manual(db,aid,unit['id'],role,owner,'Evidence handoff: '+row['title'],instructions,task['acceptance'],'execution_tasks/'+task['id'],task['priority']);manual+=created;row['manual_task_id']=mid
    task.update(human_assignee=row['human_assignee'],ai_assignee=row['ai_assignee'],assignment_id=aid)
    self.s.save(db,'execution_tasks',task);self.s.save(db,'work_assignments',row);assigned+=1
   for case in self.s.rows(db,'business_cases'):
    if case.get('closed')or case.get('president_hold')or case['cursor']>=len(case['steps']):continue
    step=case['steps'][case['cursor']]
    if step['status']=='awaiting_review':continue
    owner=owners.get((case['unit_id'],step['role']))
    if not owner or case['owner']==owner:continue
    previous=case['owner'];case['owner']=owner;case['version']+=1;case['updated_at']=stamp
    case.setdefault('history',[]).append({'command':'paired_owner_assignment','actor':user['username'],'at':stamp,'previous_owner':previous,'owner':owner,'version':case['version'],'source':data['source']})
    self.s.save(db,'business_cases',case);cases_reassigned+=1
   # Prepare the current role work packets. Future outcomes are never started.
   for plan in plans:
    unit=units[plan['unit_id']];role=plan['role'];owner=owners[(unit['id'],role)]
    if not active(db,self.s,unit['id'],role):continue
    phase_tasks=[t for t in plan['tasks']if t['start_date']<=current<=t['due_date']]
    if not phase_tasks:continue
    tasks=[t for t in backlog if t['product_id']in unit['product_ids']and role_for(t)==role and task_state(t,byid)not in ('completed','not_applicable')]
    tasks.sort(key=lambda t:(t['priority'],t['status']!='in_progress',t['key'],t['id']))
    rid=digest([POLICY,'packet',plan['id']])
    packet={'id':rid,'unit_id':unit['id'],'role':role,'human_assignee':owner or user['username'],'ai_assignee':plan['ai_assignee'],'created_at':stamp,'mode':'deterministic_scoped_preparation','plan_id':plan['id'],'active_activities':[{'id':t['id'],'title':t['title'],'due_date':t['due_date'],'acceptance':t['acceptance']}for t in phase_tasks],'prioritized_backlog':[{'id':t['id'],'title':products.get(t['product_id'],'')+' - '+t['title'],'priority':t['priority'],'status':task_state(t,byid),'acceptance':t['acceptance'],'unmet_dependencies':[byid[d]['title']if d in byid else d for d in t.get('dependencies',[])if byid.get(d,{}).get('status')not in ('completed','not_applicable')],'evidence_sources':[e.get('source','')for e in t.get('evidence',[])[-2:]],'latest_observation':t.get('evidence',[])[-1].get('note','')if t.get('evidence')else'No recorded evidence.'}for t in tasks],'external_actions':0,'outcomes_verified':False}
    packet['case_queue']=[{'id':c['id'],'title':c['title'],'status':c['steps'][c['cursor']]['status'],'next_action':c['steps'][c['cursor']]['acceptance'],'owner':c['owner']}for c in self.s.rows(db,'business_cases')if c['unit_id']==unit['id']and not c.get('closed')and c['cursor']<len(c['steps'])and c['steps'][c['cursor']]['role']==role]
    packet['source_hash']=digest([packet['active_activities'],packet['prioritized_backlog'],packet['case_queue']])
    self.s.save(db,'work_dispatch_reports',packet);prepared+=1
    if owner:
     for task in phase_tasks:
      if task['kind']=='outcome'and task['status']=='pending':
       task.update(status='in_progress',version=task['version']+1)
       task['evidence'].append({'source':'work_dispatch_reports/'+rid,'note':'Role assignment and source-linked preparation started. Human verification and the business outcome remain outstanding.','actor':'role-preparation-worker','recorded_at':stamp,'attest':False});started+=1
    self.s.save(db,'operating_plans',plan)
   for key,title,instructions,acceptance in OWNER_ACTIONS:
    _,created=self._manual(db,'president:'+key,'portfolio','President',user['username'],title,instructions,acceptance,'owner-action:'+key,0);manual+=created
   run={'id':POLICY,'assigned_at':stamp,'actor':user['username'],'authorization_source':data['source'],'assigned_activities':assigned,'cases_reassigned':cases_reassigned,'role_packets_prepared':prepared,'current_outcomes_started':started,'manual_handoffs_created':manual,'external_actions':0,'outcomes_completed':0}
   self.s.save(db,'work_assignment_runs',run);self.s.audit(db,'paired_work_assigned_and_prepared',POLICY,run,user['username'])
   return {'id':POLICY,'created':True,**run}
 def summary(self,db,user):
  units={u['id']:u for u in UNITS};president=user.get('role')=='founder'
  def visible(r):return president or(r['unit_id']in units and r['role']in self.os._roles(db,user,units[r['unit_id']]))
  plans={t['id']:t for p in self.s.rows(db,'operating_plans')for t in p['tasks']}
  backlog={t['id']:t for t in self.s.rows(db,'execution_tasks')}
  assignments=[]
  for a in self.s.rows(db,'work_assignments'):
   if not visible(a):continue
   source=plans.get(a['source_id'])if a['kind']=='plan'else backlog.get(a['source_id'])
   status=source['status']if source else'source_missing'
   if source and a['kind']=='backlog':status=task_state(source,backlog)
   assignments.append({**a,'source_status':status})
  reports=[r for r in self.s.rows(db,'work_dispatch_reports')if visible(r)]
  return {'assignments':assignments,'reports':reports,'counts':dict(Counter(a['routing']for a in assignments)),'runs':self.s.rows(db,'work_assignment_runs')if president else[],'note':'Assignments and evidence preparation do not pass readiness gates or authorize external execution. Later phases stay scheduled; unmapped products remain in the President discovery queue.'}
