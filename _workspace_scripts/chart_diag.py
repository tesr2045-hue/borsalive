import json, subprocess, time, urllib.request, tempfile, websocket, base64, sys
PORT=9339; prof=tempfile.mkdtemp(); BASE=sys.argv[1]; OUT=sys.argv[2] if len(sys.argv)>2 else None
p=subprocess.Popen(["google-chrome","--headless=new","--no-sandbox","--disable-gpu",f"--remote-debugging-port={PORT}","--remote-allow-origins=*",f"--user-data-dir={prof}","--window-size=412,915","about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try: tabs=json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")); break
        except Exception: time.sleep(0.2)
    ws=websocket.create_connection([t for t in tabs if t["type"]=="page"][0]["webSocketDebuggerUrl"],timeout=90); n=[0]; errs=[]; fails=[]; REQ={}
    def call(m,**pr):
        n[0]+=1; ws.send(json.dumps({"id":n[0],"method":m,"params":pr}))
        while True:
            r=json.loads(ws.recv()); mm=r.get("method")
            if mm=="Runtime.exceptionThrown": errs.append(str(r["params"]["exceptionDetails"].get("exception",{}).get("description",""))[:200])
            if mm=="Runtime.consoleAPICalled" and r["params"]["type"] in("error","warning"): errs.append("console: "+str([a.get("value",a.get("description")) for a in r["params"]["args"]])[:200])
            if mm=="Network.loadingFailed": fails.append(r["params"].get("errorText"))
            if mm=="Network.responseReceived" and r["params"]["response"]["status"]>=400: fails.append((r["params"]["response"]["status"], r["params"]["response"]["url"][:100]))
            if mm=="Network.requestWillBeSent" and "/api/stocks/" in r["params"]["request"]["url"]: REQ[r["params"]["requestId"]]=[time.time(),r["params"]["request"]["url"][-60:]]
            if mm=="Network.loadingFinished" and r["params"]["requestId"] in REQ: REQ[r["params"]["requestId"]].append(round(time.time()-REQ[r["params"]["requestId"]][0],1))
            if mm=="Network.loadingFailed" and r["params"]["requestId"] in REQ: REQ[r["params"]["requestId"]].append("FAIL "+r["params"].get("errorText",""))
            if r.get("id")==n[0]: return r.get("result",r)
    ev=lambda js: call("Runtime.evaluate",expression=js,awaitPromise=True,returnByValue=True).get("result",{}).get("value")
    call("Emulation.setDeviceMetricsOverride",width=412,height=915,deviceScaleFactor=2,mobile=True); call("Page.enable"); call("Runtime.enable"); call("Network.enable")
    call("Network.setExtraHTTPHeaders",headers={"ngrok-skip-browser-warning":"1"})
    if len(sys.argv)>3: call("Network.setBlockedURLs", urls=["*unpkg.com*"])
    call("Page.navigate",url=BASE+"/?symbol=THYAO&v=1.37.0"); time.sleep(10)
    print("LWC:", ev("typeof LightweightCharts"), "| msg:", ev("(()=>{const m=document.getElementById('chart-msg');return (m.hidden?'[gizli] ':'')+m.textContent})()"), "| src:", ev("document.getElementById('chart-src').textContent"))
    for s in (["THYAO","KZGYO","ASELS"] if OUT else []):
        ev(f"window.__bist.selectSymbol('{s}');1"); time.sleep(3); ev("window.__bist.openTab('ozet');1"); time.sleep(2)
        for tf in ["1m","5m","15m","1h","4h","1d","1w"]:
            ev(f"document.querySelector('#tf-bar button[data-tf=\"{tf}\"]').click();1")
            t0=time.time()
            while time.time()-t0<30:
                v=ev("(()=>{const m=document.getElementById('chart-msg');return m.hidden?'ok':m.textContent})()")
                if v=='ok' or not v.startswith('Grafik yükleniyor'): break
                time.sleep(0.5)
            print(s,tf,round(time.time()-t0,1),"sn:",v,"|",ev("document.getElementById('chart-src').textContent")[:110], flush=True)
            if tf in ("5m","1d") or s=="THYAO":
                ev("document.getElementById('chart-box').scrollIntoView({block:'center'});1"); time.sleep(0.6)
                d=call("Page.captureScreenshot",format="png")["data"]; open(f"{OUT}/grafik_{s}_{tf}.png","wb").write(base64.b64decode(d))
    print("tab", ev("window.__bist.st.tab"), "view", ev("window.__bist.st.view"), "gen", ev("window.__bist.st.gen"), "tf", ev("window.__bist.st.tf"))
    print("openTab:", ev("(()=>{try{window.__bist.openTab('ozet');return 'ok'}catch(e){return String(e.stack)}})()"))
    time.sleep(20); ev("1"); print("sonra msg:", ev("document.getElementById('chart-msg').textContent"), ev("document.getElementById('chart-msg').hidden")); print("REQ",[v[1:] for v in REQ.values()])
    print("errs",errs[:8]); print("fails",fails[:8])
finally: p.kill()
