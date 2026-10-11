"""BIST equity symbol universe: merge KAP / GitHub / Wikipedia / seed, cache to disk."""
from __future__ import annotations

import csv
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_PATH = DATA_DIR / "symbols.json"
SEED_CSV = DATA_DIR / "bist_seed.csv"

GITHUB_CSV_URL = (
    "https://raw.githubusercontent.com/ahmeterenodaci/"
    "Istanbul-Stock-Exchange--BIST--including-symbols-and-logos/main/bist.csv"
)
KAP_IGS_URL = "https://www.kap.org.tr/tr/api/company/items/IGS/A"
WIKI_URL = "https://en.wikipedia.org/wiki/List_of_companies_listed_on_the_Borsa_Istanbul"

CACHE_MAX_AGE_SEC = 24 * 3600

# BIST equity tickers: 2–8 alphanumeric (e.g. THYAO, A1CAP, DOCO)
_SYM_RE = re.compile(r"^[A-Z0-9]{2,8}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_symbol(raw: str) -> str | None:
    sym = (raw or "").strip().upper().replace(".IS", "")
    if not sym or not _SYM_RE.fullmatch(sym):
        return None
    return sym


def _primary_from_kap_stock_code(stock_code: str) -> str | None:
    """KAP sometimes returns 'A1CAP, ACP' — prefer the main equity code."""
    parts = [
        p.strip().upper()
        for p in re.split(r"[,;/]+", (stock_code or "").strip())
        if p.strip()
    ]
    parts = [p for p in parts if _SYM_RE.fullmatch(p)]
    if not parts:
        return None
    five = [p for p in parts if len(p) == 5]
    if five:
        return five[0]
    if len(parts) > 1 and len(parts[0]) < 4 and len(parts[1]) >= 4:
        return parts[1]
    return parts[0]


def _merge_into(dest: dict[str, dict], symbol: str, name: str, source: str) -> None:
    sym = _clean_symbol(symbol)
    if not sym:
        return
    name = (name or "").strip()
    existing = dest.get(sym)
    if existing is None:
        dest[sym] = {"symbol": sym, "name": name, "yahoo": f"{sym}.IS", "sources": [source]}
        return
    if name and (not existing.get("name") or len(name) > len(existing["name"])):
        existing["name"] = name
    if source not in existing["sources"]:
        existing["sources"].append(source)


def _parse_csv_text(text: str, source: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    reader = csv.DictReader(text.splitlines())
    for row in reader:
        sym = row.get("symbol") or row.get("Symbol") or ""
        name = row.get("name") or row.get("Name") or ""
        _merge_into(out, sym, name, source)
    return out


def _load_seed() -> dict[str, dict]:
    if not SEED_CSV.exists():
        return {}
    return _parse_csv_text(SEED_CSV.read_text(encoding="utf-8"), "seed")


def fetch_kap_symbols(client: httpx.Client) -> dict[str, dict]:
    r = client.get(
        KAP_IGS_URL,
        headers={
            "Accept": "application/json",
            "Referer": "https://www.kap.org.tr/tr/bist-sirketler",
        },
    )
    r.raise_for_status()
    data = r.json()
    out: dict[str, dict] = {}
    if not isinstance(data, list):
        return out
    for row in data:
        code = _primary_from_kap_stock_code(row.get("stockCode") or "")
        title = (row.get("kapMemberTitle") or "").strip()
        if code:
            _merge_into(out, code, title, "kap")
    return out


def fetch_github_symbols(client: httpx.Client) -> dict[str, dict]:
    r = client.get(GITHUB_CSV_URL)
    r.raise_for_status()
    return _parse_csv_text(r.text, "github")


def fetch_wikipedia_symbols(client: httpx.Client) -> dict[str, dict]:
    """Best-effort scrape of EN Wikipedia BIST company list (ticker cells)."""
    out: dict[str, dict] = {}
    html = ""
    try:
        r = client.get(WIKI_URL)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        logger.warning("Wikipedia via httpx failed: %s — trying curl_cffi", e)
        try:
            from curl_cffi import requests as creq

            s = creq.Session(impersonate="chrome")
            r = s.get(WIKI_URL, timeout=30)
            r.raise_for_status()
            html = r.text
        except Exception as e2:
            logger.warning("Wikipedia fetch failed: %s", e2)
            return out

    for m in re.finditer(r"<td[^>]*>\s*([A-Z][A-Z0-9]{1,7})\s*</td>", html):
        _merge_into(out, m.group(1), "", "wikipedia")
    return out


def save_cache(symbols: list[dict], meta: dict | None = None) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Strip internal 'sources' from public cache entries but keep in meta summary
    clean = [
        {"symbol": s["symbol"], "name": s.get("name") or "", "yahoo": s["yahoo"]}
        for s in symbols
    ]
    payload = {
        "updated_at": _now_iso(),
        "count": len(clean),
        "meta": meta or {},
        "symbols": clean,
    }
    CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cache() -> tuple[list[dict], str | None, dict]:
    if not CACHE_PATH.exists():
        return [], None, {}
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return data.get("symbols") or [], data.get("updated_at"), data.get("meta") or {}
    except Exception as e:
        logger.warning("Symbol cache unreadable: %s", e)
        return [], None, {}


def _cache_age_sec(updated_at: str | None) -> float | None:
    if not updated_at:
        return None
    try:
        ts = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - ts).total_seconds()
    except Exception:
        return None


def build_universe(timeout: float = 45.0) -> tuple[list[dict], dict]:
    """Merge KAP + GitHub + Wikipedia + seed; return (symbols, meta)."""
    merged: dict[str, dict] = {}
    source_counts: dict[str, int] = {}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; BIST-Analiz/1.1)"}

    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        for name, fetcher in (
            ("kap", fetch_kap_symbols),
            ("github", fetch_github_symbols),
            ("wikipedia", fetch_wikipedia_symbols),
        ):
            try:
                part = fetcher(client)
                source_counts[name] = len(part)
                for sym, item in part.items():
                    _merge_into(merged, sym, item.get("name") or "", name)
                logger.info("Symbol source %s: %d", name, len(part))
            except Exception as e:
                source_counts[name] = 0
                logger.warning("Symbol source %s failed: %s", name, e)

    seed = _load_seed()
    source_counts["seed"] = len(seed)
    for sym, item in seed.items():
        _merge_into(merged, sym, item.get("name") or "", "seed")

    symbols = sorted(merged.values(), key=lambda x: x["symbol"])
    # Drop internal sources list from returned items (kept only for meta)
    meta = {
        "sources": source_counts,
        "note": (
            "Universe = deduped BIST equity codes (.IS). "
            "Primary source KAP IGS company list; merged with GitHub CSV, Wikipedia, seed. "
            "ETFs/funds with non-ticker symbols are skipped. "
            "Yahoo may not quote every KAP member (e.g. unlisted brokerages)."
        ),
    }
    return [
        {"symbol": s["symbol"], "name": s.get("name") or "", "yahoo": s["yahoo"]}
        for s in symbols
    ], meta


def get_symbols(force_refresh: bool = False) -> list[dict]:
    """Return BIST symbol list, refreshing from remote sources when needed."""
    cached, updated_at, _meta = load_cache()
    age = _cache_age_sec(updated_at)

    if not force_refresh and cached and age is not None and age < CACHE_MAX_AGE_SEC:
        return cached

    try:
        symbols, meta = build_universe()
        if symbols:
            save_cache(symbols, meta)
            logger.info(
                "Built BIST universe: %d symbols (sources=%s)",
                len(symbols),
                meta.get("sources"),
            )
            return symbols
    except Exception as e:
        logger.warning("Universe build failed: %s", e)

    if cached:
        return cached

    seed_list = list(_load_seed().values())
    if seed_list:
        save_cache(seed_list, {"sources": {"seed": len(seed_list)}})
        logger.info("Loaded %d BIST symbols from seed CSV", len(seed_list))
        return seed_list

    fallback = [
        {"symbol": s, "name": "", "yahoo": f"{s}.IS"}
        for s in ["THYAO", "GARAN", "AKBNK", "EREGL", "ASELS", "SISE", "BIMAS", "TCELL"]
    ]
    save_cache(fallback, {"sources": {"fallback": len(fallback)}})
    return fallback
