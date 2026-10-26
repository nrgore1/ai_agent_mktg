"""Private bridge from Docker's edge gateway to a loopback SSH reverse tunnel."""
import json, os, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
class Bridge(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path!='/api/tags':return self.send_error(404)
  self.forward(None)
 def do_POST(self):
  if self.path!='/api/generate':return self.send_error(404)
  size=int(self.headers.get('Content-Length','0'))
  if not 1<=size<=131072:return self.send_error(413)
  raw=self.rfile.read(size)
  try:
   data=json.loads(raw)
   if data.get('model')!=os.environ['GROWTHPILOT_OLLAMA_MODEL'] or data.get('stream') is not False:return self.send_error(400)
  except (ValueError,KeyError):return self.send_error(400)
  self.forward(raw)
 def forward(self,raw):
  try:
   req=urllib.request.Request('http://127.0.0.1:11435'+self.path,data=raw,headers={'Content-Type':'application/json'})
   with urllib.request.urlopen(req,timeout=360) as res:body=res.read(262144)
   self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  except Exception:self.send_error(503,'Local Kimi tunnel unavailable')
if __name__=='__main__':HTTPServer((os.environ.get('GROWTHPILOT_BRIDGE_BIND','172.16.1.1'),11436),Bridge).serve_forever()
