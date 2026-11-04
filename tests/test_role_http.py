import http.cookiejar,json,os,socket,subprocess,sys,tempfile,time,unittest,urllib.request,urllib.error
from pathlib import Path
from growthpilot.platform import Platform
from growthpilot.identity import Identity

class RoleHttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.db=Path(cls.tmp.name)/'test.db';s=Platform(cls.db);i=Identity(s)
  i.create('founder','Founder-Password-Long','founder')
  i.create('admin','Admin-Password-Long','admin')
  with socket.socket() as sock:sock.bind(('127.0.0.1',0));cls.port=sock.getsockname()[1]
  cls.url='http://127.0.0.1:'+str(cls.port)
  cls.process=subprocess.Popen([sys.executable,'-m','growthpilot.server','--port',str(cls.port)],env=dict(os.environ,GROWTHPILOT_DB=str(cls.db)),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(100):
   try:urllib.request.urlopen(cls.url+'/health',timeout=1);break
   except OSError:time.sleep(.1)
 @classmethod
 def tearDownClass(cls):cls.process.terminate();cls.process.wait(timeout=10);cls.tmp.cleanup()
 def client(self,name,password):
  c=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  r=self.call(c,'login',dict(username=name,password=password));return c,r['csrf']
 def call(self,c,path,data=None,csrf=''):
  req=urllib.request.Request(self.url+'/api/'+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json','X-CSRF-Token':csrf})
  return json.load(c.open(req,timeout=15))
 def denied(self,c,path,data=None,csrf='',code=403):
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(c,path,data,csrf)
  self.assertEqual(e.exception.code,code,path)
 def test_all_role_http_boundaries_and_password_gate(self):
  from growthpilot.business_os import ROLES,UNITS
  f,fc=self.client('founder','Founder-Password-Long')
  for company in ('atmakosh','vireoka'):
   for role in ROLES:
    username=company+'-'+role.lower()
    self.call(f,'role-accounts',dict(username=username,password='Temporary-Password-Long',company=company,business_role=role,units=[u['id'] for u in UNITS if u['company_id']==company]),fc)
    c,csrf=self.client(username,'Temporary-Password-Long')
    self.denied(c,'business')
    self.denied(c,'business/create',{},csrf)
    self.call(c,'password',{'old':'Temporary-Password-Long','new':'Personal-Password-Long'},csrf)
    self.denied(c,'me',code=401)
    c,csrf=self.client(username,'Personal-Password-Long')
    d=self.call(c,'business');self.assertEqual([x['id'] for x in d['companies']],[company])
    self.assertEqual(set(d['roles']),{role})
    self.assertEqual(set(self.call(c,'state')),{'products','paused'})
    for path in ['execution','strategy','integrations','users','audit/verify','report','report?product_id=4']:
     self.denied(c,path)
    for path in ['users','role-accounts','pause','plan','keys','backup','leads','events','actions/fake/approve','business/review','business/assign','business/worker-control','records/products/4']:
     self.denied(c,path,{},csrf)
    other='weddingos' if company=='vireoka' else 'liqmint_individual'
    self.denied(c,'business/create',dict(unit_id=other,process='sales',title='Forbidden company case',owner=username,due_date='2026-12-01',reference='test:forbidden'),csrf)
 def test_admin_cannot_create_founder(self):
  c,csrf=self.client('admin','Admin-Password-Long')
  self.denied(c,'users',dict(username='escalated',password='Long-Password-Example',role='founder'),csrf)
  self.denied(c,'role-accounts',{},csrf)
 def test_private_paths_anonymous_denied_and_headers(self):
  for path in ['/api/state','/api/business','/api/execution','/data/growthpilot.db','/.env','/.git/config','/docs/private.pdf','/backups/test']:
   with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(self.url+path)
   self.assertEqual(e.exception.code,401,path)
  r=urllib.request.urlopen(self.url+'/')
  self.assertEqual(r.headers['Cache-Control'],'no-store')
  self.assertIn('noindex',r.headers['X-Robots-Tag'])
  self.assertEqual(r.headers['X-Frame-Options'],'DENY')
  self.assertIn(b'Disallow: /',urllib.request.urlopen(self.url+'/robots.txt').read())
 def test_missing_csrf_denies_account_creation(self):
  c,_=self.client('founder','Founder-Password-Long');self.denied(c,'role-accounts',{})

 def test_role_write_response_does_not_disclose_other_role_notes(self):
  f,fc=self.client('founder','Founder-Password-Long')
  self.call(f,'role-accounts',dict(username='response-cmo',password='Temporary-Password-Long',company='atmakosh',business_role='CMO',units=['weddingos']),fc)
  c,csrf=self.client('response-cmo','Temporary-Password-Long')
  self.call(c,'password',{'old':'Temporary-Password-Long','new':'Personal-Password-Long'},csrf)
  c,csrf=self.client('response-cmo','Personal-Password-Long')
  case=self.call(c,'business/create',dict(unit_id='weddingos',process='sales',title='Response privacy fixture',owner='response-cmo',due_date='2026-12-01',reference='test:privacy'),csrf)
  self.assertNotIn('steps',case);self.assertNotIn('history',case)
  s=Platform(self.db)
  with s.db() as db:
   row=s.get(db,'business_cases',case['id'])
   row['steps'][1]['note']='PRIVATE CFO NOTES'
   s.save(db,'business_cases',row)
  response=self.call(c,'business/record',dict(id=case['id'],version=1,status='in_progress',source='test:source',note='The customer scope review is in progress.'),csrf)
  self.assertNotIn('PRIVATE',str(response));self.assertNotIn('steps',response);self.assertNotIn('history',response)
