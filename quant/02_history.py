import json, sys, time
sys.path.insert(0,'.')
import yf
from concurrent.futures import ThreadPoolExecutor
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
            return s,{"t":ts,"o":qd["open"],"h":qd["high"],"l":qd["low"],"c":qd["close"],"v":qd["volume"]}
        except Exception as e:
            time.sleep(1+k)
    return s,None
out={}
with ThreadPoolExecutor(8) as ex:
    for s,d in ex.map(one,syms):
        if d: out[s]=d
print(len(out))
json.dump(out,open("hist.json","w"))
