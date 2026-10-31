# Retention and account-deletion integration — 2026-10-30

## Approved operational policy

The founder explicitly selected these defaults on 2026-10-30: unconfirmed marketing requests are removed after 7 days; withdrawn contact details after 30 days; private access links expire after 30 minutes; minimal keyed suppression and audit evidence remain to prevent accidental marketing reuse. These are operational choices, not statutory retention periods. Confirmed active subscriptions do not expire silently under this sweep.

AgentVire runs a daily sweep, clears expired private links and two-day abuse counters, and expires only exact application-owned database backup files in its own backups directory after 30 days. It does not delete product databases, unrelated backups, financial records, suppression markers or erasure journals. The dashboard shows the last sweep and outstanding mailbox-verification counts. Dry-run counts are recorded before production activation.

## Account integration and trust

A separate HMAC-authenticated internal endpoint accepts server-derived account email, scope, operation and stable event identifier. Keys are distinct per product service; Jodibana alone can address registered tenant scopes. Body, path, method and timestamp are signed. Public proxies do not expose the internal route. Stable receipts contain keyed subjects, not email, and are persisted separately from the active database. Old retries cannot erase a later freshly confirmed subscription, including after database restoration with the current journal.

Verified account deletion requires acknowledgment from AgentVire before local deletion. Outages leave local records intact and requests retryable; no best-effort success is reported. Export adds the matching central consent record only for verified email ownership. Deletion without an existing subscription creates a minimal suppression to prevent later imported marketing reuse. New consent still requires a new explicit choice and email confirmation.

An authenticated product login is not necessarily proof of email ownership. Jodibana accounts without email_verified_at, and Memoire's current accounts (which have no email verification field), use the private mailbox-verification journey. Account deletion requests a private marketing link if a matching record exists, without revealing whether one exists. Marketing erasure completes only after the mailbox owner follows that link and confirms deletion. Users can request another link at /marketing-updates/. Mail delivery is best effort and rate limited; a verification-required receipt is not a delivery receipt or an erasure completion.

## Product behavior

- WeddingOS: existing administrator-processed privacy requests and legal holds are retained. Verified deletion synchronizes consent, removes saved plans and old export manifests, clears password/verification/MFA/recovery/push credentials and revokes sessions. Row locks serialize processing; a completed retry is harmless. Shared workspace and financial records are not represented as erased.
- Jodibana/JodiUSA: existing operator-handled deletion is retained. Account export and the erasure service integrate with each relevant tenant scope; a pre-delete hook also covers direct account deletion. Owner acceptance and paid-plan access are unchanged. Migration 0064 adds nullable closed_at with no backfill. Only a real active-to-closed transition starts the 90-day account-retention clock. Suspension is excluded, reactivation clears the clock, and legacy inactive accounts without an evidenced closure date are retained for review. The scheduled purge uses the same account-erasure service.
- Memoire: own books, personal templates and legacy UUID-linked comments/memory rows are removed in a transaction. A sole owner of a shared organization must transfer ownership first. Other members, their books and workspace/financial records are preserved. The interface states deletion scope and mailbox-verification follow-up rather than claiming all data everywhere is gone.

## Validation

180 AgentVire tests passed, including 12 new lifecycle tests; nine execution tests additionally verified the dashboard change. 74 Jodibana privacy/retention/tenant tests passed. Isolated full-stack tests used disposable PostgreSQL databases for WeddingOS, Jodibana and Memoire, a private AgentVire database and a file email outbox. Eleven WeddingOS, six Jodibana and ten Memoire checks passed, plus cross-product verification of consent state and both unverified mailbox-confirmation journeys. The real Memoire browser signup/deletion test passed. No customer emails or production accounts were used.

## Remaining retention boundaries

The active consent ledger and account linkage are covered; full legal qualification is not claimed. Product media objects, audit/support history, financial holds, historical backups and external provider history need their own inventory and verified expiry/erasure procedures. Preserve current marketing-erasure-markers, marketing-account-receipts and the persistent consent secret on restores; database-only restoration is not sufficient. Validate disaster recovery with current journals and external backup replicas before closing the broader privacy gate.

Postmark documents a default 45-day content/metadata period, with configurable account-wide retention. The actual shared account setting has not been independently confirmed. No account-wide provider deletion or retention change is made because the sender is shared across products. Source: https://postmarkapp.com/support/article/how-long-are-inbound-and-outbound-messages-stored-in-activity and https://postmarkapp.com/support/article/how-does-the-retention-add-on-work.

FTC guidance recommends a written policy tied to necessity and secure disposal; it does not supply a universal retention duration for these products. Source: https://www.ftc.gov/business-guidance/resources/protecting-personal-information-guide-business.

Production deployment receipts and final smoke results will be appended below. Pricing, commissions, campaigns, tenant acceptance and paid-plan configuration are unchanged.
