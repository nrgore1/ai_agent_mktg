"""Audited account administration; no passwords or integration secrets in directory responses."""
import json,re,secrets
from .core import Invalid,now,digest
from .identity import password_hash
from .business_os import UNITS,ROLES,ACCESS_ROLES
from .saas_roles import SAAS_ROLES,STAFF_DELEGATABLE

def _profile(store,db,username):
 return next((x for x in store.rows(db,'account_profiles')if x['id']==username),{'id':username,'display_name':username,'version':0,'deleted':False})
def _grants(store,db,username):
 return [x for x in store.rows(db,'business_assignments')if x['username']==username and x['enabled']]
def _authority(store,db,actor):
 current=db.execute('SELECT role,enabled FROM users WHERE id=?',(actor.get('username'),)).fetchone()
 if not current or not current['enabled']:raise PermissionError('Active account required')
 if current['role']=='founder':return {'president':True,'units':{u['id']for u in UNITS}}
 if current['role']!='business':raise PermissionError('President or assigned company user administrator required')
 units={g['unit_id']for g in _grants(store,db,actor['username'])if g['role']=='USER_ADMIN'}
 if not units:raise PermissionError('User administration is outside your assigned role')
 return {'president':False,'units':units}
def can_manage(store,actor):
 with store.db()as db:
  try:_authority(store,db,actor);return True
  except PermissionError:return False
def _scoped(authority,grants):
 return bool(grants)and all(g['unit_id']in authority['units']and g['role']in STAFF_DELEGATABLE for g in grants)
def _version(row,profile,grants):
 return digest({'id':row['id'],'role':row['role'],'enabled':row['enabled'],'products':row['products'],'must_change':row['must_change'],'credential_revision':digest([row['password'],row['salt']]),'profile':profile,'grants':sorted(grants,key=lambda g:g['id'])})
def _safe(store,db,row,auth,actor):
 profile=_profile(store,db,row['id']);grants=_grants(store,db,row['id']);protected=row['role']=='founder' or row['id']==actor['username']
 return {'username':row['id'],'display_name':profile['display_name'],'system_role':row['role'],'enabled':bool(row['enabled']),'must_change':bool(row['must_change']),'deleted':profile.get('deleted',False),'version':_version(row,profile,grants),'grants':[{'company':g['company_id'],'unit':g['unit_id'],'role':g['role']}for g in grants],'can_edit':not protected and not profile.get('deleted',False)and(auth['president']or(row['role']=='business'and _scoped(auth,grants))),'protected':protected}
def directory(identity,actor):
 store=identity.store
 with store.db()as db:
  auth=_authority(store,db,actor);users=[]
  for row in db.execute('SELECT * FROM users ORDER BY id'):
   grants=_grants(store,db,row['id'])
   if auth['president']or row['id']==actor['username']or(row['role']=='business'and _scoped(auth,grants)):
    users.append(_safe(store,db,row,auth,actor))
  roles={k:{'name':k,'description':v,'ai_preparation':k in ROLES,'read_only':k=='AUDITOR','delegatable':k in STAFF_DELEGATABLE}for k,v in ACCESS_ROLES.items()}
  return {'is_president':auth['president'],'users':users,'roles':roles,'assignable_roles':list(ACCESS_ROLES)if auth['president']else sorted(STAFF_DELEGATABLE),'units':[dict(u)for u in UNITS if u['id']in auth['units']],'note':'Delete revokes access and retains an audit tombstone. President accounts are protected. SaaS role workflows record evidence; they cannot charge, issue invoices, refund, publish or deploy.'}
def _scope(data,auth):
 company=data.get('company');roles=data.get('roles');units=data.get('units')
 if company not in ('vireoka','atmakosh'):raise Invalid('Choose a company')
 if not isinstance(roles,list)or not roles or len(roles)!=len(set(roles))or any(r not in ACCESS_ROLES for r in roles):raise Invalid('Choose valid roles')
 if not isinstance(units,list)or not units or len(units)!=len(set(units)):raise Invalid('Choose distinct units')
 chosen=[u for u in UNITS if u['id']in units]
 if len(chosen)!=len(units)or any(u['company_id']!=company or u['id']not in auth['units']for u in chosen):raise PermissionError('Company or unit outside delegated scope')
 if not auth['president']and any(r not in STAFF_DELEGATABLE for r in roles):raise PermissionError('Only the President grants executive and user administrator roles')
 return chosen,roles
def _text(value,label,maximum=160,minimum=1):
 if not isinstance(value,str)or not minimum<=len(value.strip())<=maximum:raise Invalid('Valid '+label+' required')
 return value.strip()
def _password(value):
 if not isinstance(value,str)or not 14<=len(value)<=1024:raise Invalid('Temporary password must contain 14 to 1024 characters')
 salt=secrets.token_hex(16);return salt,password_hash(value,salt)
def dispatch(identity,action,data,actor):
 fields={
 'create':{'username','password','display_name','company','roles','units','note'},
 'update':{'username','version','display_name','company','roles','units','note'},
 'reset_password':{'username','version','password','note'},
 'disable':{'username','version','note'},
 'enable':{'username','version','note'},
 'delete':{'username','version','confirm_username','note'}}
 if action not in fields or not isinstance(data,dict)or set(data)!=fields[action]:raise Invalid('Exact account operation fields required')
 username=_text(data['username'],'username',80);note=_text(data['note'],'reason',2000,20)
 if not re.fullmatch(r'[a-zA-Z0-9_.@-]{1,80}',username):raise Invalid('Invalid username')
 credential=_password(data['password'])if action in ('create','reset_password')else None
 store=identity.store
 with store.db()as db:
  auth=_authority(store,db,actor)
  if action=='create':
   units,roles=_scope(data,auth);display=_text(data['display_name'],'display name')
   if db.execute('SELECT 1 FROM users WHERE lower(id)=lower(?)',(username,)).fetchone():raise Invalid('Username already exists or is retained in audit history')
   salt,hashed=credential
   db.execute('INSERT INTO users(id,password,salt,role,products,enabled,must_change)VALUES(?,?,?,?,?,1,1)',(username,hashed,salt,'business',json.dumps(sorted({p for u in units for p in u['product_ids']}))))
   profile={'id':username,'display_name':display,'version':1,'deleted':False,'created_at':now()}
  else:
   row=db.execute('SELECT * FROM users WHERE id=?',(username,)).fetchone()
   if not row:raise Invalid('Account unavailable')
   profile=_profile(store,db,username);grants=_grants(store,db,username)
   if row['role']=='founder' or username==actor['username']:raise PermissionError('President and your own account are protected; use personal password settings')
   if not auth['president']and(row['role']!='business'or not _scoped(auth,grants)):raise PermissionError('Account outside delegated scope')
   if profile.get('deleted'):raise Invalid('Deleted account is retained only for audit; create a new named login')
   if data['version']!=_version(row,profile,grants):raise Invalid('Account changed; refresh before saving')
   profile['version']+=1
   if action=='update':
    units,roles=_scope(data,auth);profile['display_name']=_text(data['display_name'],'display name')
    db.execute('UPDATE users SET role=?,products=? WHERE id=?',('business',json.dumps(sorted({p for u in units for p in u['product_ids']})),username))
   elif action=='reset_password':
    salt,hashed=credential;db.execute('UPDATE users SET salt=?,password=?,must_change=1 WHERE id=?',(salt,hashed,username))
   elif action in ('enable','disable'):db.execute('UPDATE users SET enabled=? WHERE id=?',(int(action=='enable'),username))
   elif action=='delete':
    if data['confirm_username']!=username:raise Invalid('Type the exact username to delete access')
    salt=secrets.token_hex(16);db.execute('UPDATE users SET enabled=0,salt=?,password=? WHERE id=?',(salt,password_hash(secrets.token_urlsafe(48),salt),username))
    profile.update(deleted=True,deleted_at=now(),display_name='Deleted account')
  if action in ('update','delete'):
   for g in store.rows(db,'business_assignments'):
    if g['username']==username and g['enabled']:g.update(enabled=False,updated_at=now());store.save(db,'business_assignments',g)
  if action in ('create','update'):
   for unit in units:
    for role in roles:
     g={'id':digest([username,unit['id'],role]),'username':username,'unit_id':unit['id'],'company_id':unit['company_id'],'role':role,'enabled':True,'updated_at':now()}
     store.save(db,'business_assignments',g)
  profile.update(updated_at=now(),updated_by=actor['username']);store.save(db,'account_profiles',profile)
  db.execute('DELETE FROM sessions WHERE user_id=?',(username,))
  store.audit(db,'user_management_'+action,username,{'note':note,'sessions_revoked':True,'roles':roles if action in ('create','update')else None,'units':[u['id']for u in units]if action in ('create','update')else None,'credentials_logged':False},actor['username'])
  return {'username':username,'action':action,'sessions_revoked':True,'must_change':action in ('create','reset_password'),'deleted':action=='delete'}

