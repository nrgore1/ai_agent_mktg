import datetime as dt
import hashlib,hmac,json,os,tempfile,time,unittest
from pathlib import Path
from growthpilot.platform import Platform
from growthpilot.core import Invalid
from growthpilot.marketing_consent import MarketingConsent,VERSION
from growthpilot.marketing_lifecycle import MarketingLifecycle,PATH

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.s=Platform(self.tmp.name+'/db');self.sent=[]
        self.clock=dt.datetime(2026,10,30,tzinfo=dt.timezone.utc)
        self.m=MarketingConsent(self.s,'s'*64,lambda r,t,k:self.sent.append((dict(r),t,k))or{},lambda:self.clock)
        self.keys={'weddingos':{'secret':'w'*64,'brands':['weddingos']},'memoire':{'secret':'m'*64,'brands':['memoire']}}
        self.l=MarketingLifecycle(self.s,self.m,self.keys)
    def signed(self,operation='erase_verified',brand='weddingos',event='account-1',service='weddingos',email='one@customer.test',stamp=None):
        body=json.dumps(dict(brand=brand,email=email,event_id=event,operation=operation)).encode()
        stamp=str(stamp or time.time());message='\n'.join([service,stamp,'POST',PATH,hashlib.sha256(body).hexdigest()])
        signature=hmac.new(self.keys[service]['secret'].encode(),message.encode(),hashlib.sha256).hexdigest()
        return {'X-Privacy-Service':service,'X-Privacy-Time':stamp,'X-Privacy-Signature':signature},body
    def subscribe(self,brand='weddingos',email='one@customer.test',confirmed=True):
        self.m.request(brand,dict(email=email,consent=True,notice_version=VERSION))
        if confirmed:self.m.confirm(brand,self.sent[-1][1])
    def record(self,brand='weddingos'):
        with self.s.db()as db:return next(r for r in self.s.rows(db,'marketing_subscriptions')if r['brand']==brand)
    def test_signed_erasure_is_scoped_and_does_not_store_email_in_receipt(self):
        self.subscribe();self.subscribe('memoire')
        result=self.l.account(*self.signed());self.assertEqual(result['status'],'erased')
        self.assertNotIn('email',self.record());self.assertEqual(self.record('memoire')['status'],'confirmed')
        receipt=next((Path(self.tmp.name)/'marketing-account-receipts').glob('*.json')).read_text()
        self.assertNotIn('one@customer.test',receipt)
    def test_unverified_account_never_erases_consent(self):
        self.subscribe('memoire')
        result=self.l.account(*self.signed('request_erasure','memoire',service='memoire'))
        self.assertEqual(result['status'],'verification_required')
        self.assertEqual(self.record('memoire')['status'],'confirmed');self.assertEqual(self.sent[-1][2],'rights')
    def test_unverified_unknown_email_same_response_without_email(self):
        result=self.l.account(*self.signed('request_erasure'))
        self.assertEqual(result['status'],'verification_required');self.assertEqual(self.sent,[])
    def test_missing_bad_expired_and_cross_scope_credentials_denied(self):
        headers,body=self.signed()
        for h,b in [({},body),(dict(headers,**{'X-Privacy-Signature':'bad'}),body),(headers,body+b' '),self.signed(stamp=time.time()-80),self.signed(brand='memoire')]:
            with self.assertRaises(Invalid):self.l.account(h,b)
    def test_event_retry_and_restore_cannot_erase_fresh_subscription(self):
        self.subscribe();args=self.signed();self.l.account(*args)
        self.clock+=dt.timedelta(minutes=16);self.subscribe()
        with self.s.db()as db:db.execute("DELETE FROM records WHERE kind='marketing_account_events'")
        self.l.account(*self.signed());self.l.rights.reconcile_erasure()
        self.assertEqual(self.record()['status'],'confirmed')
    def test_event_subject_reuse_rejected(self):
        self.l.account(*self.signed())
        with self.assertRaises(Invalid):self.l.account(*self.signed(email='other@customer.test'))
    def test_verified_export_has_no_credentials(self):
        self.subscribe();r=self.l.account(*self.signed('export_verified'))
        self.assertEqual(r['marketing']['email'],'one@customer.test');self.assertNotIn('confirm_hash',r['marketing'])
    def test_retention_dry_run_preserves_then_removes_only_aged_records(self):
        self.subscribe(confirmed=False);self.subscribe('memoire')
        self.l.rights.request('memoire',{'email':'one@customer.test'})
        self.clock+=dt.timedelta(days=8)
        dry=self.l.retention();self.assertEqual(dry['aged_contacts'],1);self.assertEqual(self.record()['status'],'pending')
        self.l.retention(True);self.assertEqual(self.record()['status'],'erased');self.assertEqual(self.record('memoire')['status'],'confirmed')
        with self.s.db()as db:self.assertEqual(self.s.rows(db,'marketing_rights_tokens'),[])
    def test_withdrawn_retention_boundary(self):
        self.subscribe();r=self.record();self.m.withdraw('weddingos',self.m.withdrawal_token(r))
        self.clock+=dt.timedelta(days=29);self.assertEqual(self.l.retention(True)['aged_contacts'],0)
        self.clock+=dt.timedelta(days=1);self.assertEqual(self.l.retention(True)['aged_contacts'],1)
    def test_backup_expiry_only_owned_regular_files(self):
        folder=Path(self.tmp.name)/'backups';folder.mkdir()
        owned=folder/'growthpilot-20260901-000000.db';owned.write_bytes(b'old')
        other=folder/'unrelated.db';other.write_bytes(b'keep')
        journal=Path(self.tmp.name)/'marketing-erasure-markers';journal.mkdir()
        marker=journal/'retained.json';marker.write_bytes(b'keep')
        old=(self.clock-dt.timedelta(days=31)).timestamp()
        for p in [owned,other,marker]:os.utime(p,(old,old))
        self.l.retention(True);self.assertFalse(owned.exists());self.assertTrue(other.exists());self.assertTrue(marker.exists())
    def test_erasure_does_not_require_existing_subscription(self):
        self.l.account(*self.signed())
        self.assertEqual(self.record()['status'],'erased')
    def test_tampered_durable_receipt_fails_closed(self):
        self.l.account(*self.signed())
        p=next((Path(self.tmp.name)/'marketing-account-receipts').glob('*.json'))
        value=json.loads(p.read_text());value['status']='fake';p.write_text(json.dumps(value))
        with self.assertRaises(Invalid):self.l.account(*self.signed())
