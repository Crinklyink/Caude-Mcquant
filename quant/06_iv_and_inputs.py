import pickle, math, numpy as np, json, datetime as dt, warnings
warnings.filterwarnings("ignore")
from math import log, sqrt, erf
rows={r["sym"]:r for r in pickle.load(open("rows.pkl","rb"))}
res=pickle.load(open("engine.pkl","rb"))
H=json.load(open("hist.json"))
def N(x): return 0.5*(1+erf(x/sqrt(2)))
T=10/252
def tdays(d0,d1):
    n=0;d=d0
    while d<=d1:
        if d.weekday()<5: n+=1
        d+=dt.timedelta(days=1)
    return n
D0=dt.date(2026,10,27)
def rvf(s,n):
    c=np.array([x for x in H[s]["c"] if x is not None]); r=np.diff(np.log(c))[-n:]
    return r.std(ddof=1)*sqrt(252)
def raw(x): return x.get("raw") if isinstance(x,dict) else x
def ivfrom(straddle,spot,exp):
    ed=dt.datetime.fromtimestamp(exp,dt.timezone.utc).date()
    n=tdays(D0,ed)
    return straddle/(0.7979*spot*sqrt(n/252)), n
out=[]
for s,o in res.items():
    r=rows[s]; a=o.get("atm"); qs=o.get("qs") or {}
    if not a or not a.get("straddle") or a["straddle"]<=0 or not o.get("spot"): continue
    spot=o["spot"]
    iv,n=ivfrom(a["straddle"],spot,o["e1"])
    p=r["p"]; atr=r["atr"]
    sig=iv*sqrt(T)
    up=2*N(-log(1.06)/sig); hold=N(-log(1.06)/sig)
    stop=p-1.5*atr; ds=log(p/stop)
    ps=2*N(-ds/sig); pfirst=ds/(ds+log(1.06))
    rv60=rvf(s,60); rv20=rvf(s,20)
    up_rv=2*N(-log(1.06)/(rv60*sqrt(T)))
    ks=qs.get("defaultKeyStatistics",{}) or {}
    et=(qs.get("earningsTrend",{}) or {}).get("trend",[{}]); q0=et[0] if et else {}
    ept=q0.get("epsTrend") or {}
    rev=q0.get("epsRevisions") or {}
    sec=(qs.get("assetProfile") or {}).get("sector"); ind=(qs.get("assetProfile") or {}).get("industry")
    fd=qs.get("financialData") or {}
    em=None
    if o.get("eatm") and o["eatm"].get("straddle"): em=o["eatm"]["straddle"]/spot
    nsa=qs.get("netSharePurchaseActivity") or {}
    out.append(dict(s=s,p=p,iv=iv,nexp=n,exp=dt.datetime.fromtimestamp(o["e1"],dt.timezone.utc).date().isoformat(),up=up,hold=hold,ps=ps,pfirst=pfirst,up_rv=up_rv,rv20=rv20,rv60=rv60,br=r["br"],atr=atr,atrp=r["atrp"],stop=stop,
        rs63=r["rs63"],hi=r["pct_hi"],d50=p/r["sma50"]-1,d200=p/r["sma200"]-1,r21=r["r21"],ret1=r["ret1"],adv=r["adv"],cap=r["cap"],vr=r["vr"],
        e=[x for x in (r["e"] or []) if "2026-10-27"<=x[0]<="2026-11-09"],sec=sec,ind=ind,
        spf=raw(ks.get("shortPercentOfFloat")),dtc=raw(ks.get("shortRatio")),
        eps_now=raw(ept.get("current")),eps7=raw(ept.get("7daysAgo")),eps30=raw(ept.get("30daysAgo")),eps90=raw(ept.get("90daysAgo")),
        upr=raw(rev.get("upLast30days")),dnr=raw(rev.get("downLast30days")),nan=raw((q0.get("earningsEstimate") or {}).get("numberOfAnalysts")),
        tgt=raw(fd.get("targetMeanPrice")),rec=raw(fd.get("recommendationMean")),
        cv=o.get("cv"),pv=o.get("pv"),emove=em,
        insbuy=raw(nsa.get("buyInfoCount")),inssell=raw(nsa.get("sellInfoCount")),netpct=raw(nsa.get("netPercentInsiderShares"))))
pickle.dump(out,open("scored.pkl","wb"))
xs=np.array([x["up"] for x in out]); ys=np.array([x["br"] for x in out]); xr=np.array([x["up_rv"] for x in out])
print(len(out),"IV median",np.median([x["iv"] for x in out]),"formula(IV) mean",xs.mean(),"formula(RV60) mean",xr.mean(),"empirical base mean",ys.mean())
print("corr IV-formula vs empirical",np.corrcoef(xs,ys)[0,1],"corr RV-formula vs emp",np.corrcoef(xr,ys)[0,1])
