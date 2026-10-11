"""v1.21.0 — OPERASYON TESPİTİ (30 özellik).

Veri kaynakları (hepsi gerçek):
* İdealData Y26 kotasyon, SRV_DRN derinlik (25 kademe) + işlem akışı (kurum + aktif taraf) → TradeStore / FlowAgg
* İdealData REQ_DGLM_TAR2 AKD (gün / hafta / ay aralıkları) — yavaş arka plan kuyruğu (canlı akışı boğmadan)
* İdealData REQ_TAKAS_FARK2 MKK takas değişimi (1 hafta / 1 ay)
* İş Yatırım HisseTekil günlük barlar (1 yıl; kapanış, yüksek/düşük, TL hacim, AOF, SERMAYE, PD, HAO_PD → fiili dolaşım)
* KAP (kap.org.tr) bildirim sorgu API'si
* Borsa İstanbul sektör endeks üyelikleri (v120.sectors)

Çok günlü özellikler data/op/ altında günlük anlık görüntü biriktirir.
"""
from __future__ import annotations

import collections
import json
import logging
import math
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger("bist.op")
IST = ZoneInfo("Europe/Istanbul")
DATA = Path(__file__).resolve().parent.parent / "data"
OPD = DATA / "op"
for _d in ("bars", "akd_period", "akd_day", "akd_week", "takas", "daily", "kap", "closing", "opening"):
    (OPD / _d).mkdir(parents=True, exist_ok=True)

FOREIGN = ["BANK OF AMERICA", "MERRILL", "HSBC", "DEUTSCHE", "CITI", "JP MORGAN", "JPMORGAN", "MORGAN STANLEY",
           "CREDIT SUISSE", "UBS", "GOLDMAN", "BARCLAYS", "WOOD", "SOCIETE", "BNP", "NOMURA", "JEFFERIES"]
INSTITUTIONAL = ["EMEKLILIK", "YATIRIM FONLARI", "SIGORTA", "PORTFOY"]

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36",
      "Referer": "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/default.aspx"}
HT_URL = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/HisseTekil"
KAP_URL = "https://www.kap.org.tr/tr/api/disclosure/members/byCriteria"


def _now() -> datetime:
    return datetime.now(IST)


def _today() -> str:
    return _now().strftime("%Y%m%d")


def _sec_now() -> int:
    n = _now()
    return n.hour * 3600 + n.minute * 60 + n.second


def _hms(sec: int) -> str:
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def _fold(s: str) -> str:
    return (s or "").upper().replace("İ", "I").replace("Ş", "S").replace("Ğ", "G").replace("Ü", "U").replace("Ö", "O").replace("Ç", "C").replace("ı", "I")


def _clip(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def _r(v, d=2):
    return None if v is None else round(v, d)


def _jload(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _jsave(p: Path, obj) -> None:
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, p)


def _weekdays_back(n: int, start: datetime | None = None) -> list[str]:
    d = (start or _now()).date()
    out = []
    while len(out) < n:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.strftime("%Y%m%d"))
    return out


def _session_progress() -> float:
    """0..1 — sürekli işlem seansında geçen süre oranı (10:00–18:00)."""
    s = _sec_now()
    return _clip((s - 36000) / (8 * 3600), 0.02, 1.0)


def _corr(a: list[float], b: list[float]) -> float | None:
    n = min(len(a), len(b))
    if n < 15:
        return None
    a, b = a[-n:], b[-n:]
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a); vb = sum((x - mb) ** 2 for x in b)
    if va <= 0 or vb <= 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb)


# ============================================================ FEATURE CATALOG ==
# fid: (başlık, açıklama, puan ağırlığı, bildirim türü, durum notu)
FEATURES = {
    29: ("Operasyon Skoru", "Tüm sinyallerin 0–100 birleşimi; her puanın kaynağı şeffaf (dökümü açın).", 0, "op_skor"),
    1: ("Sessiz Toplama Dedektörü", "Fiyat yatay/dar bantta iken bir kurumun günlerdir istikrarlı (çoğu pasif) net alımı.", 12, "op_sessiz"),
    2: ("Tavan Kuyruğu Gücü", "Tavandaki alış lotu ÷ fiili dolaşım ve ÷ ortalama günlük hacim → kilit gücü.", 6, "op_kuyruk"),
    3: ("Satış Duvarı Erimesi", "Büyük satış kademeleri işlemle değil iptalle küçülüyor (derinlik farkı − gerçekleşen işlem).", 6, "op_duvar"),
    4: ("Ardışık Süpürme Serisi", "Aynı kurumun kısa sürede tekrar tekrar satış kademelerini süpürmesi.", 8, "op_seri"),
    5: ("Kademe Çizme Hızı", "Agresif alımla dakikada kaç kademe yukarı itildiği + kaç kurumun ittiği.", 6, "op_cizme"),
    6: ("Tahtacı Maliyet Bandı", "Baskın kurumun ortalama maliyeti, fiyatın uzaklığı ve maliyet altında tepki.", 4, None),
    7: ("Kurum Konsantrasyonu", "İlk 1/3/5 alıcının alış payı ve gün içi artışı.", 8, "op_konsantrasyon"),
    8: ("Takas Birikimi Trendi", "Kurum saklama (MKK takas) payının hafta/ay boyunca artışı.", 8, None),
    9: ("Yabancı / Kurumsal Giriş", "BofA, HSBC, Deutsche, Citi, JPMorgan, Morgan Stanley, UBS/CS, Goldman, Barclays, Merrill… yeni/artan pozisyon.", 6, "op_yabanci"),
    10: ("Tavan Öncesi İmza", "Geçmiş tavan günlerinden önceki hacim/fiyat imzası; bugünkü benzerlik skoru.", 8, None),
    11: ("Düşük Float + Ani Hacim", "Hacim / fiili dolaşım oranında ani sıçrama (İş Yatırım SERMAYE × HAO oranı).", 6, "op_float"),
    12: ("Alış Derinliği Kalınlaşması", "Fiyatın altında büyük ve kalıcı alış emirlerinin birikmesi.", 5, None),
    13: ("Sahte Emir (Spoofing) Takibi", "Büyük emirlerin gerçekleşmeden kısa sürede eklenip silinmesi; ömür istatistiği.", 3, "op_spoof"),
    14: ("Kapanış Seansı Operasyonu", "18:00–18:10 kapanış seansında fiyat itme + kurumlar + ertesi gün sonucu geçmişi.", 4, "op_kapanis"),
    15: ("Açılış Seansı Baskısı", "Açılış seansı eşleşmesi: boşluk, hacim, tavana yakın açılış, açılışta alan kurumlar.", 4, "op_acilis"),
    16: ("VWAP Üstü Israr", "Fiyatın gün içi VWAP üstünde geçirdiği süre ve VWAP altı düşüşlerin geri alınması.", 5, None),
    17: ("Kırılım + Kurum Onayı", "20 günlük direncin agresif kurum alımıyla kırılması.", 8, "op_kirilim"),
    18: ("Satıcı Tükenmesi", "Satış tarafı emir/lot azalıyor, büyük satıcı satışını kesiyor.", 5, "op_tukenme"),
    19: ("Çapraz İşlem Ayıklama", "Aynı kurumun iki tarafta olduğu işlemler; çaprazlar hariç gerçek net alım.", 0, None),
    20: ("Kurum Ortaklığı Haritası", "Aynı hisselerde birlikte hareket eden kurum grupları (benzerlik grafiği).", 3, None),
    21: ("Kurumun Geçmiş Başarısı", "Kurumun haftalık toplamalarından 1/5/20 gün sonraki getiriler.", 6, None),
    22: ("Bilanço / KAP Yakınlığı", "Son/yaklaşan KAP bildirimleri (finansal rapor, bedelsiz, özel durum) + birikim.", 3, "op_kap"),
    23: ("Sektör Rotasyonu", "Sektöre para girişi başlıyor; sektördeki geride kalan hisseler.", 3, "op_rotasyon"),
    24: ("Rakip Gecikmesi", "Sektör lideri koşarken benzer davranan rakiplerin geride kalması.", 3, "op_rakip"),
    25: ("Çok Zaman Dilimli Momentum Uyumu", "1/5/15/60 dk RVOL ve fiyat birlikte hızlanıyor.", 6, "op_mtf"),
    26: ("Dar Bant Sıkışması", "Düşük oynaklık sıkışması ve hacimli kırılım.", 5, "op_sikisma"),
    27: ("Para Akışı Diverjansı", "Fiyat düşerken net para girişi artıyor.", 5, "op_diverjans"),
    28: ("Tavan Tutunma Olasılığı", "Kilit gücü + geçmiş tavanlardan ertesi gün devam olasılığı.", 0, None),
    30: ("Operasyon Zaman Çizelgesi", "Hisse bazında gün gün toplama / itme / dağıtım evreleri ve mevcut evre tahmini.", 0, None),
}
ORDER = [29, 30] + [i for i in range(1, 29)]
NT_DEFAULTS = {"op_skor": "notify", "op_sessiz": "view", "op_kuyruk": "view", "op_duvar": "view", "op_seri": "view",
               "op_cizme": "view", "op_konsantrasyon": "off", "op_yabanci": "view", "op_float": "view", "op_spoof": "off",
               "op_kapanis": "view", "op_acilis": "view", "op_kirilim": "view", "op_tukenme": "off", "op_kap": "view",
               "op_rotasyon": "view", "op_rakip": "off", "op_mtf": "view", "op_sikisma": "view", "op_diverjans": "off"}


# ================================================================ DATA LAYER ==
class Bars:
    """İş Yatırım günlük barları (1 yıl) + fiili dolaşım. Diskte önbellek, günde bir yenileme."""

    def __init__(self) -> None:
        self.d: dict[str, dict] = {}       # sym -> {"bars":[...], "float_lot", "sermaye", "day"}
        self.lock = threading.RLock()
        self.done = 0
        self.failed = 0

    def load_disk(self) -> None:
        for f in (OPD / "bars").glob("*.json"):
            v = _jload(f)
            if v and v.get("bars"):
                with self.lock:
                    self.d[f.stem] = v

    def fetch(self, sym: str) -> bool:
        end = _now().date()
        start = end - timedelta(days=400)
        try:
            r = requests.get(HT_URL, params={"hisse": sym, "startdate": start.strftime("%d-%m-%Y"),
                                             "enddate": end.strftime("%d-%m-%Y")}, headers=UA, timeout=25)
            raw = r.json()
        except Exception as e:
            self.failed += 1
            logger.debug("bars %s: %s", sym, e)
            return False
        rows = raw.get("value") or [] if isinstance(raw, dict) else []
        bars = []
        fl = sermaye = None
        today = _now().strftime("%Y-%m-%d")
        for x in rows:
            try:
                dt = datetime.strptime(x["HGDG_TARIH"], "%d-%m-%Y").strftime("%Y-%m-%d")
                c = float(x["HGDG_KAPANIS"]); h = float(x["HGDG_MAX"]); lo = float(x["HGDG_MIN"])
                tl = float(x.get("HGDG_HACIM") or 0); aof = float(x.get("HGDG_AOF") or c)
            except Exception:
                continue
            if dt == today:
                continue                        # bugünün barı canlı kotasyondan
            vol = tl / aof if aof else 0
            bars.append({"d": dt, "c": c, "h": h, "l": lo, "tl": tl, "v": vol, "a": aof})
            try:
                sm, pd_, hao = float(x.get("SERMAYE") or 0), float(x.get("PD") or 0), float(x.get("HAO_PD") or 0)
                if sm and pd_ and hao:
                    sermaye = sm; fl = sm * hao / pd_
            except Exception:
                pass
        bars.sort(key=lambda b: b["d"])
        for i in range(1, len(bars)):
            bars[i]["pc"] = bars[i - 1]["c"]
        if bars:
            bars[0]["pc"] = bars[0]["c"]
        v = {"bars": bars, "float_lot": fl, "sermaye": sermaye, "day": _today(), "ts": time.time()}
        with self.lock:
            self.d[sym] = v
        _jsave(OPD / "bars" / f"{sym}.json", v)
        self.done += 1
        return True

    def stale(self, sym: str) -> bool:
        v = self.d.get(sym)
        if not v:
            return True
        if v.get("day") != _today():
            # gün içinde: dünün barı varsa yeterli; 18:30 sonrası bugünkü bar için yenile (ertesi gün zaten)
            return True
        return False

    def get(self, sym: str) -> list[dict]:
        v = self.d.get(sym)
        return v["bars"] if v else []

    def float_lot(self, sym: str) -> float | None:
        v = self.d.get(sym)
        return v.get("float_lot") if v else None

    def avg_vol(self, sym: str, n: int = 20) -> float | None:
        b = self.get(sym)[-n:]
        return (sum(x["v"] for x in b) / len(b)) if b else None


class SlowQ:
    """İdealData tarihsel istekleri için hız sınırlı kuyruk (seans içi yavaş, seans dışı daha hızlı)."""

    def __init__(self) -> None:
        self.q: collections.deque = collections.deque()
        self.keys: set = set()
        self.lock = threading.Lock()
        self.done = collections.Counter()
        self.fail = collections.Counter()
        self.last_err = None
        self.feed = None          # v1.21.3: Op.start'ta atanır (günlük AKD önceliği)
        self.paused = False

    def put(self, key: tuple, fn, front: bool = False) -> None:
        with self.lock:
            if key in self.keys:
                return
            self.keys.add(key)
            (self.q.appendleft if front else self.q.append)((key, fn))

    def interval(self) -> float:
        s = _sec_now()
        n = _now()
        if n.weekday() < 5 and 34200 <= s <= 65400:     # 09:30–18:10 seans: canlı akışı koru
            return 1.4
        return 0.6

    def run(self, feed_ok) -> None:
        while True:
            try:
                if not feed_ok():
                    time.sleep(5)
                    continue
                if self.feed is not None and hasattr(self.feed, "akd_day_complete") and not self.feed.akd_day_complete():
                    self.paused = True             # v1.21.3: günlük AKD deposu tamamlanana kadar haftalık/takas işleri bekler
                    time.sleep(3)
                    continue
                self.paused = False
                with self.lock:
                    item = self.q.popleft() if self.q else None
                if not item:
                    time.sleep(2)
                    continue
                key, fn = item
                try:
                    ok = fn()
                    (self.done if ok else self.fail)[key[0]] += 1
                except Exception as e:
                    self.fail[key[0]] += 1
                    self.last_err = f"{key[0]}: {str(e)[:100]}"
                with self.lock:
                    self.keys.discard(key)
                time.sleep(self.interval())
            except Exception:
                time.sleep(3)

    def pending(self) -> dict:
        with self.lock:
            c = collections.Counter(k[0] for k, _ in self.q)
        return dict(c)


def _akd_pack(v: dict | None, n: int = 12) -> dict | None:
    """akd_view çıktısını küçült: ilk n alıcı/satıcı (net lot, maliyet, toplam lot)."""
    if not v:
        return None
    def pk(r):
        return [r.get("broker"), r.get("net_lot") or 0, r.get("cost"), r.get("total_lot") or 0]
    return {"b": [pk(r) for r in (v.get("buyers") or [])[:n]], "s": [pk(r) for r in (v.get("sellers") or [])[:n]],
            "tot": v.get("total_lot_sum") or 0, "from": v.get("from"), "to": v.get("to")}


# ============================================================== LIVE TRACKER ==
class SymLive:
    __slots__ = ("ptr", "merges", "last_px", "mins", "upticks", "cum_v", "cum_tl", "asks", "bids", "pend",
                 "spoofs", "genuine", "walls", "bidwalls", "samp", "ceil_hist", "ceil_peak", "trades_at",
                 "cross", "open_auc", "close_auc", "pre_close_px", "tick", "push_ref")

    def __init__(self) -> None:
        self.ptr = 0
        self.merges = -1
        self.last_px = None
        self.mins: dict[int, list] = {}       # dakika -> [lot, tl, last, high, low, up_steps]
        self.upticks = collections.deque(maxlen=4000)   # (sec, steps, buyer_idx)
        self.cum_v = 0.0; self.cum_tl = 0.0
        self.asks: dict[float, float] = {}; self.bids: dict[float, float] = {}
        self.pend: dict[tuple, dict] = {}      # (side, price) -> büyük emir kaydı (spoof adayı)
        self.spoofs = collections.deque(maxlen=300)
        self.genuine = 0
        self.walls: dict[float, dict] = {}     # satış duvarları
        self.bidwalls: dict[float, dict] = {}  # kalıcı büyük alışlar
        self.samp = collections.deque(maxlen=120)   # dakikalık örnek: (sec, ask_tot, ask_orders, bid2_10, bid_tot)
        self.ceil_hist = collections.deque(maxlen=15000)
        self.ceil_peak = 0.0
        self.trades_at: dict[tuple, float] = {}     # (sd, price) -> lot (son örneklemeden beri)
        self.cross = collections.Counter()          # broker_idx -> çapraz lot
        self.open_auc = None; self.close_auc = None
        self.pre_close_px = None
        self.tick = None
        self.push_ref = None


class Live:
    """Derinlik farkları + işlem akışından canlı türetilmiş istatistikler (2 sn örnekleme)."""

    def __init__(self) -> None:
        self.s: dict[str, SymLive] = {}
        self.day = None
        self.lock = threading.RLock()
        self.last_min_sample = 0
        self.loops = 0

    def _ticks(self, store, sym: str, L: SymLive):
        e = store.syms.get(sym)
        if e is None:
            return
        with store.lock:
            n = len(e.t)
            if e.snap_merges != L.merges or n < L.ptr:
                # geçmiş birleştirildi → bu hisse için yeniden hesapla
                L.ptr = 0; L.merges = e.snap_merges; L.mins = {}; L.upticks.clear(); L.cum_v = L.cum_tl = 0.0
                L.last_px = None; L.cross = collections.Counter(); L.open_auc = None; L.close_auc = None
                L.pre_close_px = None; L.push_ref = None
            if n == L.ptr:
                return
            T = e.t[L.ptr:n]; P = e.p[L.ptr:n]; LL = e.l[L.ptr:n]; SD = e.sd[L.ptr:n]; B = e.b[L.ptr:n]; S = e.s[L.ptr:n]
            L.ptr = n
        for i in range(len(T)):
            sec, px, lot, sd = T[i], P[i], LL[i], SD[i]
            tl = px * lot
            m = sec // 60
            mm = L.mins.get(m)
            if mm is None:
                mm = L.mins[m] = [0, 0.0, px, px, px, 0]
            mm[0] += lot; mm[1] += tl; mm[2] = px
            if px > mm[3]: mm[3] = px
            if px < mm[4]: mm[4] = px
            L.cum_v += lot; L.cum_tl += tl
            if B[i] == S[i]:
                L.cross[B[i]] += lot
            if sd == 0:
                if sec < 36300:          # açılış seansı eşleşmesi (≤10:05)
                    oa = L.open_auc or {"px": px, "lot": 0, "tl": 0.0, "buyers": collections.Counter(), "sec": sec}
                    oa["lot"] += lot; oa["tl"] += tl; oa["buyers"][B[i]] += lot; oa["px"] = px
                    L.open_auc = oa
                elif sec >= 64800:       # kapanış seansı (18:00+)
                    ca = L.close_auc or {"px": px, "lot": 0, "tl": 0.0, "buyers": collections.Counter(),
                                         "sellers": collections.Counter(), "sec": sec, "pre": L.last_px}
                    ca["lot"] += lot; ca["tl"] += tl; ca["buyers"][B[i]] += lot; ca["sellers"][S[i]] += lot; ca["px"] = px
                    L.close_auc = ca
            else:
                if sec < 64800:
                    L.pre_close_px = px
                tk = L.tick or _tick_size(px)
                if L.push_ref is None:
                    L.push_ref = px
                if sd == 1 and px > L.push_ref + tk * 0.5:
                    # yalnızca yeni zemin: alış-satış sıçraması (1 kademe geri-ileri) tekrar sayılmaz
                    steps = max(1, int(round((px - L.push_ref) / tk)))
                    mm[5] += steps
                    L.upticks.append((sec, steps, B[i]))
                    L.push_ref = px
                elif px < L.push_ref - tk * 2.5:
                    L.push_ref = px
                k = (sd, px)
                L.trades_at[k] = L.trades_at.get(k, 0) + lot
            L.last_px = px

    def _depth(self, sym: str, L: SymLive, d: dict, sec: int, last: float | None) -> None:
        asks = {v["price"]: v["lot"] for v in (d.get("asks") or {}).values() if v.get("price")}
        bids = {v["price"]: v["lot"] for v in (d.get("bids") or {}).values() if v.get("price")}
        if not asks and not bids:
            return
        px = last or (min(asks) if asks else max(bids))
        big_tl = 400_000.0
        for side, now, prev, sdk in (("ask", asks, L.asks, 1), ("bid", bids, L.bids, 2)):
            lots = sorted(now.values())
            med = lots[len(lots) // 2] if lots else 0
            big = max(med * 4, big_tl / px if px else 0)
            lo, hi = (min(now), max(now)) if now else (0, 0)
            for p in (set(prev) | set(now)) if prev else ():
                a, b = prev.get(p, 0.0), now.get(p, 0.0)
                if a == b:
                    continue
                tr = L.trades_at.get((sdk, p), 0.0)
                if b < a:
                    if b == 0 and not (lo <= p <= hi):
                        continue          # kitap kaydı → görünür aralık dışına çıktı (iptal değil)
                    dec = a - b
                    fill = min(dec, tr)
                    canc = dec - fill
                    w = (L.walls if side == "ask" else L.bidwalls).get(p)
                    if w:
                        w["fill"] += fill; w["canc"] += canc; w["cur"] = b; w["t"] = sec
                    key = (side, p)
                    pe = L.pend.get(key)
                    if pe:
                        pe["dec"] += dec; pe["fill"] += fill
                        if pe["dec"] >= pe["add"] * 0.7:
                            if pe["fill"] <= pe["dec"] * 0.25 and sec - pe["t0"] <= 120:
                                L.spoofs.append({"side": side, "p": p, "lot": pe["add"], "tl": pe["add"] * p,
                                                 "life": sec - pe["t0"], "fill": pe["fill"], "t": sec})
                            else:
                                L.genuine += 1
                            L.pend.pop(key, None)
                else:
                    add = b - a + tr
                    if add >= big and add * p >= big_tl:
                        L.pend[(side, p)] = {"add": add, "t0": sec, "dec": 0.0, "fill": 0.0}
                    w = (L.walls if side == "ask" else L.bidwalls).get(p)
                    if w:
                        w["cur"] = b; w["peak"] = max(w["peak"], b)
            ws = L.walls if side == "ask" else L.bidwalls
            for p, b in now.items():       # duvar kaydı (≥4× medyan ve ≥1 Mn ₺)
                if b >= big and b * p >= 1_000_000 and p not in ws:
                    ws[p] = {"first": sec, "peak": b, "cur": b, "fill": 0.0, "canc": 0.0, "t": sec}
            # süresi dolan spoof adayları
            for key in [k for k, v in L.pend.items() if k[0] == side and sec - v["t0"] > 150]:
                L.pend.pop(key, None); L.genuine += 1
        L.asks, L.bids = asks, bids
        L.trades_at = {}
        # duvar temizliği (30 dk'dan eski ve tamamen bitmiş)
        for ws in (L.walls, L.bidwalls):
            for p in [p for p, w in ws.items() if sec - w["t"] > 1800 and w["cur"] <= 0]:
                ws.pop(p, None)

    def sample(self, feed, store, hub) -> None:
        sec = _sec_now()
        day = store.day
        if day != self.day:
            with self.lock:
                self.day = day; self.s = {}
        uni = feed.equity_universe()
        with feed._lock:
            snap = {}
            for s in uni:
                q = feed.quotes.get(s)
                if not q:
                    continue
                d = feed.depth.get(s)
                L0 = self.s.get(s)
                fresh = bool(d and time.time() - (d.get("ts") or 0) < 15)
                if d and (fresh or L0 is None or not (L0.asks or L0.bids)):
                    # taze derinlik; seans dışında ise yalnızca ilk anlık görüntü (duvar/alış kaydı için)
                    d = {"asks": {k: dict(v) for k, v in d.get("asks", {}).items()},
                         "bids": {k: dict(v) for k, v in d.get("bids", {}).items()}, "fresh": fresh}
                else:
                    d = None
                snap[s] = (q.get("last"), q.get("ceiling"), q.get("bid"), q.get("bid_size"), d, q.get("tick"))
        minute = sec // 60
        do_min = minute != self.last_min_sample
        for s, (last, ceil, bid, bsz, d, tick) in snap.items():
            L = self.s.get(s)
            if L is None:
                L = self.s[s] = SymLive()
            if tick:
                L.tick = tick
            try:
                self._ticks(store, s, L)
                if d:
                    self._depth(s, L, d, sec, last)
                if do_min and d:
                    at = sum(v["lot"] for v in d["asks"].values())
                    ao = sum(v.get("orders", 0) for v in d["asks"].values())
                    bl = sorted(d["bids"].values(), key=lambda v: -v["price"])
                    b210 = sum(v["lot"] for v in bl[1:10])
                    bt = sum(v["lot"] for v in bl)
                    L.samp.append((sec, at, ao, b210, bt))
                if ceil and last and last >= ceil - 1e-9 and bid and bid >= ceil - 1e-9:
                    cl = None
                    if d:
                        for v in d["bids"].values():
                            if abs(v["price"] - ceil) < 1e-6:
                                cl = v["lot"]
                    cl = cl if cl is not None else (bsz or 0)
                    L.ceil_hist.append((sec, cl)); L.ceil_peak = max(L.ceil_peak, cl)
                elif L.ceil_hist and sec - L.ceil_hist[-1][0] > 60:
                    L.ceil_peak = 0.0; L.ceil_hist.clear()
            except Exception as e:  # pragma: no cover
                logger.debug("live %s: %s", s, e)
        if do_min:
            self.last_min_sample = minute
        self.loops += 1


def _tick_size(p: float) -> float:
    """BIST pay fiyat adımı."""
    if p < 20: return 0.01
    if p < 50: return 0.02
    if p < 100: return 0.05
    if p < 250: return 0.1
    if p < 500: return 0.25
    if p < 1000: return 0.5
    if p < 2500: return 1.0
    return 2.5


def C(k: str, label: str, t: str = "num", w: str | None = None) -> list:
    """Tablo sütunu: anahtar, başlık, tür (sym/txt/num/pct/chg/tl/lot/px/score/broker/time)."""
    return [k, label, t] + ([w] if w else [])


def _is_foreign(b: str) -> bool:
    f = _fold(b)
    return any(x in f for x in FOREIGN)


def _is_inst(b: str) -> bool:
    f = _fold(b)
    return any(x in f for x in INSTITUTIONAL)


# ================================================================== ENGINE ==
class Op:
    def __init__(self) -> None:
        self.feed = self.store = self.hub = self.ix = None
        self.bars = Bars()
        self.q = SlowQ()
        self.live = Live()
        self.lock = threading.RLock()
        self.res: dict[int, dict] = {}
        self.sig: dict[str, dict[int, tuple]] = {}
        self.score: dict[str, dict] = {}
        self.akdp: dict[str, dict] = {}       # sym -> {"day", "w", "m"}
        self.takas: dict[str, dict] = {}      # sym -> {"day", "w", "m", "q", "date"}
        self.akdday: dict[str, dict] = {}     # sym -> {yyyymmdd: pack}
        self.akdweek: dict[str, dict] = {}    # sym -> {"d1-d2": pack}
        self.kap: dict[str, dict] = {}        # disclosureIndex -> row
        self.kap_status = {"ok": None, "last": None, "err": None, "days": 0}
        self.conc: dict[str, collections.deque] = {}
        self.closing_hist: dict[str, dict] = {}   # yyyymmdd -> {sym: {...}}
        self.opening_hist: dict[str, dict] = {}
        self.daily_days: list[str] = []
        self.alerted: dict[tuple, float] = {}
        self.score_alert: dict[str, tuple] = {}
        self.timing: dict[str, float] = {}
        self.errors: dict[str, str] = {}
        self.computed_at = None
        self.started = False
        self.tavan_model = None
        self.sig_model = None
        self.success = None
        self.co = None
        self._last_daily_save = 0.0
        self._last_conc = 0
        self._qgen_day = None

    # ------------------------------------------------------------- setup --
    def start(self, feed, store, hub, ix) -> None:
        if self.started:
            return
        self.started = True
        self.feed, self.store, self.hub, self.ix = feed, store, hub, ix
        self.q.feed = feed
        self._load_disk()
        for fn, nm in ((self._bars_worker, "op-bars"), (lambda: self.q.run(self._feed_ok), "op-slowq"),
                       (self._kap_worker, "op-kap"), (self._live_loop, "op-live"), (self._compute_loop, "op-compute"),
                       (self._sched_loop, "op-sched")):
            threading.Thread(target=fn, name=nm, daemon=True).start()
        logger.info("operasyon motoru başladı (bars=%d akd=%d takas=%d kap=%d gün=%d)", len(self.bars.d), len(self.akdp),
                    len(self.takas), len(self.kap), len(self.daily_days))

    def _feed_ok(self) -> bool:
        f = self.feed
        return bool(f and getattr(f, "logged_in", False) and getattr(f, "state", "") == "live")

    def _load_disk(self) -> None:
        self.bars.load_disk()
        for f in (OPD / "akd_period").glob("*.json"):
            v = _jload(f)
            if v: self.akdp[f.stem] = v
        for f in (OPD / "takas").glob("*.json"):
            v = _jload(f)
            if v: self.takas[f.stem] = v
        for f in (OPD / "akd_day").glob("*.json"):
            v = _jload(f)
            if v: self.akdday[f.stem] = v
        for f in (OPD / "akd_week").glob("*.json"):
            v = _jload(f)
            if v: self.akdweek[f.stem] = v
        v = _jload(OPD / "kap" / "all.json")
        if v: self.kap = v
        for f in sorted((OPD / "closing").glob("*.json")):
            v = _jload(f)
            if v: self.closing_hist[f.stem] = v
        for f in sorted((OPD / "opening").glob("*.json")):
            v = _jload(f)
            if v: self.opening_hist[f.stem] = v
        self.daily_days = sorted(f.stem for f in (OPD / "daily").glob("*.json"))

    def hist_days(self) -> int:
        d = set(self.daily_days)
        d.add(_today())
        return len(d)

    # ------------------------------------------------------------ workers --
    def _universe_by_turnover(self) -> list[str]:
        f = self.feed
        uni = f.equity_universe()
        with f._lock:
            t = {s: (f.quotes.get(s) or {}).get("turnover") or 0 for s in uni}
        return sorted(uni, key=lambda s: -t[s])

    def _bars_worker(self) -> None:
        time.sleep(25)
        while True:
            try:
                uni = self._universe_by_turnover()
                todo = [s for s in uni if self.bars.stale(s)]
                for s in todo:
                    self.bars.fetch(s)
                    time.sleep(0.5)
            except Exception as e:
                self.errors["bars"] = str(e)[:200]
            time.sleep(600)

    def _kap_fetch(self, d1: datetime, d2: datetime) -> int:
        body = {"fromDate": d1.strftime("%Y-%m-%d"), "toDate": d2.strftime("%Y-%m-%d"), "memberType": "IGS",
                "mkkMemberOidList": [], "inactiveMkkMemberOidList": [], "disclosureClass": "", "subjectList": [],
                "isLate": "", "mainSector": "", "sector": "", "subSector": "", "marketOid": "", "index": "",
                "bdkReview": "", "bdkMemberOidList": [], "year": "", "term": "", "ruleType": "", "period": "",
                "fromSrc": False, "srcCategory": "", "disclosureIndexList": []}
        r = requests.post(KAP_URL, json=body, timeout=30,
                          headers={"User-Agent": UA["User-Agent"], "Referer": "https://www.kap.org.tr/tr/bildirim-sorgu",
                                   "Accept": "application/json"})
        r.raise_for_status()
        rows = r.json() or []
        n = 0
        for x in rows:
            subj = (x.get("subject") or "")
            if "Devre Kesici" in subj:
                continue
            codes = x.get("stockCodes") or x.get("relatedStocks") or ""
            if not codes:
                continue
            idx = str(x.get("disclosureIndex") or "")
            if not idx:
                continue
            try:
                dt = datetime.strptime(x.get("publishDate") or "", "%d.%m.%Y %H:%M:%S")
                ds = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                ds = x.get("publishDate")
            self.kap[idx] = {"i": idx, "d": ds, "codes": [c.strip() for c in str(codes).replace(";", ",").split(",") if c.strip()],
                             "t": (x.get("kapTitle") or "")[:80], "sub": subj[:120], "sum": (x.get("summary") or "")[:200],
                             "cls": x.get("disclosureClass")}
            n += 1
        return n

    def _kap_worker(self) -> None:
        time.sleep(40)
        first = True
        while True:
            try:
                now = _now()
                if first and len(self.kap) < 500:
                    d = now - timedelta(days=45)
                    while d < now:
                        d2 = min(now, d + timedelta(days=2))
                        self._kap_fetch(d, d2)
                        d = d2 + timedelta(days=1)
                        time.sleep(3)
                else:
                    self._kap_fetch(now - timedelta(days=1), now)
                first = False
                cut = (now - timedelta(days=75)).strftime("%Y-%m-%d")
                self.kap = {k: v for k, v in self.kap.items() if (v.get("d") or "") >= cut}
                _jsave(OPD / "kap" / "all.json", self.kap)
                days = {(v.get("d") or "")[:10] for v in self.kap.values()}
                self.kap_status = {"ok": True, "last": now.strftime("%H:%M:%S"), "err": None, "days": len(days),
                                   "rows": len(self.kap)}
            except Exception as e:
                self.kap_status.update({"ok": False, "err": str(e)[:160], "last": _now().strftime("%H:%M:%S")})
            time.sleep(900)

    # ---- yavaş İdealData işleri
    def _job_akdp(self, s: str) -> bool:
        y = _weekdays_back(1)[0]
        w1 = _weekdays_back(5)[-1]
        m1 = _weekdays_back(21)[-1]
        w = _akd_pack(self.feed.akd_view(s, w1, y))
        time.sleep(0.4)
        m = _akd_pack(self.feed.akd_view(s, m1, y), 15)
        if not (w or m):
            return False
        v = {"day": _today(), "w": w, "m": m}
        self.akdp[s] = v
        _jsave(OPD / "akd_period" / f"{s}.json", v)
        return True

    def _job_takas(self, s: str) -> bool:
        d2 = _today()
        out = {"day": _today()}
        for k, n in (("w", 5), ("m", 21), ("q", 63)):
            d1 = _weekdays_back(n)[-1]
            r = self.feed.takas_change(s, d1, d2)
            if not r or not r.get("rows"):
                r = self.feed.takas_change(s, d1, _weekdays_back(1)[0])
            if r and r.get("rows"):
                rows = sorted(r["rows"], key=lambda x: -(x.get("lot") or 0))[:20]
                out[k] = [[x["broker"], x.get("lot"), x.get("pct"), x.get("prev_lot"), x.get("prev_pct"), x.get("change_lot")]
                          for x in rows]
                out[k + "_d"] = [d1, r.get("to")]
            time.sleep(0.4)
        if len(out) == 1:
            return False
        self.takas[s] = out
        _jsave(OPD / "takas" / f"{s}.json", out)
        return True

    def _job_akdday(self, s: str, day: str) -> bool:
        v = _akd_pack(self.feed.akd_view(s, day, day), 10)
        ent = self.akdday.setdefault(s, {})
        ent[day] = v or {"b": [], "s": [], "tot": 0}
        _jsave(OPD / "akd_day" / f"{s}.json", ent)
        return bool(v)

    def _job_akdweek(self, s: str, d1: str, d2: str) -> bool:
        v = _akd_pack(self.feed.akd_view(s, d1, d2), 6)
        ent = self.akdweek.setdefault(s, {})
        ent[f"{d1}-{d2}"] = v or {"b": [], "s": [], "tot": 0}
        _jsave(OPD / "akd_week" / f"{s}.json", ent)
        return bool(v)

    def _sched_loop(self) -> None:
        time.sleep(60)
        while True:
            try:
                self._schedule()
            except Exception as e:
                self.errors["sched"] = str(e)[:200]
            time.sleep(120)

    def _schedule(self) -> None:
        if not self._feed_ok():
            return
        uni = self._universe_by_turnover()
        today = _today()
        sess = _now().weekday() < 5 and 34200 <= _sec_now() <= 65400
        for s in uni:
            if (self.akdp.get(s) or {}).get("day") != today:
                self.q.put(("akdp", s), lambda s=s: self._job_akdp(s))
        for s in uni[:300]:
            if (self.takas.get(s) or {}).get("day") != today:
                self.q.put(("takas", s), lambda s=s: self._job_takas(s))
        pend = sum(self.q.pending().values())
        if sess and pend > 50:
            return            # ağır geçmiş işleri seans dışına / kuyruk boşalınca bırak
        days = _weekdays_back(10)
        for s in uni[:200]:
            have = self.akdday.get(s) or {}
            for d in days:
                if d not in have:
                    self.q.put(("akdday", s, d), lambda s=s, d=d: self._job_akdday(s, d))
        # haftalık pencereler (kurum başarısı): son 9 hafta (bugünden geriye 5'er iş günü), en eski 20g sonrası ölçülebilir
        wd = _weekdays_back(45)
        wins = [(wd[i + 4], wd[i]) for i in range(0, 45, 5)]
        for s in uni[:200]:
            have = self.akdweek.get(s) or {}
            for d1, d2 in wins:
                if f"{d1}-{d2}" not in have:
                    self.q.put(("akdweek", s, d1, d2), lambda s=s, a=d1, b=d2: self._job_akdweek(s, a, b))

    # ---- canlı örnekleme
    def _live_loop(self) -> None:
        time.sleep(15)
        while True:
            t0 = time.time()
            try:
                if self.feed and self.store and self.store.day:
                    self.live.sample(self.feed, self.store, self.hub)
                    self.timing["live"] = round(time.time() - t0, 3)
                    if time.time() - self._last_conc > 600:
                        self._conc_snapshot()
                        self._last_conc = time.time()
            except Exception as e:
                self.errors["live"] = str(e)[:200]
                logger.debug("op live: %s", e)
            time.sleep(max(0.5, 2.0 - (time.time() - t0)))

    def _conc_snapshot(self) -> None:
        fl = self.hub.flows
        fl.ensure()
        sec = _sec_now()
        with fl.lock:
            items = list(fl.sym.items())
        for s, a in items:
            tot = a["lot"] or 0
            if tot <= 0 or a["trades"] < 20:
                continue
            buys = sorted((v[0] + v[2] for v in a["br"].values()), reverse=True)
            t1, t3, t5 = sum(buys[:1]) / tot, sum(buys[:3]) / tot, sum(buys[:5]) / tot
            self.conc.setdefault(s, collections.deque(maxlen=60)).append((sec, t1, t3, t5))

    def _compute_loop(self) -> None:
        time.sleep(45)
        while True:
            t0 = time.time()
            try:
                if self.feed and self.store and self.store.day and self.hub and self.hub.flows:
                    self.compute()
                    self.timing["compute"] = round(time.time() - t0, 2)
                    if time.time() - self._last_daily_save > 900 or (_sec_now() > 65700 and not self._saved_final()):
                        self.save_daily()
            except Exception as e:
                logger.warning("op compute: %s", e)
                self.errors["compute"] = str(e)[:200]
            time.sleep(max(20.0, 60.0 - (time.time() - t0)))

    def _saved_final(self) -> bool:
        return getattr(self, "_final_day", None) == _today()

    # ============================================================ COMPUTE ==
    def _ctx(self) -> dict:
        f, hub = self.feed, self.hub
        uni = f.equity_universe()
        Q = {}
        with f._lock:
            for s in uni:
                q = f.quotes.get(s)
                if not q or not q.get("last"):
                    continue
                Q[s] = {k: q.get(k) for k in ("last", "prev_close", "high", "low", "open", "ceiling", "floor", "vwap",
                                              "turnover", "volume", "bid", "ask", "bid_size", "ask_size")}
                # seans dışında İdealData ertesi günün taban/tavanını yayınlar → bugünün limitlerine geri çevir
                qq = Q[s]; pc = qq.get("prev_close"); ss = _sec_now()
                if pc and (ss >= 65400 or ss < 34800) and qq.get("ceiling") and qq["ceiling"] > pc * 1.105:
                    qq["ceiling_next"], qq["floor_next"] = qq["ceiling"], qq.get("floor")
                    lp = qq["last"]
                    qq["ceiling"] = lp if lp / pc >= 1.094 and lp >= (qq.get("high") or lp) - 1e-9 else round(pc * 1.1, 2)
                    qq["floor"] = lp if lp / pc <= 0.906 and lp <= (qq.get("low") or lp) + 1e-9 else round(pc * 0.9, 2)
            akd_raw = {s: ((e.get("TUM") or {}).get("rows") or [], (e.get("TOPLAM") or {}).get("rows") or [])
                       for s, e in f.akd.items() if s in Q}
        AKD = {}
        for s, (tum, top) in akd_raw.items():
            if tum or top:
                AKD[s] = f._akd_compose(tum, top, Q[s]["last"])
        BR = collections.defaultdict(list)
        for r in hub.broker_rows():
            BR[r["s"]].append(r)
        for v in BR.values():
            v.sort(key=lambda r: -r["net"])
        pa = hub.para_akisi()
        names = {}
        for s in Q:
            try:
                names[s] = f._name(s)
            except Exception:
                names[s] = None
        return {"Q": Q, "AKD": AKD, "BR": BR, "PARA": {r["s"]: r for r in pa["rows"]}, "PSEC": pa.get("sectors") or [],
                "SEC": hub.sectors(), "prog": _session_progress(), "sec": _sec_now(), "msec": min(_sec_now(), 64800), "N": names}

    def _base(self, s: str, X: dict) -> dict:
        q = X["Q"].get(s) or {}
        last, pc = q.get("last"), q.get("prev_close")
        return {"s": s, "n": X["N"].get(s), "p": last, "c": _r((last / pc - 1) * 100) if (last and pc) else None}

    def _proj_vol(self, s: str, X: dict) -> float:
        v = (X["Q"].get(s) or {}).get("volume") or 0
        return v / X["prog"]

    def _rvol(self, s: str, X: dict) -> float | None:
        av = self.bars.avg_vol(s, 20)
        return (self._proj_vol(s, X) / av) if av else None

    def _sigset(self, s: str, fid: int, st: float, txt: str) -> None:
        st = _clip(st)
        if st <= 0.05:
            return
        self._sig_new.setdefault(s, {})[fid] = (round(st, 3), txt)

    def _out(self, fid: int, cols: list, rows: list, note: str = "", hist: str | None = None, sort: str | None = None,
             desc: bool = True, extra: dict | None = None, status: str = "tam") -> None:
        t, d, w, nt = FEATURES[fid]
        if sort:
            if desc:
                rows.sort(key=lambda r: (r.get(sort) is not None, r.get(sort) if r.get(sort) is not None else 0), reverse=True)
            else:
                rows.sort(key=lambda r: (r.get(sort) is None, r.get(sort) if r.get(sort) is not None else 0))
        self._res_new[fid] = {"fid": fid, "title": t, "desc": d, "note": note, "hist": hist, "cols": cols, "rows": rows[:400],
                              "count": len(rows), "updated": _now().strftime("%H:%M:%S"), "weight": w, "nt": nt,
                              "status": status, **(extra or {})}

    def compute(self) -> None:
        X = self._ctx()
        self._sig_new: dict[str, dict] = {}
        self._res_new: dict[int, dict] = {}
        self._models()
        for fid in [i for i in range(1, 29) if i not in (29,)] + [30]:
            fn = getattr(self, f"_f{fid}", None)
            if not fn:
                continue
            t0 = time.time()
            try:
                fn(X)
            except Exception as e:
                logger.warning("op f%d: %s", fid, e, exc_info=True)
                self.errors[f"f{fid}"] = str(e)[:200]
                t, d, w, nt = FEATURES[fid]
                self._res_new[fid] = {"fid": fid, "title": t, "desc": d, "note": f"Hesaplama hatası: {e}", "cols": [], "rows": [],
                                      "count": 0, "updated": _now().strftime("%H:%M:%S"), "weight": w, "nt": nt, "status": "hata"}
            self.timing[f"f{fid}"] = round(time.time() - t0, 3)
        self._f29(X)
        for nm, fn in (("kademe", self._mk_kademe), ("teknik", self._mk_teknik)):
            t0 = time.time()
            try:
                fn(X)
            except Exception as e:
                logger.warning("op %s: %s", nm, e, exc_info=True)
                self.errors[nm] = str(e)[:200]
            self.timing[nm] = round(time.time() - t0, 3)
        by = collections.defaultdict(dict)
        for fid, r in self._res_new.items():
            for row in r["rows"]:
                s = row.get("s")
                if s and fid not in by[s]:
                    by[s][fid] = row
        first = self.computed_at is None
        with self.lock:
            self.res = self._res_new
            self.sig = self._sig_new
            self.by_sym = by
            self.computed_at = _now().strftime("%H:%M:%S")
        self._alerts(first)

    # ------------------------------------------------------------ models --
    def _models(self) -> None:
        """Günlük barlardan (tüm hisseler, ~1 yıl) tavan imzası + tavan tutunma taban oranları. Günde bir/bar sayısı değişince."""
        key = (_today(), len(self.bars.d) // 25)
        if self.tavan_model and self.tavan_model.get("key") == key:
            return
        feats_t, feats_all = [], []
        cont = collections.defaultdict(lambda: [0, 0, 0, 0.0])   # (streak, vb) -> [n, up, tavan, sumret]
        for s, v in list(self.bars.d.items()):
            b = v.get("bars") or []
            if len(b) < 70:
                continue
            for i in range(61, len(b)):
                x = b[i]
                r = x["c"] / x["pc"] - 1 if x.get("pc") else 0
                is_t = r >= 0.095 and x["c"] >= x["h"] * 0.997
                fx = self._sigfeat(b, i - 1)
                if fx:
                    (feats_t if is_t else feats_all).append(fx)
                if is_t and i + 1 < len(b):
                    st = 1
                    j = i - 1
                    while j > 0 and b[j].get("pc") and b[j]["c"] / b[j]["pc"] - 1 >= 0.095 and b[j]["c"] >= b[j]["h"] * 0.997:
                        st += 1; j -= 1
                    av = sum(y["v"] for y in b[i - 20:i]) / 20 or 1
                    vb = 0 if x["v"] / av < 1 else 1 if x["v"] / av < 3 else 2
                    nx = b[i + 1]
                    rn = nx["c"] / x["c"] - 1
                    e = cont[(min(st, 3), vb)]
                    e[0] += 1; e[1] += rn > 0; e[2] += (rn >= 0.095 and nx["c"] >= nx["h"] * 0.997); e[3] += rn
                    e2 = cont[(0, 0)]
                    e2[0] += 1; e2[1] += rn > 0; e2[2] += (rn >= 0.095 and nx["c"] >= nx["h"] * 0.997); e2[3] += rn

        def stats(F):
            if len(F) < 10:
                return None
            k = len(F[0])
            mu = [sum(f[j] for f in F) / len(F) for j in range(k)]
            sd = [max(1e-6, math.sqrt(sum((f[j] - mu[j]) ** 2 for f in F) / len(F))) for j in range(k)]
            return mu, sd
        st_t, st_a = stats(feats_t), stats(feats_all)
        llr_a = []
        if st_t and st_a:
            import random
            rnd = random.Random(7)
            samp = rnd.sample(feats_all, min(4000, len(feats_all)))
            llr_a = sorted(self._llr(f, st_t, st_a) for f in samp)
        self.tavan_model = {"key": key, "t": st_t, "a": st_a, "n_t": len(feats_t), "n_a": len(feats_all), "llr": llr_a,
                            "cont": {f"{k[0]}_{k[1]}": v for k, v in cont.items()}, "stocks": len(self.bars.d)}

    @staticmethod
    def _sigfeat(b: list, i: int, today: dict | None = None) -> list | None:
        """Tavan öncesi imza özellikleri (i günü kapanışı itibarıyla). today verilirse i+1 = canlı gün."""
        if i < 60:
            return None
        bb = b[max(0, i - 62): i + 1] + ([today] if today else [])
        x = bb[-1]
        prev = bb[-21:-1]
        av = sum(y["v"] for y in prev) / 20 or 1
        rets = [bb[k]["c"] / bb[k - 1]["c"] - 1 for k in range(len(bb) - 60, len(bb)) if bb[k - 1]["c"]]
        r10 = rets[-10:]
        sd10 = math.sqrt(sum(r * r for r in r10) / len(r10)) if r10 else 0
        sd60 = math.sqrt(sum(r * r for r in rets) / len(rets)) if rets else 0
        hi = max(y["h"] for y in bb[-20:]); lo = min(y["l"] for y in bb[-20:])
        c5 = bb[-6]["c"] if len(bb) > 6 else x["c"]
        return [math.log(max(x["v"], 1) / av), x["c"] / c5 - 1 if c5 else 0, (sd10 / sd60) if sd60 else 1,
                (x["c"] - lo) / (hi - lo) if hi > lo else 0.5, x["c"] / bb[-2]["c"] - 1 if bb[-2]["c"] else 0]

    @staticmethod
    def _llr(f, st_t, st_a) -> float:
        s = 0.0
        for j in range(len(f)):
            zt = (f[j] - st_t[0][j]) / st_t[1][j]; za = (f[j] - st_a[0][j]) / st_a[1][j]
            t = -0.5 * zt * zt - math.log(st_t[1][j]) + 0.5 * za * za + math.log(st_a[1][j])
            # yönlü: normalden tavan ortalamasının TERS yönüne sapma (ör. hacimsiz / düşen gün) puan kazandırmaz
            if (f[j] - st_a[0][j]) * (st_t[0][j] - st_a[0][j]) < 0:
                t = min(t, 0.0)
            s += t
        return s

    def _today_bar(self, s: str, X: dict) -> dict | None:
        q = X["Q"].get(s) or {}
        if not q.get("last") or not q.get("high"):
            return None
        return {"c": q["last"], "h": q["high"], "l": q["low"] or q["last"], "v": self._proj_vol(s, X),
                "pc": q.get("prev_close"), "tl": (q.get("turnover") or 0) / X["prog"]}

    # =========================================================== FEATURES ==
    def _akd_hist_note(self) -> str:
        n_p = sum(1 for v in self.akdp.values() if v.get("day") == _today())
        n_d = sum(len(v) for v in self.akdday.values())
        return f"AKD hafta/ay: {n_p} hisse güncel · günlük AKD geçmişi: {n_d} hisse-gün (yavaş kuyruk dolduruyor)"

    def _f1(self, X):
        rows = []
        for s, q in X["Q"].items():
            b = self.bars.get(s)
            if len(b) < 20:
                continue
            b20 = b[-20:]
            hi = max(x["h"] for x in b20); lo = min(x["l"] for x in b20)
            avgc = sum(x["c"] for x in b20) / 20
            band = (hi - lo) / avgc * 100
            ret20 = (q["last"] / b20[0]["pc"] - 1) * 100 if b20[0].get("pc") else 0
            ap = self.akdp.get(s) or {}
            m = ap.get("m") or ap.get("w")
            src = "ay" if ap.get("m") else "hafta" if ap.get("w") else None
            if not m or not m.get("b"):
                continue
            tb = m["b"][0]
            vol = (m.get("tot") or 0) / 2
            if vol <= 0 or tb[1] <= 0:
                continue
            ns = tb[1] / vol
            days = self.akdday.get(s) or {}
            pos = sum(1 for d, pk in days.items() if any(x[0] == tb[0] and x[1] > 0 for x in (pk.get("b") or [])))
            N = len(days)
            steady = pos / N if N else None
            pas = None
            for r in X["BR"].get(s, []):
                if r["b"] == tb[0]:
                    pas = r["pa"] / r["buy"] * 100 if r["buy"] else None
                    tnet = r["net"]
                    break
            flat = _clip(1 - (band - 8) / 12) * _clip(1 - (abs(ret20) - 4) / 8)
            st = _clip(ns / 0.15) * flat * ((0.5 + 0.5 * steady) if steady is not None and N >= 3 else 0.75)
            if pas is not None and pas >= 60:
                st = min(1.0, st * 1.1)
            if st < 0.15:
                continue
            row = self._base(s, X)
            row.update({"band": _r(band, 1), "r20": _r(ret20, 1), "b": tb[0], "net": tb[1], "ns": _r(ns * 100, 1),
                        "cost": tb[2], "st": f"{pos}/{N}" if N else "—", "pas": _r(pas, 0), "src": src,
                        "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 1, st, f"{tb[0]} {src}lık net %{ns*100:.0f} pay, bant %{band:.0f}")
        self._out(1, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("band", "20g bant %", "num"),
                      C("r20", "20g getiri %", "chg"), C("b", "Toplayan kurum", "broker"), C("net", "Net lot", "lot"),
                      C("ns", "Hacim payı %", "num"), C("cost", "Maliyet", "px"), C("st", "İstikrar (gün)", "txt"),
                      C("pas", "Bugün pasif %", "num"), C("src", "AKD", "txt"), C("sc", "Skor", "score")],
                  rows, note="Sezgisel. Yatay fiyat (20 gün bant/getiri) + aylık AKD'de tek kurumun yüksek net payı. İstikrar = günlük AKD'de "
                       "net alıcı olduğu gün sayısı / mevcut gün. Pasif % = bugünkü alımının kademede bekleyerek yapılan kısmı. " + self._akd_hist_note(),
                  sort="sc", status="tam" if sum(len(v) for v in self.akdday.values()) > 500 else "kısmi")

    def _f2(self, X):
        rows = []
        f = self.feed
        for s, q in X["Q"].items():
            if not q.get("ceiling") or q["last"] < q["ceiling"] - 1e-9:
                continue
            L = self.live.s.get(s) or SymLive()
            if L.ceil_hist:
                cur = L.ceil_hist[-1][1]; peak = L.ceil_peak or cur
            else:
                # canlı örnek yok (seans dışı / yeni başladı): derinlikteki tavan kademesi, yoksa en iyi alış lotu
                cur = None
                with f._lock:
                    d = f.depth.get(s) or {}
                    for v in (d.get("bids") or {}).values():
                        if v.get("price") and abs(v["price"] - q["ceiling"]) < 1e-6:
                            cur = v.get("lot")
                if cur is None and q.get("bid") and q["bid"] >= q["ceiling"] - 1e-9:
                    cur = q.get("bid_size")
                if not cur:
                    continue
                peak = cur
            fl = self.bars.float_lot(s); av = self.bars.avg_vol(s, 20)
            lf = cur / fl * 100 if fl else None
            la = cur / av if av else None
            melt = (1 - cur / peak) * 100 if peak else 0
            dur = (L.ceil_hist[-1][0] - L.ceil_hist[0][0]) / 60 if L.ceil_hist else None
            lock = 0.6 * _clip((la or 0) / 0.6) + 0.4 * _clip((lf or 0) / 1.0)
            lock *= (1 - _clip(melt / 100) * 0.7)
            row = self._base(s, X)
            row.update({"ceil": q["ceiling"], "lot": cur, "peak": peak, "tl": cur * q["ceiling"], "lf": _r(lf, 2),
                        "la": _r(la, 2), "melt": _r(melt, 1), "dur": round(dur) if dur is not None else None, "sc": round(lock * 100),
                        "fl": fl, "v": q.get("volume"), "src": "canlı" if L.ceil_hist else "derinlik anlık"})
            rows.append(row)
            self._sigset(s, 2, lock, f"tavan kuyruğu {cur:,.0f} lot (ort. hacmin {la or 0:.2f}×), erime %{melt:.0f}")
        self._out(2, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("lot", "Tavan alış lot", "lot"),
                      C("tl", "Kuyruk ₺", "tl"), C("lf", "Lot/Float %", "num"), C("la", "Lot/20g hacim ×", "num"),
                      C("peak", "Zirve lot", "lot"), C("melt", "Erime %", "num"), C("dur", "Süre dk", "num"), C("src", "Kaynak", "txt"),
                      C("sc", "Kilit gücü", "score")], rows,
                  note="Tavandaki alış kademesi lotu (SRV_DRN derinlik). Float = İş Yatırım SERMAYE × HAO oranı. Kilit gücü sezgisel: "
                       "%60 (lot / 20g ort. hacim, 0,6×'te tavan) + %40 (lot / float, %1'de tavan), erime ile azaltılır. Süre, motor "
                       "başladığından beri ölçülür.", sort="sc")

    def _f3(self, X):
        rows = []
        sec = X["sec"]
        for s, L in list(self.live.s.items()):
            q = X["Q"].get(s)
            if not q:
                continue
            for p, w in list(L.walls.items()):
                if p <= q["last"] or w["peak"] * p < 1_000_000:
                    continue
                dec = w["fill"] + w["canc"]
                melt = (1 - w["cur"] / w["peak"]) if w["peak"] else 0
                cs = w["canc"] / dec if dec > 0 else 0
                st = _clip((melt - 0.3) / 0.5) * cs * _clip(w["peak"] * p / 5e6 + 0.3) if melt >= 0.3 and dec > 0 else 0
                row = self._base(s, X)
                row.update({"lp": p, "dist": _r((p / q["last"] - 1) * 100, 2), "peak": w["peak"], "cur": w["cur"],
                            "ptl": w["peak"] * p, "melt": _r(melt * 100, 0), "canc": _r(cs * 100, 0), "fill": w["fill"],
                            "age": round((sec - w["first"]) / 60), "durum": "ERİYOR" if st > 0 else "izleniyor", "sc": round(st * 100)})
                rows.append(row)
                if st <= 0:
                    continue
                self._sigset(s, 3, max(st, (self._sig_new.get(s, {}).get(3) or (0,))[0]),
                             f"{p:g} satış duvarı %{melt*100:.0f} eridi (%{cs*100:.0f} iptal)")
        self._out(3, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("lp", "Duvar fiyatı", "px"),
                      C("dist", "Uzaklık %", "num"), C("peak", "Zirve lot", "lot"), C("cur", "Şimdi lot", "lot"),
                      C("ptl", "Duvar ₺", "tl"), C("melt", "Erime %", "num"), C("canc", "İptal payı %", "num"),
                      C("fill", "Gerçekleşen lot", "lot"), C("age", "Yaş dk", "num"), C("durum", "Durum", "txt"), C("sc", "Skor", "score")], rows,
                  note="Derinlik (25 kademe) 2 sn'de bir karşılaştırılır; bir kademedeki azalma o fiyatta gerçekleşen işlemden fazlaysa fark "
                       "'iptal' sayılır. Duvar = ≥4× medyan kademe ve ≥1 Mn ₺. Yalnızca motor çalıştığından beri (canlı) ölçülür; "
                       "geçmiş derinlik kaydı yoktur. 'izleniyor' = duvar kayıtta, henüz erimedi. Seans dışında defter değişmediği için erime ölçülmez.", sort="sc", status="kısmi")

    def _f4(self, X):
        sw = [x for x in list(self.hub.sweeps) if x.get("side") == "buy" and x.get("broker")]
        grp = collections.defaultdict(list)
        for x in sw:
            grp[(x["sym"], x["broker"])].append(x)
        rows = []
        now = X["sec"]
        for (s, b), L in grp.items():
            if len(L) < 2 or s not in X["Q"]:
                continue
            L.sort(key=lambda x: x["sec"])
            best = 0; j = 0; bi = (0, 0)
            for i in range(len(L)):
                while L[i]["sec"] - L[j]["sec"] > 900:
                    j += 1
                if i - j + 1 > best:
                    best = i - j + 1; bi = (j, i)
            if best < 3:
                continue
            ser = L[bi[0]:bi[1] + 1]
            rec = now - L[-1]["sec"]
            st = _clip((best - 2) / 5) * (1.0 if rec < 1800 else 0.6 if rec < 7200 else 0.35)
            row = self._base(s, X)
            row.update({"b": b, "ser": best, "nsw": len(L), "tl": sum(x["tl"] for x in L), "stl": sum(x["tl"] for x in ser),
                        "lv": sum(x["levels"] for x in ser), "t0": ser[0]["time"], "t1": L[-1]["time"],
                        "act": "AKTİF" if rec < 900 else "", "sc": round(st * 100)})
            rows.append(row)
            if st > (self._sig_new.get(s, {}).get(4) or (0,))[0]:
                self._sigset(s, 4, st, f"{b} 15 dk'da {best} süpürme")
        self._out(4, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("b", "Kurum", "broker"),
                      C("ser", "Seri (15 dk)", "num"), C("stl", "Seri ₺", "tl"), C("lv", "Seri kademe", "num"),
                      C("nsw", "Gün süpürme", "num"), C("tl", "Gün ₺", "tl"), C("t0", "Seri başı", "time"),
                      C("t1", "Son", "time"), C("act", "Durum", "txt"), C("sc", "Skor", "score")], rows,
                  note="Süpürme = aynı saniyede aynı yönde ≥2 kademe ve ≥100 B₺ (veya ≥250 B₺) agresif alım (Agresif ekranı). Seri = aynı "
                       "kurumun 15 dakikalık penceredeki süpürme sayısı (≥3). Bugünkü işlem kaydından.", sort="sc")

    def _f5(self, X):
        rows = []
        sec = X.get("msec", X["sec"])       # seans sonrası: 18:00 itibarıyla son pencere
        for s, L in list(self.live.s.items()):
            if s not in X["Q"] or not L.upticks:
                continue
            u5 = [x for x in L.upticks if sec - x[0] <= 300]
            u15 = [x for x in L.upticks if sec - x[0] <= 900]
            if sum(x[1] for x in u15) < 3:
                continue
            s5 = sum(x[1] for x in u5); s15 = sum(x[1] for x in u15)
            cnt = collections.Counter()
            for x in u15:
                cnt[x[2]] += x[1]
            nb = len(cnt)
            top, tl = (cnt.most_common(1) or [(0, 0)])[0]
            tn = self.store.brokers[top] if top < len(self.store.brokers) else ""
            day = sum(x[1] for x in L.upticks)
            st = _clip((s15 / 15) / 3.0) * (0.6 + 0.4 * _clip(tl / s15 / 0.6) if s15 else 0)
            if (X["Q"][s].get("turnover") or 0) < 10e6:
                st *= 0.4          # sığ tahtada alış-satış sıçraması kademe sayısını şişirir
            row = self._base(s, X)
            row.update({"m5": _r(s5 / 5, 2), "m15": _r(s15 / 15, 2), "nb": nb, "tb": tn, "tbs": _r(tl / s15 * 100, 0),
                        "day": day, "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 5, st, f"dakikada {s15/15:.1f} kademe itiliyor ({nb} kurum, {tn} %{tl/s15*100:.0f})")
        self._out(5, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("m5", "Kademe/dk (5dk)", "num"),
                      C("m15", "Kademe/dk (15dk)", "num"), C("nb", "İten kurum sayısı", "num"), C("tb", "Baş iten", "broker"),
                      C("tbs", "Payı %", "num"), C("day", "Gün toplam kademe", "num"), C("sc", "Skor", "score")], rows,
                  note="Agresif alıcının (aktif taraf=alıcı) fiyatı bir önceki işlemin üzerine taşıdığı her adım, fiyat adımı (tick) cinsinden "
                       "sayılır. 'Baş iten' en çok kademe iten kurum.", sort="sc")

    def _f6(self, X):
        rows = []
        for s, L in X["BR"].items():
            q = X["Q"].get(s)
            if not q or not L:
                continue
            tt = max(L, key=lambda r: r["score"])
            if tt["stock_tl"] < 5e6 or tt["score"] < 25:
                continue
            ap = (self.akdp.get(s) or {}).get("m") or {}
            mc = next((x[2] for x in ap.get("b", []) + ap.get("s", []) if x[0] == tt["b"]), None)
            mnet = next((x[1] for x in ap.get("b", []) + ap.get("s", []) if x[0] == tt["b"]), None)
            cost = mc or tt["bavg"]
            if not cost:
                continue
            dist = (q["last"] / cost - 1) * 100
            lo = q.get("low") or q["last"]
            react = None
            if lo < cost * 0.995 and q["last"] > lo:
                react = (q["last"] / lo - 1) * 100
            st = 0.0
            if ((mnet or 0) > 0 or tt["ntl"] >= 1e6) and -2 <= dist <= 3:
                st = 0.45 + (0.35 if react and react > 1 else 0) + (0.2 if (mnet or 0) > 0 else 0)
            row = self._base(s, X)
            row.update({"b": tt["b"], "ts": tt["score"], "bavg": tt["bavg"], "mc": mc, "dist": _r(dist, 2), "mnet": mnet,
                        "net": tt["net"], "low": lo, "react": _r(react, 2), "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 6, st, f"{tt['b']} maliyetine %{dist:.1f} uzaklıkta")
        self._out(6, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("b", "Tahtacı", "broker"),
                      C("ts", "Tahtacı skoru", "num"), C("bavg", "Bugün alış ort.", "px"), C("mc", "Aylık AKD maliyet", "px"),
                      C("dist", "Maliyete uzaklık %", "chg"), C("mnet", "Aylık net lot", "lot"), C("net", "Bugün net lot", "lot"),
                      C("react", "Maliyet altı tepki %", "chg"), C("sc", "Destek skoru", "score")], rows,
                  note="Tahtacı = bugünkü tahtacı skoru en yüksek kurum. Maliyet = aylık AKD ortalama maliyeti (yoksa bugünkü alış ortalaması). "
                       "'Maliyet altı tepki' = gün içi maliyetin altına inip geri dönüş %. Sezgisel.", sort="ts")

    def _f7(self, X):
        rows = []
        sec = X["sec"]
        for s, L in X["BR"].items():
            if not L or s not in X["Q"]:
                continue
            tot = L[0]["stock_lot"]
            if L[0]["stock_tl"] < 3e6 or tot <= 0:
                continue
            # v1.21.2: AKD DAĞILIM tanımı (net alıcının payı, AKD sekmesi ALICILAR % ile aynı) — kümülatif ilk 1/3/5
            buys = sorted(L, key=lambda r: -(r.get("bshare") or 0))
            if not buys or not (buys[0].get("bshare") or 0):
                continue
            t1, t3, t5 = (min(1.0, sum((r.get("bshare") or 0) for r in buys[:k]) / 100.0) for k in (1, 3, 5))
            past = None
            for e in (self.conc.get(s) or []):
                if sec - e[0] >= 3300:
                    past = e
            d3 = (t3 - past[2]) * 100 if past else None
            st = _clip((t3 - 0.60) / 0.30) * 0.8 + (_clip((d3 or 0) / 10) * 0.2)
            row = self._base(s, X)
            row.update({"t1": _r(t1 * 100, 1), "t3": _r(t3 * 100, 1), "t5": _r(t5 * 100, 1), "b1": buys[0]["b"],
                        "d3": _r(d3, 1), "tl": L[0]["stock_tl"], "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 7, st, f"ilk 3 alıcı %{t3*100:.0f}" + (f" (1 saatte {d3:+.0f} puan)" if d3 is not None else ""))
        self._out(7, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("t1", "İlk 1 %", "num"),
                      C("t3", "İlk 3 %", "num"), C("t5", "İlk 5 %", "num"), C("b1", "En büyük alıcı", "broker"),
                      C("d3", "İlk 3 değişim (1 sa)", "chg"), C("tl", "Hacim ₺", "tl"), C("sc", "Skor", "score")], rows,
                  note="İlk N % = en büyük N net alıcının AKD DAĞILIM % toplamı (net alış lotu / tüm net alıcıların net lot toplamı — hisse AKD "
                       "sekmesindeki ALICILAR % ile aynı; yalnızca günlük AKD'si yüklü hisseler). Gün içi değişim 10 dakikalık "
                       "anlık görüntülerden (motor başladığından beri).", sort="sc")

    def _f8(self, X):
        rows = []
        n_ok = 0
        for s, t in list(self.takas.items()):
            if s not in X["Q"]:
                continue
            n_ok += 1
            m = {x[0]: x for x in (t.get("m") or [])}
            w = {x[0]: x for x in (t.get("w") or [])}
            qq = {x[0]: x for x in (t.get("q") or [])}
            best = None
            for b, x in m.items():
                if x[2] is None or x[4] is None:
                    continue
                dm = x[2] - x[4]
                if best is None or dm > best[1]:
                    best = (b, dm)
            if not best or best[1] < 0.3:
                continue
            b = best[0]
            x = m[b]
            dw = (w[b][2] - w[b][4]) if b in w and w[b][2] is not None and w[b][4] is not None else None
            dq = (qq[b][2] - qq[b][4]) if b in qq and qq[b][2] is not None and qq[b][4] is not None else None
            mono = (dw is not None and dw > 0) + (dq is not None and dq > best[1])
            st = _clip(best[1] / 4) * (0.6 + 0.2 * mono)
            row = self._base(s, X)
            row.update({"b": b, "pct": x[2], "dw": _r(dw, 2), "dm": _r(best[1], 2), "dq": _r(dq, 2), "lot": x[1],
                        "chg": x[5], "trend": "↑↑↑" if mono == 2 else "↑↑" if mono == 1 else "↑", "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 8, st, f"{b} takas payı 1 ayda {best[1]:+.1f} puan")
        self._out(8, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("b", "Kurum", "broker"),
                      C("pct", "Takas payı %", "num"), C("dw", "Δ 1 hafta", "chg"), C("dm", "Δ 1 ay", "chg"),
                      C("dq", "Δ 3 ay", "chg"), C("chg", "1 ay Δ lot", "lot"), C("trend", "Trend", "txt"),
                      C("sc", "Skor", "score")], rows,
                  note=f"MKK takas (İdealData REQ_TAKAS_FARK2) 1 hafta / 1 ay / 3 ay değişimi; ilk ~300 hisse (ciroya göre). "
                       f"Şu an {n_ok} hisse yüklü. Her hisse için payını en çok artıran kurum gösterilir.", sort="sc",
                  status="tam" if n_ok >= 250 else "kısmi")

    def _f9(self, X):
        rows = []
        for s, q in X["Q"].items():
            seen = {}
            for r in X["BR"].get(s, []):
                if _is_foreign(r["b"]) or _is_inst(r["b"]):
                    seen[r["b"]] = {"tn": r["net"], "ttl": r["ntl"]}
            ap = self.akdp.get(s) or {}
            for k in ("w", "m"):
                for x in ((ap.get(k) or {}).get("b") or []) + ((ap.get(k) or {}).get("s") or []):
                    if _is_foreign(x[0]) or _is_inst(x[0]):
                        seen.setdefault(x[0], {})[k] = x[1]
            tk = {x[0]: x for x in ((self.takas.get(s) or {}).get("m") or [])}
            for b, x in tk.items():
                if (_is_foreign(b) or _is_inst(b)):
                    seen.setdefault(b, {})["tk"] = x
            for b, e in seen.items():
                tk_ = e.get("tk")
                dp = (tk_[2] - tk_[4]) if tk_ and tk_[2] is not None and tk_[4] is not None else None
                new = bool(tk_ and (tk_[4] or 0) < 0.05 and (tk_[2] or 0) >= 0.2)
                pos = [v for v in (e.get("tn"), e.get("w"), e.get("m")) if v is not None]
                inc = len(pos) >= 2 and all(v > 0 for v in pos)
                dec = len(pos) >= 2 and all(v < 0 for v in pos)
                if not (new or inc or dec or abs(e.get("ttl") or 0) >= 5e6 or (dp and abs(dp) >= 0.5)):
                    continue
                flag = "YENİ" if new else "ARTIRIYOR" if inc else "AZALTIYOR" if dec else ("ALIYOR" if (e.get("ttl") or 0) > 0 else "SATIYOR")
                st = 0.0
                if flag in ("YENİ", "ARTIRIYOR"):
                    st = _clip(0.5 + _clip(abs(e.get("ttl") or 0) / 2e7) * 0.3 + _clip((dp or 0) / 2) * 0.2)
                row = self._base(s, X)
                row.update({"b": b, "typ": "Yabancı" if _is_foreign(b) else "Kurumsal", "ttl": e.get("ttl"), "tn": e.get("tn"),
                            "w": e.get("w"), "m": e.get("m"), "dp": _r(dp, 2), "flag": flag, "sc": round(st * 100)})
                rows.append(row)
                if st > (self._sig_new.get(s, {}).get(9) or (0,))[0]:
                    self._sigset(s, 9, st, f"{b} {flag.lower()}")
        self._out(9, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("b", "Kurum", "broker"),
                      C("typ", "Tür", "txt"), C("flag", "Durum", "txt"), C("ttl", "Bugün net ₺", "tl"), C("tn", "Bugün net lot", "lot"),
                      C("w", "Hafta AKD net", "lot"), C("m", "Ay AKD net", "lot"), C("dp", "Takas Δ 1 ay (puan)", "chg"),
                      C("sc", "Skor", "score")], rows,
                  note="Yabancı listesi: " + ", ".join(sorted(set(x.title() for x in FOREIGN))) + ". Kurumsal: emeklilik/fon/sigorta/portföy "
                       "adlı aracılar. YENİ = 1 ay önce takasta ~yok, şimdi ≥%0,2. ARTIRIYOR = bugün/hafta/ay net alıcı.",
                  sort="sc")

    def _f10(self, X):
        M = self.tavan_model or {}
        st_t, st_a, llr = M.get("t"), M.get("a"), M.get("llr") or []
        rows = []
        if st_t and st_a and llr:
            import bisect
            for s, q in X["Q"].items():
                b = self.bars.get(s)
                tb = self._today_bar(s, X)
                if len(b) < 61 or not tb:
                    continue
                fx = self._sigfeat(b, len(b) - 1, tb)
                if not fx:
                    continue
                v = self._llr(fx, st_t, st_a)
                pr = bisect.bisect_left(llr, v) / len(llr)
                if pr < 0.8:
                    continue
                st = _clip((pr - 0.85) / 0.14)
                row = self._base(s, X)
                row.update({"tv": "TAVANDA" if (q.get("ceiling") and q["last"] >= q["ceiling"] - 1e-9) else "", "sim": round(pr * 100, 1), "vr": _r(math.exp(fx[0]), 2), "r5": _r(fx[1] * 100, 1), "sq": _r(fx[2], 2),
                            "pos": _r(fx[3] * 100, 0), "sc": round(st * 100)})
                rows.append(row)
                self._sigset(s, 10, st, f"tavan öncesi imzaya benzerlik %{pr*100:.0f}")
        self._out(10, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sim", "Benzerlik (yüzdelik)", "num"), C("tv", "Bugün", "txt"),
                       C("vr", "Hacim/20g ×", "num"), C("r5", "5g getiri %", "chg"), C("sq", "Oynaklık 10g/60g", "num"),
                       C("pos", "20g bant konumu %", "num"), C("sc", "Skor", "score")], rows,
                  note=f"Model: {M.get('stocks', 0)} hissenin ~1 yıllık günlük barlarından {M.get('n_t', 0)} tavan gününün ÖNCEKİ gün "
                       f"imzası (hacim oranı, 5g getiri, oynaklık sıkışması, bant konumu, gün getirisi) — {M.get('n_a', 0)} normal güne karşı "
                       "Gauss olabilirlik oranı. Bugün canlı (öngörülen hacim) ile değerlendirilir; benzerlik ≥%80 olanlar listelenir. "
                       "Derinlik/AKD imzası tarihsel kayıt olmadığından henüz modelde değil (veri biriktiriliyor). Olasılık değil, benzerlik.",
                  sort="sim", status="kısmi")

    def _f11(self, X):
        rows = []
        sec = X["sec"]
        for s, q in X["Q"].items():
            fl = self.bars.float_lot(s)
            av = self.bars.avg_vol(s, 20)
            v = q.get("volume") or 0
            if not fl or not av or v <= 0:
                continue
            tr = v / fl * 100
            atr_ = av / fl * 100
            ratio = self._proj_vol(s, X) / av
            L = self.live.s.get(s)
            sp = None
            if L and L.mins:
                m = sec // 60
                last15 = sum(x[0] for k, x in L.mins.items() if m - 15 < k <= m)
                mins = [k for k in L.mins if 600 <= k < 1080]
                span = max(15, (min(m, 1080) - 600)) if mins else None
                if span:
                    sp = last15 / (v / span * 15) if v else None
            fltl = fl * q["last"]
            small = _clip(1.2 - math.log10(max(fltl, 1e7) / 1e8) * 0.4)
            if ratio < 1.3 and tr < 3:
                continue
            st = _clip((ratio - 1.5) / 3) * small
            row = self._base(s, X)
            row.update({"fl": fl, "fltl": fltl, "tr": _r(tr, 2), "atr": _r(atr_, 2), "ratio": _r(ratio, 2), "sp": _r(sp, 2),
                        "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 11, st, f"float devir %{tr:.1f} (normalin {ratio:.1f}×)")
        self._out(11, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("fl", "Fiili dolaşım lot", "lot"),
                       C("fltl", "Float ₺", "tl"), C("tr", "Bugün hacim/float %", "num"), C("atr", "20g ort. %", "num"),
                       C("ratio", "Öngörülen RVOL ×", "num"), C("sp", "Son 15 dk hız ×", "num"), C("sc", "Skor", "score")], rows,
                  note="Fiili dolaşım (float) = İş Yatırım SERMAYE × HAO oranı. RVOL = gün sonuna öngörülen hacim / 20g ort. Son 15 dk hız = "
                       "son 15 dk hacmi / gün içi ortalama 15 dk hacmi. Küçük float daha yüksek puan alır.", sort="sc")

    def _f12(self, X):
        rows = []
        sec = X["sec"]
        for s, L in list(self.live.s.items()):
            q = X["Q"].get(s)
            if not q or not L.samp:
                continue
            now = L.samp[-1]
            old = next((x for x in L.samp if sec - x[0] <= 1800), L.samp[0])
            ratio = now[3] / old[3] if (old[3] and len(L.samp) >= 5) else None
            walls = [(p, w) for p, w in L.bidwalls.items() if p < q["last"] and sec - w["first"] >= 600 and w["cur"] >= w["peak"] * 0.7]
            fresh = [(p, w) for p, w in L.bidwalls.items() if p < q["last"] and w["cur"] >= w["peak"] * 0.7]
            if not walls and not (ratio and ratio >= 1.3):
                if not fresh or (now[4] / now[1] if now[1] else 0) < 1.3:
                    continue
                walls_static = True
            else:
                walls_static = False
            big = max(walls, key=lambda x: x[1]["cur"] * x[0]) if walls else None
            ba = now[4] / now[1] if now[1] else None
            st = (_clip(((ratio or 1) - 1) / 1.0) * 0.6 + _clip(len(walls) / 3) * 0.4) if not walls_static else 0.0
            if walls_static:
                walls = fresh
                big = max(walls, key=lambda x: x[1]["cur"] * x[0])
            row = self._base(s, X)
            row.update({"b210": now[3], "old": old[3] if ratio is not None else None, "ratio": _r(((ratio or 1) - 1) * 100, 0) if ratio is not None else None,
                        "nw": len(walls), "durum": "anlık (süre ölçülüyor)" if walls_static else "KALICI",
                        "wp": big[0] if big else None, "wl": big[1]["cur"] if big else None,
                        "wa": round((sec - big[1]["first"]) / 60) if big else None, "ba": _r(ba, 2), "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 12, st, f"alış derinliği 30 dk'da %{((ratio or 1)-1)*100:+.0f}, {len(walls)} kalıcı büyük alış")
        self._out(12, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("b210", "Alış 2-10. kademe lot", "lot"),
                       C("old", "30 dk önce", "lot"), C("ratio", "Değişim %", "chg"), C("nw", "Kalıcı büyük alış", "num"),
                       C("wp", "En büyük: fiyat", "px"), C("wl", "lot", "lot"), C("wa", "yaş dk", "num"),
                       C("ba", "Alış/Satış derinlik", "num"), C("durum", "Durum", "txt"), C("sc", "Skor", "score")], rows,
                  note="Kalıcı büyük alış = ≥4× medyan ve ≥1 Mn ₺, ≥10 dk duran ve zirvesinin %70'inden fazlası yerinde. Canlı derinlikten, "
                       "motor başladığından beri ölçülür.", sort="sc", status="kısmi")

    def _f13(self, X):
        rows = []
        for s, L in list(self.live.s.items()):
            if s not in X["Q"] or not L.spoofs:
                continue
            sp = list(L.spoofs)
            a = [x for x in sp if x["side"] == "ask"]; b = [x for x in sp if x["side"] == "bid"]
            life = sum(x["life"] for x in sp) / len(sp)
            ratio = len(sp) / (len(sp) + L.genuine) if (len(sp) + L.genuine) else 0
            st = _clip(len(sp) / 12) * _clip(ratio / 0.4 + 0.3)
            row = self._base(s, X)
            row.update({"nsp": len(sp), "na": len(a), "nb": len(b), "tl": sum(x["tl"] for x in sp), "life": round(life),
                        "ratio": _r(ratio * 100, 0), "last": _hms(sp[-1]["t"]), "lp": sp[-1]["p"], "ls": "Satış" if sp[-1]["side"] == "ask" else "Alış",
                        "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 13, st, f"{len(sp)} sahte emir şüphesi (ort. ömür {life:.0f} sn)")
        self._out(13, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("nsp", "Şüpheli emir", "num"),
                       C("na", "Satış tarafı", "num"), C("nb", "Alış tarafı", "num"), C("tl", "Toplam ₺", "tl"),
                       C("life", "Ort. ömür sn", "num"), C("ratio", "Büyük emirlerde oran %", "num"), C("last", "Son", "time"),
                       C("lp", "Son fiyat", "px"), C("ls", "Taraf", "txt"), C("sc", "Skor", "score")], rows,
                  note="Şüpheli = ≥4× medyan ve ≥400 B₺ eklenen emir 120 sn içinde %70+ geri çekildi ve en fazla %25'i gerçekleşti. "
                       "Derinlik verisi kurum kimliği taşımaz; kimin yaptığı bilinmez. Canlı, motor başladığından beri. Sezgisel.",
                  sort="nsp", status="kısmi")

    def _f14(self, X):
        rows = []
        today = _today()
        cur = {}
        for s, L in list(self.live.s.items()):
            ca = L.close_auc
            q = X["Q"].get(s)
            if not ca or not q or not ca["lot"]:
                continue
            pre = L.pre_close_px or ca.get("pre")
            push = (ca["px"] / pre - 1) * 100 if pre else None
            tb, tl = (ca["buyers"].most_common(1) or [(0, 0)])[0]
            ts, sl = (ca["sellers"].most_common(1) or [(0, 0)])[0]
            nm = self.store.brokers
            share = ca["lot"] / (q.get("volume") or ca["lot"]) * 100
            cur[s] = {"px": ca["px"], "pre": pre, "push": _r(push, 2), "lot": ca["lot"], "tl": ca["tl"], "share": _r(share, 1),
                      "tb": nm[tb] if tb < len(nm) else "", "tbs": _r(tl / ca["lot"] * 100, 0),
                      "ts": nm[ts] if ts < len(nm) else "", "tss": _r(sl / ca["lot"] * 100, 0)}
        if cur and _sec_now() >= 65400:
            self.closing_hist[today] = cur
            _jsave(OPD / "closing" / f"{today}.json", cur)
        # geçmiş: kapanışta itilen (push>0.5) hisselerin ertesi gün sonucu
        stat = collections.defaultdict(lambda: [0, 0, 0.0])
        for d, m in self.closing_hist.items():
            if d == today:
                continue
            ds = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            for s, e in m.items():
                if (e.get("push") or 0) < 0.5:
                    continue
                b = self.bars.get(s)
                idx = next((i for i, x in enumerate(b) if x["d"] == ds), None)
                nxt = None
                if idx is not None and idx + 1 < len(b):
                    nxt = b[idx + 1]["c"] / b[idx]["c"] - 1
                elif idx is not None and idx + 1 == len(b) and s in X["Q"]:
                    nxt = X["Q"][s]["last"] / b[idx]["c"] - 1
                if nxt is None:
                    continue
                st_ = stat[s]; st_[0] += 1; st_[1] += nxt > 0; st_[2] += nxt
        src = cur or (self.closing_hist.get(sorted(self.closing_hist)[-1]) if self.closing_hist else {})
        src_day = today if cur else (sorted(self.closing_hist)[-1] if self.closing_hist else None)
        for s, e in src.items():
            if s not in X["Q"]:
                continue
            h = stat.get(s)
            st = _clip((e.get("push") or 0) / 2) * _clip((e.get("tbs") or 0) / 40 + 0.3) if src_day == today else 0
            row = self._base(s, X)
            row.update({**e, "hn": h[0] if h else 0, "hw": _r(h[1] / h[0] * 100, 0) if h else None,
                        "hr": _r(h[2] / h[0] * 100, 2) if h else None, "sc": round(st * 100)})
            rows.append(row)
            if st:
                self._sigset(s, 14, st, f"kapanışta %{e.get('push') or 0:+.1f} itildi ({e.get('tb')})")
        nd = len([d for d in self.closing_hist if d != today])
        self._out(14, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("pre", "18:00 öncesi", "px"),
                       C("px", "Kapanış seansı", "px"), C("push", "İtme %", "chg"), C("lot", "Seans lot", "lot"),
                       C("share", "Gün hacmi payı %", "num"), C("tb", "Baş alıcı", "broker"), C("tbs", "Payı %", "num"),
                       C("ts", "Baş satıcı", "broker"), C("hn", "Geçmiş itme", "num"), C("hw", "Ertesi gün + %", "num"),
                       C("hr", "Ertesi gün ort. %", "chg"), C("sc", "Skor", "score")], rows,
                  note=(f"Gösterilen gün: {src_day or '—'}. " if rows else "Kapanış seansı 18:00–18:10; veriler 18:00'den sonra oluşur. ")
                       + f"Ertesi gün sonucu geçmişi: veri biriktiriliyor ({nd} gün kayıtlı).", sort="push",
                  status="kısmi", hist=f"veri biriktiriliyor ({nd + (1 if cur else 0)} gün)")

    def _f15(self, X):
        rows = []
        today = _today()
        nm = self.store.brokers
        cur = {}
        for s, L in list(self.live.s.items()):
            oa = L.open_auc
            q = X["Q"].get(s)
            if not oa or not q or not q.get("prev_close") or not oa["lot"]:
                continue
            gap = (oa["px"] / q["prev_close"] - 1) * 100
            av = self.bars.avg_vol(s, 20)
            vs = oa["lot"] / av * 100 if av else None
            dc = (q["ceiling"] / oa["px"] - 1) * 100 if q.get("ceiling") else None
            tb, tl = (oa["buyers"].most_common(1) or [(0, 0)])[0]
            res = (q["last"] / oa["px"] - 1) * 100
            cur[s] = {"op": oa["px"], "gap": _r(gap, 2), "lot": oa["lot"], "tl": oa["tl"], "vs": _r(vs, 1), "dc": _r(dc, 2),
                      "tb": nm[tb] if tb < len(nm) else "", "tbs": _r(tl / oa["lot"] * 100, 0)}
            st = _clip(gap / 5) * _clip((vs or 0) / 5 + 0.3) * (1.2 if dc is not None and dc <= 2 else 1)
            row = self._base(s, X)
            row.update({**cur[s], "res": _r(res, 2), "near": "TAVANA YAKIN" if dc is not None and dc <= 2 else "", "sc": round(_clip(st) * 100)})
            rows.append(row)
            self._sigset(s, 15, st * (1 if X["sec"] < 39600 else 0.5), f"açılış boşluğu %{gap:+.1f}")
        if cur:
            self.opening_hist[today] = cur
            if not getattr(self, "_open_saved", None) == today or X["sec"] < 37000:
                _jsave(OPD / "opening" / f"{today}.json", cur)
                self._open_saved = today
        self._out(15, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("op", "Açılış", "px"),
                       C("gap", "Boşluk %", "chg"), C("lot", "Açılış lot", "lot"), C("tl", "Açılış ₺", "tl"),
                       C("vs", "20g hacme oran %", "num"), C("dc", "Tavana %", "num"), C("near", "", "txt"),
                       C("tb", "Açılış baş alıcı", "broker"), C("tbs", "Payı %", "num"), C("res", "Açılıştan beri %", "chg"),
                       C("sc", "Skor", "score")], rows,
                  note="Açılış seansı (09:40–10:00) eşleşmesi = işlem kaydında aktif tarafı olmayan (seans) işlemler, 10:05 öncesi. "
                       f"Açılış emir dengesizliği (emir defteri) geçmişte kaydedilmediğinden eşleşme sonucu kullanılır. Kayıtlı gün: {len(self.opening_hist)}.",
                  sort="gap", hist=f"veri biriktiriliyor ({len(self.opening_hist)} gün)")

    def _mins_vwap(self, L: SymLive):
        ks = sorted(k for k in L.mins if 600 <= k < 1080)
        cv = ct = 0.0
        out = []
        for k in ks:
            m = L.mins[k]
            cv += m[0]; ct += m[1]
            out.append((k, m[2], ct / cv if cv else m[2], m[0], m[1], m[3], m[4]))
        return out

    def _f16(self, X):
        rows = []
        for s, L in list(self.live.s.items()):
            q = X["Q"].get(s)
            if not q or len(L.mins) < 20:
                continue
            mv = self._mins_vwap(L)
            if len(mv) < 20:
                continue
            above = sum(1 for x in mv if x[1] > x[2])
            pct = above / len(mv)
            dips = bought = 0
            below_at = None
            for x in mv:
                if x[1] < x[2] and below_at is None:
                    below_at = x[0]; dips += 1
                elif x[1] >= x[2] and below_at is not None:
                    if x[0] - below_at <= 15:
                        bought += 1
                    below_at = None
            vw = q.get("vwap") or mv[-1][2]
            dist = (q["last"] / vw - 1) * 100 if vw else None
            if pct < 0.5:
                continue
            st = _clip((pct - 0.6) / 0.35) * (1 if (dist or 0) > 0 else 0.4)
            row = self._base(s, X)
            row.update({"vw": vw, "dist": _r(dist, 2), "pct": _r(pct * 100, 0), "mins": len(mv), "dips": dips, "bought": bought,
                        "tl": q.get("turnover"), "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 16, st, f"sürenin %{pct*100:.0f}'i VWAP üstü")
        self._out(16, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("vw", "VWAP", "px"),
                       C("dist", "VWAP uzaklık %", "chg"), C("pct", "VWAP üstü süre %", "num"), C("mins", "Ölçülen dk", "num"),
                       C("dips", "VWAP altı iniş", "num"), C("bought", "15 dk'da geri alınan", "num"), C("tl", "Hacim ₺", "tl"),
                       C("sc", "Skor", "score")], rows,
                  note="Dakikalık kapanışlar işlem kaydından; VWAP gün içi kümülatif (sürekli seans). Geri alınan = VWAP altına inip ≤15 dk'da "
                       "tekrar üstüne çıkış.", sort="sc")

    def _f17(self, X):
        rows = []
        swb = collections.Counter(); swt = collections.Counter()
        for x in list(self.hub.sweeps):
            if x.get("side") == "buy":
                swb[x["sym"]] += 1; swt[x["sym"]] += x["tl"]
        for s, q in X["Q"].items():
            b = self.bars.get(s)
            if len(b) < 21:
                continue
            R = max((x.get("h") or 0) for x in b[-20:])
            if R <= 0 or not q.get("last"):
                continue
            if not (q["last"] > R or (q.get("high") or 0) > R and q["last"] >= R * 0.995):
                continue
            pa = X["PARA"].get(s) or {}
            L = X["BR"].get(s) or []
            tb = L[0] if L else None
            ag = tb["aa"] / tb["buy"] if tb and tb["buy"] else 0
            sh = tb["bshare"] if tb else 0
            st = _clip((q["last"] / R - 1) / 0.03 + 0.3) * _clip(((pa.get("netp") or 0) + 10) / 40) * _clip(0.4 + ag * 0.6) * _clip((self._rvol(s, X) or 0) / 1.5)
            row = self._base(s, X)
            row.update({"R": R, "br": _r((q["last"] / R - 1) * 100, 2), "rv": _r(self._rvol(s, X), 2), "netp": pa.get("netp"),
                        "b": tb["b"] if tb else None, "bs": sh, "ag": _r(ag * 100, 0), "sw": swb.get(s, 0), "swt": swt.get(s, 0),
                        "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 17, st, f"20g direnç {R:g} kırıldı, {tb['b'] if tb else '-'} agresif %{ag*100:.0f}")
        self._out(17, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("R", "20g direnç", "px"),
                       C("br", "Kırılım %", "chg"), C("rv", "RVOL ×", "num"), C("netp", "Net akış %", "chg"),
                       C("b", "Baş net alıcı", "broker"), C("bs", "Alış payı %", "num"), C("ag", "Agresif oranı %", "num"),
                       C("sw", "Alış süpürmesi", "num"), C("swt", "Süpürme ₺", "tl"), C("sc", "Skor", "score")], rows,
                  note="Direnç = son 20 işlem gününün en yükseği (İş Yatırım). Onay = net agresif para akışı, baş alıcının agresif alım oranı, "
                       "RVOL ve alış süpürmeleri.", sort="sc")

    def _seller_recent(self, s: str, bname: str, sec: int, win: int = 1800) -> tuple[float, float]:
        e = self.store.syms.get(s)
        bi = self.store.bidx.get(bname) if hasattr(self.store, "bidx") else None
        if e is None or bi is None:
            return 0.0, 0.0
        import bisect
        with self.store.lock:
            n = len(e.t)
            i0 = bisect.bisect_left(e.t, max(0, sec - win))
            rec = sum(e.l[i] for i in range(i0, n) if e.s[i] == bi)
            tot = e.lot_sum if hasattr(e, "lot_sum") else 0
        return rec, tot

    def _f18(self, X):
        rows = []
        sec = X["sec"]
        for s, L in list(self.live.s.items()):
            q = X["Q"].get(s)
            if not q:
                continue
            if len(L.samp) >= 10:
                now = L.samp[-1]
                old = next((x for x in L.samp if sec - x[0] <= 1800), L.samp[0])
                dl = (1 - now[1] / old[1]) if old[1] else 0.0
                do = (1 - now[2] / old[2]) if (old[2] and now[2]) else None
            else:
                now = L.samp[-1] if L.samp else (None, None, None)
                old = (None, None, None); dl = 0.0; do = None
            ap = (self.akdp.get(s) or {}).get("m") or {}
            ms = ap.get("s")[0] if ap.get("s") else None
            stop = None; rate = None
            if ms:
                today_net = next((r["net"] for r in X["BR"].get(s, []) if r["b"] == ms[0]), None)
                stop = today_net is not None and today_net >= 0
                if today_net is None:
                    stop = True
                rec, _ = self._seller_recent(s, ms[0], sec)
                tsell = next((r["sell"] for r in X["BR"].get(s, []) if r["b"] == ms[0]), 0)
                el = max(1800, min(sec, 64800) - 36000)
                rate = (rec / 1800) / (tsell / el) if tsell else 0
            if dl < 0.2 and not stop:
                continue
            if stop and ms and (ms[1] or 0) > -0.01 * ((ap.get("tot") or 0) / 2):
                if dl < 0.2:
                    continue      # aylık satıcı küçükse 'satışı kesti' anlamsız
            st = _clip(dl / 0.4) * 0.6 + (0.4 if stop else 0)
            row = self._base(s, X)
            row.update({"ask": now[1], "ask0": old[1], "dl": _r(dl * 100, 0), "do": _r(do * 100 if do is not None else None, 0),
                        "ms": ms[0] if ms else None, "msn": ms[1] if ms else None, "stop": "SATIŞI KESTİ" if stop else "",
                        "rate": _r(rate, 2), "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 18, st, f"satış derinliği 30 dk'da %{dl*100:.0f} azaldı" + (f", {ms[0]} satışı kesti" if stop else ""))
        self._out(18, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("ask", "Satış lot (25 kad.)", "lot"),
                       C("ask0", "30 dk önce", "lot"), C("dl", "Lot azalış %", "chg"), C("do", "Emir sayısı azalış %", "chg"),
                       C("ms", "Aylık en büyük satıcı", "broker"), C("msn", "Aylık net", "lot"), C("stop", "Bugün", "txt"),
                       C("rate", "Son 30 dk satış hızı ×", "num"), C("sc", "Skor", "score")], rows,
                  note="Satış derinliği dakikalık örneklerden (motor başladığından beri). Büyük satıcı = aylık AKD'de en çok net satan; bugün net "
                       "satıcı değilse 'satışı kesti'. Satış hızı = son 30 dk satış lotu / gün ortalaması.", sort="sc", status="kısmi")

    def _f19(self, X):
        rows = []
        fl = self.hub.flows
        with fl.lock:
            items = list(fl.sym.items()); names = fl.names
        BRX = collections.defaultdict(list)
        for r in self.hub.broker_rows(nocross=True):
            BRX[r["s"]].append(r)
        for s, a in items:
            if s not in X["Q"] or not a["lot"]:
                continue
            cx = {bi: v[9] + v[11] + v[13] for bi, v in a["br"].items() if (v[9] + v[11] + v[13]) > 0}
            if not cx:
                continue
            tot = sum(cx.values())
            share = tot / a["lot"] * 100
            if share < 1:
                continue
            tb, tl = max(cx.items(), key=lambda x: x[1])
            L = X["BR"].get(s, []); LX = BRX.get(s, [])
            best = max(L, key=lambda r: r["score"]) if L else None
            bestx = max(LX, key=lambda r: r["score"]) if LX else None
            bn = names[tb] if tb < len(names) else ""
            own = next((r for r in L if r["b"] == bn), None)
            row = self._base(s, X)
            row.update({"vol": a["lot"], "x": tot, "xs": _r(share, 1), "xb": bn, "xbs": _r(tl / tot * 100, 0),
                        "xown": _r(tl / ((own["buy"] if own else 0) or 1) * 100, 0) if own else None,
                        "tt": best["b"] if best else None, "ts": best["score"] if best else None,
                        "ttx": bestx["b"] if bestx else None, "tsx": bestx["score"] if bestx else None,
                        "rnet": own["net"] if own else None})
            rows.append(row)
        self._out(19, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("vol", "Toplam lot", "lot"),
                       C("x", "Çapraz lot", "lot"), C("xs", "Çapraz %", "num"), C("xb", "En çok çapraz", "broker"),
                       C("xbs", "Çaprazın payı %", "num"), C("xown", "Kendi alımının çaprazı %", "num"),
                       C("rnet", "Gerçek net lot", "lot"), C("tt", "Tahtacı (brüt)", "broker"), C("ts", "Skor", "num"),
                       C("ttx", "Tahtacı (çapraz hariç)", "broker"), C("tsx", "Skor", "num")], rows,
                  note="Çapraz = alıcı ve satıcı kurumun aynı olduğu işlem (iki tarafta aynı aracı; müşteriler farklı olabilir). Çapraz net "
                       "pozisyonu değiştirmez ama hacmi şişirir; 'çapraz hariç' tahtacı skoru bu işlemleri çıkarır. Tahtacı Tespiti ekranında "
                       "'Çapraz hariç' seçeneği de vardır.", sort="xs")

    def _f20(self, X):
        tl = collections.Counter()
        for s, L in X["BR"].items():
            for r in L:
                tl[r["b"]] += r["btl"] + r["stl"]
        top = [b for b, _ in tl.most_common(25)]
        syms = sorted(X["BR"])
        vec = {b: {} for b in top}
        for s in syms:
            for r in X["BR"][s]:
                if r["b"] in vec and r["ntl"]:
                    vec[r["b"]][s] = r["ntl"]
        mvec = {b: {} for b in top}
        for s, ap in self.akdp.items():
            m = ap.get("m") or {}
            px = (X["Q"].get(s) or {}).get("last") or 0
            for x in (m.get("b") or []) + (m.get("s") or []):
                if x[0] in mvec:
                    mvec[x[0]][s] = x[1] * px

        def cos(a, b):
            ks = set(a) & set(b)
            num = sum(a[k] * b[k] for k in ks)
            na = math.sqrt(sum(v * v for v in a.values())); nb = math.sqrt(sum(v * v for v in b.values()))
            return num / (na * nb) if na and nb else 0.0, ks
        pairs = []
        for i in range(len(top)):
            for j in range(i + 1, len(top)):
                a, b = top[i], top[j]
                c, ks = cos(vec[a], vec[b])
                cm, _ = cos(mvec[a], mvec[b])
                both = [k for k in ks if vec[a][k] > 0 and vec[b][k] > 0]
                ts = max(both, key=lambda k: vec[a][k] + vec[b][k]) if both else None
                pairs.append({"a": a, "b": b, "sim": _r(c * 100, 0), "msim": _r(cm * 100, 0), "ncom": len(both), "s": ts,
                              "tl": _r(sum(vec[a][k] + vec[b][k] for k in both), 0)})
        # kümeler: benzerlik ≥ 35
        par = {b: b for b in top}

        def find(x):
            while par[x] != x:
                par[x] = par[par[x]]; x = par[x]
            return x
        edges = [p for p in pairs if (p["sim"] or 0) >= 35]
        for p in edges:
            par[find(p["a"])] = find(p["b"])
        cl = collections.defaultdict(list)
        for b in top:
            cl[find(b)].append(b)
        clusters = [v for v in cl.values() if len(v) > 1]
        cid = {}
        for i, v in enumerate(sorted(clusters, key=len, reverse=True)):
            for b in v:
                cid[b] = i + 1
        nodes = [{"id": b, "tl": tl[b], "c": cid.get(b, 0)} for b in top]
        # ortak alım yapılan hisseler: aynı kümede ≥2 kurumun net aldığı hisseler → sinyal
        for v in clusters:
            for s in syms:
                buyers = [b for b in v if vec[b].get(s, 0) > 2e6]
                if len(buyers) >= 2:
                    self._sigset(s, 20, _clip(len(buyers) / 4 + 0.25), f"ortak hareket eden {len(buyers)} kurum alıcı: {', '.join(buyers[:3])}")
        pairs.sort(key=lambda p: -(p["sim"] or 0))
        self._out(20, [C("a", "Kurum A", "broker"), C("b", "Kurum B", "broker"), C("sim", "Benzerlik bugün %", "num"),
                       C("msim", "Benzerlik aylık AKD %", "num"), C("ncom", "Ortak alınan hisse", "num"), C("s", "En büyük ortak", "sym"),
                       C("tl", "Ortak net ₺", "tl")], pairs[:150],
                  note="En çok işlem yapan 25 kurumun hisse bazında net ₺ vektörleri arasında kosinüs benzerliği (bugün işlem kaydı; ayrıca "
                       "aylık AKD). Grafik: benzerlik ≥%35 bağlantılar, aynı renk = aynı küme. Benzerlik ortak müşteri/organizasyon kanıtı değildir.",
                  extra={"graph": {"nodes": nodes, "edges": [{"a": p["a"], "b": p["b"], "w": p["sim"]} for p in edges]},
                         "clusters": [sorted(v) for v in clusters]})

    def _f21(self, X):
        ev = collections.defaultdict(list)
        base = []
        for s, wins in list(self.akdweek.items()):
            b = self.bars.get(s)
            if len(b) < 30:
                continue
            idx = {x["d"]: i for i, x in enumerate(b)}
            for key, pk in wins.items():
                d2 = key.split("-")[1]
                ds = f"{d2[:4]}-{d2[4:6]}-{d2[6:]}"
                i = idx.get(ds)
                if i is None:
                    continue
                c0 = b[i]["c"]
                fr = {}
                for h in (1, 5, 20):
                    if i + h < len(b):
                        fr[h] = b[i + h]["c"] / c0 - 1
                    elif i + h == len(b) and s in X["Q"]:
                        fr[h] = X["Q"][s]["last"] / c0 - 1
                if 5 in fr:
                    base.append(fr[5])
                vol = (pk.get("tot") or 0) / 2
                for x in (pk.get("b") or [])[:3]:
                    if vol and x[1] / vol >= 0.05:
                        ev[x[0]].append((s, fr))
        rows = []
        bm = sum(base) / len(base) if base else 0
        succ = {}
        for br, L in ev.items():
            r = {}
            for h in (1, 5, 20):
                vs = [f[h] for _, f in L if h in f]
                r[h] = (sum(vs) / len(vs) * 100, sum(1 for v in vs if v > 0) / len(vs) * 100, len(vs)) if vs else (None, None, 0)
            if r[5][2] < 3:
                continue
            last_s = None
            for s, Lb in X["BR"].items():
                for x in Lb:
                    if x["b"] == br and x["ntl"] > 0 and (last_s is None or x["ntl"] > last_s[1]):
                        last_s = (s, x["ntl"])
            row = {"br": br, "n": len(L), "r1": _r(r[1][0], 2), "r5": _r(r[5][0], 2), "h5": _r(r[5][1], 0), "r20": _r(r[20][0], 2),
                   "h20": _r(r[20][1], 0), "n20": r[20][2], "ex5": _r(r[5][0] - bm * 100, 2) if r[5][0] is not None else None,
                   "s": last_s[0] if last_s else None}
            rows.append(row)
            succ[br] = row
        self.success = succ
        for s, Lb in X["BR"].items():
            if not Lb:
                continue
            tb = Lb[0]
            e = succ.get(tb["b"])
            if e and tb["ntl"] > 3e6 and (e["h5"] or 0) >= 55 and (e["ex5"] or 0) > 0:
                self._sigset(s, 21, _clip((e["h5"] - 50) / 25) * _clip(e["n"] / 10 + 0.3),
                             f"{tb['b']} geçmişte 5g isabet %{e['h5']:.0f} ({e['n']} toplama)")
        nwin = len({k for v in self.akdweek.values() for k in v})
        self._out(21, [C("br", "Kurum", "broker"), C("n", "Toplama olayı", "num"), C("r1", "1g ort. %", "chg"),
                       C("r5", "5g ort. %", "chg"), C("h5", "5g isabet %", "num"), C("ex5", "5g piyasa üstü %", "chg"),
                       C("r20", "20g ort. %", "chg"), C("h20", "20g isabet %", "num"), C("n20", "20g örnek", "num"),
                       C("s", "Bugün en çok aldığı", "sym")], rows,
                  note=f"Olay = haftalık AKD penceresinde (5 iş günü) kurumun ilk 3 net alıcıdan biri ve hacmin ≥%5'i olması; getiri pencere "
                       f"sonundan 1/5/20 iş günü sonra (İş Yatırım kapanış). Piyasa üstü = aynı pencerelerin tüm hisse ortalamasına göre. "
                       f"Şu an {len(self.akdweek)} hisse × {nwin} pencere yüklü (en çok 200 hisse × 9 hafta; yavaş kuyruk). Geçmiş başarı "
                       "gelecek garantisi değildir.", sort="n", status="tam" if len(self.akdweek) >= 150 else "kısmi",
                  hist=f"{len(self.akdweek)} hisse × {nwin} hafta")

    _KAP_CAT = [("Finansal", ("Finansal Rapor", "Faaliyet Raporu")), ("Sermaye/Bedelsiz", ("Sermaye Artırım", "Bedelsiz", "Bedelli", "Sermaye Azalt")),
                ("Pay alım/Geri alım", ("Geri Alım", "Pay Alım Satım", "Payların Geri")), ("Kâr payı", ("Kar Payı", "Kâr Payı", "Temettü")),
                ("İş ilişkisi/İhale", ("Yeni İş İlişkisi", "İhale", "Sözleşme", "Sipariş")), ("Özel durum", ("Özel Durum",))]

    def _kap_cat(self, x: dict) -> str:
        t = (x.get("sub") or "") + " " + (x.get("sum") or "")
        for name, keys in self._KAP_CAT:
            if any(k.lower() in t.lower() for k in keys):
                return name
        return "Diğer"

    def _f22(self, X):
        per = collections.defaultdict(list)
        now = _now()
        cut = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        for x in self.kap.values():
            if (x.get("d") or "") < cut:
                continue
            for c in x.get("codes") or []:
                if c in X["Q"]:
                    per[c].append(x)
        rows = []
        for s, L in per.items():
            L.sort(key=lambda x: x.get("d") or "", reverse=True)
            last = L[0]
            cats = collections.Counter(self._kap_cat(x) for x in L)
            imp = [x for x in L if self._kap_cat(x) != "Diğer"]
            li = imp[0] if imp else None
            age = None
            if li:
                try:
                    age = (now.replace(tzinfo=None) - datetime.strptime(li["d"], "%Y-%m-%d %H:%M")).total_seconds() / 86400
                except Exception:
                    pass
            pa = X["PARA"].get(s) or {}
            acc = ((self.akdp.get(s) or {}).get("m") or {}).get("b")
            st = 0.0
            if li and age is not None and age <= 3 and ((pa.get("netp") or 0) > 5 or acc):
                st = _clip(0.5 + (0.3 if self._kap_cat(li) in ("Sermaye/Bedelsiz", "Pay alım/Geri alım", "İş ilişkisi/İhale") else 0)
                           + _clip((pa.get("netp") or 0) / 50) * 0.2)
            row = self._base(s, X)
            row.update({"nk": len(L), "ld": last.get("d"), "lsub": last.get("sub"), "icat": self._kap_cat(li) if li else None,
                        "id": li.get("d") if li else None, "isub": (li.get("sub") or "")[:70] if li else None,
                        "cats": ", ".join(f"{k} {v}" for k, v in cats.most_common(3)), "netp": pa.get("netp"),
                        "acc": acc[0][0] if acc else None, "kid": li.get("i") if li else last.get("i"), "sc": round(st * 100)})
            rows.append(row)
            if st:
                self._sigset(s, 22, st, f"KAP: {self._kap_cat(li)} ({li['d'][:10]})")
        self._out(22, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("icat", "Önemli kategori", "txt"),
                       C("id", "Tarih", "txt"), C("isub", "Konu", "txt"), C("nk", "30g bildirim", "num"), C("cats", "Dağılım", "txt"),
                       C("netp", "Bugün net akış %", "chg"), C("acc", "Aylık baş alıcı", "broker"), C("sc", "Skor", "score")], rows,
                  note=f"KAP bildirim sorgu API (kap.org.tr; devre kesici bildirimleri hariç). Durum: "
                       f"{'erişilebilir' if self.kap_status.get('ok') else 'ERİŞİLEMEDİ ' + str(self.kap_status.get('err') or '')} · "
                       f"{self.kap_status.get('days', 0)} gün, son {self.kap_status.get('last') or '—'}. Yaklaşan: Eylül (9 aylık) finansal "
                       "raporlar SPK süresine göre ~Ekim sonu–Kasım ilk yarısı beklenir (tahmini; KAP takviminden değil).",
                  sort="id", extra={"kap_url": "https://www.kap.org.tr/tr/Bildirim/"},
                  status="tam" if self.kap_status.get("ok") else "kısmi")

    def _ret(self, s: str, n: int, X) -> float | None:
        b = self.bars.get(s)
        q = X["Q"].get(s)
        if len(b) < n or not q:
            return None
        return (q["last"] / b[-n]["c"] - 1) * 100

    def _f23(self, X):
        SEC = X["SEC"]
        mem = collections.defaultdict(list)
        for s in X["Q"]:
            if SEC.get(s):
                mem[SEC[s]].append(s)
        from app.v120 import SECTOR_LABELS
        psec = {e["sec"]: e for e in X["PSEC"]}
        srows = []
        rows = []
        for sc, L in mem.items():
            if len(L) < 3:
                continue
            ch = [((X["PARA"].get(s) or {}).get("c")) for s in L]
            ch = [c for c in ch if c is not None]
            avg = sum(ch) / len(ch) if ch else 0
            r5 = [v for v in (self._ret(s, 5, X) for s in L) if v is not None]
            r20 = [v for v in (self._ret(s, 20, X) for s in L) if v is not None]
            a5 = sum(r5) / len(r5) if r5 else None; a20 = sum(r20) / len(r20) if r20 else None
            e = psec.get(sc) or {}
            netp = e.get("netp")
            starting = (netp or 0) >= 8 and (a20 is None or a20 <= 5) and avg > 0
            srows.append({"sec": SECTOR_LABELS.get(sc, sc), "n": len(L), "netp": netp, "net": e.get("net"), "avg": _r(avg, 2),
                          "a5": _r(a5, 2), "a20": _r(a20, 2), "st": "GİRİŞ BAŞLIYOR" if starting else "",
                          "s": max(L, key=lambda s: (X["PARA"].get(s) or {}).get("net") or 0)})
            if (netp or 0) < 3:
                continue
            for s in L:
                p = X["PARA"].get(s) or {}
                c = p.get("c")
                if c is None or c >= avg:
                    continue
                lag = avg - c
                st = (_clip((netp or 0) / 20) * _clip(lag / 3) * (1.2 if starting else 0.8)) if (p.get("netp") or 0) > 0 else 0
                row = self._base(s, X)
                row.update({"sec": SECTOR_LABELS.get(sc, sc), "snetp": netp, "savg": _r(avg, 2), "s5": _r(a5, 2), "lag": _r(lag, 2),
                            "netp": p.get("netp"), "st": "GİRİŞ BAŞLIYOR" if starting else "", "sc": round(_clip(st) * 100)})
                rows.append(row)
                if st:
                    self._sigset(s, 23, st, f"{SECTOR_LABELS.get(sc, sc)} sektörüne giriş, hisse %{lag:.1f} geride")
        srows.sort(key=lambda r: -(r["netp"] or -999))
        self._out(23, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sec", "Sektör", "txt"),
                       C("snetp", "Sektör net akış %", "chg"), C("savg", "Sektör ort. %", "chg"), C("s5", "Sektör 5g %", "chg"),
                       C("lag", "Geride (puan)", "num"), C("netp", "Hisse net akış %", "chg"), C("st", "Durum", "txt"),
                       C("sc", "Skor", "score")], rows,
                  note="Sektör = Borsa İstanbul sektör endeksi üyeliği. Giriş başlıyor = bugün net agresif akış ≥%8, son 20 gün sektör getirisi "
                       "≤%5 ve gün ortalaması pozitif. Liste: net girişli sektörlerde sektör ortalamasının gerisinde kalan hisseler.",
                  sort="sc", extra={"tables": [{"title": "Sektörler", "cols": [C("sec", "Sektör", "txt"), C("n", "Hisse", "num"),
                                                 C("netp", "Net akış %", "chg"), C("net", "Net ₺", "tl"), C("avg", "Bugün ort. %", "chg"),
                                                 C("a5", "5g %", "chg"), C("a20", "20g %", "chg"), C("st", "Durum", "txt"),
                                                 C("s", "Lider (net ₺)", "sym")], "rows": srows}]})

    def _f24(self, X):
        SEC = X["SEC"]
        from app.v120 import SECTOR_LABELS
        mem = collections.defaultdict(list)
        for s in X["Q"]:
            if SEC.get(s):
                mem[SEC[s]].append(s)

        def rets(s):
            b = self.bars.get(s)[-61:]
            return {b[i]["d"]: b[i]["c"] / b[i - 1]["c"] - 1 for i in range(1, len(b)) if b[i - 1]["c"]}
        rows = []
        for sc, L in mem.items():
            ch = {s: (X["PARA"].get(s) or {}).get("c") for s in L}
            ldr = max((s for s in L if ch.get(s) is not None), key=lambda s: ch[s], default=None)
            if not ldr:
                continue
            q = X["Q"][ldr]
            at_ceil = q.get("ceiling") and q["last"] >= q["ceiling"] - 1e-9
            if ch[ldr] < 5 and not at_ceil:
                continue
            rl = rets(ldr)
            for s in L:
                if s == ldr or ch.get(s) is None:
                    continue
                rs = rets(s)
                ks = sorted(set(rl) & set(rs))
                cr = _corr([rl[k] for k in ks], [rs[k] for k in ks])
                if cr is None or cr < 0.45 or ch[s] > ch[ldr] * 0.5:
                    continue
                lag = ch[ldr] - ch[s]
                st = _clip((cr - 0.4) / 0.4) * _clip(lag / 6) * (1 if ((X["PARA"].get(s) or {}).get("netp") or 0) > 0 else 0.6)
                row = self._base(s, X)
                row.update({"sec": SECTOR_LABELS.get(sc, sc), "ldr": ldr, "lc": ch[ldr], "lt": "TAVAN" if at_ceil else "",
                            "cr": _r(cr, 2), "lag": _r(lag, 2), "netp": (X["PARA"].get(s) or {}).get("netp"), "sc": round(st * 100)})
                rows.append(row)
                self._sigset(s, 24, st, f"lider {ldr} %{ch[ldr]:+.1f}, korelasyon {cr:.2f}, %{lag:.1f} geride")
        self._out(24, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("sec", "Sektör", "txt"),
                       C("ldr", "Lider", "sym"), C("lc", "Lider %", "chg"), C("lt", "", "txt"), C("cr", "60g korelasyon", "num"),
                       C("lag", "Gecikme (puan)", "num"), C("netp", "Net akış %", "chg"), C("sc", "Skor", "score")], rows,
                  note="Sektör lideri bugün ≥%5 veya tavanda; rakip = aynı sektör endeksinde, lider ile 60 günlük günlük getiri korelasyonu "
                       "≥0,45 ve bugünkü getirisi liderin yarısından az olan hisse. 'Aynı desen' korelasyonla yaklaşık ölçülür.", sort="sc")

    def _f25(self, X):
        rows = []
        m = X.get("msec", X["sec"]) // 60
        for s, L in list(self.live.s.items()):
            q = X["Q"].get(s)
            av = self.bars.avg_vol(s, 20)
            if not q or not av or len(L.mins) < 10:
                continue
            per = av / 480
            out = {}
            ok = True
            for w in (1, 5, 15, 60):
                ks = [k for k in L.mins if m - w < k <= m]
                v = sum(L.mins[k][0] for k in ks)
                prev = [k for k in L.mins if k <= m - w]
                p0 = L.mins[max(prev)][2] if prev else None
                pr = (q["last"] / p0 - 1) * 100 if p0 else None
                rv = v / (per * w) if per else 0
                out[w] = (rv, pr)
                if rv < 1.5 or pr is None or pr <= 0:
                    ok = False
            al = sum(1 for w in out if out[w][0] >= 1.5 and (out[w][1] or 0) > 0)
            acc = (out[5][1] or 0) / 5 > (out[15][1] or 0) / 15 > (out[60][1] or 0) / 60 > 0 if all(out[w][1] is not None for w in (5, 15, 60)) else False
            if al < 2:
                continue
            st = al / 4 * (1 if acc else 0.75)
            row = self._base(s, X)
            for w in (1, 5, 15, 60):
                row[f"rv{w}"] = _r(out[w][0], 1); row[f"p{w}"] = _r(out[w][1], 2)
            row.update({"al": al, "acc": "HIZLANIYOR" if acc else "", "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 25, st, f"{al}/4 zaman diliminde RVOL+fiyat uyumlu" + (", hızlanıyor" if acc else ""))
        self._out(25, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("rv1", "RVOL 1dk", "num"), C("p1", "1dk %", "chg"),
                       C("rv5", "RVOL 5dk", "num"), C("p5", "5dk %", "chg"), C("rv15", "RVOL 15dk", "num"), C("p15", "15dk %", "chg"),
                       C("rv60", "RVOL 60dk", "num"), C("p60", "60dk %", "chg"), C("al", "Uyum /4", "num"), C("acc", "", "txt"),
                       C("sc", "Skor", "score")], rows,
                  note="RVOL = pencere hacmi / (20g ortalama günlük hacim ÷ 480 dk × pencere). Uyum = RVOL ≥1,5 ve fiyat pozitif. Hızlanıyor = "
                       "dakika başı getiri 5dk > 15dk > 60dk. Seans dışında son pencereler boştur.", sort="sc")

    def _f26(self, X):
        rows = []
        for s, q in X["Q"].items():
            b = self.bars.get(s)
            if len(b) < 140:
                continue
            cs = [x["c"] for x in b]
            ck = (s, len(b), b[-1]["d"])
            bws = self._bwcache.get(ck) if hasattr(self, "_bwcache") else None
            if bws is None:
                if not hasattr(self, "_bwcache"):
                    self._bwcache = {}
                bws = []
                for i in range(len(cs) - 120, len(cs)):
                    w = cs[i - 19:i + 1]
                    mu = sum(w) / 20
                    sd = math.sqrt(sum((x - mu) ** 2 for x in w) / 20)
                    bws.append(4 * sd / mu if mu else 0)
                self._bwcache[ck] = bws
            cur = bws[-1]
            pct = sum(1 for x in bws if x <= cur) / len(bws) * 100
            tr = [max(b[i]["h"], b[i - 1]["c"]) - min(b[i]["l"], b[i - 1]["c"]) for i in range(len(b) - 14, len(b))]
            atr = sum(tr) / 14 / cs[-1] * 100
            w20 = cs[-20:]
            mu = sum(w20) / 20; sd = math.sqrt(sum((x - mu) ** 2 for x in w20) / 20)
            up = mu + 2 * sd
            hi20 = max(x["h"] for x in b[-20:])
            rv = self._rvol(s, X)
            brk = q["last"] > max(up, hi20 * 0.999)
            if pct > 25 and not brk:
                continue
            if pct > 40:
                continue
            st = _clip((25 - pct) / 20 + 0.3) * (1.0 if brk and (rv or 0) >= 1.5 else 0.3)
            row = self._base(s, X)
            row.update({"bw": _r(cur * 100, 2), "pct": _r(pct, 0), "atr": _r(atr, 2), "up": _r(up, 2), "hi": hi20, "rv": _r(rv, 2),
                        "st": "KIRILIM" if brk and (rv or 0) >= 1.5 else "kırılım (hacimsiz)" if brk else "SIKIŞMA", "sc": round(st * 100)})
            rows.append(row)
            self._sigset(s, 26, st, f"sıkışma (bant %{pct:.0f}. yüzdelik)" + (" + hacimli kırılım" if brk and (rv or 0) >= 1.5 else ""))
        self._out(26, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("bw", "Bollinger genişlik %", "num"),
                       C("pct", "120g yüzdelik", "num"), C("atr", "ATR14 %", "num"), C("up", "Üst bant", "px"), C("hi", "20g yüksek", "px"),
                       C("rv", "RVOL ×", "num"), C("st", "Durum", "txt"), C("sc", "Skor", "score")], rows,
                  note="Bollinger (20, 2σ) bant genişliğinin son 120 gündeki yüzdeliği ≤25 → sıkışma. Kırılım = fiyat üst bant ve 20g yüksek "
                       "üstünde; hacimli = öngörülen RVOL ≥1,5. İş Yatırım günlük kapanışlarından.", sort="sc")

    def _f27(self, X):
        rows = []
        for s, q in X["Q"].items():
            p = X["PARA"].get(s) or {}
            c = p.get("c")
            r5 = self._ret(s, 5, X)
            ap = self.akdp.get(s) or {}
            w = ap.get("w") or {}
            wv = (w.get("tot") or 0) / 2
            wtop = sum(x[1] for x in (w.get("b") or [])[:5]) / wv * 100 if wv else None
            a = (c is not None and c < 0 and (p.get("netp") or 0) >= 5 and (p.get("rec_tl") or 0) >= 2e6)
            b_ = (r5 is not None and r5 < -3 and (wtop or 0) >= 15)
            if not (a or b_):
                continue
            st = (_clip((p.get("netp") or 0) / 30) * _clip(-(c or 0) / 3 + 0.2) if a else 0) * 0.6 + (_clip((wtop or 0) / 30) * _clip(-(r5 or 0) / 8) if b_ else 0) * 0.4
            row = self._base(s, X)
            row.update({"netp": p.get("netp"), "net": p.get("net"), "r5": _r(r5, 2), "wtop": _r(wtop, 1),
                        "typ": "Bugün + 5 gün" if a and b_ else "Bugün" if a else "5 gün", "sc": round(_clip(st) * 100)})
            rows.append(row)
            self._sigset(s, 27, st, f"fiyat düşerken net akış %{p.get('netp') or 0:+.0f}")
        self._out(27, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("netp", "Net akış %", "chg"),
                       C("net", "Net ₺", "tl"), C("r5", "5g getiri %", "chg"), C("wtop", "Haftalık ilk 5 net alım payı %", "num"),
                       C("typ", "Diverjans", "txt"), C("sc", "Skor", "score")], rows,
                  note="Bugün: fiyat düşüyor ama agresif net para girişi ≥%5 (işlem kaydı). 5 gün: 5 günlük getiri ≤−%3 iken haftalık AKD'de ilk 5 "
                       "net alıcının hacim payı ≥%15. Sezgisel.", sort="sc")

    def _f28(self, X):
        M = self.tavan_model or {}
        cont = M.get("cont") or {}
        rows = []
        for s, q in X["Q"].items():
            if not q.get("ceiling") or q["last"] < q["ceiling"] - 1e-9:
                continue
            b = self.bars.get(s)
            stk = 1
            for x in reversed(b):
                if x.get("pc") and x["c"] / x["pc"] - 1 >= 0.095 and x["c"] >= x["h"] * 0.997:
                    stk += 1
                else:
                    break
            rv = self._rvol(s, X) or 0
            vb = 0 if rv < 1 else 1 if rv < 3 else 2
            e = cont.get(f"{min(stk, 3)}_{vb}") or [0, 0, 0, 0]
            ea = cont.get("0_0") or [0, 0, 0, 0]
            use = e if e[0] >= 15 else ea
            pu = use[1] / use[0] if use[0] else None
            pt = use[2] / use[0] if use[0] else None
            lock = ((self._sig_new.get(s) or {}).get(2) or (0,))[0]
            adj = _clip(pu * (0.75 + 0.5 * lock)) if pu is not None else None
            row = self._base(s, X)
            row.update({"stk": stk, "rv": _r(rv, 2), "lock": round(lock * 100), "bn": use[0], "pu": _r(pu * 100 if pu is not None else None, 0),
                        "pt": _r(pt * 100 if pt is not None else None, 0), "mr": _r(use[3] / use[0] * 100 if use[0] else None, 2),
                        "adj": _r(adj * 100 if adj is not None else None, 0), "bk": "kova" if use is e else "genel"})
            rows.append(row)
        self._out(28, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("stk", "Ardışık tavan", "num"),
                       C("rv", "RVOL ×", "num"), C("lock", "Kilit gücü", "score"), C("bn", "Geçmiş örnek", "num"),
                       C("pu", "Ertesi gün + %", "num"), C("pt", "Ertesi gün tavan %", "num"), C("mr", "Ertesi gün ort. %", "chg"),
                       C("adj", "Kilitle düzeltilmiş + %", "num"), C("bk", "Oran", "txt")], rows,
                  note=f"Taban oranlar: {M.get('stocks', 0)} hissenin ~1 yıllık barlarındaki tavan kapanışları, ardışık tavan sayısı (1/2/3+) ve hacim "
                       "(RVOL <1 / 1–3 / >3) kovalarına göre (örnek <15 ise genel oran). Kilit düzeltmesi sezgisel (×0,75–1,25). "
                       "Gün içi kuyruk geçmişi henüz yok; biriktiriliyor.", sort="adj", status="kısmi")


    # ================================================ PİYASA GENELİ (v1.21) ==
    def _mk_kademe(self, X) -> None:
        f = self.feed
        today = _now().date().isoformat()          # ideal_feed.levels tarih biçimi: YYYY-MM-DD
        with f._lock:
            lv = {s: (v["rows"], v["ts"]) for s, v in f.levels.items() if v.get("date") in (today, _today()) and s in X["Q"]}
        rows = []
        T = {"b": 0.0, "sl": 0.0, "btl": 0.0, "stl": 0.0, "n": 0}
        now = time.time()
        for s in X["Q"]:
            row = self._base(s, X)
            q = X["Q"][s]
            ent = lv.get(s)
            if ent:
                R, ts = ent
                b = sl = btl = stl = tot = ttl = 0.0
                poc = None; pl = -1
                for r in R:
                    lot = r["lot"] or 0
                    bl = lot * (r["buy_pct"] or 0) / 100; sll = lot * (r["sell_pct"] or 0) / 100
                    b += bl; sl += sll; btl += bl * r["price"]; stl += sll * r["price"]
                    tot += lot; ttl += lot * r["price"]
                    if lot > pl:
                        pl = lot; poc = r["price"]
                ba = btl / b if b else None; sa = stl / sl if sl else None
                net = b - sl
                row.update({"bl": round(b), "sl": round(sl), "net": round(net), "netp": _r(net / (b + sl) * 100, 2) if (b + sl) else None,
                            "ba": _r(ba, 4), "sa": _r(sa, 4), "df": _r(sa - ba, 4) if (ba and sa) else None,
                            "dfp": _r((sa / ba - 1) * 100, 2) if (ba and sa) else None,
                            "lf": round(net), "lfp": _r(net / sl * 100, 1) if sl else None,
                            "aort": _r(ttl / tot, 4) if tot else q.get("vwap"), "poc": poc, "age": round((now - ts) / 60),
                            "nlv": len(R), "t": q.get("turnover"), "side": "alıcı" if net > 0 else "satıcı" if net < 0 else ""})
                T["b"] += b; T["sl"] += sl; T["btl"] += btl; T["stl"] += stl; T["n"] += 1
            else:
                row.update({"aort": q.get("vwap"), "t": q.get("turnover"), "side": ""})
            rows.append(row)
        rows.sort(key=lambda r: -(r.get("t") or 0))
        nb, ns = T["b"], T["sl"]
        tot_row = {"s": "TOPLAM", "n": f"{T['n']} hisse", "bl": round(nb), "sl": round(ns), "net": round(nb - ns),
                   "netp": _r((nb - ns) / (nb + ns) * 100, 2) if (nb + ns) else None, "lf": round(nb - ns),
                   "lfp": _r((nb - ns) / ns * 100, 1) if ns else None,
                   "t": sum((r.get("t") or 0) for r in rows), "total": True,
                   "btl": round(T["btl"]), "stl": round(T["stl"])}
        self._res_new["kademe"] = {
            "fid": "kademe", "title": "Kademe Analizi (tüm hisseler)",
            "desc": "Y38 fiyat bazında gerçek alış/satış lotları — tüm BIST payları tek tabloda.",
            "cols": [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("bl", "Alış lot", "lot"),
                     C("sl", "Satış lot", "lot"), C("net", "Net lot", "lot"), C("netp", "Net % (lot)", "chg"),
                     C("ba", "Alış ort.", "px"), C("sa", "Satış ort.", "px"), C("df", "Ort. farkı ₺", "num"),
                     C("dfp", "Ort. farkı %", "chg"), C("lf", "Alış−Satış lot", "lot"), C("lfp", "Alış−Satış %", "chg"),
                     C("aort", "AORT", "px"), C("poc", "POC", "px"), C("t", "Hacim ₺", "tl"), C("age", "Y38 yaşı dk", "num")],
            "rows": rows, "total": tot_row, "count": len(rows), "updated": _now().strftime("%H:%M:%S"), "status": "tam",
            "note": "Kaynak: İdealData Y38 (fiyat kademesi başına toplam lot ve alış/satış yüzdesi) — tarayıcı tüm hisseleri sırayla günceller; "
                    "'Y38 yaşı' son güncellemeden beri dakika. Alış/Satış ort. = kademe fiyatlarının alış/satış lotlarıyla ağırlıklı ortalaması. "
                    "Ort. farkı = satış ort. − alış ort. Alış−Satış % = net lot / satış lotu. AORT = tüm kademelerin hacim ağırlıklı ortalaması; "
                    "POC = en çok işlem gören fiyat."}

    @staticmethod
    def _ema(xs: list, n: int) -> list:
        k = 2 / (n + 1); out = []; e = None
        for x in xs:
            e = x if e is None else x * k + e * (1 - k)
            out.append(e)
        return out

    @staticmethod
    def _rsi(cs: list, n: int = 14) -> float | None:
        if len(cs) < n + 2:
            return None
        g = l = 0.0
        for i in range(1, n + 1):
            d = cs[i] - cs[i - 1]
            g += max(d, 0); l += max(-d, 0)
        g /= n; l /= n
        for i in range(n + 1, len(cs)):
            d = cs[i] - cs[i - 1]
            g = (g * (n - 1) + max(d, 0)) / n; l = (l * (n - 1) + max(-d, 0)) / n
        return 100.0 if l == 0 else 100 - 100 / (1 + g / l)

    def _mk_teknik(self, X) -> None:
        kd = {r["s"]: r for r in (self._res_new.get("kademe") or {}).get("rows", [])}
        m = X["sec"] // 60
        rows = []
        cnt = collections.Counter()
        m = X.get("msec", X["sec"]) // 60
        for s, q in X["Q"].items():
            row = self._base(s, X)
            b = self.bars.get(s)
            last = q["last"]
            cs = [x["c"] for x in b] + [last]
            rsi = self._rsi(cs[-120:]) if len(cs) > 20 else None
            macd = sig = hist = None; mst = ""
            if len(cs) >= 40:
                e12, e26 = self._ema(cs[-200:], 12), self._ema(cs[-200:], 26)
                ml = [a - c for a, c in zip(e12, e26)]
                sl = self._ema(ml, 9)
                macd, sig = ml[-1], sl[-1]; hist = macd - sig
                ph = ml[-2] - sl[-2]
                mst = "AL kesişim" if hist > 0 >= ph else "SAT kesişim" if hist < 0 <= ph else ("pozitif" if hist > 0 else "negatif")
            sma20 = sum(cs[-20:]) / 20 if len(cs) >= 20 else None
            sma50 = sum(cs[-50:]) / 50 if len(cs) >= 50 else None
            trend = "—"
            if sma20 and sma50:
                trend = "Yükseliş" if last > sma20 > sma50 else "Düşüş" if last < sma20 < sma50 else "Yatay"
            av20 = self.bars.avg_vol(s, 20); av10 = self.bars.avg_vol(s, 10)
            pv = self._proj_vol(s, X)
            rv = pv / av20 if av20 else None; rv10 = pv / av10 if av10 else None
            vw = q.get("vwap"); vwd = (last / vw - 1) * 100 if vw else None
            k = kd.get(s) or {}
            dom = (k["bl"] / (k["bl"] + k["sl"]) * 100) if (k.get("bl") is not None and (k["bl"] + k["sl"]) > 0) else None
            L = self.live.s.get(s)
            up = dn = 0
            if L and L.mins:
                for w in (5, 15, 60):
                    prev = [kk for kk in L.mins if kk <= m - w]
                    if prev:
                        p0 = L.mins[max(prev)][2]
                        up += last > p0; dn += last < p0
            chg = row["c"] or 0
            rvok = (rv or 0) >= 1.2 or (rv10 or 0) >= 1.2
            v = "TUT"; strong = False
            if (dom is None or dom >= 55) and chg > 0 and rvok and up >= dn:
                v = "AL"; strong = (dom is None or dom >= 62) and chg > 1 and (rv or 0) >= 1.5
            elif (dom is None or dom <= 45) and chg < 0 and (rvok or chg <= -2) and dn >= up:
                v = "SAT"; strong = (dom is None or dom <= 38) and chg < -1 and (rv or 0) >= 1.5
            sc = 50.0
            if dom is not None: sc += (dom - 50) * 0.8
            sc += _clip(chg, -5, 5) * 2.5
            if rsi is not None: sc += (rsi - 50) * 0.25
            sc += {"Yükseliş": 8, "Düşüş": -8}.get(trend, 0)
            if hist is not None: sc += 5 if hist > 0 else -5
            if vwd is not None: sc += _clip(vwd, -3, 3) * 1.5
            sc = _clip(sc, 0, 100)
            # basit işlem planı (ATR14 + VWAP/POC)
            plan = {}
            if len(b) >= 15 and v != "TUT":
                tr = [max(b[i]["h"], b[i - 1]["c"]) - min(b[i]["l"], b[i - 1]["c"]) for i in range(len(b) - 14, len(b))]
                atr = sum(tr) / 14
                tk = _tick_size(last)
                rd = lambda x: round(round(x / tk) * tk, 4)
                poc = k.get("poc")
                if v == "AL":
                    ent = last
                    sup = [x for x in (vw, poc) if x and x < ent]
                    stop = max(ent - 1.5 * atr, (max(sup) - 0.25 * atr) if sup else ent - 1.0 * atr)
                    stop = min(stop, ent - 0.5 * atr)
                    risk = ent - stop
                    cap = q.get("ceiling_next") or q.get("ceiling") or 1e18   # seans dışı: ertesi gün tavanı
                    t1, t2 = min(ent + 1.5 * risk, cap), min(ent + 2.5 * risk, cap)
                else:
                    ent = last
                    res_ = [x for x in (vw, poc) if x and x > ent]
                    stop = min(ent + 1.5 * atr, (min(res_) + 0.25 * atr) if res_ else ent + 1.0 * atr)
                    stop = max(stop, ent + 0.5 * atr)
                    risk = stop - ent
                    cap = q.get("floor_next") or q.get("floor") or 0
                    t1, t2 = max(ent - 1.5 * risk, cap), max(ent - 2.5 * risk, cap)
                rr = abs(t1 - ent) / risk if risk else None
                if abs(t1 - ent) < 1e-9:
                    rr = None
                plan = {"dir": "LONG" if v == "AL" else "SHORT", "ent": rd(ent), "stop": rd(stop), "tp1": rd(t1), "tp2": rd(t2),
                        "rr": _r(rr, 2), "risk": _r(risk / ent * 100, 2)}
            vv = ("GÜÇLÜ " if strong else "") + v
            cnt[v] += 1
            row.update({"v": vv, "vk": v, "sc": round(sc), "rv": _r(rv, 2), "rv10": _r(rv10, 2), "vwd": _r(vwd, 2), "trend": trend,
                        "rsi": _r(rsi, 1), "macd": _r(hist, 4), "mst": mst, "dom": _r(dom, 1), "tf": f"{up}↑ {dn}↓" if (up or dn) else "—",
                        "t": q.get("turnover"), **plan,
                        "plan": ((f"{plan['dir']} {plan['ent']:g} · S {plan['stop']:g} · TP1 {plan['tp1']:g} · TP2 {plan['tp2']:g}" if plan.get("rr") else
                                  f"{'TAVANDA' if v == 'AL' else 'TABANDA'} — hedef alanı yok") if plan else "BEKLE")})
            rows.append(row)
        rows.sort(key=lambda r: -(r.get("t") or 0))
        self._res_new["teknik"] = {
            "fid": "teknik", "title": "Teknik Sinyaller (tüm hisseler)",
            "desc": "Tüm BIST payları için AL / SAT / TUT, skor, RVOL, VWAP, trend, RSI, MACD ve işlem planı özeti.",
            "cols": [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("v", "Sinyal", "verdict"),
                     C("sc", "Skor", "score"), C("rv", "RVOL", "num"), C("rv10", "RVOL10", "num"), C("vwd", "VWAP uzaklık %", "chg"),
                     C("trend", "Trend", "txt"), C("rsi", "RSI14", "num"), C("mst", "MACD", "txt"), C("dom", "Alış hakimiyeti %", "num"),
                     C("tf", "TF (5/15/60dk)", "txt"), C("ent", "Giriş", "px"), C("stop", "Stop", "px"), C("tp1", "TP1", "px"),
                     C("tp2", "TP2", "px"), C("rr", "R:R", "num"), C("t", "Hacim ₺", "tl")],
            "rows": rows, "counts": dict(cnt), "count": len(rows), "updated": _now().strftime("%H:%M:%S"), "status": "tam",
            "note": "AL/SAT/TUT, hisse sayfasındaki model kurallarıyla aynı eşikler (alış hakimiyeti Y38 ≥%55, değişim, RVOL/RVOL10 ≥1,2, "
                    "çoklu zaman dilimi) ama piyasa geneli için canlı veriden hızlı hesaplanır. RSI14 / MACD(12,26,9) / SMA20-50 trendi İş Yatırım "
                    "günlük kapanışları + bugünkü son fiyattan. İşlem planı basitleştirilmiştir: giriş = son fiyat, stop = VWAP/POC destek "
                    "(veya 1–1,5 ATR14), TP1 = 1,5R, TP2 = 2,5R, tavan/taban sınırlı. Ayrıntılı plan hisse sayfasında. Yatırım tavsiyesi değildir."}

    # ----------------------------------------------------- 30 zaman çizelgesi
    PH = {"T": "toplama", "I": "itme", "D": "dağıtım", "N": "nötr"}

    def _phase_day(self, x: dict, av: float, akd: dict | None) -> tuple[str, str]:
        r = x["c"] / x["pc"] - 1 if x.get("pc") else 0
        rng = x["h"] - x["l"]
        clv = (((x["c"] - x["l"]) - (x["h"] - x["c"])) / rng) if rng > 0 else 0
        vr = x["v"] / av if av else 1
        ns = None
        if akd and akd.get("tot"):
            vol = akd["tot"] / 2
            ns = sum(y[1] for y in (akd.get("b") or [])[:3]) / vol if vol else None
        if r >= 0.03 and vr >= 1.3:
            return "I", f"%{r*100:+.1f}, hacim {vr:.1f}×"
        if (r <= -0.02 and vr >= 1.2) or (vr >= 1.5 and clv <= -0.3):
            return "D", f"%{r*100:+.1f}, hacim {vr:.1f}×, kapanış {'zayıf' if clv < 0 else 'orta'}"
        if abs(r) < 0.025 and ((ns is not None and ns >= 0.25) or (vr >= 0.9 and clv >= 0.25)):
            return "T", f"%{r*100:+.1f}, hacim {vr:.1f}×" + (f", ilk 3 net pay %{ns*100:.0f} (AKD)" if ns is not None else ", güçlü kapanış")
        return "N", f"%{r*100:+.1f}, hacim {vr:.1f}×"

    def zaman(self, s: str, X: dict | None = None, n: int = 30) -> dict:
        s = s.upper()
        b = self.bars.get(s)
        days = []
        akd = self.akdday.get(s) or {}
        for i in range(max(21, len(b) - n), len(b)):
            x = b[i]
            av = sum(y["v"] for y in b[i - 20:i]) / 20
            k = x["d"].replace("-", "")
            ph, why = self._phase_day(x, av, akd.get(k))
            days.append({"d": x["d"], "ph": ph, "phn": self.PH[ph], "why": why, "c": x["c"],
                         "r": _r((x["c"] / x["pc"] - 1) * 100 if x.get("pc") else None, 2), "vr": _r(x["v"] / av if av else None, 2),
                         "akd": bool(akd.get(k))})
        # bugün (canlı)
        if X is None:
            X = getattr(self, "_lastX", None)
        if X and s in X["Q"] and len(b) > 21:
            tb = self._today_bar(s, X)
            if tb:
                av = sum(y["v"] for y in b[-20:]) / 20
                ph, why = self._phase_day(tb, av, None)
                pa = (X["PARA"].get(s) or {}).get("netp")
                if ph == "N" and pa is not None and pa >= 15 and abs((tb["c"] / tb["pc"] - 1) if tb.get("pc") else 0) < 0.025:
                    ph, why = "T", why + f", net akış %{pa:+.0f}"
                days.append({"d": _now().strftime("%Y-%m-%d"), "ph": ph, "phn": self.PH[ph], "why": why + " (canlı)", "c": tb["c"],
                             "r": _r((tb["c"] / tb["pc"] - 1) * 100 if tb.get("pc") else None, 2), "vr": _r(tb["v"] / av if av else None, 2),
                             "akd": False, "live": True})
        cur = self._cur_phase(days)
        return {"symbol": s, "days": days, "current": cur, "akd_days": len(akd),
                "note": "Evreler sezgisel: İTME = %3+ yükseliş ve hacim ≥1,3×; DAĞITIM = %2+ düşüş hacimli veya hacimli zayıf kapanış; "
                        "TOPLAMA = dar hareket (<%2,5) ve güçlü kapanış/normal üstü hacim ya da AKD'de ilk 3 alıcının net payı ≥%25. "
                        f"AKD destekli gün: {len(akd)}."}

    def _cur_phase(self, days: list) -> dict:
        last = days[-10:]
        if not last:
            return {"ph": "N", "phn": "nötr", "conf": 0, "streak": 0}
        w = collections.Counter()
        for i, d in enumerate(last):
            w[d["ph"]] += 1 + i / len(last)
        ph = last[-1]["ph"]
        streak = 0
        for d in reversed(days):
            if d["ph"] == ph:
                streak += 1
            else:
                break
        est = ph if ph != "N" else (max((k for k in w if k != "N"), key=lambda k: w[k], default="N") if sum(v for k, v in w.items() if k != "N") >= 3 else "N")
        conf = w[est] / sum(w.values()) if w else 0
        return {"ph": est, "phn": self.PH[est], "conf": round(conf * 100), "streak": streak,
                "strip": "".join(d["ph"] for d in days[-15:])}

    def _f30(self, X):
        self._lastX = X
        rows = []
        for s in X["Q"]:
            if len(self.bars.get(s)) < 40:
                continue
            z = self.zaman(s, X, n=20)
            cur = z["current"]
            dd = z["days"]
            row = self._base(s, X)
            row.update({"ph": cur["phn"].upper(), "conf": cur["conf"], "streak": cur["streak"], "strip": cur.get("strip"),
                        "nT": sum(1 for d in dd if d["ph"] == "T"), "nI": sum(1 for d in dd if d["ph"] == "I"),
                        "nD": sum(1 for d in dd if d["ph"] == "D"), "akd": z["akd_days"]})
            rows.append(row)
            if cur["ph"] == "T":
                self._sigset(s, 30, 0.0, "")
        self._out(30, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("ph", "Mevcut evre", "txt"),
                       C("conf", "Güven %", "num"), C("streak", "Süre (gün)", "num"), C("strip", "Son 15 gün (T/İ/D/N)", "strip"),
                       C("nT", "Toplama g.", "num"), C("nI", "İtme g.", "num"), C("nD", "Dağıtım g.", "num"),
                       C("akd", "AKD gün", "num")], rows,
                  note="Satıra dokunun → hissenin OPERASYON sekmesinde gün gün zaman çizelgesi. T=toplama, İ=itme, D=dağıtım, N=nötr; son harf "
                       "bugün (canlı). Barlar İş Yatırım; AKD destekli günler yavaş kuyrukla doluyor.", sort="nT",
                  status="kısmi" if sum(len(v) for v in self.akdday.values()) < 500 else "tam")

    # ---------------------------------------------------------- 29 skor --
    def _f29(self, X):
        rows = []
        sc = {}
        for s, d in self._sig_new.items():
            if s not in X["Q"]:
                continue
            parts = []
            tot = 0.0
            for fid, (st, txt) in d.items():
                w = FEATURES[fid][2]
                if not w:
                    continue
                pts = w * st
                tot += pts
                parts.append({"f": fid, "t": FEATURES[fid][0], "w": w, "st": round(st * 100), "pts": round(pts, 1), "txt": txt})
            if tot < 3:
                continue
            parts.sort(key=lambda p: -p["pts"])
            score = 100.0 * (1.0 - math.exp(-tot / 35.0))   # doygun ölçek: 25 ham → 51, 40 → 68, 60 → 82
            row = self._base(s, X)
            row.update({"score": round(score), "raw": round(tot, 1), "nsig": len(parts), "top": " · ".join(p["t"] for p in parts[:3]),
                        "parts": parts, "t": (X["Q"][s] or {}).get("turnover")})
            rows.append(row)
            sc[s] = {"score": round(score), "raw": round(tot, 1), "parts": parts}
        self.score = sc
        maxp = sum(v[2] for v in FEATURES.values())
        self._out(29, [C("s", "Hisse", "sym"), C("p", "Fiyat", "px"), C("c", "Gün %", "chg"), C("score", "Operasyon skoru", "score"),
                       C("raw", "Ham puan", "num"), C("nsig", "Sinyal sayısı", "num"), C("top", "Başlıca sinyaller", "txt"), C("t", "Hacim ₺", "tl")], rows,
                  note=f"Ham puan = Σ (özellik ağırlığı × sinyal gücü 0–1) (ağırlık toplamı {maxp}); Skor = 100 × (1 − e^(−ham/35)) "
                       "(ör. ham 25 → 51, 40 → 68, 60 → 82). ▸ ile puanların "
                       "kaynağı görünür. Sezgisel bir sıralamadır; yatırım tavsiyesi değildir. ≥65 skor ve +10 artışlarda 'Operasyon skoru' "
                       "bildirimi.", sort="score", hist=f"veri biriktiriliyor ({self.hist_days()} gün)",
                  extra={"weights": {str(k): v[2] for k, v in FEATURES.items()}})

    # ------------------------------------------------------------ alerts --
    def _alerts(self, first: bool) -> None:
        now = time.time()
        hub = self.hub
        sec = _sec_now()
        live_sess = _now().weekday() < 5 and 35400 <= sec <= 66000
        for s, e in self.score.items():
            v = e["score"]
            prev = self.score_alert.get(s)
            if v >= 65 and (prev is None or prev[0] != _today() or v >= prev[1] + 10):
                self.score_alert[s] = (_today(), v)
                if not hasattr(self, "_srate"):
                    self._srate = collections.deque()
                while self._srate and now - self._srate[0] > 3600:
                    self._srate.popleft()
                if not first and live_sess and len(self._srate) < 12:
                    self._srate.append(now)
                    txt = " · ".join(f"{p['t']} +{p['pts']:.0f}" for p in e["parts"][:4])
                    hub._emit("olay", "op_skor", s, f"🎯 {s} operasyon skoru {v}", txt, {"score": v, "f": 29})
        # özellik uyarıları: en güçlüler önce; özellik başına saatte en çok 4, toplam saatte 30 (bildirim seli olmasın)
        if not hasattr(self, "_rate"):
            self._rate = collections.deque()
        while self._rate and now - self._rate[0][0] > 3600:
            self._rate.popleft()
        per = collections.Counter(f for _, f in self._rate)
        cand = sorted(((st, s, fid, txt) for s, d in self.sig.items() for fid, (st, txt) in d.items()
                       if FEATURES[fid][3] and FEATURES[fid][3] != "op_skor" and st >= 0.75), reverse=True)
        for st, s, fid, txt in cand:
            k = (s, fid)
            if now - self.alerted.get(k, 0) < 3600:
                continue
            if not first and (per[fid] >= 4 or len(self._rate) >= 30):
                continue
            self.alerted[k] = now
            if first or not live_sess:
                continue
            per[fid] += 1
            self._rate.append((now, fid))
            hub._emit("olay", FEATURES[fid][3], s, f"🕵 {s} · {FEATURES[fid][0]}", txt, {"f": fid, "st": round(st * 100)})

    # ------------------------------------------------------ persistence --
    def save_daily(self) -> None:
        day = _today()
        if _now().weekday() >= 5:
            return
        X = getattr(self, "_lastX", None)
        if not X:
            return
        akd = {}
        for s, (b, se) in X["AKD"].items():
            akd[s] = {"b": [[r["broker"], r.get("net_lot") or 0, r.get("cost"), r.get("total_lot") or 0] for r in b[:10]],
                      "s": [[r["broker"], r.get("net_lot") or 0, r.get("cost"), r.get("total_lot") or 0] for r in se[:10]],
                      "tot": sum((r.get("total_lot") or 0) for r in b + se)}
        flows = {s: [[r["b"], r["net"], r["ntl"], r["buy"], r["sell"], r["aa"], r["pa"]] for r in L[:8]] for s, L in X["BR"].items()}
        snap = {"day": day, "ts": _now().strftime("%H:%M:%S"),
                "scores": {s: [e["score"], [[p["f"], p["pts"]] for p in e["parts"]]] for s, e in self.score.items()},
                "akd": akd, "flows": flows,
                "spoof": {s: len(L.spoofs) for s, L in self.live.s.items() if L.spoofs},
                "conc": {s: list(d[-1][1:]) for s, d in self.conc.items() if d},
                "phase": {r["s"]: r["ph"] for r in (self.res.get(30) or {}).get("rows", [])}}
        _jsave(OPD / "daily" / f"{day}.json", snap)
        if day not in self.daily_days:
            self.daily_days.append(day)
        self._last_daily_save = time.time()
        if _sec_now() > 65700:
            # bugünün AKD'si günlük geçmişe (yarın için hazır)
            for s, pk in akd.items():
                ent = self.akdday.setdefault(s, {})
                ent[day] = pk
                _jsave(OPD / "akd_day" / f"{s}.json", ent)
            self._final_day = day

    # --------------------------------------------------------------- API --
    def catalog(self) -> dict:
        out = []
        for fid in ORDER:
            t, d, w, nt = FEATURES[fid]
            r = self.res.get(fid) or {}
            out.append({"fid": fid, "title": t, "desc": d, "weight": w, "nt": nt, "count": r.get("count"),
                        "status": r.get("status"), "updated": r.get("updated")})
        return {"features": out, "computed_at": self.computed_at, "hist_days": self.hist_days(), "nt_defaults": NT_DEFAULTS}

    def feature(self, fid, q: str | None = None) -> dict:
        r = self.res.get(fid)
        if not r:
            t, d, w, nt = FEATURES.get(fid, ({"kademe": "Kademe Analizi", "teknik": "Teknik Sinyaller"}.get(fid, "?"), "", 0, None))
            return {"fid": fid, "title": t, "desc": d, "cols": [], "rows": [], "count": 0, "pending": True,
                    "note": "Arka plan hesaplaması henüz tamamlanmadı (ilk tur ~1 dk).", "hist_days": self.hist_days()}
        out = dict(r)
        if q:
            qq = q.upper()
            out["rows"] = [x for x in r["rows"] if qq in str(x.get("s") or "") or qq in _fold(str(x.get("b") or x.get("br") or x.get("a") or ""))]
        out["hist_days"] = self.hist_days()
        out["computed_at"] = self.computed_at
        return out

    def stock(self, sym: str) -> dict:
        s = sym.upper()
        by = (getattr(self, "by_sym", {}) or {}).get(s, {})
        sig = self.sig.get(s, {})
        feats = []
        for fid in ORDER:
            if fid in (29,):
                continue
            row = by.get(fid)
            st = sig.get(fid)
            r = self.res.get(fid) or {}
            feats.append({"fid": fid, "title": FEATURES[fid][0], "w": FEATURES[fid][2], "st": round(st[0] * 100) if st else 0,
                          "txt": st[1] if st else None, "row": row, "cols": r.get("cols"), "status": r.get("status")})
        e = self.score.get(s) or {"score": 0, "parts": []}
        return {"symbol": s, "score": e["score"], "parts": e["parts"], "features": feats, "zaman": self.zaman(s),
                "hist_days": self.hist_days(), "computed_at": self.computed_at}

    def status(self) -> dict:
        return {"computed_at": self.computed_at, "timing": self.timing, "errors": self.errors, "bars": len(self.bars.d),
                "bars_failed": self.bars.failed, "akd_period": len(self.akdp), "takas": len(self.takas),
                "akd_day_syms": len(self.akdday), "akd_day_rows": sum(len(v) for v in self.akdday.values()),
                "akd_week_syms": len(self.akdweek), "kap": self.kap_status, "queue": self.q.pending(), "queue_paused": self.q.paused,
                "queue_done": dict(self.q.done), "queue_fail": dict(self.q.fail), "queue_err": self.q.last_err,
                "live_syms": len(self.live.s), "live_loops": self.live.loops, "hist_days": self.hist_days(),
                "daily_days": self.daily_days[-30:], "closing_days": sorted(self.closing_hist), "opening_days": sorted(self.opening_hist),
                "tavan_model": {k: (self.tavan_model or {}).get(k) for k in ("n_t", "n_a", "stocks")}}


op = Op()
