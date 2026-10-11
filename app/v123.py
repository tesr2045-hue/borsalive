"""v1.23.0 — MALİYET YÜKSELTEN KURUMLAR (Kurum Ayak İzi).

İşlem kaydı (TradeStore / diske kaydedilmiş gün) işlem işlem, saniye hassasiyetinde taranır; zaman kovası YOK.
Her (hisse, alıcı kurum) için: ilk ayak izi, her alıştan sonra kümülatif ortalama maliyet, maliyet yükseltme olayları,
agresiflik (aktif alış), fiyat etkisi (alıştan 10 sn / 60 sn sonraki fiyat), hacim payı, süreklilik ve 0-100 ciddiyet skoru.

* Canlı seansta artımlı: her hisse için yalnızca yeni gelen işlemler işlenir (ptr), snapshot birleştirmesinde
  (geçmişe işlem eklenmesi) o hisse baştan hesaplanır. Hesap arka plan iş parçacığında yapılır, API önbellekten döner.
* Bugün işlem yoksa (hafta sonu / seans öncesi) son kayıtlı seans, ?date=YYYYMMDD ile istenen kayıtlı gün kullanılır.
"""
from __future__ import annotations

import bisect
import collections
import logging
import math
import threading
import time

from app.live_store import TRADES_DIR
from app.v122 import (CONT_FROM, CONT_TO, C, DiskDay, _clip, _day_label, _fold, _fp, _fs, _hm, _hms, _last_disk_day,
                      _pc, _sec_now, _today)

logger = logging.getLogger("v123")
VERSION = "1.24.0"
FID = "k_maliyet"
NT = "k_maliyet"
TITLE = "Maliyet Yükselten Kurumlar (Kurum Ayak İzi)"
SHORT = "MALİYET↑"
DESC = ("Seans açılışından beri alış tarafında maliyetini YÜKSELTEN kurumlar: ilk ayak izi, her alıştan sonra kümülatif ortalama, "
        "maliyet yükseltme olayları, aktif alış, fiyat etkisi ve ciddiyet skoru — işlem işlem, saniye saniye.")
NT_DEFAULTS = {NT: "notify"}

OPEN_END = 11 * 3600          # "açılış saati" ortalaması: 11:00'den önceki alışlar
FIRST_N = 10                  # ilk N alış ortalaması
STILL_MIN = 15                # son N dk içinde alış → "hâlâ alıyor"
MIN_TL = 250_000              # listeye girmek için minimum alış tutarı
H1, H2 = 10, 60               # fiyat etkisi ufukları (sn)
HW0 = 10 * 3600               # v1.23.1: yarım saatlik pencereler 10:00'dan başlar (açılış seansı ilk pencereye)
EPS = 1e-9

WINDOWS = [["tum", "TÜMÜ"], ["ciddi", "CİDDİ YÜKSELİŞ"], ["tavan", "TAVAN ADAYI"], ["israr", "ISRARCI"], ["still5", "HÂLÂ ALIYOR + ≥5 Mn ₺"], ["1m", "≥1 Mn ₺"], ["5m", "≥5 Mn ₺"], ["20m", "≥20 Mn ₺"], ["yuk", "MALİYET ↑"],
           ["s50", "SKOR ≥50"], ["s70", "SKOR ≥70"], ["still", "HÂLÂ ALIYOR"], ["ilk", "YENİ AYAK İZİ"]]
WDEF = "tum"

HELP = {
    "ne": ("Bir hissede seans açılışından beri alıcı olan ve alım yaparken maliyetini sürekli YUKARI taşıyan kurumları (kurumsal ilk ayak izlerini) "
           "işlem işlem tespit eder. AKD'deki gün sonu ortalama maliyeti tek başına yanıltıcı olabilir: aynı ortalama, sabah ucuzdan toplayıp bırakan "
           "kurumda da, gün boyu fiyatı kovalayan kurumda da çıkar. Burada her alışın sırası, saati (saniye), fiyatı, lotu ve etkisi ayrı ayrı izlenir."),
    "nasil": ("Zaman kovası yoktur; kurumun her alışı sırayla işlenir. İlk ayak izi = günün ilk alışı (saat:dk:sn, fiyat, lot). Her alıştan sonra kümülatif "
              "ortalama = toplam alış ₺ ÷ toplam alış lotu. Maliyet yükseltme olayı = alış fiyatı bir önceki kümülatif ortalamanın veya kurumun o ana kadarki "
              "en yüksek alış fiyatının üstünde. Maliyet artışı % = şu anki ortalama ÷ ilk ayak izi fiyatı − 1; İlk 10'dan % = ortalama ÷ ilk 10 alışın ortalaması − 1. "
              "Aktif alış % = satıcının emrine vurarak (aktif alış) alınan lot payı; aktif seri = art arda aktif alış sayısı; süpürme = aynı saniyede birden çok fiyat "
              "kademesini aktif alışla tüketme. Fiyat etkisi = alıştan 10 sn ve 60 sn sonraki hisse fiyatının alış fiyatına göre değişimi (lot ağırlıklı). "
              "Yükselişe katkı % = hissenin gün içindeki tüm yukarı fiyat adımlarının bu kurumun aktif alışlarıyla gerçekleşen payı. Hacim payı % = kurum alış lotu ÷ "
              "hissenin toplam işlem lotu. Ciddiyet skoru (0-100): maliyet artışı 20 + yükseltme oranı 10 + hacim payı 15 + alış tutarı 8 + aktif alış 12 + "
              "süpürme 5 + yükselişe katkı 10 + 60 sn fiyat etkisi 5 + süreklilik (alış yapılan farklı dakika) 10 + hâlâ alıyor 5; toplam, net alış oranıyla "
              "(net lot ÷ alış lotu) 0,5-1 arasında çarpılır. Yalnızca bugün NET ALICI olan ve en az 250 bin ₺ alan kurumlar listelenir."),
    "nasil_kullan": ("Skora göre sıralayın; satıra dokunun → o kurumun o hissedeki saniye saniye maliyet grafiği (kümülatif ortalama vs fiyat, alışlar lot büyüklüğünde, "
                     "yükseltme olayları turuncu halkalı) ve işlem işlem tam liste açılır. 'YENİ AYAK İZİ' filtresi son 15 dk'da ilk alışını yapıp ciddi başlayan kurumları, "
                     "'HÂLÂ ALIYOR' son 15 dk'da alış yapmaya devam edenleri gösterir. Maliyetini yükselterek, aktif alışla, yüksek hacim payıyla ve uzun süre alan kurum "
                     "çoğunlukla fiyatı umursamayan, ciddi bir alıcıdır. Bildirim: skor 70 eşiğini geçtiğinde veya yeni ve ciddi bir ilk ayak izi oluştuğunda "
                     "(her hisse+kurum için günde bir kez)."),
    "dikkat": ("Aracı kurum kimliği müşteri kimliği değildir: büyük bir aracı kurumdaki alışlar birçok küçük yatırımcının toplamı olabilir. Aktif/pasif bilgisi "
               "işlem bazında veri akışından gelir; açılış seansı (09:55-10:00) işlemleri ne aktif ne pasiftir. Kayıt bazı hisselerde 10:00 sürekli işlem açılışından "
               "birkaç saniye/dakika sonra başlamış olabilir (detayda 'kayıt başlangıcı' gösterilir): bu durumda gerçek ilk ayak izi daha erken olabilir. "
               "Fiyat etkisi korelasyondur, nedensellik değildir. Yatırım tavsiyesi değildir."),
    "ornek": "",
}

# v1.23.1 — ayrıntılı kullanım rehberi (Açıklama panelinde açılır-kapanır alt bölümler)
GUIDE = [
    {"t": "Adım adım kullanım (önerilen akış)", "p": [
        "1) Üstteki SEANS satırından hangi günün gösterildiğine bakın: seans saatinde CANLI, hafta sonu / seans öncesi son kayıtlı seans (ör. 02.10.2026 Cuma).",
        "2) ISRARCI butonuna dokunun: liste Israr skoruna göre sıralanır (yalnızca Israr ≥40). Hızlı ciddiyet taraması için Skor sütun başlığına dokunun (en yüksek üstte; ikinci dokunuş tersine çevirir).",
        "3) HÂLÂ ALIYOR + ≥5 Mn ₺ butonu: son 15 dakikada hâlâ alış yapan ve en az 5 Mn ₺ almış kurumları bırakır. Sonra Skor veya Israr skoru başlığına dokunarak sıralayın.",
        "4) Alış dakikası ve Süre sütunlarına bakın: alış yapılan farklı dakika sayısı ne kadar yüksekse ve ilk-son alış arası ne kadar uzunsa ısrar o kadar gerçektir (ör. KORDS · Midas 309 dakika, 8 sa 07 dk).",
        "5) Maliyet artışı % ve Yükseltme: kurum fiyat yükselirken almaya devam ediyor mu? Pozitif ve büyüyen maliyet artışı + yüksek yükseltme sayısı = fiyatı kovalayan alıcı.",
        "6) Aktif alış % 60'ın üstündeyse kurum satıcının emrine vurarak (süpürerek) alıyor, yani acelesi var.",
        "7) Hâlâ alıyor = ● EVET olmalı: alım bitmişse (—) hareket de bitmiş olabilir.",
        "8) Yükseltme yayılımı: '13/17 yarım saat' gibi yüksek oran, maliyet yükseltmelerin gün boyuna dağıldığını; '1/1' veya '1/2' ise tek bir anda toplandığını gösterir.",
        "9) Satıra dokunun → detay. Turuncu halkalar (maliyet yükseltme) gün boyuna yayılmışsa GERÇEK ISRAR; tek bir bölgede kümelenmişse TEK SEFERLİK VURUŞ. Grafiğin altındaki yarım saat şeridi bunu sayıyla gösterir.",
        "10) Günlük değ. % ile karşılaştırın: hisse zaten +%9-10 (tavana yakın) ise geç kalınmış olabilir; ısrarcı alıcı var ama hisse hâlâ düşük artıdaysa izlemeye değer.",
        "11) Takip etmek için Bildirim Ayarları → KURUM → 'Maliyet yükselten kurum' türünü BİLDİRİM yapın (skor 70'i geçince veya yeni ciddi ilk ayak izinde, hisse+kurum başına günde bir kez).",
    ]},
    {"t": "Önemli sütunlar ve iyi / kötü eşikler", "p": [
        "• Skor (ciddiyet): ≥70 güçlü · 50-70 izlemeye değer · <40 zayıf.",
        "• Israr skoru: ≥70 → Durum'da ISRARCI rozeti · 50-70 orta · <40 kısa / tek seferlik.",
        "• Günlük değ. %: hissenin bugünkü değişimi (canlı kotasyon; geçmiş seansta kapanış ÷ önceki kapanış). Yeşil artı, kırmızı eksi.",
        "• Maliyet artışı %: >+2 SERT YÜKSELTİYOR · +0,5…+2 YÜKSELTİYOR · ±0,5 SABİT MALİYET · <−0,5 DÜŞÜREREK TOPLUYOR (düşüşte toplama).",
        "• Yükseltme ÷ Alış adedi: %50'nin üstü → alışların çoğu ortalamanın üstünde, fiyat kovalanıyor.",
        "• Yükseltme yayılımı: alış dönemindeki yarım saatlerin %60'ından fazlasında yükseltme varsa iyi; 1-2 pencereye sıkışmışsa kümelenme.",
        "• Aktif alış %: >60 acele / süpürme · 40-60 karışık · <40 pasif (alış emri yazıp bekliyor, sabırlı toplama olabilir).",
        "• Aktif seri / Süpürme: seri 20+ ve süpürme 10+ agresif alıcı işaretidir.",
        "• Hacim payı %: >15 hissenin ana alıcısı · 5-15 belirgin · <3 küçük oyuncu.",
        "• Alış ₺: <1 Mn ₺ gürültü olabilir · ≥5 Mn ₺ ciddi · ≥20 Mn ₺ büyük oyuncu (hissenin büyüklüğüne göre yorumlayın).",
        "• Alış dakikası: ≥120 çok ısrarlı · 30-120 orta · <15 kısa süreli.",
        "• Süre: ilk ve son alış arası; ≥4 saat gün boyu demektir.",
        "• Fiyat etkisi 60 sn %: > +0,2 alışlar fiyatı kaldırıyor · negatifse satıcılar alımı emiyor.",
        "• Yükselişe katkı %: >30 → günün yükselişinin ana motoru bu kurumun aktif alışları.",
        "• İlk ayak izi: erken (10:00-10:30) başlayıp hâlâ alan = gün boyu plan. Geç ilk ayak izi + yüksek skor = yeni giriş (YENİ AYAK İZİ filtresi).",
    ]},
    {"t": "Detay grafiği nasıl okunur?", "p": [
        "• Mavi çizgi: hisse fiyatı, saniye saniye (her saniyenin son işlemi).",
        "• Sarı basamaklı çizgi: kurumun kümülatif ortalama maliyeti; her alışta bir basamak oluşur.",
        "• Yeşil nokta: aktif alış (satıcının emrine vurarak) · gri nokta: pasif alış (bekleyen alış emrinin dolması). Nokta büyüklüğü lot miktarıdır.",
        "• Turuncu halka: maliyet yükseltme (önceki ortalamanın üstünde alış) · kırmızı halka: kurumun o ana kadarki en yüksek alış fiyatını aşan yeni zirve alış.",
        "• Küçük kırmızı kare: kurumun aynı hissedeki satışı.",
        "• Sarı çizgi yukarı eğimli ve fiyat üstünde: kurum kârda ve hâlâ maliyet yükseltiyor → güçlü talep. Fiyat sarı çizginin altına inerse kurum zararda: ya savunur (alım sürer) ya bırakır.",
        "• Yayılım mı küme mi? Turuncu halkalar ALIŞ DÖNEMİ / TÜM GÜN aralığında baştan sona dağılmışsa gerçek ısrar; tek bir 10-15 dakikalık bölgede toplanıp sonra kesiliyorsa tek seferlik vuruş. Grafiğin altındaki YARIM SAAT ŞERİDİ her 30 dakikadaki alış ve yükseltme sayısını gösterir.",
        "• Aralık butonları: ALIŞ DÖNEMİ (varsayılan), TÜM GÜN, İLK AYAK İZİ +60 DK, SON 60 DK. Noktanın üstüne gelince / dokununca saat, fiyat, lot ve ortalama görünür.",
        "• İşlem listesinde YÜKSELTMELER filtresi yalnızca maliyeti yükselten alışları gösterir; turuncu/kırmızı sol çizgi yükseltme / yeni zirve demektir.",
    ]},
    {"t": "Skor ile Israr skoru farkı", "p": [
        "• Skor (ciddiyet) bugünkü alımın ne kadar SERT ve ETKİLİ olduğunu ölçer: maliyet artışı, yükseltme oranı, hacim payı, tutar, aktif alış, süpürme, yükselişe katkı, fiyat etkisi, alış dakikası, hâlâ alıyor. Kısa sürede çok sert alım da yüksek Skor alır.",
        "• Israr skoru alımın ne kadar SÜREKLİ olduğunu ölçer: süre 20 (4 saat = tam) + farklı alış dakikası 20 (120 dk = tam) + yükseltme yayılımı 25 [(yükseltmeli yarım saat ÷ alış dönemindeki yarım saat + yükseltme zamanlarının normalize entropisi) ÷ 2, en az 4 yarım saat için tam] + aktif alış 10 + tutar 15 + hâlâ alıyor 10; toplam (0,6 + 0,4 × net lot ÷ alış lotu) ile çarpılır.",
        "• Yüksek Skor + düşük Israr = tek seferlik sert vuruş (ör. KLRHO · Bank Of America). Düşük/orta Skor + yüksek Israr = fiyatı itmeden sabırlı toplama (ör. GARAN · Ünlü). İkisi de ≥70 = en güçlü durum (ör. KORDS · Midas, AVPGY · Aktif Yatırım).",
    ]},
    {"t": "Cuma (02.10.2026) gerçek örnekleri", "p": [
        "• GERÇEK ISRAR — AVPGY · Aktif Yatırım: ilk ayak izi 10:01:02, son alış 18:08:00 (8 sa 06 dk), 154 alış dakikası; 862 alışın 832'si maliyeti yükseltti, yükseltme yayılımı 17/17 yarım saat (en yoğun yarım saat yükseltmelerin yalnızca %18'i). Aktif alış %77,6, hacim payı %45,4, 22,4 Mn ₺, ortalama +%1,77. Skor 80 · Israr 94 · hisse günü +%3,63 kapattı.",
        "• ISRARCI + SERT — KORDS · Midas: 10:01:55'te 2,83 ₺'den ilk ayak izi; 2.676 alışın 2.574'ü yükseltme, ortalama 2,83 → 2,994 ₺ (+%5,80), aktif %73,5, 116 süpürme, 309 alış dakikası, 8 sa 07 dk, yayılım 13/17 yarım saat, hacim payı %22,5, net 11,96 Mn lot. Skor 81 · Israr 81 · hisse +%7,04.",
        "• TEK SEFERLİK VURUŞ — KLRHO · Bank Of America: 10:00:52-10:15:33 arasında (14 dk, 16 alış dakikası) 826 alış, 807 yükseltme, aktif %94, 24,25 Mn ₺, ortalama 10,45 → 10,90 ₺ (+%4,31). Skor 73 ama Israr yalnızca 26: yayılım 1/1 yarım saat, yükseltmelerin %100'ü tek pencerede, 10:15'ten sonra hiç alış yok. Hisse günü +%9,95 kapattı ama kurumun alımı ilk çeyrek saatte bitti.",
        "• SABIRLI TOPLAMA — GARAN · Ünlü: 419 alış dakikası, 7 sa 56 dk, aktif %92,9, 95,6 Mn ₺, yayılım 12/16 yarım saat ama maliyet yalnızca +%0,12 (SABİT MALİYET) → Skor 49, Israr 92. Fiyatı itmeden gün boyu toplayan kurum: Skor sıralamasında kaçar, ISRARCI sıralamasında üstte çıkar.",
    ]},
]
PRESET_DOC = [
    "Bu iki buton, hisse düzeyindeki hazır senaryoyu (POC Baskısı / Alış Ortalama Baskısı tarayıcılarındaki CİDDİ YÜKSELİŞ / TAVAN ADAYI koşulları) "
    "kurum düzeyindeki maliyet yükseltme kanıtıyla birleştirir.",
    "CİDDİ YÜKSELİŞ: hisse, POC veya aktif alış ortalaması için CİDDİ YÜKSELİŞ koşullarını sağlıyor (gün ≥ +%3, fiyat seviyede/üstünde, aktif alış ≥ %50, "
    "≥3 Mn ₺ işlem, saat ≥10:30 ve 7 opsiyonelden ≥5'i) VE bu kurum: maliyet artışı > 0, en az 2 maliyet yükseltmesi, ≥1 Mn ₺ alış ve ciddiyet skoru ≥40 "
    "(02.10.2026 Cuma: 96 kurum satırı, 27 hisse).",
    "TAVAN ADAYI: hisse TAVAN ADAYI koşullarını sağlıyor (gün ≥ +%5, tavana ≤ %4, fiyat seviyede/üstünde, aktif alış ≥ %55, momentum, son 30 dk ≥3 süpürme, "
    "≥5 Mn ₺, saat ≥10:30 ve 5 opsiyonelden ≥2'si) VE kurum maliyetini yükseltiyor (artış > 0, ≥2 yükseltme, ≥1 Mn ₺) VE hâlâ alıyor (son 15 dk) "
    "(02.10.2026 Cuma: 22 kurum satırı, 7 hisse).",
    "Senaryo ✓/✗ sütunu hisse koşullarını (Z zorunlu, O opsiyonel, B bonus) ve kurum koşullarını (K) gösterir; 'Bu kurum ısrarcı (Israr ≥70)' bonus kanıttır. "
    "Tüm koşulların tam tanımı POC Baskısı / Alış Ortalama Baskısı açıklamasında 'Hazır senaryolar' başlığındadır.",
]

GUIDE_WARN = [
    "• Aracı kurum ≠ tek yatırımcı: Midas, İş Yatırım, Yapı Kredi, Garanti gibi bireysel ağırlıklı kurumlardaki alışlar binlerce müşterinin toplamı olabilir. Bu kurumlarda yüksek ısrar 'kalabalığın' alımı da olabilir; yabancı / kurumsal ağırlıklı kurumlarda (ör. Bank Of America, YFAS, Ünlü) sinyal daha anlamlıdır.",
    "• Kayıt başlangıç boşluğu: bazı hisselerde işlem kaydı 10:00 sürekli işlem açılışından birkaç saniye-dakika sonra başlar (Cuma: 428 hissede 10:00-10:01:41). Bu hisselerde gerçek ilk ayak izi daha erken olabilir; detayda 'kayıt başlangıcı' yazar.",
    "• Korelasyon nedensellik değildir: fiyat etkisi ve yükselişe katkı, alışlar ile fiyat hareketinin birlikte olduğunu gösterir, alışın fiyatı tek başına yükselttiğini kanıtlamaz.",
    "• Net alıcı filtresi: yalnızca bugün net alıcı (alış lotu > satış lotu) ve ≥250 bin ₺ alan kurumlar listelenir; aynı kurum gün içinde hem alıp hem satabilir (Alış / satış ₺ detayda).",
    "• Tavan / taban: hisse tavana kilitlendiğinde aktif alış ve yükseltme sayıları anlamını yitirir (tek fiyattan işlem).",
    "• Günlük değ. %: canlıda kotasyondan; geçmiş seansta günlük bar deposundan (kapanış ÷ önceki kapanış), bulunamazsa kotasyon veya önceki kayıtlı günün son işlemi kullanılır.",
    "• Aktif/pasif işlem bazında veri akışından gelir; açılış seansı (09:55-10:00) işlemleri ne aktif ne pasiftir. Yatırım tavsiyesi değildir.",
]


def _n(v) -> str:
    return f"{int(v or 0):,}".replace(",", ".")


def _d(v, k=1) -> str:
    return f"{float(v or 0):.{k}f}".replace(".", ",")


def _fmt_span(sec: int) -> str:
    sec = max(0, int(sec))
    h, m = sec // 3600, (sec % 3600) // 60
    return f"{h} sa {m:02d} dk" if h else (f"{m} dk" if m else f"{sec} sn")


class BS:
    """Bir hissede bir kurumun gün içi alış/satış birikimi (işlem işlem)."""
    __slots__ = ("nb", "lot", "tl", "ft", "fp", "fl", "mx", "ys", "yh", "yt", "lt", "lp", "lmin", "nsec", "nmin",
                 "alot", "an", "stk", "mstk", "sw", "swt", "swp", "swc", "big", "bigp", "bigt", "ohl", "oht", "nl", "ntl",
                 "slot", "stl", "up", "i1s", "i1w", "i2s", "i2w", "bw", "rw", "rc")

    def __init__(self) -> None:
        self.nb = 0; self.lot = 0; self.tl = 0.0
        self.ft = -1; self.fp = 0.0; self.fl = 0; self.mx = 0.0
        self.ys = 0; self.yh = 0; self.yt = -1
        self.lt = -1; self.lp = 0.0; self.lmin = -1; self.nsec = 0; self.nmin = 0
        self.alot = 0; self.an = 0; self.stk = 0; self.mstk = 0
        self.sw = 0; self.swt = -1; self.swp = 0.0; self.swc = False
        self.big = 0; self.bigp = 0.0; self.bigt = -1
        self.ohl = 0; self.oht = 0.0; self.nl = 0; self.ntl = 0.0
        self.slot = 0; self.stl = 0.0; self.up = 0.0
        self.i1s = 0.0; self.i1w = 0; self.i2s = 0.0; self.i2w = 0
        self.bw = 0; self.rw = 0; self.rc = None     # v1.23.1: yarım saatlik alış / yükseltme pencereleri (bit maskesi + sayaç)


class SS:
    """Bir hissenin artımlı durumu."""
    __slots__ = ("ptr", "merges", "tot_lot", "tot_tl", "up_tot", "prev_p", "p0", "t0", "last_t", "br", "q1", "q2")

    def __init__(self) -> None:
        self.ptr = 0; self.merges = -1
        self.tot_lot = 0; self.tot_tl = 0.0; self.up_tot = 0.0
        self.prev_p = None; self.p0 = None; self.t0 = None; self.last_t = -1
        self.br: dict[int, BS] = {}
        self.q1: collections.deque = collections.deque()
        self.q2: collections.deque = collections.deque()


def process(ss: SS, T, P, L, SD, B, S) -> None:
    """Yeni işlemleri (sıralı) tek geçişte işler — O(n)."""
    br = ss.br
    q1, q2 = ss.q1, ss.q2
    prev = ss.prev_p
    up_tot = ss.up_tot
    tot_lot = ss.tot_lot
    tot_tl = ss.tot_tl
    for i in range(len(T)):
        t = T[i]; p = P[i]; l = L[i]; sd = SD[i]; b = B[i]; s = S[i]
        # ---- fiyat etkisi: ufku dolan bekleyen alışlar (son işlem fiyatı = ufuk anındaki fiyat)
        if prev is not None:
            while q1 and q1[0][0] + H1 < t:
                t0, p0, b0, l0 = q1.popleft()
                x = br[b0]; x.i1s += l0 * (prev / p0 - 1.0); x.i1w += l0
            while q2 and q2[0][0] + H2 < t:
                t0, p0, b0, l0 = q2.popleft()
                x = br[b0]; x.i2s += l0 * (prev / p0 - 1.0); x.i2w += l0
        tot_lot += l
        tot_tl += p * l
        if b:
            x = br.get(b)
            if x is None:
                x = br[b] = BS()
            if x.nb == 0:
                x.ft = t; x.fp = p; x.fl = l; x.mx = p
            else:
                avg = x.tl / x.lot
                hi = p > x.mx + EPS
                if hi or p > avg + EPS:
                    x.ys += 1; x.yt = t
                    hw = (t - HW0) // 1800 if t > HW0 else 0
                    x.rw |= 1 << hw
                    if x.rc is None:
                        x.rc = {}
                    x.rc[hw] = x.rc.get(hw, 0) + 1
                if hi:
                    x.yh += 1; x.mx = p
            x.nb += 1; x.lot += l; x.tl += p * l
            x.bw |= 1 << ((t - HW0) // 1800 if t > HW0 else 0)
            if x.nb <= FIRST_N:
                x.nl += l; x.ntl += p * l
            if t < OPEN_END:
                x.ohl += l; x.oht += p * l
            if t != x.lt:
                x.nsec += 1
                m = t // 60
                if m != x.lmin:
                    x.nmin += 1; x.lmin = m
            x.lt = t; x.lp = p
            if sd == 1:
                x.alot += l; x.an += 1; x.stk += 1
                if x.stk > x.mstk:
                    x.mstk = x.stk
                if t == x.swt:
                    if p > x.swp + EPS and not x.swc:
                        x.sw += 1; x.swc = True
                else:
                    x.swt = t; x.swp = p; x.swc = False
                if prev is not None and p > prev:
                    x.up += p - prev
            else:
                x.stk = 0
            if l > x.big:
                x.big = l; x.bigp = p; x.bigt = t
            q1.append((t, p, b, l)); q2.append((t, p, b, l))
        if s:
            y = br.get(s)
            if y is None:
                y = br[s] = BS()
            y.slot += l; y.stl += p * l
        if prev is not None and p > prev:
            up_tot += p - prev
        if ss.p0 is None:
            ss.p0 = p; ss.t0 = t
        prev = p
        ss.last_t = t
    ss.prev_p = prev
    ss.up_tot = up_tot
    ss.tot_lot = tot_lot
    ss.tot_tl = tot_tl


def resolve(ss: SS, ref: int | None) -> None:
    """Ufku `ref`'e kadar dolmuş (ref=None → hepsi, gün bitti) bekleyen alışları son fiyatla kapatır."""
    p = ss.prev_p
    if p is None:
        return
    br = ss.br
    for q, h, a in ((ss.q1, H1, 1), (ss.q2, H2, 2)):
        while q and (ref is None or q[0][0] + h <= ref):
            t0, p0, b0, l0 = q.popleft()
            x = br[b0]
            if a == 1:
                x.i1s += l0 * (p / p0 - 1.0); x.i1w += l0
            else:
                x.i2s += l0 * (p / p0 - 1.0); x.i2w += l0


def _durum(chg, akt, ys_r) -> str:
    if chg >= 2 and akt >= 60:
        return "SERT YÜKSELTİYOR"
    if chg >= 0.5:
        return "YÜKSELTİYOR"
    if chg <= -0.5:
        return "DÜŞÜREREK TOPLUYOR"
    return "SABİT MALİYET"


def build_rows(sym: str, ss: SS, names: list) -> list:
    out = []
    tot = ss.tot_lot or 1
    upt = ss.up_tot
    for bi, x in ss.br.items():
        if x.nb == 0 or x.tl < MIN_TL:
            continue
        net = x.lot - x.slot
        if net <= 0:
            continue
        avg = x.tl / x.lot
        chg = (avg / x.fp - 1) * 100 if x.fp else 0.0
        navg = x.ntl / x.nl if x.nl else avg
        chgn = (avg / navg - 1) * 100 if navg else 0.0
        rr = x.ys / max(1, x.nb - 1)
        akt = x.alot / x.lot * 100
        pay = x.lot / tot * 100
        up = x.up / upt * 100 if upt > 0 else 0.0
        i1 = x.i1s / x.i1w * 100 if x.i1w else None
        i2 = x.i2s / x.i2w * 100 if x.i2w else None
        mult = 0.5 + 0.5 * net / x.lot
        parts = (20 * _clip(chg / 3.0) + 10 * _clip(rr / 0.5) + 15 * _clip(pay / 15.0)
                 + 8 * _clip(math.log10(max(x.tl, 1) / 5e5) / 2.3) + 12 * _clip((akt - 30) / 60.0)
                 + 5 * _clip(x.sw / 5.0) + 10 * _clip(up / 40.0) + 5 * _clip((i2 or 0) / 0.3) + 10 * _clip(x.nmin / 90.0))
        # v1.23.1 — ısrar: süre, farklı dakika, yükseltmelerin alış dönemine yayılımı, aktif %, büyüklük
        fw = (x.bw & -x.bw).bit_length() - 1
        lw = x.bw.bit_length() - 1
        tot_w = max(1, lw - fw + 1)
        rwc = x.rw.bit_count()
        ent = 0.0
        topw = 0.0
        if x.rc and x.ys:
            for c in x.rc.values():
                q = c / x.ys
                ent -= q * math.log(q)
                if q > topw:
                    topw = q
            ent = ent / math.log(tot_w) if tot_w > 1 else 0.0
        spread = 0.5 * (rwc / tot_w) + 0.5 * min(1.0, ent)
        span_s = x.lt - x.ft
        iparts = (20 * _clip(span_s / 14400.0) + 20 * _clip(x.nmin / 120.0) + 25 * spread * _clip(tot_w / 4.0)
                  + 10 * _clip((akt - 30) / 50.0) + 15 * _clip(math.log10(max(x.tl, 1) / 5e5) / 2.3))
        imult = 0.6 + 0.4 * net / x.lot
        name = names[bi] if bi < len(names) else str(bi)
        out.append({
            "s": sym, "br": name, "bi": bi, "dr": _durum(chg, akt, rr),
            "ft": _hms(x.ft), "fts": x.ft, "fp": round(x.fp, 4), "fl": x.fl,
            "c1": round(navg, 4), "oh": round(x.oht / x.ohl, 4) if x.ohl else None,
            "cur": round(avg, 4), "lp": round(x.lp, 4), "mx": round(x.mx, 4),
            "chg": round(chg, 2), "chgN": round(chgn, 2), "ys": x.ys, "yh": x.yh, "yr": round(rr * 100, 1),
            "yt": _hms(x.yt) if x.yt >= 0 else None, "nb": x.nb,
            "akt": round(akt, 1), "seri": x.mstk, "sw": x.sw, "big": x.big, "bigp": round(x.bigp, 4), "bigt": _hms(x.bigt),
            "bigtl": round(x.big * x.bigp), "net": net, "blot": x.lot, "slot": x.slot, "btl": round(x.tl), "stl": round(x.stl),
            "pay": round(pay, 2), "up": round(up, 1),
            "i10": None if i1 is None else round(i1, 3), "i60": None if i2 is None else round(i2, 3),
            "dk": x.nmin, "sn": x.nsec, "span": _fmt_span(x.lt - x.ft), "spans": x.lt - x.ft,
            "lt": _hms(x.lt), "lts": x.lt, "p": round(ss.prev_p or 0, 4),
            "yy": f"{rwc}/{tot_w} yarım saat", "yyv": round(spread * 100, 1), "yk": round(topw * 100, 1),
            "_b": parts, "_m": mult, "_ib": iparts, "_im": imult, "_dr": _durum(chg, akt, rr),
        })
    return out


def _finish(r: dict, ref: int, gd: dict | None = None) -> dict:
    still = ref - r["lts"] <= STILL_MIN * 60
    r["still"] = "● EVET" if still else "—"
    r["sc"] = round((r["_b"] + (5 if still else 0)) * r["_m"])
    r["israr"] = round((r["_ib"] + (10 if still else 0)) * r["_im"])
    r["dr"] = ("ISRARCI · " + r["_dr"]) if r["israr"] >= 70 else r["_dr"]
    if gd is not None:
        r["gd"] = gd.get(r["s"])
    return r


class DayRes:
    def __init__(self, day: str, mode: str) -> None:
        self.day = day
        self.mode = mode
        self.st: dict[str, SS] = {}
        self.rows_by: dict[str, list] = {}
        self.rows: list = []
        self.ref = 0
        self.ready = False
        self.done = 0
        self.total = 0
        self.computed_at = None
        self.src_id = None
        self.universe = 0
        self.meta: dict = {}
        self.ver = 0


class MaliyetEngine:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.days: dict[str, DayRes] = {}
        self.disk: dict[str, DiskDay] = {}
        self.want: collections.deque = collections.deque()
        self.store = None
        self.hub = None
        self.events = None
        self.k = None
        self.thread = None
        self.loops = 0
        self.errors = 0
        self.last_err = None
        self.timing = {}
        self.alerted: dict = {}
        self.arate: collections.deque = collections.deque()
        self._warm = True
        self._cache: dict = {}
        self.feed = None
        self._gdc: dict = {}
        self.preset_fn = None          # v1.24.0: hazır senaryolar (app/v124.py BaskiEngine.preset_for)

    # ------------------------------------------------------------ source --
    def start(self, feed, store, hub, k_engine=None, events=None) -> None:
        self.store, self.hub, self.k, self.events = store, hub, k_engine, events
        self.feed = feed
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name="v123-maliyet", daemon=True)
            self.thread.start()

    def _live_day(self) -> str | None:
        st = self.store
        today = _today()
        if st is not None and st.day == today:
            try:
                if any(len(e.t) for e in list(st.syms.values())):
                    return today
            except Exception:
                return None
        return None

    def default_day(self) -> str | None:
        return self._live_day() or _last_disk_day(_today())

    def dates(self) -> list:
        out = []
        try:
            ds = sorted((d.name for d in TRADES_DIR.iterdir() if d.is_dir() and d.name.isdigit()), reverse=True)
        except Exception:
            ds = []
        live = self._live_day()
        for d in ds:
            if d == live or any(True for _ in (TRADES_DIR / d).glob("*.csv")):
                out.append({"d": d, "l": _day_label(d), "live": d == live})
            if len(out) >= 6:
                break
        return out

    def _src(self, day: str):
        """(mode, syms, brokers, lock, src_id) — canlı store / v122'nin yüklediği gün / kendi DiskDay önbelleği."""
        if day == self._live_day():
            st = self.store
            return "canlı", st.syms, st.brokers, st.lock, ("live", id(st))
        kd = getattr(self.k, "disk", None) if self.k is not None else None
        if kd is not None and getattr(kd, "day", None) == day and getattr(kd, "loaded", False):
            self.disk.pop(day, None)          # v122 aynı günü yüklemiş → kopyayı bırak
            return "kayıt", kd.syms, kd.brokers, kd.lock, ("k", id(kd))
        dk = self.disk.get(day)
        if dk is None:
            dk = DiskDay(day)
            dk.load()
            self.disk[day] = dk
            for old in [d for d in self.disk if d != day][:-1]:     # en fazla 2 gün bellekte
                self.disk.pop(old, None)
        return "kayıt", dk.syms, dk.brokers, dk.lock, ("d", id(dk))

    def _gd(self, day: str, live: bool) -> dict:
        """v1.23.1 — hissenin günlük değişim %'si. Canlı: anlık kotasyon (son ÷ önceki kapanış). Kayıtlı seans: o günün kapanışı ÷
        önceki kapanış (günlük bar deposu data/op/bars) → yoksa (son seans ise) kotasyon → yoksa önceki kayıtlı günün son işlemi."""
        q = getattr(self.feed, "quotes", None) or {}
        if live:
            out = {}
            for s, v in list(q.items()):
                try:
                    la, pc = v.get("last"), v.get("prev_close")
                    if la and pc:
                        out[s] = round((la / pc - 1) * 100, 2)
                except Exception:
                    continue
            return out
        hit = self._gdc.get(day)
        if hit is not None:
            return hit
        out = {}
        iso = f"{day[:4]}-{day[4:6]}-{day[6:]}"
        bars_dir = TRADES_DIR.parent / "op" / "bars"
        try:
            import json
            for f in bars_dir.glob("*.json"):
                try:
                    bars = (json.loads(f.read_text(encoding="utf-8")) or {}).get("bars") or []
                except Exception:
                    continue
                for b in reversed(bars[-15:]):
                    if b.get("d") == iso:
                        c, pc = b.get("c"), b.get("pc")
                        if c and pc:
                            out[f.stem] = round((c / pc - 1) * 100, 2)
                        break
        except Exception as ex:
            logger.debug("v123 gd bars: %s", ex)
        if day == _last_disk_day(_today()) and not self._live_day():     # son seans: kotasyon hâlâ o günün kapanışını gösterir
            for s, v in list(q.items()):
                if s in out:
                    continue
                la, pc = v.get("last"), v.get("prev_close")
                if la and pc:
                    out[s] = round((la / pc - 1) * 100, 2)
        R = self.days.get(day)
        prev = _last_disk_day(day)
        if R is not None and prev:
            for s, ss in R.st.items():
                if s in out or ss.prev_p is None:
                    continue
                try:
                    with open(TRADES_DIR / prev / f"{s}.csv", "rb") as fh:
                        fh.seek(0, 2)
                        fh.seek(max(0, fh.tell() - 200))
                        ln = fh.read().decode("utf-8", "ignore").strip().split("\n")[-1].split(",")
                    pc = float(ln[1])
                    if pc:
                        out[s] = round((ss.prev_p / pc - 1) * 100, 2)
                except Exception:
                    continue
        self._gdc[day] = out
        return out

    def _meta(self, day: str) -> dict:
        try:
            import json
            return json.loads((TRADES_DIR / day / "_meta.json").read_text(encoding="utf-8"))
        except Exception:
            return {}

    # -------------------------------------------------------------- loop --
    def _loop(self) -> None:
        time.sleep(8)
        for _ in range(30):     # seans dışı: v122'nin son günü yüklemesini bekle (aynı veriyi iki kez yükleme)
            if self._live_day() or getattr(getattr(self.k, "disk", None), "loaded", False) or self.k is None:
                break
            time.sleep(2)
        while True:
            t0 = time.time()
            live = None
            try:
                live = self._live_day()
                day = live or _last_disk_day(_today())
                if day:
                    R = self.days.get(day)
                    if live or R is None or not R.ready:
                        self._step(day, bool(live))
                while self.want:
                    d = self.want.popleft()
                    R = self.days.get(d)
                    if R is None or not R.ready:
                        self._step(d, d == live)
                if live:
                    self._alerts(self.days.get(live))
                self.loops += 1
            except Exception as ex:
                self.errors += 1
                self.last_err = f"{type(ex).__name__}: {ex}"
                logger.exception("v123 loop")
            self.timing["loop"] = round(time.time() - t0, 3)
            time.sleep(3 if live else 2)

    def _step(self, day: str, live: bool) -> None:
        t0 = time.time()
        mode, syms, brokers, lock, sid = self._src(day)
        R = self.days.get(day)
        if R is None or (R.src_id != sid and (live or not R.ready or R.mode == "canlı")):
            R = DayRes(day, mode)
            R.src_id = sid
            R.meta = {} if live else self._meta(day)
            with self.lock:
                self.days[day] = R
                for old in [d for d in self.days if d != day and d != self._live_day()][:-2]:
                    self.days.pop(old, None)
        names = list(brokers)
        keys = list(syms.keys())
        R.total = len(keys)
        changed = False
        n_new = 0
        for k, sym in enumerate(keys):
            e = syms.get(sym)
            if e is None:
                continue
            ss = R.st.get(sym)
            with lock:
                n = len(e.t)
                mg = getattr(e, "snap_merges", 0)
                if ss is not None and ss.ptr == n and ss.merges == mg:
                    sl = None
                else:
                    if ss is None or ss.merges != mg or n < ss.ptr:
                        ss = SS(); ss.merges = mg
                    a = ss.ptr
                    sl = (e.t[a:n], e.p[a:n], e.l[a:n], e.sd[a:n], e.b[a:n], e.s[a:n])
                    if live and len(names) < len(brokers):
                        names = list(brokers)
            if sl is None:
                if live and (ss.q1 or ss.q2):
                    resolve(ss, _sec_now())
                continue
            T = sl[0]
            if any(T[i] > T[i + 1] for i in range(len(T) - 1)):        # nadiren: sıra dışı → zamana göre sırala
                idx = sorted(range(len(T)), key=T.__getitem__)
                sl = tuple([c[i] for i in idx] for c in sl)
            process(ss, *sl)
            ss.ptr = n
            R.st[sym] = ss
            resolve(ss, _sec_now() if live else None)
            R.rows_by[sym] = build_rows(sym, ss, names)
            n_new += len(sl[0])
            changed = True
            R.done = k + 1
            if not live and k % 8 == 0:
                time.sleep(0.002)          # disk günü: event loop'a nefes
        R.done = R.total
        if live:
            ref = min(max(_sec_now(), CONT_FROM), CONT_TO + 600)
        else:
            ref = max((ss.last_t for ss in R.st.values()), default=0)
        if changed or live or not R.ready:
            rows = []
            gd = self._gd(day, live)
            for lst in list(R.rows_by.values()):
                for r in lst:
                    rows.append(_finish(r, ref, gd))
            rows.sort(key=lambda r: (-r["sc"], -r["btl"]))
            with self.lock:
                R.rows = rows
                R.ref = ref
                R.universe = len(R.st)
                R.ready = True
                R.mode = mode
                R.ver += 1
                R.computed_at = time.strftime("%H:%M:%S")
        self.timing["step_" + ("live" if live else day)] = round(time.time() - t0, 3)
        if n_new and not live:
            logger.info("v123: %s hesaplandı (%d hisse, %d işlem, %.1f sn, %d satır)", day, len(R.st), n_new, time.time() - t0, len(R.rows))

    # -------------------------------------------------------------- API --
    def _cols(self):
        return [C("s", "Hisse", "sym"), C("gd", "Günlük değ. %", "chg"), C("br", "Kurum", "broker"), C("dr", "Durum", "kmdr"),
                C("ft", "İlk ayak izi", "time"), C("fp", "İlk fiyat", "px"), C("fl", "İlk lot", "lot"),
                C("c1", "İlk 10 ort.", "px"), C("oh", "Açılış saati ort.", "px"), C("cur", "Şu anki maliyet", "px"),
                C("lp", "Son alış fiyatı", "px"), C("chg", "Maliyet artışı %", "chg"), C("chgN", "İlk 10'dan %", "chg"),
                C("ys", "Yükseltme", "num"), C("yy", "Yükseltme yayılımı", "txt") + ["yyv"], C("nb", "Alış adedi", "num"), C("akt", "Aktif alış %", "pct"),
                C("seri", "Aktif seri", "num"), C("sw", "Süpürme", "num"), C("big", "En büyük alış", "lot"),
                C("net", "Net lot", "lot"), C("btl", "Alış ₺", "tl"), C("pay", "Hacim payı %", "pct"),
                C("up", "Yükselişe katkı %", "pct"), C("i10", "Etki 10 sn %", "chg"), C("i60", "Fiyat etkisi 60 sn %", "chg"),
                C("dk", "Alış dakikası", "num"), C("span", "Süre", "txt"), C("lt", "Son alış", "time"),
                C("still", "Hâlâ alıyor", "txt"), C("sc", "Skor", "score"), C("israr", "Israr skoru", "score"), C("p", "Son fiyat", "px")]

    def _resolve_day(self, date: str | None):
        live = self._live_day()
        d = (date or "").strip().replace("-", "")
        if d and d.isdigit() and len(d) == 8 and ((TRADES_DIR / d).is_dir() or d == live):
            return d, (d == live)
        d = live or _last_disk_day(_today())
        return d, (d is not None and d == live)

    def feature(self, w: str | None = None, q: str | None = None, date: str | None = None, tok: str | None = None) -> dict:
        day, live = self._resolve_day(date)
        ok = [x[0] for x in WINDOWS]
        w = w if w in ok else WDEF
        base = {"fid": FID, "title": TITLE, "short": SHORT, "desc": DESC, "nt": NT, "help": self._help(day),
                "windows": WINDOWS, "w": w, "day": day, "day_label": _day_label(day) if day else "", "dates": self.dates(),
                "live": live, "mode": "canlı" if live else "kayıt", "date_param": date or None}
        if not day:
            return {**base, "cols": self._cols(), "rows": [], "count": 0, "note": "Kayıtlı işlem günü bulunamadı.", "status": "hata"}
        R = self.days.get(day)
        if R is None or not R.ready:
            if R is None and day not in self.want:
                self.want.append(day)
            prog = f" ({R.done}/{R.total} hisse)" if R is not None and R.total else ""
            return {**base, "cols": self._cols(), "rows": [], "count": 0, "pending": True, "status": "hazırlanıyor",
                    "note": f"{_day_label(day)} işlemleri işlem işlem taranıyor{prog} — kayıtlı tam gün ilk seferde ~1 dk sürebilir."}
        pz = None
        if w in ("ciddi", "tavan"):
            try:
                pz = self.preset_fn(day) if self.preset_fn else None
            except Exception:
                pz = None
            if pz is None:
                return {**base, "cols": self._cols(), "rows": [], "count": 0, "pending": True, "status": "hazırlanıyor",
                        "note": "Hazır senaryolar (POC / alış ortalaması) hesaplanıyor — birkaç saniye sonra yenilenir."}
        pv = pz[0] if pz else 0
        key = (day, R.ver, w, (q or "").strip(), pv)
        tk = f"{day}|{R.ver}|{w}|{(q or '').strip()}|{pv}"
        if tok and tok == tk:
            return {"same": True, "tok": tk}
        hit = self._cache.get(key)
        if hit:
            return hit
        rows = R.rows
        if w == "1m":
            rows = [r for r in rows if r["btl"] >= 1e6]
        elif w == "5m":
            rows = [r for r in rows if r["btl"] >= 5e6]
        elif w == "20m":
            rows = [r for r in rows if r["btl"] >= 20e6]
        elif w == "yuk":
            rows = [r for r in rows if r["chg"] > 0 and r["ys"] > 0]
        elif w == "s50":
            rows = [r for r in rows if r["sc"] >= 50]
        elif w == "s70":
            rows = [r for r in rows if r["sc"] >= 70]
        elif w == "still":
            rows = [r for r in rows if r["still"] != "—"]
        elif w == "still5":
            rows = [r for r in rows if r["still"] != "—" and r["btl"] >= 5e6]
        elif w == "israr":
            rows = sorted((r for r in rows if r["israr"] >= 40), key=lambda r: (-r["israr"], -r["btl"]))
        elif w == "ilk":
            rows = [r for r in rows if R.ref - r["fts"] <= 15 * 60 and r["btl"] >= 1e6]
        elif w in ("ciddi", "tavan") and pz:
            # v1.24.0: hisse hazır senaryoyu sağlıyor (POC veya alış ortalaması) + bu kurum maliyetini yükseltiyor
            sset = pz[1] if w == "ciddi" else pz[2]
            if w == "ciddi":
                rows = [r for r in rows if r["s"] in sset and r["chg"] > 0 and r["ys"] >= 2 and r["btl"] >= 1e6 and r["sc"] >= 40]
            else:
                rows = [r for r in rows if r["s"] in sset and r["chg"] > 0 and r["ys"] >= 2 and r["btl"] >= 1e6 and r["still"] != "—"]
            out = []
            for r in rows:
                c = pz[3].get(r["s"]) or {}
                per = c.get("per") or {}
                pp, aa = per.get("poc"), per.get("ao")
                k = 1 if w == "tavan" else 0
                src = pp if (pp and pp[k]) else aa
                lst = list((src[3] if w == "tavan" else src[2]) if src else [])
                lst = [x for x in lst if x[2] != "B" or not x[0].startswith("Israrcı")]
                lst += [["Kurum maliyetini yükseltiyor (≥2 yükseltme)", 1, "K"], ["Kurum ≥1 Mn ₺ almış", 1, "K"], ["Kurum ciddiyet skoru ≥40", int(r["sc"] >= 40), "K"], ["Kurum hâlâ alıyor", int(r["still"] != "—"), "K"],
                        [f"Bu kurum ısrarcı (Israr ≥70)", int(r.get("israr", 0) >= 70), "K"]]
                rr = dict(r); rr["ck"] = lst
                out.append(rr)
            rows = sorted(out, key=lambda r: (-r["sc"], -r["btl"]))
        qq = (q or "").strip()
        if qq:
            f = _fold(qq)
            rows = [r for r in rows if f in _fold(r["s"]) or f in _fold(r["br"])]
        n_all = len(rows)
        drop = {"bi", "fts", "lts", "spans", "bigtl", "yr", "blot", "dr0"}
        out_rows = [{k: v for k, v in r.items() if k[0] != "_" and k not in drop} for r in rows[:3000]]
        cs_late = sum(1 for v in R.meta.values() if (v or {}).get("complete_since"))
        note = (f"{n_all} (hisse, kurum) satırı · yalnızca net alıcı ve ≥{_fs(MIN_TL)} ₺ alan kurumlar · referans saat {_hms(R.ref)} · "
                f"aktif/pasif işlem bazında bilinir (açılış seansı işlemleri hariç)."
                + (f" Not: {cs_late} hissede kayıt 10:00 açılışından sonra başladı (en geç {_hms(max((v or {}).get('complete_since') or 0 for v in R.meta.values()))})."
                   if cs_late else "")
                + (" İlk 3000 satır gösteriliyor." if n_all > 3000 else ""))
        cols = self._cols()
        if w in ("ciddi", "tavan"):
            cols = cols[:4] + [C("ck", "Senaryo ✓/✗", "chk")] + cols[4:]
        out = {**base, "cols": cols, "rows": out_rows, "count": n_all, "note": note, "status": "tam",
               "ref": _hms(R.ref), "universe": R.universe, "computed_at": R.computed_at, "updated": R.computed_at,
               "mode": R.mode, "sort": "israr" if w == "israr" else "sc", "tok": tk}
        if len(self._cache) > 40:
            self._cache.clear()
        self._cache[key] = out
        return out

    def _help(self, day) -> dict:
        h = dict(HELP)
        h["guide"] = [dict(x) for x in GUIDE] + [{"t": "Hazır senaryolar (CİDDİ YÜKSELİŞ / TAVAN ADAYI)", "p": PRESET_DOC}] + self._dyn_examples(day) + [{"t": "Nasıl hesaplanır? (ayrıntılı)", "p": [HELP["nasil"]]},
                                                                           {"t": "Dikkat edilmesi gerekenler", "p": GUIDE_WARN}]
        R = self.days.get(day) if day else None
        ex = None
        if R is not None and R.rows:
            for r in R.rows[:50]:
                if r["chg"] > 0.5 and r["ys"] >= 5:
                    ex = r
                    break
            ex = ex or R.rows[0]
        if ex:
            h["ornek"] = (f"{ex['s']} · {ex['br']} ({_day_label(day)}): ilk ayak izi {ex['ft']}'de {_fp(ex['fp'])} ₺'den {_n(ex['fl'])} lot. "
                          f"Gün içinde {_n(ex['nb'])} alışın {_n(ex['ys'])} tanesi maliyeti yükseltti; ortalama {_fp(ex['fp'])} → {_fp(ex['cur'])} ₺ "
                          f"({_pc(ex['chg'], 2)}), aktif alış %{_d(ex['akt'], 0)}, hacim payı %{_d(ex['pay'], 1)}, yükselişe katkı %{_d(ex['up'], 0)}, "
                          f"net {_n(ex['net'])} lot → ciddiyet skoru {ex['sc']}.")
        else:
            h["ornek"] = "Örnek: ilk ayak izi 10:03:17'de 41,20 ₺; 380 alışın 140'ı maliyeti yükseltti; ortalama 41,20 → 42,05 ₺ (+%2,1), aktif alış %72 → skor 78."
        return h

    def _dyn_examples(self, day) -> list:
        """Seçili seansın gerçek satırlarından: en ısrarcı alıcı ve tek seferlik vuruş örneği."""
        R = self.days.get(day) if day else None
        if R is None or not R.rows or day == "20261002":
            return []
        rows = R.rows
        per = max(rows, key=lambda r: (r["israr"], r["btl"]))
        one = [r for r in rows if r["sc"] >= 55 and r["yy"].split("/")[1].startswith(("1 ", "2 ")) and r["israr"] < 45]
        out = [f"• ISRARCI: {per['s']} · {per['br']} — {per['ft']}-{per['lt']} ({per['span']}), {per['dk']} alış dakikası, yayılım {per['yy']}, "
               f"aktif %{_d(per['akt'], 1)}, {_fs(per['btl'])} ₺, maliyet {_pc(per['chg'], 2)} → Skor {per['sc']} · Israr {per['israr']}."]
        if one:
            o = max(one, key=lambda r: r["btl"])
            out.append(f"• TEK SEFERLİK: {o['s']} · {o['br']} — {o['ft']}-{o['lt']} ({o['span']}), yayılım {o['yy']}, {_n(o['ys'])} yükseltme, "
                       f"aktif %{_d(o['akt'], 1)}, {_fs(o['btl'])} ₺, maliyet {_pc(o['chg'], 2)} → Skor {o['sc']} ama Israr {o['israr']}.")
        return [{"t": f"Bu seanstan örnekler ({_day_label(day)})", "p": out}]

    def detail(self, sym: str, br: str, date: str | None = None) -> dict:
        day, live = self._resolve_day(date)
        sym = (sym or "").upper().strip()
        if not day:
            return {"error": "kayıtlı gün yok"}
        try:
            mode, syms, brokers, lock, _ = self._src(day)
        except Exception as ex:
            return {"error": f"kaynak açılamadı: {ex}"}
        e = syms.get(sym)
        if e is None:
            return {"error": f"{sym} için {day} işlem kaydı yok", "sym": sym, "br": br, "day": day}
        with lock:
            names = list(brokers)
            n = len(e.t)
            T = list(e.t[:n]); P = list(e.p[:n]); L = list(e.l[:n]); SD = list(e.sd[:n]); B = list(e.b[:n]); S = list(e.s[:n])
            cs = getattr(e, "complete_since", None)
            gaps = list(getattr(e, "gaps", []) or [])
        bis = [i for i, nm in enumerate(names) if nm == br and i]
        if not bis:
            f = _fold(br)
            bis = [i for i, nm in enumerate(names) if i and _fold(nm) == f]
        if not bis:
            return {"error": f"kurum bulunamadı: {br}", "sym": sym, "br": br, "day": day}
        bi = bis[0]
        if any(T[i] > T[i + 1] for i in range(n - 1)):
            idx = sorted(range(n), key=T.__getitem__)
            T, P, L, SD, B, S = ([c[i] for i in idx] for c in (T, P, L, SD, B, S))
        if cs is None and not live:
            m = self._meta(day).get(sym) or {}
            cs = m.get("complete_since")
            gaps = m.get("gaps") or []
        ref = T[-1] if T else 0
        # saniye saniye fiyat (her saniyenin son işlem fiyatı) + saniye hacmi
        px = []
        for i in range(n):
            if px and px[-1][0] == T[i]:
                px[-1][1] = P[i]
            else:
                px.append([T[i], P[i]])

        def price_at(t):
            j = bisect.bisect_right(T, t) - 1
            return P[j] if j >= 0 else None
        tr = []
        lot = 0; tl = 0.0; mx = 0.0; nb = 0; slot = 0
        for i in range(n):
            if B[i] == bi:
                p, l = P[i], L[i]
                prev_avg = tl / lot if lot else None
                fl = 0
                if nb:
                    hi = p > mx + EPS
                    if hi or p > prev_avg + EPS:
                        fl = 2 if hi else 1
                    if hi:
                        mx = p
                else:
                    mx = p
                nb += 1; lot += l; tl += p * l
                avg = tl / lot
                a10 = price_at(T[i] + H1) if (not live or T[i] + H1 <= ref) else None
                a60 = price_at(T[i] + H2) if (not live or T[i] + H2 <= ref) else None
                tr.append([T[i], p, l, "A", 1 if SD[i] == 1 else (0 if SD[i] == 2 else -1), round(avg, 4),
                           None if prev_avg is None else round(avg - prev_avg, 4),
                           None if prev_avg is None else round((avg / prev_avg - 1) * 100, 4), fl, lot - slot,
                           None if a10 is None else round((a10 / p - 1) * 100, 3), None if a60 is None else round((a60 / p - 1) * 100, 3),
                           names[S[i]] if S[i] < len(names) else ""])
            elif S[i] == bi:
                slot += L[i]
                tr.append([T[i], P[i], L[i], "S", 1 if SD[i] == 2 else (0 if SD[i] == 1 else -1),
                           round(tl / lot, 4) if lot else None, 0, 0, 0, lot - slot, None, None,
                           names[B[i]] if B[i] < len(names) else ""])
        R = self.days.get(day)
        row = None
        if R is not None:
            for r in R.rows:
                if r["s"] == sym and r["br"] == names[bi]:
                    row = {k: v for k, v in r.items() if k[0] != "_"}
                    break
        akd = self._akd(day, sym, names[bi])
        return {"sym": sym, "br": names[bi], "day": day, "day_label": _day_label(day), "live": live, "mode": mode,
                "row": row, "px": px, "tr": tr, "n_all": n, "ref": _hms(ref),
                "rec_from": "açılış" if cs == 0 else (_hms(cs) if cs else (_hms(T[0]) if T else None)),
                "gaps": [[_hms(a), _hms(b)] for a, b in gaps[-10:]],
                "buy_avg": round(tl / lot, 4) if lot else None, "akd": akd,
                "gd": (row or {}).get("gd") if row else self._gd(day, live).get(sym),
                "cols": ["saat", "fiyat", "lot", "taraf", "aktif", "kümülatif ort.", "değişim", "değişim %", "yükseltme", "net lot", "etki 10sn", "etki 60sn", "karşı kurum"]}

    def _akd(self, day, sym, br) -> dict | None:
        try:
            import json
            d = json.loads((TRADES_DIR.parent / "akd" / day / f"{sym}.json").read_text(encoding="utf-8"))
            for r in d.get("TUM") or []:
                if r.get("broker") == br:
                    return {"net": r.get("value"), "cost": r.get("cost"), "ts": d.get("ts"), "range": d.get("range")}
        except Exception:
            return None
        return None

    def status(self) -> dict:
        return {"version": VERSION, "loops": self.loops, "errors": self.errors, "last_err": self.last_err, "timing": self.timing,
                "days": {d: {"ready": R.ready, "done": R.done, "total": R.total, "rows": len(R.rows), "mode": R.mode,
                             "ref": _hms(R.ref), "computed_at": R.computed_at} for d, R in list(self.days.items())},
                "alerted": len(self.alerted), "alerts_last_hour": len(self.arate)}

    # ------------------------------------------------------------ alerts --
    def _alerts(self, R: DayRes | None) -> None:
        if R is None or not R.ready or R.mode != "canlı":
            return
        sec = _sec_now()
        warm = self._warm
        self._warm = False
        if not (CONT_FROM + 300 <= sec <= CONT_TO):
            return
        now = time.time()
        while self.arate and now - self.arate[0] > 3600:
            self.arate.popleft()
        cands = []
        for r in R.rows[:400]:
            sc = r["sc"]
            if sc >= 70:
                cands.append(("sc", r))
            elif sc >= 50 and R.ref - r["fts"] <= 15 * 60 and r["btl"] >= 2e6 and r["akt"] >= 60:
                cands.append(("ilk", r))
        sent = 0
        for kind, r in cands:
            key = (R.day, r["s"], r["br"])          # hisse+kurum başına günde bir bildirim
            if key in self.alerted:
                continue
            self.alerted[key] = (now, kind, r["sc"])
            if warm:
                continue
            if sent >= 3 or len(self.arate) >= 12:
                continue
            sent += 1
            self.arate.append(now)
            s, b = r["s"], r["br"]
            if kind == "sc":
                title = f"🟢 {s} · {b} maliyet yükseltiyor (skor {r['sc']})"
            else:
                title = f"👣 {s} · {b} yeni ciddi ayak izi (skor {r['sc']})"
            txt = (f"{b}, {s} hissesinde {r['ft']}'den beri alıcı: ilk {_fp(r['fp'])} ₺ → ort. {_fp(r['cur'])} ₺ ({_pc(r['chg'], 2)}), "
                   f"{r['ys']} yükseltme, aktif alış %{r['akt']:.0f}, hacim payı %{r['pay']:.1f}, net {_fs(r['net'])} lot ({_fs(r['btl'])} ₺ alış).")
            try:
                if self.hub is not None:
                    self.hub._emit("olay", NT, s, title, txt, {"f": FID, "sc": r["sc"], "price": r.get("p"), "br": b, "kind": kind})
            except Exception as ex:
                logger.debug("v123 emit: %s", ex)
            try:
                if self.events is not None:
                    self.events.emit("kademe", s, txt, NT, r.get("p"), {"nt": NT, "title": title, "f": FID, "sc": r["sc"], "br": b})
            except Exception as ex:
                logger.debug("v123 olay: %s", ex)
        if len(self.alerted) > 20000:
            self.alerted = {k: v for k, v in self.alerted.items() if k[0] == R.day}


m_engine = MaliyetEngine()
