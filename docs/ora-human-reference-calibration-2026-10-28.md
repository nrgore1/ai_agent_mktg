# OraToPlus human-reference grading evaluation — 28 October 2026

## Decision

Human calibration is **not qualified**. No fitted score mapping is active. Keep the OraToPlus launch journey in progress and the human scoring-quality gate open. Pricing, partner commissions and campaigns still require founder approval. Deployment is limited to isolated VPS staging; product production is unchanged.

## Human evidence and licence

Used Dagstuhl-15512-ArgQuality v2, with three genuine human annotators per selected written argument. Source: https://webis.de/data/dagstuhl-15512-argquality.html and version https://zenodo.org/records/3973285. Licence: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ . Authors: Henning Wachsmuth, Nona Naderi, Yufang Hou, Yonatan Bilu, Vinodkumar Prabhakaran, Tim Alberdingk Thijm, Graeme Hirst and Benno Stein. The importer extracts, selects and normalizes annotations; these are the modifications. It creates no human labels.

Pinned archive SHA-256: a77f346ba07e9abfc76de21da1adbdc400b5722acf7306b580668bf3c3aa8056. Parsed 304 unique annotated records; selected 60 texts of 25–160 words, deterministically split into 30 development and 30 held-out examples with disjoint topics and unique text hashes. Ground-truth labels were never sent to Kimi. No holdout label was used to fit the mapping.

Human Clarity, Arrangement and LocalSufficiency are proxies for transcript clarity, structure and evidence. Ratings 1–3 are normalized as (human mean - 1) * 50 solely for ordinal comparison. This is not validated percentage proficiency. There are no matched human vocal-presence labels or audio recordings, and no overall speech calibration. Synthetic duration at 145 words/minute served API compatibility only, not an observed speaking rate. Domain transfer, subjective disagreement and possible model training contamination remain limitations.

## Frozen baseline and validation

All 60 requests returned HTTP 200, but only 37 produced accepted LLM rubric responses; 23 used the explicitly unvalidated fallback. Development: 21/30 LLM, holdout: 16/30. Fallbacks do not count as model-quality successes. Model: existing VPS-local hf.co/mradermacher/Kimi-VL-A3B-Instruct-GGUF:Q2_K, no cloud fallback.

The baseline digest is sha256:b1c86b165fe2af3010ca81c11adbcac08943689a8719de190a6cfb501c41fb3b.

Predeclared gates: 30 valid development and 30 valid holdout predictions, model coverage >=90%, holdout MAE <=20, absolute bias <=10, errors >25 points <=20%, Spearman >=0.3, and improvement over a constant score fitted from development human labels. Monotonic isotonic regression was fitted to development only.

| Proxy | Held-out valid | Raw MAE | Candidate MAE | Constant baseline MAE | Candidate Spearman | Decision |
|---|---:|---:|---:|---:|---:|---|
| Clarity | 16/30 | 61.46 | 29.20 | 19.79 | -0.308 | Fail |
| Structure | 16/30 | 51.21 | 23.41 | 20.00 | 0.308 | Fail |
| Evidence | 16/30 | 31.60 | 20.83 | 20.83 | undefined | Fail |

Every proxy failed coverage, minimum counts, error/bias and baseline gates. A lower MAE after rescaling does not establish useful grading. The grounding guard was replayed against frozen outputs without another model call: 37 remained accepted. That replay is not a fresh independent benchmark or human review. The final fixed application was smoke-tested separately; its accuracy is not claimed improved by this replay.

## Objective fixes

- Whole-token filler detection prevents customer and number from being counted as um. Number words and digits are both observable quantitative mentions, without treating them as verified facts.
- The fallback no longer manufactures vocal presence or pace grades from a requested duration. Transcript feedback cannot certify pronunciation, tone, eye contact or body language. Unsupported filler/quantity claims and exact transcript echoes are rejected.
- Malformed transcript, scenario and duration inputs are rejected. Human-calibrated flags cannot be supplied by callers. Output explicitly states text-only scope, unvalidated speech calibration, and linguistic rather than vocal presence.
- The primary Next.js practice room now saves the actual server rubric score and method. Recorded/uploaded speech share this path. Removed the duplicate automatic chat grading request. Offline estimates are labelled local. This change does not modify the separate Studio scoring UI.
- Human-calibration limitations are visible beside practice and in feedback. Coaching text uses the product's readable surface/ink colours.

Grounding checks are limited deterministic safeguards. Accepted Kimi feedback can still be off-task (for example, business advice rather than speaking coaching). This remains a scoring-quality blocker; do not market these scores as human-equivalent or use them for consequential assessment.

## Staging validation

25 backend tests passed, including leakage controls, fit math, malformed inputs and grounding regressions. 17 frontend tests passed (six practice rubric and eleven proxy tests). Production frontend build/type validation passed. Portfolio core regression: 44 passed, zero failed, run 42da2efc64; the rubric call returned llm.

A fresh isolated Edge context verified synthetic signup -> practice -> real Piper speech fixture -> faster-whisper ASR -> actual local Kimi rubric -> browser history. The saved grade and method matched the response (43, llm), human-calibrated=false, and zero automatic chat requests. Mock ASR and HTTP 502 cases produced useful errors with zero rubric calls. Screenshots and private receipts are in the downloadable evidence folder. Three targeted live grading checks passed transport/observations/scope assertions; two fell back and one used LLM. These are technical checks, not accuracy qualification.

The self-hosted runtime remains bounded to four vCPU and 10 GiB memory/combined swap, read-only model mounts, unchanged 25-second application deadline and no retries. Six product production container IDs and start times remain unchanged. No commercial records, actual customer events, pricing, commissions or campaigns were changed.

## Reproduction and remaining release gates

Download the pinned archive from the version record, then run:

    python scripts/prepare_human_proxy_benchmark.py /private/dagstuhl-15512-argquality-corpus-v2.zip /private/benchmark.json
    python scripts/evaluate_rubric_calibration.py /private/benchmark.json /private/frozen-predictions.json /private/evaluation.json

Predictions use the evaluator's schema (id, text_sha256, method and numeric rubric dimensions). Keep human labels outside model inputs, preserve actual fallback methods, freeze predictions before fitting, and never tune against this holdout. Neither command makes model calls or activates a runtime mapping. Raw public text/annotations and operational receipts are kept outside Git; retain attribution/licence and transformation notes with derived distributions.

Next: qualify a stronger compatible local Kimi grader or another version within the user's local-model constraint; commission a directly relevant speech benchmark with consent, independent human rubric ratings, adjudication and audio-based presence labels; predeclare fresh topic/speaker-disjoint splits and validate actual final-code outputs. This existing holdout cannot become a tuning set while retaining its held-out claim. No successful human calibration or full launch readiness is declared.
