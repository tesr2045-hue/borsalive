"""v1.26.0 — SEANS İŞLEM AKIŞI ANALİZİ · AKD K/Z + AKD ANALİZİ · AKD TARAMASI (tüm hisseler) + akd_tarama bildirimi.

* Akış (flow): gerçek işlem kaydından (data/trades / canlı store; v1.23 m_engine._src ile aynı kaynak) aktif alış / aktif
  satış lot-₺-%, 15/30/60 dk pencereler, agresif emir (aynı saniye + aynı taraf + aynı agresör kurum ardışık baskılar)
  büyüklük sınıfları (eşikler hissenin gün cirosuna göre), süpürmeler (≥2 fiyat kademesi), duvar süpürme (derinlik kaydı
  varsa v1.25 duvar kaydı; yoksa VEKİL: aynı fiyatta art arda aktif alışla eriyen büyük satış kademesi), fiyat etkisi.
* AKD+ : AKD sekmesiyle AYNI kaynak (ideal_feed.akd_view) → kurum başına açık K/Z (net lot × (son − maliyet)), gün içi
  gerçekleşen K/Z (işlem kaydından alış/satış ortalamaları), özet ve AKD ANALİZİ yorumu (yoğunlaşma, toplama/dağıtım,
  ısrarcı kurumlar, kapana kısılanlar).
* AKD Taraması: günlük AKD deposu (ideal_feed.broker_positions — AKD sekmesi Günlük ve Kurum Analizi ile aynı kayıt);
  geçmiş gün için data/akd/<gün>/*.json aynı _akd_compose ile. İstemci filtreler; sunucu kompakt tablo verir.
* Bildirim (akd_tarama): kullanıcının kaydettiği kurallar (kurum(lar) + min net % + min net ₺ + taraf) seans içinde
  ~60 sn'de bir kontrol edilir; kural kaydedildiği andaki eşleşmeler taban kabul edilir (yalnız YENİ girişler bildirilir);
  hisse+kurum+kural başına günde 1, saatte en çok 30, döngü başına en çok 5.
* v1.26.1 — AKD Taraması'na kurum başına AKTİF ALIŞ % (aktif alış lotu ÷ tüm alış lotu, v1.23 Maliyet Yükselten "Aktif alış %"
  ile birebir aynı tanım ve aynı işlem kaynağı), ₺ bazında aktif alış % ve AKTİF SATIŞ % (aktif satış lotu ÷ tüm satış lotu).
  Ayrıca aktif alış lot / ₺ ve aktif satış lot / ₺ (işlem kaydından, tüm kurumlar — net satıcılar dahil).
  O günün işlem kaydı yoksa / kurumun o hissede işlem kaydı yoksa None ("—"). Bildirim kuralına isteğe bağlı min aktif alış %.
* v1.26.2 — tarama satırlarına işlem kaydı alış lot/₺ (tbl/tbtl → Aktif İşlem Taraması (KURUM) ağırlıklı aktif %'si: Σabtl÷Σtbtl);
  AKD sekmesi K/Z tablosuna aktif alış %/lot (AKD Taraması ile aynı _aktif kaynağı), EN ÇOK AKTİF ALAN KURUMLAR, TAHTACI SİNYALİ
  (AKD'de en çok net alan = en çok aktif alan → "yukarı sürüyor olabilir"; tersi "aşağı bastırıyor olabilir"; güçlü/orta);
  aktif_kurum bildirimi (kullanıcı ayarı, varsayılan KAPALI: kurum bir hissede eşik ₺ üstü, eşik aktif alış % üstü aldı).
* v1.26.3 — TAVAN TRENİ: tarama satırlarına AKD sırası (rb = net alıcılar içinde sıra "Alış #k", rs = net satıcılar içinde
  "Satış #k", wb = AKD alış lotuna göre sıra = balina) ve tt (0 yok / 1 ORTA / 2 GÜÇLÜ). Koşullar (hepsi): AKD Alış #1 ya da
  hissedeki en büyük alıcı (alış lotu) · net payı (AKD DAĞILIM %) ≥ %30 · aktif alış % ≥ %65 · aktif alış ≥ 5 Mn ₺;
  GÜÇLÜ = Alış #1 + aktif alış ≥ 10 Mn ₺. Aynı sinyal AKD ANALİZİ / Özet'te TAHTACI SİNYALİ ile birleşik; tavan_treni bildirimi
  (varsayılan KAPALI). Eşikler 02.10.2026 verisiyle ayarlandı (bkz. TRN_P).
"""
from __future__ import annotations

import bisect
import collections
import json
import logging
import os
import statistics
import threading
import time
from pathlib import Path

from app.v122 import CONT_FROM, CONT_TO, _day_label, _fp, _fs, _hms, _sec_now, _tick_size, _today

logger = logging.getLogger("v126")

VERSION = "1.26.3"
NT_AKDT = "akd_tarama"
NT_AKK = "aktif_kurum"          # v1.26.2
NT_TRN = "tavan_treni"         # v1.26.3
NT_DEFAULTS = {NT_AKDT: "notify", NT_AKK: "notify", NT_TRN: "notify"}
TRN_P = {"np": 30.0, "aa": 65.0, "tl": 5e6, "tl_g": 10e6}   # v1.26.3 TAVAN TRENİ eşikleri (02.10.2026 verisiyle ayarlı)
BASE = Path(__file__).resolve().parent.parent / "data"
AKD_DIR = BASE / "akd"
TR_DIR = BASE / "trades"
VDIR = BASE / "v126"
WATCH_FILE = VDIR / "akd_watch.json"
AKK_FILE = VDIR / "akk_watch.json"       # v1.26.2 aktif_kurum bildirim ayarı
TRN_FILE = VDIR / "trn_watch.json"       # v1.26.3 tavan_treni bildirim ayarı
EPS = 1e-9


def _r(v, d=2):
    return None if v is None else round(v, d)


def _pc(a, b):
    try:
        return (a / b - 1) * 100.0 if a and b else None
    except Exception:
        return None


def _f1(v):
    return "—" if v is None else f"{v:.1f}".replace(".", ",")


def _f2(v):
    return "—" if v is None else f"{v:.2f}".replace(".", ",")


_BRF = [(r"\bIs\b", "İş"), (r"Yatirim", "Yatırım"), (r"Yapi", "Yapı"), (r"Vakif", "Vakıf"), (r"Osmanli", "Osmanlı"), (r"\bUnlu\b", "Ünlü"),
        (r"Seker", "Şeker"), (r"Bankasi", "Bankası"), (r"Yabanci", "Yabancı"), (r"Fonlari", "Fonları"), (r"Turk\b", "Türk"), (r"Doga", "Doğa")]


def _bn(n):
    import re as _re
    s = str(n or "")
    for a, b in _BRF:
        s = _re.sub(a, b, s)
    return s


_EK1 = {"1": "i", "2": "si", "3": "ü", "4": "ü", "5": "i", "6": "sı", "7": "si", "8": "i", "9": "u"}
_EK10 = {"1": "u", "2": "si", "3": "u", "4": "ı", "5": "si", "6": "ı", "7": "i", "8": "i", "9": "ı"}
_ACC = {"i": "ini", "si": "sini", "ü": "ünü", "u": "unu", "ı": "ını", "sı": "sını"}


def _pe(v, acc=False):
    """'%62,5'i' gibi yüzde + iyelik eki (acc=True → belirtme: '%62,5'ini')."""
    if v is None:
        return "%—"
    t = f"{v:.1f}".replace(".", ",")
    if t.endswith(",0"):
        t = t[:-2]
    num = t.replace(",", "")
    d = t.split(",")[-1] if "," in t else t
    if d.endswith("00"):
        ek = "ü"
    elif d[-1] != "0":
        ek = _EK1[d[-1]]
    elif len(d) >= 2:
        ek = _EK10[d[-2]]
    else:
        ek = "ı"   # sıfır
    return f"%{t}'{_ACC[ek] if acc else ek}"


def _fpct(v, sign=True):
    if v is None:
        return "—"
    s = f"{abs(v):.1f}".replace(".", ",")
    return ("+" if v > 0 and sign else "−" if v < 0 else "") + "%" + s


class V126:
    def __init__(self):
        self.feed = self.m = self.b = self.d = self.hub = None
        self.lock = threading.RLock()
        self.fcache = {}
        self.pcache = {}
        self.tcache = {}
        self.acache = {}            # v1.26.1 — gün → {"sid", "st": {sym: [ptr, merges, {bi: [bl, abl, btl, abtl, sl, asl, stl, astl]}]}}
        self.alock = threading.Lock()
        self.atime = {}
        self.watch = {"rules": [], "seen": {}, "day": None}
        self.akk = {"on": False, "min_tl": 5e6, "min_aa": 85.0, "net": True, "brokers": [], "seen": {}, "day": None}   # v1.26.2
        self.akrate = collections.deque()
        self.akk_emitted = 0
        self.thcache = {}
        self.trn = {"on": False, "grade": 2, "seen": {}, "day": None}   # v1.26.3 (grade 2 = yalnız GÜÇLÜ, 1 = GÜÇLÜ + ORTA)
        self.trrate = collections.deque()
        self.trn_emitted = 0
        self.wrate = collections.deque()
        self.emitted = 0
        self.loops = 0
        self.last_err = None
        self.thread = None

    # ------------------------------------------------------------------ start
    def start(self, feed, m_engine, b_engine, d_engine, hub):
        self.feed, self.m, self.b, self.d, self.hub = feed, m_engine, b_engine, d_engine, hub
        VDIR.mkdir(parents=True, exist_ok=True)
        try:
            self.watch.update(json.loads(WATCH_FILE.read_text()))
        except Exception:
            pass
        try:
            self.akk.update(json.loads(AKK_FILE.read_text()))
        except Exception:
            pass
        try:
            self.trn.update(json.loads(TRN_FILE.read_text()))
        except Exception:
            pass
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name="v126-akdwatch", daemon=True)
            self.thread.start()
        logger.info("v126: akış + AKD K/Z + AKD taraması başladı")

    # ---------------------------------------------------------------- trades
    def _trades(self, sym, date):
        day, live = self.m._resolve_day(date)
        if not day:
            return None, None, False, [], None
        try:
            mode, syms, brokers, lock, _ = self.m._src(day)
        except Exception:
            return day, None, live, [], None
        e = syms.get(sym)
        if e is None:
            return day, None, live, list(brokers), None
        with lock:
            n = len(e.t)
            A = (list(e.t[:n]), list(e.p[:n]), list(e.l[:n]), list(e.sd[:n]), list(e.b[:n]), list(e.s[:n]))
        return day, A, live, list(brokers), mode

    # ================================================================== FLOW
    def flow(self, sym, date=None, brief=False):
        sym = (sym or "").upper().strip()
        day, A, live, names, mode = self._trades(sym, date)
        n = len(A[0]) if A else 0
        ck = (sym, day)
        hit = self.fcache.get(ck)
        if hit and hit[1] == n and (not live or time.time() - hit[0] < 5):
            out = hit[2]
        else:
            t0 = time.time()
            try:
                out = self._flow(sym, day, A, live, names, mode)
            except Exception as ex:   # pragma: no cover
                logger.warning("v126 flow %s: %s", sym, ex, exc_info=True)
                out = {"sym": sym, "day": day, "error": str(ex)[:200]}
            out["ms"] = round((time.time() - t0) * 1000)
            if len(self.fcache) > 200:
                self.fcache.clear()
            self.fcache[ck] = (time.time(), n, out)
        if brief:
            return {k: out.get(k) for k in ("sym", "day", "day_label", "live", "mode", "tot", "size_big", "sweep_sum", "wall_sum",
                                             "effect", "yorum", "error", "empty", "ms", "version", "thr")}
        return out

    def _flow(self, sym, day, A, live, names, mode):
        out = {"sym": sym, "day": day, "day_label": _day_label(day) if day else "", "live": live, "mode": mode or "—", "version": VERSION}
        if not A or not A[0]:
            out["empty"] = True
            out["yorum"] = "Bu gün için işlem kaydı yok."
            return out
        T, P, L, SD, B, S = A
        nm = lambda i: names[i] if 0 <= i < len(names) else ""
        # ---- 1) toplamlar (sürekli işlem + tek fiyat ayrı)
        tot = {"b_lot": 0.0, "b_tl": 0.0, "s_lot": 0.0, "s_tl": 0.0, "a_lot": 0.0, "a_tl": 0.0, "nb": 0, "ns": 0}
        for t, p, l, sd in zip(T, P, L, SD):
            v = p * l
            if sd == 1:
                tot["b_lot"] += l; tot["b_tl"] += v; tot["nb"] += 1
            elif sd == 2:
                tot["s_lot"] += l; tot["s_tl"] += v; tot["ns"] += 1
            else:
                tot["a_lot"] += l; tot["a_tl"] += v
        ab = tot["b_tl"] + tot["s_tl"]
        tot["b_pct"] = _r(tot["b_tl"] / ab * 100, 1) if ab else None
        tot["net_tl"] = round(tot["b_tl"] - tot["s_tl"])
        tot["turnover"] = round(ab + tot["a_tl"])
        for k in ("b_lot", "b_tl", "s_lot", "s_tl", "a_lot", "a_tl"):
            tot[k] = round(tot[k])
        cont = [i for i, t in enumerate(T) if CONT_FROM <= t < CONT_TO and SD[i] in (1, 2)]
        p_open = P[cont[0]] if cont else P[0]
        p_last = P[-1]
        tot["p_open"], tot["p_last"] = p_open, p_last
        tot["chg"] = _r(_pc(p_last, p_open), 2)
        out["tot"] = tot
        TT = tot["turnover"] or 1
        # ---- 2) pencereler
        win = {}
        for W in (15, 30, 60):
            bk = {}
            for i in cont:
                k = (T[i] - CONT_FROM) // (W * 60)
                x = bk.get(k)
                if x is None:
                    x = bk[k] = [0.0, 0.0, 0.0, 0.0, P[i], P[i]]
                v = P[i] * L[i]
                if SD[i] == 1:
                    x[0] += v; x[2] += L[i]
                else:
                    x[1] += v; x[3] += L[i]
                x[5] = P[i]
            rows = []
            for k in sorted(bk):
                x = bk[k]
                s = x[0] + x[1]
                rows.append({"t": _hms(CONT_FROM + k * W * 60)[:5], "b": round(x[0]), "s": round(x[1]), "bl": round(x[2]), "sl": round(x[3]),
                             "bp": _r(x[0] / s * 100, 1) if s else None, "o": x[4], "c": x[5], "chg": _r(_pc(x[5], x[4]), 2)})
            win[str(W)] = rows
        out["win"] = win
        # ---- 3) agresif emirler (ardışık: aynı saniye, aynı taraf, aynı agresör kurum)
        G = []
        prev_p = None
        i = 0
        nT = len(T)
        last_before = []          # her işlemden önceki son fiyat
        while i < nT:
            sd = SD[i]
            if sd not in (1, 2) or not (CONT_FROM <= T[i] < CONT_TO):
                prev_p = P[i]; i += 1; continue
            ag = B[i] if sd == 1 else S[i]
            j = i
            lot = tl = 0.0
            prices = set()
            while j < nT and T[j] == T[i] and SD[j] == sd and (B[j] if sd == 1 else S[j]) == ag:
                lot += L[j]; tl += L[j] * P[j]; prices.add(P[j]); j += 1
            G.append((T[i], sd, lot, tl, P[i], P[j - 1], len(prices), ag, prev_p if prev_p is not None else P[i], j - 1))
            prev_p = P[j - 1]
            i = j
        whale = min(5_000_000.0, max(250_000.0, 0.002 * TT))
        large, med = whale / 4.0, whale / 20.0
        out["thr"] = {"whale": round(whale), "large": round(large), "med": round(med)}

        def px_at(t):
            k = bisect.bisect_right(T, t) - 1
            return P[k] if k >= 0 else None

        cls_ = [("küçük", 0, med), ("orta", med, large), ("büyük", large, whale), ("balina", whale, 1e18)]
        sz = []
        for name, lo, hi in cls_:
            bb = [g for g in G if g[1] == 1 and lo <= g[3] < hi]
            ss = [g for g in G if g[1] == 2 and lo <= g[3] < hi]
            btl, stl = sum(g[3] for g in bb), sum(g[3] for g in ss)
            sz.append({"k": name, "lo": round(lo), "hi": None if hi > 1e17 else round(hi), "nb": len(bb), "ns": len(ss),
                       "b": round(btl), "s": round(stl), "bp": _r(btl / (btl + stl) * 100, 1) if btl + stl else None})
        out["size"] = sz
        bigb = sum(x["b"] for x in sz[2:]); bigs = sum(x["s"] for x in sz[2:])
        out["size_big"] = {"b": bigb, "s": bigs, "bp": _r(bigb / (bigb + bigs) * 100, 1) if bigb + bigs else None,
                           "n": sum(x["nb"] + x["ns"] for x in sz[2:]), "nw_b": sz[3]["nb"], "nw_s": sz[3]["ns"]}
        topw = sorted((g for g in G if g[3] >= large), key=lambda g: -g[3])[:10]
        out["whales"] = [{"t": _hms(g[0]), "side": "ALIŞ" if g[1] == 1 else "SATIŞ", "lot": round(g[2]), "tl": round(g[3]), "p0": g[4], "p1": g[5],
                          "br": nm(g[7]), "lev": g[6], "e60": _r(_pc(px_at(g[0] + 60), g[8]), 2), "e300": _r(_pc(px_at(g[0] + 300), g[8]), 2)} for g in topw]
        # ---- 4) süpürmeler (≥2 fiyat kademesi tek agresif emirde)
        swmin = max(100_000.0, med)
        SW = [g for g in G if g[6] >= 2 and g[3] >= swmin]
        def swsum(side):
            xs = [g for g in SW if g[1] == side]
            if not xs:
                return {"n": 0, "lev": 0, "tl": 0, "e0": None, "e300": None}
            e0 = [_pc(g[5], g[8]) or 0.0 for g in xs]
            e5 = [v for v in (_pc(px_at(g[0] + 300), g[8]) for g in xs) if v is not None]
            return {"n": len(xs), "lev": sum(g[6] - 1 for g in xs), "tl": round(sum(g[3] for g in xs)),
                    "e0": _r(sum(e0) / len(e0), 2), "e300": _r(sum(e5) / len(e5), 2) if e5 else None}
        out["sweep_sum"] = {"b": swsum(1), "a": swsum(2), "min_tl": round(swmin)}
        out["sweeps"] = [{"t": _hms(g[0]), "side": "ALIŞ" if g[1] == 1 else "SATIŞ", "lev": g[6] - 1, "lot": round(g[2]), "tl": round(g[3]),
                          "p0": g[8], "p1": g[5], "e0": _r(_pc(g[5], g[8]), 2), "e300": _r(_pc(px_at(g[0] + 300), g[8]), 2), "br": nm(g[7])}
                         for g in SW[-15:]][::-1]
        # ---- 5) duvar süpürme
        out["walls"], out["wall_sum"] = self._walls(sym, day, T, P, L, SD, B, TT, px_at, nm)
        # ---- 6) fiyat etkisi
        out["effect"] = self._effect(G, T, P, L, SD, cont, med, px_at)
        # ---- 7) yorum
        out["yorum"] = self._yorum(out, sym, day, live)
        return out

    def _walls(self, sym, day, T, P, L, SD, B, TT, px_at, nm):
        thr = min(50_000_000.0, max(500_000.0, 0.004 * TT))
        ev = []
        kind = "işlem"
        # (a) derinlik kaydı varsa v1.25 duvar kaydı (SÜPÜRÜLDÜ satış duvarları)
        try:
            if self.d is not None and self.d._file(day, sym)[0] is not None:
                r = self.d.analyze(sym, [2], day).get("r", {}).get("2") or {}
                if r.get("hist"):
                    kind = "derinlik"
                    for g in r.get("gone") or []:
                        if g.get("side") == "SATIŞ" and "SÜPÜR" in (g.get("st") or ""):
                            hh, mm, ss = (int(x) for x in g["t"].split(":"))
                            t = hh * 3600 + mm * 60 + ss
                            p = g["p"]
                            ev.append({"t0": g.get("first"), "t": g["t"], "p": p, "lot": round(g.get("fill") or 0), "tl": round((g.get("fill") or 0) * p),
                                       "peak": round(g.get("peak") or 0), "e300": _r(_pc(px_at(t + 300), p), 2), "e900": _r(_pc(px_at(t + 900), p), 2),
                                       "mx": _r(_pc(max([P[k] for k in range(bisect.bisect_right(T, t), bisect.bisect_right(T, t + 300))] or [p]), p), 2)})
        except Exception as ex:   # pragma: no cover
            logger.debug("v126 walls depth %s: %s", sym, ex)
        if kind == "işlem":
            # (b) VEKİL: aynı fiyatta art arda aktif alışla eriyen büyük satış kademesi; fiyat P'nin üstünde işlem görünce "süpürüldü"
            acc = {}       # P -> [t0, lot, tl, brokers Counter]
            for i in range(len(T)):
                t = T[i]
                if not (CONT_FROM <= t < CONT_TO):
                    continue
                p, l, sd = P[i], L[i], SD[i]
                if sd == 1:
                    a = acc.get(p)
                    if a is None:
                        a = acc[p] = [t, 0.0, 0.0, collections.Counter()]
                    a[1] += l; a[2] += l * p; a[3][B[i]] += l
                # P'nin üstünde işlem → P kademesi temizlendi
                done = [q for q in acc if q < p - EPS]
                for q in done:
                    a = acc.pop(q)
                    if a[2] >= thr:
                        k1 = bisect.bisect_right(T, t + 300)
                        mx = max(P[i:k1]) if k1 > i else p
                        top = a[3].most_common(1)[0][0] if a[3] else -1
                        ev.append({"t0": _hms(a[0]), "t": _hms(t), "p": q, "lot": round(a[1]), "tl": round(a[2]), "peak": None,
                                   "e300": _r(_pc(px_at(t + 300), q), 2), "e900": _r(_pc(px_at(t + 900), q), 2), "mx": _r(_pc(mx, q), 2),
                                   "br": nm(top), "dur": int(t - a[0])})
                # fiyat 3 adım+ aşağı inerse o seviyelerdeki birikim sıfırlanır (duvar tuttu / dağıldı)
                tk = _tick_size(p)
                for q in [q for q in acc if q > p + 3 * tk + EPS]:
                    acc.pop(q, None)
        up = [e for e in ev if (e.get("e300") or 0) > 0]
        s = {"kind": kind, "n": len(ev), "up": len(up), "tl": round(sum(e["tl"] for e in ev)), "thr": round(thr),
             "e300": _r(sum(e["e300"] or 0 for e in ev) / len(ev), 2) if ev else None,
             "label": ("Derinlik kaydı: süpürülen satış duvarları (v1.25)" if kind == "derinlik" else
                       f"VEKİL (işlemlerden): aynı fiyatta art arda aktif alışla ≥{_fs(thr)} ₺ eriyip fiyatın üstüne geçildiği satış kademeleri — "
                       "kayıtlı derinlikle kesin duvar takibi canlı seansla başlar")}
        return ev[-15:][::-1], s

    def _effect(self, G, T, P, L, SD, cont, med, px_at):
        bb = [g for g in G if g[1] == 1 and g[3] >= med]
        ss = [g for g in G if g[1] == 2 and g[3] >= med]
        def avg(xs, h):
            v = [x for x in (_pc(px_at(g[0] + h), g[8]) for g in xs) if x is not None]
            return _r(sum(v) / len(v), 3) if v else None
        # dakikalık: Δfiyat ve net aktif ₺
        M = {}
        for i in cont:
            m = T[i] // 60
            x = M.get(m)
            if x is None:
                x = M[m] = [P[i], P[i], 0.0]
            x[1] = P[i]
            x[2] += P[i] * L[i] * (1 if SD[i] == 1 else -1)
        ms = sorted(M)
        up = up_b = dn = dn_s = 0.0
        sxy = sxx = 0.0
        prev = None
        for m in ms:
            o, c, net = M[m]
            base = prev if prev is not None else o
            d = c - base
            if d > 0:
                up += d
                if net > 0:
                    up_b += d
            elif d < 0:
                dn += -d
                if net < 0:
                    dn_s += -d
            r = _pc(c, base) or 0.0
            x = net / 1e6
            sxy += x * r; sxx += x * x
            prev = c
        return {"b60": avg(bb, 60), "s60": avg(ss, 60), "b300": avg(bb, 300), "s300": avg(ss, 300), "nb": len(bb), "ns": len(ss),
                "up_b": _r(up_b / up * 100, 1) if up else None, "dn_s": _r(dn_s / dn * 100, 1) if dn else None,
                "slope": _r(sxy / sxx, 4) if sxx else None, "min_tl": round(med)}

    def _yorum(self, o, sym, day, live):
        t = o["tot"]; sb = o["size_big"]; sw = o["sweep_sum"]; ws = o["wall_sum"]; ef = o["effect"]
        parts = []
        bp = t.get("b_pct")
        if bp is not None:
            side = "aktif alış" if bp >= 50 else "aktif satış"
            parts.append(f"{side} baskın (%{_f1(max(bp, 100 - bp))}, net {'+' if t['net_tl'] >= 0 else '−'}{_fs(abs(t['net_tl']))} ₺)")
        if sb.get("bp") is not None and sb.get("n"):
            parts.append(f"büyük/balina emirlerin {_pe(sb['bp'])} alış tarafında")
        thick = None
        try:
            bk = (self.d._snapshot(sym, live) if self.d is not None else None)
            if bk:
                b10 = sum(x[1] for x in bk[0][:10]); a10 = sum(x[1] for x in bk[1][:10])
                thick = a10 > b10 * 1.2 if b10 else None
        except Exception:
            thick = None
        if ws.get("n"):
            vk = " (vekil)" if ws.get("kind") == "işlem" else ""
            head = (f"satış duvarı kalın olmasına rağmen balinalar {ws['n']} kez süpürdü{vk}" if thick else
                    f"alıcılar {ws['n']} kez satış duvarı süpürdü{vk}")
            e3 = ws.get("e300")
            parts.append(head + (f", 5 dk sonra ort. {_fpct(e3)}" if e3 is not None and abs(e3) >= 0.05 else ""))
        elif sw["b"]["n"]:
            parts.append(f"{sw['b']['n']} alış süpürmesi ({sw['b']['lev']} kademe)")
        if ef.get("up_b") is not None and (t.get("chg") or 0) > 0:
            parts.append(f"günün yükselişinin {_pe(ef['up_b'])} aktif alış ağırlıklı dakikalarda geldi")
        elif ef.get("dn_s") is not None and (t.get("chg") or 0) < 0:
            parts.append(f"günün düşüşünün {_pe(ef['dn_s'])} aktif satış ağırlıklı dakikalarda geldi")
        if ef.get("slope") is not None:
            u = 1 if t["turnover"] < 3e8 else 10 if t["turnover"] < 3e9 else 100
            v = ef["slope"] * u
            parts.append(f"her {u} Mn ₺ net aktif alış ≈ {_fpct(v)} fiyat" if abs(v) >= 0.05 else "net akışın fiyata etkisi zayıf")
        if not parts:
            return f"{sym}: yorum için yeterli işlem yok."
        s = "; ".join(parts)
        return s[0].upper() + s[1:] + "."

    # ================================================================ AKD+
    def akd_plus(self, sym, d1, d2, label):
        sym = (sym or "").upper().strip()
        t0 = time.time()
        v = self.feed.akd_view(sym, d1, d2)
        out = {"sym": sym, "from": d1, "to": d2, "label": label, "version": VERSION}
        if not v or not (v.get("buyers") or v.get("sellers")):
            out["available"] = False
            out["note"] = "Bu dönem için AKD verisi yok."
            return out
        out["available"] = True
        last = v.get("last")
        out["last"] = last
        out["ts"] = v.get("ts")
        rows = []
        for r in (v.get("buyers") or []) + (v.get("sellers") or []):
            rows.append({"br": r["broker"], "net": r.get("net_lot") or 0.0, "co": r.get("cost"), "bl": r.get("buy_lot"), "sl": r.get("sell_lot"),
                         "kz": r.get("pnl_tl"), "kzp": r.get("pnl_pct"), "pct": r.get("pct"), "tp": r.get("share_pct")})
        # ---- gün içi gerçekleşen K/Z (yalnız tek gün + işlem kaydı)
        real_note = None
        tr = {}
        if d1 == d2 and (TR_DIR / d1).is_dir() or (d1 == d2 and d1 == _today()):
            day, A, live, names, mode = self._trades(sym, d1)
            if A and day == d1:
                agg = {}
                T, P, L, SD, B, S = A
                for p, l, b, s in zip(P, L, B, S):
                    x = agg.get(b)
                    if x is None:
                        x = agg[b] = [0.0, 0.0, 0.0, 0.0]
                    x[0] += l; x[1] += l * p
                    y = agg.get(s)
                    if y is None:
                        y = agg[s] = [0.0, 0.0, 0.0, 0.0]
                    y[2] += l; y[3] += l * p
                tr = {names[i]: x for i, x in agg.items() if 0 <= i < len(names)}
            else:
                real_note = "Bu gün için işlem kaydı yok — gerçekleşen K/Z hesaplanamadı."
        else:
            real_note = "Gün içi gerçekleşen K/Z yalnız tek günlük dönemde (işlem kaydından) hesaplanır."
        match = []
        for r in rows:
            x = tr.get(r["br"])
            if x:
                ba = x[1] / x[0] if x[0] else None
                sa = x[3] / x[2] if x[2] else None
                mt = min(x[0], x[2])
                r["tbl"], r["tsl"], r["ba"], r["sa"] = round(x[0]), round(x[2]), _r(ba, 4), _r(sa, 4)
                r["real"] = round(mt * (sa - ba), 2) if mt and ba and sa else 0.0
                r["mt"] = round(mt)
                if r.get("bl") is not None and r["bl"] + (r.get("sl") or 0) > 0:
                    match.append(abs(x[0] - r["bl"]) / max(1.0, r["bl"]))
            else:
                r["real"] = None
            r["tot"] = round((r["kz"] or 0) + (r["real"] or 0), 2) if (r["kz"] is not None or r["real"] is not None) else None
        # ---- v1.26.2 aktif alış/satış (AKD Taraması ile aynı kaynak _aktif; yalnız tek gün + işlem kaydı)
        A = None
        if d1 == d2:
            try:
                A = (self._aktif(d1)[0] or {}).get(sym)
            except Exception:
                A = None
        for r in rows:
            y = A.get(r["br"]) if A else None
            aa, aat, as_ = self._apct(y)
            r["aa"], r["aat"], r["as"] = aa, aat, as_
            r["abl"], r["abtl"], r["asl"], r["astl"] = (y[1], round(y[3]), y[5], round(y[7])) if y else (None, None, None, None)
        out["aktif_ok"] = bool(A)
        out["aktif_note"] = (None if A else ("Aktif alış % / lot yalnız tek günlük dönemde, o günün işlem kaydından hesaplanır (AKD Taraması ile aynı)." if d1 != d2
                                               else "Bu gün için işlem kaydı yok — aktif alış % / lot hesaplanamadı."))
        out["aktif_top"] = []
        if A:
            tab = sum(y[1] for y in A.values()) or 1
            act = sorted((r for r in rows if r.get("abl")), key=lambda r: -r["abl"])[:5]
            out["aktif_top"] = [{"br": r["br"], "aa": r["aa"], "abl": r["abl"], "abtl": r["abtl"], "net": r["net"], "co": r["co"],
                                 "share": _r(r["abl"] / tab * 100.0, 1)} for r in act]
            out["aktif_tot"] = {"abl": tab, "bl": sum(y[0] for y in A.values()), "abtl": round(sum(y[3] for y in A.values()))}
        out["rows"] = rows
        out["real_note"] = real_note
        out["match_err"] = _r(statistics.median(match) * 100, 2) if match else None
        out["sum"] = self._akd_sum(rows, last)
        out["analiz"] = self._akd_analiz(sym, rows, last, d1, d2, out["sum"])
        out["analiz"]["tahtaci"] = []
        if A:
            sig = tht_merge(rows, A)
            out["analiz"]["tahtaci"] = sig
            for x in reversed(sig):
                out["analiz"]["pts"].insert(0, x["text"])
        out["ms"] = round((time.time() - t0) * 1000)
        return out

    def _akd_sum(self, rows, last):
        withk = [r for r in rows if r.get("tot") is not None]
        prof = sorted((r for r in withk if r["tot"] > 0), key=lambda r: -r["tot"])[:3]
        loss = sorted((r for r in withk if r["tot"] < 0), key=lambda r: r["tot"])[:3]
        nb = [r for r in rows if r["net"] > 0]; ns = [r for r in rows if r["net"] < 0]
        f = lambda r: {"br": r["br"], "tot": r["tot"], "kz": r["kz"], "real": r.get("real"), "kzp": r.get("kzp"), "net": r["net"], "co": r["co"]}
        big = sorted((r for r in rows if r.get("co")), key=lambda r: -abs(r["net"] * r["co"]))[:5]
        above = [r for r in big if last and r["co"] and last > r["co"]]
        return {"prof": [f(r) for r in prof], "loss": [f(r) for r in loss],
                "kz_b": round(sum(r["kz"] or 0 for r in nb)), "kz_s": round(sum(r["kz"] or 0 for r in ns)),
                "real_b": round(sum(r.get("real") or 0 for r in nb)), "real_s": round(sum(r.get("real") or 0 for r in ns)),
                "nb": len(nb), "ns": len(ns),
                "big": [{"br": r["br"], "net": r["net"], "co": r["co"], "d": _r(_pc(last, r["co"]), 2), "side": "ALICI" if r["net"] > 0 else "SATICI",
                         "aa": r.get("aa"), "abl": r.get("abl"), "as": r.get("as"), "asl": r.get("asl")} for r in big],
                "above": len(above), "nbig": len(big)}

    def _hist_days(self, sym, upto, n=10):
        try:
            ds = sorted((d.name for d in AKD_DIR.iterdir() if d.is_dir() and d.name.isdigit() and d.name <= upto), reverse=True)[:n]
        except Exception:
            return []
        out = []
        for d in ds:
            try:
                e = json.loads((AKD_DIR / d / f"{sym}.json").read_text())
                out.append((d, {r["broker"]: (r.get("value") or 0.0) for r in e.get("TUM") or []}))
            except Exception:
                continue
        return out

    def _akd_analiz(self, sym, rows, last, d1, d2, sm):
        nb = sorted((r for r in rows if r["net"] > 0), key=lambda r: -r["net"])
        ns = sorted((r for r in rows if r["net"] < 0), key=lambda r: r["net"])
        vb = sum(r["net"] for r in nb) or 1.0
        vs = sum(-r["net"] for r in ns) or 1.0
        b3 = sum(r["net"] for r in nb[:3]) / vb * 100 if nb else 0.0
        s3 = sum(-r["net"] for r in ns[:3]) / vs * 100 if ns else 0.0
        durum = _durum(b3, s3, len(nb), len(ns))
        pts = []
        pts.append(f"Yoğunlaşma: ilk 3 alıcı net alımın {_pe(b3, True)}, ilk 3 satıcı net satışın {_pe(s3, True)} yaptı ({len(nb)} net alıcı / {len(ns)} net satıcı).")
        pts.append({"TOPLAMA": "TOPLAMA: az sayıda kurum çok sayıda satıcıdan topluyor.",
                    "DAĞITIM": "DAĞITIM: az sayıda kurum çok sayıda alıcıya dağıtıyor.",
                    "NÖTR": "Belirgin toplama/dağıtım yok (alış ve satış yoğunlaşması dengeli)."}[durum])
        # ısrarcı: çok günlü AKD + v1.23 ısrar
        pers = []
        if d1 == d2:
            H = self._hist_days(sym, d2)
            if len(H) >= 2:
                for r in nb[:8] + ns[:8]:
                    sg = 1 if r["net"] > 0 else -1
                    k = 0
                    for d, m in H:
                        if (m.get(r["br"]) or 0) * sg > 0:
                            k += 1
                        else:
                            break
                    if k >= 2:
                        pers.append({"br": r["br"], "days": k, "side": "alıcı" if sg > 0 else "satıcı", "of": len(H)})
            try:
                R = self.m.days.get(d2)
                if R is not None and R.ready:
                    for x in R.rows:
                        if x["s"] == sym and x.get("israr", 0) >= 70:
                            pers.append({"br": x["br"], "israr": x["israr"], "side": "alıcı (gün içi ısrar)"})
            except Exception:
                pass
        if pers:
            pts.append("Israrcı kurumlar: " + ", ".join(
                f"{_bn(p['br'])} ({p['days']} gündür net {p['side']})" if "days" in p else f"{_bn(p['br'])} (ısrar {p['israr']})" for p in pers[:5]) + ".")
        # kapana kısılanlar
        trapped_b = [r for r in nb[:6] if r.get("kzp") is not None and r["kzp"] <= -1.0 and abs(r["net"] * (r["co"] or 0)) >= 1e6]
        prof_s = [r for r in ns[:6] if r.get("kzp") is not None and r["kzp"] >= 1.0 and abs(r["net"] * (r["co"] or 0)) >= 1e6]
        prof_b = [r for r in nb[:6] if r.get("kzp") is not None and r["kzp"] >= 3.0 and abs(r["net"] * (r["co"] or 0)) >= 1e6]
        loss_s = [r for r in ns[:6] if r.get("kzp") is not None and r["kzp"] <= -1.0 and abs(r["net"] * (r["co"] or 0)) >= 1e6]
        if trapped_b:
            pts.append("Zararda büyük alıcılar (potansiyel destek / maliyet savunması): " + ", ".join(f"{_bn(r['br'])} maliyet {_fp(r['co'])} ({_fpct(r['kzp'])})" for r in trapped_b[:3]) + ".")
        if loss_s:
            pts.append("Fiyatın altından satan büyük satıcılar zararda (geri alım baskısı olabilir): " + ", ".join(f"{_bn(r['br'])} {_fp(r['co'])} ({_fpct(r['kzp'])})" for r in loss_s[:3]) + ".")
        if prof_s:
            pts.append("Kârda satıcılar (yukarıdan satmış, düşüşte geri alabilir): " + ", ".join(f"{_bn(r['br'])} {_fp(r['co'])} ({_fpct(r['kzp'])})" for r in prof_s[:3]) + ".")
        if prof_b:
            pts.append("Kârdaki büyük alıcılar (kâr satışı riski): " + ", ".join(f"{_bn(r['br'])} {_fp(r['co'])} ({_fpct(r['kzp'])})" for r in prof_b[:3]) + ".")
        if sm["nbig"]:
            pts.append(f"Fiyat ({_fp(last)}), en büyük {sm['nbig']} kurumun {sm['above']}'inin maliyetinin üstünde.")
        top_b = nb[0] if nb else None
        top_s = ns[0] if ns else None
        lead = ""
        if top_b and top_s:
            lead = (f"{durum}: {_bn(top_b['br'])} net alımın {_pe(top_b.get('pct'))} ile lider (maliyet {_fp(top_b['co'])}, {_fpct(top_b.get('kzp'))}), "
                    f"en büyük satıcı {_bn(top_s['br'])} (%{_f1(top_s.get('pct'))}, maliyet {_fp(top_s['co'])}, {_fpct(top_s.get('kzp'))}); "
                    f"net alıcıların açık K/Z'si {'+' if sm['kz_b'] >= 0 else '−'}{_fs(abs(sm['kz_b']))} ₺.")
        return {"durum": durum, "b3": _r(b3, 1), "s3": _r(s3, 1), "nb": len(nb), "ns": len(ns), "pers": pers[:8],
                "trapped_b": [r["br"] for r in trapped_b], "yorum": lead, "pts": pts}

    def tahtaci(self, sym, day=None):
        """v1.26.2 Özet sekmesi için: o günün AKD'si (akd_view, AKD sekmesi ile aynı) + aktif alış/satış (_aktif) → tahtacı sinyali listesi."""
        sym = (sym or "").upper().strip()
        d = (day or "").replace("-", "") or self.feed._akd_date()
        k = (sym, d)
        hit = self.thcache.get(k)
        now = time.time()
        if hit and now - hit[0] < 30:
            return hit[1]
        res = []
        try:
            A = (self._aktif(d)[0] or {}).get(sym)
            e = None
            if A:
                # ağ isteği YOK: günlük AKD deposu (AKD sekmesi Günlük ile aynı kayıt) ya da kayıtlı gün dosyası
                if d == self.feed._akd_date():
                    e = self.feed.akd_day_get(sym)
                if e is None:
                    try:
                        e = json.loads((AKD_DIR / d / f"{sym}.json").read_text())
                        if e.get("empty") or e.get("date") not in (None, d):
                            e = None
                    except Exception:
                        e = None
            if e is not None:
                with self.feed._lock:
                    last = (self.feed.quotes.get(sym) or {}).get("last")
                buyers, sellers = self.feed._akd_compose(e.get("TUM") or [], e.get("TOPLAM") or [], last)
                rows = [{"br": r["broker"], "net": r.get("net_lot") or 0.0, "co": r.get("cost"), "pct": r.get("pct"), "bl": r.get("buy_lot")} for r in buyers + sellers]
                res = tht_merge(rows, A)
        except Exception as ex:   # pragma: no cover
            logger.debug("v126 tahtaci %s: %s", sym, ex)
        self.thcache[k] = (now, res)
        if len(self.thcache) > 400:
            for kk in list(self.thcache)[:200]:
                self.thcache.pop(kk, None)
        return res

    # ============================================================ TARAMA
    def dates(self):
        try:
            ds = sorted((d.name for d in AKD_DIR.iterdir() if d.is_dir() and d.name.isdigit() and any(True for _ in d.glob("*.json"))), reverse=True)[:8]
        except Exception:
            ds = []
        cur = self.feed._akd_date()
        if cur not in ds:
            ds.insert(0, cur)
        return [{"d": d, "l": _day_label(d), "cur": d == cur} for d in ds]

    # ---------------------------------------------------- v1.26.1 AKTİF %
    def _aktif(self, d):
        """Gün d için hisse → {kurum adı: [alış lot, aktif alış lot, alış ₺, aktif alış ₺, satış lot, aktif satış lot, satış ₺, aktif satış ₺]}.
        Kaynak v1.23 ile aynı (m._src: canlı store / kayıtlı gün); aktif alış = sd==1 (alıcı agresör), aktif satış = sd==2.
        Artımlı: hisse başına işaretçi; canlı store birleşirse (snap_merges) o hisse baştan. O günün işlem kaydı yoksa {}."""
        if self.m is None:
            return {}, None
        day, live = self.m._resolve_day(d)
        if day != d:
            return {}, None
        t0 = time.time()
        with self.alock:
            try:
                mode, syms, brokers, lock, sid = self.m._src(day)
            except Exception:
                return {}, None
            C = self.acache.get(day)
            if C is None or C["sid"] != sid:
                C = {"sid": sid, "st": {}}
                self.acache[day] = C
                for old in [k for k in self.acache if k != day][:-1]:
                    self.acache.pop(old, None)
            ST = C["st"]
            names = list(brokers)
            nn = 0
            for sym in list(syms.keys()):
                e = syms.get(sym)
                if e is None:
                    continue
                cur = ST.get(sym)
                with lock:
                    n = len(e.t)
                    mg = getattr(e, "snap_merges", 0)
                    if cur is not None and cur[0] == n and cur[1] == mg:
                        continue
                    if cur is None or cur[1] != mg or n < cur[0]:
                        cur = [0, mg, {}]
                    a = cur[0]
                    P = e.p[a:n]; L = e.l[a:n]; SD = e.sd[a:n]; B = e.b[a:n]; S = e.s[a:n]
                    if len(names) < len(brokers):
                        names = list(brokers)
                ag = cur[2]
                for p, l, sd, b, s in zip(P, L, SD, B, S):
                    v = p * l
                    if b:
                        x = ag.get(b)
                        if x is None:
                            x = ag[b] = [0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0]
                        x[0] += l; x[2] += v
                        if sd == 1:
                            x[1] += l; x[3] += v
                    if s:
                        y = ag.get(s)
                        if y is None:
                            y = ag[s] = [0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0]
                        y[4] += l; y[6] += v
                        if sd == 2:
                            y[5] += l; y[7] += v
                cur[0] = n
                ST[sym] = cur
                nn += len(P)
            out = {}
            nl = len(names)
            for sym, cur in ST.items():
                out[sym] = {names[i]: x for i, x in cur[2].items() if 0 <= i < nl}
        self.atime[day] = round(time.time() - t0, 3)
        if nn > 200000:
            logger.info("v126: aktif %% %s hesaplandı (%d işlem, %.1f sn)", day, nn, time.time() - t0)
        return out, mode

    @staticmethod
    def _apct(x):
        """[bl, abl, btl, abtl, sl, asl, stl, astl] → (aktif alış % lot, aktif alış % ₺, aktif satış % lot)."""
        if not x:
            return None, None, None
        aa = round(x[1] / x[0] * 100.0, 1) if x[0] > 0 else None
        aat = round(x[3] / x[2] * 100.0, 1) if x[2] > 0 else None
        as_ = round(x[5] / x[4] * 100.0, 1) if x[4] > 0 else None
        return aa, aat, as_

    def tarama(self, date=None, tok=None):
        cur = self.feed._akd_date()
        d = (date or "").replace("-", "").strip() or cur
        if not (d.isdigit() and len(d) == 8):
            d = cur
        hit = self.tcache.get(d)
        now = time.time()
        if hit and now - hit[0] < (20 if d == cur else 600):
            res = hit[1]
        else:
            t0 = time.time()
            res = self._tarama(d, d == cur)
            res["ms"] = round((time.time() - t0) * 1000)
            self.tcache[d] = (now, res)
            if len(self.tcache) > 6:
                self.tcache.pop(next(iter(self.tcache)))
        if tok and tok == res.get("tok"):
            return {"same": True, "tok": tok, "date": d}
        return res

    def _tarama(self, d, is_cur):
        F = self.feed
        brs = []
        bix = {}
        def bi(n):
            k = bix.get(n)
            if k is None:
                k = bix[n] = len(brs); brs.append(n)
            return k
        per = collections.defaultdict(list)     # sym -> [(b, bl, sl, nl, co, np, bgp, sgp, tp, kz, kzp, p)]
        src = ""
        if is_cur:
            res = F.broker_positions()
            for r in res["rows"]:
                per[r["s"]].append((r["b"], r["bl"], r["sl"], r["nl"], r["co"], r["np"], r["bgp"], r["sgp"], r["tp"], r["kz"], r["kzp"], r["p"]))
            src = "günlük AKD deposu (AKD sekmesi Günlük / Kurum Analizi ile aynı kayıt)"
            ts = max((r.get("at") or 0) for r in res["rows"]) if res["rows"] else None
        else:
            p = AKD_DIR / d
            with F._lock:
                quotes = {s: (q.get("last")) for s, q in F.quotes.items()}
            ts = None
            for f in p.glob("*.json") if p.is_dir() else []:
                try:
                    e = json.loads(f.read_text())
                except Exception:
                    continue
                if e.get("empty") or e.get("date") != d:
                    continue
                sym = f.stem
                last = quotes.get(sym)
                buyers, sellers = F._akd_compose(e.get("TUM") or [], e.get("TOPLAM") or [], last)
                items = []
                for r in buyers + sellers:
                    net = r.get("net_lot") or 0.0
                    bl = r.get("buy_lot"); sl = r.get("sell_lot")
                    if bl is None: bl = max(net, 0.0)
                    if sl is None: sl = max(-net, 0.0)
                    items.append((r["broker"], bl, sl, net, r.get("cost"), r.get("pct"), last))
                vol = sum(i[1] for i in items) or 1.0
                svol = sum(i[2] for i in items) or vol
                tsum = sum(i[1] + i[2] for i in items) or 1.0
                for b, bl, sl, net, cost, dp, lst in items:
                    kz = kzp = None
                    if lst and cost and net:
                        kz = round(net * (lst - cost), 2); kzp = round((lst - cost) / cost * 100.0 * (1 if net > 0 else -1), 2)
                    npct = dp if net > 0 else (-dp if net < 0 and dp is not None else 0.0)
                    per[sym].append((b, round(bl), round(sl), round(net), round(cost, 4) if cost else None, npct,
                                     round(bl / vol * 100, 2), round(sl / svol * 100, 2), round((bl + sl) / tsum * 100, 2), kz, kzp, lst))
                ts = max(ts or 0, e.get("ts") or 0)
            src = f"kayıtlı günlük AKD ({_day_label(d)}) — aynı hesap (_akd_compose), son fiyat = güncel kotasyon (AKD sekmesi gibi)"
        try:
            gd = self.m._gd(d, is_cur and d == _today())
        except Exception:
            gd = {}
        with F._lock:
            qd = {s: (q.get("change_pct")) for s, q in F.quotes.items()}
            qpc = {s: (q.get("prev_close"), q.get("last"), q.get("high")) for s, q in F.quotes.items()} if is_cur else {}
        try:
            AK, amode = self._aktif(d)
        except Exception as ex:   # pragma: no cover
            logger.warning("v126 aktif: %s", ex)
            AK, amode = {}, None
        n_ak = 0
        stocks = []
        rows = []
        for si, sym in enumerate(sorted(per)):
            it = per[sym]
            nb = sorted((x for x in it if (x[3] or 0) > 0), key=lambda x: -x[3])
            ns = sorted((x for x in it if (x[3] or 0) < 0), key=lambda x: x[3])
            vb = sum(x[3] for x in nb) or 1.0; vs = sum(-x[3] for x in ns) or 1.0
            b3 = sum(x[3] for x in nb[:3]) / vb * 100 if nb else 0.0
            s3 = sum(-x[3] for x in ns[:3]) / vs * 100 if ns else 0.0
            last = next((x[11] for x in it if x[11]), None)
            g = gd.get(sym) if gd else None
            if g is None and is_cur:
                g = qd.get(sym)
            vol = sum(x[1] for x in it)
            # v1.26.1 TÜM AKD NET (hisse bazında): net alıcıların toplam net lotu (= net satıcıların toplamı, AKD TOPLAM) ÷ hissenin toplam işlem lotu (Σ alış lotu)
            tnb = sum(x[3] for x in nb); tns = sum(-x[3] for x in ns)
            A = AK.get(sym)
            sab = sabl = sasl = None
            if A:
                n_ak += 1
                sabl = sum(y[1] for y in A.values()); sasl = sum(y[5] for y in A.values())
                sab = _r(sabl / (sabl + sasl) * 100.0, 1) if sabl + sasl > 0 else None
            # v1.26.3 tavan kapanışı (yalnız güncel seans: önceki kapanış → BIST ±%10 limit)
            tv = tvh = None
            q3 = qpc.get(sym)
            if q3 and q3[0]:
                tvp = _tavan(q3[0])
                lp = q3[1] or last
                tv = 1 if (tvp and lp and lp >= tvp - 1e-9) else 0
                tvh = 1 if (tvp and q3[2] and q3[2] >= tvp - 1e-9) else 0
            stocks.append([sym, last, _r(g, 2), len(nb), len(ns), _r(b3, 1), _r(s3, 1), _durum(b3, s3, len(nb), len(ns)), round(vol),
                           round(tnb), round(tns), _r(tnb / vol * 100.0, 2) if vol else None, sab, sabl, sasl, tv, tvh])
            rbk = {x[0]: i + 1 for i, x in enumerate(nb)}
            rsk = {x[0]: i + 1 for i, x in enumerate(ns)}
            wbk = {x[0]: i + 1 for i, x in enumerate(sorted(it, key=lambda x: -(x[1] or 0)))}
            for x in it:
                y = A.get(x[0]) if A else None
                aa, aat, as_ = self._apct(y)
                if y:
                    abl, abtl, asl, astl = y[1], round(y[3]), y[5], round(y[7])
                else:
                    abl = abtl = asl = astl = None
                rb, rs, wb = rbk.get(x[0]), rsk.get(x[0]), wbk.get(x[0])
                tt = tren_eval(x[3], rb, wb, _r(x[5], 2), aa, abtl)[0] if y else 0
                rows.append([si, bi(x[0]), x[3], _r(x[5], 2), _r(x[6], 2), _r(x[7], 2), x[4], _r(x[9], 0), _r(x[10], 2), _r(x[8], 2), x[1], x[2], aa, aat, as_,
                             abl, abtl, asl, astl, y[0] if y else None, round(y[2]) if y else None, rb, rs, wb, tt])
        try:
            C = self.acache.get(d)
            nptr = sum(c[0] for c in C["st"].values()) if C else 0
        except Exception:
            nptr = 0
        tok = f"{d}:{len(rows)}:{int(ts or 0)}:{nptr}"
        return {"date": d, "date_label": _day_label(d), "cur": is_cur, "dates": self.dates(), "src": src, "ts": ts,
                "ts_s": time.strftime("%H:%M:%S", time.localtime(ts)) if ts else None,
                "brokers": brs, "stocks": stocks, "rows": rows, "tok": tok, "version": VERSION, "trn_p": TRN_P,
                "aktif": {"stocks": n_ak, "mode": amode, "sec": self.atime.get(d),
                          "note": (f"Aktif alış % = kurumun o hissedeki aktif alış lotu ÷ tüm alış lotu ({'canlı' if amode == 'canlı' else 'kayıtlı'} işlem kaydı, "
                                   f"{n_ak} hisse; v1.23 Maliyet Yükselten ile aynı tanım)") if n_ak else "Bu seans için işlem kaydı yok — aktif alış/satış % gösterilemiyor (—)."},
                "cols": {"stocks": ["s", "p", "gd", "nb", "ns", "b3", "s3", "durum", "vol", "tnb", "tns", "tnp", "sab", "sabl", "sasl", "tv", "tvh"],
                         "rows": ["si", "bi", "nl", "np", "bgp", "sgp", "co", "kz", "kzp", "tp", "bl", "sl", "aa", "aat", "as", "abl", "abtl", "asl", "astl", "tbl", "tbtl",
                                  "rb", "rs", "wb", "tt"]}}

    # ============================================================= WATCH
    def watch_get(self):
        return {"rules": self.watch.get("rules") or [], "nt": NT_AKDT, "emitted": self.emitted, "loops": self.loops,
                "note": "Seans içinde ~60 sn'de bir kontrol edilir; kural kaydedildiğindeki eşleşmeler taban kabul edilir (yalnız yeni girişler bildirilir)."}

    def watch_set(self, rules):
        clean = []
        for r in (rules or [])[:10]:
            try:
                brs = [str(b)[:60] for b in (r.get("brokers") or [])][:20]
                if not brs:
                    continue
                clean.append({"id": str(r.get("id") or f"r{int(time.time() * 1000) % 10 ** 9}")[:24], "brokers": brs,
                              "min_np": float(r.get("min_np") or 0), "min_tl": float(r.get("min_tl") or 0),
                              "side": "sell" if r.get("side") == "sell" else "buy", "name": str(r.get("name") or "")[:60],
                              "min_aa": float(r.get("min_aa") or 0)})
            except Exception:
                continue
        with self.lock:
            self.watch["rules"] = clean
            # taban: şu anki eşleşmeler "görüldü"
            d = self.feed._akd_date()
            seen = self.watch.get("seen") if self.watch.get("day") == d else {}
            seen = dict(seen or {})
            try:
                rows = self.feed.broker_positions()["rows"]
                AK = self._aktif(d)[0] if any(r.get("min_aa") for r in clean) else {}
                for r in clean:
                    for x in rows:
                        if self._match(r, x, AK):
                            seen[f"{r['id']}|{x['s']}|{x['b']}"] = 1
            except Exception:
                pass
            self.watch["seen"] = seen
            self.watch["day"] = d
            self._save()
        return self.watch_get()

    # ------------------------------------------------ v1.26.2 aktif_kurum
    def akk_get(self):
        a = self.akk
        return {"on": bool(a.get("on")), "min_tl": a.get("min_tl"), "min_aa": a.get("min_aa"), "net": bool(a.get("net")),
                "brokers": a.get("brokers") or [], "nt": NT_AKK, "emitted": self.akk_emitted,
                "note": "Seans içinde ~60 sn'de bir: bir kurum bir hissede eşik ₺ üstünde ve eşik aktif alış % üstünde aldıysa bildirir "
                        "(hisse+kurum başına günde 1, saatte en çok 15; açtığınız andaki eşleşmeler taban kabul edilir)."}

    def akk_set(self, cfg):
        cfg = cfg or {}
        with self.lock:
            a = self.akk
            a["on"] = bool(cfg.get("on"))
            try:
                a["min_tl"] = max(1e5, float(cfg.get("min_tl") if cfg.get("min_tl") is not None else a["min_tl"]))
                a["min_aa"] = min(100.0, max(0.0, float(cfg.get("min_aa") if cfg.get("min_aa") is not None else a["min_aa"])))
            except Exception:
                pass
            a["net"] = bool(cfg.get("net", a.get("net", True)))
            a["brokers"] = [str(b)[:60] for b in (cfg.get("brokers") or [])][:30]
            d = self.feed._akd_date()
            seen = dict(a.get("seen") or {}) if a.get("day") == d else {}
            if a["on"]:
                try:
                    for k in self._akk_hits(d):
                        seen[k[0]] = 1
                except Exception:
                    pass
            a["seen"] = seen; a["day"] = d
            self._save_akk()
        return self.akk_get()

    def _akk_hits(self, d):
        a = self.akk
        AK = self._aktif(d)[0] or {}
        net = {}
        if a.get("net"):
            for x in self.feed.broker_positions()["rows"]:
                net[(x["s"], x["b"])] = (x.get("nl") or 0, x.get("p"))
        brs = set(a.get("brokers") or [])
        out = []
        for sym, M in AK.items():
            for b, y in M.items():
                if brs and b not in brs:
                    continue
                if y[3] < a["min_tl"] or y[0] <= 0:
                    continue
                aa = y[1] / y[0] * 100.0
                if aa < a["min_aa"]:
                    continue
                nl = net.get((sym, b), (None, None))[0]
                if a.get("net") and not (nl and nl > 0):
                    continue
                out.append((f"{sym}|{b}", sym, b, aa, y, nl))
        out.sort(key=lambda t: -t[4][3])
        return out

    def _check_akk(self):
        a = self.akk
        if not a.get("on") or self.hub is None:
            return
        d = self.feed._akd_date()
        if d != _today():
            return
        with self.lock:
            if a.get("day") != d:
                a["day"] = d; a["seen"] = {}
            seen = a["seen"]
        now = time.time()
        while self.akrate and now - self.akrate[0] > 3600:
            self.akrate.popleft()
        n = 0
        for k, sym, b, aa, y, nl in self._akk_hits(d):
            if k in seen:
                continue
            if n >= 3 or len(self.akrate) >= 15:
                break
            seen[k] = 1
            n += 1
            self.akrate.append(now)
            title = f"⚡ {_bn(b)} · {sym} aktif alış %{_f1(aa)}"
            txt = (f"Aktif alış {_fs(y[1])} lot (≈{_fs(y[3])} ₺) / toplam alış {_fs(y[0])} lot" + (f" · net {_fs(nl)} lot" if nl else "")
                   + f" · eşik ≥%{_f1(a['min_aa'])}, ≥{_fs(a['min_tl'])} ₺")
            try:
                self.hub._emit("olay", NT_AKK, sym, title, txt, {"f": "aktif_kurum", "br": b})
                self.akk_emitted += 1
            except Exception as ex:   # pragma: no cover
                logger.debug("v126 akk emit: %s", ex)
        if n:
            with self.lock:
                self._save_akk()

    # ------------------------------------------------ v1.26.3 tavan_treni
    def trn_get(self):
        a = self.trn
        return {"on": bool(a.get("on")), "grade": 2 if a.get("grade", 2) >= 2 else 1, "nt": NT_TRN, "emitted": self.trn_emitted, "p": TRN_P,
                "note": "Seans içinde ~60 sn'de bir AKD Taraması verisiyle (aynı tt sütunu) kontrol edilir: bir kurum bir hissede TAVAN TRENİ "
                        "sinyaline girince bildirir (hisse+kurum başına günde 1, saatte en çok 10; açtığınız andaki eşleşmeler taban kabul edilir)."}

    def trn_set(self, cfg):
        cfg = cfg or {}
        with self.lock:
            a = self.trn
            a["on"] = bool(cfg.get("on"))
            try:
                a["grade"] = 1 if int(cfg.get("grade", a.get("grade", 2))) <= 1 else 2
            except Exception:
                a["grade"] = 2
            d = self.feed._akd_date()
            seen = dict(a.get("seen") or {}) if a.get("day") == d else {}
            if a["on"]:
                try:
                    for h in self._trn_hits(d, 1):
                        seen[h["k"]] = 1
                except Exception:
                    pass
            a["seen"] = seen; a["day"] = d
            self._save_trn()
        return self.trn_get()

    def _trn_hits(self, d, gmin):
        res = self.tarama(d)
        if not res or "cols" not in res:
            return []
        ci = {k: i for i, k in enumerate(res["cols"]["rows"])}
        sc = {k: i for i, k in enumerate(res["cols"]["stocks"])}
        if "tt" not in ci:
            return []
        out = []
        for r in res["rows"]:
            g = r[ci["tt"]] or 0
            if g < gmin:
                continue
            s = res["stocks"][r[ci["si"]]]
            b = res["brokers"][r[ci["bi"]]]
            out.append({"k": f"{s[sc['s']]}|{b}", "sym": s[sc["s"]], "br": b, "g": g, "rb": r[ci["rb"]], "wb": r[ci["wb"]], "np": r[ci["np"]],
                        "aa": r[ci["aa"]], "abtl": r[ci["abtl"]], "nl": r[ci["nl"]], "gd": s[sc["gd"]], "p": s[sc["p"]]})
        out.sort(key=lambda h: (-h["g"], -(h["abtl"] or 0)))
        return out

    def _check_trn(self):
        a = self.trn
        if not a.get("on") or self.hub is None:
            return
        d = self.feed._akd_date()
        if d != _today():
            return
        with self.lock:
            if a.get("day") != d:
                a["day"] = d; a["seen"] = {}
            seen = a["seen"]
        now = time.time()
        while self.trrate and now - self.trrate[0] > 3600:
            self.trrate.popleft()
        n = 0
        for h in self._trn_hits(d, 2 if a.get("grade", 2) >= 2 else 1):
            if h["k"] in seen:
                continue
            if n >= 3 or len(self.trrate) >= 10:
                break
            seen[h["k"]] = 1
            n += 1
            self.trrate.append(now)
            G = "GÜÇLÜ" if h["g"] >= 2 else "ORTA"
            title = f"🚂 TAVAN TRENİ ({G}) · {h['sym']} · {_bn(h['br'])}"
            who = "AKD Alış #1" if h["rb"] == 1 else f"en büyük alıcı (AKD Alış #{h['rb']})"
            txt = (f"{who} · net alımın {_pe(h['np'])} · aktif alış %{_f1(h['aa'])} ({_fs(h['abtl'])} ₺) · net {_fs(h['nl'])} lot"
                   + (f" · gün {_fpct(h['gd'])}" if h.get("gd") is not None else ""))
            try:
                self.hub._emit("olay", NT_TRN, h["sym"], title, txt, {"f": "tavan_treni", "br": h["br"], "price": h.get("p")})
                self.trn_emitted += 1
            except Exception as ex:   # pragma: no cover
                logger.debug("v126 trn emit: %s", ex)
        if n:
            with self.lock:
                self._save_trn()

    def _save_trn(self):
        try:
            tmp = TRN_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.trn, ensure_ascii=False))
            os.replace(tmp, TRN_FILE)
        except Exception as ex:   # pragma: no cover
            logger.debug("v126 trn save: %s", ex)

    def _save_akk(self):
        try:
            tmp = AKK_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.akk, ensure_ascii=False))
            os.replace(tmp, AKK_FILE)
        except Exception as ex:   # pragma: no cover
            logger.debug("v126 akk save: %s", ex)

    def _save(self):
        try:
            tmp = WATCH_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.watch, ensure_ascii=False))
            os.replace(tmp, WATCH_FILE)
        except Exception as ex:   # pragma: no cover
            logger.debug("v126 watch save: %s", ex)

    @classmethod
    def _match(cls, rule, x, AK=None):
        if x["b"] not in rule["brokers"]:
            return False
        ma = rule.get("min_aa") or 0
        if ma > 0:
            # v1.26.1 — aktif alış % (alıcı kuralı) / aktif satış % (satıcı kuralı); işlem kaydı yoksa eşleşmez
            A = (AK or {}).get(x["s"]) or {}
            aa, _, as_ = cls._apct(A.get(x["b"]))
            v = aa if rule["side"] == "buy" else as_
            if v is None or v < ma:
                return False
        np_ = x.get("np") or 0.0
        if rule["side"] == "buy":
            if x["nl"] <= 0 or np_ < rule["min_np"]:
                return False
        else:
            if x["nl"] >= 0 or -np_ < rule["min_np"]:
                return False
        tl = abs(x["nl"] * (x.get("p") or x.get("co") or 0))
        return tl >= rule["min_tl"]

    def _loop(self):
        time.sleep(25)
        try:                                   # v1.26.1 — aktif % önbelleğini ısıt (ilk AKD Taraması beklemesin)
            self._aktif(self.feed._akd_date())
        except Exception as ex:   # pragma: no cover
            logger.debug("v126 aktif warm: %s", ex)
        time.sleep(35)
        while True:
            try:
                self._check()
                self.loops += 1
            except Exception as ex:   # pragma: no cover
                self.last_err = str(ex)[:200]
                logger.warning("v126 watch: %s", ex)
            try:
                lt = time.localtime(); sec = lt.tm_hour * 3600 + lt.tm_min * 60
                if lt.tm_wday < 5 and CONT_FROM + 300 <= sec <= CONT_TO + 600:
                    self._check_akk()
                    self._check_trn()
            except Exception as ex:   # pragma: no cover
                self.last_err = str(ex)[:200]
                logger.warning("v126 watch: %s", ex)
            time.sleep(60)

    def _check(self):
        rules = self.watch.get("rules") or []
        if not rules or self.hub is None:
            return
        lt = time.localtime()
        sec = lt.tm_hour * 3600 + lt.tm_min * 60
        if lt.tm_wday >= 5 or not (CONT_FROM + 300 <= sec <= CONT_TO + 600):
            return
        d = self.feed._akd_date()
        if d != _today():
            return
        with self.lock:
            if self.watch.get("day") != d:
                self.watch["day"] = d; self.watch["seen"] = {}
            seen = self.watch["seen"]
        rows = self.feed.broker_positions()["rows"]
        AK = {}
        if any(r.get("min_aa") for r in rules):
            try:
                AK = self._aktif(d)[0]
            except Exception:
                AK = {}
        now = time.time()
        while self.wrate and now - self.wrate[0] > 3600:
            self.wrate.popleft()
        n = 0
        for r in rules:
            for x in rows:
                if n >= 5 or len(self.wrate) >= 30:
                    break
                if not self._match(r, x, AK):
                    continue
                k = f"{r['id']}|{x['s']}|{x['b']}"
                if k in seen:
                    continue
                seen[k] = 1
                n += 1
                self.wrate.append(now)
                side = "net alıcı" if x["nl"] > 0 else "net satıcı"
                tl = abs(x["nl"] * (x.get("p") or x.get("co") or 0))
                title = f"🏦 {_bn(x['b'])} · {x['s']} {side} %{_f1(abs(x.get('np') or 0))}"
                txt = (f"Net {_fs(abs(x['nl']))} lot (≈{_fs(tl)} ₺) · maliyet {_fp(x.get('co'))} · son {_fp(x.get('p'))}"
                       f" · K/Z {_fpct(x.get('kzp'))} · kural: {r.get('name') or ', '.join(r['brokers'][:3])} ≥%{_f1(r['min_np'])}")
                if r.get("min_aa"):
                    aa, _, as_ = self._apct(((AK or {}).get(x["s"]) or {}).get(x["b"]))
                    v = aa if r["side"] == "buy" else as_
                    txt += f" · aktif {'alış' if r['side'] == 'buy' else 'satış'} %{_f1(v or 0)} (≥%{_f1(r['min_aa'])})"
                try:
                    self.hub._emit("olay", NT_AKDT, x["s"], title, txt, {"f": "akd_tarama", "br": x["b"], "price": x.get("p")})
                    self.emitted += 1
                except Exception as ex:   # pragma: no cover
                    logger.debug("v126 emit: %s", ex)
        with self.lock:
            self._save()

    def status(self):
        return {"version": VERSION, "flow_cache": len(self.fcache), "tarama_cache": list(self.tcache), "watch_rules": len(self.watch.get("rules") or []),
                "watch_loops": self.loops, "emitted": self.emitted, "last_err": self.last_err,
                "akk_on": bool(self.akk.get("on")), "akk_emitted": self.akk_emitted,
                "trn_on": bool(self.trn.get("on")), "trn_emitted": self.trn_emitted}


def tahtaci_sig(rows, A, min_tl=2e6):
    """v1.26.2 TAHTACI SİNYALİ. rows: AKD satırları ({br, net, pct (net payı %), co}); A: {kurum: [bl, abl, btl, abtl, sl, asl, stl, astl]} (aynı hisse, aynı gün).
    YUKARI: AKD'de en çok net alan (ya da ilk 3) kurum aynı zamanda hissede EN ÇOK AKTİF ALAN (aktif alış lotu).
      güçlü: 1. net alıcı + en çok aktif alan + aktif alış ≥%65 + net alımın ≥%25'i + hissedeki aktif alışın ≥%25'i + hisse ortalamasının ≥12 puan üstü;
      orta : ilk 3 net alıcıdan biri en çok aktif alan (aktif ≥%60, payı ≥%15, ort.+8) ya da 1. net alıcı aktif ≥%65, payı ≥%20, ort.+8.
    AŞAĞI: aynısı net satıcı + aktif satış (ort. = hissenin aktif satış lotu ÷ satış lotu). Her iki yönde en az 2 Mn ₺ aktif işlem şartı."""
    out = []
    if not A:
        return out
    for side in ("up", "dn"):
        if side == "up":
            lst = sorted((r for r in rows if (r.get("net") or 0) > 0), key=lambda r: -r["net"])
            ia, it, itl = 1, 0, 3
        else:
            lst = sorted((r for r in rows if (r.get("net") or 0) < 0), key=lambda r: r["net"])
            ia, it, itl = 5, 4, 7
        if not lst:
            continue
        tot_a = sum(y[ia] for y in A.values())
        if tot_a <= 0:
            continue
        top_a = max(A.items(), key=lambda kv: kv[1][ia])[0]
        tt = sum(y[it] for y in A.values())
        avg = tot_a / tt * 100.0 if tt > 0 else 0.0
        for i, r in enumerate(lst[:3]):
            y = A.get(r["br"])
            if not y or y[it] <= 0 or y[itl] < min_tl:
                continue
            ap = y[ia] / y[it] * 100.0
            sh = y[ia] / tot_a * 100.0
            npct = abs(r.get("pct") or 0.0)
            top = r["br"] == top_a
            rel = ap - avg
            if i == 0 and top and ap >= 65 and npct >= 25 and sh >= 25 and rel >= 12:
                g = "güçlü"
            elif top and ap >= 60 and sh >= 15 and rel >= 8:
                g = "orta"
            elif i == 0 and ap >= 65 and sh >= 20 and rel >= 8:
                g = "orta"
            else:
                continue
            b = _bn(r["br"])
            if side == "up":
                who = "en çok net alan" if i == 0 else f"ilk 3 net alıcıdan ({i + 1}.)"
                act = "en çok aktif alan" if top else "yüksek aktif alışlı"
                tail = "fiyatı yukarı sürüyor olabilir"
                ex = f"aktif %{_f1(ap)} — hisse ort. %{_f1(avg)}; hissedeki aktif alışın {_pe(sh)}"
            else:
                who = "en çok net satan" if i == 0 else f"ilk 3 net satıcıdan ({i + 1}.)"
                act = "en çok aktif satan" if top else "yüksek aktif satışlı"
                tail = "fiyatı aşağı bastırıyor olabilir"
                ex = f"aktif satış %{_f1(ap)} — hisse ort. %{_f1(avg)}; hissedeki aktif satışın {_pe(sh)}"
            np_txt = f"net {'alımın' if side == 'up' else 'satışın'} {_pe(npct)}"
            extra = "" if top else f"; en çok aktif {'alan' if side == 'up' else 'satan'}: {_bn(top_a)}"
            text = f"⚠ TAHTACI SİNYALİ ({g}): {b} hem AKD'de {who} kurum ({np_txt}) hem de {act} kurum ({ex}{extra}) — {tail}."
            out.append({"side": side, "grade": g, "br": r["br"], "rank": i + 1, "top": top, "ap": _r(ap, 1), "share": _r(sh, 1), "npct": _r(npct, 1), "avg": _r(avg, 1),
                        "al": y[ia], "atl": round(y[itl]), "net": r["net"], "co": r.get("co"), "top_a": top_a, "text": text})
            break
    return out


def _tavan(pc):
    """BIST ±%10 tavan fiyatı (fiyat adımına aşağı yuvarlanır; v1.24 _lim ile aynı)."""
    if not pc:
        return None
    up = pc * 1.1
    t = _tick_size(up)
    return round(int(up / t + 1e-6) * t, 4)


def tren_eval(nl, rb, wb, np_, aa, abtl):
    """v1.26.3 TAVAN TRENİ → (derece 0/1/2, [4 koşul]). nl: net lot; rb: AKD Alış sırası (net alıcılar); wb: alış lotu sırası (balina);
    np_: net pay % (AKD DAĞILIM); aa: aktif alış % (lot); abtl: aktif alış ₺."""
    if not nl or nl <= 0:
        return 0, None
    c = [rb == 1 or wb == 1, (np_ or 0) >= TRN_P["np"], aa is not None and aa >= TRN_P["aa"], (abtl or 0) >= TRN_P["tl"]]
    if not all(c):
        return 0, c
    return (2 if rb == 1 and abtl >= TRN_P["tl_g"] else 1), c


def tren_sig(rows, A):
    """v1.26.3 hisse için TAVAN TRENİ (AKD satırları + aktif alış). En iyi aday (derece, aktif ₺) döner: [] ya da [dict]."""
    if not A or not rows:
        return []
    nb = sorted((r for r in rows if (r.get("net") or 0) > 0), key=lambda r: -r["net"])
    if not nb:
        return []
    rbk = {r["br"]: i + 1 for i, r in enumerate(nb)}
    wbk = {r["br"]: i + 1 for i, r in enumerate(sorted(rows, key=lambda r: -(r.get("bl") or 0)))}
    best = None
    for r in nb:
        rb, wb = rbk[r["br"]], wbk.get(r["br"])
        if rb != 1 and wb != 1:
            continue
        y = A.get(r["br"])
        if not y or y[0] <= 0:
            continue
        aa = round(y[1] / y[0] * 100.0, 1)
        abtl = round(y[3])
        np_ = _r(r.get("pct"), 2)
        g, c = tren_eval(r["net"], rb, wb, np_, aa, abtl)
        if g and (best is None or (g, abtl) > (best[0], best[5])):
            best = (g, r, rb, wb, aa, abtl, np_, c)
    if not best:
        return []
    g, r, rb, wb, aa, abtl, np_, c = best
    G = "GÜÇLÜ" if g == 2 else "ORTA"
    b = _bn(r["br"])
    who = "AKD Alış #1" if rb == 1 else f"alış lotunda en büyük alıcı, AKD Alış #{rb}"
    chk = [{"l": "AKD Alış #1 / en büyük balina", "ok": c[0], "v": f"Alış #{rb}" + ("" if wb != 1 else " · en büyük alış lotu")},
           {"l": f"net pay ≥ %{TRN_P['np']:g}", "ok": c[1], "v": f"%{_f1(np_)}"},
           {"l": f"aktif alış ≥ %{TRN_P['aa']:g}", "ok": c[2], "v": f"%{_f1(aa)}"},
           {"l": f"aktif alış ≥ {_fs(TRN_P['tl'])} ₺ (GÜÇLÜ: Alış #1 + ≥ {_fs(TRN_P['tl_g'])} ₺)", "ok": c[3], "v": f"{_fs(abtl)} ₺"}]
    text = (f"🚂 TAVAN TRENİ ({G}): {b} hissenin en büyük balinası ({who}; net alımın {_pe(np_)}, net {_fs(r['net'])} lot) ve alımının "
            f"{_pe(aa, True)} AKTİF (piyasa emriyle, satıcıya vurarak) yaptı ({_fs(abtl)} ₺ aktif alış). Açgözlü alıcı: ralli trenini çekiyor / çekti.")
    return [{"kind": "tren", "side": "up", "grade": "güçlü" if g == 2 else "orta", "G": G, "tt": g, "br": r["br"], "rank": rb, "wb": wb,
             "npct": np_, "ap": aa, "atl": abtl, "net": r["net"], "co": r.get("co"), "chk": chk, "text": text}]


def tht_merge(rows, A):
    """v1.26.3 TAHTACI SİNYALİ + TAVAN TRENİ birleşik liste (tren önce; aynı kurumun TAHTACI ↑ satırı trene katılır)."""
    th = tahtaci_sig(rows, A)
    tr = tren_sig(rows, A)
    if not tr:
        return th
    t = tr[0]
    rest = []
    for x in th:
        if x["side"] == "up" and x["br"] == t["br"]:
            t["tht"] = x["grade"]
            t["text"] += (f" Aynı kurum TAHTACI ↑ ({x['grade']}): hissedeki aktif alışın {_pe(x['share'])} (hisse ort. aktif %{_f1(x['avg'])}).")
        else:
            rest.append(x)
    return [t] + rest


def _durum(b3, s3, nb, ns):
    if b3 >= 55 and (nb <= ns or b3 - s3 >= 15):
        return "TOPLAMA"
    if s3 >= 55 and (ns <= nb or s3 - b3 >= 15):
        return "DAĞITIM"
    return "NÖTR"


v126 = V126()
