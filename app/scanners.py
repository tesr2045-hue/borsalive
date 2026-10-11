"""Scanners: steady risers, fast movers, multi-TF RVOL, net volume, spike alerts,
RVOL/RVOL10 volume alerts, Hacimli Kırılım (volume-break), parabolic score, POC shift,
Israrcılar (tavan bulucu), İşlem Planları (trade plans), Momentumlu Hızlanış (v1.15).
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from typing import Any

from app.history_cache import (
    RVOL_TF_DEF,
    RVOL_TF_N,
    RVOL_TF_TABLE_LIMIT,
    SCANNER_UNIVERSE_LIMIT,
    TF_INTERVALS,
    compute_rvol_all_tf,
    fetch_bars,
    fetch_bars_batch,
    rvol_from_bars,
)
from app.quotes import IST, quote_service

logger = logging.getLogger(__name__)

SCANNER_CACHE_TTL = 90.0
NET_VOLUME_CACHE_TTL = 240.0  # footprint-ish scan — cache hard
SPIKE_CACHE_TTL = 18.0  # align with ~20s UI poll
RVOL_ALERT_CACHE_TTL = 15.0
PARABOLIC_CACHE_TTL = 60.0
POC_SCAN_CACHE_TTL = 120.0
HIGH_BREAK_CACHE_TTL = 120.0
VOLUME_BREAK_CACHE_TTL = 45.0  # alarm poll ~50s; share high-break prefetch
MOMENTUM_CACHE_TTL = 40.0  # alarm poll ~45s; 1m window freshness
ISRARCILAR_CACHE_TTL = 45.0  # fresher for live watch; persistence still drives list
TRADE_PLANS_CACHE_TTL = 90.0  # 60–120s band; trade plan scan over liquid universe
SPIKE_UNIVERSE_LIMIT = 220  # warm top volume + expand beyond scanner 150
NET_VOLUME_UNIVERSE = SCANNER_UNIVERSE_LIMIT  # top ~150 by volume
NET_VOLUME_SRC_TF = "5m"  # scanner speed; 1m used if already cached

# Default min net % change by TF (session / window)
STEADY_MIN_CHANGE: dict[str, float] = {
    "1m": 1.5,
    "5m": 2.0,
    "15m": 2.5,
    "30m": 3.0,
    "1h": 3.5,
    "2h": 4.0,
    "4h": 5.0,
    "1d": 6.0,
    "1w": 8.0,
}

STEADY_GREEN_RATIO = 0.65
STEADY_MAX_PULLBACK = 0.45  # max fraction of bars that are deep red pullbacks

FAST_HOT_TF = ("1m", "5m", "15m", "30m")


class ScannerService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache: dict[str, tuple[float, Any]] = {}

    def _cached(self, key: str, ttl: float | None = None) -> Any | None:
        hit = self._cache.get(key)
        if not hit:
            return None
        ts, val = hit
        limit = SCANNER_CACHE_TTL if ttl is None else ttl
        if time.time() - ts > limit:
            return None
        return val

    def _store(self, key: str, val: Any) -> None:
        self._cache[key] = (time.time(), val)

    def top_volume_universe(self, limit: int = SCANNER_UNIVERSE_LIMIT) -> list[dict]:
        quotes = quote_service._cache or []
        pool = [q for q in quotes if q.get("volume") is not None and q.get("yahoo")]
        pool.sort(key=lambda q: q["volume"], reverse=True)
        return pool[: max(1, min(limit, 300))]


    @staticmethod
    def _spread_quote_volume(bars: list[dict], day_vol: float | int | None) -> list[dict]:
        """Distribute day quote volume across OHLC bars (İş Yatırım has no volume)."""
        if not bars:
            return bars
        try:
            day_vol_f = float(day_vol or 0)
        except (TypeError, ValueError):
            day_vol_f = 0.0
        weights: list[float] = []
        for b in bars:
            try:
                o = b.get("open")
                h = b.get("high")
                l = b.get("low")
                c = b.get("close")
                if h is not None and l is not None:
                    rng = abs(float(h) - float(l))
                else:
                    rng = 0.0
                if c is not None and o is not None:
                    body = abs(float(c) - float(o))
                else:
                    body = 0.0
                weights.append(max(rng, body, 1e-9))
            except Exception:
                weights.append(1.0)
        total_w = sum(weights) or float(len(weights)) or 1.0
        out: list[dict] = []
        for b, w in zip(bars, weights):
            nb = dict(b)
            if day_vol_f > 0:
                nb["volume"] = int(round(day_vol_f * (w / total_w)))
            elif nb.get("volume") is None:
                nb["volume"] = 0
            out.append(nb)
        return out

    def _prefetch_yahoo_tf(
        self,
        yahoo_list: list[str],
        tf: str,
        *,
        force: bool = False,
        deadline: float | None = None,
        period_override: str | None = None,
        batch_size: int = 25,
        batch_timeout_sec: float = 16.0,
    ) -> dict[str, list[dict]]:
        """Batch Yahoo bars with wall timeouts; returns partial map on deadline."""
        if not yahoo_list:
            return {}
        remain = None
        if deadline is not None:
            remain = max(3.0, deadline - time.time())
        return fetch_bars_batch(
            yahoo_list,
            tf,
            force=force,
            batch_size=batch_size,
            period_override=period_override,
            timeout_sec=remain,
            batch_timeout_sec=batch_timeout_sec,
            use_threads=False,
        )

    def _isyatirim_fill_bars(
        self,
        missing: list[str],
        by_yahoo: dict[str, dict],
        *,
        tf: str = "5m",
        deadline: float | None = None,
        session_only: bool = False,
    ) -> int:
        """Fill history_cache from İş Yatırım OHLC + quote volume for missing yahoo keys.

        Returns number of symbols successfully filled.
        """
        if not missing:
            return 0
        from app.chart_provider import fetch_chart_history
        from app.history_cache import history_cache
        from app.features import _bar_session_date, _parse_session_date

        ok = 0
        target = _parse_session_date("today")
        for y in missing:
            if deadline is not None and time.time() >= deadline:
                break
            q = by_yahoo.get(y) or {}
            sym = q.get("symbol") or str(y).replace(".IS", "")
            try:
                bars, meta = fetch_chart_history(sym, tf, force=False)
            except Exception as e:
                logger.debug("isyatirim fill %s %s: %s", sym, tf, e)
                continue
            if not bars:
                continue
            if session_only and target is not None:
                day = [b for b in bars if _bar_session_date(b) == target]
                # keep full series in cache for TF indicators; but if empty day, skip
                if len(day) < 2:
                    # try last available session date in series
                    dates = sorted(
                        {d for d in (_bar_session_date(b) for b in bars) if d},
                        reverse=True,
                    )
                    if dates:
                        day = [b for b in bars if _bar_session_date(b) == dates[0]]
                use = day if day else bars
            else:
                use = bars
            use = self._spread_quote_volume(use, q.get("volume"))
            if len(use) < 2:
                continue
            # Cache under yahoo key so compute_* / fetch_bars hit
            history_cache.put(y, tf, use)
            ok += 1
        return ok

    def _netvol_isyatirim_fill(
        self,
        missing: list[str],
        by_yahoo: dict[str, dict],
        bars_chosen: dict[str, tuple[str, list]],
        deadline: float,
    ) -> int:
        """Net-volume İş Yatırım fallback: 5m OHLC + quote volume → bars_chosen."""
        if not missing:
            return 0
        from app.chart_provider import fetch_chart_history
        from app.features import _bar_session_date, _parse_session_date

        ok = 0
        target = _parse_session_date("today")
        for y in missing:
            if time.time() >= deadline:
                break
            q = by_yahoo.get(y) or {}
            sym = q.get("symbol") or str(y).replace(".IS", "")
            try:
                bars, _meta = fetch_chart_history(sym, "5m", force=False)
            except Exception as e:
                logger.debug("netvol isy %s: %s", sym, e)
                continue
            if not bars:
                continue
            day = [b for b in bars if _bar_session_date(b) == target] if target else list(bars)
            if len(day) < 2:
                dates = sorted(
                    {d for d in (_bar_session_date(b) for b in bars) if d},
                    reverse=True,
                )
                if dates:
                    day = [b for b in bars if _bar_session_date(b) == dates[0]]
            if len(day) < 2:
                continue
            day = self._spread_quote_volume(day, q.get("volume"))
            bars_chosen[y] = ("5m_isy", day)
            ok += 1
        return ok


    def _session_bars(self, bars: list[dict], tf: str) -> list[dict]:
        """Bars belonging to the latest session date (IST) present in the series."""
        if not bars:
            return []
        if tf in ("1d", "1w"):
            # For daily/weekly use last N bars as the "window"
            n = 15 if tf == "1d" else 8
            return bars[-n:]
        # Intraday: filter to last calendar day that has bars
        last_date = None
        for b in reversed(bars):
            d = (b.get("date") or "")[:10]
            if d:
                last_date = d
                break
        if not last_date:
            return bars[-40:]
        return [b for b in bars if (b.get("date") or "").startswith(last_date)]

    def _steady_score(
        self,
        bars: list[dict],
        tf: str,
        min_change: float,
        green_ratio_min: float,
    ) -> dict[str, Any] | None:
        window = self._session_bars(bars, tf)
        if len(window) < 4:
            return None
        opens = [b.get("open") for b in window]
        closes = [b.get("close") for b in window]
        highs = [b.get("high") for b in window]
        lows = [b.get("low") for b in window]
        if any(c is None for c in closes) or opens[0] is None:
            return None

        first_open = next((b["open"] for b in window if b.get("open") is not None), None)
        last_close = closes[-1]
        if first_open is None or last_close is None or first_open <= 0:
            return None
        change_pct = ((last_close - first_open) / first_open) * 100.0
        if change_pct < min_change:
            return None

        green = 0
        red = 0
        deep_pullbacks = 0
        for b in window:
            o, c = b.get("open"), b.get("close")
            if o is None or c is None:
                continue
            if c >= o:
                green += 1
            else:
                red += 1
                # deep pullback: red bar body > 0.8% of price
                if o > 0 and (o - c) / o >= 0.008:
                    deep_pullbacks += 1

        total = green + red
        if total < 4:
            return None
        green_ratio = green / total
        if green_ratio < green_ratio_min:
            return None

        pullback_frac = deep_pullbacks / total
        if pullback_frac > STEADY_MAX_PULLBACK:
            return None

        # Higher highs / higher lows on closes
        hh = 0
        hl = 0
        for i in range(1, len(window)):
            h0, h1 = highs[i - 1], highs[i]
            l0, l1 = lows[i - 1], lows[i]
            if h0 is not None and h1 is not None and h1 >= h0:
                hh += 1
            if l0 is not None and l1 is not None and l1 >= l0:
                hl += 1
        steps = max(len(window) - 1, 1)
        hh_ratio = hh / steps
        hl_ratio = hl / steps

        # Composite score: change + green dominance + trend structure - pullbacks
        score = (
            change_pct * 1.2
            + (green_ratio - 0.5) * 40
            + hh_ratio * 15
            + hl_ratio * 15
            - pullback_frac * 25
        )
        return {
            "change_pct": round(change_pct, 3),
            "green_ratio": round(green_ratio, 3),
            "green_bars": green,
            "red_bars": red,
            "bars": len(window),
            "deep_pullbacks": deep_pullbacks,
            "hh_ratio": round(hh_ratio, 3),
            "hl_ratio": round(hl_ratio, 3),
            "score": round(score, 3),
            "first_open": first_open,
            "last_close": last_close,
            "session_date": (window[0].get("date") or "")[:10],
        }

    def steady_risers(
        self,
        interval: str = "15m",
        limit: int = 30,
        min_change: float | None = None,
        green_ratio: float = STEADY_GREEN_RATIO,
        universe_limit: int = SCANNER_UNIVERSE_LIMIT,
        force: bool = False,
    ) -> dict[str, Any]:
        interval = (interval or "15m").lower()
        if interval not in TF_INTERVALS:
            interval = "15m"
        limit = max(1, min(int(limit or 30), 100))
        thr = STEADY_MIN_CHANGE.get(interval, 3.0) if min_change is None else float(min_change)

        cache_key = f"steady:{interval}:{limit}:{thr}:{green_ratio}:{universe_limit}"
        if not force:
            hit = self._cached(cache_key)
            if hit is not None:
                return hit

        universe = self.top_volume_universe(universe_limit)
        yahoo_list = [q["yahoo"] for q in universe]
        by_yahoo = {q["yahoo"]: q for q in universe}

        bars_map = fetch_bars_batch(yahoo_list, interval, force=force, batch_size=30,
                                   period_override=("5d" if interval not in ("1d", "1w") else None),
                                   timeout_sec=40.0, batch_timeout_sec=16.0, use_threads=False)

        results: list[dict] = []
        market_state = None
        for y, bars in bars_map.items():
            q = by_yahoo.get(y)
            if not q:
                continue
            if market_state is None:
                market_state = q.get("market_state")
            scored = self._steady_score(bars, interval, thr, green_ratio)
            if not scored:
                continue
            results.append(
                {
                    "symbol": q["symbol"],
                    "yahoo": y,
                    "name": q.get("name"),
                    "price": q.get("price"),
                    "change_pct_day": q.get("change_pct"),
                    "volume": q.get("volume"),
                    "rvol": q.get("rvol"),
                    "rvol10": q.get("rvol10"),
                    "market_state": q.get("market_state"),
                    "interval": interval,
                    **scored,
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:limit]
        out = {
            "kind": "steady_risers",
            "interval": interval,
            "limit": limit,
            "count": len(results),
            "coverage": {
                "universe": len(universe),
                "scanned": len(bars_map),
                "note": (
                    f"İlk {universe_limit} hacimli hisse taranır "
                    f"(tam BIST evreni değil). N yeşil oranı ≥ {green_ratio}, "
                    f"min net % ≥ {thr}."
                ),
            },
            "params": {
                "min_change_pct": thr,
                "green_ratio_min": green_ratio,
                "max_pullback_frac": STEADY_MAX_PULLBACK,
            },
            "market_state": market_state,
            "formula": (
                "İstikrarlı yükseliş: oturum penceresinde net % değişim ≥ eşik; "
                f"yeşil bar oranı ≥ {green_ratio}; derin geri çekilme az; "
                "HH/HL oranı skora eklenir. score = change*1.2 + (green-0.5)*40 "
                "+ hh*15 + hl*15 - pullback*25."
            ),
            "stocks": results,
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._store(cache_key, out)
        return out

    def _velocity_from_bars(self, bars: list[dict], tf: str, day_change: float | None) -> dict[str, Any] | None:
        window = self._session_bars(bars, tf)
        if len(window) < 2:
            return None
        first = next((b["open"] for b in window if b.get("open") is not None), None)
        last = window[-1].get("close")
        if first is None or last is None or first <= 0:
            return None
        move_pct = abs((last - first) / first) * 100.0
        signed = ((last - first) / first) * 100.0
        n_bars = len(window)
        # Minutes per bar approx
        mins = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "2h": 120, "4h": 240, "1d": 390, "1w": 1950,
        }.get(tf, 15)
        elapsed_min = max(n_bars * mins, mins)
        velocity = move_pct / (elapsed_min / 60.0)  # % per hour
        # ATR-like: mean true range % over window
        trs = []
        for i, b in enumerate(window):
            h, l, c = b.get("high"), b.get("low"), b.get("close")
            if h is None or l is None or c is None:
                continue
            prev_c = window[i - 1].get("close") if i > 0 else c
            tr = max(h - l, abs(h - (prev_c or c)), abs(l - (prev_c or c)))
            if c > 0:
                trs.append(tr / c * 100.0)
        atr_pct = sum(trs) / len(trs) if trs else None
        atr_norm = (move_pct / atr_pct) if atr_pct and atr_pct > 0 else None

        return {
            "move_pct": round(signed, 3),
            "abs_move_pct": round(move_pct, 3),
            "bars": n_bars,
            "elapsed_min": elapsed_min,
            "velocity_pct_per_hour": round(velocity, 3),
            "atr_pct": round(atr_pct, 3) if atr_pct is not None else None,
            "move_vs_atr": round(atr_norm, 3) if atr_norm is not None else None,
            "day_change_pct": day_change,
        }

    def fast_movers(
        self,
        limit: int = 30,
        universe_limit: int = SCANNER_UNIVERSE_LIMIT,
        force: bool = False,
        interval: str = "5m",
    ) -> dict[str, Any]:
        limit = max(1, min(int(limit or 30), 100))
        interval = (interval or "5m").lower()
        if interval not in TF_INTERVALS:
            interval = "5m"
        cache_key = f"fast:{interval}:{limit}:{universe_limit}"
        if not force:
            hit = self._cached(cache_key)
            if hit is not None:
                return hit

        universe = self.top_volume_universe(universe_limit)
        yahoo_list = [q["yahoo"] for q in universe]
        by_yahoo = {q["yahoo"]: q for q in universe}

        # Primary velocity on selected TF; also flag nearby heat TFs
        primary_tf = interval
        bars_primary = fetch_bars_batch(yahoo_list, primary_tf, force=force, batch_size=30,
            period_override=("5d" if primary_tf not in ("1d", "1w") else None),
            timeout_sec=40.0, batch_timeout_sec=16.0, use_threads=False)
        hot_maps: dict[str, dict[str, list]] = {}
        for tf in FAST_HOT_TF:
            if tf == primary_tf:
                hot_maps[tf] = bars_primary
            else:
                # Smaller subset for extra TFs: top 80 by volume to stay responsive
                subset = yahoo_list[:80]
                hot_maps[tf] = fetch_bars_batch(subset, tf, force=force, batch_size=30,
                    period_override=("5d" if tf not in ("1d", "1w") else None),
                    timeout_sec=25.0, batch_timeout_sec=14.0, use_threads=False)

        # Build per-symbol velocity + hot flags
        rows: list[dict] = []
        market_state = None
        for y in yahoo_list:
            q = by_yahoo.get(y)
            if not q:
                continue
            if market_state is None:
                market_state = q.get("market_state")
            bars = bars_primary.get(y) or []
            vel = self._velocity_from_bars(bars, primary_tf, q.get("change_pct"))
            if not vel:
                # fallback: use day change from quote
                day = q.get("change_pct")
                if day is None:
                    continue
                vel = {
                    "move_pct": day,
                    "abs_move_pct": abs(day),
                    "bars": None,
                    "elapsed_min": None,
                    "velocity_pct_per_hour": abs(day),  # rough
                    "atr_pct": None,
                    "move_vs_atr": None,
                    "day_change_pct": day,
                }

            hot_flags: list[str] = []
            tf_vel: dict[str, float | None] = {}
            for tf, bmap in hot_maps.items():
                b = bmap.get(y) or []
                v2 = self._velocity_from_bars(b, tf, q.get("change_pct"))
                if v2 and v2["velocity_pct_per_hour"] is not None:
                    tf_vel[tf] = v2["velocity_pct_per_hour"]
                    # "hot" if > ~2%/hour on short TF or high abs move
                    thr = 3.0 if tf in ("1m", "5m") else 2.0
                    if v2["velocity_pct_per_hour"] >= thr and v2["abs_move_pct"] >= 0.8:
                        hot_flags.append(tf)

            score = vel["velocity_pct_per_hour"]
            if vel.get("move_vs_atr"):
                score += min(vel["move_vs_atr"], 5) * 0.5
            score += len(hot_flags) * 1.5

            rows.append(
                {
                    "symbol": q["symbol"],
                    "yahoo": y,
                    "name": q.get("name"),
                    "price": q.get("price"),
                    "change_pct": q.get("change_pct"),
                    "volume": q.get("volume"),
                    "rvol": q.get("rvol"),
                    "rvol10": q.get("rvol10"),
                    "market_state": q.get("market_state"),
                    "primary_tf": primary_tf,
                    "hot_tfs": hot_flags,
                    "tf_velocity": tf_vel,
                    "score": round(score, 3),
                    **{f"v_{k}": v for k, v in vel.items()},
                }
            )

        rows.sort(key=lambda x: x["score"], reverse=True)
        rows = rows[:limit]
        out = {
            "kind": "fast_movers",
            "limit": limit,
            "interval": primary_tf,
            "count": len(rows),
            "coverage": {
                "universe": len(universe),
                "primary_tf": primary_tf,
                "hot_tfs_checked": list(FAST_HOT_TF),
                "hot_subset": 80,
                "note": (
                    f"Hız skoru öncelikle {primary_tf} üzerinde; "
                    f"sıcak TF bayrakları {list(FAST_HOT_TF)} (alt küme 80). "
                    f"Evren: ilk {universe_limit} hacimli hisse."
                ),
            },
            "market_state": market_state,
            "formula": (
                "velocity = abs(session_move%) / hours_elapsed; "
                "score = velocity + 0.5*min(move/ATR,5) + 1.5*#hot_tfs. "
                "Hot: kısa TF'de ≥~2–3%/saat ve abs hareket ≥0.8%."
            ),
            "stocks": rows,
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._store(cache_key, out)
        return out

    def rvol_multi_tf_table(
        self,
        limit: int = RVOL_TF_TABLE_LIMIT,
        force: bool = False,
    ) -> dict[str, Any]:
        """Top volume names with RVOL across all TFs."""
        limit = max(1, min(int(limit or 40), 80))
        cache_key = f"rvoltf:{limit}"
        if not force:
            hit = self._cached(cache_key)
            if hit is not None:
                return hit

        universe = self.top_volume_universe(limit)
        rows: list[dict] = []
        # Prefer computing on 15m/1h/1d first via batch, then fill rest per symbol
        # To keep latency OK: batch each TF for the limited set
        tf_bars: dict[str, dict[str, list]] = {}
        yahoo_list = [q["yahoo"] for q in universe]
        for tf in TF_INTERVALS:
            tf_bars[tf] = fetch_bars_batch(yahoo_list, tf, force=force, batch_size=30,
                period_override=("5d" if tf not in ("1d", "1w") else None),
                timeout_sec=35.0, batch_timeout_sec=14.0, use_threads=False)

        for q in universe:
            y = q["yahoo"]
            rvols: dict[str, float | None] = {}
            details: dict[str, Any] = {}
            chg_tf: dict[str, float | None] = {}
            for tf in TF_INTERVALS:
                info = rvol_from_bars(tf_bars[tf].get(y) or [], n=RVOL_TF_N)
                rvols[tf] = info.get("rvol")
                chg_tf[tf] = info.get("change_pct")
                details[tf] = info
            # Rank key: max absolute rvol among available
            vals = [v for v in rvols.values() if v is not None]
            max_r = max(vals) if vals else 0
            rows.append(
                {
                    "symbol": q["symbol"],
                    "yahoo": y,
                    "name": q.get("name"),
                    "price": q.get("price"),
                    "change_pct": q.get("change_pct"),
                    "volume": q.get("volume"),
                    "rvol": q.get("rvol"),
                    "rvol10": q.get("rvol10"),
                    "market_state": q.get("market_state"),
                    "rvol_tf": rvols,
                    "change_pct_tf": chg_tf,
                    "rvol_tf_detail": details,
                    "max_rvol_tf": max_r,
                }
            )

        rows.sort(key=lambda x: x["max_rvol_tf"], reverse=True)
        out = {
            "kind": "rvol_multi_tf",
            "limit": limit,
            "count": len(rows),
            "n": RVOL_TF_N,
            "intervals": list(TF_INTERVALS),
            "rvol_tf_def": RVOL_TF_DEF,
            "coverage": {
                "note": f"İlk {limit} hacimli hisse; her TF için RVOL = son mum ÷ önceki mum.",
            },
            "stocks": rows,
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._store(cache_key, out)
        return out

    def stock_rvol_tf(self, symbol: str, force: bool = False) -> dict[str, Any]:
        sym = symbol.upper().replace(".IS", "")
        yahoo = f"{sym}.IS"
        by_tf = compute_rvol_all_tf(yahoo, n=RVOL_TF_N, force=force)
        quote = None
        try:
            quote = quote_service.fetch_one(sym)
        except Exception:
            cached = quote_service._cache or []
            quote = next((q for q in cached if q["symbol"] == sym), None)
        return {
            "symbol": sym,
            "yahoo": yahoo,
            "stock": quote,
            "n": RVOL_TF_N,
            "n10": 10,
            "intervals": list(TF_INTERVALS),
            "rvol_tf": {k: v.get("rvol") for k, v in by_tf.items()},
            "rvol10_tf": {k: v.get("rvol10") for k, v in by_tf.items()},
            "change_pct_tf": {k: v.get("change_pct") for k, v in by_tf.items()},
            "rvol_tf_detail": by_tf,
            "rvol_tf_def": RVOL_TF_DEF,
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        }

    def spike_alerts(
        self,
        pct: float = 2.0,
        intervals: list[str] | None = None,
        universe_limit: int = SPIKE_UNIVERSE_LIMIT,
        force: bool = False,
    ) -> dict[str, Any]:
        """Ani artış: last-bar change_pct ≥ +pct on selected TF(s).

        When intervals is non-empty: ONLY last-bar (close vs prev close) on those TFs
        for top-volume universe (expanded). When empty: daily quote change_pct on
        full quote cache (günlük seans değişimi).
        """
        threshold = float(pct)
        tf_list = [t for t in (intervals or []) if t in TF_INTERVALS]
        cache_key = f"spike:{threshold}:{','.join(tf_list) or 'quote_day'}:{universe_limit}"
        if not force:
            hit = self._cached(cache_key, ttl=SPIKE_CACHE_TTL)
            if hit is not None:
                return hit

        spikes: list[dict] = []
        err = None
        quoted = 0
        scanned = 0
        market_state = None

        if not tf_list:
            # Daily quote change — full universe
            quotes = quote_service._cache or []
            quoted = len(quotes)
            for q in quotes:
                if market_state is None:
                    market_state = q.get("market_state")
                chg = q.get("change_pct")
                if chg is not None and chg >= threshold:
                    spikes.append(
                        {
                            "symbol": q["symbol"],
                            "name": q.get("name"),
                            "price": q.get("price"),
                            "change_pct": chg,
                            "volume": q.get("volume"),
                            "rvol": q.get("rvol"),
                            "rvol10": q.get("rvol10"),
                            "source": "quote_day",
                            "tf": "1d",
                            "interval": "1d",
                        }
                    )
            formula = (
                "quote_day: regularMarketChangePercent (günlük seans değişimi) ≥ eşik. "
                "TF seçilmediği için günlük quote kullanıldı."
            )
            coverage_note = f"Tüm quote cache ({quoted} hisse); günlük değişim."
        else:
            # Last-bar % on selected TFs only
            universe = self.top_volume_universe(universe_limit)
            quoted = len(universe)
            yahoo_list = [u["yahoo"] for u in universe if u.get("yahoo")]
            by_sym = {u["yahoo"]: u for u in universe}
            seen: set[tuple[str, str]] = set()
            for tf in tf_list:
                bars_map = fetch_bars_batch(yahoo_list, tf, force=force, batch_size=30,
                    period_override=("5d" if tf not in ("1d", "1w") else None),
                    timeout_sec=35.0, batch_timeout_sec=14.0, use_threads=False)
                scanned += len(bars_map)
                for y, bars in bars_map.items():
                    info = rvol_from_bars(bars)
                    chg = info.get("change_pct")
                    if chg is None or chg < threshold:
                        continue
                    u = by_sym.get(y) or {}
                    sym = u.get("symbol") or y.replace(".IS", "")
                    key = (sym, tf)
                    if key in seen:
                        continue
                    seen.add(key)
                    if market_state is None:
                        market_state = u.get("market_state")
                    spikes.append(
                        {
                            "symbol": sym,
                            "name": u.get("name"),
                            "price": u.get("price"),
                            "change_pct": chg,
                            "last_bar_change_pct": chg,
                            "volume": u.get("volume"),
                            "rvol": info.get("rvol") if info.get("rvol") is not None else u.get("rvol"),
                            "rvol10": u.get("rvol10"),
                            "latest_close": info.get("latest_close"),
                            "prev_close": info.get("prev_close"),
                            "latest_date": info.get("latest_date"),
                            "source": "last_bar",
                            "tf": tf,
                            "interval": tf,
                        }
                    )
            formula = (
                "last_bar: (son_mum.close − önceki_mum.close) / önceki_mum.close × 100 "
                f"≥ +{threshold} (seçilen TF: {', '.join(tf_list)}). "
                "Günlük quote değişimi kullanılmaz."
            )
            coverage_note = (
                f"İlk {len(universe)} hacimli hisse (hedef ≤{universe_limit}); "
                f"TF={','.join(tf_list)}; son mum %."
            )

        spikes.sort(key=lambda x: x.get("change_pct") or 0, reverse=True)
        out = {
            "kind": "spike",
            "pct": threshold,
            "interval": tf_list[0] if len(tf_list) == 1 else None,
            "requested_interval": tf_list[0] if len(tf_list) == 1 else (tf_list or None),
            "intervals": tf_list or ["quote_day"],
            "tfs": tf_list or ["quote_day"],
            "count": len(spikes),
            "quoted": quoted,
            "scanned": scanned or quoted,
            "error": err,
            "spikes": spikes,
            "market_state": market_state,
            "coverage": {
                "universe": quoted,
                "scanned": scanned or quoted,
                "limit": universe_limit if tf_list else quoted,
                "note": coverage_note,
            },
            "formula": formula,
            "rule_tr": (
                f"Ani Artış: seçilen zaman diliminde son mum kapanışı, bir önceki mum "
                f"kapanışına göre ≥ +%{threshold:g} değişirse tetiklenir."
                if tf_list
                else f"Ani Artış (günlük): seans değişimi ≥ +%{threshold:g}."
            ),
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._store(cache_key, out)
        return out

    def net_volume(
        self,
        limit: int = 50,
        sort: str = "net",
        universe_limit: int = NET_VOLUME_UNIVERSE,
        force: bool = False,
    ) -> dict[str, Any]:
        """Daily footprint-style buy/sell/net totals for top-volume names.

        Sort keys: net | buy_dom | buy | sell | volume | change
        Default: net (net_vol desc). Purpose: buyer-dominated names during the day.
        """
        from app.analysis import session_buy_sell_totals
        from app.history_cache import history_cache

        limit = max(1, min(int(limit or 50), 1000))
        sort = (sort or "net").lower().strip()
        sort_aliases = {
            "net": "net_vol",
            "net_vol": "net_vol",
            "buy_dom": "buy_dominance_pct",
            "buy_dominance": "buy_dominance_pct",
            "buy_dominance_pct": "buy_dominance_pct",
            "buy": "buy_vol",
            "buy_vol": "buy_vol",
            "sell": "sell_vol",
            "sell_vol": "sell_vol",
            "volume": "total_vol",
            "total": "total_vol",
            "change": "change_pct",
            "change_pct": "change_pct",
        }
        sort_key = sort_aliases.get(sort, "net_vol")

        cache_key = f"netvol:{limit}:{sort_key}:{universe_limit}"
        if not force:
            hit = self._cached(cache_key, ttl=NET_VOLUME_CACHE_TTL)
            if hit is not None:
                return hit

        universe = self.top_volume_universe(universe_limit)
        yahoo_list = [q["yahoo"] for q in universe if q.get("yahoo")]
        by_yahoo = {q["yahoo"]: q for q in universe}

        # Prefer cached 1m if present for a symbol; otherwise batch 5m
        need_5m: list[str] = []
        bars_chosen: dict[str, tuple[str, list]] = {}
        source_notes: list[str] = []
        t_scan = time.time()
        # Hard deadline so UI never hangs (Yahoo threads=True used to stall forever)
        NETVOL_DEADLINE = 48.0

        for y in yahoo_list:
            cached_1m = history_cache.get(y, "1m")
            if cached_1m and len(cached_1m) >= 3:
                bars_chosen[y] = ("1m", cached_1m)
            else:
                need_5m.append(y)

        yahoo_ok = 0
        if need_5m:
            remain = max(5.0, NETVOL_DEADLINE - (time.time() - t_scan))
            # Short lookback (5d) is enough for session footprint; 60d Yahoo was slow/hang-prone
            b5 = fetch_bars_batch(
                need_5m,
                NET_VOLUME_SRC_TF,
                force=force,
                batch_size=25,
                period_override="5d",
                timeout_sec=remain,
                batch_timeout_sec=18.0,
                use_threads=False,
            )
            for y, bars in b5.items():
                if bars and len(bars) >= 2:
                    bars_chosen[y] = (NET_VOLUME_SRC_TF, bars)
                    yahoo_ok += 1
                elif y not in bars_chosen:
                    bars_chosen[y] = (NET_VOLUME_SRC_TF, bars or [])
            source_notes.append(f"Yahoo 5d/{NET_VOLUME_SRC_TF}: {yahoo_ok}/{len(need_5m)}")

        # İş Yatırım fallback for symbols still missing usable volume bars
        missing = [
            y
            for y, (src, bars) in bars_chosen.items()
            if not bars or len(bars) < 2 or not any((b.get("volume") or 0) > 0 for b in bars[-80:])
        ]
        # Also symbols never fetched if we aborted early
        for y in yahoo_list:
            if y not in bars_chosen:
                missing.append(y)
        missing = list(dict.fromkeys(missing))

        isy_ok = 0
        if missing and (time.time() - t_scan) < NETVOL_DEADLINE - 3:
            try:
                isy_ok = self._netvol_isyatirim_fill(
                    missing,
                    by_yahoo,
                    bars_chosen,
                    deadline=t_scan + NETVOL_DEADLINE,
                )
                source_notes.append(f"İş Yatırım fallback: {isy_ok}/{len(missing)}")
            except Exception as e:
                logger.warning("net_volume isyatirim fallback: %s", e)
                source_notes.append(f"İş Yatırım fallback hata: {e}")

        rows: list[dict] = []
        market_state = None
        session_date = None
        def _live_totals(sym: str) -> dict | None:
            """v1.16.0: real İdealData Y38 buy/sell lots (if fresh) instead of OHLCV approx."""
            try:
                from app.ideal_feed import ideal_feed

                fp = ideal_feed.footprint(sym)
            except Exception:
                fp = None
            if not fp or not fp.get("levels"):
                return None
            b = int(sum(int(l.get("buy_volume") or 0) for l in fp["levels"]))
            sl = int(sum(int(l.get("sell_volume") or 0) for l in fp["levels"]))
            tv = int(sum(int(l.get("total_volume") or 0) for l in fp["levels"]))
            bs = b + sl
            dom = round(b / bs * 100.0, 2) if bs > 0 else None
            return {
                "buy_vol": b, "sell_vol": sl, "net_vol": b - sl, "total_vol": tv or bs,
                "buy_dominance_pct": dom,
                "sell_dominance_pct": round(100.0 - dom, 2) if dom is not None else None,
                "vol_source": "idealdata", "vol_source_label": "İdealData canlı",
            }

        live_n = 0
        seen_rows: set[str] = set()
        for y, (src_tf, bars) in bars_chosen.items():
            q = by_yahoo.get(y)
            if not q:
                continue
            if market_state is None:
                market_state = q.get("market_state")
            totals = session_buy_sell_totals(bars)
            live_t = _live_totals(q["symbol"])
            if live_t:
                totals = {**totals, **live_t}
                if not totals.get("bar_count"):
                    totals["bar_count"] = 0
                live_n += 1
                src_tf = "İdealData"
            elif (totals.get("bar_count") or 0) < 2 or not totals.get("total_vol"):
                continue
            seen_rows.add(y)
            if session_date is None:
                session_date = totals.get("date")
            rows.append(
                {
                    "symbol": q["symbol"],
                    "yahoo": y,
                    "name": q.get("name"),
                    "price": q.get("price"),
                    "change_pct": q.get("change_pct"),
                    "volume": q.get("volume"),
                    "rvol": q.get("rvol"),
                    "rvol10": q.get("rvol10"),
                    "market_state": q.get("market_state"),
                    "buy_vol": totals["buy_vol"],
                    "sell_vol": totals["sell_vol"],
                    "net_vol": totals["net_vol"],
                    "total_vol": totals["total_vol"],
                    "buy_dominance_pct": totals["buy_dominance_pct"],
                    "sell_dominance_pct": totals["sell_dominance_pct"],
                    "bar_count": totals["bar_count"],
                    "session_date": totals.get("date"),
                    "source_tf": src_tf,
                    "vol_source": totals.get("vol_source") or "tahmini",
                    "vol_source_label": totals.get("vol_source_label") or "tahmini (OHLCV)",
                }
            )

        # Universe names without usable bars but with live İdealData levels.
        # v1.16.0: with İdealData the whole BIST share list (BISTTÜM) is covered, not only
        # the top-volume Yahoo universe — real Y38 alış/satış needs no Yahoo bars.
        all_quotes = {q.get("yahoo"): q for q in (quote_service._cache or []) if q.get("yahoo")}
        extra_ys = [y for y in all_quotes if y not in by_yahoo]
        by_yahoo.update({y: all_quotes[y] for y in extra_ys})
        for y in list(yahoo_list) + extra_ys:
            if y in seen_rows:
                continue
            q = by_yahoo.get(y)
            if not q:
                continue
            live_t = _live_totals(q["symbol"])
            if not live_t:
                continue
            live_n += 1
            rows.append(
                {
                    "symbol": q["symbol"], "yahoo": y, "name": q.get("name"),
                    "price": q.get("price"), "change_pct": q.get("change_pct"),
                    "volume": q.get("volume"), "rvol": q.get("rvol"), "rvol10": q.get("rvol10"),
                    "market_state": q.get("market_state"),
                    "buy_vol": live_t["buy_vol"], "sell_vol": live_t["sell_vol"],
                    "net_vol": live_t["net_vol"], "total_vol": live_t["total_vol"],
                    "buy_dominance_pct": live_t["buy_dominance_pct"],
                    "sell_dominance_pct": live_t["sell_dominance_pct"],
                    "bar_count": 0, "session_date": None, "source_tf": "İdealData",
                    "vol_source": "idealdata", "vol_source_label": "İdealData canlı",
                }
            )
        if live_n:
            source_notes.append(f"İdealData canlı alış/satış: {live_n} hisse")

        rows.sort(key=lambda x: (x.get(sort_key) is None, -(x.get(sort_key) or 0)))
        with_data = len(rows)
        rows = rows[:limit]
        elapsed = round(time.time() - t_scan, 1)
        warn = None
        if with_data == 0:
            warn = (
                "Net hacim verisi alınamadı (Yahoo zaman aşımı / boş; "
                "İş Yatırım gün içi seride hacim yok — kotasyon hacmi dağıtımı da yetersiz). "
                "Piyasa kapalıysa son seans barları beklenir."
            )
        note = (
            (f"Tüm BIST payları ({with_data} hisse, İdealData canlı); ilk {universe_limit} hacimli için "
             if live_n > universe_limit else f"İlk {universe_limit} hacimli hisse; ")
            + f"günlük footprint toplamları "
            f"(alış/satış bar sınıflandırması). "
            f"Kaynak: Yahoo 5d/{NET_VOLUME_SRC_TF} (timeout korumalı)"
            f"{' + İş Yatırım yedek' if isy_ok else ''}. "
            f"{' · '.join(source_notes)}. "
            f"Süre: {elapsed}s. Amaç: gün içinde alıcı hakim isimleri bulmak."
        )
        out = {
            "kind": "net_volume",
            "limit": limit,
            "sort": sort_key,
            "count": len(rows),
            "session_date": session_date,
            "coverage": {
                "universe": len(universe),
                "scanned": len(bars_chosen),
                "with_data": with_data,
                "yahoo_ok": yahoo_ok,
                "isyatirim_ok": isy_ok,
                "elapsed_sec": elapsed,
                "note": note,
                "warning": warn,
            },
            "params": {
                "universe_limit": universe_limit,
                "src_tf_default": NET_VOLUME_SRC_TF,
                "yahoo_period": "5d",
                "deadline_sec": NETVOL_DEADLINE,
            },
            "market_state": market_state,
            "error": warn,
            "formula": (
                "Her seans barında: close>open → alış oranı (close−low)/(high−low); "
                "close<open → satış oranı (high−close)/(high−low); doji %50/%50. "
                "buy_vol / sell_vol = bar hacmi × oran; net_vol = buy − sell; "
                "buy_dominance_pct = buy / (buy+sell) × 100. "
                "Yahoo yoksa: İş Yatırım 5m OHLC + gün kotasyon hacmi barlara dağıtılır."
            ),
            "stocks": rows,
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "cache_ttl_sec": NET_VOLUME_CACHE_TTL,
        }
        # Only cache successful / partial-with-rows; empty error responses stay uncached
        if with_data > 0:
            self._store(cache_key, out)
        return out


    def rvol_spike_alerts(
        self,
        threshold: float = 2.0,
        baseline_mult: float = 1.0,
        intervals: list[str] | None = None,
        include_day: bool = True,
        force: bool = False,
    ) -> dict[str, Any]:
        """RVOL ani sıçrama: day RVOL and/or multi-TF RVOL ≥ threshold.

        baseline_mult: require rvol >= threshold * baseline_mult (baseline=1.0 → absolute).
        For TF: uses last_bar/prev_bar RVOL; day uses quote.rvol.
        """
        thr = max(0.5, float(threshold or 2.0))
        bmult = max(0.5, float(baseline_mult or 1.0))
        need = thr * bmult
        tf_list = [t for t in (intervals or []) if t in TF_INTERVALS]
        include_day = bool(include_day) or not tf_list
        universe_limit = SPIKE_UNIVERSE_LIMIT
        cache_key = (
            f"rvolspike:{need:.2f}:{','.join(tf_list) or '-'}:day={int(include_day)}"
        )
        if not force:
            hit = self._cached(cache_key, ttl=RVOL_ALERT_CACHE_TTL)
            if hit is not None:
                return hit

        universe = self.top_volume_universe(universe_limit)
        spikes: list[dict[str, Any]] = []

        if include_day:
            for q in universe:
                r = q.get("rvol")
                if r is None:
                    continue
                if float(r) >= need:
                    spikes.append({
                        "symbol": q["symbol"],
                        "name": q.get("name"),
                        "price": q.get("price"),
                        "change_pct": q.get("change_pct"),
                        "volume": q.get("volume"),
                        "rvol": r,
                        "rvol10": q.get("rvol10"),
                        "tf": "day",
                        "source": "day_rvol",
                        "value": r,
                        "threshold": need,
                    })

        if tf_list:
            yahoos = [u["yahoo"] for u in universe if u.get("yahoo")]
            by_sym = {u["yahoo"]: u for u in universe if u.get("yahoo")}
            for tf in tf_list:
                try:
                    batch = fetch_bars_batch(yahoos, tf, force=force, batch_size=30,
                        period_override=("5d" if tf not in ("1d", "1w") else None),
                        timeout_sec=30.0, batch_timeout_sec=14.0, use_threads=False)
                except Exception as e:
                    logger.warning("rvol_spike batch %s: %s", tf, e)
                    batch = {}
                for y, bars in (batch or {}).items():
                    info = rvol_from_bars(bars or [])
                    rv = info.get("rvol")
                    if rv is None or float(rv) < need:
                        continue
                    u = by_sym.get(y) or {}
                    spikes.append({
                        "symbol": u.get("symbol") or y.replace(".IS", ""),
                        "name": u.get("name"),
                        "price": u.get("price"),
                        "change_pct": info.get("change_pct") if info.get("change_pct") is not None else u.get("change_pct"),
                        "volume": u.get("volume"),
                        "rvol": rv,
                        "rvol10": u.get("rvol10"),
                        "tf": tf,
                        "source": "rvol_tf",
                        "value": rv,
                        "threshold": need,
                        "last_vol": info.get("last_vol"),
                        "prev_vol": info.get("prev_vol"),
                    })

        # Dedup keep highest value per symbol
        best: dict[str, dict] = {}
        for s in spikes:
            sym = s["symbol"]
            if sym not in best or float(s["value"]) > float(best[sym]["value"]):
                best[sym] = s
        rows = sorted(best.values(), key=lambda x: float(x["value"]), reverse=True)

        market_state = "OPEN" if quote_service.is_market_open() else "CLOSED"
        out = {
            "kind": "rvol_spike",
            "threshold": thr,
            "baseline_mult": bmult,
            "effective_threshold": need,
            "intervals": tf_list,
            "include_day": include_day,
            "count": len(rows),
            "spikes": rows,
            "stocks": rows,
            "coverage": {
                "universe": len(universe),
                "note": (
                    f"RVOL ≥ {need:.2f}× (eş={thr}, baseline_mult={bmult}). "
                    f"Günlük rvol ve/veya TF son mum ÷ önceki mum. Evren: üst {universe_limit} hacim."
                ),
            },
            "market_state": market_state,
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "cache_ttl_sec": RVOL_ALERT_CACHE_TTL,
            "poll_hint_sec": 15,
        }
        self._store(cache_key, out)
        return out

    def rvol10_blast_alerts(
        self,
        threshold: float = 2.0,
        force: bool = False,
    ) -> dict[str, Any]:
        """Hacim patlaması: rvol10 ≥ threshold (today / 10-day avg)."""
        thr = max(0.5, float(threshold or 2.0))
        cache_key = f"rvol10blast:{thr:.2f}"
        if not force:
            hit = self._cached(cache_key, ttl=RVOL_ALERT_CACHE_TTL)
            if hit is not None:
                return hit

        quotes = quote_service._cache or []
        rows = []
        for q in quotes:
            r10 = q.get("rvol10")
            if r10 is None:
                continue
            if float(r10) >= thr:
                rows.append({
                    "symbol": q["symbol"],
                    "name": q.get("name"),
                    "price": q.get("price"),
                    "change_pct": q.get("change_pct"),
                    "volume": q.get("volume"),
                    "avg10_volume": q.get("avg10_volume"),
                    "rvol": q.get("rvol"),
                    "rvol10": r10,
                    "tf": "rvol10",
                    "source": "rvol10",
                    "value": r10,
                    "threshold": thr,
                })
        rows.sort(key=lambda x: float(x["rvol10"]), reverse=True)
        out = {
            "kind": "rvol10_blast",
            "threshold": thr,
            "count": len(rows),
            "spikes": rows,
            "stocks": rows,
            "coverage": {
                "quoted": len(quotes),
                "note": f"rvol10 = today_volume / mean(son 10 işlem günü) ≥ {thr}",
            },
            "market_state": "OPEN" if quote_service.is_market_open() else "CLOSED",
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "cache_ttl_sec": RVOL_ALERT_CACHE_TTL,
            "poll_hint_sec": 15,
        }
        self._store(cache_key, out)
        return out

    def parabolic_scanner(
        self,
        interval: str = "15m",
        limit: int = 40,
        min_score: float = 55.0,
        force: bool = False,
    ) -> dict[str, Any]:
        """Parabolik yükseliş skoru — sortable scanner."""
        from app.features import PARABOLIC_METHOD, compute_parabolic_score

        interval = (interval or "15m").lower()
        if interval not in TF_INTERVALS:
            interval = "15m"
        limit = max(1, min(int(limit or 40), 100))
        min_score = float(min_score or 0)
        universe_limit = SCANNER_UNIVERSE_LIMIT
        cache_key = f"parabolic:{interval}:{limit}:{min_score}:{universe_limit}"
        if not force:
            hit = self._cached(cache_key, ttl=PARABOLIC_CACHE_TTL)
            if hit is not None:
                return hit

        universe = self.top_volume_universe(universe_limit)
        t_scan = time.time()
        deadline = t_scan + 45.0
        yahoo_list = [q["yahoo"] for q in universe if q.get("yahoo")]
        by_yahoo = {q["yahoo"]: q for q in universe if q.get("yahoo")}
        period = "5d" if interval not in ("1d", "1w") else None
        self._prefetch_yahoo_tf(
            yahoo_list,
            interval,
            force=force,
            deadline=deadline,
            period_override=period,
            batch_size=30,
            batch_timeout_sec=14.0,
        )
        # Fill thin/missing via İş Yatırım
        from app.history_cache import history_cache as _hc
        missing = [y for y in yahoo_list if len(_hc.get(y, interval) or []) < 8]
        if missing and time.time() < deadline - 2:
            try:
                self._isyatirim_fill_bars(
                    missing, by_yahoo, tf=interval if interval in ("1m", "5m", "15m", "30m", "1h") else "5m",
                    deadline=deadline, session_only=False,
                )
            except Exception as e:
                logger.warning("parabolic isyatirim: %s", e)

        rows: list[dict[str, Any]] = []
        for q in universe:
            if time.time() >= deadline:
                break
            try:
                sc = compute_parabolic_score(q["symbol"], interval=interval, force=False)
            except Exception as e:
                logger.debug("parabolic %s: %s", q.get("symbol"), e)
                continue
            score = sc.get("score")
            if score is None:
                continue
            if float(score) < min_score:
                continue
            comp = sc.get("components") or {}
            rows.append({
                "symbol": sc["symbol"],
                "name": sc.get("name") or q.get("name"),
                "price": sc.get("price") or q.get("price"),
                "change_pct": sc.get("change_pct") if sc.get("change_pct") is not None else q.get("change_pct"),
                "volume": sc.get("volume") or q.get("volume"),
                "rvol": sc.get("rvol") if sc.get("rvol") is not None else q.get("rvol"),
                "rvol10": sc.get("rvol10") if sc.get("rvol10") is not None else q.get("rvol10"),
                "rvol_tf": sc.get("rvol_tf"),
                "score": score,
                "accel_pct": comp.get("accel_pct"),
                "green_ratio": comp.get("green_ratio"),
                "hh_ratio": comp.get("hh_ratio"),
                "net_return_pct": comp.get("net_return_pct"),
                "interval": interval,
            })
        rows.sort(key=lambda x: float(x["score"]), reverse=True)
        rows = rows[:limit]
        out = {
            "kind": "parabolic",
            "interval": interval,
            "limit": limit,
            "min_score": min_score,
            "count": len(rows),
            "stocks": rows,
            "method": PARABOLIC_METHOD,
            "coverage": {
                "universe": len(universe),
                "note": f"İlk {universe_limit} hacimli; skor ≥ {min_score}; TF={interval}",
            },
            "market_state": "OPEN" if quote_service.is_market_open() else "CLOSED",
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "cache_ttl_sec": PARABOLIC_CACHE_TTL,
        }
        self._store(cache_key, out)
        return out

    def poc_shift_scanner(
        self,
        limit: int = 30,
        mode: str = "hourly",
        force: bool = False,
    ) -> dict[str, Any]:
        """Largest absolute POC shifts in session (top volume names)."""
        from app.features import POC_SHIFT_METHOD, compute_poc_migration

        limit = max(1, min(int(limit or 30), 80))
        mode = (mode or "hourly").lower()
        universe_limit = min(60, SCANNER_UNIVERSE_LIMIT)  # heavy
        cache_key = f"pocshift:{mode}:{limit}:{universe_limit}"
        if not force:
            hit = self._cached(cache_key, ttl=POC_SCAN_CACHE_TTL)
            if hit is not None:
                return hit

        universe = self.top_volume_universe(universe_limit)
        t_scan = time.time()
        deadline = t_scan + 45.0
        yahoo_list = [q["yahoo"] for q in universe if q.get("yahoo")]
        by_yahoo = {q["yahoo"]: q for q in universe if q.get("yahoo")}
        self._prefetch_yahoo_tf(
            yahoo_list, "5m", force=force, deadline=deadline,
            period_override="5d", batch_size=25, batch_timeout_sec=14.0,
        )
        # 1m if time remains (better POC windows)
        if time.time() < deadline - 8:
            self._prefetch_yahoo_tf(
                yahoo_list, "1m", force=False, deadline=deadline,
                period_override="5d", batch_size=25, batch_timeout_sec=12.0,
            )
        from app.history_cache import history_cache as _hc
        missing = [
            y for y in yahoo_list
            if len(_hc.get(y, "5m") or []) < 5 and len(_hc.get(y, "1m") or []) < 10
        ]
        if missing and time.time() < deadline - 2:
            try:
                self._isyatirim_fill_bars(
                    missing, by_yahoo, tf="5m", deadline=deadline, session_only=True,
                )
            except Exception as e:
                logger.warning("pocshift isyatirim: %s", e)

        rows: list[dict[str, Any]] = []
        for q in universe:
            if time.time() >= deadline:
                break
            try:
                mig = compute_poc_migration(q["symbol"], mode=mode, force=False)
            except Exception as e:
                logger.debug("pocshift %s: %s", q.get("symbol"), e)
                continue
            shift = mig.get("poc_shift")
            if shift is None:
                continue
            rows.append({
                "symbol": mig["symbol"],
                "name": q.get("name"),
                "price": q.get("price"),
                "change_pct": q.get("change_pct"),
                "rvol": q.get("rvol"),
                "rvol10": q.get("rvol10"),
                "current_poc": mig.get("current_poc"),
                "earlier_poc": mig.get("earlier_poc"),
                "session_open_poc": mig.get("session_open_poc"),
                "poc_shift": shift,
                "poc_shift_pct": mig.get("poc_shift_pct"),
                "poc_shift_vs_open": mig.get("poc_shift_vs_open"),
                "poc_shift_vs_open_pct": mig.get("poc_shift_vs_open_pct"),
                "direction": mig.get("direction"),
                "window_count": mig.get("window_count"),
                "abs_shift": abs(float(shift)),
            })
        rows.sort(key=lambda x: x["abs_shift"], reverse=True)
        rows = rows[:limit]
        out = {
            "kind": "poc_shift",
            "mode": mode,
            "limit": limit,
            "count": len(rows),
            "stocks": rows,
            "method": POC_SHIFT_METHOD,
            "coverage": {
                "universe": len(universe),
                "note": f"İlk {universe_limit} hacimli; saatlik POC kayması |ΔPOC| sıralı",
            },
            "market_state": "OPEN" if quote_service.is_market_open() else "CLOSED",
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "cache_ttl_sec": POC_SCAN_CACHE_TTL,
        }
        self._store(cache_key, out)
        return out


    def high_breaks_scanner(
        self,
        limit: int = 30,
        min_breaks: int = 1,
        force: bool = False,
    ) -> dict[str, Any]:
        """Most intraday high-break prints among top-volume names."""
        from app.features import HIGH_BREAK_METHOD, compute_high_breaks

        limit = max(1, min(int(limit or 30), 80))
        min_breaks = max(0, int(min_breaks or 0))
        universe_limit = min(50, SCANNER_UNIVERSE_LIMIT)
        cache_key = f"highbreaks:{limit}:{min_breaks}:{universe_limit}"
        if not force:
            hit = self._cached(cache_key, ttl=HIGH_BREAK_CACHE_TTL)
            if hit is not None:
                return hit

        universe = self.top_volume_universe(universe_limit)
        t_scan = time.time()
        deadline = t_scan + 45.0
        yahoo_list = [q["yahoo"] for q in universe if q.get("yahoo")]
        by_yahoo = {q["yahoo"]: q for q in universe if q.get("yahoo")}
        self._prefetch_yahoo_tf(
            yahoo_list, "1m", force=force, deadline=deadline,
            period_override="5d", batch_size=25, batch_timeout_sec=14.0,
        )
        from app.history_cache import history_cache as _hc
        missing = [y for y in yahoo_list if len(_hc.get(y, "1m") or []) < 10]
        if missing and time.time() < deadline - 2:
            try:
                self._isyatirim_fill_bars(
                    missing, by_yahoo, tf="1m", deadline=deadline, session_only=True,
                )
                still = [y for y in missing if len(_hc.get(y, "1m") or []) < 10]
                if still:
                    self._isyatirim_fill_bars(
                        still, by_yahoo, tf="5m", deadline=deadline, session_only=True,
                    )
            except Exception as e:
                logger.warning("highbreaks isyatirim: %s", e)

        rows: list[dict[str, Any]] = []
        for q in universe:
            if time.time() >= deadline:
                break
            try:
                hb = compute_high_breaks(q["symbol"], force=False)
            except Exception as e:
                logger.debug("highbreaks %s: %s", q.get("symbol"), e)
                continue
            cnt = int(hb.get("high_break_count") or 0)
            if cnt < min_breaks:
                continue
            rows.append({
                "symbol": hb["symbol"],
                "name": q.get("name"),
                "price": q.get("price"),
                "change_pct": q.get("change_pct"),
                "volume": q.get("volume"),
                "rvol": q.get("rvol"),
                "rvol10": q.get("rvol10"),
                "high_break_count": cnt,
                "max_vol_break_price": hb.get("max_vol_break_price"),
                "max_vol_break_volume": hb.get("max_vol_break_volume"),
                "session_high": hb.get("session_high"),
                "breaks": (hb.get("breaks") or [])[-8:],
                "source_tf": hb.get("source_tf"),
            })
        rows.sort(key=lambda x: x["high_break_count"], reverse=True)
        rows = rows[:limit]
        out = {
            "kind": "high_breaks",
            "limit": limit,
            "min_breaks": min_breaks,
            "count": len(rows),
            "stocks": rows,
            "method": HIGH_BREAK_METHOD,
            "coverage": {
                "universe": len(universe),
                "note": f"İlk {universe_limit} hacimli; high_break_count sıralı",
            },
            "market_state": "OPEN" if quote_service.is_market_open() else "CLOSED",
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "cache_ttl_sec": HIGH_BREAK_CACHE_TTL,
        }
        self._store(cache_key, out)
        return out

    def volume_break_alerts(
        self,
        limit: int = 40,
        min_breaks: int = 1,
        latest_only: bool = True,
        force: bool = False,
    ) -> dict[str, Any]:
        """Hacimli Kırılım alarmı (v1.14.2).

        ONLY fire when ALL are true for a stock that day:
          1) ≥1 running day-high break (intraday)
          2) the LATEST session break is also the highest-volume break
             (son kırılım = max hacimli kırılım) — not historical ranking
          3) price rises with that break: bullish candle (close>open) AND
             close > prior high AND last ≥ prior high / broken level (no fake wick)

        Scans the full liquid top-volume universe. `latest_only` is always
        enforced (required logic; query flag kept for API compat).
        """
        from app.features import (
            HIGH_BREAK_METHOD,
            VOLUME_BREAK_ALARM_RULE,
            compute_high_breaks,
        )

        limit = max(1, min(int(limit or 40), 80))
        min_breaks = max(1, int(min_breaks or 1))
        # Required: latest == max-volume; ranking-as-alarm removed
        latest_only = True
        universe_limit = SCANNER_UNIVERSE_LIMIT  # all liquid (~150)
        cache_key = f"volbreak:v1142b:{limit}:{min_breaks}:{universe_limit}"
        if not force:
            hit = self._cached(cache_key, ttl=VOLUME_BREAK_CACHE_TTL)
            if hit is not None:
                return hit

        universe = self.top_volume_universe(universe_limit)
        t_scan = time.time()
        deadline = t_scan + 55.0
        yahoo_list = [q["yahoo"] for q in universe if q.get("yahoo")]
        by_yahoo = {q["yahoo"]: q for q in universe if q.get("yahoo")}
        self._prefetch_yahoo_tf(
            yahoo_list, "1m", force=force, deadline=deadline,
            period_override="5d", batch_size=25, batch_timeout_sec=14.0,
        )
        from app.history_cache import history_cache as _hc
        missing = [y for y in yahoo_list if len(_hc.get(y, "1m") or []) < 10]
        if missing and time.time() < deadline - 2:
            try:
                self._isyatirim_fill_bars(
                    missing, by_yahoo, tf="1m", deadline=deadline, session_only=True,
                )
                still = [y for y in missing if len(_hc.get(y, "1m") or []) < 10]
                if still:
                    self._isyatirim_fill_bars(
                        still, by_yahoo, tf="5m", deadline=deadline, session_only=True,
                    )
            except Exception as e:
                logger.warning("volbreak isyatirim: %s", e)

        rows: list[dict[str, Any]] = []
        scanned = 0
        skipped_not_latest_max = 0
        skipped_not_rising = 0
        for q in universe:
            if time.time() >= deadline:
                break
            scanned += 1
            try:
                hb = compute_high_breaks(q["symbol"], force=False)
            except Exception as e:
                logger.debug("volbreak %s: %s", q.get("symbol"), e)
                continue
            cnt = int(hb.get("high_break_count") or 0)
            if cnt < min_breaks:
                continue
            breaks = hb.get("breaks") or []
            if not breaks:
                continue

            # (2) son kırılım == max hacimli kırılım
            latest = breaks[-1]
            max_vol = max(int(b.get("volume") or 0) for b in breaks)
            latest_vol = int(latest.get("volume") or 0)
            if latest_vol < max_vol:
                skipped_not_latest_max += 1
                continue

            break_price = latest.get("price")
            if break_price is None:
                continue

            # (3) fiyat kırılımla yükselir — wick/fake değil
            o = latest.get("open")
            c = latest.get("close")
            prev_high = latest.get("prev_high")
            last = q.get("price")
            try:
                bullish = (
                    o is not None and c is not None and float(c) > float(o)
                )
            except (TypeError, ValueError):
                bullish = False
            try:
                close_above_prior = (
                    c is not None
                    and prev_high is not None
                    and float(c) > float(prev_high)
                )
            except (TypeError, ValueError):
                close_above_prior = bool(latest.get("close_above_prior"))
            # Holding = last still above the BROKEN level (prev_high), not the
            # wick extreme (break high). last≥high almost never holds (delay/pullback).
            try:
                holding = (
                    last is not None
                    and prev_high is not None
                    and float(last) >= float(prev_high)
                )
            except (TypeError, ValueError):
                holding = False
            price_rising = bool(bullish and close_above_prior and holding)
            if not price_rising:
                skipped_not_rising += 1
                continue

            rows.append({
                "symbol": hb["symbol"],
                "name": q.get("name"),
                "price": last,
                "change_pct": q.get("change_pct"),
                "volume": q.get("volume"),
                "rvol": q.get("rvol"),
                "rvol10": q.get("rvol10"),
                "high_break_count": cnt,
                "break_price": break_price,
                "break_volume": latest_vol,
                "max_vol_break_price": break_price,
                "max_vol_break_volume": latest_vol,
                "break_time": latest.get("time") or latest.get("date"),
                "break_open": o,
                "break_close": c,
                "break_prev_high": prev_high,
                "bullish": bullish,
                "close_above_prior": close_above_prior,
                "holding": holding,
                "price_rising": True,
                "is_latest_max": True,
                "session_high": hb.get("session_high"),
                "source_tf": hb.get("source_tf"),
            })

        # Display order: most recent break first (not ranking-as-alarm)
        rows.sort(
            key=lambda x: (x.get("break_time") is None, x.get("break_time") or 0),
            reverse=True,
        )
        for i, r in enumerate(rows, start=1):
            r["hit_rank"] = i
        rows = rows[:limit]

        formula = (
            "Hacimli Kırılım (zorunlu filtre): "
            "(1) ≥1 running day-high kırılımı (1m→5m) · "
            "(2) son kırılım = günün max-hacimli kırılımı · "
            "(3) mum yükseliş (close>open) + close>önceki yüksek + last≥kırılan seviye (prev_high). "
            "Geçmiş max-hacim sıralaması alarm DEĞİL."
        )
        out = {
            "kind": "volume_break",
            "limit": limit,
            "min_breaks": min_breaks,
            "latest_only": True,
            "count": len(rows),
            "scanned": scanned,
            "quoted": len(universe),
            "spikes": rows,
            "breaks": rows,
            "method": HIGH_BREAK_METHOD,
            "formula": formula,
            "rule_tr": VOLUME_BREAK_ALARM_RULE,
            "filter": {
                "require_latest_is_max_vol": True,
                "require_price_rising": True,
                "price_rising_checks": [
                    "close > open (bullish)",
                    "close > prev_high (confirmed, not wick)",
                    "last >= prev_high / kırılan seviye (holding; not wick high)",
                ],
                "skipped_not_latest_max": skipped_not_latest_max,
                "skipped_not_rising": skipped_not_rising,
            },
            "coverage": {
                "universe": len(universe),
                "scanned": scanned,
                "limit": universe_limit,
                "note": (
                    f"Tüm likit evren (top {universe_limit}); "
                    "yalnızca son=max hacim + yükseliş teyidi"
                ),
            },
            "market_state": "OPEN" if quote_service.is_market_open() else "CLOSED",
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "cache_ttl_sec": VOLUME_BREAK_CACHE_TTL,
        }
        self._store(cache_key, out)
        return out


    def momentum_burst_scanner(
        self,
        window_min: int = 5,
        limit: int = 40,
        min_score: float = 50.0,
        min_window_pct: float | None = None,
        require_accel: bool = True,
        green_n: int = 3,
        force: bool = False,
    ) -> dict[str, Any]:
        """Momentumlu Hızlanış — rare upward bursts in last W minutes."""
        from app.features import (
            MOMENTUM_ALARM_RULE,
            MOMENTUM_BURST_METHOD,
            MOMENTUM_RARE_PCT,
            MOMENTUM_WINDOWS,
            compute_momentum_burst,
        )

        try:
            w = int(window_min)
        except (TypeError, ValueError):
            w = 5
        if w not in MOMENTUM_WINDOWS:
            w = min(MOMENTUM_WINDOWS, key=lambda x: abs(x - w))
        limit = max(1, min(int(limit or 40), 100))
        min_score = float(min_score if min_score is not None else 50.0)
        if min_window_pct is None:
            thr_pct = float(MOMENTUM_RARE_PCT.get(w, 1.8)) * 0.55  # soft floor ~half of "rare"
        else:
            thr_pct = float(min_window_pct)
        green_n = max(1, min(int(green_n or 3), 10))
        universe_limit = SCANNER_UNIVERSE_LIMIT
        cache_key = (
            f"momentum:v115:{w}:{limit}:{min_score}:{thr_pct}:"
            f"{int(require_accel)}:{green_n}:{universe_limit}"
        )
        if not force:
            hit = self._cached(cache_key, ttl=MOMENTUM_CACHE_TTL)
            if hit is not None:
                return hit

        universe = self.top_volume_universe(universe_limit)
        t_scan = time.time()
        deadline = t_scan + 50.0
        yahoo_list = [q["yahoo"] for q in universe if q.get("yahoo")]
        by_yahoo = {q["yahoo"]: q for q in universe if q.get("yahoo")}
        isy_ok = 0

        # Prefetch 1m (primary) then fill thin via 5m / İş Yatırım
        self._prefetch_yahoo_tf(
            yahoo_list, "1m", force=force, deadline=deadline,
            period_override="5d", batch_size=25, batch_timeout_sec=14.0,
        )
        from app.history_cache import history_cache as _hc
        missing = [y for y in yahoo_list if len(_hc.get(y, "1m") or []) < 8]
        if missing and time.time() < deadline - 3:
            self._prefetch_yahoo_tf(
                missing, "5m", force=force, deadline=deadline,
                period_override="5d", batch_size=25, batch_timeout_sec=12.0,
            )
        missing = [y for y in yahoo_list if len(_hc.get(y, "1m") or []) < 8 and len(_hc.get(y, "5m") or []) < 4]
        if missing and time.time() < deadline - 2:
            try:
                isy_ok = self._isyatirim_fill_bars(
                    missing, by_yahoo, tf="1m", deadline=deadline, session_only=True,
                )
                still = [y for y in missing if len(_hc.get(y, "1m") or []) < 8]
                if still:
                    isy_ok += self._isyatirim_fill_bars(
                        still, by_yahoo, tf="5m", deadline=deadline, session_only=True,
                    )
            except Exception as e:
                logger.warning("momentum isyatirim: %s", e)

        rows: list[dict[str, Any]] = []
        scanned = 0
        for q in universe:
            if time.time() >= deadline:
                break
            scanned += 1
            try:
                m = compute_momentum_burst(
                    q["symbol"], window_min=w, force=False, green_n=green_n,
                )
            except Exception as e:
                logger.debug("momentum %s: %s", q.get("symbol"), e)
                continue
            score = m.get("score")
            wp = m.get("window_pct")
            if score is None or wp is None:
                continue
            if float(wp) < thr_pct:
                continue
            if float(score) < min_score:
                continue
            if require_accel and (m.get("accel_pct") is None or float(m["accel_pct"]) <= 0):
                continue
            rows.append({
                "symbol": m["symbol"],
                "name": m.get("name") or q.get("name"),
                "price": m.get("price") if m.get("price") is not None else q.get("price"),
                "change_pct": m.get("change_pct") if m.get("change_pct") is not None else q.get("change_pct"),
                "volume": m.get("volume") or q.get("volume"),
                "rvol": m.get("rvol") if m.get("rvol") is not None else q.get("rvol"),
                "rvol10": m.get("rvol10") if m.get("rvol10") is not None else q.get("rvol10"),
                "score": score,
                "window_pct": wp,
                "velocity_pct": m.get("velocity_pct"),
                "accel_pct": m.get("accel_pct"),
                "vol_surge": m.get("vol_surge"),
                "green_ratio": m.get("green_ratio"),
                "green_streak": m.get("green_streak"),
                "all_green": m.get("all_green"),
                "window_min": w,
                "source_tf": m.get("source_tf"),
                "window_start": m.get("window_start"),
                "window_end": m.get("window_end"),
                "bar_count_window": m.get("bar_count_window"),
            })

        # Hottest / rarest first: score then window_pct then accel
        rows.sort(
            key=lambda x: (
                float(x.get("score") or 0),
                float(x.get("window_pct") or 0),
                float(x.get("accel_pct") or 0),
                float(x.get("vol_surge") or 0),
            ),
            reverse=True,
        )
        for i, r in enumerate(rows, start=1):
            r["rank"] = i
        rows = rows[:limit]

        formula = (
            f"Momentumlu Hızlanış (son {w} dk): "
            "window_%=(C_son−C_ilk)/C_ilk×100 · velocity=window_% · "
            "accel_%=ret₂−ret₁ · vol_surge=vol_W/vol_önceki_W · "
            "skor=0.35·W+0.30·accel+0.20·vol+0.15·yeşil (+all-green). "
            f"Filtre: window_%≥{thr_pct:.2f} · skor≥{min_score}"
            + (" · accel>0" if require_accel else "")
            + "."
        )
        out = {
            "kind": "momentum",
            "window_min": w,
            "limit": limit,
            "min_score": min_score,
            "min_window_pct": thr_pct,
            "require_accel": bool(require_accel),
            "green_n": green_n,
            "count": len(rows),
            "scanned": scanned,
            "stocks": rows,
            "method": MOMENTUM_BURST_METHOD,
            "formula": formula,
            "rule_tr": MOMENTUM_ALARM_RULE,
            "coverage": {
                "universe": len(universe),
                "scanned": scanned,
                "limit": universe_limit,
                "isyatirim_ok": isy_ok,
                "note": (
                    f"Tüm likit evren (top {universe_limit}); pencere={w}dk; "
                    f"Yahoo 1m→5m timeout"
                    + (" + İş Yatırım" if isy_ok else "")
                ),
            },
            "market_state": "OPEN" if quote_service.is_market_open() else "CLOSED",
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "cache_ttl_sec": MOMENTUM_CACHE_TTL,
        }
        self._store(cache_key, out)
        return out

    def momentum_burst_alerts(
        self,
        window_min: int = 5,
        min_score: float = 60.0,
        min_window_pct: float | None = None,
        require_accel: bool = True,
        green_n: int = 3,
        limit: int = 40,
        force: bool = False,
    ) -> dict[str, Any]:
        """Alarm wrapper — same logic, returns spikes[] for poller."""
        from app.features import MOMENTUM_ALARM_RULE, MOMENTUM_RARE_PCT, MOMENTUM_WINDOWS

        try:
            w = int(window_min)
        except (TypeError, ValueError):
            w = 5
        if w not in MOMENTUM_WINDOWS:
            w = min(MOMENTUM_WINDOWS, key=lambda x: abs(x - w))
        # Stricter default floor for alarms (closer to rare reference)
        if min_window_pct is None:
            min_window_pct = float(MOMENTUM_RARE_PCT.get(w, 1.8)) * 0.75

        data = self.momentum_burst_scanner(
            window_min=w,
            limit=limit,
            min_score=min_score,
            min_window_pct=min_window_pct,
            require_accel=require_accel,
            green_n=green_n,
            force=force,
        )
        spikes = []
        for r in data.get("stocks") or []:
            spikes.append({
                **r,
                "tf": f"{w}m",
                "interval": f"{w}m",
                "value": r.get("score"),
                "source": "momentum",
            })
        return {
            "kind": "momentum_alert",
            "window_min": w,
            "min_score": min_score,
            "min_window_pct": min_window_pct,
            "require_accel": bool(require_accel),
            "count": len(spikes),
            "spikes": spikes,
            "stocks": spikes,
            "method": data.get("method"),
            "formula": data.get("formula"),
            "rule_tr": MOMENTUM_ALARM_RULE,
            "coverage": data.get("coverage"),
            "market_state": data.get("market_state"),
            "updated": data.get("updated"),
            "cache_ttl_sec": data.get("cache_ttl_sec"),
        }

    def check_price_alerts(
        self,
        alerts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Evaluate price target alerts against quote cache.

        Each alert: {symbol, op: 'gte'|'lte'|'>'|'<'|'>='|'<=', target: float, id?: str}
        """
        quotes = {q["symbol"]: q for q in (quote_service._cache or [])}
        triggered = []
        pending = []
        for a in alerts or []:
            sym = str(a.get("symbol") or "").upper().replace(".IS", "")
            if not sym:
                continue
            try:
                target = float(a.get("target"))
            except (TypeError, ValueError):
                continue
            op = (a.get("op") or a.get("direction") or "gte").lower()
            q = quotes.get(sym)
            price = q.get("price") if q else None
            if price is None:
                pending.append({**a, "symbol": sym, "status": "no_quote"})
                continue
            hit = False
            if op in ("gte", ">=", "above", "ge"):
                hit = float(price) >= target
                op_norm = "gte"
            elif op in ("lte", "<=", "below", "le"):
                hit = float(price) <= target
                op_norm = "lte"
            elif op in ("gt", ">"):
                hit = float(price) > target
                op_norm = "gt"
            elif op in ("lt", "<"):
                hit = float(price) < target
                op_norm = "lt"
            else:
                op_norm = "gte"
                hit = float(price) >= target
            item = {
                "id": a.get("id"),
                "symbol": sym,
                "name": (q or {}).get("name"),
                "op": op_norm,
                "target": target,
                "price": price,
                "change_pct": (q or {}).get("change_pct"),
                "triggered": hit,
                "distance_pct": round((float(price) - target) / target * 100.0, 3) if target else None,
            }
            if hit:
                triggered.append(item)
            else:
                pending.append({**item, "status": "watching"})
        return {
            "kind": "price_alerts",
            "triggered": triggered,
            "pending": pending,
            "triggered_count": len(triggered),
            "checked": len(triggered) + len(pending),
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "market_state": "OPEN" if quote_service.is_market_open() else "CLOSED",
        }

    def israrcilar_scanner(
        self,
        limit: int = 40,
        min_change: float = 2.0,
        min_score: float = 40.0,
        include_near: bool = True,
        force: bool = False,
    ) -> dict[str, Any]:
        """Israrcılar — persistence-first (reclaim/score); day% soft floor only.

        TAVAN (≥+%8) is a badge, not a list gate. Soft noise floor ~+%2 OR strong
        persistence (reclaim_count / score) so ~+%3 true ısrarcılar still appear.
        """
        from app.features import PERSISTENCE_METHOD, compute_persistence

        limit = max(1, min(int(limit or 40), 80))
        # Soft day-% floor for noise (NOT a hard ≥5/≥8 gate)
        soft_floor = float(min_change if min_change is not None else 2.0)
        min_score = float(min_score if min_score is not None else 40.0)
        universe_limit = min(220, max(SCANNER_UNIVERSE_LIMIT, 180))
        cache_key = f"israrcilar:v2:{limit}:{soft_floor}:{min_score}:{int(include_near)}:{universe_limit}"
        if not force:
            hit = self._cached(cache_key, ttl=ISRARCILAR_CACHE_TTL)
            if hit is not None:
                return hit

        # Liquid universe (top volume). Optionally seed mild gainers (≥ soft_floor)
        # so mid-cap ısrarcılar outside top-N volume are not missed — NOT ≥5% only.
        base = self.top_volume_universe(universe_limit)
        by_sym = {q["symbol"]: q for q in base}
        quotes = quote_service._cache or []
        for q in quotes:
            chg = q.get("change_pct")
            vol = q.get("volume") or 0
            if chg is None or float(chg) < soft_floor:
                continue
            if vol < 50_000:
                continue
            if q["symbol"] not in by_sym:
                by_sym[q["symbol"]] = q
        universe = list(by_sym.values())
        # Prefer volume; soft mix of day% for coverage when capping
        universe.sort(
            key=lambda q: (
                -(q.get("volume") or 0),
                (q.get("change_pct") is None),
                -(q.get("change_pct") or 0),
            )
        )
        if len(universe) > universe_limit:
            top_vol = self.top_volume_universe(universe_limit)
            mild = [
                q for q in universe
                if (q.get("change_pct") or 0) >= soft_floor
            ][: max(60, universe_limit // 3)]
            seen: set[str] = set()
            merged: list[dict] = []
            for q in top_vol + mild:
                if q["symbol"] in seen:
                    continue
                seen.add(q["symbol"])
                merged.append(q)
                if len(merged) >= universe_limit:
                    break
            universe = merged

        # --- Prefetch bars (Yahoo batch + timeouts + İş Yatırım) so per-symbol
        # compute_persistence never stalls on bare yfinance history ---
        t_scan = time.time()
        ISR_DEADLINE = 48.0
        deadline = t_scan + ISR_DEADLINE
        yahoo_list = [q["yahoo"] for q in universe if q.get("yahoo")]
        by_yahoo = {q["yahoo"]: q for q in universe if q.get("yahoo")}
        source_notes: list[str] = []

        # Prefer 1m (persistence needs ~20+ session bars early day); short lookback
        b1 = self._prefetch_yahoo_tf(
            yahoo_list,
            "1m",
            force=force,
            deadline=deadline,
            period_override="5d",
            batch_size=25,
            batch_timeout_sec=14.0,
        )
        yahoo_1m_ok = sum(1 for bars in b1.values() if bars and len(bars) >= 10)
        source_notes.append(f"Yahoo 5d/1m: {yahoo_1m_ok}/{len(yahoo_list)}")

        # 5m backup for symbols still thin
        need_5m = [
            y for y in yahoo_list
            if len(b1.get(y) or []) < 15 and (deadline - time.time()) > 4
        ]
        yahoo_5m_ok = 0
        if need_5m:
            b5 = self._prefetch_yahoo_tf(
                need_5m,
                "5m",
                force=force,
                deadline=deadline,
                period_override="5d",
                batch_size=25,
                batch_timeout_sec=12.0,
            )
            yahoo_5m_ok = sum(1 for bars in b5.values() if bars and len(bars) >= 5)
            source_notes.append(f"Yahoo 5d/5m: {yahoo_5m_ok}/{len(need_5m)}")

        # İş Yatırım fill for symbols still missing usable bars
        missing = []
        for y in yahoo_list:
            b = b1.get(y) or []
            if len(b) >= 15:
                continue
            # 5m may already be cached from prefetch
            from app.history_cache import history_cache as _hc
            b5c = _hc.get(y, "5m") or []
            if len(b5c) >= 8:
                continue
            missing.append(y)
        isy_ok = 0
        if missing and time.time() < deadline - 2:
            try:
                isy_ok = self._isyatirim_fill_bars(
                    missing,
                    by_yahoo,
                    tf="1m",
                    deadline=deadline,
                    session_only=True,
                )
                # also try 5m for still-missing
                still = []
                from app.history_cache import history_cache as _hc2
                for y in missing:
                    if len(_hc2.get(y, "1m") or []) < 15 and len(_hc2.get(y, "5m") or []) < 8:
                        still.append(y)
                if still and time.time() < deadline - 2:
                    isy_ok += self._isyatirim_fill_bars(
                        still,
                        by_yahoo,
                        tf="5m",
                        deadline=deadline,
                        session_only=True,
                    )
                source_notes.append(f"İş Yatırım fallback: {isy_ok}/{len(missing)}")
            except Exception as e:
                logger.warning("israrcilar isyatirim fallback: %s", e)
                source_notes.append(f"İş Yatırım hata: {e}")

        rows: list[dict[str, Any]] = []
        scanned = 0
        for q in universe:
            if time.time() >= deadline:
                source_notes.append("deadline_cut")
                break
            try:
                pers = compute_persistence(q["symbol"], force=False)
            except Exception as e:
                logger.debug("israrcilar %s: %s", q.get("symbol"), e)
                continue
            scanned += 1
            score = pers.get("persistence_score")
            chg = pers.get("change_pct")
            if chg is None:
                chg = q.get("change_pct")
            if score is None:
                continue
            reclaim_count = int(pers.get("reclaim_count") or 0)
            tavan = bool(pers.get("tavan_badge"))
            near = bool(pers.get("near_tavan"))
            chg_f = float(chg) if chg is not None else -999.0
            sc = float(score)

            # Persistence-quality gates (NO hard ≥5% / ≥8% primary filter)
            pass_soft = (
                chg_f >= soft_floor
                and reclaim_count >= 1
                and sc >= min_score
            )
            pass_strong = (
                reclaim_count >= 2
                and sc >= max(min_score, 50.0)
                and chg_f >= 0.0
            )
            pass_elite = (
                reclaim_count >= 1
                and sc >= max(min_score + 20, 60.0)
                and chg_f >= 0.0
            )
            pass_badge = (tavan or (include_near and near)) and sc >= 25.0

            if not (pass_soft or pass_strong or pass_elite or pass_badge):
                continue

            rows.append({
                "symbol": pers["symbol"],
                "name": pers.get("name") or q.get("name"),
                "price": pers.get("last") or q.get("price"),
                "last": pers.get("last") or q.get("price"),
                "change_pct": chg_f if chg is not None else q.get("change_pct"),
                "volume": pers.get("volume") or q.get("volume"),
                "rvol": pers.get("rvol") if pers.get("rvol") is not None else q.get("rvol"),
                "rvol10": pers.get("rvol10") if pers.get("rvol10") is not None else q.get("rvol10"),
                "reclaim_count": reclaim_count,
                "persistence_score": sc,
                "key_buy_level": pers.get("key_buy_level"),
                "key_level_volume": pers.get("key_level_volume"),
                "avg_reclaim_minutes": pers.get("avg_reclaim_minutes"),
                "buy_pressure_pct": pers.get("buy_pressure_pct"),
                "net_buy_vol": pers.get("net_buy_vol"),
                "yorum": pers.get("yorum"),
                "tavan_badge": tavan or chg_f >= 8.0,
                "near_tavan": near,
                "source_tf": pers.get("source_tf"),
                "date": pers.get("date"),
            })

        # Rank: persistence_score first; soft day% already baked into score
        rows.sort(
            key=lambda x: (
                -float(x.get("persistence_score") or 0),
                -int(x.get("reclaim_count") or 0),
                -float(x.get("change_pct") or 0),
            )
        )
        rows = rows[:limit]
        elapsed = round(time.time() - t_scan, 1)
        warn = None
        if not rows and scanned == 0:
            warn = (
                "Israrcılar verisi alınamadı (Yahoo zaman aşımı / boş bar; "
                "İş Yatırım yedek de yetersiz). Piyasa yeni açıldıysa bar birikmesini bekleyin."
            )
        note = (
            f"Likit evren (~{universe_limit}); liste israr skoru / geri alma ile. "
            f"Gürültü yumuşak taban gün ≥+%{soft_floor:g} VEYA yüksek skor/reclaim. "
            f"TAVAN rozeti ≥+%8 (filtre değil). "
            f"Kaynak: Yahoo 5d/1m+5m (timeout){' + İş Yatırım' if isy_ok else ''}. "
            f"{' · '.join(source_notes)}. Süre: {elapsed}s. Taranan: {scanned}."
        )
        out = {
            "kind": "israrcilar",
            "limit": limit,
            "min_change": soft_floor,
            "min_score": min_score,
            "include_near": include_near,
            "filter_mode": "persistence_first",
            "count": len(rows),
            "stocks": rows,
            "method": PERSISTENCE_METHOD,
            "coverage": {
                "universe": len(universe),
                "scanned": scanned,
                "yahoo_1m_ok": yahoo_1m_ok,
                "yahoo_5m_ok": yahoo_5m_ok,
                "isyatirim_ok": isy_ok,
                "elapsed_sec": elapsed,
                "note": note,
                "warning": warn,
            },
            "error": warn,
            "market_state": "OPEN" if quote_service.is_market_open() else "CLOSED",
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "cache_ttl_sec": ISRARCILAR_CACHE_TTL,
            "subtitle": "Israr skoru · TAVAN rozeti (filtre değil)",
        }
        # Cache successful / partial rows; avoid sticky empty failure cache
        if rows or scanned > 0:
            self._store(cache_key, out)
        return out

    def trade_plans_scanner(
        self,
        limit: int = 120,
        actionable_only: bool = False,
        universe_limit: int | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """İşlem Planları — LONG/SHORT/WAIT plans over top-volume liquid universe.

        Default sort: actionable (LONG/SHORT) first by nearest |entry_distance_pct|,
        then WAIT by |change_pct|. Columns include volumes (from net-volume warm)
        and plan levels (entry/stop/tp1/tp2/rr/risk).
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        from app.analysis import compute_volume_profile
        from app.features import TRADE_PLAN_METHOD, compute_trade_plan

        limit = max(1, min(int(limit or 120), 200))
        uni_lim = int(universe_limit) if universe_limit else min(180, max(SCANNER_UNIVERSE_LIMIT, 150))
        uni_lim = max(50, min(uni_lim, 220))
        cache_key = f"tradeplans:v1:{limit}:{int(actionable_only)}:{uni_lim}"
        if not force:
            hit = self._cached(cache_key, ttl=TRADE_PLANS_CACHE_TTL)
            if hit is not None:
                return hit

        universe = self.top_volume_universe(uni_lim)
        t_scan = time.time()
        TP_DEADLINE = 50.0
        deadline = t_scan + TP_DEADLINE
        yahoo_list = [q["yahoo"] for q in universe if q.get("yahoo")]
        by_yahoo = {q["yahoo"]: q for q in universe if q.get("yahoo")}

        # Warm buy/sell/net via net-volume scan (cached ~240s; also warms bars)
        nv_map: dict[str, dict] = {}
        try:
            nv = self.net_volume(limit=uni_lim, sort="net", universe_limit=uni_lim, force=False)
            for r in nv.get("stocks") or []:
                if r.get("symbol"):
                    nv_map[r["symbol"]] = r
        except Exception as e:
            logger.warning("tradeplans net_volume warm: %s", e)

        # Extra 5m/1m prefetch so persistence/VP don't hang on Yahoo
        try:
            self._prefetch_yahoo_tf(
                yahoo_list, "5m", force=False, deadline=deadline,
                period_override="5d", batch_size=25, batch_timeout_sec=12.0,
            )
            if time.time() < deadline - 6:
                self._prefetch_yahoo_tf(
                    yahoo_list, "1m", force=False, deadline=deadline,
                    period_override="5d", batch_size=25, batch_timeout_sec=10.0,
                )
            from app.history_cache import history_cache as _hc
            missing = [
                y for y in yahoo_list
                if len(_hc.get(y, "5m") or []) < 3 and len(_hc.get(y, "1m") or []) < 5
            ]
            if missing and time.time() < deadline - 2:
                self._isyatirim_fill_bars(
                    missing, by_yahoo, tf="5m", deadline=deadline, session_only=True,
                )
        except Exception as e:
            logger.warning("tradeplans prefetch: %s", e)

        def _one(q: dict) -> dict[str, Any] | None:
            sym = q.get("symbol")
            if not sym:
                return None
            if time.time() >= deadline:
                return None
            try:
                try:
                    fp = compute_volume_profile(sym, date_str="today", force=False)
                except Exception:
                    fp = {}
                # Skip nested persistence/high_breaks Yahoo (prefetched OR omit)
                # to keep scanner under deadline — plan still works from FP/signal/SR/VWAP.
                plan = compute_trade_plan(
                    sym,
                    force=False,
                    quote=q,
                    footprint=fp or {},
                    persistence={},
                    high_breaks={},
                )
            except Exception as e:
                logger.debug("tradeplans %s: %s", sym, e)
                return None

            direction = (plan.get("direction") or "WAIT").upper()
            if actionable_only and direction not in ("LONG", "SHORT"):
                return None

            last = plan.get("inputs", {}).get("last")
            if last is None:
                last = q.get("price")
            entry = plan.get("entry")
            entry_dist = None
            entry_dist_abs = None
            if last is not None and entry is not None and float(entry) != 0:
                entry_dist = round((float(last) - float(entry)) / float(entry) * 100.0, 3)
                entry_dist_abs = round(abs(entry_dist), 3)

            nv = nv_map.get(sym) or {}
            buy_vol = nv.get("buy_vol")
            sell_vol = nv.get("sell_vol")
            net_vol = nv.get("net_vol")
            if buy_vol is None and isinstance(fp, dict):
                buy_vol = fp.get("buy_vol") if fp.get("buy_vol") is not None else fp.get("buy_volume_total")
                sell_vol = fp.get("sell_vol") if fp.get("sell_vol") is not None else fp.get("sell_volume_total")
                net_vol = fp.get("net_vol") if fp.get("net_vol") is not None else fp.get("net_volume_total")
                if net_vol is None and buy_vol is not None and sell_vol is not None:
                    try:
                        net_vol = int(buy_vol) - int(sell_vol)
                    except (TypeError, ValueError):
                        net_vol = None

            inputs = plan.get("inputs") or {}
            rationale = plan.get("rationale") or []
            note = ""
            if rationale:
                note = str(rationale[0])[:120]
            elif direction == "WAIT":
                note = "Bekle / yapı yok"

            pers = inputs.get("persistence_score")
            try:
                pers_f = float(pers) if pers is not None else None
            except (TypeError, ValueError):
                pers_f = None

            dir_rank = 2 if direction == "LONG" else 1 if direction == "SHORT" else 0
            long_sc = inputs.get("long_score") or 0
            short_sc = inputs.get("short_score") or 0
            try:
                plan_score = float(max(long_sc, short_sc))
            except (TypeError, ValueError):
                plan_score = 0.0

            chg = q.get("change_pct")
            if chg is None:
                chg = inputs.get("change_pct")

            return {
                "symbol": sym,
                "name": plan.get("name") or q.get("name"),
                "price": last if last is not None else q.get("price"),
                "last": last if last is not None else q.get("price"),
                "change_pct": chg,
                "volume": q.get("volume"),
                "rvol": q.get("rvol") if q.get("rvol") is not None else inputs.get("rvol"),
                "rvol10": q.get("rvol10") if q.get("rvol10") is not None else inputs.get("rvol10"),
                "buy_vol": buy_vol,
                "sell_vol": sell_vol,
                "net_vol": net_vol,
                "direction": direction,
                "direction_rank": dir_rank,
                "entry": entry,
                "stop": plan.get("stop"),
                "tp1": plan.get("tp1"),
                "tp2": plan.get("tp2"),
                "rr": plan.get("rr_tp1"),
                "rr_tp1": plan.get("rr_tp1"),
                "rr_tp2": plan.get("rr_tp2"),
                "risk_pct": plan.get("risk_pct"),
                "entry_distance_pct": entry_dist,
                "entry_distance_abs": entry_dist_abs,
                "persistence_score": pers_f,
                "plan_score": plan_score,
                "actionable": direction in ("LONG", "SHORT") and entry is not None,
                "note": note,
            }

        rows: list[dict[str, Any]] = []
        workers = min(8, max(2, len(universe)))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(_one, q): q.get("symbol") for q in universe}
            for fut in as_completed(futs):
                try:
                    row = fut.result()
                except Exception as e:
                    logger.debug("tradeplans fut %s: %s", futs[fut], e)
                    continue
                if row:
                    rows.append(row)

        # Default: actionable nearest entry, then |change|
        def _sort_key(x: dict) -> tuple:
            actionable = 0 if x.get("actionable") else 1
            dist = x.get("entry_distance_abs")
            dist_key = float(dist) if dist is not None else 9999.0
            chg = x.get("change_pct")
            chg_abs = -abs(float(chg)) if chg is not None else 0.0
            return (actionable, dist_key, chg_abs)

        rows.sort(key=_sort_key)
        total_found = len(rows)
        rows = rows[:limit]

        n_long = sum(1 for r in rows if r.get("direction") == "LONG")
        n_short = sum(1 for r in rows if r.get("direction") == "SHORT")
        n_wait = sum(1 for r in rows if r.get("direction") == "WAIT")

        out = {
            "kind": "trade_plans",
            "limit": limit,
            "actionable_only": actionable_only,
            "count": len(rows),
            "stocks": rows,
            "method": TRADE_PLAN_METHOD,
            "coverage": {
                "universe": len(universe),
                "scanned": total_found,
                "long": n_long,
                "short": n_short,
                "wait": n_wait,
                "note": (
                    f"Likit evren (~{uni_lim} hacimli); işlem planı (LONG/SHORT/WAIT). "
                    f"Varsayılan sıra: aksiyonel + girişe en yakın. "
                    f"LONG {n_long} · SHORT {n_short} · WAIT {n_wait}."
                ),
            },
            "market_state": "OPEN" if quote_service.is_market_open() else "CLOSED",
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "cache_ttl_sec": TRADE_PLANS_CACHE_TTL,
            "subtitle": "İşlem planları · giriş/stop/TP · R:R",
            "formula": (
                "Yön = sinyal + footprint + VWAP + RVOL; giriş≈destek/VWAP; "
                "stop=invalidation; TP1/TP2=direnç/uzatma. entry_distance_pct = "
                "(last−entry)/entry×100."
            ),
        }
        self._store(cache_key, out)
        return out



scanner_service = ScannerService()
