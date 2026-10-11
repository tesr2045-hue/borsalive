"""v1.20.0 — Piyasa Radarı · Tavan/Taban İzleme · Agresif İşlem · Toplu Para Akışı · Kurum Uyarıları ·
Gün Sonu Raporu · Aktif/Pasif Kurum Paneli (Tahtacı Tespiti) · Web Push.

Veri kaynakları
* İdealData Y26 canlı kotasyon (fiyat, tavan, taban, en iyi alış/satış + lot) ve SRV_DRN derinlik (25 kademe).
* İdealData SRV_DRN 'I' işlem akışı (saat [sn], fiyat, lot, aktif taraf 1=alıcı 2=satıcı, alıcı & satıcı kurum)
  → TradeStore (tüm gün, diskte). Aktif = karşı taraftaki emri vuran (piyasa/agresif emir) taraf,
  pasif = kademede bekleyen emri vurulan taraf.
* Sektör: Borsa İstanbul resmi endeks bileşen dosyası (en dar sektör endeksi: XBANK, XELKT, XGIDA …).
"""
from __future__ import annotations

import collections
import json
import logging
import os
import queue
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

logger = logging.getLogger("bist.v120")
IST = ZoneInfo("Europe/Istanbul")
DATA = Path(__file__).resolve().parent.parent / "data"
ALERT_DIR = DATA / "alerts"
PUSH_DIR = DATA / "push"
REPORT_DIR = DATA / "reports"

SECTOR_LABELS = {
    "XBANK": "Banka", "XSGRT": "Sigorta", "XFINK": "Fin. Kiralama & Faktoring", "XHOLD": "Holding ve Yatırım",
    "XGMYO": "Gayrimenkul YO", "XAKUR": "Aracı Kurumlar", "XYORT": "Menkul Kıymet YO", "XGSYO": "Girişim Sermayesi YO",
    "XELKT": "Elektrik", "XGIDA": "Gıda & İçecek", "XKMYA": "Kimya Petrol Plastik", "XMADN": "Madencilik",
    "XMANA": "Metal Ana", "XMESY": "Metal Eşya Makina", "XKAGT": "Orman Kağıt Basım", "XTAST": "Taş Toprak",
    "XTEKS": "Tekstil Deri", "XILTM": "İletişim", "XINSA": "İnşaat", "XSPOR": "Spor", "XTCRT": "Ticaret",
    "XTTIC": "Toptan Ticaret", "XPTIC": "Perakende Ticaret", "XTRZM": "Turizm", "XKNKL": "Konaklama",
    "XYIHZ": "Yiyecek & İçecek Hizmetleri", "XULAS": "Ulaştırma", "XBLSM": "Bilişim", "XUTEK": "Teknoloji",
    "XUSIN": "Sınai", "XUHIZ": "Hizmetler", "XUMAL": "Mali",
}
BROAD = {"XUSIN", "XUHIZ", "XUMAL", "XUTEK"}
KURUM_TIERS = [1e6, 2.5e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6]
KURUM_WINDOW = 600          # sn — kurum agresif alım/satım penceresi
SWEEP_KEEP_MIN_TL = 50_000  # bu altı süpürmeler kaydedilmez (tek kademe ise)


def _now() -> datetime:
    return datetime.now(IST)


def _hms(sec: int) -> str:
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def _sec_now() -> int:
    n = _now()
    return n.hour * 3600 + n.minute * 60 + n.second


def _fmt_tl(v: float) -> str:
    a = abs(v)
    if a >= 1e9:
        s = f"{a / 1e9:.2f} Mr"
    elif a >= 1e6:
        s = f"{a / 1e6:.2f} Mn"
    elif a >= 1e3:
        s = f"{a / 1e3:.0f} bin"
    else:
        s = f"{a:.0f}"
    return ("-" if v < 0 else "") + s.replace(".", ",") + " ₺"


def _fmt_lot(v: float) -> str:
    return f"{int(round(v)):,}".replace(",", ".")


def _fp(v) -> str:
    return "—" if v is None else f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# =============================================================== FLOWS ====
class FlowAgg:
    """Incremental per-stock & per-broker aktif/pasif aggregation over TradeStore ticks."""
    # broker accum: [aa_lot, aa_tl, pa_lot, pa_tl, as_lot, as_tl, ps_lot, ps_tl, n,
    #                x1_lot, x1_tl, x2_lot, x2_tl, x0_lot, x0_tl]   (v1.21: çapraz = alıcı kurum == satıcı kurum; aktif taraf 1/2/0)
    def __init__(self, store) -> None:
        self.store = store
        self.lock = threading.RLock()
        self.day = None
        self.sym: dict[str, dict] = {}
        self.last_run = 0.0

    def _reset_sym(self) -> dict:
        return {"n": 0, "merges": -1, "lot": 0, "buy_lot": 0, "sell_lot": 0, "auc_lot": 0, "buy_tl": 0.0,
                "sell_tl": 0.0, "auc_tl": 0.0, "trades": 0, "br": {}, "first": None, "last": None}

    def update(self) -> None:
        st = self.store
        with st.lock:
            day = st.day
            items = list(st.syms.items())
            names = list(st.brokers)
        with self.lock:
            if day != self.day:
                self.day = day
                self.sym = {}
            for sym, e in items:
                a = self.sym.get(sym)
                n = len(e.t)
                if a is None or a["merges"] != e.snap_merges or n < a["n"]:
                    a = self._reset_sym()
                    a["merges"] = e.snap_merges
                    self.sym[sym] = a
                if n == a["n"]:
                    continue
                with st.lock:
                    T = e.t[a["n"]:n]; P = e.p[a["n"]:n]; L = e.l[a["n"]:n]
                    SD = e.sd[a["n"]:n]; B = e.b[a["n"]:n]; S = e.s[a["n"]:n]
                br = a["br"]
                for i in range(len(T)):
                    lot = L[i]; px = P[i]; tl = lot * px; sd = SD[i]
                    a["lot"] += lot; a["trades"] += 1
                    if a["first"] is None:
                        a["first"] = T[i]
                    a["last"] = T[i]
                    bb = br.get(B[i])
                    if bb is None:
                        bb = br[B[i]] = [0, 0.0, 0, 0.0, 0, 0.0, 0, 0.0, 0, 0, 0.0, 0, 0.0, 0, 0.0]
                    ss = br.get(S[i])
                    if ss is None:
                        ss = br[S[i]] = [0, 0.0, 0, 0.0, 0, 0.0, 0, 0.0, 0, 0, 0.0, 0, 0.0, 0, 0.0]
                    bb[8] += 1; ss[8] += 1
                    if B[i] == S[i]:   # çapraz işlem (aynı kurum iki tarafta)
                        xo = 9 if sd == 1 else 11 if sd == 2 else 13
                        bb[xo] += lot; bb[xo + 1] += tl
                    if sd == 1:      # alıcı aktif
                        a["buy_lot"] += lot; a["buy_tl"] += tl
                        bb[0] += lot; bb[1] += tl; ss[6] += lot; ss[7] += tl
                    elif sd == 2:    # satıcı aktif
                        a["sell_lot"] += lot; a["sell_tl"] += tl
                        ss[4] += lot; ss[5] += tl; bb[2] += lot; bb[3] += tl
                    else:            # seans/açılış eşleşmesi: pasif-pasif
                        a["auc_lot"] += lot; a["auc_tl"] += tl
                        bb[2] += lot; bb[3] += tl; ss[6] += lot; ss[7] += tl
                a["n"] = n
            self.names = names
            self.last_run = time.time()

    def ensure(self, max_age: float = 8.0) -> None:
        if time.time() - self.last_run > max_age:
            self.update()

    def bname(self, i: int) -> str:
        try:
            return self.names[i]
        except Exception:
            return ""


# ============================================================== ALERTS ====
# v1.20.1: bildirim türleri (istemci static/app.js NT kataloğu ile aynı anahtarlar / varsayılanlar)
# mod: "off" = KAPALI, "view" = SADECE GÖRÜNTÜLE (uygulama içi), "notify" = BİLDİRİM (ses + sistem/Web Push)
NTYPES = {
    "tavan_yaklasan": "notify", "tavan_kitlendi": "notify", "tavan_eriyen": "notify", "tavan_cozuldu": "notify",
    "taban_yaklasan": "notify", "taban_kitlendi": "notify", "taban_donen": "notify",
    "agresif_alim": "notify", "agresif_satis": "notify",
    "kurum_alim": "notify", "kurum_satis": "notify", "gun_sonu": "notify",
    "ani_hacim": "view", "hacim_rvol": "off", "zirve_52h": "view", "dip_52h": "view",
    "devre_kesici": "notify", "devre_kalkti": "view", "tam_tur": "view", "kapanis": "off", "durum": "off",
    "akis_tavan": "off", "akis_taban": "off", "fiyat_alarmi": "notify",
}
_TT_NT = {"yaklasan": "tavan_yaklasan", "tavanda": "tavan_kitlendi", "eriyen": "tavan_eriyen", "cozuldu": "tavan_cozuldu",
          "taban_yaklasan": "taban_yaklasan", "tabanda": "taban_kitlendi", "taban_donen": "taban_donen"}


def ntype_of(kind: str, sub: str | None) -> str:
    if kind == "tavan":
        return _TT_NT.get(sub or "", "tavan_yaklasan")
    if kind == "agresif":
        return "agresif_alim" if sub == "buy" else "agresif_satis"
    if kind == "kurum":
        return "kurum_alim" if sub == "buy" else "kurum_satis"
    if kind == "rapor":
        return "gun_sonu"
    return sub or kind


def _olay_nt(ev: dict) -> str | None:
    k, v = ev.get("kind"), ev.get("variant")
    if k == "hacim":
        return "ani_hacim" if v == "spike" else "hacim_rvol"
    if k == "52h":
        return "zirve_52h" if v == "high" else "dip_52h"
    if k == "devre":
        return "devre_kesici" if v == "on" else "devre_kalkti"
    return {"tur": "tam_tur", "kapanis": "kapanis", "diger": "durum", "tavan": "akis_tavan", "taban": "akis_taban"}.get(k)


_OLAY_TITLE = {"ani_hacim": "📊 {s} ani hacim", "hacim_rvol": "📊 {s} hacim", "zirve_52h": "🏔 {s} 52H zirve", "dip_52h": "🕳 {s} 52H dip",
               "devre_kesici": "⛔ {s} devre kesici", "devre_kalkti": "✅ {s} devre kesici kalktı", "tam_tur": "🔄 {s} gün içi tam tur",
               "kapanis": "🔔 {s} kapanış", "durum": "ℹ️ {s} işlem durumu", "akis_tavan": "🔺 {s} tavan (akış)", "akis_taban": "🔻 {s} taban (akış)"}


def nmode(cfg: dict, nt: str) -> str:
    n = (cfg or {}).get("notif") or {}
    if n.get("master") is False:
        return "off"
    m = (n.get("modes") or {}).get(nt) or NTYPES.get(nt, "view")
    return m if m in ("off", "view", "notify") else "view"


DEFAULT_CFG = {
    "tavan": {"on": True, "scope": "all", "syms": [], "approach_pct": 2.0, "floor_approach_pct": 2.0, "melt_pct": 30.0,
              "kinds": {"yaklasan": True, "tavanda": True, "eriyen": True, "taban_yaklasan": True, "tabanda": True,
                        "taban_donen": True}},
    "agresif": {"on": True, "scope": "all", "syms": [], "side": "both", "min_lot": 0, "min_tl": 2_000_000,
                "min_levels": 3, "min_book_pct": 0, "notify": True},
    "kurum": {"on": True, "brokers": [], "min_tl": 5_000_000, "side": "both", "notify": True},
    "rapor": {"auto": True, "brokers": []},
    "favs": [], "sound": True,
    "notif": {"master": True, "modes": {}, "sound": {}, "ts": 0},
}


def _merge(base: dict, upd: dict) -> dict:
    out = json.loads(json.dumps(base))
    for k, v in (upd or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


class Hub:
    def __init__(self) -> None:
        self.feed = None
        self.store = None
        self.flows: FlowAgg | None = None
        self.ix = None
        self.lock = threading.RLock()
        self.events: collections.deque = collections.deque(maxlen=50000)
        self.sweeps: collections.deque = collections.deque(maxlen=60000)
        self._eid = 0
        self.clients: dict[str, dict] = {}
        self._tstate: dict[str, dict] = {}       # cid -> sym -> state
        self._bursts: dict[str, dict] = {}
        self._bf_bursts: dict[str, dict] = {}
        self._bf_k = ({}, {}, {})
        self.live_from_sec = None
        self._books: dict[str, tuple] = {}       # sym -> (ts, asks[(p,l)], bids[(p,l)], ask_tot, bid_tot)
        self._kwin: dict[tuple, collections.deque] = {}
        self._ksum: dict[tuple, float] = {}
        self._kfired: dict[tuple, tuple] = {}
        self._push_q: queue.Queue = queue.Queue(maxsize=2000)
        self._push_rate: dict[str, collections.deque] = {}
        self.push_stats = {"sent": 0, "failed": 0, "expired": 0, "last_error": None}
        self.vapid_public = None
        self._vapid_file = PUSH_DIR / "vapid_private.pem"
        self.day = None
        self.backfilled = False
        self._sector_cache = (0.0, {})
        self._started = False
        self.olay_source = None
        self._olay_last = None

    # ------------------------------------------------------------ setup --
    def start(self, feed, store, ix) -> None:
        if self._started:
            return
        self._started = True
        self.feed, self.store, self.ix = feed, store, ix
        self.flows = FlowAgg(store)
        self.live_from_sec = _sec_now()
        ALERT_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        self._load_clients()
        self._init_vapid()
        threading.Thread(target=self._loop, name="v120-tick", daemon=True).start()
        threading.Thread(target=self._push_worker, name="v120-push", daemon=True).start()
        threading.Thread(target=self._slow_loop, name="v120-slow", daemon=True).start()

    def _load_clients(self) -> None:
        f = ALERT_DIR / "clients.json"
        try:
            if f.exists():
                self.clients = json.loads(f.read_text())
                for c in self.clients.values():
                    c["cfg"] = _merge(DEFAULT_CFG, c.get("cfg") or {})
        except Exception as e:
            logger.warning("clients.json okunamadı: %s", e)

    def _save_clients(self) -> None:
        f = ALERT_DIR / "clients.json"
        tmp = f.with_suffix(".tmp")
        with self.lock:
            tmp.write_text(json.dumps(self.clients, ensure_ascii=False))
        os.replace(tmp, f)

    def client(self, cid: str) -> dict:
        cid = (cid or "").strip()[:64] or "anon"
        with self.lock:
            c = self.clients.get(cid)
            if c is None:
                c = {"cid": cid, "cfg": json.loads(json.dumps(DEFAULT_CFG)), "push": None, "created": time.time()}
                self.clients[cid] = c
            c["cfg"] = _merge(DEFAULT_CFG, c.get("cfg") or {})
            n = c["cfg"]["notif"]
            if not n.get("migrated"):          # v1.20.0 ekran içi açık/kapalı → v1.20.1 modları
                n["migrated"] = True
                md = n.setdefault("modes", {})
                for k, v in (c["cfg"]["tavan"].get("kinds") or {}).items():
                    if v is False and _TT_NT.get(k):
                        md.setdefault(_TT_NT[k], "off")
                if c["cfg"]["tavan"].get("on") is False:
                    for nt in _TT_NT.values():
                        md.setdefault(nt, "off")
                if c["cfg"]["agresif"].get("notify") is False or c["cfg"]["agresif"].get("on") is False:
                    md.setdefault("agresif_alim", "view"); md.setdefault("agresif_satis", "view")
                if c["cfg"]["kurum"].get("notify") is False:
                    md.setdefault("kurum_alim", "view"); md.setdefault("kurum_satis", "view")
            return c

    def set_config(self, cid: str, cfg: dict) -> dict:
        c = self.client(cid)
        with self.lock:
            c["cfg"] = _merge(c["cfg"], cfg or {})
            for sec in ("tavan", "agresif"):
                c["cfg"][sec]["syms"] = [str(x).upper()[:12] for x in (c["cfg"][sec].get("syms") or [])][:300]
            c["cfg"]["favs"] = [str(x).upper()[:12] for x in (c["cfg"].get("favs") or [])][:300]
            self._tstate.pop(c["cid"], None)   # yeni eşikler → durumu sessizce yeniden kur
        self._save_clients()
        return c["cfg"]

    # ------------------------------------------------------------- push --
    def _init_vapid(self) -> None:
        try:
            from py_vapid import Vapid01
            from cryptography.hazmat.primitives import serialization
            import base64
            PUSH_DIR.mkdir(parents=True, exist_ok=True)
            if not self._vapid_file.exists():
                v = Vapid01()
                v.generate_keys()
                v.save_key(str(self._vapid_file))
                os.chmod(self._vapid_file, 0o600)
            v = Vapid01.from_file(str(self._vapid_file))
            raw = v.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
            self.vapid_public = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        except Exception as e:
            logger.warning("VAPID başlatılamadı: %s", e)
            self.vapid_public = None

    def subscribe(self, cid: str, sub: dict | None) -> dict:
        c = self.client(cid)
        with self.lock:
            c["push"] = sub if (sub and sub.get("endpoint")) else None
        self._save_clients()
        return {"ok": True, "push": bool(c["push"])}

    def _push_worker(self) -> None:
        while True:
            cid, payload = self._push_q.get()
            try:
                from pywebpush import webpush, WebPushException
                c = self.clients.get(cid)
                if not c or not c.get("push"):
                    continue
                try:
                    webpush(subscription_info=c["push"], data=json.dumps(payload, ensure_ascii=False),
                            vapid_private_key=str(self._vapid_file),
                            vapid_claims={"sub": "mailto:bist-analiz@users.noreply.github.com"}, ttl=600, timeout=10)
                    self.push_stats["sent"] += 1
                except WebPushException as e:
                    code = getattr(getattr(e, "response", None), "status_code", None)
                    self.push_stats["failed"] += 1
                    self.push_stats["last_error"] = f"{code} {str(e)[:120]}"
                    if code in (404, 410):
                        self.push_stats["expired"] += 1
                        with self.lock:
                            c["push"] = None
                        self._save_clients()
            except Exception as e:
                self.push_stats["failed"] += 1
                self.push_stats["last_error"] = str(e)[:160]

    def _maybe_push(self, cid: str, ev: dict) -> None:
        c = self.clients.get(cid)
        if not c or not c.get("push") or ev.get("backfill"):   # v1.38.0: yalnız Web Push (OneSignal kaldırıldı)
            return
        if time.time() - (c.get("visible_ts") or 0) < 12:   # sayfa açık ve görünür → uygulama içi bildirim yeterli
            return
        dq = self._push_rate.setdefault(cid, collections.deque())
        now = time.time()
        while dq and now - dq[0] > 60:
            dq.popleft()
        if len(dq) >= 20:
            return
        dq.append(now)
        payload = {"title": ev["title"], "body": ev["text"], "tag": f"{ev['kind']}-{ev.get('sym') or ''}",
                   "symbol": ev.get("sym"), "kind": ev["kind"], "id": ev["id"], "nt": ev.get("nt"),
                   "silent": ((c["cfg"].get("notif") or {}).get("sound") or {}).get(ev.get("nt")) is False or c["cfg"].get("sound") is False,
                   "url": ev.get("url") or (f"/?symbol={ev['sym']}" if ev.get("sym") else "/")}
        if c.get("push"):   # VAPID Web Push (tarayıcı) — v1.38.0: OneSignal kaldırıldı, arka plan bildirimi Telegram'a gider
            try:
                self._push_q.put_nowait((cid, payload))
            except queue.Full:
                pass

    # v1.22.0 OneSignal (APK / WebView) kaydı
    def os_register(self, cid: str, on: bool = True, info: dict | None = None) -> dict:
        c = self.client(cid)
        with self.lock:
            c["os_ext"] = bool(on)
            c["os_info"] = {**(info or {}), "ts": time.time()} if on else None
        self._save_clients()
        return {"ok": True, "os_ext": c["os_ext"], "cid": c["cid"]}

    def test_push(self, cid: str) -> dict:
        c = self.client(cid)
        if not c.get("push"):
            return {"ok": False, "error": "Bu cihaz için push aboneliği yok"}
        self._push_q.put((cid, {"title": "BIST Canlı · test", "body": "Arka plan bildirimi çalışıyor ✓", "tag": "test", "url": "/"}))
        return {"ok": True}

    # ----------------------------------------------------------- events --
    def _emit(self, kind: str, sub: str, sym: str | None, title: str, text: str, data: dict | None = None,
              cid: str | None = None, backfill: bool = False, tsec: int | None = None) -> dict:
        with self.lock:
            self._eid += 1
            ev = {"id": self._eid, "ts": time.time(), "time": _hms(tsec if tsec is not None else _sec_now()),
                  "kind": kind, "sub": sub, "sym": sym, "title": title, "text": text, "data": data or {},
                  "cid": cid, "backfill": backfill, "nt": ntype_of(kind, sub) if kind != "olay" else sub}
            self.events.append(ev)
        if not backfill:
            targets = [cid] if cid else [k for k, c in list(self.clients.items()) if self._match(c["cfg"], ev, notify=True)]
            for t in targets:
                c = self.clients.get(t)
                if c and nmode(c["cfg"], ev["nt"]) == "notify":   # KAPALI / SADECE GÖRÜNTÜLE → push yok
                    self._maybe_push(t, ev)
            try:   # v1.38.0 Telegram (OneSignal'ın yerine) — olay başına bir kez, sahip cihazın tür/filtre ayarlarıyla
                from app.telegram_notify import telegram as _tg
                _tg.on_event(self, ev)
            except Exception as e:   # pragma: no cover
                logger.debug("telegram: %s", e)
        return ev

    @staticmethod
    def _in_scope(cfg_sec: dict, cfg: dict, sym: str | None) -> bool:
        sc = cfg_sec.get("scope") or "all"
        if sc == "all" or not sym:
            return True
        if sc == "fav":
            return sym in (cfg.get("favs") or [])
        return sym in (cfg_sec.get("syms") or [])

    def _match(self, cfg: dict, ev: dict, notify: bool = False) -> bool:
        k = ev["kind"]
        d = ev.get("data") or {}
        if k == "agresif":
            a = cfg["agresif"]
            if a.get("side") in ("buy", "sell") and d.get("side") != a["side"]:
                return False
            if not self._in_scope(a, cfg, ev.get("sym")):
                return False
            return (d.get("lot", 0) >= (a.get("min_lot") or 0) and d.get("tl", 0) >= (a.get("min_tl") or 0)
                    and d.get("levels", 0) >= (a.get("min_levels") or 0)
                    and ((a.get("min_book_pct") or 0) <= 0 or (d.get("book_pct") or 0) >= a["min_book_pct"]))
        if k == "kurum":
            a = cfg["kurum"]
            if a.get("brokers") and d.get("broker") not in a["brokers"]:
                return False
            if notify and not a.get("brokers"):
                return False  # push/toast only for explicitly chosen brokers (feed shows all)
            if a.get("side") in ("buy", "sell") and d.get("side") != a["side"]:
                return False
            return d.get("tl", 0) >= (a.get("min_tl") or 0)
        if k == "rapor":
            return True
        if k == "olay":
            return nmode(cfg, ev.get("nt") or "") != "off"
        return False

    def feed_for(self, cid: str, since: int = 0, limit: int = 200, kinds: list[str] | None = None,
                 visible: bool = False) -> dict:
        c = self.client(cid)
        if visible:
            c["visible_ts"] = time.time()
        c["seen_ts"] = time.time()
        out = []
        with self.lock:
            evs = [e for e in self.events if e["id"] > since]
        for e in evs:
            if kinds and e["kind"] not in kinds:
                continue
            if e.get("cid"):
                if e["cid"] != c["cid"]:
                    continue
            elif not self._match(c["cfg"], e):
                continue
            out.append(e)
        return {"events": out[-limit:], "last_id": self._eid, "push": bool(c.get("push"))}

    # --------------------------------------------------------- trades ---
    def on_trade(self, sym: str, k: tuple) -> None:
        """Called by TradeStore for every live tick (inside feed lock): (sec, price, lot, side, buyer_i, seller_i)."""
        try:
            self._sweep_add(sym, k, live=True)
            self._kurum_add(sym, k, live=True)
        except Exception as e:  # pragma: no cover
            logger.debug("v120 on_trade: %s", e)

    def _book_snapshot(self, sym: str):
        b = self._books.get(sym)
        if b and time.time() - b[0] < 3.0:
            return b
        d = (self.feed.depth.get(sym) if self.feed else None) or {}
        return self._mk_book(d)

    @staticmethod
    def _mk_book(d: dict):
        asks = sorted(((v["price"], v["lot"]) for v in (d.get("asks") or {}).values()), key=lambda x: x[0])
        bids = sorted(((v["price"], v["lot"]) for v in (d.get("bids") or {}).values()), key=lambda x: -x[0])
        return (time.time(), asks, bids, sum(l for _, l in asks), sum(l for _, l in bids))

    def _sweep_add(self, sym: str, k: tuple, live: bool) -> None:
        sec, px, lot, sd = k[0], k[1], k[2], k[3]
        BU = self._bursts if live else self._bf_bursts
        if sd not in (1, 2) or lot <= 0:
            self._sweep_close(sym, live)
            return
        with self.lock:
            b = BU.get(sym)
            if b and (b["side"] != sd or b["sec"] != sec):
                self._sweep_close(sym, live)
                b = None
            if b is None:
                book = self._book_snapshot(sym) if live else None
                b = BU[sym] = {"side": sd, "sec": sec, "lot": 0, "tl": 0.0, "prices": {}, "n": 0,
                                         "first": px, "last": px, "book": book, "t": time.time(),
                                         "brokers": collections.Counter(), "live": live}
            b["lot"] += lot
            b["tl"] += lot * px
            b["prices"][px] = b["prices"].get(px, 0) + lot
            b["n"] += 1
            b["last"] = px
            b["t"] = time.time()
            b["brokers"][k[4] if sd == 1 else k[5]] += lot

    def _sweep_close(self, sym: str, live: bool = True) -> None:
        with self.lock:
            b = (self._bursts if live else self._bf_bursts).pop(sym, None)
        if not b:
            return
        levels = len(b["prices"])
        if not ((levels >= 2 and b["tl"] >= 100_000) or b["tl"] >= 250_000):
            return
        side = "buy" if b["side"] == 1 else "sell"
        book = b.get("book")
        book_pct = cleared = opp_tot = None
        if book:
            lv = book[1] if side == "buy" else book[2]
            opp_tot = book[3] if side == "buy" else book[4]
            if opp_tot:
                book_pct = round(min(100.0, b["lot"] / opp_tot * 100.0), 2)
            if side == "buy":
                cleared = sum(1 for p, _ in lv if p < b["last"])
            else:
                cleared = sum(1 for p, _ in lv if p > b["last"])
        top_br, top_lot = (b["brokers"].most_common(1) or [(0, 0)])[0]
        brn = self.store.brokers[top_br] if (self.store and top_br < len(self.store.brokers)) else ""
        q = (self.feed.quotes.get(sym) or {}) if self.feed else {}
        pc = q.get("prev_close")
        sw = {"sym": sym, "time": _hms(b["sec"]), "sec": b["sec"], "side": side, "lot": int(b["lot"]),
              "tl": round(b["tl"], 2), "levels": levels, "from": b["first"], "to": b["last"], "n": b["n"],
              "book_pct": book_pct, "cleared": cleared, "opp_lot": opp_tot, "broker": brn,
              "broker_share": round(top_lot / b["lot"] * 100, 1) if b["lot"] else None,
              "chg": round((b["last"] / pc - 1) * 100, 2) if pc else None, "live": b["live"]}
        with self.lock:
            self.sweeps.append(sw)
        if (levels >= 2 and b["tl"] >= 250_000) or b["tl"] >= 1_000_000:
            arrow = "▲ Satış tarafı süpürüldü" if side == "buy" else "▼ Alış tarafı süpürüldü"
            txt = (f"{arrow}: {levels} kademe {_fp(b['first'])}→{_fp(b['last'])} · {_fmt_lot(b['lot'])} lot · "
                   f"{_fmt_tl(b['tl'])}" + (f" · defterin %{book_pct:.0f}'i" if book_pct is not None else "")
                   + (f" · {brn}" if brn else ""))
            self._emit("agresif", side, sym, f"⚡ {sym} agresif {'ALIM' if side == 'buy' else 'SATIŞ'}", txt,
                       {k2: sw[k2] for k2 in ("side", "lot", "tl", "levels", "book_pct", "from", "to", "broker")},
                       backfill=not b["live"], tsec=b["sec"])

    def _kurum_add(self, sym: str, k: tuple, live: bool) -> None:
        sec, px, lot, sd = k[0], k[1], k[2], k[3]
        if sd not in (1, 2):
            return
        bi = k[4] if sd == 1 else k[5]
        if not bi:
            return
        key = (bi, sym, sd)
        tl = lot * px
        KW, KS, KF = (self._kwin, self._ksum, self._kfired) if live else self._bf_k
        with self.lock:
            dq = KW.get(key)
            if dq is None:
                dq = KW[key] = collections.deque()
                KS[key] = 0.0
            dq.append((sec, tl, lot))
            KS[key] += tl
            while dq and sec - dq[0][0] > KURUM_WINDOW:
                o = dq.popleft()
                KS[key] -= o[1]
            tot = KS[key]
            tier = None
            for t in KURUM_TIERS:
                if tot >= t:
                    tier = t
            if tier is None:
                return
            last = KF.get(key)
            if last and (last[0] >= tier and sec - last[1] < 1800):
                return
            KF[key] = (tier, sec)
            lots = sum(x[2] for x in dq)
        brn = self.store.brokers[bi] if bi < len(self.store.brokers) else str(bi)
        side = "buy" if sd == 1 else "sell"
        avg = tot / lots if lots else None
        txt = (f"{brn} son {KURUM_WINDOW // 60} dk'da {sym}'de agresif {'ALIM' if side == 'buy' else 'SATIŞ'}: "
               f"{_fmt_tl(tot)} · {_fmt_lot(lots)} lot · ort. {_fp(avg)} ₺")
        self._emit("kurum", side, sym, f"🏛 {brn} · {sym} {'agresif alım' if side == 'buy' else 'agresif satış'}", txt,
                   {"broker": brn, "side": side, "tl": round(tot, 2), "lot": int(lots), "avg": avg, "tier": tier},
                   backfill=not live, tsec=sec)

    def backfill(self) -> None:
        """Replay today's stored ticks through the sweep / kurum detectors (no push, book % unknown)."""
        st = self.store
        lim = self.live_from_sec or 10 ** 9
        with st.lock:
            items = [(s, list(zip(e.t, e.p, e.l, e.sd, e.b, e.s))) for s, e in st.syms.items()]
        n = 0
        for sym, rows in items:
            for k in rows:
                if k[0] >= lim:
                    break
                self._sweep_add(sym, k, live=False)
                self._kurum_add(sym, k, live=False)
                n += 1
            self._sweep_close(sym, live=False)
        with self.lock:
            # chronological order for the feeds
            evs = sorted(self.events, key=lambda e: (e["time"], e["id"]))
            self.events = collections.deque(evs, maxlen=self.events.maxlen)
            sws = sorted(self.sweeps, key=lambda s: s["sec"])
            self.sweeps = collections.deque(sws, maxlen=self.sweeps.maxlen)
            self._bf_bursts.clear()
            self._bf_k = ({}, {}, {})
        self.backfilled = True
        logger.info("v120 backfill: %d işlem, %d süpürme, %d olay", n, len(self.sweeps), len(self.events))

    # ------------------------------------------------------------ loops --
    def _loop(self) -> None:
        while True:
            try:
                self._tick()
            except Exception as e:
                logger.debug("v120 tick: %s", e)
            time.sleep(1.0)

    def _slow_loop(self) -> None:
        time.sleep(20)
        while True:
            try:
                if not self.backfilled and self.store and self.store.day:
                    self.backfill()
                self.flows.update()
                self._auto_report()
            except Exception as e:
                logger.warning("v120 slow: %s", e)
            time.sleep(10)

    def _tick(self) -> None:
        f = self.feed
        if not f:
            return
        now = time.time()
        # close idle bursts
        with self.lock:
            idle = [s for s, b in self._bursts.items() if now - b["t"] > 1.5]
        for s in idle:
            self._sweep_close(s, True)
        self._ingest_olay()
        uni = f.equity_universe()
        with f._lock:
            snap = {}
            for s in uni:
                q = f.quotes.get(s)
                if not q:
                    continue
                d = f.depth.get(s) or {}
                snap[s] = (q.get("last"), q.get("ceiling"), q.get("floor"), q.get("bid"), q.get("ask"),
                           q.get("bid_size"), q.get("ask_size"), q.get("prev_close"), d)
            books = {s: self._mk_book(v[8]) for s, v in snap.items() if v[8]}
        with self.lock:
            self._books = books
        for cid, c in list(self.clients.items()):
            cfg = c["cfg"]["tavan"] if "tavan" in c.get("cfg", {}) else None
            if not cfg or all(nmode(c["cfg"], nt) == "off" for nt in _TT_NT.values()):
                continue
            if now - (c.get("seen_ts") or 0) > 6 * 3600 and not c.get("push"):
                continue   # terk edilmiş istemci
            self._tavan_eval(cid, c["cfg"], snap)

    def _ingest_olay(self) -> None:
        """v1.20.1: Canlı Veri Akışı (event_detector) olaylarını bildirim akışına taşı (ani hacim, 52H, devre kesici...)."""
        ed = self.olay_source
        if ed is None or not ed.day:
            return
        with ed.lock:
            evs = ed.events
            mx = evs[-1]["id"] if evs else 0
            if self._olay_last is None or mx < self._olay_last:   # ilk tur / gün değişimi → sessiz başlangıç
                self._olay_last = mx if self._olay_last is None else 0
                if self._olay_last == mx:
                    return
            new = [e for e in evs[-500:] if e["id"] > self._olay_last]
            self._olay_last = mx
        now = time.time()
        for e in new:
            if e.get("initial") or now - (e.get("ts") or now) > 180:
                continue
            nt = _olay_nt(e)
            if not nt:
                continue
            s = e.get("sym") or ""
            self._emit("olay", nt, e.get("sym"), _OLAY_TITLE.get(nt, "{s}").format(s=s), e.get("text") or "",
                       {"price": e.get("price"), "variant": e.get("variant"), "src_id": e.get("id")})

    @staticmethod
    def _lvl_lot(d: dict, side: str, price: float | None) -> float | None:
        if not price:
            return None
        for v in (d.get("bids" if side == "bid" else "asks") or {}).values():
            if abs(v["price"] - price) < 1e-6:
                return v["lot"]
        return None

    def tavan_state(self, s, v) -> dict:
        last, ceil, floor, bid, ask, bsz, asz, pc, d = v
        out = {"s": s, "p": last, "ceil": ceil, "floor": floor, "bid": bid, "ask": ask,
               "c": round((last / pc - 1) * 100, 2) if last and pc else None}
        if last and ceil:
            out["dc"] = round((ceil - last) / last * 100, 3)
        if last and floor:
            out["df"] = round((last - floor) / last * 100, 3)
        at_c = bool(ceil and last and last >= ceil - 1e-9 and (bid is None or bid >= ceil - 1e-9 or not ask))
        at_f = bool(floor and last and last <= floor + 1e-9 and (ask is None or ask <= floor + 1e-9 or not bid))
        out["at_ceil"], out["at_floor"] = at_c, at_f
        cl = self._lvl_lot(d, "bid", ceil) if ceil else None
        if cl is None and bid and ceil and abs(bid - ceil) < 1e-9:
            cl = bsz
        fl = self._lvl_lot(d, "ask", floor) if floor else None
        if fl is None and ask and floor and abs(ask - floor) < 1e-9:
            fl = asz
        out["ceil_lot"], out["floor_lot"] = cl, fl
        return out

    def _tavan_eval(self, cid: str, cfg: dict, snap: dict) -> None:
        t = cfg["tavan"]
        kinds = t.get("kinds") or {}
        ap = float(t.get("approach_pct") or 2.0)
        fp = float(t.get("floor_approach_pct") or ap)
        melt = float(t.get("melt_pct") or 30.0)
        with self.lock:
            stt = self._tstate.get(cid)
            prime = stt is None
            if prime:
                stt = self._tstate[cid] = {}
        for s, v in snap.items():
            if not self._in_scope(t, cfg, s):
                continue
            x = self.tavan_state(s, v)
            if not x.get("p") or not x.get("ceil"):
                continue
            o = stt.get(s) or {"ap": False, "at": False, "peak": 0, "melted": False, "fap": False, "fat": False}
            ev = []
            dc, dfl = x.get("dc"), x.get("df")
            # --- tavan
            if x["at_ceil"]:
                lot = x.get("ceil_lot") or 0
                if not o["at"]:
                    o["at"], o["peak"], o["melted"] = True, lot, False
                    ev.append(("tavanda", f"🔺 {s} TAVANDA", f"{s} tavanda {_fp(x['ceil'])} ₺ · tavan alış lotu {_fmt_lot(lot)}"))
                else:
                    o["peak"] = max(o["peak"], lot)
                    if (o["peak"] > 0 and lot <= o["peak"] * (1 - melt / 100.0) and not o["melted"]):
                        o["melted"] = True
                        drop = (1 - lot / o["peak"]) * 100 if o["peak"] else 0
                        ev.append(("eriyen", f"🫠 {s} tavan eriyor", f"Tavan alış lotu {_fmt_lot(o['peak'])} → {_fmt_lot(lot)} (-%{drop:.0f}) · {_fp(x['ceil'])} ₺"))
                    elif o["melted"] and lot >= o["peak"] * 0.9:
                        o["melted"] = False
                o["ap"] = True
            else:
                if o["at"]:
                    ev.append(("cozuldu", f"⚠️ {s} tavandan çözüldü", f"Tavan bozuldu: son {_fp(x['p'])} ₺ (tavan {_fp(x['ceil'])}) · tavan lotu tepe {_fmt_lot(o['peak'])}"))
                    o["at"], o["melted"], o["peak"] = False, False, 0
                if dc is not None and dc <= ap and not o["ap"]:
                    o["ap"] = True
                    ev.append(("yaklasan", f"⬆️ {s} tavana yaklaşıyor", f"Tavana %{dc:.2f} · son {_fp(x['p'])} ₺ · tavan {_fp(x['ceil'])} ₺ · %{x.get('c') or 0:+.2f}"))
                elif dc is not None and dc > ap * 1.5 + 0.3:
                    o["ap"] = False
            # --- taban
            if x["at_floor"]:
                if not o["fat"]:
                    o["fat"] = True
                    ev.append(("tabanda", f"🔻 {s} TABANDA", f"{s} tabanda {_fp(x['floor'])} ₺ · taban satış lotu {_fmt_lot(x.get('floor_lot') or 0)}"))
                o["fap"] = True
            else:
                if o["fat"] and x["p"] > (x["floor"] or 0):
                    ev.append(("taban_donen", f"↩️ {s} tabandan döndü", f"Taban satışları bitti: son {_fp(x['p'])} ₺ (taban {_fp(x['floor'])}) · %{x.get('c') or 0:+.2f}"))
                    o["fat"] = False
                if dfl is not None and dfl <= fp and not o["fap"]:
                    o["fap"] = True
                    ev.append(("taban_yaklasan", f"⬇️ {s} tabana yaklaşıyor", f"Tabana %{dfl:.2f} · son {_fp(x['p'])} ₺ · taban {_fp(x['floor'])} ₺ · %{x.get('c') or 0:+.2f}"))
                elif dfl is not None and dfl > fp * 1.5 + 0.3:
                    o["fap"] = False
            stt[s] = o
            if prime:
                continue
            for sub, title, txt in ev:
                if nmode(cfg, _TT_NT.get(sub, "")) != "off":
                    self._emit("tavan", sub, s, title, txt, {k2: x.get(k2) for k2 in ("p", "ceil", "floor", "dc", "df", "ceil_lot", "floor_lot", "c")}, cid=cid)

    # --------------------------------------------------------- sectors --
    def sectors(self) -> dict[str, str]:
        ts, m = self._sector_cache
        if m and time.time() - ts < 3600:
            return m
        bist = getattr(self.ix, "_bist", {}) if self.ix else {}
        cand: dict[str, list] = {}
        for code, ent in bist.items():
            if code not in SECTOR_LABELS:
                continue
            n = len(ent.get("members") or [])
            for s in ent.get("members") or []:
                cand.setdefault(s, []).append((code in BROAD, n, code))
        m = {s: sorted(v)[0][2] for s, v in cand.items()}
        self._sector_cache = (time.time(), m)
        return m

    # ------------------------------------------------------------ radar --
    def radar(self) -> dict:
        f = self.feed
        sec = self.sectors()
        uni = f.equity_universe()
        rows = []
        with f._lock:
            for s in uni:
                q = f.quotes.get(s) or {}
                last, pc = q.get("last"), q.get("prev_close")
                if not last:
                    continue
                ceil, floor = q.get("ceiling"), q.get("floor")
                sc = sec.get(s)
                rows.append({"s": s, "n": f._name(s), "p": last, "c": round((last / pc - 1) * 100, 2) if pc else None,
                             "t": q.get("turnover"), "v": q.get("volume"), "ceil": ceil, "floor": floor,
                             "dc": round((ceil - last) / last * 100, 2) if ceil else None,
                             "df": round((last - floor) / last * 100, 2) if floor else None,
                             "sec": sc, "secn": SECTOR_LABELS.get(sc) if sc else None})
        return {"count": len(rows), "rows": rows, "sector_source": "Borsa İstanbul endeks bileşen dosyası (sektör endeksleri)",
                "updated": _now().strftime("%Y-%m-%d %H:%M:%S")}

    def peers(self, sym: str) -> dict:
        sym = sym.upper()
        sc = self.sectors().get(sym)
        r = self.radar()
        rows = [x for x in r["rows"] if sc and x["sec"] == sc]
        return {"symbol": sym, "sector": sc, "sector_name": SECTOR_LABELS.get(sc) if sc else None,
                "count": len(rows), "rows": rows}

    # ------------------------------------------------------- tavan list --
    def tavan_list(self, approach: float = 2.0) -> dict:
        f = self.feed
        uni = f.equity_universe()
        out = []
        with f._lock:
            for s in uni:
                q = f.quotes.get(s)
                if not q or not q.get("last"):
                    continue
                v = (q.get("last"), q.get("ceiling"), q.get("floor"), q.get("bid"), q.get("ask"), q.get("bid_size"),
                     q.get("ask_size"), q.get("prev_close"), f.depth.get(s) or {})
                x = self.tavan_state(s, v)
                if not x.get("ceil"):
                    continue
                if x["at_ceil"]:
                    x["st"] = "tavan"
                elif x["at_floor"]:
                    x["st"] = "taban"
                elif x.get("dc") is not None and x["dc"] <= approach:
                    x["st"] = "tavan_yakin"
                elif x.get("df") is not None and x["df"] <= approach:
                    x["st"] = "taban_yakin"
                else:
                    continue
                x["n"] = f._name(s)
                x["t"] = q.get("turnover")
                out.append(x)
        return {"rows": out, "approach": approach, "updated": _now().strftime("%H:%M:%S")}

    # --------------------------------------------------------- flows ----
    def para_akisi(self) -> dict:
        self.flows.ensure()
        f = self.feed
        sec = self.sectors()
        rows = []
        with self.flows.lock:
            items = list(self.flows.sym.items())
        uni = set(f.equity_universe())
        for s, a in items:
            if s not in uni:
                continue
            q = f.quotes.get(s) or {}
            inflow, outflow = a["buy_tl"], a["sell_tl"]
            tot = inflow + outflow
            pc, last = q.get("prev_close"), q.get("last")
            sc = sec.get(s)
            rows.append({"s": s, "n": f._name(s), "p": last, "c": round((last / pc - 1) * 100, 2) if (last and pc) else None,
                         "in": round(inflow, 2), "out": round(outflow, 2), "net": round(inflow - outflow, 2),
                         "netp": round((inflow - outflow) / tot * 100, 2) if tot else None,
                         "buy_lot": a["buy_lot"], "sell_lot": a["sell_lot"], "t": q.get("turnover"),
                         "rec_tl": round(tot + a["auc_tl"], 2), "trades": a["trades"], "sec": sc,
                         "secn": SECTOR_LABELS.get(sc) if sc else "Diğer"})
        tot_in = sum(r["in"] for r in rows)
        tot_out = sum(r["out"] for r in rows)
        secs: dict[str, dict] = {}
        for r in rows:
            k = r["sec"] or "-"
            e = secs.setdefault(k, {"sec": k, "secn": r["secn"] or "Diğer", "in": 0.0, "out": 0.0, "n": 0, "up": 0, "down": 0})
            e["in"] += r["in"]; e["out"] += r["out"]; e["n"] += 1
            if (r["c"] or 0) > 0:
                e["up"] += 1
            elif (r["c"] or 0) < 0:
                e["down"] += 1
        for e in secs.values():
            e["net"] = round(e["in"] - e["out"], 2)
            t = e["in"] + e["out"]
            e["netp"] = round(e["net"] / t * 100, 2) if t else None
            e["in"] = round(e["in"], 2); e["out"] = round(e["out"], 2)
        st = self.store.stats() if self.store else {}
        return {"rows": rows, "market": {"in": round(tot_in, 2), "out": round(tot_out, 2), "net": round(tot_in - tot_out, 2),
                                         "netp": round((tot_in - tot_out) / (tot_in + tot_out) * 100, 2) if (tot_in + tot_out) else None,
                                         "pos": sum(1 for r in rows if r["net"] > 0), "neg": sum(1 for r in rows if r["net"] < 0)},
                "sectors": sorted(secs.values(), key=lambda e: -e["net"]),
                "coverage": {"trades": st.get("trades"), "symbols": st.get("symbols"), "live_since": st.get("live_since")},
                "note": "Para girişi = aktif (agresif) alıcının vurduğu işlemlerin TL tutarı; çıkışı = aktif satıcının. "
                        "Kaynak: İdealData tick akışı (alıcı/satıcı yönü işlem bazında), tüm BIST payları.",
                "updated": _now().strftime("%Y-%m-%d %H:%M:%S")}

    @staticmethod
    def _bfold(n: str) -> str:
        t = (n or "").upper().replace("İ", "I").replace("Ş", "S").replace("Ğ", "G").replace("Ü", "U").replace("Ö", "O").replace("Ç", "C")
        return "".join(ch for ch in t if ch.isalnum())

    def _akd_index(self) -> dict:
        """v1.21.2: günlük AKD (AKD sekmesiyle aynı kaynak) → {hisse: {kurum_fold: satır}}; 5 sn önbellek."""
        hit = getattr(self, "_akd_ix", None)
        if hit and time.time() - hit[0] < 5:
            return hit[1]
        ix: dict[str, dict] = {}
        try:
            bp = self.feed.broker_positions() if self.feed else {"rows": []}
            for r in bp.get("rows") or []:
                if r.get("src") == "akd":
                    ix.setdefault(r["s"], {})[self._bfold(r["b"])] = r
        except Exception:
            logger.debug("akd index", exc_info=True)
        self._akd_ix = (time.time(), ix)
        return ix

    def _akd_status(self) -> dict | None:
        try:
            return self.feed.akd_day_status() if self.feed and hasattr(self.feed, "akd_day_status") else None
        except Exception:
            return None

    def _akd_match(self, ix_sym: dict, name: str) -> dict | None:
        if not ix_sym:
            return None
        k = self._bfold(name)
        r = ix_sym.get(k)
        if r is None and len(k) >= 4:
            # 'Aktif Yatirim' (işlem akışı) ↔ 'Aktif Yatirim Menkul' (AKD) gibi kısa/uzun adlar
            c = [v for kk, v in ix_sym.items() if kk.startswith(k) or k.startswith(kk)]
            r = c[0] if len(c) == 1 else None
        return r

    def broker_rows(self, sym_filter: str | None = None, broker: str | None = None, nocross: bool = False) -> list[dict]:
        """Per (broker, stock) aktif/pasif alım/satış + tahtacı skoru.
        v1.21.2: AKD (günlük) varsa alış/satış/net lot, maliyet, hacim payı ve ALIŞ/SATIŞ % (= AKD DAĞILIM %) AKD'den;
        aktif/pasif kırılımı işlem akışından. v1.21.3: AKD yoksa yüzde/lot/maliyet None (src='tick'); kullanıcıya gösterilen
        Tahtacı / Gün Sonu Raporu yalnızca src='akd' satırları listeler (iç sinyaller tüm satırları kullanabilir)."""
        akd_ix = self._akd_index()
        self.flows.ensure()
        fl = self.flows
        f = self.feed
        out = []
        with fl.lock:
            items = [(s, a) for s, a in fl.sym.items() if (not sym_filter or s == sym_filter)]
            names = fl.names
        for s, a in items:
            tot_lot = a["lot"] or 0
            if tot_lot <= 0:
                continue
            q = f.quotes.get(s) or {}
            AX = akd_ix.get(s) or {}
            # tick yedeği için AKD DAĞILIM tanımının paydaları (net alıcıların / net satıcıların net lot toplamı)
            tsb = tss = 0.0
            for v0 in a["br"].values():
                n0 = (v0[0] + v0[2]) - (v0[4] + v0[6])
                if n0 > 0: tsb += n0
                elif n0 < 0: tss -= n0
            tsb = tsb or 1.0; tss = tss or 1.0
            for bi, v in a["br"].items():
                bn = names[bi] if bi < len(names) else ""
                if not bn or (broker and bn != broker):
                    continue
                aa, pa, as_, ps = v[0], v[2], v[4], v[6]
                x1, x2, x0 = v[9], v[11], v[13]
                xl = x1 + x2 + x0
                btl0, stl0 = v[1] + v[3], v[5] + v[7]
                if nocross and xl:
                    # sd1 çapraz: kurum hem aktif alıcı hem pasif satıcı; sd2: aktif satıcı + pasif alıcı; 0: seans
                    aa -= x1; ps -= x1; as_ -= x2; pa -= x2; pa -= x0; ps -= x0
                    xt = v[10] + v[12] + v[14]
                    btl0 -= xt; stl0 -= xt
                buy, sell = aa + pa, as_ + ps
                if buy + sell <= 0:
                    continue
                share = (buy + sell) / (2.0 * tot_lot)
                # v1.21.3: yüzdeler YALNIZCA günlük AKD'den (AKD sekmesiyle aynı); AKD yoksa yüzde gösterilmez (None)
                bsh = ssh = None
                share_disp = None
                A = self._akd_match(AX, bn)
                if A:
                    share = (A.get("tp") or 0) / 100.0
                    share_disp = A.get("tp")
                    bsh = A.get("bp") or 0.0; ssh = A.get("sp") or 0.0
                    two = min(A["bl"], A["sl"]) / max(A["bl"], A["sl"]) if max(A["bl"], A["sl"]) else 0
                else:
                    two = min(buy, sell) / max(buy, sell) if max(buy, sell) else 0
                act = (aa + as_) / (buy + sell)
                S = min(1.0, share / 0.35)
                score = 100.0 * (S ** 0.8) * (0.35 + 0.65 * two)
                if a["trades"] < 30 or v[8] < 10:
                    score *= 0.5
                btl, stl = btl0, stl0
                out.append({"x": xl, "xp": round(xl / max(1, v[0] + v[2]) * 100, 1),"b": bn, "s": s, "aa": aa, "pa": pa, "as": as_, "ps": ps, "buy": buy, "sell": sell,
                            "net": buy - sell, "btl": round(btl, 2), "stl": round(stl, 2), "ntl": round(btl - stl, 2),
                            "bavg": round(btl / buy, 4) if buy else None, "savg": round(stl / sell, 4) if sell else None,
                            "share": share_disp, "share_t": round(share * 100, 2), "bshare": bsh, "sshare": ssh,
                            "two": round(two * 100, 1), "act": round(act * 100, 1), "score": round(score, 1),
                            "n": v[8], "p": q.get("last"), "stock_lot": tot_lot, "stock_tl": round(a["buy_tl"] + a["sell_tl"] + a["auc_tl"], 2),
                            "src": "akd" if A else "tick",
                            "abl": A["bl"] if A else None, "asl": A["sl"] if A else None, "anl": A["nl"] if A else None,
                            "aco": A["co"] if A else None, "anp": A.get("np") if A else None})
        return out

    def tahtaci(self, view: str = "score", broker: str | None = None, sym: str | None = None,
                min_tl: float = 5e6, limit: int = 300, nocross: bool = False) -> dict:
        rows = self.broker_rows(sym_filter=sym.upper() if (view == "stock" and sym) else None,
                                broker=broker if view == "broker" else None, nocross=nocross)
        rows = [r for r in rows if r.get("src") == "akd"]      # v1.21.3: yalnızca günlük AKD'si olan hisse/kurum satırları
        if view == "score":
            rows = [r for r in rows if r["stock_tl"] >= min_tl]
            # her hisse için en yüksek skorlu kurum
            best: dict[str, dict] = {}
            for r in rows:
                if r["s"] not in best or r["score"] > best[r["s"]]["score"]:
                    best[r["s"]] = r
            rows = sorted(best.values(), key=lambda r: -r["score"])[:limit]
        else:
            rows.sort(key=lambda r: -r["score"])
            rows = rows[:limit]
        brokers = sorted({n for n in (self.flows.names or []) if n})
        return {"view": view, "rows": rows, "brokers": brokers, "count": len(rows), "nocross": nocross,
                "akd_status": self._akd_status(),
                "note": "Aktif = karşı emri vuran (agresif) taraf, pasif = kademede bekleyen emri vurulan taraf. "
                        "Tahtacı skoru (0–100, sezgisel) = hissenin işlem hacmindeki payı (×%35'te tavan) ve "
                        "çift yönlülük (alım/satım dengesi). Yüksek skor: kurum tahtanın iki tarafında da baskın.",
                "updated": _now().strftime("%Y-%m-%d %H:%M:%S")}

    # --------------------------------------------------------- reports --
    def report(self, brokers: list[str] | None = None, save: bool = False) -> dict:
        rows = [r for r in self.broker_rows() if r.get("src") == "akd"]     # v1.21.3: yalnızca günlük AKD
        if brokers:
            rows = [r for r in rows if r["b"] in brokers]
        by: dict[str, list] = {}
        for r in rows:
            by.setdefault(r["b"], []).append(r)
        out = []
        for b, rs in by.items():
            rs.sort(key=lambda r: -(r["btl"] + r["stl"]))
            tb = sum(r["btl"] for r in rs); ts = sum(r["stl"] for r in rs)
            out.append({"broker": b, "stocks": len(rs), "buy_tl": round(tb, 2), "sell_tl": round(ts, 2), "net_tl": round(tb - ts, 2),
                        "aa": sum(r["aa"] for r in rs), "pa": sum(r["pa"] for r in rs), "as": sum(r["as"] for r in rs),
                        "ps": sum(r["ps"] for r in rs), "rows": rs})
        out.sort(key=lambda x: -(x["buy_tl"] + x["sell_tl"]))
        st = self.store.stats() if self.store else {}
        rep = {"date": _now().strftime("%Y-%m-%d"), "generated": _now().strftime("%Y-%m-%d %H:%M:%S"),
               "brokers": out, "selected": brokers or [], "coverage": {"trades": st.get("trades"), "symbols": st.get("symbols")},
               "akd_status": self._akd_status(),
               "note": "İdealData işlem akışından (tick) hesaplandı; ortalama maliyet = alış TL / alış lot. "
                       "Aktif alım = kurum alıcı ve emri karşı satışı vurdu; pasif alım = kurumun bekleyen alış emri vuruldu."}
        if save:
            f = REPORT_DIR / f"{_now().strftime('%Y%m%d')}.json"
            f.write_text(json.dumps(rep, ensure_ascii=False))
        return rep

    def _auto_report(self) -> None:
        n = _now()
        if n.weekday() > 4 or (n.hour, n.minute) < (18, 10):
            return
        f = REPORT_DIR / f"{n.strftime('%Y%m%d')}.json"
        if f.exists():
            return
        sel = sorted({b for c in self.clients.values() for b in ((c.get("cfg") or {}).get("rapor", {}).get("brokers") or
                                                                    (c.get("cfg") or {}).get("kurum", {}).get("brokers") or [])})
        rep = self.report(sel or None, save=True)
        top = rep["brokers"][:3]
        txt = "; ".join(f"{b['broker']} net {_fmt_tl(b['net_tl'])}" for b in top) or "rapor hazır"
        self._emit("rapor", "gun_sonu", None, "📋 Gün sonu kurum raporu hazır", txt,
                   {"date": rep["date"], "brokers": len(rep["brokers"])})

    def saved_report(self, day: str) -> dict | None:
        f = REPORT_DIR / f"{day}.json"
        if f.exists():
            return json.loads(f.read_text())
        return None

    def sweeps_query(self, side: str = "both", min_lot: float = 0, min_tl: float = 0, min_levels: int = 1,
                     min_book_pct: float = 0, syms: list[str] | None = None, limit: int = 300, since_sec: int = 0) -> dict:
        with self.lock:
            sw = list(self.sweeps)
        out = []
        for s in reversed(sw):
            if side in ("buy", "sell") and s["side"] != side:
                continue
            if syms and s["sym"] not in syms:
                continue
            if s["lot"] < min_lot or s["tl"] < min_tl or s["levels"] < min_levels:
                continue
            if min_book_pct > 0 and (s["book_pct"] is None or s["book_pct"] < min_book_pct):
                continue
            if s["sec"] < since_sec:
                continue
            out.append(s)
            if len(out) >= limit:
                break
        buy = [s for s in out if s["side"] == "buy"]
        sell = [s for s in out if s["side"] == "sell"]
        return {"rows": out, "count": len(out), "total": len(sw),
                "sum": {"buy_tl": round(sum(s["tl"] for s in buy), 2), "sell_tl": round(sum(s["tl"] for s in sell), 2),
                        "buy_n": len(buy), "sell_n": len(sell)},
                "note": "Süpürme = aynı saniyede, aynı aktif yönde art arda gelen işlemler (tek agresif emir varsayımı). "
                        "Kademe = farklı fiyat sayısı; defter % = süpürülen lot / işlem öncesi 25 kademe karşı taraf toplamı "
                        "(yalnızca canlı yakalananlarda).",
                "updated": _now().strftime("%H:%M:%S")}

    def status(self) -> dict:
        return {"clients": len(self.clients), "push_clients": sum(1 for c in self.clients.values() if c.get("push")),
                "vapid": bool(self.vapid_public), "push": self.push_stats, "events": len(self.events),
                "sweeps": len(self.sweeps), "backfilled": self.backfilled,
                "flows_age": round(time.time() - self.flows.last_run, 1) if self.flows else None}


hub = Hub()
