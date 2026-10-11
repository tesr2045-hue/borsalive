"""v1.33.0 — ALGO DESTEK / ALGO DİRENÇ: tüm hisselerin canlı derinliğinde algoritmik (tekrarlayan lot) duvar tespiti.

Örnek (kullanıcı ekranı): alış tarafında 57,45 → 56,55 arası 19 kademede ~10.000 lot (10.000 · 10.005 · 10.060 · 10.250 …).
Algoritma aynı lotu (taban lot B) ardışık kademelere dizer; üstüne gelen küçük emirler lotu B…B×1,3 aralığında tutar.

TESPİT (her 10 sn, ideal_feed.depth — DERİNLİK sekmesi ile aynı canlı defter, en fazla 25 kademe):
  · aday taban lot B: o taraftaki kademe lotları (≥ 50 bin ₺)
  · kademe uygun: B ≤ lot ≤ B × 1,30
  · en uzun ardışık uygun kademe dizisi (arada en fazla 1 uygunsuz kademe atlanabilir, sayılmaz)
  · ≥ 5 uygun kademe · dizinin toplamı ≥ 1 Mn ₺ · kademe başına ortalama emir ≤ 8 (çok emirli likit defterler doğal olarak benzer lot taşır — algo değil)
  · uygun kademelerin ≥ %30'u ve en az 3'ü lot B'ye ±%1 yakın (tam tekrar) YA DA dizide lot değişkenliği (CV) ≤ %6
  · aynı hisse/yön için en çok kademe (eşitlikte en yüksek ₺) seçilir
Kalıcılık: duvar art arda görüldükçe "ilk görülme" saati tutulur (5 dk görülmezse sıfırlanır).
"""
from __future__ import annotations

import logging
import threading
import time

from app.v122 import _fp, _fs

logger = logging.getLogger("bist.v133")
VERSION = "1.33.1"
LOOP = 10.0
TH = {"min_lv": 5, "tol": 0.30, "min_tl": 1_000_000, "lvl_tl": 50_000, "exact": 0.30, "ex_n": 3, "cv": 0.06, "gap": 1, "max_ord": 8.0}
CFG_FILE = None
try:
    from app import v130 as _v130
    CFG_FILE = _v130.DATA / "v133" / "algo.json"
except Exception:   # pragma: no cover
    pass


def _load_th():
    """data/v133/algo.json {"th": {...}} — yeniden başlatmadan eşik ayarı (her döngüde okunur)."""
    try:
        import json
        d = json.loads(CFG_FILE.read_text(encoding="utf-8"))
        for k, v in (d.get("th") or {}).items():
            if k in TH:
                TH[k] = type(TH[k])(v)
    except Exception:
        pass


def _pc(v, d=2):
    return (f"{v:+.{d}f}").replace(".", ",").replace("+", "+%").replace("-", "−%") if v is not None else "—"


def _lot(v):
    return f"{v:,.0f}".replace(",", ".")


def detect(levels, th=None):
    """levels: [(fiyat, lot, emir)] en iyi → kötü. → en iyi algo dizisi ya da None."""
    th = th or TH
    n = len(levels)
    if n < th["min_lv"]:
        return None
    cands = sorted({round(l) for p, l, _ in levels if p * l >= th["lvl_tl"] and l > 0})
    best = None
    for B in cands:
        hi = B * (1 + th["tol"])
        ok = [B - 1e-9 <= l <= hi + 1e-9 for _, l, _ in levels]
        i = 0
        while i < n:
            if not ok[i]:
                i += 1; continue
            j = i; idx = [i]; gap = 0
            k = i + 1
            while k < n:
                if ok[k]:
                    idx.append(k); gap = 0
                else:
                    gap += 1
                    if gap > th["gap"]:
                        break
                k += 1
            nlv = len(idx)
            if nlv >= th["min_lv"]:
                lots = [levels[x][1] for x in idx]
                tl = sum(levels[x][0] * levels[x][1] for x in idx)
                mean = sum(lots) / nlv
                cv = (sum((x - mean) ** 2 for x in lots) / nlv) ** 0.5 / mean if mean else 9
                ex = sum(1 for x in lots if abs(x - B) <= max(1.0, B * 0.01))
                ordn = sum(levels[x][2] or 0 for x in idx) / nlv
                if tl >= th["min_tl"] and ordn <= th["max_ord"] and ((ex >= th["ex_n"] and ex / nlv >= th["exact"]) or cv <= th["cv"]):
                    key = (nlv, tl)
                    if best is None or key > best["_k"]:
                        best = {"_k": key, "B": B, "idx": idx, "n": nlv, "tl": tl, "cv": cv, "ex": ex, "mean": mean,
                                "lots": lots, "p0": levels[idx[0]][0], "p1": levels[idx[-1]][0],
                                "ord": sum(levels[x][2] or 0 for x in idx)}
            i = idx[-1] + 1
    if best:
        best.pop("_k", None)
    return best


def effect(side, w, last, sym):
    p0, p1, B, n = _fp(w["p0"]), _fp(w["p1"]), _lot(w["B"]), w["n"]
    if side == "b":
        return (f"Algo destek {p0} → {p1}: fiyat indikçe her kademede ~{B} lot alıcı bekliyor ({n} kademe, {_fs(w['tl'])} ₺). "
                f"Destek tutarsa {p0} üzerinde taban oluşur ve sıçrama beklenir; duvar çekilir ya da kademeler hızla erirse "
                f"{p1} altına hızlı düşüş riski (algo desteği gidince alıcı boşluğu).")
    return (f"Algo direnç {p0} → {p1}: yükselişte her kademede ~{B} lot satıcı bekliyor ({n} kademe, {_fs(w['tl'])} ₺). "
            f"Direnç baskısı fiyatı {p0} altında tutabilir; duvar süpürülür ya da çekilirse {p1} üstüne hızlı yükseliş "
            f"(satıcı boşluğu) beklenir.")


class AlgoEngine:
    def __init__(self):
        self.feed = None
        self.lock = threading.RLock()
        self.res = {"b": [], "a": [], "ts": None}
        self.book = {}
        self.seen = {}      # (sym, side) → [ilk görülme, son görülme, ilk kademe sayısı]
        self.thread = None
        self.loops = self.errors = 0
        self.last_err = None
        self.ms = None

    def start(self, feed):
        self.feed = feed
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name="v133-algo", daemon=True)
            self.thread.start()

    def _loop(self):
        time.sleep(25)
        while True:
            t0 = time.time()
            try:
                self.compute()
                self.loops += 1
            except Exception as ex:
                self.errors += 1
                self.last_err = f"{type(ex).__name__}: {ex}"
                logger.exception("v133")
            self.ms = round((time.time() - t0) * 1000)
            time.sleep(max(2.0, LOOP - (time.time() - t0)))

    def compute(self):
        _load_th()
        F = self.feed
        uni = F.equity_universe()
        now = time.time()
        with F._lock:
            snap = {}
            for s in uni:
                d = F.depth.get(s)
                if not d or not d.get("ts") or now - d["ts"] > 1800:
                    continue
                q = F.quotes.get(s) or {}
                bids = [(v["price"], v["lot"], v.get("orders", 0)) for _, v in sorted(d["bids"].items()) if v.get("price") and v.get("lot")][:25]
                asks = [(v["price"], v["lot"], v.get("orders", 0)) for _, v in sorted(d["asks"].items()) if v.get("price") and v.get("lot")][:25]
                snap[s] = (bids, asks, q.get("last"), q.get("prev_close"), q.get("turnover"), d["ts"])
        out = {"b": [], "a": []}
        book = {}
        for s, (bids, asks, last, pc, to, ts) in snap.items():
            book[s] = (bids, asks, last, pc, ts)
            for side, lv in (("b", bids), ("a", asks)):
                w = detect(lv)
                if not w:
                    continue
                key = (s, side)
                sn = self.seen.get(key)
                if sn is None or now - sn[1] > 300:
                    sn = [now, now, w["n"]]
                sn[1] = now
                self.seen[key] = sn
                ref = last or (bids[0][0] if side == "b" and bids else asks[0][0] if asks else None)
                dist = (w["p0"] / ref - 1) * 100 if ref else None
                far = (w["p1"] / ref - 1) * 100 if ref else None
                opp = asks if side == "b" else bids
                otl = sum(p * l for p, l, _ in opp)
                r = {"s": s, "p": last, "c": round((last / pc - 1) * 100, 2) if (last and pc) else None, "t": to,
                     "B": w["B"], "n": w["n"], "tl": round(w["tl"]), "p0": w["p0"], "p1": w["p1"], "ex": w["ex"], "cv": round(w["cv"], 3),
                     "dist": round(dist, 2) if dist is not None else None, "far": round(far, 2) if far is not None else None,
                     "first": time.strftime("%H:%M:%S", time.localtime(sn[0])), "dur": round(now - sn[0]), "n0": sn[2],
                     "ratio": round(w["tl"] / otl, 2) if otl else None, "age": round(now - ts), "ord": w["ord"],
                     "pat": f"≈{_lot(w['B'])} lot × {w['n']} kademe", "eff": effect(side, w, last, s), "idx": w["idx"]}
                out[side].append(r)
        for k in [k for k, v in self.seen.items() if now - v[1] > 900]:
            self.seen.pop(k, None)
        for side in out:
            out[side].sort(key=lambda r: (-r["n"], -r["tl"]))
        with self.lock:
            self.res = {"b": out["b"], "a": out["a"], "ts": time.strftime("%H:%M:%S"), "epoch": now, "n_books": len(snap), "uni": len(uni)}
            self.book = book

    def listing(self):
        with self.lock:
            r = dict(self.res)
        r["version"] = VERSION; r["th"] = TH; r["loop"] = LOOP; r["ms"] = self.ms
        r["ready"] = r.get("ts") is not None
        r["age"] = round(time.time() - r["epoch"]) if r.get("epoch") else None
        return r

    def detail(self, sym):
        sym = (sym or "").upper().strip()
        with self.lock:
            bk = self.book.get(sym)
            hb = next((x for x in self.res["b"] if x["s"] == sym), None)
            ha = next((x for x in self.res["a"] if x["s"] == sym), None)
            ts = self.res.get("ts")
        if not bk:
            return {"s": sym, "found": False, "ts": ts}
        bids, asks, last, pc, bts = bk
        return {"s": sym, "found": True, "ts": ts, "p": last, "c": round((last / pc - 1) * 100, 2) if (last and pc) else None,
                "bids": [[p, l, o] for p, l, o in bids], "asks": [[p, l, o] for p, l, o in asks], "age": round(time.time() - bts),
                "b": hb, "a": ha, "name": (self.feed._name(sym) if self.feed is not None and hasattr(self.feed, "_name") else "")}

    def status(self):
        return {"version": VERSION, "loops": self.loops, "errors": self.errors, "last_err": self.last_err, "ms": self.ms,
                "nb": len(self.res.get("b") or []), "na": len(self.res.get("a") or []), "ts": self.res.get("ts")}


engine = AlgoEngine()

try:
    from fastapi import APIRouter, Query
    from fastapi.responses import JSONResponse

    router = APIRouter()

    @router.get("/api/algo/list")
    def _api_list():
        return JSONResponse(engine.listing(), headers={"Cache-Control": "no-store"})

    @router.get("/api/algo/detail")
    def _api_detail(s: str = Query("")):
        return JSONResponse(engine.detail(s), headers={"Cache-Control": "no-store"})

    @router.get("/api/algo/status")
    def _api_status():
        return engine.status()
except Exception:   # pragma: no cover
    router = None
