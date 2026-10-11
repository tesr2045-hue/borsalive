import json, subprocess as _sp, subprocess, time, urllib.request, sys, tempfile, websocket, os
PORT=9351; BASE=sys.argv[1]; SPID=int(sys.argv[2]); SYMS=sys.argv[3].split(","); HOLD=float(sys.argv[4]) if len(sys.argv)>4 else 60
prof=tempfile.mkdtemp()
p=subprocess.Popen(["google-chrome","--headless=new","--no-sandbox","--disable-gpu",f"--remote-debugging-port={PORT}","--remote-allow-origins=*",f"--user-data-dir={prof}","--window-size=412,915","about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def cpu():
    f=open(f"/proc/{SPID}/stat").read().rsplit(")",1)[1].split(); return (int(f[11])+int(f[12]))/os.sysconf("SC_CLK_TCK")
try:
    for _ in range(50):
        try: tabs=json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")); break
        except Exception: time.sleep(0.2)
    ws=websocket.create_connection([t for t in tabs if t["type"]=="page"][0]["webSocketDebuggerUrl"],timeout=120); n=[0]
    reqs={}; done=[]; fails=[]; total=[0]
    def handle(r):
        mm=r.get("method"); pr=r.get("params",{})
        if mm=="Network.requestWillBeSent" and "/api/" in pr["request"]["url"]: reqs[pr["requestId"]]=pr["request"]["url"]; total[0]+=1
        if mm=="Network.loadingFinished" and pr["requestId"] in reqs and "/derinlik-plus" in reqs[pr["requestId"]]: done.append((reqs[pr["requestId"]],time.time()))
        if mm=="Network.loadingFailed" and pr["requestId"] in reqs: fails.append((reqs[pr["requestId"]].split("?")[0][-50:],pr.get("errorText")))
        if mm=="Network.responseReceived" and pr["requestId"] in reqs and pr["response"]["status"]>=500: fails.append((reqs[pr["requestId"]][-50:],pr["response"]["status"]))
    def call(m,**pr):
        n[0]+=1; ws.send(json.dumps({"id":n[0],"method":m,"params":pr}))
        while True:
            r=json.loads(ws.recv()); handle(r)
            if r.get("id")==n[0]: return r.get("result",r)
    ev=lambda js: call("Runtime.evaluate",expression=js,awaitPromise=True,returnByValue=True).get("result",{}).get("value")
    call("Emulation.setDeviceMetricsOverride",width=412,height=915,deviceScaleFactor=2,mobile=True); call("Page.enable"); call("Runtime.enable"); call("Network.enable")
    call("Page.navigate",url=BASE+"/?v=m"+str(time.time())); time.sleep(8)
    c0=cpu(); T0=time.time(); res=[]
    for s in SYMS:
        ev(f"window.__bist.selectSymbol('{s}');1"); time.sleep(1.5); ev("window.__bist.openTab('derinlik');1"); t=time.time(); ok=None; last=""
        while time.time()-t<120:
            st=ev("(()=>{const b=[...document.querySelectorAll('.dr-body')];return [b.length,b.filter(x=>/Yükleniyor/.test(x.textContent)).length,b.filter(x=>/alınamadı|meşgul/.test(x.textContent)).length]})()")
            last=st
            got=[x for x in done if f"/{s}/derinlik-plus" in x[0] and x[1]>=t]
            if got and st and st[1]==0 and st[2]==0: ok=round(got[0][1]-t,1); break
            time.sleep(0.25)
        res.append((s,ok,last)); print(s,"tüm kartlar:",ok,"sn",last,flush=True)
        t1=time.time()
        while time.time()-t1<HOLD: ev("1"); time.sleep(0.5)
    el=time.time()-T0; c=cpu()-c0
    print(json.dumps({"results":res,"api_requests":total[0],"failed":len(fails),"fail_samples":fails[:8],"server_cpu_sec":round(c,1),"window_sec":round(el),"cpu_pct":round(100*c/el)}),flush=True)
finally: p.kill()
