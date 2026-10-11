# Bağımsız yeniden sayım: motorun ürettiği bölgeler için ham barlardan (aynı tanımlar, ayrı kod) sayım.
import sys, types, json
sys.path.insert(0, "/workspace/bist-analiz")
import numpy as np
from app.v127_bars import BarStore
from app import v136
bs = BarStore(); bs.load_disk()
E = v136.engine
E.v127 = types.SimpleNamespace(bs=bs); E.feed = None
E.ts = types.SimpleNamespace(syms={}, day=None, brokers=[""])
C = v136.cfg(); days = E._days()

def recount(lo, hi, yon, b, t_from):
    tk = v136._tick(hi); N = C["react_bars"]
    buf = max(C["exit_buf_pct"] / 100, C["min_ticks"] * tk / hi); r = max(C["react_pct"] / 100, C["min_ticks"] * tk / hi)
    idx = np.nonzero(b.t > t_from)[0]
    H, L, Cl = b.h[idx], b.l[idx], b.c[idx]
    away = (L > hi * (1 + buf)) | (H < lo * (1 - buf))
    ins = (L <= hi) & (H >= lo)
    # epizotlar: 'away' olduktan sonraki ilk 'ins' bar başlar; sonraki ilk 'away' barında biter
    eps = []; armed = bool(len(away) and away[0]); start = None
    for k in range(len(idx)):
        if start is None:
            if not armed:
                armed = bool(away[k]); continue
            if ins[k]:
                start = k
            continue
        if away[k]:
            eps.append((start, k)); start = None; armed = True
    if start is not None:
        eps.append((start, len(idx) - 1))
    v = len(eps); te = tu = kr = 0
    for a, e in eps:
        seg = slice(a, e + 1)
        brk = (Cl[seg] < lo) if yon == "U" else (Cl[seg] > hi)
        bi = int(np.argmax(brk)) if brk.any() else None
        kr += 1 if bi is not None else 0
        tu += 0 if bi is not None else 1
        lim = min(e, a + N)
        rw = slice(a, lim + 1)
        hit = (H[rw] >= hi * (1 + r)) if yon == "U" else (L[rw] <= lo * (1 - r))
        hi_ = int(np.argmax(hit)) if hit.any() else None
        if hi_ is not None and (bi is None or hi_ < bi):
            te += 1
    return v, te, tu, kr

rows = []
for sym in sys.argv[1:]:
    tb = E._tbars(sym, days)
    res = E._scan_sym(sym, C, days)
    S = {}
    for tf in C["tfs"]:
        b, n, _ = E._series(sym, tf, tb, C)
        if b is not None: S[tf] = b
    for z in [x for x in res if x["mod"]=="normal" and x["yon"]=="U"][:2] + [x for x in res if x["mod"]=="normal" and x["yon"]=="D"][:2] + [x for x in res if x["mod"] == "gunici"][:1] + [x for x in res if x["mod"] == "ortak"][:2]:
        if z["mod"] == "gunici":
            b, n, _ = E._series(sym, z["say_tf"], tb, dict(C, min_bars=10)); b = v136._slice_day(b, b.day[-1])
        else:
            b = S[z["say_tf"]]
        # t_from: motorla aynı (en ince periyot üyelerinin itki bitişi) — motordan alınamadığı için pencere başından çıkar
        t0 = z["t_from"]
        v, te, tu, kr = recount(z["lo"], z["hi"], z["yon"], b, t0)
        rows.append((sym, z["mod"], z["tur"], f'{z["lo"]}-{z["hi"]}', z["say_tf"], z["seans"], (z["ugradi"], z["tepki"], z["tuttu"], z["kirildi"]), (v, te, tu, kr)))
ok = 0
for r in rows:
    m = r[6] == r[7]; ok += m
    print(f"{r[0]:6} {r[1]:6} {r[2]:6} {r[3]:15} {r[4]:4} seans={r[5]} motor(u/t/tut/k)={r[6]} bağımsız={r[7]} {'✓' if m else '✗'}")
print(f"{ok}/{len(rows)} eşleşti")
