import json,os,tempfile,unittest,datetime as dt
from pathlib import Path
from unittest.mock import patch,MagicMock
from growthpilot.platform import Platform
from growthpilot.core import Invalid,digest
from growthpilot import postmark
class ManagerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Platform(self.tmp.name+'/m.db');self.m=self.s.manager();self.m.prepare()
 def tearDown(self):self.tmp.cleanup()
 def ready(self):
  self.s.update('products',1,{'website':'https://example.com','readiness':'verified'})
  a=next(a for a in self.m.summary()['actions'] if a['product_id']==1 and a['payload']['channel']=='producthunt.com')
  return self.s.transition(a['id'],'revise',{'account':'Founder test account','content':'Reviewed evaluation invitation: https://example.com','attestations':{'product_facts':True,'channel_rules':True,'destination':True,'founder_written':False}})
 def test_portfolio_coverage(self):
  d=self.m.summary();self.assertEqual(len(d['growthplans']),17);self.assertEqual(len(d['workitems']),102);self.assertEqual(len(d['actions']),38)
 def test_idempotent_preparation(self):
  self.m.prepare();self.assertEqual(len(self.m.summary()['actions']),38);self.assertEqual(len(self.s.snapshot()['campaigns']),17)
 def test_sender_routing(self):
  for a in self.m.summary()['actions']:self.assertEqual(a['payload']['sender'],'naren@vireoka.com' if a['product_id'] in (1,2) else 'naren@atmakosh.com')
 def test_no_fake_results(self):
  s=self.s.snapshot();self.assertEqual(s['events'],[]);self.assertEqual(s['leads'],[]);self.assertEqual(s['metrics']['actual_conversions'],0);self.assertTrue(all(x['status']!='completed' for x in s['launch_desk']['workitems']))
 def test_missing_facts_blocks_approval(self):
  a=self.m.summary()['actions'][0]
  with self.assertRaises(Invalid):self.s.transition(a['id'],'approve',{'payload_hash':a['payload_hash']})
 def test_manual_export_requires_exact_approval(self):
  a=self.ready()
  with self.assertRaises(Invalid):self.s.transition(a['id'],'export',{})
  self.s.transition(a['id'],'approve',{'payload_hash':a['payload_hash']});result=self.s.transition(a['id'],'export',{});self.assertEqual(result['payload_hash'],a['payload_hash']);self.assertEqual(self.s.snapshot()['events'],[])
 def test_edit_invalidates(self):
  a=self.ready();self.s.transition(a['id'],'approve',{'payload_hash':a['payload_hash']});a=self.s.transition(a['id'],'revise',{'content':'Revised copy'})
  self.assertIsNone(a['approval']);self.assertFalse(a['payload']['attestations']['product_facts'])
 def test_receipt_wrong_destination_blocked(self):
  a=self.ready();self.s.transition(a['id'],'approve',{'payload_hash':a['payload_hash']})
  with self.assertRaises(Invalid):self.s.transition(a['id'],'record_submission',{'receipt_url':'https://example.org/post','note':'posted'})
 def test_manual_submission_label(self):
  a=self.ready();self.s.transition(a['id'],'approve',{'payload_hash':a['payload_hash']});a=self.s.transition(a['id'],'record_submission',{'receipt_url':'https://www.producthunt.com/posts/test','note':'Founder supplied proof'})
  self.assertEqual(a['receipt']['verification'],'founder_reported');self.assertEqual(self.s.snapshot()['events'],[])
 def test_hn_requires_founder_text(self):
  a=next(a for a in self.m.summary()['actions'] if a['payload']['channel']=='news.ycombinator.com')
  self.s.update('products',a['product_id'],{'website':'https://example.org','readiness':'verified'});a=self.s.transition(a['id'],'revise',{'account':'Founder','attestations':{'product_facts':True,'channel_rules':True,'destination':True,'founder_written':True}})
  with self.assertRaises(Invalid):self.s.transition(a['id'],'approve',{'payload_hash':a['payload_hash']})
 def test_actual_feedback_required(self):
  with self.assertRaises(Invalid):self.m.activity_record('feedback',{'product_id':1},'founder')
  self.m.activity_record('feedback',{'product_id':1,'notes':'Actual interview notes','source':'Customer interview reference'},'founder');review=self.m.review();self.assertEqual(next(p for p in review['products'] if p['product_id']==1)['feedback_count'],1)
 def test_completed_demo_requires_evidence(self):
  with self.assertRaises(Invalid):self.m.activity_record('demos',{'product_id':1,'status':'completed'},'founder')
 def test_demo_lead_isolation(self):
  lead=self.s.create_record('leads',{'product_id':2,'name':'Contact','pipeline':'institutional'})
  with self.assertRaises(Invalid):self.m.activity_record('demos',{'product_id':1,'lead_id':lead['id'],'status':'proposed'},'founder')
 def test_no_data_recommendation(self):
  review=self.m.review();self.assertTrue(all(p['status']=='needs_data' for p in review['products']));self.assertEqual(review['external_changes'],0)
 def test_review_uses_actual_events_only(self):
  self.s.create_record('events',{'product_id':1,'type':'landing_view','source':'simulation','count':100});review=self.m.review();self.assertEqual(next(p for p in review['products'] if p['product_id']==1)['funnel'],{})
 def test_outreach_requires_consent(self):
  lead=self.s.create_record('leads',{'product_id':1,'name':'Contact','email':'test@example.com','pipeline':'customer'})
  with self.assertRaises(Invalid):self.m.outreach(lead['id'],'founder')
 def test_outreach_exact_recipient_and_unsubscribe(self):
  lead=self.s.create_record('leads',{'product_id':1,'name':'Contact','email':'test@example.com','pipeline':'customer','consent':'opt_in','source':'Requested evaluation on website'});a=self.m.outreach(lead['id'],'founder');self.assertEqual(a['payload']['recipient'],'test@example.com');self.assertIn('{{{ pm:unsubscribe }}}',a['payload']['content']);self.assertIsNone(a['approval'])

class PostmarkTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();path=Path(self.tmp.name)/'accounts.json';path.write_text(json.dumps({'liqmint_individual':{'sender':'naren@vireoka.com','token':'synthetic-test-token','server_id':123,'stream':'broadcast','status':'configured'}}));self.env=patch.dict(os.environ,{'GROWTHPILOT_POSTMARK_FILE':str(path)});self.env.start();self.payload={'product_id':1,'server_id':123,'message_stream':'broadcast','account':'liqmint_individual','sender':'naren@vireoka.com','recipient':'optedin@example.com','title':'Approved title','content':'Approved content\n{{{ pm:unsubscribe }}}'}
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def test_account_metadata_has_no_token(self):self.assertNotIn('token',postmark.public_accounts()['liqmint_individual'])
 def test_product_account_mismatch(self):
  with self.assertRaises(Invalid):postmark.envelope(dict(self.payload,sender='naren@atmakosh.com'),'a')
 def test_multiple_recipients_blocked(self):
  with self.assertRaises(Invalid):postmark.envelope(dict(self.payload,recipient='a@example.com,b@example.com'),'a')
 def test_unsubscribe_in_approved_payload(self):
  with self.assertRaises(Invalid):postmark.envelope(dict(self.payload,content='No opt-out'),'a')
 def test_stream_and_server_are_bound(self):
  with self.assertRaises(Invalid):postmark.envelope(dict(self.payload,server_id=456),'a')
  with self.assertRaises(Invalid):postmark.envelope(dict(self.payload,message_stream='outbound'),'a')
 def test_send_requires_enablement(self):
  with patch.dict(os.environ,{'GROWTHPILOT_ENABLE_POSTMARK':'false'}):
   with self.assertRaises(Invalid):postmark.send(self.payload,'a')
 def test_no_delivery_test_mode(self):
  response=MagicMock();response.__enter__.return_value=response;response.read.return_value=b'{"ErrorCode":0,"MessageID":"synthetic-test-id"}'
  with patch('urllib.request.urlopen',return_value=response) as network:receipt=postmark.send(self.payload,'a',test=True)
  self.assertFalse(receipt['external_delivery']);request=network.call_args.args[0];self.assertEqual(request.get_header('X-postmark-server-token'),'POSTMARK_API_TEST');self.assertEqual(json.loads(request.data)['MessageStream'],'broadcast')

class LocalDraftTests(unittest.TestCase):
 def test_compact_local_context(self):
  from growthpilot.providers import draft
  response=MagicMock();response.__enter__.return_value=response;response.read.return_value=json.dumps({'response':json.dumps({'content':'A short evaluation invitation.','claims':[],'uncertainties':['Availability needs review']})}).encode()
  with patch.dict(os.environ,{'GROWTHPILOT_OLLAMA_URL':'http://127.0.0.1:11434','GROWTHPILOT_OLLAMA_MODEL':'local-kimi-test'}),patch('urllib.request.urlopen',return_value=response) as network:
   result=draft({'name':'Test','approved_claims':['A verified claim'],'unrelated_private_field':'must-not-be-sent'},[{'source':'https://example.com','excerpt':'x'*20000}],'producthunt.com')
  payload=json.loads(network.call_args.args[0].data);self.assertLess(len(payload['prompt']),5000);self.assertNotIn('must-not-be-sent',payload['prompt']);self.assertEqual(payload['options']['num_ctx'],2048);self.assertEqual(result['claims'],[])

 def test_bounded_selection_uses_prepared_copy(self):
  from growthpilot.providers import draft
  response=MagicMock();response.__enter__.return_value=response;response.read.return_value=json.dumps({'response':json.dumps({'choice':1,'content':'Invented guarantee'})}).encode()
  with patch.dict(os.environ,{'GROWTHPILOT_OLLAMA_URL':'http://127.0.0.1:11434','GROWTHPILOT_OLLAMA_MODEL':'local-kimi-test'}),patch('urllib.request.urlopen',return_value=response):result=draft({'name':'Test','audience':'Professionals'},[],'producthunt.com')
  self.assertEqual(result['mode'],'bounded_variant_selection');self.assertNotIn('Invented guarantee',result['content']);self.assertEqual(result['claims'],[])
 def test_invalid_variant_preserves_draft(self):
  from growthpilot.providers import draft
  response=MagicMock();response.__enter__.return_value=response;response.read.return_value=json.dumps({'response':json.dumps({'choice':3})}).encode()
  with patch.dict(os.environ,{'GROWTHPILOT_OLLAMA_URL':'http://127.0.0.1:11434','GROWTHPILOT_OLLAMA_MODEL':'local-kimi-test'}),patch('urllib.request.urlopen',return_value=response):
   with self.assertRaises(Invalid):draft({'name':'Test'},[],'producthunt.com')
 def test_instruction_echo_is_rejected(self):
  from growthpilot.providers import draft
  response=MagicMock();response.__enter__.return_value=response;response.read.return_value=json.dumps({'response':json.dumps({'content':'Return valid JSON with content and claims.','claims':[],'uncertainties':[]})}).encode()
  with patch.dict(os.environ,{'GROWTHPILOT_OLLAMA_URL':'http://127.0.0.1:11434','GROWTHPILOT_OLLAMA_MODEL':'local-kimi-test'}),patch('urllib.request.urlopen',return_value=response):
   with self.assertRaises(Invalid):draft({'name':'Test','approved_claims':['Verified claim']},[],'producthunt.com')
 def test_incomplete_output_is_rejected(self):
  from growthpilot.providers import draft
  response=MagicMock();response.__enter__.return_value=response;response.read.return_value=b'{"response":"{ incomplete"}'
  with patch.dict(os.environ,{'GROWTHPILOT_OLLAMA_URL':'http://127.0.0.1:11434','GROWTHPILOT_OLLAMA_MODEL':'local-kimi-test'}),patch('urllib.request.urlopen',return_value=response):
   with self.assertRaises(Invalid):draft({'name':'Test','approved_claims':['Verified claim']},[],'producthunt.com')

if __name__=='__main__':unittest.main()
