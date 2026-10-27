import json
import tempfile
import unittest
from pathlib import Path

from growthpilot.core import Invalid
from growthpilot.economics import StrategyOS, number
from growthpilot.platform import Platform


class EconomicsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=Platform(Path(self.tmp.name)/'test.db')
        self.engine=StrategyOS(self.store)

    def tearDown(self):
        self.tmp.cleanup()

    def finance(self, **changes):
        data=dict(product_id=4,period_start='2026-09-01',period_end='2026-10-01',currency='USD',
                  recognized_revenue_usd=1000,direct_delivery_cost_usd=200,payment_fees_usd=50,
                  support_compliance_cost_usd=100,shared_delivery_cost_usd=50,
                  partner_compensation_usd=100,source_reference='Synthetic reconciled close and settlement fixture',
                  document_sha256='a'*64,allocation_basis='Synthetic logged service hours and metered single-pool allocation',
                  financial_reconciled=True,gaap_cogs_usd=300,
                  cogs_classification_reference='Synthetic reviewed cost-of-revenue classification')
        return dict(data,**changes)

    def test_unknown_costs_never_become_zero_or_live_profit(self):
        live=self.engine.overview()['live_assessments']
        self.assertEqual(len(live),17)
        self.assertTrue(all(x['cm2'] is None and x['recognized_revenue_usd'] is None for x in live))
        with self.assertRaises(Invalid):
            self.engine.import_financials(self.finance(shared_delivery_cost_usd=None),'founder')

    def test_allocation_challenge_changes_internal_floor_without_regulatory_pass(self):
        r=self.engine.calculate(3)
        self.assertTrue(r['original_allocation']['internal_floor_met'])
        self.assertFalse(r['revised_allocation']['internal_floor_met'])
        self.assertAlmostEqual(r['original_allocation']['cm2']-r['revised_allocation']['cm2'],.18,places=5)
        self.assertTrue(all(x['regulatory_status']=='not_evaluable' for x in r['options']))
        self.assertFalse(r['execution_enabled'])

    def test_partner_commission_applies_only_to_partner_attributed_sales(self):
        r=self.engine.calculate(3)
        self.assertEqual(r['revised_allocation']['partner_compensation_usd'],392)
        cut=r['options'][2]
        self.assertEqual(cut['expected_units'],90)
        self.assertEqual(cut['partner_sourced_units'],30)
        self.assertEqual(cut['partner_compensation_usd'],147)
        none=self.engine.calculate(3,{'partner_sourced_share':0})
        self.assertEqual(none['revised_allocation']['partner_compensation_usd'],0)

    def test_unchanged_commission_does_not_invent_partner_attrition(self):
        for product_id in (3,10):
            original=self.engine.defaults(self.engine.strategies['products'][product_id-1])
            r=self.engine.calculate(product_id,{'new_commission_rate':original['commission_rate']})
            self.assertEqual(r['options'][2]['expected_units'],r['revised_allocation']['expected_units'])
            self.assertEqual(r['options'][2]['contribution_change_usd'],0)

    def test_full_partner_attrition_and_withdrawal_are_safe(self):
        r=self.engine.calculate(3,{'partner_sourced_share':1,'partner_attrition_on_cut':1})
        self.assertEqual(r['options'][2]['expected_units'],0)
        exit=r['options'][3]
        self.assertIsNone(exit['cm2'])
        self.assertGreater(exit['shared_delivery_cost_usd'],0)
        self.assertTrue(exit['withdrawal_obligations_unquantified'])
        self.assertIsNone(exit['regulatory_capital_usd'])

    def test_sensitivity_price_floor_and_nonfinite_validation(self):
        r=self.engine.calculate(3,{'commission_rate':1,'partner_sourced_share':1})
        self.assertIsNone(r['price_floor_at_fixed_volume_usd'])
        self.assertGreater(r['demand_sensitivity'][0]['expected_units'],r['demand_sensitivity'][-1]['expected_units'])
        for value in [True,'NaN','Infinity',None,-1]:
            with self.assertRaises(Invalid):number(value,'amount')
        for data in [{'unknown':1},{'baseline_units':0},{'baseline_units':1.5},{'target_cm2':1},{'price_elasticity':2},{'dso_days':366}]:
            with self.assertRaises(Invalid):self.engine.calculate(3,data)

    def test_actual_finance_reconciles_distinct_margin_definitions(self):
        self.engine.import_financials(self.finance(),'founder')
        live=next(x for x in self.engine.overview()['live_assessments'] if x['product_id']==4)
        self.assertEqual(live['cm2'],.5)
        self.assertEqual(live['finance_gross_margin'],.7)
        self.assertIsNone(live['regulatory_margin'])
        self.assertEqual(live['internal_partner_cost_ceiling_usd'],0)

    def test_provisional_finance_never_produces_margin(self):
        self.engine.import_financials(self.finance(financial_reconciled=False),'founder')
        live=next(x for x in self.engine.overview()['live_assessments'] if x['product_id']==4)
        self.assertEqual(live['status'],'provisional_financial_input')
        self.assertIsNone(live['cm2'])
        with self.assertRaises(Invalid):self.engine.import_financials(self.finance(currency='EUR'),'founder')
        with self.assertRaises(Invalid):self.engine.import_financials(self.finance(document_sha256='wrong'),'founder')

    def test_finance_revisions_and_audit_preserve_provenance(self):
        a=self.engine.import_financials(self.finance(),'founder')
        b=self.engine.import_financials(self.finance(partner_compensation_usd=50),'founder')
        self.assertEqual(a['id'],b['id']);self.assertEqual(b['version'],2)
        with self.store.db() as db:self.assertEqual(len(self.store.rows(db,'financial_revisions')),1)
        self.assertTrue(self.store.verify_audit()['valid'])

    def test_all_products_run_without_execution_or_invented_prices(self):
        r=self.engine.run(actor='founder')
        self.assertEqual(len(r['scenarios']),17)
        self.assertEqual(len([s for s in r['scenarios'] if s['status']=='no_defensible_price_basis']),6)
        self.assertEqual(r['approvals'],[])
        with self.store.db() as db:
            self.assertEqual(len(self.store.rows(db,'economic_runs')),1)
            self.assertEqual(self.store.rows(db,'actions'),[])
        self.assertTrue(self.store.verify_audit()['valid'])


if __name__=='__main__':unittest.main()
