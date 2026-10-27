import pickle, numpy as np, warnings
from math import erf, sqrt, comb
warnings.filterwarnings("ignore")
syms,cum,EV,RD=pickle.load(open("joint.pkl","rb")); ix={s:i for i,s in enumerate(syms)}
erfv=np.vectorize(erf)
def Phi(x): return 0.5*(1+erfv(x/sqrt(2)))
def R7(names,w):
    c=[ix[n] for n in names]; w=np.array(w,float); w/=w.sum()
    return (cum[7][:,c]-1)@w
strats={
 "A current 4 (AXTI/FSLY/PLTR/W eq)":(["AXTI","FSLY","PLTR","W"],[1,1,1,1]),
 "B top-vol 4 (AXTI/FSLY/GRAL/LEU eq)":(["AXTI","FSLY","GRAL","LEU"],[1,1,1,1]),
 "C two names (FSLY+AXTI 50/50)":(["FSLY","AXTI"],[1,1]),
 "D one name (FSLY 100%)":(["FSLY"],[1]),
 "E tilted (FSLY40 AXTI30 PLTR20 W10)":(["FSLY","AXTI","PLTR","W"],[.4,.3,.2,.1]),
 "F conservative (PLTR/W/ZETA/DDOG eq)":(["PLTR","W","ZETA","DDOG"],[1,1,1,1]),
}
def field_cdf(r,sd):
    return 0.8*Phi(r/sd)+0.2*Phi(r/(3*sd))     # fat-tailed field: 20% of students swing 3x
def pwin(r,N,sd):
    F=np.clip(field_cdf(r,sd),0,1); return np.mean(F**N)
def ptop3(r,N,sd):
    F=np.clip(field_cdf(r,sd),1e-12,1); G=1-F
    p=sum(comb(N,k)*G**k*F**(N-k) for k in range(3)); return np.mean(p)
NP=cum.shape[1]; sub=slice(0,20000)
print("field sd = typical student 7d return spread (some fat tails). N=class size")
for sd in (0.05,0.08):
    print(f"\n=== field sd {sd*100:.0f}% ===")
    print(f'{"strategy":40} {"sd7":>5} {"P(<=-20)":>8} {"P(<=-30)":>8} | P(win)  N=10   30   100  300 | P(top3) N=30  100')
    for name,(ns,w) in strats.items():
        r=R7(ns,w)[sub]
        row=[pwin(r,N,sd)*100 for N in (10,30,100,300)]
        t3=[ptop3(r,N,sd)*100 for N in (30,100)]
        print(f'{name:40} {r.std()*100:5.1f} {np.mean(r<=-.2)*100:8.1f} {np.mean(r<=-.3)*100:8.1f} |       {row[0]:5.1f} {row[1]:5.1f} {row[2]:5.1f} {row[3]:5.1f} |       {t3[0]:5.1f} {t3[1]:5.1f}')
# what return does it take to win?
print("\nreturn needed to beat the whole field (median of the field's best):")
rng=np.random.default_rng(3)
for sd in (0.05,0.08):
    for N in (10,30,100,300):
        k=rng.random((4000,N)); 
        # sample from the mixture
        z=rng.standard_normal((4000,N)); sc=np.where(rng.random((4000,N))<0.8,1,3)
        best=(z*sc*sd).max(1)
        print(f"  field sd {sd*100:.0f}%, N={N:3d}: median winning return {np.median(best)*100:5.1f}%  (25th-75th: {np.percentile(best,25)*100:.1f} to {np.percentile(best,75)*100:.1f})")
