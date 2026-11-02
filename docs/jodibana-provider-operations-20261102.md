# Jodibana provider integrations and payment operations

2 November 2026 UTC (1 November US Eastern). Verified product fixes are deployed. Proposed paid tiers, commissions and campaigns remain pending approval. JodiUSA retains its all-feature, zero-cost grant. Product implementation and unresolved launch work remain on Jodibana's separate backlog.

## Released behavior

- Billing APIs and the legacy billing page use organization membership permissions. A stale primary tenant or bare staff flag cannot grant cross-tenant billing access. The owner wallet now serializes the actual stored fields instead of raising an error for a nonexistent balance field. Tenant billing status no longer exposes global webhook counts.
- Tenant locking prevents parallel subscription checkout creation. An existing recurring agreement blocks another checkout. A valid open session for the same plan and period is reused; a different plan is blocked until the pending session is resolved. Expired sessions can be retried. Canonical provider metadata must match the tenant and invoice. Provider errors fail closed. Opening an unpaid checkout does not grant paid access.
- A billing owner can open a restricted Stripe portal only when its explicit configuration is present and validated. The subscription/customer binding must be tenant-specific. Cancellation must occur at the period end without proration; repricing, invoice-history and customer-identity editing must be disabled. Return and destination URLs are checked. JodiUSA's free grant cannot create a portal session. Opening the portal does not change entitlement.
- The actual browser exposed a content-policy restriction that blocked Stripe redirects. Only billing pages now allow form navigation to the exact Checkout and billing portal origins; other pages retain their existing restriction.
- Actual provider events exposed cancellation represented by a `cancel_at` timestamp while `cancel_at_period_end` was false. Both representations now produce a scheduled-cancellation notice without removing already-paid access. A signed terminal event ends entitlement. Scheduling cancellation is not a refund.
- Missing Postmark/Telegram credentials no longer report a successful real delivery. An explicitly requested dry run remains a labelled simulation. Telegram ingestion rejects missing configuration or a wrong shared secret and reports the authenticated, unfinished ingestion path as unavailable. Unsafe group-name tenant inference and unlinked media ingestion were removed. This is fail-closed behavior, not completed Telegram support.

Implementation: `saas/payment_operations.py`, billing services/views/serializers and reconciliation, console routing/template, browser policy, and provider integration helpers. Regression coverage is in `jodii_core/tests/test_provider_operations.py` with existing billing tests retained. No schema migration was required.

## Measured verification

| Check | Result | Scope |
|---|---|---|
| PostgreSQL regression suite | **518 passed**, no failures/errors/skips | Final deployed image; billing, activation, limits, provider errors, authority, portal configuration, binding and cancellation representations. |
| Actual running-app HTTP | **12 passed** | Signed initial payment, owner wallet, cross-tenant denial, subscription/checkout reuse and expiry, parallel-plan denial, unpaid-access denial, stale-authority denial and unavailable Telegram. |
| Actual owner browser | **7 passed** | Final image: billing page, scheduled-cancellation notice, portal button, tenant isolation, actual redirect and hosted subscription content. |
| Genuine signed cancellation callbacks | **8 passed** | Four scheduling and four terminal assertions through a registered HTTPS test endpoint. Current paid access remains until test-clock period end; then access ends, no renewal invoice is created and no automatic refund is asserted. |
| Production release | Passed | Exact image healthy, no pending schema changes, unchanged billing/settings fingerprints, preserved JodiUSA grant and public HTTPS availability. |

The 12 HTTP assertions ran on the preceding candidate before the final cancellation-timestamp change; their checkout and authorization paths were unchanged. All 518 regressions, seven owner-browser assertions and eight signed cancellation assertions ran against the final image. Previous usage-limit, cross-tier and supported refund evidence is retained with its original scope; other products were not retested in this increment.

The portal cancellation was genuinely confirmed in the hosted test UI. An owned synthetic subscription then received a metadata-only update to trigger a fresh genuine signed event after the timestamp fix. The test clock advanced past the paid period and the provider's natural terminal event removed access. No fabricated signature or callback-forwarding surrogate was used.

## Provider readiness and remaining gates

| Capability | Evidence and decision |
|---|---|
| Postmark | Configured production server authentication returned 200. One synthetic message to Postmark's documented discard recipient was accepted with ErrorCode 0 and a message ID. This verifies authentication/acceptance, not inbox placement. No person received it. |
| Production Stripe | Configured credential is an invalid test key (read-only account check returned 401). Production signing and explicit portal configuration are absent. **Blocked**; no production credential or portal was enabled. Valid test credentials remained in isolated QA. |
| Local AI | Actual deployed local-only adapter returned a labelled stub, not a model answer. A separate already-loaded Kimi candidate timed out after 45 seconds on a tiny synthetic request. **Failed gate**; no cloud fallback or model replacement was enabled. |
| Hosted payment-method entry | The actual Add payment method screen opened but no usable input fields rendered in the automated run. **Not passed**; investigate the hosted UI and complete a real test-card update/recovery. No claim of a CAPTCHA cause or completed payment-method recovery. |
| Voice/video | TURN URL/shared-secret configuration absent. Signalling regression tests do not establish cross-network media reliability. **Blocked**. |
| Telegram | Bot token absent, no mappings, authenticated ingestion unfinished. Fail-closed tests pass; integration readiness **blocked**. |

The restricted portal follows Stripe's [session](https://docs.stripe.com/api/customer_portal/sessions/create) and [configuration](https://docs.stripe.com/api/customer_portal/configurations/create) APIs. The discard-message test follows [Postmark's testing guidance](https://postmarkapp.com/support/article/1213-best-practices-for-testing-your-emails-through-postmark); it consumes a test message credit and proves no recipient inbox outcome.

## Deployment, cleanup and recovery

Released image: `sha256:c5c0723bfea7728d5c3c22f19c897b6189007ab3f8ce89bfbb27445745fd3aed` (tag `jodi-provider-ops:20261102`). The production application is healthy and the image is pinned in the existing deployment override. Environment variables, mounts, existing plans, invoices, subscriptions and tenant/platform settings were preserved. Standard Checkout remains selected. There were no new prices, commissions, campaigns or schema migrations.

A database dump, previous container configuration and deployment override are retained privately on the VPS. The rollback container is `jodibana-web-1-before-provider-ops-20261102`, with prior image `sha256:230e7d2ffd7d761b6a30aa321d0ad5d9db8245a13244c10f2278f82f6f831f2d`. Roll back the application and override together; do not overwrite later customer activity by restoring an old database merely to revert code.

All payment mutations used the test account and synthetic identities. After cancellation assertions, a separate explicit cleanup action refunded the single synthetic $49 payment; no real funds moved. Owned unused sessions expired and the owned fixture price/product were archived. Five provider-created inline price/product pairs are immutable and remain as provider history. The default test portal configuration cannot be deactivated while it is the default, so it remains in the test account. Neither retention represents a production offer or approval.

The temporary registered callback was deleted, its exact proxy route removed, isolated app/database/Redis services stopped and local tunnel closed. Synthetic private evidence remains outside the published reports. AgentVire, JodiUSA, Jodibana, WeddingOS and Memoire public HTTPS checks returned 200.

## AgentVire decisions and separate product backlog

Qualification `jodibana-provider-ops-20261102-08` records the supported cancellation case as passed. The paid-tier case explicitly fails the measured local-AI gate. Checkout/webhook operations remain partial. Previously passed usage/cross-tier and supported refund cases retain their original evidence. Other product results are unchanged.

**Zero full technical approvals and zero commercial approvals were granted.** All 51 commercial task records are identical and the audit chain verifies. Passing scoped checks does not bypass actual operator-demo review, identity/privacy prerequisites or the unresolved provider gates.

1. **P0: production payment readiness.** Replace invalid credentials through protected configuration, register and verify signing, confirm Standard Checkout account/tax readiness, configure the restricted portal and test delivery monitoring. Do not use QA credentials in production.
2. **P0: payment recovery.** Complete hosted card replacement, retry exhaustion and terminal-access policy, alerts/reconciliation operations and remaining owner plan-change/repricing scope. Cancellation is certified only within the supported current-tier/USD test scope; proration, multi-payment invoices and alternative refund disbursement remain outside it.
3. **P0: actual local AI.** Configure a functioning local provider, measure useful answers and failure/timeout behavior, and repeat the required feature checks. A stub cannot satisfy the gate.
4. **P0: required feature providers.** Configure/test TURN with real cross-network media. Complete Telegram ingestion/mappings/authentication and resource controls if launch scope requires it; otherwise explicitly disable it in that scope.
5. **P0: owner and operational prerequisites.** Actual community-owner demo review/validation, identity prerequisites, provider-history deletion, off-site recovery and retained-data review remain open on their existing separate tasks.
6. **Approval hold:** proposed paid tiers, commissions and campaigns remain pending. No marketing launch was executed.

Evidence: [test report](evidence/jodibana-provider-operations-20261102.json), [qualification](evidence/jodibana-provider-qualification-20261102.json), [AgentVire receipt](evidence/jodibana-provider-agentvire-20261102.json).
