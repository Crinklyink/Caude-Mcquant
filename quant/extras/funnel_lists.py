import pickle, numpy as np
rows=pickle.load(open("rows.pkl","rb"))
def fmt(r):
    e=r["e"][0] if r["e"] else None
    return f'{r["sym"]:6} p={r["p"]:8.2f} cap={r["cap"]/1e9:6.1f}B adv={r["adv"]/1e6:7.0f}M atr%={r["atrp"]*100:4.1f} r21={r["r21"]*100:6.1f} rs63={r["rs63"]*100:6.1f} hi={r["pct_hi"]*100:6.1f} 50d={(r["p"]/r["sma50"]-1)*100:5.1f} 200d={(r["p"]/r["sma200"]-1)*100:6.1f} br={r["br"]*100:4.0f} ret1={r["ret1"]*100:5.1f} E={e[0] if e else "-"} {e[1][5:9] if e else ""}'
inwin=[r for r in rows if r["e"] and any("2026-10-27"<=x[0]<="2026-11-09" for x in r["e"])]
print("in-window earnings, liquid cap>1B:",len(inwin))
# A: earnings in window with strength
A=[r for r in inwin if r["p"]>r["sma50"] and r["p"]>r["sma200"] and r["rs63"]>0.0 and r["pct_hi"]>-0.12]
A.sort(key=lambda r:-r["rs63"])
print("\n== A: earnings in window + uptrend (p>50,200d, RS>0, within 12% of high)", len(A))
for r in A[:45]: print(fmt(r))
# B: recent earnings gappers
rec=[r for r in rows if r["e"] and any("2026-10-12"<=x[0]<="2026-10-26" for x in r["e"])]
B=[r for r in rec if r["p"]>r["sma50"] and r["pct_hi"]>-0.08 and r["r21"]>0.05]
B.sort(key=lambda r:-r["r21"])
print("\n== B: reported Oct12-26, strong since", len(B))
for r in B[:30]: print(fmt(r))
# C: RS leaders near highs, not earnings in window
C=[r for r in rows if r["rs63"]>0.15 and r["pct_hi"]>-0.04 and r["p"]>r["sma50"]>r["sma200"]]
C.sort(key=lambda r:-r["rs63"])
print("\n== C: RS leaders at highs", len(C))
for r in C[:40]: print(fmt(r))
