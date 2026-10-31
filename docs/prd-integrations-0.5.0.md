# AgentVire original PRD integration release

AgentVire 0.5.0 completes the original PRD's provider-interface scope using live read-only checks, built-in data services and approved manual handoffs. The PRD permits mocks and read-only connectors as the initial implementation. This release does not describe unconfigured external accounts as connected or treat portfolio product development as AgentVire work.

## Provider contracts

| PRD integration | Delivered mode | Remaining account or evidence dependency |
|---|---|---|
| Approved LLM | Existing local Kimi drafting plus model availability check | Local runtime and tunnel must be reachable; generation remains bounded and may fail without changing the draft |
| Email | Postmark identity and broadcast-stream read checks; existing consent-gated approval queue | Permissioned audience, exact approved message and compliant business footer; no campaign is launched by this release |
| CRM | Built-in pipelines with scoped CSV preview, import and export | External CRM OAuth adapter requires an actual chosen CRM account |
| GitHub | Official read-only repository check; existing exact-repository issue adapter | Publishing requires scoped server credentials, live flag and exact-action approval; a read check does not certify write permission |
| Website analytics | Existing product-key ingestion, idempotency and funnel/attribution reporting | Each product must emit real first-value and paid events; third-party analytics accounts are optional future connectors |
| Payment analytics | Protected, dated, read-only processor aggregate snapshot and source refresh script | Settlement, deferred revenue, costs and product attribution must reconcile before actual margins are declared |
| Social publishing | Exact reviewed packages for LinkedIn, X and existing registered channels | Founder manually publishes to the approved account and records a receipt; no social OAuth account is configured |
| Public research | Existing bounded public HTTPS capture with source review | Human review of claims and channel terms; account-only sources require manual evidence |
| Calendar and scheduling | Timezone-aware approved iCalendar export | Founder imports into the reviewed calendar; no calendar login, attendee invitation or availability check is implied |

## User workflow

1. Sign in as founder/admin and open **Integrations**. Read the mode shown on each card. **Check connection** performs read-only calls and records a sanitized result. Checks are limited to one per provider per minute; checks older than 24 hours are marked stale.
2. To import CRM data, select one product and a UTF-8 CSV with exactly these headers: `name,email,organization,pipeline,source`. Use a real provenance source. Pipeline must be customer, institutional, investor, partner or champion. Preview the exact file, then import. Maximum 500 rows and 200,000 characters. A malformed row rejects the whole import.
3. Imports create contacts with **unknown** marketing permission. They do not convert registration, research or a purchased list into consent. Existing contacts are preserved, suppressions and erasure markers prevent re-import, and repeated requests do not duplicate contacts. CSV export includes consent status; it is a private CRM export, not an audience approved for delivery.
4. Prepare a product campaign in **Launch Desk** or **Campaign calendar**. For a social draft, select that product/campaign in Integrations, enter the exact account, destination, title and full text, then create the draft. Internal-only products cannot create public social handoffs.
5. For a meeting, select **Calendar meeting file** and enter start/end with timezone offsets, for example `2026-11-10T14:00:00-05:00` and `2026-11-10T14:30:00-05:00`. Choose a calendar.google.com, outlook.office.com or outlook.live.com destination and the exact account. The review dialog shows normalized UTC times. A meeting can last at most 24 hours. Create a new draft to change its timing.
6. Review the entire draft and its evidence. Complete product-fact, channel-rule and destination checks. Product readiness must already be verified. **Approve exact action** binds the payload hash and version for 24 hours. Editing the payload invalidates approval; pause and expiry block export.
7. Export the approved package or calendar file. Export is audited and does not send anything. A calendar file has no attendees and sends no invitation. Publish/import manually using the approved account. Record actual submission evidence in Launch Desk; a founder-reported receipt remains labelled as such.
8. Create product analytics keys in **Settings** and place them in the product's server configuration. Never put these keys in public browser scripts. Send actual events to `/api/ingest` with stable event identifiers. Inspect Reports and daily/weekly recommendations before revising campaigns.

## Programmer interface

`growthpilot/integrations.py` owns the nine-provider registry, sanitized health checks, CRM exchange, payment snapshot projection and calendar serialization. `static/integrations.js` presents an admin-only screen. `Manager.transition` continues to own approval, expiry, revision and export checks; its package export now records an audit entry. No new execution bypass or database migration is introduced.

All integration endpoints require a founder/admin session; writes additionally require the current CSRF token and same-origin validation. Operator/viewer access is rejected. Existing product APIs retain their product scopes. All new calls are JSON except the browser's locally generated CSV/ICS download.

| Route | Input | Result |
|---|---|---|
| `GET /api/integrations` | None | Modes, sanitized latest checks, product list, analytics key coverage and protected aggregate finance status |
| `POST /api/integrations/check` | `connector`: llm, email or github | Healthy/unavailable result; no raw provider body or credentials persisted |
| `POST /api/integrations/crm-import` | `product_id`, `csv`, stable `request_id`, boolean `preview` | Counts only; atomic import and idempotent replay; different content with reused key rejected |
| `POST /api/integrations/crm-export` | `product_id` | `filename`, `media_type`, CSV `content`; spreadsheet formula prefixes neutralized |
| `POST /api/integrations/handoff` | `product_id`, `campaign_id`, `kind`, exact destination/account/title/content, stable `request_id`; `calendar_event` for calendar | Pending action in the existing Launch Desk; never approved implicitly |
| `POST /api/integrations/calendar-export` | `action_id` | ICS content and approved payload hash after normal approval validation |

The handoff request key deduplicates creation even when a response is lost. Calendar metadata is part of the approved payload and immutable through the ordinary revision endpoint. ICS content uses escaped text, UTC timestamps, stable event UID and UTF-8-safe 75-octet folding. No ATTENDEE or ORGANIZER property is generated.

CRM imports use a product-scoped request key and content hash. Duplicate emails in a file are rejected; contacts already in that product are skipped. A suppression in the global suppression list blocks import. Product-scoped keyed erasure markers are checked against the configured consent secret and brand registry; imports fail closed if required erasure verification cannot run. The import ledger records counts and hashes, not a second copy of contact data. No existing consent record is overwritten.

Connection checks allow only known provider routes or the trusted configured local Ollama endpoint. Responses are bounded to 1 MiB, requests time out after 12 seconds and redirects are rejected. Postmark's server response can contain API tokens: only matching server identity, stream type and account names are retained. Exceptions are replaced by a generic status; raw provider responses are never audited.

Environment settings reuse `GROWTHPILOT_OLLAMA_URL`, `GROWTHPILOT_OLLAMA_MODEL`, `GROWTHPILOT_POSTMARK_FILE`, `GROWTHPILOT_GITHUB_REPO` and `GROWTHPILOT_GITHUB_TOKEN`. A repository read can use public access; authenticated issue publishing is separately guarded. Provider check results are historical observations, not permanent availability promises.

## Finance provenance

`scripts/collect_actual_finance.py` reads already-authorized product processor references and local aggregate records on the VPS. It is an operator-run snapshot collector, not an unattended billing service. It performs no payment, subscription or payout mutation. Refresh the protected `economics-source.json` atomically using `scripts/refresh_finance_snapshot.py` on the VPS host; the script preserves other economic evidence, creates a private backup, runs the collector and writes only its aggregate output into `actual_finance`.

The integration screen separates currencies and deduplicates processor accounts. A repeated shared-account fingerprint invalidates the projection. A snapshot older than 24 hours is stale. Captured charges, refunds-to-date and processor fees have different accounting meanings and must not be summed into recognized product revenue. Missing sources are not zero costs. `margin_ready` remains false in this connector; use the existing economics reconciliation workflow for any actual margin decision.

## Acceptance and release boundary

The release tests cover login/roles/CSRF, source review, product-bound claims, campaign revision and approval, repeat-safe mock execution, CRM import/replay, consent and erasure protection, manual social receipts, timezone/calendar escaping, export approval/expiry/pause, idempotent product analytics and audit integrity. Synthetic events stay in isolated databases. Provider checks and local Kimi staging generation are additional operational checks, not substitutes for this regression suite.

Product signup, activation, grading, tenant UI, media deletion, third-party provider deletion and product-specific recovery remain in their respective product backlogs. OraToPlus numeric grades remain subject to its separate human-reference gates. No release task changes prices, commissions, campaigns, consent or claims to make a product appear launch-ready.

Live customer acquisition still needs a permissioned audience, exact verified offer, publishing identity and approved final payload. Optional external CRM, third-party analytics, automated social publication, calendar OAuth, enterprise identity, independent audit anchoring and off-host backup destination remain account-dependent extensions; they are not presented as authenticated integrations.

## Protocol references

- [Postmark server API](https://postmarkapp.com/developer/api/server-api) documents the server-level authentication and response fields used by the read-only check.
- [GitHub repository REST API](https://docs.github.com/en/rest/repos/repos#get-a-repository) is the repository-read contract.
- [iCalendar RFC 5545](https://www.rfc-editor.org/info/rfc5545/) defines the calendar-file format.
- [Stripe charges API](https://docs.stripe.com/api/charges/list) is one source for the existing read-only finance collector; accounting reconciliation remains separate.


## Release verification on 31 October 2026

All 203 regression tests passed in native Ubuntu and on the VPS candidate. Browser QA passed CRM preview/import and exact calendar review, approval and download with no JavaScript errors. Live read-only checks passed for the configured local Kimi model, all three Postmark identities and the configured GitHub repository. A local Kimi bounded invitation draft completed in 94.19 seconds without approval. Public research capture and audit verification passed. No external messages were sent. See [test evidence](evidence/prd-integrations-20261031/verification.json), [browser evidence](evidence/prd-integrations-20261031/browser-receipt.json) and [provider evidence](evidence/prd-integrations-20261031/provider-check-receipt.json).

Kimi depends on the local computer, Ollama and the private SSH tunnel staying available; cold starts can be slow. Use the existing `scripts/start-local-kimi-tunnel.ps1` to restore the tunnel. Failure preserves the pending draft. The payment snapshot was refreshed for all 17 product statuses; it remains financially unreconciled and does not authorize actual-margin claims.


## Production deployment and recovery

Version 0.5.0 is deployed at https://agentvire.com/. Application commit: `efdd803f5a5fe9ac4c6df599b2a8b4b290f5af26` on `codex/product-strategy-os`. All 37 deployed application files match the committed source. Production HTTPS, login rendering, unauthenticated API rejection, provider checks and audit verification passed. Existing protected records, runtime settings and all other running product services were preserved. The disposable QA service and its synthetic records and copied credentials were removed.

See [deployment receipt](evidence/prd-integrations-20261031/release-receipt.json), [live provider checks](evidence/prd-integrations-20261031/postdeploy-receipt.json), [public browser verification](evidence/prd-integrations-20261031/production-browser-receipt.json) and [source verification](evidence/prd-integrations-20261031/source-verification.json).

The live image is `growthpilot-staging:agentvire-0.5.0-prd`. The retained rollback image is `growthpilot-staging:8281172-privacy-v4`. Before cutover, SQLite online backup passed integrity checking and produced a recovery bundle. The existing original consent signing key and a fresh separately retained privacy checkpoint remain required for a compliant restore.

For a code-only rollback, use the protected `shared/pre-agentvire-0.5.0-prd.env` backup, the previous release's `compose.staging.yaml` and `compose.kimi.yaml`, project `growthpilot-staging`, and `up -d --no-deps --no-build --wait growthpilot`. Verify health, existing environment settings and audit integrity, then atomically repoint `current` to the previous release. Do not replace the live database or restore old contact data for a code rollback. The new tables are ordinary record kinds and require no destructive schema reversal.

The new runtime keeps the previous compose settings and adds `compose.integrations.yaml` solely to name the read-only GitHub repository. The existing Kimi bridge was retained. The local SSH tunnel was restored using the existing Windows SSH configuration; the local computer must stay available for generation.
