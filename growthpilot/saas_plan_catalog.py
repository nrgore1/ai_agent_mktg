"""Concrete department deliverables; no autonomous external execution."""
OBJECTIVES={
 'USER_ADMIN':[
 ('Establish named owners and least-privilege access','Review assigned-unit users, role needs and first-login handover; record the responsible person for each role without credentials.'),
 ('Verify joiner mover and leaver controls','Exercise approved account changes and session revocation using synthetic accounts; review real access exceptions with the President.'),
 ('Complete the quarterly access review','Reconcile enabled access to current responsibilities; document approved removals, protected accounts and unresolved ownership.')],
 'BILLING':[
 ('Baseline subscriptions and collection gates','Inventory applicable free and paid access, renewal and refund states with provider references. Preserve free JodiUSA and disabled live collection where required.'),
 ('Verify billing recovery and customer remedies','Collect failed-payment, payment-method update, renewal, cancellation and delayed-refund evidence; distinguish tests from live transactions.'),
 ('Review billing quality and leakage','Reconcile actual billing exceptions and recovery outcomes; report unsupported charges or missing evidence. No charge or refund is executed by this plan.')],
 'INVOICING':[
 ('Define invoice controls and source records','Identify the legal issuer, customer authority, currency, line-item sources, numbering and tax-review owner; create a protected sample draft reference.'),
 ('Validate invoice credit and settlement evidence','Trace eligible draft-to-issue, credit and payment records; use labelled synthetic examples where no genuine invoice exists. Route issue requests for approval.'),
 ('Review receivables and invoice accuracy','Report actual aging, credits and unmatched settlement, or explicitly report no issued invoices; reconcile to the revenue owner.')],
 'REVENUE':[
 ('Tie out available expense and payment evidence','Inventory periods and source totals; separate cash, recognized revenue, equipment and owner investment. Identify missing records and provisional allocations.'),
 ('Reconcile one observed operating period','Match processor, bank and source records; explain deferred revenue, refunds, fees and allocation differences for CFO review.'),
 ('Prepare the quarter reconciliation handoff','Produce company and unit controls, outstanding exceptions and source-linked economics. Do not describe provisional books as finalized.')],
 'SALES':[
 ('Build a qualified discovery queue','Define buyer fit, genuine source, customer problem, permission status and next owner. Do not convert researched contacts into an opted-in list.'),
 ('Conduct eligible discovery and track first value','Record actual authorized conversations, objections, trial activation and next steps, or no activity; use only verified offers and destinations.'),
 ('Review opportunity conversion and sales learning','Compare genuine qualified opportunities, activation and conversion; recommend the next sales experiment with evidence and no invented pipeline.')],
 'PARTNERSHIPS':[
 ('Prioritize evidence-based partner pilots','Research partner identity, mutual value, operating model and conflicts; prepare scoped pilot hypotheses without promising commissions.'),
 ('Prepare and validate a scoped pilot handoff','Document genuine partner feedback, responsibilities, customer permission and measurable success; route exact terms for approval before commitment.'),
 ('Review partner value and economics','Compare observed pilot results, service obligations and supported economics; recommend continue, revise or stop with unresolved risks.')],
 'CUSTOMER_SUCCESS':[
 ('Define first-value journeys and support ownership','Map verified free or eligible product journeys, onboarding steps, consent, escalation and first-value evidence; retain product limitations.'),
 ('Validate onboarding with authorized participants','Record observed activation, objections, support needs and permitted follow-up. Synthetic tests must not count as customer adoption.'),
 ('Review repeat use retention and service outcomes','Report actual cohorts and repeat value where data exists, with sources and coverage; propose a measured retention improvement.')],
 'SUPPORT':[
 ('Establish triage and escalation runbooks','Define support route, identity verification, severity, responsible owner and safe escalation; avoid unnecessary customer data in evidence.'),
 ('Verify resolution and recovery handoffs','Exercise representative incidents and authorized requests; link separate product fixes and distinguish synthetic drills from real resolution.'),
 ('Review recurring issues and response quality','Summarize observed response and resolution times, repeat issues and knowledge gaps; assign prevention work with acceptance criteria.')],
 'PRODUCT':[
 ('Translate customer needs into acceptance scope','Review current identity, claims, offer assumptions and constraints; prioritize customer problems with measurable acceptance and an executive reviewer.'),
 ('Validate the highest-value supported journeys','Collect user evidence and product-backlog acceptance results; retain grading, billing and privacy restrictions until their gates pass.'),
 ('Choose the next quarter from observed value','Compare observed adoption, quality, service cost and feedback; present a supported roadmap with explicitly labelled hypotheses.')],
 'ENGINEERING':[
 ('Prepare the highest-risk reproducible fixes','Reproduce assigned failures in authorized environments; link code, diagnosis, tests and rollback on separate product backlogs. Use no Google Cloud.'),
 ('Verify integration and failure handling','Attach end-to-end, retry, idempotency and recovery evidence for relevant providers and local inference; no unsupported numeric grading.'),
 ('Reduce repeat failure and maintenance risk','Review regression and operational evidence; document technical debt, mitigations and tested release procedures without claiming unperformed deployments.')],
 'QA':[
 ('Baseline acceptance and denied-access coverage','Map current version and environment to signup, activation, save/return, roles, limits and recovery checks; retain untested and failed cases.'),
 ('Run scoped end-to-end and recovery checks','Verify applicable payment/provider flows and failure paths using authorized test data; bind results to the candidate and independently record failures.'),
 ('Review sustained regression and release gates','Compare current acceptance evidence and remaining gaps; submit release-readiness recommendations only for gates that actually pass.')],
 'SECURITY':[
 ('Review access risks and exposed data paths','Inventory scoped assets, privileged access, anonymous data denial and secret custody; document risks without copying secrets into cases.'),
 ('Verify authorized controls and incident handling','Review tenant isolation, revocation, rate limits and incident exercises within authorized scope; link remediation evidence and remaining weaknesses.'),
 ('Review residual risks and security ownership','Record verified fixes, unresolved risk owners and recovery readiness; propose further assessment without claiming independent certification.')],
 'PRIVACY':[
 ('Inventory consent retention and provider obligations','Map explicit consent, withdrawal, exports, deletion, media, provider history and backup retention; identify authority and missing provider capability.'),
 ('Verify rights-request and deletion continuity','Trace authorized product/provider results and restored-backup suppression using synthetic evidence where appropriate; unavailable erasure remains unresolved.'),
 ('Review retention exceptions and audit evidence','Verify scheduled retention, minimal suppression and unresolved provider obligations; record genuine receipts rather than treating policy as execution.')],
 'SRE':[
 ('Baseline service health backup and recovery ownership','Inventory relevant VPS services, monitoring, alert owner, external-drive custody and separate recovery-key location; never place secrets in evidence.'),
 ('Verify recovery and operational failure handling','Perform authorized restore and alert checks, attach checksums and coverage, and retain missing historical recovery evidence; no Google Cloud.'),
 ('Review reliability capacity and recovery results','Report observed incidents, capacity and restore outcomes; prioritize recurring controls with owners and actual test evidence.')],
 'AUDITOR':[
 ('Define independent evidence sampling','Review assigned-unit access, cases, financial controls and approval samples; record findings through the President without changing source evidence.'),
 ('Review segregation and exception handling','Inspect samples of authorization, denied access, reconciliation and recovery; identify missing evidence and retain independent read-only access.'),
 ('Deliver the quarterly assurance findings','Present supported findings, coverage limits and unresolved exceptions. The President records the signed review; no assurance certification is inferred.')]
}
KPIS={
 'USER_ADMIN':'Named ownership coverage; access-review exceptions; offboarding evidence',
 'BILLING':'Unreconciled billing cases; tested recovery paths; genuine recovery outcomes',
 'INVOICING':'Draft validation exceptions; actual receivables aging; unmatched settlements',
 'REVENUE':'Source coverage; unexplained differences; unresolved allocation assumptions',
 'SALES':'Permissioned qualified opportunities; observed activation; actual conversion',
 'PARTNERSHIPS':'Verified partner fit; scoped pilots; measured partner value',
 'CUSTOMER_SUCCESS':'Observed first value; repeat use; unresolved onboarding objections',
 'SUPPORT':'Observed response and resolution times; recurring unresolved issues',
 'PRODUCT':'Evidence-backed acceptance coverage; observed value; unresolved hypotheses',
 'ENGINEERING':'Reproduced failures; independently verified fixes; repeat failures',
 'QA':'Applicable gates passed; failures and untested coverage; candidate traceability',
 'SECURITY':'Verified controls; open risk age; remediation evidence',
 'PRIVACY':'Verified consent/rights coverage; unresolved provider and retention exceptions',
 'SRE':'Observed health; restore and alert coverage; unresolved recovery gaps',
 'AUDITOR':'Reviewed sample coverage; supported findings; unresolved exceptions'
}
BACKLOG_ROLES={'finance':'REVENUE','health':'SRE','journey':'QA','entitlements':'QA','identity':'PRODUCT','partners':'PARTNERSHIPS','pricing':'PRODUCT','privacy':'PRIVACY','metering':'BILLING','campaign':'SALES','claims':'PRODUCT','experiment_spec':'SALES','tts_backup':'ENGINEERING','stt_backup':'ENGINEERING','llama_backup':'ENGINEERING','provider_history_scope':'PRIVACY','external_retention_inventory':'PRIVACY','retained_data_review':'PRIVACY','offsite_recovery_rollout':'SRE','jodiusa_owner_optin_acceptance':'CUSTOMER_SUCCESS'}
def responsible_role(task):return BACKLOG_ROLES.get(task['key'])
