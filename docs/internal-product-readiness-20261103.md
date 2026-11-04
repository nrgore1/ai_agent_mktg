# Internal-product applicability review - 2026-11-03

Founder request: review the 45 blocked items for internal-only products, remove
inapplicable public-launch requirements, and resolve remaining readiness checks.

## Scope and status meanings

Products 10-14 remain internal: SDIS, One-Man Hedge Fund, Quantsys, SMDP Design,
Stablecoin Pipeline. Four requirements per product are **not applicable**:
public pricing decisions, partner commissions, campaign publication, and public
campaign-claim/destination reviews. These 20 decisions are not passed tests or
approvals. Original tasks and evidence remain in history.

The other 25 previously blocked items retain operational acceptance criteria:
private runtime/access boundary, internal operator workflow, internal permissions
and limits, data protection/recovery, and measured resource/support cost.
Identity/activity and finance requirements also remain; their earlier statuses
are not automatically completed. No public domain, customer signup, paid tier,
checkout or campaign is required for internal operation. Financial/data rights
and safeguards for any actual execution still apply.

The scope policy is persisted and reapplied after strategy regeneration.
Public-launch reactivation requires a separate founder scope decision and
restoration/revalidation of the archived requirements. Ordinary task updates
cannot change not-applicable tasks to completed. Public URL probes cannot
certify private runtime readiness. This release does not add a public-scope
reactivation or commercial execution endpoint.

## Evidence obtained

All checks used synthetic test data, with non-loopback socket connections
blocked. No trades, payments, emails, external model calls or Google Cloud were
used. No product source was changed.

| Product | Source revision | Selected checks | Result and limits |
|---|---|---:|---|
| SDIS | 20c953bfb6d2403fd0edac64a8b20351594e7f4a | 16 | Research mode overrides trading flags; broker boundary; native configuration; encrypted token persistence; single-use OAuth state; synthetic research APIs/save paths. Component evidence, not full operational acceptance. |
| One-Man Hedge Fund | 44e7edc0db235129e3e64d006bfb23fcc164d9e9 | 11 | Native launchers, research-only overrides, offline action denial, holdout replay/data-change refusal and research costing. Component evidence, not full journey acceptance. |
| Quantsys | 82286dfc94aac60e1c623fdbf92f4eb89e71b46f | 50 | User activation/disable/role boundaries; signed proofs, replay/expiry refusal, human control, kill switch and tamper detection. Synthetic venue execution only. |
| SMDP Design | Unconfirmed | 0 | Do not equate the LiqMint SMDP service with this product without source/ownership mapping. |
| Stablecoin Pipeline | Unconfirmed | 0 | Registry describes a video workflow but name implies finance. Resolve actual purpose and source before operational acceptance. |

One-Man Hedge Fund's Ubuntu local service is active on loopback port 8766.
Its health response identifies the authoritative repository, research-only mode
and the same revision tested. This passes the narrowly scoped private-runtime
gate only. Its historical release metadata references an older baseline; current
health code_revision matches current clean checkout. No model or market job was
triggered to perform this read-only check.

Quantsys is running on loopback port 8010 from its authoritative checkout.
Health responds successfully; anonymous user/account routes return 401.
Health does not expose a running code version, so runtime-version attestation
remains unverified. A clean current checkout is not proof of loaded code.

The initial One-Man Hedge Fund pytest invocation could not start because pytest
is absent in its existing environment. Its unittest-based suite then ran with
the standard-library runner: all 11 passed. No package installation was needed.

## Prioritized product backlog (kept separate from AgentVire development)

1. **One-Man Hedge Fund:** confirm legal/activity owner; run the full restricted
   operator save/return/recovery journey with synthetic state; measure resource
   usage and support time. Private runtime check is complete; not launch approval.
2. **Quantsys:** add running-version attestation in its product backlog; validate
   configured resource ceilings and recovery/export/deletion; complete the
   authenticated saved-workflow check without triggering a live order.
3. **SDIS:** document the authoritative operator/worker runtime and allowed data
   sources; run the complete restricted internal workflow and recovery drill.
4. **SMDP Design:** confirm whether it is an independent runnable product or an
   internal LiqMint design capability; map source, owner and acceptance evidence.
5. **Stablecoin Pipeline:** confirm actual purpose, owner and source. Do not
   activate finance or video-related claims based on the ambiguous registry.
6. **All five:** retain data-rights/activity review, backup restoration,
   retention/access evidence, actual cost measurements and unreconciled finance
   gaps. Existing estimates remain estimates.

## Administration and verification

The trusted server maintenance entry point is
`growthpilot.internal_readiness.set_scope(Execution(store), source, actor='founder')`.
It applies only to the five fixed, founder-confirmed internal products, checks
paused/stale strategy state, records an audit event, and is idempotent.
It is not exposed as an unauthenticated or role-user API. Back up the database
before applying it.

The dashboard reports not-applicable items separately, supports filtering them,
and retains original requirement history for traceability. Automated regression
tests cover public-product preservation, zero commercial changes, idempotence,
strategy resync, authority/stale-source checks, public-health rejection and
completion bypass denial. Evidence dates and environment limitations must remain
visible when recording component results in AgentVire.

## Deployed result

The final image passed 313 AgentVire regression checks and dashboard tests.
Production browser verification passed with private routes returning 401 to
anonymous users and all 10 role accounts preserved. The live backlog now has
119 blocked tasks overall; 24 belong to these internal products. Twenty public
requirements are not applicable, and one private-runtime task was completed.
The completed count rose from 91 to 92 at application time; no full product was
approved. A database backup and previous image are retained for rollback.
Public-product task records, commercial settings and business cases were unchanged.
See the adjacent JSON evidence receipts for exact counts and source revisions.
