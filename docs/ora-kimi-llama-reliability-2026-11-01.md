# OraToPlus Kimi reliability and Llama format diagnosis — 2026-11-01

The previously failing isolated staging journeys now pass: **44/44 core checks and 7/7 browser checks**. Both real speech uploads received Kimi output and identical diagnostics/coaching. Numeric grades, saved numeric history and analytics remain withheld. No production deployment or cloud fallback occurred.

Llama's format guidance was improved, but the backup is **not qualified** and remains stopped/disabled. Its new development run accepted29/30 responses, with16 accepted all-zero assessments still present. All22 untouched holdout texts are preserved. No calibration was activated.

## Kimi findings and fix

The old bridge collapsed all upstream failures into a generic503. Prior product runs contained18-second upstream cancellations and alternated heuristic/model results on identical audio. Two baseline synthetic calls in this task initially succeeded in8.418/5.292s, confirming that the problem was intermittent.

A bounded streaming probe of an uncached prefix received no first token within18s. Load diagnostics showed `mmap=false`, an8405.22-MiB CPU weight buffer plus vision/model overhead, repeated memory-limit events and substantial major faults. One observation had10,052,644,864 anonymous bytes and634,572,800 file-cache bytes inside the unchanged10-GiB cap. The existing startup script also preloaded the olderQ2 tag rather than the servingIQ4 tag.

Batch-size experiments timed out and were **confounded by runner reloads**: Ollama reloads when runner options change. They do not establish a faster batch size, and no smaller batch was adopted. All failed diagnostic attempts remain in evidence. [Ollama0.12.6 runner-option comparison](https://github.com/ollama/ollama/blob/v0.12.6/server/sched.go) and [CPU mmap selection](https://github.com/ollama/ollama/blob/v0.12.6/llm/server.go) explain why load settings must match.

The fix pins the original batch512 and CPU/context/thread settings, explicitly enables memory mapping for this QA bridge, and preloads the exactIQ4 model/digest with those same options before the bridge admits traffic. The load-only operation took14.259s outside serving; it generated no assessment. Serving deadlines did not change. After preload, two uncached controls completed in17.507/14.296s with complete, strictly valid model output. These are joint load/configuration results, not an isolated estimate of mmap's causal speedup. The slower control remains close to the18-second limit; arbitrary workload reliability is not guaranteed by these tests.

Mapped memory was observed as1,419,997,184 anonymous bytes and9,264,308,224 file-cache bytes under the same cap. Final host available memory was15,838,085,120 bytes. No CPU/RAM/swap limit or Ollama version was increased.

The bridge now distinguishes deadline, upstream HTTP and transport failures using safe codes/logs. It caches only complete, model-pinned, strictly validated v5 rubric outputs for exact deterministic requests: at most8 entries for120s. Cache keys are hashes; the cache is in memory and does not persist prompts. Cold/mismatched model readiness still fails closed; cached output is never a heuristic or numeric qualification. Cache hits are explicitly marked and report zero new token usage. A real control took12.972s to generate, then0.011s on an exact cache hit with identical output.

The primary runtime container was not restarted. The staged startup artifact is updated for a future controlled restart; its full runtime restart path was not exercised. The new bridge's pinned preloader was exercised during the actual QA rollout. The previous private Compose/startup snapshots are retained remotely for rollback.

## Why Llama collapsed to zeros

Raw responses contained actual absent-category labels; the backend did not convert good ratings to zero. Prompt usage was285–422 tokens under context2048, so simple context truncation is not supported by the evidence.

On a synthetic coherent transcript:

| Diagnostic | Result |
|---|---|
| Original nested schema | First post-reload request timed out at9.016s |
| Same schema with reversed branches | Complete all-zero assessment |
| Flat enum/span schema | Absent labels paired with positive spans; strict validator rejected it |
| Original schema plus short output-shape instruction | Valid75/50/75/100 diagnostic values in4.789s |
| Same shape instruction on incoherent synthetic text | Valid all-zero assessment in5.817s |

The evidence supports missing output-format grounding as one cause, rather than branch ordering or a score-conversion bug. It does **not** show that formatting alone makes the1B model accurate. Ollama likewise recommends grounding structured output with schema information in the prompt. [Official structured-output guidance](https://github.com/ollama/ollama/blob/main/docs/capabilities/structured-outputs.mdx).

The implemented change adds only the short response-shape instruction for Llama. Rubric criteria, rating vocabularies, allowed spans, absence/span pairing and strict validator remain unchanged. The experimental flat schema was not adopted. No demonstrations, human labels or fresh holdout text were added to prompts. The `llama-json-shape-v1` generation contract is required for backup provenance and binds assessment IDs, separating old diagnostics from the changed generation behavior. It does not authorize grades.

## Frozen development evaluation: still unqualified

The provider was frozen after synthetic diagnosis and before scoring the existing30 development texts once. No retries were made. One first request timed out;29 completed. Sixteen of those29 were still all-zero across all traits. Nonzero output now occurs, but residual model errors remain substantial.

| Written-content proxy | Valid | Distinct raw scores | Raw development MAE | Bias | Development Spearman |
|---|---:|---|---:|---:|---:|
| Clarity |29|0,75|41.09|-31.32|0.197|
| Structure/arrangement |29|0,50,75|25.00|-22.13|0.569|
| Evidence/local sufficiency |29|0,25,75|28.45|-1.44|0.154|

These are descriptive development results, not heldout accuracy. A draft development-only isotonic fit was sealed with SHA256 `219afe4c1603fd19397c68c5e60e975b8fa6d333754347fc48c11355e735d3ed`; it was not activated. The minimum30 valid development predictions is not met. No holdout was consumed; all22 remain fresh, still8 short of the unchanged minimum30.

Unchanged human gates require30 valid examples per split, coverage≥90%, calibrated heldout MAE≤20, absolute bias≤10, >25-point errors on≤20%, Spearman≥0.30, sufficient variation and strictly beating a development-mean constant baseline. Written argument proxies do not qualify vocal presence or overall speech grading. No proof file, calibration gate or numeric-release guard was changed.

## Tests and actual staging

- Candidate backend52/52 and gateway25/25 network-isolated tests.
- Bridge/cache/preloader21/21 tests; the deployed product-source hashes match the21-test proof image. The proof image differs from deployment only in added test coverage.
- Existing local lifecycle3/3 and frontend24/24 tests.
- Core44/44, run`28c732a8dd`, including actual Kimi rubric output.
- Browser7/7: synthetic signup, two real faster-whisper/Kimi uploads with identical diagnostics/coaching and null saved scores, ASR failure guards with no rubric calls, and analytics refusing forged/unqualified grades. This rerun explicitly required `method=llm` on both real uploads. TTS was mocked; this is not an STT/TTS backup qualification.

Earlier43/44 core and6/7 browser failures remain in the previous report; they were not overwritten. Current diagnostic reservations17/24, development30/40, staging5/10. The direct staged cache check had one real generation plus one measured zero-token hit. Other staging reservations conservatively count requests, not an assertion of fresh inference for cached product responses. Operator load-only requests are separately recorded and are not generation calls.

## Isolation, rollout and limits

Only isolated QA `qa-kimi-bridge`, `qa-llm` and `ora-api` images were changed. The web image was retained. Llama fallback remains disabled and its standby stopped. Five QA app/model services remain running. All six monitored production IDs/start times are unchanged from this task's baseline; primary Kimi container ID/start and4CPU/10-GiB combined memory/swap limits also match exactly. No model-runtime upgrade, hardware purchase, cloud route or production deployment occurred.

Bridge source: [f5f4a0f](https://github.com/nrgore1/ai_agent_mktg/commit/f5f4a0f). Candidate provider/API changes and this evidence are on the existing Ora feature branch. Rollback uses the task's private pre-change Compose/startup snapshots, restores the prior QA images, and preloads the original matching runner options outside serving before admission. Never print those Compose snapshots; they contain synthetic secrets.

P0 remains blocked for numeric grading and backup qualification. Resolve the remaining Llama/model-quality and first-request timing limitations and obtain independent suitable human references before considering any grade restoration. All22 fresh holdout texts are preserved. Offline STT/TTS tasks stay pending. Pricing, commissions and campaigns remain pending explicit founder approval; no commercial/customer-event records were changed.

## AgentVire record and source provenance

Ora implementation/evidence: [2334031](https://github.com/nrgore1/oratoplus-monorepo/commit/2334031). Bridge/preload implementation: [f5f4a0f](https://github.com/nrgore1/ai_agent_mktg/commit/f5f4a0f). Both are pushed on the existing feature branches.

Only Ora journey/local-text-backup evidence and the `ora-kimi-llama-reliability-20261101` report were updated. The journey remains blocked, the local text backup remains pending/unqualified, and STT/TTS tasks stay pending. The passing primary reliability tests do not certify numeric grading or launch readiness.

The audit is valid, `source_changed` is false and commercial execution remains disabled. Transactional comparisons prove that all other execution tasks, all51 commercial tasks, products, campaigns, actions, events, prepared artifacts and the financial-source SHA are unchanged. Totals remain279 tasks:88 completed,44 pending,90 blocked,6 in progress and51 awaiting approval.
