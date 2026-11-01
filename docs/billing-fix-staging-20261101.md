# OraToPlus, Memoire and Jodibana — targeted qualification fixes

1 November 2026. **All five reported failures are fixed in candidate builds and pass their original assertions. Production deployment has not run.** Automatic approval review required explicit permission to replace the two live APIs and update Memoire's deployment setting; that approval is pending.

## Measured results

| Product | Checks passed | Evidence and limits |
|---|---:|---|
| OraToPlus | 36/36 | 15 original component checks plus 16 new database billing tests and five existing release tests. Unpaid/suspended paid eligibility is denied. Completed-but-unpaid checkout grants nothing. Signed paid and delayed-payment success, duplicate replay, missing bindings, direct mock-upgrade denial and provider-unavailable behavior covered. Actual Stripe sandbox delivery remains untested. |
| Memoire | 25/25 | 15 original component checks plus 10 PostgreSQL tests using the production custom user model. Zero, negative, nonintegral and boolean reservations fail closed; monthly resets and reservations hold a row lock. Two concurrent last-credit requests produce exactly one success. No skipped concurrency test. |
| Jodibana | 69/69 | 60 shared-engine billing tests rerun; nine read-only sandbox-preflight tests pass. **The configured Stripe test secret still returns HTTP 401.** Real checkout, webhook delivery, cancellation and refunds remain blocked. |

Total: **130 passing checks, zero final failures, zero setup errors and no skipped checks in the final runs.** Memoire/CoffeeBook share the same evidence and are not counted twice. Other products retain their prior report; they were not rerun in this targeted cycle.

An initial OraToPlus test harness used a different default release-flag setting than its existing tests expected. Restoring the established development fixture default made all five release regressions pass; no production feature flags changed. Memoire tests were also rerun with its actual custom user model. These setup adjustments did not weaken the original five failure assertions.

## Product changes and ownership

- [OraToPlus fix branch](https://github.com/nrgore1/oratoplus-monorepo/tree/codex/billing-gates-20261101), commit `a7c5e80`: only active/explicit-trial subscriptions retain paid eligibility. Checkout activation requires signed paid subscription data and customer/subscription binding. The old mock-upgrade route requires an explicit isolated-development flag and cannot be enabled in production; missing payment configuration returns unavailable instead of suggesting mock checkout. Numeric-grade gates and prices are unchanged.
- Memoire product commit `d6dd4e30`, based on deployed source `5797d869`: bounded reservations, anonymous denial, deterministic zero remaining allowance and database serialization. Its separate product backlog retains broader checkout/cancellation/refund work. The public repository's main branch is older than the deployed source; the [focused patch is published separately](https://github.com/nrgore1/memoir-platform-clean/blob/codex/quota-gates-patch-20261101/patches/20261101-illustration-quota.md) without importing unrelated unpublished migration history or environment files.
- [Jodibana sandbox branch](https://github.com/nrgore1/jodibana/tree/codex/sandbox-readiness-20261101), commit `d6178a4e`: an operator preflight reads the test key from the environment, rejects live/publishable credentials, redacts errors, checks a complete callback inventory and requires explicitly allowed HTTPS sandbox callbacks. It never creates provider objects or changes payment settings.

The payment checks follow [Stripe's fulfillment guidance](https://docs.stripe.com/checkout/fulfillment): completed checkout can precede payment completion, and delayed success needs reconciliation. Memoire uses transaction-scoped row locking as described in [Django's QuerySet documentation](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update). The tests do not constitute complete billing certification.

## Remaining holds

1. **Deployment approval:** tested OraToPlus/Memoire candidate images, protected database backups and exact runtime snapshots are ready. The intended deployment replaces only the two API containers and preserves runtime settings/data mounts with rollback. It was rejected before execution, so production images remain unchanged.
2. **Jodibana sandbox credentials:** all discovered Jodibana-specific configured/backed-up test credentials were rejected. A valid test secret and isolated callback configuration must be supplied through secure settings. The requested secret location is still pending. Live keys and dummy auto-payment are not substitutes.
3. **Full product acceptance:** complete actual provider checkout, signed callback delivery, out-of-order lifecycle handling, cancellation and full/partial refund reconciliation; close each product's journey and identity prerequisites. No complete entitlement task is approved by this fix report.
4. **Separate product backlog:** source review also found Memoire's no-provider immediate-activation fallback and local-only cancellation path. These are additional product billing blockers, not silently treated as cleared by quota fixes. OraToPlus concurrent webhook idempotency and refund reconciliation also remain separate work.

AgentVire records the latest candidate evidence for all 17 products while retaining production, provider and prerequisite holds. The 51 commercial task records are unchanged. No payments, refunds, campaigns, partner commissions or outbound messages were executed.

Evidence: [staging results](evidence/billing-fix-staging-20261101.json), [all-product qualification report](evidence/billing-fix-qualification-20261101.json). Both retain explicit staging-only status and zero complete-task approvals.

AgentVire update verified: report `wave-billing-fixes-20261101-02`, all 17 products, valid audit chain, zero complete technical approvals and all 51 commercial tasks unchanged. The 16 qualification/finance safeguard regression tests passed again. [Update receipt](evidence/billing-fix-agentvire-update-20261101.json).

Latest follow-up: [Approved production deployments and Jodibana sandbox results](billing-deployment-sandbox-20261101.md). OraToPlus/Memoire deployment and sandbox-credential holds are cleared. Jodibana recurring billing and refund reconciliation remain measured failures; all commercial task states are unchanged. Earlier evidence above is historical.
