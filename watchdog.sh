#!/usr/bin/env bash
# BIST Analiz watchdog — uvicorn'u ayakta tutar, her sabah 09:00 TR (hafta içi) temiz başlatır — veriler silinmez, kalıcı kayıtlar yeniden yüklenir.
# IDEAL_PASSWORD ortam değişkeniyle başlatılmalı (değer asla loglanmaz).
# Başlatma:  bash -lc 'nohup setsid /workspace/bist-analiz/watchdog.sh >/dev/null 2>&1 < /dev/null &'
# Kutu yeniden başlatma/taşıma sonrası otomatik başlatma: ops/ensure-up.sh (~/.bashrc kancası) — bkz. ops/README.md
cd /workspace/bist-analiz || exit 1
LOG=/workspace/bist-analiz/watchdog.log
PAT="uvicorn app.main:app --host 0.0.0.0 --port 8765"
log() { echo "$(TZ=Europe/Istanbul date '+%F %T') $*" >> "$LOG"; }
# v1.27.2 — İdealData akış güvenlik ağı (süreç içi kesinti korumasının yedeği): /api/ideal/status
# healthy=false + state=error VEYA last_msg_age çok yüksekse ve bu ≥5 dk kesintisiz sürerse uvicorn'u
# yeniden başlat (en çok 20 dk'da 1). login_failed hariç (İdealData sık girişi reddeder; süreç kendi bekler).
WD_STATUS=${WD_STATUS:-http://127.0.0.1:8765/api/ideal/status}
FEED_BAD_SEC=${WD_FEED_BAD_SEC:-300}; FEED_GAP_SEC=${WD_FEED_GAP_SEC:-1200}; FEED_AGE_MAX=${WD_FEED_AGE_MAX:-600}
FEED_STAMP=${WD_FEED_STAMP:-/workspace/bist-analiz/watchdog.feedrestart}
feed_bad_since=0
feedchk() {  # çıktı: "ok" | "bad <neden>" | "na"
  curl -s -m 10 "$WD_STATUS" | /workspace/bist-analiz/.venv/bin/python -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: print("na"); sys.exit()
st=d.get("state"); age=d.get("last_msg_age_sec"); mx=float(sys.argv[1])
if st in ("disabled","login_failed","init") or d.get("healthy"): print("ok")
elif st=="error": print("bad state=error age=%s err=%s" % (age, str(d.get("error") or "-")[:60].replace(" ","_")))
elif age is not None and age>mx: print("bad stale age=%s state=%s" % (age, st))
else: print("ok")' "$FEED_AGE_MAX" 2>/dev/null || echo na
}
feed_tick() {  # 0 → yeniden başlatıldı
  local f now last; f=$(feedchk); now=$(date +%s)
  case "$f" in
    bad*) [ "$feed_bad_since" -eq 0 ] && { feed_bad_since=$now; log "akış sağlıksız: ${f#bad } (izleniyor)"; } ;;
    *) [ "$feed_bad_since" -ne 0 ] && log "akış yeniden sağlıklı ($(( now - feed_bad_since )) sn sonra)"; feed_bad_since=0; return 1 ;;
  esac
  [ $(( now - feed_bad_since )) -lt "$FEED_BAD_SEC" ] && return 1
  case "$f" in *timed_out*|*Network_is_unreachable*|*No_route*|*Name_or_service*|*Temporary_failure*)
    # v1.37.0: ağ seviyesinde erişim yok → yeniden başlatma çözmez, tüm motorları soğuk başlatır; süreç kendi yeniden bağlanır
    [ $(( (now - feed_bad_since) % 1800 )) -lt 30 ] && log "akış sağlıksız (${f#bad }) — ağ hatası, uvicorn yeniden başlatılmıyor (süreç kendi bağlanıyor)"
    return 1 ;;
  esac
  last=$(cat "$FEED_STAMP" 2>/dev/null || echo 0)
  if [ $(( now - last )) -lt "$FEED_GAP_SEC" ]; then
    [ $(( (now - feed_bad_since) % 300 )) -lt 30 ] && log "akış hâlâ sağlıksız (${f#bad }) — son akış-yeniden başlatmasından $(( now - last )) sn geçti, 20 dk sınırı bekleniyor"
    return 1
  fi
  echo "$now" > "$FEED_STAMP"
  log "akış $(( now - feed_bad_since )) sn sağlıksız (${f#bad }) → uvicorn yeniden başlat"
  feed_bad_since=0
  stop; start "akış takıldı"
  return 0
}
if [ -z "$IDEAL_PASSWORD" ]; then log "HATA: IDEAL_PASSWORD yok, çıkılıyor"; exit 1; fi
echo $$ > /workspace/bist-analiz/watchdog.pid
# venv silinmişse (bilgisayar yeniden kurulduysa) otomatik yeniden kur
if [ ! -x .venv/bin/uvicorn ]; then log "venv yok, yeniden kuruluyor"; python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt >> "$LOG" 2>&1; fi
# ngrok kalıcı tüneli çalışmıyorsa başlat
# ops (05.10): süreç bulma /proc argv ile (pgrep -f başka komut satırlarına da eşleşebiliyordu); öldürme yalnız açık PID
. /workspace/bist-analiz/ops/lib.sh
ka_running || { start_detached "$KA_SCRIPT"; log "ngrok-keepalive yoktu → başlatıldı"; }
# Tünel bekçisi: ngrok süreci var ama genel URL ölü (ERR_NGROK_3200 vb.) → ngrok'u yeniden başlat (keepalive 5 sn'de geri açar).
# 3 ardışık kötü kontrol (~3 dk) + en çok 10 dk'da bir. Yerel uvicorn çökükse (down) tünele dokunmaz (sorun yerel).
TUN_EVERY=${WD_TUN_EVERY:-2}; TUN_BAD_MAX=${WD_TUN_BAD_MAX:-3}; TUN_GAP_SEC=${WD_TUN_GAP_SEC:-600}
TUN_STAMP=/workspace/bist-analiz/ops/ngrok.restart
tun_i=0; tun_bad=0
tunnel_tick() {  # $1 = yerel sağlık (ok|stale|down)
  tun_i=$((tun_i+1)); [ $((tun_i % TUN_EVERY)) -eq 0 ] || return 0
  ka_running || { start_detached "$KA_SCRIPT"; log "tünel bekçisi: ngrok-keepalive yoktu → başlatıldı"; tun_bad=0; return 0; }
  [ "$1" = "down" ] && return 0
  local pc; pc=$(public_check)
  if [ "$pc" = "neterr" ] && curl -s -m 3 http://127.0.0.1:4040/api/tunnels 2>/dev/null | grep -q '"public_url"'; then pc=ok; fi
  if [ "$pc" = "ok" ]; then [ $tun_bad -gt 0 ] && log "tünel bekçisi: genel URL yeniden sağlıklı"; tun_bad=0; return 0; fi
  tun_bad=$((tun_bad+1)); log "tünel bekçisi: genel URL sağlıksız ($pc) $tun_bad/$TUN_BAD_MAX"
  [ $tun_bad -lt "$TUN_BAD_MAX" ] && return 0
  local now last; now=$(date +%s); last=$(cat "$TUN_STAMP" 2>/dev/null || echo 0)
  if [ $((now - last)) -lt "$TUN_GAP_SEC" ]; then log "tünel bekçisi: son ngrok yeniden başlatmasından $((now - last)) sn geçti, 10 dk sınırı bekleniyor"; return 0; fi
  echo "$now" > "$TUN_STAMP"; tun_bad=0
  local pids; pids=$(ngrok_pids | tr '\n' ' ')
  log "tünel bekçisi: ngrok yeniden başlatılıyor (PID: ${pids:-yok}; neden: $pc)"
  for p in $pids; do kill "$p" 2>/dev/null; done; sleep 5
  for p in $pids; do [ -d "/proc/$p" ] && kill -9 "$p" 2>/dev/null; done
}
RESTARTS=0
# v1.37.0: eski sürüm her başlatmadan sonra körlemesine 45→900 sn uyuyordu (süreç çökse bile uygulama dakikalarca
# kapalı kalıyordu). Yeni: başlatınca en çok 120 sn sağlık bekle (3 sn'de bir yokla); süreç ölürse hemen dön.
# Art arda çöküşte (sağlıklı olamadan ölen süreç) bekleme 10→20→40→60 sn (üst sınır 60) — kapalı kalma ≤ ~1 dk.
start() {
  RESTARTS=$((RESTARTS+1))
  if [ $RESTARTS -gt 1 ]; then
    local b=$((10 * (1 << (RESTARTS > 4 ? 3 : RESTARTS - 2))))
    [ $b -gt 60 ] && b=60
    log "art arda yeniden başlatma #$RESTARTS → $b sn bekle"; sleep $b
  fi
  nohup setsid .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8765 --log-level info >> /tmp/app.log 2>&1 < /dev/null &
  local pid=$! t0; t0=$(date +%s)
  log "uvicorn başlatıldı pid=$pid ($1) #$RESTARTS"
  while [ $(( $(date +%s) - t0 )) -lt 120 ]; do
    sleep 3
    [ -d "/proc/$pid" ] || { log "uvicorn pid=$pid $(( $(date +%s) - t0 )) sn içinde çıktı"; return; }
    if curl -s -m 3 -o /dev/null -w '%{http_code}' http://127.0.0.1:8765/api/health 2>/dev/null | grep -q 200; then
      log "uvicorn sağlıklı ($(( $(date +%s) - t0 )) sn)"; RESTARTS=0; return
    fi
  done
}
stop() { for p in $(pgrep -f "$PAT"); do kill "$p" 2>/dev/null; done; sleep 4; for p in $(pgrep -f "$PAT"); do kill -9 "$p" 2>/dev/null; done; }
health() {  # çıktı: "ok" | "down" | "stale"
  curl -s -m 10 http://127.0.0.1:8765/api/live/stats | .venv/bin/python -c '
import json,sys,datetime,zoneinfo
try: d=json.load(sys.stdin)
except Exception: print("down"); sys.exit()
n=datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Istanbul")); m=n.hour*60+n.minute
sess = n.weekday()<5 and 9*60+40 <= m <= 18*60+15
f=d.get("feed") or {}
age=f.get("last_msg_age_sec")
if sess and (not f.get("logged_in") or age is None or age>120 or not d.get("stream_all")): print("stale")
else: print("ok")' 2>/dev/null || echo down
}
[ "${WD_LIB:-0}" = 1 ] && return 0 2>/dev/null
log "watchdog başladı pid=$$"
bad=0; last_daily=""
while true; do
  if ! pgrep -f "$PAT" >/dev/null; then start "süreç yok"; bad=0; continue; fi
  h=$(health)
  if [ "$h" = "ok" ]; then bad=0; RESTARTS=0; else bad=$((bad+1)); fi
  if [ $bad -ge 4 ]; then log "sağlık=$h (4 kez) → yeniden başlat"; stop; start "sağlık=$h"; bad=0; continue; fi
  if [ "$h" != "down" ] && feed_tick; then bad=0; continue; fi
  tunnel_tick "$h"
  # her işlem günü 09:00–09:04 TR arasında (v1.22.0: 09:40 → 09:00), süreç bugünden önce başlamışsa temiz yeniden başlat
  today=$(TZ=Europe/Istanbul date +%F); dow=$(TZ=Europe/Istanbul date +%u); hm=$(TZ=Europe/Istanbul date +%H%M)
  if [ "$dow" -le 5 ] && [ "$hm" -ge 0900 ] && [ "$hm" -le 0904 ] && [ "$last_daily" != "$today" ]; then
    pid=$(pgrep -f "$PAT" | head -1)
    st=$(TZ=Europe/Istanbul date -d "@$(stat -c %Y /proc/$pid 2>/dev/null || echo 0)" +%F 2>/dev/null)
    last_daily=$today
    if [ "$st" != "$today" ]; then log "seans öncesi günlük temiz başlatma"; stop; start "günlük 09:00"; continue; fi
  fi
  sleep 30
done
