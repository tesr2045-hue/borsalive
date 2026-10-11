import json, os, sys, threading, time, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
sys.path.insert(0, "/workspace/bist-analiz")
LOG = []; N = {"send": 0}
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self): self.do_GET()
    def do_GET(self):
        m = self.path.rsplit("/", 1)[-1].split("?")[0]
        ln = int(self.headers.get("content-length") or 0); q = parse_qs(self.rfile.read(ln).decode()) if ln else {}
        if m == "getMe": r = {"ok": True, "result": {"username": "mock_bot"}}
        elif m == "getUpdates": r = {"ok": True, "result": [{"channel_post": {"chat": {"id": -1001234567890, "type": "channel", "title": "BIST Bildirimleri"}}}]}
        elif m == "sendMessage":
            N["send"] += 1
            if N["send"] == 3: self.send_response(429); self.end_headers(); self.wfile.write(json.dumps({"ok": False, "error_code": 429, "description": "Too Many Requests", "parameters": {"retry_after": 3}}).encode()); return
            LOG.append((time.time(), q.get("chat_id", [""])[0], q.get("text", [""])[0])); r = {"ok": True, "result": {}}
        else: r = {"ok": False}
        b = json.dumps(r).encode(); self.send_response(200); self.send_header("content-type", "application/json"); self.end_headers(); self.wfile.write(b)
srv = ThreadingHTTPServer(("127.0.0.1", 18443), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ["TELEGRAM_API"] = "http://127.0.0.1:18443"
import app.telegram_notify as T
d = tempfile.mkdtemp(); T.CFG_F = T.Path(d) / "tg.json"; T.Q_F = T.Path(d) / "q.json"
tg = T.Telegram(); tg.cfg.update(token="123456:" + "x" * 35, chat_id="-1001234567890")
print("getUpdates sohbetleri:", tg._api("getUpdates", {})["result"][0]["channel_post"]["chat"]["title"])
# 1) kalıcılık: worker çalışmadan kuyruğa al → yeni örnek kuyruğu diskten okur
for i in range(5): tg.enqueue("sinyal", f"<b>persist {i}</b>")
tg2 = T.Telegram(); tg2.cfg.update(token=tg.cfg["token"], chat_id=tg.cfg["chat_id"])
print("yeniden başlatma sonrası diskten kuyruk:", len(tg2.q))
# 2) dedupe
a = tg2.enqueue("sinyal", "aynı mesaj"); b = tg2.enqueue("sinyal", "aynı mesaj"); print("dedupe: ilk", a, "ikinci", b)
# 3) patlama: 60 farklı sinyal + format
ev = {"title": "🚀 THYAO trene atla", "text": "≥5 kademe süpürme, ivme", "sym": "THYAO", "time": "10:15:03"}
print("örnek mesaj:\n" + tg2.fmt_event(ev))
for i in range(60): tg2.enqueue("sinyal", tg2.fmt_event(dict(ev, text=f"olay {i}")))
tg2.system("Yeni ngrok linki", "Eski: https://eski", cat="link")
t0 = time.time(); threading.Thread(target=tg2._worker, daemon=True).start(); tg2.ev.set()
while (tg2.q) and time.time() - t0 < 120: time.sleep(0.5)
el = time.time() - t0
print(f"kuyruk boşaldı: {len(tg2.q)} kaldı, {el:.1f} sn, Telegram'a giden mesaj: {len(LOG)}, 429 sonrası tekrar: {'evet' if N['send'] > len(LOG) else 'hayır'}")
print("birleştirilen:", tg2.st["merged"], "| son hata:", tg2.st["last_err"])
mx = max(sum(1 for t, _, _ in LOG if s <= t < s + 60) for s, _, _ in LOG); print("herhangi 60 sn'de en çok mesaj:", mx)
tot = sum(x[2].count("olay ") for x in LOG) + sum(x[2].count("persist") for x in LOG); print("iletilen içerik: 60 olay + 5 persist =", tot)
srv.shutdown()
