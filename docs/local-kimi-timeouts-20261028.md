# Local Kimi staging timeout repair — 28 October 2026

The three staging timeout gates are resolved with the existing 20/25-second application limits unchanged. Full launch readiness and rubric grading accuracy are not certified.

| Real application check | Seconds | Existing deadline |
| --- | ---: | ---: |
| LiqMint Individual advisory | 7.570 | 20 |
| LiqMint Institutional advisory | 9.380 | 25 |
| OraToPlus rubric (`method=llm`) | 8.265 | 25 |

Final core HTTP run `900f3070bc`: 44 passed, zero failed, including actual local-LLM rubric feedback. Focused deterministic tests: 78 passed; offline harness-gate cases: 12 passed; both LiqMint inventory checks passed. These are synthetic staging samples, not latency percentiles or a production SLA.

The same installed Kimi-VL-A3B Q2_K weights were SHA-256 verified and placed in an isolated Hostinger VPS-local Ollama runtime. Model inference no longer depends on the laptop or its reverse tunnel. The model directory is read-only; no external inference API or new cloud hosting was introduced. The runtime is capped at four vCPU and ten GiB RAM/combined swap ceiling, one loaded model and one active generation. Original local models and previous images/configuration remain preserved.

The first VPS bootstrap model load took 40.7 seconds outside user requests. A subsequent startup warmed automatically in 12.1 seconds. The startup script makes one bounded preload attempt and does not spin an automatic retry loop. Readiness rejected cold state in 17 ms. A real simultaneous inference request was rejected as busy in 2 ms while readiness returned promptly. The bridge has no waiting queue and enforces a bounded upstream request.

Local-only prompts now use compact server-owned edition facts; browser persona/role hints do not select authority. Existing governance runs before local inference and durable attempt/deadline controls remain in force. The canonical Moonshot assistant prefix avoids closing an empty assistant turn; JSON-schema output constrains response size. Model answers that repeat the question or claim AI can approve/execute/bypass are rejected. Rubric placeholders, incomplete sentences, invalid score types/ranges and uninformative extreme vectors are rejected instead of being labelled successful LLM scoring.

Initial candidate receipts retain semantic failures (an unsafe authority claim, an echoed question and placeholder feedback); they are not accepted successes. Source tests and validators cover these failures. The final rubric is structurally valid but still uncalibrated: one synthetic response undervalued explicit numerical evidence. Human-labelled grading benchmarks and coaching-quality review remain necessary. No claim of full agent-harness compliance is made.

The persisted run budget reserved 20/20 calls conservatively, including preloads and rejected attempts; no additional inference was run after that limit. Private receipts and rollback compose are under the deployment user's `agentvire-launch-qa-20261027` directory. Native pre-change source snapshots and the bounded contract are under `/home/nrgore1/projects/launch-readiness-recovery/kimi-timeouts-20261028`. Windows/OneDrive legacy sources, production/media assets and production databases were not changed or retired.

The owner confirmed all three earlier transactional email diagnostics arrived in the inbox. This does not approve campaigns or replace real OTP-to-inbox acceptance. Market freshness, authorized institutional routing, human/business acceptance and rubric calibration remain open. All pricing, commissions and campaigns remain pending founder approval. All six relevant production container IDs and start times remain unchanged.

Template reference: [Moonshot tokenizer/chat template](https://huggingface.co/moonshotai/Kimi-VL-A3B-Instruct/raw/main/tokenizer_config.json). Generation controls: [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md).
