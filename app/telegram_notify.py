"""v1.38.0 — TELEGRAM BİLDİRİMLERİ (OneSignal'ın yerine).
* Bot API (https://api.telegram.org/bot<TOKEN>/sendMessage) → kullanıcının kanalı/sohbeti (chat_id: @kanal ya da -100…).
* Sinyaller: v120 hub._emit → BİLDİRİM modundaki her tür (tür modları + kapsam/eşik filtreleri, "sahip" istemcinin
  ayarlarından — eskiden OneSignal'a giden cihazın ayarları aynen taşındı). Sistem: link değişti, tünel düştü/geldi,
  İdealData bağlandı/koptu/giriş reddedildi, sunucu yeniden başladı, kota %80/%90, hatalar.
* Kuyruk diske yazılır (data/telegram_queue.json) → yeniden başlatmada kayıp yok; dakikada ≤18 mesaj (Telegram ~20/dk/kanal),
  birikince birleştirir; 429'da retry_after, diğer hatalarda artan bekleme (5 sn → 5 dk); aynı metin 3 dk içinde tekrar edilmez.
* Token data/telegram.json'da (chmod 600) — hiçbir yanıtta dönmez, loglanmaz (yalnız son 4 hane).
* TELEGRAM_DRYRUN=1 (ya da ayarlarda dry) → gönderilmez, data/telegram_dryrun.log'a yazılır. TELEGRAM_API ile sahte sunucu (test).
"""
from __future__ import annotations

import collections
import hashlib
import html
import json
import logging
import os
import re
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger("bist.telegram")
ROOT = Path(__file__).resolve().parents[1]
CFG_F = ROOT / "data" / "telegram.json"
Q_F = ROOT / "data" / "telegram_queue.json"
DRY_F = ROOT / "data" / "telegram_dryrun.log"
API = os.environ.get("TELEGRAM_API", "https://api.telegram.org")
PER_MIN = 18
DEDUP_SEC = 180
CATS = {"sistem": "Sistem bildirimleri (sunucu, İdealData, tünel, kota, hata)", "link": "Link değişiklikleri (yeni ngrok / Cloudflare adresi)",
        "sinyal": "Sinyaller (tür bazında aşağıdaki BİLDİRİM modları)"}


def _now_s():
    return time.strftime("%d.%m %H:%M:%S", time.gmtime(time.time() + 3 * 3600))


def _esc(s):
    return html.escape(str(s if s is not None else ""), quote=False)


class Telegram:
    def __init__(self):
        self.lock = threading.RLock()
        self.cfg = {"token": None, "chat_id": None, "owner_cid": None, "cats": {k: True for k in CATS},
                    "quiet": {"on": False, "from": "23:00", "to": "08:00"}, "dry": False}
        self.st = {"last_sent": None, "last_err": None, "last_err_ts": None, "sent": 0, "failed": 0, "merged": 0, "deduped": 0,
                   "dropped_quiet": 0, "next_try": 0}
        self.q: list = []
        self.sent_ts = collections.deque(maxlen=PER_MIN)
        self.recent: dict = {}
        self.ev = threading.Event()
        self.hub = None
        self.feed = None
        self._load()

    # ------------------------------------------------------------ kalıcılık
    def _load(self):
        try:
            d = json.loads(CFG_F.read_text(encoding="utf-8"))
            for k in ("token", "chat_id", "owner_cid", "dry"):
                if k in d:
                    self.cfg[k] = d[k]
            self.cfg["cats"].update(d.get("cats") or {})
            self.cfg["quiet"].update(d.get("quiet") or {})
            self.st.update({k: d.get("st", {}).get(k) for k in ("last_sent", "last_err", "sent", "failed") if d.get("st", {}).get(k) is not None})
        except Exception:
            pass
        try:
            self.q = json.loads(Q_F.read_text(encoding="utf-8"))[-2000:]
        except Exception:
            self.q = []

    def _save_cfg(self):
        CFG_F.parent.mkdir(parents=True, exist_ok=True)
        d = dict(self.cfg); d["st"] = {k: self.st[k] for k in ("last_sent", "last_err", "sent", "failed")}
        fd = os.open(str(CFG_F) + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(str(CFG_F) + ".tmp", CFG_F)
        os.chmod(CFG_F, 0o600)

    def _save_q(self):
        try:
            tmp = str(Q_F) + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.q[-2000:], f, ensure_ascii=False)
            os.replace(tmp, Q_F)
        except Exception as e:
            logger.debug("tg queue save: %s", e)

    # ------------------------------------------------------------ yardımcılar
    def dry(self):
        return os.environ.get("TELEGRAM_DRYRUN") == "1" or bool(self.cfg.get("dry"))

    def ready(self):
        return bool(self.cfg.get("chat_id")) and (bool(self.cfg.get("token")) or self.dry())

    @staticmethod
    def public_url():
        try:
            p = json.loads((ROOT / "data" / "v136" / "link_primary.json").read_text()).get("primary")
        except Exception:
            p = None
        for f in (["cf_url.txt", "public_url.txt"] if p == "cf" else ["public_url.txt", "cf_url.txt"]):
            try:
                u = (ROOT / "ops" / f).read_text().strip()
                if u.startswith("http"):
                    return u.rstrip("/")
            except Exception:
                pass
        return None

    def _quiet(self):
        q = self.cfg.get("quiet") or {}
        if not q.get("on"):
            return False
        try:
            t = time.gmtime(time.time() + 3 * 3600); m = t.tm_hour * 60 + t.tm_min
            a = [int(x) for x in q.get("from", "23:00").split(":")]; b = [int(x) for x in q.get("to", "08:00").split(":")]
            fa, tb = a[0] * 60 + a[1], b[0] * 60 + b[1]
            return (fa <= m < tb) if fa < tb else (m >= fa or m < tb)
        except Exception:
            return False

    def _api(self, method, params=None, timeout=15):
        tok = self.cfg.get("token") or ""
        url = f"{API}/bot{tok}/{method}"
        data = urllib.parse.urlencode(params or {}).encode() if params is not None else None
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode())
            except Exception:
                return {"ok": False, "error_code": e.code, "description": f"HTTP {e.code}"}
        except Exception as e:
            msg = str(e)
            if tok:
                msg = msg.replace(tok, "***")
            return {"ok": False, "error_code": 0, "description": msg[:200]}

    # ------------------------------------------------------------ kuyruk
    def enqueue(self, cat, text, key=None, prio=False):
        """text: HTML (Telegram parse_mode=HTML). cat: sistem | link | sinyal | test."""
        try:
            if cat != "test":
                if not (self.cfg.get("cats") or {}).get(cat, True):
                    return False
                if not self.ready():
                    return False
                if cat == "sinyal" and self._quiet():
                    self.st["dropped_quiet"] += 1
                    return False
            h = hashlib.sha1((key or text).encode("utf-8", "ignore")).hexdigest()[:16]
            now = time.time()
            with self.lock:
                for k, t in list(self.recent.items()):
                    if now - t > DEDUP_SEC:
                        self.recent.pop(k, None)
                if cat != "test" and h in self.recent:
                    self.st["deduped"] += 1
                    return False
                self.recent[h] = now
                item = {"cat": cat, "text": text[:3800], "ts": now, "tries": 0}
                if prio:
                    self.q.insert(0, item)
                else:
                    self.q.append(item)
                if len(self.q) > 2000:
                    self.q = self.q[-2000:]
                self._save_q()
            self.ev.set()
            return True
        except Exception as e:
            logger.debug("tg enqueue: %s", e)
            return False

    def _take(self):
        """Sıradaki mesaj; birikme varsa (≥4) aynı kategoriden en çok 12 mesajı tek mesajda birleştir."""
        with self.lock:
            if not self.q:
                return None, 0
            first = self.q[0]
            if len(self.q) >= 4 and first["cat"] in ("sinyal", "sistem"):
                grp, n = [], 0
                for it in self.q:
                    if it["cat"] != first["cat"] or n >= 12 or sum(len(x) for x in grp) + len(it["text"]) > 3600:
                        break
                    grp.append(it["text"]); n += 1
                if n > 1:
                    return {"cat": first["cat"], "text": f"📦 <b>{n} bildirim</b> (birleştirildi)\n\n" + "\n──────\n".join(grp), "tries": first.get("tries", 0)}, n
            return first, 1

    def _send(self, text):
        chat = self.cfg.get("chat_id")
        if self.dry():
            with open(DRY_F, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": _now_s(), "chat_id": chat, "text": text}, ensure_ascii=False) + "\n")
            return {"ok": True, "dry": True}
        return self._api("sendMessage", {"chat_id": chat, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"})

    def _worker(self):
        back = 5
        while True:
            self.ev.wait(5); self.ev.clear()
            try:
                while self.q and self.ready():
                    if time.time() < self.st["next_try"]:
                        break
                    if len(self.sent_ts) >= PER_MIN and time.time() - self.sent_ts[0] < 60:
                        time.sleep(max(0.5, 60 - (time.time() - self.sent_ts[0])))
                        continue
                    it, n = self._take()
                    if not it:
                        break
                    r = self._send(it["text"])
                    if r.get("ok"):
                        self.sent_ts.append(time.time())
                        with self.lock:
                            del self.q[:n]
                            self._save_q()
                        self.st["sent"] += 1; self.st["merged"] += n - 1 if n > 1 else 0
                        self.st["last_sent"] = _now_s(); back = 5
                        time.sleep(1.1)
                        continue
                    code = r.get("error_code")
                    desc = str(r.get("description") or "")[:200]
                    self.st["failed"] += 1; self.st["last_err"] = f"{code} {desc}".strip(); self.st["last_err_ts"] = _now_s()
                    if code == 429:
                        ra = int(((r.get("parameters") or {}).get("retry_after")) or 30)
                        self.st["next_try"] = time.time() + ra
                    elif code in (400, 403) and "chat" in desc.lower() or code == 401:
                        self.st["next_try"] = time.time() + 300        # yapılandırma hatası — 5 dk sonra tekrar
                    elif code == 400:                                   # biçim hatası → düz metin olarak bir kez dene, olmazsa at
                        with self.lock:
                            if self.q:
                                it0 = self.q[0]; it0["tries"] = it0.get("tries", 0) + 1
                                if it0["tries"] >= 2:
                                    self.q.pop(0)
                                else:
                                    it0["text"] = re.sub(r"<[^>]+>", "", it0["text"])
                                self._save_q()
                    else:
                        self.st["next_try"] = time.time() + back
                        back = min(300, back * 2)
                    break
            except Exception as e:
                logger.debug("tg worker: %s", e)
            try:
                if self.ready():
                    self._save_cfg()
            except Exception:
                pass

    # ------------------------------------------------------------ sinyaller (v120 hub)
    def on_event(self, hub, ev):
        """hub._emit'ten: sahibin (owner) ayarlarına göre BİLDİRİM modundaki olay → Telegram."""
        try:
            if ev.get("backfill") or not self.ready() or not (self.cfg.get("cats") or {}).get("sinyal", True):
                return
            from app.v120 import nmode, DEFAULT_CFG
            c = hub.clients.get(self.cfg.get("owner_cid") or "") if self.cfg.get("owner_cid") else None
            cfg = c["cfg"] if c else DEFAULT_CFG
            if ev.get("cid") and c is not None and ev.get("cid") != c.get("cid"):
                return                                   # başka cihaza özel olay (ör. o cihazın test / fiyat alarmı)
            if not ev.get("cid") and not hub._match(cfg, ev, notify=True):
                return
            if nmode(cfg, ev.get("nt")) != "notify":
                return
            self.enqueue("sinyal", self.fmt_event(ev), key=f"{ev.get('nt')}|{ev.get('sym')}|{ev.get('text')}")
        except Exception as e:
            logger.debug("tg on_event: %s", e)

    def _price(self, sym):
        try:
            q = self.feed.live_quote(sym) if self.feed else None
            p = (q or {}).get("last") if isinstance(q, dict) else None
            if not p:
                from app.live_store import trade_store
                e = trade_store.syms.get(sym)
                p = e.p[-1] if e is not None and len(e.t) else None
            return p
        except Exception:
            return None

    def fmt_event(self, ev):
        sym = ev.get("sym")
        u = self.public_url()
        lines = [f"<b>{_esc(ev.get('title') or '')}</b>"]
        if ev.get("text"):
            lines.append(_esc(ev["text"]))
        meta = []
        if sym:
            meta.append(f"📈 <b>{_esc(sym)}</b>")
            p = self._price(sym)
            if p:
                meta.append(f"₺{str(round(float(p), 4)).replace('.', ',')}")
        meta.append(f"🕒 {_esc(ev.get('time') or _now_s())} (TR)")
        lines.append(" · ".join(meta))
        if u:
            link = f"{u}/?symbol={urllib.parse.quote(sym)}" if sym else u + "/"
            lines.append(f'🔗 <a href="{_esc(link)}">{"Hisseyi aç" if sym else "Uygulamayı aç"}</a>')
        return "\n".join(lines)

    def system(self, title, text="", cat="sistem", key=None):
        u = self.public_url()
        t = f"⚙️ <b>{_esc(title)}</b>" + (f"\n{_esc(text)}" if text else "") + f"\n🕒 {_now_s()} (TR)"
        if cat == "link" and u:
            t += f'\n🔗 <a href="{_esc(u)}/">{_esc(u)}</a>'
        elif u:
            t += f'\n🔗 <a href="{_esc(u)}/">Uygulamayı aç</a>'
        return self.enqueue(cat, t, key=key or (cat + title + text))

    # ------------------------------------------------------------ sistem izleyici
    def _watch(self):
        time.sleep(20)
        last_url = {"public_url.txt": None, "cf_url.txt": None}
        for f in last_url:
            try:
                last_url[f] = (ROOT / "ops" / f).read_text().strip()
            except Exception:
                pass
        feed_ok, feed_bad_since, feed_reported, lf_reported = None, None, False, False
        tun = {"ngrok": None}
        quota_sent = {}
        while True:
            try:
                for f, old in list(last_url.items()):
                    try:
                        cur = (ROOT / "ops" / f).read_text().strip()
                    except Exception:
                        cur = None
                    if cur and cur != old and cur.startswith("http"):
                        if old is not None:
                            self.system(("Yeni ngrok linki" if f == "public_url.txt" else "Yeni Cloudflare linki"), f"Eski: {old}", cat="link", key="link" + cur)
                        last_url[f] = cur
                # tünel: ngrok yerel API (kota harcamaz)
                try:
                    with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=3) as r:
                        up = '"public_url"' in r.read().decode()
                except Exception:
                    try:
                        with urllib.request.urlopen("http://127.0.0.1:4041/api/tunnels", timeout=3) as r:
                            up = '"public_url"' in r.read().decode()
                    except Exception:
                        up = False
                prev = tun["ngrok"]
                if prev is not None and up != prev:
                    tun.setdefault("chg", time.time())
                    if time.time() - tun["chg"] >= 60:                    # 1 dk kalıcı değişim
                        self.system("Tünel geri geldi (ngrok)" if up else "Tünel düştü (ngrok)", "" if up else "Genel link şu an açılmıyor; bekçi yeniden başlatacak.")
                        tun["ngrok"] = up; tun.pop("chg", None)
                else:
                    tun.pop("chg", None)
                    if prev is None:
                        tun["ngrok"] = up
                # İdealData akışı
                if self.feed is not None:
                    try:
                        s = self.feed.status()
                        stt, healthy = s.get("state"), bool(s.get("healthy"))
                    except Exception:
                        stt, healthy = None, None
                    if stt == "login_failed":
                        if not lf_reported:
                            self.system("İdealData girişi reddedildi", "Şifre değişmiş ya da oturum başka yerde açık olabilir. Ayarlar → İdealData Hesabı.", key="lf")
                            lf_reported = True
                    else:
                        lf_reported = False
                    if healthy:
                        if feed_reported:
                            self.system("İdealData bağlandı ✅", "Canlı akış yeniden geliyor.", key="feedup" + str(int(time.time() // 60)))
                        feed_bad_since, feed_reported = None, False
                        if feed_ok is None:
                            feed_ok = True
                    elif stt not in (None, "disabled", "init"):
                        feed_bad_since = feed_bad_since or time.time()
                        if not feed_reported and time.time() - feed_bad_since >= 180:   # 3 dk kesintisiz kopuk
                            self.system("İdealData bağlantısı koptu ❌", f"Durum: {stt} · {str(s.get('error') or '')[:120]}", key="feeddown")
                            feed_reported = True
                # kota (ngrok hesapları)
                try:
                    import app.v135 as L
                    for a in list(L._tok.get("accounts") or []):
                        pct = L._acc_pct(a)
                        for th in (80, 90):
                            k = (a.get("id"), a.get("month"), th)
                            if pct >= th and k not in quota_sent:
                                quota_sent[k] = 1
                                self.system(f"ngrok kotası %{th} aşıldı", f"Hesap {a.get('name') or a.get('id')}: %{round(pct)} kullanıldı. Link Optimizasyon → başka hesaba geç.", key=str(k))
                except Exception:
                    pass
            except Exception as e:
                logger.debug("tg watch: %s", e)
            time.sleep(15)

    # ------------------------------------------------------------ başlat
    def migrate_owner(self, hub):
        """OneSignal'dan taşıma: eskiden OneSignal'a kayıtlı (os_ext) en son cihaz → Telegram'ın tür/filtre ayarlarının sahibi."""
        if self.cfg.get("owner_cid") or hub is None:
            return
        try:
            cl = list(hub.clients.values())
            os_c = sorted([c for c in cl if c.get("os_ext")], key=lambda c: (c.get("os_info") or {}).get("ts") or 0)
            pick = os_c[-1] if os_c else (max(cl, key=lambda c: c.get("seen") or c.get("visible_ts") or 0) if cl else None)
            if pick:
                self.cfg["owner_cid"] = pick.get("cid")
                self.cfg["migrated_from"] = "onesignal" if os_c else "son aktif cihaz"
                self._save_cfg()
                logger.info("Telegram: bildirim türü ayarları %s cihazından taşındı (%s)", str(pick.get("cid"))[:6], self.cfg["migrated_from"])
        except Exception as e:
            logger.debug("tg migrate: %s", e)

    def start(self, hub=None, feed=None, version=""):
        self.hub, self.feed = hub, feed
        self.migrate_owner(hub)
        threading.Thread(target=self._worker, daemon=True, name="tg-send").start()
        threading.Thread(target=self._watch, daemon=True, name="tg-watch").start()
        try:
            why = ""
            wl = (ROOT / "watchdog.log").read_text(encoding="utf-8", errors="ignore").splitlines()[-30:]
            for ln in reversed(wl):
                if "uvicorn başlatıldı" in ln:
                    m = re.search(r"\(([^)]*)\)", ln); why = m.group(1) if m else ""
                    break
            self.system(f"Sunucu başlatıldı (v{version})", f"Neden: {why}" if why else "", key="boot" + str(int(time.time())))
        except Exception:
            pass
        h = _TgLogHandler(self); h.setLevel(logging.ERROR)
        logging.getLogger().addHandler(h)

    # ------------------------------------------------------------ API görünümü
    def public(self):
        t = self.cfg.get("token") or ""
        return {"has_token": bool(t), "token_last4": t[-4:] if t else None, "chat_id": self.cfg.get("chat_id"),
                "owner_cid": self.cfg.get("owner_cid"), "cats": self.cfg.get("cats"), "cat_labels": CATS, "quiet": self.cfg.get("quiet"),
                "dry": self.dry(), "ready": self.ready(),
                "status": {"queue": len(self.q), **{k: v for k, v in self.st.items() if not k.startswith("_")},
                           "next_try_in": max(0, round(self.st["next_try"] - time.time())) if self.st["next_try"] else 0},
                "public_url": self.public_url()}


class _TgLogHandler(logging.Handler):
    """ERROR log kayıtları → 'Hata' sistem bildirimi (aynı imza 30 dk'da bir, dakikada en çok 1)."""
    def __init__(self, tg):
        super().__init__(); self.tg = tg; self.seen = {}; self.last = 0

    def emit(self, record):
        try:
            if record.name.startswith("bist.telegram") or record.name.startswith("websocket"):
                return
            msg = record.getMessage()[:200]
            sig = record.name + re.sub(r"\d+", "#", msg)[:80]
            now = time.time()
            if now - self.seen.get(sig, 0) < 1800 or now - self.last < 60:
                return
            self.seen[sig] = now; self.last = now
            if len(self.seen) > 500:
                self.seen.clear()
            self.tg.system("Sunucu hatası", f"{record.name}: {msg}", key=sig)
        except Exception:
            pass


telegram = Telegram()
