"""Internal scope is an applicability decision, never a passed test or release approval."""
import copy
from .core import Invalid, now
from .manager import stable

PRODUCTS = (10, 11, 12, 13, 14)
POLICY = 'internal-only-20261103-v2'
EXCLUDED = {'pricing', 'partners', 'campaign', 'claims'}
REQUIREMENTS = {
 'health': ('Verify private runtime and access boundary', 'Identify the authoritative runtime and version; verify its private endpoint or local operator entry point, health, and network/access boundary. No public domain or public TLS is required. A source checkout alone is not runtime evidence.'),
 'journey': ('Test internal operator workflow, save and return', 'Dated synthetic internal-operator test: authenticated or OS-restricted access, intended first useful action, save/reload, unauthorized access denial, error recovery and session closure. Record source version and environment. No public signup or customer acquisition required.'),
 'entitlements': ('Verify internal permissions and resource limits', 'Verify operator roles, denied unauthorized access and configured resource/usage limits using synthetic data. Public free/paid tiers, checkout, billing webhooks, cancellation and refunds are outside internal scope. This does not waive access-control or usage tests.'),
 'privacy': ('Verify internal data protection and recovery', 'Inventory internal data and external data rights; verify access, retention/export/deletion, backup restoration and named operational ownership. Financial/data activity restrictions still apply. Public marketing consent is unnecessary unless actually collecting marketing data.'),
 'metering': ('Measure internal resource usage and support cost', 'Measure actual AI/storage/compute/data-provider usage and operator/support time over a named observation period; identify shared-cost allocation. Keep synthetic test usage separate from operating usage; do not invent customers or revenue.'),
 'experiment_spec': ('Prepare internal usefulness and resource evaluation', 'Document the internal operator outcome, measured resource/time baseline, feedback and stop/continue criteria. No public audience, acquisition or campaign required. Preparation is not evidence of actual use.'),
}
REASON = 'Founder-confirmed internal-only product: public pricing, partner commissions, campaign publication and public campaign claims are outside the current scope. No technical check or commercial release is approved.'

def apply(db, store, pid, source, actor):
 """Apply within caller transaction; preserve original rows and artifacts for audit."""
 rows = store.rows(db, 'execution_tasks', pid)
 if not rows:
  raise Invalid('Prepare the product backlog first')
 changed = 0
 for row in rows:
  if row.get('scope_policy') == POLICY:
   continue
  if row['key'] not in EXCLUDED and row['key'] not in REQUIREMENTS:
   continue
  original = copy.deepcopy(row)
  row.setdefault('history', []).append({'type':'scope_before_internal', 'policy':POLICY, 'recorded_at':now(), 'snapshot':original})
  row.update(scope_policy=POLICY, updated_at=now())
  if row['key'] in EXCLUDED:
   row.update(status='not_applicable', scope_reason=REASON)
  else:
   row['title'],row['acceptance']=REQUIREMENTS[row['key']]
   if row['key']=='journey':row['dependencies']=[stable('execution:'+str(pid)+':'+key) for key in ('activation_spec','health')]
   if row['key']=='metering':row['dependencies']=[stable('execution:'+str(pid)+':'+key) for key in ('strategy','experiment_spec')]
   # Public evidence cannot certify the newly scoped internal runtime/workflow.
   if row['status']=='completed' and row['key'] != 'experiment_spec' and not original.get('scope_policy'):
    row['status']='pending'
  row.setdefault('evidence',[]).append({'type':'scope_decision','source':source,'note':REASON if row['key'] in EXCLUDED else 'Internal acceptance criteria replace public-launch assumptions. Existing evidence is retained; remaining checks are not automatically passed.','actor':actor,'recorded_at':now()})
  store.save(db,'execution_tasks',row);changed+=1
 for artifact in store.rows(db,'execution_artifacts',pid):
  if artifact.get('scope_policy')==POLICY:continue
  if artifact['kind'] not in ('activation_spec','experiment_spec'):continue
  artifact.setdefault('history',[]).append({'content':copy.deepcopy(artifact['content']),'recorded_at':now()})
  if artifact['kind']=='activation_spec':
   artifact['content'].update(tests=['Restricted internal operator access','First useful internal action','Save, reload and return','Unauthorized operator denied','Configured resource limits','Error recovery and session closure'],public_signup_required=False)
  else:
   artifact['content']={'scope':'internal_only','operator_outcome':artifact['content'].get('value_to_prove'),'activation_event':artifact['content'].get('activation_event'),'events':['internal_session','internal_outcome','resource_usage','operator_feedback'],'required_dimensions':['product_id','environment','source_version','observed_at'],'controls':['Only actual measurements enter results','Synthetic test traffic remains separate','No public acquisition, campaign or paid conversion target','Financial/data rights and execution restrictions remain'],'pass_condition':'Document observed usefulness, resource costs and operator feedback; preparation alone is not a passed readiness gate.'}
  artifact['scope_policy']=POLICY;store.save(db,'execution_artifacts',artifact)
 return changed

def set_scope(execution, source, actor='founder'):
 if not isinstance(source,str) or not 10<=len(source)<=1000:raise Invalid('Scope decision source required')
 if actor!='founder':raise Invalid('Founder authority required for scope decisions')
 if execution.summary()['source_changed']:raise Invalid('Sync current strategy before reviewing applicability')
 with execution.s.db() as db:
  if execution.s.paused(db):raise Invalid('System paused')
  changed=0
  for pid in PRODUCTS:
   changed+=apply(db,execution.s,pid,source,actor)
   rid=stable('execution-scope:'+str(pid))
   existing=next((x for x in execution.s.rows(db,'execution_scopes',pid) if x['id']==rid),None)
   if not existing or existing.get('policy')!=POLICY:execution.s.save(db,'execution_scopes',{'id':rid,'product_id':pid,'scope':'internal_only','policy':POLICY,'source':source,'actor':actor,'recorded_at':now(),'public_reactivation':'A separate explicit founder scope change and revalidation are required; historical public requirements are retained in task history.'})
  if changed:execution.s.audit(db,'internal_readiness_scope_applied',POLICY,{'products':list(PRODUCTS),'changed_tasks':changed,'not_applicable_keys':sorted(EXCLUDED),'technical_approvals':0,'commercial_changes':0,'source':source},actor)
 return execution.summary()
