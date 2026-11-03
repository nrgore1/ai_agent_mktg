"""Authenticated product deletion and bounded operational consent retention."""
import datetime as dt
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import time
from .core import Invalid
from .marketing_consent import MarketingConsent
from .marketing_registry import BrandRegistry
from .marketing_rights import MarketingRights

PATH = "/internal/marketing/account"
POLICY = {"version": "2026-10-30-v1", "pending_days": 7, "withdrawn_days": 30,
          "rate_limit_days": 2, "managed_backup_days": 30}


class MarketingLifecycle:
    def __init__(self, store, service=None, keys=None):
        self.s = store
        self.m = service or MarketingConsent(store, brands=BrandRegistry(store).all())
        self.rights = MarketingRights(self.m)
        self.keys = keys

    def authorize(self, headers, body):
        keys = self.keys
        if keys is None:
            path = os.environ.get("GROWTHPILOT_PRIVACY_KEYS_FILE", "")
            keys = json.loads(Path(path).read_text()) if path else {}
        service = headers.get("X-Privacy-Service", "")
        row = keys.get(service, {})
        secret = row.get("secret", "")
        try:
            stamp = headers["X-Privacy-Time"]
            if not abs(time.time() - float(stamp)) <= 60 or len(secret) < 32:
                raise ValueError()
            message = "\n".join([service, stamp, "POST", PATH, hashlib.sha256(body).hexdigest()])
            signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, headers.get("X-Privacy-Signature", "")):
                raise ValueError()
            data = json.loads(body)
            if set(data) != {"brand", "email", "event_id", "operation"}:
                raise ValueError()
            brand = data["brand"]
            permitted = brand in row.get("brands", []) or (
                row.get("tenant_brands") is True and re.fullmatch(r"tenant-[1-9][0-9]*", brand))
            if not permitted or brand not in self.m.brands:
                raise ValueError()
            if data["operation"] not in {"erase_verified", "request_erasure", "export_verified"}:
                raise ValueError()
            if not isinstance(data["event_id"], str) or not 1 <= len(data["event_id"]) <= 200:
                raise ValueError()
            email = data["email"]
            if not isinstance(email, str) or len(email) > 254 or not re.fullmatch(r"[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+", email):
                raise ValueError()
        except (ValueError, TypeError, KeyError):
            raise Invalid("Privacy service authentication rejected")
        return service, data

    def receipt_path(self, ident):
        folder = Path(self.s.path).parent / "marketing-account-receipts"
        folder.mkdir(mode=0o700, exist_ok=True)
        return folder / (ident + ".json")

    def persist_receipt(self, receipt):
        value = dict(receipt)
        value["signature"] = self.m.sign("account-receipt:" + json.dumps(receipt, sort_keys=True))
        path = self.receipt_path(receipt["id"])
        temporary = path.with_suffix(".tmp")
        with temporary.open("w") as stream:
            os.chmod(temporary, 0o600)
            json.dump(value, stream);stream.flush();os.fsync(stream.fileno())
        temporary.replace(path)
        if hasattr(os, "O_DIRECTORY"):
            descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try: os.fsync(descriptor)
            finally: os.close(descriptor)

    def read_receipt(self, ident):
        path = self.receipt_path(ident)
        if not path.exists(): return None
        value = json.loads(path.read_text())
        signature = value.pop("signature")
        if not hmac.compare_digest(signature, self.m.sign("account-receipt:" + json.dumps(value, sort_keys=True))):
            raise Invalid("Account privacy journal verification failed")
        return value

    def account(self, headers, body):
        service, data = self.authorize(headers, body)
        brand, email, operation = data["brand"], data["email"].strip().lower(), data["operation"]
        ident = self.m.identifier(brand, email)
        receipt_id = self.m.sign("account-event:" + service + ":" + brand + ":" + data["event_id"])
        if operation == "export_verified":
            with self.s.db() as db:
                record = next((r for r in self.s.rows(db, "marketing_subscriptions") if r["id"] == ident), None)
                fields = ["email", "brand", "status", "notice_text", "notice_version", "requested_at", "confirmed_at", "withdrawn_at", "erased_at"]
                return {"status": "exported", "marketing": {k: record[k] for k in fields if k in record} if record else None}
        with self.s.db() as db:
            previous = self.read_receipt(receipt_id) or next((r for r in self.s.rows(db, "marketing_account_events") if r["id"] == receipt_id), None)
            if previous:
                if previous["subject"] != ident or previous["operation"] != operation:
                    raise Invalid("Privacy event does not match its previous request")
                return {"status": previous["status"], "receipt": receipt_id}
            record = next((r for r in self.s.rows(db, "marketing_subscriptions") if r["id"] == ident), None)
            if operation == "erase_verified":
                # Create a suppression even if the account never subscribed.
                record = record or {"id": ident, "brand": brand, "product_id": self.m.brands[brand]["product_id"]}
                marker = self.rights.write_marker(record)
                self.rights.scrub(db, marker)
                status = "erased"
            else:
                status = "verification_required"
            receipt = {
                "id": receipt_id, "subject": ident, "brand": brand, "operation": operation,
                "status": status, "at": self.m.clock().isoformat(),
            }
            self.persist_receipt(receipt)
            self.s.save(db, "marketing_account_events", receipt)
            self.s.audit(db, "account_marketing_privacy", receipt_id, {"brand": brand, "status": status}, service)
        if operation == "request_erasure":
            # An unverified product address must not erase another person's consent.
            # Reuse the fresh mailbox-verification journey; never reveal a match.
            self.rights.request(brand, {"email": email}, remote="account:" + service)
        return {"status": status, "receipt": receipt_id}

    def retention(self, apply=False):
        stamp = self.m.clock()
        report = {"policy": POLICY, "apply": apply, "expired_private_links": 0,
                  "aged_contacts": 0, "expired_rate_limits": 0, "managed_backups": 0}
        with self.s.db() as db:
            for row in self.s.rows(db, "marketing_rights_tokens"):
                if dt.datetime.fromisoformat(row["expires_at"]) <= stamp:
                    report["expired_private_links"] += 1
                    if apply: db.execute("DELETE FROM records WHERE kind='marketing_rights_tokens' AND id=?", (row["id"],))
            for row in self.s.rows(db, "marketing_subscriptions"):
                status = row.get("status")
                field = "requested_at" if status == "pending" else "withdrawn_at"
                days = POLICY["pending_days"] if status == "pending" else POLICY["withdrawn_days"]
                if status not in {"pending", "withdrawn"} or not row.get(field): continue
                if dt.datetime.fromisoformat(row[field]) <= stamp - dt.timedelta(days=days):
                    report["aged_contacts"] += 1
                    if apply:
                        marker = self.rights.write_marker(row)
                        self.rights.scrub(db, marker)
            for row in self.s.rows(db, "marketing_rate_limits"):
                if row["start"] < stamp.timestamp() - POLICY["rate_limit_days"] * 86400:
                    report["expired_rate_limits"] += 1
                    if apply: db.execute("DELETE FROM records WHERE kind='marketing_rate_limits' AND id=?", (row["id"],))
        # Only exact application-owned database backup names in its own directory.
        folder = Path(self.s.path).parent / "backups"
        if folder.exists():
            for path in folder.glob("growthpilot-*"):
                if path.is_symlink() or not re.fullmatch(r"growthpilot-\d{8}-\d{6}\.(db|recovery\.tar\.gz)", path.name): continue
                if path.stat().st_mtime < stamp.timestamp() - POLICY["managed_backup_days"] * 86400:
                    report["managed_backups"] += 1
                    if apply: path.unlink()
        if apply:
            with self.s.db() as db:
                self.s.save(db, "marketing_retention", {"id": "current", "at": stamp.isoformat(), **report})
                self.s.audit(db, "marketing_retention_sweep", "current", report, "privacy_worker")
        return report
