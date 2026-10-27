import sys, json, pickle, time, math, urllib.parse, urllib.request, datetime as dt
sys.path.insert(0,'.')
import yf, numpy as np
import config
from concurrent.futures import ThreadPoolExecutor
rows=pickle.load(open("rows.pkl","rb"))
R={r["sym"]:r for r in rows}
spy63=None
H=json.load(open("hist.json"))
# universe selection
def sel(r):
    e_in = r["e"] and any(config.WIDE_START<=x[0]<=config.WIDE_END for x in r["e"])
    trend = r["p"]>r["sma200"] and r["p"]>r["sma50"]
    if trend and r["rs63"]>0.10: return True
    if e_in and r["p"]>r["sma200"] and r["pct_hi"]>-0.15 and r["rs63"]>-0.02: return True
    return False
extra=set("PLTR TSLA NVDA AMD AVGO MU SMCI IONQ RKLB HOOD COIN MSTR SOFI AFRM UPST APP DKNG CRWD NET SNOW DDOG ZS S OKTA SHOP ROKU U TTD DASH UBER ABNB LYFT PINS SNAP W CVNA CELH ELF ONON DECK LULU NKE FSLR ENPH RUN SEDG PLUG BE OKLO SMR NNE CCJ LEU UEC DNN XOM CVX OXY DVN FANG EOG COP HAL SLB MRO CTRA EQT AR RRC CNX GPOR LNG VST CEG TLN NRG GEV".split())
extra |= set("LITE COHR ARM ALAB CRDO AXTI TSEM KLAC STX ANET INTC WDC LRCX AMAT CIEN CLS VICR TTMI MRCY VSAT NOK LEGN OKLO LEU RKLB IONQ APP COIN HOOD UPST AFRM FSLY SMCI SOFI CVNA".split())
def inwin(r):
    return bool(r["e"]) and any(config.WIN_START<=x[0]<=config.WIN_END for x in r["e"]) and r["atrp"]>0.03 and r["adv"]>30e6
cands=[s for s,r in R.items() if sel(r) or s in extra or inwin(r)]
# optional: python -I 05_options_engine.py TICK1 TICK2 ...  -> run only these and merge into engine.pkl
ONLY=[a for a in sys.argv[1:] if a in R]
if ONLY: cands=ONLY
print("universe for options:",len(cands))
def jget(u):
    for k in range(3):
        try: return json.loads(yf.get(u))
        except Exception as e:
            time.sleep(1.0+k)
    return None
def qsum(s):
    u=f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{s}?modules=assetProfile,defaultKeyStatistics,earningsTrend,calendarEvents,financialData,netSharePurchaseActivity&crumb={urllib.parse.quote(yf.crumb)}"
    j=jget(u)
    try: return j["quoteSummary"]["result"][0]
    except Exception: return None
def raw(x): 
    return x.get("raw") if isinstance(x,dict) else x
def opts(s):
    try:
        o=yf.options(s)
    except Exception: return None
    return o
def chain_at(s,exp):
    try: return yf.options(s,exp)
    except Exception: return None
def atm(ch,spot):
    c=ch["options"][0]["calls"]; p=ch["options"][0]["puts"]
    if not c or not p: return None
    kc={x["strike"]:x for x in c}; kp={x["strike"]:x for x in p}
    ks=sorted(set(kc)&set(kp), key=lambda k:abs(k-spot))
    if not ks: return None
    k=ks[0]
    def mid(x):
        b,a=x.get("bid") or 0,x.get("ask") or 0
        return (b+a)/2 if b>0 and a>0 else (x.get("lastPrice") or 0)
    iv=np.nanmean([kc[k].get("impliedVolatility",np.nan),kp[k].get("impliedVolatility",np.nan)])
    # average two nearest strikes for stability
    return dict(k=k,iv=float(iv),straddle=mid(kc[k])+mid(kp[k]),oi=(kc[k].get("openInterest") or 0)+(kp[k].get("openInterest") or 0),vol=(kc[k].get("volume") or 0)+(kp[k].get("volume") or 0))
def work(s):
    out={"sym":s}
    out["qs"]=qsum(s)
    o=opts(s)
    if not o: return out
    q=o["quote"]; spot=q.get("regularMarketPrice")
    exps=o["expirationDates"]
    out["spot"]=spot
    cutoff=config.EXPIRY_CUTOFF_TS   # first expiry on/after the day after EXIT
    after=[e for e in exps if e>=cutoff]
    if not after: return out
    e1=after[0]
    ch=o if o["options"] and o["options"][0]["expirationDate"]==e1 else chain_at(s,e1)
    if ch: 
        a=atm(ch,spot); out["e1"]=e1; out["atm"]=a
        # total option activity: call/put volume ratio on that expiry
        try:
            cv=sum((x.get("volume") or 0) for x in ch["options"][0]["calls"]); pv=sum((x.get("volume") or 0) for x in ch["options"][0]["puts"])
            out["cv"]=cv; out["pv"]=pv
        except Exception: pass
    # implied earnings move: first expiry after earnings date
    r=R[s]
    ed=[x[0] for x in (r["e"] or []) if config.WIDE_START<=x[0]<=config.WIDE_END]
    if ed:
        d0=dt.datetime.strptime(ed[0],"%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
        t0=int((d0+dt.timedelta(days=1)).timestamp())
        ex=[e for e in exps if e>=t0]
        if ex:
            c2=o if o["options"] and o["options"][0]["expirationDate"]==ex[0] else chain_at(s,ex[0])
            if c2:
                a2=atm(c2,spot); out["eexp"]=ex[0]; out["eatm"]=a2
    return out
res={}
with ThreadPoolExecutor(10) as ex:
    for i,o in enumerate(ex.map(work,cands)):
        res[o["sym"]]=o
        if i%50==0: print(i,flush=True)
if ONLY:
    try: base=pickle.load(open("engine.pkl","rb"))
    except Exception: base={}
    base.update(res); res=base
pickle.dump(res,open("engine.pkl","wb"))
print("done",len(res), sum(1 for v in res.values() if v.get("atm")))
