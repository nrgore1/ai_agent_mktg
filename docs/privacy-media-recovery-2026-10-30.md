# Media, provider history, audit and recovery â€” 2026-10-30

Scope: WeddingOS, Jodibana/JodiUSA and Memoire. This release improves deletion and recovery controls; it does not certify universal erasure or legal compliance.

## Implemented

- **WeddingOS:** durable signed account-deletion evidence outside PostgreSQL; deletion clears device labels and IP addresses for all account sessions, including already-revoked sessions. Held requests stay held. Shared workspace/vendor media, financial records and the restricted hash-chained audit remain separate retained categories. No account deletion is permitted to rewrite the audit chain or destroy shared workspace files.
- **Jodibana/JodiUSA:** the account-erasure flow inventories cascading FileFields, including gallery photos, voice notes and support attachments. It deletes exact storage references, retains references used by other records, rejects unsafe paths, and stops on storage failure while retaining database records for retry. Subject-linked audit device metadata and AI prompt/output/error content are minimized. Consent and tenant acceptance rules remain unchanged.
- **Memoire:** registered-user uploads use authenticated API writes and a durable owner ledger. Browser uploads now send the sign-in token. Upload APIs no longer change bucket-wide public access policy or issue upload credentials that outlive deletion. The standard export views use the same owner ledger. Account deletion removes ledger-tracked objects and cascading FileFields, preserving shared workspace ownership rules. Failures leave deletion retryable. Subject-linked audit entries are minimized. Unsafe thumbnail URL-to-filesystem deletion was removed.
- **All three products:** separate, persistent signed journals identify account-deletion requests without retaining email. Restore checks require a fresh, signed checkpoint and reject missing/damaged evidence. A restored account matching a deletion request blocks reopening; Jodibana/Memoire also distinguish newer account identities from reused database IDs. These checks are offline operator gates, not an automatic restore or an automatic provider-deletion service.
- **AgentVire:** database backups now include signed recovery bundles containing the database, consent-erasure markers and account-event receipts. Recovery requires a separately retained fresh checkpoint and the original signing key, refuses existing destinations, verifies checksums and the audit chain, and reapplies current erasures. Managed recovery archives follow the existing 30-day AgentVire backup policy.

## Validation

- AgentVire: existing 180 tests passed; seven new recovery tests passed separately after fixing a test fixture. Missing, corrupt, stale and incorrectly signed recovery evidence is refused; an old backup cannot restore an erased synthetic contact through the tested recovery path.
- Jodibana: 52 existing consent/privacy/retention tests passed.
- Full-stack disposable staging: 13 WeddingOS, 10 Jodibana and 17 Memoire checks, plus central consent reconciliation. Includes storage/provider-connection failures, legal holds, shared ownership and unverified-email separation. Tests use synthetic accounts and no customer messages.
- Memoire browser: real signup, authenticated PhotoTray upload and account deletion passed against disposable PostgreSQL/MinIO staging.
- Actual production database backup restore drills passed with networking disabled: WeddingOS 359 tables, Jodibana 140 tables, Memoire 62 tables. No restored application was connected to customers or providers.
- Media archive recovery verified Jodibana's 34 stored files and Memoire's 169 object-store files; Memoire's local media directory was empty. These are file/archive recovery checks, not an application-wide point-in-time consistency guarantee.

## Operational recovery

1. Keep the affected application closed to traffic and outbound providers. Restore into an isolated environment, never directly over a running database.
2. Preserve the **latest** privacy journals independently of the older database/media backup. Preserve the original signing keys in the existing protected secret configuration; do not put them in Git or evidence reports.
3. For AgentVire, use `growthpilot.recovery.checkpoint(store, new_directory)` while writes are paused, then `restore(store, archive_path, empty_destination, latest_checkpoint)`. Checkpoints must be less than one hour old. Inspect the returned integrity/audit/reconciliation result before any cutover.
4. For each product, call its `privacy_journal.checkpoint(new_directory)` while account/media writes are paused. Mount that checkpoint in the isolated restored application as `PRIVACY_RECOVERY_DIR`. Run its `recovery_check.check()` with the original service/key configuration and the restored database.
5. Any `account_reconciliation_pending` result blocks reopening. Reapply the ordinary scoped deletion workflow in isolation, respecting holds and shared ownership. The checker itself does not delete records. Recheck stored media, export artifacts, credentials and outstanding provider requests. Native media reconciliation is still an operator task.
6. Do not run campaigns or notifications from restored environments. Keep rollback images/configuration available. Validate real readiness and read-only public routes after cutover.

The release backup evidence is stored on the VPS under `/home/liqmintadmin/marketing-privacy-v4-20261030/production-backup`. Database/media backups are access-restricted. New native journals use a separate persistent mount per application. Existing historical/third-party backup copies have not been mass-deleted.

## Remaining launch gates â€” explicitly open

1. **Postmark account access and scope:** owner confirmed the Data Removal API/account token is not configured. Postmark's API requires an account token and enablement and removes recipient data across the account. Do not use it for a single-product request without reviewing shared-account impact. Server tokens cannot perform this action. A fresh verified recipient identity will be needed when executing a provider request; signed journals deliberately do not preserve raw email. [Official API](https://postmarkapp.com/developer/api/data-removals-api), [enablement](https://postmarkapp.com/updates/data-removal-api).
2. **Actual provider retention:** confirm the account's configured message-history retention and vendor response; public defaults are not proof of this account's settings. No provider history is claimed deleted.
3. **Historical/unowned media:** Memoire's legacy assets, thumbnails and remaining specialized/background writers lack reliable owner attribution. Inventory and migrate these references before automated deletion. Do not guess ownership from filenames or delete arbitrary URLs. Existing bucket access policy was not changed, because that could break public/shared books; access-policy review remains open.
4. **Shared/retained records:** approve and document retention and access controls for immutable audit, financial/legal holds, shared workspace/vendor media, support history and historical denormalized identifiers. This release minimizes specific subject-linked records, not every free-text field or legacy audit event.
5. **Recovery operations:** integrate the offline account/media reconciliation gates into every restore/cutover procedure; inventory and verify off-site replicas and hosted snapshots. The successful VPS-local drills are not disaster recovery if the entire VPS is lost. No off-site destination or independent key escrow has been confirmed. Existing nightly backup coverage is not assumed complete for every store.
6. **Alternative deletion paths:** review administrative/bulk deletion and nonstandard media writers for equivalent journal and cleanup coverage. Ordinary account-erasure paths are covered by this release.

Pricing, commissions, campaigns, tenant feature acceptance and unrelated product services are outside this engineering release.
