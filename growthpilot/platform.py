"""Persistent workflows, evidence, reporting, queues and operational controls."""
import datetime as dt, hashlib, json, os, secrets, sqlite3, uuid
from pathlib import Path
from .core import Store, Invalid, digest, encode, now
from . import providers

def positive(value):
 if type(value) is not int or value<0:raise Invalid('Expected a nonnegative integer')
 return value

class Platform(Store):
 def __init__(self,path):
  super().__init__(path)
  with self.db() as db:
   db.executescript("""CREATE TABLE IF NOT EXISTS deliveries(id TEXT PRIMARY KEY,action_id TEXT UNIQUE,status TEXT,payload_hash TEXT,attempts INTEGER,lease_until TEXT,result TEXT,created_at TEXT);
   CREATE TABLE IF NOT EXISTS ingestion(key TEXT PRIMARY KEY,product_id INTEGER,event_id TEXT);
   CREATE TABLE IF NOT EXISTS api_keys(hash TEXT PRIMARY KEY,product_id INTEGER,name TEXT);
   CREATE TABLE IF NOT EXISTS provider_limits(connector TEXT PRIMARY KEY,next_at TEXT);
   CREATE TABLE IF NOT EXISTS audit_exports(seq INTEGER PRIMARY KEY,hash TEXT);""")
 def snapshot(self,product=None):
  state=super().snapshot(product)
  state['products'].sort(key=lambda p:p['id']);state['channels'].sort(key=lambda c:c['id'])
  with self.db() as db:
   for kind in ('evidence','notifications','suppressions','reports'):state[kind]=self.rows(db,kind,product)
   state['deliveries']=[dict(r) for r in db.execute('SELECT id,action_id,status,payload_hash,attempts,lease_until,created_at FROM deliveries')]
  state['integration_status']={'llm':'configured' if os.environ.get('GROWTHPILOT_OLLAMA_URL') and os.environ.get('GROWTHPILOT_OLLAMA_MODEL') else 'needs_configuration','research':'public_https','github':'configured' if os.environ.get('GROWTHPILOT_GITHUB_TOKEN') else 'needs_configuration','smtp_sandbox':'configured' if os.environ.get('GROWTHPILOT_SMTP_HOST') else 'needs_configuration','live_delivery':os.environ.get('GROWTHPILOT_ENABLE_LIVE')=='true'}
  state['report']=self.report(product)
  return state
 def update(self,kind,id,data,actor='founder'):
  fields={
   'products':{'audience','positioning','pricing','website','landing_page','investor_profile','budget_cents','readiness','targets','channels','approved_claims','claim_evidence'},
   'channels':{'submission_types','eligibility','connector','terms_status','rules_source','rules_summary','verified_at','fees_cents','status','product_ids'},
   'leads':{'name','email','organization','stage','owner','next_followup','consent','source','fit_score','fit_rationale','notes','referral_code','suppressed'},
   'campaigns':{'name','status','budget_cents','owner','start_at','end_at'},
   'experiments':{'name','hypothesis','metric','target','budget_cents','status','decision','result'},
   'schedules':{'status','due_at','recurrence_hours','dependencies'},
   'evidence':{'status','review_note'},
  }
  if kind not in fields or set(data)-fields[kind]:raise Invalid('Unsupported fields for '+kind)
  with self.db() as db:
   row=self.get(db,kind,id)
   if 'budget_cents' in data:positive(data['budget_cents'])
   if kind=='leads' and 'fit_score' in data and (type(data['fit_score']) is not int or not 0<=data['fit_score']<=100):raise Invalid('Fit score must be 0–100')
   if 'recurrence_hours' in data:
    if type(data['recurrence_hours']) is not int or data['recurrence_hours']<1:raise Invalid('Recurrence must be at least one hour')
   if kind=='schedules' and data.get('status') not in (None,'scheduled','cancelled'):raise Invalid('Invalid schedule status')
   for date in ('due_at','next_followup','start_at','end_at'):
    if data.get(date):
     try:parsed=dt.datetime.fromisoformat(data[date])
     except ValueError:raise Invalid('Invalid date '+date)
     if parsed.tzinfo is None:raise Invalid('Timezone required for '+date)
   for url in ('website','landing_page','rules_source'):
    if data.get(url) and not data[url].startswith('https://'):raise Invalid('Public URLs require HTTPS')
   if kind=='evidence' and data.get('status') not in ('verified','rejected','unverified'):raise Invalid('Invalid evidence state')
   if kind=='channels' and data.get('terms_status')=='verified' and not data.get('rules_source',row.get('rules_source')):raise Invalid('Rules source URL required')
   if kind=='products':
    candidate=dict(row,**data)
    if not isinstance(candidate.get('approved_claims'),list):raise Invalid('Claims must be a list')
    for claim in candidate['approved_claims']:
     ids=candidate.get('claim_evidence',{}).get(claim,[])
     if not ids:raise Invalid('Every approved claim needs verified evidence')
     for eid in ids:
      e=self.get(db,'evidence',eid)
      if e.get('product_id')!=row['id'] or e.get('status')!='verified':raise Invalid('Evidence must be verified and belong to product')
   row.update(data,updated_at=now());self.save(db,kind,row);self.audit(db,'update_'+kind,id,{'fields':sorted(data)},actor)
   return row
 def create_record(self,kind,data):
  if kind in ('evidence','suppressions'):
   with self.db() as db:
    p=self.get(db,'products',data.get('product_id'))
    if kind=='evidence':
     if not data.get('source') or not data.get('excerpt'):raise Invalid('Evidence source and excerpt required')
     data=dict(data,status='unverified',confidence='manual_source_pending_review')
    elif not data.get('email'):raise Invalid('Suppression email required')
    row=dict(data,id=uuid.uuid4().hex,product_id=p['id'],created_at=now());self.save(db,kind,row);self.audit(db,'create_'+kind,row['id'],{})
    return row
  if kind=='schedules':
   hours=data.get('recurrence_hours')
   if hours is not None and (type(hours) is not int or hours<1):raise Invalid('Recurrence must be at least one hour')
   if not isinstance(data.get('dependencies',[]),list):raise Invalid('Dependencies must be a list')
  if kind=='experiments':
   if not data.get('hypothesis') or not data.get('metric'):raise Invalid('Experiment hypothesis and metric required')
   positive(data.get('budget_cents',0));data.setdefault('status','planned')
  if kind=='leads':
   if data.get('fit_score') is not None and (type(data['fit_score']) is not int or not 0<=data['fit_score']<=100):raise Invalid('Fit score must be 0–100')
  return super().create_record(kind,data)
 def research(self,product_id,url):
  with self.db() as db:
   if self.paused(db):raise Invalid('System paused')
   self.get(db,'products',product_id)
  evidence=providers.research(url)
  return self.create_record('evidence',dict(evidence,product_id=product_id))
 def generate(self,action_id):
  with self.db() as db:
   if self.paused(db):raise Invalid('System paused')
   a=self.get(db,'actions',action_id);p=self.get(db,'products',a['product_id']);sources=[e for e in self.rows(db,'evidence',p['id']) if e['status']=='verified']
   if not sources:raise Invalid('Verify at least one evidence source before LLM generation')
  result=providers.draft(p,sources,a['payload']['channel'])
  # The provider response is untrusted and cannot approve or execute anything.
  with self.db() as db:
   current=self.get(db,'actions',action_id)
   if current['version']!=a['version']:raise Invalid('Draft changed during generation; retry')
  return self.transition(action_id,'revise',{'content':result['content'],'claims':result['claims'],'evidence':[{'id':e['id'],'source':e['source']} for e in sources]})
 def plan(self,product_id,channel=None,slot=None):
  if slot:
   with self.db() as db:
    old=next((c for c in self.rows(db,'campaigns',product_id) if c.get('schedule_slot')==slot),None)
    if old:return {'campaign':old}
  result=super().plan(product_id,channel,slot)
  with self.db() as db:
   campaign=result['campaign'];p=self.get(db,'products',product_id)
   if slot:campaign['schedule_slot']=slot
   campaign['launch_package']={'title':p['name']+' — founder review','tagline':p['positioning'],'audience':p['audience'],'channel':result['action']['payload']['channel'],'checklist':['Verify platform rules','Use founder-written text where required','Verify claims and product availability','Add screenshots and working demo','Review exact destination and CTA'],'assets':[],'cta':p.get('landing_page'),'utm':campaign['utm']}
   self.save(db,'campaigns',campaign);result['campaign']=campaign
  return result
 def validate(self,db,a):
  # Keep original mock acceptance for backwards-compatible sandbox tests.
  if a['payload'].get('connector')=='mock':return super().validate(db,a)
  p=self.get(db,'products',a['product_id']);payload=a['payload']
  if payload.get('product_id')!=p['id'] or payload.get('campaign_id')!=a['campaign_id']:raise Invalid('Product/campaign mismatch')
  if p.get('readiness')!='verified':raise Invalid('Product readiness must be verified')
  if payload.get('cost_cents')!=0:raise Invalid('Paid provider actions are not enabled')
  if payload.get('connector') not in ('github','smtp_sandbox'):raise Invalid('Unsupported connector')
  if payload.get('kind') not in ('publish','outreach') or not payload.get('title') or not payload.get('content'):raise Invalid('Title and content required')
  if not payload.get('claims_reviewed'):raise Invalid('Founder must explicitly review free-text claims')
  if not payload.get('claims') or any(c not in p.get('approved_claims',[]) for c in payload['claims']):raise Invalid('Only verified approved product claims allowed')
  if not payload.get('evidence'):raise Invalid('Evidence required')
  ids={e.get('id') for e in payload['evidence'] if isinstance(e,dict)}
  for eid in ids:
   evidence=self.get(db,'evidence',eid)
   if evidence['status']!='verified' or evidence['product_id']!=p['id']:raise Invalid('Payload evidence must be verified for this product')
  for claim in payload['claims']:
   required=p.get('claim_evidence',{}).get(claim,[])
   if not required or not set(required).issubset(ids):raise Invalid('Every claim source must be included in the exact payload')
   for eid in required:
    evidence=self.get(db,'evidence',eid)
    if evidence['status']!='verified' or evidence['product_id']!=p['id']:raise Invalid('Claim evidence no longer valid')
  channel=next((c for c in self.rows(db,'channels') if c['domain']==payload.get('channel')),None)
  if not channel or channel.get('terms_status')!='verified':raise Invalid('Channel rules must be verified')
  if payload['connector']=='github':
   repo=os.environ.get('GROWTHPILOT_GITHUB_REPO','')
   if payload.get('destination')!='https://github.com/'+repo+'/issues' or not repo:raise Invalid('Destination not configured GitHub issues repository')
  if payload['connector']=='smtp_sandbox':
   lead=self.get(db,'leads',payload.get('lead_id'))
   if lead['product_id']!=p['id'] or lead.get('email')!=payload.get('recipient') or lead.get('consent')!='opt_in':raise Invalid('Recipient consent and product match required')
   suppressed=lead.get('suppressed') or any(s['email'].lower()==lead['email'].lower() for s in self.rows(db,'suppressions'))
   if suppressed:raise Invalid('Recipient suppressed')
   if payload.get('recipient')!=os.environ.get('GROWTHPILOT_TEST_RECIPIENT'):raise Invalid('Only configured sandbox recipient allowed')
 def external_action(self,data):
  allowed={'product_id','campaign_id','connector','kind','channel','destination','account','recipient','content','title','claims','evidence','lead_id','claims_reviewed'}
  if set(data)-allowed:raise Invalid('Unexpected external action field')
  with self.db() as db:
   p=self.get(db,'products',data.get('product_id'));c=self.get(db,'campaigns',data.get('campaign_id'))
   if c['product_id']!=p['id']:raise Invalid('Campaign/product mismatch')
   payload=dict(data,cost_cents=0);a=dict(id=uuid.uuid4().hex,product_id=p['id'],campaign_id=c['id'],payload=payload,payload_hash=digest(payload),version=1,status='pending',approval=None,created_at=now(),receipt=None)
   self.validate(db,a);self.save(db,'actions',a);self.audit(db,'external_draft',a['id'],{'hash':a['payload_hash']});return a
 def transition(self,id,command,data):
  if command=='comment':
   with self.db() as db:
    a=self.get(db,'actions',id);a.setdefault('comments',[]).append({'at':now(),'text':str(data.get('text',''))[:2000]});self.save(db,'actions',a);self.audit(db,'comment',id,{});return a
  with self.db() as db:a=self.get(db,'actions',id)
  if a['status'] in ('queued','executing','unknown') and command in ('revise','reject','approve'):raise Invalid('Queued delivery must be reconciled before revision')
  if command!='execute' or a['payload'].get('connector')=='mock':return super().transition(id,command,data)
  return self.enqueue(id)
 def enqueue(self,id):
  with self.db() as db:
   if self.paused(db):raise Invalid('System paused')
   a=self.get(db,'actions',id);self.validate(db,a)
   if a['status'] in ('queued','executed','executing','unknown'):return a
   approval=a.get('approval')
   if a['status']!='approved' or not approval or approval['hash']!=digest(a['payload']) or approval['version']!=a['version'] or dt.datetime.fromisoformat(approval['expires_at'])<=dt.datetime.now(dt.timezone.utc):raise Invalid('Valid exact action approval required')
   db.execute('INSERT INTO deliveries VALUES(?,?,?,?,?,?,?,?)',(uuid.uuid4().hex,id,'queued',a['payload_hash'],0,None,None,now()))
   a['status']='queued';self.save(db,'actions',a);self.audit(db,'queued',id,{'hash':a['payload_hash']});return a
 def process_delivery(self):
  current=dt.datetime.now(dt.timezone.utc)
  with self.db() as db:
   # Never blindly replay a possibly delivered network request after a crash.
   stale=db.execute("SELECT * FROM deliveries WHERE status='executing' AND lease_until<?",(now(),)).fetchall()
   for d in stale:
    db.execute("UPDATE deliveries SET status='unknown' WHERE id=?",(d['id'],));a=self.get(db,'actions',d['action_id']);a['status']='unknown';self.save(db,'actions',a);self.audit(db,'delivery_unknown',a['id'],{})
   if self.paused(db):return
   row=db.execute("SELECT * FROM deliveries WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
   if not row:return
   a=self.get(db,'actions',row['action_id'])
   try:
    self.validate(db,a)
    if not a.get('approval') or a['approval']['hash']!=digest(a['payload']) or dt.datetime.fromisoformat(a['approval']['expires_at'])<=current:raise Invalid('Approval invalid or expired')
   except Invalid as e:
    db.execute("UPDATE deliveries SET status='blocked',result=? WHERE id=?",(encode({'error':str(e)}),row['id']));a['status']='blocked';self.save(db,'actions',a);return
   connector=a['payload']['connector'];limit=db.execute('SELECT next_at FROM provider_limits WHERE connector=?',(connector,)).fetchone()
   if limit and dt.datetime.fromisoformat(limit[0])>current:return
   db.execute('INSERT OR REPLACE INTO provider_limits VALUES(?,?)',(connector,(current+dt.timedelta(seconds=60)).isoformat()))
   db.execute("UPDATE deliveries SET status='executing',attempts=attempts+1,lease_until=? WHERE id=?",((current+dt.timedelta(minutes=3)).isoformat(),row['id']))
   a['status']='executing';self.save(db,'actions',a)
  try:
   # Check pause again immediately before the side effect. An already in-flight call cannot be recalled.
   with self.db() as db:
    if self.paused(db):raise Invalid('Paused before provider call')
   receipt=providers.deliver(a['payload'],row['id']);status='executed'
  except Exception:
   receipt={'error':'Provider outcome unconfirmed; reconcile before any retry'};status='unknown'
  with self.db() as db:
   a=self.get(db,'actions',a['id']);a['status']=status;a['receipt']=dict(receipt,at=now(),payload_hash=a['payload_hash'],idempotency_key=row['id']);self.save(db,'actions',a)
   db.execute('UPDATE deliveries SET status=?,result=? WHERE id=?',(status,encode(a['receipt']),row['id']));self.audit(db,'delivery_result',a['id'],{'status':status})
 def report(self,product=None):
  with self.db() as db:
   events=[e for e in self.rows(db,'events',product) if e.get('source')=='actual'];products=self.rows(db,'products');leads=self.rows(db,'leads',product);campaigns=self.rows(db,'campaigns',product)
  funnel={};attribution={}
  for e in events:
   metric=e.get('type','unknown');funnel[metric]=funnel.get(metric,0)+e.get('count',0)
   source=e.get('utm_source','unattributed');bucket=attribution.setdefault(source,{'events':0,'revenue_cents':0,'cost_cents':0,'paid':0});bucket['events']+=e.get('count',0);bucket['revenue_cents']+=e.get('revenue_cents',0);bucket['cost_cents']+=e.get('cost_cents',0);bucket['paid']+=e.get('count',0) if metric=='paid' else 0
  revenue=sum(e.get('revenue_cents',0) for e in events);cost=sum(e.get('cost_cents',0) for e in events);paid=funnel.get('paid',0);trials=funnel.get('trial',0)
  return {'as_of':now(),'funnel':funnel,'revenue_cents':revenue,'cost_cents':cost,'cac_cents':round(cost/paid) if paid else None,'trial_to_paid_rate':paid/trials if trials else None,'attribution':attribution,'targets':[{'product_id':p['id'],'name':p['name'],'targets':p['targets']} for p in products if product is None or p['id']==product],'overdue_followups':[l['id'] for l in leads if l.get('next_followup') and l['next_followup']<now()],'budgets':[{'campaign_id':c['id'],'limit_cents':c.get('budget_cents',0),'actual_cost_cents':sum(e.get('cost_cents',0) for e in events if e.get('campaign_id')==c['id'])} for c in campaigns],'note':'Actuals reflect ingested records. Targets and mock executions are excluded.'}
 def ingest_key(self,product_id,name):
  raw=secrets.token_urlsafe(40)
  with self.db() as db:
   self.get(db,'products',product_id);db.execute('INSERT INTO api_keys VALUES(?,?,?)',(hashlib.sha256(raw.encode()).hexdigest(),product_id,name));self.audit(db,'ingest_key_created',product_id,{'name':name})
  return {'key':raw,'product_id':product_id}
 def ingest(self,key,data):
  event_key=data.get('idempotency_key')
  if not isinstance(event_key,str) or not event_key or len(event_key)>160:raise Invalid('Idempotency key required')
  with self.db() as db:
   row=db.execute('SELECT product_id FROM api_keys WHERE hash=?',(hashlib.sha256(key.encode()).hexdigest(),)).fetchone()
   if not row:raise Invalid('Invalid analytics key')
   p=row[0];scope=str(p)+':'+event_key
   if data.get('product_id',p)!=p:raise Invalid('Analytics key product mismatch')
   old=db.execute('SELECT event_id FROM ingestion WHERE key=?',(scope,)).fetchone()
   if old:return {'event_id':old[0],'duplicate':True}
   event={k:v for k,v in data.items() if k in ('type','count','revenue_cents','cost_cents','utm_source','utm_medium','utm_campaign','campaign_id','occurred_at')}
   if not event.get('type'):raise Invalid('Event type required')
   for k in ('count','revenue_cents','cost_cents'):positive(event.get(k,0))
   if event.get('campaign_id') and self.get(db,'campaigns',event['campaign_id'])['product_id']!=p:raise Invalid('Campaign product mismatch')
   event.update(id=uuid.uuid4().hex,product_id=p,source='actual',created_at=now());self.save(db,'events',event);db.execute('INSERT INTO ingestion VALUES(?,?,?)',(scope,p,event['id']));self.audit(db,'analytics_ingested',event['id'],{'product_id':p},'ingestion');return {'event_id':event['id'],'duplicate':False}
 def tick(self):
  current=dt.datetime.now(dt.timezone.utc)
  with self.db() as db:
   if self.paused(db):return {'paused':True,'processed':0}
   due=[]
   for s in self.rows(db,'schedules'):
    if s['status']=='running' and s.get('lease_until','')<now():s['status']='retry';self.save(db,'schedules',s)
    if s['status'] not in ('scheduled','retry') or dt.datetime.fromisoformat(s['due_at'])>current:continue
    dependencies=s.get('dependencies',[])
    if any(self.get(db,'schedules',d)['status']!='completed' for d in dependencies):continue
    s.update(status='running',lease_until=(current+dt.timedelta(minutes=5)).isoformat());self.save(db,'schedules',s);due.append(s)
  for s in due:
   try:
    result=self.plan(s['product_id'],s.get('channel'),s['id']+':'+s['due_at']);s.update(status='completed',campaign_id=result['campaign']['id'],attempts=0)
    if s.get('recurrence_hours'):s.update(status='scheduled',due_at=(current+dt.timedelta(hours=s['recurrence_hours'])).isoformat())
   except Exception:
    s['attempts']+=1;s.update(status='failed' if s['attempts']>=s['max_attempts'] else 'retry',error='Draft preparation failed; check channel and product configuration',due_at=(current+dt.timedelta(minutes=2**s['attempts'])).isoformat())
   with self.db() as db:self.save(db,'schedules',s);self.audit(db,'schedule_result',s['id'],{'status':s['status']},'worker')
  self.process_delivery()
  return {'processed':len(due)}
 def verify_audit(self):
  previous='';count=0
  with self.db() as db:
   for row in db.execute('SELECT * FROM audit ORDER BY seq'):
    entry={k:row[k] for k in ('at','actor','event','entity','previous')};entry['details']=json.loads(row['details'])
    if row['previous']!=previous or digest(entry)!=row['hash']:return {'valid':False,'seq':row['seq']}
    previous=row['hash'];count+=1
  return {'valid':True,'entries':count,'head':previous}
 def backup(self,directory):
  directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
  target=directory/('growthpilot-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')+'.db')
  source=sqlite3.connect(self.path);dest=sqlite3.connect(target)
  try:source.backup(dest)
  finally:dest.close();source.close()
  os.chmod(target,0o600)
  with sqlite3.connect(target) as restored:
   if restored.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise Invalid('Backup integrity check failed')
  return {'file':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'integrity':'ok'}
