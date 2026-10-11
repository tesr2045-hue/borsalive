import json, subprocess, time, urllib.request, base64, sys, tempfile, websocket
PORT=9340; BASE=sys.argv[2]; out=sys.argv[1]; prof=tempfile.mkdtemp()
p=subprocess.Popen(["google-chrome","--headless=new","--no-sandbox","--disable-gpu",f"--remote-debugging-port={PORT}","--remote-allow-origins=*",f"--user-data-dir={prof}","--window-size=412,915","about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try: tabs=json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")); break
        except Exception: time.sleep(0.2)
    ws=websocket.create_connection([t for t in tabs if t["type"]=="page"][0]["webSocketDebuggerUrl"],timeout=60); n=[0]; errs=[]; os_req=[]
    def call(m,**pr):
        n[0]+=1; ws.send(json.dumps({"id":n[0],"method":m,"params":pr}))
        while True:
            r=json.loads(ws.recv()); mm=r.get("method")
            if mm=="Runtime.exceptionThrown": errs.append(str(r["params"]["exceptionDetails"].get("exception",{}).get("description",""))[:200])
            if mm=="Network.requestWillBeSent" and "onesignal" in r["params"]["request"]["url"].lower(): os_req.append(r["params"]["request"]["url"][:100])
            if r.get("id")==n[0]: return r.get("result",r)
    ev=lambda js: call("Runtime.evaluate",expression=js,awaitPromise=True,returnByValue=True).get("result",{}).get("value")
    call("Emulation.setDeviceMetricsOverride",width=412,height=915,deviceScaleFactor=2,mobile=True); call("Page.enable"); call("Runtime.enable"); call("Network.enable")
    call("Network.setExtraHTTPHeaders",headers={"ngrok-skip-browser-warning":"1"})
    def shot(nm): d=call("Page.captureScreenshot",format="png")["data"]; open(f"{out}/{nm}.png","wb").write(base64.b64decode(d)); print("saved",nm,flush=True)
    call("Page.navigate",url=BASE+"/?v=1.38.0"); time.sleep(9)
    print("foot", ev("document.getElementById('foot').textContent"))
    ev("window.__bist.go('telegram');1"); time.sleep(4); shot("01_telegram_durum_baglanti")
    def part(sel, nm, h=915):
        y = ev(f"(()=>{{const e=document.querySelector({json.dumps(sel)});return e?Math.max(0,e.getBoundingClientRect().top+window.scrollY-70):0}})()")
        d=call("Page.captureScreenshot",format="png",captureBeyondViewport=True,clip={"x":0,"y":y,"width":412,"height":h,"scale":2})["data"]; open(f"{out}/{nm}.png","wb").write(base64.b64decode(d)); print("saved",nm,flush=True)
    part(".tg-guide","02_kurulum_rehberi")
    part("[data-tgcat]","03_ne_gonderilsin_kategoriler")
    part("#view-telegram .nf-grp","04_sinyal_turleri_toggle", 1400)
    ev("document.querySelector('[data-tg=test]').click();1"); time.sleep(3); ev("window.scrollTo(0,0);1"); time.sleep(1); shot("05_test_gonderildi")
    ev("window.__bist.go('kf');1"); time.sleep(1)
    ev("document.getElementById('live-pill').click();1"); time.sleep(2); shot("06_durum_paneli_telegram_dugmesi")
    print("sw:", ev("navigator.serviceWorker.getRegistrations().then(r=>r.map(x=>x.active&&x.active.scriptURL))"))
    print("onesignal istekleri:", os_req); print("errs", errs)
finally: p.kill()
