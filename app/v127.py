"""v1.27.0 — FORMASYON motoru: tüm hisseler × 8 periyot (5dk/15dk/30dk/60dk/2s/4s/1G/1H) mum + grafik formasyonları.

* Bar deposu: v127_bars.BarStore (Yahoo geçmiş + bugün İdealData canlı işlem kaydı). Geçmiş günde bir (seans öncesi) yenilenir.
* Arka plan iş parçacığı bar kapanışlarını izler; yalnız yeni bar kapanan periyot(lar) yeniden taranır (olay döngüsü bloklanmaz).
* Tespit daima son KAPANMIŞ bar üzerinde yapılır (oluşmakta olan bar kullanılmaz).
* Bildirimler (formasyon_mum / formasyon_grafik) varsayılan KAPALI; periyot seçimi, eşikler ve hız sınırı ile.
* Dürüstlük testi: günlük mum formasyonlarının son ~1 yıldaki tüm örneklerinde sonraki bar(lar)ın davranışı.
"""
from __future__ import annotations

import json
import logging
import threading
import time


def _LOWR():
    try:
        from app import perf
        return perf.LOW
    except Exception:
        return False
from collections import deque
from datetime import datetime, timedelta

import numpy as np

from app.v127_bars import (BASE, IST, KEEP, S_CLOSE, S_OPEN, TF_LABEL, TF_MIN, TFS, BarStore, Bars, _from_rows, _ts,
                           bars_from_trades, closed_count)
from app import v127_candles as VC
from app import v127_charts as CH

logger = logging.getLogger("v127")
NT_MUM, NT_GRAFIK = "formasyon_mum", "formasyon_grafik"
NT_DEFAULTS = {NT_MUM: "notify", NT_GRAFIK: "notify"}
WATCH_FILE = BASE / "watch.json"
BT_FILE = BASE / "bt.json"
SRC_TXT = {
    "5m": "Yahoo Finance 5 dk OHLCV (≈60 gün; kapanış seansı resmi kapanışla tamamlandı) + bugün İdealData canlı işlemler",
    "1d": "Yahoo Finance günlük OHLCV (≈2 yıl) + bugün İdealData canlı işlemlerden",
    "1w": "Günlük barlardan haftalık (Pzt–Cum, ≈2 yıl)",
}
for _tf in ("15m", "30m", "60m", "2h", "4h"):
    SRC_TXT[_tf] = f"5 dk barlardan BIST seansına hizalı ({'10–12·12–14·14–16·16–18' if _tf == '2h' else '10–14·14–18' if _tf == '4h' else '10:00 tabanlı'}); kaynak: " + SRC_TXT["5m"]
DEF_WATCH = {"mum": {"on": False, "tfs": ["60m", "4h", "1d"], "guven": 3, "yon": "all", "hacim": False},
             "grafik": {"on": False, "tfs": ["60m", "4h", "1d"], "kalite": 70, "yon": "all"}}
RATE_HOUR, RATE_SCAN = 12, 5


def _now():
    return datetime.now(IST)


def _today():
    return _now().strftime("%Y%m%d")


def _prev_wd(day: str) -> str:
    d = datetime.strptime(day, "%Y%m%d") - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.strftime("%Y%m%d")


def _f(x, nd=4):
    return None if x is None else round(float(x), nd)


def bars_np(day, T, P, L, start_sod=0):
    """Vektörel işlem → 5 dk bar (bars_from_trades ile aynı sonuç)."""
    T = np.asarray(T, dtype=np.int64); P = np.asarray(P, dtype=float); L = np.asarray(L, dtype=float)
    m = (T >= start_sod) & (P > 0)
    T, P, L = T[m], P[m], L[m]
    if not len(T):
        return Bars.empty()
    o = np.argsort(T, kind="stable")
    T, P, L = T[o], P[o], L[o]
    K = np.where(T < S_OPEN, S_OPEN, np.where(T >= 64800, 64500, T - T % 300))
    idx = np.r_[0, np.nonzero(np.diff(K))[0] + 1]
    end = np.r_[idx[1:] - 1, len(K) - 1]
    base = _ts(day, 0)
    t = base + K[idx]
    return Bars(t.astype(np.int64), P[idx], np.maximum.reduceat(P, idx), np.minimum.reduceat(P, idx), P[end],
                np.add.reduceat(L, idx), [day] * len(idx))


class Engine:
    def __init__(self):
        self.bs = BarStore()
        self.lock = threading.RLock()
        self.R = {tf: {} for tf in TFS}            # tf → sym → {"c","g","t","p","n"}
        self.LC, self.LG = {tf: [] for tf in TFS}, {tf: [] for tf in TFS}
        self.scan_key = {tf: None for tf in TFS}
        self.scan_info = {tf: {} for tf in TFS}
        self.ready = False
        self.state = "init"
        self.err = None
        self.feed = self.ts = self.hub = None
        self.universe = []
        self.ymap = {}
        self.watch = json.loads(json.dumps(DEF_WATCH))
        self.seen = {"day": None, "k": {}}
        self.rate = deque()
        self.emitted = {NT_MUM: 0, NT_GRAFIK: 0}
        self.bt = None
        self.today_src = {}
        self.ylive_at = 0.0
        self.last_refresh_try = 0.0
        self.clock = _now
        self._load_watch()

    # ------------------------------------------------------------------ ayarlar
    def _load_watch(self):
        try:
            w = json.loads(WATCH_FILE.read_text())
            for k in ("mum", "grafik"):
                self.watch[k].update(w.get(k) or {})
        except Exception:
            pass

    def _save_watch(self):
        try:
            BASE.mkdir(parents=True, exist_ok=True)
            WATCH_FILE.write_text(json.dumps(self.watch, ensure_ascii=False))
        except Exception as ex:   # pragma: no cover
            logger.warning("v127 watch save: %s", ex)

    def watch_get(self):
        return {"watch": self.watch, "nt": {"mum": NT_MUM, "grafik": NT_GRAFIK}, "emitted": self.emitted, "tfs": TFS, "tf_label": TF_LABEL,
                "note": ("Varsayılan KAPALI. Açıkken seçili periyotlarda bar kapanışında taranır: mum formasyonu son kapanan barda oluşunca, "
                         "grafik formasyonu kırılımı tam kapanan barda gerçekleşince bildirir. Hisse+periyot+formasyon başına günde 1, "
                         f"saatte en çok {RATE_HOUR}, tarama başına en çok {RATE_SCAN} bildirim; açtığınız andaki mevcut sinyaller taban kabul edilir.")}

    def watch_set(self, cfg):
        cfg = cfg or {}
        with self.lock:
            for k in ("mum", "grafik"):
                c = cfg.get(k)
                if not isinstance(c, dict):
                    continue
                w = self.watch[k]
                if "on" in c:
                    w["on"] = bool(c["on"])
                if isinstance(c.get("tfs"), list):
                    w["tfs"] = [t for t in c["tfs"] if t in TFS] or w["tfs"]
                if k == "mum":
                    if "guven" in c:
                        try: w["guven"] = max(1, min(3, int(c["guven"])))
                        except Exception: pass
                    if "hacim" in c:
                        w["hacim"] = bool(c["hacim"])
                else:
                    if "kalite" in c:
                        try: w["kalite"] = max(0, min(99, int(c["kalite"])))
                        except Exception: pass
                if c.get("yon") in ("all", "U", "D"):
                    w["yon"] = c["yon"]
            self._baseline()
            self._save_watch()
        return self.watch_get()

    def _baseline(self):
        """Açılış anındaki mevcut sinyaller tekrar bildirilmez."""
        d = _today()
        if self.seen["day"] != d:
            self.seen = {"day": d, "k": {}}
        for tf in TFS:
            for s, r in list(self.R[tf].items()):
                for h in r["c"]:
                    self.seen["k"][f"m|{s}|{tf}|{h['k']}|{h['t']}"] = 1
                for h in r["g"]:
                    if h["durum"] == "KIRILDI":
                        self.seen["k"][f"g|{s}|{tf}|{h['k']}|{h['bo_t']}"] = 1

    # ------------------------------------------------------------------ başlat
    def start(self, feed, trade_store, hub, symbols_fn):
        self.feed, self.ts, self.hub = feed, trade_store, hub
        self.symbols_fn = symbols_fn
        threading.Thread(target=self._run, name="v127", daemon=True).start()

    def _universe(self):
        try:
            syms = self.symbols_fn() or []
        except Exception:
            syms = []
        ymap = {s["symbol"]: (s.get("yahoo") or s["symbol"] + ".IS") for s in syms if s.get("symbol")}
        eq = []
        try:
            eq = list(self.feed.equity_universe() or [])
        except Exception:
            pass
        if not eq:
            try:
                eq = [s for s, q in (self.feed.quotes or {}).items() if q.get("last")]
            except Exception:
                eq = []
        U = sorted({s for s in eq if s in ymap}) or sorted(ymap)
        self.universe = U
        self.ymap = ymap
        return U

    def _need_refresh(self):
        d = _today()
        last = self.bs.meta.get("hist_last_day")
        if not last or not self.bs.hist.get("1d"):
            return True
        if last >= _prev_wd(d):
            return False
        return time.time() - self.last_refresh_try > 6 * 3600

    def _refresh(self):
        self.last_refresh_try = time.time()
        self.state = "yahoo"
        U = self._universe()
        if not U:
            return
        ok, miss = self.bs.refresh_yahoo([(s, self.ymap[s]) for s in U], before_day=_today())
        self.bs.save_disk()
        logger.info("v127: geçmiş yenilendi %d hisse, %d eksik", ok, len(miss))

    # ------------------------------------------------------------------ bugünkü barlar
    def build_today(self):
        ts = self.ts
        d = self.clock().strftime("%Y%m%d")
        if ts is None or getattr(ts, "day", None) != d or datetime.strptime(d, "%Y%m%d").weekday() >= 5:
            return 0
        U = set(self.universe)
        snap = []
        with ts.lock:
            for s, e in ts.syms.items():
                if s in U and len(e.t):
                    snap.append((s, np.frombuffer(e.t, dtype=np.uint32).astype(np.int64), np.frombuffer(e.p, dtype=np.float64).copy(),
                                 np.frombuffer(e.l, dtype=np.int64).astype(np.float64), e.complete_since))
        need_y = []
        for s, T, P, L, cs in snap:
            if cs == 0:
                self.bs.set_today(d, s, bars_np(d, T, P, L), "idealdata")
            else:
                need_y.append((s, T, P, L, cs))
        if need_y and time.time() - self.ylive_at > 600:
            self.ylive_at = time.time()
            try:
                self.bs.yahoo_today([x[0] for x in need_y], d)
            except Exception as ex:   # pragma: no cover
                logger.debug("v127 yahoo today: %s", ex)
        for s, T, P, L, cs in need_y:
            yb = (self.bs.ylive.get(s) or (0, None))[1]
            tb = bars_np(d, T, P, L)
            if yb is None or not len(yb):
                self.bs.set_today(d, s, tb, "idealdata-kısmi")
                continue
            if cs:          # kayıt cs'den beri tam: o 5 dk dilimi dahil öncesi Yahoo'dan
                cut = _ts(d, (S_OPEN if cs < S_OPEN else cs - cs % 300) + 300)
            else:           # kayıt kapsamı bilinmiyor: Yahoo'nun son barına kadar Yahoo, sonrası kayıt
                cut = int(yb.t[-1]) + 300
            ky = yb.t < cut; kt = tb.t >= cut
            yb2 = Bars(yb.t[ky], yb.o[ky], yb.h[ky], yb.l[ky], yb.c[ky], yb.v[ky], [d] * int(ky.sum()))
            tb2 = Bars(tb.t[kt], tb.o[kt], tb.h[kt], tb.l[kt], tb.c[kt], tb.v[kt], [d] * int(kt.sum()))
            self.bs.set_today(d, s, yb2.concat(tb2), "yahoo+idealdata" if len(tb2) else "yahoo")
        return len(snap)

    def roll_day(self):
        """Gün değişince dünkü canlı barları geçmişe ekle (Yahoo yenilemesine kadar kaybolmasın)."""
        bs = self.bs
        with bs.lock:
            tday, today = bs.today_day, dict(bs.today)
        if not tday or not today:
            return
        from app.v127_bars import agg_intraday, agg_daily_from5, agg_weekly
        with bs.lock:
            for s, t5 in today.items():
                h5 = bs.hist["5m"].get(s)
                if h5 is not None and len(h5) and h5.day[-1] >= tday:
                    continue
                for tf in ("5m", "15m", "30m", "60m", "2h", "4h"):
                    add = t5 if tf == "5m" else agg_intraday(t5, TF_MIN[tf])
                    h = bs.hist[tf].get(s)
                    bs.hist[tf][s] = (h.concat(add) if h is not None else add).tail(KEEP[tf])
                hd = bs.hist["1d"].get(s)
                hd = (hd.concat(agg_daily_from5(t5)) if hd is not None else agg_daily_from5(t5))
                bs.hist["1d"][s] = hd.tail(KEEP["1d"])
                bs.hist["1w"][s] = agg_weekly(hd).tail(KEEP["1w"])
            bs.meta["rolled_day"] = tday          # hist_last_day yalnız Yahoo yenilemesinde değişir
            bs.today = {}
            bs.today_day = None

    # ------------------------------------------------------------------ tarama
    def _due_key(self, tf, now):
        """Bugün kapanmış bar sayısı (periyot başına) — değişince o periyot yeniden taranır."""
        d = now.strftime("%Y%m%d")
        if now.weekday() >= 5:
            return ("wk", d[:8] if tf == "1w" else "")
        sod = now.hour * 3600 + now.minute * 60 + now.second - 25     # işlem kaydının oturması için ~25 sn pay
        if tf in ("1d", "1w"):
            return (d, 1 if sod >= S_CLOSE else 0)
        w = TF_MIN[tf] * 60
        cnt, k = 0, 0
        while True:
            e = S_OPEN + (k + 1) * w
            last = e >= 64800
            if last:
                e = S_CLOSE
            if sod < e:
                break
            cnt += 1
            if last:
                break
            k += 1
        return (d, cnt)

    def scan_tf(self, tf):
        t0 = time.time()
        R = {}
        LC, LG = [], []
        nc = ng = 0
        short = 0
        from app import progress as PG
        PG.begin("fm", len(self.universe), f"Formasyonlar · {TF_LABEL.get(tf, tf)} ({TFS.index(tf) + 1 if tf in TFS else 1}/{len(TFS)} periyot)")
        for i, s in enumerate(self.universe):
            PG.step("fm", done=i)
            b = self.bs.get(s, tf)
            n = closed_count(b, tf, self.clock())
            if n < 25:
                short += 1
                continue
            try:
                c = VC.scan(b, n)
            except Exception as ex:   # pragma: no cover
                logger.debug("v127 mum %s %s: %s", s, tf, ex); c = []
            try:
                g = CH.scan(b, n)
            except Exception as ex:   # pragma: no cover
                logger.debug("v127 grafik %s %s: %s", s, tf, ex); g = []
            p = float(b.c[n - 1])
            R[s] = {"c": c, "g": g, "t": int(b.t[n - 1]), "p": p, "n": n}
            for h in c:
                LC.append([s, tf, h["k"], h["yon"], h["tip"], h["guven"], 1 if h["hacim"] else 0, h["hr"], h["skor"], _f(h["teyit"]), _f(h["gecersiz"]),
                           _f(p), h["t"], h["nb"]])
                nc += 1
            for h in g:
                LG.append([s, tf, h["k"], h["yon"], h["durum"], _f(h["giris"]), _f(h["stop"]), _f(h["h1"]), _f(h["h2"]), h["rr"], h["d_giris"], h["d_h1"],
                           1 if h["hacim"] else 0, h["kalite"], h["bo_n"], 1 if h["h1_ok"] else 0, _f(p), h["t"], h["d_stop"]])
                ng += 1
            if i % 40 == 39:
                time.sleep(0.003)     # olay döngüsüne nefes
        with self.lock:
            self.R[tf] = R
            self.LC[tf] = LC
            self.LG[tf] = LG
            PG.end("fm")
            self.scan_info[tf] = {"at": time.time(), "sec": round(time.time() - t0, 2), "syms": len(R), "short": short, "mum": nc, "grafik": ng,
                                  "last_t": max((r["t"] for r in R.values()), default=None)}
        return R

    # ------------------------------------------------------------------ bildirim
    def _notify(self, tf):
        if self.hub is None:
            return
        wm, wg = self.watch["mum"], self.watch["grafik"]
        if not ((wm["on"] and tf in wm["tfs"]) or (wg["on"] and tf in wg["tfs"])):
            return
        d = _today()
        if self.seen["day"] != d:
            self.seen = {"day": d, "k": {}}
        now = time.time()
        while self.rate and now - self.rate[0] > 3600:
            self.rate.popleft()
        cand = []
        for s, r in self.R[tf].items():
            if wm["on"] and tf in wm["tfs"]:
                for h in r["c"]:
                    if h["yon"] == "N" or h["guven"] < wm["guven"] or (wm["yon"] != "all" and h["yon"] != wm["yon"]) or (wm["hacim"] and not h["hacim"]):
                        continue
                    if datetime.fromtimestamp(h["t"], IST).strftime("%Y%m%d") != d and tf not in ("1w",):
                        continue
                    cand.append((h["skor"], "m", s, h))
            if wg["on"] and tf in wg["tfs"]:
                for h in r["g"]:
                    if h["durum"] != "KIRILDI" or h["bo_n"] != 0 or h["kalite"] < wg["kalite"] or (wg["yon"] != "all" and h["yon"] != wg["yon"]):
                        continue
                    cand.append((h["kalite"] + 5, "g", s, h))
        cand.sort(key=lambda x: -x[0])
        n = 0
        for _sc, kind, s, h in cand:
            key = f"{kind}|{s}|{tf}|{h['k']}|{h['t'] if kind == 'm' else h['bo_t']}"
            dkey = f"{kind}|{s}|{tf}|{h['k']}"
            if key in self.seen["k"] or dkey in self.seen["k"]:
                continue
            if n >= RATE_SCAN or len(self.rate) >= RATE_HOUR:
                break
            self.seen["k"][key] = 1; self.seen["k"][dkey] = 1
            n += 1
            self.rate.append(now)
            arrow = "▲" if h["yon"] == "U" else "▼"
            try:
                if kind == "m":
                    title = f"🕯 {arrow} {h['ad']} · {s} · {TF_LABEL[tf]}"
                    txt = (f"{'YÜKSELİŞ' if h['yon'] == 'U' else 'DÜŞÜŞ'} {h['tip']} · güven {VC.REL_TXT[h['guven']]}"
                           + (f" · hacim {h['hr']:.1f}×" if h.get("hr") else "") + f" · teyit {VC.fp(h['teyit'])}, geçersiz {VC.fp(h['gecersiz'])}")
                    self.hub._emit("olay", NT_MUM, s, title, txt, {"f": "formasyon", "tf": tf, "k": h["k"], "kind": "mum", "price": h.get("c")})
                    self.emitted[NT_MUM] += 1
                else:
                    title = f"📐 {arrow} {h['ad']} KIRILIMI · {s} · {TF_LABEL[tf]}"
                    txt = (f"Giriş {VC.fp(h['giris'])} · STOP {VC.fp(h['stop'])} · HEDEF 1 {VC.fp(h['h1'])} · HEDEF 2 {VC.fp(h['h2'])} · R/R {h['rr']:.1f}"
                           + (" · hacim teyitli" if h["hacim"] else "") + f" · kalite {h['kalite']}")
                    self.hub._emit("olay", NT_GRAFIK, s, title, txt, {"f": "formasyon", "tf": tf, "k": h["k"], "kind": "grafik", "price": h.get("c")})
                    self.emitted[NT_GRAFIK] += 1
            except Exception as ex:   # pragma: no cover
                logger.debug("v127 emit: %s", ex)

    # ------------------------------------------------------------------ dürüstlük testi (günlük)
    def backtest(self):
        t0 = time.time()
        last = self.bs.meta.get("hist_last_day")
        try:
            old = json.loads(BT_FILE.read_text())
            if old.get("last") == last and old.get("v") == 2:
                self.bt = old
                return
        except Exception:
            pass
        agg = {}
        nsym = 0
        for si, s in enumerate(self.universe):
            with self.bs.lock:
                b = self.bs.hist["1d"].get(s)
            if b is None or len(b) < 160:
                continue
            nsym += 1
            n = len(b)
            x = VC.Ctx(b, n)
            for idx in range(n - 251, n - 1):
                if idx < 40:
                    continue
                x.i = idx; x.n = idx + 1; x.tick = VC.tick_of(float(b.c[idx]))
                try:
                    hits = VC.detect(x)
                except Exception:
                    continue
                for key, nb, _ck in hits:
                    d = VC.P[key][2]
                    if key in ("dragonfly_doji", "gravestone_doji"):
                        t1 = x.trend(1)[0]
                        if (key == "dragonfly_doji" and t1 >= 0) or (key == "gravestone_doji" and t1 <= 0):
                            d = "N"
                    if d == "N":
                        continue
                    sg = 1 if d == "U" else -1
                    c0 = float(b.c[idx]); c1 = float(b.c[idx + 1])
                    r1 = (c1 / c0 - 1) * 100 * sg
                    r5 = ((float(b.c[idx + 5]) / c0 - 1) * 100 * sg) if idx + 5 < n else None
                    hi = float(np.max(b.h[idx - nb + 1:idx + 1])); lo = float(np.min(b.l[idx - nb + 1:idx + 1]))
                    conf = (c1 > hi) if sg > 0 else (c1 < lo)
                    a = agg.setdefault(key, {"n": 0, "w1": 0, "r1": 0.0, "n5": 0, "w5": 0, "r5": 0.0, "cf": 0})
                    a["n"] += 1; a["w1"] += r1 > 0; a["r1"] += r1; a["cf"] += conf
                    if r5 is not None:
                        a["n5"] += 1; a["w5"] += r5 > 0; a["r5"] += r5
            if si % 10 == 9:
                time.sleep(0.005 if not _LOWR() else 0.03)
        out = {}
        for k, a in agg.items():
            out[k] = {"n": a["n"], "w1": round(a["w1"] / a["n"] * 100, 1), "r1": round(a["r1"] / a["n"], 2), "cf": round(a["cf"] / a["n"] * 100, 1),
                      "w5": round(a["w5"] / a["n5"] * 100, 1) if a["n5"] else None, "r5": round(a["r5"] / a["n5"], 2) if a["n5"] else None}
        self.bt = {"v": 2, "last": last, "syms": nsym, "bars": 250, "at": time.time(), "sec": round(time.time() - t0, 1), "p": out,
                   "note": "Günlük barlarda son ~250 işlem günü, tüm hisseler: formasyon günü kapanışından sonraki 1 ve 5 günün formasyon yönündeki getirisi (yön isabeti %, ortalama %) ve ertesi gün teyit oranı."}
        try:
            BT_FILE.write_text(json.dumps(self.bt, ensure_ascii=False))
        except Exception:   # pragma: no cover
            pass
        logger.info("v127: dürüstlük testi %d hisse %.0f sn", nsym, time.time() - t0)

    # ------------------------------------------------------------------ döngü
    def _run(self):
        try:
            self.state = "disk"
            self.bs.load_disk()
            time.sleep(20 if not _LOWR() else 120)            # v1.38.1 low_resource: daha geç · açılışta diğer motorlar önce
            self._universe()
            if self._need_refresh():
                self._refresh()
            self.state = "scan"
            day0 = _today()
            self.build_today()
            for tf in TFS:
                self.scan_tf(tf)
                self.scan_key[tf] = self._due_key(tf, _now())
            self.ready = True
            self.state = "ok"
            logger.info("v127: ilk tarama tamam (%s)", ", ".join(f"{tf}:{self.scan_info[tf].get('sec')}s" for tf in TFS))
            try:
                self.backtest()
            except Exception as ex:   # pragma: no cover
                logger.warning("v127 backtest: %s", ex)
        except Exception as ex:   # pragma: no cover
            self.err = str(ex)[:200]; self.state = "error"
            logger.exception("v127 init")
            day0 = _today()
        while True:
            try:
                time.sleep(15)
                d = _today()
                if d != day0:
                    self.roll_day(); day0 = d
                    self._universe()
                n = _now()
                if n.weekday() < 5 and 8 * 3600 + 40 * 60 <= n.hour * 3600 + n.minute * 60 < 9 * 3600 + 55 * 60 and self._need_refresh():
                    self._refresh()
                    self.build_today()
                    for tf in TFS:
                        self.scan_tf(tf); self.scan_key[tf] = self._due_key(tf, _now())
                    self.state = "ok"
                    try:
                        self.backtest()
                    except Exception:
                        pass
                    continue
                due = [tf for tf in TFS if self._due_key(tf, n) != self.scan_key[tf]]
                if not due:
                    continue
                self.build_today()
                for tf in due:
                    self.scan_tf(tf)
                    self.scan_key[tf] = self._due_key(tf, _now())
                    self._notify(tf)
            except Exception as ex:   # pragma: no cover
                self.err = str(ex)[:200]
                logger.warning("v127 loop: %s", ex)
                time.sleep(30 if not _LOWR() else 90)

    # ------------------------------------------------------------------ API
    def meta(self):
        bs = self.bs
        with bs.lock:
            m = dict(bs.meta)
            nt = len(bs.today)
            srcs = {}
            for s, v in bs.src.items():
                t = v.get("today")
                if t:
                    srcs[t] = srcs.get(t, 0) + 1
        return {"ready": self.ready, "state": self.state, "err": self.err, "universe": len(self.universe), "yahoo_ok": m.get("yahoo_ok"),
                "missing": m.get("yahoo_missing") or [], "hist_last_day": m.get("hist_last_day"), "today_day": bs.today_day, "today_syms": nt,
                "today_src": srcs, "src": SRC_TXT, "tf_label": TF_LABEL, "scan": self.scan_info,
                "closed_note": "Formasyonlar her periyotta son KAPANMIŞ bara göre hesaplanır (oluşmakta olan bar dahil edilmez). Günün son barı kapanış seansıyla 18:10'da kapanır."}

    def pat_meta(self):
        return {"mum": {k: [v[0], v[1], v[2], v[3], v[4], v[5]] for k, v in VC.P.items()},
                "grafik": {k: [v[0], v[1], v[2], v[3]] for k, v in CH.CP.items()}}

    def listing(self, kind, tfs=None):
        tfs = [t for t in (tfs or TFS) if t in TFS]
        with self.lock:
            rows = []
            for tf in tfs:
                rows.extend(self.LC[tf] if kind == "mum" else self.LG[tf])
        cols = (["s", "tf", "k", "yon", "tip", "guven", "hacim", "hr", "skor", "teyit", "gecersiz", "p", "t", "nb"] if kind == "mum" else
                ["s", "tf", "k", "yon", "durum", "giris", "stop", "h1", "h2", "rr", "d_giris", "d_h1", "hacim", "kalite", "bo_n", "h1_ok", "p", "t", "d_stop"])
        bt = (self.bt or {}).get("p") if kind == "mum" else None
        return {"ok": True, "kind": kind, "cols": cols, "rows": rows, "meta": self.meta(), "pat": self.pat_meta()["mum" if kind == "mum" else "grafik"],
                "bt": bt, "bt_note": (self.bt or {}).get("note") if kind == "mum" else None}

    def hisse(self, sym):
        sym = sym.upper()
        out = {}
        with self.lock:
            for tf in TFS:
                r = self.R[tf].get(sym)
                if r is None:
                    out[tf] = None
                    continue
                out[tf] = {"c": r["c"], "g": [{k: v for k, v in h.items() if k not in ("kontrol",)} for h in r["g"]], "t": r["t"], "p": r["p"], "n": r["n"]}
        best = self.best_chart(sym, out)
        return {"ok": True, "sym": sym, "tfs": out, "best": best, "ready": self.ready, "tf_label": TF_LABEL, "src": SRC_TXT,
                "yorum": self.yorum(sym, out, best), "bt": (self.bt or {}).get("p"), "closed_note": self.meta()["closed_note"]}

    @staticmethod
    def best_chart(sym, out):
        cands = []
        w = {"5m": 0, "15m": 1, "30m": 2, "60m": 3, "2h": 4, "4h": 5, "1d": 6, "1w": 5}
        for tf, r in out.items():
            if not r:
                continue
            for h in r["g"]:
                if h["durum"] == "BAŞARISIZ" or h["h1_ok"]:
                    continue
                sc = h["kalite"] + (8 if h["durum"] == "KIRILDI" else 0) + w[tf] * 4
                cands.append((sc, tf, h))
        if not cands:
            return None
        cands.sort(key=lambda x: -x[0])
        sc, tf, h = cands[0]
        return {"tf": tf, "k": h["k"], "ad": h["ad"], "yon": h["yon"], "durum": h["durum"], "giris": h["giris"], "stop": h["stop"], "h1": h["h1"],
                "h2": h["h2"], "rr": h["rr"], "kalite": h["kalite"], "d_h1": h["d_h1"], "d_giris": h["d_giris"]}

    @staticmethod
    def yorum(sym, out, best):
        parts = []
        if best:
            yn = "yükseliş" if best["yon"] == "U" else "düşüş" if best["yon"] == "D" else "yön bekleyen"
            if best["durum"] == "KIRILDI":
                parts.append(f"{TF_LABEL[best['tf']]} grafikte {best['ad']} kırıldı ({yn}; hedef {VC.fp(best['h1'])}, stop {VC.fp(best['stop'])})")
            else:
                parts.append(f"{TF_LABEL[best['tf']]} grafikte {best['ad']} oluşuyor ({yn}; kırılım {VC.fp(best['giris'])})")
        cm = []
        for tf in ("1d", "4h", "60m", "1w"):
            r = out.get(tf)
            if not r:
                continue
            for h in r["c"]:
                if h["yon"] != "N" and h["guven"] >= 2:
                    cm.append((h["guven"], tf, h))
        if cm:
            cm.sort(key=lambda x: -x[0])
            _g, tf, h = cm[0]
            parts.append(f"{TF_LABEL[tf]} mumda {h['ad']} ({'yükseliş' if h['yon'] == 'U' else 'düşüş'})")
        return ("Formasyonlar: " + " · ".join(parts) + ".") if parts else ""

    def chip(self, sym):
        if not self.ready:
            return None
        h = self.hisse(sym)
        b = h.get("best")
        if not b:
            return None
        ar = "▲" if b["yon"] == "U" else "▼" if b["yon"] == "D" else "◆"
        return {"chip": {"id": "formasyon", "g": "fm " + ("up" if b["yon"] == "U" else "dn" if b["yon"] == "D" else ""), "strong": b["durum"] == "KIRILDI" and b["kalite"] >= 70,
                         "l": f"📐 {ar} {b['ad']} ({TF_LABEL[b['tf']]})", "txt": ("KIRILDI" if b["durum"] == "KIRILDI" else "oluşuyor")}, "yorum": h["yorum"]}

    def kanit(self, sym, tf, kind, key):
        sym = sym.upper()
        if tf not in TFS:
            return {"ok": False, "error": "periyot"}
        with self.lock:
            r = self.R[tf].get(sym)
        if not r:
            return {"ok": False, "error": "veri yok"}
        hs = r["c"] if kind == "mum" else r["g"]
        h = next((x for x in hs if x["k"] == key), None)
        if h is None:
            return {"ok": False, "error": "formasyon artık yok (yeni bar kapandı)"}
        b = self.bs.get(sym, tf)
        n = r["n"]
        if kind == "mum":
            st = max(0, n - 40)
        else:
            t0 = h.get("t0") or int(b.t[max(0, n - 80)])
            i0 = int(np.searchsorted(b.t[:n], t0))
            st = max(0, min(i0 - 8, n - 40))
        en = n
        bars = {"t": [int(x) for x in b.t[st:en]], "o": [_f(x) for x in b.o[st:en]], "h": [_f(x) for x in b.h[st:en]], "l": [_f(x) for x in b.l[st:en]],
                "c": [_f(x) for x in b.c[st:en]], "v": [float(x) for x in b.v[st:en]]}
        with self.bs.lock:
            src = (self.bs.src.get(sym) or {}).get("today")
        return {"ok": True, "sym": sym, "tf": tf, "tfl": TF_LABEL[tf], "kind": kind, "hit": h, "bars": bars, "src": SRC_TXT[tf], "today_src": src,
                "bt": ((self.bt or {}).get("p") or {}).get(key) if kind == "mum" else None, "closed_note": self.meta()["closed_note"]}

    def status(self):
        m = self.meta()
        m["bt"] = {k: v for k, v in (self.bt or {}).items() if k != "p"} if self.bt else None
        m["watch"] = self.watch
        m["emitted"] = self.emitted
        return m


v127 = Engine()
