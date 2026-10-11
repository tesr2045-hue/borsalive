"""v1.32.0 — D-A-K SKORLARI: tüm BIST payları için canlı Derinlik Skoru · AKD Skoru · Kademe Analizi Skoru · D-A-K Skoru.

Her skor 0–100 (50 = dengeli), v1.25.0 Derinlik skoru ile aynı ölçek ve etiketler:
  ≥70 GÜÇLÜ ALIŞ · ≥57 ALIŞ AĞIRLIKLI · 44–56 DENGELİ · ≤43 SATIŞ AĞIRLIKLI · ≤30 GÜÇLÜ SATIŞ.
Skor = 50 + bileşen puanlarının toplamı (0–100'e kırpılır); her bileşen açıklamasıyla döner (dokununca gösterilir).

Kaynaklar (mevcut analizlerle AYNI veri, ağ isteği yok):
  Derinlik  : İdealData canlı derinlik (ideal_feed.depth — DERİNLİK sekmesi / Derinlik Baskısı ile aynı defter, 25 kademe + tüm defter toplamı)
              + bu motorun 1–3 dk defter geçmişi + son 15 dk işlem kaydındaki süpürmeler (v1.25.0 skorunun canlı defterle hesaplanabilen bileşenleri)
  AKD       : v1.26.0 AKD TARAMASI (v126.tarama — günlük AKD deposu + kurum bazında aktif alış/satış; AKD sekmesi Günlük ile aynı kayıt)
  Kademe    : İdealData Y38 fiyat kademe analizi (ideal_feed.levels — Kademe Analizi (tüm hisseler) / KADEME sekmesi ile aynı kayıt)
  D-A-K     : mevcut skorların ortalaması (en az 2 skor varsa).
"""
from __future__ import annotations

import bisect
import collections
import logging
import math
import threading
import time

from app.v122 import CONT_FROM, _fp, _fs, _hms, _sec_now
from app.v124 import _lim

logger = logging.getLogger("bist.v132")

VERSION = "1.33.1"
LOOP_LIVE = 15.0
LOOP_IDLE = 60.0


def _clip(v, a):
    return max(-a, min(a, v))


def _lab(sc):
    if sc is None:
        return None
    return ("GÜÇLÜ ALIŞ" if sc >= 70 else "ALIŞ AĞIRLIKLI" if sc >= 57 else "GÜÇLÜ SATIŞ" if sc <= 30
            else "SATIŞ AĞIRLIKLI" if sc <= 43 else "DENGELİ")


def _pct(v, d=1):
    if v is None:
        return "—"
    return (f"{v:+.{d}f}").replace(".", ",").replace("+", "+%").replace("-", "−%")


def _p0(v, d=0):
    return ("%" + f"{v:.{d}f}").replace(".", ",") if v is not None else "—"


def _fx(v):
    return (f"{v:.2f}".replace(".", ",") + "×") if v is not None else "—"


def _finish(comps):
    sc = max(0.0, min(100.0, 50.0 + sum(v for _, v in comps)))
    comps = [[l, round(v, 1)] for l, v in comps if abs(v) >= 0.05]
    comps.sort(key=lambda z: -abs(z[1]))
    return round(sc), comps


def _yorum(name, sc, comps):
    pos = [c[0] for c in comps if c[1] > 0][:2]; neg = [c[0] for c in comps if c[1] < 0][:2]
    y = f"{name} {sc} ({_lab(sc)})"
    if pos:
        y += ": " + ", ".join(pos)
    if neg:
        y += ("; buna karşın " if pos else ": ") + ", ".join(neg)
    return y + "."


# ======================================================================= Derinlik ==
def depth_score(bids, asks, book_bt, book_at, last, tv, tb, r10_old, sweeps15):
    """bids/asks: [(fiyat, lot)] en iyi → kötü. r10_old: ~1–3 dk önceki 10 kademe lot oranı. sweeps15: (yukarı, aşağı) son 15 dk."""
    comps = []
    b10 = sum(l for _, l in bids[:10]); a10 = sum(l for _, l in asks[:10])
    r10 = (b10 / a10) if (b10 > 0 and a10 > 0) else None
    if r10 is not None:          # v1.25.0 ile aynı formül
        comps.append([f"10 kademe alış/satış lot oranı {_fx(r10)}", _clip(12 * math.log2(max(0.05, r10)), 15)])
    elif a10 > 0:
        comps.append(["alış tarafında bekleyen emir yok", -15])
    elif b10 > 0:
        comps.append(["satış tarafında bekleyen emir yok", 15])
    btl = sum(p * l for p, l in bids[:25]); atl = sum(p * l for p, l in asks[:25])
    if btl + atl > 0:
        bp = btl / (btl + atl) * 100
        comps.append([f"25 kademe ₺ dengesi alış {_p0(bp)} ({_fs(btl)} / {_fs(atl)} ₺)", _clip((bp - 50) * 0.25, 8)])
    if book_bt is not None and book_at is not None and (book_bt + book_at) > 0:
        pall = book_bt / (book_bt + book_at) * 100
        comps.append([f"tüm defter alış payı {_p0(pall)}", _clip((pall - 50) * 0.2, 6)])
    if r10 is not None and r10_old:
        comps.append([f"son dakikalarda denge {_fx(r10_old)}→{_fx(r10)}", _clip(6 * math.log2(max(0.05, r10) / max(0.05, r10_old)), 6)])
    for side, lv, sg in (("alış", bids, 1), ("satış", asks, -1)):
        lots = sorted(l for _, l in lv[:15])
        med = lots[len(lots) // 2] if lots else 0
        n = 0
        for p, l in lv[:5]:
            if med and l >= 3 * med and p * l >= 250_000 and n < 2:
                comps.append([f"{_fp(p)} {side} duvarı ({_fs(p * l)} ₺)", 3 * sg]); n += 1
    if tv and bids and bids[0][0] >= tv - 1e-9 and not asks:
        comps.append([f"tavanda {_fs(bids[0][1])} lot alış kuyruğu", 10])
    elif tb and asks and asks[0][0] <= tb + 1e-9 and not bids:
        comps.append(["tabanda satış kuyruğu", -10])
    if sweeps15:
        u, d = sweeps15
        if u or d:
            comps.append([f"son 15 dk {u} yukarı / {d} aşağı süpürme", _clip(2 * (u - d), 8)])
    if not comps:
        return None
    sc, comps = _finish(comps)
    return {"sc": sc, "comps": comps, "r10": r10}


# ============================================================================ AKD ==
def akd_score(st, brs, last):
    """st: v126 tarama hisse satırı (sözlük). brs: o hissenin kurum satırları (sözlük listesi)."""
    comps = []
    nb, ns, b3, s3 = st.get("nb") or 0, st.get("ns") or 0, st.get("b3") or 0.0, st.get("s3") or 0.0
    if nb + ns == 0:
        return None
    comps.append([f"ilk 3 alıcı net alımın {_p0(b3)}, ilk 3 satıcı net satışın {_p0(s3)}", _clip((b3 - s3) * 0.4, 15)])
    if nb and ns:
        comps.append([f"{nb} net alıcı / {ns} net satıcı", _clip(6 * math.log2(ns / nb), 6)])
    du = st.get("durum")
    tnp = st.get("tnp") or 0.0
    if du in ("TOPLAMA", "DAĞITIM"):
        w = 3 + min(5.0, tnp / 6)
        comps.append([f"{du} (AKD net {_p0(tnp)} hacmin)", w if du == "TOPLAMA" else -w])
    buy = sorted((r for r in brs if (r.get("nl") or 0) > 0), key=lambda r: -r["nl"])
    sel = sorted((r for r in brs if (r.get("nl") or 0) < 0), key=lambda r: r["nl"])
    def wavg(rs, k, wk):
        num = den = 0.0
        for r in rs:
            v = r.get(k); w = r.get(wk) or 0
            if v is not None and w:
                num += v * w; den += w
        return num / den if den else None
    sab = st.get("sab")
    aa3 = wavg(buy[:3], "aa", "bl"); as3 = wavg(sel[:3], "as", "sl")
    if aa3 is not None and sab is not None:
        comps.append([f"ilk 3 alıcının aktif alışı {_p0(aa3)} (hisse ort. {_p0(sab)})", _clip((aa3 - sab) * 0.3, 6)])
    if as3 is not None and sab is not None:
        comps.append([f"ilk 3 satıcının aktif satışı {_p0(as3)} (hisse ort. {_p0(100 - sab)})", -_clip((as3 - (100 - sab)) * 0.3, 6)])
    if sab is not None:
        comps.append([f"hissede aktif alış {_p0(sab)}", _clip((sab - 50) * 0.2, 6)])
    num = den = 0.0
    for r in buy[:5]:
        if r.get("co"):
            num += r["co"] * r["nl"]; den += r["nl"]
    if den and last:
        co = num / den
        x = (last / co - 1) * 100
        comps.append([f"fiyat ilk 5 alıcının ort. maliyeti {_fp(co)}'in {'üstünde' if x >= 0 else 'altında'} ({_pct(x)})", _clip(x * 2, 6)])
    sc, comps = _finish(comps)
    top = [{"br": r["br"], "nl": r["nl"], "co": r.get("co"), "aa": r.get("aa")} for r in buy[:3]]
    tops = [{"br": r["br"], "nl": r["nl"], "co": r.get("co"), "as": r.get("as")} for r in sel[:3]]
    return {"sc": sc, "comps": comps, "durum": du, "top_b": top, "top_s": tops}


# ========================================================================= Kademe ==
def kademe_score(rows, last):
    """rows: Y38 [{price, lot, buy_pct, sell_pct}] — Kademe Analizi (tüm hisseler) ile aynı hesap."""
    b = s = btl = stl = tot = ttl = 0.0
    poc = None; pl = -1
    for r in rows:
        lot = r.get("lot") or 0
        bl = lot * (r.get("buy_pct") or 0) / 100; sl = lot * (r.get("sell_pct") or 0) / 100
        b += bl; s += sl; btl += bl * r["price"]; stl += sl * r["price"]; tot += lot; ttl += lot * r["price"]
        if lot > pl:
            pl = lot; poc = r["price"]
    if b + s <= 0 or not tot:
        return None
    comps = []
    netp = (b - s) / (b + s) * 100
    comps.append([f"alış lotu {_p0(b / (b + s) * 100)} · net {_pct(netp)}", _clip(netp * 0.5, 20)])
    aort = ttl / tot
    if last:
        x = (last / aort - 1) * 100
        comps.append([f"fiyat AORT {_fp(aort)}'in {'üstünde' if x >= 0 else 'altında'} ({_pct(x)})", _clip(x * 4, 8)])
        if poc:
            y = (last / poc - 1) * 100
            comps.append([f"fiyat POC {_fp(poc)}'un {'üstünde' if y >= 0 else 'altında'} ({_pct(y)})", _clip(y * 3, 6)])
    ba = btl / b if b else None; sa = stl / s if s else None
    if ba and sa:
        z = (ba / sa - 1) * 100
        comps.append([f"alış ort. {_fp(ba)} / satış ort. {_fp(sa)} ({'alıcılar yukarıdan alıyor' if z >= 0 else 'satıcılar yukarıda'})", _clip(z * 3, 6)])
    ps = sorted(r["price"] for r in rows)
    if len(ps) >= 3:
        lo, hi = ps[0], ps[-1]
        cut = hi - (hi - lo) / 3
        ub = us = 0.0
        for r in rows:
            if r["price"] >= cut - 1e-9:
                lot = r.get("lot") or 0
                ub += lot * (r.get("buy_pct") or 0) / 100; us += lot * (r.get("sell_pct") or 0) / 100
        if ub + us > 0:
            up = ub / (ub + us) * 100
            comps.append([f"üst kademelerde ({_fp(cut)}+) alış {_p0(up)}", _clip((up - 50) * 0.2, 6)])
    sc, comps = _finish(comps)
    return {"sc": sc, "comps": comps, "poc": poc, "aort": round(aort, 4), "netp": round(netp, 1), "nlv": len(rows)}


# ========================================================================= Motor ==
class PageDepth:
    """v1.32.1 — hisse sayfasındaki DERİNLİK SKORU (v1.25.0 madde 16) ile BİREBİR aynı hesap, tüm hisseler için.
    v125 motorunun gölge örneği: aynı derinlik kaydı dosyaları + aynı işlem kaydı + aynı canlı defter; yalnız durum önbelleği
    sınırsız (sayfa motoru 14 hisse tutar). Her hisse artımlı yeniden oynatılır; ilk tur ~1 dk, sonra her tur birkaç sn."""

    def __init__(self):
        self.sh = None
        self.res = {}
        self.thread = None
        self.loops = self.errors = 0
        self.last_err = None
        self.pass_s = None
        self.done = 0
        self.alock = threading.Lock()
        self.owner = None

    def _put(self, sym, out):
        x = (out.get("r") or {}).get("16")
        if x and x.get("score") is not None:
            self.res[sym] = {"sc": int(x["score"]), "lab": x.get("label"), "comps": x.get("comps") or [], "yorum": x.get("yorum"),
                             "hist": out.get("hist"), "ts": time.time()}
            return True
        return False

    def fresh(self, sym):
        """Detay açılınca o hissenin sayfa skorunu ŞİMDİ yeniden hesapla (artımlı, birkaç ms)."""
        if self.sh is None:
            return
        try:
            day, live = self.sh._resolve(None)
            out = {}
            with self.alock:
                self.sh._analyze(out, sym, day, live, {16})
            self._put(sym, out)
        except Exception as ex:
            self.last_err = f"fresh {sym}: {ex}"

    def start(self, d_engine, feed):
        try:
            from app import v125
        except Exception:
            return
        self.feed = feed
        sh = v125.DerinlikEngine.__new__(v125.DerinlikEngine)
        sh.rec = d_engine.rec
        sh.feed, sh.m, sh.b, sh.k, sh.hub = d_engine.feed, d_engine.m, d_engine.b, d_engine.k, None
        sh.ds = {}
        sh.lock = threading.RLock()
        sh.cache = {}; sh.alerted = {}; sh.arate = collections.deque(); sh.al_state = {}; sh.emitted = 0; sh.timing = {}
        sh.alive_t0 = time.time()
        DS = v125.DS

        def _state(sym, day, _sh=sh):
            key = (sym, day)
            S = _sh.ds.get(key)
            if S is None:
                tv, tb, _ = _sh._limits(sym, day)
                S = _sh.ds[key] = DS(sym, day, tv, tb)
            return S
        sh._state = _state
        self.sh = sh
        self.d_engine = d_engine
        orig = d_engine.analyze
        if not getattr(orig, "_v132", False):
            def analyze(sym, items=None, date=None, _o=orig, _me=self):
                out = _o(sym, items, date)
                try:     # sayfa (DERİNLİK sekmesi) skoru hesapladıysa listeye aynen yansıt
                    if out.get("live") and (out.get("r") or {}).get("16"):
                        _me._put(out.get("sym") or sym, out)
                except Exception:
                    pass
                return out
            analyze._v132 = True
            d_engine.analyze = analyze
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name="v132-dpage", daemon=True)
            self.thread.start()

    def _loop(self):
        time.sleep(30)
        while True:
            t0 = time.time()
            try:
                self.run_pass()
                self.loops += 1
            except Exception as ex:
                self.errors += 1
                self.last_err = f"{type(ex).__name__}: {ex}"
                logger.exception("v132 dpage")
            self.pass_s = round(time.time() - t0, 1)
            time.sleep(max(2.0, 15.0 - (time.time() - t0)))

    def run_pass(self):
        sh = self.sh
        day, live = sh._resolve(None)
        for k in [k for k in sh.ds if k[1] != day]:
            sh.ds.pop(k, None)
        uni = self.feed.equity_universe()
        n = 0
        catchup = len(sh.ds) < len(uni) * 0.9
        if catchup:   # açılış sonrası: listede üstte görünen (yüksek liste skoru / hacimli) hisseler önce — parantez (—) en kısa sürsün
            try:
                pri = {r[0]: ((r[7] if r[7] is not None else -1), r[4] if r[4] is not None else -1, r[3] or 0) for r in (self.owner.res.get("rows") or [])}
            except Exception:
                pri = {}
            uni = sorted(uni, key=lambda x: (x in self.res, tuple(-v for v in pri.get(x, (-1, -1, 0)))))
        for sym in uni:
            out = {}
            t1 = time.time()
            try:
                with self.alock:
                    sh._analyze(out, sym, day, live, {16})
            except Exception as ex:
                self.last_err = f"{sym}: {type(ex).__name__}: {ex}"
                continue
            if self._put(sym, out):
                n += 1
            # ilk turda (açılış sonrası yeniden oynatma) CPU payını yarıya indir → TRENE ATLA döngüsü yavaşlamasın
            time.sleep(max(0.004, 0.6 * (time.time() - t1) if catchup else 0.004))
        self.done = n


class ScoreEngine:
    def __init__(self):
        self.feed = self.m = self.v126 = None
        self.lock = threading.RLock()
        self.res = {"rows": [], "ts": None}
        self.det = {}
        self.r10h = collections.defaultdict(collections.deque)   # sym → [(ts, r10)]
        self.thread = None
        self.loops = self.errors = 0
        self.last_err = None
        self.ms = {}
        self.pd = PageDepth()
        self.pd.owner = self

    def start(self, feed, m_engine, v126_engine, d_engine=None):
        self.feed, self.m, self.v126 = feed, m_engine, v126_engine
        if d_engine is not None:
            try:
                self.pd.start(d_engine, feed)
            except Exception as ex:
                logger.warning("v132 page-depth start: %s", ex)
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name="v132-skor", daemon=True)
            self.thread.start()

    def _loop(self):
        time.sleep(20)
        while True:
            t0 = time.time()
            try:
                self.compute()
                self.loops += 1
            except Exception as ex:
                self.errors += 1
                self.last_err = f"{type(ex).__name__}: {ex}"
                logger.exception("v132 compute")
            live = self._live()
            time.sleep(max(3.0, (LOOP_LIVE if live else LOOP_IDLE) - (time.time() - t0)))

    def _live(self):
        try:
            return bool(self.m._live_day()) and 36000 <= _sec_now() <= 65400
        except Exception:
            return False

    def _sweeps(self, day):
        """son 15 dk yukarı/aşağı süpürme (aynı saniyede ≥3 farklı fiyat, ≥100 bin ₺, aktif alış/satış) — canlı işlem kaydı."""
        out = {}
        if not day:
            return out
        try:
            _, syms, _, lock, _ = self.m._src(day)
        except Exception:
            return out
        now = _sec_now()
        t0 = max(CONT_FROM, now - 900)
        for s, e in list(syms.items()):
            with lock:
                n = min(len(e.t), len(e.p), len(e.l), len(e.sd))
                if not n or e.t[n - 1] < t0:
                    continue
                i = bisect.bisect_left(e.t, t0, 0, n)
                T = e.t[i:n]; P = e.p[i:n]; L = e.l[i:n]; SD = e.sd[i:n]
            u = d = 0
            k = 0; m = len(T)
            while k < m:
                t = T[k]; j = k
                pu = set(); pd = set(); tu = td = 0.0
                while j < m and T[j] == t:
                    if SD[j] == 1:
                        pu.add(P[j]); tu += P[j] * L[j]
                    elif SD[j] == 2:
                        pd.add(P[j]); td += P[j] * L[j]
                    j += 1
                if len(pu) >= 3 and tu >= 100_000:
                    u += 1
                if len(pd) >= 3 and td >= 100_000:
                    d += 1
                k = j
            if u or d:
                out[s] = (u, d)
        return out

    def compute(self):
        F = self.feed
        if F is None:
            return
        t0 = time.time()
        uni = F.equity_universe()
        now = time.time()
        day = None
        try:
            day = self.m._live_day()
        except Exception:
            pass
        with F._lock:
            Q = {}
            for s in uni:
                q = F.quotes.get(s) or {}
                lm = (getattr(F, "limits", {}) or {}).get(s) or {}
                tv = q.get("ceiling") or lm.get("ceiling"); tb = q.get("floor") or lm.get("floor")
                if not tv and q.get("prev_close"):
                    tv, tb = _lim(q["prev_close"])
                Q[s] = (q.get("last"), q.get("prev_close"), q.get("turnover"), tv, tb, F._name(s) if hasattr(F, "_name") else "")
            D = {}
            for s in uni:
                d = F.depth.get(s)
                if not d or not d.get("ts"):
                    continue
                bids = [(v["price"], v["lot"]) for _, v in sorted(d["bids"].items()) if v.get("price") and v.get("lot")][:25]
                asks = [(v["price"], v["lot"]) for _, v in sorted(d["asks"].items()) if v.get("price") and v.get("lot")][:25]
                D[s] = (bids, asks, d.get("bid_total"), d.get("ask_total"), d["ts"])
            today_iso = time.strftime("%Y-%m-%d")
            today = time.strftime("%Y%m%d")
            LV = {s: ([dict(r) for r in v["rows"] if r.get("price")], v["ts"]) for s, v in F.levels.items() if v.get("date") in (today_iso, today) and s in Q}
        self.ms["copy"] = round((time.time() - t0) * 1000)
        t1 = time.time()
        SW = self._sweeps(day) if day else {}
        self.ms["sweeps"] = round((time.time() - t1) * 1000)
        t2 = time.time()
        AK = {}; AKB = collections.defaultdict(list); ak_src = None; ak_ts = None
        try:
            T = self.v126.tarama(None)
            cs = T["cols"]["stocks"]; cr = T["cols"]["rows"]; brs = T["brokers"]
            stl = [dict(zip(cs, x)) for x in T["stocks"]]
            for x in stl:
                AK[x["s"]] = x
            for r in T["rows"]:
                d = dict(zip(cr, r))
                s = stl[d["si"]]["s"]
                d["br"] = brs[d["bi"]]
                AKB[s].append(d)
            ak_src = T.get("src"); ak_ts = T.get("ts_s")
        except Exception as ex:
            logger.warning("v132 akd: %s", ex)
        self.ms["akd"] = round((time.time() - t2) * 1000)
        t3 = time.time()
        rows = []; det = {}
        for s in uni:
            last, pc, to, tv, tb, nm = Q[s]
            dd = D.get(s)
            ds = None; dage = None
            if dd and now - dd[4] <= 1800:
                bids, asks, bt, at, ts = dd
                dage = round(now - ts)
                h = self.r10h[s]
                old = None
                for (ht, hr) in h:
                    if 60 <= now - ht <= 240:
                        old = hr; break
                ds = depth_score(bids, asks, bt, at, last, tv, tb, old, SW.get(s))
                if ds and ds.get("r10") is not None:
                    if not h or now - h[-1][0] >= 10:
                        h.append((now, ds["r10"]))
                    while h and now - h[0][0] > 300:
                        h.popleft()
            a_s = None
            if s in AK:
                a_s = akd_score(AK[s], AKB.get(s, []), last)
            ks = None; kage = None
            lv = LV.get(s)
            if lv and lv[0]:
                ks = kademe_score(lv[0], last)
                kage = round(now - lv[1])
            pg = self.pd.res.get(s)
            if pg is not None and now - pg["ts"] > 600:
                pg = None
            dsc = pg["sc"] if pg else (ds["sc"] if ds else None)     # D-A-K: sayfadaki Derinlik Skoru (yoksa liste skoru)
            scs = [x for x in (dsc, a_s["sc"] if a_s else None, ks["sc"] if ks else None) if x is not None]
            dak = round(sum(scs) / len(scs)) if len(scs) >= 2 else None
            if not scs:
                continue
            chg = round((last / pc - 1) * 100, 2) if (last and pc) else None
            rows.append([s, last, chg, round(to or 0), ds["sc"] if ds else None, a_s["sc"] if a_s else None, ks["sc"] if ks else None, dak, len(scs), dage, kage,
                         pg["sc"] if pg else None])
            det[s] = {"s": s, "n": nm, "p": last, "c": chg, "t": to, "d": ds, "a": a_s, "k": ks, "dak": dak, "dage": dage, "kage": kage,
                      "dp": dict(pg) if pg else None}
        self.ms["score"] = round((time.time() - t3) * 1000)
        self.ms["total"] = round((time.time() - t0) * 1000)
        cov = {"uni": len(uni), "rows": len(rows), "d": sum(1 for r in rows if r[4] is not None), "a": sum(1 for r in rows if r[5] is not None),
               "k": sum(1 for r in rows if r[6] is not None), "dak": sum(1 for r in rows if r[7] is not None),
               "dp": sum(1 for r in rows if r[11] is not None), "diff": sum(1 for r in rows if r[11] is not None and r[4] is not None and r[11] != r[4])}
        with self.lock:
            self.res = {"rows": rows, "ts": time.strftime("%H:%M:%S"), "epoch": now, "cov": cov, "live": self._live(),
                        "akd_src": ak_src, "akd_ts": ak_ts, "version": VERSION, "ms": dict(self.ms),
                        "cols": ["s", "p", "c", "t", "d", "a", "k", "dak", "n", "dage", "kage", "dp"],
                        "dp": {"n": len(self.pd.res), "pass_s": self.pd.pass_s, "loops": self.pd.loops}}
            self.det = det

    # ---------------------------------------------------------------- API --
    def listing(self):
        with self.lock:
            r = dict(self.res)
        C = r.get("cols") or []
        if r.get("rows") and "dp" in C:
            idp, idd, ia, ik, idak, inn = C.index("dp"), C.index("d"), C.index("a"), C.index("k"), C.index("dak"), C.index("n")
            now = time.time(); rows = []
            for row in r["rows"]:
                pg = self.pd.res.get(row[0])
                if pg is not None and now - pg["ts"] <= 600 and pg["sc"] != row[idp]:
                    row = list(row); row[idp] = pg["sc"]
                    scs = [x for x in (row[idp] if row[idp] is not None else row[idd], row[ia], row[ik]) if x is not None]
                    row[idak] = round(sum(scs) / len(scs)) if len(scs) >= 2 else None; row[inn] = len(scs)
                rows.append(row)
            r["rows"] = rows
        r["ready"] = bool(r.get("rows"))
        r["loop"] = LOOP_LIVE if r.get("live") else LOOP_IDLE
        r["age"] = round(time.time() - r["epoch"]) if r.get("epoch") else None
        return r

    def detail(self, sym):
        sym = (sym or "").upper().strip()
        self.pd.fresh(sym)
        with self.lock:
            d = self.det.get(sym)
            ts = self.res.get("ts")
        if not d:
            return {"s": sym, "found": False, "ts": ts}
        out = dict(d); out["found"] = True; out["ts"] = ts
        for k, name in (("d", "Derinlik Skoru"), ("a", "AKD Skoru"), ("k", "Kademe Analizi Skoru")):
            x = out.get(k)
            if x:
                x = dict(x); x["lab"] = _lab(x["sc"]); x["yorum"] = _yorum(name, x["sc"], x["comps"]); out[k] = x
        pg = self.pd.res.get(sym)
        if pg is not None:
            out["dp"] = dict(pg)
            sc = [x for x in (pg["sc"], (out.get("a") or {}).get("sc"), (out.get("k") or {}).get("sc")) if x is not None]
            out["dak"] = round(sum(sc) / len(sc)) if len(sc) >= 2 else out.get("dak")
        if out.get("dp"):
            x = dict(out["dp"]); x["lab"] = _lab(x["sc"]); x["age"] = round(time.time() - x.pop("ts", time.time())); out["dp"] = x
        out["dak_lab"] = _lab(out.get("dak"))
        return out

    def status(self):
        return {"version": VERSION, "loops": self.loops, "errors": self.errors, "last_err": self.last_err, "ms": self.ms,
                "ts": self.res.get("ts"), "cov": self.res.get("cov"),
                "page_depth": {"n": len(self.pd.res), "loops": self.pd.loops, "pass_s": self.pd.pass_s, "errors": self.pd.errors, "last_err": self.pd.last_err,
                               "states": len(self.pd.sh.ds) if self.pd.sh else 0}}


engine = ScoreEngine()

try:
    from fastapi import APIRouter, Query, Request
    from fastapi.responses import JSONResponse

    router = APIRouter()

    @router.get("/api/skor/list")
    def _api_list():
        return JSONResponse(engine.listing(), headers={"Cache-Control": "no-store"})

    @router.get("/api/skor/detail")
    def _api_detail(s: str = Query("")):
        return JSONResponse(engine.detail(s), headers={"Cache-Control": "no-store"})

    @router.get("/api/skor/status")
    def _api_status():
        return engine.status()
except Exception:   # pragma: no cover
    router = None
