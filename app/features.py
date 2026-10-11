"""Extra analysis features: S/R, POC/VA migration, parabolic score."""
from __future__ import annotations

import logging
import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from zoneinfo import ZoneInfo

from app.analysis import (
    VP_METHOD,
    _bar_session_date,
    _idx_from_price,
    _parse_session_date,
    _price_from_idx,
    _tick_decimals,
    _tick_size,
    compute_volume_profile,
)
from app.history_cache import TF_INTERVALS, fetch_bars, rvol_from_bars
from app.quotes import IST, quote_service

logger = logging.getLogger(__name__)

SR_METHOD = (
    "Destek/direnç (yalnızca seans içi): bugünkü 1m (yoksa 5m) barlarda swing high/low "
    "(lookback N) + hacim küme seviyeleri. Swing high = high[i] ≥ high[i±k] tüm k∈1..N; "
    "swing low benzer. Yakın seviyeler (%tol) kümelenir → medyan. "
    "En yakın destek (last altı) / direnç (last üstü) işaretlenir. Multi-gün pivot yok."
)

PERSISTENCE_METHOD = (
    "Israrcılar: seans 1m/5m barlarda dip→agresif geri alma. "
    "Yerel yüksekten ≥%dip_pct geri çekilme; 3–15 dk içinde hacimli + alış-yanlı barlarla "
    "reclaim. Liste israr kalitesi ile (reclaim sayısı, güç, alış baskısı, ana seviye hacmi); "
    "gün % yumuşak skor boost. TAVAN rozeti ≥+%8 — filtre değil. "
    "Gürültü yumuşak taban ~+%2 veya yüksek skor/reclaim. "
    "Ana alım seviyesi = reclaim diplerinin hacim-ağırlıklı kümesi."
)

POC_SHIFT_METHOD = (
    "POC kayması: seans günü 1m (yoksa 5m) barlar saatlik (veya rolling) pencerelere bölünür; "
    "her pencerede volume-at-price POC. Mevcut POC − önceki pencere POC = kayma (TL ve %). "
    "İlk pencere = seans açılışı referansı."
)

VA_MIG_METHOD = (
    "Value area göçü: aynı pencerelerde VAH/VAL (%70 VA). "
    "ΔVAH / ΔVAL ve ok yönü (↑↓→). VA genişliği = VAH−VAL."
)

PARABOLIC_METHOD = (
    "Parabolik yükseliş skoru (0–100): "
    "hızlanma (son yarı getiri − önceki yarı getiri), yeşil mum oranı, "
    "higher-high oranı, RVOL/RVOL10. Ağırlıklar: accel 30%, green 25%, HH 20%, RVOL 25%."
)

SWING_LOOKBACK_DEFAULT = 3
SR_CLUSTER_TOL_PCT = 0.35  # cluster within 0.35% of price
SR_MAX_LEVELS = 12


def _session_day_bars(yahoo: str, force: bool = False) -> tuple[list[dict], str, date | None, str | None]:
    """Return (day_bars, source_tf, session_date, fallback_note)."""
    target = _parse_session_date("today")
    fallback_note = None
    bars_1m = fetch_bars(yahoo, "1m", force=force) or []
    day_bars = [b for b in bars_1m if _bar_session_date(b) == target]
    src_tf = "1m"
    if len(day_bars) < 3:
        bars_5m = fetch_bars(yahoo, "5m", force=force) or []
        day_5 = [b for b in bars_5m if _bar_session_date(b) == target]
        if len(day_5) > len(day_bars):
            day_bars, src_tf = day_5, "5m"
            fallback_note = "1m yetersiz — 5m kullanıldı."
    if not day_bars:
        b1 = bars_1m or []
        b5 = fetch_bars(yahoo, "5m", force=False) or []
        dates = sorted(
            {d for d in (_bar_session_date(b) for b in (b1 + b5)) if d},
            reverse=True,
        )
        if dates:
            target = dates[0]
            d1 = [b for b in b1 if _bar_session_date(b) == target]
            d5 = [b for b in b5 if _bar_session_date(b) == target]
            if len(d1) >= 3:
                day_bars, src_tf = d1, "1m"
            elif d5:
                day_bars, src_tf = d5, "5m"
                fallback_note = "1m yetersiz — 5m kullanıldı."
            elif d1:
                day_bars, src_tf = d1, "1m"

    # İş Yatırım fallback when Yahoo empty / thin (v1.13.2)
    if len(day_bars) < 8:
        try:
            from app.chart_provider import fetch_chart_history
            from app.history_cache import history_cache

            def _spread(bars_in: list[dict], day_vol) -> list[dict]:
                if not bars_in:
                    return bars_in
                try:
                    dv = float(day_vol or 0)
                except (TypeError, ValueError):
                    dv = 0.0
                weights = []
                for b in bars_in:
                    try:
                        o, h, l, c = b.get("open"), b.get("high"), b.get("low"), b.get("close")
                        rng = abs(float(h) - float(l)) if h is not None and l is not None else 0.0
                        body = abs(float(c) - float(o)) if c is not None and o is not None else 0.0
                        weights.append(max(rng, body, 1e-9))
                    except Exception:
                        weights.append(1.0)
                tw = sum(weights) or float(len(weights)) or 1.0
                out = []
                for b, w in zip(bars_in, weights):
                    nb = dict(b)
                    nb["volume"] = int(round(dv * (w / tw))) if dv > 0 else (nb.get("volume") or 0)
                    out.append(nb)
                return out

            sym = (yahoo or "").replace(".IS", "")
            for tf_try in ("1m", "5m"):
                bars_isy, _meta = fetch_chart_history(sym, tf_try, force=False)
                if not bars_isy:
                    continue
                day_isy = [b for b in bars_isy if _bar_session_date(b) == target]
                if not day_isy:
                    dates_isy = sorted(
                        {d for d in (_bar_session_date(b) for b in bars_isy) if d},
                        reverse=True,
                    )
                    if dates_isy:
                        target = dates_isy[0]
                        day_isy = [b for b in bars_isy if _bar_session_date(b) == dates_isy[0]]
                if len(day_isy) <= len(day_bars):
                    continue
                vol = None
                try:
                    cached = quote_service._cache or []
                    q = next((x for x in cached if x.get("symbol") == sym), None)
                    vol = (q or {}).get("volume")
                except Exception:
                    vol = None
                day_isy = _spread(day_isy, vol)
                history_cache.put(yahoo, tf_try, day_isy)
                day_bars, src_tf = day_isy, tf_try
                fallback_note = (fallback_note or "") + f" Yahoo yetersiz — İş Yatırım {tf_try}."
                break
        except Exception as e:
            logger.debug("session_day_bars isyatirim %s: %s", yahoo, e)

    return day_bars, src_tf, target, fallback_note


def _vp_from_bars(bars: list[dict]) -> dict[str, Any] | None:
    """Lightweight volume profile POC/VAH/VAL from a bar window (same method as full VP)."""
    if not bars or len(bars) < 2:
        return None
    highs = [float(b["high"]) for b in bars if b.get("high") is not None]
    lows = [float(b["low"]) for b in bars if b.get("low") is not None]
    if not highs or not lows:
        return None
    raw_high, raw_low = max(highs), min(lows)
    mid = (raw_high + raw_low) / 2.0
    tick = _tick_size(mid)
    lo_idx = _idx_from_price(raw_low, tick)
    hi_idx = _idx_from_price(raw_high, tick)
    if hi_idx < lo_idx:
        lo_idx, hi_idx = hi_idx, lo_idx
    n_est = hi_idx - lo_idx + 1
    if n_est > 3000:
        span = max(raw_high - raw_low, tick)
        tick = max(_tick_size(mid), round(span / 2500.0, 4) or 0.01)
        tick = max(0.01, round(tick / 0.01) * 0.01)
        lo_idx = _idx_from_price(raw_low, tick)
        hi_idx = _idx_from_price(raw_high, tick)
        if hi_idx < lo_idx:
            lo_idx, hi_idx = hi_idx, lo_idx
    dec = _tick_decimals(tick)
    vol_map: dict[int, float] = {i: 0.0 for i in range(lo_idx, hi_idx + 1)}
    for bar in bars:
        h, l, c = bar.get("high"), bar.get("low"), bar.get("close")
        v = float(bar.get("volume") or 0)
        if h is None or l is None or c is None or v <= 0:
            continue
        h, l = float(h), float(l)
        if h < l:
            h, l = l, h
        i0, i1 = _idx_from_price(l, tick), _idx_from_price(h, tick)
        if i1 < i0:
            i0, i1 = i1, i0
        touched = list(range(i0, i1 + 1)) or [_idx_from_price(float(c), tick)]
        share = v / len(touched)
        for idx in touched:
            if idx not in vol_map:
                vol_map[idx] = 0.0
            vol_map[idx] += share
    if not vol_map or sum(vol_map.values()) <= 0:
        return None
    poc_idx = max(vol_map.keys(), key=lambda i: vol_map[i])
    poc = _price_from_idx(poc_idx, tick)
    total = sum(vol_map.values()) or 1.0
    target = total * 0.70
    asc = sorted(vol_map.keys())
    pos = asc.index(poc_idx)
    lo_i = hi_i = pos
    acc = vol_map[poc_idx]
    while acc < target and (lo_i > 0 or hi_i < len(asc) - 1):
        left = vol_map[asc[lo_i - 1]] if lo_i > 0 else -1
        right = vol_map[asc[hi_i + 1]] if hi_i < len(asc) - 1 else -1
        if right >= left:
            hi_i += 1
            acc += vol_map[asc[hi_i]]
        else:
            lo_i -= 1
            acc += vol_map[asc[lo_i]]
    val = _price_from_idx(asc[lo_i], tick)
    vah = _price_from_idx(asc[hi_i], tick)
    return {
        "poc": poc,
        "poc_str": f"{poc:.{dec}f}",
        "vah": vah,
        "vah_str": f"{vah:.{dec}f}",
        "val": val,
        "val_str": f"{val:.{dec}f}",
        "tick": tick,
        "tick_decimals": dec,
        "bar_count": len(bars),
        "total_volume": int(round(total)),
    }


def _bar_hour_key(bar: dict) -> str | None:
    d = bar.get("date") or ""
    if len(d) >= 13:
        return d[:13]  # YYYY-MM-DD HH
    t = bar.get("time")
    if isinstance(t, (int, float)):
        dt = datetime.fromtimestamp(t, tz=IST)
        return dt.strftime("%Y-%m-%d %H")
    return None


def compute_poc_migration(
    symbol: str,
    mode: str = "hourly",
    force: bool = False,
) -> dict[str, Any]:
    """Track session POC over hourly (or rolling) windows."""
    sym = symbol.upper().replace(".IS", "")
    yahoo = f"{sym}.IS"
    mode = (mode or "hourly").lower()
    if mode not in ("hourly", "rolling"):
        mode = "hourly"

    day_bars, src_tf, target, fallback = _session_day_bars(yahoo, force=force)
    empty = {
        "symbol": sym,
        "date": target.isoformat() if target else None,
        "mode": mode,
        "source_tf": src_tf,
        "windows": [],
        "current_poc": None,
        "earlier_poc": None,
        "session_open_poc": None,
        "poc_shift": None,
        "poc_shift_pct": None,
        "poc_shift_vs_open": None,
        "poc_shift_vs_open_pct": None,
        "direction": None,
        "method": POC_SHIFT_METHOD,
        "fallback_note": fallback,
        "bar_count": len(day_bars),
    }
    if len(day_bars) < 5:
        empty["error"] = "no_intraday_bars"
        return empty

    windows: list[dict[str, Any]] = []
    if mode == "hourly":
        groups: dict[str, list[dict]] = defaultdict(list)
        for b in day_bars:
            k = _bar_hour_key(b)
            if k:
                groups[k].append(b)
        for key in sorted(groups.keys()):
            vp = _vp_from_bars(groups[key])
            if not vp:
                continue
            windows.append({
                "label": key + ":00",
                "hour": key,
                "bar_count": vp["bar_count"],
                "poc": vp["poc"],
                "poc_str": vp["poc_str"],
                "vah": vp["vah"],
                "vah_str": vp["vah_str"],
                "val": vp["val"],
                "val_str": vp["val_str"],
                "total_volume": vp["total_volume"],
            })
    else:
        # Rolling: cumulative from open in ~6 chunks
        n = len(day_bars)
        chunks = max(4, min(8, n // 15))
        step = max(1, n // chunks)
        for i in range(step, n + 1, step):
            window = day_bars[:i]
            vp = _vp_from_bars(window)
            if not vp:
                continue
            last = window[-1]
            windows.append({
                "label": (last.get("date") or "")[:16] or f"bar@{i}",
                "bar_count": vp["bar_count"],
                "poc": vp["poc"],
                "poc_str": vp["poc_str"],
                "vah": vp["vah"],
                "vah_str": vp["vah_str"],
                "val": vp["val"],
                "val_str": vp["val_str"],
                "total_volume": vp["total_volume"],
            })
        # ensure last full
        if windows and windows[-1]["bar_count"] < n:
            vp = _vp_from_bars(day_bars)
            if vp:
                windows.append({
                    "label": "seans",
                    "bar_count": vp["bar_count"],
                    "poc": vp["poc"],
                    "poc_str": vp["poc_str"],
                    "vah": vp["vah"],
                    "vah_str": vp["vah_str"],
                    "val": vp["val"],
                    "val_str": vp["val_str"],
                    "total_volume": vp["total_volume"],
                })

    # Also attach full-session POC as current if needed
    full = _vp_from_bars(day_bars)
    if not windows and full:
        windows.append({
            "label": "seans",
            "bar_count": full["bar_count"],
            "poc": full["poc"],
            "poc_str": full["poc_str"],
            "vah": full["vah"],
            "vah_str": full["vah_str"],
            "val": full["val"],
            "val_str": full["val_str"],
            "total_volume": full["total_volume"],
        })

    current = windows[-1] if windows else None
    earlier = windows[-2] if len(windows) >= 2 else None
    open_w = windows[0] if windows else None

    def _shift(a, b):
        if a is None or b is None:
            return None, None
        d = a - b
        pct = (d / b * 100.0) if b else None
        return round(d, 4), round(pct, 3) if pct is not None else None

    cur_poc = (full or {}).get("poc") if full else (current or {}).get("poc")
    earlier_poc = (earlier or {}).get("poc")
    open_poc = (open_w or {}).get("poc")
    shift, shift_pct = _shift(cur_poc, earlier_poc)
    vs_open, vs_open_pct = _shift(cur_poc, open_poc)

    direction = None
    if shift is not None:
        if shift > 0:
            direction = "up"
        elif shift < 0:
            direction = "down"
        else:
            direction = "flat"

    # annotate window-to-window deltas
    for i, w in enumerate(windows):
        if i == 0:
            w["poc_delta"] = None
            w["poc_delta_pct"] = None
            continue
        d, p = _shift(w.get("poc"), windows[i - 1].get("poc"))
        w["poc_delta"] = d
        w["poc_delta_pct"] = p

    return {
        "symbol": sym,
        "date": target.isoformat() if target else None,
        "mode": mode,
        "source_tf": src_tf,
        "windows": windows,
        "window_count": len(windows),
        "current_poc": cur_poc,
        "current_poc_str": (full or current or {}).get("poc_str"),
        "earlier_poc": earlier_poc,
        "earlier_poc_str": (earlier or {}).get("poc_str"),
        "session_open_poc": open_poc,
        "session_open_poc_str": (open_w or {}).get("poc_str"),
        "poc_shift": shift,
        "poc_shift_pct": shift_pct,
        "poc_shift_vs_open": vs_open,
        "poc_shift_vs_open_pct": vs_open_pct,
        "direction": direction,
        "vah": (full or current or {}).get("vah"),
        "val": (full or current or {}).get("val"),
        "method": POC_SHIFT_METHOD,
        "fallback_note": fallback,
        "bar_count": len(day_bars),
    }


def compute_va_migration(
    symbol: str,
    mode: str = "hourly",
    force: bool = False,
) -> dict[str, Any]:
    """VAH/VAL movement during session — reuses POC migration windows."""
    base = compute_poc_migration(symbol, mode=mode, force=force)
    windows = base.get("windows") or []
    for i, w in enumerate(windows):
        if i == 0:
            w["vah_delta"] = None
            w["val_delta"] = None
            w["vah_arrow"] = "→"
            w["val_arrow"] = "→"
            continue
        prev = windows[i - 1]
        vd = None if w.get("vah") is None or prev.get("vah") is None else round(w["vah"] - prev["vah"], 4)
        ld = None if w.get("val") is None or prev.get("val") is None else round(w["val"] - prev["val"], 4)
        w["vah_delta"] = vd
        w["val_delta"] = ld
        w["vah_arrow"] = "↑" if vd and vd > 0 else ("↓" if vd and vd < 0 else "→")
        w["val_arrow"] = "↑" if ld and ld > 0 else ("↓" if ld and ld < 0 else "→")
        if w.get("vah") is not None and w.get("val") is not None:
            w["va_width"] = round(w["vah"] - w["val"], 4)

    cur = windows[-1] if windows else {}
    earlier = windows[-2] if len(windows) >= 2 else {}
    open_w = windows[0] if windows else {}

    def _d(a, b):
        if a is None or b is None:
            return None
        return round(a - b, 4)

    vah_shift = _d(cur.get("vah"), earlier.get("vah"))
    val_shift = _d(cur.get("val"), earlier.get("val"))
    vah_vs_open = _d(cur.get("vah"), open_w.get("vah"))
    val_vs_open = _d(cur.get("val"), open_w.get("val"))

    def _arrow(d):
        if d is None:
            return "→"
        if d > 0:
            return "↑"
        if d < 0:
            return "↓"
        return "→"

    return {
        "symbol": base.get("symbol"),
        "date": base.get("date"),
        "mode": base.get("mode"),
        "source_tf": base.get("source_tf"),
        "windows": windows,
        "window_count": len(windows),
        "current_vah": cur.get("vah"),
        "current_vah_str": cur.get("vah_str"),
        "current_val": cur.get("val"),
        "current_val_str": cur.get("val_str"),
        "earlier_vah": earlier.get("vah"),
        "earlier_val": earlier.get("val"),
        "vah_shift": vah_shift,
        "val_shift": val_shift,
        "vah_arrow": _arrow(vah_shift),
        "val_arrow": _arrow(val_shift),
        "vah_vs_open": vah_vs_open,
        "val_vs_open": val_vs_open,
        "vah_vs_open_arrow": _arrow(vah_vs_open),
        "val_vs_open_arrow": _arrow(val_vs_open),
        "va_width": round(cur["vah"] - cur["val"], 4) if cur.get("vah") is not None and cur.get("val") is not None else None,
        "method": VA_MIG_METHOD,
        "fallback_note": base.get("fallback_note"),
        "bar_count": base.get("bar_count"),
        "error": base.get("error"),
    }


def detect_support_resistance(
    symbol: str,
    interval: str = "session",
    lookback: int = SWING_LOOKBACK_DEFAULT,
    max_levels: int = SR_MAX_LEVELS,
    force: bool = False,
) -> dict[str, Any]:
    """Intraday-only S/R from current session 1m (fallback 5m) bars.

    ``interval`` is accepted for API compatibility but ignored for data source —
    levels always come from the latest BIST session day (same as VWAP/footprint).
    """
    sym = symbol.upper().replace(".IS", "")
    yahoo = f"{sym}.IS"
    lookback = max(2, min(int(lookback or SWING_LOOKBACK_DEFAULT), 8))
    max_levels = max(2, min(int(max_levels or SR_MAX_LEVELS), 20))

    day_bars, src_tf, target, fallback = _session_day_bars(yahoo, force=force)
    bars = sorted(
        day_bars,
        key=lambda b: (b.get("time") is None, b.get("time") or 0, b.get("date") or ""),
    )

    last_price = None
    if bars:
        for b in reversed(bars):
            if b.get("close") is not None:
                last_price = float(b["close"])
                break
    quote = quote_service.fetch_one(sym)
    if quote and quote.get("price") is not None:
        last_price = float(quote["price"])

    empty = {
        "symbol": sym,
        "interval": "session",
        "source_tf": src_tf,
        "date": target.isoformat() if target else None,
        "lookback": lookback,
        "last_price": last_price,
        "levels": [],
        "level_count": 0,
        "nearest_support": None,
        "nearest_resistance": None,
        "swing_highs": 0,
        "swing_lows": 0,
        "bar_count": len(bars),
        "method": SR_METHOD,
        "cluster_tol_pct": SR_CLUSTER_TOL_PCT,
        "fallback_note": fallback,
        "scope": "intraday_session_only",
    }
    if len(bars) < lookback * 2 + 3:
        empty["error"] = "no_intraday_bars" if not bars else "insufficient_session_bars"
        return empty

    # Adaptive lookback for short sessions (e.g. early open)
    lb = lookback
    if len(bars) < 40:
        lb = max(2, min(lb, 2))
    elif len(bars) < 90:
        lb = max(2, min(lb, 3))

    swings_h: list[dict] = []
    swings_l: list[dict] = []
    n = len(bars)
    for i in range(lb, n - lb):
        h = bars[i].get("high")
        l = bars[i].get("low")
        if h is None or l is None:
            continue
        h, l = float(h), float(l)
        is_sh = all(
            bars[i + k].get("high") is not None and h >= float(bars[i + k]["high"])
            for k in range(-lb, lb + 1)
            if k != 0
        )
        is_sl = all(
            bars[i + k].get("low") is not None and l <= float(bars[i + k]["low"])
            for k in range(-lb, lb + 1)
            if k != 0
        )
        t = bars[i].get("time") or bars[i].get("date")
        v = float(bars[i].get("volume") or 0)
        if is_sh:
            swings_h.append({"price": h, "time": t, "kind": "resistance", "index": i, "volume": v})
        if is_sl:
            swings_l.append({"price": l, "time": t, "kind": "support", "index": i, "volume": v})

    # Volume-cluster levels: tick-bucket total volume peaks within session range
    vol_peaks: list[dict] = []
    if last_price is not None and n >= 10:
        try:
            highs = [float(b["high"]) for b in bars if b.get("high") is not None]
            lows = [float(b["low"]) for b in bars if b.get("low") is not None]
            if highs and lows:
                tick = _tick_size((max(highs) + min(lows)) / 2.0)
                buckets: dict[int, float] = defaultdict(float)
                for b in bars:
                    h, l, c = b.get("high"), b.get("low"), b.get("close")
                    v = float(b.get("volume") or 0)
                    if h is None or l is None or c is None or v <= 0:
                        continue
                    mid = (float(h) + float(l) + float(c)) / 3.0
                    buckets[_idx_from_price(mid, tick)] += v
                if buckets:
                    vals = sorted(buckets.values(), reverse=True)
                    thr = vals[min(8, len(vals) - 1)] * 0.55 if vals else 0
                    for idx, vol in buckets.items():
                        if vol >= thr and vol > 0:
                            px = _price_from_idx(idx, tick)
                            kind = "resistance" if px >= last_price else "support"
                            vol_peaks.append({
                                "price": px, "time": None, "kind": kind,
                                "index": -1, "volume": vol, "source": "volume",
                            })
        except Exception as e:
            logger.debug("SR vol cluster %s: %s", sym, e)

    def _cluster(points: list[dict], kind: str) -> list[dict]:
        if not points or last_price is None:
            return []
        pts = sorted(points, key=lambda x: x["price"])
        clusters: list[list[dict]] = []
        cur: list[dict] = [pts[0]]
        for p in pts[1:]:
            ref = sum(x["price"] for x in cur) / len(cur)
            if abs(p["price"] - ref) / max(ref, 1e-9) * 100.0 <= SR_CLUSTER_TOL_PCT * 2.5:
                cur.append(p)
            else:
                clusters.append(cur)
                cur = [p]
        clusters.append(cur)
        out = []
        for cl in clusters:
            prices = [x["price"] for x in cl]
            med = sorted(prices)[len(prices) // 2]
            dist_pct = (med - last_price) / last_price * 100.0 if last_price else None
            vol_sum = sum(float(x.get("volume") or 0) for x in cl)
            sources = {x.get("source") or "swing" for x in cl}
            out.append({
                "price": round(med, 4),
                "kind": kind,
                "touches": len(cl),
                "distance_pct": round(dist_pct, 3) if dist_pct is not None else None,
                "distance_abs": round(med - last_price, 4) if last_price is not None else None,
                "volume": int(round(vol_sum)) if vol_sum else None,
                "sources": sorted(sources),
            })
        return out

    sess_high = None
    sess_low = None
    try:
        _hs = [float(b["high"]) for b in bars if b.get("high") is not None]
        _ls = [float(b["low"]) for b in bars if b.get("low") is not None]
        if _hs:
            sess_high = max(_hs)
        if _ls:
            sess_low = min(_ls)
    except Exception:
        pass

    resists = _cluster(
        swings_h + [x for x in vol_peaks if x["kind"] == "resistance"],
        "resistance",
    )
    supports = _cluster(
        swings_l + [x for x in vol_peaks if x["kind"] == "support"],
        "support",
    )

    # Pin session high/low as hard levels (not merged into swing clusters)
    def _has_near(levels, px, tol_pct=0.15):
        for lv in levels:
            if abs(lv["price"] - px) / max(px, 1e-9) * 100.0 <= tol_pct:
                return True
        return False

    if sess_low is not None and last_price is not None and not _has_near(supports, sess_low):
        dist = (sess_low - last_price) / last_price * 100.0
        supports.append({
            "price": round(sess_low, 4),
            "kind": "support",
            "touches": 1,
            "distance_pct": round(dist, 3),
            "distance_abs": round(sess_low - last_price, 4),
            "volume": None,
            "sources": ["session_low"],
        })
    if sess_high is not None and last_price is not None and not _has_near(resists, sess_high):
        dist = (sess_high - last_price) / last_price * 100.0
        resists.append({
            "price": round(sess_high, 4),
            "kind": "resistance",
            "touches": 1,
            "distance_pct": round(dist, 3),
            "distance_abs": round(sess_high - last_price, 4),
            "volume": None,
            "sources": ["session_high"],
        })

    # Session range is tight — keep levels within ~15% of last (intraday)
    def _near(lv, lim=15.0):
        d = lv.get("distance_pct")
        return d is not None and abs(d) <= lim

    # Re-label by position vs last (volume clusters can sit on either side)
    all_lv = supports + resists
    supports = []
    resists = []
    for lv in all_lv:
        d = lv.get("distance_pct")
        if d is None:
            continue
        if d <= 0.05:
            lv = {**lv, "kind": "support"}
            supports.append(lv)
        if d >= -0.05:
            # allow dual near-touch zone; prefer resistance if clearly above
            if d >= 0:
                lv = {**lv, "kind": "resistance"}
                resists.append(lv)
            elif lv not in supports:
                supports.append({**lv, "kind": "support"})
    supports = [s for s in supports if _near(s, 18.0)] or supports
    resists = [r for r in resists if _near(r, 18.0)] or resists
    # de-dupe by price+kind
    def _dedupe(xs):
        seen = set()
        out = []
        for x in xs:
            k = (round(x["price"], 4), x["kind"])
            if k in seen:
                continue
            seen.add(k)
            out.append(x)
        return out
    supports = _dedupe(supports)
    resists = _dedupe(resists)
    supports.sort(key=lambda x: abs(x.get("distance_pct") or 999))
    resists.sort(key=lambda x: abs(x.get("distance_pct") or 999))
    half = max(1, max_levels // 2)
    supports_below = [s for s in supports if (s.get("distance_pct") or 0) <= 0.05]
    resists_above = [r for r in resists if (r.get("distance_pct") or 0) >= -0.05]
    levels = supports_below[:half] + resists_above[:half]
    if len(levels) < max_levels:
        rest = [x for x in (supports + resists) if x not in levels]
        rest.sort(key=lambda x: abs(x.get("distance_pct") or 999))
        for x in rest:
            if len(levels) >= max_levels:
                break
            if _near(x, 20.0) or len(levels) < 4:
                levels.append(x)
    levels.sort(key=lambda x: x["price"], reverse=True)

    nearest_support = next(
        (s for s in sorted(supports, key=lambda x: abs(x.get("distance_pct") or 999))
         if (s.get("distance_pct") or 0) <= 0.05),
        None,
    )
    nearest_resistance = next(
        (r for r in sorted(resists, key=lambda x: abs(x.get("distance_pct") or 999))
         if (r.get("distance_pct") or 0) >= -0.05),
        None,
    )
    for lv in levels:
        if nearest_support and lv["price"] == nearest_support["price"] and lv["kind"] == "support":
            lv["nearest"] = True
        if nearest_resistance and lv["price"] == nearest_resistance["price"] and lv["kind"] == "resistance":
            lv["nearest"] = True

    return {
        "symbol": sym,
        "interval": "session",
        "requested_interval": (interval or "session"),
        "source_tf": src_tf,
        "date": target.isoformat() if target else None,
        "lookback": lb,
        "last_price": last_price,
        "levels": levels,
        "level_count": len(levels),
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "swing_highs": len(swings_h),
        "swing_lows": len(swings_l),
        "volume_peaks": len(vol_peaks),
        "bar_count": n,
        "method": SR_METHOD,
        "cluster_tol_pct": SR_CLUSTER_TOL_PCT,
        "fallback_note": fallback,
        "scope": "intraday_session_only",
    }


def compute_parabolic_score(
    symbol: str,
    interval: str = "15m",
    force: bool = False,
) -> dict[str, Any]:
    """Parabolic rise score combining accel, green ratio, HH, RVOL."""
    sym = symbol.upper().replace(".IS", "")
    yahoo = f"{sym}.IS"
    interval = (interval or "15m").lower()
    if interval not in TF_INTERVALS:
        interval = "15m"

    bars = fetch_bars(yahoo, interval, force=force) or []
    # Use last session for intraday
    if interval not in ("1d", "1w") and bars:
        last_d = None
        for b in reversed(bars):
            d = (b.get("date") or "")[:10]
            if d:
                last_d = d
                break
        if last_d:
            sess = [b for b in bars if (b.get("date") or "").startswith(last_d)]
            if len(sess) >= 6:
                bars = sess

    quote = None
    cached = quote_service._cache or []
    quote = next((q for q in cached if q["symbol"] == sym), None)
    if not quote:
        quote = quote_service.fetch_one(sym)

    empty = {
        "symbol": sym,
        "interval": interval,
        "score": None,
        "components": {},
        "method": PARABOLIC_METHOD,
        "bar_count": len(bars),
    }
    if len(bars) < 8:
        empty["error"] = "insufficient_bars"
        if quote:
            empty["price"] = quote.get("price")
            empty["change_pct"] = quote.get("change_pct")
            empty["rvol"] = quote.get("rvol")
            empty["rvol10"] = quote.get("rvol10")
        return empty

    closes = [float(b["close"]) for b in bars if b.get("close") is not None]
    highs = [float(b["high"]) for b in bars if b.get("high") is not None]
    opens = []
    for b in bars:
        if b.get("close") is None:
            continue
        o = b.get("open")
        opens.append(float(o) if o is not None else float(b["close"]))

    n = len(closes)
    half = max(3, n // 2)
    first = closes[:half]
    second = closes[half:]
    ret1 = (first[-1] - first[0]) / first[0] * 100.0 if first[0] else 0.0
    ret2 = (second[-1] - second[0]) / second[0] * 100.0 if second and second[0] else 0.0
    accel = ret2 - ret1  # positive = accelerating

    # green ratio on recent window
    win = bars[-min(20, len(bars)):]
    green = 0
    for b in win:
        o = b.get("open")
        c = b.get("close")
        if c is None:
            continue
        o = float(o) if o is not None else float(c)
        if float(c) >= o:
            green += 1
    green_ratio = green / max(1, len(win))

    # higher highs
    hh = 0
    hh_n = 0
    hs = [float(b["high"]) for b in win if b.get("high") is not None]
    for i in range(1, len(hs)):
        hh_n += 1
        if hs[i] > hs[i - 1]:
            hh += 1
    hh_ratio = hh / hh_n if hh_n else 0.0

    rvol = (quote or {}).get("rvol")
    rvol10 = (quote or {}).get("rvol10")
    # TF rvol as fallback boost
    tf_info = rvol_from_bars(bars)
    rvol_tf = tf_info.get("rvol")

    # Normalize components to 0–100-ish then weight
    # accel: map -5..+10 → 0..100
    accel_s = max(0.0, min(100.0, (accel + 5.0) / 15.0 * 100.0))
    green_s = green_ratio * 100.0
    hh_s = hh_ratio * 100.0
    rvol_ref = rvol if rvol is not None else (rvol10 if rvol10 is not None else rvol_tf)
    if rvol_ref is None:
        rvol_s = 40.0  # neutral
    else:
        # 0.5→20, 1→40, 2→70, 3+→100
        rvol_s = max(0.0, min(100.0, (float(rvol_ref) - 0.3) / 2.7 * 100.0))

    score = (
        0.30 * accel_s
        + 0.25 * green_s
        + 0.20 * hh_s
        + 0.25 * rvol_s
    )
    # Penalize if overall return negative
    net_ret = (closes[-1] - closes[0]) / closes[0] * 100.0 if closes[0] else 0.0
    if net_ret < 0:
        score *= 0.55
    score = round(max(0.0, min(100.0, score)), 2)

    return {
        "symbol": sym,
        "name": (quote or {}).get("name"),
        "price": (quote or {}).get("price"),
        "change_pct": (quote or {}).get("change_pct"),
        "volume": (quote or {}).get("volume"),
        "rvol": rvol,
        "rvol10": rvol10,
        "rvol_tf": rvol_tf,
        "interval": interval,
        "score": score,
        "components": {
            "accel_pct": round(accel, 3),
            "accel_score": round(accel_s, 2),
            "green_ratio": round(green_ratio, 3),
            "green_score": round(green_s, 2),
            "hh_ratio": round(hh_ratio, 3),
            "hh_score": round(hh_s, 2),
            "rvol_score": round(rvol_s, 2),
            "net_return_pct": round(net_ret, 3),
            "ret_first_half_pct": round(ret1, 3),
            "ret_second_half_pct": round(ret2, 3),
        },
        "method": PARABOLIC_METHOD,
        "bar_count": len(bars),
    }


# ─── v1.9: profile bias, high breaks, VWAP/AORT ───────────────────────────────

PROFILE_BIAS_METHOD = (
    "Profil bias (0–100): POC kayması (önceki pencere + açılışa), VA göçü (VAH/VAL yönü), "
    "VA genişlik sıkışması (yükseklerde squeeze = bullish), POC konumunun VA içi. "
    "Skor ≥70 yükseliş tetikleyici · 40–69 nötr · <40 zayıf. Türkçe yorum paneli."
)

HIGH_BREAK_METHOD = (
    "Gün içi yüksek kırılımı: seans 1m (yoksa 5m) barlarda running day-high takip edilir. "
    "Bar high > önceki running high → kırılım; fiyat=yeni high, hacim=o bar volume; "
    "open/close mum OHLC. max_vol_break_price = en yüksek hacimli kırılım fiyatı."
)

VOLUME_BREAK_ALARM_RULE = (
    "Hacimli Kırılım alarmı — hisse başına YALNIZCA şu üçü birden doğruysa tetiklenir: "
    "(1) seans içi ≥1 running day-high kırılımı var; "
    "(2) seansın SON kırılımı aynı zamanda o günün max-hacimli kırılımı "
    "(son kırılım = max hacimli kırılım; historical ranking alarm DEĞİL); "
    "(3) fiyat o kırılımla yükselir: kırılım mumu yükseliş (close>open) VE "
    "close > önceki yüksek VE last ≥ kırılan seviye/prev_high (wick/fake değil). "
    "Evren: tüm likit hisseler (top-volume universe)."
)

VWAP_AORT_METHOD = (
    "Seans VWAP = Σ(typical×vol)/Σ(vol), typical=(H+L+C)/3. "
    "AORT ≈ BIST ağırlıklı ortalama = Σ(C×vol)/Σ(vol) (bar yaklaşımı; tick yoksa VWAP-eşdeğeri notu). "
    "last_vs_vwap_pct / last_vs_aort_pct = (last−ref)/ref×100."
)


def compute_profile_bias(
    symbol: str,
    mode: str = "hourly",
    force: bool = False,
) -> dict[str, Any]:
    """Combine POC + VA migration into bullishness score 0–100 + Turkish yorum."""
    poc = compute_poc_migration(symbol, mode=mode, force=force)
    va = compute_va_migration(symbol, mode=mode, force=False)  # reuse cached bars via force=False

    components: dict[str, Any] = {}
    score = 50.0  # neutral base
    bullets: list[str] = []

    # 1) POC shift vs earlier window (±25 pts)
    shift = poc.get("poc_shift")
    shift_pct = poc.get("poc_shift_pct")
    if shift is not None:
        # map roughly -2%..+2% → -25..+25
        pct = float(shift_pct) if shift_pct is not None else 0.0
        poc_pts = max(-25.0, min(25.0, pct / 2.0 * 25.0))
        # absolute TL boost if pct tiny but TL meaningful
        if abs(pct) < 0.05 and abs(shift) > 0:
            poc_pts = 8.0 if shift > 0 else -8.0
        score += poc_pts
        components["poc_shift_pts"] = round(poc_pts, 2)
        components["poc_shift"] = shift
        components["poc_shift_pct"] = shift_pct
        if shift > 0:
            bullets.append(
                f"POC yükseliyor: {poc.get('earlier_poc_str') or poc.get('earlier_poc')} → "
                f"{poc.get('current_poc_str') or poc.get('current_poc')} "
                f"(Δ {shift:+.2f} / %{pct:+.2f})."
            )
        elif shift < 0:
            bullets.append(
                f"POC geriliyor: {poc.get('earlier_poc_str') or poc.get('earlier_poc')} → "
                f"{poc.get('current_poc_str') or poc.get('current_poc')} "
                f"(Δ {shift:+.2f} / %{pct:+.2f})."
            )
        else:
            bullets.append("POC yatay — önceki pencereye göre kayma yok.")
    else:
        components["poc_shift_pts"] = 0.0
        bullets.append("POC kayması hesaplanamadı (yetersiz pencere).")

    # 2) POC vs session open (±15 pts)
    vs_open = poc.get("poc_shift_vs_open")
    vs_open_pct = poc.get("poc_shift_vs_open_pct")
    if vs_open is not None:
        op = float(vs_open_pct) if vs_open_pct is not None else 0.0
        open_pts = max(-15.0, min(15.0, op / 2.5 * 15.0))
        score += open_pts
        components["poc_vs_open_pts"] = round(open_pts, 2)
        if vs_open > 0:
            bullets.append(f"Açılış POC'una göre yukarı göç (%{op:+.2f}).")
        elif vs_open < 0:
            bullets.append(f"Açılış POC'una göre aşağı göç (%{op:+.2f}).")
        else:
            bullets.append("POC açılış seviyesinde.")
    else:
        components["poc_vs_open_pts"] = 0.0

    # 3) VA migration — both VAH & VAL up = strong bullish (±20 pts)
    vah_s = va.get("vah_shift")
    val_s = va.get("val_shift")
    va_pts = 0.0
    if vah_s is not None or val_s is not None:
        up = 0
        down = 0
        if vah_s is not None:
            if vah_s > 0:
                up += 1
            elif vah_s < 0:
                down += 1
        if val_s is not None:
            if val_s > 0:
                up += 1
            elif val_s < 0:
                down += 1
        if up == 2:
            va_pts = 20.0
            bullets.append(
                f"Value Area yukarı göçüyor (VAH {va.get('vah_arrow')} / VAL {va.get('val_arrow')})."
            )
        elif down == 2:
            va_pts = -20.0
            bullets.append(
                f"Value Area aşağı göçüyor (VAH {va.get('vah_arrow')} / VAL {va.get('val_arrow')})."
            )
        elif up == 1 and down == 0:
            va_pts = 10.0
            bullets.append("VA kısmen yukarı (tek kenar yükseliyor).")
        elif down == 1 and up == 0:
            va_pts = -10.0
            bullets.append("VA kısmen aşağı (tek kenar geriliyor).")
        else:
            va_pts = 0.0
            bullets.append("VA genişliyor/daralıyor — yön karışık (expand/contract).")
        # magnitude soft boost
        mag = abs(vah_s or 0) + abs(val_s or 0)
        if mag > 0 and va.get("current_vah"):
            ref = float(va["current_vah"]) or 1.0
            mag_pct = mag / ref * 100.0
            va_pts += max(-5.0, min(5.0, (1 if va_pts >= 0 else -1) * min(5.0, mag_pct * 2)))
    components["va_mig_pts"] = round(va_pts, 2)
    components["vah_shift"] = vah_s
    components["val_shift"] = val_s
    score += va_pts

    # 4) VA width squeeze at highs (±15 pts)
    windows = va.get("windows") or []
    width_now = va.get("va_width")
    width_earlier = None
    if len(windows) >= 2:
        w0 = windows[-2]
        if w0.get("vah") is not None and w0.get("val") is not None:
            width_earlier = round(w0["vah"] - w0["val"], 4)
        elif w0.get("va_width") is not None:
            width_earlier = w0["va_width"]
    squeeze_pts = 0.0
    if width_now is not None and width_earlier is not None and width_earlier > 0:
        width_chg_pct = (width_now - width_earlier) / width_earlier * 100.0
        components["va_width_chg_pct"] = round(width_chg_pct, 3)
        poc_up = (shift or 0) > 0 or (vs_open or 0) > 0
        poc_down = (shift or 0) < 0 or (vs_open or 0) < 0
        if width_chg_pct < -5 and poc_up:
            # squeeze while migrating up = bullish continuation
            squeeze_pts = min(15.0, abs(width_chg_pct) / 20.0 * 15.0)
            bullets.append(
                f"Yükseklerde VA sıkışması (genişlik %{width_chg_pct:.1f}) — yükseliş devam sinyali."
            )
        elif width_chg_pct < -5 and poc_down:
            squeeze_pts = -min(15.0, abs(width_chg_pct) / 20.0 * 15.0)
            bullets.append(
                f"Düşüklerde VA sıkışması (genişlik %{width_chg_pct:.1f}) — zayıf/ayı devam."
            )
        elif width_chg_pct > 8:
            # expansion = indecision / distribution-ish → slight bearish if at highs
            if poc_up:
                squeeze_pts = -6.0
                bullets.append(f"VA genişliyor (%{width_chg_pct:+.1f}) — dağılım/kararsızlık riski.")
            else:
                squeeze_pts = 3.0
                bullets.append(f"VA genişliyor (%{width_chg_pct:+.1f}).")
        else:
            bullets.append(f"VA genişliği görece sabit (%{width_chg_pct:+.1f}).")
    components["va_squeeze_pts"] = round(squeeze_pts, 2)
    components["va_width"] = width_now
    components["va_width_earlier"] = width_earlier
    score += squeeze_pts

    # 5) Consecutive window direction streak (±5)
    streak_pts = 0.0
    poc_wins = poc.get("windows") or []
    if len(poc_wins) >= 3:
        deltas = [w.get("poc_delta") for w in poc_wins[-3:] if w.get("poc_delta") is not None]
        if len(deltas) >= 2:
            if all(d > 0 for d in deltas):
                streak_pts = 5.0
                bullets.append("Son pencerelerde ardışık POC yükselişi.")
            elif all(d < 0 for d in deltas):
                streak_pts = -5.0
                bullets.append("Son pencerelerde ardışık POC düşüşü.")
    components["streak_pts"] = round(streak_pts, 2)
    score += streak_pts

    score = round(max(0.0, min(100.0, score)), 1)

    if score >= 70:
        verdict = "yükseliş tetikleyici"
        bias = "bullish"
    elif score >= 40:
        verdict = "nötr"
        bias = "neutral"
    else:
        verdict = "zayıf"
        bias = "bearish"

    # Lead sentence
    if bias == "bullish":
        lead = (
            f"Seans profili boğa yönlü (skor {score:.0f}/100 — {verdict}). "
            "POC ve value area yukarı kayarken hacim kabulü güçleniyor."
        )
    elif bias == "bearish":
        lead = (
            f"Seans profili zayıf/ayı (skor {score:.0f}/100 — {verdict}). "
            "POC/VA aşağı veya sıkışma düşüklerde; yükseliş için teyit zayıf."
        )
    else:
        lead = (
            f"Seans profili nötr (skor {score:.0f}/100 — {verdict}). "
            "Net yön için POC/VA teyidi beklenmeli."
        )

    yorum = {
        "lead": lead,
        "bullets": bullets[:6],
        "verdict": verdict,
        "bias": bias,
    }

    return {
        "symbol": poc.get("symbol"),
        "date": poc.get("date"),
        "mode": mode,
        "score": score,
        "verdict": verdict,
        "bias": bias,
        "yorum": yorum,
        "components": components,
        "poc": {
            "current_poc": poc.get("current_poc"),
            "earlier_poc": poc.get("earlier_poc"),
            "session_open_poc": poc.get("session_open_poc"),
            "poc_shift": poc.get("poc_shift"),
            "poc_shift_pct": poc.get("poc_shift_pct"),
            "poc_shift_vs_open": poc.get("poc_shift_vs_open"),
            "poc_shift_vs_open_pct": poc.get("poc_shift_vs_open_pct"),
            "direction": poc.get("direction"),
            "window_count": poc.get("window_count"),
            "source_tf": poc.get("source_tf"),
        },
        "va": {
            "current_vah": va.get("current_vah"),
            "current_val": va.get("current_val"),
            "vah_shift": va.get("vah_shift"),
            "val_shift": va.get("val_shift"),
            "vah_arrow": va.get("vah_arrow"),
            "val_arrow": va.get("val_arrow"),
            "va_width": va.get("va_width"),
            "vah_vs_open": va.get("vah_vs_open"),
            "val_vs_open": va.get("val_vs_open"),
        },
        "method": PROFILE_BIAS_METHOD,
        "fallback_note": poc.get("fallback_note") or va.get("fallback_note"),
        "bar_count": poc.get("bar_count"),
        "error": poc.get("error") or va.get("error"),
    }


def compute_high_breaks(
    symbol: str,
    force: bool = False,
) -> dict[str, Any]:
    """Count running day-high breaks from 1m (fallback 5m) session bars."""
    sym = symbol.upper().replace(".IS", "")
    yahoo = f"{sym}.IS"
    day_bars, src_tf, target, fallback = _session_day_bars(yahoo, force=force)

    empty = {
        "symbol": sym,
        "date": target.isoformat() if target else None,
        "source_tf": src_tf,
        "high_break_count": 0,
        "max_vol_break_price": None,
        "max_vol_break_volume": None,
        "breaks": [],
        "session_high": None,
        "session_low": None,
        "bar_count": len(day_bars),
        "method": HIGH_BREAK_METHOD,
        "fallback_note": fallback,
    }
    if len(day_bars) < 2:
        empty["error"] = "no_intraday_bars"
        return empty

    # chronological
    bars = sorted(
        day_bars,
        key=lambda b: (b.get("time") is None, b.get("time") or 0, b.get("date") or ""),
    )

    running_high = None
    breaks: list[dict[str, Any]] = []
    sess_low = None
    for b in bars:
        h = b.get("high")
        l = b.get("low")
        v = float(b.get("volume") or 0)
        if h is None:
            continue
        h = float(h)
        if l is not None:
            l = float(l)
            sess_low = l if sess_low is None else min(sess_low, l)
        if running_high is None:
            running_high = h
            continue
        if h > running_high + 1e-12:
            # break — new high print
            o_raw = b.get("open")
            c_raw = b.get("close")
            try:
                o_val = float(o_raw) if o_raw is not None else None
            except (TypeError, ValueError):
                o_val = None
            try:
                c_val = float(c_raw) if c_raw is not None else None
            except (TypeError, ValueError):
                c_val = None
            prev = float(running_high)
            bullish = o_val is not None and c_val is not None and c_val > o_val
            close_above_prior = c_val is not None and c_val > prev
            breaks.append({
                "price": round(h, 4),
                "volume": int(round(v)),
                "prev_high": round(prev, 4),
                "open": round(o_val, 4) if o_val is not None else None,
                "close": round(c_val, 4) if c_val is not None else None,
                "bullish": bullish,
                "close_above_prior": close_above_prior,
                "time": b.get("time"),
                "date": b.get("date"),
            })
            running_high = h
        elif h > running_high:
            running_high = h

    max_vol_price = None
    max_vol = None
    if breaks:
        best = max(breaks, key=lambda x: x.get("volume") or 0)
        max_vol_price = best["price"]
        max_vol = best["volume"]

    return {
        "symbol": sym,
        "date": target.isoformat() if target else None,
        "source_tf": src_tf,
        "high_break_count": len(breaks),
        "max_vol_break_price": max_vol_price,
        "max_vol_break_volume": max_vol,
        "breaks": breaks,
        "session_high": round(running_high, 4) if running_high is not None else None,
        "session_low": round(sess_low, 4) if sess_low is not None else None,
        "bar_count": len(bars),
        "method": HIGH_BREAK_METHOD,
        "fallback_note": fallback,
    }


def compute_vwap_aort(
    symbol: str,
    force: bool = False,
) -> dict[str, Any]:
    """Session VWAP (typical×vol) and AORT (close×vol) from 1m bars."""
    sym = symbol.upper().replace(".IS", "")
    yahoo = f"{sym}.IS"
    day_bars, src_tf, target, fallback = _session_day_bars(yahoo, force=force)

    quote = quote_service.fetch_one(sym)
    last = None
    if quote and quote.get("price") is not None:
        last = float(quote["price"])

    empty = {
        "symbol": sym,
        "date": target.isoformat() if target else None,
        "source_tf": src_tf,
        "vwap": None,
        "aort": None,
        "aort_note": None,
        "last": last,
        "last_vs_vwap_pct": None,
        "last_vs_aort_pct": None,
        "distance_vwap": None,
        "distance_aort": None,
        "series": [],
        "bar_count": len(day_bars),
        "total_volume": 0,
        "method": VWAP_AORT_METHOD,
        "fallback_note": fallback,
    }
    if len(day_bars) < 2:
        empty["error"] = "no_intraday_bars"
        return empty

    bars = sorted(
        day_bars,
        key=lambda b: (b.get("time") is None, b.get("time") or 0, b.get("date") or ""),
    )

    cum_tp_vol = 0.0
    cum_c_vol = 0.0
    cum_vol = 0.0
    series: list[dict[str, Any]] = []
    vwap = aort = None

    for b in bars:
        h, l, c = b.get("high"), b.get("low"), b.get("close")
        v = float(b.get("volume") or 0)
        if c is None or v <= 0:
            continue
        c = float(c)
        h = float(h) if h is not None else c
        l = float(l) if l is not None else c
        if h < l:
            h, l = l, h
        typical = (h + l + c) / 3.0
        cum_tp_vol += typical * v
        cum_c_vol += c * v
        cum_vol += v
        if cum_vol <= 0:
            continue
        vwap = cum_tp_vol / cum_vol
        aort = cum_c_vol / cum_vol
        series.append({
            "time": b.get("time"),
            "date": b.get("date"),
            "vwap": round(vwap, 4),
            "aort": round(aort, 4),
            "close": round(c, 4),
        })

    if last is None and bars:
        for b in reversed(bars):
            if b.get("close") is not None:
                last = float(b["close"])
                break

    # If AORT ≈ VWAP within 0.02%, note equivalence
    aort_note = None
    if vwap is not None and aort is not None:
        if abs(vwap - aort) / max(abs(vwap), 1e-9) * 100.0 < 0.02:
            aort_note = "AORT ≈ seans VWAP-eşdeğeri (bar yaklaşımı; tick verisi yok)."
        else:
            aort_note = "AORT = Σ(kapanış×hacim)/Σ(hacim) — BIST ağırlıklı ort. bar yaklaşımı."

    def _dist(ref):
        if last is None or ref is None or ref == 0:
            return None, None
        d = last - ref
        pct = d / ref * 100.0
        return round(d, 4), round(pct, 3)

    d_vwap, pct_vwap = _dist(vwap)
    d_aort, pct_aort = _dist(aort)

    # Downsample series for chart if huge (keep ~200 pts)
    out_series = series
    if len(series) > 220:
        step = max(1, len(series) // 200)
        out_series = series[::step]
        if out_series[-1] is not series[-1]:
            out_series.append(series[-1])

    return {
        "symbol": sym,
        "date": target.isoformat() if target else None,
        "source_tf": src_tf,
        "vwap": round(vwap, 4) if vwap is not None else None,
        "aort": round(aort, 4) if aort is not None else None,
        "aort_note": aort_note,
        "last": last,
        "last_vs_vwap_pct": pct_vwap,
        "last_vs_aort_pct": pct_aort,
        "distance_vwap": d_vwap,
        "distance_aort": d_aort,
        "series": out_series,
        "bar_count": len(bars),
        "total_volume": int(round(cum_vol)),
        "method": VWAP_AORT_METHOD,
        "fallback_note": fallback,
    }


def compute_persistence(
    symbol: str,
    force: bool = False,
    dip_pct: float = 1.0,
    reclaim_max_bars: int = 15,
    reclaim_min_bars: int = 2,
) -> dict[str, Any]:
    """Detect dip→aggressive reclaim events (Israrcılar / tavan bulucu).

    Approximate whale insistence from Yahoo 1m OHLCV (no true tape):
    pullback ≥ dip_pct from recent local high, then reclaim within a short
    window with above-average volume and buy-biased bars.
    """
    from app.analysis import _bar_buy_sell_frac

    sym = symbol.upper().replace(".IS", "")
    yahoo = f"{sym}.IS"
    dip_pct = max(0.5, min(float(dip_pct or 1.0), 5.0))
    reclaim_max_bars = max(5, min(int(reclaim_max_bars or 15), 30))
    reclaim_min_bars = max(1, min(int(reclaim_min_bars or 2), 8))

    day_bars, src_tf, target, fallback = _session_day_bars(yahoo, force=force)
    bars = sorted(
        day_bars,
        key=lambda b: (b.get("time") is None, b.get("time") or 0, b.get("date") or ""),
    )

    quote = None
    cached = quote_service._cache or []
    quote = next((q for q in cached if q["symbol"] == sym), None)
    if not quote:
        quote = quote_service.fetch_one(sym)

    change_pct = quote.get("change_pct") if quote else None
    last = float(quote["price"]) if quote and quote.get("price") is not None else None
    volume = quote.get("volume") if quote else None
    name = (quote or {}).get("name")

    empty: dict[str, Any] = {
        "symbol": sym,
        "name": name,
        "date": target.isoformat() if target else None,
        "source_tf": src_tf,
        "change_pct": change_pct,
        "last": last,
        "price": last,
        "volume": volume,
        "reclaim_count": 0,
        "persistence_score": 0.0,
        "key_buy_level": None,
        "key_level_volume": None,
        "avg_reclaim_minutes": None,
        "buy_pressure_pct": None,
        "net_buy_vol": None,
        "reclaims": [],
        "levels": [],
        "yorum": None,
        "tavan_badge": False,
        "near_tavan": False,
        "bar_count": len(bars),
        "method": PERSISTENCE_METHOD,
        "fallback_note": fallback,
        "params": {
            "dip_pct": dip_pct,
            "reclaim_min_bars": reclaim_min_bars,
            "reclaim_max_bars": reclaim_max_bars,
        },
    }
    if len(bars) < 20:
        empty["error"] = "no_intraday_bars" if not bars else "insufficient_session_bars"
        empty["yorum"] = "Seans barı yetersiz — ısrar analizi yapılamadı."
        return empty

    # Bar metrics
    closes: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    vols: list[float] = []
    buy_flags: list[bool] = []
    buy_vols: list[float] = []
    sell_vols: list[float] = []
    for b in bars:
        o = b.get("open")
        h = b.get("high")
        l = b.get("low")
        c = b.get("close")
        v = float(b.get("volume") or 0)
        if c is None:
            closes.append(closes[-1] if closes else 0.0)
            highs.append(highs[-1] if highs else 0.0)
            lows.append(lows[-1] if lows else 0.0)
            vols.append(0.0)
            buy_flags.append(False)
            buy_vols.append(0.0)
            sell_vols.append(0.0)
            continue
        c = float(c)
        h = float(h) if h is not None else c
        l = float(l) if l is not None else c
        o = float(o) if o is not None else c
        if h < l:
            h, l = l, h
        bf, sf = _bar_buy_sell_frac(o, h, l, c)
        closes.append(c)
        highs.append(h)
        lows.append(l)
        vols.append(v)
        buy_flags.append(c > o and bf >= 0.55)
        buy_vols.append(v * bf)
        sell_vols.append(v * sf)

    n = len(closes)
    if last is None:
        last = closes[-1]
    avg_vol = sum(vols) / max(1, sum(1 for v in vols if v > 0))
    # rolling median of last 20 bar volumes as baseline
    def _local_avg_vol(i: int, win: int = 20) -> float:
        lo = max(0, i - win)
        chunk = [vols[j] for j in range(lo, i) if vols[j] > 0]
        if not chunk:
            return avg_vol or 1.0
        return sum(chunk) / len(chunk)

    # Local highs: high[i] >= highs in ±3 window
    local_high_idx: list[int] = []
    swing = 3
    for i in range(swing, n - 1):
        h = highs[i]
        if all(h >= highs[i + k] for k in range(-swing, swing + 1) if k != 0 and 0 <= i + k < n):
            local_high_idx.append(i)

    reclaims: list[dict[str, Any]] = []
    used_until = -1
    bar_minutes = 1 if src_tf == "1m" else 5

    for hi in local_high_idx:
        if hi <= used_until:
            continue
        peak = highs[hi]
        if peak <= 0:
            continue
        # Find deepest pullback within next reclaim_max_bars*2 window
        search_end = min(n, hi + reclaim_max_bars * 2 + 5)
        dip_i = None
        dip_px = peak
        for j in range(hi + 1, search_end):
            if lows[j] < dip_px:
                dip_px = lows[j]
                dip_i = j
            # stop searching deeper if already reclaiming strongly
            if dip_i is not None and j > dip_i + 2 and closes[j] > peak * 0.995:
                break
        if dip_i is None:
            continue
        drop_pct = (peak - dip_px) / peak * 100.0
        if drop_pct < dip_pct:
            continue
        # Reclaim window: from dip within reclaim_max_bars
        reclaim_end = min(n - 1, dip_i + reclaim_max_bars)
        reclaim_i = None
        for j in range(dip_i + reclaim_min_bars, reclaim_end + 1):
            # reclaim = close back above mid of peak-dip or ≥ 60% of drop recovered
            recovered = (closes[j] - dip_px) / max(peak - dip_px, 1e-9)
            if recovered >= 0.60 and closes[j] >= dip_px * (1.0 + dip_pct * 0.004):
                # require buy pressure in the reclaim window
                win_buy = sum(buy_vols[k] for k in range(dip_i, j + 1))
                win_sell = sum(sell_vols[k] for k in range(dip_i, j + 1))
                win_vol = sum(vols[k] for k in range(dip_i, j + 1))
                buy_bars = sum(1 for k in range(dip_i, j + 1) if buy_flags[k])
                local_avg = _local_avg_vol(dip_i)
                vol_ratio = (win_vol / max(1, (j - dip_i + 1))) / max(local_avg, 1.0)
                buy_dom = win_buy / max(win_buy + win_sell, 1.0) * 100.0
                if buy_dom < 52 and buy_bars < max(1, (j - dip_i + 1) // 2):
                    continue
                if vol_ratio < 0.85 and buy_dom < 58:
                    continue
                reclaim_i = j
                minutes = (j - dip_i) * bar_minutes
                speed = drop_pct / max(minutes, 0.5)  # % recovered per minute proxy
                strength = min(100.0, (
                    min(drop_pct, 5.0) / 5.0 * 25.0
                    + min(vol_ratio, 3.0) / 3.0 * 30.0
                    + (buy_dom - 50.0) / 50.0 * 25.0
                    + min(speed, 2.0) / 2.0 * 20.0
                ) * 100.0 / 100.0)
                reclaims.append({
                    "peak_price": round(peak, 4),
                    "dip_price": round(dip_px, 4),
                    "reclaim_price": round(closes[j], 4),
                    "drop_pct": round(drop_pct, 3),
                    "recovered_pct": round(recovered * 100.0, 2),
                    "minutes": minutes,
                    "bars": j - dip_i,
                    "volume": int(round(win_vol)),
                    "buy_vol": int(round(win_buy)),
                    "sell_vol": int(round(win_sell)),
                    "buy_dominance_pct": round(buy_dom, 2),
                    "vol_ratio": round(vol_ratio, 3),
                    "strength": round(strength, 1),
                    "dip_time": bars[dip_i].get("date") or bars[dip_i].get("time"),
                    "reclaim_time": bars[j].get("date") or bars[j].get("time"),
                    "peak_index": hi,
                    "dip_index": dip_i,
                    "reclaim_index": j,
                })
                used_until = j
                break
        if reclaim_i is None:
            continue

    reclaim_count = len(reclaims)
    total_buy = sum(buy_vols)
    total_sell = sum(sell_vols)
    buy_pressure = (
        round(total_buy / (total_buy + total_sell) * 100.0, 2)
        if (total_buy + total_sell) > 0
        else None
    )
    net_buy = int(round(total_buy - total_sell))

    # Key buy level: cluster of dip prices weighted by reclaim volume
    key_buy_level = None
    key_level_volume = None
    levels_out: list[dict] = []
    if reclaims:
        dips = sorted(reclaims, key=lambda r: r["dip_price"])
        clusters: list[list[dict]] = []
        cur: list[dict] = [dips[0]]
        for r in dips[1:]:
            ref = sum(x["dip_price"] for x in cur) / len(cur)
            if abs(r["dip_price"] - ref) / max(ref, 1e-9) * 100.0 <= 0.6:
                cur.append(r)
            else:
                clusters.append(cur)
                cur = [r]
        clusters.append(cur)
        scored = []
        for cl in clusters:
            wvol = sum(x["volume"] for x in cl)
            prices = [x["dip_price"] for x in cl]
            med = sorted(prices)[len(prices) // 2]
            scored.append({
                "price": round(med, 4),
                "touches": len(cl),
                "volume": int(wvol),
                "avg_strength": round(sum(x["strength"] for x in cl) / len(cl), 1),
            })
        scored.sort(key=lambda x: (x["touches"], x["volume"]), reverse=True)
        levels_out = scored[:5]
        key_buy_level = scored[0]["price"]
        key_level_volume = scored[0]["volume"]

    avg_minutes = None
    if reclaims:
        avg_minutes = round(sum(r["minutes"] for r in reclaims) / len(reclaims), 1)

    # Persistence score 0–100
    score = 0.0
    # reclaim count (up to 35)
    score += min(35.0, reclaim_count * 9.0)
    # avg strength (up to 25)
    if reclaims:
        score += min(25.0, sum(r["strength"] for r in reclaims) / len(reclaims) * 0.25)
    # buy pressure (up to 15)
    if buy_pressure is not None:
        score += max(0.0, min(15.0, (buy_pressure - 50.0) / 50.0 * 15.0))
    # Soft day-change boost (up to ~22) — never a hard list gate; persistence first
    chg = float(change_pct) if change_pct is not None else 0.0
    if chg >= 8.0:
        score += 16.0 + min(6.0, (chg - 8.0))
    elif chg >= 5.0:
        score += 10.0 + (chg - 5.0) / 3.0 * 6.0
    elif chg >= 2.0:
        score += 5.0 + (chg - 2.0) / 3.0 * 5.0  # ~+%3 still gets meaningful soft boost
    elif chg > 0:
        score += chg / 2.0 * 4.0
    score = round(max(0.0, min(100.0, score)), 1)

    # Badges only (not filters)
    tavan_badge = chg >= 8.0
    near_tavan = (not tavan_badge) and chg >= 5.0 and score >= 55 and reclaim_count >= 1

    # Turkish yorum
    if reclaim_count == 0:
        yorum = (
            f"Seans içinde belirgin dip→geri alma yok (eşik ≥%{dip_pct:g}). "
            + (f"Gün %{chg:+.1f}." if change_pct is not None else "")
        )
    else:
        parts = [
            f"{reclaim_count} kez dip sonrası ısrarlı alım (ort. {avg_minutes} dk).",
        ]
        if key_buy_level is not None:
            parts.append(f"Ana alım seviyesi ≈ {key_buy_level:.2f} (hacim {key_level_volume or 0:,}).")
        if buy_pressure is not None:
            parts.append(f"Seans alış baskısı %{buy_pressure:.1f}.")
        if tavan_badge:
            parts.append(f"TAVAN rozeti: gün %{chg:+.1f} (≥+8, filtre değil).")
        elif near_tavan:
            parts.append(f"Tavana yakın: gün %{chg:+.1f}, israr skoru {score:.0f}.")
        else:
            parts.append(f"Gün %{chg:+.1f}, israr skoru {score:.0f}.")
        yorum = " ".join(parts)

    return {
        "symbol": sym,
        "name": name,
        "date": target.isoformat() if target else None,
        "source_tf": src_tf,
        "change_pct": change_pct,
        "last": last,
        "price": last,
        "volume": volume,
        "rvol": (quote or {}).get("rvol"),
        "rvol10": (quote or {}).get("rvol10"),
        "reclaim_count": reclaim_count,
        "persistence_score": score,
        "key_buy_level": key_buy_level,
        "key_level_volume": key_level_volume,
        "avg_reclaim_minutes": avg_minutes,
        "buy_pressure_pct": buy_pressure,
        "net_buy_vol": net_buy,
        "reclaims": reclaims[-12:],
        "levels": levels_out,
        "yorum": yorum,
        "tavan_badge": tavan_badge,
        "near_tavan": near_tavan,
        "bar_count": n,
        "method": PERSISTENCE_METHOD,
        "fallback_note": fallback,
        "params": {
            "dip_pct": dip_pct,
            "reclaim_min_bars": reclaim_min_bars,
            "reclaim_max_bars": reclaim_max_bars,
        },
    }


TRADE_PLAN_METHOD = (
    "İşlem planı (intraday, matematiksel): yön = sinyal AL/SAT + footprint hakimiyet "
    "+ VWAP tarafı + RVOL bias. Long giriş ≈ destek/VWAP reclaim/israr seviyesi; "
    "stop = VAL/destek/swing altı (invalidation); TP1 = direnç/POC/VWAP; "
    "TP2 = gün yüksek / sonraki direnç / 2R uzatma. Short ayna. "
    "R:R(TP1)<1.2 veya yapı yoksa WAIT. Max ödül / min risk."
)


def _tp_num(x):
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def _tp_round(p: float | None, ref: float | None = None) -> float | None:
    if p is None:
        return None
    mid = ref if ref is not None else p
    tick = _tick_size(abs(mid) if mid else abs(p))
    dec = _tick_decimals(tick)
    # snap to tick
    idx = _idx_from_price(p, tick)
    return round(_price_from_idx(idx, tick), dec)


def _tp_pct(a: float, b: float) -> float | None:
    if b is None or b == 0 or a is None:
        return None
    return (a - b) / b * 100.0


def compute_trade_plan(
    symbol: str,
    force: bool = False,
    *,
    quote: dict | None = None,
    footprint: dict | None = None,
    signal: dict | None = None,
    sr: dict | None = None,
    vwap: dict | None = None,
    persistence: dict | None = None,
    high_breaks: dict | None = None,
) -> dict[str, Any]:
    """Build an intraday long/short/wait trade plan from session structure."""
    from app.analysis import build_signal

    sym = symbol.upper().replace(".IS", "")

    if quote is None:
        quote = quote_service.fetch_one(sym)
        if not quote:
            cached = quote_service._cache or []
            quote = next((q for q in cached if q["symbol"] == sym), None)
    if not quote:
        return {
            "symbol": sym,
            "direction": "WAIT",
            "error": "not_found",
            "method": TRADE_PLAN_METHOD,
            "disclaimer": "Yatırım tavsiyesi değildir.",
        }

    # Gather inputs (reuse callers' payloads when provided to avoid double work)
    if footprint is None:
        try:
            footprint = compute_volume_profile(sym, date_str="today", force=force)
        except Exception as e:
            logger.warning("trade-plan footprint %s: %s", sym, e)
            footprint = {}
    if signal is None:
        try:
            signal = build_signal(sym, force=False)
        except Exception as e:
            logger.warning("trade-plan signal %s: %s", sym, e)
            signal = {}
    if sr is None:
        try:
            sr = detect_support_resistance(sym, force=force)
        except Exception as e:
            logger.warning("trade-plan sr %s: %s", sym, e)
            sr = {}
    if vwap is None:
        try:
            vwap = compute_vwap_aort(sym, force=force)
        except Exception as e:
            logger.warning("trade-plan vwap %s: %s", sym, e)
            vwap = {}
    if persistence is None:
        try:
            persistence = compute_persistence(sym, force=force)
        except Exception as e:
            logger.warning("trade-plan persistence %s: %s", sym, e)
            persistence = {}
    if high_breaks is None:
        try:
            high_breaks = compute_high_breaks(sym, force=force)
        except Exception as e:
            logger.warning("trade-plan high_breaks %s: %s", sym, e)
            high_breaks = {}

    last = _tp_num(quote.get("price"))
    day_high = _tp_num(quote.get("day_high")) or _tp_num((high_breaks or {}).get("session_high"))
    day_low = _tp_num(quote.get("day_low")) or _tp_num((high_breaks or {}).get("session_low"))
    chg = _tp_num(quote.get("change_pct"))
    rvol = _tp_num(quote.get("rvol"))
    rvol10 = _tp_num(quote.get("rvol10"))

    fp = footprint or {}
    poc = _tp_num(fp.get("poc"))
    vah = _tp_num(fp.get("vah"))
    val = _tp_num(fp.get("val"))
    buy_dom = _tp_num(fp.get("buy_dominance_pct"))
    if buy_dom is None:
        buy_dom = _tp_num((signal or {}).get("buy_dominance_pct"))
    sell_dom = _tp_num(fp.get("sell_dominance_pct"))
    if sell_dom is None:
        sell_dom = _tp_num((signal or {}).get("sell_dominance_pct"))

    vwap_px = _tp_num((vwap or {}).get("vwap"))
    aort_px = _tp_num((vwap or {}).get("aort"))
    vs_vwap = _tp_num((vwap or {}).get("last_vs_vwap_pct"))

    ns = (sr or {}).get("nearest_support") or {}
    nr = (sr or {}).get("nearest_resistance") or {}
    support = _tp_num(ns.get("price") if isinstance(ns, dict) else None)
    resistance = _tp_num(nr.get("price") if isinstance(nr, dict) else None)

    key_buy = _tp_num((persistence or {}).get("key_buy_level"))
    pers_score = _tp_num((persistence or {}).get("persistence_score")) or 0.0
    hb_count = int((high_breaks or {}).get("high_break_count") or 0)

    verdict = ((signal or {}).get("verdict") or "TUT").upper()
    strength = (signal or {}).get("strength") or "normal"

    vol_hot = (rvol is not None and rvol >= 1.2) or (rvol10 is not None and rvol10 >= 1.2)
    vol_very_hot = (rvol is not None and rvol >= 1.5) or (rvol10 is not None and rvol10 >= 1.5)
    above_vwap = vs_vwap is not None and vs_vwap >= 0.05
    below_vwap = vs_vwap is not None and vs_vwap <= -0.05

    # --- Direction ---
    long_score = 0
    short_score = 0
    rationale: list[str] = []

    if verdict == "AL":
        long_score += 3 if strength == "guclu" else 2
        rationale.append(f"Sinyal AL ({strength}).")
    elif verdict == "SAT":
        short_score += 3 if strength == "guclu" else 2
        rationale.append(f"Sinyal SAT ({strength}).")
    else:
        rationale.append("Sinyal TUT — yapı net değilse bekle.")

    if buy_dom is not None and buy_dom >= 55:
        long_score += 2 if buy_dom >= 60 else 1
        rationale.append(f"Footprint alış %{buy_dom:.1f}.")
    elif sell_dom is not None and sell_dom >= 55:
        short_score += 2 if sell_dom >= 60 else 1
        rationale.append(f"Footprint satış %{sell_dom:.1f}.")

    if above_vwap:
        long_score += 1
        rationale.append(f"Fiyat VWAP üstü (%{vs_vwap:+.2f}).")
    elif below_vwap:
        short_score += 1
        rationale.append(f"Fiyat VWAP altı (%{vs_vwap:+.2f}).")

    if vol_very_hot:
        # amplify prevailing side
        if long_score >= short_score:
            long_score += 1
        else:
            short_score += 1
        rationale.append(f"RVOL sıcak (rvol={rvol}, rvol10={rvol10}).")
    elif vol_hot:
        rationale.append(f"RVOL ılımlı yüksek (rvol={rvol}, rvol10={rvol10}).")

    if pers_score >= 40 and key_buy is not None:
        long_score += 1
        rationale.append(f"Israr skoru {pers_score:.0f}; kilit alım {key_buy}.")

    if hb_count >= 3 and (chg is not None and chg > 0):
        long_score += 1
        rationale.append(f"Gün içi yüksek kırılım ×{hb_count}.")
    elif hb_count == 0 and chg is not None and chg < -1:
        short_score += 1

    direction = "WAIT"
    if long_score >= short_score + 2 and long_score >= 3:
        direction = "LONG"
    elif short_score >= long_score + 2 and short_score >= 3:
        direction = "SHORT"
    elif long_score >= 4 and long_score > short_score:
        direction = "LONG"
    elif short_score >= 4 and short_score > long_score:
        direction = "SHORT"

    empty_plan = {
        "symbol": sym,
        "name": quote.get("name"),
        "direction": "WAIT",
        "entry": None,
        "stop": None,
        "tp1": None,
        "tp2": None,
        "rr_tp1": None,
        "rr_tp2": None,
        "risk_pct": None,
        "reward_pct_tp1": None,
        "reward_pct_tp2": None,
        "rationale": rationale + ["Temiz yapı yok veya R:R yetersiz → WAIT."],
        "inputs": {
            "last": last,
            "day_high": day_high,
            "day_low": day_low,
            "vwap": vwap_px,
            "aort": aort_px,
            "poc": poc,
            "vah": vah,
            "val": val,
            "support": support,
            "resistance": resistance,
            "key_buy_level": key_buy,
            "verdict": verdict,
            "buy_dominance_pct": buy_dom,
            "rvol": rvol,
            "rvol10": rvol10,
            "high_break_count": hb_count,
            "persistence_score": pers_score,
            "long_score": long_score,
            "short_score": short_score,
        },
        "method": TRADE_PLAN_METHOD,
        "disclaimer": "Otomatik model planı · yatırım tavsiyesi değildir.",
    }

    if last is None or last <= 0:
        empty_plan["rationale"] = rationale + ["Son fiyat yok → WAIT."]
        return empty_plan

    buf = max(last * 0.0015, _tick_size(last) * 2)  # ~0.15% or 2 ticks

    def _levels_above(px: float) -> list[float]:
        cands = []
        for x in (resistance, poc, vah, vwap_px, aort_px, day_high):
            if x is not None and x > px + buf * 0.5:
                cands.append(x)
        return sorted(set(round(c, 4) for c in cands))

    def _levels_below(px: float) -> list[float]:
        cands = []
        for x in (support, poc, val, vwap_px, aort_px, day_low, key_buy):
            if x is not None and x < px - buf * 0.5:
                cands.append(x)
        return sorted(set(round(c, 4) for c in cands), reverse=True)

    entry = stop = tp1 = tp2 = None
    plan_notes: list[str] = list(rationale)

    if direction == "LONG":
        # Entry: near support / VWAP reclaim / key_buy if close below last; else last
        entry_cands = []
        for label, lvl in (
            ("destek", support),
            ("VWAP", vwap_px),
            ("israr", key_buy),
            ("VAL", val),
            ("POC", poc if poc is not None and poc <= last else None),
        ):
            if lvl is None:
                continue
            dist_pct = abs(last - lvl) / last * 100.0
            if lvl <= last and dist_pct <= 1.2:
                entry_cands.append((dist_pct, lvl, label))
        if entry_cands:
            entry_cands.sort(key=lambda t: t[0])
            _, entry, elabel = entry_cands[0]
            plan_notes.append(f"Giriş: {elabel} yakını ({entry}).")
        else:
            # pullback preferred; if stretched above VWAP without nearby support → WAIT
            if above_vwap and support is None and key_buy is None:
                empty_plan["direction"] = "WAIT"
                empty_plan["rationale"] = plan_notes + [
                    "Long bias var ama yakında destek/israr yok — beklemeyi tercih et."
                ]
                return empty_plan
            entry = last
            plan_notes.append(f"Giriş: piyasa / son fiyat ({entry}).")

        # Stop: below invalidation (VAL / support / key_buy / day_low)
        stop_raw = None
        for lvl in (val, support, key_buy, day_low):
            if lvl is not None and lvl < entry:
                stop_raw = lvl if stop_raw is None else min(stop_raw, lvl)
        if stop_raw is None:
            stop_raw = entry * 0.985  # 1.5% soft stop fallback
            plan_notes.append("Stop: yapı yok — %1.5 soft stop.")
        else:
            plan_notes.append(f"Stop: invalidation altı ({stop_raw}).")
        stop = stop_raw - buf

        # TP1: nearest resistance / POC / VWAP above entry
        above = _levels_above(entry)
        # prefer levels that give R:R >= 1.2
        risk = entry - stop
        if risk <= 0:
            empty_plan["direction"] = "WAIT"
            empty_plan["rationale"] = plan_notes + ["Risk ≤ 0 — WAIT."]
            return empty_plan
        tp1 = None
        for lvl in above:
            reward = lvl - entry
            if reward / risk >= 1.2:
                tp1 = lvl
                break
        if tp1 is None and above:
            tp1 = above[0]
        if tp1 is None:
            tp1 = entry + risk * 1.5  # synthetic 1.5R
            plan_notes.append("TP1: sentetik 1.5R (üst yapı yok).")
        else:
            plan_notes.append(f"TP1: en yakın uygun direnç/POC/VWAP ({tp1}).")

        # TP2: day high or next level or 2R
        tp2_cands = [x for x in above if x > tp1 + buf * 0.25]
        if day_high is not None and day_high > tp1:
            tp2_cands.append(day_high)
        if tp2_cands:
            tp2 = max(tp2_cands) if day_high in tp2_cands else min(tp2_cands)
            # prefer day_high if extended, else next resistance
            if day_high is not None and day_high > tp1:
                tp2 = day_high
            else:
                tp2 = min(tp2_cands)
            plan_notes.append(f"TP2: gün yüksek / sonraki direnç ({tp2}).")
        else:
            tp2 = entry + risk * 2.0
            plan_notes.append("TP2: 2R uzatma.")

    elif direction == "SHORT":
        entry_cands = []
        for label, lvl in (
            ("direnç", resistance),
            ("VWAP", vwap_px),
            ("VAH", vah),
            ("POC", poc if poc is not None and poc >= last else None),
        ):
            if lvl is None:
                continue
            dist_pct = abs(last - lvl) / last * 100.0
            if lvl >= last and dist_pct <= 1.2:
                entry_cands.append((dist_pct, lvl, label))
        if entry_cands:
            entry_cands.sort(key=lambda t: t[0])
            _, entry, elabel = entry_cands[0]
            plan_notes.append(f"Giriş: {elabel} yakını ({entry}).")
        else:
            if below_vwap and resistance is None:
                empty_plan["direction"] = "WAIT"
                empty_plan["rationale"] = plan_notes + [
                    "Short bias var ama yakında direnç yok — beklemeyi tercih et."
                ]
                return empty_plan
            entry = last
            plan_notes.append(f"Giriş: piyasa / son fiyat ({entry}).")

        stop_raw = None
        for lvl in (vah, resistance, day_high):
            if lvl is not None and lvl > entry:
                stop_raw = lvl if stop_raw is None else max(stop_raw, lvl)
        if stop_raw is None:
            stop_raw = entry * 1.015
            plan_notes.append("Stop: yapı yok — %1.5 soft stop.")
        else:
            plan_notes.append(f"Stop: invalidation üstü ({stop_raw}).")
        stop = stop_raw + buf

        risk = stop - entry
        if risk <= 0:
            empty_plan["direction"] = "WAIT"
            empty_plan["rationale"] = plan_notes + ["Risk ≤ 0 — WAIT."]
            return empty_plan

        below = _levels_below(entry)
        tp1 = None
        for lvl in below:
            reward = entry - lvl
            if reward / risk >= 1.2:
                tp1 = lvl
                break
        if tp1 is None and below:
            tp1 = below[0]
        if tp1 is None:
            tp1 = entry - risk * 1.5
            plan_notes.append("TP1: sentetik 1.5R (alt yapı yok).")
        else:
            plan_notes.append(f"TP1: en yakın uygun destek/POC/VWAP ({tp1}).")

        tp2_cands = [x for x in below if x < tp1 - buf * 0.25]
        if day_low is not None and day_low < tp1:
            tp2 = day_low
            plan_notes.append(f"TP2: gün düşük ({tp2}).")
        elif tp2_cands:
            tp2 = min(tp2_cands)
            plan_notes.append(f"TP2: sonraki destek ({tp2}).")
        else:
            tp2 = entry - risk * 2.0
            plan_notes.append("TP2: 2R uzatma.")
    else:
        return empty_plan

    entry = _tp_round(entry, last)
    stop = _tp_round(stop, last)
    tp1 = _tp_round(tp1, last)
    tp2 = _tp_round(tp2, last)

    if entry is None or stop is None or tp1 is None:
        empty_plan["rationale"] = plan_notes + ["Seviye yuvarlama başarısız → WAIT."]
        return empty_plan

    if direction == "LONG":
        risk = entry - stop
        reward1 = tp1 - entry
        reward2 = (tp2 - entry) if tp2 is not None else None
    else:
        risk = stop - entry
        reward1 = entry - tp1
        reward2 = (entry - tp2) if tp2 is not None else None

    if risk <= 0 or reward1 is None or reward1 <= 0:
        empty_plan["rationale"] = plan_notes + ["Ödül/risk geçersiz → WAIT."]
        return empty_plan

    rr1 = round(reward1 / risk, 2)
    rr2 = round(reward2 / risk, 2) if reward2 and reward2 > 0 else None
    risk_pct = round(abs(risk) / entry * 100.0, 3)
    reward_pct1 = round(abs(reward1) / entry * 100.0, 3)
    reward_pct2 = round(abs(reward2) / entry * 100.0, 3) if reward2 else None

    # Min R:R gate
    if rr1 < 1.2:
        empty_plan["direction"] = "WAIT"
        empty_plan["entry"] = entry
        empty_plan["stop"] = stop
        empty_plan["tp1"] = tp1
        empty_plan["tp2"] = tp2
        empty_plan["rr_tp1"] = rr1
        empty_plan["risk_pct"] = risk_pct
        empty_plan["rationale"] = plan_notes + [
            f"R:R(TP1)={rr1} < 1.2 — planı atla (WAIT)."
        ]
        empty_plan["inputs"]["long_score"] = long_score
        empty_plan["inputs"]["short_score"] = short_score
        return empty_plan

    plan_notes.append(f"R:R TP1={rr1}" + (f" · TP2={rr2}" if rr2 else "") + f" · risk %{risk_pct}.")
    plan_notes.append("Max ödül / min risk ilkesi uygulandı.")

    return {
        "symbol": sym,
        "name": quote.get("name"),
        "direction": direction,
        "entry": entry,
        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,
        "rr_tp1": rr1,
        "rr_tp2": rr2,
        "risk_pct": risk_pct,
        "reward_pct_tp1": reward_pct1,
        "reward_pct_tp2": reward_pct2,
        "rationale": plan_notes,
        "inputs": {
            "last": last,
            "day_high": day_high,
            "day_low": day_low,
            "change_pct": chg,
            "vwap": vwap_px,
            "aort": aort_px,
            "poc": poc,
            "vah": vah,
            "val": val,
            "support": support,
            "resistance": resistance,
            "key_buy_level": key_buy,
            "verdict": verdict,
            "strength": strength,
            "buy_dominance_pct": buy_dom,
            "sell_dominance_pct": sell_dom,
            "rvol": rvol,
            "rvol10": rvol10,
            "high_break_count": hb_count,
            "persistence_score": pers_score,
            "long_score": long_score,
            "short_score": short_score,
        },
        "method": TRADE_PLAN_METHOD,
        "disclaimer": "Otomatik model planı · yatırım tavsiyesi değildir.",
    }


# ─── v1.15: Momentumlu Hızlanış (momentum burst) ─────────────────────────────

MOMENTUM_WINDOWS = (1, 3, 5, 10, 15)  # minutes

MOMENTUM_BURST_METHOD = (
    "Momentumlu Hızlanış: son W dakika (1/3/5/10/15) 1m barlarında (yoksa 5m) "
    "aşırı yukarı momentum. "
    "window_% = (C_son − C_ilk)/C_ilk×100; "
    "velocity = pencere sonu − başlangıç (aynı %); "
    "accel_% = ikinci yarı getiri − birinci yarı getiri (fiyat hızlanıyor); "
    "vol_surge = pencere hacmi ÷ önceki eşit pencere hacmi; "
    "yeşil oranı + son N mum hep yeşil bonusu. "
    "Skor (0–100): window 35% + accel 30% + vol_surge 20% + green 15% (+all-green bonus). "
    "Yalnızca yukarı (window_%>0); negatif accel cezası. Nadir/sıcak sıralama."
)

MOMENTUM_ALARM_RULE = (
    "Momentumlu Hızlanış alarmı — likit evrende son W dk aşırı yukarı momentum: "
    "window_% ≥ eşik VE skor ≥ min_score VE accel_% > 0 (hızlanan yükseliş) "
    "VE (isteğe bağlı) son N mum yeşil. Nadir ani fırlayışlar; ranking tek başına alarm değil."
)

# Typical "rare spike" % by window — used for score normalization & default alarm floor
MOMENTUM_RARE_PCT: dict[int, float] = {
    1: 0.9,
    3: 1.3,
    5: 1.8,
    10: 2.4,
    15: 3.0,
}


def _bar_ts(bar: dict) -> int | None:
    """Unix seconds from bar time or date string."""
    t = bar.get("time")
    if t is not None:
        try:
            return int(t)
        except (TypeError, ValueError):
            pass
    d = bar.get("date")
    if not d:
        return None
    try:
        s = str(d).strip()
        if len(s) >= 19:
            dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
        elif len(s) >= 10:
            dt = datetime.strptime(s[:10], "%Y-%m-%d").replace(tzinfo=IST)
        else:
            return None
        return int(dt.timestamp())
    except Exception:
        return None


def _slice_last_minutes(bars: list[dict], window_min: int) -> list[dict]:
    """Return bars whose timestamp is within window_min of the last bar."""
    if not bars or window_min <= 0:
        return []
    last_ts = None
    for b in reversed(bars):
        last_ts = _bar_ts(b)
        if last_ts is not None:
            break
    if last_ts is None:
        # fall back to last N bars assuming 1m
        n = max(2, int(window_min))
        return list(bars[-n:])
    cutoff = last_ts - int(window_min) * 60
    out = []
    for b in bars:
        ts = _bar_ts(b)
        if ts is None or ts >= cutoff:
            out.append(b)
    return out if out else list(bars[-max(2, window_min):])


def compute_momentum_burst(
    symbol: str,
    window_min: int = 5,
    force: bool = False,
    green_n: int = 3,
) -> dict[str, Any]:
    """Extreme upward momentum in the last ``window_min`` minutes.

    Metrics: window_%, velocity (end vs start), accel_%, vol_surge, green streak/score.
    """
    sym = symbol.upper().replace(".IS", "")
    yahoo = f"{sym}.IS"
    try:
        w = int(window_min)
    except (TypeError, ValueError):
        w = 5
    if w not in MOMENTUM_WINDOWS:
        # nearest allowed
        w = min(MOMENTUM_WINDOWS, key=lambda x: abs(x - w))
    green_n = max(1, min(int(green_n or 3), 10))

    day_bars, src_tf, sess_date, fb_note = _session_day_bars(yahoo, force=force)
    # Prefer 1m for fine windows; _session_day_bars already falls back 5m / İş Yatırım
    bars = day_bars or []

    quote = None
    cached = quote_service._cache or []
    quote = next((q for q in cached if q["symbol"] == sym), None)
    if not quote:
        try:
            quote = quote_service.fetch_one(sym)
        except Exception:
            quote = None

    empty: dict[str, Any] = {
        "symbol": sym,
        "name": (quote or {}).get("name"),
        "price": (quote or {}).get("price"),
        "change_pct": (quote or {}).get("change_pct"),
        "volume": (quote or {}).get("volume"),
        "rvol": (quote or {}).get("rvol"),
        "rvol10": (quote or {}).get("rvol10"),
        "window_min": w,
        "score": None,
        "window_pct": None,
        "velocity_pct": None,
        "accel_pct": None,
        "vol_surge": None,
        "green_ratio": None,
        "all_green": False,
        "green_streak": 0,
        "method": MOMENTUM_BURST_METHOD,
        "source_tf": src_tf,
        "session_date": sess_date.isoformat() if sess_date else None,
        "fallback_note": fb_note,
        "bar_count": len(bars),
    }

    # Need enough bars: at least ~half the window in bar units
    min_bars = 2 if w <= 1 else max(3, min(w // (5 if src_tf == "5m" else 1), w))
    if len(bars) < min_bars:
        empty["error"] = "insufficient_bars"
        return empty

    window = _slice_last_minutes(bars, w)
    # If 5m source, window by bar count ≈ ceil(w/5)
    if src_tf == "5m" and w < 5:
        window = bars[-1:] if bars else []
    elif src_tf == "5m":
        n5 = max(2, int(math.ceil(w / 5.0)))
        window = bars[-n5:]

    if len(window) < 2:
        empty["error"] = "thin_window"
        empty["bar_count_window"] = len(window)
        return empty

    closes = [float(b["close"]) for b in window if b.get("close") is not None]
    if len(closes) < 2 or not closes[0]:
        empty["error"] = "bad_closes"
        return empty

    c0 = closes[0]
    c1 = closes[-1]
    window_pct = (c1 - c0) / c0 * 100.0
    velocity_pct = window_pct  # end vs start of window

    # Acceleration: second half return − first half return
    half = max(1, len(closes) // 2)
    first = closes[:half]
    second = closes[half:] if len(closes) > half else closes[-max(1, half):]
    ret1 = (first[-1] - first[0]) / first[0] * 100.0 if first and first[0] else 0.0
    ret2 = (
        (second[-1] - second[0]) / second[0] * 100.0
        if second and second[0]
        else 0.0
    )
    accel_pct = ret2 - ret1

    # Volume surge vs prior equal-length window
    def _vol_sum(bs: list[dict]) -> float:
        s = 0.0
        for b in bs:
            v = b.get("volume")
            if v is not None:
                try:
                    s += float(v)
                except (TypeError, ValueError):
                    pass
        return s

    win_vol = _vol_sum(window)
    # prior window: bars immediately before `window` in day_bars
    try:
        idx0 = bars.index(window[0])
    except ValueError:
        idx0 = max(0, len(bars) - len(window))
    prior = bars[max(0, idx0 - len(window)):idx0]
    prior_vol = _vol_sum(prior)
    if prior_vol > 0:
        vol_surge = win_vol / prior_vol
    elif win_vol > 0:
        vol_surge = 2.0  # no prior — treat as elevated if any volume
    else:
        vol_surge = 1.0

    # Green ratio + trailing all-green streak
    green = 0
    valid = 0
    streak = 0
    for b in window:
        o = b.get("open")
        c = b.get("close")
        if c is None:
            continue
        o = float(o) if o is not None else float(c)
        valid += 1
        if float(c) >= o:
            green += 1
    green_ratio = green / max(1, valid)

    for b in reversed(window):
        o = b.get("open")
        c = b.get("close")
        if c is None:
            break
        o = float(o) if o is not None else float(c)
        if float(c) >= o:
            streak += 1
        else:
            break
    all_green = streak >= green_n

    # --- Score 0–100 (rarest / hottest upward bursts) ---
    rare = MOMENTUM_RARE_PCT.get(w, 2.0)
    # window: 0 at 0%, ~70 at rare, 100 at 2×rare
    wp_s = max(0.0, min(100.0, (window_pct / max(rare, 0.1)) * 70.0))
    # accel: map -2..+4 → 0..100
    accel_s = max(0.0, min(100.0, (accel_pct + 2.0) / 6.0 * 100.0))
    # vol_surge: 1×→25, 2×→50, 4×→100
    vol_s = max(0.0, min(100.0, (float(vol_surge) - 0.5) / 3.5 * 100.0))
    green_s = green_ratio * 100.0

    score = (
        0.35 * wp_s
        + 0.30 * accel_s
        + 0.20 * vol_s
        + 0.15 * green_s
    )
    if all_green:
        score += 12.0
    if window_pct <= 0:
        score = 0.0
    elif accel_pct < 0:
        score *= 0.55
    score = round(max(0.0, min(100.0, score)), 2)

    return {
        "symbol": sym,
        "name": (quote or {}).get("name"),
        "price": (quote or {}).get("price"),
        "change_pct": (quote or {}).get("change_pct"),
        "volume": (quote or {}).get("volume"),
        "rvol": (quote or {}).get("rvol"),
        "rvol10": (quote or {}).get("rvol10"),
        "window_min": w,
        "score": score,
        "window_pct": round(window_pct, 3),
        "velocity_pct": round(velocity_pct, 3),
        "accel_pct": round(accel_pct, 3),
        "vol_surge": round(vol_surge, 3),
        "green_ratio": round(green_ratio, 3),
        "green_streak": streak,
        "all_green": all_green,
        "green_n": green_n,
        "components": {
            "window_score": round(wp_s, 2),
            "accel_score": round(accel_s, 2),
            "vol_score": round(vol_s, 2),
            "green_score": round(green_s, 2),
            "ret_first_half_pct": round(ret1, 3),
            "ret_second_half_pct": round(ret2, 3),
            "win_vol": int(win_vol) if win_vol else 0,
            "prior_vol": int(prior_vol) if prior_vol else 0,
            "rare_pct_ref": rare,
        },
        "method": MOMENTUM_BURST_METHOD,
        "source_tf": src_tf,
        "session_date": sess_date.isoformat() if sess_date else None,
        "fallback_note": fb_note,
        "bar_count": len(bars),
        "bar_count_window": len(window),
        "window_start": window[0].get("date"),
        "window_end": window[-1].get("date"),
    }
