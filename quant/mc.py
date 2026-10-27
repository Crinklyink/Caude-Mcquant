import sys, json, datetime as dt, numpy as np, warnings, pickle
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
import ehist
H=json.load(open("hist.json"))
RD={"TENB":3,"TEAM":9,"PLTR":6,"QLYS":7,"PAYC":8,"CVI":6,"PBF":3,"APA":8,"HALO":9,"AMN":9,"HAS":None,"LMT":None,"FIGS":9,"DXC":4,"RBRK":None,"MPC":6,"TALO":6,"INTA":2,"PSX":2,"DINO":2}
rng=np.random.default_rng(7)
def load(s):
    d=H[s]; idx=[i for i,x in enumerate(d["c"]) if x is not None and d["h"][i] is not None and d["l"][i] is not None and d["o"][i] is not None]
    T=[dt.datetime.fromtimestamp(d["t"][i],dt.timezone.utc).date() for i in idx]
    return T,*[np.array([d[k][i] for i in idx],float) for k in "ochl"]
def run(s,stop_pct,N=40000):
    T,O,C,Hh,L=load(s)
    ev=ehist.moves(s,10)
    evdays=set()
    absm=[]
    for (rd,tim,mv,sp) in ev:
        # reaction day index
        i=next((k for k,x in enumerate(T) if x>=rd),None)
        if i is None: continue
        j=i+1 if tim=="AMC" else i
        if j<len(T): evdays.add(j); evdays.add(j+1); absm.append(abs(mv))
    ret=C[1:]/C[:-1]-1; hr=Hh[1:]/C[:-1]-1; lr=L[1:]/C[:-1]-1
    mask=np.array([ (k+1) not in evdays for k in range(len(ret))])
    ret,hr,lr=ret[mask],hr[mask],lr[mask]
    mu=ret.mean(); ret=ret-mu; hr=hr-mu; lr=lr-mu
    eh=np.maximum(hr-np.maximum(ret,0),0); el=np.maximum(np.minimum(ret,0)-lr,0)
    n=len(ret)
    rd=RD.get(s)
    P=np.ones(N); touch=np.zeros(N,bool); stopped=np.zeros(N,bool); first_t=np.zeros(N,bool); done=np.zeros(N,bool)
    for t in range(1,11):
        if rd==t and absm:
            m=rng.choice(absm,N)*rng.choice([-1,1],N)
            k=rng.integers(0,n,N)
            r=m; h=np.maximum(m,0)+eh[k]; l=np.minimum(m,0)-el[k]
        else:
            k=rng.integers(0,n,N); r=ret[k]; h=hr[k]; l=lr[k]
        hi=P*(1+h); lo=P*(1+l)
        th=hi>=1.06; sl=lo<=1-stop_pct
        newdone=~done
        # same-day both -> stop first (conservative)
        first_t|= newdone & th & ~sl
        stopped|= newdone & sl
        touch|= th
        done|= (th|sl)
        P=P*(1+r)
    hold=P>=1.06
    return dict(touch=touch.mean(),stopfirst=(stopped & ~first_t).mean(),tfirst=first_t.mean(),hold=hold.mean(),sd=np.std(np.log(P)),absm=np.mean(absm) if absm else None,n_ev=len(absm),days=n)
def evtouch(s,k):
    # historical earnings-conditional touch: window start = reaction idx - k, window of 10 days after start
    T,O,C,Hh,L=load(s)
    ev=ehist.moves(s,10); res=[]
    for (rd,tim,mv,sp) in ev:
        i=next((q for q,x in enumerate(T) if x>=rd),None)
        if i is None: continue
        j=i+1 if tim=="AMC" else i
        st=j-k
        if st<0 or st+10>=len(T): continue
        res.append((T[j],Hh[st+1:st+11].max()/C[st]-1, C[st+10]/C[st]-1, mv))
    return res
if __name__=="__main__":
    S=pickle.load(open("ranked.pkl","rb")); Sd={x["s"]:x for x in S}
    out={}
    for s in sys.argv[1:]:
        x=Sd.get(s)
        if not x: 
            print(s,"not in scored"); continue
        stop_pct=1.5*x["atr"]/x["p"]
        r=run(s,stop_pct); out[s]=r
        rd=RD.get(s)
        line=f"{s:5} stop={stop_pct*100:4.1f}% MC touch={r['touch']*100:4.0f}% tgt-before-stop={r['tfirst']*100:4.0f}% stop-first={r['stopfirst']*100:4.0f}% hold(Nov9>=+6%)={r['hold']*100:4.0f}% sd10={r['sd']*100:4.1f}% evAvg|m|={(r['absm'] or 0)*100:4.1f}%(n={r['n_ev']})"
        if rd:
            et=evtouch(s,rd-1)
            if et:
                line+=f" | hist earn-window touch {sum(1 for e in et if e[1]>=0.06)}/{len(et)} hold {sum(1 for e in et if e[2]>=0.06)}/{len(et)}"
        print(line)
    pickle.dump(out,open("mc.pkl","wb"))
