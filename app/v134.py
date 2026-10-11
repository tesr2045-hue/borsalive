"""v1.34.0 — ✅ AL BUNU · TAVAN ADAYI: "ne alsam?" sorusuna TEK liste.

Yeni skor uydurmaz; mevcut canlı İdealData analizlerini bir VE-kapısıyla (hepsi zorunlu) birleştirir, az ama net hisse çıkar.

ZORUNLU KOŞULLAR (hepsi; eşikler data/v134/albunu.json {"th": {...}} ile yeniden başlatmadan ayarlanır):
  K1 Lider kurum (v1.23 Maliyet Yükselten, işlem işlem): bugün net alıcı · ciddiyet ≥55 · aktif alış ≥%55 · alış ≥3 Mn ₺ ·
     hacim payı ≥%8 · maliyetini yükseltiyor (≥3 yükseltme, maliyet artışı > 0)
  K2 HÂLÂ İTİYOR (işlem kaydı, son 15 dk): lider kurum ≥250 bin ₺ aldı, 15 dk'da net alıcı, bu alışların ≥%50'si aktif,
     son alışı ≤5 dk önce
  A1 AKD (v1.26 AKD Taraması, AKD sekmesi Günlük ile aynı kayıt): lider kurum net alıcılar içinde ilk 3'te, net payı ≥%15
  A2 Dağıtım yok: AKD durumu DAĞITIM ve satıcı yoğunlaşması alıcıdan ≥8 puan fazla değil
  A3 Tahtacı satış baskın değil: Satış #1 kurum aktif satış ≥%60 + net payı ≥%25 + aktif satış ₺ ≥ lider aktif alış ₺ × 0,7 ise ELENİR
  F1 Fiyat hâlâ yukarı: gün ≥ +%1,5 · gün yükseğinden en çok %1,5 geride · son 15 dk ≥ 0 (tavanda ise geçerli)
  F2 Geç değil: tavanda DEĞİLSE tavana ≥%1,5 yer var · TAVANDA ise tavan alış kuyruğu ≥3 Mn ₺ (kuyruk büyüyor/duruyor)
  D1 Derinlik destekli: D-A-K ≥55 · sayfa Derinlik skoru ≥44 (satış ağırlıklı değil)
  D2 Üstte Algo Direnç ezmiyor: fiyatın %2,5 yakınında, algo destekten 2 kat büyük algo direnç yok
  M1 Momentum kanıtı (en az biri): TAVAN TRENİ (AKD #1 + aktif alış) · CİDDİ YÜKSELİŞ / TAVAN ADAYI senaryosu · bugün TRENE ATLA
     (fiyat sinyal fiyatının altına düşmemiş)
GÜVEN (0–100) = kurum 30 + hâlâ itiyor 15 + AKD 20 + senaryo/momentum 15 + derinlik 20. Liste güvene göre sıralı, en çok 12 hisse,
güven ≥55 (listedeyken ≥50'de kalır; D-A-K −3, Derinlik −4, gün −0,5 puan gevşek tutma eşikleri — titreşim yok). Beklenti: TAVAN (tavan senaryosu / tavanda kuyruklu / güçlü tren + tavana ≤%5) ya da DEVAM.
Stop önerisi: lider kurumun ortalama maliyeti (fiyatın %1–5 altındaysa) → yoksa −%3; tavanda: kuyruk 1 Mn ₺ altına inerse çık.
Bildirim (al_bunu): kullanıcı cihazında varsayılan KAPALI; yalnız listeye YENİ giren, güveni ≥70, iki döngü üst üste listede kalan hisse;
hisse başına günde 1, saatte en çok 3, 10:15–17:30. Yatırım tavsiyesi değildir.
"""
from __future__ import annotations

import bisect
import collections
import json
import logging
import threading
import time

from app.v122 import CONT_FROM, _fp, _fs, _hms, _sec_now

logger = logging.getLogger("bist.v134")
VERSION = "1.34.0"
NT = "al_bunu"
NT_DEFAULT = "off"
LOOP = 10.0
TH_DEF = {"sc": 55, "akt": 55.0, "btl": 3e6, "pay": 8.0, "ys": 3, "l15_tl": 250e3, "l15_akt": 50.0, "l_last": 300, "np": 15.0, "rb": 3,
          "dg_gap": 8.0, "tht_as": 60.0, "tht_np": 25.0, "tht_r": 0.7, "gd_min": 1.5, "fade": 1.5, "room": 1.5, "q_tl": 3e6, "dak": 55,
          "dp": 44, "alg_dist": 2.5, "alg_r": 2.0, "min_score": 55, "keep_score": 50, "cap": 12, "win": 900}
CFG_DEF = {"on": True, "min_sc": 70, "rate": 3, "t0": 10 * 3600 + 900, "t1": 17 * 3600 + 1800, "persist": 2}
TH = dict(TH_DEF)
CFG = dict(CFG_DEF)
DATA = VDIR = None
try:
    from app import v130 as _v130
    DATA = _v130.DATA
    VDIR = DATA / "v134"
except Exception:   # pragma: no cover
    pass


def _load():
    try:
        d = json.loads((VDIR / "albunu.json").read_text(encoding="utf-8"))
        for k, v in (d.get("th") or {}).items():
            if k in TH_DEF:
                TH[k] = type(TH_DEF[k])(v)
        for k, v in (d.get("cfg") or {}).items():
            if k in CFG_DEF:
                CFG[k] = type(CFG_DEF[k])(v)
    except Exception:
        pass


def _pc(v, d=1):
    if v is None:
        return "—"
    s = f"{abs(v):.{d}f}".replace(".", ",")
    return ("+%" if v >= 0 else "−%") + s


def _p1(v):
    return f"{v:.0f}" if v is not None else "—"


def _bn(n):
    try:
        from app.v126 import _bn as b
        return b(n)
    except Exception:
        return str(n or "")


def _clip(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


class AlBunu:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.feed = self.m = self.b = self.akd = self.skor = self.algo = self.tren = self.hub = None
        self.thread = None
        self.res = {"rows": [], "near": [], "ts": None}
        self.day = None
        self.first: dict = {}      # sym → {"t": sn, "p": fiyat, "sc": güven}
        self.gone: dict = {}       # sym → {"t", "p", "why"}
        self.seen: dict = {}       # sym → art arda listede kalınan döngü
        self.fired: dict = {}
        self.rate = collections.deque()
        self.sent = collections.deque(maxlen=50)
        self.qhist: dict = {}      # sym → deque[(sn, kuyruk ₺)]
        self.loops = self.errors = 0
        self.last_err = None
        self.ms = None
        self.started = None

    def start(self, feed, m, b, akd, skor, algo, tren, hub) -> None:
        self.feed, self.m, self.b, self.akd, self.skor, self.algo, self.tren, self.hub = feed, m, b, akd, skor, algo, tren, hub
        self.started = time.strftime("%H:%M:%S")
        self._restore()
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name="v134-albunu", daemon=True)
            self.thread.start()

    # ------------------------------------------------------------------ kalıcılık
    def _file(self, day):
        return VDIR / f"{day}.json" if VDIR is not None and day else None

    def _restore(self):
        try:
            day = self.m._resolve_day(None)[0]
            f = self._file(day)
            if f and f.exists():
                d = json.loads(f.read_text(encoding="utf-8"))
                self.day = day
                self.first = d.get("first") or {}
                self.gone = d.get("gone") or {}
                self.fired = {k: int(v) for k, v in (d.get("fired") or {}).items()}
        except Exception as ex:
            logger.warning("v134 restore: %s", ex)

    def _save(self):
        try:
            f = self._file(self.day)
            if not f:
                return
            VDIR.mkdir(parents=True, exist_ok=True)
            tmp = f.with_suffix(".tmp")
            tmp.write_text(json.dumps({"first": self.first, "gone": self.gone, "fired": self.fired, "v": VERSION}, ensure_ascii=False), encoding="utf-8")
            tmp.replace(f)
        except Exception as ex:
            logger.warning("v134 save: %s", ex)

    def _loop(self) -> None:
        time.sleep(45)
        while True:
            t0 = time.time()
            try:
                _load()
                self.step()
                self.loops += 1
            except Exception as ex:
                self.errors += 1
                self.last_err = f"{type(ex).__name__}: {ex}"
                logger.exception("v134 loop")
            dt = time.time() - t0
            self.ms = round(dt * 1000)
            time.sleep(max(2.0, LOOP - dt))

    # ------------------------------------------------------------------ veri
    def _skor(self):
        try:
            L = self.skor.listing()
            c = L.get("cols") or []
            return {r[0]: dict(zip(c, r)) for r in (L.get("rows") or [])}
        except Exception:
            return {}

    def _algo(self):
        try:
            L = self.algo.listing()
            return {x["s"]: x for x in (L.get("b") or [])}, {x["s"]: x for x in (L.get("a") or [])}
        except Exception:
            return {}, {}

    def _akd(self):
        A = self.akd.tarama(None, None)
        sc = {c: i for i, c in enumerate(A["cols"]["stocks"])}
        rc = {c: i for i, c in enumerate(A["cols"]["rows"])}
        stocks = A.get("stocks") or []
        brs = A.get("brokers") or []
        per = collections.defaultdict(list)
        for r in A.get("rows") or []:
            per[r[0]].append(r)
        out = {}
        for i, st in enumerate(stocks):
            out[st[0]] = (st, per.get(i, []))
        return out, sc, rc, brs, A.get("date")

    def _quote(self, s):
        f = self.feed
        with f._lock:
            q = f.quotes.get(s) or {}
            v = (q.get("last"), q.get("ceiling"), q.get("floor"), q.get("bid"), q.get("ask"), q.get("bid_size"), q.get("ask_size"),
                 q.get("prev_close"), f.depth.get(s) or {})
            hi = q.get("high")
        try:
            x = self.hub.tavan_state(s, v)
        except Exception:
            x = {"p": v[0], "ceil": v[1]}
        x["hi"] = hi
        x["pc"] = v[7]
        return x

    def _win(self, day, sym, lead, ref, W):
        """İşlem kaydından son W sn: lider kurum alış/satış, aktif payı, son alış; hisse fiyatı W önce, gün yükseği, aktif alış payı."""
        _, syms, brokers, lock, _ = self.m._src(day)
        e = syms.get(sym)
        if e is None:
            return None
        with lock:
            names = list(brokers)
            try:
                bi = names.index(lead)
            except ValueError:
                bi = None
            n = min(len(e.t), len(e.p), len(e.l), len(e.sd), len(e.b), len(e.s))
            if not n:
                return None
            i0 = bisect.bisect_left(e.t, ref - W, 0, n)
            T = e.t[i0:n]; P = e.p[i0:n]; L = e.l[i0:n]; SD = e.sd[i0:n]; B = e.b[i0:n]; S = e.s[i0:n]
            hi = max(e.p[:n])
            p_w = e.p[i0 - 1] if i0 > 0 else e.p[0]
            last = e.p[n - 1]
            last_t = e.t[n - 1]
        bl = btl = abl = sl = 0.0
        lb_t = None
        al = tl = 0.0
        for t, p, l, sd, b, s in zip(T, P, L, SD, B, S):
            tl += l
            if sd == 1:
                al += l
            if bi is not None and b == bi:
                bl += l; btl += l * p
                if sd == 1:
                    abl += l
                lb_t = t
            if bi is not None and s == bi:
                sl += l
        return {"bl": bl, "btl": btl, "aa": (abl / bl * 100.0) if bl else 0.0, "net": bl - sl, "lb_t": lb_t, "p_w": p_w, "hi": hi,
                "last": last, "last_t": last_t, "saa": (al / tl * 100.0) if tl else None}

    # ------------------------------------------------------------------ hesap
    def step(self):
        m = self.m
        day, live = m._resolve_day(None)
        if not day:
            return
        R = m.days.get(day)
        if R is None or not R.ready:
            self.res = {"rows": [], "near": [], "ts": time.strftime("%H:%M:%S"), "pending": True, "day": day, "live": live}
            return
        if day != self.day:
            self.day = day
            self.first, self.gone, self.fired, self.seen, self.qhist = {}, {}, {}, {}, {}
        ref = _sec_now() if live else int(R.ref or 0)
        if live and R.ref:
            ref = max(int(R.ref), min(ref, int(R.ref) + 120))
        pz = None
        try:
            pz = self.b.preset_for(day)
        except Exception:
            pz = None
        cset, tset, chk = (pz[1], pz[2], pz[3]) if pz else (set(), set(), {})
        AK, si, ri, brs, akd_day = self._akd()
        SK = self._skor()
        AB, AA = self._algo()
        TR = collections.defaultdict(list)
        try:
            if getattr(self.tren, "day", None) == day:
                for g in list(self.tren.sig):
                    TR[g["s"]].append(g)
        except Exception:
            pass
        try:
            Bd = self.b.days.get(day)
            BST = Bd.st if Bd is not None else {}
        except Exception:
            BST = {}
        th = TH
        W = int(th["win"])
        # K1: hisse başına en iyi lider kurum adayı
        cand = collections.defaultdict(list)
        for r in R.rows:
            if (r["sc"] >= th["sc"] and r["akt"] >= th["akt"] and r["btl"] >= th["btl"] and r["pay"] >= th["pay"] and r["chg"] > 0
                    and r["ys"] >= th["ys"] and r["still"] != "—"):
                cand[r["s"]].append(r)
        rows, near = [], []
        prev = {x["s"] for x in self.res.get("rows") or []}
        TK = dict(TH)   # listedeki hisse için gevşek tutma eşikleri (titreşim olmasın)
        TK.update({"dak": TH["dak"] - 3, "dp": TH["dp"] - 4, "gd_min": TH["gd_min"] - 0.5, "fade": TH["fade"] + 0.5, "l_last": TH["l_last"] + 120,
                   "l15_akt": TH["l15_akt"] - 5})
        for s, rs in cand.items():
            th = TK if s in prev else TH
            rs.sort(key=lambda r: (-r["sc"], -r["btl"]))
            ak = AK.get(s)
            fails = []
            Lr = rs[0]
            # A1 — lider kurum AKD'de ilk 3 net alıcı (adaylar içinden AKD'de en güçlü olanı seç)
            st, arows = ak if ak else (None, [])
            byb = {brs[x[ri["bi"]]]: x for x in arows} if arows else {}
            best = None
            for r in rs:
                x = byb.get(r["br"])
                if x is not None and (x[ri["rb"]] or 99) <= th["rb"] and (x[ri["np"]] or 0) >= th["np"]:
                    best = (r, x)
                    break
            if best is None:
                x = byb.get(Lr["br"])
                fails.append(f"AKD: {_bn(Lr['br'])} " + (f"Alış #{x[ri['rb']]} · net pay %{_p1(x[ri['np']])}" if x is not None and x[ri["rb"]] else "net alıcı listesinde ilk 3'te değil"))
                L, X = Lr, x
            else:
                L, X = best
            q = self._quote(s)
            p = q.get("p") or L.get("p")
            pc = q.get("pc")
            gd = round((p / pc - 1) * 100, 2) if (p and pc) else L.get("gd")
            bst = BST.get(s)
            tv = (bst.tv if bst is not None and getattr(bst, "tv", None) else None) or q.get("ceil")
            at_t = bool(tv and p and p >= tv - 1e-9 and (q.get("at_ceil") or not q.get("ask") or (q.get("bid") or 0) >= tv - 1e-9))
            room = round((tv - p) / p * 100, 2) if (tv and p) else None
            qtl = (q.get("ceil_lot") or 0) * (tv or 0) if at_t else 0.0
            # A2 / A3
            if st is not None:
                if st[si["durum"]] == "DAĞITIM" and (st[si["s3"]] or 0) - (st[si["b3"]] or 0) >= th["dg_gap"]:
                    fails.append(f"AKD DAĞITIM (satıcı ilk 3 %{_p1(st[si['s3']])} > alıcı %{_p1(st[si['b3']])})")
                ts = next((x for x in arows if x[ri["rs"]] == 1), None)
                if ts is not None and X is not None:
                    a_s = ts[ri["as"]] or 0; astl = ts[ri["astl"]] or 0; lab = X[ri["abtl"]] or 0
                    if a_s >= th["tht_as"] and abs(ts[ri["np"]] or 0) >= th["tht_np"] and astl >= th["tht_r"] * max(lab, 1):
                        fails.append(f"tahtacı satış: {_bn(brs[ts[ri['bi']]])} aktif satış %{_p1(a_s)} ({_fs(astl)} ₺)")
            else:
                fails.append("AKD yok")
            # K2 — hâlâ itiyor
            w = self._win(day, s, L["br"], ref, W)
            if w is None:
                fails.append("işlem kaydı yok")
                w = {"bl": 0, "btl": 0, "aa": 0, "net": 0, "lb_t": None, "p_w": None, "hi": None, "last": p, "last_t": None, "saa": None}
            else:
                if w["btl"] < th["l15_tl"]:
                    fails.append(f"{_bn(L['br'])} son 15 dk yalnız {_fs(w['btl'])} ₺ aldı")
                elif w["net"] <= 0:
                    fails.append(f"{_bn(L['br'])} son 15 dk net SATICI")
                elif w["aa"] < th["l15_akt"]:
                    fails.append(f"{_bn(L['br'])} son 15 dk aktif alış %{_p1(w['aa'])} (pasif topluyor)")
                if w["lb_t"] is None or ref - w["lb_t"] > th["l_last"]:
                    fails.append(f"{_bn(L['br'])} son alış {_hms(w['lb_t']) if w['lb_t'] else '—'} (≥5 dk önce)")
            hi = max(x for x in (w.get("hi"), q.get("hi"), p) if x)
            fade = round((hi - p) / hi * 100, 2) if hi and p else 0.0
            m15 = round((p / w["p_w"] - 1) * 100, 2) if (w.get("p_w") and p) else None
            # F1 / F2
            if gd is None or gd < th["gd_min"]:
                fails.append(f"gün {_pc(gd)} (< +%{th['gd_min']:g})".replace(".", ","))
            if not at_t:
                if fade > th["fade"]:
                    fails.append(f"zirveden %{fade:.1f} geride (yükseliş sönüyor)".replace(".", ","))
                if m15 is not None and m15 < 0:
                    fails.append(f"son 15 dk {_pc(m15)}")
                if room is not None and room < th["room"]:
                    fails.append(f"tavana yalnız %{room:.1f} yer (geç)".replace(".", ","))
            else:
                qh = self.qhist.setdefault(s, collections.deque(maxlen=30))
                qh.append((ref, qtl))
                q60 = next((v for t, v in qh if ref - t <= 90), qtl)
                if qtl < th["q_tl"]:
                    fails.append(f"tavanda ama kuyruk zayıf ({_fs(qtl)} ₺)")
                elif q60 and qtl < q60 * 0.7:
                    fails.append(f"tavan kuyruğu eriyor ({_fs(q60)} → {_fs(qtl)} ₺)")
            # D1 / D2
            k = SK.get(s) or {}
            dak, dp = k.get("dak"), k.get("dp")
            if dak is None or dak < th["dak"]:
                fails.append(f"D-A-K {_p1(dak)} (< {th['dak']})")
            if dp is not None and dp < th["dp"]:
                fails.append(f"sayfa Derinlik {_p1(dp)} (< {th['dp']})")
            ab, aa = AB.get(s), AA.get(s)
            if aa and not at_t and (aa.get("dist") or 99) <= th["alg_dist"] and (aa.get("tl") or 0) >= th["alg_r"] * ((ab or {}).get("tl") or 0):
                fails.append(f"üstte Algo Direnç {_fp(aa.get('p0'))} ({aa.get('pat')})")
            # M1
            tt = 0; tt_br = None
            for x in arows:
                if (x[ri["tt"]] or 0) > tt:
                    tt = x[ri["tt"]]; tt_br = brs[x[ri["bi"]]]
            tvn = s in tset; cid = s in cset
            tg = [g for g in TR.get(s, []) if p and p >= g["p"] * 0.995]
            if not (tt or tvn or cid or tg):
                fails.append("momentum kanıtı yok (tren / senaryo / TRENE ATLA)")
            # GÜVEN
            npc = (X[ri["np"]] if X is not None else 0) or 0
            sc_k = min(20.0, L["sc"] * 0.2) + min(10.0, L["israr"] * 0.1)
            sc_s = _clip(w["btl"] / 2e6) * 8 + _clip((w["aa"] - 40) / 60) * 7
            sc_a = _clip(npc / 60) * 12 + (8 if tt == 2 else 4 if tt == 1 else 0)
            sc_m = (8 if tvn else 5 if cid else 0) + (4 if tg else 0) + (3 if (at_t or fade <= 0.5) else 0)
            sc_d = _clip(((dak or 50) - 50) / 30) * 10 + _clip(((dp if dp is not None else 50) - 50) / 30) * 6 + (4 if ab else 0)
            score = int(round(min(100.0, sc_k + sc_s + sc_a + sc_m + sc_d)))
            exp = "TAVAN" if (tvn or (at_t and qtl >= th["q_tl"]) or (tt == 2 and room is not None and room <= 5)) else "DEVAM"
            # stop
            cost = L.get("cur")
            if at_t:
                stop, stop_w = None, "tavan kuyruğu 1 Mn ₺ altına inerse / tavan çözülürse çık"
            elif cost and p and 1.0 <= (p - cost) / p * 100 <= 5.0:
                stop, stop_w = round(cost, 2), f"{_bn(L['br'])} ortalama maliyeti"
            else:
                stop, stop_w = round(p * 0.97, 2) if p else None, "−%3"
            akt_l = X[ri["aa"]] if X is not None else L["akt"]
            why = (f"{_bn(L['br'])} net %{_p1(npc)} · aktif %{_p1(akt_l if akt_l is not None else L['akt'])} · {_fs(L['btl'])} ₺ aldı, "
                   f"son 15 dk {_fs(w['btl'])} ₺ (%{_p1(w['aa'])} aktif) — hâlâ itiyor")
            tags = []
            if tt:
                tags.append("TAVAN TRENİ " + ("GÜÇLÜ" if tt == 2 else "ORTA"))
            if tvn:
                tags.append("TAVAN ADAYI")
            elif cid:
                tags.append("CİDDİ YÜKSELİŞ")
            if tg:
                tags.append(f"TRENE ATLA {tg[-1]['time'][:5]}")
            if ab:
                tags.append("ALGO DESTEK")
            if at_t:
                tags.append(f"TAVANDA · kuyruk {_fs(qtl)} ₺")
            row = {"s": s, "p": p, "gd": gd, "sc": score, "exp": exp, "at_t": at_t, "tv": tv, "room": room, "qtl": round(qtl) if qtl else None,
                   "br": L["br"], "brn": _bn(L["br"]), "np": npc, "akt": akt_l, "msc": L["sc"], "israr": L["israr"], "btl": L["btl"],
                   "cost": round(cost, 4) if cost else None, "dr": L.get("dr"), "ft": L.get("ft"), "lt": _hms(w["lb_t"]) if w["lb_t"] else None,
                   "l15": round(w["btl"]), "l15a": round(w["aa"], 1), "l15n": round(w["net"]), "saa": round(w["saa"], 1) if w["saa"] is not None else None,
                   "m15": m15, "fade": fade, "hi": hi, "dak": dak, "dp": dp, "d": k.get("d"), "a": k.get("a"), "k": k.get("k"),
                   "tt": tt, "tt_br": _bn(tt_br) if tt_br else None, "tvn": tvn, "cid": cid, "tren": [{"t": g["time"], "p": g["p"]} for g in tg][-3:],
                   "ab": {"pat": ab["pat"], "p0": ab["p0"], "p1": ab["p1"], "tl": ab["tl"]} if ab else None,
                   "aa": {"pat": aa["pat"], "p0": aa["p0"], "p1": aa["p1"], "tl": aa["tl"], "dist": aa.get("dist")} if aa else None,
                   "stop": stop, "stop_w": stop_w, "why": why, "tags": tags,
                   "parts": {"kurum": round(sc_k, 1), "itiyor": round(sc_s, 1), "akd": round(sc_a, 1), "momentum": round(sc_m, 1), "derinlik": round(sc_d, 1)}}
            need = th["keep_score"] if s in prev else th["min_score"]
            if not fails and score < need:
                fails.append(f"güven {score} (< {need})")
            if fails:
                if len(fails) <= 2 and (gd or 0) >= 0:
                    near.append({"s": s, "p": p, "gd": gd, "sc": score, "brn": _bn(L["br"]), "why": fails})
                continue
            rows.append(row)
        th = TH
        rows.sort(key=lambda r: (-r["sc"], -(r["btl"] or 0)))
        rows = rows[: int(th["cap"])]
        near.sort(key=lambda r: (len(r["why"]), -r["sc"]))
        now_ids = {r["s"] for r in rows}
        # giriş / çıkış kaydı
        nearw = {x["s"]: x["why"] for x in near}
        for r in rows:
            f = self.first.get(r["s"])
            if f is None or r["s"] in self.gone:
                self.first[r["s"]] = f = {"t": ref, "p": r["p"], "sc": r["sc"]}
                self.gone.pop(r["s"], None)
            r["in_t"] = _hms(f["t"]); r["in_p"] = f["p"]
            r["in_chg"] = round((r["p"] / f["p"] - 1) * 100, 2) if (r["p"] and f["p"]) else None
            self.seen[r["s"]] = self.seen.get(r["s"], 0) + 1
        for s in list(prev - now_ids):
            self.seen.pop(s, None)
            f = self.first.get(s)
            q = self._quote(s)
            self.gone[s] = {"t": ref, "p": q.get("p"), "in_t": f["t"] if f else None, "in_p": f["p"] if f else None,
                            "why": (nearw.get(s) or ["koşullardan biri bozuldu"])[:2]}
        gone = []
        for s, g in sorted(self.gone.items(), key=lambda kv: -kv[1]["t"])[:20]:
            gq = self._quote(s).get("p")
            gone.append({"s": s, "t": _hms(g["t"]), "p": g["p"], "now": gq, "in_t": _hms(g["in_t"]) if g.get("in_t") else None, "in_p": g.get("in_p"),
                         "res": round((g["p"] / g["in_p"] - 1) * 100, 2) if (g.get("p") and g.get("in_p")) else None, "why": g["why"]})
        if live:
            self._notify(day, rows, ref)
        self.res = {"rows": rows, "near": near[:12], "gone": gone, "ts": time.strftime("%H:%M:%S"), "ref": _hms(ref), "day": day, "live": live,
                    "n_cand": len(cand), "akd_day": akd_day, "epoch": time.time()}
        self._save()

    # ------------------------------------------------------------------ bildirim
    def _notify(self, day, rows, ref):
        if not CFG.get("on", True) or self.hub is None:
            return
        if not (CFG["t0"] <= ref <= CFG["t1"]):
            return
        wall = time.time()
        while self.rate and wall - self.rate[0] > 3600:
            self.rate.popleft()
        for r in rows:
            s = r["s"]
            if r["sc"] < CFG["min_sc"] or s in self.fired or self.seen.get(s, 0) < CFG["persist"]:
                continue
            if len(self.rate) >= CFG["rate"]:
                break
            self.fired[s] = ref
            self.rate.append(wall)
            title = f"✅ AL BUNU · {s} · {_fp(r['p'])}"
            body = (f"{'TAVAN beklentisi' if r['exp'] == 'TAVAN' else 'Yükseliş devam beklentisi'} · güven {r['sc']} · {r['why']}"
                    + (f" · stop {_fp(r['stop'])} ({r['stop_w']})" if r.get("stop") else f" · {r['stop_w']}"))
            data = {"f": "al_bunu", "price": r["p"], "sc": r["sc"], "exp": r["exp"], "br": r["br"], "stop": r.get("stop"), "day": day, "src": "v134"}
            try:
                self.hub._emit("olay", NT, s, title, body, data, tsec=ref)
                st = "gönderildi"
            except Exception as ex:
                st = "hata"
                logger.warning("v134 emit: %s", ex)
            self.sent.append({"sym": s, "title": title, "text": body, "ts": wall, "st": st})

    # ------------------------------------------------------------------ API
    def listing(self) -> dict:
        r = dict(self.res)
        r.update({"version": VERSION, "th": TH, "cfg": {k: CFG[k] for k in ("min_sc", "rate", "persist")}, "nt": NT, "nt_default": NT_DEFAULT,
                  "loop": LOOP, "ms": self.ms, "ready": bool(self.res.get("ts")) and not self.res.get("pending"),
                  "age": round(time.time() - self.res["epoch"]) if self.res.get("epoch") else None})
        return r

    def status(self) -> dict:
        return {"version": VERSION, "loops": self.loops, "errors": self.errors, "last_err": self.last_err, "ms": self.ms,
                "n": len(self.res.get("rows") or []), "near": len(self.res.get("near") or []), "ts": self.res.get("ts"),
                "started": self.started, "sent": list(self.sent)[-10:], "fired": len(self.fired), "rate_1h": len(self.rate)}


engine = AlBunu()

try:
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse

    router = APIRouter()

    @router.get("/api/albunu/list")
    def _api_list():
        return JSONResponse(engine.listing(), headers={"Cache-Control": "no-store"})

    @router.get("/api/albunu/status")
    def _api_status():
        return JSONResponse(engine.status(), headers={"Cache-Control": "no-store"})
except Exception:   # pragma: no cover
    router = None
