# Approved billing fixes deployed; Jodibana sandbox qualification

1 November 2026. This supersedes the deployment/credential holds in the [earlier staging report](billing-fix-staging-20261101.md). It does not certify full launch readiness.

## Production outcome

The owner explicitly approved both deployments. OraToPlus and Memoire now run the exact tested images. Health checks return 200; protected billing endpoints reject unauthenticated access with 401. File hashes match the tested fixes. Runtime settings and data mounts were preserved, with no database migration. Protected database backups, stopped prior containers and rollback images remain available. Memoire's deployment override points to its new image.

OraToPlus has 36 passing checks and Memoire 25, including real PostgreSQL tests and Memoire's concurrent last-credit check. These tests ran on isolated candidates; after deployment we verified image identity, file hashes, health and access denial rather than exercising customer data. All five originally reported failures are resolved and deployed. CoffeeBook shares Memoire's result without double counting.

The first OraToPlus attempt rolled back automatically because the verifier used the website host instead of the API host. After correcting the health URL to `https://api.oratoplus.com/v1/health`, both approved deployments succeeded. No unresolved rollback or outage remains in this evidence.

## Jodibana sandbox outcome

The owner-supplied test credentials authenticate successfully. They are stored in protected VPS files, used only by an isolated test environment; the production key and image remain unchanged. No secret or private checkout URL is included here.

Three sandbox compatibility fixes were made on [Jodibana's separate branch](https://github.com/nrgore1/jodibana/tree/codex/sandbox-readiness-20261101): remove the rejected checkout payment-method parameter; explicitly opt into Standard Checkout only with a test key for this fixture; convert verified Stripe SDK events with `to_dict()` and reject verifier errors instead of falling back to unverified JSON. The Standard Checkout override defaults off and refuses live keys. It does not alter the account's Managed Payments default or assign a tax category.

**68/68 candidate regression tests pass**, with no skips or errors. The earlier nine unchanged preflight unit tests remain historical evidence, not newly rerun. New real-provider checks confirm:

- A hosted test-card payment succeeds and activates the matching synthetic plan, ending its prior plan.
- Unpaid and expired checkouts preserve the existing plan.
- Stripe CLI delivers actual signed checkout, expiration and refund events; invalid signatures are rejected.
- A locally signed replay of the actual event is idempotent.
- Test partial/full refunds, a provider authorization cancellation and a provider decline work. Provider-only operations do not certify application lifecycle behavior.

Two measured product checks **fail and remain blocked**:

1. The current monthly Growth path creates a one-time payment instead of a recurring subscription when no recurring price is configured.
2. Full refund succeeds at Stripe and its event is persisted, but the application invoice remains paid without a refund ledger action. The subscription remains active; access after refunds needs an explicit product policy.

Managed Payments eligibility/tax configuration, recurring lifecycle and end-of-period cancellation, out-of-order/concurrent events, full tenant/login routing, paid feature quotas and JodiUSA-specific acceptance remain on the product backlog. The browser return navigation was not certified. The test environment used synthetic SQLite data and reduced routes without tenant/auth middleware; the successful payment does not imply those omitted gates passed. The registered-callback preflight remains a separate mode: this run used authenticated Stripe CLI forwarding, with no Dashboard callback created.

All owned open test sessions were expired, remaining owned test-payment amounts refunded, and temporary listener/API containers stopped. Protected sandbox configuration and evidence remain for follow-up. No live funds, customer records or commercial campaigns were used.

## AgentVire decision

Report `wave-billing-deployed-20261101-03` covers all 17 products. Other products retain their prior evidence and were not rerun. The audit chain is valid, all 51 commercial task records are unchanged, and **zero complete technical tasks or commercial actions were approved**. No product meets every category and prerequisite yet. Jodibana's two measured failures are explicitly recorded as failures, not partial passes.

Evidence: [deployments and sandbox checks](evidence/billing-deployment-sandbox-20261101.json), [all-product qualification](evidence/billing-deployed-qualification-20261101.json), [AgentVire update receipt](evidence/billing-deployed-agentvire-update-20261101.json). Category counts overlap and must not be summed as unique tests.

Reference: Stripe's [SDK resource conversion](https://github.com/stripe/stripe-python#working-with-api-resources), [dynamic payment methods](https://docs.stripe.com/payments/payment-methods/dynamic-payment-methods), [test event forwarding](https://docs.stripe.com/cli/listen) and [Managed Payments eligibility](https://docs.stripe.com/payments/managed-payments/eligibility). The test result, not these documents alone, determines each gate.

Final verification: all 16 AgentVire qualification/finance safeguard tests pass. Jodibana candidate commit `418a6b82` is published on its separate branch; it is not deployed to production.
