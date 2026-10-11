"""v1.18.0 — tüm gün işlem kaydı (tick store) + canlı olay dedektörü.

TradeStore
    İdealData, REQ_DERINLIK ile yalnızca SON 50 işlemi verir (geriye sayfalama yok — denendi).
    Bu yüzden tüm paylar SRV_DRN akışına abone edilir; her 'I' tick kaydedilir. Y34 (son 50)
    anlık görüntüleri boşluk doldurma / doğrulama için hizalanarak birleştirilir.
    Kayıtlar gün bazında diske yazılır (data/trades/YYYYMMDD/SYM.csv) → yeniden başlatmada kaybolmaz.

EventDetector
    Canlı fiyat akışı (Y26) üzerinde tüm paylar için tavan/taban, gün içi tam tur, devre kesici
    (sezgisel), ani hacim / RVOL, 52 haftalık zirve/dip ve kapanış olaylarını üretir.
    Olaylar data/events/YYYYMMDD.jsonl dosyasına eklenir.
"""
from __future__ import annotations

import array
import bisect
import collections
import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

logger = logging.getLogger("live_store")
IST = ZoneInfo("Europe/Istanbul")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TRADES_DIR = DATA_DIR / "trades"
EVENTS_DIR = DATA_DIR / "events"
SNAP_N = 50                      # İdealData Y34 snapshot size
SESSION_OPEN_SEC = 9 * 3600 + 55 * 60   # 09:55 açılış seansı (tek fiyat) başlangıcı
SNAP_ACCEPT_FROM = 9 * 3600 + 50 * 60   # bundan önce gelen Y34 anlık görüntüleri önceki güne aittir
SIDE_CODE = {"buy": 1, "sell": 2, "auction": 0}
SIDE_NAME = {1: "buy", 2: "sell", 0: "auction", 3: "other"}


def _now() -> datetime:
    return datetime.now(IST)


def _day() -> str:
    return _now().strftime("%Y%m%d")


def _sec_now() -> int:
    n = _now()
    return n.hour * 3600 + n.minute * 60 + n.second


def _tsec(t: str | None) -> int | None:
    if not t:
        return None
    try:
        h, m, s = t.split(":")[:3]
        return int(h) * 3600 + int(m) * 60 + int(float(s))
    except Exception:
        return None


def _hms(sec: int) -> str:
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


class _Sym:
    __slots__ = ("t", "p", "l", "sd", "b", "s", "flushed", "dirty", "complete_since", "gaps",
                 "first_seen", "snap_merges", "stream_n", "lot_sum", "bcnt")

    def __init__(self) -> None:
        self.t = array.array("I")
        self.p = array.array("d")
        self.l = array.array("q")
        self.sd = bytearray()
        self.b = array.array("H")
        self.s = array.array("H")
        self.flushed = 0          # rows already on disk (append mode)
        self.dirty = False        # middle of the list changed → rewrite file
        self.complete_since: int | None = None   # seconds of day; 0 = since session open
        self.gaps: list[list[int]] = []
        self.first_seen: int | None = None
        self.snap_merges = 0
        self.stream_n = 0
        self.lot_sum = 0
        self.bcnt: dict = {}      # v1.37.0: aracı kurum işlem sayısı — artımlı (sorguda O(n) sayım yok)

    def row(self, i: int) -> tuple:
        return (self.t[i], self.p[i], self.l[i], self.sd[i], self.b[i], self.s[i])

    def append(self, k: tuple) -> None:
        self.t.append(k[0]); self.p.append(k[1]); self.l.append(k[2])
        self.sd.append(k[3]); self.b.append(k[4]); self.s.append(k[5])
        self.lot_sum += k[2]
        bc = self.bcnt
        bc[k[4]] = bc.get(k[4], 0) + 1
        bc[k[5]] = bc.get(k[5], 0) + 1

    def truncate(self, n: int) -> None:
        for arr in (self.t, self.p, self.l, self.b, self.s):
            del arr[n:]
        del self.sd[n:]
        self.lot_sum = sum(self.l)
        bc: dict = {}
        for x in self.b:
            bc[x] = bc.get(x, 0) + 1
        for x in self.s:
            bc[x] = bc.get(x, 0) + 1
        self.bcnt = bc


class TradeStore:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.day: str | None = None
        self.syms: dict[str, _Sym] = {}
        self.brokers: list[str] = [""]
        self.bidx: dict[str, int] = {"": 0}
        self._brokers_flushed = 1
        self.started_at = time.time()
        self.started_sec = _sec_now()
        self.loaded_rows = 0
        self.stream_rows = 0
        self.snapshot_rows = 0
        self.gap_count = 0
        self.on_trade: Callable[[str, tuple], None] | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        # canlı akış (tüm paylara abonelik) kesintisiz açık mı; açık olduğu ilk saniye (gün içi)
        self._live = False
        self.live_since: int | None = None
        self.live_history: list[list] = []

    def set_live(self, on: bool, reason: str = "") -> None:
        """Feed: tüm-pay aboneliği açıldı (True) / bağlantı koptu (False)."""
        with self.lock:
            if on and not self._live:
                self.live_since = _sec_now()
                self.live_history.append([_hms(self.live_since), None, reason])
            elif not on and self._live:
                if self.live_history and self.live_history[-1][1] is None:
                    self.live_history[-1][1] = _hms(_sec_now())
                self.live_since = None
            self._live = on
            self.live_history = self.live_history[-20:]

    # ---------------------------------------------------------------- day / io
    def _dir(self, day: str | None = None) -> Path:
        return TRADES_DIR / (day or self.day or _day())

    def ensure_day(self) -> None:
        d = _day()
        if d == self.day:
            return
        with self.lock:
            if d == self.day:
                return
            if self.day:
                try:
                    self._flush_locked()
                except Exception as e:
                    logger.warning("trade flush on rollover: %s", e)
            new_day = self.day is not None
            self.day = d
            self.syms = {}
            self.brokers = [""]
            self.bidx = {"": 0}
            self._brokers_flushed = 1
            self.gap_count = 0
            if new_day and self._live:
                # gün dönümünde akış zaten açık → yeni gün açılıştan itibaren eksiksiz kaydedilecek
                self.live_since = 0
                self.live_history = [["00:00:00", None, "gün dönümü"]]
            self._load(d)

    def _load(self, day: str) -> None:
        p = self._dir(day)
        if not p.exists():
            return
        t0 = time.time()
        try:
            bf = p / "_brokers.txt"
            if bf.exists():
                names = bf.read_text(encoding="utf-8").split("\n")
                if names and names[-1] == "":
                    names = names[:-1]
                self.brokers = [""] + names[1:] if names and names[0] == "" else [""] + names
                self.bidx = {n: i for i, n in enumerate(self.brokers)}
                self._brokers_flushed = len(self.brokers)
            meta = {}
            mf = p / "_meta.json"
            if mf.exists():
                meta = json.loads(mf.read_text(encoding="utf-8"))
            n = 0
            for f in p.glob("*.csv"):
                sym = f.stem
                e = _Sym()
                with f.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        c = line.rstrip("\n").split(",")
                        if len(c) < 6:
                            continue
                        try:
                            e.append((int(c[0]), float(c[1]), int(c[2]), int(c[3]), int(c[4]), int(c[5])))
                        except ValueError:
                            continue
                e.flushed = len(e.t)
                m = meta.get(sym) or {}
                e.complete_since = m.get("complete_since")
                e.gaps = m.get("gaps") or []
                e.first_seen = m.get("first_seen")
                self.syms[sym] = e
                n += len(e.t)
            self.loaded_rows = n
            # downtime gap: everything after the last stored trade until now is unknown until merged
            logger.info("trade store: %s yüklendi, %d hisse / %d işlem (%.1f sn)", day, len(self.syms), n, time.time() - t0)
        except Exception as e:
            logger.warning("trade store load: %s", e)

    def _flush_locked(self) -> None:
        if not self.day:
            return
        p = self._dir()
        p.mkdir(parents=True, exist_ok=True)
        if len(self.brokers) > self._brokers_flushed:
            with (p / "_brokers.txt").open("a", encoding="utf-8") as fh:
                if self._brokers_flushed <= 1 and not (p / "_brokers.txt").stat().st_size:
                    fh.write("\n")  # index 0 = ""
                for nm in self.brokers[self._brokers_flushed:]:
                    fh.write(nm.replace("\n", " ") + "\n")
            self._brokers_flushed = len(self.brokers)
        meta_changed = False
        for sym, e in self.syms.items():
            n = len(e.t)
            if e.dirty:
                tmp = p / f"{sym}.csv.tmp"
                with tmp.open("w", encoding="utf-8") as fh:
                    fh.write("".join(f"{e.t[i]},{e.p[i]:g},{e.l[i]},{e.sd[i]},{e.b[i]},{e.s[i]}\n" for i in range(n)))
                os.replace(tmp, p / f"{sym}.csv")
                e.flushed = n
                e.dirty = False
                meta_changed = True
            elif n > e.flushed:
                with (p / f"{sym}.csv").open("a", encoding="utf-8") as fh:
                    fh.write("".join(f"{e.t[i]},{e.p[i]:g},{e.l[i]},{e.sd[i]},{e.b[i]},{e.s[i]}\n" for i in range(e.flushed, n)))
                e.flushed = n
                meta_changed = True
        if meta_changed:
            meta = {s: {"complete_since": e.complete_since, "gaps": e.gaps[-50:], "first_seen": e.first_seen}
                    for s, e in self.syms.items()}
            tmp = p / "_meta.json.tmp"
            tmp.write_text(json.dumps(meta), encoding="utf-8")
            os.replace(tmp, p / "_meta.json")

    def flush(self) -> None:
        with self.lock:
            self._flush_locked()

    def start(self) -> None:
        self.ensure_day()
        if self._thread and self._thread.is_alive():
            return

        def _loop():
            while not self._stop.wait(3.0):
                try:
                    self.ensure_day()
                    self.flush()
                except Exception as e:
                    logger.warning("trade store flush: %s", e)
        self._thread = threading.Thread(target=_loop, name="trade-store", daemon=True)
        self._thread.start()

    # -------------------------------------------------------------- ingestion
    def _bi(self, name: str | None) -> int:
        name = (name or "").strip()
        i = self.bidx.get(name)
        if i is None:
            i = len(self.brokers)
            self.brokers.append(name)
            self.bidx[name] = i
        return i

    def _key(self, r: dict) -> tuple | None:
        t = _tsec(r.get("time"))
        p = r.get("price")
        if t is None or not p:
            return None
        return (t, round(float(p), 6), int(round(r.get("lot") or 0)), SIDE_CODE.get(r.get("side"), 3),
                self._bi(r.get("buyer")), self._bi(r.get("seller")))

    def add_stream(self, sym: str, r: dict) -> None:
        if self.day != _day():
            self.ensure_day()
        with self.lock:
            k = self._key(r)
            if k is None:
                return
            e = self.syms.get(sym)
            if e is None:
                e = self.syms[sym] = _Sym()
                e.first_seen = k[0]
                live = self.live_since
                if live is not None and live <= SESSION_OPEN_SEC and live <= k[0]:
                    e.complete_since = 0  # akış açılıştan önce başladı → bu hissenin tüm günü kayıtlı
            e.append(k)
            e.stream_n += 1
            self.stream_rows += 1
        cb = self.on_trade
        if cb:
            try:
                cb(sym, k)
            except Exception:
                pass

    def merge_snapshot(self, sym: str, rows: list[dict]) -> None:
        """Align a Y34 'last 50' snapshot (oldest→newest) with the stored list."""
        if self.day != _day():
            self.ensure_day()
        now_s = _sec_now()
        if now_s < SNAP_ACCEPT_FROM:
            return  # seans öncesi: Y34 önceki günün son işlemlerini taşır
        with self.lock:
            S = [k for k in (self._key(r) for r in rows) if k is not None]
            # gelecekteki saatler = önceki güne ait satırlar
            S = [k for k in S if k[0] <= now_s + 120]
            if not S:
                return
            e = self.syms.get(sym)
            if e is None:
                e = self.syms[sym] = _Sym()
            n = len(e.t)
            if n == 0:
                for k in S:
                    e.append(k)
                e.first_seen = e.first_seen or S[0][0]
                # fewer than 50 → the snapshot IS the whole day; also complete if we were live before
                # the opening session and before this symbol's first trade
                live = self.live_since
                if len(rows) < SNAP_N or (live is not None and live <= SESSION_OPEN_SEC and live <= S[0][0]):
                    e.complete_since = 0
                else:
                    e.complete_since = S[0][0]
                e.dirty = True
                self.snapshot_rows += len(S)
                return
            t0 = S[0][0]
            i0 = bisect.bisect_left(e.t, t0)
            if n - i0 > 20000:
                return
            W = [e.row(i) for i in range(i0, n)]
            cW = collections.Counter(W)
            cS = collections.Counter(S)
            missing = cS - cW
            if e.complete_since is None:
                e.complete_since = 0 if len(rows) < SNAP_N else min(t0, e.first_seen or t0)
            if not missing:
                return
            overlap = cS & cW
            if not overlap and len(rows) >= SNAP_N and n and S[0][0] >= e.t[n - 1]:
                # no common trade → trades between our last and the snapshot start may be lost
                e.gaps.append([int(e.t[n - 1]), int(S[0][0])])
                self.gap_count += 1
            # rebuild window: unmatched stored trades at the first second stay before the snapshot
            rem = collections.Counter(S)
            before, after = [], []
            for k in W:
                if rem.get(k, 0) > 0:
                    rem[k] -= 1
                    continue
                (before if k[0] == t0 else after).append(k)
            neww = before + S + after
            neww.sort(key=lambda k: k[0])
            e.truncate(i0)
            for k in neww:
                e.append(k)
            e.dirty = True
            e.snap_merges += 1
            self.snapshot_rows += sum(missing.values())

    # ------------------------------------------------------------------ query
    def coverage(self, sym: str, day_volume: float | None = None) -> dict:
        with self.lock:
            e = self.syms.get(sym)
            if not e:
                return {"count": 0, "lot": 0, "complete_since": None, "gaps": [], "coverage_pct": None}
            cov = None
            if day_volume:
                cov = round(min(100.0, e.lot_sum / day_volume * 100.0), 2)
            cs = e.complete_since
            return {"count": len(e.t), "lot": e.lot_sum,
                    "first_time": _hms(e.t[0]) if len(e.t) else None,
                    "last_time": _hms(e.t[-1]) if len(e.t) else None,
                    "complete_since": (None if cs is None else ("açılış" if cs == 0 else _hms(cs))),
                    "complete_from_open": cs == 0 and not e.gaps,
                    "gaps": [[_hms(a), _hms(b)] for a, b in e.gaps[-10:]], "gap_count": len(e.gaps),
                    "coverage_pct": cov, "stream_n": e.stream_n, "snap_merges": e.snap_merges}

    def query(self, sym: str, broker: str | None = None, side: str | None = None,
              minutes: int | None = None, min_tl: float | None = None, lot_eq: int | None = None,
              lot_ge: int | None = None, sort: str = "time", offset: int = 0, limit: int = 200) -> dict:
        """v1.37.0: kilit altında yalnızca C düzeyinde dizi kopyası (µs); filtre/sıralama numpy ile kilit dışında.
        Eskiden kilit altında n işlem üzerinde 2 Python döngüsü vardı → gün boyu n büyüdükçe akış (WS thread'i
        aynı kilidi bekler) geride kalıyordu: kök neden buydu."""
        import numpy as np
        with self.lock:
            e = self.syms.get(sym)
            if not e:
                return {"rows": [], "total": 0, "all_count": 0, "brokers": [], "sums": {}}
            n = len(e.t)
            T = np.frombuffer(e.t, dtype=np.uint32, count=n).copy()
            P = np.frombuffer(e.p, dtype=np.float64, count=n).copy()
            L = np.frombuffer(e.l, dtype=np.int64, count=n).copy()
            SD = np.frombuffer(bytes(e.sd[:n]), dtype=np.uint8)
            B = np.frombuffer(e.b, dtype=np.uint16, count=n).copy()
            S_ = np.frombuffer(e.s, dtype=np.uint16, count=n).copy()
            bcnt = dict(e.bcnt)
            br = list(self.brokers)
            bi = self.bidx.get(broker) if broker else None
        m = np.ones(n, dtype=bool)
        if broker and bi is None:
            m[:] = False
        else:
            if minutes:
                m[:bisect.bisect_left(T, max(0, _sec_now() - int(minutes) * 60))] = False
            sd_want = {"buy": 1, "sell": 2}.get(side or "")
            if bi is not None:
                if sd_want == 1:
                    m &= B == bi
                elif sd_want == 2:
                    m &= S_ == bi
                else:
                    m &= (B == bi) | (S_ == bi)
            elif sd_want:
                m &= SD == sd_want
            if lot_eq is not None:
                m &= L == lot_eq
            if lot_ge is not None:
                m &= L >= lot_ge
            if min_tl:
                m &= L * P >= min_tl
        idx = np.nonzero(m)[0]
        tot = int(len(idx))
        Li, Pi, SDi = L[idx], P[idx], SD[idx]
        buy_lot = int(Li[SDi == 1].sum()); sell_lot = int(Li[SDi == 2].sum())
        tl = float((Li * Pi).sum()); lot_all = int(Li.sum())
        if sort == "lot":
            o = np.lexsort((-idx, -Li))
        elif sort in ("tl", "hacim", "volume"):
            o = np.lexsort((-idx, -(Li * Pi)))
        elif sort in ("time_asc", "asc"):
            o = None
        else:
            o = np.arange(tot - 1, -1, -1)
        page = (idx if o is None else idx[o])[offset: offset + limit]
        rows = [{"n": int(i), "time": _hms(int(T[i])), "price": float(P[i]), "lot": int(L[i]),
                 "side": SIDE_NAME.get(int(SD[i]), "other"),
                 "buyer": br[B[i]] or None, "seller": br[S_[i]] or None, "tl": round(float(L[i] * P[i]), 2)}
                for i in page]
        brokers = [{"name": br[k], "count": v} for k, v in sorted(bcnt.items(), key=lambda x: -x[1]) if k < len(br) and br[k]]
        return {"rows": rows, "total": tot, "all_count": n, "offset": offset, "limit": limit,
                "brokers": brokers, "last_sec": int(T[-1]) if n else None, "server_ts": time.time(),
                "sums": {"lot": lot_all, "buy_lot": buy_lot, "sell_lot": sell_lot, "tl": round(tl, 2)}}

    def broker_agg(self, sym: str) -> dict[str, dict]:
        """Per-broker buy/sell lots & VWAPs from the recorded ticks (AKD fallback)."""
        with self.lock:
            e = self.syms.get(sym)
            if not e:
                return {}
            agg: dict[int, list] = {}
            for i in range(len(e.t)):
                lot, px = e.l[i], e.p[i]
                a = agg.setdefault(e.b[i], [0, 0.0, 0, 0.0])
                a[0] += lot; a[1] += lot * px
                a = agg.setdefault(e.s[i], [0, 0.0, 0, 0.0])
                a[2] += lot; a[3] += lot * px
            return {self.brokers[k]: {"buy_lot": v[0], "buy_tl": v[1], "sell_lot": v[2], "sell_tl": v[3]}
                    for k, v in agg.items() if self.brokers[k]}

    def stats(self) -> dict:
        with self.lock:
            n = sum(len(e.t) for e in self.syms.values())
            full = sum(1 for e in self.syms.values() if e.complete_since == 0 and not e.gaps)
            return {"day": self.day, "symbols": len(self.syms), "trades": n, "loaded_rows": self.loaded_rows,
                    "stream_rows": self.stream_rows, "snapshot_rows": self.snapshot_rows, "gaps": self.gap_count,
                    "complete_from_open_symbols": full, "brokers": len(self.brokers) - 1,
                    "started": _hms(self.started_sec), "live": self._live,
                    "live_since": None if self.live_since is None else _hms(self.live_since),
                    "live_before_open": self.live_since is not None and self.live_since <= SESSION_OPEN_SEC,
                    "live_history": self.live_history[-5:]}


trade_store = TradeStore()


# =============================================================== EVENTS ====
KINDS = ("tavan", "taban", "tur", "devre", "hacim", "52h", "kapanis", "diger")


class EventDetector:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.day: str | None = None
        self.events: list[dict] = []
        self.counts: collections.Counter = collections.Counter()
        self.st: dict[str, dict] = {}
        self.dipzirve: dict[str, dict] = {}
        self.dipzirve_ts = 0.0
        self.feed = None
        self.universe_fn: Callable[[], list[str]] | None = None
        self.prev_volume_fn: Callable[[str], float | None] | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._seq = 0
        self.started_sec = _sec_now()
        self.loops = 0

    # ------------------------------------------------------------- persistence
    def _file(self) -> Path:
        return EVENTS_DIR / f"{self.day}.jsonl"

    def _ensure_day(self) -> None:
        d = _day()
        if d == self.day:
            return
        with self.lock:
            self.day = d
            self.events = []
            self.counts = collections.Counter()
            self.st = {}
            self._seq = 0
            f = self._file()
            if f.exists():
                for line in f.read_text(encoding="utf-8").splitlines():
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    if _post_close_noise(ev):      # v1.22.0: kapanış sonrası ertesi gün limitleri → sahte tavan/taban çözülmesi
                        continue
                    self._apply_loaded(ev)
                logger.info("events: %s yüklendi (%d olay)", d, len(self.events))

    def _apply_loaded(self, ev: dict) -> None:
        self.events.append(ev)
        self.counts[ev["kind"]] += 1
        self._seq = max(self._seq, ev.get("id", 0))
        s = self._sym_state(ev["sym"]) if ev.get("sym") else None
        if s is None:
            return
        k, v = ev["kind"], ev.get("variant")
        if k == "tavan":
            if v == "on":
                s["tavan_n"] += 1
                s["at_ceiling"] = True
            else:
                s["at_ceiling"] = False
        elif k == "taban":
            if v == "on":
                s["taban_n"] += 1
                s["at_floor"] = True
            else:
                s["at_floor"] = False
        elif k == "tur":
            s["tur"] = True
        elif k == "52h":
            s["h52" if v == "high" else "l52"] = True
        elif k == "hacim" and v and v.startswith("rvol"):
            try:
                s["rvol_lv"] = max(s["rvol_lv"], float(v[4:]))
            except ValueError:
                pass
        elif k == "kapanis":
            s["kapanis"] = True
        elif k == "devre":
            s["devre_on"] = v == "on"
        s["seen"] = True

    def _sym_state(self, sym: str) -> dict:
        s = self.st.get(sym)
        if s is None:
            s = self.st[sym] = {"seen": False, "at_ceiling": False, "at_floor": False, "tavan_n": 0, "taban_n": 0,
                                "off_c": 0, "off_f": 0, "tur": False, "h52": False, "l52": False, "rvol_lv": 0.0,
                                "vol": collections.deque(maxlen=90), "spike_ts": 0.0, "kapanis": False,
                                "cross_since": None, "uncross_since": None, "devre_on": False, "devre_start": None,
                                "state": None, "last_auction_ev": 0.0}
        return s

    def emit(self, kind: str, sym: str | None, text: str, variant: str | None = None,
             price: float | None = None, extra: dict | None = None, ts: float | None = None) -> dict:
        with self.lock:
            self._seq += 1
            now = _now() if ts is None else datetime.fromtimestamp(ts, IST)
            ev = {"id": self._seq, "ts": round(now.timestamp(), 3), "time": now.strftime("%H:%M:%S"),
                  "kind": kind, "variant": variant, "sym": sym, "text": text, "price": price}
            if extra:
                ev.update(extra)
            try:
                ev["cumle"] = cumle(ev, self._names().get(sym or ""))   # v1.22.0 tam Türkçe cümle
            except Exception:
                pass
            self.events.append(ev)
            self.counts[kind] += 1
            try:
                EVENTS_DIR.mkdir(parents=True, exist_ok=True)
                with self._file().open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.debug("event write: %s", e)
            return ev

    # ------------------------------------------------------------------ query
    def _fallback_events(self) -> tuple[str | None, list[dict]]:
        """v1.22.0: bugün henüz olay yoksa (hafta sonu / seans öncesi) son işlem gününün olayları."""
        try:
            fs = sorted(p for p in EVENTS_DIR.glob("2*.jsonl") if p.stem < (self.day or _day()))
        except Exception:
            fs = []
        for fp in reversed(fs[-6:]):
            try:
                mt = fp.stat().st_mtime
            except OSError:
                continue
            cache = getattr(self, "_fb_cache", None)
            if cache and cache[0] == fp.stem and cache[1] == mt:
                return cache[0], cache[2]
            evs = []
            for line in fp.read_text(encoding="utf-8").splitlines():
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if _post_close_noise(ev):
                    continue
                evs.append(ev)
            if evs:
                self._fb_cache = (fp.stem, mt, evs)
                return fp.stem, evs
        return None, []

    def _names(self) -> dict:
        try:
            return dict(getattr(self.feed, "names", {}) or {})
        except Exception:
            return {}

    def query(self, kind: str | None = None, q: str | None = None, syms: list[str] | None = None,
              since_id: int = 0, limit: int = 300) -> dict:
        fb_day = None
        with self.lock:
            evs = self.events
            if not evs:
                fb_day, fevs = self._fallback_events()
                if fb_day:
                    evs = fevs
                    since_id = 0
        names = self._names()
        with self.lock:
            out = []
            qq = (q or "").strip().upper()
            symset = set(syms) if syms else None
            for ev in reversed(evs):
                if ev["id"] <= since_id:
                    break
                if kind and kind != "all":
                    kk = ("tavan", "taban") if kind in ("tavantaban", "tavan/taban") else (kind,)
                    if ev["kind"] not in kk:
                        continue
                if symset is not None and ev.get("sym") not in symset:
                    continue
                cm = ev.get("cumle") or cumle(ev, names.get(ev.get("sym") or ""))
                if qq and qq not in (ev.get("sym") or "") and qq not in ev["text"].upper() and qq not in cm.upper():
                    continue
                e2 = dict(ev)
                e2["cumle"] = cm
                out.append(e2)
                if len(out) >= limit:
                    break
            c = dict(self.counts) if not fb_day else dict(collections.Counter(e["kind"] for e in evs))
            c["tavantaban"] = c.get("tavan", 0) + c.get("taban", 0)
            c["all"] = len(evs)
            fav = None
            if symset is not None:
                fav = sum(1 for ev in evs if ev.get("sym") in symset)
            res = {"day": fb_day or self.day, "events": out, "counts": c, "fav_count": fav,
                   "last_id": evs[-1]["id"] if evs else 0, "started": _hms(self.started_sec)}
            if fb_day:
                res["fallback"] = True
                res["today"] = self.day
                res["note"] = f"Bugün henüz olay yok (piyasa kapalı) — son işlem günü {_day_label(fb_day)} olayları gösteriliyor."
                res["last_id"] = 0          # bugünün olayları başlayınca istemci baştan yükler
            return res

    # --------------------------------------------------------------- detector
    def start(self, feed, universe_fn=None, prev_volume_fn=None) -> None:
        self.feed = feed
        self.universe_fn = universe_fn
        self.prev_volume_fn = prev_volume_fn
        self._ensure_day()
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, name="event-detector", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop.wait(1.0):
            try:
                self._ensure_day()
                self._tick()
                self.loops += 1
            except Exception as e:
                logger.warning("event detector: %s", e)
                time.sleep(2)

    def _refresh_dipzirve(self) -> None:
        f = self.feed
        if not f or not f.healthy():
            return
        if time.time() - self.dipzirve_ts < 1200 and self.dipzirve:
            return
        self.dipzirve_ts = time.time()
        try:
            frames = [["X", "REQ_DIPZIRVE_VALUES", f.user, f._session or "", "XUTUM", "250"]]
            res = f.request_wait(frames, "SRV_DIPZIRVE_VALUES", lambda p: len(p) > 4, need=1, timeout=12.0)
            if not res:
                return
            data = json.loads(res[-1][4])
            snap = {r["s"]: {"high": r.get("z"), "low": r.get("d"), "last": r.get("l")} for r in data.get("d") or [] if r.get("s")}
            if not snap:
                return
            ref = EVENTS_DIR / f"dipzirve_{self.day}.json"
            if ref.exists():
                try:
                    base = json.loads(ref.read_text(encoding="utf-8"))
                    for s, v in snap.items():  # keep the first (morning) reference of the day
                        if s in base:
                            snap[s] = {**v, "high": base[s].get("high"), "low": base[s].get("low")}
                except Exception:
                    pass
            else:
                EVENTS_DIR.mkdir(parents=True, exist_ok=True)
                ref.write_text(json.dumps(snap), encoding="utf-8")
            self.dipzirve = snap
        except Exception as e:
            logger.debug("dipzirve: %s", e)

    def on_trade(self, sym: str, k: tuple) -> None:
        """Mid-session single-price (auction-side) match → volatility auction / devre kesici ended."""
        if k[3] != 0:
            return
        sec = k[0]
        if not (10 * 3600 + 60 <= sec <= 17 * 3600 + 59 * 60):
            return
        f = self.feed
        if not f:
            return
        q = f.quotes.get(sym) or {}
        if q.get("v_raw") == "55":   # tek fiyat pazarı — zaten gün boyu seanslı
            return
        with self.lock:
            s = self._sym_state(sym)
            now = time.time()
            if now - s["last_auction_ev"] < 600:
                return
            s["last_auction_ev"] = now
            dur = ""
            if s.get("devre_start"):
                dur = f" · ~{max(1, round((now - s['devre_start']) / 60))} dk sürdü"
            s["devre_on"] = False
            s["devre_start"] = None
            self.emit("devre", sym, f"Devre kesici kalktı · tek fiyat eşleşme {_fp(k[1])} ₺{dur}", "off", k[1])

    def _tick(self) -> None:
        f = self.feed
        if not f or not f.healthy():
            return
        nowdt = _now()
        if nowdt.weekday() >= 5:
            return
        sec = nowdt.hour * 3600 + nowdt.minute * 60 + nowdt.second
        if sec < 9 * 3600 + 56 * 60 or sec > 18 * 3600 + 20 * 60:
            return
        self._refresh_dipzirve()
        uni = self.universe_fn() if self.universe_fn else list(f.quotes.keys())
        now = time.time()
        cont = 10 * 3600 <= sec < 18 * 3600
        open_min = max(1.0, (sec - 10 * 3600) / 60.0)
        with f._lock:
            snap = {s: dict(f.quotes[s]) for s in uni if s in f.quotes}
        for sym, q in snap.items():
            last, ceil_, floor_ = q.get("last"), q.get("ceiling"), q.get("floor")
            prev = q.get("prev_close")
            if not last or not prev:
                continue
            if not (q.get("volume") or 0) > 0:
                continue  # no trade today yet
            with self.lock:
                s = self._sym_state(sym)
                first = not s["seen"]
                s["seen"] = True
                chg = (last - prev) / prev * 100.0
                if sec > 18 * 3600 + 10 * 60 + 20:
                    # v1.22.0: kapanış sonrası İdealData ertesi günün limitlerini yayınlar → yalnız kapanış özeti
                    if not s["kapanis"]:
                        s["kapanis"] = True
                        if s["at_ceiling"]:
                            self.emit("kapanis", sym, f"Tavanda kapattı · {_fp(last)} ₺", "tavan", last)
                        elif s["at_floor"]:
                            self.emit("kapanis", sym, f"Tabanda kapattı · {_fp(last)} ₺", "taban", last)
                        elif abs(chg) >= 7:
                            self.emit("kapanis", sym, f"Günü {_pct(chg)} ile kapattı · {_fp(last)} ₺", "pos" if chg > 0 else "neg", last)
                    continue
                # ---- tavan
                if ceil_ and last >= ceil_ - 1e-9:
                    s["off_c"] = 0
                    if not s["at_ceiling"]:
                        s["at_ceiling"] = True
                        s["tavan_n"] += 1
                        n = s["tavan_n"]
                        txt = ("Tavanda" if first else ("Tavan oldu" if n == 1 else f"{n}. kez tavan")) + f" · {_fp(last)} ₺"
                        self.emit("tavan", sym, txt, "on", last, {"n": n, "initial": first})
                elif s["at_ceiling"]:
                    s["off_c"] += 1
                    if s["off_c"] >= 3:
                        s["at_ceiling"] = False
                        self.emit("tavan", sym, f"Tavandan döndü · {_fp(last)} ₺", "off", last)
                # ---- taban
                if floor_ and last <= floor_ + 1e-9:
                    s["off_f"] = 0
                    if not s["at_floor"]:
                        s["at_floor"] = True
                        s["taban_n"] += 1
                        n = s["taban_n"]
                        txt = ("Tabanda" if first else ("Taban oldu" if n == 1 else f"{n}. kez taban")) + f" · {_fp(last)} ₺"
                        self.emit("taban", sym, txt, "on", last, {"n": n, "initial": first})
                elif s["at_floor"]:
                    s["off_f"] += 1
                    if s["off_f"] >= 3:
                        s["at_floor"] = False
                        self.emit("taban", sym, f"Tabandan çözüldü · {_fp(last)} ₺", "off", last)
                # ---- gün içi tam tur
                hi, lo = q.get("high"), q.get("low")
                if not s["tur"] and hi and lo:
                    hp, lp = (hi - prev) / prev * 100.0, (lo - prev) / prev * 100.0
                    if hp >= 5.0 and lp <= -5.0 and hp - lp >= 12.0:
                        s["tur"] = True
                        self.emit("tur", sym, f"Gün içi tam tur · {_pct(lp)} ↔ {_pct(hp)}", None, last)
                # ---- devre kesici (sezgisel: çapraz kotasyon = tek fiyat emir toplama)
                bid, ask = q.get("bid"), q.get("ask")
                if cont and q.get("v_raw") != "55" and sec > 10 * 3600 + 120:
                    crossed = bool(bid and ask and bid >= ask)
                    if crossed:
                        s["uncross_since"] = None
                        if s["cross_since"] is None:
                            s["cross_since"] = now
                        if not s["devre_on"] and now - s["cross_since"] >= 4:
                            s["devre_on"] = True
                            s["devre_start"] = s["cross_since"]
                            self.emit("devre", sym, f"Devre kesici / tek fiyat · alış {_fp(bid)} ≥ satış {_fp(ask)}", "on", last)
                    else:
                        s["cross_since"] = None
                        if s["devre_on"]:
                            if s["uncross_since"] is None:
                                s["uncross_since"] = now
                            elif now - s["uncross_since"] >= 5:
                                dur = max(1, round((now - (s["devre_start"] or now)) / 60))
                                s["devre_on"] = False
                                s["devre_start"] = None
                                s["last_auction_ev"] = now
                                self.emit("devre", sym, f"Devre kesici kalktı · ~{dur} dk sürdü", "off", last)
                # ---- işlem durumu değişimi
                state = q.get("state")
                if state and s["state"] and state != s["state"]:
                    self.emit("diger", sym, f"İşlem durumu değişti · {s['state']} → {state}", None, last)
                if state:
                    s["state"] = state
                # ---- hacim
                vol, tov = q.get("volume") or 0.0, q.get("turnover") or 0.0
                dq = s["vol"]
                dq.append((now, vol, tov))
                if cont and len(dq) >= 2:
                    j = 0
                    while j < len(dq) - 1 and now - dq[j][0] > 62:
                        j += 1
                    t_old, v_old, tv_old = dq[j]
                    if now - t_old >= 50:
                        d_tl = tov - tv_old
                        avg = tov / open_min
                        if (open_min >= 15 and d_tl >= 2_500_000 and avg > 0 and d_tl >= 8 * avg
                                and now - s["spike_ts"] > 1800):
                            s["spike_ts"] = now
                            self.emit("hacim", sym, f"Ani hacim · 1 dk'da {_short(d_tl)} ₺ ({_x(d_tl / avg)} ort.)",
                                      "spike", last, {"tl": round(d_tl)})
                pv = None
                if self.prev_volume_fn:
                    try:
                        pv = self.prev_volume_fn(sym)
                    except Exception:
                        pv = None
                if pv and vol and tov >= 2_000_000:
                    r = vol / pv
                    for lv in (1.0, 2.0, 3.0, 5.0, 10.0):
                        if r >= lv > s["rvol_lv"]:
                            s["rvol_lv"] = lv
                            txt = ("Hacim dünkü toplamı aştı" if lv == 1.0 else f"Hacim dünün {int(lv)} katına ulaştı") + f" · RVOL {_x(r)}"
                            self.emit("hacim", sym, txt, f"rvol{lv:g}", last, {"rvol": round(r, 2)})
                # ---- 52 hafta
                dz = self.dipzirve.get(sym)
                if dz:
                    zh, dl = dz.get("high"), dz.get("low")
                    if zh and not s["h52"] and last >= zh - 1e-9:
                        s["h52"] = True
                        txt = (f"Yeni 52 haftalık zirve · {_fp(last)} ₺ (önceki {_fp(zh)})" if last > zh + 1e-9
                               else f"52 haftalık zirvede · {_fp(last)} ₺")
                        self.emit("52h", sym, txt, "high", last)
                    if dl and not s["l52"] and last <= dl + 1e-9:
                        s["l52"] = True
                        txt = (f"Yeni 52 haftalık dip · {_fp(last)} ₺ (önceki {_fp(dl)})" if last < dl - 1e-9
                               else f"52 haftalık dipte · {_fp(last)} ₺")
                        self.emit("52h", sym, txt, "low", last)
                # ---- kapanış
                if sec >= 18 * 3600 + 10 * 60 + 30 and not s["kapanis"]:
                    s["kapanis"] = True
                    if ceil_ and last >= ceil_ - 1e-9:
                        self.emit("kapanis", sym, f"Tavanda kapattı · {_fp(last)} ₺", "tavan", last)
                    elif floor_ and last <= floor_ + 1e-9:
                        self.emit("kapanis", sym, f"Tabanda kapattı · {_fp(last)} ₺", "taban", last)
                    elif abs(chg) >= 7:
                        self.emit("kapanis", sym, f"Günü {_pct(chg)} ile kapattı · {_fp(last)} ₺", "pos" if chg > 0 else "neg", last)


def _fp(v: float | None) -> str:
    if v is None:
        return "—"
    s = f"{v:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(v: float) -> str:
    s = f"{abs(v):.1f}".replace(".", ",")
    return ("+" if v > 0 else "-" if v < 0 else "") + "%" + s


def _x(v: float) -> str:
    return f"{v:.1f}".replace(".", ",") + "×"


def _short(v: float) -> str:
    a = abs(v)
    if a >= 1e9:
        return f"{a / 1e9:.2f} Mr".replace(".", ",")
    if a >= 1e6:
        return f"{a / 1e6:.1f} Mn".replace(".", ",")
    if a >= 1e3:
        return f"{a / 1e3:.0f} bin"
    return f"{a:.0f}"


_GUN = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def _day_label(d: str) -> str:
    try:
        dt = datetime.strptime(d, "%Y%m%d")
        return f"{dt.strftime('%d.%m.%Y')} {_GUN[dt.weekday()]}"
    except Exception:
        return d


def _post_close_noise(ev: dict) -> bool:
    """18:10:30 sonrası tavan/taban 'çözüldü' olayları: ertesi gün limitleri yayınlandığı için sahte."""
    return (ev.get("kind") in ("tavan", "taban", "tur") and (ev.get("variant") == "off" or ev.get("kind") == "tur")
            and (ev.get("time") or "") >= "18:10:30")


def _detail(text: str) -> str:
    t = text or ""
    return t.split(" · ", 1)[1] if " · " in t else ""


def cumle(ev: dict, name: str | None = None) -> str:
    """v1.22.0: Canlı Veri Akışı olayını okunur, tam bir Türkçe cümleye çevirir."""
    k, v = ev.get("kind"), ev.get("variant")
    sym = ev.get("sym") or "Piyasa"
    who = sym
    p = ev.get("price")
    px = f"{_fp(p)} ₺" if p else ""
    t = ev.get("text") or ""
    det = _detail(t)
    try:
        if k == "kademe":
            return t
        if k == "tavan":
            if v == "on":
                n = ev.get("n") or 1
                if ev.get("initial"):
                    return f"{who} izleme başladığında zaten tavan fiyatındaydı ({px}); alıcılar tavanda bekliyor."
                return (f"{who} tavana ulaştı: fiyat günlük üst limit olan {px} seviyesine çıktı" +
                        (f" — bugün {n}. kez tavana geliyor." if n > 1 else "; tavanda alıcı kuyruğu oluştu."))
            return f"{who} tavandan ayrıldı: tavandaki alıcılar çözüldü ve fiyat {px} seviyesine geriledi."
        if k == "taban":
            if v == "on":
                n = ev.get("n") or 1
                if ev.get("initial"):
                    return f"{who} izleme başladığında zaten taban fiyatındaydı ({px}); satıcılar tabanda bekliyor."
                return (f"{who} tabana indi: fiyat günlük alt limit olan {px} seviyesine düştü" +
                        (f" — bugün {n}. kez tabana geliyor." if n > 1 else "; tabanda satıcı kuyruğu oluştu."))
            return f"{who} tabandan çözüldü: tabandaki satışlar karşılandı ve fiyat {px} seviyesine yükseldi."
        if k == "tur":
            return f"{who} gün içinde tam tur attı: fiyat {det.replace(' ↔ ', ' ile ')} arasında gidip geldi (çok yüksek oynaklık); şu an {px}."
        if k == "devre":
            if v == "on":
                return (f"{who} için devre kesici / tek fiyat emir toplama başladı: alış fiyatı satış fiyatına eşit ya da üstünde "
                        f"(çapraz kotasyon), sürekli işlem geçici olarak durdu ({det}).")
            d2 = det.replace("tek fiyat eşleşme ", "tek fiyat eşleşmesi ").replace("~", "yaklaşık ")
            return f"{who} için devre kesici sona erdi ve sürekli işleme geri dönüldü" + (f" ({d2})." if d2 else ".") + (f" Son fiyat {px}." if px and px not in d2 else "")
        if k == "hacim":
            if v == "spike":
                import re as _re
                m = _re.search(r"([\d.,]+ (?:Mr|Mn|bin)?) ?₺ \(([\d,]+)×", t)
                tl = (m.group(1).strip() + " ₺") if m else (_short(ev["tl"]) + " ₺" if ev.get("tl") else "yüksek tutarda")
                kat = f"; bu, günün dakika başına ortalama işlem hacminin {m.group(2)} katı" if m else ""
                return f"{who} hissesinde ani hacim patlaması: son 1 dakikada {tl} işlem gerçekleşti{kat}. Fiyat {px}."
            rv = ev.get("rvol")
            if v == "rvol1":
                return f"{who} hissesinde bugünkü işlem hacmi dünün toplam hacmini şimdiden aştı (RVOL {_x(rv) if rv else det}); fiyat {px}."
            lv = (v or "rvol")[4:]
            return f"{who} hissesinde bugünkü işlem hacmi dünün {lv} katına ulaştı (RVOL {_x(rv) if rv else det}); ilgi olağanüstü yüksek, fiyat {px}."
        if k == "52h":
            if v == "high":
                if "Yeni" in t:
                    return f"{who} son 52 haftanın en yüksek fiyatını kırdı: yeni zirve {px} ({det.split('(')[-1].rstrip(')') if '(' in det else ''})."
                return f"{who} 52 haftalık zirve seviyesinde işlem görüyor: {px}."
            if "Yeni" in t:
                return f"{who} son 52 haftanın en düşük fiyatının altına indi: yeni dip {px} ({det.split('(')[-1].rstrip(')') if '(' in det else ''})."
            return f"{who} 52 haftalık dip seviyesinde işlem görüyor: {px}."
        if k == "kapanis":
            if v == "tavan":
                return f"{who} günü tavan fiyatından kapattı: kapanış {px}."
            if v == "taban":
                return f"{who} günü taban fiyatından kapattı: kapanış {px}."
            return f"{who} günü {t.split(' ile')[0].replace('Günü ', '')} değişimle kapattı: kapanış {px}."
        if k == "diger":
            return f"{who} için işlem durumu değişti: {det.replace(' → ', ' durumundan ')} durumuna geçildi; fiyat {px}."
    except Exception:
        pass
    return f"{who}: {t}"


event_detector = EventDetector()
