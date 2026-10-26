# Local Kimi

The installed local model discovered on 2026-10-26 is `hf.co/mradermacher/Kimi-VL-A3B-Instruct-GGUF:Q2_K`, about 7.2 GB. A structured-output smoke test succeeded in 127.5 seconds including model startup. It is not the newest Kimi model.

Kimi K3 is documented as a 2.8T parameter model by [Moonshot](https://www.kimi.com/en/help/new-user-guide/agentic-chat) and is listed by [Ollama](https://ollama.com/library/kimi-k3) with a cloud tag. It cannot be represented as local on this 31 GiB VPS. Cloud tags are explicitly rejected. A newer local model can be selected by updating the server environment after a successful hardware and inference check.

Run `scripts/start-local-kimi-tunnel.ps1` on Windows with Ollama running. SSH binds port 11435 to VPS loopback and forwards it to the computer's local Ollama port. A restricted Docker bridge on the private edge gateway exposes only tags and generation routes to the app. No public Ollama listener is added. This requires the computer and SSH connection to stay on; loss of the connection produces a clear provider failure and preserves drafts.

Launch with both `compose.staging.yaml` and `compose.kimi.yaml`. Set `GROWTHPILOT_OLLAMA_MODEL` to the exact installed tag in the protected shared environment. The bridge is specific to the inspected VPS edge gateway 172.16.1.1; review that address for a different host. Verified product evidence is required before AI generation. Sources are treated as untrusted data, and all generated drafts require review.
