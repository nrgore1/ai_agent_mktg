"""Scoped business operations. Workflow evidence never executes external actions."""
import datetime as dt
import uuid
import json
import copy
from .core import Invalid, now, digest

COMPANIES = [{'id': 'vireoka', 'name': 'Vireoka LLC'}, {'id': 'atmakosh', 'name': 'Atmakosh LLC'}]
UNITS = [
 {'id':'liqmint_individual','company_id':'vireoka','name':'LiqMint Individual','product_ids':[1], 'activation':'A user completes the verified first-use journey; financial actions require separate controls.', 'constraint':'Verify financial claims and product readiness. No autonomous trading, vault deployment or treasury movement.'},
 {'id':'liqmint_institutional','company_id':'vireoka','name':'LiqMint Institutional','product_ids':[2], 'activation':'A qualified institution agrees a scoped demonstration or pilot with measurable success criteria.', 'constraint':'Verify institutional authority, security and applicable compliance. No automatic treasury sweeps.'},
 {'id':'tcompprop','company_id':'vireoka','name':'TCompprop','product_ids':[], 'activation':'A property, lease or maintenance case has a verified owner and documented next action.', 'constraint':'Property integrations are not connected. Lease commitments, legal notices and disbursements need separate authorization.'},
 {'id':'weddingos','company_id':'atmakosh','name':'WeddingOS','product_ids':[4], 'activation':'A registered user saves a useful wedding plan and returns to use it.', 'constraint':'Vendor agreements, bookings, refunds and any escrow capability require verified product/provider support.'},
 {'id':'jodibana','company_id':'atmakosh','name':'Jodibana / JodiUSA','product_ids':[6], 'activation':'A tenant configures its service and an eligible member completes onboarding.', 'constraint':'JodiUSA remains free. Tenant marketing acceptance and member consent are separate. Live collection remains subject to launch gates.'},
 {'id':'oratoplus','company_id':'atmakosh','name':'OraToPlus','product_ids':[3], 'activation':'A learner completes a practice session and receives feedback supported by current quality gates.', 'constraint':'Numeric grades require passing human-reference gates. Model availability is not grading qualification.'},
 {'id':'memoire','company_id':'atmakosh','name':'MemoirBookStudio','product_ids':[5,7], 'activation':'A user saves a book project and reviews its first useful preview.', 'constraint':'Memoir and CoffeeBook share this unit. Printing, shipping, rights and fulfillment costs must be verified; no automatic print orders.'}
]
ROLES = {
 'CEO': 'Priorities, objectives, relationships and accountable business reviews',
 'CFO': 'Cost and revenue reconciliation, pricing analysis, budgets and financial evidence',
 'CMO': 'Customer research, campaigns, sales qualification and acquisition measurement',
 'CTO': 'Product readiness, engineering requests, release evidence and technical risk',
 'COO': 'Onboarding, customer success, service delivery, vendors and incidents'
}

from .saas_roles import SAAS_ROLES, saas_processes
ACCESS_ROLES={**ROLES,**SAAS_ROLES}

def step(title, role, acceptance, gate=False):
 return {'title':title,'role':role,'acceptance':acceptance,'approval_required':gate}

PROCESSES = {
 'sales': {'name':'Sales opportunity to activation','lane':'Sales','steps':[
  step('Qualify opportunity','CMO','Record source, problem, buyer, fit and appropriate contact permission.'),
  step('Validate needs and success criteria','CEO','Record discovery evidence, decision-maker and measurable customer outcome.'),
  step('Check offer economics','CFO','Reference exact scope, net revenue, costs and commission assumptions; validate the 75% policy or documented free-service exception.'),
  step('Review proposed offer','CEO','Reference exact offer, commitments and applicable commercial gates. This review does not sign a contract.',True),
  step('Record customer decision and activation','COO','Record the actual customer outcome and first meaningful experience; do not count a proposal as a sale.') ]},
 'marketing': {'name':'Campaign research to measured learning','lane':'Marketing','steps':[
  step('Define audience and evidence','CMO','Specify customer problem, supported claims, channel and product-specific permission.'),
  step('Prepare exact campaign package','CMO','Link the AgentVire campaign and exact draft actions, sender and destinations.'),
  step('Check cost and attribution','CFO','Record costs, attribution plan, margin assumptions and stop conditions.'),
  step('Review campaign handoff','CEO','Check readiness and exact-action eligibility. Publishing still uses the existing Approvals desk.',True),
  step('Record results and next experiment','CMO','Reference actual delivery, activation and conversion evidence, or document that nothing was sent.') ]},
 'partnership': {'name':'Partner discovery to pilot review','lane':'Sales','steps':[
  step('Qualify partner and mutual value','CEO','Record partner identity, relevance, relationship source and proposed mutual benefit.'),
  step('Scope pilot and delivery','COO','Name owners, deliverables, dates and success/exit criteria.'),
  step('Validate partner economics','CFO','Specify attributed net collected revenue, refunds, costs and proposed commissions; do not promise investment-finder compensation.'),
  step('Review proposed commitment','CEO','Reference exact proposed agreement and legal entity. Signing and payments remain separate actions.',True),
  step('Review attributable pilot results','COO','Record real partner/customer outcomes and recommendation to expand, revise or stop.') ]},
 'financing': {'name':'Financing readiness and investor follow-up','lane':'Sales','steps':[
  step('Define entity and funding objective','CEO','Identify Vireoka LLC or Atmakosh LLC, purpose, amount and financing route without assuming an offering exemption.'),
  step('Prepare reconciled evidence','CFO','Reference financial period, cash, liabilities, ownership records and use-of-funds assumptions; mark missing data.'),
  step('Qualify relationship and introduction','CEO','Reference Vanguard opportunity and genuine introduction path; imported contacts are not permission.'),
  step('Review materials and proposed outreach','CEO','Review claims, recipient and applicable professional/legal review before any external handoff.',True),
  step('Record meeting and diligence outcome','CEO','Record actual meeting, diligence request or decision. A draft or expression of interest is not committed capital.') ]},
 'onboarding': {'name':'Onboarding and customer success','lane':'Operations','steps':[
  step('Confirm customer scope and permissions','COO','Record product/tenant, eligibility, requested outcome and necessary permissions.'),
  step('Verify activation readiness','CTO','Reference tested signup, entitlement and first-use behavior for this product.'),
  step('Guide first meaningful use','COO','Reference observed customer activation, with minimal personal data.'),
  step('Follow up on retention and feedback','CMO','Record return usage, objections and permitted follow-up.'),
  step('Review success or escalation','COO','Record actual success, next action or linked support case.') ]},
 'support': {'name':'Support and service recovery','lane':'Operations','steps':[
  step('Triage request and impact','COO','Record customer scope, severity, owner and response due date without secrets.'),
  step('Investigate and prepare remedy','CTO','Reference diagnosis and a scoped remedy; product fixes belong in the product backlog.'),
  step('Review consequential remedy','COO','Review proposed refund, account change or commitment. Execution requires its own applicable controls.',True),
  step('Verify resolution','COO','Reference actual resolution and customer communication evidence; unsupported provider deletion stays open.'),
  step('Record prevention and follow-up','CTO','Link regression coverage, operational improvement and remaining limitations.') ]},
 'vendor': {'name':'Vendor procurement and fulfillment','lane':'Operations','steps':[
  step('Specify delivery need','COO','Record required service, acceptance, supplier identity and legal entity.'),
  step('Compare scope and total costs','CFO','Include tax treatment, delivery, support, refunds and any physical production costs.'),
  step('Review supplier commitment','CEO','Reference exact contract/order and funding authority. No purchase or payment is executed here.',True),
  step('Verify delivery and invoice','COO','Reference actual delivery, defects, invoice and acceptance evidence.'),
  step('Reconcile and assess supplier','CFO','Match approved scope, delivery and invoice; record disputes and separate payment receipt if available.') ]},
 'finance': {'name':'Financial close and margin review','lane':'Finance','steps':[
  step('Collect source records','CFO','Identify period, currency, company and source records; distinguish cash, revenue and deferred revenue.'),
  step('Reconcile and allocate costs','CFO','Document allocation basis, equipment treatment, shared costs and unresolved differences.'),
  step('Review margin scenarios','CFO','Compare actuals and assumptions; keep founder recovery separate and free offers explicitly funded.'),
  step('Review financial recommendation','CEO','Reference precise budget, pricing or commission recommendation and unresolved validation.',True),
  step('Record approved handoff and review date','CFO','Record destination, exact scope and next review; no ledger posting, price change or payout is implied.') ]},
 'engineering': {'name':'Product change and release readiness','lane':'Technology','steps':[
  step('Define change and product backlog','CTO','Link separate product issue, customer impact, acceptance and scope.'),
  step('Prepare implementation evidence','CTO','Reference Veda/engineering work, commit and tests; do not claim workers are connected unless verified.'),
  step('Verify operational readiness','COO','Record backup, rollback, monitoring and affected customer journey.'),
  step('Review production handoff','CTO','Reference exact release and deployment authorization. This case cannot deploy software.',True),
  step('Record deployment verification','CTO','Reference actual deployment receipt and post-deployment checks, or explicitly record that deployment is held.') ]},
 'incident': {'name':'Incident response and recovery','lane':'Operations','steps':[
  step('Record impact and contain within authority','COO','Record incident time, unit, impact and existing safe containment actions.'),
  step('Diagnose and prepare recovery','CTO','Reference Kairo/operator evidence, recovery plan and data-loss risks.'),
  step('Review consequential recovery','CEO','Review exact proposed restoration or production change; emergency actions follow separately established authority.',True),
  step('Verify recovery and reconciliation','CTO','Reference service checks, restored data, privacy journals and unresolved provider state.'),
  step('Review incident and prevention','COO','Document cause, recovery timings and follow-up ownership.') ]}
}

PROCESSES.update(saas_processes(step))

class BusinessOS:
 def __init__(self, store): self.store=store
 def _unit(self, unit_id):
  unit=next((u for u in UNITS if u['id']==unit_id),None)
  if unit is None: raise Invalid('Unknown business unit')
  return unit
 def _privileged(self, user): return user.get('role') in ('founder','admin')
 def _roles(self, db, user, unit):
  if self._privileged(user): return list(ACCESS_ROLES)
  # Grants do not broaden existing product access; every product in a unit is required.
  if not set(unit['product_ids']).issubset(set(user.get('products',[]))): return []
  rows=self.store.rows(db,'business_assignments')
  return sorted({r['role'] for r in rows if r['username']==user['username'] and r['unit_id']==unit['id'] and r['enabled']})
 def _access(self, db, user, unit, role=None):
  roles=self._roles(db,user,unit)
  if not roles or (role and role not in roles): raise PermissionError('Business-unit role access denied')
  if role and user.get('role')=='viewer': raise PermissionError('Read-only account')
  return roles
 def _text(self, data, key, minimum=1, maximum=2000):
  value=data.get(key)
  if not isinstance(value,str) or not minimum<=len(value.strip())<=maximum: raise Invalid('Valid '+key+' required')
  return value.strip()
 def _due(self, value):
  if not isinstance(value,str): raise Invalid('Due date required')
  try: dt.date.fromisoformat(value)
  except ValueError: raise Invalid('Due date must be YYYY-MM-DD')
  return value
 def _fields(self, data, fields):
  if not isinstance(data,dict) or set(data)-set(fields): raise Invalid('Unsupported business operation fields')
 def _status(self, case):
  if case.get('closed'): return 'closed'
  if case.get('president_hold'): return 'held'
  if case['cursor']==len(case['steps']): return 'completed'
  return case['steps'][case['cursor']]['status']
 def summary(self,user):
  with self.store.db() as db:
   units=[dict(u,roles=self._roles(db,user,u)) for u in UNITS if self._roles(db,user,u)]
   ids={u['id'] for u in units}; pids={p for u in units for p in u['product_ids']}
   cases=[dict(c,status=self._status(c)) for c in self.store.rows(db,'business_cases') if c['unit_id'] in ids]
   for c in cases:
    current=c['steps'][c['cursor']] if c['cursor']<len(c['steps']) else None
    c['can_work']=bool((not c.get('president_hold') or user['role']=='founder') and current and current['role'] in self._roles(db,user,self._unit(c['unit_id'])) and user['role']!='viewer' and not c.get('closed'))
   leads=[x for x in self.store.rows(db,'leads') if x.get('product_id') in pids]
   campaigns=[x for x in self.store.rows(db,'campaigns') if x.get('product_id') in pids]
   actions=[x for x in self.store.rows(db,'actions') if x.get('product_id') in pids]
   tasks=[x for x in self.store.rows(db,'execution_tasks') if x.get('product_id') in pids]
   assignments=[r for r in self.store.rows(db,'business_assignments') if r['unit_id'] in ids and (self._privileged(user) or r['username']==user['username'])]
   for u in units:
    scoped=[c for c in cases if c['unit_id']==u['id']]
    u['metrics']={'open_cases':sum(c['status'] not in ('completed','closed') for c in scoped), 'decisions':sum(c['status']=='awaiting_review' for c in scoped),
     'leads':sum(x.get('product_id') in u['product_ids'] for x in leads),'campaigns':sum(x.get('product_id') in u['product_ids'] for x in campaigns),
     'readiness_open':sum(x.get('product_id') in u['product_ids'] and x.get('status')!='completed' for x in tasks),
     'actual_revenue':None,'actual_margin':None}
   users=[{'username':r['id'],'role':r['role'],'products':__import__('json').loads(r['products'])} for r in db.execute('SELECT id,role,products FROM users WHERE enabled=1')] if user['role']=='founder' else []
   mapped={p for u in UNITS for p in u['product_ids']}
   unmapped=[{'id':p['id'],'name':p['name']} for p in self.store.rows(db,'products') if p['id'] not in mapped] if self._privileged(user) else []
   result={'companies':[c for c in COMPANIES if any(u['company_id']==c['id'] for u in units)],'units':units,'roles':ACCESS_ROLES,'processes':PROCESSES,'cases':sorted(cases,key=lambda c:c['updated_at'],reverse=True),
    'assignments':assignments,'users':users,'unmapped_products':unmapped,'paused':self.store.paused(db),'as_of':now(),
    'marketing_decisions':[{'id':a['id'],'product_id':a['product_id'],'status':a['status']} for a in actions if a['status'] in ('pending','approved','queued','unknown')],
    'connections':[{'name':'AgentVire campaigns, pipelines and readiness','status':'Local records','note':'Current records are read directly. Campaign publishing retains its existing controls.'},
     {'name':'Vanguard GTM','status':'Manual handoff','note':'Reference the opportunity in case evidence. Automatic synchronization is not connected.'},
     {'name':'Accounting and company P&L','status':'Not connected','note':'Actual revenue, cash and margin are unknown here until reconciled accounting is connected.'},
     {'name':'Product services, Veda and Kairo','status':'Evidence handoff','note':'Track requests and receipts. This workspace does not provision tenants, execute code, deploy or move money.'},
     {'name':'Local AI executive agents','status':'Workflow roles only','note':'These are deterministic role workflows, not autonomous executive model workers. Existing qualified local-model features remain separate.'}],
    'external_execution':False,'can_assign':user['role']=='founder','can_review':user['role']=='founder',
    'note':'Case completion records an attested workflow outcome, not product launch approval, a sent campaign, a signed contract or a settled payment.'}
   from .business_runtime import BusinessRuntime
   from .operating_plan import OperatingPlan
   result['operating_plan']=OperatingPlan(self.store).summary(db,user)
   from .role_access import scope_summary
   result=BusinessRuntime(self.store).enrich(db,user,result)
   from .human_ai import HumanAI
   result['human_ai']=HumanAI(self.store).summary(db,user,result)
   return scope_summary(user,result)
 def dispatch(self,command,data,user):
  if user.get('role')=='viewer': raise PermissionError('Read-only account')
  with self.store.db() as db:
   if command=='assign':
    self._fields(data,{'username','unit_id','role','enabled'})
    if user['role']!='founder': raise PermissionError('Founder required for role assignments')
    unit=self._unit(data.get('unit_id')); role=data.get('role')
    if role not in ACCESS_ROLES or type(data.get('enabled')) is not bool: raise Invalid('Valid role and enabled flag required')
    target=db.execute('SELECT role,products FROM users WHERE id=? AND enabled=1',(data.get('username'),)).fetchone()
    if not target: raise Invalid('Enabled user required')
    if target['role'] not in ('founder','admin') and not set(unit['product_ids']).issubset(set(__import__('json').loads(target['products']))): raise Invalid('Assign product access in Accounts first; all unit products are required')
    row={'id':digest([data['username'],unit['id'],role]),**data,'company_id':unit['company_id'],'updated_at':now()}
    self.store.save(db,'business_assignments',row);self.store.audit(db,'business_role_assignment',row['id'],{'unit_id':unit['id'],'username':data['username'],'role':role,'enabled':data['enabled']},user['username']);return row
   if self.store.paused(db): raise Invalid('Operations paused')
   if command=='create':
    self._fields(data,{'unit_id','process','title','owner','due_date','reference','tenant_ref'})
    unit=self._unit(data.get('unit_id')); process=PROCESSES.get(data.get('process'))
    if process is None: raise Invalid('Unknown process')
    self._access(db,user,unit,process['steps'][0]['role'])
    owner=self._text(data,'owner',1,80)
    ownerrow=db.execute('SELECT id,role,products FROM users WHERE id=? AND enabled=1',(owner,)).fetchone()
    if not ownerrow: raise Invalid('An enabled AgentVire account must own this case')
    owneruser={'username':ownerrow['id'],'role':ownerrow['role'],'products':__import__('json').loads(ownerrow['products'])}
    self._access(db,owneruser,unit,process['steps'][0]['role'])
    case={'id':uuid.uuid4().hex,'unit_id':unit['id'],'company_id':unit['company_id'],'process':data['process'],'title':self._text(data,'title',5,160),
     'owner':owner,'due_date':self._due(data.get('due_date')),'reference':self._text(data,'reference',5,1000),'tenant_ref':str(data.get('tenant_ref',''))[:120],
     'cursor':0,'version':1,'created_at':now(),'updated_at':now(),'steps':[dict(s,status='pending') for s in process['steps']]}
    self.store.save(db,'business_cases',case);self.store.audit(db,'business_case_created',case['id'],{'unit_id':unit['id'],'process':data['process']},user['username']);return case
   if command not in ('record','review','schedule','close'): raise Invalid('Unknown business operation')
   allowed={'id','version','status','source','note','attest'} if command=='record' else {'id','version','decision','proposal_hash','note'} if command=='review' else {'id','version','owner','due_date'} if command=='schedule' else {'id','version','note'}
   self._fields(data,allowed)
   case=self.store.get(db,'business_cases',data.get('id'));unit=self._unit(case['unit_id']);self._access(db,user,unit)
   if type(data.get('version')) is not int or case['version']!=data['version']: raise Invalid('Case changed; refresh before continuing')
   if case.get('closed') or case['cursor']>=len(case['steps']): raise Invalid('Case is already closed or completed')
   current=case['steps'][case['cursor']]
   if case.get('president_hold') and user['role']!='founder':raise PermissionError('President holds this case')
   if command=='schedule':
    self._access(db,user,unit,current['role'])
    owner=self._text(data,'owner',1,80);row=db.execute('SELECT id,role,products FROM users WHERE id=? AND enabled=1',(owner,)).fetchone()
    if not row: raise Invalid('An enabled account must own the next action')
    self._access(db,{'username':row['id'],'role':row['role'],'products':__import__('json').loads(row['products'])},unit,current['role'])
    case.update(owner=owner,due_date=self._due(data.get('due_date')))
   elif command=='close':
    if user['role']!='founder':raise PermissionError('President required to close a cross-role case')
    self._access(db,user,unit,'CEO');case.update(closed=True,close_note=self._text(data,'note',20),closed_by=user['username'])
   elif command=='review':
    if user['role']!='founder': raise PermissionError('Founder decision required')
    if current['status']!='awaiting_review' or not current['approval_required']: raise Invalid('No decision is awaiting review')
    if data.get('proposal_hash')!=current.get('proposal_hash'): raise Invalid('Exact current proposal required')
    if dt.datetime.fromisoformat(current['expires_at'])<=dt.datetime.now(dt.timezone.utc): raise Invalid('Proposal review expired; record a fresh proposal')
    if data.get('decision') not in ('accept','return'): raise Invalid('Accept or return decision required')
    current['decision']={'actor':user['username'],'at':now(),'note':self._text(data,'note',20),'decision':data['decision'],'proposal_hash':current['proposal_hash'],'scope':'workflow_handoff_only'}
    current['status']='completed' if data['decision']=='accept' else 'blocked'
    if current['status']=='completed': case['cursor']+=1
   else:
    self._access(db,user,unit,current['role'])
    status=data.get('status')
    if status not in ('in_progress','blocked','complete'): raise Invalid('Invalid workflow status')
    note=self._text(data,'note',20,4000);source=self._text(data,'source',5,1000)
    if status=='complete' and data.get('attest') is not True: raise Invalid('Evidence verification attestation required')
    # Every new record invalidates any prior decision and binds fresh evidence.
    current.pop('decision',None);current.pop('proposal_hash',None);current.pop('expires_at',None)
    current.update(note=note,source=source,recorded_by=user['username'],recorded_at=now(),status=status)
    if status=='complete':
     if current['approval_required']:
      current['status']='awaiting_review';current['proposal_hash']=digest({'case':case['id'],'unit':unit['id'],'step':case['cursor'],'version':case['version']+1,'source':source,'note':note})
      current['expires_at']=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=24)).isoformat()
     else: current['status']='completed';case['cursor']+=1
   case.setdefault('history',[]).append({'command':command,'actor':user['username'],'at':now(),'version':case['version']+1,'input':copy.deepcopy(data)})
   case['version']+=1;case['updated_at']=now()
   self.store.save(db,'business_cases',case);self.store.audit(db,'business_'+command,case['id'],{'unit_id':unit['id'],'version':case['version'],'cursor':case['cursor'],'status':self._status(case),'record_hash':digest(case)},user['username'])
   return case
