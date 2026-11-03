import json,os,unittest
from unittest.mock import patch,MagicMock
from growthpilot.providers import draft
from growthpilot.core import Invalid

class SmallLocalModels(unittest.TestCase):
 def call(self,model,raw,product=None):
  if 'response' in raw:raw={**raw,'message':{'content':raw['response']}}
  response=MagicMock();response.__enter__.return_value=response;response.read.return_value=json.dumps(raw).encode()
  ready=MagicMock();ready.__enter__.return_value=ready;ready.read.return_value=json.dumps({'models':[{'name':model,'context_length':2048}]}).encode()
  with patch.dict(os.environ,{'GROWTHPILOT_OLLAMA_URL':'http://private-local:11434','GROWTHPILOT_OLLAMA_MODEL':model}),patch('urllib.request.urlopen',side_effect=[ready,response])as request:
   result=draft(product or {'name':'Synthetic community','audience':'community owners'},[],'email')
   return result,request
 def test_both_authorized_models_only_choose_prepared_copy(self):
  for model in ['ministral-3:3b','granite3.3:2b']:
   with self.subTest(model=model):
    result,request=self.call(model,{'model':model,'done':True,'done_reason':'stop','response':'{"choice":1}'})
    self.assertEqual(result['mode'],'bounded_variant_selection');self.assertEqual(result['claims'],[])
    self.assertIn('Synthetic community',result['content']);self.assertEqual(request.call_args.kwargs['timeout'],20)
    self.assertTrue(request.call_args.args[0].full_url.endswith('/api/chat'))
    self.assertEqual(json.loads(request.call_args.args[0].data)['options']['num_gpu'],0)
 def test_incomplete_response_never_selects(self):
  for patch_value in [{'done':False},{'done_reason':'length'},{'model':'other'},{'response':'{"choice":3}'},{'response':'{"choice":true}'}]:
   with self.subTest(patch=patch_value),self.assertRaises(Invalid):
    self.call('ministral-3:3b',{'model':'ministral-3:3b','done':True,'done_reason':'stop','response':'{"choice":1}',**patch_value})
 def test_free_form_claims_remain_gated(self):
  with self.assertRaises(Invalid):self.call('ministral-3:3b',{},product={'name':'test','approved_claims':['A feature']})
 def test_cloud_and_unreviewed_models_rejected(self):
  for name in ['ministral-3:8b-cloud','unreviewed:latest']:
   with self.subTest(model=name),self.assertRaises(Invalid):self.call(name,{})

 def test_cold_model_fails_without_generation(self):
  response=MagicMock();response.__enter__.return_value=response;response.read.return_value=b'{"models":[]}'
  with patch.dict(os.environ,{'GROWTHPILOT_OLLAMA_URL':'http://private-local:11434','GROWTHPILOT_OLLAMA_MODEL':'ministral-3:3b'}),patch('urllib.request.urlopen',return_value=response)as network:
   with self.assertRaises(Invalid):draft({'name':'Synthetic'},[],'email')
   self.assertEqual(network.call_count,1)
