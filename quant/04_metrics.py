import json, numpy as np, datetime as dt
H=json.load(open("hist.json"))
E=json.load(open("earnings.json"))
U={q["symbol"]:q for q in json.load(open("univ_all.json"))}
def arr(d,k): return np.array([np.nan if x is None else x for x in d[k]],float)
def clean(d):
    c=arr(d,"c"); m=~np.isnan(c)
    return {k:np.array([np.nan if x is None else x for x in d[k]],float)[m] for k in "ohlcv"}|{"t":np.array(d["t"])[m]}
D={s:clean(d) for s,d in H.items()}
spy=D["SPY"]
print("last bar SPY:",dt.datetime.utcfromtimestamp(spy["t"][-1]).date(),spy["c"][-1])
# earnings map
ew={}
for day,rows in E.items():
    for r in rows:
        ew.setdefault(r["symbol"],[]).append((day,r["time"],r.get("epsForecast"),r.get("noOfEsts")))
def atr(d,n=14):
    h,l,c=d["h"],d["l"],d["c"]
    tr=np.maximum(h[1:]-l[1:],np.maximum(abs(h[1:]-c[:-1]),abs(l[1:]-c[:-1])))
    return tr[-n:].mean()
def base_rate(d,win=10,thr=0.06,span=504):
    c,h=d["c"],d["h"]
    n=len(c); hits=0;tot=0
    for i in range(max(0,n-span-win-1),n-win-1):
        tot+=1
        if h[i+1:i+1+win].max()>=1.06*c[i]: hits+=1
    return hits/tot if tot else np.nan
rows=[]
for s,d in D.items():
    if s in("SPY","QQQ","IWM") or len(d["c"])<260: continue
    c=d["c"]; p=c[-1]
    sma50=c[-50:].mean(); sma200=c[-200:].mean(); sma20=c[-20:].mean()
    r63=p/c[-64]-1; spy63=spy["c"][-1]/spy["c"][-64]-1
    r21=p/c[-22]-1
    hi52=d["h"][-252:].max()
    a=atr(d); adv=(d["c"][-20:]*d["v"][-20:]).mean()
    gap=d["o"][-1]/c[-2]-1
    ret1=p/c[-2]-1
    rows.append(dict(sym=s,p=p,sma20=sma20,sma50=sma50,sma200=sma200,r21=r21,r63=r63,rs63=r63-spy63,pct_hi=p/hi52-1,atr=a,atrp=a/p,adv=adv,
        ret1=ret1,gap=gap,br=base_rate(d),e=ew.get(s),cap=U.get(s,{}).get("marketCap",0),vr=(d["v"][-5:].mean()/d["v"][-50:].mean())))
import pickle; pickle.dump(rows,open("rows.pkl","wb"))
n=len(rows)
print("N",n,"above50",np.mean([r["p"]>r["sma50"] for r in rows]),"above200",np.mean([r["p"]>r["sma200"] for r in rows]),
      "within5%52wk hi",np.mean([r["pct_hi"]>-0.05 for r in rows]),"above20",np.mean([r["p"]>r["sma20"] for r in rows]))
print("median 10d base rate",np.nanmedian([r["br"] for r in rows]))
for s in("SPY","QQQ","IWM"):
    d=D[s];c=d["c"]
    print(s,c[-1],"50d",c[-50:].mean(),"200d",c[-200:].mean(),"21d ret",c[-1]/c[-22]-1,"63d",c[-1]/c[-64]-1,"hi52",d["h"][-252:].max(),"atr%",atr(d)/c[-1], "baserate",base_rate(d))
