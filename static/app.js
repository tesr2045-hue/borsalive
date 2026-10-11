/* BIST Canlı v1.34.1 (İdealData Hesabı: durum etiketine dokun) · v1.34.0 (KEŞFET › ✅ AL BUNU · TAVAN ADAYI: tek liste — kurum fiyatı itiyor + hâlâ itiyor + AKD/derinlik destekli + geç değil · al_bunu bildirimi varsayılan KAPALI) · v1.33.1 (D-A-K: Derinlik sütununda parantez her satırda — 92(92) / 92(—)) · v1.33.0 (KEŞFET › ALGO DESTEK / ALGO DİRENÇ: tüm hisselerin canlı derinliğinde tekrarlayan lot duvarları · beklenen etki · kademe vurgusu) · v1.32.1 (D-A-K SKORLARI: Derinlik sütunu 99(74) = liste skoru (sayfa Derinlik Skoru) · sayfa skoru tüm hisseler için birebir aynı hesapla) · v1.32.0 (KEŞFET › D-A-K SKORLARI: tüm hisselerde canlı Derinlik Skoru · AKD Skoru · Kademe Analizi Skoru · D-A-K Skoru · sırala/süz · dokun = neden) · v1.31.2 (🚀 TRENE ATLA ERKEN: doğrudan işlem akışından 1 sn döngü · ≥5 kademe aktif alış süpürmesi + gün ≤ +%2 + ilk hızlanma + hacim patlaması · tetik→bildirim ≈1–3 sn) · v1.31.1 (🚀 TRENE ATLA SIKI KURAL: yalnız hareketin başı · 5 dk ≤ +%2 · son 1 dk hızlanma · kırılımda hacim · KAÇTI/DÖNDÜ gönderilmez · 30 dk soğuma) · v1.31.0 (🚀 TRENE ATLA: tek, net "şimdi sert yükseliş başlıyor" alarmı · kırılım/art arda süpürme + ivme + aktif alış + hacim + süpürme serisi AND kapısı · varsayılan AÇIK, diğer alarmlardan bağımsız · KEŞFET › TRENE ATLA canlı aday listesi) · v1.30.2 (CANLI GRAFİK: bugünün mumları İdealData işlem işlem · son mum canlı fiyatı izler · 1G/1H canlı) · v1.30.1 (FORMASYONLAR periyot sekmesi işareti = en güçlü aktif sinyal, kartla aynı · başarısız △▽ ayrı) · v1.30.0 (KEŞFET › OLAY LİSTESİ (ALARM): piyasa geneli POC olay akışı · olay türü alarmları · DİRENÇ KIRILDI + SÜPÜRME birleşik alarmı · hazır taramalar · tüm alarmlar varsayılan KAPALI + TÜM ALARMLAR ana anahtarı) · v1.29.0 (KEŞFET › EN İYİ KOŞULLAR: her tarayıcının tavan / ciddi yükseliş için en iyi ayarı · tek dokunuşla uygula + Sıfırla · Birleşik Aday Listesi) · v1.28.0 (FORMASYONLAR periyot sekmeleri · AKTİF MUM FORMASYONU · ORDER BLOCK olası güçlü tepki bölgeleri + grafikte OB) · v1.27.3 (TAM METİN: ekrana sığmayan her metin → dokun / uzun bas → tam metin penceresi · Kopyala · Detay → · OLAY LİSTESİ AYRINTI 2 satır) · v1.27.2 (İdealData kesinti koruması · AMBER YENİDEN BAĞLANIYOR · ↻ bağlantıyı uyandırır) · v1.27.1 (AKD Taraması TÜM AKD NET › İLK 3/5/10 NET PGÇ sütunları + yönlü % + HAFTALIK/AYLIK dönem + 6 hazır tarama · AKD sekmesi kartında %) · v1.27.0 (KEŞFET › Mum Formasyonları + Grafik Formasyonları · tüm hisseler × 5dk/15dk/30dk/60dk/2s/4s/1G/1H · animasyonlu kanıt · Özet FORMASYONLAR kartı · grafik işaretleri · formasyon bildirimleri) · v1.26.4 (alt menü: tüm öğelerde ad simgenin altında · durum rozeti CANLI / SEANS DIŞI / BAĞLANTI YOK / HATA) · v1.26.3 (Aktif İşlem Taraması: AKD NET % + AKD Alış/Satış sırası + 🚂 TAVAN TRENİ sinyali/ön ayarı/bildirimi · AKD ANALİZİ/Özet TAHTACI + TAVAN TRENİ birleşik) · v1.26.2 (Özet grafik OHLC lejantı + LOG · Aktif İşlem Taraması (KURUM) · kurum → ilk 5 aktif hisse · AKD aktif sütunları + EN ÇOK AKTİF ALAN + TAHTACI SİNYALİ) · v1.26.1 (AKD Taraması: Aktif alış % / Aktif satış %) · v1.26.0 (Merdiven işaretleri · Seans İşlem Akışı · AKD K/Z + Analiz · AKD Taraması) · v1.25.0 (Derinlik Analizleri) · v1.24.0 (POC / Alış Ort. Baskısı · Hazır Senaryolar · Özet+) · v1.20.0 — hisse detayı (ÖZET · DERİNLİK · İŞLEMLER · AKD · KADEME · TAKAS · SİNYALLER · AI) + Yükselenler/Hacimliler · Akış · Derinlik Baskısı · Kurum Analizi · Hisselerin Endekse Etkisi · Radar · Tavan/Taban · Agresif · Para Akışı · Kurum Uyarıları · Tahtacı */
(() => {
  "use strict";
  const VERSION = "1.23.1";
  const $ = (id) => document.getElementById(id);
  const LS = {
    get(k, d) { try { const v = localStorage.getItem("v17_" + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("v17_" + k, JSON.stringify(v)); } catch (e) {} },
  };

  // ------------------------------------------------ v1.22.1 kaydırma koruması
  // Otomatik veri yenilemesi (setInterval → render) hiçbir zaman sayfanın veya iç tabloların
  // kaydırma konumunu değiştirmemeli. Kullanıcı girdisi (dokunma/tekerlek/tuş/tık) veya gerçek
  // gezinme (go(), sgNav) dışında oluşan her kaydırma değişikliği geri alınır; render sırasında
  // sayfanın geçici olarak kısalması (Yükleniyor… yer tutucuları) görünür görünümün min-height
  // kilidiyle engellenir. İç kaydırma kutuları (yatay tablolar, çip şeritleri) anahtar yoluyla izlenir.
  const SG = { y: window.scrollY, userTs: 0, navTs: 0, allowTs: 0, lastEvt: 0, want: null, wantUntil: 0, inner: new Map(), hs: [], view: null };
  const sgNow = () => Date.now();
  const sgUser = () => { SG.userTs = sgNow(); };
  ["wheel", "touchstart", "touchmove", "keydown", "pointerdown", "mousedown"].forEach((ev) => window.addEventListener(ev, sgUser, { passive: true, capture: true }));
  function sgActive() { const n = sgNow(); return n - SG.userTs < 1500 || n - SG.navTs < 1500 || n - SG.allowTs < 600; }
  function sgNav() { SG.navTs = sgNow(); SG.want = null; SG.inner.clear(); SG.hs = []; const v = SG.view; if (v) v.style.minHeight = ""; SG.view = null; }
  function sgAllow() { SG.allowTs = sgNow(); }
  function sgKey(el) {
    let a = el.parentElement; while (a && !a.id) a = a.parentElement;
    const anc = a || document.body;
    const c = (el.id ? "#" + el.id : (el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\s+/)[0] : el.tagName));
    let i = 0;
    if (!el.id) { const sib = anc.querySelectorAll(c.startsWith(".") ? c : el.tagName); i = Array.prototype.indexOf.call(sib, el); }
    return [anc.id || "", c, i];
  }
  function sgFind(k) {
    const anc = k[0] ? document.getElementById(k[0]) : document.body; if (!anc) return null;
    if (k[1].startsWith("#")) return document.getElementById(k[1].slice(1));
    return anc.querySelectorAll(k[1].startsWith(".") ? k[1] : k[1])[k[2]] || null;
  }
  window.addEventListener("scroll", (e) => {
    const n = sgNow(), tg = e.target;
    const chain = n - SG.lastEvt < 180 && n - SG.userTs < 6000;   // momentum / scrollbar sürükleme zinciri
    if (tg === document || tg === document.documentElement || tg === document.body) {
      const y = window.scrollY;
      if (sgActive() || chain) { SG.y = y; SG.want = null; SG.lastEvt = n; if (chain) SG.userTs = n; return; }
      if (Math.abs(y - SG.y) > 1) { SG.want = SG.y; SG.wantUntil = n + 5000; sgRestore(); }
      return;
    }
    if (!(tg instanceof Element)) return;
    if (sgActive() || chain) { SG.lastEvt = n; if (chain) SG.userTs = n; const k = sgKey(tg); SG.inner.set(k.join("\u0001"), { k, l: tg.scrollLeft, t: tg.scrollTop }); if (SG.inner.size > 40) SG.inner.delete(SG.inner.keys().next().value); return; }
    sgInner();
  }, { passive: true, capture: true });
  function sgRestore() {
    if (SG.want == null) return;
    if (sgNow() > SG.wantUntil || sgActive()) { SG.want = null; return; }
    const max = document.documentElement.scrollHeight - window.innerHeight;
    if (max >= SG.want - 1) { if (Math.abs(window.scrollY - SG.want) > 1) window.scrollTo(0, SG.want); SG.want = null; }
    else requestAnimationFrame(sgRestore);
  }
  function sgInner() {
    if (sgActive()) return;
    SG.inner.forEach((v) => {
      const el = sgFind(v.k); if (!el) return;
      if (Math.abs(el.scrollLeft - v.l) > 1) el.scrollLeft = v.l;
      if (Math.abs(el.scrollTop - v.t) > 1) el.scrollTop = v.t;
    });
  }
  // DOM değişince (render) — boyamadan önce mikro görevde — konumları doğrula
  let sgQ = false;
  new MutationObserver(() => {
    if (sgQ) return; sgQ = true;
    queueMicrotask(() => {
      sgQ = false;
      if (sgActive()) return;
      sgInner();
      if (Math.abs(window.scrollY - SG.y) > 1) { SG.want = SG.y; SG.wantUntil = sgNow() + 5000; sgRestore(); }
    });
  }).observe(document.documentElement, { childList: true, subtree: true, characterData: true });
  // Görünür görünümün yüksekliği son 3 sn'nin en yüksek değerinin altına inmesin (yer tutucu kısalması → zıplama yok)
  setInterval(() => {
    const v = document.querySelector(".view:not([hidden])"); if (!v) return;
    if (v !== SG.view) { if (SG.view) SG.view.style.minHeight = ""; SG.view = v; SG.hs = []; }
    const n = sgNow();
    if (n - SG.navTs < 800) { v.style.minHeight = ""; SG.hs = []; return; }
    const prevMin = v.style.minHeight;
    const vr = v.getBoundingClientRect(); let bot = vr.top;   // doğal içerik yüksekliği (min-height'i kaldırmadan → ölçerken kırpma olmaz)
    for (const c of v.children) { if (c.hidden) continue; const b = c.getBoundingClientRect().bottom; if (b > bot) bot = b; }
    const h = Math.ceil(bot - vr.top + (parseFloat(getComputedStyle(v).paddingBottom) || 0));
    SG.hs.push([n, h]); while (SG.hs.length && n - SG.hs[0][0] > 3000) SG.hs.shift();
    const mx = Math.max(...SG.hs.map((x) => x[1]));
    v.style.minHeight = mx > h ? mx + "px" : "";
    if (prevMin !== v.style.minHeight && Math.abs(window.scrollY - SG.y) > 1 && !sgActive()) { SG.want = SG.y; SG.wantUntil = n + 5000; sgRestore(); }
  }, 250);
  // Sekme/çip şeridinde seçili öğeyi YALNIZCA yatayda ortala (pencereyi dikeyde asla kaydırmaz)
  function hCenter(el) {
    if (!el) return;
    let c = el.parentElement;
    while (c && c !== document.body && !(c.scrollWidth > c.clientWidth + 1)) c = c.parentElement;
    if (!c || c === document.body || c === document.documentElement) return;
    const er = el.getBoundingClientRect(), cr = c.getBoundingClientRect();
    sgAllow();
    c.scrollLeft += (er.left + er.width / 2) - (cr.left + cr.width / 2);
    const k = sgKey(c); SG.inner.set(k.join("\u0001"), { k, l: c.scrollLeft, t: c.scrollTop });
  }
  // innerHTML'i yalnızca içerik değiştiyse yaz (titreme yok, açık durumlar korunur)
  function setH(el, html) { if (!el) return; if (el._h === html && el._hf === el.firstChild && el._hn === el.childNodes.length) return; el.innerHTML = html; el._h = html; el._hf = el.firstChild; el._hn = el.childNodes.length; }

  // ------------------------------------------------------------ formatting
  const nfCache = {};
  function nf(d) {
    const k = String(d);
    if (!nfCache[k]) nfCache[k] = new Intl.NumberFormat("tr-TR", { minimumFractionDigits: d, maximumFractionDigits: d });
    return nfCache[k];
  }
  const isNum = (v) => typeof v === "number" && isFinite(v);
  const fN = (v, d = 0) => (isNum(v) ? nf(d).format(v) : "—");
  const fP = (v) => (isNum(v) && v !== 0 ? nf(2).format(v) : "—");
  const fPct = (v, d = 2) => (isNum(v) ? (v > 0 ? "+" : "") + nf(d).format(v) + "%" : "—");
  function fShort(v, unit = "") {
    if (!isNum(v)) return "—";
    const a = Math.abs(v), s = v < 0 ? "-" : "";
    let out;
    if (a >= 1e9) out = nf(2).format(a / 1e9) + " Mr";
    else if (a >= 1e6) out = nf(a >= 1e8 ? 1 : 2).format(a / 1e6) + " Mn";
    else if (a >= 1e4) out = nf(0).format(a / 1e3) + " bin";
    else if (a >= 1e3) out = nf(1).format(a / 1e3) + " bin";
    else out = nf(0).format(a);
    return s + out + (unit ? " " + unit : "");
  }
  const cls = (v) => (isNum(v) ? (v > 0 ? "pos" : v < 0 ? "neg" : "flat") : "flat");
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  function tickOf(p) {
    if (!isNum(p)) return 0.01;
    if (p < 20) return 0.01; if (p < 50) return 0.02; if (p < 100) return 0.05; if (p < 250) return 0.1;
    if (p < 500) return 0.25; if (p < 1000) return 0.5; if (p < 2500) return 1; return 2.5;
  }
  const trUpper = (s) => String(s || "").toLocaleUpperCase("tr-TR");
  const fold = (s) => trUpper(s).replace(/İ/g, "I").replace(/Ş/g, "S").replace(/Ğ/g, "G").replace(/Ü/g, "U").replace(/Ö/g, "O").replace(/Ç/g, "C");
  function ymd(d) { return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); }
  function fmtYmd(s) { return s && s.length === 8 ? `${s.slice(6, 8)}.${s.slice(4, 6)}.${s.slice(0, 4)}` : s || ""; }

  // Broker names (İdealData ASCII → Türkçe)
  const BR_FIX = [[/\bIs\b/g, "İş"], [/Yatirim/g, "Yatırım"], [/Yapi/g, "Yapı"], [/Vakif/g, "Vakıf"], [/Osmanli/g, "Osmanlı"],
    [/\bUnlu\b/g, "Ünlü"], [/Seker/g, "Şeker"], [/Bankasi/g, "Bankası"], [/Yabanci/g, "Yabancı"], [/Fonlari/g, "Fonları"],
    [/Menkul/g, "Menkul"], [/Kuveyt/g, "Kuveyt"], [/Turk\b/g, "Türk"], [/Doga/g, "Doğa"], [/Dinamik/g, "Dinamik"]];
  function brName(n) { let s = String(n || ""); for (const [r, t] of BR_FIX) s = s.replace(r, t); return s; }
  function brInitials(n) {
    const w = brName(n).replace(/[^\p{L}\p{N} ]/gu, " ").split(/\s+/).filter(Boolean);
    if (!w.length) return "?";
    if (w.length === 1) return trUpper(w[0].slice(0, 2));
    return trUpper(w[0][0] + w[1][0]);
  }
  function hue(s) { let h = 0; for (const c of String(s)) h = (h * 31 + c.charCodeAt(0)) % 360; return h; }
  function brIcon(n, dk) {
    if (dk) return `<span class="br-ic dk">DK</span>`;
    const h = hue(n);
    return `<span class="br-ic" style="background:hsl(${h} 55% 32%)">${esc(brInitials(n))}</span>`;
  }

  // ---------------------------------------------------------------- state
  const params = new URLSearchParams(location.search);
  const st = {
    sym: trUpper(params.get("symbol") || LS.get("last_symbol", "THYAO")).replace(/[^A-Z0-9]/g, "") || "THYAO",
    tab: LS.get("tab", "derinlik"),
    gen: 0,
    ideal: null,
    lastPrice: null,
    depthN: LS.get("depth_n", 25),
    whale: LS.get("whale", false),
    whaleTh: LS.get("whale_th", 1000000),
    akdPeriod: "daily",
    akdDate: null,
    akdView: LS.get("akd_view", "both") === "total" ? "total" : "both",
    akdExpBuy: false, akdExpSell: false,
    akdSort: "lot",
    akdSortDir: -1,
    akdTSort: "tot",          // v1.21.2 TOPLAM görünümü: toplam lot (alış+satış) varsayılan
    akdTDir: -1,
    akdTopN: LS.get("akd_topn", 3),
    akdExpanded: false,
    akd: null,
    tksExpanded: false,
    tf: LS.get("tf", "5m"),
    favs: LS.get("favs", []),
    recent: LS.get("recent", []),
    alarms: LS.get("alarms", []),
    notes: LS.get("notes", {}),
    back: [],
    list: [],
    listTs: 0,
    status: null,
    seenTrades: new Set(),
  };
  if (!["ozet", "derinlik", "islemler", "akd", "kademe", "takas", "sinyal", "ai"].includes(st.tab)) st.tab = "derinlik";

  // v1.35.0: GET isteklerinde kısa tünel kesintisine karşı 1 sessiz yeniden deneme + görünüm başına «son güncelleme» zamanı
  const LASTOK = {};
  // v1.38.1: tek uçuş (aynı GET adresi zaten yoldaysa aynı yanıt beklenir — yığılma yok); zaman aşımında yeniden deneme YOK
  // (eskiden zaman aşımı → hemen 2. istek → yavaş sunucuda yük ikiye katlanıyordu); ham "signal is aborted" yerine anlaşılır mesaj.
  const INFLIGHT = new Map();
  const API_ST = { slow: 0, fail: 0 };
  function api(url, opts = {}) {
    const get = !opts.method || opts.method === "GET";
    if (get && INFLIGHT.has(url)) return INFLIGHT.get(url);
    const p = apiRaw(url, opts, get);
    if (get) { INFLIGHT.set(url, p); p.then(() => INFLIGHT.delete(url), () => INFLIGHT.delete(url)); }
    return p;
  }
  async function apiRaw(url, opts, get) {
    for (let i = 0; ; i++) {
      const ctl = new AbortController();
      const t0 = Date.now();
      const t = setTimeout(() => ctl.abort(), opts.timeout || 20000);
      try {
        const r = await fetch(url, { cache: "no-store", signal: ctl.signal, method: opts.method || "GET", body: opts.body, headers: opts.headers });
        if (!r.ok) throw new Error("HTTP " + r.status);
        const j = await r.json();
        const dt = Date.now() - t0; API_ST.slow = dt > 3000 ? Math.min(10, API_ST.slow + 1) : Math.max(0, API_ST.slow - 1); API_ST.fail = 0;
        if (get && st.view && !/\/api\/(ideal\/status|ideal\/account|link\/)/.test(url)) LASTOK[st.view] = Date.now();
        return j;
      } catch (e) {
        const abort = e && (e.name === "AbortError" || /abort/i.test(e.message || ""));
        if (abort) { API_ST.fail = Math.min(10, API_ST.fail + 1); throw new Error("sunucu meşgul, tekrar deneniyor"); }
        if (!get || i >= 1 || (e && /HTTP 4/.test(e.message || ""))) { API_ST.fail = Math.min(10, API_ST.fail + 1); throw e; }
        await new Promise((r) => setTimeout(r, 700));
      } finally { clearTimeout(t); }
    }
  }
  // uyarlanır yoklama: yavaş/başarısız yanıtlarda geri çekil, hızlanınca toparlan (ms cinsinden ek bekleme çarpanı)
  function pollMul() { return 1 + API_ST.slow + 2 * API_ST.fail; }
  (function ageBadge() {
    const b = document.createElement("div"); b.id = "upd-age"; b.className = "upd-age"; document.body.appendChild(b);
    setInterval(() => {
      const ts = LASTOK[st.view];
      if (!ts || document.hidden) { b.hidden = true; return; }
      const sec = Math.max(0, Math.round((Date.now() - ts) / 1000));
      b.hidden = false; b.textContent = "son güncelleme " + sec + " sn önce";
      b.classList.toggle("old", sec > 15);
    }, 1000);
  })();
  function toast(msg, ms = 2400) {
    const el = $("toast"); el.textContent = msg; el.hidden = false;
    clearTimeout(toast._t); toast._t = setTimeout(() => (el.hidden = true), ms);
  }

  // ---------------------------------------------------------------- clock
  const clockFmt = new Intl.DateTimeFormat("tr-TR", { timeZone: "Europe/Istanbul", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
  function tickClock() { $("tb-clock").textContent = clockFmt.format(new Date()); }
  setInterval(tickClock, 1000); tickClock();

  // -------------------------------------------------------- live status pill
  // v1.26.4 — dürüst durum rozeti: CANLI (seans açık) · SEANS DIŞI (bağlı, seans kapalı/hafta sonu) · BAĞLANIYOR ·
  // BAĞLANTI YOK (sunucuya art arda ≥2 kez ulaşılamadı) · HATA yalnız gerçek İdealData hatasında (giriş reddi/akış hatası).
  // Tek bir başarısız yoklama (telefon uyku/arka plandan dönüş, anlık ağ kesintisi) artık kırmızı HATA göstermez.
  // v1.27.2 — süreç içi kesinti koruması yeniden bağlarken AMBER «YENİDEN BAĞLANIYOR»; kırmızı HATA yalnız giriş
  // reddinde (login_failed) veya ~2 dk'yı aşan kalıcı hatada. ↻ (sağlıksızken) bağlantıyı uyandırır → «Bağlandı ✓».
  let stFail = 0, stResume = 0, stBadSince = 0;
  const RECON = { active: false, since: 0, t: null };
  function reconWatch(on) {
    if (on) {
      RECON.active = true; RECON.since = Date.now();
      clearInterval(RECON.t); RECON.t = setInterval(() => { if (!document.hidden) loadStatus(); }, 2000);
    } else { RECON.active = false; clearInterval(RECON.t); RECON.t = null; }
  }
  async function loadStatus() {
    if (document.hidden) return;
    const pill = $("live-pill");
    try {
      const s = await api("/api/ideal/status", { timeout: 8000 });
      stFail = 0;
      st.status = s;
      const open = !(s.scan && s.scan.session_open === false);
      if (s.healthy) stBadSince = 0; else if (!stBadSince) stBadSince = Date.now();
      const badSec = s.healthy ? 0 : (s.unhealthy_sec != null ? s.unhealthy_sec : (Date.now() - stBadSince) / 1000);
      const persistent = badSec > 120;
      let cls = s.healthy ? (open ? "live" : "closed") : (s.state === "live" ? "connecting" : (s.state || "init"));
      let txt = "BAĞLANIYOR";
      if (s.healthy) txt = open ? "CANLI" : "SEANS DIŞI";
      else if (s.state === "disabled") txt = "KAPALI";
      else if (s.state === "login_failed") txt = "HATA";
      else if (persistent && s.state === "error") txt = "HATA";
      else if (s.reconnecting || RECON.active || s.state === "error") { txt = "YENİDEN BAĞLANIYOR"; cls = "reconnecting"; }
      pill.className = "live-pill state-" + cls;
      $("live-text").textContent = txt;
      pill.title = s.healthy ? (open ? "İdealData canlı akış" : "İdealData bağlı · BIST seansı kapalı (akşam/hafta sonu) — veriler son seansa ait")
        : txt === "YENİDEN BAĞLANIYOR" ? "İdealData bağlantısı yenileniyor (otomatik koruma) — " + (s.error || s.label || s.state || "—")
        : "İdealData: " + (s.error || s.label || s.state || "—");
      if (RECON.active) {
        if (s.healthy) { reconWatch(false); toast("İdealData bağlandı ✓", 2200); }
        else if (s.state === "login_failed" || Date.now() - RECON.since > 150000) reconWatch(false);
      }
    } catch (e) {
      stFail++;
      if (stFail < 3 || Date.now() - stResume < 12000) { pill.title = "Durum alınamadı, yeniden deneniyor…"; return; }
      pill.className = "live-pill state-error"; $("live-text").textContent = "BAĞLANTI YOK";
      pill.title = "Sunucuya ulaşılamadı (ağ / tünel) — otomatik yeniden deneniyor";
    }
  }
  document.addEventListener("visibilitychange", () => { if (!document.hidden) { stResume = Date.now(); stFail = 0; loadStatus(); } });
  setInterval(loadStatus, 10000); loadStatus();   // v1.35.1: 5→10 sn (tünel kotası)

  // v1.23.1 — üst bardaki ↻ YENİLE: ekranı değiştirmeden mevcut ekranın verisini ve canlı durumu yeniden çeker,
  // takılı yükleme bayraklarını / dönen simgeleri temizler. 4 sn içinde ikinci dokunuş veya yenileme hatası → önbelleksiz tam yeniden yükleme.
  let refBusy = false, refLast = 0;
  function hardReload() {
    try { const u = new URL(location.href); u.searchParams.set("_r", Date.now().toString(36)); location.replace(u.toString()); }
    catch (e) { location.reload(); }
  }
  async function softRefresh() {
    const b = $("btn-refresh"), now = Date.now();
    if (now - refLast < 4000 && !refBusy) { toast("Tam yenileme…", 1200); setTimeout(hardReload, 250); return; }
    if (refBusy) return;
    refBusy = true; refLast = now; b.classList.add("spin");
    try {
      // takılı bayraklar / dönen simgeler
      polling = false;
      try { isl.loading = false; } catch (e) {}
      try { kr.loading = false; } catch (e) {}
      try { ix.busy = false; } catch (e) {}
      try { Object.keys(scrPoll).forEach((k) => { scrPoll[k] = 0; }); } catch (e) {}
      st.listTs = 0;
      document.querySelectorAll(".spin").forEach((x) => { if (x !== b) x.classList.remove("spin"); });
      let alive = await api("/api/ideal/status", { timeout: 8000 }).then(() => true).catch(() => false);
      if (!alive) { await new Promise((r) => setTimeout(r, 1200)); alive = await api("/api/ideal/status", { timeout: 8000 }).then(() => true).catch(() => false); }
      await loadStatus();
      if (!alive) { toast("Sunucuya ulaşılamıyor — bağlantınızı kontrol edip tekrar deneyin (iki kez dokunun: tam yenileme)", 4000); return; }
      // v1.27.2 — son durum sağlıksızsa İdealData bağlantısını da uyandır (sağlıklıyken eskisi gibi; sunucu ≤1/60 sn)
      let recMsg = null;
      const ls = st.status;
      if (ls && !ls.healthy && ls.state !== "disabled") {
        try {
          const r = await api("/api/ideal/reconnect", { method: "POST", timeout: 8000 });
          if (r && r.healthy) recMsg = null;
          else if (r && (r.action === "reconnecting" || r.action === "in_progress")) { recMsg = "İdealData yeniden bağlanıyor…"; reconWatch(true); }
          else if (r && r.action === "rate_limited") { recMsg = "İdealData yeniden bağlanıyor… (yeni deneme " + (r.retry_in || 60) + " sn sonra)"; reconWatch(true); }
          loadStatus();
        } catch (e) { /* uç nokta yoksa ↻ eskisi gibi çalışır */ }
      }
      if (st.view === "stock") { pollIdeal(true); openTab(st.tab, true); }
      else { if (st.view === "op") { OPS.ktok = ""; } go(st.view, { noPush: true, keepScroll: true, keepMode: true }); }
      try { if ($("km-ov") && !$("km-ov").hidden && KM.sym) kmLoad(true); } catch (e) {}
      try { if ($("bd-ov") && !$("bd-ov").hidden && BD.sym) bdLoad(true); } catch (e) {}
      try { pollAlerts(); } catch (e) {}
      toast(recMsg || "Yenilendi ✓", recMsg ? 3000 : 1500);
    } catch (e) {
      toast("Yenilenemedi — sayfa yeniden yükleniyor…", 1800);
      setTimeout(hardReload, 800);
    } finally {
      const el = Date.now() - now;
      setTimeout(() => { b.classList.remove("spin"); refBusy = false; }, Math.max(0, 700 - el));
    }
  }
  $("btn-refresh").addEventListener("click", (e) => { e.preventDefault(); softRefresh(); });

  // -------------------------------------------------------------- stocks
  async function loadList(force) {
    if (!force && st.list.length && Date.now() - st.listTs < 60000) return st.list;
    try {
      const d = await api("/api/lite/stocks", { timeout: 30000 });
      st.list = d.stocks || []; st.listTs = Date.now();
    } catch (e) {}
    return st.list;
  }
  const nameOf = (sym) => { const r = st.list.find((x) => x.s === sym); return r ? r.n : null; };

  function setLogo(el, txtEl, sym) {
    el.classList.remove("has-img"); el.style.backgroundImage = "";
    const h = hue(sym);
    el.style.background = `linear-gradient(135deg, hsl(${h} 45% 26%), hsl(${(h + 40) % 360} 50% 14%))`;
    if (txtEl) txtEl.textContent = sym.slice(0, 2);
    const img = new Image();
    img.onload = () => { el.style.background = `#fff url(/api/logo/${sym}) center/82% no-repeat`; el.classList.add("has-img"); };
    img.src = `/api/logo/${sym}`;
  }

  function selectSymbol(sym, opts = {}) {
    sym = trUpper(sym).replace(/[^A-Z0-9]/g, "");
    if (!sym) return;
    st.fromScreen = false;
    if (sym !== st.sym && !opts.noBack) st.back.push(st.sym);
    st.sym = sym; st.gen++; st.ideal = null; st.lastPrice = null; st.akd = null; st.seenTrades = new Set();
    st.akdExpanded = false; st.akdExpBuy = false; st.akdExpSell = false; st.tksExpanded = false;
    isl.broker = ""; isl.pages = 1; isl.rows = []; isl.brokersSym = null;
    LS.set("last_symbol", sym);
    st.recent = [sym, ...st.recent.filter((s) => s !== sym)].slice(0, 20); LS.set("recent", st.recent);
    if (st.view === "stock" || !st.view) { try { history.replaceState(null, "", "/?symbol=" + sym); } catch (e) {} }
    $("sc-sym").textContent = sym;
    $("sc-name").textContent = nameOf(sym) || "Yükleniyor…";
    $("sc-price").textContent = "—"; $("sc-chg-txt").textContent = "—"; $("sc-chg").className = "chg-pill flat";
    $("sc-turnover").textContent = "— Mn"; $("sc-time").textContent = "--:--:--";
    document.title = `${sym} · BIST Canlı`;
    setLogo($("sc-logo"), $("sc-logo-txt"), sym);
    renderFav(); renderAlarmBadge();
    clearPanes();
    api(`/api/ideal/select/${sym}`, { method: "POST", timeout: 8000 }).catch(() => {});
    pollIdeal(true);
    openTab(st.tab, true);
  }

  function clearPanes() {
    $("depth-body").innerHTML = `<tr><td colspan="6" class="empty">Derinlik yükleniyor…</td></tr>`; $("depth-foot").innerHTML = "";
    $("tape-body").innerHTML = `<tr><td colspan="5" class="empty">İşlemler yükleniyor…</td></tr>`;
    ["akd-body", "akd-body-buy", "akd-body-sell"].forEach((i) => ($(i).innerHTML = `<tr><td colspan="6" class="empty">AKD yükleniyor…</td></tr>`));
    $("isl-body").innerHTML = `<tr><td colspan="5" class="empty">İşlemler yükleniyor…</td></tr>`; $("isl-sums").innerHTML = ""; $("isl-meta").textContent = "—";
    $("kad-body").innerHTML = `<tr><td colspan="5" class="empty">Kademe analizi yükleniyor…</td></tr>`; $("kad-foot").innerHTML = ""; $("kad-sum").innerHTML = "";
    $("tks-body").innerHTML = `<tr><td colspan="6" class="empty">Takas yükleniyor…</td></tr>`; $("tks-sum").innerHTML = "";
    $("sig-card").innerHTML = `<div class="empty">Sinyal yükleniyor…</div>`; $("plan-card").innerHTML = `<div class="empty">İşlem planı yükleniyor…</div>`;
    $("ai-card").innerHTML = `<div class="empty">Yorum hazırlanıyor…</div>`;
    ["lim-tavan", "lim-taban", "lim-yuksek", "lim-dusuk", "lim-aof", "lim-dk"].forEach((i) => ($(i).textContent = "—"));
  }

  // ---------------------------------------------------------------- tabs
  const tabLoaded = {};
  function openTab(tab, force) {
    st.tab = tab; LS.set("tab", tab);
    document.querySelectorAll("#tabs .tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
    document.querySelectorAll(".pane").forEach((p) => (p.hidden = p.dataset.pane !== tab));
    const t = document.querySelector(`#tabs .tab[data-tab="${tab}"]`);
    hCenter(t);
    const key = tab + ":" + st.gen;
    const fresh = force || !tabLoaded[key];
    tabLoaded[key] = Date.now();
    document.body.classList.toggle("wide", tab === "akd" && st.view === "stock");
    if (tab === "derinlik") { if (st.ideal) renderDerinlik(); drApply(); drPoll(true); flLoad(true); }
    else if (tab === "islemler") { loadTrades(true); }
    else if (tab === "akd") { if (fresh || !st.akd) loadAkd(); else renderAkd(); }
    else if (tab === "kademe") { renderKademe(); }
    else if (tab === "takas") { if (fresh) loadTakas(); }
    else if (tab === "ozet") { if (fresh) loadChart(); renderOzet(); loadExtras(); renderOzp(); loadOzp(true); flLoad(true); }
    else if (tab === "sinyal") { if (fresh) loadSignals(); }
    else if (tab === "ai") { loadSignals(true); }
    else if (tab === "operasyon") { opStockLoad(fresh); }
    if (st.kfReady) navActive();
  }
  document.querySelectorAll("#tabs .tab").forEach((b) => b.addEventListener("click", () => openTab(b.dataset.tab)));

  // ----------------------------------------------------------- ideal poll
  let polling = false;
  async function pollIdeal(force) {
    if (polling && !force) return;
    polling = true;
    const gen = st.gen, sym = st.sym, seq = (pollIdeal._seq = (pollIdeal._seq || 0) + 1);
    try {
      // v1.35.1: tek birleşik istek (üst fiyat + derinlik + işlemler) → aynı anlık görüntü, yarı istek
      // v1.37.0: eskiden aşağı kaydırınca (scrollY ≥ 900) ya da "daha fazla" ile >200 satır yüklenince liste "count" moduna
      // düşüp HİÇ güncellenmiyordu → en üstteki saat donuyor, gerçek saatle fark sürekli büyüyordu (kök neden, istemci).
      // Artık zamana göre: her saniye ilk sayfa alınır, yalnız YENİ satırlar üste eklenir (artımlı, en çok 1000 satır);
      // lota/hacme göre: aynı anlık görüntüden ilk sayfa yeniden çizilir.
      const islMode = st.tab === "islemler" && !isl.loading ? (isl.sort !== "time_asc" ? "full" : "count") : "";
      const islQ = islMode ? "&isl=" + encodeURIComponent(islUrl(0, islMode === "full" ? isl.PAGE : 1).split("?")[1]) : "";
      const d = await api(`/api/live/${sym}?trades=200${islQ}`, { timeout: 8000 });
      if (gen !== st.gen) return;
      if (seq < (pollIdeal._done || 0)) return;   // v1.37.0: geç gelen eski yanıtı at (sıra no.)
      pollIdeal._done = seq;
      st.ideal = d;
      renderHeader();
      if (st.tab === "derinlik") renderDerinlik();
      else if (st.tab === "kademe" && (force || Date.now() - (renderKademe._ts || 0) > 5000)) renderKademe();
      else if (st.tab === "ozet") renderOzet();
      else if (st.tab === "islemler" && d.isl && gen === st.gen) {   // v1.35.1: işlemler aynı yanıttan
        try {
          if (islMode === "full") loadTrades(false, false, d.isl);
          else { const n = d.isl.total - isl.total; if (n > 0 && isl.sort === "time") { $("isl-new").hidden = false; $("isl-new").textContent = `↑ ${fN(n)} yeni işlem`; } }
        } catch (x) {}
      }
      checkAlarms(sym, d.quote && d.quote.price);
    } catch (e) {
      if (gen === st.gen && !st.ideal) {
        $("depth-body").innerHTML = `<tr><td colspan="6" class="empty">Canlı veri alınamadı (${esc(e.message || e)})</td></tr>`;
      }
    } finally { polling = false; }
  }
  setInterval(() => {
    if (document.hidden || st.view !== "stock") return;
    // v1.35.0: üst fiyat + derinlik + işlemler her sekmede 1 sn · v1.38.1: canlı akış yokken (seans dışı) 5 sn; yavaş sunucuda geri çekil
    const fd = (st.ideal && st.ideal.feed) || {};
    const base = fd.healthy === false ? 5000 : 1000;
    if (Date.now() - (pollIdeal._last || 0) < base * pollMul() - 50) return;
    pollIdeal._last = Date.now(); pollIdeal();
  }, 1000);
  setInterval(() => { if (!document.hidden) api(`/api/ideal/select/${st.sym}`, { method: "POST", timeout: 8000 }).catch(() => {}); }, 60000);

  // --------------------------------------------------------------- header
  function renderHeader() {
    const d = st.ideal; if (!d) return;
    const q = d.quote || {};
    const nm = nameOf(st.sym) || d.name;
    if (nm) $("sc-name").textContent = nm;
    const p = q.price;
    const pe = $("sc-price");
    if (isNum(p)) {
      const txt = "₺" + fP(p);
      if (pe.textContent !== txt) {
        if (isNum(st.lastPrice) && p !== st.lastPrice) {
          pe.classList.remove("flash-up", "flash-down"); void pe.offsetWidth;
          pe.classList.add(p > st.lastPrice ? "flash-up" : "flash-down");
        }
        pe.textContent = txt;
      }
      st.lastPrice = p;
    } else pe.textContent = "—";
    const c = q.change_pct;
    $("sc-chg").className = "chg-pill " + cls(c);
    $("sc-chg-txt").textContent = isNum(c) ? (c >= 0 ? "+" : "") + nf(2).format(c) + "%" : "—";
    $("sc-turnover").textContent = isNum(q.turnover) ? fShort(q.turnover).replace(" bin", " bin") + " ₺" : "— Mn";
    $("sc-time").textContent = q.time || "--:--:--";
  }

  // ------------------------------------------------------------- DERİNLİK
  function renderDerinlik() {
    const d = st.ideal; if (!d) return;
    const q = d.quote || {}, lim = d.limits || {};
    $("lim-tavan").textContent = fP(q.ceiling || lim.ceiling);
    $("lim-taban").textContent = fP(q.floor || lim.floor);
    $("lim-yuksek").textContent = fP(q.high || lim.high);
    $("lim-dusuk").textContent = fP(q.low || lim.low);
    $("lim-aof").textContent = fP(q.vwap || lim.vwap);
    // Devre kesici (tahmini): BIST pay bazında aşağı yönlü %5; referans = son tek fiyat (açılış) yoksa baz fiyat
    const ref = isNum(q.open) && q.open > 0 ? q.open : q.previous_close;
    const dkEl = $("lim-dk");
    if (isNum(ref) && ref > 0) {
      const t = tickOf(ref);
      const v = Math.ceil((ref * 0.95) / t - 1e-9) * t;
      dkEl.textContent = fP(v);
      dkEl.parentElement.title = `Tahmini devre kesici (aşağı yönlü %5): referans ${fP(ref)} (${isNum(q.open) && q.open > 0 ? "açılış" : "önceki kapanış"}) × 0,95. İdealData doğrudan DK fiyatı yayınlamıyor.`;
    } else dkEl.textContent = "—";

    const dp = d.depth;
    const body = $("depth-body"), foot = $("depth-foot");
    if (!dp || (!(dp.bids || []).length && !(dp.asks || []).length)) {
      body.innerHTML = `<tr><td colspan="6" class="empty">${d.feed && !d.feed.healthy ? "İdealData bağlantısı yok" : "Derinlik verisi bekleniyor…"}</td></tr>`;
      foot.innerHTML = "";
    } else {
      const N = st.depthN;
      const bids = (dp.bids || []).slice(0, N), asks = (dp.asks || []).slice(0, N);
      const rows = Math.max(bids.length, asks.length);
      let mx = 1;
      for (const r of bids) mx = Math.max(mx, r.lot || 0);
      for (const r of asks) mx = Math.max(mx, r.lot || 0);
      let h = "";
      let bo = 0, bl = 0, bv = 0, ao = 0, al = 0, av = 0;
      const TG = drLadderTags(bids, asks);   // v1.25.0 POC / VWAP / maliyet / 🏛 / 🧱 etiketleri
      for (let i = 0; i < rows; i++) {
        const b = bids[i] || {}, a = asks[i] || {};
        const bOk = isNum(b.price) && b.price > 0 && (b.lot || 0) > 0;
        const aOk = isNum(a.price) && a.price > 0 && (a.lot || 0) > 0;
        if (bOk) { bo += b.orders || 0; bl += b.lot; bv += b.lot * b.price; }
        if (aOk) { ao += a.orders || 0; al += a.lot; av += a.lot * a.price; }
        const wb = bOk ? Math.max(1.5, (b.lot / mx) * 50) : 0, wa = aOk ? Math.max(1.5, (a.lot / mx) * 50) : 0;
        const bg = `background-image:linear-gradient(90deg,transparent calc(50% - ${wb.toFixed(2)}%),rgba(34,197,94,.20) calc(50% - ${wb.toFixed(2)}%),rgba(34,197,94,.20) 50%,rgba(239,68,68,.20) 50%,rgba(239,68,68,.20) calc(50% + ${wa.toFixed(2)}%),transparent calc(50% + ${wa.toFixed(2)}%))`;
        h += `<tr class="${i === 0 ? "first" : ""}" style="${bg}">
          <td class="b-emir">${bOk ? fN(b.orders) : ""}</td><td class="b-lot">${bOk ? fN(b.lot) : ""}</td><td class="b-px">${bOk ? fP(b.price) + (TG.b[i] ? `<span class="dr-tgs">${TG.b[i].join("")}</span>` : "") : ""}</td>
          <td class="a-px">${aOk ? fP(a.price) + (TG.a[i] ? `<span class="dr-tgs">${TG.a[i].join("")}</span>` : "") : ""}</td><td class="a-lot">${aOk ? fN(a.lot) : ""}</td><td class="a-emir">${aOk ? fN(a.orders) : ""}</td></tr>`;
      }
      if (!h || (!bl && !al)) h = `<tr><td colspan="6" class="empty">Defter boş — tek fiyat / emir toplama aşamasında olabilir</td></tr>`;
      body.innerHTML = h;
      const bAvg = bl ? bv / bl : null, aAvg = al ? av / al : null;
      foot.innerHTML = `<tr><td>${fN(bo)}</td><td class="pos">${fN(bl)}</td><td class="pos">${fP(bAvg)}</td><td class="neg">${fP(aAvg)}</td><td class="neg">${fN(al)}</td><td>${fN(ao)}</td></tr>
        <tr class="cum"><td colspan="2"><span class="flab">TÜM DEFTER ALIŞ</span>${fN(dp.book_bid_total)}</td><td>${fP(dp.book_bid_avg)}</td><td>${fP(dp.book_ask_avg)}</td><td colspan="2"><span class="flab">TÜM DEFTER SATIŞ</span>${fN(dp.book_ask_total)}</td></tr>`;
      const tot = bl + al;
      const bp = tot > 0 ? (bl / tot) * 100 : 50;
      $("press-fill").style.width = bp.toFixed(1) + "%";
      $("press-buy").textContent = `Alış %${nf(0).format(bp)}`;
      $("press-sell").textContent = `%${nf(0).format(100 - bp)} Satış`;
      const nL = Math.max(bids.length, asks.length);
      const p25 = isNum(dp.pressure_pct) ? dp.pressure_pct : bp;
      $("p25-fill").style.width = p25.toFixed(1) + "%";
      $("p25-b").textContent = "%" + nf(1).format(p25); $("p25-s").textContent = "%" + nf(1).format(100 - p25);
      const bt = dp.book_bid_total, at = dp.book_ask_total;
      if (isNum(bt) && isNum(at) && bt + at > 0) {
        const pa = (bt / (bt + at)) * 100;
        $("pall-fill").style.width = pa.toFixed(1) + "%";
        $("pall-b").textContent = "%" + nf(1).format(pa); $("pall-s").textContent = "%" + nf(1).format(100 - pa);
        mkLegend();   // v1.26.0 "İşaretler ne demek?"
      $("p2-note").textContent = `25 kademe: ${fN(dp.bid_lot)} / ${fN(dp.ask_lot)} lot · Tüm defter: ${fN(bt)} / ${fN(at)} lot (İdealData ayrıntıyı ${nL} kademe verir; tüm defter toplamı feed'den).`;
      } else { $("pall-b").textContent = "%—"; $("pall-s").textContent = "%—"; }
    }
    renderTape();
  }

  function renderTape() {
    const d = st.ideal; if (!d) return;
    const s = d.summary || {};
    const tb = s.tape_buy_lot || 0, ts = s.tape_sell_lot || 0, tt = tb + ts;
    const bp = tt > 0 ? (tb / tt) * 100 : 50;
    $("tape-fill").style.width = bp.toFixed(1) + "%";
    $("tape-buy").textContent = `Alım: ${fShort(tb)} lot (%${nf(0).format(bp)})`;
    $("tape-sell").textContent = `Satım: ${fShort(ts)} lot (%${nf(0).format(100 - bp)})`;
    let trades = d.trades || [];
    const th = st.whaleTh;
    if (st.whale) trades = trades.filter((t) => (t.lot || 0) * (t.price || 0) >= th);
    const body = $("tape-body");
    if (!trades.length) {
      body.innerHTML = `<tr><td colspan="5" class="empty">${st.whale ? `Eşik üstü (${fShort(th)} ₺) işlem yok` : "İşlem bekleniyor…"}</td></tr>`;
      return;
    }
    const first = st.seenTrades.size === 0;
    const seen = new Set();
    let h = "";
    for (const t of trades.slice(0, 100)) {
      const key = `${t.time}|${t.price}|${t.lot}|${t.buyer}|${t.seller}|${t.ts}`;
      seen.add(key);
      const isNew = !first && !st.seenTrades.has(key);
      const side = t.side === "buy" ? "buy" : t.side === "sell" ? "sell" : "";
      const whale = (t.lot || 0) * (t.price || 0) >= th;
      h += `<tr class="${side}${whale ? " whale" : ""}${isNew ? " new" : ""}"${t.side === "auction" ? ' title="Tek fiyat eşleşmesi"' : ""}>
        <td>${esc(t.time || "")}</td><td class="px">${fP(t.price)}</td><td class="lt">${fN(t.lot)}</td>
        <td class="br" title="${esc(brName(t.buyer))}">${esc(brName(t.buyer) || "—")}</td><td class="br" title="${esc(brName(t.seller))}">${esc(brName(t.seller) || "—")}</td></tr>`;
    }
    st.seenTrades = seen;
    body.innerHTML = h;
  }
  $("depth-levels").value = String(st.depthN);
  $("depth-levels").addEventListener("change", (e) => { st.depthN = +e.target.value; LS.set("depth_n", st.depthN); renderDerinlik(); });
  $("whale-toggle").checked = !!st.whale;
  $("whale-toggle").addEventListener("change", (e) => { st.whale = e.target.checked; LS.set("whale", st.whale); renderTape(); });
  $("whale-th").value = String(st.whaleTh);
  if ($("whale-th").value !== String(st.whaleTh)) $("whale-th").value = "1000000";
  $("whale-th").addEventListener("change", (e) => { st.whaleTh = +e.target.value; LS.set("whale_th", st.whaleTh); renderTape(); });

  // ------------------------------------------------------------------ AKD
  let akdReq = 0;
  function syncAkdPeriod() {
    document.querySelectorAll("#akd-periods .pb-item").forEach((x) => x.classList.toggle("active", x.dataset.period === st.akdPeriod));
  }
  async function loadAkd() {
    const gen = st.gen, sym = st.sym, rq = ++akdReq;
    syncAkdPeriod();
    const btn = $("akd-refresh"); btn.classList.add("spin");
    let url = `/api/ideal/${sym}/akd?period=${st.akdPeriod}`;
    if (st.akdPeriod === "custom" && st.akdDate) url += `&from=${st.akdDate}&to=${st.akdDate}`;
    try {
      const d = await api(url, { timeout: 20000 });
      if (gen !== st.gen || rq !== akdReq) return;
      st.akd = d; st.akdTs = Date.now();
      renderAkd();
      akpLoad();   // v1.26.0 K/Z + AKD ANALİZİ (aynı dönem, aynı kaynak)
    } catch (e) {
      if (gen === st.gen) ["akd-body", "akd-body-buy", "akd-body-sell"].forEach((i) => ($(i).innerHTML = `<tr><td colspan="6" class="empty">AKD alınamadı (${esc(e.message || e)})</td></tr>`));
    } finally { btn.classList.remove("spin"); }
  }
  // v1.27.1 İLK N yönlü %: |ALAN − SATAN| ÷ max(ALAN, SATAN) × 100 (+ Alan / − Satan) — örn. 100.000 / 50.000 → %50 Alan
  function ilkPct(a, s) { const m = Math.max(a || 0, s || 0); return m > 0 ? ((a || 0) - (s || 0)) / m * 100 : null; }
  function ilkPctTxt(p) { return isNum(p) ? `%${nf(1).format(Math.abs(p))} ${p > 0 ? "Alan" : p < 0 ? "Satan" : "denge"}` : "—"; }
  function aggOther(rows) {
    let lot = 0, val = 0, pct = 0;
    for (const r of rows) { const l = Math.abs(r._lot || 0); lot += l; if (isNum(r.cost)) val += l * r.cost; pct += r._pct || 0; }
    return { lot, cost: lot ? val / lot : null, pct };
  }
  function renderAkd() {
    const d = st.akd; if (!d) return;
    const per = d.label || "BUGÜN";
    $("akd-label").textContent = d.from && d.to && d.from !== d.to ? `${fmtYmd(d.from)} – ${fmtYmd(d.to)}` : per;
    document.querySelectorAll("#akd-periods .pb-item").forEach((b) => b.classList.toggle("active", b.dataset.period === st.akdPeriod));
    const body = $("akd-body"), more = $("akd-more");
    const note = $("akd-note");
    note.textContent = `Kaynak: İdealData AKD · ${d.range || ""}${d.age_sec != null ? " · " + Math.round(d.age_sec) + " sn önce" : ""}`;
    // top-N net card
    const N = st.akdTopN;
    const card = document.querySelector(".top-net-card");
    card.classList.toggle("hidden-vals", N === 0);
    document.querySelectorAll("#topn-seg button").forEach((b) => b.classList.toggle("active", +b.dataset.n === N));
    $("topnet-title").textContent = N ? `İLK ${N} NET PGÇ` : "İLK NET PGÇ";
    const buyers = d.buyers || [], sellers = d.sellers || [];
    if (N) {
      const al = buyers.slice(0, N).reduce((a, r) => a + (r.net_lot || 0), 0);
      const sa = sellers.slice(0, N).reduce((a, r) => a + Math.abs(r.net_lot || 0), 0);
      const net = al - sa;
      $("tn-alan").textContent = fN(al); $("tn-satan").textContent = fN(sa);
      $("tn-net-k").textContent = net >= 0 ? "NET ALAN" : "NET SATAN";
      $("tn-net").textContent = fN(Math.abs(net)); $("tn-net").className = "tv " + (net >= 0 ? "pos" : "neg");
      const pc = ilkPct(al, sa), pe = $("tn-pct");   // v1.27.1 yönlü % = |ALAN − SATAN| ÷ max(ALAN, SATAN)
      if (pe) { pe.textContent = isNum(pc) ? ilkPctTxt(pc) : "—"; pe.className = "tn-pc " + (isNum(pc) ? (pc > 0 ? "pos" : pc < 0 ? "neg" : "muted") : "muted"); pe.title = `|ALAN − SATAN| ÷ max(ALAN, SATAN) × 100 = |${fN(al)} − ${fN(sa)}| ÷ ${fN(Math.max(al, sa))} × 100`; }
    }
    const dual = $("akd-dual"), totalBox = $("akd-total");
    const view = st.akdView;
    document.querySelectorAll("#akd-seg button").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
    dual.hidden = view === "total"; totalBox.hidden = view !== "total";
    const isTot = view === "total";
    const dir = isTot ? st.akdTDir : st.akdSortDir;
    const curSort = isTot ? st.akdTSort : st.akdSort;
    document.querySelectorAll(".sort-row .sort-btn").forEach((b) => {
      if (b.dataset.sort === "tot") b.hidden = !isTot;
      const on = (isTot && b.dataset.sort === "lot" ? "net" : b.dataset.sort) === curSort;
      b.classList.toggle("active", on);
      b.querySelector(".arr").textContent = on ? (dir < 0 ? "↓" : "↑") : "";
    });
    if (!d.available) {
      const msg = `<tr><td colspan="6" class="empty">${esc(d.note || "Bu dönem için AKD verisi yok")}</td></tr>`;
      ["akd-body", "akd-body-buy", "akd-body-sell"].forEach((i) => ($(i).innerHTML = msg)); $("akd-foot").innerHTML = "";
      ["akd-more", "akd-more-buy", "akd-more-sell"].forEach((i) => ($(i).hidden = true));
      return;
    }
    const sortRows = (rows, isTotal) => {
      if (st.akdSort === "cost") rows.sort((a, b) => dir * ((a.cost || 0) - (b.cost || 0)));
      else if (isTotal) rows.sort((a, b) => dir * ((a._lot || 0) - (b._lot || 0)));
      else rows.sort((a, b) => dir * (Math.abs(a._lot || 0) - Math.abs(b._lot || 0)));
      return rows;
    };
    const fill = (bodyId, moreId, rows, kind, expanded, emptyTxt) => {
      const body = $(bodyId), more = $(moreId);
      if (!rows.length) { body.innerHTML = `<tr><td colspan="6" class="empty">${emptyTxt}</td></tr>`; more.hidden = true; return; }
      const LIMIT = 5;
      const show = expanded ? rows : rows.slice(0, LIMIT);
      const rest = expanded ? [] : rows.slice(LIMIT);
      const mxPct = Math.max(...rows.map((r) => r._pct || 0), 1);
      let h = "", i = 0;
      for (const r of show) {
        i++;
        const lotCls = kind === "buy" ? "pos" : kind === "sell" ? "neg" : cls(r._lot);
        const barCls = kind === "buy" || (kind === "total" && r._lot > 0) ? "bar-buy" : "bar-sell";
        const w = Math.min(100, ((r._pct || 0) / mxPct) * 100);
        h += `<tr class="${barCls}" style="--w:${w.toFixed(1)}%"><td class="no">${i}</td><td class="ic">${brIcon(r.broker)}</td>
          <td class="kn" data-k5br="${esc(r.broker)}" title="${esc(brName(r.broker))}">${esc(brName(r.broker))}</td>
          <td class="${lotCls}">${fN(kind === "total" ? r._lot : Math.abs(r._lot))}</td><td>${fP(r.cost)}</td><td class="dg">%${nf(1).format(r._pct || 0)}</td></tr>`;
      }
      if (rest.length) {
        const o = aggOther(rest);
        const w = Math.min(100, (o.pct / mxPct) * 100);
        const lotCls = kind === "buy" ? "pos" : kind === "sell" ? "neg" : "";
        h += `<tr class="other ${kind === "sell" ? "bar-sell" : "bar-buy"}" style="--w:${w.toFixed(1)}%"><td class="no"></td><td class="ic">${brIcon("", true)}</td>
          <td class="kn">DİĞER KURUMLAR</td><td class="${lotCls}">${fN(o.lot)}</td><td>${fP(o.cost)}</td><td class="dg">%${nf(1).format(o.pct)}</td></tr>`;
      }
      body.innerHTML = h;
      more.hidden = !rest.length && !expanded;
      more.textContent = expanded ? "Daha Az Göster" : `Diğerlerini Göster (+${rest.length})`;
    };
    if (view === "total") {
      // v1.21.1: TOPLAM = tüm kurumlar (İdealData AKD "TOPLAM" listesi: alış/satış/net lot) — net alıcılar üstte, net satıcılar altta
      renderAkdTotal(d, buyers, sellers);
    } else {
      const br = sortRows(buyers.map((r) => ({ ...r, _lot: r.net_lot, _pct: r.pct })), false);
      const sr = sortRows(sellers.map((r) => ({ ...r, _lot: r.net_lot, _pct: r.pct })), false);
      $("akd-cnt-buy").textContent = br.length ? `· ${br.length} kurum` : "";
      $("akd-cnt-sell").textContent = sr.length ? `· ${sr.length} kurum` : "";
      fill("akd-body-buy", "akd-more-buy", br, "buy", st.akdExpBuy, "Net alıcı kurum yok");
      fill("akd-body-sell", "akd-more-sell", sr, "sell", st.akdExpSell, "Net satıcı kurum yok");
    }
  }
  function renderAkdTotal(d, buyers, sellers) {
    // v1.21.2: TOPLAM AKD = kurum başına alış lot + satış lot (toplam lot); varsayılan sıralama toplam lot ↓
    const src = Array.isArray(d.total) && d.total.length ? d.total : [...buyers, ...sellers];
    const seen = new Set();
    const rows = src.filter((r) => r && r.broker && !seen.has(r.broker) && seen.add(r.broker)).map((r) => {
      const b = isNum(r.buy_lot) ? r.buy_lot : null, s = isNum(r.sell_lot) ? r.sell_lot : null;
      const net = isNum(r.net_lot) ? r.net_lot : (b != null && s != null ? b - s : 0);
      const tot = b != null || s != null ? (b || 0) + (s || 0) : (isNum(r.total_lot) ? r.total_lot : Math.abs(net));
      return { broker: r.broker, b, s, net, tot, cost: r.cost, kz: isNum(r.pnl_tl) ? r.pnl_tl : null, kzp: isNum(r.pnl_pct) ? r.pnl_pct : null };
    });
    const sumTot = rows.reduce((a, r) => a + r.tot, 0);
    for (const r of rows) r.pay = sumTot ? (r.tot / sumTot) * 100 : 0;
    const k = st.akdTSort, dir = st.akdTDir;
    if (k === "cost") rows.sort((a, b) => (isNum(a.cost) ? 0 : 1) - (isNum(b.cost) ? 0 : 1) || dir * ((a.cost || 0) - (b.cost || 0)));
    else if (k === "net") rows.sort((a, b) => dir * (a.net - b.net));
    else rows.sort((a, b) => dir * (a.tot - b.tot) || b.net - a.net);
    const body = $("akd-body"), foot = $("akd-foot"), more = $("akd-more");
    if (!rows.length) { body.innerHTML = `<tr><td colspan="10" class="empty">Veri yok</td></tr>`; foot.innerHTML = ""; more.hidden = true; return; }
    const LIMIT = 5, exp = st.akdExpanded;
    const show = exp ? rows : rows.slice(0, LIMIT), rest = exp ? [] : rows.slice(LIMIT);
    const mxPay = Math.max(...rows.map((r) => r.pay), 1);
    // uzun dönemlerde (9+ haneli lot) alış/satış/net kısaltılır ki 412px ekrana sığsın; toplam lot satırlarda tam gösterilir
    const big = Math.max(...rows.map((r) => Math.max(r.b || 0, r.s || 0))) >= 1e7;
    const fL = (v) => (big ? fShort(v) : fN(v));
    const sgn = (v) => `<td class="${v > 0 ? "pos" : v < 0 ? "neg" : ""}" title="${fN(v)}">${v > 0 ? "+" : ""}${fL(v)}</td>`;
    const kzTd = (v) => `<td class="${cls(v)}" title="${isNum(v) ? fN(v, 0) + " ₺" : ""}">${isNum(v) ? (v > 0 ? "+" : v < 0 ? "−" : "") + fShort(Math.abs(v)) : "—"}</td>`;   // v1.26.0 K/Z
    const line = (r, i, other) => {
      const w = Math.min(100, (r.pay / mxPay) * 100);
      return `<tr class="${other ? "other " : ""}${r.net >= 0 ? "bar-buy" : "bar-sell"}" style="--w:${w.toFixed(1)}%"><td class="no">${other ? "" : i}</td>
        <td class="kn"${other ? "" : ` data-k5br="${esc(r.broker)}"`} title="${esc(other ? "Diğer kurumlar" : brName(r.broker))}">${other ? "DİĞER KURUMLAR" : esc(brName(r.broker))}</td>
        <td class="tl-main">${fN(r.tot)}</td><td title="${r.b != null ? fN(r.b) : ""}">${r.b != null ? fL(r.b) : "—"}</td><td title="${r.s != null ? fN(r.s) : ""}">${r.s != null ? fL(r.s) : "—"}</td>
        ${sgn(r.net)}<td>${fP(r.cost)}</td><td class="dg">%${nf(1).format(r.pay)}</td>${kzTd(r.kz)}<td class="${cls(r.kzp)}">${isNum(r.kzp) ? (r.kzp > 0 ? "+" : "") + nf(2).format(r.kzp) + "%" : "—"}</td></tr>`;
    };
    let h = show.map((r, i) => line(r, i + 1, false)).join("");
    if (rest.length) {
      const o = { b: 0, s: 0, net: 0, tot: 0, pay: 0, kz: 0, kzp: null }; let cv = 0, cl = 0;
      for (const r of rest) { o.kz += r.kz || 0; o.b += r.b || 0; o.s += r.s || 0; o.net += r.net; o.tot += r.tot; o.pay += r.pay; if (isNum(r.cost) && r.net) { cv += r.cost * Math.abs(r.net); cl += Math.abs(r.net); } }
      o.cost = cl ? cv / cl : null;
      h += line(o, 0, true);
    }
    body.innerHTML = h;
    more.hidden = !rest.length && !exp;
    more.textContent = exp ? "Daha Az Göster" : `Diğerlerini Göster (+${rest.length})`;
    const sb = rows.reduce((a, r) => a + (r.b || 0), 0), ss = rows.reduce((a, r) => a + (r.s || 0), 0), sn = rows.reduce((a, r) => a + r.net, 0);
    const nb = rows.filter((r) => r.net > 0).length, ns = rows.filter((r) => r.net < 0).length;
    foot.innerHTML = `<tr class="akd-tot-row"><td class="no"></td><td class="kn" title="${nb} net alıcı / ${ns} net satıcı">TOPLAM · ${rows.length}</td>
      <td class="tl-main" title="${fN(sumTot)}">${sumTot >= 1e8 ? fShort(sumTot) : fN(sumTot)}</td><td title="${fN(sb)}">${fL(sb)}</td><td title="${fN(ss)}">${fL(ss)}</td>${sgn(sn)}<td>—</td><td class="dg">%100</td>${kzTd(rows.reduce((a, r) => a + (r.kz || 0), 0))}<td>—</td></tr>`;
  }
  $("akd-refresh").addEventListener("click", loadAkd);
  $("akd-more").addEventListener("click", () => { st.akdExpanded = !st.akdExpanded; renderAkd(); });
  $("akd-more-buy").addEventListener("click", () => { st.akdExpBuy = !st.akdExpBuy; renderAkd(); });
  $("akd-more-sell").addEventListener("click", () => { st.akdExpSell = !st.akdExpSell; renderAkd(); });
  document.querySelectorAll("#akd-seg button").forEach((b) => b.addEventListener("click", () => {
    st.akdView = b.dataset.view; LS.set("akd_view", st.akdView); st.akdExpanded = false; renderAkd();
  }));
  document.querySelectorAll("#topn-seg button").forEach((b) => b.addEventListener("click", () => {
    st.akdTopN = +b.dataset.n; LS.set("akd_topn", st.akdTopN); renderAkd();
  }));
  document.querySelectorAll(".sort-row .sort-btn").forEach((b) => b.addEventListener("click", () => {
    if (st.akdView === "total") {
      const k = b.dataset.sort === "lot" ? "net" : b.dataset.sort;
      if (st.akdTSort === k) st.akdTDir *= -1; else { st.akdTSort = k; st.akdTDir = -1; }
      st.akdExpanded = false;
    } else if (b.dataset.sort === "tot") return;
    else if (st.akdSort === b.dataset.sort) st.akdSortDir *= -1; else { st.akdSort = b.dataset.sort; st.akdSortDir = -1; }
    renderAkd();
  }));
  document.querySelectorAll("#akd-periods .pb-item").forEach((b) => {
    if (b.dataset.period === "custom") return;
    b.addEventListener("click", (e) => {
      if (e.target.tagName === "SELECT") return;
      st.akdPeriod = b.dataset.period; st.akdExpanded = false; st.akdExpBuy = false; st.akdExpSell = false; loadAkd();
    });
  });
  $("akd-daily-sel").addEventListener("change", () => { st.akdPeriod = "daily"; loadAkd(); });
  $("akd-daily-sel").addEventListener("click", () => { if (st.akdPeriod !== "daily") { st.akdPeriod = "daily"; loadAkd(); } });
  $("akd-date").max = ymd(new Date());
  $("akd-date").addEventListener("change", (e) => {
    if (!e.target.value) return;
    st.akdPeriod = "custom"; st.akdDate = e.target.value; st.akdExpanded = false; loadAkd();
  });
  document.querySelector('#akd-periods .pb-date').addEventListener("click", () => {
    const inp = $("akd-date");
    if (inp.showPicker) { try { inp.showPicker(); } catch (e) {} }
  });
  setInterval(() => { if (!document.hidden && st.tab === "akd" && st.akdPeriod === "daily" && Date.now() - (st.akdTs || 0) > 30000) loadAkd(); }, 5000);

  // --------------------------------------------------------------- KADEME
  function renderKademe() {
    renderKademe._ts = Date.now();
    const d = st.ideal;
    const sum = $("kad-sum"), body = $("kad-body"), foot = $("kad-foot");
    if (!d) return;
    const fp = d.footprint;
    const levels = (fp && fp.levels) || [];
    if (!levels.length) {
      body.innerHTML = `<tr><td colspan="5" class="empty">${d.feed && !d.feed.healthy ? "İdealData bağlantısı yok" : "Bugün için kademe analizi verisi yok (işlem olmamış olabilir)"}</td></tr>`;
      foot.innerHTML = ""; sum.innerHTML = ""; return;
    }
    const rows = [...levels].sort((a, b) => b.price - a.price);
    let T = 0, B = 0, S = 0, PB = 0, PS = 0, PT = 0, poc = rows[0];
    for (const r of rows) {
      const t = r.total_volume || 0, b = r.buy_volume || 0, s = r.sell_volume || 0;
      T += t; B += b; S += s; PB += r.price * b; PS += r.price * s; PT += r.price * t;
      if (t > (poc.total_volume || 0)) poc = r;
    }
    const N = Math.max(0, T - B - S);
    const k = (lab, v, c = "") => `<div class="ks"><span class="k">${lab}</span><span class="v ${c}">${v}</span></div>`;
    sum.innerHTML = k("TOPLAM LOT", fShort(T)) + k("ALIŞ LOT", fShort(B), "pos") + k("SATIŞ LOT", fShort(S), "neg") + k("YÖNSÜZ", fShort(N)) +
      k("NET LOT", fShort(B - S), cls(B - S)) + k("ALIŞ ORT", fP(B ? PB / B : null), "pos") + k("SATIŞ ORT", fP(S ? PS / S : null), "neg") + k("AORT", fP(T ? PT / T : null));
    const last = (d.quote || {}).price;
    let cur = null;
    if (isNum(last)) { let best = Infinity; for (const r of rows) { const df = Math.abs(r.price - last); if (df < best) { best = df; cur = r; } } }
    let h = "";
    for (const r of rows) {
      const t = r.total_volume || 0, b = r.buy_volume || 0, s = r.sell_volume || 0, n = Math.max(0, t - b - s);
      const share = T ? (t / T) * 100 : 0;
      const ap = isNum(r.buy_pct) ? r.buy_pct : t ? (b / t) * 100 : 0;
      const sp = isNum(r.sell_pct) ? r.sell_pct : t ? (s / t) * 100 : 0;
      const c = [r === cur ? "cur" : "", r === poc ? "poc" : ""].join(" ").trim();
      h += `<tr class="${c}"><td class="px">${fP(r.price)}</td><td>${fN(t)}<span class="shr">%${nf(1).format(share)}</span></td>
        <td class="sp"><div class="split"><span class="b" style="width:${t ? (b / t) * 100 : 0}%"></span><span class="n" style="width:${t ? (n / t) * 100 : 0}%"></span><span class="s" style="width:${t ? (s / t) * 100 : 0}%"></span></div></td>
        <td class="pos">%${nf(0).format(ap)}</td><td class="neg">%${nf(0).format(sp)}</td></tr>`;
    }
    body.innerHTML = h;
    foot.innerHTML = `<tr><td class="px">TOPLAM</td><td>${fN(T)}</td><td class="sp"><div class="split"><span class="b" style="width:${T ? (B / T) * 100 : 0}%"></span><span class="n" style="width:${T ? (N / T) * 100 : 0}%"></span><span class="s" style="width:${T ? (S / T) * 100 : 0}%"></span></div></td>
      <td class="pos">%${nf(0).format(T ? (B / T) * 100 : 0)}</td><td class="neg">%${nf(0).format(T ? (S / T) * 100 : 0)}</td></tr>`;
    $("kad-note").textContent = `Kaynak: İdealData kademe analizi (gerçek alış/satış) · ${rows.length} kademe · POC ${fP(poc.price)}${fp.age_sec != null ? " · " + Math.round(fp.age_sec) + " sn önce" : ""}`;
    $("kad-label").textContent = "BUGÜN";
  }
  $("kad-refresh").addEventListener("click", async () => {
    const b = $("kad-refresh"); b.classList.add("spin");
    try { await api(`/api/ideal/select/${st.sym}`, { method: "POST" }); } catch (e) {}
    setTimeout(async () => { await pollIdeal(true); renderKademe(); b.classList.remove("spin"); }, 900);
  });

  // ---------------------------------------------------------------- TAKAS
  async function loadTakas() {
    const gen = st.gen, sym = st.sym;
    const b = $("tks-refresh"); b.classList.add("spin");
    try {
      const d = await api(`/api/ideal/${sym}/takas?compare=${st.tksPer || "w1"}`, { timeout: 25000 });
      if (gen !== st.gen) return;
      st.takas = d; renderTakas();
    } catch (e) {
      if (gen === st.gen) $("tks-body").innerHTML = `<tr><td colspan="6" class="empty">Takas alınamadı (${esc(e.message || e)})</td></tr>`;
    } finally { b.classList.remove("spin"); }
  }
  function renderTakas() {
    const d = st.takas; if (!d) return;
    const body = $("tks-body"), more = $("tks-more"), sum = $("tks-sum");
    if (!d.available || !(d.rows || []).length) {
      $("tks-label").textContent = "—"; sum.innerHTML = "";
      body.innerHTML = `<tr><td colspan="6" class="empty">Takas verisi yok — ${esc(d.note || "İdealData yanıt vermedi")}</td></tr>`;
      $("tks-body-al").innerHTML = $("tks-body-sat").innerHTML = body.innerHTML; $("tks-al-sum").textContent = $("tks-sat-sum").textContent = "—";
      $("tks-dual").hidden = (st.tksView || "both") !== "both"; $("tks-total").hidden = (st.tksView || "both") !== "total";
      more.hidden = true; return;
    }
    $("tks-label").textContent = fmtYmd(d.date);
    const chg = {};
    const ch = d.change;
    if (ch && ch.rows) for (const r of ch.rows) chg[r.broker] = r;
    const rows = d.rows;
    const k = (lab, v, c = "") => `<div class="ks"><span class="k">${lab}</span><span class="v ${c}">${v}</span></div>`;
    const top5 = rows.slice(0, 5).reduce((a, r) => a + (r.pct || 0), 0);
    sum.innerHTML = k("TOPLAM LOT", fShort(d.total_lot)) + k("KURUM", fN(rows.length)) + k("İLK 5 PAY", "%" + nf(1).format(top5));
    const show = st.tksExpanded ? rows : rows.slice(0, 10);
    const mx = Math.max(...rows.map((r) => r.pct || 0), 1);
    let h = "", i = 0;
    for (const r of show) {
      i++;
      const c = chg[r.broker];
      const cl = c && isNum(c.change_lot) ? c.change_lot : null;
      h += `<tr class="bar-buy" style="--w:${(((r.pct || 0) / mx) * 100).toFixed(1)}%"><td class="no">${i}</td><td class="ic">${brIcon(r.broker)}</td>
        <td class="kn" title="${esc(brName(r.broker))}">${esc(brName(r.broker))}</td><td>${fN(r.lot)}</td><td class="dg">%${nf(2).format(r.pct || 0)}</td>
        <td class="${cls(cl)}">${cl == null ? "—" : (cl > 0 ? "+" : "") + fShort(cl)}</td></tr>`;
    }
    body.innerHTML = h;
    more.hidden = rows.length <= 10;
    more.textContent = st.tksExpanded ? "Daha Az Göster" : `Diğerlerini Göster (+${rows.length - 10})`;
    const PER_L = { d1: "GÜNLÜK", w1: "HAFTALIK", m1: "AYLIK" };
    $("tks-note").textContent = `Kaynak: İdealData MKK takas · ${fmtYmd(d.date)}${ch ? ` · ${PER_L[d.period] || ""} değişim: ${fmtYmd(ch.from)} → ${fmtYmd(ch.to)}` : " · karşılaştırma verisi yok"} · Alanlar = takası (saklamadaki lotu) artan kurumlar, Satanlar = azalan kurumlar`;
    renderTakasDual(d, ch);
  }
  // v1.22.0 TAKAS: ALANLAR / SATANLAR / TOPLAM (AKD düzeni)
  function renderTakasDual(d, ch) {
    const view = st.tksView || "both", per = st.tksPer || "w1";
    document.querySelectorAll("#tks-seg button").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
    document.querySelectorAll("#tks-per button").forEach((b) => b.classList.toggle("active", b.dataset.per === per));
    $("tks-dual").hidden = view !== "both"; $("tks-total").hidden = view !== "total";
    const cr = ((ch && ch.rows) || []).filter((r) => r.broker && r.broker !== "Fark-Toplam" && isNum(r.change_lot));
    const al = cr.filter((r) => r.change_lot > 0).sort((a, b) => b.change_lot - a.change_lot);
    const sat = cr.filter((r) => r.change_lot < 0).sort((a, b) => a.change_lot - b.change_lot);
    const one = (list, side, exp) => {
      if (!ch) return `<tr><td colspan="6" class="empty">Karşılaştırma için önceki takas verisi alınamadı</td></tr>`;
      if (!list.length) return `<tr><td colspan="6" class="empty">Bu dönemde ${side === "al" ? "takası artan" : "takası azalan"} kurum yok</td></tr>`;
      const mx = Math.max(...list.map((r) => Math.abs(r.change_lot)), 1);
      return (exp ? list : list.slice(0, 10)).map((r, i) => {
        const dp = isNum(r.pct) && isNum(r.prev_pct) ? r.pct - r.prev_pct : null;
        return `<tr class="${side === "al" ? "bar-buy" : "bar-sell"}" style="--w:${((Math.abs(r.change_lot) / mx) * 100).toFixed(1)}%"><td class="no">${i + 1}</td><td class="ic">${brIcon(r.broker)}</td>
          <td class="kn" title="${esc(brName(r.broker))}">${esc(brName(r.broker))}</td><td class="${side === "al" ? "pos" : "neg"} b">${side === "al" ? "+" : "−"}${fShort(Math.abs(r.change_lot))}</td>
          <td class="${cls(dp)}">${dp == null ? "—" : (dp > 0 ? "+" : "") + nf(2).format(dp)}</td><td>${fShort(r.lot)}</td></tr>`;
      }).join("");
    };
    const sa = al.reduce((a, r) => a + r.change_lot, 0), ss = sat.reduce((a, r) => a + r.change_lot, 0);
    $("tks-al-sum").textContent = ch ? `${al.length} kurum · +${fShort(sa)}` : "—";
    $("tks-sat-sum").textContent = ch ? `${sat.length} kurum · −${fShort(Math.abs(ss))}` : "—";
    $("tks-body-al").innerHTML = one(al, "al", st.tksExpAl); $("tks-body-sat").innerHTML = one(sat, "sat", st.tksExpSat);
    const ma = $("tks-more-al"), ms = $("tks-more-sat");
    ma.hidden = al.length <= 10; ma.textContent = st.tksExpAl ? "Daha Az Göster" : `Diğerlerini Göster (+${al.length - 10})`;
    ms.hidden = sat.length <= 10; ms.textContent = st.tksExpSat ? "Daha Az Göster" : `Diğerlerini Göster (+${sat.length - 10})`;
  }
  $("tks-seg").addEventListener("click", (e) => { const b = e.target.closest("[data-view]"); if (!b) return; st.tksView = b.dataset.view; LS.set("tksView", st.tksView); if (st.takas) renderTakas(); });
  $("tks-per").addEventListener("click", (e) => { const b = e.target.closest("[data-per]"); if (!b) return; st.tksPer = b.dataset.per; LS.set("tksPer", st.tksPer); document.querySelectorAll("#tks-per button").forEach((x) => x.classList.toggle("active", x === b)); loadTakas(); });
  $("tks-more-al").addEventListener("click", () => { st.tksExpAl = !st.tksExpAl; renderTakas(); });
  $("tks-more-sat").addEventListener("click", () => { st.tksExpSat = !st.tksExpSat; renderTakas(); });
  st.tksView = LS.get("tksView", "both"); st.tksPer = LS.get("tksPer", "w1");
  $("tks-refresh").addEventListener("click", loadTakas);
  $("tks-more").addEventListener("click", () => { st.tksExpanded = !st.tksExpanded; renderTakas(); });

  // ----------------------------------------------------------------- ÖZET
  let chart = null, cSeries = null, vSeries = null;
  const CHL = { bars: [], intraday: false, tf: "", pin: null };   // v1.26.2 OHLC lejantı
  function chIdx(p) {
    if (!p || !p.point || p.logical == null) return null;
    const i = Math.round(p.logical);
    return i >= 0 && i < CHL.bars.length ? i : null;
  }
  function chT(b) {
    const tf = CHL.tf;
    if (CHL.intraday) { const x = new Date(b.time * 1000); const z = (n) => String(n).padStart(2, "0"); return `${z(x.getUTCDate())}.${z(x.getUTCMonth() + 1)}.${x.getUTCFullYear()} ${z(x.getUTCHours())}:${z(x.getUTCMinutes())}`; }
    const [y, m, d] = String(b.time).split("-");
    if (tf === "1mo") return `${m}.${y} (ay)`;
    const wd = ["Paz", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"][new Date(Date.UTC(+y, +m - 1, +d)).getUTCDay()];
    return tf === "1w" ? `${d}.${m}.${y} haftası` : `${d}.${m}.${y} ${wd}`;
  }
  function chLeg(i) {
    const el = $("ohlc-leg"); if (!el) return;
    const B = CHL.bars;
    if (!B.length || i == null || i < 0 || i >= B.length) { el.innerHTML = ""; return; }
    const b = B[i], pv = i > 0 ? B[i - 1].close : null;
    const ch = isNum(pv) && pv ? (b.close / pv - 1) * 100 : null;
    const c = b.close >= b.open ? "pos" : "neg";
    el.innerHTML = `<span class="t">${esc(chT(b))}${CHL.pin === i ? " 📌" : i === B.length - 1 ? " · son" : ""}</span><span>A <b>${fP(b.open)}</b></span><span>Y <b>${fP(b.high)}</b></span><span>D <b>${fP(b.low)}</b></span><span>K <b class="${c}">${fP(b.close)}</b></span><span class="${cls(ch)}"><b>${isNum(ch) ? (ch > 0 ? "+" : ch < 0 ? "−" : "") + "%" + nf(2).format(Math.abs(ch)) : "—"}</b></span>${isNum(b.vol) && b.vol > 0 ? `<span>Hac. <b>${fShort(b.vol)}${CHL.intraday ? "" : " ₺"}</b></span>` : ""}`;
  }
  function chLogOn() { return LS.get("chLog", false) === true; }
  function ensureChart() {
    if (chart) return true;
    if (!window.LightweightCharts) return false;
    const box = $("chart-box");
    chart = LightweightCharts.createChart(box, {
      autoSize: true,
      layout: { background: { type: "solid", color: "#0a0c0e" }, textColor: "#8b929b", fontFamily: "Inter, sans-serif", fontSize: 11 },
      grid: { vertLines: { color: "rgba(255,255,255,0.04)" }, horzLines: { color: "rgba(255,255,255,0.04)" } },
      rightPriceScale: { borderColor: "#1f2328", autoScale: true, mode: chLogOn() ? 1 : 0 },
      timeScale: { borderColor: "#1f2328", timeVisible: true, secondsVisible: false },
      crosshair: { mode: 0 },
      handleScale: { axisPressedMouseMove: { time: true, price: false }, mouseWheel: true, pinch: true },   // v1.26.2 fiyat ekseni sürüklenemez (oto ölçek bozulup eksen eksiye kaymasın)
      localization: { locale: "tr-TR", priceFormatter: (p) => (p < 0 ? "" : nf(2).format(p)) },   // v1.26.2 negatif fiyat etiketi yok
    });
    cSeries = chart.addCandlestickSeries({ upColor: "#22c55e", downColor: "#ef4444", borderVisible: false, wickUpColor: "#22c55e", wickDownColor: "#ef4444",
      autoscaleInfoProvider: (orig) => { const r = orig(); if (r && r.priceRange && r.priceRange.minValue < 0) r.priceRange.minValue = 0; return r; } });   // v1.26.2 ölçek 0'ın altına inmez
    try {
      const lg = document.createElement("div"); lg.className = "ohlc-leg"; lg.id = "ohlc-leg"; box.appendChild(lg);
      const tl = document.createElement("div"); tl.className = "ch-tools"; tl.innerHTML = `<button type="button" data-chlog="1" class="${chLogOn() ? "on" : ""}" title="Logaritmik fiyat ölçeği">LOG</button><button type="button" data-chfit="1" title="Ölçeği ve görünümü sıfırla">⟲</button>`; box.appendChild(tl);
      tl.addEventListener("click", (e) => {
        e.stopPropagation();
        const lb = e.target.closest("[data-chlog]");
        if (lb) { const on = !chLogOn(); LS.set("chLog", on); lb.classList.toggle("on", on); chart.priceScale("right").applyOptions({ mode: on ? 1 : 0, autoScale: true }); return; }
        if (e.target.closest("[data-chfit]")) { chart.priceScale("right").applyOptions({ autoScale: true }); const n = CHL.bars.length; chart.timeScale().fitContent(); if (n > 150) chart.timeScale().setVisibleLogicalRange({ from: n - 150, to: n + 2 }); CHL.pin = null; chLeg(n - 1); }
      });
      // fare (hover) cihazında lejant imleci izler, tıklama sabitlemez; dokunmatikte dokunulan mum sabitlenir (tekrar dokun / boşluğa dokun → son mum)
      let ptr = (window.matchMedia && matchMedia("(hover: hover) and (pointer: fine)").matches) ? "mouse" : "touch";
      box.addEventListener("touchstart", () => { ptr = "touch"; }, { passive: true, capture: true });
      box.addEventListener("pointerdown", (e) => { if (e.pointerType) ptr = e.pointerType === "mouse" ? "mouse" : "touch"; }, { passive: true, capture: true });
      box.addEventListener("mousemove", (e) => { if (!e.sourceCapabilities || !e.sourceCapabilities.firesTouchEvents) { if (ptr !== "mouse" && Date.now() - (box._tt || 0) > 800) ptr = "mouse"; } }, { passive: true });
      box.addEventListener("touchend", () => { box._tt = Date.now(); }, { passive: true, capture: true });
      const isTouch = () => ptr !== "mouse";
      chart.subscribeCrosshairMove((p) => { CHL.hov = !!(p && p.point && p.logical != null); if (CHL.pin != null && isTouch()) return; if (CHL.pin != null && !isTouch()) CHL.pin = null; const i = chIdx(p); chLeg(i == null ? CHL.bars.length - 1 : i); });
      chart.subscribeClick((p) => { if (!isTouch()) return; const i = chIdx(p); if (i == null || CHL.pin === i) { const k = CHL.pin; CHL.pin = null; chLeg(i == null ? CHL.bars.length - 1 : k); return; } CHL.pin = i; chLeg(i); });
    } catch (e) { try { console.warn("ohlc legend", e); } catch (x) {} }
    vSeries = chart.addHistogramSeries({ priceFormat: { type: "volume" }, priceScaleId: "vol", lastValueVisible: false, priceLineVisible: false });
    chart.priceScale("vol").applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
    return true;
  }
  function chLastLab(t, intraday) {   // v1.37.0 "son veri: tarih"
    if (!intraday) return String(t).split("-").reverse().join(".");
    const d = new Date((+t) * 1000); const p = (x) => String(x).padStart(2, "0");
    return `${p(d.getUTCDate())}.${p(d.getUTCMonth() + 1)}.${d.getUTCFullYear()} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`;
  }
  async function loadChart() {
    const gen = st.gen, sym = st.sym, tf = st.tf;
    document.querySelectorAll("#tf-bar button").forEach((b) => b.classList.toggle("active", b.dataset.tf === tf));
    const msg = $("chart-msg"); msg.hidden = false; msg.textContent = "Grafik yükleniyor…";
    // v1.37.0: kütüphane yoksa sonsuz "yükleniyor" yerine ~15 sn bekle → hata + Tekrar dene
    let okc = false; try { okc = ensureChart(); } catch (e) { loadChart._libErr = String(e.message || e); }
    if (!okc) {
      loadChart._w = (loadChart._w || 0) + 1;
      if (loadChart._w <= 25 && !loadChart._libErr) { setTimeout(() => { if (gen === st.gen && st.tab === "ozet") loadChart(); }, 600); return; }
      loadChart._w = 0;
      msg.innerHTML = `Grafik kütüphanesi yüklenemedi${loadChart._libErr ? " (" + esc(loadChart._libErr) + ")" : " (ağ engeli olabilir)"} · <button type="button" class="obt-pre" data-chretry="1">Tekrar dene</button>`;
      loadChart._libErr = null; return;
    }
    loadChart._w = 0;
    try {
      const pxP = clPxFetch(sym, tf);   // v1.30.2 bugünün canlı fiyat yolu (İdealData, saniye saniye) — geçmiş ile paralel
      const d = await api(`/api/stocks/${sym}?period=${tf}&include_rvol_tf=false&include_notes=false&include_high_breaks=false&include_vwap=false`, { timeout: 45000 });
      if (gen !== st.gen || tf !== st.tf) return;
      const intraday = !["1d", "1w", "1mo"].includes(tf);
      const c = [], v = [];
      for (const b of d.history || []) {
        if (![b.open, b.high, b.low, b.close].every(isNum)) continue;
        const t = intraday ? (b.time || 0) + 3 * 3600 : (b.date || b.time_ist || "").slice(0, 10);
        if (!t) continue;
        if (!(b.close > 0) || !(b.open > 0)) continue;   // v1.26.2 bozuk (≤0) bar
        c.push({ time: t, open: b.open, high: Math.max(b.high, b.open, b.close), low: Math.max(0, Math.min(b.low, b.open, b.close)), close: b.close });
        v.push({ time: t, value: b.volume || 0, color: b.close >= b.open ? "rgba(34,197,94,.45)" : "rgba(239,68,68,.45)" });
      }
      const pxD = await pxP; if (gen !== st.gen || tf !== st.tf) return;
      const nLive = clMerge(c, v, pxD, tf, sym);   // v1.30.2 İş Yatırım gün içi verisi ~15+ dk gecikmeli → bugünün mumları İdealData canlı işlemlerinden
      chart.applyOptions({ timeScale: { timeVisible: intraday } });
      cSeries.setData(c); vSeries.setData(v.some((x) => x.value > 0) ? v : []);
      CHL.bars = c.map((x, i) => Object.assign({ vol: v[i] ? v[i].value : null }, x)); CHL.intraday = intraday; CHL.tf = tf; CHL.pin = null; chLeg(c.length - 1);   // v1.26.2
      try { fmMarkers(); } catch (e) {} try { obOv(); } catch (e) {}   // v1.27.0 / v1.28.0 OB formasyon işaretleri (Özet › FORMASYONLAR › Grafikte işaretle)
      try { chart.priceScale("right").applyOptions({ autoScale: true }); } catch (x) {}
      if (c.length) { chart.timeScale().fitContent(); if (c.length > 150) chart.timeScale().setVisibleLogicalRange({ from: c.length - 150, to: c.length + 2 }); }
      msg.hidden = !!c.length; if (!c.length) msg.textContent = "Bu zaman dilimi için veri yok";
      let wide = false; if (c.length) { let lo = Infinity, hi = 0; for (const x of c) { if (x.low > 0 && x.low < lo) lo = x.low; if (x.high > hi) hi = x.high; } wide = lo > 0 && hi / lo >= 8; }
      $("chart-src").textContent = `Kaynak: ${d.source_label || "İş Yatırım"}${nLive ? ` + bugün İdealData canlı (${nLive} mum, işlem işlem güncellenir)` : CLV.q ? " + bugün canlı fiyat (İdealData)" : ""} · ${c.length} mum${c.length ? " · son veri: " + chLastLab(c[c.length - 1].time, intraday) : ""}${intraday ? "" : " · günlük açılış = önceki kapanış (kaynak öyle veriyor)"}${wide && !chLogOn() ? " · fiyat aralığı çok geniş — LOG ölçek önerilir" : ""} · mum'a dokun → üstte A/Y/D/K`;
    } catch (e) {
      if (gen === st.gen) { msg.hidden = false; msg.innerHTML = "Grafik alınamadı (" + esc(e.message || e) + ") · <button type=\"button\" class=\"obt-pre\" data-chretry=\"1\">Tekrar dene</button>"; }
    }
  }
  document.addEventListener("click", (e) => { if (e.target && e.target.closest && e.target.closest("[data-chretry]")) { if (!window.LightweightCharts) { const s = document.createElement("script"); s.src = "/static/vendor/lightweight-charts-4.2.0.js?r=" + Date.now(); s.onload = () => loadChart(); document.head.appendChild(s); } else loadChart(); } });   // v1.37.0
  document.querySelectorAll("#tf-bar button").forEach((b) => b.addEventListener("click", () => { st.tf = b.dataset.tf; LS.set("tf", st.tf); loadChart(); }));

  // ------------------------------------------------ v1.30.2 CANLI GRAFİK (son mum canlı fiyatı izler)
  // Kök neden: grafik yalnız İş Yatırım geçmişinden bir kez yükleniyordu (gün içi seri ~15+ dk gecikmeli, seans başında önceki günün 18:04
  // mumunda kalıyor) ve sonra HİÇ güncellenmiyordu. Şimdi: bugünün mumları İdealData'nın saniye saniye fiyat yolundan kurulur (/api/k/baski/detail
  // px), ardından her 1 sn canlı işlemlerle (/api/ideal/{s}/trades) oluşan mum güncellenir, periyot sınırında yeni mum eklenir.
  // 1G/1H: bugünün mumu canlı kotasyondan (fiyat / gün yüksek / gün düşük) güncellenir.
  const CL_SZ = { "1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400 };
  const CLV = { ok: false, q: false, sym: null, tf: null, gen: -1, d0: 0, lastN: -1, ts: 0, busy: false, err: 0 };
  const clPad = (n) => String(n).padStart(2, "0");
  function clIst() { const n = new Date(Date.now() + 3 * 3600e3); return { y: n.getUTCFullYear(), m: n.getUTCMonth() + 1, d: n.getUTCDate(), dow: n.getUTCDay(), sod: n.getUTCHours() * 3600 + n.getUTCMinutes() * 60 + n.getUTCSeconds() }; }
  function clLab(sod, tf) {   // İş Yatırım etiketleme ile uyumlu: 1dk/5dk/15dk/1sa = mum başlangıcı (1sa açılış seansı 10:00 mumuna), 4sa = mum sonu (12/16/20)
    const z = CL_SZ[tf];
    if (tf === "4h") return (Math.floor(sod / z) + 1) * z;
    if (tf === "1h" && sod < 36000) sod = 36000;
    return Math.floor(sod / z) * z;
  }
  const clSod = (hms) => { const a = String(hms || "").split(":"); return a.length >= 2 ? (+a[0]) * 3600 + (+a[1]) * 60 + (+(a[2] || 0)) : null; };
  function clPush(B, t, p) {
    const L = B[B.length - 1];
    if (L && L.time === t) { if (p > L.high) L.high = p; if (p < L.low) L.low = p; L.close = p; return L; }
    if (!L || t > L.time) { const nb = { time: t, open: p, high: p, low: p, close: p }; B.push(nb); return nb; }
    return null;   // eski periyot (sıra dışı) — yok say
  }
  function clPxFetch(sym, tf) {
    const n = clIst();
    if (!CL_SZ[tf] || n.dow === 0 || n.dow === 6 || n.sod < 9 * 3600 + 50 * 60 || n.sod > 20 * 3600) return Promise.resolve(null);
    return api(`/api/k/baski/detail?sym=${encodeURIComponent(sym)}&fid=k_poc`, { timeout: 15000 }).catch(() => null);
  }
  function clMerge(c, v, px, tf, sym) {
    Object.assign(CLV, { ok: false, q: false, sym, tf, gen: st.gen, lastN: -1, ts: Date.now(), err: 0 });
    if (!CL_SZ[tf]) { CLV.q = ["1d", "1w"].includes(tf); if (CLV.q) clQuoteBars(c, v); return 0; }
    const n = clIst(), today = `${n.y}${clPad(n.m)}${clPad(n.d)}`;
    CLV.d0 = Date.UTC(n.y, n.m - 1, n.d) / 1000;
    if (!px || px.day !== today || !Array.isArray(px.px) || !px.px.length) return 0;
    const B = [];
    for (const r of px.px) { const p = +r[1]; if (p > 0 && isNum(r[0])) clPush(B, CLV.d0 + clLab(r[0], tf), p); }
    if (!B.length) return 0;
    const t0 = B[0].time; let k = c.length; while (k > 0 && c[k - 1].time >= t0) k--;   // gecikmeli İş Yatırım mumlarını (bugünün canlı kısmı) çıkar
    c.splice(k); v.splice(k);
    for (const b of B) { c.push(b); v.push({ time: b.time, value: 0, color: "rgba(0,0,0,0)" }); }
    CLV.ok = true; return B.length;
  }
  // 1G / 1H: bugünün mumu canlı kotasyondan (seriyle aynı kural: günlük açılış = önceki kapanış)
  function clQuoteBar(B, q) {
    const n = clIst(), p = q && +q.price;
    if (!(p > 0) || !B.length || n.dow === 0 || n.dow === 6 || n.sod < 9 * 3600 + 55 * 60 || !(+q.open > 0)) return null;
    let lab;
    if (CLV.tf === "1d") lab = `${n.y}-${clPad(n.m)}-${clPad(n.d)}`;
    else { const f = new Date(Date.UTC(n.y, n.m - 1, n.d + (5 - n.dow))); lab = `${f.getUTCFullYear()}-${clPad(f.getUTCMonth() + 1)}-${clPad(f.getUTCDate())}`; }   // haftalık mum etiketi = o haftanın cuması
    const L = B[B.length - 1], hi = +q.high > 0 ? +q.high : p, lo = +q.low > 0 ? +q.low : p;
    if (L.time === lab) { L.high = Math.max(L.high, hi, p); L.low = Math.min(L.low, lo, p); L.close = p; return L; }
    if (String(L.time) < lab) { const o = L.close; const nb = { time: lab, open: o, high: Math.max(o, hi, p), low: Math.min(o, lo, p), close: p }; B.push(nb); return nb; }
    return null;
  }
  function clQuoteBars(c, v) { const q = st.ideal && st.ideal.quote; const nb = clQuoteBar(c, q); if (nb && v.length < c.length) v.push({ time: nb.time, value: 0, color: "rgba(0,0,0,0)" }); }
  function clApply(bar, isNew) {
    try { cSeries.update({ time: bar.time, open: bar.open, high: bar.high, low: bar.low, close: bar.close }); } catch (e) { return; }
    const B = CHL.bars;
    if (isNew) B.push(Object.assign({ vol: null }, bar));
    else { const L = B[B.length - 1]; if (L && L.time === bar.time) Object.assign(L, bar); }
    if (CHL.pin == null && !CHL.hov) chLeg(B.length - 1);
  }
  async function clTick() {
    if (CLV.busy || document.hidden || st.view !== "stock" || st.tab !== "ozet" || !cSeries) return;
    if (CLV.gen !== st.gen || CLV.sym !== st.sym || CLV.tf !== st.tf) return;
    const n = clIst();
    if (CLV.q) {   // 1G / 1H — kotasyon her 3 sn'de geliyor (pollIdeal)
      const B = CHL.bars, L0 = B[B.length - 1], len = B.length;
      const W = B.map((x) => x);   // clQuoteBar CHL.bars üzerinde çalışır
      const nb = clQuoteBar(W, st.ideal && st.ideal.quote);
      if (nb) { if (W.length > len) { W.pop(); clApply(nb, true); } else clApply(nb, false); }
      return;
    }
    if (!CLV.ok || n.dow === 0 || n.dow === 6 || n.sod < 9 * 3600 + 50 * 60 || n.sod > 18 * 3600 + 20 * 60) return;
    if (Date.now() - CLV.ts > 120000) { CLV.ok = false; loadChart(); return; }   // uzun ara (arka plan / başka sekme) → 2 dk penceresi yetmez, yeniden kur
    CLV.busy = true;
    const gen = st.gen, sym = st.sym, tf = st.tf;
    try {
      const r = await api(`/api/ideal/${encodeURIComponent(sym)}/trades?minutes=2&limit=1000`, { timeout: 6000 });
      if (gen !== st.gen || sym !== st.sym || tf !== st.tf || !CLV.ok) return;
      const rows = (r && r.rows) || [];
      for (let i = rows.length - 1; i >= 0; i--) {   // en yeni → en eski geldi; eskiden yeniye uygula
        const x = rows[i];
        if (!(x.n > CLV.lastN) || !(+x.price > 0)) continue;
        const sod = clSod(x.time); if (sod == null) continue;
        const B = CHL.bars, len = B.length, W = B.map((y) => y);
        const t = CLV.d0 + clLab(sod, tf), L = W[W.length - 1];
        if (L && t < L.time) { CLV.lastN = x.n; continue; }
        const nb = L && L.time === t ? Object.assign({}, L) : null;
        if (nb) { const p = +x.price; nb.high = Math.max(nb.high, p); nb.low = Math.min(nb.low, p); nb.close = p; clApply(nb, false); }
        else { const p = +x.price; clApply({ time: t, open: p, high: p, low: p, close: p }, true); }
        CLV.lastN = x.n;
        void len;
      }
      CLV.ts = Date.now(); CLV.err = 0;
    } catch (e) { CLV.err++; }
    finally { CLV.busy = false; }
  }
  setInterval(() => { try { clTick(); } catch (e) {} }, 1000);

  async function loadExtras() {
    const gen = st.gen, sym = st.sym;
    try {
      const d = await api(`/api/stocks/${sym}/panel-extras`, { timeout: 45000 });
      if (gen !== st.gen) return;
      st.extras = d; st.extrasTs = Date.now(); renderOzet();
    } catch (e) {}
    loadStockIx(sym, gen);
  }
  // v1.19.0: hissenin yer aldığı endeksler + puan etkisi
  async function loadStockIx(sym, gen) {
    try {
      const d = await api(`/api/index-impact/stock/${encodeURIComponent(sym)}`, { timeout: 15000 });
      if (gen !== st.gen) return;
      st.stockIx = d; renderStockIx();
    } catch (e) { if (gen === st.gen) $("ozet-ix").innerHTML = `<div class="empty">Endeks verisi alınamadı</div>`; }
  }
  function renderStockIx() {
    const d = st.stockIx; if (!d) return;
    const rows = (d.indices || []);
    if (!rows.length) { $("ozet-ix").innerHTML = `<div class="empty">${esc(d.symbol)} hiçbir BIST endeksinde yer almıyor (veya kapsam yükleniyor)</div>`; return; }
    const PRI = ["XU100", "XU030", "XU050", "XU500", "XUTUM", "XTUMY", "XYUZO", "XELOT", "XYLDZ", "XBANA", "XLBNK", "X10XB"];
    const pr = (c) => { const i = PRI.indexOf(c); return i < 0 ? 99 : i; };
    const main = rows.filter((r) => r.group === "Gösterge").sort((a, b) => pr(a.code) - pr(b.code)).slice(0, 6);
    const mainSet = new Set(main.map((r) => r.code));
    const rest = rows.filter((r) => !mainSet.has(r.code));
    const pill = (r) => `<button type="button" class="ix-chip" data-ix="${esc(r.code)}" title="${esc(r.name)}"><b>${esc(r.code)}</b>
      <span>${r.src === "tahmini" ? "~" : ""}%${fN(r.w, 2)}</span>${isNum(r.pts) ? `<em class="${cls(r.pts)}">${r.pts > 0 ? "+" : ""}${fN(r.pts, 2)} p</em>` : ""}</button>`;
    $("ozet-ix").innerHTML = `<div class="ix-chips">${main.map(pill).join("")}</div>` +
      (rest.length ? `<div class="ix-chips sub">${rest.map(pill).join("")}</div>` : "") +
      `<div class="src-note">${rows.length} endeks · ağırlık % · bugünkü puan etkisi · "~" = tahmini ağırlık</div>`;
  }
  $("ozet-ix").addEventListener("click", (e) => { const b = e.target.closest("[data-ix]"); if (b) { ix.code = b.dataset.ix; LS.set("ix_code", ix.code); ix.data = null; go("endeks"); } });
  $("ozet-ix-all").addEventListener("click", () => go("endeks"));
  setInterval(() => { if (!document.hidden && st.tab === "ozet" && Date.now() - (st.extrasTs || 0) > 20000) loadExtras(); }, 5000);
  function renderOzet() {
    const d = st.ideal || {}, q = d.quote || {}, x = st.extras || {}, xs = x.stock || {};
    const fpS = x.footprint || {};
    const kv = (k, v, c = "") => `<div class="kv"><span class="k">${k}</span><span class="v ${c}">${v}</span></div>`;
    const buy = x.buy_vol, sell = x.sell_vol, net = x.net_vol;
    $("ozet-grid").innerHTML =
      kv("Son fiyat", fP(q.price ?? xs.price)) + kv("Değişim", fPct(q.change_pct ?? xs.change_pct), cls(q.change_pct ?? xs.change_pct)) +
      kv("Açılış", fP(q.open ?? xs.day_open)) + kv("Önceki kapanış", fP(q.previous_close ?? xs.previous_close)) +
      kv("Yüksek", fP(q.high ?? xs.day_high)) + kv("Düşük", fP(q.low ?? xs.day_low)) +
      kv("Hacim (lot)", fShort(q.volume ?? xs.volume)) + kv("TL hacim", fShort(q.turnover ?? xs.live_turnover, "₺")) +
      kv("VWAP (AOF)", fP(q.vwap ?? xs.live_vwap)) + kv("Tavan / Taban", `${fP(q.ceiling)} / ${fP(q.floor)}`) +
      kv("RVOL (önc. gün)", isNum(xs.rvol) ? nf(2).format(xs.rvol) + "×" : "—") + kv("RVOL (10 gün)", isNum(xs.rvol10) ? nf(2).format(xs.rvol10) + "×" : "—") +
      kv("Alış hacmi", fShort(buy), "pos") + kv("Satış hacmi", fShort(sell), "neg") +
      kv("Net hacim", fShort(net), cls(net)) + kv("Alış hakimiyeti", isNum(x.buy_dominance_pct) ? "%" + nf(1).format(x.buy_dominance_pct) : "—");
    $("ozet-src").textContent = (x.fp_source_label ? "Alış/satış: " + x.fp_source_label : "İdealData canlı") + (fpS.poc ? " · POC " + fP(fpS.poc) : "");
  }

  // ------------------------------------------------------------ SİNYALLER
  async function loadSignals(forAi) {
    const gen = st.gen, sym = st.sym;
    try {
      const [sig, plan, notes] = await Promise.all([
        api(`/api/stocks/${sym}/signal`, { timeout: 45000 }).catch(() => null),
        api(`/api/stocks/${sym}/trade-plan`, { timeout: 45000 }).catch(() => null),
        forAi ? api(`/api/stocks/${sym}/notes`, { timeout: 45000 }).catch(() => null) : Promise.resolve(null),
      ]);
      if (gen !== st.gen) return;
      st.sig = sig; st.plan = plan; if (notes) st.notesApi = notes;
      renderSignals(); if (forAi || st.tab === "ai") renderAi();
    } catch (e) {}
  }
  setInterval(() => { if (!document.hidden && (st.tab === "sinyal" || st.tab === "ai") && Date.now() - (loadSignals._ts || 0) > 30000) { loadSignals._ts = Date.now(); loadSignals(st.tab === "ai"); } }, 5000);
  function renderSignals() {
    const s = st.sig, p = st.plan;
    const sc = $("sig-card"), pc = $("plan-card");
    if (!s) sc.innerHTML = `<div class="empty">Sinyal hesaplanamadı</div>`;
    else {
      const v = s.verdict || "TUT";
      const chips = [];
      if (isNum(s.buy_dominance_pct)) chips.push(`<span class="chip ${s.buy_dominance_pct >= 50 ? "pos" : "neg"}">Alış hakimiyeti %${nf(1).format(s.buy_dominance_pct)}</span>`);
      if (isNum(s.rvol)) chips.push(`<span class="chip">RVOL ${nf(2).format(s.rvol)}×</span>`);
      if (isNum(s.rvol10)) chips.push(`<span class="chip">RVOL10 ${nf(2).format(s.rvol10)}×</span>`);
      const vw = p && p.inputs && p.inputs.vwap;
      const last = (st.ideal && st.ideal.quote && st.ideal.quote.price) || (p && p.inputs && p.inputs.last);
      if (isNum(vw)) chips.push(`<span class="chip ${isNum(last) && last >= vw ? "pos" : "neg"}">VWAP ${fP(vw)}${isNum(last) ? " · " + (last >= vw ? "üstü" : "altı") : ""}</span>`);
      if (s.footprint && s.footprint.poc) chips.push(`<span class="chip">POC ${fP(s.footprint.poc)}</span>`);
      if (isNum(s.change_pct)) chips.push(`<span class="chip ${cls(s.change_pct)}">Gün ${fPct(s.change_pct)}</span>`);
      sc.innerHTML = `<div class="card-h"><span>SİNYAL</span><span class="muted sm">${esc(s.strength || "")}</span></div>
        <div class="sig-top"><span class="verdict ${esc(v)}">${esc(v)}</span><div class="sig-sub">${(s.reasons || []).map(esc).join("<br>")}</div></div>
        <div class="chips">${chips.join("")}</div>
        <ul class="bul">${(s.bullets || []).slice(0, 6).map((b) => `<li>${esc(b)}</li>`).join("")}</ul>`;
    }
    if (!p) pc.innerHTML = `<div class="empty">İşlem planı hesaplanamadı</div>`;
    else {
      const dir = p.direction || "WAIT";
      const dirTr = { LONG: "LONG · ALIŞ", SHORT: "SHORT · SATIŞ", WAIT: "BEKLE" }[dir] || dir;
      const k = (lab, v, c = "") => `<div class="ks"><span class="k">${lab}</span><span class="v ${c}">${v}</span></div>`;
      const inp = p.inputs || {};
      pc.innerHTML = `<div class="card-h"><span>İŞLEM PLANI</span><span class="plan-dir ${esc(dir)}">${esc(dirTr)}</span></div>
        <div class="plan-grid">${k("GİRİŞ", fP(p.entry))}${k("STOP", fP(p.stop), "neg")}${k("TP1", fP(p.tp1), "pos")}${k("TP2", fP(p.tp2), "pos")}
        ${k("R:R (TP1)", isNum(p.rr_tp1) ? nf(2).format(p.rr_tp1) : "—")}${k("RİSK", isNum(p.risk_pct) ? "%" + nf(2).format(p.risk_pct) : "—")}
        ${k("DESTEK", fP(inp.support))}${k("DİRENÇ", fP(inp.resistance))}${k("VAH / VAL", `${fP(inp.vah)} / ${fP(inp.val)}`)}${k("AORT", fP(inp.aort))}</div>
        <ul class="bul">${(p.rationale || []).map((r) => `<li>${esc(r)}</li>`).join("")}</ul>`;
    }
  }

  // ------------------------------------------------------------------- AI
  function renderAi() {
    const el = $("ai-card");
    const s = st.sig, p = st.plan, n = st.notesApi, d = st.ideal || {};
    if (!s && !d.quote) { el.innerHTML = `<div class="empty">Yorum için veri bekleniyor…</div>`; return; }
    const q = d.quote || {}, dp = d.depth || {}, mf = d.money_flow || {}, br = d.brokers || {};
    const sec = (t, txt) => (txt ? `<div class="ai-sec"><h4>${t}</h4><p>${txt}</p></div>` : "");
    const v = (s && s.verdict) || "TUT";
    const genel = [];
    if (isNum(q.change_pct)) genel.push(`${st.sym} gün içinde ${fPct(q.change_pct)} ${q.change_pct > 0 ? "artıda" : q.change_pct < 0 ? "ekside" : "yatay"} işlem görüyor (son ${fP(q.price)} ₺).`);
    if (isNum(q.high) && isNum(q.low) && q.high > q.low && isNum(q.price)) {
      const pos = ((q.price - q.low) / (q.high - q.low)) * 100;
      genel.push(`Fiyat gün aralığının %${nf(0).format(pos)} seviyesinde (${fP(q.low)} – ${fP(q.high)}).`);
    }
    if (isNum(q.vwap) && isNum(q.price)) genel.push(`AOF/VWAP ${fP(q.vwap)}; fiyat ${q.price >= q.vwap ? "üzerinde — alıcılar ortalama maliyetin üstünde" : "altında — gün içi ortalamanın gerisinde"}.`);
    const akis = [];
    if (isNum(mf.net_tl)) akis.push(`Kademe analizine göre para girişi ${fShort(mf.inflow_tl, "₺")}, çıkışı ${fShort(mf.outflow_tl, "₺")}; net ${fShort(mf.net_tl, "₺")} (${mf.net_tl >= 0 ? "pozitif" : "negatif"}).`);
    if (isNum(mf.buy_dominance_pct)) akis.push(`Aktif alış payı %${nf(1).format(mf.buy_dominance_pct)}.`);
    if (s && isNum(s.rvol)) akis.push(`Hacim önceki seansa göre ${nf(2).format(s.rvol)}× (${s.rvol >= 1.5 ? "yüksek ilgi" : s.rvol < 0.6 ? "zayıf ilgi" : "normal"}).`);
    const derin = [];
    if (isNum(dp.pressure_pct)) derin.push(`İlk 25 kademede alış baskısı %${nf(0).format(dp.pressure_pct)} — ${dp.pressure_pct >= 55 ? "alıcı tarafı daha kalabalık" : dp.pressure_pct <= 45 ? "satıcı tarafı ağır basıyor" : "denge"}.`);
    if (isNum(dp.best_bid) && isNum(dp.best_ask) && dp.best_bid > 0) derin.push(`En iyi alış ${fP(dp.best_bid)}, en iyi satış ${fP(dp.best_ask)}.`);
    const kur = [];
    const b0 = (br.buyers || [])[0], s0 = (br.sellers || [])[0];
    if (b0) kur.push(`En çok net alan ${brName(b0.broker)} (${fN(b0.net_lot)} lot${isNum(b0.cost) ? ", maliyet " + fP(b0.cost) : ""}).`);
    if (s0) kur.push(`En çok net satan ${brName(s0.broker)} (${fN(Math.abs(s0.net_lot))} lot${isNum(s0.cost) ? ", maliyet " + fP(s0.cost) : ""}).`);
    const sev = [];
    if (p && p.inputs) {
      const i = p.inputs;
      if (isNum(i.support) || isNum(i.resistance)) sev.push(`Yakın destek ${fP(i.support)}, direnç ${fP(i.resistance)}; POC ${fP(i.poc)}.`);
      if (p.direction === "LONG" || p.direction === "SHORT") sev.push(`Model planı ${p.direction}: giriş ${fP(p.entry)}, stop ${fP(p.stop)}, TP1 ${fP(p.tp1)}.`);
      else sev.push("Model şu an net bir giriş yapısı görmüyor (BEKLE).");
    }
    const notes = ((n && n.notes) || []).slice(0, 5);
    el.innerHTML = `<div class="ai-h">Otomatik yorum · <span class="verdict ${esc(v)}" style="font-size:13px;padding:3px 8px">${esc(v)}</span></div>
      ${sec("GENEL GÖRÜNÜM", genel.join(" "))}${sec("HACİM & PARA AKIŞI", akis.join(" "))}${sec("DERİNLİK", derin.join(" "))}
      ${sec("KURUMLAR (AKD)", kur.join(" "))}${sec("SEVİYELER", sev.join(" "))}
      ${notes.length ? `<div class="ai-sec"><h4>NOTLAR</h4><ul class="bul">${notes.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>` : ""}`;
  }

  // ------------------------------------------------------------ favorites
  function renderFav() { $("btn-fav").classList.toggle("on", st.favs.includes(st.sym)); }
  $("btn-fav").addEventListener("click", () => {
    if (st.favs.includes(st.sym)) { st.favs = st.favs.filter((s) => s !== st.sym); toast(`${st.sym} favorilerden çıkarıldı`); }
    else { st.favs = [st.sym, ...st.favs]; toast(`${st.sym} favorilere eklendi ★`); }
    LS.set("favs", st.favs); renderFav(); try { saveCfg({ favs: st.favs }); } catch (e) {}
  });

  // -------------------------------------------------------------- search
  let searchList = "all";
  async function openSearch(list) {
    searchList = list || "all";
    document.querySelectorAll("#search-seg button").forEach((b) => b.classList.toggle("active", b.dataset.list === searchList));
    $("search-sheet").hidden = false;
    $("search-input").value = "";
    renderSearch();
    if (searchList === "all") setTimeout(() => $("search-input").focus(), 50);
    await loadList(); renderSearch();
  }
  function closeSheets() { ["search-sheet", "menu", "dlg", "ix-sheet", "rd-sort-sheet", "rd-peer-sheet"].forEach((i) => ($(i).hidden = true)); }
  function renderSearch() {
    const qv = fold($("search-input").value.trim());
    const by = new Map(st.list.map((x) => [x.s, x]));
    let items;
    if (searchList === "fav") items = st.favs.map((s) => by.get(s) || { s });
    else if (searchList === "recent") items = st.recent.map((s) => by.get(s) || { s });
    else items = st.list;
    if (qv) {
      items = items.filter((x) => fold(x.s).includes(qv) || fold(x.n || "").includes(qv));
      items.sort((a, b) => (fold(a.s).startsWith(qv) ? 0 : 1) - (fold(b.s).startsWith(qv) ? 0 : 1) || (b.t || 0) - (a.t || 0));
    } else if (searchList === "all") items = [...items].sort((a, b) => (b.t || 0) - (a.t || 0));
    $("search-meta").textContent = searchList === "all" ? `${st.list.length} hisse · ${items.length} sonuç` : `${items.length} hisse`;
    const ul = $("search-list");
    if (!items.length) { ul.innerHTML = `<li class="empty" style="justify-content:center">${searchList === "fav" ? "Favori yok — ☆ ile ekleyin" : st.list.length ? "Sonuç yok" : "Liste yükleniyor…"}</li>`; return; }
    ul.innerHTML = items.slice(0, 120).map((x) => `<li data-sym="${esc(x.s)}"><span class="sl-logo" data-logo="${esc(x.s)}" style="background:hsl(${hue(x.s)} 40% 22%)">${esc(x.s.slice(0, 2))}</span>
      <div class="sl-mid"><div class="sl-sym">${esc(x.s)}${st.favs.includes(x.s) ? ' <span class="sl-star">★</span>' : ""}</div><div class="sl-name">${esc(x.n || "")}</div></div>
      <div class="sl-r"><div class="sl-p">${fP(x.p)}</div><div class="sl-c ${cls(x.c)}">${fPct(x.c)}</div></div></li>`).join("");
    lazyLogos(ul);
  }
  function lazyLogos(root) {
    const els = root.querySelectorAll("[data-logo]");
    const io = "IntersectionObserver" in window ? new IntersectionObserver((ents) => {
      for (const e of ents) if (e.isIntersecting) { load(e.target); io.unobserve(e.target); }
    }, { root: root }) : null;
    function load(el) {
      const s = el.dataset.logo; const img = new Image();
      img.onload = () => { el.style.background = `#fff url(/api/logo/${s}) center/80% no-repeat`; el.textContent = ""; };
      img.src = `/api/logo/${s}`;
    }
    els.forEach((el) => (io ? io.observe(el) : load(el)));
  }
  $("search-input").addEventListener("input", renderSearch);
  $("search-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { const li = $("search-list").querySelector("li[data-sym]"); if (li) { closeSheets(); selectSymbol(li.dataset.sym); if (st.view !== "stock") go("stock"); } }
  });
  $("search-list").addEventListener("click", (e) => { const li = e.target.closest("li[data-sym]"); if (li) { closeSheets(); selectSymbol(li.dataset.sym); if (st.view !== "stock") go("stock"); } });
  document.querySelectorAll("#search-seg button").forEach((b) => b.addEventListener("click", () => { searchList = b.dataset.list; document.querySelectorAll("#search-seg button").forEach((x) => x.classList.toggle("active", x === b)); renderSearch(); }));
  document.querySelectorAll("[data-close]").forEach((el) => el.addEventListener("click", closeSheets));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") { closeSheets(); if (st.kfOpen) kfClose(); } });
  $("btn-symbol").addEventListener("click", () => openSearch("all"));
  $("btn-back2").addEventListener("click", () => openSearch("all"));
  $("btn-chevron").addEventListener("click", () => openSearch(st.favs.length ? "fav" : "recent"));
  $("btn-geri").addEventListener("click", () => {
    if (st.kfOpen) { kfClose(); return; }
    if (st.view !== "stock" || (st.fromScreen && viewStack.length)) { st.fromScreen = false; goBack(); return; }
    const prev = st.back.pop();
    if (prev) selectSymbol(prev, { noBack: true }); else openSearch("all");
  });

  // ---------------------------------------------------------------- menu
  $("btn-menu").addEventListener("click", () => ($("menu").hidden = false));
  document.querySelectorAll("#menu [data-act]").forEach((b) => b.addEventListener("click", async () => {
    closeSheets();
    const a = b.dataset.act;
    if (a.startsWith("go:")) { go(a.slice(3)); return; }
    if (a.startsWith("nf:")) { nfOpen(a.slice(3)); return; }
    if (a === "kesfet") { kfShow(); return; }
    if (a === "drset") { drSettings(); return; }   // v1.25.0
    if (a === "search") openSearch("all");
    else if (a === "fav") openSearch("fav");
    else if (a === "refresh") { selectSymbol(st.sym, { noBack: true }); loadList(true); toast("Yenilendi"); }
    else if (a === "notify") askNotify();
    else if (a === "about") {
      await loadStatus();
      const s = st.status || {};
      const sc = s.scan || {};
      dialog("Bağlantı durumu", `<div class="status-grid">İdealData: <b class="${s.healthy ? "pos" : "neg"}">${esc(s.healthy ? "Canlı" : s.label || s.state || "—")}</b>${s.error ? " · " + esc(s.error) : ""}<br>
        Kullanıcı: ${esc(s.user || "—")}<br>Tarama: ${fN(sc.universe)} hisse · döngü ~${fN(sc.last_cycle_sec || sc.est_cycle_sec)} sn<br>
        Seans: ${sc.session_open ? "açık" : "kapalı"}<br>Sürüm: v${VERSION}</div>`);
    }
  }));

  // -------------------------------------------------------------- dialogs
  function dialog(title, html) { $("dlg-title").textContent = title; $("dlg-content").innerHTML = html; $("dlg").hidden = false; }
  $("btn-share").addEventListener("click", async () => {
    const q = (st.ideal && st.ideal.quote) || {};
    const text = `${st.sym} ₺${fP(q.price)} (${fPct(q.change_pct)})`;
    const url = location.origin + "/?symbol=" + st.sym;
    try {
      if (navigator.share) await navigator.share({ title: st.sym, text, url });
      else { await navigator.clipboard.writeText(text + " " + url); toast("Bağlantı kopyalandı"); }
    } catch (e) {}
  });
  $("btn-note").addEventListener("click", () => {
    dialog(`${st.sym} · Not`, `<label>Kişisel not (bu cihazda saklanır)<textarea id="note-txt">${esc(st.notes[st.sym] || "")}</textarea></label><button type="button" class="btn-primary" id="note-save">Kaydet</button>`);
    $("note-save").addEventListener("click", () => {
      const v = $("note-txt").value.trim();
      if (v) st.notes[st.sym] = v; else delete st.notes[st.sym];
      LS.set("notes", st.notes); closeSheets(); toast("Not kaydedildi");
    });
  });

  // --------------------------------------------------------------- alarms
  function renderAlarmBadge() {
    const n = st.alarms.filter((a) => a.sym === st.sym).length;
    const b = $("alarm-count"); b.hidden = !n; b.textContent = n;
    $("btn-alarm").classList.toggle("on-alarm", n > 0);
  }
  $("btn-alarm").addEventListener("click", () => {
    const p = st.lastPrice;
    const mine = st.alarms.filter((a) => a.sym === st.sym);
    dialog(`${st.sym} · Fiyat alarmı`, `<label>Koşul<select id="al-op"><option value="gte">Fiyat ≥ hedef</option><option value="lte">Fiyat ≤ hedef</option></select></label>
      <label>Hedef fiyat (₺)<input type="number" id="al-target" step="0.01" inputmode="decimal" value="${isNum(p) ? p.toFixed(2) : ""}" /></label>
      <button type="button" class="btn-primary" id="al-add">Alarm kur</button>
      <ul class="alarm-list">${mine.map((a) => `<li><span>${a.op === "gte" ? "≥" : "≤"} ₺${fP(a.target)}${a.off ? ' <small class="muted">(KAPALI — Bildirimler › Alarmlar)</small>' : ""}</span><button type="button" class="btn-ghost" data-del="${a.id}">Sil</button></li>`).join("") || '<li class="muted">Bu hisse için alarm yok</li>'}</ul>`);
    $("al-add").addEventListener("click", () => {
      const t = parseFloat(String($("al-target").value).replace(",", "."));
      if (!isNum(t) || t <= 0) { toast("Geçerli bir fiyat girin"); return; }
      st.alarms.push({ id: Date.now().toString(36), sym: st.sym, op: $("al-op").value, target: t });
      LS.set("alarms", st.alarms); renderAlarmBadge(); closeSheets(); toast(`Alarm kuruldu: ${st.sym} ${$("al-op").value === "gte" ? "≥" : "≤"} ₺${fP(t)}`);
      askNotify(true);
    });
    document.querySelectorAll("#dlg [data-del]").forEach((b) => b.addEventListener("click", () => {
      st.alarms = st.alarms.filter((a) => a.id !== b.dataset.del); LS.set("alarms", st.alarms); renderAlarmBadge(); closeSheets();
    }));
  });
  function fireAlarm(a, price) {
    st.alarms = st.alarms.filter((x) => x.id !== a.id); LS.set("alarms", st.alarms); renderAlarmBadge();
    const title = `🔔 ${a.sym} ₺${fP(price)}`;
    const body = `Hedef ${a.op === "gte" ? "≥" : "≤"} ₺${fP(a.target)} gerçekleşti`;
    const mode = deliverLocal({ kind: "alarm", sub: "fiyat_alarmi", nt: "fiyat_alarmi", sym: a.sym, title, text: body, id: "al-" + a.id, time: clockFmt.format(new Date()) });
    if (mode !== "notify") return;
    api("/api/telegram/alarm", { method: "POST", body: JSON.stringify({ sym: a.sym, title, text: body }), headers: { "Content-Type": "application/json" } }).catch(() => {});   // v1.38.0
    try { if (navigator.vibrate) navigator.vibrate([200, 100, 200]); } catch (e) {}
    if ("Notification" in window && Notification.permission === "granted" && navigator.serviceWorker && navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: "SHOW_NOTIFICATION", title, body, tag: "alarm-" + a.id, symbol: a.sym, requireInteraction: true, vibrate: [200, 100, 200] });
    } else if ("Notification" in window && Notification.permission === "granted") {
      try { new Notification(title, { body }); } catch (e) {}
    }
  }
  function checkAlarms(sym, price) {
    if (!isNum(price)) return;
    for (const a of [...st.alarms]) if (!a.off && a.sym === sym && ((a.op === "gte" && price >= a.target) || (a.op === "lte" && price <= a.target))) fireAlarm(a, price);
  }
  setInterval(async () => {
    const others = st.alarms.filter((a) => a.sym !== st.sym && !a.off);
    if (!others.length) return;
    await loadList(true);
    const by = new Map(st.list.map((x) => [x.s, x.p]));
    for (const a of others) checkAlarms(a.sym, by.get(a.sym));
  }, 20000);
  async function askNotify(silent) {
    if (!("Notification" in window)) { if (!silent) toast(osActive() ? "Arka plan bildirimleri Telegram üzerinden açık ✓" : "Bu ortamda tarayıcı bildirimi yok — Telegram Bildirim Ayarları"); return; }
    if (Notification.permission === "granted") { if (!silent) toast("Bildirimler açık"); return; }
    try { const r = await Notification.requestPermission(); if (!silent) toast(r === "granted" ? "Bildirimler açıldı" : "Bildirim izni verilmedi"); } catch (e) {}
  }
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js?v=" + VERSION).catch(() => {});
    navigator.serviceWorker.addEventListener("message", (e) => { if (e.data && e.data.type === "ALARM_CLICK" && e.data.symbol) selectSymbol(e.data.symbol); });
  }

  // ============================================================ v1.18.0 ==
  // ---- broker short names (İşlemler tablosu, ekran görüntüsündeki gibi büyük harf)
  const BR_SHORT = { "Bank Of America": "BOFA", "Is Yatirim": "İŞ", "Yatirim Finansman": "YAT.FİN.", "QNB Invest": "QNB FİN.",
    "Citibank": "CITI", "Deutsche Bank": "DEUTSCHE", "Info Yatirim": "İNFO", "Garanti": "GARANTİ", "Ziraat": "ZİRAAT", "Midas": "MİDAS" };
  const brUp = (n) => (n ? BR_SHORT[n] || trUpper(brName(n)) : "—");

  // ---- logo cache (sayfa genelinde)
  const logoOk = new Set(), logoMiss = new Set();
  function logoSpan(sym, cl = "mv-logo") {
    if (logoOk.has(sym)) return `<span class="${cl}" style="background:#fff url(/api/logo/${sym}) center/82% no-repeat"></span>`;
    return `<span class="${cl}" data-logo2="${esc(sym)}" style="background-color:hsl(${hue(sym)} 40% 22%)">${esc(sym.slice(0, 2))}</span>`;
  }
  let logoIO = null;
  function lazyLogos2(root) {
    const els = root.querySelectorAll("[data-logo2]");
    if (!logoIO && "IntersectionObserver" in window) {
      logoIO = new IntersectionObserver((ents) => {
        for (const e of ents) if (e.isIntersecting) { loadLogo2(e.target); logoIO.unobserve(e.target); }
      }, { rootMargin: "200px" });
    }
    els.forEach((el) => { if (logoMiss.has(el.dataset.logo2)) return; logoIO ? logoIO.observe(el) : loadLogo2(el); });
  }
  function loadLogo2(el) {
    const s = el.dataset.logo2; if (!s || logoMiss.has(s)) return;
    const img = new Image();
    img.onload = () => { logoOk.add(s); el.style.background = `#fff url(/api/logo/${s}) center/82% no-repeat`; el.textContent = ""; };
    img.onerror = () => logoMiss.add(s);
    img.src = `/api/logo/${s}`;
  }
  const todayLong = () => new Intl.DateTimeFormat("tr-TR", { timeZone: "Europe/Istanbul", day: "numeric", month: "long", year: "numeric" }).format(new Date());
  const todayHead = () => trUpper(new Intl.DateTimeFormat("tr-TR", { timeZone: "Europe/Istanbul", day: "numeric", month: "long", weekday: "long" }).format(new Date()));
  document.querySelectorAll("[data-today]").forEach((el) => (el.textContent = todayLong()));

  // ------------------------------------------------------------- İŞLEMLER
  const isl = { broker: "", side: "", minutes: 0, minTl: 0, lot: "", sort: "time", rows: [], seen: new Set(), total: 0,
    allCount: 0, loading: false, brokersSym: null, brokersN: 0, PAGE: 200, done: false, data: null };
  function islUrl(offset, limit) {
    const p = new URLSearchParams({ sort: isl.sort, offset: String(offset), limit: String(limit) });
    if (isl.broker) p.set("broker", isl.broker);
    if (isl.side) p.set("side", isl.side);
    if (isl.minutes) p.set("minutes", String(isl.minutes));
    if (isl.minTl) p.set("min_tl", String(isl.minTl));
    if (isl.lot) { const [op, v] = isl.lot.split(":"); p.set(op === "eq" ? "lot_eq" : "lot_ge", v); }
    return `/api/ideal/${st.sym}/trades?` + p.toString();
  }
  function islRowHtml(t, isNew) {
    const side = t.side === "buy" ? "buy" : t.side === "sell" ? "sell" : t.side === "auction" ? "auction" : "";
    return `<tr class="${side}${isNew ? " new" : ""}"${side === "auction" ? ' title="Tek fiyat eşleşmesi"' : ""}><td>${esc(t.time)}</td><td>${fP(t.price)}</td><td>${fN(t.lot)}</td>
      <td class="br" title="${esc(brName(t.buyer))}">${esc(brUp(t.buyer))}</td><td class="br" title="${esc(brName(t.seller))}">${esc(brUp(t.seller))}</td></tr>`;
  }
  async function loadTrades(reset, more, pre) {
    if (isl.loading && !reset) return;
    const gen = st.gen;
    isl.loading = true;
    const offset = more ? isl.rows.length : 0;
    if (reset) $("isl-refresh").classList.add("spin");
    try {
      const d = pre || await api(islUrl(offset, isl.PAGE), { timeout: 20000 });
      if (gen !== st.gen) return;
      isl.data = d; isl.total = d.total; isl.allCount = d.all_count;
      const body = $("isl-body");
      if (more) {
        const add = d.rows.filter((r) => !isl.seen.has(r.n));
        add.forEach((r) => isl.seen.add(r.n));
        isl.rows = isl.rows.concat(add);
        if (add.length) body.insertAdjacentHTML("beforeend", add.map((r) => islRowHtml(r, false)).join(""));
        isl.done = d.rows.length < isl.PAGE;
        if (isl.done && isl.sort === "time" && !body.querySelector("tr.gap")) body.insertAdjacentHTML("beforeend", islGapRow(d));
      } else if (pre && !pre._full && !reset && isl.sort === "time" && isl.rows.length && d.rows.length) {
        // artımlı: yalnız yeni işlemler üste (yeniden çizim yok); boşluk bir sayfadan büyükse tam yenile
        const add = d.rows.filter((r) => !isl.seen.has(r.n));
        if (add.length >= d.rows.length) { isl.loading = false; return loadTrades(false, false, Object.assign({}, d, { _full: 1 })); }
        if (add.length) {
          add.forEach((r) => isl.seen.add(r.n));
          body.insertAdjacentHTML("afterbegin", add.map((r) => islRowHtml(r, true)).join(""));
          isl.rows = add.concat(isl.rows);
          const CAP = 1000;
          if (isl.rows.length > CAP) {
            const drop = isl.rows.splice(CAP);
            drop.forEach((r) => isl.seen.delete(r.n));
            const trs = body.querySelectorAll("tr:not(.gap)");
            for (let i = trs.length - 1; i >= CAP; i--) trs[i].remove();
            body.querySelectorAll("tr.gap").forEach((x) => x.remove());
            isl.done = false;
          }
        }
        $("isl-new").hidden = true;
      } else {
        const first = !isl.rows.length || reset;
        const old = isl.seen;
        isl.rows = d.rows; isl.seen = new Set(d.rows.map((r) => r.n));
        isl.done = d.rows.length < isl.PAGE;
        body.innerHTML = d.rows.length ? (isl.sort === "time_asc" ? islGapRow(d) : "") + d.rows.map((r) => islRowHtml(r, !first && isl.sort === "time" && !old.has(r.n))).join("") + (isl.done && isl.sort === "time" ? islGapRow(d) : "")
          : `<tr><td colspan="5" class="empty">${d.all_count ? "Filtreye uyan işlem yok" : "Bu hisse için kayıtlı işlem yok (henüz işlem görmemiş olabilir)"}</td></tr>`;
        $("isl-new").hidden = true;
      }
      renderTradesMeta(d);
      $("isl-more").hidden = isl.done;
    } catch (e) {
      if (gen === st.gen && !isl.rows.length) $("isl-body").innerHTML = `<tr><td colspan="5" class="empty">İşlemler alınamadı (${esc(e.message || e)})</td></tr>`;
    } finally { isl.loading = false; $("isl-refresh").classList.remove("spin"); }
  }
  // Türkçe ayrılma eki (-den/-dan/-ten/-tan) — saat/sayının okunuşuna göre
  function trAbl(t) {
    const m = String(t || "").match(/(\d+)\D*$/);
    if (!m) return "'den";
    const n = parseInt(m[1], 10), d = n % 10, tn = n % 100;
    let suf;
    if (d !== 0) suf = { 1: "den", 2: "den", 3: "ten", 4: "ten", 5: "ten", 6: "dan", 7: "den", 8: "den", 9: "dan" }[d];
    else if (tn === 0) suf = n === 0 ? "dan" : "den";
    else suf = { 10: "dan", 20: "den", 30: "dan", 40: "tan", 50: "den", 60: "tan", 70: "ten", 80: "den", 90: "dan" }[tn];
    return "'" + suf;
  }
  function islGapInfo(d) {
    const c = d.coverage || {};
    if (!c.complete_since || c.complete_since === "açılış") return null;
    const miss = d.missing_lot;
    return { from: "09:55", to: c.complete_since, lot: miss, pct: d.day_volume ? (miss / d.day_volume) * 100 : null };
  }
  function islGapRow(d) {
    const g = islGapInfo(d);
    if (!g) return "";
    return `<tr class="gap"><td colspan="5">⋯ <b>${g.from} – ${esc(g.to)}</b> arası tek tek işlem kaydı yok${isNum(g.lot) && g.lot > 0 ? ` · ≈ ${fShort(g.lot)} lot${isNum(g.pct) ? ` (gün hacminin %${nf(1).format(g.pct)})` : ""}` : ""}<br><small>İdealData geçmiş işlem listesi sunmuyor (yalnızca son 50 işlem); sunucu bu saatten itibaren her işlemi kaydediyor. Sonraki günlerde açılıştan (09:55) itibaren tam.</small></td></tr>`;
  }
  // v1.37.0: gecikme göstergesi — (sunucu saati − son işlem) ve (istemci saati − sunucu yanıt anı); >3 sn kırmızı
  function islLag(d) {
    let el = $("isl-lag");
    if (!el) { el = document.createElement("div"); el.id = "isl-lag"; el.className = "isl-lag"; $("isl-meta").after(el); }
    const a = isNum(d.lag_srv) ? d.lag_srv : null, b = isNum(d.server_ts) ? Math.max(0, Date.now() / 1000 - d.server_ts) : null;
    const f = (x) => x == null ? "—" : x < 60 ? nf(1).format(x) + " sn" : x < 3600 ? Math.round(x / 60) + " dk" : Math.round(x / 3600) + " sa";
    const bad = (a != null && a > 3 && d.live) || (b != null && b > 3);
    el.className = "isl-lag" + (bad ? " bad" : "");
    el.innerHTML = `⏱ Gecikme · son işlem: <b>${f(a)}</b>${d.live ? "" : " <i>(canlı akış yok)</i>"} · sunucu→ekran: <b>${f(b)}</b>`;
  }
  function renderTradesMeta(d) {
    const c = d.coverage || {};
    let txt;
    if (c.complete_since === "açılış") txt = `Kayıt: 09:55${trAbl("55")} (açılış) beri tam`;
    else if (c.complete_since) txt = `Kayıt: ${c.complete_since}${trAbl(c.complete_since)} beri tam · öncesi eksik`;
    else txt = "Kayıt: —";
    txt += ` · ${fN(d.all_count)} işlem`;
    if (c.first_time) txt += ` · ilk ${c.first_time}`;
    if (isNum(c.coverage_pct)) txt += ` · gün hacmi kapsaması %${nf(1).format(c.coverage_pct)}`;
    if (c.gap_count) txt += ` · ${c.gap_count} kısa kesinti`;
    $("isl-meta").textContent = txt;
    islLag(d);
    $("isl-meta").title = d.history_note || "";
    const s = d.sums || {};
    const bs = (s.buy_lot || 0) + (s.sell_lot || 0);
    $("isl-sums").innerHTML = `<span><b>${fN(d.total)}</b> işlem</span><span><b>${fShort(s.lot)}</b> lot</span><span><b>${fShort(s.tl)}</b> ₺</span>
      <span class="pos">Alış ${bs ? "%" + nf(0).format((s.buy_lot / bs) * 100) : "—"}</span><span class="neg">Satış ${bs ? "%" + nf(0).format((s.sell_lot / bs) * 100) : "—"}</span>`;
    // broker dropdown
    const brs = d.brokers || [];
    if (isl.brokersSym !== st.sym || Math.abs(brs.length - isl.brokersN) > 0) {
      isl.brokersSym = st.sym; isl.brokersN = brs.length;
      const sel = $("isl-broker");
      const cur = isl.broker;
      sel.innerHTML = `<option value="">KURUM SEÇ</option>` + brs.map((b) => `<option value="${esc(b.name)}">${esc(brUp(b.name))} (${fN(b.count)})</option>`).join("");
      sel.value = cur;
      if (sel.value !== cur) { sel.value = ""; }
    }
  }
  $("isl-broker").addEventListener("change", (e) => { isl.broker = e.target.value; loadTrades(true); });
  $("isl-time").addEventListener("change", (e) => { isl.minutes = +e.target.value; loadTrades(true); });
  document.querySelectorAll("#isl-side button").forEach((b) => b.addEventListener("click", () => {
    isl.side = b.dataset.side; document.querySelectorAll("#isl-side button").forEach((x) => x.classList.toggle("active", x === b)); loadTrades(true);
  }));
  document.querySelectorAll("#isl-tl button").forEach((b) => b.addEventListener("click", () => {
    isl.minTl = +b.dataset.v; document.querySelectorAll("#isl-tl button").forEach((x) => x.classList.toggle("active", x === b)); loadTrades(true);
  }));
  function setLotChip(v) {
    isl.lot = v;
    document.querySelectorAll("#isl-lot button").forEach((x) => x.classList.toggle("active", x.dataset.v === v));
    const sel = $("isl-lot-other");
    const inBtn = [...document.querySelectorAll("#isl-lot button")].some((x) => x.dataset.v === v);
    sel.classList.toggle("active", !inBtn && !!v);
    if (inBtn || !v) sel.value = "";
    loadTrades(true);
  }
  document.querySelectorAll("#isl-lot button").forEach((b) => b.addEventListener("click", () => setLotChip(b.dataset.v)));
  $("isl-lot-other").addEventListener("change", (e) => {
    let v = e.target.value;
    if (v === "custom") {
      const x = prompt("Lot filtresi: tam sayı girin (örn. 50) veya '>=500'", "100");
      if (!x) { e.target.value = ""; return; }
      const m = String(x).trim().match(/^(>=|≥)?\s*([\d.]+)$/);
      if (!m) { toast("Geçersiz lot"); e.target.value = ""; return; }
      const n = parseInt(m[2].replace(/\./g, ""), 10);
      v = (m[1] ? "ge:" : "eq:") + n;
      const opt = document.createElement("option"); opt.value = v; opt.textContent = (m[1] ? "≥ " : "= ") + fN(n);
      e.target.insertBefore(opt, e.target.lastElementChild); e.target.value = v;
    }
    if (!v) { setLotChip(""); return; }
    isl.lot = v;
    document.querySelectorAll("#isl-lot button").forEach((x) => x.classList.remove("active"));
    e.target.classList.add("active");
    loadTrades(true);
  });
  document.querySelectorAll("#isl-sort button").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.sort === "time" && (isl.sort === "time" || isl.sort === "time_asc")) isl.sort = isl.sort === "time" ? "time_asc" : "time";
    else isl.sort = b.dataset.sort;
    document.querySelectorAll("#isl-sort button").forEach((x) => x.classList.toggle("active", x === b));
    const tb = document.querySelector('#isl-sort [data-sort="time"]');
    tb.textContent = isl.sort === "time_asc" ? "ZAMAN ↑" : "ZAMAN";
    tb.title = isl.sort === "time_asc" ? "Eskiden yeniye (ilk işlemler)" : "Yeniden eskiye — eskiden yeniye için tekrar dokunun";
    window.scrollTo(0, Math.min(window.scrollY, document.querySelector("[data-pane=islemler]").offsetTop));
    loadTrades(true);
  }));
  $("isl-refresh").addEventListener("click", () => loadTrades(true));
  $("isl-more").addEventListener("click", () => loadTrades(false, true));
  $("isl-new").addEventListener("click", () => { window.scrollTo({ top: 0, behavior: "smooth" }); loadTrades(true); });
  if ("IntersectionObserver" in window) {
    new IntersectionObserver((ents) => {
      if (ents.some((e) => e.isIntersecting) && st.view === "stock" && st.tab === "islemler" && !isl.done && isl.rows.length && !isl.loading) loadTrades(false, true);
    }, { rootMargin: "400px" }).observe($("isl-sentinel"));
  }
  async function pollTrades() {
    if (isl.loading) return;
    if (isl.sort !== "time_asc" && isl.rows.length <= isl.PAGE && (window.scrollY < 900 || isl.sort !== "time")) { loadTrades(false); return; }   // v1.22.1: LOT/HACİM görünümleri kaydırılmışken de yerinde yenilenir
    try {
      const d = await api(islUrl(0, 1), { timeout: 8000 });
      const n = d.total - isl.total;
      if (n > 0 && isl.sort === "time") { $("isl-new").hidden = false; $("isl-new").textContent = `↑ ${fN(n)} yeni işlem`; }
    } catch (e) {}
  }

  // ---------------------------------------------------------------- router
  st.view = "stock"; st.mvMode = "change";
  const viewStack = [];
  const WIDE = new Set(["baski", "kurum", "movers", "endeks", "radar", "tavan", "agresif", "para", "kurumuyari", "tahtaci", "bildirim", "op", "akdt", "akk", "fm_mum", "fm_grafik", "olay", "tren", "skor", "algo", "albunu", "obt"]);
  function go(view, opts = {}) {
    if (view === "linkopt") { lkOpen(); return; }
    if (view === "telegram") { setTimeout(tgOpen, 0); }   // v1.38.0 TELEGRAM BİLDİRİM AYARLARI   // v1.35.0 LİNK OPTİMİZASYON (pencere)
    try { eikLeave(view); } catch (e) {}   // v1.29.0
    let navKey = view;
    if (view === "hacim") { st.mvMode = "volume"; view = "movers"; }
    else if (view === "movers") { if (!opts.keepMode) st.mvMode = "change"; }
    if (view === "movers" && st.mvMode === "volume") navKey = "hacim";
    if (view === "op" && st.opId == null) st.opId = 29;
    if (!opts.noPush && (st.view !== view || view === "movers" || (view === "op" && st._opPrev !== st.opId))) viewStack.push({ v: st.view, m: st.mvMode, o: st._opPrev });
    if (view === "op") st._opPrev = st.opId;
    if (viewStack.length > 30) viewStack.shift();
    st.view = view;
    document.querySelectorAll(".view").forEach((v) => (v.hidden = v.dataset.view !== view));
    if (st.kfOpen) kfClose();
    if (st.kfReady) navActive(); else document.querySelectorAll("#bnav button").forEach((b) => b.classList.toggle("active", b.dataset.go === navKey));
    document.body.classList.toggle("wide", WIDE.has(view) || (view === "stock" && st.tab === "akd"));
    try { history.replaceState(null, "", view === "stock" ? "/?symbol=" + st.sym : view === "op" ? "/#op-" + st.opId : "/#" + navKey); } catch (e) {}
    if (!opts.keepScroll) { sgNav(); window.scrollTo(0, 0); SG.y = 0; }
    if (view === "movers") { renderMovers(); loadMovers(); }
    else if (view === "akis") loadEvents(true);
    else if (view === "baski") loadBaski();
    else if (view === "kurum") { loadKurumBrokers(); loadKurum(true); }
    else if (view === "endeks") { loadIxCatalog(); loadIx(true); }
    else if (["radar", "tavan", "agresif", "para", "kurumuyari", "tahtaci"].includes(view)) v120Open(view);
    else if (view === "favs") { renderFavs(); loadMovers(); }
    else if (view === "bildirim") renderNf();
    else if (view === "op") opLoad(false);
    else if (view === "akdt") atOpen();   // v1.26.0 AKD TARAMASI
    else if (view === "akk") akkOpen();   // v1.26.2 AKTİF İŞLEM TARAMASI (KURUM)
    else if (view === "fm_mum" || view === "fm_grafik") fmOpen(view);   // v1.27.0 FORMASYONLAR
    else if (view === "eik") eikOpen();   // v1.29.0 EN İYİ KOŞULLAR
    else if (view === "olay") olOpen();   // v1.30.0 OLAY LİSTESİ (ALARM)
    else if (view === "tren") trOpen();   // v1.31.0 TRENE ATLA
    else if (view === "skor") skOpen();   // v1.32.0 D-A-K SKORLARI
    else if (view === "algo") alOpen();   // v1.33.0 ALGO DESTEK / DİRENÇ
    else if (view === "albunu") abOpen();   // v1.34.0 AL BUNU
    else if (view === "obt") obtOpen();   // v1.36.0 ORDER BLOCK TARAMASI
    else if (view === "stock") { pollIdeal(true); openTab(st.tab, false); }
  }
  function goBack() {
    const prev = viewStack.pop();
    if (prev) { st.mvMode = prev.m; if (prev.v === "op" && prev.o != null) { st.opId = prev.o; st._opPrev = prev.o; } go(prev.v === "movers" && prev.m === "volume" ? "hacim" : prev.v, { noPush: true, keepMode: true }); }
    else go("stock", { noPush: true });
  }
  document.querySelectorAll("#bnav button").forEach((b) => b.addEventListener("click", () => go(b.dataset.go)));
  document.querySelectorAll("[data-goback]").forEach((b) => b.addEventListener("click", goBack));
  function openStock(sym) { selectSymbol(sym); go("stock"); st.fromScreen = true; }

  // ----------------------------------------------------- MOVERS / HACİM
  st.movers = null; st.moversTs = 0; st.mvAll = false;
  async function loadMovers() {
    try {
      const d = await api("/api/live/movers", { timeout: 15000 });
      st.movers = d; st.moversTs = Date.now();
      if (st.view === "movers") renderMovers();
      if (st.view === "favs") renderFavs();
    } catch (e) {
      if (st.view === "movers" && !st.movers) $("mv-up").innerHTML = `<div class="empty">Veri alınamadı (${esc(e.message || e)})</div>`;
    }
  }
  function mvRow(r, i, mode) {
    const pill = `<span class="mv-pill ${cls(r.c)}">${isNum(r.c) ? (r.c > 0 ? "" : "") + nf(2).format(Math.abs(r.c)) + "%" : "—"}</span>`;
    if (mode === "volume") {
      return `<div class="mv-row" data-sym="${esc(r.s)}"><span class="mv-rank">${i}</span>${logoSpan(r.s)}<div class="mv-mid"><div class="mv-sym">${esc(r.s)}</div><div class="mv-px">${fP(r.p)} ₺</div></div>
        <div class="mv-tl">${fShort(r.t)} ₺<small>${fShort(r.v)} lot</small></div><span class="mv-pill ${cls(r.c)}">${fPct(r.c)}</span></div>`;
    }
    return `<div class="mv-row" data-sym="${esc(r.s)}"><span class="mv-rank">${i}</span>${logoSpan(r.s)}<div class="mv-mid"><div class="mv-sym">${esc(r.s)}</div><div class="mv-px">${fP(r.p)} ₺</div></div>${pill}</div>`;
  }
  function renderMovers() {
    const vol = st.mvMode === "volume";
    $("mv-title").textContent = vol ? "Yüksek Hacimliler" : "Yükselenler & Düşenler";
    $("mv-sub").textContent = vol ? "TL hacme göre anlık sıralama" : "Anlık fiyat değişim sıralaması";
    document.querySelectorAll("#mv-btns button").forEach((b) => b.classList.toggle("active", b.dataset.mode === st.mvMode));
    $("mv-cols").hidden = vol; $("mv-vol").hidden = !vol;
    const d = st.movers;
    if (!d) { $("mv-up").innerHTML = $("mv-down").innerHTML = $("mv-vlist").innerHTML = `<div class="empty">Yükleniyor…</div>`; return; }
    $("mv-breadth").innerHTML = `<span class="pos">▲ ${fN(d.positive)} Pozitif</span><span class="neg">▼ ${fN(d.negative)} Negatif</span><span class="neu">● ${fN(d.neutral)} Nötr</span>`;
    const rows = d.rows || [];
    const N = st.mvAll ? 1000 : vol ? 60 : 30;
    if (vol) {
      const v = [...rows].sort((a, b) => (b.t || 0) - (a.t || 0)).slice(0, N);
      $("mv-vlist").innerHTML = v.map((r, i) => mvRow(r, i + 1, "volume")).join("") || `<div class="empty">Veri yok</div>`;
      lazyLogos2($("mv-vlist"));
      $("mv-more").hidden = rows.length <= N;
    } else {
      const up = rows.filter((r) => r.c > 0).sort((a, b) => b.c - a.c || (b.t || 0) - (a.t || 0));
      const dn = rows.filter((r) => r.c < 0).sort((a, b) => a.c - b.c || (b.t || 0) - (a.t || 0));
      $("mv-up").innerHTML = up.slice(0, N).map((r, i) => mvRow(r, i + 1)).join("") || `<div class="empty">Yükselen yok</div>`;
      $("mv-down").innerHTML = dn.slice(0, N).map((r, i) => mvRow(r, i + 1)).join("") || `<div class="empty">Düşen yok</div>`;
      lazyLogos2($("mv-cols"));
      $("mv-more").hidden = up.length <= N && dn.length <= N;
    }
    $("mv-more").textContent = st.mvAll ? "Daha az göster" : "Tümünü göster";
    $("mv-note").textContent = `Kaynak: İdealData canlı · ${fN(d.count)} BIST payı · ${String(d.updated || "").slice(11)}`;
  }
  document.querySelectorAll("#mv-btns button").forEach((b) => b.addEventListener("click", () => { st.mvMode = b.dataset.mode; go(st.mvMode === "volume" ? "hacim" : "movers", { keepMode: true, noPush: true, keepScroll: true }); }));
  $("mv-more").addEventListener("click", () => { st.mvAll = !st.mvAll; renderMovers(); });
  ["mv-cols", "mv-vol", "fv-list"].forEach((id) => $(id).addEventListener("click", (e) => { const r = e.target.closest("[data-sym]"); if (r) openStock(r.dataset.sym); }));

  // ------------------------------------------------------------------ AKIŞ
  const ak = { kind: "all", q: "", events: [], lastId: 0, counts: {}, fav: 0, cap: 300, newIds: new Set(), day: null };
  const AK_BADGE = { tavan: "TAVAN", taban: "TABAN", tur: "TUR", devre: "DEVRE", hacim: "HACİM", "52h": "52H", kapanis: "KAPANIŞ", diger: "DİĞER", kademe: "KADEME" };
  async function loadEvents(reset) {
    const fav = st.favs.join(",");
    try {
      const url = reset || !ak.lastId ? `/api/live/events?limit=2000&syms=${encodeURIComponent(fav)}` : `/api/live/events?since_id=${ak.lastId}&limit=1000&syms=${encodeURIComponent(fav)}`;
      const d = await api(url, { timeout: 15000 });
      if (!reset && ak.day && d.day !== ak.day) { ak.day = d.day; ak.lastId = 0; return loadEvents(true); }   // v1.22.0 gün değişti → baştan
      ak.fallback = !!d.fallback; ak.note = d.note || "";
      if (reset || !ak.lastId || d.day !== ak.day) { ak.events = d.events; ak.newIds = new Set(); }
      else if (d.events.length) { ak.newIds = new Set(d.events.map((e) => e.id)); ak.events = d.events.concat(ak.events).slice(0, 5000); }
      else ak.newIds = new Set();
      ak.day = d.day; ak.lastId = Math.max(ak.lastId || 0, d.last_id || 0); if (reset) ak.lastId = d.last_id || 0;
      ak.counts = d.counts || {}; ak.fav = d.fav_count || 0;
      renderEvents();
    } catch (e) {
      if (!ak.events.length) $("ak-list").innerHTML = `<div class="empty">Olaylar alınamadı (${esc(e.message || e)})</div>`;
    }
  }
  function renderEvents() {
    const c = ak.counts;
    document.querySelectorAll("#ak-chips button").forEach((b) => {
      const k = b.dataset.k;
      b.classList.toggle("active", k === ak.kind);
      const v = k === "fav" ? ak.fav : c[k] || 0;
      b.querySelector("b").textContent = fN(v);
    });
    $("ak-date").textContent = ak.fallback && ak.note ? ak.note : todayHead();
    const qv = fold(ak.q.trim());
    const favs = new Set(st.favs);
    let list = ak.events.filter((e) => {
      if (ak.kind === "fav") { if (!favs.has(e.sym)) return false; }
      else if (ak.kind === "tavantaban") { if (e.kind !== "tavan" && e.kind !== "taban") return false; }
      else if (ak.kind !== "all" && e.kind !== ak.kind) return false;
      if (qv && !fold(e.sym || "").includes(qv) && !fold(e.text).includes(qv) && !fold(e.cumle || "").includes(qv) && !fold(AK_BADGE[e.kind] || "").includes(qv)) return false;
      return true;
    });
    const total = list.length;
    list = list.slice(0, ak.cap);
    if (!list.length) { $("ak-list").innerHTML = `<div class="empty">${ak.events.length ? "Filtreye uyan olay yok" : "Henüz olay yok — seans içinde (09:55–18:10) canlı olarak oluşur"}</div>`; return; }
    let prevMin = null, h = "";
    for (const e of list) {
      const hm = (e.time || "").slice(0, 5);
      let bc = e.kind;
      if (e.kind === "tavan" || e.kind === "taban") bc = e.kind + "-" + (e.variant === "off" ? "off" : "on");
      if (e.kind === "52h") bc = "h52";
      h += `<div class="ak-row${ak.newIds.has(e.id) ? " new" : ""}"><span class="ak-time${hm === prevMin ? " dim" : ""}">${esc(hm)}</span>
        <span class="ak-badge ${bc}">${AK_BADGE[e.kind] || "OLAY"}</span><span class="ak-sym" data-sym="${esc(e.sym || "")}">${esc(e.sym || "—")}</span>
        <span class="ak-text ak-px" title="${esc(e.time)} · ${esc(e.text)}">${e.price ? fP(e.price) + " ₺" : ""}${e.initial ? '<span class="ak-init">(izleme başı)</span>' : ""}</span>
        <div class="ak-cumle">${esc(e.cumle || e.text || "")}</div></div>`;
      prevMin = hm;
    }
    if (total > list.length) h += `<button type="button" class="more-btn" id="ak-more">Daha fazla göster (+${fN(total - list.length)})</button>`;
    $("ak-list").innerHTML = h;
    const mb = $("ak-more"); if (mb) mb.addEventListener("click", () => { ak.cap += 300; renderEvents(); });
  }
  document.querySelectorAll("#ak-chips button").forEach((b) => b.addEventListener("click", () => { ak.kind = b.dataset.k; ak.cap = 300; renderEvents(); }));
  let akT = null;
  $("ak-search").addEventListener("input", (e) => { clearTimeout(akT); akT = setTimeout(() => { ak.q = e.target.value; ak.cap = 300; renderEvents(); }, 150); });
  $("ak-list").addEventListener("click", (e) => { const s = e.target.closest(".ak-sym[data-sym]"); if (s && s.dataset.sym) openStock(s.dataset.sym); });

  // ------------------------------------------------------- DERİNLİK BASKISI
  const bk = { sort: "p25", dir: -1, f: "all", q: "", n: 100, data: null };
  async function loadBaski() {
    try { bk.data = await api("/api/live/depth-pressure", { timeout: 15000 }); renderBaski(); }
    catch (e) { if (!bk.data) $("bk-body").innerHTML = `<tr><td colspan="9" class="empty">Veri alınamadı (${esc(e.message || e)})</td></tr>`; }
  }
  const pcell = (v) => (isNum(v) ? `<span class="pbar"><i style="--w:${Math.max(0, Math.min(100, v)).toFixed(0)}%"></i><b class="${v >= 50 ? "pos" : "neg"}">%${nf(1).format(v)}</b></span>` : `<span class="muted">—</span>`);
  function renderBaski() {
    const d = bk.data; if (!d) return;
    let rows = d.rows || [];
    const qv = fold(bk.q.trim());
    if (qv) rows = rows.filter((r) => r.s.includes(qv));
    if (bk.f === "buy") rows = rows.filter((r) => isNum(r.p25) && r.p25 > 50);
    else if (bk.f === "sell") rows = rows.filter((r) => isNum(r.p25) && r.p25 < 50);
    const k = bk.sort, dir = bk.dir;
    rows = [...rows].sort((a, b) => {
      if (k === "s") return dir * a.s.localeCompare(b.s);
      const va = a[k], vb = b[k];
      if (!isNum(va) && !isNum(vb)) return 0; if (!isNum(va)) return 1; if (!isNum(vb)) return -1;
      return dir * (va - vb);
    });
    document.querySelectorAll("#bk-table th").forEach((th) => { th.classList.toggle("sorted", th.dataset.k === k); th.classList.toggle("asc", th.dataset.k === k && dir > 0); });
    const show = rows.slice(0, bk.n);
    $("bk-body").innerHTML = show.map((r) => `<tr><td class="l sticky sym" data-sym="${esc(r.s)}">${esc(r.s)}</td><td>${fP(r.p)}</td><td class="${cls(r.c)}">${fPct(r.c)}</td>
      <td class="pos">${fN(r.b25)}</td><td class="neg">${fN(r.a25)}</td><td>${pcell(r.p25)}</td>
      <td class="pos">${fN(r.ball)}</td><td class="neg">${fN(r.aall)}</td><td>${pcell(r.pall)}</td></tr>`).join("") || `<tr><td colspan="9" class="empty">Sonuç yok</td></tr>`;
    $("bk-more").hidden = rows.length <= bk.n;
    $("bk-more").textContent = `Daha fazla göster (+${fN(rows.length - bk.n)})`;
    $("bk-note").textContent = `${fN(d.count)} hisse · ${d.note} · ${String(d.updated || "").slice(11)}`;
  }
  document.querySelectorAll("#bk-table th").forEach((th) => th.addEventListener("click", () => {
    if (bk.sort === th.dataset.k) bk.dir *= -1; else { bk.sort = th.dataset.k; bk.dir = th.dataset.k === "s" ? 1 : -1; }
    renderBaski();
  }));
  document.querySelectorAll("#bk-filter button").forEach((b) => b.addEventListener("click", () => {
    bk.f = b.dataset.f; document.querySelectorAll("#bk-filter button").forEach((x) => x.classList.toggle("active", x === b)); renderBaski();
  }));
  $("bk-search").addEventListener("input", (e) => { bk.q = e.target.value; renderBaski(); });
  $("bk-more").addEventListener("click", () => { bk.n += 200; renderBaski(); });
  $("bk-body").addEventListener("click", (e) => { const t = e.target.closest("[data-sym]"); if (t) openStock(t.dataset.sym); });

  // ------------------------------------------------ HİSSELERİN ENDEKSE ETKİSİ (v1.19.0)
  const ix = { code: LS.get("ix_code", "XU100"), sort: "pts", dir: -1, f: "all", q: "", n: 150, data: null, cat: null, grp: "", busy: false };
  const IX_QUICK = ["XU100", "XU030", "XU050", "XUTUM", "XBANK", "XUSIN", "XUMAL", "XHOLD", "XK100", "XYLDZ"];
  const SRC_LBL = { idealdata: "GERÇEK AĞIRLIK · İdealData", tahmini: "TAHMİNİ AĞIRLIK", yok: "AĞIRLIK VERİSİ YOK" };
  async function loadIxCatalog() {
    try { ix.cat = await api("/api/index-impact/indices", { timeout: 20000 }); renderIxQuick(); if (!$("ix-sheet").hidden) renderIxList(); }
    catch (e) {}
  }
  async function loadIx(fresh) {
    if (ix.busy) return; ix.busy = true;
    const code = ix.code;
    try {
      const d = await api(`/api/index-impact/${encodeURIComponent(code)}`, { timeout: 20000 });
      if (code !== ix.code) return;
      ix.data = d; renderIx();
    } catch (e) {
      if (!ix.data || fresh) $("ix-body").innerHTML = `<tr><td colspan="8" class="empty">Veri alınamadı (${esc(e.message || e)})</td></tr>`;
    } finally { ix.busy = false; }
  }
  function ixInfo(code) { return ((ix.cat && ix.cat.indices) || []).find((x) => x.code === code); }
  function renderIxQuick() {
    const el = $("ix-quick");
    el.innerHTML = IX_QUICK.map((c) => { const i = ixInfo(c) || { code: c };
      return `<button type="button" data-ix="${c}" class="${c === ix.code ? "active" : ""}"><b>${c}</b><span class="${cls(i.chg)}">${fPct(i.chg)}</span></button>`; }).join("") +
      `<button type="button" data-ix="*" class="more">Tüm endeksler (${ix.cat ? ix.cat.count : "…"}) ›</button>`;
  }
  $("ix-quick").addEventListener("click", (e) => { const b = e.target.closest("[data-ix]"); if (!b) return; if (b.dataset.ix === "*") openIxSheet(); else setIx(b.dataset.ix); });
  function setIx(code) {
    if (!code) return; ix.code = code; LS.set("ix_code", code); ix.data = null; ix.n = 150;
    $("ix-body").innerHTML = `<tr><td colspan="8" class="empty">${esc(code)} yükleniyor…</td></tr>`;
    $("ix-sum").innerHTML = `<div class="empty">Yükleniyor…</div>`; $("ix-bars").innerHTML = "";
    const i = ixInfo(code); $("ix-code").textContent = code; $("ix-name").textContent = i ? i.name : "";
    renderIxQuick(); loadIx(true);
  }
  function openIxSheet() {
    $("ix-sheet").hidden = false; $("ix-sheet-input").value = ""; renderIxList();
    setTimeout(() => $("ix-sheet-input").focus(), 50);
    if (!ix.cat) loadIxCatalog();
  }
  $("ix-pick").addEventListener("click", openIxSheet);
  $("ix-sheet-input").addEventListener("input", renderIxList);
  $("ix-groups").addEventListener("click", (e) => { const b = e.target.closest("[data-g]"); if (!b) return; ix.grp = b.dataset.g; renderIxList(); });
  $("ix-list").addEventListener("click", (e) => { const li = e.target.closest("[data-ix]"); if (!li) return; $("ix-sheet").hidden = true; setIx(li.dataset.ix); });
  function renderIxList() {
    const all = (ix.cat && ix.cat.indices) || [];
    const groups = (ix.cat && ix.cat.groups) || [];
    $("ix-groups").innerHTML = [["", "TÜMÜ"], ...groups.map((g) => [g, trUpper(g)])].map(([g, l]) =>
      `<button type="button" data-g="${esc(g)}" class="${ix.grp === g ? "active" : ""}">${esc(l)} <b>${g ? all.filter((x) => x.group === g).length : all.length}</b></button>`).join("");
    const qv = fold($("ix-sheet-input").value.trim());
    let items = all.filter((x) => !ix.grp || x.group === ix.grp);
    if (qv) {
      items = items.filter((x) => fold(x.code).includes(qv) || fold(x.name).includes(qv));
      items.sort((a, b) => (fold(a.code).startsWith(qv) ? 0 : 1) - (fold(b.code).startsWith(qv) ? 0 : 1));
    }
    $("ix-sheet-meta").textContent = all.length ? `${all.length} endeks · ${items.length} sonuç · bileşen listesi BIST ${ix.cat.bist_list_date || ""}` : "Endeks listesi yükleniyor…";
    let lastG = null;
    $("ix-list").innerHTML = items.map((x) => {
      const head = !qv && x.group !== lastG ? `<li class="ix-gh">${esc(trUpper(x.group))}</li>` : ""; lastG = x.group;
      const tag = x.source === "tahmini" ? `<span class="ix-tag est">TAHMİNİ</span>` : x.source === "yok" ? `<span class="ix-tag no">VERİ YOK</span>` : "";
      return head + `<li data-ix="${esc(x.code)}" class="${x.code === ix.code ? "cur" : ""}"><span class="sl-logo ix-logo">${esc(x.code.replace(/^X/, "").slice(0, 4))}</span>
        <div class="sl-mid"><div class="sl-sym">${esc(x.code)} ${tag}</div><div class="sl-name">${esc(x.name)}${x.count ? " · " + x.count + " hisse" : ""}</div></div>
        <div class="sl-r"><div class="sl-p">${isNum(x.last) ? fN(x.last, 2) : "—"}</div><div class="sl-c ${cls(x.chg)}">${fPct(x.chg)}</div></div></li>`;
    }).join("") || `<li class="empty" style="justify-content:center">Sonuç yok</li>`;
  }
  const fPts = (v, d = 2) => (isNum(v) ? (v > 0 ? "+" : "") + nf(d).format(v) : "—");
  function renderIx() {
    const d = ix.data; if (!d) return;
    const L = d.level || {}, M = d.model || {}, B = d.breadth || {};
    $("ix-code").textContent = d.code; $("ix-name").textContent = d.name || "";
    $("ix-lvl").textContent = isNum(L.last) ? fN(L.last, 2) : isNum(L.estimated_last) ? "~" + fN(L.estimated_last, 2) : "—";
    $("ix-chg").innerHTML = isNum(L.chg_pts) ? `<span class="${cls(L.chg_pts)}">${fPts(L.chg_pts)} p · ${fPct(L.chg_pct)}</span>` : (isNum(M.pct) ? `<span class="${cls(M.pct)}">~${fPct(M.pct)}</span>` : "—");
    const srcCls = d.weight_source === "idealdata" ? "real" : d.weight_source === "tahmini" ? "est" : "no";
    const lvlSrc = L.source === "idealdata" ? "İdealData canlı" : L.source === "oyak" ? "Oyak Yatırım (gecikmeli olabilir)" : "seviye yok";
    const expl = isNum(M.explained_pct) ? `<div class="kv"><span class="k">Ağırlıklarla açıklanan</span><span class="v">%${fN(M.explained_pct, 1)}</span></div>` : "";
    $("ix-sum").innerHTML = `<div class="ix-src ${srcCls}">${SRC_LBL[d.weight_source] || d.weight_source}${d.weight_source === "tahmini" ? " — gerçek ağırlık değildir" : ""}</div>
      <div class="kv-grid">
        <div class="kv"><span class="k">Endeks (son)</span><span class="v">${isNum(L.last) ? fN(L.last, 2) : "—"}</span></div>
        <div class="kv"><span class="k">Önceki kapanış</span><span class="v">${isNum(L.prev) ? fN(L.prev, 2) : "—"}</span></div>
        <div class="kv"><span class="k">Gerçek değişim</span><span class="v ${cls(L.chg_pts)}">${fPts(L.chg_pts)} p (${fPct(L.chg_pct)})</span></div>
        <div class="kv"><span class="k">Bileşenlerden hesaplanan</span><span class="v ${cls(M.pts)}">${fPts(M.pts)} p (${fPct(M.pct, 2)})</span></div>
        <div class="kv"><span class="k">Artıranların katkısı</span><span class="v pos">${fPts(M.pos_pts)} p</span></div>
        <div class="kv"><span class="k">Düşürenlerin katkısı</span><span class="v neg">${fPts(M.neg_pts)} p</span></div>
        <div class="kv"><span class="k">Yükselen / Düşen / Sabit</span><span class="v"><b class="pos">${B.up ?? "—"}</b> / <b class="neg">${B.down ?? "—"}</b> / ${B.flat ?? "—"}</span></div>
        ${expl || `<div class="kv"><span class="k">Bileşen sayısı</span><span class="v">${d.count}</span></div>`}
      </div>
      <div class="src-note">Endeks seviyesi: ${lvlSrc}${L.source !== "idealdata" && isNum(L.estimated_last) ? ` · bileşenlerden tahmini seviye ~${fN(L.estimated_last, 2)}` : ""}</div>`;
    // bars: top 8 pushers & pullers by points (or % katkı when no level)
    const key = rowsHavePts(d) ? "pts" : "ip";
    $("ix-bars-unit").textContent = key === "pts" ? "endeks puanı" : "endeks % puanı";
    const valid = d.rows.filter((r) => isNum(r[key]));
    const up = [...valid].filter((r) => r[key] > 0).sort((a, b) => b[key] - a[key]).slice(0, 8);
    const dn = [...valid].filter((r) => r[key] < 0).sort((a, b) => a[key] - b[key]).slice(0, 8);
    const mx = Math.max(1e-9, ...up.map((r) => Math.abs(r[key])), ...dn.map((r) => Math.abs(r[key])));
    const bar = (r) => `<div class="ixb" data-sym="${esc(r.s)}"><span class="ixb-s">${esc(r.s)}</span><span class="ixb-t"><i class="${r[key] > 0 ? "up" : "dn"}" style="width:${(Math.abs(r[key]) / mx * 100).toFixed(1)}%"></i></span><span class="ixb-v ${cls(r[key])}">${fPts(r[key], key === "pts" ? 2 : 3)}</span><span class="ixb-c ${cls(r.c)}">${fPct(r.c)}</span></div>`;
    $("ix-bars").innerHTML = `<div class="ixb-col"><div class="ixb-h pos">▲ ENDEKSİ YUKARI ÇEKENLER</div>${up.map(bar).join("") || '<div class="empty">—</div>'}</div>
      <div class="ixb-col"><div class="ixb-h neg">▼ ENDEKSİ AŞAĞI ÇEKENLER</div>${dn.map(bar).join("") || '<div class="empty">—</div>'}</div>`;
    renderIxTable();
    const est = d.weight_source === "tahmini";
    $("ix-note").innerHTML = `${esc(d.note || "")} Puan etkisi = önceki kapanış × ağırlık × hissenin günlük getirisi. ${est ? "<b class='warn'>Tahmini ağırlıklı satırlar ~ ile işaretlidir.</b> " : ""}· ${esc(String(d.updated || "").slice(11))}`;
    renderIxQuick();
  }
  function rowsHavePts(d) { return d.rows.some((r) => isNum(r.pts)); }
  function renderIxTable() {
    const d = ix.data; if (!d) return;
    const est = d.weight_source === "tahmini";
    let rows = d.rows || [];
    const qv = fold(ix.q.trim());
    if (qv) rows = rows.filter((r) => r.s.includes(qv) || fold(r.n || "").includes(qv));
    if (ix.f === "up") rows = rows.filter((r) => isNum(r.ip) && r.ip > 0);
    else if (ix.f === "down") rows = rows.filter((r) => isNum(r.ip) && r.ip < 0);
    const k = ix.sort === "pts" && !rowsHavePts(d) ? "ip" : ix.sort, dir = ix.dir;
    rows = [...rows].sort((a, b) => {
      if (k === "s") return dir * a.s.localeCompare(b.s);
      const va = a[k], vb = b[k];
      if (!isNum(va) && !isNum(vb)) return 0; if (!isNum(va)) return 1; if (!isNum(vb)) return -1;
      return dir * (va - vb);
    });
    document.querySelectorAll("#ix-table th").forEach((th) => { th.classList.toggle("sorted", th.dataset.k === ix.sort); th.classList.toggle("asc", th.dataset.k === ix.sort && dir > 0); });
    const wmax = Math.max(1e-9, ...(d.rows || []).map((r) => r.w || 0));
    const show = rows.slice(0, ix.n);
    $("ix-body").innerHTML = show.map((r) => `<tr><td class="l sticky sym" data-sym="${esc(r.s)}">${esc(r.s)}${est ? '<sup class="ix-est" title="Tahmini ağırlık">~</sup>' : ""}</td>
      <td><span class="ix-w"><i style="width:${(r.w / wmax * 100).toFixed(0)}%"></i></span>${est ? "~" : ""}%${fN(r.w, 2)}</td>
      <td>${fP(r.p)}</td><td class="${cls(r.c)}">${fPct(r.c)}</td>
      <td class="${cls(r.pts)} b">${fPts(r.pts)}</td><td class="${cls(r.ip)}">${fPts(r.ip, 3)}</td>
      <td class="${cls(r.sh)}">${isNum(r.sh) ? (r.sh < 0 ? "-%" : "%") + fN(Math.abs(r.sh), 1) : "—"}</td><td>${fShort(r.t)}</td></tr>`).join("") || `<tr><td colspan="8" class="empty">${d.weight_source === "yok" ? esc(d.note) : "Sonuç yok"}</td></tr>`;
    $("ix-more").hidden = rows.length <= ix.n;
    $("ix-more").textContent = `Daha fazla göster (+${fN(rows.length - ix.n)})`;
  }
  document.querySelectorAll("#ix-table th").forEach((th) => th.addEventListener("click", () => {
    if (ix.sort === th.dataset.k) ix.dir *= -1; else { ix.sort = th.dataset.k; ix.dir = th.dataset.k === "s" ? 1 : -1; }
    renderIxTable();
  }));
  document.querySelectorAll("#ix-filter button").forEach((b) => b.addEventListener("click", () => {
    ix.f = b.dataset.f; document.querySelectorAll("#ix-filter button").forEach((x) => x.classList.toggle("active", x === b));
    if (ix.f === "down" && ix.sort === "pts") ix.dir = 1; else if (ix.f === "up" && ix.sort === "pts") ix.dir = -1;
    renderIxTable();
  }));
  $("ix-search").addEventListener("input", (e) => { ix.q = e.target.value; renderIxTable(); });
  $("ix-more").addEventListener("click", () => { ix.n += 300; renderIxTable(); });
  $("ix-body").addEventListener("click", (e) => { const t = e.target.closest("[data-sym]"); if (t) openStock(t.dataset.sym); });
  $("ix-bars").addEventListener("click", (e) => { const t = e.target.closest("[data-sym]"); if (t) openStock(t.dataset.sym); });
  $("ix-code").textContent = ix.code;

  // --------------------------------------------------------- KURUM ANALİZİ
  const kr = { mode: LS.get("kr_mode", "all"), broker: LS.get("kr_broker", ""), q: "", side: "", sort: "bl", dir: "desc",
    rows: [], total: 0, totals: null, loading: false, brokers: null, PAGE: 200, meta: null };
  async function loadKurumBrokers() {
    if (kr.brokers && Date.now() - kr.brokersTs < 60000) return;
    try {
      const d = await api("/api/live/brokers", { timeout: 20000 });
      kr.brokers = d.brokers || []; kr.brokersTs = Date.now(); kr.meta = d;
      const sel = $("kr-broker");
      sel.innerHTML = `<option value="">Kurum seçin… (${fN(kr.brokers.length)})</option>` +
        kr.brokers.map((b) => `<option value="${esc(b.b)}">${esc(brName(b.b))} · ${fN(b.n)} hisse</option>`).join("");
      sel.value = kr.broker || "";
      if (kr.mode === "one" && !kr.broker && kr.brokers.length) { kr.broker = kr.brokers[0].b; sel.value = kr.broker; loadKurum(true); }
    } catch (e) {}
  }
  function krHead() {
    const one = kr.mode === "one";
    const cols = (one ? [] : [["b", "KURUM", "l sticky"]]).concat([["s", "HİSSE", one ? "l sticky" : "l"], ["bl", "ALIŞ LOT"], ["bp", "ALIŞ %"], ["sl", "SATIŞ LOT"], ["sp", "SATIŞ %"],
      ["nl", "NET LOT"], ["np", "NET %"], ["co", "MALİYET"], ["p", "SON"], ["kz", "K/Z ₺"], ["kzp", "K/Z %"]]);
    $("kr-table").querySelector("thead").innerHTML = "<tr>" + cols.map(([k, t, c]) => `<th data-k="${k}" class="${c || ""}${kr.sort === k ? " sorted" + (kr.dir === "asc" ? " asc" : "") : ""}">${t}</th>`).join("") + "</tr>";
    $("kr-table").querySelectorAll("th").forEach((th) => th.addEventListener("click", () => {
      if (kr.sort === th.dataset.k) kr.dir = kr.dir === "desc" ? "asc" : "desc"; else { kr.sort = th.dataset.k; kr.dir = ["s", "b"].includes(th.dataset.k) ? "asc" : "desc"; }
      loadKurum(true);
    }));
    return cols.length;
  }
  function krRow(r) {
    const one = kr.mode === "one";
    return `<tr>${one ? "" : `<td class="l sticky kn" data-broker="${esc(r.b)}" title="${esc(brName(r.b))}">${esc(brName(r.b))}</td>`}
      <td class="l ${one ? "sticky " : ""}sym" data-sym="${esc(r.s)}">${esc(r.s)}</td>
      <td class="pos">${fN(r.bl)}</td><td class="pos">${isNum(r.bp) ? "%" + nf(1).format(r.bp) : "—"}</td><td class="neg">${fN(r.sl)}</td><td class="neg">${isNum(r.sp) ? "%" + nf(1).format(r.sp) : "—"}</td>
      <td class="${cls(r.nl)}">${fN(r.nl)}</td><td class="${cls(r.np)}">${isNum(r.np) && r.np ? (r.np > 0 ? "+" : "−") + "%" + nf(1).format(Math.abs(r.np)) : "—"}</td><td>${fP(r.co)}</td><td>${fP(r.p)}</td><td class="${cls(r.kz)}">${isNum(r.kz) ? fShort(r.kz) : "—"}</td><td class="${cls(r.kzp)}">${fPct(r.kzp)}</td></tr>`;
  }
  function akdBadgeHtml(a) {
    if (!a) return "";
    const pct = a.total ? Math.round((a.have / a.total) * 100) : 0;
    return a.complete
      ? `<span class="kr-akd-ok">AKD ${fmtYmd(a.date)} · ${fN(a.have)}/${fN(a.total)} hisse yüklü${a.checked > a.have ? ` (${fN(a.checked - a.have)} hissede işlem yok)` : ""}${a.oldest_age_sec != null ? ` · en eski ${a.oldest_age_sec < 120 ? a.oldest_age_sec + " sn" : Math.round(a.oldest_age_sec / 60) + " dk"}` : ""}</span>`
      : `<span class="kr-akd-load"><i style="width:${pct}%"></i><b>AKD yükleniyor: ${fN(a.have)}/${fN(a.total)}</b></span>`;
  }
  function krAkdBadge(a, id) {
    const el = $(id || "kr-akd"); if (el) el.innerHTML = akdBadgeHtml(a);
  }
  async function loadKurum(reset, more) {
    if (kr.loading && !reset) return;
    const one = kr.mode === "one";
    document.querySelectorAll("#kr-mode button").forEach((b) => b.classList.toggle("active", b.dataset.mode === kr.mode));
    $("kr-broker").hidden = !one;
    $("kr-search").placeholder = one ? "Hisse ara..." : "Hisse veya kurum ara...";
    if (one && !kr.broker) { $("kr-body").innerHTML = `<tr><td colspan="12" class="empty">Kurum seçin</td></tr>`; $("kr-sum").hidden = true; $("kr-foot").innerHTML = ""; krHead(); return; }
    kr.loading = true;
    const ncol = krHead();
    const p = new URLSearchParams({ sort: kr.sort, dir: kr.dir, offset: String(more ? kr.rows.length : 0), limit: String(kr.PAGE) });
    if (one) p.set("broker", kr.broker);
    if (kr.q) p.set("q", kr.q);
    if (kr.side) p.set("side", kr.side);
    try {
      const d = await api("/api/live/brokers/matrix?" + p.toString(), { timeout: 20000 });
      kr.rows = more ? kr.rows.concat(d.rows) : d.rows; kr.total = d.total; kr.totals = d.totals;
      const body = $("kr-body");
      if (more) body.insertAdjacentHTML("beforeend", d.rows.map(krRow).join(""));
      else body.innerHTML = d.rows.map(krRow).join("") || `<tr><td colspan="${ncol}" class="empty">${d.stocks_akd ? "Sonuç yok" + (d.akd_status && !d.akd_status.complete ? ` · AKD yükleniyor: ${fN(d.akd_status.have)}/${fN(d.akd_status.total)}` : "") : `AKD yükleniyor: ${fN((d.akd_status || {}).have || 0)}/${fN((d.akd_status || {}).total || 0)}`}</td></tr>`;
      $("kr-more").hidden = kr.rows.length >= kr.total;
      $("kr-more").textContent = `Daha fazla göster (${fN(kr.rows.length)} / ${fN(kr.total)})`;
      const t = d.totals || {};
      const showFoot = one || kr.q || kr.side;
      $("kr-foot").innerHTML = showFoot ? `<tr>${one ? "" : '<td class="l sticky">TOPLAM</td>'}<td class="l ${one ? "sticky" : ""}">${one ? "TOPLAM" : ""} ${fN(d.total)} satır</td>
        <td class="pos">${fShort(t.bl)}</td><td></td><td class="neg">${fShort(t.sl)}</td><td></td><td class="${cls(t.nl)}">${fShort(t.nl)}</td><td></td><td></td><td></td>
        <td class="${cls(t.kz)}">${fShort(t.kz)}</td><td class="${cls(t.kzp)}">${fPct(t.kzp)}</td></tr>` : "";
      if (one) {
        $("kr-sum").hidden = false;
        $("kr-sum").innerHTML = `<div class="ks"><span class="k">HİSSE</span><span class="v">${fN(d.total)}</span></div>
          <div class="ks"><span class="k">ALIŞ (₺)</span><span class="v pos">${fShort(t.btl)}</span></div>
          <div class="ks"><span class="k">SATIŞ (₺)</span><span class="v neg">${fShort(t.stl)}</span></div>
          <div class="ks"><span class="k">NET POZİSYON (₺)</span><span class="v ${cls(t.ntl)}">${fShort(t.ntl)}</span></div>
          <div class="ks"><span class="k">ANLIK K/Z (₺)</span><span class="v ${cls(t.kz)}">${fShort(t.kz)}</span></div>
          <div class="ks"><span class="k">K/Z %</span><span class="v ${cls(t.kzp)}">${fPct(t.kzp)}</span></div>`;
      } else $("kr-sum").hidden = true;
      krAkdBadge(d.akd_status);
      $("kr-note").textContent = `Kaynak: yalnızca günlük AKD (İdealData, ${fmtYmd(d.akd_date)}) — hisse AKD sekmesi "Günlük" ile aynı istek ve aynı kayıt; AKD'si henüz yüklenmemiş hisse listelenmez · ${fN(d.stocks_akd)} hisse · Alış % / Satış % = AKD sekmesindeki ALICILAR / SATICILAR DAĞILIM % (net lot / o hissenin tüm net alıcılarının ya da net satıcılarının net lot toplamı) · Net % = +alış % / −satış % · Alış/Satış lot = AKD TOPLAM alış/satış · Maliyet = net pozisyon ortalaması · K/Z = net lot × (son − maliyet)`;
    } catch (e) {
      if (!kr.rows.length) $("kr-body").innerHTML = `<tr><td colspan="12" class="empty">Veri alınamadı (${esc(e.message || e)})</td></tr>`;
    } finally { kr.loading = false; }
  }
  document.querySelectorAll("#kr-mode button").forEach((b) => b.addEventListener("click", () => {
    kr.mode = b.dataset.mode; LS.set("kr_mode", kr.mode);
    if (kr.mode === "one" && !kr.broker && kr.brokers && kr.brokers.length) { kr.broker = kr.brokers[0].b; $("kr-broker").value = kr.broker; }
    loadKurum(true);
  }));
  $("kr-broker").addEventListener("change", (e) => { kr.broker = e.target.value; LS.set("kr_broker", kr.broker); loadKurum(true); });
  let krT = null;
  $("kr-search").addEventListener("input", (e) => { clearTimeout(krT); krT = setTimeout(() => { kr.q = e.target.value.trim(); loadKurum(true); }, 300); });
  document.querySelectorAll("#kr-side button").forEach((b) => b.addEventListener("click", () => {
    kr.side = b.dataset.s; document.querySelectorAll("#kr-side button").forEach((x) => x.classList.toggle("active", x === b)); loadKurum(true);
  }));
  $("kr-more").addEventListener("click", () => loadKurum(false, true));
  $("kr-body").addEventListener("click", (e) => {
    const b = e.target.closest("[data-broker]");
    if (b) { kr.mode = "one"; kr.broker = b.dataset.broker; LS.set("kr_mode", "one"); LS.set("kr_broker", kr.broker); $("kr-broker").value = kr.broker; loadKurum(true); window.scrollTo(0, 0); return; }
    const s = e.target.closest("[data-sym]"); if (s) openStock(s.dataset.sym);
  });

  // ------------------------------------------------------------- FAVORİLER
  st.fvList = "fav";
  function renderFavs() {
    document.querySelectorAll("#fv-seg button").forEach((b) => b.classList.toggle("active", b.dataset.l === st.fvList));
    const syms = st.fvList === "fav" ? st.favs : st.recent;
    const by = new Map(((st.movers && st.movers.rows) || []).map((r) => [r.s, r]));
    const el = $("fv-list");
    if (!syms.length) { el.innerHTML = `<div class="empty">${st.fvList === "fav" ? "Favori yok — hisse kartındaki ☆ ile ekleyin" : "Henüz hisse görüntülenmedi"}</div>`; return; }
    el.innerHTML = syms.map((s, i) => { const r = by.get(s) || { s }; return `<div class="mv-row" data-sym="${esc(s)}"><span class="mv-rank">${i + 1}</span>${logoSpan(s)}
      <div class="mv-mid"><div class="mv-sym">${esc(s)}</div><div class="mv-px">${esc(r.n || nameOf(s) || "")}</div></div>
      <div class="mv-tl">${fP(r.p)} ₺<small>${fShort(r.t)} ₺ hacim</small></div><span class="mv-pill ${cls(r.c)}">${fPct(r.c)}</span></div>`; }).join("");
    lazyLogos2(el);
  }
  document.querySelectorAll("#fv-seg button").forEach((b) => b.addEventListener("click", () => { st.fvList = b.dataset.l; renderFavs(); }));

  // ===================================================================== v1.20.0 ==
  // ---- istemci kimliği + sunucu taraflı uyarı ayarları (arka planda push için sunucuda saklanır)
  const CID = (() => { let c = LS.get("cid", ""); if (!c) { c = "c" + Math.random().toString(36).slice(2) + Date.now().toString(36); LS.set("cid", c); } return c; })();
  const AL = { cfg: null, since: 0, primed: false, push: false, events: [], saving: null };
  async function loadCfg() {
    try { const d = await api(`/api/alerts/config?cid=${CID}`, { timeout: 10000 }); AL.cfg = d.cfg; AL.push = !!d.push; syncNPFromServer(); } catch (e) {}
    if (AL.cfg && JSON.stringify(AL.cfg.favs || []) !== JSON.stringify(st.favs || [])) saveCfg({ favs: st.favs || [] });
    return AL.cfg;
  }
  async function saveCfg(part) {
    try {
      const d = await api("/api/alerts/config", { method: "POST", body: JSON.stringify({ cid: CID, cfg: part }), headers: { "Content-Type": "application/json" }, timeout: 10000 });
      AL.cfg = d.cfg; return true;
    } catch (e) { toast("Ayar kaydedilemedi"); return false; }
  }
  // ---- ses
  let actx = null;
  function beep(kind) {
    if (AL.cfg && AL.cfg.sound === false) return;
    try {
      actx = actx || new (window.AudioContext || window.webkitAudioContext)();
      const seq = kind === "up" ? [660, 880, 1100] : kind === "down" ? [700, 520, 390] : [880, 880];
      seq.forEach((fq, i) => {
        const o = actx.createOscillator(), g = actx.createGain();
        o.type = "sine"; o.frequency.value = fq; o.connect(g); g.connect(actx.destination);
        const t0 = actx.currentTime + i * 0.13; g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(0.25, t0 + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.12);
        o.start(t0); o.stop(t0 + 0.13);
      });
    } catch (e) {}
  }
  document.addEventListener("click", () => { try { if (actx && actx.state === "suspended") actx.resume(); } catch (e) {} }, { passive: true });
  function evDir(e) { return ["tavanda", "yaklasan", "taban_donen", "buy"].includes(e.sub) ? "up" : ["tabanda", "taban_yaklasan", "eriyen", "cozuldu", "sell"].includes(e.sub) ? "down" : "info"; }
  function sysNotify(e) {
    if (!("Notification" in window) || Notification.permission !== "granted") return;
    if (AL.push && document.hidden) return;   // push zaten gösterir
    const opts = { type: "SHOW_NOTIFICATION", title: e.title, body: e.text, tag: `${e.kind}-${e.sym || ""}-${e.id}`, symbol: e.sym, vibrate: [120, 60, 120] };
    if (navigator.serviceWorker && navigator.serviceWorker.controller) navigator.serviceWorker.controller.postMessage(opts);
    else try { new Notification(e.title, { body: e.text }); } catch (x) {}
  }
  async function pollAlerts() {
    try {
      const d = await api(`/api/alerts/feed?cid=${CID}&since=${AL.since}&visible=${document.hidden ? 0 : 1}&limit=300`, { timeout: 10000 });
      AL.push = !!d.push;
      const evs = d.events || [];
      if (AL.primed) {
        const kb = (AL.cfg && AL.cfg.kurum && AL.cfg.kurum.brokers) || [];
        const fresh = evs.filter((e) => !e.backfill && !(e.kind === "kurum" && !kb.length));
        deliver(fresh);   // v1.20.1: üst bant + geçmiş + tür bazlı mod/ses
      }
      AL.events = [...AL.events, ...evs].slice(-3000);
      AL.since = d.last_id || AL.since; AL.primed = true;
      if (["tavan", "agresif", "kurumuyari"].includes(st.view)) renderAlertFeeds();
    } catch (e) {}
  }
  setInterval(() => pollAlerts(), 3000);
  // ---- Web Push
  function b64u(s) { const p = "=".repeat((4 - (s.length % 4)) % 4); const b = atob((s + p).replace(/-/g, "+").replace(/_/g, "/")); return Uint8Array.from([...b].map((c) => c.charCodeAt(0))); }
  // v1.22.4 — APK WebView'de Notification/PushManager yok → arka plan bildirimi OneSignal (APK) ile
  function noWebPush() { return !("Notification" in window) || !("serviceWorker" in navigator) || !("PushManager" in window); }
  function osActive() {   // v1.38.0: Telegram ayarlı mı (OneSignal kaldırıldı)
    const O = typeof OS !== "undefined" && OS ? OS : null, c = O && O.cfg;
    return !!(c && c.ready);
  }
  const FEAT_L = { tavan: "Tavan / Taban", agresif: "Agresif Alım-Satım", kurumuyari: "Kurum Uyarıları", bildirim: "Bildirimler" };
  function featTitle() { if (st.view === "op") { const t = $("op-title"); return (t && t.textContent) || "Tarayıcı"; } return FEAT_L[st.view] || "Bildirimler"; }
  async function osFeatureTest(feat) {
    try {
      const r = await api("/api/telegram/test", { method: "POST", body: JSON.stringify({ cid: CID, feature: feat || featTitle() }), headers: { "Content-Type": "application/json" } });
      toast(r.ok ? `Telegram test mesajı gönderildi ✓${r.dry ? " (deneme modu)" : ""}` : "Gönderilemedi: " + (r.error || "") + " — Telegram Bildirim Ayarları", 4500);
      return r;
    } catch (e) { toast("Test başarısız"); return null; }
  }
  async function enablePush() {
    try {
      if (noWebPush() && osActive()) { toast("Arka plan bildirimi Telegram üzerinden açık ✓"); osRegisterIfApk(); return true; }
      if (!("Notification" in window) || !("serviceWorker" in navigator)) { toast("Bu ortamda tarayıcı push'u yok — arka plan bildirimleri için Telegram Bildirim Ayarları", 4500); return false; }
      const perm = await Notification.requestPermission();
      if (perm !== "granted") { toast("Bildirim izni verilmedi"); return false; }
      const k = await api("/api/push/key", { timeout: 8000 });
      const reg = await navigator.serviceWorker.ready;
      if (!k.key || !reg.pushManager) { toast("Web Push desteklenmiyor — uygulama açıkken bildirim gelir"); return false; }
      let sub = await reg.pushManager.getSubscription();
      if (!sub) sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64u(k.key) });
      await api("/api/push/subscribe", { method: "POST", body: JSON.stringify({ cid: CID, subscription: sub.toJSON() }), headers: { "Content-Type": "application/json" } });
      AL.push = true; toast("Arka plan bildirimleri açık ✓"); return true;
    } catch (e) { toast("Push açılamadı: " + (e.message || e)); return false; }
  }
  async function testPush(feat) {
    if (osActive() && (noWebPush() || !AL.push)) return osFeatureTest(feat);
    try { const r = await api("/api/push/test", { method: "POST", body: JSON.stringify({ cid: CID }), headers: { "Content-Type": "application/json" } }); toast(r.ok ? "Test bildirimi gönderildi" : r.error); } catch (e) { toast("Test başarısız"); }
  }
  const pushRow = (feat) => {
    const osOn = osActive(), nw = noWebPush(), f = esc(feat || featTitle());
    const lbl = osOn && (nw || !AL.push) ? "🟢 Arka plan bildirimi: Telegram açık" : AL.push ? `🟢 Arka plan bildirimi (Web Push) açık${osOn ? " · Telegram açık" : ""}` : "⚪ Arka plan bildirimi kapalı";
    const btns = osOn && nw ? `<button type="button" class="btn-ghost" data-push="test" data-feat="${f}">Test</button>`
      : `<button type="button" class="btn-ghost" data-push="on">${AL.push ? "Yenile" : "Aç"}</button>${AL.push || osOn ? `<button type="button" class="btn-ghost" data-push="test" data-feat="${f}">Test</button>` : ""}`;
    return `<div class="al-push" data-pushrow="1"><span>${lbl}</span>
    ${btns}
    <label class="al-chk"><input type="checkbox" data-sound="1" ${AL.cfg && AL.cfg.sound === false ? "" : "checked"}/> Ses</label></div>`; };
  document.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-push]"); if (b) { if (b.dataset.push === "test") testPush(b.dataset.feat); else { await enablePush(); rerenderSettings(); } }
  });
  document.addEventListener("change", (e) => { const c = e.target.closest("[data-sound]"); if (c) saveCfg({ sound: c.checked }); });
  function rerenderSettings() { if (st.view === "tavan") renderTTSet(); else if (st.view === "agresif") renderAgSet(); else if (st.view === "kurumuyari") renderKuSet(); else if (st.view === "bildirim" && nfs.tab === "ayar") renderNfAyar(); }
  const scopeSel = (sec, cfg) => `<div class="al-row"><span class="k">Kapsam</span><div class="seg sm" data-scope="${sec}">
      ${[["all", "TÜM HİSSELER"], ["fav", "FAVORİLER"], ["sel", "SEÇİLİ"]].map(([v, l]) => `<button type="button" data-v="${v}" class="${cfg.scope === v ? "active" : ""}">${l}</button>`).join("")}</div></div>
    <div class="al-row" ${cfg.scope === "sel" ? "" : "hidden"}><span class="k">Seçili hisseler</span><input type="text" class="al-in wide" data-syms="${sec}" value="${esc((cfg.syms || []).join(", "))}" placeholder="THYAO, ASELS, ..."/></div>`;
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-scope] button"); if (!b) return;
    const sec = b.closest("[data-scope]").dataset.scope;
    saveCfg({ [sec]: { scope: b.dataset.v } }).then(rerenderSettings);
  });
  document.addEventListener("change", (e) => {
    const i = e.target.closest("[data-syms]"); if (!i) return;
    const syms = i.value.split(/[\s,;]+/).map((x) => fold(x)).filter(Boolean);
    saveCfg({ [i.dataset.syms]: { syms } }).then(() => toast(`${syms.length} hisse kaydedildi`));
  });
  const fT = (v) => (isNum(v) ? fShort(v) + " ₺" : "—");
  const SUBL = { yaklasan: "TAVANA YAKLAŞAN", tavanda: "TAVANDA", eriyen: "TAVAN ERİYOR", cozuldu: "TAVANDAN ÇÖZÜLDÜ", taban_yaklasan: "TABANA YAKLAŞAN", tabanda: "TABANDA", taban_donen: "TABANDAN DÖNEN", buy: "ALIM", sell: "SATIŞ", gun_sonu: "RAPOR" };
  function evRow(e) {
    const dir = evDir(e);
    return `<div class="al-ev ${dir}" ${e.sym ? `data-sym="${esc(e.sym)}"` : ""}><span class="al-t">${esc(e.time)}</span>
      <div class="al-m"><div class="al-h"><b>${esc(e.sym || "")}</b> <span class="al-tag ${dir}">${esc(SUBL[e.sub] || e.sub)}</span>${e.backfill ? '<span class="al-tag gray">GEÇMİŞ</span>' : ""}</div><div class="al-x">${esc(e.text)}</div></div></div>`;
  }
  function renderAlertFeeds() {
    if (st.view === "tavan") {
      const ev = AL.events.filter((e) => e.kind === "tavan").slice(-150).reverse();
      $("tt-evn").textContent = `${ev.length} olay`;
      $("tt-feed").innerHTML = ev.map(evRow).join("") || `<div class="empty">Henüz olay yok — eşik aşıldığında burada ve bildirim olarak görünür</div>`;
    } else if (st.view === "kurumuyari" && ku.tab === "feed") {
      const ev = AL.events.filter((e) => e.kind === "kurum" || e.kind === "rapor").slice(-300).reverse();
      $("ku-evn").textContent = `${ev.length} uyarı`;
      $("ku-feed").innerHTML = ev.map(evRow).join("") || `<div class="empty">${(AL.cfg && AL.cfg.kurum.brokers.length) ? "Seçili kurumlar için eşik üstü agresif işlem yok" : "Kurum seçin — liste boşken tüm kurumlar gösterilir, bildirim yalnızca seçili kurumlar için gelir"}</div>`;
    }
  }
  ["tt-feed", "ku-feed"].forEach((id) => $(id).addEventListener("click", (e) => { const r = e.target.closest("[data-sym]"); if (r) openStock(r.dataset.sym); }));

  // ---------------------------------------------------------- PİYASA RADARI
  const rd = { k: "all", sort: LS.get("rd_sort", "chg_desc"), q: "", n: 120, data: null, peerSym: null, peerMode: "t", peers: null };
  const RD_SORT = { chg_desc: "Değişim % — yüksekten düşüğe", chg_asc: "Değişim % — düşükten yükseğe", vol_desc: "İşlem hacmi (TL) — en yüksek", ceil: "Tavana yakınlık", alpha: "Alfabetik (A → Z)" };
  const RD_NEAR = 3.0;
  async function loadRadar() {
    try { rd.data = await api("/api/radar", { timeout: 15000 }); renderRadar(); }
    catch (e) { if (!rd.data) $("rd-list").innerHTML = `<div class="empty">Veri alınamadı (${esc(e.message || e)})</div>`; }
  }
  function rdFilter(rows, k) {
    if (k === "up") return rows.filter((r) => r.c > 0);
    if (k === "down") return rows.filter((r) => r.c < 0);
    if (k === "ceil") return rows.filter((r) => isNum(r.dc) && r.dc <= RD_NEAR && r.c > 0);
    if (k === "floor") return rows.filter((r) => isNum(r.df) && r.df <= RD_NEAR && r.c < 0);
    return rows;
  }
  function rdRow(r) {
    const nm = r.n || nameOf(r.s) || "";
    const tag = isNum(r.dc) && r.dc <= 0.001 ? '<span class="rd-tag up">TAVAN</span>' : isNum(r.df) && r.df <= 0.001 ? '<span class="rd-tag dn">TABAN</span>'
      : rd.k === "ceil" && isNum(r.dc) ? `<span class="rd-tag up">tavana %${fN(r.dc, 2)}</span>` : rd.k === "floor" && isNum(r.df) ? `<span class="rd-tag dn">tabana %${fN(r.df, 2)}</span>` : "";
    return `<div class="mv-row rd-row" data-sym="${esc(r.s)}">${logoSpan(r.s)}
      <div class="mv-mid"><div class="mv-sym">${esc(r.s)} ${tag}</div><div class="mv-px rd-nm">${esc(nm)}</div></div>
      <div class="mv-tl">${fP(r.p)} ₺<small>${fShort(r.t)} ₺</small></div><span class="mv-pill ${cls(r.c)}">${fPct(r.c)}</span>
      <button type="button" class="rd-mag" data-peer="${esc(r.s)}" aria-label="Rakipler"><svg viewBox="0 0 24 24" width="17" height="17"><circle cx="10.5" cy="10.5" r="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15 15l5 5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg></button></div>`;
  }
  function renderRadar() {
    const d = rd.data; if (!d) return;
    let rows = d.rows || [];
    const counts = { all: rows.length, up: rdFilter(rows, "up").length, down: rdFilter(rows, "down").length, ceil: rdFilter(rows, "ceil").length, floor: rdFilter(rows, "floor").length };
    document.querySelectorAll("#rd-chips button").forEach((b) => { b.classList.toggle("active", b.dataset.k === rd.k); b.querySelector("b").textContent = counts[b.dataset.k]; });
    rows = rdFilter(rows, rd.k);
    const qv = fold(rd.q.trim());
    if (qv) rows = rows.filter((r) => r.s.includes(qv) || fold(r.n || nameOf(r.s) || "").includes(qv));
    const S = rd.sort;
    rows = [...rows].sort((a, b) => S === "chg_asc" ? (a.c ?? 0) - (b.c ?? 0) : S === "vol_desc" ? (b.t || 0) - (a.t || 0) : S === "ceil" ? (a.dc ?? 99) - (b.dc ?? 99) : S === "alpha" ? a.s.localeCompare(b.s) : (b.c ?? 0) - (a.c ?? 0));
    $("rd-sortlbl").textContent = `Sıralama: ${RD_SORT[S]} · ${rows.length} hisse${rd.k === "ceil" || rd.k === "floor" ? ` · yakınlık eşiği %${RD_NEAR}` : ""}`;
    $("rd-list").innerHTML = rows.slice(0, rd.n).map(rdRow).join("") || `<div class="empty">Sonuç yok</div>`;
    lazyLogos2($("rd-list"));
    $("rd-more").hidden = rows.length <= rd.n; $("rd-more").textContent = `Daha fazla göster (+${fN(rows.length - rd.n)})`;
    $("rd-note").textContent = `İdealData canlı · ${fN(d.count)} pay · sektör: ${d.sector_source} · ${String(d.updated || "").slice(11)}`;
  }
  document.querySelectorAll("#rd-chips button").forEach((b) => b.addEventListener("click", () => { rd.k = b.dataset.k; rd.n = 120; if (rd.k === "ceil" && rd.sort === "chg_desc") rd.sort = "ceil"; renderRadar(); try { b.scrollIntoView({ block: "nearest", inline: "center" }); } catch (x) {} }));
  $("rd-search").addEventListener("input", (e) => { rd.q = e.target.value; renderRadar(); });
  $("rd-more").addEventListener("click", () => { rd.n += 200; renderRadar(); });
  $("rd-sort-btn").addEventListener("click", () => { document.querySelectorAll("#rd-sort-list li").forEach((li) => li.classList.toggle("active", li.dataset.sort === rd.sort)); $("rd-sort-sheet").hidden = false; });
  $("rd-sort-list").addEventListener("click", (e) => { const li = e.target.closest("[data-sort]"); if (!li) return; rd.sort = li.dataset.sort; LS.set("rd_sort", rd.sort); $("rd-sort-sheet").hidden = true; renderRadar(); });
  $("rd-list").addEventListener("click", (e) => {
    const m = e.target.closest("[data-peer]"); if (m) { e.stopPropagation(); openPeers(m.dataset.peer); return; }
    const r = e.target.closest("[data-sym]"); if (r) openStock(r.dataset.sym);
  });
  async function openPeers(sym) {
    rd.peerSym = sym; $("rd-peer-sheet").hidden = false; $("rp-list").innerHTML = `<div class="empty">Yükleniyor…</div>`; $("rp-sub").textContent = sym;
    try { rd.peers = await api(`/api/radar/peers/${encodeURIComponent(sym)}`, { timeout: 10000 }); renderPeers(); }
    catch (e) { $("rp-list").innerHTML = `<div class="empty">Veri alınamadı</div>`; }
  }
  function renderPeers() {
    const d = rd.peers; if (!d) return;
    document.querySelectorAll("#rp-mode button").forEach((b) => b.classList.toggle("active", b.dataset.m === rd.peerMode));
    $("rp-sub").textContent = d.sector ? `${d.symbol} · ${d.sector_name} sektörü (${d.sector}) · ${d.count} hisse` : `${d.symbol} · sektör bilgisi yok`;
    const k = rd.peerMode;
    const rows = [...(d.rows || [])].sort((a, b) => (k === "t" ? (b.t || 0) - (a.t || 0) : (b.c ?? -99) - (a.c ?? -99)));
    const mx = Math.max(1e-9, ...rows.map((r) => Math.abs(k === "t" ? r.t || 0 : r.c || 0)));
    $("rp-list").innerHTML = rows.map((r, i) => { const v = k === "t" ? r.t || 0 : r.c || 0;
      return `<div class="mv-row rp-row ${r.s === d.symbol ? "me" : ""}" data-sym="${esc(r.s)}"><span class="mv-rank">${i + 1}</span>${logoSpan(r.s)}
        <div class="mv-mid"><div class="mv-sym">${esc(r.s)}</div><div class="rp-bar"><i class="${k === "t" ? "vol" : v >= 0 ? "up" : "dn"}" style="width:${(Math.abs(v) / mx * 100).toFixed(1)}%"></i></div></div>
        <div class="mv-tl">${fP(r.p)} ₺<small>${fShort(r.t)} ₺</small></div><span class="mv-pill ${cls(r.c)}">${fPct(r.c)}</span></div>`; }).join("") || `<div class="empty">Bu sektörde başka hisse yok</div>`;
    lazyLogos2($("rp-list"));
  }
  document.querySelectorAll("#rp-mode button").forEach((b) => b.addEventListener("click", () => { rd.peerMode = b.dataset.m; renderPeers(); }));
  $("rp-list").addEventListener("click", (e) => { const r = e.target.closest("[data-sym]"); if (r) { $("rd-peer-sheet").hidden = true; openStock(r.dataset.sym); } });

  // ---------------------------------------------------------- TAVAN / TABAN
  const tt = { k: "tavan", data: null };
  async function loadTT() {
    const ap = (AL.cfg && AL.cfg.tavan.approach_pct) || 2;
    try { tt.data = await api(`/api/tavan-taban?approach=${ap}`, { timeout: 15000 }); renderTT(); } catch (e) {}
  }
  function renderTT() {
    const d = tt.data; if (!d) return;
    const rows = d.rows || [];
    document.querySelectorAll("#tt-chips button").forEach((b) => { b.classList.toggle("active", b.dataset.k === tt.k); b.querySelector("b").textContent = rows.filter((r) => r.st === b.dataset.k).length; });
    let r = rows.filter((x) => x.st === tt.k);
    r.sort((a, b) => tt.k.startsWith("tavan") ? (a.dc ?? 0) - (b.dc ?? 0) || (b.ceil_lot || 0) - (a.ceil_lot || 0) : (a.df ?? 0) - (b.df ?? 0) || (b.floor_lot || 0) - (a.floor_lot || 0));
    $("tt-body").innerHTML = r.map((x) => `<tr><td class="l sticky sym" data-sym="${esc(x.s)}">${esc(x.s)}</td><td>${fP(x.p)}</td><td class="${cls(x.c)}">${fPct(x.c)}</td>
      <td>${fP(x.ceil)}</td><td class="pos">${isNum(x.dc) ? "%" + fN(x.dc, 2) : "—"}</td><td>${fP(x.floor)}</td><td class="neg">${isNum(x.df) ? "%" + fN(x.df, 2) : "—"}</td>
      <td class="pos">${fN(x.ceil_lot)}</td><td class="neg">${fN(x.floor_lot)}</td><td>${fShort(x.t)}</td></tr>`).join("") || `<tr><td colspan="10" class="empty">Bu grupta hisse yok</td></tr>`;
    $("tt-note").textContent = `Yakınlık eşiği %${d.approach} · tavan alış lotu = tavan fiyatındaki alış kademesi (25 kademe derinlik) · ${d.updated}`;
  }
  document.querySelectorAll("#tt-chips button").forEach((b) => b.addEventListener("click", () => { tt.k = b.dataset.k; renderTT(); }));
  $("tt-body").addEventListener("click", (e) => { const t = e.target.closest("[data-sym]"); if (t) openStock(t.dataset.sym); });
  function renderTTSet() {
    const c = AL.cfg; if (!c) { $("tt-set").innerHTML = `<div class="empty">Ayarlar yükleniyor…</div>`; return; }
    const t = c.tavan, K = t.kinds || {};
    const kk = [["yaklasan", "Tavana yaklaşan"], ["tavanda", "Tavana oturan"], ["eriyen", "Tavan eriyen / çözülen"], ["taban_yaklasan", "Tabana yaklaşan"], ["tabanda", "Tabana oturan"], ["taban_donen", "Tabandan dönen"]];
    $("tt-set").innerHTML = `<div class="card-h"><span class="card-title">BİLDİRİM AYARLARI</span><button type="button" class="btn-ghost sm nf-lnk" data-nflink="ayar">🔔 Tüm bildirim ayarları</button></div>
      <div class="nm-mini">${["tavan_yaklasan", "tavan_kitlendi", "tavan_eriyen", "tavan_cozuldu", "taban_yaklasan", "taban_kitlendi", "taban_donen"].map((k) => ntRow(k, true)).join("")}</div>
      <div class="al-row"><span class="k">Tavana yaklaşma eşiği %</span><input type="number" class="al-in" id="tt-ap" step="0.1" min="0.1" max="10" value="${t.approach_pct}"/></div>
      <div class="al-row"><span class="k">Tabana yaklaşma eşiği %</span><input type="number" class="al-in" id="tt-fap" step="0.1" min="0.1" max="10" value="${t.floor_approach_pct}"/></div>
      <div class="al-row"><span class="k">Tavan erime: tavan alış lotu tepeden düşüş %</span><input type="number" class="al-in" id="tt-melt" step="5" min="5" max="95" value="${t.melt_pct}"/></div>
      ${scopeSel("tavan", t)}${pushRow("Tavan / Taban")}
      <div class="src-note">Tespit sunucuda her saniye yapılır; push açıksa tarayıcı kapalıyken de bildirim gelir.</div>`;
    [["tt-ap", "approach_pct"], ["tt-fap", "floor_approach_pct"], ["tt-melt", "melt_pct"]].forEach(([id, k]) => $(id).addEventListener("change", (e) => { const v = parseFloat(e.target.value); if (isNum(v)) saveCfg({ tavan: { [k]: v } }).then(() => { toast("Kaydedildi"); loadTT(); }); }));
  }

  // ---------------------------------------------------------- AGRESİF İŞLEM
  const ag = { data: null, ov: null };
  function agQuery() {
    const a = Object.assign({}, (AL.cfg && AL.cfg.agresif) || { side: "both", min_lot: 0, min_tl: 2e6, min_levels: 3, min_book_pct: 0, scope: "all", syms: [] }, ag.ov || {});   // v1.29.0 ag.ov = En İyi Koşul görünüm filtresi
    let syms = "";
    if (a.scope === "fav") syms = (st.favs || []).join(","); else if (a.scope === "sel") syms = (a.syms || []).join(",");
    return `side=${a.side}&min_lot=${a.min_lot || 0}&min_tl=${a.min_tl || 0}&min_levels=${a.min_levels || 1}&min_book_pct=${a.min_book_pct || 0}&limit=400${syms ? "&syms=" + encodeURIComponent(syms) : ""}`;
  }
  async function loadAg() {
    const a = AL.cfg && AL.cfg.agresif && Object.assign({}, AL.cfg.agresif, ag.ov || {});
    if (a && a.scope !== "all" && !(a.scope === "fav" ? st.favs.length : (a.syms || []).length)) { $("ag-body").innerHTML = `<tr><td colspan="10" class="empty">Kapsamda hisse yok — favori ekleyin veya hisse seçin</td></tr>`; return; }
    try { ag.data = await api(`/api/agresif?${agQuery()}`, { timeout: 15000 }); renderAg(); } catch (e) {}
  }
  function renderAg() {
    const d = ag.data; if (!d) return;
    const S = d.sum || {};
    $("ag-sum").innerHTML = `<div class="kv-grid">
      <div class="kv"><span class="k">Satış tarafı süpürme (alım)</span><span class="v pos">${fN(S.buy_n)} · ${fT(S.buy_tl)}</span></div>
      <div class="kv"><span class="k">Alış tarafı süpürme (satış)</span><span class="v neg">${fN(S.sell_n)} · ${fT(S.sell_tl)}</span></div>
      <div class="kv"><span class="k">Filtreye uyan</span><span class="v">${fN(d.count)}</span></div><div class="kv"><span class="k">Bugün toplam süpürme</span><span class="v">${fN(d.total)}</span></div></div>`;
    $("ag-body").innerHTML = (d.rows || []).map((r) => `<tr class="${r.live ? "" : "old"}"><td class="l sticky sym" data-sym="${esc(r.sym)}">${esc(r.sym)}</td><td class="l">${esc(r.time)}</td>
      <td class="${r.side === "buy" ? "pos" : "neg"} b">${r.side === "buy" ? "▲ ALIM" : "▼ SATIŞ"}</td><td class="b">${r.levels}</td><td>${fP(r.from)} → ${fP(r.to)}</td>
      <td>${fN(r.lot)}</td><td class="b">${fShort(r.tl)}</td><td>${isNum(r.book_pct) ? "%" + fN(r.book_pct, 0) : '<span class="muted">—</span>'}</td><td class="${cls(r.chg)}">${fPct(r.chg)}</td>
      <td class="l kn">${esc(brName(r.broker || ""))}${isNum(r.broker_share) && r.broker_share < 99 ? ` <span class="muted">%${fN(r.broker_share, 0)}</span>` : ""}</td></tr>`).join("") || `<tr><td colspan="10" class="empty">Filtreye uyan süpürme yok</td></tr>`;
    $("ag-note").textContent = `${d.note} · Defter % boş = geçmişten yeniden oluşturulan (yeniden başlatma öncesi) kayıt · ${d.updated}`;
  }
  $("ag-body").addEventListener("click", (e) => { const t = e.target.closest("[data-sym]"); if (t) openStock(t.dataset.sym); });
  function renderAgSet() {
    const c = AL.cfg; if (!c) { $("ag-set").innerHTML = `<div class="empty">Ayarlar yükleniyor…</div>`; return; }
    const a = c.agresif;
    $("ag-set").innerHTML = `<div class="card-h"><span class="card-title">DEDEKTÖR AYARLARI</span><button type="button" class="btn-ghost sm nf-lnk" data-nflink="ayar">🔔 Tüm bildirim ayarları</button></div>
      <div class="nm-mini">${ntRow("agresif_alim", true)}${ntRow("agresif_satis", true)}</div>
      <div class="al-row"><span class="k">Yön</span><div class="seg sm" id="ag-side">${[["buy", "SATIŞ TARAFI (ALIM)"], ["sell", "ALIŞ TARAFI (SATIŞ)"], ["both", "İKİSİ"]].map(([v, l]) => `<button type="button" data-v="${v}" class="${a.side === v ? "active" : ""}">${l}</button>`).join("")}</div></div>
      <div class="al-grid2">
        <label>Min. lot<input type="number" class="al-in" data-ag="min_lot" min="0" step="1000" value="${a.min_lot}"/></label>
        <label>Min. tutar ₺<input type="number" class="al-in" data-ag="min_tl" min="0" step="100000" value="${a.min_tl}"/></label>
        <label>Min. kademe<input type="number" class="al-in" data-ag="min_levels" min="1" max="25" step="1" value="${a.min_levels}"/></label>
        <label>Min. defter %<input type="number" class="al-in" data-ag="min_book_pct" min="0" max="100" step="5" value="${a.min_book_pct}"/></label>
      </div>${scopeSel("agresif", a)}${pushRow("Agresif Alım-Satım")}
      <div class="src-note">Koşulların tümü (VE) sağlanmalı. Bildirim tabanı: ≥2 kademe ve ≥250 bin ₺, ya da ≥1 Mn ₺.</div>`;
    document.querySelectorAll("#ag-side button").forEach((b) => b.addEventListener("click", () => saveCfg({ agresif: { side: b.dataset.v } }).then(() => { renderAgSet(); loadAg(); })));
    document.querySelectorAll("#ag-set [data-ag]").forEach((i) => i.addEventListener("change", () => { const v = parseFloat(i.value); if (isNum(v)) saveCfg({ agresif: { [i.dataset.ag]: v } }).then(loadAg); }));
  }

  // ---------------------------------------------------------- PARA AKIŞI
  const pa = { data: null, sort: "net", dir: -1, q: "", f: "all", n: 150 };
  async function loadPara() { try { pa.data = await api("/api/para-akisi", { timeout: 20000 }); renderPara(); } catch (e) { if (!pa.data) $("pa-body").innerHTML = `<tr><td colspan="8" class="empty">Veri alınamadı</td></tr>`; } }
  function renderPara() {
    const d = pa.data; if (!d) return;
    const M = d.market || {}, tot = (M.in || 0) + (M.out || 0);
    $("pa-mkt").innerHTML = `<div class="card-h"><span class="card-title">PİYASA TOPLAMI</span><span class="muted">${fN(d.rows.length)} pay</span></div>
      <div class="pa-split"><i style="width:${tot ? (M.in / tot * 100).toFixed(1) : 50}%"></i></div>
      <div class="kv-grid"><div class="kv"><span class="k">Para girişi</span><span class="v pos">${fT(M.in)}</span></div><div class="kv"><span class="k">Para çıkışı</span><span class="v neg">${fT(M.out)}</span></div>
      <div class="kv"><span class="k">Net</span><span class="v ${cls(M.net)}">${fT(M.net)} (${fPct(M.netp)})</span></div><div class="kv"><span class="k">Net giriş / çıkış hisse</span><span class="v"><b class="pos">${fN(M.pos)}</b> / <b class="neg">${fN(M.neg)}</b></span></div></div>`;
    const secs = d.sectors || []; const mx = Math.max(1e-9, ...secs.map((s) => Math.abs(s.net)));
    $("pa-sec").innerHTML = secs.map((s) => `<div class="pa-srow" data-sec="${esc(s.secn)}"><span class="pa-sn">${esc(s.secn)} <small>${s.n}</small></span>
      <span class="pa-sb"><i class="${s.net >= 0 ? "up" : "dn"}" style="width:${(Math.abs(s.net) / mx * 100).toFixed(1)}%"></i></span><span class="pa-sv ${cls(s.net)}">${fShort(s.net)}</span><span class="pa-sp ${cls(s.netp)}">${fPct(s.netp, 1)}</span></div>`).join("");
    let rows = d.rows || [];
    const qv = fold(pa.q.trim());
    if (qv) rows = rows.filter((r) => r.s.includes(qv) || fold(r.secn || "").includes(qv) || fold(r.n || nameOf(r.s) || "").includes(qv));
    if (pa.f === "in") rows = rows.filter((r) => r.net > 0); else if (pa.f === "out") rows = rows.filter((r) => r.net < 0);
    const k = pa.sort, dir = pa.dir;
    rows = [...rows].sort((a, b) => (k === "s" || k === "secn") ? dir * String(a[k] || "").localeCompare(String(b[k] || "")) : dir * ((a[k] ?? -1e18) - (b[k] ?? -1e18)));
    document.querySelectorAll("#pa-table th").forEach((th) => { th.classList.toggle("sorted", th.dataset.k === k); th.classList.toggle("asc", th.dataset.k === k && dir > 0); });
    $("pa-body").innerHTML = rows.slice(0, pa.n).map((r) => `<tr><td class="l sticky sym" data-sym="${esc(r.s)}">${esc(r.s)}</td><td>${fP(r.p)}</td><td class="${cls(r.c)}">${fPct(r.c)}</td>
      <td class="pos">${fShort(r.in)}</td><td class="neg">${fShort(r.out)}</td><td class="${cls(r.net)} b">${fShort(r.net)}</td><td class="${cls(r.netp)}">${fPct(r.netp, 1)}</td><td class="l muted">${esc(r.secn || "")}</td></tr>`).join("") || `<tr><td colspan="8" class="empty">Sonuç yok</td></tr>`;
    $("pa-more").hidden = rows.length <= pa.n; $("pa-more").textContent = `Daha fazla göster (+${fN(rows.length - pa.n)})`;
    $("pa-note").textContent = `${d.note} Kayıtlı işlem: ${fN(d.coverage.trades)} · ${String(d.updated || "").slice(11)}`;
  }
  document.querySelectorAll("#pa-table th").forEach((th) => th.addEventListener("click", () => { if (pa.sort === th.dataset.k) pa.dir *= -1; else { pa.sort = th.dataset.k; pa.dir = ["s", "secn"].includes(th.dataset.k) ? 1 : -1; } renderPara(); }));
  document.querySelectorAll("#pa-filter button").forEach((b) => b.addEventListener("click", () => { pa.f = b.dataset.f; document.querySelectorAll("#pa-filter button").forEach((x) => x.classList.toggle("active", x === b)); pa.sort = "net"; pa.dir = pa.f === "out" ? 1 : -1; renderPara(); }));
  $("pa-search").addEventListener("input", (e) => { pa.q = e.target.value; renderPara(); });
  $("pa-more").addEventListener("click", () => { pa.n += 300; renderPara(); });
  $("pa-body").addEventListener("click", (e) => { const t = e.target.closest("[data-sym]"); if (t) openStock(t.dataset.sym); });
  $("pa-sec").addEventListener("click", (e) => { const t = e.target.closest("[data-sec]"); if (t) { pa.q = t.dataset.sec; $("pa-search").value = pa.q; renderPara(); $("pa-table").scrollIntoView({ behavior: "smooth" }); } });

  // ---------------------------------------------------------- KURUM UYARILARI
  const ku = { tab: "feed", brokers: [], rapor: null, bq: "" };
  async function loadKuBrokers() { if (ku.brokers.length) return; try { ku.brokers = (await api("/api/kurum/list", { timeout: 15000 })).brokers || []; renderKuSet(); } catch (e) {} }
  function renderKuSet() {
    const c = AL.cfg; if (!c) { $("ku-set").innerHTML = `<div class="empty">Ayarlar yükleniyor…</div>`; return; }
    const k = c.kurum, sel = new Set(k.brokers || []);
    const qv = fold(ku.bq);
    const list = ku.brokers.filter((b) => !qv || fold(brName(b)).includes(qv));
    $("ku-set").innerHTML = `<div class="card-h"><span class="card-title">KURUM SEÇİMİ</span><span class="muted">${sel.size ? sel.size + " seçili" : "seçim yok = tüm kurumlar"}</span></div>
      <input type="search" class="ak-search" id="ku-bq" placeholder="Kurum ara..." value="${esc(ku.bq)}" autocomplete="off"/>
      <div class="ku-chips">${list.map((b) => `<button type="button" data-br="${esc(b)}" class="${sel.has(b) ? "active" : ""}">${esc(brName(b))}</button>`).join("") || '<span class="muted">Kurum listesi yükleniyor…</span>'}</div>
      <div class="al-row"><span class="k">Yön</span><div class="seg sm" id="ku-side">${[["buy", "AGRESİF ALIM"], ["sell", "AGRESİF SATIŞ"], ["both", "İKİSİ"]].map(([v, l]) => `<button type="button" data-v="${v}" class="${k.side === v ? "active" : ""}">${l}</button>`).join("")}</div></div>
      <div class="al-row"><span class="k">Min. tutar (10 dk penceresi) ₺</span><input type="number" class="al-in" id="ku-min" min="1000000" step="1000000" value="${k.min_tl}"/></div>
      <div class="nm-mini">${ntRow("kurum_alim", true)}${ntRow("kurum_satis", true)}${ntRow("gun_sonu", true)}</div>
      <div class="al-row"><label class="al-chk"><input type="checkbox" id="ku-auto" ${c.rapor.auto ? "checked" : ""}/> Gün sonu raporu 18:10'da otomatik</label><button type="button" class="btn-ghost sm nf-lnk" data-nflink="ayar">🔔 Tüm bildirim ayarları</button></div>
      ${pushRow("Kurum Uyarıları")}`;
    $("ku-bq").addEventListener("input", (e) => { ku.bq = e.target.value; const pos = e.target.selectionStart; renderKuSet(); const i = $("ku-bq"); i.focus(); try { i.setSelectionRange(pos, pos); } catch (x) {} });
    document.querySelectorAll("#ku-set [data-br]").forEach((b) => b.addEventListener("click", () => {
      const s = new Set(AL.cfg.kurum.brokers || []); s.has(b.dataset.br) ? s.delete(b.dataset.br) : s.add(b.dataset.br);
      const arr = [...s]; saveCfg({ kurum: { brokers: arr }, rapor: { brokers: arr } }).then(() => { renderKuSet(); AL.events = AL.events.filter((e) => e.kind !== "kurum"); AL.since = 0; AL.primed = false; pollAlerts(); });
    }));
    document.querySelectorAll("#ku-side button").forEach((b) => b.addEventListener("click", () => saveCfg({ kurum: { side: b.dataset.v } }).then(() => { renderKuSet(); refetchKu(); })));
    $("ku-min").addEventListener("change", (e) => { const v = parseFloat(e.target.value); if (isNum(v)) saveCfg({ kurum: { min_tl: v } }).then(refetchKu); });
    $("ku-auto").addEventListener("change", (e) => saveCfg({ rapor: { auto: e.target.checked } }));
  }
  function refetchKu() { AL.events = AL.events.filter((e) => e.kind !== "kurum"); AL.since = 0; AL.primed = false; pollAlerts(); }
  document.querySelectorAll("#ku-tab button").forEach((b) => b.addEventListener("click", () => {
    ku.tab = b.dataset.t; document.querySelectorAll("#ku-tab button").forEach((x) => x.classList.toggle("active", x === b));
    $("ku-feed-card").hidden = ku.tab !== "feed"; $("ku-rapor").hidden = ku.tab !== "rapor";
    if (ku.tab === "rapor") loadRapor(); else renderAlertFeeds();
  }));
  async function loadRapor() {
    const br = (AL.cfg && AL.cfg.kurum.brokers) || [];
    $("ku-rapor").innerHTML = `<div class="card"><div class="empty">Rapor hazırlanıyor…</div></div>`;
    try { ku.rapor = await api(`/api/kurum/rapor${br.length ? "?brokers=" + encodeURIComponent(br.join(",")) : ""}`, { timeout: 30000 }); renderRapor(); }
    catch (e) { $("ku-rapor").innerHTML = `<div class="card"><div class="empty">Rapor alınamadı</div></div>`; }
  }
  function renderRapor() {
    const d = ku.rapor; if (!d) return;
    const list = d.brokers.slice(0, d.selected.length ? 50 : 15);
    $("ku-rapor").innerHTML = `<div class="card"><div class="card-h"><span class="card-title">GÜN SONU RAPORU · ${esc(d.date)}</span><button type="button" class="btn-refresh" id="ku-rr">↻ Yenile</button></div>
      <div class="muted sm">${d.selected.length ? d.selected.map(brName).join(", ") : "Kurum seçilmedi → en yüksek hacimli 15 kurum"} · oluşturuldu ${esc(d.generated.slice(11))}</div></div>` +
      list.map((b) => `<div class="card rp-card"><div class="card-h"><span class="card-title">${esc(brName(b.broker))}</span><span class="${cls(b.net_tl)} b">Net ${fT(b.net_tl)}</span></div>
        <div class="kv-grid"><div class="kv"><span class="k">Alış</span><span class="v pos">${fT(b.buy_tl)}</span></div><div class="kv"><span class="k">Satış</span><span class="v neg">${fT(b.sell_tl)}</span></div>
        <div class="kv"><span class="k">Aktif / Pasif alım lot</span><span class="v">${fShort(b.aa)} / ${fShort(b.pa)}</span></div><div class="kv"><span class="k">Aktif / Pasif satış lot</span><span class="v">${fShort(b.as)} / ${fShort(b.ps)}</span></div></div>
        <div class="tbl-scroll"><table class="grid-table"><thead><tr><th class="l sticky">HİSSE</th><th>ALIŞ LOT</th><th>ALIŞ %</th><th>SATIŞ LOT</th><th>SATIŞ %</th><th>NET LOT</th><th>MALİYET</th><th>ALIŞ ₺</th><th>SATIŞ ₺</th><th>NET ₺</th><th>ORT. ALIŞ</th><th>ORT. SATIŞ</th><th>AKTİF ALIM</th><th>PASİF ALIM</th><th>AKTİF SATIŞ</th><th>PASİF SATIŞ</th></tr></thead>
        <tbody>${b.rows.slice(0, 40).map((r) => `<tr><td class="l sticky sym" data-sym="${esc(r.s)}">${esc(r.s)}</td><td class="pos">${fN(r.abl != null ? r.abl : r.buy)}</td><td class="pos">${r.bshare ? "%" + nf(1).format(r.bshare) : "—"}</td><td class="neg">${fN(r.asl != null ? r.asl : r.sell)}</td><td class="neg">${r.sshare ? "%" + nf(1).format(r.sshare) : "—"}</td><td class="${cls(r.anl != null ? r.anl : r.net)} b">${fN(r.anl != null ? r.anl : r.net)}</td><td>${fP(r.aco)}</td>
          <td>${fShort(r.btl)}</td><td>${fShort(r.stl)}</td><td class="${cls(r.ntl)}">${fShort(r.ntl)}</td><td>${fP(r.bavg)}</td><td>${fP(r.savg)}</td><td>${fN(r.aa)}</td><td>${fN(r.pa)}</td><td>${fN(r.as)}</td><td>${fN(r.ps)}</td></tr>`).join("")}</tbody></table></div>
        ${b.rows.length > 40 ? `<div class="src-note">+${b.rows.length - 40} hisse daha (toplam ${b.stocks})</div>` : ""}</div>`).join("") +
      (d.akd_status && !d.akd_status.complete ? `<div class="kr-akd">${akdBadgeHtml(d.akd_status)}</div>` : "") +
      `<div class="src-note">Yalnızca günlük AKD'si yüklü hisseler listelenir. Alış/Satış/Net lot, Alış %/Satış % ve Maliyet günlük AKD'den (hisse AKD sekmesi Günlük ile aynı kayıt). ₺ tutarları, ort. alış ve aktif/pasif kırılımı işlem kaydından. ${esc(d.note)} Kayıtlı işlem: ${fN(d.coverage.trades)}.</div>`;
    $("ku-rr").addEventListener("click", loadRapor);
  }
  $("ku-rapor").addEventListener("click", (e) => { const t = e.target.closest("[data-sym]"); if (t) openStock(t.dataset.sym); });

  // ---------------------------------------------------------- TAHTACI TESPİTİ
  const th = { view: "score", broker: LS.get("th_broker", ""), stock: LS.get("th_stock", ""), data: null, sort: "score", dir: -1, q: "", n: 150 };
  async function loadTh() {
    let url = `/api/tahtaci?view=${th.view}&limit=1500${th.nocross ? "&nocross=1" : ""}`;
    if (th.view === "broker") { if (!th.broker) { await loadThBrokers(); $("th-body").innerHTML = `<tr><td colspan="12" class="empty">Kurum seçin</td></tr>`; return; } url += "&broker=" + encodeURIComponent(th.broker); }
    if (th.view === "stock") { if (!th.stock) { $("th-body").innerHTML = `<tr><td colspan="12" class="empty">Hisse kodu girin</td></tr>`; return; } url += "&symbol=" + encodeURIComponent(th.stock); }
    try { th.data = await api(url, { timeout: 30000 }); if (th.data.brokers) fillThBrokers(th.data.brokers); renderTh(); } catch (e) { if (!th.data) $("th-body").innerHTML = `<tr><td colspan="12" class="empty">Veri alınamadı</td></tr>`; }
  }
  async function loadThBrokers() { if ($("th-broker").options.length > 1) return; try { fillThBrokers((await api("/api/kurum/list")).brokers); } catch (e) {} }
  function fillThBrokers(list) {
    const sel = $("th-broker"); if (sel.options.length - 1 === list.length) return;
    sel.innerHTML = `<option value="">Kurum seçin…</option>` + list.map((b) => `<option value="${esc(b)}" ${b === th.broker ? "selected" : ""}>${esc(brName(b))}</option>`).join("");
  }
  function renderTh() {
    const d = th.data; if (!d) return;
    $("th-broker").hidden = th.view !== "broker"; $("th-stock").hidden = th.view !== "stock";
    let rows = (d.rows || []).map((r) => (r.nl2 === undefined ? Object.assign(r, { nl2: r.anl != null ? r.anl : r.net }) : r));
    const qv = fold(th.q.trim());
    if (qv) rows = rows.filter((r) => r.s.includes(qv) || fold(brName(r.b)).includes(qv));
    const k = th.sort, dir = th.dir;
    rows = [...rows].sort((a, b) => (k === "s" || k === "b") ? dir * String(a[k]).localeCompare(String(b[k])) : dir * ((a[k] ?? -1e18) - (b[k] ?? -1e18)));
    document.querySelectorAll("#th-table th").forEach((x) => { x.classList.toggle("sorted", x.dataset.k === k); x.classList.toggle("asc", x.dataset.k === k && dir > 0); });
    const sc = (v) => `<span class="th-sc"><i style="width:${Math.min(100, v).toFixed(0)}%;background:hsl(${Math.round(120 - Math.min(100, v) * 1.2)} 70% 45%)"></i><b>${fN(v, 0)}</b></span>`;
    $("th-body").innerHTML = rows.slice(0, th.n).map((r) => `<tr><td class="l sticky sym" data-sym="${esc(r.s)}">${esc(r.s)}</td><td class="l kn" data-br="${esc(r.b)}">${esc(brName(r.b))}</td><td>${sc(r.score)}</td>
      <td class="b">${isNum(r.share) ? "%" + fN(r.share, 1) : "—"}</td><td class="pos">${r.bshare ? "%" + nf(1).format(r.bshare) : "—"}</td><td class="neg">${r.sshare ? "%" + nf(1).format(r.sshare) : "—"}</td><td class="pos">${fShort(r.aa)}</td><td class="pos muted2">${fShort(r.pa)}</td><td class="neg">${fShort(r.as)}</td><td class="neg muted2">${fShort(r.ps)}</td>
      <td class="${cls(r.nl2)} b">${fShort(r.nl2)}</td><td>${fP(r.aco)}</td><td>${fP(r.bavg)}</td><td>%${fN(r.two, 0)}</td><td>%${fN(r.act, 0)}</td></tr>`).join("") || `<tr><td colspan="15" class="empty">${d.akd_status && !d.akd_status.complete ? `AKD yükleniyor: ${fN(d.akd_status.have)}/${fN(d.akd_status.total)}` : "Sonuç yok"}</td></tr>`;
    krAkdBadge(d.akd_status && !d.akd_status.complete ? d.akd_status : null, "th-akd");
    $("th-more").hidden = rows.length <= th.n; $("th-more").textContent = `Daha fazla göster (+${fN(rows.length - th.n)})`;
    $("th-note").textContent = `${d.note} Hacim payı / Alış % / Satış % / Net lot / Maliyet: yalnızca günlük AKD (hisse AKD sekmesi Günlük ile aynı kayıt; Alış % = ALICILAR DAĞILIM %, Satış % = SATICILAR DAĞILIM %); AKD'si henüz yüklenmemiş hisse listelenmez. Aktif/pasif ve ort. alış işlem kaydından.${th.view === "score" ? " Skor görünümü: her hissenin en yüksek skorlu kurumu (≥5 Mn ₺ hacimli hisseler)." : ""} · ${String(d.updated || "").slice(11)}`;
  }
  document.querySelectorAll("#th-view button").forEach((b) => b.addEventListener("click", () => {
    th.view = b.dataset.v; document.querySelectorAll("#th-view button").forEach((x) => x.classList.toggle("active", x === b));
    $("th-broker").hidden = th.view !== "broker"; $("th-stock").hidden = th.view !== "stock"; if (th.view === "stock") $("th-stock").value = th.stock;
    th.data = null; th.n = 150; $("th-body").innerHTML = `<tr><td colspan="12" class="empty">Yükleniyor…</td></tr>`; loadTh();
  }));
  $("th-broker").addEventListener("change", (e) => { th.broker = e.target.value; LS.set("th_broker", th.broker); loadTh(); });
  $("th-stock").addEventListener("change", (e) => { th.stock = fold(e.target.value.trim()); LS.set("th_stock", th.stock); loadTh(); });
  $("th-search").addEventListener("input", (e) => { th.q = e.target.value; renderTh(); });
  th.nocross = !!LS.get("th_nocross", false); $("th-nocross").checked = th.nocross;
  $("th-nocross").addEventListener("change", (e) => { th.nocross = e.target.checked; LS.set("th_nocross", th.nocross); th.data = null; $("th-body").innerHTML = `<tr><td colspan="12" class="empty">Yükleniyor…</td></tr>`; loadTh(); });
  $("th-more").addEventListener("click", () => { th.n += 300; renderTh(); });
  document.querySelectorAll("#th-table th").forEach((x) => x.addEventListener("click", () => { if (th.sort === x.dataset.k) th.dir *= -1; else { th.sort = x.dataset.k; th.dir = ["s", "b"].includes(x.dataset.k) ? 1 : -1; } renderTh(); }));
  $("th-body").addEventListener("click", (e) => {
    const b = e.target.closest("[data-br]"); if (b) { th.view = "broker"; th.broker = b.dataset.br; LS.set("th_broker", th.broker); document.querySelectorAll("#th-view button").forEach((x) => x.classList.toggle("active", x.dataset.v === "broker")); loadThBrokers().then(() => { $("th-broker").value = th.broker; }); loadTh(); return; }
    const t = e.target.closest("[data-sym]"); if (t) openStock(t.dataset.sym);
  });

  // ===================================================================== v1.24.0 ==
  // ---- POC BASKISI / ALIŞ ORTALAMA BASKISI / CİDDİ YÜKSELİŞ – TAVAN ADAYI (sabitler; op görünümünü paylaşır)
  const BF = ["k_ciddi", "k_poc", "k_aort"];
  const BF_L = { k_ciddi: "CİDDİ YÜKSELİŞ / TAVAN ADAYI", k_poc: "POC Baskısı", k_aort: "Alış Ortalama Baskısı" };
  const BF_S = { k_ciddi: "CİDDİ / TAVAN ADAYI", k_poc: "POC BASKISI", k_aort: "ALIŞ ORT. BASKISI" };
  const OS_FEAT = { k_maliyet: "Maliyet Yükselten Kurumlar", k_poc: "POC Baskısı", k_aort: "Alış Ortalama Baskısı", k_ciddi: "CİDDİ YÜKSELİŞ", k_tavanaday: "TAVAN ADAYI",
    dr_duvar: "Derinlik: Duvar eriyor", dr_buyuk: "Derinlik: Büyük emir girişi", dr_denge: "Derinlik: Denge alışa döndü", akd_tarama: "AKD Taraması", aktif_kurum: "Aktif İşlem (Kurum)", tavan_treni: "TAVAN TRENİ" };   // v1.25.0 · v1.26.0 · v1.26.2 · v1.26.3
  const isB = (id) => BF.includes(id);
  const isKD = (id) => id === "k_maliyet" || isB(id);   // tarih seçicili + tok'lu (değişmediyse "same") tarayıcılar

  // ===================================================================== v1.20.1 ==
  // ---- Bildirim türleri kataloğu (sunucu app/v120.py NTYPES ile aynı anahtarlar / varsayılanlar)
  const NT_GROUPS = [
    { g: "albunu", name: "✅ AL BUNU", dot: "#22c55e", link: "albunu", items: [   // v1.34.0 (varsayılan KAPALI; AL BUNU ekranındaki anahtarla da açılır)
      ["al_bunu", "✅ AL BUNU (tavan adayı listesine yeni giren)", "Yalnız listeye YENİ giren, güveni ≥70 ve iki döngü üst üste listede kalan hisse · hisse başına günde 1, saatte en çok 3 · 10:15–17:30 · varsayılan KAPALI", "off", "up"]] },
    { g: "tren", name: "🚀 TRENE ATLA", dot: "#22c55e", link: "tren", items: [   // v1.31.0 (varsayılan AÇIK, diğerlerinden bağımsız)
      ["tren_atla", "🚀 TRENE ATLA (şimdi piyasa emriyle atla)", "Tek alarm, hareketin İLK saniyelerinde: aynı saniyede ≥5 kademe aktif alış süpürmesi (≥500 bin ₺) + gün değişimi ≤ +%2 (fazlası GEÇ) + son 1 dk ≥+%0,8 ve hızlanıyor + 60 sn aktif alış ≥%75 + hacim ≥5× + tavana ≥%3 · tetikten ≈1–3 sn sonra gelir · kaçmış/dönmüş sinyal gönderilmez · hisse başına 30 dk'da 1, saatte en çok 6", "notify", "up"]] },
    { g: "tt", name: "TAVAN / TABAN", dot: "#8b8cf8", link: "tavan", items: [
      ["tavan_yaklasan", "Tavana yaklaşan", "Fiyat, eşik % kadar tavana yaklaştı", "off", "up"],
      ["tavan_kitlendi", "Tavana kitlendi", "Fiyat tavana oturdu (tavan alış lotu ile)", "off", "up"],
      ["tavan_eriyen", "Tavan eriyen", "Tavandaki alış lotu tepeden eşik % kadar eridi", "off", "down"],
      ["tavan_cozuldu", "Tavandan çözülen", "Tavan bozuldu, fiyat tavandan ayrıldı", "off", "down"],
      ["taban_yaklasan", "Tabana yaklaşan", "Fiyat, eşik % kadar tabana yaklaştı", "off", "down"],
      ["taban_kitlendi", "Tabana kitlendi", "Fiyat tabana oturdu (taban satış lotu ile)", "off", "down"],
      ["taban_donen", "Taban dönen", "Taban satışları bitti, fiyat tabandan döndü", "off", "up"]] },
    { g: "ag", name: "AGRESİF İŞLEM", dot: "#f59e0b", link: "agresif", items: [
      ["agresif_alim", "Agresif alım (süpürme)", "Satış tarafında kademeler süpürüldü", "off", "up"],
      ["agresif_satis", "Agresif satış (süpürme)", "Alış tarafında kademeler süpürüldü", "off", "down"]] },
    { g: "ku", name: "KURUM", dot: "#e8833a", link: "kurumuyari", items: [
      ["kurum_alim", "Kurum agresif alım", "Seçili kurumun 10 dk'lık eşik üstü agresif alımı", "off", "up"],
      ["kurum_satis", "Kurum agresif satış", "Seçili kurumun 10 dk'lık eşik üstü agresif satışı", "off", "down"],
      ["gun_sonu", "Gün sonu raporu", "18:10'da otomatik kurum raporu hazır", "off", "info"],
      ["k_maliyet", "Maliyet yükselten kurum (ayak izi)", "Kurum maliyetini yükselterek alıyor: ciddiyet skoru ≥70 veya yeni ciddi ilk ayak izi (≥2 Mn ₺, aktif ≥%60, skor ≥50) — hisse+kurum başına günde 1 kez", "off", "up"]] },
    { g: "bs", name: "BASKI & HAZIR SENARYOLAR", dot: "#22c55e", link: "k_ciddi", items: [
      ["k_tavanaday", "TAVAN ADAYI (hazır senaryo)", "Hisse TAVAN ADAYI setine yeni girdi (POC / alış ortalaması / maliyet yükselten kurum kanıtı) — canlı seansta, hisse başına günde 1 kez", "off", "up"],
      ["k_ciddi", "CİDDİ YÜKSELİŞ (hazır senaryo)", "Hisse CİDDİ YÜKSELİŞ setine yeni girdi (POC / alış ortalaması / maliyet yükselten kurum kanıtı) — canlı seansta, hisse başına günde 1 kez", "off", "up"],
      ["k_poc", "POC Baskısı", "Baskı skoru ≥75 veya son 10 dk'da POC yükseltildi + POC'tan destek tepkisi — hisse başına günde 1 kez", "off", "up"],
      ["k_aort", "Alış Ortalama Baskısı", "Baskı skoru ≥75 veya son 10 dk'da aktif alış ortalaması yükseldi + ortalamadan destek tepkisi — hisse başına günde 1 kez", "off", "up"]] },
    { g: "dr", name: "DERİNLİK ALARMLARI", dot: "#3b82f6", link: "dr", items: [   // v1.25.0
      ["dr_duvar", "Duvar eriyor", "En iyi 2 kademedeki ≥1,5 Mn ₺ duvar, zirvesinin %40'ına veya altına indi — hisse+tür başına 30 dk'da 1, saatte en çok 40 (ciro ≥5 Mn ₺, 10:05–18:00)", "off", "info"],
      ["dr_buyuk", "Büyük emir girişi", "İlk 5 kademeye tek seferde ≥2 Mn ₺ ve kademe medyanının ≥4 katı emir girdi — hisse+tür başına 30 dk'da 1", "off", "info"],
      ["dr_denge", "Denge alışa döndü", "İlk 5 kademe alış/satış ₺ oranı 60 sn içinde ≤1,0'dan ≥2,0'a çıktı (alış ≥1 Mn ₺) — hisse+tür başına 30 dk'da 1", "off", "up"]] },
    { g: "ol", name: "PİYASA OLAYLARI", dot: "#14b8a6", link: "akis", items: [
      ["ani_hacim", "Ani hacim", "1 dk'da gün ortalamasının ≥8 katı hacim", "off", "info"],
      ["hacim_rvol", "Hacim dünü aştı (RVOL)", "Günlük hacim dünün 1× / 2× / 3× / 5× / 10× katı", "off", "info"],
      ["zirve_52h", "52H zirve", "52 haftalık zirveye ulaştı / yeni zirve", "off", "up"],
      ["dip_52h", "52H dip", "52 haftalık dibe indi / yeni dip", "off", "down"],
      ["devre_kesici", "Devre kesici", "Hisse tek fiyat emir toplamaya geçti", "off", "down"],
      ["devre_kalkti", "Devre kesici kalktı", "Sürekli işleme geri döndü", "off", "info"],
      ["tam_tur", "Gün içi tam tur", "Gün içinde −%5 ↔ +%5 arası tam tur", "off", "info"],
      ["kapanis", "Kapanış", "Tavanda / tabanda veya ±%7 kapanış", "off", "info"],
      ["durum", "İşlem durumu değişimi", "Seans / işlem durumu değişti", "off", "info"],
      ["akis_tavan", "Akış: tavan oldu / döndü", "Canlı Veri Akışı tavan olayları (tüm hisseler)", "off", "up"],
      ["akis_taban", "Akış: taban oldu / çözüldü", "Canlı Veri Akışı taban olayları (tüm hisseler)", "off", "down"]] },
    { g: "op", name: "OPERASYON TESPİTİ", dot: "#d4a64a", link: "op", items: [
      ["op_skor", "Operasyon skoru", "Hissenin operasyon skoru ≥65 oldu veya +10 arttı", "off", "up"],
      ["op_sessiz", "Sessiz toplama", "Yatay fiyatta kurumun istikrarlı net toplaması", "off", "up"],
      ["op_kuyruk", "Tavan kuyruğu güçlü", "Tavan alış kuyruğu float/hacme göre çok güçlü (kilit)", "off", "up"],
      ["op_duvar", "Satış duvarı eriyor", "Büyük satış kademesi iptalle küçülüyor", "off", "up"],
      ["op_seri", "Ardışık süpürme serisi", "Aynı kurum 15 dk'da ≥3 kez satış kademesi süpürdü", "off", "up"],
      ["op_cizme", "Kademe çizme", "Agresif alımla dakikada çok kademe yukarı itiliyor", "off", "up"],
      ["op_konsantrasyon", "Kurum konsantrasyonu", "İlk 3 alıcının alış payı yüksek / hızla artıyor", "off", "up"],
      ["op_yabanci", "Yabancı/kurumsal giriş", "Yabancı/kurumsal aracı yeni veya artan pozisyon", "off", "up"],
      ["op_float", "Düşük float + ani hacim", "Hacim/float oranı normalin çok üstünde", "off", "info"],
      ["op_spoof", "Sahte emir şüphesi", "Büyük emirler gerçekleşmeden ekleniyor/siliniyor", "off", "info"],
      ["op_kapanis", "Kapanış seansı itmesi", "18:00–18:10 kapanışta fiyat itildi", "off", "up"],
      ["op_acilis", "Açılış seansı baskısı", "Açılışta güçlü boşluk / tavana yakın açılış", "off", "up"],
      ["op_kirilim", "Kırılım + kurum onayı", "20g direnç agresif kurum alımıyla kırıldı", "off", "up"],
      ["op_tukenme", "Satıcı tükenmesi", "Satış derinliği eriyor, büyük satıcı satışı kesti", "off", "up"],
      ["op_kap", "KAP + birikim", "Önemli KAP bildirimi ve aynı anda birikim", "off", "info"],
      ["op_rotasyon", "Sektör rotasyonu", "Sektöre giriş başlıyor, hisse geride", "off", "up"],
      ["op_rakip", "Rakip gecikmesi", "Sektör lideri koşarken benzer rakip geride", "off", "up"],
      ["op_mtf", "Çok zaman dilimli momentum", "1/5/15/60 dk RVOL ve fiyat birlikte hızlanıyor", "off", "up"],
      ["op_sikisma", "Sıkışma kırılımı", "Dar bant sıkışmasından hacimli kırılım", "off", "up"],
      ["op_diverjans", "Para akışı diverjansı", "Fiyat düşerken net para girişi", "off", "info"]] },
    { g: "ks", name: "KADEME & ŞERİT ANALİZİ", dot: "#22c55e", link: "k_pozitif", items: [
      ["k_islem", "Alıcılar satıcıları siliyor", "Son 5 dk'da işlemlerin ≥%85'i aktif alış, ≥3 Mn ₺ ve fiyat ≥+%0,3 (İşlem Analizi)", "off", "up"],
      ["k_kurumfiyat", "Kurum ısrarlı fiyat alımı", "Bir kurum aynı fiyattan ≥40 işlemle ≥5 Mn ₺ aldı", "off", "up"],
      ["k_pozitif", "Pozitif anlık hareketlilik", "Skor ≥75 ve 3 dk ≥1 Mn ₺: ani ivme + süpürme + satıcı yok", "off", "up"],
      ["k_koruma", "Yakın kademe koruması", "İlk 4 alış kademesi ≥5 Mn ₺ ve skor ≥88", "off", "up"],
      ["k_bosluk", "Satış kademesi boşluğu", "Satış tarafı çok ince, skor ≥85", "off", "up"],
      ["k_otoban", "Otoban kademe", "Boş satış kademesi + iten aktif alış, skor ≥75", "off", "up"],
      ["k_doldur", "Doldur-boşalt kademe", "Alışa emir yazılıyor, satış siliniyor/süpürülüyor, skor ≥75", "off", "up"],
      ["k_baski", "Aktif alış baskı endeksi", "Endeks ≥88 ve 5 dk ≥2 Mn ₺", "off", "up"],
      ["k_supurme", "Kademeli süpürme", "≥4 satış kademesi art arda süpürüldü (gün <%6), skor ≥70", "off", "up"],
      ["k_balina", "Balina imzası", "Israrcı/algoritmik büyük alıcı, skor ≥75", "off", "up"],
      ["k_miknatis", "Fiyat mıknatısı üstü", "Fiyat ana işlem merkezinin üstüne çıktı, skor ≥70", "off", "up"],
      ["k_destek", "Gerçek destek", "Satışları emen gerçek destek seviyesi, skor ≥80", "off", "up"],
      ["k_duvar", "Satış duvarı emiliyor / süpürüldü", "Büyük satış duvarı aktif alışla tüketiliyor, skor ≥75", "off", "up"],
      ["k_sikisma", "Sıkışma → patlama (Evre 2)", "Sıkışma sonrası ilk gerçek kademe süpürmesi", "off", "up"],
      ["k_serit", "Şerit hızı patlaması", "İşlem sıklığı ≥5× ve son 60 sn ≥60 işlem", "off", "info"],
      ["k_uptick", "Yeşil dalga (seri uptick)", "≥7 adımlık kesintisiz yükselen işlem serisi sürüyor", "off", "up"],
      ["k_kayma", "Asimetrik kayma fırsatı", "Tek büyük emir +%3 kaldırabilir, skor ≥85", "off", "info"],
      ["k_agresiflik", "Kurumsal agresiflik (acil toplama)", "Aciliyet ≥85 ve kurum net ≥10 Mn ₺", "off", "up"],
      ["k_vdonus", "Onaylı V dönüş", "Dipten hacimli agresif alımla onaylı V dönüşü", "off", "up"],
      ["k_gercek", "Gerçek (hacim destekli) yükseliş", "15 dk ≥+%2, aktif alış ve gerçeklik skoru ≥75", "off", "up"]] },
    { g: "akdt", name: "AKD TARAMASI", dot: "#f59e0b", link: "akdt", items: [   // v1.26.0
      ["akd_tarama", "Kurum hisseye girdi (AKD kuralı)", "KEŞFET › AKD Taraması'nda kaydettiğiniz kural: seçtiğiniz kurum(lar) bir hissede eşik net % (DAĞILIM) ve ₺ üstünde (isteğe bağlı aktif alış/satış % eşiğiyle) net alıcı/satıcı oldu — seans içinde ~60 sn'de bir, hisse+kurum+kural başına günde 1, saatte en çok 30", "off", "up"]] },
    { g: "akk", name: "AKTİF İŞLEM (KURUM)", dot: "#22c55e", link: "akk", items: [   // v1.26.2
      ["aktif_kurum", "Kurum bir hissede agresif aktif alış yaptı", "KEŞFET › Aktif İşlem Taraması (KURUM) dedektörü (varsayılan KAPALI — o ekrandan açılır): kurum bir hissede eşik ₺ üstünde ve eşik aktif alış % üstünde aldı (isteğe bağlı yalnız net alıcı / yalnız seçili kurum) — ~60 sn'de bir, hisse+kurum başına günde 1, saatte en çok 15", "off", "up"],
      ["tavan_treni", "🚂 TAVAN TRENİ (balina kurum aktif alışla tavana çekiyor)", "KEŞFET › Aktif İşlem Taraması (KURUM) dedektörü (varsayılan KAPALI — o ekrandan açılır): hissenin en büyük balinası (AKD Alış #1 / en büyük alış lotu), net alımın ≥%30'u ve alımının ≥%65'i AKTİF, ≥5 Mn ₺ aktif alış (GÜÇLÜ: Alış #1 + ≥10 Mn ₺) — ~60 sn'de bir, hisse+kurum başına günde 1, saatte en çok 10", "off", "up"]] },   // v1.26.3
    { g: "fm", name: "FORMASYONLAR", dot: "#a78bfa", link: "fm_mum", items: [   // v1.27.0
      ["formasyon_mum", "🕯 Mum formasyonu", "KEŞFET › Mum Formasyonları dedektörü (varsayılan KAPALI — o ekrandan açılır): seçtiğiniz periyotlarda (5dk…1H) son KAPANAN barda eşik güvenilirlikte yükseliş/düşüş mum formasyonu oluştu (isteğe bağlı yalnız hacim teyitli) — hisse+periyot+formasyon başına günde 1, saatte en çok 12", "off", "up"],
      ["formasyon_grafik", "📐 Grafik formasyonu kırılımı", "KEŞFET › Grafik Formasyonları dedektörü (varsayılan KAPALI — o ekrandan açılır): OBO/Ters OBO, ikili-üçlü tepe/dip, üçgen, takoz, bayrak, kanal… seçtiğiniz periyotta tam kapanan barda kırıldı (eşik kalite) — giriş/STOP/HEDEF ile; günde 1, saatte en çok 12", "off", "up"]] },
    { g: "olm", name: "OLAY LİSTESİ (ALARM)", dot: "#ef4444", link: "olay", items: [   // v1.30.0 (varsayılan KAPALI)
      ["ol_rksw", "DİRENÇ KIRILDI + SÜPÜRME (yukarı)", "KEŞFET › Olay Listesi (ALARM): POC direnci kırıldı ve ±pencere içinde seviye üstüne eşik üstü yukarı süpürme (gerçek, hacimli kırılım) — GÜÇLÜ / ORTA", "off", "up"],
      ["ol_p_hk", "Hazır: Hacimli kırılım (GÜÇLÜ)", "Direnç kırıldı + süpürme, yalnız GÜÇLÜ derece", "off", "up"],
      ["ol_p_ard", "Hazır: Art arda süpürme", "10 dk içinde ≥4 yukarı süpürme (≥4 kademe)", "off", "up"],
      ["ol_p_pocsw", "Hazır: POC yükseltme + süpürme", "POC yükseltildi + yeni POC üstüne süpürme", "off", "up"],
      ["ol_p_dbsw", "Hazır: Destek tepkisi + süpürme", "Destek tepkisi + seviye üstüne süpürme", "off", "up"],
      ["ol_p_tvy", "Hazır: Tavan yolu", "Kırılım + süpürme, tavana yakın, gün güçlü", "off", "up"],
      ["ol_rk", "Olay: DİRENÇ KIRILDI", "Fiyat POC direncini yukarı kırdı (tüm hisseler)", "off", "up"],
      ["ol_sw", "Olay: SÜPÜRME", "Aynı saniyede aktif alışla ≥2 kademe yukarı süpürme (≥100 bin ₺)", "off", "up"],
      ["ol_up", "Olay: POC YÜKSELTME", "POC ≥60 sn kalıcı olarak yükseldi", "off", "up"],
      ["ol_db", "Olay: DESTEK TEPKİSİ", "POC desteğine temas sonrası tepki", "off", "up"],
      ["ol_sen", "Olay: SENARYO", "CİDDİ YÜKSELİŞ / TAVAN ADAYI senaryosuna giriş", "off", "up"],
      ["ol_rt", "Olay: DİRENÇ TEMASI", "Fiyat alttan POC direncine değdi", "off", "info"],
      ["ol_rr", "Olay: DİRENÇ REDDİ", "Direnç temasından aşağı dönüş", "off", "down"],
      ["ol_dt", "Olay: DESTEK TEMASI", "Fiyat üstten POC desteğine değdi", "off", "info"],
      ["ol_dk", "Olay: DESTEK KIRILDI", "Fiyat POC desteğini aşağı kırdı", "off", "down"],
      ["ol_dn", "Olay: POC DÜŞÜRME", "POC ≥60 sn kalıcı olarak düştü", "off", "down"]] },
    { g: "al", name: "ALARMLAR", dot: "#d4a64a", link: "alarm", items: [
      ["fiyat_alarmi", "Fiyat alarmı", "Kurduğunuz hedef fiyat gerçekleşti", "off", "info"]] },
  ];
  const NT = {};
  NT_GROUPS.forEach((G) => G.items.forEach(([k, l, d, def, dir]) => { NT[k] = { k, l, d, def, dir, g: G.g }; }));
  const NT_TT = { yaklasan: "tavan_yaklasan", tavanda: "tavan_kitlendi", eriyen: "tavan_eriyen", cozuldu: "tavan_cozuldu", taban_yaklasan: "taban_yaklasan", tabanda: "taban_kitlendi", taban_donen: "taban_donen" };
  function ntOf(e) {
    if (e.nt) return e.nt;
    if (e.kind === "tavan") return NT_TT[e.sub] || "tavan_yaklasan";
    if (e.kind === "agresif") return e.sub === "buy" ? "agresif_alim" : "agresif_satis";
    if (e.kind === "kurum") return e.sub === "buy" ? "kurum_alim" : "kurum_satis";
    if (e.kind === "rapor") return "gun_sonu";
    return e.sub || e.kind;
  }
  const NP = Object.assign({ master: true, modes: {}, sound: {}, ts: 0 }, LS.get("np", {}));
  function modeOf(nt) { if (NP.master === false) return "off"; return NP.modes[nt] || (NT[nt] && NT[nt].def) || "view"; }
  const rawMode = (nt) => NP.modes[nt] || (NT[nt] && NT[nt].def) || "view";
  const soundOn = (nt) => NP.sound[nt] !== false && !(AL.cfg && AL.cfg.sound === false);
  let npT = null;
  function saveNP() {
    NP.ts = Date.now(); LS.set("np", NP); clearTimeout(npT);
    npT = setTimeout(() => saveCfg({ notif: { master: NP.master, modes: NP.modes, sound: NP.sound, ts: NP.ts } }), 350);
  }
  function syncNPFromServer() {
    const n = AL.cfg && AL.cfg.notif; if (!n) return;
    const srvNewer = (n.ts || 0) > (NP.ts || 0) || (!NP.ts && Object.keys(n.modes || {}).length);
    if (srvNewer) { NP.master = n.master !== false; NP.modes = Object.assign({}, n.modes || {}); NP.sound = Object.assign({}, n.sound || {}); NP.ts = n.ts || 0; LS.set("np", NP); }
    else if ((NP.ts || 0) > (n.ts || 0)) saveNP();   // yerel tercih daha yeni → sunucuya (Web Push buna göre)
  }
  const SVG_SND_ON = `<svg viewBox="0 0 24 24"><path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4zM15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  const SVG_SND_OFF = `<svg viewBox="0 0 24 24"><path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4zM16 9.5l5 5M21 9.5l-5 5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  const MODE_L = [["off", "KAPALI"], ["view", "GÖRÜNTÜLE"], ["notify", "BİLDİRİM"]];
  function modeSeg(nt) { const m = rawMode(nt); return `<div class="nm-seg" data-nt="${nt}">${MODE_L.map(([v, l]) => `<button type="button" data-m="${v}" class="${m === v ? "on " + v : ""}">${l}</button>`).join("")}</div>`; }
  function sndBtn(nt) { const on = NP.sound[nt] !== false; return `<button type="button" class="nm-snd ${on ? "on" : ""}" data-snd="${nt}" ${rawMode(nt) !== "notify" ? "disabled" : ""} aria-label="Ses" title="Ses">${on ? SVG_SND_ON : SVG_SND_OFF}</button>`; }
  function ntRow(nt, compact) {
    const t = NT[nt];
    return `<div class="nm-row ${compact ? "compact" : ""}" data-row="${nt}"><div class="nm-l"><b>${esc(t.l)}</b>${compact ? "" : `<small>${esc(t.d)}</small>`}</div><div class="nm-r">${modeSeg(nt)}${sndBtn(nt)}</div></div>`;
  }
  function refreshNtRows(nt) {
    document.querySelectorAll(`[data-row="${nt}"] .nm-r`).forEach((r) => { r.innerHTML = modeSeg(nt) + sndBtn(nt); });
    try { allAlPaint(); } catch (e) {}   // v1.30.0
    if (st.view === "bildirim" && nfs.tab === "ayar") renderNfCounts();
  }
  document.addEventListener("click", (e) => {
    const b = e.target.closest(".nm-seg button");
    if (b) { const nt = b.closest(".nm-seg").dataset.nt; NP.modes[nt] = b.dataset.m; saveNP(); refreshNtRows(nt); if (b.dataset.m === "notify") askNotify(true); return; }
    const s = e.target.closest("[data-snd]");
    if (s) { if (s.disabled) return; const nt = s.dataset.snd; NP.sound[nt] = NP.sound[nt] === false; saveNP(); refreshNtRows(nt); if (NP.sound[nt] !== false) beep(NT[nt].dir); return; }
    const g = e.target.closest("[data-gset]");
    if (g) { const [gk, m] = g.dataset.gset.split(":"); const G = NT_GROUPS.find((x) => x.g === gk); if (G) { G.items.forEach(([k]) => { NP.modes[k] = m; }); saveNP(); renderNfAyar(); if (st.view === "telegram") tgRender(); } return; }
    const L = e.target.closest("[data-nflink]");
    if (L) { const v = L.dataset.nflink; if (v === "alarm" || v === "ayar" || v === "gecmis") nfOpen(v); else if (v === "dr") drGo(); else if (/^k_/.test(v)) opOpen(v); else go(v); }
  });

  // ---- üst bildirim bandı (slide-down, yığın, ~6 sn, dokun = aç, kaydır / ✕ = kapat)
  const NB_MAX = 4;
  function banner(e, mode) {
    const box = $("nb-stack"); const t = NT[e.nt] || {};
    const dir = t.dir || evDir(e);
    const el = document.createElement("div");
    el.className = `nb ${dir}${e.nt === "tren_atla" ? " tren" : ""}`;   // v1.31.0
    el.innerHTML = `<div class="nb-m"><div class="nb-h"><b>${esc(e.title || "")}</b><span class="nb-t">${esc(e.time || "")}</span></div>
      <div class="nb-x">${esc(e.text || "")}</div><div class="nb-f">${esc(t.l || "")}${mode === "view" ? " · sadece görüntüle" : ""}</div></div>
      <button type="button" class="nb-close" aria-label="Kapat">✕</button>`;
    box.prepend(el);
    requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add("in")));
    while (box.children.length > NB_MAX) box.lastElementChild.remove();
    let tm = setTimeout(() => close(), 6000), closed = false;
    function close(dx) {
      if (closed) return; closed = true; clearTimeout(tm);
      el.style.transform = dx ? `translateX(${dx > 0 ? 120 : -120}%)` : "translateY(-130%)"; el.style.opacity = "0";
      setTimeout(() => el.remove(), 280);
    }
    el.querySelector(".nb-close").addEventListener("click", (ev) => { ev.stopPropagation(); close(); });
    let sx = null, sy = 0, dx = 0, dy = 0;
    el.addEventListener("touchstart", (ev) => { sx = ev.touches[0].clientX; sy = ev.touches[0].clientY; dx = dy = 0; clearTimeout(tm); el.style.transition = "none"; }, { passive: true });
    el.addEventListener("touchmove", (ev) => {
      if (sx == null) return; dx = ev.touches[0].clientX - sx; dy = ev.touches[0].clientY - sy;
      if (Math.abs(dx) > Math.abs(dy)) el.style.transform = `translateX(${dx}px)`; else if (dy < 0) el.style.transform = `translateY(${dy}px)`;
    }, { passive: true });
    el.addEventListener("touchend", () => {
      el.style.transition = ""; sx = null;
      if (Math.abs(dx) > 70) close(dx); else if (dy < -35) close();
      else { el.style.transform = ""; tm = setTimeout(() => close(), 4000); }
    });
    el.addEventListener("click", () => { if (Math.abs(dx) > 10 || Math.abs(dy) > 10) return; close(); openEvent(e); });
    return el;
  }
  function openEvent(e) {
    if (e.kind === "rapor") { go("kurumuyari"); setTimeout(() => { const b = document.querySelector('#ku-tab [data-t="rapor"]'); if (b) b.click(); }, 60); }
    else if (e.sym && /^formasyon_/.test(e.nt || "") && e.data && e.data.tf && e.data.k) { const d0 = e.data; st.tab = "ozet"; LS.set("tab", "ozet"); openStock(e.sym); setTimeout(() => { try { fmProof(e.sym, d0.tf, d0.kind === "grafik" ? "grafik" : "mum", d0.k); } catch (x) {} }, 700); }   // v1.27.0
    else if (e.sym) { if (/^dr_/.test(e.nt || "")) { st.tab = "derinlik"; LS.set("tab", "derinlik"); } else if (e.nt === "akd_tarama" || e.nt === "aktif_kurum" || e.nt === "tavan_treni") { st.tab = "akd"; LS.set("tab", "akd"); } openStock(e.sym); }
    else nfOpen("gecmis");
  }

  // ---- bildirim geçmişi (KAPALI olmayan türler) + zil rozeti
  const NH = LS.get("nh", []);
  let nhRead = LS.get("nh_read", 0), nhT = null;
  function histAdd(e, mode) {
    NH.push({ id: e.id, ts: Date.now(), time: e.time, nt: e.nt, title: e.title, text: e.text, sym: e.sym || null, kind: e.kind, sub: e.sub, mode });
    if (NH.length > 500) NH.splice(0, NH.length - 500);
    clearTimeout(nhT); nhT = setTimeout(() => LS.set("nh", NH), 400);
  }
  function unreadN() { let n = 0; for (let i = NH.length - 1; i >= 0 && NH[i].ts > nhRead; i--) n++; return n; }
  function renderBell() {
    const n = unreadN(), b = $("bell-n");
    b.hidden = !n; b.textContent = n > 99 ? "99+" : String(n);
    $("btn-bell").classList.toggle("has", n > 0);
    const u = $("nf-unread"); if (u) u.textContent = n ? n : "";
  }
  function markRead() { nhRead = Date.now(); LS.set("nh_read", nhRead); renderBell(); }
  function deliver(list) {
    let beeped = false, shown = 0;
    for (const e of list) {
      e.nt = ntOf(e);
      const m = modeOf(e.nt);
      if (m === "off") continue;
      histAdd(e, m);
      if (shown < NB_MAX) { const ee = e; setTimeout(() => banner(ee, m), shown * 320); shown++; }
      if (m === "notify") {
        if (!beeped && soundOn(e.nt)) { beep((NT[e.nt] && NT[e.nt].dir) || evDir(e)); beeped = true; }
        if (document.hidden || !document.hasFocus()) sysNotify(e);
      }
    }
    if (shown || list.length) { renderBell(); if (st.view === "bildirim" && nfs.tab === "gecmis") renderNfList(); }
  }
  function deliverLocal(e) {
    e.nt = e.nt || ntOf(e); const m = modeOf(e.nt);
    if (m === "off") return m;
    histAdd(e, m); banner(e, m); renderBell();
    if (m === "notify" && soundOn(e.nt)) beep("info");
    if (st.view === "bildirim" && nfs.tab === "gecmis") renderNfList();
    return m;
  }

  // ---- Bildirimler ekranı: GEÇMİŞ / AYARLAR / ALARMLAR
  const nfs = { tab: "gecmis", f: "all", prevRead: 0 };
  function nfOpen(tab) { nfs.tab = tab || "gecmis"; if (st.view === "bildirim") renderNf(); else go("bildirim"); }
  function renderNf() {
    document.querySelectorAll("#nf-tab button").forEach((b) => b.classList.toggle("active", b.dataset.t === nfs.tab));
    $("nf-gecmis").hidden = nfs.tab !== "gecmis"; $("nf-ayar").hidden = nfs.tab !== "ayar"; $("nf-alarm").hidden = nfs.tab !== "alarm";
    if (nfs.tab === "gecmis") { nfs.prevRead = nhRead; renderNfList(); markRead(); }
    else if (nfs.tab === "ayar") renderNfAyar();
    else renderNfAlarm();
  }
  document.querySelectorAll("#nf-tab button").forEach((b) => b.addEventListener("click", () => { nfs.tab = b.dataset.t; renderNf(); }));
  function renderNfList() {
    const groups = [["all", "TÜMÜ"], ...NT_GROUPS.map((G) => [G.g, G.name])];
    const cnt = { all: NH.length }; NH.forEach((h) => { const g = (NT[h.nt] || {}).g || "ol"; cnt[g] = (cnt[g] || 0) + 1; });
    $("nf-chips").innerHTML = groups.map(([k, l]) => `<button type="button" data-f="${k}" class="${nfs.f === k ? "active" : ""}">${l} <b>${cnt[k] || 0}</b></button>`).join("");
    const rows = NH.filter((h) => nfs.f === "all" || ((NT[h.nt] || {}).g || "ol") === nfs.f).slice(-300).reverse();
    $("nf-count").textContent = `${fN(rows.length)} bildirim · okunmamış ${fN(unreadN())}`;
    $("nf-list").innerHTML = rows.map((h) => {
      const t = NT[h.nt] || {}, G = NT_GROUPS.find((x) => x.g === t.g) || {};
      return `<div class="nf-row ${t.dir || "info"} ${h.ts > nfs.prevRead ? "new" : ""}" data-hid="${esc(String(h.id))}" data-hts="${h.ts}">
        <span class="nf-dot" style="background:${G.dot || "#888"}"></span>
        <div class="nf-m"><div class="nf-h"><b>${esc(h.title || "")}</b><span class="nf-t">${esc(h.time || "")}</span></div>
        <div class="nf-x">${esc(h.text || "")}</div>
        <div class="nf-tags"><span class="al-tag gray">${esc(t.l || h.nt)}</span><span class="nf-mode ${h.mode}">${h.mode === "notify" ? "BİLDİRİM" : "GÖRÜNTÜLE"}</span></div></div></div>`;
    }).join("") || `<div class="empty">Henüz bildirim yok — KAPALI olmayan türlerdeki olaylar burada listelenir.<br><button type="button" class="btn-ghost sm" data-nflink="ayar">Bildirim ayarlarını aç</button></div>`;
  }
  $("nf-chips").addEventListener("click", (e) => { const b = e.target.closest("[data-f]"); if (b) { nfs.f = b.dataset.f; renderNfList(); } });
  $("nf-list").addEventListener("click", (e) => { const r = e.target.closest("[data-hts]"); if (!r) return; const h = NH.find((x) => String(x.ts) === r.dataset.hts); if (h) openEvent(h); });
  $("nf-read").addEventListener("click", () => { markRead(); nfs.prevRead = nhRead; renderNfList(); });
  $("nf-clear").addEventListener("click", () => { NH.length = 0; LS.set("nh", NH); markRead(); renderNfList(); });
  function renderNfCounts() {
    const c = { off: 0, view: 0, notify: 0 }; Object.keys(NT).forEach((k) => c[rawMode(k)]++);
    const el = $("nf-cnt"); if (el) el.innerHTML = `<span class="nf-mode notify">BİLDİRİM ${c.notify}</span><span class="nf-mode view">GÖRÜNTÜLE ${c.view}</span><span class="nf-mode off">KAPALI ${c.off}</span>`;
  }
  function renderNfAyar() {
    const perm = "Notification" in window ? Notification.permission : "unsupported";
    const permL = perm === "unsupported" && osActive() ? "🟢 Telegram üzerinden" : { granted: "🟢 izin verildi", denied: "🔴 engellendi (tarayıcı ayarlarından açın)", default: "⚪ sorulmadı", unsupported: "bu ortamda yok — Telegram kullanın" }[perm];
    $("nf-ayar").innerHTML = trSetCard() + allAlCard() + `<section class="card nf-master">
        <div class="card-h"><span class="card-title">BİLDİRİMLER</span><label class="nf-sw"><input type="checkbox" id="nf-master" ${NP.master !== false ? "checked" : ""}/><span></span>${NP.master !== false ? "AÇIK" : "TÜMÜ KAPALI"}</label></div>
        <div class="nf-cnt" id="nf-cnt"></div>
        <div class="al-row"><span class="k">Sistem bildirimi izni</span><span class="nf-perm">${permL}${perm === "default" ? ` <button type="button" class="btn-ghost sm" id="nf-perm">İzin ver</button>` : ""}</span></div>
        ${pushRow("Bildirimler")}
        <div id="os-slot">${osCard()}</div>
        <div class="src-note"><b>KAPALI</b>: gösterilmez · <b>GÖRÜNTÜLE</b>: üstte bant + geçmişe eklenir (ses ve sistem bildirimi yok) · <b>BİLDİRİM</b>: bant + ses (🔊 tür bazında) + sistem / Web Push bildirimi (tarayıcı arka planda veya kapalıyken). Tercihler bu cihazda ve sunucuda (push aboneliğiniz için) saklanır.</div>
      </section>` + drSetCard() + k5SetCard() +
      NT_GROUPS.map((G) => `<section class="card nf-grp ${NP.master === false ? "dim" : ""}">
        <div class="card-h"><span class="nf-gt"><i style="background:${G.dot}"></i>${G.name}<small>${G.items.length}</small></span>
          <button type="button" class="btn-ghost sm" data-nflink="${G.link}">${G.link === "alarm" ? "Alarmlar →" : G.link === "dr" ? "Derinlik →" : G.link === "akdt" ? "AKD Taraması →" : G.link === "akk" ? "Aktif İşlem →" : G.link === "fm_mum" ? "Formasyonlar →" : G.link === "tren" ? "Adaylar & kurallar →" : G.link === "akis" ? "Akış →" : /^k_/.test(G.link) ? "Tarayıcılar →" : "Eşikler & kapsam →"}</button></div>
        <div class="nf-gset"><span class="muted sm">Tümü:</span>${MODE_L.map(([v, l]) => `<button type="button" data-gset="${G.g}:${v}" class="nf-gb ${v}">${l}</button>`).join("")}</div>
        ${G.items.map(([k]) => ntRow(k, false) + (OS_FEAT[k] ? `<div class="km-ostest"><button type="button" class="btn-ghost sm" data-ostest="${esc(OS_FEAT[k])}">✈️ Telegram Test · ${esc(OS_FEAT[k])}</button><button type="button" class="btn-ghost sm" data-nflink="${k === "k_tavanaday" ? "k_ciddi" : /^dr_/.test(k) ? "dr" : k === "akd_tarama" ? "akdt" : k === "aktif_kurum" ? "akk" : k}">${/^dr_/.test(k) ? "Derinlik →" : "Tarayıcı →"}</button></div>` : "")).join("")}</section>`).join("");
    renderNfCounts();
    osLoadCfg().then(() => { osPaint(); const pr = document.querySelector("#nf-ayar [data-pushrow]"); if (pr) pr.outerHTML = pushRow("Bildirimler"); });
    $("nf-master").addEventListener("change", (e) => { NP.master = e.target.checked; saveNP(); renderNfAyar(); });
    allAlWire();   // v1.30.0
    const pb = $("nf-perm"); if (pb) pb.addEventListener("click", async () => { await askNotify(); renderNfAyar(); });
  }
  function renderNfAlarm() {
    const by = new Map((st.list || []).map((x) => [x.s, x.p]));
    const nOn = st.alarms.filter((a) => !a.off).length;
    $("nf-alarm").innerHTML = `<section class="card"><div class="card-h"><span class="card-title">FİYAT ALARMLARI</span><span class="muted">${nOn} açık · ${st.alarms.length - nOn} kapalı</span></div>
      ${st.alarms.map((a) => `<div class="nf-al ${a.off ? "off" : ""}"><b class="sym" data-sym="${esc(a.sym)}">${esc(a.sym)}</b><span>${a.op === "gte" ? "≥" : "≤"} ₺${fP(a.target)}</span><span class="muted">son ${fP(by.get(a.sym))}</span><button type="button" class="nf-altog ${a.off ? "" : "on"}" data-altog="${esc(a.id)}">${a.off ? "KAPALI" : "AÇIK"}</button><button type="button" class="btn-ghost sm" data-aldel="${esc(a.id)}">Sil</button></div>`).join("") || '<div class="empty">Aktif alarm yok</div>'}
      <div class="src-note">Yeni alarm: hisse kartındaki 🔔 düğmesi. Alarm tetiklenince "Fiyat alarmı" türünün moduna göre bant / ses / sistem bildirimi gelir.</div>
      <div class="nm-mini">${ntRow("fiyat_alarmi", false)}</div></section>`;
  }
  $("nf-alarm").addEventListener("click", (e) => {
    const tg = e.target.closest("[data-altog]"); if (tg) { const a = st.alarms.find((x) => x.id === tg.dataset.altog); if (a) { a.off = !a.off; LS.set("alarms", st.alarms); renderNfAlarm(); toast(a.off ? "Fiyat alarmı kapatıldı (listede duruyor)" : "Fiyat alarmı açıldı"); } return; }
    const d = e.target.closest("[data-aldel]"); if (d) { st.alarms = st.alarms.filter((a) => a.id !== d.dataset.aldel); LS.set("alarms", st.alarms); renderAlarmBadge(); renderNfAlarm(); return; }
    const s = e.target.closest("[data-sym]"); if (s) openStock(s.dataset.sym);
  });
  $("btn-bell").addEventListener("click", () => nfOpen("gecmis"));
  renderBell();

  // ---- KEŞFET menüsü + kullanıcı seçimli alt menü
  const P = (d) => `<svg viewBox="0 0 24 24"><path d="${d}" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  const KI = {
    eik: "M7 4h10v4a5 5 0 0 1-10 0zM7 6H4a3 3 0 0 0 3 4M17 6h3a3 3 0 0 1-3 4M12 13v4M8 20h8M10 17h4",   // v1.29.0
    olay: "M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15zM10 20a2 2 0 0 0 4 0M4 5l2 2M20 5l-2 2",   // v1.30.0
    home: "M4 11l8-7 8 7v9h-5v-6H9v6H4z", kesfet: "M4 7h16M4 12h16M4 17h16",
    tavan: "M3 18h4v-4h4v-4h4V6h6", agresif: "M13 2L4 14h7l-1 8 9-12h-7l1-8z", akis: "M3 12h4l3-7 4 14 3-7h4",
    baski: "M12 3.5a8.5 8.5 0 1 0 0 17a8.5 8.5 0 1 0 0-17M12 7.5a4.5 4.5 0 1 0 0 9a4.5 4.5 0 1 0 0-9M12 11.2v1.6",
    para: "M12 3v18M16 7.5c0-1.7-1.8-2.8-4-2.8S8 5.8 8 7.5s1.8 2.5 4 3 4 1.4 4 3.3-1.8 3-4 3-4-1.2-4-3",
    radar: "M4 5h16l-6 7.2V18l-4 2v-7.8z", movers: "M3 17l6-6 4 4 8-8M15 7h6v6", hacim: "M5 20V11M10 20V5M15 20v-7M20 20v-4",
    radar_tavan: "M12 20V9M7 13.5l5-5 5 5M5 4h14", radar_taban: "M12 4v11M7 10.5l5 5 5-5M5 20h14",
    tavanda: "M12 4l7 9H5zM5 19h14", tabanda: "M12 19l7-9H5zM5 5h14",
    kurum: "M3 10l9-6 9 6M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 20h18",
    tahtaci: "M10.5 4a6.5 6.5 0 1 0 0 13a6.5 6.5 0 1 0 0-13M15.5 15.5L21 21M10.5 7.5a2 2 0 1 0 0 4a2 2 0 1 0 0-4M7 14.5c.8-1.6 2-2.3 3.5-2.3s2.7.7 3.5 2.3",
    kurumuyari: "M6 16.5V11a6 6 0 0 1 12 0v5.5l1.6 2H4.4zM10 20.5a2.2 2.2 0 0 0 4 0",
    gunsonu: "M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6", akd: "M9 11a3.5 3.5 0 1 0 0-7a3.5 3.5 0 1 0 0 7M3 20c.6-3.4 3-5.5 6-5.5s5.4 2.1 6 5.5M16 4.5a3.5 3.5 0 0 1 0 6.5M18 14.8c1.7.8 2.7 2.6 3 5.2",
    takas: "M7 7h13l-3.5-3.5M17 17H4l3.5 3.5", search: "M10.5 4a6.5 6.5 0 1 0 0 13a6.5 6.5 0 1 0 0-13M15.5 15.5L21 21",
    derinlik: "M12 3l9 5-9 5-9-5zM3 12.5l9 5 9-5M3 16.5l9 5 9-5", islemler: "M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01",
    kademe: "M4 6h9M4 10h13M4 14h7M4 18h16", sinyal: "M3 12h3l2.5-6 4 12 3-9 2 3H21",
    ai: "M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8zM18.5 15.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z",
    endeks: "M4 19V5M4 19h16M8 15l3-4 3 2 5-6", sektor: "M12 3a9 9 0 1 0 9 9h-9zM14.5 3.3A9 9 0 0 1 20.7 9.5H14.5z",
    bildirim_ayar: "M4 7h10M18 7h2M4 17h4M12 17h8M14 4.5v5M8 14.5v5", derinlik_ayar: "M12 3l9 5-9 5-9-5zM3 12.5l9 5 9-5M17.5 17.5h4M19.5 15.5v4", bildirim_gecmis: "M12 7v5l3 2M3.5 12a8.5 8.5 0 1 0 2.5-6M3 4v4h4",
    alarmlar: "M12 6.5a7 7 0 1 0 0 14a7 7 0 1 0 0-14M12 10v3.5l2.3 1.5M5 3.5L2.5 6M19 3.5L21.5 6",
    favs: "M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z", about: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M12 11v5.5M12 7.5v.01",
  };
  // v1.21.0 OPERASYON TESPİTİ — 30 özellik (sunucu app/operasyon.py FEATURES / ORDER ile aynı)
  const OPF = [[29, "Operasyon Skoru", "OP. SKOR"], [30, "Operasyon Zaman Çizelgesi", "ZAMAN"], [1, "Sessiz Toplama Dedektörü", "SESSİZ"], [2, "Tavan Kuyruğu Gücü", "KUYRUK"],
    [3, "Satış Duvarı Erimesi", "DUVAR"], [4, "Ardışık Süpürme Serisi", "SERİ"], [5, "Kademe Çizme Hızı", "ÇİZME"], [6, "Tahtacı Maliyet Bandı", "MALİYET"],
    [7, "Kurum Konsantrasyonu", "KONSANTR."], [8, "Takas Birikimi Trendi", "TAKAS TR."], [9, "Yabancı / Kurumsal Giriş", "YABANCI"], [10, "Tavan Öncesi İmza", "İMZA"],
    [11, "Düşük Float + Ani Hacim", "FLOAT"], [12, "Alış Derinliği Kalınlaşması", "ALIŞ DER."], [13, "Sahte Emir (Spoofing) Takibi", "SPOOF"], [14, "Kapanış Seansı Operasyonu", "KAPANIŞ"],
    [15, "Açılış Seansı Baskısı", "AÇILIŞ"], [16, "VWAP Üstü Israr", "VWAP"], [17, "Kırılım + Kurum Onayı", "KIRILIM"], [18, "Satıcı Tükenmesi", "TÜKENME"],
    [19, "Çapraz İşlem Ayıklama", "ÇAPRAZ"], [20, "Kurum Ortaklığı Haritası", "ORTAKLIK"], [21, "Kurumun Geçmiş Başarısı", "BAŞARI"], [22, "Bilanço / KAP Yakınlığı", "KAP"],
    [23, "Sektör Rotasyonu", "ROTASYON"], [24, "Rakip Gecikmesi", "RAKİP"], [25, "Çok Zaman Dilimli Momentum Uyumu", "MTF"], [26, "Dar Bant Sıkışması", "SIKIŞMA"],
    [27, "Para Akışı Diverjansı", "DİVERJANS"], [28, "Tavan Tutunma Olasılığı", "TUTUNMA"]];
  const OPI = { 29: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M12 7a5 5 0 1 0 0 10a5 5 0 1 0 0-10M12 11a1 1 0 1 0 0 2a1 1 0 1 0 0-2", 30: "M4 6h6M14 6h6M4 12h10M18 12h2M4 18h3M11 18h9",
    1: "M3 17h18M6 17V13M10 17v-5M14 17v-4M18 17v-6M4 8c3-2 13-2 16 0", 2: "M12 4l7 9H5zM6 17h12M8 20h8", 3: "M5 5h14v4H5zM7 13h10v3H7zM10 19h4", 4: "M13 2L4 14h7l-1 8 9-12h-7l1-8z",
    5: "M4 20l4-4 3 2 4-6 5-6M15 6h5v5", 6: "M3 12h18M7 8l-4 4 4 4M17 8l4 4-4 4", 7: "M12 3a9 9 0 1 0 9 9h-9z", 8: "M7 7h13l-3.5-3.5M17 17H4l3.5 3.5", 9: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18",
    10: "M5 12l4 4 10-10M5 20h14", 11: "M5 20V11M10 20V5M15 20v-7M20 20v-4", 12: "M4 6h16M4 10h14M4 14h12M4 18h10", 13: "M12 3l9 16H3zM12 9v5M12 17v.01", 14: "M12 7v5l3 2M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18",
    15: "M5 19V5l7 5 7-5v14", 16: "M3 14c3-6 6-6 9 0s6 6 9 0M3 10h18", 17: "M3 15h6l3-8 3 8h6M12 3v4", 18: "M4 6h16M6 10h12M9 14h6M11 18h2", 19: "M7 4l-4 4 4 4M3 8h14M17 12l4 4-4 4M21 16H7",
    20: "M6 6a2 2 0 1 0 0 .1M18 6a2 2 0 1 0 0 .1M12 18a2 2 0 1 0 0 .1M7.5 7.5l3.5 9M16.5 7.5l-3.5 9M8 6h8", 21: "M8 21h8M12 17v4M6 4h12v4a6 6 0 0 1-12 0zM6 6H3a3 3 0 0 0 3 4M18 6h3a3 3 0 0 1-3 4",
    22: "M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6", 23: "M12 3a9 9 0 1 0 9 9M12 3v9h9M15 3.5a9 9 0 0 1 5.5 5.5", 24: "M4 18l5-8 4 5 7-11M4 21h16", 25: "M3 12h3l2.5-6 4 12 3-9 2 3H21",
    26: "M4 8h16M4 16h16M8 12h8", 27: "M4 6l7 7 3-3 6 6M4 18l7-7", 28: "M12 21V9M7 13.5l5-5 5 5M5 4h14" };
  OPF.forEach(([f]) => { KI["op_" + f] = OPI[f]; });
  // v1.22.0 KADEME & ŞERİT ANALİZİ — 20 tarayıcı (sunucu app/v122.py CAT / ORDER ile aynı)
  const KCAT = [["k_islem", "İşlem Analizi (Tüm Hisseler)", "İŞLEM ANL."], ["k_kurumfiyat", "Kurumların En Çok Alım-Satım Fiyat Analizi", "KURUM FİYAT"],
    ["k_pozitif", "Pozitif Anlık Hareketlilik", "ANLIK HAREKET"], ["k_koruma", "Yakın Kademe Koruması", "KORUMA"], ["k_bosluk", "Satış Kademesi Boşluğu", "BOŞLUK"],
    ["k_otoban", "Otoban Kademe", "OTOBAN"], ["k_doldur", "Doldur-Boşalt Kademe", "DOLDUR-BOŞALT"], ["k_baski", "Aktif Alış Baskı Endeksi", "BASKI END."],
    ["k_supurme", "Kademeli Süpürme Tespiti", "SÜPÜRME"], ["k_balina", "Balina İmza Algoritması", "BALİNA"], ["k_miknatis", "Fiyat Mıknatısı / İşlem Yoğunluk Bölgesi", "MIKNATIS"],
    ["k_destek", "Gerçek Destek – Sahte Destek Ayrımı", "GERÇEK DESTEK"], ["k_duvar", "Satış Duvarı Absorpsiyon Algılama", "DUVAR EMİLİM"], ["k_sikisma", "Sıkışma → Patlama Radarı", "SIKIŞMA"],
    ["k_serit", "Şerit Hızı (Tape Speed) Patlaması", "ŞERİT HIZI"], ["k_uptick", "Seri Uptick (Yeşil Dalga) Süpürmesi", "YEŞİL DALGA"], ["k_kayma", "Asimetrik Kayma (Slippage) Fırsatları", "KAYMA"],
    ["k_agresiflik", "Kurumsal Agresiflik Endeksi (Aggressor Ratio)", "AGRESİFLİK"], ["k_vdonus", "Hacimli V Dönüş Analizi", "V DÖNÜŞ"], ["k_gercek", "Gerçek mi Fake mi Yükseliş", "GERÇEK/FAKE"]];
  const KCAT_L = {}; KCAT.forEach(([k, l]) => { KCAT_L[k] = l; });
  Object.assign(KI, {
    k_islem: "M4 6h10M4 12h16M4 18h7M17 4v4M20 6h-6", k_kurumfiyat: "M3 10l9-6 9 6M5 10v8M19 10v8M3 20h18M9 14h6M12 11v6",
    k_pozitif: "M3 17l5-5 3 3 7-8M14 7h4v4M5 21h14", k_koruma: "M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6zM8 12h8M8 15h8",
    k_bosluk: "M4 5h16M4 9h6M14 9h6M4 13h3M17 13h3M4 17h16", k_otoban: "M8 21L10 3M16 21L14 3M12 6v2M12 11v2M12 16v2",
    k_doldur: "M4 7h8M4 11h11M4 15h14M20 5l-3 3M17 5l3 3", k_baski: "M12 20V8M7 12l5-5 5 5M4 4h16M4 20h3M17 20h3",
    k_supurme: "M4 18h3v-3h3v-3h3V9h3V6h4M18 4l2 2-2 2", k_balina: "M3 13c2-4 6-6 10-5 3 .8 5 3 8 2-1 4-5 7-10 7-4 0-7-2-8-4zM17 8c0-2 1-3 3-4M15 12h.01",
    k_miknatis: "M6 4v8a6 6 0 0 0 12 0V4h-4v8a2 2 0 0 1-4 0V4zM6 8h4M14 8h4", k_destek: "M4 18h16M7 18V9M12 18V6M17 18v-7M5 21h14",
    k_duvar: "M4 5h16v4H4zM4 11h7v4H4zM13 11h7v4h-7zM4 17h16", k_sikisma: "M4 7l8 4 8-4M4 17l8-4 8 4M12 3v2M12 19v2",
    k_serit: "M3 12h3l2-5 3 10 2-6 2 3h6M18 5l3 3-3 3", k_uptick: "M3 19l3-3 3 1 3-4 3 1 3-4 3-3M17 5h4v4",
    k_kayma: "M4 18c4 0 6-12 16-12M4 6h4M16 18h4M14 14l2 4 4-2", k_agresiflik: "M13 2L4 14h7l-1 8 9-12h-7l1-8zM20 4l-2 2",
    k_vdonus: "M4 5l8 14 8-14M8 5h-4M20 5h-4", k_gercek: "M5 12l4 4 10-10M4 4l4 4M8 4l-4 4", k_maliyet: "M4 20l5-6 4 3 7-9M15 8h5v5M6 7a1.5 1.5 0 1 0 0 .1M10 4a1.2 1.2 0 1 0 0 .1",
    k_poc: "M3 18l4-6 3 3 4-7 3 4 4-6M3 12h18M7 12v2M14 12v2", k_aort: "M3 17l5-4 4 2 5-6 4-2M3 13c4-1 8-1 18-5M12 21v-4",
    k_ciddi: "M4 20l5-7 4 3 7-11M15 5h5v5M3 3h4M3 7h2" });
  const KF = [
    { g: "🧱 ORDER BLOCK TARAMASI", dot: "#a78bfa", col: "pu", items: [["obt", "Order Block Taraması — çok periyotlu destek/direnç, ÇOK GÜÇLÜ kesişimler", "YENİ"]] },   // v1.36.0
    { g: "✈️ TELEGRAM BİLDİRİM AYARLARI", dot: "#38bdf8", col: "pu", items: [["telegram", "Telegram Bildirim Ayarları — bot, kanal, test, ne gönderilsin", "YENİ"]] },   // v1.38.0
    { g: "🔗 LİNK OPTİMİZASYON", dot: "#f59e0b", col: "pu", items: [["linkopt", "Link Optimizasyon — link, ngrok kotası, Yeni Link Oluştur", "YENİ"]] },   // v1.35.0
    { g: "✅ AL BUNU", dot: "#22c55e", col: "pu", hero: true, items: [["albunu", "AL BUNU — Tavan Adayı (tek liste: kurum itiyor, hâlâ alıyor)", "YENİ"]] },   // v1.34.0
    { g: "🚀 TRENE ATLA", dot: "#22c55e", col: "pu", items: [["tren", "TRENE ATLA — şimdi sert yükseliş başlıyor (tek alarm)", "YENİ"]] },   // v1.31.0
    { g: "D-A-K SKORLARI", dot: "#38bdf8", col: "pu", items: [["skor", "D-A-K Skorları — Derinlik · AKD · Kademe Analizi (tüm hisseler)", "YENİ"]] },   // v1.32.0
    { g: "ALGO DESTEK / DİRENÇ", dot: "#a3e635", col: "pu", items: [["algo", "Algo Destek / Algo Direnç — tekrarlayan lot duvarları (tüm hisseler)", "YENİ"]] },   // v1.33.0
    { g: "EN İYİ KOŞULLAR", dot: "#f5c542", col: "pu", items: [["eik", "En İyi Koşullar (tüm özelliklerin en iyi ayarı)", "YENİ"]] },   // v1.29.0
    { g: "OLAY LİSTESİ (ALARM)", dot: "#ef4444", col: "pu", items: [["olay", "Olay Listesi (ALARM) — tüm hisselerde olay akışı + alarm", "YENİ"]] },   // v1.30.0
    { g: "KADEME & ŞERİT ANALİZİ", dot: "#22c55e", col: "pu", items: KCAT.filter(([k]) => k !== "k_islem" && k !== "k_kurumfiyat").map(([k, l]) => [k, l, "YENİ"]) },
    { g: "BASKI & HAZIR SENARYOLAR", dot: "#22c55e", col: "pu", items: [["k_ciddi", "CİDDİ YÜKSELİŞ / TAVAN ADAYI (Hazır Senaryolar)", "YENİ"], ["k_poc", "POC Baskısı", "YENİ"], ["k_aort", "Alış Ortalama Baskısı", "YENİ"]] },
    { g: "OPERASYON TESPİTİ", dot: "#d4a64a", col: "or", items: OPF.map(([f, l]) => ["op_" + f, l, f === 29 ? "YENİ" : null]) },
    { g: "CANLI İZLEME", dot: "#8b8cf8", col: "pu", items: [["tavan", "Tavan-Taban İzleme", "CANLI"], ["agresif", "Agresif İzleme", "CANLI"], ["akis", "Canlı Veri Akışı", "CANLI"], ["baski", "Derinlik Baskısı"], ["para", "Toplu Para Giriş-Çıkışı"], ["derinlik", "Derinlik (25 Kademe)"], ["islemler", "Gerçekleşen İşlemler"], ["k_islem", "İşlem Analizi (Tüm Hisseler)", "YENİ"]] },
    { g: "TARAMALAR", dot: "#8b8cf8", col: "pu", items: [["radar", "Piyasa Radarı", "YENİ"], ["movers", "Yükselenler & Düşenler"], ["hacim", "Yüksek Hacimliler"], ["radar_tavan", "Tavana Yakın Hisseler"], ["radar_taban", "Tabana Yakın Hisseler"], ["tavanda", "Tavandaki Hisseler"], ["tabanda", "Tabandaki Hisseler"]] },
    { g: "FORMASYONLAR", dot: "#a78bfa", col: "pu", items: [["fm_mum", "Mum Formasyonları (5dk…1H)", "YENİ"], ["fm_grafik", "Grafik Formasyonları (stop/hedef)", "YENİ"]] },   // v1.27.0
    { g: "KURUM ANALİZİ", dot: "#f59e0b", col: "or", items: [["kurum", "Kurum Analizi"], ["tahtaci", "Tahtacı Tespiti"], ["k_maliyet", "Maliyet Yükselten Kurumlar (Kurum Ayak İzi)", "YENİ"], ["kurumuyari", "Kurum Uyarıları"], ["gunsonu", "Gün Sonu Raporu"], ["akd", "AKD Dağılımı"], ["akdt", "AKD Taraması (Tüm Hisseler)", "YENİ"], ["akk", "Aktif İşlem Taraması (KURUM)", "YENİ"], ["takas", "Takas Analizi"], ["k_kurumfiyat", "Kurumların En Çok Alım-Satım Fiyat Analizi", "YENİ"]] },
    { g: "HİSSE ANALİZİ", dot: "#f59e0b", col: "or", items: [["kademe", "Kademe Analizi", "TÜMÜ"], ["sinyal", "Teknik Sinyaller", "TÜMÜ"]] },
    { g: "ENDEKS", dot: "#d4a64a", col: "or", items: [["endeks", "Hisselerin Endekse Etkisi"], ["sektor", "Sektörel Para Akışı"]] },
    { g: "ARAÇLAR", dot: "#14b8a6", col: "pu", items: [["search", "Hisse Ara"], ["ai", "AI Analiz"], ["bildirim_ayar", "Bildirim Ayarları"], ["derinlik_ayar", "Derinlik Analizleri Ayarları", "YENİ"], ["bildirim_gecmis", "Bildirim Geçmişi"], ["alarmlar", "Alarm Yönetimi"], ["favs", "Favoriler / Listem"], ["about", "Bağlantı Durumu"]] },
  ];
  KI.akdt = "M4 5h16M4 10h10M4 15h7M4 20h5M16.5 11a3.5 3.5 0 1 0 0 7a3.5 3.5 0 1 0 0-7M19 17l2.5 2.5";   // v1.26.0
  KI.akk = "M13 3L5 13h6l-1 8 8-10h-6l1-8z";   // v1.26.2
  KI.albunu = "M4 12l5 5L20 6M3 21h18";   // v1.34.0
  KI.algo = "M4 4h7v3H4zM4 9h7v3H4zM4 14h7v3H4zM4 19h7v2H4zM14 5h6M14 10h6M14 15h6M14 20h6";   // v1.33.0
  KI.skor = "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M12 7a5 5 0 1 0 0 10a5 5 0 1 0 0-10M12 11a1 1 0 1 0 0 2a1 1 0 1 0 0-2";   // v1.32.0
  KI.tren = "M12 2c3 2.5 4.5 6 4.5 10l-2 3h-5l-2-3c0-4 1.5-7.5 4.5-10zM12 9.5a1.5 1.5 0 1 0 0 .1M9.5 15l-3 3 .5 3 3-2M14.5 15l3 3-.5 3-3-2M10.5 18.5L12 22l1.5-3.5";   // v1.31.0
  KI.fm_mum = "M7 3v3M7 15v6M5 6h4v9H5zM17 3v5M17 17v4M15 8h4v9h-4z";   // v1.27.0
  KI.fm_grafik = "M3 18l5-7 4 4 4-9 5 8M3 21h18M8 11v.01M16 6v.01";   // v1.27.0
  const KF_L = {}; KF.forEach((G) => G.items.forEach(([id, l]) => { KF_L[id] = l; }));
  const KF_SHORT = { obt: "ORDER BLOCK", albunu: "AL BUNU", algo: "ALGO", skor: "D-A-K", olay: "OLAY", eik: "EN İYİ", tavan: "TAVAN", agresif: "AGRESİF", akis: "AKIŞ", baski: "BASKI", para: "PARA", radar: "RADAR", movers: "YÜKSELEN", hacim: "HACİM", radar_tavan: "TAVANA YAKIN", radar_taban: "TABANA YAKIN",
    tavanda: "TAVANDA", tabanda: "TABANDA", kurum: "KURUM", tahtaci: "TAHTACI", kurumuyari: "UYARILAR", gunsonu: "GÜN SONU", akd: "AKD", takas: "TAKAS", search: "ARA", derinlik: "DERİNLİK",
    islemler: "İŞLEMLER", kademe: "KADEME", sinyal: "SİNYAL", ai: "AI", endeks: "ENDEKS", sektor: "SEKTÖR", bildirim_ayar: "BİLDİRİM", derinlik_ayar: "DER. AYAR", bildirim_gecmis: "GEÇMİŞ", alarmlar: "ALARM", favs: "LİSTEM", about: "DURUM" };
  OPF.forEach(([f, l, sh]) => { KF_SHORT["op_" + f] = sh; });
  KCAT.forEach(([k, , sh]) => { KF_SHORT[k] = sh; });
  KF_SHORT.tren = "TRENE ATLA"; KF_SHORT.k_maliyet = "MALİYET↑"; KF_SHORT.akdt = "AKD TARA"; KF_SHORT.akk = "AKTİF KURUM";
  KF_SHORT.fm_mum = "MUM FORM."; KF_SHORT.fm_grafik = "GRAFİK FORM."; KF_SHORT.k_ciddi = "CİDDİ/TAVAN"; KF_SHORT.k_poc = "POC BASKI"; KF_SHORT.k_aort = "AORT BASKI";
  const STOCK_TABS = ["derinlik", "islemler", "akd", "kademe", "takas", "sinyal", "ai"];
  const PIN_MAX = 5, PIN_DEF = ["albunu", "op_29", "radar", "tavan", "agresif"];
  st.pins = (LS.get("navPins", null) || PIN_DEF).filter((id) => KF_L[id]).slice(0, PIN_MAX);
  if (!LS.get("ab_pin_v1340", 0)) { LS.set("ab_pin_v1340", Date.now()); if (!st.pins.includes("albunu") && st.pins.length < PIN_MAX) { st.pins.unshift("albunu"); LS.set("navPins", st.pins); } }   // v1.34.0 AL BUNU alt menüde (yer varsa)
  let kfEdit = false;
  function kfViewOf(id) {
    if (/^op_\d+$/.test(id)) return "op:" + id.slice(3);
    if (/^k_/.test(id)) return "op:" + id;
    if (id === "kademe") return "op:kademe";
    if (id === "sinyal") return "op:teknik";
    if (STOCK_TABS.includes(id)) return "stock:" + id;
    return { radar_tavan: "radar", radar_taban: "radar", tavanda: "tavan", tabanda: "tavan", gunsonu: "kurumuyari", sektor: "para", bildirim_ayar: "bildirim", derinlik_ayar: "bildirim", bildirim_gecmis: "bildirim", alarmlar: "bildirim", search: null, about: null }[id] ?? id;
  }
  function kfRun(id) {
    st.lastItem = id;
    if (/^op_\d+$/.test(id)) opOpen(+id.slice(3));
    else if (/^k_/.test(id)) opOpen(id);
    else if (id === "kademe") opOpen("kademe");
    else if (id === "sinyal") opOpen("teknik");
    else if (STOCK_TABS.includes(id)) { go("stock"); openTab(id, true); }
    else if (id === "radar_tavan" || id === "radar_taban") { rd.k = id === "radar_tavan" ? "ceil" : "floor"; if (rd.sort === "chg_desc") rd.sort = "ceil"; go("radar"); }
    else if (id === "tavanda" || id === "tabanda") { tt.k = id === "tavanda" ? "tavan" : "taban"; go("tavan"); setTimeout(() => { try { renderTT(); } catch (e) {} }, 400); }
    else if (id === "gunsonu") { go("kurumuyari"); setTimeout(() => { const b = document.querySelector('#ku-tab [data-t="rapor"]'); if (b) b.click(); }, 60); }
    else if (id === "sektor") { go("para"); setTimeout(() => { const s = $("pa-sec"); if (s) window.scrollTo(0, s.getBoundingClientRect().top + window.scrollY - 120); }, 700); }
    else if (id === "bildirim_ayar") nfOpen("ayar");
    else if (id === "derinlik_ayar") drSettings();
    else if (id === "bildirim_gecmis") nfOpen("gecmis");
    else if (id === "alarmlar") nfOpen("alarm");
    else if (id === "search") openSearch("all");
    else if (id === "about") { const b = document.querySelector('#menu [data-act="about"]'); if (b) b.click(); }
    else go(id);
    navActive();
  }
  function curKey() { const v = st.view === "movers" && st.mvMode === "volume" ? "hacim" : st.view; return v === "stock" ? "stock:" + st.tab : v === "op" ? "op:" + st.opId : v; }
  function navActive() {
    const btns = [...$("bnav").querySelectorAll("button[data-item]")];
    let act = null;
    if (st.kfOpen) act = "kesfet";
    else {
      const k = curKey();
      if (st.lastItem && st.pins.includes(st.lastItem) && kfViewOf(st.lastItem) === k) act = st.lastItem;
      else act = st.pins.find((id) => kfViewOf(id) === k) || (st.view === "stock" ? "home" : null);
    }
    btns.forEach((b) => b.classList.toggle("active", b.dataset.item === act));
  }
  function renderBnav() {
    const btn = (id, label, icon, aria) => `<button type="button" data-item="${id}" aria-label="${esc(aria || label)}">${P(KI[icon] || KI.home)}<span>${esc(label)}</span></button>`;
    $("bnav").innerHTML = btn("home", "ANA SAYFA", "home", "Ana sayfa") + st.pins.map((id) => btn(id, String(KF_SHORT[id] || trUpper(KF_L[id])).replace(/\//g, "/\u200b"), id, KF_L[id])).join("") + btn("kesfet", "KEŞFET", "kesfet", "Keşfet menüsü");
    navActive(); bnavFit();
  }
  // v1.26.4 — her öğenin adı simgesinin ALTINDA, her zaman; öğe sayısına göre yazı küçülür, sığmayan etiket (taşma/kesme yok)
  // önce iki satıra bölünür, gerekirse yazı boyutu 7 px'e kadar düşürülür.
  function bnavFit() {
    const nav = $("bnav"); if (!nav) return;
    const btns = [...nav.querySelectorAll("button")];
    nav.dataset.n = btns.length;
    const base = btns.length <= 5 ? 10 : btns.length === 6 ? 9.5 : 9;
    btns.forEach((b) => {
      const sp = b.querySelector("span"); if (!sp) return;
      let fs = base; sp.style.fontSize = fs + "px";
      while (fs > 7 && (sp.scrollWidth > b.clientWidth - 2 || sp.scrollHeight > fs * 2.3)) { fs -= 0.5; sp.style.fontSize = fs + "px"; }
    });
  }
  window.addEventListener("resize", () => { clearTimeout(bnavFit._t); bnavFit._t = setTimeout(bnavFit, 150); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(bnavFit);
  $("bnav").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-item]"); if (!b) return;
    const id = b.dataset.item;
    if (id === "kesfet") { st.kfOpen ? kfClose() : kfShow(); return; }
    if (st.kfOpen) kfClose();
    if (id === "home") { st.lastItem = null; go("stock"); } else kfRun(id);
  });
  function savePins() { st.pins = st.pins.slice(0, PIN_MAX); LS.set("navPins", st.pins); renderBnav(); }
  function togglePin(id) {
    const i = st.pins.indexOf(id);
    if (i >= 0) { st.pins.splice(i, 1); toast(`${KF_L[id]} alt menüden çıkarıldı`); }
    else if (st.pins.length >= PIN_MAX) { toast(`Alt menüye en fazla ${PIN_MAX} öğe eklenebilir — önce birini çıkarın`); return; }
    else { st.pins.push(id); toast(`${KF_L[id]} alt menüye eklendi ★`); }
    savePins(); kfRender();
  }
  function kfShow() {
    st.kfOpen = true; $("kesfet").hidden = false; document.body.classList.add("kf-open");
    $("btn-geri").innerHTML = `<span class="ico">✕</span> Kapat`; kfRender(); navActive(); abPeek();
    $("kesfet").querySelector(".kf-sheet").scrollTop = 0;
  }
  function kfClose() {
    st.kfOpen = false; kfEdit = false; $("kesfet").hidden = true; document.body.classList.remove("kf-open");
    $("btn-geri").innerHTML = `<span class="ico">&#8592;</span> Geri`; navActive();
  }
  function kfRender() {
    const q = fold($("kf-q").value.trim());
    $("kf-edit").textContent = kfEdit ? "Bitti" : "Düzenle"; $("kf-edit").classList.toggle("on", kfEdit);
    $("kf-pins").hidden = !kfEdit;
    if (kfEdit) {
      $("kf-pins").innerHTML = `<div class="kf-ph"><span>ALT MENÜ</span><span class="muted">${st.pins.length}/${PIN_MAX} · ⋮⋮ tutup sürükleyin</span></div>
        <div class="kf-pin fixed">${P(KI.home)}<span class="kf-pl">Ana Sayfa</span><small>sabit</small></div>` +
        st.pins.map((id, i) => `<div class="kf-pin" data-pin="${id}"><span class="kf-drag" aria-label="Sürükle">⋮⋮</span>${P(KI[id] || KI.home)}<span class="kf-pl">${esc(KF_L[id])}</span>
          <button type="button" data-mv="${i}:-1" ${i === 0 ? "disabled" : ""}>↑</button><button type="button" data-mv="${i}:1" ${i === st.pins.length - 1 ? "disabled" : ""}>↓</button><button type="button" class="kf-unpin" data-unpin="${id}">✕</button></div>`).join("") +
        (st.pins.length ? "" : `<div class="muted sm kf-none">Alt menü boş — aşağıdan ☆ ile ekleyin</div>`) +
        `<div class="kf-pin fixed">${P(KI.kesfet)}<span class="kf-pl">KEŞFET</span><small>sabit</small></div>`;
    }
    $("kf-groups").innerHTML = KF.map((G) => {
      const its = G.items.filter(([id, l]) => !q || fold(l).includes(q));
      if (!its.length) return "";
      if (G.hero && !kfEdit) return its.map(([id]) => `<button type="button" class="kf-hero" data-kf="${id}"><span class="kf-hero-ic">✅</span><span class="kf-hero-t"><b>AL BUNU</b><small>Tavan adayı · kurum fiyatı itiyor ve hâlâ itiyor — "ne alsam?" tek liste</small></span><span class="kf-hero-n" id="kf-ab-n">${abHeroN()}</span></button>`).join("");
      return `<div class="kf-gh"><span><i style="background:${G.dot}"></i>${G.g}</span><b>${its.length}</b></div><div class="kf-grid">` +
        its.map(([id, l, badge]) => {
          const pin = st.pins.includes(id);
          const right = kfEdit ? `<span class="kf-star ${pin ? "on" : ""}">${pin ? "★" : "☆"}</span>`
            : `${badge ? `<span class="kf-b ${badge === "CANLI" ? "live" : "new"}">${badge}</span>` : ""}${pin ? '<span class="kf-pinned">★</span>' : ""}`;
          return `<button type="button" class="kf-it ${G.col}" data-kf="${id}"><span class="kf-ic">${P(KI[id] || KI.home)}</span><span class="kf-l">${esc(l)}</span>${right}</button>`;
        }).join("") + `</div>`;
    }).join("") || `<div class="empty">Sonuç yok</div>`;
  }
  $("kf-q").addEventListener("input", kfRender);
  $("kf-edit").addEventListener("click", () => { kfEdit = !kfEdit; kfRender(); });
  // uzun bas = alt menüye ekle / çıkar
  let lpT = null, lpFired = false, lpXY = null;
  $("kf-groups").addEventListener("pointerdown", (e) => {
    const it = e.target.closest("[data-kf]"); if (!it) return;
    lpFired = false; lpXY = [e.clientX, e.clientY]; it.classList.add("press");
    clearTimeout(lpT); lpT = setTimeout(() => { lpFired = true; it.classList.remove("press"); try { navigator.vibrate && navigator.vibrate(30); } catch (x) {} togglePin(it.dataset.kf); }, 550);
  });
  const lpCancel = () => { clearTimeout(lpT); document.querySelectorAll("#kf-groups .press").forEach((x) => x.classList.remove("press")); };
  $("kf-groups").addEventListener("pointerup", lpCancel);
  $("kf-groups").addEventListener("pointercancel", lpCancel);
  $("kf-groups").addEventListener("pointermove", (e) => { if (lpXY && Math.hypot(e.clientX - lpXY[0], e.clientY - lpXY[1]) > 10) lpCancel(); });
  $("kf-groups").addEventListener("contextmenu", (e) => { if (e.target.closest("[data-kf]")) e.preventDefault(); });
  $("kf-groups").addEventListener("click", (e) => {
    const it = e.target.closest("[data-kf]"); if (!it) return;
    if (lpFired) { lpFired = false; return; }
    if (kfEdit) { togglePin(it.dataset.kf); return; }
    const id = it.dataset.kf; kfClose(); kfRun(id);
  });
  $("kf-pins").addEventListener("click", (e) => {
    const u = e.target.closest("[data-unpin]"); if (u) { togglePin(u.dataset.unpin); return; }
    const m = e.target.closest("[data-mv]"); if (m) { const [i, d] = m.dataset.mv.split(":").map(Number); const j = i + d; if (j < 0 || j >= st.pins.length) return; [st.pins[i], st.pins[j]] = [st.pins[j], st.pins[i]]; savePins(); kfRender(); }
  });
  // sürükle-bırak sıralama
  $("kf-pins").addEventListener("pointerdown", (e) => {
    const h = e.target.closest(".kf-drag"); if (!h) return;
    const pins = $("kf-pins"), row = h.closest(".kf-pin"); e.preventDefault();
    row.classList.add("dragging");
    const move = (ev) => {
      const rows = [...pins.querySelectorAll(".kf-pin[data-pin]")].filter((r) => r !== row);
      const nx = rows.find((r) => { const bb = r.getBoundingClientRect(); return ev.clientY < bb.top + bb.height / 2; });
      if (nx) pins.insertBefore(row, nx); else if (rows.length) rows[rows.length - 1].after(row);
    };
    const up = () => {
      window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); window.removeEventListener("pointercancel", up);
      row.classList.remove("dragging");
      st.pins = [...pins.querySelectorAll(".kf-pin[data-pin]")].map((r) => r.dataset.pin); savePins(); kfRender();
    };
    window.addEventListener("pointermove", move); window.addEventListener("pointerup", up); window.addEventListener("pointercancel", up);
  });
  renderBnav();
  st.kfReady = true;
  navActive();

  // ---- view loader hook (go → v120)
  function v120Open(view) {
    if (view === "radar") loadRadar();
    else if (view === "tavan") { loadCfg().then(() => { renderTTSet(); loadTT(); }); renderAlertFeeds(); }
    else if (view === "agresif") loadCfg().then(() => { renderAgSet(); loadAg(); });
    else if (view === "para") loadPara();
    else if (view === "kurumuyari") { loadCfg().then(() => { renderKuSet(); renderAlertFeeds(); }); loadKuBrokers(); }
    else if (view === "tahtaci") { $("th-broker").hidden = th.view !== "broker"; $("th-stock").hidden = th.view !== "stock"; loadTh(); }
  }
  loadCfg().then(() => pollAlerts());

  // ===================================================================== v1.21.0 ==
  // ---- OPERASYON TESPİTİ: 30 özellik + piyasa geneli Kademe Analizi / Teknik Sinyaller (tek genel tablo motoru)
  const OPS = { data: null, sort: null, dir: -1, q: "", n: 200, filt: "", sortFor: null, exp: {} };
  const OPF_L = {}; OPF.forEach(([f, l]) => { OPF_L[f] = l; });
  const OP_MK = { kademe: { t: "Kademe Analizi", ic: "kademe", filt: [["", "TÜMÜ"], ["alici", "NET ALICI"], ["satici", "NET SATICI"]] },
    teknik: { t: "Teknik Sinyaller", ic: "sinyal", filt: [["", "TÜMÜ"], ["AL", "AL"], ["SAT", "SAT"], ["TUT", "TUT"]] } };
  const PH_C = { T: "#22c55e", I: "#d4a64a", D: "#ef4444", N: "#3a4049" };
  const PH_L = { T: "T", I: "İ", D: "D", N: "N" };
  function opOpen(id) { st.opId = id; go("op"); }
  function opNumD(v) { const a = Math.abs(v); return Number.isInteger(v) || a >= 1000 ? 0 : a >= 100 ? 1 : 2; }
  function opCell(c, r) {
    const [k, , t] = c, v = r[k];
    if (t === "sym") return v ? `<td class="l sticky sym" data-sym="${esc(v)}">${esc(v)}</td>` : `<td class="l sticky">—</td>`;
    if (t === "broker") return `<td class="l kn">${v ? esc(brName(v)) : "—"}</td>`;
    if (t === "txt" || t === "time") return `<td class="${t === "txt" ? "l op-txt" : ""}">${v == null || v === "" ? (t === "txt" ? "" : "—") : esc(v)}</td>`;
    if (t === "px") return `<td>${fP(v)}</td>`;
    if (t === "lot") return `<td class="${k === "net" || k === "lf" || k === "tn" || k === "rnet" || k === "chg" || k === "w" || k === "m" || k === "mnet" || k === "msn" ? cls(v) : ""}">${fShort(v)}</td>`;
    if (t === "tl") return `<td class="${["ttl", "net", "ntl"].includes(k) ? cls(v) : ""}">${fShort(v)}</td>`;
    if (t === "chg") return `<td class="${cls(v)} b">${isNum(v) ? fPct(v, Math.abs(v) >= 100 ? 0 : 2) : "—"}</td>`;
    if (t === "pct") return `<td>${isNum(v) ? "%" + fN(v, 1) : "—"}</td>`;
    if (t === "score") { if (!isNum(v)) return `<td>—</td>`; const x = Math.max(0, Math.min(100, v)); return `<td><span class="th-sc"><i style="width:${x.toFixed(0)}%;background:hsl(${Math.round(x * 1.1)} 70% 45%)"></i><b>${fN(v, 0)}</b></span></td>`; }
    if (t === "strip") return `<td class="l"><span class="op-ph">${String(v || "").split("").map((ch, i, a) => `<i style="background:${PH_C[ch] || "#333"}" class="${i === a.length - 1 ? "now" : ""}">${PH_L[ch] || ch}</i>`).join("")}</span></td>`;
    if (t === "kmdr") return `<td class="l">${String(v || "—").split(" · ").map((x) => `<span class="km-bd ${x === "ISRARCI" ? "isr" : /SERT/.test(x) ? "sert" : /DÜŞÜREREK/.test(x) ? "dus" : /SABİT/.test(x) ? "sab" : "yuk"}">${esc(x)}</span>`).join("")}</td>`;
    if (t === "chk") return chkCell(r, v);   // v1.24.0
    if (t === "sen") return senCell(v);
    if (t === "verdict") { const vk = r.vk || ""; return `<td class="l"><span class="op-vd ${vk === "AL" ? "al" : vk === "SAT" ? "sat" : "tut"}">${esc(v || "—")}</span></td>`; }
    return `<td>${isNum(v) ? fN(v, opNumD(v)) : v == null ? "—" : esc(v)}</td>`;
  }
  function opRowsFiltered() {
    const d = OPS.data; if (!d) return [];
    let rows = d.rows || [];
    const q = st.opId === "k_kurumfiyat" ? "" : fold(OPS.q.trim());
    if (q) rows = rows.filter((r) => fold(r.s || "").includes(q) || fold(r.n || "").includes(q) || fold(brName(r.b || r.br || r.a || r.tb || r.xb || "")).includes(q) || fold(brName(r.a || "")).includes(q));
    if (st.opId === "kademe" && OPS.filt) rows = rows.filter((r) => OPS.filt === "alici" ? (r.net || 0) > 0 : (r.net || 0) < 0);
    if (st.opId === "teknik" && OPS.filt) rows = rows.filter((r) => r.vk === OPS.filt);
    if (OPS.sort) {
      const k = OPS.sort, dir = OPS.dir;
      const col = (d.cols || []).find((c) => c[0] === k);
      const sk = col && col[3] ? col[3] : k;   // v1.23.1: metin sütunu için sayısal sıralama anahtarı (ör. yy → yyv)
      const str = col && !col[3] && ["sym", "txt", "broker", "time", "strip", "verdict", "kmdr", "sen"].includes(col[2]);
      const ckn = col && col[2] === "chk" ? (z) => (Array.isArray(z) ? z.filter((q) => q[1] === 1).length : null) : null;
      rows = [...rows].sort((a, b) => {
        const x = ckn ? ckn(a[sk]) : a[sk], y = ckn ? ckn(b[sk]) : b[sk];
        if (str) return dir * String(x ?? "").localeCompare(String(y ?? ""), "tr");
        const xn = isNum(x), yn = isNum(y);
        if (!xn && !yn) return 0; if (!xn) return 1; if (!yn) return -1;
        return dir * (x - y);
      });
    }
    return rows;
  }
  function opStripCenter(id) { if (OPS._stripId === id) return; OPS._stripId = id; requestAnimationFrame(() => hCenter($("op-strip").querySelector(".on"))); }
  function opHeader() {
    const id = st.opId, d = OPS.data || {}, mk = OP_MK[id];
    if (isK(id)) { kHeader(id, d); return; }
    $("op-q").placeholder = "Hisse / kurum ara...";
    $("op-title").textContent = mk ? mk.t : (OPF_L[id] || d.title || "Operasyon");
    $("op-sub").textContent = mk ? "Tüm BIST payları · tek tablo" : `OPERASYON TESPİTİ · ${OPF.findIndex(([f]) => f === id) + 1}/30`;
    $("op-ic").innerHTML = `<svg viewBox="0 0 24 24" width="22" height="22"><path d="${mk ? KI[mk.ic] : OPI[id] || OPI[29]}" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    setH($("op-strip"), mk ? Object.keys(OP_MK).map((k) => `<button type="button" class="op-chip ${k === id ? "on" : ""}" data-opgo="${k}">${OP_MK[k].t}</button>`).join("")
      : OPF.map(([f, , sh]) => `<button type="button" class="op-chip ${f === id ? "on" : ""}" data-opgo="${f}">${esc(sh)}</button>`).join(""));
    opStripCenter(id);
    const fl = $("op-filt");
    if (mk) { fl.hidden = false; setH(fl, mk.filt.map(([v, l]) => `<button type="button" data-f="${v}" class="${OPS.filt === v ? "active" : ""}">${l}${d.counts && d.counts[v] != null ? " " + d.counts[v] : ""}</button>`).join("")); }
    else { fl.hidden = true; setH(fl, ""); }
  }
  async function opLoad(quiet) {
    const id = st.opId;
    if (OPS.sortFor !== id) { OPS.data = null; OPS.sort = null; OPS.dir = -1; OPS.q = ""; OPS.filt = ""; OPS.n = (OP_MK[st.opId] ? 100000 : 200); OPS.exp = {}; $("op-q").value = ""; OPS.sortFor = id; OPS.w = null; OPS.wSet = false; OPS.kq = ""; OPS.kdate = ""; OPS.ktok = ""; }
    if (OPS.pendW) { OPS.w = OPS.pendW; OPS.wSet = true; OPS.pendW = null; OPS.ktok = ""; }   // v1.24.0: Özet çipinden belirli pencereye
    if (OPS.pendS) { const P = OPS.pendS; OPS.pendS = null; if (P.w) { OPS.w = P.w; OPS.wSet = true; } OPS.sort = P.sort || null; OPS.dir = P.dir || -1; OPS.filt = P.filt || ""; if (P.date) OPS.kdate = P.date; OPS.ktok = ""; OPS.n = (OP_MK[id] ? 100000 : 200); }   // v1.29.0 En İyi Koşul
    opHeader();
    if (!quiet || !OPS.data) {
      if (!OPS.data) { $("op-body").innerHTML = `<tr><td class="empty">Yükleniyor…</td></tr>`; $("op-head").innerHTML = ""; $("op-foot").innerHTML = ""; $("op-info").innerHTML = `<div class="empty">Yükleniyor…</div>`; $("op-special").innerHTML = ""; $("op-extra").innerHTML = ""; }
    }
    const url = isK(id) ? kUrl(id) : OP_MK[id] ? `/api/op/mk/${id}` : `/api/op/f/${id}`;
    try {
      const d = await api(url, { timeout: 25000 });
      if (st.opId !== id) return;
      if (d && d.same) return;   // v1.23.0: sunucuda değişiklik yok → tabloya dokunma
      if (isKD(id)) OPS.ktok = d.tok || "";
      if (isK(id) && d.w && !OPS.wSet) OPS.w = d.w;
      OPS.data = d; opRender();
    } catch (e) { if (!OPS.data) $("op-body").innerHTML = `<tr><td class="empty">Veri alınamadı (${esc(e.message || e)})</td></tr>`; }
  }
  function opRender() {
    const d = OPS.data; if (!d) return;
    const id = st.opId;
    opHeader();
    const stTxt = d.pending ? "HESAPLANIYOR" : d.status === "tam" ? "TAM" : d.status === "hata" ? "HATA" : "KISMİ";
    setH($("op-info"), `<div class="op-desc">${esc(d.desc || "")}</div>
      <div class="op-badges"><span class="op-b ${d.status === "tam" ? "ok" : "warn"}">${stTxt}</span>${d.hist ? `<span class="op-b hist">${esc(d.hist)}</span>` : (d.hist_days != null ? `<span class="op-b hist">veri biriktiriliyor (${d.hist_days} gün)</span>` : "")}
      <span class="op-b">${fN(d.count || 0)} satır</span><span class="op-b">⟳ ${esc(d.updated || d.computed_at || "—")}</span>${d.weight ? `<span class="op-b">skor ağırlığı ${d.weight}</span>` : ""}</div>
      ${d.nt && NT[d.nt] ? `<div class="op-nt">${ntRow(d.nt, true)}${OS_FEAT[d.nt] ? `<button type="button" class="btn-ghost sm" data-ostest="${esc(OS_FEAT[d.nt])}">✈️ Telegram Test</button>` : ""}${d.nt2 && NT[d.nt2] ? ntRow(d.nt2, true) + `<button type="button" class="btn-ghost sm" data-ostest="${esc(OS_FEAT[d.nt2] || "")}">✈️ Telegram Test</button>` : ""}<button type="button" class="btn-ghost sm nf-lnk" data-nflink="ayar">🔔 Tüm bildirim ayarları</button></div>` : ""}`);
    // özel görünümler
    let sp = "";
    if (id === 20 && d.graph) sp = opGraph(d.graph, d.clusters || []);
    if (id === 30) sp = `<div class="card op-legend"><span><i style="background:${PH_C.T}"></i>Toplama</span><span><i style="background:${PH_C.I}"></i>İtme</span><span><i style="background:${PH_C.D}"></i>Dağıtım</span><span><i style="background:${PH_C.N}"></i>Nötr</span><span class="muted sm">Satıra dokun → hissenin OPERASYON sekmesi</span></div>`;
    if (id === 29) sp = `<div class="card op-legend"><span class="muted sm">▸ ile puan dökümünü açın · satıra dokunun → hisse</span></div>`;
    if (isK(id)) sp = kSpecial(d);
    setH($("op-special"), sp);
    setH($("op-extra"), (d.tables || []).map((T, ti) => `<div class="card tbl-card"><div class="card-h" style="padding:8px 8px 0"><span class="card-title">${esc(T.title)}</span></div><div class="tbl-scroll"><table class="grid-table op-table">
      <thead><tr>${T.cols.map((c, i) => `<th class="${i === 0 ? "l sticky" : ""}">${esc(trUpper(c[1]))}</th>`).join("")}</tr></thead>
      <tbody>${T.rows.map((r) => `<tr data-row-sym="${esc(r.s || "")}">${T.cols.map((c, i) => i === 0 && c[2] !== "sym" ? `<td class="l sticky b">${esc(r[c[0]] ?? "—")}</td>` : opCell(c, r)).join("")}</tr>`).join("")}</tbody></table></div></div>`).join(""));
    const cols = d.cols || [];
    const exp = id === 29;
    setH($("op-head"), `<tr>${exp ? `<th class="op-x"></th>` : ""}${cols.map((c, i) => `<th data-k="${esc(c[0])}" class="${c[2] === "sym" || i === 0 ? "l sticky" : ["txt", "broker", "strip", "verdict", "kmdr", "chk", "sen"].includes(c[2]) ? "l" : ""} ${OPS.sort === c[0] ? "sorted" + (OPS.dir > 0 ? " asc" : "") : ""}">${esc(trUpper(c[1]))}</th>`).join("")}</tr>`);
    const rows = opRowsFiltered();
    setH($("op-body"), rows.slice(0, OPS.n).map((r, i) => {
      const key = r.s || r.br || (r.a + "|" + r.b) || i;
      let h = `<tr data-row-sym="${esc(r.s || "")}"${id === "k_maliyet" ? ` data-row-br="${esc(r.br || "")}" class="km-row"` : isB(id) ? ` data-row-ref="${id === "k_ciddi" ? (/POC/.test(r.kay || "") ? "k_poc" : "k_aort") : id}" class="km-row"` : ""}>${exp ? `<td class="op-x"><button type="button" data-exp="${esc(key)}">${OPS.exp[key] ? "▾" : "▸"}</button></td>` : ""}${cols.map((c, ci) => ci === 0 && c[2] !== "sym" ? (c[2] === "broker" ? `<td class="l sticky kn">${esc(brName(r[c[0]] || "—"))}</td>` : `<td class="l sticky">${esc(r[c[0]] ?? "—")}</td>`) : opCell(c, r)).join("")}</tr>`;
      if (exp && OPS.exp[key] && r.parts) h += `<tr class="op-bd"><td colspan="${cols.length + 1}">${opParts(r.parts)}</td></tr>`;
      if (Array.isArray(r.ck) && OPS.exp["ck:" + ckKey(r)]) h += `<tr class="op-bd"><td colspan="${cols.length + (exp ? 1 : 0)}">${ckList(r.ck)}</td></tr>`;   // v1.24.0
      return h;
    }).join("") || `<tr><td colspan="${cols.length + 1}" class="empty">${d.pending ? "Hesaplanıyor…" : "Şu an bu kritere uyan hisse yok"}</td></tr>`);
    const T = d.total;
    setH($("op-foot"), T ? `<tr>${cols.map((c, i) => i === 0 ? `<td class="l sticky">TOPLAM</td>` : c[0] === "n" ? `<td></td>` : (T[c[0]] != null ? opCell(c, T) : "<td></td>")).join("")}</tr>` : "");
    $("op-more").hidden = rows.length <= OPS.n; $("op-more").textContent = `Daha fazla göster (+${fN(rows.length - OPS.n)})`;
    setH($("op-note"), `${esc(d.note || "")}`);
    if (isK(id)) kAfterRender(d);
  }
  function opParts(parts) {
    return `<div class="op-parts">${parts.map((p) => `<div class="op-pt" data-opgo="${p.f}"><span class="op-ptl">${esc(p.t)}</span><span class="op-ptb"><i style="width:${Math.min(100, p.st)}%"></i></span><b>+${fN(p.pts, 1)}</b><small>${esc(p.txt || "")} · ağırlık ${p.w} × güç %${p.st}</small></div>`).join("")}</div>`;
  }
  function opGraph(g, clusters) {
    const N = g.nodes || []; if (!N.length) return "";
    const W = 380, H = 380, cx = W / 2, cy = H / 2, R = 150;
    const pos = {}; const mx = Math.max(...N.map((n) => n.tl || 1));
    const ord = [...N].sort((a, b) => (a.c || 99) - (b.c || 99));
    ord.forEach((n, i) => { const a = (i / ord.length) * Math.PI * 2 - Math.PI / 2; pos[n.id] = [cx + R * Math.cos(a), cy + R * Math.sin(a)]; });
    const col = (c) => c ? `hsl(${(c * 67) % 360} 65% 55%)` : "#6b7280";
    const E = (g.edges || []).map((e) => { const a = pos[e.a], b = pos[e.b]; if (!a || !b) return ""; return `<line x1="${a[0].toFixed(1)}" y1="${a[1].toFixed(1)}" x2="${b[0].toFixed(1)}" y2="${b[1].toFixed(1)}" stroke="rgba(212,166,74,${Math.min(0.9, (e.w || 0) / 100).toFixed(2)})" stroke-width="${(1 + (e.w || 0) / 30).toFixed(1)}"/>`; }).join("");
    const V = N.map((n) => { const p = pos[n.id]; const r = 4 + 9 * Math.sqrt((n.tl || 0) / mx); const lx = p[0] + (p[0] < cx ? -r - 3 : r + 3); return `<circle cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="${r.toFixed(1)}" fill="${col(n.c)}"/><text x="${lx.toFixed(1)}" y="${(p[1] + 3).toFixed(1)}" font-size="9" fill="#cbd5e1" text-anchor="${p[0] < cx ? "end" : "start"}">${esc(brName(n.id).slice(0, 16))}</text>`; }).join("");
    return `<div class="card"><div class="card-h"><span class="card-title">KURUM ORTAKLIK GRAFİĞİ</span><span class="muted">${clusters.length} küme</span></div>
      <svg viewBox="-40 0 ${W + 80} ${H}" class="op-graph">${E}${V}</svg>
      <div class="muted sm">${clusters.map((c, i) => `<span class="op-cl"><i style="background:${col(i + 1)}"></i>${c.map(brName).join(", ")}</span>`).join("") || "Benzerlik ≥%35 küme yok"}</div></div>`;
  }
  $("op-strip").addEventListener("click", (e) => { const b = e.target.closest("[data-opgo]"); if (!b) return; const v = b.dataset.opgo; opOpen(/^\d+$/.test(v) ? +v : v); });
  // ---- v1.22.0 KADEME & ŞERİT ANALİZİ (op görünümünü paylaşır: st.opId = "k_...")
  function isK(id) { return typeof id === "string" && /^k_/.test(id); }
  function kUrl(id) { const p = new URLSearchParams(); if (OPS.wSet && OPS.w) p.set("w", OPS.w); if ((id === "k_kurumfiyat" || id === "k_maliyet") && OPS.kq) p.set("q", OPS.kq); if (isKD(id)) { if (OPS.kdate) p.set("date", OPS.kdate); if (OPS.ktok && OPS.data) p.set("tok", OPS.ktok); } const qs = p.toString(); return `/api/k/f/${id}${qs ? "?" + qs : ""}`; }
  function kHeader(id, d) {
    if (id === "k_maliyet") return kmHeader(d);
    if (isB(id)) return bHeader(id, d);   // v1.24.0
    const i = KCAT.findIndex(([k]) => k === id);
    $("op-title").textContent = KCAT_L[id] || d.title || "Kademe & Şerit";
    $("op-sub").textContent = `KADEME & ŞERİT ANALİZİ · ${i + 1}/${KCAT.length} · tüm BIST payları`;
    $("op-ic").innerHTML = `<svg viewBox="0 0 24 24" width="22" height="22"><path d="${KI[id] || KI.kademe}" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    setH($("op-strip"), KCAT.map(([k, , sh]) => `<button type="button" class="op-chip ${k === id ? "on" : ""}" data-opgo="${k}">${esc(sh)}</button>`).join(""));
    opStripCenter(id);
    const fl = $("op-filt"), W = d.windows || null;
    if (W && W.length) { fl.hidden = false; const cur = OPS.wSet ? OPS.w : (d.w || OPS.w); setH(fl, W.map(([v, l]) => `<button type="button" data-kw="${v}" class="${cur === v ? "active" : ""}">${esc(l)}</button>`).join("")); }
    else { fl.hidden = true; setH(fl, ""); }
    $("op-q").placeholder = id === "k_kurumfiyat" ? "Hisse kodu (tüm kurumlar) veya kurum adı yazın..." : "Hisse / kurum ara...";
  }
  const K_HELP_L = [["ne", "Ne işe yarar?"], ["nasil", "Nasıl hesaplanır?"], ["nasil_kullan", "Nasıl kullanılır?"], ["dikkat", "Dikkat edilmesi gerekenler"], ["ornek", "Örnek"]];
  function kSpecial(d) {
    if (st.opId === "k_maliyet") return kmSpecial(d);
    if (isB(st.opId)) return bSpecial(d);   // v1.24.0
    const H = d.help || {};
    const open = LS.get("kHelpOpen", false);
    const mode = d.mode === "kayıt" ? `<span class="op-b warn">KAYITLI GÜN · ${esc(d.day_label || d.day || "")}</span>` : d.live ? `<span class="op-b ok">CANLI</span>` : `<span class="op-b warn">SEANS DIŞI</span>`;
    return `<div class="card k-help ${open ? "open" : ""}"><button type="button" class="k-help-h" data-khelp="1"><span>ℹ️ AÇIKLAMA · NASIL ÇALIŞIR?</span><b>${open ? "▾" : "▸"}</b></button>
      <div class="k-help-b">${K_HELP_L.filter(([k]) => H[k]).map(([k, l]) => `<div class="k-hs"><div class="k-hl">${l}</div><div class="k-ht">${esc(H[k])}</div></div>`).join("")}</div></div>
      <div class="k-meta">${mode}<span class="op-b">${fN(d.universe || 0)} hisse tarandı</span>${d.depth_based ? `<span class="op-b">derinlik tabanlı</span>` : ""}${d.replay ? `<span class="op-b hist">günün en güçlü anları</span>` : ""}<span class="op-b">⟳ ~4 sn</span></div>`;
  }
  // ---- v1.23.0 MALİYET YÜKSELTEN KURUMLAR (Kurum Ayak İzi) — op görünümünü paylaşır (st.opId = "k_maliyet")
  const kmP = (v) => (isNum(v) && v !== 0 ? nf(v < 10 ? 4 : v < 100 ? 3 : 2).format(v) : "—");
  const kmHms = (t) => { t = Math.max(0, Math.round(t || 0)); return `${String(Math.floor(t / 3600)).padStart(2, "0")}:${String(Math.floor((t % 3600) / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`; };
  function kmHeader(d) {
    $("op-title").textContent = "Maliyet Yükselten Kurumlar (Kurum Ayak İzi)";
    $("op-sub").textContent = `KURUM ANALİZİ · işlem işlem, saniye saniye · tüm BIST payları${d.day_label ? " · " + d.day_label : ""}`;
    $("op-ic").innerHTML = `<svg viewBox="0 0 24 24" width="22" height="22"><path d="${KI.k_maliyet}" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    setH($("op-strip"), `<button type="button" class="op-chip on" data-opgo="k_maliyet">MALİYET↑ · KURUM AYAK İZİ</button>`);
    const fl = $("op-filt"), W = d.windows || null;
    if (W && W.length) { fl.hidden = false; const cur = OPS.wSet ? OPS.w : (d.w || OPS.w); setH(fl, W.map(([v, l]) => `<button type="button" data-kw="${v}" class="${cur === v ? "active" : ""}">${esc(l)}</button>`).join("")); }
    else { fl.hidden = true; setH(fl, ""); }
    $("op-q").placeholder = "Hisse veya kurum ara (tüm satırlarda)...";
  }
  const KMG = LS.get("kmGuide", { "Adım adım kullanım (önerilen akış)": true });
  function kmLine(x) {
    let h = esc(brName(x));
    h = h.replace(/^(•\s*)([^:—]{2,70}?)(:| —)/, "$1<b>$2</b>$3").replace(/^(\d+\))/, "<b>$1</b>");
    return `<div class="km-gl ${/^\d+\)/.test(x) ? "step" : ""}">${h}</div>`;
  }
  function kmGuide(H) {
    const sec = (t, lines) => `<details class="km-gd" data-kmg="${esc(t)}" ${KMG[t] ? "open" : ""}><summary>${esc(t)}</summary><div class="km-gb">${lines.map(kmLine).join("")}</div></details>`;
    return `${H.ne ? `<div class="k-hs"><div class="k-hl">Ne işe yarar?</div><div class="k-ht">${esc(H.ne)}</div></div>` : ""}
      <div class="k-hl km-gh">📘 NASIL KULLANMALIYIM? · başlıklara dokunarak açın/kapatın</div>
      ${(H.guide || []).map((g) => sec(g.t, g.p || [])).join("")}
      ${H.nasil_kullan ? sec("Kısa özet", [H.nasil_kullan]) : ""}${H.ornek ? sec("Örnek (bu seans)", [H.ornek]) : ""}`;
  }
  $("op-special").addEventListener("toggle", (e) => { const g = e.target.closest && e.target.closest("[data-kmg]"); if (!g) return; KMG[g.dataset.kmg] = g.open; LS.set("kmGuide", KMG); }, true);
  function kmSpecial(d) {
    const H = d.help || {};
    const open = LS.get("kHelpOpen", false);
    const sel = OPS.kdate || d.day || "";
    const mode = d.live ? `<span class="op-b ok">CANLI SEANS · ${esc(d.day_label || "")}</span>` : `<span class="op-b warn">GÖSTERİLEN SEANS: ${esc(d.day_label || d.day || "—")}${OPS.kdate ? "" : " (son seans)"}</span>`;
    const dates = (d.dates || []).map((x) => `<button type="button" data-kdate="${esc(x.d)}" class="${x.d === sel ? "active" : ""}">${esc(x.live ? "BUGÜN · CANLI" : x.l)}</button>`).join("");
    return `<div class="card k-help ${open ? "open" : ""}"><button type="button" class="k-help-h" data-khelp="1"><span>ℹ️ AÇIKLAMA · NASIL KULLANMALIYIM?</span><b>${open ? "▾" : "▸"}</b></button>
      <div class="k-help-b">${kmGuide(H)}</div></div>
      <div class="km-dates"><span class="muted sm">SEANS:</span>${dates}</div>
      <div class="k-meta">${mode}<span class="op-b">${fN(d.universe || 0)} hisse tarandı</span>${d.ref ? `<span class="op-b">referans ${esc(d.ref)}</span>` : ""}<span class="op-b">aktif/pasif işlem bazında</span><span class="op-b hist">satıra dokun → saniye saniye maliyet grafiği</span></div>`;
  }
  $("op-special").addEventListener("click", (e) => { const b = e.target.closest("[data-kdate]"); if (!b || !isKD(st.opId)) return; const v = b.dataset.kdate; const live = OPS.data && OPS.data.dates && OPS.data.dates.find((x) => x.d === v && x.live); OPS.kdate = live ? "" : v; OPS.ktok = ""; OPS.data = null; opLoad(); });
  document.addEventListener("click", (e) => { const b = e.target.closest("[data-ostest]"); if (!b) return; e.preventDefault(); osFeatureTest(b.dataset.ostest); });

  const KM = { sym: null, br: null, d: null, rng: "buy", n: 400, flt: "all", gen: 0, tm: null };
  function kmOv() {
    let ov = $("km-ov");
    if (!ov) {
      ov = document.createElement("div"); ov.id = "km-ov"; ov.className = "km-ov"; ov.hidden = true;
      ov.innerHTML = `<div class="km-box" role="dialog" aria-modal="true"><div class="km-top"><div class="km-tt"><b id="km-title"></b><small id="km-sub"></small></div><button type="button" class="btn-ghost sm" data-km="stock">Hisse →</button><button type="button" class="km-x" data-km="close" aria-label="Kapat">✕</button></div>
        <div id="km-kpi"></div><div id="km-rng" class="km-rng"></div><div class="km-chart" id="km-chart"></div><div id="km-leg" class="km-leg"></div><div id="km-hh"></div><div id="km-chk"></div><div id="km-tbl"></div></div>`;
      document.body.appendChild(ov);
      ov.addEventListener("click", kmClick);
      ov.querySelector("#km-chart").addEventListener("pointermove", kmTip);
      ov.querySelector("#km-chart").addEventListener("pointerleave", () => { const t = $("km-tip"); if (t) t.hidden = true; });
    }
    return ov;
  }
  function kmOpen(sym, br, day) {
    Object.assign(KM, { sym, br, day: day || null, d: null, rng: "buy", n: 400, flt: "all" }); KM.gen++;
    const ov = kmOv(); ov.hidden = false; document.body.classList.add("km-lock");
    $("km-title").textContent = `${sym} · ${brName(br)}`; $("km-sub").textContent = "Yükleniyor…";
    ["km-kpi", "km-rng", "km-chart", "km-leg", "km-hh", "km-chk", "km-tbl"].forEach((k) => { const el = $(k); el.innerHTML = ""; el._h = null; });
    $("km-chart").innerHTML = `<div class="empty">İşlemler yükleniyor…</div>`;
    ov.querySelector(".km-box").scrollTop = 0;
    kmLoad();
    clearInterval(KM.tm); KM.tm = setInterval(() => { if (!document.hidden && KM.d && KM.d.live && !$("km-ov").hidden) kmLoad(true); }, 10000);
  }
  function kmClose() { const ov = $("km-ov"); if (ov) ov.hidden = true; document.body.classList.remove("km-lock"); clearInterval(KM.tm); KM.gen++; }
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && $("km-ov") && !$("km-ov").hidden) kmClose(); });
  window.addEventListener("resize", () => { if (KM.d && $("km-ov") && !$("km-ov").hidden) kmChart(); });
  async function kmLoad(quiet) {
    const g = KM.gen, p = new URLSearchParams({ sym: KM.sym, br: KM.br });
    const day = KM.day || OPS.kdate || (OPS.data && OPS.data.day) || ""; if (day) p.set("date", day);
    try {
      const d = await api(`/api/k/maliyet/detail?${p.toString()}`, { timeout: 25000 });
      if (g !== KM.gen) return;
      if (d.error) { $("km-sub").textContent = d.error; $("km-chart").innerHTML = `<div class="empty">${esc(d.error)}</div>`; return; }
      KM.d = d; kmPrep(d); kmRender();
    } catch (e) { if (!quiet && g === KM.gen) $("km-chart").innerHTML = `<div class="empty">Detay alınamadı (${esc(e.message || e)})</div>`; }
  }
  function kmPrep(d) {
    d.buys = d.tr.filter((x) => x[3] === "A"); d.sells = d.tr.filter((x) => x[3] === "S");
    d.maxL = Math.max(1, ...d.buys.map((x) => x[2]));
  }
  function kmRange() {
    const d = KM.d, px = d.px; if (!px.length) return [0, 1];
    const T0 = px[0][0], T1 = px[px.length - 1][0], b = d.buys;
    if (!b.length || KM.rng === "all") return [T0, T1];
    if (KM.rng === "buy") return [Math.max(T0, b[0][0] - 120), Math.min(T1, b[b.length - 1][0] + 120)];
    if (KM.rng === "first") return [Math.max(T0, b[0][0] - 300), Math.min(T1, b[0][0] + 3600)];
    if (KM.rng === "last") return [Math.max(T0, T1 - 3600), T1];
    return [T0, T1];
  }
  function kmRender() {
    const d = KM.d, r = d.row || {};
    $("km-title").textContent = `${d.sym} · ${brName(d.br)}`;
    $("km-sub").textContent = `${d.day_label}${d.live ? " · CANLI" : " · kayıtlı seans"} · ${fN(d.buys.length)} alış, ${fN(d.sells.length)} satış · hissede toplam ${fN(d.n_all)} işlem · kayıt başlangıcı ${d.rec_from || "—"}`;
    const k = (l, v, c = "") => `<div class="km-k"><small>${l}</small><b class="${c}">${v}</b></div>`;
    const b0 = d.buys[0];
    setH($("km-kpi"), `<div class="km-kpis">
      ${k("GÜNLÜK DEĞ. %", fPct(isNum(r.gd) ? r.gd : d.gd), cls(isNum(r.gd) ? r.gd : d.gd))}
      ${k("ISRAR SKORU", r.israr != null ? `${r.israr}/100` : "—", r.israr >= 70 ? "pos" : "")}
      ${k("YÜKSELTME YAYILIMI", r.yy ? `${esc(r.yy)} · en yoğun %${fN(r.yk, 0)}` : "—")}
      ${k("İLK AYAK İZİ", b0 ? `${kmHms(b0[0])} · ${kmP(b0[1])} ₺ · ${fN(b0[2])} lot` : "—")}
      ${k("İLK 10 ALIŞ ORT.", kmP(r.c1))}${k("AÇILIŞ SAATİ ORT.", r.oh ? kmP(r.oh) : "—")}
      ${k("ŞU ANKİ MALİYET", kmP(r.cur || d.buy_avg))}${k("SON ALIŞ FİYATI", kmP(r.lp))}
      ${k("MALİYET ARTIŞI", fPct(r.chg), cls(r.chg))}${k("İLK 10'DAN", fPct(r.chgN), cls(r.chgN))}
      ${k("YÜKSELTME", r.ys != null ? `${fN(r.ys)} / ${fN(r.nb)} alış · ${fN(r.yh)} yeni zirve` : "—")}
      ${k("AKTİF ALIŞ", r.akt != null ? "%" + fN(r.akt, 1) : "—")}${k("AKTİF SERİ / SÜPÜRME", r.seri != null ? `${fN(r.seri)} / ${fN(r.sw)}` : "—")}
      ${k("EN BÜYÜK ALIŞ", r.big ? `${fN(r.big)} lot @ ${kmP(r.bigp)} · ${esc(r.bigt)}` : "—")}
      ${k("NET LOT", r.net != null ? fN(r.net) : "—", cls(r.net))}${k("ALIŞ / SATIŞ ₺", r.btl != null ? `${fShort(r.btl)} / ${fShort(r.stl)}` : "—")}
      ${k("HACİM PAYI", r.pay != null ? "%" + fN(r.pay, 2) : "—")}${k("YÜKSELİŞE KATKI", r.up != null ? "%" + fN(r.up, 1) : "—")}
      ${k("FİYAT ETKİSİ 10 SN / 60 SN", `${fPct(r.i10, 3)} / ${fPct(r.i60, 3)}`)}
      ${k("SÜRE · ALIŞ DK · SN", r.span ? `${esc(r.span)} · ${fN(r.dk)} dk · ${fN(r.sn)} sn` : "—")}
      ${k("SON ALIŞ", esc(r.lt || "—"))}${k("HÂLÂ ALIYOR", esc(r.still || "—"), r.still && r.still !== "—" ? "pos" : "")}
      ${k("CİDDİYET SKORU", r.sc != null ? `${r.sc}/100` : "listede değil", r.sc >= 70 ? "pos" : "")}${k("DURUM", esc(r.dr || "—"))}</div>`);
    const R = [["buy", "ALIŞ DÖNEMİ"], ["all", "TÜM GÜN"], ["first", "İLK AYAK İZİ +60 DK"], ["last", "SON 60 DK"]];
    setH($("km-rng"), R.map(([v, l]) => `<button type="button" data-kmr="${v}" class="${KM.rng === v ? "active" : ""}">${l}</button>`).join(""));
    setH($("km-leg"), `<span><i class="ln px"></i>Hisse fiyatı (saniye saniye)</span><span><i class="ln av"></i>Kümülatif ortalama maliyet</span><span><i class="dt ak"></i>Aktif alış (lot büyüklüğünde)</span><span><i class="dt ps"></i>Pasif alış</span><span><i class="dt ry"></i>Maliyet yükseltme</span><span><i class="dt rz"></i>Yeni zirve alış</span><span><i class="dt sl"></i>Satış</span>`);
    setH($("km-hh"), kmHalfHours(d));
    const a = d.akd;
    const netCost = r.net > 0 && r.btl != null ? (r.btl - r.stl) / r.net : null;
    setH($("km-chk"), `<div class="km-chk">✔ Kontrol: işlem kayıtlarından alış ortalaması <b>${kmP(d.buy_avg)} ₺</b>${netCost ? ` · net maliyet (alış ₺ − satış ₺) ÷ net lot <b>${kmP(netCost)} ₺</b>` : ""}${a ? ` · AKD (İdealData) maliyet <b>${kmP(a.cost)} ₺</b>, AKD net <b>${fN(a.net)}</b> lot${r.net ? ` (kayıt: ${fN(r.net)})` : ""}` : " · AKD verisi yok"}. Kayıt başlangıcı: ${esc(d.rec_from || "—")} (bu saatten itibaren tam${(d.gaps || []).length ? `, ${d.gaps.length} boşluk` : ""}).</div>`);
    kmChart(); kmTable();
  }
  function kmHalfHours(d) {   // v1.23.1: yarım saat şeridi — yükseltmeler gün boyuna mı yayılmış, tek yerde mi kümelenmiş
    const B = d.buys; if (!B.length) return "";
    const wOf = (t) => Math.max(0, Math.floor((t - 36000) / 1800));
    const nb = {}, nr = {};
    B.forEach((x) => { const w = wOf(x[0]); nb[w] = (nb[w] || 0) + 1; if (x[8]) nr[w] = (nr[w] || 0) + 1; });
    const ws = Object.keys(nb).map(Number), w0 = Math.min(...ws), w1 = Math.max(...ws), mx = Math.max(1, ...Object.values(nr));
    let cells = "", act = 0;
    for (let w = 0; w <= 16; w++) {
      const inb = w >= w0 && w <= w1, r = nr[w] || 0, b = nb[w] || 0; if (inb && r) act++;
      const t = 36000 + w * 1800, lbl = kmHms(t).slice(0, 5);
      cells += `<div class="km-hc ${inb ? "in" : ""}" title="${lbl}-${kmHms(t + 1800).slice(0, 5)} · ${b} alış · ${r} yükseltme"><i style="opacity:${r ? (0.25 + 0.75 * r / mx).toFixed(2) : 0}"></i><b>${r || (b ? "·" : "")}</b><small>${lbl}</small></div>`;
    }
    const tot = w1 - w0 + 1;
    const verdict = tot <= 2 ? "KÜMELENMİŞ / TEK SEFERLİK" : act / tot >= 0.6 ? "GÜN BOYUNA YAYILMIŞ (ısrar)" : act / tot >= 0.35 ? "KISMEN YAYILMIŞ" : "KÜMELENMİŞ";
    return `<div class="km-hh"><div class="km-hht"><b>YARIM SAAT ŞERİDİ</b><span>yükseltmeli ${act}/${tot} yarım saat · ${verdict}</span></div><div class="km-hcs">${cells}</div><div class="muted sm">Hücredeki sayı o 30 dakikadaki maliyet yükseltme adedi; turuncu yoğunluk yükseltme sayısı, çerçeveli hücreler kurumun alış dönemi.</div></div>`;
  }
  function kmChart() {
    const d = KM.d, box = $("km-chart"); if (!d || !box) return;
    const W = Math.max(300, Math.round(box.clientWidth || 360)), Hh = W < 600 ? 280 : 380, padL = 6, padR = 52, padT = 14, padB = 22;
    const [t0, t1] = kmRange(); const span = Math.max(1, t1 - t0);
    const px = d.px.filter((p) => p[0] >= t0 && p[0] <= t1);
    const bs = d.buys.filter((x) => x[0] >= t0 && x[0] <= t1), ss = d.sells.filter((x) => x[0] >= t0 && x[0] <= t1);
    let lo = Infinity, hi = -Infinity;
    px.forEach((p) => { if (p[1] < lo) lo = p[1]; if (p[1] > hi) hi = p[1]; });
    bs.forEach((x) => { if (x[5] < lo) lo = x[5]; if (x[5] > hi) hi = x[5]; });
    if (!isFinite(lo)) { box.innerHTML = `<div class="empty">Bu aralıkta işlem yok</div>`; return; }
    const pad = (hi - lo) * 0.06 || hi * 0.005 || 1; lo -= pad; hi += pad;
    const X = (t) => padL + (t - t0) / span * (W - padL - padR), Y = (v) => padT + (hi - v) / (hi - lo) * (Hh - padT - padB);
    let pth = ""; px.forEach((p, i) => { pth += (i ? "L" : "M") + X(p[0]).toFixed(1) + " " + Y(p[1]).toFixed(1); });
    // kümülatif ortalama: her alışta basamak
    let av = ""; const prevB = d.buys.filter((x) => x[0] < t0); let last = prevB.length ? prevB[prevB.length - 1][5] : null;
    if (last != null) av = `M${X(t0).toFixed(1)} ${Y(last).toFixed(1)}`;
    bs.forEach((x) => { const xx = X(x[0]).toFixed(1); av += last == null ? `M${xx} ${Y(x[5]).toFixed(1)}` : `L${xx} ${Y(last).toFixed(1)}L${xx} ${Y(x[5]).toFixed(1)}`; last = x[5]; });
    if (last != null && (bs.length || prevB.length)) { const tEnd = d.live ? t1 : Math.min(t1, d.px[d.px.length - 1][0]); av += `L${X(tEnd).toFixed(1)} ${Y(last).toFixed(1)}`; }
    const mk = bs.map((x) => { const r = 2 + 9 * Math.sqrt(x[2] / d.maxL); const c = x[4] === 1 ? "ak" : "ps"; const rz = x[8] === 2 ? " rz" : x[8] === 1 ? " ry" : "";
      return `<circle class="km-m ${c}${rz}" cx="${X(x[0]).toFixed(1)}" cy="${Y(x[1]).toFixed(1)}" r="${r.toFixed(1)}"/>`; }).join("");
    const sm = ss.map((x) => `<rect class="km-s" x="${(X(x[0]) - 1.5).toFixed(1)}" y="${(Y(x[1]) - 1.5).toFixed(1)}" width="3" height="3"/>`).join("");
    let ax = ""; for (let i = 0; i <= 4; i++) { const v = lo + (hi - lo) * i / 4, y = Y(v); ax += `<line x1="${padL}" x2="${W - padR}" y1="${y.toFixed(1)}" y2="${y.toFixed(1)}" class="km-g"/><text x="${W - padR + 4}" y="${(y + 3).toFixed(1)}" class="km-t">${kmP(v)}</text>`; }
    const nx = W < 600 ? 3 : 6; for (let i = 0; i <= nx; i++) { const t = t0 + span * i / nx, x = X(t); ax += `<text x="${x.toFixed(1)}" y="${Hh - 6}" class="km-t" text-anchor="${i === 0 ? "start" : i === nx ? "end" : "middle"}">${kmHms(t).slice(0, span > 900 ? 5 : 8)}</text>`; }
    const b0 = d.buys[0]; let fx = "";
    if (b0 && b0[0] >= t0 && b0[0] <= t1) { const x = X(b0[0]).toFixed(1); fx = `<line x1="${x}" x2="${x}" y1="${padT}" y2="${Hh - padB}" class="km-f"/><text x="${(+x + 4).toFixed(1)}" y="${padT + 9}" class="km-t km-ft">İlk ayak izi ${kmHms(b0[0])}</text>`; }
    box.innerHTML = `<svg width="${W}" height="${Hh}" viewBox="0 0 ${W} ${Hh}" class="km-svg">${ax}${fx}<path d="${pth}" class="km-px"/>${sm}<path d="${av}" class="km-av"/>${mk}<line id="km-cur" class="km-cur" x1="0" x2="0" y1="${padT}" y2="${Hh - padB}" visibility="hidden"/></svg><div id="km-tip" class="km-tip" hidden></div>`;
    KM.geo = { t0, span, W, padL, padR };
  }
  function kmTip(e) {
    const d = KM.d, g = KM.geo, tip = $("km-tip"); if (!d || !g || !tip) return;
    const box = $("km-chart"), rc = box.getBoundingClientRect(), x = e.clientX - rc.left;
    const t = g.t0 + (x - g.padL) / (g.W - g.padL - g.padR) * g.span;
    const B = d.buys; if (!B.length) return;
    let lo = 0, hi = B.length - 1; while (lo < hi) { const m = (lo + hi) >> 1; if (B[m][0] < t) lo = m + 1; else hi = m; }
    if (lo > 0 && Math.abs(B[lo - 1][0] - t) < Math.abs(B[lo][0] - t)) lo--;
    const b = B[lo]; const pi = d.px.findIndex((p) => p[0] >= t); const pp = d.px[Math.max(0, pi < 0 ? d.px.length - 1 : pi)];
    tip.hidden = false;
    tip.innerHTML = `<b>${kmHms(b[0])}</b> alış ${kmP(b[1])} ₺ × ${fN(b[2])} lot · ${b[4] === 1 ? "AKTİF" : b[4] === 0 ? "pasif" : "açılış/bilinmiyor"}${b[8] ? (b[8] === 2 ? " · ▲▲ yeni zirve" : " · ▲ yükseltme") : ""}<br>kümülatif ort. ${kmP(b[5])} ₺ ${b[7] != null ? `(${fPct(b[7], 3)})` : ""}<br><span class="muted">fiyat ${kmHms(pp[0])}: ${kmP(pp[1])} ₺</span>`;
    tip.style.left = Math.min(Math.max(4, x + 10), rc.width - 210) + "px";
    const cur = $("km-cur"); if (cur) { const cx = g.padL + (b[0] - g.t0) / g.span * (g.W - g.padL - g.padR); cur.setAttribute("x1", cx); cur.setAttribute("x2", cx); cur.setAttribute("visibility", "visible"); }
  }
  function kmTable() {
    const d = KM.d; let rows = d.tr;
    if (KM.flt === "buy") rows = d.buys; else if (KM.flt === "ys") rows = d.buys.filter((x) => x[8]);
    const F = [["all", `TÜMÜ ${fN(d.tr.length)}`], ["buy", `ALIŞLAR ${fN(d.buys.length)}`], ["ys", `YÜKSELTMELER ${fN(d.buys.filter((x) => x[8]).length)}`]];
    const body = rows.slice(0, KM.n).map((x) => { const A = x[3] === "A";
      return `<tr class="${A ? "" : "km-sr"} ${x[8] === 2 ? "km-rz" : x[8] === 1 ? "km-ry" : ""}"><td class="l sticky">${kmHms(x[0])}</td><td class="l ${A ? "pos" : "neg"}">${A ? "ALIŞ" : "SATIŞ"}</td><td>${kmP(x[1])}</td><td>${fN(x[2])}</td>
        <td class="l">${x[4] === 1 ? (A ? "AKTİF" : "AKTİF SATIŞ") : x[4] === 0 ? "pasif" : "açılış"}</td><td class="b">${kmP(x[5])}</td>
        <td class="${cls(x[6])}">${A && x[6] != null ? (x[6] > 0 ? "+" : "") + nf(4).format(x[6]) : "—"}</td><td class="${cls(x[7])}">${A && x[7] != null ? fPct(x[7], 3) : "—"}</td>
        <td>${x[8] === 2 ? "▲▲ zirve" : x[8] === 1 ? "▲" : ""}</td><td class="${cls(x[9])}">${fN(x[9])}</td><td class="${cls(x[10])}">${fPct(x[10], 2)}</td><td class="${cls(x[11])}">${fPct(x[11], 2)}</td><td class="l kn">${esc(brName(x[12] || ""))}</td></tr>`; }).join("");
    setH($("km-tbl"), `<div class="card tbl-card km-tc"><div class="card-h" style="padding:8px 8px 0"><span class="card-title">İŞLEM İŞLEM TAM LİSTE</span><span class="muted sm">saniye hassasiyetinde · eskiden yeniye</span></div>
      <div class="km-rng">${F.map(([v, l]) => `<button type="button" data-kmf="${v}" class="${KM.flt === v ? "active" : ""}">${l}</button>`).join("")}</div>
      <div class="tbl-scroll"><table class="grid-table op-table km-table"><thead><tr><th class="l sticky">SAAT</th><th class="l">TARAF</th><th>FİYAT</th><th>LOT</th><th class="l">AKTİF/PASİF</th><th>KÜMÜLATİF ORT.</th><th>DEĞİŞİM</th><th>DEĞİŞİM %</th><th>YÜKSELTME</th><th>NET LOT</th><th>ETKİ 10 SN</th><th>ETKİ 60 SN</th><th class="l">KARŞI KURUM</th></tr></thead>
      <tbody>${body || `<tr><td colspan="13" class="empty">İşlem yok</td></tr>`}</tbody></table></div>
      ${rows.length > KM.n ? `<div class="km-more"><button type="button" class="btn-ghost" data-km="more">Daha fazla göster (+${fN(Math.min(1000, rows.length - KM.n))})</button><button type="button" class="btn-ghost" data-km="all">Tümünü göster (${fN(rows.length)})</button></div>` : ""}</div>`);
  }
  function kmClick(e) {
    if (e.target.id === "km-ov") { kmClose(); return; }
    const b = e.target.closest("[data-km],[data-kmr],[data-kmf]"); if (!b) return;
    if (b.dataset.kmr) { KM.rng = b.dataset.kmr; kmRender(); return; }
    if (b.dataset.kmf) { KM.flt = b.dataset.kmf; KM.n = 400; kmTable(); return; }
    const a = b.dataset.km;
    if (a === "close") kmClose();
    else if (a === "stock") { const s = KM.sym; kmClose(); openStock(s); }
    else if (a === "more") { KM.n += 1000; kmTable(); }
    else if (a === "all") { KM.n = 1e9; kmTable(); }
  }
  function kAfterRender(d) { }
  $("op-special").addEventListener("click", (e) => { const b = e.target.closest("[data-khelp]"); if (!b) return; LS.set("kHelpOpen", !LS.get("kHelpOpen", false)); opRender(); });
  $("op-filt").addEventListener("click", (e) => { const b = e.target.closest("[data-kw]"); if (!b || !isK(st.opId)) return; e.stopPropagation(); OPS.w = b.dataset.kw; OPS.wSet = true; OPS.ktok = ""; if (st.opId === "k_maliyet" && OPS.w === "israr") OPS.sort = null; opHeader(); opLoad(true); }, true);
  let kqT = null;
  $("op-q").addEventListener("input", (e) => { if (st.opId !== "k_kurumfiyat" && st.opId !== "k_maliyet") return; clearTimeout(kqT); const km = st.opId === "k_maliyet"; kqT = setTimeout(() => { OPS.kq = e.target.value.trim(); if (!km) OPS.q = ""; OPS.ktok = ""; opLoad(true); }, 450); });
  $("op-special").addEventListener("click", (e) => { const b = e.target.closest("[data-opgo]"); if (b) opOpen(+b.dataset.opgo); });
  $("op-q").addEventListener("input", (e) => { OPS.q = e.target.value; OPS.n = (OP_MK[st.opId] ? 100000 : 200); opRender(); });
  $("op-filt").addEventListener("click", (e) => { const b = e.target.closest("[data-f]"); if (!b) return; OPS.filt = b.dataset.f; OPS.n = (OP_MK[st.opId] ? 100000 : 200); opRender(); });
  $("op-more").addEventListener("click", () => { OPS.n += 400; opRender(); });
  $("op-head").addEventListener("click", (e) => {
    const th = e.target.closest("th[data-k]"); if (!th) return;
    const k = th.dataset.k; const col = ((OPS.data && OPS.data.cols) || []).find((c) => c[0] === k);
    if (OPS.sort === k) OPS.dir *= -1; else { OPS.sort = k; OPS.dir = col && !col[3] && ["sym", "txt", "broker", "time", "kmdr"].includes(col[2]) ? 1 : -1; }
    opRender();
  });
  function opRowClick(e) {
    const x = e.target.closest("[data-exp]");
    if (x) { const k = x.dataset.exp; OPS.exp[k] = !OPS.exp[k]; opRender(); return; }
    const cx = e.target.closest("[data-ckx]");
    if (cx) { const k = "ck:" + cx.dataset.ckx; OPS.exp[k] = !OPS.exp[k]; opRender(); return; }   // v1.24.0 ✓/✗ listesi
    if (e.target.closest(".op-bd .ck-list")) return;
    const pt = e.target.closest(".op-pt[data-opgo]"); if (pt) { opOpen(+pt.dataset.opgo); return; }
    const tr = e.target.closest("tr[data-row-sym]"); if (!tr || !tr.dataset.rowSym) return;
    const sym = tr.dataset.rowSym;
    if (st.opId === "k_maliyet" && tr.dataset.rowBr) { kmOpen(sym, tr.dataset.rowBr); return; }
    if (isB(st.opId) && tr.dataset.rowRef) { bdOpen(sym, tr.dataset.rowRef); return; }   // v1.24.0
    if (st.opId === 30) { st.tab = "operasyon"; LS.set("tab", "operasyon"); }
    openStock(sym);
  }
  $("op-body").addEventListener("click", opRowClick);
  $("op-extra").addEventListener("click", opRowClick);

  // ---- hisse sayfası OPERASYON sekmesi
  async function opStockLoad(force) {
    const sym = st.sym, gen = st.gen;
    if (force !== true && opStockLoad._sym === sym && opStockLoad._d) opStockRender(opStockLoad._d);
    try {
      const d = await api(`/api/op/stock/${encodeURIComponent(sym)}`, { timeout: 15000 });
      if (gen !== st.gen) return;
      opStockLoad._sym = sym; opStockLoad._d = d; opStockRender(d);
    } catch (e) { if (opStockLoad._sym !== sym) $("opx").innerHTML = `<div class="card"><div class="empty">Operasyon verisi alınamadı</div></div>`; }
  }
  function opStockRender(d) {
    const z = d.zaman || {}, cur = z.current || {};
    const sc = d.score || 0;
    const days = (z.days || []).slice(-30);
    const sig = d.features.filter((f) => f.st > 0).sort((a, b) => b.st * (b.w || 1) - a.st * (a.w || 1));
    const none = d.features.filter((f) => !(f.st > 0));
    const val = (f) => { if (!f.row || !f.cols) return ""; return f.cols.filter((c) => !["s", "p", "c", "sc", "n"].includes(c[0]) && f.row[c[0]] != null && f.row[c[0]] !== "").slice(0, 4)
      .map((c) => `<span class="op-kv"><small>${esc(c[1])}</small>${opCell(c, f.row).replace(/^<td[^>]*>|<\/td>$/g, "")}</span>`).join(""); };
    $("opx").innerHTML = `<div class="card op-hero"><div class="op-big" style="--v:${sc}"><b>${fN(sc, 0)}</b><small>/100</small></div>
        <div class="op-hero-t"><div class="card-title">OPERASYON SKORU · ${esc(d.symbol)}</div><div class="muted sm">${sig.length} aktif sinyal · evre: <b style="color:${PH_C[cur.ph] || "#999"}">${esc(trUpper(cur.phn || "—"))}</b> (güven %${fN(cur.conf || 0)}, ${fN(cur.streak || 0)} gün) · ⟳ ${esc(d.computed_at || "—")}</div>
        <div class="muted sm">veri biriktiriliyor (${d.hist_days} gün) · sezgisel, yatırım tavsiyesi değildir</div></div></div>
      ${d.parts && d.parts.length ? `<div class="card"><div class="card-h"><span class="card-title">PUAN DÖKÜMÜ</span></div>${opParts(d.parts)}</div>` : ""}
      <div class="card"><div class="card-h"><span class="card-title">ZAMAN ÇİZELGESİ</span><span class="muted">son ${days.length} gün</span></div>
        <div class="op-tl">${days.map((x) => `<div class="op-tld ${x.live ? "live" : ""}" title="${esc(x.d + " · " + x.phn + " · " + x.why)}"><i style="background:${PH_C[x.ph]}">${PH_L[x.ph]}</i><small>${esc(x.d.slice(8, 10))}</small></div>`).join("")}</div>
        <div class="tbl-scroll"><table class="grid-table op-table"><thead><tr><th class="l">TARİH</th><th class="l">EVRE</th><th>GÜN %</th><th>HACİM ×</th><th class="l">NEDEN</th></tr></thead>
        <tbody>${days.slice().reverse().slice(0, 12).map((x) => `<tr><td class="l">${esc(x.d.slice(5))}${x.live ? " ●" : ""}</td><td class="l"><b style="color:${PH_C[x.ph]}">${esc(trUpper(x.phn))}</b>${x.akd ? " <small class='muted'>AKD</small>" : ""}</td><td class="${cls(x.r)}">${fPct(x.r)}</td><td>${fN(x.vr, 2)}</td><td class="l op-txt">${esc(x.why)}</td></tr>`).join("")}</tbody></table></div>
        <div class="src-note">${esc(z.note || "")}</div></div>
      <div class="card"><div class="card-h"><span class="card-title">AKTİF SİNYALLER</span><span class="muted">${sig.length}/${d.features.length}</span></div>
        ${sig.map((f) => `<div class="op-fs" data-opgo="${f.fid}"><div class="op-fsh"><b>${esc(f.title)}</b><span class="op-ptb"><i style="width:${f.st}%"></i></span><span class="b">%${f.st}</span></div><div class="muted sm">${esc(f.txt || "")}</div><div class="op-kvs">${val(f)}</div></div>`).join("") || `<div class="empty">Bu hisse için şu an güçlü sinyal yok</div>`}</div>
      <div class="card"><div class="card-h"><span class="card-title">DİĞER ÖZELLİKLER</span></div>
        ${none.map((f) => `<div class="op-fs dim" data-opgo="${f.fid}"><div class="op-fsh"><b>${esc(f.title)}</b><span class="muted sm">${f.row ? "listede · sinyal zayıf" : "sinyal yok"}</span></div>${f.row ? `<div class="op-kvs">${val(f)}</div>` : ""}</div>`).join("")}</div>`;
  }
  $("opx").addEventListener("click", (e) => { const b = e.target.closest("[data-opgo]"); if (b) opOpen(+b.dataset.opgo); });

  // ===================================================================== v1.24.0 ==
  // ---- POC BASKISI / ALIŞ ORTALAMA BASKISI / CİDDİ YÜKSELİŞ – TAVAN ADAYI
  function bHeader(id, d) {
    $("op-title").textContent = BF_L[id];
    $("op-sub").textContent = `BASKI & HAZIR SENARYOLAR · işlem işlem, saniye saniye · tüm BIST payları${d.day_label ? " · " + d.day_label : ""}`;
    $("op-ic").innerHTML = `<svg viewBox="0 0 24 24" width="22" height="22"><path d="${KI[id] || KI.k_maliyet}" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    setH($("op-strip"), [...BF, "k_maliyet"].map((k) => `<button type="button" class="op-chip ${k === id ? "on" : ""}" data-opgo="${k}">${esc(k === "k_maliyet" ? "MALİYET↑ KURUM" : BF_S[k])}</button>`).join(""));
    opStripCenter(id);
    const fl = $("op-filt"), W = d.windows || null, C = d.counts || {};
    if (W && W.length) { fl.hidden = false; const cur = OPS.wSet ? OPS.w : (d.w || OPS.w); setH(fl, W.map(([v, l]) => `<button type="button" data-kw="${v}" class="${cur === v ? "active" : ""}${v === "ciddi" || v === "tavan" ? " kw-pre " + v : ""}">${v === "tavan" ? "🚀 " : v === "ciddi" ? "🟢 " : ""}${esc(l)}${C[v] != null ? " · " + C[v] : ""}</button>`).join("")); }
    else { fl.hidden = true; setH(fl, ""); }
    $("op-q").placeholder = "Hisse ara...";
  }
  function bSpecial(d) {
    const H = d.help || {};
    const open = LS.get("kHelpOpen", false);
    const sel = OPS.kdate || d.day || "";
    const mode = d.live ? `<span class="op-b ok">CANLI SEANS · ${esc(d.day_label || "")}</span>` : `<span class="op-b warn">GÖSTERİLEN SEANS: ${esc(d.day_label || d.day || "—")}${OPS.kdate ? "" : " (son seans)"}</span>`;
    const dates = (d.dates || []).map((x) => `<button type="button" data-kdate="${esc(x.d)}" class="${x.d === sel ? "active" : ""}">${esc(x.live ? "BUGÜN · CANLI" : x.l)}</button>`).join("");
    const w = OPS.wSet ? OPS.w : d.w;
    const pre = w === "ciddi" || w === "tavan" ? `<div class="card bs-pre ${w}"><b>${w === "tavan" ? "🚀 TAVAN ADAYI" : "🟢 CİDDİ YÜKSELİŞ"}</b><span class="muted sm"> · hazır senaryo · ${fN(d.count || 0)} hisse · Koşullar sütununda ▸ ile ✓/✗ listesini açın · <b>Z</b> zorunlu (hepsi) · <b>O</b> opsiyonel (yeterli sayıda) · <b>B</b> bonus kanıt · tam tanım: AÇIKLAMA → Hazır senaryolar</span></div>` : "";
    return `<div class="card k-help ${open ? "open" : ""}"><button type="button" class="k-help-h" data-khelp="1"><span>ℹ️ AÇIKLAMA · NASIL KULLANMALIYIM? · HAZIR SENARYOLAR</span><b>${open ? "▾" : "▸"}</b></button>
      <div class="k-help-b">${kmGuide(H)}</div></div>
      <div class="km-dates"><span class="muted sm">SEANS:</span>${dates}</div>
      <div class="k-meta">${mode}<span class="op-b">${fN(d.universe || 0)} hisse tarandı</span>${d.ref ? `<span class="op-b">referans ${esc(d.ref)}</span>` : ""}<span class="op-b">işlem işlem</span><span class="op-b hist">satıra dokun → saniye saniye fiyat & ${st.opId === "k_aort" ? "alış ortalaması" : "POC"} grafiği</span></div>${pre}`;
  }
  const ckKey = (r) => (r.s || "") + "|" + (r.br || "");
  const CK_G = { Z: "ZORUNLU", O: "OPSİYONEL", B: "BONUS", K: "KURUM" };
  function ckList(L, title) {
    L = L || [];
    return `<div class="ck-list">${title ? `<div class="ck-t">${title}</div>` : ""}${["Z", "O", "B", "K"].filter((g) => L.some((x) => x[2] === g)).map((g) => { const G = L.filter((x) => x[2] === g); const ok = G.filter((x) => x[1] === 1).length;
      return `<div class="ck-g"><small>${CK_G[g]} · ${ok}/${G.length}</small>${G.map((x) => `<span class="ck-i ${x[1] === 1 ? "y" : x[1] === 0 ? "n" : "u"}">${x[1] === 1 ? "✓" : x[1] === 0 ? "✗" : "–"} ${esc(x[0])}</span>`).join("")}</div>`; }).join("")}</div>`;
  }
  function chkCell(r, v) {
    const L = Array.isArray(v) ? v : null; if (!L || !L.length) return `<td>—</td>`;
    const ok = L.filter((x) => x[1] === 1).length, k = ckKey(r);
    return `<td class="l ck-td"><button type="button" class="ck-sum" data-ckx="${esc(k)}"><b>✓${ok}</b>/${L.length} ${OPS.exp["ck:" + k] ? "▾" : "▸"}</button><span class="ck-dots">${L.map((x) => `<i class="${x[1] === 1 ? "y" : x[1] === 0 ? "n" : "u"}" title="${esc((x[1] === 1 ? "✓ " : x[1] === 0 ? "✗ " : "– ") + x[0])}"></i>`).join("")}</span></td>`;
  }
  function senCell(v) { return `<td class="l">${v ? `<span class="sen-b ${/TAVAN ADAYI/.test(v) ? "t" : "c"}">${esc(v)}</span>` : `<span class="muted">—</span>`}</td>`; }

  // ---- detay penceresi (saniye saniye fiyat vs POC / alış ortalaması)
  const BD = { sym: null, fid: "k_poc", d: null, gen: 0, tm: null, flt: "all", rng: "all", n: 300 };
  function bdOv() {
    let ov = $("bd-ov");
    if (!ov) {
      ov = document.createElement("div"); ov.id = "bd-ov"; ov.className = "km-ov"; ov.hidden = true;
      ov.innerHTML = `<div class="km-box" role="dialog" aria-modal="true"><div class="km-top"><div class="km-tt"><b id="bd-title"></b><small id="bd-sub"></small></div><button type="button" class="btn-ghost sm" data-bd="stock">Hisse →</button><button type="button" class="km-x" data-bd="close" aria-label="Kapat">✕</button></div>
        <div id="bd-ref" class="km-rng"></div><div id="bd-kpi"></div><div id="bd-rng" class="km-rng"></div><div class="km-chart" id="bd-chart"></div><div id="bd-leg" class="km-leg"></div><div id="bd-ck"></div><div id="bd-tbl"></div></div>`;
      document.body.appendChild(ov);
      ov.addEventListener("click", bdClick);
      ov.querySelector("#bd-chart").addEventListener("pointermove", bdTip);
      ov.querySelector("#bd-chart").addEventListener("pointerleave", () => { const t = $("bd-tip"); if (t) t.hidden = true; });
    }
    return ov;
  }
  function bdOpen(sym, fid, day) {
    Object.assign(BD, { sym, fid: fid === "k_aort" ? "k_aort" : "k_poc", day: day || null, d: null, flt: "all", rng: "all", n: 300, at: null, atDone: false }); BD.gen++;
    const ov = bdOv(); ov.hidden = false; document.body.classList.add("km-lock");
    $("bd-title").textContent = `${sym} · ${BD.fid === "k_aort" ? "Alış Ortalama Baskısı" : "POC Baskısı"}`; $("bd-sub").textContent = "Yükleniyor…";
    ["bd-ref", "bd-kpi", "bd-rng", "bd-chart", "bd-leg", "bd-ck", "bd-tbl"].forEach((k) => { const el = $(k); el.innerHTML = ""; el._h = null; });
    $("bd-chart").innerHTML = `<div class="empty">İşlemler işlem işlem yeniden oynatılıyor…</div>`;
    ov.querySelector(".km-box").scrollTop = 0;
    bdLoad();
    clearInterval(BD.tm); BD.tm = setInterval(() => { if (!document.hidden && BD.d && BD.d.live && !$("bd-ov").hidden) bdLoad(true); }, 10000);
  }
  function bdClose() { const ov = $("bd-ov"); if (ov) ov.hidden = true; document.body.classList.remove("km-lock"); clearInterval(BD.tm); BD.gen++; }
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && $("bd-ov") && !$("bd-ov").hidden) bdClose(); });
  window.addEventListener("resize", () => { if (BD.d && $("bd-ov") && !$("bd-ov").hidden) bdChart(); });
  async function bdLoad(quiet) {
    const g = BD.gen, p = new URLSearchParams({ sym: BD.sym, fid: BD.fid });
    const day = BD.day || OPS.kdate || (OPS.data && isB(st.opId) && OPS.data.day) || ""; if (day) p.set("date", day);
    try {
      const d = await api(`/api/k/baski/detail?${p.toString()}`, { timeout: 30000 });
      if (g !== BD.gen) return;
      if (d.error) { $("bd-sub").textContent = d.error; $("bd-chart").innerHTML = `<div class="empty">${esc(d.error)}</div>`; return; }
      BD.d = d; bdRender();
    } catch (e) { if (!quiet && g === BD.gen) $("bd-chart").innerHTML = `<div class="empty">Detay alınamadı (${esc(e.message || e)})</div>`; }
  }
  const bdNm = () => (BD.fid === "k_aort" ? "Alış ort." : "POC");
  function bdRender() {
    const d = BD.d, K = d.kpi || {}, nm = bdNm();
    $("bd-title").textContent = `${d.sym} · ${BD.fid === "k_aort" ? "Alış Ortalama Baskısı" : "POC Baskısı"}`;
    $("bd-sub").textContent = `${d.live ? "CANLI · " : ""}${d.day_label || d.day} · ${fN(d.n_all || 0)} işlem · ${(d.px || []).length} fiyat noktası`;
    setH($("bd-ref"), [["k_poc", "POC BASKISI"], ["k_aort", "ALIŞ ORTALAMA BASKISI"]].map(([v, l]) => `<button type="button" data-bdf="${v}" class="${BD.fid === v ? "active" : ""}">${l}</button>`).join(""));
    const sen = K.t_ok ? `<span class="sen-b t">TAVAN ADAYI</span>` : K.c_ok ? `<span class="sen-b c">CİDDİ YÜKSELİŞ</span>` : `<span class="muted">senaryo yok</span>`;
    const kp = (l, v, c = "") => `<div class="km-k"><small>${l}</small><b class="${c}">${v}</b></div>`;
    const pc = (v, dd = 2) => (isNum(v) ? fPct(v, dd) : "—");
    setH($("bd-kpi"), `<div class="km-kpis">
      ${kp("Baskı skoru", isNum(K.sc) ? fN(K.sc, 1) : "—", (K.sc || 0) >= 60 ? "pos" : "")}${kp("Senaryo", sen)}
      ${kp(nm + " (şimdi)", kmP(K.R))}${kp("İlk " + nm, kmP(K.R0))}${kp("Son fiyat", fP(K.last))}${kp("Fiyat – " + nm, pc(K.pr), cls(K.pr))}
      ${kp("Yükseltme / düşürme", `${K.up ?? "—"} / ${K.dn ?? "—"}`)}${kp("Destek temas / tepki / kırılma", `${K.st ?? 0} / <span class="pos">${K.sb ?? 0}</span> / <span class="neg">${K.sk ?? 0}</span>`)}
      ${kp("Direnç temas / red / kırılma", `${K.rt ?? 0} / ${K.rr ?? 0} / ${K.rk ?? 0}`)}${kp(nm + " → yüksek", pc(K.rh))}${kp(nm + " → düşük", pc(K.rl))}
      ${kp(nm + " → tavan", pc(K.rtv))}${kp(nm + " → taban", pc(K.rtb))}${kp("Gün %", pc(K.gd), cls(K.gd))}
      ${kp("Aktif alış % (gün / son 15 dk)", `${isNum(K.akt) ? "%" + fN(K.akt, 0) : "—"} / ${isNum(K.a15) ? "%" + fN(K.a15, 0) : "—"}`)}${kp("RVOL (zaman ayarlı)", isNum(K.rv) ? fN(K.rv, 2) + "×" : "—")}
      ${kp("Süpürme (son 30 dk)", K.sw30 ?? "—")}${kp("Tavan / taban", `${fP(K.tv)} / ${fP(K.tb)}`)}
      ${K.ent_c ? kp("CİDDİ giriş", `${esc(K.ent_c[0])} · ${fP(K.ent_c[1])}`) : ""}${K.ent_t ? kp("TAVAN ADAYI giriş", `${esc(K.ent_t[0])} · ${fP(K.ent_t[1])}`) : ""}</div>`);
    setH($("bd-rng"), [["all", "TÜM GÜN"], ["am", "İLK 2 SAAT"], ["pm", "SON 2 SAAT"], ["l30", "SON 30 DK"]].map(([v, l]) => `<button type="button" data-bdr="${v}" class="${BD.rng === v ? "active" : ""}">${l}</button>`).join(""));
    bdChart();
    setH($("bd-leg"), `<span><i class="lg px"></i>Fiyat</span><span><i class="lg ln"></i>${nm}</span><span><b class="pos">▲</b> ${nm} yükseltildi</span><span><b class="neg">▼</b> düşürüldü</span><span><b class="pos">●</b> destek tepkisi</span><span><b class="neg">✕</b> destek kırıldı</span><span><b style="color:#f59e0b">◆</b> süpürme</span><span><b style="color:#a78bfa">┆</b> senaryo girişi</span><span><b style="color:#ef4444">┄</b> tavan</span>`);
    setH($("bd-ck"), `<div class="card-h" style="padding:8px 0 4px"><span class="card-title">HAZIR SENARYO KOŞULLARI · ${nm}</span><span class="muted sm">şu anki değerlerle</span></div><div class="bd-cks">${ckList(K.ck_c, `🟢 CİDDİ YÜKSELİŞ ${K.c_ok ? "✓" : "✗"}`)}${ckList(K.ck_t, `🚀 TAVAN ADAYI ${K.t_ok ? "✓" : "✗"}`)}</div>
      <div class="src-note">Kurallar: temas = fiyat seviyenin ${esc((d.rules || {}).tol || "")} yakınına iner · tepki = sonra seviyenin ${esc((d.rules || {}).thr || "")} üstüne çıkar · kırılma = seviyenin ${esc((d.rules || {}).brk || "")} altına iner${BD.fid === "k_poc" ? ` · POC kayması yeni POC ≥${(d.rules || {}).hold || 60} sn korunursa sayılır` : ""}.</div>`);
    bdTable();
  }
  function bdRange() {
    const px = BD.d.px || []; if (!px.length) return [0, 1];
    const T0 = px[0][0], T1 = px[px.length - 1][0];
    if (BD.rng === "am") return [T0, Math.min(T1, T0 + 7200)];
    if (BD.rng === "pm") return [Math.max(T0, T1 - 7200), T1];
    if (BD.rng === "l30") return [Math.max(T0, T1 - 1800), T1];
    return [T0, T1];
  }
  function bdChart() {
    const d = BD.d, box = $("bd-chart"); if (!d) return;
    const px = d.px || [], ln = d.line || []; if (!px.length) { box.innerHTML = `<div class="empty">İşlem yok</div>`; return; }
    const [A, B] = bdRange();
    const Wd = Math.max(300, box.clientWidth || 600), Ht = Wd < 520 ? 240 : 300, pl = 6, pr = 52, pt = 10, pb = 22;
    const P = px.filter((x) => x[0] >= A && x[0] <= B);
    let L = ln.filter((x) => x[0] >= A && x[0] <= B); const lb = ln.filter((x) => x[0] < A); if (lb.length) L = [[A, lb[lb.length - 1][1]], ...L];
    let lo = Infinity, hi = -Infinity; P.forEach((x) => { lo = Math.min(lo, x[1]); hi = Math.max(hi, x[1]); }); L.forEach((x) => { lo = Math.min(lo, x[1]); hi = Math.max(hi, x[1]); });
    const K = d.kpi || {};
    if (isNum(K.tv) && K.tv > hi && (K.tv - hi) / hi <= 0.04) hi = K.tv;
    if (!(hi > lo)) { hi = lo * 1.001 + 0.01; lo = lo * 0.999; }
    const pad = (hi - lo) * 0.06; lo -= pad; hi += pad;
    const X = (t) => pl + ((t - A) / Math.max(1, B - A)) * (Wd - pl - pr), Y = (v) => pt + (1 - (v - lo) / (hi - lo)) * (Ht - pt - pb);
    // fiyat: piksel başına min/max
    const cols = Math.max(50, Math.floor(Wd - pl - pr)); const bk = new Map();
    P.forEach((x) => { const c = Math.floor(((x[0] - A) / Math.max(1, B - A)) * (cols - 1)); const o = bk.get(c); if (!o) bk.set(c, [x[1], x[1], x[1], x[0]]); else { o[0] = Math.min(o[0], x[1]); o[1] = Math.max(o[1], x[1]); o[2] = x[1]; o[3] = x[0]; } });
    let pp = ""; [...bk.entries()].sort((a, b) => a[0] - b[0]).forEach(([c, o], i) => { const x = (pl + (c / (cols - 1)) * (Wd - pl - pr)).toFixed(1); pp += (i ? "L" : "M") + x + " " + Y(o[0]).toFixed(1) + "L" + x + " " + Y(o[1]).toFixed(1) + "L" + x + " " + Y(o[2]).toFixed(1); });
    let lp = ""; L.forEach((x, i) => { const xx = X(x[0]).toFixed(1); lp += i ? `H${xx}V${Y(x[1]).toFixed(1)}` : `M${xx} ${Y(x[1]).toFixed(1)}`; }); if (L.length) lp += `H${X(B).toFixed(1)}`;
    const grid = []; for (let i = 0; i <= 4; i++) { const v = lo + ((hi - lo) * i) / 4; grid.push(`<line x1="${pl}" x2="${Wd - pr}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" class="bd-gr"/><text x="${Wd - pr + 4}" y="${(Y(v) + 3).toFixed(1)}" class="bd-ax">${nf(v < 10 ? 3 : 2).format(v)}</text>`); }
    const span = B - A, stp = span > 14400 ? 3600 : span > 5400 ? 1800 : span > 1800 ? 600 : 300;
    for (let t = Math.ceil(A / stp) * stp; t <= B; t += stp) { const xx = X(t); grid.push(`<text x="${xx.toFixed(1)}" y="${Ht - 6}" class="bd-ax" text-anchor="${xx < 18 ? "start" : xx > Wd - pr - 14 ? "end" : "middle"}">${kmHms(t).slice(0, 5)}</text>`); }
    if (isNum(K.tv) && K.tv <= hi && K.tv >= lo) grid.push(`<line x1="${pl}" x2="${Wd - pr}" y1="${Y(K.tv).toFixed(1)}" y2="${Y(K.tv).toFixed(1)}" class="bd-tv"/><text x="${pl + 2}" y="${(Y(K.tv) - 3).toFixed(1)}" class="bd-ax tv">TAVAN ${kmP(K.tv)}</text>`);
    const mk = [];
    (d.events || []).forEach((e) => {
      const [t, k, , v] = e; if (t < A || t > B) return; const x = X(t), y = Y(v);
      if (k === "up") mk.push(`<path d="M${x.toFixed(1)} ${(y - 9).toFixed(1)}l-4.5 7h9z" class="bd-up"/>`);
      else if (k === "dn") mk.push(`<path d="M${x.toFixed(1)} ${(y + 9).toFixed(1)}l-4.5 -7h9z" class="bd-dn"/>`);
      else if (k === "db") mk.push(`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.6" class="bd-db"/>`);
      else if (k === "dk") mk.push(`<path d="M${(x - 3.5).toFixed(1)} ${(y - 3.5).toFixed(1)}l7 7m0 -7l-7 7" class="bd-dk"/>`);
      else if (k === "sw") mk.push(`<path d="M${x.toFixed(1)} ${(y - 3).toFixed(1)}l2.2 3-2.2 3-2.2-3z" class="bd-sw"/>`);
      else if (k === "sen") mk.push(`<line x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${pt}" y2="${Ht - pb}" class="bd-sen"/><text x="${(x + 3).toFixed(1)}" y="${pt + 9}" class="bd-ax sen">${/TAVAN/.test(e[2]) ? "TAVAN ADAYI" : "CİDDİ"}</text>`);
    });
    BD.geo = { A, B, X, Y, pl, pr, Wd, P, L };
    box.innerHTML = `<svg viewBox="0 0 ${Wd} ${Ht}" width="100%" height="${Ht}" class="bd-svg">${grid.join("")}<path d="${pp}" class="bd-px"/><path d="${lp}" class="bd-ln"/>${mk.join("")}<line id="bd-cur" x1="0" x2="0" y1="${pt}" y2="${Ht - pb}" class="bd-cur" visibility="hidden"/></svg><div id="bd-tip" class="km-tip" hidden></div>`;
  }
  function bdTip(e) {
    const G = BD.geo, box = $("bd-chart"), tip = $("bd-tip"); if (!G || !tip || !G.P.length) return;
    const r = box.getBoundingClientRect(), sx = (e.clientX - r.left) * (G.Wd / r.width);
    const t = G.A + ((sx - G.pl) / (G.Wd - G.pl - G.pr)) * (G.B - G.A);
    let i = 0, j = G.P.length - 1; while (i < j) { const m = (i + j) >> 1; if (G.P[m][0] < t) i = m + 1; else j = m; }
    const p = G.P[Math.min(i, G.P.length - 1)]; let lv = null; for (const x of G.L) { if (x[0] <= p[0]) lv = x[1]; else break; }
    const cur = $("bd-cur"); if (cur) { cur.setAttribute("x1", G.X(p[0])); cur.setAttribute("x2", G.X(p[0])); cur.setAttribute("visibility", "visible"); }
    tip.hidden = false; tip.innerHTML = `<b>${kmHms(p[0])}</b> · fiyat ${kmP(p[1])}${lv != null ? `<br>${bdNm()} ${kmP(lv)} (${fPct((p[1] / lv - 1) * 100, 2)})` : ""}`;
    const tx = e.clientX - r.left; tip.style.left = Math.min(r.width - 170, Math.max(0, tx + 10)) + "px"; tip.style.top = "6px";
  }
  const BD_EV = { up: ["YÜKSELTME", "pos"], dn: ["DÜŞÜRME", "neg"], dt: ["DESTEK TEMASI", ""], db: ["DESTEK TEPKİSİ", "pos"], dk: ["DESTEK KIRILDI", "neg"], rt: ["DİRENÇ TEMASI", ""], rr: ["DİRENÇ REDDİ", "neg"], rk: ["DİRENÇ KIRILDI", "pos"], sw: ["SÜPÜRME", ""], sen: ["SENARYO", "pos"] };
  const BD_F = { all: null, kay: ["up", "dn"], ds: ["dt", "db", "dk", "rt", "rr", "rk"], sw: ["sw"], sen: ["sen"] };
  function bdTable() {
    const d = BD.d, F = BD_F[BD.flt];
    const ev = (d.events || []).filter((e) => !F || F.includes(e[1]));
    const cnt = (k) => (d.events || []).filter((e) => !BD_F[k] || BD_F[k].includes(e[1])).length;
    const rows = ev.slice().reverse().slice(0, BD.n);
    setH($("bd-tbl"), `<div class="card-h" style="padding:10px 0 4px"><span class="card-title">OLAY LİSTESİ</span><span class="muted sm">${fN(ev.length)} olay · yeni → eski</span></div>
      <div class="km-rng">${[["all", "TÜMÜ"], ["kay", "KAYMALAR"], ["ds", "DESTEK / DİRENÇ"], ["sw", "SÜPÜRME"], ["sen", "SENARYO"]].map(([v, l]) => `<button type="button" data-bdt="${v}" class="${BD.flt === v ? "active" : ""}">${l} ${cnt(v)}</button>`).join("")}</div>
      <div class="tbl-scroll"><table class="grid-table op-table"><thead><tr><th class="l sticky">SAAT</th><th class="l">OLAY</th><th class="l">AYRINTI</th></tr></thead><tbody>
      ${rows.map((e) => { const L = BD_EV[e[1]] || [e[1], ""]; return `<tr class="${BD.at != null && e[0] === BD.at && (!BD.atK || BD.atK === e[1]) ? "bd-at" : ""}"><td class="l sticky">${kmHms(e[0])}</td><td class="l"><b class="${L[1]}">${L[0]}</b></td><td class="l op-txt"><div class="tx-2l">${esc(brName(e[2]))}</div></td></tr>`; }).join("") || `<tr><td colspan="3" class="empty">Olay yok</td></tr>`}</tbody></table></div>
      ${ev.length > BD.n ? `<button type="button" class="btn-ghost sm" data-bd="more">Daha fazla göster (+${fN(ev.length - BD.n)})</button>` : ""}`);
    setTimeout(bdAtScroll, 60);
  }
  function bdAtScroll() {   // v1.30.0: Olay Listesi (ALARM) satırından gelinen olayı vurgula
    if (BD.at == null || BD.atDone) return;
    const r = document.querySelector("#bd-tbl tr.bd-at"); if (!r) return;
    BD.atDone = true; const box = $("bd-ov") && $("bd-ov").querySelector(".km-box");
    if (box) { const rb = r.getBoundingClientRect(), bb = box.getBoundingClientRect(); box.scrollTop += rb.top - bb.top - bb.height / 2; }
  }
  function bdClick(e) {
    const b = e.target.closest("button"); if (!b) { if (e.target.id === "bd-ov") bdClose(); return; }
    if (b.dataset.bdf) { if (BD.fid !== b.dataset.bdf) { BD.fid = b.dataset.bdf; BD.gen++; $("bd-chart").innerHTML = `<div class="empty">Yükleniyor…</div>`; bdLoad(); } return; }
    if (b.dataset.bdr) { BD.rng = b.dataset.bdr; bdRender(); return; }
    if (b.dataset.bdt) { BD.flt = b.dataset.bdt; BD.n = Math.max(300, BD.n); bdTable(); return; }
    const a = b.dataset.bd;
    if (a === "close") bdClose();
    else if (a === "stock") { const s = BD.sym; bdClose(); openStock(s); }
    else if (a === "more") { BD.n += 1000; bdTable(); }
  }

  // ---- ÖZET sekmesi ek kartları (tek uç nokta: /api/stocks/{sym}/ozet-plus)
  const OZP = { d: null, sym: null, busy: false, ts: 0 };
  async function loadOzp(force) {
    const sym = st.sym, gen = st.gen;
    if (OZP.busy && !force) return;
    if (OZP.sym !== sym) { OZP.d = null; OZP.sym = sym; renderOzp(); }
    OZP.busy = true;
    try {
      const d = await api(`/api/stocks/${encodeURIComponent(sym)}/ozet-plus?cid=${encodeURIComponent(CID)}`, { timeout: 20000 });
      if (gen !== st.gen || sym !== st.sym) return;
      OZP.d = d; OZP.ts = Date.now(); renderOzp();
    } catch (e) { if (!OZP.d && sym === st.sym) { setH($("ozp-top"), ""); setH($("ozp"), `<div class="card"><div class="empty">Özet kartları alınamadı (${esc(e.message || e)})</div></div>`); } }
    finally { OZP.busy = false; }
  }
  setInterval(() => { if (!document.hidden && st.view === "stock" && st.tab === "ozet" && Date.now() - OZP.ts >= 10000) loadOzp(); }, 2000);
  function ozpNotifs(d) {
    const day = d.day || "", ds = day ? `${day.slice(0, 4)}-${day.slice(4, 6)}-${day.slice(6, 8)}` : "";
    const srv = (d.bildirim || []).filter((x) => modeOf(x.nt) !== "off");
    const hid = (d.bildirim || []).length - srv.length;
    const loc = NH.filter((h) => h.sym === d.sym && ds && (() => { const t = new Date(h.ts); return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, "0")}-${String(t.getDate()).padStart(2, "0")}` === ds; })())
      .map((h) => ({ time: h.time || "", nt: h.nt, title: h.title, text: h.text, src: "cihaz" }));
    const seen = new Set(), out = [];
    [...srv, ...loc].forEach((x) => { const k = (x.time || "").slice(0, 5) + "|" + (x.title || ""); if (seen.has(k)) return; seen.add(k); out.push(x); });
    out.sort((a, b) => String(b.time).localeCompare(String(a.time)));
    return { out, hid };
  }
  function renderOzp() {
    const top = $("ozp-top"), el = $("ozp"); if (!top || !el) return;
    const d = OZP.d;
    if (!d) { setH(top, `<div class="card ozp-y"><div class="empty">Özet yorum hazırlanıyor…</div></div>`); setH(el, ""); return; }
    if (d.error) { setH(top, ""); setH(el, `<div class="card"><div class="empty">${esc(d.error)}</div></div>`); return; }
    const lbl = d.live ? `<span class="op-b ok">CANLI</span>` : `<span class="op-b warn">SON SEANS · ${esc(d.day_label || d.day)}</span>`;
    const ok = (v) => v === 1 || v === true;
    setH(top, `<div class="card ozp-y"><div class="card-h"><span>ÖZET YORUM</span><span class="ozp-meta">${lbl}<span class="muted sm">⟳ ${esc(d.ts || "")}</span></span></div>
      ${ozTht(d)}<div class="ozp-yt">${esc(d.yorum || "—")}</div>${d.pending ? `<div class="src-note">Gün içi tarama hesaplanıyor — kartlar birkaç saniye içinde tamamlanır.</div>` : ""}</div>`);
    const C = [];
    const card = (t, sub, body, cl = "") => `<div class="card ozp-c ${cl}"><div class="card-h"><span>${t}</span>${sub ? `<span class="muted sm">${sub}</span>` : ""}</div>${body}</div>`;
    const kv = (k, v, c = "") => `<div class="ozp-kv"><small>${k}</small><b class="${c}">${v}</b></div>`;
    const pc = (v, dd = 2) => (isNum(v) ? fPct(v, dd) : "—");
    // 1) Israrcı kurum
    const I = d.israr || {};
    if (I.top) {
      const t = I.top;
      C.push(card("ISRARCI KURUM", `${I.n} kurum maliyet yükseltiyor`, `<button type="button" class="ozp-isr" data-ozkm="${esc(t.br)}"><div class="ozp-isr-h"><b>${esc(brName(t.br))}</b><span class="th-sc"><i style="width:${Math.min(100, t.israr || 0)}%;background:hsl(${Math.round((t.israr || 0) * 1.1)} 70% 45%)"></i><b>${fN(t.israr || 0, 0)}</b></span><small>Israr</small></div>
        <div class="ozp-kvs">${kv("İlk ayak izi", `${esc(t.ft)} · ${kmP(t.fp)}`)}${kv("Güncel maliyet", kmP(t.cur))}${kv("Maliyet değişimi", pc(t.chg), cls(t.chg))}${kv("Hâlâ alıyor", t.still && t.still !== "—" ? "● EVET" : "—", t.still && t.still !== "—" ? "pos" : "")}${kv("Skor", fN(t.sc, 0))}${kv("Fiyat – maliyet", pc(t.dist), cls(t.dist))}${kv("Alış", fShort(t.btl, "₺"))}${kv("Aktif alış", isNum(t.akt) ? "%" + fN(t.akt, 0) : "—")}</div>
        <div class="muted sm">Dokun → saniye saniye maliyet grafiği</div></button>
        ${(I.top3 || []).length > 1 ? `<div class="ozp-l3">${I.top3.map((x, i) => `<button type="button" class="ozp-l3r" data-ozkm="${esc(x.br)}"><span>${i + 1}. ${esc(brName(x.br))}</span><span>Israr <b>${fN(x.israr || 0, 0)}</b></span><span>skor ${fN(x.sc, 0)}</span><span class="${cls(x.chg)}">${pc(x.chg)}</span></button>`).join("")}</div>` : ""}`));
    } else C.push(card("ISRARCI KURUM", "", `<div class="empty">${I.ready === false ? "Kurum ayak izi hesaplanıyor…" : "Bu hissede maliyet yükselten kurum yok"}</div>`));
    // 2) Kurum yoğunlaşması
    const A = d.akd || {};
    if (!A.error) {
      const lc = A.label === "TOPLAMA" ? "pos" : A.label === "DAĞITIM" ? "neg" : "";
      C.push(card("KURUM YOĞUNLAŞMASI (AKD)", esc(A.src || ""), `<div class="ozp-lab ${lc}">${esc(A.label || "—")}<small>${esc(A.desc || "")}</small></div>
        <div class="ozp-kvs">${kv("İlk 3 alıcı payı", isNum(A.top3) ? "%" + fN(A.top3, 1) : "—", (A.top3 || 0) >= 60 ? "pos" : "")}${kv("İlk 3 satıcı payı", isNum(A.top3s) ? "%" + fN(A.top3s, 1) : "—")}${kv("Net alıcı kurum", fN(A.nb || 0), "pos")}${kv("Net satıcı kurum", fN(A.ns || 0), "neg")}</div>
        <div class="ozp-2c"><div>${(A.buyers || []).map((x) => `<div class="ozp-br"><span>${esc(brName(x[0]))}</span><b class="pos">+${fShort(x[1])} <small>lot</small></b></div>`).join("")}</div><div>${(A.sellers || []).map((x) => `<div class="ozp-br"><span>${esc(brName(x[0]))}</span><b class="neg">−${fShort(x[1])} <small>lot</small></b></div>`).join("")}</div></div>`));
    } else C.push(card("KURUM YOĞUNLAŞMASI (AKD)", "", `<div class="empty">${esc(A.error)}</div>`));
    // 3) Son 5 dk nabız
    const N = d.nabiz || {};
    if (!N.error) {
      const sp = N.speed, spc = isNum(sp) ? (sp >= 1.3 ? "pos" : sp <= 0.7 ? "neg" : "") : "";
      C.push(card("SON 5 DK NABZI", esc(N.label || ""), `<div class="ozp-kvs">${kv("Aktif alış", isNum(N.akt) ? "%" + fN(N.akt, 0) : "—", (N.akt || 0) >= 55 ? "pos" : (N.akt ?? 50) <= 45 ? "neg" : "")}${kv("Gün ort. aktif alış", isNum(N.akt_day) ? "%" + fN(N.akt_day, 0) : "—")}
        ${kv("İşlem / dk", `${fN(N.tpm || 0, 1)} <small>(gün ${fN(N.rate_day || 0, 1)})</small>`)}${kv("Hız (gün ortalamasına göre)", isNum(sp) ? fN(sp, 2) + "×" : "—", spc)}${kv("İşlem hacmi", fShort(N.tl, "₺"))}${kv("₺ hızı (gün ort.)", isNum(N.tl_x) ? fN(N.tl_x, 2) + "×" : "—")}</div>
        <div class="ozp-ln">${N.big ? `<b>Son büyük alış</b> (≥${fShort(N.big_th, "₺")}): ${esc(N.big.t)} · ${fShort(N.big.lot)} lot @ ${kmP(N.big.p)} · ${esc(brName(N.big.br))}${N.big.in5 ? ` <span class="sen-b c">son 5 dk</span>` : ""}` : `<span class="muted">Büyük aktif alış yok</span>`}</div>
        <div class="ozp-ln">${N.sweep ? `<b>Son süpürme</b>: ${esc(N.sweep.t)} · ${N.sweep.nlev} kademe ${kmP(N.sweep.p0)}→${kmP(N.sweep.p1)} · ${fShort(N.sweep.tl, "₺")} · ${esc(brName(N.sweep.br))}${N.sweep.n5 ? ` <span class="sen-b c">son 5 dk: ${N.sweep.n5}</span>` : ""}` : `<span class="muted">Süpürme (≥100 Bin ₺) yok</span>`}</div>`));
    } else C.push(card("SON 5 DK NABZI", "", `<div class="empty">${esc(N.error)}</div>`));
    // 4) Kademe dengesi
    const KD = d.kademe || {};
    if (!KD.error) {
      const r = KD.ratio, rc = isNum(r) ? (r >= 1.3 ? "pos" : r <= 0.77 ? "neg" : "") : "";
      C.push(card("KADEME DENGESİ", esc(KD.label || ""), `<div class="ozp-kvs">${kv("İlk 5 alış / satış", `${fShort(KD.b5)} / ${fShort(KD.a5)}`)}${kv("Alış / satış oranı", isNum(r) ? fN(r, 2) + "×" : "—", rc)}${kv("En iyi alış / satış", `${fP(KD.bb)} / ${fP(KD.ba)}`)}
        ${kv("En büyük duvar", KD.wall ? `${KD.wall.side} ${kmP(KD.wall.p)} · ${fShort(KD.wall.lot)} lot` : "—", KD.wall ? (KD.wall.side === "ALIŞ" ? "pos" : "neg") : "")}</div>
        <div class="ozp-bal"><i style="width:${isNum(r) ? Math.max(4, Math.min(96, (r / (1 + r)) * 100)).toFixed(0) : 50}%"></i></div>
        <div class="ozp-ln">${KD.melt ? `<b>Duvar erimesi</b>: ${kmP(KD.melt.p)} · tepe ${fShort(KD.melt.peak)} → ${fShort(KD.melt.cur || 0)} lot · ${esc(KD.melt.st || "")} (işlemle %${fN(KD.melt.tuk || 0, 0)}) · ${esc(KD.melt.t)}` : `<span class="muted">Eriyen duvar yok (Kademe & Şerit · Duvar takibi)</span>`}</div>`));
    } else C.push(card("KADEME DENGESİ", "", `<div class="empty">${esc(KD.error)}</div>`));
    // 5) Konum
    const K = d.konum || {};
    if (!K.error) {
      const row = (l, v, dd) => `<div class="ozp-pos"><span>${l}</span><b>${kmP(v)}</b><em class="${cls(dd)}">${pc(dd)}</em></div>`;
      const ln = (o, nm, fid) => o && isNum(o.R) ? `<button type="button" class="ozp-pl" data-ozgo="${fid}"><b>${nm}</b> ${kmP(o.R)} · ${o.up}↑ / ${o.dn}↓ kayma · ${o.sb} tepki / ${o.sk} kırılma · skor <b>${fN(o.sc || 0, 0)}</b> ›</button>` : "";
      C.push(card("KONUM", "fiyatın seviyelere uzaklığı", `${row("POC", K.poc, K.d_poc)}${row("VAH (değer alanı üstü)", K.vah, K.d_vah)}${row("VAL (değer alanı altı)", K.val, K.d_val)}${row("VWAP", K.vwap, K.d_vwap)}
        <div class="ozp-pos"><span>Gün yükseği (uzaklık)</span><b>${kmP(K.hi)}</b><em>${pc(K.d_hi)}</em></div><div class="ozp-pos"><span>Tavan (uzaklık)</span><b>${kmP(K.tv)}</b><em class="${(K.d_tv ?? 99) <= 3 ? "pos" : ""}">${pc(K.d_tv)}</em></div><div class="ozp-pos"><span>Taban (uzaklık)</span><b>${kmP(K.tb)}</b><em>${pc(K.d_tb)}</em></div>
        ${K.tv_bid != null || K.tv_ask != null ? `<div class="ozp-ln">Tavanda: alış <b class="pos">${fShort(K.tv_bid || 0)}</b> lot · satış <b class="neg">${fShort(K.tv_ask || 0)}</b> lot</div>` : ""}
        ${ln(K.poc_line, "POC Baskısı", "k_poc")}${ln(K.ao_line, "Alış Ort. Baskısı", "k_aort")}`));
    } else C.push(card("KONUM", "", `<div class="empty">${esc(K.error)}</div>`));
    // 6) Operasyon skoru + tarayıcı çipleri
    const O = d.op || {}, CH = d.chips || [], S = d.senaryo;
    C.push(card("OPERASYON SKORU & TARAYICILAR", `${CH.length} tarayıcıda`, `<div class="ozp-op"><div class="op-big" style="--v:${O.score || 0}"><b>${fN(O.score || 0, 0)}</b><small>/100</small></div><div class="muted sm">${O.n || 0} puan kalemi · ⟳ ${esc(O.computed_at || "—")}<br>Çipe dokun → ilgili KEŞFET tarayıcısı</div></div>
      <div class="ozp-chips">${CH.map((c) => `<button type="button" class="ozp-chip ${c.g} ${c.strong ? "strong" : ""}" data-ozgo="${esc(c.id)}"${c.w ? ` data-ozw="${esc(c.w)}"` : ""}>${esc(c.l)}${isNum(c.sc) ? ` <b>${fN(c.sc, 0)}</b>` : ""}${c.rank ? ` <small>#${c.rank}/${c.of}</small>` : ""}${c.txt ? ` <small>${esc(brName(c.txt))}</small>` : ""}</button>`).join("") || `<span class="muted sm">Şu an hiçbir tarayıcıda değil</span>`}</div>
      ${d.chips_note ? `<div class="src-note">${esc(d.chips_note)}</div>` : ""}
      ${S ? `<details class="ozp-sen"><summary>Hazır senaryolar: CİDDİ YÜKSELİŞ ${S.c ? "✓" : "✗"} · TAVAN ADAYI ${S.t ? "✓" : "✗"} (✓/✗ listesi)</summary><div class="bd-cks">${ckList(S.ck_c, "🟢 CİDDİ YÜKSELİŞ")}${ckList(S.ck_t, "🚀 TAVAN ADAYI")}</div></details>` : ""}`));
    // 7) Bugünkü bildirimler
    const { out, hid } = ozpNotifs(d);
    C.push(card(d.live ? "BUGÜNKÜ BİLDİRİMLER" : `BİLDİRİMLER · ${esc(d.day_label || "")}`, `${out.length} olay`, (out.length ? `<div class="ozp-nf">${out.slice(0, 30).map((x) => `<div class="ozp-nfr"><span class="t">${esc((x.time || "").slice(0, 8))}</span><span class="b"><b>${esc(x.title || "")}</b><small>${esc(x.text || "")}</small></span></div>`).join("")}</div>` : `<div class="empty">${d.live ? "Bugün bildirim yok" : "Bu seans için bildirim yok"}</div>`) +
      (hid ? `<div class="src-note">${hid} olay KAPALI bildirim türünde olduğu için gizlendi.</div>` : "")));
    setH(el, `<div class="ozp-grid">${C.join("")}</div>`);
  }
  document.addEventListener("click", (e) => {
    const p = e.target.closest("#ozp, #ozp-top"); if (!p) return;
    const k = e.target.closest("[data-ozkm]"); if (k) { kmOpen(OZP.d.sym, k.dataset.ozkm, OZP.d.day); return; }
    const g = e.target.closest("[data-ozgo]"); if (g && g.dataset.ozgo === "formasyon") { fmChipGo(); return; }   // v1.27.0 FORMASYON çipi → kanıt
    if (g && g.dataset.ozgo === "akd_tab") { openTab("akd"); try { window.scrollTo({ top: 0, behavior: "smooth" }); } catch (x) {} return; }   // v1.26.2 TAHTACI çipi → AKD sekmesi
    if (g) { const id = g.dataset.ozgo; OPS.pendW = g.dataset.ozw || null; kfRun(id); }
  });

  // ------------------------------------------------------------ screen poll
  const scrPoll = {};
  setInterval(() => {
    if (document.hidden) return;
    const now = Date.now();
    const due = (k, ms) => { if (now - (scrPoll[k] || 0) >= ms) { scrPoll[k] = now; return true; } return false; };
    if (st.view === "movers" && due("mv", 3000)) loadMovers();
    else if (st.view === "favs" && due("fv", 5000)) loadMovers();
    else if (st.view === "akis" && due("ak", 3000)) loadEvents(false);
    else if (st.view === "baski" && due("bk", 4000)) loadBaski();
    else if (st.view === "radar" && due("rd", 3000)) loadRadar();
    else if (st.view === "tavan" && due("tt", 3000)) loadTT();
    else if (st.view === "agresif" && due("ag", 2500)) loadAg();
    else if (st.view === "para" && due("pa", 10000)) loadPara();
    else if (st.view === "kurumuyari" && ku.tab === "rapor" && due("kur", 60000)) loadRapor();
    else if (st.view === "tahtaci" && due("th", 20000)) loadTh();
    else if (st.view === "op" && isK(st.opId) && due("opk", isKD(st.opId) ? 8000 : 4000)) opLoad(true);
    else if (st.view === "op" && due("op", 30000)) opLoad(true);
    else if (st.view === "stock" && st.tab === "operasyon" && due("opx", 45000)) opStockLoad(true);
    else if (st.view === "endeks" && due("ix", 3000)) { loadIx(false); if (due("ixc", 30000)) loadIxCatalog(); }
    else if (st.view === "kurum" && due("kr", 15000) && kr.rows.length <= kr.PAGE) loadKurum(true);
    // v1.35.0: İşlemler artık pollIdeal (1 sn) ile birlikte yenilenir
  }, 1000);

  // ----------------------------------------------------------------- boot
  document.addEventListener("visibilitychange", () => { if (!document.hidden) { pollIdeal(true); loadStatus(); } });
  loadList().then(() => { const nm = nameOf(st.sym); if (nm) $("sc-name").textContent = nm; });
  const initHash = location.hash || "";
  selectSymbol(st.sym, { noBack: true });
  const hashGo = (ev0) => { const h = (ev0 === true ? initHash : location.hash || "").replace("#", ""); if (["movers", "hacim", "akis", "baski", "kurum", "favs", "endeks", "radar", "tavan", "agresif", "para", "kurumuyari", "tahtaci", "bildirim", "akdt", "akk", "fm_mum", "fm_grafik"].includes(h)) go(h, { noPush: true });
    else { const m = /^op-(\d+|kademe|teknik|k_[a-z]+)$/.exec(h); if (m) { st.opId = /^\d+$/.test(m[1]) ? +m[1] : m[1]; go("op", { noPush: true }); } } };
  hashGo(true); window.addEventListener("hashchange", hashGo);
  // ===================================================================== v1.22.0 ==
  // ---- v1.38.0: OneSignal KALDIRILDI (eski kod /workspace/tmp/pre1380/) → arka plan bildirimleri TELEGRAM kanalına (sunucudan).
  // Eski çağrı noktaları (osCard / osPaint / osLoadCfg / osRegisterIfApk) Telegram durum kartına bağlandı.
  var OS = { cfg: null };
  async function osLoadCfg() { try { OS.cfg = await api(`/api/telegram/config?cid=${encodeURIComponent(CID)}`, { timeout: 8000 }); } catch (e) {} return OS.cfg; }
  function osRegisterIfApk() {}
  function osCard() {
    const c = OS.cfg;
    const st0 = !c ? "…" : c.ready ? `🟢 Telegram açık · ${esc(c.chat_id || "")}${c.dry ? " (deneme modu)" : ""}` : "⚪ Telegram ayarlı değil";
    return `<div class="os-card"><div class="al-row"><span class="k"><b>✈️ Telegram</b> · arka plan bildirimleri (uygulama kapalıyken de)</span></div>
      <div class="al-row"><span>${st0}</span><button type="button" class="btn-ghost sm" data-gotg="1">Telegram Bildirim Ayarları →</button></div></div>`;
  }
  function osPaint() { const sl = $("os-slot"); if (sl) sl.innerHTML = osCard(); }
  document.addEventListener("click", (e) => { if (e.target && e.target.closest && e.target.closest("[data-gotg]")) { try { idaClose(); } catch (x) {} go("telegram"); } });
  setTimeout(() => osLoadCfg().then(osPaint), 2500);

  // ===================================================================== v1.38.0 TELEGRAM BİLDİRİM AYARLARI
  const TGS = { d: null, msg: null, chats: null, busy: false };
  async function tgPost(url, body) {
    return api(url, { method: "POST", timeout: 20000, body: JSON.stringify(Object.assign({ confirm: true }, body || {})), headers: { "Content-Type": "application/json", "X-BIST-Confirm": "1" } });
  }
  async function tgOpen() { await tgLoad(); clearInterval(TGS.tm); TGS.tm = setInterval(() => { if (st.view !== "telegram") { clearInterval(TGS.tm); return; } if (!document.hidden) tgLoad(true); }, 5000); }
  async function tgLoad(quiet) { try { TGS.d = await api(`/api/telegram/config?cid=${encodeURIComponent(CID)}`, { timeout: 8000 }); OS.cfg = TGS.d; } catch (e) { TGS.err = String(e.message || e); } tgRender(quiet); }
  const TG_GUIDE = [
    ["Bot oluştur", "Telegram'da <b>@BotFather</b>'ı aç → <code>/newbot</code> yaz → bota bir ad ver (ör. BIST Canlı) → kullanıcı adı ver (sonu <code>bot</code> ile bitmeli, ör. <code>bistcanli_ender_bot</code>). BotFather sana <b>token</b> verir: <code>123456789:AA…</code> — kimseyle paylaşma."],
    ["Kanal oluştur", "Telegram → Yeni Kanal → ad ver (ör. BIST Bildirimleri) → Özel ya da Herkese açık (herkese açıksa bir <code>@kullaniciadi</code> seç)."],
    ["Botu yönetici yap", "Kanal → Yöneticiler → Yönetici ekle → botunu ara (@…bot) → yalnız <b>Mesaj gönderme (Post messages)</b> izni yeterli → Kaydet."],
    ["Token'ı kaydet", "Aşağıdaki <b>Bot Token</b> alanına yapıştır → <b>Kaydet</b>. Token sunucuda saklanır; ekranda yalnız son 4 hanesi görünür."],
    ["Chat ID'yi bul", "Kanala herhangi bir mesaj yaz (ör. <i>merhaba</i>) → burada <b>Chat ID'yi otomatik bul</b>'a dokun → kanalını seç. (Herkese açık kanalda <code>@kanaladi</code> da yazılabilir; özel kanal <code>-100…</code> ile başlar.)"],
    ["Test et", "<b>Test mesajı gönder</b> → birkaç saniye içinde kanala ✅ mesajı düşmeli. Sonra aşağıdan hangi bildirimlerin gideceğini seç."],
  ];
  function tgRender(quiet) {
    const body = $("tg-body"); if (!body) return;
    const d = TGS.d;
    if (!d) { body.innerHTML = `<div class="card"><div class="empty">${TGS.err ? "Alınamadı: " + esc(TGS.err) : "Yükleniyor…"}</div></div>`; return; }
    const S = d.status || {};
    const stat = `<section class="card"><div class="card-h"><span class="card-title">DURUM</span><span class="tg-pill ${d.ready ? "ok" : "off"}">${d.ready ? (d.dry ? "DENEME MODU" : "AÇIK") : "AYARLI DEĞİL"}</span></div>
      <div class="al-row"><span class="k">Son gönderim</span><b>${esc(S.last_sent || "—")}</b></div>
      <div class="al-row"><span class="k">Kuyruk</span><b>${fN(S.queue || 0)}${S.next_try_in ? ` · ${S.next_try_in} sn sonra tekrar` : ""}</b></div>
      <div class="al-row"><span class="k">Gönderilen / hata</span><b>${fN(S.sent || 0)} / ${fN(S.failed || 0)}</b></div>
      <div class="al-row"><span class="k">Son hata</span><span class="${S.last_err ? "neg" : "muted"}">${esc(S.last_err ? S.last_err + (S.last_err_ts ? " · " + S.last_err_ts : "") : "yok")}</span></div>
      <div class="al-row"><span class="k">Birleştirilen / tekrar atlanan</span><span class="muted">${fN(S.merged || 0)} / ${fN(S.deduped || 0)}</span></div>
      <div class="al-row"><span class="k">Link (mesajlardaki)</span><span class="muted sm">${esc(d.public_url || "—")}</span></div></section>`;
    if (quiet && $("tg-stat")) { $("tg-stat").innerHTML = stat; return; }
    const guide = `<section class="card tg-guide"><div class="card-h"><span class="card-title">📘 KURULUM REHBERİ (2 dk)</span></div>
      <ol>${TG_GUIDE.map(([h, t]) => `<li><b>${h}</b><div>${t}</div></li>`).join("")}</ol></section>`;
    const form = `<section class="card"><div class="card-h"><span class="card-title">✈️ BAĞLANTI</span></div>
      <label class="os-f"><span>Bot Token ${d.has_token ? `<i class="muted">(kayıtlı · …${esc(d.token_last4)})</i>` : ""}</span><input type="password" id="tg-tok" autocomplete="new-password" spellcheck="false" placeholder="${d.has_token ? "değiştirmek için yeni token yapıştır" : "123456789:AA…"}"/></label>
      <label class="os-f"><span>Chat ID</span><input type="text" id="tg-chat" autocomplete="off" spellcheck="false" placeholder="@kanaladi ya da -100…" value="${esc(d.chat_id || "")}"/></label>
      <div class="tg-btns"><button type="button" class="btn-ghost tg-save" data-tg="save">Kaydet</button><button type="button" class="btn-ghost" data-tg="find">Chat ID'yi otomatik bul</button><button type="button" class="btn-ghost" data-tg="test">Test mesajı gönder</button>${d.has_token || d.chat_id ? `<button type="button" class="btn-ghost sm" data-tg="clear">Sil</button>` : ""}</div>
      ${TGS.chats ? `<div class="tg-chats">${TGS.chats.length ? TGS.chats.map((c) => `<button type="button" class="obt-pre" data-tgchat="${esc(String(c.username ? "@" + c.username : c.id))}">${c.type === "channel" ? "📢" : c.type === "private" ? "👤" : "👥"} ${esc(c.title || "")} <span class="muted">${esc(String(c.username ? "@" + c.username : c.id))}</span></button>`).join("") : `<div class="muted sm">${esc(TGS.chatsNote || "Sohbet bulunamadı")}</div>`}</div>` : ""}
      <div class="tg-msg ${TGS.msg ? TGS.msg.t : ""}" id="tg-msg">${TGS.msg ? esc(TGS.msg.x) : ""}</div>
      <div class="src-note">Token yalnız sunucuda (<code>data/telegram.json</code>, izin 600) saklanır; hiçbir yanıtta geri gönderilmez.</div></section>`;
    const cats = d.cats || {}, L = d.cat_labels || {};
    const q = d.quiet || {};
    const catc = `<section class="card"><div class="card-h"><span class="card-title">NE GÖNDERİLSİN?</span></div>
      ${Object.keys(L).map((k) => `<label class="tg-row"><input type="checkbox" data-tgcat="${k}" ${cats[k] !== false ? "checked" : ""}/> ${esc(L[k])}</label>`).join("")}
      <label class="tg-row"><input type="checkbox" id="tg-q" ${q.on ? "checked" : ""}/> Sessiz saatler (yalnız sinyaller susar)
        <input type="time" id="tg-qf" value="${esc(q.from || "23:00")}"/>–<input type="time" id="tg-qt" value="${esc(q.to || "08:00")}"/></label>
      <div class="al-row"><span class="muted sm">Tür/filtre ayarları: ${d.this_is_owner ? "<b>bu cihazınkiler</b> kullanılıyor ✓" : "başka bir cihazınkiler kullanılıyor"}</span>${d.this_is_owner ? "" : `<button type="button" class="btn-ghost sm" data-tg="owner">Bu cihazın ayarlarını kullan</button>`}</div></section>`;
    const sig = `<section class="card"><div class="card-h"><span class="card-title">SİNYALLER — TÜR BAZINDA</span></div>
      <div class="src-note">Telegram'a yalnız <b>BİLDİRİM</b> modundaki türler gider (GÖRÜNTÜLE / KAPALI gitmez). Modlar eskiden OneSignal'a gidenlerle aynen taşındı.</div>
      <div class="nf-gset"><span class="muted sm">Ana anahtar:</span><label class="nf-sw"><input type="checkbox" id="tg-master" ${NP.master !== false ? "checked" : ""}/><span></span>${NP.master !== false ? "AÇIK" : "TÜMÜ KAPALI"}</label></div></section>` +
      NT_GROUPS.map((G) => `<section class="card nf-grp ${NP.master === false ? "dim" : ""}"><div class="card-h"><span class="nf-gt"><i style="background:${G.dot}"></i>${G.name}<small>${G.items.length}</small></span></div>
        <div class="nf-gset"><span class="muted sm">Tümü:</span>${MODE_L.map(([v, l]) => `<button type="button" data-gset="${G.g}:${v}" class="nf-gb ${v}">${l}</button>`).join("")}</div>
        ${G.items.map(([k]) => ntRow(k, false)).join("")}</section>`).join("");
    body.innerHTML = `<div id="tg-stat">${stat}</div>` + form + guide + catc + sig;
  }
  document.addEventListener("click", async (e) => {
    const c = e.target.closest && e.target.closest("[data-tgchat]");
    if (c) { const i = $("tg-chat"); if (i) i.value = c.dataset.tgchat; TGS.msg = { t: "info", x: "Seçildi — Kaydet'e dokunun." }; const m = $("tg-msg"); if (m) { m.className = "tg-msg info"; m.textContent = TGS.msg.x; } return; }
    const b = e.target.closest && e.target.closest("[data-tg]"); if (!b || st.view !== "telegram") return;
    const act = b.dataset.tg; let r;
    try {
      b.disabled = true;
      if (act === "save") {
        const tok = ($("tg-tok").value || "").trim(), chat = ($("tg-chat").value || "").trim();
        r = await tgPost("/api/telegram/settings", Object.assign({ chat_id: chat, owner_cid: (TGS.d && TGS.d.owner_cid) ? undefined : CID }, tok ? { token: tok } : {}));
        TGS.msg = r.ok ? { t: "ok", x: "Kaydedildi ✓" + (r.bot ? " · bot @" + r.bot : "") + " — şimdi 'Test mesajı gönder'." } : { t: "err", x: r.error || "Kaydedilemedi" };
      } else if (act === "find") {
        r = await tgPost("/api/telegram/find_chat", {});
        if (r.ok) { TGS.chats = r.chats || []; TGS.chatsNote = r.note; TGS.msg = { t: "info", x: TGS.chats.length ? "Kanalını seç:" : (r.note || "") }; } else TGS.msg = { t: "err", x: r.error || "Bulunamadı" };
      } else if (act === "test") {
        r = await api("/api/telegram/test", { method: "POST", body: JSON.stringify({ feature: "" }), headers: { "Content-Type": "application/json" } });
        TGS.msg = r.ok ? { t: "ok", x: (r.dry ? "Deneme modu: mesaj kanala gitmedi, sunucu günlüğüne yazıldı ✓" : "Test mesajı kuyruğa alındı — birkaç saniye içinde kanala düşer ✓") } : { t: "err", x: r.error || "Gönderilemedi" };
      } else if (act === "clear") {
        if (!confirm("Bot Token ve Chat ID silinsin mi? Telegram bildirimleri durur.")) return;
        r = await tgPost("/api/telegram/clear", {}); TGS.msg = r.ok ? { t: "ok", x: "Silindi." } : { t: "err", x: r.error || "" };
      } else if (act === "owner") {
        r = await tgPost("/api/telegram/settings", { owner_cid: CID }); TGS.msg = r.ok ? { t: "ok", x: "Bu cihazın bildirim türü ayarları kullanılacak ✓" } : { t: "err", x: r.error || "" };
      }
    } catch (x) { TGS.msg = { t: "err", x: String(x.message || x) }; }
    finally { b.disabled = false; }
    await tgLoad();
  });
  document.addEventListener("change", async (e) => {
    if (st.view !== "telegram") return;
    const c = e.target.closest("[data-tgcat]");
    if (c) { await tgPost("/api/telegram/settings", { cats: { [c.dataset.tgcat]: c.checked } }).catch(() => {}); return tgLoad(); }
    if (["tg-q", "tg-qf", "tg-qt"].includes(e.target.id)) { await tgPost("/api/telegram/settings", { quiet: { on: $("tg-q").checked, from: $("tg-qf").value, to: $("tg-qt").value } }).catch(() => {}); return tgLoad(); }
    if (e.target.id === "tg-master") { NP.master = e.target.checked; saveNP(); tgRender(); }
  });

  // ===================================================================== v1.25.0 ==
  // ---- DERİNLİK ANALİZLERİ (sunucu app/v125.py · /api/stocks/{sym}/derinlik-plus) — DERİNLİK sekmesinde mevcut defterin
  // çevresinde kartlar + merdiven işaretleri; Ayarlar'da madde başına aç/kapat (localStorage "drOn", varsayılan hepsi açık).
  // Kapalı kartlar istenmez / hesaplanmaz; hepsi kapalıysa hiç istek atılmaz.
  var DRI = [
    [1, "a", "ALIŞ / SATIŞ DENGESİ", "Alış/satış dengesi", "İlk 5 / 10 / 25 kademe toplam lot oranı + son 1 dk değişim"],
    [15, "a", "MERDİVEN İŞARETLERİ", "POC / VWAP / kurum maliyetleri", "POC, VWAP, aktif alış ortalaması ve ısrarcı kurum maliyetleri derinlik merdiveninde"],
    [2, "a", "DUVAR TAKİBİ", "Duvar takibi", "En büyük alış/satış duvarları, ne zamandır orada oldukları, büyüyor mu eriyor mu"],
    [3, "a", "SAHTE DUVAR (SPOOFING)", "Sahte duvar (spoofing)", "Fiyat yaklaşınca işlem görmeden çekilen büyük emirler"],
    [4, "a", "GİZLİ EMİR (ICEBERG)", "Gizli emir (iceberg)", "İşlem gördükçe aynı kademenin tekrar tekrar dolması"],
    [5, "a", "KADEME YENİLEME HIZI", "Kademe yenileme hızı", "Süpürülen kademenin ne kadar sürede yeniden dolduğu"],
    [7, "a", "KADEME ÇİZME", "Kademe çizme", "Alış tarafının yukarı çıkması / satışların geri çekilmesi"],
    [8, "a", "TAVAN / TABAN KUYRUĞU", "Tavan/taban kuyruğu", "Tavanda/tabanda bekleyen lot ve eriyip erimediği"],
    [9, "a", "EMİR SAYISI VE LOT", "Emir sayısı ve lot", "Kademe başına emir sayısı, ortalama emir büyüklüğü, az emirle büyük lot = kurumsal"],
    [10, "a", "SON SÜPÜRMELER", "Son süpürmeler", "Aktif alışla az önce temizlenen satış kademeleri"],
    [11, "g", "DERİNLİK ISI HARİTASI", "Derinlik ısı haritası", "Gün boyu her fiyatta ne kadar emir beklediği"],
    [12, "g", "DESTEK / DİRENÇ HARİTASI", "Destek/direnç haritası", "Duvarların en çok tuttuğu fiyatlar"],
    [13, "g", "DERİNLİK – İŞLEM UYUMU", "Derinlik ile işlem uyumu", "Görünen duvarlar gerçekten işlem görüyor mu, yoksa sadece gösteriş mi"],
    [14, "g", "DENGESİZLİK GRAFİĞİ", "Dengesizlik grafiği", "Gün boyu dakika dakika alış/satış oranı"],
    [16, "t", "DERİNLİK SKORU", "Derinlik skoru ve yorum", "Yukarıdakileri birleştiren skor ve tek cümlelik Türkçe yorum"],
    [17, "g", "DERİNLİK ALARMLARI", "Derinlik alarmları", "Duvar eriyor · büyük emir girişi · alış yönüne sert denge kayması (bildirim türleri)"],
  ];
  var DR = { d: null, gen: -1, sym: null, busy: false, last: 0, on: LS.get("drOn", {}) || {}, built: false, hsig: "", tm: 0 };
  function drOn(n) { return !DR || !DR.on || DR.on[n] !== false; }
  function drItems() { if (!DRI) return []; return DRI.map((x) => x[0]).filter(drOn).sort((a, b) => a - b); }
  const drTL = (v) => (isNum(v) ? fShort(v) + " ₺" : "—");
  const drX = (r) => (isNum(r) ? nf(2).format(r) + "×" : "—");
  const drL = (v) => (isNum(v) ? fShort(v) : "—");
  function drDur(s) { if (!isNum(s)) return "—"; s = Math.round(s); if (s < 60) return s + " sn"; if (s < 3600) return Math.floor(s / 60) + " dk " + (s % 60 ? (s % 60) + " sn" : ""); return Math.floor(s / 3600) + " sa " + Math.floor((s % 3600) / 60) + " dk"; }
  const drKV = (k, v, c) => `<div class="ozp-kv"><small>${esc(k)}</small><b class="${c || ""}">${v}</b></div>`;
  const drLive = (x) => `<div class="dr-live">⏳ ${esc((x && x.note) || "canlı seansla başlar")}</div>`;
  const drNote = (t) => (t ? `<div class="src-note">${esc(t)}</div>` : "");
  const drSide = (s) => (s === "ALIŞ" || s === "b" ? `<b class="pos">ALIŞ</b>` : `<b class="neg">SATIŞ</b>`);

  function drBuild() {
    if (!DR || DR.built) return;
    const top = $("dr-top"), a = $("dr-a"), g = $("dr-g"); if (!top || !a || !g) return;
    const card = (x) => `<section class="card dr-card" data-dri="${x[0]}" hidden><div class="card-h"><span class="card-title">${esc(x[2])}</span><span class="dr-bdg" id="drb-${x[0]}"></span></div><div class="dr-body" id="drc-${x[0]}"><div class="empty">Yükleniyor…</div></div></section>`;
    top.innerHTML = DRI.filter((x) => x[1] === "t").map(card).join("");
    a.innerHTML = `<div class="dr-sec" data-drsec="a"><span>ANLIK DERİNLİK ANALİZLERİ</span><button type="button" class="btn-ghost sm" data-drset="1">⚙ Ayarlar</button></div>` + DRI.filter((x) => x[1] === "a").map(card).join("");
    g.innerHTML = `<div class="dr-sec" data-drsec="g"><span>GÜN İÇİ (GENEL) ANALİZLER</span><button type="button" class="btn-ghost sm" data-drset="1">⚙ Ayarlar</button></div>` + DRI.filter((x) => x[1] === "g").map(card).join("");
    DR.built = true;
    drVis();
  }
  function drVis() {
    let need = false;
    DRI.forEach(([n]) => { const c = document.querySelector(`.dr-card[data-dri="${n}"]`); if (!c) return; const on = drOn(n); c.hidden = !on; if (on && DR.d && DR.d.r && !(String(n) in DR.d.r)) need = true; });
    ["a", "g"].forEach((s) => { const h = document.querySelector(`[data-drsec="${s}"]`); if (h) h.hidden = !DRI.some((x) => x[1] === s && drOn(x[0])); });
    const off = $("dr-off"); if (off) off.hidden = drItems().length > 0;
    return need;
  }
  function drApply() {
    if (!DR) return;   // betik yüklenirken (ilk openTab) henüz tanımlı değil
    drBuild();
    const need = drVis();
    if (DR.d) drRender();
    if (need) drPoll(true);
    try { if (st.ideal && st.tab === "derinlik") renderDerinlik(); } catch (e) {}
  }
  function drReset() {
    DR.d = null; DR.hsig = ""; DR.gen = st.gen; DR.sym = st.sym; DR.last = 0; DR.err = 0;
    document.querySelectorAll(".dr-body").forEach((b) => { setH(b, `<div class="empty">Yükleniyor…</div>`); });
    document.querySelectorAll(".dr-bdg").forEach((b) => { b.textContent = ""; b._h = ""; });
  }
  async function drPoll(force) {
    if (!DR) return;
    if (st.view !== "stock" || st.tab !== "derinlik" || document.hidden) return;
    drBuild();
    if (DR.gen !== st.gen || DR.sym !== st.sym) drReset();
    const its = drItems(); if (!its.length) return;
    // v1.38.1: seans dışı / canlı akış yok → bir kez + 60 sn'de bir (ya da ↻); canlı 3 sn; hata/yavaşlıkta geri çekil
    const iv = (DR.d && DR.d.live ? 3000 : 60000) * pollMul() + (DR.err ? Math.min(60000, 5000 * 2 ** (DR.err - 1)) : 0);
    if (!force && Date.now() - DR.last < (DR.d || DR.err ? iv : 0)) return;
    if (DR.busy) return;
    DR.busy = true; DR.last = Date.now();
    const gen = st.gen, sym = st.sym;
    try {
      const d = await api(`/api/stocks/${sym}/derinlik-plus?items=${its.join(",")}`, { timeout: 45000 });
      if (gen !== st.gen || sym !== st.sym) return;
      DR.d = d; DR.err = 0; drRender();
      try { if (st.ideal) renderDerinlik(); } catch (e) {}
    } catch (e) {
      DR.err = Math.min(6, (DR.err || 0) + 1);
      const m = `sunucu meşgul, tekrar deneniyor (${Math.round(Math.min(60000, 5000 * 2 ** (DR.err - 1)) / 1000)} sn içinde) — ↻ ile hemen`;
      if (!DR.d) document.querySelectorAll(".dr-body").forEach((b) => setH(b, `<div class="empty">${esc(m)}</div>`));
      else if (Date.now() - (DR.toastTs || 0) > 60000) { DR.toastTs = Date.now(); toast("Derinlik analizleri: " + m); }   // son iyi veri ekranda kalır
    } finally { DR.busy = false; }
  }
  setInterval(() => drPoll(false), 1000);

  function drRender() {
    if (!DR) return;
    const d = DR.d; if (!d || !d.r) return;
    if (d.error) { const c = $("drc-16"); if (c) setH(c, `<div class="empty">Hata: ${esc(d.error)}</div>`); }
    DRI.forEach(([n]) => {
      if (!drOn(n)) return;
      const x = d.r[String(n)]; if (x === undefined) return;
      const el = $("drc-" + n); if (!el) return;
      let h = "";
      try { h = (DRR[n] || (() => ""))(x, d); } catch (e) { h = `<div class="empty">Gösterilemedi: ${esc(e.message || e)}</div>`; }
      setH(el, h);
      const bd = $("drb-" + n);
      if (bd) {
        const k = x.live_only ? ["CANLI SEANSLA", "live"] : x.kind === "işlem" ? ["VEKİL · İŞLEM VERİSİ", "vek"] : (x.kind === "derinlik" || x.hist || (n === 16 && d.hist)) ? [d.live ? "CANLI DERİNLİK" : "DERİNLİK KAYDI", "ok"] : n === 17 ? [d.live ? "CANLI" : "SEANS DIŞI", d.live ? "ok" : "live"] : [d.live ? "CANLI" : "SON GÖRÜNTÜ", d.live ? "ok" : "snap"];
        const t = `<i class="dr-b ${k[1]}">${k[0]}</i>`; if (bd._h !== t) { bd.innerHTML = t; bd._h = t; }
      }
      if (n === 11) drHeat(x, d);
    });
  }

  const DRR = {
    16(x, d) {
      const sc = x.score, c = sc >= 57 ? "pos" : sc <= 43 ? "neg" : "";
      const tr = (t) => String(t || "").replace(/(\d)\.(\d)/g, "$1,$2");   // sunucu metnindeki ondalık nokta → virgül
      return `<div class="dr-score"><div class="dr-sc ${c}"><b>${isNum(sc) ? sc : "—"}</b><small>/100</small></div><div class="dr-sct"><b class="${c}">${esc(x.label || "")}</b><div class="ozp-yt">${esc(tr(x.yorum))}</div></div></div>
        ${(x.comps || []).length ? `<div class="dr-comps">${x.comps.map(([l, v]) => `<span class="dr-cmp ${v > 0 ? "pos" : v < 0 ? "neg" : ""}">${v > 0 ? "+" : ""}${nf(1).format(v)} · ${esc(tr(l))}</span>`).join("")}</div>` : ""}
        <div class="src-note">${esc(d.day_label || "")} · kaynak: ${esc(d.src || "—")} · ${esc(d.rec_note || "")} <button type="button" class="btn-ghost sm" data-drset="1">⚙ Derinlik Analizleri ayarları</button></div>`;
    },
    1(x) {
      const row = (n) => { const r = x[n] || {}; const bp = isNum(r.bp) ? r.bp : 50;
        return `<div class="dr-bal"><span class="dr-bk">${n} KADEME</span><div class="press-bar thin"><span style="width:${bp.toFixed(1)}%"></span></div><span class="dr-bv"><b class="pos">${drL(r.bl)}</b> / <b class="neg">${drL(r.al)}</b> lot · <b class="${r.r >= 1.2 ? "pos" : r.r <= 0.83 ? "neg" : ""}">${drX(r.r)}</b></span><span class="dr-bt muted">${drTL(r.b)} / ${drTL(r.a)}</span></div>`; };
      let ch = "";
      if (x.ch) ch = `<div class="dr-chs"><span class="muted sm">Son ${drDur(x.ch.sec)}:</span>${["5", "10", "25"].map((n) => { const c = x.ch[n] || {}; return `<span class="dr-cmp ${c.d > 0 ? "pos" : c.d < 0 ? "neg" : ""}">${n}: ${drX(c.r0)} → ${drX(c.r1)} (${c.d > 0 ? "+" : ""}${isNum(c.d) ? nf(2).format(c.d) : "—"})</span>`; }).join("")}</div>`;
      else ch = `<div class="dr-live">⏳ 1 dk değişim: ${esc(x.ch_note || "")}</div>`;
      return row("5") + row("10") + row("25") + ch + `<div class="src-note">Oran = alış lot ÷ satış lot. Çubuk: alış payı.</div>`;
    },
    15(x, d) {
      const L = x.list || [];
      if (!L.length) return `<div class="empty">POC / VWAP / maliyet verisi henüz yok (işlem taraması hazırlanıyor olabilir)</div>`;
      const last = d.last;
      return `<div class="dr-mk">${L.map((m) => { const dv = isNum(last) && last > 0 && isNum(m.p) ? ((m.p / last - 1) * 100) : null;
        const lb = m.k === "MALİYET" ? `MALİYET · ${esc(m.br || "")}${isNum(m.israr) ? ` <small>ısrar ${fN(m.israr)}</small>` : ""}` : esc(m.k);
        return `<div class="dr-mki ${m.k === "POC" ? "poc" : m.k === "VWAP" ? "vwap" : m.k === "MALİYET" ? "mal" : "aort"}"><small>${lb}</small><b>${fP(m.p)}</b><small class="muted">${isNum(dv) ? (dv >= 0 ? "+" : "") + nf(2).format(dv) + "%" : ""}</small></div>`; }).join("")}</div>
        <div class="src-note">Merdivende ilgili fiyatın yanında etiketlenir (en yakın kademe, ±1 adım). Maliyetler: v1.23 ısrarcı kurumlar (en yüksek ısrar ilk 3).</div>`;
    },
    2(x) {
      const W = (L, s) => (L || []).length ? L.map((w) => `<div class="dr-w"><div class="dr-wh">${s === "b" ? `<b class="pos">${fP(w.p)}</b>` : `<b class="neg">${fP(w.p)}</b>`}<span>${fN(w.lot)} lot · ${drTL(w.tl)}</span><span class="muted">${isNum(w.x) ? nf(1).format(w.x) + "× medyan" : ""} · ${fN(w.ord)} emir</span></div>
          <div class="dr-wd">${isNum(w.dur) ? `<span>⏱ ${drDur(w.dur)}${w.first ? ` (${esc(w.first)}'den beri)` : ""}</span>` : `<span class="muted">⏱ süre: canlı seansla</span>`}${w.trend ? `<span class="${w.trend === "ERİYOR" ? (s === "a" ? "pos" : "neg") : w.trend === "BÜYÜYOR" ? (s === "a" ? "neg" : "pos") : "muted"}">${esc(w.trend)}${isNum(w.trend_ch) ? ` (${w.trend_ch > 0 ? "+" : ""}${nf(0).format(w.trend_ch)}%)` : ""}</span>` : ""}${isNum(w.fill) && (w.fill || w.canc) ? `<span class="muted">işlem ${drL(w.fill)} · iptal ${drL(w.canc)}</span>` : ""}${isNum(w.dist) ? `<span class="muted">son fiyata uzaklık %${nf(2).format(Math.abs(w.dist))}</span>` : ""}</div></div>`).join("") : `<div class="empty sm">Belirgin duvar yok</div>`;
      const G = (x.gone || []).slice(0, 6);
      return `<div class="dr-2c"><div><div class="dr-st pos">ALIŞ DUVARLARI</div>${W(x.b, "b")}</div><div><div class="dr-st neg">SATIŞ DUVARLARI</div>${W(x.a, "a")}</div></div>
        ${G.length ? `<div class="dr-st">BİTEN DUVARLAR</div>${G.map((g) => `<div class="dr-li"><span class="muted">${esc(g.t)}</span>${drSide(g.side)}<b>${fP(g.p)}</b><span>${drL(g.peak)} lot</span><span class="${/SÜPÜR/.test(g.st) ? "pos" : /İPTAL/.test(g.st) ? "warn" : "muted"}">${esc(g.st)}</span></div>`).join("")}` : ""}
        ${x.hist ? "" : `<div class="dr-live">⏳ ${esc(x.note || "Süre ve büyüyor/eriyor bilgisi canlı seansla başlar")}</div>`}
        <div class="src-note">Duvar: ilk 15 kademe medyanının ≥3 katı ve ≥500 bin ₺.</div>`;
    },
    3(x) {
      if (x.live_only) return drLive(x);
      const L = x.list || [];
      return `<div class="ozp-kvs">${drKV("Bugün", fN(x.n))}${drKV("Alışta (sahte destek)", fN(x.nb), x.nb ? "neg" : "")}${drKV("Satışta (sahte direnç)", fN(x.na), x.na ? "pos" : "")}</div>
        ${L.length ? L.map((s) => `<div class="dr-li"><span class="muted">${esc(s.t)}</span>${drSide(s.side)}<b>${fP(s.p)}</b><span>${drL(s.peak)} lot · ${drTL(s.tl)}</span><span class="muted">${drDur(s.dur)} durdu · işlem ${drL(s.fill)} / iptal ${drL(s.canc)}</span></div>`).join("") : `<div class="empty sm">Bugün sahte duvar tespit edilmedi</div>`}
        <div class="src-note">Fiyat ≤3 adım (veya %0,6) yaklaşınca, büyük kısmı işlem görmeden iptal edilen duvarlar.</div>`;
    },
    4(x) {
      if (x.live_only) return drLive(x);
      const L = x.list || [], Wt = x.watch || [];
      return `${L.length ? L.map((z) => `<div class="dr-li"><span class="muted">${esc(z.t)}</span>${drSide(z.side)}<b>${fP(z.p)}</b><span>görünen en çok ${drL(z.mx)} lot</span><span>işlem ${drL(z.tr)} lot (${drX(z.x)})</span><span class="muted">${fN(z.ref)} yenileme · ${drTL(z.tl)}</span></div>`).join("") : `<div class="empty sm">Bugün gizli emir tespit edilmedi</div>`}
        ${Wt.length ? `<div class="dr-st">İZLENEN KADEMELER</div>${Wt.map((z) => `<div class="dr-li">${drSide(z.side)}<b>${fP(z.p)}</b><span>işlem ${drL(z.tr)} / görünen ${drL(z.mx)}</span><span class="muted">${fN(z.ref)} yenileme</span></div>`).join("")}` : ""}
        <div class="src-note">Gizli emir: en iyi kademe işlem gördükçe ≥3 kez yeniden dolmuş, işlem gören lot görünenin ≥2 katı ve ≥250 bin ₺.</div>`;
    },
    5(x) {
      if (x.live_only) return drLive(x);
      const L = x.list || [];
      return `<div class="ozp-kvs">${drKV("Satış kademesi dolma", x.avg_a != null ? "ort. " + drDur(x.avg_a) : "—", x.avg_a != null && x.avg_a <= 10 ? "neg" : "")}${drKV("Alış kademesi dolma", x.avg_b != null ? "ort. " + drDur(x.avg_b) : "—")}${drKV("Süpürülen / dolan", `${fN(x.n)} / ${fN(x.done)}`)}${drKV("5 dk'da dolmayan", fN(x.never))}${drKV("Bekleyen", fN(x.pend))}</div>
        ${L.length ? L.map((r) => `<div class="dr-li"><span class="muted">${esc(r.t)}</span>${drSide(r.side)}<b>${fP(r.p)}</b><span>${drL(r.lot)} lot</span><span class="${r.s == null ? "pos" : r.s <= 10 ? "neg" : ""}">${r.s == null ? "dolmadı" : drDur(r.s) + "'de doldu"}</span></div>`).join("") : `<div class="empty sm">Bugün süpürülen kademe yok</div>`}
        <div class="src-note">Hızlı dolan satış kademesi = arkada satıcı var; dolmayan = satıcı tükeniyor.</div>`;
    },
    7(x) {
      if (x.live_only) return drLive(x);
      const C = [["m5", "5 DK"], ["m15", "15 DK"], ["day", "GÜN"]];
      const R = [["bu", "Alış yukarı çıktı", "pos"], ["ac", "Satış geri çekildi", "pos"], ["bc", "Alış geri çekildi", "neg"], ["ad", "Satış aşağı indi", "neg"]];
      return `<table class="dr-t"><thead><tr><th></th>${C.map((c) => `<th>${c[1]}</th>`).join("")}</tr></thead><tbody>${R.map((r) => `<tr><td class="${r[2]}">${r[1]}</td>${C.map((c) => `<td>${fN((x[c[0]] || {})[r[0]])}</td>`).join("")}</tr>`).join("")}
        <tr class="dr-net"><td>NET</td>${C.map((c) => { const v = (x[c[0]] || {}).net; return `<td class="${v > 0 ? "pos" : v < 0 ? "neg" : ""}">${v > 0 ? "+" : ""}${fN(v)}</td>`; }).join("")}</tr></tbody></table>
        <div class="src-note">En iyi alış fiyatının yükselmesi / en iyi satışın yukarı çekilmesi (+) — tersi (−).</div>`;
    },
    8(x) {
      let h = `<div class="ozp-kvs">${drKV("Tavan", fP(x.tv), "pos")}${drKV("Taban", fP(x.tb), "neg")}`;
      if (x.at === "tv") h += drKV("TAVANDA ALIŞ KUYRUĞU", `${drL(x.lot)} lot`, "pos") + drKV("Emir / tutar", `${fN(x.ord)} · ${drTL(x.tl)}`) + drKV("Tavandan satış", `${drL(x.opp)} lot`);
      else if (x.at === "tb") h += drKV("TABANDA SATIŞ KUYRUĞU", `${drL(x.lot)} lot`, "neg") + drKV("Emir / tutar", `${fN(x.ord)} · ${drTL(x.tl)}`);
      else h += drKV("Durum", "Tavanda / tabanda değil") + (isNum(x.tv_ask) ? drKV("Tavanda bekleyen satış", drL(x.tv_ask) + " lot") : "");
      h += `</div>`;
      if (x.state) h += `<div class="ozp-kvs">${drKV("Kuyruk durumu", esc(x.state), x.state === "ERİYOR" ? (x.side === "tv" ? "neg" : "pos") : x.state === "BÜYÜYOR" ? (x.side === "tv" ? "pos" : "neg") : "")}${drKV("10 dk tepe → şimdi", `${drL(x.peak10)} → ${drL(x.cur)}`)}${drKV("10 dk erime", isNum(x.melt10) ? "%" + nf(1).format(x.melt10) : "—")}${drKV("Gün tepe", drL(x.peak))}</div>` + drSpark(x.series);
      else if (x.note) h += `<div class="dr-live">⏳ ${esc(x.note)}</div>`;
      return h;
    },
    9(x) {
      if (!x.has) return `<div class="empty">Bu defterde kademe emir sayısı yok</div>`;
      const R = x.rows || [];
      const T = (s) => `<table class="dr-t dr-o"><thead><tr><th>#</th><th>FİYAT</th><th>LOT</th><th>EMİR</th><th>ORT.</th></tr></thead><tbody>${R.filter((r) => r.side === s).map((r) => `<tr class="${r.inst ? "inst" : ""}"><td>${r.lvl}</td><td class="${s === "b" ? "pos" : "neg"}">${fP(r.p)}${r.inst ? " 🏛" : ""}</td><td>${drL(r.lot)}</td><td>${fN(r.ord)}</td><td>${drL(r.avg)}</td></tr>`).join("") || `<tr><td colspan="5" class="empty">—</td></tr>`}</tbody></table>`;
      const I = x.inst || [];
      return `<div class="ozp-kvs">${drKV("Alış emir (25 kad.)", fN(x.ob), "pos")}${drKV("Satış emir (25 kad.)", fN(x.oa), "neg")}${drKV("Ort. alış emri", drL(x.avg_b) + " lot")}${drKV("Ort. satış emri", drL(x.avg_a) + " lot")}</div>
        <div class="dr-2c"><div><div class="dr-st pos">ALIŞ</div>${T("b")}</div><div><div class="dr-st neg">SATIŞ</div>${T("a")}</div></div>
        ${I.length ? `<div class="dr-inst">🏛 KURUMSAL GÖRÜNÜM: ${I.map((r) => `${r.side === "b" ? "alış" : "satış"} ${fP(r.p)} (${fN(r.ord)} emir, ort. ${drL(r.avg)} lot)`).join(" · ")}</div>` : ""}
        <div class="src-note">🏛 = az emirle büyük lot (≤3 emir ve ≥1 Mn ₺, ya da ≤10 emir ve ortalama emir medyanın ≥5 katı, ≥500 bin ₺). Emir sayısı İdealData defterinden.</div>`;
    },
    10(x) {
      const L = x.list || [];
      if (!L.length) return `<div class="empty">${esc(x.note || "Bugün ≥100 bin ₺ aktif alış süpürmesi yok")}</div>`;
      return `<div class="ozp-kvs">${drKV("Gün toplam", fN(x.n) + " süpürme")}${drKV("Son 15 dk", fN(x.n15) + " · " + drTL(x.tl15), x.n15 ? "pos" : "")}</div>
        ${L.map((s) => `<div class="dr-li"><span class="muted">${esc(s.t)}</span><b class="pos">${fN(s.nlev)} kademe</b><span>${fP(s.p0)} → ${fP(s.p1)}</span><span>${drL(s.lot)} lot · ${drTL(s.tl)}</span>${s.br ? `<span class="muted">${esc(s.br)}</span>` : ""}</div>`).join("")}
        <div class="src-note">Aktif alışla tek seferde ≥2 satış kademesinin temizlendiği işlemler (≥100 bin ₺).</div>`;
    },
    11(x) {
      if (x.empty) return x.note ? drLive(x) : `<div class="empty">Henüz yeterli kayıt yok</div>`;
      return `<div class="dr-hm-w" id="dr-hm-w"><canvas id="dr-hm" class="dr-hm"></canvas></div><div class="dr-hm-l"><span><i style="background:#22c55e"></i>${x.kind === "işlem" ? "aktif alış" : "alışta bekleyen"}</span><span><i style="background:#ef4444"></i>${x.kind === "işlem" ? "aktif satış" : "satışta bekleyen"}</span><span><i style="background:#eab308"></i>son fiyat</span><span class="muted">${esc(x.bucket || "")} dilim · en koyu ${drL(x.max)} lot</span></div>${drNote(x.label)}`;
    },
    12(x) {
      if (x.note && !(x.sup || []).length && !(x.res || []).length) return drLive(x);
      const L = (A, c) => (A || []).length ? A.map((z) => `<div class="dr-li"><b class="${c}">${fP(z.p)}</b>${isNum(z.sec) ? `<span>${drDur(z.sec)} tuttu</span>${z.held ? `<span class="pos">hâlâ duruyor</span>` : z.broke ? `<span class="muted">kırıldı</span>` : ""}` : `<span>${fN(z.n)} kez döndü</span>`}</div>`).join("") : `<div class="empty sm">—</div>`;
      return `<div class="dr-2c"><div><div class="dr-st pos">DESTEK</div>${L(x.sup, "pos")}</div><div><div class="dr-st neg">DİRENÇ</div>${L(x.res, "neg")}</div></div>${drNote(x.label)}`;
    },
    13(x) {
      if (x.kind === "derinlik") {
        const S = (k, lb) => { const v = x[k] || {}; const fp = isNum(v.fill_pct) ? v.fill_pct : null;
          return `<div class="dr-bal"><span class="dr-bk">${lb}</span><div class="press-bar thin dr-fc"><span style="width:${fp == null ? 0 : fp.toFixed(1)}%"></span></div><span class="dr-bv">işlem <b class="pos">${drTL(v.fill)}</b> · iptal <b class="warn">${drTL(v.canc)}</b></span><span class="dr-bt muted">gerçek %${fp == null ? "—" : nf(0).format(fp)} · duvar toplamı ${drTL(v.peak)}</span></div>`; };
        const G = x.gone || {};
        return S("b", "ALIŞ DUVARI") + S("a", "SATIŞ DUVARI") + (Object.keys(G).length ? `<div class="dr-chs">${Object.entries(G).map(([k, v]) => `<span class="dr-cmp">${esc(k)}: ${fN(v)}</span>`).join("")}</div>` : "") + drNote(x.label);
      }
      if (x.note && !(x.rows || []).length) return drLive(x);
      const R = x.rows || [];
      return `${R.length ? `<table class="dr-t"><thead><tr><th>TARAF</th><th>FİYAT</th><th>DUVAR</th><th>VURULAN</th><th>KAT</th></tr></thead><tbody>${R.map((r) => `<tr><td>${drSide(r.side)}</td><td>${fP(r.p)}</td><td>${drL(r.lot)}</td><td>${drL(r.traded)}</td><td class="${r.x >= 1 ? "pos" : "warn"}">${drX(r.x)}</td></tr>`).join("")}</tbody></table>` : `<div class="empty sm">Defterde belirgin duvar yok</div>`}${drNote(x.label)}`;
    },
    14(x) {
      const S = x.series || [];
      if (!S.length) return x.note ? drLive(x) : `<div class="empty">Henüz veri yok</div>`;
      return drImb(S, x.kind) + drNote(x.label);
    },
    17(x, d) {
      const L = x.list || [];
      const K = ["dr_duvar", "dr_buyuk", "dr_denge"].filter((k) => NT[k]);
      return `${L.length ? L.map((e) => `<div class="dr-li"><span class="muted">${esc(e.time || "")}</span><b>${esc(e.title || "")}</b><span class="muted">${esc(e.text || "")}</span></div>`).join("") : `<div class="empty sm">Bu hisse için bugün derinlik alarmı yok</div>`}
        ${x.note ? `<div class="dr-live">⏳ ${esc(x.note)}</div>` : ""}
        <div class="dr-nts">${K.map((k) => ntRow(k, true) + `<div class="km-ostest"><button type="button" class="btn-ghost sm" data-ostest="${esc(OS_FEAT[k] || NT[k].l)}">✈️ Telegram Test · ${esc(NT[k].l)}</button></div>`).join("")}</div>
        <div class="src-note">Sunucu tüm hisselerde izler (ciro ≥5 Mn ₺, hafta içi 10:05–18:00). Tekrar engeli: aynı hisse+tür için 30 dk'da 1; toplam saatte en fazla 40. <button type="button" class="btn-ghost sm" data-nflink="ayar">🔔 Tüm bildirim ayarları</button></div>`;
    },
  };

  function drSpark(S) {
    if (!S || S.length < 2) return "";
    const W = 600, H = 60, t0 = S[0][0], t1 = S[S.length - 1][0] || t0 + 1, mx = Math.max(1, ...S.map((p) => p[1]));
    const pts = S.map((p) => `${(((p[0] - t0) / Math.max(1, t1 - t0)) * W).toFixed(1)},${(H - 4 - (p[1] / mx) * (H - 8)).toFixed(1)}`).join(" ");
    return `<svg class="dr-spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><polyline points="${pts}" fill="none" stroke="#eab308" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>`;
  }
  function drImb(S0, kind) {
    let S = S0;
    const W = 600, H = 160, T0 = 36000, T1 = 64800;
    const X = (t) => (((Math.min(T1, Math.max(T0, t)) - T0) / (T1 - T0)) * W).toFixed(1);
    const Y = (r) => { const v = Math.max(-3, Math.min(3, Math.log2(Math.max(0.125, Math.min(8, isNum(r) && r > 0 ? r : 0.125))))); return (H / 2 - (v / 3) * (H / 2 - 6)).toFixed(1); };
    const col = kind === "işlem" ? 1 : 2;   // derinlik: [t, r5, r10, r25] → 10 kademe ana çizgi
    if (kind === "işlem") {   // dakikalık işlem oranı çok oynak → log ölçekte 5 dk kayan ortalama
      const lg = S.filter((p) => isNum(p[1])).map((p) => [p[0], Math.max(-3, Math.min(3, Math.log2(Math.max(0.125, Math.min(8, p[1] > 0 ? p[1] : 0.125)))))]);
      S = lg.map((p, i) => { let sm = 0, c = 0; for (let j = i; j >= 0 && p[0] - lg[j][0] < 300; j--) { sm += lg[j][1]; c++; } return [p[0], Math.pow(2, sm / c)]; });
    }
    const pts = S.filter((p) => isNum(p[col])).map((p) => `${X(p[0])},${Y(p[col])}`);
    if (!pts.length) return `<div class="empty">Henüz veri yok</div>`;
    const area = `M${pts[0].split(",")[0]},${H / 2} L${pts.join(" L")} L${pts[pts.length - 1].split(",")[0]},${H / 2} Z`;
    const p2 = kind !== "işlem" ? S.filter((p) => isNum(p[1])).map((p) => `${X(p[0])},${Y(p[1])}`).join(" ") : "";
    const grid = [10, 12, 14, 16, 18].map((h) => `<line x1="${X(h * 3600)}" y1="0" x2="${X(h * 3600)}" y2="${H}" stroke="#1f2328" stroke-width="1" vector-effect="non-scaling-stroke"/>`).join("");
    return `<div class="dr-imb"><svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><defs><clipPath id="drc-up"><rect x="0" y="0" width="${W}" height="${H / 2}"/></clipPath><clipPath id="drc-dn"><rect x="0" y="${H / 2}" width="${W}" height="${H / 2}"/></clipPath></defs>${grid}
      <path d="${area}" fill="rgba(34,197,94,.30)" clip-path="url(#drc-up)"/><path d="${area}" fill="rgba(239,68,68,.30)" clip-path="url(#drc-dn)"/>
      <line x1="0" y1="${H / 2}" x2="${W}" y2="${H / 2}" stroke="#5d636b" stroke-width="1" stroke-dasharray="4 4" vector-effect="non-scaling-stroke"/>
      ${p2 ? `<polyline points="${p2}" fill="none" stroke="#8b929b" stroke-width="1" vector-effect="non-scaling-stroke" opacity=".7"/>` : ""}
      <polyline points="${pts.join(" ")}" fill="none" stroke="#3b82f6" stroke-width="1.6" vector-effect="non-scaling-stroke"/></svg>
      <span class="dr-ya" style="top:0">8×</span><span class="dr-ya" style="top:calc(50% - 7px)">1×</span><span class="dr-ya" style="bottom:0">⅛×</span></div>
      <div class="dr-xa"><span>10:00</span><span>12:00</span><span>14:00</span><span>16:00</span><span>18:00</span></div>
      <div class="dr-hm-l"><span><i style="background:#3b82f6"></i>${kind === "işlem" ? "aktif alış ÷ aktif satış lot (dakikalık, 5 dk kayan ort.)" : "10 kademe alış ÷ satış (dakika)"}</span>${p2 ? `<span><i style="background:#8b929b"></i>5 kademe</span>` : ""}<span class="muted">üst yarı alış ağırlıklı · log ölçek</span></div>`;
  }
  function drHeat(x, d) {
    const cv = $("dr-hm"), wr = $("dr-hm-w"); if (!cv || !wr || x.empty) return;
    const P = (x.p || []).slice().sort((a, b) => b - a), T = x.t || [];
    const w = Math.max(200, wr.clientWidth || 360);
    const sig = [w, P.length, T.length, (x.cells || []).length, x.max, d.last, DR.d && DR.d.ts].join("|");
    if (cv._sig === sig) return; cv._sig = sig;
    const rh = Math.max(5, Math.min(13, Math.floor(420 / Math.max(1, P.length)))), LW = 46, BH = 16;
    const h = P.length * rh + BH, dpr = window.devicePixelRatio || 1;
    cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); cv.style.width = w + "px"; cv.style.height = h + "px";
    const c = cv.getContext("2d"); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, w, h);
    const cw = (w - LW) / Math.max(1, T.length), pi = new Map(P.map((p, i) => [p.toFixed(4), i])), mx = Math.max(1, x.max || 1);
    for (const [ci, p, vb, va] of x.cells || []) {
      const i = pi.get((+p).toFixed(4)); if (i == null) continue;
      const v = Math.max(vb, va); if (v <= 0) continue;
      const a = 0.12 + 0.88 * Math.sqrt(v / mx);
      c.fillStyle = vb >= va ? `rgba(34,197,94,${a.toFixed(3)})` : `rgba(239,68,68,${a.toFixed(3)})`;
      c.fillRect(LW + ci * cw, i * rh, Math.max(1, cw - 0.5), Math.max(1, rh - 0.5));
    }
    c.font = "9px Inter, system-ui, sans-serif"; c.fillStyle = "#8b929b"; c.textBaseline = "middle";
    const step = Math.max(1, Math.ceil(11 / rh));
    P.forEach((p, i) => { if (i % step === 0) c.fillText(fP(p), 2, i * rh + rh / 2); });
    const lp = d.last;
    if (isNum(lp)) { let bi = -1, bd = Infinity; P.forEach((p, i) => { const dd = Math.abs(p - lp); if (dd < bd) { bd = dd; bi = i; } }); if (bi >= 0) { c.strokeStyle = "#eab308"; c.lineWidth = 1.2; c.strokeRect(LW, bi * rh, w - LW - 1, rh); } }
    c.textBaseline = "alphabetic"; c.fillStyle = "#8b929b";
    const ts = Math.max(1, Math.ceil(T.length / Math.max(1, Math.floor((w - LW) / 44))));
    T.forEach((t, i) => { if (i % ts === 0) c.fillText(t, LW + i * cw, h - 4); });
  }

  // ---- merdiven etiketleri (madde 15 POC/VWAP/maliyet · 9 kurumsal 🏛 · 2 duvar 🧱)
  function drLadderTags(bids, asks) {
    const out = { b: [], a: [] };
    if (!DR || !DR.d || !DR.d.r || DR.sym !== st.sym) return out;
    const R = DR.d.r, M = { b: [], a: [] }, add = (s, i, t, mk) => { (out[s][i] = out[s][i] || []).push(t); if (mk) (M[s][i] = M[s][i] || []).push(mk); };   // v1.26.0 M: dokunmatik ayrıntı
    out.m = M; DR.mk = out;
    const L = [];
    bids.forEach((r, i) => { if (isNum(r.price) && r.price > 0) L.push(["b", i, r.price]); });
    asks.forEach((r, i) => { if (isNum(r.price) && r.price > 0) L.push(["a", i, r.price]); });
    if (drOn(15) && R["15"] && L.length) {
      for (const m of R["15"].list || []) {
        if (!isNum(m.p)) continue;
        let best = null, bd = Infinity; for (const z of L) { const dd = Math.abs(z[2] - m.p); if (dd < bd) { bd = dd; best = z; } }
        if (best && bd <= tickOf(m.p) * 1.01 + 1e-9) add(best[0], best[1], m.k === "POC" ? `<i class="dr-tg poc">POC</i>` : m.k === "VWAP" ? `<i class="dr-tg vwap">VWAP</i>` : m.k === "MALİYET" ? `<i class="dr-tg mal" title="${esc(m.br || "")} maliyeti ${fP(m.p)}">${esc(String(m.br || "M").replace(/\s+/g, "").slice(0, 4))}</i>` : `<i class="dr-tg aort">AORT</i>`,
          { k: m.k === "POC" ? "poc" : m.k === "VWAP" ? "vwap" : m.k === "MALİYET" ? "mal" : "aort", m });
      }
    }
    const same = (a, b) => Math.abs(a - b) < 1e-6;
    if (drOn(9) && R["9"]) for (const r of R["9"].inst || []) { const A = r.side === "b" ? bids : asks; const i = A.findIndex((z) => same(z.price, r.p)); if (i >= 0) add(r.side, i, `<i class="dr-tg inst" title="az emirle büyük lot">🏛</i>`, { k: "inst", m: r }); }
    if (drOn(2) && R["2"]) for (const s of ["b", "a"]) for (const w of R["2"][s] || []) { const A = s === "b" ? bids : asks; const i = A.findIndex((z) => same(z.price, w.p)); if (i >= 0) add(s, i, `<i class="dr-tg wall" title="duvar">🧱</i>`, { k: "wall", m: w }); }
    return out;
  }

  // ---- AYARLAR → DERİNLİK ANALİZLERİ
  function drSetCard() {
    if (!DR || !DRI) return "";
    const n = drItems().length;
    const row = (x) => `<label class="dr-row"><span class="dr-rl"><b>${esc(x[3])}</b><small>${esc(x[4])}</small></span><span class="nf-sw"><input type="checkbox" data-dron="${x[0]}" ${drOn(x[0]) ? "checked" : ""}/><span></span></span></label>`;
    const anl = DRI.filter((x) => x[1] === "a").sort((p, q) => p[0] - q[0]);
    const gen = DRI.filter((x) => x[1] !== "a").sort((p, q) => p[0] - q[0]);
    return `<section class="card dr-set" id="dr-set"><div class="card-h"><span class="card-title">DERİNLİK ANALİZLERİ</span><span class="muted" id="dr-set-n">${n}/${DRI.length} açık</span></div>
      <div class="nf-gset"><button type="button" class="nf-gb notify" data-drall="1">Tümünü aç</button><button type="button" class="nf-gb off" data-drall="0">Tümünü kapat</button><button type="button" class="btn-ghost sm" data-nflink="dr">Derinlik →</button></div>
      <div class="dr-st">ANLIK</div>${anl.map(row).join("")}<div class="dr-st">GENEL</div>${gen.map(row).join("")}
      <div class="src-note">Hisse sayfası → DERİNLİK sekmesindeki kartlar. Kapalı kartlar hesaplanmaz ve sunucudan istenmez. Seçimler bu cihazda saklanır, anında uygulanır.</div></section>`;
  }
  function drSetSync() {
    if (!DR) return;
    document.querySelectorAll("[data-dron]").forEach((i) => { i.checked = drOn(+i.dataset.dron); });
    const c = $("dr-set-n"); if (c) c.textContent = `${drItems().length}/${DRI.length} açık`;
  }
  document.addEventListener("change", (e) => {
    const i = e.target.closest && e.target.closest("[data-dron]"); if (!i) return;
    DR.on[+i.dataset.dron] = i.checked; LS.set("drOn", DR.on); drSetSync(); drApply();
  });
  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-drall]");
    if (a) { const v = a.dataset.drall === "1"; DRI.forEach(([n]) => { DR.on[n] = v; }); LS.set("drOn", DR.on); drSetSync(); drApply(); toast(v ? "Tüm derinlik analizleri açıldı" : "Tüm derinlik analizleri kapatıldı", 1500); return; }
    const s = e.target.closest("[data-drset]");
    if (s) { e.preventDefault(); drSettings(); }
  });
  function drSettings() {
    nfOpen("ayar");
    setTimeout(() => { const s = $("dr-set"); if (s) { sgNav(); window.scrollTo(0, Math.max(0, s.getBoundingClientRect().top + window.scrollY - 70)); SG.y = window.scrollY; } }, 150);
  }
  function drGo() { if (st.view !== "stock") go("stock"); openTab("derinlik", true); }

  // ===================================================================== v1.26.0 ==
  // ---- (1) MERDİVEN İŞARETLERİ dokunmatik açıklama (alt sayfa / popover) + "İşaretler ne demek?" lejantı
  // ---- (2) SEANS İŞLEM AKIŞI ANALİZİ (DERİNLİK kartı + Özet özeti) · /api/stocks/{sym}/akis
  // ---- (3) AKD sekmesi K/Z sütunları + KURUM KÂR/ZARAR + AKD ANALİZİ · /api/stocks/{sym}/akd-plus
  // ---- (4) KEŞFET › AKD TARAMASI (tüm hisseler) · /api/akd/tarama (+ akd_tarama bildirim kuralları)
  // Not: bu blok betiğin sonunda çalışır; ilk selectSymbol/openTab bundan ÖNCE çağrılır → tüm giriş fonksiyonları
  // V126_READY bayrağıyla korunur, durumlar "var" (TDZ yok); blok sonunda mevcut ekran için bir kez tetiklenir.
  var V126_READY, FL, AKP, AT, MKS;
  function v6ok() { return V126_READY === true; }
  function v6pc(v, d) { return isNum(v) ? (v > 0 ? "+" : v < 0 ? "−" : "") + "%" + nf(d == null ? 2 : d).format(Math.abs(v)) : "—"; }
  function v6tl(v) { return isNum(v) ? (v < 0 ? "−" : "") + fShort(Math.abs(v)) + " ₺" : "—"; }
  function v6stl(v) { return isNum(v) ? (v > 0 ? "+" : v < 0 ? "−" : "") + fShort(Math.abs(v)) + " ₺" : "—"; }
  function v6kv(k, v, c) { return `<div class="ozp-kv"><small>${esc(k)}</small><b class="${c || ""}">${v}</b></div>`; }
  function v6bar(p, lb, ls) { const w = isNum(p) ? Math.max(2, Math.min(98, p)) : 50; return `<div class="fl-bar"><span class="pos">${esc(lb || "")} ${isNum(p) ? "%" + nf(1).format(p) : "%—"}</span><div class="press-bar thin"><span style="width:${w.toFixed(1)}%"></span></div><span class="neg">${isNum(p) ? "%" + nf(1).format(100 - p) : "%—"} ${esc(ls || "")}</span></div>`; }

  // ================================================================ (1) İŞARETLER
  function mkDef() {
    return {
      poc: ["POC", "POC — En çok işlem gören fiyat", "Point of Control: bugün EN ÇOK LOTUN el değiştirdiği fiyat. Piyasanın günün \"adil fiyatı\" kabul ettiği yerdir. Fiyat POC'un üstündeyse POC çoğu zaman destek, altındaysa direnç gibi çalışır."],
      vwap: ["VWAP", "VWAP — Hacim ağırlıklı ortalama fiyat", "Bugün işlem gören tüm lotların ortalama fiyatı (günün ortalama maliyeti). Fiyat VWAP'ın üstündeyse günün alıcıları ortalamada kârda (güçlü görünüm), altındaysa zararda (zayıf görünüm)."],
      aort: ["AORT", "AORT — Aktif alış ortalaması", "Bugün piyasa emriyle (satıcının fiyatına giderek) ALAN agresif alıcıların ortalama fiyatı. Fiyat bunun üstündeyse agresif alıcılar kârda; bu seviye sık sık destek olur, altına inilirse agresif alıcılar zarara geçer."],
      mal: ["IsYa", "Kurum maliyeti (kurum etiketi)", "Etiket, kurum adının ilk harfleridir (örn. IsYa = İş Yatırım). Bu kurum bugün maliyetini yükselterek ısrarla alıyor (Maliyet Yükselten Kurumlar); bugünkü ortalama alış maliyeti bu fiyatta. Kurumlar maliyetlerini çoğu zaman savunur → olası destek seviyesi."],
      inst: ["🏛", "🏛 Kurumsal emir — az emirle büyük lot", "Bu kademede AZ SAYIDA emirle ÇOK BÜYÜK lot bekliyor: emir başına ortalama lot, defterin genel emir ortalamasının birkaç katı. Genelde tek bir büyük oyuncunun / kurumun emridir, küçük yatırımcı emri değildir."],
      wall: ["🧱", "🧱 Duvar — kalın kademe", "Defterdeki en kalın kademelerden biri (ilk 25 kademenin ortalama lotunun katları). Alış tarafındaysa DESTEK, satış tarafındaysa DİRENÇ görevi görür. Lot azalıyorsa (eriyor) kırılabilir; büyüyorsa savunuluyor demektir. Balinalar bazen kalın satış duvarını tek seferde süpürüp fiyatı yukarı iter."],
      lvl: ["", "Kademe", "Derinlik merdiveninde bir fiyat kademesi: o fiyatta bekleyen toplam lot ve emir sayısı."],
    };
  }
  function mkLegend() {
    const el = $("mk-leg"); if (!el) return;
    const D = mkDef();
    const chip = (k, cl) => `<button type="button" class="mk-lc" data-mkleg="${k}"><i class="dr-tg ${cl}">${esc(D[k][0])}</i><span>${esc(D[k][1].split(" — ")[1] || D[k][1])}</span></button>`;
    setH(el, `<div class="mk-lh"><b>ⓘ İşaretler ne demek?</b><small>Merdivendeki fiyat hücresine / işarete dokunun → o kademenin ayrıntısı</small></div>
      <div class="mk-lr">${chip("poc", "poc")}${chip("vwap", "vwap")}${chip("aort", "aort")}${chip("mal", "mal")}${chip("inst", "inst")}${chip("wall", "wall")}</div>`);
  }
  function mkOv() {
    let o = $("mk-ov");
    if (!o) {
      o = document.createElement("div"); o.id = "mk-ov"; o.className = "mk-ov"; o.hidden = true;
      o.innerHTML = `<div class="mk-box" role="dialog" aria-modal="true"><div class="mk-h"><b id="mk-t">—</b><button type="button" class="mk-x" data-mkx="1" aria-label="Kapat">✕</button></div><div class="mk-b" id="mk-b"></div></div>`;
      document.body.appendChild(o);
    }
    return o;
  }
  function mkClose() { const o = $("mk-ov"); if (o) o.hidden = true; }
  function mkOpen(title, html) { const o = mkOv(); $("mk-t").textContent = title; $("mk-b").innerHTML = html; o.hidden = false; const b = $("mk-b"); if (b) b.scrollTop = 0; }
  function mkMeaning(k) { const D = mkDef()[k] || mkDef().lvl; return `<div class="mk-m"><div class="mk-mt">${esc(D[1])}</div><p>${esc(D[2])}</p></div>`; }
  function mkRefs(last) {
    const L = (DR && DR.d && DR.d.r && DR.d.r["15"] && DR.d.r["15"].list) || [];
    const ref = L.filter((m) => m.k !== "MALİYET");
    if (!ref.length) return "";
    return `<div class="mk-sub">Günün referans fiyatları</div><div class="ozp-kvs">${ref.map((m) => v6kv(m.k === "AKT. ALIŞ ORT." ? "AORT (akt. alış ort.)" : m.k, kmP(m.p) + (isNum(last) && last ? ` <small class="${cls(last - m.p)}">son ${v6pc((last / m.p - 1) * 100)}</small>` : ""))).join("")}${isNum(last) ? v6kv("Son fiyat", kmP(last)) : ""}</div>`;
  }
  function mkLevel(side, i, ti) {
    const d = st.ideal, dp = d && d.depth; if (!dp) return;
    const N = st.depthN, A = ((side === "b" ? dp.bids : dp.asks) || []).slice(0, N), r = A[i];
    if (!r || !isNum(r.price)) return;
    const q = (d.quote || {}), last = q.price;
    const tags = ((DR && DR.mk && DR.mk.m && DR.mk.m[side] && DR.mk.m[side][i]) || []).slice();
    if (isNum(ti) && ti > 0 && ti < tags.length) tags.unshift(tags.splice(ti, 1)[0]);   // dokunulan işaret en üstte
    const R = (DR && DR.d && DR.d.r && DR.sym === st.sym) ? DR.d.r : {};
    const same = (a, b) => Math.abs(a - b) < 1e-6;
    const avgOrd = r.orders ? r.lot / r.orders : null;
    const sideL = side === "b" ? "ALIŞ" : "SATIŞ";
    const tot = A.reduce((s, z) => s + (z.lot || 0), 0), avgLot = A.length ? tot / A.length : null;
    let h = `<div class="mk-lvl"><span class="mk-sd ${side === "b" ? "pos" : "neg"}">${sideL} · ${i + 1}. kademe</span><b>${fP(r.price)} ₺</b></div>
      <div class="ozp-kvs">${v6kv("Lot", fN(r.lot))}${v6kv("Emir sayısı", fN(r.orders))}${v6kv("Emir başına ort. lot", isNum(avgOrd) ? fN(avgOrd) : "—")}${v6kv("Tutar", v6tl(r.lot * r.price))}${v6kv("Son fiyata uzaklık", isNum(last) && last ? v6pc((r.price / last - 1) * 100) : "—")}${v6kv("25 kademe ort. lotunun", isNum(avgLot) && avgLot ? nf(1).format(r.lot / avgLot) + "×" : "—")}</div>`;
    if (!tags.length) h += `<div class="src-note">Bu kademede işaret yok.</div>` + mkMeaning("lvl");
    let first = true;
    for (const t of tags) {
      h += `<div class="mk-sec">`;
      if (t.k === "wall") {
        const w = ((R["2"] || {})[side] || []).find((z) => same(z.p, r.price)) || {};
        const tr = w.trend ? String(w.trend) : null;
        h += mkMeaning("wall") + `<div class="ozp-kvs">${v6kv("Duvar lotu", fN(w.lot ?? r.lot))}${v6kv("Emir", fN(w.ord ?? r.orders))}${v6kv("Tutar", v6tl(w.tl ?? r.lot * r.price))}${v6kv("Ortalamanın katı", isNum(w.x) ? nf(1).format(w.x) + "×" : "—")}
          ${v6kv("Ne zamandır", isNum(w.dur) ? drDur(w.dur) + (w.first ? ` <small>(${esc(w.first)}'den beri)</small>` : "") : "canlı seansla")}${v6kv("Büyüyor / eriyor", tr ? esc(tr) + (isNum(w.trend_ch) ? ` <small>${v6pc(w.trend_ch, 0)}</small>` : "") : "canlı seansla", /BÜY/.test(tr || "") ? "pos" : /ERİ/.test(tr || "") ? "neg" : "")}
          ${v6kv("Gün tepe lot", fN(w.peak))}${v6kv("İşlemle dolan", isNum(w.fill) ? fN(w.fill) : "—")}${v6kv("İptal edilen", isNum(w.canc) ? fN(w.canc) : "—")}</div>${(R["2"] || {}).note && !isNum(w.dur) ? `<div class="src-note">${esc(R["2"].note)}</div>` : ""}`;
      } else if (t.k === "inst") {
        const x = ((R["9"] || {}).inst || []).find((z) => z.side === side && same(z.p, r.price)) || {};
        const sa = side === "b" ? (R["9"] || {}).avg_b : (R["9"] || {}).avg_a;
        h += mkMeaning("inst") + `<div class="ozp-kvs">${v6kv("Lot", fN(x.lot ?? r.lot))}${v6kv("Emir sayısı", fN(x.ord ?? r.orders))}${v6kv("Emir başına ort. lot", fN(x.avg ?? avgOrd))}${v6kv(sideL + " tarafı ort. emir", isNum(sa) ? fN(sa) + " lot" : "—")}${v6kv("Katı", isNum(x.x) ? nf(1).format(x.x) + "×" : "—", "pos")}${v6kv("Tutar", v6tl(x.tl ?? r.lot * r.price))}</div>`;
      } else if (t.k === "mal") {
        const m = t.m || {};
        let akd = "";
        const A2 = st.akd && st.akd.symbol === st.sym ? [...(st.akd.buyers || []), ...(st.akd.sellers || [])].find((z) => z.broker === m.br) : null;
        if (A2) akd = `<div class="mk-sub">AKD (${esc(st.akd.label || "günlük")})</div><div class="ozp-kvs">${v6kv("Net lot", fN(A2.net_lot), cls(A2.net_lot))}${v6kv("AKD maliyeti", kmP(A2.cost))}${v6kv("K/Z", v6stl(A2.pnl_tl), cls(A2.pnl_tl))}${v6kv("K/Z %", v6pc(A2.pnl_pct), cls(A2.pnl_pct))}</div>`;
        h += mkMeaning("mal") + `<div class="ozp-kvs">${v6kv("Kurum", esc(brName(m.br || "—")))}${v6kv("Güncel maliyet", kmP(m.p))}${v6kv("Israr skoru", isNum(m.israr) ? fN(m.israr) + (m.israr >= 70 ? " · ISRARCI" : "") : "—", (m.israr || 0) >= 70 ? "pos" : "")}${v6kv("Ciddiyet skoru", isNum(m.sc) ? fN(m.sc) : "—")}${v6kv("Fiyat – maliyet", isNum(last) && m.p ? v6pc((last / m.p - 1) * 100) : "—", isNum(last) && m.p ? cls(last - m.p) : "")}</div>${akd}
          <button type="button" class="btn-ghost sm" data-mkkm="${esc(m.br || "")}">Kurum ayak izi →</button>`;
      } else {
        const k = t.k, m = t.m || {};
        h += mkMeaning(k) + `<div class="ozp-kvs">${v6kv(k === "aort" ? "Aktif alış ort." : k.toUpperCase(), kmP(m.p))}${v6kv("Bu kademe", fP(r.price))}${v6kv("Son fiyata göre", isNum(last) && m.p ? v6pc((last / m.p - 1) * 100) : "—", isNum(last) && m.p ? cls(last - m.p) : "")}</div>`;
      }
      h += `</div>`;
      first = false;
    }
    h += mkRefs(last);
    h += `<div class="src-note">Kaynak: İdealData derinlik + v1.25 derinlik analizleri (${esc((DR && DR.d && DR.d.src) || "—")}). İşaretler ⚙ Derinlik Analizleri → Merdiven işaretleri / Duvar takibi / Emir sayısı ile açılıp kapanır.</div>`;
    const ttl = tags.length ? tags.map((t) => t.k === "mal" ? brName((t.m || {}).br || "") : (mkDef()[t.k] || [""])[0]).join(" · ") + " · " + fP(r.price) : `${sideL} ${fP(r.price)}`;
    mkOpen(ttl, h);
  }
  document.addEventListener("click", (e) => {
    if (!v6ok()) return;
    const x = e.target.closest("[data-mkx]"); if (x || e.target.id === "mk-ov") { mkClose(); return; }
    const lg = e.target.closest("[data-mkleg]"); if (lg) { const k = lg.dataset.mkleg; mkOpen(mkDef()[k][1], mkMeaning(k) + mkRefs((st.ideal && st.ideal.quote || {}).price)); return; }
    const km = e.target.closest("[data-mkkm]"); if (km) { mkClose(); try { kmOpen(st.sym, km.dataset.mkkm); } catch (er) { opOpen("k_maliyet"); } return; }
    const td = e.target.closest("#depth-body td.b-px, #depth-body td.a-px"); if (!td || !td.textContent.trim()) return;
    const tr = td.parentElement, i = Array.prototype.indexOf.call(tr.parentElement.children, tr);
    const tg = e.target.closest(".dr-tg"), ti = tg && tg.parentElement ? Array.prototype.indexOf.call(tg.parentElement.children, tg) : -1;
    mkLevel(td.classList.contains("b-px") ? "b" : "a", i, ti);
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") mkClose(); });

  // ================================================================ (2) İŞLEM AKIŞI
  function flS() { return FL || (FL = { d: null, sym: null, gen: -1, busy: false, last: 0, win: LS.get("flWin", "15"), more: false }); }
  async function flLoad(force) {
    if (!v6ok()) return;
    const S = flS();
    if (st.view !== "stock" || (st.tab !== "derinlik" && st.tab !== "ozet") || document.hidden) return;
    if (S.gen !== st.gen || S.sym !== st.sym) { S.d = null; S.gen = st.gen; S.sym = st.sym; S.last = 0; flRender(); }
    const iv = S.d && S.d.live ? 15000 : 120000;
    if (!force && Date.now() - S.last < iv) return;
    if (S.busy) return;
    S.busy = true; S.last = Date.now();
    const gen = st.gen, sym = st.sym;
    try {
      const d = await api(`/api/stocks/${sym}/akis`, { timeout: 30000 });
      if (gen !== st.gen || sym !== st.sym) return;
      S.d = d; flRender();
    } catch (e) {
      if (!S.d) { const m = `<div class="empty">İşlem akışı alınamadı (${esc(e.message || e)}) — ↻ ile yeniden deneyin</div>`; setH($("fl-body"), m); setH($("ozp-flow"), ""); }
    } finally { S.busy = false; }
  }
  setInterval(() => { try { flLoad(false); } catch (e) {} }, 2000);
  function flRender() {
    const S = flS(), w = $("fl-wrap");
    if (w && !$("fl-body")) w.innerHTML = `<section class="card fl-card" id="fl-card"><div class="card-h"><span class="card-title">SEANS İŞLEM AKIŞI ANALİZİ</span><span class="dr-bdg" id="fl-bdg"></span></div><div id="fl-body"><div class="empty">Yükleniyor…</div></div></section>`;
    const d = S.d;
    const body = $("fl-body"), oz = $("ozp-flow");
    if (!d) { setH(body, `<div class="empty">Yükleniyor…</div>`); if (oz) setH(oz, ""); return; }
    const bd = $("fl-bdg"); if (bd) { const t = `<i class="dr-b ${d.live ? "ok" : "snap"}">${d.live ? "CANLI" : esc(d.day_label || "")}</i>`; if (bd._h !== t) { bd.innerHTML = t; bd._h = t; } }
    if (d.empty || d.error || !d.tot) { setH(body, `<div class="empty">${esc(d.yorum || d.error || "İşlem kaydı yok")}</div>`); if (oz) setH(oz, ""); return; }
    try { setH(body, flHtml(d, S)); } catch (e) { setH(body, `<div class="empty">Gösterilemedi: ${esc(e.message || e)}</div>`); }
    try { if (oz) setH(oz, flOzet(d)); } catch (e) { if (oz) setH(oz, ""); }
  }
  function flHtml(d, S) {
    const t = d.tot, sb = d.size_big || {}, sw = d.sweep_sum || {}, ws = d.wall_sum || {}, ef = d.effect || {}, th = d.thr || {};
    let h = `<div class="fl-y"><b>YORUM</b> ${esc(d.yorum || "—")}</div>`;
    h += `<div class="mk-sub">GÜN TOPLAMI · aktif alış / aktif satış</div>${v6bar(t.b_pct, "Aktif alış", "Aktif satış")}
      <div class="ozp-kvs">${v6kv("Aktif alış", `${fShort(t.b_lot)} lot · ${v6tl(t.b_tl)}`, "pos")}${v6kv("Aktif satış", `${fShort(t.s_lot)} lot · ${v6tl(t.s_tl)}`, "neg")}${v6kv("Net aktif", v6stl(t.net_tl), cls(t.net_tl))}${v6kv("İşlem adedi (A/S)", `${fN(t.nb)} / ${fN(t.ns)}`)}${v6kv("Tek fiyat (açılış/kapanış)", v6tl(t.a_tl))}${v6kv("Sürekli işlem değişimi", `${kmP(t.p_open)} → ${kmP(t.p_last)} · ${v6pc(t.chg)}`, cls(t.chg))}</div>`;
    // pencereler
    const W = (d.win || {})[S.win] || [];
    h += `<div class="mk-sub fl-sh"><span>ZAMAN PENCERELERİ</span><span class="seg sm fl-ws">${["15", "30", "60"].map((x) => `<button type="button" data-flw="${x}" class="${S.win === x ? "active" : ""}">${x} dk</button>`).join("")}</span></span></div>
      <div class="tbl-scroll fl-ts"><table class="grid-table fl-t"><thead><tr><th class="l">SAAT</th><th>AKTİF ALIŞ</th><th>AKTİF SATIŞ</th><th class="l">ALIŞ %</th><th>FİYAT Δ</th></tr></thead><tbody>${W.slice().reverse().map((r) => `<tr><td class="l">${esc(r.t)}</td><td class="pos">${fShort(r.b)}</td><td class="neg">${fShort(r.s)}</td><td class="l"><span class="fl-mb"><i style="width:${isNum(r.bp) ? r.bp.toFixed(0) : 50}%"></i></span> ${isNum(r.bp) ? "%" + nf(0).format(r.bp) : "—"}</td><td class="${cls(r.chg)}">${v6pc(r.chg)}</td></tr>`).join("") || `<tr><td colspan="5" class="empty">Pencere yok</td></tr>`}</tbody></table></div>`;
    // büyüklük
    h += `<div class="mk-sub">EMİR BÜYÜKLÜĞÜ · agresif emir = aynı saniyede aynı kurumun ardışık baskıları</div>
      <div class="tbl-scroll"><table class="grid-table fl-t"><thead><tr><th class="l">SINIF (₺)</th><th>ALIŞ ADET</th><th>ALIŞ ₺</th><th>SATIŞ ADET</th><th>SATIŞ ₺</th><th>ALIŞ %</th></tr></thead><tbody>${(d.size || []).map((r) => `<tr><td class="l"><b>${esc(trUpper(r.k))}</b> <small class="muted">${r.hi ? fShort(r.lo) + "–" + fShort(r.hi) : "≥" + fShort(r.lo)}</small></td><td>${fN(r.nb)}</td><td class="pos">${fShort(r.b)}</td><td>${fN(r.ns)}</td><td class="neg">${fShort(r.s)}</td><td class="${(r.bp ?? 50) >= 55 ? "pos" : (r.bp ?? 50) <= 45 ? "neg" : ""}">${isNum(r.bp) ? "%" + nf(1).format(r.bp) : "—"}</td></tr>`).join("")}</tbody></table></div>
      <div class="ozp-ln">Büyük + balina emirlerde alış payı <b class="${(sb.bp ?? 50) >= 50 ? "pos" : "neg"}">%${isNum(sb.bp) ? nf(1).format(sb.bp) : "—"}</b> · balina: <b class="pos">${fN(sb.nw_b)} alış</b> / <b class="neg">${fN(sb.nw_s)} satış</b> <small class="muted">(eşikler gün cirosuna göre: balina ≥${fShort(th.whale)} ₺, büyük ≥${fShort(th.large)} ₺, orta ≥${fShort(th.med)} ₺)</small></div>`;
    if ((d.whales || []).length) h += `<details class="fl-det"><summary>En büyük ${d.whales.length} agresif emir</summary><div class="tbl-scroll"><table class="grid-table fl-t"><thead><tr><th class="l">SAAT</th><th>YÖN</th><th>TUTAR</th><th>LOT</th><th>FİYAT</th><th class="l">KURUM</th><th>60 SN</th><th>5 DK</th></tr></thead><tbody>${d.whales.map((r) => `<tr><td class="l">${esc(r.t)}</td><td>${drSide(r.side)}</td><td>${fShort(r.tl)}</td><td>${fShort(r.lot)}</td><td>${kmP(r.p0)}${r.p1 !== r.p0 ? "→" + kmP(r.p1) : ""}</td><td class="l">${esc(brName(r.br))}</td><td class="${cls(r.e60)}">${v6pc(r.e60)}</td><td class="${cls(r.e300)}">${v6pc(r.e300)}</td></tr>`).join("")}</tbody></table></div></details>`;
    // süpürmeler
    const sB = sw.b || {}, sA = sw.a || {};
    h += `<div class="mk-sub">SÜPÜRMELER · tek agresif emirde ≥2 fiyat kademesi (≥${fShort(sw.min_tl)} ₺)</div>
      <div class="ozp-kvs">${v6kv("Alış süpürmesi", `${fN(sB.n)} kez · ${fN(sB.lev)} kademe · ${v6tl(sB.tl)}`, "pos")}${v6kv("Etki (anlık / 5 dk)", `${v6pc(sB.e0)} / ${v6pc(sB.e300)}`, cls(sB.e300))}${v6kv("Satış süpürmesi", `${fN(sA.n)} kez · ${fN(sA.lev)} kademe · ${v6tl(sA.tl)}`, "neg")}${v6kv("Etki (anlık / 5 dk)", `${v6pc(sA.e0)} / ${v6pc(sA.e300)}`, cls(sA.e300))}</div>`;
    if ((d.sweeps || []).length) h += `<details class="fl-det"><summary>Son ${d.sweeps.length} süpürme</summary><div class="tbl-scroll"><table class="grid-table fl-t"><thead><tr><th class="l">SAAT</th><th>YÖN</th><th>KADEME</th><th>FİYAT</th><th>TUTAR</th><th>ANLIK</th><th>5 DK</th><th class="l">KURUM</th></tr></thead><tbody>${d.sweeps.map((r) => `<tr><td class="l">${esc(r.t)}</td><td>${drSide(r.side)}</td><td>${fN(r.lev)}</td><td>${kmP(r.p0)}→${kmP(r.p1)}</td><td>${fShort(r.tl)}</td><td class="${cls(r.e0)}">${v6pc(r.e0)}</td><td class="${cls(r.e300)}">${v6pc(r.e300)}</td><td class="l">${esc(brName(r.br))}</td></tr>`).join("")}</tbody></table></div></details>`;
    // duvar süpürme
    h += `<div class="mk-sub">DUVAR SÜPÜRME · kalın satış duvarı aktif alışla tüketilip fiyat üstüne geçti</div>
      <div class="ozp-kvs">${v6kv("Süpürülen duvar", `${fN(ws.n)} kez`, ws.n ? "pos" : "")}${v6kv("Sonrası 5 dk yükselen", `${fN(ws.up)} / ${fN(ws.n)}`)}${v6kv("Süpürülen tutar", v6tl(ws.tl))}${v6kv("Ort. 5 dk etki", v6pc(ws.e300), cls(ws.e300))}</div>
      ${(d.walls || []).length ? `<div class="tbl-scroll"><table class="grid-table fl-t"><thead><tr><th class="l">SAAT</th><th>FİYAT</th><th>LOT</th><th>TUTAR</th><th>SÜRE</th><th>5 DK</th><th>15 DK</th><th>5 DK TEPE</th><th class="l">EN ÇOK ALAN</th></tr></thead><tbody>${d.walls.map((r) => `<tr><td class="l">${esc(r.t0 ? r.t0.slice(0, 5) + "→" : "")}${esc(r.t)}</td><td>${kmP(r.p)}</td><td>${fShort(r.lot)}</td><td>${fShort(r.tl)}</td><td>${isNum(r.dur) ? drDur(r.dur) : "—"}</td><td class="${cls(r.e300)}">${v6pc(r.e300)}</td><td class="${cls(r.e900)}">${v6pc(r.e900)}</td><td class="${cls(r.mx)}">${v6pc(r.mx)}</td><td class="l">${esc(brName(r.br || ""))}</td></tr>`).join("")}</tbody></table></div>` : `<div class="empty">Duvar süpürme yok</div>`}
      <div class="src-note">${esc(ws.label || "")}</div>`;
    // fiyat etkisi
    h += `<div class="mk-sub">FİYAT ETKİSİ · taraf başına (≥${fShort(ef.min_tl)} ₺ agresif emirler)</div>
      <div class="ozp-kvs">${v6kv("Aktif alış sonrası 60 sn", v6pc(ef.b60, 3), cls(ef.b60))}${v6kv("Aktif satış sonrası 60 sn", v6pc(ef.s60, 3), cls(ef.s60))}${v6kv("Aktif alış sonrası 5 dk", v6pc(ef.b300, 3), cls(ef.b300))}${v6kv("Aktif satış sonrası 5 dk", v6pc(ef.s300, 3), cls(ef.s300))}
        ${v6kv("Yükselişin aktif alışlı dakikalardan payı", isNum(ef.up_b) ? "%" + nf(1).format(ef.up_b) : "—", "pos")}${v6kv("Düşüşün aktif satışlı dakikalardan payı", isNum(ef.dn_s) ? "%" + nf(1).format(ef.dn_s) : "—", "neg")}${v6kv("1 Mn ₺ net aktif başına", v6pc(ef.slope, 3), cls(ef.slope))}${v6kv("Emir adedi (A/S)", `${fN(ef.nb)} / ${fN(ef.ns)}`)}</div>
      <div class="src-note">Kaynak: gerçek işlem kaydı (${esc(d.mode || "")} · ${esc(d.day_label || "")}). Aktif alış = alıcının satış fiyatına giderek aldığı işlem, aktif satış = satıcının alış fiyatına giderek sattığı işlem; tek fiyat (açılış/kapanış) ayrı tutulur. "Yükselişin payı" = fiyatın yükseldiği dakikalardan net aktif alışlı olanların yükselişteki payı.</div>`;
    return h;
  }
  function flOzet(d) {
    const t = d.tot, sb = d.size_big || {}, sw = d.sweep_sum || {}, ws = d.wall_sum || {}, ef = d.effect || {};
    return `<div class="card ozp-c fl-oz"><div class="card-h"><span>SEANS İŞLEM AKIŞI</span><span class="muted sm">${d.live ? "canlı" : esc(d.day_label || "")}</span></div>
      <div class="ozp-yt">${esc(d.yorum || "—")}</div>${v6bar(t.b_pct, "Aktif alış", "Aktif satış")}
      <div class="ozp-kvs">${v6kv("Net aktif", v6stl(t.net_tl), cls(t.net_tl))}${v6kv("Büyük/balina alış payı", isNum(sb.bp) ? "%" + nf(1).format(sb.bp) : "—", (sb.bp ?? 50) >= 50 ? "pos" : "neg")}${v6kv("Süpürme A / S", `${fN((sw.b || {}).n)} / ${fN((sw.a || {}).n)}`)}${v6kv("Duvar süpürme", fN(ws.n) + (ws.kind === "işlem" ? " (vekil)" : ""))}${v6kv("Yükselişin aktif alış payı", isNum(ef.up_b) ? "%" + nf(1).format(ef.up_b) : "—")}${v6kv("Gün değişimi", v6pc(t.chg), cls(t.chg))}</div>
      <button type="button" class="ozp-pl" data-flgo="1"><b>Ayrıntı</b> DERİNLİK › SEANS İŞLEM AKIŞI ANALİZİ ›</button></div>`;
  }
  document.addEventListener("click", (e) => {
    if (!v6ok()) return;
    const w = e.target.closest("[data-flw]"); if (w) { const S = flS(); S.win = w.dataset.flw; LS.set("flWin", S.win); flRender(); return; }
    const g = e.target.closest("[data-flgo]"); if (g) { openTab("derinlik", true); setTimeout(() => { const c = $("fl-card"); if (c) { sgNav(); window.scrollTo(0, Math.max(0, c.getBoundingClientRect().top + window.scrollY - 70)); SG.y = window.scrollY; } }, 250); }
  });

  // ================================================================ (3) AKD K/Z + ANALİZ
  function akpS() { return AKP || (AKP = { d: null, key: "", busy: false, sort: "tot", dir: -1, exp: false }); }
  function akpKey() { return `${st.sym}|${st.akdPeriod}|${st.akdPeriod === "custom" ? st.akdDate || "" : ""}`; }
  async function akpLoad() {
    if (!v6ok()) return;
    const S = akpS(), key = akpKey(), gen = st.gen;
    if (S.key !== key) { S.d = null; S.key = key; S.exp = false; akpRender(); }
    if (S.busy) return;
    S.busy = true;
    let url = `/api/stocks/${st.sym}/akd-plus?period=${st.akdPeriod}`;
    if (st.akdPeriod === "custom" && st.akdDate) url += `&from=${st.akdDate}&to=${st.akdDate}`;
    try {
      const d = await api(url, { timeout: 25000 });
      if (gen !== st.gen || key !== akpKey()) return;
      S.d = d; akpRender();
    } catch (e) {
      if (!S.d) setH($("akp"), `<div class="card"><div class="empty">K/Z analizi alınamadı (${esc(e.message || e)})</div></div>`);
    } finally { S.busy = false; }
  }
  function akpRender() {
    const el = $("akp"); if (!el) return;
    const S = akpS(), d = S.d;
    if (!d) { setH(el, `<div class="card"><div class="empty">Kurum K/Z ve AKD analizi yükleniyor…</div></div>`); return; }
    if (!d.available) { setH(el, `<div class="card"><div class="empty">${esc(d.note || "AKD verisi yok")}</div></div>`); return; }
    try { setH(el, akpHtml(d, S)); } catch (e) { setH(el, `<div class="card"><div class="empty">Gösterilemedi: ${esc(e.message || e)}</div></div>`); }
  }
  function akpHtml(d, S) {
    const sm = d.sum || {}, A = d.analiz || {}, last = d.last;
    const li = (r) => `<div class="ozp-br"><span>${esc(brName(r.br))} <small class="muted">${r.net > 0 ? "alıcı" : "satıcı"} · ${fShort(Math.abs(r.net))} lot @ ${kmP(r.co)}</small></span><b class="${cls(r.tot)}">${v6stl(r.tot)} <small>${v6pc(r.kzp)}</small></b></div>`;
    const K = (k) => (r) => (isNum(r[k]) ? r[k] : -Infinity);
    const rows = (d.rows || []).slice();
    const key = S.sort, dir = S.dir;
    rows.sort((a, b) => { const x = K(key)(a), y = K(key)(b); return key === "br" ? dir * String(a.br).localeCompare(String(b.br), "tr") : dir * ((x === -Infinity ? -1e18 : x) - (y === -Infinity ? -1e18 : y)); });
    const show = S.exp ? rows : rows.slice(0, 10);
    const th = (k, l, c) => `<th data-akps="${k}" class="${c || ""} ${S.sort === k ? "sorted" + (S.dir > 0 ? " asc" : "") : ""}">${l}</th>`;
    const hasReal = rows.some((r) => isNum(r.real));
    const dl = A.durum === "TOPLAMA" ? "pos" : A.durum === "DAĞITIM" ? "neg" : "";
    let h = `<section class="card akp-card" id="akp-kz"><div class="card-h"><span class="card-title">KURUM KÂR / ZARAR</span><span class="muted sm">${esc(d.label || "")} · son ${kmP(last)}</span></div>
      <div class="ozp-kvs">${v6kv(`Net alıcılar (${fN(sm.nb)}) açık K/Z`, v6stl(sm.kz_b), cls(sm.kz_b))}${v6kv(`Net satıcılar (${fN(sm.ns)}) açık K/Z`, v6stl(sm.kz_s), cls(sm.kz_s))}
        ${hasReal ? v6kv("Gün içi gerçekleşen · alıcılar", v6stl(sm.real_b), cls(sm.real_b)) + v6kv("Gün içi gerçekleşen · satıcılar", v6stl(sm.real_s), cls(sm.real_s)) : ""}
        ${v6kv("Fiyat büyük kurum maliyetlerinin", `${fN(sm.above)} / ${fN(sm.nbig)} üstünde`, sm.above * 2 >= sm.nbig ? "pos" : "neg")}</div>
      <div class="ozp-2c"><div><div class="mk-sub pos">EN ÇOK KÂRDA</div>${(sm.prof || []).map(li).join("") || `<div class="muted sm">—</div>`}</div><div><div class="mk-sub neg">EN ÇOK ZARARDA</div>${(sm.loss || []).map(li).join("") || `<div class="muted sm">—</div>`}</div></div>
      <div class="mk-sub">BÜYÜK KURUMLARIN MALİYETİ vs FİYAT</div><div class="akp-big">${(sm.big || []).map((r) => `<div class="ozp-pos"><span><span data-k5br="${esc(r.br)}">${esc(brName(r.br))}</span> <small class="${r.side === "ALICI" ? "pos" : "neg"}">${r.side}</small><small class="akp-ak" title="Aktif alış % / aktif alış lotu (bugünkü işlem kaydı, AKD Taraması ile aynı)">aktif alış ${isNum(r.aa) ? "%" + nf(1).format(r.aa) : "—"} · ${isNum(r.abl) ? fShort(r.abl) + " lot" : "—"}</small></span><b>${kmP(r.co)}</b><em class="${cls(r.d)}" title="fiyatın maliyete göre konumu">${v6pc(r.d)}</em></div>`).join("")}</div>
      <div class="tbl-scroll akp-ts"><table class="grid-table akp-t"><thead><tr>${th("br", "KURUM", "l sticky")}${th("net", "NET LOT")}${th("co", "MALİYET")}${th("aa", "AKTİF ALIŞ %")}${th("abl", "AKTİF ALIŞ LOT")}${th("kz", "AÇIK K/Z ₺")}${th("kzp", "K/Z %")}${hasReal ? th("real", "GERÇEKLEŞEN ₺") + th("ba", "ALIŞ ORT.") + th("sa", "SATIŞ ORT.") : ""}${th("tot", "TOPLAM K/Z ₺")}</tr></thead>
      <tbody>${show.map((r) => `<tr><td class="l sticky" data-k5br="${esc(r.br)}">${esc(brName(r.br))}</td><td class="${cls(r.net)}">${r.net > 0 ? "+" : ""}${fN(r.net)}</td><td>${kmP(r.co)}</td>${atAkTd(r.aa, r.aat, 1)}${atLotTd(r.abl, 1)}<td class="${cls(r.kz)}">${v6stl(r.kz)}</td><td class="${cls(r.kzp)}">${v6pc(r.kzp)}</td>${hasReal ? `<td class="${cls(r.real)}" title="${isNum(r.mt) ? fN(r.mt) + " lot hem alınıp hem satıldı" : ""}">${isNum(r.real) ? v6stl(r.real) : "—"}</td><td>${kmP(r.ba)}</td><td>${kmP(r.sa)}</td>` : ""}<td class="${cls(r.tot)}"><b>${v6stl(r.tot)}</b></td></tr>`).join("")}</tbody></table></div>
      ${rows.length > 10 ? `<button type="button" class="more-btn" data-akpexp="1">${S.exp ? "Daha Az Göster" : `Tüm kurumlar (+${rows.length - 10})`}</button>` : ""}
      <div class="src-note">Açık K/Z (tahmini) = net lot × (son − maliyet), AKD sekmesiyle aynı kaynak ve aynı maliyet. K/Z % = kurumun yönüne göre (alıcı için fiyat maliyetin üstündeyse +). ${hasReal ? "Gerçekleşen = gün içinde hem alıp hem satılan lot × (satış ort. − alış ort.), gerçek işlem kaydından (kurumun işlem kaydı alışı AKD alışından medyan %" + nf(2).format(d.match_err || 0) + " sapıyor). Toplam = açık + gerçekleşen." : esc(d.real_note || "")} ${d.aktif_ok ? "Aktif alış % = kurumun bu hissedeki aktif alış lotu ÷ tüm alış lotu, aktif alış lot = piyasa emriyle (satıcının fiyatına giderek) alınan lot — işlem kaydından, AKD Taraması sütunlarıyla birebir aynı." : esc(d.aktif_note || "")}</div></section>`;
    // v1.26.2 EN ÇOK AKTİF ALAN KURUMLAR
    const AT5 = d.aktif_top || [];
    h += `<section class="card akp-card" id="akp-act"><div class="card-h"><span class="card-title">EN ÇOK AKTİF ALAN KURUMLAR</span><span class="muted sm">aktif alış lotuna göre ilk 5${d.aktif_tot ? ` · hissede ${fShort(d.aktif_tot.abl)} lot aktif alış` : ""}</span></div>
      ${d.aktif_ok && AT5.length ? `<div class="akp-act">${AT5.map((r, i) => `<div class="akp-ar"><span class="n">${i + 1}</span><span class="b"><b data-k5br="${esc(r.br)}">${esc(brName(r.br))}</b><small>hissedeki aktif alışın %${nf(1).format(r.share || 0)}'i</small></span><span class="v"><b class="${(r.aa || 0) >= 70 ? "pos" : (r.aa || 0) < 30 ? "muted" : ""}">${isNum(r.aa) ? "%" + nf(1).format(r.aa) : "—"}</b><small>aktif %</small></span><span class="v"><b>${fShort(r.abl)}</b><small>aktif lot · ${fShort(r.abtl)} ₺</small></span><span class="v"><b class="${cls(r.net)}">${r.net > 0 ? "+" : r.net < 0 ? "−" : ""}${fShort(Math.abs(r.net))}</b><small>net lot</small></span><span class="v"><b>${kmP(r.co)}</b><small>maliyet</small></span></div>`).join("")}</div>`
        : `<div class="muted sm">${esc(d.aktif_note || "Aktif alış verisi yok.")}</div>`}</section>`;
    h += `<section class="card akp-card" id="akp-an"><div class="card-h"><span class="card-title">AKD ANALİZİ</span><span class="ozp-lab ${dl} akp-dur">${esc(A.durum || "—")}</span></div>
      ${(A.tahtaci || []).map(thtHtml).join("")}
      <div class="ozp-yt">${esc(A.yorum || "")}</div>
      <div class="mk-sub">YOĞUNLAŞMA · ilk 3 alıcı / ilk 3 satıcı</div><div class="fl-bar"><span class="pos">İlk 3 alıcı %${nf(1).format(A.b3 || 0)}</span><div class="press-bar thin"><span style="width:${(A.b3 || 0) + (A.s3 || 0) ? Math.max(2, Math.min(98, (A.b3 / (A.b3 + A.s3)) * 100)).toFixed(1) : 50}%"></span></div><span class="neg">İlk 3 satıcı %${nf(1).format(A.s3 || 0)}</span></div>
      <ul class="akp-pts">${(A.pts || []).filter((p) => !/^(⚠ TAHTACI|🚂 TAVAN TRENİ)/.test(p)).map((p) => `<li>${esc(p)}</li>`).join("")}</ul>
      <div class="src-note">TOPLAMA = az sayıda kurum net alımın büyük kısmını yapıyor (ilk 3 alıcı ≥%55, alıcı sayısı satıcıdan az ya da yoğunlaşma farkı ≥15 puan); DAĞITIM simetriği. Israrcı = son kayıtlı günlerde aynı yönde net olan kurumlar (data/akd) + v1.23 ısrar skoru ≥70. TAHTACI SİNYALİ = aynı kurum hem AKD'de en çok net alan (ya da ilk 3) hem de hissede en çok AKTİF alan (aktif alış lotu) — güçlü: 1. net alıcı, aktif ≥%65, net alımın ≥%25'i, hissedeki aktif alışın ≥%25'i ve hisse ortalamasının ≥12 puan üstü; orta: daha gevşek eşikler; satış tarafı simetrik ("aşağı bastırıyor olabilir"). 🚂 TAVAN TRENİ = hissenin en büyük balinası (AKD Alış #1 ya da en büyük alış lotu) + net alımın ≥%30'u + alımının ≥%65'i AKTİF + ≥5 Mn ₺ aktif alış (GÜÇLÜ: Alış #1 + ≥10 Mn ₺); aynı kurumun TAHTACI ↑ sinyali bu satırda birleşir. Bu bir yorumdur, yatırım tavsiyesi değildir.</div></section>`;
    return h;
  }
  document.addEventListener("click", (e) => {
    if (!v6ok()) return;
    const s = e.target.closest("[data-akps]"); if (s) { const S = akpS(), k = s.dataset.akps; if (S.sort === k) S.dir *= -1; else { S.sort = k; S.dir = k === "br" ? 1 : -1; } akpRender(); return; }
    const x = e.target.closest("[data-akpexp]"); if (x) { const S = akpS(); S.exp = !S.exp; akpRender(); }
  });

  // ================================================================ (4) AKD TARAMASI
  function atDefF() { return { mode: "best", side: "", durum: "", q: "", brs: [], np: ["", ""], bgp: ["", ""], sgp: ["", ""], nl: ["", ""], ntl: ["", ""], nb: ["", ""], ns: ["", ""], b3: ["", ""], kz: ["", ""], kzp: ["", ""], tp: ["", ""], gd: ["", ""], aa: ["", ""], as: ["", ""], abl: ["", ""], abtl: ["", ""], asl: ["", ""], tnb: ["", ""], tnp: ["", ""], tntl: ["", ""], s3: ["", ""], sab: ["", ""], ilkn: "5", ilkd: "", ilkp: "", ilkl: "", ilkc: ["3", "5", "10"], per: "" }; }   // v1.27.1 İLK N + dönem
  function atS() {
    if (!AT) { const f = Object.assign(atDefF(), LS.get("atF", {}) || {}); AT = { d: null, date: "", busy: false, last: 0, sort: "ntl", dir: -1, n: 100, f, sets: LS.get("atSets", []) || [], brq: "", brOpen: false, watch: null, preset: "" }; }
    return AT;
  }
  function atSave() { const S = atS(); LS.set("atF", S.f); }
  var AT_FL = [["np", "Net % (DAĞILIM)", "Alıcıda +, satıcıda − (AKD sekmesi DAĞILIM)"], ["bgp", "Alış payı %", "Kurumun alış lotu / hissenin toplam alış lotu"], ["sgp", "Satış payı %", "Kurumun satış lotu / toplam satış lotu"],
    ["nl", "Net lot", "Alıcıda +, satıcıda −"], ["ntl", "Net ₺", "Net lot × son fiyat (alıcıda +)"], ["nb", "Alıcı kurum sayısı", "Hissedeki net alıcı sayısı"], ["ns", "Satıcı kurum sayısı", "Hissedeki net satıcı sayısı"],
    ["b3", "İlk 3 alıcı yoğunlaşma %", "İlk 3 net alıcının net alımdaki payı"], ["kz", "K/Z ₺", "Net lot × (son − maliyet)"], ["kzp", "K/Z %", "Kurumun yönüne göre"], ["tp", "Hacim payı %", "Kurumun (alış+satış) / toplam"], ["gd", "Günlük değişim %", "Hissenin günlük % değişimi"],
    ["aa", "Aktif alış %", "Kurumun bu hissedeki alış lotunun ne kadarı AKTİF (piyasa emriyle, satıcının fiyatına giderek) alındı — v1.23 Maliyet Yükselten ile aynı tanım"], ["as", "Aktif satış %", "Kurumun satış lotunun ne kadarı AKTİF (alıcının fiyatına giderek) satıldı"],
    ["abl", "Aktif alış lot", "Kurumun seans boyunca aktif aldığı lot (işlem kaydı)"], ["abtl", "Aktif alış ₺", "Kurumun seans boyunca aktif aldığı tutar (₺)"], ["asl", "Aktif satış lot", "Kurumun seans boyunca aktif sattığı lot"]];   // v1.26.1
  // v1.26.1 TÜM AKD NET (hisse bazında) filtreleri
  var AT_FN = [["tnb", "Net lot (tüm net alıcılar)", "Net alıcıların toplam net lotu = net satıcıların toplamı (AKD TOPLAM)"], ["tnp", "Net % (hacme göre)", "Toplam net lot ÷ hissenin toplam işlem lotu"], ["tntl", "Net ₺", "Toplam net lot × son fiyat"],
    ["b3", "İlk 3 alıcı %", "İlk 3 net alıcının net alımdaki payı"], ["s3", "İlk 3 satıcı %", "İlk 3 net satıcının net satıştaki payı"], ["nb", "Alıcı kurum sayısı", "Net alıcı sayısı"], ["ns", "Satıcı kurum sayısı", "Net satıcı sayısı"],
    ["sab", "Aktif alış % (hisse)", "Hissede aktif alış lotu ÷ (aktif alış + aktif satış) — Seans İşlem Akışı ile aynı"], ["gd", "Günlük değişim %", "Hissenin günlük % değişimi"]];
  var AT_CN = [["s", "HİSSE", "l sticky"], ["tnb", "NET LOT"], ["tntl", "NET ₺"], ["tnp", "NET % (HACİM)"], ["vol", "TOPLAM LOT"], ["b3", "İLK 3 ALICI %"], ["s3", "İLK 3 SATICI %"], ["nb", "ALICI/SATICI"], ["du", "DURUM", "l"], ["sab", "AKTİF ALIŞ %"], ["p", "SON"], ["gd", "GÜNLÜK %"]];
  var AT_PRE = [["p30", "Tek kurum %30+ net alıcı", { side: "buy", np: ["30", ""], ntl: ["1000000", ""] }, "best"], ["top", "Toplama", { durum: "TOPLAMA", side: "buy" }, "best"],
    ["kar", "Kurum kârda + alıyor", { side: "buy", kzp: ["0.5", ""], ntl: ["1000000", ""] }, "all"], ["sav", "Kurum zararda + alıyor (maliyet savunma)", { side: "buy", kzp: ["", "-0.5"], ntl: ["1000000", ""] }, "all"],
    ["dag", "Dağıtım", { durum: "DAĞITIM", side: "sell" }, "best"], ["sat30", "Tek kurum %30+ net satıcı", { side: "sell", np: ["", "-30"], ntl: ["", "-1000000"] }, "best"],
    ["agr", "Agresif alıcı (aktif alış ≥%70 + net alıcı)", { side: "buy", aa: ["70", ""], ntl: ["1000000", ""] }, "all"], ["agrs", "Agresif satıcı (aktif satış ≥%70 + net satıcı)", { side: "sell", as: ["70", ""], ntl: ["", "-1000000"] }, "all"],
    ["enak", "En çok aktif alış yapan", {}, "all", "abtl"], ["tnp", "En yüksek net % (hisse)", { tntl: ["1000000", ""] }, "net", "tnp"], ["tnb", "En yüksek net lot (hisse)", {}, "net", "tnb"],   // v1.26.1
    // v1.27.1 İLK N NET PGÇ (AKD sekmesi kartı ile aynı): [anahtar, ad, filtre, mod, sıralama, yön]
    ["i5a50", "İlk 5 güçlü net alan (≥%50)", { ilkn: "5", ilkd: "a", ilkp: "50", tntl: ["1000000", ""] }, "net", "i5p", -1], ["i5s50", "İlk 5 güçlü net satan (≥%50)", { ilkn: "5", ilkd: "s", ilkp: "50", tntl: ["1000000", ""] }, "net", "i5p", 1],
    ["i3a", "İlk 3 güçlü alan (≥%40)", { ilkn: "3", ilkd: "a", ilkp: "40", tntl: ["1000000", ""] }, "net", "i3p", -1], ["i10a", "İlk 10 güçlü alan (≥%15)", { ilkn: "10", ilkd: "a", ilkp: "15", tntl: ["1000000", ""] }, "net", "i10p", -1],
    ["i5top", "En yüksek İlk 5 net alan %", { ilkn: "5", ilkd: "a", tntl: ["1000000", ""] }, "net", "i5p", -1], ["i5bot", "En yüksek İlk 5 net satan %", { ilkn: "5", ilkd: "s", tntl: ["1000000", ""] }, "net", "i5p", 1]];
  const AT_IN = ["3", "5", "10"];
  function atIlk(o, n, a, s) { o["i" + n + "a"] = a; o["i" + n + "s"] = s; o["i" + n + "n"] = isNum(a) && isNum(s) ? a - s : null; o["i" + n + "p"] = isNum(a) && isNum(s) ? ilkPct(a, s) : null; }
  function atCN() {   // v1.27.1 TÜM AKD NET sütunları: HİSSE + seçili İLK N sütunları + v1.26.1 sütunları
    const S = atS(), f = S.f, sel = AT_IN.filter((n) => (f.ilkc || AT_IN).includes(n));
    const tip = "ALAN = ilk N net alıcının net lot toplamı · SATAN = ilk N net satıcının · NET = ALAN − SATAN · % = |ALAN − SATAN| ÷ max(ALAN, SATAN) × 100 (AKD sekmesi İLK N NET PGÇ kartı ile aynı)";
    return [AT_CN[0]].concat(sel.map((n) => ["i" + n + "n", `<span title="${esc(tip)}">İLK ${n} NET</span> <span class="at-pcs ${S.sort === "i" + n + "p" ? "on" : ""}" data-atsort="i${n}p" title="% ile sırala">%${S.sort === "i" + n + "p" ? (S.dir > 0 ? "↑" : "↓") : "⇅"}</span>`, "at-ilkh"]), AT_CN.slice(1));
  }
  function atIlkTd(r, n) {
    const a = r["i" + n + "a"], s = r["i" + n + "s"], v = r["i" + n + "n"], p = r["i" + n + "p"];
    if (!isNum(v)) return `<td class="muted at-ilkc">—</td>`;
    const c = v > 0 ? "pos" : v < 0 ? "neg" : "muted", big = Math.abs(p || 0) >= 50 ? " at-akh" : "";
    return `<td class="at-ilkc ${c}${big}" title="İLK ${n}: ALAN ${fN(a)} · SATAN ${fN(s)} · NET ${v > 0 ? "ALAN" : "SATAN"} ${fN(Math.abs(v))} · |${fN(a)} − ${fN(s)}| ÷ ${fN(Math.max(a, s))} = ${ilkPctTxt(p)}"><b>${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(v) >= 1e7 ? fShort(Math.abs(v)) : fN(Math.abs(v))}</b><small>${ilkPctTxt(p)}</small></td>`;
  }
  function atPerS() { const S = atS(); if (!S.pd) S.pd = {}; return S.pd; }
  async function atPerLoad(per, force) {
    const P = atPerS(), X = P[per] || (P[per] = { d: null, busy: false, ts: 0 });
    if (X.busy || (!force && X.d && !X.d.running && Date.now() - X.ts < 120000)) return;
    X.busy = true;
    try {
      const d = await api(`/api/akd/donem?period=${per}`, { timeout: 30000 }); X.d = d; X.ts = Date.now(); X.err = null;
      const C = (d.cols && d.cols.stocks) || [], ix = {}; C.forEach((c, i) => (ix[c] = i));
      X.stk = (d.stocks || []).map((s) => { const o = { s: s[ix.s], p: s[ix.p], gd: s[ix.gd], nb: s[ix.nb], ns: s[ix.ns], b3: s[ix.b3], s3: s[ix.s3], du: s[ix.durum], vol: s[ix.vol], tnb: s[ix.tnb], tns: s[ix.tns], tnp: s[ix.tnp], sab: null, tntl: isNum(s[ix.tnb]) && isNum(s[ix.p]) ? s[ix.tnb] * s[ix.p] : null };
        AT_IN.forEach((n) => atIlk(o, n, s[ix["i" + n + "a"]], s[ix["i" + n + "s"]])); return o; });
    } catch (e) { X.err = String(e.message || e); }
    finally { X.busy = false; }
    if (st.view === "akdt" && atS().f.mode === "net" && atS().f.per === per) atRender();
    if (X.d && X.d.running) { clearTimeout(X.t); X.t = setTimeout(() => { if (st.view === "akdt" && atS().f.per === per && !document.hidden) atPerLoad(per, true); }, 3000); }
  }
  function atOpen() {
    if (!v6ok()) return;
    atBuild(); atLoad(true); atWatchLoad();
  }
  async function atLoad(force) {
    const S = atS();
    if (S.busy) return;
    if (!force && Date.now() - S.last < 60000) return;
    S.busy = true; S.last = Date.now();
    const b = $("at-ref"); if (b) b.classList.add("spin");
    try {
      const tok = S.d && S.d.tok && (S.d.date === S.date || !S.date) ? `&tok=${encodeURIComponent(S.d.tok)}` : "";
      const d = await api(`/api/akd/tarama?date=${encodeURIComponent(S.date || "")}${force ? "" : tok}`, { timeout: 60000 });
      if (d && d.same) return;
      S.d = d; atPrep(); atRender();
    } catch (e) {
      if (!S.d) setH($("at-body"), `<tr><td colspan="18" class="empty">AKD taraması alınamadı (${esc(e.message || e)}) — ↻ ile yeniden deneyin</td></tr>`);
    } finally { S.busy = false; const b2 = $("at-ref"); if (b2) b2.classList.remove("spin"); }
  }
  setInterval(() => { try { if (v6ok() && st.view === "akdt" && !document.hidden && AT && AT.d && AT.d.cur) atLoad(false); } catch (e) {} }, 10000);
  function atPrep() {
    const S = atS(), d = S.d; if (!d) return;
    const B = d.brokers, Sk = d.stocks;
    S.rows = d.rows.map((r) => { const s = Sk[r[0]], p = s[1]; return { s: s[0], p, gd: s[2], nb: s[3], ns: s[4], b3: s[5], s3: s[6], du: s[7], br: B[r[1]], nl: r[2], np: r[3], bgp: r[4], sgp: r[5], co: r[6], kz: r[7], kzp: r[8], tp: r[9], bl: r[10], sl: r[11], aa: r[12], aat: r[13], as: r[14], abl: r[15], abtl: r[16], asl: r[17], astl: r[18], ntl: isNum(p) ? r[2] * p : (isNum(r[6]) ? r[2] * r[6] : null) }; });
    S.stk = Sk.map((s) => ({ s: s[0], p: s[1], gd: s[2], nb: s[3], ns: s[4], b3: s[5], s3: s[6], du: s[7], vol: s[8], tnb: s[9], tns: s[10], tnp: s[11], sab: s[12], sabl: s[13], sasl: s[14], tntl: isNum(s[9]) && isNum(s[1]) ? s[9] * s[1] : null }));   // v1.26.1 TÜM AKD NET
    S.blist = [...new Set(B)].sort((a, b) => brName(a).localeCompare(brName(b), "tr"));
    // v1.27.1 İLK 3/5/10 (günlük): AKD sekmesi kartı ile aynı — ilk N net alıcının net lot toplamı / ilk N net satıcının |net lot| toplamı
    const G = Sk.map(() => [[], []]);
    for (const r of d.rows) { const v = r[2]; if (v > 0) G[r[0]][0].push(v); else if (v < 0) G[r[0]][1].push(-v); }
    S.stk.forEach((o, i) => { const b = G[i][0].sort((x, y) => y - x), s = G[i][1].sort((x, y) => y - x); AT_IN.forEach((n) => { const N = +n; let a = 0, z = 0; for (let k = 0; k < N && k < b.length; k++) a += b[k]; for (let k = 0; k < N && k < s.length; k++) z += s[k]; atIlk(o, n, a, z); }); });
  }
  function atNum(v) { if (v === "" || v == null) return null; const x = parseFloat(String(v).replace(/\s/g, "").replace(",", ".")); return isFinite(x) ? x : null; }
  function atFilterN() {   // v1.26.1 TÜM AKD NET — hisse başına tek satır
    const S = atS(), f = S.f, PX = f.per ? atPerS()[f.per] : null, src = f.per ? (PX && PX.stk) : S.stk; if (!src) return [];
    if (f.per && S.stk && PX._gdf !== S.stk) { const gm = new Map(S.stk.map((o) => [o.s, o.gd])); src.forEach((o) => { if (!isNum(o.gd) && isNum(gm.get(o.s))) o.gd = gm.get(o.s); }); PX._gdf = S.stk; }   // GÜNLÜK % = seçili seans
    const rng = AT_FN.map(([k]) => [k, atNum(f[k][0]), atNum(f[k][1])]).filter((x) => x[1] != null || x[2] != null);
    const q = trUpper(f.q || "").trim();
    const iN = AT_IN.includes(String(f.ilkn)) ? String(f.ilkn) : "5", kp = "i" + iN + "p", kn = "i" + iN + "n", mp = atNum(f.ilkp), ml = atNum(f.ilkl);   // v1.27.1
    const out = src.filter((r) => { if (f.durum && r.du !== f.durum) return false;
      if (f.ilkd || mp != null || ml != null) { const p = r[kp]; if (!isNum(p)) return false; if (f.ilkd === "a" && !(p > 0)) return false; if (f.ilkd === "s" && !(p < 0)) return false; if (mp != null && Math.abs(p) < Math.abs(mp)) return false; if (ml != null && Math.abs(r[kn] || 0) < Math.abs(ml)) return false; } for (const [k, lo, hi] of rng) { const v = r[k]; if (!isNum(v)) return false; if (lo != null && v < lo) return false; if (hi != null && v > hi) return false; } if (q && !r.s.includes(q)) return false; return true; });
    const k = S.sort, dir = S.dir;
    out.sort((a, b) => { if (k === "s" || k === "du") return dir * String(a[k]).localeCompare(String(b[k]), "tr"); const x = isNum(a[k]) ? a[k] : -1e18, y = isNum(b[k]) ? b[k] : -1e18; return dir * (x - y); });
    return out;
  }
  function atFilter() {
    const S = atS(), f = S.f; if (!S.rows) return [];
    const rng = AT_FL.map(([k]) => [k, atNum(f[k][0]), atNum(f[k][1])]).filter((x) => x[1] != null || x[2] != null);
    const q = trUpper(f.q || "").trim();
    const sel = new Set(f.brs || []);
    const useSel = f.mode === "sel" && sel.size;
    let out = S.rows.filter((r) => {
      if (useSel && !sel.has(r.br)) return false;
      if (f.side === "buy" && !(r.nl > 0)) return false;
      if (f.side === "sell" && !(r.nl < 0)) return false;
      if (f.durum && r.du !== f.durum) return false;
      for (const [k, lo, hi] of rng) { const v = r[k]; if (!isNum(v)) return false; if (lo != null && v < lo) return false; if (hi != null && v > hi) return false; }
      if (q && !(r.s.includes(q) || trUpper(brName(r.br)).includes(q) || trUpper(r.br).includes(q))) return false;
      return true;
    });
    if (f.mode === "best") { const m = new Map(); for (const r of out) { const c = m.get(r.s); if (!c || Math.abs(r.ntl || 0) > Math.abs(c.ntl || 0)) m.set(r.s, r); } out = [...m.values()]; }
    const k = S.sort, dir = S.dir;
    out.sort((a, b) => { if (k === "s" || k === "br" || k === "du") return dir * String(k === "br" ? brName(a[k]) : a[k]).localeCompare(String(k === "br" ? brName(b[k]) : b[k]), "tr"); const x = isNum(a[k]) ? a[k] : -1e18, y = isNum(b[k]) ? b[k] : -1e18; return dir * (x - y); });
    return out;
  }
  function atBuild() {
    if ($("at-ctl") && $("at-ctl")._b) return;
    const c = $("at-ctl"); if (!c) return;
    c._b = 1;
    $("at-info").innerHTML = `<details class="card at-info"><summary><b>ⓘ AKD Taraması nedir?</b> <small class="muted">ne · nasıl kullanılır · dikkat</small></summary>
      <p><b>Ne:</b> Tüm hisselerin günlük AKD'sini (aracı kurum dağılımı) tek tabloda tarar: her hissede her kurumun net lotu, DAĞILIM %'si (AKD sekmesindeki ile birebir aynı), alış/satış payı, maliyeti, son fiyata göre kâr/zararı, <b>aktif alış % / aktif satış %</b>'si ve hissenin TOPLAMA/DAĞITIM durumu.</p>
      <p><b>Aktif alış %:</b> kurumun o hissedeki alış lotunun ne kadarının AKTİF (piyasa emriyle, satıcının bekleyen emrine vurarak) alındığı = aktif alış lotu ÷ tüm alış lotu, gerçek işlem kaydından (o seansın işlemleri; v1.23 Maliyet Yükselten "Aktif alış %" ile birebir aynı). Küçük yazı: ₺ bazında aynı oran. <b>%70+</b> = kurum fiyatı kovalıyor, acelesi var (agresif alıcı); <b>%30 altı</b> = çoğunlukla pasif, bekleyen alış emirleriyle sabırla topluyor. <b>Aktif satış %</b> aynı şekilde satış lotunun alıcının fiyatına giderek satılan payıdır (yüksekse kurum mal boşaltmakta acele ediyor). İşlem kaydı olmayan hisse/kurumda "—" gösterilir; açılış/kapanış seansı (tek fiyat) işlemleri ne aktif ne pasiftir, paydada kalır.</p>
      <p><b>Nasıl kullanılır:</b> Hazır kalıplardan birine dokunun (örn. "Tek kurum %30+ net alıcı") ya da filtreleri kendiniz girin. <i>EN İYİ EŞLEŞME</i> her hisse için filtreye uyan en büyük (net ₺) kurumu, <i>TÜM SATIRLAR</i> tüm kurum satırlarını, <i>KURUM SEÇ</i> seçtiğiniz kurum(lar)ın işlem yaptığı TÜM hisseleri gösterir (örn. Yapı Kredi hangi hisselerde ne kadar aktif aldı? — Taraf: Net alıcı ile yalnız net alıcı olduklarına daraltın). <i>TÜM AKD NET (hisse bazında)</i> her hisse için tek satır: tüm net alıcıların toplam net lotu (= net satıcıların toplamı), net ₺, net % (toplam işlem lotuna göre), ilk 3 alıcı/satıcı payı, alıcı/satıcı kurum sayısı, TOPLAMA/DAĞITIM ve hissenin aktif alış %'si. "En çok aktif alış yapan" kalıbı tüm hisse × kurum satırlarını aktif alış ₺'ye göre sıralar (net satıcı kurumlar dahil). Başlığa dokunup sıralayın; filtre setlerinizi kaydedin. Bildirim kuralı ekleyerek seçtiğiniz kurum bir hisseye eşik üstü girdiğinde bildirim alın (isteğe bağlı "aktif % ≥" eşiğiyle yalnız agresif girişler). "Agresif alıcı" kalıbı: aktif alış ≥%70 + net alıcı + ≥1 Mn ₺.</p>
      <p><b>Dikkat:</b> AKD kurum bazlı toplamdır, kurumun kendi mi müşterisi mi olduğunu söylemez; bir kurumdaki çok sayıda küçük yatırımcı da "kurum alıyor" gibi görünür (Midas, Garanti gibi). K/Z tahminidir (net lot × (son − maliyet)); gün içi alıp-satma kârını içermez. Seans içinde AKD periyodik güncellenir; az işlem gören hisselerde DAĞILIM % küçük lotlarla bile yüksek çıkabilir — net ₺ filtresini birlikte kullanın. Aktif % AKD'den değil işlem kaydından gelir; kurum adı eşleşmesi işlem kaydıyla AKD'de aynıdır, küçük lot farkları (gecikmeli/düzeltilmiş işlemler) olabilir. Az alış yapan kurumda aktif % tek bir işlemle %0 ya da %100 olabilir — net ₺ ile birlikte değerlendirin.</p></details>`;
    c.innerHTML = `<div class="at-r1"><select id="at-date" class="pill-select" aria-label="Seans"></select><input type="search" class="ak-search" id="at-q" placeholder="Hisse / kurum ara..." autocomplete="off" spellcheck="false" /><button type="button" class="btn-refresh" id="at-ref" title="Yenile">↻</button></div>
      <div class="seg full at-mode" id="at-mode"><button type="button" data-atm="best">EN İYİ EŞLEŞME</button><button type="button" data-atm="all">TÜM SATIRLAR</button><button type="button" data-atm="sel">KURUM SEÇ</button><button type="button" data-atm="net">TÜM AKD NET (hisse bazında)</button></div>
      <div class="at-ilk" id="at-ilk" hidden></div>
      <div class="at-brw" id="at-brw" hidden><div class="at-chips" id="at-chips"></div><input type="search" class="ak-search" id="at-brq" placeholder="Kurum ara (örn. Yapı Kredi) — birden çok seçilebilir" autocomplete="off" spellcheck="false" /><div class="at-brl" id="at-brl" hidden></div></div>
      <div class="at-pre" id="at-pre">${AT_PRE.map(([k, l]) => `<button type="button" class="ozp-chip" data-atp="${k}">${esc(l)}</button>`).join("")}<button type="button" class="ozp-chip" data-atp="reset">↺ Sıfırla</button></div>
      <details class="at-fd" id="at-fd"><summary>Filtreler <b id="at-fn"></b></summary>
        <div class="at-fg"><label><span>Taraf</span><select id="at-side" class="pill-select"><option value="">Tümü</option><option value="buy">Net alıcı</option><option value="sell">Net satıcı</option></select></label>
        <label><span>Durum</span><select id="at-du" class="pill-select"><option value="">Tümü</option><option value="TOPLAMA">TOPLAMA</option><option value="DAĞITIM">DAĞITIM</option><option value="NÖTR">NÖTR</option></select></label>
        ${AT_FL.map(([k, l, t]) => `<label class="at-fbr" title="${esc(t)}"><span>${esc(l)}</span><span class="at-mm"><input type="text" inputmode="decimal" data-atf="${k}" data-ati="0" placeholder="min" /><input type="text" inputmode="decimal" data-atf="${k}" data-ati="1" placeholder="max" /></span></label>`).join("")}${AT_FN.map(([k, l, t]) => `<label class="at-fnet" title="${esc(t)}"><span>${esc(l)}</span><span class="at-mm"><input type="text" inputmode="decimal" data-atf="${k}" data-ati="0" placeholder="min" /><input type="text" inputmode="decimal" data-atf="${k}" data-ati="1" placeholder="max" /></span></label>`).join("")}</div>
        <div class="at-sv"><input type="text" class="ak-search" id="at-svn" placeholder="Filtre seti adı" maxlength="40" /><button type="button" class="btn-ghost sm" id="at-svb">💾 Kaydet</button></div>
      </details>
      <div class="at-sets" id="at-sets"></div>`;
    const S = atS();
    $("at-q").value = S.f.q || "";
    $("at-q").addEventListener("input", (e) => { S.f.q = e.target.value; S.n = 100; atSave(); atRender(); });
    $("at-ref").addEventListener("click", () => atLoad(true));
    $("at-date").addEventListener("change", (e) => { S.date = e.target.value; S.d = null; setH($("at-body"), `<tr><td colspan="18" class="empty">Yükleniyor…</td></tr>`); atLoad(true); });
    $("at-side").addEventListener("change", (e) => { S.f.side = e.target.value; S.preset = ""; atSave(); atRender(); });
    $("at-du").addEventListener("change", (e) => { S.f.durum = e.target.value; S.preset = ""; atSave(); atRender(); });
    c.addEventListener("input", (e) => { const i = e.target.closest("[data-atf]"); if (!i) return; S.f[i.dataset.atf][+i.dataset.ati] = i.value; S.preset = ""; S.n = 100; atSave(); clearTimeout(S._t); S._t = setTimeout(atRender, 250); });
    $("at-brq").addEventListener("input", (e) => { S.brq = e.target.value; atBrList(); });
    $("at-brq").addEventListener("focus", () => { S.brOpen = true; atBrList(); });
    $("at-svb").addEventListener("click", () => { const n = ($("at-svn").value || "").trim() || `Set ${S.sets.length + 1}`; S.sets = S.sets.filter((x) => x.n !== n); S.sets.push({ n, f: JSON.parse(JSON.stringify(S.f)) }); if (S.sets.length > 20) S.sets.shift(); LS.set("atSets", S.sets); $("at-svn").value = ""; atSetsR(); toast("Filtre seti kaydedildi ✓", 1500); });
    atSync();
  }
  function atSync() {
    const S = atS(), f = S.f;
    document.querySelectorAll("#at-mode [data-atm]").forEach((b) => b.classList.toggle("active", b.dataset.atm === f.mode));
    const bw = $("at-brw"); if (bw) bw.hidden = f.mode !== "sel";
    const isN = f.mode === "net";   // v1.26.1
    atIlkCtl(isN);   // v1.27.1
    document.querySelectorAll("#at-ctl .at-fbr").forEach((l) => (l.hidden = isN)); document.querySelectorAll("#at-ctl .at-fnet").forEach((l) => (l.hidden = !isN));
    const sdl = $("at-side") && $("at-side").closest("label"); if (sdl) sdl.hidden = isN;
    if ($("at-side")) $("at-side").value = f.side || "";
    if ($("at-du")) $("at-du").value = f.durum || "";
    document.querySelectorAll("[data-atf]").forEach((i) => { const v = f[i.dataset.atf][+i.dataset.ati]; if (i.value !== String(v ?? "")) i.value = v ?? ""; });
    document.querySelectorAll("[data-atp]").forEach((b) => b.classList.toggle("on", b.dataset.atp === S.preset));
    const n = (isN ? AT_FN : AT_FL).filter(([k]) => f[k][0] !== "" || f[k][1] !== "").length + (f.side && !isN ? 1 : 0) + (f.durum ? 1 : 0) + (isN ? (f.ilkd ? 1 : 0) + (f.ilkp !== "" && f.ilkp != null ? 1 : 0) + (f.ilkl !== "" && f.ilkl != null ? 1 : 0) : 0);
    const fnb = $("at-fn"); if (fnb) fnb.textContent = n ? `(${n} aktif)` : "";
    const ch = $("at-chips"); if (ch) ch.innerHTML = (f.brs || []).map((b) => `<button type="button" class="at-chip" data-atrm="${esc(b)}">${esc(brName(b))} ✕</button>`).join("") || `<span class="muted sm">Kurum seçilmedi — aşağıdan arayıp seçin</span>`;
    atSetsR();
  }
  function atIlkCtl(isN) {   // v1.27.1
    const el = $("at-ilk"); if (!el) return; el.hidden = !isN; if (!isN) return;
    const f = atS().f, P = f.per ? atPerS()[f.per] : null, cs = f.ilkc || AT_IN;
    const h = `<div class="at-ilr"><span class="at-ill">Dönem</span><div class="seg sm at-per">${[["", "SEANS (seçili gün)"], ["weekly", "HAFTALIK"], ["monthly", "AYLIK"]].map(([v, l]) => `<button type="button" data-atper="${v}" class="${(f.per || "") === v ? "active" : ""}">${l}</button>`).join("")}</div></div>
      <div class="at-ilr"><span class="at-ill">İLK N NET PGÇ</span><select class="pill-select" data-atik="ilkn">${AT_IN.map((n) => `<option value="${n}" ${String(f.ilkn) === n ? "selected" : ""}>İlk ${n}</option>`).join("")}</select>
        <select class="pill-select" data-atik="ilkd"><option value="" ${!f.ilkd ? "selected" : ""}>Yön: tümü</option><option value="a" ${f.ilkd === "a" ? "selected" : ""}>Net ALAN</option><option value="s" ${f.ilkd === "s" ? "selected" : ""}>Net SATAN</option></select>
        <label class="at-ilm"><span>min %</span><input type="text" inputmode="decimal" data-atik="ilkp" value="${esc(f.ilkp ?? "")}" placeholder="örn. 50"/></label>
        <label class="at-ilm"><span>min net lot</span><input type="text" inputmode="decimal" data-atik="ilkl" value="${esc(f.ilkl ?? "")}" placeholder="—"/></label>
        <span class="at-pci" title="İLK N: ALAN = ilk N net alıcının net lot toplamı, SATAN = ilk N net satıcının |net lot| toplamı, NET = ALAN − SATAN. % = |ALAN − SATAN| ÷ max(ALAN, SATAN) × 100 — örn. ALAN 100.000, SATAN 50.000 → %50 Alan. AKD sekmesi İLK N NET PGÇ kartı ile birebir aynı.">ⓘ % = |A − S| ÷ max(A, S)</span></div>
      <div class="at-ilr"><span class="at-ill">Sütunlar</span>${AT_IN.map((n) => `<button type="button" class="fm-tf ${cs.includes(n) ? "on" : ""}" data-atic="${n}">İlk ${n}</button>`).join("")}${f.per ? `<span class="muted sm at-pst">${P && P.d ? (P.d.running ? `⏳ ${esc(P.d.label)} AKD hazırlanıyor… ${fN(P.d.done)}/${fN(P.d.total)}` : `${esc(P.d.label)} · ${fmtYmd(P.d.from)} – ${fmtYmd(P.d.to)}${P.d.fin_s ? " · " + esc(P.d.fin_s) : ""}${P.d.miss ? ` · ${fN(P.d.miss)} hisse yanıtsız` : ""}`) : P && P.err ? "Alınamadı: " + esc(P.err) : "Yükleniyor…"}</span>` : ""}</div>`;
    if (el._h !== h) { const ae = document.activeElement, ak = ae && ae.dataset ? ae.dataset.atik : null; el.innerHTML = h; el._h = h; if (ak === "ilkp" || ak === "ilkl") { const i = el.querySelector(`[data-atik="${ak}"]`); if (i) { i.focus(); const L = i.value.length; try { i.setSelectionRange(L, L); } catch (e) {} } } }
  }
  function atSetsR() { const S = atS(), el = $("at-sets"); if (!el) return; el.innerHTML = S.sets.length ? `<span class="muted sm">Kayıtlı setler:</span>` + S.sets.map((x, i) => `<span class="at-set"><button type="button" class="ozp-chip" data-atset="${i}">${esc(x.n)}</button><button type="button" class="at-x" data-atdel="${i}" aria-label="Sil">✕</button></span>`).join("") : ""; }
  function atBrList() {
    const S = atS(), el = $("at-brl"); if (!el) return;
    const L = S.blist || [];
    if (!S.brOpen) { el.hidden = true; return; }
    const q = trUpper(S.brq || "").trim(), sel = new Set(S.f.brs || []);
    const m = L.filter((b) => !q || trUpper(brName(b)).includes(q) || trUpper(b).includes(q)).slice(0, 80);
    el.hidden = false;
    el.innerHTML = m.map((b) => `<button type="button" class="at-bri ${sel.has(b) ? "on" : ""}" data-atbr="${esc(b)}">${brIcon(b)}<span>${esc(brName(b))}</span>${sel.has(b) ? "<b>✓</b>" : ""}</button>`).join("") || `<div class="muted sm">Eşleşen kurum yok</div>`;
  }
  function atRender() {
    const S = atS(), d = S.d;
    atFixSort(); atSync();
    const ds = $("at-date");
    if (ds && d && d.dates) { const h = d.dates.map((x) => `<option value="${x.d}" ${x.d === d.date ? "selected" : ""}>${esc(x.l)}${x.cur ? " · güncel" : ""}</option>`).join(""); if (ds._h !== h) { ds.innerHTML = h; ds._h = h; } }
    const sub = $("at-sub"); if (sub && d) sub.textContent = `${d.date_label}${d.cur ? " · güncel AKD" : ""} · ${fN(d.stocks.length)} hisse · ${fN(d.rows.length)} kurum satırı`;
    const head = $("at-head"), body = $("at-body"), more = $("at-more"), note = $("at-note");
    const isN = S.f.mode === "net";   // v1.26.1 TÜM AKD NET
    const C = isN ? atCN() : [["s", "HİSSE", "l sticky"], ["br", "KURUM", "l"], ["nl", "NET LOT"], ["ntl", "NET ₺"], ["np", "NET %"], ["bgp", "ALIŞ PAYI %"], ["sgp", "SATIŞ PAYI %"], ["aa", "AKTİF ALIŞ %"], ["abl", "AKTİF ALIŞ LOT"], ["abtl", "AKTİF ALIŞ ₺"], ["as", "AKTİF SATIŞ %"], ["asl", "AKTİF SATIŞ LOT"], ["co", "MALİYET"], ["p", "SON"], ["kz", "K/Z ₺"], ["kzp", "K/Z %"], ["tp", "HACİM PAYI"], ["gd", "GÜNLÜK %"], ["du", "DURUM", "l"], ["nb", "ALICI/SATICI"], ["b3", "İLK 3 %"]];
    const hh = `<tr>${C.map(([k, l, c]) => `<th data-atsort="${k}" class="${c || ""} ${S.sort === k ? "sorted" + (S.dir > 0 ? " asc" : "") : ""}">${l}</th>`).join("")}</tr>`;
    if (head && head._h !== hh) { head.innerHTML = hh; head._h = hh; }
    if (!d) { setH(body, `<tr><td colspan="18" class="empty">Yükleniyor…</td></tr>`); return; }
    if (isN) { atRenderN(S, d, body, more, note); atWatchR(); return; }
    const R = atFilter();
    const show = R.slice(0, S.n);
    const pct = (v) => (isNum(v) ? "%" + nf(1).format(v) : "—");
    setH(body, show.map((r) => `<tr data-atsym="${esc(r.s)}"><td class="l sticky"><b>${esc(r.s)}</b></td><td class="l at-brc" data-k5br="${esc(r.br)}">${esc(brName(r.br))}</td><td class="${cls(r.nl)}">${r.nl > 0 ? "+" : ""}${fN(r.nl)}</td><td class="${cls(r.ntl)}">${v6stl(r.ntl)}</td><td class="${cls(r.np)}"><b>${isNum(r.np) ? (r.np > 0 ? "+" : r.np < 0 ? "−" : "") + "%" + nf(1).format(Math.abs(r.np)) : "—"}</b></td>
      <td>${pct(r.bgp)}</td><td>${pct(r.sgp)}</td>${atAkTd(r.aa, r.aat, 1)}${atLotTd(r.abl, 1)}${atTlTd(r.abtl)}${atAkTd(r.as, null, -1)}${atLotTd(r.asl, -1)}<td>${kmP(r.co)}</td><td>${kmP(r.p)}</td><td class="${cls(r.kz)}">${v6stl(r.kz)}</td><td class="${cls(r.kzp)}">${v6pc(r.kzp)}</td><td>${pct(r.tp)}</td><td class="${cls(r.gd)}">${v6pc(r.gd)}</td>
      <td class="l"><span class="at-du ${r.du === "TOPLAMA" ? "pos" : r.du === "DAĞITIM" ? "neg" : "muted"}">${esc(r.du)}</span></td><td>${fN(r.nb)}/${fN(r.ns)}</td><td>${pct(r.b3)}</td></tr>`).join("") || `<tr><td colspan="18" class="empty">${S.f.mode === "sel" && !(S.f.brs || []).length ? "KURUM SEÇ: yukarıdan en az bir kurum seçin" : "Filtrelere uyan satır yok"}</td></tr>`);
    if (more) { more.hidden = R.length <= S.n; more.textContent = `Daha fazla göster (+${Math.min(100, R.length - S.n)} / ${fN(R.length - S.n)})`; }
    if (note) note.textContent = `${fN(R.length)} satır · ${S.f.mode === "best" ? "hisse başına en büyük (net ₺) eşleşen kurum" : S.f.mode === "sel" ? `seçili kurum(lar): ${(S.f.brs || []).map(brName).join(", ") || "—"}` : "tüm kurum satırları"} · Kaynak: ${d.src}${d.ts_s ? " · AKD " + d.ts_s : ""} · hesap ${fN(d.ms)} ms.${d.aktif && d.aktif.note ? " " + d.aktif.note + "." : ""} Satıra dokunun → hissenin AKD sekmesi.`;
    atWatchR();
  }
  function atFixSort() {   // v1.26.1 mod değişince geçersiz sıralama anahtarı → mod varsayılanı
    const S = atS(), N = S.f.mode === "net", ks = N ? AT_CN.map((x) => x[0]).concat(["i3n", "i3p", "i5n", "i5p", "i10n", "i10p"]) : ["s", "br", "nl", "ntl", "np", "bgp", "sgp", "aa", "abl", "abtl", "as", "asl", "co", "p", "kz", "kzp", "tp", "gd", "du", "nb", "b3"];
    if (!ks.includes(S.sort)) { S.sort = N ? "tnb" : "ntl"; S.dir = -1; }
  }
  function atRenderN(S, d, body, more, note) {
    const f = S.f, PX = f.per ? atPerS()[f.per] : null;   // v1.27.1 dönem (HAFTALIK/AYLIK)
    if (f.per && (!PX || !PX.d) && !(PX && PX.busy)) atPerLoad(f.per, false);
    if (f.per && !(PX && PX.stk && PX.stk.length)) { setH(body, `<tr><td colspan="16" class="empty">${PX && PX.err ? "Dönem AKD alınamadı: " + esc(PX.err) : `⏳ ${f.per === "weekly" ? "HAFTALIK" : "AYLIK"} AKD tüm hisseler için İdealData'dan hazırlanıyor${PX && PX.d ? ` (${fN(PX.d.done)}/${fN(PX.d.total)})` : ""}… ilk seferde birkaç dakika sürer, sonra önbellekten gelir.`}</td></tr>`); if (more) more.hidden = true; if (note) note.textContent = PX && PX.d ? PX.d.src : ""; return; }
    const R = atFilterN(), show = R.slice(0, S.n), sel = AT_IN.filter((n) => (f.ilkc || AT_IN).includes(n));
    const pct = (v) => (isNum(v) ? "%" + nf(1).format(v) : "—");
    setH(body, show.map((r) => `<tr data-atsym="${esc(r.s)}"><td class="l sticky"><b>${esc(r.s)}</b></td>${sel.map((n) => atIlkTd(r, n)).join("")}<td class="pos" title="Net satıcılar toplamı: ${fN(r.tns)}">+${r.tnb >= 1e7 ? fShort(r.tnb) : fN(r.tnb)}</td><td>${isNum(r.tntl) ? fShort(r.tntl) + " ₺" : "—"}</td>
      <td class="${(r.tnp || 0) >= 30 ? "pos at-akh" : ""}"><b>${pct(r.tnp)}</b></td><td title="${fN(r.vol)}">${fShort(r.vol)}</td><td class="pos">${pct(r.b3)}</td><td class="neg">${pct(r.s3)}</td><td>${fN(r.nb)}/${fN(r.ns)}</td>
      <td class="l"><span class="at-du ${r.du === "TOPLAMA" ? "pos" : r.du === "DAĞITIM" ? "neg" : "muted"}">${esc(r.du)}</span></td>${atAkTd(r.sab, null, 1)}<td>${kmP(r.p)}</td><td class="${cls(r.gd)}">${v6pc(r.gd)}</td></tr>`).join("") || `<tr><td colspan="15" class="empty">Filtrelere uyan hisse yok${atNum(f.ilkp) != null ? ` — İlk ${esc(String(f.ilkn))} için min %${esc(String(f.ilkp))} eşiğini düşürmeyi deneyin (ör. %30)` : ""}</td></tr>`);
    if (more) { more.hidden = R.length <= S.n; more.textContent = `Daha fazla göster (+${Math.min(100, R.length - S.n)} / ${fN(R.length - S.n)})`; }
    const ilkNote = ` · İLK N (AKD sekmesi İLK N NET PGÇ kartı ile aynı): ALAN = ilk N net alıcının net lot toplamı, SATAN = ilk N net satıcının, NET = ALAN − SATAN; % = |ALAN − SATAN| ÷ max(ALAN, SATAN) × 100 (örn. 100.000 / 50.000 → %50 Alan)${f.per && PX && PX.d ? ` · Dönem: ${PX.d.src}. ${PX.d.note}` : ""}`;
    if (note) note.textContent = `${fN(R.length)} hisse${ilkNote} · TÜM AKD NET: net lot = net alıcıların toplam net lotu (= net satıcıların toplamı, AKD sekmesi TOPLAM ile aynı); net % = net lot ÷ hissenin toplam işlem lotu (AKD Σ alış lotu); aktif alış % = aktif alış lotu ÷ (aktif alış + aktif satış), Seans İşlem Akışı ile aynı · Kaynak: ${d.src}${d.ts_s ? " · AKD " + d.ts_s : ""}. Satıra dokunun → hissenin AKD sekmesi.`;
  }
  function atLotTd(v, sd) { return isNum(v) ? `<td class="${v > 0 ? (sd > 0 ? "pos" : "neg") : "muted"}" title="${fN(v)} lot">${v >= 1e7 ? fShort(v) : fN(v)}</td>` : `<td class="muted">—</td>`; }
  function atTlTd(v) { return isNum(v) ? `<td title="${fN(v)} ₺">${v ? fShort(v) + " ₺" : "0"}</td>` : `<td class="muted">—</td>`; }
  function atAkTd(v, vt, sd) {   // v1.26.1 aktif alış/satış % hücresi (yüksek aktif alış yeşil, yüksek aktif satış kırmızı; işlem kaydı yoksa —)
    if (!isNum(v)) return `<td class="muted" title="İşlem kaydı yok / bu tarafta işlem yok">—</td>`;
    const c = v >= 70 ? (sd > 0 ? "pos at-akh" : "neg at-akh") : v >= 50 ? (sd > 0 ? "pos" : "neg") : v < 30 ? "muted" : "";
    return `<td class="${c}" title="${sd > 0 ? "Alış lotunun" : "Satış lotunun"} %${nf(1).format(v)}'i aktif${isNum(vt) ? " · ₺ bazında %" + nf(1).format(vt) : ""}">%${nf(1).format(v)}${isNum(vt) ? `<small class="at-akt">₺ %${nf(1).format(vt)}</small>` : ""}</td>`;
  }
  function atApplyPreset(k) {
    const S = atS();
    if (k === "reset") { const brs = S.f.brs, md = S.f.mode === "sel" || S.f.mode === "net" ? S.f.mode : "best", per = S.f.per, ic = S.f.ilkc; S.f = atDefF(); S.f.brs = brs; S.f.mode = md; S.f.per = per || ""; S.f.ilkc = ic || AT_IN.slice(); S.preset = ""; }
    else { const P = AT_PRE.find((x) => x[0] === k); if (!P) return; const keep = { q: S.f.q, brs: S.f.brs, mode: P[3] === "net" ? "net" : S.f.mode === "sel" ? "sel" : P[3], per: S.f.per || "", ilkc: (S.f.ilkc || AT_IN).slice() }; S.f = Object.assign(atDefF(), JSON.parse(JSON.stringify(P[2])), keep); S.preset = k; S.sort = P[4] || (/np|ntl/.test(JSON.stringify(P[2])) || k === "top" || k === "dag" ? "ntl" : "kz"); S.dir = P[5] != null ? P[5] : !P[4] && P[2].side === "sell" ? 1 : -1; if (P[2].ilkn && !S.f.ilkc.includes(P[2].ilkn)) S.f.ilkc = AT_IN.filter((n) => n === P[2].ilkn || S.f.ilkc.includes(n)); }
    S.n = 100; atSave(); atRender();
  }
  document.addEventListener("click", (e) => {
    if (!v6ok() || st.view !== "akdt") return;
    const S = atS();
    const m = e.target.closest("[data-atm]"); if (m) { S.f.mode = m.dataset.atm; S.n = 100; atSave(); if (S.f.mode === "sel") { S.brOpen = true; atBrList(); } atRender(); return; }
    const p = e.target.closest("[data-atp]"); if (p) { atApplyPreset(p.dataset.atp); return; }
    const pe = e.target.closest("[data-atper]"); if (pe) { S.f.per = pe.dataset.atper; S.n = 100; atSave(); if (S.f.per) atPerLoad(S.f.per, false); atRender(); return; }   // v1.27.1
    const ic = e.target.closest("[data-atic]"); if (ic) { const n = ic.dataset.atic, L = (S.f.ilkc || AT_IN).slice(); const i = L.indexOf(n); if (i >= 0) { if (L.length > 1) L.splice(i, 1); } else L.push(n); S.f.ilkc = AT_IN.filter((x) => L.includes(x)); atSave(); atRender(); return; }
    const br = e.target.closest("[data-atbr]"); if (br) { const b = br.dataset.atbr, L = S.f.brs || (S.f.brs = []); const i = L.indexOf(b); if (i >= 0) L.splice(i, 1); else L.push(b); S.f.mode = "sel"; S.n = 100; atSave(); atBrList(); atRender(); return; }
    const rm = e.target.closest("[data-atrm]"); if (rm) { S.f.brs = (S.f.brs || []).filter((x) => x !== rm.dataset.atrm); atSave(); atBrList(); atRender(); return; }
    const so = e.target.closest("[data-atsort]"); if (so) { const k = so.dataset.atsort; if (S.sort === k) S.dir *= -1; else { S.sort = k; S.dir = ["s", "br", "du"].includes(k) ? 1 : -1; } atRender(); return; }
    const st1 = e.target.closest("[data-atset]"); if (st1) { const x = S.sets[+st1.dataset.atset]; if (x) { S.f = Object.assign(atDefF(), JSON.parse(JSON.stringify(x.f))); S.preset = ""; S.n = 100; atSave(); atRender(); toast(`"${x.n}" uygulandı`, 1200); } return; }
    const dl = e.target.closest("[data-atdel]"); if (dl) { S.sets.splice(+dl.dataset.atdel, 1); LS.set("atSets", S.sets); atSetsR(); return; }
    if (e.target.id === "at-more") { S.n += 100; atRender(); return; }
    const wa = e.target.closest("[data-atwadd]"); if (wa) { atWatchAdd(); return; }
    const wd = e.target.closest("[data-atwdel]"); if (wd) { const W = (S.watch && S.watch.rules) || []; atWatchSet(W.filter((r) => r.id !== wd.dataset.atwdel)); return; }
    const row = e.target.closest("[data-atsym]"); if (row) { if (S.f.mode === "net") { st.akdTopN = AT_IN.includes(String(S.f.ilkn)) ? +S.f.ilkn : st.akdTopN; if (S.f.per) st.akdPeriod = S.f.per; else if (S.d && !S.d.cur && S.d.date) { st.akdPeriod = "custom"; st.akdDate = `${S.d.date.slice(0, 4)}-${S.d.date.slice(4, 6)}-${S.d.date.slice(6, 8)}`; } else st.akdPeriod = "daily"; } st.tab = "akd"; LS.set("tab", "akd"); openStock(row.dataset.atsym); return; }   // v1.27.1 AKD sekmesi aynı dönem + İLK N
    if (!e.target.closest("#at-brw")) { if (S.brOpen) { S.brOpen = false; atBrList(); } }
  });
  document.addEventListener("change", (e) => {   // v1.27.1 İLK N seçimleri
    const i = e.target.closest("#at-ilk [data-atik]"); if (!i || !v6ok()) return;
    const S = atS(); S.f[i.dataset.atik] = i.value; S.preset = ""; S.n = 100; atSave(); atRender();
  });
  document.addEventListener("input", (e) => {
    const i = e.target.closest('#at-ilk input[data-atik]'); if (!i || !v6ok()) return;
    const S = atS(); S.f[i.dataset.atik] = i.value; S.preset = ""; S.n = 100; atSave(); clearTimeout(S._ti); S._ti = setTimeout(atRender, 300);
  });
  async function atWatchLoad() { const S = atS(); try { S.watch = await api("/api/akd/tarama/watch", { timeout: 10000 }); } catch (e) { S.watch = S.watch || { rules: [], err: String(e.message || e) }; } atWatchR(); }
  async function atWatchSet(rules) { const S = atS(); try { S.watch = await api("/api/akd/tarama/watch", { method: "POST", body: JSON.stringify({ rules }), headers: { "Content-Type": "application/json" }, timeout: 15000 }); toast("Bildirim kuralları kaydedildi ✓", 1500); } catch (e) { toast("Kaydedilemedi: " + (e.message || e), 3000); } atWatchR(); }
  function atWatchAdd() {
    const S = atS(), brs = (S.f.brs || []).slice();
    if (!brs.length) { toast("Önce KURUM SEÇ ile en az bir kurum seçin", 2500); return; }
    const np = atNum($("at-wnp").value) ?? 20, tl = atNum($("at-wtl").value) ?? 1000000, side = $("at-wsd").value === "sell" ? "sell" : "buy", aa = atNum(($("at-waa") || {}).value) ?? 0;
    const W = ((S.watch && S.watch.rules) || []).slice();
    W.push({ id: "r" + Date.now().toString(36), brokers: brs, min_np: Math.abs(np), min_tl: Math.abs(tl), side, min_aa: Math.max(0, Math.min(100, Math.abs(aa))), name: brs.map(brName).join(", ").slice(0, 60) });
    atWatchSet(W.slice(-10));
  }
  function atWatchR() {
    const el = $("at-nt"); if (!el) return;
    const S = atS(), W = (S.watch && S.watch.rules) || [];
    const rl = W.map((r) => `<div class="at-wr"><span><b>${esc(r.brokers.map(brName).join(", "))}</b> <small>${r.side === "sell" ? "net SATICI" : "net ALICI"} · net % ≥${nf(1).format(r.min_np)} · ≥${fShort(r.min_tl)} ₺${r.min_aa ? ` · aktif ${r.side === "sell" ? "satış" : "alış"} % ≥${nf(1).format(r.min_aa)}` : ""}</small></span><button type="button" class="at-x" data-atwdel="${esc(r.id)}" aria-label="Sil">✕</button></div>`).join("");
    const h = `<section class="card at-ntc"><div class="card-h"><span class="card-title">BİLDİRİM · AKD TARAMASI</span><button type="button" class="btn-ghost sm nf-lnk" data-nflink="ayar">🔔 Tüm bildirim ayarları</button></div>
      ${NT.akd_tarama ? ntRow("akd_tarama", false) : ""}<div class="km-ostest"><button type="button" class="btn-ghost sm" data-ostest="${esc(OS_FEAT.akd_tarama || "AKD Taraması")}">✈️ Telegram Test · AKD Taraması</button></div>
      <div class="mk-sub">KURALLAR (seçili kurum bir hisseye eşik üstü girince)</div>${rl || `<div class="muted sm">Henüz kural yok.</div>`}
      <div class="at-wf"><span class="muted sm">Seçili kurum(lar): <b>${esc((S.f.brs || []).map(brName).join(", ") || "— (KURUM SEÇ)")}</b></span>
        <select id="at-wsd" class="pill-select"><option value="buy">net alıcı</option><option value="sell">net satıcı</option></select>
        <label>net % ≥ <input type="text" inputmode="decimal" id="at-wnp" value="20" /></label><label>≥ ₺ <input type="text" inputmode="decimal" id="at-wtl" value="1000000" /></label><label title="Boş = koşul yok. Alıcı kuralında aktif alış %, satıcı kuralında aktif satış %">aktif % ≥ <input type="text" inputmode="decimal" id="at-waa" value="" placeholder="—" /></label>
        <button type="button" class="btn-ghost sm" data-atwadd="1">＋ Kural ekle</button></div>
      <div class="src-note">${esc((S.watch && S.watch.note) || "Seans içinde ~60 sn'de bir sunucuda kontrol edilir.")} Hisse+kurum+kural başına günde 1 bildirim, saatte en çok 30. Bildirim modu (KAPALI / GÖRÜNTÜLE / BİLDİRİM) yukarıdaki satırdan.</div></section>`;
    if (el._wh !== h || !el.firstChild) { const keep = { np: $("at-wnp") && $("at-wnp").value, tl: $("at-wtl") && $("at-wtl").value, sd: $("at-wsd") && $("at-wsd").value, aa: $("at-waa") && $("at-waa").value }; el.innerHTML = h; el._wh = h; if (keep.np != null) { $("at-wnp").value = keep.np; $("at-wtl").value = keep.tl; $("at-wsd").value = keep.sd; if ($("at-waa")) $("at-waa").value = keep.aa || ""; } }
  }

  // ===================================================================== v1.26.2 ==
  // ---- (1) KEŞFET › AKTİF İŞLEM TARAMASI (KURUM) — /api/akd/tarama ile AYNI veri (aktif alış % = AKD Taraması sütunu)
  // ---- (2) Kurum adına dokun → en çok aktif alış yaptığı ilk 5 hisse (ayar, varsayılan KAPALI; yakalama aşamasında, KAPALIyken hemen döner)
  // ---- (3) AKD sekmesi aktif sütunları / EN ÇOK AKTİF ALAN KURUMLAR / TAHTACI SİNYALİ (akpHtml içinde) · Özet tahtacı satırı
  var AKK;
  function akkS() {
    if (!AKK) AKK = { d: null, date: "", busy: false, last: 0, view: LS.get("akkV", "br") || "br", f: Object.assign({ min_tl: "1000000", min_lot: "", aa: ["", ""], net: false, q: "", bmin: "10000000", br: "", tt: false, ttg: false }, LS.get("akkF", {}) || {}), sort: "", dir: -1, n: 100, brq: "", brOpen: false, watch: null, trw: null };
    return AKK;
  }
  function akkSave() { const S = akkS(); LS.set("akkF", S.f); LS.set("akkV", S.view); }
  function akkRows(d) {
    if (!d || !d.cols || !d.rows) return [];
    if (d._akk) return d._akk;
    const ci = {}, sc = {}; d.cols.rows.forEach((k, i) => (ci[k] = i)); d.cols.stocks.forEach((k, i) => (sc[k] = i));
    const B = d.brokers, Sk = d.stocks, out = [];
    for (const r of d.rows) {
      const abl = r[ci.abl]; if (!isNum(abl)) continue;
      const s = Sk[r[ci.si]];
      let tbtl = ci.tbtl != null ? r[ci.tbtl] : null, tbl = ci.tbl != null ? r[ci.tbl] : null;
      const aat = r[ci.aat], aa = r[ci.aa];
      if (!isNum(tbtl) && isNum(aat) && aat > 0) tbtl = r[ci.abtl] / (aat / 100);   // eski sunucu yanıtı için yedek
      if (!isNum(tbl) && isNum(aa) && aa > 0) tbl = abl / (aa / 100);
      out.push({ s: s[sc.s], p: s[sc.p], gd: s[sc.gd], br: B[r[ci.bi]], nl: r[ci.nl], co: r[ci.co], aa, aat, abl, abtl: r[ci.abtl], tbl, tbtl, as: r[ci.as], asl: r[ci.asl],
        np: r[ci.np], rb: ci.rb != null ? r[ci.rb] : null, rs: ci.rs != null ? r[ci.rs] : null, wb: ci.wb != null ? r[ci.wb] : null, tt: ci.tt != null ? r[ci.tt] || 0 : 0,
        tv: sc.tv != null ? s[sc.tv] : null, tvh: sc.tvh != null ? s[sc.tvh] : null });   // v1.26.3
    }
    d._akk = out; return out;
  }
  function akkFilt(S, agg) {
    const f = S.f, R = akkRows(S.d);
    const mt = atNum(f.min_tl), ml = atNum(f.min_lot), lo = atNum(f.aa[0]), hi = atNum(f.aa[1]);
    const q = trUpper(f.q || "").trim();
    return R.filter((r) => {
      if (!isNum(r.aa)) return false;
      if (mt != null && !((r.tbtl || 0) >= mt)) return false;
      if (ml != null && !((r.tbl || 0) >= ml)) return false;
      if (f.net && !(r.nl > 0)) return false;
      if (f.tt && !(r.tt > 0)) return false;          // v1.26.3 🚂 TAVAN TRENİ ön ayarı
      if (f.tt && f.ttg && !(r.tt >= 2)) return false;
      if (!agg) {
        if (lo != null && r.aa < lo) return false;
        if (hi != null && r.aa > hi) return false;
        if (S.view === "one" && r.br !== f.br) return false;
        if (q && !(r.s.includes(q) || trUpper(brName(r.br)).includes(q) || trUpper(r.br).includes(q))) return false;
      }
      return true;
    });
  }
  function akkAgg(S) {
    const m = new Map();
    for (const r of akkFilt(S, true)) {
      let x = m.get(r.br); if (!x) m.set(r.br, (x = { br: r.br, n: 0, abtl: 0, tbtl: 0, abl: 0, tbl: 0, nn: 0, top: null, n1: 0, s1: 0, ntt: 0, ntg: 0 }));
      x.n++; x.abtl += r.abtl || 0; x.tbtl += r.tbtl || 0; x.abl += r.abl || 0; x.tbl += r.tbl || 0; if (r.nl > 0) x.nn++;
      if (r.rb === 1) x.n1++; if (r.rs === 1) x.s1++; if (r.tt > 0) { x.ntt++; if (r.tt >= 2) x.ntg++; }   // v1.26.3
      if (!x.top || (r.abtl || 0) > (x.top.abtl || 0)) x.top = r;
    }
    const f = S.f, bm = atNum(f.bmin), lo = atNum(f.aa[0]), hi = atNum(f.aa[1]), q = trUpper(f.q || "").trim(), out = [];
    for (const x of m.values()) {
      x.wa = x.tbtl > 0 ? (x.abtl / x.tbtl) * 100 : null; x.wal = x.tbl > 0 ? (x.abl / x.tbl) * 100 : null;
      if (bm != null && x.tbtl < bm) continue;
      if (lo != null && !(x.wa >= lo)) continue;
      if (hi != null && !(x.wa <= hi)) continue;
      if (q && !(trUpper(brName(x.br)).includes(q) || trUpper(x.br).includes(q))) continue;
      out.push(x);
    }
    return out;
  }
  function akkTop5(d, br, mt) {
    const m = mt != null ? mt : (atNum(akkS().f.min_tl) ?? 1e6);
    return akkRows(d).filter((r) => r.br === br && isNum(r.aa) && (r.tbtl || 0) >= m).sort((a, b) => b.aa - a.aa || (b.abtl || 0) - (a.abtl || 0)).slice(0, 5);
  }
  function akkOpen() { if (!v6ok()) return; akkBuild(); akkLoad(true); akkWatchLoad(); trnWatchLoad(); }
  async function akkLoad(force) {
    const S = akkS();
    if (S.busy) return;
    if (!force && Date.now() - S.last < 60000) return;
    S.busy = true; S.last = Date.now();
    const b = $("akk-ref"); if (b) b.classList.add("spin");
    try {
      const tok = S.d && S.d.tok && (S.d.date === S.date || !S.date) ? `&tok=${encodeURIComponent(S.d.tok)}` : "";
      const d = await api(`/api/akd/tarama?date=${encodeURIComponent(S.date || "")}${force ? "" : tok}`, { timeout: 60000 });
      if (d && d.same) return;
      S.d = d; akkRender();
    } catch (e) {
      if (!S.d) setH($("akk-body"), `<tr><td colspan="12" class="empty">Aktif işlem taraması alınamadı (${esc(e.message || e)}) — ↻ ile yeniden deneyin</td></tr>`);
    } finally { S.busy = false; const b2 = $("akk-ref"); if (b2) b2.classList.remove("spin"); }
  }
  setInterval(() => { try { if (v6ok() && st.view === "akk" && !document.hidden && AKK && AKK.d && AKK.d.cur) akkLoad(false); } catch (e) {} }, 10000);
  function akkBuild() {
    const c = $("akk-ctl"); if (!c || c._b) return;
    c._b = 1;
    $("akk-info").innerHTML = `<details class="card at-info"><summary><b>ⓘ Aktif İşlem Taraması (KURUM) nedir?</b> <small class="muted">ne · nasıl kullanılır · dikkat</small></summary>
      <p><b>Ne:</b> Hangi aracı kurum, hangi hisselerde alımlarını <b>AKTİF</b> (piyasa emriyle, satıcının bekleyen emrine vurarak) yaptı? Kaynak AKD Taraması ile aynı (aynı istek, aynı işlem kaydı): satır başına <b>aktif alış %</b> = kurumun o hissedeki aktif alış lotu ÷ tüm alış lotu — AKD Taraması'ndaki "AKTİF ALIŞ %" sütunuyla birebir aynı sayı.</p>
      <p><b>Görünümler:</b> <i>KURUM BAZINDA</i>: her kurum için işlem yaptığı hisse sayısı, <b>ağırlıklı aktif alış %</b> (₺ bazında: Σ aktif alış ₺ ÷ Σ alış ₺; küçük yazı lot bazında), toplam aktif alış ₺ ve en çok aktif aldığı hisse. <i>KURUM × HİSSE</i>: tüm kurum-hisse satırları aktif alış %'ye göre. <i>KURUM SEÇ</i>: aradığınız tek kurumun (örn. Yapı Kredi) tüm hisseleri. Başlığa dokunup sıralayın; kurum satırına dokunun → o kurumun hisseleri; hisse satırına dokunun → hissenin AKD sekmesi.</p>
      <p><b>Nasıl kullanılır:</b> Varsayılan filtre satır başına en az 1 Mn ₺ alış (küçük alışlarda tek işlem %0/%100 yapar), kurum bazında en az 10 Mn ₺ toplam alış (küçük kurumlar listeyi domine etmesin). "Yalnız net alıcı" ile kurumun net alıcı olduğu hisselere daraltın. Yüksek ağırlıklı aktif % (örn. %70+) = kurum genel olarak fiyatı kovalıyor; düşük (%30 altı) = pasif, bekleyen emirle topluyor. Bildirim: kurum bir hissede eşik ₺ üstünde ve eşik aktif % üstünde alınca (varsayılan KAPALI).</p>
      <p><b>🚂 TAVAN TRENİ:</b> Tavana götürme niyetindeki kurum = hissenin <b>en büyük balinası</b> (AKD Alış #1 ya da en büyük alış lotu), net alıcılar arasında çok güçlü (<b>net payı ≥ %30</b> — AKD sekmesi DAĞILIM %) ve net alımının çoğunu <b>AKTİF</b> (piyasa emriyle) yapmış (<b>aktif alış ≥ %65</b>), en az <b>5 Mn ₺</b> aktif alışla. Açgözlü alıcı: ralli trenini çekiyor / çekti. <b>GÜÇLÜ</b> = AKD Alış #1 + ≥10 Mn ₺ aktif alış; <b>ORTA</b> = diğer tüm koşullar sağlanmış. Satırdaki ✓/✗ = koşullar (#1/🐋 · %30 · A%65 · 5 Mn₺). "🚂 TAVAN TRENİ" düğmesi ön ayarı açar (KURUM × HİSSE, derece sırası, günün sağlama özeti). Aynı sinyal hissenin AKD ANALİZİ ve Özet yorumunda TAHTACI SİNYALİ ile birleşik görünür; bildirimi aşağıda (varsayılan KAPALI).</p>
      <p><b>Dikkat:</b> Aktif/pasif ayrımı işlem kaydının agresör tarafıdır; açılış/kapanış seansı (tek fiyat) eşleşmeleri ne aktif ne pasiftir, paydada kalır. Kurum toplamı müşterilerin toplamıdır (Midas gibi bireysel ağırlıklı kurumlarda çok sayıda küçük yatırımcı). Geçmiş günlerde yalnız işlem kaydı olan günler hesaplanır. Bu bir tarama aracıdır, yatırım tavsiyesi değildir.</p></details>`;
    c.innerHTML = `<div class="at-r1"><select id="akk-date" class="pill-select" aria-label="Seans"></select><input type="search" class="ak-search" id="akk-q" placeholder="Hisse / kurum ara..." autocomplete="off" spellcheck="false" /><button type="button" class="btn-refresh" id="akk-ref" title="Yenile">↻</button></div>
      <div class="seg full at-mode" id="akk-mode"><button type="button" data-akkv="br">KURUM BAZINDA</button><button type="button" data-akkv="bs">KURUM × HİSSE</button><button type="button" data-akkv="one">KURUM SEÇ</button></div>
      <div class="at-brw" id="akk-brw" hidden><div class="at-chips" id="akk-chips"></div><input type="search" class="ak-search" id="akk-brq" placeholder="Kurum ara (örn. Yapı Kredi)" autocomplete="off" spellcheck="false" /><div class="at-brl" id="akk-brl" hidden></div></div>
      <div class="at-fg akk-fg"><label title="Satır başına kurumun o hissedeki toplam alış tutarı (işlem kaydı)"><span>Min alış ₺</span><input type="text" inputmode="decimal" data-akkf="min_tl" placeholder="örn. 1000000" /></label>
        <label title="Satır başına kurumun o hissedeki toplam alış lotu"><span>Min alış lot</span><input type="text" inputmode="decimal" data-akkf="min_lot" placeholder="—" /></label>
        <label title="KURUM BAZINDA: ağırlıklı aktif %; diğer görünümlerde satırın aktif alış %'si"><span>Aktif alış %</span><span class="at-mm"><input type="text" inputmode="decimal" data-akkf="aa" data-akki="0" placeholder="min" /><input type="text" inputmode="decimal" data-akkf="aa" data-akki="1" placeholder="max" /></span></label>
        <label class="akk-bmin" title="KURUM BAZINDA: kurumun (filtreye uyan satırlardaki) toplam alış ₺ alt sınırı"><span>Kurum min toplam alış ₺</span><input type="text" inputmode="decimal" data-akkf="bmin" placeholder="örn. 10000000" /></label>
        <label class="akk-ck"><input type="checkbox" id="akk-net" /> <span>Yalnız net alıcı</span></label></div>
      <div class="trn-pre-w"><button type="button" class="trn-pre" id="akk-trn" data-akkpre="trn" title="Ön ayar: hissenin en büyük balinası + net payı ≥%30 + aktif alış ≥%65 + aktif alış ≥5 Mn ₺">🚂 TAVAN TRENİ</button>
        <label class="akk-ck" id="akk-ttg-l"><input type="checkbox" id="akk-ttg" /> <span>yalnız GÜÇLÜ</span></label><small class="muted">Kurum = hissenin en büyük balinası (AKD Alış #1 / en büyük alış lotu) · net payı ≥%30 · alımının ≥%65'i AKTİF · ≥5 Mn ₺ aktif alış</small></div>
      <label class="akk-ck akk-k5"><input type="checkbox" data-k5tog="1" /> <span>Kurum adına basınca en çok aktif alış yaptığı ilk 5 hisseyi göster <small class="muted">(AKD sekmesi, AKD Taraması, Maliyet Yükselten ve bu ekranda; Ayarlar'dan da açılır)</small></span></label>`;
    const S = akkS();
    $("akk-q").value = S.f.q || "";
    $("akk-q").addEventListener("input", (e) => { S.f.q = e.target.value; S.n = 100; akkSave(); clearTimeout(S._t); S._t = setTimeout(akkRender, 200); });
    $("akk-ref").addEventListener("click", () => akkLoad(true));
    $("akk-date").addEventListener("change", (e) => { S.date = e.target.value; S.d = null; setH($("akk-body"), `<tr><td colspan="12" class="empty">Yükleniyor…</td></tr>`); akkLoad(true); });
    $("akk-net").addEventListener("change", (e) => { S.f.net = !!e.target.checked; S.n = 100; akkSave(); akkRender(); });
    $("akk-ttg").addEventListener("change", (e) => { S.f.ttg = !!e.target.checked; S.n = 100; akkSave(); akkRender(); });   // v1.26.3
    c.addEventListener("input", (e) => { const i = e.target.closest("[data-akkf]"); if (!i) return; const k = i.dataset.akkf; if (k === "aa") S.f.aa[+i.dataset.akki] = i.value; else S.f[k] = i.value; S.n = 100; akkSave(); clearTimeout(S._t); S._t = setTimeout(akkRender, 250); });
    $("akk-brq").addEventListener("input", (e) => { S.brq = e.target.value; akkBrList(); });
    $("akk-brq").addEventListener("focus", () => { S.brOpen = true; akkBrList(); });
    akkSync();
  }
  function akkSync() {
    const S = akkS(), f = S.f;
    document.querySelectorAll("#akk-mode [data-akkv]").forEach((b) => b.classList.toggle("active", b.dataset.akkv === S.view));
    const bw = $("akk-brw"); if (bw) bw.hidden = S.view !== "one";
    document.querySelectorAll("#akk-ctl .akk-bmin").forEach((l) => (l.hidden = S.view !== "br"));
    document.querySelectorAll("[data-akkf]").forEach((i) => { const k = i.dataset.akkf, v = k === "aa" ? f.aa[+i.dataset.akki] : f[k]; if (i.value !== String(v ?? "")) i.value = v ?? ""; });
    const n = $("akk-net"); if (n) n.checked = !!f.net;
    const tb = $("akk-trn"); if (tb) tb.classList.toggle("on", !!f.tt);
    const tg = $("akk-ttg"); if (tg) tg.checked = !!f.ttg;
    const tgl = $("akk-ttg-l"); if (tgl) tgl.hidden = !f.tt;
    document.querySelectorAll("[data-k5tog]").forEach((i) => (i.checked = k5On()));
    const ch = $("akk-chips"); if (ch) ch.innerHTML = f.br ? `<button type="button" class="at-chip" data-akkbrx="1">${esc(brName(f.br))} ✕</button>` : `<span class="muted sm">Kurum seçilmedi — aşağıdan arayıp seçin</span>`;
  }
  function akkBrList() {
    const S = akkS(), el = $("akk-brl"); if (!el) return;
    if (!S.brOpen || !S.d) { el.hidden = true; return; }
    const L = [...new Set(akkRows(S.d).map((r) => r.br))].sort((a, b) => brName(a).localeCompare(brName(b), "tr"));
    const q = trUpper(S.brq || "").trim();
    const m = L.filter((b) => !q || trUpper(brName(b)).includes(q) || trUpper(b).includes(q)).slice(0, 80);
    el.hidden = false;
    el.innerHTML = m.map((b) => `<button type="button" class="at-bri ${b === S.f.br ? "on" : ""}" data-akkpick="${esc(b)}">${brIcon(b)}<span>${esc(brName(b))}</span>${b === S.f.br ? "<b>✓</b>" : ""}</button>`).join("") || `<div class="muted sm">Eşleşen kurum yok</div>`;
  }
  const AKK_CB = [["br", "KURUM", "l sticky"], ["wa", "AĞIRLIKLI AKTİF %"], ["n", "HİSSE"], ["abtl", "AKTİF ALIŞ ₺"], ["tbtl", "TOPLAM ALIŞ ₺"], ["abl", "AKTİF ALIŞ LOT"], ["nn", "NET ALICI"],
    ["n1", "AKD ALIŞ #1"], ["s1", "AKD SATIŞ #1"], ["ntt", "🚂 TAVAN TRENİ"], ["top", "EN ÇOK AKTİF ALDIĞI", "l"]];   // v1.26.3 sıra / tren sayıları
  const AKK_CS = [["s", "HİSSE", "l sticky"], ["br", "KURUM", "l"], ["aa", "AKTİF ALIŞ %"], ["np", "AKD NET %"], ["rb", "AKD ALIŞ SIRA"], ["rs", "AKD SATIŞ SIRA"], ["tt", "🚂 TAVAN TRENİ", "l"],
    ["abl", "AKTİF ALIŞ LOT"], ["abtl", "AKTİF ALIŞ ₺"], ["tbtl", "TOPLAM ALIŞ ₺"], ["nl", "NET LOT"], ["co", "MALİYET"], ["p", "SON"], ["gd", "GÜNLÜK %"]];
  function akkRender() {
    const S = akkS(), d = S.d;
    akkSync();
    const ds = $("akk-date");
    if (ds && d && d.dates) { const h = d.dates.map((x) => `<option value="${x.d}" ${x.d === d.date ? "selected" : ""}>${esc(x.l)}${x.cur ? " · güncel" : ""}</option>`).join(""); if (ds._h !== h) { ds.innerHTML = h; ds._h = h; } }
    const head = $("akk-head"), body = $("akk-body"), more = $("akk-more"), note = $("akk-note"), sum = $("akk-sum");
    const isB = S.view === "br";
    let C = isB ? AKK_CB : AKK_CS;
    if (S.view === "one") C = C.filter((c) => c[0] !== "br");
    const ks = C.map((c) => c[0]);
    if (!ks.includes(S.sort)) { S.sort = isB ? "wa" : "aa"; S.dir = -1; }
    const hh = `<tr>${C.map(([k, l, c]) => `<th data-akksort="${k}" class="${c || ""} ${S.sort === k ? "sorted" + (S.dir > 0 ? " asc" : "") : ""}">${l}</th>`).join("")}</tr>`;
    if (head && head._h !== hh) { head.innerHTML = hh; head._h = hh; }
    const sub = $("akk-sub"); if (sub && d) sub.textContent = `${d.date_label}${d.cur ? " · güncel" : ""} · ${fN((d.aktif && d.aktif.stocks) || 0)} hissede işlem kaydı`;
    if (!d) { setH(body, `<tr><td colspan="12" class="empty">Yükleniyor…</td></tr>`); return; }
    if (!(d.aktif && d.aktif.stocks)) { setH(body, `<tr><td colspan="12" class="empty">${esc((d.aktif && d.aktif.note) || "Bu seans için işlem kaydı yok — aktif alış % hesaplanamıyor.")}</td></tr>`); if (sum) setH(sum, ""); if (more) more.hidden = true; akkWatchR(); return; }
    const k = S.sort, dir = S.dir;
    const cmp = (a, b) => { if (k === "rb" || k === "rs") { const x = isNum(a[k]) ? a[k] : 1e9, y = isNum(b[k]) ? b[k] : 1e9; return dir * (x - y) || (b.abtl || 0) - (a.abtl || 0); }
      if (k === "tt") return dir * ((a.tt || 0) - (b.tt || 0)) || (b.abtl || 0) - (a.abtl || 0);
      if (k === "s" || k === "br") return dir * String(k === "br" ? brName(a.br) : a.s).localeCompare(String(k === "br" ? brName(b.br) : b.s), "tr"); if (k === "top") return dir * (((a.top && a.top.abtl) || 0) - ((b.top && b.top.abtl) || 0)); const x = isNum(a[k]) ? a[k] : -1e18, y = isNum(b[k]) ? b[k] : -1e18; return dir * (x - y); };
    const pc = (v) => (isNum(v) ? "%" + nf(1).format(v) : "—");
    let R;
    if (isB) {
      R = akkAgg(S).sort(cmp);
      setH(body, R.slice(0, S.n).map((x) => `<tr data-akkbr="${esc(x.br)}"><td class="l sticky"><b data-k5br="${esc(x.br)}">${esc(brName(x.br))}</b></td>${atAkTd(x.wa, null, 1).replace("</td>", isNum(x.wal) ? `<small class="at-akt">lot %${nf(1).format(x.wal)}</small></td>` : "</td>")}<td>${fN(x.n)}</td>${atTlTd(Math.round(x.abtl))}${atTlTd(Math.round(x.tbtl))}${atLotTd(x.abl, 1)}<td>${fN(x.nn)}/${fN(x.n)}</td>
        <td class="${x.n1 ? "pos" : "muted"}">${fN(x.n1)}</td><td class="${x.s1 ? "neg" : "muted"}">${fN(x.s1)}</td><td>${x.ntt ? `<span class="trn-b ${x.ntg ? "g" : "o"}">🚂 ${fN(x.ntt)}</span>${x.ntg ? `<small class="at-akt">${fN(x.ntg)} GÜÇLÜ</small>` : ""}` : `<span class="muted">0</span>`}</td>
        <td class="l">${x.top ? `<b>${esc(x.top.s)}</b> <small class="muted">%${nf(1).format(x.top.aa)} · ${fShort(x.top.abtl)} ₺${x.top.rb ? ` · Alış #${x.top.rb}` : x.top.rs ? ` · Satış #${x.top.rs}` : ""}${isNum(x.top.np) && x.top.np ? ` · net %${nf(1).format(Math.abs(x.top.np))}` : ""}</small>${x.top.tt ? ` <span class="trn-b ${x.top.tt >= 2 ? "g" : "o"}">🚂</span>` : ""}` : "—"}</td></tr>`).join("") || `<tr><td colspan="11" class="empty">Filtrelere uyan kurum yok</td></tr>`);
      if (sum) setH(sum, trnSum(S));
    } else {
      if (S.view === "one" && !S.f.br) { setH(body, `<tr><td colspan="10" class="empty">KURUM SEÇ: yukarıdan bir kurum arayıp seçin (örn. Yapı Kredi)</td></tr>`); if (sum) setH(sum, ""); if (more) more.hidden = true; if (note) note.textContent = ""; akkWatchR(); return; }
      R = akkFilt(S, false).sort(cmp);
      const one = S.view === "one";
      setH(body, R.slice(0, S.n).map((r) => `<tr data-akksym="${esc(r.s)}"><td class="l sticky"><b>${esc(r.s)}</b>${r.tt ? `<small class="trn-b sm ${r.tt >= 2 ? "g" : "o"}" title="TAVAN TRENİ ${r.tt >= 2 ? "GÜÇLÜ" : "ORTA"}">🚂 ${r.tt >= 2 ? "GÜÇLÜ" : "ORTA"}</small>` : ""}</td>${one ? "" : `<td class="l at-brc" data-k5br="${esc(r.br)}">${esc(brName(r.br))}</td>`}${atAkTd(r.aa, r.aat, 1)}${trnTds(r, d)}${atLotTd(r.abl, 1)}${atTlTd(r.abtl)}${atTlTd(isNum(r.tbtl) ? Math.round(r.tbtl) : null)}<td class="${cls(r.nl)}">${r.nl > 0 ? "+" : ""}${fN(r.nl)}</td><td>${kmP(r.co)}</td><td>${kmP(r.p)}</td><td class="${cls(r.gd)}">${v6pc(r.gd)}${r.tv === 1 ? ` <small class="trn-tv">TAVAN</small>` : ""}</td></tr>`).join("") || `<tr><td colspan="14" class="empty">${S.f.tt ? "Bu seansta TAVAN TRENİ sinyali yok (ya da filtreler eliyor)" : "Filtrelere uyan satır yok"}</td></tr>`);
      if (sum) {
        if (one) { const a = akkAgg(Object.assign({}, S, { f: Object.assign({}, S.f, { bmin: "", aa: ["", ""], q: "" }) })).find((x) => x.br === S.f.br);
          setH(sum, trnSum(S) + (a ? `<div class="ozp-kvs akk-kvs">${v6kv("Ağırlıklı aktif alış % (₺)", pc(a.wa), (a.wa || 0) >= 60 ? "pos" : "")}${v6kv("Lot bazında", pc(a.wal))}${v6kv("Hisse sayısı", fN(a.n))}${v6kv("Aktif alış", fShort(a.abtl) + " ₺")}${v6kv("Toplam alış", fShort(a.tbtl) + " ₺")}${v6kv("Net alıcı olduğu", `${fN(a.nn)} hisse`)}${v6kv("AKD Alış #1", `${fN(a.n1)} hisse`)}${v6kv("🚂 TAVAN TRENİ", `${fN(a.ntt)} hisse`, a.ntt ? "pos" : "")}</div>` : `<div class="muted sm">Bu kurum için filtreye uyan satır yok.</div>`));
        } else setH(sum, trnSum(S));
      }
    }
    if (more) { more.hidden = R.length <= S.n; more.textContent = `Daha fazla göster (+${Math.min(100, R.length - S.n)} / ${fN(R.length - S.n)})`; }
    if (note) note.textContent = `${fN(R.length)} ${isB ? "kurum" : "satır"} · ${isB ? "ağırlıklı aktif % = Σ aktif alış ₺ ÷ Σ alış ₺ (filtreye uyan hisseler)" : "aktif alış % = aktif alış lotu ÷ alış lotu (AKD Taraması ile aynı)"} · min alış ${S.f.min_tl ? fShort(atNum(S.f.min_tl) || 0) + " ₺" : "—"}${S.f.min_lot ? " / " + fShort(atNum(S.f.min_lot) || 0) + " lot" : ""}${isB && S.f.bmin ? " · kurum ≥" + fShort(atNum(S.f.bmin) || 0) + " ₺" : ""}${S.f.net ? " · yalnız net alıcı" : ""}${S.f.tt ? " · 🚂 TAVAN TRENİ" + (S.f.ttg ? " (yalnız GÜÇLÜ)" : "") : ""} · AKD NET % = AKD sekmesi ALICILAR/SATICILAR DAĞILIM %'si; AKD ALIŞ/SATIŞ SIRA = AKD sekmesindeki sıra (net lot) · Kaynak: ${d.src}${d.ts_s ? " · AKD " + d.ts_s : ""}.${d.aktif && d.aktif.note ? " " + d.aktif.note + "." : ""}`;
    akkWatchR();
  }
  document.addEventListener("click", (e) => {
    if (!v6ok() || st.view !== "akk") return;
    const S = akkS();
    const v = e.target.closest("[data-akkv]"); if (v) { S.view = v.dataset.akkv; S.n = 100; akkSave(); if (S.view === "one" && !S.f.br) { S.brOpen = true; akkBrList(); } akkRender(); return; }
    const pk = e.target.closest("[data-akkpick]"); if (pk) { S.f.br = pk.dataset.akkpick; S.view = "one"; S.brOpen = false; S.n = 100; akkSave(); akkBrList(); akkRender(); return; }
    if (e.target.closest("[data-akkbrx]")) { S.f.br = ""; akkSave(); akkRender(); return; }
    const so = e.target.closest("[data-akksort]"); if (so) { const k = so.dataset.akksort; if (S.sort === k) S.dir *= -1; else { S.sort = k; S.dir = ["s", "br"].includes(k) ? 1 : -1; } akkRender(); return; }
    if (e.target.id === "akk-more") { S.n += 100; akkRender(); return; }
    if (e.target.closest("[data-akkwsave]")) { akkWatchSave(); return; }
    if (e.target.closest("[data-trnwsave]")) { trnWatchSave(); return; }
    if (e.target.closest("[data-akkpre]")) { S.f.tt = !S.f.tt; if (S.f.tt) { if (S.view === "br") S.view = "bs"; S.sort = "tt"; S.dir = -1; } S.n = 100; akkSave(); akkRender(); return; }   // v1.26.3
    const br = e.target.closest("tr[data-akkbr]"); if (br) { S.f.br = br.dataset.akkbr; S.view = "one"; S.n = 100; akkSave(); akkRender(); try { $("akk-table").scrollIntoView({ block: "start" }); } catch (x) {} return; }
    const row = e.target.closest("[data-akksym]"); if (row) { st.tab = "akd"; LS.set("tab", "akd"); openStock(row.dataset.akksym); return; }
    if (!e.target.closest("#akk-brw")) { if (S.brOpen) { S.brOpen = false; akkBrList(); } }
  });
  async function akkWatchLoad() { const S = akkS(); try { S.watch = await api("/api/aktif-kurum/watch", { timeout: 10000 }); } catch (e) { S.watch = S.watch || { err: String(e.message || e) }; } akkWatchR(); }
  async function akkWatchSave() {
    const S = akkS();
    const on = !!($("akk-won") || {}).checked, tl = atNum(($("akk-wtl") || {}).value) ?? 5e6, aa = atNum(($("akk-waa") || {}).value) ?? 85, net = !!($("akk-wnet") || {}).checked, only = !!($("akk-wbr") || {}).checked;
    const body = { on, min_tl: Math.abs(tl), min_aa: Math.max(0, Math.min(100, Math.abs(aa))), net, brokers: only && S.f.br ? [S.f.br] : [] };
    try { S.watch = await api("/api/aktif-kurum/watch", { method: "POST", body: JSON.stringify(body), headers: { "Content-Type": "application/json" }, timeout: 15000 }); toast(on ? "Aktif kurum bildirimi AÇIK ✓" : "Aktif kurum bildirimi KAPALI", 1600); } catch (e) { toast("Kaydedilemedi: " + (e.message || e), 3000); }
    akkWatchR(true);
  }
  function akkWatchR(force) {
    const el = $("akk-nt"); if (!el) return;
    const S = akkS(), W = S.watch || {};
    const h = `<section class="card at-ntc"><div class="card-h"><span class="card-title">BİLDİRİM · AKTİF İŞLEM (KURUM)</span><button type="button" class="btn-ghost sm nf-lnk" data-nflink="ayar">🔔 Tüm bildirim ayarları</button></div>
      ${NT.aktif_kurum ? ntRow("aktif_kurum", false) : ""}<div class="km-ostest"><button type="button" class="btn-ghost sm" data-ostest="${esc(OS_FEAT.aktif_kurum || "Aktif İşlem (Kurum)")}">✈️ Telegram Test · Aktif İşlem (Kurum)</button></div>
      <div class="at-wf"><label class="akk-ck"><input type="checkbox" id="akk-won" ${W.on ? "checked" : ""}/> <span><b>Dedektör ${W.on ? "AÇIK" : "KAPALI"}</b></span></label>
        <label>≥ ₺ <input type="text" inputmode="decimal" id="akk-wtl" value="${esc(String(W.min_tl ?? 5000000))}" /></label><label>aktif alış % ≥ <input type="text" inputmode="decimal" id="akk-waa" value="${esc(String(W.min_aa ?? 85))}" /></label>
        <label class="akk-ck"><input type="checkbox" id="akk-wnet" ${W.net !== false ? "checked" : ""}/> <span>yalnız net alıcı</span></label>
        <label class="akk-ck" title="KURUM SEÇ görünümünde seçili kurum"><input type="checkbox" id="akk-wbr" ${(W.brokers || []).length ? "checked" : ""}/> <span>yalnız ${esc(S.f.br ? brName(S.f.br) : (W.brokers || []).map(brName).join(", ") || "seçili kurum")}</span></label>
        <button type="button" class="btn-ghost sm" data-akkwsave="1">💾 Kaydet</button></div>
      <div class="src-note">${esc(W.note || "Seans içinde ~60 sn'de bir sunucuda kontrol edilir.")} Varsayılan KAPALI. Bildirim modu (KAPALI / GÖRÜNTÜLE / BİLDİRİM) yukarıdaki satırdan.${W.err ? " (" + esc(W.err) + ")" : ""}</div></section>` + trnWatchH();
    if (force || el._wh !== h || !el.firstChild) { if (!force && el.firstChild && el.contains(document.activeElement) && document.activeElement.tagName === "INPUT") return; el.innerHTML = h; el._wh = h; }
  }

  // ---- (2) kurum adına dokun → ilk 5 aktif hisse
  function k5On() { return LS.get("k5br", false) === true; }
  function k5Set(v) { LS.set("k5br", !!v); document.querySelectorAll("[data-k5tog]").forEach((i) => (i.checked = !!v)); toast(v ? "Kurum adına basınca ilk 5 aktif hisse: AÇIK" : "Kurum adına basınca ilk 5 aktif hisse: KAPALI", 1600); }
  function k5SetCard() {
    return `<section class="card dr-set" id="k5-set"><div class="card-h"><span class="card-title">KURUM ADINA BASINCA</span></div>
      <label class="dr-row"><span class="dr-rl"><b>En çok aktif alış yaptığı ilk 5 hisseyi göster</b><small>AKD sekmesi, AKD Taraması, Aktif İşlem Taraması (KURUM) ve Maliyet Yükselten'de kurum adına dokununca küçük panel açılır (aktif %, aktif lot, ₺; satırdan hisseye gidilir). Varsayılan KAPALI; bu cihazda saklanır.</small></span><span class="nf-sw"><input type="checkbox" data-k5tog="1" ${k5On() ? "checked" : ""}/><span></span></span></label></section>`;
  }
  document.addEventListener("change", (e) => { const i = e.target.closest && e.target.closest("[data-k5tog]"); if (i) k5Set(i.checked); });
  async function k5Data() {
    const S = akkS();
    if (S.d && (!S.date || (S.d.cur && Date.now() - S.last < 120000))) return S.d;
    if (AT && AT.d && !AT.date && Date.now() - AT.last < 120000) return AT.d;
    const d = await api(`/api/akd/tarama?date=`, { timeout: 60000 });
    if (!S.d || !S.date) { S.d = d; S.last = Date.now(); }
    return d;
  }
  function k5Close() { const p = $("k5-pop"); if (p) p.remove(); }
  async function k5Show(br) {
    k5Close();
    const p = document.createElement("div"); p.id = "k5-pop"; p.className = "k5-pop";
    const mt = atNum(akkS().f.min_tl) ?? 1e6;
    const hd = `<div class="k5-h">${brIcon(br)}<b>${esc(brName(br))}</b><span class="muted sm">en çok aktif alış yaptığı 5 hisse</span><button type="button" class="k5-x" data-k5x="1" aria-label="Kapat">✕</button></div>`;
    p.innerHTML = hd + `<div class="empty">Yükleniyor…</div>`;
    document.body.appendChild(p);
    try {
      const d = await k5Data();
      if (!$("k5-pop") || $("k5-pop") !== p) return;
      const T = akkTop5(d, br, mt);
      p.innerHTML = hd + (T.length ? `<div class="k5-l">${T.map((r, i) => `<button type="button" class="k5-r" data-k5sym="${esc(r.s)}"><span class="n">${i + 1}</span><b>${esc(r.s)}</b><span class="v ${r.aa >= 70 ? "pos" : ""}">%${nf(1).format(r.aa)}<small>aktif</small></span><span class="v">${fShort(r.abl)}<small>lot</small></span><span class="v">${fShort(r.abtl)}<small>₺</small></span><span class="v ${cls(r.nl)}">${r.nl > 0 ? "+" : ""}${fShort(r.nl)}<small>net</small></span></button>`).join("")}</div>`
        : `<div class="muted sm" style="padding:8px 2px">Bu kurumun min ${fShort(mt)} ₺ alış yaptığı hisse yok (ya da işlem kaydı yok).</div>`)
        + `<div class="src-note">${esc(d.date_label || "")} · aktif alış % = aktif alış lotu ÷ alış lotu (AKD Taraması ile aynı) · satır başına min ${fShort(mt)} ₺ alış (Aktif İşlem Taraması filtresi). Hisseye dokun → hisse.</div>`;
    } catch (e) { if ($("k5-pop") === p) p.innerHTML = hd + `<div class="empty">Alınamadı (${esc(e.message || e)})</div>`; }
  }
  document.addEventListener("click", (e) => {
    const pop = $("k5-pop");
    if (pop) {
      if (e.target.closest && e.target.closest("#k5-pop")) {
        if (e.target.closest("[data-k5x]")) { k5Close(); e.stopPropagation(); return; }
        const s = e.target.closest("[data-k5sym]"); if (s) { const sym = s.dataset.k5sym; k5Close(); e.stopPropagation(); openStock(sym); }
        return;
      }
    }
    if (!k5On()) { if (pop) k5Close(); return; }
    const t = e.target; if (!t || !t.closest) return;
    let br = null;
    const a = t.closest("[data-k5br]");
    if (a) br = a.dataset.k5br;
    else { const kn = t.closest("td.kn"); if (kn) { const tr = kn.closest("tr[data-row-br]"); if (tr) br = tr.dataset.rowBr; } }
    if (!br) { if (pop) k5Close(); return; }
    e.stopPropagation(); e.preventDefault();
    k5Show(br);
  }, true);

  // ---- (3) Özet: tahtacı satırı
  function ozTht(d) {
    const T = (d && d.tahtaci) || []; if (!T.length) return "";
    return T.map(thtHtml).join("");
  }
  // ===================================================================== v1.26.3 ==
  // ---- 🚂 TAVAN TRENİ: Aktif İşlem Taraması (KURUM) sütunları (AKD NET % / AKD Alış-Satış sırası / rozet + ✓✗ kontrol listesi), ön ayar, özet, bildirim kartı
  function thtHtml(x) {
    const tr = x && x.kind === "tren";
    const ck = tr && Array.isArray(x.chk) ? `<div class="trn-cl">${x.chk.map((c) => `<span class="${c.ok ? "y" : "n"}">${c.ok ? "✓" : "✗"} ${esc(String(c.l || ""))} <b>${esc(String(c.v || ""))}</b></span>`).join("")}</div>` : "";
    return `<div class="tht-sig ${x.side === "up" ? "up" : "dn"} ${x.grade === "güçlü" ? "g" : "o"}${tr ? " tren" : ""}">${esc(String(x.text || ""))}${ck}</div>`;
  }
  function trnP(d) { return (d && d.trn_p) || { np: 30, aa: 65, tl: 5e6, tl_g: 10e6 }; }
  function trnCell(r, P) {
    if (!(r.nl > 0)) return `<span class="muted">—</span>`;
    const c = [r.rb === 1 || r.wb === 1, (r.np || 0) >= P.np, isNum(r.aa) && r.aa >= P.aa, (r.abtl || 0) >= P.tl];
    const L = [r.rb !== 1 && r.wb === 1 ? "🐋" : "#1", `%${P.np}`, `A%${P.aa}`, `${nf(0).format(P.tl / 1e6)}Mn₺`];
    const T = [`AKD Alış #1 ya da hissenin en büyük alış lotu (bu satır: Alış #${isNum(r.rb) ? r.rb : "—"}${isNum(r.wb) ? " · alış lotu #" + r.wb : ""})`,
      `net payı (AKD DAĞILIM %) ≥ %${P.np} (bu satır %${nf(1).format(Math.abs(r.np || 0))})`,
      `aktif alış ≥ %${P.aa} (bu satır ${isNum(r.aa) ? "%" + nf(1).format(r.aa) : "—"})`,
      `aktif alış ≥ ${fShort(P.tl)} ₺ (bu satır ${fShort(r.abtl || 0)} ₺) · GÜÇLÜ: Alış #1 + ≥ ${fShort(P.tl_g)} ₺`];
    const ck = `<span class="trn-ck">${c.map((ok, i) => `<i class="${ok ? "y" : "n"}" title="${esc(T[i])}">${ok ? "✓" : "✗"}${esc(L[i])}</i>`).join("")}</span>`;
    return (r.tt ? `<span class="trn-b ${r.tt >= 2 ? "g" : "o"}">🚂 ${r.tt >= 2 ? "GÜÇLÜ" : "ORTA"}</span>` : "") + ck;
  }
  function trnTds(r, d) {
    const P = trnP(d);
    const np = isNum(r.np) && (r.np || r.rb || r.rs) ? `<td class="${cls(r.np)}" title="${r.np > 0 ? "net alımın payı (ALICILAR DAĞILIM %)" : "net satışın payı (SATICILAR DAĞILIM %)"}">%${nf(1).format(Math.abs(r.np))}</td>` : `<td class="muted">—</td>`;
    const rb = isNum(r.rb) ? `<td><span class="trn-rk ${r.rb === 1 ? "g" : ""}">Alış #${r.rb}</span>${r.wb === 1 ? `<small class="at-akt">🐋 en büyük alış</small>` : ""}</td>` : `<td class="muted">—</td>`;
    const rs = isNum(r.rs) ? `<td><span class="trn-rk s ${r.rs === 1 ? "g" : ""}">Satış #${r.rs}</span></td>` : `<td class="muted">—</td>`;
    return np + rb + rs + `<td class="l">${trnCell(r, P)}</td>`;
  }
  function trnSum(S) {
    const d = S.d; if (!S.f.tt || !d) return "";
    const R = akkRows(d).filter((r) => r.tt > 0);
    const by = new Map(); for (const r of R) { const o = by.get(r.s); if (!o || r.tt > o.tt || (r.tt === o.tt && (r.abtl || 0) > (o.abtl || 0))) by.set(r.s, r); }
    const st = [...by.values()];
    const med = (a) => { if (!a.length) return null; const s = a.slice().sort((x, y) => x - y), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
    const f = (A) => ({ n: A.length, tv: A.filter((r) => r.tv === 1).length, up: A.filter((r) => (r.gd || 0) > 0).length, med: med(A.map((r) => r.gd || 0)) });
    const hasTv = st.some((r) => r.tv != null);
    const sc = {}; ((d.cols && d.cols.stocks) || []).forEach((k, i) => (sc[k] = i));
    const SK = d.stocks || [], ntv = sc.tv != null ? SK.filter((s) => s[sc.tv] === 1).length : 0, nup = SK.filter((s) => (s[sc.gd] || 0) > 0).length;
    const line = (l, x, c) => `<div class="trn-sr"><b class="${c}">${l}</b><span>${fN(x.n)} hisse</span>${hasTv ? `<span class="${x.tv ? "pos" : "muted"}">${fN(x.tv)} tavan kapattı${x.n ? ` (%${nf(0).format((x.tv / x.n) * 100)})` : ""}</span>` : ""}<span>${fN(x.up)} yükseldi</span><span>medyan gün ${isNum(x.med) ? v6pc(x.med) : "—"}</span></div>`;
    const P = trnP(d);
    return `<section class="card trn-sum"><div class="card-h"><span class="card-title">🚂 TAVAN TRENİ · ${esc(d.date_label || "")}${d.cur ? " · güncel" : ""}</span><span class="muted sm">${fN(R.length)} kurum-hisse satırı</span></div>
      ${line("GÜÇLÜ", f(st.filter((r) => r.tt >= 2)), "g")}${line("ORTA", f(st.filter((r) => r.tt < 2)), "o")}${line("TOPLAM", f(st), "")}
      <div class="trn-sr base"><b>Tüm hisseler</b><span>${fN(SK.length)} hisse</span>${hasTv ? `<span>${fN(ntv)} tavan (%${nf(1).format(SK.length ? (ntv / SK.length) * 100 : 0)})</span>` : ""}<span>${fN(nup)} yükseldi</span></div>
      <div class="src-note">Koşullar (hepsi): kurum hissenin en büyük balinası (AKD Alış #1 ya da en büyük alış lotu) · net payı (AKD DAĞILIM %) ≥ %${P.np} · alımının ≥ %${P.aa}'i AKTİF (piyasa emriyle) · ≥ ${nf(0).format(P.tl / 1e6)} Mn ₺ aktif alış. GÜÇLÜ = AKD Alış #1 + ≥ ${nf(0).format(P.tl_g / 1e6)} Mn ₺ aktif alış. Eşikler 02.10.2026 verisiyle ayarlandı. ${hasTv ? "Tavan = son fiyat ≥ önceki kapanışın +%10 limiti (yalnız güncel seans). " : ""}Gün sonu AKD'siyle sağlama tek günlüktür (sinyal günün kendi verisinden hesaplanır); seans içinde canlı oluşur. Garanti değildir, yatırım tavsiyesi değildir.</div></section>`;
  }
  async function trnWatchLoad() { const S = akkS(); try { S.trw = await api("/api/tavan-treni/watch", { timeout: 10000 }); } catch (e) { S.trw = S.trw || { err: String(e.message || e) }; } akkWatchR(); }
  async function trnWatchSave() {
    const S = akkS();
    const on = !!($("trn-won") || {}).checked, grade = +(($("trn-wg") || {}).value || 2) === 1 ? 1 : 2;
    try { S.trw = await api("/api/tavan-treni/watch", { method: "POST", body: JSON.stringify({ on, grade }), headers: { "Content-Type": "application/json" }, timeout: 15000 }); toast(on ? "TAVAN TRENİ bildirimi AÇIK ✓" : "TAVAN TRENİ bildirimi KAPALI", 1600); } catch (e) { toast("Kaydedilemedi: " + (e.message || e), 3000); }
    akkWatchR(true);
  }
  function trnWatchH() {
    const W = akkS().trw || {};
    return `<section class="card at-ntc trn-ntc"><div class="card-h"><span class="card-title">BİLDİRİM · 🚂 TAVAN TRENİ</span><button type="button" class="btn-ghost sm nf-lnk" data-nflink="ayar">🔔 Tüm bildirim ayarları</button></div>
      ${NT.tavan_treni ? ntRow("tavan_treni", false) : ""}<div class="km-ostest"><button type="button" class="btn-ghost sm" data-ostest="${esc(OS_FEAT.tavan_treni || "TAVAN TRENİ")}">✈️ Telegram Test · TAVAN TRENİ</button></div>
      <div class="at-wf"><label class="akk-ck"><input type="checkbox" id="trn-won" ${W.on ? "checked" : ""}/> <span><b>Dedektör ${W.on ? "AÇIK" : "KAPALI"}</b></span></label>
        <label>derece <select id="trn-wg" class="pill-select"><option value="2" ${W.grade !== 1 ? "selected" : ""}>yalnız GÜÇLÜ</option><option value="1" ${W.grade === 1 ? "selected" : ""}>GÜÇLÜ + ORTA</option></select></label>
        <button type="button" class="btn-ghost sm" data-trnwsave="1">💾 Kaydet</button></div>
      <div class="src-note">${esc(W.note || "Seans içinde ~60 sn'de bir sunucuda kontrol edilir.")} Varsayılan KAPALI. Bildirim modu (KAPALI / GÖRÜNTÜLE / BİLDİRİM) yukarıdaki satırdan.${W.err ? " (" + esc(W.err) + ")" : ""}</div></section>`;
  }


  // ---- blok sonu: hazır → mevcut ekranı bir kez tetikle (ilk openTab/hashGo bu bloktan önce çalıştı)
  V126_READY = true;
  try {
    if (st.view === "akdt") atOpen();
    else if (st.view === "akk") akkOpen();   // v1.26.2
    else if (st.view === "stock") {
      if (st.tab === "derinlik" || st.tab === "ozet") { flRender(); flLoad(true); }
      if (st.tab === "derinlik" && st.ideal) renderDerinlik();
      if (st.tab === "akd" && st.akd) akpLoad();
    }
    mkLegend();
  } catch (e) { try { console.warn("v1.26 init", e); } catch (x) {} }


  // ===================================================================== v1.27.0 ==
  // MUM FORMASYONLARI + GRAFİK FORMASYONLARI (KEŞFET) · animasyonlu kanıt · Özet FORMASYONLAR kartı · grafik işaretleri · bildirimler
  var V127_READY, FMS, FMK, FMZ;
  const FM_TFS = ["5m", "15m", "30m", "60m", "2h", "4h", "1d", "1w"];
  const FM_TFL = { "5m": "5dk", "15m": "15dk", "30m": "30dk", "60m": "60dk", "2h": "2s", "4h": "4s", "1d": "1G", "1w": "1H" };
  const FM_TFLL = { "5m": "5 dk", "15m": "15 dk", "30m": "30 dk", "60m": "60 dk", "2h": "2 saat", "4h": "4 saat", "1d": "Günlük", "1w": "Haftalık" };
  const FM_YON = { U: "YÜKSELİŞ", D: "DÜŞÜŞ", N: "KARARSIZ" };
  const FM_REL = { 1: "Düşük", 2: "Orta", 3: "Yüksek" };
  const fmP = (v) => (isNum(v) ? nf(Math.abs(v) >= 1000 ? 1 : 2).format(v) : "—");
  const fmPc = (v, d = 1) => (isNum(v) ? (v > 0 ? "+" : "") + nf(d).format(v) + "%" : "—");
  const fmCls = (y) => (y === "U" ? "up" : y === "D" ? "dn" : "nt");
  const fmAr = (y) => (y === "U" ? "▲" : y === "D" ? "▼" : "◆");
  function fmTime(t, tf, full) {
    const d = new Date((t + 3 * 3600) * 1000), p2 = (x) => String(x).padStart(2, "0");
    const dm = `${p2(d.getUTCDate())}.${p2(d.getUTCMonth() + 1)}`;
    if (tf === "1d") return full ? `${dm}.${d.getUTCFullYear()}` : `${dm}.${String(d.getUTCFullYear()).slice(2)}`;
    if (tf === "1w") return `${dm}.${String(d.getUTCFullYear()).slice(2)} hf`;
    return `${dm} ${p2(d.getUTCHours())}:${p2(d.getUTCMinutes())}`;
  }
  const FM_MUM_PRE = [
    ["guclu_up", "💪 Güçlü yükseliş dönüşleri", { yon: "U", tip: "dönüş", guven: 3 }],
    ["guclu_dn", "⚠️ Güçlü düşüş dönüşleri", { yon: "D", tip: "dönüş", guven: 3 }],
    ["hacim_up", "📊 Hacim teyitli yükseliş", { yon: "U", hacim: true, guven: 2 }],
    ["yildiz", "⭐ Yıldız & Yutan (4s/1G)", { pats: ["morning_star", "evening_star", "morning_doji_star", "evening_doji_star", "abandoned_baby_bull", "abandoned_baby_bear", "engulfing_bull", "engulfing_bear"], tfs: ["4h", "1d"] }],
    ["kararsiz", "◆ Kararsızlık (doji ailesi)", { yon: "N" }]];
  const FM_GR_PRE = [
    ["taze_up", "🚀 Taze yükseliş kırılımları", { yon: "U", durum: ["KIRILDI"], taze: 3, kalite: 60 }],
    ["taze_dn", "🔻 Taze düşüş kırılımları", { yon: "D", durum: ["KIRILDI"], taze: 3, kalite: 60 }],
    ["yakin", "🎯 Kırılıma yakın (≤%2)", { durum: ["OLUŞUYOR"], uzak: 2, kalite: 60 }],
    ["obo", "👤 OBO / Ters OBO", { pats: ["obo", "ters_obo"] }],
    ["ucgen", "📐 Üçgen & Takoz", { pats: ["yukselen_ucgen", "alcalan_ucgen", "simetrik_ucgen", "yukselen_takoz", "alcalan_takoz"] }],
    ["rr", "⚖️ Yüksek R/R (≥2)", { rr: 2, durum: ["KIRILDI", "OLUŞUYOR"], kalite: 50 }]];
  const FM_DEF = {
    mum: { tfs: FM_TFS.slice(), yon: "", pats: [], guven: 1, hacim: false, tip: "", q: "", sort: "skor", pre: "" },
    grafik: { tfs: FM_TFS.slice(), yon: "", pats: [], durum: ["KIRILDI", "OLUŞUYOR"], kalite: 50, hacim: false, rr: 0, uzak: 0, taze: 0, q: "", sort: "kalite", pre: "" } };
  function fmS() {
    if (!FMS) {
      FMS = { mum: { d: null, ts: 0, busy: false, n: 60 }, grafik: { d: null, ts: 0, busy: false, n: 60 }, w: null, f: {} };
      ["mum", "grafik"].forEach((k) => { FMS.f[k] = Object.assign(JSON.parse(JSON.stringify(FM_DEF[k])), LS.get("fmF_" + k, null) || {}); });
    }
    return FMS;
  }
  const fmKind = (view) => (view === "fm_grafik" ? "grafik" : "mum");
  const fmPx = (k) => (k === "mum" ? "fmm" : "fmg");
  function fmOpen(view) {
    if (!V127_READY) return;
    const k = fmKind(view); fmS();
    fmCtl(k); fmRender(k); fmLoad(k, !FMS[k].d); fmWatchLoad();
  }
  async function fmLoad(k, force) {
    const S = fmS()[k];
    if (S.busy || (!force && Date.now() - S.ts < 45000 && S.d)) return;
    S.busy = true;
    try { S.d = await api(`/api/formasyon/${k}`, { timeout: 30000 }); S.ts = Date.now(); S.err = null; }
    catch (e) { S.err = String(e.message || e); }
    finally { S.busy = false; }
    if (st.view === "fm_" + k) fmRender(k);
  }
  function fmRows(k) {
    const d = fmS()[k].d; if (!d || !d.rows) return [];
    const C = {}; d.cols.forEach((c, i) => { C[c] = i; });
    return d.rows.map((r) => { const o = {}; for (const c in C) o[c] = r[C[c]]; return o; });
  }
  function fmFilter(k, rows) {
    const f = fmS().f[k], pat = (fmS()[k].d || {}).pat || {};
    const q = (f.q || "").trim().toLocaleUpperCase("tr-TR");
    return rows.filter((r) => {
      if (!f.tfs.includes(r.tf)) return false;
      if (f.yon && r.yon !== f.yon) return false;
      if (f.pats && f.pats.length && !f.pats.includes(r.k)) return false;
      if (q && !r.s.includes(q)) return false;
      if (f.hacim && !r.hacim) return false;
      if (k === "mum") {
        if ((r.guven || 0) < (f.guven || 1)) return false;
        if (f.tip && r.tip !== f.tip) return false;
      } else {
        if (f.durum && f.durum.length && !f.durum.includes(r.durum)) return false;
        if ((r.kalite || 0) < (f.kalite || 0)) return false;
        if (f.rr && !(r.rr >= f.rr)) return false;
        if (f.uzak && !(r.durum === "OLUŞUYOR" && Math.abs(r.d_giris) <= f.uzak)) return false;
        if (f.taze && !(r.durum === "KIRILDI" && r.bo_n != null && r.bo_n <= f.taze)) return false;
      }
      return !!pat[r.k];
    });
  }
  function fmSort(k, rows) {
    const s = fmS().f[k].sort, tfi = (tf) => FM_TFS.indexOf(tf);
    const by = {
      skor: (a, b) => b.skor - a.skor || b.guven - a.guven, guven: (a, b) => b.guven - a.guven || b.skor - a.skor, hacim: (a, b) => (b.hr || 0) - (a.hr || 0),
      hisse: (a, b) => a.s.localeCompare(b.s, "tr") || tfi(a.tf) - tfi(b.tf), periyot: (a, b) => tfi(b.tf) - tfi(a.tf) || b.skor - a.skor,
      kalite: (a, b) => b.kalite - a.kalite || (a.bo_n ?? 99) - (b.bo_n ?? 99), rr: (a, b) => (b.rr || 0) - (a.rr || 0),
      uzak: (a, b) => Math.abs(a.d_giris) - Math.abs(b.d_giris), hedef: (a, b) => Math.abs(b.d_h1) - Math.abs(a.d_h1), taze: (a, b) => (a.bo_n ?? 999) - (b.bo_n ?? 999) || b.kalite - a.kalite };
    return rows.sort(by[s] || by[k === "mum" ? "skor" : "kalite"]);
  }
  function fmSave(k) { LS.set("fmF_" + k, fmS().f[k]); }
  function fmCtl(k) {
    const el = $(fmPx(k) + "-ctl"); if (!el) return;
    const f = fmS().f[k], d = fmS()[k].d, pat = (d && d.pat) || {};
    const PRE = k === "mum" ? FM_MUM_PRE : FM_GR_PRE;
    const opts = (arr, cur) => arr.map(([v, l]) => `<option value="${esc(String(v))}" ${String(cur) === String(v) ? "selected" : ""}>${esc(l)}</option>`).join("");
    const pk = Object.keys(pat).sort((a, b) => pat[a][0].localeCompare(pat[b][0], "tr"));
    const patSel = `<select class="pill-select" data-fmf="pat"><option value="">Tüm formasyonlar</option>${f.pats.length > 1 ? `<option value="__multi" selected>${f.pats.length} formasyon (ön ayar)</option>` : ""}${pk.map((p) => `<option value="${p}" ${f.pats.length === 1 && f.pats[0] === p ? "selected" : ""}>${fmAr(pat[p][2])} ${esc(pat[p][0])}</option>`).join("")}</select>`;
    const sorts = k === "mum" ? [["skor", "Skor"], ["guven", "Güvenilirlik"], ["hacim", "Hacim oranı"], ["periyot", "Uzun periyot önce"], ["hisse", "Hisse (A-Z)"]]
      : [["kalite", "Kalite"], ["taze", "Taze kırılım"], ["rr", "R/R"], ["uzak", "Kırılıma yakın"], ["hedef", "Hedef potansiyeli"], ["periyot", "Uzun periyot önce"], ["hisse", "Hisse (A-Z)"]];
    setH(el, `<div class="fm-pre">${PRE.map(([id, l]) => `<button type="button" class="fm-chip ${f.pre === id ? "on" : ""}" data-fmpre="${id}">${esc(l)}</button>`).join("")}${f.pre ? `<button type="button" class="fm-chip clr" data-fmpre="">✕ Temizle</button>` : ""}</div>
      <div class="fm-tfs"><span class="fm-lb">Periyot</span>${FM_TFS.map((t) => `<button type="button" class="fm-tf ${f.tfs.includes(t) ? "on" : ""}" data-fmtf="${t}">${FM_TFL[t]}</button>`).join("")}<button type="button" class="fm-tf all" data-fmtf="*">${f.tfs.length === FM_TFS.length ? "Hiçbiri" : "Tümü"}</button></div>
      <div class="fm-row">
        <select class="pill-select" data-fmf="yon">${opts([["", "Tüm yönler"], ["U", "▲ Yükseliş"], ["D", "▼ Düşüş"], ["N", "◆ Kararsız"]], f.yon)}</select>
        ${patSel}
        ${k === "mum" ? `<select class="pill-select" data-fmf="guven">${opts([[1, "Güven: tümü"], [2, "Güven: Orta+"], [3, "Güven: Yüksek"]], f.guven)}</select>
          <select class="pill-select" data-fmf="tip">${opts([["", "Dönüş + devam"], ["dönüş", "Yalnız dönüş"], ["devam", "Yalnız devam"], ["kararsızlık", "Kararsızlık"]], f.tip)}</select>`
        : `<select class="pill-select" data-fmf="kalite">${opts([[0, "Kalite: tümü"], [50, "Kalite ≥ 50"], [60, "Kalite ≥ 60"], [70, "Kalite ≥ 70"], [80, "Kalite ≥ 80"]], f.kalite)}</select>
          <select class="pill-select" data-fmf="rr">${opts([[0, "R/R: tümü"], [1, "R/R ≥ 1"], [1.5, "R/R ≥ 1,5"], [2, "R/R ≥ 2"], [3, "R/R ≥ 3"]], f.rr)}</select>
          <select class="pill-select" data-fmf="uzak">${opts([[0, "Uzaklık: tümü"], [1, "Kırılıma ≤ %1"], [2, "Kırılıma ≤ %2"], [5, "Kırılıma ≤ %5"]], f.uzak)}</select>
          <select class="pill-select" data-fmf="taze">${opts([[0, "Kırılım: her zaman"], [1, "Son 1 bar"], [3, "Son 3 bar"], [6, "Son 6 bar"]], f.taze)}</select>`}
        <select class="pill-select" data-fmf="sort">${opts(sorts, f.sort)}</select>
      </div>
      <div class="fm-row">
        ${k === "grafik" ? `<span class="fm-lb">Durum</span>${["KIRILDI", "OLUŞUYOR", "BAŞARISIZ"].map((x) => `<button type="button" class="fm-tf ${f.durum.includes(x) ? "on" : ""}" data-fmdur="${x}">${x}</button>`).join("")}` : ""}
        <label class="akk-ck"><input type="checkbox" data-fmf="hacim" ${f.hacim ? "checked" : ""}/> <span>Hacim teyitli</span></label>
        <input type="search" class="fm-q" data-fmf="q" placeholder="Hisse ara…" value="${esc(f.q || "")}" autocomplete="off"/>
      </div>`);
  }
  function fmApplyPre(k, id) {
    const f = fmS().f[k], q = f.q, sort = f.sort;
    const base = JSON.parse(JSON.stringify(FM_DEF[k]));
    const P = (k === "mum" ? FM_MUM_PRE : FM_GR_PRE).find((x) => x[0] === id);
    Object.assign(base, P ? JSON.parse(JSON.stringify(P[2])) : {}, { q, sort: P ? (k === "grafik" && P[2].taze ? "taze" : P && P[2].uzak ? "uzak" : P && P[2].rr ? "rr" : sort) : sort, pre: P ? id : "" });
    fmS().f[k] = base;
  }
  function fmRender(k) {
    const S = fmS()[k], px = fmPx(k), d = S.d;
    const body = $(px + "-list"), sum = $(px + "-sum"), note = $(px + "-note"), more = $(px + "-more");
    if (!body) return;
    if (!d) { setH(body, `<div class="empty">${S.err ? "Alınamadı: " + esc(S.err) : "Formasyonlar yükleniyor…"}</div>`); if (more) more.hidden = true; return; }
    if (!d.meta || !d.meta.ready) { setH(body, `<div class="empty">Formasyon motoru hazırlanıyor (${esc((d.meta && d.meta.state) || "—")}) — barlar yükleniyor, ilk tarama ~1 dk sürer.</div>`); setTimeout(() => fmLoad(k, true), 15000); }
    const all = fmRows(k), rows = fmSort(k, fmFilter(k, all));
    const pat = d.pat || {}, M = d.meta || {};
    // özet
    const nU = rows.filter((r) => r.yon === "U").length, nD = rows.filter((r) => r.yon === "D").length, nN = rows.length - nU - nD;
    const byTf = {}; rows.forEach((r) => { byTf[r.tf] = byTf[r.tf] || { U: 0, D: 0, N: 0 }; byTf[r.tf][r.yon]++; });
    const byP = {}; rows.forEach((r) => { byP[r.k] = (byP[r.k] || 0) + 1; });
    const topP = Object.entries(byP).sort((a, b) => b[1] - a[1]).slice(0, 6);
    const last = Object.values(M.scan || {}).map((x) => x.at || 0).reduce((a, b) => Math.max(a, b), 0);
    setH(sum, `<section class="card fm-sum"><div class="fm-sum-h"><b>${fN(rows.length)}</b> eşleşme <span class="muted">/ ${fN(all.length)} sinyal · ${fN(new Set(rows.map((r) => r.s)).size)} hisse</span>
        <span class="fm-b up">▲ ${fN(nU)}</span><span class="fm-b dn">▼ ${fN(nD)}</span>${nN ? `<span class="fm-b nt">◆ ${fN(nN)}</span>` : ""}</div>
      <div class="fm-tfgrid">${FM_TFS.map((t) => { const x = byTf[t] || { U: 0, D: 0, N: 0 }; return `<div class="fm-tfc ${fmS().f[k].tfs.includes(t) ? "" : "off"}"><b>${FM_TFL[t]}</b><span class="up">▲${x.U}</span><span class="dn">▼${x.D}</span></div>`; }).join("")}</div>
      ${topP.length ? `<div class="fm-top">${topP.map(([p, n]) => `<button type="button" class="fm-chip sm ${fmCls(pat[p][2])}" data-fmpat="${p}">${esc(pat[p][0])} <b>${n}</b></button>`).join("")}</div>` : ""}
      <div class="src-note">${esc(M.closed_note || "")} Son tarama ${last ? new Date(last * 1000).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" }) : "—"} · geçmiş ${esc(fmDay(M.hist_last_day))}${M.today_day ? ` · bugün canlı (${fN(M.today_syms || 0)} hisse)` : " · seans dışı: son barlar son seansa ait"}.</div></section>`);
    const n = Math.min(rows.length, S.n);
    const bt = d.bt || {};
    const rowH = (r) => {
      const P = pat[r.k] || [r.k, "", "N", ""], nm = P[0];
      if (k === "mum") {
        const b = bt[r.k];
        return `<button type="button" class="fm-r" data-fmk="${esc(r.s)}|${r.tf}|${r.k}"><div class="fm-r1"><b class="fm-s">${esc(r.s)}</b><span class="fm-tfb">${FM_TFL[r.tf]}</span><span class="fm-nm ${fmCls(r.yon)}">${fmAr(r.yon)} ${esc(nm)}</span>
          <span class="fm-rel r${r.guven}" title="Güvenilirlik">${"●".repeat(r.guven)}${"○".repeat(3 - r.guven)}</span>${r.hacim ? `<span class="fm-b vol">HACİM ${fN(r.hr, 1)}×</span>` : ""}</div>
          <div class="fm-r2"><span class="${fmCls(r.yon)}">${FM_YON[r.yon]}</span> · ${esc(r.tip)} · kapanış <b>${fmP(r.p)}</b> · ${r.yon === "D" ? "teyit &lt;" : "teyit &gt;"} <b>${fmP(r.yon === "D" ? r.gecersiz : r.teyit)}</b>${r.yon !== "N" ? ` · geçersiz ${fmP(r.yon === "D" ? r.teyit : r.gecersiz)}` : ""}
          ${b && b.n >= 30 ? `<span class="fm-bt" title="Günlük geçmiş test">1G test: ertesi gün %${fN(b.w1, 0)} isabet (n=${fN(b.n)})</span>` : ""}</div></button>`;
      }
      const dc = r.durum === "KIRILDI" ? "kir" : r.durum === "OLUŞUYOR" ? "olu" : "bas";
      return `<button type="button" class="fm-r" data-fmk="${esc(r.s)}|${r.tf}|${r.k}"><div class="fm-r1"><b class="fm-s">${esc(r.s)}</b><span class="fm-tfb">${FM_TFL[r.tf]}</span><span class="fm-nm ${fmCls(r.yon)}">${fmAr(r.yon)} ${esc(nm)}</span>
        <span class="fm-dur ${dc} ${fmCls(r.yon)}">${r.durum}${r.durum === "KIRILDI" && r.bo_n != null ? ` · ${r.bo_n === 0 ? "son bar" : r.bo_n + " bar önce"}` : ""}</span>${r.hacim ? `<span class="fm-b vol">HACİM</span>` : ""}${r.h1_ok ? `<span class="fm-b ok">H1 ✓</span>` : ""}</div>
        <div class="fm-lv"><span>Giriş <b>${fmP(r.giris)}</b></span><span class="neg">STOP <b>${fmP(r.stop)}</b></span><span class="pos">H1 <b>${fmP(r.h1)}</b></span><span class="pos">H2 <b>${fmP(r.h2)}</b></span><span>R/R <b>${fN(r.rr, 1)}</b></span></div>
        <div class="fm-r2">fiyat ${fmP(r.p)} · ${r.durum === "OLUŞUYOR" ? `kırılıma <b>${fmPc(r.d_giris)}</b>` : `H1'e <b>${fmPc(r.d_h1)}</b>`} · stop ${fmPc(r.d_stop)}<span class="fm-qb"><i style="width:${Math.max(4, r.kalite)}%"></i></span><span class="muted">kalite ${r.kalite}</span></div></button>`;
    };
    setH(body, rows.length ? rows.slice(0, n).map(rowH).join("") : `<div class="empty">Filtrelere uyan formasyon yok.</div>`);
    if (more) { more.hidden = rows.length <= n; more.textContent = `Daha fazla göster (${fN(rows.length - n)})`; }
    if (note) {
      const miss = (M.missing || []).length;
      setH(note, `<b>Veri kaynakları (gerçek OHLCV, uydurma bar yok):</b> ${FM_TFS.map((t) => `<br>• <b>${FM_TFLL[t]}</b>: ${esc((M.src || {})[t] || "—")} — ${fN(((M.scan || {})[t] || {}).syms || 0)} hisse taranıyor${((M.scan || {})[t] || {}).short ? `, ${((M.scan || {})[t] || {}).short} hissede yetersiz geçmiş (&lt;25 bar, yeni halka arz vb.)` : ""}`).join("")}
        <br>• Evren ${fN(M.universe || 0)} hisse${miss ? ` · Yahoo verisi olmayan: ${esc((M.missing || []).join(", "))}` : ""}. İş Yatırım gün içi serisi yalnız kapanış içerdiği (gölge yok) için mum analizinde kullanılmaz.
        ${k === "mum" && d.bt_note ? `<br>• <b>Dürüstlük testi:</b> ${esc(d.bt_note)}` : ""}`);
    }
  }
  function fmDay(d) { return d ? `${d.slice(6, 8)}.${d.slice(4, 6)}.${d.slice(0, 4)}` : "—"; }
  document.addEventListener("click", (e) => {
    const v = e.target.closest("#view-fm_mum, #view-fm_grafik"); if (!v || !V127_READY) return;
    const k = v.id === "view-fm_grafik" ? "grafik" : "mum", f = fmS().f[k];
    const pre = e.target.closest("[data-fmpre]"); if (pre) { fmApplyPre(k, pre.dataset.fmpre); fmS()[k].n = 60; fmSave(k); fmCtl(k); fmRender(k); return; }
    const tf = e.target.closest("[data-fmtf]");
    if (tf) { const t = tf.dataset.fmtf; if (t === "*") f.tfs = f.tfs.length === FM_TFS.length ? [] : FM_TFS.slice(); else f.tfs = f.tfs.includes(t) ? f.tfs.filter((x) => x !== t) : FM_TFS.filter((x) => x === t || f.tfs.includes(x)); f.pre = ""; fmSave(k); fmCtl(k); fmRender(k); return; }
    const du = e.target.closest("[data-fmdur]"); if (du) { const x = du.dataset.fmdur; f.durum = f.durum.includes(x) ? f.durum.filter((y) => y !== x) : f.durum.concat([x]); f.pre = ""; fmSave(k); fmCtl(k); fmRender(k); return; }
    const fp = e.target.closest("[data-fmpat]"); if (fp) { f.pats = [fp.dataset.fmpat]; f.pre = ""; fmSave(k); fmCtl(k); fmRender(k); return; }
    const r = e.target.closest("[data-fmk]"); if (r) { const [s, t, p] = r.dataset.fmk.split("|"); fmProof(s, t, k, p); return; }
    if (e.target.closest("#" + fmPx(k) + "-more")) { fmS()[k].n += 80; fmRender(k); return; }
    if (e.target.closest("[data-fmwsave]")) { fmWatchSave(); return; }
    const wt = e.target.closest("[data-fmwtf]"); if (wt) { wt.classList.toggle("on"); return; }
  });
  document.addEventListener("change", (e) => {
    const el = e.target.closest("#view-fm_mum [data-fmf], #view-fm_grafik [data-fmf]"); if (!el || !V127_READY) return;
    const k = el.closest("#view-fm_grafik") ? "grafik" : "mum", f = fmS().f[k], key = el.dataset.fmf;
    if (key === "pat") { if (el.value !== "__multi") f.pats = el.value ? [el.value] : []; }
    else if (key === "hacim") f.hacim = !!el.checked;
    else if (key === "q") f.q = el.value;
    else if (["guven", "kalite", "rr", "uzak", "taze"].includes(key)) f[key] = +el.value;
    else f[key] = el.value;
    if (key !== "sort" && key !== "q") f.pre = "";
    fmS()[k].n = 60; fmSave(k); if (key !== "q") fmCtl(k); fmRender(k);
  });
  document.addEventListener("input", (e) => {
    const el = e.target.closest("#view-fm_mum .fm-q, #view-fm_grafik .fm-q"); if (!el || !V127_READY) return;
    const k = el.closest("#view-fm_grafik") ? "grafik" : "mum"; fmS().f[k].q = el.value; clearTimeout(fmS()._qt); fmS()._qt = setTimeout(() => fmRender(k), 200);
  });
  setInterval(() => { try { if (V127_READY && !document.hidden && (st.view === "fm_mum" || st.view === "fm_grafik")) fmLoad(fmKind(st.view), false); } catch (e) {} }, 20000);

  // ---------------------------------------------------------------- bildirim ayarı (motor: varsayılan KAPALI)
  async function fmWatchLoad() { try { fmS().w = await api("/api/formasyon/watch", { timeout: 10000 }); } catch (e) { fmS().w = fmS().w || { err: String(e.message || e) }; } fmWatchR(); }
  function fmWatchR() {
    ["mum", "grafik"].forEach((k) => { const el = $(fmPx(k) + "-nt"); if (el) setH(el, fmWatchH(k)); });
  }
  function fmWatchH(k) {
    const W = (fmS().w || {}).watch, w = W ? W[k] : null, nt = k === "mum" ? "formasyon_mum" : "formasyon_grafik";
    if (!w) return `<section class="card at-ntc fm-ntc"><div class="empty">Bildirim ayarı yükleniyor…</div></section>`;
    const sel = (id, arr, cur) => `<select class="pill-select" id="${id}">${arr.map(([v, l]) => `<option value="${v}" ${String(cur) === String(v) ? "selected" : ""}>${l}</option>`).join("")}</select>`;
    return `<section class="card at-ntc fm-ntc" data-fmw="${k}"><div class="card-h"><span class="card-title">BİLDİRİM · ${k === "mum" ? "🕯 MUM FORMASYONU" : "📐 GRAFİK FORMASYONU KIRILIMI"}</span><button type="button" class="btn-ghost sm nf-lnk" data-nflink="ayar">🔔 Tüm bildirim ayarları</button></div>
      ${NT[nt] ? ntRow(nt, false) : ""}
      <div class="at-wf"><label class="akk-ck"><input type="checkbox" id="fmw-on-${k}" ${w.on ? "checked" : ""}/> <span><b>Dedektör ${w.on ? "AÇIK" : "KAPALI"}</b></span></label>
        ${k === "mum" ? sel("fmw-g-" + k, [[3, "güven: Yüksek"], [2, "güven: Orta+"], [1, "güven: tümü"]], w.guven) : sel("fmw-g-" + k, [[80, "kalite ≥ 80"], [70, "kalite ≥ 70"], [60, "kalite ≥ 60"], [50, "kalite ≥ 50"]], w.kalite)}
        ${sel("fmw-y-" + k, [["all", "her iki yön"], ["U", "yalnız ▲ yükseliş"], ["D", "yalnız ▼ düşüş"]], w.yon)}
        ${k === "mum" ? `<label class="akk-ck"><input type="checkbox" id="fmw-h-${k}" ${w.hacim ? "checked" : ""}/> <span>yalnız hacim teyitli</span></label>` : ""}</div>
      <div class="fm-tfs fm-wtfs"><span class="fm-lb">Periyotlar</span>${FM_TFS.map((t) => `<button type="button" class="fm-tf ${w.tfs.includes(t) ? "on" : ""}" data-fmwtf="${t}">${FM_TFL[t]}</button>`).join("")}<button type="button" class="btn-ghost sm" data-fmwsave="${k}">💾 Kaydet</button></div>
      <div class="src-note">${esc((fmS().w || {}).note || "")} Bildirim modu (KAPALI / GÖRÜNTÜLE / BİLDİRİM) yukarıdaki satırdan. Gönderilen: ${fN(((fmS().w || {}).emitted || {})[nt] || 0)}.${(fmS().w || {}).err ? " (" + esc(fmS().w.err) + ")" : ""}</div></section>`;
  }
  async function fmWatchSave() {
    const body = {};
    ["mum", "grafik"].forEach((k) => {
      const on = $("fmw-on-" + k); if (!on) return;
      const tfs = [...document.querySelectorAll(`[data-fmw="${k}"] [data-fmwtf].on`)].map((b) => b.dataset.fmwtf);
      body[k] = { on: !!on.checked, tfs, yon: ($("fmw-y-" + k) || {}).value || "all" };
      if (k === "mum") { body[k].guven = +(($("fmw-g-" + k) || {}).value || 3); body[k].hacim = !!(($("fmw-h-" + k) || {}).checked); }
      else body[k].kalite = +(($("fmw-g-" + k) || {}).value || 70);
    });
    try { fmS().w = await api("/api/formasyon/watch", { method: "POST", body: JSON.stringify(body), headers: { "Content-Type": "application/json" }, timeout: 15000 }); toast("Formasyon bildirim ayarı kaydedildi ✓", 1600); }
    catch (e) { toast("Kaydedilemedi: " + (e.message || e), 3000); }
    fmWatchR();
  }

  // ---------------------------------------------------------------- KANIT: animasyonlu gösterim (canvas)
  function fmOv() {
    let ov = $("fmk-ov");
    if (ov) return ov;
    ov = document.createElement("div"); ov.id = "fmk-ov"; ov.className = "fmk-ov"; ov.hidden = true;
    ov.innerHTML = `<div class="fmk-sh" role="dialog" aria-modal="true"><div class="fmk-h"><div class="fmk-t" id="fmk-t">—</div><button type="button" class="fmk-x" data-fmkx="1" aria-label="Kapat">✕</button></div>
      <div class="fmk-cvw"><canvas id="fmk-cv"></canvas></div>
      <div class="fmk-bar"><button type="button" class="btn-ghost sm" data-fmkplay="1">▶ Tekrar oynat</button><button type="button" class="btn-ghost sm" data-fmkgo="1">Hisseye git ›</button><span class="muted sm" id="fmk-st"></span></div>
      <div class="fmk-b" id="fmk-b"></div></div>`;
    document.body.appendChild(ov);
    ov.addEventListener("click", (e) => {
      if (e.target === ov || e.target.closest("[data-fmkx]")) { fmClose(); return; }
      if (e.target.closest("[data-fmkplay]")) { fmPlay(); return; }
      if (e.target.closest("[data-fmkgo]") && FMK && (FMK.K || FMK.ob)) { const s = (FMK.K || FMK.ob).sym; fmClose(); openStock(s); }
    });
    return ov;
  }
  function fmClose() { const ov = $("fmk-ov"); if (ov) ov.hidden = true; document.body.classList.remove("fmk-open"); if (FMK) { cancelAnimationFrame(FMK.raf); FMK.raf = 0; } }
  async function fmProof(sym, tf, kind, k) {
    if (!V127_READY) return;
    const ov = fmOv(); ov.hidden = false; document.body.classList.add("fmk-open");
    FMK = FMK || {}; cancelAnimationFrame(FMK.raf); FMK.K = null; FMK.ob = null;
    setH($("fmk-t"), `<b>${esc(sym)}</b> · ${FM_TFLL[tf] || tf} · yükleniyor…`); setH($("fmk-b"), ""); $("fmk-st").textContent = "";
    const cv = $("fmk-cv"), g = cv.getContext("2d"); g.clearRect(0, 0, cv.width, cv.height);
    let K;
    try { K = await api(`/api/formasyon/kanit?sym=${encodeURIComponent(sym)}&tf=${tf}&kind=${kind}&k=${encodeURIComponent(k)}`, { timeout: 20000 }); }
    catch (e) { setH($("fmk-b"), `<div class="empty">Alınamadı: ${esc(e.message || e)}</div>`); return; }
    if (!K.ok) { setH($("fmk-t"), `<b>${esc(sym)}</b> · ${FM_TFLL[tf] || tf}`); setH($("fmk-b"), `<div class="empty">${esc(K.error || "—")} — listeyi yenileyin.</div>`); return; }
    FMK.K = K; FMK.map = fmPrep(K);
    const h = K.hit, isM = kind === "mum";
    setH($("fmk-t"), `<b>${esc(sym)}</b> · ${esc(K.tfl)} · <span class="fm-nm ${fmCls(h.yon)}">${fmAr(h.yon)} ${esc(h.ad)}</span> ${isM ? `<span class="fm-b ${fmCls(h.yon)}">${FM_YON[h.yon]}</span><span class="fm-b">${esc(h.tip)}</span><span class="fm-rel r${h.guven}">güven ${FM_REL[h.guven]}</span>`
      : `<span class="fm-dur ${h.durum === "KIRILDI" ? "kir" : h.durum === "OLUŞUYOR" ? "olu" : "bas"} ${fmCls(h.yon)}">${h.durum}</span><span class="fm-b">kalite ${h.kalite}</span>`}`);
    setH($("fmk-b"), fmProofBody(K));
    fmPlay();
  }
  function fmPrep(K) {
    const B = K.bars, idx = {}; B.t.forEach((t, i) => { idx[t] = i; });
    const near = (t) => { if (t == null) return null; if (idx[t] != null) return idx[t]; let best = null; for (let i = 0; i < B.t.length; i++) if (B.t[i] <= t) best = i; return best; };
    return { idx, near };
  }
  function fmProofBody(K) {
    const h = K.hit, B = K.bars, tf = K.tf, isM = K.kind === "mum";
    const tr = (i, lbl) => `<tr><td>${lbl ? `<b>${esc(lbl)}</b> ` : ""}${fmTime(B.t[i], tf)}</td><td>${fmP(B.o[i])}</td><td>${fmP(B.h[i])}</td><td>${fmP(B.l[i])}</td><td class="${B.c[i] >= B.o[i] ? "pos" : "neg"}">${fmP(B.c[i])}</td><td>${fShort ? fShort(B.v[i]) : fN(B.v[i])}</td></tr>`;
    const head = `<tr><th>Bar</th><th>Açılış</th><th>Yüksek</th><th>Düşük</th><th>Kapanış</th><th>Hacim</th></tr>`;
    let ohlc = "";
    if (isM) {
      const i1 = B.t.length - 1, i0 = Math.max(0, i1 - h.nb + 1);
      const rows = []; if (i0 - 1 >= 0) rows.push(tr(i0 - 1, "önceki")); for (let i = i0; i <= i1; i++) rows.push(tr(i, h.nb > 1 ? `${i - i0 + 1}.` : "formasyon"));
      ohlc = `<div class="fmk-tbw"><table class="fmk-tb">${head}${rows.join("")}</table></div>`;
    } else {
      const M = FMK.map, rows = (h.pts || []).map((p) => { const i = M.near(p[0]); return `<tr><td><b>${esc(p[2] || "pivot")}</b></td><td>${i != null ? fmTime(B.t[i], tf) : "—"}</td><td>${fmP(p[1])}</td></tr>`; }).join("");
      const bi = h.bo_t != null ? M.near(h.bo_t) : null;
      ohlc = `<div class="fmk-tbw"><table class="fmk-tb"><tr><th>Nokta</th><th>Zaman</th><th>Fiyat</th></tr>${rows}</table></div>${bi != null ? `<div class="fmk-sub">Kırılım barı</div><div class="fmk-tbw"><table class="fmk-tb">${head}${tr(bi, "kırılım")}</table></div>` : ""}`;
    }
    const ck = (h.kontrol || []).map((x) => `<li><span class="ok">✓</span> ${esc(x)}</li>`).join("")
      + (isM ? `<li><span class="${h.hacim ? "ok" : "no"}">${h.hacim ? "✓" : "✗"}</span> Hacim teyidi: son bar hacmi ${h.hr ? fN(h.hr, 2) + "×" : "—"} son 20 bar ortalaması (eşik 1,2×)</li>`
        : `<li><span class="${h.hacim ? "ok" : "no"}">${h.hacim ? "✓" : "✗"}</span> Kırılım hacmi ${h.hr ? fN(h.hr, 2) + "×" : "—"} ortalama (eşik 1,5×)</li>`)
      + `<li><span class="ok">✓</span> Son KAPANMIŞ bar: ${fmTime(B.t[B.t.length - 1], tf, true)}</li>`;
    const lv = isM ? `<div class="fmk-lv"><span>Kapanış <b>${fmP(h.c)}</b></span><span class="pos">Teyit ${h.yon === "D" ? "&lt;" : "&gt;"} <b>${fmP(h.yon === "D" ? h.gecersiz : h.teyit)}</b></span><span class="neg">Geçersiz <b>${fmP(h.yon === "D" ? h.teyit : h.gecersiz)}</b></span><span>Skor <b>${h.skor}</b></span></div>`
      : `<div class="fmk-lv"><span>Giriş/kırılım <b>${fmP(h.giris)}</b> <small>${fmPc(h.d_giris)}</small></span><span class="neg">STOP <b>${fmP(h.stop)}</b> <small>${fmPc(h.d_stop)}</small></span><span class="pos">HEDEF 1 <b>${fmP(h.h1)}</b> <small>${fmPc(h.d_h1)}</small></span><span class="pos">HEDEF 2 <b>${fmP(h.h2)}</b></span><span>R/R <b>${fN(h.rr, 2)}</b></span>${h.bo_t ? `<span>Kırılım <b>${fmTime(h.bo_t, tf)}</b></span>` : ""}${h.h1_ok ? `<span class="pos"><b>HEDEF 1 ✓</b></span>` : ""}</div>`;
    const bt = K.bt ? `<div class="fmk-bt"><b>Dürüstlük testi (günlük barlar, son ~1 yıl, tüm hisseler):</b> ${fN(K.bt.n)} örnek · ertesi gün formasyon yönünde %${fN(K.bt.w1, 1)} (ort. ${fmPc(K.bt.r1, 2)}) · 5 gün %${fN(K.bt.w5, 1)} (ort. ${fmPc(K.bt.r5, 2)}) · ertesi gün teyit %${fN(K.bt.cf, 1)}${K.bt.w1 < 50 ? " — <b>tarihsel olarak yazı-turadan iyi değil</b>, teyit bekleyin." : ""}</div>` : "";
    return `<div class="fmk-et"><b>Etkisi:</b> ${esc((h.etki || "").replace(/ \(%[+-]?\d+(?:[.,]\d+)?\)/g, ""))}</div>${lv}${bt}<div class="fmk-sub">Kural kontrolleri (kanıt)</div><ul class="fmk-ck">${ck}</ul><div class="fmk-sub">${isM ? "Formasyon barları (OHLC)" : "Pivotlar"}</div>${ohlc}
      <div class="src-note">Kaynak: ${esc(K.src || "")}${K.today_src ? ` · bugün: ${esc(K.today_src)}` : ""}. ${esc(K.closed_note || "")}</div>`;
  }
  function fmPlay() { if (!FMK || !(FMK.K || FMK.ob)) return; cancelAnimationFrame(FMK.raf); FMK.t0 = performance.now(); FMK.frozen = null; const step = () => { const t = performance.now() - FMK.t0; const end = FMK.ob ? obDraw($("fmk-cv"), FMK.ob, t, false) : fmDraw($("fmk-cv"), FMK.K, FMK.map, t, false); $("fmk-st").textContent = t < end ? "oynatılıyor…" : "✓ kanıt tamam"; if (t < end + 50) FMK.raf = requestAnimationFrame(step); }; FMK.raf = requestAnimationFrame(step); }
  function fmSeek(ms) { if (!FMK || !(FMK.K || FMK.ob)) return; cancelAnimationFrame(FMK.raf); const end = FMK.ob ? obDraw($("fmk-cv"), FMK.ob, ms, false) : fmDraw($("fmk-cv"), FMK.K, FMK.map, ms, false); $("fmk-st").textContent = ms < end ? "duraklatıldı (ara kare)" : "✓ kanıt tamam"; }
  function fmDraw(cv, K, M, T, thumb, opt) {
    const dpr = window.devicePixelRatio || 1, W = cv.clientWidth || 360, H = cv.clientHeight || 240;
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    const B = K.bars, h = K.hit, N = B.t.length, isM = K.kind === "mum";
    const pl = thumb ? 2 : 6, pr = thumb ? 2 : 60, pt = thumb ? 4 : 16, pb = thumb ? 4 : 20;
    let lo = Math.min(...B.l), hi = Math.max(...B.h);
    const lvl = isM ? [h.teyit, h.gecersiz] : [h.giris, h.stop, h.h1].concat(thumb ? [] : [h.h2]);
    lvl.forEach((v) => { if (isNum(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); } });
    const pad = (hi - lo) * 0.06 || 1; lo -= pad; hi += pad;
    const cw = W - pl - pr, ch = H - pt - pb, slot = cw / N, bw = Math.max(1, Math.min(14, slot * 0.66));
    const X = (i) => pl + slot * (i + 0.5), Y = (p) => pt + ((hi - p) / (hi - lo)) * ch;
    const cl = (x) => Math.max(0, Math.min(1, x));
    const css = getComputedStyle(document.documentElement);
    const UP = "#22c55e", DN = "#ef4444", GOLD = "#d4a64a", MUT = "#8b929b";
    // ızgara
    if (!thumb) {
      g.strokeStyle = "rgba(255,255,255,.06)"; g.lineWidth = 1; g.fillStyle = MUT; g.font = "10px system-ui, sans-serif"; g.textAlign = "left";
      for (let k = 0; k <= 4; k++) { const p = lo + ((hi - lo) * k) / 4, y = Y(p); g.beginPath(); g.moveTo(pl, y); g.lineTo(W - pr, y); g.stroke(); g.fillText(fmP(p), W - pr + 4, y + 3); }
      g.textAlign = "center"; const nt = Math.max(2, Math.min(4, Math.floor(cw / 110)));
      for (let k = 0; k < nt; k++) { const i = Math.round(((N - 1) * (k + 0.5)) / nt); g.fillText(fmTime(B.t[i], K.tf), X(i), H - 6); }
    }
    const candle = (i, alpha, prog, glow) => {
      const o = B.o[i], c0 = B.c[i], c = o + (c0 - o) * prog, up = c0 >= o, col = up ? UP : DN;
      g.globalAlpha = alpha; g.strokeStyle = col; g.fillStyle = col; g.lineWidth = 1;
      const x = X(i), hh = o + (B.h[i] - o) * prog, ll = o + (B.l[i] - o) * prog;
      g.beginPath(); g.moveTo(x, Y(Math.max(hh, o, c))); g.lineTo(x, Y(Math.min(ll, o, c))); g.stroke();
      const y1 = Y(Math.max(o, c)), y2 = Y(Math.min(o, c)); g.fillRect(x - bw / 2, y1, bw, Math.max(1, y2 - y1));
      if (glow) { g.globalAlpha = alpha * 0.9; g.strokeStyle = GOLD; g.lineWidth = 1.5; g.strokeRect(x - bw / 2 - 3, Y(B.h[i]) - 3, bw + 6, Y(B.l[i]) - Y(B.h[i]) + 6); }
      g.globalAlpha = 1;
    };
    const hline = (p, col, prog, label, dash, x0) => {
      if (!isNum(p)) return; const xa = x0 != null ? x0 : pl, xb = xa + (W - pr - xa) * cl(prog), y = Y(p);
      g.strokeStyle = col; g.lineWidth = 1.4; g.setLineDash(dash ? [5, 4] : []); g.beginPath(); g.moveTo(xa, y); g.lineTo(xb, y); g.stroke(); g.setLineDash([]);
      if (!thumb && prog >= 1 && label) { g.font = "bold 9.5px system-ui, sans-serif"; const tw = Math.max(52, g.measureText(label).width + 8), xs = Math.min(W - pr + 1, W - tw - 1); g.fillStyle = col; g.fillRect(xs, y - 8, tw, 16); g.fillStyle = "#0b0d0f"; g.textAlign = "left"; g.fillText(label, xs + 4, y + 3); }
    };
    const tag = (x, y, txt, col, alpha) => {
      g.globalAlpha = alpha; g.font = `bold ${thumb ? 9 : 11}px system-ui, sans-serif`; const tw = g.measureText(txt).width + 10;
      const xx = Math.max(pl, Math.min(W - pr - tw, x - tw / 2)); g.fillStyle = "rgba(11,13,15,.88)"; g.strokeStyle = col; g.lineWidth = 1;
      g.fillRect(xx, y - 9, tw, 18); g.strokeRect(xx, y - 9, tw, 18); g.fillStyle = col; g.textAlign = "left"; g.fillText(txt, xx + 5, y + 4); g.globalAlpha = 1;
    };
    if (isM) {
      const i1 = N - 1, i0 = Math.max(0, i1 - (h.nb || 1) + 1), col = h.yon === "U" ? UP : h.yon === "D" ? DN : GOLD;
      const SQ = opt && opt.seq ? 1100 : 0, D0 = SQ || 500;   // v1.28.0 seq: önceki barlar tek tek çizilir
      if (SQ) { const nS = Math.ceil(i0 * cl(T / SQ)); for (let i = 0; i < nS; i++) candle(i, 0.7, i === nS - 1 && T < SQ ? cl((T / SQ) * i0 - i) : 1, false); }
      else { const a0 = cl(T / 500); for (let i = 0; i < i0; i++) candle(i, 0.55 * a0, 1, false); }
      const t1 = D0 + (i1 - i0 + 1) * 520;
      for (let i = i0; i <= i1; i++) { const st0 = D0 + (i - i0) * 520; if (T >= st0) { const p = cl((T - st0) / 420); if (!thumb && p < 1) { g.fillStyle = "rgba(212,166,74,.12)"; g.fillRect(X(i) - slot / 2, pt, slot, ch); } candle(i, 1, p, true); } }
      if (T >= t1) {
        const a = cl((T - t1) / 380), hiP = Math.max(...B.h.slice(i0)), loP = Math.min(...B.l.slice(i0)), xm = (X(i0) + X(i1)) / 2;
        g.globalAlpha = a; g.fillStyle = col; g.font = "bold 18px system-ui, sans-serif"; g.textAlign = "center";
        const off = (1 - a) * 12;
        if (h.yon === "D") g.fillText("▼", xm, Y(hiP) - 8 - off); else if (h.yon === "U") g.fillText("▲", xm, Y(loP) + 22 + off); else g.fillText("◆", xm, Y(loP) + 22);
        g.globalAlpha = 1;
        if (!thumb) tag(xm, h.yon === "U" ? Math.max(pt + 10, Y(hiP) - 16) : Math.min(H - pb - 10, Y(loP) + 36), h.ad, col, a);
      }
      const t2 = t1 + 420;
      if (T >= t2) {
        const p = cl((T - t2) / 520), x0 = X(i0) - slot / 2;
        const up = h.yon !== "D";
        hline(up ? h.teyit : h.gecersiz, UP, p, (up ? "Teyit " : "Teyit ") + fmP(up ? h.teyit : h.gecersiz), true, x0);
        if (h.yon !== "N") hline(up ? h.gecersiz : h.teyit, DN, p, "Geçersiz " + fmP(up ? h.gecersiz : h.teyit), true, x0);
        else hline(h.gecersiz, DN, p, "Alt " + fmP(h.gecersiz), true, x0);
      }
      return t2 + 600;
    }
    // ---- grafik formasyonu
    const rv = cl(T / 800), nShow = Math.ceil(N * rv);
    for (let i = 0; i < nShow; i++) candle(i, 0.8, 1, false);
    const pts = (h.pts || []).map((p) => ({ i: M.near(p[0]), p: p[1], l: p[2] })).filter((p) => p.i != null);
    const col = h.yon === "U" ? UP : h.yon === "D" ? DN : GOLD;
    let t = 800;
    // pivot bağlantıları
    const segT = 360;
    if (pts.length) {
      g.strokeStyle = "#a78bfa"; g.lineWidth = thumb ? 1.4 : 2;
      for (let k = 0; k < pts.length; k++) {
        const s0 = t + k * segT;
        if (T >= s0) {
          if (k > 0) { const a = pts[k - 1], b = pts[k], p = cl((T - s0) / segT); g.beginPath(); g.moveTo(X(a.i), Y(a.p)); g.lineTo(X(a.i) + (X(b.i) - X(a.i)) * p, Y(a.p) + (Y(b.p) - Y(a.p)) * p); g.stroke(); }
          g.fillStyle = "#a78bfa"; g.beginPath(); g.arc(X(pts[k].i), Y(pts[k].p), thumb ? 2 : 3.5, 0, Math.PI * 2); g.fill();
          if (!thumb && pts[k].l && T >= s0 + segT * 0.6) { const isHigh = pts.length > 1 && (k === 0 ? pts[0].p > pts[1].p : pts[k].p > pts[k - 1].p); tag(X(pts[k].i), Y(pts[k].p) + (isHigh ? -16 : 16), pts[k].l, "#c4b5fd", cl((T - s0 - segT * 0.6) / 200)); }
        }
      }
      t += pts.length * segT;
    }
    // çizgiler (boyun / direnç / destek / eğri)
    const lines = h.lines || [];
    lines.forEach((ln, k) => {
      const s0 = t + k * 480; if (T < s0) return; const p = cl((T - s0) / 480);
      if (ln[0] === "curve") { const cp = ln[1].map(([tt, pp]) => ({ i: M.near(tt), p: pp })).filter((q) => q.i != null); g.strokeStyle = GOLD; g.lineWidth = 2; g.beginPath(); const m = Math.max(1, Math.round(cp.length * p)); cp.slice(0, m).forEach((q, j) => (j ? g.lineTo(X(q.i), Y(q.p)) : g.moveTo(X(q.i), Y(q.p)))); g.stroke(); return; }
      const i1 = M.near(ln[0]), i2 = M.near(ln[2]); if (i1 == null || i2 == null) return;
      const c2 = ln[4] === "neck" ? GOLD : ln[4] === "res" ? "#f87171" : ln[4] === "sup" ? "#4ade80" : "#a78bfa";
      g.strokeStyle = c2; g.lineWidth = thumb ? 1.2 : 1.8; g.setLineDash(ln[4] === "pole" ? [3, 3] : []);
      g.beginPath(); g.moveTo(X(i1), Y(ln[1])); g.lineTo(X(i1) + (X(i2) - X(i1)) * p, Y(ln[1]) + (Y(ln[3]) - Y(ln[1])) * p); g.stroke(); g.setLineDash([]);
      if (!thumb && p >= 1 && ln[5]) { g.fillStyle = c2; g.font = "10px system-ui, sans-serif"; g.textAlign = "left"; g.fillText(ln[5], Math.min(X(i2) - 60, W - pr - 70), Y(ln[3]) - 5); }
    });
    t += lines.length * 480;
    // kırılım barı yanıp söner
    const bi = h.bo_t != null ? M.near(h.bo_t) : null;
    if (bi != null) {
      if (T >= t) {
        const p = (T - t) / 900, on = p < 1 ? Math.abs(Math.sin(p * Math.PI * 3)) : 0.35;
        g.fillStyle = `rgba(250,204,21,${0.12 + 0.35 * on})`; g.fillRect(X(bi) - slot / 2 - 1, pt, slot + 2, ch);
        candle(bi, 1, 1, true);
        if (!thumb && p >= 0.3) tag(X(bi), pt + 10, h.durum === "BAŞARISIZ" ? "KIRILIM (geri alındı)" : "KIRILIM", "#facc15", cl((p - 0.3) / 0.4));
      }
      t += 900;
    }
    // seviyeler
    const x0 = X(bi != null ? bi : Math.max(0, N - Math.min(N, 12)));
    const L = [[h.giris, GOLD, "Giriş " + fmP(h.giris), false], [h.stop, DN, "STOP " + fmP(h.stop), true], [h.h1, UP, "H1 " + fmP(h.h1), true]].concat(thumb ? [] : [[h.h2, "#86efac", "H2 " + fmP(h.h2), true]]);
    L.forEach((x, k) => { const s0 = t + k * 300; if (T >= s0) hline(x[0], x[1], (T - s0) / 300, x[2], x[3], x0); });
    t += L.length * 300;
    // hedef projeksiyonu (ok + bölge)
    if (T >= t && isNum(h.giris) && isNum(h.h1)) {
      const p = cl((T - t) / 700), xa = Math.min(W - pr - 14, X(N - 1) + Math.min(slot * 2, 18)), ya = Y(h.giris), yb = ya + (Y(h.h1) - ya) * p;
      g.fillStyle = h.h1 > h.giris ? "rgba(34,197,94,.10)" : "rgba(239,68,68,.10)"; g.fillRect(x0, Math.min(ya, yb), W - pr - x0, Math.abs(yb - ya));
      g.strokeStyle = col; g.lineWidth = 2.2; g.beginPath(); g.moveTo(xa, ya); g.lineTo(xa, yb); g.stroke();
      if (p > 0.15) { const d = h.h1 > h.giris ? -1 : 1; g.fillStyle = col; g.beginPath(); g.moveTo(xa, yb); g.lineTo(xa - 5, yb - d * 8); g.lineTo(xa + 5, yb - d * 8); g.closePath(); g.fill(); }
      if (!thumb && p >= 1) tag(Math.max(pl + 60, xa - 70), (ya + Y(h.h1)) / 2, `H1 girişten ${fmPc(((h.h1 - h.giris) / h.giris) * 100)}`, col, 1);
    }
    return t + 800;
  }

  // ---------------------------------------------------------------- Özet → FORMASYONLAR kartı + çip + grafik işaretleri
  function fmzS() { if (!FMZ) FMZ = { sym: null, d: null, ts: 0, busy: false, K: null, raf: 0, mk: LS.get("fmMk", false) }; return FMZ; }
  async function fmzLoad(force) {
    const Z = fmzS(), sym = st.sym;
    if (Z.busy || (!force && Z.sym === sym && Date.now() - Z.ts < 60000)) return;
    if (Z.sym !== sym) { Z.d = null; Z.K = null; Z.A = {}; Z.cache = {}; Z.ci = {}; Z.sym = sym; fmzRender(); }
    Z.busy = true;
    try { const d = await api(`/api/formasyon/hisse/${encodeURIComponent(sym)}`, { timeout: 15000 }); if (sym !== st.sym) return; Z.d = d; Z.ts = Date.now(); }
    catch (e) { if (sym === st.sym) Z.err = String(e.message || e); }
    finally { Z.busy = false; }
    fmzRender(); fmMarkers(); try { obOv(); } catch (e) {}
    fmzSelLoad();   // v1.28.0 seçili periyot: grafik + mum + order block kutuları
  }
  function fmzRender() {
    const el = $("fmz"); if (!el) return;
    const Z = fmzS(), d = Z.d;
    if (!d) { setH(el, `<section class="card fmz"><div class="card-h"><span class="card-title">FORMASYONLAR</span></div><div class="empty">${Z.err ? "Alınamadı: " + esc(Z.err) : "Formasyonlar yükleniyor…"}</div></section>`); return; }
    if (!d.ready) { setH(el, `<section class="card fmz"><div class="card-h"><span class="card-title">FORMASYONLAR</span></div><div class="empty">Formasyon motoru hazırlanıyor…</div></section>`); return; }
    const badge = (tf, kind, x) => `<button type="button" class="fmz-bd ${fmCls(x.yon)} ${kind === "grafik" ? "g" : ""}" data-fmzk="${tf}|${kind}|${x.k}" title="${esc(x.ad)}">${kind === "grafik" ? "📐" : "🕯"}${fmAr(x.yon)} ${esc(x.ad)}${kind === "grafik" ? ` <small>${x.durum === "KIRILDI" ? "kırıldı" : x.durum === "OLUŞUYOR" ? "oluşuyor" : "başarısız"}</small>` : ""}</button>`;
    const grid = FM_TFS.map((tf) => {
      const r = d.tfs[tf];
      if (!r) return `<div class="fmz-row"><span class="fmz-tf">${FM_TFL[tf]}</span><span class="muted sm">veri yok</span></div>`;
      const c = r.c.filter((x) => x.yon !== "N" || x.guven >= 1).sort((a, b) => b.guven - a.guven).slice(0, 3);
      const gg = r.g.slice().sort((a, b) => (a.durum === "BAŞARISIZ") - (b.durum === "BAŞARISIZ") || b.kalite - a.kalite).slice(0, 2);
      const u = r.c.filter((x) => x.yon === "U").length + r.g.filter((x) => x.yon === "U" && x.durum !== "BAŞARISIZ").length;
      const dn = r.c.filter((x) => x.yon === "D").length + r.g.filter((x) => x.yon === "D" && x.durum !== "BAŞARISIZ").length;
      return `<div class="fmz-row"><span class="fmz-tf ${fmzSig(r).cls}">${FM_TFL[tf]}<small>${u ? `▲${u}` : ""}${dn ? ` ▼${dn}` : ""}</small></span><div class="fmz-bds">${c.map((x) => badge(tf, "mum", x)).join("")}${gg.map((x) => badge(tf, "grafik", x)).join("")}${!c.length && !gg.length ? `<span class="muted sm">—</span>` : ""}</div></div>`;
    }).join("");
    const tfSel = fmzTf();   // v1.28.0 periyot sekmeleri (seçili olan vurgulu; oturumda hatırlanır)
    const mini = `<div class="fmz-mini" role="tablist" aria-label="Formasyon periyodu">${FM_TFS.map((tf) => { const S = fmzSig(d.tfs[tf]); return `<button type="button" role="tab" aria-selected="${tf === tfSel}" class="fmz-mc ${S.cls}${tf === tfSel ? " sel" : ""}" data-fmztf="${tf}" data-fmzsig="${S.k}" title="${FM_TFLL[tf]}: ${esc(S.tt)}" aria-label="${FM_TFLL[tf]}: ${esc(S.tt)}"><b>${FM_TFL[tf]}</b><i>${S.gl}</i></button>`; }).join("")}</div><div class="fmz-lg" aria-hidden="true"><span class="up">▲▼ aktif grafik</span><span class="up fmz-c">▴▾ yalnız mum</span><span class="fmz-h">✓ hedef 1 tamam</span><span class="fmz-f">△▽ başarısız</span><span>• yok</span></div>`;
    setH(el, `<section class="card fmz"><div class="card-h"><span class="card-title">FORMASYONLAR</span><label class="akk-ck fmz-mk"><input type="checkbox" id="fmz-mk" ${Z.mk ? "checked" : ""}/> <span>Grafikte işaretle</span></label></div>
      ${mini}<div id="fmz-sel">${fmzSelHtml(d, tfSel)}</div><div class="fmz-grid">${grid}</div>${d.yorum ? `<div class="fmz-y">${esc(d.yorum)}</div>` : ""}
      <div class="src-note">Son KAPANMIŞ bara göre · periyoda dokun → üstteki 3 kutu o periyoda geçer (▶ tekrar oynat) · 🕯 mum, 📐 grafik · yeşil = yükseliş, kırmızı = düşüş · rozete dokun → kanıt.</div><div class="fmz-go"><button type="button" class="fm-chip sm" data-fmzgo="fm_mum">🕯 Mum taraması ›</button><button type="button" class="fm-chip sm" data-fmzgo="fm_grafik">📐 Grafik taraması ›</button></div></section>`);
    { const A = Z.A || {}; for (const k in A) if (A[k]) A[k].drawn = false; }
    fmzAnim();
  }
  function fmzThumb() { fmzAnim(); }   // v1.28.0: ortak döngü (fmzAnim)
  const fmShort = (s) => { s = String(s || "").replace(/\s*\(.*?\)\s*/g, " ").trim(); return s.length > 16 ? s.slice(0, 15) + "…" : s; };
  function fmMarkers() {
    if (!V127_READY || typeof cSeries === "undefined" || !cSeries) return;
    const Z = fmzS();
    try {
      const map = { "5m": "5m", "15m": "15m", "1h": "60m", "4h": "4h", "1d": "1d", "1w": "1w" }, tf = map[st.tf];
      if (!Z.mk || !Z.d || !Z.d.tfs || !tf || Z.sym !== st.sym || !Z.d.tfs[tf] || !CHL.bars.length) { cSeries.setMarkers([]); return; }
      const r = Z.d.tfs[tf], bars = CHL.bars, daily = typeof bars[0].time === "string";
      const toT = (t) => { if (daily) return new Date((t + 3 * 3600) * 1000).toISOString().slice(0, 10); return t + 3 * 3600; };
      const near = (t) => { const x = toT(t); let best = null; for (const b of bars) { if (b.time <= x) best = b.time; else break; } return best; };
      const mk = [];
      r.c.forEach((x) => { const tm = near(x.t); if (tm == null) return; mk.push({ time: tm, position: x.yon === "D" ? "aboveBar" : "belowBar", color: x.yon === "U" ? "#22c55e" : x.yon === "D" ? "#ef4444" : "#d4a64a", shape: x.yon === "U" ? "arrowUp" : x.yon === "D" ? "arrowDown" : "circle", text: "🕯 " + fmShort(x.ad) }); });
      r.g.forEach((x) => { if (!x.bo_t) return; const tm = near(x.bo_t); if (tm == null) return; mk.push({ time: tm, position: x.yon === "D" ? "aboveBar" : "belowBar", color: x.yon === "U" ? "#4ade80" : "#f87171", shape: "square", text: "📐 " + fmShort(x.ad) + (x.durum === "BAŞARISIZ" ? " ✗" : " kırılım") }); });
      mk.sort((a, b) => (a.time < b.time ? -1 : a.time > b.time ? 1 : 0));
      cSeries.setMarkers(mk);
    } catch (e) { try { cSeries.setMarkers([]); } catch (x) {} }
  }
  function fmChipGo() {
    const b = fmzS().d && fmzS().d.best;
    if (b) fmProof(st.sym, b.tf, "grafik", b.k);
    else { const el = $("fmz"); if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 70, behavior: "smooth" }); }
  }
  document.addEventListener("click", (e) => {
    const z = e.target.closest("#fmz"); if (!z || !V127_READY) return;
    if (fmzClick(e)) return;   // v1.28.0 periyot sekmesi · ▶ · +N · order block
    const k = e.target.closest("[data-fmzk]"); if (k) { const [tf, kind, p] = k.dataset.fmzk.split("|"); fmProof(st.sym, tf, kind, p); return; }
    const gv = e.target.closest("[data-fmzgo]"); if (gv) { go(gv.dataset.fmzgo); return; }
  });
  document.addEventListener("change", (e) => { if (e.target && e.target.id === "fmz-mk") { fmzS().mk = !!e.target.checked; LS.set("fmMk", fmzS().mk); fmMarkers(); } });
  let fmzLast = "";
  setInterval(() => {
    try {
      if (!V127_READY || document.hidden) return;
      const on = st.view === "stock" && st.tab === "ozet", key = st.sym + "|" + on;
      if (on && (key !== fmzLast || Date.now() - fmzS().ts > 60000)) fmzLoad(key !== fmzLast);
      fmzLast = key;
    } catch (e) {}
  }, 1000);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && $("fmk-ov") && !$("fmk-ov").hidden) fmClose(); });

  // ------------------------------------------------------- v1.28.0 FORMASYONLAR: periyot sekmeleri + AKTİF MUM + ORDER BLOCK
  // Periyot hücresine dokun → altındaki 3 kutu (grafik formasyonu · mum formasyonu · order block) o periyoda geçer ve animasyon baştan oynar.
  // Seçim oturum boyunca hatırlanır (sessionStorage); seçim yoksa en güçlü grafik formasyonunun periyodu. Sessiz başka periyoda düşme yok.
  const FMZ_SS = "fmzTf";
  function fmzTf() {
    const d = fmzS().d; let t = null;
    try { t = sessionStorage.getItem(FMZ_SS); } catch (e) {}
    if (FM_TFS.includes(t)) return t;
    if (d && d.best && FM_TFS.includes(d.best.tf)) return d.best.tf;
    if (d && d.tfs) { const f = FM_TFS.slice().reverse().find((x) => d.tfs[x] && (d.tfs[x].g.length || d.tfs[x].c.length)); if (f) return f; }
    return "1d";
  }
  const fmzGsc = (x) => x.kalite + (x.durum === "KIRILDI" ? 8 : 0);   // motorun best_chart sıralaması (periyot ağırlığı aynı periyotta sabit)
  function fmzPickG(r) { return r ? r.g.filter((x) => x.durum !== "BAŞARISIZ" && !x.h1_ok).sort((a, b) => fmzGsc(b) - fmzGsc(a))[0] || null : null; }
  function fmzPickC(r) { return r ? r.c.slice().sort((a, b) => b.skor - a.skor || b.guven - a.guven) : []; }
  // v1.30.1 periyot sekmesi işareti = o periyodun EN GÜÇLÜ sinyali, kartlarla AYNI seçim mantığı (önceden tüm mum + grafik formasyonlarının
  // yukarı/aşağı sayım oylamasıydı: zıt yönlüler birbirini götürüp aktif grafik formasyonu varken "·" çıkabiliyordu; başarısızlar ise hiç görünmüyordu).
  // Öncelik: aktif grafik (EN GÜÇLÜ AKTİF kartındaki) ▲/▼ > yalnız aktif mum ▴/▾ > hedef 1 tamam ✓ > başarısız △/▽ (amber) > yok •
  function fmzSig(r) {
    const L = (y) => (y === "U" ? "yükseliş" : y === "D" ? "düşüş" : "nötr");
    if (!r) return { k: "0", cls: "", gl: "•", tt: "veri yok" };
    const g = fmzPickG(r);
    if (g && (g.yon === "U" || g.yon === "D")) return { k: "g", cls: g.yon === "U" ? "up" : "dn", gl: g.yon === "U" ? "▲" : "▼", tt: `aktif grafik formasyonu: ${g.ad} (${g.durum === "KIRILDI" ? "kırıldı" : "oluşuyor"}, ${L(g.yon)})` };
    const c = fmzPickC(r).find((x) => x.yon === "U" || x.yon === "D");
    if (c) return { k: "c", cls: (c.yon === "U" ? "up" : "dn") + " fmz-c", gl: c.yon === "U" ? "▴" : "▾", tt: `aktif grafik formasyonu yok · yalnız mum formasyonu: ${c.ad} (${L(c.yon)})` };
    const h = r.g.find((x) => x.durum !== "BAŞARISIZ" && x.h1_ok);
    if (h) return { k: "h", cls: "fmz-h", gl: "✓", tt: `aktif sayılmayan: ${h.ad} (hedef 1 tamam)` };
    const f = r.g.find((x) => x.durum === "BAŞARISIZ");
    if (f) return { k: "f", cls: "fmz-f", gl: f.yon === "D" ? "▽" : "△", tt: `başarısız: ${f.ad} (aktif sayılmaz)` };
    const n = r.c.length ? r.c[0] : null;
    return { k: "0", cls: "", gl: "•", tt: n ? `yönsüz mum formasyonu: ${n.ad}` : "formasyon yok" };
  }
  function fmzGet(key, url) {
    const Z = fmzS(); Z.cache = Z.cache || {};
    if (Z.cache[key]) return Z.cache[key];
    const p = api(url, { timeout: 20000 }).then((K) => { if (!K || !K.ok) delete Z.cache[key]; return K; }, (e) => { delete Z.cache[key]; throw e; });
    Z.cache[key] = p; return p;
  }
  const fmzEt = (s) => { s = String(s || "").replace(/ \(%[+-]?\d+(?:[.,]\d+)?\)/g, ""); const i = s.indexOf(". "); return i > 0 ? s.slice(0, i + 1) : s; };
  function fmzSelHtml(d, tf) {
    const Z = fmzS(), r = d.tfs[tf], L = FM_TFL[tf], LL = FM_TFLL[tf];
    const play = (b) => `<button type="button" class="fmz-play" data-fmzplay="${b}" aria-label="Animasyonu tekrar oynat" title="Tekrar oynat">▶</button>`;
    // 1) grafik formasyonu
    const g = fmzPickG(r), T1 = `EN GÜÇLÜ AKTİF GRAFİK FORMASYONU · ${L}`;
    let h1;
    if (!g) {
      const oth = r ? r.g.map((x) => `${esc(x.ad)} (${x.durum === "BAŞARISIZ" ? "başarısız" : x.h1_ok ? "hedef 1 tamam" : x.durum === "KIRILDI" ? "kırıldı" : "oluşuyor"})`) : [];
      h1 = `<div class="fmz-best fmz-emp" data-fmzempty="g"><div class="fmz-bi"><div class="fmz-bt">${T1}</div><div class="fmz-en">${r ? "Bu periyotta aktif grafik formasyonu yok" : "Bu periyotta veri yok"}</div>${oth.length ? `<div class="muted sm">Aktif sayılmayan: ${oth.join(", ")}.</div>` : ""}</div></div>`;
    } else {
      h1 = `<div class="fmz-best ${fmCls(g.yon)}" role="button" tabindex="0" data-fmzk="${tf}|grafik|${g.k}" data-fmzbox="g"><div class="fmz-cvw"><canvas id="fmz-cv"></canvas>${play("g")}</div><div class="fmz-bi"><div class="fmz-bt">${T1}</div>
        <div class="fmz-bn">${fmAr(g.yon)} ${esc(g.ad)} <small>${LL} · ${g.durum === "KIRILDI" ? "KIRILDI" : "OLUŞUYOR"} · kalite ${g.kalite}</small></div>
        <div class="fm-lv"><span>Giriş <b>${fmP(g.giris)}</b></span><span class="neg">STOP <b>${fmP(g.stop)}</b></span><span class="pos">H1 <b>${fmP(g.h1)}</b></span><span class="pos">H2 <b>${fmP(g.h2)}</b></span><span>R/R <b>${fN(g.rr, 1)}</b></span></div>
        <div class="muted sm">Dokun → animasyonlu kanıt ›</div></div></div>`;
    }
    // 2) aktif mum formasyonu
    const cs = fmzPickC(r), n = cs.length, ci = n ? (((Z.ci && Z.ci[tf]) || 0) % n) : 0, c = cs[ci], T2 = `AKTİF MUM FORMASYONU · ${L}`;
    let h2;
    if (!c) {
      h2 = `<div class="fmz-box fmz-emp" data-fmzempty="c"><div class="fmz-bh"><span class="fmz-bt">${T2}</span></div><div class="fmz-en">${r ? "Son kapanmış barda mum formasyonu yok" : "Bu periyotta veri yok"}</div>${r ? `<div class="muted sm">Son kapanmış bar: ${fmTime(r.t, tf, true)}</div>` : ""}</div>`;
    } else {
      const bt = d.bt && d.bt[c.k], up = c.yon !== "D";
      h2 = `<div class="fmz-box ${fmCls(c.yon)}" role="button" tabindex="0" data-fmzk="${tf}|mum|${c.k}" data-fmzbox="c">
        <div class="fmz-bh"><span class="fmz-bt">${T2}</span><span class="fmz-bx">${n > 1 ? `<button type="button" class="fmz-cyc" data-fmzcyc="1" title="Sıradaki mum formasyonu">${ci + 1}/${n} · +${n - 1} ›</button>` : ""}${play("c")}</span></div>
        <div class="fmz-cvw2"><canvas id="fmz-cv-c" class="fmz-cvb"></canvas></div>
        <div class="fmz-bn">${fmAr(c.yon)} ${esc(c.ad)} <span class="fm-b ${fmCls(c.yon)}">${FM_YON[c.yon]}</span><span class="fm-b">${esc(c.tip)}</span><span class="fm-rel r${c.guven}">güven ${FM_REL[c.guven]}</span></div>
        <div class="fmz-et"><b>Etkisi:</b> ${esc(fmzEt(c.etki))}</div>
        <div class="fm-lv"><span>Kapanış <b>${fmP(c.c)}</b></span>${c.yon === "N" ? `<span class="pos">Üst <b>${fmP(c.teyit)}</b></span><span class="neg">Alt <b>${fmP(c.gecersiz)}</b></span>`
          : `<span class="pos">Teyit ${up ? "&gt;" : "&lt;"} <b>${fmP(up ? c.teyit : c.gecersiz)}</b></span><span class="neg">Geçersiz ${up ? "&lt;" : "&gt;"} <b>${fmP(up ? c.gecersiz : c.teyit)}</b></span>`}<span>Skor <b>${c.skor}</b></span>${c.hacim ? `<span class="pos">hacim ✓</span>` : ""}</div>
        ${bt ? `<div class="fmz-btx">Geçmiş test (günlük, ~1 yıl, ${fN(bt.n)} örnek): ertesi gün yönünde <b>%${fN(bt.w1, 1)}</b> · 5 gün <b>%${fN(bt.w5, 1)}</b>${bt.w1 < 50 ? ` · <span class="neg">yazı-turadan iyi değil</span>` : ""}</div>` : `<div class="muted sm">Geçmiş test: bu formasyon için yeterli örnek yok.</div>`}
        <div class="muted sm">Dokun → tam mum kanıtı ›</div></div>`;
    }
    // 3) order block
    const ob = d.ob && d.ob[tf], T3 = `ORDER BLOCK · OLASI GÜÇLÜ TEPKİ BÖLGELERİ · ${L}`;
    let h3;
    if (!ob) {
      h3 = `<div class="fmz-box ob fmz-emp" data-fmzempty="o"><div class="fmz-bh"><span class="fmz-bt">${T3}</span></div><div class="fmz-en">${r ? "Order block hesaplanıyor…" : "Bu periyotta veri yok"}</div></div>`;
    } else {
      const zr = (z) => `<div class="obz-r ${z.yon === "U" ? "up" : "dn"}"><span class="obz-p">${fmP(z.bot)}–${fmP(z.top)}</span><span class="obz-d">${z.ic ? "İÇİNDE" : fmPc(z.d)}</span><span class="obz-s"><i style="width:${Math.max(4, Math.min(100, z.skor))}%"></i><b>${z.skor}</b></span><span class="obz-st ${z.durum === "TAZE" ? "tz" : "ts"}">${z.durum === "TAZE" ? "TAZE" : `TEST ${z.tests}×`}</span></div>`;
      const none = !ob.sup.length && !ob.dem.length;
      h3 = `<div class="fmz-box ob${none ? " fmz-emp" : ""}" role="button" tabindex="0" data-fmzob="${tf}" data-fmzbox="o"${none ? ` data-fmzempty="o"` : ""}>
        <div class="fmz-bh"><span class="fmz-bt">${T3}</span><span class="fmz-bx">${none ? "" : play("o")}</span></div>
        ${none ? `<div class="fmz-en">Bu periyotta geçerli order block yok</div>` : `<div class="fmz-cvw2"><canvas id="fmz-cv-o" class="fmz-cvb ob"></canvas></div>`}
        <div class="obz-h"><span>▼ DİRENÇ · arz (üstte)</span><span>uzaklık</span><span>güç</span><span>durum</span></div>
        ${ob.sup.length ? ob.sup.slice().reverse().map(zr).join("") : `<div class="muted sm obz-0">Fiyatın üstünde geçerli arz bölgesi yok</div>`}
        <div class="obz-px"><span>Fiyat</span><b>${fmP(ob.p)}</b></div>
        <div class="obz-h"><span>▲ DESTEK · talep (altta)</span><span>uzaklık</span><span>güç</span><span>durum</span></div>
        ${ob.dem.length ? ob.dem.map(zr).join("") : `<div class="muted sm obz-0">Fiyatın altında geçerli talep bölgesi yok</div>`}
        <div class="muted sm obz-f">Bu periyotta ${fN(ob.n.tum)} OB: ${fN(ob.n.gecerli)} geçerli (${fN(ob.n.taze)} taze), ${fN(ob.n.kirik)} kırıldı · açık FVG ${fN(ob.n.fvg)} · Dokun → tanım + kanıt ›</div></div>`;
    }
    return h1 + h2 + h3;
  }
  function fmzSelRender() {
    const Z = fmzS(), d = Z.d, el = $("fmz-sel"); if (!el || !d || !d.tfs) return;
    const tf = fmzTf();
    setH(el, fmzSelHtml(d, tf));
    document.querySelectorAll("#fmz [data-fmztf]").forEach((b) => { const on = b.dataset.fmztf === tf; b.classList.toggle("sel", on); b.setAttribute("aria-selected", on ? "true" : "false"); });
    const A = Z.A || {}; for (const b in A) if (A[b]) A[b].drawn = false;
    fmzAnim();
  }
  function fmzSelLoad() {
    const Z = fmzS(), d = Z.d, sym = st.sym; if (!d || !d.ready || !d.tfs || Z.sym !== sym) return;
    const tf = fmzTf(), r = d.tfs[tf], g = fmzPickG(r), cs = fmzPickC(r), c = cs.length ? cs[(((Z.ci && Z.ci[tf]) || 0) % cs.length)] : null;
    const ob = d.ob && d.ob[tf], A = (Z.A = Z.A || {}), rt = r ? r.t : 0;
    const want = { g: g ? `${tf}|${rt}|g|${g.k}` : null, c: c ? `${tf}|${rt}|c|${c.k}` : null, o: ob && (ob.sup.length || ob.dem.length) ? `${tf}|${rt}|o` : null };
    ["g", "c", "o"].forEach((b) => {
      const key = want[b];
      if (!key) { A[b] = null; return; }
      if (A[b] && A[b].key === key) return;   // aynı veri: animasyon durumu korunur (60 sn yenilemede baştan oynamaz)
      A[b] = { key, K: null, M: null, t0: 0, done: false, drawn: false, frz: null };
      const url = b === "o" ? `/api/formasyon/ob?sym=${encodeURIComponent(sym)}&tf=${tf}`
        : `/api/formasyon/kanit?sym=${encodeURIComponent(sym)}&tf=${tf}&kind=${b === "g" ? "grafik" : "mum"}&k=${encodeURIComponent(b === "g" ? g.k : c.k)}`;
      fmzGet(sym + "|" + key, url).then((K) => {
        const a = fmzS().A[b]; if (!a || a.key !== key || st.sym !== sym) return;
        if (!K || !K.ok) { a.err = (K && K.error) || "—"; return; }
        a.K = K; a.M = b === "o" ? null : fmPrep(K); a.t0 = performance.now(); a.done = false; a.drawn = false;
        if (b === "g") { Z.K = K; Z.KM = a.M; }
        fmzAnim();
      }).catch(() => {});
    });
  }
  function fmzSetTf(tf) {
    if (!FM_TFS.includes(tf)) return;
    const same = tf === fmzTf();
    try { sessionStorage.setItem(FMZ_SS, tf); } catch (e) {}
    fmzSelRender(); fmzSelLoad();
    if (same) fmzReplay();
  }
  function fmzReplay(b) {
    const A = fmzS().A || {};
    (b ? [b] : ["g", "c", "o"]).forEach((k) => { const a = A[k]; if (a) { a.t0 = performance.now(); a.done = false; a.frz = null; a.drawn = false; } });
    fmzAnim();
  }
  function fmzCv(b) { return $(b === "g" ? "fmz-cv" : "fmz-cv-" + b); }
  function fmzDrawBox(b, cv, a, T) { return b === "o" ? obDraw(cv, a.K, T, true) : fmDraw(cv, a.K, a.M, T, b === "g", b === "c" ? { seq: true } : null); }
  function fmzAnim() {
    const Z = fmzS(); if (Z.raf) return;
    const loop = () => {
      Z.raf = 0;
      if (st.view !== "stock" || document.hidden) return;
      const A = Z.A || {}; let more = false;
      for (const b of ["g", "c", "o"]) {
        const a = A[b]; if (!a || !a.K) continue;
        const cv = fmzCv(b); if (!cv) continue;
        const box = cv.closest("[data-fmzbox]");
        if (a.frz != null) { if (!a.drawn) { fmzDrawBox(b, cv, a, a.frz); a.drawn = true; } if (box) box.classList.remove("playing"); continue; }
        if (a.done && a.drawn) continue;
        const T = a.done ? 1e9 : performance.now() - a.t0;
        const end = fmzDrawBox(b, cv, a, T); a.drawn = true; a.end = end;
        if (b === "g") { if (T > end + 2200) a.t0 = performance.now(); more = true; }   // grafik küçük resmi v1.27'deki gibi döngüde
        else if (T >= end + 30) { a.done = true; if (box) box.classList.remove("playing"); }
        else { more = true; if (box) box.classList.add("playing"); }
      }
      if (more) Z.raf = requestAnimationFrame(loop);
    };
    Z.raf = requestAnimationFrame(loop);
  }
  function fmzSeek(b, ms) {   // test/ekran görüntüsü: kutuyu ms anında dondur (null → normal oynat)
    const a = (fmzS().A || {})[b]; if (!a) return null;
    if (ms == null) { a.frz = null; a.t0 = performance.now(); a.done = false; } else a.frz = ms;
    a.drawn = false; fmzAnim(); return a.end || null;
  }
  function fmzClick(e) {
    const tb = e.target.closest("[data-fmztf]"); if (tb) { fmzSetTf(tb.dataset.fmztf); return true; }
    const pl = e.target.closest("[data-fmzplay]"); if (pl) { fmzReplay(pl.dataset.fmzplay); return true; }
    const cy = e.target.closest("[data-fmzcyc]"); if (cy) { const Z = fmzS(), tf = fmzTf(); Z.ci = Z.ci || {}; Z.ci[tf] = (Z.ci[tf] || 0) + 1; fmzSelRender(); fmzSelLoad(); return true; }
    const ob = e.target.closest("[data-fmzob]"); if (ob) { obProof(st.sym, ob.dataset.fmzob); return true; }
    return false;
  }
  document.addEventListener("keydown", (e) => {
    const t = e.target; if (!t || !t.closest || (e.key !== "Enter" && e.key !== " ")) return;
    if (t.matches && t.matches("#fmz [role=button]")) { e.preventDefault(); t.click(); }
  });
  document.addEventListener("visibilitychange", () => { try { if (!document.hidden && V127_READY) { const A = fmzS().A || {}; for (const b in A) if (A[b]) A[b].drawn = false; fmzAnim(); } } catch (e) {} });

  // ---- ORDER BLOCK çizimi (kutu + tam kanıt): barlar tek tek → köken mumu → itki oku → bölge sağa uzar → diğer bölgeler/FVG → fiyat çizgisi
  function obDraw(cv, D, T, small) {
    const dpr = window.devicePixelRatio || 1, W = cv.clientWidth || 340, H = cv.clientHeight || 170;
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    const B = D.bars, N = B.t.length, ob = D.ob, p = ob.p; if (!N) return 0;
    const near = (t) => { if (t == null) return null; let k = null; for (let i = 0; i < N; i++) { if (B.t[i] <= t) k = i; else break; } return k; };
    let lo = Math.min(...B.l), hi = Math.max(...B.h); const span = hi - lo || 1;
    const all = ob.sup.concat(ob.dem), vis = [], off = [];
    all.forEach((z) => { if (z.bot >= lo - span * 0.6 && z.top <= hi + span * 0.6) vis.push(z); else off.push(z); });
    vis.forEach((z) => { lo = Math.min(lo, z.bot); hi = Math.max(hi, z.top); });
    const pad = (hi - lo) * 0.07 || 1; lo -= pad; hi += pad;
    const pl = 4, pr = small ? 46 : 62, pt = small ? 8 : 16, pb = small ? 14 : 20;
    const cw = W - pl - pr, ch = H - pt - pb, slot = cw / N, bw = Math.max(1, Math.min(10, slot * 0.66));
    const X = (i) => pl + slot * (i + 0.5), Y = (q) => pt + ((hi - q) / (hi - lo)) * ch, cl = (x) => Math.max(0, Math.min(1, x));
    const UP = "#22c55e", DN = "#ef4444", GOLD = "#d4a64a", MUT = "#8b929b", XR = W - pr;
    const F = (px, b) => `${b ? "bold " : ""}${px}px system-ui, sans-serif`;
    // ızgara + eksenler
    g.strokeStyle = "rgba(255,255,255,.05)"; g.lineWidth = 1; g.fillStyle = MUT; g.font = F(small ? 9 : 10); g.textAlign = "left";
    for (let k = 0; k <= 3; k++) { const q = lo + ((hi - lo) * k) / 3, y = Y(q); g.beginPath(); g.moveTo(pl, y); g.lineTo(XR, y); g.stroke(); g.fillText(fmP(q), XR + 3, y + 3); }
    g.textAlign = "center"; const nt = Math.max(2, Math.min(4, Math.floor(cw / 110)));
    for (let k = 0; k < nt; k++) { const i = Math.round(((N - 1) * (k + 0.5)) / nt); g.fillText(fmTime(B.t[i], D.tf), X(i), H - 3); }
    const prim = vis.filter((z) => z.win).sort((a, b) => Math.abs(a.d) - Math.abs(b.d) || b.skor - a.skor)[0] || null;
    const rest = vis.filter((z) => z !== prim);
    const zcol = (z, a) => (z.yon === "U" ? `rgba(34,197,94,${a})` : `rgba(239,68,68,${a})`);
    const zrect = (z, x0, x1, alpha) => { const y1 = Y(z.top), y2 = Y(z.bot); g.fillStyle = zcol(z, 0.16 * alpha); g.fillRect(x0, y1, Math.max(0, x1 - x0), Math.max(1.5, y2 - y1)); g.strokeStyle = zcol(z, 0.7 * alpha); g.lineWidth = 1; g.strokeRect(x0, y1, Math.max(0, x1 - x0), Math.max(1.5, y2 - y1)); };
    const tag = (x, y, txt, col, alpha, right) => {
      g.globalAlpha = alpha; g.font = F(small ? 9.5 : 11, true); const tw = g.measureText(txt).width + 8;
      const xx = right ? Math.max(pl, Math.min(XR - tw - 2, x - tw)) : Math.max(pl, Math.min(XR - tw - 2, x - tw / 2));
      const yy = Math.max(pt + 1, Math.min(H - pb - 15, y - 8));
      g.fillStyle = "rgba(11,13,15,.9)"; g.fillRect(xx, yy, tw, 15); g.strokeStyle = col; g.lineWidth = 1; g.strokeRect(xx, yy, tw, 15);
      g.fillStyle = col; g.textAlign = "left"; g.fillText(txt, xx + 4, yy + 11); g.globalAlpha = 1;
    };
    const candle = (i, alpha, prog) => {
      const o = B.o[i], c0 = B.c[i], c = o + (c0 - o) * prog, col = c0 >= o ? UP : DN;
      g.globalAlpha = alpha; g.strokeStyle = col; g.fillStyle = col; g.lineWidth = 1;
      const x = X(i), hh = o + (B.h[i] - o) * prog, ll = o + (B.l[i] - o) * prog;
      g.beginPath(); g.moveTo(x, Y(Math.max(hh, o, c))); g.lineTo(x, Y(Math.min(ll, o, c))); g.stroke();
      const y1 = Y(Math.max(o, c)), y2 = Y(Math.min(o, c)); g.fillRect(x - bw / 2, y1, bw, Math.max(1, y2 - y1)); g.globalAlpha = 1;
    };
    const tB = 1000, tO = tB + 500, tI = tO + 600, tZ = tI + 800, tR = tZ + 600, tP = tR + 500;
    // katman 1: diğer bölgeler + FVG (arka planda)
    if (T >= tZ) {
      const a = cl((T - tZ) / 600);
      (ob.fvg || []).forEach((f) => { const k = near(f.t), x0 = k == null ? pl : X(k) - slot / 2; if (x0 >= XR) return; const y1 = Y(f.hi), y2 = Y(f.lo); if (y2 < pt || y1 > H - pb) return; g.fillStyle = `rgba(167,139,250,${0.13 * a})`; g.fillRect(x0, y1, XR - x0, Math.max(1, y2 - y1)); if (!small || slot > 2) { g.globalAlpha = a * 0.85; g.fillStyle = "#a78bfa"; g.font = F(8.5); g.textAlign = "left"; g.fillText("FVG", Math.min(XR - 22, x0 + 2), y1 + Math.min(9, Math.max(7, (y2 - y1) / 2 + 3))); g.globalAlpha = 1; } });
      rest.forEach((z) => { const k = z.win ? near(z.t) : null, x0 = k == null ? pl : X(k) - slot / 2; zrect(z, x0, XR, a); g.globalAlpha = a; g.fillStyle = z.yon === "U" ? "#4ade80" : "#f87171"; g.font = F(small ? 8.5 : 10, true); g.textAlign = "left"; g.fillText(`${z.yon === "U" ? "T" : "A"} ${fmP(z.top)}`, XR + 3, Y(z.mid) + 3); g.globalAlpha = 1; });
    }
    // katman 2: ana bölge dikdörtgeni (köken → sağa uzar)
    let io = null, ie = null;
    if (prim) { io = near(prim.t); ie = near(prim.te); }
    if (prim && io != null && T >= tI) {
      const a = cl((T - tI) / 800), x0 = X(io) - slot / 2, x1 = x0 + (XR - x0) * a;
      zrect(prim, x0, x1, 1);
    }
    // katman 3: barlar tek tek
    const nS = Math.min(N, Math.ceil(N * cl(T / tB)));
    for (let i = 0; i < nS; i++) candle(i, i === io && T >= tB ? 1 : 0.85, i === nS - 1 && T < tB ? cl(N * (T / tB) - i) : 1);
    // katman 4: köken mumu vurgusu + itki oku
    if (prim && io != null && T >= tB) {
      const a = cl((T - tB) / 500), pulse = T < tO ? 0.4 + 0.6 * Math.abs(Math.sin(((T - tB) / 500) * Math.PI * 2)) : 1;
      g.globalAlpha = pulse; g.strokeStyle = GOLD; g.lineWidth = 1.6; g.strokeRect(X(io) - bw / 2 - 3, Y(B.h[io]) - 3, bw + 6, Y(B.l[io]) - Y(B.h[io]) + 6); g.globalAlpha = 1;
      const fo = 1 - cl((T - tZ) / 350);   // bölge etiketi gelince «köken» etiketi söner (köken mumu altın çerçeveyle işaretli kalır)   // küçük kutu: bölge etiketi gelince köken/itki etiketleri söner (kalabalık olmasın)
      if ((!small || a >= 1) && fo > 0) tag(X(io), prim.yon === "U" ? Y(B.l[io]) + 18 : Y(B.h[io]) - 12, small ? "köken" : `köken: son ${prim.yon === "U" ? "düşüş" : "yükseliş"} mumu`, GOLD, a * fo, false);
    }
    if (prim && io != null && ie != null && T >= tO) {
      const a = cl((T - tO) / 600), up = prim.yon === "U";
      const xa = X(io), ya = Y(up ? B.l[io] : B.h[io]), xb = X(ie), yb = Y(B.c[ie]), xm = xa + (xb - xa) * a, ym = ya + (yb - ya) * a;
      const col = up ? "#4ade80" : "#f87171";
      g.strokeStyle = col; g.lineWidth = small ? 2 : 2.6; g.beginPath(); g.moveTo(xa, ya); g.lineTo(xm, ym); g.stroke();
      if (a > 0.2) { const ang = Math.atan2(ym - ya, xm - xa), s = small ? 6 : 8; g.fillStyle = col; g.beginPath(); g.moveTo(xm, ym); g.lineTo(xm - s * Math.cos(ang - 0.45), ym - s * Math.sin(ang - 0.45)); g.lineTo(xm - s * Math.cos(ang + 0.45), ym - s * Math.sin(ang + 0.45)); g.closePath(); g.fill(); }
      const fo2 = small ? 1 - cl((T - tZ) / 350) : 1;
      if (a >= 1 && fo2 > 0) tag(xb + 6, up ? yb - 12 : yb + 14, `itki ${fN(prim.imp, 1)}×ATR${prim.fvg ? " · FVG" : ""}`, col, cl((T - tO - 600) / 250) * fo2, false);
    }
    // ana bölge etiketi
    if (prim && io != null && T >= tZ) {
      const a = cl((T - tZ) / 300), up = prim.yon === "U", col = up ? "#4ade80" : "#f87171";
      const st0 = prim.durum === "TAZE" ? "TAZE" : `TEST ${prim.tests}×`;
      tag(XR - 2, up ? Y(prim.bot) + 12 : Y(prim.top) - 10, small ? `${up ? "TALEP" : "ARZ"} ${fmP(prim.bot)}–${fmP(prim.top)} · ${st0}` : `${up ? "TALEP (destek)" : "ARZ (direnç)"} ${fmP(prim.bot)}–${fmP(prim.top)} · ${st0} · güç ${prim.skor}`, col, a, true);
      g.globalAlpha = a; g.fillStyle = col; g.font = F(small ? 8.5 : 10, true); g.textAlign = "left"; g.fillText(`${up ? "T" : "A"} ${fmP(prim.top)}`, XR + 3, Y(prim.mid) + 3); g.globalAlpha = 1;
    }
    // görünür alan dışındaki bölgeler: kenar oku
    if (T >= tZ && off.length) {
      const a = cl((T - tZ) / 600); const ab = off.filter((z) => z.bot > hi), be = off.filter((z) => z.top < lo);
      if (ab.length) tag(pl + 70, pt + 8, `↑ ${ab[0].yon === "U" ? "TALEP" : "ARZ"} ${fmP(ab[0].bot)}–${fmP(ab[0].top)} (${fmPc(ab[0].d)})`, ab[0].yon === "U" ? "#4ade80" : "#f87171", a, false);
      if (be.length) tag(pl + 70, H - pb - 6, `↓ ${be[0].yon === "U" ? "TALEP" : "ARZ"} ${fmP(be[0].bot)}–${fmP(be[0].top)} (${fmPc(be[0].d)})`, be[0].yon === "U" ? "#4ade80" : "#f87171", a, false);
    }
    // fiyat çizgisi
    if (T >= tR && isNum(p)) {
      const a = cl((T - tR) / 500), y = Y(p);
      g.strokeStyle = "#e5e7eb"; g.lineWidth = 1; g.setLineDash([4, 3]); g.beginPath(); g.moveTo(pl, y); g.lineTo(pl + (XR - pl) * a, y); g.stroke(); g.setLineDash([]);
      if (a >= 1) { g.fillStyle = "#e5e7eb"; g.fillRect(XR + 1, y - 7, pr - 2, 14); g.fillStyle = "#0b0d0f"; g.font = F(small ? 9 : 10, true); g.textAlign = "left"; g.fillText(fmP(p), XR + 4, y + 4); }
    }
    return tP;
  }
  async function obProof(sym, tf) {
    if (!V127_READY) return;
    const ov = fmOv(); ov.hidden = false; document.body.classList.add("fmk-open");
    FMK = FMK || {}; cancelAnimationFrame(FMK.raf); FMK.K = null; FMK.ob = null;
    setH($("fmk-t"), `<b>${esc(sym)}</b> · ${FM_TFLL[tf] || tf} · ORDER BLOCK yükleniyor…`); setH($("fmk-b"), ""); $("fmk-st").textContent = "";
    const cv = $("fmk-cv"); cv.getContext("2d").clearRect(0, 0, cv.width, cv.height);
    let D;
    try { D = await fmzGet(`${sym}|${tf}|obfull|${(fmzS().d && fmzS().d.tfs[tf] && fmzS().d.tfs[tf].t) || 0}`, `/api/formasyon/ob?sym=${encodeURIComponent(sym)}&tf=${tf}`); }
    catch (e) { setH($("fmk-b"), `<div class="empty">Alınamadı: ${esc(e.message || e)}</div>`); return; }
    if (!D || !D.ok) { setH($("fmk-b"), `<div class="empty">${esc((D && D.error) || "—")}</div>`); return; }
    FMK.ob = D;
    setH($("fmk-t"), `<b>${esc(sym)}</b> · ${esc(D.tfl)} · <span class="fm-nm">ORDER BLOCK</span> <span class="fm-b">olası güçlü tepki bölgeleri</span>`);
    setH($("fmk-b"), obBody(D));
    fmPlay();
  }
  function obBody(D) {
    const ob = D.ob, tf = D.tf;
    const row = (z) => `<tr class="${z.yon === "U" ? "pos" : "neg"}"><td><b>${fmP(z.bot)}–${fmP(z.top)}</b></td><td>${z.ic ? "İÇİNDE" : fmPc(z.d)}</td><td>${z.durum === "TAZE" ? "TAZE" : `TEST EDİLDİ (${z.tests})`}${z.depth ? ` · en derin %${z.depth}` : ""}</td><td>${z.skor}</td><td>${fN(z.imp, 2)}×</td><td>${z.vr != null ? fN(z.vr, 2) + "×" : "—"}</td><td>${z.fvg ? `${fmP(z.fvg[0])}–${fmP(z.fvg[1])}` : "—"}</td><td>${fmP(z.bos)} <small>(${fmTime(z.bos_t, tf)})</small></td><td>${fmTime(z.t, tf)}</td></tr>`;
    const head = `<tr><th>Bölge</th><th>Uzaklık</th><th>Durum</th><th>Güç</th><th>İtki/ATR</th><th>İtki hacmi</th><th>FVG</th><th>Kırılan yapı (BOS)</th><th>Köken mumu</th></tr>`;
    const tbl = (zs, empty) => zs.length ? `<div class="fmk-tbw"><table class="fmk-tb">${head}${zs.map(row).join("")}</table></div>` : `<div class="muted sm">${empty}</div>`;
    const prim = ob.sup.concat(ob.dem).filter((z) => z.win).sort((a, b) => Math.abs(a.d) - Math.abs(b.d) || b.skor - a.skor)[0];
    const ib = prim && prim.imp_bars ? `<div class="fmk-sub">Ana bölge: köken + itki barları (OHLC)</div><div class="fmk-tbw"><table class="fmk-tb"><tr><th>Bar</th><th>Açılış</th><th>Yüksek</th><th>Düşük</th><th>Kapanış</th><th>Hacim</th></tr>${prim.imp_bars.map((b, i) => `<tr><td><b>${i ? i + ". itki" : "köken"}</b> ${fmTime(b[0], tf)}</td><td>${fmP(b[1])}</td><td>${fmP(b[2])}</td><td>${fmP(b[3])}</td><td class="${b[4] >= b[1] ? "pos" : "neg"}">${fmP(b[4])}</td><td>${fShort ? fShort(b[5]) : fN(b[5])}</td></tr>`).join("")}</table></div>` : "";
    const kr = (ob.kirik || []).map((z) => `<li><span class="no">✗</span> ${z.yon === "U" ? "Talep" : "Arz"} ${fmP(z.bot)}–${fmP(z.top)} (köken ${fmTime(z.t, tf)}) — ${fmTime(z.brk_t, tf)} kapanışıyla kırıldı</li>`).join("");
    const fv = (ob.fvg || []).map((f) => `<li><span class="ok">◆</span> ${f.yon === "U" ? "Yükseliş" : "Düşüş"} FVG ${fmP(f.lo)}–${fmP(f.hi)} (${fmTime(f.t, tf)}) — henüz doldurulmadı</li>`).join("");
    return `<div class="fmk-et"><b>Tanım:</b> ${esc(D.def)}</div>
      <div class="fmk-lv"><span>Fiyat <b>${fmP(ob.p)}</b></span><span>ATR14 <b>${fmP(ob.atr)}</b></span><span>OB <b>${fN(ob.n.tum)}</b></span><span class="pos">geçerli <b>${fN(ob.n.gecerli)}</b> (taze ${fN(ob.n.taze)})</span><span class="neg">kırık <b>${fN(ob.n.kirik)}</b></span><span>açık FVG <b>${fN(ob.n.fvg)}</b></span></div>
      <div class="fmk-sub">▼ Direnç (arz) bölgeleri — fiyatın üstü</div>${tbl(ob.sup, "Fiyatın üstünde geçerli arz bölgesi yok.")}
      <div class="fmk-sub">▲ Destek (talep) bölgeleri — fiyatın altı</div>${tbl(ob.dem, "Fiyatın altında geçerli talep bölgesi yok.")}
      ${ib}${kr ? `<div class="fmk-sub">Son kırılan (geçersiz) bölgeler</div><ul class="fmk-ck">${kr}</ul>` : ""}${fv ? `<div class="fmk-sub">Açık FVG (dengesizlik) bantları</div><ul class="fmk-ck">${fv}</ul>` : ""}
      <div class="src-note">Kaynak: ${esc(D.src || "")}${D.today_src ? ` · bugün: ${esc(D.today_src)}` : ""}. ${esc(D.closed_note || "")} Eşik: itki ≥ ${fN(D.param.imp_atr, 1)}×ATR14, en çok ${D.param.imp_max_bars} bar, BOS için ${D.param.fractal}+${D.param.fractal} bar fraktal tepe/dip.</div>`;
  }

  // ---- ana grafikte OB bölgeleri (grafik araçlarında «OB» düğmesi; Özet › FORMASYONLAR verisi, grafiğin periyodu)
  const OBV = { on: LS.get("chOb", false) === true, cv: null, raf: 0, init: false };
  const OB_CHTF = { "5m": "5m", "15m": "15m", "30m": "30m", "1h": "60m", "60m": "60m", "2h": "2h", "4h": "4h", "1d": "1d", "1w": "1w" };
  function obOv() {
    if (!V127_READY || typeof chart === "undefined" || !chart || !cSeries) return;
    const box = $("chart-box"); if (!box) return;
    if (!OBV.init || !OBV.cv || !box.contains(OBV.cv)) {
      OBV.init = true;
      const tl = box.querySelector(".ch-tools");
      if (tl && !tl.querySelector("[data-chob]")) {
        const bt = document.createElement("button"); bt.type = "button"; bt.dataset.chob = "1"; bt.title = "Order block bölgeleri (olası güçlü tepki bölgeleri)"; bt.textContent = "OB"; if (OBV.on) bt.className = "on";
        tl.insertBefore(bt, tl.firstChild);
        bt.addEventListener("click", (e) => { e.stopPropagation(); OBV.on = !OBV.on; LS.set("chOb", OBV.on); bt.classList.toggle("on", OBV.on); obOvQ(); });
      }
      const cv = document.createElement("canvas"); cv.className = "ob-ov"; box.appendChild(cv); OBV.cv = cv;
      try { chart.timeScale().subscribeVisibleLogicalRangeChange(() => obOvQ()); } catch (e) {}
      try { chart.subscribeCrosshairMove(() => obOvQ()); } catch (e) {}
      try { new ResizeObserver(() => obOvQ()).observe(box); } catch (e) {}
    }
    obOvQ();
  }
  function obOvQ() { if (OBV.raf) return; OBV.raf = requestAnimationFrame(() => { OBV.raf = 0; try { obOvDraw(); } catch (e) {} }); }
  function obOvDraw() {
    const cv = OBV.cv, box = $("chart-box"); if (!cv || !box) return;
    const dpr = window.devicePixelRatio || 1, W = box.clientWidth, H = box.clientHeight;
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    OBV.n = 0;
    if (!OBV.on) return;
    const Z = fmzS(), tf = OB_CHTF[st.tf];
    if (!tf || !Z.d || !Z.d.ob || Z.sym !== st.sym || !Z.d.ob[tf] || !CHL.bars.length) { if (!tf) { g.fillStyle = "#8b929b"; g.font = "10px system-ui, sans-serif"; g.textAlign = "left"; g.fillText("OB: bu periyotta yok", 8, H - 36); } return; }
    const ob = Z.d.ob[tf], bars = CHL.bars, daily = typeof bars[0].time === "string";
    const toT = (t) => (daily ? new Date((t + 3 * 3600) * 1000).toISOString().slice(0, 10) : t + 3 * 3600);
    const idxOf = (t) => { const x = toT(t); let k = null; for (let i = 0; i < bars.length; i++) { if (bars[i].time <= x) k = i; else break; } return k; };
    const ts = chart.timeScale(); let psw = 0, tsh = 0; try { psw = chart.priceScale("right").width(); tsh = ts.height(); } catch (e) {}
    const pw = W - psw, ph = H - tsh;
    g.save(); g.beginPath(); g.rect(0, 0, pw, ph); g.clip();
    (ob.fvg || []).slice(0, 3).forEach((f) => {
      const y1 = cSeries.priceToCoordinate(f.hi), y2 = cSeries.priceToCoordinate(f.lo); if (y1 == null || y2 == null) return;
      const k = idxOf(f.t); let x0 = k == null ? 0 : ts.logicalToCoordinate(k); if (x0 == null || x0 < 0) x0 = 0; if (x0 >= pw) return;
      g.fillStyle = "rgba(167,139,250,.12)"; g.fillRect(x0, Math.min(y1, y2), pw - x0, Math.max(1, Math.abs(y2 - y1)));
    });
    ob.sup.concat(ob.dem).forEach((z) => {
      const y1 = cSeries.priceToCoordinate(z.top), y2 = cSeries.priceToCoordinate(z.bot); if (y1 == null || y2 == null) return;
      const k = idxOf(z.t); let x0 = 0;
      if (k != null) { const c0 = ts.logicalToCoordinate(k), c1 = ts.logicalToCoordinate(k + 1); x0 = c0 == null ? 0 : c0 - (c1 != null ? (c1 - c0) / 2 : 0); }   // kesirli mantıksal indeks LWC'de 0 döner → tam indeks − yarım bar
      if (!isNum(x0) || x0 < 0) x0 = 0; if (x0 >= pw) return;
      const up = z.yon === "U", yt = Math.min(y1, y2), hh = Math.max(1.5, Math.abs(y2 - y1));
      g.fillStyle = up ? "rgba(34,197,94,.14)" : "rgba(239,68,68,.14)"; g.fillRect(x0, yt, pw - x0, hh);
      g.strokeStyle = up ? "rgba(34,197,94,.65)" : "rgba(239,68,68,.65)"; g.lineWidth = 1; g.strokeRect(x0 + 0.5, yt + 0.5, pw - x0 - 1, hh);
      g.font = "bold 10px system-ui, sans-serif"; g.textAlign = "right"; g.fillStyle = up ? "#4ade80" : "#f87171";
      const lb = `OB ${up ? "talep" : "arz"} ${fmP(z.bot)}–${fmP(z.top)} · ${z.durum === "TAZE" ? "taze" : "test " + z.tests}`;
      g.fillText(lb, pw - 4, up ? yt + hh + 11 : yt - 3);
      OBV.n++;
    });
    g.restore();
  }

  V127_READY = true;
  try { if (st.view === "fm_mum" || st.view === "fm_grafik") fmOpen(st.view); } catch (e) { try { console.warn("v1.27 init", e); } catch (x) {} }


  // ------------------------------------------------------- v1.27.3 TAM METİN
  // Ekrana sığmayan (… ile kesilen / satır sınırlı) her metin: dokun veya uzun bas → tam metin penceresi.
  // Tek, belgeye bağlı (capture) dinleyici; kesilme dokunma anında ölçülür → dinamik içerik ekran-özel kod gerekmeden çalışır.
  // Kural: yalnız GERÇEKTEN kesik öğe pencereyi açar; kesik olmayan hücre/satır dokunuşları eskisi gibi. Kesik öğenin satırının
  // kendi eylemi varsa (hisse/detay açma) pencerede «Detay →» düğmesi aynı eylemi tetikler.
  const TX = { src: null, tgt: null, loc: null, bypass: false, lpT: 0, lpXY: null, lpOpen: false, suppress: 0, scanT: 0 };
  const TX_HARD = "input,textarea,select,button,a,label,summary,option,[contenteditable],[role=button],[role=slider],[role=tab],svg,canvas,video," +
    "header.topbar,.bnav,.kesfet,#search-sheet,.km-chart,.km-tip,.km-hcs,.mk-box,[class*='fmk-'],th[data-k],#tx-ov,[data-noexp]";
  // hisse listelerindeki ikincil şirket adı: dokunuş eskisi gibi hisseyi açar, UZUN BASINCA tam ad penceresi
  const TX_SOFT = ".sc-name,.sl-name,.ix-name,.rd-nm";
  // küçük aç/kapa denetimleri (kendi dokunuş eylemi olan rozet/düğme benzeri öğeler) — kapsayıcı değil, yalnız küçük öğede geçerli
  const TX_CTL = "[data-exp],[data-ckx],[data-opgo],[data-mkx],[data-mkleg],[data-mkkm],[data-k5tog],[data-k5x],[data-sort],[data-g],[data-f],[data-sec],[data-per],[data-scope]";
  function txCtl(el) { const c = el.closest(TX_CTL); return !!(c && c.childElementCount <= 8 && (c.textContent || "").length < 200); }
  const txNo = (el, lp) => !!el.closest(TX_HARD) || (!lp && !!el.closest(TX_SOFT)) || txCtl(el);
  const TX_STOP = new Set(["TR", "TABLE", "TBODY", "THEAD", "TFOOT", "BODY", "HTML", "SECTION", "MAIN", "NAV", "HEADER"]);
  function txIsCut(el) {
    if (!el || el.nodeType !== 1) return false;
    const cw = el.clientWidth, ch = el.clientHeight;
    if (!cw || !ch) return false;
    const ox = el.scrollWidth > cw + 1, oy = el.scrollHeight > ch + 1;
    if (!ox && !oy) return false;
    if (el.childElementCount > 12 || el.getElementsByTagName("*").length > 12) return false;   // kapsayıcı değil, metin öğesi
    const t = (el.textContent || "").trim();
    if (t.length < 3 || t.length > 3000) return false;
    if (el.querySelector("table,svg,canvas,input,select,textarea,button,video")) return false;
    const cs = getComputedStyle(el);
    const clipX = cs.overflowX === "hidden" || cs.overflowX === "clip", clipY = cs.overflowY === "hidden" || cs.overflowY === "clip";
    const clamp = cs.webkitLineClamp && cs.webkitLineClamp !== "none";
    if (!(ox && clipX) && !(oy && clipY && (clamp || (cs.maxHeight !== "none" && t.length < 800)))) return false;
    if ((parseFloat(cs.fontSize) || 12) < 8.5) return false;          // ısı haritası vb. mikro etiketler
    if (ox && clipX && cs.textOverflow === "ellipsis") return true;   // … ile kesilmiş metin (Chrome parçayı … noktasında keser → aralık ölçümü güvenilmez)
    // taşan şey gerçekten metin mi? (dekoratif/mutlak konumlu kutuları ele)
    try {
      const r = document.createRange(); r.selectNodeContents(el);
      const rr = r.getBoundingClientRect(), er = el.getBoundingClientRect();
      const pr = parseFloat(cs.paddingRight) || 0, pb = parseFloat(cs.paddingBottom) || 0;
      if (ox && clipX && rr.right > er.right - pr + 0.5) return true;
      if (oy && clipY && rr.bottom > er.bottom - pb + 0.5) return true;
      return false;
    } catch (e) { return true; }
  }
  function txFind(t, lp) {
    if (!t || t.nodeType !== 1) t = t && t.parentElement;
    if (!t || !t.closest || txNo(t, lp)) return null;
    let el = t;
    for (let i = 0; el && i < 7; i++, el = el.parentElement) {
      if (TX_STOP.has(el.tagName) || el.classList.contains("view") || el.classList.contains("km-box") || el.classList.contains("card") || el.classList.contains("shell")) break;
      if (txIsCut(el)) return el;
      if (el.tagName === "TD" || el.tagName === "TH" || el.tagName === "LI") break;
    }
    const cell = t.closest("td,th,li");
    const box = cell || (!TX_STOP.has(t.tagName) && t.childElementCount <= 10 ? t : null);
    if (box) for (const c of box.querySelectorAll("*")) { if (!txNo(c, lp) && txIsCut(c)) return c; }
    return null;
  }
  function txCtx(el) {
    let col = "", row = "", sym = "";
    const cell = el.closest("td,th");
    if (cell && cell.parentElement) {
      const tr = cell.parentElement, tb = cell.closest("table");
      let idx = 0; for (const c of tr.cells) { if (c === cell) break; idx += c.colSpan || 1; }
      const hr = tb && tb.tHead && tb.tHead.rows[tb.tHead.rows.length - 1];
      if (hr && cell.tagName === "TD") { let k = 0; for (const h of hr.cells) { const n = h.colSpan || 1; if (idx >= k && idx < k + n) { col = (h.innerText || "").trim(); break; } k += n; } }
      sym = tr.dataset.rowSym || tr.dataset.sym || "";
      for (const c of tr.cells) { if (c === cell) break; const v = (c.innerText || "").trim().split("\n")[0]; if (/[0-9A-Za-zÇĞİÖŞÜçğıöşü]{2}/.test(v)) { row = v.slice(0, 40); break; } }
    }
    const ds = el.closest("[data-sym]"); if (!sym && ds) sym = ds.dataset.sym || "";
    let scope = "";
    const box = el.closest(".km-box"); const kt = box && box.querySelector(".km-tt b");
    let ct = null;
    for (let a = el.parentElement, i = 0; a && i < 10 && a !== document.body; a = a.parentElement, i++) {
      ct = a.querySelector(":scope > .card-h .card-title, :scope > .card-title, :scope > .card-h > b, :scope > h3"); if (ct) break;
      if (a.classList.contains("view") || a.classList.contains("km-box")) break;
    }
    scope = [kt && kt.textContent.trim(), ct && ct.textContent.trim()].filter(Boolean).filter((v, i, a) => a.indexOf(v) === i).join(" · ");
    return { col, row, sym, scope };
  }
  function txAct(el) {
    for (let a = el, i = 0; a && i < 8 && a !== document.body; a = a.parentElement, i++) {
      if (a.classList.contains("view") || a.classList.contains("km-box") || a.tagName === "TABLE") break;
      if ((a.tagName === "TR" && a.dataset.rowSym) || a.hasAttribute("data-sym") || a.hasAttribute("onclick") || getComputedStyle(a).cursor === "pointer") return a;
    }
    return null;
  }
  function txLoc(t) {   // canlı yenilemede satır yeniden çizilirse aynı satırı yeniden bulmak için
    const tr = t.closest("tr,li,[data-sym]"); if (!tr) return null;
    const host = tr.closest("[id]");
    const sel = tr.tagName.toLowerCase() + Object.entries(tr.dataset).map(([k, v]) => `[data-${k.replace(/[A-Z]/g, (m) => "-" + m.toLowerCase())}="${CSS.escape(v)}"]`).join("");
    const cell = t.closest("td");
    return { host: host && host.id, sel, ci: cell ? cell.cellIndex : -1 };
  }
  function txOv() {
    let ov = $("tx-ov");
    if (ov) return ov;
    ov = document.createElement("div"); ov.id = "tx-ov"; ov.className = "tx-ov"; ov.hidden = true;
    ov.innerHTML = `<div class="tx-sh" role="dialog" aria-modal="true" aria-labelledby="tx-t"><div class="tx-grip"></div>
      <div class="tx-hd"><div class="tx-tt"><b id="tx-t"></b><small id="tx-s"></small></div><button type="button" class="km-x" data-tx="close" aria-label="Kapat">✕</button></div>
      <div class="tx-body" id="tx-b"></div>
      <div class="tx-ft"><button type="button" class="btn-ghost sm" data-tx="copy">Kopyala</button><button type="button" class="btn-ghost sm tx-act" data-tx="act" hidden>Detay →</button><button type="button" class="btn-ghost sm" data-tx="close">Kapat</button></div></div>`;
    document.body.appendChild(ov);
    ov.addEventListener("click", (e) => {
      if (Date.now() < TX.suppress) return;
      if (e.target === ov) { txClose(); return; }
      const b = e.target.closest("[data-tx]"); if (!b) return;
      const a = b.dataset.tx;
      if (a === "close") txClose();
      else if (a === "copy") txCopy();
      else if (a === "act") txDoAct();
    });
    // aşağı kaydırarak kapat
    const sh = ov.querySelector(".tx-sh"), body = ov.querySelector(".tx-body");
    let y0 = null, dy = 0;
    sh.addEventListener("touchstart", (e) => { const inBody = body.contains(e.target); y0 = (!inBody || body.scrollTop <= 0) ? e.touches[0].clientY : null; dy = 0; }, { passive: true });
    sh.addEventListener("touchmove", (e) => {
      if (y0 == null) return; dy = e.touches[0].clientY - y0;
      if (dy > 0 && !(window.getSelection && String(window.getSelection()))) { sh.style.transform = `translateY(${dy}px)`; sh.style.transition = "none"; } else dy = 0;
    }, { passive: true });
    sh.addEventListener("touchend", () => { if (y0 == null) return; sh.style.transition = ""; if (dy > 80) txClose(); else sh.style.transform = ""; y0 = null; dy = 0; });
    ov.addEventListener("touchmove", (e) => { if (e.target === ov) e.preventDefault(); }, { passive: false });
    return ov;
  }
  function txOpen(el, tgt) {
    const ov = txOv();
    let txt = (el.innerText || el.textContent || "").replace(/\u00a0/g, " ").replace(/[ \t]+\n/g, "\n").trim();
    const ttl = el.getAttribute("title"); if (ttl && ttl.trim() && !txt.includes(ttl.trim())) txt += "\n\n" + ttl.trim();
    const c = txCtx(el);
    $("tx-t").textContent = c.col || c.scope || "Tam metin";
    $("tx-s").textContent = [c.sym, c.row && c.row !== c.sym ? c.row : "", c.col ? c.scope : ""].filter(Boolean).join(" · ");
    $("tx-b").textContent = txt; $("tx-b").scrollTop = 0;
    const act = txAct(tgt || el);
    TX.src = el; TX.tgt = act ? (tgt || el) : null; TX.loc = act ? txLoc(tgt || el) : null;
    const ab = ov.querySelector("[data-tx=act]"); ab.hidden = !act; ab.textContent = c.sym ? `${c.sym} · Detay →` : "Detay →";
    const sh = ov.querySelector(".tx-sh"); sh.style.transform = ""; sh.style.transition = "";
    ov.hidden = false; document.body.classList.add("tx-open");
  }
  function txClose() { const ov = $("tx-ov"); if (ov) ov.hidden = true; document.body.classList.remove("tx-open"); TX.src = null; }
  async function txCopy() {
    const s = $("tx-b").textContent || "";
    try { await navigator.clipboard.writeText(s); toast("Kopyalandı ✓", 1400); }
    catch (e) {
      try { const ta = document.createElement("textarea"); ta.value = s; ta.style.cssText = "position:fixed;left:-9999px;top:0"; document.body.appendChild(ta); ta.select(); document.execCommand("copy"); ta.remove(); toast("Kopyalandı ✓", 1400); }
      catch (e2) { toast("Kopyalanamadı — metni basılı tutup seçin", 2200); }
    }
  }
  function txDoAct() {
    let t = TX.tgt; const L = TX.loc; txClose();
    if (t && !t.isConnected && L && L.host) { const h = $(L.host), r = h && h.querySelector(L.sel); t = r ? (L.ci >= 0 && r.cells && r.cells[L.ci] ? r.cells[L.ci] : r) : null; }
    if (!t || !t.isConnected) { toast("Satır yenilendi — tekrar dokunun", 1600); return; }
    TX.bypass = true;
    try { t.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window })); } finally { TX.bypass = false; }
  }
  const txIsOpen = () => { const ov = $("tx-ov"); return !!(ov && !ov.hidden); };
  window.addEventListener("click", (e) => {
    if (TX.bypass) return;
    if (Date.now() < TX.suppress) { e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation(); return; }
    if (txIsOpen() || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    const sel = window.getSelection && window.getSelection();
    if (sel && !sel.isCollapsed && String(sel).trim() && sel.containsNode && sel.containsNode(e.target, true)) return;   // metin seçiyor
    const c = txFind(e.target); if (!c) return;
    e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
    txOpen(c, e.target);
  }, true);
  // uzun bas → aynı pencere (işletim sistemi seçim çubuğu yerine)
  window.addEventListener("pointerdown", (e) => {
    clearTimeout(TX.lpT); TX.lpXY = null;
    if (e.pointerType !== "touch" || txIsOpen()) return;
    const t = e.target; TX.lpXY = [e.clientX, e.clientY];
    TX.lpT = setTimeout(() => {
      const c = txFind(t, true); if (!c) return;
      TX.lpOpen = true; TX.suppress = Date.now() + 5000;
      try { window.getSelection().removeAllRanges(); } catch (x) {}
      txOpen(c, t);
    }, 480);
  }, true);
  window.addEventListener("pointermove", (e) => { if (TX.lpXY && Math.hypot(e.clientX - TX.lpXY[0], e.clientY - TX.lpXY[1]) > 10) { clearTimeout(TX.lpT); TX.lpXY = null; } }, true);
  const txUp = () => { clearTimeout(TX.lpT); TX.lpXY = null; if (TX.lpOpen) { TX.lpOpen = false; TX.suppress = Date.now() + 450; } };
  window.addEventListener("pointerup", txUp, true); window.addEventListener("pointercancel", txUp, true);
  window.addEventListener("contextmenu", (e) => {
    const ov = $("tx-ov");
    if (ov && ov.contains(e.target)) return;                       // pencere içinde: normal seçim/menü
    if (txIsOpen()) { e.preventDefault(); return; }
    const c = txFind(e.target, true); if (!c) return;
    e.preventDefault(); clearTimeout(TX.lpT);
    if (e.pointerType === "mouse" || !("ontouchstart" in window)) { txOpen(c, e.target); return; }   // masaüstü sağ tık
    TX.lpOpen = true; TX.suppress = Date.now() + 5000; txOpen(c, e.target);
  }, true);
  window.addEventListener("keydown", (e) => { if (e.key === "Escape" && txIsOpen()) { e.preventDefault(); e.stopImmediatePropagation(); txClose(); } }, true);
  // ince ipucu: kesik öğeler noktalı alt çizgi (tembel tarama: DOM değişince / yeniden boyutlanınca, boşta)
  const TX_SCAN_SEL = "td,th,li,span,b,small,div,p,strong,em,h3,h4,i";
  function txScan() {
    TX.scanT = 0;
    const t0 = performance.now();
    const roots = [...document.querySelectorAll(".view:not([hidden]), .km-ov:not([hidden]), body > div:not([hidden]):not(.shell):not(#tx-ov):not(.kesfet):not(.sheet):not(.toast)")];
    const on = [], off = [];
    let n = 0;
    for (const r of roots) {
      const l = r.querySelectorAll(TX_SCAN_SEL);
      for (let i = 0; i < l.length && n < 6000; i++, n++) {
        const el = l[i], had = el.classList.contains("tx-cut");
        const cut = el.clientWidth > 0 && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1) && txIsCut(el) && !txNo(el);
        if (cut !== had) (cut ? on : off).push(el);
      }
    }
    on.forEach((el) => el.classList.add("tx-cut")); off.forEach((el) => el.classList.remove("tx-cut"));
    TX.lastScan = { ms: Math.round(performance.now() - t0), n, on: on.length, off: off.length };
  }
  function txSched() { if (TX.scanT) return; TX.scanT = setTimeout(() => { (window.requestIdleCallback || ((f) => f()))(txScan, { timeout: 800 }); }, 700); }
  new MutationObserver(txSched).observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["hidden"] });
  window.addEventListener("resize", txSched); txSched();


  // ===================================================================== v1.29.0 ==
  // ---- EN İYİ KOŞULLAR: her özelliğin tavan / ciddi yükseliş için en iyi ayarı (sunucuda tek yapılandırma: /api/eik)
  //      satıra dokun → o özelliğe git + ayarı uygula (applyConfig) → afiş "En İyi Koşul uygulandı" + Sıfırla (önceki ayarlar)
  //      Kullanıcının kayıtlı filtre setlerine (atSets vb.) dokunulmaz; Agresif/Kurum Uyarıları bildirim ayarları değişmez.
  const EIK = { cfg: null, ts: 0, err: "", bir: null, birErr: "", birAll: false, cur: null, q: "", inl: {} };
  const EIK_KIND = { kanit: ["KANIT", "ek-k"], zayif: ["ZAYIF KANIT", "ek-z"], uzman: ["UZMAN", "ek-u"], tanim: ["TANIM GEREĞİ", "ek-t"], not: ["NOT", "ek-n"] };
  const eikClone = (o) => JSON.parse(JSON.stringify(o == null ? null : o));
  async function eikOpen() {
    eikRender();
    if (!EIK.cfg || Date.now() - EIK.ts > 300000) {
      try { EIK.cfg = await api("/api/eik", { timeout: 20000 }); EIK.ts = Date.now(); EIK.err = ""; } catch (e) { EIK.err = e.message || String(e); }
      eikRender();
    }
    if (!EIK.bir || Date.now() - (EIK.birTs || 0) > 60000) eikBir(false);
  }
  async function eikBir(force) {
    EIK.birBusy = true; eikBirRender();
    try { EIK.bir = await api(`/api/eik/birlesik${force ? "?force=1" : ""}`, { timeout: 90000 }); EIK.birTs = Date.now(); EIK.birErr = ""; } catch (e) { EIK.birErr = e.message || String(e); }
    EIK.birBusy = false; eikBirRender();
  }
  const eikDay = (d) => (d ? d.slice(6, 8) + "." + d.slice(4, 6) : "");
  function eikEv(ev, lab) {
    if (!ev) return "";
    return `<span class="ek-ev"><b>${esc(lab || eikDay(ev.day))}</b> ${fN(ev.n)} hisse · <span class="pos">${fN(ev.tv)} tavan</span> · %${fN(ev.up, 0)} yükseldi · medyan ${fPct(ev.med)}</span>`;
  }
  function eikRow(it) {
    const K = EIK_KIND[it.kind] || EIK_KIND.uzman;
    const il = it.ileri ? `<span class="ek-ev il"><b>İLERİ ${eikDay(it.ileri.sig)}→${eikDay(it.ileri.day)}</b> ${fN(it.ileri.n)} hisse · ${fN(it.ileri.tv)} tavan · %${fN(it.ileri.up, 0)} yükseldi · medyan ${fPct(it.ileri.med)}</span>` : "";
    const en = isNum(it.entr) ? `<span class="ek-ev il"><b>GİRİŞTEN KAPANIŞA</b> medyan ${fPct(it.entr)}</span>` : "";
    const lbl = it.ev && it.kind !== "tanim" ? `<span class="ek-note">tek gün, korelasyon</span>` : "";
    const inl = it.tgt && it.tgt.v === "inline" ? `<div class="ek-inl" id="eik-inl-${esc(it.id)}" ${EIK.inl[it.id] ? "" : "hidden"}>${EIK.inl[it.id] || ""}</div>` : "";
    return `<button type="button" class="ek-row" data-eik="${esc(it.id)}">
      <div class="ek-t"><b>${esc(it.f)}</b> <span class="ek-sep">—</span> <span class="ek-c">${esc(it.c)}</span></div>
      <div class="ek-d">${esc(it.d)}</div>
      <div class="ek-w"><i>neden:</i> ${esc(it.why)}</div>
      <div class="ek-evs"><span class="ek-kind ${K[1]}">${K[0]}</span>${eikEv(it.ev)}${eikEv(it.ev2)}${il}${en}${lbl}${it.note ? `<span class="ek-note">${esc(it.note)}</span>` : ""}</div>
      <span class="ek-go" aria-hidden="true">›</span></button>${inl}`;
  }
  function eikRender() {
    const el = $("eik-body"); if (!el) return;
    const C = EIK.cfg;
    if (!C) { setH(el, `<div class="card"><div class="empty">${EIK.err ? "En iyi koşullar alınamadı: " + esc(EIK.err) : "En iyi koşullar yükleniyor…"}</div></div>`); return; }
    const sub = $("eik-sub"); if (sub) sub.textContent = `Son güncelleme ${C.updated_label} · ${C.items.length} özellik · ${C.label}`;
    const qv = fold((EIK.q || "").trim());
    const its = C.items.filter((it) => !qv || fold(it.f + " " + it.c + " " + it.d).includes(qv));
    const B = C.base || {}, b2 = B["20261002"], b1 = B["20261001"];
    const bs = (b) => (b ? `${eikDay(b.day)}: ${fN(b.n)} hisse · ${fN(b.tv)} tavan (%${fN(100 * b.tv / b.n, 1)}) · %${fN(b.up, 0)} yükseldi · medyan ${fPct(b.med)}` : "");
    const head = `<div class="card ek-head"><div class="ek-hl">Son güncelleme: <b>${esc(C.updated_label)}</b> · ${fN(C.items.length)} özellik · <span class="ek-lbl">${esc(C.label)}</span></div>
      <div class="ek-base">Karşılaştırma tabanı (tüm BIST) — ${esc(bs(b2))}${b1 ? " · " + esc(bs(b1)) : ""}</div>
      <div class="ek-leg"><span class="ek-kind ek-k">KANIT</span> taban oranın belirgin üstünde <span class="ek-kind ek-z">ZAYIF KANIT</span> ölçüldü, taban civarı <span class="ek-kind ek-u">UZMAN</span> kanıt canlı seansla birikecek <span class="ek-kind ek-t">TANIM GEREĞİ</span> liste zaten tavandakiler</div>
      <details class="ek-m"><summary>Yöntem ve uyarı</summary><div>${esc(C.method)}</div></details></div>`;
    const cats = C.cats.map((c) => {
      const r = its.filter((it) => it.cat === c.id); if (!r.length) return "";
      return `<div class="card ek-cat" data-eikcat="${esc(c.id)}"><div class="ek-ch"><i style="background:${esc(c.col)}"></i>${esc(c.t)} <small>${r.length}</small></div>${r.map(eikRow).join("")}</div>`;
    }).join("") || `<div class="card"><div class="empty">Eşleşen özellik yok</div></div>`;
    setH(el, head + `<div class="card ek-bir" id="eik-bir"></div>` + cats);
    eikBirRender();
  }
  function eikBirRender() {
    const el = $("eik-bir"); if (!el) return;
    const B = EIK.bir;
    const hd = (x) => `<div class="ek-ch ek-bh"><span>⭐ BİRLEŞİK ADAY LİSTESİ</span>${x || ""}<button type="button" class="ek-ref ${EIK.birBusy ? "spin" : ""}" data-eikbir="ref" aria-label="Yenile">↻</button></div>`;
    if (!B) { setH(el, hd() + `<div class="empty">${EIK.birErr ? "Alınamadı: " + esc(EIK.birErr) : "En iyi koşul taramaları birleştiriliyor…"}</div>`); return; }
    const rows = EIK.birAll ? B.rows : B.rows.slice(0, 20);
    setH(el, hd(`<small>${fN(B.rows.length)} hisse · ≥${B.min} taramada · ${fN(B.scans)} tarama${B.day_label ? " · " + esc(B.day_label) : ""} · ${esc(B.ts || "")}</small>`) +
      `<div class="ek-bl">${rows.map((r) => `<button type="button" class="ek-bs" data-eiksym="${esc(r.s)}" title="${esc(r.src.map((i) => (B.names && B.names[i]) || i).join(" · "))}"><b>${esc(r.s)}</b><span class="ek-cnt">${r.n}</span></button>`).join("") || `<div class="empty">Şu an ${B.min}+ en iyi koşul taramasında ortak hisse yok</div>`}</div>
      ${B.rows.length > 20 ? `<button type="button" class="more-btn ek-more" data-eikbir="all">${EIK.birAll ? "Daha az göster" : "Tümünü göster (" + fN(B.rows.length) + ")"}</button>` : ""}
      <div class="src-note">Rozet = hissenin göründüğü en iyi koşul taraması sayısı (KANIT etiketli ${fN(B.scans)} tarama). Aynı gün, korelasyon — al/sat önerisi değildir. Hisseye dokunun → detay.</div>`);
  }
  async function eikInline(it) {
    const id = it.id;
    if (EIK.inl[id]) { EIK.inl[id] = ""; const p = $("eik-inl-" + id); if (p) { p.hidden = true; p.innerHTML = ""; } return; }
    const show = (h) => { EIK.inl[id] = h; const p = $("eik-inl-" + id); if (p) { p.hidden = false; p.innerHTML = h; } };
    show(`<div class="empty">${esc(it.f)} taranıyor… (arka plan tarayıcısı, ~1 dk sürebilir)</div>`);
    try {
      const d = await api(it.tgt.api, { timeout: 150000 });
      const L = d[it.tgt.key] || d.stocks || d.rows || [];
      const rows = (Array.isArray(L) ? L : []).slice(0, 40);
      show(`<div class="ek-ih">${esc(it.f)} · <b>${fN(rows.length)}</b> hisse · ${esc(d.market_state === "CLOSED" ? "seans kapalı — son gün" : "canlı")}</div>` +
        (rows.length ? `<div class="ek-bl">${rows.map((r) => { const s = r.symbol || r.s; return `<span class="ek-bs" role="button" data-eiksym="${esc(s)}"><b>${esc(s)}</b><span class="${cls(r.change_pct)}">${fPct(r.change_pct)}</span></span>`; }).join("")}</div>` : `<div class="empty">Şu an bu koşulu sağlayan hisse yok</div>`) +
        `<div class="src-note">Bu özelliğin ayrı ekranı yok; en iyi koşulla sonuçlar burada gösterilir. Hisseye dokunun → detay.</div>`);
    } catch (e) { show(`<div class="empty">Alınamadı: ${esc(e.message || e)}</div>`); }
  }
  // --- ekran başına uygula / anlık görüntü / geri yükle
  function eikOp(id) { st.lastItem = /^op_\d+$/.test(id) ? id : id === "teknik" ? "sinyal" : id; opOpen(/^op_\d+$/.test(id) ? +id.slice(3) : id); }
  function eikSeg(sel, attr, val) { document.querySelectorAll(sel).forEach((b) => b.classList.toggle("active", b.dataset[attr] === val)); }
  const EIK_AP = {
    op: {
      snap(c) { const same = String(OPS.sortFor) === String(/^op_\d+$/.test(c.id) ? +c.id.slice(3) : c.id); return same ? { id: c.id, same, sort: OPS.sort, dir: OPS.dir, filt: OPS.filt, w: OPS.w, wSet: OPS.wSet, kdate: OPS.kdate } : { id: c.id, same }; },
      apply(c) { OPS.pendS = { sort: c.sort || null, dir: c.dir || -1, filt: c.filt || "", w: c.w || null, date: c.date || "" }; eikOp(c.id); if (st.view === "op" && OPS.pendS) opLoad(false); },
      restore(s) {
        if (s.same) { OPS.sort = s.sort; OPS.dir = s.dir; OPS.filt = s.filt; OPS.w = s.w; OPS.wSet = s.wSet; OPS.kdate = s.kdate; }
        else { OPS.sort = null; OPS.dir = -1; OPS.filt = ""; OPS.w = null; OPS.wSet = false; OPS.kdate = ""; }
        OPS.ktok = ""; OPS.n = OP_MK[s.id] ? 100000 : 200;
        if (st.view === "op" && String(st.opId) === String(/^op_\d+$/.test(s.id) ? +s.id.slice(3) : s.id)) opLoad(false);
      } },
    movers: {
      snap() { return { m: st.view === "movers" ? st.mvMode : "change" }; },
      apply(c) { st.lastItem = c.mode === "volume" ? "hacim" : "movers"; go(c.mode === "volume" ? "hacim" : "movers"); },
      restore(s) { st.mvMode = s.m; go(s.m === "volume" ? "hacim" : "movers", { keepMode: true, noPush: true, keepScroll: true }); } },
    akis: {
      snap() { return { kind: ak.kind }; },
      apply(c) { ak.kind = c.kind; ak.cap = 300; st.lastItem = "akis"; go("akis"); renderEvents(); },
      restore(s) { ak.kind = s.kind; ak.cap = 300; renderEvents(); } },
    baski: {
      snap() { return { sort: bk.sort, dir: bk.dir, f: bk.f }; },
      apply(c) { bk.sort = c.sort; bk.dir = c.dir; bk.f = c.f; eikSeg("#bk-filter button", "f", bk.f); st.lastItem = "baski"; go("baski"); renderBaski(); },
      restore(s) { Object.assign(bk, s); eikSeg("#bk-filter button", "f", bk.f); renderBaski(); } },
    endeks: {
      snap() { return { code: ix.code, sort: ix.sort, dir: ix.dir, f: ix.f }; },
      apply(c) { if (ix.code !== c.code) { ix.code = c.code; ix.data = null; } ix.sort = c.sort; ix.dir = c.dir; ix.f = c.f; ix.n = 150; eikSeg("#ix-filter button", "f", ix.f); st.lastItem = "endeks"; go("endeks"); renderIx(); },
      restore(s) { const ch = ix.code !== s.code; Object.assign(ix, s); eikSeg("#ix-filter button", "f", ix.f); if (ch) { ix.data = null; loadIxCatalog(); loadIx(true); } else renderIx(); } },
    kurum: {
      snap() { return { mode: kr.mode, side: kr.side, sort: kr.sort, dir: kr.dir }; },
      apply(c) { kr.mode = c.mode; kr.side = c.side; kr.sort = c.sort; kr.dir = c.dir; eikSeg("#kr-side button", "s", kr.side); st.lastItem = "kurum"; go("kurum"); },
      restore(s) { Object.assign(kr, s); eikSeg("#kr-side button", "s", kr.side); loadKurum(true); } },
    radar: {
      snap() { return { k: rd.k, sort: rd.sort }; },
      apply(c) { rd.k = c.k; rd.sort = c.sort; rd.n = 120; st.lastItem = "radar"; go("radar"); renderRadar(); },
      restore(s) { rd.k = s.k; rd.sort = s.sort; rd.n = 120; renderRadar(); } },
    tavan: {
      snap() { return { k: tt.k }; },
      apply(c) { tt.k = c.k; st.lastItem = "tavan"; go("tavan"); eikSeg("#tt-chips button", "k", tt.k); renderTT(); },
      restore(s) { tt.k = s.k; eikSeg("#tt-chips button", "k", tt.k); renderTT(); } },
    agresif: {
      snap() { return { ov: eikClone(ag.ov) }; },
      apply(c) { ag.ov = eikClone(c.o); ag.data = null; st.lastItem = "agresif"; go("agresif"); EIK.cur && (EIK.cur.extra = "Yalnız bu görünüm için filtre — bildirim ayarlarınız değişmedi"); },
      restore(s) { ag.ov = s.ov; ag.data = null; loadAg(); } },
    para: {
      snap() { return { sort: pa.sort, dir: pa.dir, f: pa.f }; },
      apply(c) { pa.sort = c.sort; pa.dir = c.dir; pa.f = c.f; eikSeg("#pa-filter button", "f", pa.f); st.lastItem = "para"; go("para"); renderPara(); },
      restore(s) { Object.assign(pa, s); eikSeg("#pa-filter button", "f", pa.f); renderPara(); } },
    sektor: { snap() { return {}; }, apply() { kfRun("sektor"); }, restore() { window.scrollTo(0, 0); } },
    kurumuyari: {
      snap() { return { tab: ku.tab }; },
      apply(c) { st.lastItem = c.tab === "rapor" ? "gunsonu" : "kurumuyari"; go("kurumuyari"); const b = document.querySelector(`#ku-tab [data-t="${c.tab}"]`); if (b && ku.tab !== c.tab) b.click(); },
      restore(s) { const b = document.querySelector(`#ku-tab [data-t="${s.tab}"]`); if (b && ku.tab !== s.tab) b.click(); } },
    tahtaci: {
      snap() { return { view: th.view, sort: th.sort, dir: th.dir, nocross: !!th.nocross }; },
      apply(c) { th.view = c.view; th.sort = c.sort; th.dir = c.dir; th.nocross = !!c.nocross; $("th-nocross").checked = th.nocross; th.data = null; eikSeg("#th-view button", "v", th.view); st.lastItem = "tahtaci"; go("tahtaci"); },
      restore(s) { Object.assign(th, s); $("th-nocross").checked = th.nocross; th.data = null; eikSeg("#th-view button", "v", th.view); $("th-broker").hidden = th.view !== "broker"; $("th-stock").hidden = th.view !== "stock"; loadTh(); } },
    akdt: {
      snap() { const S = atS(); return { f: eikClone(S.f), sort: S.sort, dir: S.dir, preset: S.preset || "", n: S.n }; },
      apply(c) { st.lastItem = "akdt"; go("akdt"); const b = document.querySelector(`#at-pre [data-atp="${c.preset}"]`); if (b) b.click(); },
      restore(s) { const S = atS(); S.f = s.f; S.sort = s.sort; S.dir = s.dir; S.preset = s.preset; if (s.n) S.n = s.n; atSave(); atRender(); } },
    akk: {
      snap() { const S = akkS(); return { f: eikClone(S.f), view: S.view, sort: S.sort || (S.view === "br" ? "wa" : "aa"), dir: S.dir }; },
      apply(c) { st.lastItem = "akk"; go("akk"); const S = akkS(); S.f.tt = true; S.f.ttg = !!c.ttg; if (S.view === "br") S.view = "bs"; S.sort = "tt"; S.dir = -1; S.n = 100; akkSave(); akkRender(); },
      restore(s) { const S = akkS(); S.f = s.f; S.view = s.view; S.sort = s.sort; S.dir = s.dir; S.n = 100; akkSave(); akkRender(); } },
    fm_mum: {
      snap() { return { f: eikClone(fmS().f.mum) }; },
      apply(c) { st.lastItem = "fm_mum"; go("fm_mum"); fmApplyPre("mum", c.pre); fmS().mum.n = 60; fmSave("mum"); fmCtl("mum"); fmRender("mum"); },
      restore(s) { fmS().f.mum = s.f; fmSave("mum"); fmCtl("mum"); fmRender("mum"); } },
    fm_grafik: {
      snap() { return { f: eikClone(fmS().f.grafik) }; },
      apply(c) { st.lastItem = "fm_grafik"; go("fm_grafik"); fmApplyPre("grafik", c.pre); fmS().grafik.n = 60; fmSave("grafik"); fmCtl("grafik"); fmRender("grafik"); },
      restore(s) { fmS().f.grafik = s.f; fmSave("grafik"); fmCtl("grafik"); fmRender("grafik"); } },
    olay: {   // v1.30.0 Olay Listesi (ALARM): hazır taramayı akışa uygula (alarm KAPALI kalır)
      snap() { return { f: eikClone(OL.f), pre: OL.pre, tab: OL.tab }; },
      apply(c) { st.lastItem = "olay"; OL.tab = "akis"; OL.pre = c.preset || null; OL.f = Object.assign(olF0(), { }); OL.n = 300; go("olay"); EIK.cur && (EIK.cur.extra = "Yalnız akış filtresi — alarm ayarlarınız değişmedi (KAPALI)"); },
      restore(s) { OL.f = s.f; OL.pre = s.pre; OL.tab = s.tab; OL.n = 300; if (st.view === "olay") { olTabs(); olLoad(); } } },
    stock: {
      snap() { return { tab: st.tab }; },
      apply(c) { go("stock"); openTab(c.tab, true); },
      restore(s) { openTab(s.tab, true); } } };
  // Genel kanca: applyConfig(ekran, ayar) — ekranın kendi hazır ayar / filtre mekanizmasını kullanır, önceki durumu saklar
  function applyConfig(screen, cfg, it) {
    const Ap = EIK_AP[screen]; if (!Ap) return false;
    eikClear();
    const tEl = $("toast"); if (tEl && !tEl.hidden) { clearTimeout(toast._t); tEl.hidden = true; }   // önceki Sıfırla bildirimi yeni afişin Sıfırla düğmesini örtmesin (üstte konumlu toast)
    let snap = null; try { snap = Ap.snap(cfg); } catch (e) { snap = null; }
    EIK.cur = { screen, cfg, snap, label: it ? `${it.f} — ${it.c}` : cfg.label || screen, view: null, opId: null, extra: "" };
    Ap.apply(cfg);
    if (!EIK.cur) return false;
    EIK.cur.view = st.view; EIK.cur.opId = st.view === "op" ? st.opId : null;
    eikBanner();
    return true;
  }
  function eikLeave(view) {
    const C = EIK.cur; if (!C || !C.view) return;
    if (view !== C.view || (view === "op" && st.opId !== C.opId)) eikClear();
  }
  function eikBanner() {
    document.querySelectorAll(".ek-ban").forEach((b) => b.remove());
    const C = EIK.cur; if (!C) return;
    const v = document.querySelector(`.view[data-view="${C.view}"]`); if (!v) return;
    const b = document.createElement("div"); b.className = "ek-ban"; b.id = "eik-ban";
    b.innerHTML = `<span class="ek-bi">⭐</span><div class="ek-bt"><b>En İyi Koşul uygulandı:</b> <span class="ek-bl2">${esc(C.label)}</span>${C.extra ? `<small>${esc(C.extra)}</small>` : ""}</div><button type="button" class="ek-rst" data-eikrst="1">Sıfırla</button><button type="button" class="ek-x" data-eikx="1" aria-label="Kapat">✕</button>`;
    const head = v.querySelector(":scope > .scr-head");
    if (head) head.after(b); else v.prepend(b);
    b.addEventListener("click", (e) => { if (e.target.closest("[data-eikrst]")) eikReset(); else if (e.target.closest("[data-eikx]")) eikClear(); });
  }
  function eikClear() { document.querySelectorAll(".ek-ban").forEach((b) => b.remove()); EIK.cur = null; }
  function eikReset() {
    const C = EIK.cur; if (!C) return;
    const Ap = EIK_AP[C.screen]; eikClear();
    try { if (C.snap) Ap.restore(C.snap, C.cfg); } catch (e) { console.warn("eik restore", e); }
    toast("Önceki ayarlarınız geri yüklendi");
  }
  function eikTap(id) {
    const it = EIK.cfg && EIK.cfg.items.find((x) => x.id === id); if (!it) return;
    if (it.tgt.v === "inline") { eikInline(it); return; }
    applyConfig(it.tgt.v, it.tgt, it);
  }
  $("eik-body").addEventListener("click", (e) => {
    const s = e.target.closest("[data-eiksym]"); if (s) { e.stopPropagation(); openStock(s.dataset.eiksym); return; }
    const bb = e.target.closest("[data-eikbir]"); if (bb) { if (bb.dataset.eikbir === "all") { EIK.birAll = !EIK.birAll; eikBirRender(); } else eikBir(true); return; }
    const r = e.target.closest("[data-eik]"); if (r) eikTap(r.dataset.eik);
  });
  $("eik-q").addEventListener("input", (e) => { EIK.q = e.target.value; clearTimeout(EIK._t); EIK._t = setTimeout(eikRender, 150); });

  // ===================================================================== v1.30.0 ==
  // ---- OLAY LİSTESİ (ALARM): tüm hisselerde POC Baskısı OLAY LİSTESİ olayları (sunucu: app/v130.py · /api/olay/*)
  //      AKIŞ (filtreli, satıra dokun → hissenin POC detayı o olayda) · ALARMLAR (tür başına aç/kapa + gelişmiş) · HAZIR TARAMALAR
  //      Bildirim mevcut yoldan (hub → Web Push / OneSignal, gönderim mantığı aynı); tüm alarmlar varsayılan KAPALI.
  const olF0 = () => ({ grp: "all", k: "", d: "", tl: 0, lot: 0, n: 0, q: "" });
  const OL = { tab: "akis", d: null, err: "", day: "", f: olF0(), n: 300, busy: false, tm: null, al: null, alErr: "", pr: null, open: { rksw: true }, pre: null, hl: null, gen: 0 };
  const OL_GRP = [["all", "TÜMÜ", ""], ["kay", "KAYMALAR", "up,dn"], ["ds", "DESTEK / DİRENÇ", "dt,db,dk,rt,rr,rk"], ["sw", "SÜPÜRME", "sw"], ["sen", "SENARYO", "sen"], ["kombi", "KIRILIM + SÜPÜRME", "rksw"]];
  const OL_EV = { up: ["YÜKSELTME", "pos"], dn: ["DÜŞÜRME", "neg"], dt: ["DESTEK TEMASI", ""], db: ["DESTEK TEPKİSİ", "pos"], dk: ["DESTEK KIRILDI", "neg"], rt: ["DİRENÇ TEMASI", ""],
    rr: ["DİRENÇ REDDİ", "neg"], rk: ["DİRENÇ KIRILDI", "pos"], sw: ["SÜPÜRME", "pos"], sen: ["SENARYO", "pos"], rksw: ["DİRENÇ KIRILDI + SÜPÜRME", "pos"],
    p_hk: ["HACİMLİ KIRILIM (GÜÇLÜ)", "pos"], p_ard: ["ART ARDA SÜPÜRME", "pos"], p_pocsw: ["POC YÜKSELTME + SÜPÜRME", "pos"], p_dbsw: ["DESTEK TEPKİSİ + SÜPÜRME", "pos"], p_tvy: ["TAVAN YOLU", "pos"] };
  const OL_BDF = { up: "kay", dn: "kay", dt: "ds", db: "ds", dk: "ds", rt: "ds", rr: "ds", rk: "ds", sw: "sw", sen: "sen" };
  const OL_AD = { rksw: "POC direnci kırıldı ve ±pencere içinde kırılan seviyenin üstüne (seviyede/üstünde) eşik üstü yukarı süpürme — gerçek, hacimli kırılım",
    p_hk: "Birleşik alarmın yalnız GÜÇLÜ olanları", p_ard: "10 dk içinde ≥4 yukarı süpürme (her biri ≥4 kademe)", p_pocsw: "POC yükseltildi + yeni POC üstüne ≥5 kademe süpürme",
    p_dbsw: "Destek tepkisi + seviye üstüne ≥5 kademe / ≥500 bin ₺ süpürme", p_tvy: "Kırılım + süpürme · tavana ≤%6 · gün ≥+%3",
    rk: "Fiyat POC direncini max(2 adım, %0,3) yukarı kırdı", sw: "Aynı saniyede aktif alışla ≥2 kademe yukarı süpürme", up: "POC ≥60 sn kalıcı yükseldi", db: "POC desteğine temas + tepki",
    sen: "CİDDİ YÜKSELİŞ / TAVAN ADAYI senaryosuna giriş", rt: "Alttan POC direncine temas", rr: "Direnç temasından aşağı dönüş", dt: "Üstten POC desteğine temas", dk: "POC desteği aşağı kırıldı", dn: "POC ≥60 sn kalıcı düştü" };
  const olDay = (d) => (d ? d.slice(6, 8) + "." + d.slice(4, 6) : "");
  const olTl = (v) => (!isNum(v) ? "—" : v >= 1e9 ? fN(v / 1e9, 2) + " Mr" : v >= 1e6 ? fN(v / 1e6, 1) + " Mn" : v >= 1e3 ? fN(v / 1e3, 0) + " bin" : fN(v, 0));
  function olOpen() {
    olTabs();
    if (OL.tab === "akis") olLoad(); else if (OL.tab === "alarm") olAlLoad(); else olPrLoad();
    clearInterval(OL.tm);
    OL.tm = setInterval(() => { if (st.view !== "olay") { clearInterval(OL.tm); return; } if (!document.hidden && OL.tab === "akis" && OL.d && (OL.d.live || !OL.d.ready)) olLoad(true); }, 5000);
  }
  function olTabs() { document.querySelectorAll("#ol-tab button").forEach((b) => b.classList.toggle("active", b.dataset.olt === OL.tab)); }
  function olKeys() {
    if (OL.pre) return OL.pre;
    if (OL.f.k) return OL.f.k;
    const g = OL_GRP.find((x) => x[0] === OL.f.grp); return g ? g[2] : "";
  }
  async function olLoad(quiet) {
    const g = ++OL.gen;
    const p = new URLSearchParams({ limit: String(OL.n) });
    if (OL.day) p.set("date", OL.day);
    const k = olKeys(); if (k) p.set("k", k);
    if (OL.f.d) p.set("d", OL.f.d);
    if (OL.f.tl) p.set("min_tl", String(OL.f.tl));
    if (OL.f.lot) p.set("min_lot", String(OL.f.lot));
    if (OL.f.n) p.set("min_n", String(OL.f.n));
    if (OL.f.q) p.set("sym", OL.f.q);
    if (!quiet && !OL.d) olRender();
    OL.busy = true;
    try { const d = await api(`/api/olay/feed?${p.toString()}`, { timeout: 60000 }); if (g !== OL.gen) return; OL.d = d; OL.err = ""; if (!OL.day && d.day) OL.dayAuto = d.day; }
    catch (e) { if (g === OL.gen) OL.err = e.message || String(e); }
    OL.busy = false;
    if (g === OL.gen && st.view === "olay" && OL.tab === "akis") { olRender(); if (OL.d && !OL.d.ready) setTimeout(() => { if (st.view === "olay" && OL.tab === "akis") olLoad(true); }, 4000); }
  }
  function olRender() {
    if (OL.tab === "alarm") return olAlRender();
    if (OL.tab === "hazir") return olPrRender();
    const el = $("ol-body"); if (!el) return;
    const d = OL.d;
    if (!d) { setH(el, `<div class="card"><div class="empty">${OL.err ? "Olaylar alınamadı: " + esc(OL.err) : "Olaylar yükleniyor…"}</div></div>`); return; }
    const sub = $("ol-sub"); if (sub) sub.textContent = `${d.live ? "CANLI · " : ""}${d.day_label || d.day || ""} · ${d.ready ? fN(d.total || 0) + " olay · tüm hisseler" : "hesaplanıyor…"}`;
    if (!d.ready) { setH(el, `<div class="card"><div class="empty">${esc(d.note || "Hesaplanıyor…")}</div></div>`); return; }
    const C = d.counts || {};
    const gc = (g) => (g[2] ? g[2].split(",").reduce((a, k) => a + (C[k] || 0), 0) : Object.keys(C).filter((k) => !/^p_/.test(k)).reduce((a, k) => a + C[k], 0));
    const days = (d.days || []).map((x) => `<button type="button" data-olday="${x}" class="${(OL.day || d.day) === x ? "active" : ""}">${olDay(x)}${d.live && x === d.day ? " · CANLI" : ""}</button>`).join("");
    const grp = OL_GRP.map((g) => `<button type="button" data-olg="${g[0]}" class="${!OL.pre && !OL.f.k && OL.f.grp === g[0] ? "active" : ""}">${g[1]} ${fN(gc(g))}</button>`).join("");
    const opt = (v, cur, l) => `<option value="${v}" ${String(cur) === String(v) ? "selected" : ""}>${l}</option>`;
    const types = ["", "rk", "rksw", "sw", "up", "db", "sen", "rt", "rr", "dt", "dk", "dn"].map((k) => opt(k, OL.f.k, k ? `${OL_EV[k][0]} (${fN(C[k] || 0)})` : "Tür: hepsi")).join("");
    const pre = OL.pre ? `<div class="ek-ban ol-preban"><span class="ek-bi">⚡</span><div class="ek-bt"><b>Hazır tarama:</b> ${esc((OL_EV[OL.pre] || [OL.pre])[0])} <small>yalnız akış filtresi — alarm KAPALI</small></div><button type="button" class="ek-rst" data-olpreclr="1">Sıfırla</button></div>` : "";
    const rows = (d.events || []).map((e) => {
      const L = OL_EV[e.k] || [e.lab || e.k, ""];
      return `<tr data-ols="${esc(e.s)}" data-olt="${e.t}" data-olk="${e.k}" data-olrk="${e.t_rk || ""}"><td class="l sticky">${kmHms(e.t)}</td><td class="l"><b class="sym">${esc(e.s)}</b>${isNum(e.gd) ? `<small class="${cls(e.gd)}">${fPct(e.gd, 1)}</small>` : ""}</td>
        <td class="l"><b class="${L[1]}">${esc(e.lab || L[0])}</b>${e.g === 2 ? ' <span class="ol-g g2">GÜÇLÜ</span>' : e.g === 1 ? ' <span class="ol-g">ORTA</span>' : ""}</td><td class="l op-txt"><div class="tx-2l">${esc(brName(e.x || ""))}</div></td></tr>`;
    }).join("");
    setH(el, `<section class="card ol-feed">
      <div class="card-h"><span class="card-title">OLAY AKIŞI</span><span class="muted sm">${fN(d.n)} eşleşme · yeni → eski${d.built_at ? " · " + esc(d.built_at) : ""}</span></div>
      <div class="km-rng ol-days">${days}</div>
      <div class="km-rng ol-grp">${grp}</div>
      <div class="ol-flt">
        <select data-olf="k" aria-label="Tür">${types}</select>
        <select data-olf="d" aria-label="Yön">${opt("", OL.f.d, "Yön: hepsi")}${opt("up", OL.f.d, "Yukarı")}${opt("dn", OL.f.d, "Aşağı")}${opt("nt", OL.f.d, "Nötr (temas)")}</select>
        <select data-olf="tl" aria-label="Min ₺">${[0, 250000, 500000, 1e6, 2e6, 5e6].map((v) => opt(v, OL.f.tl, v ? "≥ " + olTl(v) + " ₺" : "Min ₺: yok")).join("")}</select>
        <select data-olf="n" aria-label="Min kademe">${[0, 2, 3, 4, 5, 6, 8].map((v) => opt(v, OL.f.n, v ? "≥ " + v + " kademe" : "Min kademe: yok")).join("")}</select>
        <input type="number" inputmode="numeric" min="0" step="1000" data-olf="lot" placeholder="Min lot" value="${OL.f.lot || ""}" aria-label="Min lot" />
        <input type="search" data-olf="q" placeholder="Hisse" value="${esc(OL.f.q)}" autocomplete="off" spellcheck="false" aria-label="Hisse" />
      </div>
      ${pre}
      <div class="tbl-scroll"><table class="grid-table op-table ol-tbl"><thead><tr><th class="l sticky">SAAT</th><th class="l">HİSSE</th><th class="l">OLAY</th><th class="l">AYRINTI</th></tr></thead><tbody>
      ${rows || `<tr><td colspan="4" class="empty">Bu filtrelerle olay yok</td></tr>`}</tbody></table></div>
      ${d.n > (d.events || []).length ? `<button type="button" class="more-btn" data-olmore="1">Daha fazla göster (${fN((d.events || []).length)} / ${fN(d.n)})</button>` : ""}
      <div class="src-note">Kaynak: POC Baskısı OLAY LİSTESİ ile aynı motor (v124), tüm hisseler için artımlı: canlı seansta işlem akışından anlık, kayıtlı günde diskten yeniden oynatma. Satıra dokunun → hissenin POC detayı o olayda açılır. Süpürme = aynı saniyede aktif alışla ≥2 kademe yukarı (≥100 bin ₺). DİRENÇ KIRILDI + SÜPÜRME eşikleri ALARMLAR sekmesindeki ayarlardan.</div>
    </section>`);
  }
  function olOpenAt(sym, t, k, trk) {
    const day = (OL.d && OL.d.day) || "";
    bdOpen(sym, "k_poc", day);
    const isTr = /^(rksw|p_)/.test(k);
    BD.at = isTr && trk ? +trk : +t; BD.atK = isTr ? (trk ? "rk" : "sw") : k; BD.flt = isTr ? "all" : (OL_BDF[k] || "all"); BD.n = 100000;
    if (isTr && !trk) { BD.atK = null; }
  }
  // ---- ALARMLAR
  async function olAlLoad() {
    try { OL.al = await api("/api/olay/alarms", { timeout: 15000 }); OL.alErr = ""; } catch (e) { OL.alErr = e.message || String(e); }
    if (!OL.pr) { try { OL.pr = await api("/api/olay/presets", { timeout: 15000 }); } catch (e) {} }
    if (st.view === "olay" && OL.tab === "alarm") olAlRender();
  }
  async function olAlPost(body) {
    try { OL.al = await api("/api/olay/alarms", { method: "POST", body: JSON.stringify(body), headers: { "Content-Type": "application/json" }, timeout: 15000 }); return true; }
    catch (e) { toast("Alarm ayarı kaydedilemedi"); return false; }
  }
  const olLab = (k) => (OL.al && OL.al.labels && OL.al.labels[k]) || (OL_EV[k] || [k])[0];
  function olFld(k, f, l, a, type, extra) {
    const v = a[f];
    if (type === "sel") return `<label class="ol-fd"><span>${l}</span><select data-olaf="${k}:${f}">${extra.map(([x, y]) => `<option value="${x}" ${String(v) === String(x) ? "selected" : ""}>${y}</option>`).join("")}</select></label>`;
    if (type === "chk") return `<label class="ol-fd ol-chk"><input type="checkbox" data-olaf="${k}:${f}" ${v ? "checked" : ""}/><span>${l}</span></label>`;
    if (type === "time") return `<label class="ol-fd"><span>${l}</span><input type="time" data-olaf="${k}:${f}" value="${esc(v || "")}" /></label>`;
    if (type === "txt") return `<label class="ol-fd wide"><span>${l}</span><input type="text" data-olaf="${k}:${f}" value="${esc((v || []).join(", "))}" placeholder="örn. SAFKR, ORGE, THYAO" autocomplete="off" spellcheck="false" /></label>`;
    return `<label class="ol-fd"><span>${l}</span><input type="number" inputmode="numeric" min="0" step="${extra || 1}" data-olaf="${k}:${f}" value="${isNum(v) ? v : ""}" /></label>`;
  }
  function olAlForm(k, a) {
    const cmb = k === "rksw";
    const f = [];
    if (cmb) {
      f.push(olFld(k, "n", "Min kademe (süpürme)", a, "num", 1), olFld(k, "tl", "Min ₺ (süpürme)", a, "num", 50000), olFld(k, "lot", "Min lot (süpürme)", a, "num", 1000),
        olFld(k, "win", "Pencere ± sn (kırılım ↔ süpürme)", a, "num", 10), olFld(k, "hold", "Seviyenin üstünde tutunma (sn, 0 = yok)", a, "num", 10),
        olFld(k, "pre", "Kırılımdan ÖNCEKİ süpürme de sayılsın", a, "chk"),
        olFld(k, "grade", "Derece", a, "sel", [[1, "ORTA ve GÜÇLÜ"], [2, "Yalnız GÜÇLÜ"]]), olFld(k, "g_n", "GÜÇLÜ: min kademe", a, "num", 1), olFld(k, "g_tl", "GÜÇLÜ: min ₺", a, "num", 100000));
    }
    if (k === "sw") f.push(olFld(k, "min_n", "Min kademe", a, "num", 1));
    if (!cmb) f.push(olFld(k, "min_tl", "Min ₺", a, "num", 50000), olFld(k, "min_lot", "Min lot", a, "num", 1000));
    f.push(olFld(k, "scope", "Kapsam", a, "sel", [["all", "Tüm hisseler"], ["list", "İzleme listesi"]]));
    if (a.scope === "list") f.push(olFld(k, "syms", "İzleme listesi (virgülle)", a, "txt"));
    f.push(olFld(k, "from", "Saat: başlangıç", a, "time"), olFld(k, "to", "Saat: bitiş", a, "time"), olFld(k, "cd", "Hisse başına soğuma (dk)", a, "num", 5), olFld(k, "rate", "Saatte en çok bildirim", a, "num", 1));
    const nt = "ol_" + k;
    return `<div class="ol-form">${f.join("")}</div>
      ${NT[nt] ? `<div class="ol-nt"><small class="muted">Bu cihazda bildirim türü (KAPALI / GÖRÜNTÜLE / BİLDİRİM):</small>${ntRow(nt, true)}</div>` : ""}
      <div class="ol-acts"><button type="button" class="btn-primary sm" data-olsave="${k}">Kaydet</button><button type="button" class="btn-ghost sm" data-olsample="${k}">Örnek bildirim (kuru çalıştırma)</button></div>`;
  }
  function olAlRow(k, a, big) {
    const st0 = OL.open[k] || big;
    return `<div class="ol-al ${a.on ? "on" : ""} ${OL.hl === k ? "hl" : ""}" data-olrow="${k}">
      <div class="ol-al-h"><div class="ol-al-t"><b>${esc(olLab(k))}</b><small>${esc(OL_AD[k] || "")}</small></div>
        <label class="nf-sw ol-sw"><input type="checkbox" data-olon="${k}" ${a.on ? "checked" : ""}/><span></span>${a.on ? "AÇIK" : "KAPALI"}</label>
        ${big ? "" : `<button type="button" class="btn-ghost sm ol-gear" data-olset="${k}" aria-label="Gelişmiş">${st0 ? "▲" : "⚙"}</button>`}</div>
      ${st0 ? olAlForm(k, a) : ""}</div>`;
  }
  function olAlRender() {
    const el = $("ol-body"); if (!el || OL.tab !== "alarm") return;
    const A = OL.al;
    if (!A) { setH(el, `<div class="card"><div class="empty">${OL.alErr ? "Alarm ayarları alınamadı: " + esc(OL.alErr) : "Alarm ayarları yükleniyor…"}</div></div>`); return; }
    const al = A.alarms || {}, keys = A.keys || [];
    const pr = keys.filter((k) => /^p_/.test(k)), ev = keys.filter((k) => !/^p_/.test(k) && k !== "rksw");
    const cmbSt = OL.pr && OL.pr.stats && OL.pr.stats.rksw;
    const s2 = cmbSt && cmbSt["20261002"];
    setH(el, `<section class="card ol-mgr"><div class="card-h"><span class="card-title">ALARM YÖNETİCİSİ</span><span class="ol-cnt ${A.n_on ? "on" : ""}">${fN(A.n_on)} açık / ${fN(keys.length)}</span></div>
        <div class="src-note">Varsayılan: <b>tüm alarmlar KAPALI</b>. Açtığınız alarm bu cihazda ilgili bildirim türünü BİLDİRİM moduna alır (bant + ses + Web Push / Telegram — mevcut gönderim yolu). Soğuma hisse başına, oran sınırı alarm başına saatliktir; ek olarak tüm olay alarmları için saatte en çok 60, döngü başına 6 bildirim.</div>
        ${A.n_on ? `<button type="button" class="btn-ghost sm" data-olalloff="1">Tümünü kapat</button>` : ""}</section>
      <section class="card ol-cmb"><div class="card-h"><span class="card-title">⭐ DİRENÇ KIRILDI + SÜPÜRME (yukarı)</span><span class="muted sm">birleşik alarm</span></div>
        ${olAlRow("rksw", al.rksw || {}, true)}
        ${s2 ? `<div class="src-note">Varsayılanlar Cuma 02.10 + 01.10 optimizasyonundan (HAZIR TARAMALAR › tablo): ≥${A.combo_def.n} kademe, ≥${olTl(A.combo_def.tl)} ₺, ±${A.combo_def.win} sn, tutunma ${A.combo_def.hold} sn. 02.10'da ${fN(s2.n)} hisse tetiklendi; ilk tetiklerin %${fN(s2.hit3_60, 1)}'i 60 dk içinde ≥+%3 (yalnız DİRENÇ KIRILDI: %${fN(OL.pr.stats.base_rk["20261002"].hit3_60, 1)}), %${fN(s2.tt, 1)}'i tavana dokundu. Kademe 1 ile 2 aynıdır (süpürme tanımı ≥2 kademe); 2 kademe sinyali yalnız kırılımdan pek ayırmıyor (%${fN(OL.pr.stats.rksw_n2["20261002"].hit3_60, 1)}).</div>` : ""}
      </section>
      <section class="card"><div class="card-h"><span class="card-title">HAZIR TARAMA ALARMLARI</span><span class="muted sm">${pr.length}</span></div>${pr.map((k) => olAlRow(k, al[k] || {})).join("")}</section>
      <section class="card"><div class="card-h"><span class="card-title">OLAY TÜRÜ ALARMLARI</span><span class="muted sm">${ev.length}</span></div>${ev.map((k) => olAlRow(k, al[k] || {})).join("")}</section>
      ${(A.sent || []).length ? `<section class="card"><div class="card-h"><span class="card-title">SON GÖNDERİLENLER</span></div>${A.sent.slice().reverse().slice(0, 10).map((r) => `<div class="ol-sent"><b>${esc(r.title)}</b><small>${esc(r.text)}</small></div>`).join("")}</section>` : ""}`);
    if (OL.hl) { const r = document.querySelector(`[data-olrow="${OL.hl}"]`); OL.hl = null; if (r) { window.dispatchEvent(new Event("wheel")); r.scrollIntoView({ block: "center" }); } }
  }
  function olFormVals(k) {
    const o = {};
    document.querySelectorAll(`[data-olaf^="${k}:"]`).forEach((inp) => {
      const f = inp.dataset.olaf.split(":")[1];
      if (inp.type === "checkbox") o[f] = inp.checked;
      else if (f === "syms") o[f] = inp.value.split(/[,\s]+/).map((x) => x.trim().toUpperCase()).filter(Boolean);
      else if (inp.type === "time" || f === "scope") o[f] = inp.value;
      else if (inp.value !== "") o[f] = +inp.value;
    });
    return o;
  }
  async function olToggle(k, on) {
    if (!(await olAlPost({ alarms: { [k]: { on } } }))) { olAlRender(); return; }
    const nt = "ol_" + k;
    if (NT[nt]) { NP.modes[nt] = on ? (rawMode(nt) === "off" ? "notify" : rawMode(nt)) : "off"; saveNP(); refreshNtRows(nt); }
    if (on) askNotify(true);
    toast(on ? `Alarm açıldı: ${olLab(k)} — bildirim türü ${NT[nt] ? (rawMode(nt) === "notify" ? "BİLDİRİM" : "GÖRÜNTÜLE") : ""}` : `Alarm kapatıldı: ${olLab(k)}`);
    olAlRender();
  }
  async function olSample(k) {   // kuru çalıştırma: yalnız bu cihazda üst bant (push / sunucu bildirimi YOK)
    let e = null;
    try { const d = await api(`/api/olay/feed?k=${encodeURIComponent(k)}&limit=1${OL.day ? "&date=" + OL.day : ""}`, { timeout: 30000 }); e = (d.events || [])[0]; } catch (x) {}
    const lab = (e && e.lab) || olLab(k);
    const ev = e ? { title: `${/^(rksw|p_)/.test(k) ? "🚀" : (OL_EV[k] || [, ""])[1] === "neg" ? "🔴" : "🟢"} ${e.s} · ${lab}`, text: `${e.x} · ${kmHms(e.t)}`, time: kmHms(e.t), nt: "ol_" + k, sym: e.s }
      : { title: `🚀 ÖRNEK · ${lab}`, text: "Bu gün için örnek olay bulunamadı", time: clockFmt.format(new Date()), nt: "ol_" + k };
    banner(ev, "view");
    toast("Örnek bildirim gösterildi (kuru çalıştırma — push gönderilmedi)");
    return ev;
  }
  // ---- HAZIR TARAMALAR
  async function olPrLoad() {
    if (!OL.pr) { try { OL.pr = await api("/api/olay/presets", { timeout: 15000 }); } catch (e) { OL.prErr = e.message || String(e); } }
    if (!OL.al) { try { OL.al = await api("/api/olay/alarms", { timeout: 15000 }); } catch (e) {} }
    if (st.view === "olay" && OL.tab === "hazir") olPrRender();
  }
  function olStRow(lab, s) {
    if (!s || !s.n) return `<tr><td class="l">${lab}</td><td colspan="7" class="muted">yetersiz örnek</td></tr>`;
    return `<tr><td class="l">${lab}</td><td>${fN(s.n)}<small class="muted">/${fN(s.n_all)}</small></td><td><b>%${fN(s.hit3_60, 1)}</b></td><td>${fPct(s.r60, 2)}</td><td class="${cls(s.c_med)}">${fPct(s.c_med, 2)}</td><td>%${fN(s.tt, 1)}</td><td>${fN(s.E_med, 2)}</td><td>${s.recall_big == null ? "—" : "%" + fN(s.recall_big, 1)}</td></tr>`;
  }
  function olStTbl(S) {
    return `<div class="tbl-scroll"><table class="grid-table ol-st"><thead><tr><th class="l">GÜN</th><th>HİSSE/TETİK</th><th>60dk ≥+%3</th><th>60dk medyan</th><th>KAPANIŞA</th><th>TAVANA DOKUNDU</th><th>ERKEN (E)</th><th>CİDDİ YÜKS. ERKEN</th></tr></thead><tbody>
      ${olStRow("Cuma 02.10", S["20261002"])}${olStRow("01.10 (eksik kayıt)", S["20261001"])}</tbody></table></div>`;
  }
  function olPrRender() {
    const el = $("ol-body"); if (!el || OL.tab !== "hazir") return;
    const P = OL.pr;
    if (!P) { setH(el, `<div class="card"><div class="empty">${OL.prErr ? "Alınamadı: " + esc(OL.prErr) : "Hazır taramalar yükleniyor…"}</div></div>`); return; }
    const S = P.stats || {}, B = S.base_rk || {};
    const cards = Object.entries(P.presets || {}).map(([k, p]) => {
      const al = (OL.al && OL.al.alarms && OL.al.alarms[k]) || {};
      return `<section class="card ol-pr" data-olpr="${k}"><div class="card-h"><span class="card-title">${esc(p.l)}${P.best === k ? ' <span class="ol-best">EN İYİ</span>' : ""}</span><span class="ol-cnt ${al.on ? "on" : ""}">${al.on ? "ALARM AÇIK" : "ALARM KAPALI"}</span></div>
        <div class="ol-prd">${esc(p.d)}</div>
        ${S[k] ? olStTbl(S[k]) : `<div class="empty">İstatistik yok</div>`}
        <div class="ol-acts"><button type="button" class="btn-primary sm" data-olpre="${k}">Akışa uygula</button><button type="button" class="btn-ghost sm" data-olmk="${k}">Alarm yap (KAPALI)</button></div></section>`;
    }).join("");
    const O = P.opt || {}, tbl = (rows, key) => `<div class="tbl-scroll"><table class="grid-table ol-st"><thead><tr><th class="l">${key}</th><th>02.10 hisse/tetik</th><th>60dk ≥+%3</th><th>15/30/60dk medyan</th><th>kapanışa</th><th>tavana dok.</th><th>E</th><th>ciddi yüks. erken</th><th>01.10 hisse</th><th>60dk ≥+%3</th><th>tavana dok.</th></tr></thead><tbody>
      ${(rows || []).map((r) => { const a = r["20261002"] || {}, b = r["20261001"] || {}; const lab = key === "KADEME" ? "≥" + r.n : key === "₺" ? "≥" + olTl(r.tl) : key === "PENCERE" ? "±" + r.win + " sn" : r.hold + " sn";
        const sel = r.n === P.combo.n && r.tl === P.combo.tl && r.win === P.combo.win && r.hold === P.combo.hold;
        return `<tr class="${sel ? "ol-sel" : ""}"><td class="l">${lab}${sel ? " ✓" : ""}</td><td>${fN(a.n)}/${fN(a.n_all)}</td><td><b>%${fN(a.hit3_60, 1)}</b></td><td>${fN(a.r15, 2)} / ${fN(a.r30, 2)} / ${fN(a.r60, 2)}</td><td>${fPct(a.c_med, 2)}</td><td>%${fN(a.tt, 1)}</td><td>${fN(a.E_med, 2)}</td><td>%${fN(a.recall_big, 1)}</td><td>${fN(b.n)}</td><td>%${fN(b.hit3_60, 1)}</td><td>%${fN(b.tt, 1)}</td></tr>`; }).join("")}</tbody></table></div>`;
    setH(el, `<section class="card"><div class="card-h"><span class="card-title">HAZIR TARAMALAR</span><span class="muted sm">ciddi yükselişi erken yakalamak için</span></div>
        <div class="src-note">Her tarama tüm hisselerde olay akışından hesaplanır. Tablo: hisse başına İLK tetik; <b>60dk ≥+%3</b> = tetikten sonraki 60 dk içinde en az +%3; <b>TAVANA DOKUNDU</b> = tetikten sonra; <b>ERKEN (E)</b> = açılış→gün zirvesi hareketinin tetik anında kalan payı (1 = en başta); <b>CİDDİ YÜKS. ERKEN</b> = günün ciddi yükselenlerinin (açılış→zirve ≥%8 ya da tavan) hareketinin yarısı önündeyken yakalanma oranı. Taban (yalnız DİRENÇ KIRILDI) 02.10: 60dk ≥+%3 %${fN((B["20261002"] || {}).hit3_60, 1)}, tavana dokunma %${fN((B["20261002"] || {}).tt, 1)}. <b>Örneklem içi, yalnız 2 gün — kesin değil, al/sat önerisi değildir.</b></div></section>
      ${cards}
      <section class="card"><details class="ol-opt"><summary>Optimizasyon tablosu · DİRENÇ KIRILDI + SÜPÜRME (${fN(O.grid_n || 0)} kombinasyon tarandı)</summary>
        <div class="src-note">${esc(O.note || "")} En az örnek: ${esc(O.min_count || "")}. Seçilen: ≥${P.combo.n} kademe · ≥${olTl(P.combo.tl)} ₺ · ±${P.combo.win} sn · tutunma ${P.combo.hold} sn (✓).</div>
        <h4 class="ol-h4">Min kademe (₺ ≥500 bin, ±300 sn, tutunma 0)</h4>${tbl(O.kademe, "KADEME")}
        <h4 class="ol-h4">Min ₺ (≥4 kademe, ±300 sn)</h4>${tbl(O.tl, "₺")}
        <h4 class="ol-h4">Pencere (≥4 kademe, ≥500 bin ₺)</h4>${tbl(O.win, "PENCERE")}
        <h4 class="ol-h4">Tutunma (fiyat seviyenin üstünde X sn)</h4>${tbl(O.hold, "TUTUNMA")}</details></section>`);
  }
  // ---- olaylar
  $("ol-tab").addEventListener("click", (e) => { const b = e.target.closest("[data-olt]"); if (!b) return; OL.tab = b.dataset.olt; olTabs(); olOpen(); });
  $("ol-body").addEventListener("click", async (e) => {
    const r = e.target.closest("tr[data-ols]"); if (r) { olOpenAt(r.dataset.ols, +r.dataset.olt, r.dataset.olk, r.dataset.olrk); return; }
    const b = e.target.closest("button"); if (!b) return;
    if (b.dataset.olday) { OL.day = b.dataset.olday; OL.n = 300; OL.d = null; olLoad(); return; }
    if (b.dataset.olg) { OL.f.grp = b.dataset.olg; OL.f.k = ""; OL.pre = null; OL.n = 300; olLoad(); return; }
    if (b.dataset.olmore) { OL.n += 600; olLoad(); return; }
    if (b.dataset.olpreclr) { OL.pre = null; OL.n = 300; olLoad(); return; }
    if (b.dataset.olset) { const k = b.dataset.olset; OL.open[k] = !OL.open[k]; olAlRender(); return; }
    if (b.dataset.olsave) { const k = b.dataset.olsave; if (await olAlPost({ alarms: { [k]: olFormVals(k) } })) { toast(`Kaydedildi: ${olLab(k)}`); olAlRender(); if (k === "rksw") OL.d = null; } return; }
    if (b.dataset.olsample) { olSample(b.dataset.olsample); return; }
    if (b.dataset.olalloff) { if (await olAlPost({ all_off: true })) { (OL.al.keys || []).forEach((k) => { const nt = "ol_" + k; if (NT[nt]) NP.modes[nt] = "off"; }); saveNP(); toast("Tüm olay alarmları kapatıldı"); olAlRender(); } return; }
    if (b.dataset.olpre) { OL.pre = b.dataset.olpre; OL.f = olF0(); OL.n = 300; OL.tab = "akis"; olTabs(); OL.d = null; olLoad(); window.scrollTo(0, 0); toast(`Akışa uygulandı: ${(OL_EV[OL.pre] || [OL.pre])[0]} (alarm KAPALI)`); return; }
    if (b.dataset.olmk) { const k = b.dataset.olmk; if (await olAlPost({ alarms: { [k]: { on: false } } })) { OL.tab = "alarm"; OL.open[k] = true; OL.hl = k; olTabs(); olAlRender(); toast("Alarm hazır (KAPALI) — açmak için anahtara dokunun"); } return; }
  });
  $("ol-body").addEventListener("change", (e) => {
    const t = e.target;
    if (t.dataset.olon) { olToggle(t.dataset.olon, t.checked); return; }
    if (t.dataset.olaf && t.dataset.olaf.endsWith(":scope")) { const k = t.dataset.olaf.split(":")[0]; OL.al.alarms[k] = Object.assign({}, OL.al.alarms[k], olFormVals(k)); olAlRender(); return; }
    if (t.dataset.olf && t.dataset.olf !== "q" && t.dataset.olf !== "lot") { const f = t.dataset.olf; OL.f[f] = f === "k" || f === "d" ? t.value : +t.value || 0; if (f === "k") OL.pre = null; OL.n = 300; olLoad(); }
  });
  $("ol-body").addEventListener("input", (e) => {
    const t = e.target; if (t.dataset.olf !== "q" && t.dataset.olf !== "lot") return;
    clearTimeout(OL._t); OL._t = setTimeout(() => { OL.f[t.dataset.olf] = t.dataset.olf === "q" ? trUpper(t.value.trim()) : (+t.value || 0); OL.n = 300; olLoad(); }, 350);
  });
  // ---- TÜM ALARMLAR (ayarlar) — sayaç: açık bildirim türü + açık fiyat alarmı + açık olay alarmı
  function allAlCount() {
    const types = Object.keys(NT).filter((k) => k !== "tren_atla" && NP.master !== false && rawMode(k) !== "off").length;   // v1.31.0 TRENE ATLA ayrı anahtarla yönetilir
    const price = st.alarms.filter((a) => !a.off).length;
    const ev = (OL.al && OL.al.n_on) || 0;
    return { types, nTypes: Object.keys(NT).length - 1, price, nPrice: st.alarms.length, ev, nEv: (OL.al && (OL.al.keys || []).length) || 16, total: types + price + ev };
  }
  function allAlCard() {
    const c = allAlCount(), bk = LS.get("np_before_v1300", null);
    return `<section class="card nf-allal" id="nf-allal-card"><div class="card-h"><span class="card-title">TÜM ALARMLAR</span>
        <label class="nf-sw"><input type="checkbox" id="nf-allal" ${c.total > 0 ? "checked" : ""}/><span></span><b id="nf-allal-n">${fN(c.total)} açık</b></label></div>
      <div class="nf-cnt" id="nf-allal-d"><span class="nf-mode ${c.types ? "notify" : "off"}">BİLDİRİM TÜRÜ ${fN(c.types)}/${fN(c.nTypes)}</span><span class="nf-mode ${c.price ? "notify" : "off"}">FİYAT ALARMI ${fN(c.price)}/${fN(c.nPrice)}</span><span class="nf-mode ${c.ev ? "notify" : "off"}">OLAY ALARMI ${fN(c.ev)}/${fN(c.nEv)}</span></div>
      <div class="src-note">v1.30.0: tüm alarm ve bildirim türleri <b>KAPALI</b> konuma getirildi (önceki durum yedeklendi; fiyat alarmlarınız silinmedi, Alarmlar sekmesinde KAPALI olarak duruyor). İstediklerinizi aşağıdan tek tek açın. Anahtar KAPALI → hepsini kapatır (seçiminiz hatırlanır); AÇIK → hatırlanan seçimi geri açar. <b>🚀 TRENE ATLA</b> bu sayaca ve anahtara dahil değildir (yukarıdaki kendi anahtarı).</div>
      ${bk ? `<button type="button" class="btn-ghost sm" data-allrestore="1">v1.30.0 öncesi ayarları geri yükle</button>` : ""}</section>`;
  }
  function allAlPaint() {
    const c = allAlCount(); const n = $("nf-allal-n"); if (!n) return;
    n.textContent = `${fN(c.total)} açık`; const i = $("nf-allal"); if (i) i.checked = c.total > 0;
    const d = $("nf-allal-d"); if (d) d.innerHTML = `<span class="nf-mode ${c.types ? "notify" : "off"}">BİLDİRİM TÜRÜ ${fN(c.types)}/${fN(c.nTypes)}</span><span class="nf-mode ${c.price ? "notify" : "off"}">FİYAT ALARMI ${fN(c.price)}/${fN(c.nPrice)}</span><span class="nf-mode ${c.ev ? "notify" : "off"}">OLAY ALARMI ${fN(c.ev)}/${fN(c.nEv)}</span>`;
  }
  async function allAlWire() {
    const i = $("nf-allal"); if (!i) return;
    i.addEventListener("change", async () => {
      if (!i.checked) {
        const keep = { modes: Object.assign({}, NP.modes), price: st.alarms.filter((a) => !a.off).map((a) => a.id), ev: ((OL.al && OL.al.on) || []).slice() };
        LS.set("allal_last", keep);
        Object.keys(NT).forEach((k) => { if (k !== "tren_atla") NP.modes[k] = "off"; }); saveNP();   // v1.31.0 TRENE ATLA etkilenmez
        st.alarms.forEach((a) => { a.off = true; }); LS.set("alarms", st.alarms);
        await olAlPost({ all_off: true });
        toast("Tüm alarmlar kapatıldı (seçiminiz hatırlandı)");
      } else {
        const L = LS.get("allal_last", null);
        const any = L && (Object.values(L.modes || {}).some((m) => m !== "off") || (L.price || []).length || (L.ev || []).length);
        if (!any) { i.checked = false; toast("Açılacak kayıtlı seçim yok — türleri aşağıdan tek tek açın"); return; }
        const trM = NP.modes.tren_atla; NP.modes = Object.assign({}, L.modes); if (trM) NP.modes.tren_atla = trM; else delete NP.modes.tren_atla; saveNP();
        st.alarms.forEach((a) => { if ((L.price || []).includes(a.id)) a.off = false; }); LS.set("alarms", st.alarms);
        if ((L.ev || []).length) await olAlPost({ alarms: Object.fromEntries(L.ev.map((k) => [k, { on: true }])) });
        toast("Hatırlanan alarmlar yeniden açıldı");
      }
      renderNfAyar();
    });
    const rb = document.querySelector("[data-allrestore]");
    if (rb) rb.addEventListener("click", () => {
      const bk = LS.get("np_before_v1300", null); if (!bk) return;
      NP.master = bk.master !== false; NP.modes = Object.assign({}, bk.modes || {}); NP.sound = Object.assign({}, bk.sound || {});
      Object.keys(NT).forEach((k) => { if (!NP.modes[k] && k !== "tren_atla") NP.modes[k] = (NT_DEF0[k] || "view"); });
      saveNP();
      const ab = LS.get("alarms_before_v1300", []); const ids = new Set(ab.filter((a) => !a.off).map((a) => a.id));
      st.alarms.forEach((a) => { if (ids.has(a.id)) a.off = false; }); LS.set("alarms", st.alarms);
      toast("v1.30.0 öncesi bildirim ayarlarınız geri yüklendi"); renderNfAyar();
    });
    if (!OL.al) { try { OL.al = await api("/api/olay/alarms", { timeout: 15000 }); allAlPaint(); } catch (e) {} }
  }
  // ---- v1.30.0 bir kerelik: bu cihazın tüm bildirim türleri + fiyat alarmları KAPALI (önceki durum yerelde yedeklenir; sunucu ayrıca data/notif_state_before_v1300.json)
  const NT_DEF0 = { tavan_yaklasan: "notify", tavan_kitlendi: "notify", tavan_eriyen: "notify", tavan_cozuldu: "notify", taban_yaklasan: "notify", taban_kitlendi: "notify", taban_donen: "notify",
    agresif_alim: "notify", agresif_satis: "notify", kurum_alim: "notify", kurum_satis: "notify", gun_sonu: "notify", fiyat_alarmi: "notify" };
  (function olMigrate() {
    try {
      if (LS.get("v1300_off", 0)) return;
      LS.set("np_before_v1300", JSON.parse(JSON.stringify(NP)));
      LS.set("alarms_before_v1300", JSON.parse(JSON.stringify(st.alarms || [])));
      Object.keys(NT).forEach((k) => { if (k !== "tren_atla") NP.modes[k] = "off"; });   // v1.31.0 TRENE ATLA varsayılan AÇIK kalır
      (st.alarms || []).forEach((a) => { a.off = true; }); LS.set("alarms", st.alarms);
      NP.ts = Date.now(); LS.set("np", NP);
      LS.set("v1300_off", Date.now());
      setTimeout(() => { try { saveNP(); } catch (e) {} }, 1500);
    } catch (e) { console.warn("v1300 migrate", e); }
  })();

  // ================================================================ v1.31.0 🚀 TRENE ATLA (tek, net alarm)
  const TR = { d: null, pv: null, tm: null, gen: 0, err: null };
  const TR_NT = "tren_atla";
  const trOn = () => NP.master !== false && rawMode(TR_NT) === "notify";
  const trSt = { "erken": ["ERKEN", "ok"], "gönderildi": ["BİLDİRİLDİ", "ok"], "kuru": ["KURU ÇALIŞTIRMA", "dim"], "soğuma": ["SOĞUMA (30 dk)", "dim"], "oran": ["SAATLİK SINIR", "dim"], "bayat": ["GEÇ YAKALANDI · gönderilmedi", "dim"], "kaçtı": ["KAÇTI · gönderilmedi", "dim"], "döndü": ["DÖNDÜ · gönderilmedi", "dim"], "geçmiş": ["GEÇMİŞ", "dim"], "kapalı": ["MOTOR KAPALI", "dim"], "hata": ["HATA", "neg"] };
  function trSwitch(big) {
    const on = trOn();
    return `<label class="nf-sw tr-sw ${big ? "big" : ""}"><input type="checkbox" data-trsw="1" ${on ? "checked" : ""}/><span></span><b>${on ? "AÇIK" : "KAPALI"}</b></label>`;
  }
  function trSetCard() {
    const on = trOn(), mOff = NP.master === false;
    return `<section class="card tr-set ${on ? "on" : ""}" id="tr-set">
      <div class="tr-set-h"><span class="tr-rk">🚀</span><div class="tr-set-t"><b>TRENE ATLA</b><small>Tek alarm: hisse ŞİMDİ sert yükselmeye başlıyor → piyasa emriyle atla</small></div>${trSwitch(true)}</div>
      ${mOff ? `<div class="tr-warn">BİLDİRİMLER ana anahtarı KAPALI — TRENE ATLA da susuyor. <button type="button" class="btn-ghost sm" data-trmaster="1">Ana anahtarı aç</button></div>` : ""}
      <div class="src-note">Diğer 93 bildirim türünden ve <b>TÜM ALARMLAR</b> anahtarından bağımsızdır (varsayılan <b>AÇIK</b>). Yalnız hareketin İLK saniyelerinde (≥5 kademe aktif alış süpürmesi + hızlanma + hacim patlaması, <b>gün henüz ≤ +%2</b>); gün zaten yükselmiş, kaçmış ya da dönen hissede bildirim gelmez. Hisse başına 30 dk'da en çok 1, saatte en çok 6.<div class="tr-ex">Örnek bildirim: <b>🚀 TRENE ATLA · GENIL · 5,43</b></div><button type="button" class="btn-ghost sm" data-nflink="tren">Adaylar ve kurallar →</button></div>
    </section>`;
  }
  function trPaintSw() {
    document.querySelectorAll("[data-trsw]").forEach((i) => { i.checked = trOn(); const b = i.parentElement.querySelector("b"); if (b) b.textContent = trOn() ? "AÇIK" : "KAPALI"; });
    document.querySelectorAll(".tr-set, .tr-hero").forEach((c) => c.classList.toggle("on", trOn()));
    const h = $("tr-hero-st"); if (h) h.innerHTML = trHeroSt();
  }
  document.addEventListener("change", (e) => {
    const i = e.target.closest && e.target.closest("[data-trsw]"); if (!i) return;
    NP.modes[TR_NT] = i.checked ? "notify" : "off"; saveNP();
    if (i.checked) { askNotify(true); toast("🚀 TRENE ATLA bildirimi AÇIK"); } else toast("TRENE ATLA bildirimi KAPALI (liste görünmeye devam eder)");
    try { refreshNtRows(TR_NT); } catch (x) {}
    trPaintSw();
  });
  document.addEventListener("click", (e) => {
    const m = e.target.closest("[data-trmaster]"); if (m) { NP.master = true; saveNP(); if (st.view === "bildirim") renderNfAyar(); trPaintSw(); if (st.view === "tren") trRender(); return; }
    const o = e.target.closest("#tr-body [data-trsym]"); if (o) { openStock(o.dataset.trsym); return; }
  });
  function trHeroSt() {
    if (NP.master === false) return `<span class="tr-pill off">BİLDİRİMLER ANA ANAHTARI KAPALI</span>`;
    return trOn() ? `<span class="tr-pill on">● BU CİHAZA BİLDİRİM GELİR</span>` : `<span class="tr-pill off">BİLDİRİM KAPALI · yalnız liste</span>`;
  }
  function trOpen() {
    clearInterval(TR.tm);
    trLoad();
    if (!TR.pv) api("/api/tren/preview", { timeout: 10000 }).then((p) => { TR.pv = p; if (st.view === "tren") trRender(); }).catch(() => {});
    TR.tm = setInterval(() => { if (st.view !== "tren") { clearInterval(TR.tm); return; } if (!document.hidden) trLoad(true); }, 3000);
  }
  async function trLoad(quiet) {
    const g = ++TR.gen;
    try { const d = await api("/api/tren/list?limit=80", { timeout: 12000 }); if (g !== TR.gen) return; TR.d = d; TR.err = null; }
    catch (e) { if (g !== TR.gen) return; TR.err = String(e && e.message || e); }
    if (st.view === "tren") trRender();
  }
  const trAge = (s) => (s < 60 ? `${s} sn önce` : s < 3600 ? `${Math.floor(s / 60)} dk önce` : `${Math.floor(s / 3600)} sa ${Math.floor((s % 3600) / 60)} dk önce`);
  function trCard(r) {
    const hot = !!r.hot, st0 = trSt[r.st] || null, f = r.f || {};
    return `<div class="tr-sig ${hot ? "hot" : ""}" data-trsym="${esc(r.s)}">
      <div class="tr-sig-h"><span class="tr-badge ${hot ? "hot" : ""}">${hot ? "🚀 ŞİMDİ" : "🚀 TRENE ATLA"}</span><b class="tr-sym">${esc(r.s)}</b>
        <span class="tr-px">giriş <b>${fP(r.p)}</b></span><span class="tr-tm">${esc(r.time)}${isNum(r.age) ? ` · ${trAge(r.age)}` : ""}</span></div>
      <div class="tr-why">${(r.why || []).filter(Boolean).map((x) => `<div>${esc(x)}</div>`).join("")}</div>
      <div class="tr-kv"><span>şimdi <b class="${cls(r.chg)}">${fP(r.now)} (${fPct(r.chg)})</b></span><span>sonra en yüksek <b class="${cls(r.max_pc)}">${fPct(r.max_pc)}</b></span><span>en düşük <b class="${cls(r.min_pc)}">${fPct(r.min_pc)}</b></span><span>stop önerisi <b>${fP(r.stop)}</b> (−%2)</span>${st0 ? `<span class="tr-st ${st0[1]}">${st0[0]}</span>` : ""}</div>
    </div>`;
  }
  function trRender() {
    const b = $("tr-body"); if (!b) return;
    const d = TR.d;
    const hero = `<section class="card tr-hero ${trOn() ? "on" : ""}"><div class="tr-hero-h"><span class="tr-rk big">🚀</span><div class="tr-set-t"><b>TRENE ATLA ALARMI</b><small>Bildirim gelince: telefonu aç → o hisseye <b>piyasa emriyle</b> gir. Az ama güçlü sinyal.</small></div>${trSwitch(true)}</div>
      <div class="tr-hero-st" id="tr-hero-st">${trHeroSt()}</div></section>`;
    if (!d) { b.innerHTML = hero + `<div class="card"><div class="empty">${TR.err ? "Bağlantı hatası — yeniden deneniyor" : "Yükleniyor…"}</div></div>`; return; }
    const sg = d.signals || [], hot = sg.filter((x) => x.hot);
    $("tr-sub").textContent = `${d.live ? "CANLI" : "Son işlem günü"} · ${d.day_label || ""} · bugün ${fN(d.n || 0)} sinyal`;
    const list = !d.ready ? `<div class="empty">${esc(d.note || "Hesaplanıyor…")}</div>`
      : sg.length ? sg.map(trCard).join("") : `<div class="empty">${d.live ? "Henüz TRENE ATLA sinyali yok — koşulların HEPSİ birden sağlanınca burada belirir ve bildirim gelir." : "Bu gün için sinyal yok."}</div>`;
    const near = (d.near || []).length ? `<details class="tr-near"><summary>İzlemede (henüz değil) · ${fN(d.near.length)}</summary>${d.near.map((n) => `<div class="tr-nr"><b>${esc(n.s)}</b><span>${esc(n.time)}</span><span>${fP(n.p)}</span><span class="muted">eksik: ${esc(n.bad.join(", "))}</span></div>`).join("")}</details>` : "";
    const th = d.th || {}, S = d.stats || {};
    const rules = `<section class="card tr-rules"><div class="card-h"><span class="card-title">KURAL (hepsi aynı anda)</span><span class="muted">v${esc(d.version || "")}</span></div>
      <ol class="tr-ol">
        <li><b>Kademe süpürmesi ŞİMDİ:</b> aynı saniyede aktif alışla ≥${fN(th.lev)} farklı fiyat kademesi yukarı süpürüldü, ≥${fShort(th.swtl)} ₺ — tetik o saniye kapanır kapanmaz (≈1–3 sn)</li>
        <li><b>Gün henüz yükselmemiş:</b> gün değişimi ≤ +%${fN(th.gd_max, 1)} — <b>fazlası GEÇ = bildirim YOK</b> · tavana ≥ %${fN(th.tvd, 1)}</li>
        <li><b>İlk hızlanma:</b> son 1 dk ≥ +%${fN(th.m1, 1)}, 5 dk ≤ +%${fN(th.m5_hi, 1)} · son 1 dk eğimi önceki 2 dk'nın ≥${fN(th.acc, 1)} katı · son 30 sn düşmüyor</li>
        <li><b>Agresif alış dalgası:</b> son 60 sn aktif alış lotu ≥ %${fN((th.bs60 || 0) * 100)} (120 sn ≥ %${fN((th.bs || 0) * 100)})</li>
        <li><b>Hacim patlaması:</b> son 60 sn ≥ ${fShort(th.tl60)} ₺ ve önceki 3 dk ortalamasının ≥${fN(th.vacc, 1)} katı</li>
        <li><b>Gönderim anı kontrolü:</b> fiyat sinyalden +%${fN(th.run_max, 1)} fazla kaçtıysa (KAÇTI) ya da −%${fN(th.back_max, 1)} döndüyse (DÖNDÜ) bildirim <b>gönderilmez</b> · tetik ≤${fN((d.cfg || {}).fresh || 10)} sn taze olmalı</li>
        <li><b>Az ve seyrek:</b> 10:10–17:30 · hisse başına ${fN((d.cfg || {}).cd || 30)} dk'da 1 · saatte en çok ${fN((d.cfg || {}).rate || 6)}</li></ol>
      <div class="tr-stats"><div class="tr-sh">Geriye dönük test (giriş = tetikten 3 sn sonraki fiyat)</div>
        <table class="tr-tb"><tr><th>Gün</th><th>Sinyal</th><th>60 dk ≥+%3</th><th>önce −%2</th><th>zirve (med.)</th></tr>
        ${(S.rows || []).map((r) => `<tr><td>${esc(r.day)}</td><td>${fN(r.n)}</td><td class="pos">%${fN(r.hit3, 1)}</td><td class="neg">%${fN(r.loss2, 1)}</td><td>+%${fN(r.r60, 2)}</td></tr>`).join("")}</table>
        <div class="src-note">Toplam ${fN((S.pooled || {}).n)} sinyalin <b>%${fN((S.pooled || {}).hit3, 1)}</b>'i 60 dk içinde +%3 gördü; <b>%${fN((S.pooled || {}).loss2, 1)}</b>'inde fiyat önce −%2'ye indi (v1.31.1 kuralında %${fN((S.old || {}).loss2, 1)} idi). Garanti değildir — her girişte stop kullanın. ${esc(S.def || "")}${S.lat ? `<br>${esc(S.lat)}.` : ""} Yalnız 2–3 günlük kayıtla seçildi (aşırı uyum riski).</div></div></section>`;
    const pv = TR.pv ? `<section class="card tr-pv"><div class="card-h"><span class="card-title">BİLDİRİM ÖNİZLEMESİ</span><span class="muted">${TR.pv.example ? "örnek" : "son sinyal"} · gönderilmedi</span></div>
      <div class="tr-phone"><div class="tr-ph-app">BIST Canlı · şimdi</div><div class="tr-ph-t">${esc(TR.pv.title)}</div><div class="tr-ph-b">${esc(TR.pv.body)}</div></div>
      <div class="src-note">Dokununca doğrudan hisse açılır. Push yolu: mevcut bildirim altyapısı (Telegram kanalı + Web Push).</div></section>` : "";
    b.innerHTML = hero + `<section class="card tr-list"><div class="card-h"><span class="card-title">${hot.length ? `<span class="tr-live">● ${fN(hot.length)} AKTİF</span>` : ""} SİNYALLER</span><span class="muted">${d.live ? "canlı · 3 sn" : esc(d.day_label || "")}</span></div>${list}${near}</section>` + pv + rules;
  }


  // ================================================================ v1.32.0 D-A-K SKORLARI (Derinlik · AKD · Kademe Analizi · D-A-K)
  const SK = { d: null, tm: null, gen: 0, err: null, sort: "dak", dir: -1, f: "all", q: "", vol: false, n: 150, sel: null };
  const skC = (v) => (!isNum(v) ? "na" : v >= 70 ? "g2" : v >= 57 ? "g1" : v <= 30 ? "r2" : v <= 43 ? "r1" : "n");
  const skLab = (v) => (!isNum(v) ? "—" : v >= 70 ? "GÜÇLÜ ALIŞ" : v >= 57 ? "ALIŞ AĞIRLIKLI" : v <= 30 ? "GÜÇLÜ SATIŞ" : v <= 43 ? "SATIŞ AĞIRLIKLI" : "DENGELİ");
  const skPill = (v, big) => `<span class="sk-p ${skC(v)}${big ? " big" : ""}">${isNum(v) ? fN(v) : "—"}</span>`;
  // v1.32.1 Derinlik: liste skoru (anlık defter) + parantezde hisse sayfasındaki Derinlik Skoru — farklıysa 99(74), aynıysa tek sayı
  // v1.33.1: parantez HER satırda — eşitse 92(92), sayfa skoru henüz yoksa 92(—)
  const skDual = (a, b) => `<span class="sk-dual" title="Liste skoru ${isNum(a) ? a : "—"} · hisse sayfası Derinlik Skoru ${isNum(b) ? b : "hesaplanıyor"}">${skPill(a)}<span class="sk-pg ${skC(b)}">(${isNum(b) ? fN(b) : "—"})</span></span>`;
  const SK_F = [["all", "TÜMÜ"], ["g2", "D-A-K ≥70"], ["g1", "57–69"], ["n", "DENGELİ"], ["r1", "31–43"], ["r2", "≤30"]];
  const SK_COLS = [["s", "Hisse"], ["d", "Derinlik"], ["a", "AKD"], ["k", "Kademe"], ["dak", "D-A-K"]];
  function skOpen() {
    clearInterval(SK.tm);
    skLoad();
    SK.tm = setInterval(() => { if (st.view !== "skor") { clearInterval(SK.tm); return; } if (!document.hidden) skLoad(true); }, 5000);
  }
  async function skLoad() {
    const g = ++SK.gen;
    try { const d = await api("/api/skor/list", { timeout: 15000 }); if (g !== SK.gen) return; SK.d = d; SK.err = null; }
    catch (e) { if (g !== SK.gen) return; SK.err = String(e && e.message || e); }
    if (st.view === "skor") skRender();
  }
  function skRows() {
    const d = SK.d; if (!d || !d.rows) return [];
    const C = d.cols, ix = Object.fromEntries(C.map((c, i) => [c, i]));
    let R = d.rows.map((r) => ({ s: r[ix.s], p: r[ix.p], c: r[ix.c], t: r[ix.t], d: r[ix.d], a: r[ix.a], k: r[ix.k], dak: r[ix.dak], n: r[ix.n], dp: ix.dp != null ? r[ix.dp] : null }));
    const q = (SK.q || "").trim().toLocaleUpperCase("tr");
    if (q) R = R.filter((r) => r.s.includes(q));
    if (SK.vol) R = R.filter((r) => (r.t || 0) >= 10e6);
    if (SK.f !== "all") R = R.filter((r) => skC(r.dak) === SK.f);
    const k = SK.sort, dir = SK.dir;
    R.sort((x, y) => {
      if (k === "s") return dir * x.s.localeCompare(y.s, "tr");
      const a = x[k], b = y[k];
      if (!isNum(a) && !isNum(b)) return x.s.localeCompare(y.s, "tr");
      if (!isNum(a)) return 1; if (!isNum(b)) return -1;
      return dir * (a - b) || (y.t || 0) - (x.t || 0);
    });
    return R;
  }
  function skRender() {
    const b = $("sk-body"); if (!b) return;
    const d = SK.d;
    if (!d) { b.innerHTML = `<div class="card"><div class="empty">${SK.err ? "Bağlantı hatası — yeniden deneniyor" : "Yükleniyor…"}</div></div>`; return; }
    const cov = d.cov || {};
    $("sk-sub").textContent = `${d.live ? "CANLI" : "Seans dışı (son veriler)"} · ${fN(cov.rows || 0)} hisse · ${d.ts || "—"}`;
    if (!d.ready) { b.innerHTML = `<div class="card"><div class="empty">Skorlar hesaplanıyor… (açılıştan ~30 sn sonra hazır)</div></div>`; return; }
    const R = skRows(), shown = R.slice(0, SK.n);
    const ae = document.activeElement, hadQ = ae && ae.id === "sk-q", cp = hadQ ? ae.selectionStart : 0;
    const head = SK_COLS.map(([k, l]) => `<th data-sksort="${k}" class="${SK.sort === k ? "on" : ""}${k === "s" ? " l" : ""}">${l}${SK.sort === k ? (SK.dir < 0 ? " ▼" : " ▲") : ""}</th>`).join("");
    const rows = shown.map((r) => `<tr data-sksym="${esc(r.s)}"><td class="l"><b>${esc(r.s)}</b><small>${fP(r.p)} <span class="${cls(r.c)}">${fPct(r.c)}</span></small></td><td>${skDual(r.d, r.dp)}</td><td>${skPill(r.a)}</td><td>${skPill(r.k)}</td><td>${skPill(r.dak, 1)}</td></tr>`).join("");
    b.innerHTML = `<section class="card sk-top">
        <div class="sk-ctl"><input type="search" id="sk-q" class="sk-q" placeholder="Hisse ara (örn. THYAO)" value="${esc(SK.q)}" autocomplete="off"/>
          <label class="sk-vol"><input type="checkbox" id="sk-vol" ${SK.vol ? "checked" : ""}/> Hacim ≥10 Mn ₺</label></div>
        <div class="sk-chips">${SK_F.map(([k, l]) => `<button type="button" class="sk-chip ${k} ${SK.f === k ? "on" : ""}" data-skf="${k}">${l}</button>`).join("")}</div>
        <div class="sk-legend"><span class="sk-p r2">0–30</span><span class="sk-p r1">31–43</span><span class="sk-p n">44–56</span><span class="sk-p g1">57–69</span><span class="sk-p g2">70–100</span><span class="muted">satış ← → alış</span></div>
        <div class="sk-dleg"><b>Derinlik 99(74)</b> = <b>99</b> liste skoru (anlık defter: 25 kademe + tüm defter + süpürmeler, tüm hisseler) · <b>(74)</b> hisse sayfasındaki <b>Derinlik Skoru</b> (DERİNLİK sekmesi göstergesi: sahte/gizli emir, duvar geçmişi dahil). Her satırda ikisi birden yazılır: eşitse 92(92); sayfa skoru henüz hesaplanmadıysa 92(—). D-A-K ortalamasında sayfa skoru kullanılır.</div>
        <div class="src-note">${fN(R.length)} hisse${R.length > shown.length ? ` · ilk ${fN(shown.length)} gösteriliyor` : ""} · Derinlik ${fN(cov.d || 0)} · AKD ${fN(cov.a || 0)} · Kademe ${fN(cov.k || 0)} / ${fN(cov.uni || 0)} pay · ${d.live ? `her ${fN(d.loop || 15)} sn yenilenir` : "seans dışı"} · başlığa dokun = sırala, satıra dokun = neden?</div></section>
      <section class="card sk-list"><div class="sk-tw"><table class="sk-tb"><thead><tr>${head}</tr></thead><tbody>${rows || `<tr><td colspan="5" class="empty">Eşleşen hisse yok</td></tr>`}</tbody></table></div>
        ${R.length > shown.length ? `<button type="button" class="btn-ghost sk-more" data-skmore="1">+${fN(Math.min(200, R.length - shown.length))} hisse daha göster</button>` : ""}</section>
      <section class="card sk-how"><div class="card-h"><span class="card-title">SKORLAR NASIL HESAPLANIR?</span><span class="muted">v${esc(d.version || "")}</span></div>
        <div class="src-note">Her skor 0–100 · <b>50 = dengeli</b> · 50 + bileşen puanları (v1.25.0 Derinlik skoru ile aynı ölçek ve etiketler: ≥70 GÜÇLÜ ALIŞ · ≥57 ALIŞ AĞIRLIKLI · ≤43 SATIŞ AĞIRLIKLI · ≤30 GÜÇLÜ SATIŞ).</div>
        <ul class="sk-ul"><li><b>Derinlik Skoru</b> — İdealData canlı derinlik (25 kademe + tüm defter): 10 kademe alış/satış lot oranı (±15), 25 kademe ₺ dengesi (±8), tüm defter alış payı (±6), son 1–4 dk denge değişimi (±6), ilk 5 kademedeki alış/satış duvarları (±3), tavan/taban kuyruğu (±10), son 15 dk yukarı − aşağı süpürme (±8).</li>
          <li><b>AKD Skoru</b> — Günlük AKD (AKD Taraması ile aynı kayıt): ilk 3 alıcı − ilk 3 satıcı yoğunlaşması (±15), net alıcı/satıcı sayısı (±6), TOPLAMA / DAĞITIM (±8), ilk 3 alıcının aktif alışı ve ilk 3 satıcının aktif satışı (±6 / ±6), hissede aktif alış (±6), fiyatın ilk 5 alıcının maliyetine göre konumu (±6).</li>
          <li><b>Kademe Analizi Skoru</b> — İdealData fiyat kademe analizi (Y38, Kademe Analizi ile aynı kayıt): alış/satış lot dengesi (±20), fiyat − AORT (±8), fiyat − POC (±6), alış ort. − satış ort. (±6), gün aralığının üst üçte birinde alış payı (±6).</li>
          <li><b>Parantez (Derinlik)</b> — hisse sayfasındaki DERİNLİK SKORU ile birebir aynı hesap (v1.25.0: 10 kademe oranı, son 1 dk denge, duvarlar büyüyor/eriyor, sahte duvar, gizli emir, kademe çizme, süpürme, tavan/taban kuyruğu, kademe yenileme) — tüm hisseler için ~15 sn'de bir yeniden hesaplanır. AKD ve Kademe skorlarının sayfada ayrı bir karşılığı yok (tek sayı).</li>
          <li><b>D-A-K Skoru</b> — Derinlik (sayfa skoru; yoksa liste skoru) + AKD + Kademe ortalaması (en az ikisi varsa).</li></ul>
        <div class="src-note">Kademe kaydı tarayıcıyla sırayla güncellenir (~1–3 dk), AKD ~20 sn, derinlik saniyeler. Al/sat önerisi değildir.</div></section>`;
    if (hadQ) { const i = $("sk-q"); if (i) { i.focus(); try { i.setSelectionRange(cp, cp); } catch (e) {} } }
  }
  function skCompRows(x) {
    return (x.comps || []).map(([l, v]) => `<div class="sk-cr"><span>${esc(l)}</span><b class="${v > 0 ? "pos" : v < 0 ? "neg" : ""}">${v > 0 ? "+" : ""}${fN(v, 1)}</b></div>`).join("");
  }
  async function skDetail(sym) {
    SK.sel = sym;
    const sh = $("sk-sheet"), body = $("sk-sbody"); if (!sh || !body) return;
    sh.hidden = false; document.body.classList.add("sk-lock");
    body.innerHTML = `<div class="sk-sh"><b>${esc(sym)}</b><button type="button" class="sheet-x" data-skclose="1" aria-label="Kapat">✕</button></div><div class="empty">Yükleniyor…</div>`;
    let d = null;
    try { d = await api("/api/skor/detail?s=" + encodeURIComponent(sym), { timeout: 12000 }); } catch (e) {}
    if (SK.sel !== sym || sh.hidden) return;
    if (!d || !d.found) { body.innerHTML = `<div class="sk-sh"><b>${esc(sym)}</b><button type="button" class="sheet-x" data-skclose="1">✕</button></div><div class="empty">Bu hisse için skor verisi yok</div><button type="button" class="btn-primary sk-open" data-skopen="${esc(sym)}">Hisseyi aç →</button>`; return; }
    const part = (k, t, src, age) => { const x = d[k]; return `<div class="sk-part sk-p-${k}"><div class="sk-ph">${skPill(x ? x.sc : null, 1)}<div><b>${t}</b><small>${x ? esc(x.lab) : "veri yok"}${age != null ? ` · ${esc(age)}` : ""}</small></div></div>
      ${x ? `<div class="sk-yr">${esc(x.yorum)}</div><div class="sk-comps">${skCompRows(x)}</div>` : `<div class="muted sk-yr">${esc(src)}</div>`}</div>`; };
    const ageS = (s) => (s == null ? null : s < 90 ? `${s} sn önce` : `${Math.round(s / 60)} dk önce`);
    const ak = d.a || {};
    const tops = (ak.top_b || []).length ? `<div class="sk-tops"><span>İlk alıcılar: ${(ak.top_b || []).map((r) => esc(r.br)).join(", ")}</span><span>İlk satıcılar: ${(ak.top_s || []).map((r) => esc(r.br)).join(", ")}</span></div>` : "";
    body.innerHTML = `<div class="sk-sh"><div><b>${esc(d.s)}</b> <span class="muted">${esc(d.n || "")}</span><div class="sk-shp">${fP(d.p)} <span class="${cls(d.c)}">${fPct(d.c)}</span> · ${esc(d.ts || "")}</div></div><button type="button" class="sheet-x" data-skclose="1" aria-label="Kapat">✕</button></div>
      <div class="sk-dak">${skPill(d.dak, 1)}<div><b>D-A-K Skoru</b><small>${isNum(d.dak) ? esc(skLab(d.dak)) + " · Derinlik (sayfa) + AKD + Kademe ortalaması" : "en az 2 skor gerekli"}</small></div></div>
      ${part("d", "Derinlik Skoru — liste (anlık defter)", "Canlı derinlik verisi yok", ageS(d.dage))}
      ${d.dp ? `<div class="sk-part sk-pgp"><div class="sk-ph">${skPill(d.dp.sc, 1)}<div><b>Derinlik Skoru — hisse sayfası</b><small>${esc(d.dp.lab || "")} · DERİNLİK sekmesindeki göstergeyle aynı hesap · ${ageS(d.dp.age) || ""}</small></div></div>
        <div class="sk-yr">${esc(d.dp.yorum || "")}</div><div class="sk-comps">${skCompRows(d.dp)}</div>${d.d && d.d.sc !== d.dp.sc ? `<div class="src-note">Listede <b>${fN(d.d.sc)}(${fN(d.dp.sc)})</b> görünür: liste skoru yalnız anlık defteri tartar; sayfa skoru gün içi derinlik geçmişini (sahte duvar, gizli emir, çekilen duvarlar) de katar.</div>` : ""}</div>` : ""}
      ${part("a", "AKD Skoru", "Günlük AKD kaydı yok", null)}${tops}
      ${part("k", "Kademe Analizi Skoru", "Bugün için kademe analizi (Y38) yok", ageS(d.kage))}
      <button type="button" class="btn-primary sk-open" data-skopen="${esc(d.s)}">Hisseyi aç → (Özet · Derinlik · AKD · Kademe)</button>`;
  }
  function skClose() { const sh = $("sk-sheet"); if (sh) sh.hidden = true; document.body.classList.remove("sk-lock"); SK.sel = null; }
  document.addEventListener("click", (e) => {
    if (!e.target.closest) return;
    if (e.target.closest("[data-skclose]")) { skClose(); return; }
    const o = e.target.closest("[data-skopen]"); if (o) { const s = o.dataset.skopen; skClose(); openStock(s); return; }
    if (st.view !== "skor") return;
    const h = e.target.closest("[data-sksort]"); if (h) { const k = h.dataset.sksort; if (SK.sort === k) SK.dir = -SK.dir; else { SK.sort = k; SK.dir = k === "s" ? 1 : -1; } skRender(); return; }
    const f = e.target.closest("[data-skf]"); if (f) { SK.f = f.dataset.skf; SK.n = 150; skRender(); return; }
    if (e.target.closest("[data-skmore]")) { SK.n += 200; skRender(); return; }
    const r = e.target.closest("#sk-body [data-sksym]"); if (r) { skDetail(r.dataset.sksym); return; }
  });
  document.addEventListener("input", (e) => { if (e.target && e.target.id === "sk-q") { SK.q = e.target.value; SK.n = 150; skRender(); } });
  document.addEventListener("change", (e) => { if (e.target && e.target.id === "sk-vol") { SK.vol = e.target.checked; skRender(); } });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && SK.sel) skClose(); });


  // ================================================================ v1.33.0 ALGO DESTEK / ALGO DİRENÇ
  const AGW = { d: null, tm: null, gen: 0, err: null, side: "b", sort: "n", q: "", sel: null };
  const alLot = (v) => (isNum(v) ? nf(0).format(v) : "—");
  const alDur = (s) => (!isNum(s) ? "—" : s < 60 ? `${s} sn` : s < 3600 ? `${Math.floor(s / 60)} dk` : `${Math.floor(s / 3600)} sa ${Math.floor((s % 3600) / 60)} dk`);
  function alOpen() {
    clearInterval(AGW.tm);
    alTabs(); alLoad();
    AGW.tm = setInterval(() => { if (st.view !== "algo") { clearInterval(AGW.tm); return; } if (!document.hidden) alLoad(true); }, 5000);
  }
  function alTabs() { document.querySelectorAll("#al-tab [data-alt]").forEach((b) => b.classList.toggle("active", b.dataset.alt === AGW.side)); }
  async function alLoad() {
    const g = ++AGW.gen;
    try { const d = await api("/api/algo/list", { timeout: 15000 }); if (g !== AGW.gen) return; AGW.d = d; AGW.err = null; }
    catch (e) { if (g !== AGW.gen) return; AGW.err = String(e && e.message || e); }
    if (st.view === "algo") alRender();
  }
  function alCard(r, side) {
    const dCls = side === "b" ? "pos" : "neg";
    return `<div class="al-c ${side}" data-alsym="${esc(r.s)}">
      <div class="al-h"><b class="al-sym">${esc(r.s)}</b><span>${fP(r.p)} <span class="${cls(r.c)}">${fPct(r.c)}</span></span><span class="al-badge ${side}">${side === "b" ? "ALGO DESTEK" : "ALGO DİRENÇ"}</span></div>
      <div class="al-pat"><b>${esc(r.pat)}</b> · ${fP(r.p0)} → ${fP(r.p1)} · <b>${fShort(r.tl)} ₺</b></div>
      <div class="al-kv"><span>uzaklık <b class="${dCls}">${fPct(r.dist)}</b> … ${fPct(r.far)}</span><span>tam ${alLot(r.B)} lot: <b>${fN(r.ex)}</b> kademe</span><span>karşı tarafın <b>${isNum(r.ratio) ? nf(1).format(r.ratio) + "×" : "—"}</b></span><span>${esc(r.first)}'den beri (${alDur(r.dur)})</span></div>
      <div class="al-eff">${esc(r.eff)}</div></div>`;
  }
  function alRender() {
    const b = $("al-body"); if (!b) return;
    const d = AGW.d;
    if (!d) { b.innerHTML = `<div class="card"><div class="empty">${AGW.err ? "Bağlantı hatası — yeniden deneniyor" : "Yükleniyor…"}</div></div>`; return; }
    $("al-sub").textContent = `${fN((d.b || []).length)} algo destek · ${fN((d.a || []).length)} algo direnç · ${fN(d.n_books || 0)} defter · ${d.ts || "—"}`;
    if (!d.ready) { b.innerHTML = `<div class="card"><div class="empty">Defterler taranıyor… (açılıştan ~30 sn sonra hazır)</div></div>`; return; }
    let R = (d[AGW.side] || []).slice();
    const q = (AGW.q || "").trim().toLocaleUpperCase("tr");
    if (q) R = R.filter((r) => r.s.includes(q));
    const K = { n: (x, y) => y.n - x.n || y.tl - x.tl, tl: (x, y) => y.tl - x.tl, dist: (x, y) => Math.abs(x.dist ?? 99) - Math.abs(y.dist ?? 99), dur: (x, y) => y.dur - x.dur };
    R.sort(K[AGW.sort] || K.n);
    const ae = document.activeElement, hadQ = ae && ae.id === "al-q", cp = hadQ ? ae.selectionStart : 0;
    const th = d.th || {};
    b.innerHTML = `<section class="card al-top"><div class="sk-ctl"><input type="search" id="al-q" class="sk-q" placeholder="Hisse ara" value="${esc(AGW.q)}" autocomplete="off"/>
        <select id="al-sort" class="al-sel">${[["n", "En çok kademe"], ["tl", "En büyük ₺"], ["dist", "Fiyata en yakın"], ["dur", "En uzun süredir"]].map(([k, l]) => `<option value="${k}" ${AGW.sort === k ? "selected" : ""}>${l}</option>`).join("")}</select></div>
        <div class="src-note">${AGW.side === "b" ? "<b>ALGO DESTEK</b>: alış tarafında ardışık kademelere aynı büyüklükte (±%30) dizilmiş emirler — algoritma fiyat indikçe alıyor." : "<b>ALGO DİRENÇ</b>: satış tarafında ardışık kademelere aynı büyüklükte (±%30) dizilmiş emirler — algoritma fiyat yükseldikçe satıyor."} Kural: ≥${fN(th.min_lv)} kademe · taban lot B ≤ lot ≤ B×${nf(2).format(1 + (th.tol || 0))} · toplam ≥ ${fShort(th.min_tl)} ₺ · kademe başına ort. emir ≤ ${fN(th.max_ord)} (çok emirli likit defter algo sayılmaz) · kademelerin ≥%${fN((th.exact || 0) * 100)}'i ve en az ${fN(th.ex_n)} kademe tam B (±%1) ya da lot değişkenliği ≤%${fN((th.cv || 0) * 100)}. Her ${fN(d.loop || 10)} sn yenilenir · karta dokun = kademeler.</div></section>
      <section class="card al-list">${R.length ? R.map((r) => alCard(r, AGW.side)).join("") : `<div class="empty">${q ? "Eşleşen hisse yok" : AGW.side === "b" ? "Şu an algo destek tespit edilmedi" : "Şu an algo direnç tespit edilmedi"}</div>`}</section>
      <section class="card"><div class="src-note">İdealData derinliği en fazla 25 kademe verir; duvar daha derine uzanıyor olabilir. Algo duvarları anında çekilebilir — beklenen etki yorumdur, al/sat önerisi değildir.</div></section>`;
    if (hadQ) { const i = $("al-q"); if (i) { i.focus(); try { i.setSelectionRange(cp, cp); } catch (e) {} } }
  }
  async function alDetail(sym) {
    AGW.sel = sym;
    const sh = $("al-sheet"), body = $("al-sbody"); if (!sh || !body) return;
    sh.hidden = false; document.body.classList.add("sk-lock");
    body.innerHTML = `<div class="sk-sh"><b>${esc(sym)}</b><button type="button" class="sheet-x" data-alclose="1" aria-label="Kapat">✕</button></div><div class="empty">Yükleniyor…</div>`;
    let d = null;
    try { d = await api("/api/algo/detail?s=" + encodeURIComponent(sym), { timeout: 12000 }); } catch (e) {}
    if (AGW.sel !== sym || sh.hidden) return;
    if (!d || !d.found) { body.innerHTML = `<div class="sk-sh"><b>${esc(sym)}</b><button type="button" class="sheet-x" data-alclose="1">✕</button></div><div class="empty">Defter verisi yok</div>`; return; }
    const hb = new Set((d.b && d.b.idx) || []), ha = new Set((d.a && d.a.idx) || []);
    const n = Math.max(d.bids.length, d.asks.length);
    let rows = "";
    for (let i = 0; i < n; i++) {
      const x = d.bids[i], y = d.asks[i];
      rows += `<tr><td class="${hb.has(i) ? "al-hb" : ""}">${x ? fN(x[2]) : ""}</td><td class="${hb.has(i) ? "al-hb" : ""}">${x ? alLot(x[1]) : ""}</td><td class="pos ${hb.has(i) ? "al-hb" : ""}">${x ? fP(x[0]) : ""}</td><td class="neg ${ha.has(i) ? "al-ha" : ""}">${y ? fP(y[0]) : ""}</td><td class="${ha.has(i) ? "al-ha" : ""}">${y ? alLot(y[1]) : ""}</td><td class="${ha.has(i) ? "al-ha" : ""}">${y ? fN(y[2]) : ""}</td></tr>`;
    }
    const sec = (r, side) => r ? `<div class="al-dsec ${side}"><span class="al-badge ${side}">${side === "b" ? "ALGO DESTEK" : "ALGO DİRENÇ"}</span> <b>${esc(r.pat)}</b> · ${fP(r.p0)} → ${fP(r.p1)} · ${fShort(r.tl)} ₺ · uzaklık ${fPct(r.dist)}<div class="al-eff">${esc(r.eff)}</div></div>` : "";
    body.innerHTML = `<div class="sk-sh"><div><b>${esc(d.s)}</b> <span class="muted">${esc(d.name || "")}</span><div class="sk-shp">${fP(d.p)} <span class="${cls(d.c)}">${fPct(d.c)}</span> · defter ${fN(d.age)} sn önce</div></div><button type="button" class="sheet-x" data-alclose="1" aria-label="Kapat">✕</button></div>
      ${sec(d.b, "b")}${sec(d.a, "a")}${!d.b && !d.a ? `<div class="muted">Bu hissede şu an algo duvarı yok.</div>` : ""}
      <table class="al-lad"><thead><tr><th>EMİR</th><th>LOT</th><th>ALIŞ</th><th>SATIŞ</th><th>LOT</th><th>EMİR</th></tr></thead><tbody>${rows}</tbody></table>
      <div class="src-note">Vurgulu kademeler = algo duvarı (yeşil: destek, kırmızı: direnç).</div>
      <button type="button" class="btn-primary sk-open" data-alopen="${esc(d.s)}">Hisseyi aç → DERİNLİK</button>`;
  }
  function alClose() { const sh = $("al-sheet"); if (sh) sh.hidden = true; document.body.classList.remove("sk-lock"); AGW.sel = null; }
  document.addEventListener("click", (e) => {
    if (!e.target.closest) return;
    if (e.target.closest("[data-alclose]")) { alClose(); return; }
    const o = e.target.closest("[data-alopen]"); if (o) { const s = o.dataset.alopen; alClose(); selectSymbol(s); go("stock"); st.fromScreen = true; setTimeout(() => { try { openTab("derinlik", true); } catch (x) {} }, 50); return; }
    if (st.view !== "algo") return;
    const t = e.target.closest("#al-tab [data-alt]"); if (t) { AGW.side = t.dataset.alt; alTabs(); alRender(); return; }
    const c = e.target.closest("#al-body [data-alsym]"); if (c) { alDetail(c.dataset.alsym); return; }
  });
  document.addEventListener("input", (e) => { if (e.target && e.target.id === "al-q") { AGW.q = e.target.value; alRender(); } });
  document.addEventListener("change", (e) => { if (e.target && e.target.id === "al-sort") { AGW.sort = e.target.value; alRender(); } });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && AGW.sel) alClose(); });


  // ================================================================ v1.34.0 ✅ AL BUNU · TAVAN ADAYI
  const AB = { d: null, tm: null, gen: 0, err: null, sel: null, peek: null };
  const AB_NT = "al_bunu";
  const abOn = () => NP.master !== false && rawMode(AB_NT) === "notify";
  function abHeroN() {
    try {
      const d = AB.peek || AB.d;
      if (!d || !d.ready) return `<i>…</i>`;
      const n = (d.rows || []).length;
      return n ? `<b>${fN(n)}</b><i>hisse şimdi</i>` : `<b>0</b><i>şimdi yok</i>`;
    } catch (e) { return `<i>…</i>`; }
  }
  async function abPeek() {
    try { const d = await api("/api/albunu/list", { timeout: 8000 }); AB.peek = d; const n = $("kf-ab-n"); if (n) n.innerHTML = abHeroN(); } catch (e) {}
  }
  function abOpen() {
    clearInterval(AB.tm);
    abLoad();
    AB.tm = setInterval(() => { if (st.view !== "albunu") { clearInterval(AB.tm); return; } if (!document.hidden) abLoad(); }, 5000);
  }
  async function abLoad() {
    const g = ++AB.gen;
    try { const d = await api("/api/albunu/list", { timeout: 15000 }); if (g !== AB.gen) return; AB.d = d; AB.peek = d; AB.err = null; }
    catch (e) { if (g !== AB.gen) return; AB.err = String(e && e.message || e); }
    if (st.view === "albunu") abRender();
  }
  const abBr = (r) => esc(brName ? brName(r.br) : r.brn);
  function abSw() {
    const on = abOn();
    return `<label class="nf-sw ab-sw"><input type="checkbox" data-absw="1" ${on ? "checked" : ""}/><span></span><b>${on ? "BİLDİRİM AÇIK" : "BİLDİRİM KAPALI"}</b></label>`;
  }
  function abCard(r, i) {
    const tv = r.exp === "TAVAN";
    const inTxt = r.in_t ? `listede <b>${esc(r.in_t.slice(0, 5))}</b>'ten beri · giriş ${fP(r.in_p)}${isNum(r.in_chg) ? ` → <b class="${cls(r.in_chg)}">${fPct(r.in_chg)}</b>` : ""}` : "";
    const stop = r.at_t ? `<b>${esc(r.stop_w)}</b>` : `stop <b>${fP(r.stop)}</b> <span class="muted">(${esc(r.stop_w)})</span>`;
    return `<div class="ab-c ${tv ? "tv" : ""}" data-absym="${esc(r.s)}">
      <div class="ab-h"><span class="ab-rk">${i + 1}</span><b class="ab-sym">${esc(r.s)}</b><span class="ab-px">${fP(r.p)}</span><span class="ab-gd ${cls(r.gd)}">${fPct(r.gd)}</span>
        <span class="ab-rt"><span class="ab-exp ${tv ? "tv" : ""}">${tv ? "TAVAN" : "DEVAM"}</span><span class="ab-sc" title="Güven (0–100)">${fN(r.sc)}</span></span></div>
      <div class="ab-why"><b>${abBr(r)}</b> net %${fN(r.np, 0)} · aktif %${fN(r.akt ?? 0, 0)} · ${fShort(r.btl)} ₺ aldı · son 15 dk ${fShort(r.l15)} ₺ (%${fN(r.l15a, 0)} aktif) — <b>hâlâ itiyor</b></div>
      <div class="ab-tags">${(r.tags || []).map((t) => `<span>${esc(t)}</span>`).join("")}${r.at_t ? "" : isNum(r.room) ? `<span class="dim">tavana %${nf(1).format(r.room)}</span>` : ""}</div>
      <div class="ab-ft"><span>${stop}</span>${inTxt ? `<span>${inTxt}</span>` : ""}</div></div>`;
  }
  function abRender() {
    const b = $("ab-body"); if (!b) return;
    const d = AB.d;
    if (!d) { b.innerHTML = `<div class="card"><div class="empty">${AB.err ? "Bağlantı hatası — yeniden deneniyor" : "Yükleniyor…"}</div></div>`; return; }
    const R = d.rows || [];
    $("ab-sub").textContent = `${d.ready ? fN(R.length) + " hisse" : "hazırlanıyor"} · ${d.live ? "CANLI" : "son seans"} · ${d.ts || "—"} · her 10 sn`;
    const head = `<section class="card ab-top ${abOn() ? "on" : ""}"><div class="ab-top-h"><div class="ab-top-t"><b>Ne alsam? → bu liste.</b><small>Yalnız tüm koşullar birlikte tuttuğunda listelenir: kurum fiyatı ısrarla yukarı itiyor <b>ve son 15 dk'da hâlâ itiyor</b>, AKD ve derinlik destekliyor, geç kalınmamış.</small></div>${abSw()}</div></section>`;
    if (!d.ready) { b.innerHTML = head + `<section class="card"><div class="empty">Hesaplanıyor… (açılıştan ~1 dk sonra hazır)</div></section>`; return; }
    const near = d.near || [], gone = d.gone || [];
    const list = R.length ? R.map(abCard).join("") : `<div class="ab-empty"><b>Şu an tüm koşulları sağlayan hisse yok.</b><span>Beklemek de pozisyondur — koşullar oluşunca burada belirir${abOn() ? " ve bildirim gelir" : ""}.</span></div>`;
    const nearH = near.length ? `<details class="card ab-det"><summary>Eşiğe yakın — ALMA, izle (${fN(near.length)})</summary>${near.map((x) => `<div class="ab-nr" data-absym2="${esc(x.s)}"><b>${esc(x.s)}</b> <span class="${cls(x.gd)}">${fPct(x.gd)}</span> <span class="muted">· ${esc(x.brn)}</span><div class="ab-nw">✗ ${(x.why || []).map(esc).join(" · ✗ ")}</div></div>`).join("")}</details>` : "";
    const goneH = gone.length ? `<details class="card ab-det"><summary>Bugün listeden çıkanlar (${fN(gone.length)})</summary>${gone.map((x) => `<div class="ab-nr" data-absym2="${esc(x.s)}"><b>${esc(x.s)}</b> <span class="muted">${esc(x.in_t ? x.in_t.slice(0, 5) : "—")} girdi ${fP(x.in_p)} → ${esc(x.t.slice(0, 5))} çıktı ${fP(x.p)}</span> ${isNum(x.res) ? `<b class="${cls(x.res)}">${fPct(x.res)}</b>` : ""}<div class="ab-nw">${(x.why || []).map(esc).join(" · ")}</div></div>`).join("")}</details>` : "";
    const th = d.th || {};
    const rules = `<details class="card ab-det"><summary>Koşullar (hepsi birlikte şart)</summary><ol class="ab-rules">
      <li><b>Lider kurum</b> (Maliyet Yükselten): ciddiyet ≥${th.sc} · aktif alış ≥%${th.akt} · alış ≥${fShort(th.btl)} ₺ · hacim payı ≥%${th.pay} · maliyetini yükseltiyor (≥${th.ys} kez)</li>
      <li><b>Hâlâ itiyor</b> (işlem kaydı, son 15 dk): lider kurum ≥${fShort(th.l15_tl)} ₺ aldı, net alıcı, alışlarının ≥%${th.l15_akt}'i aktif, son alışı ≤5 dk önce</li>
      <li><b>AKD</b>: lider kurum net alıcılarda ilk ${th.rb}'te, net payı ≥%${th.np} · DAĞITIM yok · tahtacı satış (Satış #1 aktif satış ≥%${th.tht_as}) baskın değil</li>
      <li><b>Fiyat</b>: gün ≥ +%${th.gd_min} · zirveden ≤%${th.fade} geride · son 15 dk ≥ 0 · tavana ≥%${th.room} yer var <i>ya da</i> tavanda ve alış kuyruğu ≥${fShort(th.q_tl)} ₺ (erimiyor)</li>
      <li><b>Derinlik</b>: D-A-K ≥${th.dak} · sayfa Derinlik ≥${th.dp} · üstte (%${th.alg_dist} içinde) güçlü Algo Direnç yok</li>
      <li><b>Momentum kanıtı</b> (en az biri): TAVAN TRENİ · CİDDİ YÜKSELİŞ / TAVAN ADAYI senaryosu · bugün TRENE ATLA (fiyat sinyalin altına inmemiş)</li></ol>
      <div class="src-note">Güven 0–100 = kurum 30 + hâlâ itiyor 15 + AKD 20 + momentum 15 + derinlik 20; liste güvene göre sıralı, en çok ${fN(th.cap)} hisse, güven ≥${th.min_score}. <b>TAVAN</b> = tavan senaryosu / tavanda kuyruklu / güçlü tren + tavana ≤%5; diğerleri <b>DEVAM</b>. Stop: lider kurumun ortalama maliyeti (fiyatın %1–5 altındaysa) yoksa −%3. Bildirim varsayılan KAPALI; açarsanız yalnız listeye yeni giren güven ≥70 hisse, hisse başına günde 1, saatte en çok 3. Kaynaklar: İdealData canlı işlem + AKD + derinlik. Yatırım tavsiyesi değildir.</div></details>`;
    b.innerHTML = head + `<section class="card ab-list">${list}</section>` + nearH + goneH + rules;
  }
  function abDetail(sym) {
    const d = AB.d; if (!d) return;
    const r = (d.rows || []).find((x) => x.s === sym); if (!r) { openStock(sym); return; }
    AB.sel = sym;
    const sh = $("ab-sheet"), body = $("ab-sbody"); if (!sh || !body) return;
    sh.hidden = false; document.body.classList.add("sk-lock");
    const P = r.parts || {};
    const bar = (l, v, mx) => `<div class="ab-pt"><span>${l}</span><i><em style="width:${Math.max(0, Math.min(100, (v / mx) * 100)).toFixed(0)}%"></em></i><b>${nf(0).format(v)}/${mx}</b></div>`;
    const ok = (t) => `<li>✓ ${t}</li>`;
    body.innerHTML = `<div class="sk-sh"><div><b>${esc(r.s)}</b> <span class="ab-exp ${r.exp === "TAVAN" ? "tv" : ""}">${r.exp}</span><div class="sk-shp">${fP(r.p)} <span class="${cls(r.gd)}">${fPct(r.gd)}</span> · güven <b>${fN(r.sc)}</b></div></div><button type="button" class="sheet-x" data-abclose="1" aria-label="Kapat">✕</button></div>
      <div class="ab-parts">${bar("Kurum", P.kurum || 0, 30)}${bar("Hâlâ itiyor", P.itiyor || 0, 15)}${bar("AKD", P.akd || 0, 20)}${bar("Momentum", P.momentum || 0, 15)}${bar("Derinlik", P.derinlik || 0, 20)}</div>
      <ul class="ab-ok">
        ${ok(`<b>${abBr(r)}</b> ${esc(r.dr || "")} · ilk ayak izi ${esc(r.ft || "—")} · ciddiyet ${fN(r.msc)} · ısrar ${fN(r.israr)} · ${fShort(r.btl)} ₺ · ort. maliyet ${fP(r.cost)}`)}
        ${ok(`Son 15 dk: ${fShort(r.l15)} ₺ alış, %${fN(r.l15a, 0)} aktif, net ${fShort(r.l15n)} lot · son alış ${esc(r.lt || "—")}`)}
        ${ok(`AKD: net payı %${fN(r.np, 0)} · aktif alış %${fN(r.akt ?? 0, 0)}${r.tt ? ` · TAVAN TRENİ ${r.tt === 2 ? "GÜÇLÜ" : "ORTA"} (${esc(r.tt_br || "")})` : ""}`)}
        ${ok(r.at_t ? `TAVANDA · alış kuyruğu ${fShort(r.qtl)} ₺` : `Fiyat: zirveden %${nf(1).format(r.fade || 0)} geride · son 15 dk ${fPct(r.m15)} · tavana %${nf(1).format(r.room ?? 0)} yer`)}
        ${ok(`D-A-K ${fN(r.dak)} · Derinlik ${fN(r.d)}(${isNum(r.dp) ? fN(r.dp) : "—"}) · AKD ${fN(r.a)} · Kademe ${fN(r.k)}${r.ab ? ` · ALGO DESTEK ${esc(r.ab.pat)} ${fP(r.ab.p0)}→${fP(r.ab.p1)}` : ""}${r.aa ? ` · algo direnç ${fP(r.aa.p0)} (zayıf)` : ""}`)}
        ${ok([r.tvn ? "TAVAN ADAYI senaryosu" : r.cid ? "CİDDİ YÜKSELİŞ senaryosu" : "", (r.tren || []).length ? `TRENE ATLA ${r.tren.map((g) => g.t.slice(0, 5) + " @" + fP(g.p)).join(", ")}` : "", r.tt ? "TAVAN TRENİ" : ""].filter(Boolean).join(" · ") || "momentum")}
      </ul>
      <div class="ab-stop">${r.at_t ? esc(r.stop_w) : `Stop önerisi: <b>${fP(r.stop)}</b> (${esc(r.stop_w)})`}</div>
      <div class="src-note">Liste her 10 sn yeniden hesaplanır; koşullardan biri bozulursa hisse listeden çıkar ("Bugün listeden çıkanlar"). Yatırım tavsiyesi değildir.</div>
      <button type="button" class="btn-primary sk-open" data-abopen="${esc(r.s)}">Hisseyi aç</button>`;
  }
  function abClose() { const sh = $("ab-sheet"); if (sh) sh.hidden = true; document.body.classList.remove("sk-lock"); AB.sel = null; }
  document.addEventListener("change", (e) => {
    const i = e.target.closest && e.target.closest("[data-absw]"); if (!i) return;
    NP.modes[AB_NT] = i.checked ? "notify" : "off"; saveNP();
    if (i.checked) { if (NP.master === false) { NP.master = true; saveNP(); } askNotify(true); toast("✅ AL BUNU bildirimi AÇIK (listeye yeni giren güçlü hisse)"); } else toast("AL BUNU bildirimi KAPALI (liste görünmeye devam eder)");
    try { refreshNtRows(AB_NT); } catch (x) {}
    if (st.view === "albunu") abRender();
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest) return;
    if (e.target.closest("[data-abclose]")) { abClose(); return; }
    const o = e.target.closest("[data-abopen]"); if (o) { const s = o.dataset.abopen; abClose(); openStock(s); return; }
    if (st.view !== "albunu") return;
    const c = e.target.closest("#ab-body [data-absym]"); if (c) { abDetail(c.dataset.absym); return; }
    const c2 = e.target.closest("#ab-body [data-absym2]"); if (c2) { openStock(c2.dataset.absym2); return; }
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && AB.sel) abClose(); });

  window.__bist = { ab: { S: AB, open: abOpen, load: abLoad, render: abRender, detail: abDetail, close: abClose }, al: { S: AGW, open: alOpen, load: alLoad, render: alRender, detail: alDetail, close: alClose }, sk: { S: SK, open: skOpen, load: skLoad, render: skRender, detail: skDetail, close: skClose }, tr: { S: TR, open: trOpen, load: trLoad, render: trRender, on: trOn }, cl: () => CLV, ol: { S: OL, open: olOpen, load: olLoad, openAt: olOpenAt, sample: olSample, render: olRender, allCount: allAlCount },  eik: { S: EIK, apply: applyConfig, tap: eikTap, reset: eikReset, clear: eikClear, AP: EIK_AP, open: eikOpen }, atFilter: () => atFilter(), atFilterN: () => atFilterN(),  ob: { tf: fmzTf, setTf: fmzSetTf, seek: fmzSeek, replay: fmzReplay, proof: obProof, ov: obOv, ovState: OBV, draw: obDraw, chart: () => chart }, tx: { scan: txScan, find: txFind, open: txOpen, close: txClose, state: TX }, st, selectSymbol, openTab, go, isl, ak, bk, kr, ix, rd, tt, ag, pa, ku, th, AL, CID, NP, NH, NT, nfs, deliver, deliverLocal, kfShow, kfClose, togglePin, atS, flS, akpS, mkLevel, akkS, k5Show, CHL, fmS, fmProof, fmSeek, fmzS, fmApplyPre, atS };

  // ================================================================ v1.34.1 İdealData Hesabı (üstteki durum etiketine dokun)
  const IDA = { el: null, timer: 0 };
  function idaStatusText(s) {
    if (!s) return "—";
    if (s.healthy) return "✅ Bağlı";
    if (s.state === "login_failed") return "❌ Hata: " + (s.error || "giriş reddedildi");
    if (s.state === "error") return "⚠️ Hata: " + (s.error || "—");
    if (s.state === "connecting" || s.state === "logging_in" || s.reconnecting) return "⏳ Bağlanıyor…";
    return s.label || s.state || "—";
  }
  async function idaRefresh() {
    try {
      const a = await api("/api/ideal/account", { timeout: 8000 });
      const s = await api("/api/ideal/status", { timeout: 8000 });
      if (!IDA.el) return;
      const u = IDA.el.querySelector("#ida-user");
      if (u && !u.dataset.touched) u.value = a.user || "";
      IDA.el.querySelector("#ida-st").textContent = idaStatusText(s);
      IDA.el.querySelector("#ida-src").textContent = a.saved_in_app ? "Şifre: uygulamada kayıtlı" : "Şifre: sunucu ayarından";
      return s;
    } catch (e) { if (IDA.el) IDA.el.querySelector("#ida-st").textContent = "Sunucuya ulaşılamıyor"; }
  }
  function idaClose() { if (IDA.el) { IDA.el.remove(); IDA.el = null; } clearInterval(IDA.timer); IDA.timer = 0; }
  function idaOpen() {
    if (IDA.el) return;
    const ov = document.createElement("div");
    ov.className = "ida-ov";
    ov.innerHTML = '<div class="ida-box" role="dialog" aria-label="İdealData Hesabı">' +
      '<div class="ida-h">🔑 İdealData Hesabı<button class="ida-x" type="button" aria-label="Kapat">✕</button></div>' +
      '<div class="ida-row"><span>Durum</span><b id="ida-st">…</b></div>' +
      '<div class="ida-src" id="ida-src"></div>' +
      '<form id="ida-f" autocomplete="off">' +
      '<label>Kullanıcı adı<input id="ida-user" name="user" autocapitalize="off" autocorrect="off" spellcheck="false" maxlength="64" required></label>' +
      '<label>Şifre<input id="ida-pw" name="password" type="password" autocomplete="new-password" maxlength="128" required></label>' +
      '<button type="submit" class="ida-go">Kaydet ve Bağlan</button>' +
      '<div class="ida-msg" id="ida-msg"></div>' +
      '</form>' +
      '<button type="button" class="ida-lk" id="ida-lk">🔗 Link Optimizasyon</button>' +
      '<button type="button" class="ida-lk" data-gotg="1">✈️ Telegram Bildirim Ayarları</button>' +
      '<div class="ida-note">Hesabın başka bir yerde açık kaldıysa önce İdealData\'da şifreni değiştir, sonra yeni şifreyi buraya gir. Şifre sadece sunucuda saklanır, ekranda gösterilmez.</div>' +
      '</div>';
    document.body.appendChild(ov); IDA.el = ov;
    ov.addEventListener("click", (e) => { if (e.target === ov) idaClose(); });
    ov.querySelector(".ida-x").addEventListener("click", idaClose);
    ov.querySelector("#ida-lk").addEventListener("click", () => { idaClose(); lkOpen(); });
    ov.querySelector("#ida-user").addEventListener("input", (e) => { e.target.dataset.touched = "1"; });
    ov.querySelector("#ida-f").addEventListener("submit", async (e) => {
      e.preventDefault();
      const user = ov.querySelector("#ida-user").value.trim(), pwEl = ov.querySelector("#ida-pw"), msg = ov.querySelector("#ida-msg");
      const btn = ov.querySelector(".ida-go");
      if (!user || !pwEl.value) { msg.textContent = "Kullanıcı adı ve şifre gerekli"; return; }
      btn.disabled = true; msg.textContent = "Kaydediliyor…";
      try {
        const r = await fetch("/api/ideal/credentials", { method: "POST", headers: { "Content-Type": "application/json", "ngrok-skip-browser-warning": "1" },
          body: JSON.stringify({ user, password: pwEl.value }) });
        const d = await r.json().catch(() => ({}));
        pwEl.value = "";
        if (!r.ok || !d.ok) { msg.textContent = d.error || ("Hata " + r.status); btn.disabled = false; return; }
        msg.textContent = "Kaydedildi, bağlanıyor… (en çok ~1 dk)";
        const t0 = Date.now();
        const tick = async () => {
          const s = await idaRefresh();
          if (s && s.healthy) { msg.textContent = "✅ İdealData bağlandı"; btn.disabled = false; try { loadStatus(); } catch (x) {} toast("İdealData bağlandı ✓", 2200); return; }
          if (s && s.state === "login_failed" && Date.now() - t0 > 8000) { msg.textContent = "❌ Giriş reddedildi: " + (s.error || "şifreyi kontrol et"); btn.disabled = false; return; }
          if (Date.now() - t0 > 120000) { msg.textContent = "Hâlâ bağlanamadı — durumu yukarıdan takip et"; btn.disabled = false; return; }
          setTimeout(tick, 3000);
        };
        setTimeout(tick, 3000);
      } catch (x) { msg.textContent = "Sunucuya ulaşılamadı"; btn.disabled = false; }
    });
    idaRefresh(); IDA.timer = setInterval(idaRefresh, 5000);
    setTimeout(() => { const u = ov.querySelector("#ida-user"); (u && u.value ? ov.querySelector("#ida-pw") : u).focus(); }, 50);
  }
  try { const lp = $("live-pill"); lp.style.cursor = "pointer"; lp.addEventListener("click", (e) => { e.preventDefault(); idaOpen(); }); } catch (e) {}
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && IDA.el) idaClose(); });
  window.__bistIda = { open: idaOpen, close: idaClose };

  // ================================================================ v1.35.0 LİNK OPTİMİZASYON
  const LK = { el: null, timer: 0 };
  const fB = (b) => b >= 1e9 ? (b / 1e9).toFixed(2) + " GB" : b >= 1e6 ? (b / 1e6).toFixed(1) + " MB" : (b / 1e3).toFixed(0) + " KB";
  function lkBar(pct) { const c = pct >= 80 ? "#ef4444" : pct >= 50 ? "#f59e0b" : "#22c55e"; return `<div class="lk-bar"><i style="width:${Math.min(100, pct)}%;background:${c}"></i></div>`; }
  async function lkRefresh(cloud) {
    if (!LK.el) return;
    try {
      const d = await api("/api/link/status" + (cloud ? "?cloud=1" : ""), { timeout: 8000 });
      if (!LK.el) return;
      const m = d.month || {}, se = d.session || {};
      LK.d = d;
      LK.el.querySelector("#lk-body").innerHTML =
        `<div class="ida-row"><span>Tünel</span><b>${d.tunnel_up ? "✅ Açık" : d.ngrok_running ? "⏳ Başlıyor" : "❌ Kapalı"}</b></div>` +
        `<div class="lk-url">${esc(d.url || "—")}</div>` +
        (() => { const c = d.cf || {}; const up = c.uptime_sec;
          const upT = up == null ? "—" : up < 3600 ? Math.round(up / 60) + " dk" : (up / 3600).toFixed(1) + " sa";
          return `<div class="lk-cf"><div class="lk-h">☁️ Cloudflare (hesapsız quick tunnel)</div>` +
          `<div class="ida-row"><span>Durum</span><b>${c.healthy ? "✅ Sağlıklı" : c.registered ? "⚠️ Yanıt yok" : c.running ? "⏳ Bağlanıyor" : "❌ Kapalı"}</b></div>` +
          `<div class="lk-url">${esc(c.url || "— (link yok)")}</div>` +
          `<div class="ida-row"><span>Ömür</span><b>${upT}</b></div>` +
          `<div class="ida-row"><span>Son sağlık OK</span><b>${c.last_ok_ago != null ? c.last_ok_ago + " sn önce" : "—"} · hata ${fN(c.fails || 0)}</b></div>` +
          (c.err ? `<div class="lk-warn">${esc(c.err)}${c.next_retry_in ? " · " + c.next_retry_in + " sn sonra yeniden denenecek" : ""}</div>` : "") +
          `<div class="lk-btns"><button type="button" class="ida-go lk-copy" id="lk-cfcopy"${c.url ? "" : " disabled"}>📋 Kopyala</button><button type="button" class="ida-go lk-new" id="lk-cfnew"${c.new_wait > 0 ? " disabled" : ""}>Yeni Cloudflare Linki${c.new_wait > 0 ? " (" + c.new_wait + " sn)" : ""}</button></div>` +
          `<div class="ida-src">${esc(c.note || "")}</div></div>` +
          `<div class="lk-prim">Birincil link: <label><input type="radio" name="lkp" value="ngrok"${d.primary !== "cf" ? " checked" : ""}> ngrok</label> <label><input type="radio" name="lkp" value="cf"${d.primary === "cf" ? " checked" : ""}> Cloudflare</label><div class="ida-src">Açık sayfalar sağlıklıysa birincil linke otomatik geçer.</div></div>`; })() +
        `<div class="lk-h">ngrok hesapları (kota HESAP başına)</div>` +
        (d.accounts || []).map((a) => `<div class="lk-acc${a.current ? " cur" : ""}"><div class="ida-row"><span>${a.current ? "▶ " : ""}<b>${esc(a.label)}</b> ···${esc(a.last4)}</span><b>kalan %${a.remaining_pct}</b></div>` +
          `<div class="ida-src">${fN(a.req)} / 20.000 istek · ${fB(a.bytes)} / 1 GB${a.current ? " · KULLANIMDA" : ""}</div>${lkBar(Math.max(a.req_pct, a.bytes_pct))}` +
          (a.current ? "" : `<button type="button" class="lk-sw" data-id="${esc(a.id)}">Bu hesaba geç</button> <button type="button" class="lk-del" data-id="${esc(a.id)}">Sil</button>`) + `</div>`).join("") +
        `<label class="lk-auto"><input type="checkbox" id="lk-auto"${d.auto_switch ? " checked" : ""}> Etkin hesap %${d.auto_pct}'ı geçince otomatik (kesintisiz) en boş hesaba geç</label>` +
        `<div class="lk-h">Bu ay (${esc(m.month || "")}) · bu sunucunun toplam tünel kullanımı</div>` +
        `<div class="ida-row"><span>İstek</span><b>${fN(m.req)} / ${fN(m.req_limit)} (%${m.req_pct})</b></div>${lkBar(m.req_pct || 0)}` +
        `<div class="ida-row"><span>Veri</span><b>${fB(m.bytes || 0)} / 1 GB (%${m.bytes_pct})</b></div>${lkBar(m.bytes_pct || 0)}` +
        `<div class="ida-row"><span>Şu an</span><b>${fN(m.rpm)} istek/dk (sınır ${fN(m.rpm_limit)})</b></div>` +
        `<div class="ida-row"><span>Ay sonu tahmini</span><b>${fN(m.proj_req)} istek</b></div>` +
        `<div class="ida-row"><span>Bu tünel oturumu</span><b>${fN(se.http || 0)} istek · ${fN(se.conns || 0)} bağlantı</b></div>` +
        (d.warn && d.warn.length ? `<div class="lk-warn">⚠️ ${d.warn.map(esc).join("<br>⚠️ ")}</div>` : "") +
        (d.cloud ? `<div class="ida-src">ngrok API: ${d.cloud.ok ? "anahtar geçerli ✓ (kota verisi API'de yok)" : "hata " + esc(d.cloud.error || "")}</div>` : "") +
        `<div class="ida-src">Kaynak: ${esc(d.source)}. ${esc(d.note)}</div>`;
      LK.el.querySelectorAll(".lk-del").forEach((b) => b.addEventListener("click", async () => {
        if (!confirm("Bu hesap silinsin mi?")) return;
        await fetch("/api/link/accounts/delete", { method: "POST", headers: { "Content-Type": "application/json", "ngrok-skip-browser-warning": "1" }, body: JSON.stringify({ id: b.dataset.id }) }); lkRefresh();
      }));
      LK.el.querySelectorAll(".lk-sw").forEach((b) => b.addEventListener("click", async () => {
        if (!confirm("Bu hesaba geçilsin mi? Yeni tünel önce açılır, sonra eski kapanır (kesintisiz).")) return;
        const msg = LK.el.querySelector("#lk-msg"); msg.textContent = "Yeni hesabın tüneli açılıyor ve doğrulanıyor (~10-30 sn)…";
        try {
          const r = await fetch("/api/link/switch", { method: "POST", headers: { "Content-Type": "application/json", "ngrok-skip-browser-warning": "1" }, body: JSON.stringify({ id: b.dataset.id }) });
          const d = await r.json().catch(() => ({}));
          if (!r.ok) msg.textContent = d.detail || ("Hata " + r.status);
          else if (d.url) { msg.innerHTML = `✅ ${esc(d.account)} · yeni link: <b>${esc(d.url)}</b> (kota sıfır) — yönlendiriliyor…`; if (location.hostname.includes("ngrok")) setTimeout(() => { location.href = d.url + "/?v=" + APPV; }, 2000); }
          else msg.textContent = d.note || "Geçilemedi";
        } catch (e) { msg.textContent = "Sunucuya ulaşılamadı"; }
        lkRefresh();
      }));
      const cc = LK.el.querySelector("#lk-cfcopy");
      if (cc) cc.addEventListener("click", async () => { const u = d.cf && d.cf.url; if (!u) return; try { await navigator.clipboard.writeText(u + "/?v=" + APPV); LK.el.querySelector("#lk-msg").textContent = "Cloudflare linki kopyalandı ✓"; } catch (e) { LK.el.querySelector("#lk-msg").textContent = u; } });
      const cn = LK.el.querySelector("#lk-cfnew");
      if (cn) cn.addEventListener("click", async () => {
        const msg = LK.el.querySelector("#lk-msg"); cn.disabled = true; msg.textContent = "Cloudflare yeniden başlatılıyor (~10-60 sn)…";
        try { const r = await fetch("/api/link/cf/new", { method: "POST", headers: { "ngrok-skip-browser-warning": "1" } }); const x = await r.json().catch(() => ({}));
          msg.textContent = !r.ok ? (x.detail || "Hata " + r.status) : x.url ? "✅ Yeni Cloudflare linki: " + x.url : (x.note || "Bağlanamadı"); } catch (e) { msg.textContent = "Sunucuya ulaşılamadı"; }
        lkRefresh();
      });
      LK.el.querySelectorAll('input[name="lkp"]').forEach((r) => r.addEventListener("change", async () => {
        await fetch("/api/link/primary", { method: "POST", headers: { "Content-Type": "application/json", "ngrok-skip-browser-warning": "1" }, body: JSON.stringify({ p: r.value }) }).catch(() => {});
        LK.el.querySelector("#lk-msg").textContent = "Birincil: " + (r.value === "cf" ? "Cloudflare" : "ngrok"); lkRefresh();
      }));
      const au = LK.el.querySelector("#lk-auto");
      if (au) au.addEventListener("change", () => fetch("/api/link/auto", { method: "POST", headers: { "Content-Type": "application/json", "ngrok-skip-browser-warning": "1" }, body: JSON.stringify({ on: au.checked }) }));
      const nb = LK.el.querySelector("#lk-new");
      if (!LK.busy) { nb.disabled = d.new_link_wait > 0; nb.textContent = d.new_link_wait > 0 ? `Yeni Link Oluştur (${d.new_link_wait} sn)` : ((d.accounts || []).length > 1 ? "Yeni Link Oluştur (sonraki hesap · kota sıfır)" : "Yeni Link Oluştur (aynı hesap · kota SIFIRLANMAZ)"); }
      LK.el.querySelector("#lk-keyst").textContent = d.has_api_key ? "ngrok API anahtarı kayıtlı" : "ngrok API anahtarı yok (isteğe bağlı)";
    } catch (e) { if (LK.el) LK.el.querySelector("#lk-body").innerHTML = '<div class="ida-src">Sunucuya ulaşılamıyor — tekrar deneniyor…</div>'; }
  }
  function lkClose() { if (LK.el) { LK.el.remove(); LK.el = null; } clearInterval(LK.timer); LK.timer = 0; }
  function lkOpen() {
    if (LK.el) return;
    if (st.kfOpen) { try { kfClose(); } catch (e) {} }
    const ov = document.createElement("div"); ov.className = "ida-ov";
    ov.innerHTML = '<div class="ida-box lk-box" role="dialog" aria-label="Link Optimizasyon">' +
      '<div class="ida-h">🔗 Link Optimizasyon<button class="ida-x" type="button" aria-label="Kapat">✕</button></div>' +
      '<div id="lk-body"><div class="ida-src">Yükleniyor…</div></div>' +
      '<div class="lk-btns"><button type="button" class="ida-go lk-copy" id="lk-copy">📋 Linki Kopyala</button>' +
      '<button type="button" class="ida-go lk-new" id="lk-new">Yeni Link Oluştur</button></div>' +
      '<div class="ida-msg" id="lk-msg"></div>' +
      '<details class="lk-key" open><summary>➕ ngrok hesabı ekle (kota sıfırlamak için)</summary>' +
      '<input id="lk-alabel" placeholder="Etiket (ör. hesap2)" maxlength="40">' +
      '<input id="lk-atok" type="password" autocomplete="off" placeholder="ngrok authtoken (dashboard → Your Authtoken)">' +
      '<button type="button" class="ida-go" id="lk-aadd">Hesabı Ekle</button>' +
      '<div class="ida-src">Token yalnız sunucuda (izin 600) saklanır; ekranda sadece son 4 karakteri görünür.</div></details>' +
      '<details class="lk-key"><summary id="lk-keyst">ngrok API anahtarı</summary>' +
      '<input id="lk-key" type="password" autocomplete="off" placeholder="ngrok API anahtarı (dashboard → API)">' +
      '<button type="button" class="ida-go" id="lk-keysave">Kaydet / Doğrula</button>' +
      '<div class="ida-src">Anahtar yalnız sunucuda (izin 600) saklanır, geri gösterilmez. Boş bırakıp kaydedersen silinir. Not: ngrok API ücretsiz planda kullanım/kota bilgisi vermiyor; yalnız tünel listesini doğrular.</div></details>' +
      '<div class="ida-note">Yeni Link Oluştur: ngrok yeniden başlatılır, yeni adres birkaç saniyede gelir (2 dk\'da 1 kez). Eski link çalışmaz olur — bu sayfa yeni linke kendisi geçer. <b>Önemli:</b> ngrok kotası HESAP başınadır. Aynı hesapla yeni link kotayı SIFIRLAMAZ; buton kalan kotası en çok olan diğer hesaba geçer (kota sıfırlanır).</div>' +
      '</div>';
    document.body.appendChild(ov); LK.el = ov;
    ov.addEventListener("click", (e) => { if (e.target === ov) lkClose(); });
    ov.querySelector(".ida-x").addEventListener("click", lkClose);
    const msg = ov.querySelector("#lk-msg");
    ov.querySelector("#lk-copy").addEventListener("click", async () => {
      const u = LK.d && LK.d.url; if (!u) return;
      try { await navigator.clipboard.writeText(u + "/?v=" + APPV); msg.textContent = "Kopyalandı ✓"; }
      catch (e) { const ta = document.createElement("textarea"); ta.value = u + "/?v=" + APPV; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); msg.textContent = "Kopyalandı ✓"; } catch (x) { msg.textContent = u; } ta.remove(); }
    });
    ov.querySelector("#lk-new").addEventListener("click", async () => {
      if (!confirm("Yeni link oluşturulsun mu? Eski link kapanır.")) return;
      const nb = ov.querySelector("#lk-new"); LK.busy = true; nb.disabled = true; nb.textContent = "Oluşturuluyor…"; msg.textContent = "ngrok yeniden başlatılıyor (~10-20 sn)…";
      try {
        const r = await fetch("/api/link/new", { method: "POST", headers: { "ngrok-skip-browser-warning": "1" } });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) { msg.textContent = d.detail || ("Hata " + r.status); }
        else if (d.url) { msg.innerHTML = `✅ Yeni link: <b>${esc(d.url)}</b>` + (d.quota_reset ? ` · hesap: ${esc(d.account)} (kota sıfır)` : " · aynı hesap, kota SIFIRLANMADI"); if (location.hostname.includes("ngrok")) setTimeout(() => { location.href = d.url + "/?v=" + APPV; }, 2500); }
        else msg.textContent = d.note || "Link bekleniyor…";
      } catch (e) {
        msg.textContent = "Eski tünel kapandı — yeni link oluşuyor. Linki Tesr'e sor ya da sunucu bilgisayarından aç.";
      }
      LK.busy = false; lkRefresh();
    });
    ov.querySelector("#lk-aadd").addEventListener("click", async () => {
      const l = ov.querySelector("#lk-alabel"), t = ov.querySelector("#lk-atok");
      try {
        const r = await fetch("/api/link/accounts", { method: "POST", headers: { "Content-Type": "application/json", "ngrok-skip-browser-warning": "1" }, body: JSON.stringify({ label: l.value.trim(), token: t.value.trim() }) });
        const d = await r.json().catch(() => ({})); t.value = "";
        msg.textContent = r.ok ? "Hesap eklendi ✓" : (d.detail || "Hata"); if (r.ok) l.value = ""; lkRefresh();
      } catch (e) { msg.textContent = "Sunucuya ulaşılamadı"; }
    });
    ov.querySelector("#lk-keysave").addEventListener("click", async () => {
      const k = ov.querySelector("#lk-key");
      try {
        const r = await fetch("/api/link/apikey", { method: "POST", headers: { "Content-Type": "application/json", "ngrok-skip-browser-warning": "1" }, body: JSON.stringify({ key: k.value.trim() }) });
        const d = await r.json().catch(() => ({})); k.value = "";
        msg.textContent = !r.ok ? (d.detail || "Hata") : !d.has_api_key ? "Anahtar silindi" : d.cloud && d.cloud.ok ? "Anahtar kaydedildi ✓ (geçerli)" : "Kaydedildi ama doğrulanamadı: " + ((d.cloud && d.cloud.error) || "");
        lkRefresh(true);
      } catch (e) { msg.textContent = "Sunucuya ulaşılamadı"; }
    });
    lkRefresh(true); LK.timer = setInterval(() => { if (!document.hidden) lkRefresh(); }, 5000);
  }
  const APPV = "1.38.1";
  // v1.35.1: her ekranda etkin ngrok hesabı kota uyarısı (%80 sarı, %90 kırmızı) + link değişince otomatik yönlendirme
  (function quotaBanner() {
    const b = document.createElement("div"); b.id = "q-ban"; b.className = "q-ban"; b.hidden = true; document.body.appendChild(b);
    b.addEventListener("click", () => lkOpen());
    async function tick() {
      if (document.hidden) return;
      try {
        const d = await api("/api/link/status", { timeout: 8000 });
        const r = d.redirect, pub = /ngrok|trycloudflare/.test(location.hostname);
        if (r && r.to && location.hostname.includes("ngrok") && !r.to.includes(location.hostname)) { location.href = r.to + "/?v=" + APPV; return; }
        if (pub && d.primary_url && !d.primary_url.includes(location.hostname) && !sessionStorage.getItem("lkNoRedir")) { location.href = d.primary_url + "/?v=" + APPV; return; }   // v1.36.0 birincil sağlayıcı
        const a = (d.accounts || []).find((x) => x.current);
        const pct = a ? Math.max(a.req_pct, a.bytes_pct) : 0;
        if (pct >= 80) { b.hidden = false; b.className = "q-ban " + (pct >= 90 ? "red" : "amber"); b.textContent = `⚠️ ngrok kotası %${pct.toFixed(0)} (${a.label}) — dokun: Link Optimizasyon → hesap değiştir`; }
        else b.hidden = true;
      } catch (e) {}
    }
    setInterval(tick, 20000); setTimeout(tick, 3000);
  })();
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && LK.el) lkClose(); });
  // ================================================================ v1.36.0 ORDER BLOCK TARAMASI
  // v1.36.2: mod (ORTAK EN GÜÇLÜ varsayılan · Tüm bölgeler · GÜN İÇİ) + sıralama + güçlü filtreler + hazır ayarlar (localStorage)
  const OBT_DEF = { mode: "ortak", tur: "", tfs: [], min: 0, uz: 0, sev: "", minOrtak: 1, minUg: 0, minTep: 0, minTut: 0, kirilmamis: false, sonN: 0, bolgede: false, sort: "ortak", asc: false };
  const OBT = { d: null, tm: 0, f: Object.assign({}, OBT_DEF), sel: null, tf: "15m", panel: false };
  try { Object.assign(OBT.f, JSON.parse(localStorage.getItem("obtF") || "{}")); } catch (e) {}
  const obtSave = () => { try { localStorage.setItem("obtF", JSON.stringify(OBT.f)); } catch (e) {} };
  const OBT_PRE = {
    yakin: { label: "🟢 En güçlü ortak destekler (fiyata yakın)", f: { mode: "ortak", tur: "Destek", minOrtak: 3, uz: 3, sort: "ortak", asc: false } },
    tutan: { label: "🛡️ Çok test edilmiş ve tutan", f: { mode: "normal", minUg: 3, minTut: 70, kirilmamis: true, sort: "tutma", asc: false } },
    bolge: { label: "🎯 Şu an bölgede olanlar", f: { bolgede: true, sort: "guc", asc: false } },
  };
  const OBT_SORT = [["guc", "Güç"], ["ortak", "Ortak periyot sayısı"], ["ugradi", "Uğrama (test) sayısı"], ["tepki", "Tepki sayısı"], ["tuttu", "Tutma sayısı"],
    ["tutma", "Tutma oranı %"], ["tepkio", "Tepki oranı %"], ["sontest", "Son test zamanı"], ["yakin", "Fiyata yakınlık"], ["dtl", "Derinlik lotu (TL)"]];
  const obtKey = { guc: (r) => r.guc, ortak: (r) => r.ortak_n * 1000 + r.guc, ugradi: (r) => r.ugradi, tepki: (r) => r.tepki, tuttu: (r) => r.tuttu,
    tutma: (r) => r.tutma_oran ?? -1, tepkio: (r) => r.tepki_oran ?? -1, sontest: (r) => r.son_test || 0, yakin: (r) => -Math.abs(r.uzaklik), dtl: (r) => r.derinlik_tl || 0 };
  function obtOpen() { clearInterval(OBT.tm); obtLoad(); OBT.tm = setInterval(() => { if (st.view !== "obt") { clearInterval(OBT.tm); return; } if (!document.hidden) obtLoad(); }, 30000); }
  async function obtLoad() {
    const mode = OBT.f.mode;
    try { const d = await api("/api/ob/list?limit=6000&tf=" + (mode === "normal" ? "" : mode), { timeout: 25000 }); d._mode = mode; OBT.d = d; OBT.err = null; } catch (e) { OBT.err = String(e.message || e); }
    if (st.view === "obt") obtRender();
  }
  const obtAge = (s) => s == null ? "—" : s < 90 ? s + " sn" : s < 5400 ? Math.round(s / 60) + " dk" : Math.round(s / 3600) + " sa";
  function obtRender() {
    const d = OBT.d, body = $("obt-body"), f = OBT.f;
    if (d && d._mode !== f.mode) { obtLoad(); }
    if (!d) { body.innerHTML = `<div class="card"><div class="empty">${OBT.err ? "Alınamadı: " + esc(OBT.err) : "Yükleniyor…"}</div></div>`; return; }
    const m = d.meta || {}, TL = d.tf_label || {}, ALL = (d.tfs || []).filter((x) => x !== "gunici");
    $("obt-sub").textContent = m.ready ? `${fN(m.n_sym)} hisse · ${m.live ? "CANLI" : "kayıtlı veri"} · tarama ${obtAge(m.age_sec)} önce (${m.sec} sn)` : "Tarama hazırlanıyor (ilk tarama ~2 dk)…";
    const R = (d.rows || []).filter((r) => (!f.tur || r.tur === f.tur) && r.guc >= f.min && (!f.uz || Math.abs(r.uzaklik) <= f.uz) && (!f.sev || r.seviye === f.sev)
      && r.ortak_n >= f.minOrtak && r.ugradi >= f.minUg && r.tepki >= f.minTep && (!f.minTut || (r.tutma_oran ?? -1) >= f.minTut) && (!f.kirilmamis || r.kirildi === 0)
      && (!f.sonN || (r.test_seans_once != null && r.test_seans_once < f.sonN)) && (!f.bolgede || r.aktif || r.uzaklik === 0) && (!f.tfs.length || f.tfs.every((x) => r.tfs.includes(x))));
    const k = obtKey[f.sort] || obtKey.guc; R.sort((a, b) => (f.asc ? 1 : -1) * (k(a) - k(b)) || (b.guc - a.guc));
    const chip = (key, v, t, extra = "") => `<button type="button" class="obt-f${f[key] === v ? " on" : ""}${extra}" data-k="${key}" data-v="${v}">${t}</button>`;
    const modes = `<div class="obt-modes">${chip("mode", "ortak", "⭐ ORTAK EN GÜÇLÜ", " big")}${chip("mode", "normal", "Tüm bölgeler")}${chip("mode", "gunici", "GÜN İÇİ")}</div>`;
    const pres = Object.entries(OBT_PRE).map(([id, p]) => `<button type="button" class="obt-pre" data-pre="${id}">${p.label}</button>`).join("");
    const sel = (key, opts) => `<select class="obt-sel" data-k="${key}">${opts.map(([v, t]) => `<option value="${v}"${String(f[key]) === String(v) ? " selected" : ""}>${t}</option>`).join("")}</select>`;
    const num = (key, opts, lab) => `<label class="obt-lab">${lab}${sel(key, opts.map((x) => [x, x || "—"]))}</label>`;
    const panel = `<div class="card obt-fil">
      ${modes}
      <div class="obt-row">${pres}</div>
      <div class="obt-row"><label class="obt-lab">Sırala${sel("sort", OBT_SORT)}</label><button type="button" class="obt-f on" data-asc="1">${f.asc ? "↑ Artan" : "↓ Azalan"}</button>
        <button type="button" class="obt-f" data-panel="1">${OBT.panel ? "▲ Filtreleri gizle" : "▼ Tüm filtreler"}</button><button type="button" class="obt-f" data-reset="1">Sıfırla</button></div>
      <div class="obt-row">${chip("tur", "", "Hepsi")}${chip("tur", "Destek", "🟢 Destek")}${chip("tur", "Direnç", "🔴 Direnç")}</div>
      ${OBT.panel ? `<div class="obt-row">${num("minOrtak", [1, 2, 3, 4, 5, 6, 7, 8, 9], "Min ortak periyot")}${num("minUg", [0, 1, 2, 3, 5, 10], "Min uğrama")}${num("minTep", [0, 1, 2, 3, 5], "Min tepki")}</div>
      <div class="obt-row">${num("minTut", [0, 50, 70, 80, 100], "Min tutma %")}${num("uz", [0, 1, 2, 3, 5, 10], "Uzaklık ≤ %")}${num("min", [0, 40, 50, 60, 75], "Min güç")}${num("sonN", [0, 1, 2, 3, 5, 10], "Son N seansta test")}</div>
      <div class="obt-row"><label class="obt-lab"><input type="checkbox" data-cb="kirilmamis"${f.kirilmamis ? " checked" : ""}> Hiç kırılmamış</label><label class="obt-lab"><input type="checkbox" data-cb="bolgede"${f.bolgede ? " checked" : ""}> Şu an bölgede</label>${chip("sev", "", "Tüm seviyeler")}${chip("sev", "ÇOK GÜÇLÜ", "ÇOK GÜÇLÜ")}${chip("sev", "GÜÇLÜ", "GÜÇLÜ")}</div>
      <div class="obt-row">Periyot içersin: ${(f.mode === "gunici" ? ["1m", "5m", "15m"] : ALL).map((x) => `<button type="button" class="obt-f${f.tfs.includes(x) ? " on" : ""}" data-tfc="${x}">${esc(TL[x] || x)}</button>`).join("")}</div>` : ""}
      ${f.mode === "ortak" ? `<div class="obt-gi">ORTAK EN GÜÇLÜ: her hissede en çok periyodun (9: 1dk…1 Hafta) örtüştüğü fiyat aralıkları (±%${(m.cfg || {}).ortak_tol_pct ?? 0.3} / ${(m.cfg || {}).ortak_tol_ticks ?? 2} adım tolerans). Önce ortak periyot sayısı, sonra güç.</div>` : ""}
      ${f.mode === "gunici" ? `<div class="obt-gi">GÜN İÇİ: her hissenin SON SEANS dip–tepe aralığında, o seansın 1/5/15 dk barlarıyla bulunan bölgeler.</div>` : ""}
      <div class="src-note">${fN(R.length)} sonuç / ${fN((d.rows || []).length)} · Sayımlar OB oluştuktan sonra, bölgenin en ince periyodunun kendi barlarıyla. Veri: ${esc(m.src || "—")} · son tarama ${esc(m.ts_ad || "—")}</div></div>`;
    const badge = (r) => (r.mod === "gunici" ? ["1m", "5m", "15m"] : ALL).map((x) => `<span class="obt-b${r.tfs.includes(x) ? " on" : (r.mevcut || []).includes(x) ? "" : " na"}" title="${r.tfs.includes(x) ? "ortak" : (r.mevcut || []).includes(x) ? "bu periyotta örtüşmüyor" : "veri yok"}">${esc(TL[x] || x)}</span>`).join("");
    const ON = OBT.n || 300;
    const rows = R.slice(0, ON).map((r) => `<div class="card obt-it ${r.yon === "U" ? "sup" : "res"}" data-sym="${esc(r.sym)}">
      <div class="obt-top"><b>${esc(r.sym)}</b><span class="obt-tag ${r.yon === "U" ? "g" : "r"}">${r.tur}</span><span class="obt-ort">${r.ortak_n}/${r.tum_n} periyotta ortak</span><span class="obt-guc">${r.guc}</span></div>
      <div class="obt-l dim">${r.ortak_n}/${r.mevcut_n} mevcut periyot · ${r.tum_n - r.mevcut_n ? (r.tum_n - r.mevcut_n) + " periyotta veri yok" : "tüm periyotlarda veri var"}</div>
      <div class="obt-bs">${badge(r)}</div>
      ${r.seans_ar ? `<div class="obt-l obt-gi">Seans ${esc(r.seans_ar.gun)}: dip ₺${fP(r.seans_ar.lo)} · tepe ₺${fP(r.seans_ar.hi)}</div>` : ""}
      <div class="obt-l">Ortak aralık <b>₺${fP(r.lo)} – ₺${fP(r.hi)}</b> · fiyat ₺${fP(r.fiyat)} · uzaklık %${r.uzaklik}${r.aktif ? " · <b>şu an bölgede</b>" : ""}</div>
      <div class="obt-l">uğradı <b>${r.ugradi}</b> · tepki <b>${r.tepki}</b>${r.tepki_oran != null ? " (%" + r.tepki_oran + ")" : ""} · tuttu <b>${r.tuttu}</b>${r.tutma_oran != null ? " (%" + r.tutma_oran + ")" : ""} · kırıldı <b>${r.kirildi}</b>${r.son_test_ad ? " · son test " + esc(r.son_test_ad) : ""}</div>
      <div class="obt-l dim">Sayım: ${esc(r.say_tf_ad)} barları · son ${r.seans} seans${r.derinlik ? ` · derinlik ${fN(r.derinlik.lot)} lot ≈ ₺${fN(r.derinlik_tl)} (${esc(r.derinlik.src)} ${esc(r.derinlik.ts)})` : ""}</div>
    </div>`).join("");
    body.innerHTML = panel + (rows || `<div class="card"><div class="empty">${m.ready ? "Filtreye uyan bölge yok" : "Tarama sürüyor…"}</div></div>`) + (R.length > ON ? `<div class="src-note">İlk ${fN(ON)} / ${fN(R.length)} gösteriliyor <button type="button" class="obt-pre" data-obtmore="1">daha fazla</button></div>` : "");
    const upd = () => { obtSave(); obtRender(); };
    body.querySelectorAll(".obt-f[data-k]").forEach((b) => b.addEventListener("click", () => { const kk = b.dataset.k; f[kk] = b.dataset.v; if (kk === "mode") { f.tfs = []; obtSave(); obtLoad(); return; } upd(); }));
    body.querySelectorAll(".obt-sel").forEach((x) => x.addEventListener("change", () => { const kk = x.dataset.k; f[kk] = kk === "sort" ? x.value : +x.value; upd(); }));
    body.querySelectorAll("[data-cb]").forEach((x) => x.addEventListener("change", () => { f[x.dataset.cb] = x.checked; upd(); }));
    body.querySelectorAll("[data-tfc]").forEach((b) => b.addEventListener("click", () => { const x = b.dataset.tfc; f.tfs = f.tfs.includes(x) ? f.tfs.filter((y) => y !== x) : f.tfs.concat([x]); upd(); }));
    const q = (sel) => body.querySelector(sel);
    q("[data-asc]").addEventListener("click", () => { f.asc = !f.asc; upd(); });
    q("[data-panel]").addEventListener("click", () => { OBT.panel = !OBT.panel; obtRender(); });
    q("[data-reset]").addEventListener("click", () => { const md = f.mode; OBT.f = Object.assign({}, OBT_DEF, { mode: md }); obtSave(); obtRender(); });
    body.querySelectorAll("[data-pre]").forEach((b) => b.addEventListener("click", () => { const md = f.mode; OBT.f = Object.assign({}, OBT_DEF, { mode: md }, OBT_PRE[b.dataset.pre].f); obtSave(); if (OBT.f.mode !== md) obtLoad(); else obtRender(); toast(OBT_PRE[b.dataset.pre].label); }));
    body.querySelectorAll(".obt-it").forEach((c) => c.addEventListener("click", () => obtDetail(c.dataset.sym, f.mode === "gunici" ? "gunici" : (OBT.tf === "gunici" ? "15m" : null))));
  }
  async function obtDetail(sym, tf) {
    OBT.sel = sym; if (tf) OBT.tf = tf;
    const sh = $("obt-sheet"), sb = $("obt-sbody"); sh.hidden = false; sb.innerHTML = '<div class="empty">Yükleniyor…</div>';
    let d; try { d = await api(`/api/ob/detail/${encodeURIComponent(sym)}?tf=${OBT.tf}`, { timeout: 20000 }); } catch (e) { sb.innerHTML = `<div class="empty">Alınamadı</div>`; return; }
    const Z = d.zones || [], B = d.bars || [];
    let svg = '<div class="empty">Bu periyotta bar yok</div>';
    if (B.length) {
      const W = 380, H = 240;
      let lo = Math.min(...B.map((b) => b[3])), hi = Math.max(...B.map((b) => b[2]));
      const blo = lo * 0.92, bhi = hi * 1.08, vis = (z) => z.hi >= blo && z.lo <= bhi;   // v1.36.2: uzak bölgeler grafiği ezmesin
      Z.forEach((z) => { if (vis(z)) { lo = Math.min(lo, z.lo); hi = Math.max(hi, z.hi); } });
      (d.ortak || []).forEach((z) => { if (vis(z)) { lo = Math.min(lo, z.lo); hi = Math.max(hi, z.hi); } });
      if (d.seans) { lo = Math.min(lo, d.seans.lo); hi = Math.max(hi, d.seans.hi); }
      const pad = (hi - lo) * 0.05 || 1; lo -= pad; hi += pad;
      const y = (p) => H - ((p - lo) / (hi - lo)) * H, bw = W / B.length;
      const se = d.seans;
      const sl = se ? `<line x1="0" x2="${W}" y1="${y(se.hi)}" y2="${y(se.hi)}" stroke="#fbbf24" stroke-dasharray="4 3"/><text x="4" y="${y(se.hi) - 2}" fill="#fbbf24" font-size="9">Seans tepe ${fP(se.hi)}</text><line x1="0" x2="${W}" y1="${y(se.lo)}" y2="${y(se.lo)}" stroke="#fbbf24" stroke-dasharray="4 3"/><text x="4" y="${y(se.lo) + 10}" fill="#fbbf24" font-size="9">Seans dip ${fP(se.lo)}</text>` : "";
      const OR = (d.ortak || []).filter(vis).slice(0, 6);
      const orr = OR.map((z) => `<rect x="0" width="${W}" y="${y(z.hi)}" height="${Math.max(3, y(z.lo) - y(z.hi))}" fill="none" stroke="${z.yon === "U" ? "#4ade80" : "#f87171"}" stroke-width="2.5"/><text x="4" y="${y(z.lo) + 10}" fill="#fde68a" font-size="10" font-weight="700">★ ${z.ortak_n}/${z.tum_n} ${fP(z.lo)}–${fP(z.hi)}</text>`).join("");
      const zr = sl + orr + Z.filter(vis).map((z) => `<rect x="0" width="${W}" y="${y(z.hi)}" height="${Math.max(2, y(z.lo) - y(z.hi))}" fill="${z.yon === "U" ? "#22c55e" : "#ef4444"}" opacity="${z.seviye === "ÇOK GÜÇLÜ" ? 0.35 : z.seviye === "GÜÇLÜ" ? 0.25 : 0.14}"/><text x="${W - 4}" y="${y(z.hi) - 2}" fill="${z.yon === "U" ? "#86efac" : "#fca5a5"}" font-size="9" text-anchor="end">${z.tur} ${z.guc}</text>`).join("");
      const cs = B.map((b, i) => { const x = i * bw + bw / 2, up = b[4] >= b[1], col = up ? "#22c55e" : "#ef4444";
        return `<line x1="${x}" x2="${x}" y1="${y(b[2])}" y2="${y(b[3])}" stroke="${col}" stroke-width="1"/><rect x="${x - bw * 0.35}" width="${Math.max(1, bw * 0.7)}" y="${y(Math.max(b[1], b[4]))}" height="${Math.max(1, Math.abs(y(b[1]) - y(b[4])))}" fill="${col}"/>`; }).join("");
      svg = `<svg viewBox="0 0 ${W} ${H}" class="obt-svg">${zr}${cs}</svg>`;
    }
    const tfs = (d.tfs || []).map((x) => `<button type="button" class="obt-f${x === OBT.tf ? " on" : ""}" data-tf="${x}">${(d.tf_label || {})[x] || x}</button>`).join("");
    const zs = Z.map((z) => `<div class="obt-z ${z.yon === "U" ? "sup" : "res"}"><div class="obt-top"><b>${z.tur}</b> ₺${fP(z.lo)}–₺${fP(z.hi)} ${z.seviye !== "NORMAL" ? `<span class="obt-sev${z.seviye === "ÇOK GÜÇLÜ" ? " cok" : ""}">${z.seviye}</span>` : ""}<span class="obt-guc">${z.guc}</span></div>
      <div class="obt-l">Periyotlar: ${z.tf_ad.join(" · ")} · uzaklık %${z.uzaklik}</div>
      <div class="obt-cnt"><div><b>${z.ugradi}</b><span>uğradı</span></div><div><b>${z.tepki}</b><span>tepki</span></div><div><b>${z.tuttu}</b><span>tuttu</span></div><div><b>${z.kirildi}</b><span>kırıldı</span></div></div>
      <div class="obt-l dim">Sayım: ${esc(z.say_tf_ad)} barları · son ${z.seans} seans · ${z.bar} bar (${esc(z.pencere || "—")})${z.aktif ? " · şu an bölgede" : ""}${z.son_test_ad ? " · son test " + esc(z.son_test_ad) : ""}</div>
      ${(z.epizot || []).length ? `<div class="obt-l dim">Ziyaretler: ${z.epizot.map((e) => `${esc(e.t)} ${e.kirildi ? "❌kırıldı" : "✅tuttu"}${e.tepki ? "↗tepki" : ""}${e.aktif ? " (sürüyor)" : ""}`).join(" · ")}</div>` : ""}
      <div class="obt-l dim">Güç dökümü: kesişim ${z.dokum.kesisim} + tepki ${z.dokum.tepki} + tutma ${z.dokum.tutma} + OB ${z.dokum.ob_skor} + derinlik ${z.dokum.derinlik} + kademe ${z.dokum.kademe} = ${z.guc}</div>
      ${z.derinlik ? `<div class="obt-l dim">Derinlik (${esc(z.derinlik.src)}, ${esc(z.derinlik.ts)}): ${fN(z.derinlik.lot)} lot, ${z.derinlik.kademe} kademe, kademe ort. ×${z.derinlik.oran}</div>` : `<div class="obt-l dim">Derinlik: kayıt yok</div>`}
      ${z.kademe ? `<div class="obt-l dim">Kademe (${esc(z.kademe.gun)}, ${esc(z.kademe.src)}): ${fN(z.kademe.lot)} lot · ₺${fN(z.kademe.tl)} · günün %${z.kademe.pay_gun}'i · aktif alış %${z.kademe.aktif_alis} / satış %${z.kademe.aktif_satis}${z.kademe.alan ? " · en çok alan " + esc(z.kademe.alan.ad) + " %" + z.kademe.alan.pay : ""}${z.kademe.satan ? " · en çok satan " + esc(z.kademe.satan.ad) + " %" + z.kademe.satan.pay : ""}</div>` : `<div class="obt-l dim">Kademe: bölgede işlem kaydı yok</div>`}
      <div class="obt-l dim">Üye OB'ler: ${(z.uyeler || []).map((u) => `${esc((d.tf_label || {})[u.tf] || u.tf)} ₺${fP(u.bot)}–${fP(u.top)} (skor ${u.skor}${u.t ? ", " + esc(u.t) : ""}; kendi barlarında u${u.ugradi}/t${u.tepki}/tut${u.tuttu}/k${u.kirildi})`).join(" · ")}</div></div>`).join("");
    sb.innerHTML = `<div class="ida-h">🧱 ${esc(sym)} · Order Block<button class="ida-x" type="button" data-obtclose="1">✕</button></div>
      ${(d.ortak || []).length ? `<div class="obt-oc"><div class="lk-h">⭐ ORTAK EN GÜÇLÜ SEVİYELER</div>${d.ortak.map((z) => `<div class="obt-ocr ${z.yon === "U" ? "sup" : "res"}"><b>${z.tur} ₺${fP(z.lo)}–₺${fP(z.hi)}</b> <span class="obt-ort">${z.ortak_n}/${z.tum_n}</span> <span class="obt-guc s">${z.guc}</span>
        <div class="obt-l dim">${z.ortak_n}/${z.mevcut_n} mevcut · ${z.tf_ad.join(" · ")} · uzaklık %${z.uzaklik}</div>
        <div class="obt-l">uğradı ${z.ugradi} · tepki ${z.tepki} · tuttu ${z.tuttu} · kırıldı ${z.kirildi} <span class="dim">(${esc(z.say_tf_ad)} barları, son ${z.seans} seans)</span></div></div>`).join("")}</div>` : ""}
      <div class="obt-row">${tfs}</div>${svg}<div class="src-note">Grafik: ${esc((d.tf_label || {})[d.tf] || d.tf)} barlar; yeşil = destek, kırmızı = direnç (koyu = ÇOK GÜÇLÜ). Tarama ${obtAge((d.meta || {}).age_sec)} önce.</div>
      ${zs || '<div class="empty">Bu hissede geçerli bölge yok</div>'}
      <button type="button" class="ida-go" id="obt-go">Hisse sayfasını aç</button>`;
    sb.querySelectorAll("[data-tf]").forEach((b) => b.addEventListener("click", () => obtDetail(sym, b.dataset.tf)));
    sb.querySelector("#obt-go").addEventListener("click", () => { $("obt-sheet").hidden = true; selectSymbol(sym); });
  }
  document.addEventListener("click", (e) => { if (e.target && e.target.closest && e.target.closest("[data-obtclose]")) $("obt-sheet").hidden = true; });
  document.addEventListener("click", (e) => { if (e.target && e.target.closest && e.target.closest("[data-obtmore]")) { OBT.n = (OBT.n || 300) + 300; obtRender(); } });   // v1.37.0
  window.__bistObt = { open: obtOpen, detail: obtDetail, S: OBT };

  window.__bistLk = { open: lkOpen, close: lkClose, refresh: lkRefresh };

// ===================================================================== v1.37.0 ORTAK İLERLEME ÇUBUĞU
// Tek bileşen: her tarayıcı ekranının üstünde ince çubuk + "X yükleniyor: 312/524 (%60) · ~20 sn kaldı" /
// boştayken "Son tarama: X sn önce". Kaynak: GET /api/progress?k=… (çalışırken 2 sn, boşta 15 sn'de bir; üst üste istek yok).
(function () {
  const MAP = {
    fm_mum: ["fm"], fm_grafik: ["fm"], obt: ["ob"], skor: ["skor", "dpage"], algo: ["algo"], albunu: ["albunu"],
    baski: ["baski"], akdt: ["akd"], akk: ["akd"], olay: ["olay"], op: ["op", "kademe", "maliyet", "baski"],
    eik: ["eik"], tren: ["tren"], radar: ["radar"], tavan: ["radar"], agresif: ["radar"], para: ["radar"],
    kurumuyari: ["radar"], tahtaci: ["radar"], movers: ["lite"], favs: ["lite"],
  };
  const PGS = { d: null, at: 0, busy: false, next: 0, prev: {} };
  // tur bittiğinde (ya da Formasyonlarda her periyot bittiğinde → kısmi sonuç) ekranı hemen tazele
  const RELOAD = {
    fm_mum: () => fmLoad(fmKind(st.view), false), fm_grafik: () => fmLoad(fmKind(st.view), false), obt: () => obtLoad(),
    skor: () => skLoad(true), algo: () => alLoad(true), albunu: () => abLoad(), olay: () => olLoad(true),
  };
  const fmtS = (s) => s == null ? "—" : s < 60 ? Math.round(s) + " sn" : s < 3600 ? Math.round(s / 60) + " dk" : Math.round(s / 3600) + " sa";
  function el() {
    const v = document.querySelector(`.view[data-view="${st.view}"]`);
    if (!v) return null;
    let b = v.querySelector(":scope > .pgbar");
    if (!b) { b = document.createElement("div"); b.className = "pgbar"; b.innerHTML = '<div class="pg-t"></div><div class="pg-r"><i></i></div>'; v.prepend(b); }
    return b;
  }
  function draw() {
    const keys = MAP[st.view];
    document.querySelectorAll(".pgbar").forEach((x) => { if (!keys || !x.closest(`.view[data-view="${st.view}"]`)) x.hidden = true; });
    if (!keys || !PGS.d) return;
    const b = el(); if (!b) return;
    const dt = (Date.now() - PGS.at) / 1000;
    const E = keys.map((k) => PGS.d[k]).filter(Boolean);
    b.hidden = false;
    const run = E.find((e) => e.running);
    const t = b.querySelector(".pg-t"), bar = b.querySelector(".pg-r i");
    if (run) {
      const el2 = (run.elapsed || 0) + dt;
      let txt = `${esc(run.phase || run.label + " yükleniyor")}`, pct = run.pct;
      if (run.total) {
        txt += `: ${fN(run.done)}/${fN(run.total)} (%${Math.round(run.pct || 0)})`;
      }
      let eta = run.eta != null ? Math.max(0, run.eta - dt) : null;
      if (eta != null) txt += ` · ~${fmtS(eta)} kaldı`;
      else txt += ` · ${fmtS(el2)} geçti`;
      if (pct == null && run.last_sec) pct = Math.min(99, (el2 / run.last_sec) * 100);
      b.className = "pgbar run" + (pct == null ? " ind" : "");
      bar.style.width = (pct == null ? 30 : Math.max(2, pct)) + "%";
      t.innerHTML = txt;
    } else {
      const last = E.filter((e) => e.age != null).sort((a, c) => a.age - c.age)[0];
      b.className = "pgbar idle";
      bar.style.width = "100%";
      t.innerHTML = last ? `Son tarama: ${fmtS(last.age + dt)} önce${last.last_sec != null ? ` · ${String(last.last_sec).replace(".", ",")} sn sürdü` : ""}${last.err ? ` · <span class="neg">hata</span>` : ""}`
        : `${esc((E[0] && E[0].label) || "Tarama")} henüz tamamlanmadı (motor başlıyor)`;
    }
  }
  async function poll() {
    const keys = MAP[st.view];
    if (!keys || document.hidden || PGS.busy || Date.now() < PGS.next) return;
    PGS.busy = true;
    try {
      const d = await api("/api/progress?k=" + [...new Set(Object.values(MAP).flat())].join(","), { timeout: 6000 });
      PGS.d = d.engines || {}; PGS.at = Date.now();
      try {
        const ks = MAP[st.view] || [];
        const fire = ks.some((k) => { const a = PGS.prev[k], b = PGS.d[k]; return a && b && ((a.running && !b.running) || (a.running && b.running && a.phase !== b.phase)); });
        PGS.prev = PGS.d;
        if (fire && RELOAD[st.view]) RELOAD[st.view]();
      } catch (x) {}
      const anyRun = Object.values(PGS.d).some((e) => e.running);
      PGS.next = Date.now() + (anyRun ? 2000 : 15000);
    } catch (e) { PGS.next = Date.now() + 5000; }
    finally { PGS.busy = false; }
    draw();
  }
  let lastView = null;
  setInterval(() => {
    if (st.view !== lastView) { lastView = st.view; PGS.next = 0; }
    poll(); draw();
  }, 1000);
  window.PGBAR = { poll, draw, MAP };
})();

})();
