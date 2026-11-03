import json,unittest,time,copy,http.client
from unittest.mock import patch
from growthpilot import bounded_kimi_bridge as b
from tests import test_bounded_kimi_bridge as helpers

class CacheTests(unittest.TestCase):
 def setUp(self):b.CACHE.clear();self.enabled=patch.object(b,'CACHE_ENABLED',True);self.enabled.start()
 def tearDown(self):self.enabled.stop();b.CACHE.clear()
 def payload(self,text='Synthetic'):
  return b.bounded_payload({'model':b.MODEL,'stream':False,'prompt':text,'format':b.rubric_schema(2),'options':{'seed':42,'temperature':0,'num_predict':128}})
 def answer(self):return {'model':b.MODEL,'done':True,'done_reason':'stop','response':json.dumps({k:{'rating':v[3],'span':1}for k,v in b.RATINGS.items()}),'eval_count':70,'prompt_eval_count':300}
 def test_exact_key_cache_hit_has_zero_new_usage(self):
  p=self.payload();key=b.cache_key(p);b.remember_result(key,self.answer(),p);r=b.cached_result(key);self.assertTrue(r['cache_hit']);self.assertEqual(r['eval_count'],0);self.assertEqual(r['prompt_eval_count'],0);self.assertNotIn('Synthetic',repr(b.CACHE));self.assertNotEqual(key,b.cache_key(self.payload('Different')))
 def test_truncated_invalid_and_other_model_are_never_cached(self):
  p=self.payload();key=b.cache_key(p)
  for changes in [{'done_reason':'length'},{'done':'true'},{'model':'other'},{'response':'{}'},{'response':self.answer()['response']+' trailing'},{'response':self.answer()['response'].replace('"span": 1','"span": true',1)},{'response':self.answer()['response'].replace('"span": 1','"span": 0',1)}]:
   data=self.answer();data.update(changes);b.remember_result(key,data,p);self.assertIsNone(b.cached_result(key))
 def test_expiration_limit_and_nonrubric_exclusion(self):
  p=self.payload();key=b.cache_key(p);b.remember_result(key,self.answer(),p)
  with patch.object(b.time,'monotonic',return_value=time.monotonic()+121):self.assertIsNone(b.cached_result(key))
  for i in range(12):
   p=self.payload(str(i));b.remember_result(b.cache_key(p),self.answer(),p)
  self.assertEqual(len(b.CACHE),8);p.pop('format');self.assertIsNone(b.cache_key(p))
 def test_pins_load_options_and_ignores_caller_changes(self):
  with patch.object(b,'MMAP','true'):
   p=b.bounded_payload({'model':b.MODEL,'stream':False,'prompt':'Synthetic','options':{'use_mmap':False,'num_batch':1}});self.assertTrue(p['options']['use_mmap']);self.assertEqual(p['options']['num_batch'],512)

class CachedAdmissionTests(unittest.TestCase):
 def setUp(self):
  self.helper=helpers.AdmissionTests();self.helper.setUp();self.server=self.helper.server
 def tearDown(self):self.helper.tearDown()
 def test_cached_valid_response_does_not_queue_behind_busy_inference(self):
  with patch.object(b,'CACHE_ENABLED',True),patch.object(b,'model_ready',return_value=True):
   b.CACHE.clear();raw={'model':b.MODEL,'stream':False,'prompt':'Synthetic','format':b.rubric_schema(2),'options':{'seed':42,'temperature':0}}
   p=b.bounded_payload(raw);data=CacheTests().answer();b.remember_result(b.cache_key(p),data,p);b.SLOT.acquire()
   try:
    c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2);c.request('POST','/api/generate',json.dumps(raw),{'Content-Type':'application/json'});r=c.getresponse();v=json.loads(r.read());self.assertEqual(r.status,200);self.assertTrue(v['cache_hit']);c.close()
   finally:b.SLOT.release();b.CACHE.clear()

 def test_upstream_http_failure_has_safe_distinct_code(self):
  import urllib.error
  with patch.object(b,'model_ready',return_value=True),patch.object(b.urllib.request,'urlopen',side_effect=urllib.error.HTTPError('http://private',503,'Sensitive upstream detail',None,None)):
   c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2);c.request('POST','/api/generate',json.dumps({'model':b.MODEL,'stream':False,'prompt':'Synthetic'}),{'Content-Type':'application/json'});r=c.getresponse();data=json.loads(r.read());c.close();self.assertEqual(r.status,503);self.assertEqual(data,{'error':'local_upstream_http','upstream_status':503})
