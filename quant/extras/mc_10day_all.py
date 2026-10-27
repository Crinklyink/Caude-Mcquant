import sys, json, pickle, numpy as np, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
import mc
from concurrent.futures import ThreadPoolExecutor
S=pickle.load(open("ranked.pkl","rb"))
DAYIDX={"2026-10-27":1,"2026-10-28":2,"2026-10-29":3,"2026-10-30":4,"2026-11-02":5,"2026-11-03":6,"2026-11-04":7,"2026-11-05":8,"2026-11-06":9,"2026-11-09":10}
def rd_for(x):
    if not x["e"]: return None
    d,tm=x["e"][0][0],x["e"][0][1]
    i=DAYIDX[d]
    if "pre" in tm: return i
    return i+1 if i+1<=10 else 11   # after-hours / not supplied -> next day
# candidates: top 90 by score + hand picks
hand="TENB TEAM PLTR QLYS PAYC CVI PBF APA HALO AMN FIGS DXC RBRK HAS SLDE SN HOG INTA FTNT TWLO EFOR MANH ZETA ARQT CRL MPC DK PSX DINO TALO CHRD DT IT SM AMD FRSH PCTY".split()
names=[x["s"] for x in S[:90]]
for h in hand:
    if h not in names: names.append(h)
Sd={x["s"]:x for x in S}
def one(s):
    x=Sd[s]
    mc.RD[s]=rd_for(x)
    try:
        r=mc.run(s,1.5*x["atr"]/x["p"],N=20000)
        rd=mc.RD[s]
        et=None
        if rd and rd<=10:
            e=mc.evtouch(s,rd-1)
            if e: et=(sum(1 for q in e if q[1]>=0.06),sum(1 for q in e if q[2]>=0.06),len(e))
        return s,r,et
    except Exception as ex:
        return s,None,str(ex)
out={}
with ThreadPoolExecutor(6) as ex:
    for s,r,et in ex.map(one,names):
        out[s]=(r,et)
pickle.dump(out,open("mcall.pkl","wb"))
rows=[]
for s,(r,et) in out.items():
    if not r: continue
    x=Sd[s]
    rows.append((s,x["sec"],x["score"],x["iv"],x["up"],r["touch"],r["tfirst"],r["stopfirst"],r["hold"],x["br"],mc.RD.get(s),r["absm"],x["emove"],et))
rows.sort(key=lambda t:-t[5])
print(f'{"sym":6}{"sector":>12}{"scr":>5}{"IV":>5}{"fTch":>5}{"mcTch":>6}{"T1st":>5}{"S1st":>5}{"hold":>5}{"base":>5}{"rd":>4}{"hAvg":>6} earn-window(touch,hold,n)')
for t in rows[:60]:
    print(f'{t[0]:6}{(t[1] or "")[:11]:>12}{t[2]:5.1f}{t[3]*100:5.0f}{t[4]*100:5.0f}{t[5]*100:6.0f}{t[6]*100:5.0f}{t[7]*100:5.0f}{t[8]*100:5.0f}{t[9]*100:5.0f}{str(t[10]):>4}{(t[11] or 0)*100:6.1f} {t[13]}')
