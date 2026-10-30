# Tenant opt-in and consent data rights — 2026-10-30

Jodibana provides optional email collection as a configurable tenant service. It defaults off. Service access and owner acceptance are separate requirements:

1. A platform billing administrator includes the feature in selected existing plans, or provides an explicit no-charge service grant, at /platform/admin/marketing/.
2. An actual active subscription must have started and must not have expired; both subscription and plan must be active. A grant does not create an invoice or change prices.
3. The tenant owner visits /console/<tenant-slug>/marketing/, supplies the operator and support contact, and explicitly accepts the current versioned notice before enabling collection. Ordinary administrators cannot accept for an owner. Acceptance records actor, timestamp, exact notice and version.
4. Each subscriber separately chooses the unchecked marketing checkbox and confirms their own email. Tenant acceptance never constitutes subscriber permission.

JodiUSA uses Atmakosh LLC and rashmi@jodiusa.com. Its owner must accept at https://jodibana.com/console/jodiusa/marketing/. Deployment does not fabricate owner acceptance. Platform plan inclusion initially remains empty. No new price, commission, charge or campaign is activated.

## Isolation and disabling

Verified tenant domains and managed tenant subdomains use signed, short-lived context bound to host, method, path and body. Account cookies and authorization are not forwarded. Tenant records and verification links have separate scopes; platform/unknown hosts and cross-tenant tokens are rejected. Other tenant brands use tenant identifiers rather than joining JodiUSA permission.

Collection requires active tenant status, current service access and current owner acceptance. Disabling or losing access stops subscriptions and confirmations. Export, deletion and unsubscribe remain available, including for suspended tenants. Dynamic tenant campaigns remain held until their own sender and release checks are satisfied. No legacy registration consent is imported.

## Subscriber export and deletion

WeddingOS, JodiUSA, Memoire and enabled tenant sites provide an export/deletion request at /marketing-updates/. A generic response prevents disclosing record existence. A new private email link, valid for 30 minutes and scoped to one site, is required. Requesting another link revokes the previous one. GET requests never delete records; deletion requires an explicit checkbox and POST.

Export contains the active email, consent status, exact notice/version, timestamps and consent events. It excludes credentials and provider identifiers. Deletion removes the active subscription email and managed contact details, redacts linked action payload/history/receipts, cancels queued deliveries and revokes private access. Dispatch rechecks current permission immediately before sending; messages already in flight cannot be recalled.

A keyed suppression marker and minimal audit remain. A signed erasure journal on the persistent data volume reapplies deletion if an older database is restored. Keep the journal and persistent consent secret when restoring; never restore only the database. A fresh subscription after deletion requires fresh explicit choice and confirmation. Existing provider/global suppressions remain.

This is marketing-consent data management, not full account deletion. Account/purchase records, provider records, historical backups and statutory retention are separate. Reviewed retention schedules, backup/provider expiry and account-deletion integration remain open launch work; no claim of complete regulatory compliance is made.

## Operations

GROWTHPILOT_TENANT_SECRET and JODIBANA_MARKETING_PROXY_SECRET must match and be stored outside source control. Preserve the existing GROWTHPILOT_CONSENT_SECRET unchanged. Rights emails use the existing transactional sender with tracking disabled. Campaign enablement remains separate. WeddingOS and Memoire already proxy the narrowly scoped marketing prefix, so their APIs, databases and web images need no replacement.

Deploy only AgentVire and Jodibana web, keeping prior images and environment/compose backups for rollback. On rollback after tenant acceptance, ensure collection cannot bypass the newly required acceptance gate. Preserve the current erasure journal even when rolling back application code; old code cannot safely resume marketing after an erasure without reconciliation.

## Validation

168 AgentVire tests passed, including fresh ownership, rotation/expiry, consent isolation, signed context tampering, erasure of queued actions, restore reconciliation and confirmed re-subscription. 43 Jodibana tests passed and cover owner permissions, real subscription timing, plan/grant revocation, cross-tenant access, disabled/suspended privacy and connection failures. Isolated real-browser tests cover WeddingOS, Memoire, JodiUSA and a second Jodibana tenant, including owner acceptance, disabling, export, deletion and token replay rejection. Postmark blackhole checks accepted private data-link messages for the three public products; zero customer messages.

Final production verification and AgentVire backlog evidence will be appended after deployment.


## Production release verified

AgentVire release 32372ce-rights (source 32372ce7a58d2e7741cdc4f9b3b203032c6d32d6) and Jodibana image agentvire-rights-jodi:20261030-r2 (source f1e1cfbd4a72f0388052df1b7309911826a5e79c) are live. SHA-256 parity checks verified every changed runtime file against its committed source.

Public HTTPS browser checks passed on WeddingOS, Memoire and JodiUSA, including mobile layout, export/deletion controls and unchecked choices where collection is enabled. Private owner/plan configuration pages require login. Invalid tokens and requests without consent are rejected. Zero production subscription records or customer messages were created by validation.

JodiUSA retains its previous service eligibility through an explicit no-charge grant. Collection remains off; no tenant-owner acceptance exists. Rashmi Gore must sign in as tenant owner and accept at https://jodibana.com/console/jodiusa/marketing/. Platform plan inclusion is configurable at https://jodibana.com/platform/admin/marketing/ and remains unassigned until an administrator chooses plans.

Jodibana deployment uses both /opt/liqmint/jodibana/app/docker-compose.yml and /opt/liqmint/jodibana/app/compose.marketing-rights.json. Preserve the override and its private .marketing-proxy.env file during subsequent deployments. AgentVire current points to the new release; shared consent secret is unchanged. Previous images, compose files and environment backups remain available.

All WeddingOS and Memoire containers, Jodibana database/Redis/media and AgentVire's Kimi bridge retained the same container identities and start times. Finance-source hash, commercial conditions and audit chain were verified. Four isolated QA containers and their dedicated network were removed after evidence capture.

AgentVire records four additional completed engineering tasks. The three broader data-rights tasks remain in progress for reviewed retention, full-account deletion and provider/backup handling. A separate pending task records genuine JodiUSA owner acceptance. Backlog totals after this release: 79 completed, 38 pending, 87 blocked, 6 in progress, 51 historic commercial items awaiting release conditions. This release does not claim the remaining portfolio backlog is complete.
