# API v2 and operations

POST `/api/login` with username/password creates an HttpOnly SameSite=Strict cookie and returns a CSRF token. Secure cookies are enabled on the HTTPS staging instance. GET `/api/me` restores the session; every mutation except login and keyed analytics ingestion requires `X-CSRF-Token`. Logout and password changes invalidate sessions. No bearer founder token is accepted.

Founder/admin can approve, execute, pause, manage users and verify product/channel/evidence records. Operators can manage only assigned products; viewers cannot mutate. Product scopes filter portfolio and associated data; portfolio-wide reports/audit are restricted to administrators.

POST `/api/records/{kind}/{id}` edits whitelisted fields. GET `/api/state` returns console data; GET `/api/report?product_id=1` returns scoped actuals. POST `/api/research` takes product_id and public HTTPS URL. POST `/api/actions/{id}/generate` prepares a local Kimi revision from verified product evidence. POST `/api/actions/{id}/comment` adds a review note. Existing approve/reject/revise/execute endpoints remain. `/api/actions/batch` accepts up to 20 explicit action IDs and hashes and returns per-action results.

POST `/api/keys` creates a product-scoped ingestion key shown once. POST `/api/ingest` uses `Authorization: Bearer <analytics-key>` with `{idempotency_key,type,count,revenue_cents,cost_cents,utm_source,utm_medium,utm_campaign,campaign_id}`. Campaign IDs must match the key product. Repeated keys do not duplicate results. Do not send personal data in analytics events.

POST `/api/external-action` prepares a zero-cost GitHub issue or sandbox SMTP action with exact title, content, claims, sources, recipient and account. It must pass product readiness, verified channel policy and evidence checks before approval. Queued actions cannot be revised. Provider execution is rate limited to one request per minute per connector. Network failures and expired in-flight leases are marked unknown. Manual provider reconciliation is required before any new attempt; no auto resend endpoint is provided.

POST `/api/backup` creates a SQLite online backup and runs an integrity check. The worker also does this daily. GET `/api/audit/verify` validates the full hash chain. Backups live in the data volume; off-host replication must be configured separately. Protect the initial-login file, database, backups and shared environment as secrets.

## Staging compose

Use both files after enabling local Kimi:

```bash
cd ~/growthpilot-staging/current
docker compose -p growthpilot-staging --env-file ../../shared/.env -f compose.staging.yaml -f compose.kimi.yaml ps
```

Initial credentials are inside `/app/data/initial-login.txt` in `growthpilot-staging-growthpilot-1`. Retrieve privately using docker exec, then change the password. Do not paste them into chat or logs. Shared env contains the exact installed Kimi tag. Local Kimi inference depends on the Windows reverse SSH tunnel; it does not run if the computer is off.
