# OraToPlus grading accuracy and coverage — 28 October 2026

## Decision

**Structured-assessment coverage is repaired in the tested range; numeric grading accuracy is not qualified.** The final local Kimi scorer returned accepted assessments for60/60 fresh reference texts, with zero fallback or transport failure. It still failed the held-out accuracy gates. No calibration mapping is active and no full human-speech validation is claimed.

The isolated staging app now provides transcript-based coaching and practice history while withholding numeric grades and score trends. Top-level grade fields are null, numeric_score_available=false, and raw model points remain only in diagnostic_scores. This is a qualification safeguard, not a claim that hiding grades fixes model accuracy. The grading launch gate remains blocked. Product production, pricing, commissions and campaigns were not changed.

## Bugs and model behaviour addressed

All five previously rejected reference cases failed the old literal numeric-evidence rule. Valid qualitative reasons, implicit organization and purposeful language do not require digits, first/finally words or a literal audience pronoun. Those false prerequisites were removed. Strict response shape, actual transcript-span bounds, model identity, deadlines and schema checks remain. The gateway now constrains support IDs to the actual number of input spans, instead of allowing up to24 regardless of transcript length. Safe rejection codes make failures observable without leaking prompts or exception contents.

The first revised numeric-anchor round covered60/60 texts but copied one overall level across all four traits on59/60 examples. Its calibration failed, and it was not accepted as the final solution. The final transcript-v5-semantic rubric uses different rating words for each trait: clarity, arrangement, support and purposeful language. The same-level pattern occurred on1/60 in this second round. These are different samples, so this is a diagnostic behavioural comparison, not a paired accuracy improvement claim.

The actual diagnostic counterexample now distinguishes clear wording from an unsupported assertion: clarity75, evidence25. An uncached whitespace/duration repeat produced identical diagnostic points and coaching. A demand for100 on every trait did not receive the requested full marks. These are authored engineering checks, not human ground truth.

All model-selected support excerpts remain server-owned spans of the normalized transcript. Valid support choices can differ while grades remain the same. Coaching examples are selected deterministically and are explicitly separate from the model-selected evidence; that prevents arbitrary support selection from changing the coaching text. Feedback is generated from speaking-focused templates, not unrestricted business advice. This does not certify the semantic quality of every model judgement or coaching suggestion.

## Human-reference protocol and results

The source is [Dagstuhl-15512-ArgQuality v2](https://zenodo.org/records/3973285), with three human annotations per item, licensed [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). Authors: Henning Wachsmuth, Nona Naderi, Yufang Hou, Yonatan Bilu, Vinodkumar Prabhakaran, Tim Alberdingk Thijm, Graeme Hirst and Benno Stein. [Dataset documentation](https://webis.de/data/dagstuhl-15512-argquality.html) and the [original quality taxonomy](https://downloads.webis.de/publications/papers/wachsmuth_2017b.pdf) informed the distinction between clear language, ordered reasoning and sufficient support. Literal marker counts are not substitutes for those semantic judgements.

Archive SHA256: a77f346ba07e9abfc76de21da1adbdc400b5722acf7306b580668bf3c3aa8056. Human Clarity, Arrangement and LocalSufficiency are mapped only as proxies for three content traits. The comparison normalization is (mean of three ordinal ratings - 1)*50. It is not validated percentage proficiency. Presence and overall speech have no matching human reference in this source.

Two distinct60-example rounds were run in this task. Each had30 development and30 holdout examples, topic-disjoint within that round, with unique text hashes. The first excluded all72 earlier evaluated texts. The final round excluded all132 texts already evaluated before it. Neither human labels nor scores were sent to Kimi. Each development-only isotonic mapping was sealed by SHA256 before the first holdout request, with immutable scoring images during the run. No holdout tuning, automatic retry or relaxed acceptance threshold was used. The second round followed a diagnosed trait-copying failure in the first; it used a genuinely new holdout rather than recycling the failed one.

Predeclared per-trait gates:30 valid development predictions,30 valid holdout predictions, coverage>=90%, MAE<=20 points, absolute bias<=10, error>25 points on<=20% of cases, Spearman>=0.3, and lower MAE than a constant score derived from development labels. All three proxy gates must pass for the fitted overall content calibration to qualify. None passed in the final round.

Final round:60/60 accepted LLM assessments, zero fallback, zero transport failure. Holdout results (30 examples):

| Proxy | Raw MAE | Candidate MAE | Constant baseline MAE | Candidate Spearman | Decision |
|---|---:|---:|---:|---:|---|
| Clarity | 26.67 | not available | 18.85 | not available | Fail: no_monotonic_fit |
| Structure | 28.89 | 18.09 | 18.89 | -0.02 | Fail: large_errors, insufficient_rank_signal |
| Evidence | 16.94 | 16.86 | 16.67 | 0.12 | Fail: large_errors, does_not_beat_constant_baseline, insufficient_rank_signal |

Clarity was75 on every final development and holdout text. There was no raw variation from which to fit or demonstrate useful ranking. Structure's candidate MAE alone passed, but its ranking and large-error rate failed. Evidence's average error alone was small enough, but the fit did not beat the constant baseline and failed the ranking/large-error gates. Calibration rescaling cannot manufacture a missing ranking signal. All candidates remain inactive.

Qualified numeric-grade coverage is therefore0, even though structured output coverage is100% on these bounded texts. Those two measures must not be conflated. The corpus contains written online arguments, not human-reviewed OraToPlus speech recordings. The same historical topics have appeared in earlier rounds; only the new round's development/holdout topics are mutually disjoint. Domain transfer, subjective annotation variation, potential training exposure and the small held-out sample limit generalization. There are no acoustic presence, pronunciation, tone or video labels.

## Qualification enforcement and current user experience

- The API release gate binds to the model/rubric and failed-reference proof. A well-formed response, caller-supplied true flag, missing proof or unreviewed model cannot publish a qualified grade. Public clarity/structure/evidence/presence/overall fields are null. Raw points are explicitly diagnostic.
- The primary Next.js practice room keeps coaching and session provenance but saves score=null with scoreAvailable=false. It does not insert zero as a fake grade. Network or server fallback cannot restore a local heuristic grade.
- Analytics retains practice history, timing and transcript observations but withholds grade averages, best scores and trends. Legacy or unqualified points cannot be treated as learning progress. Historic data is retained rather than deleted.
- Saved-session create/list/retrieve also withhold client-declared or historical grades, retain unverified diagnostics and preserve ownership/tenant controls. There is no database migration or rewrite of historical rows. No per-session human-review queue or promised review time is implied: model qualification itself is pending.
- Raw classifier points use five ordinal bands,0/25/50/75/100, and the existing overall weights30/25/20/25. These are provisional internal assumptions, not validated proficiency. Vocal presence, tone and pronunciation are not assessed from text.

An offline replay of all60 frozen final outputs through the qualification projection verified that raw diagnostics and coaching remained unchanged while all public numeric grades were withheld. This was a transformation check with zero model calls, not another independent benchmark.

## Staging validation

| Check | Result |
|---|---|
| Backend rubric, validation, calibration and qualification tests | 46 passed |
| Local-only gateway tests | 11 passed |
| Cross-service rating-vocabulary contract tests | 2 passed |
| Frontend score/provenance/qualification/proxy tests | 24 passed |
| Frontend production build and type validation | Passed |
| Portfolio signup/activation regression | 44 passed,0 failed; run87dd4b54a6 |
| Saved-session qualification integration | Claimed grade99 withheld on create and fresh retrieval; diagnostics preserved |
| Real browser path | Signup, two real speech uploads, faster-whisper ASR, actual local Kimi coaching, saved history and unavailable-grade contract passed |
| Browser failure paths | Mock ASR and HTTP502 produced useful errors, with zero rubric calls |
| Browser analytics | Unqualified/legacy entries could not populate average or trend; practice history remained visible |

The two real audio uploads produced identical transcription hashes, raw diagnostic points and coaching. Their diagnostic overall value was59; it was not displayed or stored as a qualified grade. No automatic extra chat grading request occurred. The analytics fault records existed only in the synthetic browser's local storage. Screenshots were visually inspected.

The portfolio44-check regression exercised the new coaching-only response and authenticated save/return flow. Additional qualification serializer tests and a live save/retrieve forgery check verified the final saved-session gate. A stale encoded legacy-row locator caused one browser harness failure after scoring assertions; it was repaired and the full browser check rerun. The semantic round's operational budget was explicitly amended from70 to72 calls for that two-call rerun. Human acceptance gates and the frozen model/holdout were unchanged. The initial numeric-anchor round used81 of its96 reserved calls. No extra inference was hidden in the offline replays.

## Runtime, scope and remaining work

The existing VPS-local hf.co/mradermacher/Kimi-VL-A3B-Instruct-GGUF:IQ4_XS weights were retained. No cloud fallback, new model download or larger runtime was introduced in this task. Serving remains CPU-only, four vCPU,10GiB memory and combined memory/swap ceiling, context2048, read-only model mounts, one loaded model and one admitted generation. Structured output is capped at128 tokens; bridge/provider/application deadlines remain18/19/25 seconds with no queue or automatic retry. The supported direct content window remains<=300 words,<=2400 normalized characters and<=24 spans; longer text receives explicit fallback rather than silent truncation. No application response cache was added to claim repeatability.

Keep the OraToPlus numeric-grading launch gate blocked. The current local configuration has not demonstrated the required human alignment. A further qualified local grader and directly relevant, independently human-reviewed speech examples are needed before restoring numeric grades. That may require a different local inference configuration, stronger local capacity or a validated task-specific scoring approach; none is assumed to solve the problem without a fresh test. Do not tune against either holdout already reported here. Coaching usefulness also needs product-specific human review. The separate Studio frontend was not qualified in these primary Next.js staging checks and must be verified before any production rollout.

Both frozen selections are reproducible using scripts/prepare_content_proxy_benchmark.py and the committed selection specifications in docs/qa/fixtures/. The existing offline evaluator consumes the frozen raw prediction schema. For new collection, read diagnostic_scores as research outputs; do not coerce unavailable public grades from null to zero. scripts/check_rubric_consistency.py is restricted to loopback staging and compares unqualified diagnostics separately from grade availability. Raw corpus text, labels, receipts and operational secrets stay outside public Git; source/license attribution and transformation notes accompany the derived benchmark specifications.

Six product production container IDs and start times remain unchanged. Current staging source hashes match native source. Protected rollback images/configuration are retained. No commercial records, campaign sends, pricing, partner commissions, actual customer events or finance-source data were changed. All51 commercial approval gates remain pending founder approval. AgentVire records the coverage repair, qualification guard and blocked numeric-accuracy gate separately; the product is not declared fully launch-ready.
