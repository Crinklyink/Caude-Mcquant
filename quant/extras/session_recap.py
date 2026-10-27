import sys, json, datetime as dt, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
import yf
from concurrent.futures import ThreadPoolExecutor
names="SPY QQQ IWM AXTI FSLY ALAB PLTR W TEAM HALO SN ARQT PBF CVI TENB SMCI ZETA GRAL LEU U COHR ARM TSEM DDOG HOOD STX SLDE INTA MANH LITE APP COIN UPST SEDG RUN INTC ADPT MSTR".split()
def one(s):
    try:
        u=f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=1d&interval=5m&includePrePost=true"
        r=json.loads(yf.get(u))["chart"]["result"][0]; m=r["meta"]
        ts=r["timestamp"]; q=r["indicators"]["quote"][0]
        reg=[(t,o,h,l,c) for t,o,h,l,c in zip(ts,q["open"],q["high"],q["low"],q["close"]) if c is not None and m["currentTradingPeriod"]["regular"]["start"]<=t<m["currentTradingPeriod"]["regular"]["end"]]
        post=[(t,c) for t,c in zip(ts,q["close"]) if c is not None and t>=m["currentTradingPeriod"]["regular"]["end"]]
        prev=m.get("chartPreviousClose")
        op=reg[0][1]; cl=reg[-1][4]; hi=max(x[2] for x in reg); lo=min(x[3] for x in reg)
        ah=post[-1][1] if post else None; aht=dt.datetime.fromtimestamp(post[-1][0],dt.timezone.utc).strftime("%H:%M") if post else None
        return s,dict(prev=prev,open=op,close=cl,hi=hi,lo=lo,ah=ah,aht=aht)
    except Exception as e:
        return s,{"err":str(e)[:60]}
with ThreadPoolExecutor(8) as ex: res=dict(ex.map(one,names))
json.dump(res,open("today.json","w"))
print(f'{"sym":5}{"prevC":>9}{"open":>9}{"close":>9}{"gap%":>6}{"o->c%":>7}{"c->c%":>7}{"hi%":>6}{"lo%":>6}{"AH px":>9}{"AH%":>6} AH utc')
for s in names:
    d=res[s]
    if "err" in d: print(s,d); continue
    p=d["prev"]
    ah=("%9.2f"%d["ah"]) if d["ah"] else "      n/a"
    ahp=("%6.1f"%((d["ah"]/d["close"]-1)*100)) if d["ah"] else "   n/a"
    print(f'{s:5}{p:9.2f}{d["open"]:9.2f}{d["close"]:9.2f}{(d["open"]/p-1)*100:6.1f}{(d["close"]/d["open"]-1)*100:7.1f}{(d["close"]/p-1)*100:7.1f}{(d["hi"]/p-1)*100:6.1f}{(d["lo"]/p-1)*100:6.1f}{ah}{ahp} {d["aht"]}')
