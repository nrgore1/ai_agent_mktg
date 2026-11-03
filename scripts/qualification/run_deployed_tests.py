"""Run bundled product tests in disposable containers with no network or live mounts."""
import datetime as dt,json,subprocess,time
from pathlib import Path
out=Path.home()/'agentvire-wave-tests-20261101';out.mkdir(mode=0o700,exist_ok=True)
cases=[
 ('jodibana',6,'jodibana-web-1','pytest',['jodii_core/tests/test_billing_fails_closed.py','jodii_core/tests/test_billing_analytics.py','jodii_core/tests/test_commerce_content.py']),
 ('liqmint-individual',1,'liqmint-individual-prod-api-1','django',['apps.rewards.tests.test_platform_billing_service','apps.backtesting.tests.test_wallet_transfer_entitlement']),
 ('liqmint-institutional',2,'liqmint-institutional-prod-api-1','django',['apps.subscriptions.tests.test_institutional_billing','apps.backtesting.tests.test_wallet_transfer_entitlement','apps.backtesting.tests.test_wallet_transfer_quota','apps.rewards.tests.test_billing_jwt_refresh'])]
results=[]
for name,pid,container,kind,labels in cases:
 image=json.loads(subprocess.check_output(['docker','inspect',container]))[0]['Image']
 runner='''
import json,os,sys,time,types,traceback
os.environ.update(SECRET_KEY='isolated-wave-test-key',DJANGO_SECRET_KEY='isolated-wave-test-key',DATABASE_URL='sqlite:////tmp/agentvire-test.sqlite3',EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',DJANGO_EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',POSTMARK_SERVER_TOKEN='',STRIPE_SECRET_KEY='',STRIPE_SECRET_KEY_PROD='',LIQMINT_INSTITUTIONAL_STRIPE_SECRET_KEY='',CELERY_BROKER_URL='memory://',REDIS_URL='redis://127.0.0.1:1/0',DEBUG='true',USE_POSTGRES='0',PYTHONDONTWRITEBYTECODE='1')
sys.argv=['manage.py','test']
'''
 if kind=='pytest':
  runner+="""
os.environ['DJANGO_SETTINGS_MODULE']='jodii_proj.settings.test'
import pytest,xml.etree.ElementTree as ET
code=pytest.main(LABELS+['-q','-p','no:cacheprovider','--junitxml=/tmp/qualification.xml'])
root=ET.parse('/tmp/qualification.xml').getroot()
nodes=list(root.iter('testcase'))
print('AGENTVIRE_RESULT '+json.dumps({'tests':len(nodes),'failed':sum(n.find('failure')is not None for n in nodes),'errors':sum(n.find('error')is not None for n in nodes),'skipped':sum(n.find('skipped')is not None for n in nodes),'exit_code':int(code),'test_names':[n.attrib.get('name')for n in nodes]}))
"""
 else:
  runner+='''
os.environ['DJANGO_SETTINGS_MODULE']='agentvire_test_settings'
import config.settings as original
module=types.ModuleType('agentvire_test_settings')
for key in dir(original):
 if key.isupper():setattr(module,key,getattr(original,key))
module.DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}
module.EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
module.CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache'}}
module.CHANNEL_LAYERS={'default':{'BACKEND':'channels.layers.InMemoryChannelLayer'}}
module.MEDIA_ROOT='/tmp/media';module.STATIC_ROOT='/tmp/static';module.ALLOWED_HOSTS=['testserver','localhost']
module.PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher']
module.SECURE_SSL_REDIRECT=False;module.POSTMARK_SERVER_TOKEN=''
module.LIQMINT_INSTITUTIONAL_STRIPE_SECRET_KEY='';module.STRIPE_SECRET_KEY=''
class DisableMigrations(dict):
 def __contains__(self,item):return True
 def __getitem__(self,item):return None
module.MIGRATION_MODULES=DisableMigrations()
sys.modules['agentvire_test_settings']=module
import django;django.setup()
from django.test.runner import DiscoverRunner
class Runner(DiscoverRunner):
 def run_suite(self,suite,**kwargs):
  result=super().run_suite(suite,**kwargs)
  print('AGENTVIRE_RESULT '+json.dumps({'tests':result.testsRun,'failed':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'exit_code':0 if result.wasSuccessful()else 1,'failures':[str(t)for t,_ in result.failures],'error_tests':[str(t)for t,_ in result.errors]}),flush=True)
  return result
Runner(verbosity=2,interactive=False).run_tests(LABELS)
'''
 runner=runner.replace('LABELS',repr(labels))
 runtime='agentvire-wave-jodi-tests:20261101' if kind=='pytest' else image
 cmd=['docker','run','--rm','-i','--name','agentvire-wave-'+name,'--network','none','--read-only','--tmpfs','/tmp:rw,size=256m','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--cpus','1','--entrypoint','python',runtime,'-']
 if pid==2:cmd[cmd.index('--cap-drop'):cmd.index('--cap-drop')]=['--tmpfs','/mnt/c/Users/NAREN/vireoka-dev/yieldminter/backend/runtime/reports:rw,size=16m']
 start=time.monotonic()
 try:
  result=subprocess.run(cmd,input=runner.encode(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240)
  text=result.stdout.decode(errors='replace');(out/(name+'.log')).write_text(text)
  markers=[line.removeprefix('AGENTVIRE_RESULT ')for line in text.splitlines()if line.startswith('AGENTVIRE_RESULT ')]
  summary=json.loads(markers[-1])if markers else{'tests':0,'status':'blocked','reason':'Test harness could not initialize','diagnostic_tail':text[-1800:]}
 except subprocess.TimeoutExpired:
  subprocess.run(['docker','rm','-f','agentvire-wave-'+name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  summary={'tests':0,'status':'blocked','reason':'240 second test budget exceeded'}
 summary.update(product_id=pid,name=name,image=image,environment='isolated_deployed_image_offline',network='none',production_data_mounted=False,provider_credentials=False,seconds=round(time.monotonic()-start,2),recorded_at=dt.datetime.now(dt.timezone.utc).isoformat())
 results.append(summary);(out/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps(summary),flush=True)
