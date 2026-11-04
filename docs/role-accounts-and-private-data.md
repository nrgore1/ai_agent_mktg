# Company role accounts and private data

Original release: 3 November 2026. User administration updated 4 November 2026. Role accounts are human logins; AI worker permissions remain separate.

The President uses **User management** for named accounts, multiple scoped roles, password resets, access changes and audited deletion. Ten initial executive logins remain available; their temporary passwords are handed over privately and require a first-login change. See [User administration and SaaS roles](user-management-and-saas-rbac.md) for the current 20-role catalog and company-admin boundaries.

| Role | Available information |
| --- | --- |
| CEO | CEO workflow steps and scoped relationship opportunities |
| CFO | Financial evidence, relevant workflow steps and CFO AI results |
| CMO | Sales and campaign workflows, customer, design-partner and champion opportunities and CMO results |
| CTO | Engineering and technical workflow steps and CTO results |
| COO | Onboarding, service, fulfillment and operations steps and COO results |

Role accounts do not receive the portfolio state payload, integration settings, account directory, audit exports, pricing engine or execution dashboard. The server rejects those endpoints. Business responses exclude other-role notes and history; writes return metadata only. CEO evidence is limited to its assigned workflow role. Founder approval and executive AI-worker controls remain President-only. Delegated USER_ADMIN accounts may manage eligible staff within their assigned units. Password reset or disabling an account revokes all its sessions. Unit-role revocation applies on the next request.

Private data routes, guessed document locations, configuration and backups require authentication. The server does not expose a filesystem directory or a public document download service. Responses use no-store, noindex and frame restrictions; HTTPS deployments send HSTS. Authenticated data reads are bounded to 120 per account per minute within the service process. This is a scraping deterrent, not a defense against volumetric denial of service. robots.txt is advisory; authentication and authorization provide protection. An authorized user can still copy visible information. MFA and external penetration testing remain separate security improvements, not claimed as implemented.

The database migration adds must_change with a default of zero. Existing users continue to sign in. New role accounts require a password change. Backups and the previous image are retained for deployment recovery. Old images can read existing accounts; do not create new users with an old image against the expanded users table without compatibility review.

Historical 3 November release evidence follows; these counts are not current status. The blocked headline reports launch tasks, not failed test cases. On this release, 140 effective blockers consisted of 28 direct readiness tasks, 51 commercial-condition holds and 61 pending tasks waiting on dependencies. Forty-five blocked tasks concerned internal-only products and require scope review. No task was marked complete by the explanatory UI change.

Validation: 308 automated tests passed in the exact VPS candidate; five role dashboards passed browser tests including initial password changes, direct-link restrictions and mobile layout. Production verification confirmed ten scoped accounts, protected anonymous paths, security headers, the founder account controls and the same 140-task breakdown. Pricing, commissions, campaigns and product services were not executed by this release.

## Remaining security work

Track MFA enrollment and recovery, an independent penetration test, and edge-level traffic protection as follow-up work. Current authenticated read budgets are process-local. Account owners remain responsible for sharing only appropriate information with authorized colleagues. Documents and source projections are not committed to the public repository.
