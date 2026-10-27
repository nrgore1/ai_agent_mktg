"""Auditable product economics. Observations, hypotheses and rules never share a ledger."""
import copy
import datetime as dt
import hashlib
import json
import math
import uuid
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from .core import Invalid, digest, now


def number(value, name, minimum=0, maximum=1000000000):
    if isinstance(value, bool):
        raise Invalid(name + ' must be numeric')
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise Invalid(name + ' must be numeric')
    if not result.is_finite() or result < Decimal(str(minimum)) or result > Decimal(str(maximum)):
        raise Invalid(name + ' is outside the permitted range')
    return result


def money(value):
    return float(value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))


def rate(value):
    return float(value.quantize(Decimal('.000001'), rounding=ROUND_HALF_UP))


class StrategyOS:
    def __init__(self, store):
        self.s = store
        here = Path(__file__).parent
        self.strategies = json.loads((here / 'product_strategies.json').read_text())
        self.policy = json.loads((here / 'economics_policy.json').read_text())

    def source(self):
        path = Path(self.s.path).parent / 'economics-source.json'
        if not path.exists():
            return {'status': 'unavailable', 'products': [], 'captured_at': None,
                    'limitations': ['No production aggregate snapshot imported.']}
        if path.stat().st_size > 262144:
            raise Invalid('Economics snapshot exceeds the size limit')
        data = json.loads(path.read_text())
        if not isinstance(data, dict) or not isinstance(data.get('products'), list):
            raise Invalid('Invalid economics source snapshot')
        data['snapshot_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        return data

    def defaults(self, product):
        p = number(product['scenario_price_usd'], 'price', .01, 1000000)
        pid = product['product_id']
        org = pid in (2, 4, 6, 9, 12, 13)
        qty = Decimal(5 if pid in (2, 9, 12) else 10 if org else 100)
        commission = {1: '.15', 2: '.10', 3: '.20', 4: '.20', 5: '.10', 6: '.10', 9: '.10'}.get(pid, '0')
        return {'unit_price_usd': money(p), 'baseline_units': int(qty),
                'direct_cost_per_unit_usd': money(p * Decimal('.45' if pid == 5 else '.12')),
                'support_cost_per_unit_usd': money(p * Decimal('.06')),
                'shared_delivery_cost_usd': money(p * qty * Decimal('.12')),
                'other_fixed_operating_cost_usd': 2000 if org else 500,
                'payment_fee_rate': .029, 'payment_fixed_fee_usd': .30,
                'commission_rate': float(commission), 'partner_sourced_share': .40,
                'partner_attrition_on_cut': .25, 'price_change': .20,
                'price_elasticity': -1, 'coverage_cost_reduction': .20,
                'coverage_volume_loss': .10, 'new_commission_rate': float(Decimal(commission) / 2),
                'target_cm2': float(self.policy['threshold_cm2']),
                'dso_days': 30 if pid in (2, 9, 12) else 0, 'refund_reserve_rate': .05,
                'setup_cash_usd': 2000 if org else 250, 'winddown_cash_usd': 1000,
                'cash_buffer_months': 3}

    def import_financials(self, data, actor):
        fields = {'product_id', 'period_start', 'period_end', 'currency', 'recognized_revenue_usd',
                  'direct_delivery_cost_usd', 'payment_fees_usd', 'support_compliance_cost_usd',
                  'shared_delivery_cost_usd', 'partner_compensation_usd', 'source_reference',
                  'document_sha256', 'allocation_basis', 'financial_reconciled', 'gaap_cogs_usd',
                  'cogs_classification_reference'}
        if not isinstance(data, dict) or set(data)-fields:
            raise Invalid('Unsupported financial input')
        pid = data.get('product_id')
        if type(pid) is not int or not 1 <= pid <= 17 or data.get('currency') != 'USD':
            raise Invalid('Choose an explicit product and one currency (USD)')
        try:
            start = dt.date.fromisoformat(data['period_start'])
            end = dt.date.fromisoformat(data['period_end'])
        except (KeyError, ValueError, TypeError):
            raise Invalid('Financial period dates required')
        if start >= end or end > dt.datetime.now(dt.timezone.utc).date():
            raise Invalid('Use a completed financial period with an exclusive end date')
        for key in ['source_reference', 'allocation_basis']:
            if not isinstance(data.get(key), str) or not 20 <= len(data[key]) <= 2000:
                raise Invalid(key + ' must document the evidence/basis (20–2000 characters)')
        sha = data.get('document_sha256', '')
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise Invalid('Source document SHA-256 required; do not upload customer identifiers')
        if type(data.get('financial_reconciled')) is not bool:
            raise Invalid('Explicit reconciliation attestation required')
        normalized = dict(data)
        for key in ['recognized_revenue_usd', 'direct_delivery_cost_usd', 'payment_fees_usd',
                    'support_compliance_cost_usd', 'shared_delivery_cost_usd', 'partner_compensation_usd']:
            normalized[key] = money(number(data.get(key), key))
        if data.get('gaap_cogs_usd') is not None:
            normalized['gaap_cogs_usd'] = money(number(data['gaap_cogs_usd'], 'gaap_cogs_usd'))
            if len(str(data.get('cogs_classification_reference', ''))) < 20:
                raise Invalid('COGS classification evidence required for a finance gross margin')
        else:
            normalized['gaap_cogs_usd'] = None
        normalized.update(id=digest([pid, str(start), str(end)])[:32], created_at=now(),
                          attested_by=actor, verification='founder/admin attestation; source not independently audited')
        with self.s.db() as db:
            old = next((row for row in self.s.rows(db, 'financial_inputs', pid) if row['id']==normalized['id']), None)
            if old:
                revision=dict(old, id=uuid.uuid4().hex, original_id=old['id'])
                self.s.save(db, 'financial_revisions', revision)
            normalized['version'] = old.get('version',1)+1 if old else 1
            self.s.save(db, 'financial_inputs', normalized)
            self.s.audit(db, 'financial_input_attested', normalized['id'],
                {'input_hash': digest(normalized), 'version': normalized['version'], 'product_id': pid}, actor)
        return normalized

    def live_assessments(self, source):
        found = {p['product_id']: p for p in source.get('products', [])}
        with self.s.db() as db:
            financials = self.s.rows(db, 'financial_inputs')
        assessments = []
        for p in self.strategies['products']:
            pid = p['product_id']
            candidates = [x for x in financials if x['product_id']==pid]
            f = max(candidates, key=lambda x: (x['period_end'],x['created_at'])) if candidates else None
            result = {'product_id': pid, 'name': p['name'],
                'status': 'incomplete_financial_inputs' if pid in found else 'source_not_connected',
                'source_observed': pid in found, 'recognized_revenue_usd': None,
                'cm2': None, 'regulatory_margin': None, 'regulatory_capital': None,
                'missing': ['Reconciled recognized net platform revenue', 'Measured delivery and support costs',
                            'Shared-cost pool and allocation driver', 'Eligible commissions and refunds',
                            'Applicable regulatory rule and capital requirements'],
                'note': 'Observed empty tables do not prove zero revenue. Configured plans and subscriptions do not prove paid customers.'}
            if f:
                result.update(financial_input_id=f['id'],financial_input_hash=digest(f),
                              financial_period=[f['period_start'],f['period_end']],
                              verification=f['verification'], source_reference=f['source_reference'])
                if f['financial_reconciled']:
                    revenue=Decimal(str(f['recognized_revenue_usd']))
                    service=sum(Decimal(str(f[k])) for k in ['direct_delivery_cost_usd','payment_fees_usd',
                                'support_compliance_cost_usd','shared_delivery_cost_usd'])
                    partner=Decimal(str(f['partner_compensation_usd']))
                    cm=revenue-service-partner
                    finance_gross=(revenue-Decimal(str(f['gaap_cogs_usd']))) if f.get('gaap_cogs_usd') is not None else None
                    ceiling=max(Decimal(0),revenue*(1-Decimal(self.policy['threshold_cm2']))-service)
                    result.update(status='attested_financial_period',recognized_revenue_usd=money(revenue),
                        cm2_usd=money(cm),cm2=rate(cm/revenue) if revenue else None,
                        finance_gross_margin=rate(finance_gross/revenue) if revenue and finance_gross is not None else None,
                        service_cost_usd=money(service),partner_compensation_usd=money(partner),
                        internal_partner_cost_ceiling_usd=money(ceiling),
                        missing=['Applicable regulatory rule and capital requirements'],
                        note='Attested completed-period finance input. Commission ceiling is a planning bound, not a payable or permission to change contracts. Regulatory assessment remains unresolved.')
                else:
                    result['status']='provisional_financial_input';result['note']='Reconciliation not attested; margin remains unavailable.'
            assessments.append(result)
        return assessments

    def overview(self):
        source = self.source()
        fresh = False
        if source.get('captured_at'):
            try:
                when = dt.datetime.fromisoformat(source['captured_at'])
                age = dt.datetime.now(dt.timezone.utc) - when
                fresh = when.tzinfo is not None and dt.timedelta(0) <= age <= dt.timedelta(days=7)
            except (TypeError, ValueError):
                pass
        with self.s.db() as db:
            runs = self.s.rows(db, 'economic_runs')
        strategies = copy.deepcopy(self.strategies)
        for p in strategies['products']:
            p['default_assumptions'] = self.defaults(p) if p['scenario_price_usd'] is not None else None
        return {'strategies': strategies, 'policy': self.policy, 'live_source': source,
                'source_fresh': fresh, 'live_assessments': self.live_assessments(source),
                'recent_runs': sorted(runs, key=lambda r: r['created_at'], reverse=True)[:30],
                'execution_enabled': False}

    def calculate(self, product_id, overrides=None):
        p = next((p for p in self.strategies['products'] if p['product_id'] == product_id), None)
        if not p:
            raise Invalid('Unknown product')
        if p['scenario_price_usd'] is None:
            return {'product_id': product_id, 'status': 'no_defensible_price_basis',
                    'reason': 'Discovery, mission funding or acquisition cost center; do not fabricate a commercial SKU.',
                    'options': p['options'], 'regulatory_status': 'not_evaluable', 'execution_enabled': False}
        inputs = self.defaults(p)
        overrides = overrides or {}
        if not isinstance(overrides, dict) or set(overrides) - set(inputs):
            raise Invalid('Unsupported scenario input')
        inputs.update(overrides)
        values = {}
        fractions = {'payment_fee_rate', 'commission_rate', 'partner_sourced_share', 'partner_attrition_on_cut',
                     'coverage_cost_reduction', 'coverage_volume_loss', 'new_commission_rate', 'target_cm2', 'refund_reserve_rate'}
        for key, value in inputs.items():
            if key == 'price_elasticity':
                values[key] = number(value, key, -5, 0)
            elif key == 'price_change':
                values[key] = number(value, key, -.5, 2)
            else:
                values[key] = number(value, key, 0, 1 if key in fractions else 1000000)
        d = values
        if d['baseline_units'] <= 0 or d['baseline_units'] % 1:
            raise Invalid('Baseline units must be a positive whole number')
        if d['unit_price_usd'] <= 0 or d['target_cm2'] >= 1 or d['cash_buffer_months'] > 24 or d['dso_days'] > 365:
            raise Invalid('Invalid price, margin target or capital timing')
        if d['new_commission_rate'] > d['commission_rate']:
            raise Invalid('Commission-cut scenario requires a rate no higher than the current assumption')

        def model(label, price, units, commission, delivery_factor=Decimal(1), full_cost=True, withdrawal=False, partner_share=None):
            revenue = price * units
            direct = d['direct_cost_per_unit_usd'] * delivery_factor * units
            support = d['support_cost_per_unit_usd'] * units if full_cost else Decimal(0)
            shared = d['shared_delivery_cost_usd'] if full_cost else Decimal(0)
            fees = revenue * d['payment_fee_rate'] + d['payment_fixed_fee_usd'] * units
            effective_share = d['partner_sourced_share'] if partner_share is None else partner_share
            partner = revenue * commission * effective_share
            service_gross = revenue - direct - support - shared - fees
            contribution = service_gross - partner
            cm2 = contribution / revenue if revenue else None
            other_opex = d['other_fixed_operating_cost_usd']
            monthly_cash_surplus = contribution - other_opex
            receivables = revenue * d['dso_days'] / 30
            refund_reserve = revenue * d['refund_reserve_rate']
            setup = d['winddown_cash_usd'] if withdrawal else d['setup_cash_usd']
            buffer = max(Decimal(0), -monthly_cash_surplus) * d['cash_buffer_months']
            return {'option': label, 'unit_price_usd': money(price), 'expected_units': rate(units),
                'revenue_usd': money(revenue), 'direct_cost_usd': money(direct), 'support_cost_usd': money(support),
                'shared_delivery_cost_usd': money(shared), 'payment_fees_usd': money(fees),
                'partner_compensation_usd': money(partner), 'partner_sourced_units': rate(units*effective_share), 'service_gross_proxy_usd': money(service_gross),
                'cm2_usd': money(contribution), 'cm2': rate(cm2) if cm2 is not None else None,
                'internal_floor_met': cm2 is not None and cm2 >= d['target_cm2'],
                'monthly_cash_surplus_proxy_usd': money(monthly_cash_surplus),
                'receivables_proxy_usd': money(receivables), 'refund_reserve_assumption_usd': money(refund_reserve),
                'planning_cash_requirement_usd': money(setup + receivables + refund_reserve + buffer),
                'regulatory_capital_usd': None, 'regulatory_status': 'not_evaluable',
                'basis': 'hypothetical operating scenario; not live revenue, GAAP financials or a regulatory calculation',
                'withdrawal_obligations_unquantified': withdrawal}

        price, qty, commission = d['unit_price_usd'], d['baseline_units'], d['commission_rate']
        naive = model('Original allocation assumption', price, qty, commission, full_cost=False)
        revised = model('Revised full-service allocation', price, qty, commission)
        new_price = price * (1 + d['price_change'])
        def demand(elasticity):
            return Decimal(str(float(qty) * math.pow(float(new_price / price), float(elasticity))))
        cut_attrition = d['partner_attrition_on_cut'] if d['new_commission_rate'] < commission else Decimal(0)
        options = [model('Reprice', new_price, demand(d['price_elasticity']), commission),
                   model('Redesign service coverage', price, qty * (1-d['coverage_volume_loss']), commission,
                         delivery_factor=1-d['coverage_cost_reduction']),
                   model('Restructure commissions', price, qty * (1-d['partner_sourced_share']*cut_attrition), d['new_commission_rate'],
                         partner_share=(d['partner_sourced_share']*(1-cut_attrition) /
                         (1-d['partner_sourced_share']*cut_attrition)) if (1-d['partner_sourced_share']*cut_attrition) else Decimal(0)),
                   model('Full withdrawal after transition', price, Decimal(0), Decimal(0), withdrawal=True)]
        for item in options:
            item['volume_change_pct'] = rate((Decimal(str(item['expected_units'])) / qty - 1) * 100)
            item['contribution_change_usd'] = money(Decimal(str(item['cm2_usd'])) - Decimal(str(revised['cm2_usd'])))
            item['partner_compensation_change_usd'] = money(Decimal(str(item['partner_compensation_usd'])) - Decimal(str(revised['partner_compensation_usd'])))
            item['planning_cash_change_usd'] = money(Decimal(str(item['planning_cash_requirement_usd'])) - Decimal(str(revised['planning_cash_requirement_usd'])))
        denominator = 1-d['payment_fee_rate']-commission*d['partner_sourced_share']-d['target_cm2']
        static_floor = ((d['direct_cost_per_unit_usd'] + d['support_cost_per_unit_usd'] +
                         d['shared_delivery_cost_usd']/qty + d['payment_fixed_fee_usd']) / denominator) if denominator > 0 else None
        sensitivity = [{'elasticity': e, **model('Reprice sensitivity', new_price, demand(Decimal(str(e))), commission)} for e in [-.3, -1, -2]]
        return {'product_id': product_id, 'name': p['name'], 'unit': p['scenario_unit'], 'status': 'illustrative_assumptions_only',
            'period': 'one month of sales/service volume; one-time orders are not MRR',
            'inputs': {key: float(value) for key, value in d.items()},
            'original_allocation': naive, 'revised_allocation': revised, 'options': options,
            'allocation_margin_change_percentage_points': rate((Decimal(str(revised['cm2'])) - Decimal(str(naive['cm2']))) * 100),
            'price_floor_at_fixed_volume_usd': money(static_floor) if static_floor is not None else None,
            'price_floor_note': 'Static contribution floor at assumed volume; excludes other operating cost and may rise if volume falls. It is not a price recommendation.',
            'demand_sensitivity': sensitivity, 'regulatory_status': 'not_evaluable', 'execution_enabled': False,
            'limitations': ['No measured price elasticity, partner attrition or coverage response; sensitivity is not a causal forecast.',
                'All default costs, cohort sizes, fee rates, reserve, DSO, setup and other operating costs are assumptions, even where the price matches an observed catalog.',
                'Shared cost remains committed in the withdrawal scenario; existing customer runoff, termination liability and released capital are not established.',
                'Planning cash is setup/wind-down + assumed receivables + reserve + cash-deficit buffer; not bank liquidity, enterprise valuation or regulatory capital.',
                'Scenarios for overlapping modules are mutually alternative commercial packages; do not sum their revenue as a portfolio forecast.']}

    def run(self, product_id=None, overrides=None, actor='founder'):
        if product_id is not None and (type(product_id) is not int or not 1 <= product_id <= 17):
            raise Invalid('Product must be an integer from 1 to 17')
        if product_id is None and overrides:
            raise Invalid('Custom inputs require one explicit product')
        source = self.source()
        products = [product_id] if product_id else list(range(1,18))
        result = {'id': uuid.uuid4().hex, 'product_id': product_id, 'created_at': now(), 'created_by': actor,
                  'policy_id': self.policy['id'], 'policy_hash': digest(self.policy),
                  'strategy_hash': digest(self.strategies), 'source_hash': source.get('snapshot_sha256'),
                  'source_captured_at': source.get('captured_at'), 'regulatory_status': 'not_evaluable',
                  'live_assessments': [p for p in self.live_assessments(source) if p['product_id'] in products],
                  'scenarios': [self.calculate(pid, overrides) for pid in products], 'execution_enabled': False,
                  'approvals': [], 'note': 'Analysis only. No pricing, product entitlement, coverage, commission or capital action is executed.'}
        with self.s.db() as db:
            self.s.save(db, 'economic_runs', result)
            self.s.audit(db, 'economics_analysis_run', result['id'], {'products': products, 'policy_hash': result['policy_hash'],
                         'source_hash': result['source_hash'], 'external_actions': 0}, actor)
        return result
