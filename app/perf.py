"""v1.38.1 — Kaynak profili (data/perf.json). Küçük makinede (CPU ≤ 2 ya da RAM ≤ 4 GB) low_resource otomatik açılır:
* arka plan motorlarının tur aralıkları uzar (interval_mul, en az min_gap_sec boşluk), motor iş parçacıkları düşük öncelik (nice),
* açılışta motorlar sırayla başlar (startup_stagger_sec arayla), istek iş parçacığı havuzu sınırlanır (threadpool).
Gecikmeye duyarlı canlı yollar (işlem akışı, Son İşlemler, Trene Atla, Radar/Tavan) YAVAŞLATILMAZ.
perf.json: {"low_resource": "auto" | true | false, "interval_mul": 3, "min_gap_sec": 20, "startup_stagger_sec": 20, "threadpool": 16, "nice": 10}"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

F = Path(__file__).resolve().parents[1] / "data" / "perf.json"
DEF = {"low_resource": "auto", "interval_mul": 3.0, "min_gap_sec": 20, "startup_stagger_sec": 20, "threadpool": 16, "nice": 0,
       "no_throttle": ["tren", "radar", "dpage"]}


def _cpus():
    try:
        return len(os.sched_getaffinity(0))
    except Exception:
        return os.cpu_count() or 1


def _ram_gb():
    try:
        for ln in open("/proc/meminfo"):
            if ln.startswith("MemTotal:"):
                kb = int(ln.split()[1])
                break
        try:   # cgroup sınırı (konteyner / VDS)
            v = open("/sys/fs/cgroup/memory.max").read().strip()
            if v.isdigit():
                kb = min(kb, int(v) // 1024)
        except Exception:
            pass
        return kb / 1024 / 1024
    except Exception:
        return 99.0


def load():
    c = dict(DEF)
    try:
        c.update(json.loads(F.read_text(encoding="utf-8")))
    except Exception:
        try:
            F.parent.mkdir(parents=True, exist_ok=True)
            F.write_text(json.dumps(DEF, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:
            pass
    env = os.environ.get("BIST_LOW_RESOURCE")
    if env in ("0", "1"):
        c["low_resource"] = env == "1"
    cpus, ram = _cpus(), _ram_gb()
    lr = c.get("low_resource")
    c["auto_reason"] = f"{cpus} CPU, {ram:.1f} GB RAM"
    c["active"] = (cpus <= 2 or ram <= 4.0) if lr == "auto" else bool(lr)
    c["cpus"], c["ram_gb"] = cpus, round(ram, 1)
    return c


CFG = load()
LOW = CFG["active"]
_stag = {"n": 0}
_stag_lock = threading.Lock()
_niced = set()


THROTTLE = {("skor", "compute"), ("algo", "compute"), ("maliyet", "_step"), ("baski", "_step"), ("akd", "tarama"),
            ("kademe", "compute"), ("op", "compute")}


def engine_pass_done(key, elapsed, meth=""):
    """Bir motor turu bitti → low_resource'ta ek bekleme (tur süresi × (mul−1), en az min_gap). Yalnız ağır tarama turları."""
    if not LOW or (key, meth) not in THROTTLE:
        return
    extra = max(float(CFG["min_gap_sec"]), elapsed * (float(CFG["interval_mul"]) - 1.0))
    time.sleep(min(extra, 300.0))


def engine_thread_init(key, meth=""):
    """Motor iş parçacığının ilk turu: düşük öncelik (nice) + açılışta sıralı başlangıç (low_resource)."""
    tid = threading.get_native_id()
    if tid in _niced:
        return
    _niced.add(tid)
    if (key, meth) not in THROTTLE:
        return
    try:
        # not: aynı süreçteki iş parçacığına nice vermek GIL tutarken uyutulmasına (öncelik terslemesi) yol açıyor —
        # ölçümde istekleri yavaşlattı; varsayılan 0. Asıl önceliklendirme tur aralığı uzatma + sıralı açılışla yapılır.
        if LOW and int(CFG.get("nice", 0)) > 0:
            os.setpriority(os.PRIO_PROCESS, tid, int(CFG.get("nice", 10)))
    except Exception:
        pass
    if LOW:
        with _stag_lock:
            k = _stag["n"]; _stag["n"] += 1
        time.sleep(k * float(CFG["startup_stagger_sec"]))


def status():
    return {k: CFG[k] for k in ("low_resource", "active", "auto_reason", "cpus", "ram_gb", "interval_mul", "min_gap_sec",
                                 "startup_stagger_sec", "threadpool", "nice")}
