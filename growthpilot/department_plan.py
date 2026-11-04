"""SaaS department plans, scoped execution routing and President oversight."""
import copy,datetime as dt,json
from collections import Counter
from .core import Invalid,now,digest
from .business_os import BusinessOS,UNITS
from .saas_roles import SAAS_ROLES
from .saas_plan_catalog import OBJECTIVES,KPIS,responsible_role

POLICY='saas-department-plans-20261104'
TERMINAL={'completed','cancelled'}

def candidates(store,db,plan):
 unit=next(u for u in UNITS if u['id']==plan['unit_id'])
 names={a['username']for a in store.rows(db,'business_assignments')if a['enabled']and a['unit_id']==unit['id']and a['role']==plan['role']}
 return sorted(r['id']for r in db.execute('SELECT id,role,enabled,products FROM users')if r['id']in names and r['enabled']and r['role']=='business'and set(unit['product_ids']).issubset(json.loads(r['products'])))

def reconcile_owners(store,db,actor='department-router'):
 """Run in the caller transaction. Never creates access grants or changes outcomes."""
 changed=0
 for p in store.rows(db,'operating_plans'):
  if p.get('department_policy')!=POLICY:continue
  available=candidates(store,db,p);requested=p.get('selected_owner')
  owner=requested if requested in available or requested=='founder'else available[0]if len(available)==1 else'founder'
  state='named_role_owner'if owner!='founder'else'president_interim_owner'
  if p.get('accountable_human')==owner and p.get('owner_routing')==state:continue
  previous=p.get('accountable_human');p.update(accountable_human=owner,owner_routing=state,owner_version=p.get('owner_version',0)+1)
  for task in p['tasks']:task['human_assignee']=owner
  store.save(db,'operating_plans',p);changed+=1
  for a in store.rows(db,'work_assignments'):
   if a.get('department_plan_id',a.get('plan_id'))==p['id']and a.get('department_policy')==POLICY:
    a.update(human_assignee=owner,routing=state);store.save(db,'work_assignments',a)
  for m in store.rows(db,'human_manual_tasks'):
   if m.get('department_plan_id')!=p['id']or m['status']in TERMINAL or m.get('president_locked'):continue
   assignee='founder'if p['role']=='AUDITOR'else owner
   if m['assignee']==assignee:continue
   m.setdefault('history',[]).append({'action':'department_owner_changed','previous_assignee':m['assignee'],'assignee':assignee,'actor':actor,'at':now()})
   m.update(assignee=assignee,version=m['version']+1,authorization=None);store.save(db,'human_manual_tasks',m)
  store.audit(db,'department_owner_routed',p['id'],{'previous_owner':previous,'owner':owner,'routing':state},actor)
 return changed

def sync_manual(store,db,row):
 """Manual evidence can submit an outcome, never approve it."""
 if row.get('department_policy')!=POLICY or not row.get('milestone_id'):return
 p=store.get(db,'operating_plans',row['department_plan_id']);t=next(t for t in p['tasks']if t['id']==row['milestone_id'])
 target='ready_for_review'if row['status']=='completed'else'in_progress'if row['status']=='in_progress'else'blocked'
 if t['status']=='completed'and row['status']=='completed':return
 t.update(status=target,version=t['version']+1)
 t['evidence'].append({'source':'human_manual_tasks/'+row['id'],'note':'Manual task state: '+row['status']+'. President outcome review is separate.','recorded_at':now()})
 if target!='ready_for_review':
  for later in p['tasks']:
   if later['kind']=='outcome'and later['phase']>t['phase']and later['status']in ('completed','ready_for_review'):
    later.update(status='blocked',version=later['version']+1)
    later['evidence'].append({'source':t['id'],'note':'Earlier manual evidence reopened; dependent outcome requires review again.','recorded_at':now()})
 store.save(db,'operating_plans',p)

class DepartmentPlan:
 def __init__(self,store):self.s=store;self.os=BusinessOS(store)
 def _president(self,user):
  if user.get('role')!='founder':raise PermissionError('President required')
 def prepare(self,data,user):
  self._president(user)
  if set(data)!={'source'}or not isinstance(data['source'],str)or not 10<=len(data['source'])<=1000:raise Invalid('Authorization source required')
  from .operating_plan import today
  with self.s.db()as db:
   if self.s.paused(db):raise Invalid('Operations paused')
   programs=self.s.rows(db,'operating_program')
   if not programs or not programs[0].get('scope_approved')or not programs[0].get('enabled'):raise Invalid('Approved active operating program required')
   program=programs[0];start=dt.date.fromisoformat(program['start_date'])
   if not start<=today()<=dt.date.fromisoformat(program['end_date']):raise Invalid('Department expansion requires an active 90-day window')
   old=self.s.rows(db,'department_program')
   if old:return {'id':POLICY,'created':False}
   created=0;stamp=now();plans={}
   for unit in UNITS:
    for role in SAAS_ROLES:
     pid=digest([program['id'],unit['id'],role]);tasks=[]
     for phase,(title,acceptance)in enumerate(OBJECTIVES[role],1):
      begin=start+dt.timedelta(days=(phase-1)*30);due=begin+dt.timedelta(days=29)
      for kind in ('preparation','outcome'):
       tid=pid+':'+str(phase-1)+':'+kind
       task={'id':tid,'phase':phase,'kind':kind,'title':('Prepare evidence: 'if kind=='preparation'else'')+title,'acceptance':'Produce a current scoped evidence pack with blockers and sources; no outcome is certified.'if kind=='preparation'else acceptance,'start_date':str(begin),'due_date':str(due),'status':'pending','version':1,'evidence':[],'human_assignee':'founder','ai_assignee':'deterministic_department_preparation'}
       tasks.append(task)
       aid=digest([POLICY,'plan',tid]);task['assignment_id']=aid
       self.s.save(db,'work_assignments',{'id':aid,'kind':'plan','source_id':tid,'plan_id':pid,'department_policy':POLICY,'unit_id':unit['id'],'company_id':unit['company_id'],'role':role,'human_assignee':'founder','ai_assignee':'deterministic_department_preparation','routing':'president_interim_owner','title':task['title'],'start_date':str(begin),'due_date':str(due),'assigned_at':stamp,'source':data['source']})
       if kind=='outcome':
        mid=digest([POLICY,'manual',tid]);task['manual_task_id']=mid
        self.s.save(db,'human_manual_tasks',{'id':mid,'unit_id':unit['id'],'role':role,'assignee':'founder','title':title,'instructions':acceptance+' Unit constraint: '+unit['constraint']+' Record actual evidence or the exact missing dependency. Product fixes remain on their separate backlogs.','acceptance':acceptance,'source':'operating_plans/'+pid,'consequential':False,'status':'open','version':1,'created_at':stamp,'created_by':user['username'],'history':[],'evidence':[],'authorization':None,'priority':1 if phase==1 else 2,'department_policy':POLICY,'department_plan_id':pid,'milestone_id':tid,'start_date':str(begin),'due_date':str(due),'completion_scope':'Evidence preparation and handoff only. President accepts the outcome separately.'})
     plan={'id':pid,'program_id':program['id'],'department_policy':POLICY,'company_id':unit['company_id'],'unit_id':unit['id'],'role':role,'name':unit['name']+' / '+role,'accountable_human':'founder','owner_routing':'president_interim_owner','owner_version':1,'tasks':tasks,'created_at':stamp,'kpis':KPIS[role],'automation':'deterministic_evidence_preparation','linked_backlog':[]}
     plans[(unit['id'],role)]=plan;self.s.save(db,'operating_plans',plan);created+=1
   routed,moved=self._route_backlog(db,plans,data['source'],user)
   for p in plans.values():self.s.save(db,'operating_plans',p)
   reconcile_owners(self.s,db,user['username'])
   result={'id':POLICY,'created':True,'plans_created':created,'activities_created':created*6,'phase_manual_tasks_created':created*3,'backlog_routed':routed,'existing_manual_tasks_routed':moved,'start_date':program['start_date'],'end_date':program['end_date'],'source':data['source'],'created_at':stamp,'outcomes_completed':0,'external_actions':0}
   self.s.save(db,'department_program',result);self.s.audit(db,'department_program_prepared',POLICY,result,user['username']);return result
 def _route_backlog(self,db,plans,source,user):
  from .operating_plan import role_for
  mapping={pid:u for u in UNITS for pid in u['product_ids']};routed=moved=0
  for t in self.s.rows(db,'execution_tasks'):
   if t['status']in ('completed','not_applicable'):continue
   u=mapping.get(t['product_id']);r=responsible_role(t)
   if not u or not r:continue
   p=plans[(u['id'],r)];p['linked_backlog'].append(t['id']);aid=digest([POLICY,'backlog',t['id']])
   a={'id':aid,'kind':'department_backlog','source_id':t['id'],'product_id':t['product_id'],'department_plan_id':p['id'],'department_policy':POLICY,'unit_id':u['id'],'company_id':u['company_id'],'role':r,'oversight_role':role_for(t),'human_assignee':'founder','ai_assignee':'deterministic_department_preparation','routing':'president_interim_owner','title':t['title'],'priority':t['priority'],'assigned_at':now(),'source':source}
   # Reuse open evidence handoffs. Preserve completed, locked and consequential tasks.
   matches=[m for m in self.s.rows(db,'human_manual_tasks')if m.get('source')=='execution_tasks/'+t['id']]
   if len(matches)==1:
    m=matches[0]
    if m['status']not in TERMINAL|{'held','rejected'}and not m.get('president_locked')and not m.get('consequential'):
     m.setdefault('history',[]).append({'action':'department_routing','actor':user['username'],'at':now(),'previous_role':m['role'],'previous_assignee':m['assignee'],'source':source})
     m.update(role=r,assignee='founder',version=m['version']+1,department_policy=POLICY,department_plan_id=p['id'],authorization=None,oversight_role=role_for(t));self.s.save(db,'human_manual_tasks',m);a['manual_task_id']=m['id'];moved+=1
   if not matches:
    mid=digest([POLICY,'backlog_manual',t['id']]);a['manual_task_id']=mid
    self.s.save(db,'human_manual_tasks',{'id':mid,'unit_id':u['id'],'role':r,'assignee':'founder','title':('Evidence handoff: '+t['title'])[:160],'instructions':'Prepare the acceptance evidence and preserve all source dependencies and commercial gates. Product fixes remain separate.','acceptance':t['acceptance'],'source':'execution_tasks/'+t['id'],'consequential':False,'status':'open','version':1,'created_at':now(),'created_by':user['username'],'history':[],'evidence':[],'authorization':None,'priority':t['priority'],'department_policy':POLICY,'department_plan_id':p['id'],'oversight_role':role_for(t)})
   self.s.save(db,'work_assignments',a);routed+=1
  return routed,moved
 def owner(self,data,user):
  self._president(user)
  if set(data)!={'plan_id','version','username','note'}or not isinstance(data['note'],str)or len(data['note'].strip())<20:raise Invalid('Exact owner selection and reason required')
  with self.s.db()as db:
   if self.s.paused(db):raise Invalid('Operations paused')
   p=self.s.get(db,'operating_plans',data['plan_id'])
   if p.get('department_policy')!=POLICY:raise Invalid('Department plan required')
   if type(data['version'])is not int or p['owner_version']!=data['version']:raise Invalid('Owner changed; refresh')
   if data['username']!='founder'and data['username']not in candidates(self.s,db,p):raise PermissionError('Enabled scoped role account required')
   p['selected_owner']=data['username'];p['owner_version']+=1;self.s.save(db,'operating_plans',p);reconcile_owners(self.s,db,user['username']);self.s.audit(db,'department_owner_selected',p['id'],{'username':data['username'],'note':data['note']},user['username'])
   return {'id':p['id']}
 def summary(self,db,user):
  from .operating_plan import today,task_state
  allplans=[p for p in self.s.rows(db,'operating_plans')if p.get('department_policy')==POLICY]
  plans=[p for p in allplans if p['role']in self.os._roles(db,user,self.os._unit(p['unit_id']))]
  ids={p['id']for p in plans};backlog={t['id']:t for t in self.s.rows(db,'execution_tasks')};manual=self.s.rows(db,'human_manual_tasks');president=user.get('role')=='founder'
  current=str(today());rows=[]
  for p in plans:
   tasks=[t for t in p['tasks']if t['kind']=='outcome'];linked=[{'id':i,'title':backlog[i]['title'],'status':task_state(backlog[i],backlog),'priority':backlog[i]['priority'],'acceptance':backlog[i]['acceptance']}for i in p['linked_backlog']if i in backlog]
   rows.append({'id':p['id'],'company_id':p['company_id'],'unit_id':p['unit_id'],'role':p['role'],'owner':p['accountable_human'],'owner_routing':p['owner_routing'],'owner_version':p['owner_version'],'candidate_owners':candidates(self.s,db,p)if president else[],'kpis':p['kpis'],'current_tasks':[t for t in tasks if t['start_date']<=current<=t['due_date']],'outcomes_completed':sum(t['status']=='completed'for t in tasks),'overdue':sum(t['due_date']<current and t['status']!='completed'for t in tasks),'linked_backlog':linked,'missing_backlog':[i for i in p['linked_backlog']if i not in backlog]})
  approval=[{'plan_id':p['id'],'unit_id':p['unit_id'],'company_id':p['company_id'],'role':p['role'],**t}for p in plans for t in p['tasks']if t['kind']=='outcome'and t['status']=='ready_for_review']
  return {'program':next(iter(self.s.rows(db,'department_program')),None),'plans':rows,'counts':{'plans':len(plans),'activities':sum(len(p['tasks'])for p in plans),'ready_for_review':len(approval),'interim_owner_plans':sum(p['owner_routing']=='president_interim_owner'for p in plans),'completed_outcomes':sum(r['outcomes_completed']for r in rows),'overdue_outcomes':sum(r['overdue']for r in rows)},'approvals':approval,'manual_tasks':[m for m in manual if m.get('department_plan_id')in ids],'note':'Department preparation is deterministic and source-linked. President review certifies only recorded evidence, not external execution. Unassigned roles remain in the President interim-owner queue; no permissions are granted by routing.'}
