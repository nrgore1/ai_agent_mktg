from pathlib import Path
import json
root=Path(__file__).parent
cases=[('oratoplus',3,'oratoplus-core-api-tsvalidation-1dc247b','component_ora.py'),('memoire',5,'memoir-production-api-django-1','component_memoire.py'),('weddingos',4,'weddingos-production-api-1','component_wedding.py')]
payload=[(n,p,c,(root/f).read_text())for n,p,c,f in cases]
runner='''import datetime as dt,json,subprocess,time
from pathlib import Path
out=Path.home()/'agentvire-wave-tests-20261101';out.mkdir(mode=0o700,exist_ok=True)
results=[]
for name,pid,container,script in CASES:
 image=json.loads(subprocess.check_output(['docker','inspect',container]))[0]['Image']
 cmd=['docker','run','--rm','-i','--name','agentvire-wave-'+name,'--network','none','--read-only','--tmpfs','/tmp:rw,size=256m','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--cpus','1','--entrypoint','python',image,'-']
 start=time.monotonic()
 try:
  proc=subprocess.run(cmd,input=script.encode(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
  log=proc.stdout.decode(errors='replace');(out/(name+'.log')).write_text(log)
  markers=[s.removeprefix('AGENTVIRE_RESULT ')for s in log.splitlines()if s.startswith('AGENTVIRE_RESULT ')]
  result=json.loads(markers[-1])if markers else {'tests':0,'status':'blocked','diagnostic_tail':log[-1800:]}
 except subprocess.TimeoutExpired:
  subprocess.run(['docker','rm','-f','agentvire-wave-'+name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  result={'tests':0,'status':'blocked','diagnostic_tail':'90-second isolated test budget exceeded'}
 result.update(product_id=pid,name=name,image=image,seconds=round(time.monotonic()-start,2),recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),network='none',provider_credentials=False,production_data_mounted=False)
 results.append(result);print(json.dumps(result),flush=True)
 (out/'component-results.json').write_text(json.dumps(results,indent=2))
'''
(root/'run_components.py').write_text(runner.replace('CASES',repr(payload)))
