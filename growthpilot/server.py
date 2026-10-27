"""Same-origin authenticated API and local console."""
import argparse, datetime as dt, hmac, json, logging, os, threading, time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from .core import Invalid, now
from .platform import Platform
from .identity import Identity

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--port',type=int,default=8098);args=parser.parse_args()
 path=Path(os.environ.get('GROWTHPILOT_DB','data/growthpilot.db'));path.parent.mkdir(parents=True,exist_ok=True)
 store=Platform(path);identity=Identity(store);identity.bootstrap(path.parent)
 secure=os.environ.get('GROWTHPILOT_SECURE_COOKIE')=='true'
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def send(self,status,obj,ctype='application/json',cookie=None):
   body=json.dumps(obj).encode() if ctype=='application/json' else obj
   self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.send_header('Referrer-Policy','no-referrer');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
   if cookie:self.send_header('Set-Cookie',cookie)
   self.end_headers();self.wfile.write(body)
  def raw_session(self):
   try:
    cookie=SimpleCookie(self.headers.get('Cookie',''));return cookie['gp_session'].value if 'gp_session' in cookie else ''
   except Exception:return ''
  def user(self):return identity.session(self.raw_session())
  def allowed(self,user,product_id):
   return user['role'] in ('founder','admin') or product_id in user['products']
  def readable_state(self,user):
   state=store.snapshot()
   if user['role'] not in ('founder','admin'):
    ids=user['products'];state['products']=[p for p in state['products'] if p['id'] in ids]
    for key in ('campaigns','actions','leads','events','experiments','schedules','jobs','evidence','notifications','suppressions','reports'):state[key]=[r for r in state[key] if r.get('product_id') in ids]
    state['launch_desk']={}
    state['audit']=[];state['deliveries']=[];state['report']={};state['metrics']={}
   return state
  def origin_ok(self):
   origin=self.headers.get('Origin')
   return not origin or urlsplit(origin).netloc==self.headers.get('Host')
  def do_GET(self):
   path=urlsplit(self.path).path
   if path=='/health':return self.send(200,{'status':'ok','mode':'approval-governed','version':'0.4.0'})
   assets={'/':'index.html','/app.js':'app.js','/style.css':'style.css','/console.js':'console.js','/roadmap.js':'roadmap.js','/launchdesk.js':'launchdesk.js','/strategyos.js':'strategyos.js'}
   if path in assets:
    ctype='text/html; charset=utf-8' if path=='/' else 'text/css' if path.endswith('.css') else 'text/javascript'
    return self.send(200,(Path(__file__).parent/'static'/assets[path]).read_bytes(),ctype)
   user=self.user()
   if not user:return self.send(401,{'error':'Sign in required'})
   try:
    if path=='/api/strategy':
     if user['role'] not in ('founder','admin'):return self.send(403,{'error':'Administrator required for product economics'})
     from .economics import StrategyOS
     return self.send(200,StrategyOS(store).overview())
    if path=='/api/me':return self.send(200,user)
    if path=='/api/state':return self.send(200,self.readable_state(user))
    if path=='/api/report':
     q=parse_qs(urlsplit(self.path).query);p=int(q['product_id'][0]) if 'product_id' in q else None
     if (p is None and user['role'] not in ('founder','admin')) or (p is not None and not self.allowed(user,p)):return self.send(403,{'error':'Product access denied'})
     return self.send(200,store.report(p))
    if path=='/api/users' and user['role'] in ('founder','admin'):return self.send(200,identity.users())
    if path=='/api/audit/verify' and user['role'] in ('founder','admin'):return self.send(200,store.verify_audit())
    return self.send(404,{'error':'Not found'})
   except (Invalid,ValueError):return self.send(400,{'error':'Invalid request'})
  def do_POST(self):
   if not self.origin_ok():return self.send(403,{'error':'Origin rejected'})
   try:
    size=int(self.headers.get('Content-Length','0'))
    if size<0 or size>262144:return self.send(413,{'error':'Request too large'})
    data=json.loads(self.rfile.read(size) or '{}')
    if not isinstance(data,dict):raise Invalid('JSON object required')
    path=urlsplit(self.path).path;parts=path.strip('/').split('/')
    if path=='/api/login':
     session=identity.login(str(data.get('username',''))[:80],str(data.get('password',''))[:1024],self.client_address[0])
     if not session:return self.send(401,{'error':'Invalid username or password'})
     raw=session.pop('session');return self.send(200,session,cookie='gp_session='+raw+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800'+('; Secure' if secure else ''))
    if path=='/api/ingest':
     key=self.headers.get('Authorization','').removeprefix('Bearer ')
     return self.send(200,store.ingest(key,data))
    user=self.user()
    if not user:return self.send(401,{'error':'Sign in required'})
    if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),user['csrf']):return self.send(403,{'error':'CSRF validation failed'})
    if path=='/api/logout':
     identity.logout(self.raw_session());return self.send(200,{'ok':True},cookie='gp_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
    if path=='/api/password':
     identity.change_password(user['username'],data.get('old',''),data.get('new',''));return self.send(200,{'ok':True,'sign_in_again':True},cookie='gp_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
    if user['role']=='viewer':return self.send(403,{'error':'Read-only account'})
    admin=user['role'] in ('founder','admin')
    if path in ('/api/pause','/api/tick','/api/users','/api/backup','/api/keys','/api/actions/batch','/api/roadmap','/api/manager/prepare','/api/manager/review','/api/manager/outreach','/api/manager/record') and not admin:return self.send(403,{'error':'Administrator required'})
    if len(parts)==4 and parts[:2]==['api','actions']:
     with store.db() as db:record=store.get(db,'actions',parts[2])
     if not self.allowed(user,record['product_id']):return self.send(403,{'error':'Product access denied'})
     if parts[3] in ('approve','execute','reject','export','record_submission') and not admin:return self.send(403,{'error':'Founder/admin approval required'})
    if len(parts)==4 and parts[:2]==['api','records']:
     kind=parts[2]
     with store.db() as db:record=store.get(db,kind,parts[3])
     product=record.get('product_id',record['id'] if kind=='products' else None)
     if kind in ('products','channels','evidence') and not admin:return self.send(403,{'error':'Administrator verification required'})
     if product is not None and not self.allowed(user,product):return self.send(403,{'error':'Product access denied'})
    if 'product_id' in data and not self.allowed(user,data['product_id']):return self.send(403,{'error':'Product access denied'})
    if path in ('/api/strategy/run','/api/strategy/financials'):
     if not admin:return self.send(403,{'error':'Administrator required for product economics'})
     from .economics import StrategyOS
     engine=StrategyOS(store)
     if path.endswith('/run'):
      if set(data)-{'product_id','inputs'}:raise Invalid('Unsupported analysis request')
      result=engine.run(data.get('product_id'),data.get('inputs'),user['username'])
     else:result=engine.import_financials(data,user['username'])
    elif path=='/api/manager/prepare':result=store.manager().prepare(user['username'])
    elif path=='/api/manager/review':result=store.manager().review(user['username'])
    elif path=='/api/manager/outreach':result=store.manager().outreach(data.get('lead_id'),user['username'])
    elif path=='/api/manager/record':result=store.manager().activity_record(data.get('kind'),data.get('record',{}),user['username'])
    elif path=='/api/plan':result=store.plan(data.get('product_id'),data.get('channel'))
    elif path=='/api/roadmap':result=store.update_roadmap(data,user['username'])
    elif path=='/api/pause':result=store.pause(data.get('paused'))
    elif path=='/api/tick':result=store.tick()
    elif path=='/api/research':result=store.research(data.get('product_id'),data.get('url',''))
    elif path=='/api/external-action':
     if not admin:return self.send(403,{'error':'Administrator required'})
     result=store.external_action(data)
    elif path=='/api/keys':result=store.ingest_key(data.get('product_id'),data.get('name','analytics'))
    elif path=='/api/backup':result=store.backup(pathlib_backup(path))
    elif path=='/api/users':result=identity.create(data.get('username',''),data.get('password',''),data.get('role','operator'),data.get('products',[]))
    elif path=='/api/actions/batch':
     items=data.get('items',[])
     if not isinstance(items,list) or not 1<=len(items)<=20:raise Invalid('Batch must contain 1–20 explicit actions and hashes')
     result=[]
     for item in items:
      try:result.append({'id':item['id'],'result':store.transition(item['id'],'approve',{'payload_hash':item['payload_hash']},actor=user['username'])})
      except Invalid as e:result.append({'id':item.get('id'),'error':str(e)})
    elif len(parts)==4 and parts[:2]==['api','actions']:
     result=store.generate(parts[2]) if parts[3]=='generate' else store.transition(parts[2],parts[3],data,actor=user['username'])
    elif len(parts)==4 and parts[:2]==['api','records']:result=store.update(parts[2],parts[3],data,user['username'])
    elif len(parts)==2 and parts[0]=='api':result=store.create_record(parts[1],data)
    else:return self.send(404,{'error':'Not found'})
    with store.db() as db:store.audit(db,'api_request',path,{'method':'POST'},user['username'])
    return self.send(200,result)
   except (Invalid,ValueError,TypeError,KeyError) as e:return self.send(400,{'error':str(e)})
   except Exception:
    logging.exception('API operation failed');return self.send(500,{'error':'Operation not confirmed; inspect server logs'})
 def pathlib_backup(unused):return path.parent/'backups'
 def worker():
  last_backup=''
  while True:
   try:
    store.tick()
    today=dt.datetime.now(dt.timezone.utc).date().isoformat()
    if today!=last_backup:
     store.backup(path.parent/'backups');last_backup=today
     with store.db() as db:store.audit(db,'daily_backup','system',{'date':today},'worker')
   except Exception:logging.exception('Background workflow failed')
   time.sleep(15)
 threading.Thread(target=worker,daemon=True).start()
 print(f'GrowthPilot: http://{args.host}:{args.port}; initial credentials stored beside database',flush=True)
 ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()
if __name__=='__main__':main()
