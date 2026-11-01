import os,sys,types,unittest,json,time
from unittest.mock import patch,MagicMock
os.environ.update(DEBUG='true',DJANGO_SECRET_KEY='isolated-test-only',STRIPE_SECRET_KEY='',STRIPE_WEBHOOK_SECRET='whsec_isolated_test_only',DATABASE_URL='sqlite:////tmp/unused.sqlite3')
import core.settings as original
cfg=types.ModuleType('isolated_settings')
for k in dir(original):
 if k.isupper():setattr(cfg,k,getattr(original,k))
cfg.DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}
cfg.EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
cfg.CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache'}}
cfg.CHANNEL_LAYERS={'default':{'BACKEND':'channels.layers.InMemoryChannelLayer'}}
sys.modules['isolated_settings']=cfg;os.environ['DJANGO_SETTINGS_MODULE']='isolated_settings'
import django;django.setup()
from api import entitlements as e,stripe_billing as b,views_billing as v
from rest_framework.test import APIRequestFactory

class Checks(unittest.TestCase):
 def feature(self,tier,status,key):
  with patch.object(e,'release_enabled',return_value=True),patch.object(e,'_org_killed',return_value=False),patch.object(e.Subscription.objects,'filter')as q:
   q.return_value.first.return_value=types.SimpleNamespace(tier=tier,status=status)
   return e.resolve_feature(None,object(),key)
 def test_free_blocks_growth(self):self.assertEqual(self.feature('free','active','ai_coach'),'locked')
 def test_growth_blocks_enterprise(self):self.assertEqual(self.feature('growth','active','team_seats'),'locked')
 def test_growth_gets_released_growth(self):self.assertEqual(self.feature('growth','active','ai_coach'),'on')
 def test_free_practice_available(self):self.assertEqual(self.feature('free','active','practice_studio'),'on')
 def test_suspended_paid_access_denied(self):self.assertNotEqual(self.feature('growth','suspended','ai_coach'),'on')
 def test_unpaid_paid_access_denied(self):self.assertNotEqual(self.feature('enterprise','unpaid','team_seats'),'on')
 def test_unknown_feature_closed(self):self.assertEqual(e.resolve_feature(None,None,'nonexistent'),'off')
 def test_unreleased_paid_feature_closed(self):
  with patch.object(e,'release_enabled',return_value=False):self.assertEqual(e.resolve_feature(None,None,'ai_coach'),'off')
 def test_tenant_kill_switch_closed(self):
  with patch.object(e,'release_enabled',return_value=True),patch.object(e,'_org_killed',return_value=True):self.assertEqual(e.resolve_feature(None,object(),'ai_coach'),'off')
 def test_valid_signature(self):
  p=b'{"id":"evt_synthetic"}';self.assertEqual(b.verify_webhook(p,b.sign_payload(p))['id'],'evt_synthetic')
 def test_tampered_body_denied(self):
  p=b'{"id":"evt_synthetic"}';self.assertIsNone(b.verify_webhook(p+b' ',b.sign_payload(p)))
 def test_expired_signature_denied(self):
  p=b'{}';self.assertIsNone(b.verify_webhook(p,b.sign_payload(p,int(time.time())-301)))
 def test_missing_signature_denied(self):self.assertIsNone(b.verify_webhook(b'{}',''))
 def test_signed_invalid_json_denied(self):
  p=b'not-json';self.assertIsNone(b.verify_webhook(p,b.sign_payload(p)))
 def test_unpaid_checkout_does_not_activate(self):
  event={'id':'evt_unpaid_synthetic','type':'checkout.session.completed','data':{'object':{'payment_status':'unpaid','metadata':{'org_id':'00000000-0000-0000-0000-000000000001','tier':'growth'}}}}
  req=APIRequestFactory().post('/billing/webhook',{},format='json')
  with patch.object(b,'verify_webhook',return_value=event),patch.object(v.Org.objects,'filter')as orgs,patch.object(v,'_apply_paid_subscription')as activate,patch.object(v.SecurityAuditLog.objects,'create'):
   orgs.return_value.first.return_value=MagicMock()
   response=v.stripe_webhook(req)
   self.assertEqual(response.status_code,200);activate.assert_not_called()

suite=unittest.defaultTestLoader.loadTestsFromTestCase(Checks);result=unittest.TextTestRunner(verbosity=2).run(suite)
print('AGENTVIRE_RESULT '+json.dumps({'tests':result.testsRun,'failed':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'failed_tests':[str(t)for t,_ in result.failures],'error_tests':[str(t)for t,_ in result.errors]}))
