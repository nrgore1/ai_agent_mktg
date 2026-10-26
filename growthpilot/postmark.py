"""Explicitly scoped Postmark identities; secrets never enter snapshots or audit payloads."""
import json,os,re,urllib.request
from pathlib import Path
from .core import Invalid

def account_key(product_id):return 'liqmint_individual' if product_id==1 else 'liqmint_institutional' if product_id==2 else 'atmakosh'
def accounts():
 path=Path(os.environ.get('GROWTHPILOT_POSTMARK_FILE',str(Path(os.environ.get('GROWTHPILOT_DB','data/growthpilot.db')).parent/'postmark-accounts.json')))
 if not path.exists():return {}
 return json.loads(path.read_text())
def configured(product_id):return accounts().get(account_key(product_id),{})
def public_accounts():return {key:{k:v for k,v in value.items() if k in ('sender','server_id','stream','status')} for key,value in accounts().items()}
def envelope(payload,key):
 account=configured(payload['product_id'])
 if account.get('status')!='configured' or not account.get('token') or not account.get('stream'):raise Invalid('Postmark account or broadcast stream not configured')
 if payload.get('account')!=account_key(payload['product_id']) or payload.get('sender')!=account['sender']:raise Invalid('Sender account does not match product')
 recipient=payload.get('recipient','')
 if not re.fullmatch(r'[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+',recipient):raise Invalid('Exactly one valid recipient required')
 if any('\r' in str(payload.get(k,'')) or '\n' in str(payload.get(k,'')) for k in ('title','sender','recipient')):raise Invalid('Invalid email header')
 # The opt-out instructions are part of the approved body, never silently appended on send.
 if '{{{ pm:unsubscribe }}}' not in payload.get('content',''):raise Invalid('Approved marketing body must include the Postmark unsubscribe placeholder')
 return account,{'From':payload['sender'],'To':recipient,'Subject':payload['title'],'TextBody':payload['content'],'MessageStream':account['stream'],'TrackOpens':False,'TrackLinks':'None','Metadata':{'growthpilot_action':key,'product_id':str(payload['product_id'])}}
def send(payload,key,test=False):
 account,body=envelope(payload,key)
 if not test and os.environ.get('GROWTHPILOT_ENABLE_POSTMARK')!='true':raise Invalid('Postmark delivery not enabled')
 token='POSTMARK_API_TEST' if test else account['token']
 req=urllib.request.Request('https://api.postmarkapp.com/email',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Accept':'application/json','X-Postmark-Server-Token':token})
 with urllib.request.urlopen(req,timeout=25) as response:result=json.load(response)
 if result.get('ErrorCode')!=0 or not result.get('MessageID'):raise Invalid('Postmark did not confirm acceptance')
 return {'mode':'postmark_test' if test else 'postmark','external_delivery':not test,'provider_id':result['MessageID'],'provider_accepted':True,'delivered':False}
