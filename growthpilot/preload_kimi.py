"""Operator/startup-only pinned local preload; never called by serving requests."""
import json, time, re, urllib.request
from . import bounded_kimi_bridge as bridge

def preload():
    if not re.fullmatch('[a-f0-9]{64}',bridge.MODEL_DIGEST):raise ValueError('Pinned model digest required')
    with urllib.request.urlopen(bridge.UPSTREAM+'/api/tags',timeout=2)as r:models=json.load(r).get('models',[])
    if not any(m.get('name')==bridge.MODEL and m.get('digest')==bridge.MODEL_DIGEST for m in models):raise ValueError('Pinned local model missing; downloads prohibited')
    payload={'model':bridge.MODEL,'prompt':'','stream':False,'keep_alive':-1,'options':bridge.load_options()}
    started=time.monotonic()
    req=urllib.request.Request(bridge.UPSTREAM+'/api/generate',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=60)as r:data=json.load(r)
    if data.get('model')!=bridge.MODEL or data.get('done')is not True or not bridge.model_ready():raise ValueError('Pinned model not ready')
    return {'model':bridge.MODEL,'digest':bridge.MODEL_DIGEST,'seconds':round(time.monotonic()-started,3),'load_only':True,'load_options':bridge.load_options()}

if __name__=='__main__':print(json.dumps(preload()))
