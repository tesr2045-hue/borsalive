"""v1.27.0 — GRAFİK FORMASYONLARI dedektörü (ZigZag pivotları, iki ölçek: 1,5×ATR ve 2,5×ATR).

Yükseliş yönlü dedektörler bir kez yazılır; düşüş karşılıkları fiyat serisi aynalanarak (H' = −L, L' = −H) bulunur
(Ters OBO ↔ OBO, İkili Dip ↔ İkili Tepe, Fincan-Kulp ↔ Ters Fincan-Kulp, Boğa ↔ Ayı Bayrağı/Flaması, Yuvarlak Dip ↔ Tepe).
Çizgi formasyonları (üçgen/takoz/kanal/dikdörtgen/genişleyen) eğimlerden doğrudan sınıflandırılır.
Seviyeler: giriş = kırılım çizgisi; STOP = formasyonun geçersizlik noktası; HEDEF 1 = giriş ± formasyon yüksekliği
(ölçülen hareket), HEDEF 2 = giriş ± 1,618 × yükseklik; R/R = (HEDEF 1 − giriş) / (giriş − STOP).
"""
from __future__ import annotations

import numpy as np

from app.v127_candles import atr as _atr, fp, tick_of

MAX_AGE = 12          # kırılım / başarısızlık en çok kaç bar önce olmuş olabilir
WIN = 220

# key: (ad, en, yön, tip, mirror_key)
CP = {
    "ters_obo": ("Ters OBO", "Inverse Head & Shoulders", "U", "dönüş"),
    "obo": ("OBO (Omuz-Baş-Omuz)", "Head & Shoulders", "D", "dönüş"),
    "ikili_dip": ("İkili Dip", "Double Bottom", "U", "dönüş"),
    "ikili_tepe": ("İkili Tepe", "Double Top", "D", "dönüş"),
    "uclu_dip": ("Üçlü Dip", "Triple Bottom", "U", "dönüş"),
    "uclu_tepe": ("Üçlü Tepe", "Triple Top", "D", "dönüş"),
    "fincan_kulp": ("Fincan-Kulp", "Cup & Handle", "U", "devam"),
    "ters_fincan": ("Ters Fincan-Kulp", "Inverted Cup & Handle", "D", "devam"),
    "yukselen_ucgen": ("Yükselen Üçgen", "Ascending Triangle", "U", "devam"),
    "alcalan_ucgen": ("Alçalan Üçgen", "Descending Triangle", "D", "devam"),
    "simetrik_ucgen": ("Simetrik Üçgen", "Symmetrical Triangle", "N", "devam"),
    "yukselen_takoz": ("Yükselen Takoz", "Rising Wedge", "D", "dönüş"),
    "alcalan_takoz": ("Alçalan Takoz", "Falling Wedge", "U", "dönüş"),
    "boga_bayrak": ("Boğa Bayrağı", "Bull Flag", "U", "devam"),
    "ayi_bayrak": ("Ayı Bayrağı", "Bear Flag", "D", "devam"),
    "boga_flama": ("Boğa Flaması", "Bull Pennant", "U", "devam"),
    "ayi_flama": ("Ayı Flaması", "Bear Pennant", "D", "devam"),
    "dikdortgen": ("Dikdörtgen (Yatay Kanal)", "Rectangle", "N", "devam"),
    "yukselen_kanal": ("Yükselen Kanal", "Ascending Channel", "U", "devam"),
    "alcalan_kanal": ("Alçalan Kanal", "Descending Channel", "D", "devam"),
    "genisleyen": ("Genişleyen Formasyon", "Broadening Formation", "N", "kararsızlık"),
    "yuvarlak_dip": ("Yuvarlak Dip", "Rounding Bottom", "U", "dönüş"),
    "yuvarlak_tepe": ("Yuvarlak Tepe", "Rounding Top", "D", "dönüş"),
}
MIRROR = {"ters_obo": "obo", "ikili_dip": "ikili_tepe", "uclu_dip": "uclu_tepe", "fincan_kulp": "ters_fincan",
          "boga_bayrak": "ayi_bayrak", "boga_flama": "ayi_flama", "yuvarlak_dip": "yuvarlak_tepe"}
MEANING = {
    "ters_obo": "Düşüş trendinin sonunda üç dip (ortadaki en derin): satıcılar her dipte zayıfladı; boyun çizgisi kırılırsa yükselişe dönüş beklenir.",
    "obo": "Yükseliş trendinin sonunda üç tepe (ortadaki en yüksek): alıcılar yoruldu; boyun çizgisi kırılırsa düşüşe dönüş beklenir.",
    "ikili_dip": "Aynı seviyede iki dip: o fiyatta güçlü talep var; aradaki tepe (boyun) aşılırsa yükseliş beklenir.",
    "ikili_tepe": "Aynı seviyede iki tepe: o fiyatta güçlü arz var; aradaki dip (boyun) kırılırsa düşüş beklenir.",
    "uclu_dip": "Aynı destekte üç dip: satıcılar desteği kıramadı; direnç aşılırsa güçlü yükseliş beklenir.",
    "uclu_tepe": "Aynı dirençte üç tepe: alıcılar direnci aşamadı; destek kırılırsa güçlü düşüş beklenir.",
    "fincan_kulp": "U şeklinde yuvarlak taban (fincan) ve kısa geri çekilme (kulp): birikim tamamlanıyor; kulp tepesi aşılırsa yükseliş devamı.",
    "ters_fincan": "Ters U şeklinde tepe ve kısa tepki (kulp): dağıtım tamamlanıyor; kulp dibi kırılırsa düşüş devamı.",
    "yukselen_ucgen": "Yatay direnç ve yükselen dipler: alıcılar her seferinde daha yüksekten alıyor; direnç kırılımı yükseliş getirir.",
    "alcalan_ucgen": "Yatay destek ve alçalan tepeler: satıcılar her seferinde daha aşağıdan satıyor; destek kırılımı düşüş getirir.",
    "simetrik_ucgen": "Alçalan tepeler ve yükselen dipler sıkışıyor: kırılım yönünde sert hareket beklenir (çoğunlukla trend yönünde).",
    "yukselen_takoz": "Daralan iki yükselen çizgi: yükseliş ivme kaybediyor; alt çizginin kırılımı düşüş getirir.",
    "alcalan_takoz": "Daralan iki alçalan çizgi: düşüş ivme kaybediyor; üst çizginin kırılımı yükseliş getirir.",
    "boga_bayrak": "Sert yükseliş (direk) sonrası hafif aşağı eğimli dar kanal: kısa mola; üst sınır aşılırsa direk boyu kadar yükseliş beklenir.",
    "ayi_bayrak": "Sert düşüş (direk) sonrası hafif yukarı eğimli dar kanal: kısa tepki; alt sınır kırılırsa direk boyu kadar düşüş beklenir.",
    "boga_flama": "Sert yükseliş sonrası küçük simetrik sıkışma: kırılımla yükselişin devamı beklenir.",
    "ayi_flama": "Sert düşüş sonrası küçük simetrik sıkışma: kırılımla düşüşün devamı beklenir.",
    "dikdortgen": "Yatay destek ile direnç arasında gidip gelme: kırılım yönünde aralık yüksekliği kadar hareket beklenir.",
    "yukselen_kanal": "Paralel yükselen çizgiler arasında düzenli yükseliş: destekte alım bölgesi, alt çizginin kırılması trendi bozar.",
    "alcalan_kanal": "Paralel alçalan çizgiler arasında düzenli düşüş: dirençte satış bölgesi, üst çizginin aşılması trendi bozar.",
    "genisleyen": "Giderek yükselen tepeler ve alçalan dipler: oynaklık artıyor, piyasa kararsız; kırılım yönü takip edilir.",
    "yuvarlak_dip": "Uzun ve yavaş, kase şeklinde dip: satış baskısı kademeli olarak alıma döndü; kenar seviyesi aşılırsa yükseliş.",
    "yuvarlak_tepe": "Uzun ve yavaş, ters kase şeklinde tepe: alım baskısı kademeli olarak satışa döndü; kenar seviyesi kırılırsa düşüş.",
}


def zigzag(h, l, a, k):
    """ZigZag pivotları: [(i, fiyat, 'H'/'L', tentative)] (son pivot geçici olabilir)."""
    n = len(h)
    piv = []
    if n < 5:
        return piv
    hi_i = lo_i = 0
    up = None
    ext = 0
    for i in range(1, n):
        th = k * a[i]
        if up is None:
            if h[i] > h[hi_i]: hi_i = i
            if l[i] < l[lo_i]: lo_i = i
            if h[hi_i] - l[lo_i] >= th:
                if hi_i > lo_i:
                    piv.append([lo_i, l[lo_i], "L", False]); up = True; ext = hi_i
                else:
                    piv.append([hi_i, h[hi_i], "H", False]); up = False; ext = lo_i
            continue
        if up:
            if h[i] >= h[ext]:
                ext = i
            elif h[ext] - l[i] >= th:
                piv.append([ext, h[ext], "H", False]); up = False; ext = i
        else:
            if l[i] <= l[ext]:
                ext = i
            elif h[i] - l[ext] >= th:
                piv.append([ext, l[ext], "L", False]); up = True; ext = i
    if up is not None:
        piv.append([ext, h[ext] if up else l[ext], "H" if up else "L", True])
    return piv


class S:
    """Seri bağlamı (gerekirse aynalanmış)."""
    def __init__(self, t, o, h, l, c, v, flip=False):
        self.flip = flip
        if flip:
            o, h, l, c = -o, -l, -h, -c
        self.t, self.o, self.h, self.l, self.c, self.v = t, o, h, l, c, v
        self.n = len(c)
        self.a = np.maximum(_atr(h, l, c), tick_of(abs(float(c[-1]))))
        self.A = float(self.a[-1])

    def P(self, x):       # gerçek fiyata çevir
        return -x if self.flip else x

    def vavg(self, i):
        s = self.v[max(0, i - 20):i]
        s = s[s > 0]
        return float(s.mean()) if len(s) else 0.0


def _line(i1, p1, i2, p2):
    if i2 == i1:
        return lambda i: p1
    m = (p2 - p1) / (i2 - i1)
    return lambda i: p1 + m * (i - i1)


def _fit(xs, ys):
    if len(xs) < 2:
        return None
    m, b = np.polyfit(np.asarray(xs, float), np.asarray(ys, float), 1)
    return lambda i, m=m, b=b: m * i + b


def _breakout(s: S, start, line, up=True):
    """start'tan sonra çizginin üstünde (up) ilk kapanış."""
    for i in range(start, s.n):
        if (s.c[i] > line(i)) if up else (s.c[i] < line(i)):
            return i
    return None


def _finish(s: S, key, start_i, last_piv_i, line, stop, height, pts, lines, checks, qual, tgt1=None, bo_from=None, inside_ok=True):
    """Yükseliş yönlü (aynalanmış olabilir) formasyon → durum + seviyeler. None = güncel değil / geçersiz."""
    n = s.n
    bo = _breakout(s, (bo_from if bo_from is not None else last_piv_i + 1), line, True)
    status, fail_i = "OLUŞUYOR", None
    if bo is None:
        if s.c[-1] <= stop:
            return None
        if n - 1 - last_piv_i > max(12, (last_piv_i - start_i) * 0.6):
            return None
        entry = line(n - 1)
        if entry - s.c[-1] > 1.2 * height:
            return None
    else:
        if n - 1 - bo > 3 * MAX_AGE:
            return None
        entry = line(bo)
        status = "KIRILDI"
        for j in range(bo + 1, n):
            if s.c[j] < stop:
                status, fail_i = "BAŞARISIZ", j
                break
        if status == "KIRILDI" and n - 1 - bo > MAX_AGE:
            return None
        if status == "BAŞARISIZ" and n - 1 - fail_i > MAX_AGE:
            return None
    t1 = tgt1 if (tgt1 is not None and tgt1 > entry) else entry + height
    t2 = entry + 1.618 * height
    if t2 <= t1:
        t2 = t1 + 0.618 * height
    risk = entry - stop
    if risk <= 0:
        return None
    rr = (t1 - entry) / risk
    vc, vr = False, None
    if bo is not None:
        va = s.vavg(bo)
        if va > 0 and s.v[bo] > 0:
            vr = round(float(s.v[bo] / va), 2); vc = vr >= 1.5
    hit1 = bo is not None and float(np.max(s.h[bo:])) >= t1
    q = qual + (15 if vc else 0) + (8 if height >= 4 * s.A else 0) + (5 if 1.0 <= rr <= 6 else 0) - (10 if status == "BAŞARISIZ" else 0)
    return {"k": key, "durum": status, "bo": bo, "fail": fail_i, "entry": entry, "stop": stop, "t1": t1, "t2": t2, "rr": round(rr, 2),
            "vc": vc, "vr": vr, "hit1": hit1, "q": int(max(5, min(99, q))), "height": height, "start": start_i,
            "pts": pts, "lines": lines, "checks": checks}


# ------------------------------------------------------------------ yükseliş yönlü dedektörler (aynalanarak düşüş)
def det_inv_hs(s: S, P, out):
    for j in range(len(P) - 1, max(4, len(P) - 4) - 1, -1):
        if P[j][2] != "L" or P[j][3] or j < 5:
            continue
        LS, N1, HD, N2, RS = P[j - 4], P[j - 3], P[j - 2], P[j - 1], P[j]
        pre = P[j - 5]
        if not (LS[2] == "L" and HD[2] == "L" and N1[2] == "H" and N2[2] == "H"):
            continue
        neck = _line(N1[0], N1[1], N2[0], N2[1])
        height = neck(HD[0]) - HD[1]
        if height < 2 * s.A:
            continue
        if not (HD[1] < LS[1] - 0.2 * height and HD[1] < RS[1] - 0.2 * height):
            continue
        if abs(LS[1] - RS[1]) > 0.45 * height or abs(N1[1] - N2[1]) > 0.6 * height:
            continue
        r = (HD[0] - LS[0]) / max(1, RS[0] - HD[0])
        if not (0.33 <= r <= 3.0):
            continue
        if pre[1] <= max(N1[1], N2[1]):
            continue
        if np.min(s.l[RS[0]:]) < HD[1]:
            continue
        sym = 1 - abs(LS[1] - RS[1]) / (0.45 * height)
        q = 45 + int(15 * sym) + (8 if 0.6 <= r <= 1.6 else 0)
        pts = [[LS[0], LS[1], "Sol omuz"], [N1[0], N1[1], "Boyun 1"], [HD[0], HD[1], "Baş"], [N2[0], N2[1], "Boyun 2"], [RS[0], RS[1], "Sağ omuz"]]
        lines = [[N1[0], N1[1], s.n - 1, neck(s.n - 1), "neck", "Boyun çizgisi"]]
        ck = [f"Baş ({fp(s.P(HD[1]))}) iki omuzdan da belirgin derin (≥ yüksekliğin %20'si)",
              f"Omuzlar dengeli: {fp(s.P(LS[1]))} ≈ {fp(s.P(RS[1]))}", f"Formasyon yüksekliği {fp(height)} ≥ 2×ATR ({fp(2 * s.A)})",
              f"Zaman simetrisi {r:.2f} (0,33–3)", "Öncesinde ters yönlü trend (boyun çizgisinin ötesinden gelindi)"]
        res = _finish(s, "ters_obo", LS[0], RS[0], neck, RS[1] - 0.1 * s.A, height, pts, lines, ck, q)
        if res:
            out.append(res); return


def det_double(s: S, P, out):
    for j in range(len(P) - 1, max(2, len(P) - 4) - 1, -1):
        if P[j][2] != "L" or P[j][3] or j < 3:
            continue
        L1, H1, L2, pre = P[j - 2], P[j - 1], P[j], P[j - 3]
        if L1[2] != "L" or H1[2] != "H":
            continue
        height = H1[1] - min(L1[1], L2[1])
        if height < 2.5 * s.A or L2[0] - L1[0] < 6:
            continue
        tol = max(0.5 * s.A, 0.12 * height)
        if abs(L1[1] - L2[1]) > tol or pre[1] <= H1[1]:
            continue
        # üçlü dip ise ikiliyi bildirme
        if j >= 4 and P[j - 4][2] == "L" and abs(P[j - 4][1] - L2[1]) <= tol and P[j - 3][1] - min(L1[1], L2[1]) >= 2 * s.A:
            continue
        lo = min(L1[1], L2[1])
        if np.min(s.l[L2[0]:]) < lo - 0.25 * s.A:
            continue
        neck = lambda i, v=H1[1]: v
        q = 50 + int(15 * (1 - abs(L1[1] - L2[1]) / tol))
        pts = [[L1[0], L1[1], "1. dip"], [H1[0], H1[1], "Boyun"], [L2[0], L2[1], "2. dip"]]
        lines = [[H1[0], H1[1], s.n - 1, H1[1], "neck", "Boyun (direnç)"], [L1[0], lo, s.n - 1, lo, "sup", "Destek"]]
        ck = [f"İki dip eşit: {fp(s.P(L1[1]))} ≈ {fp(s.P(L2[1]))} (fark ≤ {fp(tol)})", f"Aradaki tepe (boyun) {fp(s.P(H1[1]))}",
              f"Yükseklik {fp(height)} ≥ 2,5×ATR", f"Dipler arası {L2[0] - L1[0]} bar (≥ 6)", "Öncesinde ters yönlü trend"]
        res = _finish(s, "ikili_dip", L1[0], L2[0], neck, lo - 0.1 * s.A, height, pts, lines, ck, q)
        if res:
            out.append(res); return


def det_triple(s: S, P, out):
    for j in range(len(P) - 1, max(4, len(P) - 4) - 1, -1):
        if P[j][2] != "L" or P[j][3] or j < 5:
            continue
        L1, H1, L2, H2, L3, pre = P[j - 4], P[j - 3], P[j - 2], P[j - 1], P[j], P[j - 5]
        if not (L1[2] == "L" and L2[2] == "L" and H1[2] == "H" and H2[2] == "H"):
            continue
        lows = [L1[1], L2[1], L3[1]]
        neckv = max(H1[1], H2[1])
        height = neckv - min(lows)
        tol = max(0.5 * s.A, 0.12 * height)
        if height < 2.5 * s.A or max(lows) - min(lows) > tol or pre[1] <= neckv:
            continue
        if np.min(s.l[L3[0]:]) < min(lows) - 0.25 * s.A:
            continue
        neck = lambda i, v=neckv: v
        pts = [[L1[0], L1[1], "1. dip"], [H1[0], H1[1], ""], [L2[0], L2[1], "2. dip"], [H2[0], H2[1], ""], [L3[0], L3[1], "3. dip"]]
        lines = [[H1[0], neckv, s.n - 1, neckv, "neck", "Direnç (boyun)"], [L1[0], min(lows), s.n - 1, min(lows), "sup", "Destek"]]
        ck = [f"Üç dip aynı bölgede: {', '.join(fp(s.P(x)) for x in lows)} (yayılım ≤ {fp(tol)})", f"Boyun/direnç {fp(s.P(neckv))}",
              f"Yükseklik {fp(height)} ≥ 2,5×ATR", "Öncesinde ters yönlü trend"]
        res = _finish(s, "uclu_dip", L1[0], L3[0], neck, min(lows) - 0.1 * s.A, height, pts, lines, ck, 60)
        if res:
            out.append(res); return


def det_cup(s: S, P, out):
    Hs = [p for p in P if p[2] == "H" and not p[3]]
    for bi in range(len(Hs) - 1, max(0, len(Hs) - 3) - 1, -1):
        R2 = Hs[bi]
        for ai in range(bi - 1, -1, -1):
            R1 = Hs[ai]
            a, b = R1[0], R2[0]
            if b - a < 15:
                continue
            seg = s.l[a:b + 1]
            bot_i = a + int(np.argmin(seg)); bot = float(seg.min())
            rim = min(R1[1], R2[1])
            depth = rim - bot
            if depth < 3 * s.A or abs(R1[1] - R2[1]) > 0.15 * depth:
                continue
            if not (a + 0.25 * (b - a) <= bot_i <= a + 0.75 * (b - a)):
                continue
            if any(p[1] > bot + 0.65 * depth for p in Hs if a < p[0] < b):
                continue
            mid = s.c[a + (b - a) // 3: a + 2 * (b - a) // 3 + 1]
            if not len(mid) or float(np.mean(mid)) > bot + 0.45 * depth:
                continue
            res_lv = max(R1[1], R2[1])
            # kulp: R2'den sonra kırılıma kadar
            bo = _breakout(s, b + 1, lambda i: res_lv, True)
            hend = bo if bo is not None else s.n
            if hend - b < 3 or hend - b > max(5, 0.5 * (b - a)):
                break
            hseg = s.l[b + 1:hend]
            hl = float(hseg.min())
            if R2[1] - hl > 0.5 * depth or R2[1] - hl < 0.08 * depth or hl < bot + 0.5 * depth:
                break
            hl_i = b + 1 + int(np.argmin(hseg))
            pts = [[a, R1[1], "Sol kenar"], [bot_i, bot, "Fincan dibi"], [b, R2[1], "Sağ kenar"], [hl_i, hl, "Kulp"]]
            lines = [[a, res_lv, s.n - 1, res_lv, "res", "Kenar direnci"]]
            ck = [f"Fincan derinliği {fp(depth)} ≥ 3×ATR, süre {b - a} bar (≥ 15)", f"Kenarlar eşit: {fp(s.P(R1[1]))} ≈ {fp(s.P(R2[1]))}",
                  "Yuvarlak (U) taban: orta üçte birlik bölüm dibe yakın", f"Kulp geri çekilmesi {fp(R2[1] - hl)} ≤ derinliğin yarısı"]
            res = _finish(s, "fincan_kulp", a, hl_i, lambda i: res_lv, hl - 0.1 * s.A, depth, pts, lines, ck, 62, bo_from=b + 1)
            if res:
                out.append(res); return
            break


def det_flag(s: S, P, out):
    Hs = [p for p in P[-7:] if p[2] == "H" and not p[3]]
    for TP in Hs:
        ti = TP[0]
        b0 = max(0, ti - 15)
        if ti - b0 < 2:
            continue
        bi = b0 + int(np.argmin(s.l[b0:ti]))
        BT = [bi, float(s.l[bi]), "L", False]
        rise = TP[1] - BT[1]
        bars = ti - bi
        a0 = float(s.a[max(0, bi - 1)])          # direk öncesi ATR
        if bars > 15 or bars < 2 or rise < max(6 * a0, 3 * s.A) or rise / bars < 1.0 * a0:
            continue
        ti = TP[0]
        bo = None
        for k in range(ti + 4, min(s.n, ti + 22)):
            if s.c[k] > float(np.max(s.h[ti + 1:k])) and s.c[k] > TP[1] - 0.05 * rise:
                bo = k; break
        cend = bo if bo is not None else s.n
        m = cend - (ti + 1)
        if m < 3 or m > 20:
            continue
        hs, ls = s.h[ti + 1:cend], s.l[ti + 1:cend]
        if TP[1] - float(ls.min()) > 0.5 * rise or float(hs.max()) > TP[1] + 0.1 * s.A:
            continue
        hm_ = m // 2
        i1h = ti + 1 + int(np.argmax(hs[:hm_])); i2h = ti + 1 + hm_ + int(np.argmax(hs[hm_:]))
        i1l = ti + 1 + int(np.argmin(ls[:hm_])); i2l = ti + 1 + hm_ + int(np.argmin(ls[hm_:]))
        uf = _line(i1h, float(s.h[i1h]), i2h, float(s.h[i2h])); lf = _line(i1l, float(s.l[i1l]), i2l, float(s.l[i2l]))
        su = (float(s.h[i2h]) - float(s.h[i1h])) / rise
        sl = (float(s.l[i2l]) - float(s.l[i1l])) / rise
        if sl - su >= 0.05 and su <= 0.02 and sl >= -0.02:
            key = "boga_flama"
        elif su <= 0.05 and sl <= 0.05 and abs(su - sl) <= 0.25:
            key = "boga_bayrak"
        else:
            continue
        top = float(hs.max()); low = float(ls.min())
        pts = [[BT[0], BT[1], "Direk dibi"], [ti, TP[1], "Direk tepesi"]]
        lines = [[ti + 1, uf(ti + 1), cend - 1, uf(cend - 1), "res", "Üst sınır"], [ti + 1, lf(ti + 1), cend - 1, lf(cend - 1), "sup", "Alt sınır"],
                 [BT[0], BT[1], ti, TP[1], "pole", "Direk"]]
        ck = [f"Direk: {bars} barda {fp(rise)} (≥ 6× direk öncesi ATR = {fp(6 * a0)})", f"Konsolidasyon {m} bar (3–20)",
              f"Geri çekilme {fp(TP[1] - low)} ≤ direğin yarısı", "Bayrak: paralel, hafif ters eğimli kanal" if key == "boga_bayrak" else "Flama: daralan küçük üçgen"]
        res = _finish(s, key, BT[0], cend - 1, lambda i, v=top: v, low - 0.1 * s.A, rise, pts, lines, ck, 58, bo_from=ti + 4 if bo is None else bo)
        if res:
            out.append(res); return


def det_round(s: S, P, out):
    n = s.n
    for W in (60, 100, 140):
        if n < W + 5:
            break
        st = n - W
        y = s.c[st:]
        x = np.linspace(0, 1, W)
        A2, B1, C0 = np.polyfit(x, y, 2)
        if A2 <= 0:
            continue
        xv = -B1 / (2 * A2)
        if not (0.3 <= xv <= 0.75):
            continue
        fit = A2 * x * x + B1 * x + C0
        ss = float(np.sum((y - y.mean()) ** 2)) or 1e-9
        r2 = 1 - float(np.sum((y - fit) ** 2)) / ss
        if r2 < 0.88:
            continue
        rim = float(np.max(s.h[st:st + max(3, W // 10)]))
        bot_i = st + int(np.argmin(s.l[st:])); bot = float(s.l[bot_i])
        depth = rim - bot
        if depth < 5 * s.A or bot_i - st < 0.25 * W or st + W - bot_i < 0.25 * W:
            continue
        if s.c[-1] < bot + 0.5 * depth or float(np.std(y - fit)) > 0.12 * depth:
            continue
        stop = float(np.min(s.l[n - max(5, W // 4):])) - 0.1 * s.A
        pts = [[st, rim, "Sol kenar"], [bot_i, bot, "Dip"]]
        curve = [[st + int(i * (W - 1) / 12), float(A2 * (i / 12) ** 2 + B1 * (i / 12) + C0)] for i in range(13)]
        lines = [[st, rim, n - 1, rim, "res", "Kenar direnci"], ["curve", curve]]
        ck = [f"Kapanışlara ikinci derece eğri uyumu R² = {r2:.2f} (≥ 0,88)", f"Tepe/dip noktası pencerenin %{xv * 100:.0f}'inde (30–75)",
              f"Derinlik {fp(depth)} ≥ 5×ATR, eğriden sapma ≤ derinliğin %12'si", f"Pencere {W} bar"]
        res = _finish(s, "yuvarlak_dip", st, n - 2, lambda i, v=rim: v, stop, depth, pts, lines, ck, 50 + int(20 * (r2 - 0.88) / 0.12), bo_from=bot_i + 1)
        if res:
            out.append(res); return


BULL_DETS = (det_inv_hs, det_double, det_triple, det_cup, det_flag, det_round)


# ------------------------------------------------------------------ çizgi formasyonları (her iki yön)
def det_lines(s: S, P, out):
    conf = [p for p in P if not p[3]]
    if len(conf) < 4:
        return
    n = s.n
    for k in (6, 5):
        if len(conf) < k:
            continue
        seg = conf[-k:]
        Hs = [p for p in seg if p[2] == "H"]; Ls = [p for p in seg if p[2] == "L"]
        if len(Hs) < 2 or len(Ls) < 2:
            continue
        st, e = seg[0][0], seg[-1][0]
        if e - st < 10:
            continue
        uf = _fit([p[0] for p in Hs], [p[1] for p in Hs]); lf = _fit([p[0] for p in Ls], [p[1] for p in Ls])
        h0 = uf(st) - lf(st); h1 = uf(e) - lf(e)
        if h0 <= 0 or h1 <= 0:
            continue
        hm = max(h0, h1)
        if hm < 2 * s.A:
            continue
        # pivotların çizgilere uyumu
        if max(abs(p[1] - uf(p[0])) for p in Hs) > max(0.6 * s.A, 0.15 * hm) or max(abs(p[1] - lf(p[0])) for p in Ls) > max(0.6 * s.A, 0.15 * hm):
            continue
        # kapanışlar kanal içinde (son pivota kadar)
        tol = 0.35 * s.A
        cc = s.c[st:e + 1]; xi = np.arange(st, e + 1)
        if np.sum((cc > uf(xi) + tol) | (cc < lf(xi) - tol)) > 1:
            continue
        su = (uf(e) - uf(st)) / hm; sl = (lf(e) - lf(st)) / hm
        f = 0.2
        conv = h1 < 0.75 * h0; par = abs(h1 / h0 - 1) <= 0.3; div = h1 > 1.35 * h0
        key = None
        if abs(su) <= f and sl >= 0.3 and conv: key = "yukselen_ucgen"
        elif abs(sl) <= f and su <= -0.3 and conv: key = "alcalan_ucgen"
        elif su <= -0.25 and sl >= 0.25 and conv: key = "simetrik_ucgen"
        elif su > f and sl > f and conv: key = "yukselen_takoz"
        elif su < -f and sl < -f and conv: key = "alcalan_takoz"
        elif su > f and sl > f and par: key = "yukselen_kanal"
        elif su < -f and sl < -f and par: key = "alcalan_kanal"
        elif abs(su) <= f and abs(sl) <= f and par: key = "dikdortgen"
        elif su > f and sl < -f and div: key = "genisleyen"
        if not key:
            continue
        apex = None
        if conv:
            mu = (uf(e + 1) - uf(e)); ml = (lf(e + 1) - lf(e))
            if ml - mu > 1e-12:
                apex = e + (uf(e) - lf(e)) / (ml - mu)
            if apex is None or apex < e:
                continue
        # kırılım (son pivottan sonra, tepe noktasından önce)
        bo, bdir = None, 0
        for i in range(e + 1, n):
            if apex is not None and i > apex + 2:
                break
            if s.c[i] > uf(i) + 0.1 * s.A: bo, bdir = i, 1; break
            if s.c[i] < lf(i) - 0.1 * s.A: bo, bdir = i, -1; break
        if bo is None:
            if n - 1 - e > max(12, 0.6 * (e - st)):
                continue
            if apex is not None and n - 1 > apex:
                continue
        nm, en, d, typ = CP[key]
        touches = len(Hs) + len(Ls)
        q = 40 + min(20, (touches - 4) * 7 + 6) + int(10 * (1 - min(1, abs(su - sl) if par else 0)))
        if key in ("yukselen_kanal", "alcalan_kanal"):
            # kanal: içeride → kanal yönünde işlem; ters kırılım → BAŞARISIZ, aynı yönde kırılım → KIRILDI (hızlanma)
            up = key == "yukselen_kanal"
            j = n - 1
            if bo is not None and n - 1 - bo > MAX_AGE and not ((bdir > 0) != up):
                continue
            hh = uf(j) - lf(j)
            if up:
                entry, stop, t1, t2 = float(s.c[-1]), lf(j) - 0.25 * hh, uf(j), uf(j) + hh
            else:
                entry, stop, t1, t2 = float(s.c[-1]), uf(j) + 0.25 * hh, lf(j), lf(j) - hh
            status = "OLUŞUYOR"
            if bo is not None:
                status = "KIRILDI" if (bdir > 0) == up else "BAŞARISIZ"
                if status == "BAŞARISIZ" and n - 1 - bo > MAX_AGE:
                    continue
                if status == "KIRILDI":
                    entry = uf(bo) if up else lf(bo)
                    stop = lf(bo) if up else uf(bo)
                    t1 = entry + hh if up else entry - hh
                    t2 = entry + 1.618 * hh if up else entry - 1.618 * hh
            risk = abs(entry - stop)
            if risk <= 0 or (up and t1 <= entry and status == "OLUŞUYOR") or (not up and t1 >= entry and status == "OLUŞUYOR"):
                continue
            rr = abs(t1 - entry) / risk
            ddir = d
        else:
            if bo is not None:
                ddir = "U" if bdir > 0 else "D"
                if d != "N" and ddir != d:
                    # beklenenin tersine kırılım = başarısız formasyon
                    status, ddir = "BAŞARISIZ", d
                else:
                    status = "KIRILDI"
                if n - 1 - bo > MAX_AGE:
                    continue
            else:
                status = "OLUŞUYOR"
                if d == "N":
                    pre = s.c[max(0, st - 20)]
                    ddir = "U" if s.c[st] > pre else "D" if s.c[st] < pre else "N"
                else:
                    ddir = d
            up = (ddir == "U") if ddir != "N" else True
            j = bo if bo is not None else n - 1
            if key in ("yukselen_takoz", "alcalan_takoz"):
                height = h0
            elif key == "genisleyen":
                height = h1
            else:
                height = h0 if conv else hm
            if up:
                entry, stop = uf(j), (lf(j) if key not in ("yukselen_ucgen",) else Ls[-1][1]) - 0.1 * s.A
                t1 = entry + height
                if key == "alcalan_takoz":
                    t1 = max(uf(st), entry + 0.5 * height)
                t2 = entry + 1.618 * height
            else:
                entry, stop = lf(j), (uf(j) if key not in ("alcalan_ucgen",) else Hs[-1][1]) + 0.1 * s.A
                t1 = entry - height
                if key == "yukselen_takoz":
                    t1 = min(lf(st), entry - 0.5 * height)
                t2 = entry - 1.618 * height
            risk = abs(entry - stop)
            if risk <= 0:
                continue
            rr = abs(t1 - entry) / risk
            if status != "OLUŞUYOR":
                # stop sonrası bozulma
                for jj in range((bo or n) + 1, n):
                    if (up and s.c[jj] < stop) or ((not up) and s.c[jj] > stop):
                        status = "BAŞARISIZ"; break
        vc, vr = False, None
        if bo is not None:
            va = s.vavg(bo)
            if va > 0 and s.v[bo] > 0:
                vr = round(float(s.v[bo] / va), 2); vc = vr >= 1.5
        else:
            v1 = s.v[st:(st + e) // 2 + 1]; v2 = s.v[(st + e) // 2:e + 1]
            if len(v1) and len(v2) and v2.mean() < v1.mean():
                q += 5
        q += (15 if vc else 0) + (5 if 1 <= rr <= 6 else 0) - (10 if status == "BAŞARISIZ" else 0)
        lend = bo if bo is not None else n - 1
        if apex is not None:
            lend = min(lend, int(apex))
        pts = [[p[0], p[1], ("T" if p[2] == "H" else "D") + str(ix + 1)] for ix, p in enumerate(seg)]
        lines = [[Hs[0][0], uf(Hs[0][0]), lend, uf(lend), "res", "Üst çizgi"], [Ls[0][0], lf(Ls[0][0]), lend, lf(lend), "sup", "Alt çizgi"]]
        ck = [f"{len(Hs)} tepe üst çizgiye, {len(Ls)} dip alt çizgiye değiyor (sapma ≤ {fp(max(0.6 * s.A, 0.15 * hm))})",
              f"Üst çizgi eğimi {su:+.2f}, alt çizgi eğimi {sl:+.2f} (yüksekliğe göre)",
              f"Genişlik başta {fp(h0)}, sonda {fp(h1)} ({'daralan' if conv else 'genişleyen' if div else 'paralel'})",
              f"Kapanışlar {st}–{e} arası çizgilerin içinde", f"Yükseklik {fp(hm)} ≥ 2×ATR"]
        hit1 = bo is not None and ((float(np.max(s.h[bo:])) >= t1) if up else (float(np.min(s.l[bo:])) <= t1))
        out.append({"k": key, "durum": status, "bo": bo, "fail": None, "entry": entry, "stop": stop, "t1": t1, "t2": t2, "rr": round(rr, 2),
                    "vc": vc, "vr": vr, "hit1": hit1, "q": int(max(5, min(99, q))), "height": abs(t1 - entry), "start": st,
                    "pts": pts, "lines": lines, "checks": ck, "dir": ddir})
        return


def _unflip(r, s: S):
    """Aynalanmış sonucu gerçek fiyatlara çevir."""
    if not s.flip:
        return r
    r["k"] = MIRROR.get(r["k"], r["k"])
    for f in ("entry", "stop", "t1", "t2"):
        r[f] = -r[f]
    r["pts"] = [[p[0], -p[1], p[2]] for p in r["pts"]]
    nl = []
    for ln in r["lines"]:
        if ln[0] == "curve":
            nl.append(["curve", [[a, -b] for a, b in ln[1]]])
        else:
            nl.append([ln[0], -ln[1], ln[2], -ln[3], ln[4], ln[5]])
    r["lines"] = nl
    return r


def scan(b, n):
    """Bars + kapanmış bar sayısı → grafik formasyonları (dict listesi, anahtar başına en iyisi)."""
    if n < 40:
        return []
    st = max(0, n - WIN)
    t, o, h, l, c, v = b.t[st:n], b.o[st:n], b.h[st:n], b.l[st:n], b.c[st:n], b.v[st:n]
    if float(np.max(h) - np.min(l)) <= 0:
        return []
    res = []
    for flip in (False, True):
        s = S(t, o, h, l, c, v, flip)
        if s.A < 2 * tick_of(abs(float(c[-1]))):
            return []
        for kz in (1.5, 2.5):
            P = zigzag(s.h, s.l, s.a, kz)
            if len(P) < 3:
                continue
            got = []
            for det in BULL_DETS:
                try:
                    det(s, P, got)
                except Exception:   # pragma: no cover
                    pass
            if not flip:
                try:
                    det_lines(s, P, got)
                except Exception:   # pragma: no cover
                    pass
            for r in got:
                r.setdefault("dir", "D" if flip else "U")
                r = _unflip(r, s)
                r["zz"] = kz
                res.append(r)
    best = {}
    rank = {"KIRILDI": 3, "OLUŞUYOR": 2, "BAŞARISIZ": 1}
    for r in res:
        k = r["k"]
        sc = (rank[r["durum"]], r["q"])
        if k not in best or sc > best[k][0]:
            best[k] = (sc, r)
    out = []
    last = float(c[-1])
    for _sc, r in best.values():
        nm, en, d, typ = CP[r["k"]]
        d = r.get("dir") or d
        T = lambda i: int(t[i]) if i is not None and 0 <= i < len(t) else None
        res_d = {
            "k": r["k"], "ad": nm, "en": en, "yon": d, "tip": typ, "durum": r["durum"],
            "bo_t": T(r["bo"]), "bo_n": (len(t) - 1 - r["bo"]) if r["bo"] is not None else None, "fail_t": T(r.get("fail")),
            "giris": round(float(r["entry"]), 4), "stop": round(float(r["stop"]), 4), "h1": round(float(r["t1"]), 4), "h2": round(float(r["t2"]), 4), "rr": float(r["rr"]),
            "d_giris": round(float((r["entry"] - last) / last * 100), 2), "d_stop": round(float((r["stop"] - last) / last * 100), 2),
            "d_h1": round(float((r["t1"] - last) / last * 100), 2), "hacim": r["vc"], "hr": r["vr"], "h1_ok": bool(r["hit1"]), "kalite": r["q"],
            "pts": [[T(p[0]), round(float(p[1]), 4), p[2]] for p in r["pts"]],
            "lines": [(["curve", [[T(a), round(float(bb), 4)] for a, bb in ln[1]]] if ln[0] == "curve" else
                       [T(ln[0]), round(float(ln[1]), 4), T(ln[2]), round(float(ln[3]), 4), ln[4], ln[5]]) for ln in r["lines"]],
            "kontrol": r["checks"], "t0": T(r["start"]), "t": int(t[-1]), "c": last, "zz": r["zz"],
        }
        res_d["etki"] = chart_etki(res_d)
        out.append(res_d)
    out.sort(key=lambda r: ({"KIRILDI": 0, "OLUŞUYOR": 1, "BAŞARISIZ": 2}[r["durum"]], -r["kalite"]))
    return out


def chart_etki(r):
    m = MEANING.get(r["k"], "")
    up = r["h1"] > r["giris"]
    yn = "yukarı" if up else "aşağı"
    if r["durum"] == "KIRILDI":
        s = (f"{m} Kırılım gerçekleşti ({fp(r['giris'])} {yn}). Hedef 1: {fp(r['h1'])} (%{r['d_h1']:+.1f}), hedef 2: {fp(r['h2'])}. "
             f"STOP: {fp(r['stop'])} — bu seviyenin {'altında' if up else 'üstünde'} kapanış formasyonu bozar.")
        if r["h1_ok"]:
            s += " Hedef 1'e ulaşıldı."
    elif r["durum"] == "OLUŞUYOR":
        s = (f"{m} Henüz kırılım yok: {fp(r['giris'])} {'üzerinde' if up else 'altında'} kapanış teyit sayılır (şu an %{r['d_giris']:+.1f} uzakta). "
             f"Teyitte hedef 1: {fp(r['h1'])}, hedef 2: {fp(r['h2'])}; STOP: {fp(r['stop'])}.")
    else:
        s = f"{m} Formasyon BAŞARISIZ oldu: kırılım geri alındı / ters yönde kırıldı; beklenen hareket gerçekleşmedi. Ters yönlü baskıya dikkat."
    return s
