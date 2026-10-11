import json, subprocess, time, urllib.request, base64, sys, tempfile, websocket
PORT=9361; BASE=sys.argv[2]; out=sys.argv[1]; prof=tempfile.mkdtemp()
p=subprocess.Popen(["google-chrome","--headless=new","--no-sandbox","--disable-gpu",f"--remote-debugging-port={PORT}","--remote-allow-origins=*",f"--user-data-dir={prof}","--window-size=412,915","about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try: tabs=json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")); break
        except Exception: time.sleep(0.2)
    ws=websocket.create_connection([t for t in tabs if t["type"]=="page"][0]["webSocketDebuggerUrl"],timeout=90); n=[0]; errs=[]
    def call(m,**pr):
        n[0]+=1; ws.send(json.dumps({"id":n[0],"method":m,"params":pr}))
        while True:
            r=json.loads(ws.recv())
            if r.get("method")=="Runtime.exceptionThrown": errs.append(str(r["params"]["exceptionDetails"])[:300])
            if r.get("id")==n[0]: return r.get("result",r)
    ev=lambda js: call("Runtime.evaluate",expression=js,awaitPromise=True,returnByValue=True).get("result",{}).get("value")
    call("Emulation.setDeviceMetricsOverride",width=412,height=915,deviceScaleFactor=2,mobile=True); call("Page.enable"); call("Runtime.enable")
    call("Network.enable"); call("Network.setExtraHTTPHeaders",headers={"ngrok-skip-browser-warning":"1"})
    def shot(nm, y=None, h=915):
        kw={} if y is None else {"captureBeyondViewport":True,"clip":{"x":0,"y":y,"width":412,"height":h,"scale":2}}
        d=call("Page.captureScreenshot",format="png",**kw)["data"]; open(f"{out}/{nm}.png","wb").write(base64.b64decode(d)); print("saved",nm,flush=True)
    call("Page.navigate",url=BASE+"/?v=1.38.1"); time.sleep(10)
    print("foot", ev("document.getElementById('foot').textContent"))
    ev("window.__bist.selectSymbol('AKBNK');1"); time.sleep(2); ev("window.__bist.openTab('derinlik');1"); time.sleep(8)
    shot("01_derinlik_ust_seans_disi")
    y=ev("(()=>{const e=document.querySelector('.dr-body');return e?Math.max(0,e.getBoundingClientRect().top+window.scrollY-120):0})()")
    print("kart durumu", ev("(()=>{const b=[...document.querySelectorAll('.dr-body')];return [b.length,b.filter(x=>/Yükleniyor|alınamadı|meşgul/.test(x.textContent)).length]})()"))
    for i in range(4): shot(f"0{2+i}_derinlik_analiz_kartlari_{i+1}", y+i*1800, 1800)
    print("errs", errs)
finally: p.kill()
