# AgentVire business command center

Release scope: two-company business operations workspace, 3 November 2026 (America/New_York).

AgentVire is the shared entry point for sales, marketing and operations across Vireoka LLC and Atmakosh LLC. The command center adds persistent work cases, role handoffs, founder decisions and scoped portfolio visibility to the existing marketing system. It does not turn role names into autonomous agents or execute contracts, payments, deployments or product operations.

## Companies and business units

| Company | Unit | Existing product records |
| --- | --- | --- |
| Vireoka LLC | LiqMint Individual | 1 |
| Vireoka LLC | LiqMint Institutional | 2 |
| Vireoka LLC | TCompprop | No product connector or existing registry ID |
| Atmakosh LLC | WeddingOS | 4 |
| Atmakosh LLC | Jodibana and its JodiUSA tenant | 6 |
| Atmakosh LLC | OraToPlus | 3 |
| Atmakosh LLC | MemoirBookStudio | Memoir 5 and CoffeeBook 7 |

These mappings follow the owner's confirmed operating entities. They do not establish a parent holding company. Other portfolio records retain their existing IDs and require explicit unit mapping. JodiUSA retains free access; the business workspace does not change billing entitlements or live collection settings.

## Daily use

1. Sign in at AgentVire. The default view is **Business command center**; the direct route is `/?view=business`.
2. Select both companies or one company, then an optional business unit and next responsible role.
3. Review open cases, founder decisions and overdue cases. Unit cards show current local leads, campaigns and unfinished readiness records. These are record counts, not unique customers, qualified opportunities or certified launch results.
4. Open **Work queues** and create a case for a real opportunity or request. Choose a process, an enabled AgentVire account as owner, a due date and a source reference. Keep secrets and sensitive customer content in their source systems.
5. Open the case to see the complete process and the next step's acceptance criteria. Record progress or a blocker. To complete a step, provide an evidence reference and outcome and attest that the evidence meets the criteria.
6. A step marked for founder review goes to **Decision inbox**. The founder accepts the exact recorded handoff or returns it for changes. Acceptance does not send a campaign, sign an agreement, post accounting entries or execute a release.
7. Reassign the owner and next due date when handing work over. The receiving account must have the current step's role and unit access. The role queue is based on the next required role; the case owner is the accountable coordinator and does not replace role authorization.
8. Close an abandoned case with a reason. Closed and completed are separate outcomes.
9. Download the filtered operating brief for the weekly review. Evidence references and notes are private operational information.

The **Process library** explains all ten workflows. **People & roles** manages explicit assignments. **Connections** distinguishes local data from manual handoffs and missing integrations. Existing Approvals, Launch Desk, Pipelines, Strategy execution and reporting remain accessible inside AgentVire.

## Role responsibilities and access

| Role | Primary work |
| --- | --- |
| CEO | Priorities, discovery, partnerships, financing relationships and accountable business reviews |
| CFO | Source records, reconciliation, allocation assumptions, economics and financial recommendations |
| CMO | Customer qualification, campaign preparation, acquisition and learning |
| CTO | Technical readiness, engineering requests, release evidence and diagnosis |
| COO | Onboarding, service delivery, vendors, recovery and customer outcomes |

Founder and administrator accounts retain existing portfolio oversight. Only founder-role accounts can grant business roles and accept gated workflow handoffs. Operators need explicit unit/role assignments plus access to every existing product ID mapped to that unit. Viewers with assignments can read unit cases but cannot mutate them. Revocation takes effect on the next request; no session restart is needed. TCompprop access requires an explicit unit assignment because it has no existing product mapping.

Unit members can read their unit's operational cases across roles. This is a staff workspace, not a customer-tenant portal. The optional tenant reference is a label; it grants no tenant access and is not a row-level tenant security boundary. External Jodibana tenants must not receive internal staff accounts for this workspace.

## Process definitions

Each process has five ordered steps with role ownership and evidence criteria. All ten processes can be instantiated independently in each of the seven units.

| Process | Ordered work |
| --- | --- |
| Sales opportunity to activation | Qualification; discovery; economics; founder offer-handoff review; actual decision/activation |
| Campaign research to learning | Audience/evidence; exact package; costs/attribution; founder handoff; actual results |
| Partner discovery to pilot review | Mutual value; pilot delivery scope; economics; proposed commitment review; attributable results |
| Financing readiness | Entity/objective; reconciled evidence; qualified relationship; materials/outreach handoff review; actual diligence outcome |
| Onboarding and customer success | Eligibility; technical readiness; first useful experience; retention feedback; success/escalation |
| Support and service recovery | Triage; investigation; consequential-remedy review; verified resolution; prevention |
| Vendor procurement and fulfillment | Requirement; total cost; proposed commitment review; delivery/invoice evidence; reconciliation |
| Financial close and margin review | Source records; reconciliation/allocation; scenarios; recommendation review; documented handoff |
| Product change and release readiness | Separate product issue; implementation/tests; operating readiness; production handoff review; deployment receipt |
| Incident response and recovery | Impact/containment; diagnosis; consequential recovery review; verification; prevention |

These are operational preparation and evidence processes. A handoff receipt that explicitly records an external action being held is valid workflow evidence but is not evidence that the external action succeeded. Business outcomes must be measured from their actual source systems.

## Product-specific operating rules

- LiqMint Individual: verify claims and first-use readiness; this workspace cannot trade, manage vaults or move treasury funds.
- LiqMint Institutional: require qualified institutional stakeholders, scoped demonstrations, security/compliance evidence and explicit pilot success measures.
- TCompprop: use documented property, lease and maintenance cases; integrations, contracts, notices and payments remain separate.
- WeddingOS: measure saved plans and return usage; verify vendor commitments, booking/refund behavior and any escrow capability before claims or execution.
- Jodibana/JodiUSA: distinguish tenant marketing acceptance from member permission; preserve free JodiUSA entitlements and outstanding collection gates.
- OraToPlus: measure useful practice feedback; numeric grades remain dependent on human-reference quality gates.
- MemoirBookStudio: measure saved projects and useful previews; verify media rights, print quality, shipping and physical fulfillment costs before orders.

## Architecture and programmer reference

`growthpilot/business_os.py` defines the entity/unit registry, role catalog, process templates and the BusinessOS service. `growthpilot/static/business.js` adds the cockpit to the existing authenticated console. `server.py` exposes:

| Endpoint | Operation |
| --- | --- |
| GET `/api/business` | Authorized units, cases, process definitions, local counts and connection status |
| POST `/api/business/assign` | Founder grants or revokes a role for an existing enabled account |
| POST `/api/business/create` | Create an evidenced, owned and dated process case |
| POST `/api/business/record` | Record progress/blocker or submit completion evidence |
| POST `/api/business/review` | Founder accepts or returns an exact current handoff |
| POST `/api/business/schedule` | Update accountable owner and due date |
| POST `/api/business/close` | CEO role closes a case without claiming completion |

Sessions, CSRF and origin checks use the existing authentication boundary. Scope is derived from the server registry and authenticated account, never accepted as a client-supplied company or role assertion. Unsupported input fields are rejected. No new database schema is needed: `business_cases` and `business_assignments` use the existing records table. Existing backups include these records automatically.

Updates run inside the existing serialized SQLite transaction. Every case mutation requires an exact integer version. Competing or replayed updates fail rather than overwriting new work. Ordered steps prevent skipping a prerequisite. Evidence updates invalidate prior review state. Gated proposals bind unit, case, step, next version and exact evidence content in a hash and expire after 24 hours. The authenticated founder's decision is stored in the case; it is not a portable cryptographically signed execution capability.

Evidence history is retained in each case. The audit chain includes actor, transition, version and a hash of the resulting case. The database remains an application-scoped store, not database-enforced tenant isolation. Existing administrators remain privileged. Global pause blocks case mutation and decisions while allowing access administration, including revocation.

No new cloud service, model worker or third-party dependency is installed. The seven pods are logical role workspaces. The existing qualified local model functionality is unchanged.

## Connection and data boundaries

Current local lead, campaign, approval and readiness records are read directly with business-unit scope. Existing marketing approvals remain in the exact-action Approvals desk. Their presence in the decision view does not renew or broaden them.

Vanguard is a manual-reference handoff in this release. No dedicated synchronization is claimed. Accounting is not connected; actual revenue and margin deliberately remain null rather than fabricated or inferred from illustrative scenarios. Product services and Veda/Kairo use referenced evidence rather than newly provisioned execution adapters. Corporate P&L, cash, contract status, tenant provisioning and vendor fulfillment need their own verified integrations.

The 75% margin policy is retained in economic-review criteria. It is not automatically calculated by a workflow checkbox. Free-service exceptions need explicit funding treatment. Founder sweat equity and recovery remain distinct from cash expenses and recognized accounting treatment.

## Remaining Agent OS backlog

1. **P0: Vanguard handoff.** Stable relationship IDs, source ownership, stage mapping, consent/suppression references, idempotent updates and conflict reconciliation. Acceptance: duplicate/stale events cannot create duplicate actions or transfer approval implicitly.
2. **P0: Reconciled company finance.** Select and connect the accounting source; map entity, business unit, period and allocation basis. Acceptance: source-to-ledger reconciliation and scoped read/write denial; unresolved figures stay unknown.
3. **P0: Remaining product mapping.** Confirm ownership and placement of the retained portfolio records. Acceptance: no inferred legal transfer or automatic pooling of contacts or funds.
4. **P1: Durable cross-system events.** Outbox, bounded retries, idempotent consumers and ambiguous-outcome reconciliation. Acceptance: restart/replay cannot duplicate an external effect.
5. **P1: Local agent workers.** Role-specific task contracts, model qualification, context isolation, tool scopes and resource budgets. Acceptance: prompt injection and unauthorized tools cannot bypass deterministic controls.
6. **P1: Shared engineering/operations workers.** Scoped Veda/Kairo requests and receipts, monitoring and rollback. Acceptance: one unit cannot read another's secrets or deploy without applicable authorization.
7. **P1: Product operational adapters.** Onboarding, billing state, service incidents and fulfillment status, selected per product. Acceptance: no customer-tenant data leakage and source freshness visible in every report.
8. **P2: Enterprise identity and recovery.** MFA/SSO, separate service identities, independent audit anchoring and proven full-stack recovery. Acceptance: revoked access fails, erasure history survives restore and approval evidence remains verifiable.

Product signup, grading, billing and media fixes stay on their product backlogs. Completing a cockpit case cannot mark those launch gates passed.

## Release and recovery

Test the service and HTTP authorization boundaries, all seven-by-ten process combinations, stale/expired approvals, pause/revocation, persistence, existing regression coverage and browser interactions. Use synthetic data for workflow mutation checks. Production verification should be read-only apart from normal authenticated-session audit records.

Deploy as a narrow overlay on the recorded running AgentVire image, preserving environment, mounts, data, pause state and other services. Take a verified backup first and retain the previous image and compose configuration. Roll back to that image if health or permission checks fail. The additive records can remain in the database; the older application ignores their kinds. Do not restore an older database merely to undo this UI/module release.

## Verified release evidence

The release passed 262 regression tests, a 21-test final audit-binding rerun, and 28 feature/HTTP tests on the exact deployed VPS image. These are overlapping suites, not 311 distinct tests. Browser checks covered company filters, case evidence, founder decisions, role isolation, mobile layout, live sign-in/sign-out and the existing execution screen. No production test cases were created.

Deployment preserved runtime settings, mounts, protected data and other services. The previous local-model image remains available for rollback. See [machine-readable release evidence](evidence/business-command-center-20261103.json). Accounting, Vanguard synchronization and autonomous role workers remain on the backlog above.
