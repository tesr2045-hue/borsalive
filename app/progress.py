"""v1.37.0 — Ortak ilerleme kaydı: her motor done/total, faz, başlangıç, ETA, son tam bitiş süresini buraya yazar.
GET /api/progress (tümü) · /api/progress?k=fm,ob (seçili). Motorlar arası hata yalıtımı: buradaki her çağrı
try/except ile sarılıdır, ilerleme kaydı asla motoru düşürmez."""
from __future__ import annotations

import functools
import threading
import time

from fastapi import APIRouter, Query

router = APIRouter()
_L = threading.Lock()
_E: dict = {}

LABELS = {
    "fm": "Formasyonlar", "ob": "Order Block", "skor": "D-A-K skorları", "dpage": "D-A-K derinlik",
    "algo": "Algo Destek/Direnç", "albunu": "AL BUNU", "maliyet": "Maliyet Yükselten", "baski": "POC/AORT Baskısı",
    "akd": "AKK/AKD taramaları", "olay": "Olay listesi", "kademe": "Kademe/Şerit", "eik": "En İyi Koşullar",
    "op": "Operasyon (KEŞFET)", "tren": "Trene Atla", "lite": "Hisse listesi", "radar": "Piyasa Radarı",
}


def _e(k):
    e = _E.get(k)
    if e is None:
        e = _E[k] = {"k": k, "label": LABELS.get(k, k), "running": False, "phase": "", "done": 0, "total": None,
                     "start": None, "last_end": None, "last_sec": None, "runs": 0, "err": None}
    return e


def begin(k, total=None, phase=""):
    try:
        with _L:
            e = _e(k)
            e.update(running=True, phase=phase, done=0, total=total, start=time.time(), err=None)
    except Exception:
        pass


def step(k, done=None, inc=1, total=None, phase=None):
    try:
        e = _E.get(k)
        if e is None or not e["running"]:
            begin(k, total, phase or ""); e = _E[k]
        e["done"] = done if done is not None else e["done"] + inc
        if total is not None:
            e["total"] = total
        if phase is not None:
            e["phase"] = phase
    except Exception:
        pass


def end(k, err=None):
    try:
        with _L:
            e = _e(k)
            now = time.time()
            if e["start"]:
                e["last_sec"] = round(now - e["start"], 1)
            e.update(running=False, last_end=now, err=(str(err)[:160] if err else None))
            e["runs"] += 1
            if e["total"]:
                e["done"] = e["total"]
    except Exception:
        pass


def wrap(obj, meth, k):
    """Bir motorun tur fonksiyonunu ilerleme kaydıyla sarar (adet bilinmiyorsa ETA = son tur süresi)."""
    f = getattr(obj, meth, None)
    if f is None or getattr(f, "_pg", False):
        return
    @functools.wraps(f)
    def w(*a, **kw):
        nested = _E.get(k, {}).get("running")
        try:   # v1.38.1 low_resource: düşük öncelik + sıralı açılış (yalnız arka plan motor iş parçacıklarında)
            from app import perf as _pf
            bg = threading.current_thread().name not in ("MainThread",) and not threading.current_thread().name.startswith(("AnyIO", "asyncio"))
            if bg and not nested:
                _pf.engine_thread_init(k, meth)
        except Exception:
            bg, _pf = False, None
        if not nested:
            begin(k)
        t0 = time.time()
        try:
            r = f(*a, **kw)
        except Exception as ex:
            if not nested:
                end(k, ex)
            raise
        if not nested:
            end(k)
            if bg and _pf is not None:
                _pf.engine_pass_done(k, time.time() - t0, meth)
        return r
    w._pg = True
    setattr(obj, meth, w)


def view(e):
    now = time.time()
    d = dict(e)
    el = now - e["start"] if e["running"] and e["start"] else None
    eta = None
    if el is not None:
        if e["total"] and e["done"]:
            eta = max(0.0, (e["total"] - e["done"]) * el / e["done"])
        elif e["last_sec"]:
            eta = max(0.0, e["last_sec"] - el)
    d["elapsed"] = round(el, 1) if el is not None else None
    d["eta"] = round(eta, 1) if eta is not None else None
    d["pct"] = round(100.0 * e["done"] / e["total"], 1) if e["total"] else None
    d["age"] = round(now - e["last_end"], 1) if e["last_end"] else None
    return d


def snapshot(keys=None):
    with _L:
        return {k: view(e) for k, e in _E.items() if not keys or k in keys}


@router.get("/api/progress")
def api_progress(k: str = Query("")):
    keys = [x for x in k.split(",") if x] if k else None
    return {"ts": time.time(), "engines": snapshot(keys)}


# v1.37.0 bellek: pandas/numpy geçici tamponları serbest bırakılsa da glibc belleği işletim sistemine geri vermiyordu
# (ölçüm: OB taraması +750 MB RSS → malloc_trim sonrası +64 MB). 60 sn'de bir malloc_trim + sınırlı RSS geçmişi.
import collections as _c
RSS = _c.deque(maxlen=240)


def _rss_mb():
    try:
        return int(open("/proc/self/statm").read().split()[1]) * 4096 / 1e6
    except Exception:
        return None


def _mem_loop():
    import ctypes
    try:
        trim = ctypes.CDLL("libc.so.6").malloc_trim
    except Exception:
        trim = None
    while True:
        time.sleep(60)
        try:
            a = _rss_mb()
            if trim:
                trim(0)
            RSS.append((int(time.time()), round(a or 0), round(_rss_mb() or 0)))
        except Exception:
            pass


threading.Thread(target=_mem_loop, daemon=True, name="v137-mem").start()


@router.get("/api/progress/mem")
def api_mem():
    return {"rss_mb": round(_rss_mb() or 0), "hist": list(RSS)[-60:]}
