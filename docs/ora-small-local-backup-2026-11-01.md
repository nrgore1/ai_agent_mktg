# OraToPlus small local backup evaluation — 2026-11-01

**Llama fits the VPS and completed a real failover, but is rejected for grading quality and post-reload reliability. Numeric grades remain withheld.** The candidate is stopped and disabled. No cloud fallback, production deployment, pricing, commission or campaign change occurred.

## Candidate selection and frozen configuration

The current `gemma3:1b` manifest requires a newer Ollama than the pinned 0.12.6 runtime; the manifest check failed before downloading a usable model or making inference calls. The shared runtime was not upgraded. The next candidate was the explicitly quantized [Llama 3.2 1B Instruct Q4_K_M](https://ollama.com/library/llama3.2:1b-instruct-q4_K_M): 807,709,787 downloaded bytes, digest `22bc6b92eb0160c4629782fca05a9032c59d306ab2058b7dacc8a4644fbafa02`.

The standalone standby retained two CPUs, a 4-GiB combined memory/swap ceiling, context 2048, one inference slot, CPU-only generation, a read-only model directory, internal QA networking and no host ports. Primary Kimi's four-CPU/10-GiB limits were unchanged. The lifecycle checks host available memory against 3 GiB, verifies model identity, preloads outside serving traffic, monitors readiness and stops on termination/failure. Cold rejection and a supervised reload were exercised. Restart is disabled after rollback.

The unchanged v5 prompt, trait/span schema, zero temperature, seed42, 128 output-token budget and model-native Ollama chat framing were frozen before reference inference. Deadlines remain: primary10s; backup read9s and total11s; gateway target23s; application25s. No deadline or grading proof was relaxed. Provider source hashes and worker hash are retained in the frozen-profile evidence.

## Development accuracy: rejected before holdout

All30 development arguments returned structurally valid assessments within3.522–8.268s (mean5.3014s). The three prescreen outputs were reused, so each of the30 development arguments was scored once. **Every trait score was0 for every argument.** This is schema coverage, not accuracy or useful coaching.

| Written-content proxy | Development raw MAE | Bias | Errors >25 | Distinct scores | Rank signal |
|---|---:|---:|---:|---:|---|
| Clarity |55.00|-55.00|86.67%|1|undefined|
| Arrangement/structure |40.00|-40.00|70.00%|1|undefined|
| Local sufficiency/evidence |27.78|-27.78|43.33%|1|undefined|

These are descriptive **development** errors, not heldout accuracy estimates. A monotonic calibration could not be fitted because there was no raw variation. The failed fit was sealed with SHA256 `3a6871ddb676b3d78c2a50af41b9855fe651d8468aa6e43210c5442e6b673d3f`. No mapping was activated. No untouched holdout was consumed: all22 remaining raw/canonically unique holdout texts are preserved.

Unchanged acceptance still requires30 valid development and30 valid holdout examples, ≥90% model coverage, MAE≤20, absolute bias≤10, errors>25 on≤20%, Spearman≥0.30, meaningful variation and strictly beating the development-mean constant baseline. Eight independent fresh human examples are still missing. Written-content proxy labels do not qualify vocal presence or overall speech grading. All human/product gates remain unsatisfied; numeric restoration is prohibited.

## Actual operational drills and their limits

- A disposable primary stub delayed responses14s. The candidate gateway hit its real10s primary deadline, then invoked actual local Llama. The candidate API returned `method=llm`, exact Llama identity, `local_backup_used=true`, numeric availabilityfalse and overallnull in13.645s. Diagnostic values were again all0. Shared Kimi was never stopped or faulted.
- A running-but-unloaded standby was rejected in0.006s by readiness, with no generation/load from serving. The lifecycle then reloaded the pinned model outside serving.
- An overlapping caller was rejected as `local_backup_busy` while the first real HTTP inference was in flight. **That first inference after reload timed out at the unchanged9s read deadline.** The failed busy drill is retained; it was not retried to manufacture a pass. Model responses were never mocked. Only synchronization on actual HTTP dispatch was instrumented. No elapsed busy-rejection timing was persisted, so none is claimed.

The standby is stopped after all candidate requests completed. Compose remains opt-in with restart`no`; serving is disabled. This is not a qualified backup, reliable restart demonstration for inference, or production readiness claim.

## Isolated staging results: failures retained

Offline candidate checks passed51 backend tests and25 gateway tests; lifecycle3 and existing frontend24 also passed. No frontend source/build artifact changed.

The existing safe staging core regression passed43/44, run`92025d083b`. Its rubric check received heuristic coaching instead of expected Kimi model output. The candidate was already stopped and disabled. This is a primary-serving failure retained in evidence, not a candidate success.

Browser checks comprise6 unique passes and1 failure. The original run passed signup and both actual faster-whisper uploads, verified null numeric/saved scores, then failed repeat consistency because identical audio produced different heuristic versus Kimi diagnostics. That failure remains. The three unreached ASR-error/analytics guards were completed separately using mocked ASR failures and synthetic local-history fixtures, with zero rubric calls. No real upload was retried. TTS was mocked; STT/TTS backup evaluation is not completed by these checks.

## Isolation, budgets and remaining work

Candidate budget30/62; staging reservations6/8. Actual staging model attempts5: one failed post-reload Llama call, one successful Llama failover, one core Kimi attempt and two browser Kimi attempts. Cold readiness and follow-up browser guards made no model inference. No holdout retries, cloud inference or real-customer events occurred.

All six monitored production container IDs/start times match this run's initial snapshot. Four also match the older2026-10-28 receipt. The Individual and Institutional production APIs had already changed before this run; the new initial snapshot preserves that fact. None changed during this task. Five QA app/model services remain running, Kimi caps unchanged. Approximate host available memory after stopping the candidate was7.7GiB.

P0 remains open: primary reliability is unstable; the smaller Llama fails variation/accuracy and post-reload timing; independent human reference data is insufficient. Keep numeric grades withheld and the standby disabled. Evaluate a different feasible local text candidate before consuming untouched holdout, then verify all operational and product gates. Offline STT/TTS backups remain pending after text/grading. Pricing, commissions and campaigns require separate explicit founder approval.

## Reproduction and rollback

Use `deploy/qa-llama-backup.compose.json` with existing `LLAMA_MODEL_STORE`, `STANDBY_UID` and `STANDBY_GID`; its network is the existing internal QA network and it exposes no host port. `scripts/llama_backup_runtime.py <compose-path> supervise` performs offline preload and readiness/memory monitoring. `... stop` stops only the standby. The model store is retained. This rejected candidate must stay disabled; starting the lifecycle is not qualification or authorization to enable serving. Candidate images were tested separately; live QA retained its original safe v5 coaching-only images.

## AgentVire execution record

Source implementation/evidence: [f022168](https://github.com/nrgore1/oratoplus-monorepo/commit/f022168) on `codex/signup-activation-20261027`.

Only Ora journey/local-text-backup evidence and the `ora-small-backup-20261101` execution report were updated. Journey remains blocked, the local text backup task remains pending/unqualified, and offline STT/TTS tasks remain pending. No readiness or qualification was marked complete.

Audit verification is valid; `source_changed` is false and commercial execution remains disabled. Transactional comparisons preserve products, campaigns, actions, events, prepared artifacts, all51 commercial tasks, non-Ora tasks, and the financial-source SHA. Current totals are279 tasks:88 completed,44 pending,90 blocked,6 in progress and51 awaiting approval. These totals include intervening unrelated work and were not reset to the October snapshot.
