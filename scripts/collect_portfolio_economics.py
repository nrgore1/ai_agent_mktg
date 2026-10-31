"""Read-only production aggregates. No customer identifiers, payloads, or secrets exported."""
import datetime as dt, json, subprocess
from pathlib import Path
from urllib.parse import urlsplit

def sql(container,database,query):
    r=subprocess.run(['docker','exec',container,'sh','-c',
        'PGOPTIONS="-c statement_timeout=5000 -c default_transaction_read_only=on" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$1" -At -c "$2"',
        'sh',database,query],capture_output=True,text=True,timeout=20)
    if r.returncode:return {'status':'unavailable','reason':r.stderr.strip()[:180]}
    return {'status':'observed','rows':r.stdout.strip().splitlines()}

sources=[
(1,'liqmint-individual-prod-postgres-1','liqmint_individual_prod',{
 'subscription_payment_status_currency_mode':"SELECT json_build_object('status',status,'currency',currency,'livemode',coalesce(raw_payload->>'livemode','unknown'),'rows',count(*),'amount_cents',sum(amount_cents)) FROM subscriptions_subscriptionpayment WHERE created_at>=now()-interval '30 days' GROUP BY status,currency,raw_payload->>'livemode';",
 'retail_ledger_status_currency':"SELECT json_build_object('status',status,'currency',currency,'rows',count(*),'amount_usd',sum(amount_usd)) FROM rewards_retailbillingledger WHERE created_at>=now()-interval '30 days' GROUP BY status,currency;",
 'subscription_status':"SELECT json_build_object('status',status,'rows',count(*)) FROM subscriptions_customersubscription GROUP BY status;",
 'catalog':"SELECT json_build_object('key',key,'monthly_price',monthly_price,'annual_price',annual_price) FROM subscription_access_accesssubscriptionplan WHERE is_active=true;",
 'usage_30d':"SELECT json_build_object('event_type',event_type,'events',count(*),'quantity',sum(quantity)) FROM rewards_usagemeterevent WHERE created_at>=now()-interval '30 days' GROUP BY event_type;"
}),
(2,'liqmint-data-postgres-1','liqmint_institutional_prod',{
 'invoices_30d':"SELECT json_build_object('status',status,'currency',currency,'rows',count(*),'amount_cents',sum(amount_cents)) FROM subscriptions_institutionalinvoice WHERE created_at>=now()-interval '30 days' GROUP BY status,currency;",
 'contracts':"SELECT json_build_object('status',status,'rows',count(*)) FROM subscriptions_institutionalcontract GROUP BY status;",
 'catalog':"SELECT json_build_object('key',key,'monthly_price',monthly_price,'annual_price',annual_price) FROM subscription_access_accesssubscriptionplan WHERE is_active=true;",
 'usage_30d':"SELECT json_build_object('meter_key',meter_key,'events',count(*),'quantity',sum(quantity)) FROM subscriptions_institutionalusagemeterevent WHERE recorded_at>=now()-interval '30 days' GROUP BY meter_key;"
}),
(4,'weddingos-production-postgres-1','weddingos',{
 'subscription_status':"SELECT json_build_object('status',status,'rows',count(*)) FROM professional_subscriptions GROUP BY status;",
 'published_catalog':"SELECT json_build_object('key',plan_key,'name',name,'price',price,'currency',currency,'billing_period',billing_period,'status',status) FROM professional_plan_versions WHERE status='published';",
 'marketplace_payments_30d':"SELECT json_build_object('status',status,'currency',currency,'rows',count(*),'gross_minor',sum(amount_minor),'platform_fee_minor',sum(platform_fee_minor),'vendor_amount_minor',sum(vendor_amount_minor),'tax_minor',sum(tax_minor)) FROM marketplace_payment_intents WHERE created_at>=now()-interval '30 days' GROUP BY status,currency;",
 'registered_accounts':"SELECT json_build_object('all_accounts',count(*),'email_verified',count(*) FILTER (WHERE email_verified),'note','May include founder, admin or noncustomer accounts; not acquisition or paid customers') FROM user_accounts;",
 'saved_tool_results':"SELECT json_build_object('tool',tool,'saved_results',count(*),'note','Saved-result rows are not unique customers or campaign attribution') FROM free_tool_plans GROUP BY tool;"
}),
(5,'memoir-production-postgres-1','memoir',{
 'orders_30d':"SELECT json_build_object('status',status,'currency',currency,'rows',count(*),'amount_total',sum(amount_total)) FROM billing_order WHERE created_at>=now()-interval '30 days' GROUP BY status,currency;",
 'print_orders_30d':"SELECT json_build_object('status',status,'currency',currency,'rows',count(*),'amount',sum(amount)) FROM commerce_printorder WHERE created_at>=now()-interval '30 days' GROUP BY status,currency;"
}),
(6,'jodibana-db-1','jodibana',{
 'invoices_30d':"SELECT json_build_object('status',status,'currency',currency,'rows',count(*),'amount',sum(amount)) FROM saas_invoice WHERE created_at>=now()-interval '30 days' GROUP BY status,currency;",
 'catalog':"SELECT json_build_object('code',code,'name',name,'price_monthly',price_monthly,'price_yearly',price_yearly,'currency',currency) FROM saas_plan WHERE is_active=true;",
 'subscriptions':"SELECT json_build_object('active',is_active,'period',period,'rows',count(*)) FROM saas_subscription GROUP BY is_active,period;"
})]
result={'captured_at':dt.datetime.now(dt.timezone.utc).isoformat(),'window':'Rolling 30 days ending at collection; catalog and account counts are point-in-time.',
 'method':'PostgreSQL read-only transactions with 5-second statement timeout; aggregates only. No processor API, general ledger, invoices from hosting providers, payroll, or partner statements reconciled.',
 'products':[],'unavailable_product_ids':[3,7,8,9,10,11,12,13,14,15,16,17],
 'limitations':['Empty billing tables are observed empty tables, not evidence of zero business revenue.','Catalog prices are configured offers, not realized prices or revenue.','Never sum operational ledgers and payment tables: they may describe the same transaction.','Recognized revenue, processor settlements, refunds, taxes, vendor payables and test-mode exclusion require reconciliation.','No measured cost allocation, payroll, shared-host invoice, AI bill, commissions, cash balance or capital requirements were available from these aggregates.']}
for pid,container,database,queries in sources:
    row={'product_id':pid,'source_container':container,'database':database,'queries':{}}
    for label,query in queries.items():
        out=sql(container,database,query)
        if out['status']=='observed':
            out['rows']=[json.loads(x) for x in out['rows'] if x.strip()]
            out['row_groups']=len(out['rows'])
        row['queries'][label]=out
    result['products'].append(row)
out=Path('/home/liqmintadmin/portfolio-economics-aggregate.json');out.write_text(json.dumps(result,indent=2));out.chmod(0o600)
print(json.dumps(result,indent=2))
