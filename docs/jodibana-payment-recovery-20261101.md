# Jodibana failed-payment and delayed-refund recovery

1 November 2026. Recovery fixes are deployed. JodiUSA's all-feature $0 grant, existing paid prices, credentials, operator settings, consent settings, commissions and campaigns are unchanged. The proposed paid tiers remain pending approval. No full product launch approval is implied.

## Problems fixed

The previous handler acknowledged failed invoices without maintaining a local recovery state. Refund accounting assumed the cumulative refunded amount could only increase, so it could not distinguish pending refunds from settled cash or reverse a refund that subsequently failed. Paid renewals also re-enabled subscription features that an operator had disabled.

The new refund handler reads current provider refund history after locking the bound local invoice. It validates charge, payment, currency, amount and status, paginates the provider list, and records per-refund state. Only successful refunds reduce settled cash. A pending or action-required refund remains pending; a later failure or cancellation reverses any prior settlement with a new positive ledger entry. History is retained. Duplicate, concurrent and delayed events cannot duplicate the net settlement. The operator billing page shows pending refunds and failed-refund follow-up notices. A failure notice does not claim the customer received replacement funds: arranging an alternative refund remains an operator responsibility.

Failed invoice events retrieve current provider state, create or reuse the correctly bound local invoice, record retry information and show a payment-recovery notice. A successful retry settles that same invoice and clears the notice. A delayed failure cannot reopen a paid invoice. Existing access remains during the provider's `past_due` retry state; this preserves the existing policy rather than inventing a new grace period. Provider `unpaid` suspends paid entitlement without erasing operator choices. Recovery requires the current provider subscription to be active and its latest invoice paid. Canceled subscriptions, an older paid invoice and a newer chosen plan cannot be overridden by recovery. Ordinary paid renewals no longer re-enable operator-disabled features.

Provider errors or invalid bindings roll back webhook processing, allowing retry rather than recording an unprocessed event as successful. No new database migration is needed: recovery metadata, webhook records and signed ledger adjustments use the existing schema.

## Measured evidence

| Verification | Result | Scope |
|---|---|---|
| PostgreSQL regression suite | 313 passed; 0 failed/errors/skipped | Prior 188 checks; 25 new recovery/concurrency checks; 100 additional existing profile creation, completeness, owner email verification, signup-abuse, tenant-isolation and referrer-signup checks |
| Real failed renewal and retry | 8 passed | Genuine provider decline/past_due; local failed invoice; existing access retained during retry; paid recovery; warning cleared; same invoice reused; access active; disabled feature preserved |
| Real delayed refunds and redelivery | 12 passed | Pending-to-success and success-to-failure, exact ledger reversal, follow-up state, signed events, and stability after original events were resent |
| Real partial-to-full refund | 4 passed | Separate test payment: partial state, full state, exact two incremental ledger entries, no pending/failed remainder |
| Operator browser workflow | 4 passed | Failed-refund notice visible, settled pending notice removed, recovered-payment warning removed, another tenant's free billing denied |

Stripe initially reported one refund as pending and the other as succeeded. Later it reported the first succeeded and the second failed. The local system followed those transitions through the registered HTTPS callback. The failed refund retained a negative debit and one positive reversal with a zero net refund total; the successful refund settled once. Three original real provider events were redelivered after recovery without undoing it. The provider's documented test methods were used; no real money or customer email was involved.

Tests used persistent isolated PostgreSQL/pgvector, actual application migrations, production routes/middleware and ASGI, shared Redis, and a file email sink. The asynchronous refund fixtures bind genuine paid test PaymentIntents to synthetic one-time invoices: this tests refund recovery, not creation of a fresh Checkout session. The subscription fixture uses a genuine provider subscription/test clock tied to synthetic local invoice metadata; previous hosted Checkout evidence is retained separately. No provider signing bypass or CLI forwarding was used.

The final image is `sha256:99d1a54d20b8583b572f63be0fa0e0ab625233e0bec04159691265eba3c7392c`. Initial asynchronous refund events ran on an earlier candidate with identical refund implementation. Failed-renewal recovery ran after the operator-setting preservation fix; the final image adds further test files with unchanged runtime code, and reran the full 313 checks, real partial/full refund test and operator browser checks. The browser test initially expected mixed-case labels while CSS rendered uppercase; assertions were corrected to compare case-insensitively without dropping the status, notice or access checks.

## Deployment and cleanup

The Jodibana application container was replaced after passing the checks above. A database dump, stopped previous container/image and prior Compose override are retained privately on the VPS. Environment variables and data mounts were preserved. Fingerprints verified that invoices, subscriptions, active/inactive plans, platform settings, tenant settings and feature toggles were unchanged by deployment. JodiUSA's free grant was checked before and after. The tested image is persisted in the existing Compose override.

Synthetic subscriptions were canceled, their two test payments refunded, and the temporary test product/price archived. The intentionally failed refund remains a labelled failed synthetic fixture; it is not described as refunded, and no real funds are involved. The temporary webhook and proxy route were removed and test receivers stopped. Synthetic test data remains private. AgentVire, JodiUSA, Jodibana, WeddingOS and Memoire all returned HTTP 200 after cleanup.

## Gates and remaining product backlog

The supported USD single-payment refund lifecycle case is **passed**. This is a scoped technical test result, not approval to issue customer refunds. Full entitlement and launch tasks remain blocked because not all prerequisites and categories pass. Other products retain prior evidence and were not rerun. AgentVire qualification `jodibana-payment-recovery-20261101-06` granted zero full technical approvals and zero commercial approvals; all 51 commercial task records remained unchanged and the audit chain verified.

Remaining Jodibana work, kept separate from AgentVire development:

1. **P0 — production paid-payment setup:** valid production credentials, registered live signing configuration, selected Standard Checkout account/tax readiness and operational callback monitoring. No test key was installed in production.
2. **P0 — final delinquency operations:** verify the account's full retry-exhaustion sequence and chosen terminal/grace policy. Real tests covered failure/past_due and recovery; unpaid suspension/restoration and cancellation protection were covered by database tests, not a complete real provider exhaustion cycle.
3. **P0 — complete activation and feature coverage:** full profile/photo/first meaningful interaction with save/reload/logout in the browser, all current paid feature and quota boundaries, owner plan changes and customer-facing cancellation management. The added regression suite improves coverage but does not certify the entire browser journey.
4. **P0 — operational release checks:** retries/alerts, recovery procedures and remaining cross-event concurrency/order coverage. The temporary registered callback is deliberately removed after tests.
5. **Approval hold — paid tiers, commissions and campaigns:** exact owner approval plus validated cost/margin and related prerequisites. No proposed rates or campaigns activated.

Proration/repricing, multiple payments against one invoice, unsupported currencies, disputes and alternative refund disbursement are outside this tested USD subscription/refund scope; they must not be inferred from a pass here.

## Programmer notes

`saas/recovery.py` owns current-provider refund reconciliation, failed invoice state and guarded unpaid-access restoration. `saas/billing_hardening.py` dispatches `refund.created`, `refund.updated`, `refund.failed`, `charge.refunded`, and invoice events within the existing idempotent transaction. `saas/stripe_reconciliation.py` binds failed/paid renewal invoices and preserves operator choices on recoverable suspension. `console/billing.html` displays the resulting operational notices. Provider retrieval errors intentionally remain retryable; do not replace them with acknowledgement or derive settled cash from a pending refund's amount.

References: [Stripe asynchronous refund test methods](https://docs.stripe.com/testing#refunds), [failed refunds and follow-up](https://docs.stripe.com/refunds#failed-refunds), [subscription lifecycle](https://docs.stripe.com/billing/subscriptions/overview). The approval result is based on the measured evidence above.

Evidence: [recovery results](evidence/jodibana-payment-recovery-20261101.json), [qualification](evidence/jodibana-recovery-qualification-20261101.json), [AgentVire receipt](evidence/jodibana-recovery-agentvire-20261101.json).
