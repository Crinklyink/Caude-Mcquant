import pickle, numpy as np, warnings, sys
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
import ehist
syms,cum,EV,RD=pickle.load(open("joint.pkl","rb"))
S={x["s"]:x for x in pickle.load(open("ranked.pkl","rb"))}
rows=[]
for s in syms:
    x=S[s]
    up,dn=x["upr"] or 0,x["dnr"] or 0
    ch=(x["eps_now"]/x["eps90"]-1) if (x["eps_now"] is not None and x["eps90"] and x["eps90"]>0) else None
    mv=ehist.moves(s,10)
    upshare=np.mean([m[2]>0 for m in mv]) if mv else None
    mean_sg=np.mean([m[2] for m in mv]) if mv else None
    flags=[]
    if dn>up: flags.append("revs-down")
    if ch is not None and ch<-0.10: flags.append("eps-falling")
    if upshare is not None and len(mv)>=5 and upshare<0.35: flags.append("evt-skew-neg")
    if mean_sg is not None and len(mv)>=5 and mean_sg<-0.04: flags.append("evt-mean-neg")
    if x["cap"]<1.5e9 or x["p"]<7: flags.append("size/price")
    if x["tgt"] and x["p"]>1.35*x["tgt"]: flags.append("price>>target")
    rows.append((s,flags,up,dn,ch,upshare,mean_sg,len(mv)))
pickle.dump(rows,open("quality.pkl","wb"))
ok=[r[0] for r in rows if not r[1]]
print("pool",len(syms),"passing quality filter:",len(ok))
print("failed:",{r[0]:r[1] for r in rows if r[1]})
