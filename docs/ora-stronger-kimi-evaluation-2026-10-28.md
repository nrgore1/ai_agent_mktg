# OraToPlus stronger local Kimi evaluation — 28 October 2026

## Decision

Numeric grades remain withheld. Kimi-VL-A3B-Thinking-2506 IQ4_XS completed all 60 fresh human-reference examples within the existing 18-second inference deadline, but all three content-proxy accuracy gates failed. No calibration mapping was activated. The retained staging application remains coaching-only; public grade fields are null, raw points are diagnostic, saved sessions cannot promote caller-supplied scores, and analytics withholds numeric progress.

The candidate runtime was stopped before the previous Instruct IQ4_XS model was restored. Production was unchanged. Pricing, commissions and campaigns remain pending founder approval.

## Model and serving experiment

- Candidate: `hf.co/mradermacher/Kimi-VL-A3B-Thinking-2506-GGUF:IQ4_XS`; model digest `2a527a2db4d7df99ce945b1e1914ed226217b864f5352db2c6d2dc8f7aa0e42b`.
- Ollama 0.12.6, CPU only, 4 vCPU, 10 GiB RAM/combined swap ceiling, one resident model, context 2048, read-only weights, internal Docker network, no published candidate ports or cloud fallback.
- Existing bridge/provider/application deadlines remain 18/19/25 seconds. Model preparation/preload is outside request latency and used the existing operator procedure.
- Canonical reasoning prescreen: temperature 0.8, 768-token cap. It ended at the token cap after 58.455 seconds without a completed final answer and was rejected. Intermediate reasoning JSON was never accepted as a grade. This is a failure of that bounded profile on this VPS, not an evaluation of unrestricted full-length reasoning capability.
- Selected profile: exact existing bridge framing and v5 semantic rubric, schema-constrained JSON, 128 tokens, temperature 0, seed 42, repetition penalty 1.0/window 0. Selected using known/synthetic prescreens before new human examples. The model's reasoning-trained lineage alone does not make this forced-JSON profile more accurate.
- Seven prescreen dispatches plus 60 human-reference dispatches: 67/68 candidate budget. No retries. All 60 completed and passed output validation; reference latency range 5.923–10.769 seconds. Operational acceptance is separate from grading qualification.

## Frozen human-reference protocol

The reference is the Dagstuhl-15512-ArgQuality v2 corpus, with three human ratings per argument. These are written-argument proxies for clarity, arrangement and local sufficiency; they do not validate acoustic delivery, vocal presence, full speech ability or the product's population. Presence and an overall speech grade remain unqualified. Human ordinal ratings are normalized for comparison, not treated as proficiency percentages.

All 192 texts used in earlier rounds were excluded. Sixty new examples were chosen by deterministic hashes/counts, with topic-disjoint 30 development / 30 holdout examples in this round. Original corpus topics have appeared historically; this is not a claim of globally unseen topics. No labels were sent to the model. The development-only monotonic mapping was sealed before holdout inference, and neither prompt nor model/rubric settings were tuned after holdout exposure. Offline maps remain inactive.

Unchanged gates for each trait: 30 valid development and 30 valid holdout examples; coverage at least 90%; calibrated MAE at most 20; absolute bias at most 10; fraction with errors over 25 points at most 20%; Spearman at least 0.30; strictly outperform the development-human-mean constant baseline; sufficient variation for a monotonic fit. Every trait must pass before any numeric restoration is considered, followed by operational qualification.

| Trait | Raw MAE | Calibrated MAE | Calibrated bias | Calibrated Spearman | Errors >25 | Constant MAE | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| clarity | 24.17 | 22.19 | -4.44 | undefined | 40.0% | 22.19 | Failed |
| structure | 21.11 | 21.32 | -11.82 | 0.07 | 26.7% | 21.44 | Failed |
| evidence | 23.33 | 25.41 | -18.89 | undefined | 53.3% | 25.41 | Failed |

Clarity and evidence calibrated predictions collapse to constants. Their undefined rank correlations do not pass. Structure has weak ranking and fails error/bias thresholds despite narrowly beating its constant baseline. New and prior models were evaluated on different human samples; these results do not establish a paired improvement or regression against the old model.

Frozen worker SHA256: `167115d49b9aad9f71adc64a00cc6a18be16a372620249aa549562bcccca0fd7`. Sealed development-fit SHA256: `ae337feaf6f50e204e9047c632628d69621ddf5253860fded1e158c4af7b6bb7`. The exact 60-example selection reproduces from the source archive and committed specification; raw texts, human labels and raw reasoning are not committed.

## Staging and regression verification

- Eight new protocol tests passed: completion, truncation, wrong model identity, incomplete response, explicit final-answer handling, trailing garbage and span bounds. These are synthetic engineering tests, not human ground truth.
- Frozen dataset reproduction passed without inference.
- Retained-model portfolio signup/activation regression: 44/44 passed, run `f1d5106e09`. Current local Kimi, no fault-injection fallback.
- Browser checks: 7 passed, including fresh signup, two real audio uploads through actual speech transcription and local Kimi, consistent diagnostics/coaching, saved-history contract, failed/mock transcription rejection without grading calls, and withheld analytics grades for unqualified/legacy sessions.
- Staging model dispatches: 3/4 reserved (one portfolio regression plus two browser uploads). Candidate was not promoted, so browser and portfolio checks qualify retained coaching-only staging rather than the failed candidate.
- Health checks passed; six production container IDs and start times unchanged. Existing source/image and resource limits retained. No new cloud inference or outbound email/campaign.

## Remaining launch gate and next experiment

Numeric-grading launch readiness remains blocked. A future candidate needs sufficient ranking signal and calibrated accuracy under the same gates, a newly reserved untouched benchmark, and then app-level latency/repeatability checks. More CPU/memory, a longer reasoning budget, a different quantization or fine-tuning are separate experiments; none is silently provisioned or treated as qualified here. Product-specific human-reviewed speech and presence references remain necessary before a broad speech-grading claim. The separate Studio client is not qualified by these tests.

## Reproduction and primary references

From the OraToPlus repository, run `python3 -m unittest discover -s tests -p test_kimi_candidate_protocol.py`. Rebuild the split with `python3 scripts/prepare_content_proxy_benchmark.py ARCHIVE docs/qa/fixtures/thinking-2506-candidate-selection.json PRIVATE_OUTPUT.json`. The candidate worker is an offline operator tool, imports the backend via PYTHONPATH, and targets an isolated internal candidate runtime; it does not change the application's model or qualification policy. Apply a dispatch budget before invoking it. Do not rerun the frozen holdout for tuning.

- [Moonshot Kimi-VL model documentation](https://github.com/MoonshotAI/Kimi-VL/blob/main/README.md)
- [Thinking-2506 canonical chat template](https://huggingface.co/moonshotai/Kimi-VL-A3B-Thinking-2506/blob/main/chat_template.jinja)
- [Quantized model files](https://huggingface.co/mradermacher/Kimi-VL-A3B-Thinking-2506-GGUF/tree/main)
- [Human-reference dataset documentation](https://webis.de/data/dagstuhl-15512-argquality.html), [source archive and license](https://zenodo.org/records/3973285). Authors: Henning Wachsmuth, Nona Naderi, Yufang Hou, Yonatan Bilu, Vinodkumar Prabhakaran, Tim Alberdingk Thijm, Graeme Hirst and Benno Stein; CC BY 4.0. Archive SHA256 `a77f346ba07e9abfc76de21da1adbdc400b5722acf7306b580668bf3c3aa8056`.
