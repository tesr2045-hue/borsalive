"""v1.27.1 — AKD Taraması · TÜM AKD NET için DÖNEM (HAFTALIK / AYLIK) verisi.

AKD sekmesindeki HAFTALIK/AYLIK ile BİREBİR aynı kaynak ve hesap:
  • tarih aralığı = main._akd_period_range(period)  (AKD sekmesi ile aynı fonksiyon)
  • veri          = ideal_feed.akd_range(sym, d1, d2) (REQ_DGLM_TAR2 TUM + TOPLAM — AKD sekmesi ile aynı istek)
  • alıcı/satıcı  = ideal_feed._akd_compose(...)      (AKD sekmesi ile aynı fonksiyon/sıralama)
  • İLK N ALAN    = ilk N net alıcının net lot toplamı; İLK N SATAN = ilk N net satıcının |net lot| toplamı
    (AKD sekmesi 'İLK N NET PGÇ' kartı ile aynı formül)
Tüm hisseler için arka planda nazikçe (aralıklı) çekilir, data/v1271/ altına önbelleklenir.
OneSignal / bildirim mantığına DOKUNMAZ.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger("v1271")
IST = timezone(timedelta(hours=3))
DIR = Path(__file__).resolve().parent.parent / "data" / "v1271"
PERIODS = {"weekly": "HAFTALIK", "monthly": "AYLIK"}
NS = (3, 5, 10)
COLS = ["s", "p", "gd", "nb", "ns", "b3", "s3", "durum", "vol", "tnb", "tns", "tnp", "sab", "sabl", "sasl", "tv", "tvh",
        "i3a", "i3s", "i5a", "i5s", "i10a", "i10s"]


def _r(v, d=2):
    try:
        return None if v is None else round(float(v), d)
    except Exception:
        return None


def _durum(b3, s3, nb, ns):
    try:
        from app.v126 import _durum as D
        return D(b3, s3, nb, ns)
    except Exception:
        return "NÖTR"


def ilk_n(buyers, sellers, ns=NS):
    """AKD sekmesi kartı ile aynı: buyers/sellers _akd_compose sırasında (net lot büyükten küçüğe)."""
    out = {}
    for n in ns:
        a = sum((r.get("net_lot") or 0.0) for r in buyers[:n])
        s = sum(abs(r.get("net_lot") or 0.0) for r in sellers[:n])
        out[n] = (a, s)
    return out


def pct(a, s):
    """|Alan − Satan| / max(Alan, Satan) × 100, yön işaretli (+ Alan, − Satan)."""
    m = max(a, s)
    if not m:
        return None
    return (a - s) / m * 100.0


class AkdDonem:
    def __init__(self):
        self.feed = None
        self.prange = None
        self.lock = threading.Lock()
        self.jobs = {}          # key -> job
        self.th = {}

    def start(self, feed, prange):
        self.feed = feed
        self.prange = prange
        DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------ önbellek
    def _path(self, key):
        return DIR / f"akdp_{key}.json"

    def _load(self, key):
        p = self._path(key)
        try:
            return json.loads(p.read_text())
        except Exception:
            return None

    def _save(self, key, job):
        try:
            tmp = self._path(key).with_suffix(".tmp")
            tmp.write_text(json.dumps({k: v for k, v in job.items() if k not in ("running",)}, ensure_ascii=False))
            tmp.replace(self._path(key))
            for old in sorted(DIR.glob("akdp_*.json"))[:-6]:
                old.unlink(missing_ok=True)
        except Exception as ex:   # pragma: no cover
            logger.warning("v1271 save: %s", ex)

    @staticmethod
    def _final_ts(d2):
        """d2 seansının AKD'si 18:12'den sonra kesinleşir."""
        dt = datetime.strptime(d2, "%Y%m%d").replace(hour=18, minute=12, tzinfo=IST)
        return dt.timestamp()

    def _stale(self, job):
        if not job or not job.get("fin"):
            return True
        if job.get("fin") >= self._final_ts(job["to"]) and not job.get("miss"):
            return False                      # dönem kapanmış ve eksiksiz → kesin
        return time.time() - job["fin"] > 900  # seans içi / eksikli → 15 dk

    # ------------------------------------------------------------ API
    def get(self, period):
        period = (period or "weekly").lower()
        if period not in PERIODS:
            period = "weekly"
        if self.feed is None or self.prange is None:
            return {"ok": False, "error": "motor başlamadı"}
        d1, d2, label = self.prange(period, None, None)
        key = f"{d1}_{d2}"
        with self.lock:
            job = self.jobs.get(key)
            if job is None:
                job = self._load(key)
                if job:
                    job["running"] = False
                    self.jobs[key] = job
            run = job is not None and job.get("running")
            if not run and self._stale(job):
                prev = job
                job = {"period": period, "label": label, "from": d1, "to": d2, "key": key, "running": True,
                       "done": 0, "total": 0, "st": (prev or {}).get("st") or {}, "at": time.time(), "fin": None, "miss": 0,
                       "prev_fin": (prev or {}).get("fin")}
                self.jobs[key] = job
                t = threading.Thread(target=self._run, args=(key,), daemon=True, name=f"v1271-{key}")
                self.th[key] = t
                t.start()
        return self._payload(job)

    def _payload(self, job):
        F = self.feed
        with F._lock:
            qd = {s: (q.get("change_pct"), q.get("last")) for s, q in F.quotes.items()}
        rows = []
        for sym in sorted(job.get("st") or {}):
            e = job["st"][sym]
            if not e:
                continue
            q = qd.get(sym) or (None, None)
            last = q[1] or e.get("p")
            tnb = e["tnb"]
            rows.append([sym, last, _r(q[0], 2), e["nb"], e["ns"], e["b3"], e["s3"], e["du"], e["vol"], tnb, e["tns"],
                         _r(tnb / e["vol"] * 100.0, 2) if e["vol"] else None, None, None, None, None, None]
                        + [e["i"][str(n)][k] for n in NS for k in (0, 1)])
        fin = job.get("fin") or job.get("prev_fin")
        return {"ok": True, "period": job["period"], "label": job["label"], "from": job["from"], "to": job["to"],
                "running": bool(job.get("running")), "done": job.get("done", 0), "total": job.get("total", 0),
                "miss": job.get("miss", 0), "fin": fin,
                "fin_s": datetime.fromtimestamp(fin, IST).strftime("%d.%m %H:%M") if fin else None,
                "stocks": rows, "cols": {"stocks": COLS},
                "src": (f"İdealData AKD {job['label']} ({job['from'][6:]}.{job['from'][4:6]}–{job['to'][6:]}.{job['to'][4:6]}.{job['to'][:4]}) — "
                        "AKD sekmesi HAFTALIK/AYLIK ile aynı istek (REQ_DGLM_TAR2) ve aynı hesap (_akd_compose)"),
                "note": "Dönem verisinde aktif alış % yok (işlem kaydı günlüktür) — '—'."}

    # ------------------------------------------------------------ toplu çekim
    def _run(self, key):
        F = self.feed
        job = self.jobs[key]
        d1, d2 = job["from"], job["to"]
        try:
            for _ in range(60):
                if F.connected and F.logged_in and len(F.equity_universe()) >= 100:
                    break
                time.sleep(2)
            uni = F.equity_universe()
            with F._lock:
                tv = {s: ((F.quotes.get(s) or {}).get("turnover") or 0) for s in uni}
            order = sorted(uni, key=lambda s: -tv[s])
            job["total"] = len(order)
            new_st = {}
            fails = []
            gap = 0.12
            t0 = time.time()
            for i, sym in enumerate(order):
                e = self._one(sym, d1, d2)
                if e is None:
                    fails.append(sym)
                    gap = min(2.0, gap * 1.5 + 0.1)
                else:
                    new_st[sym] = e
                    gap = max(0.12, gap / 1.3)
                job["done"] = i + 1
                if (i + 1) % 25 == 0:
                    merged = dict(job["st"]); merged.update(new_st); job["st"] = merged
                time.sleep(gap)
            for sym in fails[:]:
                time.sleep(0.5)
                e = self._one(sym, d1, d2)
                if e is not None:
                    new_st[sym] = e
                    fails.remove(sym)
            job["st"] = new_st if len(new_st) >= max(50, len(job.get("st") or {}) * 0.8) else {**(job.get("st") or {}), **new_st}
            job["miss"] = len(fails)
            job["fin"] = time.time()
            logger.info("v1271: AKD dönem %s hazır: %d hisse, %d yanıtsız, %.0f sn", key, len(new_st), len(fails), time.time() - t0)
        except Exception as ex:   # pragma: no cover
            logger.warning("v1271 run %s: %s", key, ex)
            job["fin"] = job.get("fin") or time.time()
            job["miss"] = job.get("miss") or 1
        finally:
            job["running"] = False
            self._save(key, job)

    def _one(self, sym, d1, d2):
        F = self.feed
        try:
            raw = F.akd_range(sym, d1, d2, ttl=600.0)
        except Exception:
            raw = None
        if not raw:
            return None
        with F._lock:
            last = (F.quotes.get(sym) or {}).get("last")
        buyers, sellers = F._akd_compose(raw.get("TUM") or [], raw.get("TOPLAM") or [], last)
        if not buyers and not sellers:
            return {}
        nb = [r["net_lot"] for r in buyers]
        ns = [-r["net_lot"] for r in sellers]
        vb = sum(nb) or 1.0
        vs = sum(ns) or 1.0
        b3 = sum(nb[:3]) / vb * 100 if nb else 0.0
        s3 = sum(ns[:3]) / vs * 100 if ns else 0.0
        vol = 0.0
        for r in buyers + sellers:
            bl = r.get("buy_lot")
            vol += bl if bl is not None else max(r.get("net_lot") or 0.0, 0.0)
        I = ilk_n(buyers, sellers)
        return {"p": last, "nb": len(nb), "ns": len(ns), "b3": _r(b3, 1), "s3": _r(s3, 1), "du": _durum(b3, s3, len(nb), len(ns)),
                "vol": round(vol), "tnb": round(sum(nb)), "tns": round(sum(ns)),
                "i": {str(n): [I[n][0], I[n][1]] for n in NS}}

    def status(self):
        return {k: {"running": bool(j.get("running")), "done": j.get("done"), "total": j.get("total"), "miss": j.get("miss"), "fin": j.get("fin")}
                for k, j in self.jobs.items()}


akd_donem = AkdDonem()
