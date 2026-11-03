import json,unittest
from unittest.mock import patch,MagicMock
from growthpilot import bounded_kimi_bridge as b
from growthpilot.preload_kimi import preload
class PreloadTests(unittest.TestCase):
 def response(self,x):r=MagicMock();r.read.return_value=json.dumps(x).encode();r.__enter__.return_value=r;return r
 def test_pinned_load_only_uses_same_options_before_readiness(self):
  with patch.object(b,'MODEL_DIGEST','a'*64),patch.object(b,'MMAP','true'),patch.object(b,'model_ready',return_value=True),patch('urllib.request.urlopen',side_effect=[self.response({'models':[{'name':b.MODEL,'digest':'a'*64}]}),self.response({'model':b.MODEL,'done':True,'done_reason':'load'})]) as network:
   result=preload();payload=json.loads(network.call_args.args[0].data);self.assertEqual(payload['prompt'],'');self.assertTrue(payload['options']['use_mmap']);self.assertEqual(network.call_args.kwargs['timeout'],60);self.assertTrue(result['load_only'])
 def test_wrong_digest_never_loads_or_downloads(self):
  with patch.object(b,'MODEL_DIGEST','a'*64),patch('urllib.request.urlopen',return_value=self.response({'models':[{'name':b.MODEL,'digest':'b'*64}]})) as network:
   with self.assertRaises(ValueError):preload()
   self.assertEqual(network.call_count,1)
 def test_missing_pin_never_contacts_runtime(self):
  with patch.object(b,'MODEL_DIGEST',''),patch('urllib.request.urlopen')as network:
   with self.assertRaises(ValueError):preload()
   network.assert_not_called()

 def test_readiness_rejects_replaced_digest(self):
  with patch.object(b,'MODEL_DIGEST','a'*64),patch('urllib.request.urlopen',return_value=self.response({'models':[{'name':b.MODEL,'digest':'b'*64,'size_vram':0,'context_length':2048}]})):
   self.assertFalse(b.model_ready())
