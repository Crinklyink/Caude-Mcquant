import pickle, itertools, numpy as np, warnings
from math import erf, sqrt
warnings.filterwarnings("ignore")
syms,cum,EV,RD=pickle.load(open("joint.pkl","rb")); ix={s:i for i,s in enumerate(syms)}
Q={r[0]:r[1] for r in pickle.load(open("quality.pkl","rb"))}
R7=(cum[-1]-1)[:20000]   # last day = exit.astype(np.float32)
grid=np.linspace(-1,3,4001); erfv=np.vectorize(erf)
def mk(sd): return (0.8*0.5*(1+erfv(grid/sd/sqrt(2)))+0.2*0.5*(1+erfv(grid/(3*sd)/sqrt(2)))).astype(np.float32)
T5,T8=mk(0.05),mk(0.08)
def pw(r,T,N): return float(np.mean(np.interp(r,grid,T)**N))
ok=[s for s in syms if not Q[s]]
# prefilter by single-name upside tail to keep search tractable
sc={s:np.mean(R7[:,ix[s]]>=.15) for s in ok}
top=sorted(ok,key=lambda s:-sc[s])[:34]
print("search set (34):",top)
out=[]
for c in itertools.combinations([ix[s] for s in top],4):
    r=R7[:,c].mean(1)
    out.append((c,pw(r,T5,30),pw(r,T8,30),pw(r,T5,100),float(np.mean(r<=-.2)),float(np.mean(r<=-.3)),float(np.mean(r>=.10))))
out.sort(key=lambda t:-t[1]); pickle.dump(out[:500],open("win5.pkl","wb"))
def show(r,tag=""):
    print(f'{"/".join(syms[i] for i in r[0]):26} P(win) N30sd5={r[1]*100:4.1f} N30sd8={r[2]*100:4.1f} N100sd5={r[3]*100:4.1f} | P<=-20={r[4]*100:4.1f} P<=-30={r[5]*100:4.1f} P>=10={r[6]*100:4.1f} {tag}')
print("\nTOP 15 (quality-passing names only):")
for r in out[:15]: show(r)
# prior basket and variants for reference (compute directly)
for nm in (["AXTI","FSLY","PLTR","ALAB"],["AXTI","FSLY","PLTR","W"],["AXTI","FSLY","ALAB","SMCI"]):
    c=[ix[n] for n in nm]; r=R7[:,c].mean(1)
    show((c,pw(r,T5,30),pw(r,T8,30),pw(r,T5,100),float(np.mean(r<=-.2)),float(np.mean(r<=-.3)),float(np.mean(r>=.10))),"<- reference (not all pass filter)")
# single-name table for search set
print("\nsearch-set single names: P(R7>=+15) / P(R7<=-15) / event day:")
for s in top[:34]:
    x=R7[:,ix[s]]; print(f"{s:5} {np.mean(x>=.15)*100:4.1f} {np.mean(x<=-.15)*100:4.1f} rd={RD[s]}")
