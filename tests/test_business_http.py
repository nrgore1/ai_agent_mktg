import http.cookiejar,json,os,socket,subprocess,sys,tempfile,time,unittest,urllib.request,urllib.error
from pathlib import Path
from growthpilot.platform import Platform
from growthpilot.identity import Identity

class BusinessHttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.path=Path(cls.tmp.name)/'test.db';s=Platform(cls.path);i=Identity(s)
  for name,role,pids in [('founder','founder',[]),('operator','operator',[4]),('viewer','viewer',[4])]:i.create(name,'Test-password-Long-Only',role,pids)
  with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  cls.url='http://127.0.0.1:'+str(port);cls.process=subprocess.Popen([sys.executable,'-m','growthpilot.server','--port',str(port)],env=dict(os.environ,GROWTHPILOT_DB=str(cls.path),GROWTHPILOT_ENABLE_RETENTION='false'),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(150):
   try:urllib.request.urlopen(cls.url+'/health',timeout=1);break
   except OSError:time.sleep(.1)
 @classmethod
 def tearDownClass(cls):cls.process.terminate();cls.process.wait(timeout=10);cls.tmp.cleanup()
 def call(self,o,path,data=None,csrf=None):
  request=urllib.request.Request(self.url+'/api/'+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json',**({'X-CSRF-Token':csrf} if csrf else {})})
  return json.load(o.open(request,timeout=15))
 def client(self,name='founder'):
  o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));r=self.call(o,'login',{'username':name,'password':'Test-password-Long-Only'});return o,r['csrf']
 def create(self,o,csrf,unit='weddingos'):
  return self.call(o,'business/create',dict(unit_id=unit,process='sales',title='HTTP workflow opportunity',owner='founder',due_date='2026-12-01',reference='http:test'),csrf)
 def test_anonymous_denied_and_asset_public(self):
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(urllib.request.build_opener(),'business')
  self.assertEqual(e.exception.code,401)
  self.assertIn(b'/business.js',urllib.request.urlopen(self.url+'/').read());self.assertIn(b'Business command center',urllib.request.urlopen(self.url+'/business.js').read())
 def test_csrf_and_origin(self):
  o,c=self.client()
  with self.assertRaises(urllib.error.HTTPError) as e:self.create(o,None)
  self.assertEqual(e.exception.code,403)
  req=urllib.request.Request(self.url+'/api/business/create',data=b'{}',headers={'Content-Type':'application/json','X-CSRF-Token':c,'Origin':'https://untrusted.example'})
  with self.assertRaises(urllib.error.HTTPError) as e:o.open(req)
  self.assertEqual(e.exception.code,403)
 def test_unit_scope_and_role_assignment(self):
  o,c=self.client();self.call(o,'business/assign',dict(username='operator',unit_id='weddingos',role='CMO',enabled=True),c)
  a,ac=self.client('operator');d=self.call(a,'business');self.assertEqual([u['id'] for u in d['units']],['weddingos']);self.assertEqual(d['users'],[])
  with self.assertRaises(urllib.error.HTTPError) as e:self.create(a,ac,unit='liqmint_individual')
  self.assertEqual(e.exception.code,403)
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(a,'business/assign',dict(username='operator',unit_id='weddingos',role='CFO',enabled=True),ac)
  self.assertEqual(e.exception.code,403)
 def test_viewer_cannot_mutate(self):
  o,c=self.client('viewer')
  with self.assertRaises(urllib.error.HTTPError) as e:self.create(o,c)
  self.assertEqual(e.exception.code,403)
 def test_round_trip_and_stale_form(self):
  o,c=self.client();case=self.create(o,c);payload=dict(id=case['id'],version=1,status='complete',source='http:report',note='Verified buyer qualification and all relevant evidence.',attest=True)
  updated=self.call(o,'business/record',payload,c);self.assertEqual(updated['cursor'],1)
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(o,'business/record',payload,c)
  self.assertEqual(e.exception.code,400)
  data=self.call(o,'business');self.assertTrue(any(x['id']==case['id'] for x in data['cases']));self.assertFalse(data['external_execution'])
 def test_forged_scope_and_generic_record_bypass_rejected(self):
  o,c=self.client()
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(o,'business/create',{'unit_id':'weddingos','role':'founder','company_id':'vireoka'},c)
  self.assertEqual(e.exception.code,400)
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(o,'business_cases',{'product_id':4,'unit_id':'weddingos','steps':[]},c)
  self.assertEqual(e.exception.code,400)
 def test_logout_clears_access(self):
  o,c=self.client();self.call(o,'logout',{},c)
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(o,'business')
  self.assertEqual(e.exception.code,401)
