import json,subprocess,secrets,os,hashlib
from pathlib import Path
root=Path.home()/'agentvire-business-connectors-20261103';root.chmod(0o700)
config=root/'vanguard-reader.json';role='agentvire_ops_reader'
info=json.loads(subprocess.check_output(['docker','inspect','vanguard-db']))[0]
env=dict(x.split('=',1) for x in info['Config']['Env'] if '=' in x)
admin=env.get('POSTGRES_USER','postgres');database=env.get('POSTGRES_DB',admin)
def sql(text,user=admin,password=None):
 command=['docker','exec','-i']
 local=dict(os.environ)
 if password:local['PGPASSWORD']=password;command+=['--env','PGPASSWORD']
 command+=['vanguard-db','psql']+(['-h','127.0.0.1'] if password else [])+['-U',user,'-d',database,'-At','-v','ON_ERROR_STOP=1']
 r=subprocess.run(command,input=text.encode(),env=local,capture_output=True)
 if r.returncode:raise RuntimeError('Protected database operation failed; no credentials logged')
 return r.stdout.decode().strip()
exists=sql("SELECT count(*) FROM pg_roles WHERE rolname='agentvire_ops_reader';")=='1'
if config.exists():
 settings=json.loads(config.read_text());assert exists and settings['database']==database
else:
 assert not exists,'Reader already exists without its protected configuration; stop for reconciliation'
 password=secrets.token_urlsafe(36)
 sql("CREATE ROLE agentvire_ops_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD '"+password+"'; ALTER ROLE agentvire_ops_reader SET default_transaction_read_only=on; GRANT USAGE ON SCHEMA public TO agentvire_ops_reader; GRANT SELECT (id,property_id,name,kind,stage,next_step,next_step_date,updated_at,priority_score,is_segment,email_consent,website) ON public.partners TO agentvire_ops_reader;")
 fd=os.open(config,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'w') as f:json.dump({'database':database,'password':password},f)
 settings={'password':password,'database':database}
assert sql("SELECT has_table_privilege('agentvire_ops_reader','public.partners','UPDATE');")=='f'
assert sql("SELECT has_column_privilege('agentvire_ops_reader','public.partners','contact_email','SELECT');")=='f'
assert sql('SHOW default_transaction_read_only;',role,settings['password'])=='on'
count=int(sql('SELECT count(id) FROM public.partners;',role,settings['password']))
subprocess.run(['python3',str(root/'deploy/vanguard_snapshot_bridge.py')],check=True)
old=subprocess.run(['crontab','-l'],capture_output=True,text=True)
assert old.returncode in (0,1)
marker='# agentvire-vanguard-sync-v1'
line='*/5 * * * * /usr/bin/flock -n '+str(root/'vanguard-sync.lock')+' /usr/bin/python3 '+str(root/'deploy/vanguard_snapshot_bridge.py')+' > '+str(root/'vanguard-sync-last.log')+' 2>&1 '+marker
lines=[x for x in old.stdout.splitlines() if marker not in x]
subprocess.run(['crontab','-'],input=('\n'.join(lines+[line])+'\n').encode(),check=True)
receipt={'connected':True,'records':count,'read_only':True,'contact_email_denied':True,'update_denied':True,'schedule':'every five minutes','direction':'Vanguard to AgentVire','source_mutations':0}
(root/'bridge-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
