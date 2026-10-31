"""VPS-host-only aggregate refresh; never writes to product services or payment APIs."""
import json
import subprocess
import sys
from pathlib import Path

def main():
    collector=Path(__file__).with_name('collect_actual_finance.py')
    # The existing collector logs aggregates; capture privately, emit only safe counts here.
    subprocess.run([sys.executable,str(collector)],stdout=subprocess.PIPE,check=True)
    actual=json.loads((Path.home()/'actual-finance-reconciliation.json').read_text())
    if len(actual.get('product_status',[]))!=17 or not actual.get('captured_at'):
        raise SystemExit('Incomplete collector envelope; existing snapshot preserved')
    container='growthpilot-staging-growthpilot-1'
    code='''
import datetime as dt,json,os,sys
from pathlib import Path
p=Path('/app/data/economics-source.json')
original=p.read_bytes();source=json.loads(original)
actual=json.load(sys.stdin)
stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
backup=p.with_name('economics-source.before-refresh-'+stamp+'.json')
fd=os.open(backup,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(original)
source['actual_finance']=actual
temporary=p.with_name('economics-source.refresh-'+stamp+'.tmp')
fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:
 json.dump(source,f);f.flush();os.fsync(f.fileno())
temporary.replace(p)
print(json.dumps({'captured_at':actual['captured_at'],'processor_accounts':len(actual.get('processor_accounts',[])),'products':len(actual['product_status']),'financial_reconciled':actual.get('financial_reconciled') is True}))
'''
    subprocess.run(['docker','exec','-i',container,'python','-c',code],input=json.dumps(actual).encode(),check=True)

if __name__=='__main__':main()
