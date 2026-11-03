# OraToPlus local human-anchor experiment — 29 October 2026

The attempted grading improvement did not qualify. Local Kimi Instruct IQ4_XS with explicit criterion anchors and four disjoint human-reviewed development demonstrations completed 60/60 reference assessments within 18 seconds. All three human-reference gates failed. Numeric grades remain withheld; no fitted mapping, candidate rubric or new model was promoted into the app.

## Experiment and integrity

The existing v5 rubric returns coarse ratings with weak human alignment. This offline candidate isolates three content traits, expands low/mid/high definitions, supplies four genuine human-rated historical examples as rounded ordinal anchors, requires a level0–4 plus a real target span per trait, and removes the unqualified presence/overall fields from the experiment. Production and retained staging scoring still use transcript-v5-semantic.

Model: `hf.co/mradermacher/Kimi-VL-A3B-Instruct-GGUF:IQ4_XS`. Existing VPS only: 4 vCPU, CPU inference, 10 GiB memory/combined swap ceiling, one resident model, read-only weights, context2048, temperature0, seed42. Candidate output limit96; baseline128. Strict complete-answer, exact model identity, bounded context, span and level checks. Deadline18 seconds; no cloud inference or model retry.

The initial alternating-profile tuning check accepted2/12 baseline and3/12 candidate examples under the deadline. One operator-interrupted reserved request was conservatively retained as unsuccessful and was not retried. The successful sets differ, so their separate errors are not a fair paired accuracy comparison. An initial clear synthetic repeat timed out while its later identical prompt completed; repeated availability was not established by that prescreen. These failures remain in the spent-call ledger and are not hidden by the later successful reference run.

The fixed-profile final reference run accepted60/60. A stable prefix/cache state is one possible latency factor, not an isolated causal finding; the prescreen failures still preclude declaring operational qualification. Total candidate calls reserved87/88, including failures/interruption, tuning, synthetic tests and final reference. Public grades were never enabled.

## Human reference

Source: Dagstuhl-15512-ArgQuality v2, three human raters per argument, CC BY4.0. Clarity, Arrangement and LocalSufficiency are written-argument proxies for clarity, structure and evidence. Ratings are ordinal; normalizing their average to0–100 is a comparison scale, not proficiency percentages. No vocal presence, acoustic delivery, product-specific speech population or overall speech grade is qualified.

Only52 unused unique texts remained after excluding252 previously tested raw texts. This evaluation uses30 previously exposed development texts and30 untouched holdout texts, with disjoint topics within this round. The four in-context demonstrations and12 tuning examples are disjoint from both evaluation splits. Selection used hashes/topic counts, not holdout labels. All30 holdout texts also pass whitespace/NFKC canonical uniqueness and have zero overlap with all prior texts under that canonicalization. Many remaining examples are short arguments; results should not be extrapolated to longer speeches. Corpus topics have appeared historically, so globally unseen topics are not claimed.

The development mapping was sealed before holdout requests. No holdout labels were supplied to the model, and prompts/settings were not changed after holdout exposure. Inputs, splits and human labels reproduce from the source archive and committed specification. Optional historical word-count and mean fields are derived, checked and ignored by the canonical comparison; the frozen remote manifest was not rewritten.

Unchanged per-trait gates:30 valid development and30 valid holdout cases, coverage>=90%, calibrated MAE<=20, absolute bias<=10, errors over25 points<=20%, Spearman>=0.30, sufficient score variation and strictly better MAE than the development-mean constant baseline. All traits must pass; then app-level operational gates must pass separately.

| Trait | Raw MAE | Calibrated MAE | Calibrated bias | Calibrated Spearman | Errors >25 | Constant MAE | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| clarity | 26.67 | 23.02 | 11.15 | undefined | 40.0% | 23.67 | Failed |
| structure | 14.44 | 23.97 | 20.48 | undefined | 26.7% | 25.96 | Failed |
| evidence | 17.78 | 17.06 | 12.58 | undefined | 3.3% | 18.56 | Failed |

All calibrated holdout rankings are constant and undefined. Raw evidence ranking is0.213, below0.30. Calibrated clarity/structure exceed error and bias limits; evidence exceeds the bias limit and fails rank signal. Better MAE than a constant baseline alone cannot pass the full gate. No fitting or relabelling was performed on holdout to rescue a failed criterion. Earlier candidates used different samples; no paired improvement over those models is claimed.

Frozen worker SHA256: `3f5685342464b6f4eb32e264a73ccc76d6bfa704b436744aadd81e107d2dd2fc`. Sealed development-fit SHA256: `8b4248736aaefa09d7321b2c87a77bf4dc7f8856ec78b3830fe9b78f65e8ccc5`. Raw corpus text, labels, secrets and reasoning are not committed.

## Retained staging and founder direction

After the founder briefly requested Grok fallback, an opt-in transport prototype was tested without live cloud requests. The founder then explicitly cancelled Grok and requested Llama as backup instead. The Grok integration and disclosure were removed from active source; the prior local-only API/gateway images were restored and the temporary cloud-egress network removed. The Grok web build was never deployed and is not a release artifact. Unused prototype images/receipts may remain only as private QA evidence. No Grok credential is needed for the current direction.

Llama backup is requested work, not an implemented or qualified feature. A suitable local model must first be checked against available VPS resources and a finite inference budget, then tested for failure routing, provenance, latency and actual human-reference accuracy. Switching to Llama must never bypass numeric-grade qualification, overwrite historical model identity or load two large models simultaneously beyond the existing cap.

Restored local-only staging passed44/44 portfolio signup/activation checks, run `3ee9d76caf`, including actual local Kimi rubric method=llm. Seven browser checks passed: fresh signup; two real faster-whisper/local-Kimi audio uploads; identical diagnostics/coaching; saved history with no numeric grade; mocked/error ASR produces no grading call; analytics withholds unqualified/legacy score trends. The extra core run before the Grok cancellation is retained only in the dispatch record; the final report uses the run after restoration. Four staging dispatches reserved: two core runs plus two browser uploads.

Twelve offline protocol tests and four synthetic split/reproduction tests passed. These synthetic fixtures are engineering checks, not human ground truth. Backend/frontend Grok prototype tests were superseded by cancellation and are not presented as qualification of the retained app. The unchanged v5 qualification proof, backend scoring code and model limits match the previous local-only source. Six production container IDs and start times are unchanged. Pricing, partner commissions and campaigns remain pending founder approval; no customer outcomes or commercial approvals were fabricated.

The tracked gateway example configuration contained a credential-like value. It was replaced with an empty placeholder without copying it to new artifacts. If that historical credential is active, its owner should revoke/rotate it; removing the current value does not erase Git history.

## Reproduction and next gate

Run `python3 -m unittest discover -s tests -p test_kimi_content_candidate.py` and `python3 -m unittest discover -s tests -p test_content_proxy_reproduction.py`. Use `scripts/prepare_content_proxy_benchmark.py` with `docs/qa/fixtures/content-v6-candidate-selection.json` and the original archive. The candidate worker is an offline operator tool requiring backend PYTHONPATH and a private, budgeted evaluation input; it does not enable public grades. Do not tune on the now-exposed holdout. A new candidate needs a genuinely untouched additional source or product-specific human-reviewed examples before a new final qualification test.

[Dataset documentation](https://webis.de/data/dagstuhl-15512-argquality.html) · [Source archive and license](https://zenodo.org/records/3973285). Authors: Henning Wachsmuth, Nona Naderi, Yufang Hou, Yonatan Bilu, Vinodkumar Prabhakaran, Tim Alberdingk Thijm, Graeme Hirst and Benno Stein. Archive SHA256 `a77f346ba07e9abfc76de21da1adbdc400b5722acf7306b580668bf3c3aa8056`.
