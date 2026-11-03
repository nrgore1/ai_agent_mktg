# Staging integrations — 28 October 2026

Scope: isolated `agentvire-signup-qa` on Hostinger VPS, synthetic accounts/data only. No production or commercial changes.

The final core HTTP run `4bb8fe0dd6` passed 44/44 portfolio checks. It deliberately stopped the QA LLM gateway to verify labelled heuristic fallback without extra inference, then restored it. Do not cite this as LLM success.

Both real market adapters returned 17 filtered USDC/Base opportunities; advisory SMDP scoring and readiness passed. Upstream pool observation timestamps were absent: retrieval time does not prove source freshness. Institutional `route.run` authorization remains a separate release gate. No trading or provider execution is authorized.

Three owner-only Postmark transactional diagnostics were delivered according to provider events. This is provider delivery proof, not mailbox placement, automatic OTP inbox completion, bounce/webhook acceptance or campaign approval. Real OTP challenge generation/verification remains tested through guarded synthetic capture. No production credentials were stored in QA APIs.

OraToPlus passed real local Piper synthesis, signed audio fetch, unsigned-access denial and frontend-proxied faster-whisper with word timings. Separate QA MinIO and model-cache copies are used. The loopback signed media gateway preserves the signing Host. Real microphone/accents/human quality remain open; synthetic recognition included an opening-verb substitution.

Installed local model: `hf.co/mradermacher/Kimi-VL-A3B-Instruct-GGUF:Q2_K`. No claim that this is the newest Kimi release. Pinned local inference and cloud denial are configured in QA only. OraToPlus chat returned a real local-model response. Both LiqMint advisory requests exceeded existing 20/25-second limits; Ora rubric scoring exceeded 25 seconds and returned explicit heuristic scoring. These are unresolved release blockers. Do not increase harness deadlines or switch to cloud to manufacture a pass. Existing gateway-to-core usage telemetry was rejected (401); usage-ledger integration remains unverified. Source capability/configuration is not application acceptance.

Recovery: `/home/nrgore1/projects/launch-readiness-recovery/integrations-20261028` and protected VPS `compose-before-integrations-20261028.json`; previous images retained. Reload QA nginx upstreams after API replacements. Do not replay diagnostic email sends or inference blindly. An initial six-call test budget did not encompass one supplemental core scoring dispatch; seven model dispatches were reconstructed, so the test orchestration budget was exceeded. Subsequent core checks used explicit gateway outage injection and no model calls. This is not full agent-harness compliance.

Remaining gates: real OTP-to-owner-inbox completion/placement, SMTP/auth/email webhook validation where applicable, market observation freshness, authorized institutional routing acceptance, local Kimi latency/structured rubric quality, usage ledger, microphone/device/voice quality and business acceptance. Pricing, commissions and campaigns remain pending founder approval.

## AgentVire evidence update

Private execution report `staging-integrations-20261028` is recorded with a valid audit chain. Product journey tasks 1, 2 and 3 remain in progress. All 51 commercial gates remain awaiting founder approval, commercial execution remains disabled, and products/campaigns/actions/events and private economics-source hashes were unchanged by the update. No synthetic acquisition events were recorded.

Subsequent OraToPlus Django SMTP TLS authentication passed using ephemeral stdin credentials, with zero additional messages and no permanent provider secret in the QA API. A new unique QA-only internal token was configured for gateway-to-core usage telemetry after the observed 401 errors; no further inference was sent, so runtime usage-ingestion acceptance remains open.

Deterministic validation: 23 advisory/local-provider/governance unit cases plus 7 mail/QA-boundary cases per LiqMint edition, 4 Ora gateway guard cases and 6 harness-gate cases per edition: 76 passed. Both inventory checks passed; release/all-agent compliance was not claimed.

Current staging-only images: Individual API `agentvire-signup-qa/individual-api:20261028-mail-r2`; Institutional API `agentvire-signup-qa/institutional-api:20261028-mail-r2`; LLM `agentvire-signup-qa/llm:20261028`. QA web gateways remain loopback ports 18281/18282/18283; signed media uses 18284. Preserve the protected compose file and all previous images for rollback; do not commit secrets.
