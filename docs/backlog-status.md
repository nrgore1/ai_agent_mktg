# Current AgentVire release boundary

The current integration scope is recorded in [release 0.5.0](prd-integrations-0.5.0.md). CRM CSV exchange, calendar export and a nine-provider status desk are implemented. The historical ledger below is retained as a dated implementation record, not the current account configuration. Product-specific work is tracked separately in [the product backlog index](product-backlogs.md).

# Backlog implementation status — 0.2.0

This is an implementation ledger, not a declaration that all commercial integrations are live.

| Item | Delivered | Remaining dependency |
|---|---|---|
| Staging access | Domain-specific edge route and individual login | DNS A record to 2.25.123.229; valid TLS verification before public access |
| Authentication | Scrypt passwords, sessions, logout, CSRF, roles and product scopes, password changes, login throttling | MFA/enterprise identity provider not part of this local identity release |
| Product profiles | Editable profiles and source-linked claim verification | Founder verification of actual capabilities, readiness, URLs and pricing for 17 products |
| Evidence | Public HTTPS capture, content hash, review states, product-bound claim evidence | Human source accuracy review; claim checking does not fully understand arbitrary prose |
| Queue | Durable delivery records, leases, rate limiting, expired approval checks, unknown outcome quarantine | Provider-specific reconciliation before enabling unattended live delivery |
| Local LLM | Ollama local-Kimi adapter and encrypted reverse-tunnel bridge | Laptop/model must stay running; newest frontier model exceeds available VPS RAM |
| Research | Bounded public HTTPS fetch, public-IP pinning, timestamps and excerpts | Sources requiring accounts, robots permission, or unsupported content need manual research |
| 50 channels | Registry and editable rules/eligibility/fee verification | All 50 current commercial submission policies need source review; no fabricated verification |
| Launch packages | Product/channel draft, CTA, UTM, checklist and asset slots | Real screenshots, demos and founder-written HN submissions |
| Approvals | Exact payloads, comments, bounded batch approval API, version invalidation and expiry | Review each draft and recipient before public action |
| CRM | Leads, pipeline stages, owner, consent, evidence, fit rationale, follow-ups, referrals and suppressions | Real customer/investor data and account permissions |
| Analytics | Product-scoped keys, replay-safe ingestion, funnel/UTM reports | Each product must emit its real events; no payment credentials discovered or reused |
| Reporting | Actuals, CAC, trial conversion, channel revenue/costs, budgets and report export | Retention/cohort instrumentation and actual event volume |
| Scheduling | Recurrence, dependencies, leases, crash recovery and draft deduplication | Host must remain available; only internal preparation is scheduled automatically |
| Email | Consent/suppression gates and exact test-recipient SMTP sandbox adapter | Sender account, test mailbox and secrets; no unsolicited production email |
| Publishing | GitHub issue publishing adapter with exact configured repo/account | Owner-selected publishing account and tested scoped credentials; other social APIs not implemented |
| Investor workflow | Investor pipeline, evidence, fit scores, rationale, follow-ups and reviewable drafts | Verified investor list and individually approved contact |
| Champions/partners | Partner and champion pipelines, referral codes, consent and follow-up fields | Program terms and attribution events from actual referral systems |
| Experiments | Hypothesis, metric, target, budget, status, result and decision | Meaningful experiment data |
| Budgets | Campaign limits and actual spend reporting; paid side effects remain blocked | Paid advertising provider, reservation accounting and separate spending approval |
| Operations | Daily SQLite online backups, integrity restore checks and hash-chain verification | Off-host backup destination, independent audit anchoring and alert delivery account |
| Scale | Dedicated durable queue tables on SQLite WAL | PostgreSQL/Redis migration remains future work; no demonstrated scale requirement |
| Dashboard | Evidence/experiments/reports/settings, edits, row filters, mobile CSS and focus states | Further usability feedback and accessibility audit |

Live publication, investor contact, spending and purchases are not authorized by a broad request to implement the backlog. The deployed agent still enforces exact-action founder review.
