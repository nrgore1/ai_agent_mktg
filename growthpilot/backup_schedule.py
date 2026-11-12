"""Bound daily backup retries; failures never count as successful recovery."""
import datetime as dt
import time


class DailyBackup:
    def __init__(self, store, directory, clock=None, monotonic=None):
        self.store = store
        self.directory = directory
        self.clock = clock or (lambda: dt.datetime.now(dt.timezone.utc))
        self.monotonic = monotonic or time.monotonic
        self.last_success = None
        self.retry_after = 0.0

    def tick(self):
        today = self.clock().astimezone(dt.timezone.utc).date().isoformat()
        if today == self.last_success:
            return {"status": "current"}
        stamp = self.monotonic()
        if stamp < self.retry_after:
            return {"status": "retry_deferred"}
        # Set before attempting: a signing, I/O or integrity failure must not
        # produce another database snapshot on the worker's next 15-second tick.
        self.retry_after = stamp + 3600
        result = self.store.backup(self.directory)
        self.last_success = today
        # Audit failure must not regenerate an already successful backup.
        with self.store.db() as db:
            self.store.audit(db, "daily_backup", "system", {"date": today}, "worker")
        return {"status": "backed_up", "result": result}
