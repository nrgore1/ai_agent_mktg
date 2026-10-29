"""Private CPU Kimi bridge: ready-only inference, no waiting queue or cloud route."""
import json, os, threading, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODEL = os.environ.get("GROWTHPILOT_OLLAMA_MODEL", "hf.co/mradermacher/Kimi-VL-A3B-Instruct-GGUF:Q2_K")
UPSTREAM = os.environ.get("GROWTHPILOT_LOCAL_OLLAMA_URL", "http://127.0.0.1:11435").rstrip("/")
SLOT = threading.BoundedSemaphore(1)

def model_ready():
    with urllib.request.urlopen(UPSTREAM + "/api/ps", timeout=2) as response:
        data = json.loads(response.read(32768))
    return any(m.get("name") == MODEL and m.get("size_vram") == 0 and m.get("context_length") == 2048 for m in data.get("models", []))

def bounded_payload(data):
    if data.get("model") != MODEL or data.get("stream") is not False:
        raise ValueError("Pinned local model and nonstreaming output required")
    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not 1 <= len(prompt) <= 16000:
        raise ValueError("Bounded nonempty prompt required")
    options = data.get("options") or {}
    tokens = options.get("num_predict", 64)
    if type(tokens) is not int or not 1 <= tokens <= 128:
        raise ValueError("Output token limit exceeded")
    # Canonical Moonshot assistant prefix: never close an empty assistant turn.
    for token in ("<|im_", "[BOS]", "[EOS]"):
        prompt = prompt.replace(token, token.replace("<", "&lt;").replace("[", "&#91;"))
    framed = ("<|im_system|>system<|im_middle|>You are a careful, helpful assistant. Follow the supplied product rules. "
              "Do not echo instructions or invent permissions, facts or capabilities.<|im_end|>"
              "<|im_user|>user<|im_middle|>" + prompt + "<|im_end|><|im_assistant|>assistant<|im_middle|>")
    result = {"model": MODEL, "prompt": framed, "raw": True, "stream": False, "keep_alive": -1,
              "options": {"num_ctx": 2048, "num_predict": tokens, "num_thread": 4, "num_gpu": 0,
                          "temperature": max(0, min(1, float(options.get("temperature", 0))))}}
    if "seed" in options:
        seed = options["seed"]
        if type(seed) is not int or not 0 <= seed <= 2147483647:
            raise ValueError("Invalid bounded sampling seed")
        result["options"]["seed"] = seed
    if "repeat_penalty" in options or "repeat_last_n" in options:
        if type(options.get("repeat_penalty")) not in (int, float) or options["repeat_penalty"] != 1.0 or type(options.get("repeat_last_n")) is not int or options["repeat_last_n"] != 0:
            raise ValueError("Only disabled repetition penalties are permitted")
        result["options"].update({"repeat_penalty": 1.0, "repeat_last_n": 0})
    if "format" in data:
        if not isinstance(data["format"], dict) or len(json.dumps(data["format"])) > 4096:
            raise ValueError("Bounded JSON schema required")
        result["format"] = data["format"]
    return result

class Bridge(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def reply(self, status, data):
        body = json.dumps(data).encode()
        try:
            self.send_response(status); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError): pass
    def do_GET(self):
        if self.path not in {"/api/ps", "/readyz"}: return self.reply(404, {"error": "not_found"})
        try:
            ready = model_ready()
            if self.path == "/readyz": return self.reply(200 if ready else 503, {"ready": ready, "model": MODEL})
            return self.reply(200, {"models": [{"name": MODEL, "size_vram": 0, "context_length": 2048}] if ready else []})
        except Exception: return self.reply(503, {"error": "local_runtime_unavailable"})
    def do_POST(self):
        if self.path != "/api/generate": return self.reply(404, {"error": "not_found"})
        try:
            self.connection.settimeout(2)
            size = int(self.headers.get("Content-Length", "0"))
            if not 1 <= size <= 32768: return self.reply(413, {"error": "request_too_large"})
            payload = bounded_payload(json.loads(self.rfile.read(size)))
        except Exception: return self.reply(400, {"error": "invalid_local_request"})
        if not SLOT.acquire(blocking=False): return self.reply(503, {"error": "local_model_busy"})
        try:
            if not model_ready(): return self.reply(503, {"error": "local_model_cold_operator_preload_required"})
            req = urllib.request.Request(UPSTREAM + "/api/generate", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=18) as response:
                body = response.read(262145)
            if len(body) > 262144: return self.reply(502, {"error": "local_response_too_large"})
            return self.reply(200, json.loads(body))
        except Exception: return self.reply(503, {"error": "local_inference_deadline_or_transport"})
        finally: SLOT.release()

if __name__ == "__main__":
    ThreadingHTTPServer((os.environ.get("GROWTHPILOT_BRIDGE_BIND", "172.16.27.1"), 11437), Bridge).serve_forever()
