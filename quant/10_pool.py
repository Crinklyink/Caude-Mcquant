import pickle, json, datetime as dt, numpy as np, warnings
warnings.filterwarnings("ignore")
rows=pickle.load(open("rank7.pkl","rb")); eng=pickle.load(open("engine.pkl","rb"))
def est_flag(s):
    qs=(eng.get(s) or {}).get("qs") or {}
    try:
        ce=qs["calendarEvents"]["earnings"]; return ce.get("isEarningsDateEstimate")
    except Exception: return None
pool=[]
for sym,sc,x,m,r,kind,rd in rows:
    if x["adv"]<40e6: continue
    if x["p"]<7: continue
    # exclude suspected deal-pinned: very low ATR relative to IV/trend or known
    if sym in("BWIN","RXO","SGRY"): continue
    ok_event = (kind=="in")
    hv = r["touch"]>=0.55
    if ok_event and hv:
        pool.append((sym,x,m,r,rd,est_flag(sym)))
print(len(pool))
print(f'{"sym":6}{"sec":>11}{"p":>8}{"rd":>3}{"estDate":>8}{"mcT":>5}{"sd7":>6}{"evAvg":>6}{"nEv":>4}{"atr%":>5}{"cap$B":>7}{"adv$M":>7}{"d50":>6}{"hi":>6}')
for sym,x,m,r,rd,ef in sorted(pool,key=lambda t:-t[3]["touch"]):
    print(f'{sym:6}{(x["sec"] or "")[:10]:>11}{x["p"]:8.2f}{rd:3d}{str(ef):>8}{r["touch"]*100:5.0f}{r["sd"]*100:6.1f}{(r["absm"] or 0)*100:6.1f}{r["nev"]:4d}{x["atrp"]*100:5.1f}{x["cap"]/1e9:7.1f}{x["adv"]/1e6:7.0f}{x["d50"]*100:6.1f}{x["hi"]*100:6.1f}')
pickle.dump([(s,rd,ef) for s,x,m,r,rd,ef in pool],open("pool.pkl","wb"))
