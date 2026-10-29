# OraToPlus Qwen backup evaluation — 2026-10-29

Qwen3 4B Instruct Q4_K_M is **not qualified as a Kimi backup** on the existing VPS under the unchanged serving deadlines. Numeric grades remain withheld. Kimi remains the primary, and no production deployment or commercial change occurred.

## Operational result

Pinned model digest: `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`. Ollama 0.12.6; CPU only; two CPUs; 4 GiB combined memory/swap ceiling; context 2048; one inference slot; read-only model store; internal QA network; no host port. Primary Kimi's four-CPU/10-GiB limits were preserved.

Three development-only inference attempts on two previously exposed arguments all hit the nine-second read deadline (9.020, 9.015, 9.018 seconds). The first and second attempts used the same shortest argument. One earlier reservation never dispatched inference because a worker copy was rejected by the read-only container. Reservations remain conservatively charged: 4/62; actual candidate attempts: 3. No retries on holdout occurred.

A real fallback drill used disposable candidate gateway/API containers. Only that gateway's primary address was deliberately unreachable; shared Kimi was never stopped. Qwen again timed out. The API returned heuristic coaching in 9.074 seconds, numeric availability false and overall null. This verifies failure containment, **not successful Qwen failover**. Positive provenance, cold, busy, malformed, and wrong-model paths were tested with mocks and must not be represented as successful live inference.

The manual standby was stopped after all candidate requests finished, recovering host available memory to approximately 9.5 GiB. It is retained stopped under an archive name. A separate Compose service is registered in created/stopped state, with restart disabled and no application enablement. The opt-in lifecycle script checks private-network isolation, resource caps and model digest, preloads only outside serving, and stops on readiness failure, termination or host available memory below 3 GiB. Offline lifecycle checks pass. The supervised running/restart path is not operationally qualified; do not enable it based on this report.

## Human-reference integrity and accuracy

The frozen selection remains 30 historically exposed development arguments and all 22 raw/canonically unique untouched holdout arguments, with disjoint topics and no in-context demonstrations. All 22 holdout texts remain unexposed to this candidate. Because development inference failed the operational screen, the holdout was not consumed and no calibration mapping was fitted or activated. MAE, bias and rank accuracy are **unavailable**, not passing or zero.

Unchanged gates require at least 30 valid development and 30 valid holdout predictions, coverage ≥90%, MAE ≤20, absolute bias ≤10, errors >25 on ≤20%, Spearman ≥0.30, sufficient variation and strictly lower MAE than a development-mean constant baseline. Eight independent fresh human examples are still missing. Written argument clarity/arrangement/local-sufficiency proxies do not establish vocal presence or overall speech grading. Previous primary-model human-reference failures also remain unresolved. No proof file or threshold was changed.

## Validation and isolation

- Candidate backend: 49/49 offline tests; gateway: 21/21, including 10 Qwen safety tests.
- Lifecycle: 3/3 offline tests. Frontend: 24/24 existing qualification/proxy tests; no frontend source or build artifact changed.
- Restored existing safe staging: 44/44 portfolio core checks, run `c351e4b803`.
- Browser: 7/7 checks, including two actual faster-whisper/Kimi uploads with identical diagnostics/coaching; saved numeric values null and analytics withheld. ASR failure cases were mocked and dispatched no rubric inference. TTS was mocked, so this is not a TTS backup test.
- Staging inference reservations: 4/8 (one failed Qwen fallback, one core Kimi check, two browser Kimi uploads).
- All six baseline production container IDs and start times match exactly. Five QA model/app services remain running; primary limits unchanged; fallback remains disabled; no cloud fallback configured.

## Rollback and remaining work

Live QA retained its original safe v5 coaching-only images throughout; candidate images were tested separately. To stop the optional standby use the separate Compose manifest's `stop qwen-backup`; no primary/shared service needs to be stopped. The model store is never deleted. Starting the manifest requires `QWEN_MODEL_STORE` set to the existing model directory and a foreground process supervisor running `scripts/qwen_backup_runtime.py <compose-path> supervise`; serving requests cannot pull or preload. Qualification and explicit server enablement are separate from readiness. This rejected model must remain disabled.

P0 local text/grading work remains open: evaluate another feasible local Llama/Qwen/Gemma/GPT-OSS candidate, validate successful failover/concurrency/deadlines, and obtain independent suitable human reference data before any numeric restoration. STT and TTS backup evaluation remains pending. Pricing, commissions and campaigns remain pending explicit founder approval. No emails, campaigns or real-customer events were created.

## AgentVire execution record

Source implementation/evidence commit: [4b6395d](https://github.com/nrgore1/oratoplus-monorepo/commit/4b6395d), on `codex/signup-activation-20261027`.

Updated only Ora journey/local-text-backup evidence and the `ora-qwen-backup-20261029` execution report. Journey remains blocked, local-text backup remains open, STT/TTS tasks remain pending. Audit verification is valid and `source_changed` is false. Transactional snapshots prove products, campaigns, actions, events, prepared artifacts, all 51 commercial tasks, non-Ora tasks, and the financial-source SHA unchanged. Commercial execution remains disabled.

Task totals remain 241: 62 completed, 37 pending, 88 blocked, 3 in progress and 51 awaiting approval. No candidate or numeric grading qualification was marked completed.
