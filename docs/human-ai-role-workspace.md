# Human counterparts and President oversight

AgentVire pairs each CEO, CFO, CMO, CTO and COO AI role with a human role within its assigned business unit. The seven units produce 35 pairings. Existing company-role accounts cover those units: five for Atmakosh LLC and five for Vireoka LLC. The existing founder login is the President account; its credentials and access remain unchanged.

## Where to work

Sign in at https://agentvire.com/?view=business and choose **Human + AI workspace**. Select company, unit and role using the existing filters.

The President uses **Role accounts** to create a named person's login with one company, one role and selected units. The existing ten role accounts remain available. Set temporary passwords privately through the existing account controls when onboarding a person; the first login requires a password change. Do not share one password among several people. Disabling an account, changing its password or revoking its assignment removes access through the existing session controls.

## Roles and access

| Human role | Corresponding AI work | Typical manual work |
| --- | --- | --- |
| CEO | Priorities, relationships, financing objectives and business reviews | Discovery, partner qualification, accountable decisions |
| CFO | Revenue/cost evidence, pricing analysis, budget assumptions | Reconcile records, verify costs, review financial evidence |
| CMO | Customer research, campaign preparation, sales qualification | Verify audience permission, prepare exact drafts, measure acquisition |
| CTO | Readiness, release evidence, technical risk | Test products, investigate issues, document deployment evidence |
| COO | Activation, service delivery, vendors and incidents | Customer onboarding, service recovery and vendor follow-up |
| President | Entire system, every company, role and unit | Delegate, approve consequential handoffs, override or pause work |

Company and role checks apply on the server, not merely to visible menu items. A company CEO does not receive another role's detailed evidence or finance view. Cross-role case steps expose only handoff role and status. Roles can see work performed by or for their own role in assigned units. President access spans the portfolio.

## Review AI work

1. Open an AI recommendation or a 90-day evidence pack.
2. Inspect its action and evidence references alongside the full **AI work results**, **90-day role plans** or **Work queues** view.
3. Approve the internal preparation or reject it with a reason.
4. For a current AI recommendation, select one of the three qualified action focuses and request a revision. The bounded local worker prepares a new result on its next run.
5. Review the new result separately. An approval never transfers automatically to changed evidence.

Free-text feedback remains in the scoped human record. Only the selected focus and fixed evidence flags reach the qualified local model. This is bounded preparation, not unrestricted AI chat. Failed, paused or stale results cannot be approved. Rejection records a decision; use **Request AI revision** to queue a revised recommendation.

An internal review is not permission to publish a campaign, collect money, deploy a product or sign a contract. Those workflows retain their existing exact-action approval and evidence gates. Outcome milestones still require President acceptance.

## Perform manual tasks

Create a task for your own paired role and login, stating instructions, acceptance evidence and its source/case reference. The President may delegate to another enabled, appropriately scoped account. Start the work, perform it outside this record where necessary, then record completion with evidence and the verification checkbox.

Mark consequential handoffs explicitly. They require President authorization tied to the exact task before start/completion can be recorded; this does not grant access to external systems or bypass their controls. The workspace records evidence of manual execution; it does not itself send, charge, sign or deploy.

## President overrides

The President can:
- Supersede an AI approval/rejection and lock the decision; release the lock when the paired role may decide again.
- Hold, cancel, reject, complete or reopen manual work, retaining its previous evidence and history. Reopening clears consequential authorization.
- Hold/cancel a business case, or reopen its current or an earlier step. Dependent steps reset and their prior state remains in the override history.
- Pause/resume one AI role in one unit, covering case preparation and scheduled evidence packs.
- Use existing account controls, global pause and consequential decision inbox across the full system.

Every override requires a reason and checks the current record version. Overrides cannot turn failed tests into passing evidence, skip forward over unmet case steps, erase the audit trail, or reverse a completed external transaction. External reversals need their own authorized compensating action.

## Implementation and maintenance

The existing founder identity implements President authority; no new privileged password or account is introduced. `human_ai.py` owns paired reviews, feedback, tasks and controls. `business_os.py`, `business_runtime.py`, `operating_plan.py` and `role_access.py` enforce their workflow effects.

Records use the existing SQLite transaction and hash-chained audit mechanism:
- `human_ai_reviews`: artifact hash, decision version, actor, President lock and prior decisions.
- `human_ai_feedback`: scoped human context and structured revision focus.
- `human_manual_tasks`: assignee, acceptance criteria, authorization, evidence and historical state.
- `human_ai_controls`: enabled flag and version for each unit/role.

Authenticated, CSRF-protected business routes are `human-review`, `human-feedback`, `manual-create`, and `manual-action`. `president-pair` and `president-override` require the President. Request fields are exact; versions prevent lost updates. Role assignment and product scope are checked on each operation. New role controls invalidate in-flight AI results through their input fingerprint.

No database migration, external provider, paid-tier activation or Google Cloud dependency is introduced. Existing role accounts, assignments, 90-day plans, commercial records and product-specific launch backlogs are preserved.

## Release verification

Released on November 4, 2026. All 349 regression tests passed on the VPS, including 20 focused human/AI permission and workflow tests. Browser checks passed for all ten company-role logins, forced password changes, company/role isolation, CSRF rejection, stale versions, manual completion, President locks, case holds, per-role pauses and mobile layout. Live verification confirmed 35 pairings, 19 cases and 35 plans, with no test tasks or review decisions inserted into production. Existing credentials, commercial settings and all 282 launch-backlog items were preserved. See [release evidence](evidence/human-ai-role-release-20261104.json).

## Assigned plans and backlog

The live **Assigned work and next actions** panel now links the 90-day activities, remaining backlog and prepared role packets. Current source-linked recommendations are available for paired-human review, and the President manual queue lists owner-dependent actions. See [assignments and first actions](work-assignment-and-first-actions-20261104.md) for counts, owners, timing and preserved approval gates.
