import time,urllib.request,statistics,sys,json
B="http://127.0.0.1:8765"
eps=["/api/health","/api/ideal/status","/api/live/THYAO?trades=200","/api/lite/stocks","/api/ob/list?tf=ortak&limit=6000","/api/albunu/list","/api/link/status","/api/alerts/feed?cid=bench&since=0&visible=1&limit=300"]
out={}
for e in eps:
    ts=[]
    for i in range(int(sys.argv[1]) if len(sys.argv)>1 else 10):
        t=time.time()
        try: urllib.request.urlopen(urllib.request.Request(B+e,headers={"Accept-Encoding":"gzip"}),timeout=90).read()
        except Exception as x: pass
        ts.append((time.time()-t)*1000)
    ts.sort(); out[e]=(round(statistics.median(ts),1), round(ts[int(len(ts)*0.95)-1 if len(ts)>1 else 0],1))
    print(e,out[e],flush=True)
