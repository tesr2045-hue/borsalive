"""v1.30.0 — OLAY LİSTESİ (ALARM): piyasa geneli olay motoru + alarm yöneticisi + birleşik alarm + hazır taramalar.

Olaylar POC Baskısı detayındaki OLAY LİSTESİ ile aynı kaynaktan (app/v124.py process / LT / süpürme / POC kayması)
üretilir: canlı gün → v124 motorunun zaten tüm hisseler için artımlı işlettiği durumdan (SB) imleçle okunur
(LT olayları için SB alt sınıfı sınırlı deque tutar), kayıtlı gün → diskten bir kez yeniden oynatılır (önbellek).
Bildirimler mevcut hub._emit("olay", nt, …) yolundan gider (OneSignal gönderim mantığı DEĞİŞMEDİ); varsayılan KAPALI.
"""
from __future__ import annotations

import bisect
import collections
import json
import logging
import math
import os
import threading
import time
from pathlib import Path

from app import v124
from app.v122 import CONT_FROM, CONT_TO, DiskDay, _day_label, _fp, _fs, _hms, _last_disk_day, _sec_now, _tick_size, _today

logger = logging.getLogger("v130")
VERSION = "1.30.0"
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
VDIR = DATA / "v130"
TRADES_DIR = DATA / "trades"
ALARM_FILE = VDIR / "alarms.json"
PRESET_FILE = Path(__file__).resolve().parent / "olay_presets.json"     # optimizasyon çıktısı (Cuma 02.10 + 01.10)
SW_TL = v124.SW_TL

# ------------------------------------------------------------------ olay türleri (POC Baskısı · OLAY LİSTESİ ile aynı kodlar)
EV = {
    "up": ("YÜKSELTME", "kay", "up"), "dn": ("DÜŞÜRME", "kay", "dn"),
    "dt": ("DESTEK TEMASI", "ds", "nt"), "db": ("DESTEK TEPKİSİ", "ds", "up"), "dk": ("DESTEK KIRILDI", "ds", "dn"),
    "rt": ("DİRENÇ TEMASI", "ds", "nt"), "rr": ("DİRENÇ REDDİ", "ds", "dn"), "rk": ("DİRENÇ KIRILDI", "ds", "up"),
    "sw": ("SÜPÜRME", "sw", "up"), "sen": ("SENARYO", "sen", "up"),
    "rksw": ("DİRENÇ KIRILDI + SÜPÜRME", "kombi", "up"),
}
LAB_DETAIL = {"dt": "Destek teması", "db": "DESTEK TEPKİSİ", "dk": "Destek kırıldı", "rt": "Direnç teması", "rr": "Direnç reddi", "rk": "Direnç kırıldı"}

# ------------------------------------------------------------------ birleşik alarm varsayılanları (optimizasyonla seçildi; olay_presets.json üzerine yazar)
COMBO_DEF = {"n": 4, "tl": 500_000, "lot": 0, "win": 300, "hold": 0, "pre": True, "g_n": 6, "g_tl": 1_000_000}
PRESETS_DEF = {
    "p_hk": {"l": "Hacimli kırılım (GÜÇLÜ)", "d": "Direnç kırıldı + ±5 dk içinde seviye üstüne ≥4 kademe / ≥500 bin ₺ yukarı süpürme, yalnız GÜÇLÜ (≥6 kademe ve ≥1 Mn ₺ ya da ≥2 nitelikli süpürme)",
             "kind": "combo", "grade": 2, "n": 4, "tl": 500_000, "win": 300, "hold": 0, "g_n": 6, "g_tl": 1_000_000},
    "p_ard": {"l": "Art arda süpürme", "d": "10 dk içinde ≥4 yukarı süpürme (her biri ≥4 kademe, ≥100 bin ₺), son süpürmenin vardığı fiyat ilkinin başladığı fiyatın üstünde",
              "kind": "ard", "k": 4, "w": 600, "n": 4, "tl": 100_000},
    "p_pocsw": {"l": "POC yükseltme + süpürme", "d": "POC yükseltildi ve ±2 dk içinde yeni POC'un üstüne ≥5 kademe / ≥250 bin ₺ yukarı süpürme",
                "kind": "pair", "a": "up", "n": 5, "tl": 250_000, "win": 120},
    "p_dbsw": {"l": "Destek tepkisi + süpürme", "d": "Destek tepkisi ve ±5 dk içinde seviyenin üstüne ≥5 kademe / ≥500 bin ₺ yukarı süpürme",
               "kind": "pair", "a": "db", "n": 5, "tl": 500_000, "win": 300},
    "p_tvy": {"l": "Tavan yolu", "d": "DİRENÇ KIRILDI + SÜPÜRME (varsayılan eşikler) ve tetikte fiyat tavana ≤%6, gün ≥+%3", "kind": "tvy", "tvd": 6.0, "gd": 3.0},
}
NT_PREFIX = "ol_"
ALARM_KEYS = ["rksw", "p_hk", "p_ard", "p_pocsw", "p_dbsw", "p_tvy", "rk", "sw", "up", "db", "sen", "rt", "rr", "dt", "dk", "dn"]


def nt_of(key: str) -> str:
    return NT_PREFIX + key


def NT_DEFAULTS() -> dict:
    return {nt_of(k): "off" for k in ALARM_KEYS}


def _tk(p):
    return _tick_size(p or 0)


def _pc(a, b):
    try:
        return (a / b - 1) * 100 if a and b else None
    except Exception:
        return None


def _r(v, d=2):
    return None if v is None else round(v, d)


def _ev_id(sym, k, t, lv) -> str:
    return f"{sym}|{k}|{int(t)}|{(lv or 0):.4f}"


# ================================================================ SB alt sınıfı (canlı LT olay kaydı) ==
class SBX(v124.SB):
    """v124 canlı durum nesnesi + sınırlı LT olay kaydı (POC seviyesi). rec=True (detay) davranışı aynen korunur."""
    __slots__ = ()

    def __init__(self, pc=None, av10=None, rec=False) -> None:
        super().__init__(pc, av10, rec)
        if not rec:
            self.ltp.ev = collections.deque(maxlen=400)


_ORIG_SB = v124.SB


def patch_v124() -> bool:
    if v124.SB is _ORIG_SB:
        v124.SB = SBX
    return v124.SB is SBX


# ================================================================ olay çıkarımı (canlı + yeniden oynatma ortak) ==
def sym_events(sym: str, st, names, pc=None) -> list:
    """SB durumundan OLAY LİSTESİ olayları (POC referansı) — metinler v124.detail ile birebir."""
    out = []
    f4 = _fp

    def add(t, k, lv, p, x, **kw):
        e = {"i": _ev_id(sym, k, t, lv), "s": sym, "t": int(t), "k": k, "lv": _r(lv, 4), "p": _r(p, 4), "x": x}
        g = _pc(p, pc)
        if g is not None:
            e["gd"] = round(g, 2)
        e.update(kw)
        out.append(e)

    for t, a, b in list(st.pev):
        k = "up" if b > a else "dn"
        add(t, k, b, b, f"POC {'yükseltildi' if b > a else 'düşürüldü'}: {f4(a)} → {f4(b)}", a=_r(a, 4))
    lt = st.ltp
    if lt.ev is not None:
        for t, k, lvl, p in list(lt.ev):
            add(t, k, lvl, p, f"{LAB_DETAIL[k]} · seviye {f4(lvl)} · fiyat {_fp(p)}")
    for key, v in list(st.ent.items()):
        if key.startswith("poc"):
            t, p = v
            add(t, "sen", 1.0 if key.endswith("t") else 0.0, p,
                f"SENARYO GİRİŞİ: {'TAVAN ADAYI' if key.endswith('t') else 'CİDDİ YÜKSELİŞ'} · fiyat {_fp(p)}", sc="t" if key.endswith("t") else "c")
    for x in list(st.sw):
        if x[3] >= SW_TL:
            br = names[x[6]] if x[6] < len(names) else ""
            add(x[0], "sw", x[5], x[5], f"Süpürme: {x[1]} kademe {_fp(x[4])}→{_fp(x[5])} · {_fs(x[2])} lot · {_fs(x[3])} ₺ · {br}",
                n=x[1], lot=x[2], tl=x[3], fr=_r(x[4], 4), to=_r(x[5], 4), br=br)
    return out


# ================================================================ fiyat yolu (saniye: [t, min, son]) ==
def sec_path(T, P, t0, t1) -> list:
    """T sıralı. [t0, t1] aralığındaki işlemlerden saniye bazında [t, min, son]."""
    i = bisect.bisect_left(T, t0)
    out = []
    n = len(T)
    while i < n and T[i] <= t1:
        t = T[i]; p = P[i]
        if out and out[-1][0] == t:
            o = out[-1]
            if p < o[1]:
                o[1] = p
            o[2] = p
        else:
            out.append([t, p, p])
        i += 1
    return out


def windows_union(ts, before, after) -> list:
    iv = sorted((t - before, t + after) for t in ts)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


class Path_:
    """Saniye yolu sorgusu (yalnız ilgili pencereler saklanır)."""
    __slots__ = ("pts", "ts")

    def __init__(self, pts) -> None:
        self.pts = pts
        self.ts = [x[0] for x in pts]

    def rng(self, a, b):
        i = bisect.bisect_left(self.ts, a)
        j = bisect.bisect_right(self.ts, b)
        return self.pts[i:j]

    def last_at(self, t):
        j = bisect.bisect_right(self.ts, t) - 1
        return self.pts[j][2] if j >= 0 else None


# ================================================================ birleşik dedektör (saf fonksiyon, birim testli) ==
def combo_eval(rks, sws, path, cfg, clock=None) -> tuple:
    """DİRENÇ KIRILDI + SÜPÜRME (yukarı).
    rks: [(t, seviye, fiyat)] direnç kırılımları; sws: [(t, kademe, lot, tl, from, to, kurum)] yukarı süpürmeler (aktif alış);
    path: Path_ (saniye yolu) ya da None; cfg: n, tl, lot, win, hold, pre, g_n, g_tl; clock: canlıda şimdiki sn (None = gün bitti).
    → (tetikler, bekleyen_rk). Kural: süpürme kırılımın ±win sn içinde (pre=False → yalnız sonra), süpürmenin vardığı fiyat ≥ kırılan
    seviye (seviyede/üstünde = gerçek, hacimli kırılım), kademe ≥ n, ₺ ≥ tl, lot ≥ lot; hold>0 → tetik anından sonra hold sn boyunca
    fiyat seviyenin altına inmez. Derece: GÜÇLÜ = (kademe ≥ g_n ve ₺ ≥ g_tl) veya pencerede ≥2 nitelikli süpürme; aksi ORTA."""
    n, tl, lot = cfg.get("n", 2), cfg.get("tl", 0), cfg.get("lot", 0)
    win, hold, pre = int(cfg.get("win", 120)), int(cfg.get("hold", 0)), cfg.get("pre", True)
    g_n, g_tl = cfg.get("g_n", 4), cfg.get("g_tl", 1e6)
    sts = [s[0] for s in sws]
    trig, pend = [], []
    used = set()                     # bir süpürme yalnız bir kırılımı onaylar (aynı seviyenin yeniden kırılımında tekrar yok)
    for rk in rks:
        t0, L = rk[0], rk[1]
        lo = t0 - (win if pre else 0)
        i = bisect.bisect_left(sts, lo)
        cands = []
        while i < len(sws) and sws[i][0] <= t0 + win:
            s = sws[i]
            if s[0] not in used and s[5] >= L - 1e-9 and s[5] > s[4] and s[1] >= n and s[3] >= tl and s[2] >= lot:
                cands.append(s)
            i += 1
        hit = None
        waiting = False
        for s in cands:
            tt = max(t0, s[0])
            if clock is not None and tt > clock:
                waiting = True
                break
            if hold > 0:
                if clock is not None and tt + hold > clock:
                    waiting = True
                    break
                seg = path.rng(tt + 1, tt + hold) if path is not None else []
                if any(x[1] < L - 1e-9 for x in seg):
                    continue
            hit = (tt, s)
            break
        if hit is None:
            if waiting or (clock is not None and clock < t0 + win):
                pend.append(rk)
            continue
        tt, s = hit
        used.add(s[0])
        nq = len(cands)
        strong = (s[1] >= g_n and s[3] >= g_tl) or nq >= 2
        tp = tt + hold
        px = (path.last_at(tp) if path is not None else None) or s[5]
        trig.append({"t": int(tp), "t_rk": int(t0), "L": L, "sw": list(s), "g": 2 if strong else 1, "p": px, "nq": nq})
    return trig, pend


def ard_eval(sws, cfg) -> list:
    """Art arda süpürme: w sn içinde ≥k nitelikli yukarı süpürme ve son süpürmenin vardığı fiyat ilk süpürmenin başladığı fiyatın üstünde."""
    k, w, n, tl = cfg.get("k", 3), cfg.get("w", 600), cfg.get("n", 2), cfg.get("tl", 100_000)
    q = collections.deque()
    out = []
    nxt = -1
    for s in sws:
        if s[1] < n or s[3] < tl:
            continue
        q.append(s)
        while q and q[0][0] < s[0] - w:
            q.popleft()
        if len(q) >= k and s[0] >= nxt and s[5] > q[0][4]:
            out.append({"t": int(s[0]), "sw": list(s), "c": len(q), "p": s[5], "tl": sum(x[3] for x in q), "fr": q[0][4]})
            nxt = s[0] + w
            q.clear()
    return out


def pair_eval(evs, sws, cfg) -> list:
    """Olay (POC yükseltme / destek tepkisi) + ±win içinde seviye üstünde yukarı süpürme."""
    n, tl, win = cfg.get("n", 2), cfg.get("tl", 250_000), cfg.get("win", 120)
    sts = [s[0] for s in sws]
    out = []
    for e in evs:
        t0, L = e[0], e[1]
        i = bisect.bisect_left(sts, t0 - win)
        while i < len(sws) and sws[i][0] <= t0 + win:
            s = sws[i]
            if s[5] >= L - 1e-9 and s[1] >= n and s[3] >= tl:
                out.append({"t": int(max(t0, s[0])), "t_a": int(t0), "L": L, "sw": list(s), "p": s[5]})
                break
            i += 1
    return out


# ================================================================ olay → metin ==
def fmt_trig(key: str, sym: str, tr: dict) -> tuple:
    """→ (olay etiketi, ayrıntı metni)."""
    s = tr.get("sw")
    sw_t = (f"{s[1]} kademe süpürme {_fs(s[3])} ₺" + (f" ({s[6]})" if len(s) > 6 and s[6] else "")) if s else ""
    if key == "rksw":
        return EV["rksw"][0], f"{_fp(tr['L'])} kırıldı, {sw_t} · {'GÜÇLÜ' if tr.get('g') == 2 else 'ORTA'}"
    if key == "p_hk":
        return "HACİMLİ KIRILIM (GÜÇLÜ)", f"{_fp(tr['L'])} kırıldı, {sw_t}"
    if key == "p_tvy":
        return "TAVAN YOLU", f"{_fp(tr['L'])} kırıldı, {sw_t} · tavana %{(tr.get('tvd') or 0):.1f}".replace(".", ",")
    if key == "p_ard":
        return "ART ARDA SÜPÜRME", f"10 dk'da {tr['c']} yukarı süpürme · {_fp(tr['fr'])}→{_fp(tr['p'])} · {_fs(tr['tl'])} ₺"
    if key == "p_pocsw":
        return "POC YÜKSELTME + SÜPÜRME", f"POC {_fp(tr['L'])} oldu, {sw_t}"
    if key == "p_dbsw":
        return "DESTEK TEPKİSİ + SÜPÜRME", f"{_fp(tr['L'])} desteğinden tepki, {sw_t}"
    return key, ""


# ================================================================ gün durumu ==
class DayO:
    def __init__(self, day, live) -> None:
        self.day = day
        self.live = live
        self.ev: list = []                 # zaman sıralı (canlıda eklenerek)
        self.ids: set = set()
        self.by: dict = collections.defaultdict(list)    # sym → olaylar
        self.paths: dict = {}              # sym → Path_ (kayıtlı gün)
        self.meta: dict = {}               # sym → {pc, tv}
        self.ready = False
        self.err = None
        self.built_at = None
        self.trig: dict = {}               # (anahtar, cfg imzası) → tetikler
        self.tcache: dict = {}             # sym → (olay sayısı, cfg imzası, {anahtar: tetik olayları})
        self.ver = 0

    def add(self, e) -> bool:
        if e["i"] in self.ids:
            return False
        self.ids.add(e["i"])
        self.ev.append(e)
        self.by[e["s"]].append(e)
        self.ver += 1
        return True


def _limits_offline(day: str) -> dict:
    """v124._limits ile aynı kaynak (op/bars): sym → [önceki kapanış, 10 gün ort. lot]."""
    out = {}
    iso = f"{day[:4]}-{day[4:6]}-{day[6:]}"
    for f in (DATA / "op" / "bars").glob("*.json"):
        try:
            bars = (json.loads(f.read_text(encoding="utf-8")) or {}).get("bars") or []
        except Exception:
            continue
        pc = None
        prev = [b for b in bars if (b.get("d") or "") < iso]
        for b in reversed(bars[-15:]):
            if b.get("d") == iso:
                pc = b.get("pc")
                break
        if pc is None and prev:
            pc = prev[-1].get("c")
        vs = [b.get("v") for b in prev[-10:] if b.get("v")]
        out[f.stem] = [pc, (sum(vs) / len(vs)) if vs else None]
    return out


def replay_day(day: str, limits: dict | None = None, syms=None, keep_trades=False, sleep=0.0) -> dict:
    """Kayıtlı günü diskten yeniden oynatır → {sym: (olaylar, Path_, meta)} (+ isteğe bağlı işlemler)."""
    D = DiskDay(day)
    D.load()
    lim = limits if limits is not None else _limits_offline(day)
    names = D.brokers
    out = {}
    for k, (s, e) in enumerate(D.syms.items()):
        if syms and s not in syms:
            continue
        n = len(e.t)
        if n == 0:
            continue
        T = list(e.t); Pp = list(e.p); L = list(e.l); SD = list(e.sd); B = list(e.b)
        if any(T[i] > T[i + 1] for i in range(n - 1)):
            idx = sorted(range(n), key=T.__getitem__)
            T, Pp, L, SD, B = ([c[i] for i in idx] for c in (T, Pp, L, SD, B))
        lm = lim.get(s) or [None, None]
        st = _ORIG_SB(lm[0], lm[1], rec=False)
        st.pev = []; st.sw = []; st.ltp.ev = []
        v124.process(st, T, Pp, L, SD, B, ck_fn=v124._ck_entry)
        v124._sw_close(st)
        evs = sym_events(s, st, names, lm[0])
        anchors = [x["t"] for x in evs if x["k"] in ("rk", "db", "up")]
        pts = []
        for a, b in windows_union(anchors, 300, 1500):
            pts.extend(sec_path(T, Pp, a, b))
        out[s] = (evs, Path_(pts), {"pc": lm[0], "tv": st.tv, "last": st.last, "hi": st.hi}, (T, Pp) if keep_trades else None)
        if sleep and k % 8 == 0:
            time.sleep(sleep)
    return out


def sym_streams(evs) -> tuple:
    rks = [(e["t"], e["lv"], e["p"]) for e in evs if e["k"] == "rk"]
    sws = sorted(((e["t"], e["n"], e["lot"], e["tl"], e["fr"], e["to"], e.get("br", "")) for e in evs if e["k"] == "sw"))
    ups = [(e["t"], e["lv"]) for e in evs if e["k"] == "up"]
    dbs = [(e["t"], e["lv"]) for e in evs if e["k"] == "db"]
    rks.sort(); ups.sort(); dbs.sort()
    return rks, sws, ups, dbs


def triggers_for(key: str, sym: str, evs, path, meta, combo_cfg, pcfg, clock=None) -> tuple:
    """Bir hisse için birleşik / hazır tarama tetikleri → (tetikler, bekleyen var mı)."""
    rks, sws, ups, dbs = sym_streams(evs)
    pc, tv = (meta or {}).get("pc"), (meta or {}).get("tv")
    pend = False
    if key in ("rksw", "p_hk", "p_tvy"):
        cf = dict(combo_cfg)
        if key == "p_hk":
            cf.update({k: v for k, v in pcfg.items() if k in ("n", "tl", "win", "hold", "g_n", "g_tl")})
        tr, pe = combo_eval(rks, sws, path, cf, clock)
        pend = bool(pe)
        if key == "p_hk":
            tr = [x for x in tr if x["g"] >= pcfg.get("grade", 2)]
        if key == "p_tvy":
            o = []
            for x in tr:
                tvd = _pc(tv, x["p"]) if tv else None
                gd = _pc(x["p"], pc)
                if tvd is not None and gd is not None and tvd <= pcfg.get("tvd", 4.0) and gd >= pcfg.get("gd", 5.0):
                    x["tvd"] = round(tvd, 2)
                    o.append(x)
            tr = o
        return tr, pend
    if key == "p_ard":
        return ard_eval(sws, pcfg), False
    if key in ("p_pocsw", "p_dbsw"):
        return pair_eval(ups if key == "p_pocsw" else dbs, sws, pcfg), False
    return [], False


def trig_event(key, sym, tr, meta) -> dict:
    lab, x = fmt_trig(key, sym, tr)
    s = tr.get("sw") or [None] * 7
    lv = tr.get("L") or tr.get("p") or 0
    e = {"i": _ev_id(sym, key, tr["t"], lv), "s": sym, "t": int(tr["t"]), "k": key, "lab": lab, "lv": _r(lv, 4), "p": _r(tr.get("p"), 4), "x": x,
         "n": s[1], "lot": s[2], "tl": s[3], "br": s[6] if len(s) > 6 else "", "g": tr.get("g")}
    g = _pc(tr.get("p"), (meta or {}).get("pc"))
    if g is not None:
        e["gd"] = round(g, 2)
    if tr.get("t_rk") is not None:
        e["t_rk"] = tr["t_rk"]
    return e


# ================================================================ alarm yapılandırması ==
def _alarm_default(key: str) -> dict:
    a = {"on": False, "scope": "all", "syms": [], "min_tl": 0, "min_lot": 0, "min_n": 0, "from": "10:00", "to": "18:00", "cd": 30, "rate": 12}
    if key == "rksw":
        a.update({k: v for k, v in COMBO_DEF.items()})
        a["grade"] = 1
    if key == "sw":
        a.update({"min_n": 3, "min_tl": 1_000_000})
    if key in ("rt", "dt", "rr", "dk", "dn"):
        a.update({"rate": 6})
    return a


class OlayEngine:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.days: dict = {}
        self.b = self.m = self.hub = self.feed = None
        self.thread = None
        self.loops = self.errors = 0
        self.last_err = None
        self.timing = {}
        self.cfg = {"alarms": {k: _alarm_default(k) for k in ALARM_KEYS}, "ts": 0}
        self.presets = {"combo": dict(COMBO_DEF), "presets": json.loads(json.dumps(PRESETS_DEF)), "stats": {}, "opt": {}}
        self._load_presets()
        self._load_cfg()
        self._cur: dict = {}               # canlı: sym → (id(st), ptr, merges)
        self.fired: dict = {}              # (gün, anahtar, sym) → son sn
        self.frate: dict = collections.defaultdict(collections.deque)   # anahtar → zaman damgaları
        self.grate = collections.deque()
        self.sent = collections.deque(maxlen=200)
        self.dry = False
        self.dry_out: list = []
        self.sender = None
        self.started_sec = None
        self._building = set()
        self.migr = None

    # ------------------------------------------------------------ setup --
    def _load_presets(self) -> None:
        try:
            d = json.loads(PRESET_FILE.read_text(encoding="utf-8"))
            self.presets["combo"].update(d.get("combo") or {})
            for k, v in (d.get("presets") or {}).items():
                if k in self.presets["presets"]:
                    self.presets["presets"][k].update(v)
            self.presets["stats"] = d.get("stats") or {}
            self.presets["opt"] = d.get("opt") or {}
            self.presets["best"] = d.get("best")
        except Exception:
            pass
        COMBO_DEF.update({k: v for k, v in self.presets["combo"].items() if k in COMBO_DEF})

    def _load_cfg(self) -> None:
        try:
            d = json.loads(ALARM_FILE.read_text(encoding="utf-8"))
            for k, v in (d.get("alarms") or {}).items():
                if k in self.cfg["alarms"]:
                    self.cfg["alarms"][k].update(v)
            self.cfg["ts"] = d.get("ts") or 0
        except Exception:
            for k in ALARM_KEYS:
                self.cfg["alarms"][k] = _alarm_default(k)

    def _save_cfg(self) -> None:
        VDIR.mkdir(parents=True, exist_ok=True)
        tmp = ALARM_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.cfg, ensure_ascii=False))
        os.replace(tmp, ALARM_FILE)

    def start(self, b_engine, m_engine, hub, feed) -> None:
        self.b, self.m, self.hub, self.feed = b_engine, m_engine, hub, feed
        self.started_sec = _sec_now()
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name="v130-olay", daemon=True)
            self.thread.start()

    # ------------------------------------------------------------ günler --
    def live_day(self):
        try:
            return self.m._live_day() if self.m is not None else None
        except Exception:
            return None

    def disk_days(self) -> list:
        try:
            return sorted((d.name for d in TRADES_DIR.iterdir() if d.is_dir() and d.name.isdigit() and any(True for _ in d.glob("*.csv"))), reverse=True)
        except Exception:
            return []

    def resolve(self, date=None):
        live = self.live_day()
        d = (date or "").replace("-", "").strip()
        if d and d.isdigit() and len(d) == 8:
            return d, d == live
        if live:
            return live, True
        return _last_disk_day(_today() + "x") or (self.disk_days() or [None])[0], False

    def _ensure_offline(self, day: str) -> "DayO":
        D = self.days.get(day)
        if D is not None and (D.ready or day in self._building):
            return D
        if D is None:
            D = DayO(day, False)
            with self.lock:
                self.days[day] = D
                for old in [d for d in self.days if d != day and d != self.live_day()][:-2]:
                    self.days.pop(old, None)
        self._building.add(day)
        threading.Thread(target=self._build_offline, args=(D,), name=f"v130-replay-{day}", daemon=True).start()
        return D

    def _build_offline(self, D: "DayO") -> None:
        t0 = time.time()
        try:
            lim = None
            try:
                if self.b is not None:
                    lim = self.b._limits(D.day, False)
            except Exception:
                lim = None
            res = replay_day(D.day, lim, sleep=0.001 if self.b is not None else 0.0)
            allev = []
            for s, (evs, path, meta, _) in res.items():
                D.paths[s] = path
                D.meta[s] = meta
                allev.extend(evs)
            allev.sort(key=lambda e: (e["t"], e["s"]))
            for e in allev:
                D.add(e)
            D.ready = True
            D.built_at = time.strftime("%H:%M:%S")
            self.timing["replay_" + D.day] = round(time.time() - t0, 1)
            logger.info("v130: %s yeniden oynatıldı (%d olay, %.1f sn)", D.day, len(D.ev), time.time() - t0)
        except Exception as ex:
            D.err = f"{type(ex).__name__}: {ex}"
            logger.exception("v130 replay")
        finally:
            self._building.discard(D.day)

    # ------------------------------------------------------------ canlı --
    def _loop(self) -> None:
        time.sleep(20)
        while True:
            t0 = time.time()
            try:
                live = self.live_day()
                if live:
                    self._step_live(live)
                else:
                    d, _ = self.resolve(None)
                    if d:
                        self._ensure_offline(d)
                self.loops += 1
            except Exception as ex:
                self.errors += 1
                self.last_err = f"{type(ex).__name__}: {ex}"
                logger.exception("v130 loop")
            self.timing["loop"] = round(time.time() - t0, 3)
            time.sleep(3)

    def _step_live(self, day: str) -> None:
        B = self.b.days.get(day) if self.b is not None else None
        if B is None:
            return
        D = self.days.get(day)
        if D is None or not D.live:
            D = DayO(day, True)
            with self.lock:
                self.days[day] = D
            self._cur = {}
        try:
            mode, syms, brokers, lock, sid = self.m._src(day)
            names = list(brokers)
        except Exception:
            names, syms, lock = [""], {}, threading.RLock()
        new = []
        for s, st in list(B.st.items()):
            key = (id(st), st.ptr, st.merges)
            if self._cur.get(s) == key:
                continue
            self._cur[s] = key
            D.meta[s] = {"pc": st.pc, "tv": st.tv, "last": st.last, "hi": st.hi}
            for e in sym_events(s, st, names, st.pc):
                if D.add(e):
                    new.append(e)
        if new:
            D.ev.sort(key=lambda e: e["t"])
        D.ready = True
        D.built_at = time.strftime("%H:%M:%S")
        self._alarms_live(D, new, syms, lock)

    def _live_path(self, syms, lock, sym, a, b):
        e = syms.get(sym)
        if e is None:
            return Path_([])
        with lock:
            n = len(e.t)
            i = bisect.bisect_left(e.t, a, 0, n)
            j = bisect.bisect_right(e.t, b, 0, n)
            T = list(e.t[i:j]); P = list(e.p[i:j])
        return Path_(sec_path(T, P, a, b))

    # ------------------------------------------------------------ alarmlar --
    def _on_keys(self) -> list:
        return [k for k in ALARM_KEYS if self.cfg["alarms"].get(k, {}).get("on")]

    def _passes(self, key: str, a: dict, e: dict) -> bool:
        if a.get("scope") == "list" and e["s"] not in (a.get("syms") or []):
            return False
        if (e.get("tl") or 0) < (a.get("min_tl") or 0) and key in ("sw",):
            return False
        if key == "sw":
            if (e.get("n") or 0) < (a.get("min_n") or 0) or (e.get("lot") or 0) < (a.get("min_lot") or 0):
                return False
        elif key in ("rksw", "p_hk", "p_tvy", "p_ard", "p_pocsw", "p_dbsw"):
            if (e.get("tl") or 0) < (a.get("min_tl") or 0) or (e.get("lot") or 0) < (a.get("min_lot") or 0):
                return False
            if key == "rksw" and (e.get("g") or 1) < (a.get("grade") or 1):
                return False
        try:
            h0, m0 = (int(x) for x in (a.get("from") or "10:00").split(":"))
            h1, m1 = (int(x) for x in (a.get("to") or "18:00").split(":"))
            if not (h0 * 3600 + m0 * 60 <= e["t"] <= h1 * 3600 + m1 * 60 + 59):
                return False
        except Exception:
            pass
        return True

    def candidates(self, D: "DayO", new: list, path_fn=None, clock=None, only=None) -> list:
        """Açık alarmlar için yeni tetikler → [(anahtar, olay)] (canlı + kuru çalıştırma ortak)."""
        keys = only or self._on_keys()
        out = []
        if not keys:
            return out
        base = [k for k in keys if k in EV and k != "rksw"]
        for e in new:
            if e["k"] in base:
                out.append((e["k"], e))
        ck = [k for k in keys if k == "rksw" or k.startswith("p_")]
        if ck:
            syms = {e["s"] for e in new if e["k"] in ("rk", "sw", "up", "db")} | set(getattr(self, "_pend", set()))
            pend = set()
            for s in syms:
                evs = D.by.get(s, [])
                for k in ck:
                    a = self.cfg["alarms"][k]
                    cc = dict(COMBO_DEF)
                    if k == "rksw":
                        cc.update({x: a[x] for x in ("n", "tl", "lot", "win", "hold", "pre", "g_n", "g_tl") if x in a})
                    pc = self.presets["presets"].get(k, {})
                    need_path = (k in ("rksw", "p_hk", "p_tvy")) and cc.get("hold", 0) > 0
                    path = None
                    if need_path:
                        path = D.paths.get(s) if path_fn is None else path_fn(s)
                    trs, pe = triggers_for(k, s, evs, path, D.meta.get(s), cc, pc, clock)
                    if pe:
                        pend.add(s)
                    for tr in trs:
                        te = trig_event(k, s, tr, D.meta.get(s))
                        if te["i"] in D.ids:
                            continue
                        D.ids.add(te["i"])
                        out.append((k, te))
            self._pend = pend
        return out

    def _alarms_live(self, D, new, syms, lock) -> None:
        if not self._on_keys():
            return
        clock = max((m.get("last_t") or 0 for m in []), default=0) or _sec_now()
        cands = self.candidates(D, new, path_fn=lambda s: self._live_path(syms, lock, s, max(CONT_FROM, clock - 2400), clock), clock=clock)
        warm_cut = (self.started_sec or 0) + 60
        self.deliver(D.day, cands, now_sec=clock, warm_cut=warm_cut)

    def deliver(self, day, cands, now_sec=None, warm_cut=None) -> list:
        """Soğuma (hisse başına) + saatlik oran sınırı + döngü başına üst sınır → gönder (ya da kuru çalıştırmada topla)."""
        sent = []
        now = time.time()
        while self.grate and now - self.grate[0] > 3600:
            self.grate.popleft()
        per_loop = 0
        for key, e in sorted(cands, key=lambda x: x[1]["t"]):
            a = self.cfg["alarms"].get(key) or {}
            if not a.get("on") or not self._passes(key, a, e):
                continue
            if warm_cut is not None and e["t"] < warm_cut - 120 and not self.dry:
                continue                      # yeniden başlatma birikimi bildirilmez
            fk = (day, key, e["s"])
            last = self.fired.get(fk)
            if last is not None and e["t"] - last < (a.get("cd") or 0) * 60:
                continue
            dq = self.frate[key]
            ref = e["t"] if self.dry else now
            while dq and ref - dq[0] > 3600:
                dq.popleft()
            if len(dq) >= (a.get("rate") or 12):
                continue
            if not self.dry and (len(self.grate) >= 60 or per_loop >= 6):
                continue
            self.fired[fk] = e["t"]
            dq.append(ref)
            self.grate.append(now)
            per_loop += 1
            title, body = self.text(key, e)
            data = {"f": "olay_alarm", "ev": e["i"], "k": key, "t": e["t"], "price": e.get("p"), "day": day, "src": "v130"}
            rec = {"nt": nt_of(key), "sym": e["s"], "title": title, "text": body, "data": data, "tsec": e["t"]}
            if self.dry:
                self.dry_out.append(rec)
            else:
                try:
                    if self.sender is not None:
                        self.sender(rec)
                    elif self.hub is not None:
                        self.hub._emit("olay", rec["nt"], e["s"], title, body, data, tsec=e["t"])
                except Exception as ex:
                    logger.debug("v130 emit: %s", ex)
            self.sent.append({**rec, "ts": now})
            sent.append(rec)
        if len(self.fired) > 50000:
            self.fired = {k: v for k, v in self.fired.items() if k[0] == day}
        return sent

    @staticmethod
    def text(key: str, e: dict) -> tuple:
        s = e["s"]
        if key in EV and key != "rksw":
            lab = EV[key][0]
            return f"{'🟢' if EV[key][2] == 'up' else '🔴' if EV[key][2] == 'dn' else '⚪'} {s} · {lab}", f"{e['x']} · {_hms(e['t'])}"
        lab = e.get("lab") or EV.get(key, (key,))[0]
        return f"🚀 {s} · {lab}", f"{e['x']} · {_hms(e['t'])}"

    # ------------------------------------------------------------ API --
    def feed_q(self, date=None, k=None, d=None, min_tl=0, min_lot=0, min_n=0, sym=None, limit=400, since=0, g=0) -> dict:
        day, live = self.resolve(date)
        if not day:
            return {"error": "kayıtlı gün yok", "events": []}
        D = self.days.get(day)
        if D is None or (not D.ready and not live):
            D = self._ensure_offline(day) if not live else D
        if D is None or not D.ready:
            return {"day": day, "day_label": _day_label(day), "live": live, "ready": False, "building": True, "events": [], "counts": {},
                    "note": "Olaylar hesaplanıyor (tüm hisseler işlem işlem yeniden oynatılıyor, ~30 sn)…", "err": D.err if D else None}
        evs = list(D.ev)
        combo = dict(COMBO_DEF)
        a = self.cfg["alarms"].get("rksw") or {}
        combo.update({x: a[x] for x in ("n", "tl", "lot", "win", "hold", "pre", "g_n", "g_tl") if x in a})
        tg = self._trigs(D, ["rksw"] + list(PRESETS_DEF), combo)
        ks0 = set((k or "").split(",")) - {""} if k else set()
        evs = evs + [e for e in tg if e["k"] == "rksw" or e["k"] in ks0]
        pcnt = collections.Counter(e["k"] for e in tg)
        cnt = collections.Counter(e["k"] for e in D.ev)
        cnt.update(pcnt)
        ks = ks0 or None
        sy = (sym or "").upper().strip()
        out = []
        for e in evs:
            if ks and e["k"] not in ks:
                continue
            if d and EV.get(e["k"], ("", "", "nt"))[2] != d:
                continue
            if sy and not e["s"].startswith(sy):
                continue
            if min_tl and (e.get("tl") or 0) < min_tl:
                continue
            if min_lot and (e.get("lot") or 0) < min_lot:
                continue
            if min_n and (e.get("n") or 0) < min_n:
                continue
            if g and (e.get("g") or 0) < g:
                continue
            if since and e["t"] <= since:
                continue
            out.append(e)
        out.sort(key=lambda e: (e["t"], e["s"]), reverse=True)
        n = len(out)
        return {"day": day, "day_label": _day_label(day), "live": live, "ready": True, "built_at": D.built_at, "total": len(evs), "n": n,
                "counts": dict(cnt), "events": out[: max(1, min(int(limit or 400), 3000))], "combo": combo,
                "labels": {k: v[0] for k, v in EV.items()}, "groups": {k: v[1] for k, v in EV.items()}, "dirs": {k: v[2] for k, v in EV.items()},
                "days": self.disk_days()[:6], "version": VERSION}

    def _trigs(self, D: "DayO", keys, combo) -> list:
        """Birleşik / hazır tarama tetikleri — hisse başına önbellek (olay sayısı değişince yeniden hesaplanır)."""
        sig = json.dumps(combo, sort_keys=True)
        live_hold = D.live and combo.get("hold", 0) > 0
        pf = None
        if D.live:
            try:
                _, syms, _, lock, _ = self.m._src(D.day)
                now = _sec_now()
                pf = lambda s: self._live_path(syms, lock, s, max(CONT_FROM, now - 2400), now)
            except Exception:
                pf = None
        out = []
        for s, se in list(D.by.items()):
            c = D.tcache.get(s)
            if c is None or c[0] != len(se) or c[1] != sig or live_hold:
                c = (len(se), sig, {})
                D.tcache[s] = c
            for k in keys:
                if k not in c[2]:
                    if not any(x["k"] in ("rk", "sw") for x in se):
                        c[2][k] = []
                        continue
                    need = k in ("rksw", "p_hk", "p_tvy") and (combo.get("hold", 0) > 0 or (k == "p_hk" and self.presets["presets"]["p_hk"].get("hold", 0) > 0))
                    path = (pf(s) if pf else None) if (D.live and need) else D.paths.get(s)
                    trs, _ = triggers_for(k, s, se, path, D.meta.get(s), combo, self.presets["presets"].get(k, {}), _sec_now() if live_hold else None)
                    c[2][k] = [trig_event(k, s, x, D.meta.get(s)) for x in trs]
                out.extend(c[2][k])
        return out

    def alarms_get(self) -> dict:
        on = self._on_keys()
        return {"alarms": self.cfg["alarms"], "keys": ALARM_KEYS, "on": on, "n_on": len(on), "nt": {k: nt_of(k) for k in ALARM_KEYS},
                "labels": {k: (EV[k][0] if k in EV else self.presets["presets"].get(k, {}).get("l", k)) for k in ALARM_KEYS},
                "combo_def": COMBO_DEF, "sent": list(self.sent)[-30:], "ts": self.cfg.get("ts"),
                "note": "Varsayılan: tüm alarmlar KAPALI. Açtığınız alarm, aynı zamanda bu cihazda ilgili bildirim türünü BİLDİRİM moduna alır (Bildirimler › Ayarlar'dan KAPALI / GÖRÜNTÜLE / BİLDİRİM)."}

    def alarms_set(self, body: dict) -> dict:
        al = (body or {}).get("alarms") or {}
        with self.lock:
            for k, v in al.items():
                if k not in self.cfg["alarms"] or not isinstance(v, dict):
                    continue
                a = self.cfg["alarms"][k]
                for f, val in v.items():
                    if f == "on":
                        a["on"] = bool(val)
                    elif f == "scope":
                        a["scope"] = "list" if val == "list" else "all"
                    elif f == "syms":
                        a["syms"] = [str(x).upper().strip()[:12] for x in (val or []) if str(x).strip()][:300]
                    elif f in ("from", "to"):
                        s = str(val or "")[:5]
                        if len(s) == 5 and s[2] == ":" and s[:2].isdigit() and s[3:].isdigit():
                            a[f] = s
                    elif f in ("pre",):
                        a[f] = bool(val)
                    elif f in ("min_tl", "min_lot", "min_n", "cd", "rate", "n", "tl", "lot", "win", "hold", "g_n", "g_tl", "grade"):
                        try:
                            x = float(val)
                            if math.isfinite(x) and x >= 0:
                                a[f] = int(x) if f not in ("tl", "g_tl", "min_tl") else round(x)
                        except Exception:
                            pass
            if (body or {}).get("all_off"):
                for a in self.cfg["alarms"].values():
                    a["on"] = False
            self.cfg["ts"] = int(time.time() * 1000)
            self._save_cfg()
        return self.alarms_get()

    def presets_get(self) -> dict:
        return {"presets": self.presets["presets"], "stats": self.presets.get("stats") or {}, "combo": COMBO_DEF,
                "opt": self.presets.get("opt") or {}, "best": self.presets.get("best")}

    def status(self) -> dict:
        return {"version": VERSION, "loops": self.loops, "errors": self.errors, "last_err": self.last_err, "timing": self.timing,
                "patched": v124.SB is SBX, "days": {d: {"ready": D.ready, "live": D.live, "events": len(D.ev), "built_at": D.built_at, "err": D.err}
                                                    for d, D in list(self.days.items())},
                "alarms_on": self._on_keys(), "sent": len(self.sent), "migration": self.migr}


engine = OlayEngine()


# ================================================================ bildirim türleri: hepsi KAPALI (v1.30.0 göçü) ==
STATE_FILE = DATA / "notif_state_before_v1300.json"


def notif_all_off(hub, v120mod, extra: dict | None = None) -> dict:
    """Bir kerelik: tüm istemcilerin tüm bildirim türlerini KAPALI yapar, önceki durumu STATE_FILE'a yedekler.
    OneSignal App ID / anahtar / kayıtlar / gönderim mantığına dokunmaz; yalnız tür modları (notif.modes) değişir."""
    NT = v120mod.NTYPES
    if STATE_FILE.exists():
        for k in list(NT):
            NT[k] = "off"
        return {"done": False, "note": "göç daha önce yapılmış", "file": str(STATE_FILE)}
    before_def = dict(NT)
    snap = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "version": VERSION, "ntypes_defaults": before_def, "clients": {}, "extra": extra or {}}
    now_ms = int(time.time() * 1000)
    with hub.lock:
        for cid, c in hub.clients.items():
            cfg = c.get("cfg") or {}
            n = cfg.setdefault("notif", {})
            eff = {k: v120mod.nmode(cfg, k) for k in NT}
            snap["clients"][cid] = {"push": bool(c.get("push")), "os_ext": c.get("os_ext"), "master": n.get("master", True),
                                    "modes": dict(n.get("modes") or {}), "ts": n.get("ts"), "effective": eff,
                                    "on": sorted(k for k, v in eff.items() if v != "off"),
                                    "sections": {s: (cfg.get(s) or {}).get("on") for s in ("tavan", "agresif", "kurum")}}
    VDIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(snap, ensure_ascii=False, indent=1))
    os.replace(tmp, STATE_FILE)
    with hub.lock:
        for cid, c in hub.clients.items():
            n = c["cfg"].setdefault("notif", {})
            md = n.setdefault("modes", {})
            for k in NT:
                md[k] = "off"
            n["ts"] = now_ms
        for k in list(NT):
            NT[k] = "off"
    try:
        hub._save_clients()
    except Exception as ex:
        logger.warning("v130 save clients: %s", ex)
    return {"done": True, "clients": len(snap["clients"]), "types": len(NT), "file": str(STATE_FILE), "ts": now_ms}


# ================================================================ FastAPI ==
try:
    from fastapi import APIRouter, Request
    from fastapi.responses import JSONResponse

    router = APIRouter()

    @router.get("/api/olay/feed")
    def _api_feed(date: str | None = None, k: str | None = None, d: str | None = None, min_tl: float = 0, min_lot: float = 0,
                  min_n: int = 0, sym: str | None = None, limit: int = 400, since: int = 0, g: int = 0):
        return JSONResponse(engine.feed_q(date, k, d, min_tl, min_lot, min_n, sym, limit, since, g), headers={"Cache-Control": "no-store"})

    @router.get("/api/olay/alarms")
    def _api_alarms_get():
        return engine.alarms_get()

    @router.post("/api/olay/alarms")
    async def _api_alarms_set(request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        return engine.alarms_set(body or {})

    @router.get("/api/olay/presets")
    def _api_presets():
        return engine.presets_get()

    @router.get("/api/olay/status")
    def _api_status():
        return engine.status()
except Exception:      # pragma: no cover (FastAPI'siz ortam: hazırlık vekili / testler)
    router = None
