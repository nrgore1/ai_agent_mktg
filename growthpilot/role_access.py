"""Server-enforced human role accounts; no external execution authority."""
import copy
from .business_os import UNITS, ROLES
from .core import Invalid, digest, now

def validate_scope(company, role, units):
 if company not in ('atmakosh','vireoka') or role not in ROLES:
  raise Invalid('Choose a company and a business role')
 available=[u for u in UNITS if u['company_id']==company]
 if not isinstance(units,list) or not units or len(set(units))!=len(units) or any(u not in [x['id'] for x in available] for u in units):
  raise Invalid('Choose business units belonging to the selected company')
 return [u for u in available if u['id'] in units]

def create_account(identity, data, actor):
 if actor.get('role')!='founder': raise PermissionError('Founder required for role accounts')
 if set(data)!= {'username','password','company','business_role','units'}: raise Invalid('Exact role account fields required')
 units=validate_scope(data['company'],data['business_role'],data['units'])
 return identity.create(data['username'],data['password'],'business',
  sorted({p for u in units for p in u['product_ids']}), grants=[(u,data['business_role']) for u in units], actor=actor['username'])

def scope_summary(user, result):
 if user.get('role')!='business': return result
 result=copy.deepcopy(result)
 roles={u['id']:set(u['roles']) for u in result['units']}
 visible=[]
 for c in result['cases']:
  allowed=roles[c['unit_id']]
  if 'CEO' not in allowed and not any(s['role'] in allowed for s in c['steps']): continue
  c.pop('history',None)
  if 'CEO' not in allowed:
   for s in c['steps']:
    if s['role'] not in allowed:
     for k in list(s):
      if k not in ('title','role','acceptance','status','approval_required'): del s[k]
   c.pop('close_note',None);c.pop('closed_by',None)
  visible.append(c)
 result['cases']=visible
 caseids={c['id'] for c in visible}
 result['role_workers']['jobs']=[j for j in result['role_workers']['jobs'] if j['case_id'] in caseids and j['role'] in roles.get(j['unit_id'],set())]
 records=[r for r in result['vanguard']['records'] if roles.get(r.get('unit_id'),set()) & {'CEO','CMO'} and ('CEO' in roles.get(r.get('unit_id'),set()) or r.get('kind') in ('design_partner','customer','champion'))]
 result['vanguard']['records']=records
 result['vanguard']['source_count']=len(records)
 result['marketing_decisions']=[]
 result['users']=[];result['unmapped_products']=[]
 result['can_assign']=False;result['can_review']=False
 role_set=set().union(*roles.values()) if roles else set()
 result['roles']={k:v for k,v in result['roles'].items() if k in role_set}
 result['dashboard_tabs']=['overview','work','processes','workers']
 if role_set & {'CEO','CMO'}: result['dashboard_tabs'].append('opportunities')
 if role_set & {'CEO','CFO'}: result['dashboard_tabs'].append('finance')
 for u in result['units']:
  scoped=[c for c in visible if c['unit_id']==u['id']]
  u['metrics']['open_cases']=sum(c['status'] not in ('completed','closed') for c in scoped)
  u['metrics']['decisions']=sum(c['status']=='awaiting_review' for c in scoped)
 return result

def manage_account(identity, data, actor):
 if actor.get('role')!='founder':raise PermissionError('Founder required for account management')
 if set(data) not in ({'username','password'},{'username','enabled'}):raise Invalid('Choose password reset or account access change')
 from .identity import password_hash
 import secrets
 if 'password' in data and (not isinstance(data['password'],str) or not 14<=len(data['password'])<=1024):raise Invalid('Password must contain 14 to 1024 characters')
 if 'enabled' in data and type(data['enabled']) is not bool:raise Invalid('Enabled must be a boolean')
 with identity.store.db() as db:
  row=db.execute('SELECT role FROM users WHERE id=?',(data['username'],)).fetchone()
  if not row or row['role']!='business':raise Invalid('Only role accounts can be managed here')
  if 'password' in data:
   salt=secrets.token_hex(16)
   db.execute('UPDATE users SET password=?,salt=?,must_change=1 WHERE id=?',(password_hash(data['password'],salt),salt,data['username']))
   action='role_password_reset'
  else:
   db.execute('UPDATE users SET enabled=? WHERE id=?',(int(data['enabled']),data['username']))
   action='role_account_access'
  db.execute('DELETE FROM sessions WHERE user_id=?',(data['username'],))
  identity.store.audit(db,action,data['username'],{'sessions_revoked':True,**({'enabled':data['enabled']} if 'enabled' in data else {})},actor['username'])
 return {'username':data['username'],'sessions_revoked':True}
