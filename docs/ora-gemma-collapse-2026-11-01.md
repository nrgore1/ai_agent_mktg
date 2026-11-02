# Gemma 2 constant-score investigation — 2026-11-01

Final frozen isolated development run: **30/30 valid responses**, 0 timeouts. Median 6.066s, maximum 7.282s. Previous tuple-v2 run completed30/30 with0 timeouts but returned constant clarity25/structure0/evidence0. Rating ranges in this run are reported below. **Grading qualification remains failed; no grades or mapping are activated.** Both standbys are stopped and disabled.

## Investigation and implementation

The installed pinned Gemma template renders system and user roles as consecutive user turns. The earlier tuple format instructions lived in the first turn; rubric wording in the second asked for rating and span without explicitly grounding the tuple layout. The corrected provider uses a single native user turn and places explicit [rating,span] instructions immediately before the numbered transcript spans, after the original criterion wording. It retains exact original rating strings, fields, transcript content and span IDs. This is a combined format-grounding correction; it does not establish that role handling alone caused the collapse.

Ablations are retained in the machine-readable report. Combining turns alone did not resolve the low scores and had a timeout. JSON-only generation produced malformed string spans and a timeout. A flat tuple grammar produced invalid absent-rating/span pairs and was rejected. Explicit layout plus the original strict grammar distinguished the coherent control (clarity50/structure50) from the incoherent control (25/0), both within9s. Synthetic controls are engineering diagnostics, never human ground truth. No examples with expected ratings were added to the prompt.

In the completed30-case run all four traits varied. Accuracy remains insufficient.

The final schema and semantic decoder are unchanged: exact four fields, original label vocabulary, integer span bounds, absent-label/span0 coupling, duplicate/trailing-data rejection and the original backend validator. No partial output is salvaged, scores are never clamped, jittered or rescaled to create variation. Existing providers retain their old two-message framing through a default hook. The generation contract changes to gemma-single-turn-tuple-v3 so results cannot enter the older cohort.

Warmup and serving now call the same message builder and span-JSON compactor. One unlabelled operator token primes the common prefix before admission; startup took 11.406s, outside assessment serving. The fresh receipt binds the exact model/digest/contract/recipe, expires25s and refreshes every10s. Missing/stale/mismatched receipts reject before generation. Shutdown revokes readiness. Diagnostic budget12 was consumed without reset; the final candidate startup token is separately and explicitly charged to the40-call candidate budget, followed by30 development calls. Each final example was dispatched once; no retries and no holdout calls.

## Preserved deadlines and grading gates

Unchanged deadlines:18s primary bridge,19s ordinary primary,10s fallback primary,9s backup read,11s backup total,23s gateway,25s application. Gemma2 2B Q4_K_M digest cb2d06dce81356b9799c814de8dab1f2dd265084d16ea22f88e1bff70206fabd; Ollama0.12.6; CPU-only3CPU/4GiB combined memory/swap; context2048,predict128,seed42,temp0. Private QA network, read-only model store, no host ports and3GiB available-memory guard. Kimi remains4CPU/10GiB and its container/start unchanged.

|Trait|Observed development scores|Raw MAE|Bias|
|---|---|---:|---:|
|clarity|25,75|32.22|-25.00|
|structure|0,25,50,75|28.89|-18.33|
|evidence|0,25,50,75|17.78|-9.44|

Presence text-proxy scores: [25, 75]; no vocal grading qualification is claimed. These are exposed-development descriptive metrics, not heldout accuracy. Reported completion and latency include every failure, if any. The human-reference evaluator preserves the original coverage90%,MAE20,absolute bias10,over25-error fraction20%,rho0.30,variation,development-mean-constant comparison and minimum30 valid each split. No gate was relaxed. All22 fresh holdout examples remain untouched,8 independent examples still missing. No calibration is activated. The development helper initially named fit availability as holdout eligibility; that label was corrected in the report, preserving the original helper summary. A fitted mapping does not authorize evaluation against only22 holdout examples. Zero holdout calls were made.

## Isolated regression and disposition

Real fallback drill: {"returncode": 0, "stdout": "{\"method\": \"llm\", \"model\": \"gemma2:2b-instruct-q4_K_M\", \"local_backup_used\": true, \"numeric_score_available\": false, \"overall\": null, \"rejection_code\": null, \"diagnostic_scores\": {\"clarity\": 75, \"structure\": 50, \"evidence\": 0, \"presence\": 75, \"overall\": 54}, \"generation_contract\": \"gemma-single-turn-tuple-v3\", \"seconds\": 14.012}\n", "stderr": "", "primary_fault": "14-second HTTP delay in disposable primary stub; actual 10-second primary deadline", "production_or_shared_primary_stopped": false, "real_gemma2_attempt": true}

58 backend,42 gateway,6 runtime and24 frontend tests pass. Unchanged Kimi staging: 43/44 core passed, 1 failed; browser suite stopped on the first real speech upload because method was heuristic instead of llm. It did not pass7/7 and did not establish repeated-upload consistency. Numeric grading remained withheld. The core rubric request hit the unchanged18s Kimi bridge deadline (gateway19s read timeout) and returned coaching-only heuristic, so the complete regression is not green. This failure is retained; the candidate was never deployed to that live QA baseline. Six production container IDs/start times, primary identity/caps and live QA images remain unchanged. Candidate API/gateway images were tested only in disposable containers. Both standbys are stopped, readiness revoked, evaluator removed, restart policy no, default fallback disabled. No cloud fallback or production deployment. STT/TTS and commercial gates remain pending.

Sources for runtime framing and structured output: [pinned model/template](https://ollama.com/library/gemma2:2b-instruct-q4_K_M), [Ollama structured output documentation](https://github.com/ollama/ollama/blob/main/docs/capabilities/structured-outputs.mdx). Exact installed template and observed results are retained in report.json.

## AgentVire update and source

Implementation and evidence: [97deb5f](https://github.com/nrgore1/oratoplus-monorepo/commit/97deb5f). AgentVire report `ora-gemma-collapse-20261101` records corrected format grounding, varying scores in30/30 completed development requests with0 timeouts, failed grading qualification and failed Kimi core/browser regression checks. The Ora journey remains blocked; local text backup remains pending/unqualified; STT/TTS remain pending. Audit verification is valid. The transaction preserved every other task, all51 commercial tasks, products, campaigns, actions, events, prepared artifacts and the financial source. Source unchanged; commercial execution disabled.
