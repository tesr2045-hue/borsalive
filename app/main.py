"""BIST Analiz — FastAPI backend for Borsa Istanbul live quotes & movers."""
from __future__ import annotations

import json
import logging
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.history_cache import (
    RVOL_TF_DEF,
    RVOL_TF_N,
    RVOL10_TF_N,
    SCANNER_UNIVERSE_LIMIT,
    TF_INTERVALS,
)
from app.analysis import (
    NOTES_RULES,
    SIGNAL_RULES,
    VP_METHOD,
    build_signal,
    build_stock_notes,
    compute_volume_profile,
)
from app.features import (
    HIGH_BREAK_METHOD,
    MOMENTUM_BURST_METHOD,
    PARABOLIC_METHOD,
    PERSISTENCE_METHOD,
    POC_SHIFT_METHOD,
    PROFILE_BIAS_METHOD,
    SR_METHOD,
    TRADE_PLAN_METHOD,
    VA_MIG_METHOD,
    VWAP_AORT_METHOD,
    compute_high_breaks,
    compute_momentum_burst,
    compute_parabolic_score,
    compute_persistence,
    compute_poc_migration,
    compute_profile_bias,
    compute_trade_plan,
    compute_va_migration,
    compute_vwap_aort,
    detect_support_resistance,
)
from app.quotes import (
    ALLOWED_PERIODS,
    CHART_PRESETS,
    CHART_SOURCE,
    CHART_SOURCE_LABEL,
    CHART_TF_DOC,
    QUOTE_CACHE_TTL_CLOSED,
    QUOTE_CACHE_TTL_OPEN,
    RVOL10_DEF,
    RVOL_DEF,
    RVOL_DEFS,
    YAHOO_DELAY_NOTE,
    YAHOO_INTRADAY_NOTES,
    is_bist_session_open,
    quote_service,
)
from app.chart_provider import CHART_NOTES, provider_info as chart_provider_info
from app.scanners import scanner_service
from app.symbols import get_symbols, load_cache
from app.ideal_feed import ideal_feed
from app.live_store import event_detector, trade_store
from app.index_impact import get_index_impact
from app.v120 import hub as v120_hub
from app.operasyon import op as op_engine, NT_DEFAULTS as OP_NT_DEFAULTS
from app import v120 as _v120mod
from app.v122 import engine as k_engine, NT_DEFAULTS as K_NT_DEFAULTS   # v1.22.0 kademe & şerit
from app.v123 import m_engine, NT_DEFAULTS as M_NT_DEFAULTS, FID as M_FID   # v1.23.0 maliyet yükselten kurumlar
from app.v124 import b_engine, NT_DEFAULTS as B_NT_DEFAULTS, FIDS as B_FIDS   # v1.24.0 POC / alış ort. baskısı + hazır senaryolar + Özet+
from app.v125 import d_engine, NT_DEFAULTS as D_NT_DEFAULTS   # v1.25.0 derinlik analizleri + derinlik kaydı
from app.v126 import v126 as v126_engine, NT_DEFAULTS as V126_NT_DEFAULTS   # v1.26.0 işlem akışı + AKD K/Z + AKD taraması
from app.v127 import v127 as v127_engine, NT_DEFAULTS as V127_NT_DEFAULTS   # v1.27.0 mum + grafik formasyonları
import app.v128 as _v128   # v1.28.0 ORDER BLOCK katmanı (v127 motoruna OB/FVG + /api/formasyon/ob)
from app.v1271 import akd_donem as v1271_akd_donem   # v1.27.1 AKD Taraması TÜM AKD NET — HAFTALIK/AYLIK dönem (İLK 3/5/10 NET PGÇ)
from app.telegram_notify import telegram as tg_sender   # v1.38.0 (OneSignal kaldırıldı)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bist")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

_symbols: list[dict] = []


_pv_cache: dict = {"ts": 0.0, "map": {}}


def _prev_volume(sym: str):
    import time as _t
    if _t.time() - _pv_cache["ts"] > 120:
        m = {}
        for q in (quote_service._cache or []):
            if q.get("symbol") and q.get("prev_volume"):
                m[q["symbol"]] = q["prev_volume"]
        _pv_cache["map"] = m
        _pv_cache["ts"] = _t.time()
    return _pv_cache["map"].get(sym)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _symbols
    _symbols = get_symbols()
    quote_service.set_name_map(_symbols)
    _, _, meta = load_cache()
    logger.info("Loaded %d BIST symbols (meta=%s)", len(_symbols), meta.get("sources") if meta else {})

    def _warm():
        try:
            quotes, err = quote_service.fetch_all(_symbols)
            logger.info("Warm cache: %d quotes (err=%s)", len(quotes), err)
        except Exception as e:
            logger.warning("Warm cache failed: %s", e)

    threading.Thread(target=_warm, daemon=True).start()

    # v1.16.0: İdealData live WebSocket feed (background; app works without it)
    def _ideal_universe():
        try:
            return [q["symbol"] for q in scanner_service.top_volume_universe(150) if q.get("symbol")]
        except Exception:
            return []

    def _ideal_name(sym):
        try:
            return quote_service._name_map.get(sym) or None
        except Exception:
            return None

    # v1.18.0: tüm gün işlem kaydı (diskten yükle) + olay dedektörü
    try:
        trade_store.start()
    except Exception as e:
        logger.warning("trade store start failed: %s", e)
    try:
        ideal_feed.start(universe_fn=_ideal_universe, name_fn=_ideal_name)
        logger.info("İdealData feed started (user=%s, password_set=%s)", ideal_feed.user,
                    bool(ideal_feed._password()))
    except Exception as e:
        logger.warning("İdealData feed start failed: %s", e)
    try:
        get_index_impact(ideal_feed).start()   # v1.19.0 Hisselerin Endekse Etkisi
    except Exception as e:
        logger.warning("index impact start failed: %s", e)
    try:
        v120_hub.start(ideal_feed, trade_store, get_index_impact(ideal_feed))   # v1.20.0
    except Exception as e:
        logger.warning("v120 hub start failed: %s", e)
    try:
        for _k, _v in OP_NT_DEFAULTS.items():      # v1.21.0 operasyon bildirim türleri
            _v120mod.NTYPES.setdefault(_k, _v)
        op_engine.start(ideal_feed, trade_store, v120_hub, get_index_impact(ideal_feed))   # v1.21.0
    except Exception as e:
        logger.warning("operasyon start failed: %s", e)
    try:
        for _k, _v in K_NT_DEFAULTS.items():        # v1.22.0 kademe & şerit bildirim türleri
            _v120mod.NTYPES.setdefault(_k, _v)
        for _k, _v in M_NT_DEFAULTS.items():        # v1.23.0 maliyet yükselten kurumlar
            _v120mod.NTYPES.setdefault(_k, _v)
        for _k, _v in B_NT_DEFAULTS.items():        # v1.24.0 POC / alış ort. baskısı + hazır senaryolar
            _v120mod.NTYPES.setdefault(_k, _v)
        for _k, _v in D_NT_DEFAULTS.items():        # v1.25.0 derinlik alarmları
            _v120mod.NTYPES.setdefault(_k, _v)
        for _k, _v in V126_NT_DEFAULTS.items():     # v1.26.0 AKD taraması bildirimi
            _v120mod.NTYPES.setdefault(_k, _v)
        for _k, _v in V127_NT_DEFAULTS.items():     # v1.27.0 formasyon bildirimleri (motor tarafında varsayılan KAPALI)
            _v120mod.NTYPES.setdefault(_k, _v)
    except Exception as e:
        logger.warning("v122 ntypes failed: %s", e)

    def _on_trade_all(sym, k):
        try:
            event_detector.on_trade(sym, k)
        finally:
            v120_hub.on_trade(sym, k)
    try:
        trade_store.on_trade = _on_trade_all
        event_detector.start(ideal_feed, universe_fn=ideal_feed.equity_universe, prev_volume_fn=_prev_volume)
        v120_hub.olay_source = event_detector   # v1.20.1: piyasa olayları → bildirim akışı
    except Exception as e:
        logger.warning("event detector start failed: %s", e)
    try:
        k_engine.start(ideal_feed, trade_store, v120_hub, op_engine, event_detector)   # v1.22.0
    except Exception as e:
        logger.warning("v122 engine start failed: %s", e)
    try:
        m_engine.start(ideal_feed, trade_store, v120_hub, k_engine, event_detector)   # v1.23.0
    except Exception as e:
        logger.warning("v123 engine start failed: %s", e)
    try:
        b_engine.start(m_engine, k_engine, ideal_feed, v120_hub, event_detector, op_engine)   # v1.24.0
    except Exception as e:
        logger.warning("v124 engine start failed: %s", e)
    try:
        d_engine.start(ideal_feed, m_engine, b_engine, k_engine, v120_hub)   # v1.25.0
    except Exception as e:
        logger.warning("v125 engine start failed: %s", e)
    try:
        v126_engine.start(ideal_feed, m_engine, b_engine, d_engine, v120_hub)   # v1.26.0
    except Exception as e:
        logger.warning("v126 engine start failed: %s", e)
    try:
        v127_engine.start(ideal_feed, trade_store, v120_hub, lambda: _symbols)   # v1.27.0 (arka plan iş parçacığı)
    except Exception as e:
        logger.warning("v127 engine start failed: %s", e)
    try:
        v1271_akd_donem.start(ideal_feed, _akd_period_range)   # v1.27.1 (istek gelince arka planda toplu çekim)
    except Exception as e:
        logger.warning("v1271 start failed: %s", e)
    try:   # v1.30.0 Olay Listesi (ALARM): piyasa geneli olay motoru + olay alarmları (hepsi KAPALI) + tek seferlik "tüm bildirimler KAPALI" göçü
        for _k, _v in _v130.NT_DEFAULTS().items():
            _v120mod.NTYPES.setdefault(_k, _v)
        _v130.engine.start(b_engine, m_engine, v120_hub, ideal_feed)
        _v130.engine.migr = _v130.notif_all_off(v120_hub, _v120mod)
        logger.info("v130 notif migration: %s", _v130.engine.migr)
    except Exception as e:
        logger.warning("v130 start failed: %s", e)
    try:   # v1.31.0 🚀 TRENE ATLA — v130 göçünden SONRA kaydedilir (göç her açılışta varsayılanları KAPALI yapar; bu tür varsayılan AÇIK)
        _v120mod.NTYPES[_v131.NT] = _v131.NT_DEFAULT
        _v131.engine.start(_v130.engine, v120_hub, m_engine)
    except Exception as e:
        logger.warning("v131 start failed: %s", e)
    try:   # v1.32.0 D-A-K SKORLARI (Derinlik · AKD · Kademe Analizi) — tüm hisseler
        _v132.engine.start(ideal_feed, m_engine, v126_engine, d_engine)
    except Exception as e:
        logger.warning("v132 start failed: %s", e)
    try:   # v1.33.0 ALGO DESTEK / ALGO DİRENÇ — tüm hisselerin canlı derinliği
        _v133.engine.start(ideal_feed)
    except Exception as e:
        logger.warning("v133 start failed: %s", e)
    try:   # v1.34.0 ✅ AL BUNU · TAVAN ADAYI — mevcut sinyallerin VE-kapısı (al_bunu bildirimi cihazda varsayılan KAPALI)
        _v120mod.NTYPES[_v134.NT] = _v134.NT_DEFAULT
        _v134.engine.start(ideal_feed, m_engine, b_engine, v126_engine, _v132.engine, _v133.engine, _v131.engine, v120_hub)
    except Exception as e:
        logger.warning("v134 start failed: %s", e)
    try:
        _v136.engine.start(ideal_feed, v127_engine, trade_store)   # v1.36.0 ORDER BLOCK TARAMASI
    except Exception as e:
        logger.warning("v136 start failed: %s", e)
    try:   # v1.38.1 low_resource: istek iş parçacığı havuzunu sınırla (küçük VDS'de bağlam değişimi/yığılma azalır)
        from app import perf as _perf
        if _perf.LOW:
            import anyio.to_thread as _att
            _att.current_default_thread_limiter().total_tokens = int(_perf.CFG.get("threadpool", 16))
        logger.info("perf: low_resource=%s (%s)", _perf.LOW, _perf.CFG.get("auto_reason"))
    except Exception as e:
        logger.warning("perf init failed: %s", e)
    try:   # v1.37.0: ortak ilerleme kaydı — her motorun tur fonksiyonu (hata yalıtımlı; sarma başarısızsa motor aynen çalışır)
        from app import progress as _PG
        import app.v129 as _v129p
        for _o, _m, _k in ((_v132.engine, "compute", "skor"), (_v132.engine.pd, "run_pass", "dpage"),
                           (_v133.engine, "compute", "algo"), (_v134.engine, "step", "albunu"),
                           (m_engine, "_step", "maliyet"), (b_engine, "_step", "baski"), (v126_engine, "tarama", "akd"),
                           (v126_engine, "_check", "akd"), (_v130.engine, "_step_live", "olay"), (_v130.engine, "_ensure_offline", "olay"),
                           (k_engine, "compute", "kademe"), (op_engine, "compute", "op"), (_v131.engine, "step", "tren"),
                           (v120_hub, "_tick", "radar"), (_v129p, "birlesik", "eik")):
            try:
                _PG.wrap(_o, _m, _k)
            except Exception as _ex:
                logger.debug("progress wrap %s: %s", _k, _ex)
    except Exception as e:
        logger.warning("progress wrap failed: %s", e)
    try:
        tg_sender.start(v120_hub, ideal_feed, APP_VERSION)   # v1.38.0 Telegram bildirimleri
    except Exception as e:
        logger.warning("telegram start failed: %s", e)
    yield
    try:
        ideal_feed.stop()
    except Exception:
        pass
    try:
        trade_store.flush()
    except Exception:
        pass


APP_VERSION = "1.38.1"

app = FastAPI(title="BIST Analiz", version=APP_VERSION, lifespan=lifespan)


@app.get("/api/health")
def health():
    _, updated_at, meta = load_cache()
    return {
        "ok": True,
        "version": APP_VERSION,
        "symbols": len(_symbols),
        "cache_quotes": len(quote_service._cache or []),
        "symbols_updated_at": updated_at,
        "symbol_sources": (meta or {}).get("sources"),
        "rvol_def": RVOL_DEF,
        "rvol10_def": RVOL10_DEF,
        "rvol_defs": RVOL_DEFS,
        "rvol_tf_def": RVOL_TF_DEF,
        "rvol_tf_n": RVOL_TF_N,
        "rvol10_tf_n": RVOL10_TF_N,
        "tf_intervals": list(TF_INTERVALS),
        "scanner_universe_limit": SCANNER_UNIVERSE_LIMIT,
        "chart_presets": CHART_PRESETS,
        "chart_tf_doc": CHART_TF_DOC,
        "chart_source": CHART_SOURCE,
        "chart_source_label": CHART_SOURCE_LABEL,
        "chart_notes": CHART_NOTES,
        "chart_provider": chart_provider_info(),
        "candle_timeframes": {
            "1 dakika": "1m",
            "5 dakika": "5m",
            "15 dakika": "15m",
            "30 dakika": "30m",
            "1 saat": "60m",
            "2 saat": "resample 60m→2h",
            "4 saat": "resample 60m→4h",
            "1 gün": "1d",
            "1 hafta": "1wk",
            "1 ay": "1mo",
            "1 yıl": "resample 1mo→YS (yıllık mum)",
        },
        "notes_rules": NOTES_RULES,
        "signal_rules": SIGNAL_RULES,
        "volume_profile_method": VP_METHOD,
        "trade_plan_method": TRADE_PLAN_METHOD,
        "yahoo_intraday_notes": YAHOO_INTRADAY_NOTES,
        "alerts_spike": {
            "endpoint": "/api/alerts/spike?pct=1&interval=5m",
            "rule": "TF seçiliyse son mum close vs önceki mum close %; TF yoksa günlük quote",
            "poll_hint_sec": 20,
        },
        "alerts_rvol_spike": {
            "endpoint": "/api/alerts/rvol-spike?threshold=2&include_day=true&tfs=15m,1h",
            "rule": "Günlük RVOL ve/veya multi-TF RVOL ≥ eşik (baseline_mult ile)",
            "poll_hint_sec": 15,
        },
        "alerts_rvol10": {
            "endpoint": "/api/alerts/rvol10?threshold=2",
            "rule": "rvol10 ≥ eşik — hacim patlaması",
            "poll_hint_sec": 15,
        },
        "alerts_price": {
            "endpoint": "POST /api/alerts/price",
            "rule": "[{symbol, op:gte|lte, target}] vs quote cache",
        },
        "alerts_volume_break": {
            "endpoint": "/api/alerts/volume-break?limit=40&latest_only=true",
            "rule": "Hacimli Kırılım — ONLY if latest break == max-vol break AND price rising (bullish + close>prev_high + last≥prev_high); full liquid universe; no ranking-as-alarm",
            "poll_hint_sec": 15,
        },
        "support_resistance": {
            "endpoint": "/api/stocks/{symbol}/support-resistance?lookback=3",
            "method": SR_METHOD,
            "scope": "intraday_session_only",
        },
        "israrcilar": {
            "endpoint": "/api/scanners/israrcilar?limit=40&min_change=2&min_score=40",
            "method": PERSISTENCE_METHOD,
            "detail": "/api/stocks/{symbol}/persistence",
            "filter": "persistence_first; soft day floor ~+2%; TAVAN ≥+8 badge only",
        },
        "poc_migration": {
            "endpoint": "/api/stocks/{symbol}/poc-migration?mode=hourly",
            "method": POC_SHIFT_METHOD,
        },
        "va_migration": {
            "endpoint": "/api/stocks/{symbol}/va-migration?mode=hourly",
            "method": VA_MIG_METHOD,
        },
        "profile_bias": {
            "endpoint": "/api/stocks/{symbol}/profile-bias?mode=hourly",
            "method": PROFILE_BIAS_METHOD,
        },
        "high_breaks": {
            "endpoint": "/api/stocks/{symbol}/high-breaks",
            "method": HIGH_BREAK_METHOD,
        },
        "vwap_aort": {
            "endpoint": "/api/stocks/{symbol}/vwap",
            "method": VWAP_AORT_METHOD,
        },
        "parabolic": {
            "endpoint": "/api/scanners/parabolic?interval=15m&min_score=55",
            "method": PARABOLIC_METHOD,
        },
        "momentum": {
            "endpoint": "/api/scanners/momentum?window=5&min_score=50",
            "method": MOMENTUM_BURST_METHOD,
            "windows_min": [1, 3, 5, 10, 15],
            "alert": "/api/alerts/momentum?window=5&min_score=60",
            "poll_hint_sec": 40,
        },
        "poc_shift_scanner": {
            "endpoint": "/api/scanners/poc-shift?limit=30&mode=hourly",
        },
        "net_volume": {
            "endpoint": "/api/scanners/net-volume?limit=50&sort=net",
            "universe": SCANNER_UNIVERSE_LIMIT,
        },
        "trade_plans": {
            "endpoint": "/api/scanners/trade-plans?limit=120",
            "method": TRADE_PLAN_METHOD,
            "detail": "/api/stocks/{symbol}/trade-plan",
            "universe": SCANNER_UNIVERSE_LIMIT,
        },
        "live": {
            "quote_cache_ttl_open_sec": QUOTE_CACHE_TTL_OPEN,
            "quote_cache_ttl_closed_sec": QUOTE_CACHE_TTL_CLOSED,
            "sse": "/api/stream/quotes",
            "market_open": is_bist_session_open(),
            "session_hours": "10:00–18:10 Europe/Istanbul",
            "yahoo_delay_note": YAHOO_DELAY_NOTE,
            "frontend_refresh_open_sec": 4,
            "frontend_refresh_closed_sec": 60,
        },
        "cache_meta": quote_service.cache_meta(),
        "ideal": _ideal_brief(),
    }


def _ideal_brief() -> dict:
    try:
        st = ideal_feed.status()
        return {k: st.get(k) for k in ("state", "label", "connected", "logged_in", "healthy", "error",
                                         "last_msg_age_sec", "stores")}
    except Exception as e:
        return {"state": "error", "error": str(e)}


@app.get("/api/stocks")
def list_stocks(
    force: bool = Query(False, description="Cache'i atla, Yahoo'dan yenile"),
    refresh_symbols: bool = Query(False, description="Sembol listesini yenile"),
):
    global _symbols
    if refresh_symbols:
        _symbols = get_symbols(force_refresh=True)
        quote_service.set_name_map(_symbols)

    if not _symbols:
        _symbols = get_symbols()
        quote_service.set_name_map(_symbols)

    quotes, err = quote_service.fetch_all(_symbols, force=force)
    return {
        "count": len(quotes),
        "symbol_universe": len(_symbols),
        "error": err,
        "stocks": quotes,
        "rvol_defs": RVOL_DEFS,
        "cache_meta": quote_service.cache_meta(),
        "yahoo_delay_note": YAHOO_DELAY_NOTE,
    }


def _ensure_symbols():
    global _symbols
    if not _symbols:
        _symbols = get_symbols()
        quote_service.set_name_map(_symbols)


def _movers(kind: str, limit: int, force: bool):
    _ensure_symbols()
    quotes, err = quote_service.fetch_all(_symbols, force=force)
    items = quote_service.top_movers(quotes, kind, limit=limit)
    rvol_note = None
    if kind == "rvol":
        rvol_note = RVOL_DEF
    elif kind == "rvol10":
        rvol_note = RVOL10_DEF
    return {
        "kind": kind,
        "limit": limit,
        "count": len(items),
        "symbol_universe": len(_symbols),
        "quoted": len(quotes),
        "error": err,
        "stocks": items,
        "rvol_def": rvol_note,
    }


@app.get("/api/movers/gainers")
def movers_gainers(
    limit: int = Query(20, ge=1, le=100),
    force: bool = Query(False),
):
    return _movers("gainers", limit, force)


@app.get("/api/movers/losers")
def movers_losers(
    limit: int = Query(20, ge=1, le=100),
    force: bool = Query(False),
):
    return _movers("losers", limit, force)


@app.get("/api/movers/volume")
def movers_volume(
    limit: int = Query(20, ge=1, le=100),
    force: bool = Query(False),
):
    return _movers("volume", limit, force)


@app.get("/api/movers/rvol")
def movers_rvol(
    limit: int = Query(20, ge=1, le=100),
    force: bool = Query(False),
):
    return _movers("rvol", limit, force)


@app.get("/api/movers/rvol10")
def movers_rvol10(
    limit: int = Query(20, ge=1, le=100),
    force: bool = Query(False),
):
    return _movers("rvol10", limit, force)


@app.get("/api/stocks/{symbol}/rvol-tf")
def stock_rvol_tf(
    symbol: str,
    force: bool = Query(False),
):
    """Multi-timeframe RVOL for one symbol (last bar ÷ previous bar, same TF)."""
    data = scanner_service.stock_rvol_tf(symbol, force=force)
    if not data.get("rvol_tf") and not data.get("stock"):
        raise HTTPException(status_code=404, detail=f"Sembol bulunamadı: {symbol}")
    return data


@app.get("/api/stocks/{symbol}")
def stock_detail(
    symbol: str,
    period: str = Query(
        "1d",
        description="Mum boyutu: 1m,5m,15m,30m,1h,2h,4h,1d,1w,1mo,1y",
    ),
    interval: str | None = Query(
        None,
        description="Kullanılmıyor (compat); chart provider kendi TF seçer",
    ),
    include_rvol_tf: bool = Query(True, description="Çoklu TF RVOL özetini ekle"),
    include_notes: bool = Query(True, description="Kısa notları ekle"),
    include_high_breaks: bool = Query(True, description="Gün içi yüksek kırılımları ekle"),
    include_vwap: bool = Query(True, description="Seans VWAP/AORT ekle"),
    include_profile_bias: bool = Query(False, description="Profil bias skoru ekle (ağır)"),
):
    period = (period or "1d").lower()
    aliases = {"60m": "1h", "1wk": "1w", "1hafta": "1w"}
    period = aliases.get(period, period)
    if period not in ALLOWED_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz period. İzinli: {sorted(ALLOWED_PERIODS)}",
        )

    quote = quote_service.fetch_one(symbol)
    if not quote:
        cached = quote_service._cache or []
        sym = symbol.upper().replace(".IS", "")
        quote = next((q for q in cached if q["symbol"] == sym), None)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Sembol bulunamadı: {symbol}")

    preset = CHART_PRESETS.get(period, {})
    used_interval = interval or preset.get("interval")
    used_range = preset.get("period")
    candle = preset.get("candle") or used_interval
    resample = preset.get("resample")

    # Parallelize independent heavy work (history / rvol_tf / high_breaks / vwap / bias)
    history = None
    rvol_tf = None
    high_breaks = None
    vwap = None
    profile_bias = None

    def _hist():
        return quote_service.history(symbol, period=period, interval=interval)

    def _rvol():
        return scanner_service.stock_rvol_tf(symbol)

    def _hb():
        return compute_high_breaks(symbol, force=False)

    def _vw():
        return compute_vwap_aort(symbol, force=False)

    def _bias():
        return compute_profile_bias(symbol, mode="hourly", force=False)

    jobs = {"history": _hist}
    if include_rvol_tf:
        jobs["rvol_tf"] = _rvol
    if include_high_breaks:
        jobs["high_breaks"] = _hb
    if include_vwap:
        jobs["vwap"] = _vw
    if include_profile_bias:
        jobs["profile_bias"] = _bias

    results: dict = {}
    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        futs = {pool.submit(fn): name for name, fn in jobs.items()}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                results[name] = fut.result()
            except Exception as e:
                logger.warning("%s for %s: %s", name, symbol, e)
                results[name] = None

    history = results.get("history") or []
    rvol_tf = results.get("rvol_tf")
    high_breaks = results.get("high_breaks")
    vwap = results.get("vwap")
    profile_bias = results.get("profile_bias")

    notes = None
    if include_notes:
        try:
            notes = generate_notes_from_detail(quote, rvol_tf)
        except Exception as e:
            logger.warning("notes for %s: %s", symbol, e)
            notes = []

    chart_meta = quote_service.last_chart_meta()
    return {
        "stock": quote,
        "history": history,
        "period": period,
        "candle": candle,
        "resample": resample or chart_meta.get("resample"),
        "interval": used_interval,
        "lookback": used_range,
        "yahoo_period": used_range,  # legacy alias (=lookback)
        "yahoo_notes": YAHOO_INTRADAY_NOTES,
        "source": chart_meta.get("source") or CHART_SOURCE,
        "source_label": chart_meta.get("source_label") or CHART_SOURCE_LABEL,
        "chart_meta": chart_meta,
        "chart_notes": chart_meta.get("notes") or CHART_NOTES,
        "chart_tf_doc": CHART_TF_DOC,
        "notes": notes,
        "notes_rules": NOTES_RULES,
        "rvol_tf": (rvol_tf or {}).get("rvol_tf"),
        "rvol10_tf": (rvol_tf or {}).get("rvol10_tf"),
        "change_pct_tf": (rvol_tf or {}).get("change_pct_tf"),
        "rvol_tf_detail": (rvol_tf or {}).get("rvol_tf_detail"),
        "rvol_tf_def": RVOL_TF_DEF,
        "rvol_tf_n": RVOL_TF_N,
        "rvol10_tf_n": RVOL10_TF_N,
        "high_breaks": high_breaks,
        "vwap": vwap,
        "profile_bias": profile_bias,
    }


@app.get("/api/stocks/{symbol}/panel-extras")
def stock_panel_extras(
    symbol: str,
    force: bool = Query(False),
):
    """Bundled detail-panel extras: footprint + signal + rvol_tf + notes.

    Computed in parallel on the server so the UI can prefetch once instead of
    serial waterfalls for signal/footprint/rvol/notes. Chart history stays on
    /api/stocks/{symbol} with include_* flags off for a light payload.
    """
    quote = quote_service.fetch_one(symbol)
    if not quote:
        cached = quote_service._cache or []
        sym = symbol.upper().replace(".IS", "")
        quote = next((q for q in cached if q["symbol"] == sym), None)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Sembol bulunamadı: {symbol}")

    def _fp():
        return compute_volume_profile(symbol, date_str="today", force=force)

    def _rvol():
        return scanner_service.stock_rvol_tf(symbol, force=force)

    fp = None
    rvol_payload = None
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_fp = pool.submit(_fp)
        f_rv = pool.submit(_rvol)
        try:
            fp = f_fp.result()
        except Exception as e:
            logger.warning("panel footprint %s: %s", symbol, e)
            fp = {"error": str(e), "levels": []}
        try:
            rvol_payload = f_rv.result()
        except Exception as e:
            logger.warning("panel rvol_tf %s: %s", symbol, e)
            rvol_payload = {}

    # Signal reuses cached footprint + rvol (force=False after warm)
    try:
        signal = build_signal(symbol, force=False)
    except Exception as e:
        logger.warning("panel signal %s: %s", symbol, e)
        signal = {"error": str(e), "verdict": None}

    try:
        notes = generate_notes_from_detail(quote, rvol_payload)
    except Exception as e:
        logger.warning("panel notes %s: %s", symbol, e)
        notes = []

    buy_vol, sell_vol, net_vol = _extract_fp_volumes(fp, signal)

    # Trade plan (reuse warmed fp/signal; other inputs fetched inside)
    try:
        trade_plan = compute_trade_plan(
            symbol,
            force=False,
            quote=quote,
            footprint=fp,
            signal=signal,
        )
    except Exception as e:
        logger.warning("panel trade_plan %s: %s", symbol, e)
        trade_plan = {"direction": "WAIT", "error": str(e)}

    return {
        "symbol": quote.get("symbol") or symbol.upper().replace(".IS", ""),
        "stock": quote,
        "footprint": fp,
        "signal": signal,
        "notes": notes,
        "notes_rules": NOTES_RULES,
        "rvol_tf": (rvol_payload or {}).get("rvol_tf"),
        "rvol10_tf": (rvol_payload or {}).get("rvol10_tf"),
        "change_pct_tf": (rvol_payload or {}).get("change_pct_tf"),
        "rvol_tf_detail": (rvol_payload or {}).get("rvol_tf_detail"),
        "rvol_tf_def": RVOL_TF_DEF,
        "rvol_tf_n": RVOL_TF_N,
        "rvol10_tf_n": RVOL10_TF_N,
        "buy_vol": buy_vol,
        "sell_vol": sell_vol,
        "net_vol": net_vol,
        "buy_dominance_pct": (fp or {}).get("buy_dominance_pct")
            if (fp or {}).get("buy_dominance_pct") is not None
            else (signal or {}).get("buy_dominance_pct"),
        "sell_dominance_pct": (fp or {}).get("sell_dominance_pct")
            if (fp or {}).get("sell_dominance_pct") is not None
            else (signal or {}).get("sell_dominance_pct"),
        "trade_plan": trade_plan,
        "fp_source": (fp or {}).get("fp_source") or "tahmini",
        "fp_source_label": (fp or {}).get("fp_source_label") or "tahmini (OHLCV)",
        "price_source": (quote or {}).get("price_source") or "yahoo",
    }


def generate_notes_from_detail(quote, rvol_tf_payload):
    from app.analysis import generate_notes

    payload = rvol_tf_payload or {}
    return generate_notes(
        quote,
        rvol_tf=payload.get("rvol_tf"),
        change_pct_tf=payload.get("change_pct_tf"),
    )


@app.get("/api/stocks/{symbol}/notes")
def stock_notes(
    symbol: str,
    force: bool = Query(False),
):
    """Türkçe önemli kısa notlar (olgusal, 2–5 madde)."""
    data = build_stock_notes(symbol, force=force)
    if data.get("error") == "not_found":
        raise HTTPException(status_code=404, detail=f"Sembol bulunamadı: {symbol}")
    return data


@app.get("/api/stocks/{symbol}/signal")
def stock_signal(
    symbol: str,
    force: bool = Query(False),
):
    """AL / SAT / TUT model sinyali + Türkçe analiz (yatırım tavsiyesi değildir)."""
    data = build_signal(symbol, force=force)
    if data.get("error") == "not_found":
        raise HTTPException(status_code=404, detail=f"Sembol bulunamadı: {symbol}")
    return data


@app.get("/api/stocks/{symbol}/volume-profile")
@app.get("/api/stocks/{symbol}/footprint")
def stock_volume_profile(
    symbol: str,
    date: str = Query("today", description="Seans günü YYYY-MM-DD veya today"),
    force: bool = Query(False),
):
    """Günlük footprint / hacim profili — seans günü 1m (yoksa 5m) volume-at-price."""
    data = compute_volume_profile(symbol, date_str=date, force=force)
    if data.get("error") == "not_found":
        raise HTTPException(status_code=404, detail=f"Sembol bulunamadı: {symbol}")
    return data



@app.get("/api/stocks/{symbol}/trade-plan")
def stock_trade_plan(
    symbol: str,
    force: bool = Query(False),
):
    """Intraday işlem planı: giriş / stop / TP1 / TP2 (matematiksel yapı)."""
    _ensure_symbols()
    try:
        plan = compute_trade_plan(symbol, force=force)
    except Exception as e:
        logger.exception("trade-plan %s", symbol)
        raise HTTPException(status_code=500, detail=str(e)) from e
    return plan


@app.get("/api/alerts/spike")
def alerts_spike(
    pct: float = Query(2.0, ge=0.1, le=50.0, description="Ani artış eşiği % (ör. 2)"),
    interval: str | None = Query(
        None,
        description="Tek TF (1m/5m/15m/…). Verilirse SADECE o TF son mum % kullanılır — asla 15m’ye düşmez",
    ),
    tfs: str | None = Query(
        None,
        description="Virgülle TF listesi. interval ile birlikte birleştirilir",
    ),
    force: bool = Query(False),
):
    """Ani Artış alarmı.

    Örnek: `?pct=1&interval=5m` → son 5dk mumunun change_pct ≥ +1
    (son bar close vs önceki bar close). TF seçiliyken günlük quote değişimi
    kullanılmaz. TF yoksa günlük seans change_pct taranır.
    """
    _ensure_symbols()
    # Warm quotes so volume universe is fresh
    quote_service.fetch_all(_symbols, force=force)

    tf_list: list[str] = []
    if interval:
        tf_list.append(interval.strip().lower())
    if tfs:
        tf_list.extend(t.strip().lower() for t in tfs.split(",") if t.strip())
    # dedupe preserve order
    seen_tf: set[str] = set()
    ordered: list[str] = []
    for t in tf_list:
        if t not in seen_tf:
            seen_tf.add(t)
            ordered.append(t)
    tf_list = ordered

    bad = [t for t in tf_list if t not in TF_INTERVALS]
    if bad:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz TF: {bad}. İzinli: {list(TF_INTERVALS)}",
        )

    return scanner_service.spike_alerts(
        pct=pct,
        intervals=tf_list,
        force=force,
    )



@app.get("/api/scanners/net-volume")
def scanners_net_volume(
    limit: int = Query(50, ge=1, le=1000),
    sort: str = Query(
        "net",
        description="net|buy_dom|buy|sell|volume|change",
    ),
    force: bool = Query(False),
):
    """Net hacim: günlük footprint alış/satış toplamları (top ~150 hacimli).

    buy_vol, sell_vol, net_vol, buy_dominance_pct — alıcı hakim isimleri bulmak için.
    """
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=False)
    return scanner_service.net_volume(limit=limit, sort=sort, force=force)


@app.get("/api/scanners/steady-risers")
def scanners_steady_risers(
    interval: str = Query("15m", description="TF: 1m,5m,15m,30m,1h,2h,4h,1d,1w"),
    limit: int = Query(30, ge=1, le=100),
    min_change: float | None = Query(None, description="Min net %% (boş=TF varsayılanı)"),
    green_ratio: float = Query(0.65, ge=0.5, le=1.0),
    force: bool = Query(False),
):
    interval = (interval or "15m").lower()
    if interval not in TF_INTERVALS:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz interval. İzinli: {list(TF_INTERVALS)}",
        )
    _ensure_symbols()
    # Ensure quotes warm for universe
    quote_service.fetch_all(_symbols, force=False)
    return scanner_service.steady_risers(
        interval=interval,
        limit=limit,
        min_change=min_change,
        green_ratio=green_ratio,
        force=force,
    )


@app.get("/api/scanners/fast-movers")
def scanners_fast_movers(
    interval: str = Query("5m", description="TF: 1m,5m,15m,30m,1h,2h,4h,1d,1w"),
    limit: int = Query(30, ge=1, le=100),
    force: bool = Query(False),
):
    interval = (interval or "5m").lower()
    if interval not in TF_INTERVALS:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz interval. İzinli: {list(TF_INTERVALS)}",
        )
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=False)
    return scanner_service.fast_movers(limit=limit, force=force, interval=interval)


@app.get("/api/scanners/rvol-tf")
def scanners_rvol_tf(
    limit: int = Query(40, ge=1, le=80),
    force: bool = Query(False),
):
    """RVOL çoklu TF tablosu — top hacimli isimler."""
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=False)
    return scanner_service.rvol_multi_tf_table(limit=limit, force=force)


@app.get("/api/alerts/rvol-spike")
def alerts_rvol_spike(
    threshold: float = Query(2.0, ge=0.5, le=50.0, description="RVOL eşiği (×)"),
    baseline_mult: float = Query(1.0, ge=0.5, le=5.0, description="Eşik çarpanı (baseline)"),
    include_day: bool = Query(True, description="Günlük RVOL dahil"),
    interval: str | None = Query(None, description="Tek TF"),
    tfs: str | None = Query(None, description="Virgülle TF listesi"),
    force: bool = Query(False),
):
    """RVOL ani sıçrama alarmı — gün / multi-TF RVOL ≥ eşik."""
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=force)
    tf_list: list[str] = []
    if interval:
        tf_list.append(interval.strip().lower())
    if tfs:
        tf_list.extend(t.strip().lower() for t in tfs.split(",") if t.strip())
    seen: set[str] = set()
    ordered: list[str] = []
    for t in tf_list:
        if t not in seen:
            seen.add(t)
            ordered.append(t)
    bad = [t for t in ordered if t not in TF_INTERVALS]
    if bad:
        raise HTTPException(status_code=400, detail=f"Geçersiz TF: {bad}. İzinli: {list(TF_INTERVALS)}")
    return scanner_service.rvol_spike_alerts(
        threshold=threshold,
        baseline_mult=baseline_mult,
        intervals=ordered,
        include_day=include_day,
        force=force,
    )


@app.get("/api/alerts/rvol10")
def alerts_rvol10(
    threshold: float = Query(2.0, ge=0.5, le=50.0, description="RVOL(10) eşiği"),
    force: bool = Query(False),
):
    """Hacim patlaması alarmı — rvol10 ≥ eşik."""
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=force)
    return scanner_service.rvol10_blast_alerts(threshold=threshold, force=force)



@app.get("/api/alerts/volume-break")
def alerts_volume_break(
    limit: int = Query(40, ge=1, le=80, description="Döndürülecek alarm sayısı"),
    min_breaks: int = Query(1, ge=1, le=50, description="Minimum kırılım sayısı (≥1)"),
    latest_only: bool = Query(
        True,
        description="Zorunlu: son kırılım = max hacimli (False gönderilse bile uygulanır)",
    ),
    force: bool = Query(False),
):
    """Hacimli Kırılım alarmı (v1.14.2).

    Yalnızca şu üçü birden doğruysa tetiklenir:
    (1) seans içi ≥1 running day-high kırılımı;
    (2) son kırılım = günün max-hacimli kırılımı;
    (3) fiyat yükselir: close>open + close>önceki yüksek + last≥kırılan seviye (prev_high).
    Tüm likit evren taranır; historical ranking alarm değildir.
    """
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=False)
    return scanner_service.volume_break_alerts(
        limit=limit,
        min_breaks=min_breaks,
        latest_only=True,  # required
        force=force,
    )


@app.post("/api/alerts/price")
def alerts_price(payload: dict = Body(...)):
    """Fiyat hedef alarmı kontrolü.

    Body: {"alerts": [{"symbol":"THYAO","op":"gte","target":350.0,"id":"..."}, ...]}
    """
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=False)
    alerts = payload.get("alerts") if isinstance(payload, dict) else None
    if alerts is None and isinstance(payload, list):
        alerts = payload
    if not isinstance(alerts, list):
        raise HTTPException(status_code=400, detail="alerts listesi gerekli")
    return scanner_service.check_price_alerts(alerts)



def _extract_fp_volumes(fp, signal=None):
    """Resolve buy/sell/net from footprint aliases, signal totals, or level sums.

    Never treat 0 as missing (avoid `or` falsy trap). Prefer explicit aliases
    buy_vol/sell_vol/net_vol, then buy_volume_total*, then signal, then Σ levels.
    """
    fp = fp or {}
    signal = signal or {}

    def _pick(*vals):
        for v in vals:
            if v is None:
                continue
            try:
                return int(round(float(v)))
            except (TypeError, ValueError):
                continue
        return None

    levels = fp.get("levels") or []
    level_buy = level_sell = None
    if levels:
        level_buy = int(sum(int(l.get("buy_volume") or 0) for l in levels))
        level_sell = int(sum(int(l.get("sell_volume") or 0) for l in levels))

    buy = _pick(
        fp.get("buy_vol"),
        fp.get("buy_volume_total"),
        signal.get("buy_vol"),
        signal.get("buy_volume_total"),
        level_buy,
    )
    sell = _pick(
        fp.get("sell_vol"),
        fp.get("sell_volume_total"),
        signal.get("sell_vol"),
        signal.get("sell_volume_total"),
        level_sell,
    )
    net = _pick(
        fp.get("net_vol"),
        fp.get("net_volume_total"),
        signal.get("net_vol"),
        signal.get("net_volume_total"),
    )
    if net is None and buy is not None and sell is not None:
        net = int(buy) - int(sell)
    return buy, sell, net


@app.get("/api/stocks/{symbol}/support-resistance")
def stock_support_resistance(
    symbol: str,
    interval: str = Query("session", description="Seans içi (interval yok sayılır — yalnızca bugün)"),
    lookback: int = Query(3, ge=2, le=10),
    max_levels: int = Query(12, ge=2, le=30),
    force: bool = Query(False),
):
    """Otomatik destek-direnç — yalnızca seans içi 1m/5m swing + hacim kümesi."""
    return detect_support_resistance(
        symbol, interval=interval, lookback=lookback, max_levels=max_levels, force=force
    )


@app.get("/api/stocks/{symbol}/persistence")
def stock_persistence(
    symbol: str,
    force: bool = Query(False),
):
    """Israrcılar detayı — dip→geri alma olayları ve ana alım seviyesi."""
    return compute_persistence(symbol, force=force)


@app.get("/api/scanners/israrcilar")
def scanners_israrcilar(
    limit: int = Query(40, ge=1, le=80),
    min_change: float = Query(2.0, ge=0, le=20, description="Yumuşak gün-% tabanı (gürültü); sert ≥5/≥8 kapısı değil"),
    min_score: float = Query(40.0, ge=0, le=100, description="Min israr skoru"),
    include_near: bool = Query(True, description="near_tavan rozetli isimleri dahil et (filtre değil)"),
    force: bool = Query(False),
):
    """Israrcılar — persistence-first tarayıcı (TAVAN rozeti ≥+%8, filtre değil)."""
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=False)
    return scanner_service.israrcilar_scanner(
        limit=limit,
        min_change=min_change,
        min_score=min_score,
        include_near=include_near,
        force=force,
    )


@app.get("/api/stocks/{symbol}/poc-migration")
def stock_poc_migration(
    symbol: str,
    mode: str = Query("hourly", description="hourly|rolling"),
    force: bool = Query(False),
):
    """Footprint POC kayması — saatlik / rolling pencereler."""
    return compute_poc_migration(symbol, mode=mode, force=force)


@app.get("/api/stocks/{symbol}/va-migration")
def stock_va_migration(
    symbol: str,
    mode: str = Query("hourly", description="hourly|rolling"),
    force: bool = Query(False),
):
    """Value area (VAH/VAL) göçü — oklar ve delta."""
    return compute_va_migration(symbol, mode=mode, force=force)



@app.get("/api/stocks/{symbol}/profile-bias")
def stock_profile_bias(
    symbol: str,
    mode: str = Query("hourly", description="hourly|rolling"),
    force: bool = Query(False),
):
    """POC + VA göçünden boğa/ayı skor (0–100) + Türkçe yorum."""
    return compute_profile_bias(symbol, mode=mode, force=force)


@app.get("/api/stocks/{symbol}/high-breaks")
def stock_high_breaks(
    symbol: str,
    force: bool = Query(False),
):
    """Gün içi running day-high kırılımları (1m bar)."""
    return compute_high_breaks(symbol, force=force)


@app.get("/api/stocks/{symbol}/vwap")
def stock_vwap(
    symbol: str,
    force: bool = Query(False),
):
    """Seans VWAP + AORT (ağırlıklı ortalama) ve last mesafesi."""
    return compute_vwap_aort(symbol, force=force)


@app.get("/api/scanners/high-breaks")
def scanners_high_breaks(
    limit: int = Query(30, ge=1, le=80),
    min_breaks: int = Query(1, ge=0, le=500),
    force: bool = Query(False),
):
    """En çok gün-içi yüksek kırılımı yapan hisseler (hacim evreni)."""
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=False)
    return scanner_service.high_breaks_scanner(
        limit=limit, min_breaks=min_breaks, force=force
    )


@app.get("/api/stocks/{symbol}/parabolic")
def stock_parabolic(
    symbol: str,
    interval: str = Query("15m"),
    force: bool = Query(False),
):
    """Tek hisse parabolik yükseliş skoru."""
    interval = (interval or "15m").lower()
    if interval not in TF_INTERVALS:
        raise HTTPException(status_code=400, detail=f"Geçersiz interval: {list(TF_INTERVALS)}")
    return compute_parabolic_score(symbol, interval=interval, force=force)


@app.get("/api/scanners/parabolic")
def scanners_parabolic(
    interval: str = Query("15m"),
    limit: int = Query(40, ge=1, le=100),
    min_score: float = Query(55.0, ge=0, le=100),
    force: bool = Query(False),
):
    interval = (interval or "15m").lower()
    if interval not in TF_INTERVALS:
        raise HTTPException(status_code=400, detail=f"Geçersiz interval: {list(TF_INTERVALS)}")
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=False)
    return scanner_service.parabolic_scanner(
        interval=interval, limit=limit, min_score=min_score, force=force
    )


@app.get("/api/stocks/{symbol}/momentum")
def stock_momentum(
    symbol: str,
    window: int = Query(5, description="Pencere (dakika): 1,3,5,10,15"),
    green_n: int = Query(3, ge=1, le=10, description="Son N mum yeşil eşiği"),
    force: bool = Query(False),
):
    """Tek hisse Momentumlu Hızlanış skoru."""
    return compute_momentum_burst(symbol, window_min=window, force=force, green_n=green_n)


@app.get("/api/scanners/momentum")
def scanners_momentum(
    window: int = Query(5, description="Pencere (dakika): 1,3,5,10,15"),
    limit: int = Query(40, ge=1, le=100),
    min_score: float = Query(50.0, ge=0, le=100),
    min_pct: float | None = Query(None, description="Min window % (None=otomatik)"),
    require_accel: bool = Query(True, description="accel_% > 0 zorunlu"),
    green_n: int = Query(3, ge=1, le=10),
    force: bool = Query(False),
):
    """Momentumlu Hızlanış tarayıcı — son W dk aşırı yukarı momentum (nadir fırlayış)."""
    from app.features import MOMENTUM_WINDOWS
    w = int(window or 5)
    if w not in MOMENTUM_WINDOWS:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz window. İzinli: {list(MOMENTUM_WINDOWS)}",
        )
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=False)
    return scanner_service.momentum_burst_scanner(
        window_min=w,
        limit=limit,
        min_score=min_score,
        min_window_pct=min_pct,
        require_accel=require_accel,
        green_n=green_n,
        force=force,
    )


@app.get("/api/alerts/momentum")
def alerts_momentum(
    window: int = Query(5, description="Pencere (dakika): 1,3,5,10,15"),
    min_score: float = Query(60.0, ge=0, le=100),
    min_pct: float | None = Query(None, description="Min window % (None=nadir eşik)"),
    require_accel: bool = Query(True),
    green_n: int = Query(3, ge=1, le=10),
    limit: int = Query(40, ge=1, le=80),
    force: bool = Query(False),
):
    """Momentumlu Hızlanış alarmı — nadir ani yukarı fırlayış (SW poll)."""
    from app.features import MOMENTUM_WINDOWS
    w = int(window or 5)
    if w not in MOMENTUM_WINDOWS:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz window. İzinli: {list(MOMENTUM_WINDOWS)}",
        )
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=False)
    return scanner_service.momentum_burst_alerts(
        window_min=w,
        min_score=min_score,
        min_window_pct=min_pct,
        require_accel=require_accel,
        green_n=green_n,
        limit=limit,
        force=force,
    )


@app.get("/api/scanners/poc-shift")
def scanners_poc_shift(
    limit: int = Query(30, ge=1, le=80),
    mode: str = Query("hourly"),
    force: bool = Query(False),
):
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=False)
    return scanner_service.poc_shift_scanner(limit=limit, mode=mode, force=force)



@app.get("/api/scanners/trade-plans")
def scanners_trade_plans(
    limit: int = Query(120, ge=1, le=200),
    actionable_only: bool = Query(False, description="Sadece LONG/SHORT (WAIT hariç)"),
    force: bool = Query(False),
):
    """İşlem Planları tarayıcı — likit evrende LONG/SHORT/WAIT planları.

    Varsayılan sıra: aksiyonel (LONG/SHORT) + |entry_distance_pct| artan.
    """
    _ensure_symbols()
    quote_service.fetch_all(_symbols, force=False)
    return scanner_service.trade_plans_scanner(
        limit=limit,
        actionable_only=actionable_only,
        force=force,
    )


@app.get("/api/live/meta")
def live_meta():
    """Canlı yenileme ipuçları + Yahoo gecikme notu."""
    _ensure_symbols()
    meta = quote_service.cache_meta()
    return {
        **meta,
        "version": APP_VERSION,
        "sse": "/api/stream/quotes",
        "yahoo_intraday_notes": YAHOO_INTRADAY_NOTES,
        "chart_source": CHART_SOURCE,
        "chart_source_label": CHART_SOURCE_LABEL,
        "chart_notes": CHART_NOTES,
    }


@app.get("/api/stream/quotes")
async def stream_quotes(
    compact: bool = Query(True, description="Sadece fiyat alanları"),
):
    """SSE: quote tick push (açıkken ~6s, kapalı ~60s). Yahoo gecikmeli olabilir."""
    import asyncio
    import json
    import time as _time

    _ensure_symbols()

    async def event_gen():
        hello = {
            "type": "hello",
            "market_open": quote_service.is_market_open(),
            "yahoo_delay_note": YAHOO_DELAY_NOTE,
            "ttl_open": QUOTE_CACHE_TTL_OPEN,
            "ttl_closed": QUOTE_CACHE_TTL_CLOSED,
        }
        yield f"event: hello\ndata: {json.dumps(hello, ensure_ascii=False)}\n\n"
        while True:
            try:
                quotes, err = await asyncio.to_thread(
                    quote_service.fetch_all, _symbols, False
                )
                open_ = quote_service.is_market_open()
                if compact:
                    ticks = [
                        {
                            "symbol": q["symbol"],
                            "price": q.get("price"),
                            "change_pct": q.get("change_pct"),
                            "volume": q.get("volume"),
                            "rvol": q.get("rvol"),
                            "rvol10": q.get("rvol10"),
                            "updated": q.get("updated"),
                            "market_state": q.get("market_state"),
                            "price_source": q.get("price_source"),
                        }
                        for q in quotes
                    ]
                else:
                    ticks = quotes
                payload = {
                    "type": "quotes",
                    "count": len(ticks),
                    "error": err,
                    "market_open": open_,
                    "ts": _time.time(),
                    "cache_meta": quote_service.cache_meta(),
                    "stocks": ticks,
                }
                yield f"event: quotes\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
                delay = QUOTE_CACHE_TTL_OPEN if open_ else QUOTE_CACHE_TTL_CLOSED
                # Open: poll as fast as cache TTL; closed: slower meta refresh
                await asyncio.sleep(max(3.0 if open_ else 15.0, delay))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("SSE quotes: %s", e)
                err_payload = json.dumps({"error": str(e)}, ensure_ascii=False)
                yield f"event: error\ndata: {err_payload}\n\n"
                await asyncio.sleep(15)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



# ======================= İdealData canlı (v1.16.0) =======================

def _sort_rows(rows: list[dict], key: str, desc: bool = True) -> list[dict]:
    return sorted(rows, key=lambda r: (r.get(key) is None, -(r.get(key) or 0) if desc else (r.get(key) or 0)))


@app.post("/api/ideal/reconnect")
def ideal_reconnect():
    """v1.27.2: ↻ button — wake a stalled İdealData feed (no-op when healthy, ≤1/60 s)."""
    return ideal_feed.request_reconnect("manual")


_CRED_HITS: list = []


@app.get("/api/ideal/account")
def ideal_account():
    """v1.34.1: hesap bilgisi (şifre asla dönmez)."""
    import importlib as _il; _if = _il.import_module("app.ideal_feed")
    return {"user": ideal_feed.user, "saved_in_app": _if.cred_saved(), "state": ideal_feed.state,
            "error": ideal_feed.error}


@app.post("/api/ideal/credentials")
async def ideal_credentials(request: Request):
    """v1.34.1: İdealData kullanıcı adı/şifre kaydet + hemen yeniden bağlan (10 dk'da en çok 5 deneme)."""
    import time as _t
    try:
        body = await request.json()
    except Exception:
        body = {}
    user = str((body or {}).get("user") or "").strip()
    pw = str((body or {}).get("password") or "")
    if not user or not pw or len(user) > 64 or len(pw) > 128:
        return JSONResponse({"ok": False, "error": "Kullanıcı adı ve şifre gerekli"}, status_code=400)
    now = _t.time()
    _CRED_HITS[:] = [x for x in _CRED_HITS if now - x < 600]
    if len(_CRED_HITS) >= 5:
        return JSONResponse({"ok": False, "error": "Çok fazla deneme — birkaç dakika sonra tekrar deneyin",
                             "retry_in": round(600 - (now - _CRED_HITS[0]))}, status_code=429)
    _CRED_HITS.append(now)
    return ideal_feed.set_credentials(user, pw)


@app.get("/api/ideal/status")
def ideal_status():
    """İdealData bağlantı durumu (şifre asla dönmez)."""
    return ideal_feed.status()


@app.get("/api/ideal/pressure")
def ideal_pressure(
    limit: int = Query(1000, ge=1, le=1500),
    sort: str = Query("pressure_pct", description="pressure_pct|book_pressure_pct|imbalance_lot|bid_lot|ask_lot|change_pct"),
    asc: bool = Query(False),
):
    """Derinlik Baskısı — ilk 25 kademe alış lot ÷ (alış+satış) %."""
    rows = ideal_feed.pressure_ranking()
    key = sort if sort in ("pressure_pct", "book_pressure_pct", "imbalance_lot", "bid_lot", "ask_lot",
                           "change_pct", "volume", "spread") else "pressure_pct"
    rows = _sort_rows(rows, key, desc=not asc)
    total = len(rows)
    st = ideal_feed.status()
    return {
        "kind": "ideal_pressure", "count": min(total, limit), "total": total, "sort": key,
        "stocks": rows[:limit], "feed": {k: st[k] for k in ("state", "label", "healthy", "error")},
        "scan": st.get("scan"),
        "coverage": {"universe": st.get("scan", {}).get("universe"), "with_data": total,
                     "note": f"İdealData canlı derinlik · ilk 25 kademe · {total} hisse (tarama döngüsü ~90 sn)"},
        "updated": st.get("now"),
    }


@app.get("/api/ideal/moneyflow")
def ideal_moneyflow(
    limit: int = Query(1000, ge=1, le=1500),
    sort: str = Query("net_tl", description="net_tl|inflow_tl|outflow_tl|buy_dominance_pct|net_lot|change_pct"),
    asc: bool = Query(False),
):
    """Para Akışı — Y38 kademe analizi: Σ fiyat × alış lot (giriş) − Σ fiyat × satış lot (çıkış)."""
    rows = ideal_feed.moneyflow_ranking()
    key = sort if sort in ("net_tl", "inflow_tl", "outflow_tl", "buy_dominance_pct", "net_lot",
                           "change_pct", "total_lot", "turnover") else "net_tl"
    rows = _sort_rows(rows, key, desc=not asc)
    total = len(rows)
    st = ideal_feed.status()
    return {
        "kind": "ideal_moneyflow", "count": min(total, limit), "total": total, "sort": key,
        "stocks": rows[:limit], "feed": {k: st[k] for k in ("state", "label", "healthy", "error")},
        "coverage": {"universe": st.get("scan", {}).get("universe"), "with_data": total,
                     "note": f"İdealData canlı para akışı (fiyat kademe analizi) · {total} hisse"},
        "updated": st.get("now"),
    }


@app.get("/api/ideal/institutions")
def ideal_institutions(
    limit: int = Query(300, ge=1, le=500),
    sort: str = Query("net_tl", description="net_tl|pnl_tl|buy_tl|sell_tl|symbols|pnl_pct"),
    asc: bool = Query(False),
    symbol: str | None = Query(None, description="Verilirse o hissenin AKD listesi"),
):
    """Kurumlar — AKD (TUM net lot + maliyet) tüm taranan hisselerde kurum bazında toplam; K/Z = net × (son − maliyet)."""
    if symbol:
        v = ideal_feed.symbol_view(symbol)
        return {"symbol": v["symbol"], "brokers": v["brokers"]}
    rows = ideal_feed.institutions()
    key = sort if sort in ("net_tl", "pnl_tl", "buy_tl", "sell_tl", "symbols", "pnl_pct",
                           "buy_symbols", "sell_symbols") else "net_tl"
    rows = _sort_rows(rows, key, desc=not asc)
    st = ideal_feed.status()
    cov = ideal_feed.akd_coverage()
    for r in rows:
        r.setdefault("symbol", r["broker"])  # UI table key
    return {
        "kind": "ideal_institutions", "count": min(len(rows), limit), "total": len(rows), "sort": key,
        "stocks": rows[:limit], "akd_symbols": cov,
        "feed": {k: st[k] for k in ("state", "label", "healthy", "error")},
        "coverage": {"universe": st.get("scan", {}).get("universe"), "with_data": cov,
                     "note": f"İdealData AKD · {cov} hisse tarandı · K/Z = net lot × (son − maliyet), tahmini"},
        "updated": st.get("now"),
    }


@app.post("/api/ideal/select/{symbol}")
def ideal_select(symbol: str):
    """Detay panelinde açılan hisseyi öncelikli abone et (derinlik + kademe + AKD hemen)."""
    return ideal_feed.select(symbol)


# ---------------------------------------------------------------- v1.17.0 --
def _ist_today():
    from datetime import datetime as _dt
    from zoneinfo import ZoneInfo as _Z
    return _dt.now(_Z("Europe/Istanbul")).date()


def _prev_weekday(d):
    from datetime import timedelta as _td
    while d.weekday() >= 5:
        d = d - _td(days=1)
    return d


def _akd_period_range(period: str, d_from: str | None, d_to: str | None) -> tuple[str, str, str]:
    """period → (yyyymmdd, yyyymmdd, label)."""
    from datetime import date as _date, timedelta as _td
    from datetime import datetime as _dt
    from zoneinfo import ZoneInfo as _Z

    now = _dt.now(_Z("Europe/Istanbul"))
    end = now.date()
    # before the opening auction there is no AKD for today → last trading day
    if end.weekday() >= 5 or (now.hour * 60 + now.minute) < 9 * 60 + 55:
        end = _prev_weekday(end - _td(days=1)) if end.weekday() < 5 else _prev_weekday(end)
    period = (period or "daily").lower()

    def _p(s):
        return _date.fromisoformat(s[:10]) if s and "-" in s else _dt.strptime(s, "%Y%m%d").date()

    if period in ("custom", "date", "tarih") and d_from:
        a = _p(d_from)
        b = _p(d_to) if d_to else a
        if b < a:
            a, b = b, a
        label = a.strftime("%d.%m.%Y") + ("" if a == b else " – " + b.strftime("%d.%m.%Y"))
    elif period in ("weekly", "haftalik"):
        a, b, label = end - _td(days=6), end, "HAFTALIK"
    elif period in ("monthly", "aylik"):
        a, b, label = end - _td(days=30), end, "AYLIK"
    elif period in ("3m", "quarterly", "3aylik"):
        a, b, label = end - _td(days=91), end, "3 AYLIK"
    else:
        a = b = end
        label = "BUGÜN" if end == now.date() else end.strftime("%d.%m.%Y")
    return a.strftime("%Y%m%d"), b.strftime("%Y%m%d"), label


_PROBE_TOKEN_FILE = Path(__file__).resolve().parent.parent / "data" / ".probe_token"


def _probe_token() -> str:
    import secrets
    try:
        t = _PROBE_TOKEN_FILE.read_text().strip()
        if t:
            return t
    except Exception:
        pass
    t = secrets.token_hex(16)
    _PROBE_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PROBE_TOKEN_FILE.write_text(t)
    try:
        _PROBE_TOKEN_FILE.chmod(0o600)
    except Exception:
        pass
    return t


@app.post("/api/ideal/debug/probe")
def ideal_probe(payload: dict = Body(...)):
    """Geliştirici: ham İdealData isteği (token korumalı, yanıtlar maskeli)."""
    if payload.get("token") != _probe_token():
        raise HTTPException(403, "forbidden")
    if "sub_extra" in payload:
        ideal_feed.sub_extra = [str(x).upper() for x in (payload.get("sub_extra") or [])]
    if payload.get("tick_counts"):
        return {"ticks": dict(ideal_feed.tick_counts), "drn_ops": dict(ideal_feed.drn_ops),
                "msgs": dict(ideal_feed.msg_counts)}
    frames = payload.get("frames") or []
    return {"replies": ideal_feed.probe(frames, payload.get("typ") or "", payload.get("contains"),
                                        int(payload.get("need") or 1), float(payload.get("timeout") or 6.0))}


# ------------------------------------------------------------------ v1.18.0
def _tr_fold(s: str) -> str:
    return (s or "").upper().replace("İ", "I").replace("Ş", "S").replace("Ğ", "G").replace("Ü", "U").replace("Ö", "O").replace("Ç", "C").replace("ı", "I")


@app.get("/api/live/stats")
def live_stats():
    return {"trades": trade_store.stats(), "events": {"counts": dict(event_detector.counts), "loops": event_detector.loops,
            "day": event_detector.day, "dipzirve": len(event_detector.dipzirve)},
            "stream_all": bool(ideal_feed.sub_extra), "stream_symbols": len(ideal_feed.sub_extra),
            "akd_coverage": ideal_feed.akd_coverage(), "version": APP_VERSION,
            "feed": {"connected": bool(ideal_feed.connected), "logged_in": bool(ideal_feed.logged_in),
                     "last_msg_age_sec": (round(time.time() - ideal_feed.last_msg_time, 1) if ideal_feed.last_msg_time else None),
                     "pid": os.getpid()},
            "history_source": "İdealData geçmiş işlem isteği sunmuyor (REQ_DERINLIK yalnızca son 50); kayıt canlı akıştan"}


@app.get("/api/live/movers")
def live_movers():
    rows = ideal_feed.movers()
    pos = sum(1 for r in rows if r["c"] > 0)
    neg = sum(1 for r in rows if r["c"] < 0)
    return {"count": len(rows), "positive": pos, "negative": neg, "neutral": len(rows) - pos - neg,
            "rows": rows, "source_label": "İdealData canlı", "updated": _ist_now_str()}


@app.get("/api/live/events")
def live_events(kind: str = "all", q: str = "", syms: str = "", since_id: int = 0, limit: int = 300):
    sl = [x.strip().upper() for x in syms.split(",") if x.strip()] if syms else None
    return event_detector.query(kind=kind, q=q, syms=sl, since_id=since_id, limit=max(1, min(limit, 2000)))


# ------------------------------------------------------------------ v1.20.0
@app.get("/api/radar")
def v120_radar():
    """Piyasa Radarı: tüm paylar (fiyat, % değişim, TL hacim, tavan/taban uzaklığı, sektör)."""
    return v120_hub.radar()


@app.get("/api/radar/peers/{symbol}")
def v120_peers(symbol: str):
    """RAKİPLER: aynı sektör endeksindeki paylar."""
    return v120_hub.peers(symbol)


@app.get("/api/tavan-taban")
def v120_tavan(approach: float = Query(2.0, ge=0.1, le=10)):
    return v120_hub.tavan_list(approach)


@app.get("/api/agresif")
def v120_agresif(side: str = "both", min_lot: float = 0, min_tl: float = 0, min_levels: int = 1,
                 min_book_pct: float = 0, syms: str | None = None, limit: int = Query(300, ge=1, le=3000),
                 since_sec: int = 0):
    sl = [x.strip().upper() for x in syms.split(",") if x.strip()] if syms else None
    return v120_hub.sweeps_query(side, min_lot, min_tl, max(1, min_levels), min_book_pct, sl, limit, since_sec)


@app.get("/api/para-akisi")
def v120_para():
    return v120_hub.para_akisi()


@app.get("/api/tahtaci")
def v120_tahtaci(view: str = "score", broker: str | None = None, symbol: str | None = None,
                 min_tl: float = 5e6, limit: int = Query(300, ge=1, le=3000), nocross: int = 0):
    return v120_hub.tahtaci(view, broker, symbol, min_tl, limit, nocross=bool(nocross))


@app.get("/api/kurum/rapor")
def v120_rapor(brokers: str | None = None, day: str | None = None):
    """Gün sonu raporu: seçili kurumlar (boş = tümü). day=YYYYMMDD → kaydedilmiş otomatik rapor."""
    if day:
        r = v120_hub.saved_report(day)
        if r is None:
            raise HTTPException(404, "rapor yok")
        return r
    bl = [x.strip() for x in brokers.split(",") if x.strip()] if brokers else None
    return v120_hub.report(bl)


@app.get("/api/kurum/list")
def v120_brokers():
    v120_hub.flows.ensure()
    return {"brokers": sorted({n for n in (v120_hub.flows.names or []) if n})}


@app.get("/api/alerts/config")
def v120_cfg_get(cid: str):
    c = v120_hub.client(cid)
    return {"cfg": c["cfg"], "push": bool(c.get("push"))}


@app.post("/api/alerts/config")
def v120_cfg_set(payload: dict = Body(...)):
    cid = str(payload.get("cid") or "")
    if not cid:
        raise HTTPException(400, "cid gerekli")
    return {"cfg": v120_hub.set_config(cid, payload.get("cfg") or {})}


@app.get("/api/alerts/feed")
def v120_feed(cid: str, since: int = 0, kinds: str | None = None, visible: int = 0, limit: int = Query(200, ge=1, le=2000)):
    kl = [k for k in kinds.split(",") if k] if kinds else None
    return v120_hub.feed_for(cid, since, limit, kl, bool(visible))


@app.get("/api/push/key")
def v120_push_key():
    return {"key": v120_hub.vapid_public, "enabled": bool(v120_hub.vapid_public)}


@app.post("/api/push/subscribe")
def v120_push_sub(payload: dict = Body(...)):
    return v120_hub.subscribe(str(payload.get("cid") or ""), payload.get("subscription"))


@app.post("/api/push/test")
def v120_push_test(payload: dict = Body(...)):
    return v120_hub.test_push(str(payload.get("cid") or ""))


@app.get("/api/v120/status")
def v120_status():
    return v120_hub.status()


# ------------------------------------------------------------------ v1.21.0 OPERASYON TESPİTİ
@app.get("/api/op/list")
def op_list():
    return op_engine.catalog()


@app.get("/api/op/f/{fid}")
def op_feature(fid: int, q: str | None = None):
    return op_engine.feature(fid, q)


@app.get("/api/op/mk/{name}")
def op_market(name: str):
    if name not in ("kademe", "teknik"):
        raise HTTPException(status_code=404, detail="bilinmeyen ekran")
    return op_engine.feature(name)


@app.get("/api/op/stock/{symbol}")
def op_stock(symbol: str):
    return op_engine.stock(symbol)


@app.get("/api/op/zaman/{symbol}")
def op_zaman(symbol: str):
    return op_engine.zaman(symbol)


@app.get("/api/op/status")
def op_status():
    return op_engine.status()


# ------------------------------------------------------------------ v1.19.0
@app.get("/api/index-impact/indices")
def index_impact_indices():
    """Tüm BIST endeksleri (İdealData + Borsa İstanbul resmi bileşen listesi)."""
    return get_index_impact(ideal_feed).catalog()


@app.get("/api/index-impact/stock/{symbol}")
def index_impact_stock(symbol: str):
    """Bir hissenin yer aldığı endeksler, ağırlığı ve puan etkisi."""
    return get_index_impact(ideal_feed).stock_indices(symbol)


@app.get("/api/index-impact/{code}")
def index_impact_code(code: str):
    """Hisselerin endekse etkisi: ağırlık × günlük getiri → puan etkisi (canlı)."""
    return get_index_impact(ideal_feed).impact(code)


@app.get("/api/live/depth-pressure")
def live_depth_pressure():
    rows = ideal_feed.depth_pressure()
    return {"count": len(rows), "rows": rows, "levels": 25,
            "note": "İdealData derinlikte en fazla 25 kademe ayrıntı verir; 'Tüm kademe' değerleri feed'in yayınladığı "
                    "tüm defter toplam lotlarıdır (alış/satış toplamı ve ortalama fiyat).",
            "updated": _ist_now_str()}


@app.get("/api/live/brokers")
def live_brokers():
    res = ideal_feed.broker_positions()
    agg: dict = {}
    for r in res["rows"]:
        a = agg.setdefault(r["b"], {"b": r["b"], "n": 0, "bl": 0.0, "sl": 0.0, "btl": 0.0, "stl": 0.0, "kz": 0.0, "ntl": 0.0})
        a["n"] += 1
        a["bl"] += r["bl"]; a["sl"] += r["sl"]
        if r["p"]:
            a["btl"] += r["bl"] * r["p"]; a["stl"] += r["sl"] * r["p"]
        if r["co"] and r["nl"]:
            a["ntl"] += r["nl"] * r["co"]
        a["kz"] += r["kz"] or 0.0
    out = sorted(agg.values(), key=lambda a: -(a["btl"] + a["stl"]))
    for a in out:
        for k in ("bl", "sl", "btl", "stl", "kz", "ntl"):
            a[k] = round(a[k], 2)
    return {"count": len(out), "brokers": out, "stocks_akd": res["stocks_akd"], "stocks_tick": res["stocks_tick"],
            "akd_date": res["akd_date"], "akd_cycle_sec": ideal_feed.last_akd_cycle_sec}


@app.get("/api/live/brokers/matrix")
def live_broker_matrix(broker: str = "", q: str = "", sort: str = "bl", dir: str = "desc",
                       offset: int = 0, limit: int = 200, side: str = ""):
    res = ideal_feed.broker_positions()
    rows = res["rows"]
    if broker:
        bf = _tr_fold(broker)
        rows = [r for r in rows if _tr_fold(r["b"]) == bf]
    if q:
        qf = _tr_fold(q)
        rows = [r for r in rows if qf in r["s"] or qf in _tr_fold(r["b"])]
    if side == "buy":
        rows = [r for r in rows if r["nl"] > 0]
    elif side == "sell":
        rows = [r for r in rows if r["nl"] < 0]
    key = sort if sort in ("bl", "bp", "sl", "sp", "np", "tp", "nl", "co", "p", "kz", "kzp", "s", "b") else "bl"
    rev = dir != "asc"
    if key in ("s", "b"):
        rows = sorted(rows, key=lambda r: r[key], reverse=rev)
    else:
        rows = sorted(rows, key=lambda r: (r.get(key) is None, -(r.get(key) or 0) if rev else (r.get(key) or 0)))
    tot = {"bl": 0.0, "sl": 0.0, "nl": 0.0, "kz": 0.0, "btl": 0.0, "stl": 0.0, "ntl": 0.0}
    for r in rows:
        tot["bl"] += r["bl"]; tot["sl"] += r["sl"]; tot["nl"] += r["nl"]; tot["kz"] += r["kz"] or 0.0
        if r["p"]:
            tot["btl"] += r["bl"] * r["p"]; tot["stl"] += r["sl"] * r["p"]
        if r["co"] and r["nl"]:
            tot["ntl"] += r["nl"] * r["co"]
    tot = {k: round(v, 2) for k, v in tot.items()}
    tot["kzp"] = round(tot["kz"] / abs(tot["ntl"]) * 100.0, 2) if tot["ntl"] else None
    limit = max(1, min(limit, 1000))
    return {"total": len(rows), "offset": offset, "limit": limit, "rows": rows[offset: offset + limit], "totals": tot,
            "stocks_akd": res["stocks_akd"], "stocks_tick": res["stocks_tick"], "akd_date": res["akd_date"],
            "akd_status": res.get("akd_status")}


@app.get("/api/akd/day/status")
def akd_day_status():
    """v1.21.3: günlük AKD deposu kapsamı (Kurum Analizi / AKD sekmesi ortak kaynak)."""
    return ideal_feed.akd_day_status()


def _ist_now_str() -> str:
    from datetime import datetime as _dt
    from zoneinfo import ZoneInfo as _Z
    return _dt.now(_Z("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M:%S")


@app.get("/api/ideal/{symbol}/trades")
def ideal_trades(symbol: str, broker: str = "", side: str = "", minutes: int = 0, min_tl: float = 0,
                 lot_eq: int | None = None, lot_ge: int | None = None, sort: str = "time",
                 offset: int = 0, limit: int = 200):
    sym = "".join(ch for ch in symbol.upper() if ch.isalnum())
    res = trade_store.query(sym, broker=broker or None, side=side or None, minutes=minutes or None,
                            min_tl=min_tl or None, lot_eq=lot_eq, lot_ge=lot_ge, sort=sort,
                            offset=max(0, offset), limit=max(1, min(limit, 1000)))
    q = ideal_feed.live_quote(sym) or {}
    vol = None
    with ideal_feed._lock:
        vol = (ideal_feed.quotes.get(sym) or {}).get("volume")
    res["coverage"] = trade_store.coverage(sym, vol)
    res["day_volume"] = vol
    res["symbol"] = sym
    stt = trade_store.stats()
    res["store"] = {"started": stt["started"], "live_since": stt["live_since"],
                    "live_before_open": stt["live_before_open"], "session_open": "09:55"}
    cov = res["coverage"] or {}
    if vol and cov.get("lot") is not None:
        res["missing_lot"] = max(0.0, float(vol) - float(cov.get("lot") or 0))
    res["history_note"] = ("İdealData geçmiş (tüm gün) işlem listesi sunmuyor: REQ_DERINLIK yalnızca son 50 işlemi "
                           "döndürüyor. Kayıt, sunucunun canlı akışa abone olduğu andan itibaren eksiksizdir.")
    res["price"] = q.get("last") if isinstance(q, dict) else None
    try:   # v1.37.0: gecikme = sunucu saati − son işlem saati (gün saniyesi, İstanbul)
        from app.live_store import _sec_now as _sn
        res["lag_srv"] = (_sn() - res["last_sec"]) if res.get("last_sec") is not None else None
        res["live"] = bool(trade_store._live)
    except Exception:
        pass
    res["server_ts"] = time.time()
    return res


def _hms_sec(v):
    try:
        v = str(v or "")
        if "T" in v or " " in v:
            v = v.replace("T", " ").split(" ")[1]
        a = [int(float(x)) for x in v.split(":")[:3]]
        while len(a) < 3:
            a.append(0)
        return a[0] * 3600 + a[1] * 60 + a[2]
    except Exception:
        return None


def _lite_trade_overlay(q):
    """v1.35.0: liste satırlarında da takılan kotasyon yerine son işlem (trade_store) fiyatı."""
    try:
        e = trade_store.syms.get(q.get("symbol"))
        if e is None or not len(e.t):
            return q
        lt, lp = e.t[-1], e.p[-1]
        qt = _hms_sec(q.get("time"))
        if lp <= 0 or qt is None or lt <= qt:
            return q
        q = dict(q); q["price"] = lp
        pc = q.get("previous_close")
        if isinstance(pc, (int, float)) and pc > 0:
            q["change_pct"] = (lp / pc - 1) * 100
    except Exception:
        pass
    return q


@app.get("/api/lite/stocks")
def lite_stocks():
    """v1.17.0 arama listesi: tüm BIST payları, hafif alanlar (sembol, ad, fiyat, değişim, TL hacim)."""
    _ensure_symbols()
    quotes, err = quote_service.fetch_all(_symbols, force=False)
    out = []
    for q in quotes:
        q = _lite_trade_overlay(q)
        out.append({
            "s": q.get("symbol"), "n": q.get("name"), "p": q.get("price"),
            "c": round(q["change_pct"], 3) if q.get("change_pct") is not None else None,
            "t": q.get("live_turnover") or ((q.get("volume") or 0) * (q.get("price") or 0)) or None,
        })
    return {"count": len(out), "stocks": out, "error": err}


@app.get("/api/ideal/{symbol}/akd")
def ideal_akd(
    symbol: str,
    period: str = Query("daily", description="daily|weekly|monthly|3m|custom"),
    date_from: str | None = Query(None, alias="from"),
    date_to: str | None = Query(None, alias="to"),
):
    """AKD (aracı kurum dağılımı) — İdealData REQ_DGLM_TAR2 tarih aralığı."""
    try:
        d1, d2, label = _akd_period_range(period, date_from, date_to)
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz tarih")
    ideal_feed.touch(symbol)
    v = ideal_feed.akd_view(symbol, d1, d2)
    st = ideal_feed.status()
    if not v:
        return {"symbol": symbol.upper(), "period": period, "label": label, "from": d1, "to": d2,
                "available": False, "buyers": [], "sellers": [], "total": [],
                "note": ("İdealData bağlantısı yok" if not st.get("healthy")
                         else "Bu dönem için İdealData AKD yanıtı alınamadı."),
                "feed": {k: st[k] for k in ("state", "label", "healthy", "error")}}
    v.update({"period": period, "label": label, "available": bool(v["buyers"] or v["sellers"]),
              "feed": {k: st[k] for k in ("state", "label", "healthy", "error")}})
    if not v["available"]:
        v["note"] = "Bu dönem için AKD verisi yok (tatil / seans öncesi olabilir)."
    return v


@app.get("/api/ideal/{symbol}/takas")
def ideal_takas(symbol: str, date: str | None = Query(None), compare: str | None = Query(None)):
    """MKK takas (saklama) dağılımı — REQ_TKS4 (MKK lisansı gerekir)."""
    from datetime import timedelta as _td, datetime as _dt

    st = ideal_feed.status()
    if "MKK" not in (st.get("licenses") or []):
        return {"symbol": symbol.upper(), "available": False, "rows": [],
                "note": "Takas verisi için İdealData MKK lisansı gerekir (lisans bulunamadı)."}
    tried = []
    if date:
        cands = [date.replace("-", "")]
    else:
        d = _ist_today()
        cands = []
        for _ in range(6):
            d = _prev_weekday(d - _td(days=1)) if cands else _prev_weekday(d)
            cands.append(d.strftime("%Y%m%d"))
    res = None
    for c in cands:
        tried.append(c)
        r = ideal_feed.takas(symbol, c)
        if r and r.get("rows"):
            res = r
            break
    if not res:
        return {"symbol": symbol.upper(), "available": False, "rows": [], "tried": tried,
                "note": "İdealData takas verisi alınamadı (MKK verisi henüz yayımlanmamış olabilir)."}
    rows = res["rows"]
    tot = sum((r.get("lot") or 0) for r in rows) or 0
    out = {"symbol": res["symbol"], "available": True, "date": res["date"], "rows": rows,
           "total_lot": tot, "header": res.get("header"), "source_label": "İdealData MKK takas"}
    if compare:
        from datetime import datetime as _dt2
        _back = {"auto": 7, "w1": 7, "d1": 1, "m1": 30}.get(compare)
        out["period"] = {"auto": "w1"}.get(compare, compare)
        if _back:
            d0 = _dt2.strptime(res["date"], "%Y%m%d").date() - _td(days=_back)
            compare = _prev_weekday(d0).strftime("%Y%m%d")
        ch = ideal_feed.takas_change(symbol, compare.replace("-", ""), res["date"])
        if not ch and _back:     # o gün takas yoksa bir önceki iş gününü dene
            for _ in range(3):
                d0 = _prev_weekday(d0 - _td(days=1))
                ch = ideal_feed.takas_change(symbol, d0.strftime("%Y%m%d"), res["date"])
                if ch:
                    break
        if ch:
            out["change"] = ch
    return out


_LOGO_DIR = Path(__file__).resolve().parent.parent / "data" / "logos"


@app.get("/api/logo/{symbol}")
def stock_logo(symbol: str):
    """Şirket logosu (İdealData s3 companylogo) — diske önbelleklenir."""
    import re as _re
    import time as _time
    from fastapi.responses import Response

    sym = _re.sub(r"[^A-Za-z0-9]", "", symbol or "").lower()[:12]
    if not sym:
        raise HTTPException(status_code=404)
    _LOGO_DIR.mkdir(parents=True, exist_ok=True)
    f = _LOGO_DIR / f"{sym}.png"
    miss = _LOGO_DIR / f"{sym}.miss"
    if f.exists() and f.stat().st_size > 100:
        return FileResponse(f, media_type="image/png", headers={"Cache-Control": "public, max-age=604800"})
    def _placeholder():
        # 404 yerine baş harfli SVG (tarayıcı konsolunda kaynak hatası oluşmasın)
        import hashlib
        h = int(hashlib.md5(sym.encode()).hexdigest()[:4], 16) % 360
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="10" '
               f'fill="hsl({h},40%,22%)"/><text x="32" y="41" font-family="Arial,Helvetica,sans-serif" font-size="24" '
               f'font-weight="700" fill="#e8e3d3" text-anchor="middle">{sym[:2].upper()}</text></svg>')
        return Response(svg, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=21600", "X-Logo": "placeholder"})

    if miss.exists() and _time.time() - miss.stat().st_mtime < 21600:
        return _placeholder()
    try:
        import httpx

        for url in (f"https://s3.idealdata.com.tr/companylogo/{sym}.png",
                    f"https://cdn.jsdelivr.net/gh/ahmeterenodaci/Istanbul-Stock-Exchange--BIST--including-symbols-and-logos/logos/{sym.upper()}.png"):
            try:
                r = httpx.get(url, timeout=6.0, follow_redirects=True)
            except Exception:
                continue
            if r.status_code == 200 and r.content[:4] == b"\x89PNG":
                f.write_bytes(r.content)
                miss.unlink(missing_ok=True)
                return Response(r.content, media_type="image/png", headers={"Cache-Control": "public, max-age=604800"})
    except Exception:
        pass
    miss.write_text("")
    return _placeholder()


@app.get("/api/ideal/{symbol}")
def ideal_symbol(
    request: Request,
    symbol: str,
    trades: int = Query(100, ge=1, le=200),
    touch: bool = Query(True, description="Seçili hisse aboneliğini canlı tut"),
):
    """Tek hisse canlı İdealData: derinlik, özet, işlemler, AKD alıcı/satıcı, para akışı, footprint."""
    if touch:
        ideal_feed.touch(symbol)
    res = _quote_from_trades(ideal_feed.symbol_view(symbol, trades_limit=trades))
    if isinstance(res, dict):
        res = dict(res); res["server_ts"] = time.time()
    return _gz_json(request, res)   # v1.35.0: gzip → ngrok veri kotası ~5× daha az


@app.get("/api/live/{symbol}")
def live_combined(request: Request, symbol: str, trades: int = Query(100, ge=1, le=200), isl: str = Query("")):
    """v1.35.1 tek istek: üst fiyat + derinlik + son işlemler (+ İşlemler sekmesi sorgusu) aynı anda → tünel kotası yarıya."""
    ideal_feed.touch(symbol)
    res = _quote_from_trades(ideal_feed.symbol_view(symbol, trades_limit=trades))
    res = dict(res) if isinstance(res, dict) else {"data": res}
    res["server_ts"] = time.time()
    if isl:
        from urllib.parse import parse_qsl
        kw = {}
        conv = {"minutes": int, "min_tl": float, "lot_eq": int, "lot_ge": int, "offset": int, "limit": int}
        for k, v in parse_qsl(isl):
            if k in ("broker", "side", "sort") or k in conv:
                try:
                    kw[k] = conv.get(k, str)(v)
                except Exception:
                    pass
        try:
            res["isl"] = ideal_trades(symbol, **kw)
        except Exception as e:
            res["isl_error"] = type(e).__name__
    return _gz_json(request, res)


def _quote_from_trades(res):
    """v1.34.2: İdealData fiyat (quote) akışı bazen takılıyor ama işlemler/derinlik canlı geliyor →
    son işlem kotasyondan yeniyse üst fiyat/saat/% son işlemden; alış/satış en iyi kademeden."""
    try:
        if not isinstance(res, dict):
            return res
        q = res.get("quote")
        tr = res.get("trades") or []
        if not isinstance(q, dict) or not tr:
            return res
        last = max(tr, key=lambda t: str(t.get("time") or ""))
        lt, lp = str(last.get("time") or ""), last.get("price")
        if not lt or not isinstance(lp, (int, float)) or lp <= 0 or lt <= str(q.get("time") or ""):
            return res
        q = dict(q)
        q["price"] = lp
        q["time"] = lt
        q["price_src"] = "trade"
        pc = q.get("previous_close")
        if isinstance(pc, (int, float)) and pc > 0:
            q["change_pct"] = round((lp / pc - 1) * 100, 3)
        if isinstance(q.get("high"), (int, float)) and lp > q["high"]:
            q["high"] = lp
        if isinstance(q.get("low"), (int, float)) and q["low"] > 0 and lp < q["low"]:
            q["low"] = lp
        dp = res.get("depth") or {}
        if isinstance(dp.get("best_bid"), (int, float)):
            q["bid"] = dp["best_bid"]
        if isinstance(dp.get("best_ask"), (int, float)):
            q["ask"] = dp["best_ask"]
        res = dict(res)
        res["quote"] = q
    except Exception:
        pass
    return res


# ------------------------------------------------- v1.22.0 KADEME & ŞERİT
def _gz_json(request: Request, obj) -> Response:
    import gzip as _gz
    import json as _json
    raw = _json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")
    hdr = {"Cache-Control": "no-store"}
    if len(raw) > 2048 and "gzip" in (request.headers.get("accept-encoding") or "").lower():
        hdr["Content-Encoding"] = "gzip"
        hdr["Vary"] = "Accept-Encoding"
        return Response(_gz.compress(raw, 5), media_type="application/json; charset=utf-8", headers=hdr)
    return Response(raw, media_type="application/json; charset=utf-8", headers=hdr)


@app.get("/api/k/list")
def k_list():
    """v1.22.0 Kademe & Şerit tarayıcı kataloğu."""
    return k_engine.catalog()


@app.get("/api/k/status")
def k_status():
    return k_engine.status()


@app.get("/api/k/maliyet/detail")
def k_maliyet_detail(request: Request, sym: str = Query(...), br: str = Query(...), date: str | None = Query(None)):
    """v1.23.0 Bir kurumun bir hissedeki işlem işlem maliyet yolu (kümülatif ortalama, yükseltmeler, saniye saniye fiyat)."""
    return _gz_json(request, m_engine.detail(sym, br, date))


@app.get("/api/k/baski/detail")
def k_baski_detail(request: Request, sym: str = Query(...), fid: str = Query("k_poc"), date: str | None = Query(None)):
    """v1.24.0 Hissenin saniye saniye fiyatı + POC / aktif alış ortalaması çizgisi, kaymalar, destek/direnç testleri, süpürmeler."""
    return _gz_json(request, b_engine.detail(fid, sym, date))


@app.get("/api/k/baski/status")
def k_baski_status():
    return b_engine.status()


@app.get("/api/stocks/{symbol}/ozet-plus")
def stock_ozet_plus(request: Request, symbol: str, date: str | None = Query(None), cid: str | None = Query(None)):
    """v1.24.0 Hisse ÖZET sekmesi ek kartları — tek çağrıda: ısrarcı kurum, kurum yoğunlaşması, son 5 dk nabız, kademe dengesi,
    konum (POC/VAH/VAL/VWAP/zirve/tavan), operasyon skoru + aktif tarayıcı çipleri, bugünkü bildirimler, tek cümlelik yorum."""
    res = b_engine.ozet(symbol, date, (cid or "").strip()[:64] or None)
    # v1.26.2 TAHTACI SİNYALİ (AKD net lider = aktif lider) — önbellekteki sözlük değiştirilmez (sığ kopya)
    try:
        if isinstance(res, dict) and res.get("day") and not res.get("error"):
            sig = v126_engine.tahtaci(res.get("sym") or symbol, res.get("day"))
            if sig:
                res = dict(res)
                res["tahtaci"] = sig
                ch = list(res.get("chips") or [])
                for i, x in enumerate(sig):   # v1.26.3 TAVAN TRENİ (birleşik) önce
                    if x.get("kind") == "tren":
                        lab = f"🚂 TAVAN TRENİ ({x.get('G') or x['grade']})" + (" + TAHTACI ↑" if x.get("tht") else "")
                    else:
                        lab = f"TAHTACI {'↑' if x['side'] == 'up' else '↓'} ({x['grade']})"
                    ch.insert(i, {"id": "akd_tab", "g": "trn" if x.get("kind") == "tren" else "tht", "strong": x["grade"] == "güçlü", "txt": x["br"], "l": lab})
                res["chips"] = ch
    except Exception as ex:   # pragma: no cover
        logger.debug("ozet tahtaci: %s", ex)
    # v1.27.0 FORMASYONLAR: çip + yorumda tek satır (yalnız güncel gün)
    try:
        if isinstance(res, dict) and not res.get("error") and not date:
            fx = v127_engine.chip(res.get("sym") or symbol.upper())
            if fx:
                res = dict(res)
                res["chips"] = list(res.get("chips") or []) + [fx["chip"]]
                if fx.get("yorum"):
                    res["formasyon"] = fx["yorum"]
                    if isinstance(res.get("yorum"), str):
                        res["yorum"] = (res["yorum"].rstrip() + " " + fx["yorum"]).strip()
    except Exception as ex:   # pragma: no cover
        logger.debug("ozet formasyon: %s", ex)
    return _gz_json(request, res)


@app.get("/api/stocks/{symbol}/derinlik-plus")
def stock_derinlik_plus(request: Request, symbol: str, items: str | None = Query(None), date: str | None = Query(None)):
    """v1.25.0 Hisse DERİNLİK sekmesi analizleri — yalnız istenen maddeler (items=1,2,3,…; 6 yok) hesaplanır."""
    its = None
    if items is not None:
        its = [int(x) for x in items.split(",") if x.strip().isdigit()]
    return _gz_json(request, d_engine.analyze(symbol.upper(), its, date))


@app.get("/api/perf")
def perf_status():
    """v1.38.1 kaynak profili (data/perf.json · low_resource auto: CPU ≤ 2 ya da RAM ≤ 4 GB)."""
    from app import perf as _perf
    return _perf.status()


@app.get("/api/derinlik/status")
def derinlik_status():
    return d_engine.status()


@app.get("/api/stocks/{symbol}/akis")
def stock_akis(request: Request, symbol: str, date: str | None = Query(None), brief: int = Query(0)):
    """v1.26.0 SEANS İŞLEM AKIŞI ANALİZİ — gerçek işlem kaydından aktif alış/satış, büyüklük, süpürme, duvar süpürme, fiyat etkisi."""
    return _gz_json(request, v126_engine.flow(symbol.upper(), date, bool(brief)))


@app.get("/api/stocks/{symbol}/akd-plus")
def stock_akd_plus(
    request: Request, symbol: str,
    period: str = Query("daily"),
    date_from: str | None = Query(None, alias="from"),
    date_to: str | None = Query(None, alias="to"),
):
    """v1.26.0 AKD sekmesi K/Z + AKD ANALİZİ — AKD sekmesiyle aynı kaynak (akd_view, aynı dönem)."""
    try:
        d1, d2, label = _akd_period_range(period, date_from, date_to)
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz tarih")
    return _gz_json(request, v126_engine.akd_plus(symbol, d1, d2, label))


@app.get("/api/akd/tarama")
def akd_tarama(request: Request, date: str | None = Query(None), tok: str | None = Query(None)):
    """v1.26.0 KEŞFET › AKD TARAMASI — tüm hisselerin günlük AKD'si (AKD sekmesi Günlük / Kurum Analizi ile aynı kayıt)."""
    return _gz_json(request, v126_engine.tarama(date, tok))


@app.get("/api/akd/tarama/watch")
def akd_tarama_watch_get():
    return v126_engine.watch_get()


@app.get("/api/aktif-kurum/watch")
def aktif_kurum_watch_get():
    """v1.26.2 aktif_kurum bildirim ayarı (varsayılan KAPALI)."""
    return v126_engine.akk_get()


@app.get("/api/tavan-treni/watch")
def tavan_treni_watch_get():
    """v1.26.3 tavan_treni bildirim ayarı (varsayılan KAPALI)."""
    return v126_engine.trn_get()


@app.post("/api/tavan-treni/watch")
async def tavan_treni_watch_set(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz JSON")
    return v126_engine.trn_set(body or {})


@app.post("/api/aktif-kurum/watch")
async def aktif_kurum_watch_set(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz JSON")
    return v126_engine.akk_set(body or {})


@app.post("/api/akd/tarama/watch")
async def akd_tarama_watch_set(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz JSON")
    return v126_engine.watch_set((body or {}).get("rules") or [])


# ---------------------------------------------------------------- v1.27.0 FORMASYONLAR
def _tf_list(tf):
    return [t for t in (tf or "").split(",") if t] or None


@app.get("/api/formasyon/mum")
def formasyon_mum(request: Request, tf: str | None = Query(None)):
    """Mum formasyonları (tüm hisseler, son kapanmış bar): sıkıştırılmış satırlar + formasyon sözlüğü + dürüstlük testi."""
    return _gz_json(request, v127_engine.listing("mum", _tf_list(tf)))


@app.get("/api/formasyon/grafik")
def formasyon_grafik(request: Request, tf: str | None = Query(None)):
    """Grafik formasyonları (tüm hisseler): durum, giriş/STOP/HEDEF 1-2, R/R, uzaklık, hacim teyidi, kalite."""
    return _gz_json(request, v127_engine.listing("grafik", _tf_list(tf)))


@app.get("/api/formasyon/hisse/{symbol}")
def formasyon_hisse(request: Request, symbol: str):
    return _gz_json(request, v127_engine.hisse(symbol))


@app.get("/api/formasyon/kanit")
def formasyon_kanit(request: Request, sym: str = Query(...), tf: str = Query(...), kind: str = Query("mum"), k: str = Query(...)):
    """Kanıt: gerçek barlar + formasyon geometrisi + kural kontrolleri (animasyonlu gösterim için)."""
    return _gz_json(request, v127_engine.kanit(sym, tf, "mum" if kind == "mum" else "grafik", k))


@app.get("/api/formasyon/ob")
def formasyon_ob(request: Request, sym: str = Query(...), tf: str = Query(...)):
    """v1.28.0 ORDER BLOCK: gerçek barlar + en yakın arz/talep bölgeleri (TAZE/TEST EDİLDİ), FVG, tanım (animasyonlu kanıt için)."""
    return _gz_json(request, v127_engine.ob_kanit(sym, tf))


@app.get("/api/formasyon/status")
def formasyon_status():
    return v127_engine.status()


@app.get("/api/formasyon/watch")
def formasyon_watch_get():
    return v127_engine.watch_get()


@app.post("/api/formasyon/watch")
def formasyon_watch_set(body: dict = Body(None)):
    return v127_engine.watch_set(body or {})


# ---------------------------------------------------------------- v1.27.1 AKD TARAMASI · DÖNEM
@app.get("/api/akd/donem")
def akd_donem_api(request: Request, period: str = Query("weekly", description="weekly|monthly")):
    """TÜM AKD NET için HAFTALIK/AYLIK hisse bazında satırlar (İLK 3/5/10 ALAN-SATAN dahil) — AKD sekmesi ile aynı istek/hesap.
    İlk çağrıda tüm hisseler arka planda çekilir (running/done/total ile ilerleme)."""
    return _gz_json(request, v1271_akd_donem.get(period))


@app.get("/api/v126/status")
def v126_status():
    return v126_engine.status()


@app.get("/api/k/maliyet/status")
def k_maliyet_status():
    return m_engine.status()


@app.get("/api/k/f/{fid}")
def k_feature(request: Request, fid: str, w: str | None = Query(None), q: str | None = Query(None),
              date: str | None = Query(None), tok: str | None = Query(None)):
    """v1.22.0 Tek tarayıcı sonucu (tüm hisseler, arka planda ~3 sn'de bir hesaplanır)."""
    if fid == M_FID:   # v1.23.0 — ?date=YYYYMMDD (yoksa bugün / son seans)
        return _gz_json(request, m_engine.feature(w, q, date, tok))
    if fid in B_FIDS:  # v1.24.0 — POC Baskısı / Alış Ortalama Baskısı / Ciddi Yükseliş-Tavan Adayı
        return _gz_json(request, b_engine.feature(fid, w, q, date, tok))
    return _gz_json(request, k_engine.feature(fid, w, q))


# ------------------------------------------------- v1.38.0 TELEGRAM (OneSignal kaldırıldı; eski kod /workspace/tmp/pre1380/)
# v1.22.2 — OneSignal anahtarlarını Bildirim Ayarları ekranından düzenleme (giriş yok → asgari koruma:
# aynı köken (Origin/Referer = Host) + özel başlık X-BIST-Confirm (çapraz köken ön-uçuşu reddedilir) + JSON + hız sınırı).
_OS_EDIT_TS: list = []


def _os_guard(request: Request, body: dict) -> None:
    from urllib.parse import urlparse
    hosts = {h.strip().lower() for h in ((request.headers.get("host") or "") + "," + (request.headers.get("x-forwarded-host") or "")).split(",") if h.strip()}
    src = request.headers.get("origin") or request.headers.get("referer") or ""
    if not src or urlparse(src).netloc.lower() not in hosts:
        raise HTTPException(status_code=403, detail="Yalnızca uygulamanın kendi sayfasından değiştirilebilir (köken uyuşmuyor).")
    if request.headers.get("x-bist-confirm") != "1" or body.get("confirm") is not True:
        raise HTTPException(status_code=403, detail="Onay gerekli.")
    if "application/json" not in (request.headers.get("content-type") or ""):
        raise HTTPException(status_code=415, detail="JSON gerekli")
    now = time.time()
    _OS_EDIT_TS[:] = [t for t in _OS_EDIT_TS if now - t < 60]
    if len(_OS_EDIT_TS) >= 8:
        raise HTTPException(status_code=429, detail="Çok fazla deneme — 1 dakika sonra tekrar deneyin.")
    _OS_EDIT_TS.append(now)



@app.get("/api/telegram/config")
def telegram_config(cid: str | None = Query(None)):
    out = tg_sender.public()
    out["this_is_owner"] = bool(cid) and cid == out.get("owner_cid")
    return out


@app.post("/api/telegram/settings")
def telegram_settings(request: Request, body: dict = Body(...)):
    """Bot Token (yalnız yazılır, asla dönmez) + Chat ID + kategoriler + sessiz saatler + sahip cihaz."""
    _os_guard(request, body)
    import re as _re
    c = tg_sender.cfg
    tok = (body.get("token") or "").strip()
    if tok:
        if not _re.fullmatch(r"\d{5,12}:[A-Za-z0-9_-]{30,60}", tok):
            return {"ok": False, "error": "Bot Token biçimi geçersiz (ör. 123456789:AA…; @BotFather verir)."}
    chat = body.get("chat_id")
    if chat is not None:
        chat = str(chat).strip()
        if chat and not _re.fullmatch(r"@[A-Za-z][A-Za-z0-9_]{3,}|-?\d{5,20}", chat):
            return {"ok": False, "error": "Chat ID geçersiz: @kanaladi ya da -100… biçiminde olmalı."}
    me = None
    if tok:
        old = c.get("token"); c["token"] = tok
        me = tg_sender._api("getMe") if not tg_sender.dry() else {"ok": True, "result": {"username": "dryrun_bot"}}
        if not me.get("ok"):
            c["token"] = old
            return {"ok": False, "error": "Token doğrulanamadı: " + str(me.get("description") or "")[:120]}
    if chat is not None:
        c["chat_id"] = chat or None
    if isinstance(body.get("cats"), dict):
        c["cats"].update({k: bool(v) for k, v in body["cats"].items() if k in c["cats"]})
    if isinstance(body.get("quiet"), dict):
        q = body["quiet"]
        c["quiet"].update({k: q[k] for k in ("on", "from", "to") if k in q})
    if body.get("owner_cid"):
        c["owner_cid"] = str(body["owner_cid"])[:64]
    if "dry" in body:   # deneme modu: Telegram'a gitmez, data/telegram_dryrun.log'a yazılır
        c["dry"] = bool(body["dry"])
    tg_sender._save_cfg()
    logger.info("Telegram ayarları kaydedildi (token …%s)", (c.get("token") or "")[-4:])
    return {"ok": True, "bot": ((me or {}).get("result") or {}).get("username"), "config": tg_sender.public()}


@app.post("/api/telegram/find_chat")
def telegram_find_chat(request: Request, body: dict = Body(...)):
    """getUpdates → botun gördüğü sohbetler (kanala yönetici eklendikten / bota mesaj atıldıktan sonra)."""
    _os_guard(request, body)
    if not tg_sender.cfg.get("token"):
        return {"ok": False, "error": "Önce Bot Token kaydedin."}
    r = tg_sender._api("getUpdates", {"limit": 100, "allowed_updates": '["message","channel_post","my_chat_member","chat_member"]'})
    if not r.get("ok"):
        d = str(r.get("description") or "")
        hint = " (webhook tanımlı — botun webhook'unu silin)" if "webhook" in d.lower() else ""
        return {"ok": False, "error": d[:160] + hint}
    seen = {}
    for u in r.get("result") or []:
        for k in ("message", "channel_post", "my_chat_member", "chat_member", "edited_channel_post"):
            ch = (u.get(k) or {}).get("chat")
            if ch:
                seen[ch["id"]] = {"id": ch["id"], "type": ch.get("type"), "title": ch.get("title") or " ".join(x for x in (ch.get("first_name"), ch.get("last_name")) if x),
                                  "username": ch.get("username")}
    chats = sorted(seen.values(), key=lambda x: (x["type"] != "channel", str(x["title"])))
    return {"ok": True, "chats": chats, "note": None if chats else "Hiç sohbet görünmüyor: botu kanala yönetici ekleyin ve kanala bir mesaj yazın (ya da bota /start gönderin), sonra tekrar deneyin."}


@app.post("/api/telegram/test")
def telegram_test(request: Request, body: dict = Body(...)):
    if not tg_sender.ready():
        return {"ok": False, "error": "Bot Token ve Chat ID kaydedilmemiş."}
    feat = str(body.get("feature") or "")[:60]
    ok = tg_sender.enqueue("test", f"✅ <b>BIST Canlı · Telegram test{(' · ' + feat) if feat else ''}</b>\nBildirimler bu kanala gelecek.\n🕒 {time.strftime('%d.%m %H:%M:%S', time.gmtime(time.time() + 10800))} (TR)"
                           + (f'\n🔗 <a href="{tg_sender.public_url()}/">Uygulamayı aç</a>' if tg_sender.public_url() else ""), prio=True)
    return {"ok": ok, "dry": tg_sender.dry(), "queue": len(tg_sender.q)}


@app.post("/api/telegram/alarm")
def telegram_alarm(body: dict = Body(...)):
    """İstemci tarafı fiyat alarmı tetiklendi (tür modu BİLDİRİM) → Telegram."""
    sym = "".join(ch for ch in str(body.get("sym") or "").upper() if ch.isalnum())[:12]
    if not sym:
        return {"ok": False}
    ev = {"title": str(body.get("title") or f"🔔 {sym}")[:120], "text": str(body.get("text") or "")[:300], "sym": sym,
          "time": time.strftime("%H:%M:%S", time.gmtime(time.time() + 10800))}
    if not tg_sender.cfg["cats"].get("sinyal", True):
        return {"ok": False, "reason": "sinyal kategorisi kapalı"}
    return {"ok": tg_sender.enqueue("sinyal", tg_sender.fmt_event(ev), key="alarm" + sym + ev["text"])}


@app.post("/api/telegram/clear")
def telegram_clear(request: Request, body: dict = Body(...)):
    _os_guard(request, body)
    tg_sender.cfg.update({"token": None, "chat_id": None})
    tg_sender._save_cfg()
    return {"ok": True, "config": tg_sender.public()}


# Eski OneSignal service worker'ları cihazlarda kendini kaldırsın (SDK artık yok; PWA'nın /sw.js'i etkilenmez)
_OS_KILL_SW = "self.addEventListener('install',()=>self.skipWaiting());self.addEventListener('activate',e=>e.waitUntil(self.registration.unregister()));"


@app.get("/OneSignalSDKWorker.js")
@app.get("/OneSignalSDKUpdaterWorker.js")
@app.get("/push/onesignal/{name}")
def onesignal_removed_sw(name: str = ""):
    return Response(_OS_KILL_SW, media_type="application/javascript; charset=utf-8", headers={"Cache-Control": "no-cache"})


@app.get("/sw.js")
def service_worker():
    """Service Worker at root scope — background alarm notifications when tab hidden."""
    path = STATIC_DIR / "sw.js"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="sw.js missing")
    return FileResponse(
        path,
        media_type="application/javascript; charset=utf-8",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


# ------------------------------------------------------------------ v1.29.0 EN İYİ KOŞULLAR
import app.v129 as _v129   # tek yapılandırma app/eik_config.json → /api/eik · /api/eik/birlesik
app.include_router(_v129.router)
import app.v130 as _v130   # v1.30.0 Olay Listesi (ALARM) → /api/olay/feed · /api/olay/alarms · /api/olay/presets · /api/olay/status
_v130.patch_v124()
app.include_router(_v130.router)
import app.v131 as _v131   # v1.31.0 TRENE ATLA → /api/tren/list · /api/tren/preview · /api/tren/status
app.include_router(_v131.router)
import app.v132 as _v132   # v1.32.0 D-A-K SKORLARI → /api/skor/list · /api/skor/detail · /api/skor/status
app.include_router(_v132.router)
import app.v133 as _v133   # v1.33.0 ALGO DESTEK / DİRENÇ → /api/algo/list · /api/algo/detail · /api/algo/status
app.include_router(_v133.router)
import app.v136 as _v136   # v1.36.0 ORDER BLOCK TARAMASI → /api/ob/list · /api/ob/detail/{sym}
app.include_router(_v136.router)
import app.progress as _progress   # v1.37.0 /api/progress
app.include_router(_progress.router)
import app.v135 as _v135   # v1.35.0 LİNK OPTİMİZASYON → /api/link/status · /api/link/new · /api/link/apikey
app.include_router(_v135.router)
class _StaticGZ:
    """v1.37.0: statik dosyalar (app.js ~740 KB, style.css, index.html) gzip'siz gidiyordu → yalnız bu yollar için gzip
    (JSON uçları zaten _gz_json ile sıkıştırılıyor; akış/SSE uçlarına dokunulmaz). TunnelCounter dışta → sıkıştırılmış bayt sayılır."""

    def __init__(self, app):
        from starlette.middleware.gzip import GZipMiddleware
        self.app = app
        self.gz = GZipMiddleware(app, minimum_size=1024)

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            pth = scope.get("path") or ""
            if pth.startswith("/static/") or pth in ("/", "/sw.js", "/index.html", "/manifest.json"):
                return await self.gz(scope, receive, send)
        return await self.app(scope, receive, send)


app.add_middleware(_StaticGZ)
app.add_middleware(_v135.TunnelCounter)
import app.v134 as _v134   # v1.34.0 AL BUNU · TAVAN ADAYI → /api/albunu/list · /api/albunu/status
app.include_router(_v134.router)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
