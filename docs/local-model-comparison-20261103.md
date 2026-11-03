# Local Mistral and Granite evaluation

3 November 2026, US Eastern. The owner requested a smaller local model after the Kimi K3 capacity check, then authorized candidates from an attached list. Selected candidates are the Mistral family’s `ministral-3:3b` and `granite3.3:2b`. Both are installed on the existing VPS. They are different models from Kimi K3; no K3 weights were installed and no cloud inference is used.

## Decision and release boundary

**Select Mistral only for choosing between prepared invitation drafts.** Do not enable unrestricted customer-facing generation, automatic pricing/commissions, numeric grading or campaign execution. Both candidates failed broader quality checks. Their language-model outputs cannot approve an action or override application permissions.

Production deployment is pending explicit owner approval. Automatic approval review rejected changing the running AgentVire image/model configuration because it interpreted the authorization as local testing only. The tested candidate is not activated; the installed model service is private.

The AgentVire candidate accepts only the two explicitly authorized small model names in addition to the existing Kimi route; cloud tags and unreviewed names remain rejected. Small models can return only a choice of 1 or 2. The application supplies the entire invitation text. It rejects incomplete output, unknown choices and free-form approved-claims drafting. A read-only readiness check requires the exact model to be loaded with a 2,048-token context; it never loads a model on a user request. Cold/unavailable models preserve the draft and require operator preload. Generation has a 20-second timeout.

## Hardware and installation

Measured VPS capacity: 32,094 MiB RAM, eight logical CPUs, approximately 232 GiB free root disk at the capacity check, and no detected NVIDIA runtime/GPU device. Kimi K3’s official 2.8-trillion-parameter MXFP4 specification implies roughly 1.4 TB for four-bit weights before scales or runtime overhead. This is an arithmetic estimate, not a complete hardware sizing recommendation. [Official Kimi K3 specification](https://huggingface.co/moonshotai/Kimi-K3).

The isolated runtime uses Ollama `v0.40.14`, pinned by the recorded image digest. It has a 6 GiB memory limit, a matching memory-plus-swap limit (no extra swap), and a two-CPU quota. Models are downloaded to a separate directory; there are no public model ports. After downloading, the container’s egress network was removed and it is connected only to its private test network. `OLLAMA_NO_CLOUD=1` is set. Other application/model containers were not replaced.

The [Ministral package](https://ollama.com/library/ministral-3:3b) is about 3 GB and the [Granite package](https://ollama.com/library/granite3.3:2b) about 1.5 GB; these are package sizes, not measured total runtime memory. During the Mistral evaluation the container approached its 6 GiB limit. Keep the conservative resource bounds and do not infer suitability for large contexts or concurrent generations from these results. Both model cards identify Apache 2.0 licensing: [Mistral](https://docs.mistral.ai/models/ministral-3b-latest), [IBM Granite](https://huggingface.co/ibm-granite/granite-3.3-2b-instruct).

## Same-task comparison

Eight fixed synthetic cases were run three times per model, using native chat, a 2,048-token context, two CPU threads, zero GPU layers, temperature 0.2 and a fixed seed. Schemas constrain shape, not correct answers. The gates require exact expected fields, complete output and latency no greater than 20 seconds. This is a small engineering benchmark; it is not a human-reviewed grading dataset or a general quality certification.

| Model | Exact structured cases | Median / slowest request | Initial model load | Writing probe |
|---|---:|---:|---:|---|
| Ministral 3 3B | 21/24 | 2.63 / 11.79 seconds | 24.60 seconds | Added “outdoors” to supplied hiking/cooking facts; not fully grounded. |
| Granite 3.3 2B | 15/24 | 2.14 / 7.67 seconds | 6.28 seconds | Rephrased the supplied hobbies without additional personal facts. |

All structured requests completed; the failures were output correctness. Both models added “skiing” after an instruction embedded in quoted member text, despite instructions to treat that text as data. Granite returned a 60% margin for supplied revenue 100, direct costs 20 and commission 5, instead of 75%. Granite also used the string “Not provided” where the harness expected null; that mismatch is an exact output-contract failure, not a fabricated occupation/city. The prompt could make that null requirement more explicit in a future benchmark. The original results remain recorded and are not retroactively changed.

Prepared invitations use a separate, smaller and enforceable scope. Four actual AgentVire requests for Jodibana, WeddingOS, Memoire and JodiUSA selected a permitted variant in 2.09–2.83 seconds. A fifth check verified that free-form claims drafting is blocked. No message was sent, action created or approval granted by these probes. Variant preference is only a hypothesis; it is not evidence of higher conversion.

## Reliability changes and tests

- AgentVire: the full suite passed 234 tests, and final focused native-chat/readiness tests passed. The final candidate passed all five real local integration checks. Interface labels now say “local model” instead of incorrectly naming every provider Kimi.
- Jodibana’s separate candidate: 49 provider safeguards passed with network access disabled. These cover exact model/context readiness, no implicit model loading, bounded requests, concurrency refusal, truncated/wrong-model output, cooldown/recovery, explicit cloud opt-in and a shared summary route. A real local adapter request returned the non-stub text `READY` from `ministral-3:3b` in 7.09 seconds. This proves connectivity, not general output quality. Jodibana production was not changed.
- The first AgentVire attempts timed out. Shortening the prompt alone did not resolve them. Runtime logs showed model reload/default prompt overhead. Using native chat with an explicit short system message and matching preload options resolved the scoped checks. Earlier failures remain part of the history; no failing result was approved.
- Earlier Kimi VL checks still fail their actual latency/factuality gates. Installing another model does not restore OraToPlus grades or certify Jodibana compatibility scores.

## Operations and recovery

Private VPS evaluation root: `~/jodibana-local-models-20261103`. The local model container/network is `jodi-local-model-qa-20261103`. Model IDs and digests, exact runtime image, candidate application image, timing samples and audit receipt are in the evidence JSON. No secrets or private payment URLs are published.

Preload the selected model with context 2048, CPU layers only, two threads, memory mapping enabled and `keep_alive=-1`; verify `/api/ps` before exposing generation. The application deliberately refuses a cold model. After a model-container restart, operator preload is required. Do not increase context or allow concurrent model loading without a new resource/reliability evaluation. The running local test service can be stopped without removing its persisted model files.

The prior AgentVire image is retained as `growthpilot-staging:before-local-models-20261103`; the deployment candidate and proposed Compose override are stored separately. Production deployment, if approved, replaces only AgentVire’s image and the two model endpoint/name settings, verifies protected records and preserves all other environment settings. A failed verification rolls back to the previous Compose files. No database migration is required. Jodibana’s candidate is a separate backlog item and is not included in that deployment.

The interrupted Stripe test fixture was canceled and its synthetic payment refunded; the provider showed only the original 4242 test card. No replacement card or renewal check is claimed passed. The temporary callback/route was removed and the isolated payment services stopped. Existing public sites returned HTTPS 200 afterward. Payment-method updates, production Stripe credentials/signing and other launch gates remain open.

## Approval and backlog status

AgentVire records the measured results without changing the existing portfolio qualification or approving a full launch. All 51 commercial task records remain identical and the audit chain verifies. Proposed paid tiers, commissions and campaigns stay pending; JodiUSA’s free grant is unchanged.

Remaining work:

1. Explicit production approval for the prepared-selection AgentVire update, then post-deployment verification; this is distinct from general model-quality approval.
2. Fresh adversarial/source-grounding examples and stronger content validation before free-form profiles or campaign claims.
3. Use deterministic application calculations for margins/commissions; do not delegate financial arithmetic or approval decisions to a small language model.
4. Complete Jodibana’s card-update/default-method/renewal checks on a new owned synthetic fixture, along with remaining payment/provider launch gates.
5. Keep numeric grading disabled until its separate human-reference gates pass.

Evidence: [model evaluation](evidence/local-model-comparison-20261103.json), [AgentVire receipt](evidence/local-model-agentvire-20261103.json).
