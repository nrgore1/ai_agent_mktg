# Jodibana recurring billing and refund reconciliation

1 November 2026. Both failures in the prior sandbox report are fixed in the separate product candidate. Production is unchanged; no public pricing, commissions or campaigns were activated.

## Implementation

- Subscription invoices carry an explicit monthly/yearly interval. Checkout uses subscription mode and an inline recurring price at the existing server-side catalog amount. Existing configured recurring prices are accepted only if amount, currency and interval match. Unsupported intervals fail closed. This fixes recurring behavior without changing rates or silently treating a monthly plan as a one-time purchase.
- Checkout binds provider subscription, invoice and payment IDs to the local invoice and tenant. Invoice-paid events create separate local renewal invoices. Unsupported repricing/proration is held for separate handling rather than inferred.
- Partial/full charge refunds use immutable provider relationships, a cumulative per-charge high-water mark and locked invoice rows. Negative refund ledger entries account for each new increment exactly once. Invoice states become partially refunded/refunded. Refund-before-checkout, stale partial events and duplicate delivery cannot erase a refund or duplicate its accounting.
- Refunds do not implicitly cancel subscriptions. Scheduled cancellation retains paid access; explicit provider cancellation deactivates the subscription and its owned features. Late payment/status events do not reactivate a canceled subscription. The customer-facing cancellation UI and natural end-of-period expiry remain separate acceptance work.
- Verified Stripe SDK event conversion uses JSON-safe output, including decimal-valued price fields. A real renewal test exposed this issue; it was fixed before the final fresh lifecycle run. Verifier failures continue to fail closed.

## Measured final results

**90/90 PostgreSQL tests passed, zero failures/errors/skips.** Includes three concurrent refund scenarios: same event twice, different events for the same cumulative full refund, and competing partial/full refunds. PostgreSQL ran in a disposable internal network with no provider credentials or production data. The concurrency test is mounted alongside the candidate; its SHA-256 is recorded separately.

**8/8 real provider lifecycle assertions passed** on the final candidate: monthly renewal payment; separate local renewal invoice; partial refund; full refund and ledger totals; refund preserves subscription; scheduled cancellation preserves access; explicit cancellation reconciles; renewal refund binds to its own invoice. Stripe's test clock generated the renewal. Actual events arrived through the authenticated Stripe CLI and were processed by the application's signature-verifying handler.

Initial monthly hosted payment was independently confirmed at Stripe and in the local database. An annual checkout used subscription mode, yearly interval and the existing annual catalog amount; it remained inactive while unpaid and was expired. No annual payment was submitted. Browser return navigation was not certified.

The live provider fixture uses synthetic SQLite data and reduced routes without tenant/auth middleware. The PostgreSQL suite separately exercises database behavior; neither implies complete end-to-end tenant acceptance. The account's sandbox Standard Checkout override remains explicit; Managed Payments default and tax configuration are not certified.

All owned test subscriptions were canceled and outstanding test payments refunded. Test clocks and protected evidence are retained for inspection; receivers were stopped. No live funds or customer records were touched.

## Remaining release gates

1. Full tenant/login/return flow, cross-tier usage limits, operator controls and JodiUSA-specific acceptance.
2. A protected registered staging HTTPS callback and operational retry monitoring. This test used Stripe CLI forwarding.
3. Natural period-end cancellation, renewal failure/dunning recovery, pending/failed refund recovery and exhaustive cross-event concurrency/ordering. Current tests do not certify these cases.
4. A versioned owner-controlled grant making JodiUSA eligible for all available features at no charge, including negative tests preventing other tenants from acquiring that grant. The owner's requested exception is reflected in a private pricing proposal; it has not changed live entitlements.
5. Actual unit cost/support measurements, margin validation, provider/tax setup, deployment review and broader launch prerequisites. Existing prices and campaigns remain unchanged.

The new migration `saas.0004_invoice_refund_status` adds invoice status choices. It is included in the candidate and must be applied through the normal production migration process when deployment is separately authorized; this run did not migrate production.

AgentVire report `jodibana-recurring-refunds-20261101-04` records all 17 products, retaining other products' earlier evidence. Both known failures are cleared to partial category coverage; zero complete entitlement tasks or commercial actions were approved because remaining gates are open. All 51 commercial task records and the strategy revision are unchanged; the audit chain is valid. The detailed tenant pricing proposal is a private, non-executing AgentVire artifact, not a public catalog change.

References: [Stripe recurring Checkout](https://docs.stripe.com/api/checkout/sessions/create), [invoice/payment relationships](https://docs.stripe.com/api/invoice-payment/list), [test clocks](https://docs.stripe.com/api/test_clocks/create), and [JSON-safe SDK conversion](https://github.com/stripe/stripe-python#working-with-api-resources). Gate decisions are based on measured evidence, not documentation alone.

Evidence: [final test results](evidence/jodibana-recurring-refunds-20261101.json), [all-product qualification](evidence/jodibana-recurring-qualification-20261101.json), [AgentVire receipt](evidence/jodibana-recurring-agentvire-20261101.json). Product code remains on the [separate Jodibana branch](https://github.com/nrgore1/jodibana/tree/codex/sandbox-readiness-20261101).
