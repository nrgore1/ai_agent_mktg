#!/bin/bash
# Start the private local model once, outside application request deadlines.
set -u
/bin/ollama serve &
server=$!
trap 'kill -TERM "$server" 2>/dev/null || true' TERM INT EXIT
connected=0
for attempt in {1..30}; do
  if { exec 3<>/dev/tcp/127.0.0.1/11434; } 2>/dev/null; then connected=1; break; fi
  sleep 1
done
if [ "$connected" = 1 ]; then
  payload='{"model":"hf.co/mradermacher/Kimi-VL-A3B-Instruct-GGUF:Q2_K","stream":false,"keep_alive":-1,"options":{"num_ctx":2048,"num_gpu":0,"num_thread":4}}'
  printf 'POST /api/generate HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: %s\r\nConnection: close\r\n\r\n%s' "${#payload}" "$payload" >&3
  if IFS= read -r -t 120 status <&3 && [[ "$status" == *" 200 "* ]]; then
    echo 'Private Kimi preload completed; bridge still verifies current residency.'
  else
    echo 'Private Kimi preload failed; no automatic retry; inference remains unavailable until operator repair.' >&2
  fi
  exec 3<&-
  exec 3>&-
else
  echo 'Private Kimi server did not become reachable; no preload retry.' >&2
fi
wait "$server"
