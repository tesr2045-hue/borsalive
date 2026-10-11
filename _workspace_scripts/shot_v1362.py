import json, subprocess, time, urllib.request, base64, sys, tempfile, websocket
PORT = 9333
prof = tempfile.mkdtemp(prefix="chr-")
p = subprocess.Popen(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
                      f"--user-data-dir={prof}", "--window-size=412,915", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")); break
        except Exception: time.sleep(0.2)
    page = [t for t in tabs if t["type"] == "page"][0]
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=60)
    n = [0]
    def call(m, **pr):
        n[0] += 1; ws.send(json.dumps({"id": n[0], "method": m, "params": pr}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == n[0]: return r.get("result", r)
    def ev(js):
        return call("Runtime.evaluate", expression=js, awaitPromise=True, returnByValue=True).get("result", {}).get("value")
    call("Emulation.setDeviceMetricsOverride", width=412, height=915, deviceScaleFactor=2, mobile=True)
    call("Emulation.setUserAgentOverride", userAgent="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36")
    call("Page.enable")
    def shot(path):
        d = call("Page.captureScreenshot", format="png")["data"]; open(path, "wb").write(base64.b64decode(d)); print("saved", path)
    out = sys.argv[1]
    call("Page.navigate", url="http://127.0.0.1:8765/?v=1.36.2"); time.sleep(8)
    ev("localStorage.removeItem('obtF'); 1")
    ev("window.__bist.go('obt'); 1"); time.sleep(7)
    shot(out + "/01_ortak_en_guclu_liste.png")
    ev("document.querySelector('[data-panel]').click(); 1"); time.sleep(1)
    ev("const s=document.querySelector('.obt-sel[data-k=sort]'); s.value='ugradi'; s.dispatchEvent(new Event('change')); 1"); time.sleep(1)
    ev("window.scrollTo(0,0); 1"); time.sleep(1)
    shot(out + "/02_siralama_filtre_paneli.png")
    ev("document.querySelector('[data-pre=yakin]').click(); 1"); time.sleep(5)
    shot(out + "/03_hazir_ayar_ortak_destek_yakin.png")
    ev("window.__bistObt.detail('KARTN','15m'); 1"); time.sleep(5)
    shot(out + "/04_detay_ortak_kart.png")
    ev("document.getElementById('obt-sbody').scrollTop=560; 1"); time.sleep(1)
    shot(out + "/05_detay_grafik_ortak_kalin.png")
finally:
    p.kill()

