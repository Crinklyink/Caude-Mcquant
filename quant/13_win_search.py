"""Best 4-name equal-dollar baskets by P(finishing first), under the selection rules:
quality filter passed (12), fewer than 2 red-team flags (12b), at most one name per industry.
Also prints the best baskets ignoring the rules, so you can see what the rules cost.
Set QUANT_PREV=AAA,BBB,CCC,DDD to score the previous pick for comparison, and QUANT_EXCLUDE=AAA,BBB to drop names
the manual checks cut (pre-announced quarter, deal pending, unconfirmed date...). Writes win5.pkl (rule-following baskets).
"""
import os, pickle, itertools, numpy as np, warnings
from math import erf, sqrt
warnings.filterwarnings("ignore")
syms,cum,EV,RD=pickle.load(open("joint.pkl","rb")); ix={s:i for i,s in enumerate(syms)}
Q={r[0]:r[1] for r in pickle.load(open("quality.pkl","rb"))}
RT=pickle.load(open("redteam.pkl","rb"))
R7=(cum[-1]-1)[:20000]   # last day = exit
grid=np.linspace(-1,3,4001); erfv=np.vectorize(erf)
def mk(sd): return (0.8*0.5*(1+erfv(grid/sd/sqrt(2)))+0.2*0.5*(1+erfv(grid/(3*sd)/sqrt(2)))).astype(np.float32)
T5,T8=mk(0.05),mk(0.08)
def pw(r,T,N): return float(np.mean(np.interp(r,grid,T)**N))
def score(c):
    r=R7[:,list(c)].mean(1)
    return (tuple(c),pw(r,T5,30),pw(r,T8,30),pw(r,T5,100),float(np.mean(r<=-.2)),float(np.mean(r<=-.3)),float(np.mean(r>=.10)))
def show(r,tag=""):
    print(f'{"/".join(syms[i] for i in r[0]):26} P(win) N30sd5={r[1]*100:4.1f} N30sd8={r[2]*100:4.1f} N100sd5={r[3]*100:4.1f} | P<=-20={r[4]*100:4.1f} P<=-30={r[5]*100:4.1f} P>=10={r[6]*100:4.1f} {tag}')
tail=lambda s: np.mean(R7[:,ix[s]]>=.15)   # single-name upside tail, used to keep the search tractable

quality=[s for s in syms if not Q.get(s)]
manual=[s for s in os.environ.get("QUANT_EXCLUDE","").split(",") if s]
elig=[s for s in quality if s in RT and len(RT[s]["flags"])<2 and s not in manual]
print("quality-passing:",len(quality),"| also <2 red-team flags and not excluded by hand:",len(elig),"| excluded by hand:",manual)
print("cut by red team:",{s:RT[s]["flags"] for s in quality if s in RT and len(RT[s]["flags"])>=2})
top=sorted(elig,key=lambda s:-tail(s))[:30]
ind={s:RT[s]["ind"] for s in top}
out=[score(c) for c in itertools.combinations([ix[s] for s in top],4) if len({ind[syms[i]] for i in c})==4]
out.sort(key=lambda t:-t[1])
# differences under half a point are noise: among those, take the basket with the fewest red-team flags
nflags=lambda r: sum(len(RT[syms[i]]["flags"]) for i in r[0])
if out:
    tied=[r for r in out if out[0][1]-r[1]<=0.005]
    best=min(tied,key=lambda r:(nflags(r),-r[1])); out.remove(best); out.insert(0,best)
pickle.dump(out[:500],open("win5.pkl","wb"))
print(f"\nTOP 15 following the rules ({len(out)} baskets searched; first = pick, chosen by fewest flags among ties):")
for r in out[:15]: show(r,f"flags={nflags(r)}")

raw=sorted(quality,key=lambda s:-tail(s))[:30]
best_raw=sorted((score(c) for c in itertools.combinations([ix[s] for s in raw],4)),key=lambda t:-t[1])[:3]
print("\nbest ignoring red team and industry rules (reference only):")
for r in best_raw: show(r)
prev=[s for s in os.environ.get("QUANT_PREV","").split(",") if s]
if prev:
    if all(s in ix for s in prev): show(score([ix[s] for s in prev]),"<- previous pick")
    else: print("previous pick not scorable here (not in the pool):",[s for s in prev if s not in ix])

print("\nsearch-set single names: P(+15% or more) / P(-15% or worse) / reaction session / industry:")
for s in top:
    x=R7[:,ix[s]]; print(f"{s:5} {np.mean(x>=.15)*100:4.1f} {np.mean(x<=-.15)*100:4.1f} rd={RD[s]}  {ind[s]}")
