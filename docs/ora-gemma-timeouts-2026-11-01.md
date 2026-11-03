# Gemma 2 timeout investigation — 2026-11-01

Gemma 2 completed 30/30 exposed development assessments, compared with18/30 previously. The deadlines and grading gates are unchanged. This is a latency improvement, not grading qualification. The standby is stopped and disabled; no production deployment or cloud fallback occurred.

## Investigation and change

Original-format diagnostics showed the first streamed token arriving as late as8.341s against the unchanged9s read deadline. A short completed response used66 output tokens and4.467s generation after1.805s prompt processing. A long example still had only partial output at9s. Partial streams were never salvaged or scored.

The selected transport uses exact original rating words and supporting span IDs in four two-element arrays. Strict decoding reconstructs the original label objects and invokes the unchanged semantic validator. Duplicate keys, invalid labels, absence/span mismatches, extra fields and trailing prose are rejected. Span JSON separator whitespace is compacted; all transcript strings, span IDs and criteria survive unchanged. Tuple responses generally use45 output tokens.

Static instructions precede variable transcript text. Operator startup primes the shared prefix with one unlabelled token before admission, taking12.372s in the tuple trial. This is startup work, never an assessment or a relaxed request deadline. A read-only readiness receipt binds model, digest, transport and warmup hash, expires after25s and refreshes every10s following model/memory checks. Missing/stale receipts reject before generation; shutdown revokes the receipt. The default application fallback remains disabled.

A rejected indexed-label prototype returned all-zero ratings for a coherent control and timed out on the longest development item. Its evidence remains retained. The selected tuple prototype also timed out on that longest item before the final input-JSON compaction. All30 development cases were therefore evaluated afresh under the final frozen configuration, once each with no retries. Diagnostic budget12 was fully consumed and never expanded.

## Unchanged limits and results

Model gemma2:2b-instruct-q4_K_M, digest cb2d06dce81356b9799c814de8dab1f2dd265084d16ea22f88e1bff70206fabd, Ollama0.12.6, CPU-only3CPUs/4GiB combined memory/swap, context2048, predict128, seed42 and temperature0. Private QA network, read-only model store, no host ports,3GiB available-memory guard. Kimi remains4CPUs/10GiB with unchanged container and start time.

Deadlines remain18s bridge,19s ordinary primary,10s fallback-primary,9s backup read,11s backup total,23s gateway and25s application.

Final development accepted:30/30. Latency min/median/max:4.017/5.910/7.715s. These are warm isolated development observations, not a production reliability guarantee. The full machine-readable report retains all failures and accepted-subset metrics. Changed coverage prevents treating raw accepted-subset accuracy as an improvement over the older subset.

Final clarity/structure/evidence scores were constant25/0/0. MAE was34.44/40.00/27.78 and bias-30.00/-40.00/-27.78; Spearman correlation is undefined. Ratings have inadequate variation/accuracy. No mapping is activated. All gates remain: coverage90%,MAE20,absolute bias10,over25-error fraction20%,rho0.30, variation, beating the development-mean constant, minimum30 valid per split. All22 fresh holdout examples remain untouched;8 independent examples are still missing. Numeric grades, full speech and vocal-presence qualification remain blocked.

Actual end-to-end fallback evidence:{"returncode": 0, "stdout": "{\"method\": \"llm\", \"model\": \"gemma2:2b-instruct-q4_K_M\", \"local_backup_used\": true, \"numeric_score_available\": false, \"overall\": null, \"rejection_code\": null, \"diagnostic_scores\": {\"clarity\": 25, \"structure\": 0, \"evidence\": 0, \"presence\": 25, \"overall\": 14}, \"generation_contract\": \"gemma-tuple-json-v2\", \"seconds\": 14.052}\n", "stderr": "", "primary_fault": "14-second HTTP delay in disposable primary stub; actual 10-second primary deadline", "production_or_shared_primary_stopped": false, "real_gemma2_attempt": true}

## Regression and isolation

Offline58backend,40gateway,6runtime and24frontend tests pass. Existing safe Kimi staging:44 core passed,0 failed;7 browser checks passed, including two real speech uploads, consistent coaching and withheld numeric history/analytics. Six production container IDs/start times and the primary container/caps remain unchanged. Candidate API/gateway images ran only in disposable staging. Both backup standbys are stopped, no restart policy, no live fallback enabled. STT/TTS and commercial approval gates remain pending.

## AgentVire update and source

Implementation and evidence: [a49d93c](https://github.com/nrgore1/oratoplus-monorepo/commit/a49d93c). AgentVire report `ora-gemma-timeouts-20261101` records the latency improvement and failed grading qualification. The Ora journey remains blocked; local text backup remains pending/unqualified; STT/TTS remain pending. Audit verification is valid. The transaction preserved every other task, all51 commercial tasks, products, campaigns, actions, events, prepared artifacts and the financial source. Source unchanged; commercial execution disabled.
