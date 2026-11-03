# Jodibana payment-method updates and monthly renewal

3 November 2026, America/New_York. **Hosted test-card replacement and subsequent monthly renewal pass within the scope below.** No product deployment or live payment configuration was changed. Product work remains on Jodibana's separate backlog.

## Verified behavior

Jodibana's restricted portal service opened the hosted Stripe form for a synthetic customer. The form saved a Mastercard test card ending 4444. Read-only provider inspection confirmed the correct customer binding, new customer default and removal of the old subscription-specific Visa override. Price, period and access were unchanged; saving the card created no extra invoice.

The test clock advanced to the next month. Stripe charged the replacement card for the unchanged $49 monthly test plan. A genuine signed HTTPS callback created exactly one separate local renewal invoice, recorded its payment link and preserved access. No invoice was manually marked paid and no signature was fabricated. A separate API-configured fixture independently verified default-method precedence and renewal reconciliation; it is not substituted for hosted evidence.

| Verification | Result | Scope |
|---|---:|---|
| Baseline PostgreSQL regressions | 518 passed | Known test image; no provider credentials or production data |
| Current billing-source regressions | 522 passed | Current services.py in known test runtime; version caveat below |
| Actual hosted browser | 4 passed | Test mode, active subscription, hosted fields, saved replacement |
| Hosted update provider state | 6 passed | Customer/default, cleared override, unchanged terms/access, no extra charge |
| Hosted natural renewal | 8 passed | Replacement charged, invoice/payment link, access, uniqueness, signed event |
| Separate API setup and renewal | 6 + 8 passed | Independent synthetic fixture |
| Cleanup/refund reconciliation | 6 passed | Cancellation, four full refunds, exact local ledger |

These counts describe overlapping suites and separate assertions, not unique requirements. Do not add the 518- and 522-test suites together.

## Findings and recovery

The first setup fixture's payment preceded callback-route readiness. It was canceled/refunded and replaced after route verification; the fresh initial payment activated the app through genuine signed delivery.

Two headless attempts timed out saving the card. A diagnostic inspection found a human-verification frame. The visible-browser run completed; the owner subsequently reported no visible challenge. Automation did not solve or bypass a CAPTCHA. The test uses a visible browser for this hosted flow and checks canonical saved state and the next charge. No application billing defect was found, so no product-code deployment was necessary.

Stripe gives a subscription-specific payment method precedence over the customer's default. The actual portal update cleared that override, and the next charge verified the effective result. [Stripe portal guidance](https://docs.stripe.com/customer-management/integrate-customer-portal), [subscription default-method reference](https://docs.stripe.com/api/subscriptions/update).

## Version limits

Provider tests and the 518-test baseline used image sha256:c5c0723bfea7728d5c3c22f19c897b6189007ab3f8ce89bfbb27445745fd3aed. The production image detected during verification was sha256:0c1015e2e3f0c5c2a27bc1d102098df01b5ff73224716ebd840c1d08d1e8b52e, deployed outside this work.

Its payment operations, reconciliation, billing hardening, recovery and views files matched exactly. Its services.py adds photo_moderation to optional features. The current slim image lacks pytest, so a direct suite attempt could not execute. Its changed services.py was then mounted read-only into the known isolated test runtime; all 522 checks passed. This verifies billing-source compatibility in that runtime, not the entire newer image or its photo-moderation feature. The newer deployment was left untouched.

## Owner approval and open gates

The owner explicitly approved **pricing, commissions and campaign publishing, subject to all gates passing**. This supersedes historical pending-owner-approval statements. AgentVire records the decision against the current strategy revision and commercial-plan hash. All 51 commercial tasks have incomplete prerequisites and now show **blocked by validation**, with approval attached. Zero full technical approvals or commercial task completions were granted; no campaign was sent.

Remaining gates:

1. Production Stripe credentials, signing endpoint, restricted portal, account/tax readiness and monitoring. Prior production holds were neither revalidated nor cleared; test credentials stayed isolated.
2. Full failed-payment exhaustion/grace operations, event ordering/alerts and remaining plan-change/proration scope. Existing-rate USD monthly renewal is the passed scope.
3. Actual operator/community review, identity/privacy, provider-history retention/deletion and off-site recovery.
4. Required local-AI quality, TURN and Telegram where applicable. AgentVire's limited prepared-invitation Mistral mode is a separate qualification.
5. Reconciled economics, observed usage/support costs, the minimum 75% margin, exact terms and eligible campaign accounts/recipients/claims. Owner approval does not supply missing evidence.

JodiUSA's all-feature, zero-cost grant remains unchanged.

## No Google Cloud

The owner requested no Google Cloud. No populated Google/Gemini/GCP/Vertex/bucket configuration variables were found in the inspected Jodibana, QA and AgentVire containers. The Google reference in logs is an old startup warning recommending GS_BUCKET_NAME; that variable is unset. The warning does not indicate a connection.

AgentVire remains configured for local ministral-3:3b on the VPS. No Google provider was enabled or added, and these test scripts made no Google Cloud calls. Future deployment/storage work must remain local or use an owner-approved non-Google service. This configuration check is not a browser-wide traffic audit.

## Cleanup and AgentVire

Both successful test agreements were explicitly canceled and all four $49 test payments refunded ($196), with signed local refunds checked. The superseded setup fixture's $49 was refunded separately. No live money moved. Owned prices/products and nondefault portal configurations were deactivated; provider history remains as test evidence.

The temporary webhook and exact route were removed and QA app/database/Redis stopped. AgentVire, Jodibana, JodiUSA, WeddingOS and Memoire returned HTTPS 200 afterward.

Qualification: jodibana-card-renewal-20261103. Readiness artifact: 208fe39aefb1532f97c39b4670312082. The audit chain verifies. Unrelated qualification results and product/campaign/action/delivery/lead records were preserved. Only scoped payment evidence and conditional owner-approval state were updated.

