"""Actual HTTP+database staging acceptance; no API stubs or production credentials."""
import datetime as dt,email as mail,email.policy,http.cookiejar,json,re,subprocess,urllib.request,urllib.error,uuid
from pathlib import Path
ROOT=Path.home()/'agentvire-launch-qa-20261027';cfg=json.loads((ROOT/'compose.json').read_text());run=uuid.uuid4().hex[:10];results=[]
class Client:
 def __init__(self,port):self.base='http://127.0.0.1:'+str(port);self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));self.token=None
 def call(self,path,payload=None,method=None,headers=None):
  h={'Content-Type':'application/json',**({'Authorization':'Bearer '+self.token}if self.token else {}),**(headers or {})}
  req=urllib.request.Request(self.base+path,data=json.dumps(payload).encode() if payload is not None else None,headers=h,method=method)
  try:
   with self.opener.open(req,timeout=35)as r:
    raw=r.read();return r.status,json.loads(raw)if raw and 'json' in r.headers.get('Content-Type','')else raw.decode(errors='replace')[:100]
  except urllib.error.HTTPError as e:
   raw=e.read()
   try:return e.code,json.loads(raw)
   except ValueError:return e.code,raw.decode(errors='replace')[:100]
def check(product,name,condition,detail=''):
 row={'product':product,'check':name,'passed':bool(condition),'detail':str(detail)[:250]};results.append(row);print(json.dumps(row),flush=True)
def script(key,code):
 raw=subprocess.check_output(['docker','exec','-i','agentvire-signup-qa-'+key+'-api-1','python','-c',code]);return json.loads(raw)
def mail_code(key,address):
 code='''from pathlib import Path
import email,email.policy,json,re
messages=[]
for p in Path('/tmp/qa-mail').glob('*'):
 m=email.message_from_bytes(p.read_bytes(),policy=email.policy.default)
 if ADDRESS.lower() not in str(m.get('To','')).lower():continue
 body=' '.join(part.get_payload(decode=True).decode(errors='replace')for part in m.walk()if part.get_content_type()=='text/plain')
 found=re.search(r'\\b(\\d{6})\\b',body)
 if found:messages.append((p.stat().st_mtime,found[1]))
print(json.dumps(sorted(messages)[-1][1]if messages else None))
'''.replace('ADDRESS',repr(address))
  # Only a synthetic mailbox code returns to this runner; never printed or persisted.
 value=script(key,code)
 if not value:raise RuntimeError('Synthetic staging mail was not captured')
 return value
def login_liq(key,port,address,password):
 client=Client(port);status,start=client.call('/api/access/login/start/',{'identifier':address,'email':address,'password':password})
 check(key,'password starts real MFA challenge',status==200 and bool(start.get('challenge_id')),str(status)+': '+str(start.get('code','')))
 if status!=200:raise RuntimeError('MFA login start failed '+str(start.get('error',''))[:140])
 code=mail_code(key,address);wrong='000001'if code=='000000'else'000000'
 bad=client.call('/api/access/login/verify/',{'challenge_id':start['challenge_id'],'code':wrong});check(key,'wrong login MFA rejected',bad[0]>=400)
 status,verified=client.call('/api/access/login/verify/',{'challenge_id':start['challenge_id'],'code':code})
 check(key,'real MFA login establishes session',status==200 and bool(verified.get('access_token')or verified.get('access')),status)
 if status!=200:raise RuntimeError('MFA verify failed '+str(verified.get('error',''))[:140])
 client.token=verified.get('access_token')or verified.get('access');return client

password='Synthetic-signup-QA-'+run+'!'
try:
 key='individual';port=18281;c=Client(port);address='signup-'+run+'@example.com'
 status,start=c.call('/api/access/retail-mfa/start/',{'email':address,'first_name':'Synthetic QA','source':'agentvire_fullstack_signup_qa'})
 check(key,'signup generates real email MFA',status==200 and bool(start.get('challenge_id')),str(status)+': '+str(start.get('code','')))
 if status!=200:raise RuntimeError(str(start.get('error',''))[:140])
 check(key,'MFA secret not exposed in public response','dev_code'not in start and 'code'not in start)
 code=mail_code(key,address);status,verified=c.call('/api/access/retail-mfa/verify/',{'email':address,'challenge_id':start['challenge_id'],'code':code})
 check(key,'signup verifies captured real OTP',status==200 and bool(verified.get('mfa_token')),status)
 if status!=200:raise RuntimeError('signup OTP verification failed')
 status,created=c.call('/api/access/complete-account-setup/',{'email':address,'username':address,'password':password,'confirm_password':password,'mfa_token':verified['mfa_token'],'plan':'basic','preferred_mfa_method':'email_otp'})
 check(key,'verified free account setup',status==200 and created.get('ok')is True,str(status)+': '+str(created.get('code','')))
 if status!=200:raise RuntimeError(str(created.get('error',''))[:140])
 replay=c.call('/api/access/complete-account-setup/',{'email':address,'username':address,'password':password,'confirm_password':password,'mfa_token':verified['mfa_token'],'plan':'basic'})
 check(key,'consumed account setup verification rejected',replay[0]>=400)
 signed=login_liq(key,port,address,password)
 status,me=signed.call('/api/security-iam/me/');check(key,'signed-in profile accessible',status==200,status)
 anon=Client(port).call('/api/security-iam/me/');check(key,'anonymous response contains no account or tenant data',anon[0]in(401,403)or(anon[0]==200 and anon[1].get('authenticated')is False and not anon[1].get('user',{}).get('id')and not anon[1].get('user',{}).get('email')and not anon[1].get('organization',{}).get('id')))
 status,layers=signed.call('/api/stablecoin-intelligence/data-layers/');check(key,'first read-only workflow context loads',status==200,status)
except Exception as exc:check('individual','flow completed',False,str(exc))

try:
 key='institutional';port=18282
 seed='''import os,json,django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.launch_staging_settings');django.setup()
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.security_iam.models import Organization,Membership,UserSecurityProfile
assert settings.DATABASES['default']['NAME']=='agentvire_institutional_signup_qa'
out=[]
for index,role in [(0,'organization_admin'),(1,'organization_admin'),(2,'institution_analyst')]:
 org=Organization.objects.get_or_create(slug='signup-qa-'+RUN+'-'+str(index if index<2 else 0),defaults={'name':'SYNTHETIC Signup QA '+str(index),'plan':'institutional_pro','onboarding_status':'active','profile_metadata':{'synthetic_test_only':True}})[0]
 address='institution-'+RUN+'-'+str(index)+'@example.com'
 user=get_user_model().objects.create_user(username=address,email=address,password=PASSWORD)
 Membership.objects.create(user=user,organization=org,role=role,is_active=True)
 UserSecurityProfile.objects.update_or_create(user=user,defaults={'email_verified':True,'mfa_required':True,'mfa_enabled':True})
 user.groups.add(Group.objects.get_or_create(name='institution_admin'if role=='organization_admin'else'analyst')[0])
 out.append({'email':address,'organization_id':org.id,'organization_slug':org.slug})
print(json.dumps(out))
'''.replace('RUN',repr(run)).replace('PASSWORD',repr(password))
 users=script(key,seed);a=login_liq(key,port,users[0]['email'],password);b=login_liq(key,port,users[1]['email'],password)
 status,profile=a.call('/api/security-iam/organization/profile/');check(key,'provisioned tenant profile accessible after MFA',status==200,str(status)+': '+str(profile.get('code','')))
 if status==200:
  check(key,'profile scoped to authenticated tenant',profile['organization']['id']==users[0]['organization_id'])
  status,changed=a.call('/api/security-iam/organization/profile/',{'legal_name':'SYNTHETIC QA PERSISTED '+run},method='PATCH');check(key,'authorized tenant profile save',status==200,status)
  again=login_liq(key,port,users[0]['email'],password);status,persisted=again.call('/api/security-iam/organization/profile/');check(key,'saved tenant state survives fresh login',status==200 and persisted.get('organization',{}).get('legal_name')=='SYNTHETIC QA PERSISTED '+run)
  status,other=b.call('/api/security-iam/organization/profile/');check(key,'second tenant cannot see first tenant state',status==200 and other.get('organization',{}).get('id')==users[1]['organization_id'] and other.get('organization',{}).get('legal_name')!='SYNTHETIC QA PERSISTED '+run)
  forged=a.call('/api/security-iam/organization/profile/',headers={'X-LiqMint-Organization':users[1]['organization_slug'],'X-Tenant-ID':str(users[1]['organization_id'])});check(key,'forged tenant header does not cross tenant boundary',forged[0]in(400,403,404)or forged[1].get('organization',{}).get('id')==users[0]['organization_id'])
 analyst=login_liq(key,port,users[2]['email'],password);denied=analyst.call('/api/security-iam/organization/profile/',{'legal_name':'UNAUTHORIZED QA'},method='PATCH');check(key,'analyst cannot administer tenant',denied[0]in(401,403))
 blocked=Client(port).call('/api/access/retail-mfa/start/',{'email':'blocked-'+run+'@example.com'});check(key,'consumer signup remains blocked',blocked[0]in(403,404))
except Exception as exc:check('institutional','flow completed',False,str(exc))

try:
 key='ora';port=18283;c=Client(port);address='ora-'+run+'@example.com'
 status,registered=c.call('/api/core/auth/register',{'username':address,'email':address,'password':password,'org_name':'Synthetic QA '+run});check(key,'real signup creates user, free workspace and session',status==201 and bool(registered.get('access')),status)
 if status!=201:raise RuntimeError(str(registered.get('detail',''))[:140])
 c.token=registered['access'];status,catalog=c.call('/api/core/goal-profiles');check(key,'activation goal catalog available',status==200 and bool(catalog.get('profiles')),status)
 goal=catalog['profiles'][0]['key'];status,saved=c.call('/api/core/me/goal',{'goal':goal});check(key,'selected goal persisted to account',status==200 and saved.get('goal')==goal,status)
 fresh=Client(port);status,logged=fresh.call('/api/core/auth/login',{'username':address,'password':password});check(key,'returning user sign-in establishes session',status==200 and bool(logged.get('access')),status);fresh.token=logged.get('access')
 status,persisted=fresh.call('/api/core/me/goal');check(key,'activation goal survives fresh login',status==200 and persisted.get('goal')==goal,status)
 status,score=c.call('/api/core/practice/score',{'transcript':'First I will explain the problem. Second, our team helped 12 customers. Finally, I will summarize the next step.','duration_sec':30,'scenario':'Synthetic presentation QA'});check(key,'server computes transparent practice feedback',status==200 and isinstance(score.get('overall'),(int,float)) and bool(score.get('feedback')),str(status)+': '+str(score.get('method')))
 if status!=200:raise RuntimeError('scoring failed')
 status,session=c.call('/api/core/practice-sessions',{'scenario_id':'synthetic-qa','scenario_title':'Synthetic QA','pillar':'Business Communication','duration_sec':30,'transcript':'Synthetic staging rehearsal '+run,'scores':score});check(key,'practice result saved to signed-in account',status==201,status)
 status,listed=fresh.call('/api/core/practice-sessions');rows=listed.get('results',[])if isinstance(listed,dict)else listed;check(key,'practice result survives fresh sign-in',status==200 and any(str(p.get('id'))==str(session.get('id'))for p in rows),status)
 status,detail=fresh.call('/api/core/practice-sessions/'+str(session.get('id')));check(key,'saved practice result opens by ID',status==200,status)
 other=Client(port);otheraddress='ora-other-'+run+'@example.com';status,otheruser=other.call('/api/core/auth/register',{'username':otheraddress,'email':otheraddress,'password':password});other.token=otheruser.get('access');status,otherdetail=other.call('/api/core/practice-sessions/'+str(session.get('id')));check(key,'other account cannot open saved practice',status in(403,404),status)
 status,refreshed=c.call('/api/core/auth/refresh',{});check(key,'cookie session refresh works through frontend proxy',status==200 and bool(refreshed.get('access')),status)
 status,logout=c.call('/api/core/auth/logout',{});check(key,'sign-out succeeds',status==200,status);status,after=c.call('/api/core/auth/refresh',{});check(key,'sign-out clears refresh access',status in(400,401,403),status)
except Exception as exc:check('ora','flow completed',False,str(exc))
receipt={'run_id':run,'recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),'mode':'isolated_vps_full_stack_actual_http','results':results,'passed':sum(r['passed']for r in results),'failed':sum(not r['passed']for r in results),'production_changed':False,'email_delivery':'real generated OTP captured in guarded synthetic mail adapter; external inbox delivery unverified','llm_scoring':'Response method recorded; heuristic fallback is not LLM service proof','commercial_approvals':'pending_founder_approval'}
(ROOT/('fullstack-'+run+'.json')).write_text(json.dumps(receipt,indent=2));(ROOT/'latest-fullstack.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({'passed':receipt['passed'],'failed':receipt['failed'],'run_id':run}),flush=True)
