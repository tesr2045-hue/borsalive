"""Yahoo Finance quote fetcher for BIST (.IS) tickers — batch quotes + RVOL + history."""
from __future__ import annotations

import logging
import threading
import time
import warnings
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from curl_cffi import requests as creq

logger = logging.getLogger(__name__)

IST = ZoneInfo("Europe/Istanbul")
# Adaptive quote cache: tight while BIST continuous session open, looser when closed.
QUOTE_CACHE_TTL = 60.0  # legacy default / closed fallback
QUOTE_CACHE_TTL_OPEN = 6.0   # aggressive while session open (Yahoo still delayed)
QUOTE_CACHE_TTL_CLOSED = 60.0  # closed: slower pull; UI must not look like live lag
PREV_VOL_CACHE_TTL = 6 * 3600.0  # previous-session volumes stable within a day
BATCH_SIZE = 80
PREV_VOL_BATCH = 80

# BIST cash equity continuous trading (Europe/Istanbul): 10:00–18:10 weekdays.
# Close is 18:10 TR — NOT 17:00 / 17:30 / 18:00. Minute 18:10 still open; 18:11 closed.
BIST_OPEN_MIN = 10 * 60          # 10:00
BIST_CLOSE_MIN = 18 * 60 + 10    # 18:10

YAHOO_DELAY_NOTE = (
    "Yahoo Finance BIST (.IS) kotasyonları genelde gecikmeli olabilir "
    "(resmi BIST seviye-1 değil). Canlı yenileme agresif olsa da kaynak gecikmesi kalır; "
    "alarm / RVOL kararlarını buna göre yorumlayın."
)


def is_bist_session_open(now: datetime | None = None) -> bool:
    """True during BIST cash equity continuous trading (Europe/Istanbul).

    Regular session: weekdays 10:00–18:10 local (inclusive through 18:10).
    Closed from 18:11, weekends; holidays optional via Yahoo CLOSED override.
    """
    now = now or datetime.now(IST)
    if now.tzinfo is None:
        now = now.replace(tzinfo=IST)
    else:
        now = now.astimezone(IST)
    if now.weekday() >= 5:
        return False
    mins = now.hour * 60 + now.minute
    return BIST_OPEN_MIN <= mins <= BIST_CLOSE_MIN

# Quote fields (avg volumes kept for reference display; RVOL uses previous session)
QUOTE_FIELDS = (
    "symbol,shortName,longName,regularMarketPrice,regularMarketPreviousClose,"
    "regularMarketChange,regularMarketChangePercent,regularMarketVolume,"
    "regularMarketDayHigh,regularMarketDayLow,regularMarketOpen,"
    "averageDailyVolume3Month,averageDailyVolume10Day,"
    "currency,regularMarketTime,marketState,quoteType"
)

# Chart timeframe presets → candle SIZE (UI button = bar duration), not lookback range.
# Each key is what one candle represents. Yahoo period sized long enough for indicators.
# resample: optional pandas rule applied after fetch (2h/4h from 60m; 1y from 1mo).
CHART_PRESETS: dict[str, dict[str, str]] = {
    # Chart candles from İş Yatırım (see app.chart_provider) — NOT Yahoo history.
    # "period" here = lookback hint for UI/meta; "interval" = source native TF.
    # Times are Europe/Istanbul (frontend IST formatters from v1.10.5 kept).
    "1m":  {"period": "10d",  "interval": "1m",  "candle": "1m"},
    "5m":  {"period": "60d",  "interval": "5m",  "candle": "5m"},
    "15m": {"period": "60d",  "interval": "5m",  "candle": "15m", "resample": "15min"},
    "30m": {"period": "60d",  "interval": "5m",  "candle": "30m", "resample": "30min"},
    "1h":  {"period": "180d", "interval": "60m", "candle": "60m"},
    "2h":  {"period": "365d", "interval": "60m", "candle": "2h",  "resample": "2h"},
    "4h":  {"period": "730d", "interval": "60m", "candle": "4h",  "resample": "4h"},
    "1d":  {"period": "2y",   "interval": "1d",  "candle": "1d"},
    "1w":  {"period": "5y",   "interval": "1d",  "candle": "1wk", "resample": "W-FRI"},
    "1mo": {"period": "10y",  "interval": "1d",  "candle": "1mo", "resample": "ME"},
    "1y":  {"period": "10y",  "interval": "1d",  "candle": "1y",  "resample": "YE"},
}
ALLOWED_PERIODS = set(CHART_PRESETS.keys())

# Back-compat alias used by main.py
PERIOD_INTERVAL = {k: v["interval"] for k, v in CHART_PRESETS.items()}

CHART_TF_DOC = (
    "UI mum boyutu eşlemesi (buton → mum süresi): "
    "1 dakika→1m, 5 dakika→5m, 15 dakika→15m (5m resample), 30 dakika→30m (5m resample), "
    "1 saat→60m, 2 saat→60m resample 2h, 4 saat→60m resample 4h, "
    "1 gün→1d (HisseTekil), 1 hafta→1d resample W-FRI, 1 ay→1d resample ME, "
    "1 yıl→1d resample YE. Kaynak: İş Yatırım ChartData/HisseTekil (Yahoo history yok). "
    "Eski hata: 1G yanlışlıkla 5m göstermemeli — 1d her zaman günlük mum."
)

YAHOO_INTRADAY_NOTES = (
    "Kotasyon/tarayıcı hâlâ Yahoo Finance BIST (.IS) kullanabilir (gecikmeli). "
    "Grafik mumları v1.11+ İş Yatırım public uçlarından gelir — Yahoo history kullanılmaz. "
    "Gün içi: 1m≈10g, 5m≈60g, 60m≈aylar; 15m/30m=5m resample; 2h/4h=60m resample. "
    "Günlük+: HisseTekil OHLC (open≈önceki kapanış). Seans 10:00–18:10 Europe/Istanbul."
)

CHART_SOURCE = "isyatirim"
CHART_SOURCE_LABEL = "İş Yatırım"


RVOL_DEF = (
    "rvol = today_volume / previous_session_volume "
    "(önceki işlem günü hacmi; yoksa veya 0 ise null)"
)
RVOL10_DEF = (
    "rvol10 = today_volume / mean(volume of last 10 trading days before today) "
    "(günlük barlar; avg yok/0 ise null)"
)
RVOL_DEFS = {"rvol": RVOL_DEF, "rvol10": RVOL10_DEF}


def _sanitize_ohlc(o: float | None, h: float | None, l: float | None, c: float | None) -> tuple[float | None, float | None, float | None, float | None] | None:
    """Repair/drop absurd OHLC that create tall spike candles on the chart.

    Returns None to drop the bar; otherwise (o,h,l,c) with high/low consistent.
    """
    if c is None:
        return None
    if o is None:
        o = c
    if h is None:
        h = max(o, c)
    if l is None:
        l = min(o, c)
    # Force OHLC consistency
    hi = max(o, h, l, c)
    lo = min(o, h, l, c)
    # Drop absurd intraday spikes (bad merge / bad adjust): range > 40% of close
    # or high/low wildly off close. Daily/weekly gaps can be large — caller decides.
    if c != 0 and (hi - lo) / abs(c) > 0.45:
        return None
    if c != 0 and (hi > abs(c) * 1.45 or lo < abs(c) * 0.55):
        return None
    return (float(o), float(hi), float(lo), float(c))


class QuoteService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._session: creq.Session | None = None
        self._crumb: str | None = None
        self._crumb_ts: float = 0.0
        self._cache: list[dict[str, Any]] | None = None
        self._cache_ts: float = 0.0
        self._cache_error: str | None = None
        self._name_map: dict[str, str] = {}
        # yahoo_symbol -> previous session volume
        self._prev_vol: dict[str, int] = {}
        self._avg10_vol: dict[str, float] = {}
        self._prev_vol_ts: float = 0.0

    def set_name_map(self, symbols: list[dict]) -> None:
        self._name_map = {
            s["symbol"]: s.get("name") or ""
            for s in symbols
            if s.get("symbol")
        }

    def is_market_open(self) -> bool:
        """BIST open/closed: Europe/Istanbul clock is authoritative after close.

        Continuous cash equities: 10:00–18:10 weekdays. After 18:10 / weekends
        always CLOSED — Yahoo market_state must NEVER force OPEN (stale REGULAR
        or POST used to keep the UI live past 18:10).

        When the clock says open, majority Yahoo CLOSED can still force closed
        (exchange holiday).
        """
        clock_open = is_bist_session_open()
        if not clock_open:
            return False
        quotes = self._cache or []
        if quotes:
            states = [(q.get("market_state") or "").upper() for q in quotes]
            # Only treat true continuous / open states as live (not POST)
            live = sum(1 for s in states if s in ("REGULAR", "OPEN", "PRE", "PREPRE"))
            closed = sum(1 for s in states if s in ("CLOSED", "PREPRECLOSE"))
            # Holiday: clock open but majority clearly CLOSED
            if closed > live and closed > len(quotes) * 0.55:
                return False
        return True

    def quote_cache_ttl(self) -> float:
        return QUOTE_CACHE_TTL_OPEN if self.is_market_open() else QUOTE_CACHE_TTL_CLOSED

    def cache_meta(self) -> dict[str, Any]:
        age = (time.time() - self._cache_ts) if self._cache_ts else None
        open_ = self.is_market_open()
        return {
            "market_open": open_,
            "session_label": "açık" if open_ else "kapalı",
            "session_hours": "10:00–18:10 Europe/Istanbul",
            "cache_ttl_sec": self.quote_cache_ttl(),
            "cache_age_sec": round(age, 1) if age is not None else None,
            "cache_count": len(self._cache or []),
            "yahoo_delay_note": YAHOO_DELAY_NOTE,
            # UI poll hint: open = near-instant; closed = meta only (not "live lag")
            "refresh_hint_sec": 4 if open_ else 60,
            "frontend_refresh_open_sec": 4,
            "frontend_refresh_closed_sec": 60,
        }

    def _ensure_session(self) -> tuple[creq.Session, str]:
        now = time.time()
        if self._session and self._crumb and (now - self._crumb_ts) < 3600:
            return self._session, self._crumb

        session = creq.Session(impersonate="chrome")
        try:
            session.get("https://fc.yahoo.com", timeout=15)
        except Exception:
            pass
        r = session.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=15)
        r.raise_for_status()
        crumb = r.text.strip()
        if not crumb or "html" in crumb.lower():
            raise RuntimeError("Yahoo crumb alınamadı")
        self._session = session
        self._crumb = crumb
        self._crumb_ts = now
        return session, crumb

    def _fetch_batch(self, yahoo_symbols: list[str]) -> list[dict]:
        session, crumb = self._ensure_session()
        url = "https://query1.finance.yahoo.com/v7/finance/quote"
        params = {
            "symbols": ",".join(yahoo_symbols),
            "fields": QUOTE_FIELDS,
            "crumb": crumb,
        }
        r = session.get(url, params=params, timeout=45)
        if r.status_code in (401, 403):
            self._crumb = None
            session, crumb = self._ensure_session()
            params["crumb"] = crumb
            r = session.get(url, params=params, timeout=45)
        r.raise_for_status()
        data = r.json()
        return data.get("quoteResponse", {}).get("result") or []

    def _session_date(self, raw: dict) -> date:
        mtime = raw.get("regularMarketTime")
        if isinstance(mtime, (int, float)):
            return datetime.fromtimestamp(mtime, tz=timezone.utc).astimezone(IST).date()
        return datetime.now(IST).date()

    def _normalize(
        self,
        raw: dict,
        prev_vol: int | None = None,
        avg10_vol: float | None = None,
    ) -> dict[str, Any] | None:
        yahoo = raw.get("symbol") or ""
        qtype = (raw.get("quoteType") or "").upper()
        if qtype and qtype not in ("EQUITY", ""):
            return None

        if yahoo.endswith(".IS"):
            symbol = yahoo[:-3]
        else:
            symbol = yahoo.replace(".IS", "")

        price = raw.get("regularMarketPrice")
        if price is None:
            return None

        prev = raw.get("regularMarketPreviousClose")
        change_pct = raw.get("regularMarketChangePercent")
        if change_pct is None and price is not None and prev:
            change_pct = ((price - prev) / prev) * 100.0

        volume = raw.get("regularMarketVolume")
        avg3 = raw.get("averageDailyVolume3Month")
        avg10_yahoo = raw.get("averageDailyVolume10Day")
        avg_volume = None
        if avg3 is not None and float(avg3) > 0:
            avg_volume = int(avg3)
        elif avg10_yahoo is not None and float(avg10_yahoo) > 0:
            avg_volume = int(avg10_yahoo)

        ykey = yahoo if yahoo.endswith(".IS") else f"{symbol}.IS"
        if prev_vol is None:
            prev_vol = self._prev_vol.get(ykey)
        if avg10_vol is None:
            avg10_vol = self._avg10_vol.get(ykey)

        # rvol = today / previous session
        rvol = None
        if volume is not None and prev_vol is not None and prev_vol > 0:
            rvol = float(volume) / float(prev_vol)

        # rvol10 = today / avg of last 10 trading days (exclude today)
        rvol10 = None
        if volume is not None and avg10_vol is not None and avg10_vol > 0:
            rvol10 = float(volume) / float(avg10_vol)

        local_name = self._name_map.get(symbol) or ""
        yahoo_name = raw.get("shortName") or raw.get("longName") or ""
        display_name = local_name or yahoo_name

        mtime = raw.get("regularMarketTime")
        if isinstance(mtime, (int, float)):
            updated = datetime.fromtimestamp(mtime, tz=timezone.utc).astimezone(IST)
            updated_str = updated.strftime("%Y-%m-%d %H:%M:%S")
            session_date = updated.date().isoformat()
        else:
            updated_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
            session_date = datetime.now(IST).date().isoformat()

        def _optf(key: str) -> float | None:
            v = raw.get(key)
            if v is None:
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        item = {
            "symbol": symbol,
            "yahoo": yahoo if yahoo.endswith(".IS") else f"{symbol}.IS",
            "name": display_name,
            "price": float(price) if price is not None else None,
            "previous_close": float(prev) if prev is not None else None,
            "change": float(raw["regularMarketChange"]) if raw.get("regularMarketChange") is not None else None,
            "change_pct": float(change_pct) if change_pct is not None else None,
            "day_high": _optf("regularMarketDayHigh"),
            "day_low": _optf("regularMarketDayLow"),
            "day_open": _optf("regularMarketOpen"),
            "volume": int(volume) if volume is not None else None,
            "prev_volume": int(prev_vol) if prev_vol is not None else None,
            "avg10_volume": int(avg10_vol) if avg10_vol is not None else None,
            "avg_volume": avg_volume,  # Yahoo 3M/10D informational
            "rvol": round(rvol, 3) if rvol is not None else None,
            "rvol10": round(rvol10, 3) if rvol10 is not None else None,
            "currency": raw.get("currency") or "TRY",
            "updated": updated_str,
            "session_date": session_date,
            "market_state": raw.get("marketState"),
        }
        # v1.16.0: live İdealData last/volume/high/low override (Yahoo stays as fallback)
        try:
            from app.ideal_feed import ideal_feed

            item = ideal_feed.overlay_quote(item)
        except Exception as e:  # never break quotes
            logger.debug("ideal overlay %s: %s", symbol, e)
            item.setdefault("price_source", "yahoo")
        return item

    def _fetch_daily_vol_stats(
        self, yahoo_symbols: list[str], session_dates: dict[str, date]
    ) -> tuple[dict[str, int], dict[str, float]]:
        """Previous-session vol + avg of last 10 trading days before session_date."""
        import pandas as pd
        import yfinance as yf

        prev_out: dict[str, int] = {}
        avg10_out: dict[str, float] = {}
        if not yahoo_symbols:
            return prev_out, avg10_out

        logging.getLogger("yfinance").setLevel(logging.CRITICAL)

        for i in range(0, len(yahoo_symbols), PREV_VOL_BATCH):
            batch = yahoo_symbols[i : i + PREV_VOL_BATCH]
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    # threads=False: threads=True can hang forever on Yahoo (v1.13.2)
                    df = yf.download(
                        batch,
                        period="1mo",
                        interval="1d",
                        group_by="ticker",
                        threads=False,
                        progress=False,
                        auto_adjust=True,
                    )
            except Exception as e:
                logger.warning("daily vol batch failed: %s", e)
                continue

            if df is None or df.empty:
                continue

            def _extract(ysym: str, sub: "pd.DataFrame") -> None:
                if sub is None or sub.empty or "Volume" not in sub.columns:
                    return
                rows: list[tuple[date, int]] = []
                for idx, v in sub["Volume"].items():
                    try:
                        if v != v or v is None or float(v) <= 0:
                            continue
                        d = idx.date() if hasattr(idx, "date") else idx
                        rows.append((d, int(v)))
                    except Exception:
                        continue
                if not rows:
                    return
                rows.sort(key=lambda x: x[0])
                sess = session_dates.get(ysym) or datetime.now(IST).date()
                before = [(d, vol) for d, vol in rows if d < sess]
                if not before:
                    return
                prev_out[ysym] = before[-1][1]
                last10 = before[-10:]
                if last10:
                    avg10_out[ysym] = sum(v for _, v in last10) / len(last10)

            if isinstance(df.columns, pd.MultiIndex):
                level0 = set(df.columns.get_level_values(0).unique())
                for ysym in batch:
                    if ysym not in level0:
                        continue
                    _extract(ysym, df[ysym].dropna(how="all"))
            else:
                if len(batch) == 1:
                    _extract(batch[0], df)

        return prev_out, avg10_out

    def _ensure_prev_volumes(self, items: list[tuple[str, date]], force: bool = False) -> None:
        """Refresh cached previous-session + 10-day avg volumes."""
        now = time.time()
        if (
            not force
            and self._prev_vol
            and (now - self._prev_vol_ts) < PREV_VOL_CACHE_TTL
        ):
            missing = [
                y for y, _ in items
                if y not in self._prev_vol or y not in self._avg10_vol
            ]
            if not missing:
                return
            sess_map = {y: d for y, d in items if y in missing}
            prev_f, avg_f = self._fetch_daily_vol_stats(list(sess_map.keys()), sess_map)
            self._prev_vol.update(prev_f)
            self._avg10_vol.update(avg_f)
            return

        sess_map = {y: d for y, d in items}
        prev_f, avg_f = self._fetch_daily_vol_stats(list(sess_map.keys()), sess_map)
        if prev_f or avg_f or not self._prev_vol:
            if prev_f:
                self._prev_vol = prev_f
            if avg_f:
                self._avg10_vol = avg_f
            self._prev_vol_ts = now

    # v1.37.0: stale-while-revalidate — bayat önbellek (bellek ya da disk) HEMEN döner, yenileme arka planda.
    _SWR_FILE = Path(__file__).resolve().parents[1] / "data" / "v137" / "quotes_cache.json"

    def fetch_all(self, symbols: list[dict], force: bool = False) -> tuple[list[dict], str | None]:
        if force:
            return self._fetch_all_sync(symbols, True)
        if self._cache is None and not getattr(self, "_swr_disk", False):
            self._swr_disk = True
            try:
                import json as _j
                d = _j.loads(self._SWR_FILE.read_text(encoding="utf-8"))
                if d.get("rows") and self._cache is None:
                    self._cache, self._cache_ts, self._cache_error = d["rows"], 0.0, d.get("err")
            except Exception:
                pass
        if self._cache is None:
            return self._fetch_all_sync(symbols, False)
        if (time.time() - self._cache_ts) >= self.quote_cache_ttl():
            th = getattr(self, "_swr_th", None)
            if th is None or not th.is_alive():
                def _bg():
                    try:
                        self._fetch_all_sync(symbols, False)
                    except Exception as e:  # pragma: no cover
                        logger.warning("SWR quote refresh: %s", e)
                self._swr_th = threading.Thread(target=_bg, daemon=True, name="quotes-swr")
                self._swr_th.start()
        return self._cache, self._cache_error

    def _fetch_all_sync(self, symbols: list[dict], force: bool = False) -> tuple[list[dict], str | None]:
        """Return (quotes, error). Adaptive TTL: ~6s open / ~60s closed unless force=True."""
        from app import progress as PG
        with self._lock:
            now = time.time()
            ttl = self.quote_cache_ttl()
            if (
                not force
                and self._cache is not None
                and (now - self._cache_ts) < ttl
            ):
                return self._cache, self._cache_error

            yahoo_list = [s["yahoo"] for s in symbols if s.get("yahoo")]
            raw_by_yahoo: dict[str, dict] = {}
            errors: list[str] = []

            PG.begin("lite", len(yahoo_list), "Fiyatlar (Yahoo) yükleniyor")
            for i in range(0, len(yahoo_list), BATCH_SIZE):
                PG.step("lite", done=i)
                batch = yahoo_list[i : i + BATCH_SIZE]
                try:
                    raw_list = self._fetch_batch(batch)
                    for raw in raw_list:
                        y = raw.get("symbol") or ""
                        if y:
                            raw_by_yahoo[y] = raw
                except Exception as e:
                    msg = f"batch {i // BATCH_SIZE + 1}: {e}"
                    logger.warning("Quote batch failed: %s", msg)
                    errors.append(msg)
                    self._crumb = None
                    time.sleep(0.5)

            # Session dates for prev-volume lookup
            sess_items: list[tuple[str, date]] = []
            for y, raw in raw_by_yahoo.items():
                if raw.get("regularMarketPrice") is None:
                    continue
                sess_items.append((y, self._session_date(raw)))

            try:
                self._ensure_prev_volumes(sess_items, force=force)
            except Exception as e:
                logger.warning("prev volume enrich failed: %s", e)
                errors.append(f"prev_vol: {e}")

            results: list[dict] = []
            for y, raw in raw_by_yahoo.items():
                item = self._normalize(raw, prev_vol=self._prev_vol.get(y), avg10_vol=self._avg10_vol.get(y))
                if item:
                    results.append(item)

            # v1.16.0: BIST shares Yahoo does not return → live İdealData-only items (BISTTÜM)
            try:
                from app.ideal_feed import ideal_feed

                extra = ideal_feed.extra_quotes(
                    {r["symbol"] for r in results}, self._name_map, self._prev_vol, self._avg10_vol
                )
                if extra:
                    results.extend(extra)
            except Exception as e:  # never break quotes
                logger.debug("ideal extra quotes: %s", e)

            err = "; ".join(errors) if errors else None
            PG.end("lite", err if not results else None)
            if results:
                results.sort(key=lambda x: x["symbol"])
                self._cache = results
                self._cache_ts = now
                try:
                    import json as _j
                    self._SWR_FILE.parent.mkdir(parents=True, exist_ok=True)
                    tmp = self._SWR_FILE.with_suffix(".tmp")
                    tmp.write_text(_j.dumps({"ts": now, "rows": results, "err": err}, default=str), encoding="utf-8")
                    tmp.replace(self._SWR_FILE)
                except Exception as e:
                    logger.debug("SWR disk: %s", e)
                self._cache_error = err
            elif self._cache is not None:
                self._cache_error = err or "Yahoo'dan veri alınamadı"
                return self._cache, self._cache_error
            else:
                self._cache_error = err or "Yahoo'dan veri alınamadı"

            return results, self._cache_error

    def fetch_one(self, symbol: str) -> dict | None:
        sym = symbol.upper().replace(".IS", "")
        yahoo = f"{sym}.IS"
        try:
            raw_list = self._fetch_batch([yahoo])
            if not raw_list:
                return None
            raw = raw_list[0]
            sess = self._session_date(raw)
            if yahoo not in self._prev_vol:
                try:
                    self._ensure_prev_volumes([(yahoo, sess)])
                except Exception as e:
                    logger.warning("fetch_one prev_vol %s: %s", yahoo, e)
            return self._normalize(raw, prev_vol=self._prev_vol.get(yahoo), avg10_vol=self._avg10_vol.get(yahoo))
        except Exception as e:
            logger.warning("fetch_one %s failed: %s", yahoo, e)
            return None

    @staticmethod
    def _resample_ohlcv(df, rule: str):
        """Aggregate OHLCV to larger bars (2h/4h/YS)."""
        import pandas as pd

        if df is None or df.empty:
            return df
        agg = {
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum",
        }
        cols = {c: agg[c] for c in agg if c in df.columns}
        if not cols:
            return df.iloc[0:0]
        d = df.sort_index()
        try:
            # Year-start for yearly candles; otherwise standard resample
            if rule in ("YS", "AS", "1Y", "Y"):
                return d.resample("YS").agg(cols).dropna(subset=["Close"])
            return d.resample(rule, label="right", closed="right").agg(cols).dropna(subset=["Close"])
        except Exception:
            return d.iloc[0:0]

    def history(
        self,
        symbol: str,
        period: str = "1d",
        interval: str | None = None,
    ) -> list[dict]:
        """OHLCV for charts via İş Yatırım (app.chart_provider) — not Yahoo.

        `period` is a CHART_PRESETS candle-size key (1m…1y).
        `interval` is ignored (kept for API compat); provider picks native TF.
        """
        from app.chart_provider import fetch_chart_history

        _ = interval  # API compat; provider owns interval selection
        bars, meta = fetch_chart_history(symbol, period=period, force=False)
        # Stash last meta for stock_detail / debugging
        self._last_chart_meta = meta
        if meta.get("error") and not bars:
            logger.warning(
                "chart history %s %s: %s",
                symbol,
                period,
                meta.get("error"),
            )
        return bars

    def last_chart_meta(self) -> dict:
        return getattr(self, "_last_chart_meta", None) or {
            "source": CHART_SOURCE,
            "source_label": CHART_SOURCE_LABEL,
        }

    @staticmethod
    def top_movers(quotes: list[dict], kind: str, limit: int = 20) -> list[dict]:
        """kind: gainers | losers | volume | rvol | rvol10"""
        limit = max(1, min(int(limit or 20), 100))
        kind = (kind or "").lower()

        if kind == "gainers":
            pool = [q for q in quotes if q.get("change_pct") is not None]
            pool.sort(key=lambda q: q["change_pct"], reverse=True)
        elif kind == "losers":
            pool = [q for q in quotes if q.get("change_pct") is not None]
            pool.sort(key=lambda q: q["change_pct"])
        elif kind == "volume":
            pool = [q for q in quotes if q.get("volume") is not None]
            pool.sort(key=lambda q: q["volume"], reverse=True)
        elif kind == "rvol":
            pool = [q for q in quotes if q.get("rvol") is not None]
            pool.sort(key=lambda q: q["rvol"], reverse=True)
        elif kind == "rvol10":
            pool = [q for q in quotes if q.get("rvol10") is not None]
            pool.sort(key=lambda q: q["rvol10"], reverse=True)
        else:
            return []
        return pool[:limit]


quote_service = QuoteService()
