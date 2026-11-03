# OraToPlus stronger local backup trial — 2026-11-01

**Llama3.2 3B and Gemma2 2B both fit the VPS memory envelope, but neither qualifies under the unchanged deadlines and grading gates. Both are stopped and disabled.** Numeric grades remain withheld. No cloud fallback or production deployment occurred.

The existing Kimi app remains healthy in isolated staging:44/44 core and7/7 browser checks pass. A single warm Gemma failover succeeded in16.617s with correct provenance and null numeric grades, but it does not override the failed coverage/reliability evaluation.

## Candidate selection and resources

| Candidate | Exact digest | Download bytes | Result |
|---|---|---:|---|
| [Llama3.2 3B Instruct Q4_K_M](https://ollama.com/library/llama3.2:3b-instruct-q4_K_M) |`a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`|2,019,393,189|Rejected in timing/synthetic screen |
| [Gemma2 2B Instruct Q4_K_M](https://ollama.com/library/gemma2:2b-instruct-q4_K_M) |`cb2d06dce81356b9799c814de8dab1f2dd265084d16ea22f88e1bff70206fabd`|1,708,591,777|18/30 valid development responses; unqualified |

Models ran **serially**, each capped at3 CPUs and4GiB combined memory/swap, CPU-only, context2048, one inference slot and one resident model, read-only store, internal QA network and no host port. This uses one more standby CPU than the earlier1B trial, declared before reference evaluation; Kimi remains at4 CPUs/10GiB. Model caps sum to7 of the VPS's8 CPUs; this is not a CPU-affinity reservation. No hardware/service purchase, memory-cap increase, runtime upgrade or primary container restart occurred.

The initial host available memory was16,279,678,976 bytes. Gemma's loaded runtime reported about2.0GB. Neither candidate was OOM-killed. Both controllers enforce the3GiB host-available-memory guard and stop on failure. They preload the exact tag/digest and matching three-thread, batch512, memory-mapped options outside serving. Source and worker hashes were frozen for each final evaluation phase.

## Deadlines and response contract

Unchanged: primary bridge18s; ordinary primary provider19s; fallback-primary attempt10s; backup read9s and overall11s; gateway target23s; application25s. Output budget128 tokens, context2048, temperature0 and seed42 are preserved. No partial output was salvaged.

Both candidates use the corrected response-shape guidance and model-native Ollama `/api/chat` framing. A compact, single-line JSON instruction was added during exposed synthetic performance diagnosis to reduce indentation overhead. It changes formatting, not rubric criteria, rating vocabularies, span bounds or strict absence/span pairing. The original nested schema remains intact.

Generation contracts bind provenance and assessment IDs: `llama-compact-json-v1` for3B and `gemma-compact-json-v1` for Gemma2. The previous1B profile remains `llama-json-shape-v1`; its guidance/thread budget is unchanged. Merely registering these candidates does not enable serving or qualify grades.

## Llama3B screen: rejected before full reference evaluation

With the original corrected shape guidance, all three screen requests hit the9s read deadline (9.017/9.017/9.018s). A separate stream diagnostic was stopped at9.001s: first token2.962s,75 chunks, but only a partial indented JSON object. It was never parsed into scores or counted as accepted.

After freezing compact formatting, the coherent synthetic control completed in6.778s and the incoherent control in7.916s. However, the incoherent control received `very_clear`/100 clarity and `coherent`/75 structure; that is a synthetic-control failure, not human-reference accuracy. The longest exposed development argument still timed out at9.019s. The model was stopped and no full Llama3B reference run or holdout inference was performed. All original/compact failures and distinct source hashes are retained.

Gemma2 was selected next because it is stronger than the1B candidate by model size while using a smaller package than3B Llama. Selection used compatibility, timing and synthetic controls, not holdout labels. Both standbys were never resident together.

## Gemma2 development evaluation: unqualified

The initial coherent synthetic control timed out at9.016s; the incoherent control completed in7.286s with clarity25, structure0, evidence0 and linguistic-presence25; the longest development item timed out at9.018s. That failed development result was reused in the final30-item run rather than retried.

The frozen candidate was evaluated once on all30 historically exposed development texts. **18 completed and12 timed out:60% development completion.** No accepted assessment was all-zero across all four traits. Lack of zero collapse does not establish useful accuracy.

| Written-content proxy | Valid subset | Raw scores observed | Raw development MAE | Bias | Development Spearman |
|---|---:|---|---:|---:|---:|
| Clarity |18|25,50,75|33.33|-21.30|0.134|
| Arrangement/structure |18|0,50,75|34.72|-28.24|-0.014|
| Local sufficiency/evidence |18|0,25,75|17.59|-4.63|0.214|

These are descriptive errors on the accepted subset, not heldout accuracy or a directly comparable improvement over previous trials with different completion sets. Structure's draft isotonic mapping collapsed to one constant block. The development-only fit was sealed as SHA256 `574e28f4de4197bc4b024e52c50b1be314c63037b35df8676418d1c5ae8935c5`; no mapping was activated.

All22 raw/canonically unique fresh holdout texts remain untouched. The unchanged minimum30 valid examples per split is not met: only18 valid development predictions, no holdout predictions and8 independent fresh holdout examples still missing. Existing gates also require≥90% coverage, calibrated heldout MAE≤20, absolute bias≤10, >25 errors on≤20%, Spearman≥0.30, sufficient variation and strictly beating a development-mean constant baseline. None was relaxed. Written-content proxies do not qualify vocal presence or overall speech grading.

## Actual fallback and product regression

A disposable primary stub delayed responses14s. The candidate gateway exercised its actual10s primary timeout and invoked real private Gemma2. The candidate API returned `method=llm`, exact Gemma2 tag, `local_backup_used=true`, `generation_contract=gemma-compact-json-v1`, numeric availabilityfalse and overallnull in16.617s. Diagnostic75 values are unqualified content diagnostics, not published grades. Shared Kimi was never stopped or faulted. This is one warm failover demonstration, not evidence of reliable cold/busy/concurrent serving or successful qualification.

Tests passed58 backend,33 gateway,4 lifecycle and24 frontend checks. Candidate API/gateway tests ran with network disabled. The new CPU-cap check rejects a4-CPU container when the controller is configured for3 CPUs. Private endpoints, model/contract selection, model-size identity separation and numeric withholding were tested.

The existing safe Kimi staging app passed44/44 core checks (run`82f88c8409`) and7/7 browser checks after both standbys were stopped. Both actual faster-whisper uploads received Kimi output with identical diagnostics/coaching, saved null grades and withheld analytics. ASR failure guards made no rubric calls; TTS was mocked. These checks do not complete STT/TTS backup evaluation.

Combined candidate reservations39/62 include initial Llama timing calls, the bounded stream probe, compact controls, Gemma controls and the full development run. Staging reservations4/8 cover the real Gemma failover, core rubric check and two real browser uploads. No exhausted budget was reset. All timeouts are retained; no holdout retries or prompt demonstrations were used.

## Isolation, rollback and remaining work

Candidate API/gateway images ran only in disposable internal QA containers; the live QA app images were not changed in this trial. Both new standbys are stopped, restart`no`, no host ports, and stores retained read-only. Future startup uses the dedicated model controller with its pinned digest; keep application fallback disabled unless all gates pass.

All six monitored production IDs/start times match this task's baseline. Primary Kimi container ID/start and CPU/memory/swap limits are unchanged, as are its pinned memory-mapped/cache settings. Five QA app/model services remain running. Final host available memory was16,934,727,680 bytes. No production deployment or cloud inference fallback occurred.

P0 backup and numeric grading remain blocked. These CPU-local candidates are memory-feasible but fail current latency/valid-reference requirements. More parameters alone did not solve the problem. All22 holdout texts are preserved. STT/TTS backups remain pending after text/grading. Pricing, commissions and campaigns remain pending explicit founder approval; no real-customer events or commercial records were changed.

## AgentVire record and source provenance

Implementation and evaluation evidence: [790a3cb](https://github.com/nrgore1/oratoplus-monorepo/commit/790a3cb), on the existing `codex/signup-activation-20261027` branch.

Only Ora journey/local-text-backup evidence and `ora-stronger-local-backup-20261101` were updated. The journey remains blocked, the backup task stays pending/unqualified, and STT/TTS tasks stay pending. No completed readiness or grading qualification was claimed.

Audit verification is valid; `source_changed` is false and commercial execution remains disabled. Transactional comparisons preserve all other tasks, all51 commercial tasks, products, campaigns, actions, events, prepared artifacts and the financial-source SHA. Totals remain279 tasks:88 completed,44 pending,90 blocked,6 in progress and51 awaiting approval.
