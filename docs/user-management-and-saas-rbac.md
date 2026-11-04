# AgentVire user administration and SaaS roles

Updated 4 November 2026. The President uses the existing `founder` account to manage both Atmakosh LLC and Vireoka LLC. Open **User management** after signing in to AgentVire. Passwords are delivered privately; they are never available from the account directory.

## First sign in and account ownership

The ten existing executive logins are `atmakosh.ceo`, `atmakosh.cfo`, `atmakosh.cmo`, `atmakosh.cto`, `atmakosh.coo`, and the corresponding five `vireoka` logins. Each temporary password is unique. First sign-in requires changing it before business information becomes available; sign in again with the new password. The President's existing password is preserved.

Use a named account for each person rather than sharing a role login. For example, create a person-specific account, select the company, assign CFO or BILLING, and choose the necessary business units. Disable an unused role placeholder once its responsibilities have moved to named accounts. Never put passwords, payment-card details or API keys in cases, evidence notes or email drafts.

## President and delegated administration

The President can view all users and grant any of the 20 business roles across the seven configured units. The President also retains existing global oversight, approval and reasoned-override controls. The President account and the current administrator's own account are protected against accidental disable, deletion or access replacement. Change your own password in personal account settings.

A USER_ADMIN account manages staff only within its assigned units. It may create or change the 14 department roles other than USER_ADMIN. It cannot create executives, appoint another administrator, manage the President, change itself, or manage a user whose existing access extends beyond its delegated scope. An account combining an executive or administrator role with staff permissions also remains outside delegated staff administration.

Select one company and one or more units when creating or editing an account. The selected role set applies to every selected unit. For different role combinations by unit or access spanning both companies, use separate scoped logins; the President retains a single portfolio-wide login. This avoids accidentally granting a broad Cartesian combination of roles and units.

## Create read update and delete users

1. Open **User management** and review the account directory before creating an account.
2. Under **Create a user**, enter a stable user ID, a person's name, and a unique temporary password of at least 14 characters.
3. Select the company, the minimum necessary roles, and the intended business units. No unit is selected automatically for a new user.
4. Enter the reason for access and select **Create user**. Share the temporary password through a private channel; the user must replace it at first sign-in.
5. Expand a user in the directory and choose **Edit roles and units** to change access. Saving replaces the entire role and unit selection, rather than adding to an unseen existing set.
6. Use **Reset disable or delete access** to set a new temporary password, disable or enable the account, or delete its login access. Deletion requires typing the exact user ID.
7. Refresh if another administrator changed the account while you were editing. Stale changes are rejected rather than overwriting newer decisions.

Creation, changes, resets, enable/disable and deletion are recorded in the audit trail with the acting administrator and reason. Updates and resets revoke existing sessions. Disabling prevents new sign-ins. Deletion disables the account, revokes grants, invalidates its credential and retains an audit tombstone. Its user ID cannot be reused. Deleting login access does not erase financial records, customer data or historical case attribution.

## Role permissions and useful outcomes

All business roles are scoped to assigned units. The President is the separate system-wide authority.

| Role | Work and information | Useful outcome |
| --- | --- | --- |
| CEO | CEO workflow steps, scoped relationships, CEO preparation and plans | Qualified opportunities, accountable priorities and business decisions |
| CFO | CFO steps, financial evidence, CFO preparation and plans | Supported economics, reconciliation review and financial handoffs |
| CMO | CMO steps, permitted acquisition relationships, CMO preparation and plans | Evidence-based positioning, qualified pipeline and campaign preparation |
| CTO | Technical steps, CTO preparation and plans | Verified readiness, release review and technical risk decisions |
| COO | Service and operating steps, COO preparation and plans | Reliable onboarding, delivery and recovery |
| USER_ADMIN | Scoped account directory and eligible staff lifecycle | Correct access, prompt offboarding and no unnecessary privileges |
| BILLING | Billing request, handoff and provider-outcome steps | Authorized subscription or refund requests with reconciled receipts |
| INVOICING | Invoice draft evidence and issue/settlement records | Correct legal entity, line items and genuine invoice references |
| REVENUE | Assigned-unit finance evidence, matching and exception steps | Explained payment differences and supported reconciliation |
| SALES | Sales qualification intake and scoped manual tasks | Genuine buyer need, source and accountable discovery handoff |
| PARTNERSHIPS | Partner research intake and scoped manual tasks | Verified partner identity, mutual value and pilot handoff |
| CUSTOMER_SUCCESS | Customer outcome, activation and follow-up steps | Observed first value and documented retention opportunities |
| SUPPORT | Triage and resolution steps | Verified customer resolution and clear escalation ownership |
| PRODUCT | Product acceptance and requirements steps | Measurable requirements linked to customer problems |
| ENGINEERING | Diagnosis and implementation evidence steps | Product-backlog fixes with tests and rollback evidence |
| QA | Test definition, acceptance and regression evidence | Independent proof of what passed, failed or remains untested |
| SECURITY | Risk intake and remediation verification | Verified containment and residual-risk evidence |
| PRIVACY | Rights-request intake and outcome evidence | Verified authority and truthful export/deletion receipts |
| SRE | Service condition, recovery handoff and outcome steps | Observed service health and tested recovery evidence |
| AUDITOR | Read-only assigned-unit case steps and finance evidence | Independent review without changing business records |

Assigning multiple roles adds their permissions. In particular, AUDITOR combined with another role does not make that other role read-only. Use a dedicated auditor account for independent review. An ordinary CEO does not receive the CFO finance view or other roles' detailed notes. Department roles cannot open portfolio-wide execution, pricing, integrations, audit exports or unrelated company data.

## Billing invoice and revenue workflow

For a billing request, BILLING records the verified request; REVENUE matches payment evidence; CFO reviews the proposed remedy; BILLING submits the exact handoff for President review and records the genuine provider outcome. For an invoice, INVOICING records the protected draft reference, REVENUE validates amounts, CFO submits the handoff for President review, and INVOICING records actual issue and settlement evidence. Revenue reconciliation similarly routes sources and exceptions through CFO and President review.

These workflows record and govern work. They do not themselves create Stripe invoices, charge cards, refund payments, cancel subscriptions or finalize accounting books. Perform an authorized provider action in its appropriate system, then attach the real result. A draft or approved handoff is not a payment receipt. Keep unresolved exceptions open. Product collection switches, launch checks and JodiUSA's free access retain their existing controls.

## Running department work

Open **Business command center**, select the company and unit, then open **Work queues**. A role can create a process only when it owns that process's first step. For example, BILLING can start billing intake, SALES can start qualification, and PRODUCT can start a product request. ENGINEERING receives its implementation step after the preceding owner completes a handoff; it does not receive an empty case-creation form.

The President may create and route any supported case. Record the actual source, due date, owner, outcome and limitations. The next owner receives the next step. A consequential handoff goes to the President with exact evidence. Mark a step complete only after checking its acceptance conditions. When blocked, state the missing evidence and owner rather than treating the absence of evidence as a pass.

Department users may use the human workspace for scoped manual work. The five original executive AI roles and 35 unit-role plans remain in place. The new departments have human workflows; this release does not claim new autonomous AI billing, invoicing, engineering or security workers. Executive AI preparation remains bounded by its existing qualification and authorization gates.

## Operating rhythm

Each day, department owners review due work, failed handoffs and missing evidence. Each week, administrators review staffing changes, finance owners review reconciliation exceptions, QA reviews failed gates, and the President reviews consequential decisions and the 90-day executive plans. Use named owners, real receipts and a next date for every open exception.

Monitor business outcomes appropriate to each role: qualified opportunities for SALES, observed activation for CUSTOMER_SUCCESS, aging unresolved cases for SUPPORT, unmatched amounts for REVENUE, verified readiness for QA, and recovery results for SRE. Completed records measure activity; they are not automatically customer adoption, collected revenue or business profit.

## Security and maintenance

All account operations require a current authenticated session and CSRF protection. The server rechecks authority and unit scope; hiding navigation is not the access-control boundary. Account directory responses exclude password hashes, salts and integration credentials. Access updates invalidate older sessions, and optimistic versions reject stale edits.

Authentication and scoped access protect private data from anonymous retrieval. Authorized users can still copy information they can see. MFA, independent penetration testing and stronger edge-level traffic controls remain follow-up improvements. Do not claim this release prevents every form of scraping or account compromise.

The new implementation uses `user_management.py`, `saas_roles.py` and `static/user-management.js`, with scope checks in the existing business and human-workflow modules. No new external identity, payment or cloud provider is required. Account profiles and audit records use the existing database. Back up the database before release; keep the previous image for rollback. Password changes made during credential handover must be preserved during any recovery, or deliberately reissued with a recorded reason.

## Release validation

The deployed candidate passed 374 automated server tests and browser checks covering all 15 department dashboards, user creation, edits, reset, disable/enable, deletion, first-login password changes, delegated administration and auditor restrictions. Live verification confirmed the President controls, seven-unit scope, 20 assignable roles, 22 processes and preserved business records. All ten executive role logins were verified after their private credential handover; the first-change gate remained enforced. The previous release image and predeployment database backup are retained.

See [release evidence](release-evidence/user-management-20261104.json) for the exact candidate and verification receipts.
