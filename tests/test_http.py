import http.cookiejar,json,os,socket,subprocess,sys,tempfile,time,unittest,urllib.request,urllib.error
from pathlib import Path
from growthpilot.platform import Platform
from growthpilot.identity import Identity
class HttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();path=Path(cls.tmp.name)/'http.db';store=Platform(path);identity=Identity(store)
  identity.create('admin','Test-password-Long-Only','founder');identity.create('viewer','Test-password-Long-Only','viewer',[1]);identity.create('operator','Test-password-Long-Only','operator',[1])
  with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
  cls.url='http://127.0.0.1:'+str(port)
  cls.process=subprocess.Popen([sys.executable,'-m','growthpilot.server','--port',str(port)],env=dict(os.environ,GROWTHPILOT_DB=str(path)),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(100):
   try:urllib.request.urlopen(cls.url+'/health',timeout=1);break
   except OSError:time.sleep(.05)
 @classmethod
 def tearDownClass(cls):cls.process.terminate();cls.process.wait(timeout=10);cls.tmp.cleanup()
 def client(self,name='admin'):
  jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar));result=self.call(opener,'login',{'username':name,'password':'Test-password-Long-Only'});return opener,result['csrf']
 def call(self,opener,path,data=None,csrf=None):
  req=urllib.request.Request(self.url+'/api/'+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json',**({'X-CSRF-Token':csrf} if csrf else {})})
  return json.load(opener.open(req,timeout=15))
 def test_auth_required(self):
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(urllib.request.build_opener(),'state')
  self.assertEqual(e.exception.code,401)
 def test_csrf_required(self):
  opener,_=self.client()
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(opener,'plan',{'product_id':1})
  self.assertEqual(e.exception.code,403)
 def test_session_mock_workflow(self):
  o,c=self.client();a=self.call(o,'plan',{'product_id':1},c)['action'];self.call(o,'actions/'+a['id']+'/approve',{'payload_hash':a['payload_hash']},c);a=self.call(o,'actions/'+a['id']+'/execute',{},c);self.assertFalse(a['receipt']['external_delivery'])
 def test_viewer_cannot_write(self):
  o,c=self.client('viewer')
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(o,'plan',{'product_id':1},c)
  self.assertEqual(e.exception.code,403)
 def test_product_scope(self):
  o,c=self.client('operator');s=self.call(o,'state');self.assertEqual([p['id'] for p in s['products']],[1]);self.assertEqual(s['audit'],[])
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(o,'plan',{'product_id':2},c)
  self.assertEqual(e.exception.code,403)
 def test_operator_cannot_approve(self):
  a,c=self.client();action=self.call(a,'plan',{'product_id':1},c)['action'];o,c=self.client('operator')
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(o,'actions/'+action['id']+'/approve',{'payload_hash':action['payload_hash']},c)
  self.assertEqual(e.exception.code,403)
 def test_logout_invalidates(self):
  o,c=self.client();self.call(o,'logout',{},c)
  with self.assertRaises(urllib.error.HTTPError):self.call(o,'state')
 def test_static_and_headers(self):
  with urllib.request.urlopen(self.url+'/') as response:
   self.assertIn('frame-ancestors',response.headers['Content-Security-Policy']);self.assertIn(b'/console.js',response.read())
 def test_roadmap_admin_update(self):
  o,c=self.client();result=self.call(o,'roadmap',{'current_phase':'launch_learn'},c);self.assertEqual(result['current_phase'],'launch_learn')
 def test_roadmap_operator_denied(self):
  o,c=self.client('operator')
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(o,'roadmap',{'current_phase':'foundation'},c)
  self.assertEqual(e.exception.code,403)
 def test_manager_requires_admin(self):
  o,c=self.client('operator')
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(o,'manager/prepare',{},c)
  self.assertEqual(e.exception.code,403)
 def test_manager_preparation_and_scope(self):
  o,c=self.client();self.call(o,'manager/prepare',{},c);s=self.call(o,'state');self.assertEqual(len(s['launch_desk']['growthplans']),17)
  operator,_=self.client('operator');self.assertEqual(self.call(operator,'state')['launch_desk'],{})
 def test_strategy_admin_only_and_no_finance_leak(self):
  admin,csrf=self.client();data=self.call(admin,'strategy');self.assertEqual(len(data['strategies']['products']),17)
  self.assertFalse(data['execution_enabled'])
  for role in ('viewer','operator'):
   user,c=self.client(role)
   with self.assertRaises(urllib.error.HTTPError) as e:self.call(user,'strategy')
   self.assertEqual(e.exception.code,403)
   with self.assertRaises(urllib.error.HTTPError) as e:self.call(user,'strategy/run',{},c)
   self.assertEqual(e.exception.code,403)
   self.assertNotIn('economic_runs',self.call(user,'state'))
 def test_strategy_run_requires_csrf_and_preserves_no_execution(self):
  user,c=self.client()
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(user,'strategy/run',{})
  self.assertEqual(e.exception.code,403)
  actual=self.call(user,'strategy/run',{'mode':'actual_only'},c)
  self.assertEqual(actual['mode'],'actual_only');self.assertEqual(actual['scenarios'],[])
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(user,'strategy/run',{'mode':'actual_only','inputs':{'baseline_units':100}},c)
  self.assertEqual(e.exception.code,400)
  r=self.call(user,'strategy/run',{'product_id':3},c)
  self.assertEqual(r['scenarios'][0]['status'],'illustrative_assumptions_only')
  self.assertFalse(r['execution_enabled'])
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(user,'strategy/run',{'product_id':3,'execute':True},c)
  self.assertEqual(e.exception.code,400)
 def test_finance_import_requires_admin_and_source(self):
  user,c=self.client('operator')
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(user,'strategy/financials',{},c)
  self.assertEqual(e.exception.code,403)
  user,c=self.client()
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(user,'strategy/financials',{'product_id':4},c)
  self.assertEqual(e.exception.code,400)
if __name__=='__main__':unittest.main()
