"""BIST chart OHLCV via İş Yatırım public chart endpoints (no Yahoo).

Sources:
  - Intraday / hourly: ChartData.aspx/IndexHistoricalAll  (close series → OHLC)
  - Daily+: Data.aspx/HisseTekil  (real high/low/close; open = prev close)

Symbol map: BIST ticker (THYAO, MIATK, …) == İş Yatırım code/hisse/endeks param.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import requests
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

IST = ZoneInfo("Europe/Istanbul")
SOURCE_ID = "isyatirim"
SOURCE_LABEL = "İş Yatırım"

# Public chart endpoints (no login)
_INTRADAY_URL = (
    "https://www.isyatirim.com.tr/_Layouts/15/IsYatirim.Website/Common/"
    "ChartData.aspx/IndexHistoricalAll"
)
_DAILY_URL = (
    "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/"
    "Data.aspx/HisseTekil"
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Referer": "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/default.aspx",
    "X-Requested-With": "XMLHttpRequest",
}

# Native minute periods supported by IndexHistoricalAll
_NATIVE_PERIODS = {1, 5, 60, 1440}

# Chart TF → fetch plan
# src_minutes: native IsYatirim period (minutes); None = daily HisseTekil
# lookback_days: calendar days for from/to
# resample: pandas rule after fetch (None = native)
CHART_FETCH: dict[str, dict[str, Any]] = {
    "1m":  {"src_minutes": 1,    "lookback_days": 10,  "resample": None,   "candle": "1m"},
    "5m":  {"src_minutes": 5,    "lookback_days": 60,  "resample": None,   "candle": "5m"},
    "15m": {"src_minutes": 5,    "lookback_days": 60,  "resample": "15min","candle": "15m"},
    "30m": {"src_minutes": 5,    "lookback_days": 60,  "resample": "30min","candle": "30m"},
    "1h":  {"src_minutes": 60,   "lookback_days": 180, "resample": None,   "candle": "60m"},
    "2h":  {"src_minutes": 60,   "lookback_days": 365, "resample": "2h",   "candle": "2h"},
    "4h":  {"src_minutes": 60,   "lookback_days": 730, "resample": "4h",   "candle": "4h"},
    "1d":  {"src_minutes": None, "lookback_days": 730, "resample": None,   "candle": "1d"},
    "1w":  {"src_minutes": None, "lookback_days": 1825,"resample": "W-FRI","candle": "1wk"},
    "1mo": {"src_minutes": None, "lookback_days": 3650,"resample": "ME",   "candle": "1mo"},
    "1y":  {"src_minutes": None, "lookback_days": 3650,"resample": "YE",   "candle": "1y"},
}

CHART_NOTES = (
    "Grafik mumları İş Yatırım public ChartData/HisseTekil uçlarından gelir "
    "(Yahoo history kullanılmaz). Gün içi seriler kapanış bazlıdır; "
    "OHLC, bar içi kapanışlardan (veya önceki kapanış→open) türetilir. "
    "15m/30m = 5m resample; 2h/4h = 60m resample; 1w/1mo/1y = günlük resample. "
    "Seans ~10:00–18:10 Europe/Istanbul; 5m son mum genelde ~18:00 TR."
)

# Cache TTL
_TTL_INTRADAY = 45.0
_TTL_INTRADAY_OPEN = 30.0
_TTL_DAILY = 600.0


def _session_ttl(tf: str) -> float:
    if tf in ("1d", "1w", "1mo", "1y"):
        return _TTL_DAILY
    try:
        from app.quotes import is_bist_session_open
        if is_bist_session_open():
            return _TTL_INTRADAY_OPEN
    except Exception:
        pass
    return _TTL_INTRADAY


def normalize_symbol(symbol: str) -> str:
    """BIST ticker → İş Yatırım code (identity map, uppercase, strip .IS)."""
    s = (symbol or "").strip().upper()
    if s.endswith(".IS"):
        s = s[:-3]
    return s


_EMPTY_TTL = 20.0   # v1.26.2 boş sonuç önbellek süresi (sn)


def _sane_bars(bars: list[dict]) -> list[dict]:
    """v1.26.2: sıfır/negatif fiyatlı (bozuk) barları at; low < 0 olamaz."""
    out = []
    for b in bars or []:
        try:
            if not (b.get("close") and b["close"] > 0 and (b.get("open") or 0) > 0 and (b.get("high") or 0) > 0 and (b.get("low") or 0) > 0):
                continue
        except Exception:
            continue
        out.append(b)
    return out


class ChartCache:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[tuple[str, str], tuple[float, list[dict]]] = {}

    def get(self, sym: str, tf: str) -> list[dict] | None:
        with self._lock:
            hit = self._data.get((sym, tf))
            if not hit:
                return None
            ts, bars = hit
            age = time.time() - ts
            # v1.26.2: boş sonuç (geçici kaynak hatası) uzun süre önbellekte kalmasın — 1H GUNDG "0 bar" hatası
            if not bars and age > _EMPTY_TTL:
                return None
            if age > _session_ttl(tf):
                return None
            return bars

    def put(self, sym: str, tf: str, bars: list[dict]) -> None:
        with self._lock:
            self._data[(sym, tf)] = (time.time(), bars)


chart_cache = ChartCache()


def _fmt_chart_dt(dt: datetime) -> str:
    """İş Yatırım FormatDateForChartService: YYYYMMDDHHmmss in local wall clock."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    else:
        dt = dt.astimezone(IST)
    return dt.strftime("%Y%m%d%H%M%S")


def _http_get_json(url: str, params: dict | None = None, timeout: float = 25.0) -> Any:
    r = requests.get(url, params=params, headers=_HEADERS, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code} from chart source")
    if not r.content:
        return None
    try:
        return r.json()
    except Exception as e:
        raise RuntimeError(f"JSON parse failed: {e}") from e


def _fetch_close_series(code: str, period_minutes: int, lookback_days: int) -> list[tuple[datetime, float]]:
    """Fetch [ts_ms, close] from IndexHistoricalAll → list of (aware IST dt, close)."""
    if period_minutes not in _NATIVE_PERIODS:
        raise ValueError(f"Unsupported native period: {period_minutes}")
    end = datetime.now(IST)
    start = end - timedelta(days=int(lookback_days))
    params = {
        "period": period_minutes,
        "from": _fmt_chart_dt(start),
        "to": _fmt_chart_dt(end),
        "endeks": code,
    }
    raw = _http_get_json(_INTRADAY_URL, params=params)
    if not raw or not isinstance(raw, dict):
        return []
    data = raw.get("data") or []
    out: list[tuple[datetime, float]] = []
    for row in data:
        try:
            if not isinstance(row, (list, tuple)) or len(row) < 2:
                continue
            ts_ms = float(row[0])
            px = float(row[1])
            if px != px:  # NaN
                continue
            dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=IST)
            out.append((dt, px))
        except Exception:
            continue
    return out


def _fetch_daily_tekil(code: str, lookback_days: int) -> list[dict]:
    """HisseTekil daily bars with real high/low/close; open = previous close."""
    end = datetime.now(IST).date()
    start = end - timedelta(days=int(lookback_days))
    params = {
        "hisse": code,
        "startdate": start.strftime("%d-%m-%Y"),
        "enddate": end.strftime("%d-%m-%Y"),
    }
    raw = _http_get_json(_DAILY_URL, params=params, timeout=30.0)
    if not raw or not isinstance(raw, dict) or not raw.get("ok"):
        return []
    rows = raw.get("value") or []
    # Sort ascending by date
    parsed: list[tuple[datetime, float, float, float, int | None]] = []
    for row in rows:
        try:
            dstr = row.get("HGDG_TARIH") or ""
            # dd-mm-YYYY
            day = datetime.strptime(dstr, "%d-%m-%Y").replace(tzinfo=IST)
            high = float(row["HGDG_MAX"])
            low = float(row["HGDG_MIN"])
            close = float(row["HGDG_KAPANIS"])
            vol_raw = row.get("HG_HACIM") or row.get("HGDG_HACIM")
            vol = int(float(vol_raw)) if vol_raw is not None else None
            parsed.append((day, high, low, close, vol))
        except Exception:
            continue
    parsed.sort(key=lambda x: x[0])
    bars: list[dict] = []
    prev_close: float | None = None
    for day, high, low, close, vol in parsed:
        o = prev_close if prev_close is not None else close
        h = max(o, high, low, close)
        l = min(o, high, low, close)
        # noon IST as unix for daily (stable); date string is calendar day
        ts = day.replace(hour=12, minute=0, second=0)
        bars.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                "time": int(ts.timestamp()),
                "time_ist": day.strftime("%Y-%m-%d"),
                "tz": "Europe/Istanbul",
                "open": o,
                "high": h,
                "low": l,
                "close": close,
                "volume": vol,
            }
        )
        prev_close = close
    return bars


def _closes_to_df(points: list[tuple[datetime, float]]) -> pd.DataFrame:
    """Build OHLCV frame from close series (each bar O=H=L=C=close initially)."""
    if not points:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    idx = pd.DatetimeIndex([p[0] for p in points], tz=IST)
    closes = [p[1] for p in points]
    df = pd.DataFrame(
        {
            "Open": closes,
            "High": closes,
            "Low": closes,
            "Close": closes,
            "Volume": [0.0] * len(closes),
        },
        index=idx,
    )
    # Improve single-bar open: previous close (gap candles)
    if len(df) > 1:
        prev = df["Close"].shift(1)
        df.loc[df.index[1]:, "Open"] = prev.iloc[1:].values
        df["High"] = df[["Open", "Close"]].max(axis=1)
        df["Low"] = df[["Open", "Close"]].min(axis=1)
    return df.sort_index()


def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    cols = {c: agg[c] for c in agg if c in df.columns}
    d = df.sort_index()
    try:
        out = d.resample(rule, label="right", closed="right").agg(cols).dropna(subset=["Close"])
        return out
    except Exception as e:
        logger.warning("resample %s failed: %s", rule, e)
        return d.iloc[0:0]


def _df_to_bars(df: pd.DataFrame, intraday: bool) -> list[dict]:
    out: list[dict] = []
    if df is None or df.empty:
        return out
    for idx, row in df.iterrows():
        try:
            ts = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
            if getattr(ts, "tzinfo", None) is None:
                ts = ts.replace(tzinfo=IST)
            ts_ist = ts.astimezone(IST)

            def _f(col: str) -> float | None:
                if col not in row.index:
                    return None
                v = row[col]
                try:
                    if v != v:
                        return None
                    return float(v)
                except Exception:
                    return None

            o, h, l, c = _f("Open"), _f("High"), _f("Low"), _f("Close")
            v = _f("Volume")
            if c is None:
                continue
            if o is None:
                o = c
            if h is None:
                h = max(o, c)
            if l is None:
                l = min(o, c)
            h = max(o, h, l, c)
            l = min(o, h, l, c)
            date_str = (
                ts_ist.strftime("%Y-%m-%d %H:%M:%S")
                if intraday
                else ts_ist.strftime("%Y-%m-%d")
            )
            vol = int(v) if v is not None and v > 0 else None
            out.append(
                {
                    "date": date_str,
                    "time": int(ts.timestamp()),
                    "time_ist": date_str,
                    "tz": "Europe/Istanbul",
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "volume": vol,
                }
            )
        except Exception:
            continue
    return out


def _daily_bars_to_df(bars: list[dict]) -> pd.DataFrame:
    if not bars:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    rows = []
    idx = []
    for b in bars:
        try:
            day = datetime.strptime(b["date"][:10], "%Y-%m-%d").replace(tzinfo=IST)
            idx.append(day)
            rows.append(
                {
                    "Open": b["open"],
                    "High": b["high"],
                    "Low": b["low"],
                    "Close": b["close"],
                    "Volume": float(b["volume"] or 0),
                }
            )
        except Exception:
            continue
    if not rows:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    return pd.DataFrame(rows, index=pd.DatetimeIndex(idx, tz=IST)).sort_index()


def fetch_chart_history(
    symbol: str,
    period: str = "5m",
    force: bool = False,
) -> tuple[list[dict], dict[str, Any]]:
    """Fetch chart bars for a CHART_FETCH key.

    Returns (bars, meta). Meta always includes source / error info for API.
    Never raises to caller for empty data — returns [] + error note.
    """
    aliases = {
        "60m": "1h",
        "1wk": "1w",
        "1hafta": "1w",
        "hafta": "1w",
        "1mth": "1mo",
        "month": "1mo",
        "year": "1y",
    }
    raw = (period or "5m").strip()
    # Distinguish 1M (month) from 1m (minute) before lowercasing
    if raw in ("1M", "1Mo", "1MO"):
        key = "1mo"
    elif raw in ("1Y", "1y", "year"):
        key = "1y"
    else:
        key = aliases.get(raw.lower(), raw.lower())

    meta: dict[str, Any] = {
        "source": SOURCE_ID,
        "source_label": SOURCE_LABEL,
        "period": key,
        "symbol": None,
        "provider_code": None,
        "error": None,
        "notes": CHART_NOTES,
    }

    code = normalize_symbol(symbol)
    meta["symbol"] = code
    meta["provider_code"] = code
    if not code:
        meta["error"] = "empty symbol"
        return [], meta

    spec = CHART_FETCH.get(key)
    if not spec:
        meta["error"] = f"unsupported period: {period}"
        return [], meta

    meta["candle"] = spec["candle"]
    meta["resample"] = spec.get("resample")
    meta["lookback_days"] = spec["lookback_days"]
    meta["src_minutes"] = spec["src_minutes"]

    if not force:
        hit = chart_cache.get(code, key)
        if hit is not None:
            meta["cache"] = "hit"
            return hit, meta

    meta["cache"] = "miss"
    bars, meta = _fetch_once(code, key, spec, meta)
    if not bars:
        # v1.26.2: kaynak geçici olarak boş döndüyse bir kez daha dene (boş sonuç yalnız ~20 sn önbellekte kalır)
        time.sleep(0.6)
        meta.pop("error", None)
        meta["retry"] = 1
        bars, meta = _fetch_once(code, key, spec, meta)
    n0 = len(bars)
    bars = _sane_bars(bars)
    if n0 != len(bars):
        meta["dropped_bad"] = n0 - len(bars)
    chart_cache.put(code, key, bars)
    meta["bar_count"] = len(bars)
    if bars:
        meta["first_bar"] = bars[0].get("date")
        meta["last_bar"] = bars[-1].get("date")
    return bars, meta


def _fetch_once(code, key, spec, meta):
    try:
        if spec["src_minutes"] is None:
            daily = _fetch_daily_tekil(code, spec["lookback_days"])
            if not daily:
                meta["error"] = "no daily data from HisseTekil"
                return [], meta
            rule = spec.get("resample")
            if rule:
                df = _daily_bars_to_df(daily)
                df = _resample_ohlcv(df, rule)
                bars = _df_to_bars(df, intraday=False)
            else:
                bars = daily
        else:
            points = _fetch_close_series(code, int(spec["src_minutes"]), int(spec["lookback_days"]))
            if not points:
                meta["error"] = "no intraday data from IndexHistoricalAll"
                return [], meta
            df = _closes_to_df(points)
            rule = spec.get("resample")
            if rule:
                df = _resample_ohlcv(df, rule)
            bars = _df_to_bars(df, intraday=True)
    except Exception as e:
        logger.warning("chart_provider %s %s: %s", code, key, e)
        meta["error"] = str(e)
        # Do not cache hard failures for long — short empty cache to avoid stampede
        return [], meta
    return bars, meta


def provider_info() -> dict[str, Any]:
    return {
        "source": SOURCE_ID,
        "source_label": SOURCE_LABEL,
        "notes": CHART_NOTES,
        "symbol_map": "BIST ticker == IsYatirim code (THYAO → THYAO)",
        "endpoints": {
            "intraday": _INTRADAY_URL,
            "daily": _DAILY_URL,
        },
        "timeframes": {k: {kk: vv for kk, vv in v.items()} for k, v in CHART_FETCH.items()},
    }
