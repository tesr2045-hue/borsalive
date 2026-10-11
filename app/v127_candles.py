"""v1.27.0 — MUM FORMASYONLARI dedektörü (son KAPANMIŞ bar ve onunla biten çok barlı formasyonlar).

Bağlam: ATR14, ortalama gövde (10 bar), trend = EMA20'ye göre konum + 5 bar eğim (|eğim| ≥ 0,5 ATR).
Çekiç ↔ Asılı Adam, Ters Çekiç ↔ Kayan Yıldız gibi aynı şekilli çiftler trend bağlamıyla ayrılır.
Gürültü filtresi: son bar aralığı ≥ 3 fiyat adımı ve ATR ≥ 3 adım; tavan/taban kilitli (aralığı 0) barlar atlanır.
"""
from __future__ import annotations

import numpy as np

REL_TXT = {1: "Düşük", 2: "Orta", 3: "Yüksek"}


def tick_of(p: float) -> float:
    if p < 20: return 0.01
    if p < 50: return 0.02
    if p < 100: return 0.05
    if p < 250: return 0.10
    if p < 500: return 0.25
    if p < 1000: return 0.50
    if p < 2500: return 1.0
    return 2.5


def ema(a, n):
    out = np.empty(len(a))
    k = 2.0 / (n + 1)
    m = a[0] if len(a) else 0.0
    for i, x in enumerate(a):
        m = x if i == 0 else m + k * (x - m)
        out[i] = m
    return out


def atr(h, l, c, n=14):
    tr = np.empty(len(c))
    for i in range(len(c)):
        tr[i] = h[i] - l[i] if i == 0 else max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    out = np.empty(len(c))
    m = tr[0] if len(tr) else 0.0
    for i in range(len(tr)):
        m = tr[i] if i == 0 else (m * (n - 1) + tr[i]) / n
        out[i] = m
    return out


def fp(x):
    """Fiyat biçimi (TR)."""
    if x is None:
        return "—"
    d = 2 if abs(x) < 1000 else 1
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# --------------------------------------------------------------------------- formasyon tanımları
# key: (Türkçe ad, İngilizce, yön U/D/N, tip dönüş/devam/kararsızlık, güven 1-3, bar sayısı, anlam)
P = {
    "doji": ("Doji", "Doji", "N", "kararsızlık", 1, 1, "Açılış ve kapanış neredeyse aynı; alıcı ve satıcı dengede, mevcut trendde yorgunluk olabilir."),
    "dragonfly_doji": ("Yusufçuk Doji", "Dragonfly Doji", "U", "dönüş", 2, 1, "Satıcılar fiyatı aşağı çekti ama alıcılar tamamen geri aldı; düşüş sonrası dip sinyali."),
    "gravestone_doji": ("Mezar Taşı Doji", "Gravestone Doji", "D", "dönüş", 2, 1, "Alıcılar fiyatı yukarı taşıdı ama satıcılar tamamen geri itti; yükseliş sonrası tepe sinyali."),
    "long_legged_doji": ("Uzun Bacaklı Doji", "Long-Legged Doji", "N", "kararsızlık", 1, 1, "İki yönde de geniş salınım, kapanış açılışta; güçlü kararsızlık, yön kırılımı beklenir."),
    "hammer": ("Çekiç", "Hammer", "U", "dönüş", 2, 1, "Düşüş trendinde uzun alt gölge: dipten güçlü alım geldi, satış baskısı zayıflıyor."),
    "hanging_man": ("Asılı Adam", "Hanging Man", "D", "dönüş", 1, 1, "Yükseliş trendinde uzun alt gölge: seans içi sert satış görüldü, tepe uyarısı."),
    "inverted_hammer": ("Ters Çekiç", "Inverted Hammer", "U", "dönüş", 1, 1, "Düşüş trendinde uzun üst gölge: alıcılar ilk kez yukarı denedi; teyit gerekir."),
    "shooting_star": ("Kayan Yıldız", "Shooting Star", "D", "dönüş", 2, 1, "Yükseliş trendinde uzun üst gölge: yukarıda satıcılar devreye girdi, tepe sinyali."),
    "marubozu_bull": ("Yükseliş Marubozu", "Bullish Marubozu", "U", "devam", 2, 1, "Gölgesiz uzun beyaz gövde: bar boyunca alıcılar tam hâkim, güçlü talep."),
    "marubozu_bear": ("Düşüş Marubozu", "Bearish Marubozu", "D", "devam", 2, 1, "Gölgesiz uzun siyah gövde: bar boyunca satıcılar tam hâkim, güçlü arz."),
    "spinning_top": ("Topaç", "Spinning Top", "N", "kararsızlık", 1, 1, "Küçük gövde, iki yanda gölge: kararsızlık; trendin gücü azalıyor olabilir."),
    "belt_hold_bull": ("Yükseliş Kuşak Tutma", "Bullish Belt Hold", "U", "dönüş", 2, 1, "Düşüşte dipte açılıp gün boyu yükselen uzun beyaz gövde; dönüş girişimi."),
    "belt_hold_bear": ("Düşüş Kuşak Tutma", "Bearish Belt Hold", "D", "dönüş", 2, 1, "Yükselişte tepede açılıp gün boyu düşen uzun siyah gövde; dönüş uyarısı."),
    "engulfing_bull": ("Yutan Boğa", "Bullish Engulfing", "U", "dönüş", 3, 2, "Beyaz gövde önceki siyah gövdeyi tamamen yuttu: kontrol satıcıdan alıcıya geçti."),
    "engulfing_bear": ("Yutan Ayı", "Bearish Engulfing", "D", "dönüş", 3, 2, "Siyah gövde önceki beyaz gövdeyi tamamen yuttu: kontrol alıcıdan satıcıya geçti."),
    "harami_bull": ("Boğa Harami", "Bullish Harami", "U", "dönüş", 1, 2, "Uzun siyah mumun gövdesi içinde küçük beyaz mum: düşüş ivmesi durdu."),
    "harami_bear": ("Ayı Harami", "Bearish Harami", "D", "dönüş", 1, 2, "Uzun beyaz mumun gövdesi içinde küçük siyah mum: yükseliş ivmesi durdu."),
    "harami_cross_bull": ("Boğa Harami Haç", "Bullish Harami Cross", "U", "dönüş", 2, 2, "Uzun siyah mumun gövdesi içinde doji: satış baskısı belirgin biçimde tükendi."),
    "harami_cross_bear": ("Ayı Harami Haç", "Bearish Harami Cross", "D", "dönüş", 2, 2, "Uzun beyaz mumun gövdesi içinde doji: alım iştahı belirgin biçimde tükendi."),
    "piercing": ("Delici Mum", "Piercing Line", "U", "dönüş", 2, 2, "Aşağı açılan beyaz mum önceki siyah gövdenin yarısının üzerinde kapattı: güçlü dipten dönüş."),
    "dark_cloud": ("Kara Bulut", "Dark Cloud Cover", "D", "dönüş", 2, 2, "Yukarı açılan siyah mum önceki beyaz gövdenin yarısının altında kapattı: tepe uyarısı."),
    "tweezer_bottom": ("Cımbız Dip", "Tweezer Bottom", "U", "dönüş", 1, 2, "İki ardışık mum aynı dipte durdu: o seviyede güçlü destek/alım var."),
    "tweezer_top": ("Cımbız Tepe", "Tweezer Top", "D", "dönüş", 1, 2, "İki ardışık mum aynı tepede durdu: o seviyede güçlü direnç/satış var."),
    "kicker_bull": ("Boğa Tekme", "Bullish Kicker", "U", "dönüş", 3, 2, "Siyah mumdan sonra boşlukla yukarı açılan güçlü beyaz mum: ani ve sert yön değişimi."),
    "kicker_bear": ("Ayı Tekme", "Bearish Kicker", "D", "dönüş", 3, 2, "Beyaz mumdan sonra boşlukla aşağı açılan güçlü siyah mum: ani ve sert yön değişimi."),
    "on_neck": ("Boyun Üstü", "On-Neck", "D", "devam", 1, 2, "Düşüşte aşağı açılan beyaz mum ancak önceki dibe kadar toparlandı: düşüş devam eğilimi."),
    "in_neck": ("Boyun İçi", "In-Neck", "D", "devam", 1, 2, "Düşüşte aşağı açılan beyaz mum önceki kapanışın hemen üstünde kaldı: zayıf tepki, düşüş devam eğilimi."),
    "thrusting": ("İtme", "Thrusting", "D", "devam", 1, 2, "Düşüşte beyaz mum önceki gövdenin yarısına ulaşamadı: tepki yetersiz, düşüş devam edebilir."),
    "matching_low": ("Eşleşen Dip", "Matching Low", "U", "dönüş", 1, 2, "İki siyah mum aynı seviyede kapattı: o fiyatta destek oluştu."),
    "matching_high": ("Eşleşen Tepe", "Matching High", "D", "dönüş", 1, 2, "İki beyaz mum aynı seviyede kapattı: o fiyatta direnç oluştu."),
    "counterattack_bull": ("Boğa Karşı Saldırı", "Bullish Counterattack", "U", "dönüş", 1, 2, "Sert aşağı açılan beyaz mum önceki kapanışa kadar geri aldı: alıcılar karşı saldırıda."),
    "counterattack_bear": ("Ayı Karşı Saldırı", "Bearish Counterattack", "D", "dönüş", 1, 2, "Sert yukarı açılan siyah mum önceki kapanışa kadar geri verdi: satıcılar karşı saldırıda."),
    "morning_star": ("Sabah Yıldızı", "Morning Star", "U", "dönüş", 3, 3, "Uzun siyah mum, küçük gövdeli yıldız ve güçlü beyaz mum: klasik dip dönüşü."),
    "evening_star": ("Akşam Yıldızı", "Evening Star", "D", "dönüş", 3, 3, "Uzun beyaz mum, küçük gövdeli yıldız ve güçlü siyah mum: klasik tepe dönüşü."),
    "morning_doji_star": ("Sabah Doji Yıldızı", "Morning Doji Star", "U", "dönüş", 3, 3, "Sabah yıldızının doji'li hâli: dipte kararsızlıktan alıcı hâkimiyetine geçiş."),
    "evening_doji_star": ("Akşam Doji Yıldızı", "Evening Doji Star", "D", "dönüş", 3, 3, "Akşam yıldızının doji'li hâli: tepede kararsızlıktan satıcı hâkimiyetine geçiş."),
    "abandoned_baby_bull": ("Boğa Terk Edilmiş Bebek", "Bullish Abandoned Baby", "U", "dönüş", 3, 3, "İki yanından boşlukla ayrılmış dipteki doji: nadir ve güçlü dip dönüşü."),
    "abandoned_baby_bear": ("Ayı Terk Edilmiş Bebek", "Bearish Abandoned Baby", "D", "dönüş", 3, 3, "İki yanından boşlukla ayrılmış tepedeki doji: nadir ve güçlü tepe dönüşü."),
    "three_white_soldiers": ("Üç Beyaz Asker", "Three White Soldiers", "U", "dönüş", 3, 3, "Art arda üç güçlü beyaz mum, her biri daha yüksek kapanış: kalıcı alım baskısı."),
    "three_black_crows": ("Üç Kara Karga", "Three Black Crows", "D", "dönüş", 3, 3, "Art arda üç güçlü siyah mum, her biri daha düşük kapanış: kalıcı satış baskısı."),
    "three_inside_up": ("Üçlü İçeriden Yükseliş", "Three Inside Up", "U", "dönüş", 2, 3, "Boğa haramisi, ardından ilk mumun açılışı üzerinde kapanış: teyitli dip dönüşü."),
    "three_inside_down": ("Üçlü İçeriden Düşüş", "Three Inside Down", "D", "dönüş", 2, 3, "Ayı haramisi, ardından ilk mumun açılışı altında kapanış: teyitli tepe dönüşü."),
    "three_outside_up": ("Üçlü Dışarıdan Yükseliş", "Three Outside Up", "U", "dönüş", 3, 3, "Yutan boğa, ardından daha yüksek kapanış: teyitli güçlü dip dönüşü."),
    "three_outside_down": ("Üçlü Dışarıdan Düşüş", "Three Outside Down", "D", "dönüş", 3, 3, "Yutan ayı, ardından daha düşük kapanış: teyitli güçlü tepe dönüşü."),
    "rising_three": ("Yükselen Üç Yöntem", "Rising Three Methods", "U", "devam", 2, 5, "Uzun beyaz mum, aralığı içinde küçük düzeltme mumları ve yeni zirveye kapanış: yükseliş devam."),
    "falling_three": ("Düşen Üç Yöntem", "Falling Three Methods", "D", "devam", 2, 5, "Uzun siyah mum, aralığı içinde küçük tepki mumları ve yeni dibe kapanış: düşüş devam."),
    "tri_star_bull": ("Boğa Üçlü Yıldız", "Bullish Tri-Star", "U", "dönüş", 2, 3, "Düşüşte art arda üç doji, ortadaki en altta: satıcılar tükendi."),
    "tri_star_bear": ("Ayı Üçlü Yıldız", "Bearish Tri-Star", "D", "dönüş", 2, 3, "Yükselişte art arda üç doji, ortadaki en üstte: alıcılar tükendi."),
    "tasuki_up": ("Yukarı Tasuki Boşluğu", "Upside Tasuki Gap", "U", "devam", 1, 3, "Boşluklu yükselişten sonra boşluğu kapatmayan geri çekilme: yükseliş devam eğilimi."),
    "tasuki_down": ("Aşağı Tasuki Boşluğu", "Downside Tasuki Gap", "D", "devam", 1, 3, "Boşluklu düşüşten sonra boşluğu kapatmayan tepki: düşüş devam eğilimi."),
    "advance_block": ("İlerleme Bloğu", "Advance Block", "D", "dönüş", 1, 3, "Üç beyaz mum ama gövdeler küçülüyor, üst gölgeler uzuyor: yükseliş güç kaybediyor."),
    "stick_sandwich": ("Sandviç", "Stick Sandwich", "U", "dönüş", 1, 3, "İki siyah mum aynı kapanışta, aralarında beyaz mum: o seviyede destek."),
    "ladder_bottom": ("Merdiven Dip", "Ladder Bottom", "U", "dönüş", 2, 5, "Art arda düşen siyah mumlardan sonra yukarı açılan güçlü beyaz mum: dip dönüşü."),
}
DIR_TXT = {"U": "YÜKSELİŞ", "D": "DÜŞÜŞ", "N": "KARARSIZ"}


class Ctx:
    def __init__(self, b, n):
        """b: Bars; n: kapanmış bar sayısı (değerlendirilecek son bar = n-1)."""
        self.o, self.h, self.l, self.c, self.v = b.o[:n], b.h[:n], b.l[:n], b.c[:n], b.v[:n]
        self.n = n
        self.i = n - 1
        self.body = np.abs(self.c - self.o)
        self.rng = self.h - self.l
        self.up = self.h - np.maximum(self.o, self.c)
        self.lo = np.minimum(self.o, self.c) - self.l
        self.atr = atr(self.h, self.l, self.c)
        self.ema = ema(self.c, 20)
        self.tick = tick_of(float(self.c[-1]))

    # k = kaç bar geri (0 = son bar)
    def O(self, k): return float(self.o[self.i - k])
    def H(self, k): return float(self.h[self.i - k])
    def L(self, k): return float(self.l[self.i - k])
    def C(self, k): return float(self.c[self.i - k])
    def B(self, k): return float(self.body[self.i - k])
    def R(self, k): return float(self.rng[self.i - k])
    def U(self, k): return float(self.up[self.i - k])
    def W(self, k): return float(self.lo[self.i - k])
    def bull(self, k): return self.c[self.i - k] > self.o[self.i - k]
    def bear(self, k): return self.c[self.i - k] < self.o[self.i - k]

    def avgbody(self, k):
        j = self.i - k
        s = self.body[max(0, j - 10):j]
        s = s[s > 0]
        return max(float(s.mean()) if len(s) else 0.0, self.tick)

    def ATR(self, k=0):
        return max(float(self.atr[self.i - k]), self.tick)

    def trend(self, k):
        """k bar gerideki bara göre trend: +1 yükseliş, -1 düşüş, 0 belirsiz. (eğim, ema farkı) döner."""
        j = self.i - k
        if j < 6:
            return 0, 0.0
        slope = float(self.c[j] - self.c[j - 5])
        a = max(float(self.atr[j]), self.tick)
        above = self.c[j] > self.ema[j]
        if slope >= 0.5 * a and above:
            return 1, slope / max(self.c[j - 5], 1e-9) * 100
        if slope <= -0.5 * a and not above:
            return -1, slope / max(self.c[j - 5], 1e-9) * 100
        return 0, slope / max(self.c[j - 5], 1e-9) * 100

    def doji(self, k): return self.R(k) > 0 and self.B(k) <= 0.1 * self.R(k)
    def long(self, k): return self.B(k) >= max(self.avgbody(k), 0.5 * self.R(k), 2 * self.tick) and self.B(k) >= 0.5 * self.R(k)
    def small(self, k): return self.B(k) <= max(0.5 * self.avgbody(k), self.tick) or self.B(k) <= 0.3 * self.R(k)
    def eq(self, a, b): return abs(a - b) <= max(self.tick, 0.05 * self.ATR())
    def mid(self, k): return (self.O(k) + self.C(k)) / 2


def _tr(t):
    return {1: "yükseliş", -1: "düşüş", 0: "yatay"}[t]


def detect(x: Ctx):
    """Son barla biten tüm mum formasyonları → [(key, nbars, checks[list[str]])]."""
    hits = []
    if x.n < 25:
        return hits
    if x.R(0) < 3 * x.tick - 1e-9 or x.ATR() < 3 * x.tick - 1e-9:
        return hits
    t1, s1 = x.trend(1)
    t2, s2 = x.trend(2)
    t3, s3 = x.trend(3)
    t5, s5 = x.trend(5)
    a = x.ATR()
    pct = lambda v, r: f"%{v / r * 100:.0f}" if r else "—"
    trtxt = lambda t, s: f"Önceki trend {_tr(t)} (5 bar eğim %{s:+.1f}, EMA20 {'üstü' if t > 0 else 'altı' if t < 0 else 'çevresi'})"

    def add(key, nb, checks):
        hits.append((key, nb, checks))

    # ---------------- tek bar
    o, h, l, c, bd, r, up, lo = x.O(0), x.H(0), x.L(0), x.C(0), x.B(0), x.R(0), x.U(0), x.W(0)
    if x.doji(0):
        base = [f"Gövde {fp(bd)} ≤ aralığın %10'u ({fp(0.1 * r)})"]
        if up <= 0.1 * r and lo >= 0.6 * r:
            add("dragonfly_doji", 1, base + [f"Üst gölge {pct(up, r)} ≤ %10", f"Alt gölge {pct(lo, r)} ≥ %60"] + ([trtxt(t1, s1)] if t1 else []))
        elif lo <= 0.1 * r and up >= 0.6 * r:
            add("gravestone_doji", 1, base + [f"Alt gölge {pct(lo, r)} ≤ %10", f"Üst gölge {pct(up, r)} ≥ %60"] + ([trtxt(t1, s1)] if t1 else []))
        elif up >= 0.3 * r and lo >= 0.3 * r and r >= 1.2 * x.ATR(1):
            add("long_legged_doji", 1, base + [f"İki gölge de ≥ %30 (üst {pct(up, r)}, alt {pct(lo, r)})", f"Aralık {fp(r)} ≥ 1,2×ATR ({fp(1.2 * x.ATR(1))})"])
        else:
            add("doji", 1, base)
    else:
        hammer_shape = bd >= 0.1 * r and lo >= 2 * bd and up <= max(0.1 * r, 0.3 * bd) and min(o, c) >= l + 0.6 * r
        inv_shape = bd >= 0.1 * r and up >= 2 * bd and lo <= max(0.1 * r, 0.3 * bd) and max(o, c) <= l + 0.4 * r
        sh = [f"Alt gölge {fp(lo)} = {lo / bd:.1f}× gövde (≥ 2×)", f"Üst gölge {pct(up, r)} (küçük)", "Gövde aralığın üst kısmında"]
        ish = [f"Üst gölge {fp(up)} = {up / bd:.1f}× gövde (≥ 2×)", f"Alt gölge {pct(lo, r)} (küçük)", "Gövde aralığın alt kısmında"]
        if hammer_shape and t1 < 0:
            add("hammer", 1, [trtxt(t1, s1)] + sh)
        if hammer_shape and t1 > 0:
            add("hanging_man", 1, [trtxt(t1, s1)] + sh)
        if inv_shape and t1 < 0:
            add("inverted_hammer", 1, [trtxt(t1, s1)] + ish)
        if inv_shape and t1 > 0:
            add("shooting_star", 1, [trtxt(t1, s1)] + ish)
        if bd >= 0.9 * r and bd >= 1.3 * x.avgbody(0) and up <= 0.05 * r + 1e-9 and lo <= 0.05 * r + 1e-9:
            mk = [f"Gövde aralığın {pct(bd, r)}'i (≥ %90)", f"Gövde {fp(bd)} ≥ 1,3× ort. gövde ({fp(1.3 * x.avgbody(0))})", "Gölgeler ≤ %5"]
            add("marubozu_bull" if c > o else "marubozu_bear", 1, mk)
        if 0.1 * r < bd <= 0.3 * r and up > bd and lo > bd:
            add("spinning_top", 1, [f"Gövde aralığın {pct(bd, r)}'i (%10–30)", f"Üst ({fp(up)}) ve alt ({fp(lo)}) gölge > gövde"])
        if t1 < 0 and c > o and lo <= max(x.tick, 0.03 * r) and bd >= 0.6 * r and bd >= 1.2 * x.avgbody(0) and o < x.C(1):
            add("belt_hold_bull", 1, [trtxt(t1, s1), f"Açılış {fp(o)} = günün dibi (alt gölge {fp(lo)})", f"Açılış önceki kapanışın ({fp(x.C(1))}) altında", f"Uzun beyaz gövde {fp(bd)} (≥ 1,2× ort.)"])
        if t1 > 0 and c < o and up <= max(x.tick, 0.03 * r) and bd >= 0.6 * r and bd >= 1.2 * x.avgbody(0) and o > x.C(1):
            add("belt_hold_bear", 1, [trtxt(t1, s1), f"Açılış {fp(o)} = günün tepesi (üst gölge {fp(up)})", f"Açılış önceki kapanışın ({fp(x.C(1))}) üstünde", f"Uzun siyah gövde {fp(bd)} (≥ 1,2× ort.)"])

    # ---------------- iki bar
    o1, h1, l1, c1, b1, r1 = x.O(1), x.H(1), x.L(1), x.C(1), x.B(1), x.R(1)
    if r1 > 0:
        if t2 < 0 and x.bear(1) and x.bull(0) and ((c >= o1 and o < c1) or (c > o1 and o <= c1)) and bd > b1:
            add("engulfing_bull", 2, [trtxt(t2, s2), f"1. mum siyah ({fp(o1)}→{fp(c1)})", f"2. mum beyaz ({fp(o)}→{fp(c)})", f"Beyaz gövde siyah gövdeyi yuttu: açılış {fp(o)} ≤ {fp(c1)}, kapanış {fp(c)} ≥ {fp(o1)}"])
        if t2 > 0 and x.bull(1) and x.bear(0) and ((c <= o1 and o > c1) or (c < o1 and o >= c1)) and bd > b1:
            add("engulfing_bear", 2, [trtxt(t2, s2), f"1. mum beyaz ({fp(o1)}→{fp(c1)})", f"2. mum siyah ({fp(o)}→{fp(c)})", f"Siyah gövde beyaz gövdeyi yuttu: açılış {fp(o)} ≥ {fp(c1)}, kapanış {fp(c)} ≤ {fp(o1)}"])
        inside = max(o, c) <= max(o1, c1) and min(o, c) >= min(o1, c1) and bd <= 0.6 * b1
        if t2 < 0 and x.bear(1) and x.long(1) and inside:
            if x.doji(0):
                add("harami_cross_bull", 2, [trtxt(t2, s2), f"1. mum uzun siyah (gövde {fp(b1)})", "2. mum doji ve 1. gövdenin içinde"])
            elif x.bull(0):
                add("harami_bull", 2, [trtxt(t2, s2), f"1. mum uzun siyah (gövde {fp(b1)})", f"2. mum küçük beyaz ({fp(o)}→{fp(c)}) 1. gövdenin içinde"])
        if t2 > 0 and x.bull(1) and x.long(1) and inside:
            if x.doji(0):
                add("harami_cross_bear", 2, [trtxt(t2, s2), f"1. mum uzun beyaz (gövde {fp(b1)})", "2. mum doji ve 1. gövdenin içinde"])
            elif x.bear(0):
                add("harami_bear", 2, [trtxt(t2, s2), f"1. mum uzun beyaz (gövde {fp(b1)})", f"2. mum küçük siyah ({fp(o)}→{fp(c)}) 1. gövdenin içinde"])
        m1 = (o1 + c1) / 2
        if t2 < 0 and x.bear(1) and x.long(1) and x.bull(0) and o <= c1 and c > m1 and c < o1 and o < l1 + 0.25 * r1:
            add("piercing", 2, [trtxt(t2, s2), f"1. mum uzun siyah ({fp(o1)}→{fp(c1)})", f"2. mum {fp(o)} ile aşağıda açıldı", f"Kapanış {fp(c)} > 1. gövde ortası {fp(m1)} ve < açılış {fp(o1)}"])
        if t2 > 0 and x.bull(1) and x.long(1) and x.bear(0) and o >= c1 and c < m1 and c > o1 and o > h1 - 0.25 * r1:
            add("dark_cloud", 2, [trtxt(t2, s2), f"1. mum uzun beyaz ({fp(o1)}→{fp(c1)})", f"2. mum {fp(o)} ile yukarıda açıldı", f"Kapanış {fp(c)} < 1. gövde ortası {fp(m1)} ve > açılış {fp(o1)}"])
        if t2 < 0 and x.bear(1) and x.bull(0) and x.eq(l, l1) and min(l, l1) <= min(x.l[x.i - 6:x.i - 1]) :
            add("tweezer_bottom", 2, [trtxt(t2, s2), f"Dipler eşit: {fp(l1)} ≈ {fp(l)}", "Siyah mumu beyaz mum izledi", "Dip son 6 barın en düşüğü"])
        if t2 > 0 and x.bull(1) and x.bear(0) and x.eq(h, h1) and max(h, h1) >= max(x.h[x.i - 6:x.i - 1]):
            add("tweezer_top", 2, [trtxt(t2, s2), f"Tepeler eşit: {fp(h1)} ≈ {fp(h)}", "Beyaz mumu siyah mum izledi", "Tepe son 6 barın en yükseği"])
        if x.bear(1) and b1 >= 0.5 * x.avgbody(1) and x.bull(0) and x.long(0) and o > o1 and l >= o1:
            add("kicker_bull", 2, [f"1. mum siyah ({fp(o1)}→{fp(c1)})", f"2. mum 1. açılışın üstünde açıldı ({fp(o)} > {fp(o1)}) — boşluk", f"2. mum uzun beyaz (gövde {fp(bd)}), dip {fp(l)} ≥ {fp(o1)}"])
        if x.bull(1) and b1 >= 0.5 * x.avgbody(1) and x.bear(0) and x.long(0) and o < o1 and h <= o1:
            add("kicker_bear", 2, [f"1. mum beyaz ({fp(o1)}→{fp(c1)})", f"2. mum 1. açılışın altında açıldı ({fp(o)} < {fp(o1)}) — boşluk", f"2. mum uzun siyah (gövde {fp(bd)}), tepe {fp(h)} ≤ {fp(o1)}"])
        if t2 < 0 and x.bear(1) and x.long(1) and x.bull(0) and o < l1:
            if abs(c - l1) <= max(x.tick, 0.05 * r1):
                add("on_neck", 2, [trtxt(t2, s2), f"1. mum uzun siyah, dip {fp(l1)}", f"2. mum dibin altında açıldı ({fp(o)})", f"Kapanış {fp(c)} ≈ 1. dip {fp(l1)}"])
            elif c1 <= c <= c1 + max(x.tick, 0.1 * b1):
                add("in_neck", 2, [trtxt(t2, s2), f"1. mum uzun siyah ({fp(o1)}→{fp(c1)})", f"2. mum aşağıda açıldı ({fp(o)})", f"Kapanış {fp(c)} 1. kapanışın hemen üstünde (≤ gövdenin %10'u)"])
            elif c1 + 0.1 * b1 < c < m1:
                add("thrusting", 2, [trtxt(t2, s2), f"1. mum uzun siyah ({fp(o1)}→{fp(c1)})", f"2. mum aşağıda açıldı ({fp(o)})", f"Kapanış {fp(c)} gövdeye girdi ama ortanın ({fp(m1)}) altında"])
        if t2 < 0 and x.bear(1) and x.bear(0) and x.long(1) and abs(c - c1) <= x.tick + 1e-9:
            add("matching_low", 2, [trtxt(t2, s2), "İki siyah mum", f"Kapanışlar eşit: {fp(c1)} = {fp(c)}"])
        if t2 > 0 and x.bull(1) and x.bull(0) and x.long(1) and abs(c - c1) <= x.tick + 1e-9:
            add("matching_high", 2, [trtxt(t2, s2), "İki beyaz mum", f"Kapanışlar eşit: {fp(c1)} = {fp(c)}"])
        if t2 < 0 and x.bear(1) and x.long(1) and x.bull(0) and x.long(0) and o < c1 - 0.5 * a and abs(c - c1) <= max(x.tick, 0.05 * a):
            add("counterattack_bull", 2, [trtxt(t2, s2), "Uzun siyah + uzun beyaz", f"2. mum sert aşağı açıldı ({fp(o)} < {fp(c1)} − 0,5 ATR)", f"Kapanışlar eşit: {fp(c1)} ≈ {fp(c)}"])
        if t2 > 0 and x.bull(1) and x.long(1) and x.bear(0) and x.long(0) and o > c1 + 0.5 * a and abs(c - c1) <= max(x.tick, 0.05 * a):
            add("counterattack_bear", 2, [trtxt(t2, s2), "Uzun beyaz + uzun siyah", f"2. mum sert yukarı açıldı ({fp(o)} > {fp(c1)} + 0,5 ATR)", f"Kapanışlar eşit: {fp(c1)} ≈ {fp(c)}"])

    # ---------------- üç bar
    o2, h2, l2, c2, b2, r2 = x.O(2), x.H(2), x.L(2), x.C(2), x.B(2), x.R(2)
    if r2 > 0 and r1 > 0:
        m2 = (o2 + c2) / 2
        star_small = b1 <= 0.5 * b2 and (x.small(1) or x.doji(1))
        if t3 < 0 and x.bear(2) and x.long(2) and star_small and max(o1, c1) <= c2 + x.tick and x.bull(0) and c > m2 and bd >= 0.5 * x.avgbody(0):
            if x.doji(1) and h1 < l2 and h1 < l:
                add("abandoned_baby_bull", 3, [trtxt(t3, s3), "1. uzun siyah", f"Ortadaki doji iki yandan boşlukla ayrık (tepe {fp(h1)} < {fp(l2)} ve < {fp(l)})", f"3. beyaz mum 1. gövde ortası {fp(m2)} üstünde kapattı ({fp(c)})"])
            else:
                add("morning_doji_star" if x.doji(1) else "morning_star", 3, [trtxt(t3, s3), f"1. uzun siyah ({fp(o2)}→{fp(c2)})", f"2. küçük gövde{' (doji)' if x.doji(1) else ''} 1. kapanışın altında ({fp(max(o1, c1))} ≤ {fp(c2)})", f"3. beyaz mum 1. gövde ortası {fp(m2)} üstünde kapattı ({fp(c)})"])
        if t3 > 0 and x.bull(2) and x.long(2) and star_small and min(o1, c1) >= c2 - x.tick and x.bear(0) and c < m2 and bd >= 0.5 * x.avgbody(0):
            if x.doji(1) and l1 > h2 and l1 > h:
                add("abandoned_baby_bear", 3, [trtxt(t3, s3), "1. uzun beyaz", f"Ortadaki doji iki yandan boşlukla ayrık (dip {fp(l1)} > {fp(h2)} ve > {fp(h)})", f"3. siyah mum 1. gövde ortası {fp(m2)} altında kapattı ({fp(c)})"])
            else:
                add("evening_doji_star" if x.doji(1) else "evening_star", 3, [trtxt(t3, s3), f"1. uzun beyaz ({fp(o2)}→{fp(c2)})", f"2. küçük gövde{' (doji)' if x.doji(1) else ''} 1. kapanışın üstünde ({fp(min(o1, c1))} ≥ {fp(c2)})", f"3. siyah mum 1. gövde ortası {fp(m2)} altında kapattı ({fp(c)})"])
        ab = x.avgbody(2)
        sold = all(x.bull(k) and x.B(k) >= 0.6 * ab and x.U(k) <= 0.35 * x.B(k) for k in (0, 1, 2)) and c > c1 > c2 and min(o2, c2) <= o1 <= c2 and min(o1, c1) <= o <= c1
        if sold and t3 <= 0:
            add("three_white_soldiers", 3, [trtxt(t3, s3), f"Üç beyaz mum, kapanışlar yükseliyor: {fp(c2)} → {fp(c1)} → {fp(c)}", "Her mum öncekinin gövdesi içinde açıldı", "Üst gölgeler kısa (≤ gövdenin %35'i)"])
        crow = all(x.bear(k) and x.B(k) >= 0.6 * ab and x.W(k) <= 0.35 * x.B(k) for k in (0, 1, 2)) and c < c1 < c2 and c2 <= o1 <= max(o2, c2) and c1 <= o <= max(o1, c1)
        if crow and t3 >= 0:
            add("three_black_crows", 3, [trtxt(t3, s3), f"Üç siyah mum, kapanışlar düşüyor: {fp(c2)} → {fp(c1)} → {fp(c)}", "Her mum öncekinin gövdesi içinde açıldı", "Alt gölgeler kısa (≤ gövdenin %35'i)"])
        if t3 < 0 and x.bear(2) and x.long(2) and x.bull(1) and max(o1, c1) <= o2 and min(o1, c1) >= c2 and b1 <= 0.6 * b2 and x.bull(0) and c > o2:
            add("three_inside_up", 3, [trtxt(t3, s3), f"1. uzun siyah ({fp(o2)}→{fp(c2)})", "2. küçük beyaz 1. gövdenin içinde (boğa harami)", f"3. mum 1. açılışın ({fp(o2)}) üstünde kapattı ({fp(c)})"])
        if t3 > 0 and x.bull(2) and x.long(2) and x.bear(1) and max(o1, c1) <= c2 and min(o1, c1) >= o2 and b1 <= 0.6 * b2 and x.bear(0) and c < o2:
            add("three_inside_down", 3, [trtxt(t3, s3), f"1. uzun beyaz ({fp(o2)}→{fp(c2)})", "2. küçük siyah 1. gövdenin içinde (ayı harami)", f"3. mum 1. açılışın ({fp(o2)}) altında kapattı ({fp(c)})"])
        if t3 < 0 and x.bear(2) and x.bull(1) and ((c1 >= o2 and o1 < c2) or (c1 > o2 and o1 <= c2)) and b1 > b2 and x.bull(0) and c > c1:
            add("three_outside_up", 3, [trtxt(t3, s3), "1–2: yutan boğa", f"3. mum daha yüksek kapattı ({fp(c)} > {fp(c1)})"])
        if t3 > 0 and x.bull(2) and x.bear(1) and ((c1 <= o2 and o1 > c2) or (c1 < o2 and o1 >= c2)) and b1 > b2 and x.bear(0) and c < c1:
            add("three_outside_down", 3, [trtxt(t3, s3), "1–2: yutan ayı", f"3. mum daha düşük kapattı ({fp(c)} < {fp(c1)})"])
        if x.doji(0) and x.doji(1) and x.doji(2) and r >= 3 * x.tick:
            mb = (o1 + c1) / 2
            if t3 < 0 and mb < min(o2, c2) and mb < min(o, c):
                add("tri_star_bull", 3, [trtxt(t3, s3), "Art arda üç doji", f"Ortadaki doji ({fp(mb)}) ikisinin de altında"])
            if t3 > 0 and mb > max(o2, c2) and mb > max(o, c):
                add("tri_star_bear", 3, [trtxt(t3, s3), "Art arda üç doji", f"Ortadaki doji ({fp(mb)}) ikisinin de üstünde"])
        if t3 > 0 and x.bull(2) and x.bull(1) and l1 > h2 and x.bear(0) and min(o1, c1) < o < max(o1, c1) and h2 < c < o1:
            add("tasuki_up", 3, [trtxt(t3, s3), f"İki beyaz mum arasında yukarı boşluk ({fp(h2)}–{fp(l1)})", f"3. siyah mum 2. gövde içinde açıldı ({fp(o)})", f"Kapanış {fp(c)} boşluğun içinde (boşluk kapanmadı)"])
        if t3 < 0 and x.bear(2) and x.bear(1) and h1 < l2 and x.bull(0) and min(o1, c1) < o < max(o1, c1) and o1 < c < l2:
            add("tasuki_down", 3, [trtxt(t3, s3), f"İki siyah mum arasında aşağı boşluk ({fp(h1)}–{fp(l2)})", f"3. beyaz mum 2. gövde içinde açıldı ({fp(o)})", f"Kapanış {fp(c)} boşluğun içinde (boşluk kapanmadı)"])
        if t3 > 0 and all(x.bull(k) for k in (0, 1, 2)) and c > c1 > c2 and bd < b1 < b2 and up > x.U(1) * 0.99 and up >= 0.5 * bd and x.U(1) >= x.U(2) and min(o2, c2) <= o1 <= c2 + x.tick and min(o1, c1) <= o <= c1 + x.tick:
            add("advance_block", 3, [trtxt(t3, s3), f"Üç beyaz mum, kapanışlar yükseliyor ({fp(c2)} → {fp(c1)} → {fp(c)})", f"Gövdeler küçülüyor: {fp(b2)} > {fp(b1)} > {fp(bd)}", f"Üst gölgeler uzuyor: {fp(x.U(2))} ≤ {fp(x.U(1))} ≤ {fp(up)}"])
        if t3 < 0 and x.bear(2) and x.bull(1) and x.bear(0) and c1 > c2 and o1 >= c2 - x.tick and abs(c - c2) <= x.tick + 1e-9 and l1 > c2 - 0.5 * a:
            add("stick_sandwich", 3, [trtxt(t3, s3), f"1. siyah ({fp(c2)}), 2. beyaz ({fp(c1)} > {fp(c2)}), 3. siyah", f"1. ve 3. kapanış eşit: {fp(c2)} = {fp(c)}"])

    # ---------------- beş bar
    if x.n >= 30:
        o4, c4, h4, l4, b4 = x.O(4), x.C(4), x.H(4), x.L(4), x.B(4)
        mids = (1, 2, 3)
        if x.bull(4) and x.long(4) and all(x.H(k) <= h4 + x.tick and x.L(k) >= l4 - x.tick and x.B(k) <= 0.6 * b4 for k in mids) and sum(x.bear(k) for k in mids) >= 2 and x.bull(0) and x.long(0) and c > c4 and t5 >= 0:
            add("rising_three", 5, [f"1. uzun beyaz ({fp(o4)}→{fp(c4)})", f"2–4: küçük mumlar 1. aralığın ({fp(l4)}–{fp(h4)}) içinde, çoğu siyah", f"5. uzun beyaz yeni kapanış zirvesi ({fp(c)} > {fp(c4)})"])
        if x.bear(4) and x.long(4) and all(x.H(k) <= h4 + x.tick and x.L(k) >= l4 - x.tick and x.B(k) <= 0.6 * b4 for k in mids) and sum(x.bull(k) for k in mids) >= 2 and x.bear(0) and x.long(0) and c < c4 and t5 <= 0:
            add("falling_three", 5, [f"1. uzun siyah ({fp(o4)}→{fp(c4)})", f"2–4: küçük mumlar 1. aralığın ({fp(l4)}–{fp(h4)}) içinde, çoğu beyaz", f"5. uzun siyah yeni kapanış dibi ({fp(c)} < {fp(c4)})"])
        if t5 < 0 and all(x.bear(k) for k in (4, 3, 2, 1)) and x.C(4) > x.C(3) > x.C(2) > c1 and x.O(4) > x.O(3) > x.O(2) and x.U(1) >= 0.5 * b1 and x.bull(0) and o > max(o1, c1) and c > h1:
            add("ladder_bottom", 5, [trtxt(t5, s5), f"1–3: düşen açılış/kapanışlı siyah mumlar ({fp(x.C(4))} → {fp(x.C(2))})", f"4. siyah mumda üst gölge ({fp(x.U(1))} ≥ gövdenin yarısı)", f"5. beyaz mum 4. gövdenin üstünde açıldı ({fp(o)}) ve tepesini aştı ({fp(c)} > {fp(h1)})"])
    return hits


def vol_confirm(x: Ctx, nb):
    """Formasyonun son barı hacmi ≥ 1,2× son 20 bar ortalaması."""
    j = x.i
    s = x.v[max(0, j - nb - 20):j - nb + 1]
    s = s[s > 0]
    if not len(s) or x.v[j] <= 0:
        return False, None
    r = float(x.v[j] / s.mean())
    return r >= 1.2, round(r, 2)


def etki(key, d, typ, nb, x: Ctx):
    """Etkisi: anlam + teyit + geçersizlik."""
    hi = float(max(x.h[x.i - nb + 1:x.i + 1]))
    lo = float(min(x.l[x.i - nb + 1:x.i + 1]))
    meaning = P[key][6]
    if d == "U":
        conf, inv = hi, lo
        txt = (f"{meaning} Teyit: sonraki bar {fp(hi)} üzerinde kapanırsa yükseliş sinyali güçlenir. "
               f"Geçersizlik: {fp(lo)} altında kapanış formasyonu bozar.")
        if typ == "devam":
            txt = f"{meaning} Teyit: {fp(hi)} üzeri kapanışla yükseliş trendi sürer. Geçersizlik: {fp(lo)} altı."
    elif d == "D":
        conf, inv = lo, hi
        txt = (f"{meaning} Teyit: sonraki bar {fp(lo)} altında kapanırsa düşüş sinyali güçlenir. "
               f"Geçersizlik: {fp(hi)} üzerinde kapanış formasyonu bozar.")
        if typ == "devam":
            txt = f"{meaning} Teyit: {fp(lo)} altı kapanışla düşüş trendi sürer. Geçersizlik: {fp(hi)} üzeri."
    else:
        conf, inv = hi, lo
        txt = f"{meaning} Yön için bekleyin: {fp(hi)} üzeri kapanış yükseliş, {fp(lo)} altı kapanış düşüş yönünü teyit eder."
    return txt, conf, inv


def scan(b, n, with_bars=False):
    """Bars + kapanmış bar sayısı → mum formasyonu sonuçları (dict listesi)."""
    if n < 25:
        return []
    b0 = b
    start = max(0, n - 120)
    x = Ctx(type(b0)(b0.t[start:n], b0.o[start:n], b0.h[start:n], b0.l[start:n], b0.c[start:n], b0.v[start:n], b0.day[start:n]), n - start)
    out = []
    for key, nb, checks in detect(x):
        nm, en, d, typ, rel, _nb, _m = P[key]
        # dragonfly/gravestone trend bağlamı yoksa kararsız
        if key in ("dragonfly_doji", "gravestone_doji"):
            t1 = x.trend(1)[0]
            if (key == "dragonfly_doji" and t1 >= 0) or (key == "gravestone_doji" and t1 <= 0):
                d, typ, rel = "N", "kararsızlık", 1
        if key == "three_white_soldiers" and x.trend(3)[0] > 0:
            typ = "devam"
        if key == "three_black_crows" and x.trend(3)[0] < 0:
            typ = "devam"
        vc, vr = vol_confirm(x, nb)
        txt, conf, inv = etki(key, d, typ, nb, x)
        score = rel * 25 + (15 if vc else 0) + min(10, int(abs(x.trend(nb)[1]) * 2))
        out.append({"k": key, "ad": nm, "en": en, "yon": d, "tip": typ, "guven": rel, "nb": nb, "hacim": vc, "hr": vr,
                    "teyit": round(conf, 4), "gecersiz": round(inv, 4), "etki": txt, "kontrol": checks, "skor": min(100, score),
                    "t": int(b0.t[n - 1]), "t0": int(b0.t[n - nb]), "c": float(b0.c[n - 1])})
    return out
