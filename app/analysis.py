"""Stock short notes (Turkish) + intraday volume profile."""
from __future__ import annotations

import logging
import time
import threading
import math
from datetime import date, datetime, timedelta
from typing import Any

from zoneinfo import ZoneInfo

from app.history_cache import TF_INTERVALS, fetch_bars, rvol_from_bars
from app.quotes import IST, quote_service

logger = logging.getLogger(__name__)

NOTES_RULES = (
    "Önemli kısa notlar (2–5 madde, olgusal): "
    "günlük değişim %; RVOL / RVOL(10); fiyata göre gün yüksek/düşüğüne uzaklık; "
    "hacim vs önceki seans; çoklu TF son mum yönü (yükseliş/düşüş sayısı); "
    "istikrarlı/hızlı bayrakları varsa eklenir. Tahmin veya tavsiye yok."
)

VP_METHOD = (
    "Günlük footprint: son seans gününün 1m (yoksa 5m) OHLCV barları. "
    "Her barın hacmi low–high arası tick seviyelerine eşit dağıtılır (volume-at-price). "
    "Alış/satış: klasik bar sınıflandırması — close>open ise alış oranı (close−low)/(high−low); "
    "close<open ise satış oranı (high−close)/(high−low); doji %50/%50. "
    "times_tested = o seviyeyi [low,high] ile dokunan bar sayısı. "
    "Tick (fiyata göre): 0.01 / 0.02 / 0.05. Anahtar = tamsayı tick indeksi. "
    "POC = max toplam hacim; VAH/VAL = POC etrafında kümülatif %70 value area."
)


def _tick_size(price: float) -> float:
    """Adaptive BIST-style tick by price level (0.01 / 0.02 / 0.05)."""
    p = abs(float(price) or 1.0)
    if p < 20:
        return 0.01
    if p < 50:
        return 0.02
    return 0.05


def _tick_decimals(tick: float) -> int:
    t = abs(float(tick) or 0.01)
    if t >= 1:
        return 0
    s = f"{t:.10f}".rstrip("0")
    if "." in s:
        return len(s.split(".", 1)[1])
    return 2


def _price_from_idx(idx: int, tick: float) -> float:
    dec = _tick_decimals(tick)
    return round(idx * tick, dec)


def _idx_from_price(price: float, tick: float) -> int:
    if tick <= 0:
        return int(round(price * 100))
    return int(round(float(price) / tick))


def _round_tick(price: float, tick: float) -> float:
    return _price_from_idx(_idx_from_price(price, tick), tick)


def _fmt_pct(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{v:+.2f}%"


def _fmt_num(v: float | None, digits: int = 2) -> str:
    if v is None:
        return "—"
    return f"{v:.{digits}f}"


def _fmt_vol(v: int | float | None) -> str:
    if v is None:
        return "—"
    v = float(v)
    if abs(v) >= 1_000_000:
        return f"{v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"{v/1_000:.1f}K"
    return f"{int(v)}"


def generate_notes(
    quote: dict[str, Any],
    rvol_tf: dict[str, Any] | None = None,
    change_pct_tf: dict[str, float | None] | None = None,
    flags: dict[str, Any] | None = None,
) -> list[str]:
    """Build 2–5 factual Turkish bullet notes from quote + TF bias."""
    notes: list[str] = []
    chg = quote.get("change_pct")
    if chg is not None:
        notes.append(f"Günlük değişim {_fmt_pct(chg)}.")

    rvol = quote.get("rvol")
    rvol10 = quote.get("rvol10")
    if rvol is not None or rvol10 is not None:
        parts = []
        if rvol is not None:
            parts.append(f"RVOL {rvol:.2f}× (önceki seans)")
        if rvol10 is not None:
            parts.append(f"RVOL(10) {rvol10:.2f}×")
        notes.append("; ".join(parts) + ".")

    price = quote.get("price")
    day_high = quote.get("day_high")
    day_low = quote.get("day_low")
    if price is not None and day_high is not None and day_low is not None and day_high > day_low:
        span = day_high - day_low
        from_high = (day_high - price) / span * 100.0
        from_low = (price - day_low) / span * 100.0
        notes.append(
            f"Fiyat gün aralığında: düşükten %{from_low:.0f}, yüksekten %{from_high:.0f} "
            f"(L {_fmt_num(day_low)} / H {_fmt_num(day_high)})."
        )
    elif price is not None and day_high is not None:
        notes.append(f"Gün yükseğine uzaklık: {_fmt_num(day_high - price)} TL.")
    elif price is not None and day_low is not None:
        notes.append(f"Gün düşüğüne uzaklık: {_fmt_num(price - day_low)} TL.")

    vol = quote.get("volume")
    prev_vol = quote.get("prev_volume")
    if vol is not None and prev_vol is not None and prev_vol > 0:
        ratio = vol / prev_vol
        notes.append(
            f"Hacim {_fmt_vol(vol)} vs önceki seans {_fmt_vol(prev_vol)} ({ratio:.2f}×)."
        )
    elif vol is not None:
        notes.append(f"Bugünkü hacim {_fmt_vol(vol)}.")

    # Multi-TF last-bar bias
    chg_map = change_pct_tf or {}
    if not chg_map and rvol_tf:
        # rvol_tf detail may nest change_pct
        pass
    up = down = flat = 0
    for tf in TF_INTERVALS:
        c = None
        if change_pct_tf and tf in change_pct_tf:
            c = change_pct_tf.get(tf)
        if c is None:
            continue
        if c > 0.05:
            up += 1
        elif c < -0.05:
            down += 1
        else:
            flat += 1
    total = up + down + flat
    if total >= 3:
        if up > down and up >= total * 0.55:
            bias = "çoklu TF yükseliş eğilimi"
        elif down > up and down >= total * 0.55:
            bias = "çoklu TF düşüş eğilimi"
        else:
            bias = "çoklu TF karışık"
        notes.append(f"Son mum yönü: {up}↑ / {down}↓ / {flat}→ — {bias}.")

    flags = flags or {}
    if flags.get("steady"):
        notes.append("İstikrarlı yükselen taramasında işaretli.")
    if flags.get("fast"):
        notes.append("Hızlı hareket taramasında işaretli.")

    # Cap 2–5; ensure at least 2 if we have anything
    notes = notes[:5]
    if len(notes) < 2 and price is not None:
        notes.append(f"Son fiyat {_fmt_num(price)} {quote.get('currency') or 'TRY'}.")
    return notes


def build_stock_notes(symbol: str, force: bool = False) -> dict[str, Any]:
    from app.scanners import scanner_service

    quote = quote_service.fetch_one(symbol)
    if not quote:
        cached = quote_service._cache or []
        sym = symbol.upper().replace(".IS", "")
        quote = next((q for q in cached if q["symbol"] == sym), None)
    if not quote:
        return {"symbol": symbol.upper().replace(".IS", ""), "notes": [], "error": "not_found"}

    rvol_tf = None
    change_pct_tf = None
    try:
        data = scanner_service.stock_rvol_tf(symbol, force=force)
        rvol_tf = data.get("rvol_tf")
        change_pct_tf = data.get("change_pct_tf")
    except Exception as e:
        logger.warning("notes rvol_tf %s: %s", symbol, e)

    notes = generate_notes(quote, rvol_tf=rvol_tf, change_pct_tf=change_pct_tf)
    return {
        "symbol": quote["symbol"],
        "notes": notes,
        "rules": NOTES_RULES,
        "rvol_tf": rvol_tf,
        "change_pct_tf": change_pct_tf,
        "stock": {
            "price": quote.get("price"),
            "change_pct": quote.get("change_pct"),
            "rvol": quote.get("rvol"),
            "rvol10": quote.get("rvol10"),
            "day_high": quote.get("day_high"),
            "day_low": quote.get("day_low"),
            "volume": quote.get("volume"),
            "prev_volume": quote.get("prev_volume"),
        },
    }


def _parse_session_date(date_str: str | None) -> date:
    now = datetime.now(IST).date()
    if not date_str or date_str.lower() in ("today", "bugun", "bugün"):
        return now
    try:
        return date.fromisoformat(date_str[:10])
    except Exception:
        return now


def _bar_session_date(bar: dict) -> date | None:
    d = bar.get("date") or ""
    try:
        return date.fromisoformat(str(d)[:10])
    except Exception:
        t = bar.get("time")
        if t is not None:
            return datetime.fromtimestamp(int(t), tz=IST).date()
    return None



def _bar_buy_sell_frac(o: float, h: float, l: float, c: float) -> tuple[float, float]:
    """Classic bar buy/sell fraction (same rule as volume profile)."""
    hl = h - l
    if hl <= 0 or abs(c - o) < 1e-12:
        return 0.5, 0.5
    if c > o:
        buy_frac = max(0.0, min(1.0, (c - l) / hl))
    else:
        sell_frac = max(0.0, min(1.0, (h - c) / hl))
        buy_frac = 1.0 - sell_frac
    return buy_frac, 1.0 - buy_frac


def session_buy_sell_totals(
    bars: list[dict],
    target: date | None = None,
) -> dict[str, Any]:
    """Session buy/sell/net totals from OHLCV bars (no price-level VAP).

    Uses the same classic close-vs-open split as günlük footprint, but aggregates
    at bar level — suitable for scanning ~150 names without tick maps.
    """
    if not bars:
        return {
            "buy_vol": 0,
            "sell_vol": 0,
            "net_vol": 0,
            "total_vol": 0,
            "buy_dominance_pct": None,
            "sell_dominance_pct": None,
            "bar_count": 0,
            "date": None,
            "source_tf": None,
        }

    # Pick session: explicit target, else latest date present
    if target is None:
        dates = sorted(
            {d for d in (_bar_session_date(b) for b in bars) if d is not None},
            reverse=True,
        )
        target = dates[0] if dates else None

    day_bars = [b for b in bars if _bar_session_date(b) == target] if target else list(bars)
    buy_acc = 0.0
    sell_acc = 0.0
    n = 0
    for bar in day_bars:
        o = bar.get("open")
        h = bar.get("high")
        l = bar.get("low")
        c = bar.get("close")
        v = float(bar.get("volume") or 0)
        if h is None or l is None or c is None:
            continue
        h = float(h)
        l = float(l)
        c = float(c)
        o = float(o) if o is not None else c
        if h < l:
            h, l = l, h
        if v <= 0:
            n += 1
            continue
        bf, sf = _bar_buy_sell_frac(o, h, l, c)
        buy_acc += v * bf
        sell_acc += v * sf
        n += 1

    buy_vol = int(round(buy_acc))
    sell_vol = int(round(sell_acc))
    total = buy_vol + sell_vol
    buy_dom = round(buy_vol / total * 100.0, 2) if total > 0 else None
    sell_dom = round(100.0 - buy_dom, 2) if buy_dom is not None else None
    return {
        "buy_vol": buy_vol,
        "sell_vol": sell_vol,
        "net_vol": buy_vol - sell_vol,
        "total_vol": total,
        "buy_dominance_pct": buy_dom,
        "sell_dominance_pct": sell_dom,
        "bar_count": n,
        "date": target.isoformat() if target else None,
    }


_VP_CACHE_TTL = 40.0
_vp_cache: dict[str, tuple[float, dict]] = {}
_vp_lock = threading.Lock()


LIVE_FP_METHOD = (
    "İdealData canlı kademe analizi (Y38): her fiyat seviyesinde gerçekleşen gerçek lot × "
    "alış% / satış% (aktif alıcı/satıcı). POC = en çok lot; VA = POC'tan genişleyen %70."
)


def _merge_live_footprint(base: dict[str, Any] | None, live: dict[str, Any], sym: str) -> dict[str, Any]:
    """Build a footprint payload (same schema) from live İdealData Y38 levels."""
    base = base or {}
    dec = int(live.get("tick_decimals") or 2)
    tick = live.get("tick") or base.get("tick") or 0.01
    tested: dict[str, int] = {}
    for bl in base.get("levels") or []:
        try:
            tested[f"{float(bl.get('price')):.{dec}f}"] = int(bl.get("times_tested") or 0)
        except (TypeError, ValueError):
            continue
    levels = []
    for lv in live["levels"]:
        row = dict(lv)
        row["times_tested"] = tested.get(row["price_str"], 0)
        levels.append(row)
    levels.sort(key=lambda x: x["price"], reverse=True)
    poc = vah = val = None
    poc_str = vah_str = val_str = None
    if levels:
        poc_lev = max(levels, key=lambda x: x["total_volume"])
        poc, poc_str = poc_lev["price"], poc_lev["price_str"]
        total_vol = sum(x["total_volume"] for x in levels) or 1
        target_vol = total_vol * 0.70
        asc = sorted(levels, key=lambda x: x["price"])
        idx = next(i for i, x in enumerate(asc) if x["price"] == poc)
        lo_i = hi_i = idx
        acc = asc[idx]["total_volume"]
        while acc < target_vol and (lo_i > 0 or hi_i < len(asc) - 1):
            left = asc[lo_i - 1]["total_volume"] if lo_i > 0 else -1
            right = asc[hi_i + 1]["total_volume"] if hi_i < len(asc) - 1 else -1
            if right >= left:
                hi_i += 1
                acc += asc[hi_i]["total_volume"]
            else:
                lo_i -= 1
                acc += asc[lo_i]["total_volume"]
        val, val_str = asc[lo_i]["price"], asc[lo_i]["price_str"]
        vah, vah_str = asc[hi_i]["price"], asc[hi_i]["price_str"]
    buy_t = int(sum(int(x.get("buy_volume") or 0) for x in levels))
    sell_t = int(sum(int(x.get("sell_volume") or 0) for x in levels))
    tot = buy_t + sell_t
    buy_dom = round(buy_t / tot * 100.0, 2) if tot > 0 else None
    day_high = max(x["price"] for x in levels) if levels else None
    day_low = min(x["price"] for x in levels) if levels else None
    return {
        "symbol": sym,
        "date": datetime.now(IST).date().isoformat(),
        "label": "Günlük footprint",
        "levels": levels,
        "level_count": len(levels),
        "buy_volume_total": buy_t,
        "sell_volume_total": sell_t,
        "net_volume_total": buy_t - sell_t,
        "buy_vol": buy_t,
        "sell_vol": sell_t,
        "net_vol": buy_t - sell_t,
        "buy_dominance_pct": buy_dom,
        "sell_dominance_pct": round(100.0 - buy_dom, 2) if buy_dom is not None else None,
        "poc": poc,
        "poc_str": poc_str,
        "vah": vah,
        "vah_str": vah_str,
        "val": val,
        "val_str": val_str,
        "tick": tick,
        "tick_decimals": dec,
        "day_high": day_high,
        "day_high_str": f"{day_high:.{dec}f}" if day_high is not None else None,
        "day_low": day_low,
        "day_low_str": f"{day_low:.{dec}f}" if day_low is not None else None,
        "source_tf": "İdealData",
        "bar_count": base.get("bar_count") or 0,
        "method": LIVE_FP_METHOD,
        "value_area_pct": 70,
        "fallback_note": None,
        "fp_source": "idealdata",
        "fp_source_label": "İdealData canlı",
        "live_age_sec": live.get("age_sec"),
        "ohlcv_buy_vol": base.get("buy_vol"),
        "ohlcv_sell_vol": base.get("sell_vol"),
    }


def compute_volume_profile(
    symbol: str,
    date_str: str | None = "today",
    force: bool = False,
) -> dict[str, Any]:
    """Daily footprint. v1.16.0: live İdealData Y38 (real buy/sell per price) when
    available for today's session; otherwise the OHLCV approximation (tahmini)."""
    base = _compute_volume_profile_ohlcv(symbol, date_str=date_str, force=force)
    sym = symbol.upper().replace(".IS", "")
    try:
        ds = (date_str or "today").lower()
        if ds in ("today", datetime.now(IST).date().isoformat()):
            from app.ideal_feed import ideal_feed

            live = ideal_feed.footprint(sym)
            if live and live.get("levels"):
                return _merge_live_footprint(base, live, sym)
    except Exception as e:  # never break the OHLCV fallback
        logger.debug("live footprint %s: %s", sym, e)
    if isinstance(base, dict) and "fp_source" not in base:
        base = dict(base)
        base["fp_source"] = "tahmini"
        base["fp_source_label"] = "tahmini (OHLCV)"
    return base


def _compute_volume_profile_ohlcv(
    symbol: str,
    date_str: str | None = "today",
    force: bool = False,
) -> dict[str, Any]:
    """Daily-session footprint / volume-at-price from 1m (fallback 5m) bars."""
    sym = symbol.upper().replace(".IS", "")
    cache_key = f"{sym}:{(date_str or 'today').lower()}"
    if not force:
        with _vp_lock:
            hit = _vp_cache.get(cache_key)
            if hit and (time.time() - hit[0]) < _VP_CACHE_TTL:
                return hit[1]
    yahoo = f"{sym}.IS"
    target = _parse_session_date(date_str)
    fallback_note: str | None = None

    bars_1m = fetch_bars(yahoo, "1m", force=force) or []
    day_bars = [b for b in bars_1m if _bar_session_date(b) == target]
    src_tf = "1m"

    if len(day_bars) < 3:
        bars_5m = fetch_bars(yahoo, "5m", force=force) or []
        day_5 = [b for b in bars_5m if _bar_session_date(b) == target]
        if len(day_5) > len(day_bars):
            day_bars = day_5
            src_tf = "5m"
            fallback_note = "1m veri yok/yetersiz — 5m barlar kullanıldı."

    # Last available session if target empty (weekend / holiday / closed)
    if not day_bars:
        candidates: list[tuple[str, list[dict]]] = []
        b1 = bars_1m or fetch_bars(yahoo, "1m", force=False) or []
        b5 = fetch_bars(yahoo, "5m", force=False) or []
        dates = sorted(
            {
                d
                for d in (_bar_session_date(b) for b in (b1 + b5))
                if d is not None
            },
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
                fallback_note = "1m veri yok/yetersiz — 5m barlar kullanıldı."
            elif d1:
                day_bars, src_tf = d1, "1m"

    empty = {
        "symbol": sym,
        "date": target.isoformat(),
        "label": "Günlük footprint",
        "levels": [],
        "level_count": 0,
        "poc": None,
        "vah": None,
        "val": None,
        "tick": None,
        "day_high": None,
        "day_low": None,
        "source_tf": src_tf,
        "bar_count": len(day_bars),
        "method": VP_METHOD,
        "value_area_pct": 70,
        "fallback_note": fallback_note,
        "buy_volume_total": 0,
        "sell_volume_total": 0,
        "net_volume_total": 0,
        "buy_vol": 0,
        "sell_vol": 0,
        "net_vol": 0,
    }

    if not day_bars:
        empty["error"] = "no_intraday_bars"
        with _vp_lock:
            _vp_cache[cache_key] = (time.time(), empty)
        return empty

    highs = [float(b["high"]) for b in day_bars if b.get("high") is not None]
    lows = [float(b["low"]) for b in day_bars if b.get("low") is not None]
    if not highs or not lows:
        empty["error"] = "no_hl"
        empty["bar_count"] = len(day_bars)
        with _vp_lock:
            _vp_cache[cache_key] = (time.time(), empty)
        return empty

    raw_high = max(highs)
    raw_low = min(lows)
    mid = (raw_high + raw_low) / 2.0
    tick = _tick_size(mid)
    dec = _tick_decimals(tick)

    # Nearest-tick indices (Yahoo float noise must not add phantom ticks)
    lo_idx = _idx_from_price(raw_low, tick)
    hi_idx = _idx_from_price(raw_high, tick)
    if hi_idx < lo_idx:
        lo_idx, hi_idx = hi_idx, lo_idx

    n_est = hi_idx - lo_idx + 1
    if n_est > 5000:
        # Coarsen tick to keep profile manageable
        span = max(raw_high - raw_low, tick)
        tick = max(_tick_size(mid), round(span / 4000.0, 4) or 0.01)
        tick = max(0.01, round(tick / 0.01) * 0.01)
        dec = _tick_decimals(tick)
        lo_idx = _idx_from_price(raw_low, tick)
        hi_idx = _idx_from_price(raw_high, tick)
        if hi_idx < lo_idx:
            lo_idx, hi_idx = hi_idx, lo_idx

    day_low = _price_from_idx(lo_idx, tick)
    day_high = _price_from_idx(hi_idx, tick)

    # Integer tick index → accumulators
    buy_map: dict[int, float] = {i: 0.0 for i in range(lo_idx, hi_idx + 1)}
    sell_map: dict[int, float] = {i: 0.0 for i in range(lo_idx, hi_idx + 1)}
    test_map: dict[int, int] = {i: 0 for i in range(lo_idx, hi_idx + 1)}

    for bar in day_bars:
        o = bar.get("open")
        h = bar.get("high")
        l = bar.get("low")
        c = bar.get("close")
        v = float(bar.get("volume") or 0)
        if h is None or l is None or c is None:
            continue
        h = float(h)
        l = float(l)
        c = float(c)
        o = float(o) if o is not None else c
        if h < l:
            h, l = l, h

        i0 = _idx_from_price(l, tick)
        i1 = _idx_from_price(h, tick)
        if i1 < i0:
            i0, i1 = i1, i0
        # Clamp to session range keys (and extend map if needed)
        touched = list(range(i0, i1 + 1))
        if not touched:
            touched = [_idx_from_price(c, tick)]

        for idx in touched:
            if idx not in test_map:
                test_map[idx] = 0
                buy_map[idx] = 0.0
                sell_map[idx] = 0.0
            test_map[idx] += 1

        if v <= 0 or not touched:
            continue

        buy_frac, sell_frac = _bar_buy_sell_frac(o, h, l, c)

        share = v / len(touched)
        buy_share = share * buy_frac
        sell_share = share * sell_frac
        for idx in touched:
            buy_map[idx] += buy_share
            sell_map[idx] += sell_share

    levels: list[dict[str, Any]] = []
    for idx in sorted(test_map.keys(), reverse=True):  # high → low
        price = _price_from_idx(idx, tick)
        buy_v = int(round(buy_map.get(idx, 0.0)))
        sell_v = int(round(sell_map.get(idx, 0.0)))
        total = buy_v + sell_v
        levels.append(
            {
                "tick_index": idx,
                "price": price,
                "price_str": f"{price:.{dec}f}",
                "times_tested": int(test_map.get(idx, 0)),
                "buy_volume": buy_v,
                "sell_volume": sell_v,
                "total_volume": total,
                "net_volume": buy_v - sell_v,
            }
        )

    poc = vah = val = None
    poc_str = vah_str = val_str = None
    if levels:
        poc_lev = max(levels, key=lambda x: x["total_volume"])
        poc = poc_lev["price"]
        poc_str = poc_lev["price_str"]
        total_vol = sum(x["total_volume"] for x in levels) or 1
        target_vol = total_vol * 0.70
        # levels are high→low; rebuild ascending for VA expand
        asc = sorted(levels, key=lambda x: x["tick_index"])
        idx = next(i for i, x in enumerate(asc) if x["tick_index"] == poc_lev["tick_index"])
        lo_i = hi_i = idx
        acc = asc[idx]["total_volume"]
        while acc < target_vol and (lo_i > 0 or hi_i < len(asc) - 1):
            left = asc[lo_i - 1]["total_volume"] if lo_i > 0 else -1
            right = asc[hi_i + 1]["total_volume"] if hi_i < len(asc) - 1 else -1
            if right >= left:
                hi_i += 1
                acc += asc[hi_i]["total_volume"]
            else:
                lo_i -= 1
                acc += asc[lo_i]["total_volume"]
        val = asc[lo_i]["price"]
        vah = asc[hi_i]["price"]
        val_str = asc[lo_i]["price_str"]
        vah_str = asc[hi_i]["price_str"]

    buy_volume_total = int(sum(int(x.get("buy_volume") or 0) for x in levels))
    sell_volume_total = int(sum(int(x.get("sell_volume") or 0) for x in levels))
    _tot = buy_volume_total + sell_volume_total
    buy_dominance_pct = round(buy_volume_total / _tot * 100.0, 2) if _tot > 0 else None
    sell_dominance_pct = (
        round(100.0 - buy_dominance_pct, 2) if buy_dominance_pct is not None else None
    )

    result = {
        "symbol": sym,
        "date": target.isoformat(),
        "label": "Günlük footprint",
        "levels": levels,
        "level_count": len(levels),
        "buy_volume_total": buy_volume_total,
        "sell_volume_total": sell_volume_total,
        "net_volume_total": buy_volume_total - sell_volume_total,
        "buy_vol": buy_volume_total,  # alias (scanner / Hisse bilgisi)
        "sell_vol": sell_volume_total,
        "net_vol": buy_volume_total - sell_volume_total,
        "buy_dominance_pct": buy_dominance_pct,
        "sell_dominance_pct": sell_dominance_pct,
        "poc": poc,
        "poc_str": poc_str,
        "vah": vah,
        "vah_str": vah_str,
        "val": val,
        "val_str": val_str,
        "tick": tick,
        "tick_decimals": dec,
        "day_high": day_high,
        "day_high_str": f"{day_high:.{dec}f}",
        "day_low": day_low,
        "day_low_str": f"{day_low:.{dec}f}",
        "source_tf": src_tf,
        "bar_count": len(day_bars),
        "method": VP_METHOD,
        "value_area_pct": 70,
        "fallback_note": fallback_note,
    }
    with _vp_lock:
        _vp_cache[cache_key] = (time.time(), result)
    return result


SIGNAL_RULES = (
    "AL-SAT-TUT model kuralları (yatırım tavsiyesi değildir): "
    "hakimiyet_alis% = footprint alış hacmi / (alış+satış) × 100; "
    "hakimiyet_satis% = 100 − alış. "
    "AL: alış hakimiyeti ≥ %55 VE günlük değişim > 0 VE (RVOL≥1.2 veya RVOL10≥1.2) "
    "VE çoklu TF yükseliş sayısı ≥ düşüş. "
    "Güçlü AL: alış ≥ %62 VE değişim > %+1 VE RVOL≥1.5. "
    "SAT: satış hakimiyeti ≥ %55 VE değişim < 0 VE (RVOL≥1.2 veya RVOL10≥1.2 veya değişim≤−2) "
    "VE TF düşüş ≥ yükseliş. "
    "Güçlü SAT: satış ≥ %62 VE değişim < %−1 VE RVOL≥1.5. "
    "TUT: karışık / eşik altı. Footprint yoksa hakimiyet atlanır, yalnızca fiyat+RVOL+TF."
)


def _tf_bias_counts(change_pct_tf: dict[str, float | None] | None) -> tuple[int, int, int]:
    up = down = flat = 0
    for tf in TF_INTERVALS:
        c = (change_pct_tf or {}).get(tf)
        if c is None:
            continue
        if c > 0.05:
            up += 1
        elif c < -0.05:
            down += 1
        else:
            flat += 1
    return up, down, flat


def _day_range_pos(quote: dict[str, Any]) -> dict[str, float | None]:
    price = quote.get("price")
    day_high = quote.get("day_high")
    day_low = quote.get("day_low")
    if price is None or day_high is None or day_low is None or day_high <= day_low:
        return {"from_low_pct": None, "from_high_pct": None, "span": None}
    span = day_high - day_low
    return {
        "from_low_pct": (price - day_low) / span * 100.0,
        "from_high_pct": (day_high - price) / span * 100.0,
        "span": span,
    }


def build_signal(
    symbol: str,
    force: bool = False,
    include_footprint: bool = True,
) -> dict[str, Any]:
    """AL / SAT / TUT verdict + Turkish multi-paragraph commentary."""
    from app.scanners import scanner_service

    sym = symbol.upper().replace(".IS", "")
    quote = quote_service.fetch_one(symbol)
    if not quote:
        cached = quote_service._cache or []
        quote = next((q for q in cached if q["symbol"] == sym), None)
    if not quote:
        return {"symbol": sym, "verdict": None, "error": "not_found"}

    rvol_tf = None
    change_pct_tf = None
    try:
        data = scanner_service.stock_rvol_tf(symbol, force=force)
        rvol_tf = data.get("rvol_tf")
        change_pct_tf = data.get("change_pct_tf")
    except Exception as e:
        logger.warning("signal rvol_tf %s: %s", symbol, e)

    buy_total = sell_total = None
    buy_dom = sell_dom = None
    fp_meta: dict[str, Any] = {}
    if include_footprint:
        try:
            vp = compute_volume_profile(symbol, date_str="today", force=force)
            levels = vp.get("levels") or []
            buy_total = int(sum(int(l.get("buy_volume") or 0) for l in levels))
            sell_total = int(sum(int(l.get("sell_volume") or 0) for l in levels))
            tot = buy_total + sell_total
            if tot > 0:
                buy_dom = round(buy_total / tot * 100.0, 2)
                sell_dom = round(100.0 - buy_dom, 2)
            fp_meta = {
                "date": vp.get("date"),
                "source_tf": vp.get("source_tf"),
                "bar_count": vp.get("bar_count"),
                "poc": vp.get("poc"),
                "poc_str": vp.get("poc_str"),
                "fallback_note": vp.get("fallback_note"),
                "error": vp.get("error"),
            }
        except Exception as e:
            logger.warning("signal footprint %s: %s", symbol, e)
            fp_meta = {"error": str(e)}

    chg = quote.get("change_pct")
    rvol = quote.get("rvol")
    rvol10 = quote.get("rvol10")
    up, down, flat = _tf_bias_counts(change_pct_tf)
    range_pos = _day_range_pos(quote)

    # --- Verdict ---
    reasons: list[str] = []
    strength = "normal"
    verdict = "TUT"

    vol_hot = (rvol is not None and rvol >= 1.2) or (rvol10 is not None and rvol10 >= 1.2)
    vol_very_hot = (rvol is not None and rvol >= 1.5) or (rvol10 is not None and rvol10 >= 1.5)
    tf_up_bias = up >= down and (up + down + flat) >= 3
    tf_down_bias = down >= up and (up + down + flat) >= 3
    has_fp = buy_dom is not None

    # Strong AL
    if (
        has_fp
        and buy_dom >= 62
        and chg is not None
        and chg > 1.0
        and vol_very_hot
    ):
        verdict = "AL"
        strength = "guclu"
        reasons.append("Güçlü alış hakimiyeti + pozitif gün + yüksek RVOL")
    # Strong SAT
    elif (
        has_fp
        and sell_dom is not None
        and sell_dom >= 62
        and chg is not None
        and chg < -1.0
        and vol_very_hot
    ):
        verdict = "SAT"
        strength = "guclu"
        reasons.append("Güçlü satış hakimiyeti + negatif gün + yüksek RVOL")
    # Standard AL
    elif (
        has_fp
        and buy_dom >= 55
        and chg is not None
        and chg > 0
        and vol_hot
        and (tf_up_bias or (up + down + flat) < 3)
    ):
        verdict = "AL"
        reasons.append("Alış hakimiyeti ≥%55, gün pozitif, RVOL sıcak, TF uyumlu/yeterli")
    # Standard SAT
    elif (
        has_fp
        and sell_dom is not None
        and sell_dom >= 55
        and chg is not None
        and chg < 0
        and (vol_hot or (chg is not None and chg <= -2.0))
        and (tf_down_bias or (up + down + flat) < 3)
    ):
        verdict = "SAT"
        reasons.append("Satış hakimiyeti ≥%55, gün negatif, hacim/düşüş eşiği, TF uyumlu")
    # No footprint fallback: price + RVOL + TF only
    elif not has_fp:
        if (
            chg is not None
            and chg > 1.0
            and vol_hot
            and tf_up_bias
        ):
            verdict = "AL"
            strength = "zayif"
            reasons.append("Footprint yok; fiyat+RVOL+TF yükseliş (zayıf sinyal)")
        elif (
            chg is not None
            and chg < -1.0
            and (vol_hot or chg <= -2.0)
            and tf_down_bias
        ):
            verdict = "SAT"
            strength = "zayif"
            reasons.append("Footprint yok; fiyat+RVOL+TF düşüş (zayıf sinyal)")
        else:
            reasons.append("Footprint yok veya eşikler tutmadı → TUT")
    else:
        reasons.append("Metrikler karışık / eşik altı → TUT")

    # --- Commentary (Turkish, factual, disclaimer) ---
    paragraphs: list[str] = []
    bullets: list[str] = []

    # Dominance
    if has_fp:
        paragraphs.append(
            f"Günlük footprint üzerinde alış hacmi {_fmt_vol(buy_total)}, "
            f"satış {_fmt_vol(sell_total)}. "
            f"Alış hakimiyeti %{buy_dom:.1f}, satış hakimiyeti %{sell_dom:.1f}."
        )
        if buy_dom >= 55:
            bullets.append(f"Footprint alış tarafı baskın (%{buy_dom:.1f}).")
        elif sell_dom is not None and sell_dom >= 55:
            bullets.append(f"Footprint satış tarafı baskın (%{sell_dom:.1f}).")
        else:
            bullets.append(f"Footprint dengeli (alış %{buy_dom:.1f} / satış %{sell_dom:.1f}).")
    else:
        paragraphs.append(
            "Günlük footprint verisi yok veya yetersiz; hakimiyet hesaplanamadı."
        )

    # Day change + range
    if chg is not None:
        paragraphs.append(f"Seans değişimi {_fmt_pct(chg)}.")
        bullets.append(f"Günlük değişim {_fmt_pct(chg)}.")
    fl = range_pos.get("from_low_pct")
    fh = range_pos.get("from_high_pct")
    if fl is not None and fh is not None:
        paragraphs.append(
            f"Fiyat gün aralığında: düşükten %{fl:.0f}, yüksekten %{fh:.0f} "
            f"(L {_fmt_num(quote.get('day_low'))} / H {_fmt_num(quote.get('day_high'))})."
        )
        if fl >= 70:
            bullets.append("Fiyat gün aralığının üst bölgesinde.")
        elif fl <= 30:
            bullets.append("Fiyat gün aralığının alt bölgesinde.")

    # RVOL
    rvol_parts = []
    if rvol is not None:
        rvol_parts.append(f"RVOL {rvol:.2f}× (önceki seans)")
    if rvol10 is not None:
        rvol_parts.append(f"RVOL(10) {rvol10:.2f}×")
    if rvol_parts:
        paragraphs.append("; ".join(rvol_parts) + ".")
        if vol_very_hot:
            bullets.append("Hacim önceki ortalamaya göre belirgin yüksek (RVOL≥1.5).")
        elif vol_hot:
            bullets.append("Hacim görece sıcak (RVOL≥1.2).")
        else:
            bullets.append("Hacim görece normal / düşük RVOL.")

    # Multi-TF
    total_tf = up + down + flat
    if total_tf >= 3:
        if up > down and up >= total_tf * 0.55:
            bias_txt = "çoklu TF yükseliş eğilimi"
        elif down > up and down >= total_tf * 0.55:
            bias_txt = "çoklu TF düşüş eğilimi"
        else:
            bias_txt = "çoklu TF karışık"
        paragraphs.append(
            f"Son mum yönleri: {up}↑ / {down}↓ / {flat}→ — {bias_txt}."
        )
        bullets.append(f"TF bias: {up}↑ {down}↓ {flat}→ ({bias_txt}).")

    # Verdict line
    vlabel = {"AL": "AL", "SAT": "SAT", "TUT": "TUT"}.get(verdict, verdict)
    strength_tr = {"guclu": "güçlü", "zayif": "zayıf", "normal": ""}.get(strength, "")
    paragraphs.append(
        f"Model sonucu: {vlabel}"
        + (f" ({strength_tr})" if strength_tr else "")
        + ". " + "; ".join(reasons) + "."
    )
    paragraphs.append(
        "Bu metin otomatik model yorumudur; yatırım tavsiyesi değildir."
    )

    notes = generate_notes(quote, rvol_tf=rvol_tf, change_pct_tf=change_pct_tf)

    return {
        "symbol": quote["symbol"],
        "name": quote.get("name"),
        "verdict": verdict,
        "strength": strength,
        "reasons": reasons,
        "buy_volume_total": buy_total,
        "sell_volume_total": sell_total,
        "net_volume_total": (int(buy_total) - int(sell_total))
            if buy_total is not None and sell_total is not None else None,
        "buy_vol": buy_total,  # alias → Hisse bilgisi cards
        "sell_vol": sell_total,
        "net_vol": (int(buy_total) - int(sell_total))
            if buy_total is not None and sell_total is not None else None,
        "buy_dominance_pct": buy_dom,
        "sell_dominance_pct": sell_dom,
        "change_pct": chg,
        "rvol": rvol,
        "rvol10": rvol10,
        "tf_bias": {"up": up, "down": down, "flat": flat},
        "day_range": range_pos,
        "footprint": fp_meta,
        "rvol_tf": rvol_tf,
        "change_pct_tf": change_pct_tf,
        "analysis": paragraphs,
        "bullets": bullets,
        "notes": notes,
        "rules": SIGNAL_RULES,
        "disclaimer": "Model yorumu / yatırım tavsiyesi değildir.",
        "stock": {
            "price": quote.get("price"),
            "change_pct": chg,
            "rvol": rvol,
            "rvol10": rvol10,
            "day_high": quote.get("day_high"),
            "day_low": quote.get("day_low"),
            "volume": quote.get("volume"),
            "prev_volume": quote.get("prev_volume"),
        },
    }
