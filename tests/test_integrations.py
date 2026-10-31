import csv
import datetime as dt
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from growthpilot.core import Invalid, digest, now
from growthpilot.platform import Platform
from growthpilot.integrations import IntegrationHub, calendar_event, fold, NoRedirect


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.s = Platform(Path(self.tmp.name)/'test.db')
        self.hub = IntegrationHub(self.s)
        self.campaign = self.s.plan(1)['campaign']

    def tearDown(self):
        self.tmp.cleanup()

    def crm(self, rows=None, **changes):
        text = 'name,email,organization,pipeline,source\n'
        text += rows or 'Example,a@example.test,Example Ltd,customer,Owner supplied research\n'
        return dict(product_id=1, csv=text, request_id='test-import-001', preview=False, **changes)

    def draft(self, kind='calendar', **changes):
        data = dict(product_id=1, campaign_id=self.campaign['id'], kind=kind,
                    destination='https://calendar.google.com/calendar/u/0/r' if kind=='calendar' else 'https://www.linkedin.com/company/example/',
                    account='Owner test calendar', title='Evaluation meeting', content='Discuss the workflow; no performance claims.', request_id='handoff-001')
        if kind=='calendar':
            data['calendar_event']={'start':'2026-11-10T14:00:00-05:00','end':'2026-11-10T14:30:00-05:00','location':'Online'}
        data.update(changes)
        return self.hub.prepare(data, 'test_owner')

    def approve(self, action):
        self.s.update('products',1,{'website':'https://example.test','readiness':'verified'})
        action=self.s.transition(action['id'],'revise',{'attestations':{'product_facts':True,'channel_rules':True,'destination':True}})
        return self.s.transition(action['id'],'approve',{'payload_hash':action['payload_hash']})

    def test_nine_contracts_preserve_registry(self):
        overview=self.hub.overview()
        self.assertEqual(len(overview['integrations']),9)
        self.assertEqual(len(overview['products']),17)
        self.assertEqual(len(self.s.snapshot()['channels']),50)
        self.assertFalse(overview['payments']['margin_ready'])

    def test_crm_preview_replay_and_no_consent(self):
        data=self.crm();data['preview']=True
        self.assertEqual(self.hub.import_crm(data,'owner')['eligible_to_import'],1)
        self.assertEqual(self.s.snapshot()['leads'],[])
        data['preview']=False
        self.assertEqual(self.hub.import_crm(data,'owner')['created'],1)
        self.assertTrue(self.hub.import_crm(data,'owner')['replay'])
        leads=self.s.snapshot()['leads'];self.assertEqual(len(leads),1);self.assertEqual(leads[0]['consent'],'unknown')
        with self.assertRaises(Invalid):self.s.manager().outreach(leads[0]['id'],'owner')

    def test_crm_atomic_invalid_rows_and_forbidden_consent(self):
        data=self.crm(rows='Valid,a@example.test,Org,customer,Source\nBad,not-email,Org,customer,Source\n')
        with self.assertRaises(Invalid):self.hub.import_crm(data,'owner')
        self.assertEqual(self.s.snapshot()['leads'],[])
        data=self.crm();data['csv']=data['csv'].replace('pipeline,source','pipeline,consent,source')
        with self.assertRaises(Invalid):self.hub.import_crm(data,'owner')

    def test_crm_conflict_and_product_isolation(self):
        data=self.crm();self.hub.import_crm(data,'owner')
        other=dict(data,csv=data['csv'].replace('Example Ltd','Other Ltd'))
        with self.assertRaises(Invalid):self.hub.import_crm(other,'owner')
        other=dict(data,product_id=2);self.assertEqual(self.hub.import_crm(other,'owner')['created'],1)
        data['request_id']='test-import-002';self.assertEqual(self.hub.import_crm(data,'owner')['skipped_existing'],1)
        self.assertEqual(len(self.s.snapshot()['leads']),2)

    def test_crm_suppression_and_erasure_prevent_reimport(self):
        from growthpilot.marketing_consent import MarketingConsent
        with patch.dict(os.environ,{'GROWTHPILOT_CONSENT_SECRET':'test-secret-only-'*4}):
            service=MarketingConsent(self.s)
            ident=service.identifier('weddingos','a@example.test')
            with self.s.db() as db:
                self.s.save(db,'marketing_erasure_suppressions',{'id':ident,'product_id':4,'brand':'weddingos'})
                self.s.save(db,'suppressions',{'id':'one','email':'b@example.test'})
            data=self.crm(rows='A,a@example.test,Org,customer,Research\nB,b@example.test,Org,customer,Research\n');data['product_id']=4
            result=self.hub.import_crm(data,'owner');self.assertEqual(result['skipped_suppressed'],2)
            self.assertEqual(self.s.snapshot()['leads'],[])
        data['request_id']='test-import-no-secret'
        with patch.dict(os.environ,{'GROWTHPILOT_CONSENT_SECRET':''}):
            with self.assertRaises(Invalid):self.hub.import_crm(data,'owner')

    def test_csv_export_neutralizes_formula_and_is_product_scoped(self):
        self.s.create_record('leads',{'product_id':1,'name':'=HYPERLINK("bad")','email':'a@example.test','pipeline':'customer'})
        self.s.create_record('leads',{'product_id':2,'name':'Other','email':'b@example.test','pipeline':'customer'})
        exported=self.hub.export_crm(1,'owner');rows=list(csv.DictReader(io.StringIO(exported['content'])))
        self.assertEqual(len(rows),1);self.assertTrue(rows[0]['name'].startswith("'="))
        self.assertNotIn('b@example.test',exported['content'])

    def test_calendar_exact_approval_expiry_pause_revision(self):
        action=self.draft()
        with self.assertRaises(Invalid):self.hub.export_calendar(action['id'],'owner')
        action=self.approve(action)
        result=self.hub.export_calendar(action['id'],'owner')
        self.assertIn('DTSTART:20261110T190000Z',result['content']);self.assertFalse(result['external_delivery'])
        self.assertNotIn('ATTENDEE:',result['content']);self.assertNotIn('ORGANIZER:',result['content'])
        self.assertEqual(result['payload_hash'],action['payload_hash'])
        self.assertEqual(self.s.snapshot()['events'],[])
        self.s.pause(True)
        with self.assertRaises(Invalid):self.hub.export_calendar(action['id'],'owner')
        self.s.pause(False)
        with self.s.db() as db:
            action['approval']['expires_at']='2020-01-01T00:00:00+00:00';self.s.save(db,'actions',action)
        with self.assertRaises(Invalid):self.hub.export_calendar(action['id'],'owner')
        self.s.transition(action['id'],'revise',{'content':'Changed'})
        with self.assertRaises(Invalid):self.hub.export_calendar(action['id'],'owner')

    def test_calendar_rejects_invalid_times_and_cross_product(self):
        for value in ({'start':'2026-11-10T14:00:00','end':'2026-11-10T15:00:00','location':''},
                      {'start':'2026-11-10T14:00:00Z','end':'2026-11-10T13:00:00Z','location':''}):
            with self.assertRaises(Invalid):calendar_event(value)
        with self.assertRaises(Invalid):self.draft(product_id=2)
        with self.assertRaises(Invalid):self.draft(destination='https://calendar.google.com@evil.test/')

    def test_calendar_header_injection_unicode_and_immutable_timing(self):
        action=self.draft(title='日本語'*100+'\r\nATTENDEE:mailto:wrong@example.test')
        action=self.approve(action);content=self.hub.export_calendar(action['id'],'owner')['content']
        self.assertNotIn('\r\nATTENDEE:',content)
        self.assertTrue(all(len(line.encode())<=75 for line in content.split('\r\n')))
        with self.assertRaises(Invalid):self.s.transition(action['id'],'revise',{'calendar_event':{}})

    def test_social_idempotency_and_internal_public_scope(self):
        first=self.draft('social');self.assertEqual(first['id'],self.draft('social')['id'])
        with self.assertRaises(Invalid):self.draft('social',content='Different')
        internal=self.s.plan(10)['campaign']
        with self.assertRaises(Invalid):self.draft('social',product_id=10,campaign_id=internal['id'])
        first=self.approve(first)
        package=self.s.transition(first['id'],'export',{})
        self.assertEqual(package['package']['destination'],'https://www.linkedin.com/company/example/')
        receipt=self.s.transition(first['id'],'record_submission',{'receipt_url':'https://www.linkedin.com/feed/update/example','note':'Synthetic test receipt'})
        self.assertEqual(receipt['receipt']['verification'],'founder_reported');self.assertEqual(self.s.snapshot()['events'],[])
        self.assertTrue(self.s.verify_audit()['valid'])

    def test_payment_snapshot_currency_separation_stale_and_duplicate(self):
        path=Path(self.tmp.name)/'economics-source.json'
        account={'configured_product_ids':[1,2],'account_fingerprint':'shared','status':'read_only_collected','balance_arithmetic_valid':True,
                 'captured_charge_groups':[{'currency':c,'captured_count':2,'captured_minor':100,'refunded_to_date_minor':0,'disputed_count':0} for c in ('usd','inr')]}
        data={'actual_finance':{'captured_at':now(),'processor_accounts':[account]}}
        path.write_text(json.dumps(data));r=self.hub.payments();self.assertEqual(r['status'],'fresh');self.assertFalse(r['margin_ready']);self.assertEqual(len(r['accounts'][0]['charges']),2)
        data['actual_finance']['captured_at']='2020-01-01T00:00:00+00:00';path.write_text(json.dumps(data));self.assertEqual(self.hub.payments()['status'],'stale')
        data['actual_finance']['processor_accounts'].append(account);path.write_text(json.dumps(data));self.assertEqual(self.hub.payments()['status'],'invalid')

    def test_provider_check_redacts_secrets_and_cooldown(self):
        account={'token':'secret-test-token','status':'configured','stream':'broadcast','server_id':5}
        replies=[{'ID':5,'ApiTokens':['secret-test-token']},{'ID':'broadcast','ServerID':5,'MessageStreamType':'Broadcasts','ArchivedAt':None,'SubscriptionManagementConfiguration':{'UnsubscribeHandlingType':'Postmark'}}]
        with patch('growthpilot.integrations.postmark.accounts',return_value={'test':account}),patch('growthpilot.integrations.read_json',side_effect=replies):
            result=self.hub.check('email','owner');self.assertEqual(result['status'],'healthy')
        self.assertNotIn('secret-test-token',json.dumps(self.hub.overview()))
        with self.assertRaises(Invalid):self.hub.check('email','owner')
        with patch.dict(os.environ,{'GROWTHPILOT_GITHUB_REPO':'owner/repo'}),patch('growthpilot.integrations.read_json',side_effect=ValueError('secret-raw-body')):
            result=self.hub.check('github','owner');self.assertEqual(result['status'],'unavailable');self.assertNotIn('secret',json.dumps(result))

    def test_local_kimi_health_and_redirect_rejected(self):
        with patch.dict(os.environ,{'GROWTHPILOT_OLLAMA_MODEL':'kimi-local','GROWTHPILOT_OLLAMA_URL':'http://localhost:11434'}),patch('growthpilot.integrations.read_json',return_value={'models':[{'name':'kimi-local'}]}):
            self.assertEqual(self.hub.check('llm','owner')['status'],'healthy')
        with self.assertRaises(Invalid):NoRedirect().redirect_request(None,None,None,None,None,None)

    def test_invalid_dispatch_and_no_unknown_fields(self):
        with self.assertRaises(Invalid):self.hub.dispatch('delete',{},'owner')
        with self.assertRaises(Invalid):self.hub.dispatch('crm-export',{'product_id':1,'include_tokens':True},'owner')


if __name__=='__main__':unittest.main()
