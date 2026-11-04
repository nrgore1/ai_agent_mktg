"""Human counterparts, evidence-bound decisions, manual work and President overrides."""
import copy,json,uuid
from .core import Invalid,now,digest
from .business_os import BusinessOS,UNITS,ROLES,ACCESS_ROLES

def control(db,store,unit,role):
 return next((r for r in store.rows(db,'human_ai_controls')if r['unit_id']==unit and r['role']==role),{'id':digest([unit,role]),'unit_id':unit,'role':role,'enabled':True,'version':0})
def active(db,store,unit,role):return control(db,store,unit,role)['enabled']
def task_hash(t):return digest({k:t[k]for k in ('unit_id','role','title','instructions','acceptance','assignee','consequential')})
def target_hash(target):return digest({k:v for k,v in target.items()if k not in ('stale','can_review')})

class HumanAI:
 def __init__(self,store):self.s=store;self.os=BusinessOS(store)
 def _president(self,user):
  if user.get('role')!='founder':raise PermissionError('President required')
 def _access(self,db,user,unit,role):
  if unit=='portfolio'and role=='President':
   self._president(user);return
  if user.get('role')=='viewer':raise PermissionError('Read-only account')
  if role not in ACCESS_ROLES:raise Invalid('Unknown work role')
  if role=='AUDITOR'and user.get('role')not in ('founder','admin'):raise PermissionError('Auditor evidence is read only')
  self.os._access(db,user,self.os._unit(unit),role)
 def _fields(self,data,fields):
  if not isinstance(data,dict)or set(data)!=set(fields):raise Invalid('Exact request fields required')
 def _text(self,data,key,minimum=10,maximum=2000):
  v=data.get(key)
  if not isinstance(v,str)or not minimum<=len(v.strip())<=maximum:raise Invalid('Detailed '+key+' required')
  return v.strip()
 def _version(self,data,row):
  if type(data.get('version'))is not int or data['version']!=row.get('version',0):raise Invalid('Record changed; refresh before deciding')
 def _resolve(self,db,kind,id):
  if kind not in ('job','report'):raise Invalid('Choose an AI result or evidence pack')
  target=self.s.get(db,'business_agent_jobs'if kind=='job'else'operating_reports',id)
  unit=target['unit_id'];role=target['role'];stale=False
  if kind=='job':
   from .business_runtime import BusinessRuntime,vanguard_snapshot,financial_evidence
   runtime=BusinessRuntime(self.s);case=self.s.get(db,'business_cases',target['case_id'])
   stale=target['status']!='ready' or case['version']!=target['case_version']or case.get('closed')or case['cursor']>=len(case['steps'])
   if not stale:
    context=runtime._context(db,case,vanguard_snapshot(runtime.directory),financial_evidence(runtime.directory,[]))
    stale=context['blocked']or not context['authorized']or context['input_hash']!=target['input_hash']
  else:
   from .operating_plan import OperatingPlan
   plan=self.s.get(db,'operating_plans',target['plan_id'])
   reports=[r for r in self.s.rows(db,'operating_reports')if r['plan_id']==target['plan_id']]
   stale=any(r['created_at']>target['created_at']for r in reports)
   current=OperatingPlan(self.s)._report(db,plan,target['week'],target['phase'])
   stale=stale or current['source_hash']!=target['source_hash']
   if 'finance'in target:stale=stale or current.get('finance')!=target['finance']
   if 'relationships'in target:
    clean=lambda v:{k:x for k,x in v.items()if k!='captured_at'}
    stale=stale or clean(current.get('relationships',{}))!=clean(target['relationships'])
  return target,unit,role,bool(stale)
 def summary(self,db,user,result):
  pairs=[];allowed=set()
  for unit in result['units']:
   for role in unit['roles']:
    allowed.add((unit['id'],role))
    people=[]
    for a in self.s.rows(db,'business_assignments'):
     if a['unit_id']==unit['id']and a['role']==role and a['enabled']:
      r=db.execute('SELECT id,enabled,products FROM users WHERE id=?',(a['username'],)).fetchone()
      if r and r['enabled']and set(unit['product_ids']).issubset(json.loads(r['products'])):people.append(r['id'])
    if role not in ROLES and not people and not any(p.get('department_policy')and p['unit_id']==unit['id']and p['role']==role for p in self.s.rows(db,'operating_plans')):continue
    pairs.append({'ai_preparation':role in ROLES,'unit_id':unit['id'],'unit_name':unit['name'],'company_id':unit['company_id'],'role':role,'human_accounts':sorted(people),'control':control(db,self.s,unit['id'],role)})
  def visible(r):return (r['unit_id'],r['role'])in allowed or(user.get('role')=='founder'and r['unit_id']=='portfolio'and r['role']=='President')
  reviews=[r for r in self.s.rows(db,'human_ai_reviews')if visible(r)]
  targets=[]
  for kind,rows in [('job',result['role_workers']['jobs']),('report',result['operating_plan']['reports'])]:
   for row in rows:
    if not visible(row)or row['role']not in ROLES:continue
    if kind=='job':stale=row.get('stale',True)or row['status']!='ready'
    else:
     _,_,_,stale=self._resolve(db,kind,row['id'])
    review=next((r for r in reviews if r['kind']==kind and r['target_id']==row['id']),None)
    h=target_hash(row)
    targets.append({'id':row['id'],'kind':kind,'unit_id':row['unit_id'],'role':row['role'],'hash':h,'stale':bool(stale),'title':(row.get('result')or {}).get('recommendation')or row.get('acceptance')or row.get('error')or 'AI preparation','evidence':row.get('next_actions',[]) if kind=='report' else [{'reference':row.get('source_ref',''),'action':(row.get('result')or {}).get('recommendation','')}],'review':review,'review_current':bool(review and review.get('target_hash')==h and not stale)})
  from .business_runtime import PLANS
  from .work_assignment import WorkAssignment
  return {'work_assignment':WorkAssignment(self.s).summary(db,user),'focus_options':{r:PLANS[r]for _,r in allowed if r in PLANS},'pairs':pairs,'targets':targets,'reviews':reviews,'manual_tasks':[r for r in self.s.rows(db,'human_manual_tasks')if visible(r)],'feedback':[r for r in self.s.rows(db,'human_ai_feedback')if visible(r)],'is_president':user.get('role')=='founder','note':'Approve/reject only your paired AI role. Approval is internal acceptance, not an external execution receipt. Manual work requires evidence. President decisions are locked until the President releases them; original history is retained.'}
 def review(self,data,user):
  self._fields(data,{'kind','target_id','target_hash','version','decision','note'})
  if data['decision']not in ('approve','reject','release'):raise Invalid('Invalid review decision')
  note=self._text(data,'note',20)
  with self.s.db()as db:
   target,unit,role,stale=self._resolve(db,data['kind'],data['target_id']);self._access(db,user,unit,role)
   rid=digest([data['kind'],data['target_id']]);old=next((r for r in self.s.rows(db,'human_ai_reviews')if r['id']==rid),{'version':0,'history':[]})
   self._version(data,old)
   if old.get('president_locked')and user['role']!='founder':raise PermissionError('President decision is locked')
   if data['target_hash']!=target_hash(target):raise Invalid('Exact current AI artifact required')
   if data['decision']=='release':self._president(user)
   if data['decision']=='approve'and(stale or self.s.paused(db)or not active(db,self.s,unit,role)):raise Invalid('Stale or paused AI result cannot be approved')
   row={'id':rid,'kind':data['kind'],'target_id':target['id'],'target_hash':data['target_hash'],'unit_id':unit,'role':role,'version':old['version']+1,'decision':data['decision'],'note':note,'actor':user['username'],'updated_at':now(),'president_locked':user['role']=='founder'and data['decision']!='release','history':old['history']+[{k:v for k,v in old.items()if k!='history'}],'external_execution_authorized':False}
   self.s.save(db,'human_ai_reviews',row);self.s.audit(db,'human_ai_review',rid,{'decision':data['decision'],'role':role,'unit_id':unit,'president_override':user['role']=='founder','prior_version':old['version'],'external_actions':0},user['username'])
   return {'id':rid,'version':row['version']}
 def feedback(self,data,user):
  self._fields(data,{'job_id','target_hash','focus','note'})
  if type(data['focus'])is not int or data['focus']not in (1,2,3):raise Invalid('Choose one of the three qualified action focuses')
  note=self._text(data,'note',20)
  with self.s.db()as db:
   target,unit,role,stale=self._resolve(db,'job',data['job_id']);self._access(db,user,unit,role)
   if stale or data['target_hash']!=target_hash(target):raise Invalid('Current AI recommendation required')
   if self.s.paused(db)or not active(db,self.s,unit,role):raise Invalid('AI preparation paused')
   review=next((r for r in self.s.rows(db,'human_ai_reviews')if r['kind']=='job'and r['target_id']==target['id']),{})
   if review.get('president_locked')and user['role']!='founder':raise PermissionError('President decision is locked')
   case=self.s.get(db,'business_cases',target['case_id'])
   if case.get('president_hold'):raise Invalid('President holds this case')
   row={'id':uuid.uuid4().hex,'job_id':target['id'],'unit_id':unit,'role':role,'focus':data['focus'],'note':note,'actor':user['username'],'created_at':now(),'response_mode':'bounded_local_revision_requested','free_text_sent_to_model':False}
   case['human_ai_feedback']={'role':role,'focus':data['focus'],'feedback_id':row['id']}
   case['version']+=1;case['updated_at']=now()
   self.s.save(db,'business_cases',case);self.s.save(db,'human_ai_feedback',row)
   self.s.audit(db,'human_ai_revision_requested',row['id'],{'case_id':case['id'],'role':role,'focus':data['focus'],'external_actions':0},user['username'])
   return {'id':row['id'],'version':case['version']}
 def pair_control(self,data,user):
  self._president(user);self._fields(data,{'unit_id','role','enabled','version','note'})
  if data['role']not in ROLES:raise Invalid('Choose an AI unit role')
  if type(data['enabled'])is not bool:raise Invalid('Enabled must be boolean')
  note=self._text(data,'note',20)
  with self.s.db()as db:
   self._access(db,user,data['unit_id'],data['role']);old=control(db,self.s,data['unit_id'],data['role']);self._version(data,old)
   row={**old,'enabled':data['enabled'],'version':old['version']+1,'note':note,'actor':user['username'],'updated_at':now()}
   self.s.save(db,'human_ai_controls',row);self.s.audit(db,'president_pair_control',row['id'],{'unit_id':row['unit_id'],'role':row['role'],'enabled':row['enabled'],'note':note},user['username'])
   return {'id':row['id'],'version':row['version']}
 def create_task(self,data,user):
  self._fields(data,{'unit_id','role','assignee','title','instructions','acceptance','source','consequential'})
  if type(data['consequential'])is not bool:raise Invalid('Consequential classification required')
  with self.s.db()as db:
   if self.s.paused(db):raise Invalid('Operations paused')
   self._access(db,user,data['unit_id'],data['role'])
   if user['role']!='founder'and data['assignee']!=user['username']:raise PermissionError('Assign your own manual work; President can delegate')
   assigned=db.execute('SELECT id,role,products FROM users WHERE id=? AND enabled=1',(data['assignee'],)).fetchone()
   if not assigned:raise Invalid('Enabled assignee required')
   self._access(db,{'username':assigned['id'],'role':assigned['role'],'products':json.loads(assigned['products'])},data['unit_id'],data['role'])
   row={'id':uuid.uuid4().hex,'unit_id':data['unit_id'],'role':data['role'],'assignee':data['assignee'],'title':self._text(data,'title',5,160),'instructions':self._text(data,'instructions',20),'acceptance':self._text(data,'acceptance',20),'source':self._text(data,'source',5,1000),'consequential':data['consequential'],'status':'open','version':1,'created_at':now(),'created_by':user['username'],'history':[],'evidence':[],'authorization':None}
   self.s.save(db,'human_manual_tasks',row);self.s.audit(db,'human_manual_task_created',row['id'],{'unit_id':row['unit_id'],'role':row['role'],'assignee':row['assignee'],'external_actions':0},user['username'])
   return {'id':row['id'],'version':1}
 def task_action(self,data,user):
  self._fields(data,{'id','version','action','source','note','attest'})
  action=data['action']
  if action not in ('start','complete','reject','authorize','hold','cancel','reopen'):raise Invalid('Unknown manual action')
  note=self._text(data,'note',20);source=self._text(data,'source',5,1000)
  with self.s.db()as db:
   row=self.s.get(db,'human_manual_tasks',data['id']);self._access(db,user,row['unit_id'],row['role']);self._version(data,row)
   president=user['role']=='founder'
   if action in ('authorize','hold','cancel','reopen'):self._president(user)
   if row.get('department_policy')and action in ('start','complete','authorize'):
    from .operating_plan import today
    if row.get('start_date','')>str(today()):raise Invalid('Future phase is not active')
   if not president and row.get('president_locked'):raise PermissionError('President decision is locked; President must reopen this task')
   if not president and row['assignee']!=user['username']:raise PermissionError('Only the assignee may record manual execution')
   if row['status']in ('completed','cancelled','held')and not president:raise Invalid('Task is closed or held; President review required')
   if self.s.paused(db)and action in ('start','complete','authorize'):raise Invalid('Operations paused')
   old=copy.deepcopy({k:v for k,v in row.items()if k!='history'})
   if action=='authorize':
    if not row['consequential']:raise Invalid('Internal preparation does not need external authorization')
    row['authorization']={'actor':user['username'],'at':now(),'task_hash':task_hash(row),'note':note,'scope':'manual_handoff_only'}
   elif action in ('start','complete'):
    if row['consequential']and(not row['authorization']or row['authorization']['task_hash']!=task_hash(row)):raise Invalid('Exact President authorization required before consequential manual work')
    if action=='complete'and data['attest']is not True:raise Invalid('Verified execution evidence required')
    row['status']='completed'if action=='complete'else'in_progress'
    row['evidence'].append({'source':source,'note':note,'actor':user['username'],'recorded_at':now(),'attest':data['attest']is True})
   else:
    row['status']={'reject':'rejected','hold':'held','cancel':'cancelled','reopen':'open'}[action]
    if action in ('hold','cancel','reopen'):row['authorization']=None
   if president and action in ('complete','reject','hold','cancel'):row['president_locked']=True
   if action=='reopen':row['president_locked']=False
   row['history'].append({'before':old,'action':action,'actor':user['username'],'note':note,'source':source,'at':now()})
   row['version']+=1;row['updated_at']=now()
   self.s.save(db,'human_manual_tasks',row)
   from .department_plan import sync_manual
   sync_manual(self.s,db,row)
   self.s.audit(db,'human_manual_'+action,row['id'],{'unit_id':row['unit_id'],'role':row['role'],'president_override':president,'version':row['version'],'external_actions':0},user['username'])
   return {'id':row['id'],'version':row['version']}
 def override(self,data,user):
  self._president(user);self._fields(data,{'kind','id','version','step','action','note'})
  note=self._text(data,'note',20)
  if data['kind']!='case'or data['action']not in ('hold','reopen','cancel'):raise Invalid('Use the corresponding review or manual-task control; case override supports hold, reopen or cancel')
  with self.s.db()as db:
   case=self.s.get(db,'business_cases',data['id']);self._version(data,case)
   old=copy.deepcopy({k:v for k,v in case.items()if k!='history'})
   if data['action']=='reopen':
    index=data['step']
    if type(index)is not int or not 0<=index<=min(case['cursor'],len(case['steps'])-1):raise Invalid('Choose an existing or earlier step; overrides cannot skip evidence')
    case.update(cursor=index,closed=False,president_hold=False)
    for s in case['steps'][index:]:
     for key in ('decision','proposal_hash','expires_at'):s.pop(key,None)
     s['status']='pending'
   elif data['action']=='hold':case['president_hold']=True
   else:case.update(closed=True,close_note=note,closed_by=user['username'],president_hold=True)
   case.setdefault('history',[]).append({'command':'president_override','actor':user['username'],'at':now(),'note':note,'action':data['action'],'before':old})
   case['version']+=1;case['updated_at']=now()
   self.s.save(db,'business_cases',case);self.s.audit(db,'president_case_override',case['id'],{'action':data['action'],'note':note,'version':case['version'],'external_actions':0},user['username'])
   return {'id':case['id'],'version':case['version']}
