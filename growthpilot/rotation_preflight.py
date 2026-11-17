"""Read-only inventory for a separately authorized offline key-generation rollover.

This module never rotates keys, moves backups, or authorizes production cutover.
Recheck the returned manifest after all writers stop and immediately before rollover.
"""
import hashlib,json,os,re,fcntl
from pathlib import Path
from contextlib import contextmanager
from . import backup_maintenance as bm
from .core import Invalid

@contextmanager
def snapshot_lock(root):
    # Existing lock only: preflight must not create any production artifact.
    p=root/'.lock'
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    finally:os.close(fd)

def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def snapshot(directory,service):
    directory=Path(directory);bm.plain_dir(directory)
    root=directory/'managed-v1';bm.plain_dir(root)
    with snapshot_lock(root):
        items=list(root.iterdir())
        if any(p.name!='.lock' and not re.fullmatch(bm.NAME,p.name) for p in items):
            raise Invalid('In-progress or unexpected backup entry; no rotation readiness claim')
        sets=sorted((p for p in items if p.name!='.lock'),key=lambda p:p.name)
        if not sets:raise Invalid('No managed generation to preserve')
        inventory=[]
        for p in sets:
            bm.read_set(service,p)
            inventory.append({'name':p.name,'files':{f.name:{'size':f.stat().st_size,'sha256':bm.sha(f)} for f in sorted(bm.safe_files(p))}})
        payload={'version':1,'generation':'managed-v1','sets':inventory}
        return {'payload':payload,'sha256':fingerprint(payload),'set_count':len(sets),'bytes':sum(f['size'] for row in inventory for f in row['files'].values()),'cutover_authorized':False}

def verify_unchanged(directory,service,expected):
    # Pin to an independently retained digest at execution time; this envelope is not a signature.
    if not isinstance(expected,dict) or set(expected)!={'payload','sha256','set_count','bytes','cutover_authorized'}:
        raise Invalid('Exact preflight envelope required')
    if expected['cutover_authorized'] is not False or fingerprint(expected['payload'])!=expected['sha256']:
        raise Invalid('Invalid preflight digest or authorization claim')
    actual=snapshot(directory,service)
    if actual!=expected:raise Invalid('Backup generation changed; prepare a fresh manifest')
    return True
