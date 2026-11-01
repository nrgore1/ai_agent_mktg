# All-wave tier and billing qualification — 1 November 2026

This release tests existing deployed behavior and records technical readiness. It does not activate recommended prices, partner terms, paid campaigns, refunds, charges or public launches. Product fixes remain in the [separate product backlog](product-billing-backlog-20261101.md).

## Results

203 unique product component tests ran against six deployed images: **198 passed, five failed, zero remaining setup errors**. CoffeeBook references Memoire's results without counting another suite. This is selected component coverage, not full product certification.

| Wave | Product | Measured result | Remaining acceptance |
|---|---|---|---|
| 1 | LiqMint Individual | 17/17 selected billing and wallet-entitlement tests pass | Current catalog/browser journey, concurrent quota enforcement, provider sandbox checkout, signed delivery, cancellation and full/partial refund reconciliation |
| 1 | LiqMint Institutional | 85/85 selected billing, wallet quota and refresh tests pass | Same provider/browser gates; temporary isolated report directory was needed for two offboarding fixtures |
| 1 | OraToPlus | 12/15 component checks pass; three fail | Unpaid/suspended entitlement and unpaid checkout activation defects; usage and full lifecycle acceptance; numeric grading remains separately gated |
| 1 | WeddingOS | 11/11 free-tool checks pass | Saved-plan ownership, 20-plan cap, last allowed save, safe retry and bounded payloads covered at router/model level; paid workspace, database/browser journey and billing still unverified |
| 2 | Memoire | 13/15 component checks pass; two fail | Zero allowance and negative reservation accepted by usage helper; all call sites, anonymous restrictions, concurrent requests and provider lifecycle remain to test |
| 2 | Jodibana / JodiUSA | 60/60 shared-engine tests pass | Configured Stripe test key rejected with HTTP 401; tenant-specific catalog, paid marketing feature acceptance and actual sandbox lifecycle remain open |
| 2 | Atmasphere | No version-matched billing suite run | Registry points to Atmakosh website; establish actual product destination and test environment |
| 3 | CoffeeBook | Same Memoire suite, not additional tests | Same two helper failures; verify its journey on the shared commercial track |
| 3 | Charam | Public HTTPS responds; no tier suite run | Verify deployed catalog, authorization, quotas and sandbox fixtures |
| 3 | SDIS | Internal-only scope confirmed | Internal access/usage/journey tests remain; public commercial lifecycle outside current release |
| 3 | One-Man Hedge Fund | Internal-only scope confirmed | Same internal readiness requirements; no public paid launch inferred |
| 3 | Quantsys | Internal-only scope confirmed | Same internal readiness requirements |
| 3 | SMDP Design | Internal-only scope confirmed | Same internal readiness requirements |
| 3 | Stablecoin Pipeline | Internal-only scope confirmed | Same internal readiness requirements |
| 3 | Vanguard GTM | Public HTTPS responds; no tier suite run | Deployed commercial scope, catalog and isolated fixtures required |
| 3 | Vireoka Website | Public HTTPS responds; no tier suite run | Verify whether any account/paid service exists before marking commercial cases inapplicable |
| 3 | Atmakosh Website | Public HTTPS responds; no tier suite run | Same scope verification; website reachability does not qualify Atmasphere |

All 11 configured public destinations checked returned HTTP 200. Two product records share Atmakosh's destination; this does not establish their identity or functionality. Internal products were not exposed publicly for testing.

## Recommended acceptance matrix

For every actual free and existing paid plan, record the current plan ID, price ID, currency, billing interval, quotas and deployed source version. Database overrides and grandfathered plans need their own rows; code catalog defaults do not establish the price a customer is charged. New strategy recommendations are excluded.

1. **Free account:** register, verify email, sign in, reach first value, save/reload, return in another session and sign out. Verify free access without checkout and access denied when logged out.
2. **Existing paid plan:** provision only through a sandbox payment event or documented test fixture. Verify exactly the purchased features, correct customer and tenant binding, renewal and downgrade. No caller-supplied tier, price or payment-provider override may grant access.
3. **Usage:** test zero allowance, the last allowed unit, first denied unit, invalid/negative quantities, simultaneous reservations, safe retries, monthly reset, cancellation/release and failed-job accounting. Check API and UI, not just catalog labels.
4. **Cross-tier/tenant access:** try free-to-paid, paid-to-higher-tier, suspended/unpaid-to-paid, foreign organization headers, direct API routes, object identifiers, exports and background jobs. Apply tenant configuration and paid opt-in requirements independently of subscriber consent.
5. **Sandbox checkout:** verify test-mode keys and isolated callback destinations first. Test successful, declined, authentication-required, abandoned, expired and completed-but-unpaid sessions. Success-page navigation alone must never grant access. Use provider test payment methods only.
6. **Webhooks:** reject missing/invalid/stale signatures, process a duplicate once, tolerate out-of-order events, bind customer/subscription/tenant, reconcile provider status, prevent stale cancellation of a replacement subscription and retry failures without duplicate invoices or grants.
7. **Cancellation:** test immediate and period-end behavior, grace policy, scheduled reversal, renewal races and retries. Confirm future billing stops, valid remaining access is handled correctly, quota stops or resets according to policy and audit evidence remains.
8. **Refunds:** test full and partial refunds, repeated requests, pending/failed provider refunds, refund after cancellation, dispute events, ledger/recognized-revenue effects, partner-commission reversal and entitlement policy. These are sandbox tests; real refunds require separate authorization.

Use Stripe's [testing guidance](https://docs.stripe.com/testing) and [webhook documentation](https://docs.stripe.com/webhooks) for provider fixtures and signature handling. Test-mode prefix checks alone are insufficient: Jodibana's current key had a test prefix but failed authentication. No provider mutation was attempted.

## What automatic approval means

The server-side qualification importer requires one report for every product and all eight acceptance categories. It checks the current strategy revision, timestamps, run identity and pause state; rejects stale, conflicting, incomplete or falsely relabelled evidence; and appends the decision to each entitlement task's audit history.

A task completes only when every applicable category has measured sandbox end-to-end evidence and its journey prerequisite is complete. A scoped inapplicability statement must reference verified product scope. Component success is recorded as partial, never a full pass. Known failures remain failed. New incomplete or failed evidence reopens the technical task. Pricing, partners, campaigns, identity and other prerequisite tasks cannot be approved by this importer.

**This run approves zero complete entitlement tasks.** Every product retains missing coverage or prerequisites. The 198 passing checks are accepted evidence, not 198 approvals or a claim that all products can launch. The 51 commercial task statuses remain unchanged.

The importer is an operator CLI, not a public report-upload API. The operator must verify runner outputs, exact source/image and environment; the importer does not cryptographically attest that a test runner executed. Changing the strategy requires new evidence. Product deployments after the recorded image require retesting before approval; no deployment watcher is added by this release.

## Evidence and reproduction

- [Measured unique product results](evidence/product-tests-20261101.json): counts, exact images, failures and provider readiness.
- [All 17 product/category records](evidence/wave-qualification-20261101.json): partial/failed/blocked/inapplicable evidence, with no credentials or customer data.
- `scripts/qualification/`: isolated product test runners. They use no live database mounts, no network and synthetic fixtures; third-party calls and selected persistence managers are mocked where stated. These are not migration, browser or live-provider tests.
- AgentVire regression coverage: test evidence validation, dependency checks, idempotency/conflict, stale evidence, pause, revision drift, failed-followup reopening, immutable commercial records and finance-reference preservation.

The LiqMint Institutional fixture required a temporary report directory at the code's hard-coded development path. It was a container tmpfs only, not a host/Windows mount. Memoire's normal settings force PostgreSQL during startup, so helper tests use minimal Django settings and mocked managers; database integration remains outstanding. WeddingOS tests exercise actual deployed router/model functions with mocked persistence. Jodibana uses bundled tests plus a test-only pytest layer on its exact deployed base image.

AgentVire's finance collector now preserves the four existing strategy/cost-reference fields while replacing observed processor data. The missing reference in the preceding refresh was restored from its verified backup without replacing the newer transactions or approving any financial assumptions.


## Deployed release

AgentVire **0.5.1** is live at [the execution desk](https://agentvire.com/?view=execution). Source commit `821d5c2` is on `codex/product-strategy-os`. All **219 AgentVire regression tests passed**. Isolated browser checks passed for all 17 product rows, product filtering, expanded evidence, JSON download and mobile rendering, with zero script errors. Production TLS/login and unauthorized-access checks passed; all 39 deployed application files match the release source.

Open **Automated tier and billing qualification**, select a product or expand its row, then choose **Download test and approval report**. The report distinguishes failed, partially tested, blocked and out-of-scope categories. No complete entitlement task was automatically approved in this run.

The preceding image `growthpilot-staging:agentvire-0.5.0-prd`, a database/recovery backup and previous runtime settings are retained. Other product services, protected finance/configuration files and all 51 commercial task records were preserved. No payment-provider mutation or outbound message occurred. The isolated QA container was removed after verification.

Receipts: [deployment and data checks](evidence/agentvire-0.5.1-release.json), [isolated browser workflow](evidence/agentvire-0.5.1-browser.json), [production browser](evidence/agentvire-0.5.1-production-browser.json).

Follow-up: [Targeted OraToPlus/Memoire fixes and Jodibana sandbox readiness](billing-fix-staging-20261101.md). The original five failures pass in candidates; production deployment is pending explicit approval and real Jodibana sandbox access remains blocked.
