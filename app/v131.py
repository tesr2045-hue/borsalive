"""v1.31.2 — 🚀 TRENE ATLA: hareketin İLK saniyelerinde tek, net alarm (düşük gecikme).

v1.31.0/1 dersleri (RYGYO 48,70 · ONCSM 100,10 · CRFSA 206,90): tetik v1.30.0 olay hattına (POC kırılımı / art arda süpürme)
bağlıydı → 3 ayrı döngü (v124 3 sn + v130 3 sn + v131 2 sn) + kırılım/4. süpürme beklemesi = 7–19 sn gecikme ve hissede gün
zaten +%3–4 iken sinyal. v1.31.2: dedektör DOĞRUDAN İdealData işlem deposunu (saniye saniye) 1 sn'de bir okur; bir saniye kapanır
kapanmaz (sonraki saniyenin ilk işlemi gelince ya da duvar saatiyle) değerlendirilir ve aynı döngüde gönderilir.

KURAL (hepsi, tetik saniyesinde yalnız o ana kadarki işlemlerle — canlı ve geriye dönük test birebir aynı kod):
  1) Kademe süpürmesi ŞİMDİ : aynı saniyede aktif alışla ≥5 farklı fiyat kademesi yukarı süpürüldü, ≥500 bin ₺
  2) Gün henüz yükselmemiş   : gün değişimi ≤ +%2,0 (fazlası GEÇ → bildirim yok)   · tavana ≥ %3
  3) İlk hızlanma            : son 1 dk ≥ +%0,8, 5 dk ≤ +%2,0, son 1 dk eğimi önceki 2 dk'nın ≥1,5 katı, son 30 sn düşmüyor
  4) Agresif alış dalgası    : son 60 sn aktif alış lotu ≥ %75 (120 sn ≥ %60)
  5) Hacim patlaması         : son 60 sn ≥ 500 bin ₺ ve önceki 3 dk ortalamasının ≥5 katı
  6) Gönderim anı            : tetik ≤ 10 sn taze · fiyat sinyalden > +%1 kaçtıysa ya da −%0,5 döndüyse GÖNDERİLMEZ
  7) Seyrek                  : 10:10–17:30 · hisse başına 30 dk'da 1 · saatte en çok 6
OneSignal / Web Push hedeflemesine dokunmaz — v120 hub._emit("olay", "tren_atla", …) yolunu kullanır.
"""
from __future__ import annotations

import bisect
import collections
import json
import logging
import threading
import time

from app import v130
from app.v122 import CONT_FROM, _fp, _fs, _hms, _sec_now, _tick_size

logger = logging.getLogger("bist.v131")

VERSION = "1.31.2"
NT = "tren_atla"
NT_DEFAULT = "notify"
DATA = v130.DATA
VDIR = DATA / "v131"
CFG_FILE = VDIR / "tren.json"
LOG_FILE = VDIR / "tren_log.jsonl"

TH_DEF = {"lev": 5, "swtl": 500_000, "gd_max": 2.0, "tvd": 3.0, "m1": 0.8, "m5_hi": 2.0, "acc": 1.5, "m30": 0.0,
          "bs60": 0.75, "bs": 0.60, "tl60": 500_000, "vacc": 5.0, "t0": 36600, "t1": 63000, "run_max": 1.0, "back_max": 0.5}
CFG_DEF = {"on": True, "cd": 30, "rate": 6, "fresh": 10, "dry": False, "loop": 1.0}
STATS = {
    "method": "Kayıtlı günler işlem işlem yeniden oynatıldı; GİRİŞ = tetikten 3 sn sonraki fiyat (yeni motor gecikmesi); hisse başına 30 dk soğuma.",
    "rows": [
        {"day": "01.10", "n": 7, "hit3": 71.4, "loss2": 14.3, "r60": 3.51},
        {"day": "02.10", "n": 24, "hit3": 50.0, "loss2": 4.2, "r60": 2.34},
        {"day": "05.10 (örneklem dışı, ~11:15'e kadar)", "n": 2, "hit3": 0.0, "loss2": 0.0, "r60": 1.19},
    ],
    "old": {"n": 39, "hit3": 38.5, "loss2": 20.5, "note": "v1.31.1 (olay hattına bağlı, 15 sn gecikmeli giriş)"},
    "pooled": {"n": 33, "hit3": 51.5, "loss2": 6.1},
    "lat": "Gecikme: v1.31.1'de tetik→gönderim 7–19 sn (RYGYO 13, ONCSM 7, CRFSA 19 sn) · v1.31.2 hedef ≤ 3 sn",
    "def": "hit3 = +%3, −%2'den ÖNCE görüldü (60 dk) · loss2 = −%2 önce görüldü · r60 = 60 dk içi en yüksek (medyan, %)",
}


# ================================================================ saf fonksiyonlar (canlı + geriye dönük ortak) ==
def sweep_at(T, P, L, SD, i, j):
    """T[i:j] aynı saniye → (kademe sayısı (farklı fiyat), aktif alış ₺, ilk, son) ya da None (yukarı süpürme değilse)."""
    px = set(); tl = 0.0; f = last = None
    for k in range(i, j):
        if SD[k] == 1:
            px.add(P[k]); tl += P[k] * L[k]
            if f is None:
                f = P[k]
            last = P[k]
    if len(px) >= 2 and last is not None and last > f:
        return len(px), tl, f, last
    return None


def features(T, P, L, SD, t, pc, tv) -> dict | None:
    i = bisect.bisect_right(T, t)
    if i == 0:
        return None
    p0 = P[i - 1]

    def px(tt):
        j = bisect.bisect_right(T, tt) - 1
        return P[j] if j >= 0 else None

    p1, p3, p5, p30 = px(t - 60), px(t - 180), px(t - 300), px(t - 30)
    j60 = bisect.bisect_left(T, t - 59); j120 = bisect.bisect_left(T, t - 119)
    j240 = bisect.bisect_left(T, t - 239); j300 = bisect.bisect_left(T, t - 299)
    b = s = b6 = s6 = 0
    tl60 = tlpre = tl5 = 0.0
    for k in range(j300, i):
        v = P[k] * L[k]; tl5 += v
        if k >= j60:
            tl60 += v
        elif k >= j240:
            tlpre += v
        if k >= j120:
            if SD[k] == 1:
                b += L[k]
            elif SD[k] == 2:
                s += L[k]
            if k >= j60:
                if SD[k] == 1:
                    b6 += L[k]
                elif SD[k] == 2:
                    s6 += L[k]
    return {"p0": p0, "m1": (p0 / p1 - 1) * 100 if p1 else 0.0, "m5": (p0 / p5 - 1) * 100 if p5 else 0.0,
            "m30": (p0 / p30 - 1) * 100 if p30 else 0.0, "mpre": ((p1 / p3 - 1) * 100 / 2) if (p1 and p3) else 0.0,
            "bs": b / (b + s) if (b + s) else 0.5, "bs60": b6 / (b6 + s6) if (b6 + s6) else 0.5,
            "tl60": tl60, "tl5": tl5, "vacc": (tl60 / (tlpre / 3)) if tlpre else 99.0,
            "gd": (p0 / pc - 1) * 100 if pc else None, "tvd": (tv / p0 - 1) * 100 if tv else None}


def gate(f: dict, sw: tuple, t: int, th=None) -> tuple:
    th = th or TH_DEF
    bad = []
    if not (th["t0"] <= t <= th["t1"]):
        bad.append("saat")
    if sw[0] < th["lev"] or sw[1] < th["swtl"]:
        bad.append("süpürme küçük")
    if f["gd"] is None or f["gd"] > th["gd_max"]:
        bad.append("GEÇ: gün zaten " + (f"+%{f['gd']:.1f}".replace(".", ",") if f["gd"] is not None else "?"))
    if f["tvd"] is None or f["tvd"] < th["tvd"]:
        bad.append("tavana yakın")
    if f["m1"] < th["m1"]:
        bad.append("son 1 dk zayıf")
    if f["m5"] > th["m5_hi"]:
        bad.append("GEÇ: 5 dk zaten " + f"+%{f['m5']:.1f}".replace(".", ","))
    if f["m1"] < th["acc"] * f["mpre"]:
        bad.append("yavaşlıyor")
    if f["m30"] < th["m30"]:
        bad.append("dönüyor")
    if f["bs60"] < th["bs60"] or f["bs"] < th["bs"]:
        bad.append("agresif alış yok")
    if f["tl60"] < th["tl60"] or f["vacc"] < th["vacc"]:
        bad.append("hacim patlaması yok")
    return (not bad), bad


def _pc1(v) -> str:
    return f"{v:+.1f}".replace(".", ",").replace("+", "+%").replace("-", "−%")


def stop_price(p0: float) -> float:
    tk = _tick_size(p0) or 0.01
    return round(int((p0 * 0.98) / tk + 1e-9) * tk, 4)


def why_lines(sw, f) -> list:
    l1 = f"{sw[0]} kademe aktif alışla süpürüldü ({_fp(sw[2])}→{_fp(sw[3])}, {_fs(sw[1])} ₺) · gün {_pc1(f['gd'])}"
    l2 = (f"son 1 dk {_pc1(f['m1'])} (önceki {_pc1(f['mpre'])}/dk) · 5 dk {_pc1(f['m5'])} · aktif alış 60 sn %{f['bs60'] * 100:.0f} · "
          f"1 dk hacim {_fs(f['tl60'])} ₺ (×{min(f['vacc'], 99):.0f}) · tavana %" + f"{f['tvd']:.1f}".replace(".", ","))
    return [l1, l2]


def notif_text(sig: dict) -> tuple:
    f = sig["f"]
    title = f"🚀 TRENE ATLA · {sig['s']} · {_fp(sig['p'])}"
    body = (f"ŞİMDİ piyasa emri · hareket BAŞLIYOR: son 1 dk {_pc1(f['m1'])} · gün {_pc1(f['gd'])} · aktif alış %{f['bs60'] * 100:.0f} · "
            f"stop {_fp(sig.get('stop') or stop_price(sig['p']))} · {_hms(sig['t'])}")
    return title, body


def scan_arrays(T, P, L, SD, pc, tv, t_from=0, t_to=10 ** 6, th=None):
    """Bir hissenin işlem dizilerinde kapanmış saniyeleri tara → [(t, sw, f, ok, bad)] (yalnız büyük süpürmeler)."""
    th = th or TH_DEF
    out = []
    n = len(T)
    i = bisect.bisect_left(T, max(t_from, CONT_FROM + 300))
    while i < n:
        t = T[i]
        if t > t_to:
            break
        j = i
        while j < n and T[j] == t:
            j += 1
        sw = sweep_at(T, P, L, SD, i, j)
        if sw and sw[0] >= 3 and sw[1] >= 250_000:
            f = features(T, P, L, SD, t, pc, tv)
            if f:
                ok, bad = gate(f, sw, t, th)
                out.append((t, sw, f, ok, bad))
        i = j
    return out


# ================================================================ motor ==
class TrenEngine:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.olay = self.hub = self.m = None
        self.thread = None
        self.cfg = dict(CFG_DEF)
        self.th = dict(TH_DEF)
        self._load_cfg()
        self.day = None
        self.sig: list = []
        self.near: dict = {}
        self.ptr: dict = {}                 # sym → (merges, sıradaki değerlendirilmemiş saniye)
        self.fired: dict = {}
        self.rate = collections.deque()
        self.sent = collections.deque(maxlen=100)
        self.dry_out: list = []
        self.sender = None
        self.started_sec = None
        self.loops = self.errors = 0
        self.last_err = None
        self.n_base = 0
        self.timing = {}
        self.lat = collections.deque(maxlen=50)   # tetik saniyesi → gönderim (sn)
        self._hist = False
        self.hist_busy = False
        self.sync_hist = False

    def _load_cfg(self) -> None:
        try:
            d = json.loads(CFG_FILE.read_text(encoding="utf-8"))
            self.cfg.update({k: v for k, v in (d.get("cfg") or {}).items() if k in CFG_DEF})
            self.th.update({k: v for k, v in (d.get("th") or {}).items() if k in TH_DEF})
        except Exception:
            pass

    def start(self, olay, hub, m) -> None:
        self.olay, self.hub, self.m = olay, hub, m
        self.started_sec = _sec_now()
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name="v131-tren", daemon=True)
            self.thread.start()

    def _reset(self, day) -> None:
        with self.lock:
            self.day = day
            self.sig, self.near, self.ptr, self.fired = [], {}, {}, {}
            self._hist = False

    def _loop(self) -> None:
        time.sleep(15)
        while True:
            t0 = time.time()
            try:
                self.step()
                self.loops += 1
            except Exception as ex:
                self.errors += 1
                self.last_err = f"{type(ex).__name__}: {ex}"
                logger.exception("v131 loop")
            dt = time.time() - t0
            self.timing["loop"] = round(dt, 3)
            time.sleep(max(0.2, float(self.cfg.get("loop", 1.0)) - dt))

    def _day(self):
        o = self.olay
        if o is None:
            return None, False
        live = o.live_day()
        if live:
            return live, True
        d, _ = o.resolve(None)
        return d, False

    def _lims(self, day, live, sym):
        """(önceki kapanış, tavan) — canlıda v124 durumundan (İdealData tavanı dahil)."""
        try:
            B = self.olay.b.days.get(day) if self.olay is not None and self.olay.b is not None else None
            st = B.st.get(sym) if B is not None else None
            if st is not None and st.pc:
                return st.pc, st.tv
        except Exception:
            pass
        try:
            lim = self.olay.b._limits(day, live)
            pc = (lim.get(sym) or [None])[0]
            if pc:
                return pc, v130.v124._lim(pc)[0]
        except Exception:
            pass
        return None, None

    def _mk(self, s, t, sw, f, st=None) -> dict:
        sig = {"id": f"{s}:{t}", "s": s, "t": t, "time": _hms(t), "k": "erken", "base": "Kademe süpürmesi + ilk hızlanma", "p": f["p0"],
               "f": {x: (round(v, 4) if isinstance(v, float) else v) for x, v in f.items()},
               "sw": [sw[0], round(sw[1]), sw[2], sw[3]], "stop": stop_price(f["p0"]), "why": why_lines(sw, f)}
        sig["title"], sig["body"] = notif_text(sig)
        if st:
            sig["st"] = st
        return sig

    def _add_sig(self, sig) -> bool:
        with self.lock:
            if any(x["s"] == sig["s"] and abs(x["t"] - sig["t"]) <= 120 for x in self.sig):
                return False
            self.sig.append(sig)
            self.sig.sort(key=lambda x: x["t"])
        return True

    def step(self, now_sec=None) -> list:
        day, live = self._day()
        if not day:
            return []
        if day != self.day:
            self._reset(day)
        try:
            _, syms, _, lock, _ = self.m._src(day)
        except Exception:
            return []
        now = now_sec if now_sec is not None else (_sec_now() if live else 10 ** 6)
        if not self._hist:
            self._hist = True
            bound = {}
            with lock:
                for s, e in list(syms.items()):
                    n = min(len(e.t), len(e.p), len(e.l), len(e.sd))
                    last_t = e.t[n - 1] if n else -1
                    close_to = last_t - 1 if (live and n and now < last_t + 2) else last_t
                    bound[s] = close_to
                    self.ptr[s] = (getattr(e, "snap_merges", 0), close_to + 1, n if close_to == last_t else -1)
            if self.sync_hist:
                self._history(day, live, syms, lock, bound)
            else:      # geçmiş arka planda — canlı tarama hemen başlar (gecikme yok)
                threading.Thread(target=self._history, args=(day, live, syms, lock, bound), name="v131-hist", daemon=True).start()
            return []
        new = []
        for s, e in list(syms.items()):
            with lock:
                n = min(len(e.t), len(e.p), len(e.l), len(e.sd))
                mg = getattr(e, "snap_merges", 0)
                pm = self.ptr.get(s)
                if pm is None:
                    self.ptr[s] = (mg, e.t[n - 1] + 1 if n else 0, n)
                    continue
                if pm[2] == n and pm[0] == mg:
                    continue
                sec0 = pm[1]
                i0 = bisect.bisect_left(e.t, sec0, 0, n)
                if i0 >= n:
                    self.ptr[s] = (mg, sec0, n)
                    continue
                last_t = e.t[n - 1]
                # kapanmış saniyeler: son işlemin saniyesinden önceki saniyeler (ya da duvar saatiyle ≥2 sn geçmiş)
                close_to = last_t - 1 if now < last_t + 2 else last_t
                if e.t[i0] > close_to:
                    self.ptr[s] = (pm[0], sec0, pm[2]) if False else (mg, sec0, pm[2])
                    continue
                i1 = bisect.bisect_right(e.t, close_to, i0, n)
                T = list(e.t[i0:i1]); P = list(e.p[i0:i1]); L = list(e.l[i0:i1]); SD = list(e.sd[i0:i1])
            self.ptr[s] = (mg, close_to + 1, n if close_to == last_t else pm[2])
            # büyük süpürme var mı (ucuz ön tarama)
            hit = []
            k = 0
            while k < len(T):
                t = T[k]; j = k
                while j < len(T) and T[j] == t:
                    j += 1
                sw = sweep_at(T, P, L, SD, k, j)
                if sw and sw[0] >= 3 and sw[1] >= 250_000 and t >= CONT_FROM + 300:
                    hit.append((t, sw))
                k = j
            if not hit:
                continue
            pc, tv = self._lims(day, live, s)
            with lock:
                n2 = len(e.t)
                a = bisect.bisect_left(e.t, hit[0][0] - 3600, 0, n2)
                b = bisect.bisect_right(e.t, hit[-1][0], a, n2)
                TT = list(e.t[a:b]); PP = list(e.p[a:b]); LL = list(e.l[a:b]); SS = list(e.sd[a:b])
            for t, sw in hit:
                f = features(TT, PP, LL, SS, t, pc, tv)
                if not f:
                    continue
                self.n_base += 1
                ok, bad = gate(f, sw, t, self.th)
                if not ok:
                    if len(bad) <= 2 and "saat" not in bad:
                        self.near[s] = {"s": s, "t": t, "p": f["p0"], "bad": bad, "time": _hms(t), "gd": round(f["gd"] or 0, 2)}
                    continue
                sig = self._mk(s, t, sw, f)
                if self._add_sig(sig):
                    new.append(sig)
        if new:
            if live:
                self.deliver(day, new, now)
            else:
                for g in new:
                    g["st"] = "geçmiş"
        return new

    def _history(self, day, live, syms, lock, bound) -> None:
        """Bugünün geçmiş sinyallerini aynı dedektörle yeniden kur (yalnız liste, bildirim GÖNDERİLMEZ). Arka plan iş parçacığı."""
        t0 = time.time()
        nh = 0
        self.hist_busy = True
        try:
            for s, close_to in bound.items():
                if self.day != day:
                    return
                e = syms.get(s)
                if e is None or close_to < 0:
                    continue
                with lock:
                    n = min(len(e.t), len(e.p), len(e.l), len(e.sd))
                    if n < 50:
                        continue
                    i1 = bisect.bisect_right(e.t, close_to, 0, n)
                    T = list(e.t[:i1]); P = list(e.p[:i1]); L = list(e.l[:i1]); SD = list(e.sd[:i1])
                if any(T[k] > T[k + 1] for k in range(len(T) - 1)):
                    idx = sorted(range(len(T)), key=T.__getitem__)
                    T, P, L, SD = ([c[k] for k in idx] for c in (T, P, L, SD))
                pc, tv = self._lims(day, live, s)
                for t, sw, f, ok, bad in scan_arrays(T, P, L, SD, pc, tv, 0, close_to, self.th):
                    self.n_base += 1
                    if ok:
                        if self._add_sig(self._mk(s, t, sw, f, "geçmiş")):
                            nh += 1
                    elif len(bad) <= 2 and "saat" not in bad:
                        nr = self.near.get(s)
                        if nr is None or nr["t"] < t:
                            self.near[s] = {"s": s, "t": t, "p": f["p0"], "bad": bad, "time": _hms(t), "gd": round(f["gd"] or 0, 2)}
                if live:
                    time.sleep(0.002)
        finally:
            self.hist_busy = False
            self.timing["history"] = round(time.time() - t0, 1)
            self.timing["history_n"] = nh

    def _last_px(self, sym):
        try:
            _, syms, _, lock, _ = self.m._src(self.day)
            e = syms.get(sym)
            if e is None:
                return None
            with lock:
                return e.p[len(e.p) - 1] if len(e.p) else None
        except Exception:
            return None

    def deliver(self, day, sigs, now) -> list:
        out = []
        wall = time.time()
        for g in sigs:
            ref = g["t"] if self.cfg.get("dry") else wall
            while self.rate and ref - self.rate[0] > 3600:
                self.rate.popleft()
            if not self.cfg.get("on", True):
                g["st"] = "kapalı"; continue
            if self.started_sec is not None and g["t"] < self.started_sec:
                g["st"] = "geçmiş"; continue
            if now - g["t"] > int(self.cfg.get("fresh", 10)):
                g["st"] = "bayat"; continue
            px = self._last_px(g["s"])
            if px:
                mv = (px / g["p"] - 1) * 100
                g["px_send"] = px
                if mv > float(self.th.get("run_max", 1.0)):
                    g["st"] = "kaçtı"; continue
                if mv < -float(self.th.get("back_max", 0.5)):
                    g["st"] = "döndü"; continue
            last = self.fired.get(g["s"])
            if last is not None and g["t"] - last < int(self.cfg.get("cd", 30)) * 60:
                g["st"] = "soğuma"; continue
            if len(self.rate) >= int(self.cfg.get("rate", 6)):
                g["st"] = "oran"; continue
            self.fired[g["s"]] = g["t"]
            self.rate.append(ref)
            data = {"f": "tren_atla", "k": g["k"], "t": g["t"], "price": g["p"], "stop": g["stop"], "day": day, "src": "v131",
                    "m1": round(g["f"]["m1"], 2), "gd": round(g["f"]["gd"], 2), "bs60": round(g["f"]["bs60"], 3), "tvd": round(g["f"]["tvd"], 2)}
            rec = {"nt": NT, "sym": g["s"], "title": g["title"], "text": g["body"], "data": data, "tsec": g["t"]}
            if self.cfg.get("dry"):
                g["st"] = "kuru"
                self.dry_out.append(rec)
            else:
                try:
                    if self.sender is not None:
                        self.sender(rec)
                    elif self.hub is not None:
                        self.hub._emit("olay", NT, g["s"], g["title"], g["body"], data, tsec=g["t"])
                    g["st"] = "gönderildi"
                except Exception as ex:
                    g["st"] = "hata"
                    logger.warning("v131 emit: %s", ex)
            g["lat"] = max(0, _sec_now() - g["t"]) if now_is_live(now) else None
            if g.get("lat") is not None:
                self.lat.append(g["lat"])
            self.sent.append({**rec, "ts": wall, "st": g["st"], "lat": g.get("lat")})
            if self.sender is None:
                try:
                    VDIR.mkdir(parents=True, exist_ok=True)
                    with LOG_FILE.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps({"day": day, **rec, "st": g["st"], "ts": round(wall, 1), "lat": g.get("lat"), "v": VERSION}, ensure_ascii=False) + "\n")
                except Exception:
                    pass
            out.append(rec)
        return out

    # ------------------------------------------------------------ API --
    def listing(self, limit=60) -> dict:
        day, live = self._day()
        ready = bool(self._hist and self.day == day)
        sigs = list(self.sig)[-max(1, min(int(limit or 60), 300)):] if ready else []
        try:
            _, syms, _, lock, _ = self.m._src(day) if day else (None, {}, None, threading.RLock(), None)
        except Exception:
            syms, lock = {}, threading.RLock()
        now = _sec_now() if live else None
        out = []
        for g in reversed(sigs):
            r = dict(g)
            e = syms.get(g["s"]) if syms else None
            if e is not None:
                with lock:
                    nn = min(len(e.t), len(e.p))
                    i = bisect.bisect_right(e.t, g["t"], 0, nn)
                    seg = e.p[i:nn]
                    last = e.p[nn - 1] if nn else None
                    mx = max(seg) if len(seg) else None
                    mn = min(seg) if len(seg) else None
                if last:
                    r["now"] = last; r["chg"] = round((last / g["p"] - 1) * 100, 2)
                if mx:
                    r["max"] = mx; r["max_pc"] = round((mx / g["p"] - 1) * 100, 2)
                if mn:
                    r["min_pc"] = round((mn / g["p"] - 1) * 100, 2)
            if now is not None:
                r["age"] = max(0, now - g["t"])
                r["hot"] = r["age"] <= 300 and r.get("st") == "gönderildi"
            out.append(r)
        near = sorted(self.near.values(), key=lambda x: -x["t"])[:12] if ready else []
        return {"day": day, "day_label": v130._day_label(day) if day else None, "live": live, "ready": ready, "signals": out, "n": len(self.sig) if ready else 0,
                "near": near, "th": self.th, "cfg": self.cfg, "stats": STATS, "nt": NT, "nt_default": NT_DEFAULT, "version": VERSION,
                "base_n": self.n_base, "lat": list(self.lat)[-10:], "hist_busy": self.hist_busy, "note": None if ready else "Hesaplanıyor…"}

    def preview(self) -> dict:
        g = next((x for x in reversed(self.sig) if x.get("st") == "gönderildi"), None) or (self.sig[-1] if self.sig else None)
        ex = g is None
        if ex:
            f = {"p0": 5.43, "m1": 1.1, "m5": 1.3, "gd": 0.9, "bs60": 0.86, "tvd": 9.0}
            g = {"s": "GENIL", "p": 5.43, "t": 37281, "f": f, "stop": stop_price(5.43)}
        title, body = notif_text(g)
        return {"example": ex, "nt": NT, "kind": "olay", "sym": g["s"], "title": title, "body": body,
                "payload": {"title": title, "body": body, "tag": f"olay-{g['s']}", "symbol": g["s"], "kind": "olay", "nt": NT,
                            "url": f"/?symbol={g['s']}"}, "sent": False, "note": "Önizleme — gönderilmedi"}

    def status(self) -> dict:
        return {"version": VERSION, "loops": self.loops, "errors": self.errors, "last_err": self.last_err, "timing": self.timing,
                "day": self.day, "signals": len(self.sig), "base_seen": self.n_base, "sent": list(self.sent)[-20:], "cfg": self.cfg,
                "started": _hms(self.started_sec) if self.started_sec else None, "rate_1h": len(self.rate), "lat": list(self.lat)[-20:]}


def now_is_live(now) -> bool:
    return now is not None and now < 10 ** 5


engine = TrenEngine()

try:
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse

    router = APIRouter()

    @router.get("/api/tren/list")
    def _api_list(limit: int = 60):
        return JSONResponse(engine.listing(limit), headers={"Cache-Control": "no-store"})

    @router.get("/api/tren/preview")
    def _api_preview():
        return engine.preview()

    @router.get("/api/tren/status")
    def _api_status():
        return engine.status()
except Exception:      # pragma: no cover
    router = None
