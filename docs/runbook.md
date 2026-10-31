# AgentVire operational runbook

Current baseline: 30 October 2026. Individual login replaces the retired dashboard token. Selected live delivery exists; do not rely on earlier mock-only runbook statements.

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
