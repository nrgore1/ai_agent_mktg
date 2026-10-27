import subprocess,json
from pathlib import Path
q="""
WITH r AS (
 SELECT *, coalesce(nullif(invoice_id,''),raw_event#>>'{data,object,invoice}') AS invoice_ref,
 raw_event#>>'{data,object,id}' AS object_ref,
 raw_event#>>'{data,object,payment_intent}' AS payment_intent_ref
 FROM rewards_retailbillingledger
 WHERE created_at>=now()-interval '30 days'
 AND coalesce(raw_event->>'livemode',raw_event#>>'{data,object,livemode}')='true'
), invoices AS (
 SELECT currency,invoice_ref,max(amount_usd) amount,count(distinct amount_usd) amount_variants
 FROM r WHERE event_type IN ('invoice.paid','invoice.payment_succeeded') AND status='paid'
 AND invoice_ref IS NOT NULL GROUP BY currency,invoice_ref
), intents AS (
 SELECT r.currency,r.object_ref,max(r.amount_usd) amount,count(distinct r.amount_usd) amount_variants
 FROM r WHERE r.event_type='payment_intent.succeeded' AND r.status IN ('paid','succeeded')
 AND r.object_ref IS NOT NULL AND r.invoice_ref IS NULL
 AND NOT EXISTS (SELECT 1 FROM r i JOIN invoices v ON i.invoice_ref=v.invoice_ref
                 WHERE i.payment_intent_ref=r.object_ref)
 GROUP BY r.currency,r.object_ref
)
SELECT json_build_object('kind',kind,'currency',currency,'distinct_events',count(*),
 'candidate_successful_event_amount_usd',sum(amount),'conflicting_amount_groups',count(*) FILTER (WHERE amount_variants>1))
FROM (SELECT 'invoice' kind,* FROM invoices UNION ALL SELECT 'standalone_payment_intent' kind,* FROM intents) x GROUP BY kind,currency;
"""
cmd=['docker','exec','liqmint-individual-prod-postgres-1','sh','-c','PGOPTIONS="-c statement_timeout=5000 -c default_transaction_read_only=on" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d liqmint_individual_prod -At -c "$1"','sh',q]
r=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=20)
rows=[json.loads(x) for x in r.stdout.splitlines() if x.strip()]
p=Path('/home/liqmintadmin/portfolio-economics-aggregate.json');data=json.loads(p.read_text())
data['reconciliation']={'product_id':1,'method':'Live-mode invoice settlement events deduplicated by invoice; standalone successful payment intents deduplicated by object, excluding invoice-linked intents. Identifiers remain on source system.',
 'rows':rows,'status':'candidate_events_not_financial_reconciliation',
 'remaining_checks':['Processor settlement and refund reconciliation','Revenue recognition and deferred revenue','Proof each reference is genuine customer activity, not controlled live-mode testing','Classify standalone payment purpose; exclude pass-through customer funds','Resolve fees, tax, support and shared infrastructure costs'],
 'naive_paid_and_succeeded_event_sum_usd':696.95}
p.write_text(json.dumps(data,indent=2));print(json.dumps(data['reconciliation'],indent=2))
