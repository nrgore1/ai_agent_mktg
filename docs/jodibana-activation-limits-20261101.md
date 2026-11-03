# Jodibana activation, catalogue access and usage limits

1 November 2026 (US Eastern). Tested fixes are deployed. Existing prices and the proposed paid-tier approval hold are unchanged. JodiUSA retains its platform-owned all-feature, zero-cost grant. No real payments, customer emails or campaigns were sent.

## Fixed behavior

1. **Finite daily limits survive display changes.** Turning off the curated daily batch no longer removes a finite commercial allowance. The existing Starter, Growth and Pro daily-like ceilings remain 8, 25 and 100. Enterprise can remain unlimited or use its optional curated batch. JodiUSA's approved grant has unlimited commercial member/like caps. This does not remove safety throttles or operator choices.
2. **Valid subscriptions determine capacity.** Inactive, future and expired subscriptions, or inactive plans, cannot supply higher limits. Stored quota metadata may lower a limit but cannot increase it above the current catalogue tier. A missing or unrecognized subscription falls back to Starter. No proposed catalogue values were introduced.
3. **Member capacity is enforced at admission.** Existing member ceilings are Starter 5,000, Growth 20,000, Pro 100,000 and Enterprise unlimited. All stored tenant member profiles count, including incomplete and suspended profiles; referrer-only accounts do not. Edits remain possible at capacity. Deleting a profile frees a slot. Registration at capacity returns an actionable message without creating an account or spending an invitation.
4. **Parallel requests cannot overspend the final slot.** A tenant-row transaction lock serializes member admissions. Profile creation, imports and individual tenant moves share the guard. Bulk tenant reassignment is rejected; use individual saves. Bulk imports are atomic and do not support conflict-ignoring upserts that bypass admission checks.
5. **Likes are consistent under retries.** A user-row lock serializes quota consumption. Repeating an existing positive like is idempotent and consumes no additional allowance. Changing a like to pass and liking again is a new positive action. Passing remains possible at the limit, uses no like allowance and invokes no compatibility model. Invalid actions are rejected. Existing mutual-match behavior is preserved.

The implementation is in `jodii_core/services/usage_limits.py`, `services/likeme.py`, `services/site_features.py`, the member manager/model and registration/swipe views. It uses the existing schema; no migration was required. The new regression file is `jodii_core/tests/test_activation_limits.py`.

## Measured checks

| Check | Result | Evidence scope |
|---|---|---|
| PostgreSQL regressions | **437 passed**, zero failures/errors/skips | Previous 313 checks plus 124 new catalogue, capacity, stale-plan, replay and concurrent-boundary checks. Includes two simultaneous attempts for the final member slot and daily like. |
| Running-service HTTP checks | **466 passed**, zero failures | Actual CSRF-authenticated HTTP through ASGI with PostgreSQL and Redis. All 27 feature keys across four existing tiers: 108 operator-toggle assertions and 108 runtime assertions. Another 249 verify quotas/admission and one verifies the free grant. |
| Full browser member journey | **17 passed**, zero failures | Two fresh registrations; incomplete-profile guidance; main and extra photo submission; profile completion; reload; discovery; likes; mutual match; persisted likes; tenant-host session separation; logout denial; fresh-session login restores the correct profile. |
| Production verification | Passed | Exact tested image, healthy service, schema check, unchanged billing/settings fingerprints, JodiUSA unlimited free grant and public HTTPS availability. |

HTTP tests exercised all 8, 25 and 100 positive-like slots, the next denied request, a repeated positive action at capacity, pass at capacity and the next-day reset. Enterprise accepted 101 likes without a commercial daily meter. A synthetic reduced member ceiling tested admission denial, preserved invitation/account state and successful signup after a profile deletion; no thousands of real or fake production customers were created.

All write tests used a separate database and synthetic `.test` identities, a local file email sink and private test storage. The full-stack image used production routes/middleware, ASGI and shared Redis. No provider payment call was made in this run. The isolated services and local tunnel were stopped after testing; synthetic evidence remains private.

The first candidate exposed a Django request-user wrapper error in the new lock; it was fixed before the clean 437-test run. Browser-harness corrections used explicit consent/navigation waits, unique member names and the actual `mutual` response field. Incomplete profiles intentionally save as drafts and return to the form with a missing-fields message; this was verified rather than changed. No failing result was approved.

## Deployment and recovery

The released image is `sha256:230e7d2ffd7d761b6a30aa321d0ad5d9db8245a13244c10f2278f82f6f831f2d`. The tested application container replaced the prior web container. Environment variables, mounts, plans, subscriptions, invoices, platform settings, tenant settings and feature switches were preserved. No billing credential was copied from the test environment. The image is pinned in the existing deployment override.

A current database dump, previous container/image and previous deployment override are retained privately on the VPS. The rollback container is `jodibana-web-1-before-activation-20261101`. Operational rollback must restore the saved container/network configuration and prior override together; do not restore an old database over later customer activity merely to roll back application code.

## AgentVire decisions

Qualification `jodibana-activation-limits-20261101-07` records scoped **usage limits** and **cross-tier denial** cases as passed. Earlier supported refund evidence is retained, not described as rerun. Other products retain their earlier results.

**Zero full launch/entitlement approvals and zero commercial approvals were granted.** All 51 commercial task records are unchanged and the audit chain verifies. The member-engineering journey passed, but Jodibana's strategy activation is `operator_demo_reviewed`: it also requires an actual community-owner review and validation plan. Automated synthetic accounts cannot stand in for that review, and the existing identity/other dependencies are not bypassed. AgentVire attaches the passing technical evidence while keeping that broader journey task blocked.

Feature tests certify catalogue access, operator control, runtime entitlement and isolation. They do **not** certify every external AI, voice/video, identity-verification, gifts or social-provider capability. Availability of a feature is not evidence that its integration or vendor account is ready.

## Remaining separate Jodibana backlog

- **P0 — operator activation:** review the synthetic community demo with the actual operator; confirm admission/safety rules and the community validation plan. Complete identity prerequisites with named evidence.
- **P0 — feature capability:** verify the required external providers and their actual configured capability, failure behavior and resource limits. This is separate from the passed feature-access matrix.
- **P0 — paid operations:** production credentials and registered signing configuration, Standard Checkout account/tax readiness, callback monitoring, full retry-exhaustion/terminal-access policy and owner plan-change/customer-facing cancellation management. Earlier test checkout, renewal and supported refund results remain valid within their stated scope.
- **P0 — operational/privacy scope:** remaining provider-history deletion, off-site recovery and retained-data reviews stay open on their existing tasks. No new compliance claim follows from these activation checks.
- **Approval hold — proposed paid tiers, commissions and campaigns:** unchanged. Exact approvals and financial/operational prerequisites are still required. No campaign or new price was activated.

Unsupported payment proration, multi-payment invoices, currencies and alternative refund disbursement remain outside the prior scoped billing certification. Test accounts do not count as customer acquisition or observed product demand.

Evidence: [test report](evidence/jodibana-activation-limits-20261101.json), [qualification](evidence/jodibana-activation-qualification-20261101.json), [AgentVire receipt](evidence/jodibana-activation-agentvire-20261101.json).
