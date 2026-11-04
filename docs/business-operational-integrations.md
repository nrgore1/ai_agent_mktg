# AgentVire operational integrations and autonomous preparation

Release date: 3 November 2026, America/New_York. This extends the business command center for Vireoka LLC and Atmakosh LLC.

## What is connected

- Vanguard relationship records refresh automatically into a read-only AgentVire mirror every five minutes. This is inbound synchronization, not a two-way CRM merge.
- Existing statement-extraction, approved provisional cost-allocation and processor-payment evidence is read from the protected economics source.
- Local role workers automatically inspect eligible case evidence and use the existing Mistral model to select a prepared next-action plan. They do not complete business steps or execute external commitments.

The owner confirmed that the companies' books are not finalized. No reconciliation checkbox or source flag can turn the connected evidence into finalized books in this release.

## Starting work

Open Business command center. Work queues contains source-linked cases with explicit role ownership, an accountable person, a next review date and evidence criteria.

The initial production case preparation uses six existing research-stage AgentVire leads, two Vanguard records marked in conversation, seven unit-level finance-close requests and four operational-readiness requests. Source stages remain source-reported. A researched prospect is not an acquired customer; an in-conversation record is not a signed pilot.

Review dates of 5 November and 10 November 2026 are initial internal targets that the owner can edit. No meeting or customer deadline is booked by case creation. Repeating the preparation request returns the same case identities without duplicating work.

Use Vanguard opportunities to inspect source stages and create a scoped case. Company-level relationships require an explicit unit selection inside the correct legal entity. Unit-scoped records cannot be reassigned to another unit. Opening or creating a case never sends an invitation.

Use Finance evidence to review the source capture date, two distinct financial periods, provisional allocated cash, shared processor groups and missing close work. Source PDF controls are extraction checks, not completed ledger reconciliation. Currency amounts remain in their recorded minor units; shared accounts are not treated as company revenue. Equipment and founder recovery remain distinct from recurring operating costs.

Use AI work results to inspect model attempts, recommendations, errors and older source/case versions. The same recommendation also appears inside its work case. Founder controls can pause autonomous preparation or retry a failed current work item. Global pause also prevents new AI results from being accepted.

## Legal-entity and data scope

Vireoka LLC: LiqMint Individual, LiqMint Institutional and TCompprop.

Atmakosh LLC: WeddingOS, Jodibana/JodiUSA, OraToPlus and MemoirBookStudio.

Vanguard properties map as follows:

| Source property | Scope |
| --- | --- |
| liqmint | Vireoka / LiqMint Individual |
| liqmint-institutional | Vireoka / LiqMint Institutional |
| vireoka | Vireoka company-level pool |
| atmakosh | Atmakosh company-level pool |
| weddingos | Atmakosh / WeddingOS |
| jodibana and jodiusa | Atmakosh / Jodibana |
| oratoplus | Atmakosh / OraToPlus |

Unmapped source properties are quarantined from unit views. Company-level pools are visible to existing portfolio-privileged users; a unit-role assignment alone cannot reveal them. Finance amounts require a CFO or CEO unit assignment. If a processor account spans unauthorized products, its amounts are withheld.

No emails, phone numbers, outreach bodies, approval records or private relationship history are copied by the Vanguard bridge. The source email-status label is informational. Marketing eligibility remains false and existing product consent, suppression and exact-payload publishing controls remain authoritative. Deleted source rows disappear from the mirror; linked cases become source-unavailable for automated preparation. Case-retention policy is separate from deleting a source prospect.

## Autonomous role worker contract

Workers operate one at a time, with at most 24 attempts per hour and two automatic attempts per unchanged case/input combination. They require an enabled case owner with unit access. They skip closed/completed cases and cases awaiting founder review.

The model sees only a role, a process identifier, fixed prepared alternatives and boolean evidence flags. Customer names, free-form CRM instructions, account credentials and financial amounts are not sent to it. It returns an integer selection, validated against the permitted choices and exact prepared text.

The worker records a recommendation and provenance. It cannot call publishing, billing, deployment, contractual, treasury or approval tools. Its result is an internal preparation artifact, not proof that a customer was contacted, a reconciliation was completed or a launch gate passed.

The configured qualified mode uses local ministral-3:3b (or the separately allowed local granite selector). Public endpoints and cloud model tags are rejected. Inference requires the existing preloaded 2048-token context and has a bounded request timeout. Missing/cold models, incomplete responses and unsupported output result in a visible failed job. There is no fabricated successful fallback.

Job identity includes the case version and source-evidence fingerprint. Case edits, role revocation, owner disablement, source deletion/change, financial-source changes relevant to CFO work, or a changed worker-control decision invalidate in-flight results. New source versions create new work; prior results remain visible as older evidence.

## Programmer reference

- growthpilot/business_runtime.py: source validation, scoped projections, deterministic case creation, runtime controls, leases and local model selection.
- growthpilot/static/business-runtime.js: opportunities, finance and AI-result views.
- deploy/vanguard_snapshot_bridge.py: host-side read-only PostgreSQL extraction and atomic publication.
- tests/test_business_runtime.py and tests/test_business_http.py: data-scope, finance-honesty, lifecycle, permissions and failure checks.

The existing business API gains:

| Endpoint | Authority |
| --- | --- |
| POST /api/business/opportunity-case | Appropriate unit role; fresh source and legal-entity checks |
| POST /api/business/bootstrap | Founder; idempotent source-linked operational case preparation |
| POST /api/business/worker-control | Founder; explicit enabled boolean only |
| POST /api/business/worker-retry | Founder; current failed/blocked work only |
| GET /api/business | Existing scoped view, enriched with validated evidence and worker results |

No endpoint accepts a caller-provided database URL, model endpoint, model prompt, signing key or arbitrary tool request.

The authorized VPS account installs the column-limited reader and preserving cron entry with deploy/install_vanguard_snapshot_bridge.py after transferring the adapter. The installer is idempotent when its protected configuration exists; it stops if a reader role exists without that file rather than rotating an unknown credential. The file is private to the VPS account and excluded from the repository.

The bridge runs outside the application container. AgentVire receives no Docker socket or PostgreSQL superuser credentials. A dedicated PostgreSQL role has read access only to the selected partners columns. It has no insert, update or delete permission. Its password is stored in a private VPS file and passed through process environment rather than command arguments or logs. Refresh uses a non-overlapping host schedule and writes only a complete, bounded source snapshot. Failed refresh retains the prior snapshot and reports source unavailability; data older than 15 minutes cannot create a new opportunity case or support a worker result.

The financial connector reads the existing protected snapshot and exposes its original capture time. It does not automatically refresh banks, retrieve invoices, post journal entries, depreciate assets, close books or calculate actual margins from estimates. Updating that source file updates the dashboard evidence; a new provider/ledger integration is separate work.

## Validation and operating controls

Required checks cover company/unit isolation, incomplete and duplicate snapshots, source deletion, unknown mappings, scope-limited shared-account amounts, nonfinite and duplicate allocations, idempotent case creation, API authentication and CSRF, worker retry/attempt limits, owner revocation, source changes during inference, prompt-injection-shaped CRM text, local-only inference, and unchanged external action records.

Deployment must preserve existing runtime settings, protected records and JodiUSA's free access. Jodibana live collection remains subject to its existing launch gates. No Google Cloud service is used.

## Remaining work

- Finalize revenue recognition, deferred revenue, supplier/invoice matching, support time, allocation pool tie-outs and partner accrual/payout records before reporting actual margins.
- Define and qualify any bidirectional Vanguard update contract; the current mirror deliberately does not overwrite source stages.
- Qualify broader generative or tool-executing agent capabilities separately. Current autonomy is evidence inspection and prepared-action selection.
- Add product operational adapters, independent audit anchoring and enterprise identity improvements on their own backlogs.

## Release verification

295 regression tests passed, plus 61 overlapping focused tests on the exact VPS image. Synthetic browser checks passed for source case creation, company filtering, finance role restrictions and mobile layout. The local Mistral selector passed ten actual inference checks across all five roles; qualified responses took 0.8 to 2.3 seconds. An earlier longer prompt timed out and was replaced before deployment. These checks validate bounded selection, not unrestricted business judgment.

Live browser verification confirmed 541 Vanguard records, provisional finance labels, 19 idempotent source-linked cases, enabled preparation workers, the existing execution view and no browser errors. All case steps remained pending. Deployment retained settings, protected records, other VPS services and the previous image for rollback. The scheduled Vanguard refresh was observed after setup. See [release evidence](evidence/business-operational-integrations-20261103.json).

All 19 initial cases subsequently received a current, non-stale local-worker result: CEO 5, CFO 7, CMO 3, CTO 2 and COO 2. The final live browser check verified those results inside both AI work results and Work queues. No case step was completed, no external action occurred and the audit chain remained valid.
