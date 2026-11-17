import os,tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch
from growthpilot.platform import Platform
from growthpilot.marketing_consent import MarketingConsent
from growthpilot.rotation_preflight import snapshot,verify_unchanged
from growthpilot.core import Invalid

class RotationPreflightTests(unittest.TestCase):
 def setUp(self):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)
  env=patch.dict(os.environ,{'GROWTHPILOT_CONSENT_SECRET':'synthetic-preflight-key-only-'*3});env.start();self.addCleanup(env.stop)
  self.s=Platform(self.root/'growthpilot.db');self.d=self.root/'backups';self.first=self.s.backup(self.d);self.service=MarketingConsent(self.s)
 def test_inventory_and_recheck_do_not_change_bytes(self):
  before={str(p):p.read_bytes() for p in self.d.rglob('*') if p.is_file()}
  plan=snapshot(self.d,self.service);self.assertEqual(plan['set_count'],1);self.assertFalse(plan['cutover_authorized'])
  self.assertTrue(verify_unchanged(self.d,self.service,plan));self.assertEqual(before,{str(p):p.read_bytes() for p in self.d.rglob('*') if p.is_file()})
  self.assertNotIn(os.environ['GROWTHPILOT_CONSENT_SECRET'],json.dumps(plan))
 def test_added_snapshot_invalidates_plan(self):
  plan=snapshot(self.d,self.service);self.s.backup(self.d)
  with self.assertRaises(Invalid):verify_unchanged(self.d,self.service,plan)
 def test_tampered_snapshot_refused(self):
  (self.d/self.first['file']).write_bytes(b'synthetic damage')
  with self.assertRaises(Invalid):snapshot(self.d,self.service)
 def test_in_progress_backup_refused(self):
  (self.d/'managed-v1'/'.pending').mkdir()
  with self.assertRaises(Invalid):snapshot(self.d,self.service)
 def test_symlink_refused(self):
  source=(self.d/self.first['file']).parent;name=source.name
  archive=self.root/'outside';source.rename(archive);source.symlink_to(archive,target_is_directory=True)
  with self.assertRaises(Invalid):snapshot(self.d,self.service)
 def test_manifest_tampering_refused(self):
  plan=snapshot(self.d,self.service);plan['payload']['sets'][0]['name']='changed'
  with self.assertRaises(Invalid):verify_unchanged(self.d,self.service,plan)
 def test_wrong_key_refused(self):
  with patch.dict(os.environ,{'GROWTHPILOT_CONSENT_SECRET':'different-synthetic-key-'*3}):
   with self.assertRaises(Invalid):snapshot(self.d,MarketingConsent(self.s))
 def test_busy_writer_refused_without_wait(self):
  from growthpilot.backup_maintenance import lock
  with lock(self.d/'managed-v1'):
   with self.assertRaises(BlockingIOError):snapshot(self.d,self.service)
