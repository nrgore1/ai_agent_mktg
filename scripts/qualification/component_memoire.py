import os,sys,types,unittest,json
from unittest.mock import patch,MagicMock
os.environ.update(DJANGO_SETTINGS_MODULE='isolated_settings',DJANGO_SECRET_KEY='isolated-test-only',DATABASE_URL='sqlite:////tmp/unused.sqlite3',STRIPE_SECRET_KEY='',DEBUG='true')
from django.conf import settings
settings.configure(SECRET_KEY='isolated-test-only',USE_TZ=True,INSTALLED_APPS=['django.contrib.auth','django.contrib.contenttypes','memoir_api.commerce'],DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},REST_FRAMEWORK={})
import django;django.setup()
from memoir_api.commerce import plans as p,usage as u,rbac as r

class Checks(unittest.TestCase):
 def charge(self,plan,used,n):
  org=MagicMock(plan=plan,illustrations_used=used,illustrations_month=u._month());user=types.SimpleNamespace(is_authenticated=True)
  with patch.object(u,'get_or_create_org',return_value=(org,None)),patch.object(u,'illustration_usage',return_value={}):return u.charge_illustrations(user,n)
 def test_free_catalog(self):self.assertEqual(p.entitlements_for('free')['max_books'],1);self.assertFalse(p.entitlements_for('free')['hd_export'])
 def test_unknown_plan_is_free(self):self.assertEqual(p.entitlements_for('forged'),p.entitlements_for('free'))
 def test_paid_hd_export(self):self.assertTrue(p.entitlements_for('personal')['hd_export'])
 def test_personal_not_white_label(self):self.assertFalse(p.entitlements_for('personal')['white_label'])
 def test_family_not_studio(self):self.assertFalse(p.entitlements_for('family')['white_label']);self.assertTrue(p.entitlements_for('studio')['white_label'])
 def test_personal_last_credit_allowed(self):self.assertTrue(self.charge('personal',19,1)[0])
 def test_personal_over_quota_denied(self):self.assertFalse(self.charge('personal',20,1)[0])
 def test_family_over_quota_denied(self):self.assertFalse(self.charge('family',60,1)[0])
 def test_studio_over_quota_denied(self):self.assertFalse(self.charge('studio',200,1)[0])
 def test_free_zero_allowance_denied(self):self.assertFalse(self.charge('free',0,1)[0])
 def test_negative_reservation_denied(self):
  try:result=self.charge('personal',20,-1)
  except (ValueError,TypeError):return
  self.assertFalse(result[0])
 def test_registered_free_premium_gate(self):
  with patch.object(r,'current_plan',return_value='free'):
   response=r.entitlement_gate(types.SimpleNamespace(user=types.SimpleNamespace(is_authenticated=True)),'hd_export');self.assertEqual(response.status_code,402)
 def test_registered_personal_premium_gate(self):
  with patch.object(r,'current_plan',return_value='personal'):
   self.assertIsNone(r.entitlement_gate(types.SimpleNamespace(user=types.SimpleNamespace(is_authenticated=True)),'hd_export'))
 def test_print_quote_extra_pages(self):self.assertEqual(p.print_quote(25,'essential',1)['total'],29.8)
 def test_print_quote_bulk_threshold(self):self.assertEqual(p.print_quote(24,'essential',10)['total'],246.5)

suite=unittest.defaultTestLoader.loadTestsFromTestCase(Checks);result=unittest.TextTestRunner(verbosity=2).run(suite)
print('AGENTVIRE_RESULT '+json.dumps({'tests':result.testsRun,'failed':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'failed_tests':[str(t)for t,_ in result.failures],'error_tests':[str(t)for t,_ in result.errors]}))
