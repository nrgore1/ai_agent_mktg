import unittest,tempfile,json
from pathlib import Path
from growthpilot.platform import Platform
from growthpilot.identity import Identity
from growthpilot.user_management import directory,dispatch,can_manage
from growthpilot.business_os import BusinessOS,UNITS,ACCESS_ROLES,ROLES,PROCESSES
from growthpilot.business_runtime import BusinessRuntime
from growthpilot.core import Invalid
from growthpilot.role_access import manage_account

class UserManagementTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Platform(Path(self.tmp.name)/'db');self.i=Identity(self.s)
  self.i.create('founder','Owner-Private-Password','founder');self.f={'username':'founder','role':'founder','products':[]}
 def tearDown(self):self.tmp.cleanup()
 def create(self,name='staff',roles=None,company='atmakosh',units=None,actor=None):
  data={'username':name,'password':'Temporary-Private-Password','display_name':name,'company':company,'roles':roles or ['BILLING'],'units':units or ['weddingos'],'note':'Create explicitly scoped staff access for QA.'}
  dispatch(self.i,'create',data,actor or self.f)
  return self.i.login(name,data['password'],'qa-'+name)
 def row(self,name,actor=None):return next(u for u in directory(self.i,actor or self.f)['users']if u['username']==name)
 def action(self,name,action,actor=None,**extra):
  return dispatch(self.i,action,{'username':name,'version':self.row(name,actor)['version'],'note':'Verified explicit account lifecycle action.',**extra},actor or self.f)
 def test_catalog_and_all_role_company_boundaries(self):
  self.assertEqual(len(ACCESS_ROLES),20);self.assertEqual(len(PROCESSES),22)
  for company in ('atmakosh','vireoka'):
   unit='weddingos'if company=='atmakosh'else'liqmint_individual'
   for role in ACCESS_ROLES:
    user=self.create(company+'-'+role,roles=[role],company=company,units=[unit]);summary=BusinessOS(self.s).summary(user)
    self.assertEqual({u['id']for u in summary['units']},{unit})
    self.assertEqual(set(summary['roles']),{role})
    self.assertEqual('finance'in summary['dashboard_tabs'],role in {'CFO','REVENUE','AUDITOR'})
    self.assertEqual(can_manage(self.s,user),role=='USER_ADMIN')
    if role not in ROLES:self.assertEqual(summary['role_workers']['jobs'],[]);self.assertEqual(summary['operating_plan']['plans'],[])
 def test_create_edit_revokes_all_sessions_and_replaces_scope(self):
  u=self.create();a=self.i.login('staff','Temporary-Private-Password','qa');v=self.row('staff')['version']
  dispatch(self.i,'update',{'username':'staff','version':v,'display_name':'Billing and invoices','company':'vireoka','roles':['BILLING','INVOICING'],'units':['liqmint_individual'],'note':'President transfers this test login to the verified new unit.'},self.f)
  self.assertIsNone(self.i.session(a['session']))
  new=self.i.login('staff','Temporary-Private-Password','qa');d=BusinessOS(self.s).summary(new)
  self.assertEqual([x['id']for x in d['companies']],['vireoka']);self.assertEqual(set(d['roles']),{'BILLING','INVOICING'})
  with self.assertRaises(Invalid):dispatch(self.i,'disable',{'username':'staff','version':v,'note':'This stale account edit must be refused.'},self.f)
 def test_password_reset_and_delete_preserve_audit_without_secrets(self):
  u=self.create();self.action('staff','reset_password',password='Reset-Private-Password-123')
  self.assertIsNone(self.i.session(u['session']));self.assertIsNone(self.i.login('staff','Temporary-Private-Password','qa'))
  self.assertTrue(self.i.login('staff','Reset-Private-Password-123','qa')['must_change'])
  self.action('staff','delete',confirm_username='staff');self.assertIsNone(self.i.login('staff','Reset-Private-Password-123','qa'))
  self.assertTrue(self.row('staff')['deleted']);self.assertEqual(self.row('staff')['grants'],[])
  with self.assertRaises(Invalid):manage_account(self.i,{'username':'staff','enabled':True},self.f)
  with self.s.db()as db:
   dump=str([dict(x)for x in db.execute('SELECT * FROM audit')]);self.assertNotIn('Reset-Private-Password',dump);self.assertNotIn('Temporary-Private-Password',dump)
  self.assertTrue(self.s.verify_audit()['valid'])
 def test_directory_never_exposes_credentials(self):
  self.create();text=json.dumps(directory(self.i,self.f))
  for value in ['Temporary-Private-Password','Owner-Private-Password','"password"','"salt"']:self.assertNotIn(value,text)
 def test_president_and_self_protected(self):
  for action in ['delete','disable','enable','reset_password']:
   data={'username':'founder','version':self.row('founder')['version'],'note':'Protected owner account must remain accessible.'}
   if action=='delete':data['confirm_username']='founder'
   if action=='reset_password':data['password']='Should-Never-Apply-Password'
   with self.assertRaises(PermissionError):dispatch(self.i,action,data,self.f)
 def test_delegated_admin_scope_and_escalation_denial(self):
  admin=self.create('team.admin',['USER_ADMIN']);self.create('other',['BILLING'],company='vireoka',units=['liqmint_individual'])
  self.create('own',['INVOICING'],actor=admin);self.create('executive',['CFO'])
  names={u['username']for u in directory(self.i,admin)['users']}
  self.assertEqual(names,{'team.admin','own'})
  for roles in [['CFO'],['USER_ADMIN'],['BILLING','CEO']]:
   with self.assertRaises(PermissionError):self.create('escalate',roles,actor=admin)
  for unit,company in [('jodibana','atmakosh'),('liqmint_individual','vireoka')]:
   with self.assertRaises(PermissionError):self.create('crossscope',['SUPPORT'],company,[unit],admin)
  for target in ['other','executive','team.admin','founder']:
   data={'username':target,'version':self.row(target)['version'],'note':'Disallowed target lifecycle action must fail.'}
   with self.assertRaises(PermissionError):dispatch(self.i,'disable',data,admin)
 def test_admin_cannot_reset_mixed_privilege_or_out_of_scope_account(self):
  admin=self.create('admin',['USER_ADMIN']);self.create('mixed',['BILLING','CFO'])
  with self.assertRaises(PermissionError):dispatch(self.i,'reset_password',{'username':'mixed','version':self.row('mixed')['version'],'password':'Forbidden-Reset-Password','note':'Do not elevate through another account password.'},admin)
 def test_invalid_delete_confirmation_and_username_reuse(self):
  self.create()
  with self.assertRaises(Invalid):self.action('staff','delete',confirm_username='someoneelse')
  with self.assertRaises(Invalid):self.create('STAFF')
  self.action('staff','delete',confirm_username='staff')
  with self.assertRaises(Invalid):self.create('staff')
 def test_department_case_isolation_and_no_unqualified_ai_work(self):
  billing=self.create();invoice=self.create('invoice',['INVOICING']);os=BusinessOS(self.s)
  c=os.dispatch('create',{'unit_id':'weddingos','process':'billing_operations','title':'Billing evidence QA','owner':'staff','due_date':'2026-12-01','reference':'qa:billing'},billing)
  with self.s.db()as db:
   raw=self.s.get(db,'business_cases',c['id']);raw['steps'][2]['note']='PRIVATE CFO COST';self.s.save(db,'business_cases',raw)
  self.assertNotIn('PRIVATE CFO COST',str(os.summary(billing)));self.assertEqual(os.summary(invoice)['cases'],[])
  with self.assertRaises(PermissionError):os.dispatch('create',{'unit_id':'weddingos','process':'invoice_operations','title':'Forbidden invoice step','owner':'staff','due_date':'2026-12-01','reference':'qa:denied'},billing)
  runtime=BusinessRuntime(self.s);runtime.control({'enabled':True},self.f)
  self.assertEqual(runtime.tick(selector=lambda *a: self.fail('Specialist model must not run'))['status'],'idle')
 def test_auditor_read_scope_and_manual_preparation_limit(self):
  auditor=self.create('auditor',['AUDITOR']);os=BusinessOS(self.s)
  for unit in ['weddingos','liqmint_individual']:os.dispatch('create',{'unit_id':unit,'process':'financing','title':'Private funding request','owner':'founder','due_date':'2026-12-01','reference':'qa:funding'},self.f)
  d=os.summary(auditor);self.assertTrue(d['read_only']);self.assertEqual(len(d['cases']),1);self.assertEqual(d['cases'][0]['unit_id'],'weddingos');self.assertFalse(d['cases'][0]['can_work'])
  self.assertEqual(len(os.summary(self.f)['operating_plan']['plans']),0)

