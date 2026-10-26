# VPS staging deployment

The staging instance uses the configured SSH alias `weddingos-hostinger-staging`, with source releases under `/home/liqmintadmin/growthpilot-staging/releases`, a `current` symlink and a protected `shared/.env`. It is separate from the existing `/opt/growth` application.

Compose project: `growthpilot-staging`. Configuration: `compose.staging.yaml`. Host endpoint: `127.0.0.1:8098`. The persistent database uses the dedicated `growthpilot-staging_growthpilot-staging-data` Docker volume. Only mock providers are enabled.

## Access

From Windows PowerShell:

```powershell
ssh -N -L 8098:127.0.0.1:8098 weddingos-hostinger-staging
```

Open http://localhost:8098. Retrieve the token directly into your local clipboard without placing it in chat:

```powershell
ssh weddingos-hostinger-staging "sed -n 's/^GROWTHPILOT_API_TOKEN=//p' /home/liqmintadmin/growthpilot-staging/shared/.env" | Set-Clipboard
```

Paste it into the dashboard and connect. Clear your clipboard afterward. The browser keeps the token in memory only.

## Operations

```bash
cd ~/growthpilot-staging/current
docker compose --project-name growthpilot-staging --env-file ../../shared/.env -f compose.staging.yaml ps
docker compose --project-name growthpilot-staging --env-file ../../shared/.env -f compose.staging.yaml logs --tail 100
```

The service restarts automatically with Docker. Pause all in the dashboard stops work without deleting data. Stop staging with the same Compose options followed by `stop`. Never use `down -v` unless database deletion is intended.

For rollback, run `up -d --no-build` with the prior release's Compose file and its `GROWTHPILOT_RELEASE` image tag. Keep the same project name and volume. The current release has no database migration, but future migrations require a backup and compatibility check before rollback.

No public domain or TLS route is created by this staging deployment. Use the SSH tunnel. Live research, LLM generation, publishing, email and financial actions remain disabled.
