# Original PRD and release scope

Baseline reviewed 30 October 2026 at source `5a75aa658c239d7319ae11d973f07326a24f3744`; runtime `growthpilot-staging:8281172-privacy-v4`. Documentation updates do not change the runtime.

## Closeout decision

Close the original mock-capable marketing core as a documented operating baseline. Do not claim every long-term integration or every later portfolio engineering task is complete. The original PRD explicitly accepted an end-to-end mock connector. Research and draft preparation, exact founder approval, execution evidence and actual/simulation separation define that acceptance boundary.

The current implementation is Python standard-library HTTP + SQLite WAL + vanilla JavaScript + an in-process worker. FastAPI, PostgreSQL, Redis and React were proposed architecture, not installed components.

## Requirement traceability

| ID | Original requirement | Evidence | Disposition |
| --- | --- | --- | --- |
| PRD-01 | 17 products and 50 channels | registry.json; test_core.test_registries | Implemented; facts and channel rules still need verification |
| PRD-02 | Eight marketing responsibilities | core.AGENTS; planner jobs; manager packages | Implemented as deterministic workflows, not eight autonomous agents |
| PRD-03 | Research and evidence | providers.py; test_ssrf_private_blocked; evidence tests | Bounded HTTPS capture implemented; broad unattended discovery deferred |
| PRD-04 | Claim validation | test_unsupported_claim; test_claim_requires_evidence; test_claim_cross_product_blocked | Implemented |
| PRD-05 | Exact approval and rejection | test_requires_approval; test_rejection_blocks_execution; test_provider_not_called_before_approval | Implemented |
| PRD-06 | Edit and expiry invalidate approval | test_revision_invalidates; test_expiration | Implemented; 24-hour validity |
| PRD-07 | Duplicate prevention and honest failure | test_idempotent_concurrent; test_failure_no_false_receipt; test_queue_delivery_once; test_unknown_delivery_not_replayed | Implemented; unknown outcomes require reconciliation |
| PRD-08 | Pause and product isolation | test_pause; test_queue_pause; test_product_isolation; test_product_scope | Implemented |
| PRD-09 | Investor/recipient and financial controls | test_recipient_tampering; test_budget_guard | Implemented; no spending/financial commitment connector |
| PRD-10 | End-to-end mock acceptance | test_http.test_session_mock_workflow | Implemented and passing |
| PRD-11 | Leads, partners, demos and feedback | test_lead_management; test_manager | Implemented internal records; external CRM sync deferred |
| PRD-12 | Schedules and experiments | test_due_schedule; test_recurring_schedule; test_lease_recovery_and_slot_dedup | Internal draft scheduling implemented; not autonomous publishing |
| PRD-13 | Attribution and actual results | test_analytics_idempotency_and_scope; test_reports_exclude_simulation | Keyed ingestion implemented; event semantics require product integration |
| PRD-14 | Identity and permissions | test_auth_required; test_csrf_required; test_viewer_cannot_write; test_operator_cannot_approve | Implemented; MFA/SSO deferred |
| PRD-15 | Audit and recovery | test_audit_tamper_detection; test_backup_restore; test_recovery | Local verification implemented; off-host anchoring/DR deferred |
| PRD-16 | LLM and provider interfaces | providers.py, llm_bridge.py, postmark.py, platform.py | Local Kimi and selected guarded adapters; full social/payment/CRM integration deferred |
| PRD-17 | Manuals and operations | architecture.md, programmer-manual.md, user-guide.md, runbook.md | Refreshed to implemented baseline |
| PRD-18 | 90-day growth strategy | campaigns.md, manager activities, founder playbook | Planning workflow, not achieved commercial results |

## Verification and honest limits

`python3 -m unittest discover -s tests` passed 187 tests in 67.979 seconds during this closeout review. Test evidence is recorded in [the evidence summary](evidence/prd-closeout-20261030/verification.json). Tests establish tested behavior, not legal compliance, customer traction or provider readiness for all channels.

Safe live inventory: 17 products, 50 channels, 279 execution tasks. All 17 product records still require verification, with no approved claims or catalog prices in that registry. Do not bulk-complete those tasks or infer readiness from historic planning checkboxes.

## Later additions and handoff

Launch Desk, strategy economics, conditional commercial policy and marketing consent are retained extensions. Product signup repairs, OraToPlus scoring, native media recovery and provider-history deletion belong to their product owners. They remain visible dependencies rather than expanding the original AgentVire core indefinitely.

Five products remain internal: SDIS, One-Man Hedge Fund, Quantsys, SMDP Design and Stablecoin Pipeline. CoffeeBook uses the Memoire domain and shares its launch track. JodiUSA is a Jodibana tenant, not an eighteenth product.

P0 external launch prerequisites remain supported product claims, working activation, exact publishing account, eligible audience, required email footer details and actual commercial validation. P1 platform work includes full provider integrations, independent monitoring, off-host recovery/audit and stronger identity. Scale migration requires measured need. No runtime, billing, commission or campaign execution change is included in this documentation closeout.
