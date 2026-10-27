import sys, pickle, numpy as np, warnings
sys.path.insert(0,'.')
import config
warnings.filterwarnings("ignore")
S=pickle.load(open("scored.pkl","rb"))
def pr(vals):
    a=np.array(vals,float); 
    return {i:float((a<a[i]).mean()) for i in range(len(a))}
rs_r=pr([x["rs63"] for x in S])
def clip(v,a=0,b=10): return max(a,min(b,v))
for i,x in enumerate(S):
    # technical (0-10)
    t=0
    t+=4*rs_r[i]
    t+=2.0 if (x["p"]>x["d50"] and True) else 0
    t+=0  # placeholder
    trend=(x["d50"]>0) + (x["d200"]>0) + (x["hi"]>-0.05)*1 + (x["hi"]>-0.02)*1
    t=4*rs_r[i] + 1.5*trend  # max 4+6=10
    x["tech"]=clip(t)
    # earnings & revisions
    er=0
    if x["eps_now"] and x["eps90"] and x["eps90"]>0:
        ch=x["eps_now"]/x["eps90"]-1
        er+=clip(5+ch*40,0,8)
    else: er+=4
    ur=(x["upr"] or 0); dr=(x["dnr"] or 0)
    if ur+dr>0: er+= 2*(ur/(ur+dr))
    x["rev"]=clip(er)
    # catalyst
    c=2
    if x["e"]:
        d=x["e"][0][0]
        c=6
        if d<=config.CAT_MID: c=7
        if d<=config.CAT_EARLY: c=8
        if d>=config.CAT_LATE: c=4.5   # little room, hold risk
    x["cat"]=c
    # positioning
    pz=4
    if x["spf"] and x["spf"]>0.08: pz+=2
    if x["spf"] and x["spf"]>0.15: pz+=1
    if x["cv"] and x["pv"] and (x["pv"]+x["cv"])>200:
        ratio=x["cv"]/max(1,x["pv"]); pz+=clip((ratio-1)*1.5,-2,3)
    if x["netpct"] and x["netpct"]>0: pz+=1
    x["pos"]=clip(pz)
    # macro/sector
    sec=(x["sec"] or "")
    m=5
    if sec=="Energy": m=8
    elif sec=="Technology": m=6
    elif sec in("Consumer Cyclical","Real Estate","Financial Services","Consumer Defensive"): m=4
    x["mac"]=m
    x["score"]=0.25*x["cat"]+0.25*x["rev"]+0.25*x["tech"]+0.15*x["pos"]+0.10*x["mac"]
S.sort(key=lambda x:-x["score"])
pickle.dump(S,open("ranked.pkl","wb"))
print(f'{"sym":6}{"scr":>5}{"p":>8}{"cap$B":>7}{"sec":>12} {"E":>11} {"iv":>5}{"touch":>6}{"stop":>6}{"1st":>5}{"rv60T":>6}{"base":>5}{"rs63":>6}{"hi":>6}{"emv":>5}{"spf":>5} cat rev tec pos')
for x in S[:70]:
    e=x["e"][0][0][5:]+x["e"][0][1][5:6] if x["e"] else "-"
    print(f'{x["s"]:6}{x["score"]:5.1f}{x["p"]:8.2f}{x["cap"]/1e9:7.1f}{(x["sec"] or "")[:11]:>12} {e:>11} {x["iv"]*100:5.0f}{x["up"]*100:6.0f}{x["ps"]*100:6.0f}{x["pfirst"]*100:5.0f}{x["up_rv"]*100:6.0f}{x["br"]*100:5.0f}{x["rs63"]*100:6.0f}{x["hi"]*100:6.1f}{(x["emove"] or 0)*100:5.1f}{(x["spf"] or 0)*100:5.1f} {x["cat"]:.0f} {x["rev"]:.1f} {x["tech"]:.1f} {x["pos"]:.1f}')
