# Assigned 90-day work and President action queue

## Operating scope

The President requested assignment of the 90-day activities and remaining backlog to the corresponding human and AI roles, startup of eligible work, and visibility of approval/manual-action needs.

The seven confirmed units retain 35 CEO/CFO/CMO/CTO/COO role pairings. Ten company-role accounts cover these units. No legal ownership, product mapping, contact permission or financial outcome is inferred by assignment.

The 90-day period is November 4, 2026 through February 1, 2027:
- Days 1–30: November 4–December 3.
- Days 31–60: December 4–January 2.
- Days 61–90: January 3–February 1.

## What is assigned and started

All 210 plan activities receive a human account, AI role and durable source-linked assignment. The 35 current outcome activities enter “in progress” because role assignment and preparation have started. Their human execution and business results remain unverified. The 35 previously completed preparation activities remain completed; the 140 later-phase activities remain pending.

All 170 unfinished launch-backlog items receive accountable routing:
- 86 map to established units and paired role accounts.
- 84 remain owned by the President for product/unit scope confirmation. These products are not silently attached to a company's role permissions. Existing internal-only products remain private.

Each established role receives a dated preparation packet containing its current phase objectives, prioritized backlog, unmet prerequisites, latest recorded observations, evidence references and active case handoffs. These are deterministic evidence packets, not new market research, grading decisions or claims of accomplished outcomes.

The 86 mapped backlog items also create manual evidence handoffs in **Human + AI workspace**. Completing a handoff does not complete its source readiness item. Product fixes remain on their separate product backlogs. Active operating cases transfer to the human account for the current role, invalidating prior AI input versions; the existing bounded local AI worker can prepare fresh recommendations.

## Who does what first

| Role | Human counterpart | Initial work |
| --- | --- | --- |
| CEO | atmakosh.ceo / vireoka.ceo | Rank customer, partner and financing opportunities; confirm scope and next accountable decision. |
| CFO | atmakosh.cfo / vireoka.cfo | Tie out available expense/payment evidence, identify missing records and preserve provisional assumptions. |
| CMO | atmakosh.cmo / vireoka.cmo | Prepare supported acquisition experiments, exact campaign drafts, consent evidence and attribution. |
| CTO | atmakosh.cto / vireoka.cto | Reproduce the highest-risk applicable readiness check and route required product fixes. |
| COO | atmakosh.coo / vireoka.coo | Verify onboarding, support, provider retention, fulfillment and recovery ownership. |
| President | Existing founder account | Resolve portfolio scope and owner inputs, review consequential handoffs, and retain override authority. |

Accounts are assigned roles, not proof that a named person has accepted the job. All ten accounts initially required their first password change. Assign named people and hand over passwords privately using **Accounts & integrations**.

## Eight President-owned manual actions

| Action | Information or action needed |
| --- | --- |
| Human role handover | Name the people covering the ten company roles; arrange private login handover and initial password changes. |
| Additional product scope | Confirm the company/unit homes for Charam, Atmasphere, SDIS, One-Man Hedge Fund, Quantsys, SMDP Design, Stablecoin Pipeline, Vanguard GTM and the two corporate websites. Keep internal products private and unclear products in discovery. |
| Publishing setup | Identify owned social pages/accounts and the business mailing address for campaign footers. CMO separately verifies each recipient's product-specific consent. |
| Accounting evidence | Supply remaining record locations and reporting periods for revenue, supplier bills, payouts and support time. Previously approved provisional allocations are retained. |
| Postmark retention | Confirm account-level Data Removal API availability and retention settings. If configured, provide only the protected secret location; no deletion occurs from completing the task. |
| Backup custody and alerts | Confirm the external-drive custodian, separate recovery-key escrow and monitored alert recipient. Prior drive repair/restore evidence remains valid within its tested scope. |
| Jodibana owner acceptance | Name the reviewer for the community/operator demo and business/tax/privacy/tenant opt-in review. Free JodiUSA access and live-collection gates remain intact. |
| TCompprop sources | Identify property, lease, maintenance and associated income/cost source locations and the accountable operator. |

These tasks appear in the President's manual queue when company, unit and role filters are cleared. The assigned role teams do the preparation and follow-up; the President supplies the owner-dependent decisions and access.

## Approval is separate from assignment

Existing approval for pricing, commissions and campaigns is retained. This assignment does not repeat that request or bypass unmet evidence gates. The original readiness status, acceptance criteria, dependency graph, test evidence and commercial records remain intact.

Human roles can approve/reject current AI recommendations within their scope. Stale results require fresh preparation. A business milestone requires its acceptance evidence and President review. Exact external campaigns, contracts, production changes and financial actions retain their existing controls. No outreach, payment, contract or product deployment is performed by this assignment workflow.

Use **Human + AI workspace → Assigned work and next actions** for the assignment register and prepared packets; **90-day role plans** for milestone evidence; **Work queues** for active cases; and **Manual work queue** for evidence handoffs and President actions.

## Implementation and checks

`work_assignment.py` writes deterministic assignments, scoped packets and manual preparation tasks within the existing serialized database transaction and audit chain. The President-only `assign-work` endpoint is idempotent and preserves later human decisions. It respects global and role pauses, source dates and disabled/ambiguous human assignments. Portfolio-only manual actions require the President.

The release is checked with 360 regression tests, including 11 focused assignment tests, and browser checks across all ten human role logins. Browser coverage includes scope isolation, no future-phase startup, preservation of President decisions, idempotent assignment and explicit recovery from an interrupted read. Private credentials are not changed or included in evidence.

## Verified activation result

Production verification confirmed 380 assignments: 210 plan activities and 170 remaining backlog items. There are 35 current role packets, 35 current outcome activities in progress, 140 future activities pending, 86 role evidence handoffs and eight President manual actions. All 19 operating cases now have the corresponding role owner.

The current local ministral-3:3b worker produced 19 qualified case recommendations. One initial attempt failed qualification and later recovered through the existing bounded retry path; no failed result was accepted. All 19 current results are ready for paired-human review. No case handoff currently awaits President approval. Weekly scoped preparation remains enabled.

Remaining backlog ownership: CEO 14, CFO 21, CMO 14, CTO 17, COO 20 and President scope queue 84. Each executive role also has 42 plan activities across the seven units.

The underlying launch backlog remains 92 completed, 45 pending, 113 blocked, 12 in progress and 20 not applicable. No business outcome, release gate or external action was falsely completed. See [release evidence](evidence/work-assignment-release-20261104.json).
