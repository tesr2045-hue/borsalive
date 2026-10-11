"""v1.27.0 — FORMASYON bar deposu (tüm hisseler · 5dk / 15dk / 30dk / 60dk / 2s / 4s / 1G / 1H).

Kaynaklar (gerçek veri, uydurma bar yok):
* Geçmiş gün içi: Yahoo Finance 5 dk OHLCV (gerçek açılış/yüksek/düşük/kapanış/hacim, son ~60 gün; toplu indirme 40 hisse/istek).
  Yahoo 5 dk serisi kapanış seansını (18:00–18:10) içermez → her günün son 5 dk barı o günün resmi kapanışıyla (Yahoo günlük
  kapanış + hacim farkı) tamamlanır. 09:55 açılış seansı barı 10:00 barına katılır.
* Bugünkü seans: İdealData canlı işlem kaydı (trade_store, gerçek zamanlı; Yahoo ~15 dk gecikmeli) → 5 dk barlar; kayıt bir hissede
  tam değilse o hisse için Yahoo'nun bugünkü barları (gecikmeli) + kayıttaki sonraki işlemler kullanılır.
* Günlük: Yahoo 1G (son ~2 yıl, gerçek açılış) + bugün için 5 dk barların toplamı. Haftalık = günlüklerden (Pzt–Cum).
* 15/30/60 dk, 2 s, 4 s = 5 dk barlardan BIST seans saatine hizalı (10:00'dan itibaren; 2 s: 10–12, 12–14, 14–16, 16–18;
  4 s: 10–14, 14–18; günün son barı kapanış seansını içerir).
Doğrulama (02.10.2026): İdealData kaydından kurulan 5 dk barlar Yahoo 5 dk barlarıyla OHLC birebir, hacim oranı 1,00.
"""
from __future__ import annotations

import logging
import pickle
import threading
import time
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from zoneinfo import ZoneInfo

logger = logging.getLogger("v127")
IST = ZoneInfo("Europe/Istanbul")
BASE = Path(__file__).resolve().parent.parent / "data" / "v127"
TFS = ["5m", "15m", "30m", "60m", "2h", "4h", "1d", "1w"]
TF_MIN = {"5m": 5, "15m": 15, "30m": 30, "60m": 60, "2h": 120, "4h": 240}
TF_LABEL = {"5m": "5 dk", "15m": "15 dk", "30m": "30 dk", "60m": "60 dk", "2h": "2 saat", "4h": "4 saat", "1d": "Günlük", "1w": "Haftalık"}
KEEP = {"5m": 400, "15m": 400, "30m": 400, "60m": 500, "2h": 300, "4h": 200, "1d": 520, "1w": 160}
S_OPEN, S_LAST, S_CLOSE = 36000, 64500, 65400      # 10:00 · son sürekli 5 dk barı 17:55 · kapanış seansı bitişi 18:10
YH_BATCH = 40
DAYS: dict = {}          # gün dizgeleri tek nesne (bellek)


def _sod(ts: int) -> int:
    d = datetime.fromtimestamp(ts, IST)
    return d.hour * 3600 + d.minute * 60 + d.second


def _day_of(ts: int) -> str:
    return datetime.fromtimestamp(ts, IST).strftime("%Y%m%d")


def _ts(day: str, sod: int) -> int:
    d = datetime.strptime(day, "%Y%m%d").replace(tzinfo=IST)
    return int(d.timestamp()) + int(sod)


def _bucket5(sod: int) -> int:
    """5 dk bar başlangıcı (gün saniyesi): açılış seansı → 10:00, kapanış seansı → 17:55."""
    if sod < S_OPEN:
        return S_OPEN
    if sod >= 64800:
        return S_LAST
    return sod - (sod % 300)


class Bars:
    """Tek seri: t (bar başlangıcı, epoch sn; günlük/haftalıkta günün 00:00'ı), o,h,l,c,v (numpy) + gün anahtarı."""
    __slots__ = ("t", "o", "h", "l", "c", "v", "day")

    def __init__(self, t, o, h, l, c, v, day):
        self.t, self.o, self.h, self.l, self.c, self.v, self.day = t, o, h, l, c, v, day

    def __len__(self):
        return len(self.c)

    @staticmethod
    def empty():
        z = np.zeros(0)
        return Bars(np.zeros(0, dtype=np.int64), z, z, z, z, z, [])

    def tail(self, n):
        if len(self) <= n:
            return self
        return Bars(self.t[-n:], self.o[-n:], self.h[-n:], self.l[-n:], self.c[-n:], self.v[-n:], self.day[-n:])

    def concat(self, other):
        if not len(other):
            return self
        if not len(self):
            return other
        return Bars(np.concatenate([self.t, other.t]), np.concatenate([self.o, other.o]), np.concatenate([self.h, other.h]),
                    np.concatenate([self.l, other.l]), np.concatenate([self.c, other.c]), np.concatenate([self.v, other.v]),
                    list(self.day) + list(other.day))


def _from_rows(rows):
    """rows: list of (t, o, h, l, c, v, day) sıralı."""
    if not rows:
        return Bars.empty()
    t = np.array([r[0] for r in rows], dtype=np.int64)
    a = np.array([r[1:6] for r in rows], dtype=np.float64)
    return Bars(t, a[:, 0], a[:, 1], a[:, 2], a[:, 3], a[:, 4], [r[6] for r in rows])


def agg_intraday(b5: Bars, minutes: int) -> Bars:
    """5 dk barları seans hizalı N dakikalık barlara topla (10:00 tabanlı; günün son barı kapanış seansını içerir)."""
    if minutes == 5 or not len(b5):
        return b5
    w = minutes * 60
    rows = []
    cur = None
    for i in range(len(b5)):
        day = b5.day[i]
        sod = _sod(int(b5.t[i]))
        k = (day, (sod - S_OPEN) // w)
        if cur is None or cur[0] != k:
            if cur is not None:
                rows.append(cur[1])
            st = _ts(day, S_OPEN + k[1] * w)
            cur = (k, [st, b5.o[i], b5.h[i], b5.l[i], b5.c[i], b5.v[i], day])
        else:
            r = cur[1]
            r[2] = max(r[2], b5.h[i]); r[3] = min(r[3], b5.l[i]); r[4] = b5.c[i]; r[5] += b5.v[i]
    if cur is not None:
        rows.append(cur[1])
    return _from_rows(rows)


def agg_daily_from5(b5: Bars) -> Bars:
    rows = []
    cur = None
    for i in range(len(b5)):
        day = b5.day[i]
        if cur is None or cur[6] != day:
            if cur is not None:
                rows.append(cur)
            cur = [_ts(day, 0), b5.o[i], b5.h[i], b5.l[i], b5.c[i], b5.v[i], day]
        else:
            cur[2] = max(cur[2], b5.h[i]); cur[3] = min(cur[3], b5.l[i]); cur[4] = b5.c[i]; cur[5] += b5.v[i]
    if cur is not None:
        rows.append(cur)
    return _from_rows(rows)


def agg_weekly(bd: Bars) -> Bars:
    rows = []
    cur = None
    for i in range(len(bd)):
        dt = datetime.strptime(bd.day[i], "%Y%m%d")
        wk = dt.isocalendar()[:2]
        if cur is None or cur[0] != wk:
            if cur is not None:
                rows.append(cur[1])
            cur = (wk, [int(bd.t[i]), bd.o[i], bd.h[i], bd.l[i], bd.c[i], bd.v[i], bd.day[i]])
        else:
            r = cur[1]
            r[2] = max(r[2], bd.h[i]); r[3] = min(r[3], bd.l[i]); r[4] = bd.c[i]; r[5] += bd.v[i]
    if cur is not None:
        rows.append(cur[1])
    return _from_rows(rows)


def bars_from_trades(day, T, P, L, start_sod=0):
    """İşlem kaydı (gün saniyesi, fiyat, lot) → 5 dk barlar (açılış/kapanış seansı katlanır)."""
    out = {}
    order = []
    for t, p, l in zip(T, P, L):
        if t < start_sod or p <= 0:
            continue
        k = _bucket5(int(t))
        b = out.get(k)
        if b is None:
            out[k] = [p, p, p, p, float(l)]
            order.append(k)
        else:
            if p > b[1]: b[1] = p
            if p < b[2]: b[2] = p
            b[3] = p; b[4] += l
    rows = [(_ts(day, k), *out[k], day) for k in sorted(order)]
    return _from_rows(rows)


# ------------------------------------------------------------------ Yahoo
def _yahoo_download(ysyms, period, interval):
    import yfinance as yf
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return yf.download(ysyms, period=period, interval=interval, group_by="ticker", threads=False, progress=False, auto_adjust=False)


def _df_rows(sub, daily):
    """Yahoo DataFrame → satırlar (vektörel; iterrows yok)."""
    if sub is None or "Close" not in sub.columns:
        return []
    sub = sub.dropna(subset=["Close"])
    if sub.empty:
        return []
    O = sub["Open"].to_numpy(dtype=float); H = sub["High"].to_numpy(dtype=float); L = sub["Low"].to_numpy(dtype=float)
    C = sub["Close"].to_numpy(dtype=float); V = np.nan_to_num(sub["Volume"].to_numpy(dtype=float))
    ok = (C > 0) & (O > 0) & (H > 0) & (L > 0)
    O, H, L, C = np.round(O, 4), np.round(H, 4), np.round(L, 4), np.round(C, 4)
    H = np.maximum(H, np.maximum(O, C)); L = np.minimum(L, np.minimum(O, C))
    idx = sub.index
    if daily:
        days = idx.strftime("%Y%m%d")
        sods = None
    else:
        ii = idx.tz_convert(IST) if idx.tz is not None else idx.tz_localize(IST)
        days = ii.strftime("%Y%m%d")
        sods = (ii.hour * 3600 + ii.minute * 60).to_numpy()
    rows = []
    t0cache = {}
    for i in np.nonzero(ok)[0]:
        day = DAYS.setdefault(days[i], days[i])
        b0 = t0cache.get(day)
        if b0 is None:
            b0 = t0cache[day] = _ts(day, 0)
        if daily:
            rows.append((b0, O[i], H[i], L[i], C[i], V[i], day))
        else:
            rows.append((b0 + _bucket5(int(sods[i])), O[i], H[i], L[i], C[i], V[i], day))
    return rows


def _merge_dup(rows):
    """Aynı bar zamanına düşen satırları birleştir (09:55 açılış barı → 10:00)."""
    out = []
    for r in rows:
        if out and out[-1][0] == r[0]:
            p = out[-1]
            out[-1] = (p[0], p[1], max(p[2], r[2]), min(p[3], r[3]), r[4], p[5] + r[5], p[6])
        else:
            out.append(r)
    return out


def _close_fix(rows5, drows):
    """Her günün son 5 dk barına kapanış seansını ekle (resmi günlük kapanış, hacim farkı)."""
    D = {r[6]: r for r in drows}
    out = list(rows5)
    last_i = {}
    vs = {}
    for i, r in enumerate(out):
        last_i[r[6]] = i
        vs[r[6]] = vs.get(r[6], 0.0) + r[5]
    for day, i in last_i.items():
        d = D.get(day)
        if not d:
            continue
        r = out[i]
        c = d[4]
        dv = max(0.0, d[5] - vs[day])
        if abs(c - r[4]) > 1e-9 or dv > 0:
            out[i] = (r[0], r[1], max(r[2], c), min(r[3], c), c, r[5] + dv, r[6])
    return out


class BarStore:
    def __init__(self):
        self.lock = threading.RLock()
        self.hist = {tf: {} for tf in TFS}      # geçmiş (kapanmış günler) — tf → sym → Bars
        self.today = {}                          # sym → Bars (bugünkü 5 dk; canlı)
        self.today_day = None
        self.src = {}                            # sym → {"hist": "yahoo", "today": "idealdata"/"yahoo"/None}
        self.meta = {"yahoo_5m_at": None, "yahoo_1d_at": None, "yahoo_ok": 0, "yahoo_missing": [], "hist_last_day": None, "err": None}
        self.ylive = {}                          # sym → (fetched_at, Bars) bugünün Yahoo 5 dk yedeği

    # ---------------------------------------------------------------- yükle / kaydet
    def _file(self):
        return BASE / "hist.pkl"

    def load_disk(self):
        try:
            with open(self._file(), "rb") as f:
                d = pickle.load(f)
            with self.lock:
                self.hist = d["hist"]
                self.meta.update(d.get("meta") or {})
            return True
        except Exception as ex:
            logger.info("v127: disk önbelleği yok/okunamadı (%s)", ex)
            return False

    def save_disk(self):
        try:
            BASE.mkdir(parents=True, exist_ok=True)
            tmp = self._file().with_suffix(".tmp")
            with self.lock:
                d = {"hist": self.hist, "meta": dict(self.meta)}
            with open(tmp, "wb") as f:
                pickle.dump(d, f, protocol=5)
            tmp.replace(self._file())
        except Exception as ex:   # pragma: no cover
            logger.warning("v127 save: %s", ex)

    # ---------------------------------------------------------------- Yahoo geçmiş
    def refresh_yahoo(self, universe, before_day=None, sleep=0.4, log=None):
        """universe: [(sym, yahoo)]. before_day: bu günden (dahil) sonraki barlar geçmişe alınmaz (bugün canlı kayıttan)."""
        t0 = time.time()
        ymap = {y: s for s, y in universe}
        ys = list(ymap)
        r5, r1 = {}, {}
        for i in range(0, len(ys), YH_BATCH):
            batch = ys[i:i + YH_BATCH]
            for interval, period, store in (("5m", "60d", r5), ("1d", "2y", r1)):
                try:
                    df = _yahoo_download(batch, period, interval)
                except Exception as ex:
                    logger.warning("v127 yahoo %s batch %d: %s", interval, i, ex)
                    continue
                if df is None or df.empty:
                    continue
                lv0 = set(df.columns.get_level_values(0)) if hasattr(df.columns, "levels") else set()
                for y in batch:
                    if y in lv0:
                        try:
                            rows = _df_rows(df[y], interval == "1d")
                        except Exception:
                            rows = []
                        if rows:
                            store[ymap[y]] = rows
                time.sleep(sleep)
            if log and (i // YH_BATCH) % 4 == 0:
                log(f"yahoo {i + len(batch)}/{len(ys)}")
        hist = {tf: {} for tf in TFS}
        ok = 0
        missing = []
        last_day = None
        for s, _y in universe:
            d1 = r1.get(s) or []
            m5 = r5.get(s) or []
            if before_day:
                d1 = [r for r in d1 if r[6] < before_day]
                m5 = [r for r in m5 if r[6] < before_day]
            if not d1 and not m5:
                missing.append(s)
                continue
            ok += 1
            m5 = _close_fix(_merge_dup(m5), d1)
            b5 = _from_rows(m5)
            hist["5m"][s] = b5.tail(KEEP["5m"])
            for tf in ("15m", "30m", "60m", "2h", "4h"):
                hist[tf][s] = agg_intraday(b5, TF_MIN[tf]).tail(KEEP[tf])
            bd = _from_rows(d1)
            hist["1d"][s] = bd.tail(KEEP["1d"])
            hist["1w"][s] = agg_weekly(bd).tail(KEEP["1w"])
            if len(bd):
                last_day = max(last_day or "", bd.day[-1])
        with self.lock:
            self.hist = hist
            self.meta.update({"yahoo_5m_at": time.time(), "yahoo_1d_at": time.time(), "yahoo_ok": ok, "yahoo_missing": missing,
                              "hist_last_day": last_day, "yahoo_sec": round(time.time() - t0, 1), "before_day": before_day})
        logger.info("v127: Yahoo geçmiş %d hisse (%d eksik) %.0f sn", ok, len(missing), time.time() - t0)
        return ok, missing

    def yahoo_today(self, syms, day):
        """Canlı kaydı tam olmayan hisseler için bugünün Yahoo 5 dk barları (gecikmeli yedek)."""
        out = {}
        ys = [(s, s + ".IS") for s in syms]
        for i in range(0, len(ys), YH_BATCH):
            batch = ys[i:i + YH_BATCH]
            try:
                df = _yahoo_download([y for _, y in batch], "1d", "5m")
            except Exception as ex:
                logger.debug("v127 yahoo today: %s", ex)
                continue
            lv0 = set(df.columns.get_level_values(0)) if df is not None and not df.empty and hasattr(df.columns, "levels") else set()
            for s, y in batch:
                if y in lv0:
                    rows = [r for r in _merge_dup(_df_rows(df[y], False)) if r[6] == day]
                    out[s] = _from_rows(rows)
            time.sleep(0.4)
        now = time.time()
        with self.lock:
            for s, b in out.items():
                self.ylive[s] = (now, b)
        return out

    # ---------------------------------------------------------------- bugün (canlı kayıt)
    def set_today(self, day, sym, b5, src):
        with self.lock:
            if self.today_day != day:
                self.today = {}
                self.today_day = day
            self.today[sym] = b5
            self.src.setdefault(sym, {})["today"] = src

    # ---------------------------------------------------------------- okuma
    def get(self, sym, tf):
        """Geçmiş + bugün birleşik seri (KEEP sınırında)."""
        with self.lock:
            h = self.hist.get(tf, {}).get(sym)
            t5 = self.today.get(sym) if self.today_day else None
            tday = self.today_day
        h = h if h is not None else Bars.empty()
        if t5 is None or not len(t5):
            return h
        if len(h) and h.day[-1] >= tday:      # geçmiş zaten bugünü içeriyor
            return h
        if tf == "5m":
            add = t5
        elif tf in TF_MIN:
            add = agg_intraday(t5, TF_MIN[tf])
        elif tf == "1d":
            add = agg_daily_from5(t5)
        else:   # 1w: bu haftanın günlükleri + bugün
            with self.lock:
                hd = self.hist["1d"].get(sym)
            hd = hd if hd is not None else Bars.empty()
            bd = hd.concat(agg_daily_from5(t5))
            return agg_weekly(bd).tail(KEEP["1w"])
        return h.concat(add).tail(KEEP[tf])


def closed_count(b: Bars, tf, now=None):
    """Serinin KAPANMIŞ bar sayısı (son bar seans içinde hâlâ oluşuyorsa hariç)."""
    n = len(b)
    if not n:
        return 0
    now = now or datetime.now(IST)
    today = now.strftime("%Y%m%d")
    sod = now.hour * 3600 + now.minute * 60 + now.second
    last_day = b.day[-1]
    if last_day < today:
        if tf == "1w":
            # hafta: son barın haftası bitmiş mi (bugün başka hafta ya da Cumartesi/Pazar)?
            lw = datetime.strptime(last_day, "%Y%m%d").isocalendar()[:2]
            if lw == now.isocalendar()[:2] and now.weekday() < 5 and not (now.weekday() == 4 and sod >= S_CLOSE):
                return n - 1
        return n
    # son bar bugün
    if tf in ("1d",):
        return n if sod >= S_CLOSE else n - 1
    if tf == "1w":
        return n if (now.weekday() >= 4 and sod >= S_CLOSE) or now.weekday() >= 5 else n - 1
    w = TF_MIN[tf] * 60
    st = _sod(int(b.t[-1]))
    end = st + w
    if end >= 64800:
        end = S_CLOSE
    return n if sod >= end else n - 1
