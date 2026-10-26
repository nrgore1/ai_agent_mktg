# GrowthPilot / AgentVire

Approval-governed portfolio marketing operations for 17 products and 50 channels. Version 0.3.0 includes individual login, role/product scopes, a founder approval console, evidence capture and review, editable product/CRM records, recurring campaigns, experiments, UTM analytics ingestion, reports, local Kimi support and a durable guarded delivery queue.

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
