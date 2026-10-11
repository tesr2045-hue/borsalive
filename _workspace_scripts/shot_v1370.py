import json, subprocess, time, urllib.request, base64, sys, tempfile, websocket
PORT = 9337
BASE = sys.argv[2]; out = sys.argv[1]
prof = tempfile.mkdtemp(prefix="chr-")
p = subprocess.Popen(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
                      f"--user-data-dir={prof}", "--window-size=412,915", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try: tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")); break
        except Exception: time.sleep(0.2)
    page = [t for t in tabs if t["type"] == "page"][0]
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=60)
    n = [0]; errs = []
    def call(m, **pr):
        n[0] += 1; ws.send(json.dumps({"id": n[0], "method": m, "params": pr}))
        while True:
            r = json.loads(ws.recv())
            if r.get("method") == "Runtime.exceptionThrown": errs.append(str(r["params"]["exceptionDetails"].get("exception", {}).get("description", ""))[:200])
            if r.get("id") == n[0]: return r.get("result", r)
    def ev(js): return call("Runtime.evaluate", expression=js, awaitPromise=True, returnByValue=True).get("result", {}).get("value")
    call("Emulation.setDeviceMetricsOverride", width=412, height=915, deviceScaleFactor=2, mobile=True)
    call("Page.enable"); call("Runtime.enable"); call("Network.enable"); call("Network.setExtraHTTPHeaders", headers={"ngrok-skip-browser-warning": "1"})
    def shot(name):
        d = call("Page.captureScreenshot", format="png")["data"]; open(f"{out}/{name}.png", "wb").write(base64.b64decode(d)); print("saved", name, flush=True)
    def until(js, sec):
        t = time.time() + sec
        while time.time() < t:
            v = ev(js)
            if v: return v
            time.sleep(0.7)
        return None
    for _ in range(60):
        try:
            call("Page.navigate", url=BASE + "/?v=1.37.0"); time.sleep(6)
            if ev("!!(window.__bist && window.__bist.go)"): break
        except Exception: pass
        time.sleep(3)
    print("APPV", ev("document.getElementById('foot').textContent"), flush=True)
    ev("window.__bist.go('fm_grafik'); 1")
    r = until("(()=>{const b=document.querySelector('.view[data-view=fm_grafik] .pgbar.run'); return b&&!b.hidden&&/\\d+\\/\\d+/.test(b.textContent)?b.textContent:null})()", 150)
    print("fm:", r, flush=True); time.sleep(0.5); shot("01_formasyonlar_ilerleme")
    ev("window.__bist.go('obt'); 1")
    r = until("(()=>{const b=document.querySelector('.view[data-view=obt] .pgbar.run'); return b&&!b.hidden&&(+((b.textContent.match(/: (\\d+)\\//)||[])[1]||0))>=60?b.textContent:null})()", 200)
    print("ob:", r, flush=True); shot("02_order_block_ilerleme")
    r = until("(()=>{const b=document.querySelector('.view[data-view=obt] .pgbar.idle'); return b&&!b.hidden&&/Son tarama/.test(b.textContent)?b.textContent:null})()", 200)
    until("document.querySelectorAll('.obt-it').length>0", 40); time.sleep(2); r = ev("document.querySelector('.view[data-view=obt] .pgbar').textContent")
    print("ob idle:", r, flush=True); shot("03_order_block_son_tarama")
    ev("window.__bist.go('skor'); 1"); time.sleep(5); print("skor:", ev("(document.querySelector('.view[data-view=skor] .pgbar')||{}).textContent"), flush=True); shot("04_dak_skor")
    ev("window.__bist.selectSymbol('ASTOR'); 1"); time.sleep(4); ev("window.__bist.openTab('islemler'); 1"); time.sleep(5)
    print("lag:", ev("(document.getElementById('isl-lag')||{}).textContent"), flush=True); shot("05_islemler_gecikme")
    print("errs", errs)
finally:
    p.kill()
