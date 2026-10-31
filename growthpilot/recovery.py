"""Verified database recovery with a fresh, separately retained privacy checkpoint.

Never overwrite a running database. Use an empty destination, then inspect it
offline before cutover. A backup alone is intentionally insufficient.
"""
import datetime as dt
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tarfile
import tempfile
from .core import Invalid
from .marketing_consent import MarketingConsent
from .marketing_rights import MarketingRights
from .marketing_lifecycle import MarketingLifecycle

JOURNALS = ("marketing-erasure-markers", "marketing-account-receipts")


def signed(service, data):
    return dict(data, signature=service.sign("recovery:" + json.dumps(data, sort_keys=True)))


def verified(service, value):
    data = dict(value); signature = data.pop("signature")
    if not hmac.compare_digest(signature, service.sign("recovery:" + json.dumps(data, sort_keys=True))):
        raise Invalid("Recovery manifest signature failed")
    return data


def journal_snapshot(store):
    root = Path(store.path).parent
    return {str(p.relative_to(root)): p.read_bytes() for name in JOURNALS
            for p in (root / name).glob("*.json")}


def checkpoint(store, destination):
    target = Path(destination)
    target.mkdir(mode=0o700, parents=True, exist_ok=False)
    try:
        payload = journal_snapshot(store)
        manifest = {"version":1,"created_at":dt.datetime.now(dt.timezone.utc).isoformat(),
                    "files":{n:hashlib.sha256(v).hexdigest() for n,v in payload.items()}}
        for name, data in payload.items():
            path = target/name; path.parent.mkdir(mode=0o700, exist_ok=True)
            path.write_bytes(data); path.chmod(0o600)
        p=target/'checkpoint.json';p.write_text(json.dumps(signed(MarketingConsent(store), manifest)));p.chmod(0o600)
        return {"files":len(payload),"created_at":manifest["created_at"]}
    except Exception:
        shutil.rmtree(target); raise


def bundle(store, database):
    database=Path(database);target=database.with_suffix('.recovery.tar.gz')
    payload={"growthpilot.db":database.read_bytes(), **journal_snapshot(store)}
    manifest={"version":1,"created_at":dt.datetime.now(dt.timezone.utc).isoformat(),
              "files":{n:hashlib.sha256(v).hexdigest() for n,v in payload.items()}}
    payload['manifest.json']=json.dumps(signed(MarketingConsent(store),manifest)).encode()
    fd,temp=tempfile.mkstemp(dir=database.parent,prefix='.recovery-')
    os.close(fd)
    try:
        with tarfile.open(temp,'w:gz') as archive:
            for name,data in payload.items():
                info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o600
                archive.addfile(info,io.BytesIO(data))
        os.replace(temp,target)
    finally:
        if os.path.exists(temp):os.unlink(temp)
    return {"bundle":target.name,"bundle_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
            "recovery_requires":"fresh separately retained privacy checkpoint and original consent signing key"}


def safe_member(name):
    return name=='growthpilot.db' or bool(re.fullmatch(r'(marketing-erasure-markers|marketing-account-receipts)/[0-9a-f]{64}\.json',name))


def restore(store, archive_path, destination, latest):
    service=MarketingConsent(store);latest=Path(latest);destination=Path(destination)
    current=verified(service,json.loads((latest/'checkpoint.json').read_text()))
    age=(dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(current['created_at'])).total_seconds()
    if not -60<=age<=3600:raise Invalid('A fresh privacy checkpoint (within one hour) is required')
    fresh={}
    for name,digest in current['files'].items():
        if not safe_member(name) or name=='growthpilot.db':raise Invalid('Unsafe checkpoint entry')
        data=(latest/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest:raise Invalid('Privacy checkpoint is incomplete or damaged')
        fresh[name]=data
    with tarfile.open(archive_path,'r:gz') as archive:
        members=archive.getmembers();names=[m.name for m in members]
        if len(names)!=len(set(names)) or any(not m.isfile() or (m.name!='manifest.json' and not safe_member(m.name)) for m in members):
            raise Invalid('Unsafe recovery archive')
        manifest=verified(service,json.loads(archive.extractfile('manifest.json').read()))
        if set(names)!=set(manifest['files'])|{'manifest.json'}:raise Invalid('Incomplete recovery archive')
        payload={n:archive.extractfile(n).read()for n in manifest['files']}
    for name,data in payload.items():
        if hashlib.sha256(data).hexdigest()!=manifest['files'][name]:raise Invalid('Recovery checksum failed')
    if not {n for n in payload if n!='growthpilot.db'}<=set(fresh):
        raise Invalid('Latest checkpoint has lost privacy history')
    destination.mkdir(mode=0o700,parents=True,exist_ok=False)
    try:
        for name,data in {'growthpilot.db':payload['growthpilot.db'],**fresh}.items():
            path=destination/name;path.parent.mkdir(mode=0o700,exist_ok=True);path.write_bytes(data);path.chmod(0o600)
        with sqlite3.connect(destination/'growthpilot.db')as db:
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise Invalid('Restored database integrity failed')
        from .platform import Platform
        restored=Platform(destination/'growthpilot.db')
        lifecycle=MarketingLifecycle(restored)
        # Verify every account receipt as well as every erasure marker.
        for p in (destination/'marketing-account-receipts').glob('*.json'):lifecycle.read_receipt(p.stem)
        MarketingRights(MarketingConsent(restored)).reconcile_erasure()
        audit=restored.verify_audit()
        if not audit['valid']:raise Invalid('Restored audit chain failed verification')
        return {'integrity':'ok','audit_valid':True,'privacy_reconciled':True,'journal_files':len(fresh)}
    except Exception:
        shutil.rmtree(destination);raise
