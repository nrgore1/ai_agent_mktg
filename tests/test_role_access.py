import tempfile, unittest
from pathlib import Path
from growthpilot.platform import Platform
from growthpilot.identity import Identity
from growthpilot.business_os import BusinessOS, UNITS, ROLES
from growthpilot.role_access import create_account
from growthpilot.core import Invalid
from growthpilot.request_limits import ReadLimits

class RoleAccessTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Platform(Path(self.tmp.name)/'db');self.i=Identity(self.s);self.os=BusinessOS(self.s)
  self.i.create('founder','Founder-Long-Password','founder');self.f={'username':'founder','role':'founder','products':[]}
 def tearDown(self):self.tmp.cleanup()
 def account(self,company='atmakosh',role='CMO'):
  name=company+'-'+role.lower()
  data=dict(username=name,password='Temporary-Long-Password',company=company,business_role=role,units=[u['id'] for u in UNITS if u['company_id']==company])
  create_account(self.i,data,self.f)
  login=self.i.login(name,data['password'],'local');return self.i.session(login['session']),data
 def case(self,unit,process):
  return self.os.dispatch('create',dict(unit_id=unit,process=process,title='Private '+process+' opportunity',owner='founder',due_date='2026-12-01',reference='private:source'),self.f)
 def test_all_ten_logins_company_role_scope(self):
  for company in ('vireoka','atmakosh'):
   for role in ROLES:
    u,_=self.account(company,role);d=self.os.summary(u)
    self.assertTrue(u['must_change']);self.assertEqual({x['company_id'] for x in d['units']},{company})
    self.assertTrue(all(x['roles']==[role] for x in d['units']))
    self.assertFalse(d['can_assign']);self.assertFalse(d['can_review']);self.assertEqual(d['users'],[])
    self.assertEqual('finance' in d['dashboard_tabs'],role=='CFO')
    self.assertEqual('opportunities' in d['dashboard_tabs'],role in ('CEO','CMO'))
 def test_step_notes_history_and_worker_results_do_not_leak(self):
  u,_=self.account();c=self.case('weddingos','sales')
  c=self.os.dispatch('record',dict(id=c['id'],version=1,status='complete',source='source:test',note='Public customer scope verified for this test.',attest=True),self.f)
  c=self.os.dispatch('record',dict(id=c['id'],version=2,status='in_progress',source='secret:ledger',note='CONFIDENTIAL CFO margins and private cost data'),self.f)
  self.case('weddingos','financing');self.case('liqmint_individual','sales')
  d=self.os.summary(u);self.assertEqual(len(d['cases']),1)
  self.assertNotIn('CONFIDENTIAL',str(d));self.assertNotIn('secret:ledger',str(d));self.assertNotIn('history',d['cases'][0])
  self.assertFalse(d['cases'][0]['can_work'])
 def test_revocation_applies_to_active_session(self):
  u,_=self.account();self.os.dispatch('assign',dict(username=u['username'],unit_id='weddingos',role='CMO',enabled=False),self.f)
  self.assertNotIn('weddingos',[x['id'] for x in self.os.summary(u)['units']])
 def test_no_cross_company_or_role_escalation(self):
  u,data=self.account()
  with self.assertRaises(PermissionError):create_account(self.i,{**data,'username':'attacker'},u)
  with self.assertRaises(Invalid):create_account(self.i,{**data,'username':'wrong','units':['liqmint_individual']},self.f)
  with self.assertRaises(Invalid):self.i.create('unsafe','Temporary-Long-Password','business',[])
  c=self.case('liqmint_individual','sales')
  with self.assertRaises(PermissionError):self.os.dispatch('record',dict(id=c['id'],version=1,status='in_progress',source='source:test',note='Cross company access must fail completely'),u)
 def test_password_change_invalidates_all_sessions(self):
  u,data=self.account();session=self.i.login(u['username'],data['password'],'local')
  with self.assertRaises(Invalid):self.i.change_password(u['username'],data['password'],data['password'])
  self.i.change_password(u['username'],data['password'],'New-Personal-Long-Password')
  self.assertIsNone(self.i.session(session['session']))
  self.assertFalse(self.i.login(u['username'],'New-Personal-Long-Password','local')['must_change'])
 def test_read_budget_is_per_account_and_expires(self):
  time=[0];limits=ReadLimits(limit=2,window=60,clock=lambda:time[0])
  self.assertTrue(limits.allow('a'));self.assertTrue(limits.allow('a'));self.assertFalse(limits.allow('a'))
  self.assertTrue(limits.allow('b'));time[0]=60;self.assertTrue(limits.allow('a'))

 def test_founder_reset_and_disable_revoke_sessions_without_secrets_in_audit(self):
  from growthpilot.role_access import manage_account
  u,data=self.account();session=self.i.login(u['username'],data['password'],'local')
  with self.assertRaises(PermissionError):manage_account(self.i,{'username':u['username'],'enabled':False},u)
  with self.assertRaises(Invalid):manage_account(self.i,{'username':'founder','enabled':False},self.f)
  manage_account(self.i,{'username':u['username'],'password':'Private-Reset-Password'},self.f)
  self.assertIsNone(self.i.session(session['session']))
  self.assertTrue(self.i.login(u['username'],'Private-Reset-Password','local')['must_change'])
  manage_account(self.i,{'username':u['username'],'enabled':False},self.f)
  self.assertIsNone(self.i.login(u['username'],'Private-Reset-Password','local'))
  with self.s.db() as db:
   self.assertNotIn('Private-Reset-Password',str([dict(r) for r in db.execute('SELECT * FROM audit')]))

 def test_cmo_source_view_defaults_closed_for_ambiguous_investor_partner_records(self):
  from growthpilot.role_access import scope_summary
  u,_=self.account();d=self.os.summary(u)
  d['vanguard']['records']=[{'id':k,'unit_id':'weddingos','kind':k,'name':'PRIVATE FUNDING' if k in ('investor','partner','unknown') else 'Customer research'} for k in ('investor','partner','unknown','design_partner','customer','champion')]
  d=scope_summary(u,d)
  self.assertEqual({r['kind'] for r in d['vanguard']['records']},{'design_partner','customer','champion'})
  self.assertNotIn('PRIVATE FUNDING',str(d))
