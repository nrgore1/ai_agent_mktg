# Product requirements and release scope
Mission: manage the 90-day customer, institutional and investor strategy with founder approval.

Implemented: all 17 product strategy records and 50 channels, eight deterministic agent roles, campaign planning, approval queue, content editing, evidence, immutable payload fingerprints, 24-hour approvals, mock execution receipts, transactional idempotency, pause, CRM records, conversion input, attribution, scheduled drafting, experiment API, audit events and reporting metrics.

Unknown URLs, pricing, claims and readiness are explicitly unset or require verification. Strategy hypotheses come from the user-supplied portfolio brief, not independent market research.

Acceptance flow: opportunity hypothesis from registry → campaign and draft → evidence/claim checks → exact hash approval → mock execution → simulated event and receipt → dashboard metrics. Mock events never increase actual paid conversions or actual revenue.

Deferred: live web research, LLM generation, email, payment analytics, third-party CRM, social API adapters, bulk execution, real spending, external commitments, multiuser permissions, production deployment. These require configured accounts, tested implementations and explicit action approvals. This repository is not a claim that the autonomous live strategy is complete.
