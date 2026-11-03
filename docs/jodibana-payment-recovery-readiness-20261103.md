# Jodibana payment recovery and live readiness — 3 November 2026

## Current result

Staging passed; production deployment awaiting approval. The restricted Stripe live key authenticated to the expected Jodibana account. A live webhook and restricted customer portal were created. Stripe reports charges disabled, payouts disabled and account details not submitted. Business onboarding remains an owner task. No real payment, paid tier or campaign was activated. JodiUSA retains all features at no cost.

Owner commercial approval remains **approved subject to all gates**. This is not a full launch approval. Product changes are tracked in Jodibana's separate backlog; AgentVire records evidence and retains unresolved gates.

## Changes

- Reconcile retry schedules arriving through `invoice.updated`, using current Stripe invoice state. Late updates cannot reopen paid invoices.
- Reconcile provider terminal invoice events without claiming payment.
- Prevent the local overdue-invoice command from writing off Stripe-owned debt.
- Require explicit live collection enablement, live keys, signing secret, Standard Checkout, restricted portal and secure site origin before creating live Checkout or payment intents.
- Add `python manage.py payment_readiness --provider`: read-only configuration, live-account capability, webhook coverage and portal verification. It reports a blocked result while collection is intentionally disabled or provider prerequisites fail. It never enables collection or makes a payment.
- Replace the misleading Google-storage startup instruction with provider-neutral persistent-volume guidance. No Google Cloud service was configured or used.

## Verification

540 tests passed with PostgreSQL in an isolated environment without provider credentials or production data. The first run passed 538 and failed two stale photo-publication expectations; the rerun used tests shipped with the current production moderation code and passed all 540. No moderation behavior was weakened.

14 real Stripe test-mode recovery checks passed. The corrected payment method recovered naturally on attempt two. The persistently failing subscription reached nine attempts, then Stripe canceled it; Jodibana removed access and retained the unpaid invoice as open debt. Genuine signed `invoice.updated` delivery reconciled current schedules and preserved paid status. This is evidence for the observed account policy, not every possible retry policy.

Six explicit cleanup checks passed. Only paid synthetic invoices were refunded ($147 total test money); the remaining test debt was explicitly voided after recording the natural outcome. Temporary callback and proxy route were removed, isolated services stopped, and five public sites returned HTTP 200. No cancellation was treated as an automatic refund.

## Live configuration

Key name: `Jodibana VPS billing 2026-11-03`. Read permissions: Accounts, Balance, Charges and Refunds, Invoices, Prices, Subscriptions. Write permissions: Checkout Sessions, Customer Portal, Payment Intents, Webhook Endpoints. Zero connected-account or payout permissions. Credentials are outside source control in private VPS files.

Webhook: `https://jodibana.com/saas/webhooks/stripe/`. Required events cover checkout completion/async success, paid/failed/updated/voided/uncollectible invoices, subscription updates/deletion and refund/charge reconciliation. The live signing secret is separate from test credentials.

Customer portal permits payment-method changes and cancellation at period end without proration. Plan changes, customer-detail changes and invoice history are disabled. The application creates each session with its verified tenant-specific billing return URL; the portal default returns to the public home page.

`STRIPE_STANDARD_CHECKOUT=true`, `STRIPE_TEST_STANDARD_CHECKOUT=false`, `STRIPE_LIVE_PAYMENTS_ENABLED=false` are the intended production settings. Configuring a key does not constitute launch approval or enable collection.

## Remaining gates

- Complete Stripe business/account onboarding; verify charges, payouts and details-submitted flags afterward. Review operator tax and business settings.
- Verify genuine live signing delivery when an appropriate live event is available; synthetic test delivery is not presented as live-delivery proof.
- Validate exact live offers, price mappings, cost/margin evidence, commissions and recipient eligibility before enabling collection or campaigns.
- Continue separate provider/AI quality, operator/privacy and backup recovery work. This payment result clears none of those gates.
- Confirm full plan-change/proration behavior and alternative account retry policies if offered.

## Release and rollback

The release overlays only billing/readiness changes on the current production image, preserving the newer photo moderation implementation. The tested image identifiers and base image are in the evidence JSON. A database dump, original container configuration, original service/environment files and rollback container/image are retained privately. No schema migration is required. Deployment verification checks service health, unchanged billing/settings records, JodiUSA free access and blocked live collection.

Detailed evidence: `jodibana-payment-recovery-readiness-20261103.json` (AgentVire: `docs/evidence/`).
