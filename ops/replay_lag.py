#!/usr/bin/env python3
"""v1.37.0 — İşlem akışı gecikme (lag) yük testi. ÜRETİMDE KULLANILMAZ (app tarafından import edilmez).
Kayıtlı bir günün işlemlerini GERÇEK alım yolundan (IdealFeed._parse_drn → trade_store.add_stream) zaman
sırasıyla, gerçek hızda ya da Nx hızda besler; aynı anda 'Son İşlemler' istemcilerini taklit eden thread'ler
zamana/lota/hacme göre sorgular. Ölçülen: lag = simülasyon saati − işlenmiş son işlem saati, ve istemci yanıt süreleri.
Kullanım: python ops/replay_lag.py --day 20261006 --start 10:00 --mins 30 --speed 5 [--old] [--clients 3]
Diske hiçbir şey yazmaz (trade_store geçici dizine yönlendirilir)."""
import argparse, os, sys, time, threading, tempfile, statistics, importlib.util, csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
ap = argparse.ArgumentParser()
ap.add_argument("--day", default="20261006"); ap.add_argument("--start", default="10:00")
ap.add_argument("--mins", type=float, default=30); ap.add_argument("--speed", type=float, default=1)
ap.add_argument("--old", default=""); ap.add_argument("--clients", type=int, default=3)
ap.add_argument("--sym", default="ASTOR")
A = ap.parse_args()
os.environ.setdefault("BIST_REPLAY", "1")
if A.old:   # karşılaştırma: eski live_store sürümü
    sp = importlib.util.spec_from_file_location("app.live_store", A.old); m = importlib.util.module_from_spec(sp)
    sys.modules["app.live_store"] = m; sp.loader.exec_module(m)
import app.live_store as LS
tmp = Path(tempfile.mkdtemp()); LS.TRADES_DIR = tmp
from app.ideal_feed import IdealFeed
from app.live_store import trade_store as TS
feed = IdealFeed()
td = ROOT / "data" / "trades" / A.day
nm = (td / "_brokers.txt").read_text(encoding="utf-8").split("\n")
names = [""] + [x for x in (nm[1:] if nm and nm[0] == "" else nm)]
h, mi = map(int, A.start.split(":")); s0 = h * 3600 + mi * 60; s1 = s0 + int(A.mins * 60)
ev = []
for f in td.glob("*.csv"):
    with open(f) as fh:
        for r in csv.reader(fh):
            t = int(r[0])
            if s0 <= t < s1:
                ev.append((t, f.stem, r))
ev.sort(key=lambda x: x[0])
print(f"{len(ev)} işlem, {A.mins} dk simüle, hız {A.speed}x, {'ESKİ' if A.old else 'YENİ'} kod, {A.clients} istemci", flush=True)
SIDE = {"1": "1", "2": "2", "0": "0"}
def nmof(i):
    i = int(i); return names[i] if 0 <= i < len(names) else ""
wall0 = time.time()
simnow = lambda: s0 + (time.time() - wall0) * A.speed
stop = False; lat = []; samples = []
def client():
    sorts = ["time", "lot", "hacim"]; k = 0
    while not stop:
        t = time.time()
        TS.query(A.sym, sort=sorts[k % 3], limit=100); k += 1
        with feed._lock: pass          # API ucu ideal_feed._lock'u da alır (hacim için)
        lat.append((time.time() - t) * 1000)
        time.sleep(max(0, 1.0 - (time.time() - t)))   # istemci: 1 sn'de bir, üst üste binmez
cl = [threading.Thread(target=client, daemon=True) for _ in range(A.clients)]
last = [s0]
def sampler():
    while not stop:
        time.sleep(max(1.0, A.mins * 60 / A.speed / 60))
        samples.append((round(simnow() - s0), round(simnow() - last[0], 2)))
i = 0; started = False
while i < len(ev):
    t = ev[i][0]
    w = (t - s0) / A.speed - (time.time() - wall0)
    if w > 0: time.sleep(w)
    if not started:
        TS.ensure_day(); [c.start() for c in cl]; threading.Thread(target=sampler, daemon=True).start(); started = True
    j = i; toks = []
    while j < len(ev) and ev[j][0] == t:     # aynı saniyedeki işlemler tek DRN mesajında
        _, sym, r = ev[j]; hh = f"{t//3600:02d}{t//60%60:02d}{t%60:02d}"
        toks += [sym, f"I;{hh};{r[1]};{r[2]};{SIDE.get(r[3], r[3])};{nmof(r[4])};{nmof(r[5])}"]; j += 1
    feed._parse_drn(["", "", "|".join(toks)], time.time())
    last[0] = t; i = j
stop = True
samples.append((round(simnow() - s0), round(simnow() - last[0], 2)))
lat.sort()
n = len(samples)
pick = [samples[0], samples[n // 2], samples[-1]] if n else []
print("lag örnekleri (sim sn, gecikme sn):", samples, flush=True)
print("BAŞ/ORTA/SON lag:", pick)
print(f"istemci sorgu p50={statistics.median(lat):.1f} ms p95={lat[int(len(lat)*.95)-1]:.1f} ms n={len(lat)}; "
      f"duvar süresi {time.time()-wall0:.0f} sn; işlenen {TS.stream_rows}")
