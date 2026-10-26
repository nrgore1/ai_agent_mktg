import argparse, hmac, json, os, secrets, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from .core import Store, Invalid

def main():
 parser=argparse.ArgumentParser(); parser.add_argument('--host',default='127.0.0.1'); parser.add_argument('--port',type=int,default=8098); args=parser.parse_args()
 token=os.environ.get('GROWTHPILOT_API_TOKEN')
 if not token or len(token)<24: raise SystemExit('Set GROWTHPILOT_API_TOKEN to a random secret of at least 24 characters')
 path=Path(os.environ.get('GROWTHPILOT_DB','data/growthpilot.db')); path.parent.mkdir(parents=True,exist_ok=True); store=Store(path)
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args): pass
  def send(self,status,obj,ctype='application/json'):
   body=json.dumps(obj).encode() if ctype=='application/json' else obj
   self.send_response(status); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('X-Frame-Options','DENY'); self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'"); self.end_headers(); self.wfile.write(body)
  def auth(self): return hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+token)
  def do_GET(self):
   u=urlsplit(self.path)
   if u.path=='/health': return self.send(200,{'status':'ok','mode':'mock'})
   if u.path in ('/','/app.js','/style.css'):
    name={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[u.path]
    return self.send(200,(Path(__file__).parent/'static'/name).read_bytes(),{'/':'text/html; charset=utf-8','/app.js':'text/javascript','/style.css':'text/css'}[u.path])
   if not self.auth(): return self.send(401,{'error':'Authentication required'})
   if u.path=='/api/state':
    try:
     query=parse_qs(u.query); product=int(query['product_id'][0]) if 'product_id' in query else None
     return self.send(200,store.snapshot(product))
    except ValueError: return self.send(400,{'error':'Invalid product filter'})
   self.send(404,{'error':'Not found'})
  def do_POST(self):
   if not self.auth(): return self.send(401,{'error':'Authentication required'})
   origin=self.headers.get('Origin')
   if origin and urlsplit(origin).netloc!=self.headers.get('Host'): return self.send(403,{'error':'Origin rejected'})
   try:
    size=int(self.headers.get('Content-Length','0'))
    if size>262144: return self.send(413,{'error':'Request too large'})
    data=json.loads(self.rfile.read(size) or '{}')
    if not isinstance(data,dict): raise Invalid('JSON object required')
    path=urlsplit(self.path).path; parts=path.strip('/').split('/')
    if path=='/api/plan': result=store.plan(data.get('product_id'),data.get('channel'))
    elif path=='/api/pause': result=store.pause(data.get('paused'))
    elif path=='/api/tick': result=store.tick()
    elif len(parts)==4 and parts[:2]==['api','actions']: result=store.transition(parts[2],parts[3],data)
    elif len(parts)==2 and parts[0]=='api': result=store.create_record(parts[1],data)
    else: return self.send(404,{'error':'Not found'})
    self.send(200,result)
   except (Invalid,ValueError,TypeError,KeyError) as e: self.send(400,{'error':str(e)})
   except Exception: self.send(500,{'error':'Internal error; operation not confirmed'})
 def worker():
  while True:
   try: store.tick()
   except Exception: pass
   time.sleep(30)
 threading.Thread(target=worker,daemon=True).start()
 print(f'GrowthPilot mock dashboard: http://{args.host}:{args.port}',flush=True)
 ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()
if __name__=='__main__': main()
