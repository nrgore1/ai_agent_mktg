"""Run as the application user. Passwords are discarded; founder sets them privately in Accounts."""
import secrets
from growthpilot.platform import Platform
from growthpilot.identity import Identity
from growthpilot.role_access import create_account
from growthpilot.business_os import ROLES,UNITS
import os,json
s=Platform(os.environ.get('GROWTHPILOT_DB','/app/data/growthpilot.db'));identity=Identity(s)
existing={u['username'] for u in identity.users()};created=[]
for company in ('atmakosh','vireoka'):
 for role in ROLES:
  username=company+'.'+role.lower()
  if username in existing: continue
  create_account(identity,dict(username=username,password=secrets.token_urlsafe(36),company=company,business_role=role,units=[u['id'] for u in UNITS if u['company_id']==company]),{'role':'founder','username':'founder'})
  created.append(username)
print(json.dumps({'created':created,'passwords':'Not stored or displayed. Founder must set a temporary password in Accounts before handing over each login.'}))
