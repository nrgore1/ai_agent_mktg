# AgentVire design and architecture

Release baseline and original PRD reconciliation

Prepared for the founder and engineering team • 30 October 2026

AgentVire is a founder-controlled marketing operations system for 17 products. It keeps product facts, research, campaign drafts, approvals, execution evidence and measured results together. Its release boundary is the original research-to-approval-to-evidence workflow. Product signup repairs, speech grading and application-specific media recovery belong to their respective product roadmaps.

The original PRD explicitly allowed a working mock connector for the first release. That core workflow is implemented, and the current automated suite passes 187 tests. This is not a declaration that every live connector, every product launch or every later backlog item is complete. The broader production ambitions remain conditional on product readiness, verified claims, eligible audiences, configured accounts and reliable measurement.

The deployed application uses Python’s standard-library HTTP server, SQLite and a vanilla JavaScript interface. The initial FastAPI, PostgreSQL, Redis and React architecture was a proposal; it is not the system currently running. This manual documents the implementation that exists and identifies deliberate future migration points.

## How to read this document

| Section | Subject |
| --- | --- |
| 1 | PRD boundaries and acceptance evidence |
| 2 | Components and responsibility boundaries |
| 3 | Workflow and action state machine |
| 4 | Data model and isolation |
| 5 | Security and provider boundaries |
| 6 | Measurement and commercial reasoning |
| 7 | Deployment and recovery |
| 8 | Release decisions and remaining handoff |

Use the programmer’s manual to install, extend, test and operate the system. Use the user guide for daily work and all 17 product playbooks. Prices in the user guide are planning recommendations, not checkout changes or verified actual margins.

## Evidence baseline

Original source: the founder’s initial pasted marketing strategy and PRD. Implementation inspected: repository branch `codex/product-strategy-os`, baseline commit `5a75aa658c239d7319ae11d973f07326a24f3744`. Runtime inspected: `growthpilot-staging:8281172-privacy-v4` at agentvire.com. The later repository commit includes documentation and evidence beyond the deployed runtime. Tests: `python3 -m unittest discover -s tests`, 187 passing on this review.

## 1 Original PRD and release acceptance

The PRD’s central contract is controlled marketing execution: research an opportunity, prepare an evidence-supported draft, approve its exact payload, execute through an allowed connector and record the outcome. The acceptance unit is an action with traceable evidence, not an autonomous agent’s assertion that a campaign succeeded.

The live inventory contains 17 products, 50 channels and 279 execution tasks. All 17 product records still require verification, have no approved claims and have no approved catalog price in that registry. Readiness cannot be inferred from the number of tasks marked complete.

| PRD requirement | Implementation and closeout disposition |
| --- | --- |
| 17 products and 50 channels | Seed registry and editable records exist. Product truth and current channel rules require owner review. |
| Research and evidence | Public HTTPS source capture, provenance and reviewed evidence exist. Broad unattended market discovery is not implemented. |
| Eight marketing agent roles | Deterministic workflow jobs and manager packages represent the roles. They are not eight independent autonomous agents. |
| Draft and founder approval | Exact payload hashes, revisions, expiration, comments, rejection, bounded batch approval and pause are implemented. |
| Execution and evidence | Mock acceptance path, manual submission packages and guarded live adapters exist. Most channels remain manual. |
| Customer and partner funnels | Product-scoped lead records, follow-ups, demos, feedback and launch packages exist. External CRM synchronization remains future work. |
| Analytics and improvement | Keyed event ingestion, idempotency, attribution, actual-only reports and experiment records exist. Full payment reconciliation is separate. |
| Durable governance | Sessions, roles, CSRF, serialized delivery queue, audit chain and verified backups are implemented. Off-host audit anchoring is not. |
| Operational documentation | This set replaces the early mock-only descriptions and defines current limitations and handoff. |

The 187-test suite covers governance, authentication, HTTP permissions, workflows, schedules, ingestion, financial-model validation, consent and recovery behavior. Passing tests establish software behavior under tested conditions; they do not establish commercial traction, legal applicability, human grading accuracy or deliverability for every provider.

### Boundaries that prevent further scope drift

AgentVire owns campaign preparation, exact approvals, execution records, contact consent integration, marketing analytics and the release checklist. Each product owns registration, billing, product features, customer data, its own consent entry points and its technical readiness evidence. AgentVire may track those dependencies without absorbing their implementation into its core release.

The PRD’s 90-day ambitions—40 or more subscriptions, 3–5 institutional pilot proposals, 15–20 investor conversations and 8–10 champions—are planning targets. They are neither acceptance tests nor achieved outcomes. Previously completed planning checkboxes are not proof of customer acquisition.

## 2 Components and responsibility boundaries

```text
Founder and product operators
          |
          v
HTTPS reverse proxy -> JavaScript dashboard
          |                 |
          +---- HTTP API ---+
                    |
        Identity and product permissions
                    |
       Platform workflow and approval policy
          /          |              \
 Research and LLM   SQLite       Background worker
 draft preparation records       schedules and outbox
          |        audit                 |
          |        sessions        Allowed connectors
          |                            /       \
   Reviewed evidence            mock/manual   live provider
                                      \       /
                                  receipts and actual events
```

The browser is a review and command surface. It never receives provider secrets and is not trusted to enforce business permissions. `server.py` validates sessions, request size, CSRF, role and product scope before calling domain methods. `identity.py` manages passwords and sessions. `core.py` implements the base store and approval workflow; `platform.py` adds editable records, generation, live delivery and reports.

`manager.py` prepares launch packages, activation journeys, demonstration plans, feedback prompts and measured reviews. `execution.py` tracks execution work. `economics.py` and `commercial_policy.py` support analysis; neither is a billing or payout service. Consent and recovery modules coordinate marketing records with product-owned account lifecycle events.

The worker is a background thread in the same application process. It runs approximately every 15 seconds and handles draft schedules, queued deliveries, reviews, daily backups and enabled retention. There is no independent queue broker. Process availability is therefore also scheduler availability. The original proposed daily 6 AM research timetable is not an activated automation.

### Connector responsibilities

Mock execution produces a simulated receipt. Manual export prepares a founder submission package and later accepts a founder-reported URL. Postmark is enabled in the inspected deployment but remains subject to recipient, content and approval gates. GitHub issue and SMTP sandbox adapters require separate configuration and enablement. There are no general-purpose authenticated social publishing connectors for all 50 registry channels.

Local Kimi generates constrained revisions from verified evidence. The configured tag is `hf.co/mradermacher/Kimi-VL-A3B-Instruct-GGUF:Q2_K`; this is not a claim that it is the newest or strongest Kimi. The bridge is a network dependency. No qualified Llama or Qwen fallback is represented as active in this release.

## 3 Workflow and action state machine

An opportunity begins with a selected product and channel. The operator verifies the product’s audience, landing page, readiness and supported claims; reviews the channel’s destination and rules; and captures evidence. The planner creates a campaign and draft action. Research content is data, never authority to approve or execute.

The payload binds product, campaign, connector, channel, destination, account, recipient, title, content, claims, evidence and cost. Canonical serialization produces a SHA-256 hash. Approval records the exact hash, reviewer and expiry. Changing any relevant payload content creates a new version and invalidates the old approval.

| Transition | Required condition and meaning |
| --- | --- |
| Draft to approved | Founder or administrator reviews the exact current payload. Approval expires after 24 hours. |
| Approved to mock executed | Mock connector records a simulation, not a real publication or customer event. |
| Approved to manual export | Approved package is downloadable. Export is not publication. |
| Export to submitted | Founder records an actual submission URL and note. This is founder-reported evidence. |
| Approved to queued | Live adapter, configuration and execution gates pass. Unique action ID prevents duplicate queue entries. |
| Queued to executing | Worker obtains a delivery lease and obeys provider rate limits. |
| Executing to executed | Provider acceptance is recorded. Acceptance is not proof of inbox placement, response or conversion. |
| Executing to unknown | Ambiguous network outcome or expired in-flight lease. Manual reconciliation precedes any new attempt. |

Rejection and revision are available before an irreversible or uncertain delivery stage. Queued, executing and unknown actions cannot be edited into a different message under the same approval. A batch contains at most 20 explicit action IDs and hashes; it approves those actions rather than authorizing an open-ended campaign.

Pause blocks further workflow execution where checked. It cannot recall a request already accepted by a provider. Operator recovery must inspect queued and in-flight work before resuming. The outbox offers at-most-one queued record per action, not a guarantee of exactly-once effects across a remote network.

### Role mapping to the original eight agents

Market Intelligence supplies research and evidence. Content and SEO prepares drafts. Launch and Directory selects channel packages. Customer Acquisition manages trial journeys and follow-ups. Investor Research prepares qualified profiles and exact outreach. Partnerships and Champions tracks introductions and referral hypotheses. Analytics and Optimization compares measured results. Compliance and Evidence checks facts, destinations and approval requirements. These are accountable workflow responsibilities with recorded jobs, not unconstrained autonomous identities.

## 4 Data model and isolation

SQLite is the authoritative application store. WAL mode supports concurrent reads; application transactions use `BEGIN IMMEDIATE` to serialize writes. The architecture targets a single host and a bounded operating team. Product permissions are enforced at the HTTP boundary, not by database row-level security.

| Table | Purpose and important constraints |
| --- | --- |
| records | JSON entities keyed by kind and ID, with product ID for scoped records. Products, actions, campaigns, leads, events and later modules share this store. |
| audit | Ordered timestamped actor/event/entity/details entries with previous and current hashes. |
| settings | Persisted application settings including workflow controls. |
| deliveries | Unique action ID, payload hash, status, attempts, lease, result and creation time. |
| ingestion | Idempotency key, product ID and event ID for analytics replay protection. |
| api_keys | Hashed product-scoped analytics keys and labels. |
| provider_limits | Next allowed request time by connector. |
| users and sessions | Password material, role/scopes, hashed session identifiers, CSRF and expiry. |
| auth_limits | Rate-limit state for authentication failures. |
| audit_exports | Reserved audit-export bookkeeping; not evidence of external immutable storage. |

The JSON record model made the small portfolio system easy to extend. Its tradeoff is weaker database-level shape enforcement and harder cross-record querying. Domain validators and tests are essential. Existing seed records are inserted only when absent; changing `registry.json` does not migrate live values.

### Relationships and integrity

Campaigns belong to products. Actions refer to campaigns and include the exact external payload. Evidence supports claims; verification is explicit. Events refer to the product and optionally a matching campaign. Leads retain their product context and consent state. Delivery rows bind to one action and its payload hash. Report generation excludes simulated events from actuals.

Do not nest store transaction contexts. Reads also open serialized transactions, so nested connections can lock each other. Pass an existing database connection through a domain operation when atomic work spans multiple records. Complete remote requests outside database locks, then persist the result with a version or lease check.

### Audit properties

The hash chain detects ordinary editing, deletion or reordering when verified against the stored chain. Application code appends records rather than editing history. A privileged person able to rewrite the database and chain is outside that guarantee. External anchoring or write-once storage is a future requirement; “tamper-evident” must not be promoted to “tamper-proof.”

## 5 Security and provider boundaries

Passwords use salted scrypt with parameters N=16384, r=8 and p=1. Passwords must contain at least 14 characters. Session tokens are hashed in the database, expire after eight hours and are carried in an HttpOnly, SameSite Strict cookie. The inspected HTTPS deployment enables Secure cookies. Mutations require the session’s CSRF token, except explicitly authenticated public or service interfaces.

| Role | Intended authority |
| --- | --- |
| Founder or administrator | Portfolio administration, verification, exact approval, execution, pause, user management and protected economics. |
| Operator | Draft and manage permitted records for assigned products; cannot grant founder approval. |
| Viewer | Read permitted records without mutation. |

Login throttling locks an address-derived key after eight failed attempts for 15 minutes. Password changes revoke sessions. The application has no documented MFA, SSO or self-service password-reset service. These are future identity improvements, not hidden capabilities.

Research fetches allow public HTTPS on port 443 only. They reject URL credentials, non-public DNS destinations and redirects, pin the resolved connection, bound responses and apply timeouts. Captured text remains unverified until reviewed. This boundary reduces server-side request forgery and prompt-injection exposure; it does not establish that a source is truthful.

Provider keys belong in protected environment or data-volume configuration. Analytics keys are product-scoped and shown once. Postmark account mapping, financial source snapshots, service keys and initial credentials must not enter Git, screenshots or support logs. A configured sender establishes technical capability, not recipient permission.

### Consent and account lifecycle boundary

Marketing forms collect explicit product-specific permission. Registration alone is not converted into marketing permission under the portfolio policy. Export and deletion links use private access tokens; account integration uses product-specific signed requests. Jodibana’s optional tenant marketing feature requires tenant acceptance and configuration before JodiUSA can use it.

Approved operational defaults remove unconfirmed requests after seven days, remove withdrawn contact details after 30 days, expire private access links after 30 minutes and retain minimal suppression information to prevent accidental re-import. These are product settings, not a universal legal retention schedule.

Product-native deletion, media ownership and recovery journals remain separate from AgentVire’s marketing contact lifecycle. Postmark provider-history deletion remains blocked because the account-level deletion facility is not configured. A local deletion receipt must not claim the provider’s history has also been deleted.

## 6 Measurement and commercial reasoning

Product backends send aggregate events through product-scoped analytics keys with unique idempotency keys. Campaign and UTM identifiers connect actions to measured acquisition. Reports aggregate recorded funnel events, revenue and cost; they exclude mock events. Missing instrumentation means unknown performance, not zero customer demand.

The current report’s acquisition cost divides recorded campaign cost by recorded paid conversions. Its trial-to-paid ratio compares totals in the selected data, not a fully modeled retention cohort. Events are counts rather than deduplicated people. These limitations must remain visible in business decisions.

### Two analysis paths

The strategy engine can compare reprice, redesign coverage, restructure commissions and withdraw scenarios. Its demand response, partner attrition and planning cash estimates are hypotheses unless independently measured. A separate `actual_only` mode rejects scenario inputs and requires attested completed-period financial aggregates. Operational payment events, cash processor movements and recognized revenue are different records.

The commercial policy calculates contribution after usage, support labor, allocated operating cost, payment fees, refunds and partner payouts. Its 75% floor is the founder’s internal operating-margin target. It is not a U.S. regulator’s definition of margin. No applicable regulator, draft rule, capital requirement or legal deadline has been established for the portfolio as a whole.

| Quantity | Decision use |
| --- | --- |
| Net realized revenue | Price after modeled discount and refund allowance; tax and pass-through treatment require reconciliation. |
| Operating contribution | Net revenue less delivery, support, allocated operations, fees and partner payout. |
| Operating margin | Operating contribution divided by net revenue. Undefined for a free offer. |
| Owner recovery | Separate economic recovery of founder investment over an assumed horizon. Not automatically a cash expense or GAAP charge. |
| Pricing floor | Minimum price at the assumed scope, volume and commission. Not proof of customer willingness to pay. |

A proposed price must clear both a customer-value test and a cost test. If competitors are cheaper and customers do not value the difference, redesign the scope or hold the launch; raising price merely to make a spreadsheet pass is not a strategy.

The commercial modules cannot change billing, issue partner payouts, trade assets or make financial commitments. Historical task labels may predate the founder’s provisional commercial approval. The valid interpretation is conditional commercial authorization with factual execution gates, not a blanket permission to publish unsupported claims.

## 7 Deployment and recovery design

The public entry point is https://agentvire.com behind the VPS HTTPS reverse proxy. The application container is `growthpilot-staging-growthpilot-1`; the staging name is a deployment label and does not make the public site disposable. Persistent data lives under `/app/data`. The source release and container image must be recorded separately because documentation-only commits do not require a runtime deployment.

The current configuration includes enabled Postmark, consent email and retention. GitHub and SMTP live delivery are not globally enabled by the inspected settings. Kimi uses `http://172.16.1.1:11436` through a bridge and the configured local model. That endpoint’s availability must be tested independently of application health; a successful `/health` response does not prove inference works.

### Recovery assets

The backup operation uses SQLite’s online backup mechanism and checks integrity. The worker creates daily backups while it runs. Privacy recovery bundles additionally include signed journals and file checksums. A safe restore requires the original signing key and a separately retained fresh privacy checkpoint, no older than one hour, so erased contact data is not resurrected from an old database.

Restore into a new destination, verify archive structure and checksums, reconcile erasure markers, verify database integrity and audit continuity, then run application checks before cutover. Never test a restore by overwriting the active database. A rollback to an older image also requires schema and privacy-history compatibility; image rollback alone is insufficient.

### Availability and scale limits

The application and worker share a host and process. The database, daily backup and journals on the same VPS are not an offsite disaster-recovery system. No measured recovery-time or recovery-point SLA is promised. External backup replication, independent monitoring and off-host audit anchoring remain operational work.

At higher load, measure lock contention, queue delay, provider latency and report cost before migrating. Move to PostgreSQL, a separately deployed worker and a durable queue when measured concurrency and availability needs justify it. Preserve payload hashes, action IDs, idempotency keys and approval history through any migration. A framework rewrite alone does not improve governance.

### Verification at closeout

The current repository suite passed all 187 tests. Previous product privacy and recovery drills remain supporting evidence in their product handoffs. This documentation review did not send campaigns, change billing, activate tenant marketing or restore any production database. Runtime behavior remains unchanged by the documentation release.

## 8 Release decisions and remaining handoff

Close the original mock-capable AgentVire core as a documented operating baseline. Continue using its approval and measurement workflow. Do not label the complete long-term PRD or all portfolio launches finished: several requirements depend on external systems, verified product facts or later engineering.

| Priority | Remaining work | Completion evidence |
| --- | --- | --- |
| P0 before campaigns | Verify product claims, landing experience, exact account, eligible audience and required email footer details | Reviewed product/channel records and a tested exact action |
| P0 before paid offers | Reconcile actual delivery costs, billing SKU, refunds and partner terms | Completed-period finance close and approved offer version |
| P0 operations | Retain off-host backups and conduct isolated restore drills | Successful independent restore and retained checkpoint evidence |
| P1 integration | Connect approved social/CRM/payment providers as needed | Sandbox contract tests, least-privilege credentials and exact-action acceptance |
| P1 reliability | Monitor worker, queue, model bridge and backup freshness | Alerts tested against deliberate failures |
| P1 security | Add stronger identity and external audit anchoring | Independent control tests and recovery procedures |
| Product handoff | OraToPlus grading, product-specific activation and provider deletion gaps | Product owner’s evidence; do not bulk-complete AgentVire tasks |
| Future scale | PostgreSQL, independent worker and richer orchestration | Measured need plus parity and migration tests |

### Ownership

The founder owns offer choices, claim verification, exact external approval and risk acceptance. Product owners own readiness and supported features. A marketing operator owns source review, drafts, consent evidence, follow-ups and weekly analysis. Engineering owns connectors, access controls, instrumentation and recovery. Finance owns completed-period reconciliation and commission eligibility. One person may hold several roles, but the records must distinguish the decisions.

### Sources and document control

The initial pasted PRD is the scope authority. The inspected source tree, automated tests and safe runtime inventory establish implementation facts. Detailed evidence is retained with this closeout package; no private keys or raw customer records were copied into it.

Repository: https://github.com/nrgore1/ai_agent_mktg/tree/codex/product-strategy-os

Primary technical references are the implementation modules, `docs/api-v2.md`, `docs/launch-learn-operations.md`, `docs/commercial-policy-75-percent.md` and `docs/privacy-media-recovery-2026-10-30.md`. Older mock-only architecture descriptions are superseded by this baseline. Recheck the deployed image, provider settings and product registry before relying on this document after a release change.

Document owner: AgentVire founder. Review trigger: any new execution connector, identity boundary, data store, approval rule, model provider or commercial execution path.


## Original PRD integration release 0.5.0

See [integration contracts, operating workflow and release boundary](prd-integrations-0.5.0.md) for the nine-provider desk, consent-preserving CRM exchange, approved social/calendar handoffs, payment evidence and test coverage. Product-specific development remains on separate backlogs.
