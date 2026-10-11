"""v1.29.0 — EN İYİ KOŞULLAR: tek yapılandırma (app/eik_config.json) + Birleşik Aday Listesi.
Çekirdek yalnız stdlib kullanır (sunucunun kendi uç noktalarını yerelden çağırır) → hazırlık ortamında da aynı kod çalışır."""
from __future__ import annotations
import json, os, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eik_config.json")
SELF = os.environ.get("EIK_SELF", "http://127.0.0.1:8765")
_lock = threading.Lock()
_cache: dict = {"cfg": None, "mt": 0.0, "bir": None, "bir_ts": 0.0}
BIR_TTL = 60.0
MIN_HIT = 3


def load_cfg() -> dict:
    mt = os.path.getmtime(CFG_PATH)
    with _lock:
        if _cache["cfg"] is None or mt != _cache["mt"]:
            with open(CFG_PATH, encoding="utf-8") as f:
                _cache["cfg"] = json.load(f)
            _cache["mt"] = mt
        return _cache["cfg"]


def _get(path: str, timeout: float = 30.0) -> dict:
    with urllib.request.urlopen(SELF + path, timeout=timeout) as r:
        return json.loads(r.read())


def _scan_url(t: dict) -> str | None:
    fid = t.get("id")
    if t.get("v") != "op" or fid is None:
        return None
    if isinstance(fid, str) and fid.startswith("k_"):
        return f"/api/k/f/{fid}" + (f"?w={t['w']}" if t.get("w") else "")
    if isinstance(fid, str) and fid.startswith("op_"):
        return f"/api/op/f/{int(fid[3:])}"
    if fid in ("kademe", "teknik"):
        return f"/api/op/mk/{fid}"
    return None


def _syms(it: dict) -> tuple[str, list[str], str]:
    t = it["tgt"]; url = _scan_url(t)
    if not url:
        return it["id"], [], ""
    d = _get(url)
    rows, seen = [], set()
    for r in d.get("rows") or []:
        s = r.get("s")
        if s and s not in seen:
            seen.add(s); rows.append(r)
    flt = t.get("filt")
    if flt and t.get("id") == "teknik":
        rows = [r for r in rows if r.get("vk") == flt]
    if flt and t.get("id") == "kademe":
        rows = [r for r in rows if ((r.get("net") or 0) > 0) == (flt == "alici")]
    k = t.get("sort")
    top = 20
    if k and t.get("id") not in ("k_ciddi", "k_poc", "k_aort"):
        rows = sorted([r for r in rows if isinstance(r.get(k), (int, float))], key=lambda r: -r[k] if (t.get("dir") or -1) < 0 else r[k])[:top]
    elif len(rows) > 60:
        rows = rows[:top]
    return it["id"], [r["s"] for r in rows], d.get("day_label") or ""


def birlesik(force: bool = False) -> dict:
    now = time.time()
    with _lock:
        if not force and _cache["bir"] is not None and now - _cache["bir_ts"] < BIR_TTL:
            return _cache["bir"]
    cfg = load_cfg()
    its = [i for i in cfg["items"] if i.get("bir") and _scan_url(i["tgt"])]
    names = {i["id"]: f'{i["f"]} — {i["c"]}' for i in its}
    hits: dict[str, list[str]] = {}
    errs, day = [], ""
    with ThreadPoolExecutor(max_workers=6) as ex:
        for fut in [ex.submit(_syms, i) for i in its]:
            try:
                iid, ss, dl = fut.result(timeout=60)
                day = day or dl
                for s in ss:
                    hits.setdefault(s, []).append(iid)
            except Exception as e:  # tek tarayıcı hatası listeyi düşürmez
                errs.append(str(e)[:120])
    rows = sorted(({"s": s, "n": len(v), "src": v} for s, v in hits.items() if len(v) >= MIN_HIT), key=lambda r: (-r["n"], r["s"]))
    out = {"rows": rows, "scans": len(its), "names": names, "min": MIN_HIT, "day_label": day, "errors": errs,
           "ts": time.strftime("%H:%M:%S"), "updated": cfg.get("updated_label")}
    with _lock:
        _cache["bir"], _cache["bir_ts"] = out, now
    return out


try:
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/api/eik")
    def eik_cfg():
        return load_cfg()

    @router.get("/api/eik/birlesik")
    def eik_birlesik(force: bool = False):
        return birlesik(force)
except Exception:  # hazırlık vekilinde fastapi olmayabilir
    router = None
