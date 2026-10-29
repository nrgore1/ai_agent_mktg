# OraToPlus scoring consistency and grounding — 28 October 2026

## Outcome and release decision

The isolated staging scorer now repeats identical grades and feedback on the tested identical transcripts and repeated real audio. Free-form business advice and invented model quotes are removed from the active grading path. Scores retain their grading method, model, rubric version and assessment identity; analytics compares compatible cohorts only.

**Human grading accuracy is still not qualified.** The fresh human-reference sanity check fails the combined acceptance criteria. Do not declare the product fully launch-ready, activate a fitted human-calibration mapping, or market the points as human-equivalent proficiency. Pricing, partner commissions and campaigns remain pending founder approval. Product production was not deployed.

## Diagnosis and implementation

The previous application requested temperature 0.2, and the private bridge did not carry a fixed seed through to Ollama. The model generated unconstrained percentage grades and free coaching, which could become advice about the transcript's business topic. The low-precision Q2 candidate also invented purported supporting quotations. These observations do not establish a single isolated cause for every earlier score difference; ASR/model variance in those earlier tests had not been separated.

Staging now uses the higher-precision local Kimi `hf.co/mradermacher/Kimi-VL-A3B-Instruct-GGUF:IQ4_XS`, manifest digest `6381f668376aec5538e9267263ce81f48a4d502bcbc06fcad54d2cbf531a24ff`. This is a precision change within the existing model family, not a claim that it is the newest Kimi family. No paid/cloud inference route was enabled. The downloaded candidate runtime was stopped before promotion so two large models did not compete for memory.

The shared staging runtime remains CPU-only: four vCPU, 10 GiB memory and combined memory/swap ceiling, context 2048, read-only model storage, one loaded model and one admitted generation. The output cap is 128 tokens. Bridge/provider/application deadlines remain 18/19/25 seconds, with no waiting queue or automatic retry. Operator preload remains outside application requests. Because staging clients share this runtime, their configured model identities were aligned; the 44-check portfolio regression passed after promotion. No LiqMint application source was changed.

The versioned `transcript-v3-grounded` contract uses greedy decoding, seed42, repetition penalty1.0 and repeat window0. Disabling repetition penalties prevents intentionally repeated grade tokens from being discouraged; we have not claimed a controlled causal attribution from that setting alone. The bridge validates and forwards these bounded options without relaxing CPU, context or token caps.

Kimi selects an ordinal level0–3 and a numbered supporting transcript span for clarity, structure, evidence and linguistic presence. A grammar ties absent level0 to span0 and positive levels to positive span IDs. The server validates bounds and observability conditions, then supplies excerpts from the actual transcript. The model cannot manufacture quotation text or insert its own feedback field. Positive evidence grades require observable support in the selected span; full structure requires opening/closing cues. These necessary conditions do not prove semantic correctness and can conservatively reject valid examples without explicit markers.

Coaching is deliberately generated from reviewed speaking-feedback templates and the assessed traits, with transcript excerpts. It is not unrestricted model-written advice. Template usefulness and specificity still require human review. Presence refers to language only: no pronunciation, vocal delivery, tone, gaze, posture or video assessment is inferred.

Levels map to internal rubric points0/33/67/100; these are not calibrated percentage proficiency. The existing overall weights remain clarity30%, structure25%, evidence20%, linguistic presence25%. Those weights and anchors are provisional assumptions needing human validation. Invalid/unavailable assessments use the explicitly labelled, unvalidated text heuristic. Never treat fallback success as model-quality success or compare its score with a different method.

The bounded transcript path covers at most300 words,2400 normalized characters and24 spans of at most24 words. Longer text receives a labelled fallback instead of silently truncating a transcript and pretending the full speech was model-assessed. Duration is excluded from the model's content grade prompt; caller-supplied timing remains an observation and is not an audio-verified vocal assessment. Scenario/model/version remain part of the stable assessment identity. No application response cache was added to manufacture repeatability.

## Saved history and analytics

The primary Next.js practice room saves the server grade and method plus rubric version, actual model and assessment ID. It labels points as provisional. Average, best and trend calculations compare only matching grading method, version and model; legacy/unversioned or unknown LLM provenance cannot form a comparison cohort. Incompatible records remain visible in the session log, with model variants identified. An existing chart-height defect found in visual QA was also corrected. The separate Studio scoring UI was not modified.

## Validation

| Check | Result |
|---|---|
| Active backend rubric/input/calibration controls | 36 passed |
| Frontend scoring/provenance/proxy controls | 20 passed |
| Bounded bridge controls | 11 passed |
| Local-only gateway controls | 7 passed |
| Frontend production build and type validation | Passed |
| Portfolio signup/activation HTTP regression | 44 passed,0 failed; run f7828b1d86; Ora rubric method llm |
| Uncached API consistency | 5/5 pairs identical across grades, feedback, method and assessment ID, despite whitespace and duration variants |
| Real audio repetition | Two independent uploads; identical ASR transcript hash, all grades, selected evidence, feedback and identity; score67 twice, method llm |
| Failure-path browser checks | Mock ASR and HTTP502 produce errors, with zero rubric calls |
| Saved history and analytics | Server grade/provenance retained; two matching reps average67; three synthetic incompatible entries excluded |

The uncached engineering fixtures are authored synthetic counterexamples, not human ground truth. Vague content scored18, supported content67, grade-injection content0, and a numbers-only weak example26 with evidence0. The prior off-task example consistently used the labelled fallback. Eight of ten calls were accepted LLM assessments; two were fallbacks. Every call stayed below25 seconds. The same audio fixture previously yielded43 and30 under the old rubric, but comparing those numeric values to the new67 does not demonstrate learning or better human accuracy because the grading contract changed.

Browser testing used a fresh synthetic account, real Piper-generated speech and faster-whisper transcription, followed by actual local Kimi scoring and persisted browser history. No automatic extra chat grading request occurred. The analytics fault records were injected only into the isolated browser's local storage, not customer or AgentVire business records. Screenshots were visually inspected. The live backend/provider/bridge source hashes matched the native source being committed.

## Fresh human-reference check: gate remains open

Used twelve previously unused texts from [Dagstuhl-15512-ArgQuality v2](https://zenodo.org/records/3973285), excluding all60 texts in the earlier evaluation. Three genuine human annotations per argument; CC BY4.0. Authors: Henning Wachsmuth, Nona Naderi, Yufang Hou, Yonatan Bilu, Vinodkumar Prabhakaran, Tim Alberdingk Thijm, Graeme Hirst and Benno Stein. Dataset documentation: https://webis.de/data/dagstuhl-15512-argquality.html ; licence: https://creativecommons.org/licenses/by/4.0/ . Archive SHA256: a77f346ba07e9abfc76de21da1adbdc400b5722acf7306b580668bf3c3aa8056.

Selection was deterministic SHA256 order, fixed before inference. Labels were never included in requests. Original three-point ordinal means were normalized as (mean-1)*50 solely for comparison. No fitting, rescaling, holdout tuning or mapping activation was performed. The final scorer image was frozen throughout this check. These are fresh text-disjoint proxies, not a large independent speech benchmark or proof of topic/speaker generalization.

| Proxy | Accepted model outputs | MAE on accepted outputs | Bias | Error >25 points |
|---|---:|---:|---:|---:|
| Clarity | 7/12 | 28.71 | -14.62 | 57.1% |
| Structure | 7/12 | 26.33 | +7.19 | 42.9% |
| Evidence | 7/12 | 16.62 | +6.81 | 14.3% |

Coverage was58.3%, with five fallbacks. The predeclared reference was coverage>=90%, MAE<=20, absolute bias<=10 and errors>25 points<=20%. All combined proxy gates failed; evidence's accepted-output errors alone cannot override failed coverage. Numeric errors use only seven accepted outputs and are not population-wide accuracy estimates. The twelve-example sample is too small to qualify release even if these reference thresholds had passed. It is a different sample and contract from the previous60-example evaluation, so do not claim a controlled before/after accuracy improvement from these numbers.

The source domain is written online argumentation. It has no matched OraToPlus speech recordings, vocal-presence labels or overall speech human rating. Content-marker rejection, domain mismatch, subjective annotation disagreement and possible model training exposure remain limitations. Prior human-calibration mappings remain inactive and every API response remains human_calibrated=false.

## Remaining work and rollback

Keep the human scoring-quality launch gate open. Obtain consented, directly relevant speech examples with independent human rubric scores, adjudication and actual acoustic labels where vocal presence is desired. Predeclare a fresh speaker/topic-disjoint qualification set, verify accepted-model coverage and error/ranking/consistency, and evaluate the complete final pipeline. Improve semantic grading and coaching specificity without tuning against this now-seen proxy set. Persistently weak results require a better qualified local Kimi configuration or adequate local hardware, not rebranding heuristic fallback as validated AI grading.

Reproduction uses repository unit suites, the repeated-audio end-to-end contract and `scripts/check_rubric_consistency.py --base-url http://127.0.0.1:18283 --output-dir /private/qa-checks`. The latter performs ten uncached synthetic requests, is restricted to loopback/SSH-forward endpoints, and does not qualify human accuracy. Never point these synthetic tests at product production. Raw corpus text, test receipts and operational secret files stay outside public Git.

Protected staging rollback retains the pre-change compose configuration, old read-only Q2 model store and previous images. The current IQ4 model files remain read-only from the serving runtime. Six product production container IDs and start times remain unchanged. All51 commercial approval gates stay pending; there were no campaign sends, pricing/commission changes or actual customer events added to AgentVire.

Implementation references: [Ollama generation parameters](https://docs.ollama.com/modelfile), [Moonshot's canonical template](https://huggingface.co/moonshotai/Kimi-VL-A3B-Instruct/blob/main/chat_template.jinja), and the [quantized Kimi artifact repository](https://huggingface.co/mradermacher/Kimi-VL-A3B-Instruct-GGUF). Fixed seeds improve reproducibility but the observed finite tests are not a universal determinism guarantee across runtime/model/hardware changes.
