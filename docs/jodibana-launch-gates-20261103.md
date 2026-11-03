# Jodibana launch-gate follow-up — 3 November 2026

## Result

The production privacy/storage repair is deployed and verified. Live collection remains disabled. JodiUSA retains all available features at no cost. No prices, commissions, campaigns, customer emails or live payments were activated. Commercial owner approval is recorded subject to all gates; it is not waiting for another blanket approval.

## Defects found and corrected

The running service had no AgentVire privacy signing settings, required-connection flag, tenant marketing proxy key or durable journal mount. Earlier privacy implementation evidence did not establish that those settings survived later replacements. The existing product-scoped keys were reused privately, the retained journal directory was mounted, and all settings were persisted in the deployment environment and service definition. No keys were invented, rotated, printed or committed.

The operational report incorrectly demanded Google-backed media storage despite the existing VPS media volume. It now verifies the actual enclosing writable mount, rejecting ephemeral/root-only storage and nested temporary mounts. It checks required privacy wiring and signed journal integrity. Restricted Stripe keys are classified correctly, including missing webhook secrets. No Google Cloud service was used.

## Measured evidence

- 564 PostgreSQL regression checks passed: the existing 540 plus 24 new storage/privacy/restricted-key checks; zero failures, errors or skips. The first run had a new test parameter collection error, which was corrected before the complete rerun.
- Eight candidate runtime checks passed: actual media and journal mounts, no critical operational errors, genuine signed account-consent export, signed tenant preferences, missing-key refusal, JodiUSA free grant and blocked live collection. Export used a reserved nonexistent synthetic address; no consent or customer message was created. These probes used live read-only integration calls, not a synthetic full customer deletion on production.
- Four native recovery assertions passed on isolated synthetic data: a restored deleted account blocks reopening; reused account identity is protected; unsafe media paths are rejected; corrupt checkpoints are rejected.
- The fresh production backup restored into a disposable PostgreSQL container with no network. All 140 public-table counts matched production. Restore took approximately 4.83 seconds at this data size; this is not full incident RTO or an off-site disaster-recovery guarantee. Temporary restored data was removed.
- Production health and signed privacy export passed. Billing/catalog/feature/settings fingerprints were unchanged. Environment, image and journal mount persistence were verified. The rollback container is stopped with automatic restart disabled. No database migration was needed.

The retained live journal is currently empty and has no current restore checkpoint. That is valid for future journal writes, but does not prove continuity of historical deletion requests. No empty checkpoint was used to certify historical recovery.

## Current remaining gates

| Gate | Current status | Required evidence/action |
|---|---|---|
| Stripe business onboarding and live signed event transport | Passed in prior run, account capability rechecked | Keep the live collection switch off until all product and commercial prerequisites pass. No real charge was made. |
| Existing-tier limits, cross-tier denial, cancellation and supported USD refunds | Prior scoped passes retained | No expansion to new tiers, proration or multi-payment refunds claimed. |
| Signup/member activation | Synthetic flow passed previously | Named community operator must review the operator demo; complete product identity and business/tax review. |
| Required feature providers | Blocked | TURN/video cross-network coverage and Telegram provider setup are absent. General local AI is still a stub/unqualified; the limited AgentVire Mistral selection mode is not proof of Jodibana generation quality. |
| Full owner plan changes/proration | Open, portal changes disabled | Test and qualify only if offered; do not advertise unimplemented scope. |
| Privacy deletion integration | Configuration repaired; scoped checks passed | Historical journal continuity, retained financial/audit data and provider retention review still need evidence. |
| Postmark history deletion | Blocked by external setup | Owner previously confirmed account token/Data Removal API are not configured. Do not substitute a server token or claim provider history erased. |
| Off-site disaster recovery | Open | Approved non-Google destination, current journal/key escrow and complete restore/cutover drill required. Local database restore is already proven. |
| Operational alert delivery | Open | Define an operator destination and verify alert receipt and recovery; a command exit code alone is insufficient. |
| Economics and price mapping | Open | Reconcile actual usage/support costs and exact offer/commission mapping to the required 75% margin. Estimates and synthetic traffic are not measured customer economics. |
| Campaign eligibility | Open | Tenant owner opt-in acceptance, confirmed recipient consent, exact publishing accounts and required sender details. Never infer consent from registration. |

Product implementation stays on the separate Jodibana backlog. AgentVire records these scoped passes and unresolved gates; no full launch or commercial task is approved by this evidence.

## Recovery and verification

Use `python manage.py ops_report --json --fail-on critical` for operational drift and `python manage.py payment_readiness --provider` for read-only payment configuration. The latter intentionally remains not ready while application collection is disabled.

Restore only into an isolated database first. Before customer traffic returns, reconcile a fresh signed privacy checkpoint and media deletion records, preserved encryption keys, tenant grants and billing state. Do not replace current deletion evidence with an older database backup. Unknown historical continuity is a blocking review item.

Rollback image/container and private database/config backups are retained on the VPS. Rolling back this repair also removes its wiring unless explicitly preserved; do not treat rollback as privacy launch approval.
