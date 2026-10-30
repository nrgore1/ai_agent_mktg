import datetime as dt
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from growthpilot.core import Store, Invalid
from growthpilot.marketing_consent import MarketingConsent, BRANDS, VERSION, brand_for_host
from growthpilot.marketing_page import page

class ConsentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name+'/test.db');self.sent=[]
        self.time=dt.datetime(2026,10,30,tzinfo=dt.timezone.utc)
        self.service=MarketingConsent(self.store,'q'*64,self.mailer,lambda:self.time)
    def mailer(self,record,token,manage):
        self.sent.append((dict(record),token,manage));return {'provider_id':'qa'}
    def request(self,brand='weddingos',email='person@customer.test',**extra):
        return self.service.request(brand,dict(email=email,consent=True,notice_version=VERSION,**extra))
    def rows(self,kind):
        with self.store.db() as db:return self.store.rows(db,kind)
    def test_requires_explicit_current_choice(self):
        for change in ({'consent':False},{'consent':'true'},{'notice_version':'old'}):
            with self.assertRaises(Invalid):self.service.request('weddingos',dict(email='a@customer.test',consent=True,notice_version=VERSION,**{} )|change)
        self.assertEqual(self.rows('marketing_subscriptions'),[])
    def test_pending_is_not_a_lead(self):
        self.request();self.assertFalse(self.rows('leads'))
        self.assertEqual(self.rows('marketing_subscriptions')[0]['status'],'pending')
    def test_confirm_withdraw_and_no_cross_product(self):
        self.request();record,token,_=self.sent[0]
        with self.assertRaises(Invalid):self.service.confirm('memoire',token)
        result=self.service.confirm('weddingos',token);self.assertTrue(result['confirmed'])
        with self.assertRaises(Invalid):self.service.confirm('weddingos',token)
        lead=self.rows('leads')[0];payload={'product_id':4,'marketing_brand':'weddingos'}
        with self.store.db() as db:
            self.service.validate_lead(db,lead,payload)
            with self.assertRaises(Invalid):self.service.validate_lead(db,lead,dict(payload,marketing_brand='jodiusa'))
        stop=self.service.withdrawal_token(record)
        with self.assertRaises(Invalid):self.service.withdraw('jodiusa',stop)
        self.service.withdraw('weddingos',stop);self.service.withdraw('weddingos',stop)
        with self.store.db() as db:
            with self.assertRaises(Invalid):self.service.validate_lead(db,lead,payload)
        self.assertEqual(self.rows('leads')[0]['consent'],'opt_out')
    def test_expired_confirmation(self):
        self.request();self.time+=dt.timedelta(hours=25)
        with self.assertRaises(Invalid):self.service.confirm('weddingos',self.sent[0][1])
    def test_resend_rotates_token(self):
        self.request();first=self.sent[0][1];self.time+=dt.timedelta(minutes=16);self.request()
        with self.assertRaises(Invalid):self.service.confirm('weddingos',first)
        self.service.confirm('weddingos',self.sent[-1][1])
    def test_rate_limit_and_honeypot(self):
        self.request();self.request();self.assertEqual(len(self.sent),1)
        self.request(email='bot@customer.test',company='spam');self.assertEqual(len(self.sent),1)
    def test_synthetic_never_lead_or_eligible(self):
        self.request(email='qa@example.com');self.service.confirm('weddingos',self.sent[0][1])
        self.assertEqual(self.rows('leads'),[]);self.assertEqual(self.service.summary()['brands'][0]['confirmed'],0)
    def test_manage_unknown_is_generic_and_does_not_create(self):
        response=self.service.request('jodiusa',{'email':'unknown@customer.test'},manage=True)
        self.assertTrue(response['accepted']);self.assertEqual(self.rows('marketing_subscriptions'),[]);self.assertEqual(self.sent,[])
    def test_manage_does_not_resubscribe(self):
        self.request();record,token,_=self.sent[0];self.service.confirm('weddingos',token)
        self.service.withdraw('weddingos',self.service.withdrawal_token(record));self.time+=dt.timedelta(minutes=16)
        self.service.request('weddingos',{'email':record['email']},manage=True)
        self.assertTrue(self.sent[-1][2]);self.assertEqual(self.rows('marketing_subscriptions')[0]['status'],'withdrawn')
    def test_mail_failure_remains_pending(self):
        self.service.mailer=lambda *args:(_ for _ in ()).throw(RuntimeError('offline'))
        self.request();row=self.rows('marketing_subscriptions')[0]
        self.assertEqual(row['status'],'pending');self.assertEqual(row['delivery_status'],'not_confirmed')
    def test_no_token_or_hash_in_private_summary(self):
        self.request();row=self.service.summary()['records'][0]
        self.assertNotIn('confirm_hash',row);self.assertNotIn('provider_id',row)
    def test_host_allowlist_and_unchecked_form(self):
        for brand,b in BRANDS.items():
            self.assertEqual(brand_for_host(b['host']),brand)
            html=page(brand).decode();self.assertIn('type="checkbox" required',html);self.assertNotIn('checked',html)
            self.assertNotIn('token-action',html);self.assertIn('type="email"',html)
        with self.assertRaises(Invalid):brand_for_host('evil.test')
    def test_concurrent_confirm_only_one_succeeds(self):
        self.request();token=self.sent[0][1]
        def run(_):
            try:self.service.confirm('weddingos',token);return True
            except Invalid:return False
        with ThreadPoolExecutor(max_workers=4) as pool:self.assertEqual(sum(pool.map(run,range(4))),1)
        self.assertEqual(len(self.rows('leads')),1)

if __name__=='__main__':unittest.main()
