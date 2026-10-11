#!/bin/bash
# v1.36.0 — Cloudflare quick tunnel (hesapsız, trycloudflare.com) bekçisi. ngrok'tan bağımsız, paralel.
# cloudflared çıkarsa yeniden başlatır. Edge'e bağlanamazsa / 429 alırsa artan bekleme (2 dk → 30 dk) — Cloudflare'i
# dövmez. URL → ops/cf_url.txt, durum → ops/cf_state.json. Yeni link: cloudflared PID'ini öldürmek yeter.
APP=/workspace/bist-analiz
BIN=/workspace/cloudflared
RUNLOG=$APP/ops/cf_run.log
URLF=$APP/ops/cf_url.txt
STF=$APP/ops/cf_state.json
back=120
state() { printf '{"url":"%s","start":%s,"pid":%s,"registered":%s,"err":"%s","next_retry":%s,"ts":%s}\n' "$1" "$2" "$3" "$4" "$5" "$6" "$(date +%s)" > "$STF.tmp" && mv "$STF.tmp" "$STF"; }
while true; do
  : > "$RUNLOG"
  start=$(date +%s)
  "$BIN" tunnel --no-autoupdate --url http://localhost:8765 >> "$RUNLOG" 2>&1 &
  pid=$!
  url=""; reg=false
  for i in $(seq 1 45); do
    sleep 2
    [ -d /proc/$pid ] || break
    [ -z "$url" ] && url=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$RUNLOG" | head -1)
    if grep -q 'Registered tunnel connection' "$RUNLOG"; then reg=true; break; fi
  done
  if $reg; then
    echo "$url" > "$URLF"
    state "$url" "$start" "$pid" true "" 0
    back=120
    wait $pid
    state "" "$start" 0 false "çıktı" 0
    sleep 5
    continue
  fi
  err="edge bağlantısı kurulamadı (UDP/TCP 7844 kapalı olabilir)"
  grep -qi '429\|Too Many Requests\|1015' "$RUNLOG" && { err="429 hız sınırı (trycloudflare)"; [ $back -lt 600 ] && back=600; }
  [ -d /proc/$pid ] || grep -q . "$RUNLOG" || err="cloudflared çalışmadı"
  kill $pid 2>/dev/null; sleep 2; [ -d /proc/$pid ] && kill -9 $pid 2>/dev/null
  state "$url" "$start" 0 false "$err" $(( $(date +%s) + back ))
  sleep $back
  back=$(( back * 2 )); [ $back -gt 1800 ] && back=1800
done
