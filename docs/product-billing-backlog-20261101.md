# Product billing and entitlement backlog — 1 November 2026

These tasks belong to the individual product repositories. The AgentVire reporting release does not change product implementations or payment settings. Tests use synthetic isolated fixtures, not live customers. See [all-wave qualification](wave-billing-qualification-20261101.md).

| Priority / owner | Confirmed finding or missing gate | Required fix and retest |
|---|---|---|
| P0 OraToPlus billing owner | `org_tier` ignores subscription status: suspended Growth and unpaid Enterprise still resolve paid features on | Define eligible paid states and approved grace policy; deny suspended/unpaid features across direct API and jobs; test cancellation/renewal and tenant overrides |
| P0 OraToPlus billing owner | Completed-but-unpaid checkout invokes `_apply_paid_subscription` | Require validated paid/eligible provider state, expected plan and org/subscription binding. Reconcile duplicates, async completion and stale events in the provider sandbox |
| P0 OraToPlus billing owner | Source review: mock `change_tier` endpoint directly sets paid status and creates a paid invoice | Verify public route exposure and remove/gate mock behavior outside explicit isolated tests. Add authenticated permission and provider-backed upgrade tests. No live route exploitation was attempted |
| P0 Memoire commerce owner | Zero illustration allowance still accepts a reservation | Fail closed at zero; verify every call site, free/anonymous routes and API response. Test both helper and authenticated HTTP behavior |
| P0 Memoire commerce owner | Negative reservation reduces recorded usage | Validate positive integral quantities; atomic bounded reservations and idempotent release. Test concurrency, errors, resets and unknown plan values |
| P0 Jodibana platform owner | Stripe rejects the configured test key with 401 | Install a valid test-mode secret via secret management; verify callback isolation before sandbox mutations. Test JodiUSA-specific catalog, tenant acceptance and paid opt-in gating |
| P0 all public paid products | No complete provider/browser entitlement certificate | Run all eight acceptance categories against exact current plans and deployed source. Full and partial refund results must reconcile billing, access and commissions |
| P1 LiqMint Institutional owner | Offboarding tests depend on a hard-coded developer report directory | Move report storage to a configured runtime path with production permissions; test offboarding against configured storage. Current isolated tmpfs only fixes the fixture setup |
| P1 WeddingOS owner | Free-tool helper/router checks pass; paid workspace and full browser persistence not covered | Extend product-owned tests through registration, save/reload, 20-plan boundary, paid workspace denial and actual billing/cancellation if applicable |
| P1 Memoire/CoffeeBook owner | Shared track could be counted twice | Use one source for revenue and commercial tests; add distinct journey coverage without duplicating test totals or launch approval |
| P1 Atmasphere owner | Registry destination is the Atmakosh website | Confirm canonical product and deployed environment before defining paid/free acceptance |
| P1 Charam/Vanguard/site owners | Reachability exists; commercial scope and test fixtures unverified | Establish whether each has paid offerings. Mark only genuinely out-of-scope categories inapplicable, with evidence |
| P1 internal product owners | Internal scope confirmed; technical readiness unverified | Test internal identity/access, quotas and first value; keep public checkout, campaigns and sales out of scope until authorized |

Numeric OraToPlus grades remain subject to their existing human-reference gates. No scoring gate is cleared by billing tests. Postmark account-level history deletion also retains its separate provider-configuration dependency.
