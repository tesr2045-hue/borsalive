"""v1.35.0 LİNK OPTİMİZASYON — ngrok tünel durumu, kota tahmini, yeni link oluşturma.

Kota kaynağı: ngrok resmi "Free Plan Limits" (ngrok.com/docs/pricing-limits/free-plan-limits, 10.10.2026):
aylık 20.000 HTTP isteği, 1 GB dışa veri, dakikada 4.000 istek. ngrok bulut API'si (api.ngrok.com) ücretsiz
plan kullanım/kota verisini döndürmüyor; bu yüzden sayaç bizim (tünelden gelen istekleri sayan ASGI ara katmanı)
+ ngrok yerel ajanı (127.0.0.1:4040) metrikleri. Değerler TAHMİNDİR (başka cihaz/tünel kullanımı görünmez).
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "v135"
DATA.mkdir(parents=True, exist_ok=True)
USAGE_F = DATA / "ngrok_usage.json"
KEY_F = DATA / "ngrok_api_key.json"
URL_F = ROOT / "ops" / "public_url.txt"
LIMIT_REQ = 20000
LIMIT_BYTES = 1_000_000_000
LIMIT_RPM = 4000
SRC = "ngrok.com/docs/pricing-limits/free-plan-limits (Free: 20.000 istek/ay, 1 GB veri/ay, 4.000 istek/dk)"
NEW_LINK_GAP = 120.0

TOK_F = ROOT / "data" / "ngrok_tokens.json"
YML = Path.home() / ".config" / "ngrok" / "ngrok.yml"
NGROK_BIN = "/workspace/ngrok"
AUTO_PCT = 90.0
_tok_lock = threading.RLock()
_tok = {"auto": True, "accounts": []}
_cur_id = [None]


def _tid(token: str) -> str:
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()[:12]


def _yml_token():
    try:
        for ln in YML.read_text().splitlines():
            if ln.strip().startswith("authtoken:"):
                return ln.split(":", 1)[1].strip().strip('"').strip("'") or None
    except Exception:
        pass
    return None


def _tok_save():
    fd = os.open(str(TOK_F), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(_tok, f)
    os.chmod(TOK_F, 0o600)


def _tok_load():
    global _tok
    try:
        d = json.loads(TOK_F.read_text())
        if isinstance(d, dict) and isinstance(d.get("accounts"), list):
            _tok = d
    except Exception:
        pass
    cur = _yml_token()
    if cur and not any(a.get("token") == cur for a in _tok["accounts"]):
        _tok["accounts"].insert(0, {"id": _tid(cur), "label": "endersener08", "token": cur,
                                    "month": _month(), "req": _u.get("req", 0), "bytes": _u.get("bytes", 0)})
    _cur_id[0] = _tid(cur) if cur else None
    _tok_save()


def _acc_roll(a):
    if a.get("month") != _month():
        a.update({"month": _month(), "req": 0, "bytes": 0})


def _acc_pct(a):
    _acc_roll(a)
    return max(a.get("req", 0) / LIMIT_REQ * 100, a.get("bytes", 0) / LIMIT_BYTES * 100)


def _write_yml(token: str):
    txt = 'version: "3"\nagent:\n  crl_noverify: true\n  authtoken: ' + token + "\n"
    old = YML.read_text() if YML.exists() else None
    fd = os.open(str(YML) + ".new", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(txt)
    os.replace(str(YML) + ".new", str(YML))
    r = subprocess.run([NGROK_BIN, "config", "check"], capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        if old is not None:
            YML.write_text(old); os.chmod(YML, 0o600)
        raise HTTPException(500, "ngrok config check başarısız — eski ayar geri yüklendi")


router = APIRouter()
_lock = threading.Lock()
_u = {"month": None, "req": 0, "bytes": 0, "by_day": {}}
_minute: list[float] = []
_last_new = 0.0
_dirty = False


def _month():
    return time.strftime("%Y-%m")


def _load():
    global _u
    try:
        d = json.loads(USAGE_F.read_text())
        if isinstance(d, dict):
            _u.update(d)
    except Exception:
        pass


def _roll():
    m = _month()
    if _u.get("month") != m:
        _u.update({"month": m, "req": 0, "bytes": 0, "by_day": {}})


def _save():
    global _dirty
    with _lock:
        if not _dirty:
            return
        raw = json.dumps(_u)
        _dirty = False
    tmp = USAGE_F.with_suffix(".tmp")
    tmp.write_text(raw)
    tmp.replace(USAGE_F)


def _saver():
    while True:
        time.sleep(20)
        try:
            _save()
            with _tok_lock:
                _tok_save()
            if _tok.get("auto"):
                _auto_switch()
        except Exception:
            pass


def _auto_switch():
    with _tok_lock:
        cur = next((a for a in _tok["accounts"] if a.get("id") == _cur_id[0]), None)
        if not cur or _acc_pct(cur) < AUTO_PCT or len(_tok["accounts"]) < 2:
            return
    if time.time() - _last_new < 600:
        return
    try:
        _do_new(switch=True, auto=True)
    except Exception:
        pass


_load()
_tok_load()
threading.Thread(target=_saver, name="v135-save", daemon=True).start()


def _count(nbytes: int):
    global _dirty
    now = time.time()
    with _lock:
        _roll()
        _u["req"] += 1
        _u["bytes"] += nbytes
        d = time.strftime("%m-%d")
        bd = _u.setdefault("by_day", {})
        e = bd.setdefault(d, [0, 0])
        e[0] += 1; e[1] += nbytes
        _minute.append(now)
        cid = _cur_id[0]
        if cid:
            with _tok_lock:
                for a in _tok["accounts"]:
                    if a.get("id") == cid:
                        _acc_roll(a); a["req"] = a.get("req", 0) + 1; a["bytes"] = a.get("bytes", 0) + nbytes
                        break
        if len(_minute) > 6000:
            del _minute[:3000]
        _dirty = True


class TunnelCounter:
    """Saf ASGI ara katmanı: yalnız ngrok üzerinden gelen (Host *.ngrok*) HTTP isteklerini ve yanıt baytlarını sayar."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        host = ""
        fwd = False
        for k, v in scope.get("headers") or []:
            if k == b"host":
                host = v.decode("latin-1")
            elif k == b"x-forwarded-for":
                fwd = True
        if "ngrok" not in host and not fwd:
            return await self.app(scope, receive, send)
        n = [600]  # ~istek+yanıt başlıkları

        async def _send(msg):
            if msg.get("type") == "http.response.body":
                n[0] += len(msg.get("body") or b"")
            await send(msg)
        try:
            await self.app(scope, receive, _send)
        finally:
            _count(n[0])


ACTIVE_F = ROOT / "data" / "ngrok_active.json"   # keepalive'ın okuduğu etkin config + web portu


def _active():
    try:
        d = json.loads(ACTIVE_F.read_text())
        if d.get("cfg") and d.get("port"):
            return d
    except Exception:
        pass
    return {"cfg": str(Path.home() / ".config" / "ngrok" / "ngrok.yml"), "port": 4040}


def _tunnels(port=None):
    port = port or _active()["port"]
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/tunnels", timeout=2) as r:
            d = json.loads(r.read())
        return [t for t in d.get("tunnels", []) if str(t.get("public_url", "")).startswith("https")]
    except Exception:
        return None


def _ngrok_pids():
    try:
        out = subprocess.run(["pgrep", "-x", "ngrok"], capture_output=True, text=True, timeout=3).stdout
        return [int(x) for x in out.split()]
    except Exception:
        return []


def _key():
    try:
        return (json.loads(KEY_F.read_text()) or {}).get("key") or None
    except Exception:
        return None


def _cloud_check(key: str):
    """API anahtarını doğrular (uç nokta listesi). ngrok API ücretsiz planda kullanım/kota vermez."""
    try:
        req = urllib.request.Request("https://api.ngrok.com/endpoints?limit=5",
                                     headers={"Authorization": "Bearer " + key, "Ngrok-Version": "2"})
        with urllib.request.urlopen(req, timeout=6) as r:
            d = json.loads(r.read())
        return {"ok": True, "endpoints": [e.get("public_url") or e.get("hostport") for e in d.get("endpoints", [])]}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}" + (" (anahtar geçersiz)" if e.code in (401, 403) else "")}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}


def _acc_view():
    out = []
    with _tok_lock:
        for a in _tok["accounts"]:
            _acc_roll(a)
            pr, pb = a["req"] / LIMIT_REQ * 100, a["bytes"] / LIMIT_BYTES * 100
            out.append({"id": a["id"], "label": a.get("label"), "last4": a["token"][-4:], "current": a["id"] == _cur_id[0],
                        "req": a["req"], "bytes": a["bytes"], "req_pct": round(pr, 1), "bytes_pct": round(pb, 1),
                        "remaining_req": max(0, LIMIT_REQ - a["req"]), "remaining_bytes": max(0, LIMIT_BYTES - a["bytes"]),
                        "remaining_pct": round(max(0, 100 - max(pr, pb)), 1)})
    return out


# ------------------------------------------------------------------ v1.36.0 CLOUDFLARE QUICK TUNNEL
CF_STATE = ROOT / "ops" / "cf_state.json"
CF_URL = ROOT / "ops" / "cf_url.txt"
CF_KA = ROOT / "ops" / "cf-keepalive.sh"
PRIM_F = ROOT / "data" / "v136" / "link_primary.json"
_cf = {"last_ok": None, "fails": 0, "checks": 0, "last_err": None, "last_check": None}
_cf_last_new = 0.0


def _cf_state():
    try:
        return json.loads(CF_STATE.read_text())
    except Exception:
        return {}


def _cf_ka_pids():
    out = []
    for d in Path("/proc").iterdir():
        if not d.name.isdigit():
            continue
        try:
            a = open(d / "cmdline", "rb").read().split(b"\0")
            if any(x.endswith(b"cf-keepalive.sh") for x in a[:3]):
                out.append(int(d.name))
        except Exception:
            pass
    return out


def _cf_pids():
    try:
        return [int(x) for x in subprocess.run(["pgrep", "-x", "cloudflared"], capture_output=True, text=True, timeout=3).stdout.split()]
    except Exception:
        return []


def _primary():
    try:
        return json.loads(PRIM_F.read_text()).get("p") or "ngrok"
    except Exception:
        return "ngrok"


def _cf_loop():
    time.sleep(20)
    while True:
        try:
            if CF_KA.exists() and not (ROOT / "ops" / "cf_disabled").exists() and not _cf_ka_pids():
                subprocess.Popen(["setsid", "nohup", str(CF_KA)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 stdin=subprocess.DEVNULL, start_new_session=True)
            stt = _cf_state()
            if stt.get("registered") and stt.get("url"):
                _cf["checks"] += 1; _cf["last_check"] = time.time()
                if _pub_ok(stt["url"]):
                    _cf["last_ok"] = time.time(); _cf["fails"] = 0; _cf["last_err"] = None
                else:
                    _cf["fails"] += 1; _cf["last_err"] = "/api/health yanıt vermedi"
        except Exception as e:
            _cf["last_err"] = type(e).__name__
        time.sleep(30)


threading.Thread(target=_cf_loop, name="v136-cf", daemon=True).start()


def _cf_view():
    stt = _cf_state()
    now = time.time()
    reg = bool(stt.get("registered"))
    healthy = bool(reg and _cf["last_ok"] and now - _cf["last_ok"] < 90)
    return {"url": stt.get("url") if reg else None, "url_pending": stt.get("url") if not reg else None,
            "registered": reg, "healthy": healthy, "start": stt.get("start"),
            "uptime_sec": int(now - stt["start"]) if reg and stt.get("start") else None,
            "last_ok": _cf["last_ok"], "last_ok_ago": int(now - _cf["last_ok"]) if _cf["last_ok"] else None,
            "fails": _cf["fails"], "checks": _cf["checks"], "err": stt.get("err") or _cf["last_err"],
            "next_retry_in": max(0, int(stt.get("next_retry", 0) - now)) if stt.get("next_retry") else 0,
            "keepalive": bool(_cf_ka_pids()), "running": bool(_cf_pids()),
            "new_wait": max(0, int(NEW_LINK_GAP - (now - _cf_last_new))),
            "note": "Cloudflare quick tunnel (trycloudflare.com): hesap yok, istek/veri kotası yok; ama link her yeniden başlatmada değişir ve garanti/SLA yoktur."}


@router.get("/api/link/cf/status")
def cf_status():
    return _cf_view()


@router.post("/api/link/cf/new")
def cf_new():
    global _cf_last_new
    now = time.time()
    if now - _cf_last_new < NEW_LINK_GAP:
        raise HTTPException(429, f"Yeni Cloudflare linki için {int(NEW_LINK_GAP - (now - _cf_last_new))} sn bekle")
    _cf_last_new = now
    old = _cf_state().get("url")
    pids = _cf_pids()
    for p in pids:
        try: os.kill(p, signal.SIGTERM)
        except Exception: pass
    if not pids:
        v = _cf_view()
        return {"ok": False, "note": f"cloudflared şu an çalışmıyor (bekçi beklemede, {v['next_retry_in']} sn sonra tekrar dener). Son hata: {v['err'] or '—'}"}
    new = None; t0 = time.time()
    while time.time() - t0 < 60:
        time.sleep(2)
        stt = _cf_state()
        if stt.get("registered") and stt.get("url") and stt["url"] != old:
            new = stt["url"]; break
        if stt.get("err") and stt.get("ts", 0) > now:
            break
    if new and _pub_ok(new):
        _cf["last_ok"] = time.time(); _cf["fails"] = 0
    return {"ok": bool(new), "url": new, "old": old, "note": None if new else ("Cloudflare'e bağlanılamadı: " + (_cf_state().get("err") or "zaman aşımı"))}


@router.post("/api/link/primary")
def link_primary(body: dict = Body(...)):
    p = (body or {}).get("p")
    if p not in ("ngrok", "cf"):
        raise HTTPException(400, "ngrok | cf")
    PRIM_F.parent.mkdir(parents=True, exist_ok=True)
    PRIM_F.write_text(json.dumps({"p": p}))
    return {"ok": True, "primary": p}


@router.get("/api/link/status")
def link_status(cloud: bool = False):
    now = time.time()
    tl = _tunnels()
    t = tl[0] if tl else None
    with _lock:
        _roll()
        req, by = _u["req"], _u["bytes"]
        rpm = sum(1 for x in _minute if now - x < 60)
        days = dict(sorted((_u.get("by_day") or {}).items())[-7:])
    m = (t or {}).get("metrics") or {}
    dom = int(time.strftime("%d"))
    proj_req = int(req / max(dom - 1 + (time.localtime().tm_hour + 1) / 24, 0.05) * 30)
    pr, pb = req / LIMIT_REQ * 100, by / LIMIT_BYTES * 100
    warn = []
    if pr >= 80: warn.append(f"İstek kotası %{pr:.0f} — yakında dolabilir, yeni link/hesap hazırla")
    if pb >= 80: warn.append(f"Veri kotası %{pb:.0f} — yakında dolabilir")
    if rpm >= LIMIT_RPM * 0.8: warn.append("Dakikalık istek sınırına yakın")
    url = (t or {}).get("public_url")
    try:
        saved = URL_F.read_text().strip()
    except Exception:
        saved = None
    out = {
        "url": url or saved, "tunnel_up": bool(url), "saved_url": saved,
        "ngrok_running": bool(_ngrok_pids()),
        "session": {"conns": (m.get("conns") or {}).get("count"), "http": (m.get("http") or {}).get("count"),
                    "rate1_per_min": round(((m.get("http") or {}).get("rate1") or 0) * 60, 1)},
        "month": {"month": _u.get("month"), "req": req, "bytes": by, "req_pct": round(pr, 1), "bytes_pct": round(pb, 1),
                  "req_limit": LIMIT_REQ, "bytes_limit": LIMIT_BYTES, "proj_req": proj_req, "rpm": rpm,
                  "rpm_limit": LIMIT_RPM, "by_day": days},
        "warn": warn, "source": SRC,
        "note": "Tahmini: sayaç bu sunucunun tünelden aldığı istekleri sayar (v1.35.0'dan itibaren). ngrok panelindeki "
                "gerçek değer farklı olabilir; ngrok API ücretsiz planda kullanım/kota vermiyor.",
        "has_api_key": bool(_key()),
        "redirect": (_redirect if now - _redirect["ts"] < 900 else None) if _primary() == "ngrok" else None,
        "cf": _cf_view(), "primary": _primary(), "web_port": _active()["port"],
        "accounts": _acc_view(), "auto_switch": bool(_tok.get("auto")), "auto_pct": AUTO_PCT,
        "new_link_wait": max(0, int(NEW_LINK_GAP - (now - _last_new))),
    }
    pu = None
    if out["primary"] == "cf" and out["cf"]["healthy"]:
        pu = out["cf"]["url"]
    elif out["primary"] == "ngrok" and out["tunnel_up"]:
        pu = out["url"]
    out["primary_url"] = pu
    if cloud and out["has_api_key"]:
        out["cloud"] = _cloud_check(_key())
    return out


def _write_cfg(path: Path, token: str, port: int):
    txt = ('version: "3"\nagent:\n  authtoken: ' + token + '\n  crl_noverify: true\n  web_addr: 127.0.0.1:' + str(port) + "\n")
    fd = os.open(str(path) + ".new", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(txt)
    os.replace(str(path) + ".new", str(path))
    r = subprocess.run([NGROK_BIN, "config", "check", "--config", str(path)], capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        raise HTTPException(500, "ngrok config check başarısız")


def _pub_ok(url: str) -> bool:
    try:
        req = urllib.request.Request(url + "/api/health", headers={"ngrok-skip-browser-warning": "1"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status == 200 and b"version" in r.read(4000)
    except Exception:
        return False


def _pids_on_port(port: int):
    """ngrok PID'leri: web portu bu olan (komut satırı config'inden)."""
    out = []
    act = _active()
    for pid in _ngrok_pids():
        try:
            cmd = open(f"/proc/{pid}/cmdline", "rb").read().decode(errors="ignore").replace("\0", " ")
        except Exception:
            continue
        cfgp = None
        for part in cmd.split():
            if part.startswith("--config="):
                cfgp = part.split("=", 1)[1]
        pport = 4040
        if cfgp:
            try:
                for ln in Path(cfgp).read_text().splitlines():
                    if "web_addr:" in ln:
                        pport = int(ln.rsplit(":", 1)[1])
            except Exception:
                pass
        if pport == port:
            out.append(pid)
    return out


_switch_lock = threading.Lock()


def _do_new(switch: bool, auto: bool = False, target_id: str | None = None):
    global _last_new
    if not _switch_lock.acquire(blocking=False):
        raise HTTPException(409, "Geçiş zaten sürüyor")
    try:
        _last_new = time.time()
        act = _active()
        tl = _tunnels()
        old = tl[0].get("public_url") if tl else None
        acc = None
        with _tok_lock:
            if target_id:
                acc = next((x for x in _tok["accounts"] if x["id"] == target_id), None)
                if not acc:
                    raise HTTPException(404, "Hesap yok")
            elif switch:
                others = [x for x in _tok["accounts"] if x.get("id") != _cur_id[0]]
                if others:
                    acc = min(others, key=_acc_pct)
            if acc is None:
                acc = next((x for x in _tok["accounts"] if x.get("id") == _cur_id[0]), None)
        if acc is None:
            raise HTTPException(400, "Kayıtlı ngrok hesabı yok")
        same = acc["id"] == _cur_id[0]
        old_pids = _pids_on_port(act["port"])
        if same:
            # aynı hesap: ücretsiz hesapta 2. eşzamanlı oturum reddedilebilir → klasik yeniden başlatma (kısa kesinti)
            for p in old_pids:
                try: os.kill(p, signal.SIGTERM)
                except Exception: pass
            new = None; t0 = time.time()
            while time.time() - t0 < 40:
                time.sleep(1.5)
                t2 = _tunnels()
                if t2 and t2[0].get("public_url") and t2[0]["public_url"] != old:
                    new = t2[0]["public_url"]; break
        else:
            # SIFIR KESİNTİ: yeni hesabın ajanını ayrı config + ayrı web portuyla önce başlat, doğrula, sonra eskiyi durdur
            port = 4041 if int(act["port"]) != 4041 else 4040
            cfg = ROOT / "data" / f"ngrok_{port}.yml"
            _write_cfg(cfg, acc["token"], port)
            for p in _pids_on_port(port):
                try: os.kill(p, signal.SIGTERM)
                except Exception: pass
            logf = open("/workspace/ngrok.log", "ab")
            proc = subprocess.Popen([NGROK_BIN, "http", "8765", f"--config={cfg}", "--log=stdout"], stdout=logf,
                                    stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
            new = None; t0 = time.time()
            while time.time() - t0 < 45:
                time.sleep(1.5)
                if proc.poll() is not None:
                    break
                t2 = _tunnels(port)
                if t2 and t2[0].get("public_url"):
                    u = t2[0]["public_url"]
                    if _pub_ok(u):
                        new = u; break
            if not new:
                try: proc.terminate()
                except Exception: pass
                return {"ok": False, "old": old, "url": None, "account": acc.get("label"), "quota_reset": False,
                        "note": "Yeni hesabın tüneli doğrulanamadı (token geçersiz olabilir) — eski link aynen çalışıyor."}
            tmp = ACTIVE_F.with_suffix(".tmp"); tmp.write_text(json.dumps({"cfg": str(cfg), "port": port})); tmp.replace(ACTIVE_F)
            try:
                _write_yml(acc["token"])   # ~/.config/ngrok/ngrok.yml da etkin token'ı tutsun
            except Exception:
                pass
            _cur_id[0] = acc["id"]
            def _later(pids=old_pids):
                time.sleep(30)   # açık sayfalar (20 sn yoklama) yeni linke eski tünelden yönlensin
                for p in pids:
                    try: os.kill(p, signal.SIGTERM)
                    except Exception: pass
            threading.Thread(target=_later, daemon=True).start()
        if new:
            global _redirect
            _redirect = {"from": old, "to": new, "ts": time.time()}
            try:
                URL_F.write_text(new + "\n")
            except Exception:
                pass
        return {"ok": bool(new), "old": old, "url": new, "auto": auto, "account": acc.get("label"),
                "quota_reset": not same, "zero_downtime": not same,
                "note": None if (new and not same) else ("Aynı hesap — kota SIFIRLANMADI." if new else
                        "ngrok yeniden başlatıldı; yeni link henüz gelmedi, birkaç sn sonra durumu yenile.")}
    finally:
        _switch_lock.release()


_redirect = {"from": None, "to": None, "ts": 0}


@router.post("/api/link/switch")
def link_switch(body: dict = Body(...)):
    now = time.time()
    if now - _last_new < NEW_LINK_GAP:
        raise HTTPException(429, f"Yeni geçiş için {int(NEW_LINK_GAP - (now - _last_new))} sn bekle")
    return _do_new(switch=True, target_id=str((body or {}).get("id") or ""))


@router.post("/api/link/new")
def link_new(body: dict | None = Body(None)):
    now = time.time()
    if now - _last_new < NEW_LINK_GAP:
        raise HTTPException(429, f"Yeni link için {int(NEW_LINK_GAP - (now - _last_new))} sn bekle")
    switch = (body or {}).get("switch", True)
    return _do_new(switch=bool(switch))


@router.post("/api/link/accounts")
def link_acc_add(body: dict = Body(...)):
    label = str((body or {}).get("label") or "").strip()[:40]
    token = str((body or {}).get("token") or "").strip()
    import re as _re
    if not label or not _re.fullmatch(r"[A-Za-z0-9_\-]{20,120}", token):
        raise HTTPException(400, "Etiket ve geçerli bir ngrok authtoken gerekli")
    with _tok_lock:
        if any(a["token"] == token for a in _tok["accounts"]):
            raise HTTPException(400, "Bu token zaten ekli")
        _tok["accounts"].append({"id": _tid(token), "label": label, "token": token, "month": _month(), "req": 0, "bytes": 0})
        _tok_save()
    return {"ok": True, "accounts": _acc_view()}


@router.post("/api/link/accounts/delete")
def link_acc_del(body: dict = Body(...)):
    aid = str((body or {}).get("id") or "")
    if aid == _cur_id[0]:
        raise HTTPException(400, "Kullanımdaki hesap silinemez — önce başka hesaba geç")
    with _tok_lock:
        _tok["accounts"] = [a for a in _tok["accounts"] if a["id"] != aid]
        _tok_save()
    return {"ok": True, "accounts": _acc_view()}


@router.post("/api/link/auto")
def link_auto(body: dict = Body(...)):
    with _tok_lock:
        _tok["auto"] = bool((body or {}).get("on"))
        _tok_save()
    return {"ok": True, "auto_switch": _tok["auto"]}


@router.post("/api/link/apikey")
def link_apikey(body: dict = Body(...)):
    key = str((body or {}).get("key") or "").strip()
    if not key:
        try:
            KEY_F.unlink()
        except FileNotFoundError:
            pass
        return {"ok": True, "has_api_key": False}
    if len(key) < 20 or len(key) > 200:
        raise HTTPException(400, "Geçersiz anahtar")
    chk = _cloud_check(key)
    fd = os.open(str(KEY_F), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump({"key": key}, f)
    os.chmod(KEY_F, 0o600)
    return {"ok": True, "has_api_key": True, "cloud": chk}
