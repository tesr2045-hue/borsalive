#!/bin/bash
# $1 = label ; restart uvicorn (explicit PID), pin to core 0 with a burner, measure from startup
cd /workspace/bist-analiz
OLD=$(pgrep -f "port 8765 --log-level"); kill $OLD
for i in $(seq 120); do P=$(pgrep -f "port 8765 --log-level"); [ -n "$P" ] && [ "$P" != "$OLD" ] && break; sleep 0.25; done
taskset -a -cp 0 $P >/dev/null
taskset -c 0 python3 /workspace/tmp/burn.py & B=$!
for i in $(seq 240); do taskset -a -cp 0 $P >/dev/null; curl -sf -m2 127.0.0.1:8765/api/health >/dev/null && break; sleep 1; done
echo "[$1] PID $P up after ${i}s"
taskset -a -cp 0 $P >/dev/null
.venv/bin/python /workspace/tmp/dr_measure.py http://127.0.0.1:8765 $P AKBNK,EREGL,TUPRS,BIMAS,KCHOL 40 2>&1 | tail -7
kill $B
