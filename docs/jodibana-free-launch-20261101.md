# JodiUSA free access and Jodibana launch verification

1 November 2026. JodiUSA's owner-authorized free all-feature grant is deployed. Standard Stripe Checkout is selected explicitly. The proposed paid tier structure is still pending approval; existing paid catalog prices, commissions and campaigns were not changed.

## What is live

The platform owns a versioned grant tied to the reviewed tenant ID, organization ID, creation timestamp and verified domain. A tenant cannot obtain it by choosing a similar name/domain, copying tenant settings or buying the hidden complimentary plan. JodiUSA has all 27 current catalog features available at $0, with no commercial user/like cap. Catalog additions are included through the shared feature catalog. Availability does not override platform safety controls, operator-disabled features, optional-feature defaults or marketing consent acceptance. These remain independent controls.

The old JodiUSA subscription had a verified DummyProvider invoice, not a Stripe agreement. It was replaced with one active non-purchasable $0 plan, with an audit event. Unknown references or real provider relationships block conversion. No invoice was created and no live provider API call was made. All existing feature and tenant-setting records were checked unchanged, as was the active paid catalog.

Free tenants bypass paid checkout, and the operator billing page displays “All features included — $0”. Paid tenants cannot buy the hidden plan. Feature enforcement now requires a valid plan entitlement as well as an enabled switch; previously the switch alone could enable a paid capability. Expired plans, revoked grants and suspended tenants do not retain the grant. Cross-tenant billing and feature controls remain isolated.

The owner selected Standard Checkout. `STRIPE_STANDARD_CHECKOUT=true` explicitly disables account-default Managed Payments for checkout creation. This does not assert completed tax configuration or activate a proposed price. Missing webhook verification configuration now returns 503; unsigned delivery is restricted to the explicitly enabled development-only path.

## Measured tests

- **188 PostgreSQL tests passed**, zero failures, errors or skips on the final image. Includes free-grant identity and revocation, verified dummy conversion, real/unknown agreement protection, free checkout, paid feature denial, consent, tenant isolation, registration, recurring billing, refunds and concurrent refund accounting. The regression database used an internal network with no production data or provider credentials.
- **Five browser checks passed** on the final candidate: owner login and $0 billing, hidden paid checkout for JodiUSA, other-tenant billing denial, member-host console isolation, and invitation signup reaching profile setup. A consumed single-use invitation was correctly rejected; the final signup rerun used a fresh invitation. Reaching profile setup does not certify the complete profile/photo/first-match journey.
- Full-stack staging used actual database migrations on PostgreSQL with pgvector, the production middleware/routes and ASGI server, and shared Redis. The fixture used local-only HTTP cookies through an SSH tunnel and a private file email sink. It was not a production email-delivery test. The synthetic database's libc collation warning is a fixture limitation and is not production migration evidence.
- A real hosted Standard Checkout test payment returned to the application and was activated through a registered HTTPS Stripe callback. No CLI event forwarding was used. A failed initial delivery before the router reload was retried by Stripe and then reconciled. Unsigned requests returned 400.
- **Eight actual provider lifecycle assertions passed:** paid monthly renewal, separate renewal invoice, partial refund, full refund with exact negative ledger total, refund preserves subscription, scheduled cancellation preserves paid access, explicit cancellation deactivates access, and renewal refund updates its own invoice. These were run on the same runtime before the narrowly scoped legacy-dummy conversion addition; the final image reran the complete 188 regression suite and a fresh hosted payment and natural-expiry scenario.
- **Four natural-expiry assertions passed** on the final image: provider cancellation at period end, local access deactivation, removal of the paid tier, and recorded signed deletion. Annual checkout used the existing yearly interval and amount; unpaid checkout did not activate access and was expired.

The deployed image is `sha256:feb92a913d61c25af3563081e86338f1d8313e21d06693b76bba05ea92007f1c`. The prior image/container, database dump and previous Compose configuration are retained privately on the VPS. The existing Compose override pins the tested image and Standard Checkout setting for subsequent deployments. Production media mounts, credentials and other settings are retained. The single invoice-status migration was reviewed and applied explicitly after the final check found automatic startup migrations disabled. Jodibana and JodiUSA health checks passed after deployment.

All owned test subscriptions were canceled and outstanding test payments refunded. The temporary registered callback and route were removed and test services stopped. Synthetic data and receipts remain private. AgentVire, JodiUSA, Jodibana, WeddingOS and Memoire returned HTTP 200 after cleanup. No live payment, customer email, commission or campaign was executed.

## Remaining launch gates

| Priority | Separate Jodibana work | Acceptance condition |
|---|---|---|
| P0 | Production paid-provider configuration | Valid production credentials and registered production signing configuration; selected Standard Checkout confirmed; tax/account prerequisites reviewed. Test credentials were not copied into production. |
| P0 | Failed renewal and recovery | Exercise actual decline, retry/recovery and final delinquency; define and verify the grace/access policy and operational notification behavior. |
| P0 | Asynchronous refund recovery | Exercise pending-to-success and failed/reversed refunds, reconcile final balances, and verify refund-event ordering. Synchronous refund success is not proof of these cases. |
| P0 | Feature and quota matrix | Complete paid tier boundaries, all protected endpoints and feature journeys. The free grant makes capabilities available; it does not prove every external integration is configured. |
| P0 | Activation and self-service billing | Complete profile/photo/first meaningful interaction; owner-initiated plan changes and customer-facing cancellation/refund management. |
| P0 | Operational acceptance | Monitoring and retry alerts, full cross-event ordering, recovery evidence and broader product-owned launch prerequisites. |
| Approval hold | Proposed paid tiers, commissions and campaigns | Owner approval plus validated costs/margins and all relevant launch gates. Existing values remain unchanged. |

AgentVire qualification `jodibana-free-launch-20261101-05` retains other products' prior evidence and records partial coverage for Jodibana. Zero full technical approvals and zero commercial approvals were granted; all 51 commercial task records remained unchanged and the audit chain verified. A separate readiness artifact records the completed free-grant deployment and remaining work. The earlier private paid-pricing proposal is retained, not activated.

Implementation belongs to the separate Jodibana repository/branch. AgentVire stores evidence and launch status, not product code. Earlier reports are historical and are superseded only where this report explicitly records new results.

Provider references: [Stripe test environments and test payment methods](https://docs.stripe.com/testing), [recurring Checkout](https://docs.stripe.com/api/checkout/sessions/create), and [test clocks](https://docs.stripe.com/api/test_clocks/create). Approval decisions rely on measured results above.

Evidence: [test/deployment results](evidence/jodibana-free-launch-20261101.json), [qualification](evidence/jodibana-free-qualification-20261101.json), [AgentVire receipt](evidence/jodibana-free-agentvire-20261101.json).
