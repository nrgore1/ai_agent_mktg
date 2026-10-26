import contextlib, datetime as dt, hashlib, json, sqlite3, uuid
from pathlib import Path

AGENTS=['Market Intelligence','Content and SEO','Launch and Directory','Customer Acquisition','Investor Research','Partnerships and Champions','Analytics and Optimization','Compliance and Evidence']
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def encode(v): return json.dumps(v,sort_keys=True,separators=(',',':'))
def digest(v): return hashlib.sha256(encode(v).encode()).hexdigest()
class Invalid(ValueError): pass

class Store:
 def __init__(self,path):
  self.path=str(path)
  with self.db() as db:
   db.executescript("""
   CREATE TABLE IF NOT EXISTS records(kind TEXT,id TEXT,product_id INTEGER,data TEXT NOT NULL,PRIMARY KEY(kind,id));
   CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT,at TEXT,actor TEXT,event TEXT,entity TEXT,details TEXT,previous TEXT,hash TEXT);
   CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
   INSERT OR IGNORE INTO settings VALUES('paused','false');
   """)
   seeds=json.loads(Path(__file__).with_name('registry.json').read_text())
   for kind,rows in seeds.items():
    for row in rows: db.execute('INSERT OR IGNORE INTO records VALUES(?,?,?,?)',(kind,str(row['id']),row['id'] if kind=='products' else None,encode(row)))
 @contextlib.contextmanager
 def db(self):
  db=sqlite3.connect(self.path,timeout=30,isolation_level=None); db.row_factory=sqlite3.Row
  db.execute('PRAGMA foreign_keys=ON'); db.execute('PRAGMA journal_mode=WAL'); db.execute('BEGIN IMMEDIATE')
  try: yield db; db.commit()
  except: db.rollback(); raise
  finally: db.close()
 def rows(self,db,kind,product=None):
  return [json.loads(r[0]) for r in db.execute('SELECT data FROM records WHERE kind=?'+(' AND product_id=?' if product is not None else ''), (kind,product) if product is not None else (kind,))]
 def get(self,db,kind,id):
  r=db.execute('SELECT data FROM records WHERE kind=? AND id=?',(kind,str(id))).fetchone()
  if not r: raise Invalid('Record not found')
  return json.loads(r[0])
 def save(self,db,kind,row):
  db.execute('INSERT INTO records VALUES(?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET data=excluded.data,product_id=excluded.product_id',(kind,str(row['id']),row.get('product_id'),encode(row)))
 def audit(self,db,event,entity,details,actor='founder'):
  previous=db.execute('SELECT hash FROM audit ORDER BY seq DESC LIMIT 1').fetchone(); previous=previous[0] if previous else ''
  entry=dict(at=now(),actor=actor,event=event,entity=str(entity),details=details,previous=previous)
  db.execute('INSERT INTO audit(at,actor,event,entity,details,previous,hash) VALUES(?,?,?,?,?,?,?)',(entry['at'],actor,event,str(entity),encode(details),previous,digest(entry)))
 def paused(self,db): return db.execute("SELECT value FROM settings WHERE key='paused'").fetchone()[0]=='true'
 def pause(self,value):
  if not isinstance(value,bool): raise Invalid('paused must be boolean')
  with self.db() as db:
   db.execute("UPDATE settings SET value=? WHERE key='paused'",(encode(value),)); self.audit(db,'pause','system',value)
  return {'paused':value}
 def snapshot(self,product=None):
  with self.db() as db:
   result={k:self.rows(db,k,product if k not in ('products','channels') else None) for k in ['products','channels','campaigns','actions','leads','events','experiments','schedules','jobs']}
   result['paused']=self.paused(db); result['agents']=AGENTS
   result['audit']=[dict(r) for r in db.execute('SELECT * FROM audit ORDER BY seq DESC LIMIT 100')]
   events=result['events']; actions=result['actions']
   result['metrics']={'mock_executions':sum(a['status']=='executed' for a in actions),'actual_conversions':sum(e.get('count',0) for e in events if e.get('type')=='paid' and e.get('source')=='actual'),'actual_revenue_cents':sum(e.get('revenue_cents',0) for e in events if e.get('source')=='actual'),'leads':len(result['leads'])}
   return result
 def create_record(self,kind,data):
  if kind not in ('leads','events','experiments','schedules'): raise Invalid('Unsupported record type')
  with self.db() as db:
   product=self.get(db,'products',data.get('product_id')); data=dict(data,product_id=product['id'])
   if kind=='leads':
    if data.get('pipeline') not in ('customer','institutional','investor','partner','champion'): raise Invalid('Invalid pipeline')
    if not data.get('name'): raise Invalid('Lead name required')
    data.setdefault('stage','research'); data.setdefault('consent','unknown')
   if kind=='events':
    if data.get('source') not in ('actual','simulation'): raise Invalid('Specify actual or simulation')
    if not data.get('type'): raise Invalid('Event type required')
    for field in ('count','revenue_cents','cost_cents'):
     value=data.get(field,0)
     if type(value) is not int or value<0: raise Invalid('Metrics must be nonnegative integers')
   if kind=='schedules':
    try: due=dt.datetime.fromisoformat(data['due_at'])
    except (KeyError,ValueError): raise Invalid('Valid due_at required')
    if due.tzinfo is None: raise Invalid('due_at requires timezone')
    data.update(status='scheduled',attempts=0,max_attempts=3)
   data.update(id=uuid.uuid4().hex,created_at=now()); self.save(db,kind,data); self.audit(db,'create',data['id'],{'kind':kind})
   return data
 def plan(self,product_id,channel=None,slot=None):
  with self.db() as db:
   if self.paused(db): raise Invalid('System paused')
   p=self.get(db,'products',product_id); channel=channel or p['channels'][0]
   if slot:
    existing=next((c for c in self.rows(db,'campaigns',product_id) if c.get('schedule_slot')==slot),None)
    if existing:return {'campaign':existing,'action':next(a for a in self.rows(db,'actions',product_id) if a['campaign_id']==existing['id'])}
   if channel not in [c['domain'] for c in self.rows(db,'channels')]: raise Invalid('Unknown channel')
   cid=uuid.uuid4().hex
   campaign=dict(id=cid,product_id=p['id'],name=p['name']+' — 90-day validation',created_at=now(),status='draft',targets=p['targets'],budget_cents=p['budget_cents'],phases=[{'days':'1–30','goal':'Readiness, interviews and evidence'},{'days':'31–60','goal':'Approved launches and acquisition'},{'days':'61–90','goal':'Retention, pilots and channel optimization'}],utm={'utm_source':channel,'utm_medium':'community','utm_campaign':cid},provider='deterministic_mock',confidence='hypothesis',evidence=[{'source':'registry.json','note':'User supplied strategy; not independently verified'}])
   if slot:campaign['schedule_slot']=slot
   self.save(db,'campaigns',campaign)
   payload=dict(product_id=p['id'],campaign_id=cid,kind='manual_submission',channel=channel,destination='https://'+channel,recipient=None,account='mock-founder',content=f"Founder review draft: We are exploring {p['name']} for {p['audience']}. We welcome feedback on the problem and a conversation about your needs. Product availability, pricing and capabilities require founder verification.",claims=[],evidence=campaign['evidence'],connector='mock',cost_cents=0)
   action=dict(id=uuid.uuid4().hex,product_id=p['id'],campaign_id=cid,payload=payload,payload_hash=digest(payload),version=1,status='pending',approval=None,created_at=now(),receipt=None)
   self.save(db,'actions',action)
   for agent in AGENTS:
    job=dict(id=uuid.uuid4().hex,product_id=p['id'],campaign_id=cid,agent=agent,status='completed',provider='deterministic_mock',output='Prepared strategy-derived review package; no live research or external contact.',evidence=campaign['evidence'],confidence='requires_verification',version=1)
    self.save(db,'jobs',job)
   self.audit(db,'plan',cid,{'action_id':action['id']},'orchestrator'); return {'campaign':campaign,'action':action}
 def validate(self,db,a):
  p=self.get(db,'products',a['product_id']); payload=a['payload']
  if payload['product_id']!=a['product_id'] or payload['campaign_id']!=a['campaign_id']: raise Invalid('Cross-product or campaign mismatch')
  if any(c not in p['approved_claims'] for c in payload.get('claims',[])): raise Invalid('Unsupported product claim')
  if not payload.get('evidence') or not payload.get('content','').strip(): raise Invalid('Content and evidence required')
  channels=self.rows(db,'channels')
  if not any(c['domain']==payload.get('channel') and c['url']==payload.get('destination') for c in channels): raise Invalid('Destination must match registered channel')
  if payload.get('connector')!='mock' or payload.get('cost_cents')!=0: raise Invalid('Only zero-cost mock execution enabled')
  if payload.get('kind')!='manual_submission' or payload.get('recipient') is not None or payload.get('account')!='mock-founder': raise Invalid('Unsupported external action')
 def transition(self,id,command,data):
  with self.db() as db:
   a=self.get(db,'actions',id)
   if command=='revise':
    if a['status']=='executed': raise Invalid('Executed action is immutable')
    allowed={'content','claims','evidence','channel','destination'}
    if set(data)-allowed: raise Invalid('Unsupported payload edit')
    a['payload'].update(data); a.update(version=a['version']+1,status='pending',approval=None,payload_hash=digest(a['payload']))
   elif command=='reject':
    if a['status']=='executed': raise Invalid('Already executed')
    a.update(status='rejected',approval=None)
   elif command=='approve':
    if self.paused(db): raise Invalid('System paused')
    if a['status']!='pending': raise Invalid('Only pending actions can be approved')
    self.validate(db,a)
    if data.get('payload_hash')!=a['payload_hash']: raise Invalid('Stale preview; reload exact payload')
    a.update(status='approved',approval={'hash':a['payload_hash'],'version':a['version'],'actor':'founder','expires_at':(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=24)).isoformat()})
   elif command=='execute':
    if self.paused(db): raise Invalid('System paused')
    if a['status']=='executed': return a
    if a['status']!='approved' or not a['approval']: raise Invalid('Exact action approval required')
    if a['approval']['hash']!=digest(a['payload']) or a['approval']['version']!=a['version']: raise Invalid('Approval invalidated by edit')
    if dt.datetime.fromisoformat(a['approval']['expires_at'])<=dt.datetime.now(dt.timezone.utc): raise Invalid('Approval expired')
    self.validate(db,a)
    # Transaction serializes executions. The mock makes no network calls.
    if data.get('simulate_failure'): raise Invalid('Mock connector failed; no success recorded')
    a.update(status='executed',receipt={'id':uuid.uuid4().hex,'at':now(),'mode':'mock','idempotency_key':a['id']+':'+str(a['version']),'payload_hash':a['payload_hash'],'external_delivery':False})
    self.save(db,'events',dict(id=uuid.uuid4().hex,product_id=a['product_id'],campaign_id=a['campaign_id'],type='mock_execution',source='simulation',count=1,created_at=now()))
   else: raise Invalid('Unknown transition')
   self.save(db,'actions',a); self.audit(db,command,id,{'hash':a['payload_hash'],'version':a['version'],'status':a['status']}); return a
 def tick(self):
  with self.db() as db:
   if self.paused(db): return {'paused':True,'processed':0}
   due=[s for s in self.rows(db,'schedules') if s['status'] in ('scheduled','retry') and dt.datetime.fromisoformat(s['due_at'])<=dt.datetime.now(dt.timezone.utc)]
   # Claim work transactionally before generating drafts; crash leaves an inspectable running record.
   for s in due: s['status']='running'; self.save(db,'schedules',s)
  for s in due:
   try:
    result=self.plan(s['product_id'],s.get('channel')); s.update(status='completed',campaign_id=result['campaign']['id'])
   except Exception as e:
    s['attempts']+=1; s.update(status='failed' if s['attempts']>=s['max_attempts'] else 'retry',error=str(e),due_at=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=2**s['attempts'])).isoformat())
   with self.db() as db: self.save(db,'schedules',s); self.audit(db,'schedule_result',s['id'],{'status':s['status']},'worker')
  return {'processed':len(due)}
