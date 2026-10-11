"""v1.36.0 ORDER BLOCK TARAMASI — tüm hisseler, çok periyotlu OB destek/direnç + kesişim (ÇOK GÜÇLÜ) + bölge istatistiği.

* OB tespiti: v1.28.0 motoru (app.v128_ob.detect) — v1.27 bar deposundaki KAPANMIŞ barlar (5dk/15dk/60dk/Günlük...).
  Yükseliş OB = DESTEK, düşüş OB = DİRENÇ. Kırılmış (kapanışla geçilmiş) bölgeler listeye alınmaz.
* Kesişim: aynı yönlü bölgeler farklı periyotlarda fiyat olarak örtüşüyorsa küme olur; kesişim aralığı bölge olur.
  Periyot sayısı ≥ conf_cok (varsayılan 3) → ÇOK GÜÇLÜ, ≥2 → GÜÇLÜ, 1 → NORMAL.
* Bölge istatistiği (5 dk barlarla, bölgenin oluştuğu andan sonra): UĞRADI = dışarıdan bölgeye giriş;
  TEPKİ = girişten sonra en çok react_bars bar içinde fiyat bölge kenarından ≥ react_pct % uzaklaştı (destekte yukarı,
  dirençte aşağı) ve bu arada kapanışla bölge kırılmadı; KIRILDI = kapanış bölgenin karşı ucunun ötesinde (sonra geri
  dönüş olabilir, sayılır); TUTTU = tepki verdiği ziyaret sayısı. Son test = son giriş zamanı.
* Derinlik: canlı derinlik varsa ondan, yoksa data/depth altındaki SON kayıtlı defter (zaman damgasıyla) — bölge ±near_pct
  içindeki alış (destek) / satış (direnç) lotu, kademe ortalamasına oranı.
* Kademe: bölge fiyat aralığında gerçekleşen işlemler (bugün canlı yoksa son kayıtlı işlem günü): lot, TL, aktif alış/
  satış payı, en çok alan / satan kurum.
* BÖLGE GÜCÜ (0–100) = kesişim 30 + tepki 25 + tutma oranı 15 + OB skoru 15 + derinlik 10 + kademe hacmi 5 (döküm döner).
Eşikler data/v136/ob.json'dan okunur. Yalnız mevcut veriyle çalışır; canlı akış dönünce otomatik canlı veriyi kullanır.
"""
from __future__ import annotations

import gzip
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


def _MUL():
    from app import perf
    return float(perf.CFG.get("interval_mul", 3))
from datetime import datetime
from pathlib import Path

import numpy as np
from fastapi import APIRouter, Query, Request

from app import v128_ob
from app.v127_bars import IST, TF_LABEL as _TFL, Bars, _ts, closed_count

TF_LABEL = dict(_TFL); TF_LABEL["1m"] = "1 dk"
TB_SEC = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "60m": 3600, "2h": 7200, "4h": 14400}
TF_LABEL["60m"] = "1 saat"; TF_LABEL["1d"] = "1 Gün"; TF_LABEL["1w"] = "1 Hafta"; TF_LABEL["gunici"] = "GÜN İÇİ"
GI_TFS = ["1m", "5m", "15m"]

logger = logging.getLogger("bist.v136")
ROOT = Path(__file__).resolve().parent.parent
CFG_F = ROOT / "data" / "v136" / "ob.json"
DEF = {"tfs": ["1m", "5m", "15m", "30m", "60m", "2h", "4h", "1d", "1w"], "react_pct": 0.8, "react_bars": 12, "exit_buf_pct": 0.2, "min_ticks": 2, "ortak_tol_pct": 0.3, "ortak_tol_ticks": 2, "ortak_min": 2, "ortak_max_per_side": 3, "conf_cok": 3, "near_pct": 0.5,
       "interval_live_sec": 300, "interval_idle_sec": 1800, "max_zones_per_side": 4, "min_bars": 40}
router = APIRouter()


def cfg():
    c = dict(DEF)
    try:
        c.update(json.loads(CFG_F.read_text()))
    except Exception:
        CFG_F.parent.mkdir(parents=True, exist_ok=True)
        CFG_F.write_text(json.dumps(DEF, indent=2, ensure_ascii=False))
    return c


def _fmt_t(ts):
    try:
        return datetime.fromtimestamp(int(ts), IST).strftime("%d.%m %H:%M")
    except Exception:
        return None


def _stats(lo, hi, yon, b, t_from, C):
    """v1.36.1 bölge istatistiği — periyodun KENDİ barlarıyla, OB itkisi tamamlandıktan SONRAKİ barlarda.
    UĞRAMA: fiyat bölge dışındayken (en az exit_buf_pct % uzakta) bölgeye [lo,hi] girer → 1 ziyaret; bölgede kalınan
      ardışık barlar aynı ziyarettir; ziyaret, fiyat bölgeden exit_buf_pct % uzaklaşınca biter.
    TEPKİ: ziyaret başlangıcından itibaren react_bars bar içinde, uzak kenar kapanışla geçilmeden, fiyat yakın kenardan
      react_pct % beklenen yöne gider (destek: yukarı hi×(1+r), direnç: aşağı lo×(1−r)).
    KIRILDI: ziyaret sırasında KAPANIŞ uzak kenarın ötesinde (destek: c < lo, direnç: c > hi). TUTTU: kırılmadan biten ziyaret.
    Süren (henüz bitmemiş) ziyaret de sayılır, "aktif" işaretlenir."""
    side = 1 if yon == "U" else -1
    i0 = int(np.searchsorted(b.t, t_from, side="right"))
    t, h, l, c = b.t[i0:], b.h[i0:], b.l[i0:], b.c[i0:]
    n = len(c)
    tk = _tick(hi)
    buf = max(C.get("exit_buf_pct", 0.2) / 100.0, C.get("min_ticks", 2) * tk / hi)     # en az 2 fiyat adımı
    rp = max(C["react_pct"] / 100.0, C.get("min_ticks", 2) * tk / hi)
    N = int(C["react_bars"])
    out = {"ugradi": 0, "tepki": 0, "tuttu": 0, "kirildi": 0, "son_test": None, "aktif": False, "epizot": []}
    if not n:
        out.update({"pencere": None, "bar": 0, "seans": 0}); return out
    def far(k):   # bölgeden tampon kadar uzakta mı (iki yönden biri)
        return l[k] > hi * (1 + buf) or h[k] < lo * (1 - buf)
    armed = far(0)
    ep = None
    for k in range(n):
        inside = l[k] <= hi and h[k] >= lo
        if ep is None:
            if not armed:
                armed = far(k)
                continue
            if inside:
                ep = {"k0": k, "t": int(t[k]), "react": False, "broke": False}
                out["ugradi"] += 1; out["son_test"] = int(t[k])
            else:
                continue
        # ziyaret içinde
        if not ep["broke"] and ((side == 1 and c[k] < lo) or (side == -1 and c[k] > hi)):
            ep["broke"] = True
        if not ep["broke"] and not ep["react"] and k - ep["k0"] <= N:
            if (side == 1 and h[k] >= hi * (1 + rp)) or (side == -1 and l[k] <= lo * (1 - rp)):
                ep["react"] = True
        if far(k):
            out["kirildi" if ep["broke"] else "tuttu"] += 1
            out["tepki"] += 1 if ep["react"] else 0
            out["epizot"].append({"t": _fmt_t(ep["t"]), "tepki": ep["react"], "kirildi": ep["broke"]})
            ep = None; armed = True
    if ep is not None:
        out["kirildi" if ep["broke"] else "tuttu"] += 1
        out["tepki"] += 1 if ep["react"] else 0
        out["aktif"] = True
        out["epizot"].append({"t": _fmt_t(ep["t"]), "tepki": ep["react"], "kirildi": ep["broke"], "aktif": True})
    out["epizot"] = out["epizot"][-12:]
    if out["son_test"] is not None:
        j = int(np.searchsorted(t, out["son_test"]))
        out["test_seans_once"] = len(set(b.day[i0 + j:])) - 1
    else:
        out["test_seans_once"] = None
    nd = len(set(b.day[i0:])) if n else 0
    out.update({"pencere": f"{_fmt_t(t[0])} → {_fmt_t(t[-1])}", "bar": int(n), "seans": int(nd), "t_from": int(t_from)})
    return out


def _tick(p):
    """BIST pay fiyat adımı."""
    for lim, t in ((20, 0.01), (50, 0.02), (100, 0.05), (250, 0.1), (500, 0.25), (1000, 0.5), (2500, 1.0)):
        if p < lim:
            return t
    return 2.5


def _slice_day(b, day):
    idx = [i for i, d in enumerate(b.day) if d == day]
    if not idx:
        return None
    i0, i1 = idx[0], idx[-1] + 1
    return Bars(b.t[i0:i1], b.o[i0:i1], b.h[i0:i1], b.l[i0:i1], b.c[i0:i1], b.v[i0:i1], list(b.day[i0:i1]))


class Engine:
    def __init__(self):
        self.lock = threading.Lock()
        self.rows = []          # bölge listesi (tüm hisseler)
        self.by_sym = {}
        self.meta = {"ready": False, "state": "bekliyor", "ts": None, "sec": None, "n_sym": 0, "src": None}
        self.depth_cache = {}   # sym → (ts_label, bids, asks, src)
        self.trade_cache = {"day": None, "data": {}}
        self.feed = None
        self.v127 = None
        self.ts = None

    def start(self, feed, v127_engine, trade_store):
        self.feed, self.v127, self.ts = feed, v127_engine, trade_store
        threading.Thread(target=self._loop, name="v136-ob", daemon=True).start()

    # ------------------------------------------------------------- veri kaynakları
    def _live(self):
        try:
            return bool(self.feed and self.feed.healthy())
        except Exception:
            return False

    def _depth(self, sym):
        if self._live():
            try:
                d = self.feed._depth_view(sym)
                if d:
                    bids = [(x.get("price"), x.get("lot")) for x in (d.get("bids") or []) if x.get("price")]
                    asks = [(x.get("price"), x.get("lot")) for x in (d.get("asks") or []) if x.get("price")]
                    if bids or asks:
                        return {"src": "canlı", "ts": time.strftime("%d.%m %H:%M:%S"), "b": bids, "a": asks}
            except Exception:
                pass
        if sym in self.depth_cache:
            return self.depth_cache[sym]
        out = None
        dd = ROOT / "data" / "depth"
        for day in sorted([p.name for p in dd.iterdir() if p.is_dir()], reverse=True)[:5] if dd.exists() else []:
            f = dd / day / f"{sym}.jsonl.gz"
            f2 = dd / day / f"{sym}.jsonl"
            fp = f if f.exists() else f2 if f2.exists() else None
            if not fp:
                continue
            try:
                op = gzip.open if fp.suffix == ".gz" else open
                B, A, tl = {}, {}, None
                with op(fp, "rt") as fh:
                    for ln in fh:
                        o = json.loads(ln)
                        if o.get("k"):
                            B = {x[0]: x[1] for x in o.get("b", [])}; A = {x[0]: x[1] for x in o.get("a", [])}
                        else:
                            for x in o.get("b", []):
                                (B.__setitem__(x[0], x[1]) if x[1] > 0 else B.pop(x[0], None))
                            for x in o.get("a", []):
                                (A.__setitem__(x[0], x[1]) if x[1] > 0 else A.pop(x[0], None))
                        tl = o.get("t")
                s = int(tl or 0)
                out = {"src": "son kayıt", "ts": f"{day[6:8]}.{day[4:6]} {s // 3600:02d}:{s // 60 % 60:02d}",
                       "b": sorted(B.items(), reverse=True), "a": sorted(A.items())}
            except Exception:
                out = None
            break
        self.depth_cache[sym] = out
        return out

    def _trades(self, sym):
        """(gün, T, P, L, SD, B, S, brokers) — bugün canlı veri varsa trade_store, yoksa son kayıtlı gün CSV."""
        try:
            e = self.ts.syms.get(sym)
            if e is not None and len(e.t) > 50:
                return self.ts.day, np.array(e.p), np.array(e.l, dtype=float), np.frombuffer(bytes(e.sd), dtype=np.uint8), np.array(e.b), np.array(e.s), self.ts.brokers, "bugün"
        except Exception:
            pass
        td = ROOT / "data" / "trades"
        days = sorted([p.name for p in td.iterdir() if p.is_dir() and any(p.glob("*.csv"))], reverse=True) if td.exists() else []
        if not days:
            return None
        day = days[0]
        if self.trade_cache["day"] != day:
            names = [""]
            try:
                nm = (td / day / "_brokers.txt").read_text(encoding="utf-8").split("\n")
                names = [""] + [x for x in (nm[1:] if nm and nm[0] == "" else nm)]
            except Exception:
                pass
            self.trade_cache = {"day": day, "data": {}, "brokers": names}
        dc = self.trade_cache["data"]
        if sym not in dc:
            f = td / day / f"{sym}.csv"
            try:
                a = np.loadtxt(f, delimiter=",", ndmin=2) if f.exists() and f.stat().st_size else None
            except Exception:
                a = None
            dc[sym] = a
        a = dc[sym]
        if a is None or not len(a):
            return None
        return day, a[:, 1], a[:, 2], a[:, 3].astype(np.uint8), a[:, 4].astype(int), a[:, 5].astype(int), self.trade_cache["brokers"], "son kayıtlı gün"

    # ------------------------------------------------------------- işlem kaydından bar (Yahoo geçmişi yoksa)
    def _days(self):
        td = ROOT / "data" / "trades"
        return sorted([p.name for p in td.iterdir() if p.is_dir() and any(p.glob("*.csv"))])[-5:] if td.exists() else []

    _TBC: dict = {}   # v1.37.0: (sym, gün, boyut, mtime) → {tf: dizi demeti}; geçmiş gün dosyaları değişmez

    @staticmethod
    def _agg(d, t, p, l):
        """Bir günün işlemleri → tf başına (T,O,H,L,C,V) — tamamen vektörel (eski: bar başına Python döngüsü)."""
        m = p > 0
        t, p, l = t[m], p[m], l[m]
        out = {}
        if not len(t):
            return out
        o = np.argsort(t, kind="stable"); t, p, l = t[o], p[o], l[o]
        base = _ts(d, 0)
        for tf, w in TB_SEC.items():
            k = (t // w).astype(np.int64)
            st = np.concatenate([[0], np.nonzero(np.diff(k))[0] + 1])
            en = np.concatenate([st[1:], [len(k)]])
            out[tf] = (base + k[st] * w, p[st], np.maximum.reduceat(p, st), np.minimum.reduceat(p, st), p[en - 1],
                       np.add.reduceat(l, st))
        return out

    def _tbars(self, sym, days):
        import pandas as pd
        parts = []
        for d in days:
            f = ROOT / "data" / "trades" / d / f"{sym}.csv"
            try:
                stt = f.stat()
            except OSError:
                continue
            if not stt.st_size:
                continue
            key = (sym, d, stt.st_size, int(stt.st_mtime))
            g = self._TBC.get(key)
            if g is None:
                try:
                    a = pd.read_csv(f, header=None, usecols=[0, 1, 2], dtype=float).to_numpy()
                    g = self._agg(d, a[:, 0], a[:, 1], a[:, 2])
                except Exception:
                    g = {}
                if len(self._TBC) > 6000:      # sınırlı önbellek (≈ 600 hisse × 5 gün + pay)
                    self._TBC.pop(next(iter(self._TBC)))
                self._TBC[key] = g
            parts.append((d, g))
        try:
            e = self.ts.syms.get(sym)
            if e is not None and len(e.t) and self.ts.day not in days:
                parts.append((self.ts.day, self._agg(self.ts.day, np.array(e.t, dtype=float), np.array(e.p), np.array(e.l, dtype=float))))
        except Exception:
            pass
        out = {}
        for tf in TB_SEC:
            ps = [(d, g[tf]) for d, g in parts if tf in g]
            if not ps:
                continue
            T, O, H, L_, C_, V = (np.concatenate([x[i] for _, x in ps]) for i in range(6))
            D = [d for d, x in ps for _ in range(len(x[0]))]
            out[tf] = Bars(T.astype(np.int64), O, H, L_, C_, V, D)
        return out

    def _series(self, sym, tf, tb, C):
        try:
            b = self.v127.bs.get(sym, tf) if tf != "1m" else None
        except Exception:
            b = None
        y = b if b is not None and len(b) >= C["min_bars"] else None
        t = tb.get(tf)
        t = t if t is not None and len(t) >= C["min_bars"] else None
        if y is not None and (t is None or len(y) >= len(t)):
            return y, closed_count(y, tf), "yahoo+canlı"
        if t is not None:
            return t, len(t) - (1 if self._live() else 0), "işlem kaydı"
        return None, 0, None

    # ------------------------------------------------------------- tarama
    def _scan_sym(self, sym, C, days=None):
        bs = self.v127.bs
        tb = self._tbars(sym, days if days is not None else self._days())
        b5 = tb.get("1m") if tb.get("1m") is not None and len(tb["1m"]) >= C["min_bars"] else bs.get(sym, "5m")
        if b5 is None or len(b5) < 10:
            return []
        price = None
        try:
            q = self.feed.live_quote(sym) if self._live() else None
            price = (q or {}).get("price")
        except Exception:
            pass
        price = float(price or b5.c[-1])
        tr = self._trades(sym)
        dp = self._depth(sym)
        res = []
        # ---- normal: tüm periyotlar
        S = {}
        zs = []
        for tf in C["tfs"]:
            b, n, srcb = self._series(sym, tf, tb, C)
            if b is None or n < 30:
                continue
            S[tf] = b
            zs += self._detect(b, n, tf, price, None)
        res += self._clusters(sym, zs, S, C["tfs"], price, C, tr, dp, "normal", None)
        # ---- v1.36.2 ORTAK EN GÜÇLÜ: tüm periyotların kesiştiği fiyat seviyeleri (tarama çizgisi + tolerans)
        res += self._clusters(sym, zs, S, C["tfs"], price, C, tr, dp, "ortak", None, groups=self._ortak(zs, C))
        # ---- GÜN İÇİ: son seans aralığı
        fin = None
        for tf in GI_TFS:
            b, n, srcb = self._series(sym, tf, tb, dict(C, min_bars=10))
            if b is not None and len(b):
                fin = b; break
        if fin is not None:
            day = fin.day[-1]
            GS, gz = {}, []
            for tf in GI_TFS:
                b, n, srcb = self._series(sym, tf, tb, dict(C, min_bars=10))
                if b is None:
                    continue
                bd = _slice_day(b, day)
                if bd is None or len(bd) < 30:
                    continue
                GS[tf] = bd
            if GS:
                f0 = GS[[x for x in GI_TFS if x in GS][0]]
                slo, shi = float(f0.l.min()), float(f0.h.max())
                sess = {"gun": f"{day[6:8]}.{day[4:6]}.{day[:4]}", "lo": round(slo, 4), "hi": round(shi, 4)}
                for tf, bd in GS.items():
                    nn = len(bd) - (1 if (self._live() and day == datetime.now(IST).strftime("%Y%m%d")) else 0)
                    gz += self._detect(bd, nn, tf, price, (slo, shi))
                res += self._clusters(sym, gz, GS, GI_TFS, price, C, tr, dp, "gunici", sess)
        mx = int(C["max_zones_per_side"])
        fin_ = []
        for mod in ("normal", "gunici", "ortak"):
            rr, seen = [], set()
            for r in sorted([r for r in res if r["mod"] == mod], key=lambda r: -r["guc"]):
                key = (r["yon"], r["lo"], r["hi"])
                if key in seen:
                    continue
                seen.add(key); rr.append(r)
            mm = mx if mod != "ortak" else int(C["ortak_max_per_side"])
            if mod == "ortak":
                rr.sort(key=lambda r: (-r["ortak_n"], -r["guc"]))
            fin_ += [r for r in rr if r["yon"] == "U"][:mm] + [r for r in rr if r["yon"] == "D"][:mm]
        return fin_

    def _detect(self, b, n, tf, price, rng):
        out = []
        r = v128_ob.detect(b.o, b.h, b.l, b.c, b.v, b.t, n)
        for z in r.get("zones", []):
            if z["durum"] == "KIRILDI":
                continue
            if z["yon"] == "U" and z["bot"] > price * 1.002:
                continue
            if z["yon"] == "D" and z["top"] < price * 0.998:
                continue
            z = dict(z); z["tf"] = tf
            if rng:
                lo, hi = max(z["bot"], rng[0]), min(z["top"], rng[1])
                if hi <= lo:
                    continue
                z["bot"], z["top"] = lo, hi
            out.append(z)
        return out

    def _ortak(self, zs, C):
        """Her yön için: bölgeler (±tolerans) fiyat ekseninde taranır; en çok FARKLI periyodun örtüştüğü aralıklar.
        v1.36.1 kümelemesi açgözlüydü (en yüksek skorlu bölge etrafında, kesişim daraldıkça diğerleri dışarıda kalıyordu,
        tolerans yoktu, yön başına 4 bölge güce göre kesiliyordu) → çok periyotlu seviyeler kayboluyordu."""
        out = []
        for yon in ("U", "D"):
            side = [z for z in zs if z["yon"] == yon]
            if not side:
                continue
            ev = []
            for z in side:
                tol = max(C["ortak_tol_pct"] / 100 * z["top"], C["ortak_tol_ticks"] * _tick(z["top"]))
                ev.append((z["bot"] - tol, z["top"] + tol, z))
            xs = sorted({e[0] for e in ev} | {e[1] for e in ev})
            segs = []
            for a, b in zip(xs, xs[1:]):
                m = (a + b) / 2
                cov = [e for e in ev if e[0] <= m <= e[1]]
                tfs = {e[2]["tf"] for e in cov}
                if len(tfs) >= C["ortak_min"]:
                    segs.append([a, b, tfs, cov])
            # aynı periyot kümesine sahip bitişik parçaları birleştir
            mg = []
            for sg in segs:
                if mg and abs(mg[-1][1] - sg[0]) < 1e-9 and mg[-1][2] == sg[2]:
                    mg[-1][1] = sg[1]; mg[-1][3] = list({id(e): e for e in mg[-1][3] + sg[3]}.values())
                else:
                    mg.append(sg)
            mg.sort(key=lambda g: (-len(g[2]), g[1] - g[0]))
            kept = []
            for a, b, tfs, cov in mg:
                if any(not (b <= k[0] or a >= k[1]) for k in kept):
                    continue
                kept.append((a, b, tfs, cov))
                if len(kept) >= C["ortak_max_per_side"]:
                    break
            for a, b, tfs, cov in kept:
                # gerçek (toleranssız) kesişim; toleransla birleşen dar bölgelerde tolerans aralığı kullanılır
                lo = max(e[2]["bot"] for e in cov); hi = min(e[2]["top"] for e in cov)
                if hi <= lo:
                    lo, hi = max(a, min(e[2]["bot"] for e in cov)), min(b, max(e[2]["top"] for e in cov))
                tk = _tick(hi)
                lo = round(np.floor(lo / tk + 1e-9) * tk, 4); hi = round(np.ceil(hi / tk - 1e-9) * tk, 4)
                if hi <= lo:
                    hi = round(lo + tk, 4)
                best = {}
                for e in cov:
                    z = e[2]
                    if z["tf"] not in best or z["skor"] > best[z["tf"]]["skor"]:
                        best[z["tf"]] = z
                out.append({"yon": yon, "lo": lo, "hi": hi, "tfs": None, "members": list(best.values())})
        return out

    def _clusters(self, sym, zs, S, order, price, C, tr, dp, mod, sess, groups=None):
        out = []
        for g in (groups or []):
            g["tfs"] = sorted({m["tf"] for m in g["members"]}, key=lambda x: order.index(x))
            out.append(g)
        for yon in (("U", "D") if groups is None else ()):
            side = sorted([z for z in zs if z["yon"] == yon], key=lambda z: -z["skor"])
            used = [False] * len(side)
            for i, z in enumerate(side):
                if used[i]:
                    continue
                grp = [z]; used[i] = True
                lo, hi = z["bot"], z["top"]
                for j in range(i + 1, len(side)):
                    w = side[j]
                    if used[j]:
                        continue
                    nlo, nhi = max(lo, w["bot"]), min(hi, w["top"])
                    if nhi > nlo:
                        grp.append(w); used[j] = True
                        if w["tf"] not in {g["tf"] for g in grp[:-1]}:
                            lo, hi = nlo, nhi
                tfs = sorted({g["tf"] for g in grp}, key=lambda x: order.index(x))
                out.append({"yon": yon, "lo": lo, "hi": hi, "tfs": tfs, "members": grp})
        res = []
        for k in out:
            yon, lo, hi = k["yon"], k["lo"], k["hi"]
            fine = k["tfs"][0]                        # en ince periyot: kesişim bölgesi bir kez, bu barlarla sayılır
            fm = [g for g in k["members"] if g["tf"] == fine]
            t_from = min(g["te"] for g in fm)
            stt = _stats(lo, hi, yon, S[fine], t_from, C)
            stt["say_tf"] = fine
            ntf = len(k["tfs"])
            lvl = "ÇOK GÜÇLÜ" if ntf >= C["conf_cok"] else "GÜÇLÜ" if ntf >= 2 else "NORMAL"
            dep = None
            if dp:
                near = C["near_pct"] / 100.0
                book = dp["b"] if yon == "U" else dp["a"]
                lots = [l for p, l in book if lo * (1 - near) <= p <= hi * (1 + near)]
                allv = [l for p, l in book] or [0]
                avg = float(np.mean(allv)) if allv else 0
                dep = {"lot": float(sum(lots)), "kademe": len(lots), "oran": round(sum(lots) / avg / max(1, len(lots)), 2) if avg and lots else 0,
                       "src": dp["src"], "ts": dp["ts"]}
            kad = None
            if tr:
                day, P, L, SD, B, Sx, names, tsrc = tr
                m = (P >= lo) & (P <= hi)
                if m.any():
                    lot = float(L[m].sum()); tl = float((P[m] * L[m]).sum())
                    buy = float(L[m & (SD == 1)].sum()); sell = float(L[m & (SD == 2)].sum())
                    totlot = float(L.sum()) or 1
                    def top_br(arr):
                        vals = np.bincount(arr[m].astype(int), weights=L[m])
                        if not len(vals):
                            return None
                        vals[0] = 0
                        i = int(np.argmax(vals))
                        return {"ad": names[i] if i < len(names) else str(i), "pay": round(vals[i] / lot * 100, 1)} if vals[i] > 0 else None
                    kad = {"lot": lot, "tl": tl, "pay_gun": round(lot / totlot * 100, 1), "aktif_alis": round(buy / lot * 100, 1) if lot else None,
                           "aktif_satis": round(sell / lot * 100, 1) if lot else None, "alan": top_br(B), "satan": top_br(Sx),
                           "gun": f"{day[6:8]}.{day[4:6]}", "src": tsrc}
            parts = {}
            parts["kesisim"] = round(30 * min(1.0, ntf / max(1, min(len(order), C["conf_cok"] + 1))), 1)
            parts["tepki"] = round(25 * min(1.0, stt["tepki"] / 4), 1)
            done = stt["tuttu"] + stt["kirildi"]
            parts["tutma"] = round(15 * (stt["tuttu"] / done if done else 0.5), 1)
            parts["ob_skor"] = round(15 * max(g["skor"] for g in k["members"]) / 99, 1)
            parts["derinlik"] = round(10 * min(1.0, (dep or {}).get("oran", 0) / 2), 1)
            parts["kademe"] = round(5 * min(1.0, ((kad or {}).get("pay_gun") or 0) / 20), 1)
            guc = int(round(sum(parts.values())))
            dist = 0.0 if lo <= price <= hi else round(((hi if yon == "U" else lo) / price - 1) * 100, 2)
            uy = []
            for g in k["members"]:
                ms = _stats(g["bot"], g["top"], yon, S[g["tf"]], g["te"], C)
                uy.append({"tf": g["tf"], "top": round(g["top"], 4), "bot": round(g["bot"], 4), "skor": g["skor"], "t": _fmt_t(g["t"]),
                           "ugradi": ms["ugradi"], "tepki": ms["tepki"], "tuttu": ms["tuttu"], "kirildi": ms["kirildi"], "seans": ms["seans"]})
            done_ = stt["tuttu"] + stt["kirildi"]
            res.append({"ortak_n": ntf, "mevcut": [x for x in order if x in S], "mevcut_n": sum(1 for x in order if x in S),
                        "tum_n": len(order), "tutma_oran": round(stt["tuttu"] / done_ * 100, 1) if done_ else None,
                        "tepki_oran": round(stt["tepki"] / stt["ugradi"] * 100, 1) if stt["ugradi"] else None,
                        "derinlik_tl": round((dep or {}).get("lot", 0) * (lo + hi) / 2) if dep else 0,
                        "sym": sym, "mod": mod, "seans_ar": sess, "yon": yon, "tur": "Destek" if yon == "U" else "Direnç",
                        "lo": round(lo, 4), "hi": round(hi, 4), "mid": round((lo + hi) / 2, 4), "tfs": k["tfs"],
                        "tf_ad": [TF_LABEL.get(x, x) for x in k["tfs"]], "seviye": lvl, "guc": guc, "dokum": parts, "uzaklik": dist,
                        "fiyat": price, **stt, "say_tf_ad": TF_LABEL.get(fine, fine), "son_test_ad": _fmt_t(stt["son_test"]),
                        "derinlik": dep, "kademe": kad, "uyeler": uy})
        return res


    def scan(self):
        C = cfg()
        t0 = time.time()
        self.meta["state"] = "taranıyor"
        if self._live():
            self.depth_cache = {}
        days = self._days()
        syms = set()
        try:
            syms |= set(self.v127.bs.hist.get("5m", {}).keys())
        except Exception:
            pass
        if days:
            syms |= {p.stem for p in (ROOT / "data" / "trades" / days[-1]).glob("*.csv")}
        try:
            syms |= {k for k, e in self.ts.syms.items() if len(e.t)}
        except Exception:
            pass
        syms = sorted(syms)
        rows, by = [], {}
        from app import progress as PG
        PG.begin("ob", len(syms), "Order Block bölgeleri taranıyor")
        for i, s in enumerate(syms):
            PG.step("ob", done=i)
            try:
                r = self._scan_sym(s, C, days)
            except Exception as e:
                logger.debug("v136 %s: %s", s, e)
                r = []
            if r:
                rows.extend(r); by[s] = r
            if i % 20 == 19:
                time.sleep(0.05 if not _LOWR() else 0.15)   # CPU'yu boğma (v1.38.1 low_resource: daha uzun nefes)
        rows.sort(key=lambda r: -r["guc"])
        PG.end("ob")
        live = self._live()
        with self.lock:
            self.rows, self.by_sym = rows, by
            self.meta = {"ready": True, "state": "hazır", "ts": time.time(), "ts_ad": time.strftime("%d.%m %H:%M:%S"),
                         "sec": round(time.time() - t0, 1), "n_sym": len(by), "n_zone": len(rows), "live": live,
                         "src": "canlı İdealData" if live else "kayıtlı veri (canlı akış yok)",
                         "bar_son": self._bar_last(), "trade_gun": self.trade_cache.get("day"), "islem_gunleri": days, "cfg": C}
        logger.info("v136 OB taraması: %d hisse, %d bölge, %.1f sn", len(by), len(rows), time.time() - t0)

    def _bar_last(self):
        try:
            b = self.v127.bs.get("THYAO", "5m")
            return _fmt_t(b.t[-1]) if len(b) else None
        except Exception:
            return None

    def _loop(self):
        time.sleep(45 if not _LOWR() else 90)   # v1.38.1 küçük makinede daha geç başla
        while True:
            try:
                self.scan()
            except Exception:
                logger.exception("v136 scan")
                self.meta["state"] = "hata"
            C = cfg()
            time.sleep((C["interval_live_sec"] if self._live() else C["interval_idle_sec"]) * (_MUL() if _LOWR() else 1))


engine = Engine()


def _gz(request, obj):
    from app.main import _gz_json
    return _gz_json(request, obj)


@router.get("/api/ob/list")
def ob_list(request: Request, tur: str = Query(""), tf: str = Query(""), min_guc: int = Query(0), max_uzak: float = Query(0),
            seviye: str = Query(""), limit: int = Query(300, le=6000)):
    with engine.lock:
        rows = list(engine.rows); meta = dict(engine.meta)
    if tur in ("Destek", "Direnç"):
        rows = [r for r in rows if r["tur"] == tur]
    if tf in ("gunici", "ortak"):
        rows = [r for r in rows if r.get("mod") == tf]
    else:
        rows = [r for r in rows if r.get("mod") == "normal"]
        if tf:
            rows = [r for r in rows if tf in r["tfs"]]
    if min_guc:
        rows = [r for r in rows if r["guc"] >= min_guc]
    if max_uzak:
        rows = [r for r in rows if abs(r["uzaklik"]) <= max_uzak]
    if seviye:
        rows = [r for r in rows if r["seviye"] == seviye]
    meta["age_sec"] = int(time.time() - meta["ts"]) if meta.get("ts") else None
    lite = [{k: v for k, v in r.items() if k not in ("uyeler", "epizot")} for r in rows[:limit]]
    return _gz(request, {"meta": meta, "count": len(rows), "rows": lite, "tfs": cfg()["tfs"] + ["gunici"], "tf_label": TF_LABEL})


@router.get("/api/ob/detail/{sym}")
def ob_detail(request: Request, sym: str, tf: str = Query("15m")):
    sym = sym.upper()
    with engine.lock:
        zs = list(engine.by_sym.get(sym, [])); meta = dict(engine.meta)
    bars = []
    try:
        C = cfg(); tb = engine._tbars(sym, engine._days())
        if tf == "gunici":
            zs = [z for z in zs if z.get("mod") == "gunici"]
            b, _n, _s = engine._series(sym, "5m", tb, dict(C, min_bars=10))
            b = _slice_day(b, b.day[-1])
            sess = zs[0]["seans_ar"] if zs else {"lo": round(float(b.l.min()), 4), "hi": round(float(b.h.max()), 4), "gun": b.day[-1]}
        else:
            zs = [z for z in zs if z.get("mod") == "normal"]
            b, _n, _s = engine._series(sym, tf, tb, C)
            sess = None
        b = b.tail(160)
        bars = [[int(b.t[i]), round(float(b.o[i]), 4), round(float(b.h[i]), 4), round(float(b.l[i]), 4), round(float(b.c[i]), 4)] for i in range(len(b))]
    except Exception:
        pass
    meta["age_sec"] = int(time.time() - meta["ts"]) if meta.get("ts") else None
    sess = locals().get("sess")
    with engine.lock:
        ort = sorted([z for z in engine.by_sym.get(sym, []) if z.get("mod") == "ortak"], key=lambda z: (-z["ortak_n"], -z["guc"]))
    return _gz(request, {"sym": sym, "tf": tf, "zones": zs, "bars": bars, "seans": sess, "ortak": ort, "meta": meta, "tfs": cfg()["tfs"] + ["gunici"], "tf_label": TF_LABEL})


@router.get("/api/ob/status")
def ob_status():
    m = dict(engine.meta); m.pop("cfg", None)
    return m
