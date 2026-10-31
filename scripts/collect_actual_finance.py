"""Run on the VPS. GET-only processor collection; aggregate output, no identifiers exported."""
import datetime as dt
import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo


def sql(container, database, query):
    result = subprocess.run(['docker', 'exec', container, 'sh', '-c',
        'PGOPTIONS="-c statement_timeout=5000 -c default_transaction_read_only=on" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$1" -At -c "$2"',
        'sh', database, query], capture_output=True, text=True, timeout=20)
    if result.returncode:
        return None
    return [json.loads(x) for x in result.stdout.splitlines() if x.strip()]


def get(key, endpoint, params=None):
    url = 'https://api.stripe.com/v1/' + endpoint
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + key})
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)


def pages(key, endpoint, start, end):
    params = {'limit': 100, 'created[gte]': start, 'created[lt]': end}
    rows = {}
    for _ in range(100):
        data = get(key, endpoint, params)
        for row in data['data']:
            rows[row['id']] = row
        if not data.get('has_more'):
            return list(rows.values())
        if not data['data']:
            raise ValueError('Invalid pagination')
        params['starting_after'] = data['data'][-1]['id']
    raise ValueError('Collection limit exceeded; no partial totals accepted')


def collect():
    end = dt.datetime.now(ZoneInfo('America/New_York')).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - dt.timedelta(days=30)
    out = {'captured_at': dt.datetime.now(dt.timezone.utc).isoformat(),
           'period_start': start.isoformat(), 'period_end_exclusive': end.isoformat(),
           'basis': 'Completed 30-day America/New_York window; processor cash movements are not recognized revenue.',
           'processor_accounts': [], 'cost_sources': [],
           'product_status': [{'product_id': p, 'status': 'incomplete', 'actual_margin': None} for p in range(1, 18)],
           'missing': ['Recognized revenue and deferred-revenue close', 'Supplier invoices and payment reconciliation',
                       'Measured support/compliance hours and cost', 'Shared-cost allocation with pool tie-out',
                       'Partner contracts, accruals and payouts', 'Product attribution for shared processor activity']}
    services = [(1, 'liqmint-individual-prod-api-1', '/run/secrets/STRIPE_SECRET_KEY_PROD'),
                (2, 'liqmint-institutional-prod-api-1', '/run/secrets/stripe_secret_key'),
                (3, 'oratoplus-core-api-tsvalidation-1dc247b', None)]
    accounts = {}
    for pid, service, secret in services:
        row = None
        try:
            if secret:
                key = subprocess.check_output(['docker', 'exec', service, 'cat', secret], text=True).strip()
            else:
                info = json.loads(subprocess.check_output(['docker', 'inspect', service]))[0]
                env = dict(x.split('=', 1) for x in info['Config']['Env'] if '=' in x)
                key = env.get('STRIPE_SECRET_KEY', '').strip()
            if not key.startswith(('sk_live_', 'rk_live_')):
                raise ValueError('Missing live key; test mode excluded')
            account = get(key, 'account')['id']
            if account in accounts:
                accounts[account]['configured_product_ids'].append(pid)
                continue
            row = {'configured_product_ids': [pid], 'account_fingerprint': hashlib.sha256(account.encode()).hexdigest()[:16],
                   'status': 'collecting'}
            accounts[account] = row
            out['processor_accounts'].append(row)
            balances = pages(key, 'balance_transactions', int(start.timestamp()), int(end.timestamp()))
            charges = pages(key, 'charges', int(start.timestamp()), int(end.timestamp()))
            groups = defaultdict(lambda: {'count': 0, 'amount_minor': 0, 'fee_minor': 0, 'net_minor': 0})
            for b in balances:
                g = groups[(b['currency'], b.get('reporting_category', b['type']))]
                g['count'] += 1
                for field in ('amount', 'fee', 'net'):
                    g[field + '_minor'] += b[field]
            successful = [c for c in charges if c.get('livemode') is True and c.get('paid') and c.get('captured')]
            charge_groups = defaultdict(lambda: {'captured_count': 0, 'captured_minor': 0, 'refunded_to_date_minor': 0, 'disputed_count': 0})
            for c in successful:
                g = charge_groups[c['currency']]
                g['captured_count'] += 1
                g['captured_minor'] += c['amount_captured']
                g['refunded_to_date_minor'] += c.get('amount_refunded', 0)
                g['disputed_count'] += int(bool(c.get('disputed')))
            row.update(status='complete_processor_window',
                       balance_groups=[dict(currency=k[0], category=k[1], **v) for k,v in sorted(groups.items())],
                       captured_charge_groups=[dict(currency=k, **v) for k,v in sorted(charge_groups.items())],
                       balance_arithmetic_valid=all(b['amount']-b['fee']==b['net'] for b in balances),
                       attribution='Unallocated shared account; never duplicate account totals across products.',
                       settlement='Balance movements only; bank settlement and recognized revenue not reconciled.')
            # Compare references in memory on the VPS; export only counts and currency totals.
            for product, database_container, database in [(1,'liqmint-individual-prod-postgres-1','liqmint_individual_prod'),
                                                         (2,'liqmint-data-postgres-1','liqmint_institutional_prod')]:
                refs = sql(database_container, database,
                    "SELECT json_build_object('invoice',coalesce(nullif(invoice_id,''),raw_event#>>'{data,object,invoice}'),'object',raw_event#>>'{data,object,id}','intent',raw_event#>>'{data,object,payment_intent}') FROM rewards_retailbillingledger WHERE created_at >= to_timestamp(%d) AND created_at < to_timestamp(%d)" % (start.timestamp(),end.timestamp()))
                if refs is None:
                    continue
                ids = {v for r in refs for v in r.values() if v}
                matches = [c for c in successful if any(c.get(f) in ids for f in ('id','invoice','payment_intent'))]
                totals = defaultdict(int)
                for c in matches:
                    totals[c['currency']] += c['amount_captured']
                row.setdefault('local_reference_matches', []).append({'product_id': product, 'matched_captured_charges': len(matches),
                    'captured_minor_by_currency': dict(totals), 'recognized_revenue': None,
                    'note': 'Reference match is evidence of collection only; purpose, tax, pass-through and service period unverified.'})
                invoices = sorted({r['invoice'] for r in refs if r.get('invoice')})
                invoice_totals = defaultdict(int)
                invoice_count = 0
                if len(invoices) <= 100:
                    for reference in invoices:
                        invoice = get(key, 'invoices/' + urllib.parse.quote(reference, safe=''))
                        if invoice.get('livemode') is True and invoice.get('status') == 'paid':
                            invoice_count += 1
                            invoice_totals[invoice['currency']] += invoice.get('amount_paid', 0)
                row.setdefault('local_invoice_checks', []).append({'product_id': product,
                    'paid_invoice_count': invoice_count if len(invoices)<=100 else None,
                    'amount_paid_minor_by_currency': dict(invoice_totals),
                    'complete': len(invoices)<=100,
                    'note': 'Cross-check only; do not add invoices to charge totals. Payment date, service period, recognition and tax remain separate checks.'})
        except urllib.error.HTTPError as error:
            failure = {'configured_product_ids':[pid], 'status':'http_error', 'http_status':error.code}
            if row is not None:
                row.clear(); row.update(failure)
            else:
                out['processor_accounts'].append(failure)
        except Exception as error:
            failure = {'configured_product_ids':[pid], 'status':'collection_unavailable', 'error_type':type(error).__name__}
            if row is not None:
                row.clear(); row.update(failure)
            else:
                out['processor_accounts'].append(failure)
    for pid, container, database, table, amount, currency, date in [
        (5,'memoir-production-postgres-1','memoir','commerce_expense','amount','currency','date'),
        (6,'jodibana-db-1','jodibana','platform_control_expense','amount','currency','incurred_on'),
        (None,'growth-production-growth-postgres-1','growth','cost_entries','amount_usd',"'USD'",'created_at')]:
        q = "SELECT json_build_object('currency',%s,'rows',count(*),'recorded_amount',sum(%s)) FROM %s WHERE %s >= '%s' AND %s < '%s'" % (currency,amount,table,date,start.date(),date,end.date())
        if currency != "'USD'":
            q += ' GROUP BY ' + currency
        rows = sql(container,database,q)
        out['cost_sources'].append({'product_id':pid,'source_table':table,'status':'observed' if rows is not None else 'unavailable',
            'groups':rows,'interpretation':'Recorded expense aggregates only; empty records are not zero operating cost; invoices/payment and allocation unverified.'})
    out['financial_reconciled'] = False
    out['pricing_and_commission_decision'] = 'hold_for_reconciliation'
    path = Path.home()/'actual-finance-reconciliation.json'
    fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f:
        json.dump(out,f,indent=2)
    os.chmod(path,0o600)
    print(json.dumps(out,indent=2))


if __name__ == '__main__':
    collect()
