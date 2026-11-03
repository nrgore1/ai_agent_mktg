"""Conservative planning math; never authorizes sending, billing or payouts."""
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR

D = Decimal
FLOOR = D('0.75')

def number(value, name):
    result = D(str(value))
    if not result.is_finite() or result < 0:
        raise ValueError(name + ' must be finite and nonnegative')
    return result

def assess(model, price=None, partner_rate=None, discount=0, cost_multiplier=1):
    p=number(model['price_usd'] if price is None else price,'price')
    rate=number(model['partner_rate'] if partner_rate is None else partner_rate,'partner rate')
    refund=number(model['refund_allowance'],'refund allowance')
    fee_rate=number(model['payment_fee_rate'],'payment fee')
    discount=number(discount,'discount')
    units=number(model['cohort_units'],'cohort')
    multiplier=number(cost_multiplier,'cost multiplier')
    if any(x>=1 for x in [rate,refund,fee_rate,discount]) or units<=0 or multiplier<1:
        raise ValueError('Invalid rate, cohort or cost multiplier')
    gross=p*(1-discount)
    net=gross*(1-refund)
    service=(number(model['incremental_nonlabor_per_unit_usd'],'usage')+
             number(model['support_minutes_per_unit'],'support')/60*number(model['labor_hourly_usd'],'labor')+
             number(model['extra_compliance_delivery_per_unit_usd'],'delivery'))*multiplier
    allocated=number(model['fixed_budget_usd'],'fixed costs')/units*multiplier
    payment=gross*fee_rate+number(model['fixed_payment_fee_usd'],'fixed fee')
    commission=net*rate  # Every acquired unit is partner-attributed, conservatively.
    cost=service+allocated+payment+commission
    margin=(net-cost)/net if net>0 else None
    room=net*(1-FLOOR)-service-allocated-payment
    max_rate=max(D(0),room/net) if net>0 else D(0)
    denominator=(1-discount)*((1-refund)*(1-FLOOR-rate)-fee_rate)
    minimum=(service+allocated+number(model['fixed_payment_fee_usd'],'fixed fee'))/denominator if denominator>0 else None
    minimum=minimum.quantize(D('.01'),rounding=ROUND_CEILING) if minimum is not None else None
    owner=number(model.get('owner_value_usd',0),'owner value')
    recovery=number(model.get('recovery_months',60),'recovery months')
    if recovery<=0:raise ValueError('Recovery horizon must be positive')
    economic_margin=(net-cost-owner/recovery/units)/net if net>0 else None
    def f(x):return None if x is None else float(x)
    return {
        'price_usd':f(p),'cohort_units':f(units),'net_revenue_per_unit_usd':f(net),
        'service_cost_usd':f(service),'allocated_cost_usd':f(allocated),'payment_fee_usd':f(payment),
        'partner_rate':f(rate),'partner_commission_usd':f(commission),'total_operating_cost_usd':f(cost),
        'operating_margin':f(margin),'meets_75_percent_model_floor':margin is not None and margin>=FLOOR,
        'commission_ceiling_rate':f(max_rate.quantize(D('.0001'),rounding=ROUND_FLOOR)),
        'minimum_price_at_current_scope_usd':f(minimum),'economic_margin_after_owner_recovery':f(economic_margin),
        'actual_margin_verified':False,'execution_authorized':False,
        'warning':'Planning estimates and hypothetical paid volumes; not actual margins or a publication/payout approval.'}

def validate_release(*,model_floor_met,actual_costs_verified,scope_ready,market_evidence,
                     audience_eligible,account_verified,claims_supported,public_launch_enabled):
    gates=locals()
    # Strict booleans: a string such as "false" must never open a gate.
    missing=[k for k,v in gates.items() if v is not True]
    return {'eligible':not missing,'missing_gates':missing,'sends_messages':False}
