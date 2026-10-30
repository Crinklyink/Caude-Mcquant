import sys, json, time, urllib.parse, urllib.request, datetime as dt, numpy as np, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
import yf, config
H=json.load(open("hist.json"))
def clean(s):
    d=H[s]; idx=[i for i,x in enumerate(d["c"]) if x is not None]
    g=lambda k:[d[k][i] for i in idx]
    return dict(t=[dt.datetime.fromtimestamp(x,dt.timezone.utc).date() for x in g("t")],o=g("o"),c=g("c"))
def yahoo_dates(sym):
    q={"sortType":"DESC","entityIdType":"earnings","sortField":"startdatetime","includeFields":["ticker","startdatetime","epsestimate","epsactual","epssurprisepct"],
       "query":{"operator":"and","operands":[{"operator":"eq","operands":["ticker",sym]}]},"size":20,"offset":0}
    u="https://query1.finance.yahoo.com/v1/finance/visualization?crumb="+urllib.parse.quote(yf.crumb)+"&lang=en-US&region=US"
    req=urllib.request.Request(u,data=json.dumps(q).encode(),headers={"User-Agent":"Mozilla/5.0","Content-Type":"application/json"})
    try:
        d=json.loads(yf.op.open(req,timeout=30).read())["finance"]["result"][0]["documents"][0]
        cols=[c["id"] for c in d["columns"]]
        return [dict(zip(cols,r)) for r in d["rows"]]
    except Exception: return []
def nasdaq_dates(sym):
    req=urllib.request.Request(f"https://api.nasdaq.com/api/company/{sym}/earnings-surprise",headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
    try:
        j=json.loads(urllib.request.urlopen(req,timeout=25).read())
        rows=j["data"]["earningsSurpriseTable"]["rows"]
        out=[]
        for r in rows:
            m,d,y=map(int,r["dateReported"].split("/")); out.append((dt.date(y,m,d),r.get("percentageSurprise")))
        return out
    except Exception: return []
def retry(f,sym,k=3):
    # both sources return [] on any error; retry so a transient failure does not drop a stock's history
    for i in range(k):
        r=f(sym)
        if r: return r
        time.sleep(1+i)
    return []
def moves(sym,n=8):
    P=clean(sym); T=P["t"]; C=P["c"]; O=P["o"]
    ds={}
    yd,nd=retry(yahoo_dates,sym),retry(nasdaq_dates,sym)
    if not yd and not nd: print(f"WARN ehist: no earnings dates for {sym}",file=sys.stderr)
    for r in yd:
        try:
            d=dt.datetime.fromisoformat(r["startdatetime"].replace("Z","+00:00")).astimezone(dt.timezone(dt.timedelta(hours=-4))).date()
            ds[d]=r.get("epssurprisepct")
        except Exception: pass
    for d,sp in nd: ds[d]=sp
    res=[]
    for d in sorted(ds,reverse=True):
        if d>config.AS_OF: continue   # ignore reports after the last completed session
        if d<T[0]+dt.timedelta(days=3): continue
        # locate index of d (or next trading day)
        i=next((k for k,x in enumerate(T) if x>=d),None)
        if i is None or i<1 or i+1>=len(T): continue
        if T[i]!=d: pass
        gapD=abs(O[i]/C[i-1]-1); gapN=abs(O[i+1]/C[i]-1)
        if gapN>gapD: mv=C[i+1]/C[i]-1; day=T[i+1]; tim="AMC"
        else: mv=C[i]/C[i-1]-1; day=T[i]; tim="BMO"
        res.append((d,tim,mv,ds[d]))
        if len(res)>=n: break
    return res
if __name__=="__main__":
    out={}
    for s in sys.argv[1:]:
        m=moves(s)
        out[s]=m
        a=np.mean([abs(x[2]) for x in m]) if m else float("nan")
        up=np.mean([x[2]>0 for x in m]) if m else float("nan")
        print(s,f"n={len(m)} avg|move|={a*100:.1f}% up%={up*100:.0f}% mean signed={np.mean([x[2] for x in m])*100 if m else float('nan'):.1f}%  ", " ".join(f"{x[0].isoformat()[2:]}{x[1][0]}:{x[2]*100:+.1f}" for x in m))
