import unittest
from datetime import datetime, timezone
from growthpilot.audience import build_audience

class AudienceTests(unittest.TestCase):
    def row(self, **kwargs):
        return dict(dict(product_id=4, email='Member@customer.test', purpose='product_marketing',
            occurred_at='2026-10-29T12:00:00+00:00', status='confirmed', basis='explicit', channel='email',
            suppressed=False, source_verified=True, source_kind='signup_checkbox', source_reference='consent:123',
            notice_version='v1', notice_text='Email me WeddingOS product news. Optional.',
            email_confirmed=True, account_active=True, synthetic=False), **kwargs)
    def build(self, rows, **kwargs):
        return build_audience(rows, product_id=4, checked_at=datetime(2026,10,30,tzinfo=timezone.utc), **kwargs)
    def test_explicit_consent_deduplicates(self):
        d=self.build([self.row(),self.row()]);self.assertEqual(len(d['eligible']),1)
        self.assertEqual(d['eligible'][0]['email'],'member@customer.test');self.assertFalse(d['dispatch_authorized'])
    def test_no_cross_product_permission(self):
        self.assertEqual(self.build([self.row(product_id=6)])['eligible'],[])
    def test_signup_and_verification_are_not_marketing(self):
        for change in [dict(purpose='account'),dict(basis='service'),dict(status='replied'),dict(source_kind='import'),dict(source_verified='true')]:
            self.assertEqual(self.build([self.row(**change)])['eligible'],[])
    def test_withdrawal_wins(self):
        self.assertEqual(self.build([self.row(),self.row(status='withdrawn',occurred_at='2026-10-29T13:00:00Z')])['eligible'],[])
    def test_suppression_wins(self):
        self.assertEqual(self.build([self.row()],suppressions=['MEMBER@CUSTOMER.TEST'])['eligible'],[])
    def test_invalid_future_naive_and_expired_dates(self):
        for v in ['bad','2026-10-31T00:00:00Z','2026-10-29T00:00:00']:
            self.assertEqual(self.build([self.row(occurred_at=v)])['eligible'],[])
        self.assertEqual(self.build([self.row(expires_at='2026-10-29T00:00:00Z')])['eligible'],[])
    def test_synthetic_and_unknown_excluded(self):
        for change in [dict(synthetic=True),dict(synthetic=None),dict(email='qa@example.com'),dict(email_confirmed=False),dict(suppressed=None)]:
            self.assertEqual(self.build([self.row(**change)])['eligible'],[])
    def test_ambiguous_latest_fails_closed(self):
        self.assertEqual(self.build([self.row(),self.row(status='withdrawn')])['eligible'],[])
    def test_missing_notice_fails_closed(self):
        for key in ['notice_text','notice_version','source_reference']:
            self.assertEqual(self.build([self.row(**{key:''})])['eligible'],[])
    def test_empty_source_stays_empty(self):
        self.assertEqual(self.build([])['eligible'],[])

if __name__=='__main__':unittest.main()
