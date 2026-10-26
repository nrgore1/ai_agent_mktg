# Vireoka GrowthPilot AI

An approval-governed marketing operations application for 17 products and 50 distribution channels. Includes a responsive founder console, SQLite persistence, strategy-derived campaign generation, eight mock agent roles, exact-action approval, manual submission packages, relationship pipelines, timezone-aware scheduling, UTM attribution, actual-vs-simulation reporting and a hash-chained audit log.

**Release status:** working mock-provider application. It does not research live websites, generate content with an LLM, deliver email, publish posts, spend money, or deploy customer products. The eight agent jobs are deterministic preparation records, not eight independently intelligent agents. All product positioning and channel terms require verification. No targets are presented as actual traction.

## Run in Ubuntu WSL2

Python 3.10+ is the only runtime dependency. No pip install required.

```bash
cd ~/projects/vireoka-growthpilot
export GROWTHPILOT_API_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
# Keep this value in a password manager; enter it in the dashboard token field.
python3 -m unittest discover -s tests -v
python3 -m growthpilot.server --host 127.0.0.1 --port 8098
```

Open http://localhost:8098. Enter the API token, connect, generate a campaign, review the payload and evidence, approve its hash, then execute the mock. The receipt explicitly confirms that nothing was externally delivered. Save revisions before approval; edits revoke approval.

The worker checks scheduled draft preparation every 30 seconds while the server runs. Schedule times entered in the browser are converted to UTC. This is not a host-level timer; keep the service running for scheduled work.

## Staging

```bash
git clone https://github.com/nrgore1/ai_agent_mktg.git
cd ai_agent_mktg
cp .env.example .env
# Replace the placeholder token in .env with a strong random secret.
docker compose up -d --build
```

The container binds to localhost only. Use an SSH tunnel (`ssh -L 8098:127.0.0.1:8098 user@host`) or a TLS reverse proxy with additional identity/access controls. Do not expose the development HTTP server directly to the Internet. SSH host, DNS, TLS and hosting credentials are deployment-specific.

## Documents

- [Requirements and release scope](docs/requirements.md)
- [Architecture, schema and API](docs/architecture.md)
- [Approval policy and tool contracts](docs/governance.md)
- [User guide](docs/user-guide.md)
- [Programmer manual](docs/programmer-manual.md)
- [Operational runbook](docs/runbook.md)
- [90-day campaign templates](docs/campaigns.md)
- [Full product and channel registry](growthpilot/registry.json)

## Verification

`python3 -m unittest discover -s tests -v` covers approval bypass, rejection, revisions, expiration, concurrent idempotency, failure receipts, emergency stop, product filtering, unsupported claims, recipient tampering, spending gates, schedules, evidence requirements and separation of simulated outcomes.

## Limits before a live release

SQLite is suitable for this single-host sandbox. The shared founder token is not tenant authentication: product filtering isolates records by product for workflow purposes, not by user authorization. Add real identities, roles, recipient consent workflows, an independently secured audit sink, connector permission scopes, reliable queue leases and outbox reconciliation before enabling external delivery. Live adapters must be implemented and tested separately. PostgreSQL, Redis, FastAPI and Next.js are proposed future scale choices; this release uses a dependency-free Python HTTP server and browser JavaScript.
