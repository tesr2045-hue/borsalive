#!/bin/bash
# v1.35.1 — ngrok tünelini ayakta tutar. Etkin config + web portu data/ngrok_active.json'dan okunur
# (Link Optimizasyon hesap geçişi yeni ajanı kendisi başlatır; bu betik onu ÖLDÜRMEZ ve ÇİFTLEMEZ:
#  etkin portta bir ajan cevap veriyorsa hiçbir şey yapmaz).
APP=/workspace/bist-analiz
BIN=/workspace/ngrok
LOG=/workspace/ngrok.log
ACT=$APP/data/ngrok_active.json
while true; do
  CFG=$HOME/.config/ngrok/ngrok.yml; PORT=4040
  if [ -f "$ACT" ]; then
    c=$(python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));print(d["cfg"],d["port"])' "$ACT" 2>/dev/null)
    [ -n "$c" ] && { CFG=${c% *}; PORT=${c##* }; }
  fi
  if curl -s -m 3 "http://127.0.0.1:$PORT/api/tunnels" 2>/dev/null | grep -q '"public_url"'; then sleep 10; continue; fi
  # etkin portta ajan yok/tünelsiz: o porttaki takılı ajanı (varsa) bırak, yeniden başlat
  if [ -n "$FORCE_NGROK_URL" ]; then
    $BIN http 8765 --config="$CFG" --url="$FORCE_NGROK_URL" --log=stdout >> "$LOG" 2>&1
  else
    $BIN http 8765 --config="$CFG" --log=stdout >> "$LOG" 2>&1
  fi
  sleep 5
done
