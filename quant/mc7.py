import sys, json, pickle, datetime as dt, numpy as np, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
import ehist, mc
from concurrent.futures import ThreadPoolExecutor
HZ=7
IDX={"2026-10-28":1,"2026-10-29":2,"2026-10-30":3,"2026-11-02":4,"2026-11-03":5,"2026-11-04":6,"2026-11-05":7}
TDAYS=["2026-10-27","2026-10-28","2026-10-29","2026-10-30","2026-11-02","2026-11-03","2026-11-04","2026-11-05","2026-11-06","2026-11-09"]
def rd7(x):
    """reaction day index inside the Oct28-Nov5 window; None if before/at entry or after exit"""
    if not x["e"]: return None,"none"
    d,tm=x["e"][0][0],x["e"][0][1]
    if d not in TDAYS: return None,"none"
    i=TDAYS.index(d)
    ri = i if "pre" in tm else i+1   # index into TDAYS of reaction day
    if ri>=len(TDAYS): return None,"after"
    rdate=TDAYS[ri]
    if rdate=="2026-10-27": return None,"before"
    if rdate=="2026-10-28": return None,"atopen"   # reaction is the entry-open gap
    if rdate in IDX: return IDX[rdate],"in"
    return None,"after"   # Nov 6 or later
CACHE={}
def moves(s):
    if s not in CACHE: CACHE[s]=ehist.moves(s,10)
    return CACHE[s]
def run7(s,stop_pct,rd,N=20000,seed=11):
    rng=np.random.default_rng(seed)
    T,O,C,Hh,L=mc.load(s)
    ev=moves(s); evdays=set(); absm=[]
    for (rdt,tim,mv,sp) in ev:
        i=next((k for k,x in enumerate(T) if x>=rdt),None)
        if i is None: continue
        j=i+1 if tim=="AMC" else i
        if j<len(T): evdays.add(j); evdays.add(j+1); absm.append(abs(mv))
    ret=C[1:]/C[:-1]-1; hr=Hh[1:]/C[:-1]-1; lr=L[1:]/C[:-1]-1
    mask=np.array([(k+1) not in evdays for k in range(len(ret))])
    ret,hr,lr=ret[mask],hr[mask],lr[mask]
    mu=ret.mean(); ret=ret-mu; hr=hr-mu; lr=lr-mu
    eh=np.maximum(hr-np.maximum(ret,0),0); el=np.maximum(np.minimum(ret,0)-lr,0); n=len(ret)
    P=np.ones(N); done=np.zeros(N,bool); tfirst=np.zeros(N,bool); stopped=np.zeros(N,bool); touch=np.zeros(N,bool); stoptouch=np.zeros(N,bool)
    for t in range(1,HZ+1):
        if rd==t and absm:
            m=rng.choice(absm,N)*rng.choice([-1,1],N); k=rng.integers(0,n,N)
            r=m; h=np.maximum(m,0)+eh[k]; l=np.minimum(m,0)-el[k]
        else:
            k=rng.integers(0,n,N); r=ret[k]; h=hr[k]; l=lr[k]
        hi=P*(1+h); lo=P*(1+l); th=hi>=1.06; sl=lo<=1-stop_pct
        nd=~done
        tfirst|=nd&th&~sl; stopped|=nd&sl; touch|=th; stoptouch|=sl; done|=(th|sl)
        P=P*(1+r)
    return dict(touch=touch.mean(),tfirst=tfirst.mean(),stopfirst=(stopped&~tfirst).mean(),stoptouch=stoptouch.mean(),
                hold=(P>=1.06).mean(),exit_pos=(P>1).mean(),exit_med=float(np.median(P)-1),sd=float(np.std(np.log(P))),absm=float(np.mean(absm)) if absm else None,nev=len(absm))
def base7(s,span=504):
    T,O,C,Hh,L=mc.load(s); n=len(C); hit=0;tot=0;hold=0
    for i in range(max(0,n-span-HZ-1),n-HZ-1):
        tot+=1
        if Hh[i+1:i+1+HZ].max()>=1.06*C[i]: hit+=1
        if C[i+HZ]>=1.06*C[i]: hold+=1
    return hit/tot, hold/tot
def evwin(s,rd):
    T,O,C,Hh,L=mc.load(s); res=[]
    for (rdt,tim,mv,sp) in moves(s):
        i=next((q for q,x in enumerate(T) if x>=rdt),None)
        if i is None: continue
        j=i+1 if tim=="AMC" else i; st=j-rd
        if st<0 or st+HZ>=len(T): continue
        res.append((Hh[st+1:st+1+HZ].max()/C[st]-1, C[st+HZ]/C[st]-1))
    return res
if __name__=="__main__":
    S=pickle.load(open("ranked.pkl","rb"))
    def one(x):
        s=x["s"]
        try:
            rd,kind=rd7(x)
            r=run7(s,1.5*x["atr"]/x["p"],rd)
            b,bh=base7(s)
            ew=evwin(s,rd) if rd else []
            return s,dict(rd=rd,kind=kind,mc=r,base=b,basehold=bh,ev=(sum(1 for e in ew if e[0]>=0.06),sum(1 for e in ew if e[1]>=0.06),len(ew)))
        except Exception as e:
            return s,dict(err=str(e))
    out={}
    with ThreadPoolExecutor(6) as ex:
        for i,(s,o) in enumerate(ex.map(one,S)):
            out[s]=o
            if i%60==0: print(i,flush=True)
    pickle.dump(out,open("mc7.pkl","wb")); print("done",len(out),sum(1 for v in out.values() if "err" in v))
