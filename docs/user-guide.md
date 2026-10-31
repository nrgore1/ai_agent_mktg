# AgentVire user guide

Operating edition — 30 October 2026. This supersedes the initial mock-only guide. The founder receives a separate detailed 17-product commercial playbook; private prices, cost inputs and owner-investment allocations are intentionally not committed. See [release scope](requirements.md), [architecture](architecture.md) and [programmer manual](programmer-manual.md).

## 1 Set up the operating desk

Sign in using the founder account initially supplied privately by the system operator. Change that password in Settings. The older API token is not a dashboard login credential. If a local browser shows “connection refused,” the local service or tunnel is not running; use the deployed address or ask the operator to restore the local instance.

### Confirm the product before preparing campaigns

In Portfolio, select the product and review its audience, positioning, website, landing page, pricing, readiness, goals and approved claims. Replace a vague description with one specific customer problem and one demonstrable result. Keep an unsupported field unverified rather than making it look complete. A price field in AgentVire is planning metadata; it does not edit the product’s billing system.

Use Evidence library to capture a public HTTPS source or attach a supported evidence record. Read the source and verify the particular claim it supports. A captured page is not automatically verified. For product capability, retain the successful product test or demonstration, not only a competitor’s page. For pricing comparisons, record date, billing period, limits and important differences.

In Channels, review the exact destination and rules. “Reddit” is not a sufficient destination: the community and its promotion rules matter. Likewise, a social network account, company page, directory listing and email sender are different publishing identities. Do not infer that every registry channel has a connected publishing account.

### Choose the correct workspace

Launch Desk organizes campaign approvals, trial activation, institutional demonstrations, feedback and measurement. Approvals shows exact action review. Pipelines holds customer, institutional, investor, partner and champion records. Campaign calendar schedules preparation. Product strategy and economics compares hypotheses; Strategy execution tracks tasks. Reports shows recorded actuals, while Audit trail shows actions and decisions.

Create teammates in Settings with the minimum required role and product access. Operators can prepare work for their assigned products. Founder/admin approval is needed for consequential external actions. Viewers can inspect assigned material without changing it.

### First session completion

Finish one verified product record, one reviewed channel and one draft. Do not prepare 50 submissions before proving that the landing flow works. The first success is a traceable, reviewable package; the next is a real user completing a meaningful product action.

## 2 Prepare and approve a campaign

Open Launch Desk. Use “Prepare all 17 products” only when initializing the operating packages; it is preparation, not permission to launch all products. Filter launch products to focus on the current public scope. Select Campaign approvals and open the relevant review.

Inspect the title, publishing account, exact destination, exact draft, claim evidence and call to action. Check the product facts, channel rules and destination before saving a review revision. A saved edit invalidates prior approval. If you use “Refine with local Kimi,” read the entire resulting draft again; local generation does not verify truth or approve the action.

### Exact action review

1. Confirm the customer segment and the specific offer. Remove features or prices that have not been verified in the product.
2. Open the landing link and complete its intended first action using a test account. Confirm the mobile experience and return/save flow where relevant.
3. Confirm the account, sender or recipient. Check current consent and suppression before email outreach.
4. Review claims, evidence, costs, dates and the complete message. For a manual channel, review its current submission requirements.
5. Select “Approve exact action” for the current version. Approval expires after 24 hours.
6. Execute using the enabled workflow, or download the approved submission package and submit it manually when allowed.

For Hacker News, the founder must write the final text personally and post manually. Its current guidelines disallow generated or AI-edited text and automated posting. Do not copy a generated campaign draft there. Source: https://news.ycombinator.com/newsguidelines.html

### Interpret the result correctly

Mock execution means simulation. Downloading a submission package means preparation. Recording a founder-reported URL means you have documented a manual submission. A provider-accepted email means the provider accepted the request; it does not prove inbox placement, a response or a sale.

If an action is unknown after a network failure, ask the operator to reconcile provider history before attempting another send. Use Pause when stopping further activity is necessary, recognizing that it cannot recall a message already sent. Reject an unsuitable draft rather than keeping it indefinitely in an apparently approved state.

Batch approval is limited to a visible list of explicit action versions. It is not an approval for future model-generated content or an entire contact database.

## 3 Contacts consent and outreach

Pipelines separates customers, institutions, investors, partners and champions. Record a real owner, source, qualification, stage and next follow-up. An email address found in a registration database, invoice or public website is not automatically a permissioned marketing contact under the portfolio’s policy.

For WeddingOS, Memoire and accepted Jodibana tenants, use the explicit optional marketing forms. Preserve the product, notice version, source and confirmation evidence. Keep unknown permission as unknown; do not mark an entire imported list opted in. Consent to one life-events product does not authorize promotional emails from all the others.

### Sender and contact identities

LiqMint Individual and Institutional use the configured naren@vireoka.com identity. Other portfolio outreach uses naren@atmakosh.com where the sender is configured and verified. JodiUSA’s support and invitation responsibility belongs to Rashmi Gore at rashmi@jodiusa.com. A support contact does not by itself establish a verified promotional sender for a provider.

Before email promotion, confirm the exact sender account, a genuinely eligible recipient, supported content, unsubscribe handling and a valid business postal address. The portfolio’s business mailing address has not been supplied in this workflow. Do not invent one or use a personal address without authorization. This is a remaining send prerequisite.

The FTC requires truthful headers and subject lines, advertising identification, a valid postal address and an effective opt-out for commercial email, including business-to-business messages. Opt-outs must be honored within 10 business days. AgentVire’s explicit opt-in policy is an additional operating choice, not a statement that every U.S. commercial email requires prior opt-in. Source: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business

### Withdrawal export and deletion

Direct users to the product’s marketing management or privacy links. Private access links expire after 30 minutes. Unconfirmed requests are removed after seven days; withdrawn contact details are removed after 30 days under the accepted operational defaults. Minimal suppression records prevent accidental re-import.

Account deletion, marketing deletion, media deletion and provider-history deletion have different scopes. Do not promise that deleting a local marketing record erases Postmark history. That provider deletion facility is not configured. Escalate unresolved requests with a clear record of what is complete and what remains.

For Jodibana, the tenant must first accept and configure the optional marketing feature. JodiUSA is not authorized merely because AgentVire has a brand entry or because an individual joined the community.

## 4 Measure value and run the weekly review

Agree on the first meaningful product result before sending traffic. Examples are a saved wedding plan, a completed speaking practice with useful coaching or a reviewable keepsake proof. Registration is an intermediate step. Paid conversion requires actual payment evidence, and recognized revenue requires accounting reconciliation.

Ask the product engineer to connect product-scoped event ingestion. Standard operating definitions should cover landing view, verified signup, activation, repeat use and paid conversion. Keep personal data out of aggregate events. Campaign IDs and UTM parameters identify the source; avoid counting the same event twice.

### Weekly operating sequence

1. Run the internal review from Launch Desk and inspect Reports. Check whether data is actually arriving before interpreting low counts.
2. Compare qualified leads, activation, paid conversion and recorded acquisition cost by source. Read customer feedback alongside the numbers.
3. Inspect overdue follow-ups and incomplete demonstrations. A prepared demo agenda is not a completed meeting.
4. Choose one change to test: audience, message, onboarding step, offer scope or channel. Record a hypothesis and decision rule in Experiments.
5. Prepare the revised exact action and obtain approval before external execution. Keep the old result for comparison.

The current report’s trial-to-paid ratio is an aggregate ratio, not a fully matured cohort analysis. Its cost measure includes only recorded costs. Zero advertising spend does not mean zero marketing cost: include founder time, support, tools, partner payouts and shared infrastructure in commercial review.

### Decision rules

Use early thresholds as practical prompts, not statistical proof. If 100 measured landing visits yield no activation, first verify instrumentation and the signup/save flow, then investigate message fit. Interview five qualified users before changing several parts of the offer. Stop a campaign immediately if its advertised result cannot be completed or its claims are unsupported.

For institutions, measure qualified workflow discovery, demonstration completion, agreed pilot criteria and paid continuation. For investors, measure relevant conversations and documented next steps; never fabricate traction or imply a financing commitment. For partners, measure introductions that become qualified, activated and paid customers—not just links shared.

Use “Download operating package” to retain the review material. Keep source evidence and actual decisions with the campaign. Historical tasks marked complete on the founder’s earlier instruction do not substitute for real customer or revenue evidence.


## Portfolio operating scope

| ID | Product | Current marketing treatment |
| --- | --- | --- |
| 1 | LiqMint Individual | Verify supported review workflow; no return or yield promises. |
| 2 | LiqMint Institutional | Qualified discovery and a bounded workflow demonstration. |
| 3 | OraToPlus | Coaching-only claims; numerical grades require the separate human-reference gate. |
| 4 | WeddingOS / WeddingPro | Free couple tools and a separate professional workflow proposition. |
| 5 | Memoir / Memoire Studio | Verified digital keepsake; printing needs separate fulfillment evidence. |
| 6 | Jodibana / JodiUSA | Distinct operator and member audiences; tenant feature acceptance and member consent are separate. |
| 7 | CoffeeBook | Owner-confirmed memoirbookstudio.com track; do not duplicate Memoire revenue. |
| 8 | Charam | Verify mission, operator and transaction type before fundraising or commercial claims. |
| 9 | Atmasphere LLM | Confirm distinct governance value and supported integration before a paid launch. |
| 10 | SDIS | Internal only. |
| 11 | One-Man Hedge Fund | Internal only; no public solicitation or performance claims. |
| 12 | Quantsys | Internal only. |
| 13 | SMDP Design | Internal only. |
| 14 | Stablecoin Pipeline | Internal only; resolve name/audience contradiction before positioning. |
| 15 | Vanguard GTM | Verify standalone workflow and willingness to pay before public offer. |
| 16 | Vireoka Website | Portfolio acquisition surface; attribute sales to the purchased product. |
| 17 | Atmakosh Website | Company discovery and qualified routing; no separate website subscription. |

The life-events theme connects dating/community, wedding planning and keepsakes without combining accounts or marketing permission. A customer can enter at any occasion. The five internal products remain internal until a new founder decision.

## Commercial governance

The founder's provisional commercial approval is conditional on relevant research and at least 75% operating margin. It does not replace exact-action approval, actual cost verification, claim evidence, product readiness or recipient eligibility. The internal margin target is not a U.S. regulatory margin rule. Free offers have no positive margin and need an explicit acquisition budget.

The founder edition explains all 17 product playbooks, comparable offerings, provisional prices, referral terms, scenario sensitivity and remaining assumptions. Do not treat those proposals as a billing change or overwrite existing customer agreements. Keep the detailed commercial inputs in the protected operating environment.
