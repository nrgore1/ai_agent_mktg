"""Assignable SaaS staff roles. They do not inherit executive AI or payment authority."""
SAAS_ROLES = {
 'USER_ADMIN':'Company user administrator, scoped staff access and account lifecycle',
 'BILLING':'Billing operations, subscription requests and refund evidence',
 'INVOICING':'Invoice management, draft validation and provider receipts',
 'REVENUE':'Revenue reconciliation, payment matching and exceptions',
 'SALES':'Sales operations, buyer qualification and sales handoffs',
 'PARTNERSHIPS':'Partner operations, research and pilot coordination',
 'CUSTOMER_SUCCESS':'Customer success, activation and retention follow-up',
 'SUPPORT':'Customer support, triage and resolution evidence',
 'PRODUCT':'Product management, requirements and acceptance scope',
 'ENGINEERING':'Engineering, diagnosis and implementation evidence',
 'QA':'Quality assurance, independent acceptance and regression checks',
 'SECURITY':'Security operations, risk review and incident evidence',
 'PRIVACY':'Privacy operations, consent and rights-request evidence',
 'SRE':'Infrastructure operations, monitoring and recovery evidence',
 'AUDITOR':'Read-only auditor, assigned-unit cases and finance evidence',
}
READ_ONLY={'AUDITOR'}
STAFF_DELEGATABLE=set(SAAS_ROLES)-{'USER_ADMIN'}
def saas_processes(step):
 def flow(name,role,title,acceptance):return step(title,role,acceptance)
 return {
 'billing_operations':{'name':'Billing request and recovery','lane':'Billing','steps':[
 step('Verify billing request','BILLING','Record tenant, account authority, subscription and requested change; no card details.'),
 step('Reconcile payment evidence','REVENUE','Match provider references, amount, currency, refunds and duplicate risk.'),
 step('Review financial remedy','CFO','Confirm exact financial exposure, policy and unresolved differences.'),
 step('Review billing handoff','BILLING','Submit exact remedy and provider authorization. No charge, refund or cancellation is performed by this case.',True),
 step('Record provider outcome','BILLING','Attach genuine provider receipt and reconciled result, or retain the unresolved state.')]},
 'invoice_operations':{'name':'Invoice preparation and reconciliation','lane':'Billing','steps':[
 step('Prepare invoice evidence','INVOICING','Record legal entity, customer authorization, invoice reference, line items, currency and due date; link the protected draft.'),
 step('Validate invoice amounts','REVENUE','Tie line items, credits, tax review and totals to source evidence; avoid duplicate invoices.'),
 step('Review invoice handoff','CFO','Review exact draft and accounting treatment before external issue.',True),
 step('Record invoice issue and settlement','INVOICING','Reference actual provider invoice and payment/credit status; draft completion is not issue or settlement.')]},
 'revenue_reconciliation':{'name':'Payment and revenue reconciliation','lane':'Finance','steps':[
 step('Collect period controls','REVENUE','Identify company, period, currency, bank and processor source controls.'),
 step('Reconcile exceptions','REVENUE','Explain unmatched amounts, credits, refunds and deferred revenue without inventing recognition.'),
 step('Review reconciliation','CFO','Review source tie-out and unresolved exceptions. Acceptance does not finalize books without accounting evidence.',True),
 step('Record reconciled evidence','REVENUE','Reference accepted evidence and remaining items, not unsupported actual margins.')]},
 'sales_intake':{'name':'Sales qualification handoff','lane':'Sales','steps':[
 step('Qualify sales request','SALES','Record genuine source, buyer problem and appropriate contact permission.'),
 step('Verify acquisition fit','CMO','Check supported claims, destination and audience eligibility.'),
 step('Accept discovery scope','CEO','Record accountable discovery owner, outcome and next date.')]},
 'partner_intake':{'name':'Partner research handoff','lane':'Sales','steps':[
 step('Prepare partner evidence','PARTNERSHIPS','Record partner identity, source, mutual benefit and permissions; no promise of fees.'),
 step('Qualify partnership','CEO','Verify relationship and route any proposed pilot through the existing partnership gates.')]},
 'customer_success_operations':{'name':'Customer success follow-through','lane':'Operations','steps':[
 step('Confirm customer outcome','CUSTOMER_SUCCESS','Record eligible customer scope, permissions and desired first value.'),
 step('Verify relevant journey','CTO','Link current environment-specific first-use evidence and limitations.'),
 step('Record activation and follow-up','CUSTOMER_SUCCESS','Record observed use, permitted follow-up and objections; tests are not customer adoption.'),
 step('Review delivery outcome','COO','Verify actual service result and assign remaining obligations.')]},
 'support_operations':{'name':'Support triage and resolution','lane':'Operations','steps':[
 step('Triage customer request','SUPPORT','Record authorized scope, impact and response owner without secrets.'),
 step('Diagnose issue','ENGINEERING','Reference reproduction and a separate product-backlog remedy.'),
 step('Review consequential remedy','COO','Review exact account change, refund or deployment handoff; provider execution stays separate.',True),
 step('Verify customer resolution','SUPPORT','Record genuine resolution and permitted communication evidence.')]},
 'product_delivery':{'name':'Product request through release evidence','lane':'Engineering','steps':[
 step('Define product acceptance','PRODUCT','Record problem, supported scope, acceptance and affected users.'),
 step('Prepare implementation evidence','ENGINEERING','Reference product commit, tests and rollback; do not change production from this record.'),
 step('Verify independent acceptance','QA','Record actual positive, denied-access, failure and recovery checks for the candidate.'),
 step('Review release handoff','CTO','Review exact release evidence and production authorization.',True),
 step('Record deployment evidence','SRE','Reference actual authorized deployment and post-release checks, or record held status.')]},
 'quality_review':{'name':'Quality acceptance review','lane':'Engineering','steps':[
 step('Define test scope','QA','Identify product, version, environment and acceptance conditions.'),
 step('Record test outcomes','QA','Attach observed passes, failures and untested coverage; never approve failed gates.'),
 step('Review quality outcome','CTO','Decide next remediation or release preparation with current evidence.')]},
 'security_operations':{'name':'Security review and remediation','lane':'Security','steps':[
 step('Record scoped security risk','SECURITY','Record authorized affected scope, evidence and containment recommendation without exploit secrets.'),
 step('Prepare remedy','ENGINEERING','Link product-level diagnosis, fix and rollback evidence.'),
 step('Verify security acceptance','QA','Record authorized isolation and regression tests against the current candidate.'),
 step('Review security release handoff','CTO','Review exact production change and risk evidence.',True),
 step('Verify security outcome','SECURITY','Record residual risk and actual remediation evidence.')]},
 'privacy_operations':{'name':'Privacy request and evidence','lane':'Privacy','steps':[
 step('Verify rights request scope','PRIVACY','Record verified requester authority and minimal request reference; no unnecessary personal data.'),
 step('Prepare supported action','CTO','Identify applicable product/provider capability, retention constraints and recovery continuity.'),
 step('Review privacy action handoff','COO','Review exact authorized action and unresolved provider limits.',True),
 step('Record provider and product result','PRIVACY','Verify actual export/deletion receipts and retained scope; unavailable provider erasure stays open.')]},
 'infrastructure_operations':{'name':'Infrastructure monitoring and recovery','lane':'Operations','steps':[
 step('Record service condition','SRE','Record service, environment, health and actual monitoring or recovery evidence.'),
 step('Prepare remedy scope','CTO','Review root cause, customer impact and rollback or trusted recovery procedure.'),
 step('Review infrastructure handoff','SRE','Submit exact change and restore evidence for President review.',True),
 step('Verify operational result','SRE','Record actual authorized result, alerts and remaining recovery dependencies.')]},
 }

