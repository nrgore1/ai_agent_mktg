# Rationale and working assumptions for internal readiness

## Decision

Treat SDIS, One-Man Hedge Fund, Quantsys, SMDP Design and Stablecoin Pipeline as
internal capabilities, as instructed by the founder. Evaluate whether they can
be operated safely and usefully in their actual environment. Do not require a
public SaaS launch from an internal research tool.

## Working assumptions and boundaries

| Topic | Working assumption | What it permits | What remains unverified |
|---|---|---|---|
| Audience | Internal operators only | Private/local workflows; no acquisition target | Wider staff access requires verified roles |
| Revenue | No external sale is in the approved current scope | Public pricing, commissions, paid checkout and campaigns are not applicable | This is not proof of zero historical revenue or reconciled books |
| Test activity | Synthetic data and restricted research tests | Run technical checks before completing legal/activity review | No live trades, investment advice, treasury movements or external publishing authorized by these tests |
| Identity | Keep the existing product identity provisional where evidence is missing | Inventory source and test safely without inventing legal ownership | Legal operator, rights and actual activity remain open |
| Costs | Existing estimates remain estimates | Collect measurements and supplier evidence now | Do not assume free compute, zero support or 75% verified margin |
| SMDP Design | Discovery of an internal design capability | Map existing documents/source without assuming another service is the product | Actual runtime or design-only acceptance scope |
| Stablecoin Pipeline | Discovery only until purpose is resolved | Inventory source and clarify the video-versus-finance contradiction | No claimed product capability or approval |
| Infrastructure | Existing local/Ubuntu and VPS infrastructure | Local tests and private operation | No Google Cloud introduced |

## Remove false dependencies, not necessary safeguards

- Cost measurement can begin independently of the full operator journey.
  Its prerequisites are the versioned strategy and measurement specification.
  A useful observation period, usage attribution, supplier rates and support time
  are still needed before completing the cost gate.
- A synthetic internal operator test needs a verified private runtime and a
  documented test specification. Legal-identity review need not prevent running
  that test. Legal identity and data protection remain separate unfinished tasks.
  A passed technical workflow does not authorize live financial activity.
- Public launch tasks are not applicable, with their original requirements
  archived. They are not counted as passed tests.
- Unknown source/runtime mappings remain discovery work. They are not quietly
  reassigned to similarly named services.

## What has been done

The initial 45 internal blockers were reviewed: 20 public requirements became
not applicable and one private-runtime gate passed. Seventy-seven selected
synthetic component checks passed across SDIS, One-Man Hedge Fund and Quantsys.

The dependency correction enables five cost-measurement tasks and the
One-Man Hedge Fund synthetic operator journey to proceed. This is a sequencing
change, not six additional passed tests. Cost collection has started for the
two running services using a short, timestamped process CPU/memory sample.
This sample excludes subprocesses and provider/support/storage costs and cannot
be extrapolated into a monthly bill or per-customer margin.

## Order of execution

1. One-Man Hedge Fund: complete a restricted saved-workflow and error-recovery
   test; retain its verified local runtime. Gather representative operating costs.
2. Quantsys: confirm the loaded runtime version; finish authenticated
   saved-workflow, resource-limit and recovery evidence without live execution.
3. SDIS: map and verify the authoritative worker runtime; exercise its restricted
   research workflow and recovery. Existing synthetic tests remain component evidence.
4. SMDP Design and Stablecoin Pipeline: resolve source/purpose first. Do not
   spend implementation time on assumed public SaaS or payments.
5. Complete product-specific ownership/data-rights, retention/recovery and
   finance evidence before any broader operating or public-release approval.

Each gate is approved only on evidence for its own acceptance criteria.
A reduced blocked count can mean a task is ready to work on, not completed.

## Final verified status

The follow-up release passed 315 AgentVire regression tests and browser checks.
Of the original 45 internal blockers: 20 are not applicable, one runtime check
passed, six sequencing dependencies were removed, and 18 remain blocked.
Of those six available tasks, two cost-collection tasks are now in progress
and four are pending execution. The portfolio blocked count is 113.
No additional test task was completed by the dependency correction.
The public-product tasks and commercial settings were preserved; anonymous
private API and document paths still return 401.
