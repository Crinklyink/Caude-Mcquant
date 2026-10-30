import json, sys, time, datetime as dt
sys.path.insert(0,'.')
import yf, config
from concurrent.futures import ThreadPoolExecutor
CUT=config.AS_OF.isoformat()
U=json.load(open("univ_all.json"))
syms=[]
for q in U:
    p=q.get("regularMarketPrice") or 0
    v=q.get("averageDailyVolume3Month") or 0
    if p>5 and p*v>25e6: syms.append(q["symbol"])
syms=[s for s in syms if "-" not in s or s in ("BRK-B","BF-B")] + ["SPY","QQQ","IWM"]
print(len(syms))
def one(s):
    for k in range(3):
        try:
            r=yf.chart(s,"2y","1d")
            ts=r["timestamp"]; qd=r["indicators"]["quote"][0]
            # drop any bar after AS_OF (a partial pre-market/intraday bar for today)
            k=[i for i,x in enumerate(ts) if dt.datetime.fromtimestamp(x,dt.timezone.utc).date().isoformat()<=CUT]
            g=lambda a:[a[i] for i in k]
            return s,{"t":g(ts),"o":g(qd["open"]),"h":g(qd["high"]),"l":g(qd["low"]),"c":g(qd["close"]),"v":g(qd["volume"])}
        except Exception as e:
            time.sleep(1+k)
    return s,None
out={}
with ThreadPoolExecutor(8) as ex:
    for s,d in ex.map(one,syms):
        if d: out[s]=d
print(len(out))
json.dump(out,open("hist.json","w"))
