import datetime as dt,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from growthpilot.platform import Platform
from growthpilot.marketing_consent import MarketingConsent,VERSION
from growthpilot.marketing_rights import MarketingRights
from growthpilot.recovery import checkpoint,restore,signed
from growthpilot.core import Invalid

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.env=patch.dict(os.environ,{'GROWTHPILOT_CONSENT_SECRET':'recovery-test-key-only-'*3});self.env.start();self.addCleanup(self.env.stop)
        self.root=Path(self.tmp.name);(self.root/'live').mkdir();self.store=Platform(self.root/'live'/'growthpilot.db');self.sent=[]
        self.m=MarketingConsent(self.store,mailer=lambda r,t,k:self.sent.append(t)or{})
        self.rights=MarketingRights(self.m)
        self.m.request('weddingos',{'email':'synthetic@example.test','consent':True,'notice_version':VERSION})
        self.m.confirm('weddingos',self.sent[-1]);self.backup=self.store.backup(self.root/'backups')
        self.archive=self.root/'backups'/self.backup['bundle']
        self.rights.request('weddingos',{'email':'synthetic@example.test'});self.rights.erase('weddingos',self.sent[-1],True)
        checkpoint(self.store,self.root/'latest')
    def test_old_backup_replays_latest_erasure_and_preserves_audit(self):
        result=restore(self.store,self.archive,self.root/'restored',self.root/'latest')
        self.assertTrue(result['privacy_reconciled']);s=Platform(self.root/'restored'/'growthpilot.db')
        with s.db()as db:self.assertNotIn('synthetic@example.test',json.dumps(s.rows(db,'marketing_subscriptions')))
        self.assertTrue(s.verify_audit()['valid'])
    def test_missing_checkpoint_refused(self):
        with self.assertRaises(FileNotFoundError):restore(self.store,self.archive,self.root/'restored',self.root/'absent')
        self.assertFalse((self.root/'restored').exists())
    def test_missing_journal_refused(self):
        next((self.root/'latest'/'marketing-erasure-markers').glob('*.json')).unlink()
        with self.assertRaises(FileNotFoundError):restore(self.store,self.archive,self.root/'restored',self.root/'latest')
    def test_corrupt_journal_refused(self):
        next((self.root/'latest'/'marketing-erasure-markers').glob('*.json')).write_text('{}')
        with self.assertRaises(Invalid):restore(self.store,self.archive,self.root/'restored',self.root/'latest')
    def test_stale_checkpoint_refused(self):
        p=self.root/'latest'/'checkpoint.json';v=json.loads(p.read_text());v.pop('signature');v['created_at']=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=2)).isoformat();p.write_text(json.dumps(signed(self.m,v)))
        with self.assertRaises(Invalid):restore(self.store,self.archive,self.root/'restored',self.root/'latest')
    def test_wrong_signing_key_refused(self):
        with patch.dict(os.environ,{'GROWTHPILOT_CONSENT_SECRET':'other-key-'*8}):
            with self.assertRaises(Invalid):restore(self.store,self.archive,self.root/'restored',self.root/'latest')
    def test_existing_destination_never_overwritten(self):
        p=self.root/'restored';p.mkdir();(p/'keep').write_text('safe')
        with self.assertRaises(FileExistsError):restore(self.store,self.archive,p,self.root/'latest')
        self.assertEqual((p/'keep').read_text(),'safe')

