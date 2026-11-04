"""VPS-side, read-only Vanguard snapshot bridge; no Docker socket in AgentVire."""
import datetime as dt
import json
import os
import subprocess
from pathlib import Path

ROOT=Path.home()/'agentvire-business-connectors-20261103'
CONTAINER='growthpilot-staging-growthpilot-1'
FIELDS=['id','property_id','name','kind','stage','next_step','next_step_date','updated_at','priority_score','is_segment','email_consent','website']
SQL="""SELECT COALESCE(json_agg(row_to_json(s) ORDER BY id),'[]'::json) FROM (
SELECT id,property_id,name,kind,stage,COALESCE(next_step,'') AS next_step,
COALESCE(next_step_date,'') AS next_step_date,COALESCE(updated_at,'') AS updated_at,
COALESCE(priority_score,0) AS priority_score,COALESCE(is_segment,0) AS is_segment,
COALESCE(email_consent,'none') AS email_consent,COALESCE(website,'') AS website
FROM public.partners) s"""
WRITER="""import json,os,sys
from pathlib import Path
packet=json.load(sys.stdin)
for name,body in packet.items():
 assert name in ('vanguard-snapshot.json','vanguard-sync-status.json')
 p=Path('/app/data')/name;t=p.with_suffix('.tmp')
 fd=os.open(t,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
 with os.fdopen(fd,'w') as f:json.dump(body,f);f.flush();os.fsync(f.fileno())
 t.replace(p)
"""
def publish(packet):
 subprocess.run(['docker','exec','-i',CONTAINER,'python','-c',WRITER],input=json.dumps(packet).encode(),check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)
def main():
 checked=dt.datetime.now(dt.timezone.utc).isoformat()
 try:
  config=json.loads((ROOT/'vanguard-reader.json').read_text())
  env=dict(os.environ,PGPASSWORD=config['password'])
  raw=subprocess.check_output(['docker','exec','--env','PGPASSWORD','vanguard-db','psql','-h','127.0.0.1','-U','agentvire_ops_reader','-d',config['database'],'-At','-v','ON_ERROR_STOP=1','-c',SQL],env=env,stderr=subprocess.DEVNULL,timeout=20)
  if len(raw)>3000000:raise ValueError('Snapshot too large')
  records=json.loads(raw)
  if not isinstance(records,list) or len(records)>5000 or any(set(r)!=set(FIELDS) for r in records):raise ValueError('Unexpected source schema')
  publish({'vanguard-snapshot.json':{'schema_version':1,'source':'vanguard-gtm','complete':True,'captured_at':checked,'records':records},'vanguard-sync-status.json':{'status':'ok','checked_at':checked,'source_count':len(records)}})
  print(json.dumps({'status':'ok','checked_at':checked,'records':len(records),'outbound_mutations':0}))
 except Exception:
  publish({'vanguard-sync-status.json':{'status':'error','checked_at':checked,'note':'Source refresh failed; retained snapshot must not be treated as current.'}})
  raise SystemExit('Vanguard read-only refresh failed; inspect protected service configuration.')
if __name__=='__main__':main()
