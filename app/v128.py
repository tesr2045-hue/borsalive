"""v1.28.0 — v1.27 formasyon motoruna ORDER BLOCK katmanı.

* Her periyot taramasının (Engine.scan_tf, arka plan iş parçacığı) hemen ardından AYNI barlarla (kapanmış n bar) tüm hisseler için
  OB + FVG tespiti yapılır; sonuç Engine.OB[tf][sym] (özet) olarak tutulur. 40 hissede bir 3 ms uyku → olay döngüsü bloklanmaz
  (iş parçacığı GIL'i bırakır; API uçları threadpool'da çalışır).
* /api/formasyon/hisse/{sym} çıktısına "ob" (periyot → en yakın arz/talep bölgeleri, FVG, sayımlar) ve "ob_def" eklenir.
* /api/formasyon/ob?sym&tf → animasyon için gerçek barlar + bölgeler (Engine.ob_kanit).
"""
from __future__ import annotations

import logging
import time

import numpy as np

from app import v127 as _m
from app import v128_ob as OB
from app.v127_bars import TF_LABEL, TFS, closed_count

logger = logging.getLogger("bist.v128")
Engine = _m.Engine
_f = _m._f


def _ob_one(b, n):
    res = OB.detect(b.o, b.h, b.l, b.c, b.v, b.t, n)
    return res, OB.summarize(res)


def _compact(sm):
    s = lambda zs: [OB.strip(z) for z in zs]
    return {"p": sm["p"], "atr": _f(sm["atr"]) if sm.get("atr") is not None else None, "sup": s(sm["sup"]), "dem": s(sm["dem"]),
            "kirik": s(sm["kirik"]), "fvg": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in f.items() if k != "k"} for f in sm["fvg"]],
            "n": sm["n"]}


_orig_scan = Engine.scan_tf
_orig_hisse = Engine.hisse


def scan_tf(self, tf):
    R = _orig_scan(self, tf)
    t0 = time.time()
    out = {}
    tot = val = taze = 0
    worst = 0.0
    for i, (s, r) in enumerate(list(R.items())):
        try:
            t1 = time.perf_counter()
            b = self.bs.get(s, tf)
            n = min(r["n"], len(b))
            if n >= 30:
                _, sm = _ob_one(b, n)
                out[s] = _compact(sm)
                tot += sm["n"]["tum"]; val += sm["n"]["gecerli"]; taze += sm["n"]["taze"]
            worst = max(worst, time.perf_counter() - t1)
        except Exception as ex:   # pragma: no cover
            logger.debug("v128 ob %s %s: %s", s, tf, ex)
        if i % 40 == 39:
            time.sleep(0.003)
    with self.lock:
        if not hasattr(self, "OB"):
            self.OB = {}
        self.OB[tf] = out
        info = dict(self.scan_info.get(tf) or {})
        info["ob"] = {"sec": round(time.time() - t0, 2), "syms": len(out), "zones": tot, "gecerli": val, "taze": taze, "max_ms": round(worst * 1000, 1)}
        self.scan_info[tf] = info
    return R


def hisse(self, sym):
    out = _orig_hisse(self, sym)
    s = sym.upper()
    ob = {}
    with self.lock:
        OBt = getattr(self, "OB", {})
        for tf in TFS:
            ob[tf] = (OBt.get(tf) or {}).get(s)
    out["ob"] = ob
    out["ob_def"] = OB.DEF_TXT
    return out


def ob_kanit(self, sym, tf):
    sym = sym.upper()
    if tf not in TFS:
        return {"ok": False, "error": "periyot"}
    with self.lock:
        r = self.R[tf].get(sym)
    b = self.bs.get(sym, tf)
    n = min(r["n"], len(b)) if r else closed_count(b, tf, self.clock())
    if n < 30:
        return {"ok": False, "error": "yetersiz bar"}
    res, sm = _ob_one(b, n)
    zs = sm["sup"] + sm["dem"]
    st = max(0, n - 120)
    if zs:
        jmin = min(z["j"] for z in zs)
        if jmin - 4 < st and n - jmin <= 260:
            st = max(0, jmin - 4)
    bars = {"t": [int(x) for x in b.t[st:n]], "o": [_f(x) for x in b.o[st:n]], "h": [_f(x) for x in b.h[st:n]], "l": [_f(x) for x in b.l[st:n]],
            "c": [_f(x) for x in b.c[st:n]], "v": [float(x) for x in b.v[st:n]]}
    with self.bs.lock:
        src = (self.bs.src.get(sym) or {}).get("today")
    c = _compact(sm)
    for z, zz in zip(sm["sup"] + sm["dem"], c["sup"] + c["dem"]):
        zz["win"] = z["j"] >= st          # köken mumu pencerede mi
        # itki barları (köken+1 … e) OHLC (kanıt tablosu)
        zz["imp_bars"] = [[int(b.t[k]), _f(b.o[k]), _f(b.h[k]), _f(b.l[k]), _f(b.c[k]), float(b.v[k])] for k in range(z["j"], z["e"] + 1)]
    return {"ok": True, "sym": sym, "tf": tf, "tfl": TF_LABEL[tf], "bars": bars, "ob": c, "def": OB.DEF_TXT, "src": _m.SRC_TXT[tf],
            "today_src": src, "closed_note": self.meta()["closed_note"],
            "param": {"imp_atr": OB.IMP_ATR, "imp_max_bars": OB.IMP_MAX_BARS, "fractal": OB.FR}}


Engine.scan_tf = scan_tf
Engine.hisse = hisse
Engine.ob_kanit = ob_kanit
v127 = _m.v127
