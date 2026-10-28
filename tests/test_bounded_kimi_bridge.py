import json,os,threading,time,unittest,urllib.request,urllib.error
from unittest.mock import patch,MagicMock
from http.server import ThreadingHTTPServer
from growthpilot import bounded_kimi_bridge as b
class PayloadTests(unittest.TestCase):
 def valid(self):return {"model":b.MODEL,"stream":False,"prompt":"Synthetic","options":{"num_predict":64,"num_gpu":99,"num_ctx":99999}}
 def test_pins_cpu_context_and_threads(self):
  p=b.bounded_payload(self.valid());self.assertEqual(p['options']['num_gpu'],0);self.assertEqual(p['options']['num_ctx'],2048);self.assertEqual(p['options']['num_thread'],4);self.assertEqual(p['keep_alive'],-1);self.assertTrue(p['raw']);self.assertTrue(p['prompt'].endswith('<|im_assistant|>assistant<|im_middle|>'));self.assertFalse(p['prompt'].endswith('<|im_end|>'))
 def test_rejects_other_model(self):
  p=self.valid();p['model']='other:cloud'
  with self.assertRaises(ValueError):b.bounded_payload(p)
 def test_rejects_unbounded_tokens(self):
  p=self.valid();p['options']['num_predict']=129
  with self.assertRaises(ValueError):b.bounded_payload(p)
 def test_rejects_long_prompt(self):
  p=self.valid();p['prompt']='x'*16001
  with self.assertRaises(ValueError):b.bounded_payload(p)
 def test_rejects_oversize_schema(self):
  p=self.valid();p['format']={'description':'x'*4097}
  with self.assertRaises(ValueError):b.bounded_payload(p)
class AdmissionTests(unittest.TestCase):
 def setUp(self):
  self.server=ThreadingHTTPServer(('127.0.0.1',0),b.Bridge);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.base='http://127.0.0.1:'+str(self.server.server_port)
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join(2)
 def post(self):
  q=urllib.request.Request(self.base+'/api/generate',data=json.dumps({'model':b.MODEL,'stream':False,'prompt':'Synthetic'}).encode(),headers={'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(q,timeout=2)as r:return r.status,json.load(r)
  except urllib.error.HTTPError as e:return e.code,json.load(e)
 def test_busy_is_fast_and_health_is_not_queued(self):
  self.assertTrue(b.SLOT.acquire(False))
  try:
   with patch.object(b,'model_ready',return_value=True),patch('urllib.request.urlopen',wraps=urllib.request.urlopen):
    t=time.monotonic();s,d=self.post();self.assertEqual((s,d['error']),(503,'local_model_busy'));self.assertLess(time.monotonic()-t,1)
    with urllib.request.urlopen(self.base+'/readyz',timeout=1)as r:self.assertEqual(r.status,200)
  finally:b.SLOT.release()
 def test_cold_does_not_dispatch_inference(self):
  with patch.object(b,'model_ready',return_value=False):
   s,d=self.post();self.assertEqual((s,d['error']),(503,'local_model_cold_operator_preload_required'))
 def test_transport_deadline_is_fixed(self):
  # Patch only bridge's upstream operation while preserving the HTTP test client.
  original=b.UPSTREAM;b.UPSTREAM='http://unused-private-runtime'
  try:
   with patch.object(b,'model_ready',return_value=True),patch.object(b.urllib.request,'urlopen',side_effect=TimeoutError):
    # Invoke handler logic through a real server using a separate stdlib client.
    import http.client
    c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2);c.request('POST','/api/generate',json.dumps({'model':b.MODEL,'stream':False,'prompt':'Synthetic'}),{'Content-Type':'application/json'});r=c.getresponse();d=json.loads(r.read());self.assertEqual(r.status,503);self.assertEqual(d['error'],'local_inference_deadline_or_transport');c.close()
  finally:b.UPSTREAM=original
