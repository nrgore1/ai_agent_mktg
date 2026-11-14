"""One successful backup per UTC day; durable retries and visible health."""
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import tempfile
import time

class DailyBackup:
    def __init__(self,store,directory,clock=None,monotonic=None):
        self.store=store;self.directory=Path(directory)
        self.clock=clock or (lambda:dt.datetime.now(dt.timezone.utc))
        self.monotonic=monotonic or time.monotonic
        self.last_success=None
        self.path=self.directory.parent/('.'+self.directory.name+'-schedule.json')

    def save(self,state):
        fd,name=tempfile.mkstemp(dir=self.path.parent,prefix='.backup-state-')
        try:
            with os.fdopen(fd,'w') as f:json.dump(state,f);f.flush();os.fsync(f.fileno())
            os.replace(name,self.path)
            fd=os.open(self.path.parent,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
        finally:
            if os.path.exists(name):os.unlink(name)

    def tick(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(str(self.path)+'.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd);return {'status':'busy'}
        try:
            current=self.clock().astimezone(dt.timezone.utc);today=current.date().isoformat()
            if self.path.is_symlink():raise ValueError('Unsafe backup schedule state')
            state=json.loads(self.path.read_text()) if self.path.exists() else {}
            self.last_success=state.get('last_success')
            if self.last_success==today:return {'status':'current','health':state.get('status')}
            if current.timestamp()<state.get('retry_after',0):return {'status':'retry_deferred','health':state.get('status')}
            state.update(status='attempting',last_attempt=current.isoformat(),retry_after=current.timestamp()+3600)
            self.save(state)
            try:result=self.store.backup(self.directory)
            except Exception as exc:
                state.update(status='failed',error_type=type(exc).__name__);self.save(state);raise
            self.last_success=today
            retention=result.get('retention',{}) if isinstance(result,dict) else {}
            state.update(last_success=today,last_success_at=current.isoformat(),status='retention_blocked' if retention.get('status')=='blocked' else 'ok',retention=retention)
            state.pop('error_type',None);self.save(state)
            # Persist success before audit: audit failures cannot duplicate the backup.
            try:
                with self.store.db() as db:self.store.audit(db,'daily_backup','system',{'date':today,'retention':retention},'worker')
            except Exception:
                state['status']='audit_failed';self.save(state);raise
            return {'status':'backed_up','result':result}
        finally:os.close(fd)

def health(directory):
    directory=Path(directory);path=directory.parent/('.'+directory.name+'-schedule.json')
    try:
        state=json.loads(path.read_text())
        age=(dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(state['last_success_at'])).total_seconds()/3600 if state.get('last_success_at') else None
        return {'status':state.get('status'),'last_success_at':state.get('last_success_at'),'age_hours':round(age,2) if age is not None else None,'stale':age is None or age>36,'retention':state.get('retention',{})}
    except (OSError,ValueError,KeyError,TypeError):return {'status':'unknown','stale':True}
