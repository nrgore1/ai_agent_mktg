"""Private CPU Kimi bridge: ready-only inference, no waiting queue or cloud route."""
import json, os, threading, urllib.error, urllib.request
import hashlib, time, copy, socket, logging
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODEL = os.environ.get("GROWTHPILOT_OLLAMA_MODEL", "hf.co/mradermacher/Kimi-VL-A3B-Instruct-GGUF:Q2_K")
UPSTREAM = os.environ.get("GROWTHPILOT_LOCAL_OLLAMA_URL", "http://127.0.0.1:11435").rstrip("/")
SLOT = threading.BoundedSemaphore(1)

MODEL_DIGEST = os.getenv('GROWTHPILOT_OLLAMA_MODEL_DIGEST', '')
MMAP = os.getenv('GROWTHPILOT_KIMI_MMAP')
CACHE_ENABLED = os.getenv('GROWTHPILOT_KIMI_CACHE_ENABLED') == 'true'
CACHE_TTL = 120
CACHE_LIMIT = 8
CACHE = OrderedDict()
CACHE_LOCK = threading.Lock()
RATINGS = {'clarity':['unintelligible','unclear','partly_clear','clear','very_clear'],'structure':['unstructured','disconnected','partly_connected','coherent','well_organized'],'evidence':['no_support','assertion_only','limited_support','relevant_support','sufficient_support'],'presence':['no_purpose','weak_purpose','some_purpose','purposeful','engaging']}

def load_options():
    options = {'num_ctx':2048,'num_gpu':0,'num_thread':4,'num_batch':512}
    if MMAP in ('true','false'):
        options['use_mmap'] = MMAP == 'true'
    return options

def rubric_schema(count):
    if type(count)is not int or not 1 <= count <= 24:raise ValueError('Invalid span count')
    props={}
    for trait,choices in RATINGS.items():
        props[trait]={'oneOf':[{'type':'object','properties':{'rating':{'const':choices[0]},'span':{'const':0}},'required':['rating','span'],'additionalProperties':False},{'type':'object','properties':{'rating':{'type':'string','enum':choices[1:]},'span':{'type':'integer','minimum':1,'maximum':count}},'required':['rating','span'],'additionalProperties':False}]}
    return {'type':'object','properties':props,'required':list(RATINGS),'additionalProperties':False}

def cache_key(payload):
    if not CACHE_ENABLED or payload['options'].get('seed') != 42 or payload['options'].get('temperature') != 0:return None
    try:
        count=payload['format']['properties']['clarity']['oneOf'][1]['properties']['span']['maximum']
        if payload['format'] != rubric_schema(count):return None
    except (KeyError,TypeError,ValueError,IndexError):return None
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def valid_cached_assessment(data, payload):
    try:
        if not isinstance(data,dict):return False
        if data.get('model') != MODEL or data.get('done') is not True or data.get('done_reason') != 'stop':return False
        output = data['response']
        if not isinstance(output,str) or not 1 <= len(output) <= 8192:return False
        value,end = json.JSONDecoder().raw_decode(output.strip())
        if output.strip()[end:].strip() or not isinstance(value,dict) or set(value) != set(RATINGS):return False
        for trait,choices in RATINGS.items():
            item=value[trait]
            count=payload['format']['properties'][trait]['oneOf'][1]['properties']['span']['maximum']
            if type(count)is not int or not 1 <= count <= 24:return False
            if not isinstance(item,dict) or set(item) != {'rating','span'} or item['rating']not in choices:return False
            if type(item['span'])is not int or not 0 <= item['span'] <= count:return False
            if (item['rating']==choices[0]) != (item['span']==0):return False
        return True
    except (KeyError,TypeError,ValueError,IndexError):return False

def cached_result(key):
    if key is None:return None
    with CACHE_LOCK:
        entry=CACHE.get(key)
        if entry is None:return None
        recorded,data=entry
        if time.monotonic()-recorded > CACHE_TTL:
            del CACHE[key];return None
        result=copy.deepcopy(data)
    result.update(cache_hit=True,cache_age_seconds=round(time.monotonic()-recorded,3))
    # Reused output is not newly generated token usage.
    for name in ['prompt_eval_count','eval_count','total_duration','load_duration','prompt_eval_duration','eval_duration']:result[name]=0
    return result

def remember_result(key,data,payload):
    if key is None or not valid_cached_assessment(data,payload):return
    with CACHE_LOCK:
        CACHE[key]=(time.monotonic(),copy.deepcopy(data));CACHE.move_to_end(key)
        while len(CACHE)>CACHE_LIMIT:CACHE.popitem(last=False)


def model_ready():
    with urllib.request.urlopen(UPSTREAM + "/api/ps", timeout=2) as response:
        data = json.loads(response.read(32768))
    return any(m.get("name") == MODEL and m.get("size_vram") == 0 and m.get("context_length") == 2048 and (not MODEL_DIGEST or m.get("digest") == MODEL_DIGEST) for m in data.get("models", []))

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
    result["options"].update(load_options())
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
        key = cache_key(payload)
        cached = cached_result(key)
        if cached is not None:
            try:
                if not model_ready():return self.reply(503, {'error':'local_model_cold_operator_preload_required'})
                return self.reply(200,cached)
            except Exception:return self.reply(503, {'error':'local_runtime_unavailable'})
        if not SLOT.acquire(blocking=False): return self.reply(503, {"error": "local_model_busy"})
        started=time.monotonic()
        try:
            if not model_ready(): return self.reply(503, {"error": "local_model_cold_operator_preload_required"})
            req = urllib.request.Request(UPSTREAM + "/api/generate", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=18) as response:
                body = response.read(262145)
            if len(body) > 262144: return self.reply(502, {"error": "local_response_too_large"})
            data=json.loads(body)
            remember_result(key,data,payload)
            return self.reply(200,data)
        except (TimeoutError,socket.timeout):
            logging.warning('local_inference_deadline elapsed=%.3f',time.monotonic()-started)
            return self.reply(503, {'error':'local_inference_deadline'})
        except urllib.error.HTTPError as error:
            logging.warning('local_upstream_http status=%s elapsed=%.3f',error.code,time.monotonic()-started)
            return self.reply(503, {'error':'local_upstream_http','upstream_status':error.code})
        except Exception:
            logging.warning('local_runtime_transport elapsed=%.3f',time.monotonic()-started)
            return self.reply(503, {'error':'local_runtime_transport'})
        finally: SLOT.release()

if __name__ == "__main__":
    ThreadingHTTPServer((os.environ.get("GROWTHPILOT_BRIDGE_BIND", "172.16.27.1"), 11437), Bridge).serve_forever()
