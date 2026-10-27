import sys, json, pickle, datetime as dt, numpy as np, itertools, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
import ehist
H=json.load(open("hist.json"))
pool=pickle.load(open("pool.pkl","rb"))
S={x["s"]:x for x in pickle.load(open("ranked.pkl","rb"))}
syms=[p[0] for p in pool]; RD={p[0]:p[1] for p in pool}
HZ=7
# ---- aligned matrices (last 480 sessions of SPY dates)
def series(s):
    d=H[s]; return {t:(o,c) for t,o,c in zip(d["t"],d["o"],d["c"]) if o is not None and c is not None}
spy=series("SPY"); dates=sorted(spy)[-481:]
A={s:series(s) for s in syms}
ok=[s for s in syms if all(t in A[s] for t in dates)]
print("aligned",len(ok),"of",len(syms),"dropped",[s for s in syms if s not in ok])
syms=ok
D=len(dates)-1
RC=np.zeros((D,len(syms))); ROC=np.zeros((D,len(syms)))
for j,s in enumerate(syms):
    for i in range(D):
        t0,t1=dates[i],dates[i+1]
        RC[i,j]=A[s][t1][1]/A[s][t0][1]-1
        ROC[i,j]=A[s][t1][1]/A[s][t1][0]-1
dd=[dt.datetime.fromtimestamp(t,dt.timezone.utc).date() for t in dates[1:]]
# ---- earnings moves and masking
rng=np.random.default_rng(5)
EV={}
for j,s in enumerate(syms):
    mv=ehist.moves(s,10); EV[s]=[abs(m[2]) for m in mv]
    bad=set()
    for (rdt,tim,m,sp) in mv:
        k=next((q for q,x in enumerate(dd) if x>=rdt),None)
        if k is None: continue
        r0=k+1 if tim=="AMC" else k
        for q in (r0,r0+1):
            if 0<=q<D: bad.add(q)
    good=np.array([q for q in range(D) if q not in bad])
    for q in bad:
        g=rng.choice(good); RC[q,j]=RC[g,j]; ROC[q,j]=ROC[g,j]
mu=RC.mean(0); RC=RC-mu; ROC=ROC-ROC.mean(0)
print("pool:",syms)
# ---- simulate: shared date draws -> preserves cross-correlation
NP=40000
idx=rng.integers(0,D,size=(NP,HZ))
cum=np.zeros((HZ+1,NP,len(syms)))   # cumulative gross return path (value of 1 invested)
val=np.ones((NP,len(syms)))
for d in range(1,HZ+1):
    r=(ROC if d==1 else RC)[idx[:,d-1]]   # day1 = open->close
    r=r.copy()
    for j,s in enumerate(syms):
        if RD[s]==d and EV[s]:
            m=rng.choice(EV[s],NP)*rng.choice([-1,1],NP)
            r[:,j]=m
    val=val*(1+r)
    cum[d]=val
pickle.dump((syms,cum,EV,RD),open("joint.pkl","wb"))
print("sim done",cum.shape)
