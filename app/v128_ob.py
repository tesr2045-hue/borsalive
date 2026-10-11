"""v1.28.0 — ORDER BLOCK (olası güçlü tepki bölgeleri) + FVG tespiti.

Tanım (gerçek, KAPANMIŞ barlar; v1.27 formasyon motorunun aynı bar serisi):
* Yükseliş OB (TALEP / destek): güçlü yukarı itkiden (displacement) hemen önceki SON DÜŞÜŞ mumu.
  - j: kırmızı mum (c<o), j+1 yeşil mum (itki başlangıcı).
  - İtki: j+1..j+3 içindeki ilk e barında  c[e] − o[j] ≥ 1,5 × ATR14[j]  VE  c[e] > son teyitli tepe (BOS, yapı kırılımı;
    j veya öncesinde oluşmuş, 2+2 bar fraktal tepe; e anında teyitli). İkisi birden sağlanmazsa OB değildir.
  - Bölge: o[j] (gövde üstü) → l[j] (fitil dibi). Gövde+fitil: likiditenin alındığı fitil dahil, karşı fitil hariç.
    Orta çizgi (mean threshold) = (üst+alt)/2.
* Düşüş OB (ARZ / direnç): ayna — son yükseliş mumu (c>o), ardından düşüş itkisi o[j] − c[e] ≥ 1,5 ATR ve c[e] < son teyitli dip;
  bölge h[j] (fitil tepesi) → o[j] (gövde altı).
* Durum (itki sonrası barlarda): TAZE (hiç dönülmedi) · TEST EDİLDİ (n) (fiyat bölgeye her yeniden girişi = 1 test, fitil yeter)
  · KIRILDI/GEÇERSİZ (KAPANIŞ bölgenin karşı ucunun ötesinde: talepte c < alt, arzda c > üst). Derinlik: bölgeye en derin giriş %.
* Güç (0–99): itki/ATR (35) + itki hacmi / önceki 20 bar ort. (20) + itkide FVG (15) + tazelik (20: 0 test=1, 1=0,6, 2=0,35, 3+=0,1)
  + yakınlık-yenilik (10).
* FVG (dengesizlik): 3 mum boşluğu — yükselişte l[k+1] > h[k−1], düşüşte h[k+1] < l[k−1]; sonradan fiyat boşluğu tam doldurunca kapanır.
"""
from __future__ import annotations

import numpy as np

IMP_ATR = 1.5          # itki eşiği (ATR)
IMP_MAX_BARS = 3       # itki en çok kaç bar sürebilir
FR = 2                 # fraktal yarı genişliği (pivot)
PIV_LOOK = 60          # BOS için geriye en çok kaç bar içinde pivot aranır
MAX_SHOW = 3

DEF_TXT = ("Order block = güçlü, yapı kıran bir itkiden (≥1,5×ATR ve son tepe/dip kapanışla aşıldı) hemen önceki son ters mum. "
           "Bölge: talepte gövde üstü→fitil dibi (açılış→düşük), arzda fitil tepesi→gövde altı (yüksek→açılış). "
           "TAZE = hiç dönülmedi, TEST EDİLDİ (n) = fiyat bölgeye n kez geri girdi, KIRILDI = kapanış bölgenin ötesinde (geçersiz). "
           "Güç: itki/ATR, itki hacmi, FVG (boşluk), tazelik ve yenilik. Olası tepki bölgesidir; garanti değildir.")


def _atr(h, l, c, n=14):
    pc = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    out = np.empty(len(tr))
    m = tr[0] if len(tr) else 0.0
    for i in range(len(tr)):
        m = tr[i] if i == 0 else (m * (n - 1) + tr[i]) / n
        out[i] = m
    return out


def _pivots(h, l, k=FR):
    n = len(h)
    ph, pl = [], []
    for i in range(k, n - k):
        wh = h[i - k:i + k + 1]; wl = l[i - k:i + k + 1]
        if h[i] == wh.max() and (h[i] > h[i - k:i]).all():
            ph.append(i)
        if l[i] == wl.min() and (l[i] < l[i - k:i]).all():
            pl.append(i)
    return np.array(ph, dtype=int), np.array(pl, dtype=int)


def _last_pivot(piv, upto, confirm_by, look):
    """upto (dahil) ve öncesindeki, confirm_by anında teyitli (p+FR <= confirm_by) en son pivot."""
    if not len(piv):
        return None
    k = int(np.searchsorted(piv, upto, side="right")) - 1
    while k >= 0:
        p = int(piv[k])
        if p + FR <= confirm_by:
            return p if upto - p <= look else None
        k -= 1
    return None


def detect(o, h, l, c, v, t=None, n=None):
    """OB + FVG tespiti. Diziler numpy; n = kapanmış bar sayısı. Dönüş: dict (zones: tüm bölgeler, durumlarıyla)."""
    n = len(c) if n is None else n
    o, h, l, c, v = (np.asarray(x[:n], dtype=float) for x in (o, h, l, c, v))
    t = np.asarray(t[:n]) if t is not None else np.arange(n)
    out = {"zones": [], "fvg": [], "n": n}
    if n < 30:
        return out
    A = _atr(h, l, c)
    ph, pl = _pivots(h, l)
    vavg = np.convolve(v, np.ones(20) / 20, mode="full")[:n]       # v[i-19..i] ortalaması
    p_now = float(c[-1])
    zones = []
    for j in range(20, n - 1):
        a = float(A[j]) or 1e-9
        for side in (1, -1):
            if side == 1 and not (c[j] < o[j] and c[j + 1] > o[j + 1]):
                continue
            if side == -1 and not (c[j] > o[j] and c[j + 1] < o[j + 1]):
                continue
            piv = ph if side == 1 else pl
            e_ok = None
            for e in range(j + 1, min(j + 1 + IMP_MAX_BARS, n)):
                disp = (c[e] - o[j]) if side == 1 else (o[j] - c[e])
                if disp < IMP_ATR * a:
                    continue
                p = _last_pivot(piv, j, e, PIV_LOOK)
                if p is None:
                    continue
                lvl = h[p] if side == 1 else l[p]
                if (side == 1 and c[e] > lvl) or (side == -1 and c[e] < lvl):
                    e_ok = (e, float(disp), float(lvl), p)
                    break
            if e_ok is None:
                continue
            e, disp, bos, p = e_ok
            if side == 1:
                top, bot = float(max(o[j], c[j])), float(l[j])
            else:
                top, bot = float(h[j]), float(min(o[j], c[j]))
            if top - bot <= 0:
                continue
            # itkide FVG
            fvg = None
            for k in range(j + 1, min(e, n - 2) + 1):
                if side == 1 and l[k + 1] > h[k - 1]:
                    fvg = (float(h[k - 1]), float(l[k + 1]), k); break
                if side == -1 and h[k + 1] < l[k - 1]:
                    fvg = (float(h[k + 1]), float(l[k - 1]), k); break
            pre = vavg[j] if j >= 19 else float(np.mean(v[:j + 1]))
            vr = float(np.mean(v[j + 1:e + 1]) / pre) if pre > 0 else None
            # durum takibi
            st_i = e + 1
            sc, sl_, sh = c[st_i:], l[st_i:], h[st_i:]
            if side == 1:
                brk = np.nonzero(sc < bot)[0]
                end = int(brk[0]) if len(brk) else len(sc)
                inside = sl_[:end + (1 if len(brk) else 0)] <= top
                prev_in = bool(l[e] <= top)
                depth = float(np.max((top - sl_[:end + (1 if len(brk) else 0)]) / (top - bot))) if len(sl_) else 0.0
            else:
                brk = np.nonzero(sc > top)[0]
                end = int(brk[0]) if len(brk) else len(sc)
                inside = sh[:end + (1 if len(brk) else 0)] >= bot
                prev_in = bool(h[e] >= bot)
                depth = float(np.max((sh[:end + (1 if len(brk) else 0)] - bot) / (top - bot))) if len(sh) else 0.0
            ins = inside[:end] if len(brk) else inside
            if len(ins):
                rising = np.diff(np.concatenate([[prev_in], ins]).astype(int))
                tests = int((rising == 1).sum())
            else:
                tests = 0
            broken = bool(len(brk))
            bi = st_i + int(brk[0]) if broken else None
            fresh = 1.0 if tests == 0 else 0.6 if tests == 1 else 0.35 if tests == 2 else 0.1
            age = (n - 1) - j
            imp = disp / a
            score = (35 * min(1.0, (imp - IMP_ATR) / 2.5 + 0.3) + 20 * (min(1.0, max(0.0, ((vr or 1) - 0.8) / 1.7))) + (15 if fvg else 0)
                     + 20 * fresh + 10 * max(0.0, 1 - age / max(60, n)))
            zones.append({
                "yon": "U" if side == 1 else "D", "j": j, "e": e, "t": int(t[j]), "te": int(t[e]), "top": top, "bot": bot,
                "mid": (top + bot) / 2, "imp": round(imp, 2), "vr": round(vr, 2) if vr else None, "fvg": [fvg[0], fvg[1], int(t[fvg[2]])] if fvg else None,
                "bos": bos, "bos_t": int(t[p]), "tests": tests, "depth": round(max(0.0, min(1.0, depth)) * 100) if len(sc) else 0,
                "durum": "KIRILDI" if broken else ("TAZE" if tests == 0 else "TEST EDİLDİ"), "brk_t": int(t[bi]) if broken else None,
                "skor": int(max(1, min(99, round(score)))), "age": int(age),
            })
    # FVG listesi (doldurulmamış)
    fv = []
    for k in range(1, n - 1):
        if l[k + 1] > h[k - 1]:
            lo, hi, yon = float(h[k - 1]), float(l[k + 1]), "U"
            later = l[k + 2:]
            filled = bool(len(later) and later.min() <= lo)
        elif h[k + 1] < l[k - 1]:
            lo, hi, yon = float(h[k + 1]), float(l[k - 1]), "D"
            later = h[k + 2:]
            filled = bool(len(later) and later.max() >= hi)
        else:
            continue
        if not filled and (hi - lo) >= 0.15 * float(A[k]):
            fv.append({"yon": yon, "lo": lo, "hi": hi, "t": int(t[k]), "k": k})
    out["zones"] = zones
    out["fvg"] = fv
    out["atr"] = float(A[-1])
    out["p"] = p_now
    return out


def _overlap(a, b):
    lo, hi = max(a["bot"], b["bot"]), min(a["top"], b["top"])
    if hi <= lo:
        return 0.0
    return (hi - lo) / max(1e-9, min(a["top"] - a["bot"], b["top"] - b["bot"]))


def summarize(res, keep=MAX_SHOW):
    """Fiyatın üstündeki en yakın ARZ (direnç) ve altındaki en yakın TALEP (destek) bölgeleri (geçerli olanlar)."""
    p = res.get("p")
    zs = [z for z in res.get("zones", []) if z["durum"] != "KIRILDI"]
    # örtüşen aynı yönlü bölgelerden güçlüsünü tut
    zs.sort(key=lambda z: -z["skor"])
    kept = []
    for z in zs:
        if any(k["yon"] == z["yon"] and _overlap(k, z) > 0.5 for k in kept):
            continue
        kept.append(z)
    for z in kept:
        if z["bot"] <= p <= z["top"]:
            z["d"] = 0.0; z["ic"] = True
        elif z["top"] < p:
            z["d"] = round((z["top"] / p - 1) * 100, 2); z["ic"] = False
        else:
            z["d"] = round((z["bot"] / p - 1) * 100, 2); z["ic"] = False
    # talep fiyatın altında/içinde; arz üstünde/içinde (kırılmamış talep zaten c>=alt)
    dem = sorted([z for z in kept if z["yon"] == "U" and z["bot"] <= p], key=lambda z: abs(z["d"]))[:keep]
    sup = sorted([z for z in kept if z["yon"] == "D" and z["top"] >= p], key=lambda z: abs(z["d"]))[:keep]
    # yön dışı kalanlar (fiyat tamamen ötesinde ama kapanışla kırmamış — ör. arz fiyatın altında kaldıysa zaten kırılmıştır)
    br = sorted([z for z in res.get("zones", []) if z["durum"] == "KIRILDI"], key=lambda z: -(z["brk_t"] or 0))[:3]
    fv = res.get("fvg") or []
    fvu = sorted([f for f in fv if f["lo"] >= p], key=lambda f: f["lo"] - p)[:2]
    fvd = sorted([f for f in fv if f["hi"] <= p], key=lambda f: p - f["hi"])[:2]
    fvi = [f for f in fv if f["lo"] < p < f["hi"]][:1]
    return {"p": p, "atr": res.get("atr"), "sup": sup, "dem": dem, "kirik": br, "fvg": fvi + fvu + fvd,
            "n": {"tum": len(res.get("zones", [])), "gecerli": len(kept), "kirik": sum(1 for z in res.get("zones", []) if z["durum"] == "KIRILDI"),
                  "taze": sum(1 for z in kept if z["durum"] == "TAZE"), "fvg": len(fv)}}


def strip(z):
    """API için sade bölge (indeks alanları hariç)."""
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in z.items() if k not in ("j", "e", "age")}
