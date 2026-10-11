"""v1.24.0 — POC BASKISI · ALIŞ ORTALAMA BASKISI · CİDDİ YÜKSELİŞ / TAVAN ADAYI (hazır senaryolar) + hisse ÖZET+ toplayıcı.

* İşlem işlem (zaman kovası yok) artımlı hesap: her hisse için gün içi POC (en çok lot işlem gören fiyat), aktif alış
  ortalaması (kümülatif aktif-alış ₺ / lot), destek/direnç testleri, süpürmeler, dakika özetleri.
* Kaynak v1.23 ile aynı: canlı TradeStore ya da diske kaydedilmiş gün (v122 DiskDay paylaşılır, ikinci kopya yüklenmez).
* Hazır senaryolar (CİDDİ YÜKSELİŞ / TAVAN ADAYI) her 5 dakikalık kontrol noktasında yerel koşullarla değerlendirilir →
  "senaryoya giriş saati / fiyatı" kaydedilir (geriye dönük sağlama için).
"""
from __future__ import annotations

import bisect
import collections
import json
import logging
import math
import threading
import time

from app.live_store import TRADES_DIR, EVENTS_DIR
from app.v122 import (CONT_FROM, CONT_TO, C, _clip, _day_label, _fold, _fp, _fs, _hm, _hms, _last_disk_day, _pc,
                      _sec_now, _tick_size, _today)

logger = logging.getLogger("v124")

VERSION = "1.24.0"
F_POC, F_AORT, F_CID = "k_poc", "k_aort", "k_ciddi"
FIDS = (F_POC, F_AORT, F_CID)
NT_POC, NT_AORT, NT_CID, NT_TVN = "k_poc", "k_aort", "k_ciddi", "k_tavanaday"
NT_DEFAULTS = {NT_POC: "view", NT_AORT: "view", NT_CID: "notify", NT_TVN: "notify"}
TITLES = {F_POC: "POC Baskısı", F_AORT: "Alış Ortalama Baskısı", F_CID: "Ciddi Yükseliş / Tavan Adayı (Birleşik)"}
SHORTS = {F_POC: "POC BASKISI", F_AORT: "ALIŞ ORT. BASKISI", F_CID: "CİDDİ / TAVAN ADAYI"}

WARM_N = 30            # POC'un "oturması" için en az işlem
HOLD = 60              # POC kayması: yeni POC ≥60 sn kalırsa kalıcı sayılır
AO_MIN = 10            # aktif alış ortalaması: en az 10 aktif alış
SW_TL = 100_000        # süpürme sayımı için en az ₺
MIN_TL = 250_000       # listeye girmek için gün içi işlem ₺
EPS = 1e-9
SANITY_C = "92 hisse girdi → 18'i tavan kapattı (%20), 8'i tavana ≤%1,5 kapattı, 45'i girişten sonra yükseldi (%49)"
SANITY_T = "23 hisse girdi → 11'i tavan kapattı (%48), 4'ü tavana ≤%1,5 kapattı, 13'ü girişten sonra yükseldi (%57)"

# ---------------------------------------------------------------- senaryo eşikleri (Cuma 02.10 verisiyle ayarlandı) --
P = {
    "c_gd": 3.0, "c_akt": 50.0, "c_tl": 3e6, "c_k": 5,      # CİDDİ YÜKSELİŞ: zorunlu + 7 opsiyonelden en az k
    "c_up": 2, "c_hi": 3.0, "c_a15": 60.0, "c_rv": 1.5, "c_mom": 0.5, "c_tv": 6.0,
    "t_gd": 5.0, "t_tv": 4.0, "t_akt": 55.0, "t_tl": 5e6, "t_mom": 0.5, "t_sw": 3, "t_k": 2,   # TAVAN ADAYI
    "t_up": 3, "t_hi": 2.5, "t_a15": 60.0, "t_rv": 2.0,
    "bounce": 2, "israr": 70, "t0": 10 * 3600 + 1800,
}


def _tk(p):
    return _tick_size(p or 0)


def _r(v, d=2):
    return None if v is None else round(v, d)


def _pct(a, b):
    try:
        return (a / b - 1) * 100 if a and b else None
    except Exception:
        return None


def _lim(pc):
    """BIST ±%10 fiyat limiti (tavan aşağı, taban yukarı fiyat adımına yuvarlanır)."""
    if not pc:
        return None, None
    up = pc * 1.1
    t = _tk(up)
    tv = math.floor(up / t + 1e-6) * t
    dn = pc * 0.9
    t2 = _tk(dn)
    tb = math.ceil(dn / t2 - 1e-6) * t2
    return round(tv, 4), round(tb, 4)


# ================================================================ TESTER ==
class LT:
    """Seviye testi (destek / direnç) — işlem işlem durum makinesi.
    Temas: üstten seviyenin en fazla tol = max(1 fiyat adımı, %0,1) üstüne inmek. Tepki: seviyenin tol + max(2 adım, %0,3) üstüne dönmek.
    Kırılım: seviyenin max(2 adım, %0,3) altına inmek. Yeniden kurulma (yeni test için): fiyat önce tepki seviyesine çıkmalı."""
    __slots__ = ("pos", "tt", "tr", "side", "st", "sb", "sk", "rt", "rr", "rk", "bt", "ev", "low")

    def __init__(self, rec=False) -> None:
        self.pos = 0
        self.tt = None
        self.tr = None
        self.side = 0
        self.st = self.sb = self.sk = self.rt = self.rr = self.rk = 0
        self.bt = collections.deque(maxlen=12)       # (temas sn, tepki sn, seviye)
        self.ev = [] if rec else None
        self.low = None

    def step(self, t, p, R):
        if R is None:
            return
        tk = _tk(R)
        tol = max(tk, R * 0.001)                 # temas bölgesi
        mv = max(2 * tk, R * 0.003)              # anlamlı hareket
        d = p - R
        if self.tt is None:
            if self.pos == 1 and d <= tol:
                self.tt, self.tr, self.side, self.low = t, R, 1, p
                self.st += 1
                if self.ev is not None:
                    self.ev.append((t, "dt", R, p))
            elif self.pos == -1 and d >= -tol:
                self.tt, self.tr, self.side, self.low = t, R, -1, p
                self.rt += 1
                if self.ev is not None:
                    self.ev.append((t, "rt", R, p))
            else:
                if d >= tol + mv:
                    self.pos = 1
                elif d <= -(tol + mv):
                    self.pos = -1
                return
        r0 = self.tr
        tk0 = _tk(r0)
        tol0 = max(tk0, r0 * 0.001)
        mv0 = max(2 * tk0, r0 * 0.003)
        dd = p - r0
        if self.side == 1:
            self.low = min(self.low, p)
            if dd >= tol0 + mv0:
                self.sb += 1; self.bt.append((self.tt, t, r0)); self.pos = 1; self.tt = None
                if self.ev is not None:
                    self.ev.append((t, "db", r0, p))
            elif dd <= -mv0:
                self.sk += 1; self.pos = -1 if dd <= -(tol0 + mv0) else 0; self.tt = None
                if self.ev is not None:
                    self.ev.append((t, "dk", r0, p))
        else:
            if dd <= -(tol0 + mv0):
                self.rr += 1; self.pos = -1; self.tt = None
                if self.ev is not None:
                    self.ev.append((t, "rr", r0, p))
            elif dd >= mv0:
                self.rk += 1; self.pos = 1 if dd >= tol0 + mv0 else 0; self.tt = None
                if self.ev is not None:
                    self.ev.append((t, "rk", r0, p))


# ============================================================ PER-SYMBOL ==
class SB:
    __slots__ = ("ptr", "merges", "n", "lot", "tl", "hi", "lo", "hi_t", "p0", "last", "last_t", "first_t", "vol", "poc",
                 "poc_since", "cp", "cp0", "cpx", "pup", "pdn", "pev", "alot", "atl", "an", "slot", "ao", "aom", "ao0", "aox",
                 "aup", "adn", "aev", "ltp", "lta", "mins", "sw", "sec", "pc", "tv", "tb", "av10", "ent", "ckt", "rec")

    def __init__(self, pc=None, av10=None, rec=False) -> None:
        self.ptr = 0
        self.merges = -1
        self.n = 0; self.lot = 0; self.tl = 0.0
        self.hi = self.lo = self.hi_t = self.p0 = self.last = self.last_t = self.first_t = None
        self.vol: dict = {}
        self.poc = self.poc_since = self.cp = self.cp0 = self.cpx = None
        self.pup = self.pdn = 0
        self.pev = collections.deque(maxlen=40) if not rec else []
        self.alot = 0; self.atl = 0.0; self.an = 0; self.slot = 0
        self.ao = self.aom = self.ao0 = self.aox = None
        self.aup = self.adn = 0
        self.aev = collections.deque(maxlen=40) if not rec else []
        self.ltp = LT(rec); self.lta = LT(rec)
        self.mins: dict = {}
        self.sw = collections.deque(maxlen=400) if not rec else []
        self.sec = None
        self.pc = pc
        self.tv, self.tb = _lim(pc)
        self.av10 = av10
        self.ent: dict = {}
        self.ckt = None
        self.rec = {"px": [], "poc": [], "ao": [], "ck": []} if rec else None


def _sw_close(st: SB) -> None:
    s = st.sec
    st.sec = None
    if not s or s[5] < 2:
        return
    tk = _tk(s[1])
    if s[2] - s[1] < tk * 0.99:
        return
    nlev = int(round((s[2] - s[1]) / tk)) + 1
    by = max(s[6], key=s[6].get) if s[6] else 0
    st.sw.append((s[0], nlev, s[3], round(s[4]), s[1], s[2], by))


def process(st: SB, T, P_, L, SD, B, ck_fn=None) -> None:
    rec = st.rec
    vol = st.vol
    for i in range(len(T)):
        t = T[i]; p = P_[i]; l = L[i]; sd = SD[i]
        ck = t // 300
        if st.ckt is None:
            st.ckt = ck
        elif ck != st.ckt:
            if ck_fn is not None and st.n >= WARM_N and st.last_t and st.last_t >= CONT_FROM:
                ck_fn(st, (st.ckt + 1) * 300)
            st.ckt = ck
        if st.sec is not None and st.sec[0] != t:
            _sw_close(st)
        st.n += 1; st.lot += l; st.tl += p * l
        if st.first_t is None:
            st.first_t = t
        if st.hi is None or p > st.hi + EPS:
            st.hi = p; st.hi_t = t
        if st.lo is None or p < st.lo - EPS:
            st.lo = p
        if st.p0 is None and t >= CONT_FROM:
            st.p0 = p
        v = vol.get(p, 0) + l
        vol[p] = v
        if st.poc is None or (p != st.poc and v > vol[st.poc]):
            st.poc = p; st.poc_since = t
        if st.cp is None:
            if st.n >= WARM_N:
                st.cp = st.cp0 = st.cpx = st.poc
        elif st.poc != st.cp and t - st.poc_since >= HOLD:
            st.pev.append((st.poc_since, st.cp, st.poc))
            if st.poc > st.cp:
                st.pup += 1
            else:
                st.pdn += 1
            st.cp = st.poc
            if st.poc > st.cpx:
                st.cpx = st.poc
        if sd == 1:
            st.alot += l; st.atl += p * l; st.an += 1
            s = st.sec
            if s is None:
                st.sec = [t, p, p, l, p * l, 1, {B[i]: l}]
            else:
                if p < s[1]: s[1] = p
                if p > s[2]: s[2] = p
                s[3] += l; s[4] += p * l; s[5] += 1
                s[6][B[i]] = s[6].get(B[i], 0) + l
            if st.an >= AO_MIN:
                ao = st.atl / st.alot
                st.ao = ao
                if st.aom is None:
                    st.aom = st.ao0 = st.aox = ao
                else:
                    step = max(_tk(ao), ao * 0.002)
                    if ao >= st.aom + step:
                        st.aev.append((t, st.aom, ao)); st.aup += 1; st.aom = ao
                    elif ao <= st.aom - step:
                        st.aev.append((t, st.aom, ao)); st.adn += 1; st.aom = ao
                    if ao > st.aox:
                        st.aox = ao
        elif sd == 2:
            st.slot += l
        if t >= CONT_FROM:
            st.ltp.step(t, p, st.cp)
            st.lta.step(t, p, st.ao)
        m = t // 60
        mm = st.mins.get(m)
        if mm is None:
            mm = st.mins[m] = [0, 0, 0.0, 0, 0, p, p]
        mm[0] += 1; mm[1] += l; mm[2] += p * l
        if sd == 1:
            mm[3] += l
        elif sd == 2:
            mm[4] += l
        mm[5] = p
        if p > mm[6]:
            mm[6] = p
        st.last = p; st.last_t = t
        if rec is not None:
            for key, val in (("px", p), ("poc", st.cp), ("ao", st.ao)):
                arr = rec[key]
                if val is None:
                    continue
                vv = round(val, 4)
                if arr and arr[-1][0] == t:
                    arr[-1][1] = vv
                elif not arr or arr[-1][1] != vv or key == "px":
                    arr.append([t, vv])


# ============================================================ CONDITIONS ==
def _vals(st: SB, t: int) -> dict:
    p = st.last
    a = st.alot + st.slot
    m1 = t // 60
    al15 = sl15 = 0
    for m in range(m1 - 14, m1 + 1):
        mm = st.mins.get(m)
        if mm:
            al15 += mm[3]; sl15 += mm[4]
    p15 = None
    for m in range(m1 - 15, m1 - 30, -1):
        mm = st.mins.get(m)
        if mm:
            p15 = mm[5]
            break
    if p15 is None:
        ks = [k for k in st.mins if k <= m1 - 15]
        if ks:
            p15 = st.mins[max(ks)][5]
    frac = max(0.05, min(1.0, (min(t, CONT_TO) - CONT_FROM) / (CONT_TO - CONT_FROM)))
    sw30 = sum(1 for x in st.sw if x[0] > t - 1800 and x[3] >= SW_TL)
    return {
        "p": p, "gd": _pct(p, st.pc), "akt": (st.alot / a * 100) if a else None,
        "a15": (al15 / (al15 + sl15) * 100) if (al15 + sl15) else None,
        "m15": _pct(p, p15) if p15 else None, "nh15": bool(st.hi_t and st.hi_t > t - 900 and st.hi and p >= st.hi - _tk(p) * 1.01),
        "rv": (st.lot / (st.av10 * frac)) if st.av10 else None,
        "sw30": sw30, "tvd": _pct(st.tv, p) if st.tv else None, "attv": bool(st.tv and p >= st.tv - EPS),
    }


def _ref(st: SB, ref: str):
    if ref == "poc":
        return st.cp, st.pup, st.pdn, st.cpx, st.ltp
    return st.ao, st.aup, st.adn, st.aox, st.lta


def checks(st: SB, v: dict, ref: str, extra: dict | None = None, t: int | None = None):
    """→ (ciddi_ok, tavan_ok, ciddi_list, tavan_list). Liste: [etiket, 1/0/None, grup] (grup: Z=zorunlu, O=opsiyonel, B=bonus)."""
    R, up, dn, Rx, lt = _ref(st, ref)
    nm = "POC" if ref == "poc" else "Alış ort."
    p = v["p"]
    ge = lambda x, th: (None if x is None else int(x >= th))
    le = lambda x, th: (None if x is None else int(x <= th))
    near = bool(R and R >= (Rx or R) - _tk(R) * 1.01)
    up_c = int(bool(R and up - dn >= P["c_up"] and near))
    up_t = int(bool(R and up - dn >= P["t_up"] and near))
    at = int(bool(R and p >= R - _tk(R) * 1.01))
    rhi = (st.hi / R - 1) * 100 if (R and st.hi) else None
    bn = int(lt.sb >= P["bounce"] and lt.sb > lt.sk)
    mom_c = int(bool((v["m15"] is not None and v["m15"] >= P["c_mom"]) or v["nh15"] or v["attv"]))
    mom_t = int(bool((v["m15"] is not None and v["m15"] >= P["t_mom"]) or v["nh15"] or v["attv"]))
    tt = t if t is not None else (st.last_t or 0)
    tok = int(tt >= P["t0"])
    ex = extra or {}
    bonus = [[f"Israrcı kurum (Israr ≥{P['israr']})", ex.get("israr"), "B"], ["AKD: TOPLAMA (az kurum alıyor)", ex.get("topl"), "B"],
             ["Tavan satışı inceliyor", ex.get("thin"), "B"]]
    cz = [[f"Gün ≥ +%{P['c_gd']:g}", ge(v["gd"], P["c_gd"]), "Z"], [f"Fiyat {nm} seviyesinde/üstünde", at, "Z"],
          [f"Aktif alış ≥ %{P['c_akt']:g}", ge(v["akt"], P["c_akt"]), "Z"], [f"İşlem ≥ {_fs(P['c_tl'])} ₺ · saat ≥ 10:30", int(st.tl >= P["c_tl"] and bool(tok)), "Z"]]
    co = [[f"{nm} net ≥{P['c_up']} kez yükseldi, zirvesinde", up_c, "O"], [f"≥{P['bounce']} destek tepkisi (tepki > kırılım)", bn, "O"],
          [f"{nm} gün yükseğine ≤ %{P['c_hi']:g}", le(rhi, P["c_hi"]), "O"], [f"Son 15 dk aktif ≥ %{P['c_a15']:g}", ge(v["a15"], P["c_a15"]), "O"],
          [f"RVOL ≥ {P['c_rv']:g}×", ge(v["rv"], P["c_rv"]), "O"], [f"Momentum (15 dk ≥ +%{P['c_mom']:g} / yeni zirve)", mom_c, "O"],
          [f"Tavana ≤ %{P['c_tv']:g}", le(v["tvd"], P["c_tv"]), "O"]]
    c_ok = all(x[1] == 1 for x in cz) and sum(1 for x in co if x[1] == 1) >= P["c_k"]
    tz = [[f"Gün ≥ +%{P['t_gd']:g}", ge(v["gd"], P["t_gd"]), "Z"], [f"Tavana ≤ %{P['t_tv']:g}", le(v["tvd"], P["t_tv"]), "Z"],
          [f"Fiyat {nm} seviyesinde/üstünde", at, "Z"], [f"Aktif alış ≥ %{P['t_akt']:g}", ge(v["akt"], P["t_akt"]), "Z"],
          [f"Momentum (15 dk ≥ +%{P['t_mom']:g} / yeni zirve / tavanda)", mom_t, "Z"],
          [f"Son 30 dk ≥{P['t_sw']} süpürme", int(v["sw30"] >= P["t_sw"]), "Z"],
          [f"İşlem ≥ {_fs(P['t_tl'])} ₺ · saat ≥ 10:30", int(st.tl >= P["t_tl"] and bool(tok)), "Z"]]
    to = [[f"{nm} net ≥{P['t_up']} kez yükseldi, zirvesinde", up_t, "O"], [f"≥{P['bounce']} destek tepkisi (tepki > kırılım)", bn, "O"],
          [f"{nm} gün yükseğine ≤ %{P['t_hi']:g}", le(rhi, P["t_hi"]), "O"], [f"Son 15 dk aktif ≥ %{P['t_a15']:g}", ge(v["a15"], P["t_a15"]), "O"],
          [f"RVOL ≥ {P['t_rv']:g}×", ge(v["rv"], P["t_rv"]), "O"]]
    t_ok = all(x[1] == 1 for x in tz) and sum(1 for x in to if x[1] == 1) >= P["t_k"]
    return c_ok, t_ok, cz + co + bonus, tz + to + bonus


def baski(st: SB, v: dict, ref: str):
    R, up, dn, Rx, lt = _ref(st, ref)
    if not R or not v["p"]:
        return None
    rhi = (st.hi / R - 1) * 100 if st.hi else 5
    sc = (22 * _clip((up - dn) / 4) + 22 * _clip(lt.sb / 3) + 20 * _clip(1 - rhi / 5) + 12 * _clip((v["p"] / R - 1) * 100 / 2)
          + 12 * _clip(((v["akt"] or 50) - 50) / 20) + 12 * _clip(((v["rv"] or 1) - 1) / 3) - 6 * min(lt.sk, 2))
    return round(max(0.0, min(100.0, sc)), 1)


def _ck_entry(st: SB, t: int) -> None:
    v = _vals(st, t)
    for ref in ("poc", "ao"):
        c_ok, t_ok, _, _ = checks(st, v, ref, None, t)
        for k, ok in (("c", c_ok), ("t", t_ok)):
            key = ref + k
            if ok and key not in st.ent:
                st.ent[key] = (t, st.last)
                if st.rec is not None:
                    st.rec["ck"].append((t, key, st.last))


# ================================================================ HELP ==
def _preset_doc(ref_nm: str) -> list:
    return [
        f"CİDDİ YÜKSELİŞ — ZORUNLU (hepsi): gün değişimi ≥ +%{P['c_gd']:g} · fiyat {ref_nm} seviyesinde ya da üstünde (en fazla 1 fiyat adımı altı) · "
        f"gün geneli aktif alış ≥ %{P['c_akt']:g} · bugüne kadar işlem ≥ {_fs(P['c_tl'])} ₺ · saat ≥ 10:30 (POC/ortalama otursun). "
        f"OPSİYONEL (7 koşuldan en az {P['c_k']}): {ref_nm} net ≥{P['c_up']} kez yükseltildi (yükseltme − düşürme) ve şu an gün içi zirvesinde (1 adım içinde) · "
        f"≥{P['bounce']} destek tepkisi ve tepki sayısı kırılımdan fazla · {ref_nm} ile gün yükseği arası ≤ %{P['c_hi']:g} · son 15 dk aktif alış ≥ %{P['c_a15']:g} · "
        f"zaman ayarlı RVOL ≥ {P['c_rv']:g}× · momentum (son 15 dk ≥ +%{P['c_mom']:g} ya da son 15 dk'da yeni gün zirvesi ya da tavanda) · tavana ≤ %{P['c_tv']:g}.",
        f"TAVAN ADAYI (daha sıkı) — ZORUNLU (hepsi): gün ≥ +%{P['t_gd']:g} · tavana ≤ %{P['t_tv']:g} · fiyat {ref_nm} seviyesinde/üstünde · aktif alış ≥ %{P['t_akt']:g} · "
        f"momentum (son 15 dk ≥ +%{P['t_mom']:g} / son 15 dk'da yeni zirve / tavanda) · son 30 dk'da ≥{P['t_sw']} süpürme (aynı saniyede ≥2 satış kademesini alan, "
        f"≥{_fs(SW_TL)} ₺ aktif alış) · işlem ≥ {_fs(P['t_tl'])} ₺ · saat ≥ 10:30. OPSİYONEL (5 koşuldan en az {P['t_k']}): {ref_nm} net ≥{P['t_up']} kez yükseldi ve zirvesinde · "
        f"≥{P['bounce']} destek tepkisi (tepki > kırılım) · {ref_nm}–gün yükseği ≤ %{P['t_hi']:g} · son 15 dk aktif ≥ %{P['t_a15']:g} · RVOL ≥ {P['t_rv']:g}×.",
        f"BONUS (eleme yapmaz, ✓ olarak görünür ve birleşik senaryo skorunu artırır): hissede Israr skoru ≥{P['israr']} bir kurum (Maliyet Yükselten Kurumlar) · "
        "AKD TOPLAMA (net alıcı kurum sayısı satıcıların ≤0,7 katı ve ilk 3 alıcı net alımın ≥%60'ı) · tavan satış kademesi son 15 dk zirvesinin ≤%60'ına indi (yalnız canlı seans).",
        "Senaryoya giren hisse daha sonra tavana kilitlenirse (aktif alış ve süpürme doğal olarak durur) listede 'TAVANDA' etiketiyle kalır.",
        "Her satırda ✓/✗ listesi hangi koşulun tuttuğunu gösterir (Z = zorunlu, O = opsiyonel, B = bonus; — = veri yok). "
        "Zaman ayarlı RVOL = bugüne kadarki lot ÷ (son 10 günün ortalama günlük lotu × seansın geçen oranı, en az %5).",
        "SENARYOYA GİRİŞ: koşullar her 5 dakikalık kontrol noktasında yeniden değerlendirilir; ilk sağlandığı saat ve o andaki fiyat kaydedilir, "
        f"'Girişten beri %' o fiyattan bugüne değişimdir. CUMA 02.10 SAĞLAMASI (POC + alış ort. birlikte, ilk giriş): CİDDİ YÜKSELİŞ ~{SANITY_C} · "
        f"TAVAN ADAYI ~{SANITY_T}. Karşılaştırma (aynı gün, saat 12/14/16 anlık taraması): gün ≥+%3 ve ≥3 Mn ₺ olan hisselerin ~%16'sı, gün ≥+%3 ve ≥5 Mn ₺ olanların ~%30'u tavan kapattı — yani CİDDİ YÜKSELİŞ bir 'tavan tahmincisi' değil, güçlü yükselişin kanıt listesidir; TAVAN ADAYI ise belirgin biçimde daha seçicidir. Tek günlük sağlamadır, garanti değildir.",
    ]


def _help(fid: str) -> dict:
    if fid == F_POC:
        ne = ("Gün içi POC (Point of Control: o güne kadar EN ÇOK LOT işlem gören fiyat) işlem işlem hesaplanır. POC'un yukarı kayması, alıcıların "
              "daha yüksek fiyatta yoğun işlem kabul ettiğini; POC'a geri gelip tepki veren fiyat, POC'un destek olduğunu gösterir. Baskı skoru bu "
              "yukarı yönlü baskıyı tek sayıda toplar.")
        nasil = (f"Her işlemde fiyat-lot histogramı güncellenir; en çok lotlu fiyat anlık POC'tur. İlk {WARM_N} işlem (POC oturmadan) sayılmaz. "
                 f"Yeni POC en az {HOLD} sn kalıcı olursa 'kayma' sayılır (yukarı = yükseltildi, aşağı = düşürüldü) ve saati kaydedilir. "
                 "DESTEK TESTİ: fiyat POC'un belirgin üstündeyken (POC + tol + hareket) POC'un en fazla tol = max(1 fiyat adımı, %0,1) üstüne inerse TEMAS sayılır; "
                 "ardından temas anındaki POC'un tol + max(2 adım, %0,3) üstüne dönerse 'DESTEK TEPKİSİ', POC'un max(2 adım, %0,3) altına inerse 'DESTEK KIRILDI'. "
                 "Örn. 3,04 ₺ POC'ta (adım 0,01): temas ≤3,05, tepki ≥3,07, kırılım ≤3,02; 292 ₺ POC'ta (adım 0,25): temas ≤292,25, tepki ≥293,25, kırılım ≤291,00. "
                 "Direnç bunun tersidir (alttan temas → aşağı dönüş = 'direnç reddi', POC'un üstüne çıkış = 'direnç kırıldı'). Uzaklıklar POC'a göre %: (seviye ÷ POC − 1). Tavan/taban: önceki "
                 "kapanışın ±%10'u fiyat adımına yuvarlanır (canlıda İdealData limitleri). Baskı skoru (0-100) = 22×net yükseltme (4'te tam) + 22×destek tepkisi "
                 "(3'te tam) + 20×POC'un zirveye yakınlığı (%5'te 0) + 12×fiyatın POC üstü mesafesi (%2'de tam) + 12×aktif alış (%50→%70) + 12×RVOL (1→4×) − 6×destek kırılımı (en çok 2).")
        kul = ("Önce CİDDİ YÜKSELİŞ / TAVAN ADAYI hazır senaryolarına bakın; sonra Baskı skoruna göre sıralayın. Satıra dokununca saniye saniye fiyat ile POC çizgisi, "
               "▲ yükseltme ve ● destek tepkisi işaretleri ve olay listesi açılır. İdeal tablo: POC birkaç kez yükseltilmiş, fiyat POC üstünde, POC zirveye yakın, "
               "en az 2 destek tepkisi ve az kırılım.")
        dk = ("POC tek bir fiyattır; çok sığ hissede birkaç büyük işlem POC'u oynatabilir (İşlem ₺ sütununa bakın). Seans başındaki kayıt boşlukları POC'u etkiler. "
              "Tepki/kırılım eşikleri fiyat adımına bağlıdır: ucuz hisselerde 1 adım %0,3'ü geçebilir. Yatırım tavsiyesi değildir.")
    elif fid == F_AORT:
        ne = ("Gün içi AKTİF ALIŞ ORTALAMASI (satıcının fiyatından alan, yani 'aktif' alışların kümülatif ₺ ÷ lot ortalaması) işlem işlem izlenir. "
              "Bu ortalamanın yükselmesi, aceleci alıcıların her seferinde daha yükseğe razı olduğunu; fiyatın ortalamaya dönüp tepki vermesi, alıcıların "
              "maliyetlerini savunduğunu gösterir.")
        nasil = (f"Ortalama, ilk {AO_MIN} aktif alıştan sonra başlar. Ortalama son işaretli değerinden max(1 adım, %0,2) yükselirse 'yükseltildi', "
                 "aynı kadar düşerse 'düşürüldü' sayılır (titreşime karşı histerezis). Destek/direnç testleri ve Baskı skoru POC Baskısı ile birebir aynı "
                 "kurallarla, POC yerine aktif alış ortalaması kullanılarak hesaplanır: temas = ortalamanın en fazla max(1 adım, %0,1) üstü, tepki = bunun "
                 "max(2 adım, %0,3) daha üstü, kırılım = ortalamanın max(2 adım, %0,3) altı.")
        kul = ("Ortalama sürekli yükseliyor, fiyat ortalamanın üstünde ve ortalamaya her dönüşte tepki geliyorsa alıcılar maliyetini savunuyor demektir. "
               "Satıra dokununca fiyat ile ortalama çizgisi, ▲ yükseltmeler ve ● tepkiler görünür.")
        dk = ("Aktif/pasif ayrımı işlem bazında bilinir; açılış/kapanış seansı eşleşmeleri aktif sayılmaz. Tek bir büyük aktif alış ortalamayı sıçratabilir. "
              "Yatırım tavsiyesi değildir.")
    else:
        ne = ("Üç tarayıcının (POC Baskısı, Alış Ortalama Baskısı, Maliyet Yükselten Kurumlar) hazır senaryo sinyallerini birleştirir: bir hisse en az "
              "birinde CİDDİ YÜKSELİŞ ya da TAVAN ADAYI koşullarını sağlıyorsa listelenir.")
        nasil = ("POC ve aktif alış ortalaması için senaryolar ayrı ayrı değerlendirilir; 'Kaynak' sütunu hangilerinde tuttuğunu gösterir. Maliyet Yükselten "
                 "Kurumlar kaynağı: hisse senaryoyu sağlarken maliyetini yükselten (artış > 0, ≥2 yükseltme; TAVAN ADAYI'nda ayrıca hâlâ alıyor) bir kurum var. "
                 "Senaryo skoru = tutan koşul sayısı ÷ toplam koşul (bonuslar dahil).")
        kul = "TAVAN ADAYI satırlarında ✓ sayısı yüksek ve giriş saati yeni olanlar en taze sinyallerdir; satıra dokunun → POC detay grafiği."
        dk = "Senaryolar geçmiş veriye göre ayarlanmış sezgisel filtrelerdir; tavanı garanti etmez. Yatırım tavsiyesi değildir."
    rn = "POC" if fid == F_POC else ("aktif alış ortalaması" if fid == F_AORT else "POC / aktif alış ortalaması")
    return {"ne": ne, "nasil": nasil, "nasil_kullan": kul, "dikkat": dk,
            "guide": [{"t": "Nasıl hesaplanır?", "p": [nasil]}, {"t": "Hazır senaryolar (CİDDİ YÜKSELİŞ / TAVAN ADAYI)", "p": _preset_doc(rn)},
                      {"t": "Nasıl kullanılır?", "p": [kul]}, {"t": "Dikkat edilmesi gerekenler", "p": [dk]}]}


WIN = {
    F_POC: [["tum", "TÜMÜ"], ["ciddi", "CİDDİ YÜKSELİŞ"], ["tavan", "TAVAN ADAYI"], ["s60", "SKOR ≥60"], ["up", "POC YÜKSELEN"],
            ["dest", "≥2 DESTEK TEPKİSİ"], ["ust", "FİYAT POC ÜSTÜ"], ["1m", "≥1 Mn ₺"], ["10m", "≥10 Mn ₺"]],
    F_AORT: [["tum", "TÜMÜ"], ["ciddi", "CİDDİ YÜKSELİŞ"], ["tavan", "TAVAN ADAYI"], ["s60", "SKOR ≥60"], ["up", "ORT. YÜKSELEN"],
             ["dest", "≥2 DESTEK TEPKİSİ"], ["ust", "FİYAT ORT. ÜSTÜ"], ["1m", "≥1 Mn ₺"], ["10m", "≥10 Mn ₺"]],
    F_CID: [["tum", "TÜMÜ"], ["ciddi", "CİDDİ YÜKSELİŞ"], ["tavan", "TAVAN ADAYI"]],
}


class DayB:
    def __init__(self, day, mode):
        self.day = day; self.mode = mode
        self.st: dict[str, SB] = {}
        self.rows = {F_POC: [], F_AORT: [], F_CID: []}
        self.sets = {"c": set(), "t": set()}
        self.chk: dict = {}
        self.ref = 0
        self.ready = False
        self.done = self.total = 0
        self.src_id = None
        self.ver = 0
        self.computed_at = None
        self._bt = 0
        self.km = (set(), set())


# ================================================================ ENGINE ==
class BaskiEngine:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.days: dict[str, DayB] = {}
        self.want = collections.deque()
        self.m = self.k = self.feed = self.hub = self.events = self.op = None
        self.thread = None
        self.loops = self.errors = 0
        self.last_err = None
        self.timing = {}
        self._lim: dict = {}
        self._akd: dict = {}
        self._cache: dict = {}
        self._ozc: dict = {}
        self._evc: dict = {}
        self.thin: dict = {}
        self.tvq: dict = {}
        self.alerted: dict = {}
        self.arate = collections.deque()
        self._warm = True

    def start(self, m_engine, k_engine, feed, hub, events, op_engine) -> None:
        self.m, self.k, self.feed, self.hub, self.events, self.op = m_engine, k_engine, feed, hub, events, op_engine
        try:
            m_engine.preset_fn = self.preset_for     # v1.24.0: Maliyet Yükselten Kurumlar hazır senaryo filtreleri
        except Exception:
            pass
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name="v124-baski", daemon=True)
            self.thread.start()

    # ------------------------------------------------------------ inputs --
    def _limits(self, day: str, live: bool) -> dict:
        """sym → [önceki kapanış, 10 gün ort. lot]."""
        hit = self._lim.get(day)
        if hit is not None and (not live or time.time() - hit.get("_ts", 0) < 300):
            return hit
        out = {"_ts": time.time()}
        iso = f"{day[:4]}-{day[4:6]}-{day[6:]}"
        try:
            for f in (TRADES_DIR.parent / "op" / "bars").glob("*.json"):
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
        except Exception as ex:
            logger.debug("v124 bars: %s", ex)
        q = getattr(self.feed, "quotes", None) or {}
        last_sess = day == _last_disk_day(_today()) and not live
        if live or last_sess:
            for s, v in list(q.items()):
                pc = v.get("prev_close")
                if pc and (live or s not in out or not out[s][0]):
                    out.setdefault(s, [None, None])[0] = pc
        self._lim[day] = out
        for d in [d for d in self._lim if d != day][:-3]:
            self._lim.pop(d, None)
        return out

    def _akd_map(self, day: str, live: bool) -> dict:
        hit = self._akd.get(day)
        if hit is not None and (not live or time.time() - hit[0] < 60):
            return hit[1]
        out = {}
        f = self.feed
        akd_day = None
        try:
            akd_day = f._akd_date() if f is not None else None
        except Exception:
            pass
        if akd_day == day and f is not None:
            try:
                for s, e in list(f._akdd().items()):
                    if e and e.get("date") == day and not e.get("empty"):
                        out[s] = conc(e.get("TUM") or [])
            except Exception as ex:
                logger.debug("v124 akd store: %s", ex)
        if not out:
            try:
                for p in (TRADES_DIR.parent / "akd" / day).glob("*.json"):
                    try:
                        d = json.loads(p.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    if not d.get("empty"):
                        out[p.stem] = conc(d.get("TUM") or [])
            except Exception:
                pass
        self._akd[day] = (time.time(), out)
        for d in [d for d in self._akd if d != day][:-2]:
            self._akd.pop(d, None)
        return out

    def _israr_map(self, day: str) -> dict:
        out = {}
        R = (self.m.days.get(day) if self.m is not None else None)
        if R is None or not R.ready:
            return out
        for r in R.rows:
            x = out.get(r["s"])
            if x is None or r.get("israr", 0) > x[1]:
                out[r["s"]] = (r["br"], r.get("israr", 0))
        return out

    def _thin_upd(self, live: bool) -> None:
        """Canlı: tavana ≤%5 hisselerde tavan satış kademesi lotu örneklenir (15 dk zirvesine göre incelme)."""
        if not live or self.feed is None:
            return
        now = time.time()
        q = getattr(self.feed, "quotes", {}) or {}
        dep = getattr(self.feed, "depth", {}) or {}
        for s, v in list(q.items()):
            ce, la = v.get("ceiling"), v.get("last")
            if not ce or not la or la < ce * 0.95:
                continue
            d = dep.get(s) or {}
            asks = list((d.get("asks") or {}).values())
            if not asks:
                continue
            lot = 0.0
            for a in asks:
                if abs((a.get("price") or 0) - ce) < 1e-6:
                    lot = a.get("lot") or 0.0
            if max((a.get("price") or 0) for a in asks) < ce - 1e-6 and lot == 0:
                continue        # tavan görünür 25 kademenin dışında
            dq = self.tvq.setdefault(s, collections.deque(maxlen=400))
            dq.append((now, lot))
            while dq and now - dq[0][0] > 900:
                dq.popleft()
            mx = max(x[1] for x in dq)
            self.thin[s] = (int(mx > 0 and lot <= 0.6 * mx and len(dq) >= 3), lot, mx)

    # -------------------------------------------------------------- loop --
    def _loop(self) -> None:
        time.sleep(12)
        for _ in range(60):
            try:
                if self.m._live_day() or getattr(getattr(self.k, "disk", None), "loaded", False):
                    break
            except Exception:
                break
            time.sleep(2)
        while True:
            t0 = time.time()
            live = None
            try:
                live = self.m._live_day()
                day = live or _last_disk_day(_today())
                if day:
                    D = self.days.get(day)
                    if live or D is None or not D.ready:
                        self._step(day, bool(live))
                    elif time.time() - D._bt > 30:
                        self._build(D, False)        # Israr / AKD sonradan hazır olabilir → hafif yeniden kurulum
                while self.want:
                    d = self.want.popleft()
                    D = self.days.get(d)
                    if D is None or not D.ready:
                        self._step(d, d == live)
                if live:
                    self._thin_upd(True)
                    self._alerts(self.days.get(live))
                self.loops += 1
            except Exception as ex:
                self.errors += 1
                self.last_err = f"{type(ex).__name__}: {ex}"
                logger.exception("v124 loop")
            self.timing["loop"] = round(time.time() - t0, 3)
            time.sleep(3)

    def _step(self, day: str, live: bool) -> None:
        t0 = time.time()
        mode, syms, brokers, lock, sid = self.m._src(day)
        D = self.days.get(day)
        if D is None or (D.src_id != sid and (live or not D.ready or D.mode == "canlı")):
            D = DayB(day, mode); D.src_id = sid
            with self.lock:
                self.days[day] = D
                for old in [d for d in self.days if d != day and d != self.m._live_day()][:-2]:
                    self.days.pop(old, None)
        lim = self._limits(day, live)
        keys = list(syms.keys())
        D.total = len(keys)
        changed = False
        for k, sym in enumerate(keys):
            e = syms.get(sym)
            if e is None:
                continue
            st = D.st.get(sym)
            with lock:
                n = len(e.t)
                mg = getattr(e, "snap_merges", 0)
                if st is not None and st.ptr == n and st.merges == mg:
                    sl = None
                else:
                    if st is None or st.merges != mg or n < st.ptr:
                        lm = lim.get(sym) or [None, None]
                        st = SB(lm[0], lm[1]); st.merges = mg
                    a = st.ptr
                    sl = (e.t[a:n], e.p[a:n], e.l[a:n], e.sd[a:n], e.b[a:n])
            if sl is None:
                continue
            T = sl[0]
            if any(T[i] > T[i + 1] for i in range(len(T) - 1)):
                idx = sorted(range(len(T)), key=T.__getitem__)
                sl = tuple([c[i] for i in idx] for c in sl)
            if live and st.pc is None:
                lm = lim.get(sym) or [None, None]
                st.pc = lm[0]; st.tv, st.tb = _lim(st.pc); st.av10 = lm[1]
            process(st, *sl, ck_fn=_ck_entry)
            if not live and st.sec is not None:
                _sw_close(st)
            st.ptr = n
            D.st[sym] = st
            changed = True
            D.done = k + 1
            if not live and k % 8 == 0:
                time.sleep(0.002)
        D.done = D.total
        if live:
            q = getattr(self.feed, "quotes", {}) or {}
            for s, st in D.st.items():
                v = q.get(s) or {}
                if v.get("ceiling") and v.get("floor") and st.pc and v["ceiling"] < st.pc * 1.105:
                    st.tv, st.tb = v["ceiling"], v["floor"]
        if changed or live or not D.ready:
            self._build(D, live)
        self.timing["step_" + ("live" if live else day)] = round(time.time() - t0, 3)
        if changed and not live:
            logger.info("v124: %s hesaplandı (%d hisse, %.1f sn)", day, len(D.st), time.time() - t0)

    def _build(self, D: DayB, live: bool) -> None:
        day = D.day
        ref = min(max(_sec_now(), CONT_FROM), CONT_TO + 600) if live else max((s.last_t or 0 for s in D.st.values()), default=0)
        isr = self._israr_map(day)
        akd = self._akd_map(day, live)
        rows_p, rows_a = [], []
        sets = {"c": set(), "t": set()}
        chk = {}
        for s, st in list(D.st.items()):
            if st.n < WARM_N or st.tl < MIN_TL or not st.last:
                continue
            t = ref if live else (st.last_t or ref)
            v = _vals(st, t)
            ib = isr.get(s)
            ak = akd.get(s)
            th = self.thin.get(s) if live else None
            extra = {"israr": (int(ib[1] >= P["israr"]) if ib else 0) if isr else None,
                     "topl": (int(ak[0] == "TOPLAMA") if ak else None), "thin": (th[0] if th else None)}
            per = {}
            for ref_k, rows in (("poc", rows_p), ("ao", rows_a)):
                c_ok, t_ok, cl, tlst = checks(st, v, ref_k, extra, t)
                if v["attv"]:      # senaryoya girmiş, sonra tavana kilitlenmiş → listede kalır (TAVANDA)
                    c_ok = c_ok or bool(st.ent.get(ref_k + "c"))
                    t_ok = t_ok or bool(st.ent.get(ref_k + "t"))
                if live:
                    for kk, ok in (("c", c_ok), ("t", t_ok)):
                        if ok and ref_k + kk not in st.ent:
                            st.ent[ref_k + kk] = (ref, st.last)
                per[ref_k] = (c_ok, t_ok, cl, tlst)
                r = self._row(s, st, v, ref_k, c_ok, t_ok, cl, tlst)
                if r:
                    rows.append(r)
            chk[s] = {"v": v, "per": per, "israr": ib, "akd": ak, "thin": th, "extra": extra}
        R = self.m.days.get(day) if self.m is not None else None
        kmc, kmt = set(), set()
        if R is not None and R.ready:
            for r in R.rows:
                c = chk.get(r["s"])
                if not c:
                    continue
                cc = c["per"]["poc"][0] or c["per"]["ao"][0]
                tt = c["per"]["poc"][1] or c["per"]["ao"][1]
                if cc and r.get("chg", 0) > 0 and r.get("ys", 0) >= 2:
                    kmc.add(r["s"])
                if tt and r.get("chg", 0) > 0 and r.get("ys", 0) >= 2 and r.get("still") not in (None, "—"):
                    kmt.add(r["s"])
        rows_c = []
        for s, c in chk.items():
            pp, aa = c["per"]["poc"], c["per"]["ao"]
            ic = pp[0] or aa[0]
            it = pp[1] or aa[1]
            if ic:
                sets["c"].add(s)
            if it:
                sets["t"].add(s)
            if ic or it:
                rows_c.append(self._crow(s, D.st[s], c, s in kmc, s in kmt))
        rows_p.sort(key=lambda r: -(r["sc"] or 0)); rows_a.sort(key=lambda r: -(r["sc"] or 0))
        rows_c.sort(key=lambda r: (-(r["tvn"]), -(r["sc"] or 0)))
        with self.lock:
            D.rows = {F_POC: rows_p, F_AORT: rows_a, F_CID: rows_c}
            D.sets = sets; D.chk = chk; D.ref = ref; D.ready = True
            if live:
                D.mode = "canlı"
            D.ver += 1; D.computed_at = time.strftime("%H:%M:%S")
            D._bt = time.time()
            D.km = (kmc, kmt)
        self._cache.clear()

    @staticmethod
    def _times(evs, n=4):
        return " ".join(_hm(e[0]) + ("↑" if e[2] > e[1] else "↓") for e in list(evs)[-n:])

    def _row(self, s, st, v, ref, c_ok, t_ok, cl, tlst):
        R, up, dn, Rx, lt = _ref(st, ref)
        if not R:
            return None
        sen = "TAVAN ADAYI" if t_ok else ("CİDDİ YÜKSELİŞ" if c_ok else "")
        if sen and v["attv"]:
            sen += " · TAVANDA"
        r = {"s": s, "gd": _r(v["gd"]), "p": v["p"], "sc": baski(st, v, ref), "ref": _r(R, 4),
             "pr": _r(_pct(v["p"], R)), "rh": _r(_pct(st.hi, R)), "rl": _r(_pct(st.lo, R)),
             "rtv": _r(_pct(st.tv, R)), "rtb": _r(_pct(st.tb, R)), "up": up, "dn": dn,
             "upt": self._times(st.pev if ref == "poc" else st.aev),
             "dst": lt.st, "dsb": lt.sb, "dsk": lt.sk, "dbt": " ".join(_hm(x[1]) for x in list(lt.bt)[-4:]),
             "rst": lt.rt, "rsr": lt.rr, "rsk": lt.rk, "akt": _r(v["akt"], 1), "a15": _r(v["a15"], 1), "rv": _r(v["rv"]),
             "tl": round(st.tl), "sw30": v["sw30"], "tvd": _r(v["tvd"]), "r0": _r(st.cp0 if ref == "poc" else st.ao0, 4),
             "sen": sen, "c_ok": int(c_ok), "t_ok": int(t_ok), "ck_c": cl, "ck_t": tlst}
        ec, et = st.ent.get(ref + "c"), st.ent.get(ref + "t")
        r["ent_c"] = [_hm(ec[0]), ec[1], _r(_pct(v["p"], ec[1]))] if ec else None
        r["ent_t"] = [_hm(et[0]), et[1], _r(_pct(v["p"], et[1]))] if et else None
        e = r["ent_t"] if t_ok else (r["ent_c"] if c_ok else None)
        if e:
            r["ent"], r["entp"], r["entr"] = e
        return r

    def _crow(self, s, st, c, kmc, kmt):
        v = c["v"]; pp, aa = c["per"]["poc"], c["per"]["ao"]
        it = bool(pp[1] or aa[1])
        best = (pp if pp[1] else aa) if it else (pp if pp[0] else aa)
        lst = best[3] if it else best[2]
        src_c = " · ".join(x for x, ok in (("POC", pp[0]), ("ALIŞ ORT.", aa[0]), ("MALİYET↑", kmc)) if ok)
        src_t = " · ".join(x for x, ok in (("POC", pp[1]), ("ALIŞ ORT.", aa[1]), ("MALİYET↑", kmt)) if ok)
        n_ok = sum(1 for x in lst if x[1] == 1); n_all = len(lst)
        ib = c["israr"]

        def first(keys):
            es = [st.ent.get(k) for k in keys if st.ent.get(k)]
            e = min(es, key=lambda x: x[0]) if es else None
            return [_hm(e[0]), e[1], _r(_pct(v["p"], e[1]))] if e else None
        r = {"s": s, "gd": _r(v["gd"]), "p": v["p"], "sen": ("TAVAN ADAYI" if it else "CİDDİ YÜKSELİŞ") + (" · TAVANDA" if v["attv"] else ""), "tvn": int(it),
             "sc": round(n_ok / n_all * 100) if n_all else None, "kay": src_t if it else src_c, "kay_c": src_c, "kay_t": src_t, "ck": lst,
             "ck_c": (pp if pp[0] else aa)[2], "ck_t": (pp if pp[1] else aa)[3],
             "tvd": _r(v["tvd"]), "akt": _r(v["akt"], 1), "a15": _r(v["a15"], 1), "rv": _r(v["rv"]), "sw30": v["sw30"],
             "isr": f"{ib[0]} {ib[1]:.0f}" if ib else "—", "topl": (c["akd"][0] if c["akd"] else "—"),
             "thin": ("EVET" if c["thin"] and c["thin"][0] else ("hayır" if c["thin"] else "—")),
             "poc": _r(st.cp, 4), "ao": _r(st.ao, 4), "tl": round(st.tl), "c_ok": int(bool(pp[0] or aa[0])), "t_ok": int(it),
             "km_c": int(kmc), "km_t": int(kmt), "ent_c": first(("pocc", "aoc")), "ent_t": first(("poct", "aot"))}
        e = r["ent_t"] if it else r["ent_c"]
        if e:
            r["ent"], r["entp"], r["entr"] = e
        return r

    # -------------------------------------------------------------- API --
    def _resolve_day(self, date):
        return self.m._resolve_day(date)

    def _cols(self, fid, w):
        nm = "POC" if fid == F_POC else "Alış ort."
        pre = w in ("ciddi", "tavan")
        if fid == F_CID:
            return [C("s", "Hisse", "sym"), C("gd", "Gün %", "chg"), C("p", "Fiyat", "px"), C("sen", "Senaryo", "sen"),
                    C("sc", "Senaryo skoru", "score"), C("kay", "Kaynak", "txt"), C("ck", "Koşullar ✓/✗", "chk"),
                    C("ent", "Giriş saati", "time"), C("entp", "Giriş fiyatı", "px"), C("entr", "Girişten beri %", "chg"),
                    C("tvd", "Tavana %", "num"), C("akt", "Aktif alış %", "pct"), C("a15", "Son 15 dk aktif %", "pct"),
                    C("rv", "RVOL (zaman ayarlı)", "num"), C("sw30", "Süpürme (30 dk)", "num"), C("isr", "Israrcı kurum", "txt"),
                    C("topl", "AKD yoğunlaşma", "txt"), C("thin", "Tavan satışı inceliyor", "txt"), C("poc", "POC", "px"),
                    C("ao", "Aktif alış ort.", "px"), C("tl", "İşlem ₺", "tl")]
        cols = [C("s", "Hisse", "sym"), C("gd", "Gün %", "chg"), C("p", "Fiyat", "px"), C("sc", "Baskı skoru", "score")]
        if pre:
            cols += [C("ck", "Koşullar ✓/✗", "chk"), C("ent", "Giriş saati", "time"), C("entp", "Giriş fiyatı", "px"),
                     C("entr", "Girişten beri %", "chg")]
        cols += [C("sen", "Senaryo", "sen"), C("ref", nm if fid == F_POC else "Aktif alış ort.", "px"), C("pr", f"Fiyat – {nm} %", "chg"),
                 C("rh", f"{nm} → Yüksek %", "chg"), C("rl", f"{nm} → Düşük %", "chg"), C("rtv", f"{nm} → Tavan %", "chg"),
                 C("rtb", f"{nm} → Taban %", "chg"), C("up", "Yükseltme", "num"), C("dn", "Düşürme", "num"), C("upt", "Son kaymalar", "txt"),
                 C("dst", "Destek teması", "num"), C("dsb", "Destek tepkisi", "num"), C("dsk", "Destek kırıldı", "num"),
                 C("dbt", "Tepki saatleri", "txt"), C("rst", "Direnç teması", "num"), C("rsr", "Direnç reddi", "num"),
                 C("rsk", "Direnç kırıldı", "num"), C("akt", "Aktif alış %", "pct"), C("a15", "Son 15 dk aktif %", "pct"),
                 C("rv", "RVOL (zaman ayarlı)", "num"), C("sw30", "Süpürme (30 dk)", "num"), C("tvd", "Tavana %", "num"),
                 C("r0", "İlk " + nm, "px"), C("tl", "İşlem ₺", "tl")]
        return cols

    def feature(self, fid: str, w=None, q=None, date=None, tok=None) -> dict:
        day, live = self._resolve_day(date)
        W = WIN[fid]
        w = w if w in [x[0] for x in W] else "tum"
        H = _help(fid)
        base = {"fid": fid, "title": TITLES[fid], "short": SHORTS[fid], "desc": H["ne"], "help": H,
                "nt": {F_POC: NT_POC, F_AORT: NT_AORT, F_CID: NT_CID}[fid], "nt2": NT_TVN if fid == F_CID else None,
                "windows": W, "w": w, "day": day, "day_label": _day_label(day) if day else "", "dates": self.m.dates(),
                "live": live, "mode": "canlı" if live else "kayıt", "date_param": date or None}
        if not day:
            return {**base, "cols": self._cols(fid, w), "rows": [], "count": 0, "status": "hata", "note": "Kayıtlı işlem günü bulunamadı."}
        D = self.days.get(day)
        if D is None or not D.ready:
            if D is None and day not in self.want:
                self.want.append(day)
            prog = f" ({D.done}/{D.total} hisse)" if D is not None and D.total else ""
            return {**base, "cols": self._cols(fid, w), "rows": [], "count": 0, "pending": True, "status": "hazırlanıyor",
                    "note": f"{_day_label(day)} işlemleri işlem işlem taranıyor{prog}."}
        qq = (q or "").strip()
        tk = f"{day}|{D.ver}|{w}|{qq}"
        if tok and tok == tk:
            return {"same": True, "tok": tk}
        key = (fid, day, D.ver, w, qq)
        hit = self._cache.get(key)
        if hit:
            return hit
        rows = D.rows[fid]
        if w == "ciddi":
            rows = [r for r in rows if r["c_ok"]]
        elif w == "tavan":
            rows = [r for r in rows if r["t_ok"]]
        elif w == "s60":
            rows = [r for r in rows if (r["sc"] or 0) >= 60]
        elif w == "up":
            rows = [r for r in rows if r["up"] - r["dn"] >= 2]
        elif w == "dest":
            rows = [r for r in rows if r["dsb"] >= 2]
        elif w == "ust":
            rows = [r for r in rows if (r["pr"] or 0) > 0]
        elif w == "1m":
            rows = [r for r in rows if r["tl"] >= 1e6]
        elif w == "10m":
            rows = [r for r in rows if r["tl"] >= 1e7]
        if qq:
            f = _fold(qq)
            rows = [r for r in rows if f in _fold(r["s"])]
        out_rows = []
        for r in rows[:3000]:
            x = {k: v for k, v in r.items() if k not in ("ck_c", "ck_t", "ent_c", "ent_t", "kay_c", "kay_t")}
            if w in ("ciddi", "tavan"):
                pick = "t" if w == "tavan" else "c"
                x["ck"] = r["ck_t"] if pick == "t" else r["ck_c"]
                e = r.get("ent_t" if pick == "t" else "ent_c")
                x["ent"], x["entp"], x["entr"] = e if e else (None, None, None)
                if fid == F_CID:
                    x["kay"] = r["kay_t"] if pick == "t" else r["kay_c"]
            out_rows.append(x)
        n_c = sum(1 for r in D.rows[fid] if r["c_ok"]); n_t = sum(1 for r in D.rows[fid] if r["t_ok"])
        note = (f"{len(rows)} hisse · ≥{_fs(MIN_TL)} ₺ işlem görmüş ve ≥{WARM_N} işlemli hisseler · referans saat {_hms(D.ref)} · "
                f"CİDDİ YÜKSELİŞ {n_c}, TAVAN ADAYI {n_t} hisse. Kayıt 10:00'dan sonra başlayan hisselerde POC/ortalama kısmidir.")
        out = {**base, "cols": self._cols(fid, w), "rows": out_rows, "count": len(rows), "note": note, "status": "tam",
               "ref": _hms(D.ref), "universe": len(D.st), "computed_at": D.computed_at, "updated": D.computed_at, "tok": tk,
               "counts": {"ciddi": n_c, "tavan": n_t}, "sort": "sc"}
        if len(self._cache) > 60:
            self._cache.clear()
        self._cache[key] = out
        return out

    def preset_for(self, day: str):
        """v123 kancası → (sürüm, ciddi set, tavan set, chk)."""
        D = self.days.get(day)
        if D is None or not D.ready:
            return None
        return D.ver, D.sets["c"], D.sets["t"], D.chk

    # ------------------------------------------------------------ detail --
    def detail(self, fid: str, sym: str, date=None) -> dict:
        day, live = self._resolve_day(date)
        sym = (sym or "").upper().strip()
        if not day:
            return {"error": "kayıtlı gün yok"}
        mode, syms, brokers, lock, _ = self.m._src(day)
        e = syms.get(sym)
        if e is None:
            return {"error": f"{sym} için {day} işlem kaydı yok", "sym": sym, "day": day}
        with lock:
            n = len(e.t)
            T = list(e.t[:n]); Pp = list(e.p[:n]); L = list(e.l[:n]); SD = list(e.sd[:n]); B = list(e.b[:n])
            names = list(brokers)
        if any(T[i] > T[i + 1] for i in range(n - 1)):
            idx = sorted(range(n), key=T.__getitem__)
            T, Pp, L, SD, B = ([c[i] for i in idx] for c in (T, Pp, L, SD, B))
        lim = self._limits(day, live).get(sym) or [None, None]
        st = SB(lim[0], lim[1], rec=True)
        D = self.days.get(day)
        if D is not None and sym in D.st:
            st.tv, st.tb = D.st[sym].tv, D.st[sym].tb
        process(st, T, Pp, L, SD, B, ck_fn=_ck_entry)
        _sw_close(st)
        ref = "poc" if fid != F_AORT else "ao"
        R, up, dn, Rx, lt = _ref(st, ref)
        nm = "POC" if ref == "poc" else "Alış ort."
        f4 = (lambda x: _fp(x)) if ref == "poc" else (lambda x: f"{x:.4f}".replace(".", ","))
        evs = []
        for t, a, b in (st.pev if ref == "poc" else st.aev):
            evs.append([t, "up" if b > a else "dn", f"{nm} {'yükseltildi' if b > a else 'düşürüldü'}: {f4(a)} → {f4(b)}", round(b, 4)])
        lab = {"dt": "Destek teması", "db": "DESTEK TEPKİSİ", "dk": "Destek kırıldı", "rt": "Direnç teması", "rr": "Direnç reddi", "rk": "Direnç kırıldı"}
        for t, k, lvl, p in lt.ev:
            evs.append([t, k, f"{lab[k]} · seviye {f4(lvl)} · fiyat {_fp(p)}", round(p, 4)])
        for t, key, p in st.rec["ck"]:
            if key.startswith(ref):
                evs.append([t, "sen", f"SENARYO GİRİŞİ: {'TAVAN ADAYI' if key.endswith('t') else 'CİDDİ YÜKSELİŞ'} · fiyat {_fp(p)}", p])
        for x in st.sw:
            if x[3] >= SW_TL:
                evs.append([x[0], "sw", f"Süpürme: {x[1]} kademe {_fp(x[4])}→{_fp(x[5])} · {_fs(x[2])} lot · {_fs(x[3])} ₺ · {names[x[6]] if x[6] < len(names) else ''}", x[5]])
        evs.sort(key=lambda z: z[0])
        row = None
        ch = (D.chk.get(sym) or {}) if (D is not None and D.ready) else {}
        if D is not None and D.ready:
            for r in D.rows.get(F_AORT if ref == "ao" else F_POC, []):
                if r["s"] == sym:
                    row = {k: v for k, v in r.items() if k not in ("ck_c", "ck_t")}
                    break
        v = _vals(st, st.last_t or 0)
        c_ok, t_ok, cl, tl_ = checks(st, v, ref, ch.get("extra"), st.last_t)
        return {"sym": sym, "fid": fid, "ref": ref, "day": day, "day_label": _day_label(day), "live": live, "mode": mode,
                "px": st.rec["px"], "line": st.rec["poc" if ref == "poc" else "ao"], "events": evs, "row": row, "n_all": n,
                "kpi": {"R": _r(R, 4), "R0": _r(st.cp0 if ref == "poc" else st.ao0, 4), "up": up, "dn": dn, "st": lt.st, "sb": lt.sb, "sk": lt.sk,
                        "rt": lt.rt, "rr": lt.rr, "rk": lt.rk, "hi": st.hi, "lo": st.lo, "tv": st.tv, "tb": st.tb, "pc": st.pc, "last": st.last,
                        "gd": _r(v["gd"]), "akt": _r(v["akt"], 1), "a15": _r(v["a15"], 1), "rv": _r(v["rv"]), "sw30": v["sw30"],
                        "sc": baski(st, v, ref), "c_ok": c_ok, "t_ok": t_ok, "ck_c": cl, "ck_t": tl_,
                        "pr": _r(_pct(st.last, R)), "rh": _r(_pct(st.hi, R)), "rl": _r(_pct(st.lo, R)), "rtv": _r(_pct(st.tv, R)), "rtb": _r(_pct(st.tb, R)),
                        "ent_c": (lambda x: [_hms(x[0]), x[1]] if x else None)(st.ent.get(ref + "c")),
                        "ent_t": (lambda x: [_hms(x[0]), x[1]] if x else None)(st.ent.get(ref + "t"))},
                "rules": {"tol": "max(1 fiyat adımı, %0,1)", "thr": "tol + max(2 fiyat adımı, %0,3)", "brk": "max(2 fiyat adımı, %0,3)", "hold": HOLD}}

    def status(self) -> dict:
        return {"version": VERSION, "loops": self.loops, "errors": self.errors, "last_err": self.last_err, "timing": self.timing,
                "days": {d: {"ready": D.ready, "done": D.done, "total": D.total, "rows": len(D.rows[F_POC]), "mode": D.mode,
                             "ciddi": len(D.sets["c"]), "tavan": len(D.sets["t"]), "ref": _hms(D.ref), "computed_at": D.computed_at}
                         for d, D in list(self.days.items())}, "alerted": len(self.alerted), "alerts_last_hour": len(self.arate)}

    # ------------------------------------------------------------ alerts --
    def _alerts(self, D) -> None:
        if D is None or not D.ready or D.mode != "canlı":
            return
        sec = _sec_now()
        warm = self._warm
        self._warm = False
        if not (CONT_FROM + 300 <= sec <= CONT_TO):
            return
        now = time.time()
        while self.arate and now - self.arate[0] > 3600:
            self.arate.popleft()
        cands = []
        for r in D.rows[F_CID]:
            if r["t_ok"]:
                cands.append((NT_TVN, r, "t"))
            if r["c_ok"]:
                cands.append((NT_CID, r, "c"))
        for fid, nt in ((F_POC, NT_POC), (F_AORT, NT_AORT)):
            for r in D.rows[fid][:300]:
                st = D.st.get(r["s"])
                if st is None:
                    continue
                evs = st.pev if fid == F_POC else st.aev
                lt = st.ltp if fid == F_POC else st.lta
                rec_up = any(e[2] > e[1] and e[0] >= sec - 600 for e in evs)
                rec_b = any(b[1] >= sec - 600 for b in lt.bt)
                if (r["sc"] or 0) >= 75:
                    cands.append((nt, r, "sc"))
                elif rec_up and rec_b:
                    cands.append((nt, r, "ub"))
        sent = 0
        for nt, r, kind in cands:
            key = (D.day, nt, r["s"])           # hisse + tür başına günde bir bildirim
            if key in self.alerted:
                continue
            self.alerted[key] = (now, kind)
            if warm or sent >= 4 or len(self.arate) >= 20:
                continue
            sent += 1
            self.arate.append(now)
            s = r["s"]
            if nt in (NT_POC, NT_AORT):
                nm = "POC" if nt == NT_POC else "Alış ort."
                title = f"📈 {s} {nm} baskısı (skor {r['sc']:.0f})" if kind == "sc" else f"📈 {s} {nm} yükseltildi + destek tepkisi"
                txt = (f"{nm} {_fp(r['ref'])} ₺ · fiyat {_pc(r['pr'], 2)} · {r['up']} yükseltme / {r['dn']} düşürme · "
                       f"{r['dsb']} destek tepkisi · zirveye {_pc(r['rh'], 1)} · gün {_pc(r['gd'], 1)}")
            else:
                ok = sum(1 for x in r["ck"] if x[1] == 1)
                title = f"{'🚀' if nt == NT_TVN else '🟢'} {s} {'TAVAN ADAYI' if nt == NT_TVN else 'CİDDİ YÜKSELİŞ'}"
                txt = (f"Gün {_pc(r['gd'], 1)} · tavana %{abs(r['tvd'] or 0):.1f} · aktif alış %{(r['akt'] or 0):.0f} · RVOL {(r['rv'] or 0):.1f}× · "
                       f"kaynak: {r['kay']} · {ok}/{len(r['ck'])} koşul ✓")
            try:
                if self.hub is not None:
                    self.hub._emit("olay", nt, s, title, txt, {"f": F_CID if nt in (NT_CID, NT_TVN) else nt, "price": r.get("p"), "kind": kind})
            except Exception as ex:
                logger.debug("v124 emit: %s", ex)
        if len(self.alerted) > 20000:
            self.alerted = {k: v for k, v in self.alerted.items() if k[0] == D.day}

    # ======================================================== ÖZET+ ==
    def _events_for(self, sym: str, day: str, live: bool) -> list:
        out = []
        try:
            from app.v120 import _olay_nt, _OLAY_TITLE
        except Exception:
            return out
        if live and self.events is not None and getattr(self.events, "day", None) == day:
            evs = [e for e in list(self.events.events) if e.get("sym") == sym]
        else:
            hit = self._evc.get(day)
            if hit is None:
                hit = {}
                try:
                    from app.live_store import _post_close_noise
                except Exception:
                    _post_close_noise = lambda e: False
                try:
                    with open(EVENTS_DIR / f"{day}.jsonl", "r", encoding="utf-8") as fh:      # salt okunur
                        for ln in fh:
                            try:
                                e = json.loads(ln)
                            except Exception:
                                continue
                            if e.get("sym") and not _post_close_noise(e):
                                hit.setdefault(e["sym"], []).append(e)
                except Exception:
                    pass
                self._evc = {day: hit}
            evs = hit.get(sym, [])
        for e in evs:
            if e.get("initial"):
                continue
            nt = _olay_nt(e)
            if not nt:
                continue
            out.append({"time": e.get("time"), "nt": nt, "title": _OLAY_TITLE.get(nt, "{s}").format(s=sym), "text": e.get("text") or "", "src": "akış"})
        hub = self.hub
        if hub is not None:
            iso = f"{day[:4]}-{day[4:6]}-{day[6:]}"
            with hub.lock:
                hev = [e for e in hub.events if e.get("sym") == sym and not e.get("backfill")]
            for e in hev:
                if time.strftime("%Y-%m-%d", time.localtime(e.get("ts") or 0)) != iso:
                    continue
                if e.get("kind") == "olay" and (e.get("data") or {}).get("src_id"):
                    continue        # akış kaydındaki olayın bildirimi (yukarıda zaten var)
                out.append({"time": e.get("time"), "nt": e.get("nt"), "title": e.get("title"), "text": e.get("text") or "",
                            "src": "bildirim", "cid": e.get("cid")})
        out.sort(key=lambda x: x.get("time") or "")
        return out

    def ozet(self, sym: str, date=None, cid=None) -> dict:
        sym = (sym or "").upper().strip()
        day, live = self._resolve_day(date)
        ck = (sym, day, cid or "")
        hit = self._ozc.get(ck)
        if hit and time.time() - hit[0] < (4 if live else 15):
            return hit[1]
        out = self._ozet(sym, day, live)
        out["bildirim"] = [{k: v for k, v in e.items() if k != "cid"} for e in out.get("bildirim", [])
                           if not e.get("cid") or e.get("cid") == cid]
        if len(self._ozc) > 200:
            self._ozc.clear()
        self._ozc[ck] = (time.time(), out)
        return out

    def _ozet(self, sym: str, day, live: bool) -> dict:
        res = {"sym": sym, "day": day, "day_label": _day_label(day) if day else "", "live": live, "version": VERSION,
               "ts": time.strftime("%H:%M:%S")}
        if not day:
            res["error"] = "kayıtlı gün yok"
            return res
        D = self.days.get(day)
        if D is None and day not in self.want:
            self.want.append(day)
        st = D.st.get(sym) if D is not None else None
        try:
            mode, syms, brokers, lock, _ = self.m._src(day)
        except Exception:
            syms, brokers, lock = {}, [""], threading.RLock()
        e = syms.get(sym)
        names = list(brokers)
        q = (getattr(self.feed, "quotes", {}) or {}).get(sym) or {}
        last_sess = live or day == _last_disk_day(_today())
        last = (st.last if st else None) or (q.get("last") if last_sess else None)
        res["last"] = last
        res["pending"] = D is None or not D.ready
        # ---- 1) Israrcı kurum (v1.23 Maliyet Yükselten Kurumlar)
        try:
            R = self.m.days.get(day)
            rr = [r for r in (R.rows if R is not None and R.ready else []) if r["s"] == sym]
            rr.sort(key=lambda r: (-r.get("israr", 0), -r["btl"]))

            def km(r):
                return {"br": r["br"], "ft": r["ft"], "fp": r["fp"], "cur": r["cur"], "chg": r["chg"], "still": r["still"], "sc": r["sc"],
                        "israr": r.get("israr"), "btl": r["btl"], "akt": r["akt"], "ys": r["ys"], "dk": r.get("dk"), "span": r.get("span"),
                        "dist": _r(_pct(last, r["cur"])), "dr": r.get("dr"), "yy": r.get("yy")}
            res["israr"] = {"top": km(rr[0]) if rr else None, "top3": [km(r) for r in rr[:3]], "n": len(rr),
                            "ready": bool(R is not None and R.ready)}
        except Exception as ex:
            res["israr"] = {"error": str(ex)[:120]}
        # ---- 2) Kurum yoğunlaşması (AKD)
        try:
            akd = None
            f = self.feed
            if f is not None and f._akd_date() == day:
                v = f.akd_view(sym, day, day)
                if v and (v.get("buyers") or v.get("sellers")):
                    tum = [{"broker": b["broker"], "value": b["net_lot"]} for b in v["buyers"]] + \
                          [{"broker": b["broker"], "value": b["net_lot"]} for b in v["sellers"]]
                    akd = (tum, "İdealData AKD · AKD sekmesi (Günlük) ile aynı")
            if akd is None:
                d = json.loads((TRADES_DIR.parent / "akd" / day / f"{sym}.json").read_text(encoding="utf-8"))
                akd = (d.get("TUM") or [], "kayıtlı gün sonu AKD")
            c = conc(akd[0])
            res["akd"] = {"label": c[0], "desc": c[4], "top3": c[1], "nb": c[2], "ns": c[3], "top3s": c[5], "src": akd[1],
                          "buyers": c[6], "sellers": c[7]}
        except Exception as ex:
            res["akd"] = {"error": "AKD verisi yok"}
        # ---- 3) Son 5 dk nabız
        try:
            if e is not None:
                with lock:
                    n = len(e.t)
                    T = e.t
                    # sürekli işlem: kapanış seansı (18:00–18:10 tek fiyat) eşleşmesi aktif/pasif yön taşımadığından hariç
                    ref = min(_sec_now(), CONT_TO) if live else min(T[n - 1] if n else 0, CONT_TO)
                    j0 = bisect.bisect_left(T, ref - 300, 0, n) if n else 0
                    W = [(T[i], e.p[i], e.l[i], e.sd[i]) for i in range(j0, bisect.bisect_right(T, ref, 0, n))]
                    tl_day = st.tl if st else sum(e.p[i] * e.l[i] for i in range(n))
                    big_th = max(250_000.0, 10 * tl_day / max(1, n))
                    lb = None
                    jr = bisect.bisect_right(T, ref, 0, n)
                    for i in range(jr - 1, max(-1, jr - 300000), -1):
                        if e.sd[i] == 1 and e.p[i] * e.l[i] >= big_th:
                            lb = (T[i], e.p[i], e.l[i], e.b[i], e.s[i])
                            break
                    t_first = T[bisect.bisect_left(T, CONT_FROM, 0, n)] if n and T[n - 1] >= CONT_FROM else CONT_FROM
                al = sum(x[2] for x in W if x[3] == 1); sl = sum(x[2] for x in W if x[3] == 2)
                tl5 = sum(x[1] * x[2] for x in W)
                mins_day = max(1.0, (min(ref, CONT_TO) - max(CONT_FROM, t_first)) / 60)
                rate_day = n / mins_day; tlm_day = tl_day / mins_day
                lsw = None
                if st and st.sw:
                    xs = [y for y in st.sw if y[3] >= SW_TL]
                    if xs:
                        x = xs[-1]
                        lsw = {"t": _hms(x[0]), "nlev": x[1], "lot": x[2], "tl": x[3], "p0": x[4], "p1": x[5],
                               "br": names[x[6]] if x[6] < len(names) else "", "in5": x[0] >= ref - 300,
                               "n5": sum(1 for y in xs if y[0] >= ref - 300)}
                aday = (st.alot / (st.alot + st.slot) * 100) if st and (st.alot + st.slot) else None
                res["nabiz"] = {"ref": _hms(ref), "from": _hms(ref - 300), "n": len(W), "tpm": round(len(W) / 5, 1), "tl": round(tl5),
                                "pmin": min(x[1] for x in W) if W else None, "pmax": max(x[1] for x in W) if W else None,   # v1.26.2 kilit tespiti
                                "lot": sum(x[2] for x in W), "akt": _r(al / (al + sl) * 100, 1) if (al + sl) else None,
                                "akt_day": _r(aday, 1), "rate_day": round(rate_day, 1), "tlm_day": round(tlm_day),
                                "speed": _r((len(W) / 5) / rate_day, 2) if rate_day else None,
                                "tl_x": _r((tl5 / 5) / tlm_day, 2) if tlm_day else None, "big_th": round(big_th),
                                "big": ({"t": _hms(lb[0]), "p": lb[1], "lot": lb[2], "tl": round(lb[1] * lb[2]),
                                         "br": names[lb[3]] if lb[3] < len(names) else "", "sel": names[lb[4]] if lb[4] < len(names) else "",
                                         "in5": lb[0] >= ref - 300} if lb else None), "sweep": lsw,
                                "label": ("CANLI · son 5 dk" if _sec_now() < CONT_TO else f"bugünkü sürekli işlemlerin son 5 dakikası ({_hm(ref - 300)}–{_hm(ref)})") if live
                                else f"{_day_label(day)} sürekli işlemlerinin son 5 dakikası ({_hm(ref - 300)}–{_hm(ref)}, kapanış seansı hariç)"}
            else:
                res["nabiz"] = {"error": "bu gün için işlem kaydı yok"}
        except Exception as ex:
            res["nabiz"] = {"error": str(ex)[:120]}
        # ---- 4) Kademe dengesi
        try:
            d = (getattr(self.feed, "depth", {}) or {}).get(sym) or {}
            asks = sorted(((v["price"], v["lot"]) for v in (d.get("asks") or {}).values() if v.get("lot")), key=lambda x: x[0])
            bids = sorted(((v["price"], v["lot"]) for v in (d.get("bids") or {}).values() if v.get("lot")), key=lambda x: -x[0])
            if (asks or bids) and last_sess:
                b5 = sum(l for _, l in bids[:5]); a5 = sum(l for _, l in asks[:5])
                cand = [(l, p, "SATIŞ") for p, l in asks[:10]] + [(l, p, "ALIŞ") for p, l in bids[:10]]
                wl = max(cand) if cand else None
                melt = None
                K = (getattr(self.k, "d", {}) or {}).get(sym) if self.k is not None else None
                if K is not None:
                    ws = []
                    for p, w in list(K.walls.items()):
                        if w.get("peak") and (w.get("cur", 0) <= 0.7 * w["peak"] or w.get("gone")):
                            ws.append((w.get("t") or 0, p, w))
                    if ws:
                        t_, p_, w_ = max(ws, key=lambda z: z[0])
                        tuk = (w_.get("fill") or 0) / w_["peak"] * 100 if w_["peak"] else 0
                        melt = {"p": p_, "peak": w_["peak"], "cur": w_.get("cur"), "fill": round(w_.get("fill") or 0), "canc": round(w_.get("canc") or 0),
                                "st": w_.get("st") if w_.get("gone") else ("ERİYOR (aktif alışla)" if tuk >= 30 else "İPTALLE KÜÇÜLÜYOR"),
                                "t": _hms(t_), "tuk": round(tuk, 1)}
                res["kademe"] = {"b5": b5, "a5": a5, "ratio": _r(b5 / a5, 2) if a5 else None,
                                 "wall": {"p": wl[1], "lot": wl[0], "side": wl[2], "tl": round(wl[0] * wl[1])} if wl else None,
                                 "melt": melt, "bb": bids[0][0] if bids else None, "ba": asks[0][0] if asks else None,
                                 "label": "CANLI derinlik" if live else "son seans kapanış defteri (İdealData'nın son görüntüsü)"}
            else:
                res["kademe"] = {"error": "derinlik verisi yok" if last_sess else "geçmiş gün için derinlik kaydı yok"}
        except Exception as ex:
            res["kademe"] = {"error": str(ex)[:120]}
        # ---- 5) Konum
        kon = {}
        try:
            if st is not None and st.vol:
                poc, vah, val = value_area(st.vol)
                vw = st.tl / st.lot if st.lot else None
                tv, tb = st.tv, st.tb
                p = last
                kon = {"poc": poc, "vah": vah, "val": val, "vwap": _r(vw, 4), "aof": q.get("vwap") if last_sess else None,
                       "hi": st.hi, "lo": st.lo, "tv": tv, "tb": tb, "pc": st.pc,
                       "d_poc": _r(_pct(p, poc)), "d_vah": _r(_pct(p, vah)), "d_val": _r(_pct(p, val)), "d_vwap": _r(_pct(p, vw)),
                       "d_hi": _r(_pct(st.hi, p)), "d_tv": _r(_pct(tv, p)), "d_tb": _r(_pct(tb, p))}
                d = (getattr(self.feed, "depth", {}) or {}).get(sym) or {}
                if tv and last_sess:
                    for v in (d.get("bids") or {}).values():
                        if abs((v.get("price") or 0) - tv) < 1e-6:
                            kon["tv_bid"] = v.get("lot")
                    for v in (d.get("asks") or {}).values():
                        if abs((v.get("price") or 0) - tv) < 1e-6:
                            kon["tv_ask"] = v.get("lot")
                if tb and last_sess:                       # v1.26.2 taban kademesindeki lotlar
                    for v in (d.get("asks") or {}).values():
                        if abs((v.get("price") or 0) - tb) < 1e-6:
                            kon["tb_ask"] = v.get("lot")
                    for v in (d.get("bids") or {}).values():
                        if abs((v.get("price") or 0) - tb) < 1e-6:
                            kon["tb_bid"] = v.get("lot")
                kon["at_tv"] = bool(p and tv and p >= tv - EPS)
                kon["at_tb"] = bool(p and tb and p <= tb + EPS)
                nbz = res.get("nabiz") or {}
                if nbz.get("n") and nbz.get("pmin") is not None:   # son 5 dk işlemlerinin TAMAMI tavan / taban fiyatından → kilit
                    if tv and nbz["pmin"] >= tv - EPS:
                        nbz["lock"] = "tavan"; nbz["lock_p"] = tv
                    elif tb and nbz["pmax"] <= tb + EPS:
                        nbz["lock"] = "taban"; nbz["lock_p"] = tb
                vv = _vals(st, st.last_t or 0)
                kon["poc_line"] = {"R": _r(st.cp, 4), "up": st.pup, "dn": st.pdn, "sb": st.ltp.sb, "sk": st.ltp.sk, "sc": baski(st, vv, "poc")}
                kon["ao_line"] = {"R": _r(st.ao, 4), "up": st.aup, "dn": st.adn, "sb": st.lta.sb, "sk": st.lta.sk, "sc": baski(st, vv, "ao")}
            res["konum"] = kon or {"error": "işlem kaydı yok" if D is not None and D.ready else "hesaplanıyor"}
        except Exception as ex:
            res["konum"] = {"error": str(ex)[:120]}
        # ---- 6) Operasyon skoru + aktif sinyaller
        try:
            chips = []
            ops = None
            if self.op is not None:
                o = self.op.stock(sym)
                ops = {"score": o.get("score"), "computed_at": o.get("computed_at"), "n": len(o.get("parts") or [])}
                for f_ in o.get("features") or []:
                    if f_.get("fid") in (29, 30):
                        continue
                    if (f_.get("st") or 0) > 0:
                        chips.append({"id": f"op_{f_['fid']}", "l": f_.get("title"), "sc": f_.get("st"), "g": "op", "strong": (f_.get("st") or 0) >= 60})
            res["op"] = ops
            kday = getattr(self.k, "day", None)
            kres = getattr(self.k, "res", {}) or {}
            if kday == day:
                from app.v122 import CAT
                for fid_, out in list(kres.items()):
                    if fid_ in ("k_islem", "k_kurumfiyat") or not out:
                        continue
                    rows = out.get("rows") or []
                    for i, r in enumerate(rows):
                        if r.get("s") == sym:
                            chips.append({"id": fid_, "l": CAT[fid_][0], "sc": r.get("sc"), "rank": i + 1, "of": len(rows), "g": "k",
                                          "strong": (r.get("sc") or 0) >= 70})
                            break
            isr = res.get("israr") or {}
            if isr.get("n"):
                t0 = isr["top"]
                best = max(isr["top3"], key=lambda z: z["sc"])
                chips.append({"id": "k_maliyet", "l": "Maliyet Yükselten Kurumlar", "sc": best["sc"], "g": "km", "strong": best["sc"] >= 70,
                              "txt": f"{isr['n']} kurum"})
                if (t0.get("israr") or 0) >= 70:
                    chips.append({"id": "k_maliyet", "w": "israr", "l": "Israrcı kurum", "sc": t0["israr"], "g": "km", "strong": True, "txt": t0["br"]})
            if D is not None and D.ready:
                for fid_, nm in ((F_POC, "POC Baskısı"), (F_AORT, "Alış Ortalama Baskısı")):
                    for i, r in enumerate(D.rows[fid_]):
                        if r["s"] == sym:
                            chips.append({"id": fid_, "l": nm, "sc": r["sc"], "rank": i + 1, "of": len(D.rows[fid_]), "g": "b", "strong": (r["sc"] or 0) >= 60})
                            break
                if sym in D.sets["t"]:
                    chips.append({"id": F_CID, "w": "tavan", "l": "TAVAN ADAYI", "g": "sen", "strong": True})
                if sym in D.sets["c"]:
                    chips.append({"id": F_CID, "w": "ciddi", "l": "CİDDİ YÜKSELİŞ", "g": "sen", "strong": True})
                c = D.chk.get(sym)
                if c:
                    pp, aa = c["per"]["poc"], c["per"]["ao"]
                    res["senaryo"] = {"c": bool(sym in D.sets["c"]), "t": bool(sym in D.sets["t"]),
                                      "ck_c": (pp if pp[0] or not aa[0] else aa)[2], "ck_t": (pp if pp[1] or not aa[1] else aa)[3]}
            if last and kon.get("tv") and (live or last_sess):   # v1.26.2: son seans (hafta sonu) da
                if last >= kon["tv"] - EPS:
                    chips.append({"id": "tavanda", "l": "Tavandaki Hisseler", "g": "tt", "strong": True})
                elif (_pct(kon["tv"], last) or 99) <= 3:
                    chips.append({"id": "radar_tavan", "l": "Tavana Yakın Hisseler", "g": "tt"})
            if last and kon.get("tb") and (live or last_sess):   # v1.26.2 taban çipleri
                if last <= kon["tb"] + EPS:
                    chips.append({"id": "tabanda", "l": "Tabandaki Hisseler", "g": "tt", "strong": True})
                elif (_pct(last, kon["tb"]) or 99) <= 3:
                    chips.append({"id": "radar_taban", "l": "Tabana Yakın Hisseler", "g": "tt"})
            chips.sort(key=lambda c: (not c.get("strong"), -(c.get("sc") or 0)))
            res["chips"] = chips
            res["chips_note"] = None if kday == day else f"Kademe & Şerit tarayıcıları {_day_label(kday)} gününü gösteriyor."
        except Exception as ex:
            res["chips"] = res.get("chips") or []
            res["chips_err"] = str(ex)[:120]
        # ---- 7) Bildirimler
        try:
            res["bildirim"] = self._events_for(sym, day, live)
        except Exception as ex:
            res["bildirim"] = []
            res["bildirim_err"] = str(ex)[:120]
        try:
            res["yorum"] = yorum(res)
        except Exception as ex:
            res["yorum"] = ""
            res["yorum_err"] = str(ex)[:120]
        return res


def conc(tum: list):
    """AKD net dağılımı → (etiket, ilk3 alıcı payı %, alıcı n, satıcı n, açıklama, ilk3 satıcı payı %, ilk3 alıcı, ilk3 satıcı)."""
    b = sorted([(x["broker"], x["value"]) for x in tum if x.get("value") and x["value"] > 0], key=lambda z: -z[1])
    s = sorted([(x["broker"], -x["value"]) for x in tum if x.get("value") and x["value"] < 0], key=lambda z: -z[1])
    tb = sum(v for _, v in b); ts = sum(v for _, v in s)
    t3 = sum(v for _, v in b[:3]) / tb * 100 if tb else None
    s3 = sum(v for _, v in s[:3]) / ts * 100 if ts else None
    nb, ns = len(b), len(s)
    if nb and ns and nb <= 0.7 * ns and (t3 or 0) >= 60:
        lab, ds = "TOPLAMA", "az kurum alıyor, çok kurum satıyor"
    elif nb and ns and ns <= 0.7 * nb and (s3 or 0) >= 60:
        lab, ds = "DAĞITIM", "çok kurum alıyor, az kurum satıyor"
    else:
        lab, ds = "DENGELİ", "alıcı/satıcı kurum dağılımı dengeli"
    return (lab, _r(t3, 1), nb, ns, ds, _r(s3, 1), [[n, v] for n, v in b[:3]], [[n, v] for n, v in s[:3]])


def value_area(vol: dict, pct=0.70):
    """POC + %70 değer alanı (POC'tan başlayıp hacmi büyük olan komşu fiyata doğru genişler)."""
    if not vol:
        return None, None, None
    ps = sorted(vol)
    tot = sum(vol.values())
    i = max(range(len(ps)), key=lambda k: vol[ps[k]])
    lo = hi = i
    acc = vol[ps[i]]
    while acc < tot * pct and (lo > 0 or hi < len(ps) - 1):
        up = vol[ps[hi + 1]] if hi < len(ps) - 1 else -1
        dn = vol[ps[lo - 1]] if lo > 0 else -1
        if up >= dn:
            hi += 1; acc += up
        else:
            lo -= 1; acc += dn
    return ps[i], ps[hi], ps[lo]


def _tr(v, d=1):
    if v is None:
        return "—"
    return f"{abs(v):.{d}f}".replace(".", ",")


def _ek(n) -> str:
    """Türkçe yüzde/sayı eki: %64'ü, %70'i, %78'i, %100'ü ..."""
    try:
        x = int(round(abs(float(n))))
    except Exception:
        return "'i"
    if x == 0:
        return "'ı"
    last = x % 10
    if last == 0:
        tens = (x // 10) % 10
        if x % 100 == 0:
            return "'ü"
        return {1: "'u", 2: "'si", 3: "'u", 4: "'ı", 5: "'i", 6: "'ı", 7: "'i", 8: "'i", 9: "'u"}.get(tens, "'i")
    return {1: "'i", 2: "'si", 3: "'ü", 4: "'ü", 5: "'i", 6: "'sı", 7: "'si", 8: "'i", 9: "'u"}[last]


def _abl(hms) -> str:
    """'10:01' → "10:01'den", '10:00' → "10:00'dan", '10:40' → "10:40'tan" (Türkçe ayrılma hâli, okunuşa göre)."""
    t = str(hms or "")[:5]
    try:
        h, m = int(t[:2]), int(t[3:5])
    except Exception:
        return t + "'den"
    n = m if m else h
    u = n % 10
    if u:
        suf = {1: "den", 2: "den", 3: "ten", 4: "ten", 5: "ten", 6: "dan", 7: "den", 8: "den", 9: "dan"}[u]
    else:
        suf = {0: "dan", 1: "dan", 2: "den", 3: "dan", 4: "tan", 5: "den"}.get((n // 10) % 10, "den")
    return f"{t}'{suf}"


def yorum(o: dict) -> str:
    """1-3 cümlelik Türkçe özet — yalnız gerçek sayılar, verisi olmayan parça atlanır."""
    parts = []
    isr = (o.get("israr") or {}).get("top")
    if isr and isr.get("chg") is not None:
        still = isr.get("still") not in (None, "—")
        if isr["chg"] > 0:
            parts.append(f"{isr['br']} {_abl(isr['ft'])} beri maliyetini %{_tr(isr['chg'])} artırarak {'topluyor' if still else 'topladı'}"
                         + (f" (Israr {isr['israr']:.0f})" if isr.get("israr") is not None else ""))
        else:
            parts.append(f"{isr['br']} {_abl(isr['ft'])} beri net alıcı" + (f" (Israr {isr['israr']:.0f})" if isr.get("israr") is not None else ""))
    a = o.get("akd") or {}
    if a.get("top3") is not None:
        if a.get("label") == "DAĞITIM" and a.get("top3s") is not None:
            parts.append(f"AKD'de DAĞITIM görünümü: {a['nb']} alıcıya karşı {a['ns']} satıcı kurum, ilk 3 satıcının net satıştaki payı %{_tr(a['top3s'], 0)}")
        elif a.get("label") == "TOPLAMA":
            parts.append(f"AKD'de TOPLAMA görünümü: {a['ns']} satıcıya karşı {a['nb']} alıcı kurum, ilk 3 alıcının net alımdaki payı %{_tr(a['top3'], 0)}")
        else:
            parts.append(f"AKD dengeli: ilk 3 alıcının net alımdaki payı %{_tr(a['top3'], 0)} ({a['nb']} alıcı / {a['ns']} satıcı kurum)")
    nb = o.get("nabiz") or {}
    k = o.get("konum") or {}
    lk = nb.get("lock")
    if lk and nb.get("akt") is not None:
        # v1.26.2 — son 5 dk'nın tüm işlemleri tavan/taban fiyatından: aktif % kuyruğun yönünü gösterir, momentum değildir
        liq = f"{'düşük likidite: ' if nb['n'] < 50 else ''}{nb['n']} işlem, {_fs(nb.get('lot') or 0)} lot"
        ak = nb["akt"]
        if lk == "taban":
            what = ("bekleyen satış kuyruğundan alım, yükseliş sinyali değil" if ak >= 50
                    else "taban alış kuyruğuna satış")
            parts.append(f"son 5 dk işlemlerin tamamı taban fiyatından ({_fp(nb['lock_p'])}): aktif alış %{_tr(ak, 0)} = {what} (taban kilidi, {liq})")
        else:
            what = ("tavanda bekleyen satışların toplanması" if ak >= 50
                    else "tavanda bekleyen alış kuyruğuna satış, düşüş sinyali değil")
            parts.append(f"son 5 dk işlemlerin tamamı tavan fiyatından ({_fp(nb['lock_p'])}): aktif alış %{_tr(ak, 0)} = {what} (tavan kilidi, {liq})")
    elif nb.get("akt") is not None:
        x = f"son 5 dk aktif alış %{_tr(nb['akt'], 0)}"
        if nb.get("speed"):
            x += f" (hız {_tr(nb['speed'])}× gün ortalaması)"
        parts.append(x)
    if k.get("at_tb"):
        parts.append("fiyat TABANDA (taban kilidi" + (f"; {_fs(k['tb_ask'])} lot taban satışta bekliyor" if k.get("tb_ask") else "") + ")")
    elif k.get("d_tv") is not None:
        if k["d_tv"] <= 0.001:
            parts.append("fiyat tavanda" + (f" ({_fs(k['tv_bid'])} lot tavan alışta bekliyor)" if k.get("tv_bid") else ""))
        else:
            # v1.26.2 yön: fiyat tabana tavandan daha yakınsa (önceki kapanışın altında) tabana mesafe yazılır
            if k.get("d_tb") is not None and abs(k["d_tb"]) < k["d_tv"]:
                parts.append(f"tabana %{_tr(abs(k['d_tb']))} var")
            else:
                parts.append(f"tavana %{_tr(k['d_tv'])} var")
    out = []
    s1 = ", ".join(parts[:2]); s2 = ", ".join(parts[2:])
    for s in (s1, s2):
        if s:
            out.append(s[0].upper() + s[1:] + ".")
    pl = k.get("poc_line") or {}
    sen = o.get("senaryo") or {}
    ex = []
    if pl.get("R"):
        ex.append(f"POC {_fp(pl['R'])} ₺ ({pl['up']} kez yükseltildi, {pl['sb']} destek tepkisi)")
    if sen.get("t"):
        ex.append("hazır senaryo: TAVAN ADAYI")
    elif sen.get("c"):
        ex.append("hazır senaryo: CİDDİ YÜKSELİŞ")
    if ex:
        out.append("; ".join(ex) + ".")
    return " ".join(out[:3])


b_engine = BaskiEngine()
