"""Evidence-backed strategy execution. Commercial decisions remain outside this workflow."""
import copy
import datetime as dt
from .core import Invalid, digest, now
from .economics import StrategyOS
from .manager import stable

VERSION = 1
COMMERCIAL = {'pricing', 'partners', 'campaign'}
PREPARATION = {'strategy', 'activation_spec', 'experiment_spec'}
# key, title, priority, owner, effort hours, dependencies, acceptance evidence
TEMPLATES = [
 ('strategy','Implement the current product strategy',0,'marketing_manager',1,[], 'Versioned audience, buyer, value, scope, offer, assumptions and constraints linked to the current private recommendation.'),
 ('activation_spec','Prepare first-value and onboarding acceptance tests',0,'product_engineering',1,['strategy'],'Product-specific first-value event, synthetic journey steps, cross-account isolation and save/reload checks are documented; this is preparation, not a passed journey.'),
 ('experiment_spec','Prepare acquisition measurement and feedback protocol',1,'marketing_manager',1,['strategy'],'Consent, attribution, actual-only events, feedback questions and weekly stop/continue criteria are documented; no participants or results invented.'),
 ('identity','Confirm product identity and legal operating scope',0,'founder_legal',2,['strategy'],'Named operating entity and actual implemented activity; buyer and product identity confirmed. For financial products, qualified activity-specific US review; no automatic regulator approval.'),
 ('health','Verify the public destination and TLS',0,'product_engineering',0.5,['strategy'],'Timestamped HTTPS response from the configured destination. A successful page proves reachability only, not signup, identity or product capability.'),
 ('journey','Test signup, first value, save and return journey',0,'product_engineering',3,['activation_spec','identity','health'],'Dated test report for synthetic accounts: registration/login, intended first value, saved state after reload, account isolation, error recovery and logout. Record environment and commit; no real user data.'),
 ('entitlements','Verify free limits, paid entitlements and cancellation',0,'product_engineering',3,['journey'],'Test current free and existing paid tiers, usage limits, denied cross-tier access, sandbox checkout/webhooks and cancellation/refunds. Proposed prices remain disabled. Mark genuinely inapplicable cases with a scoped rationale.'),
 ('privacy','Review privacy, security and customer support boundaries',0,'founder_legal',2,['identity'],'Product-specific data inventory, retention/export/deletion, consent, terms, rights and support ownership; permissions and backup recovery evidence. Do not infer compliance from this checklist.'),
 ('finance','Reconcile revenue, supplier costs and investment allocations',1,'finance_owner',3,['strategy'],'Completed-period revenue/deferred revenue, processor settlements/refunds, supplier invoices, shared-cost allocation and founder estimates reconciled. Missing data stays missing; sweat equity is separate from operating costs.'),
 ('metering','Measure actual usage and support cost per activation',1,'product_engineering',2,['journey','experiment_spec'],'Observed metered AI/storage/email/compute usage and support time with source period and cohort. Separate test traffic; no assumed cohort recorded as actual demand.'),
 ('claims','Verify claims, demo and exact campaign destinations',1,'marketing_manager',2,['journey','privacy'],'Evidence-backed claims, synthetic demo and exact channel/account/rules review. Legal/data/identity holds remain until the relevant review passes.'),
 ('pricing','Founder decision on proposed pricing and quotas',1,'founder',0.5,['finance','metering','entitlements'],'Separate explicit founder approval of exact offer, limits, terms and evidence. This execution API cannot approve or publish pricing.'),
 ('partners','Founder decision on partner terms and commissions',1,'founder',0.5,['finance','identity','privacy'],'Separate explicit approval of eligible revenue, attribution, term, payout timing, margin floor and legal scope. No new payout contract or commission activated.'),
 ('campaign','Founder decision on exact first campaign',1,'founder',0.5,['claims','experiment_spec'],'Review exact copy, claims, account, destination, recipients/consent and payload hash in Founder approvals. No campaign is approved or sent by this backlog.'),
]

class Execution:
 def __init__(self,store):self.s=store
 def source(self):
  engine=StrategyOS(self.s)
  plan=engine.source().get('actual_finance',{}).get('commercial_pricing_plan')
  return engine,plan
 def prepare(self,actor='founder'):
  engine,plan=self.source()
  if not plan or len(plan.get('offers',[]))!=17 or plan.get('execution_enabled') is not False:
   raise Invalid('A private, non-executing 17-product commercial recommendation is required')
  if {x.get('product_id') for x in plan['offers']}!=set(range(1,18)):raise Invalid('Exactly one offer per product is required')
  offers={x['product_id']:x for x in plan['offers']}
  revision=digest({'version':VERSION,'plan':plan,'dossiers':engine.strategies})
  with self.s.db() as db:
   if self.s.paused(db):raise Invalid('System paused')
   for p in engine.strategies['products']:
    pid=p['product_id'];offer=offers[pid];profile=self.s.manager().profiles[str(pid)]
    # Strategy records are private plans, never product catalog or billing updates.
    dossier=dict(copy.deepcopy(p),commercial_proposal=copy.deepcopy(offer),source_plan_id=plan['id'],revision=revision,commercial_status='pending_founder_approval')
    artifacts={
     'strategy':dossier,
     'activation_spec':{'event':profile['activation'],'steps':profile['steps'],'proposed_scope':offer['proposed_scope'],'tests':['Synthetic registration and login','First meaningful product action','Save, reload and return in a new session','Second account cannot access first account data','Current free limits; no proposed paid offer activated','Validation, error and cancellation paths'],'pass_condition':'Attach dated product/environment/version-specific test evidence before marking journey verified.'},
     'experiment_spec':{'target_user':p['target_user'],'economic_buyer':p['economic_buyer'],'value_to_prove':p['value_proof'],'acquisition':p['zero_ad_spend_path'],'activation_event':profile['activation'],'feedback_questions':[profile['question'],'What blocked your first useful outcome?','Would you return and why?'],'events':['landing_view','signup',profile['activation'],'paid','feedback'],'required_dimensions':['product_id','campaign_id','source','consent_source','observed_at'],'controls':['Only actual records enter results','No unsolicited outreach or paid advertising','Founder approves exact campaign before distribution','Review on Fridays; investigate zero activations after 100 attributed views','Do not extrapolate small cohorts or treat targets as observed users'],'budget_advertising_usd':0,'labor_and_services_are_not_free':True}
    }
    for key,artifact in artifacts.items():
     self.s.save(db,'execution_artifacts',{'id':stable('strategy-artifact:'+str(pid)+':'+key),'product_id':pid,'kind':key,'revision':revision,'content':artifact,'evidence_type':'prepared_specification','created_at':now()})
    for key,title,priority,owner,hours,deps,acceptance in TEMPLATES:
     tid=stable('execution:'+str(pid)+':'+key)
     old=next((x for x in self.s.rows(db,'execution_tasks',pid) if x['id']==tid),None)
     if old and old.get('revision')==revision:continue
     row={'id':tid,'product_id':pid,'key':key,'title':title,'priority':priority,'wave':1 if pid<=4 else 2 if pid in (5,6,9) else 3,'owner':owner,'estimate_hours':hours,'dependencies':[stable('execution:'+str(pid)+':'+k) for k in deps],'acceptance':acceptance,'revision':revision,'source_plan_id':plan['id'],'commercial_gate':key in COMMERCIAL,'status':'awaiting_approval' if key in COMMERCIAL else 'completed' if key in PREPARATION else 'pending','created_at':old.get('created_at',now()) if old else now(),'updated_at':now(),'evidence':[],'history':old.get('history',[])+[{'revision':old.get('revision'),'status':old['status'],'evidence':old.get('evidence',[])}] if old else []}
     if key in PREPARATION:row['evidence']=[{'source':'execution_artifacts/'+stable('strategy-artifact:'+str(pid)+':'+key),'note':'Internal preparation completed; no live product readiness or market outcome attested.','type':'prepared_specification','recorded_at':now()}]
     self.s.save(db,'execution_tasks',row)
   self.s.save(db,'execution_program',{'id':'portfolio-strategy','version':VERSION,'revision':revision,'source_plan_id':plan['id'],'created_at':now(),'approval_policy':'Pricing, commissions and campaigns require separate explicit founder approval. No commercial execution from this backlog.','financial_reconciled':False})
   self.s.audit(db,'strategy_execution_prepared','portfolio-strategy',{'revision':revision,'products':17,'tasks':len(TEMPLATES)*17,'commercial_changes':0},actor)
  return self.summary()
 def summary(self):
  engine,plan=self.source()
  with self.s.db() as db:
   tasks=self.s.rows(db,'execution_tasks');artifacts=self.s.rows(db,'execution_artifacts');programs=self.s.rows(db,'execution_program')
  byid={x['id']:x for x in tasks}
  for row in tasks:
   row['blocked_by']=[x for x in row['dependencies'] if byid.get(x,{}).get('status')!='completed']
   row['effective_status']='blocked' if row['blocked_by'] and row['status']=='pending' else row['status']
  tasks.sort(key=lambda x:(x['priority'],x['wave'],x['product_id'],x['key']))
  counts={key:sum(x['effective_status']==key for x in tasks) for key in ('completed','pending','blocked','in_progress','awaiting_approval')}
  current_revision=digest({'version':VERSION,'plan':plan,'dossiers':engine.strategies}) if plan else None
  return {'program':programs[0] if programs else None,'source_changed':bool(programs and programs[0]['revision']!=current_revision),'products':engine.strategies['products'],'commercial_plan':plan,'tasks':tasks,'artifacts':artifacts,'counts':counts,'commercial_execution_enabled':False,'launch_verified_products':0,'note':'Completed specifications are preparation, not passed product tests. Commercial gates remain pending separate approval. Readiness evidence is timestamped and may require retest.'}
 def transition(self,data,actor):
  if set(data)-{'id','status','source','note','attest_verified'}:raise Invalid('Unsupported execution update')
  status=data.get('status')
  if status not in ('pending','in_progress','completed','blocked'):raise Invalid('Unknown readiness status')
  snapshot=self.summary()
  if snapshot['source_changed']:raise Invalid('Strategy changed: regenerate the backlog before updating evidence')
  with self.s.db() as db:
   if self.s.paused(db):raise Invalid('System paused')
   row=self.s.get(db,'execution_tasks',data.get('id'))
   if row['commercial_gate']:raise Invalid('Commercial decisions remain pending separate founder approval')
   if row['key'] in PREPARATION:raise Invalid('Prepared artifacts are managed by the strategy revision')
   if status in ('completed','blocked'):
    if not isinstance(data.get('source'),str) or not 10<=len(data['source'])<=1000 or not isinstance(data.get('note'),str) or not 30<=len(data['note'])<=4000:raise Invalid('Evidence source and detailed outcome are required')
   if status=='completed':
    if data.get('attest_verified') is not True:raise Invalid('Explicit evidence verification attestation required')
    for dep in row['dependencies']:
     if self.s.get(db,'execution_tasks',dep)['status']!='completed':raise Invalid('Complete prerequisite evidence first')
   row.setdefault('history',[]).append({'status':row['status'],'updated_at':row['updated_at'],'evidence':copy.deepcopy(row['evidence'])})
   row.update(status=status,updated_at=now())
   if data.get('source'):row['evidence'].append({'source':data['source'],'note':data.get('note',''),'type':'founder_attested_test' if status=='completed' else 'readiness_observation','actor':actor,'recorded_at':now()})
   self.s.save(db,'execution_tasks',row)
   # Reopening a prerequisite invalidates dependent completions, transitively.
   if status!='completed':
    invalid={row['id']};changed=True
    while changed:
     changed=False
     for other in self.s.rows(db,'execution_tasks',row['product_id']):
      if other['status']=='completed' and any(d in invalid for d in other['dependencies']):
       other.update(status='pending',updated_at=now());other['evidence'].append({'type':'dependency_invalidated','source':row['id'],'note':'Prerequisite reopened; prior evidence retained for history, retest required.','recorded_at':now()});self.s.save(db,'execution_tasks',other);invalid.add(other['id']);changed=True
   self.s.audit(db,'strategy_readiness_updated',row['id'],{'status':status,'product_id':row['product_id'],'commercial_changes':0},actor)
  return row
 def record_health(self,pid,observation,actor='readiness_probe'):
  """Import a bounded deployment-run probe; no arbitrary network requests from the API."""
  tid=stable('execution:'+str(pid)+':health')
  with self.s.db() as db:
   if self.s.paused(db):raise Invalid('System paused')
   row=self.s.get(db,'execution_tasks',tid)
   product=self.s.get(db,'products',pid)
   url=product.get('landing_page') or product.get('website')
   if observation.get('url')!=url:raise Invalid('Probe must match configured product destination')
   ok=observation.get('ok') is True
   row.update(status='completed' if ok else 'blocked',updated_at=now())
   row['evidence'].append(dict(observation,type='https_reachability_only',recorded_at=now(),note='Public response only; signup, ownership, entitlements and actual product identity remain unverified.'))
   self.s.save(db,'execution_tasks',row);self.s.audit(db,'readiness_destination_probed',tid,{'product_id':pid,'reachable':ok,'commercial_changes':0},actor)
