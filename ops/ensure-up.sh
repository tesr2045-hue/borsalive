#!/usr/bin/env bash
# BIST Analiz — "ayakta tut" (idempotent). Kutu yeniden başlatıldıktan / taşındıktan sonra watchdog (→ uvicorn) ve
# ngrok-keepalive (→ ngrok kalıcı tünel) çalışmıyorsa başlatır. Çalışanlara DOKUNMAZ, hiçbir şeyi öldürmez.
# Tetikleyiciler: ~/.bashrc kancası (her yeni ajan kabuk oturumu `bash -ilc` ile açılırken + insan terminali),
# elle:  /workspace/bist-analiz/ops/ensure-up.sh   (çıktı: ops/ensure.log)
. /workspace/bist-analiz/ops/lib.sh
exec 9>/tmp/bist-ensure-up.lck
flock -n 9 || exit 0                     # aynı anda tek kopya
mkdir -p "$APP/ops"
"$APP/ops/install-hook.sh" --quiet 2>/dev/null   # kanca silinmişse (ör. ev dizini yenilendiyse) geri koy
did=""
if ! wd_running; then
  if [ -z "$IDEAL_PASSWORD" ]; then
    ops_log "watchdog çalışmıyor AMA IDEAL_PASSWORD bu ortamda yok → başlatılamadı (bir ajan kabuğundan tekrar çalıştırın)"
  else
    (cd "$APP" && start_detached "$WD_SCRIPT")
    did="$did watchdog"
  fi
fi
sleep 2
# watchdog zaten keepalive'ı başlatır; yine de bağımsız kontrol (watchdog başlatılamadıysa da tünel ayakta olsun)
if ! ka_running; then
  sleep 3
  if ! ka_running; then start_detached "$KA_SCRIPT"; did="$did ngrok-keepalive"; fi
fi
# v1.36.0 Cloudflare quick tunnel bekçisi (ngrok'tan bağımsız)
CF_SCRIPT=$APP/ops/cf-keepalive.sh
if [ -x "$CF_SCRIPT" ] && [ ! -f "$APP/ops/cf_disabled" ] && [ -z "$(script_pids "$CF_SCRIPT")" ]; then start_detached "$CF_SCRIPT"; did="$did cf-keepalive"; fi
if [ -n "$did" ]; then
  ops_log "başlatıldı:$did (tetik: ${ENSURE_TRIGGER:-elle}; uptime $(cut -d. -f1 /proc/uptime) sn)"
fi
[ "${1:-}" = "-v" ] && { echo "watchdog: $(script_pids "$WD_SCRIPT" | tr '\n' ' ')"; echo "keepalive: $(script_pids "$KA_SCRIPT" | tr '\n' ' ')"; echo "ngrok: $(ngrok_pids | tr '\n' ' ')"; echo "cf-keepalive: $(script_pids "$APP/ops/cf-keepalive.sh" | tr '\n' ' ')"; echo "başlatılan:${did:- yok}"; }
exit 0
