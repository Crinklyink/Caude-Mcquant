import pickle, json, datetime as dt, numpy as np, warnings
warnings.filterwarnings("ignore")
rows=pickle.load(open("rank7.pkl","rb")); eng=pickle.load(open("engine.pkl","rb"))
def est_flag(s):
    qs=(eng.get(s) or {}).get("qs") or {}
    try:
        ce=qs["calendarEvents"]["earnings"]; return ce.get("isEarningsDateEstimate")
    except Exception: return None
pool=[]; n_in=n_liquid=0
for sym,sc,x,m,r,kind,rd in rows:
    ok_event = (kind=="in")
    n_in+=ok_event
    if x["adv"]<40e6: continue
    if x["p"]<7: continue
    # exclude suspected deal-pinned: very low ATR relative to IV/trend or known
    if sym in("BWIN","RXO","SGRY"): continue
    n_liquid+=ok_event
    hv = r["touch"]>=0.55
    if ok_event and hv:
        pool.append((sym,x,m,r,rd,est_flag(sym)))
print(len(pool))
if not pool:   # an empty pool used to end in "no basket passes the rules" with no reason given
    import sys
    why = ("no earnings reaction falls inside the trade window: check the calendar step (03)" if not n_in else
           f"{n_in} names react inside the window, {n_liquid} of them liquid (ADV >= $40M, price >= $7), none with "
           "simulated P(touch +6%) >= 55%; windows of 1-3 sessions rarely reach it")
    print(f"WARN pool: empty - {why}", file=sys.stderr)
print(f'{"sym":6}{"sec":>11}{"p":>8}{"rd":>3}{"estDate":>8}{"mcT":>5}{"sd7":>6}{"evAvg":>6}{"nEv":>4}{"atr%":>5}{"cap$B":>7}{"adv$M":>7}{"d50":>6}{"hi":>6}')
for sym,x,m,r,rd,ef in sorted(pool,key=lambda t:-t[3]["touch"]):
    print(f'{sym:6}{(x["sec"] or "")[:10]:>11}{x["p"]:8.2f}{rd:3d}{str(ef):>8}{r["touch"]*100:5.0f}{r["sd"]*100:6.1f}{(r["absm"] or 0)*100:6.1f}{r["nev"]:4d}{x["atrp"]*100:5.1f}{x["cap"]/1e9:7.1f}{x["adv"]/1e6:7.0f}{x["d50"]*100:6.1f}{x["hi"]*100:6.1f}')
pickle.dump([(s,rd,ef) for s,x,m,r,rd,ef in pool],open("pool.pkl","wb"))
