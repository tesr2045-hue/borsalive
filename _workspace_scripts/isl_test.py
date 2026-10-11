import json, subprocess, time, urllib.request, tempfile, websocket, base64
PORT=9338; prof=tempfile.mkdtemp()
p=subprocess.Popen(["google-chrome","--headless=new","--no-sandbox","--disable-gpu",f"--remote-debugging-port={PORT}","--remote-allow-origins=*",f"--user-data-dir={prof}","--window-size=412,915","about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try: tabs=json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")); break
        except Exception: time.sleep(0.2)
    ws=websocket.create_connection([t for t in tabs if t["type"]=="page"][0]["webSocketDebuggerUrl"],timeout=60); n=[0]; errs=[]
    def call(m,**pr):
        n[0]+=1; ws.send(json.dumps({"id":n[0],"method":m,"params":pr}))
        while True:
            r=json.loads(ws.recv())
            if r.get("method")=="Runtime.exceptionThrown": errs.append(str(r["params"]["exceptionDetails"])[:300])
            if r.get("id")==n[0]: return r.get("result",r)
    ev=lambda js: call("Runtime.evaluate",expression=js,awaitPromise=True,returnByValue=True).get("result",{}).get("value")
    call("Emulation.setDeviceMetricsOverride",width=412,height=915,deviceScaleFactor=1,mobile=True); call("Page.enable"); call("Runtime.enable")
    # sahte canlı akış: sayfa açıldıktan sonra her sn 7 yeni işlem; /api/live/ASTOR?isl=… yanıtı sunucu gibi üretilir
    call("Page.addScriptToEvaluateOnNewDocument", source="""
    (()=>{const of=window.fetch; const T0=Date.now(); const N0=500;
      const sec=()=>{const d=new Date(); return d.getHours()*3600+d.getMinutes()*60+d.getSeconds();};
      const hms=s=>[s/3600|0,(s/60|0)%60,s%60].map(x=>String(x).padStart(2,'0')).join(':');
      window.fetch=async(u,o)=>{const s=String(u); if(!s.includes('/api/live/ASTOR')&&!s.includes('/api/ideal/ASTOR/trades')) return of(u,o);
        const tot=N0+Math.floor((Date.now()-T0)/1000)*7; const q=new URLSearchParams(decodeURIComponent((s.split('isl=')[1]||s.split('?')[1]||'')));
        const off=+(q.get('offset')||0), lim=+(q.get('limit')||200), now=sec();
        const rows=[]; for(let i=tot-1-off;i>=0&&rows.length<lim;i--){const t=now-Math.floor((tot-1-i)/7); rows.push({n:i,time:hms(t),price:100,lot:i%97+1,side:i%2?'buy':'sell',buyer:'A',seller:'B',tl:100*(i%97+1)});}
        const isl={rows,total:tot,all_count:tot,offset:off,limit:lim,brokers:[],sums:{lot:1,buy_lot:1,sell_lot:1,tl:1},coverage:{},last_sec:now,lag_srv:0,live:true,server_ts:Date.now()/1000};
        const body=s.includes('/api/ideal/')?isl:{quote:{price:100,symbol:'ASTOR'},depth:{bids:[],asks:[]},trades:[],isl};
        return new Response(JSON.stringify(body),{status:200,headers:{'content-type':'application/json'}});};})();""")
    call("Page.navigate",url="http://127.0.0.1:8765/?symbol=ASTOR&v=1.37.0"); time.sleep(7)
    ev("window.__bist.openTab('islemler');1"); time.sleep(4)
    top=lambda: ev("(()=>{const r=document.querySelector('#isl-body tr:not(.gap) td'); return r?r.textContent:null})()")
    cnt=lambda: ev("document.querySelectorAll('#isl-body tr:not(.gap)').length")
    print("başlangıç üst satır", top(), "satır", cnt(), "saat", time.strftime("%H:%M:%S"))
    ev("document.getElementById('isl-more').click();1"); time.sleep(2); ev("document.getElementById('isl-more').click();1"); time.sleep(2)
    ev("window.scrollTo(0, document.body.scrollHeight);1"); print("daha fazla ×2 + en alta kaydırıldı; satır", cnt(), "scrollY", ev("scrollY"))
    for k in range(4):
        time.sleep(5); print("t+%ds üst satır"%(5*(k+1)), top(), "| saat", time.strftime("%H:%M:%S"), "| satır", cnt(), "| gecikme:", ev("(document.getElementById('isl-lag')||{}).textContent"))
    print("errs", errs)
finally: p.kill()
