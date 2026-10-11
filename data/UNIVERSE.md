# BIST sembol evreni

Son güncelleme: uygulama `get_symbols(force_refresh=True)` ile üretir; sonuç `symbols.json` içinde cache’lenir (24 saat).

## Kaynaklar (birleştirilir, dedupe)

| Kaynak | Açıklama |
|--------|----------|
| KAP `IGS/A` API | Resmi BIST şirket listesi (`stockCode`) — ana kaynak |
| GitHub bist.csv | ahmeterenodaci KAP tabanlı liste |
| Wikipedia | EN “List of companies listed on the Borsa Istanbul” (ticker hücreleri) |
| `bist_seed.csv` | Yerel yedek |

Sadece `.IS` hisse kodları tutulur (`[A-Z0-9]{2,8}`); ETF/fon gibi uzun isim satırları atılır.

## Hedef

700+ BIST hisse kodu. Yahoo Finance her KAP üyesini kotasyonlamayabilir (ör. borsada işlem görmeyen aracı kurumlar / delist).

## RVOL formülleri

| Alan | Formül |
|------|--------|
| `rvol` | `today_volume / previous_session_volume` (önceki işlem günü günlük barı) |
| `rvol10` | `today_volume / mean(son 10 işlem günü hacmi)` (bugün hariç) |
| `rvol_tf` | `latest_bar_volume / mean(önceki N=20 bar hacmi)` aynı TF’de |

Çoklu TF: `1m,5m,15m,30m,1h,2h,4h,1d,1w`. `2h`/`4h` = 60m resample; `1w` = 1d → haftalık.

Fiyat cache TTL ≈ 60 sn. Günlük hacim istatistikleri ≈ 6 saat. İntraday geçmiş ≈ 2 dk.

## Tarayıcı kapsamı

`steady-risers`, `fast-movers`, `rvol-tf`, **`net-volume`**: quote cache'teki **ilk ~150 hacimli** hisse (RVOL TF tablo limiti ~40). Tam BIST evreni taranmaz — Yahoo batch limiti.

### Net Hacim (`/api/scanners/net-volume`)

Günlük footprint bar sınıflandırması ile `buy_vol`, `sell_vol`, `net_vol`, `buy_dominance_pct`.
Amaç: gün içinde alıcı hakim isimleri bulmak. Cache ~240 sn (ağır). Varsayılan sıralama `net_vol` desc.

### Ani Artış alarmı (`/api/alerts/spike?pct=1&interval=5m`)

TF seçiliyse: **son mum close vs önceki mum close %** (o TF). Günlük quote kullanılmaz.
Evren: üst ~220 hacimli. UI poll ~20 sn.

## v1.8 — Canlı yenileme + yeni özellikler

### Quote cache TTL
- Seans açık (BIST ~10:00–18:10 TR): **~10 sn**
- Kapalı: **~45 sn**
- Frontend: SSE `/api/stream/quotes` + poll ~8 sn açık / ~45 sn kapalı
- **Yahoo BIST kotasyonları gecikmeli olabilir** (resmi seviye-1 değil)
- **Grafik mumları (v1.11+):** İş Yatırım public ChartData/HisseTekil — Yahoo history kullanılmaz. Sembol eşlemesi: BIST kodu = İş Yatırım `code`/`hisse` (THYAO→THYAO).

### Alarmlar
| Endpoint | Özellik |
|----------|---------|
| `/api/alerts/spike` | Ani artış % (TF son mum) |
| `/api/alerts/rvol-spike` | RVOL ani sıçrama (gün + multi-TF) |
| `/api/alerts/rvol10` | Hacim patlaması RVOL(10) ≥ eşik |
| `POST /api/alerts/price` | Fiyat hedefi (≥ / ≤); UI localStorage |

### Detay panelleri
| Endpoint | Özellik |
|----------|---------|
| `/api/stocks/{s}/support-resistance` | Swing S/R + mesafe %; grafik priceLine |
| `/api/stocks/{s}/poc-migration` | Saatlik/rolling POC kayması |
| `/api/stocks/{s}/va-migration` | VAH/VAL göçü + oklar |

### Tarayıcılar
| Endpoint | Özellik |
|----------|---------|
| `/api/scanners/parabolic` | Parabolik yükseliş skoru |
| `/api/scanners/poc-shift` | En büyük \|ΔPOC\| |
