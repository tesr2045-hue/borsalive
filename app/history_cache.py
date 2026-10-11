"""Aggressive OHLCV history cache + Yahoo interval helpers (resample 2h/4h/1w)."""
from __future__ import annotations

import logging
import threading
import time
import warnings
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from zoneinfo import ZoneInfo

IST = ZoneInfo("Europe/Istanbul")

logger = logging.getLogger(__name__)

# Legacy N kept for API compat; formula no longer uses mean of N bars
RVOL_TF_N = 20  # unused by rvol_from_bars (prev-bar ratio)
RVOL10_TF_N = 10  # last ÷ mean(prev ≤10 bars) per TF

# Scanner / TF coverage: top volume names first
SCANNER_UNIVERSE_LIMIT = 150
RVOL_TF_TABLE_LIMIT = 40

TF_INTERVALS = ("1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w")

# How we fetch each logical TF from Yahoo
# period sized to yield >= N+1 bars when market has data
TF_FETCH: dict[str, dict[str, str]] = {
    # Aligned with CHART_PRESETS: enough bars for full BIST session day + context
    "1m": {"period": "7d", "interval": "1m"},
    "5m": {"period": "60d", "interval": "5m"},
    "15m": {"period": "60d", "interval": "15m"},
    "30m": {"period": "60d", "interval": "30m"},
    "1h": {"period": "3mo", "interval": "60m"},
    "2h": {"period": "6mo", "interval": "60m"},  # resample 2×60m
    "4h": {"period": "1y", "interval": "60m"},  # resample 4×60m
    "1d": {"period": "3mo", "interval": "1d"},
    "1w": {"period": "2y", "interval": "1d"},  # resample weekly
}

RVOL_TF_DEF = (
    "rvol_tf = last_bar.volume / previous_bar.volume (same TF; son mum ÷ önceki mum). "
    "rvol10_tf = last_bar.volume / mean(volume of up to 10 prior bars, same TF). "
    "change_pct = (last.close - prev.close) / prev.close * 100 "
    "(son mum kapanışı ÷ bir önceki mum kapanışı). "
    "2h/4h = 60m bars resampled; 1w = 1d bars resampled to week. "
    "Null if prev volume missing/0 or fewer than 2 bars."
)

HIST_TTL_INTRADAY = 120.0  # 2 min closed fallback
HIST_TTL_INTRADAY_OPEN = 35.0  # tighter while market open
HIST_TTL_DAILY = 900.0  # 15 min for daily/weekly


class HistoryCache:
    """Thread-safe OHLCV cache keyed by (yahoo, logical_tf)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # (yahoo, tf) -> (ts, list[dict])
        self._cache: dict[tuple[str, str], tuple[float, list[dict]]] = {}

    def _ttl(self, tf: str) -> float:
        if tf in ("1d", "1w"):
            return HIST_TTL_DAILY
        try:
            from app.quotes import is_bist_session_open
            if is_bist_session_open():
                return HIST_TTL_INTRADAY_OPEN
        except Exception:
            pass
        return HIST_TTL_INTRADAY

    def get(self, yahoo: str, tf: str) -> list[dict] | None:
        with self._lock:
            hit = self._cache.get((yahoo, tf))
            if not hit:
                return None
            ts, bars = hit
            if time.time() - ts > self._ttl(tf):
                return None
            return bars

    def put(self, yahoo: str, tf: str, bars: list[dict]) -> None:
        with self._lock:
            self._cache[(yahoo, tf)] = (time.time(), bars)

    def clear_stale(self) -> None:
        now = time.time()
        with self._lock:
            dead = [
                k
                for k, (ts, _) in self._cache.items()
                if now - ts > self._ttl(k[1]) * 2
            ]
            for k in dead:
                del self._cache[k]


history_cache = HistoryCache()


def _bars_from_df(df: pd.DataFrame, intraday: bool) -> list[dict]:
    out: list[dict] = []
    if df is None or df.empty:
        return out
    for idx, row in df.iterrows():
        try:
            ts = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
            if getattr(ts, "tzinfo", None) is None:
                ts = ts.replace(tzinfo=timezone.utc)
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
            date_str = (
                ts_ist.strftime("%Y-%m-%d %H:%M:%S")
                if intraday
                else ts_ist.strftime("%Y-%m-%d")
            )
            out.append(
                {
                    "date": date_str,
                    "time": int(ts.timestamp()),
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "volume": int(v) if v is not None else None,
                }
            )
        except Exception:
            continue
    return out


def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample Yahoo OHLCV to larger bars (2h/4h/1W)."""
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
    # Yahoo index may be tz-aware; resample needs sorted index
    d = df.sort_index()
    try:
        return d.resample(rule, label="right", closed="right").agg(cols).dropna(subset=["Close"])
    except Exception:
        return d.iloc[0:0]


def fetch_bars(
    yahoo: str,
    tf: str,
    force: bool = False,
    timeout_sec: float = 12.0,
    period_override: str | None = None,
) -> list[dict]:
    """Fetch (or cache-hit) OHLCV bars for a logical timeframe.

    Hardening (v1.13.2): wall-clock timeout around yfinance history — bare
    Ticker.history() can hang forever (same class as threads=True batch hang).
    """
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

    tf = (tf or "15m").lower()
    if tf not in TF_FETCH:
        return []
    if not force:
        hit = history_cache.get(yahoo, tf)
        if hit is not None:
            return hit

    import yfinance as yf

    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    spec = TF_FETCH[tf]
    y_interval = spec["interval"]
    y_period = period_override or spec["period"]

    def _hist():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            t = yf.Ticker(yahoo)
            return t.history(period=y_period, interval=y_interval, auto_adjust=True)

    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_hist)
            df = fut.result(timeout=max(2.0, float(timeout_sec or 12.0)))
    except FuturesTimeout:
        logger.warning("history %s %s timeout (%.1fs)", yahoo, tf, timeout_sec)
        # do not cache empty on timeout — allow retry / İş Yatırım fallback
        return []
    except Exception as e:
        logger.warning("history %s %s: %s", yahoo, tf, e)
        history_cache.put(yahoo, tf, [])
        return []

    if df is None or df.empty:
        history_cache.put(yahoo, tf, [])
        return []

    if tf == "2h":
        df = _resample_ohlcv(df, "2h")
    elif tf == "4h":
        df = _resample_ohlcv(df, "4h")
    elif tf == "1w":
        df = _resample_ohlcv(df, "1W")

    intraday = tf not in ("1d", "1w")
    bars = _bars_from_df(df, intraday=intraday)
    history_cache.put(yahoo, tf, bars)
    return bars


def fetch_bars_batch(
    yahoo_list: list[str],
    tf: str,
    force: bool = False,
    batch_size: int = 40,
    period_override: str | None = None,
    timeout_sec: float | None = None,
    batch_timeout_sec: float = 25.0,
    use_threads: bool = False,
) -> dict[str, list[dict]]:
    """Batch-download bars for many symbols on one TF. Uses cache per symbol.

    Hardening (v1.13.1/1.13.2):
      - yfinance threads=False by default (threads=True can hang forever on Yahoo)
      - per-batch wall timeout via ThreadPoolExecutor
      - optional overall timeout_sec → return partial results
      - period_override for scanners that only need recent session bars
    """
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

    tf = (tf or "15m").lower()
    if tf not in TF_FETCH:
        return {}

    out: dict[str, list[dict]] = {}
    need: list[str] = []
    for y in yahoo_list:
        if not force:
            hit = history_cache.get(y, tf)
            if hit is not None:
                out[y] = hit
                continue
        need.append(y)

    if not need:
        return out

    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    spec = TF_FETCH[tf]
    y_interval = spec["interval"]
    y_period = period_override or spec["period"]
    intraday = tf not in ("1d", "1w")
    t0 = time.time()

    def _one(ysym: str, sub: pd.DataFrame) -> list[dict]:
        if sub is None or sub.empty:
            return []
        sub = sub.dropna(how="all")
        if tf == "2h":
            sub = _resample_ohlcv(sub, "2h")
        elif tf == "4h":
            sub = _resample_ohlcv(sub, "4h")
        elif tf == "1w":
            sub = _resample_ohlcv(sub, "1W")
        return _bars_from_df(sub, intraday=intraday)

    def _download_batch(batch: list[str]):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return yf.download(
                batch,
                period=y_period,
                interval=y_interval,
                group_by="ticker",
                threads=bool(use_threads),
                progress=False,
                auto_adjust=True,
            )

    for i in range(0, len(need), batch_size):
        if timeout_sec is not None and (time.time() - t0) >= timeout_sec:
            logger.warning(
                "batch hist %s overall timeout after %.1fs (%d/%d done)",
                tf,
                time.time() - t0,
                len(out),
                len(yahoo_list),
            )
            for y in need[i:]:
                if y not in out:
                    out[y] = []
            break

        batch = need[i : i + batch_size]
        remain = None
        if timeout_sec is not None:
            remain = max(1.0, timeout_sec - (time.time() - t0))
        bt = batch_timeout_sec if remain is None else min(batch_timeout_sec, remain)

        df = None
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_download_batch, batch)
                df = fut.result(timeout=bt)
        except FuturesTimeout:
            logger.warning("batch hist %s timeout (%.1fs) for %d syms", tf, bt, len(batch))
            for y in batch:
                # do not cache empty on timeout — allow retry / fallback
                out[y] = []
            continue
        except Exception as e:
            logger.warning("batch hist %s failed: %s", tf, e)
            for y in batch:
                history_cache.put(y, tf, [])
                out[y] = []
            continue

        if df is None or df.empty:
            for y in batch:
                history_cache.put(y, tf, [])
                out[y] = []
            continue

        if isinstance(df.columns, pd.MultiIndex):
            level0 = set(df.columns.get_level_values(0).unique())
            for ysym in batch:
                if ysym in level0:
                    bars = _one(ysym, df[ysym])
                else:
                    bars = []
                history_cache.put(ysym, tf, bars)
                out[ysym] = bars
        else:
            if len(batch) == 1:
                bars = _one(batch[0], df)
                history_cache.put(batch[0], tf, bars)
                out[batch[0]] = bars
            else:
                for y in batch:
                    history_cache.put(y, tf, [])
                    out[y] = []

        time.sleep(0.05)

    return out


def rvol_from_bars(bars: list[dict], n: int = RVOL_TF_N) -> dict[str, Any]:
    """rvol_tf = last_bar.volume / previous_bar.volume (same TF).

    rvol10 = last_bar.volume / mean(volume of up to 10 prior bars with volume).
    change_pct = (last.close - prev.close) / prev.close * 100
    (bar close vs previous bar close — consistent across TFs).

    `n` is ignored for the prev-bar ratio (legacy API param); rvol10 uses RVOL10_TF_N.
    """
    empty = {
        "rvol": None,
        "rvol10": None,
        "change_pct": None,
        "latest_vol": None,
        "prev_vol": None,
        "avg_vol": None,
        "avg10_vol": None,
        "bars_used": 0,
        "n": n,
        "n10": RVOL10_TF_N,
        "formula": "last_vol/prev_vol; rvol10=last_vol/mean(prev≤10)",
    }
    if not bars:
        return empty

    # Prefer bars that have volume for the RVOL ratio; still need close for change_pct
    usable = [b for b in bars if b.get("close") is not None]
    if len(usable) < 2:
        return {**empty, "bars_used": len(usable)}

    latest = usable[-1]
    prev = usable[-2]

    # RVOL: require positive volumes on both bars
    lv = latest.get("volume")
    pv = prev.get("volume")
    rvol = None
    if lv is not None and pv is not None and pv > 0 and lv >= 0:
        rvol = round(float(lv) / float(pv), 3)

    # rvol10: last ÷ mean of up to 10 prior bars with positive volume
    rvol10 = None
    avg10 = None
    prior_vol = [
        float(b["volume"])
        for b in usable[:-1]
        if b.get("volume") is not None and float(b["volume"]) > 0
    ]
    if lv is not None and prior_vol:
        window = prior_vol[-RVOL10_TF_N:]
        avg10 = sum(window) / len(window)
        if avg10 > 0:
            rvol10 = round(float(lv) / avg10, 3)

    # change_pct: last close vs previous bar close
    change_pct = None
    try:
        lc = float(latest["close"])
        pc = float(prev["close"])
        if pc != 0:
            change_pct = round((lc - pc) / pc * 100.0, 3)
    except (TypeError, ValueError, KeyError):
        change_pct = None

    return {
        "rvol": rvol,
        "rvol10": rvol10,
        "change_pct": change_pct,
        "latest_vol": int(lv) if lv is not None else None,
        "prev_vol": int(pv) if pv is not None else None,
        "avg_vol": int(pv) if pv is not None else None,  # alias: prev bar (compat)
        "avg10_vol": int(round(avg10)) if avg10 is not None else None,
        "prior_bars": 1,
        "prior_bars_10": len(prior_vol[-RVOL10_TF_N:]) if prior_vol else 0,
        "bars_used": len(usable),
        "n": n,
        "n10": RVOL10_TF_N,
        "latest_date": latest.get("date"),
        "prev_date": prev.get("date"),
        "latest_close": latest.get("close"),
        "prev_close": prev.get("close"),
        "formula": (
            "last_vol/prev_vol; rvol10=last_vol/mean(prev≤10 vols); "
            "change=(close-prev_close)/prev_close*100"
        ),
    }


_RVOL_ALL_TTL = 45.0
_rvol_all_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_rvol_all_lock = threading.Lock()


def compute_rvol_all_tf(yahoo: str, n: int = RVOL_TF_N, force: bool = False) -> dict[str, Any]:
    """Compute RVOL (+ rvol10) for every TF — base TFs fetched in parallel.

    Order: fetch independent base TFs (1m/5m/15m/30m/1h/1d) concurrently, then
    derive 2h/4h/1w (still parallel). Short result cache avoids repeat work when
    detail panel, signal, and notes all ask for the same symbol.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    ykey = (yahoo or "").upper()
    if not force:
        with _rvol_all_lock:
            hit = _rvol_all_cache.get(ykey)
            if hit and (time.time() - hit[0]) < _RVOL_ALL_TTL:
                return hit[1]

    base_tfs = ("1m", "5m", "15m", "30m", "1h", "1d")
    derived = ("2h", "4h", "1w")
    by_tf: dict[str, Any] = {}

    def _one(tf: str) -> tuple[str, dict[str, Any]]:
        bars = fetch_bars(yahoo, tf, force=force)
        return tf, rvol_from_bars(bars, n=n)

    # 1) Parallel base fetches
    with ThreadPoolExecutor(max_workers=len(base_tfs)) as pool:
        futs = {pool.submit(_one, tf): tf for tf in base_tfs}
        for fut in as_completed(futs):
            tf, info = fut.result()
            by_tf[tf] = info

    # 2) Derived TFs in parallel (may reuse Yahoo / hist cache)
    with ThreadPoolExecutor(max_workers=len(derived)) as pool:
        futs = {pool.submit(_one, tf): tf for tf in derived}
        for fut in as_completed(futs):
            tf, info = fut.result()
            by_tf[tf] = info

    out = {tf: by_tf.get(tf) or rvol_from_bars([], n=n) for tf in TF_INTERVALS}
    with _rvol_all_lock:
        _rvol_all_cache[ykey] = (time.time(), out)
    return out
