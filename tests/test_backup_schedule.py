import contextlib
import datetime as dt
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from growthpilot.backup_schedule import DailyBackup
from growthpilot.platform import Platform
from growthpilot.core import Invalid


class BackupScheduleTests(unittest.TestCase):
    def setUp(self):
        self.when = dt.datetime(2026, 11, 12, tzinfo=dt.timezone.utc)
        self.stamp = 0
        self.store = Mock()
        self.store.db.side_effect = lambda: contextlib.nullcontext(object())
        self.scheduler = DailyBackup(self.store, 'unused',
            clock=lambda: self.when, monotonic=lambda: self.stamp)

    def test_success_only_once_per_utc_day(self):
        self.assertEqual(self.scheduler.tick()['status'], 'backed_up')
        self.stamp = 80000
        self.assertEqual(self.scheduler.tick()['status'], 'current')
        self.store.backup.assert_called_once_with('unused')
        self.store.audit.assert_called_once()

    def test_failure_does_not_retry_every_worker_tick(self):
        self.store.backup.side_effect = Invalid('not configured')
        with self.assertRaises(Invalid): self.scheduler.tick()
        for tick in range(15, 3600, 15):
            self.stamp = tick
            self.assertEqual(self.scheduler.tick()['status'], 'retry_deferred')
        self.store.backup.assert_called_once()
        self.assertIsNone(self.scheduler.last_success)
        self.store.audit.assert_not_called()
        self.stamp = 3600
        self.store.backup.side_effect = None
        self.assertEqual(self.scheduler.tick()['status'], 'backed_up')
        self.assertEqual(self.store.backup.call_count, 2)

    def test_midnight_does_not_bypass_failed_retry_delay(self):
        self.store.backup.side_effect = OSError('disk full')
        with self.assertRaises(OSError): self.scheduler.tick()
        self.when += dt.timedelta(days=1)
        self.stamp = 15
        self.assertEqual(self.scheduler.tick()['status'], 'retry_deferred')

    def test_next_day_success_can_run_after_interval(self):
        self.scheduler.tick()
        self.when += dt.timedelta(days=1)
        self.stamp = 86400
        self.assertEqual(self.scheduler.tick()['status'], 'backed_up')
        self.assertEqual(self.store.backup.call_count, 2)

    def test_audit_failure_does_not_duplicate_completed_backup(self):
        self.store.audit.side_effect = OSError('audit failed')
        with self.assertRaises(OSError): self.scheduler.tick()
        self.stamp = 3600
        self.assertEqual(self.scheduler.tick()['status'], 'current')
        self.store.backup.assert_called_once()

    def test_missing_key_leaves_no_new_database_copies(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = Platform(root/'growthpilot.db')
            backups = root/'backups'
            backups.mkdir()
            old = backups/'existing.db'
            old.write_bytes(b'preserve historical evidence')
            with patch.dict(os.environ, {'GROWTHPILOT_CONSENT_SECRET': ''}):
                for _ in range(3):
                    with self.assertRaises(Invalid): store.backup(backups)
            self.assertEqual(list(backups.iterdir()), [old])
            self.assertEqual(old.read_bytes(), b'preserve historical evidence')
            self.assertTrue(store.verify_audit()['valid'])

    def test_restart_with_missing_key_still_cannot_accumulate_copies(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = Platform(root/'growthpilot.db')
            with patch.dict(os.environ, {'GROWTHPILOT_CONSENT_SECRET': ''}):
                for _ in range(3):
                    with self.assertRaises(Invalid): DailyBackup(store, root/'backups').tick()
            self.assertFalse((root/'backups').exists())
