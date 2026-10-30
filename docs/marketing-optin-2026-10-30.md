# Explicit marketing subscriptions — 2026-10-30

WeddingOS, JodiUSA and Memoire Studio have optional, product-specific email preference pages at /marketing-updates/. Registration and access do not require subscribing. An unchecked checkbox records the exact notice/version; a separate email confirmation activates permission. Links expire after 24 hours; GET requests never change permission. Confirmation and withdrawal tokens travel in fragments, are removed from the address bar and are submitted in same-origin JSON requests. Unsubscribe is immediate and idempotent.

AgentVire stores subscription state and append-only consent events. Pending requests do not create leads. Confirmed non-synthetic subscriptions create product-scoped leads. Managed leads are revalidated at approval, queueing and dispatch, so a withdrawn permission cannot be reused by a previously prepared action. JodiUSA carries its own brand scope within catalog product 6; it cannot authorize Jodibana operator marketing. Existing provider/global suppressions are retained.

The private execution dashboard shows live confirmed, pending and withdrawn counts and downloadable evidence. Counts represent consent, not commercial launch authorization. The earlier zero-recipient audit remains historical. No legacy account, verification, service consent or reply was imported as marketing permission.

## Delivery and deployment

User-requested confirmation/preference messages use the existing Atmakosh Postmark sender, outbound transactional stream, with open/link tracking disabled. JodiUSA reply-to is rashmi@jodiusa.com. Production requires a persistent secret of at least 32 characters in GROWTHPILOT_CONSENT_SECRET and GROWTHPILOT_ENABLE_CONSENT_EMAIL=true. Do not rotate the secret casually: it identifies records and signs preference links. Back it up securely with the environment. Campaign delivery remains under its separate existing flag and release policy.

WeddingOS and Memoire proxy only the marketing URL prefix through their own web containers; JodiUSA uses an explicit method/path allowlist restricted to its two public hosts. Account cookies and authorization headers are not forwarded. There is no central dashboard exposure through these paths. Preference assets bypass WeddingOS service-worker caching. Account onboarding/password gates do not prevent access to JodiUSA preferences.

Rate limits are initially conservative: 100 requests/hour overall, 20/hour per upstream connection address, one confirmation/preference request per brand/address per 15 minutes, and three per email/day. Proxy connection grouping can make the hourly limit apply to an entire product. Review real opt-in volume before increasing it; do not trust arbitrary forwarded IP headers. Failures do not activate permission, and delivery status is visible privately.

## Validation

- 155 AgentVire tests passed, including 13 new lifecycle, concurrency, isolation and abuse tests.
- 29 JodiUSA tests passed covering proxy, registration, legal pages and tenant isolation.
- WeddingOS production build/bundle budget and 5 free-tool/signup tests passed.
- Memoire production web build passed; existing bundle-size warning remains.
- Real browser tests on isolated VPS instances passed for all three products: unchecked choice, mobile layout, invalid/cross-origin rejection, confirmation, replay rejection, withdrawal and registration link.
- Postmark blackhole recipient accepted all three confirmation messages; no customer outreach.
- Isolated synthetic confirmations created zero campaign leads.

## Remaining release conditions

Acquire real, product-specific opt-ins organically. Supply a business mailing address before promotional email. Connect exact social publishing accounts. Verify product-specific launch claims and current actual margin/commission economics. These forms do not override those conditions or send campaigns.

Continue: complete production smoke checks; monitor confirmation delivery; retest account and save-plan journeys; address WeddingOS concurrent saved-plan quota enforcement with a database-backed serialization test; integrate consent export/erasure into each product's data-rights process; define reviewed retention/expiry rules for unconfirmed requests. OraToPlus grading remains in its separate workstream.


## Deployment completed and additional launch work

All three public registration-to-preferences browser journeys now pass on their real HTTPS domains. Requests without explicit permission fail. Privacy links load. No production subscribers or customer email were created by these checks.

- AgentVire: d45bfc2-optin; source d45bfc2508e27dcff17952586ddb8ec5d77323b2.
- WeddingOS web: agentvire-optin-wedding:20261030; source 328b8025ef53ce8d95ba4bc81ef5d6217db8efcb.
- JodiUSA web: agentvire-optin-jodi:20261030-r2; source eb1d1e4a4cbc93e102bbddc0b8b093d73c43f5e7. An existing fixed privacy banner obscured footer links during production browser QA. The final build reserves its measured height and adds a registration-heading opt-in link, accessible without accepting account terms.
- Memoire web: agentvire-optin-memoire:20261030; source 611bd879e4b734040e0ee5d1a6e6840774cffcf2. Source preserved in the deployed checkout; portable patch in docs/patches/memoire-marketing-optin-20261030.patch. Older unrelated Memoire history was not pushed to its public remote.
- WeddingOS API: weddingos-api:serialized-save-20261030; source 892cf9bcca29c1c0e58542a3cdf72927289b9aa8. Reproduced the old concurrency bug: two requests accepted one remaining quota slot. Added a per-account PostgreSQL row lock before retry lookup/count/insert. Deterministic held-lock test verifies only one success, one limit response, independent-account progress and duplicate-retry single insertion. All 27 full-stack signup/activation/plan checks pass. The HTTP report's sequential-only limitation is supplemented by the separate PostgreSQL concurrency report. API readiness reports the new source revision. No quota, schema or pricing changes.

Rollback images and prior compose/environment files are retained. Opt-in deployments kept existing APIs, databases and workers unchanged; the subsequent WeddingOS save fix replaced only its API. AgentVire's financial source hash, audit chain and commercial controls were verified. No new campaign authorization was created.

AgentVire records four newly completed tasks and three explicit follow-ups for consent export/erasure/retention. Current backlog: 75 completed, 40 pending, 87 blocked, 3 in progress, 51 commercial items with release conditions unmet (historic stored status awaiting_approval; founder provisional approval remains recorded). No whole-product privacy, entitlement or commercial gate was marked complete by these technical changes.
