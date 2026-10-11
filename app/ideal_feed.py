"""İdealData canlı WebSocket akışı (v1.16.0).

Arka planda tek bir WebSocket bağlantısı (wss://ms5.idealdata.com.tr:7651/) açar,
giriş yapar ve şu verileri bellekte (thread-safe) tutar:

* Y 26  — tüm piyasa canlı kotasyon akışı (son, alış, satış, yüksek, düşük, önceki
          kapanış, hacim lot, işlem hacmi TL, VWAP …)  → Yahoo gecikmeli fiyatını ezer
* Y 43  — giriş anı kotasyon görüntüsü (piyasa / son / önceki kapanış)
* Y 33  — derinlik görüntüsü (25 kademe alış/satış lot + emir)
* SRV_DRN — derinlik kademe güncellemeleri (D) + gerçekleşen işlemler (I)
* Y 34  — son işlemler görüntüsü (saat, fiyat, lot, yön, alıcı, satıcı kurum)
* Y 38  — fiyat kademe analizi (fiyat başına lot, alış %, satış %) → gerçek footprint
* Y 41  — tavan / taban / VWAP / gün yüksek / düşük
* SRV_DGLM_TAR2 — AKD (aracı kurum dağılımı: net lot TUM, toplam lot TOPLAM, maliyet)

Şifre yalnızca çalışma anında os.environ['IDEAL_PASSWORD'] üzerinden okunur;
hiçbir log/dosyaya yazılmaz. Ham örnek mesajlar data/ideal_debug/raw_samples.log
dosyasına oturum/şifre/token maskelenerek yazılır (REQ_CONNECT asla yazılmaz).
"""
from __future__ import annotations

import collections
import json
import logging
import os
import socket
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

try:
    import websocket  # websocket-client
except Exception:  # pragma: no cover
    websocket = None

logger = logging.getLogger("bist.ideal")

IST = ZoneInfo("Europe/Istanbul")
WS_URL = os.environ.get("IDEAL_WS_URL") or "wss://ms5.idealdata.com.tr:7651/"
S1, S2, S3 = "\x02", "\x03", "\x04"
DEBUG_DIR = Path(__file__).resolve().parent.parent / "data" / "ideal_debug"
AKD_DAY_DIR = Path(__file__).resolve().parent.parent / "data" / "akd"      # v1.21.3 günlük AKD kalıcı deposu
AKDD_SESSION_AGE = float(os.environ.get("IDEAL_AKDD_AGE") or 200.0)        # seans içi yenileme hedefi (sn)
AKDD_GAP_OPEN = float(os.environ.get("IDEAL_AKDD_GAP_OPEN") or 0.05)
AKDD_GAP_CLOSED = float(os.environ.get("IDEAL_AKDD_GAP_CLOSED") or 0.3)
SAMPLES_FILE = DEBUG_DIR / "raw_samples.log"

DEPTH_LEVELS = 25
TRADES_MAX = 200
SELECT_TTL_SEC = 120.0
MAX_SELECTED = 3
SCAN_UNIVERSE = 1200             # v1.16.0: tüm BIST payları (BISTTÜM) taranır
# Adaptive scan pacing (server-paced): next symbol is requested only when fewer than
# SCAN_MAX_INFLIGHT depth answers are outstanding, never faster than SCAN_MIN_GAP.
SCAN_MIN_GAP = float(os.environ.get("IDEAL_SCAN_GAP") or 0.08)
STREAM_ALL = os.environ.get("IDEAL_STREAM_ALL", "1") != "0"   # v1.18.0: tüm paylar SRV_DRN akışına abone
STREAM_SCAN_GAP = float(os.environ.get("IDEAL_STREAM_SCAN_GAP") or 0.15)
SCAN_MAX_INFLIGHT = int(os.environ.get("IDEAL_SCAN_INFLIGHT") or 4)
SCAN_TIMEOUT_SEC = 6.0
AKD_MIN_GAP = float(os.environ.get("IDEAL_AKD_GAP") or 0.3)
AKD_MAX_INFLIGHT = int(os.environ.get("IDEAL_AKD_INFLIGHT") or 2)
AKD_TIMEOUT_SEC = 10.0
SEND_MIN_GAP = float(os.environ.get("IDEAL_SEND_GAP") or 0.035)  # client-side frame spacing guard
HOT_COUNT = 40                   # most liquid names get extra refreshes inside each cycle
HOT_EVERY = 4                    # every 4th scan slot goes to the hot ring
FRESH_QUOTE_FEED_SEC = 90.0      # feed must have produced a message within this window
FOOTPRINT_MAX_AGE_SEC = 20 * 60  # Y38 older than this is not used as "live"
LOGIN_TIMEOUT_SEC = 25.0
LOGIN_FAIL_BACKOFF_SEC = 300.0   # avoid hammering the account on bad credentials
RECONNECT_SEC = 3.0
# v1.35.0: İdealData sunucusu WS pong'larını geç/hiç göndermiyor (log: veri 2 sn önce gelirken
# "ping/pong timed out" → gereksiz kopma). İstemci ping kapalı; ölü oturumu uygulama içi
# sessizlik bekçisi (STALL_NOMSG_SEC) + TCP keepalive/USER_TIMEOUT yakalar.
PING_INTERVAL = float(os.environ.get("IDEAL_PING_INTERVAL") or 0)
PING_TIMEOUT = float(os.environ.get("IDEAL_PING_TIMEOUT") or 15)
# v1.27.2 stall guard. After hours the scanner still gets ~6 msg/s (max gap <1 s,
# measured Sun 04.10), so 180 s of silence while logged in means a dead session.
STALL_ERROR_SEC = float(os.environ.get("IDEAL_STALL_ERROR_SEC") or 20)     # state=error but run_forever not returned
STALL_NOMSG_SEC = float(os.environ.get("IDEAL_STALL_NOMSG_SEC") or 60)    # logged in, no message at all (v1.35.0: 180→60)
STALL_CONNECT_SEC = float(os.environ.get("IDEAL_STALL_CONNECT_SEC") or 120)  # connecting/logging_in hang
STALL_JOIN_SEC = float(os.environ.get("IDEAL_STALL_JOIN_SEC") or 30)       # teardown → new thread if still stuck
MANUAL_RECONNECT_GAP_SEC = 60.0   # İdealData rejects quick re-logins
GUARD_TICK_SEC = 2.0
# kernel-level backstop: a send that stays un-ACKed for 45 s (or a dead peer under
# keepalive) aborts the socket instead of blocking ~15 min in TCP retransmission.
_SOCKOPT = [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)]
for _n, _v in (("TCP_KEEPIDLE", 30), ("TCP_KEEPINTVL", 10), ("TCP_KEEPCNT", 3), ("TCP_USER_TIMEOUT", 45000)):
    if hasattr(socket, _n):
        _SOCKOPT.append((socket.IPPROTO_TCP, getattr(socket, _n), _v))
_SOCKOPT = tuple(_SOCKOPT)

# Numeric symbol codes used by Y26 (iDeal web app function aX) — only applied to pure digits.
SYMBOL_CODES = {"0":"EURUSD","1":"EURTRY","2":"USDTRY","3":"TRYJPY","4":"EURJPY","5":"EURCAD","6":"EURGBP","7":"EURCHF","8":"GBPUSD","9":"GBPJPY","10":"GBPEUR","11":"USDJPY","12":"DAX-A","13":"YM-A","14":"NQ-A","15":"ES-A","16":"VIP-X030","17":"VIP-USD","18":"VIP-EUR","19":"VIP-GLD","20":"GARAN","21":"HALKB","22":"ISCTR","23":"VAKBN","24":"THYAO","25":"EREGL","26":"AKBNK","27":"YKBNK","28":"KRDMD","29":"TCELL","30":"ENKAI","31":"BIMAS","32":"SAHOL","33":"PETKM","34":"OTKAR","35":"ASYAB","36":"PGSUS","37":"MGROS","38":"ARCLK","39":"KOZAA","40":"TTKOM","41":"EKGYO","42":"ASELS","43":"ULKER","44":"KCHOL","45":"TAVHL","46":"FENER","47":"NTTUR","48":"NTHOL","49":"TUPRS","50":"BIZIM"}

# Y26 field codes → (key, type). Confirmed by live comparison (2026-10-01):
# 0 last, 2 bid, 3 ask, J high, L low, P prev close, N tavan, O taban, K open (açılış),
# D VWAP (=F/H), F turnover TL, H volume lot, A last trade lot, B/C best bid/ask lot, Y HHMMSS.
Y26_FIELDS = {
    "0": ("last", "f"), "1": ("prev_close", "f"), "P": ("prev_close", "f"),
    "2": ("bid", "f"), "3": ("ask", "f"), "4": ("direction", "s"),
    "J": ("high", "f"), "L": ("low", "f"), "K": ("open", "f"),
    "N": ("ceiling", "f"), "O": ("floor", "f"),
    "D": ("vwap", "f"), "F": ("turnover", "f"), "H": ("volume", "f"),
    "A": ("last_qty", "f"), "B": ("bid_size", "f"), "C": ("ask_size", "f"),
    "Y": ("time", "s"), "M": ("m_raw", "f"), "T": ("t_raw", "f"),
    # v1.17.0: remaining codes kept raw (iDeal web: 8 tick, Q session state, R/S %, p/s, X, a..g)
    "8": ("tick", "f"), "Q": ("state", "s"), "R": ("r_raw", "s"), "S": ("s_raw", "s"),
    "V": ("v_raw", "s"), "X": ("x_raw", "s"), "a": ("a_raw", "s"), "b": ("b_raw", "s"),
    "c": ("c_raw", "s"), "d": ("d_raw", "s"), "f": ("f_raw", "s"), "p": ("p_raw", "s"),
    "s": ("s2_raw", "s"), "E": ("e_raw", "s"), "G": ("g_raw", "s"), "I": ("i_raw", "s"),
    "U": ("u_raw", "s"),
}


def _f(s: Any) -> float | None:
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        try:
            return float(s.replace(",", ""))
        except ValueError:
            return None


def _loose(s: Any) -> float | None:
    """'1,234,567' / '-535,549' / '289.9434' → float."""
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if all(len(p) == 3 for p in parts[1:]):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _hhmmss(s: str | None) -> str | None:
    if not s:
        return None
    s = s.strip()
    if ":" in s:
        return s
    if s.isdigit() and len(s) <= 6:
        s = s.zfill(6)
        return f"{s[0:2]}:{s[2:4]}:{s[4:6]}"
    return s


def _today() -> str:
    return datetime.now(IST).date().isoformat()


def _now_ist_str() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def _clean_sym(sym: str) -> str:
    s = (sym or "").strip().upper()
    if s.endswith(".IS"):
        s = s[:-3]
    if "'" in s:
        s = s.split("'", 1)[1]
    return s


def _session_open_now() -> bool:
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    hm = now.hour * 60 + now.minute
    return 9 * 60 + 40 <= hm <= 18 * 60 + 15


from app.live_store import trade_store  # noqa: E402


# v1.34.1 — uygulama içi İdealData hesabı (şifre dosyada 600 izinle; asla loglanmaz/dönmez)
CRED_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ideal_cred.json")


def _load_cred() -> dict:
    try:
        with open(CRED_FILE, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save_cred(user: str, password: str) -> None:
    os.makedirs(os.path.dirname(CRED_FILE), exist_ok=True)
    tmp = CRED_FILE + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"user": user, "password": password, "saved_at": time.time()}, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, CRED_FILE)


def cred_saved() -> bool:
    return bool(_load_cred().get("password"))



class IdealFeed:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._send_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._sched_thread: threading.Thread | None = None
        self._ws = None
        self._session: str | None = None
        self.user = os.environ.get("IDEAL_USER") or "ender99"
        _c = _load_cred()
        if _c.get("user"):
            self.user = _c["user"]
        self.universe_fn: Callable[[], list[str]] | None = None
        self.name_fn: Callable[[str], str | None] | None = None

        # status
        self.state = "init"          # init|connecting|logging_in|live|error|disabled
        self.connected = False
        self.logged_in = False
        self.error: str | None = None
        self.login_hint: str | None = None
        self.connected_at: float | None = None
        self.logged_in_at: float | None = None
        self.last_msg_time: float | None = None
        self.reconnects = 0
        # v1.27.2 stall guard
        self._gen = 0                       # run-loop generation; an abandoned loop exits
        self._wake = threading.Event()      # wakes the reconnect back-off early (manual)
        self._run_active = False            # run_forever() currently executing
        self._attempt_ts: float | None = None
        self._err_since: float | None = None
        self._teardown: dict | None = None  # {"ws","ts","reason","gen"} pending force-teardown
        self._unhealthy_since: float | None = None
        self._reconnecting_since: float | None = None
        self._manual_last = 0.0
        self._sched_beat = time.time()
        self._sched_gen = 0
        self.stalls = 0
        self.last_stall: dict | None = None
        self.stall_log: collections.deque = collections.deque(maxlen=20)
        self.licenses: list[str] = []
        self.msg_counts: collections.Counter = collections.Counter()
        self.sent_counts: collections.Counter = collections.Counter()
        self.drn_ops: collections.Counter = collections.Counter()
        self.parse_errors = 0
        self._open_ts: float | None = None
        self._last_sample_write = 0.0
        self._samples: dict[str, list[str]] = {}

        # stores
        self.quotes: dict[str, dict] = {}
        self.markets: dict[str, str] = {}
        self.names: dict[str, str] = {}
        self.sym_types: dict[str, str] = {}
        self.depth: dict[str, dict] = {}
        self.levels: dict[str, dict] = {}
        self.trades: dict[str, collections.deque] = {}
        self.trades_ts: dict[str, float] = {}
        self.limits: dict[str, dict] = {}
        self.akd: dict[str, dict] = {}
        self.news: collections.deque = collections.deque(maxlen=30)

        # subscriptions / scheduling
        self.selected: "collections.OrderedDict[str, float]" = collections.OrderedDict()
        self._pending: collections.deque = collections.deque()
        self._last_req: dict[tuple[str, str], float] = {}
        self._scan_list: list[str] = []
        self._scan_list_ts = 0.0
        self._scan_idx = 0
        self._akd_idx = 0
        self._scan_sym: str | None = None
        self._last_send = 0.0
        self.scan_cycles = 0
        self.scan_last_symbol: str | None = None
        # adaptive pacing / coverage stats
        self._inflight: dict[str, float] = {}
        self._akd_inflight: dict[str, list] = {}
        self._hot: list[str] = []
        self._hot_idx = 0
        self._slot = 0
        self._cycle_start: float | None = None
        self.last_cycle_sec: float | None = None
        self.akd_cycles = 0
        self._akd_cycle_start: float | None = None
        self.last_akd_cycle_sec: float | None = None
        self.scan_timeouts = 0
        self.akd_timeouts = 0
        self.hot_scans = 0
        self._lat_ema: float | None = None
        self._akd_lat_ema: float | None = None
        self._pace_scale = 1.0
        self._pace_ok_since = time.time()
        self.universe_source = "init"
        # one-shot request/response waiters (AKD ranges, takas …)
        self._waiters: list[dict] = []
        self._oneshot_cache: dict[tuple, tuple[float, Any]] = {}
        self.sub_extra: list[str] = []
        self.tick_counts: collections.Counter = collections.Counter()

    # ------------------------------------------------------------ lifecycle --
    def start(self, universe_fn=None, name_fn=None) -> None:
        if universe_fn:
            self.universe_fn = universe_fn
        if name_fn:
            self.name_fn = name_fn
        if self._thread and self._thread.is_alive():
            return
        if os.environ.get("IDEAL_DISABLED") == "1":
            self.state = "disabled"
            self.error = "IDEAL_DISABLED=1"
            return
        if websocket is None:
            self.state = "error"
            self.error = "websocket-client kütüphanesi yok"
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, args=(self._gen,), name="ideal-ws", daemon=True)
        self._thread.start()
        self._sched_thread = threading.Thread(target=self._scheduler_loop, args=(self._sched_gen,),
                                              name="ideal-sched", daemon=True)
        self._sched_thread.start()
        self._guard_thread = threading.Thread(target=self._guard_loop, name="ideal-guard", daemon=True)
        self._guard_thread.start()
        self._akdd()
        self._akdd_load(self._akd_date())
        self._akdd_thread = threading.Thread(target=self._akdd_loop, name="ideal-akd-day", daemon=True)
        self._akdd_thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        try:
            if self._ws:
                self._ws.close()
        except Exception:
            pass

    def _password(self) -> str | None:
        # v1.34.1: uygulamadan kaydedilen şifre (data/ideal_cred.json, 600) ortam değişkenine göre önceliklidir
        c = _load_cred()
        if c.get("password"):
            return c["password"]
        pw = os.environ.get("IDEAL_PASSWORD")
        return pw if pw else None

    def set_credentials(self, user: str, password: str) -> dict:
        """v1.34.1: kullanıcı adı/şifreyi kaydet ve hemen yeniden bağlan (şifre asla dönmez/loglanmaz)."""
        _save_cred(user, password)
        self.user = user
        self._manual_last = 0.0
        self.error = None
        if self._reconnecting_since is None:
            self._reconnecting_since = time.time()
        if self._run_active and self._ws is not None:
            self._stall("credentials", self._ws, detail="yeni kimlik bilgisi")
        self._wake.set()
        return {"ok": True, "user": user, "action": "reconnecting"}

    def _run_loop(self, gen: int = 0, first_wait: float = 0.0) -> None:
        fails = 0
        if first_wait > 0:
            self._backoff_wait(first_wait)
        while not self._stop.is_set() and gen == self._gen:
            pw = self._password()
            if not pw:
                self.state = "error"
                self.error = "IDEAL_PASSWORD ortam değişkeni tanımlı değil"
                self._stop.wait(60)
                continue
            self._session = str(uuid.uuid4())
            self.state = "connecting"
            self.connected = False
            self.logged_in = False
            self._open_ts = None
            self._attempt_ts = time.time()
            self._err_since = None
            try:
                ws = websocket.WebSocketApp(
                    WS_URL,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                self._ws = ws
                self._run_active = True
                ws.run_forever(ping_interval=PING_INTERVAL, ping_timeout=(PING_TIMEOUT if PING_INTERVAL else None), skip_utf8_validation=True,
                               sockopt=_SOCKOPT)
            except Exception as e:  # pragma: no cover
                self.error = f"Bağlantı hatası: {type(e).__name__}: {e}"[:300]
                logger.warning("ideal ws run_forever: %s", self.error)
            if gen != self._gen:
                # the stall guard abandoned this loop and already started a fresh one
                logger.warning("ideal: eski bağlantı döngüsü (gen %s) sonunda döndü; kapatılıyor", gen)
                return
            self._run_active = False
            self._teardown = None
            self.connected = False
            was_logged = self.logged_in
            self.logged_in = False
            try:
                trade_store.set_live(False, "bağlantı koptu")
            except Exception:
                pass
            if self._stop.is_set():
                break
            self.reconnects += 1
            if self.state == "login_failed":
                wait = LOGIN_FAIL_BACKOFF_SEC
            else:
                fails = 0 if was_logged else fails + 1
                wait = RECONNECT_SEC if fails < 6 else 30.0
                if self.state not in ("error",):
                    self.state = "connecting"
            if self.state != "login_failed" and self._reconnecting_since is None:
                self._reconnecting_since = time.time()
            logger.info("ideal ws closed; reconnect in %.0fs (state=%s)", wait, self.state)
            self._backoff_wait(wait)

    def _backoff_wait(self, wait: float) -> None:
        """Sleep before reconnecting; a manual reconnect may cut it short, but never
        sooner than MANUAL_RECONNECT_GAP_SEC after the previous attempt."""
        self._wake.clear()
        end = time.time() + wait
        while not self._stop.is_set():
            left = end - time.time()
            if left <= 0:
                return
            if self._wake.wait(min(left, 1.0)):
                self._wake.clear()
                floor = (self._attempt_ts or 0) + MANUAL_RECONNECT_GAP_SEC
                end = min(end, max(time.time(), floor))

    # -------------------------------------------------------------- ws hooks --
    def _on_open(self, ws) -> None:
        if ws is not self._ws:
            return
        self.connected = True
        self.connected_at = time.time()
        self._open_ts = time.time()
        self.state = "logging_in"
        self.error = None
        self.login_hint = None

        def _login():
            try:
                pw = self._password() or ""
                # NEVER log this frame
                self._raw_send(S1.join(["X", "REQ_CONNECT", self.user, pw, self._session, "WEB", "ANY"]), "REQ_CONNECT")
                del pw
                time.sleep(1.0)
                self._raw_send(S1.join(["X", "REQ_SDP_TOKEN", self.user, self._session]), "REQ_SDP_TOKEN")
                time.sleep(1.0)
                self._raw_send(S1.join(["X", "REQ_SEMBOLACIKLAMA", self.user, self._session]), "REQ_SEMBOLACIKLAMA")
                # login watchdog
                deadline = time.time() + LOGIN_TIMEOUT_SEC
                while time.time() < deadline and not self.logged_in and self.connected:
                    time.sleep(0.5)
                if self.connected and not self.logged_in:
                    self.state = "login_failed"
                    self.error = "Giriş doğrulanamadı (sunucu kotasyon/lisans göndermedi)" + (
                        f" — sunucu: {self.login_hint}" if self.login_hint else "")
                    logger.warning("ideal login failed: %s", self.error)
                    try:
                        ws.close()
                    except Exception:
                        pass
            except Exception as e:
                self.error = f"Giriş gönderilemedi: {e}"[:300]
        threading.Thread(target=_login, name="ideal-login", daemon=True).start()

    def _on_error(self, ws, err) -> None:
        if ws is not self._ws:
            return
        msg = f"{type(err).__name__}: {err}"[:300]
        pw = self._password()
        if pw and pw in msg:
            msg = msg.replace(pw, "***")
        self.error = msg
        if self.state != "login_failed":
            self.state = "error"
            if self._err_since is None:
                self._err_since = time.time()
        logger.warning("ideal ws error: %s", msg)
        # v1.27.2: on a timeout the library's teardown can block on a stuck send
        # (ping thread / scheduler) → shut the socket down now so it returns.
        if isinstance(err, (TimeoutError, socket.timeout)) or "timed out" in msg.lower() \
                or "Timeout" in type(err).__name__:
            self._stall("ping-timeout", ws, detail=msg)

    def _on_close(self, ws, code, reason) -> None:
        if ws is not self._ws:
            return
        self.connected = False
        # unexpected drop shortly after (re)login while scanning → slow the scan down
        if self.logged_in_at and time.time() - self.logged_in_at < 600 and not self._stop.is_set():
            self._pace_scale = min(4.0, self._pace_scale * 1.5)
            logger.warning("ideal: bağlantı koptu, tarama hızı düşürüldü (x%.2f)", self._pace_scale)
        self._pace_ok_since = time.time()
        self._inflight.clear()
        self._akd_inflight.clear()
        if self.state == "live":
            self.state = "connecting"
            self.error = f"Bağlantı kapandı ({code})"

    # ------------------------------------------------------- v1.27.2 guard --
    def _stall(self, reason: str, ws=None, detail: str | None = None) -> bool:
        """Record an incident and force-tear-down the current socket (non-blocking)."""
        ws = ws or self._ws
        now = time.time()
        if ws is None:
            return False
        td = self._teardown
        if td and td.get("ws") is ws:
            return False                      # already tearing this one down
        age = round(now - self.last_msg_time, 1) if self.last_msg_time else None
        self.stalls += 1
        self.last_stall = {"ts": now, "reason": reason, "detail": (detail or self.error or "")[:200],
                           "state": self.state, "last_msg_age_sec": age,
                           "recovered_at": None, "recovery_sec": None, "escalated": False}
        self.stall_log.append(self.last_stall)
        self._teardown = {"ws": ws, "ts": now, "reason": reason, "gen": self._gen}
        if self._reconnecting_since is None:
            self._reconnecting_since = now
        logger.warning("ideal STALL #%d: %s (state=%s, last_msg_age=%s s, err=%s) → bağlantı zorla kapatılıyor",
                       self.stalls, reason, self.state, age, (detail or self.error or "-")[:120])
        was_live = self.connected and self.logged_in
        self.connected = False                # scheduler stops sending into the dead socket
        self.logged_in = False
        if self.state not in ("login_failed",):
            self.state = "error" if reason != "manual" else "connecting"
            if not self.error or reason in ("no-msg", "manual"):
                self.error = {"no-msg": f"{int(age or 0)} sn mesaj yok — yeniden bağlanıyor",
                              "manual": "Elle yeniden bağlanma"}.get(reason, self.error)
        if was_live:
            try:
                trade_store.set_live(False, "bağlantı yenileniyor")
            except Exception:
                pass
        self._force_teardown(ws)
        return True

    def _force_teardown(self, ws) -> None:
        try:
            ws.keep_running = False
        except Exception:
            pass

        def _close():
            try:
                ws.close(timeout=2)
            except Exception:
                pass
        t = threading.Thread(target=_close, name="ideal-close", daemon=True)
        t.start()
        t.join(1.5)
        # close() blocks if another thread is stuck in send() under the ws lock →
        # shut the raw TCP socket down: wakes every blocked send/recv with an error.
        if t.is_alive() or self._run_active:
            raw = getattr(getattr(ws, "sock", None), "sock", None)
            if raw is not None:
                try:
                    socket.socket.shutdown(raw, socket.SHUT_RDWR)   # bypass SSLSocket wrapper
                except Exception:
                    pass

    def _guard_loop(self) -> None:
        while not self._stop.wait(GUARD_TICK_SEC):
            try:
                self._guard_tick()
            except Exception:
                logger.exception("ideal guard")

    def _guard_tick(self) -> None:
        now = time.time()
        if self.healthy():
            self._unhealthy_since = None
        elif self._unhealthy_since is None:
            self._unhealthy_since = now
        ws = self._ws
        td = self._teardown
        if td is not None:
            if td["ws"] is not self._ws or not self._run_active or td["gen"] != self._gen:
                self._teardown = None
            elif now - td["ts"] > STALL_JOIN_SEC:
                self._abandon(td)
            return
        if not self._run_active or ws is None:
            return
        if self.state == "error" and self._err_since and now - self._err_since > STALL_ERROR_SEC:
            self._stall("error-hang", ws)
        elif self.connected and self.logged_in and self.last_msg_time \
                and now - self.last_msg_time > STALL_NOMSG_SEC:
            self._stall("no-msg", ws)
        elif self.state in ("connecting", "logging_in") and self._attempt_ts \
                and now - self._attempt_ts > STALL_CONNECT_SEC:
            self._stall("connect-hang", ws)
        elif self.state == "login_failed" and self._attempt_ts \
                and now - self._attempt_ts > LOGIN_TIMEOUT_SEC + STALL_JOIN_SEC + 10:
            self._stall("close-hang", ws)
        # scheduler stuck (e.g. in a send that never returned) → fresh scheduler thread
        if now - self._sched_beat > 60 and self._sched_thread is not None:
            stuck = int(now - self._sched_beat)
            self._sched_gen += 1
            self._send_lock = threading.Lock()
            self._sched_beat = now
            logger.warning("ideal: zamanlayıcı %s sn takıldı → yeni zamanlayıcı (gen %d)", stuck, self._sched_gen)
            self._sched_thread = threading.Thread(target=self._scheduler_loop, args=(self._sched_gen,),
                                                  name="ideal-sched", daemon=True)
            self._sched_thread.start()

    def _abandon(self, td: dict) -> None:
        """run_forever() still hasn't returned STALL_JOIN_SEC after teardown: give up on
        that thread (its socket is already shut down, its callbacks are ignored) and
        start a fresh connection loop. Only one loop is ever current (self._gen)."""
        old = td["ws"]
        raw = getattr(getattr(old, "sock", None), "sock", None)
        if raw is not None:
            try:
                raw.close()
            except Exception:
                pass
        self._gen += 1
        self._ws = None
        self._run_active = False
        self._teardown = None
        self._send_lock = threading.Lock()    # a stuck sender may still hold the old one
        self.connected = False
        self.logged_in = False
        self.reconnects += 1
        if self.last_stall:
            self.last_stall["escalated"] = True
        wait = LOGIN_FAIL_BACKOFF_SEC if self.state == "login_failed" else RECONNECT_SEC
        logger.warning("ideal STALL: run_forever %d sn içinde dönmedi → yeni bağlantı döngüsü (gen %d, %.0f sn sonra)",
                       int(STALL_JOIN_SEC), self._gen, wait)
        self._thread = threading.Thread(target=self._run_loop, args=(self._gen, wait),
                                        name=f"ideal-ws-{self._gen}", daemon=True)
        self._thread.start()

    def request_reconnect(self, source: str = "manual") -> dict:
        """Manual wake-up (↻ button). Never touches a healthy feed; at most once per
        MANUAL_RECONNECT_GAP_SEC; never opens a second connection."""
        now = time.time()
        base = {"ok": True, "state": self.state, "healthy": self.healthy()}
        if self.state == "disabled" or self._stop.is_set():
            return {**base, "action": "none", "reason": "disabled"}
        if self.healthy():
            return {**base, "action": "none", "reason": "healthy"}
        if self._teardown is not None:
            return {**base, "action": "in_progress", "reason": "teardown"}
        if self._run_active and self.state in ("connecting", "logging_in") and self._attempt_ts \
                and now - self._attempt_ts < 45:
            return {**base, "action": "in_progress", "reason": "connecting"}
        gap = now - self._manual_last
        if gap < MANUAL_RECONNECT_GAP_SEC:
            return {**base, "action": "rate_limited", "retry_in": round(MANUAL_RECONNECT_GAP_SEC - gap)}
        self._manual_last = now
        if self._run_active and self._ws is not None:
            self._stall("manual", self._ws, detail=f"{source}: {self.state}")
            return {**base, "action": "reconnecting", "reason": "teardown"}
        # loop is sleeping in its back-off → wake it (floor: 60 s after last attempt)
        if self._reconnecting_since is None and self.state != "login_failed":
            self._reconnecting_since = now
        self._wake.set()
        floor = (self._attempt_ts or 0) + MANUAL_RECONNECT_GAP_SEC
        return {**base, "action": "reconnecting", "reason": "wake",
                "eta_sec": max(0, round(floor - now))}

    def _raw_send(self, frame: str, kind: str) -> bool:
        ws = self._ws
        if ws is None or not self.connected:
            return False
        with self._send_lock:
            gap = time.time() - self._last_send
            if gap < SEND_MIN_GAP:
                time.sleep(SEND_MIN_GAP - gap)
            try:
                ws.send(frame)
                self._last_send = time.time()
                self.sent_counts[kind] += 1
                return True
            except Exception as e:
                self.error = f"Gönderim hatası: {type(e).__name__}"
                return False

    def _send(self, *fields: str) -> bool:
        kind = fields[1] if len(fields) > 1 else "?"
        return self._raw_send(S1.join(fields), kind)

    # ------------------------------------------------------------- requests --
    @staticmethod
    def _full(sym: str) -> str:
        return "IMKBH'" + sym

    def _sub_list(self, extra: str | None = None) -> str:
        syms = list(self.selected.keys())
        if extra and extra not in syms:
            syms.append(extra)
        syms = syms[: MAX_SELECTED + 1]
        for x in self.sub_extra:
            if x not in syms:
                syms.append(x)
        return ";".join(self._full(s) for s in syms)

    def req_depth(self, sym: str, extra: str | None = None) -> None:
        s = self._full(sym)
        self._send("X", "REQ_DERINLIK", self.user, self._session or "", s, "0", "0", "0", self._sub_list(extra or sym))
        if STREAM_ALL and self.logged_in and len(self.sub_extra) >= 500 and not trade_store._live:
            try:
                trade_store.set_live(True, f"{len(self.sub_extra)} pay abone")
            except Exception:
                pass
        self._last_req[(sym, "drn")] = time.time()

    def req_levels(self, sym: str) -> None:
        self._send("X", "REQ_KDM2", self.user, self._full(sym), "G")
        self._last_req[(sym, "kdm")] = time.time()

    def req_akd(self, sym: str) -> None:
        d = self._akd_date()
        self._send("X", "REQ_DGLM_TAR2", sym, "TUM", "LISTE", d, d, self.user, self._session or "")
        self._send("X", "REQ_DGLM_TAR2", sym, "TOPLAM", "LISTE", d, d, self.user, self._session or "")
        self._last_req[(sym, "akd")] = time.time()

    @staticmethod
    def _akd_date() -> str:
        now = datetime.now(IST)
        d = now.date()
        # Before the session opens (or weekend) iDeal has no AKD for today → previous weekday
        from datetime import timedelta
        if now.weekday() >= 5 or (now.hour * 60 + now.minute) < 9 * 60 + 55:
            d = d - timedelta(days=1)
            while d.weekday() >= 5:
                d = d - timedelta(days=1)
        return d.strftime("%Y%m%d")

    def select(self, symbol: str) -> dict:
        sym = _clean_sym(symbol)
        if not sym:
            return {"ok": False}
        with self._lock:
            is_new = sym not in self.selected
            self.selected[sym] = time.time()
            self.selected.move_to_end(sym, last=False)
            while len(self.selected) > MAX_SELECTED:
                self.selected.popitem(last=True)
            if is_new:
                self._pending.append(sym)
        return {"ok": True, "symbol": sym, "new": is_new, "selected": list(self.selected.keys())}

    def touch(self, symbol: str) -> None:
        sym = _clean_sym(symbol)
        with self._lock:
            if sym in self.selected:
                self.selected[sym] = time.time()
            else:
                self.select(sym)

    def equity_universe(self) -> list[str]:
        """All BIST shares (BISTTÜM) from SRV_SEMBOLACIKLAMA: market IMKBH, type 1 (pay).

        Excludes warrants / V-suffixed codes, certificates (type 2), funds and indices."""
        with self._lock:
            out = []
            for s, m in self.markets.items():
                if m != "IMKBH" or self.sym_types.get(s) != "1":
                    continue
                if not s.isalnum() or not s[0].isalpha() or not (3 <= len(s) <= 6):
                    continue
                nm = (self.names.get(s) or "").upper()
                if s.endswith("V") and (len(s) >= 6 or "VARANT" in nm or "WARRANT" in nm):
                    continue
                if any(k in nm for k in ("VARANT", "SERTIFIKA", "SERTİFİKA", " FON", "FONU", "BYF")):
                    continue
                out.append(s)
            return out

    def _refresh_scan_list(self) -> None:
        now = time.time()
        # Only rebuild at a cycle boundary so that every share is visited exactly once per
        # cycle (the hot ring gives liquid names extra visits). Exception: upgrade from the
        # app fallback list as soon as the iDeal symbol list has arrived.
        if self._scan_list and self._scan_idx < len(self._scan_list):
            if not (self.universe_source == "app" and now - self._scan_list_ts > 15):
                return
        out = self.equity_universe()
        src = "idealdata"
        if len(out) < 100:  # symbol list not received yet → app universe fallback
            src = "app"
            try:
                if self.universe_fn:
                    out = [_clean_sym(x) for x in (self.universe_fn() or []) if x]
            except Exception as e:
                logger.debug("universe_fn: %s", e)
        with self._lock:
            turn = {x: (self.quotes.get(x) or {}).get("turnover") or 0 for x in out}
        # liquid first (turnover desc), then the rest alphabetically — every share once per cycle
        out = sorted(dict.fromkeys(out), key=lambda x: (-turn.get(x, 0), x))[:SCAN_UNIVERSE]
        if src == "idealdata" and self.universe_source == "app":
            self._scan_idx = 0  # restart the cycle on the full list
            self._cycle_start = None
        self._scan_list = out
        if STREAM_ALL and src == "idealdata":
            self.sub_extra = list(out)
        self._hot = [x for x in out if turn.get(x, 0) > 0][:HOT_COUNT]
        self.universe_source = src
        self._scan_list_ts = now

    def _next_scan_symbol(self, now: float) -> str | None:
        self._slot += 1
        if self._hot and self._slot % HOT_EVERY == 0:
            sym = self._hot[self._hot_idx % len(self._hot)]
            self._hot_idx += 1
            self.hot_scans += 1
            return sym
        if self._cycle_start is None:
            self._cycle_start = now
        if self._scan_idx >= len(self._scan_list):
            self._scan_idx = 0
            self.scan_cycles += 1
            self.last_cycle_sec = round(now - self._cycle_start, 1)
            self._cycle_start = now
            logger.info("ideal: tam tarama döngüsü %d hisse / %.0f sn", len(self._scan_list), self.last_cycle_sec)
        sym = self._scan_list[self._scan_idx]
        self._scan_idx += 1
        return sym

    def _ack(self, sym: str, now: float) -> None:
        t = self._inflight.pop(sym, None)
        if t is not None:
            lat = now - t
            self._lat_ema = lat if self._lat_ema is None else self._lat_ema * 0.9 + lat * 0.1

    def _akd_ack(self, sym: str, mode: str, now: float) -> None:
        ent = self._akd_inflight.get(sym)
        if not ent:
            return
        ent[1].discard(mode)
        if not ent[1]:
            self._akd_inflight.pop(sym, None)
            lat = now - ent[0]
            self._akd_lat_ema = lat if self._akd_lat_ema is None else self._akd_lat_ema * 0.9 + lat * 0.1

    def _scheduler_loop(self, sgen: int = 0) -> None:
        last_scan = 0.0
        last_akd_scan = 0.0
        while not self._stop.is_set() and sgen == self._sched_gen:
            time.sleep(0.03)
            self._sched_beat = time.time()
            if not (self.connected and self.logged_in):
                continue
            try:
                now = time.time()
                self._maybe_write_samples()
                # expire selections
                with self._lock:
                    for s, ts in list(self.selected.items()):
                        if now - ts > SELECT_TTL_SEC:
                            self.selected.pop(s, None)
                    pending = self._pending.popleft() if self._pending else None
                    selected = list(self.selected.keys())
                if pending:
                    self.req_depth(pending, extra=self._scan_sym)
                    self.req_levels(pending)
                    self.req_akd(pending)
                    continue
                open_ = _session_open_now()
                did = False
                for s in selected:
                    if now - self._last_req.get((s, "kdm"), 0) > (3.0 if open_ else 30.0):
                        self.req_levels(s)
                        did = True
                    if now - self._last_req.get((s, "akd"), 0) > (20.0 if open_ else 120.0):
                        self.req_akd(s)
                        did = True
                    if now - self._last_req.get((s, "drn"), 0) > (60.0 if open_ else 300.0):
                        self.req_depth(s, extra=self._scan_sym)
                        did = True
                if did:
                    continue
                # expire lost answers so a silent server never stalls the rotation
                for k, t in list(self._inflight.items()):
                    if now - t > SCAN_TIMEOUT_SEC:
                        self._inflight.pop(k, None)
                        self.scan_timeouts += 1
                for k, ent in list(self._akd_inflight.items()):
                    if now - ent[0] > AKD_TIMEOUT_SEC:
                        self._akd_inflight.pop(k, None)
                        self.akd_timeouts += 1
                if self._pace_scale > 1.0 and now - self._pace_ok_since > 600:
                    self._pace_scale = max(1.0, self._pace_scale / 1.25)
                    self._pace_ok_since = now
                scan_gap = ((STREAM_SCAN_GAP if self.sub_extra else SCAN_MIN_GAP) if open_ else 1.5) * self._pace_scale
                if now - last_scan >= scan_gap and len(self._inflight) < SCAN_MAX_INFLIGHT:
                    self._refresh_scan_list()
                    if self._scan_list:
                        sym = self._next_scan_symbol(now)
                        if sym and sym not in selected:
                            self._scan_sym = sym
                            self.scan_last_symbol = sym
                            self._inflight[sym] = now
                            self.req_depth(sym, extra=sym)
                            self.req_levels(sym)
                    last_scan = now
                akd_gap = (AKD_MIN_GAP if open_ else 6.0) * self._pace_scale
                if (now - last_akd_scan >= akd_gap and self._scan_list
                        and not getattr(self, "_akdd_running", False)      # v1.21.3: günlük AKD deposu döngüsü devrede
                        and len(self._akd_inflight) < AKD_MAX_INFLIGHT):
                    if self._akd_cycle_start is None:
                        self._akd_cycle_start = now
                    if self._akd_idx >= len(self._scan_list):
                        self._akd_idx = 0
                        self.akd_cycles += 1
                        self.last_akd_cycle_sec = round(now - self._akd_cycle_start, 1)
                        self._akd_cycle_start = now
                        logger.info("ideal: AKD döngüsü %d hisse / %.0f sn", len(self._scan_list), self.last_akd_cycle_sec)
                    sym = self._scan_list[self._akd_idx]
                    self._akd_idx += 1
                    if sym not in selected:
                        self._akd_inflight[sym] = [now, {"TUM", "TOPLAM"}]
                        self.req_akd(sym)
                    last_akd_scan = now
            except Exception as e:  # pragma: no cover
                logger.warning("ideal scheduler: %s", e)
                time.sleep(1)

    # -------------------------------------------------------------- parsing --
    def _redact(self, m: str) -> str:
        pw = self._password()
        if pw and pw in m:
            m = m.replace(pw, "<PW>")
        if self._session:
            m = m.replace(self._session, "<SES>")
        return m

    def _sample(self, typ: str, m: str) -> None:
        lst = self._samples.setdefault(typ, [])
        if len(lst) >= 3:
            return
        if typ == "SRV_SDP_TOKEN":
            m = m[:30] + "…<TOKEN GİZLENDİ>"
        lst.append(self._redact(m)[:1500].replace(S1, "<S1>").replace(S2, "<S2>"))

    def _maybe_write_samples(self) -> None:
        now = time.time()
        if now - self._last_sample_write < 30:
            return
        self._last_sample_write = now
        try:
            DEBUG_DIR.mkdir(parents=True, exist_ok=True)
            lines = [f"# İdealData ham örnekler — {_now_ist_str()} (şifre/oturum/token maskeli)",
                     f"# counts: {dict(self.msg_counts.most_common())}",
                     f"# drn_ops: {dict(self.drn_ops)}", ""]
            for t, lst in sorted(self._samples.items()):
                for s in lst:
                    lines.append(f"[{t}] {s}")
            SAMPLES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except Exception as e:
            logger.debug("samples write: %s", e)

    def _on_message(self, ws, data) -> None:
        if ws is not self._ws:
            return
        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8", "replace")
        now = time.time()
        self.last_msg_time = now
        for m in data.split(S3):
            if not m or not m.strip():
                continue
            m = m.strip("\r\n")
            parts = m.split(S1)
            if len(parts) < 2:
                continue
            typ = parts[1]
            self.msg_counts[typ] += 1
            if self.msg_counts[typ] <= 3:
                self._sample(typ, m)
            try:
                self._dispatch(typ, parts, now, m)
            except Exception as e:
                self.parse_errors += 1
                logger.debug("ideal parse %s: %s", typ, e)
            if self._waiters:
                self._notify_waiters(typ, parts)

    # ------------------------------------------------------- one-shot reqs --
    def _notify_waiters(self, typ: str, parts: list[str]) -> None:
        with self._lock:
            ws = list(self._waiters)
        for w in ws:
            try:
                if (w["typ"] == typ or (w["typ"] == "*" and typ not in ("SRV_DRN", "33", "38", "41", "26", "43"))) and w["match"](parts):
                    w["results"].append(parts)
                    if len(w["results"]) >= w["need"]:
                        w["event"].set()
            except Exception:
                pass

    def request_wait(self, frames: list[list[str]], typ: str, match, need: int = 1,
                     timeout: float = 8.0) -> list[list[str]] | None:
        """Send frames and wait for `need` messages of `typ` satisfying match(parts)."""
        if not (self.connected and self.logged_in):
            return None
        w = {"typ": typ, "match": match, "need": need, "results": [], "event": threading.Event()}
        with self._lock:
            self._waiters.append(w)
        try:
            for f in frames:
                self._send(*f)
            w["event"].wait(timeout)
            return w["results"] or None
        finally:
            with self._lock:
                if w in self._waiters:
                    self._waiters.remove(w)

    def probe(self, frames: list[list[str]], typ: str, contains: str | None = None,
              need: int = 1, timeout: float = 6.0) -> list[str]:
        """Debug: send raw frames ({U}=user, {S}=session) and return redacted replies of `typ`."""
        sub = self._sub_list("") if any("{L}" in x for f in frames for x in f) else ""
        fr = [[x.replace("{U}", self.user).replace("{S}", self._session or "").replace("{L}", sub) for x in f] for f in frames]

        def match(parts):
            return (not contains) or contains in S1.join(parts)
        res = self.request_wait(fr, typ, match, need=need, timeout=timeout) or []
        return [self._redact(S1.join(p)).replace(S1, "<S1>").replace(S2, "<S2>") for p in res]

    def _cached_oneshot(self, key: tuple, ttl: float, fn):
        hit = self._oneshot_cache.get(key)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
        val = fn()
        if val is not None:
            self._oneshot_cache[key] = (time.time(), val)
            if len(self._oneshot_cache) > 400:
                for k in sorted(self._oneshot_cache, key=lambda k: self._oneshot_cache[k][0])[:100]:
                    self._oneshot_cache.pop(k, None)
        return val

    @staticmethod
    def _akd_rows(parts: list[str]) -> list[dict]:
        rows = []
        for part in parts[7:]:
            c = part.split(S2)
            if len(c) < 2 or not c[0].strip():
                continue
            c += [""] * (4 - len(c))
            rows.append({"broker": c[0].strip(), "value": _loose(c[1]), "pct": _loose(c[2]), "cost": _loose(c[3])})
        return rows

    def akd_range(self, symbol: str, d1: str, d2: str, ttl: float = 20.0) -> dict | None:
        """AKD for an arbitrary date range (yyyymmdd..yyyymmdd) via REQ_DGLM_TAR2."""
        sym = _clean_sym(symbol)

        def _do():
            frames = [["X", "REQ_DGLM_TAR2", sym, mode, "LISTE", d1, d2, self.user, self._session or ""]
                      for mode in ("TUM", "TOPLAM")]
            got = {}

            want = f"{d1} - {d2}"

            def match(parts):
                return len(parts) > 6 and parts[4] == sym and parts[5].strip() == want
            res = self.request_wait(frames, "SRV_DGLM_TAR2", match, need=2, timeout=10.0) or []
            rng = None
            for parts in res:
                mode = "TUM" if parts[6].upper().startswith("TUM") else "TOPLAM"
                got[mode] = self._akd_rows(parts)
                rng = parts[5]
            if not got:
                return None
            return {"symbol": sym, "from": d1, "to": d2, "range": rng, "modes": sorted(got),
                    "TUM": got.get("TUM") or [], "TOPLAM": got.get("TOPLAM") or [], "ts": time.time()}
        return self._cached_oneshot(("akd", sym, d1, d2), ttl, _do)

    def takas(self, symbol: str, date: str, ttl: float = 600.0) -> dict | None:
        """MKK takas (custody) distribution per broker via REQ_TKS4 (needs MKK license)."""
        sym = _clean_sym(symbol)

        def _do():
            frames = [["X", "REQ_TKS4", self.user, self._full(sym), date]]
            res = self.request_wait(frames, "SRV_TKS4", lambda p: len(p) > 2 and p[2] in (sym, self._full(sym)),
                                    need=1, timeout=10.0)
            if not res:
                return None
            parts = res[-1]
            rows = []
            for part in parts[4:]:
                c = part.split(S2)
                if not c or not c[0].strip() or len(c) < 2:
                    continue
                rows.append({"broker": c[0].strip(), "lot": _loose(c[1]), "pct": _loose(c[2]) if len(c) > 2 else None})
            return {"symbol": sym, "date": date, "header": parts[3] if len(parts) > 3 else None,
                    "rows": rows, "ts": time.time()}
        return self._cached_oneshot(("tks4", sym, date), ttl, _do)

    def takas_change(self, symbol: str, d1: str, d2: str, ttl: float = 600.0) -> dict | None:
        """Takas change between two dates via REQ_TAKAS_FARK2."""
        sym = _clean_sym(symbol)

        def _do():
            frames = [["X", "REQ_TAKAS_FARK2", sym, d1, d2, self.user, self._session or ""]]
            res = self.request_wait(frames, "SRV_TAKAS_FARK2", lambda p: len(p) > 4 and p[4] in (sym, self._full(sym)),
                                    need=1, timeout=10.0)
            if not res:
                return None
            parts = res[-1]
            rows = []
            for part in parts[5:]:
                c = part.split(S2)
                if not c or not c[0].strip() or len(c) < 7:
                    continue
                # iDeal web (ary): n=c1 |değişim|, y=c2 değişim payı %, nL=c3 ilk tarih lot, ob=c4 ilk %,
                # pb=c5 son tarih lot, oy=c6 son %  (doğrulandı: c3 − c5 = c1)
                prev_lot, cur_lot = _loose(c[3]), _loose(c[5])
                chg = (cur_lot - prev_lot) if (cur_lot is not None and prev_lot is not None) else None
                rows.append({"broker": c[0].strip(), "lot": cur_lot, "pct": _loose(c[6]),
                             "prev_lot": prev_lot, "prev_pct": _loose(c[4]),
                             "change_lot": chg, "change_abs": _loose(c[1]), "change_share_pct": _loose(c[2])})
            return {"symbol": sym, "from": d1, "to": d2, "rows": rows, "ts": time.time()}
        return self._cached_oneshot(("tfark", sym, d1, d2), ttl, _do)

    def _mark_live(self) -> None:
        if not self.logged_in:
            self.logged_in = True
            self.logged_in_at = time.time()
            logger.info("İdealData giriş başarılı (canlı akış)")
        if self.state != "live":
            self.state = "live"
            self.error = None
        self._err_since = None
        if self._reconnecting_since is not None:
            took = time.time() - self._reconnecting_since
            self._reconnecting_since = None
            st = self.last_stall
            if st and st.get("recovered_at") is None:
                st["recovered_at"] = time.time()
                st["recovery_sec"] = round(st["recovered_at"] - st["ts"], 1)
                logger.warning("ideal: kesinti giderildi — %s sonrası %.1f sn içinde yeniden canlı",
                               st.get("reason"), st["recovery_sec"])
            else:
                logger.info("ideal: yeniden bağlandı (%.1f sn)", took)

    def _dispatch(self, typ: str, parts: list[str], now: float, raw: str) -> None:
        if typ == "26":
            if len(parts) > 3:
                self._mark_live()
                self._parse_y26(parts, now)
            return
        if typ == "35":
            self._mark_live()
            lic = set()
            for c in (parts[3] if len(parts) > 3 else "").split("|"):
                c = c.strip()
                if c.startswith("ML"):
                    lic.update(x for x in c[2:].split(";") if len(x) > 1)
                elif len(c) > 1:
                    lic.add(c)
            self.licenses = sorted(lic)
            return
        if typ == "43":
            self._mark_live()
            self._parse_y43(parts, now)
            return
        if typ == "SRV_SEMBOLACIKLAMA":
            self._parse_desc(parts)
            return
        if typ == "33":
            self._parse_depth(parts, now)
            return
        if typ == "SRV_DRN":
            self._parse_drn(parts, now)
            return
        if typ == "34":
            self._parse_trades(parts, now)
            return
        if typ == "38":
            self._parse_levels(parts, now)
            return
        if typ == "41":
            if len(parts) >= 8:
                sym = parts[2]
                with self._lock:
                    self.limits[sym] = {"ceiling": _f(parts[3]), "floor": _f(parts[4]), "vwap": _f(parts[5]),
                                        "high": _f(parts[6]), "low": _f(parts[7]), "ts": now}
            return
        if typ == "SRV_DGLM_TAR2":
            self._parse_akd(parts, now)
            return
        if typ == "28":
            if len(parts) > 3:
                f = parts[3].split(S2)
                if len(f) >= 4:
                    self.news.appendleft({"time": f[1], "title": f[3], "ts": now})
            return
        if not self.logged_in and typ not in ("SRV_SDP_TOKEN",):
            # possible login error text — keep a short, redacted hint
            txt = self._redact(S1.join(parts[1:]))
            txt = txt.replace(S1, " | ").replace(S2, " ; ")
            self.login_hint = txt[:200]

    def _parse_y26(self, parts: list[str], now: float) -> None:
        with self._lock:
            for rec in parts[3:]:
                if not rec:
                    continue
                f = rec.split(S2)
                sym = f[0].strip()
                if not sym:
                    continue
                if sym.isdigit():
                    sym = SYMBOL_CODES.get(sym, sym)
                q = self.quotes.get(sym)
                if q is None:
                    q = {}
                    self.quotes[sym] = q
                changed = False
                for tok in f[1:]:
                    if not tok or tok[:2] in ("PS", "SP"):
                        continue
                    spec = Y26_FIELDS.get(tok[0])
                    if not spec:
                        continue
                    val = tok[1:]
                    if val == "":
                        continue
                    key, typ = spec
                    if typ == "f":
                        v = _f(val)
                        if v is None:
                            continue
                        q[key] = v
                    else:
                        q[key] = val
                    if key == "last":
                        changed = True
                q["ts"] = now
                if changed:
                    q["last_ts"] = now

    def _parse_y43(self, parts: list[str], now: float) -> None:
        with self._lock:
            for rec in parts[2:]:
                f = rec.split(S2)
                if len(f) < 11 or not f[1]:
                    continue
                market, sym = f[0], f[1]
                self.markets[sym] = market
                q = self.quotes.setdefault(sym, {})
                for key, idx in (("last", 7), ("prev_close", 8), ("bid", 9), ("ask", 10)):
                    v = _f(f[idx])
                    if v is not None and key not in q:
                        q[key] = v
                q.setdefault("ts", now)

    def _parse_desc(self, parts: list[str]) -> None:
        blob = S2.join(parts[2:])
        with self._lock:
            for item in blob.split(S2):
                if not item or "=" not in item or "'" not in item:
                    continue
                market, _, rest = item.partition("'")
                bits = rest.split("=")
                sym = bits[0].strip()
                if not sym:
                    continue
                self.markets.setdefault(sym, market)
                if len(bits) >= 2 and bits[1]:
                    self.names[sym] = bits[1]
                if len(bits) >= 3:
                    self.sym_types[sym] = bits[-1]

    def _parse_depth(self, parts: list[str], now: float) -> None:
        if len(parts) < 4 or not parts[2]:
            return
        sym = parts[2]
        self._ack(sym, now)
        bids: dict[int, dict] = {}
        asks: dict[int, dict] = {}
        meta: dict[str, Any] = {}
        for part in parts[4:]:
            c = part.split(S2)
            if len(c) < 5 or c[0] not in ("B", "A"):
                continue
            try:
                lvl = int(c[1])
            except ValueError:
                continue
            row = {"price": _f(c[2]), "lot": _f(c[3]) or 0.0, "orders": int(_f(c[4]) or 0)}
            (bids if c[0] == "B" else asks)[lvl] = row
            if len(c) >= 8:
                side = "bid" if c[0] == "B" else "ask"
                meta[side + "_avg"] = _f(c[6])
                meta[side + "_total"] = _f(c[7])
        with self._lock:
            self.depth[sym] = {"bids": bids, "asks": asks, "ts": now, "snap_ts": now, "seq": parts[3], **meta}

    def _parse_drn(self, parts: list[str], now: float) -> None:
        sym = None
        with self._lock:
            for tok in "|".join(parts[2:]).split("|"):
                tok = tok.strip()
                if not tok:
                    continue
                if ";" not in tok:
                    sym = tok
                    continue
                c = tok.split(";")
                if sym is None:
                    continue
                op = c[0]
                self.drn_ops[op] += 1
                if op == "I" and len(c) >= 5:
                    c += [""] * (7 - len(c))
                    dq = self.trades.setdefault(sym, collections.deque(maxlen=TRADES_MAX))
                    rec = {"time": _hhmmss(c[1]), "price": _f(c[2]), "lot": _f(c[3]) or 0.0,
                           "side": "buy" if c[4] == "1" else "sell" if c[4] == "2" else "auction" if c[4] == "0" else c[4],
                           "buyer": c[5] or None, "seller": c[6] or None, "ts": now}
                    dq.append(rec)
                    try:
                        trade_store.add_stream(sym, rec)
                    except Exception as e:  # pragma: no cover
                        logger.debug("trade_store stream: %s", e)
                    self.trades_ts[sym] = now
                    self.tick_counts[sym] += 1
                elif op == "D" and len(c) >= 6:
                    d = self.depth.get(sym)
                    if d is None:
                        d = {"bids": {}, "asks": {}, "ts": now}
                        self.depth[sym] = d
                    try:
                        lvl = int(c[2])
                    except ValueError:
                        continue
                    book = d["bids"] if c[1] == "B" else d["asks"]
                    price = _f(c[3])
                    lot = _f(c[4]) or 0.0
                    if not price or lot <= 0:
                        book.pop(lvl, None)
                    else:
                        book[lvl] = {"price": price, "lot": lot, "orders": int(_f(c[5]) or 0)}
                    if len(c) >= 9:
                        side = "bid" if c[1] == "B" else "ask"
                        d[side + "_avg"] = _f(c[7])
                        d[side + "_total"] = _f(c[8])
                    d["ts"] = now

    def _parse_trades(self, parts: list[str], now: float) -> None:
        if len(parts) < 5 or not parts[2]:
            return
        sym = parts[2]
        rows = []
        for part in parts[5:]:
            c = part.split(S2)
            if len(c) < 3:
                continue
            c += [""] * (6 - len(c))
            rows.append({"time": _hhmmss(c[0]), "price": _f(c[1]), "lot": _f(c[2]) or 0.0,
                         "side": "buy" if c[3] == "1" else "sell" if c[3] == "2" else "auction" if c[3] == "0" else c[3],
                         "buyer": c[4] or None, "seller": c[5] or None, "ts": now})
        with self._lock:
            dq = collections.deque(rows[-TRADES_MAX:], maxlen=TRADES_MAX)
            self.trades[sym] = dq
            self.trades_ts[sym] = now
        try:
            trade_store.merge_snapshot(sym, rows)
        except Exception as e:  # pragma: no cover
            logger.debug("trade_store snapshot: %s", e)

    def _parse_levels(self, parts: list[str], now: float) -> None:
        if len(parts) < 3 or not parts[2]:
            return
        sym = parts[2]
        rows = []
        for part in parts[3:]:
            c = part.split(S2)
            if len(c) < 2:
                continue
            price = _f(c[0])
            lot = _f(c[1])
            if price is None or lot is None:
                continue
            c += [""] * (5 - len(c))
            rows.append({"price": price, "price_str": c[0], "lot": lot, "pct": _f(c[2]),
                         "buy_pct": _f(c[3]) or 0.0, "sell_pct": _f(c[4]) or 0.0})
        if not rows:
            return
        with self._lock:
            self.levels[sym] = {"rows": rows, "ts": now, "date": _today()}

    def _parse_akd(self, parts: list[str], now: float) -> None:
        if len(parts) < 7 or not parts[4]:
            return
        sym = parts[4]
        rng = parts[5]
        mode = "TUM" if parts[6].upper().startswith("TUM") else "TOPLAM"
        self._akd_ack(sym, mode, now)
        rows = []
        for part in parts[7:]:
            c = part.split(S2)
            if len(c) < 2 or not c[0].strip():
                continue
            c += [""] * (4 - len(c))
            rows.append({"broker": c[0].strip(), "value": _loose(c[1]), "pct": _loose(c[2]), "cost": _loose(c[3])})
        with self._lock:
            ent = self.akd.setdefault(sym, {})
            ent[mode] = {"rows": rows, "ts": now, "range": rng}

    # -------------------------------------------------------------- queries --
    def healthy(self) -> bool:
        return bool(self.logged_in and self.connected and self.last_msg_time
                    and time.time() - self.last_msg_time < FRESH_QUOTE_FEED_SEC)

    def status(self) -> dict:
        now = time.time()
        label = {
            "live": "Canlı", "connecting": "Bağlanıyor", "logging_in": "Giriş yapılıyor",
            "login_failed": "Hata", "error": "Hata", "init": "Başlatılıyor", "disabled": "Kapalı",
        }.get(self.state, self.state)
        with self._lock:
            n_q = len(self.quotes)
            n_stock_q = sum(1 for s in self.quotes if self.markets.get(s) == "IMKBH")
            n_depth = len(self.depth)
            n_levels = len(self.levels)
            n_akd = len(self.akd)
            n_trades = len(self.trades)
            selected = list(self.selected.keys())
        return {
            "state": self.state,
            "label": label,
            "connected": self.connected,
            "logged_in": self.logged_in,
            "healthy": self.healthy(),
            "user": self.user,
            "url": WS_URL,
            "error": self.error,
            "login_hint": self.login_hint,
            "connected_at": self.connected_at,
            "logged_in_at": self.logged_in_at,
            "last_msg_time": self.last_msg_time,
            "last_msg_age_sec": round(now - self.last_msg_time, 1) if self.last_msg_time else None,
            "reconnects": self.reconnects,
            "reconnecting": self._reconnecting_since is not None and self.state != "login_failed",
            "reconnecting_sec": round(now - self._reconnecting_since, 1) if self._reconnecting_since else None,
            "unhealthy_sec": round(now - self._unhealthy_since, 1) if self._unhealthy_since else None,
            "stalls": self.stalls,
            "last_stall": ({k: v for k, v in self.last_stall.items()} if self.last_stall else None),
            "stall_guard": {"error_sec": STALL_ERROR_SEC, "nomsg_sec": STALL_NOMSG_SEC,
                            "connect_sec": STALL_CONNECT_SEC, "join_sec": STALL_JOIN_SEC,
                            "run_active": self._run_active, "gen": self._gen,
                            "tearing_down": self._teardown is not None},
            "licenses": self.licenses,
            "msg_counts": dict(self.msg_counts.most_common()),
            "sent_counts": dict(self.sent_counts),
            "drn_ops": dict(self.drn_ops),
            "parse_errors": self.parse_errors,
            "stores": {"quotes": n_q, "stock_quotes": n_stock_q, "depth": n_depth, "levels": n_levels,
                       "akd": n_akd, "trades": n_trades},
            "selected": selected,
            "scan": {"universe": len(self._scan_list), "universe_source": self.universe_source,
                     "index": self._scan_idx, "cycles": self.scan_cycles,
                     "last_cycle_sec": self.last_cycle_sec,
                     "current_cycle_sec": round(now - self._cycle_start, 1) if self._cycle_start else None,
                     "est_cycle_sec": self._est_cycle(now),
                     "hot": len(self._hot), "hot_scans": self.hot_scans,
                     "inflight": len(self._inflight), "timeouts": self.scan_timeouts,
                     "latency_ms": round(self._lat_ema * 1000) if self._lat_ema else None,
                     "pace_scale": round(self._pace_scale, 2),
                     "akd_index": self._akd_idx, "akd_cycles": self.akd_cycles,
                     "last_akd_cycle_sec": self.last_akd_cycle_sec,
                     "akd_inflight": len(self._akd_inflight), "akd_timeouts": self.akd_timeouts,
                     "akd_latency_ms": round(self._akd_lat_ema * 1000) if self._akd_lat_ema else None,
                     "last_symbol": self.scan_last_symbol, "session_open": _session_open_now()},
            "symbol_types": self._type_counts(),
            "excluded_shares": self.excluded_shares()[:20],
            "password_set": bool(self._password()),
            "now": _now_ist_str(),
        }

    def _est_cycle(self, now: float) -> float | None:
        if not self._cycle_start or not self._scan_idx or not self._scan_list:
            return self.last_cycle_sec
        el = now - self._cycle_start
        return round(el / self._scan_idx * len(self._scan_list), 1) if self._scan_idx > 5 else None

    def excluded_shares(self) -> list[str]:
        with self._lock:
            t1 = [x for x, m in self.markets.items() if m == "IMKBH" and self.sym_types.get(x) == "1"]
        eq = set(self.equity_universe())
        return sorted(x for x in t1 if x not in eq)

    def _type_counts(self) -> dict:
        with self._lock:
            c = collections.Counter(self.sym_types.get(s, "?") for s, m in self.markets.items() if m == "IMKBH")
        return dict(c.most_common(8))

    def extra_quotes(self, have: set, name_map: dict | None = None,
                     prev_vol: dict | None = None, avg10: dict | None = None) -> list[dict]:
        """Live-only quote items (same schema as Yahoo items) for BIST shares Yahoo lacks."""
        if not self.healthy():
            return []
        out = []
        today = _today()
        for sym in self.equity_universe():
            if sym in have:
                continue
            with self._lock:
                q = dict(self.quotes.get(sym) or {})
            last = q.get("last")
            if not last:
                continue
            ykey = f"{sym}.IS"
            pv = (prev_vol or {}).get(ykey)
            a10 = (avg10 or {}).get(ykey)
            item = {
                "symbol": sym, "yahoo": ykey,
                "name": (name_map or {}).get(sym) or self.names.get(sym) or sym,
                "price": float(last), "previous_close": None, "change": None, "change_pct": None,
                "day_high": None, "day_low": None, "day_open": None, "volume": None,
                "prev_volume": int(pv) if pv else None, "avg10_volume": int(a10) if a10 else None,
                "avg_volume": None, "rvol": None, "rvol10": None, "currency": "TRY",
                "updated": f"{today} {_hhmmss(q.get('time')) or ''}".strip(),
                "session_date": today, "market_state": "REGULAR" if _session_open_now() else "CLOSED",
            }
            item = self.overlay_quote(item)
            item.pop("yahoo_price", None)
            item["live_only"] = True
            out.append(item)
        return out

    def live_quote(self, symbol: str) -> dict | None:
        if not self.healthy():
            return None
        sym = _clean_sym(symbol)
        with self._lock:
            q = self.quotes.get(sym)
            if not q or not q.get("last"):
                return None
            if self.markets.get(sym) not in (None, "IMKBH"):
                return None
            return dict(q)

    def overlay_quote(self, item: dict) -> dict:
        """Override delayed Yahoo quote fields with live iDeal values (if healthy)."""
        if not item:
            return item
        lq = self.live_quote(item.get("symbol") or "")
        if not lq:
            item.setdefault("price_source", "yahoo")
            return item
        last = lq.get("last")
        prev = lq.get("prev_close") or item.get("previous_close")
        item["yahoo_price"] = item.get("price")
        item["price"] = float(last)
        if prev:
            item["previous_close"] = float(prev)
            item["change"] = round(float(last) - float(prev), 6)
            item["change_pct"] = (float(last) - float(prev)) / float(prev) * 100.0
        if lq.get("high"):
            item["day_high"] = lq["high"]
        if lq.get("low"):
            item["day_low"] = lq["low"]
        if lq.get("open"):
            item["day_open"] = lq["open"]
        vol = lq.get("volume")
        if vol is not None and vol > 0:
            item["volume"] = int(vol)
            pv = item.get("prev_volume")
            if pv:
                item["rvol"] = round(float(vol) / float(pv), 3)
            a10 = item.get("avg10_volume")
            if a10:
                item["rvol10"] = round(float(vol) / float(a10), 3)
        for k in ("bid", "ask", "vwap", "turnover", "bid_size", "ask_size", "ceiling", "floor"):
            if lq.get(k) is not None:
                item["live_" + k] = lq[k]
        t = lq.get("time")
        if t and len(t) >= 6 and t.isdigit():
            item["updated"] = f"{_today()} {_hhmmss(t)}"
            item["session_date"] = _today()
        item["price_source"] = "idealdata"
        item["price_source_label"] = "İdealData canlı"
        return item

    # ---- derived per-symbol views
    def _depth_view(self, sym: str, n: int = DEPTH_LEVELS) -> dict | None:
        d = self.depth.get(sym)
        if not d:
            return None
        bids = [dict(level=k, **v) for k, v in sorted(d["bids"].items())][:n]
        asks = [dict(level=k, **v) for k, v in sorted(d["asks"].items())][:n]
        bid_lot = sum(r["lot"] for r in bids)
        ask_lot = sum(r["lot"] for r in asks)
        tot = bid_lot + ask_lot
        bb = bids[0]["price"] if bids else None
        ba = asks[0]["price"] if asks else None
        bt, at = d.get("bid_total"), d.get("ask_total")
        if (bt is not None or at is not None) and ((bt or 0) + (at or 0)) > 0:
            bt, at = (bt or 0), (at or 0)
            book_p = bt / (bt + at) * 100.0
        else:
            book_p = None
        return {
            "bids": bids, "asks": asks,
            "bid_lot": bid_lot, "ask_lot": ask_lot,
            "bid_orders": sum(r["orders"] for r in bids), "ask_orders": sum(r["orders"] for r in asks),
            "pressure_pct": round(bid_lot / tot * 100.0, 2) if tot > 0 else None,
            "best_bid": bb, "best_ask": ba,
            "spread": round(ba - bb, 6) if bb and ba else None,
            "book_bid_total": bt, "book_ask_total": at,
            "book_bid_avg": d.get("bid_avg"), "book_ask_avg": d.get("ask_avg"),
            "book_pressure_pct": round(book_p, 2) if book_p is not None else None,
            "ts": d.get("ts"), "age_sec": round(time.time() - d["ts"], 1) if d.get("ts") else None,
        }

    def _moneyflow(self, sym: str) -> dict | None:
        lv = self.levels.get(sym)
        if not lv:
            return None
        inflow = outflow = buy_lot = sell_lot = total_lot = 0.0
        for r in lv["rows"]:
            b = r["lot"] * r["buy_pct"] / 100.0
            s = r["lot"] * r["sell_pct"] / 100.0
            buy_lot += b
            sell_lot += s
            total_lot += r["lot"]
            inflow += b * r["price"]
            outflow += s * r["price"]
        bs = buy_lot + sell_lot
        return {
            "inflow_tl": round(inflow, 2), "outflow_tl": round(outflow, 2), "net_tl": round(inflow - outflow, 2),
            "buy_lot": int(round(buy_lot)), "sell_lot": int(round(sell_lot)),
            "net_lot": int(round(buy_lot - sell_lot)), "total_lot": int(round(total_lot)),
            "buy_dominance_pct": round(buy_lot / bs * 100.0, 2) if bs > 0 else None,
            "level_count": len(lv["rows"]), "date": lv.get("date"),
            "ts": lv["ts"], "age_sec": round(time.time() - lv["ts"], 1),
        }

    def footprint(self, symbol: str, max_age: float = FOOTPRINT_MAX_AGE_SEC) -> dict | None:
        """Real per-price buy/sell lots from Y38 (same level schema as analysis.compute_volume_profile)."""
        sym = _clean_sym(symbol)
        with self._lock:
            lv = self.levels.get(sym)
            if not lv or lv.get("date") != _today() or time.time() - lv["ts"] > max_age:
                return None
            rows = [dict(r) for r in lv["rows"]]
            ts = lv["ts"]
        if not rows:
            return None
        rows.sort(key=lambda r: r["price"], reverse=True)
        diffs = sorted({round(rows[i]["price"] - rows[i + 1]["price"], 6) for i in range(len(rows) - 1)
                        if rows[i]["price"] - rows[i + 1]["price"] > 0})
        tick = diffs[0] if diffs else 0.01
        dec = max((len(r["price_str"].split(".")[1]) if "." in r["price_str"] else 0) for r in rows)
        dec = max(dec, 2)
        levels = []
        for r in rows:
            b = int(round(r["lot"] * r["buy_pct"] / 100.0))
            s = int(round(r["lot"] * r["sell_pct"] / 100.0))
            levels.append({
                "tick_index": int(round(r["price"] / tick)) if tick else 0,
                "price": r["price"], "price_str": f"{r['price']:.{dec}f}",
                "times_tested": 0, "buy_volume": b, "sell_volume": s,
                "total_volume": int(round(r["lot"])), "net_volume": b - s,
                "buy_pct": r["buy_pct"], "sell_pct": r["sell_pct"], "pct": r["pct"],
            })
        return {"levels": levels, "tick": tick, "tick_decimals": dec, "ts": ts,
                "age_sec": round(time.time() - ts, 1)}

    @staticmethod
    def _akd_compose(tum: list, top: list, last: float | None) -> tuple[list, list]:
        by: dict[str, dict] = {}
        for r in tum:
            b = by.setdefault(r["broker"], {"broker": r["broker"]})
            b["net_lot"] = r["value"] or 0.0
            b["cost"] = r["cost"]
        for r in top:
            b = by.setdefault(r["broker"], {"broker": r["broker"]})
            b["total_lot"] = r["value"] or 0.0
            b["share_pct"] = r["pct"]
            if b.get("cost") in (None, 0):
                b["cost"] = r["cost"]
        rows = []
        for b in by.values():
            net = b.get("net_lot") or 0.0
            tot = b.get("total_lot")
            if tot is not None:
                b["buy_lot"] = max(0.0, (tot + net) / 2.0)
                b["sell_lot"] = max(0.0, (tot - net) / 2.0)
            cost = b.get("cost")
            if last and cost and net:
                b["pnl_tl"] = round(net * (last - cost), 2)
                b["pnl_pct"] = round((last - cost) / cost * 100.0 * (1 if net > 0 else -1), 2)
            b["net_tl"] = round(net * cost, 2) if cost else None
            rows.append(b)
        buyers = sorted([r for r in rows if (r.get("net_lot") or 0) > 0], key=lambda r: -r["net_lot"])
        sellers = sorted([r for r in rows if (r.get("net_lot") or 0) < 0], key=lambda r: r["net_lot"])
        sb = sum(r["net_lot"] for r in buyers) or 1.0
        ss = sum(-r["net_lot"] for r in sellers) or 1.0
        for r in buyers:
            r["pct"] = round(r["net_lot"] / sb * 100.0, 2)
        for r in sellers:
            r["pct"] = round(-r["net_lot"] / ss * 100.0, 2)
        return buyers, sellers

    # ------------------------------------------------ v1.21.3 günlük AKD deposu --
    def _akdd(self) -> dict:
        if not hasattr(self, "akd_day"):
            self.akd_day = {}                 # sym -> {"date","TUM","TOPLAM","range","ts","empty"}
            self._akdd_flock = threading.Lock()
            self._akdd_date_loaded = None
            self.akdd_complete_at = {}        # date -> epoch (ilk kez tüm hisseler tamamlandığında)
            self.akdd_fetches = 0
            self.akdd_fail = 0
            self._akdd_running = False
        return self.akd_day

    def _akdd_load(self, d: str) -> int:
        st = self._akdd()
        n = 0
        p = AKD_DAY_DIR / d
        if p.is_dir():
            for f in p.glob("*.json"):
                try:
                    e = json.loads(f.read_text())
                    if e.get("date") != d:
                        continue
                    sym = f.stem
                    with self._lock:
                        cur = st.get(sym)
                        if cur and cur.get("date") == d and (cur.get("ts") or 0) >= (e.get("ts") or 0):
                            continue
                        st[sym] = e
                        if not e.get("empty"):
                            ent = self.akd.setdefault(sym, {})
                            rg = e.get("range") or f"{d} - {d}"
                            for k in ("TUM", "TOPLAM"):
                                if (ent.get(k) or {}).get("ts", 0) < e["ts"]:
                                    ent[k] = {"rows": e.get(k) or [], "ts": e["ts"], "range": rg}
                    n += 1
                except Exception:
                    continue
        self._akdd_date_loaded = d
        self._bp_cache = None
        if n:
            logger.info("ideal: günlük AKD deposu yüklendi %s: %d hisse (diskten)", d, n)
        return n

    def _akdd_put(self, sym: str, raw: dict, d: str) -> dict:
        st = self._akdd()
        e = {"date": d, "TUM": raw.get("TUM") or [], "TOPLAM": raw.get("TOPLAM") or [],
             "range": raw.get("range") or f"{d} - {d}", "ts": raw.get("ts") or time.time()}
        e["empty"] = not (e["TUM"] or e["TOPLAM"])
        with self._lock:
            cur = st.get(sym)
            if cur and cur.get("date") == d and (cur.get("ts") or 0) > e["ts"]:
                return cur
            st[sym] = e
            if not e["empty"]:
                ent = self.akd.setdefault(sym, {})
                ent["TUM"] = {"rows": e["TUM"], "ts": e["ts"], "range": e["range"]}
                ent["TOPLAM"] = {"rows": e["TOPLAM"], "ts": e["ts"], "range": e["range"]}
            self._bp_cache = None
        try:
            p = AKD_DAY_DIR / d
            p.mkdir(parents=True, exist_ok=True)
            tmp = p / f".{sym}.tmp"
            tmp.write_text(json.dumps(e, ensure_ascii=False))
            os.replace(tmp, p / f"{sym}.json")
        except Exception as ex:
            logger.debug("akd day write %s: %s", sym, ex)
        return e

    def akd_day_get(self, sym: str) -> dict | None:
        e = self._akdd().get(_clean_sym(sym))
        return e if e and e.get("date") == self._akd_date() else None

    def akd_day_fetch(self, sym: str) -> dict | None:
        """Günlük AKD'yi AKD sekmesiyle aynı istekle (REQ_DGLM_TAR2 TUM+TOPLAM, gün=gün) çek ve depoya yaz."""
        sym = _clean_sym(sym)
        d = self._akd_date()
        raw = self.akd_range(sym, d, d, ttl=1.0)
        self.akdd_fetches += 1
        if not raw or len(raw.get("modes") or []) < 2:      # TUM + TOPLAM ikisi de gelmeli (eksik yanıt depoya yazılmaz)
            self.akdd_fail += 1
            return None
        return self._akdd_put(sym, raw, d)

    @staticmethod
    def _akdd_final_ts(d: str) -> float:
        """d günü için kapanış sonrası (18:12 TR) epoch; bundan sonra alınan AKD kesindir."""
        dt = datetime.strptime(d, "%Y%m%d").replace(hour=18, minute=12, tzinfo=IST)
        return dt.timestamp()

    def _akdd_stale(self, e: dict | None, now: float, d: str) -> bool:
        if not e or e.get("date") != d:
            return True
        age = now - (e.get("ts") or 0)
        if e.get("empty"):
            return age > 600
        fin = self._akdd_final_ts(d)
        if (e.get("ts") or 0) >= fin:
            return False                       # kapanış sonrası alınmış → kesin, yenileme yok
        if now >= fin:
            return True                        # seans bitti, kesin veri bir kez daha çekilir
        return age > AKDD_SESSION_AGE          # seans içi ~3–4 dk döngü

    def akd_day_status(self) -> dict:
        st = self._akdd()
        d = self._akd_date()
        uni = self.equity_universe()
        have = sum(1 for s in uni if (st.get(s) or {}).get("date") == d and not st[s].get("empty"))
        checked = sum(1 for s in uni if (st.get(s) or {}).get("date") == d)
        ages = [time.time() - st[s]["ts"] for s in uni if (st.get(s) or {}).get("date") == d and not st[s].get("empty")]
        ca = self.akdd_complete_at.get(d)
        return {"date": d, "have": have, "checked": checked, "total": len(uni), "complete": bool(uni) and checked >= len(uni),
                "complete_at": datetime.fromtimestamp(ca, IST).strftime("%Y-%m-%d %H:%M:%S") if ca else None,
                "oldest_age_sec": round(max(ages)) if ages else None, "fetches": self.akdd_fetches, "fails": self.akdd_fail}

    def akd_day_complete(self) -> bool:
        try:
            return self.akd_day_status()["complete"]
        except Exception:
            return True

    def _akdd_loop(self) -> None:
        self._akdd()
        self._akdd_running = True
        gap = AKDD_GAP_CLOSED
        while not self._stop.is_set():
            try:
                if not (self.connected and self.logged_in):
                    time.sleep(2); continue
                uni = self.equity_universe()
                if len(uni) < 100:
                    time.sleep(2); continue
                d = self._akd_date()
                if self._akdd_date_loaded != d:
                    self._akdd_load(d)
                now = time.time()
                st = self.akd_day
                with self._lock:
                    tv = {s: ((self.quotes.get(s) or {}).get("turnover") or 0) for s in uni}
                order = sorted(uni, key=lambda s: -tv[s])
                todo = [s for s in order if self._akdd_stale(st.get(s), now, d)]
                if not todo:
                    if d not in self.akdd_complete_at:
                        self.akdd_complete_at[d] = now
                        logger.info("ideal: günlük AKD deposu TAMAM %s: %d hisse", d, len(uni))
                    time.sleep(3); continue
                base = AKDD_GAP_OPEN if _session_open_now() else AKDD_GAP_CLOSED
                gap = max(gap, base)
                for s in todo[:40]:
                    if self._stop.is_set() or self._akd_date() != d:
                        break
                    e = self.akd_day_fetch(s)
                    fc = getattr(self, "_akdd_failc", None)
                    if fc is None:
                        fc = self._akdd_failc = collections.Counter()
                    if e is None:
                        fc[s] += 1
                        if fc[s] >= 2:
                            # iki kez yanıtsız/eksik → bugün işlem yok say (boş kayıt, 10 dk sonra tekrar denenir)
                            self._akdd_put(s, {"TUM": [], "TOPLAM": [], "ts": time.time()}, d)
                            fc[s] = 0
                        gap = min(3.0, gap * 1.5 + 0.1)       # İdealData yavaşladı/cevap yok → nazikçe yavaşla
                    else:
                        fc[s] = 0
                        gap = max(base, gap / 1.3)
                    time.sleep(gap)
            except Exception as ex:  # pragma: no cover
                logger.warning("ideal akd-day: %s", ex)
                time.sleep(3)

    def akd_view(self, symbol: str, d1: str, d2: str) -> dict | None:
        sym0 = _clean_sym(symbol)
        raw = None
        if d1 == d2 == self._akd_date():
            # v1.21.3: Günlük = ortak depo (Kurum Analizi / Tahtacı / rapor ile birebir aynı anlık görüntü)
            e = self.akd_day_get(sym0)
            now = time.time()
            fresh = e is not None and not e.get("empty") and (
                not self._akdd_stale(e, now, d1) and (not _session_open_now() or now - e["ts"] < 20))
            if not fresh:
                e2 = self.akd_day_fetch(sym0)
                e = e2 or e
            if e is not None:
                raw = {"symbol": sym0, "range": e.get("range"), "TUM": e.get("TUM") or [], "TOPLAM": e.get("TOPLAM") or [],
                       "ts": e.get("ts")}
        else:
            raw = self.akd_range(symbol, d1, d2)
        if not raw:
            return None
        sym = raw["symbol"]
        with self._lock:
            last = (self.quotes.get(sym) or {}).get("last")
        buyers, sellers = self._akd_compose(raw["TUM"], raw["TOPLAM"], last)
        total_rows = sorted(buyers + sellers, key=lambda r: -(r.get("total_lot") or 0))
        tot_all = sum(r.get("total_lot") or 0 for r in total_rows) or 0
        return {"symbol": sym, "from": d1, "to": d2, "range": raw.get("range"), "last": last,
                "buyers": buyers, "sellers": sellers, "total": total_rows,
                "total_lot_sum": tot_all, "ts": raw["ts"], "age_sec": round(time.time() - raw["ts"], 1),
                "source": "idealdata_akd", "source_label": "İdealData AKD"}

    def _brokers(self, sym: str, last: float | None) -> dict:
        ent = self.akd.get(sym) or {}
        tum = (ent.get("TUM") or {}).get("rows") or []
        top = (ent.get("TOPLAM") or {}).get("rows") or []
        if tum or top:
            buyers, sellers = self._akd_compose(tum, top, last)
            ts = max((ent.get(k) or {}).get("ts") or 0 for k in ("TUM", "TOPLAM"))
            rng = (ent.get("TUM") or ent.get("TOPLAM") or {}).get("range")
            return {"source": "idealdata_akd", "source_label": "İdealData AKD", "range": rng,
                    "buyers": buyers, "sellers": sellers, "ts": ts,
                    "age_sec": round(time.time() - ts, 1) if ts else None}
        # fallback: aggregate the trades tape
        dq = self.trades.get(sym) or []
        agg: dict[str, dict] = {}
        for t in dq:
            lot = t.get("lot") or 0.0
            px = t.get("price") or 0.0
            if t.get("buyer"):
                a = agg.setdefault(t["buyer"], {"broker": t["buyer"], "buy_lot": 0.0, "sell_lot": 0.0, "buy_tl": 0.0, "sell_tl": 0.0})
                a["buy_lot"] += lot
                a["buy_tl"] += lot * px
            if t.get("seller"):
                a = agg.setdefault(t["seller"], {"broker": t["seller"], "buy_lot": 0.0, "sell_lot": 0.0, "buy_tl": 0.0, "sell_tl": 0.0})
                a["sell_lot"] += lot
                a["sell_tl"] += lot * px
        rows = []
        for a in agg.values():
            net = a["buy_lot"] - a["sell_lot"]
            a["net_lot"] = net
            a["total_lot"] = a["buy_lot"] + a["sell_lot"]
            if net > 0 and a["buy_lot"]:
                a["cost"] = round(a["buy_tl"] / a["buy_lot"], 4)
            elif net < 0 and a["sell_lot"]:
                a["cost"] = round(a["sell_tl"] / a["sell_lot"], 4)
            rows.append(a)
        buyers = sorted([r for r in rows if r["net_lot"] > 0], key=lambda r: -r["net_lot"])
        sellers = sorted([r for r in rows if r["net_lot"] < 0], key=lambda r: r["net_lot"])
        sb = sum(r["net_lot"] for r in buyers) or 1.0
        ss = sum(-r["net_lot"] for r in sellers) or 1.0
        for r in buyers:
            r["pct"] = round(r["net_lot"] / sb * 100.0, 2)
        for r in sellers:
            r["pct"] = round(-r["net_lot"] / ss * 100.0, 2)
        return {"source": "trades_tape", "source_label": f"Son {len(dq)} işlemden (tahmini)",
                "buyers": buyers, "sellers": sellers, "ts": self.trades_ts.get(sym)}

    def _name(self, sym: str) -> str | None:
        n = None
        if self.name_fn:
            try:
                n = self.name_fn(sym)
            except Exception:
                n = None
        return n or self.names.get(sym)

    def _quote_brief(self, sym: str) -> dict:
        q = self.quotes.get(sym) or {}
        last, prev = q.get("last"), q.get("prev_close")
        chg = (last - prev) / prev * 100.0 if last and prev else None
        return {"price": last, "previous_close": prev, "change_pct": round(chg, 3) if chg is not None else None,
                "volume": q.get("volume"), "turnover": q.get("turnover"), "high": q.get("high"), "low": q.get("low"),
                "open": q.get("open"), "bid": q.get("bid"), "ask": q.get("ask"), "vwap": q.get("vwap"),
                "bid_size": q.get("bid_size"), "ask_size": q.get("ask_size"), "ceiling": q.get("ceiling"),
                "floor": q.get("floor"), "time": _hhmmss(q.get("time")) if q.get("time") else None,
                "ts": q.get("ts"), "state": q.get("state"), "tick": q.get("tick"),
                "raw": {k: q.get(k) for k in ("r_raw", "s_raw", "p_raw", "s2_raw", "x_raw", "v_raw", "a_raw",
                                              "b_raw", "c_raw", "d_raw", "f_raw", "e_raw", "g_raw", "i_raw",
                                              "u_raw", "m_raw", "t_raw") if q.get(k) not in (None, "")}}

    def symbol_view(self, symbol: str, trades_limit: int = 100) -> dict:
        sym = _clean_sym(symbol)
        with self._lock:
            quote = self._quote_brief(sym) if sym in self.quotes else None
            depth = self._depth_view(sym)
            mf = self._moneyflow(sym)
            dq = list(self.trades.get(sym) or [])
            last = (quote or {}).get("price")
            brokers = self._brokers(sym, last)
            limits = dict(self.limits.get(sym) or {}) or None
        trades = list(reversed(dq))[:max(1, min(trades_limit, TRADES_MAX))]
        tb = sum(t["lot"] for t in dq if t.get("side") == "buy")
        ts_ = sum(t["lot"] for t in dq if t.get("side") == "sell")
        fp = self.footprint(sym)
        summary = None
        if quote or depth or mf:
            summary = {
                "price": (quote or {}).get("price"), "change_pct": (quote or {}).get("change_pct"),
                "best_bid": (depth or {}).get("best_bid") or (quote or {}).get("bid"),
                "best_ask": (depth or {}).get("best_ask") or (quote or {}).get("ask"),
                "pressure_pct": (depth or {}).get("pressure_pct"),
                "net_money_tl": (mf or {}).get("net_tl"),
                "tape_buy_lot": tb, "tape_sell_lot": ts_,
                "tape_buy_pct": round(tb / (tb + ts_) * 100.0, 2) if (tb + ts_) > 0 else None,
            }
        return {
            "symbol": sym,
            "name": self._name(sym),
            "feed": {"state": self.state, "healthy": self.healthy(), "error": self.error},
            "selected": sym in self.selected,
            "quote": quote,
            "limits": limits,
            "summary": summary,
            "depth": depth,
            "trades": trades,
            "trades_count": len(dq),
            "brokers": brokers,
            "money_flow": mf,
            "footprint": fp,
            "has_data": bool(quote or depth or mf or dq),
            "source_label": "İdealData canlı",
            "updated": _now_ist_str(),
        }

    def pressure_ranking(self, max_age: float = 15 * 60) -> list[dict]:
        out = []
        now = time.time()
        with self._lock:
            for sym, d in self.depth.items():
                if not d.get("ts") or now - d["ts"] > max_age:
                    continue
                v = self._depth_view(sym)
                if not v:
                    continue
                qb = self._quote_brief(sym)
                out.append({
                    "symbol": sym, "name": self._name(sym), "price": qb["price"], "change_pct": qb["change_pct"],
                    "volume": qb["volume"], "bid_lot": v["bid_lot"], "ask_lot": v["ask_lot"],
                    "pressure_pct": v["pressure_pct"], "imbalance_lot": v["bid_lot"] - v["ask_lot"],
                    "book_bid_total": v["book_bid_total"], "book_ask_total": v["book_ask_total"],
                    "book_pressure_pct": v["book_pressure_pct"], "best_bid": v["best_bid"],
                    "best_ask": v["best_ask"], "spread": v["spread"], "age_sec": v["age_sec"],
                    "book_state": "live" if v["pressure_pct"] is not None else "empty",
                    "book_note": None if v["pressure_pct"] is not None else "Tek fiyat / boş defter",
                })
        return out

    def moneyflow_ranking(self) -> list[dict]:
        out = []
        today = _today()
        with self._lock:
            for sym, lv in self.levels.items():
                if lv.get("date") != today:
                    continue
                mf = self._moneyflow(sym)
                if not mf:
                    continue
                qb = self._quote_brief(sym)
                out.append({"symbol": sym, "name": self._name(sym), "price": qb["price"],
                            "change_pct": qb["change_pct"], "volume": qb["volume"],
                            "turnover": qb["turnover"], **mf})
        return out

    def institutions(self) -> list[dict]:
        agg: dict[str, dict] = {}
        with self._lock:
            for sym, ent in self.akd.items():
                tum = (ent.get("TUM") or {}).get("rows") or []
                if not tum:
                    continue
                last = (self.quotes.get(sym) or {}).get("last")
                for r in tum:
                    net = r.get("value") or 0.0
                    cost = r.get("cost")
                    if not net:
                        continue
                    a = agg.setdefault(r["broker"], {"broker": r["broker"], "symbols": 0, "buy_symbols": 0,
                                                     "sell_symbols": 0, "net_tl": 0.0, "buy_tl": 0.0,
                                                     "sell_tl": 0.0, "pnl_tl": 0.0, "_buys": [], "_sells": []})
                    a["symbols"] += 1
                    val = net * cost if cost else 0.0
                    a["net_tl"] += val
                    pnl = net * (last - cost) if (last and cost) else 0.0
                    a["pnl_tl"] += pnl
                    item = {"symbol": sym, "net_lot": net, "cost": cost, "last": last,
                            "net_tl": round(val, 2), "pnl_tl": round(pnl, 2)}
                    if net > 0:
                        a["buy_symbols"] += 1
                        a["buy_tl"] += val
                        a["_buys"].append(item)
                    else:
                        a["sell_symbols"] += 1
                        a["sell_tl"] += -val
                        a["_sells"].append(item)
        out = []
        for a in agg.values():
            buys = sorted(a.pop("_buys"), key=lambda x: -x["net_tl"])
            sells = sorted(a.pop("_sells"), key=lambda x: x["net_tl"])
            a["top_buys"] = buys[:5]
            a["top_sells"] = sells[:5]
            a["top_buy"] = buys[0]["symbol"] if buys else None
            a["top_sell"] = sells[0]["symbol"] if sells else None
            gross = a["buy_tl"] + a["sell_tl"]
            a["pnl_pct"] = round(a["pnl_tl"] / gross * 100.0, 3) if gross else None
            for k in ("net_tl", "buy_tl", "sell_tl", "pnl_tl"):
                a[k] = round(a[k], 2)
            out.append(a)
        return out

    # ------------------------------------------------------------ v1.18.0 --
    def movers(self) -> list[dict]:
        """All shares from live İdealData quotes (Yükselenler/Düşenler & Hacimliler)."""
        uni = self.equity_universe()
        out = []
        with self._lock:
            for sym in uni:
                q = self.quotes.get(sym)
                if not q:
                    continue
                last, prev = q.get("last"), q.get("prev_close")
                if not last or not prev:
                    continue
                out.append({"s": sym, "n": self._name(sym), "p": last, "c": round((last - prev) / prev * 100.0, 3),
                            "t": q.get("turnover") or 0.0, "v": q.get("volume") or 0.0,
                            "ce": q.get("ceiling"), "fl": q.get("floor")})
        return out

    def depth_pressure(self) -> list[dict]:
        out = []
        uni = set(self.equity_universe())
        now = time.time()
        with self._lock:
            for sym in uni:
                d = self.depth.get(sym)
                if not d:
                    continue
                v = self._depth_view(sym, 25)
                if not v:
                    continue
                qb = self._quote_brief(sym)
                bt, at = v.get("book_bid_total"), v.get("book_ask_total")
                out.append({
                    "s": sym, "p": qb["price"], "c": qb["change_pct"], "t": qb["turnover"],
                    "b25": v["bid_lot"], "a25": v["ask_lot"], "p25": v["pressure_pct"],
                    "lv_b": len(v["bids"]), "lv_a": len(v["asks"]),
                    "ball": bt, "aall": at, "pall": v["book_pressure_pct"],
                    "bavg": v.get("book_bid_avg"), "aavg": v.get("book_ask_avg"),
                    "age": round(now - d["ts"], 1) if d.get("ts") else None,
                })
        return out

    def broker_positions(self, ttl: float = 5.0) -> dict:
        """Every broker × every stock: buy/sell lot & share, net, cost, live K/Z.
        v1.21.3: YALNIZCA günlük AKD deposu (AKD sekmesi Günlük ile aynı kayıt); işlem kaydı (*) yedeği kaldırıldı."""
        hit = getattr(self, "_bp_cache", None)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
        today = self._akd_date()
        uni = self.equity_universe()
        rows: list[dict] = []
        src_akd = src_tick = 0
        with self._lock:
            akdd = dict(self._akdd())
            quotes = {s: (self.quotes.get(s) or {}) for s in uni}
        for sym in uni:
            q = quotes.get(sym) or {}
            last = q.get("last")
            ent = akdd.get(sym)
            items = []
            source = None
            if ent and ent.get("date") == today and not ent.get("empty"):
                # v1.21.3: yalnızca günlük AKD deposu (AKD sekmesi Günlük ile aynı sonuç); işlem kaydı yedeği YOK
                buyers, sellers = self._akd_compose(ent.get("TUM") or [], ent.get("TOPLAM") or [], last)
                for r in buyers + sellers:
                    net = r.get("net_lot") or 0.0
                    bl = r.get("buy_lot")
                    sl = r.get("sell_lot")
                    if bl is None:
                        bl = max(net, 0.0)
                    if sl is None:
                        sl = max(-net, 0.0)
                    items.append((r["broker"], bl, sl, net, r.get("cost"), r.get("pct")))
                source = "akd"
                src_akd += 1
            if not items:
                continue
            vol = sum(i[1] for i in items) or (q.get("volume") or 0.0)
            svol = sum(i[2] for i in items) or vol
            # v1.21.2: ALIŞ % / SATIŞ % = AKD sekmesindeki ALICILAR / SATICILAR DAĞILIM % ile birebir aynı tanım:
            # net alıcının net lotu / tüm net alıcıların net lot toplamı (satıcılar için simetrik). Tick yedeği (*) de aynı formül.
            tsum = sum(i[1] + i[2] for i in items) or 1.0
            for b, bl, sl, net, cost, dpct in items:
                pnl = pnl_pct = None
                if last and cost and net:
                    pnl = round(net * (last - cost), 2)
                    pnl_pct = round((last - cost) / cost * 100.0 * (1 if net > 0 else -1), 2)
                # v1.21.3: ALIŞ % / SATIŞ % = _akd_compose 'pct' (AKD sekmesi ALICILAR / SATICILAR DAĞILIM %) — aynı fonksiyon, aynı değer
                bp = dpct if net > 0 else None
                sp = dpct if net < 0 else None
                rows.append({"b": b, "s": sym, "bl": round(bl), "bp": bp,
                             "sl": round(sl), "sp": sp, "np": bp if bp is not None else (-sp if sp is not None else 0.0),
                             "bgp": round(bl / vol * 100.0, 2) if vol else None, "sgp": round(sl / svol * 100.0, 2) if svol else None,
                             "tp": round((bl + sl) / tsum * 100.0, 2),
                             "nl": round(net), "co": round(cost, 4) if cost else None, "p": last,
                             "kz": pnl, "kzp": pnl_pct, "src": source, "at": round(ent["ts"], 1)})
        res = {"rows": rows, "stocks_akd": src_akd, "stocks_tick": src_tick, "ts": time.time(), "akd_date": today,
               "akd_status": self.akd_day_status()}
        self._bp_cache = (time.time(), res)
        return res

    def akd_coverage(self) -> int:
        with self._lock:
            return sum(1 for e in self.akd.values() if (e.get("TUM") or {}).get("rows"))


ideal_feed = IdealFeed()
