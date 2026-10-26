# Operational runbook
Staging uses Docker Compose, persistent named volume, non-root container and localhost port binding. Put the token in a protected .env outside source control. Use TLS and identity-aware access for remote teams. Health endpoint contains no business data. CI runs safety tests for pushes and pull requests.

Emergency: Pause all; stop the process/container to stop all work. No live connector exists in this release. Rotate API token by updating environment and restarting. Restarted server retains SQLite state. Interrupted running schedules need review before being recreated; do not blindly resubmit unknown live delivery outcomes in future adapters.

Back up using SQLite online backup or stop service before copying the database and WAL. Test restore in an isolated directory with a different port. Audit hashes are tamper-evident within the database, not independently anchored. Review stale pending actions weekly and reject obsolete ones. Approved payloads expire after 24 hours. Do not expose /api/state publicly.

Deployment handoff requires SSH host, user, directory, authorized access, desired hostname and TLS path. VPB destination must be identified before publishing. No cloud deployment has been performed solely by building this repository.
