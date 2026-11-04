import unittest,tempfile,subprocess,socket,os,sys,time,json,http.cookiejar,urllib.request,urllib.error
from pathlib import Path
from growthpilot.platform import Platform
from growthpilot.identity import Identity
class UserManagementHttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.db=Path(cls.tmp.name)/'db';s=Platform(cls.db);Identity(s).create('founder','Owner-Synthetic-Password','founder')
  with socket.socket()as sock:sock.bind(('127.0.0.1',0));cls.port=sock.getsockname()[1]
  cls.url='http://127.0.0.1:'+str(cls.port);cls.proc=subprocess.Popen([sys.executable,'-m','growthpilot.server','--port',str(cls.port)],env=dict(os.environ,GROWTHPILOT_DB=str(cls.db)),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(100):
   try:urllib.request.urlopen(cls.url+'/health',timeout=1);break
   except OSError:time.sleep(.1)
 @classmethod
 def tearDownClass(cls):cls.proc.terminate();cls.proc.wait(timeout=10);cls.tmp.cleanup()
 def call(self,c,path,data=None,csrf=''):
  return json.load(c.open(urllib.request.Request(self.url+'/api/'+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json','X-CSRF-Token':csrf}),timeout=30))
 def client(self,user,password):
  c=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));result=self.call(c,'login',dict(username=user,password=password));return c,result
 def denied(self,c,path,data=None,csrf='',status=403):
  with self.assertRaises(urllib.error.HTTPError)as e:self.call(c,path,data,csrf)
  self.assertEqual(e.exception.code,status,path)
 def create(self,f,fc,name,roles,company='atmakosh',units=None):
  return self.call(f,'user-management/create',{'username':name,'password':'Temporary-Synthetic-Password','display_name':name,'company':company,'roles':roles,'units':units or ['weddingos'],'note':'Create a scoped synthetic account for HTTP acceptance.'},fc)
 def ready(self,name):
  c,login=self.client(name,'Temporary-Synthetic-Password')
  self.denied(c,'user-management')
  self.call(c,'password',{'old':'Temporary-Synthetic-Password','new':'Personal-Synthetic-Password'},login['csrf'])
  return self.client(name,'Personal-Synthetic-Password')
 def test_president_full_crud_http_csrf_and_stale_version(self):
  f,login=self.client('founder','Owner-Synthetic-Password');fc=login['csrf'];self.assertTrue(login['can_manage_users'])
  self.denied(f,'user-management/create',{},'')
  self.create(f,fc,'http-staff',['BILLING','INVOICING'])
  row=next(u for u in self.call(f,'user-management')['users']if u['username']=='http-staff')
  self.call(f,'user-management/update',{'username':row['username'],'version':row['version'],'display_name':'Updated person','company':'atmakosh','roles':['SUPPORT'],'units':['jodibana'],'note':'Update scoped staff role and unit after owner review.'},fc)
  self.denied(f,'user-management/disable',{'username':row['username'],'version':row['version'],'note':'This stale version must be rejected safely.'},fc,400)
  row=next(u for u in self.call(f,'user-management')['users']if u['username']=='http-staff')
  self.call(f,'user-management/delete',{'username':row['username'],'version':row['version'],'confirm_username':row['username'],'note':'Delete only synthetic account access after verification.'},fc)
  self.denied(urllib.request.build_opener(),'login',dict(username='http-staff',password='Temporary-Synthetic-Password'),status=401)
 def test_department_and_auditor_http_denials(self):
  f,l=self.client('founder','Owner-Synthetic-Password');self.create(f,l['csrf'],'http-billing',['BILLING']);self.create(f,l['csrf'],'http-audit',['AUDITOR'])
  for name in ['http-billing','http-audit']:
   c,l=self.ready(name);self.assertFalse(l['can_manage_users'])
   for path in ['user-management','users','execution','integrations','audit/verify']:self.denied(c,path)
   for path in ['user-management/create','user-management/reset_password','role-accounts','users','business/assign','business/review']:
    self.denied(c,path,{},l['csrf'])
   d=self.call(c,'business');self.assertEqual({u['id']for u in d['units']},{'weddingos'})
   if name=='http-audit':
    self.assertTrue(d['read_only'])
    for path in ['business/create','business/manual-create','business/manual-action','business/human-review']:self.denied(c,path,{},l['csrf'])
 def test_company_admin_cannot_promote_or_manage_president(self):
  f,l=self.client('founder','Owner-Synthetic-Password');self.create(f,l['csrf'],'http-admin',['USER_ADMIN'])
  a,al=self.ready('http-admin');self.assertTrue(al['can_manage_users'])
  self.create(a,al['csrf'],'http-team-support',['SUPPORT'])
  data={'username':'escalated','password':'Temporary-Synthetic-Password','display_name':'No escalation','company':'atmakosh','roles':['CEO'],'units':['weddingos'],'note':'Forbidden attempt to grant an executive role.'}
  self.denied(a,'user-management/create',data,al['csrf'])
  data['roles']=['USER_ADMIN'];self.denied(a,'user-management/create',data,al['csrf'])
  data['roles']=['BILLING'];data['company']='vireoka';data['units']=['liqmint_individual'];self.denied(a,'user-management/create',data,al['csrf'])
  self.assertNotIn('founder',{u['username']for u in self.call(a,'user-management')['users']})
 def test_anonymous_and_password_gate(self):
  self.denied(urllib.request.build_opener(),'user-management',status=401)
  self.denied(urllib.request.build_opener(),'user-management/create',{},status=401)

