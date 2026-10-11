"""v1.22.0 — KADEME & ŞERİT ANALİZİ + İşlem Analizi (Tüm Hisseler) + Kurum Fiyat Analizi.

Tüm BIST payları (635) için arka planda artımlı hesaplanan 20 tarayıcı:
  * İşlem kaydı (TradeStore) satır satır bir kez işlenir → hisse başına fiyat/lot/kurum/dakika özetleri.
  * Derinlik (25 kademe) her ~2 sn örneklenir → önceki görüntüyle fark (yazılan / iptal edilen / gerçekleşen lot),
    destek seviyesi ve satış duvarı izleme. Bellekte sınırlı (deque maxlen) tutulur.
  * Sonuçlar ~3 sn'de bir yeniden hesaplanır, API önbellekten döner (feed asla bloklanmaz).
  * Piyasa kapalıyken (hafta sonu / seans öncesi) son işlem gününün diske kaydedilmiş işlemleri kullanılır,
    derinlik tabanlı ekranlar son derinlik görüntüsünü (ör. Cuma kapanış) gösterir.
"""
from __future__ import annotations

import array
import bisect
import collections
import gzip
import json
import logging
import math
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.live_store import _Sym, TRADES_DIR

logger = logging.getLogger("v122")
IST = ZoneInfo("Europe/Istanbul")
DATA = Path(__file__).resolve().parent.parent / "data" / "v122"
VERSION = "1.22.0"
CONT_FROM, CONT_TO = 10 * 3600, 18 * 3600          # sürekli işlem
DAY_NAMES = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def _now() -> datetime:
    return datetime.now(IST)


def _today() -> str:
    return _now().strftime("%Y%m%d")


def _sec_now() -> int:
    n = _now()
    return n.hour * 3600 + n.minute * 60 + n.second


def _hms(sec) -> str:
    sec = int(sec or 0)
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def _hm(sec) -> str:
    sec = int(sec or 0)
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}"


def _clip(x, a=0.0, b=1.0):
    try:
        return a if x is None or x != x else max(a, min(b, x))
    except Exception:
        return a


def _r(v, d=2):
    return None if v is None else round(v, d)


def _tick_size(p: float) -> float:
    if p < 20: return 0.01
    if p < 50: return 0.02
    if p < 100: return 0.05
    if p < 250: return 0.1
    if p < 500: return 0.25
    if p < 1000: return 0.5
    if p < 2500: return 1.0
    return 2.5


def _fp(v) -> str:
    if v is None:
        return "—"
    s = f"{v:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _fs(v) -> str:
    """Kısa TL / lot gösterimi (Türkçe)."""
    if v is None:
        return "—"
    a = abs(v)
    sg = "-" if v < 0 else ""
    if a >= 1e9:
        return sg + f"{a / 1e9:.2f} Mr".replace(".", ",")
    if a >= 1e6:
        return sg + f"{a / 1e6:.1f} Mn".replace(".", ",")
    if a >= 1e3:
        return sg + f"{a / 1e3:.0f} bin"
    return sg + f"{a:.0f}"


def _pc(v, d=1) -> str:
    if v is None:
        return "—"
    s = f"{abs(v):.{d}f}".replace(".", ",")
    return ("+" if v > 0 else "-" if v < 0 else "") + "%" + s


def C(k: str, label: str, t: str = "num") -> list:
    return [k, label, t]


# ================================================================ SOURCE ==
class DiskDay:
    """Son işlem gününün diske kaydedilmiş işlemleri (salt okunur, hafta sonu / seans öncesi)."""

    def __init__(self, day: str) -> None:
        self.day = day
        self.syms: dict[str, _Sym] = {}
        self.brokers: list[str] = [""]
        self.lock = threading.RLock()
        self.loaded = False
        self.rows = 0

    def load(self) -> None:
        p = TRADES_DIR / self.day
        bf = p / "_brokers.txt"
        if bf.exists():
            names = bf.read_text(encoding="utf-8").split("\n")
            if names and names[-1] == "":
                names = names[:-1]
            self.brokers = [""] + names[1:] if names and names[0] == "" else [""] + names
        n = 0
        for f in sorted(p.glob("*.csv")):
            e = _Sym()
            T, P, L, SD, B, S = e.t, e.p, e.l, e.sd, e.b, e.s
            try:
                with f.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        c = line.split(",")
                        if len(c) < 6:
                            continue
                        try:
                            T.append(int(c[0])); P.append(float(c[1])); L.append(int(c[2]))
                            SD.append(int(c[3])); B.append(int(c[4])); S.append(int(c[5]))
                        except ValueError:
                            m = min(len(T), len(P), len(L), len(SD), len(B), len(S))
                            for arr in (T, P, L, B, S):
                                del arr[m:]
                            del SD[m:]
            except Exception as ex:
                logger.warning("v122 disk %s: %s", f.name, ex)
                continue
            e.flushed = len(T)
            self.syms[f.stem] = e
            n += len(T)
        self.rows = n
        self.loaded = True
        logger.info("v122: %s diskten yüklendi (%d hisse, %d işlem)", self.day, len(self.syms), n)


def _last_disk_day(before: str) -> str | None:
    try:
        ds = sorted(d.name for d in TRADES_DIR.iterdir() if d.is_dir() and d.name.isdigit() and d.name < before)
    except Exception:
        return None
    for d in reversed(ds):
        try:
            if any(True for _ in (TRADES_DIR / d).glob("*.csv")):
                return d
        except Exception:
            continue
    return None


# ============================================================ PER-SYMBOL ==
class KS:
    """Hisse başına artımlı işlem özetleri."""
    __slots__ = ("ptr", "merges", "n", "nb", "ns", "lb", "ls", "la", "tb", "ts", "ta", "px", "lotc", "brp", "bra",
                 "mins", "secq", "last", "open", "hi", "lo", "hi_sec", "lo_sec", "run", "runs", "best_run",
                 "burst", "bursts", "big", "self_lot", "tat", "last_cont", "first_cont", "small_s")

    def __init__(self) -> None:
        self.ptr = 0
        self.merges = -1
        self.n = self.nb = self.ns = 0
        self.lb = self.ls = self.la = 0
        self.tb = self.ts = self.ta = 0.0
        self.px: dict[float, list] = {}        # fiyat -> [aktif alış lot, aktif satış lot, n alış, n satış, diğer lot]
        self.lotc: dict[int, list] = {}        # lot büyüklüğü -> [adet, alış adet, satış adet]
        self.brp: dict[tuple, list] = {}       # (kurum, 1=aldı/2=sattı, fiyat) -> [lot, adet, aktif lot]
        self.bra: dict[int, list] = {}         # kurum -> [aktif alış, pasif alış, aktif satış, pasif satış, aktif alış ₺, net ₺, süpürme lot]
        self.mins: dict[int, list] = {}        # dakika -> [n, lot, tl, lb, ls, o, h, l, c, nb, ns, bigb, bigs, push_lot, self_lot]
        self.secq = collections.deque(maxlen=900)   # [saniye, işlem sayısı]
        self.last = self.open = self.hi = self.lo = None
        self.hi_sec = self.lo_sec = None
        self.run = None                        # [adım, başlangıç px, başlangıç sn, lot, son sn, son px, alış lot]
        self.runs = collections.deque(maxlen=80)
        self.best_run = None
        self.burst = None
        self.bursts = collections.deque(maxlen=600)  # (sn, yön, kademe, lot, tl, ilk, son, kurum, pay, n)
        self.big = collections.deque(maxlen=1000)    # (sn, px, lot, tl, yön, alıcı, satıcı)
        self.self_lot = 0
        self.tat: dict[tuple, float] = {}      # (yön, fiyat) -> son derinlik örneğinden beri gerçekleşen lot
        self.last_cont = None
        self.first_cont = None
        self.small_s = 0                       # küçük (<20 bin ₺) aktif satış adedi


class KD:
    """Hisse başına derinlik geçmişi ve fark istatistikleri (sınırlı bellek)."""
    __slots__ = ("ts", "asks", "bids", "pa", "pb", "hist", "evq", "sup", "walls", "fakes", "gone", "n", "src")

    def __init__(self) -> None:
        self.ts = None
        self.asks: list = []                   # [(fiyat, lot, emir)] artan
        self.bids: list = []                   # [(fiyat, lot, emir)] azalan
        self.pa: dict = {}
        self.pb: dict = {}
        self.hist = collections.deque(maxlen=360)   # (sn, ask5, bid5, askT, bidT, best_bid, best_ask)
        self.evq = collections.deque(maxlen=600)    # (sn, ask_add, ask_canc, ask_fill, bid_add, bid_canc, bid_fill)
        self.sup: dict[float, dict] = {}
        self.walls: dict[float, dict] = {}
        self.fakes = collections.deque(maxlen=100)
        self.gone = collections.deque(maxlen=100)   # süpürülen / iptal edilen duvarlar
        self.n = 0
        self.src = "canlı"


# ================================================================ ENGINE ==
class Engine:
    def __init__(self) -> None:
        self.feed = self.store = self.hub = self.op = self.events = None
        self.lock = threading.RLock()
        self.k: dict[str, KS] = {}
        self.d: dict[str, KD] = {}
        self.mode = None            # "canlı" | "kayıt"
        self.day = None
        self.disk: DiskDay | None = None
        self.brokers: list[str] = [""]
        self.res: dict[str, dict] = {}
        self.X: dict | None = None
        self.cache: dict[tuple, tuple] = {}
        self.timing: dict[str, float] = {}
        self.errors: dict[str, str] = {}
        self.computed_at = None
        self.started = False
        self.ingested = 0
        self.ready = False
        self.loops = 0
        self.alerted: dict[tuple, tuple] = {}
        self.arate = collections.deque()
        self.prev_state: dict[tuple, object] = {}
        self.stage: dict[str, dict] = {}
        self._books_saved = 0.0
        self._first_alert_pass = True
        self.ondemand_lock = threading.Lock()

    # ------------------------------------------------------------ setup --
    def start(self, feed, store, hub=None, op=None, events=None) -> None:
        if self.started:
            return
        self.started = True
        self.feed, self.store, self.hub, self.op, self.events = feed, store, hub, op, events
        DATA.mkdir(parents=True, exist_ok=True)
        threading.Thread(target=self._sample_loop, name="v122-sample", daemon=True).start()
        threading.Thread(target=self._compute_loop, name="v122-compute", daemon=True).start()
        logger.info("v122 kademe & şerit motoru başladı")

    # ----------------------------------------------------------- source --
    def _pick(self):
        st = self.store
        today = _today()
        live_n = 0
        if st is not None and st.day == today:
            try:
                live_n = sum(1 for e in list(st.syms.values()) if len(e.t))
            except Exception:
                live_n = 0
        if live_n > 0:
            return "canlı", st.day, st.syms, st.brokers, st.lock
        # canlı kayıt yok (hafta sonu / seans öncesi) → son kayıtlı gün
        dd = _last_disk_day(today)
        if not dd:
            return "canlı", st.day if st else today, (st.syms if st else {}), (st.brokers if st else [""]), (st.lock if st else self.lock)
        if self.disk is None or self.disk.day != dd:
            dk = DiskDay(dd)
            dk.load()
            self.disk = dk
        dk = self.disk
        return "kayıt", dk.day, dk.syms, dk.brokers, dk.lock

    def _reset(self, mode, day) -> None:
        with self.lock:
            self.mode, self.day = mode, day
            self.k = {}
            for D in self.d.values():
                D.hist.clear(); D.evq.clear(); D.sup.clear(); D.walls.clear(); D.fakes.clear(); D.gone.clear()
                D.pa = {}; D.pb = {}; D.ts = None
            self.stage = {}
            self.prev_state = {}
            self.cache = {}
            self.ingested = 0
            self.ready = False
            self._first_alert_pass = True
        if mode == "canlı" and self.disk is not None:
            self.disk = None          # belleği bırak
        logger.info("v122 kaynak: %s %s", mode, day)

    # ----------------------------------------------------------- ingest --
    def _ingest(self, sym: str, e, slock) -> int:
        K = self.k.get(sym)
        if K is None:
            K = self.k[sym] = KS()
        with slock:
            n = min(len(e.t), len(e.p), len(e.l), len(e.sd), len(e.b), len(e.s))
            if getattr(e, "snap_merges", 0) != K.merges or n < K.ptr:
                if K.ptr:
                    K = self.k[sym] = KS()
                K.merges = getattr(e, "snap_merges", 0)
            if n == K.ptr:
                return 0
            a = K.ptr
            T = e.t[a:n]; P = e.p[a:n]; LL = e.l[a:n]; SD = e.sd[a:n]; B = e.b[a:n]; S = e.s[a:n]
            K.ptr = n
        with self.lock:
            self._ingest_rows(K, T, P, LL, SD, B, S)
        return len(T)

    def _ingest_rows(self, K: KS, T, P, LL, SD, B, S) -> None:
        pxd, lotc, brp, bra, mins, secq, tat = K.px, K.lotc, K.brp, K.bra, K.mins, K.secq, K.tat
        bursts = K.bursts
        for i in range(len(T)):
            sec = T[i]; px = P[i]; lot = LL[i]; sd = SD[i]; b = B[i]; s = S[i]
            if lot <= 0:
                continue
            tl = px * lot
            K.n += 1
            pa = pxd.get(px)
            if pa is None:
                pa = pxd[px] = [0, 0, 0, 0, 0]
            m = sec // 60
            mm = mins.get(m)
            if mm is None:
                mm = mins[m] = [0, 0, 0.0, 0, 0, px, px, px, px, 0, 0, 0, 0, 0, 0]
            mm[0] += 1; mm[1] += lot; mm[2] += tl; mm[8] = px
            if px > mm[6]: mm[6] = px
            if px < mm[7]: mm[7] = px
            if secq and secq[-1][0] == sec:
                secq[-1][1] += 1
            else:
                secq.append([sec, 1])
            cont = sd == 1 or sd == 2
            if sd == 1:
                K.nb += 1; K.lb += lot; K.tb += tl; pa[0] += lot; pa[2] += 1; mm[3] += lot; mm[9] += 1
            elif sd == 2:
                K.ns += 1; K.ls += lot; K.ts += tl; pa[1] += lot; pa[3] += 1; mm[4] += lot; mm[10] += 1
                if tl < 20000:
                    K.small_s += 1
            else:
                K.la += lot; K.ta += tl; pa[4] += lot
            if cont:
                lc = lotc.get(lot)
                if lc is None:
                    lc = lotc[lot] = [0, 0, 0]
                lc[0] += 1; lc[sd] += 1
            # kurum × fiyat
            if b:
                k1 = (b, 1, px)
                v = brp.get(k1)
                if v is None:
                    v = brp[k1] = [0, 0, 0]
                v[0] += lot; v[1] += 1
                if sd == 1:
                    v[2] += lot
                ba = bra.get(b)
                if ba is None:
                    ba = bra[b] = [0, 0, 0, 0, 0.0, 0.0, 0]
                if sd == 1:
                    ba[0] += lot; ba[4] += tl
                elif sd == 2:
                    ba[1] += lot
                ba[5] += tl
            if s:
                k2 = (s, 2, px)
                v = brp.get(k2)
                if v is None:
                    v = brp[k2] = [0, 0, 0]
                v[0] += lot; v[1] += 1
                if sd == 2:
                    v[2] += lot
                sa = bra.get(s)
                if sa is None:
                    sa = bra[s] = [0, 0, 0, 0, 0.0, 0.0, 0]
                if sd == 2:
                    sa[2] += lot
                elif sd == 1:
                    sa[3] += lot
                sa[5] -= tl
            if b and b == s:
                K.self_lot += lot
                mm[14] += lot
            if not cont:
                # açılış / kapanış seansı eşleşmesi: süpürme / uptick dizisini kapat
                if K.burst:
                    self._burst_close(K)
                continue
            tat[(sd, px)] = tat.get((sd, px), 0) + lot
            prev = K.last
            if K.open is None:
                K.open = px; K.first_cont = sec
            if K.hi is None or px > K.hi:
                K.hi = px; K.hi_sec = sec
            if K.lo is None or px < K.lo:
                K.lo = px; K.lo_sec = sec
            K.last = px; K.last_cont = sec
            # büyük işlem
            avg = (K.tb + K.ts) / max(1, K.nb + K.ns)
            thr = max(300_000.0, 12.0 * avg) if (K.nb + K.ns) > 30 else 300_000.0
            if tl >= thr:
                K.big.append((sec, px, lot, tl, sd, b, s))
                if sd == 1: mm[11] += lot
                else: mm[12] += lot
            # uptick dizisi (eşit fiyat diziyi bozmaz, düşüş bozar, 60 sn boşluk bozar)
            if prev is not None:
                r = K.run
                if r is not None and sec - r[4] > 60:
                    self._run_close(K); r = None
                if px > prev + 1e-9:
                    if sd == 1:
                        mm[13] += lot
                    if r is None:
                        K.run = [1, prev, sec, lot, sec, px, lot if sd == 1 else 0]
                    else:
                        r[0] += 1; r[3] += lot; r[4] = sec; r[5] = px
                        if sd == 1: r[6] += lot
                elif px < prev - 1e-9:
                    if r is not None:
                        self._run_close(K)
                elif r is not None:
                    r[3] += lot; r[4] = sec
                    if sd == 1: r[6] += lot
            # süpürme (aynı saniye + aynı yön ardışık işlemler = tek agresif emir)
            bu = K.burst
            if bu is not None and (bu[0] != sd or bu[1] != sec):
                self._burst_close(K); bu = None
            if bu is None:
                bu = K.burst = [sd, sec, 0, 0.0, set(), px, px, 0, collections.Counter()]
            bu[2] += lot; bu[3] += tl; bu[4].add(px); bu[6] = px; bu[7] += 1
            bu[8][b if sd == 1 else s] += lot

    def _burst_close(self, K: KS) -> None:
        bu = K.burst
        K.burst = None
        if not bu:
            return
        lv = len(bu[4])
        if lv >= 2 or bu[3] >= 250_000:
            tb, tl_ = (bu[8].most_common(1) or [(0, 0)])[0]
            K.bursts.append((bu[1], bu[0], lv, bu[2], bu[3], bu[5], bu[6], tb, (tl_ / bu[2]) if bu[2] else 0, bu[7]))
            if bu[0] == 1 and lv >= 2 and tb:
                ba = K.bra.get(tb)
                if ba is not None:
                    ba[6] += bu[2]

    def _run_close(self, K: KS) -> None:
        r = K.run
        K.run = None
        if not r or r[0] < 3:
            return
        rec = (r[2], r[4], r[0], r[1], r[5], r[3], r[6])
        K.runs.append(rec)
        if K.best_run is None or r[0] > K.best_run[2]:
            K.best_run = rec

    # ------------------------------------------------------------ depth --
    def _depth(self, sym: str, d: dict, sec: int, K: KS | None, fresh: bool) -> None:
        D = self.d.get(sym)
        if D is None:
            D = self.d[sym] = KD()
        ts = d.get("ts")
        if ts is not None and ts == D.ts:
            return
        asks = sorted((v["price"], v["lot"], v.get("orders", 0)) for v in (d.get("asks") or {}).values() if v.get("price") and v.get("lot"))
        bids = sorted(((v["price"], v["lot"], v.get("orders", 0)) for v in (d.get("bids") or {}).values() if v.get("price") and v.get("lot")),
                      key=lambda x: -x[0])
        if not asks and not bids:
            return
        first = D.ts is None
        D.ts = ts
        D.asks, D.bids = asks, bids
        D.n += 1
        D.src = "canlı" if fresh else "son görüntü"
        na = {p: l for p, l, _ in asks}
        nb = {p: l for p, l, _ in bids}
        a5 = sum(l for _, l, _ in asks[:5]); b5 = sum(l for _, l, _ in bids[:5])
        D.hist.append((sec, a5, b5, sum(na.values()), sum(nb.values()), bids[0][0] if bids else None, asks[0][0] if asks else None))
        tat = K.tat if K is not None else {}
        if not first and fresh:
            aa = ac = af = ba = bc = bf = 0.0
            ahi = asks[-1][0] if asks else 0
            blo = bids[-1][0] if bids else 0
            best_ask = asks[0][0] if asks else None
            # satış tarafı: düşüş = aktif alışla gerçekleşen + iptal; artış = yeni yazılan
            for p in set(D.pa) | set(na):
                a, b2 = D.pa.get(p, 0.0), na.get(p, 0.0)
                if a == b2:
                    continue
                tr = tat.get((1, p), 0.0)
                if b2 < a:
                    if b2 == 0 and p > ahi:
                        continue        # görünür 25 kademenin dışına itildi
                    dec = a - b2
                    fill = min(dec, tr); canc = dec - fill
                    af += fill * p; ac += canc * p
                    w = D.walls.get(p)
                    if w:
                        w["fill"] += fill; w["canc"] += canc; w["cur"] = b2; w["t"] = sec
                        if b2 == 0 and not w.get("gone"):
                            w["gone"] = sec
                            st = "SÜPÜRÜLDÜ" if w["fill"] >= 0.5 * w["peak"] else "İPTAL EDİLDİ" if w["canc"] >= 0.6 * w["peak"] else "BİTTİ"
                            w["st"] = st
                            D.gone.append((sec, p, w["peak"], w["fill"], w["canc"], st))
                else:
                    add = b2 - a + tr
                    aa += add * p
                    w = D.walls.get(p)
                    if w:
                        w["cur"] = b2; w["peak"] = max(w["peak"], b2); w["t"] = sec
            for p in set(D.pb) | set(nb):
                a, b2 = D.pb.get(p, 0.0), nb.get(p, 0.0)
                if a == b2:
                    continue
                tr = tat.get((2, p), 0.0)
                if b2 < a:
                    if b2 == 0 and p < blo:
                        continue
                    dec = a - b2
                    fill = min(dec, tr); canc = dec - fill
                    bf += fill * p; bc += canc * p
                    s = D.sup.get(p)
                    if s:
                        s["fill"] += fill; s["canc"] += canc; s["cur"] = b2
                        if fill > 0:
                            s["tests"] += 1; s["lt"] = sec
                        if (not s.get("fake") and s["big"] and s["canc"] >= 0.7 * s["peak"] and s["fill"] <= 0.2 * s["peak"]):
                            s["fake"] = sec
                            D.fakes.append((sec, p, s["peak"], s["fill"], s["canc"]))
                else:
                    add = b2 - a + tr
                    ba += add * p
                    s = D.sup.get(p)
                    if s:
                        s["add"] += max(0.0, b2 - a); s["cur"] = b2; s["peak"] = max(s["peak"], b2)
            D.evq.append((sec, aa, ac, af, ba, bc, bf))
        # destek (alış ilk 8) ve duvar (satış ilk 10) kayıtları
        if bids:
            lots = sorted(l for _, l, _ in bids[:15])
            med = lots[len(lots) // 2] if lots else 0
            for p, l, o in bids[:8]:
                s = D.sup.get(p)
                big = l >= max(3 * med, 500_000 / p if p else 0)
                if s is None:
                    D.sup[p] = {"first": sec, "peak": l, "cur": l, "fill": 0.0, "canc": 0.0, "add": 0.0, "tests": 0, "lt": None,
                                "big": big, "ord": o}
                else:
                    s["cur"] = l; s["peak"] = max(s["peak"], l); s["ord"] = o
                    s["big"] = s["big"] or big
            if len(D.sup) > 60:
                keep = set(p for p, _, _ in bids[:15])
                for p in sorted(D.sup, key=lambda x: D.sup[x].get("lt") or D.sup[x]["first"])[:len(D.sup) - 60]:
                    if p not in keep:
                        D.sup.pop(p, None)
        if asks:
            lots = sorted(l for _, l, _ in asks[:15])
            med = lots[len(lots) // 2] if lots else 0
            for p, l, o in asks[:10]:
                if l >= max(3 * med, 750_000 / p if p else 0) and p not in D.walls:
                    D.walls[p] = {"first": sec, "peak": l, "cur": l, "fill": 0.0, "canc": 0.0, "t": sec, "gone": None, "st": "DURUYOR"}
            if len(D.walls) > 40:
                for p in sorted(D.walls, key=lambda x: D.walls[x]["t"])[:len(D.walls) - 40]:
                    D.walls.pop(p, None)
        D.pa, D.pb = na, nb
        if K is not None:
            K.tat = {}

    # ------------------------------------------------------------- loops --
    def _universe(self) -> list[str]:
        f = self.feed
        try:
            u = f.equity_universe()
        except Exception:
            u = []
        return u or list(getattr(f, "quotes", {}).keys())

    def _sample_once(self) -> None:
        mode, day, syms, brokers, slock = self._pick()
        if (mode, day) != (self.mode, self.day):
            self._reset(mode, day)
        self.brokers = brokers
        uni = self._universe()
        f = self.feed
        sec = _sec_now()
        nowt = time.time()
        tot = 0
        for s in uni:
            e = syms.get(s)
            if e is not None:
                try:
                    tot += self._ingest(s, e, slock)
                except Exception as ex:   # pragma: no cover
                    self.errors["ingest"] = f"{s}: {ex}"[:200]
            with f._lock:
                d = f.depth.get(s)
                if d:
                    d = {"asks": {k: dict(v) for k, v in (d.get("asks") or {}).items()},
                         "bids": {k: dict(v) for k, v in (d.get("bids") or {}).items()}, "ts": d.get("ts")}
            if not d:
                d = self._saved_book(s)
            if d:
                fresh = bool(mode == "canlı" and d.get("ts") and nowt - d["ts"] < 20 and self._in_session(sec))
                try:
                    with self.lock:
                        self._depth(s, d, sec, self.k.get(s), fresh)
                except Exception as ex:   # pragma: no cover
                    self.errors["depth"] = f"{s}: {ex}"[:200]
        # açık kalan süpürme/uptick dizilerini kapat (kayıt modunda gün sonu)
        if mode == "kayıt":
            with self.lock:
                for K in self.k.values():
                    if K.burst:
                        self._burst_close(K)
        else:
            with self.lock:
                for K in self.k.values():
                    if K.burst and sec - K.burst[1] > 2:
                        self._burst_close(K)
        self.ingested += tot
        self.ready = True
        self.loops += 1
        if mode == "canlı" and time.time() - self._books_saved > 300 and self._in_session(sec, pad=900):
            self._save_books()

    @staticmethod
    def _in_session(sec: int, pad: int = 0) -> bool:
        return _now().weekday() < 5 and 9 * 3600 + 55 * 60 - pad <= sec <= 18 * 3600 + 10 * 60 + pad

    def _sample_loop(self) -> None:
        time.sleep(8)
        while True:
            t0 = time.time()
            try:
                self._sample_once()
                self.timing["sample"] = round(time.time() - t0, 3)
            except Exception as ex:
                logger.warning("v122 sample: %s", ex, exc_info=True)
                self.errors["sample"] = str(ex)[:200]
            time.sleep(max(0.8, 2.0 - (time.time() - t0)))

    def _compute_loop(self) -> None:
        time.sleep(12)
        while True:
            t0 = time.time()
            try:
                sig = (self.mode, self.day, self.ingested, sum(len(D.evq) for D in list(self.d.values())))
                stale = (self.mode == "kayıt" and sig == getattr(self, "_last_sig", None)
                         and time.time() - getattr(self, "_last_full", 0) < 60)   # kayıtlı gün: veri değişmedikçe 60 sn'de bir
                if self.ready and not stale:
                    self.compute()
                    self._last_sig = sig
                    self._last_full = time.time()
                    self.timing["compute"] = round(time.time() - t0, 3)
            except Exception as ex:
                logger.warning("v122 compute: %s", ex, exc_info=True)
                self.errors["compute"] = str(ex)[:200]
            time.sleep(max(1.5, 3.0 - (time.time() - t0)))

    # ------------------------------------------------- book persistence --
    def _save_books(self) -> None:
        self._books_saved = time.time()
        try:
            out = {}
            with self.lock:
                for s, D in self.d.items():
                    if D.asks or D.bids:
                        out[s] = [D.asks[:25], D.bids[:25]]
            p = DATA / f"books_{self.day}.json"
            tmp = p.with_suffix(".tmp")
            tmp.write_text(json.dumps({"saved": _now().strftime("%Y-%m-%d %H:%M:%S"), "b": out}), encoding="utf-8")
            os.replace(tmp, p)
        except Exception as ex:
            logger.debug("v122 books save: %s", ex)

    _books_disk = None

    def _saved_book(self, sym: str):
        if self._books_disk is None or time.time() - getattr(self, "_books_chk", 0) > 60:
            self._books_chk = time.time()
            try:
                fs = sorted(DATA.glob("books_*.json"))
                key = (fs[-1].name, fs[-1].stat().st_mtime) if fs else None
                if key != getattr(self, "_books_key", None) or self._books_disk is None:
                    self._books_key = key
                    self._books_disk = json.loads(fs[-1].read_text(encoding="utf-8")).get("b") or {} if fs else {}
            except Exception:
                self._books_disk = self._books_disk or {}
        v = self._books_disk.get(sym)
        if not v:
            return None
        return {"asks": {i: {"price": a[0], "lot": a[1], "orders": a[2]} for i, a in enumerate(v[0])},
                "bids": {i: {"price": a[0], "lot": a[1], "orders": a[2]} for i, a in enumerate(v[1])}, "ts": -1}


    # =========================================================== CONTEXT ==
    def _ctx(self) -> dict:
        f = self.feed
        uni = self._universe()
        sec = _sec_now()
        Q = {}
        with f._lock:
            for s in uni:
                q = f.quotes.get(s)
                if not q or not q.get("last"):
                    continue
                Q[s] = {k: q.get(k) for k in ("last", "prev_close", "high", "low", "open", "ceiling", "floor", "vwap",
                                              "turnover", "volume", "bid", "ask", "tick")}
            names = dict(getattr(f, "names", {}) or {})
        for s, qq in Q.items():
            pc = qq.get("prev_close")
            if pc and (sec >= 65400 or sec < 34800 or _now().weekday() >= 5) and qq.get("ceiling") and qq["ceiling"] > pc * 1.105:
                lp = qq["last"]
                qq["ceiling"] = lp if lp / pc >= 1.094 and lp >= (qq.get("high") or lp) - 1e-9 else round(pc * 1.1, 2)
                qq["floor"] = lp if lp / pc <= 0.906 and lp <= (qq.get("low") or lp) + 1e-9 else round(pc * 0.9, 2)
        live = self.mode == "canlı" and self._in_session(sec)
        if live:
            ref = min(sec, CONT_TO)
        else:
            lc = [K.last_cont for K in list(self.k.values()) if K.last_cont]
            ref = max(lc) if lc else CONT_TO
        el = max(1.0, (min(ref, CONT_TO) - CONT_FROM) / 60.0)
        return {"Q": Q, "N": names, "sec": sec, "ref": ref, "live": live, "el": el, "mode": self.mode, "day": self.day}

    def _base(self, s: str, X: dict, K: KS | None = None) -> dict:
        q = X["Q"].get(s) or {}
        last = q.get("last") or (K.last if K else None)
        pc = q.get("prev_close")
        return {"s": s, "n": X["N"].get(s), "p": last, "c": _r((last / pc - 1) * 100) if (last and pc) else None,
                "t": q.get("turnover")}

    def _magg(self, K: KS, m0: int, m1: int) -> dict:
        a = {"n": 0, "lot": 0, "tl": 0.0, "lb": 0, "ls": 0, "nb": 0, "ns": 0, "bigb": 0, "bigs": 0, "push": 0, "self": 0,
             "o": None, "c": None, "h": None, "l": None, "mins": 0}
        mins = K.mins
        for m in range(m0, m1 + 1):
            mm = mins.get(m)
            if not mm:
                continue
            a["n"] += mm[0]; a["lot"] += mm[1]; a["tl"] += mm[2]; a["lb"] += mm[3]; a["ls"] += mm[4]
            a["nb"] += mm[9]; a["ns"] += mm[10]; a["bigb"] += mm[11]; a["bigs"] += mm[12]; a["push"] += mm[13]; a["self"] += mm[14]
            if a["o"] is None:
                a["o"] = mm[5]
            a["c"] = mm[8]
            a["h"] = mm[6] if a["h"] is None else max(a["h"], mm[6])
            a["l"] = mm[7] if a["l"] is None else min(a["l"], mm[7])
            a["mins"] += 1
        return a

    def _price_before(self, K: KS, m: int, back: int = 30):
        """m dakikasından önceki son kapanış fiyatı."""
        for x in range(m - 1, m - back - 1, -1):
            mm = K.mins.get(x)
            if mm:
                return mm[8]
        return K.open

    def _src_arrays(self, sym: str, s0: int, s1: int):
        """Kaynak işlem dizilerinden [s0, s1] aralığı (kopya)."""
        if self.mode == "kayıt" and self.disk is not None:
            syms, slock = self.disk.syms, self.disk.lock
        else:
            syms, slock = (self.store.syms if self.store else {}), (self.store.lock if self.store else self.lock)
        e = syms.get(sym)
        if e is None:
            return None
        with slock:
            n = min(len(e.t), len(e.p), len(e.l), len(e.sd), len(e.b), len(e.s))
            i0 = bisect.bisect_left(e.t, s0, 0, n)
            i1 = bisect.bisect_right(e.t, s1, i0, n)
            if i1 <= i0:
                return None
            return e.t[i0:i1], e.p[i0:i1], e.l[i0:i1], e.sd[i0:i1], e.b[i0:i1], e.s[i0:i1]

    def bname(self, i: int) -> str:
        try:
            return self.brokers[i] or ""
        except Exception:
            return ""

    @staticmethod
    def _win_label(w) -> str:
        return "Gün geneli" if w in ("gun", None, 0) else f"Son {w} dk"

    # =========================================================== FEATURES ==
    # A ------------------------------------------------------------ İşlem Analizi
    def f_islem(self, X: dict, w="15"):
        rows = []
        ref = X["ref"]
        gun = w in ("gun", None)
        wm = 0 if gun else int(w)
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or not (K.nb + K.ns):
                continue
            if gun:
                lb, ls, tb, ts_ = K.lb, K.ls, K.tb, K.ts
                n = K.nb + K.ns
                pr = [(p, v[0], v[1], v[2] + v[3]) for p, v in K.px.items() if v[2] + v[3]]
                lots = K.lotc
                lot_items = [(l, v[0]) for l, v in lots.items()]
                p0 = K.open
            else:
                arr = self._src_arrays(s, ref - wm * 60 + 1, ref)
                if not arr:
                    continue
                T, P, L, SD, _, _ = arr
                lb = ls = 0; tb = ts_ = 0.0; n = 0
                pd: dict = {}; lc: dict = {}
                for i in range(len(T)):
                    sd = SD[i]
                    if sd != 1 and sd != 2:
                        continue
                    px = P[i]; lot = L[i]
                    v = pd.get(px)
                    if v is None:
                        v = pd[px] = [0, 0, 0]
                    if sd == 1:
                        lb += lot; tb += px * lot; v[0] += lot
                    else:
                        ls += lot; ts_ += px * lot; v[1] += lot
                    v[2] += 1; n += 1
                    lc[lot] = lc.get(lot, 0) + 1
                if not n:
                    continue
                pr = [(p, v[0], v[1], v[2]) for p, v in pd.items()]
                lot_items = list(lc.items())
                p0 = self._price_before(K, (ref - wm * 60) // 60 + 1)
            tl = tb + ts_
            if tl < (100_000 if gun else 30_000) or n < 3:
                continue
            B = self._base(s, X, K)
            last = B["p"] or K.last
            ab = lb / (lb + ls) * 100 if (lb + ls) else None
            avgb = tb / lb if lb else None
            avgs = ts_ / ls if ls else None
            vw = tl / (lb + ls) if (lb + ls) else None
            tp = max(pr, key=lambda x: (x[3], x[1] + x[2])) if pr else None
            tlt = max(lot_items, key=lambda x: (x[1], x[0])) if lot_items else None
            sup = max((x for x in pr if x[0] <= last + 1e-9), key=lambda x: x[2], default=None)
            res = max((x for x in pr if x[0] >= last - 1e-9), key=lambda x: x[1], default=None)
            algo = bool(tlt and tlt[0] >= 10 and tlt[1] >= max(15, 0.04 * n))
            if ab is None:
                du = "—"
            elif ab >= 80 and tb >= 1_000_000:
                du = "ALICI SATICIYI SİLİYOR"
            elif ab >= 65:
                du = "ALICI BASKIN"
            elif ab <= 20 and ts_ >= 1_000_000:
                du = "SATICI ALICIYI SİLİYOR"
            elif ab <= 35:
                du = "SATICI BASKIN"
            else:
                du = "DENGELİ"
            wt = min(1.0, (tl / 1_000_000) ** 0.35) if tl > 0 else 0
            sc = (ab or 0) * wt
            r = dict(B)
            r.update({"du": du, "ab": _r(ab, 1), "as": _r(100 - ab, 1) if ab is not None else None, "alot": lb, "slot": ls,
                      "atl": round(tb), "stl": round(ts_), "net": round(tb - ts_), "nn": n,
                      "tpx": tp[0] if tp else None, "tpxn": tp[3] if tp else None, "tpxl": (tp[1] + tp[2]) if tp else None,
                      "tlot": tlt[0] if tlt else None, "tlotn": tlt[1] if tlt else None, "algo": "ALGO?" if algo else "",
                      "avgb": _r(avgb, 4), "avgs": _r(avgs, 4),
                      "etki": _r((avgb / avgs - 1) * 100, 2) if (avgb and avgs) else None,
                      "vsv": _r((last / vw - 1) * 100, 2) if (vw and last) else None,
                      "wchg": _r((last / p0 - 1) * 100, 2) if (p0 and last) else None,
                      "sup": sup[0] if sup else None, "suplot": sup[2] if sup else None,
                      "res": res[0] if res else None, "reslot": res[1] if res else None,
                      "wtl": round(tl), "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("du", "Durum", "txt"),
                C("ab", "Aktif alış %", "pct"), C("as", "Aktif satış %", "pct"), C("atl", "Aktif alış ₺", "tl"),
                C("stl", "Aktif satış ₺", "tl"), C("net", "Net aktif ₺", "tl"), C("alot", "Aktif alış lot", "lot"),
                C("slot", "Aktif satış lot", "lot"), C("nn", "İşlem", "num"), C("wchg", "Pencere %", "chg"),
                C("tpx", "En çok tekrar fiyat", "px"), C("tpxn", "Tekrar", "num"), C("tpxl", "O fiyatta lot", "lot"),
                C("tlot", "En çok tekrar lot", "num"), C("tlotn", "Lot tekrar", "num"), C("algo", "Algo", "txt"),
                C("avgb", "Ort. alış fiyatı", "px"), C("avgs", "Ort. satış fiyatı", "px"), C("etki", "Alış-satış farkı %", "chg"),
                C("vsv", "Son / VWAP %", "chg"), C("sup", "Güçlü destek", "px"), C("suplot", "Emilen satış lot", "lot"),
                C("res", "Güçlü direnç", "px"), C("reslot", "Direnç lot", "lot"), C("wtl", "Pencere ₺", "tl"), C("sc", "Skor", "score")]
        return cols, rows, "sc"

    # B ---------------------------------------------------- Kurum fiyat analizi
    def f_kurumfiyat(self, X: dict, w="gun", q: str | None = None):
        ref = X["ref"]
        gun = w in ("gun", None)
        qq = (q or "").strip().upper()
        only_sym = qq if qq and qq in X["Q"] else None
        from_fold = _fold(qq) if qq and not only_sym else None
        rows = []
        for s in (X["Q"] if not only_sym else [only_sym]):
            K = self.k.get(s)
            if not K or not K.n:
                continue
            if gun:
                items = K.brp.items()
            else:
                arr = self._src_arrays(s, ref - int(w) * 60 + 1, ref)
                if not arr:
                    continue
                T, P, L, SD, Bb, Ss = arr
                tmp: dict = {}
                for i in range(len(T)):
                    px = P[i]; lot = L[i]; sd = SD[i]
                    for key, ak in (((Bb[i], 1, px), sd == 1), ((Ss[i], 2, px), sd == 2)):
                        if not key[0]:
                            continue
                        v = tmp.get(key)
                        if v is None:
                            v = tmp[key] = [0, 0, 0]
                        v[0] += lot; v[1] += 1
                        if ak:
                            v[2] += lot
                items = tmp.items()
            agg: dict = {}
            for (bi, sd, px), v in items:
                a = agg.get((bi, sd))
                if a is None:
                    a = agg[(bi, sd)] = {"lot": 0, "n": 0, "tl": 0.0, "akt": 0, "best": None, "bestn": None, "px": []}
                a["lot"] += v[0]; a["n"] += v[1]; a["tl"] += v[0] * px; a["akt"] += v[2]
                a["px"].append((px, v[0], v[1]))
            if not agg:
                continue
            side_tot = {1: sum(a["lot"] for (bi, sd), a in agg.items() if sd == 1) or 1,
                        2: sum(a["lot"] for (bi, sd), a in agg.items() if sd == 2) or 1}
            B0 = self._base(s, X, K)
            per = []
            for (bi, sd), a in agg.items():
                nm = self.bname(bi)
                if not nm:
                    continue
                if from_fold and from_fold not in _fold(nm):
                    continue
                per.append((bi, sd, a, nm))
            if not only_sym and not from_fold:
                keep = []
                for sd in (1, 2):
                    keep += sorted((x for x in per if x[1] == sd), key=lambda x: -x[2]["lot"])[:3]
                per = keep
            for bi, sd, a, nm in per:
                pl = sorted(a["px"], key=lambda x: -x[1])
                pn = max(a["px"], key=lambda x: (x[2], x[1]))
                r = dict(B0)
                r.update({"br": nm, "yon": "ALIŞ" if sd == 1 else "SATIŞ", "vk": "AL" if sd == 1 else "SAT",
                          "fpx": pl[0][0], "flot": pl[0][1], "fn": pl[0][2],
                          "npx": pn[0], "nn": pn[2], "nlot": pn[1],
                          "px2": pl[1][0] if len(pl) > 1 else None, "lot2": pl[1][1] if len(pl) > 1 else None,
                          "tlot": a["lot"], "tn": a["n"], "avg": _r(a["tl"] / a["lot"], 4) if a["lot"] else None,
                          "ttl": round(a["tl"]), "akt": _r(a["akt"] / a["lot"] * 100, 1) if a["lot"] else None,
                          "pay": _r(a["lot"] / side_tot[sd] * 100, 1), "fpay": _r(pl[0][1] / a["lot"] * 100, 1) if a["lot"] else None,
                          "nfiyat": len(a["px"])})
                rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("br", "Kurum", "broker"), C("yon", "Yön", "verdict"), C("fpx", "En çok lot fiyatı", "px"),
                C("flot", "O fiyatta lot", "lot"), C("fn", "O fiyatta adet", "num"), C("fpay", "Fiyat payı %", "pct"),
                C("npx", "En çok tekrar fiyat", "px"), C("nn", "Tekrar adedi", "num"), C("px2", "2. fiyat", "px"), C("lot2", "2. fiyat lot", "lot"),
                C("tlot", "Toplam lot", "lot"), C("tn", "Toplam işlem", "num"), C("avg", "Ort. fiyat", "px"), C("ttl", "Toplam ₺", "tl"),
                C("akt", "Aktif %", "pct"), C("pay", "Yön payı %", "pct"), C("nfiyat", "Fiyat sayısı", "num"), C("p", "Son fiyat", "px")]
        return cols, rows, "ttl"

    # 1 -------------------------------------------- Pozitif Anlık Hareketlilik
    def f_pozitif(self, X: dict, w=None):
        if not X.get("live"):
            return self._replay(X, "pozitif")
        ref = X["ref"]; mref = ref // 60; el = X["el"]
        rows = []
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or not K.nb or not K.last:
                continue
            a3 = self._magg(K, mref - 2, mref)
            if a3["tl"] < 200_000 or not a3["lb"]:
                continue
            p_prev = self._price_before(K, mref - 2)
            last = K.last
            if not p_prev:
                continue
            chg3 = (last / p_prev - 1) * 100
            if chg3 <= 0.15:
                continue
            p1 = self._price_before(K, mref)
            chg1 = (last / p1 - 1) * 100 if p1 else 0.0
            acc = chg1 - (chg3 - chg1) / 2.0
            ab3 = a3["lb"] / max(1, a3["lb"] + a3["ls"])
            sw = [b for b in K.bursts if b[0] >= ref - 180 and b[1] == 1 and b[2] >= 2]
            swn = len(sw); swlot = sum(b[3] for b in sw)
            rate = (K.tb + K.ts) / el
            vr = (a3["tl"] / 3.0) / rate if rate else 0.0
            B = self._base(s, X, K)
            c = B["c"] or 0.0
            q = X["Q"][s]
            ce = q.get("ceiling")
            dc = (ce / last - 1) * 100 if ce else None
            sc = 30 * _clip(chg3 / 2) + 25 * _clip((ab3 - 0.5) / 0.45) + 20 * _clip(vr / 5) + 15 * _clip(swn / 3) + 10 * _clip(acc / 0.8)
            if c > 8:
                sc *= 0.6
            if sc < 25:
                continue
            du = ("ERKEN" if c < 4 else "ORTA" if c < 7 else "GEÇ") + (f" · tavana {_pc(dc)}" if dc is not None else "")
            r = dict(B)
            r.update({"chg3": _r(chg3), "chg1": _r(chg1), "acc": _r(acc), "ab3": _r(ab3 * 100, 1), "sw": swn, "swlot": swlot,
                      "bigb": a3["bigb"], "as3": a3["ls"], "vr": _r(vr, 1), "tl3": round(a3["tl"]), "du": du, "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"),
                C("chg3", "3 dk %", "chg"), C("chg1", "1 dk %", "chg"), C("acc", "İvme", "num"), C("ab3", "Aktif alış %", "pct"),
                C("sw", "Süpürme", "num"), C("swlot", "Süpürülen lot", "lot"), C("bigb", "Balina alış lot", "lot"),
                C("as3", "Aktif satış lot", "lot"), C("vr", "Hacim hızı ×", "num"), C("tl3", "3 dk ₺", "tl"), C("du", "Evre", "txt")]
        return cols, rows, "sc"

    # 2 ------------------------------------------------- Yakın Kademe Koruması
    def f_koruma(self, X: dict, w=None):
        el = X["el"]; rows = []
        for s, D in list(self.d.items()):
            if s not in X["Q"] or len(D.bids) < 6 or not D.asks:
                continue
            bids, asks = D.bids, D.asks
            b4 = sum(l for _, l, _ in bids[:4]); a4 = sum(l for _, l, _ in asks[:4]) or 1
            b4tl = sum(p * l for p, l, _ in bids[:4])
            if b4tl < 250_000:
                continue
            deep = [l for _, l, _ in bids[4:15]]
            davg = (sum(deep) / len(deep)) if deep else 0
            thick = (b4 / 4) / davg if davg else 1.0
            K = self.k.get(s)
            srate = (K.ls / el) if (K and K.ls) else None
            kir = b4 / srate if srate else None
            r = b4 / a4
            if r < 1.2:
                continue
            ords = sum(o for _, _, o in bids[:4])
            sk = max(bids[:4], key=lambda x: x[1])
            sc = 35 * _clip(math.log2(r) / 3) + 35 * _clip((kir or 0) / 30) + 30 * _clip((thick - 1) / 3)
            B = self._base(s, X, K)
            row = dict(B)
            row.update({"b4": b4, "b4tl": round(b4tl), "a4": a4, "r": _r(r, 2), "kir": _r(kir, 1), "thick": _r(thick, 2),
                        "ord": ords, "sk": sk[0], "sklot": sk[1], "src": D.src, "sc": round(sc, 1)})
            rows.append(row)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"),
                C("b4", "İlk 4 alış lot", "lot"), C("b4tl", "İlk 4 alış ₺", "tl"), C("a4", "İlk 4 satış lot", "lot"),
                C("r", "Alış/Satış ×", "num"), C("kir", "Kırma süresi dk", "num"), C("thick", "Kalınlık ×", "num"),
                C("ord", "Emir sayısı", "num"), C("sk", "En güçlü kademe", "px"), C("sklot", "O kademe lot", "lot"), C("src", "Derinlik", "txt")]
        return cols, rows, "sc"

    # 3 ------------------------------------------------ Satış Kademesi Boşluğu
    def _bos_metrics(self, s: str, D: KD, X: dict):
        q = X["Q"].get(s) or {}
        if len(D.asks) < 3 or (q.get("turnover") or 0) < 1_000_000:
            return None
        K = self.k.get(s)
        if not K or not K.tb:
            return None
        asks, bids = D.asks, D.bids
        k5 = min(5, len(asks))
        a5 = sum(l for _, l, _ in asks[:k5]); a5tl = sum(p * l for p, l, _ in asks[:k5])
        rate = K.tb / X["el"]
        clr = a5tl / rate if rate else None
        tick = q.get("tick") or _tick_size(asks[0][0])
        gap = max(0, int(round((asks[k5 - 1][0] - asks[0][0]) / tick)) - (k5 - 1)) if tick else 0
        last = q.get("last") or K.last
        p5 = asks[k5 - 1][0]
        pct5 = (p5 / last - 1) * 100 if last else None
        b5 = sum(l for _, l, _ in bids[:5]) if bids else 0
        ratio = b5 / a5 if a5 else None
        sc = 40 * _clip(1 - (clr or 99) / 10) + 25 * _clip(gap / 6) + 20 * _clip(math.log2(ratio) / 2 if ratio else 0) + 15 * _clip((pct5 or 0) / 3)
        return {"a5": a5, "a5tl": round(a5tl), "clr": _r(clr, 2), "gap": gap, "p5": p5, "pct5": _r(pct5), "b5a5": _r(ratio, 2),
                "sc": round(sc, 1), "src": D.src}

    def f_bosluk(self, X: dict, w=None):
        rows = []
        for s, D in list(self.d.items()):
            if s not in X["Q"]:
                continue
            m = self._bos_metrics(s, D, X)
            if not m or m["clr"] is None or m["clr"] > 15:
                continue
            r = self._base(s, X, self.k.get(s)); r.update(m)
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"),
                C("a5", "İlk 5 satış lot", "lot"), C("a5tl", "İlk 5 satış ₺", "tl"), C("clr", "Temizleme dk", "num"),
                C("gap", "Boş kademe", "num"), C("p5", "5. kademe", "px"), C("pct5", "5 kademe sonrası %", "chg"),
                C("b5a5", "Alış/Satış ×", "num"), C("src", "Derinlik", "txt")]
        return cols, rows, "sc"

    # 4 ------------------------------------------------------- Otoban Kademe
    def f_otoban(self, X: dict, w=None):
        ref = X["ref"]; mref = ref // 60
        rows = []
        for s, D in list(self.d.items()):
            if s not in X["Q"]:
                continue
            m = self._bos_metrics(s, D, X)
            if not m or not m["a5tl"]:
                continue
            K = self.k.get(s)
            a5 = self._magg(K, mref - 4, mref)
            if not (a5["lb"] + a5["ls"]):
                continue
            ab5 = a5["lb"] / (a5["lb"] + a5["ls"])
            last = K.last or 0
            btl5 = a5["lb"] * last
            if ab5 < 0.55 or btl5 < 200_000:
                continue
            push = btl5 / m["a5tl"]
            sw = [b for b in K.bursts if b[0] >= ref - 300 and b[1] == 1 and b[2] >= 2]
            arr = self._src_arrays(s, ref - 299, ref)
            br, brp = None, None
            if arr:
                cnt = collections.Counter()
                T, P, L, SD, Bb, _ = arr
                for i in range(len(T)):
                    if SD[i] == 1:
                        cnt[Bb[i]] += L[i]
                if cnt:
                    bi, bl = cnt.most_common(1)[0]
                    br = self.bname(bi); brp = bl / max(1, sum(cnt.values())) * 100
            sc = 0.45 * m["sc"] + 30 * _clip((ab5 - 0.5) / 0.4) + 15 * _clip(push) + 10 * _clip(len(sw) / 3)
            r = self._base(s, X, K)
            r.update({"a5tl": m["a5tl"], "clr": m["clr"], "gap": m["gap"], "pct5": m["pct5"], "ab5": _r(ab5 * 100, 1),
                      "btl5": round(btl5), "push": _r(push, 2), "sw": len(sw), "br": br, "brp": _r(brp, 1), "src": m["src"],
                      "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"),
                C("a5tl", "Boş yol (5 kademe ₺)", "tl"), C("clr", "Temizleme dk", "num"), C("gap", "Boş kademe", "num"),
                C("pct5", "Yol sonu %", "chg"), C("ab5", "5 dk aktif alış %", "pct"), C("btl5", "5 dk aktif alış ₺", "tl"),
                C("push", "İtme gücü ×", "num"), C("sw", "Süpürme", "num"), C("br", "İten kurum", "broker"), C("brp", "Kurum payı %", "pct"),
                C("src", "Derinlik", "txt")]
        return cols, rows, "sc"

    # 5 ------------------------------------------------- Doldur-Boşalt Kademe
    def f_doldur(self, X: dict, w=None):
        ref = X["ref"]; rows = []
        live = X["live"]
        for s, D in list(self.d.items()):
            if s not in X["Q"] or not D.asks or not D.bids:
                continue
            K = self.k.get(s)
            a5tl = sum(p * l for p, l, _ in D.asks[:5]); b5tl = sum(p * l for p, l, _ in D.bids[:5])
            ev = [e for e in D.evq if e[0] >= ref - 300] if live else []
            r = self._base(s, X, K)
            if ev:
                aa = sum(e[1] for e in ev); ac = sum(e[2] for e in ev); af = sum(e[3] for e in ev)
                ba = sum(e[4] for e in ev); bc = sum(e[5] for e in ev)
                h0 = next((h for h in D.hist if h[0] >= ref - 300), None)
                hn = D.hist[-1] if D.hist else None
                da5 = (hn[1] / h0[1] - 1) * 100 if (h0 and hn and h0[1]) else None
                db5 = (hn[2] / h0[2] - 1) * 100 if (h0 and hn and h0[2]) else None
                netb = ba - bc
                rem = ac + af
                if netb <= 0 and rem <= 0:
                    continue
                sc = (30 * _clip(netb / max(a5tl, 1)) + 30 * _clip(rem / max(a5tl + rem, 1)) + 20 * _clip(-(da5 or 0) / 50)
                      + 20 * _clip((db5 or 0) / 50))
                du = ("YOL AÇILIYOR" if (da5 or 0) < -20 and (db5 or 0) > 0 and af > 0 else
                      "ALIŞ DOLUYOR" if netb > 0 and (db5 or 0) > 10 else "SATIŞ BOŞALIYOR" if rem > aa else "İZLE")
                r.update({"badd": round(ba), "bcanc": round(bc), "acanc": round(ac), "afill": round(af), "aadd": round(aa),
                          "da5": _r(da5, 1), "db5": _r(db5, 1), "b5tl": round(b5tl), "a5tl": round(a5tl), "du": du, "sc": round(sc, 1)})
            else:
                if a5tl <= 0 or b5tl < 200_000:
                    continue
                ratio = b5tl / a5tl
                if ratio < 1.5:
                    continue
                sc = 50 * _clip(math.log2(ratio) / 3)
                r.update({"badd": None, "bcanc": None, "acanc": None, "afill": None, "aadd": None, "da5": None, "db5": None,
                          "b5tl": round(b5tl), "a5tl": round(a5tl), "du": "SON GÖRÜNTÜ (fark yok)", "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"), C("du", "Durum", "txt"),
                C("badd", "Alışa yazılan ₺", "tl"), C("bcanc", "Alıştan silinen ₺", "tl"), C("acanc", "Satıştan silinen ₺", "tl"),
                C("afill", "Satıştan süpürülen ₺", "tl"), C("aadd", "Satışa yazılan ₺", "tl"), C("da5", "Satış 5 kad. değişim %", "chg"),
                C("db5", "Alış 5 kad. değişim %", "chg"), C("b5tl", "Arkadaki destek ₺", "tl"), C("a5tl", "Kalan satış ₺", "tl")]
        return cols, rows, "sc"

    # 6 ---------------------------------------------- Aktif Alış Baskı Endeksi
    def f_baski(self, X: dict, w="5"):
        ref = X["ref"]; mref = ref // 60
        gun = w in ("gun", None)
        rows = []
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or not K.nb:
                continue
            if gun:
                lb, ls, push, wtl = K.lb, K.ls, sum(mm[13] for mm in K.mins.values()), K.tb + K.ts
                t0 = 0; p0 = K.open
            else:
                wm = int(w)
                a = self._magg(K, mref - wm + 1, mref)
                lb, ls, push, wtl = a["lb"], a["ls"], a["push"], a["tl"]
                t0 = ref - wm * 60; p0 = self._price_before(K, mref - wm + 1)
            if wtl < 100_000 or not lb:
                continue
            sw = [b for b in K.bursts if b[0] >= t0 and b[1] == 1 and b[2] >= 2]
            swlot = sum(b[3] for b in sw)
            ratio = min(lb / max(ls, 1), 99.0)
            pushp = push / lb
            idx = 55 * _clip(math.log2(ratio) / 3 if ratio > 0 else 0) + 25 * _clip(pushp * 2) + 20 * _clip(swlot / lb * 2)
            idx *= 0.6 + 0.4 * _clip(math.log10(max(wtl, 1) / 100_000) / 2)   # hacim ağırlığı (100 bin ₺ → ×0,6 · 10 Mn ₺ → ×1)
            r = self._base(s, X, K)
            r.update({"alot": lb, "slot": ls, "ratio": _r(ratio, 2), "push": push, "pushp": _r(pushp * 100, 1),
                      "pas": _r(ls / (lb + ls) * 100, 1), "sw": len(sw), "swlot": swlot,
                      "chgw": _r((K.last / p0 - 1) * 100) if (p0 and K.last) else None, "wtl": round(wtl), "sc": round(idx, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Baskı endeksi", "score"),
                C("ratio", "Aktif alış / satış ×", "num"), C("alot", "Aktif alış lot", "lot"), C("slot", "Pasif alış lot", "lot"),
                C("pas", "Pasif alış %", "pct"), C("push", "Fiyat iten alış lot", "lot"), C("pushp", "İten pay %", "pct"),
                C("sw", "Üst kademe süpürme", "num"), C("swlot", "Süpürülen lot", "lot"), C("chgw", "Pencere %", "chg"), C("wtl", "Pencere ₺", "tl")]
        return cols, rows, "sc"

    # 7 ------------------------------------------------- Kademeli Süpürme
    def f_supurme(self, X: dict, w="10"):
        ref = X["ref"]
        gun = w in ("gun", None)
        t0 = 0 if gun else ref - int(w) * 60
        rows = []
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or not K.bursts:
                continue
            bs = [b for b in K.bursts if b[0] >= t0 and b[1] == 1 and b[2] >= 2]
            if not bs:
                continue
            cas, cur = [], None
            for b in bs:
                if cur is None or b[0] - cur["end"] > 45 or b[5] < cur["to"] - 2 * (_tick_size(cur["to"]) or 0.01):
                    cur = {"start": b[0], "end": b[0], "n": 0, "lv": 0, "lot": 0, "tl": 0.0, "from": b[5], "to": b[6], "br": collections.Counter()}
                    cas.append(cur)
                cur["end"] = b[0]; cur["n"] += 1; cur["lv"] += b[2]; cur["lot"] += b[3]; cur["tl"] += b[4]
                cur["from"] = min(cur["from"], b[5]); cur["to"] = max(cur["to"], b[6])
                if b[7]:
                    cur["br"][b[7]] += b[3]
            B = self._base(s, X, K)
            c = B["c"] or 0.0
            best = None
            for x in cas:
                dur = max(1, x["end"] - x["start"])
                pch = (x["to"] / x["from"] - 1) * 100 if x["from"] else 0
                tk = _tick_size(x["from"]) or 0.01
                x["dl"] = min(x["lv"], int(round((x["to"] - x["from"]) / tk)) + 1)   # farklı fiyat kademesi
                speed = x["dl"] / max(1.0, dur / 60.0)
                sc = 35 * _clip(x["dl"] / 8) + 20 * _clip(x["tl"] / 5e6) + 20 * _clip(speed / 10) + 15 * _clip(pch / 2) + 10 * (1 if ((((x["from"] / X["Q"][s]["prev_close"] - 1) * 100) if X["Q"][s].get("prev_close") else c) < 5) else 0.3)
                rec = (sc, x, dur, pch, speed)
                if best is None or sc > best[0]:
                    best = rec
            sc, x, dur, pch, speed = best
            if sc < 20:
                continue
            tb = x["br"].most_common(1)
            pcl = X["Q"][s].get("prev_close")
            cw = ((x["from"] / pcl - 1) * 100) if pcl else c
            r = dict(B)
            r.update({"zaman": _hms(x["end"]), "kad": x["dl"], "top": x["lv"], "seri": x["n"], "slot": x["lot"], "stl": round(x["tl"]), "from": x["from"],
                      "to": x["to"], "pch": _r(pch), "sure": dur, "hiz": _r(speed, 1), "br": self.bname(tb[0][0]) if tb else None,
                      "du": "ERKEN" if cw < 4 else "ORTA" if cw < 7 else "GEÇ", "cw": _r(cw), "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"), C("zaman", "Son süpürme", "time"),
                C("cw", "Başlangıçta gün %", "chg"),
                C("kad", "Süpürülen kademe", "num"), C("seri", "Ardışık emir", "num"), C("top", "Toplam vurulan kademe", "num"), C("hiz", "Kademe/dk", "num"), C("slot", "Lot", "lot"),
                C("stl", "₺", "tl"), C("from", "Başlangıç", "px"), C("to", "Bitiş", "px"), C("pch", "Fiyat değişimi %", "chg"),
                C("sure", "Süre sn", "num"), C("br", "Baskın kurum", "broker"), C("du", "Evre", "txt")]
        return cols, rows, "sc"

    # 8 ------------------------------------------------- Balina İmza Algoritması
    def f_balina(self, X: dict, w="gun"):
        ref = X["ref"]
        gun = w in ("gun", None)
        t0 = 0 if gun else ref - int(w) * 60
        rows = []
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or not K.big:
                continue
            bigs = [b for b in K.big if b[0] >= t0]
            if not bigs:
                continue
            btl = sum(b[3] for b in bigs if b[4] == 1); stl = sum(b[3] for b in bigs if b[4] == 2)
            side = 1 if btl >= stl else 2
            dom = [b for b in bigs if b[4] == side]
            if not dom:
                continue
            def _key(l):
                if l <= 0:
                    return l
                e = int(math.floor(math.log10(l))) - 1
                return int(round(l / 10 ** e) * 10 ** e) if e > 0 else l
            lc = collections.Counter(_key(b[2]) for b in dom)
            lotv, rep = lc.most_common(1)[0]
            pxs = sorted(b[1] for b in dom)
            med = pxs[len(pxs) // 2]
            clu = sum(1 for p in pxs if abs(p / med - 1) <= 0.005) / len(pxs)
            bc = collections.Counter(b[5] if side == 1 else b[6] for b in dom)
            bi, bn = bc.most_common(1)[0]
            brs = bn / len(dom)
            if rep >= 3:
                tip = f"ALGORİTMA (aynı lot ×{rep})"
            elif bn >= 3 and clu >= 0.6:
                tip = "ISRARCI BÜYÜK OYUNCU"
            elif len(dom) == 1:
                tip = "TEK SEFERLİK"
            else:
                tip = "DAĞINIK BÜYÜK İŞLEMLER"
            sc = 30 * _clip(len(dom) / 15) + 25 * _clip((rep - 1) / 5) + 25 * _clip(clu) + 20 * _clip(brs)
            if len(dom) == 1:
                sc = min(sc, 30)
            r = self._base(s, X, K)
            r.update({"yon": "BALİNA ALIŞ" if side == 1 else "BALİNA SATIŞ", "vk": "AL" if side == 1 else "SAT", "nbig": len(bigs),
                      "ndom": len(dom), "btl": round(btl), "stl": round(stl), "lot": lotv, "rep": rep, "cpx": med, "clu": _r(clu * 100, 1),
                      "br": self.bname(bi), "brn": bn, "tip": tip, "son": _hms(dom[-1][0]), "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"), C("yon", "Yön", "verdict"),
                C("tip", "Sınıf", "txt"), C("ndom", "Büyük işlem", "num"), C("btl", "Büyük alış ₺", "tl"), C("stl", "Büyük satış ₺", "tl"),
                C("lot", "En sık lot", "lot"), C("rep", "Tekrar", "num"), C("cpx", "Yoğun fiyat", "px"), C("clu", "Fiyat kümelenmesi %", "pct"),
                C("br", "Kurum", "broker"), C("brn", "Kurum işlem", "num"), C("son", "Son", "time")]
        return cols, rows, "sc"

    # 9 ------------------------------------------ Fiyat Mıknatısı / Yoğunluk
    def f_miknatis(self, X: dict, w=None):
        ref = X["ref"]; mref = ref // 60
        rows = []
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or len(K.px) < 3 or not K.last:
                continue
            last = K.last
            items = sorted((p, v[0] + v[1] + v[4], v[0], v[1]) for p, v in K.px.items())
            tot = sum(x[1] for x in items)
            if tot * last < 1_000_000:
                continue
            poc = max(items, key=lambda x: x[1])
            best, bi = -1, 0
            for i in range(len(items) - 2):
                v = items[i][1] + items[i + 1][1] + items[i + 2][1]
                if v > best:
                    best, bi = v, i
            zlo, zhi = items[bi][0], items[bi + 2][0]
            zpay = best / tot
            up = [x for x in items if x[0] > zhi + 1e-9]
            ub = sum(x[2] for x in up); us = sum(x[3] for x in up)
            abu = ub / (ub + us) * 100 if (ub + us) else None
            if last > zhi + 1e-9:
                konum = "ÜSTÜNDE"; uz = (last / zhi - 1) * 100
            elif last < zlo - 1e-9:
                konum = "ALTINDA"; uz = (last / zlo - 1) * 100
            else:
                konum = "İÇİNDE"; uz = 0.0
            dk = 0
            if konum != "İÇİNDE":
                for m in range(mref, mref - 240, -1):
                    mm = K.mins.get(m)
                    if not mm:
                        continue
                    if (konum == "ÜSTÜNDE" and mm[8] <= zhi + 1e-9) or (konum == "ALTINDA" and mm[8] >= zlo - 1e-9):
                        break
                    dk = mref - m + 1
            top3 = " · ".join(f"{_fp(p)} → {_fs(v)} lot" for p, v, _, _ in sorted(items, key=lambda x: -x[1])[:3])
            if konum == "ÜSTÜNDE":
                sc = 35 * _clip(zpay / 0.5) + 35 * _clip(((abu or 50) - 50) / 40) + 30 * _clip(uz / 3)
            elif konum == "İÇİNDE":
                sc = 25 * _clip(zpay / 0.5)
            else:
                sc = 10 * _clip(zpay / 0.5)
            r = self._base(s, X, K)
            r.update({"poc": poc[0], "poclot": poc[1], "zlo": zlo, "zhi": zhi, "zpay": _r(zpay * 100, 1),
                      "konum": konum + (f" · {dk} dk" if dk else ""), "uz": _r(uz), "abu": _r(abu, 1), "top3": top3, "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"), C("poc", "Ana merkez (POC)", "px"),
                C("poclot", "POC lot", "lot"), C("zlo", "Bölge alt", "px"), C("zhi", "Bölge üst", "px"), C("zpay", "Bölge hacim payı %", "pct"),
                C("konum", "Fiyat konumu", "txt"), C("uz", "Bölgeye uzaklık %", "chg"), C("abu", "Bölge üstü aktif alış %", "pct"),
                C("top3", "En yoğun 3 fiyat", "txt")]
        return cols, rows, "sc"

    # 10 ------------------------------------ Gerçek Destek – Sahte Destek
    def f_destek(self, X: dict, w=None):
        rows = []
        for s, D in list(self.d.items()):
            if s not in X["Q"] or len(D.bids) < 3:
                continue
            K = self.k.get(s)
            last = (X["Q"][s].get("last")) or (K.last if K else None)
            if not last:
                continue
            fakes = sum(1 for p, sv in D.sup.items() if sv.get("fake"))
            best = None
            for p, l, o in D.bids[:8]:
                sv = D.sup.get(p) or {}
                pv = K.px.get(p) if K else None
                emil = pv[1] if pv else 0
                test = (pv[3] if pv else 0)
                peak = max(sv.get("peak") or l, l)
                canc = sv.get("canc") or 0.0
                fill = sv.get("fill") or 0.0
                held = last >= p - 1e-9
                if sv.get("fake") or (peak * p >= 500_000 and canc >= 0.6 * peak and fill <= 0.2 * peak):
                    kr, vk = "SAHTE DESTEK ŞÜPHESİ", "SAT"
                elif emil * p >= 300_000 and test >= 5 and held:
                    kr, vk = "GERÇEK DESTEK", "AL"
                elif l * p >= 1_000_000 and emil < 0.1 * l:
                    kr, vk = "GÖSTERMELİK (test edilmedi)", "TUT"
                else:
                    kr, vk = "ZAYIF / NORMAL", "TUT"
                sc = 40 * _clip(emil * p / 5e6) + 20 * _clip(test / 30) + 20 * _clip(l * p / 5e6) + 20 * (1 if held else 0)
                if vk == "SAT":
                    sc *= 0.5
                rec = (sc, p, l, o, emil, test, canc, kr, vk, peak)
                if best is None or (rec[8] == "AL" and best[8] != "AL") or (rec[0] > best[0] and not (best[8] == "AL" and rec[8] != "AL")):
                    best = rec
            if not best or best[0] < 10:
                continue
            sc, p, l, o, emil, test, canc, kr, vk, peak = best
            note = []
            if fakes:
                note.append(f"{fakes} seviyede gösterilip silinen emir")
            if D.src != "canlı":
                note.append("iptal ölçümü canlı seansta")
            r = self._base(s, X, K)
            r.update({"dpx": p, "goster": l, "gtl": round(l * p), "peak": peak, "emilen": emil, "test": test,
                      "tepki": _r((last / p - 1) * 100), "iptal": round(canc) if D.src == "canlı" else None, "ord": o,
                      "karar": kr, "vk": vk, "not": " · ".join(note), "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"), C("karar", "Karar", "verdict"),
                C("dpx", "Destek fiyatı", "px"), C("goster", "Görünen lot", "lot"), C("gtl", "Görünen ₺", "tl"), C("emilen", "Emilen satış lot", "lot"),
                C("test", "Test (vuruş)", "num"), C("tepki", "Fiyat tepkisi %", "chg"), C("iptal", "İptal edilen lot", "lot"),
                C("ord", "Emir sayısı", "num"), C("not", "Not", "txt")]
        return cols, rows, "sc"

    # 11 --------------------------------------- Satış Duvarı Absorpsiyon
    def f_duvar(self, X: dict, w=None):
        ref = X["ref"]; mref = ref // 60
        rows = []
        for s, D in list(self.d.items()):
            if s not in X["Q"] or not D.asks:
                continue
            K = self.k.get(s)
            last = X["Q"][s].get("last") or (K.last if K else None)
            if not last:
                continue
            asks = D.asks[:10]
            lots = sorted(l for _, l, _ in D.asks[:15])
            med = lots[len(lots) // 2] if lots else 0
            p15 = self._price_before(K, mref - 14) if K else None
            hold = bool(p15 and last >= p15 * 0.997)
            cands = []
            for p, l, o in asks:
                if l >= max(3 * med, 750_000 / p):
                    wv = D.walls.get(p) or {}
                    tr = (K.px.get(p) or [0])[0] if K else 0
                    cons = max(wv.get("fill") or 0.0, tr)
                    tuk = cons / (cons + l) if (cons + l) else 0
                    du = "EMİLİYOR" if tuk >= 0.3 and hold else "DURUYOR"
                    cands.append((p, max(wv.get("peak") or l, l), l, cons, tuk, du, False))
            for g in D.gone:
                if g[0] >= ref - 1800 and g[5] in ("SÜPÜRÜLDÜ",):
                    cands.append((g[1], g[2], 0, g[3], 1.0, "SÜPÜRÜLDÜ", True))
            if not cands:
                continue
            best = None
            for p, peak, cur, cons, tuk, du, gone in cands:
                sc = 45 * _clip(tuk / 0.8) + 20 * (1 if hold else 0) + 20 * _clip(cons * p / 5e6) + 15 * (1 if gone else 0)
                if best is None or sc > best[0]:
                    best = (sc, p, peak, cur, cons, tuk, du)
            sc, p, peak, cur, cons, tuk, du = best
            r = self._base(s, X, K)
            r.update({"wpx": p, "wpeak": peak, "wcur": cur, "wcons": round(cons), "tuk": _r(tuk * 100, 1), "wtl": round(peak * p),
                      "uz": _r((p / last - 1) * 100), "du": du, "hold": "EVET" if hold else "HAYIR", "src": D.src, "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"), C("du", "Durum", "txt"),
                C("wpx", "Duvar fiyatı", "px"), C("wpeak", "Duvar lot (zirve)", "lot"), C("wcur", "Kalan lot", "lot"), C("wcons", "Tüketilen lot", "lot"),
                C("tuk", "Tüketim %", "pct"), C("wtl", "Duvar ₺", "tl"), C("uz", "Uzaklık %", "chg"), C("hold", "Fiyat tutuyor", "txt"), C("src", "Derinlik", "txt")]
        return cols, rows, "sc"

    # 12 --------------------------------------------- Sıkışma → Patlama
    def f_sikisma(self, X: dict, w=None):
        ref = X["ref"]; mref = ref // 60; el = X["el"]
        rows = []
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or not K.last or len(K.mins) < 25:
                continue
            a20 = self._magg(K, mref - 19, mref)
            if a20["mins"] < 10 or a20["tl"] < 500_000:
                continue
            a10 = self._magg(K, mref - 9, mref); ap = self._magg(K, mref - 29, mref - 10)
            last = K.last
            band = (a20["h"] - a20["l"]) / last * 100
            rs = [(mm[6] - mm[7]) / mm[8] * 100 for m, mm in K.mins.items() if CONT_FROM // 60 + 10 <= m < CONT_TO // 60 and mm[8]]
            atr1 = sum(rs) / len(rs) if rs else 0
            comp = band / (atr1 * 4.5) if atr1 else 1.0
            yog = (a10["n"] / 10) / (ap["n"] / 20) if ap["n"] else 1.0
            ab10 = a10["lb"] / max(1, a10["lb"] + a10["ls"]); abp = ap["lb"] / max(1, ap["lb"] + ap["ls"])
            D = self.d.get(s)
            a5tl = sum(p * l for p, l, _ in D.asks[:5]) if D and D.asks else None
            rate = K.tb / el if K.tb else 0
            thin = a5tl / rate if (a5tl and rate) else None
            bg10 = sum(1 for b in K.big if b[0] >= ref - 600); bgp = sum(1 for b in K.big if ref - 1800 <= b[0] < ref - 600)
            bigc = (bg10 / 10) / (bgp / 20) if bgp else (2.0 if bg10 else 1.0)
            conds = [comp < 0.75, yog >= 1.25, ab10 >= 0.55 and ab10 > abp, thin is not None and thin <= 5, bigc >= 1.5]
            nc = sum(conds)
            sc = (20 * _clip((1 - comp) / 0.6) + 20 * _clip((yog - 1) / 1.5) + 20 * _clip((ab10 - 0.5) / 0.3)
                  + 20 * _clip(1 - (thin if thin is not None else 10) / 10) + 20 * _clip((bigc - 1) / 2))
            stg = self.stage.get(s)
            evre = None
            if comp < 0.8 and nc >= 3:
                evre = "1 · HAREKET ÖNCESİ SIKIŞMA"
                if not stg or stg.get("st") != 1 or ref - stg.get("t", 0) > 1800:
                    self.stage[s] = {"st": 1, "t": ref, "hi": a20["h"], "lo": a20["l"]}
                else:
                    stg["hi"] = max(stg["hi"], a20["h"]) if comp < 0.8 else stg["hi"]
            if stg and stg.get("st") in (1, 2) and ref - stg.get("t", 0) <= 1800:
                sw = [b for b in K.bursts if b[0] >= ref - 180 and b[1] == 1 and b[2] >= 2]
                if sw and last > stg["hi"] + 1e-9:
                    evre = "2 · KADEME SÜPÜRÜLDÜ — PATLAMA"
                    stg["st"] = 2
                    sc = min(100.0, sc + 25)
            if not evre:
                if nc < 2:
                    continue
                evre = "İZLE"
            r = self._base(s, X, K)
            r.update({"band": _r(band), "comp": _r(comp, 2), "yog": _r(yog, 2), "ab10": _r(ab10 * 100, 1), "thin": _r(thin, 1),
                      "bigc": _r(bigc, 1), "nc": nc, "evre": evre, "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"), C("evre", "Evre", "txt"),
                C("band", "20 dk bant %", "pct"), C("comp", "Sıkışma oranı", "num"), C("yog", "İşlem yoğunluğu ×", "num"),
                C("ab10", "10 dk aktif alış %", "pct"), C("thin", "Satış inceliği dk", "num"), C("bigc", "Büyük işlem artışı ×", "num"),
                C("nc", "Koşul (5)", "num")]
        return cols, rows, "sc"

    # 13 ------------------------------------------- Şerit Hızı Patlaması
    def f_serit(self, X: dict, w=None):
        if not X.get("live"):
            return self._replay(X, "serit")
        ref = X["ref"]; mref = ref // 60; el = X["el"]
        rows = []
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or K.n < 50 or not K.last:
                continue
            n60 = n15 = 0
            for sec, c in reversed(K.secq):
                if sec < ref - 59:
                    break
                if sec > ref:
                    continue
                n60 += c
                if sec >= ref - 14:
                    n15 += c
            if n60 < 15:
                continue
            base = (K.nb + K.ns) / el
            a30 = self._magg(K, mref - 31, mref - 2)
            b30 = a30["n"] / 30 if a30["n"] else 0
            ratio = n60 / max(base, 1.0)
            if ratio < 1.8:
                continue
            p3 = self._price_before(K, mref - 2)
            chg3 = (K.last / p3 - 1) * 100 if p3 else 0.0
            a1 = self._magg(K, mref - 1, mref)
            ab1 = a1["lb"] / max(1, a1["lb"] + a1["ls"])
            sc = 50 * _clip(math.log2(ratio) / 3) + 25 * (1 - _clip(abs(chg3) / 1.5)) + 25 * _clip((ab1 - 0.5) / 0.4)
            r = self._base(s, X, K)
            r.update({"n60": n60, "base": _r(base, 1), "b30": _r(b30, 1), "oran": _r(ratio, 1), "tps": _r(n15 / 15, 2), "chg3": _r(chg3),
                      "ab1": _r(ab1 * 100, 1), "du": "FİYAT HENÜZ TEPKİSİZ" if abs(chg3) < 0.7 else "FİYAT HAREKETLİ", "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"), C("n60", "Son 60 sn işlem", "num"),
                C("base", "Gün ort. işlem/dk", "num"), C("b30", "Son 30 dk ort./dk", "num"), C("oran", "Hız ×", "num"), C("tps", "İşlem/sn (15 sn)", "num"),
                C("chg3", "3 dk fiyat %", "chg"), C("ab1", "Aktif alış %", "pct"), C("du", "Durum", "txt")]
        return cols, rows, "sc"

    # 14 ---------------------------------------- Seri Uptick (Yeşil Dalga)
    def f_uptick(self, X: dict, w="15"):
        ref = X["ref"]
        gun = w in ("gun", None)
        t0 = 0 if gun else ref - int(w) * 60
        rows = []
        for s in X["Q"]:
            K = self.k.get(s)
            if not K:
                continue
            cand = [x for x in K.runs if x[1] >= t0]
            act = None
            if K.run and K.run[0] >= 3 and K.run[4] >= ref - 60:
                r0 = K.run
                act = (r0[2], r0[4], r0[0], r0[1], r0[5], r0[3], r0[6])
                cand.append(act)
            if gun and K.best_run:
                cand.append(K.best_run)
            if not cand:
                continue
            b = max(cand, key=lambda x: (x[2], x[1]))
            st, en, steps, fp, tp, lot, blot = b
            if steps < 4:
                continue
            pch = (tp / fp - 1) * 100 if fp else 0
            tl = lot * tp
            sc = 50 * _clip(steps / 10) + 25 * _clip(pch / 3) + 25 * _clip(tl / 2e6)
            r = self._base(s, X, K)
            r.update({"adim": steps, "from": fp, "to": tp, "pch": _r(pch), "sure": en - st, "lot": lot, "tl": round(tl),
                      "bp": _r(blot / lot * 100, 1) if lot else None, "zaman": _hms(en),
                      "du": "DEVAM EDİYOR" if (act is not None and b is act) else "BİTTİ", "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"), C("adim", "Ardışık yükseliş", "num"),
                C("from", "Başlangıç", "px"), C("to", "Bitiş", "px"), C("pch", "Değişim %", "chg"), C("sure", "Süre sn", "num"), C("lot", "Lot", "lot"),
                C("tl", "₺", "tl"), C("bp", "Aktif alış payı %", "pct"), C("zaman", "Saat", "time"), C("du", "Durum", "txt")]
        return cols, rows, "sc"

    # 15 ------------------------------------- Asimetrik Kayma (Slippage)
    def f_kayma(self, X: dict, w=None):
        el = X["el"]; rows = []
        for s, D in list(self.d.items()):
            q = X["Q"].get(s)
            if not q or not D.asks or not D.bids or (q.get("turnover") or 0) < 500_000:
                continue
            K = self.k.get(s)
            last = q.get("last") or (K.last if K else None)
            if not last:
                continue
            def up(x):
                tgt = last * (1 + x / 100)
                if D.asks[-1][0] < tgt - 1e-9:
                    return None
                return sum(p * l for p, l, _ in D.asks if p <= tgt + 1e-9)
            def dn(x):
                tgt = last * (1 - x / 100)
                if D.bids[-1][0] > tgt + 1e-9:
                    return None
                return sum(p * l for p, l, _ in D.bids if p >= tgt - 1e-9)
            u = {x: up(x) for x in (1, 2, 3, 4)}
            d3 = dn(3)
            ref_u = u[3] if u[3] is not None else u[2]
            if ref_u is None:
                continue
            asym = (d3 / ref_u) if (d3 and ref_u) else None
            rate = (K.tb / el) if (K and K.tb) else None
            dk = ref_u / rate if rate else None
            mb = max((b[4] for b in K.bursts if b[1] == 1), default=0) if K else 0
            tek = "EVET" if mb and mb >= ref_u else "HAYIR"
            sc = 40 * _clip(math.log2(asym) / 3 if asym and asym > 0 else 0) + 40 * (1 - _clip((dk if dk is not None else 30) / 30)) + 20 * (1 if tek == "EVET" else 0)
            r = self._base(s, X, K)
            r.update({"u1": round(u[1]) if u[1] is not None else None, "u2": round(u[2]) if u[2] is not None else None,
                      "u3": round(u[3]) if u[3] is not None else None, "u4": round(u[4]) if u[4] is not None else None,
                      "d3": round(d3) if d3 is not None else None, "asym": _r(asym, 2), "dk": _r(dk, 1), "mb": round(mb),
                      "tek": tek, "kap": ("+%4 25 kademe içinde" if u[4] is not None else "+%4 için 25 kademe yetmiyor"), "src": D.src,
                      "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"), C("u1", "+%1 için ₺", "tl"),
                C("u2", "+%2 için ₺", "tl"), C("u3", "+%3 için ₺", "tl"), C("u4", "+%4 için ₺", "tl"), C("d3", "−%3 için ₺", "tl"),
                C("asym", "Asimetri ×", "num"), C("dk", "Dakika eşdeğeri", "num"), C("mb", "Günün en büyük emri ₺", "tl"),
                C("tek", "Tek emir yeter mi", "txt"), C("kap", "Kapsam", "txt"), C("src", "Derinlik", "txt")]
        return cols, rows, "sc"

    # 16 ------------------------------------ Kurumsal Agresiflik Endeksi
    def f_agresiflik(self, X: dict, w="gun"):
        ref = X["ref"]; mref = ref // 60
        gun = w in ("gun", None)
        rows = []
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or not K.nb or (K.tb + K.ts) < 500_000:
                continue
            if gun:
                bra = K.bra; lb, ls = K.lb, K.ls; tl_all = K.tb + K.ts
            else:
                arr = self._src_arrays(s, ref - int(w) * 60 + 1, ref)
                if not arr:
                    continue
                T, P, L, SD, Bb, Ss = arr
                bra = {}; lb = ls = 0; tl_all = 0.0
                for i in range(len(T)):
                    sd = SD[i]; lot = L[i]; px = P[i]; tl = lot * px; tl_all += tl
                    if sd == 1: lb += lot
                    elif sd == 2: ls += lot
                    for bi, side in ((Bb[i], 1), (Ss[i], 2)):
                        if not bi:
                            continue
                        a = bra.get(bi)
                        if a is None:
                            a = bra[bi] = [0, 0, 0, 0, 0.0, 0.0, 0]
                        if side == 1:
                            if sd == 1: a[0] += lot; a[4] += tl
                            elif sd == 2: a[1] += lot
                            a[5] += tl
                        else:
                            if sd == 2: a[2] += lot
                            elif sd == 1: a[3] += lot
                            a[5] -= tl
                if tl_all < 200_000:
                    continue
            buyers = sorted(((bi, a) for bi, a in bra.items() if a[5] > 0 and self.bname(bi)), key=lambda x: -x[1][5])[:3]
            if not buyers or not (lb + ls):
                continue
            t_ab = sum(a[0] for _, a in buyers); t_pb = sum(a[1] for _, a in buyers)
            aggr = t_ab / (t_ab + t_pb) if (t_ab + t_pb) else 0
            net3 = sum(a[5] for _, a in buyers)
            swl = sum(a[6] for _, a in buyers) if gun else 0
            a30 = self._magg(K, mref - 29, mref)
            ab30 = a30["lb"] / max(1, a30["lb"] + a30["ls"]) if (a30["lb"] + a30["ls"]) else 0.5
            bi1, a1 = buyers[0]
            br_akt = a1[0] / (a1[0] + a1[1]) if (a1[0] + a1[1]) else 0
            sc = 40 * aggr + 30 * _clip(net3 / max(tl_all, 1) * 3) + 15 * _clip(swl / max(lb, 1) * 3) + 15 * _clip((ab30 - 0.5) / 0.4)
            sc = max(1.0, min(100.0, sc))
            r = self._base(s, X, K)
            r.update({"br": self.bname(bi1), "brakt": _r(br_akt * 100, 1), "brnet": round(a1[5]), "top3": _r(aggr * 100, 1),
                      "net3": round(net3), "mkt": _r(lb / (lb + ls) * 100, 1), "lim": _r(ls / (lb + ls) * 100, 1),
                      "swl": swl if gun else None, "ab30": _r(ab30 * 100, 1),
                      "du": "ACİL TOPLAMA" if sc >= 75 else "AGRESİF" if sc >= 55 else "SAKİN / PASİF", "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Aciliyet 1-100", "score"), C("du", "Durum", "txt"),
                C("br", "En acil alıcı kurum", "broker"), C("brakt", "Kurum aktif %", "pct"), C("brnet", "Kurum net ₺", "tl"),
                C("top3", "İlk 3 alıcı aktif %", "pct"), C("net3", "İlk 3 net ₺", "tl"), C("mkt", "Piyasa emriyle alış %", "pct"),
                C("lim", "Limitle bekleyen alış %", "pct"), C("swl", "Süpürme lot", "lot"), C("ab30", "Son 30 dk aktif alış %", "pct")]
        return cols, rows, "sc"

    # 17 ------------------------------------------- Hacimli V Dönüş
    def f_vdonus(self, X: dict, w=None):
        ref = X["ref"]; mref = ref // 60
        rows = []
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or not K.lo or not K.last or len(K.mins) < 30:
                continue
            lo, lo_m = K.lo, (K.lo_sec or 0) // 60
            pre = [(m, mm[6]) for m, mm in K.mins.items() if m < lo_m and m >= CONT_FROM // 60]
            if not pre:
                continue
            h0_m, h0 = max(pre, key=lambda x: x[1])
            drop = (h0 - lo) / h0 * 100
            if drop < 2.0 or lo_m - h0_m < 15:
                continue
            reb_min = mref - lo_m
            if reb_min < 3 or reb_min > 180:
                continue
            last = K.last
            retr = (last - lo) / (h0 - lo) if h0 > lo else 0
            if retr < 0.2:
                continue
            ad = self._magg(K, h0_m, lo_m); ar = self._magg(K, lo_m, mref)
            volr = (ar["tl"] / max(1, ar["mins"])) / (ad["tl"] / max(1, ad["mins"])) if ad["tl"] else 0
            abr = ar["lb"] / max(1, ar["lb"] + ar["ls"]); abd = ad["lb"] / max(1, ad["lb"] + ad["ls"])
            after = [mm[7] for m, mm in K.mins.items() if lo_m + 3 <= m <= mref]
            hl = bool(after) and min(after) > lo + 1e-9
            small = K.small_s / max(1, K.ns) * 100
            if retr >= 0.5 and volr >= 1.3 and abr >= 0.58 and hl:
                evre = "ONAYLI V DÖNÜŞ"
            elif retr >= 0.25 and abr >= 0.55:
                evre = "V BAŞLANGICI"
            else:
                evre = "İZLE"
            sc = 25 * _clip(drop / 6) + 25 * _clip((volr - 0.8) / 1.7) + 25 * _clip((abr - 0.5) / 0.35) + 25 * _clip(retr / 0.7)
            r = self._base(s, X, K)
            r.update({"dusus": _r(-drop), "tepe": h0, "dip": lo, "dipz": _hms(K.lo_sec), "retr": _r(retr * 100, 1), "volr": _r(volr, 2),
                      "abr": _r(abr * 100, 1), "abd": _r(abd * 100, 1), "kucuk": _r(small, 1), "hl": "EVET" if hl else "HAYIR",
                      "evre": evre, "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Skor", "score"), C("evre", "Evre", "txt"),
                C("dusus", "Düşüş %", "chg"), C("tepe", "Tepe", "px"), C("dip", "Dip", "px"), C("dipz", "Dip saati", "time"),
                C("retr", "Geri alınan %", "pct"), C("volr", "Dönüş hacmi ×", "num"), C("abr", "Dönüşte aktif alış %", "pct"),
                C("abd", "Düşüşte aktif alış %", "pct"), C("kucuk", "Küçük satış payı %", "pct"), C("hl", "Yükselen dip", "txt")]
        return cols, rows, "sc"

    # 18 ----------------------------------------- Gerçek mi Fake mi Yükseliş
    def f_gercek(self, X: dict, w=None):
        ref = X["ref"]; mref = ref // 60
        rows = []
        prog = _clip(X["el"] / 480.0, 0.02, 1.0)
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or not K.last:
                continue
            a15 = self._magg(K, mref - 14, mref)
            if a15["tl"] < 500_000 or not (a15["lb"] + a15["ls"]):
                continue
            p0 = self._price_before(K, mref - 14)
            if not p0:
                continue
            chg15 = (K.last / p0 - 1) * 100
            ab15 = a15["lb"] / (a15["lb"] + a15["ls"])
            if chg15 < 0.8 or ab15 < 0.55:
                continue
            q = X["Q"][s]
            rvol = None
            try:
                av = self.op.bars.avg_vol(s, 20) if self.op else None
                if av:
                    rvol = (q.get("volume") or 0) / prog / av
            except Exception:
                rvol = None
            arr = self._src_arrays(s, ref - 899, ref)
            alici, konc, wash = 0, 1.0, 0.0
            if arr:
                T, P, L, SD, Bb, Ss = arr
                cnt = collections.Counter(); tot = 0; sl = 0
                for i in range(len(T)):
                    if Bb[i] and Bb[i] == Ss[i]:
                        sl += L[i]
                    tot += L[i]
                    if SD[i] == 1:
                        cnt[Bb[i]] += L[i]
                ts_ = sum(cnt.values()) or 1
                alici = sum(1 for v in cnt.values() if v / ts_ >= 0.02)
                konc = (cnt.most_common(1)[0][1] / ts_) if cnt else 1.0
                wash = sl / tot if tot else 0.0
            follow = (K.last - a15["l"]) / (a15["h"] - a15["l"]) if a15["h"] > a15["l"] else 1.0
            D = self.d.get(s)
            canc = None; fk = 0
            if D and X["live"]:
                ev = [e for e in D.evq if e[0] >= ref - 900]
                badd = sum(e[4] for e in ev); bc = sum(e[5] for e in ev)
                canc = bc / badd if badd else None
                fk = sum(1 for f in D.fakes if f[0] >= ref - 900)
            sc = (25 * _clip((rvol or 1.0) / 2) + 20 * _clip(alici / 8) * (1 - 0.5 * _clip((konc - 0.5) / 0.4)) + 20 * _clip(follow)
                  + 15 * (1 - _clip(canc if canc is not None else 0.5)) - 5 * min(fk, 3) + 10 * (1 - _clip(wash * 5)) + 10 * _clip(a15["tl"] / 5e6))
            sc = max(0.0, min(100.0, sc))
            neg, pos = [], []
            (pos if (rvol or 0) >= 1.5 else neg).append(f"RVOL {_r(rvol, 1) if rvol else '—'}")
            (pos if alici >= 6 else neg).append(f"{alici} alıcı kurum")
            if konc >= 0.6: neg.append(f"tek kurum %{konc * 100:.0f}")
            (pos if follow >= 0.7 else neg).append(f"zirveye yakınlık %{follow * 100:.0f}")
            if canc is not None: (neg if canc >= 0.6 else pos).append(f"alış iptal %{canc * 100:.0f}")
            if fk: neg.append(f"{fk} sahte emir")
            if wash >= 0.05: neg.append(f"çapraz/aynı kurum %{wash * 100:.0f}")
            if sc >= 65:
                kr, vk = "GERÇEK · hacim destekli", "AL"
            elif sc >= 45:
                kr, vk = "ŞÜPHELİ · teyit bekle", "TUT"
            else:
                kr, vk = "FAKE RİSKİ YÜKSEK", "SAT"
            r = self._base(s, X, K)
            r.update({"chg15": _r(chg15), "ab15": _r(ab15 * 100, 1), "rvol": _r(rvol, 2), "alici": alici, "konc": _r(konc * 100, 1),
                      "takip": _r(follow * 100, 1), "iptal": _r(canc * 100, 1) if canc is not None else None, "wash": _r(wash * 100, 2),
                      "karar": kr, "vk": vk, "neden": ("✓ " + ", ".join(pos) if pos else "") + (" ✗ " + ", ".join(neg) if neg else ""),
                      "tl15": round(a15["tl"]), "sc": round(sc, 1)})
            rows.append(r)
        cols = [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sc", "Gerçeklik skoru", "score"), C("karar", "Karar", "verdict"),
                C("chg15", "15 dk %", "chg"), C("ab15", "Aktif alış %", "pct"), C("rvol", "RVOL", "num"), C("alici", "Alıcı kurum", "num"),
                C("konc", "Tek kurum payı %", "pct"), C("takip", "Zirveye yakınlık %", "pct"), C("iptal", "Alış iptal %", "pct"),
                C("wash", "Çapraz %", "pct"), C("tl15", "15 dk ₺", "tl"), C("neden", "Gerekçe", "txt")]
        return cols, rows, "sc"


    # ------------------------------------------- seans dışı: gün içi tekrar --
    def _replay(self, X: dict, kind: str):
        """Piyasa kapalıyken: kayıtlı günün dakika verisi üzerinde sinyali her dakika için yeniden hesaplar,
        her hisse için günün en güçlü anını ve SONRASINDA (15 dk / gün sonu) ne olduğunu gösterir."""
        key = (kind, self.day, self.ingested)
        hit = getattr(self, "_rp_cache", {}).get(key)
        if hit:
            return hit
        rows = []
        m_from = CONT_FROM // 60 + 3
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or not K.mins or K.n < 50:
                continue
            ms = sorted(K.mins)
            mins = K.mins
            pc = X["Q"][s].get("prev_close")
            ce = X["Q"][s].get("ceiling")
            # burst'leri dakikaya kovala
            bm = collections.defaultdict(lambda: [0, 0])
            for b in K.bursts:
                if b[1] == 1 and b[2] >= 2:
                    x = bm[b[0] // 60]; x[0] += 1; x[1] += b[3]
            cum_n = cum_tl = 0; cum_m = 0
            last_close = None
            closes = {}
            best = None
            prev3 = collections.deque(maxlen=4)
            for m in range(ms[0], ms[-1] + 1):
                mm = mins.get(m)
                if mm:
                    closes[m] = mm[8]
                    last_close = mm[8]
                if m * 60 < CONT_FROM or m * 60 > CONT_TO:
                    if mm:
                        cum_n += mm[0]; cum_tl += mm[2]; cum_m += 1
                    prev3.append(last_close)
                    continue
                if m >= m_from and last_close and len(prev3) >= 3 and prev3[0]:
                    el = max(1.0, (m * 60 - CONT_FROM) / 60.0)
                    if kind == "pozitif":
                        a3 = self._magg(K, m - 2, m)
                        if a3["tl"] >= 200_000 and a3["lb"]:
                            p_prev = prev3[-3] if prev3[-3] else prev3[0]
                            chg3 = (last_close / p_prev - 1) * 100 if p_prev else 0
                            p1 = prev3[-1] or p_prev
                            chg1 = (last_close / p1 - 1) * 100 if p1 else 0
                            if chg3 > 0.15:
                                acc = chg1 - (chg3 - chg1) / 2.0
                                ab3 = a3["lb"] / max(1, a3["lb"] + a3["ls"])
                                swn = sum(bm[x][0] for x in (m - 2, m - 1, m) if x in bm)
                                swlot = sum(bm[x][1] for x in (m - 2, m - 1, m) if x in bm)
                                rate = cum_tl / el if cum_tl else 0
                                vr = (a3["tl"] / 3.0) / rate if rate else 0.0
                                c = (last_close / pc - 1) * 100 if pc else 0
                                sc = 30 * _clip(chg3 / 2) + 25 * _clip((ab3 - 0.5) / 0.45) + 20 * _clip(vr / 5) + 15 * _clip(swn / 3) + 10 * _clip(acc / 0.8)
                                if c > 8:
                                    sc *= 0.6
                                if sc >= 25 and (best is None or sc > best["sc"]):
                                    best = {"m": m, "sc": round(sc, 1), "chg3": _r(chg3), "chg1": _r(chg1), "acc": _r(acc), "ab3": _r(ab3 * 100, 1),
                                            "sw": swn, "swlot": swlot, "bigb": a3["bigb"], "as3": a3["ls"], "vr": _r(vr, 1), "tl3": round(a3["tl"]),
                                            "pz": last_close, "cz": _r(c),
                                            "du": ("ERKEN" if c < 4 else "ORTA" if c < 7 else "GEÇ") + (f" · tavana {_pc((ce / last_close - 1) * 100)}" if ce else "")}
                    else:   # serit
                        if mm and mm[0] >= 20 and cum_m >= 5:
                            base = cum_n / el
                            ratio = mm[0] / max(base, 1.0)
                            if ratio >= 3:
                                p3 = prev3[-3] or prev3[0]
                                chg3 = (last_close / p3 - 1) * 100 if p3 else 0
                                ab1 = mm[3] / max(1, mm[3] + mm[4])
                                sc = 50 * _clip(math.log2(ratio) / 3) + 25 * (1 - _clip(abs(chg3) / 1.5)) + 25 * _clip((ab1 - 0.5) / 0.4)
                                if best is None or sc > best["sc"]:
                                    best = {"m": m, "sc": round(sc, 1), "n60": mm[0], "base": _r(base, 1), "oran": _r(ratio, 1),
                                            "tps": _r(mm[0] / 60, 2), "chg3": _r(chg3), "ab1": _r(ab1 * 100, 1), "pz": last_close,
                                            "du": "FİYAT HENÜZ TEPKİSİZ" if abs(chg3) < 0.7 else "FİYAT HAREKETLİ"}
                if mm:
                    cum_n += mm[0]; cum_tl += mm[2]; cum_m += 1
                prev3.append(last_close)
            if not best:
                continue
            m = best.pop("m")
            pz = best.pop("pz")
            after = None
            for x in range(m + 15, m, -1):
                if x in closes:
                    after = closes[x]; break
            r = self._base(s, X, K)
            r.update(best)
            r["zaman"] = _hm(m * 60)
            r["pz"] = pz
            r["s15"] = _r((after / pz - 1) * 100) if (after and pz) else None
            r["sgun"] = _r((K.last / pz - 1) * 100) if (K.last and pz) else None
            rows.append(r)
        if kind == "pozitif":
            cols = [C("s", "Hisse", "sym"), C("zaman", "Sinyal anı", "time"), C("pz", "O anki fiyat", "px"), C("sc", "Skor", "score"),
                    C("s15", "Sonraki 15 dk %", "chg"), C("sgun", "Gün sonuna %", "chg"), C("chg3", "3 dk %", "chg"), C("chg1", "1 dk %", "chg"),
                    C("acc", "İvme", "num"), C("ab3", "Aktif alış %", "pct"), C("sw", "Süpürme", "num"), C("swlot", "Süpürülen lot", "lot"),
                    C("bigb", "Balina alış lot", "lot"), C("as3", "Aktif satış lot", "lot"), C("vr", "Hacim hızı ×", "num"),
                    C("tl3", "3 dk ₺", "tl"), C("du", "Evre", "txt"), C("p", "Kapanış", "px"), C("c", "Gün %", "chg")]
        else:
            cols = [C("s", "Hisse", "sym"), C("zaman", "Sinyal anı", "time"), C("pz", "O anki fiyat", "px"), C("sc", "Skor", "score"),
                    C("s15", "Sonraki 15 dk %", "chg"), C("sgun", "Gün sonuna %", "chg"), C("n60", "O dakika işlem", "num"),
                    C("base", "Gün ort. işlem/dk", "num"), C("oran", "Hız ×", "num"), C("tps", "İşlem/sn", "num"),
                    C("chg3", "3 dk fiyat %", "chg"), C("ab1", "Aktif alış %", "pct"), C("du", "Durum", "txt"), C("p", "Kapanış", "px"), C("c", "Gün %", "chg")]
        out = (cols, rows, "sc")
        if not hasattr(self, "_rp_cache"):
            self._rp_cache = {}
        self._rp_cache = {k: v for k, v in self._rp_cache.items() if k[1] == self.day and k[2] == self.ingested}
        self._rp_cache[key] = out
        return out


# ================================================================ CATALOG ==
W_ALL = [["1", "1 DK"], ["5", "5 DK"], ["15", "15 DK"], ["30", "30 DK"], ["60", "60 DK"], ["gun", "GÜN"]]
# id: (başlık, kısa ad, bildirim türü, varsayılan mod, kısa açıklama, pencereler, varsayılan pencere, derinlik tabanlı)
CAT = {
    "k_islem": ("İşlem Analizi (Tüm Hisseler)", "İŞLEM ANALİZİ", "k_islem", "view",
                "Tüm hisselerin gerçekleşen işlemleri: aktif alış % / aktif satış %, en çok tekrar eden fiyat ve lot, alış-satış ortalama fiyatı, en güçlü destek ve direnç fiyatı.",
                W_ALL, "15", False),
    "k_kurumfiyat": ("Kurumların En Çok Alım-Satım Fiyat Analizi", "KURUM FİYAT", "k_kurumfiyat", "off",
                     "Her hissede her kurumun en çok lot aldığı / sattığı fiyat, o fiyattaki lot ve işlem adedi, ortalama fiyatı ve aktiflik oranı.",
                     [["15", "15 DK"], ["30", "30 DK"], ["60", "60 DK"], ["gun", "GÜN"]], "gun", False),
    "k_pozitif": ("Pozitif Anlık Hareketlilik", "ANLIK HAREKET", "k_pozitif", "notify",
                  "Ani fiyat ivmesi + piyasa emriyle yukarı süpüren alıcılar + neredeyse hiç satıcı yok: +%2-3 koşabilecek hisseleri erken yakalar.", None, None, False),
    "k_koruma": ("Yakın Kademe Koruması", "KADEME KORUMA", "k_koruma", "view",
                 "Fiyatın hemen altındaki ilk 3-4 alış kademesi çok yüklü, kırılması zor hisseler.", None, None, True),
    "k_bosluk": ("Satış Kademesi Boşluğu", "SATIŞ BOŞLUĞU", "k_bosluk", "view",
                 "Satış kademeleri ince / boşluklu: az alımla fiyat kolayca yukarı gidebilir.", None, None, True),
    "k_otoban": ("Otoban Kademe", "OTOBAN", "k_otoban", "notify",
                 "Boş satış kademeleri + o boşluğa doğru sert aktif alışla iten kurum(lar): yol açık, itici var.", None, None, True),
    "k_doldur": ("Doldur-Boşalt Kademe", "DOLDUR-BOŞALT", "k_doldur", "view",
                 "Alışa yüklü emir yazılırken satış emirleri siliniyor / aktif alışla süpürülüyor: arkası sağlam, yol açılıyor.", None, None, True),
    "k_baski": ("Aktif Alış Baskı Endeksi", "BASKI ENDEKSİ", "k_baski", "view",
                "Aktif alış lotu ÷ aktif satış lotu + üst kademeleri süpüren alımlara ek puan; pasif alış ile fiyatı iten aktif alış ayrılır.",
                W_ALL, "5", False),
    "k_supurme": ("Kademeli Süpürme Tespiti", "SÜPÜRME", "k_supurme", "notify",
                  "Satış kademeleri 5→4→3→2→1 hızla art arda süpürülüyor; hız + lot + fiyat değişimi, fiyat çok yükselmeden erken yakalama.",
                  [["5", "5 DK"], ["10", "10 DK"], ["30", "30 DK"], ["60", "60 DK"], ["gun", "GÜN"]], "10", False),
    "k_balina": ("Balina İmza Algoritması", "BALİNA İMZA", "k_balina", "view",
                 "Olağandışı büyük lotlar, aynı/benzer büyüklükte tekrarlar ve aynı fiyatta kümelenme; tek seferlik büyük işlem ile ısrarcı büyük oyuncuyu ayırır.",
                 [["30", "30 DK"], ["60", "60 DK"], ["gun", "GÜN"]], "gun", False),
    "k_miknatis": ("Fiyat Mıknatısı / İşlem Yoğunluk Bölgesi", "MIKNATIS", "k_miknatis", "view",
                   "Gün içinde en çok hacmin döndüğü fiyatlar ve ana işlem merkezi; fiyat merkezin üstüne çıkınca davranış değişimi.", None, None, False),
    "k_destek": ("Gerçek Destek – Sahte Destek Ayrımı", "GERÇEK DESTEK", "k_destek", "view",
                 "Yalnızca büyük alış lotuna bakmaz: o seviyeye gelen satışlar gerçekten emildi mi, kaç kez test edildi, fiyat tepkisi ve gösterilip silinen emirler.", None, None, True),
    "k_duvar": ("Satış Duvarı Absorpsiyon Algılama", "DUVAR EMİLİM", "k_duvar", "notify",
                "Büyük satış duvarı sürekli aktif alış yiyor, fiyat düşmüyor → emilim; duvarın tamamen süpürülmesi takip edilir.", None, None, True),
    "k_sikisma": ("Sıkışma → Patlama Radarı", "SIKIŞMA RADARI", "k_sikisma", "notify",
                  "Fiyat dar bantta sıkışırken işlem yoğunluğu, aktif alış oranı ve büyük işlemler artıyor (Evre 1); ilk gerçek kademe süpürmesi (Evre 2).", None, None, False),
    "k_serit": ("Şerit Hızı (Tape Speed) Patlaması", "ŞERİT HIZI", "k_serit", "view",
                "Saniyedeki işlem sayısında (lottan bağımsız) olağandışı artış — fiyat henüz hareket etmeden.", None, None, False),
    "k_uptick": ("Seri Uptick (Yeşil Dalga) Süpürmesi", "YEŞİL DALGA", "k_uptick", "view",
                 "Her biri bir öncekinden yüksek fiyattan gerçekleşen kesintisiz işlem serisi.",
                 [["15", "15 DK"], ["60", "60 DK"], ["gun", "GÜN"]], "15", False),
    "k_kayma": ("Asimetrik Kayma (Slippage) Fırsatları", "KAYMA", "k_kayma", "off",
                "Satış defteri o kadar sığ ki tek büyük piyasa emri fiyatı anında +%3-4 kaldırabilir; +%1/+%2/+%3/+%4 için gereken ₺.", None, None, True),
    "k_agresiflik": ("Kurumsal Agresiflik Endeksi (Aggressor Ratio)", "AGRESİFLİK", "k_agresiflik", "view",
                     "Piyasa emriyle (agresif) alanlar ile limit emirle bekleyenler; toplama aciliyeti 1-100, kurum bazında.",
                     [["15", "15 DK"], ["60", "60 DK"], ["gun", "GÜN"]], "gun", False),
    "k_vdonus": ("Hacimli V Dönüş Analizi", "V DÖNÜŞ", "k_vdonus", "notify",
                 "Gün içi baskılanıp küçük yatırımcının silkelendiği hisselerde dipten ani, yüksek hacimli agresif alımla gerçek V dönüş başlangıcı.", None, None, False),
    "k_gercek": ("Gerçek mi Fake mi Yükseliş", "GERÇEK/FAKE", "k_gercek", "view",
                 "Aktif alışla süpürülen hissede yükseliş gerçekten hacim destekli mi: RVOL, kurum genişliği/yoğunlaşma, takip, iptal edilen emirler, çapraz işlem → karar.", None, None, False),
}
ORDER = ["k_islem", "k_kurumfiyat", "k_pozitif", "k_koruma", "k_bosluk", "k_otoban", "k_doldur", "k_baski", "k_supurme", "k_balina",
         "k_miknatis", "k_destek", "k_duvar", "k_sikisma", "k_serit", "k_uptick", "k_kayma", "k_agresiflik", "k_vdonus", "k_gercek"]
NT_DEFAULTS = {v[2]: v[3] for v in CAT.values()}


def _fold(s: str) -> str:
    return (s or "").translate(str.maketrans("İIıŞşĞğÜüÖöÇç", "iiissgguuoocc")).lower()


# ================================================================== HELP ==
# Her özellik için: ne işe yarar · nasıl hesaplanır · nasıl kullanılır · dikkat edilmesi gerekenler · örnek
HELP = {
    "k_islem": {
        "ne": "Tüm BIST paylarının gerçekleşen işlemlerini tek ekranda toplar. Hisse sayfasındaki İŞLEMLER sekmesinin 'hacme göre' görünümündeki fiyat bazlı Alış%-Satış% (aktiften) hesabını tüm hisselere uygular; hangi hissede alıcıların aktiften çizdiğini (satıcıları sildiğini) gösterir.",
        "nasil": "Seçilen penceredeki (son 1/5/15/30/60 dk veya gün) her işlem, aracı olan tarafa göre ayrılır: alıcının piyasa emri satış kademesine çarptıysa AKTİF ALIŞ, satıcının emri alış kademesine çarptıysa AKTİF SATIŞ. Aktif alış % = aktif alış lot ÷ (aktif alış + aktif satış lot). En çok tekrar eden fiyat = en çok işlem adedi olan fiyat; en çok tekrar eden lot = aynı lot büyüklüğünün adet sayısı (≥15 ve işlemlerin ≥%4'ü ise 'ALGO?' işareti). Ort. alış fiyatı = aktif alışların ağırlıklı ortalaması, ort. satış fiyatı = aktif satışlarınki; 'Alış-satış farkı %' pozitifse alıcılar fiyatı yukarı taşıyarak ödüyor. Güçlü destek = son fiyat ve altındaki fiyatlar içinde en çok aktif satışın emildiği fiyat (satıcılar vurdu, alıcılar karşıladı, fiyat aşağı kırılmadı); güçlü direnç = son fiyat ve üstündeki fiyatlar içinde en çok aktif alışın karşılandığı fiyat (alıcılar vurdu ama satıcılar geçit vermedi). Skor = aktif alış % × hacim ağırlığı.",
        "nasil_kullan": "Pencereyi seçin (alım dalgasının başlangıcını yakalamak için 1-5 dk, genel resim için 15-60 dk/gün). 'Aktif alış %' sütununa dokunarak sıralayın. 'ALICI SATICIYI SİLİYOR' durumundaki ve 'Net aktif ₺' yüksek hisseler en güçlü alım baskısını gösterir. Hisseye dokununca hisse sayfası açılır.",
        "dikkat": "Kısa pencerelerde az işlemli hisselerde yüzde yanıltıcı olabilir — 'Pencere ₺' ve 'İşlem' sütunlarına bakın. Açılış/kapanış seansı (tek fiyat) eşleşmeleri aktif alış/satış sayılmaz. Destek/direnç günün işlem dağılımından hesaplanır, emir defterinden değil.",
        "ornek": "THYAO son 5 dk: aktif alış %86, aktif alış 42 Mn ₺, en çok tekrar 292,00 ₺ (318 işlem), en çok lot 500 ×64 (ALGO?), güçlü destek 291,75 ₺ (1,2 Mn lot emildi), güçlü direnç 292,25 ₺."},
    "k_kurumfiyat": {
        "ne": "Her hissede her aracı kurumun en çok hangi fiyattan aldığını / sattığını, o fiyatta kaç lot ve kaç işlem yaptığını gösterir. Kurumun maliyet bölgesini ve ısrarla savunduğu fiyatı ortaya çıkarır.",
        "nasil": "Kayıtlı tüm işlemler (alıcı ve satıcı kurum bilgisiyle) kurum × yön × fiyat bazında toplanır. 'En çok lot fiyatı' en yüksek lotun gerçekleştiği fiyat, 'En çok tekrar fiyat' en çok işlem adedinin olduğu fiyattır. Ort. fiyat = ağırlıklı ortalama. Aktif % = kurumun piyasa emriyle (karşı kademeye vurarak) yaptığı payı. Yön payı = kurumun o hissedeki tüm alış (veya satış) lotu içindeki payı.",
        "nasil_kullan": "Arama kutusuna hisse kodu yazın (ör. ASELS) → o hissedeki TÜM kurumlar; kurum adı yazın (ör. Ak Yatırım) → o kurumun tüm hisseleri. Varsayılan listede her hissenin en büyük 3 alıcı ve 3 satıcı kurumu yer alır. Pencere ile son 15/30/60 dk'ya daraltın.",
        "dikkat": "Kurum adı işlem anında İdealData'nın bildirdiği aracıdır; takas/AKD ile birebir aynı olmayabilir (AKD gün sonu düzeltmeleri içerir). Çapraz (aynı kurumun iki tarafta olduğu) işlemler her iki tarafa da yazılır.",
        "ornek": "ASELS · Ak Yatırım · ALIŞ · en çok lot fiyatı 182,40 ₺ → 410 bin lot / 236 işlem (%38), toplam 1,1 Mn lot, ort. 182,61 ₺, aktif %72."},
    "k_pozitif": {
        "ne": "Ani ve agresif yükselen hisseleri erken yakalar: fiyat hızlanıyor, alıcılar piyasa emriyle üst kademeleri süpürüyor, satıcı neredeyse yok. Henüz çok yükselmemiş (+%2-3 ve üzeri koşabilecek) hisseler öne çıkar.",
        "nasil": "Son 3 dk fiyat değişimi, son 1 dk değişimi ve ivme (son dakika − önceki ortalama), 3 dk aktif alış %, aynı saniyede birden çok kademeyi süpüren alış emri sayısı, balina (olağandışı büyük) alış lotu ve dakika başı hacmin gün ortalamasına oranı birleştirilir. Skor = 30×fiyat + 25×aktif alış + 20×hacim hızı + 15×süpürme + 10×ivme; gün içinde zaten +%8 üstündeyse skor düşürülür (geç kalınmış).",
        "nasil_kullan": "Skora göre sıralı listeyi izleyin; 'Evre' sütununda ERKEN olanlar henüz koşmamış hisselerdir. Bildirim türünü BİLDİRİM yaparsanız skor ≥75 ve 3 dk hacim ≥1 Mn ₺ olunca anında haber verilir.",
        "dikkat": "Çok sığ hisselerde tek emir skoru şişirebilir — 3 dk ₺ sütununa bakın. Haber/KAP kaynaklı ani hareketlerde geri çekilme sert olabilir; stop seviyesi belirleyin.",
        "ornek": "KONTR 3 dk +%1,9, 1 dk +%0,9 (ivme +0,4), aktif alış %94, 4 süpürme (180 bin lot), hacim hızı 6,3× → skor 88, evre ERKEN · tavana +%6,1."},
    "k_koruma": {
        "ne": "Fiyatın hemen altındaki ilk 3-4 alış kademesi olağandışı yüklü olan, kırılması zor (güçlü korunan) hisseleri listeler.",
        "nasil": "25 kademe derinlikten ilk 4 alış kademesindeki lot ve ₺ toplanır. Alış/Satış × = ilk 4 alış ÷ ilk 4 satış lotu. Kalınlık × = ilk 4 kademenin ortalaması ÷ 5-15. kademelerin ortalaması. Kırma süresi = ilk 4 alış lotu ÷ günün dakika başına ortalama aktif satış lotu (bu hızda satışla kaç dakikada eritilir). Skor = 35×oran + 35×kırma süresi + 30×kalınlık.",
        "nasil_kullan": "Yüksek skorlu hisselerde aşağı yönlü risk sınırlıdır; destek üstünde alım düşünülebilir. 'En güçlü kademe' en yüklü alış fiyatıdır. Gerçek mi sahte mi olduğunu 'Gerçek Destek – Sahte Destek' ekranıyla doğrulayın.",
        "dikkat": "Büyük alış emirleri iptal edilebilir (spoofing). Seans dışında son derinlik görüntüsü gösterilir.",
        "ornek": "EREGL: ilk 4 alış 3,2 Mn lot (95 Mn ₺), satışın 3,4 katı, kırma süresi 41 dk, kalınlık 2,8× → skor 91."},
    "k_bosluk": {
        "ne": "Satış tarafı ince veya kademeler arası boşluklu hisseleri bulur: az alımla fiyat kolayca yukarı gidebilir.",
        "nasil": "İlk 5 satış kademesinin lot ve ₺ toplamı alınır. Temizleme dk = bu ₺ ÷ günün dakika başına aktif alış ₺ (mevcut alış hızıyla 5 kademe kaç dakikada biter). Boş kademe = ilk 5 satış fiyatı arasında emir olmayan fiyat adımı sayısı. 5 kademe sonrası % = 5. satış kademesinin son fiyata uzaklığı. Skor = 40×(hızlı temizlenme) + 25×boşluk + 20×alış/satış oranı + 15×yükselme payı.",
        "nasil_kullan": "Temizleme süresi 1-3 dk olan ve alış tarafı daha kalın hisseler 'yolu açık' hisselerdir. Otoban Kademe ekranı bu boşluğa doğru iten alıcıyı da arar.",
        "dikkat": "Günlük hacmi 1 Mn ₺ altındaki hisseler elenir. İnce defter iki yönlüdür: satıcı gelirse fiyat aşağı da kolay gider.",
        "ornek": "ODAS: ilk 5 satış 0,9 Mn ₺, temizleme 1,2 dk, 3 boş kademe, 5 kademe sonrası +%1,8 → skor 84."},
    "k_otoban": {
        "ne": "'Otoban' = satış kademeleri boş VE bir veya birkaç kurum sert aktif alışla fiyatı bu boşluğa doğru itmeye başlamış. Yol açık + itici var.",
        "nasil": "Satış Kademesi Boşluğu ölçüleri + son 5 dk aktif alış %, son 5 dk aktif alış ₺, itme gücü (5 dk aktif alış ₺ ÷ ilk 5 satış kademesi ₺; 1× = mevcut hızla 5 dk'da yol biter), üst kademe süpürme sayısı ve son 5 dk'nın en çok aktif alan kurumu. Skor = 0,45×boşluk skoru + 30×aktif alış + 15×itme + 10×süpürme.",
        "nasil_kullan": "İtme gücü ≥1 ve iten kurum payı yüksek olanlar en kuvvetlileridir. BİLDİRİM modunda skor ≥75 olunca haber verilir.",
        "dikkat": "İten kurum bir anda durabilir; satış tarafına yeni emir yazılıyorsa (Doldur-Boşalt ekranı) yol kapanıyor demektir.",
        "ornek": "SASA: 5 kademe 1,4 Mn ₺, 5 dk aktif alış %81 (3,9 Mn ₺), itme 2,8×, 3 süpürme, iten kurum Bank of America %46 → skor 86."},
    "k_doldur": {
        "ne": "Alış tarafına yüklü emir yazılırken satış emirleri iptal ediliyor veya aktif alışla süpürülüyor: arkada sağlam destek, önde açılan yol.",
        "nasil": "Her ~2 sn'lik derinlik görüntüsü öncekiyle karşılaştırılır. Kademedeki lot azalışı, o fiyatta gerçekleşen işlemle açıklanıyorsa 'süpürülen', açıklanamıyorsa 'silinen (iptal)'; artış 'yazılan' sayılır. Son 5 dk: alışa yazılan − alıştan silinen (net alış), satıştan silinen + süpürülen, ilk 5 satış ve alış kademesinin % değişimi. Skor = 30×net alış + 30×satış boşalması + 20×satış azalması + 20×alış artışı.",
        "nasil_kullan": "'YOL AÇILIYOR' durumunda satış 5 kademe hızla erirken alış büyüyordur — süpürme/otoban sinyalleriyle birlikte güçlüdür.",
        "dikkat": "Fark ölçümü yalnızca canlı seansta yapılır; piyasa kapalıyken son derinlik görüntüsünden yalnızca alış/satış dengesi gösterilir ('SON GÖRÜNTÜ'). Görünür 25 kademenin dışına itilen emirler iptal sayılmaz.",
        "ornek": "PGSUS son 5 dk: alışa 18 Mn ₺ yazıldı, satıştan 6 Mn ₺ silindi + 4 Mn ₺ süpürüldü, satış 5 kademe −%42, alış 5 kademe +%35 → YOL AÇILIYOR, skor 82."},
    "k_baski": {
        "ne": "Alım baskısının gücünü tek sayıda toplar: aktif alış lotunun aktif satış lotuna oranı + üst kademeleri süpüren alımlara ek puan. Pasif alış (bekleyen alış emirlerinin karşılanması) ile fiyatı yukarı iten aktif alış ayrı gösterilir.",
        "nasil": "Pencere içinde: Aktif alış / satış × = aktif alış lot ÷ aktif satış lot. Pasif alış lot = satıcının vurduğu, bekleyen alış emirleriyle gerçekleşen lot. Fiyat iten alış = önceki işlemden YÜKSEK fiyattan gerçekleşen aktif alış lotu. Süpürme = aynı saniyede ≥2 kademeyi alan emirler. Endeks = 55×log₂(oran)/3 + 25×iten pay×2 + 20×süpürme payı×2 (0-100).",
        "nasil_kullan": "Varsayılan pencere 5 dk; 1 dk ani dalgaları, gün genel eğilimi gösterir. Endeks ≥85 ve pencere ₺ ≥2 Mn olunca bildirim.",
        "dikkat": "Oran tek başına yeterli değildir: aktif alış yüksek ama 'iten pay' düşükse alıcılar aynı fiyattan topluyor, fiyatı itmiyordur.",
        "ornek": "KCHOL 5 dk: aktif alış 820 bin lot, pasif alış 190 bin, oran 4,3×, fiyat iten %34, 5 süpürme → endeks 79."},
    "k_supurme": {
        "ne": "Satış kademelerinin 5→4→3→2→1 sırasıyla kısa sürede art arda süpürüldüğü 'kademeli süpürme' dalgalarını yakalar; fiyat çok yükselmeden erken uyarı verir.",
        "nasil": "Aynı saniyede aynı yönde ardışık gerçekleşen işlemler tek agresif emir sayılır; ≥2 farklı fiyat = kademe süpürmesi. 90 sn'den kısa aralıklarla gelen alış süpürmeleri tek dalga olarak birleştirilir: toplam süpürülen kademe, emir sayısı, lot, ₺, başlangıç→bitiş fiyatı, süre, kademe/dk hızı ve baskın kurum. Skor = 35×kademe + 20×₺ + 20×hız + 15×fiyat değişimi + 10×erkenlik (gün <%5).",
        "nasil_kullan": "Pencereyi 5-10 dk tutun; 'Evre ERKEN' ve kademe sayısı ≥4 olanlar en değerlidir. BİLDİRİM modunda ≥4 kademelik erken dalgalarda haber verilir.",
        "dikkat": "Tek büyük emir de birden çok kademe süpürebilir (dalga değil); 'Ardışık emir' sütununa bakın. Tavana yakın hisselerde süpürme kilitlenmeyle bitebilir.",
        "ornek": "GESAN 14:32:10: 6 ardışık emirle 9 kademe, 44,10 → 44,60 ₺ (+%1,1), 3,8 Mn ₺, 41 sn, baskın kurum Ak Yatırım → skor 83."},
    "k_balina": {
        "ne": "Olağandışı büyük işlemlerin imzasını çıkarır: aynı/benzer lotla tekrarlanan (algoritmik) büyük alımlar, aynı fiyatta kümelenme ve aynı kurumun ısrarı. Tek seferlik büyük işlemi ısrarcı büyük oyuncudan ayırır.",
        "nasil": "Büyük işlem = ≥300 bin ₺ ve hissenin ortalama işlem büyüklüğünün ≥12 katı. Baskın yön (alış/satış ₺) seçilir; lotlar 2 anlamlı basamağa yuvarlanarak gruplanır (en sık lot ve tekrar sayısı), fiyatların medyanın ±%0,5'inde toplanma oranı (kümelenme) ve en sık kurum hesaplanır. Sınıf: tekrar ≥3 → ALGORİTMA; aynı kurum ≥3 kez + kümelenme ≥%60 → ISRARCI BÜYÜK OYUNCU; tek işlem → TEK SEFERLİK; diğer → DAĞINIK.",
        "nasil_kullan": "BALİNA ALIŞ + ISRARCI/ALGORİTMA sınıfı en güçlü birikim izidir. Yoğun fiyat, balinanın maliyet bölgesidir.",
        "dikkat": "Blok/çapraz işlemler de büyük görünür; Gerçek mi Fake mi ekranındaki çapraz % sütununu kontrol edin.",
        "ornek": "TUPRS: 11 büyük alış (64 Mn ₺), en sık lot 25 bin ×7, %82'si 171,20 ₺ civarında, kurum İş Yatırım (8) → ALGORİTMA (aynı lot ×7), skor 86."},
    "k_miknatis": {
        "ne": "Gün içinde en çok hacmin döndüğü fiyatları (işlem yoğunluk bölgesi) ve ana işlem merkezini bulur; fiyat bu merkezin üstüne çıkınca davranış değişimini izler.",
        "nasil": "Her fiyattaki toplam lot (aktif alış + aktif satış + seans eşleşmeleri) hesaplanır. POC = en yüksek lotlu fiyat. Yoğunluk bölgesi = toplam lotu en yüksek olan art arda 3 fiyat. Bölge hacim payı = bölgedeki lot ÷ gün toplamı. Konum = son fiyat bölgenin üstünde / içinde / altında (ve kaç dakikadır). Bölge üstü aktif alış % = bölgenin üstündeki fiyatlarda aktif alış payı.",
        "nasil_kullan": "Fiyat merkezin ÜSTÜNDE ve üstteki işlemlerde aktif alış ≥%65 ise mıknatıs artık destek olur, yukarı eğilim güçlenir. Altına inerse merkez direnç olur.",
        "dikkat": "Gün başında bölge oluşmamıştır; ilk 30-60 dk sonuçları değişkendir.",
        "ornek": "ISCTR: 52,10 → 1,8 Mn lot · 52,05 → 1,2 Mn · 52,15 → 0,9 Mn; bölge 52,05–52,15 (%41); fiyat 52,40 · 18 dk'dır ÜSTÜNDE, üstte aktif alış %72."},
    "k_destek": {
        "ne": "Gerçek destek ile sahte (gösterme) desteği ayırır. Sadece büyük alış lotuna bakmaz: o seviyeye gelen satışlar gerçekten emildi mi, kaç kez test edildi, fiyat tuttu mu, emir gösterilip silindi mi?",
        "nasil": "İlk 8 alış kademesinin her biri için: o fiyatta bugün gerçekleşen aktif satış lotu (emilen), aktif satış işlem sayısı (test), görünen lot, fiyatın seviyeye göre konumu (tepki %) ve canlı seansta derinlik farkından hesaplanan iptal edilen lot. Karar: büyük gösterilip %60+ iptal edilen ve %20'den azı gerçekleşen → SAHTE DESTEK ŞÜPHESİ; ≥300 bin ₺ emilmiş, ≥5 test, fiyat üstünde → GERÇEK DESTEK; ≥1 Mn ₺ görünüp hiç test edilmemiş → GÖSTERMELİK.",
        "nasil_kullan": "GERÇEK DESTEK satırları stop/alım seviyesi için güvenilirdir. SAHTE şüphesinde büyük alış lotuna güvenmeyin. Not sütunu hissede kaç seviyede gösterilip silinen emir görüldüğünü yazar.",
        "dikkat": "İptal ölçümü canlı seansta (2 sn derinlik farkıyla) yapılır; piyasa kapalıyken karar yalnızca işlemlerden (emilim/test) verilir.",
        "ornek": "BIMAS 488,50 ₺: görünen 62 bin lot, bugün 410 bin lot satış emildi, 57 test, fiyat +%0,6 üstünde → GERÇEK DESTEK, skor 88."},
    "k_duvar": {
        "ne": "Büyük satış duvarı sürekli aktif alış yiyor ve fiyat düşmüyorsa bu bir emilim (absorpsiyon) sinyalidir; duvarın tamamen süpürülmesi kırılımın habercisidir.",
        "nasil": "İlk 10 satış kademesinde ≥3× medyan ve ≥750 bin ₺ olan kademeler 'duvar' kabul edilir. Tüketilen lot = o fiyatta aktif alışla gerçekleşen lot (canlıda derinlik farkıyla da). Tüketim % = tüketilen ÷ (tüketilen + kalan). Fiyat tutuyor = son fiyat 15 dk öncesinden düşük değil. Durum: EMİLİYOR (tüketim ≥%30 ve fiyat tutuyor), SÜPÜRÜLDÜ (duvar ≥%50 işlemle bitti), DURUYOR.",
        "nasil_kullan": "EMİLİYOR → SÜPÜRÜLDÜ geçişi takip edilir; bildirim modunda ikisinde de haber verilir.",
        "dikkat": "Duvar iptal edilerek de kalkabilir (İPTAL EDİLDİ — gerçek emilim değil). Duvar yenilenebilir (iceberg); kalan lot sabit kalıp tüketim artıyorsa gizli satıcı vardır.",
        "ornek": "ASTOR 98,50 ₺ duvarı: zirve 1,4 Mn lot, 0,9 Mn lot tüketildi (%64), fiyat tutuyor → EMİLİYOR, skor 79."},
    "k_sikisma": {
        "ne": "Patlama öncesi sıkışmayı yakalar: fiyat dar bantta sıkışırken işlem yoğunluğu, aktif alış oranı ve büyük işlemler artıyor, satış kademeleri inceliyor → Evre 1 'hareket öncesi sıkışma'. İlk gerçek kademe süpürmesi ve bant üstü → Evre 2 'patlama'.",
        "nasil": "Son 20 dk bant % (en yüksek−en düşük) günün ortalama 1 dk aralığının 4,5 katıyla kıyaslanır (sıkışma oranı <0,75 = sıkışık). 5 koşul: sıkışma, işlem yoğunluğu (son 10 dk ÷ önceki 20 dk ≥1,25), aktif alış ≥%55 ve artıyor, satış inceliği (ilk 5 satış ≤5 dk alım), büyük işlem artışı ≥1,5×. ≥3 koşul + sıkışma → Evre 1. Evre 1 sonrası 30 dk içinde alış süpürmesiyle bant üstü → Evre 2.",
        "nasil_kullan": "Evre 1 hisseleri izleme listesine alın; Evre 2 bildirimi geldiğinde hareket başlamıştır.",
        "dikkat": "Sıkışma aşağı da kırılabilir — aktif alış oranı düşüyorsa dikkat. Öğle saatlerinde doğal düşük oynaklık sıkışma gibi görünebilir.",
        "ornek": "AKSEN: 20 dk bant %0,4 (oran 0,52), yoğunluk 1,8×, aktif alış %63, satış inceliği 2,1 dk → Evre 1; 14:05'te 4 kademe süpürüldü → Evre 2."},
    "k_serit": {
        "ne": "Şerit (tape) hızındaki olağandışı artışı yakalar: lot büyüklüğünden bağımsız olarak saniyedeki işlem sayısı aniden artıyor ama fiyat henüz pek hareket etmemiş.",
        "nasil": "Son 60 sn'deki işlem adedi, günün dakika başına ortalama işlem adediyle (ve son 30 dk ortalamasıyla) kıyaslanır: Hız × = son 60 sn ÷ gün ortalaması. İşlem/sn son 15 sn'lik anlık hızdır. Skor = 50×hız + 25×(fiyat henüz tepkisiz) + 25×aktif alış.",
        "nasil_kullan": "'FİYAT HENÜZ TEPKİSİZ' + yüksek aktif alış = algoritmik toplama veya haber öncesi hareketlenme olabilir; Süpürme ve Pozitif Hareket ekranlarıyla teyit edin.",
        "dikkat": "Çok küçük lotlarla yapılan işlem yağmuru (bölünmüş emirler) hızı artırır ama hacmi artırmaz.",
        "ornek": "VESTL son 60 sn 186 işlem, gün ortalaması 24/dk → 7,8×, fiyat 3 dk'da +%0,2, aktif alış %78 → skor 84."},
    "k_uptick": {
        "ne": "Her biri bir öncekinden daha yüksek fiyattan gerçekleşen kesintisiz işlem serisini ('yeşil dalga') bulur.",
        "nasil": "İşlemler sırayla izlenir: fiyat yükselirse seri bir adım uzar, aynı fiyat seriyi bozmaz (aynı kademede birden çok karşı emir), düşüş veya 60 sn boşluk seriyi bitirir. ≥3 adımlık seriler kaydedilir; pencere içindeki en uzun seri (sürüyorsa DEVAM EDİYOR) gösterilir.",
        "nasil_kullan": "Adım sayısı ≥7 ve sürmekte olan seriler en güçlüsüdür; bildirim modunda haber verilir. Gün penceresi günün en uzun dalgasını gösterir.",
        "dikkat": "Sığ hisselerde birkaç küçük işlemle uzun seri oluşabilir — ₺ sütununu kontrol edin.",
        "ornek": "MGROS 11:42: 9 ardışık yükseliş 512,0 → 516,5 ₺ (+%0,9), 74 sn, 6,1 Mn ₺, aktif alış %92 → DEVAM EDİYOR."},
    "k_kayma": {
        "ne": "Satış defteri o kadar sığ ki tek bir büyük piyasa emri fiyatı anında +%3-4 kaldırabilecek hisseleri bulur ve fiyatı +%1/+%2/+%3/+%4 kaldırmak için gereken ₺'yi hesaplar.",
        "nasil": "25 kademe satış defterinde son fiyattan hedef fiyata kadar olan tüm kademelerin ₺ toplamı alınır (hedef 25 kademenin dışındaysa '—'). Aynı hesap alış tarafında −%3 için yapılır; Asimetri × = −%3 için gereken ÷ +%3 için gereken. Dakika eşdeğeri = +%3 tutarı ÷ dakika başı ortalama aktif alış ₺. Tek emir yeter mi = günün en büyük agresif alış emri bu tutarı karşılıyor mu.",
        "nasil_kullan": "Asimetri yüksek (aşağı itmek pahalı, yukarı itmek ucuz) ve dakika eşdeğeri düşük hisseler yukarı kaymaya en açık olanlardır.",
        "dikkat": "Gizli (iceberg) emirler görünmez; gerçek maliyet daha yüksek olabilir. Bu bir fırsat haritasıdır, manipülasyon tavsiyesi değildir.",
        "ornek": "KLSER: +%1 için 0,4 Mn ₺, +%3 için 1,6 Mn ₺, −%3 için 9,8 Mn ₺ (asimetri 6,1×), dakika eşdeğeri 2,3, günün en büyük emri 2,1 Mn ₺ → EVET."},
    "k_agresiflik": {
        "ne": "Piyasa emriyle (agresif, karşı kademeye vurarak) alanlar ile limit emirle bekleyenleri ayırır ve toplamanın aciliyetini 1-100 puanlar; kurum bazında en acil alıcıyı gösterir.",
        "nasil": "Her kurum için aktif alış (piyasa emri) ve pasif alış (limit emrin karşılanması) lotu tutulur. Net alıcı ilk 3 kurumun aktif oranı, net alımlarının hisse hacmine oranı, süpürme lotu ve son 30 dk aktif alış % birleştirilir: Aciliyet = 40×aktif oran + 30×net pay + 15×süpürme + 15×son 30 dk. Piyasa emriyle alış % = aktif alış ÷ tüm işlem; limitle bekleyen = kalanı.",
        "nasil_kullan": "ACİL TOPLAMA (≥75) hisselerde büyük oyuncu beklemeye tahammül etmiyor, fiyatı kovalıyordur. Kurum net ₺ büyüklüğüne dikkat edin.",
        "dikkat": "Agresif alış dağıtım öncesi fiyat yükseltme amaçlı da olabilir; Gerçek mi Fake mi ekranıyla birlikte değerlendirin.",
        "ornek": "FROTO: en acil alıcı Yatırım Finansman, net 46 Mn ₺, %88 aktif; ilk 3 alıcı %79 aktif → aciliyet 87, ACİL TOPLAMA."},
    "k_vdonus": {
        "ne": "Gün içi baskılanıp küçük yatırımcının silkelendiği hisselerde dipten gelen ani, yüksek hacimli agresif alımla başlayan gerçek V dönüşü tespit eder.",
        "nasil": "Günün dibi ve dipten önceki tepe bulunur (düşüş ≥%2, ≥15 dk sürmüş). Dönüş: geri alınan % = (son − dip) ÷ (tepe − dip); dönüş hacmi × = dipten sonraki dakika başı ₺ ÷ düşüş sırasındaki; dönüşte ve düşüşte aktif alış %; yükselen dip (dipten 3 dk sonra yeni dip yok). ONAYLI V: geri alınan ≥%50, hacim ≥1,3×, aktif alış ≥%58 ve yükselen dip. V BAŞLANGICI: geri alınan ≥%25 ve aktif alış ≥%55.",
        "nasil_kullan": "ONAYLI V bildirimi geldiğinde dip seviyesi doğal stop olur. Küçük satış payı yüksekse düşüşte küçük yatırımcı satmış, büyük oyuncu toplamış olabilir.",
        "dikkat": "Dönüş düşük hacimliyse (×<1) ölü kedi sıçraması olabilir. Dip 3 saatten eskiyse listelenmez.",
        "ornek": "KOZAL −%4,8 düştü, 12:14'te 23,10 ₺ dip; düşüşün %61'i geri alındı, dönüş hacmi 2,4×, dönüşte aktif alış %71, yükselen dip → ONAYLI V DÖNÜŞ, skor 84."},
    "k_gercek": {
        "ne": "Aktif alışla süpürülen ve yükselen hissede yükselişin gerçekten hacim destekli mi yoksa yapay (fake) mi olduğunu analiz edip karar verir.",
        "nasil": "Son 15 dk'da ≥%0,8 yükselen ve aktif alışı ≥%55 olan hisseler incelenir: RVOL (günlük hacim projeksiyonu ÷ 20 gün ortalaması), alıcı kurum sayısı (≥%2 paylı), tek kurum payı (yoğunlaşma), zirveye yakınlık (takip), canlı derinlikte alış emirlerinin iptal oranı ve sahte emir sayısı, çapraz (aynı kurum alıcı+satıcı) işlem payı. Gerçeklik skoru ≥65 GERÇEK, 45-65 ŞÜPHELİ, <45 FAKE RİSKİ YÜKSEK.",
        "nasil_kullan": "Süpürme/pozitif hareket sinyali gelen hissenin burada kararına bakın; Gerekçe sütunu artı (✓) ve eksi (✗) nedenleri listeler.",
        "dikkat": "Tek kurumun yüksek payı her zaman kötü değildir (kurumsal alım) ama çapraz işlem ve yüksek iptal oranı birlikteyse yapay fiyat riski yüksektir. İptal ölçümü yalnızca canlı seansta.",
        "ornek": "ALFAS 15 dk +%3,1: RVOL 2,8, 14 alıcı kurum, tek kurum %22, zirveye yakınlık %91, alış iptal %18 → GERÇEK · hacim destekli, skor 81."},
}


# ================================================================ COMPUTE ==
def _install(cls):
    def _out(self, fid: str, cols, rows, sort, X, w, extra=None) -> dict:
        t, sh, nt, ntd, desc, wins, wdef, depth = CAT[fid]
        rows = sorted(rows, key=lambda r: (r.get(sort) is not None, r.get(sort) if r.get(sort) is not None else 0), reverse=True)
        mode = X.get("mode")
        dl = _day_label(X.get("day"))
        if mode == "kayıt":
            note = (f"Piyasa kapalı — son işlem günü {dl} kayıtlı işlemleri ({_hm(X['ref'])} itibarıyla) analiz ediliyor. "
                    + ("Derinlik: son derinlik görüntüsü (kapanış); yazılan/iptal edilen emir farkları canlı seansta ölçülür. " if depth else "")
                    + "Pazartesi seans açılınca otomatik olarak canlı veriye geçer.")
        elif not X.get("live"):
            note = f"Seans dışı — bugünün kayıtlı işlemleri ({_hm(X['ref'])}'e kadar)."
        else:
            note = f"Canlı · {_hms(X['sec'])} · tüm BIST payları her ~3 sn yeniden hesaplanır."
        out = {"fid": fid, "title": t, "short": sh, "desc": desc, "nt": nt, "cols": cols, "rows": rows[:3000], "count": len(rows),
               "updated": _now().strftime("%H:%M:%S"), "status": "tam", "note": note, "help": HELP.get(fid),
               "windows": wins, "w": w if wins else None, "mode": mode, "day": X.get("day"), "day_label": dl,
               "ref": _hms(X["ref"]), "live": X.get("live"), "universe": len(X["Q"]), "depth_based": depth}
        if extra:
            out.update(extra)
            if extra.get("note_extra"):
                out["note"] = out["note"] + " " + extra["note_extra"]
        return out

    def compute(self) -> None:
        X = self._ctx()
        res = {}
        if not hasattr(self, "_fid_ts"):
            self._fid_ts = {}
        nowc = time.time()
        for fid in ORDER:
            mi = SLOW_FIDS.get(fid)
            if mi and X.get("live") and fid in self.res and nowc - self._fid_ts.get(fid, 0) < mi and self.res[fid].get("status") == "tam":
                res[fid] = self.res[fid]          # ağır tarayıcı: daha seyrek yeniden hesapla
                continue
            self._fid_ts[fid] = nowc
            t0 = time.time()
            wdef = CAT[fid][6]
            try:
                wuse = wdef
                with self.lock:
                    cols, rows, sort = getattr(self, "f_" + fid[2:])(X, wdef)
                    wins = CAT[fid][5] or []
                    if not rows and not X.get("live") and wdef != "gun" and any(x[0] == "gun" for x in wins):
                        cols, rows, sort = getattr(self, "f_" + fid[2:])(X, "gun")
                        wuse = "gun"
                ex2 = None
                if fid in ("k_pozitif", "k_serit") and not X.get("live"):
                    ex2 = {"replay": True, "note_extra": "Seans kapalı: her hisse için kayıtlı günün EN GÜÇLÜ sinyal anı ve sonrasında fiyatın ne yaptığı (sonraki 15 dk / gün sonu) gösteriliyor. Canlı seansta anlık sinyale döner."}
                elif wuse != wdef:
                    ex2 = {"note_extra": f"Seans kapalı ve son {wdef} dk'da işlem yok — gün geneli gösteriliyor."}
                res[fid] = self._out(fid, cols, rows, sort, X, wuse, ex2)
            except Exception as ex:
                logger.warning("v122 %s: %s", fid, ex, exc_info=True)
                self.errors[fid] = str(ex)[:200]
                res[fid] = {"fid": fid, "title": CAT[fid][0], "desc": CAT[fid][4], "cols": [], "rows": [], "count": 0,
                            "status": "hata", "note": f"Hesaplama hatası: {ex}", "help": HELP.get(fid), "windows": CAT[fid][5], "w": wdef}
            self.timing[fid] = round(time.time() - t0, 3)
        with self.lock:
            self.res = res
            self.X = X
            self.cache = {}
            self.computed_at = _now().strftime("%H:%M:%S")
        try:
            self._alerts(X, res)
        except Exception as ex:
            logger.warning("v122 alerts: %s", ex, exc_info=True)
            self.errors["alerts"] = str(ex)[:200]

    def feature(self, fid: str, w: str | None = None, q: str | None = None) -> dict:
        if fid not in CAT:
            return {"fid": fid, "error": "bilinmeyen tarayıcı", "rows": [], "cols": []}
        wins = CAT[fid][5]
        wdef = CAT[fid][6]
        wraw = w
        if wins:
            ok = [x[0] for x in wins]
            w = w if w in ok else wdef
        else:
            w = None
        qq = (q or "").strip()
        base = self.res.get(fid)
        if base is None or self.X is None:
            return {"fid": fid, "title": CAT[fid][0], "desc": CAT[fid][4], "cols": [], "rows": [], "count": 0, "pending": True,
                    "note": "Arka plan hesaplaması hazırlanıyor (ilk tur birkaç saniye — kayıtlı gün yükleniyorsa ~1 dk).",
                    "help": HELP.get(fid), "windows": wins, "w": w, "status": "hazırlanıyor"}
        need = (wraw is not None and w is not None and w != base.get("w")) or (fid == "k_kurumfiyat" and qq)
        if not need:
            out = base
        else:
            key = (fid, w, qq.upper() if fid == "k_kurumfiyat" else "")
            hit = self.cache.get(key)
            if hit and time.time() - hit[0] < 5:
                out = hit[1]
            else:
                with self.ondemand_lock:
                    hit = self.cache.get(key)
                    if hit and time.time() - hit[0] < 5:
                        out = hit[1]
                    else:
                        X = self.X
                        with self.lock:
                            if fid == "k_kurumfiyat":
                                cols, rows, sort = self.f_kurumfiyat(X, w, qq)
                            else:
                                cols, rows, sort = getattr(self, "f_" + fid[2:])(X, w)
                        out = self._out(fid, cols, rows, sort, X, w)
                        self.cache[key] = (time.time(), out)
        if qq and fid != "k_kurumfiyat":
            f = _fold(qq)
            out = dict(out)
            out["rows"] = [r for r in out["rows"] if f in _fold(r.get("s") or "") or f in _fold(r.get("n") or "") or f in _fold(r.get("br") or "")]
        return out

    def catalog(self) -> dict:
        return {"features": [{"fid": f, "title": CAT[f][0], "short": CAT[f][1], "nt": CAT[f][2], "desc": CAT[f][4],
                              "count": (self.res.get(f) or {}).get("count")} for f in ORDER],
                "nt_defaults": NT_DEFAULTS, "computed_at": self.computed_at, "mode": self.mode, "day": self.day}

    def status(self) -> dict:
        return {"version": VERSION, "mode": self.mode, "day": self.day, "ready": self.ready, "computed_at": self.computed_at,
                "symbols": len(self.k), "depth_symbols": len(self.d), "ingested": self.ingested, "loops": self.loops,
                "timing": self.timing, "errors": self.errors,
                "disk": {"day": self.disk.day, "rows": self.disk.rows} if self.disk else None,
                "depth_hist": sum(len(D.hist) for D in self.d.values()), "depth_ev": sum(len(D.evq) for D in self.d.values()),
                "alerts_last_hour": len(self.arate)}

    # ---------------------------------------------------------- alerts --
    def _alerts(self, X: dict, res: dict) -> None:
        first = self._first_alert_pass
        self._first_alert_pass = False
        if not X.get("live") or self.mode != "canlı" or not (CONT_FROM + 300 <= X["sec"] <= CONT_TO):
            return
        now = time.time()
        while self.arate and now - self.arate[0][0] > 3600:
            self.arate.popleft()
        per = collections.Counter(nt for _, nt in self.arate)
        cands = []
        for fid, (min_sc, rule) in ALERT_RULES.items():
            R = res.get(fid) or {}
            nt = CAT[fid][2]
            for r in (R.get("rows") or [])[:60]:
                sc = r.get("sc") or 0
                if sc < min_sc:
                    continue
                try:
                    msg = rule(self, r)
                except Exception:
                    msg = None
                if not msg:
                    continue
                cands.append((sc, fid, nt, r, msg))
        # A: son 5 dk alıcı satıcıyı siliyor (dakika özetlerinden, ucuz)
        mref = X["ref"] // 60
        for s in X["Q"]:
            K = self.k.get(s)
            if not K or not K.last:
                continue
            a5 = self._magg(K, mref - 4, mref)
            tot = a5["lb"] + a5["ls"]
            if not tot:
                continue
            ab = a5["lb"] / tot
            btl = a5["lb"] * K.last
            avg5 = (K.tb + K.ts) / X["el"] * 5
            p0 = self._price_before(K, mref - 4)
            ch = (K.last / p0 - 1) * 100 if p0 else 0
            if ab >= 0.85 and btl >= max(3_000_000, 3 * avg5) and ch >= 0.3:
                txt = (f"{s} hissesinde son 5 dakikada işlemlerin %{ab * 100:.0f}'i aktif alış: alıcılar satıcıları siliyor "
                       f"(aktif alış {_fs(btl)} ₺, fiyat {_pc(ch)}, son {_fp(K.last)} ₺).")
                cands.append((ab * 100, "k_islem", "k_islem", {"s": s, "p": K.last, "sc": round(ab * 100)}, (f"🟢 {s} · alıcılar satıcıları siliyor", txt)))
        cands.sort(key=lambda x: -x[0])
        for sc, fid, nt, r, (title, txt) in cands:
            s = r.get("s")
            key = (s, nt)
            last = self.alerted.get(key)
            cool = 7200 if nt in STATIC_NT else 1800          # durağan sinyal: hisse başına 2 saatte bir
            if last and now - last[0] < cool and sc < last[1] + 15:
                continue
            if first:
                self.alerted[key] = (now, sc)
                continue
            if per[nt] >= (4 if nt in STATIC_NT else 10) or len(self.arate) >= 150:
                continue
            self.alerted[key] = (now, sc)
            per[nt] += 1
            self.arate.append((now, nt))
            try:
                if self.hub is not None:
                    self.hub._emit("olay", nt, s, title, txt, {"f": fid, "sc": round(sc), "price": r.get("p")})
            except Exception as ex:
                logger.debug("v122 emit: %s", ex)
            try:
                if self.events is not None:
                    self.events.emit("kademe", s, txt, nt, r.get("p"), {"nt": nt, "title": title, "f": fid, "sc": round(sc)})
            except Exception as ex:
                logger.debug("v122 olay: %s", ex)

    for fn in (_out, compute, feature, catalog, status, _alerts):
        setattr(cls, fn.__name__, fn)


SLOW_FIDS = {"k_kurumfiyat": 12, "k_agresiflik": 6, "k_miknatis": 6, "k_vdonus": 6, "k_sikisma": 6, "k_balina": 6}


def _fx(v, d=1) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(v)


STATIC_NT = {"k_koruma", "k_bosluk", "k_kayma", "k_destek", "k_miknatis"}   # durağan (defter durumu) sinyaller


def _day_label(d: str | None) -> str:
    if not d or len(d) != 8:
        return d or "—"
    try:
        dt = datetime.strptime(d, "%Y%m%d")
        return f"{dt.strftime('%d.%m.%Y')} {DAY_NAMES[dt.weekday()]}"
    except Exception:
        return d


def _A(fn):
    return fn


ALERT_RULES = {
    "k_pozitif": (75, lambda E, r: (r.get("tl3") or 0) >= 1_000_000 and (
        f"⚡ {r['s']} pozitif anlık hareket",
        f"{r['s']} son 3 dakikada {_pc(r.get('chg3'))} ivmelendi; işlemlerin %{r.get('ab3') or 0:.0f}'i aktif alış, {r.get('sw')} kez üst kademe "
        f"süpürüldü (gün {_pc(r.get('c'))}, fiyat {_fp(r.get('p'))} ₺). Skor {r['sc']:.0f}.")),
    "k_koruma": (88, lambda E, r: (r.get("b4tl") or 0) >= 5_000_000 and (
        f"🛡 {r['s']} yakın kademe koruması",
        f"{r['s']} hissesinde ilk 4 alış kademesinde {_fs(r.get('b4tl'))} ₺ ({_fs(r.get('b4'))} lot) bekliyor; satış tarafının {_fx(r.get('r'))} katı, "
        f"mevcut satış hızıyla kırılması ~{_fx(r.get('kir'), 0)} dk sürer.")),
    "k_bosluk": (85, lambda E, r: (
        f"🕳 {r['s']} satış kademesi boşluğu",
        f"{r['s']} hissesinde ilk 5 satış kademesi yalnızca {_fs(r.get('a5tl'))} ₺; ortalama alış hızıyla ~{_fx(r.get('clr'))} dk'da temizlenir, "
        f"5 kademe sonrası fiyat {_pc(r.get('pct5'))} ({_fp(r.get('p5'))} ₺).")),
    "k_otoban": (75, lambda E, r: (
        f"🛣 {r['s']} otoban kademe",
        f"{r['s']} hissesinde satış tarafı boş ({_fs(r.get('a5tl'))} ₺ / 5 kademe) ve son 5 dk'da %{r.get('ab5') or 0:.0f} aktif alışla "
        f"{_fs(r.get('btl5'))} ₺ itiliyor" + (f"; iten kurum {r['br']} (%{r.get('brp') or 0:.0f})" if r.get("br") else "") + ".")),
    "k_doldur": (75, lambda E, r: r.get("badd") is not None and (
        f"🔁 {r['s']} doldur-boşalt",
        f"{r['s']} hissesinde son 5 dk'da alışa {_fs(r.get('badd'))} ₺ yazıldı, satıştan {_fs(r.get('acanc'))} ₺ silindi ve "
        f"{_fs(r.get('afill'))} ₺ süpürüldü; satış 5 kademe {_pc(r.get('da5'))}, alış 5 kademe {_pc(r.get('db5'))}. Durum: {r.get('du')}.")),
    "k_baski": (88, lambda E, r: (r.get("wtl") or 0) >= 2_000_000 and (
        f"📈 {r['s']} aktif alış baskısı",
        f"{r['s']} son 5 dk'da aktif alış, aktif satışın {_fx(r.get('ratio'))} katı; fiyatı iten alış payı %{r.get('pushp') or 0:.0f}, "
        f"{r.get('sw')} üst kademe süpürmesi. Baskı endeksi {r['sc']:.0f}.")),
    "k_supurme": (70, lambda E, r: (r.get("kad") or 0) >= 4 and (r.get("c") or 0) < 6 and (
        f"🧹 {r['s']} kademeli süpürme",
        f"{r['s']} hissesinde {r.get('zaman')} itibarıyla {r.get('seri')} ardışık emirle {r.get('kad')} satış kademesi süpürüldü "
        f"({_fp(r.get('from'))} → {_fp(r.get('to'))} ₺, {_fs(r.get('stl'))} ₺" + (f", {r['br']}" if r.get("br") else "") + "); gün hâlâ "
        f"{_pc(r.get('c'))}.")),
    "k_balina": (75, lambda E, r: r.get("vk") == "AL" and ("ISRARCI" in (r.get("tip") or "") or "ALGORİTMA" in (r.get("tip") or "")) and (
        f"🐋 {r['s']} balina imzası",
        f"{r['s']} hissesinde {r.get('tip')}: {r.get('ndom')} büyük alış (toplam {_fs(r.get('btl'))} ₺), en sık lot {_fs(r.get('lot'))} "
        f"×{r.get('rep')}, fiyatlar {_fp(r.get('cpx'))} ₺ civarında %{r.get('clu') or 0:.0f} kümelenmiş" + (f", kurum {r['br']}" if r.get("br") else "") + ".")),
    "k_miknatis": (70, lambda E, r: str(r.get("konum") or "").startswith("ÜSTÜNDE") and (
        f"🧲 {r['s']} mıknatısın üstüne çıktı",
        f"{r['s']} günün ana işlem merkezinin ({_fp(r.get('zlo'))}–{_fp(r.get('zhi'))} ₺, hacmin %{r.get('zpay') or 0:.0f}'i) üstüne çıktı "
        f"({_pc(r.get('uz'))}); bölge üstünde aktif alış %{r.get('abu') or 0:.0f}.")),
    "k_destek": (80, lambda E, r: r.get("vk") == "AL" and (
        f"🧱 {r['s']} gerçek destek",
        f"{r['s']} hissesinde {_fp(r.get('dpx'))} ₺ desteği {r.get('test')} kez test edildi, {_fs(r.get('emilen'))} lot satış emildi ve fiyat "
        f"tuttu ({_pc(r.get('tepki'))}).")),
    "k_duvar": (75, lambda E, r: r.get("du") in ("SÜPÜRÜLDÜ", "EMİLİYOR") and (
        f"🧱 {r['s']} satış duvarı {'süpürüldü' if r.get('du') == 'SÜPÜRÜLDÜ' else 'emiliyor'}",
        f"{r['s']} hissesinde {_fp(r.get('wpx'))} ₺'deki {_fs(r.get('wpeak'))} lotluk satış duvarının %{r.get('tuk') or 0:.0f}'i aktif alışla "
        f"tüketildi" + (" ve duvar tamamen süpürüldü" if r.get("du") == "SÜPÜRÜLDÜ" else ", fiyat düşmüyor") + ".")),
    "k_sikisma": (70, lambda E, r: str(r.get("evre") or "").startswith("2") and (
        f"💥 {r['s']} sıkışmadan patlama",
        f"{r['s']} dar bantta (%{_fx(r.get('band'))}) sıkıştıktan sonra ilk gerçek kademe süpürmesi geldi: Evre 2 — patlama başladı "
        f"(10 dk aktif alış %{r.get('ab10') or 0:.0f}, işlem yoğunluğu {_fx(r.get('yog'))}×).")),
    "k_serit": (80, lambda E, r: (r.get("oran") or 0) >= 5 and (r.get("n60") or 0) >= 60 and (
        f"⏱ {r['s']} şerit hızı patlaması",
        f"{r['s']} hissesinde son 60 sn'de {r.get('n60')} işlem — günün normalinin {_fx(r.get('oran'))} katı; fiyat 3 dk'da yalnızca "
        f"{_pc(r.get('chg3'))}, aktif alış %{r.get('ab1') or 0:.0f}.")),
    "k_uptick": (75, lambda E, r: r.get("du") == "DEVAM EDİYOR" and (r.get("adim") or 0) >= 7 and (
        f"🟩 {r['s']} yeşil dalga",
        f"{r['s']} hissesinde {r.get('adim')} ardışık yükselen işlem serisi sürüyor ({_fp(r.get('from'))} → {_fp(r.get('to'))} ₺, "
        f"{_pc(r.get('pch'))}, {_fs(r.get('tl'))} ₺).")),
    "k_kayma": (85, lambda E, r: r.get("tek") == "EVET" and (
        f"🎯 {r['s']} asimetrik kayma",
        f"{r['s']} hissesinde fiyatı +%3 kaldırmak için yalnızca {_fs(r.get('u3'))} ₺ yeterli (düşürmek için {_fs(r.get('d3'))} ₺, "
        f"asimetri {_fx(r.get('asym'))}×); günün en büyük agresif emri bunu tek başına karşılıyor.")),
    "k_agresiflik": (85, lambda E, r: (r.get("brnet") or 0) >= 10_000_000 and (
        f"🏛 {r['s']} acil kurumsal toplama",
        f"{r['s']} hissesinde {r.get('br')} net {_fs(r.get('brnet'))} ₺ alımının %{r.get('brakt') or 0:.0f}'ini piyasa emriyle (agresif) yaptı; "
        f"aciliyet {r['sc']:.0f}/100.")),
    "k_vdonus": (70, lambda E, r: r.get("evre") == "ONAYLI V DÖNÜŞ" and (
        f"✅ {r['s']} hacimli V dönüş",
        f"{r['s']} gün içinde {_pc(r.get('dusus'))} düşüp {r.get('dipz')}'de {_fp(r.get('dip'))} ₺ dibini gördükten sonra düşüşün "
        f"%{r.get('retr') or 0:.0f}'ini geri aldı; dönüş hacmi düşüşün {_fx(r.get('volr'))}×, aktif alış %{r.get('abr') or 0:.0f}.")),
    "k_gercek": (75, lambda E, r: r.get("vk") == "AL" and (r.get("chg15") or 0) >= 2 and (
        f"✔ {r['s']} yükseliş gerçek görünüyor",
        f"{r['s']} son 15 dk'da {_pc(r.get('chg15'))}; karar: {r.get('karar')} ({r.get('neden')}).")),
}


ALERT_RULES["k_kurumfiyat"] = (0, lambda E, r: r.get("vk") == "AL" and (r.get("fn") or 0) >= 40 and (r.get("flot") or 0) * (r.get("fpx") or 0) >= 5_000_000 and (
    f"🏛 {r['s']} · {r.get('br')} ısrarlı alım",
    f"{r.get('br')} {r['s']} hissesinde {_fp(r.get('fpx'))} ₺ fiyatından {r.get('fn')} işlemde toplam {_fs(r.get('flot'))} lot aldı "
    f"(kurumun bu hissedeki alışının %{r.get('fpay') or 0:.0f}'i; ort. {_fp(r.get('avg'))} ₺)."))

_install(Engine)
engine = Engine()
