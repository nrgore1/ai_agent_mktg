import unittest
from growthpilot.commercial_policy import assess,validate_release

class CommercialPolicyTests(unittest.TestCase):
 def model(self):
  return dict(price_usd=100,partner_rate=.05,refund_allowance=0,payment_fee_rate=0,cohort_units=10,
   incremental_nonlabor_per_unit_usd=10,support_minutes_per_unit=0,labor_hourly_usd=40,
   extra_compliance_delivery_per_unit_usd=0,fixed_budget_usd=100,fixed_payment_fee_usd=0)
 def test_exact_75_percent_and_commission_boundary(self):
  m=self.model();d=assess(m);self.assertEqual(d['operating_margin'],.75)
  self.assertTrue(d['meets_75_percent_model_floor']);self.assertEqual(d['commission_ceiling_rate'],.05)
  self.assertFalse(assess(m,partner_rate=.0501)['meets_75_percent_model_floor'])
 def test_discounts_refunds_and_cost_growth_reduce_margin(self):
  m=self.model();self.assertFalse(assess(m,discount=.1)['meets_75_percent_model_floor'])
  self.assertFalse(assess(m,cost_multiplier=2)['meets_75_percent_model_floor'])
  m['refund_allowance']=.1;self.assertFalse(assess(m)['meets_75_percent_model_floor'])
 def test_free_is_not_infinite_margin(self):
  d=assess(self.model(),price=0);self.assertIsNone(d['operating_margin']);self.assertFalse(d['meets_75_percent_model_floor'])
 def test_model_never_claims_actual_margin(self):
  d=assess(self.model(),price=1000);self.assertFalse(d['actual_margin_verified']);self.assertFalse(d['execution_authorized'])
 def test_minimum_price_rounds_up(self):
  m=self.model();m['payment_fee_rate']=.029;m['refund_allowance']=.03
  d=assess(m);self.assertTrue(assess(m,price=d['minimum_price_at_current_scope_usd'])['meets_75_percent_model_floor'])
 def test_impossible_denominator(self):
  d=assess(self.model(),partner_rate=.3);self.assertIsNone(d['minimum_price_at_current_scope_usd'])
 def test_bad_numbers_rejected(self):
  for x in ['NaN','Infinity',-1]:
   with self.assertRaises(ValueError):assess(self.model(),price=x)
  m=self.model();m['cohort_units']=0
  with self.assertRaises(ValueError):assess(m)
 def test_owner_recovery_does_not_disappear(self):
  m=self.model();m.update(owner_value_usd=60000,recovery_months=60)
  d=assess(m);self.assertEqual(d['operating_margin'],.75);self.assertEqual(d['economic_margin_after_owner_recovery'],-.25)
 def test_incomplete_or_string_gate_cannot_release(self):
  gates=dict(model_floor_met=True,actual_costs_verified=True,scope_ready=True,market_evidence=True,
   audience_eligible=True,account_verified=True,claims_supported=True,public_launch_enabled=True)
  self.assertTrue(validate_release(**gates)['eligible'])
  for k in gates:
   self.assertFalse(validate_release(**dict(gates,**{k:False}))['eligible'])
   self.assertFalse(validate_release(**dict(gates,**{k:'true'}))['eligible'])

if __name__=='__main__':unittest.main()
