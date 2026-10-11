"""Hisselerin Endekse Etkisi (v1.19.0) — tüm BIST endeksleri.

Kaynaklar
---------
* İdealData ``REQ_ENDEKS_KAPSAM`` → ``SRV_ENDEKS_KAPSAM``: endeks bileşenleri + gerçek ağırlık (%)
  (İdealData'nın yayınladığı ~75 pay endeksi; tümü Borsa İstanbul listesiyle birebir doğrulandı).
* Borsa İstanbul günlük bileşen dosyası ``hisse_endeks_ds.csv``: resmi endeks → pay üyelik listesi
  (İdealData'da olmayan XSD25, XKTMT, XTM25S, XSINS, XGYOS, XT05Y, XT10Y, XTTIC, XPTIC, XKNKL,
  XYIHZ, XGSYO için bileşen kaynağı). Bu endekslerin ağırlıkları **tahminidir**: İdealData BIST TÜM
  (XUTUM) ağırlıkları (= fiili dolaşımdaki piyasa değeri payı) endeks içinde yeniden normalize edilir,
  ağırlık sınırlamalı endekslerde Borsa İstanbul'un sınırlama oranı (%10 / %20) uygulanır.
* Endeks seviyesi: İdealData canlı kotasyon; İdealData'da olmayan endeksler için Oyak Yatırım
  "BİST Endeksleri" tablosu (gecikmeli olabilir) → önceki kapanış = son / (1 + günlük %).

Puan etkisi  = Endeks önceki kapanış × ağırlık × hisse günlük getirisi
Endeks % etkisi = ağırlık × hisse getirisi (endeksin % değişimine katkı, yüzde puan)
"""
from __future__ import annotations

import csv
import html as _html
import io
import logging
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None

logger = logging.getLogger("bist.index")
IST = ZoneInfo("Europe/Istanbul")
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "index"
BIST_CSV_URL = "https://www.borsaistanbul.com/datum/hisse_endeks_ds.csv"
BIST_CSV_FILE = DATA_DIR / "hisse_endeks_ds.csv"
OYAK_URL = "https://www.oyakyatirim.com.tr/bist-endeksleri"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}
S1 = "\x02"

KAPSAM_TTL = 30 * 60          # İdealData ağırlıkları önceki kapanış bazlı; gün içinde değişmez
CSV_TTL = 6 * 3600
OYAK_TTL = 120
# Non-equity / undocumented İdealData codes (faiz, fon, bileşen ağırlığı yayınlanmayanlar)
EXCLUDE = {"TLREF", "TLREFK", "ZPYTI", "ZREBD", "GBNIE", "ISKDN"}
# Borsa İstanbul endeks sayfalarındaki "Kıymetlere Uygulanan Ağırlık Sınırlaması (%)"
CAPS = {"XSD25": 10.0, "XTM25S": 10.0, "XKTMT": 10.0, "XSINS": 20.0, "XGYOS": 20.0}

GOSTERGE = ["XU100", "XU030", "XU050", "XU500", "XUTUM", "XTUMY", "XYUZO", "XELOT", "XELOS", "XELOC",
            "X030S", "X030C", "X100S", "X100C", "X030EA", "XLBNK", "X10XB", "XYLDZ", "XBANA"]
TEMATIK = ["XHARZ", "XKOBI", "XTMTU", "XTM25", "XTM25S", "XT05Y", "XT10Y", "XKURY", "XUSRD", "XSD25", "XUGRA", "ISIST"]
SEHIR = ["XSADA", "XSANK", "XSANT", "XSAYD", "XSBAL", "XSBUR", "XSDNZ", "XSIST", "XSIZM", "XSKAY", "XSKOC",
         "XSKON", "XSMNS", "XSTKR"]
GROUP_ORDER = ["Gösterge", "Sektör", "Katılım", "Tematik", "Şehir"]
EXTRA_NAMES = {"XKTUM": "BIST KATILIM TUM", "XK030": "BIST KATILIM 30", "XK050": "BIST KATILIM 50",
               "XK100": "BIST KATILIM 100", "XK030EA": "BIST KATILIM 30 ESIT AGIRLIKLI GETIRI",
               "XSRDK": "BIST KATILIM SURDURULEBILIRLIK", "XAKUR": "BIST ARACI KURUMLAR",
               "XUGRA": "BIST GERI ALIM", "ISIST": "IS BANKASI ISTIRAKLERI"}


def _group(code: str) -> str:
    if code in GOSTERGE:
        return "Gösterge"
    if code.startswith("XK") and code not in ("XKAGT", "XKMYA", "XKOBI", "XKURY", "XKNKL") or code in ("XSRDK", "XKTMT"):
        return "Katılım"
    if code in TEMATIK:
        return "Tematik"
    if code in SEHIR:
        return "Şehir"
    return "Sektör"


def _num(s) -> float | None:
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(",", "") if s.rfind(".") > s.rfind(",") else s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def cap_weights(w: dict[str, float], cap: float) -> dict[str, float]:
    """Normalize to 100 and iteratively cap each weight at `cap` (excess redistributed pro-rata)."""
    tot = sum(w.values())
    if tot <= 0:
        return dict(w)
    w = {k: v * 100.0 / tot for k, v in w.items()}
    capped: set[str] = set()
    for _ in range(60):
        over = {k for k, v in w.items() if k not in capped and v > cap + 1e-9}
        if not over:
            break
        capped |= over
        free = {k: v for k, v in w.items() if k not in capped}
        fs = sum(free.values())
        room = 100.0 - cap * len(capped)
        if fs <= 0 or room <= 0:
            break
        w = {**{k: cap for k in capped}, **{k: v * room / fs for k, v in free.items()}}
    return w


class IndexImpact:
    def __init__(self, feed) -> None:
        self.feed = feed
        self._lock = threading.RLock()
        self._kapsam: dict[str, dict] = {}      # code -> {"ts", "rows": [(sym, w)], "ok": bool}
        self._bist: dict[str, dict] = {}        # code -> {"name", "members": [...], "date"}
        self._bist_ts = 0.0
        self._bist_date = None
        self._oyak: dict[str, dict] = {}
        self._oyak_ts = 0.0
        self._oyak_err = None
        self._started = False
        self._prefetch_done = False
        self._fetch_lock = threading.Lock()

    # ------------------------------------------------------------ lifecycle
    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._load_bist_file()
        threading.Thread(target=self._bg_loop, name="index-impact", daemon=True).start()

    def _bg_loop(self) -> None:
        while True:
            try:
                if time.time() - self._bist_ts > CSV_TTL or not self._bist:
                    self._refresh_bist_csv()
                if self.feed.connected and self.feed.logged_in:
                    self._prefetch_all()
            except Exception as e:  # pragma: no cover
                logger.debug("index bg: %s", e)
            time.sleep(60 if self._prefetch_done else 10)

    # --------------------------------------------------------- BIST CSV --
    def _parse_bist_csv(self, raw: bytes) -> dict[str, dict]:
        try:
            txt = raw.decode("utf-8")
        except UnicodeDecodeError:
            txt = raw.decode("cp1254", errors="replace")
        out: dict[str, dict] = {}
        for i, r in enumerate(csv.reader(io.StringIO(txt), delimiter=";")):
            if i < 2 or len(r) < 4:
                continue
            sym = r[0].split(".")[0].strip().upper()
            code = r[2].strip().upper()
            if not sym or not code:
                continue
            ent = out.setdefault(code, {"name": r[3].strip(), "members": [], "date": (r[5].strip() if len(r) > 5 else None)})
            ent["members"].append(sym)
        return out

    def _load_bist_file(self) -> None:
        try:
            if BIST_CSV_FILE.exists():
                d = self._parse_bist_csv(BIST_CSV_FILE.read_bytes())
                if len(d) > 20:
                    with self._lock:
                        self._bist = d
                        self._bist_ts = BIST_CSV_FILE.stat().st_mtime
                        self._bist_date = next(iter(d.values())).get("date")
        except Exception as e:
            logger.warning("BIST bileşen dosyası okunamadı: %s", e)

    def _refresh_bist_csv(self) -> None:
        if httpx is None:
            return
        try:
            r = httpx.get(BIST_CSV_URL, headers=UA, timeout=25, follow_redirects=True)
            r.raise_for_status()
            d = self._parse_bist_csv(r.content)
            if len(d) > 20:
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                BIST_CSV_FILE.write_bytes(r.content)
                with self._lock:
                    self._bist = d
                    self._bist_ts = time.time()
                    self._bist_date = next(iter(d.values())).get("date")
                logger.info("BIST endeks bileşenleri güncellendi: %d endeks (%s)", len(d), self._bist_date)
                return
        except Exception as e:
            logger.info("BIST bileşen dosyası indirilemedi: %s", e)
        self._bist_ts = time.time() - CSV_TTL + 900   # retry in 15 min

    # --------------------------------------------------------- İdealData --
    def ideal_codes(self) -> dict[str, str]:
        f = self.feed
        with f._lock:
            return {s: (f.names.get(s) or "") for s, m in f.markets.items()
                    if m == "IMKBX" and f.sym_types.get(s) == "4" and s not in EXCLUDE}

    def _fetch_kapsam(self, code: str) -> dict | None:
        import json
        f = self.feed
        frames = [["X", "REQ_ENDEKS_KAPSAM", f.user, f._session or "", code, ""]]
        tag = '"e":"%s"' % code

        def match(parts):
            return len(parts) > 4 and tag in parts[4]
        res = f.request_wait(frames, "SRV_ENDEKS_KAPSAM", match, need=1, timeout=6.0)
        if not res:
            return None
        try:
            j = json.loads(res[0][4])
        except Exception:
            return None
        rows = []
        for x in j.get("d") or []:
            s = str(x.get("s") or "").strip().upper()
            w = _num(x.get("w"))
            if s and w is not None:
                rows.append((s, w, _num(x.get("p"))))
        ok = sum(w for _, w, _ in rows) > 50
        ent = {"ts": time.time(), "rows": [r for r in rows if r[1] > 0] if ok else [], "ok": ok}
        with self._lock:
            self._kapsam[code] = ent
        return ent

    def kapsam(self, code: str, max_age: float = KAPSAM_TTL) -> dict | None:
        with self._lock:
            ent = self._kapsam.get(code)
        if ent and time.time() - ent["ts"] < max_age:
            return ent
        if not (self.feed.connected and self.feed.logged_in):
            return ent
        with self._fetch_lock:
            got = self._fetch_kapsam(code)
        return got or ent

    def _prefetch_all(self) -> None:
        codes = sorted(self.ideal_codes())
        if "XUTUM" in codes:
            codes.remove("XUTUM")
            codes.insert(0, "XUTUM")
        n = 0
        for c in codes:
            with self._lock:
                ent = self._kapsam.get(c)
            if ent and time.time() - ent["ts"] < KAPSAM_TTL:
                continue
            with self._fetch_lock:
                self._fetch_kapsam(c)
            n += 1
            time.sleep(0.35)
        if n:
            logger.info("İdealData endeks kapsamları yenilendi: %d endeks", n)
        self._prefetch_done = len(self._kapsam) >= max(1, len(codes) - 2)

    # ------------------------------------------------------------- Oyak --
    def _oyak_levels(self) -> dict[str, dict]:
        if time.time() - self._oyak_ts < OYAK_TTL or httpx is None:
            return self._oyak
        self._oyak_ts = time.time()
        try:
            r = httpx.get(OYAK_URL, headers=UA, timeout=15, follow_redirects=True)
            r.raise_for_status()
            out = {}
            for row in re.findall(r"<tr[^>]*>(.*?)</tr>", r.text, re.S):
                cells = [_html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                         for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
                if len(cells) >= 6 and re.fullmatch(r"X[A-Z0-9]{3,6}", cells[0] or ""):
                    last = _num(cells[2].replace(",", ""))
                    chg = _num(cells[5])
                    if last and chg is not None:
                        out[cells[0]] = {"last": last, "chg": chg, "prev": last / (1 + chg / 100.0),
                                         "name": cells[1], "ts": time.time()}
            if out:
                self._oyak = out
                self._oyak_err = None
        except Exception as e:
            self._oyak_err = str(e)[:120]
            logger.info("Oyak endeks tablosu alınamadı: %s", e)
        return self._oyak

    def _oyak_get(self) -> dict[str, dict]:
        """Cached Oyak levels; first call fetches synchronously, later refreshes run in background."""
        if not self._oyak:
            return self._oyak_levels()
        if time.time() - self._oyak_ts >= OYAK_TTL and not getattr(self, "_oyak_bg", False):
            self._oyak_bg = True

            def _bg():
                try:
                    self._oyak_levels()
                finally:
                    self._oyak_bg = False
            threading.Thread(target=_bg, daemon=True).start()
        return self._oyak

    # ---------------------------------------------------------- catalog --
    def _name(self, code: str, ideal_name: str = "") -> str:
        b = self._bist.get(code)
        return (b or {}).get("name") or ideal_name or EXTRA_NAMES.get(code) or code

    def _quote(self, sym: str) -> tuple[float | None, float | None]:
        q = self.feed.quotes.get(sym) or {}
        return q.get("last"), q.get("prev_close")

    def catalog(self) -> dict:
        ideal = self.ideal_codes()
        self._oyak_get()
        with self._lock:
            bist = dict(self._bist)
            kap = dict(self._kapsam)
        codes = set(ideal) | set(bist)
        items = []
        for c in codes:
            k = kap.get(c)
            if c in ideal and (k is None or k.get("ok")):
                src = "idealdata"
                cnt = len(k["rows"]) if k else len((bist.get(c) or {}).get("members") or []) or None
            elif c in bist:
                src = "tahmini"
                cnt = len(bist[c]["members"])
            else:
                src = "yok"
                cnt = 0
            last, prev = self._quote(c) if c in ideal else (None, None)
            lvl_src = "idealdata" if last else None
            if not last:
                o = self._oyak.get(c)
                if o:
                    last, prev, lvl_src = o["last"], o["prev"], "oyak"
            chg = (last / prev - 1) * 100 if last and prev else None
            items.append({"code": c, "name": self._name(c, ideal.get(c, "")), "group": _group(c), "source": src,
                          "count": cnt, "last": last, "prev": prev, "chg": round(chg, 3) if chg is not None else None,
                          "level_source": lvl_src})
        pri = {c: i for i, c in enumerate(GOSTERGE)}
        items.sort(key=lambda x: (GROUP_ORDER.index(x["group"]), pri.get(x["code"], 999), x["name"]))
        return {"count": len(items), "indices": items, "groups": GROUP_ORDER,
                "bist_list_date": self._bist_date, "ideal_ready": self._prefetch_done,
                "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")}

    # ---------------------------------------------------------- weights --
    def weights(self, code: str) -> dict:
        """{'rows': {sym: w%}, 'source': 'idealdata'|'tahmini'|'yok', 'note': str}"""
        ideal = self.ideal_codes()
        if code in ideal:
            k = self.kapsam(code)
            if k and k.get("ok") and k["rows"]:
                return {"rows": {s: w for s, w, _ in k["rows"]}, "source": "idealdata",
                        "ideal_pts": {s: p for s, _, p in k["rows"]}, "ts": k["ts"],
                        "note": "Ağırlıklar İdealData endeks kapsamından (gerçek)."}
        with self._lock:
            b = self._bist.get(code)
        if not b:
            return {"rows": {}, "source": "yok",
                    "note": "Bu endeks için ne İdealData ne de Borsa İstanbul bileşen/ağırlık listesi yayınlıyor."}
        base = self.kapsam("XUTUM")
        ut = {s: w for s, w, _ in (base or {}).get("rows") or []}
        mem = list(dict.fromkeys(b["members"]))
        est = {s: ut[s] for s in mem if ut.get(s)}
        missing = [s for s in mem if s not in est]
        if est and missing:   # en küçük ağırlığın yarısı ile temsil et (XUTUM'da olmayan pay)
            mn = min(est.values()) / 2.0
            for s in missing:
                est[s] = mn
        elif not est:
            est = {s: 1.0 for s in mem}
        cap = CAPS.get(code)
        est = cap_weights(est, cap) if cap else cap_weights(est, 100.0)
        note = ("TAHMİNİ ağırlık: bileşenler Borsa İstanbul resmi listesinden ({d}); ağırlıklar İdealData BIST TÜM "
                "(fiili dolaşım piyasa değeri) ağırlıklarının endeks içinde yeniden ölçeklenmesiyle{c} hesaplandı. "
                "Aynı yöntem İdealData'nın gerçek ağırlık verdiği endekslerde (XU030, X030S, XUSRD…) %0,05'ten az sapma verir."
                ).format(d=b.get("date") or "?", c=(f", %{cap:g} ağırlık sınırı uygulanarak" if cap else ""))
        if missing:
            note += f" {len(missing)} payın BIST TÜM ağırlığı yok (asgari ağırlıkla gösterildi): {', '.join(missing[:8])}."
        return {"rows": est, "source": "tahmini", "note": note, "missing": missing, "ts": base["ts"] if base else None}

    # ----------------------------------------------------------- impact --
    def impact(self, code: str) -> dict:
        code = (code or "").strip().upper()
        wi = self.weights(code)
        ideal = self.ideal_codes()
        name = self._name(code, ideal.get(code, ""))
        last, prev = self._quote(code) if code in ideal else (None, None)
        lvl_src = "idealdata" if last and prev else None
        if not (last and prev):
            o = self._oyak_get().get(code)
            if o:
                last, prev, lvl_src = o["last"], o["prev"], "oyak"
        rows = []
        f = self.feed
        with f._lock:
            for s, w in wi["rows"].items():
                q = f.quotes.get(s) or {}
                p, pc = q.get("last"), q.get("prev_close")
                r = (p / pc - 1.0) if p and pc else None
                rows.append({"s": s, "n": f._name(s) if hasattr(f, "_name") else None, "w": round(w, 4), "p": p, "pc": pc,
                             "c": round(r * 100, 3) if r is not None else None,
                             "ip": round(w * r, 4) if r is not None else None,     # endeks % puanı
                             "pts": round(prev * w / 100.0 * r, 3) if (r is not None and prev) else None,
                             "t": q.get("turnover"), "ts": q.get("last_ts") or q.get("ts")})
        valid = [x for x in rows if x["ip"] is not None]
        model_pct = sum(x["ip"] for x in valid)
        model_pts = prev * model_pct / 100.0 if prev else None
        actual_pts = (last - prev) if (last and prev) else None
        actual_pct = (last / prev - 1) * 100 if (last and prev) else None
        pos = sum(x["pts"] for x in valid if x["pts"] and x["pts"] > 0) if prev else None
        neg = sum(x["pts"] for x in valid if x["pts"] and x["pts"] < 0) if prev else None
        est_level = prev * (1 + model_pct / 100.0) if prev else None
        for x in rows:   # hareketin yüzde kaçını bu hisse açıklıyor
            x["sh"] = round(x["ip"] / model_pct * 100, 2) if (x["ip"] is not None and abs(model_pct) > 1e-9) else None
        return {
            "code": code, "name": name, "group": _group(code), "weight_source": wi["source"], "note": wi["note"],
            "missing": wi.get("missing") or [],
            "level": {"last": last, "prev": prev, "chg_pts": round(actual_pts, 2) if actual_pts is not None else None,
                      "chg_pct": round(actual_pct, 3) if actual_pct is not None else None, "source": lvl_src,
                      "estimated_last": round(est_level, 2) if est_level else None},
            "model": {"pct": round(model_pct, 4), "pts": round(model_pts, 2) if model_pts is not None else None,
                      "pos_pts": round(pos, 2) if pos is not None else None, "neg_pts": round(neg, 2) if neg is not None else None,
                      "explained_pct": round(model_pts / actual_pts * 100, 1) if (model_pts is not None and actual_pts) else None},
            "breadth": {"up": sum(1 for x in valid if x["c"] > 0), "down": sum(1 for x in valid if x["c"] < 0),
                        "flat": sum(1 for x in valid if x["c"] == 0), "noquote": len(rows) - len(valid)},
            "count": len(rows), "rows": rows, "weights_ts": wi.get("ts"),
            "updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        }

    def stock_indices(self, symbol: str) -> dict:
        """Bir hissenin yer aldığı tüm endeksler + o endekslerdeki ağırlığı ve puan etkisi."""
        sym = (symbol or "").strip().upper()
        out = []
        ideal = self.ideal_codes()
        with self._lock:
            kap = dict(self._kapsam)
            bist = dict(self._bist)
        q = self.feed.quotes.get(sym) or {}
        p, pc = q.get("last"), q.get("prev_close")
        r = (p / pc - 1.0) if p and pc else None
        self._oyak_get()
        seen = set()
        for c, k in kap.items():
            if not k.get("ok") or c in EXCLUDE:
                continue
            for s, w, _ in k["rows"]:
                if s == sym:
                    seen.add(c)
                    last, prev = self._quote(c)
                    out.append({"code": c, "name": self._name(c, ideal.get(c, "")), "w": round(w, 4), "src": "idealdata",
                                "pts": round(prev * w / 100 * r, 3) if (prev and r is not None) else None,
                                "ip": round(w * r, 4) if r is not None else None, "group": _group(c)})
                    break
        for c, b in bist.items():
            if c in seen or sym not in b["members"]:
                continue
            if c in ideal and kap.get(c, {}).get("ok"):
                continue
            wi = self.weights(c)
            w = wi["rows"].get(sym)
            o = self._oyak.get(c) or {}
            prev = o.get("prev")
            out.append({"code": c, "name": self._name(c), "w": round(w, 4) if w else None, "src": wi["source"],
                        "pts": round(prev * w / 100 * r, 3) if (prev and w and r is not None) else None,
                        "ip": round(w * r, 4) if (w and r is not None) else None, "group": _group(c)})
        pri = {c: i for i, c in enumerate(GOSTERGE)}
        out.sort(key=lambda x: (GROUP_ORDER.index(x["group"]), pri.get(x["code"], 999), -(x["w"] or 0)))
        return {"symbol": sym, "change_pct": round(r * 100, 3) if r is not None else None, "count": len(out), "indices": out}


index_impact = None


def get_index_impact(feed) -> IndexImpact:
    global index_impact
    if index_impact is None:
        index_impact = IndexImpact(feed)
    return index_impact
