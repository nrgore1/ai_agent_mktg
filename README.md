# GrowthPilot / AgentVire

Approval-governed portfolio marketing operations for 17 products and 50 channels. The current implementation includes individual login, role/product scopes, a founder approval console, evidence capture and review, editable product/CRM records, recurring campaigns, experiments, UTM analytics ingestion, reports, local Kimi support and a durable guarded delivery queue.

## Integration release 0.5.0

The nine original provider interfaces now have an Integrations desk with read-only connection checks, built-in CRM and analytics, protected finance evidence, and approval-governed social/calendar handoffs. See [workflow, API and remaining account dependencies](docs/prd-integrations-0.5.0.md). External CRM and social/calendar accounts are not implicitly connected. Product engineering remains outside this release.

## Original PRD closeout

The mock-capable marketing core is documented and regression-tested; the complete long-term multi-provider vision and all portfolio launches are not declared finished. See [scope and evidence](docs/requirements.md), [design and architecture](docs/architecture.md), [programmer manual](docs/programmer-manual.md), [user guide](docs/user-guide.md) and [runbook](docs/runbook.md). The 30 October 2026 closeout passed 187 tests. Private commercial inputs remain outside Git.

## Run locally (Ubuntu WSL2)

Python 3.10+; no third-party runtime dependencies.

```bash
cd ~/projects/vireoka-growthpilot
python3 -m unittest discover -s tests -v
python3 -m growthpilot.server --host 127.0.0.1 --port 8098
```

Open http://localhost:8098. Initial credentials are written once to `data/initial-login.txt` with mode 0600. Read them privately, sign in as founder, and change the password in Accounts & integrations. Password changes invalidate existing sessions. The old dashboard API token is no longer used.

## Workflows

- Verify product positioning and readiness in Portfolio. Attach evidence to every approved claim.
- Capture public HTTPS sources in Evidence library, then review them. Fetched source text never grants agent permissions.
- Generate a campaign package, then use local Kimi to revise it from verified evidence. Every AI revision invalidates prior approval.
- Review exact content, account, destination, recipient, evidence and payload hash. Approve one action or a bounded list of explicit hashes.
- Mock execution remains the default. Live adapters are disabled by default and require separately configured accounts and reviewed actions.
- Manage customers, institutional prospects, investors, partners and champions in Pipelines. Track opt-in, owners, follow-ups and referrals.
- Create product-scoped analytics keys. POST real product events to `/api/ingest` with an idempotency key. Reports exclude simulated events.
- Use recurring schedules for internal draft preparation and experiments for hypotheses, success metrics and budget decisions.

## Deployment and integration guides

- [VPS access and operations](docs/staging-deployment.md)
- [Local Kimi connection](docs/local-kimi.md)
- [Publishing accounts](docs/publishing-accounts.md)
- [Backlog status and remaining dependencies](docs/backlog-status.md)
- [API v2 and operations](docs/api-v2.md)
- [90-day strategy templates](docs/campaigns.md)
- [17-product and 50-channel registry](growthpilot/registry.json)

## Operational boundaries

This release does not claim that every backlog item is finished. Product prices and readiness need founder verification; channel rules need current review; publishing/email credentials need owner configuration; PostgreSQL/Redis scale migration, full social connectors, payment-system integration, off-host audit anchoring and production campaign email remain outstanding. See the status ledger.

Only zero-cost provider actions are supported. Spending and financial commitments are blocked. GitHub issue publishing and exact-test-recipient SMTP are implemented adapters, but remain disabled until configured and sandbox-tested. Unknown network outcomes are quarantined rather than retried automatically. SQLite WAL and serialized transactions support a single-host deployment; product-scoped roles are enforced at the HTTP boundary.

## Verification

The automated suite covers governance, session authentication, CSRF, permissions, HTTP workflows, evidence, queue effects/failures, schedules, analytic replay protection, backup restoration and audit tamper detection. The dashboard is also checked in a browser. CI runs the suite on Ubuntu.

## Launch Desk

[Launch & Learn operating guide](docs/launch-learn-operations.md): all-product campaign packages, activation journeys, demos, feedback and measured manager reviews. Postmark sender routing and exact-action approval are enforced.


## Product strategy and economics OS (0.4)

Open `/?view=strategyos` as a founder/admin. The module contains 17 founder-review strategy dossiers, a versioned internal U.S.-scope policy, financial input reconciliation, a cost-allocation challenge, and reprice/redesign/commission/withdrawal scenario comparisons. It has no commercial execution connector.

`GET /api/strategy` returns the private overview. `POST /api/strategy/run` accepts an optional `product_id` and allowlisted `inputs`. `POST /api/strategy/financials` records explicit completed-period USD aggregates with a source digest, allocation basis and reconciliation attestation. All endpoints require founder/admin access; writes require CSRF. Financial revisions and analysis runs are audited. Runs include the exact economics-engine source digest as well as policy, strategy and input/source provenance. Normalized input validation deliberately rejects missing cost amounts rather than substituting zero.

Production aggregates belong in the protected data-volume file `economics-source.json`, which is excluded from Git. The checked-in scripts collect only read-only aggregates with statement timeouts; execute through the authorized server account, never expose credentials or export raw customers. OraToPlus uses its separate production Django connection; record that source separately. A snapshot is not a continuous live feed.

The internal CM2 target is a draft business policy, not U.S. law. Regulatory margin, deadlines and capital remain not evaluable without an applicable sourced rule and reviewed activity/entity/state scope. Actual margin requires reconciled finance inputs. Catalog prices, trials, free users and operational payment events are not recognized revenue. Default model cohorts, costs, elasticities, partner attrition and cash timing are illustrative. Do not sum alternative module scenarios into portfolio revenue.

Partner commissions in the model apply only to partner-attributed sales. The commission-cut scenario reduces partner-sourced volume and recalculates the surviving partner share. Shared delivery cost remains committed in withdrawal. Planning cash is a simplified setup/receivables/reserve/burn-buffer proxy, never a regulatory capital assessment. Paid pricing, coverage, payout and withdrawal changes remain separately approved business actions.


### Actual financial reconciliation

`scripts/collect_actual_finance.py` runs on the authorized VPS and uses GET-only Stripe requests and read-only SQL. Secret values and transaction references stay in process on the VPS; only aggregates are persisted. It collects a completed 30-day America/New_York window, paginates completely or reports failure, deduplicates shared Stripe account identity across configured products, separates charge/fee/refund/payout categories and matches local references without exporting them. Processor movements are not recognized revenue or confirmed bank receipts. Test keys are excluded. Missing/invalid credentials and empty expense tables remain explicit gaps.

Attach its aggregate JSON as `actual_finance` in the protected economics source snapshot. Founder/admin `POST /api/strategy/run` with `{"mode":"actual_only"}` records a provenance-linked actual-only assessment for every product. It never calls scenario defaults or invents demand, commission response, or capital forecasts. Complete attested finance closes can supply historical CM2; incomplete products remain unavailable. Pricing and commission execution remains disabled. No recurring collection is implied.
