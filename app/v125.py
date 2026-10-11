"""v1.25.0 — DERİNLİK ANALİZLERİ (hisse sayfası · DERİNLİK sekmesi) + derinlik kaydı + derinlik alarmları.

* Kayıt (DepthRecorder): seans içinde (hafta içi 09:55–18:15) İdealData derinliği her ~2 sn'de taranır; yalnızca değişen
  kademeler (fiyat, lot, emir) hisse başına gün dosyasına yazılır (data/depth/YYYYMMDD/SYM.jsonl). Her 5 dk'da bir tam
  görüntü (anahtar kare). Geçmiş günler gzip'lenir; disk sınırı: en çok 20 gün ve 3 GB (en eski gün önce silinir).
* Analiz (DerinlikEngine.analyze): istenen hisse için gün dosyası artımlı (dosya ofsetinden) yeniden oynatılır ve aynı
  zaman aralığındaki işlemlerle eşleştirilir → duvarlar, sahte duvar (iptal), gizli emir (iceberg), kademe yenileme,
  kademe çizme, tavan/taban kuyruğu, ısı haritası, destek/direnç haritası, derinlik–işlem uyumu, dakikalık dengesizlik.
* Derinlik kaydı olmayan gün (ör. v1.25.0 öncesi Cuma): son defter görüntüsü + işlem verisinden VEKİL hesaplar açıkça
  etiketlenir; yalnız canlı derinlik gerektirenler "canlı seansla başlar" der. Veri uydurulmaz.
* Alarmlar (dr_duvar / dr_buyuk / dr_denge): kayıt döngüsünde ucuz kontroller; hisse+tür başına 30 dk tekrar yok,
  saatte en çok 40, döngü başına en çok 5; yalnız sürekli işlem (10:05–18:00).
"""
from __future__ import annotations

import bisect
import collections
import gzip
import json
import logging
import math
import os
import shutil
import threading
import time
from pathlib import Path

from app.v122 import CONT_FROM, CONT_TO, _day_label, _fp, _fs, _hm, _hms, _last_disk_day, _sec_now, _tick_size, _today

logger = logging.getLogger("v125")

VERSION = "1.25.0"
DDIR = Path(__file__).resolve().parent.parent / "data" / "depth"
NT_DUVAR, NT_BUYUK, NT_DENGE = "dr_duvar", "dr_buyuk", "dr_denge"
NT_DEFAULTS = {NT_DUVAR: "view", NT_BUYUK: "view", NT_DENGE: "view"}
REC_GAP = 2.0
KEY_EVERY = 300
FLUSH_EVERY = 10.0
MAX_DAYS, MAX_BYTES = 20, 3 * 1024 ** 3
WALL_TL = 500_000          # duvar: ≥ 3× (ilk 15 kademe medyanı) ve ≥ 500 bin ₺
ALARM_MIN_TL = 5_000_000   # alarm için hissenin gün içi işlem hacmi
ITEMS = tuple(range(1, 18))
LIVE_NOTE = "canlı seansla başlar (Pazartesi 10:00) — bu gün için derinlik kaydı yok"
EPS = 1e-9


def _r(v, d=2):
    return None if v is None else round(v, d)


def _pct(a, b):
    try:
        return (a / b - 1) * 100 if a and b else None
    except Exception:
        return None


def _now_wd():
    return time.localtime().tm_wday


def _in_rec_window(sec):
    return _now_wd() < 5 and 9 * 3600 + 55 * 60 <= sec <= 18 * 3600 + 15 * 60


def _fx(r):
    return (f"{r:.2f}".replace(".", ",") + "×") if r is not None else "—"


def _tl(lv):
    return sum(p * l for p, l, _ in lv)


# ============================================================ RECORDER ==
class DepthRecorder:
    def __init__(self):
        self.feed = None
        self.lock = threading.RLock()
        self.prev: dict[str, tuple] = {}     # sym -> (bids{p:(l,o)}, asks{p:(l,o)}, ts, last_key_sec)
        self.buf: dict[str, list] = collections.defaultdict(list)
        self.day = None
        self.lines = 0
        self.bytes = 0
        self.loops = 0
        self.last_flush = 0.0
        self.errors = 0
        self.last_err = None
        self.timing = {}
        self.on_sample = None                # alarm kancası: fn(sym, bids, asks, sec)

    def start(self, feed):
        self.feed = feed
        DDIR.mkdir(parents=True, exist_ok=True)
        threading.Thread(target=self._loop, name="v125-depthrec", daemon=True).start()
        threading.Thread(target=self._housekeep, name="v125-house", daemon=True).start()

    def path(self, day, sym):
        return DDIR / day / f"{sym}.jsonl"

    def _loop(self):
        time.sleep(10)
        while True:
            t0 = time.time()
            try:
                sec = _sec_now()
                f = self.feed
                if f is not None and _in_rec_window(sec) and getattr(f, "logged_in", False):
                    self._sample(sec)
                    self.loops += 1
                if self.buf and time.time() - self.last_flush >= FLUSH_EVERY:
                    self.flush()
                self.timing["loop"] = round(time.time() - t0, 3)
            except Exception as ex:   # pragma: no cover
                self.errors += 1
                self.last_err = str(ex)[:200]
                logger.warning("v125 rec: %s", ex, exc_info=True)
            time.sleep(max(0.5, REC_GAP - (time.time() - t0)))

    def _sample(self, sec):
        f = self.feed
        day = _today()
        if day != self.day:
            self.flush()
            self.day = day
            self.prev.clear()
        nowt = time.time()
        snaps = []
        with f._lock:
            for s, d in f.depth.items():
                ts = d.get("ts")
                if not ts or nowt - ts > 30:
                    continue
                pv = self.prev.get(s)
                if pv is not None and pv[2] == ts:
                    continue
                b = {v["price"]: (v["lot"], v.get("orders", 0)) for v in (d.get("bids") or {}).values() if v.get("price") and v.get("lot")}
                a = {v["price"]: (v["lot"], v.get("orders", 0)) for v in (d.get("asks") or {}).values() if v.get("price") and v.get("lot")}
                snaps.append((s, b, a, ts))
        with self.lock:
            for s, b, a, ts in snaps:
                pv = self.prev.get(s)
                if pv is None or sec - pv[3] >= KEY_EVERY:
                    line = {"t": sec, "k": 1, "b": [[p, l, o] for p, (l, o) in sorted(b.items(), reverse=True)],
                            "a": [[p, l, o] for p, (l, o) in sorted(a.items())]}
                    kt = sec
                else:
                    ob, oa, _, kt, _lt = pv
                    db = [[p, (b.get(p) or (0, 0))[0], (b.get(p) or (0, 0))[1]] for p in set(ob) | set(b) if ob.get(p) != b.get(p)]
                    da = [[p, (a.get(p) or (0, 0))[0], (a.get(p) or (0, 0))[1]] for p in set(oa) | set(a) if oa.get(p) != a.get(p)]
                    if not db and not da:
                        if sec - pv[4] >= 20:          # değişim yok: işlem-yalnız aralıklar için kalp atışı satırı
                            self.buf[s].append(json.dumps({"t": sec}))
                            self.prev[s] = (b, a, ts, kt, sec)
                        else:
                            self.prev[s] = (b, a, ts, kt, pv[4])
                        continue
                    line = {"t": sec}
                    if db:
                        line["b"] = db
                    if da:
                        line["a"] = da
                self.buf[s].append(json.dumps(line, separators=(",", ":")))
                self.prev[s] = (b, a, ts, kt, sec)
        hook = self.on_sample
        if hook is not None:
            for s, b, a, ts in snaps:
                try:
                    hook(s, b, a, sec)
                except Exception as ex:   # pragma: no cover
                    self.last_err = f"alarm {s}: {ex}"[:200]

    def flush(self, sym=None):
        with self.lock:
            if not self.buf or not self.day:
                return
            keys = [sym] if sym else list(self.buf.keys())
            dd = DDIR / self.day
            dd.mkdir(parents=True, exist_ok=True)
            for s in keys:
                L = self.buf.pop(s, None)
                if not L:
                    continue
                txt = "\n".join(L) + "\n"
                try:
                    with open(dd / f"{s}.jsonl", "a", encoding="utf-8") as fh:
                        fh.write(txt)
                    self.lines += len(L)
                    self.bytes += len(txt)
                except Exception as ex:   # pragma: no cover
                    self.errors += 1
                    self.last_err = str(ex)[:200]
            if sym is None:
                self.last_flush = time.time()

    def _housekeep(self):
        time.sleep(60)
        while True:
            try:
                self.prune()
            except Exception as ex:   # pragma: no cover
                logger.debug("v125 house: %s", ex)
            time.sleep(1800)

    def prune(self):
        """Geçmiş günleri gzip'le; 20 gün / 3 GB sınırını uygula."""
        if not DDIR.exists():
            return
        today = _today()
        days = sorted(p for p in DDIR.iterdir() if p.is_dir() and p.name.isdigit())
        for d in days:
            if d.name >= today:
                continue
            for f in d.glob("*.jsonl"):
                g = f.with_suffix(".jsonl.gz")
                try:
                    with open(f, "rb") as src, gzip.open(g, "wb", compresslevel=6) as dst:
                        shutil.copyfileobj(src, dst)
                    f.unlink()
                except Exception as ex:   # pragma: no cover
                    logger.debug("v125 gzip %s: %s", f, ex)
        days = sorted(p for p in DDIR.iterdir() if p.is_dir() and p.name.isdigit())
        while len(days) > MAX_DAYS:
            shutil.rmtree(days.pop(0), ignore_errors=True)
        tot = sum(f.stat().st_size for d in days for f in d.iterdir())
        while days and tot > MAX_BYTES and days[0].name < today:
            d = days.pop(0)
            tot -= sum(f.stat().st_size for f in d.iterdir())
            shutil.rmtree(d, ignore_errors=True)

    def disk(self):
        if not DDIR.exists():
            return {"days": [], "bytes": 0}
        out = []
        tot = 0
        for d in sorted(p for p in DDIR.iterdir() if p.is_dir()):
            n = sum(f.stat().st_size for f in d.iterdir())
            tot += n
            out.append({"day": d.name, "files": len(list(d.iterdir())), "bytes": n})
        return {"days": out, "bytes": tot}


# ======================================================= REPLAY STATE ==
class DS:
    """Bir hissenin gün içi derinlik geçmişi (artımlı yeniden oynatma)."""

    def __init__(self, sym, day, tv, tb):
        self.sym, self.day, self.tv, self.tb = sym, day, tv, tb
        self.b: dict = {}
        self.a: dict = {}
        self.t = None
        self.off = 0
        self.tail = b""
        self.tp = 0
        self.n = 0
        self.t0 = None
        self.mins: dict = {}          # dakika -> [ağırlık, b5, a5, b10, a10, b25, a25] (₺, zaman ağırlıklı)
        self.heat: dict = {}          # 5 dk kova -> [ağırlık, {p: b lot·sn}, {p: a lot·sn}]
        self.walls: dict = {}         # (yön, p) -> dict
        self.gone = collections.deque(maxlen=300)
        self.spoof = collections.deque(maxlen=200)
        self.ice: dict = {}
        self.icev = collections.deque(maxlen=200)
        self.sweep: dict = {}
        self.refill = collections.deque(maxlen=400)
        self.moves = collections.deque(maxlen=4000)
        self.sr: dict = {}            # (yön, p) -> [duvarla tutunma sn, test (işlem) sayısı, işlem lotu]
        self.q = collections.deque(maxlen=3000)
        self.hist = collections.deque(maxlen=900)
        self.wtot = {"b": [0.0, 0.0, 0.0], "a": [0.0, 0.0, 0.0]}   # duvar ₺: tepe, işlem, iptal
        self.big = collections.deque(maxlen=200)   # büyük emir girişi (t, yön, p, Δlot, ₺)
        self.used = time.time()


def _levels(m, side):
    return sorted(((p, v[0], v[1]) for p, v in m.items()), key=lambda x: -x[0] if side == "b" else x[0])


def _ratio(b, a):
    return (b / a) if a else (None if not b else 99.0)


class DerinlikEngine:
    def __init__(self):
        self.rec = DepthRecorder()
        self.feed = self.m = self.b = self.k = self.hub = None
        self.ds: collections.OrderedDict = collections.OrderedDict()
        self.lock = threading.RLock()
        self.cache: dict = {}
        self.alerted: dict = {}
        self.arate = collections.deque()
        self.alive_t0 = time.time()
        self.al_state: dict = {}
        self.emitted = 0
        self.timing = {}

    def start(self, feed, m_engine, b_engine, k_engine, hub):
        self.feed, self.m, self.b, self.k, self.hub = feed, m_engine, b_engine, k_engine, hub
        self.rec.on_sample = self._alarm_hook
        self.rec.start(feed)
        logger.info("v125 derinlik kaydı + analiz motoru başladı")

    # -------------------------------------------------------- helpers --
    def _resolve(self, date):
        try:
            return self.m._resolve_day(date)
        except Exception:
            return (date or _today()), False

    def _limits(self, sym, day):
        D = self.b.days.get(day) if self.b is not None else None
        st = D.st.get(sym) if D is not None else None
        if st is not None and st.tv:
            return st.tv, st.tb, st
        q = (getattr(self.feed, "quotes", {}) or {}).get(sym) or {}
        return q.get("ceiling"), q.get("floor"), st

    def _trades(self, sym, day):
        try:
            mode, syms, brokers, lock, _ = self.m._src(day)
        except Exception:
            return None, [""], None
        return syms.get(sym), list(brokers), lock

    def _snapshot(self, sym, live):
        """Anlık defter: canlı → İdealData; değilse İdealData'nın son görüntüsü ya da v1.22 kapanış defteri kaydı."""
        f = self.feed
        d = None
        if f is not None:
            with f._lock:
                x = f.depth.get(sym)
                if x:
                    d = {"bids": [(v["price"], v["lot"], v.get("orders", 0)) for v in (x.get("bids") or {}).values() if v.get("price") and v.get("lot")],
                         "asks": [(v["price"], v["lot"], v.get("orders", 0)) for v in (x.get("asks") or {}).values() if v.get("price") and v.get("lot")],
                         "ts": x.get("ts")}
        src = "İdealData canlı derinlik" if live else "İdealData'nın son defter görüntüsü (kapanış)"
        if (not d or (not d["bids"] and not d["asks"])) and self.k is not None:
            try:
                v = self.k._saved_book(sym)
            except Exception:
                v = None
            if v:
                d = {"bids": [(x["price"], x["lot"], x.get("orders", 0)) for x in v["bids"].values()],
                     "asks": [(x["price"], x["lot"], x.get("orders", 0)) for x in v["asks"].values()], "ts": None}
                src = "kayıtlı kapanış defteri (v1.22)"
        if not d:
            return [], [], None
        bids = sorted((x for x in d["bids"] if x[0] and x[1] and x[0] > 0 and x[1] > 0), key=lambda x: -x[0])
        asks = sorted((x for x in d["asks"] if x[0] and x[1] and x[0] > 0 and x[1] > 0), key=lambda x: x[0])
        return bids, asks, src

    def _file(self, day, sym):
        p = self.rec.path(day, sym)
        if p.exists():
            return p, False
        g = p.with_suffix(".jsonl.gz")
        if g.exists():
            return g, True
        return None, False

    # --------------------------------------------------------- replay --
    def _state(self, sym, day):
        key = (sym, day)
        with self.lock:
            S = self.ds.get(key)
            if S is not None:
                self.ds.move_to_end(key)
                return S
            tv, tb, _ = self._limits(sym, day)
            S = DS(sym, day, tv, tb)
            self.ds[key] = S
            while len(self.ds) > 14:
                self.ds.popitem(last=False)
            return S

    def _advance(self, S, live):
        p, gz = self._file(S.day, S.sym)
        if p is None:
            return False
        if live and S.day == self.rec.day:
            self.rec.flush(S.sym)
        if gz:
            if S.off:
                return True
            with gzip.open(p, "rb") as fh:
                data = fh.read()
            S.off = len(data) or 1
        else:
            with open(p, "rb") as fh:
                fh.seek(S.off)
                data = fh.read()
            S.off += len(data)
        data = S.tail + data
        lines = data.split(b"\n")
        S.tail = lines.pop() if not gz else b""
        if not lines:
            return True
        e, names, lock = self._trades(S.sym, S.day)
        T = Pp = L = SD = None
        if e is not None:
            with lock:
                n = len(e.t)
                T = list(e.t[S.tp:n]); Pp = list(e.p[S.tp:n]); L = list(e.l[S.tp:n]); SD = list(e.sd[S.tp:n])
        ti = 0
        for ln in lines:
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            t = o["t"]
            tr = {}; trn = {}
            if T is not None:
                while ti < len(T) and T[ti] <= t:
                    sd = SD[ti]
                    if sd == 1:
                        k = ("a", Pp[ti]); tr[k] = tr.get(k, 0.0) + L[ti]; trn[k] = trn.get(k, 0) + 1
                    elif sd == 2:
                        k = ("b", Pp[ti]); tr[k] = tr.get(k, 0.0) + L[ti]; trn[k] = trn.get(k, 0) + 1
                    ti += 1
            S.trn = trn
            if o.get("k"):
                nb = {x[0]: (x[1], x[2]) for x in o.get("b", [])}
                na = {x[0]: (x[1], x[2]) for x in o.get("a", [])}
            else:
                nb = dict(S.b); na = dict(S.a)
                for x in o.get("b", []):
                    if x[1] > 0:
                        nb[x[0]] = (x[1], x[2])
                    else:
                        nb.pop(x[0], None)
                for x in o.get("a", []):
                    if x[1] > 0:
                        na[x[0]] = (x[1], x[2])
                    else:
                        na.pop(x[0], None)
            self._step(S, t, nb, na, tr)
        S.tp += ti
        return True

    def _step(self, S, t, nb, na, tr):
        if S.t0 is None:
            S.t0 = t
        ob, oa = S.b, S.a
        if S.t is not None and (ob or oa):
            dt = max(0.0, min(60.0, t - S.t))
            if dt > 0:
                self._accum(S, S.t, dt, ob, oa)
        S.n += 1
        # ---- fark: işlem (fill) / iptal (canc) / ekleme
        for side, O, N in (("b", ob, nb), ("a", oa, na)):
            if not O and not N:
                continue
            edge = (min(N) if side == "b" else max(N)) if N else None
            for p in set(O) | set(N):
                ol = O[p][0] if p in O else 0.0
                nl = N[p][0] if p in N else 0.0
                if ol == nl:
                    continue
                trd = tr.get((side, p), 0.0)
                key = (side, p)
                if nl < ol:
                    if nl == 0 and edge is not None and ((side == "b" and p < edge) or (side == "a" and p > edge)):
                        continue        # görünür kademelerin dışına itildi
                    dec = ol - nl
                    fill = min(dec, trd); canc = dec - fill
                    w = S.walls.get(key)
                    if w:
                        w["fill"] += fill; w["canc"] += canc; w["cur"] = nl; w["t"] = t
                        if nl == 0:
                            self._wall_gone(S, side, p, w, t, ob, oa)
                    ic = S.ice.get(key)
                    if ic is None and fill > 0 and ((side == "a" and p == min(oa)) or (side == "b" and p == max(ob))):
                        ic = S.ice[key] = {"tr": 0.0, "mx": ol, "ref": 0, "ld": None, "t0": t, "flag": False}
                    if ic is not None and fill > 0:
                        ic["tr"] += trd; ic["ld"] = t; ic["mx"] = max(ic["mx"], ol)
                        if trd > dec * 1.05:      # görünen düşüşten fazla işlem → gizli yenileme
                            ic["ref"] += 1
                    if nl == 0 and ol * p >= 100_000 and fill >= 0.6 * ol:
                        S.sweep[key] = (t, ol)
                else:
                    add = nl - ol
                    w = S.walls.get(key)
                    if w:
                        w["cur"] = nl; w["peak"] = max(w["peak"], nl); w["t"] = t
                    ic = S.ice.get(key)
                    if ic is not None and ic.get("ld") and t - ic["ld"] <= 30:
                        ic["ref"] += 1; ic["ld"] = None
                    if add * p >= 2_000_000:
                        S.big.append((t, side, p, add, add * p))
                if trd > 0 and nl > 0 and ((side == "a" and oa and p == min(oa)) or (side == "b" and ob and p == max(ob))):
                    ic = S.ice.setdefault(key, {"tr": 0.0, "mx": 0.0, "ref": 0, "ld": None, "t0": t, "flag": False})
                    ic["mx"] = max(ic["mx"], ol, nl)
            # yeni kayıt satırındaki işlemler kayıtta görünmeden ice'e eklensin (lot düşmeden yenilenen kademe)
            for (sd_, p), trd in tr.items():
                if sd_ != side or p not in N:
                    continue
                if (side == "a" and N and p == min(N)) or (side == "b" and N and p == max(N)):
                    ic = S.ice.setdefault((side, p), {"tr": 0.0, "mx": 0.0, "ref": 0, "ld": None, "t0": t, "flag": False})
                    ol = O[p][0] if p in O else 0.0
                    nl = N[p][0]
                    if nl >= ol:     # işlem gördü ama lot düşmedi → her işlemden sonra yenilendi
                        ic["tr"] += trd; ic["ref"] += max(1, getattr(S, "trn", {}).get((side, p), 1))
                    ic["mx"] = max(ic["mx"], ol, nl)
        for (side, p), ic in S.ice.items():
            if not ic["flag"] and ic["ref"] >= 3 and ic["tr"] >= 2 * max(1.0, ic["mx"]) and ic["tr"] * p >= 250_000:
                ic["flag"] = True
                S.icev.append((t, side, p, ic["tr"], ic["mx"], ic["ref"]))
        # ---- süpürülen kademe yeniden doldu mu?
        for key, (ts, lot) in list(S.sweep.items()):
            side, p = key
            N = nb if side == "b" else na
            if p in N and N[p][0] >= 0.3 * lot and t > ts:
                S.refill.append((ts, side, p, lot, t - ts))
                S.sweep.pop(key, None)
            elif t - ts > 300:
                S.refill.append((ts, side, p, lot, None))
                S.sweep.pop(key, None)
        # ---- kademe çizme (en iyi fiyat hareketleri)
        if ob and nb:
            o1, n1 = max(ob), max(nb)
            if n1 > o1 + EPS:
                S.moves.append((t, "bu"))
            elif n1 < o1 - EPS and tr.get(("b", o1), 0.0) < 0.5 * ob[o1][0]:
                S.moves.append((t, "bc"))
        if oa and na:
            o1, n1 = min(oa), min(na)
            if n1 > o1 + EPS and tr.get(("a", o1), 0.0) < 0.5 * oa[o1][0]:
                S.moves.append((t, "ac"))
            elif n1 < o1 - EPS:
                S.moves.append((t, "ad"))
        # ---- tavan / taban kuyruğu
        if S.tv and nb and abs(max(nb) - S.tv) < 1e-6:
            S.q.append((t, "tv", nb[max(nb)][0], nb[max(nb)][1]))
        if S.tb and na and abs(min(na) - S.tb) < 1e-6:
            S.q.append((t, "tb", na[min(na)][0], na[min(na)][1]))
        # ---- duvar kaydı
        for side, N in (("b", nb), ("a", na)):
            lv = _levels(N, side)
            if not lv:
                continue
            lots = sorted(l for _, l, _ in lv[:15])
            med = lots[len(lots) // 2]
            for p, l, o in lv[:10]:
                key = (side, p)
                w = S.walls.get(key)
                if w is None and l >= 3 * med and l * p >= WALL_TL:
                    S.walls[key] = {"side": side, "p": p, "first": t, "peak": l, "cur": l, "fill": 0.0, "canc": 0.0, "t": t,
                                    "h": collections.deque(maxlen=40), "ord": o}
                    S.wtot[side][0] += l * p
                elif w is not None:
                    if l > w["peak"]:
                        S.wtot[side][0] += (l - w["peak"]) * p
                    w["ord"] = o
                w = S.walls.get(key)
                if w is not None:
                    if not w["h"] or t - w["h"][-1][0] >= 10:
                        w["h"].append((t, l))
            if len(S.walls) > 80:
                for k_ in sorted(S.walls, key=lambda x: S.walls[x]["t"])[:len(S.walls) - 80]:
                    S.walls.pop(k_, None)
        if len(S.ice) > 60:
            for k_ in sorted(S.ice, key=lambda x: S.ice[x]["t0"])[:len(S.ice) - 60]:
                S.ice.pop(k_, None)
        S.b, S.a, S.t = nb, na, t

    def _wall_gone(self, S, side, p, w, t, ob, oa):
        st = "SÜPÜRÜLDÜ (işlemle)" if w["fill"] >= 0.5 * w["peak"] else "İPTAL EDİLDİ" if w["canc"] >= 0.6 * w["peak"] else "BİTTİ"
        rec = (w["first"], t, side, p, w["peak"], w["fill"], w["canc"], st)
        S.gone.append(rec)
        S.wtot[side][1] += w["fill"] * p
        S.wtot[side][2] += w["canc"] * p
        if st == "İPTAL EDİLDİ" and w["fill"] <= 0.25 * w["peak"]:
            opp = (max(ob) if ob else None) if side == "a" else (min(oa) if oa else None)
            tk = _tick_size(p)
            near = opp is not None and abs(p - opp) <= max(3 * tk, p * 0.006) + EPS
            at_best = (side == "a" and oa and p == min(oa)) or (side == "b" and ob and p == max(ob))
            if near or at_best:
                S.spoof.append((t, side, p, w["peak"], w["fill"], w["canc"], t - w["first"]))
        S.walls.pop((side, p), None)

    def _accum(self, S, t, dt, ob, oa):
        bl, al = _levels(ob, "b"), _levels(oa, "a")
        m = t // 60
        r = S.mins.get(m)
        if r is None:
            r = S.mins[m] = [0.0] * 7
        b5, a5, b10, a10, b25, a25 = _tl(bl[:5]), _tl(al[:5]), _tl(bl[:10]), _tl(al[:10]), _tl(bl[:25]), _tl(al[:25])
        r[0] += dt
        for i, v in enumerate((b5, a5, b10, a10, b25, a25)):
            r[i + 1] += v * dt
        if not S.hist or t - S.hist[-1][0] >= 5:
            S.hist.append((t, b5, a5, b10, a10, b25, a25))
        k = (t - CONT_FROM) // 300 if t >= CONT_FROM else -1
        h = S.heat.get(k)
        if h is None:
            h = S.heat[k] = [0.0, {}, {}]
        h[0] += dt
        for p, l, _ in bl[:25]:
            h[1][p] = h[1].get(p, 0.0) + l * dt
        for p, l, _ in al[:25]:
            h[2][p] = h[2].get(p, 0.0) + l * dt
        # destek / direnç: en iyi fiyattaki duvar ne kadar tuttu
        for side, lv in (("b", bl), ("a", al)):
            if not lv:
                continue
            p = lv[0][0]
            if (side, p) in S.walls:
                x = S.sr.setdefault((side, p), [0.0, 0, 0.0])
                x[0] += dt

    # ---------------------------------------------------------- analyze --
    def analyze(self, sym, items=None, date=None):
        sym = (sym or "").upper().strip()
        want = set(items or ITEMS)
        want.discard(6)
        day, live = self._resolve(date)
        ck = (sym, day, tuple(sorted(want)))
        # v1.38.1: önbellek canlı 1 sn / seans dışı 60 sn; aynı anahtar için tek hesap (eşzamanlı istekler bekler, ikinci kez
        # hesaplamaz); seans dışında süresi geçmiş kayıt hemen döner, yenisi arka planda hesaplanır (bayatken-yenile).
        ttl = 1.0 if live else 60.0
        hit = self.cache.get(ck)
        if hit is None and not live and day:
            hit = self._dload(ck)   # v1.38.1 seans dışı disk önbelleği (yeniden başlatmada da anında)
            if hit:
                self.cache[ck] = hit
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
        if not hasattr(self, "_sf"):
            self._sf, self._sf_lock = {}, threading.Lock()
        with self._sf_lock:
            ev = self._sf.get(ck)
            mine = ev is None
            if mine:
                ev = self._sf[ck] = threading.Event()
        if not mine:
            if hit and not live:
                return hit[1]
            ev.wait(60)
            h2 = self.cache.get(ck)
            return h2[1] if h2 else (hit[1] if hit else {"sym": sym, "day": day, "live": live, "items": sorted(want), "r": {}, "error": "hesaplanıyor"})
        if hit and not live:
            def _bg():
                try:
                    self._compute(ck, sym, day, live, want)
                finally:
                    with self._sf_lock:
                        self._sf.pop(ck, None)
                    ev.set()
            threading.Thread(target=_bg, daemon=True, name="v125-swr").start()
            return hit[1]
        try:
            return self._compute(ck, sym, day, live, want)
        finally:
            with self._sf_lock:
                self._sf.pop(ck, None)
            ev.set()

    def _compute(self, ck, sym, day, live, want):
        t0 = time.time()
        out = {"sym": sym, "day": day, "day_label": _day_label(day) if day else "", "live": live, "version": VERSION,
               "ts": time.strftime("%H:%M:%S"), "items": sorted(want)}
        try:
            self._analyze(out, sym, day, live, want)
        except Exception as ex:   # pragma: no cover
            logger.warning("v125 analyze %s: %s", sym, ex, exc_info=True)
            out["error"] = str(ex)[:200]
        out["ms"] = round((time.time() - t0) * 1000)
        if len(self.cache) > 300:
            self.cache.clear()
        self.cache[ck] = (time.time(), out)
        if not live and day and not out.get("error"):
            self._dsave(ck, out)
        return out

    _DC = Path(__file__).resolve().parents[1] / "data" / "v138" / "dr_cache"

    def _dpath(self, ck):
        sym, day, its = ck
        return self._DC / f"{day}_{sym}_{'-'.join(map(str, its))}.json.gz"

    def _dload(self, ck):
        try:
            p = self._dpath(ck)
            src, _ = self._file(ck[1], ck[0])
            if src is not None and Path(src).stat().st_mtime > p.stat().st_mtime:
                return None   # kayıt dosyası daha yeni → yeniden hesapla
            with gzip.open(p, "rt", encoding="utf-8") as f:
                out = json.load(f)
            return (time.time(), out)
        except Exception:
            return None

    def _dsave(self, ck, out):
        try:
            self._DC.mkdir(parents=True, exist_ok=True)
            p = self._dpath(ck); tmp = p.with_suffix(".tmp")
            with gzip.open(tmp, "wt", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, default=str)
            os.replace(tmp, p)
            fs = sorted(self._DC.glob("*.json.gz"), key=lambda x: x.stat().st_mtime)
            for x in fs[:-2000]:
                x.unlink(missing_ok=True)
        except Exception as ex:
            logger.debug("v125 dsave: %s", ex)

    def _analyze(self, out, sym, day, live, want):
        tv, tb, bst = self._limits(sym, day)
        bids, asks, src = self._snapshot(sym, live)
        p_file, _ = self._file(day, sym) if day else (None, False)
        S = None
        if p_file is not None:
            S = self._state(sym, day)
            S.tv, S.tb = tv, tb
            with self.lock:
                self._advance(S, live)
            S.used = time.time()
            if S.b or S.a:
                if not live or not bids:
                    bids, asks = _levels(S.b, "b"), _levels(S.a, "a")
                    src = f"derinlik kaydı ({_day_label(day)} son görüntü)"
        hist = S is not None and S.n > 1
        out["hist"] = hist
        out["src"] = src
        out["mode"] = "canlı" if live else "kayıt"
        out["rec_note"] = (f"Derinlik kaydı: {S.n} değişim, {_hms(S.t0)}–{_hms(S.t)}" if hist else
                           "Bu gün için derinlik kaydı yok (kayıt v1.25.0 ile başladı) — geçmiş gerektiren bölümler canlı seansla başlar; "
                           "bazı bölümler işlem verisinden VEKİL olarak gösterilir.")
        last = (bst.last if bst is not None else None) or ((getattr(self.feed, "quotes", {}) or {}).get(sym) or {}).get("last")
        out["last"], out["tv"], out["tb"] = last, tv, tb
        e, names, lock = self._trades(sym, day)
        now_s = S.t if hist else (min(_sec_now(), CONT_TO) if live else None)
        R = {}
        ask = set(want)
        if 16 in want:      # skor kapalı kartların sinyallerini de kullanır (yalnız sunucuda; istemciye gönderilmez)
            want = set(want) | {1, 2, 3, 4, 5, 7, 8, 10}
        # ---- 1) alış/satış dengesi
        if 1 in want:
            x = {}
            for n in (5, 10, 25):
                b_, a_ = _tl(bids[:n]), _tl(asks[:n])
                bl_, al_ = sum(l for _, l, _ in bids[:n]), sum(l for _, l, _ in asks[:n])
                x[str(n)] = {"b": round(b_), "a": round(a_), "bl": bl_, "al": al_, "r": _r(_ratio(bl_, al_), 2), "bp": _r(bl_ / (bl_ + al_) * 100, 1) if bl_ + al_ else None}
            ch = None
            if hist and len(S.hist) > 2:
                tN = S.hist[-1][0]
                old = None
                for h in reversed(S.hist):
                    if tN - h[0] >= 60:
                        old = h; break
                if old:
                    cur = S.hist[-1]
                    ch = {"sec": tN - old[0]}
                    for n, (ib, ia) in (("5", (1, 2)), ("10", (3, 4)), ("25", (5, 6))):
                        r0, r1 = _ratio(old[ib], old[ia]), _ratio(cur[ib], cur[ia])
                        ch[n] = {"r0": _r(r0, 2), "r1": _r(r1, 2), "d": _r((r1 - r0) if r0 is not None and r1 is not None else None, 2)}
            x["ch"] = ch
            x["ch_note"] = None if ch else LIVE_NOTE if not hist else "1 dk'lık geçmiş birikiyor"
            R[1] = x
        # ---- 2) duvarlar
        if 2 in want:
            R[2] = self._walls_out(S, bids, asks, hist, now_s, last)
        # ---- 3) sahte duvar
        if 3 in want:
            if hist:
                L = [{"t": _hms(x[0]), "side": "ALIŞ" if x[1] == "b" else "SATIŞ", "p": x[2], "peak": x[3], "fill": round(x[4]), "canc": round(x[5]),
                      "tl": round(x[3] * x[2]), "dur": int(x[6])} for x in list(S.spoof)[-12:]][::-1]
                R[3] = {"list": L, "n": len(S.spoof), "nb": sum(1 for x in S.spoof if x[1] == "b"), "na": sum(1 for x in S.spoof if x[1] == "a")}
            else:
                R[3] = {"live_only": True, "note": LIVE_NOTE}
        # ---- 4) gizli emir
        if 4 in want:
            if hist:
                L = [{"t": _hms(x[0]), "side": "ALIŞ" if x[1] == "b" else "SATIŞ", "p": x[2], "tr": round(x[3]), "mx": round(x[4]), "ref": x[5],
                      "x": _r(x[3] / max(1.0, x[4]), 1), "tl": round(x[3] * x[2])} for x in list(S.icev)[-12:]][::-1]
                act = [{"side": "ALIŞ" if k_[0] == "b" else "SATIŞ", "p": k_[1], "tr": round(v["tr"]), "mx": round(v["mx"]), "ref": v["ref"]}
                       for k_, v in S.ice.items() if v["ref"] >= 1 and not v["flag"] and v["tr"] > v["mx"]]
                R[4] = {"list": L, "watch": sorted(act, key=lambda z: -z["tr"])[:4]}
            else:
                R[4] = {"live_only": True, "note": LIVE_NOTE}
        # ---- 5) kademe yenileme hızı
        if 5 in want:
            if hist:
                rf = list(S.refill)
                done = [x for x in rf if x[4] is not None]
                def avg(side):
                    v = [x[4] for x in done if x[1] == side]
                    return _r(sum(v) / len(v), 1) if v else None
                R[5] = {"n": len(rf), "done": len(done), "never": len(rf) - len(done), "avg_a": avg("a"), "avg_b": avg("b"),
                        "pend": len(S.sweep),
                        "list": [{"t": _hms(x[0]), "side": "SATIŞ" if x[1] == "a" else "ALIŞ", "p": x[2], "lot": round(x[3]), "s": x[4]} for x in rf[-10:]][::-1]}
            else:
                R[5] = {"live_only": True, "note": LIVE_NOTE}
        # ---- 7) kademe çizme
        if 7 in want:
            if hist:
                tN = S.t
                def cnt(w):
                    c = collections.Counter(k_ for t_, k_ in S.moves if t_ >= tN - w)
                    return {"bu": c["bu"], "bc": c["bc"], "ac": c["ac"], "ad": c["ad"], "net": c["bu"] + c["ac"] - c["bc"] - c["ad"]}
                R[7] = {"m5": cnt(300), "m15": cnt(900), "day": cnt(10 ** 6)}
            else:
                R[7] = {"live_only": True, "note": LIVE_NOTE}
        # ---- 8) tavan / taban kuyruğu
        if 8 in want:
            R[8] = self._queue_out(S, bids, asks, tv, tb, hist)
        # ---- 9) emir sayısı ve lot
        if 9 in want:
            R[9] = self._orders_out(bids, asks)
        # ---- 10) son süpürmeler
        if 10 in want:
            R[10] = self._sweeps_out(sym, day, names)
        # ---- 11) ısı haritası
        if 11 in want:
            R[11] = self._heat_out(S) if hist else self._heat_trades(e, lock, tv, tb)
        # ---- 12) destek / direnç haritası
        if 12 in want:
            R[12] = self._sr_out(S) if hist else self._sr_trades(e, lock)
        # ---- 13) derinlik–işlem uyumu
        if 13 in want:
            R[13] = self._match_out(S, e, lock, bids, asks, hist)
        # ---- 14) dengesizlik grafiği
        if 14 in want:
            R[14] = self._imb_out(S) if hist else self._imb_trades(e, lock)
        # ---- 15) merdivende POC / VWAP / kurum maliyetleri
        if 15 in want:
            R[15] = self._marks(sym, day, bst, e, lock)
        # ---- 17) alarmlar (bu hisse)
        if 17 in want:
            R[17] = self._alarms_for(sym, day, live)
        if 16 in want:
            R[16] = self._score(R, S, hist, bids, asks, live, tv, last)
        out["r"] = {str(k): v for k, v in R.items() if k in ask}

    # ----------------------------------------------------- parts (out) --
    def _walls_out(self, S, bids, asks, hist, now_s, last):
        def thr(lv):
            lots = sorted(l for _, l, _ in lv[:15])
            return lots[len(lots) // 2] if lots else 0
        out = {"b": [], "a": [], "hist": hist}
        for side, lv in (("b", bids), ("a", asks)):
            med = thr(lv)
            for p, l, o in lv[:10]:
                if l >= 3 * med and l * p >= WALL_TL:
                    w = S.walls.get((side, p)) if hist else None
                    trend, dur, fill, canc, peak = None, None, None, None, l
                    if w is not None:
                        dur = int((now_s or w["t"]) - w["first"])
                        peak = w["peak"]; fill = round(w["fill"]); canc = round(w["canc"])
                        h = w["h"]
                        old = next((x for x in reversed(h) if (h[-1][0] - x[0]) >= 60), None) if h else None
                        if old:
                            ch = (l - old[1]) / old[1] * 100 if old[1] else 0
                            trend = "BÜYÜYOR" if ch >= 10 else "ERİYOR" if ch <= -10 else "SABİT"
                            trend_ch = round(ch, 1)
                        else:
                            trend_ch = None
                    else:
                        trend_ch = None
                    out[side].append({"p": p, "lot": l, "ord": o, "tl": round(l * p), "x": _r(l / med, 1) if med else None, "dur": dur,
                                      "first": _hms(w["first"]) if w is not None else None, "peak": peak, "fill": fill, "canc": canc,
                                      "trend": trend, "trend_ch": trend_ch, "dist": _r(_pct(p, last), 2) if last else None})
            out[side] = sorted(out[side], key=lambda z: -z["tl"])[:5]
        if hist:
            out["gone"] = [{"first": _hms(x[0]), "t": _hms(x[1]), "side": "ALIŞ" if x[2] == "b" else "SATIŞ", "p": x[3], "peak": round(x[4]),
                            "fill": round(x[5]), "canc": round(x[6]), "st": x[7]} for x in list(S.gone)[-8:]][::-1]
        else:
            out["note"] = "Süre ve büyüyor/eriyor bilgisi " + LIVE_NOTE + "; şu an son defter görüntüsündeki duvarlar gösteriliyor."
        return out

    def _queue_out(self, S, bids, asks, tv, tb, hist):
        out = {"tv": tv, "tb": tb}
        if tv and bids and abs(bids[0][0] - tv) < 1e-6:
            out["at"] = "tv"; out["lot"] = bids[0][1]; out["ord"] = bids[0][2]; out["tl"] = round(bids[0][1] * tv)
            out["opp"] = asks[0][1] if asks and abs(asks[0][0] - tv) < 1e-6 else 0
        elif tb and asks and abs(asks[0][0] - tb) < 1e-6:
            out["at"] = "tb"; out["lot"] = asks[0][1]; out["ord"] = asks[0][2]; out["tl"] = round(asks[0][1] * tb)
        else:
            out["at"] = None
            out["tv_ask"] = next((l for p, l, _ in asks if abs(p - (tv or -1)) < 1e-6), None)
        if hist and S.q:
            side = out.get("at") or S.q[-1][1]
            Q = [x for x in S.q if x[1] == side]
            if Q:
                pk = max(x[2] for x in Q)
                tN = Q[-1][0]
                w10 = [x for x in Q if x[0] >= tN - 600]
                pk10 = max(x[2] for x in w10) if w10 else pk
                cur = Q[-1][2]
                out["series"] = [[x[0], x[2]] for x in Q[-240:]]
                out["peak"], out["peak10"], out["cur"] = pk, pk10, cur
                out["melt10"] = _r((pk10 - cur) / pk10 * 100, 1) if pk10 else None
                out["state"] = "ERİYOR" if out["melt10"] and out["melt10"] >= 25 else "BÜYÜYOR" if len(w10) > 1 and cur > w10[0][2] * 1.1 else "SABİT"
                out["side"] = side
        elif out.get("at"):
            out["note"] = "Eriyor/büyüyor takibi " + LIVE_NOTE
        return out

    def _orders_out(self, bids, asks):
        has = any(o for _, _, o in bids[:25]) or any(o for _, _, o in asks[:25])
        rows = []
        for side, lv in (("b", bids), ("a", asks)):
            avgs = sorted(l / o for _, l, o in lv[:15] if o)
            med = avgs[len(avgs) // 2] if avgs else 0
            for i, (p, l, o) in enumerate(lv[:10]):
                av = l / o if o else None
                inst = bool(o and ((o <= 3 and l * p >= 1_000_000) or (av and med and o <= 10 and av >= 5 * med and l * p >= 500_000)))
                rows.append({"side": side, "lvl": i + 1, "p": p, "lot": l, "ord": o, "avg": round(av) if av else None, "tl": round(l * p), "inst": inst,
                             "x": _r(av / med, 1) if av and med else None})
        sb = sum(o for _, _, o in bids[:25]); sa = sum(o for _, _, o in asks[:25])
        lb = sum(l for _, l, _ in bids[:25]); la = sum(l for _, l, _ in asks[:25])
        return {"has": has, "rows": rows, "inst": [r for r in rows if r["inst"]], "ob": sb, "oa": sa,
                "avg_b": round(lb / sb) if sb else None, "avg_a": round(la / sa) if sa else None}

    def _sweeps_out(self, sym, day, names):
        D = self.b.days.get(day) if self.b is not None else None
        st = D.st.get(sym) if D is not None else None
        if st is None:
            return {"list": [], "note": "işlem taraması hazırlanıyor"}
        xs = [x for x in st.sw if x[3] >= 100_000]
        L = [{"t": _hms(x[0]), "nlev": x[1], "lot": x[2], "tl": round(x[3]), "p0": x[4], "p1": x[5],
              "br": names[x[6]] if x[6] < len(names) else ""} for x in xs[-12:]][::-1]
        tN = xs[-1][0] if xs else 0
        return {"list": L, "n": len(xs), "n15": sum(1 for x in xs if x[0] >= (st.last_t or 0) - 900), "last_t": st.last_t,
                "tl15": round(sum(x[3] for x in xs if x[0] >= (st.last_t or 0) - 900))}

    def _heat_out(self, S):
        ks = sorted(k for k in S.heat if k >= 0)
        if not ks:
            return {"kind": "derinlik", "empty": True}
        prices = set()
        for k in ks:
            prices |= set(S.heat[k][1]) | set(S.heat[k][2])
        P = sorted(prices)
        if len(P) > 60:
            mid = (S.b and max(S.b)) or P[len(P) // 2]
            i = bisect.bisect_left(P, mid)
            P = P[max(0, i - 30): i + 30]
        cells = []
        mx = 1.0
        for ci, k in enumerate(ks):
            w, hb, ha = S.heat[k]
            if w <= 0:
                continue
            for p in P:
                vb = hb.get(p, 0.0) / w; va = ha.get(p, 0.0) / w
                if vb or va:
                    cells.append([ci, p, round(vb), round(va)])
                    mx = max(mx, vb, va)
        return {"kind": "derinlik", "t": [_hm(CONT_FROM + k * 300) for k in ks], "p": P, "cells": cells, "max": round(mx),
                "bucket": "5 dk", "label": "Kademelerde bekleyen ortalama lot (zaman ağırlıklı)"}

    def _heat_trades(self, e, lock, tv, tb):
        if e is None:
            return {"kind": "işlem", "empty": True, "note": LIVE_NOTE}
        with lock:
            n = len(e.t); T = list(e.t[:n]); Pp = list(e.p[:n]); L = list(e.l[:n]); SD = list(e.sd[:n])
        acc = {}
        mx = 1.0
        for t, p, l, sd in zip(T, Pp, L, SD):
            if t < CONT_FROM or t > CONT_TO:
                continue
            k = (t - CONT_FROM) // 900
            x = acc.setdefault((k, p), [0.0, 0.0])
            x[0 if sd == 1 else 1] += l
        if not acc:
            return {"kind": "işlem", "empty": True, "note": LIVE_NOTE}
        ks = sorted(set(k for k, _ in acc))
        P = sorted(set(p for _, p in acc))
        if len(P) > 60:
            vol = collections.Counter()
            for (k, p), v in acc.items():
                vol[p] += v[0] + v[1]
            poc = max(vol, key=vol.get)
            i = bisect.bisect_left(P, poc)
            P = P[max(0, i - 30): i + 30]
        Ps = set(P)
        kix = {k: i for i, k in enumerate(ks)}
        cells = []
        for (k, p), v in acc.items():
            if p in Ps:
                cells.append([kix[k], p, round(v[0]), round(v[1])])
                mx = max(mx, v[0], v[1])
        return {"kind": "işlem", "t": [_hm(CONT_FROM + k * 900) for k in ks], "p": P, "cells": cells, "max": round(mx), "bucket": "15 dk",
                "label": "VEKİL: fiyat × 15 dk işlem hacmi (yeşil aktif alış, kırmızı aktif satış) — derinlik ısı haritası " + LIVE_NOTE}

    def _sr_out(self, S):
        tops = []
        for (side, p), (secs, tests, flot) in S.sr.items():
            tops.append({"side": "DESTEK" if side == "b" else "DİRENÇ", "p": p, "sec": int(secs)})
        sup = sorted([x for x in tops if x["side"] == "DESTEK"], key=lambda z: -z["sec"])[:6]
        res = sorted([x for x in tops if x["side"] == "DİRENÇ"], key=lambda z: -z["sec"])[:6]
        # tutunma: duvar en iyi fiyatta beklerken işlem gördü ve yine de kaldı
        for x in sup + res:
            g = [w for w in S.gone if w[3] == x["p"] and (w[2] == "b") == (x["side"] == "DESTEK")]
            x["broke"] = len(g)
            x["held"] = (("b" if x["side"] == "DESTEK" else "a"), x["p"]) in S.walls
        return {"kind": "derinlik", "sup": sup, "res": res, "label": "Duvarın en iyi fiyatta bekleyerek tuttuğu süre"}

    def _sr_trades(self, e, lock):
        if e is None:
            return {"kind": "işlem", "sup": [], "res": [], "note": LIVE_NOTE}
        with lock:
            n = len(e.t); T = list(e.t[:n]); Pp = list(e.p[:n]); L = list(e.l[:n])
        M = {}
        for t, p, l in zip(T, Pp, L):
            if t < CONT_FROM or t > CONT_TO:
                continue
            m = t // 60
            x = M.get(m)
            if x is None:
                M[m] = [p, p, p, p, l]
            else:
                x[1] = max(x[1], p); x[2] = min(x[2], p); x[3] = p; x[4] += l
        sup = collections.Counter(); res = collections.Counter(); vol = collections.Counter()
        ms = sorted(M)
        for i, m in enumerate(ms):
            o, h, lo, c, v = M[m]
            nxt = M[ms[i + 1]] if i + 1 < len(ms) else None
            tk = _tick_size(lo)
            if c >= lo + tk - EPS and (nxt is None or nxt[2] >= lo - EPS):
                sup[lo] += 1; vol[lo] += v
            if c <= h - tk + EPS and (nxt is None or nxt[1] <= h + EPS):
                res[h] += 1
        return {"kind": "işlem", "sup": [{"side": "DESTEK", "p": p, "n": c} for p, c in sup.most_common(6)],
                "res": [{"side": "DİRENÇ", "p": p, "n": c} for p, c in res.most_common(6)],
                "label": "VEKİL (işlem verisi): fiyatın dakika dibinde/tepesinde dönüp sonraki dakikada da korunduğu seviyeler; "
                         "duvar bazlı harita " + LIVE_NOTE}

    def _match_out(self, S, e, lock, bids, asks, hist):
        if hist:
            out = {"kind": "derinlik"}
            for side in ("b", "a"):
                pk, fl, cn = S.wtot[side]
                for w in S.walls.values():
                    if w["side"] == side:
                        fl += w["fill"] * w["p"]; cn += w["canc"] * w["p"]
                out[side] = {"peak": round(pk), "fill": round(fl), "canc": round(cn),
                             "fill_pct": _r(fl / (fl + cn) * 100, 1) if fl + cn else None}
            out["gone"] = collections.Counter(x[7] for x in S.gone)
            out["label"] = "Görünen duvarlardan azalan lotun ne kadarı İŞLEMLE (gerçek), ne kadarı İPTALLE (gösteriş) gitti"
            return out
        if e is None:
            return {"kind": "işlem", "note": LIVE_NOTE}
        with lock:
            n = len(e.t); Pp = list(e.p[:n]); L = list(e.l[:n]); SD = list(e.sd[:n])
        tr = collections.Counter()
        for p, l, sd in zip(Pp, L, SD):
            tr[(sd, p)] += l
        rows = []
        for side, lv in (("b", bids), ("a", asks)):
            lots = sorted(l for _, l, _ in lv[:15])
            med = lots[len(lots) // 2] if lots else 0
            for p, l, o in lv[:10]:
                if l >= 3 * med and l * p >= WALL_TL:
                    t_ = tr[(1 if side == "a" else 2, p)]
                    rows.append({"side": "ALIŞ" if side == "b" else "SATIŞ", "p": p, "lot": l, "traded": round(t_), "x": _r(t_ / l, 2) if l else None})
        return {"kind": "işlem", "rows": rows,
                "label": "VEKİL: kapanış defterindeki duvar fiyatlarında gün içinde o tarafa vurularak gerçekleşen lot (duvarın kaç katı). "
                         "İşlem/iptal ayrımı " + LIVE_NOTE}

    def _imb_out(self, S):
        ms = sorted(S.mins)
        ser = []
        for m in ms:
            w, b5, a5, b10, a10, b25, a25 = S.mins[m]
            if w <= 0:
                continue
            ser.append([m * 60, _r(_ratio(b5, a5), 3), _r(_ratio(b10, a10), 3), _r(_ratio(b25, a25), 3)])
        return {"kind": "derinlik", "series": ser, "label": "Dakikalık alış/satış ₺ oranı (5 / 10 / 25 kademe, zaman ağırlıklı)"}

    def _imb_trades(self, e, lock):
        if e is None:
            return {"kind": "işlem", "series": [], "note": LIVE_NOTE}
        with lock:
            n = len(e.t); T = list(e.t[:n]); L = list(e.l[:n]); SD = list(e.sd[:n])
        M = {}
        for t, l, sd in zip(T, L, SD):
            if t < CONT_FROM or t > CONT_TO:
                continue
            x = M.setdefault(t // 60, [0.0, 0.0])
            if sd == 1:
                x[0] += l
            elif sd == 2:
                x[1] += l
        ser = [[m * 60, _r(_ratio(x[0], x[1]), 3)] for m, x in sorted(M.items()) if x[0] or x[1]]
        return {"kind": "işlem", "series": ser,
                "label": "VEKİL: dakikalık aktif alış / aktif satış lot oranı (işlem dengesizliği) — derinlik dengesizliği " + LIVE_NOTE}

    def _marks(self, sym, day, bst, e, lock):
        M = []
        if bst is not None and bst.vol:
            poc = max(bst.vol, key=bst.vol.get)
            M.append({"k": "POC", "p": poc})
            if bst.lot:
                M.append({"k": "VWAP", "p": round(bst.tl / bst.lot, 4)})
            if bst.ao:
                M.append({"k": "AKT. ALIŞ ORT.", "p": round(bst.ao, 4)})
        try:
            R = self.m.days.get(day)
            rr = [r for r in (R.rows if R is not None and R.ready else []) if r["s"] == sym]
            rr.sort(key=lambda r: (-r.get("israr", 0), -r["btl"]))
            for r in rr[:3]:
                M.append({"k": "MALİYET", "br": r["br"], "p": r["cur"], "israr": r.get("israr"), "sc": r.get("sc")})
        except Exception:
            pass
        return {"list": M}

    def _alarms_for(self, sym, day, live):
        hub = self.hub
        L = []
        if hub is not None:
            try:
                with hub.lock:
                    evs = list(hub.events)
                for ev in evs:
                    if ev.get("sym") == sym and ev.get("nt") in NT_DEFAULTS:
                        L.append({"time": ev.get("time"), "nt": ev.get("nt"), "title": ev.get("title"), "text": ev.get("text")})
            except Exception:
                pass
        out = {"list": L[-20:][::-1]}
        if not live:
            out["note"] = "Derinlik alarmları " + LIVE_NOTE.split(" — ")[0] + " (hafta içi 10:05–18:00)."
        return out

    def _score(self, R, S, hist, bids, asks, live, tv, last):
        comps = []
        def add(lbl, v):
            if v:
                comps.append([lbl, round(v, 1)])
        b10 = sum(l for _, l, _ in bids[:10]); a10 = sum(l for _, l, _ in asks[:10])
        r10 = _ratio(b10, a10)
        if b10 > 0 and a10 > 0:
            add(f"10 kademe alış/satış lot oranı {_fx(r10)}", max(-15, min(15, 12 * math.log2(max(0.05, r10)))))
        elif a10 > 0:
            add("alış tarafında bekleyen emir yok", -15)
        elif b10 > 0:
            add("satış tarafında bekleyen emir yok", 15)
        x1 = R.get(1) or {}
        ch = (x1.get("ch") or {}).get("10") if x1 else None
        if ch and ch.get("r0") and ch.get("r1"):
            add(f"son 1 dk denge {_fx(ch['r0'])}→{_fx(ch['r1'])}", max(-6, min(6, 6 * math.log2(max(0.05, ch["r1"]) / max(0.05, ch["r0"])))))
        W = R.get(2) or {}
        for w in W.get("a", []):
            if w.get("trend") == "ERİYOR" and (w.get("fill") or 0) > (w.get("canc") or 0):
                add(f"{_fp(w['p'])} satış duvarı işlemle eriyor", 6)
            elif w.get("trend") == "BÜYÜYOR":
                add(f"{_fp(w['p'])} satış duvarı büyüyor", -4)
        for w in W.get("b", [])[:2]:
            add(f"{_fp(w['p'])} alış duvarı ({_fs(w['tl'])} ₺)", 3)
        x3 = R.get(3) or {}
        if x3.get("list"):
            nb = x3.get("nb", 0); na = x3.get("na", 0)
            if nb:
                add(f"{nb} sahte alış duvarı (iptal)", -min(10, 4 * nb))
            if na:
                add(f"{na} satış duvarı fiyat yaklaşınca çekildi", min(6, 2 * na))
        x4 = R.get(4) or {}
        for z in x4.get("list", [])[:3]:
            add(f"{'alışta' if z['side'] == 'ALIŞ' else 'satışta'} gizli emir {_fp(z['p'])}", 5 if z["side"] == "ALIŞ" else -5)
        x7 = R.get(7) or {}
        if x7.get("m15"):
            n = x7["m15"]["net"]
            add(f"son 15 dk kademe çizme net {n:+d}", max(-8, min(8, n)))
        x10 = R.get(10) or {}
        if x10.get("n15"):
            add(f"son 15 dk {x10['n15']} süpürme", min(8, 2 * x10["n15"]))
        x8 = R.get(8) or {}
        if x8.get("at") == "tv":
            add(f"tavanda {_fs(x8.get('lot') or 0)} lot alış kuyruğu", 6 if x8.get("state") != "ERİYOR" else -8)
        elif x8.get("at") == "tb":
            add("tabanda satış kuyruğu", -10)
        x5 = R.get(5) or {}
        if x5.get("avg_a") is not None and x5["avg_a"] <= 10 and x5.get("done", 0) >= 3:
            add(f"süpürülen satış kademeleri hızla doluyor (ort. {x5['avg_a']:.0f} sn)", -4)
        sc = max(0, min(100, 50 + sum(v for _, v in comps)))
        comps.sort(key=lambda z: -abs(z[1]))
        lab = ("GÜÇLÜ ALIŞ" if sc >= 70 else "ALIŞ AĞIRLIKLI" if sc >= 57 else "GÜÇLÜ SATIŞ" if sc <= 30
               else "SATIŞ AĞIRLIKLI" if sc <= 43 else "DENGELİ")
        pos = [c for c in comps if c[1] > 0][:2]; neg = [c for c in comps if c[1] < 0][:2]
        y = f"Derinlik skoru {sc:.0f} ({lab})"
        if pos:
            y += ": " + ", ".join(c[0] for c in pos)
        if neg:
            y += ("; buna karşın " if pos else ": ") + ", ".join(c[0] for c in neg)
        y += "."
        if not hist:
            y += " (Derinlik geçmişi olmadan, son defter görüntüsü ve işlem verisiyle.)"
        return {"score": round(sc), "label": lab, "comps": comps[:10], "yorum": y}

    # ----------------------------------------------------------- alarms --
    def _alarm_hook(self, sym, b, a, sec):
        if not (CONT_FROM + 300 <= sec <= CONT_TO) or time.time() - self.alive_t0 < 300:
            return
        q = (getattr(self.feed, "quotes", {}) or {}).get(sym) or {}
        if (q.get("turnover") or 0) < ALARM_MIN_TL:
            return
        st = self.al_state.get(sym)
        bl, al = _levels(b, "b"), _levels(a, "a")
        b5, a5 = _tl(bl[:5]), _tl(al[:5])
        if st is None:
            st = self.al_state[sym] = {"h": collections.deque(maxlen=40), "pk": {}, "prev": (b, a)}
        st["h"].append((sec, b5, a5))
        pb, pa = st["prev"]
        st["prev"] = (b, a)
        cands = []
        # büyük emir girişi (ilk 5 kademe)
        for side, lv, P in (("b", bl, pb), ("a", al, pa)):
            lots = sorted(l for _, l, _ in lv[:10])
            med = lots[len(lots) // 2] if lots else 0
            for p, l, o in lv[:5]:
                d = l - (P.get(p, (0, 0))[0])
                if d * p >= 2_000_000 and d >= 4 * max(1.0, med):
                    cands.append((NT_BUYUK, f"{side}{p}", f"🧱 {sym} büyük {'alış' if side == 'b' else 'satış'} emri",
                                  f"{_fp(p)} ₺ kademesine +{_fs(d)} lot ({_fs(d * p)} ₺) girdi · kademede {_fs(l)} lot, {o} emir"))
                    break
        # duvar eriyor (en iyi 2 kademe)
        pk = st["pk"]
        for side, lv in (("b", bl), ("a", al)):
            for p, l, o in lv[:2]:
                k = (side, p)
                if l * p >= 1_000_000:
                    pk[k] = max(pk.get(k, 0), l)
                x = pk.get(k)
                if x and x * p >= 1_500_000 and l <= 0.4 * x:
                    cands.append((NT_DUVAR, f"{side}{p}", f"🫠 {sym} {'alış' if side == 'b' else 'satış'} duvarı eriyor",
                                  f"{_fp(p)} ₺ duvarı {_fs(x)} → {_fs(l)} lot (%{(1 - l / x) * 100:.0f} azaldı)"))
                    pk.pop(k, None)
        if len(pk) > 20:
            for k in list(pk)[:len(pk) - 20]:
                pk.pop(k, None)
        # alış yönüne sert denge kayması
        r = _ratio(b5, a5)
        if r and r >= 2.0 and b5 >= 1_000_000:
            old = [h for h in st["h"] if sec - h[0] <= 60]
            mn = min((_ratio(h[1], h[2]) or 99) for h in old) if old else None
            if mn is not None and mn <= 1.0:
                cands.append((NT_DENGE, "up", f"⚖️ {sym} derinlik alış yönüne döndü",
                              f"İlk 5 kademe alış/satış ₺ oranı 60 sn içinde {_fx(mn)} → {_fx(r)} (alış {_fs(b5)} ₺ / satış {_fs(a5)} ₺)"))
        if not cands:
            return
        now = time.time()
        while self.arate and now - self.arate[0] > 3600:
            self.arate.popleft()
        n = 0
        for nt, sub, title, txt in cands:
            key = (nt, sym)
            if now - self.alerted.get(key, 0) < 1800 or len(self.arate) >= 40 or n >= 5:
                continue
            self.alerted[key] = now
            self.arate.append(now)
            n += 1
            try:
                if self.hub is not None:
                    self.hub._emit("olay", nt, sym, title, txt, {"f": "derinlik", "price": q.get("last")})
                    self.emitted += 1
            except Exception as ex:   # pragma: no cover
                logger.debug("v125 emit: %s", ex)

    def status(self):
        R = self.rec
        return {"version": VERSION, "rec": {"day": R.day, "loops": R.loops, "lines": R.lines, "bytes": R.bytes, "errors": R.errors,
                                            "last_err": R.last_err, "timing": R.timing, "tracked": len(R.prev),
                                            "window": "hafta içi 09:55–18:15", "disk": R.disk()},
                "replay_states": len(self.ds), "alerts_emitted": self.emitted, "alerts_last_hour": len(self.arate)}


d_engine = DerinlikEngine()
