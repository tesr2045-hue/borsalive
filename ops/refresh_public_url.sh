#!/bin/bash
# Write current ngrok public HTTPS URL into ops/public_url.txt (no secrets).
APP=/workspace/bist-analiz
u=$(curl -s -m 3 http://127.0.0.1:4040/api/tunnels 2>/dev/null | $APP/.venv/bin/python -c 'import json,sys
try: d=json.load(sys.stdin)
except Exception: raise SystemExit(1)
for t in d.get("tunnels") or []:
  u=t.get("public_url") or ""
  if u.startswith("https://"):
    print(u); break
')
[ -n "$u" ] && echo "$u" > $APP/ops/public_url.txt && echo "$u"
