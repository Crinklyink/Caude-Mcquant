import json, pickle, datetime as dt, numpy as np, warnings
warnings.filterwarnings("ignore")
H=json.load(open("hist.json")); rows=pickle.load(open("rows.pkl","rb"))
out=[]
for r in rows:
    if not r["e"]: continue
    ds=[x for x in r["e"] if "2026-10-12"<=x[0]<="2026-10-26"]
    if not ds: continue
    s=r["sym"]; d=H[s]
    idx=[i for i,x in enumerate(d["c"]) if x is not None]
    T=[dt.datetime.fromtimestamp(d["t"][i],dt.timezone.utc).date() for i in idx]
    C=[d["c"][i] for i in idx]; O=[d["o"][i] for i in idx]; Hh=[d["h"][i] for i in idx]; L=[d["l"][i] for i in idx]
    ed=dt.datetime.strptime(ds[0][0],"%Y-%m-%d").date()
    i=next((k for k,x in enumerate(T) if x>=ed),None)
    if i is None or i+1>=len(T): continue
    gD=O[i]/C[i-1]-1; gN=O[i+1]/C[i]-1
    if abs(gN)>abs(gD) and i+1<len(T)-0: j=i+1; pre=C[i]
    else: j=i; pre=C[i-1]
    react=C[j]/pre-1
    if react>=0.05:
        low_since=min(L[j:]); 
        out.append((s,ed.isoformat(),react,C[-1]/C[j]-1,C[-1]/pre-1,(len(T)-1-j),r["pct_hi"],r["adv"],r["cap"],r["atrp"]))
out.sort(key=lambda x:-x[2])
print("sym   rep-date  reaction  sinceReact  sinceTotal  daysSince  hi  adv$M cap$B atr%")
for o in out[:40]:
    print(f"{o[0]:6}{o[1]} {o[2]*100:7.1f}% {o[3]*100:8.1f}% {o[4]*100:8.1f}% {o[5]:4d} {o[6]*100:7.1f} {o[7]/1e6:7.0f} {o[8]/1e9:6.1f} {o[9]*100:5.1f}")
