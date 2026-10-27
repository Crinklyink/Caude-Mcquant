import pickle, numpy as np, warnings
warnings.filterwarnings("ignore")
S=pickle.load(open("ranked.pkl","rb")); M=pickle.load(open("mc7.pkl","rb"))
rows=[]
for x in S:
    m=M[x["s"]]
    if "err" in m: continue
    r=m["mc"]
    # catalyst re-score for the Oct28->Nov5 window
    kind=m["kind"]; rd=m["rd"]
    if kind=="in":
        cat=8 if rd in(2,3,4,5) else 6.5       # room after the event to hold vs. event on exit day
    elif kind=="after": cat=3.5      # reaction after exit: pre-earnings drift only
    elif kind=="atopen": cat=2.5     # gap is already in the entry price
    elif kind=="before": cat=2.5
    else: cat=2
    sc=0.25*cat+0.25*x["rev"]+0.25*x["tech"]+0.15*x["pos"]+0.10*x["mac"]
    rows.append((x["s"],sc,x,m,r,kind,rd))
rows.sort(key=lambda t:-t[1])
pickle.dump(rows,open("rank7.pkl","wb"))
def show(lst,n=45):
    print(f'{"sym":6}{"sec":>11}{"scr":>5}{"p":>8} {"evt":>7}{"rd":>3}{"mcT":>5}{"T1st":>5}{"S1st":>5}{"sold>=6":>8}{"exit>0":>7}{"base":>5}{"bsHold":>7}{"hAvg":>5}{"IV":>4}{"atr%":>5}{"rs63":>5}{"hi":>6}{"r21":>5}{"rev":>6} evwin')
    for sym,sc,x,m,r,kind,rd in lst[:n]:
        e=x["e"][0][0][5:]+x["e"][0][1][5:6] if x["e"] else "-"
        print(f'{sym:6}{(x["sec"] or "")[:10]:>11}{sc:5.1f}{x["p"]:8.2f} {e:>7}{str(rd):>3}{r["touch"]*100:5.0f}{r["tfirst"]*100:5.0f}{r["stopfirst"]*100:5.0f}{r["hold"]*100:8.0f}{r["exit_pos"]*100:7.0f}{m["base"]*100:5.0f}{m["basehold"]*100:7.0f}{(r["absm"] or 0)*100:5.1f}{x["iv"]*100:4.0f}{x["atrp"]*100:5.1f}{x["rs63"]*100:5.0f}{x["hi"]*100:6.1f}{x["r21"]*100:5.0f} {str(x["upr"])+"/"+str(x["dnr"]):>6} {m["ev"]}')
print("TOP by score (all):"); show(rows,45)
# event-in-window only, trend intact
tr=[t for t in rows if t[5]=="in" and t[2]["d50"]>0 and t[2]["d200"]>0]
print("\nIN-WINDOW EVENT + p>50d,200d by MC touch:")
tr.sort(key=lambda t:-t[4]["touch"]); show(tr,30)
