import datetime as dt
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from growthpilot.platform import Platform
from growthpilot.core import Invalid
from growthpilot.backup_schedule import DailyBackup,health
from growthpilot import backup_maintenance as bm
from growthpilot.recovery import checkpoint,restore

class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
        env=patch.dict(os.environ,{'GROWTHPILOT_CONSENT_SECRET':'synthetic-backup-maintenance-key-'*3});env.start();self.addCleanup(env.stop)
        self.store=Platform(self.root/'growthpilot.db');self.directory=self.root/'backups'

    def test_retention_and_recovery_preserve_legacy_and_other_files(self):
        self.directory.mkdir();legacy=self.directory/'growthpilot-20200101-000000.db';legacy.write_bytes(b'preserve')
        latest=None
        for _ in range(17):latest=self.store.backup(self.directory)
        root=self.directory/'managed-v1';sets=sorted(p for p in root.iterdir() if p.name.startswith('v1-'))
        self.assertEqual(len(sets),14);self.assertEqual(legacy.read_bytes(),b'preserve')
        self.assertEqual(latest['retention']['removed_sets'],1)
        checkpoint(self.store,self.root/'checkpoint')
        result=restore(self.store,self.directory/latest['bundle'],self.root/'restored',self.root/'checkpoint')
        self.assertEqual(result['integrity'],'ok');self.assertTrue(result['audit_valid'])

    def test_bundle_failure_cleans_partial_attempt(self):
        with patch.object(bm,'bundle',side_effect=OSError('synthetic failure')):
            for _ in range(3):
                with self.assertRaises(OSError):self.store.backup(self.directory)
        self.assertEqual([p.name for p in (self.directory/'managed-v1').iterdir()],['.lock'])

    def test_low_space_creates_no_snapshot_and_preserves_old(self):
        self.store.backup(self.directory)
        before={str(p):p.read_bytes() for p in self.directory.rglob('*') if p.is_file()}
        with patch.object(bm.shutil,'disk_usage',return_value=type('Disk',(),{'free':1})()):
            with self.assertRaises(Invalid):self.store.backup(self.directory)
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.directory.rglob('*') if p.is_file()})

    def test_process_crash_staging_is_cleaned_on_next_attempt(self):
        root=self.directory/'managed-v1';root.mkdir(parents=True)
        (root/'.pending').mkdir();(root/'.pending'/'growthpilot.db').write_bytes(b'partial')
        self.store.backup(self.directory)
        self.assertFalse((root/'.pending').exists())

    def test_tampered_set_blocks_retention_without_deleting_evidence(self):
        with patch.object(bm,'KEEP',2):
            first=self.store.backup(self.directory);self.store.backup(self.directory)
            p=self.directory/first['file'];p.write_bytes(b'corrupt evidence')
            result=self.store.backup(self.directory)
            self.assertEqual(result['retention']['status'],'blocked')
            self.assertEqual(p.read_bytes(),b'corrupt evidence')
            self.assertEqual(len(list((self.directory/'managed-v1').glob('v1-*'))),3)

    def test_unsafe_stage_never_followed_or_deleted(self):
        root=self.directory/'managed-v1';root.mkdir(parents=True)
        outside=self.root/'keep';outside.mkdir();(outside/'growthpilot.db').write_bytes(b'keep')
        (root/'.pending').symlink_to(outside,target_is_directory=True)
        with self.assertRaises(Invalid):self.store.backup(self.directory)
        self.assertEqual((outside/'growthpilot.db').read_bytes(),b'keep')

    def test_restart_keeps_success_and_failure_cooldown(self):
        now=dt.datetime.now(dt.timezone.utc)
        self.assertEqual(DailyBackup(self.store,self.directory,clock=lambda:now).tick()['status'],'backed_up')
        self.assertEqual(DailyBackup(self.store,self.directory,clock=lambda:now).tick()['status'],'current')
        tomorrow=now+dt.timedelta(days=1)
        with patch.object(self.store,'backup',side_effect=OSError('failure')) as create:
            with self.assertRaises(OSError):DailyBackup(self.store,self.directory,clock=lambda:tomorrow).tick()
            self.assertEqual(DailyBackup(self.store,self.directory,clock=lambda:tomorrow+dt.timedelta(seconds=15)).tick()['status'],'retry_deferred')
            self.assertEqual(create.call_count,1)
        self.assertEqual(health(self.directory)['status'],'failed')

    def test_interrupted_retirement_resumes_without_touching_kept_sets(self):
        self.store.backup(self.directory);self.store.backup(self.directory)
        root=self.directory/'managed-v1';old=sorted(root.glob('v1-*'))[0]
        dest=root/('.retiring-'+old.name);old.rename(dest);(dest/'growthpilot.db').unlink()
        result=self.store.backup(self.directory)
        self.assertEqual(result['retention']['status'],'ok');self.assertFalse(dest.exists())

    def test_corrupt_schedule_fails_closed(self):
        s=DailyBackup(self.store,self.directory);s.path.write_text('broken')
        with self.assertRaises(ValueError):s.tick()
        self.assertFalse(self.directory.exists())
