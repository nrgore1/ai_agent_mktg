# AgentVire programmer manual

Implementation maintenance and operations

Prepared for developers and system operators • 30 October 2026

This manual explains how to run and maintain the implemented AgentVire application without weakening its approval controls. The repository retains the internal package name `growthpilot`. Production uses the same domain code as the local mock-capable application, with protected configuration enabling selected integrations.

The supported baseline is a single-host Python application, SQLite WAL, a vanilla JavaScript dashboard and an in-process worker. It has no required third-party Python runtime dependencies. Do not begin maintenance by replacing it with the originally proposed FastAPI and React stack. Preserve behavior first; migrate infrastructure only for a measured requirement.

## Reading map

| Section | Task |
| --- | --- |
| 1 | Start an isolated development instance |
| 2 | Find the code and understand persistence |
| 3 | Authenticate and use the API |
| 4 | Maintain approval and execution contracts |
| 5 | Integrate analytics and financial inputs |
| 6 | Maintain research and local Kimi |
| 7 | Maintain consent and account lifecycle |
| 8 | Add features safely and test them |
| 9 | Release and roll back |
| 10 | Back up and recover |
| 11 | Diagnose common failures |

Commands use an Ubuntu shell unless specified otherwise. Example ports and database paths are for isolated development. The public service at agentvire.com is not a disposable test environment. Never copy live customer databases or provider credentials into a development checkout.

## Verified baseline

Repository: https://github.com/nrgore1/ai_agent_mktg/tree/codex/product-strategy-os

Inspected source commit: `5a75aa658c239d7319ae11d973f07326a24f3744`. Deployed image: `growthpilot-staging:8281172-privacy-v4`. Current test result: 187 passing. Documentation-only updates may move the branch beyond the inspected commit without changing the runtime image.

This guide includes exact interface examples and operational recipes, but it does not contain passwords, account tokens, customer exports or private financial-source files. Obtain those through the existing secret-management process, not through chat or a repository commit.

## 1 Start an isolated development instance

Use Python 3.10 or newer. From an authorized checkout, run the suite before changing code. Choose a database outside the repository and an unused loopback port. All live providers should remain disabled in development.

```bash
cd ~/projects/vireoka-growthpilot
python3 -m unittest discover -s tests -v
export GROWTHPILOT_DB=/tmp/agentvire-dev/growthpilot.db
export GROWTHPILOT_ENABLE_LIVE=false
export GROWTHPILOT_ENABLE_POSTMARK=false
export GROWTHPILOT_ENABLE_CONSENT_EMAIL=false
export GROWTHPILOT_ENABLE_RETENTION=false
export GROWTHPILOT_SECURE_COOKIE=false
python3 -m growthpilot.server --host 127.0.0.1 --port 18111
```

Open `http://localhost:18111`. The first start creates the database, seeds the registry and writes a random founder password to `initial-login.txt` beside the database. Read that file privately on the machine, sign in as founder and change the password in Settings. It is not an API bearer token. Do not paste the initial password into logs or tickets.

No consent signing secret is needed for a basic mock workflow. Consent tests or local form use require a separate randomly generated development secret of at least 32 characters; never reuse the production secret. A Secure cookie is appropriate on HTTPS production but will prevent an ordinary HTTP development login from behaving as expected if enabled there.

### First acceptance exercise

1. Sign in and inspect Portfolio and Channels. Confirm the 17-product and 50-channel seed.
2. Choose one product, create a mock campaign and inspect the resulting action and evidence requirements.
3. Attempt execution without approval and confirm rejection.
4. Review the exact draft and approve its current hash. Revise it and confirm that the previous approval no longer works.
5. Approve the new version and execute only the mock connector. Confirm the receipt is labeled simulation and actual revenue remains unchanged.
6. Pause the system and confirm new workflow execution is blocked. Verify the audit chain.

The automated tests provide deterministic fixtures for verified product and channel records. Do not bypass readiness by changing a live database just to make a smoke test pass.

The checked-in staging compose file still requires `GROWTHPILOT_API_TOKEN` for legacy configuration compatibility. The application’s dashboard authentication no longer uses that variable. Keep the configured value private; do not tell users to enter it at login.

## 2 Code map and persistence

| Location | Responsibility |
| --- | --- |
| growthpilot/server.py | HTTP routes, session boundary, product authorization, security headers and worker loop |
| growthpilot/core.py | Store, canonical JSON/hash, seed registry, mock planning and core transitions |
| growthpilot/platform.py | Extended validation, record edits, generation, live delivery and reporting |
| growthpilot/identity.py | Users, passwords, sessions, CSRF and authentication throttling |
| growthpilot/providers.py | Restricted research and local model drafting |
| growthpilot/llm_bridge.py | Bounded bridge to local inference |
| growthpilot/manager.py | Launch packages, journeys, demo/feedback records and reviews |
| growthpilot/execution.py | Execution program, tasks and reported evidence |
| growthpilot/economics.py | Strategy dossiers, finance provenance and scenario/actual analysis |
| growthpilot/commercial_policy.py | Decimal-based margin and release-prerequisite assessment |
| growthpilot/marketing_*.py | Product/tenant consent, rights, retention and account lifecycle |
| growthpilot/recovery.py | Signed recovery bundles, checkpoints and safe restore |
| growthpilot/registry.json | Initial 17 products and 50 channels |
| tests/ and docs/ | Regression contracts, operating evidence and guides |

Static HTML, JavaScript and CSS are served by the application. Inspect the complete scripts before editing: some UI behavior is extended later in the file, so changing an earlier function alone may not change the final rendered behavior. There is no front-end package build pipeline to assume.

### Storage conventions

`records` is a JSON entity store keyed by `(kind, id)`. Record kinds include products, channels, campaigns, actions, leads, events, evidence, jobs, schedules, experiments and later operational modules. Separate SQL tables hold deliveries, authentication, ingestion keys and audit history. Use integer product IDs consistently; JodiUSA belongs to Jodibana product 6.

`Store.db()` starts `BEGIN IMMEDIATE`, including for reads. Avoid nested store contexts and network requests while holding a transaction. Use the supplied connection for compound changes. A new save must preserve the intended `product_id`; generic save derives it from the record and is not a substitute for authorization.

Seeds use insert-if-absent behavior. Editing the JSON seed does not update an existing product. For a migration, write a bounded, idempotent routine with old-value checks, a backup, an audit entry and tests for repeated execution. Preserve approval payloads and historical events. Never bulk-rewrite prices, claims or consent states as a side effect of a schema migration.

## 3 Authentication and API access

`POST /api/login` accepts username and password and returns a CSRF token while setting `gp_session`. `GET /api/me` restores the authenticated identity and CSRF token. Send the cookie and `X-CSRF-Token` on subsequent mutations. Use same-origin requests; do not loosen CSRF or origin validation to work around an integration mistake.

The following browser-console example runs only after signing in to an isolated development instance. It prepares a draft and reads it; it does not approve or execute anything.

```javascript
const me = await fetch('/api/me').then(r => r.json());
const response = await fetch('/api/plan', {
  method: 'POST',
  headers: {'Content-Type': 'application/json',
            'X-CSRF-Token': me.csrf},
  body: JSON.stringify({product_id: 4,
                        channel: 'producthunt.com'})
});
if (!response.ok) throw new Error(await response.text());
const draft = await response.json();
console.log(draft.action.id, draft.action.payload_hash);
```

| Interface | Purpose |
| --- | --- |
| GET /health | Minimal public process-health check |
| GET /api/state | Session-scoped dashboard state |
| GET /api/report?product_id=4 | Product report from recorded actuals |
| POST /api/password | Change password with old/new fields; revoke sessions |
| POST /api/users | Administrator creates username, password, role and product scopes |
| POST /api/records/{kind}/{id} | Edit allowlisted fields with role and scope checks |
| POST /api/research | Capture product_id and public HTTPS url |
| GET /api/audit/verify | Administrator verifies the audit chain |
| POST /api/pause | Administrator sets a strict boolean paused value |

Expected failures include 401 for missing authentication, 403 for unauthorized role, scope, CSRF or origin, 400 for invalid domain input, 404 for absent routes and 413 for oversized bodies. General request bodies are bounded at 256 KiB; public marketing requests have a smaller 16 KiB limit. A generic 500 means the operation is not confirmed. Inspect state before retrying an external action.

Founder and administrator have portfolio authority. Operators manage assigned products; viewers cannot mutate. Product-scoped analytics authentication is separate from interactive sessions. Do not reuse an analytics key as an administrator credential.

## 4 Approval and execution contracts

Action commands use `POST /api/actions/{id}/{command}`. Commands include approve, reject, revise, execute, comment, generate, export and record_submission. Payload details vary by connector; use the current UI and domain tests as the contract for revisions rather than sending arbitrary JSON fields.

Approval body:

```json
{"payload_hash":"<hash of the exact current action>"}
```

Bounded approval body at `POST /api/actions/batch`:

```json
{"items":[{"id":"<action id>",
           "payload_hash":"<current hash>"}]}
```

The batch accepts one to 20 explicit items and returns per-item results. It does not execute them. Approval expires after 24 hours. Any material revision changes the version and hash. A generated revision is untrusted model output and must go through the same review boundary.

### Live adapter invariants

`POST /api/external-action` prepares supported GitHub or SMTP sandbox actions. Postmark outreach is prepared through `POST /api/manager/outreach` with a lead ID. Product readiness, supported claims, reviewed channel policy, exact account/destination and recipient requirements remain mandatory. Provider configuration does not relax them.

The outbox’s unique action ID prevents a second queue record for the same action. Workers lease delivery for three minutes and rate-limit a connector to one request per minute. A timeout after provider submission is ambiguous. Store an unknown result and require provider reconciliation; do not automatically replay it or fabricate failure followed by a resend.

Manual export is a distinct contract. It packages exact approved content for a human to submit. The later URL is founder-reported evidence and should not be described as a provider-verified receipt. Mock receipts remain simulation and must never enter actual conversion totals.

### Adding a connector

Implement preparation, validation, account/destination restrictions, execution and receipt normalization separately. Bind all consequential fields into the action hash. Keep secrets server-side. Add tests for expired approval, altered content, wrong product/account/recipient, pause, duplicate queue entry, provider rejection and ambiguous timeout. Run against a sandbox before production enablement. Do not create an unrestricted “HTTP request” connector that bypasses specific provider controls.

Provider spending and financial commitments are blocked in the current application. A future commercial execution connector requires its own authorization model and tests; the economics module’s recommendation is not such an authorization.

## 5 Analytics and finance integration

Create an analytics key with `POST /api/keys`, providing product_id and name as an authorized administrator. The raw key is shown once. Store it only in the corresponding product backend. Send aggregate events using `Authorization: Bearer <key>` to `POST /api/ingest`; this endpoint does not use an interactive session’s CSRF token.

```json
{
  "idempotency_key":"weddingos:activation:example-001",
  "type":"activated",
  "count":1,
  "revenue_cents":0,
  "cost_cents":0,
  "utm_source":"partner_planner",
  "utm_medium":"referral",
  "utm_campaign":"weddingos_free_tools_pilot"
}
```

The key determines the product. If campaign_id is supplied, it must belong to that product. Reusing the same idempotency key must not double-count. Use stable opaque identifiers, not names or email addresses, and keep keys within the validated length. Event count and money fields are nonnegative integers. Do not send customer transcripts, photo URLs, financial holdings or other personal data in analytics.

Define event meaning in the product backend before launch. A signup is not activation; activation is a meaningful saved result. A paid event is not automatically recognized accounting revenue. Correcting an erroneous event requires an auditable reconciliation design; do not manufacture negative counts if the validator forbids them.

### Strategy and financial endpoints

`GET /api/strategy` is administrator-only. `POST /api/strategy/run` accepts product_id, inputs and mode. Illustrative mode runs planning scenarios. Actual-only mode uses `{"mode":"actual_only"}` and rejects scenario overrides. Missing actual cost or revenue evidence remains missing.

`POST /api/strategy/financials` records attested completed-period USD aggregates, source digest, reconciliation status and allocation basis. Follow the validator and finance tests for its exact payload. `scripts/collect_actual_finance.py` collects authorized read-only aggregates, excludes test keys and deduplicates shared processor accounts. It is a snapshot collector, not a continuous accounting integration.

The protected `economics-source.json` belongs beside the application database, outside Git. Separate revenue recognition, refunds, processor fees, payouts, deferred revenue and bank receipts. Never use a customer count times list price as actual revenue. Never sum alternative scenario outcomes or CoffeeBook and Memoire’s shared sale twice.

## 6 Research and local Kimi

The research provider accepts an explicit public HTTPS URL. It checks all resolved addresses, pins the connection, blocks redirects and credentials, limits content to supported text formats and caps response size and time. Captured title, text, source URL, timestamp and hash establish provenance. The evidence status remains unverified until a reviewer accepts it.

Local drafting requires verified product evidence. The current provider checks for a Kimi model name and rejects cloud-tagged models. When approved claims are absent, its constrained mode chooses between cautious invitation templates rather than inventing product capabilities. Generation failure must preserve the previous draft and cannot silently approve or execute a replacement.

| Configuration | Meaning |
| --- | --- |
| GROWTHPILOT_OLLAMA_URL | Server-side local inference endpoint |
| GROWTHPILOT_OLLAMA_MODEL | Exact installed model tag, not a family nickname |
| GROWTHPILOT_BRIDGE_BIND | Address bound by the bounded bridge service |
| GROWTHPILOT_ENABLE_LIVE | Gate for applicable live adapters; default false |
| GROWTHPILOT_ENABLE_POSTMARK | Separate Postmark delivery gate |
| GROWTHPILOT_POSTMARK_FILE | Protected sender/account mapping file |
| GROWTHPILOT_SECURE_COOKIE | True for the HTTPS deployment |

The inspected AgentVire endpoint is `http://172.16.1.1:11436`, using `hf.co/mradermacher/Kimi-VL-A3B-Instruct-GGUF:Q2_K`. A bridge container runs `python -m growthpilot.llm_bridge`. The endpoint’s upstream availability must be checked independently; historic deployment notes may describe a tunnel that should not be assumed healthy merely because the bridge listens.

### Model changes

Benchmark a replacement with fixed verified evidence, unsupported-claim traps, timeout tests, schema validation and draft-version races. A model family’s general reputation is not acceptance evidence. The current provider does not automatically support an arbitrary Llama or Qwen tag; add a deliberate adapter and tests before declaring fallback available.

OraToPlus rubric grading is a separate product responsibility. Existing evidence showed a Qwen backup attempt failing its latency gate, and numeric grades remain withheld until all human-reference gates pass. AgentVire copy generation tests cannot qualify that scoring system.

If inference is unavailable, continue manual editing and review. Do not send data to an unapproved cloud provider or remove claim validation to make generation appear successful. Research sources and model responses are untrusted input even when the endpoint is local.

## 7 Consent and account lifecycle

Public marketing entry points live under `/marketing-updates/` with confirmation, withdrawal and rights flows. Their API operations include subscribe, manage, rights-request, rights-export, rights-delete, confirm and withdraw. Use the product-facing form or current route tests; do not expose raw contact exports through the dashboard or a URL query string.

Brand routing binds WeddingOS to product 4, Memoire to product 5 and JodiUSA to product 6. JodiUSA’s operator is Atmakosh LLC in Georgia; the confirmed responsible contact is Rashmi Gore at rashmi@jodiusa.com. Jodibana tenant feature acceptance is independent of an individual member’s marketing consent. Both must be respected.

### Service integration

`POST /internal/marketing/account` uses product-specific service authentication with a signed body and timestamp tolerance of 60 seconds. Read the lifecycle tests for canonicalization and header names before implementing a client. Bind product, account operation and verified identity to the signature. Do not replace verified account deletion with a public email-address-only request.

Account erasure and marketing withdrawal have different effects. Withdrawal suppresses future marketing. Export/deletion access requires proof of control through private links or a verified product service request. Retain minimal suppression and recovery markers so old backups or imports do not resurrect erased contacts.

### Configuration and retention

`GROWTHPILOT_CONSENT_SECRET` must contain at least 32 characters and remain stable for verification and recovery. Protect `privacy-service-keys.json` and the Postmark account map. `GROWTHPILOT_ENABLE_CONSENT_EMAIL` controls confirmation/rights mail; it does not authorize promotional campaigns. `GROWTHPILOT_ENABLE_RETENTION` enables the daily lifecycle job.

Defaults accepted by the founder are seven days for unconfirmed requests, 30 days before removing withdrawn contact details, 30-minute private access links and a minimal retained suppression record. Changing them is a documented policy revision, not an arbitrary cleanup script.

### Required regression coverage

Test cross-product denial, cross-tenant denial, forged signatures, stale timestamps, replay behavior, expired private links, deletion idempotency, withdrawal before dispatch, disabled tenant features and restored-backup erasure reconciliation. Native media and provider-history deletion require separate product/provider evidence. Postmark account-level deletion is currently unavailable; never mark that step complete solely because local records were removed.

## 8 Change discipline and tests

Start from a clean branch and identify the invariant your change affects. Prefer a small module-level change with a regression test for a real failure. Avoid rewriting the entire UI or data model to solve a documentation or configuration problem.

| Test module | Important contract |
| --- | --- |
| test_core and test_http | Exact approval, simulated effects, authentication and HTTP permissions |
| test_platform | Evidence, records, provider execution, schedules and analytics |
| test_manager and test_execution | Launch packages, activity records, execution program and transitions |
| test_economics and test_commercial_policy | Provenance, actual-only behavior, 75% boundary and invalid inputs |
| test_bounded_kimi_bridge | Bounded inference behavior and failure handling |
| test_audience and test_marketing_consent | Audience eligibility, product-specific confirmation and suppression |
| test_marketing_rights and test_marketing_lifecycle | Private rights access, account integration and retention |
| test_recovery | Signed bundles, fresh checkpoints and privacy-safe restoration |

Run the complete suite after changes to shared domain, authentication, delivery or persistence code:

```bash
python3 -m unittest discover -s tests -v
```

The closeout run passed 187 tests. Keep that result associated with the inspected source revision; it is not a permanent claim about future commits. Browser testing should cover login, product scope, draft revision, exact approval, manual export, reports and responsive navigation. Provider staging tests must use authorized controlled recipients and sandbox accounts.

### UI changes

Use textContent or safe escaping for untrusted research, notes and provider data. Do not interpolate raw HTML from external sources. Keep credentials out of browser state and logs. Preserve the distinction among mock execution, manual export, founder-reported submission and provider-accepted delivery. A cosmetic status label must not imply publication or revenue.

### Adding a product or offer

First determine whether it is a separate product, a tenant or a bundle. JodiUSA is a tenant of product 6; CoffeeBook shares Memoire’s launch domain and must not create duplicate revenue. Add approved scope and instrumentation deliberately. Keep unknown features and prices null until verified. Registry edits do not change live checkout or historical records.

Do not mark old backlog tasks complete because a new document explains them. Completion requires evidence of the task’s actual acceptance criteria. Product engineering work can be handed off without disguising it as a finished AgentVire connector.

## 9 Release and rollback procedure

The existing VPS alias is `weddingos-hostinger-staging`. AgentVire’s current release directory is under `~/growthpilot-staging/current`. Use the existing protected shared environment and both compose files; preserve the named data volume and external reverse-proxy network.

Read-only inspection:

```bash
cd ~/growthpilot-staging/current
docker compose -p growthpilot-staging \
  --env-file ../../shared/.env \
  -f compose.staging.yaml -f compose.kimi.yaml ps
curl --fail --silent https://agentvire.com/health
```

### Deployment sequence

1. Record source commit, image tag, compose configuration and active release path. Confirm the change is authorized and tests pass.
2. Create and verify a database backup plus the required privacy checkpoint. Retain the current image and release directory.
3. Build a versioned image from the tested source. Run it against a separate staging database with live adapters disabled.
4. Check login, permissions, core acceptance, ingestion replay, model timeout behavior and any changed provider contracts.
5. Pause workflow execution for the cutover and inspect queued or unknown deliveries. Never replay an ambiguous action during deployment.
6. Update the release using the established compose deployment, preserving volumes and secrets. Do not use `down -v`.
7. Verify health, login, audit chain, worker progress, backup freshness and the changed workflow. Resume only after checking the delivery state.

This manual intentionally does not provide a one-line production overwrite command. Release path, environment and data compatibility must be checked for the specific change. Current runtime flags may include settings injected beyond the base compose files; compare names and intended values without dumping secrets.

### Rollback

If the release fails, pause new work and retain logs and delivery state. Revert the application image only if it can read the current database and privacy journals. Restore data only into a new location using the recovery procedure. A database rewind may lose accepted provider receipts and cause duplicate external effects; reconcile those before resuming. Do not roll back consent suppression or deletion history.

Documentation-only changes do not require replacing the running service. The closeout documentation refresh does not change provider settings, billing, commissions or campaign execution.

## 10 Backup and recovery

An authorized administrator can call `POST /api/backup` or use the Settings backup control. The operation creates a SQLite online backup and checks integrity. The worker also backs up daily while running. Same-volume backups protect against some application mistakes, not loss of the VPS.

Privacy-aware recovery requires a signed recovery archive, the original consent signing key and a fresh separately retained checkpoint. The recovery code rejects checkpoints older than one hour, unsafe archive members, duplicate entries, checksum failures, lost journal history and an already-existing destination.

Illustrative operator recipe, to be adapted to verified paths in an isolated recovery environment:

```python
from growthpilot.platform import Platform
from growthpilot.recovery import checkpoint, restore

current = Platform('/protected/current/growthpilot.db')
# The original signing key must already be in the environment.
checkpoint(current, '/protected/fresh-checkpoint')
result = restore(
    current,
    '/protected/backups/selected.recovery.tar.gz',
    '/protected/restore-new',
    '/protected/fresh-checkpoint',
)
assert result['integrity'] == 'ok'
assert result['audit_valid'] and result['privacy_reconciled']
```

The checkpoint destination must be new. The archive path must be the actual generated recovery bundle, not a renamed raw database. Do not run this recipe against guessed paths or overwrite the active volume. Restrict output permissions and keep the restored service disconnected from live providers during validation.

### Recovery acceptance

Verify database integrity, audit validity, product inventory and critical records. Confirm deleted contacts remain erased, suppressions remain effective and private links behave correctly. Inspect queued and unknown deliveries before any worker runs with live credentials. Test authentication and the original mock acceptance path. Record the restore duration and the age of restored data to establish actual recovery objectives.

Store backups, checkpoints and signing-key recovery material independently with appropriate access control. If the latest privacy checkpoint is unavailable, do not claim a safe restoration of contact state. Follow the product-specific journal procedures for WeddingOS, Jodibana and Memoire; AgentVire’s database restore does not restore or erase their native media automatically.

## 11 Troubleshooting and maintenance handoff

| Symptom | Check and safe response |
| --- | --- |
| Localhost refuses connection | Confirm the server is running, the selected port matches and the browser can reach that host. A stale browser tab is not a running service. |
| Login asks for credentials | Use the individual username/password, not the retired API token. Check Secure-cookie settings for HTTP development. |
| Login keeps failing | Check the 15-minute throttle and password privately. Do not disable authentication or publish the bootstrap file. |
| 403 on a mutation | Check session, CSRF, origin, role and product scope. Do not solve it with a wildcard permission. |
| Approval rejected | Reload current payload, review changed content/evidence and approve its current hash before expiry. |
| Kimi timeout | Check endpoint reachability, bridge and exact installed model. Preserve the previous draft and use manual review. |
| Delivery unknown | Reconcile the provider’s receipt or message history. Never blind-retry. |
| No paid conversions | Check real ingestion and event definitions. A prepared campaign or mock receipt does not create customers. |
| Database locked | Look for nested transaction contexts, long work inside locks and competing processes. |
| Missing deletion evidence | Check product journal and provider capability separately. Local success is not provider deletion. |
| Restore rejected | Check archive integrity, original signing key and a complete fresh privacy checkpoint; do not bypass validation. |

### Routine operations

Daily, inspect failed or unknown deliveries, model availability, worker progress and backup freshness. Weekly, verify the audit chain, review access scopes, compare actual event counts with source systems and inspect overdue follow-ups. After a release or retention change, perform an isolated recovery drill and review the applicable product handoff.

The application does not provide a complete external monitoring service. Assign an operator to these checks or implement monitored jobs with explicit alert ownership. Avoid alerts that merely repeat an unchanged state; notify on failure, completion or a decision required.

### Remaining engineering boundaries

Full social connectors, CRM synchronization, continuous accounting feeds, off-host audit anchoring, independent disaster recovery, stronger identity and scale migration remain separate work. Product grading and native media/provider-history tasks remain with their products. Preserve the original AgentVire release boundary instead of reopening all portfolio engineering whenever a marketing dependency is missing.

The implementation modules and tests are the final authority for exact payload schemas. When behavior changes, update this manual, API documentation and user instructions in the same release. Keep private accounting inputs, provider secrets and raw customer records outside the repository.


## Original PRD integration release 0.5.0

See [integration contracts, operating workflow and release boundary](prd-integrations-0.5.0.md) for the nine-provider desk, consent-preserving CRM exchange, approved social/calendar handoffs, payment evidence and test coverage. Product-specific development remains on separate backlogs.
