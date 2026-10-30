import base64,datetime as dt,hashlib,hmac,json,os,tempfile,time,unittest
from unittest.mock import patch
from growthpilot.core import Invalid
from growthpilot.platform import Platform
from growthpilot.marketing_consent import MarketingConsent,BRANDS,VERSION
from growthpilot.marketing_registry import BrandRegistry
from growthpilot.marketing_rights import MarketingRights

class RightsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.s=Platform(self.tmp.name+'/db');self.sent=[]
        self.clock=dt.datetime(2026,10,30,tzinfo=dt.timezone.utc)
        self.m=MarketingConsent(self.s,'s'*64,lambda r,t,k:self.sent.append((dict(r),t,k))or{},lambda:self.clock)
        self.r=MarketingRights(self.m)
    def subscribed(self,brand='weddingos',email='person@customer.test'):
        self.m.request(brand,{'email':email,'consent':True,'notice_version':VERSION})
        token=self.sent[-1][1];self.m.confirm(brand,token)
        self.r.request(brand,{'email':email});return self.sent[-1][1]
    def test_fresh_verification_required_for_export_and_delete(self):
        token=self.subscribed();record=self.sent[-1][0]
        with self.assertRaises(Invalid):self.r.export('weddingos',self.m.withdrawal_token(record))
        with self.assertRaises(Invalid):self.r.export('memoire',token)
        result=self.r.export('weddingos',token)['export'];self.assertEqual(result['subscription']['email'],'person@customer.test')
        self.assertNotIn('confirm_hash',json.dumps(result));self.assertNotIn('token_hash',json.dumps(result))
        with self.assertRaises(Invalid):self.r.erase('weddingos',token,False)
        self.r.erase('weddingos',token,True)
        with self.assertRaises(Invalid):self.r.export('weddingos',token)
    def test_fresh_optin_after_erasure_requires_confirmation_and_keeps_marker(self):
        token=self.subscribed();self.r.erase('weddingos',token,True)
        self.clock+=dt.timedelta(minutes=16)
        self.m.request('weddingos',{'email':'person@customer.test','consent':True,'notice_version':VERSION})
        with self.s.db()as db:self.assertEqual(self.s.rows(db,'leads')[0]['consent'],'opt_out')
        self.m.confirm('weddingos',self.sent[-1][1]);self.r.reconcile_erasure()
        with self.s.db()as db:
            lead=self.s.rows(db,'leads')[0];self.assertEqual(lead['consent'],'opt_in');self.assertNotIn('erased_at',lead)
        self.assertEqual(len(list(self.r.marker_dir().glob('*.json'))),1)

    def test_expiry_and_rotation(self):
        old=self.subscribed();self.clock+=dt.timedelta(minutes=2)
        self.r.request('weddingos',{'email':'person@customer.test'});new=self.sent[-1][1]
        with self.assertRaises(Invalid):self.r.export('weddingos',old)
        self.clock+=dt.timedelta(minutes=31)
        with self.assertRaises(Invalid):self.r.export('weddingos',new)
    def test_unknown_address_is_generic_without_record(self):
        response=self.r.request('weddingos',{'email':'unknown@customer.test'})
        self.assertTrue(response['accepted']);self.assertEqual(self.sent,[])
    def test_erasure_redacts_contacts_and_queued_action_without_touching_other_product(self):
        token=self.subscribed();other=self.subscribed('memoire')
        record=self.sent[1][0];ident=record['id']
        with self.s.db()as db:
            lead=next(x for x in self.s.rows(db,'leads')if x['marketing_brand']=='weddingos')
            self.s.save(db,'actions',{'id':'privacy-qa','product_id':4,'campaign_id':'qa','status':'queued','payload':{'lead_id':lead['id'],'recipient':'person@customer.test','content':'Private draft'},'history':[{'email':'person@customer.test'}],'approval':{'approved':True}})
            db.execute("INSERT INTO deliveries VALUES(?,?,?,?,?,?,?,?)",('qa','privacy-qa','queued','hash',0,None,None,self.clock.isoformat()))
        self.r.erase('weddingos',token,True)
        with self.s.db()as db:
            row=self.s.get(db,'marketing_subscriptions',ident);self.assertEqual(row['status'],'erased');self.assertNotIn('email',row)
            action=self.s.get(db,'actions','privacy-qa');self.assertNotIn('person@customer.test',json.dumps(action));self.assertEqual(action['status'],'privacy_erased')
            self.assertEqual(db.execute("SELECT status FROM deliveries WHERE id='qa'").fetchone()[0],'privacy_erased')
        self.assertEqual(self.r.export('memoire',other)['export']['subscription']['status'],'confirmed')
        self.assertTrue(self.s.verify_audit()['valid'])
    def test_restore_reapplies_erasure_marker(self):
        token=self.subscribed()
        with self.s.db()as db:
            old=self.s.rows(db,'marketing_subscriptions')[0];lead=self.s.rows(db,'leads')[0]
        self.r.erase('weddingos',token,True)
        with self.s.db()as db:
            self.s.save(db,'marketing_subscriptions',old);self.s.save(db,'leads',lead)
        self.r.reconcile_erasure()
        with self.s.db()as db:
            self.assertEqual(self.s.get(db,'marketing_subscriptions',old['id'])['status'],'erased')
            self.assertNotIn('email',self.s.get(db,'leads',lead['id']))
        self.assertTrue(self.s.verify_audit()['valid'])
    def test_controls_remain_available_when_collection_disabled(self):
        token=self.subscribed();self.m.brands={k:dict(v,enabled=False)for k,v in BRANDS.items()}
        with self.assertRaises(Invalid):self.m.request('weddingos',{'email':'new@customer.test','consent':True,'notice_version':VERSION})
        self.assertIn('export',self.r.export('weddingos',token));self.r.erase('weddingos',token,True)
    def test_rights_link_email_uses_correct_scope(self):
        with patch.dict(os.environ,{'GROWTHPILOT_CONSENT_MODE':'file','GROWTHPILOT_ENVIRONMENT':'consent-qa','GROWTHPILOT_SECURE_COOKIE':'false'}):
            self.m.mailer=self.m.send_email
            self.m.request('weddingos',{'email':'qa@example.com','consent':True,'notice_version':VERSION})
            self.r.request('weddingos',{'email':'qa@example.com'})
        files=list((self.r.marker_dir().parent/'consent-test-outbox').glob('*.json'))
        mails=[json.loads(p.read_text())for p in files];message=next(x for x in mails if x['Subject'].startswith('Private consent access:'))
        self.assertIn('https://weddingos.pro/marketing-updates/rights#',message['TextBody']);self.assertEqual(message['MessageStream'],'outbound')

class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.s=Platform(self.tmp.name+'/db');self.secret='k'*64;self.registry=BrandRegistry(self.s,self.secret)
    def data(self,**extra):
        return dict({'id':'tenant-123','product_id':6,'tenant_id':'123','tenant_slug':'alpha','name':'Alpha Community','host':'alpha.jodibana.com','aliases':[],'operator':'Alpha LLC','reply_to':'support@alpha.test','privacy':'/privacy/','topics':'community news, events and service updates','enabled':True,'accepted_at':'2026-10-30T00:00:00+00:00','acceptance_version':VERSION},**extra)
    def headers(self,data,host='alpha.jodibana.com',path='/marketing-updates/',method='GET',body=b'',stamp=None):
        raw=base64.urlsafe_b64encode(json.dumps(data).encode()).decode();stamp=str(stamp or time.time())
        signed='\n'.join([stamp,method,path,host,hashlib.sha256(body).hexdigest(),raw])
        return {'X-Marketing-Context':raw,'X-Marketing-Time':stamp,'X-Marketing-Signature':hmac.new(self.secret.encode(),signed.encode(),hashlib.sha256).hexdigest()}
    def test_signed_verified_host_registers_isolated_brand(self):
        brand,data=self.registry.resolve('alpha.jodibana.com',self.headers(self.data()),'GET','/marketing-updates/')
        self.assertEqual(brand,'tenant-123');self.assertEqual(data['operator'],'Alpha LLC')
        with self.assertRaises(Invalid):self.registry.resolve('beta.jodibana.com',self.headers(self.data()),'GET','/marketing-updates/')
    def test_forgery_stale_or_method_body_replay_rejected(self):
        for headers in [self.headers(self.data(),stamp=time.time()-70),dict(self.headers(self.data()),**{'X-Marketing-Signature':'bad'})]:
            with self.assertRaises(Invalid):self.registry.resolve('alpha.jodibana.com',headers,'GET','/marketing-updates/')
        with self.assertRaises(Invalid):self.registry.resolve('alpha.jodibana.com',self.headers(self.data()),'POST','/marketing-updates/',b'{}')
    def test_cannot_override_other_products_or_flagship(self):
        for host in ['weddingos.pro','www.jodiusa.com']:
            data=self.data(host=host)
            with self.assertRaises(Invalid):self.registry.resolve(host,self.headers(data,host=host),'GET','/marketing-updates/')
    def test_disabling_cannot_be_reversed_by_older_signed_context(self):
        old=self.headers(self.data(),stamp=time.time()-.1)
        self.registry.resolve('alpha.jodibana.com',self.headers(self.data(enabled=False)),'GET','/marketing-updates/')
        _,data=self.registry.resolve('alpha.jodibana.com',old,'GET','/marketing-updates/');self.assertFalse(data['enabled'])
    def test_no_shared_consent_between_two_tenants(self):
        a=self.data();b=self.data(id='tenant-456',tenant_id='456',tenant_slug='beta',host='beta.jodibana.com')
        for data in [a,b]:self.registry.resolve(data['host'],self.headers(data,host=data['host']),'GET','/marketing-updates/')
        sent=[];m=MarketingConsent(self.s,'s'*64,lambda r,t,k:sent.append((r,t,k))or{},brands=self.registry.all())
        m.request('tenant-123',{'email':'member@customer.test','consent':True,'notice_version':VERSION})
        with self.assertRaises(Invalid):m.confirm('tenant-456',sent[-1][1])
        m.confirm('tenant-123',sent[-1][1]);rights=MarketingRights(m);rights.request('tenant-123',{'email':'member@customer.test'});token=sent[-1][1]
        with self.assertRaises(Invalid):rights.export('tenant-456',token)
        self.assertEqual(rights.export('tenant-123',token)['export']['subscription']['brand'],'tenant-123')

if __name__=='__main__':unittest.main()
