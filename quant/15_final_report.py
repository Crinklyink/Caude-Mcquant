import sys, json, pickle, numpy as np, warnings
from math import log, sqrt, erf
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
import mc, mc7
def N(x): return 0.5*(1+erf(x/sqrt(2)))
RD={"AXTI":3,"FSLY":7,"DOCN":5,"HUT":6,"ALAB":6,"PLTR":5,"ICHR":5}
IV6={"AXTI":1.34,"FSLY":1.48,"DOCN":1.26,"HUT":1.11}
IV30={"AXTI":1.78,"FSLY":0.89,"DOCN":0.92,"HUT":0.98}
T=7/252
names=["AXTI","FSLY","DOCN","HUT"]
print(f'{"sym":5}{"close":>8}{"atr$":>6}{"atr%":>5}{"stop":>8}{"stop%":>6}{"RR":>5}{"tgt+6":>8} | IV  fTouch fStop fTgt1st fHold | mcTouch mcT1st mcS1st mcSold>=6 | base7 | impEv% histEv% | sh@6k  cost')
tot=0
for s in names:
    T_,O,C,Hh,L=mc.load(s); p=C[-1]
    tr=np.maximum(Hh[1:]-L[1:],np.maximum(abs(Hh[1:]-C[:-1]),abs(L[1:]-C[:-1]))); atr=tr[-14:].mean()
    stop=p-1.5*atr; ds=log(p/stop); sig=IV6[s]*sqrt(T)
    ft=2*N(-log(1.06)/sig); fs=2*N(-ds/sig); tf=ds/(ds+log(1.06)); fh=N(-log(1.06)/sig)
    r=mc7.run7(s,1.5*atr/p,RD[s],N=30000); b,bh=mc7.base7(s)
    ev=mc7.moves(s); hav=np.mean([abs(m[2]) for m in ev])
    evv=(IV30[s]**2*3/252-0.85**2*2/252) if s=="AXTI" else IV6[s]**2*8/252-IV30[s]**2*7/252
    imp=0.7979*sqrt(max(evv,0)); sh=int(6000//p); cost=sh*p; tot+=cost
    print(f'{s:5}{p:8.2f}{atr:6.2f}{atr/p*100:5.1f}{stop:8.2f}{(1-stop/p)*100:6.1f}{0.06/(1-stop/p):5.2f}{p*1.06:8.2f} | {IV6[s]*100:3.0f} {ft*100:6.0f}% {fs*100:4.0f}% {tf*100:6.0f}% {fh*100:5.0f}% | {r["touch"]*100:6.0f}% {r["tfirst"]*100:6.0f}% {r["stopfirst"]*100:6.0f}% {r["hold"]*100:8.0f}% | {b*100:4.0f}%/{bh*100:3.0f}% | {imp*100:5.1f} {hav*100:7.1f} | {sh:4d} {cost:9.2f}')
print("total",round(tot,2),"cash left",round(24000-tot,2))
syms,cum,EV,RDj=pickle.load(open("joint.pkl","rb")); ix={s:i for i,s in enumerate(syms)}
erfv=np.vectorize(erf); grid=np.linspace(-1,3,4001)
def basket(nm,tag):
    c=[ix[n] for n in nm]; P=lambda d:(cum[d][:,c]-1).mean(1)
    r1,r2,r3,r7=P(1),P(2),P(3),P(7)
    q=np.percentile(r7,[5,25,50,75,95])
    wins=[]
    for sd in (0.04,0.05,0.08):
        tab=0.8*0.5*(1+erfv(grid/sd/sqrt(2)))+0.2*0.5*(1+erfv(grid/(3*sd)/sqrt(2)))
        wins.append([np.mean(np.interp(r7[:20000],grid,tab)**Nn)*100 for Nn in (30,60,100)])
    print(f"\n{tag}: {'/'.join(nm)}")
    print("  pctl 5/25/50/75/95:",np.round(q*100,1)," P(>=5/10/15/20/25):",[round(np.mean(r7>=t)*100,1) for t in (.05,.10,.15,.20,.25)]," P(<=-10/-20/-30):",[round(np.mean(r7<=t)*100,1) for t in (-.10,-.20,-.30)])
    print("  up d1/d2/d3/Thu:",[round(np.mean(x>0)*100,1) for x in (r1,r2,r3,r7)]," all(d1,d2,Thu):",round(np.mean((r1>0)&(r2>0)&(r7>0))*100,1)," day1 p10/p90:",np.round(np.percentile(r1,[10,90])*100,1)," day2:",np.round(np.percentile(r2,[10,90])*100,1))
    for sd,w in zip((4,5,8),wins): print(f"  P(win) field sd {sd}%: N30/60/100 = {np.round(w,1)}")
basket(["AXTI","FSLY","DOCN","HUT"],"NEW (quality-passing)")
basket(["AXTI","FSLY","PLTR","ALAB"],"PREVIOUS")
basket(["AXTI","FSLY","ICHR","HUT"],"NEW alt (top raw)")
basket(["AXTI","FSLY","DOCN","W"],"NEW diversified alt")
# correlation of 60d regime among the new four
H=json.load(open("hist.json"))
def rets(s):
    d=H[s]; c=[(t,x) for t,x in zip(d["t"],d["c"]) if x is not None]
    return {t:np.log(c[i][1]/c[i-1][1]) for i,(t,_) in enumerate(c) if i>0}
R={s:rets(s) for s in names+["SPY"]}
common=sorted(set.intersection(*[set(R[s]) for s in R]))[-60:]
M=np.array([[R[s][t] for t in common] for s in names+["SPY"]]); C=np.corrcoef(M)
print("\n60d corr:"); print("      "+" ".join(f"{s:>5}" for s in names+["SPY"]))
for i,s in enumerate(names+["SPY"]): print(f"{s:5} "+" ".join(f"{C[i][j]:5.2f}" for j in range(len(names)+1)))
