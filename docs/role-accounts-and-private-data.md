# Company role accounts and private data

Release date: 3 November 2026. Role accounts are human logins; AI worker permissions remain separate.

The founder can create named accounts in Accounts and integrations, select one company, one executive role and specific units. The ten initial placeholders are atmakosh.ceo, atmakosh.cfo, atmakosh.cmo, atmakosh.cto, atmakosh.coo and the equivalent vireoka usernames. Their generated passwords are discarded. The founder must set a temporary password privately in Manage role logins before handing over access. Each person must change it at first sign-in. Prefer named accounts when more than one person fills a role.

| Role | Available information |
| --- | --- |
| CEO | Assigned unit workflows, finance evidence and relationship opportunities |
| CFO | Financial evidence, relevant workflow steps and CFO AI results |
| CMO | Sales and campaign workflows, customer, design-partner and champion opportunities and CMO results |
| CTO | Engineering and technical workflow steps and CTO results |
| COO | Onboarding, service, fulfillment and operations steps and COO results |

Role accounts do not receive the portfolio state payload, integration settings, account directory, audit exports, pricing engine or execution dashboard. The server rejects those endpoints. Business responses exclude other-role notes and history; writes return metadata only. CEO oversight includes all assigned unit cases. Founder approval, account grants and AI-worker controls remain founder-only. Password reset or disabling an account revokes all its sessions. Unit-role revocation applies on the next request.

Private data routes, guessed document locations, configuration and backups require authentication. The server does not expose a filesystem directory or a public document download service. Responses use no-store, noindex and frame restrictions; HTTPS deployments send HSTS. Authenticated data reads are bounded to 120 per account per minute within the service process. This is a scraping deterrent, not a defense against volumetric denial of service. robots.txt is advisory; authentication and authorization provide protection. An authorized user can still copy visible information. MFA and external penetration testing remain separate security improvements, not claimed as implemented.

The database migration adds must_change with a default of zero. Existing users continue to sign in. New role accounts require a password change. Backups and the previous image are retained for deployment recovery. Old images can read existing accounts; do not create new users with an old image against the expanded users table without compatibility review.

The blocked headline reports launch tasks, not failed test cases. On this release, 140 effective blockers consisted of 28 direct readiness tasks, 51 commercial-condition holds and 61 pending tasks waiting on dependencies. Forty-five blocked tasks concerned internal-only products and require scope review. No task was marked complete by the explanatory UI change.

Validation: 308 automated tests passed in the exact VPS candidate; five role dashboards passed browser tests including initial password changes, direct-link restrictions and mobile layout. Production verification confirmed ten scoped accounts, protected anonymous paths, security headers, the founder account controls and the same 140-task breakdown. Pricing, commissions, campaigns and product services were not executed by this release.

## Remaining security work

Track MFA enrollment and recovery, an independent penetration test, and edge-level traffic protection as follow-up work. Current authenticated read budgets are process-local. Account owners remain responsible for sharing only appropriate information with authorized colleagues. Documents and source projections are not committed to the public repository.
