"""Bounded, atomic backup sets. Legacy backups are never retention candidates."""
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import uuid
from .core import Invalid
from .marketing_consent import MarketingConsent
from .recovery import bundle, signed, verified

KEEP = 14
RESERVE = 5 * 1024**3
FILES = {'growthpilot.db', 'growthpilot.recovery.tar.gz', 'receipt.json'}
NAME = r'v1-\d{20}-[0-9a-f]{8}'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)

def plain_dir(path):
    if path.is_symlink() or not path.is_dir(): raise Invalid('Unsafe backup directory')

def safe_files(path):
    plain_dir(path)
    children = list(path.iterdir())
    if any(p.name not in FILES or p.is_symlink() or not p.is_file() for p in children):
        raise Invalid('Unexpected backup-set contents; manual review required')
    return children

def remove_set(path):
    # Only our three known files, in an exclusively locked managed directory.
    for p in sorted(safe_files(path), key=lambda p: p.name == 'receipt.json'): p.unlink()
    path.rmdir()

def read_set(service, path, partial=False):
    children = safe_files(path)
    receipt = path/'receipt.json'
    data = verified(service, json.loads(receipt.read_text()))
    if data.get('version') != 1 or set(data.get('files', {})) != FILES-{'receipt.json'}:
        raise Invalid('Invalid managed backup receipt')
    for name, expected in data['files'].items():
        p = path/name
        if partial and not p.exists(): continue
        if not p.is_file() or sha(p) != expected: raise Invalid('Managed backup checksum failed')
    if not partial and len(children) != 3: raise Invalid('Incomplete managed backup')
    return data

def prune(service, root):
    """Require all retained sets to verify before removing any older managed set."""
    sets=[]; retiring=[]
    for p in root.iterdir():
        if re.fullmatch(NAME, p.name): sets.append(p)
        elif p.name.startswith('.retiring-') and re.fullmatch(NAME, p.name[10:]): retiring.append(p)
    sets.sort(key=lambda p:p.name)
    for p in sets: read_set(service, p)
    for p in retiring:
        if (p/'receipt.json').exists(): read_set(service, p, partial=True)
        elif safe_files(p): raise Invalid('Incomplete retirement receipt')
    removed=0
    for p in retiring: remove_set(p); removed+=1
    for p in sets[:-KEEP]:
        dest=root/('.retiring-'+p.name)
        p.rename(dest); sync_dir(root)
        remove_set(dest); removed+=1
    sync_dir(root)
    return {'retained_sets':min(len(sets),KEEP),'removed_sets':removed,'keep_latest':KEEP,'legacy_backups_untouched':True}

@contextlib.contextmanager
def lock(root):
    plain_dir(root)
    path=root/'.lock'
    fd=os.open(path, os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX)
        yield
    finally: os.close(fd)

def create(store, directory):
    service=MarketingConsent(store);service.sign('backup-readiness')
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True);plain_dir(directory)
    root=directory/'managed-v1'
    root.mkdir(mode=0o700,exist_ok=True);plain_dir(root)
    with lock(root):
        # A fixed staging directory bounds disk consumption even after process death.
        stage=root/'.pending'
        if stage.exists() or stage.is_symlink(): remove_set(stage)
        required=RESERVE + 3*Path(store.path).stat().st_size
        if shutil.disk_usage(root).free < required:
            raise Invalid('Backup paused: less than 5 GiB reserve plus snapshot working space')
        stage.mkdir(mode=0o700)
        published=None
        try:
            database=stage/'growthpilot.db'
            source=sqlite3.connect(store.path);dest=sqlite3.connect(database)
            try:
                source.backup(dest)
                dest.execute('PRAGMA journal_mode=DELETE')
                if dest.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:
                    raise Invalid('Backup integrity check failed')
            finally:dest.close();source.close()
            database.chmod(0o600)
            result=bundle(store,database)
            archive=stage/result['bundle'];archive.chmod(0o600)
            stamp=dt.datetime.now(dt.timezone.utc)
            data={'version':1,'created_at':stamp.isoformat(),'files':{database.name:sha(database),archive.name:sha(archive)}}
            receipt=stage/'receipt.json';receipt.write_text(json.dumps(signed(service,data)));receipt.chmod(0o600)
            read_set(service,stage)
            for p in stage.iterdir():
                with p.open('rb') as f:os.fsync(f.fileno())
            sync_dir(stage)
            name='v1-'+stamp.strftime('%Y%m%d%H%M%S%f')+'-'+uuid.uuid4().hex[:8]
            published=root/name;stage.rename(published);sync_dir(root)
            result.update(file=str((published/database.name).relative_to(directory)),
                          bundle=str((published/archive.name).relative_to(directory)),
                          sha256=data['files'][database.name],integrity='ok')
            # Retention failure must not turn a successfully published backup into
            # an hourly retry. Surface the failure, preserving every suspect set.
            try:result['retention']=dict(status='ok',**prune(service,root))
            except Exception as exc:result['retention']={'status':'blocked','error_type':type(exc).__name__}
            return result
        finally:
            if stage.exists():remove_set(stage)
