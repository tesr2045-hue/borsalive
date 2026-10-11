# BIST Analiz — yeniden başlatma sonrası otomatik kurtarma (05.10.2026)

## Sorun
Kutu ~05:00'te yeniden başladı / yeni örneğe taşındı (dosyalar `/workspace` + `/home/box` mağazadan geri yüklendi,
.venv ve sistem paketleri gelmedi). Hiçbir şey çalışmıyordu → kalıcı URL ERR_NGROK_3200.

## Kutuda neler var / yok
- PID 1 = tini → pod-daemon; systemd yok, cron yok, XDG autostart (xfce-session) yok.
- sudo var ama kök dosya sistemi taşımada korunmuyor (yalnız /workspace ve /home/box kalıcı) → /etc tabanlı çözüm kalıcı değil.
- Platform betiklerine (start-sand-box vb.) dokunmak / PATH ele geçirmek bilinçli olarak YAPILMADI.
- Kalıcı ve kullanıcıya ait tek tetik: ajan kabuk oturumları `bash -O extglob -ilc` ile (etkileşimli + login)
  başlatılıyor (exec-daemon initBashState) → `~/.profile` → `~/.bashrc` okunuyor. İnsan terminali de okur.

## Kurulum
- `ops/ensure-up.sh` — idempotent: watchdog yoksa başlatır (watchdog da keepalive'ı açar), keepalive yoksa başlatır.
  Çalışana dokunmaz, hiçbir şeyi öldürmez; flock ile tek kopya; kancayı da yeniden kurar. Log: `ops/ensure.log`.
- `ops/install-hook.sh` — `~/.bashrc` başına (etkileşim korumasından önce) sessiz arka plan kancası ekler.
- `ops/lib.sh` — /proc argv ile süreç bulma (pgrep -f/pkill -f yok), açık PID ile öldürme, genel URL kontrolü.
- `watchdog.sh` tünel bekçisi: ~her 60 sn genel URL `/api/health`; ERR_NGROK_* / HTTP≠200 (veya zaman aşımı + 4040'ta tünel yok)
  3 ardışık kez (~3 dk) ve yerel uvicorn ayaktaysa → ngrok PID'ini öldür (keepalive 5 sn'de yeniden açar); en çok 10 dk'da 1.
  Keepalive ölmüşse yeniden başlatır. Ayar: WD_TUN_EVERY / WD_TUN_BAD_MAX / WD_TUN_GAP_SEC.

## Doğrulama
- `ops/ensure-up.sh -v`  → watchdog / keepalive / ngrok PID'leri, "başlatılan: yok" = hepsi ayakta.
- `head -3 ~/.bashrc` → `# >>> bist-analiz ensure-up >>>` satırı.
- `grep "tünel bekçisi" watchdog.log`, `cat ops/ensure.log`.
- Elle kurtarma: `/workspace/bist-analiz/ops/ensure-up.sh` (IDEAL_PASSWORD olan bir ajan kabuğundan).

## Sınır
Kutu açıldıktan sonra İLK ajan kabuk oturumu (herhangi bir ajanın ilk Shell komutu ya da terminal) tetikler; kutu açılıp hiç
oturum açılmazsa kutu içinden başlatacak bir mekanizma yok. Tam boşluk için ayrıca düzenli (ör. 15 dk) bir zamanlanmış
Grok Bot görevi `ops/ensure-up.sh` çalıştırabilir.
