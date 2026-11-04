"""Read-only operational evidence and bounded, local role-worker execution."""
import datetime as dt
import ipaddress
import json
import math
import os
import socket
import urllib.parse
import urllib.request
from pathlib import Path
from .core import Invalid, now, digest
from .business_os import UNITS, PROCESSES, BusinessOS

PROPERTY_SCOPE = {
 'liqmint':('vireoka','liqmint_individual'),
 'liqmint-institutional':('vireoka','liqmint_institutional'),
 'vireoka':('vireoka',None),
 'atmakosh':('atmakosh',None),
 'weddingos':('atmakosh','weddingos'),
 'jodibana':('atmakosh','jodibana'),
 'jodiusa':('atmakosh','jodibana'),
 'oratoplus':('atmakosh','oratoplus'),
}
PARTNER_FIELDS = {'id','property_id','name','kind','stage','next_step','next_step_date','updated_at','priority_score','is_segment','email_consent','website'}
PLANS = {
 'CEO':[
  'Verify the decision-maker, current relationship and one measurable objective before proposing a commitment.',
  'Prepare a scoped pilot or meeting brief with owners, success criteria and an explicit exit condition.',
  'Resolve missing authority, evidence or legal-entity attribution before moving this opportunity forward.'],
 'CFO':[
  'Reconcile the source period, payment movements and allocation basis; keep unknown recognized revenue and costs unfilled.',
  'Collect missing supplier, support, deferred-revenue and partner-payout evidence before calculating an actual margin.',
  'Compare the provisional offer with the 75% operating-margin policy and document any funded free-service exception.'],
 'CMO':[
  'Verify the prospect problem, source and appropriate permission; prepare a discovery question without unsupported claims.',
  'Prepare an exact founder-review campaign package with a measurable activation goal and source attribution.',
  'Review recorded results and objections before selecting the next small acquisition experiment.'],
 'CTO':[
  'Check the linked product readiness evidence and reproduce the next unresolved acceptance condition.',
  'Prepare a narrowly scoped product-backlog request with tests, rollback requirements and affected user journey.',
  'Collect fresh operational evidence before treating a previous technical check as a current release pass.'],
 'COO':[
  'Confirm the requested outcome, accountable owner, delivery scope and next customer or vendor checkpoint.',
  'Prepare an onboarding or fulfillment checklist with acceptance evidence and a documented escalation path.',
  'Reconcile delivery, support or incident evidence and record the next unresolved operational dependency.'],
}

def age(stamp):
 try:
  value=dt.datetime.fromisoformat(stamp)
  if value.tzinfo is None:return None
  return (dt.datetime.now(dt.timezone.utc)-value).total_seconds()
 except (ValueError,TypeError):return None

def read_object(path,limit=3000000):
 if not path.exists():return None
 if path.stat().st_size>limit:raise Invalid('Evidence file exceeds limit')
 value=json.loads(path.read_text())
 if not isinstance(value,dict):raise Invalid('Evidence object required')
 return value

def vanguard_snapshot(directory):
 result={'status':'not_connected','captured_at':None,'records':[],'unmapped_count':0,'direction':'Vanguard to AgentVire','marketing_permission_transferred':False}
 try:
  data=read_object(Path(directory)/'vanguard-snapshot.json')
  if data is None:return result
  if data.get('schema_version')!=1 or data.get('complete') is not True or data.get('source')!='vanguard-gtm':raise Invalid('Incomplete snapshot')
  rows=data.get('records')
  if not isinstance(rows,list) or len(rows)>5000:raise Invalid('Invalid snapshot size')
  seen=set();mapped=[]
  for row in rows:
   if not isinstance(row,dict) or set(row)!=PARTNER_FIELDS or type(row['id']) is not int or row['id']<=0 or row['id'] in seen:raise Invalid('Invalid or duplicate source record')
   seen.add(row['id'])
   for key in ['property_id','name','kind','stage','next_step','next_step_date','updated_at','email_consent','website']:
    if row[key] is not None and (not isinstance(row[key],str) or len(row[key])>4000):raise Invalid('Invalid source field')
   if type(row['priority_score']) is not int or not 0<=row['priority_score']<=100 or row['is_segment'] not in (0,1):raise Invalid('Invalid priority')
   scope=PROPERTY_SCOPE.get(row['property_id'])
   if not scope:
    result['unmapped_count']+=1
    continue
   mapped.append({**row,'company_id':scope[0],'unit_id':scope[1],'marketing_eligible':False,'source_ref':'vanguard:partner:'+str(row['id'])})
  seconds=age(data.get('captured_at'));status='fresh' if seconds is not None and 0<=seconds<=900 else 'stale'
  heartbeat=read_object(Path(directory)/'vanguard-sync-status.json',10000)
  if heartbeat and heartbeat.get('status')!='ok':status='source_unavailable'
  result.update(status=status,captured_at=data.get('captured_at'),records=mapped,source_count=len(rows),source_hash=digest(rows),last_check=heartbeat.get('checked_at') if heartbeat else None)
 except (ValueError,TypeError,KeyError,AttributeError,OSError,Invalid):
  result.update(status='invalid',records=[])
 return result

def financial_evidence(directory,units,privileged=False):
 result={'status':'not_connected','books_finalized':False,'financial_reconciled':False,'units':[],'shared_accounts':[],'missing':[],'actual_revenue':None,'actual_margin':None}
 try:
  source=read_object(Path(directory)/'economics-source.json',4000000)
  if source is None:return result
  actual=source.get('actual_finance')
  if not isinstance(actual,dict):raise Invalid('Missing financial evidence')
  provisional=actual.get('provisional_margin_run') or {}
  statements=actual.get('statement_cost_evidence') or {}
  rows=provisional.get('live_assessments',[])
  if not isinstance(rows,list):raise Invalid('Invalid allocations')
  byproduct={}
  for row in rows:
   pid=row.get('product_id')
   if type(pid) is not int or pid in byproduct:raise Invalid('Duplicate cost allocation')
   value=row.get('allocated_cash_cost_proxy_usd')
   if value is not None and (type(value) not in (float,int) or not math.isfinite(value)):raise Invalid('Invalid cost amount')
   byproduct[pid]=value
  approved=provisional.get('mode')=='approved_provisional_cash_allocation' and provisional.get('policy_status')=='approved_for_provisional_planning_only' and provisional.get('currency')=='USD'
  for unit in units:
   values=[byproduct.get(pid) for pid in unit['product_ids']]
   cost=round(sum(values),2) if approved and values and all(v is not None for v in values) else None
   result['units'].append({'unit_id':unit['id'],'company_id':unit['company_id'],'name':unit['name'],'allocated_cash_proxy_usd':cost,'recognized_cost_usd':None,'recognized_revenue_usd':None,'actual_margin':None})
  allowed={p for u in units for p in u['product_ids']}
  seen_accounts=set()
  for account in actual.get('processor_accounts',[]):
   pids=account.get('configured_product_ids',[])
   if not isinstance(pids,list) or any(type(p) is not int for p in pids):raise Invalid('Invalid processor scope')
   if not set(pids)&allowed:continue
   fingerprint=account.get('account_fingerprint')
   if fingerprint and fingerprint in seen_accounts:raise Invalid('Duplicate processor account')
   if fingerprint:seen_accounts.add(fingerprint)
   visible=bool(pids) and (privileged or set(pids).issubset(allowed))
   groups=[]
   if visible:
    for group in account.get('captured_charge_groups',[]):
     currency=group.get('currency')
     keys=('captured_count','captured_minor','refunded_to_date_minor','disputed_count')
     if not isinstance(currency,str) or len(currency)!=3 or not currency.isalpha() or any(type(group.get(k)) is not int or group[k]<0 for k in keys):raise Invalid('Invalid processor totals')
     groups.append({k:group[k] for k in ('currency',)+keys})
   result['shared_accounts'].append({'products':pids if visible else sorted(set(pids)&allowed),'status':account.get('status','unknown'),'amounts_withheld_for_scope':not visible,'cash_groups':groups,'recognized_revenue':None})
  seconds=age(actual.get('captured_at'))
  result.update(status='provisional_evidence',captured_at=actual.get('captured_at'),stale=seconds is None or seconds<0 or seconds>86400,period_start=actual.get('period_start'),period_end_exclusive=actual.get('period_end_exclusive'),
   allocation_period_start=provisional.get('period_start'),allocation_period_end_exclusive=provisional.get('period_end_exclusive'),allocation_authorization=provisional.get('authorization') if approved else None,
   missing=[str(v)[:500] for v in actual.get('missing',[])][:30],equipment_note=str(provisional.get('equipment','Equipment remains separate from recurring subscriptions.'))[:1000],
   source_hash=digest(actual),books_finalized=False,financial_reconciled=False)
  if privileged:
   result['portfolio_source_controls']={k:statements.get(k) for k in ['file_count','extracted_record_count','candidate_count','pdf_controls_reconciled','possible_duplicate_candidate_records','parse_failure_count']}
  result['note']='Source controls and provisional allocation tie-outs do not finalize company books. Processor cash is not recognized revenue. Owner recovery and equipment remain separate.'
 except (ValueError,TypeError,KeyError,AttributeError,OSError,Invalid):
  result.update(status='invalid',units=[],shared_accounts=[],missing=['Financial source validation failed; no actual margin is reported.'])
 return result

class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):raise Invalid('Model redirect denied')

def choose_local(role,process,flags):
 base=os.environ.get('GROWTHPILOT_OLLAMA_URL','').rstrip('/')
 model=os.environ.get('GROWTHPILOT_OLLAMA_MODEL','')
 if model not in ('ministral-3:3b','granite3.3:2b'):raise Invalid('Qualified local selection model required')
 url=urllib.parse.urlsplit(base)
 if url.scheme not in ('http','https') or not url.hostname or url.username or url.password or url.path not in ('','/') or url.query or url.fragment:raise Invalid('Local model URL rejected')
 addresses=socket.getaddrinfo(url.hostname,url.port or (443 if url.scheme=='https' else 80),type=socket.SOCK_STREAM)
 if not addresses or any(not ipaddress.ip_address(a[4][0]).is_private for a in addresses):raise Invalid('Local-only inference required')
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
 with opener.open(base+'/api/ps',timeout=3) as response:
  loaded=json.loads(response.read(32769))
 if not any(x.get('name')==model and x.get('context_length')==2048 for x in loaded.get('models',[])):raise Invalid('Local model must be preloaded at the qualified context')
 choices=PLANS[role]
 # Model input is a fixed vocabulary and booleans, never CRM text or financial amounts.
 labels={
 'CEO':'1=qualify decision-maker; 2=scope pilot; 3=resolve missing authority',
 'CFO':'1=reconcile payments; 2=collect missing cost and revenue evidence; 3=review margin policy',
 'CMO':'1=qualify problem and permission; 2=prepare campaign review; 3=review experiment results',
 'CTO':'1=reproduce acceptance check; 2=scope tested product fix; 3=refresh release evidence',
 'COO':'1=confirm owner and scope; 2=prepare fulfillment checklist; 3=review delivery issues'}
 prompt=role+' '+process+'. '+labels[role]+'. Facts: '+','.join(k for k,v in flags.items() if v)+'. Return JSON choice 1, 2 or 3.'
 schema={'type':'object','properties':{'choice':{'type':'integer','enum':[1,2,3]}},'required':['choice'],'additionalProperties':False}
 payload={'model':model,'messages':[{'role':'system','content':'Select one permitted internal action; do not generate text or execute tools.'},{'role':'user','content':prompt}],'stream':False,'format':schema,'keep_alive':-1,'options':{'num_predict':32,'num_ctx':2048,'num_gpu':0,'num_thread':2,'use_mmap':True,'temperature':0}}
 request=urllib.request.Request(base+'/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
 with opener.open(request,timeout=20) as response:
  body=response.read(32769)
 if len(body)>32768:raise Invalid('Oversized model response')
 raw=json.loads(body)
 if raw.get('model')!=model or raw.get('done') is not True or raw.get('done_reason')!='stop':raise Invalid('Incomplete model response')
 result=json.loads(raw['message']['content'])
 if not isinstance(result,dict) or set(result)!={'choice'} or type(result['choice']) is not int or result['choice'] not in (1,2,3):raise Invalid('Model choice rejected')
 return {'model':model,'choice':result['choice'],'recommendation':choices[result['choice']-1],'mode':'bounded_role_selection'}

class BusinessRuntime:
 def __init__(self,store):
  self.s=store;self.directory=Path(store.path).parent;self.os=BusinessOS(store)
 def control(self,data,user):
  if user.get('role')!='founder':raise PermissionError('Founder required')
  if set(data)!={'enabled'} or type(data['enabled']) is not bool:raise Invalid('Explicit enabled flag required')
  with self.s.db() as db:
   row={'id':'workers','enabled':data['enabled'],'updated_at':now(),'updated_by':user['username'],'mode':'local_bounded_preparation','max_jobs_per_hour':24,'max_attempts':2}
   self.s.save(db,'business_runtime',row);self.s.audit(db,'business_workers_control','workers',{'enabled':data['enabled']},user['username'])
   return row
 def enrich(self,db,user,result):
  ids={u['id'] for u in result['units']};privileged=user.get('role') in ('founder','admin')
  snapshot=vanguard_snapshot(self.directory)
  visible=[r for r in snapshot['records'] if r['unit_id'] in ids or (privileged and r['unit_id'] is None)]
  result['vanguard']={**snapshot,'records':visible}
  if not privileged:
   result['vanguard']['source_count']=len(visible);result['vanguard']['unmapped_count']=None;result['vanguard'].pop('source_hash',None)
  finance_units=[u for u in result['units'] if set(u['roles'])&{'CFO'}]
  result['finance']=financial_evidence(self.directory,finance_units,privileged) if finance_units else {'status':'role_required','units':[],'shared_accounts':[],'missing':[]}
  settings=next((x for x in self.s.rows(db,'business_runtime') if x['id']=='workers'),{'enabled':False,'mode':'local_bounded_preparation','max_jobs_per_hour':24})
  jobs=[j for j in self.s.rows(db,'business_agent_jobs') if j['unit_id'] in ids]
  current={c['id']:c for c in result['cases']}
  worker_finance=financial_evidence(self.directory,[])
  for job in jobs:
   c=current.get(job['case_id']);job['stale']=not c or c['version']!=job['case_version'] or c.get('closed',False) or c['cursor']>=len(c['steps'])
   if not job['stale']:job['stale']=self._context(db,c,snapshot,worker_finance)['input_hash']!=job.get('input_hash')
  result['role_workers']={'config':settings,'jobs':sorted(jobs,key=lambda j:j['created_at'],reverse=True)[:300],'model':os.environ.get('GROWTHPILOT_OLLAMA_MODEL','not_configured'),'external_execution':False,'note':'Autonomous evidence inspection and local selection of a prepared next action. Case completion and external execution require separate controls.'}
  for connection in result['connections']:
   if connection['name']=='Vanguard GTM':connection.update(status='Automatic inbound sync: '+snapshot['status'],note='Read-only source mirror. Stages remain source-reported; approvals and recipient permission are never transferred.')
   if connection['name']=='Accounting and company P&L':connection.update(status=result['finance']['status'],note='Existing expense and processor evidence connected. Books are not finalized; recognized revenue and actual margins stay unknown.')
   if connection['name']=='Local AI executive agents':connection.update(status='Autonomous bounded preparation enabled' if settings['enabled'] else 'Role workers paused',note=result['role_workers']['note'])
  return result
 def retry(self,data,user):
  if user.get('role')!='founder':raise PermissionError('Founder required')
  if set(data)!={'job_id'}:raise Invalid('Job ID required')
  with self.s.db() as db:
   job=self.s.get(db,'business_agent_jobs',data['job_id'])
   if job['status'] not in ('failed','blocked','superseded'):raise Invalid('Only blocked or failed work can be retried')
   case=self.s.get(db,'business_cases',job['case_id'])
   if case['version']!=job['case_version'] or case.get('closed') or case['cursor']>=len(case['steps']):raise Invalid('Case changed; use its current work item')
   job.update(status='retry',attempts=0,next_attempt_at=now());self.s.save(db,'business_agent_jobs',job);self.s.audit(db,'business_worker_retry',job['id'],{},user['username'])
   return job
 def _context(self,db,case,snapshot,finance):
  unit=self.os._unit(case['unit_id']);role=case['steps'][case['cursor']]['role']
  linked=None;source_status='owner_request';blocked=False
  if case['reference'].startswith('vanguard:partner:'):
   linked=next((r for r in snapshot['records'] if r['source_ref']==case['reference']),None)
   source_status=snapshot['status']
   blocked=not linked or source_status!='fresh' or linked['company_id']!=unit['company_id'] or linked['unit_id'] not in (None,unit['id'])
  elif case['reference'].startswith('agentvire:lead:'):
   source_id=case['reference'].split(':',2)[2]
   linked=next((r for r in self.s.rows(db,'leads') if str(r['id'])==source_id),None)
   blocked=not linked or linked.get('product_id') not in unit['product_ids']
   source_status='available' if not blocked else 'missing_or_out_of_scope'
  owner=db.execute('SELECT id,role,products,enabled FROM users WHERE id=?',(case['owner'],)).fetchone()
  authorized=bool(owner and owner['enabled'] and owner['role']!='viewer' and self.os._roles(db,{'username':owner['id'],'role':owner['role'],'products':json.loads(owner['products'])},unit))
  stage=linked.get('stage') if linked else case.get('origin_stage')
  facts={'finance_incomplete':finance['financial_reconciled'] is False,'source_is_research':stage in ('research','identified','contacted'),'source_active_conversation':stage=='in_conversation','approval_step':case['steps'][case['cursor']]['approval_required']}
  from .human_ai import control
  pair=control(db,self.s,unit['id'],role)
  feedback=case.get('human_ai_feedback',{})
  if feedback.get('role')==role and feedback.get('focus')in (1,2,3):
   facts['human_revision_requested']=True;facts['human_requested_choice_'+str(feedback['focus'])]=True
  authorized=authorized and pair['enabled'] and not case.get('president_hold',False)
  result={'facts':facts,'blocked':bool(blocked),'authorized':authorized,'source_status':source_status,'source_digest':digest(linked) if linked else None,'finance_digest':finance.get('source_hash') if role=='CFO' else None}
  if pair['version']:result['pair_version']=pair['version']
  result['input_hash']=digest(result)
  return result
 def tick(self,selector=None):
  selector=selector or choose_local
  with self.s.db() as db:
   config=next((x for x in self.s.rows(db,'business_runtime') if x['id']=='workers'),{})
   if not config.get('enabled') or self.s.paused(db):return {'status':'paused'}
   jobs=self.s.rows(db,'business_agent_jobs')
   if any(j['status']=='running' and age(j.get('started_at')) is not None and age(j['started_at'])<120 for j in jobs):return {'status':'busy'}
   for j in jobs:
    if j['status']=='running':
     j.update(status='failed',error='Worker lease expired; result was not applied.',next_attempt_at=now());self.s.save(db,'business_agent_jobs',j)
   if sum(1 for j in jobs for stamp in j.get('attempt_history',[]) if age(stamp) is not None and 0<=age(stamp)<3600)>=24:return {'status':'hourly_budget'}
   snapshot=vanguard_snapshot(self.directory);finance=financial_evidence(self.directory,[])
   byid={j['id']:j for j in jobs};case=None
   for c in sorted(self.s.rows(db,'business_cases'),key=lambda c:c['created_at']):
    if c.get('closed') or c.get('president_hold') or c['cursor']>=len(c['steps']) or c['steps'][c['cursor']]['status']=='awaiting_review':continue
    context=self._context(db,c,snapshot,finance)
    if not context['authorized']:continue
    key=digest(['role-worker-v1',c['id'],c['version'],context['input_hash']]);prior=byid.get(key)
    if prior and (prior['status']=='ready' or prior['attempts']>=2 or (prior.get('next_attempt_at') and age(prior['next_attempt_at'])<0)):continue
    case=c;break
   if case is None:return {'status':'idle'}
   unit=self.os._unit(case['unit_id']);role=case['steps'][case['cursor']]['role']
   at=now();attempts=(prior or {}).get('attempts',0)+1
   job={'id':key,'unit_id':unit['id'],'company_id':unit['company_id'],'case_id':case['id'],'case_version':case['version'],'role':role,'status':'running','created_at':(prior or {}).get('created_at',at),'started_at':at,'attempts':attempts,'attempt_history':(prior or {}).get('attempt_history',[])+[at],'facts':context['facts'],'source_ref':case['reference'],'input_hash':context['input_hash'],'source_digest':context['source_digest'],'finance_digest':context['finance_digest'],'external_actions':0}
   self.s.save(db,'business_agent_jobs',job)
  try:
   if context['blocked']:raise Invalid('Linked source is unavailable')
   result=selector(role,case['process'],context['facts'])
   if not isinstance(result,dict) or result.get('mode')!='bounded_role_selection' or result.get('model') not in ('ministral-3:3b','granite3.3:2b') or type(result.get('choice')) is not int or result['choice'] not in (1,2,3) or result.get('recommendation')!=PLANS[role][result['choice']-1]:raise Invalid('Unqualified worker result')
   state='ready';error=None
  except Exception:
   state='blocked' if context['blocked'] else 'failed';result=None;error='Source evidence is stale or unavailable.' if context['blocked'] else 'Local model did not return a qualified result. No case or external action was completed.'
  with self.s.db() as db:
   current=self.s.get(db,'business_cases',case['id'])
   active=next((x for x in self.s.rows(db,'business_runtime') if x['id']=='workers'),{})
   valid=current['version']==case['version'] and not current.get('closed') and not self.s.paused(db) and active.get('enabled') and active.get('updated_at')==config.get('updated_at')
   if current['cursor']>=len(current['steps']):valid=False
   else:
    latest=self._context(db,current,vanguard_snapshot(self.directory),financial_evidence(self.directory,[]))
    valid=valid and latest['authorized'] and latest['input_hash']==context['input_hash']
   if not valid:state='superseded';result=None;error='Case, source or authorization changed while preparing the result.'
   job.update(status=state,result=result,error=error,finished_at=now(),next_attempt_at=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=1)).isoformat())
   self.s.save(db,'business_agent_jobs',job);self.s.audit(db,'business_worker_result',job['id'],{'unit_id':unit['id'],'role':role,'status':state,'case_version':case['version'],'external_actions':0},'local-role-worker:'+unit['id']+':'+role)
   return {'status':state,'job_id':job['id'],'role':role}
 def _create_case(self,db,user,unit,process,title,reference,due_date,origin_stage):
  self.os._access(db,user,unit,PROCESSES[process]['steps'][0]['role'])
  key=digest(['business-origin-v1',unit['id'],process,reference])
  existing=next((c for c in self.s.rows(db,'business_cases') if c['id']==key),None)
  if existing:return existing,False
  owner=db.execute('SELECT enabled FROM users WHERE id=?',(user['username'],)).fetchone()
  if not owner or not owner['enabled']:raise Invalid('Enabled owner account required')
  case={'id':key,'unit_id':unit['id'],'company_id':unit['company_id'],'process':process,'title':title[:160],'owner':user['username'],'due_date':self.os._due(due_date),'reference':reference,'tenant_ref':'','cursor':0,'version':1,'created_at':now(),'updated_at':now(),'origin_stage':origin_stage,'origin':'owner_authorized_operating_request','steps':[dict(s,status='pending') for s in PROCESSES[process]['steps']]}
  self.s.save(db,'business_cases',case);self.s.audit(db,'business_case_from_source',key,{'unit_id':unit['id'],'process':process,'reference':reference,'origin_stage':origin_stage},user['username'])
  return case,True
 def opportunity_case(self,data,user):
  if user.get('role')=='viewer':raise PermissionError('Read-only account')
  if set(data)-{'source_id','unit_id','due_date'} or type(data.get('source_id')) is not int:raise Invalid('Valid source ID required')
  snapshot=vanguard_snapshot(self.directory)
  if snapshot['status']!='fresh':raise Invalid('Fresh Vanguard synchronization required')
  row=next((r for r in snapshot['records'] if r['id']==data['source_id']),None)
  if row is None:raise Invalid('Source record not found')
  unit_id=row['unit_id'] or data.get('unit_id')
  if row['unit_id'] and data.get('unit_id') not in (None,'',row['unit_id']):raise Invalid('Source unit cannot be reassigned')
  unit=self.os._unit(unit_id)
  if row['company_id']!=unit['company_id']:raise PermissionError('Cross-company source handoff denied')
  if row['unit_id'] is None and user.get('role') not in ('founder','admin'):raise PermissionError('Portfolio oversight required for company-level relationships')
  process='financing' if row['kind']=='investor' else 'sales' if row['kind']=='design_partner' else 'partnership'
  title=('Review next step: ' if row['stage']=='in_conversation' else 'Qualify researched prospect: ')+row['name']
  with self.s.db() as db:
   if self.s.paused(db):raise Invalid('Operations paused')
   case,created=self._create_case(db,user,unit,process,title,row['source_ref'],data.get('due_date'),row['stage'])
   return {'case':case,'created':created,'external_actions':0}
 def bootstrap(self,data,user):
  if user.get('role')!='founder':raise PermissionError('Founder required')
  if set(data)!={'review_date','finance_review_date'}:raise Invalid('Review dates required')
  due=self.os._due(data['review_date']);finance_due=self.os._due(data['finance_review_date'])
  snapshot=vanguard_snapshot(self.directory);created=[];existing=[]
  with self.s.db() as db:
   if self.s.paused(db):raise Invalid('Operations paused')
   requests=[]
   for lead in self.s.rows(db,'leads'):
    unit=next((u for u in UNITS if lead.get('product_id') in u['product_ids']),None)
    if not unit:continue
    process='partnership' if lead.get('pipeline') in ('partner','champion') else 'sales'
    requests.append((unit,process,'Qualify existing research: '+str(lead.get('organization') or lead.get('name')),'agentvire:lead:'+str(lead['id']),due,lead.get('stage','research')))
   if snapshot['status']=='fresh':
    for row in snapshot['records']:
     if row['stage']!='in_conversation' or not row['unit_id']:continue
     unit=self.os._unit(row['unit_id']);process='financing' if row['kind']=='investor' else 'partnership'
     requests.append((unit,process,'Verify next step: '+row['name'],row['source_ref'],due,row['stage']))
   for unit in UNITS:
    requests.append((unit,'finance',unit['name']+' - reconcile expense and payment evidence','owner-request:finance-close:2026-11-03:'+unit['id'],finance_due,'operational_request'))
   for unit_id,process,title in [
    ('jodibana','engineering','Verify remaining launch gates before enabling collection'),
    ('oratoplus','engineering','Verify current grading evidence against human-reference gates'),
    ('memoire','vendor','Validate print supplier pricing and fulfillment scope'),
    ('tcompprop','onboarding','Identify property, lease and maintenance source systems')]:
    requests.append((self.os._unit(unit_id),process,title,'owner-request:operational-readiness:2026-11-03:'+unit_id,due,'operational_request'))
   for args in requests:
    c,new=self._create_case(db,user,*args)
    (created if new else existing).append(c['id'])
   return {'created':len(created),'existing':len(existing),'case_ids':created+existing,'source_status':snapshot['status'],'due_dates_are_internal_review_targets':True,'external_actions':0}
