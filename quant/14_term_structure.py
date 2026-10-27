import sys, json, datetime as dt, numpy as np, warnings, pickle
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
import yf
from math import sqrt
D0=dt.date(2026,10,28)
def tdays(d1):
    n=0;d=D0
    while d<=d1:
        if d.weekday()<5: n+=1
        d+=dt.timedelta(days=1)
    return n
def mid(x):
    b,a=x.get("bid") or 0,x.get("ask") or 0
    if b>0 and a>0 and a<=b*1.6+0.05: return (b+a)/2,"m"
    return (x.get("lastPrice") or 0),"l"
def term(sym,maxd=dt.date(2026,12,5)):
    o=yf.options(sym); spot=o["quote"]["regularMarketPrice"]
    res=[]
    for e in o["expirationDates"]:
        ed=dt.datetime.fromtimestamp(e,dt.timezone.utc).date()
        if ed>maxd: break
        ch=o if o["options"][0]["expirationDate"]==e else yf.options(sym,e)
        c={x["strike"]:x for x in ch["options"][0]["calls"]}; p={x["strike"]:x for x in ch["options"][0]["puts"]}
        ks=sorted(set(c)&set(p),key=lambda k:abs(k-spot))[:3]
        vals=[];q=[]
        for k in ks:
            cm,cq=mid(c[k]); pm,pq=mid(p[k])
            if cm>0 and pm>0: vals.append(cm+pm); q.append(cq+pq)
        if not vals: continue
        st=float(np.median(vals)); n=tdays(ed)
        iv=st/(0.7979*spot*sqrt(n/252))
        vol=sum((c[k].get("volume") or 0)+(p[k].get("volume") or 0) for k in ks)
        res.append((ed.isoformat(),n,st,st/spot,iv,vol,"".join(sorted(set("".join(q))))))
    return spot,res
if __name__=="__main__":
    out={}
    for s in sys.argv[1:]:
        try:
            spot,r=term(s); out[s]=(spot,r)
            print(f"\n{s} spot={spot}")
            for x in r: print(f"  {x[0]} n={x[1]:2d} straddle={x[2]:7.2f} ({x[3]*100:5.1f}%) IV={x[4]*100:5.0f}% vol3k={x[5]:6d} q={x[6]}")
        except Exception as e: print(s,"ERR",e)
    pickle.dump(out,open("term7.pkl","wb"))
