"""The answer card: the best rule-following basket from 13_win_search.py, priced at the latest trade, with its odds.
Replaces hand-filling the EDIT block of 15_final_report.py (15 still works for custom baskets). Writes today.json.
"""
import sys, json, pickle, datetime as dt, numpy as np, warnings
from math import erf, sqrt, log
warnings.filterwarnings("ignore")
sys.path.insert(0, '.')
import mc, mc7, config

BUDGET = 6000                     # dollars per stock, whole shares, never over
syms, cum, EV, RD = pickle.load(open("joint.pkl", "rb")); ix = {s: i for i, s in enumerate(syms)}
W = pickle.load(open("win5.pkl", "rb")); RT = pickle.load(open("redteam.pkl", "rb"))
if not W: sys.exit("no basket passes the rules; loosen them by hand in 13_win_search.py")
pick = [syms[i] for i in W[0][0]]
LAST = cum.shape[0] - 1; T = config.HZ / 252
N = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
erfv = np.vectorize(erf); grid = np.linspace(-1, 3, 4001)
when = {"time-pre-market": "before open", "time-after-hours": "after close"}

rows = []
for s in pick:
    o = RT[s]; _, O, C, Hh, L = mc.load(s); close = C[-1]
    tr = np.maximum(Hh[1:] - L[1:], np.maximum(abs(Hh[1:] - C[:-1]), abs(L[1:] - C[:-1]))); atr = tr[-14:].mean()
    px = o["live"] if o.get("live") else close           # latest trade (pre-market / after-hours if newer than the close)
    r = mc7.run7(s, 1.5 * atr / close, RD[s], N=30000)
    sh = int(BUDGET // px)
    rows.append(dict(s=s, ind=o["ind"], close=float(close), px=float(px), gap=o["gap"], shares=sh, cost=round(sh * px, 2),
                     report=o["e"][0] if o["e"] else None, timing=when.get(o["e"][1], "time not given") if o["e"] else "",
                     rd=RD[s], iv=o.get("iv_x"), imp=o.get("imp"), hist=o.get("hist"),
                     ftouch=2 * N(-log(1.06) / (o["iv_x"] * sqrt(T))) if o.get("iv_x") else None,
                     mctouch=float(r["touch"]), sold6=float(r["hold"]), stop=float(close - 1.5 * atr),
                     flags=o["flags"], info=o["info"], est=o["est"]))

c = [ix[s] for s in pick]; P = lambda d: (cum[d][:, c] - 1).mean(1)
rx, r1 = P(LAST), P(1)
win = {}
for sd in (0.04, 0.05, 0.08):
    tab = 0.8 * 0.5 * (1 + erfv(grid / sd / sqrt(2))) + 0.2 * 0.5 * (1 + erfv(grid / (3 * sd) / sqrt(2)))
    win[sd] = [float(np.mean(np.interp(rx[:20000], grid, tab) ** n)) for n in (30, 60, 100)]
H = json.load(open("hist.json"))
def rets(s):
    d = H[s]; cc = [(t, x) for t, x in zip(d["t"], d["c"]) if x is not None]
    return {t: np.log(cc[i][1] / cc[i - 1][1]) for i, (t, _) in enumerate(cc) if i > 0}
Rr = {s: rets(s) for s in pick}; common = sorted(set.intersection(*[set(v) for v in Rr.values()]))[-60:]
cor = np.corrcoef(np.array([[Rr[s][t] for t in common] for s in pick]))
pairs = sorted(((cor[i][j], pick[i], pick[j]) for i in range(4) for j in range(i + 1, 4)), reverse=True)
near = [("/".join(syms[i] for i in w[0]), w[1]) for w in W[1:] if W[0][1] - w[1] <= 0.005][:5]
cut = {s: o["flags"] for s, o in RT.items() if len(o["flags"]) >= 2}
lt = max((o["live_t"] for o in RT.values() if o.get("live_t")), default=None)
quotes = "".join(sorted(set("".join(RT[s].get("quote", "") for s in pick))))
card = dict(made=dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"), as_of=config.AS_OF.isoformat(),
            entry=config.ENTRY.isoformat(), exit=config.EXIT.isoformat(), sessions=config.HZ, picks=rows,
            total=round(sum(x["cost"] for x in rows), 2),
            pct=dict(zip(("p5", "p25", "p50", "p75", "p95"), [float(v) for v in np.percentile(rx, [5, 25, 50, 75, 95])])),
            p_up10=float(np.mean(rx >= .10)), p_up20=float(np.mean(rx >= .20)), p_dn10=float(np.mean(rx <= -.10)),
            p_dn20=float(np.mean(rx <= -.20)), p_dn30=float(np.mean(rx <= -.30)), p_up_day1=float(np.mean(r1 > 0)),
            p_up_exit=float(np.mean(rx > 0)), win={f"sd{int(k*100)}": v for k, v in win.items()},
            max_corr=[round(float(pairs[0][0]), 2), pairs[0][1], pairs[0][2]], close_alternatives=near, cut=cut,
            latest_trade_utc=lt.isoformat(timespec="minutes") if lt else None,
            option_quotes="mid prices (market open)" if quotes == "m" else "last trades (market closed): IV is approximate")
json.dump(card, open("today.json", "w"), indent=1)

print(f"\nPREDICTION  buy at the {card['entry']} open, sell at the {card['exit']} close ({card['sessions']} sessions)")
print(f"prices: {card['as_of']} close; latest trade {lt:%m-%d %H:%M} UTC; options: {card['option_quotes']}" if lt else "")
print(f'\n{"stock":6}{"industry":26}{"latest":>9}{"vs close":>9}{"shares":>7}{"cost":>10}  {"reports":22}{"IV":>5}{"impl/hist move":>16}{"touch+6 sim/frm":>17}{"sold>=+6":>9}{"stop":>9}  flags')
for x in rows:
    rep = f'{x["report"]} {x["timing"]}' + (" (est.)" if x["est"] else "")
    mv = f'{x["imp"]*100:.1f}% / {x["hist"]*100:.1f}%' if x["imp"] and x["hist"] else "-"
    ft = f'{x["ftouch"]*100:.0f}%' if x["ftouch"] else "-"
    print(f'{x["s"]:6}{x["ind"][:25]:26}{x["px"]:9.2f}{x["gap"]*100:8.1f}%{x["shares"]:7d}{x["cost"]:10,.2f}  {rep:22}'
          f'{(x["iv"] or 0)*100:4.0f}%{mv:>16}{x["mctouch"]*100:9.0f}% / {ft:>4}{x["sold6"]*100:8.0f}%{x["stop"]:9.2f}  {", ".join(x["flags"]) or "-"}')
print(f'total {card["total"]:,.2f}  cash left {4*BUDGET-card["total"]:,.2f}   (at the real open use floor({BUDGET} / open price))')
q = card["pct"]
print(f'\nbasket at the {card["exit"]} close: 5th/50th/95th pct {q["p5"]*100:+.1f} / {q["p50"]*100:+.1f} / {q["p95"]*100:+.1f}%'
      f' | up 10%+ {card["p_up10"]*100:.0f}% | up 20%+ {card["p_up20"]*100:.0f}% | down 20%+ {card["p_dn20"]*100:.0f}% | down 30%+ {card["p_dn30"]*100:.1f}%')
print(f'chance of finishing first (class spread +/-5%): class of 30 {win[0.05][0]*100:.1f}% | 60 {win[0.05][1]*100:.1f}% | 100 {win[0.05][2]*100:.1f}%'
      f'   (spread +/-4%: {win[0.04][0]*100:.1f}% in 30, +/-8%: {win[0.08][0]*100:.1f}% in 30)')
print(f'most correlated pair (60d): {pairs[0][1]}/{pairs[0][2]} {pairs[0][0]:.2f}')
if near: print("close alternatives (within 0.5 pt = noise):", ", ".join(f"{b} {p*100:.1f}%" for b, p in near))
if cut: print("cut by red team:", "; ".join(f"{s} ({', '.join(f)})" for s, f in cut.items()))
print("still check by hand: each report date in the company's own release, and news behind any big move.")
