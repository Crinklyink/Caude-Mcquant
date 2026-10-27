"""Final report for a chosen basket: stops, share counts, per-name odds, basket distribution, win odds.

Edit the EDIT block, then:  python -I 15_final_report.py
Needs (from earlier steps): hist.json, joint.pkl.  Inputs marked "from 14" come from
`python -I 14_term_structure.py TICKER ...` (IV by expiry).
"""
import sys, json, pickle, numpy as np, warnings
from math import log, sqrt, erf
warnings.filterwarnings("ignore")
sys.path.insert(0, '.')
import mc, mc7, config


# ================================ EDIT ================================
NAMES = ["AXTI", "FSLY", "DOCN", "HUT"]            # the basket you want a report on
COMPARE = {                                        # other baskets to print the same distribution for
    "PREVIOUS": ["AXTI", "FSLY", "PLTR", "ALAB"],
    "ALT": ["AXTI", "FSLY", "DOCN", "W"],
}
BUDGET_PER_NAME = 6000                             # dollars per name (whole shares, never over)
TOTAL_BUDGET = 24000

# Session of the earnings reaction inside the trade (1 = entry day). Same value 10_pool.py stored in pool.pkl.
RD = {"AXTI": 3, "FSLY": 7, "DOCN": 5, "HUT": 6}
# from 14: IV (as a fraction) of the first expiry on/after the day after EXIT, and sessions ENTRY -> that expiry
IV_EXIT = {"AXTI": 1.34, "FSLY": 1.48, "DOCN": 1.26, "HUT": 1.11}
EXIT_N = 8
# from 14: IV of the nearest weekly expiry (the "normal days" baseline) and sessions ENTRY -> that expiry
IV_NEAR = {"AXTI": 1.78, "FSLY": 0.89, "DOCN": 0.92, "HUT": 0.98}
NEAR_N = 3
# Assumed normal-day vol for names whose reaction falls INSIDE the near expiry (their near IV already contains the jump)
BASE_IV_IF_EVENT_IN_NEAR = 0.85
# =====================================================================

T = config.HZ / 252
def N(x): return 0.5 * (1 + erf(x / sqrt(2)))

print(f'{"sym":5}{"close":>8}{"atr$":>6}{"atr%":>5}{"stop":>8}{"stop%":>6}{"RR":>5}{"tgt+6":>8} | IV  fTouch fStop fTgt1st fHold | '
      f'mcTouch mcT1st mcS1st mcSold>=6 | base | impEv% histEv% | shares  cost')
tot = 0
for s in NAMES:
    T_, O, C, Hh, L = mc.load(s); p = C[-1]
    tr = np.maximum(Hh[1:] - L[1:], np.maximum(abs(Hh[1:] - C[:-1]), abs(L[1:] - C[:-1]))); atr = tr[-14:].mean()
    stop = p - 1.5 * atr; ds = log(p / stop); sig = IV_EXIT[s] * sqrt(T)
    ft = 2 * N(-log(1.06) / sig); fs = 2 * N(-ds / sig); tf = ds / (ds + log(1.06)); fh = N(-log(1.06) / sig)
    r = mc7.run7(s, 1.5 * atr / p, RD[s], N=30000); b, bh = mc7.base7(s)
    ev = mc7.moves(s); hav = np.mean([abs(m[2]) for m in ev]) if ev else float("nan")
    if RD[s] <= NEAR_N:   # reaction inside the near expiry: its straddle holds the jump
        evv = IV_NEAR[s] ** 2 * NEAR_N / 252 - BASE_IV_IF_EVENT_IN_NEAR ** 2 * (NEAR_N - 1) / 252
    else:                 # reaction between the near and exit expiries
        evv = IV_EXIT[s] ** 2 * EXIT_N / 252 - IV_NEAR[s] ** 2 * (EXIT_N - 1) / 252
    imp = 0.7979 * sqrt(max(evv, 0)); sh = int(BUDGET_PER_NAME // p); cost = sh * p; tot += cost
    print(f'{s:5}{p:8.2f}{atr:6.2f}{atr/p*100:5.1f}{stop:8.2f}{(1-stop/p)*100:6.1f}{0.06/(1-stop/p):5.2f}{p*1.06:8.2f} | '
          f'{IV_EXIT[s]*100:3.0f} {ft*100:6.0f}% {fs*100:4.0f}% {tf*100:6.0f}% {fh*100:5.0f}% | '
          f'{r["touch"]*100:6.0f}% {r["tfirst"]*100:6.0f}% {r["stopfirst"]*100:6.0f}% {r["hold"]*100:8.0f}% | '
          f'{b*100:4.0f}%/{bh*100:3.0f}% | {imp*100:5.1f} {hav*100:7.1f} | {sh:5d} {cost:9.2f}')
print("total", round(tot, 2), "cash left", round(TOTAL_BUDGET - tot, 2))

syms, cum, EV, RDj = pickle.load(open("joint.pkl", "rb")); ix = {s: i for i, s in enumerate(syms)}
LAST = cum.shape[0] - 1                      # exit day index in the simulation
erfv = np.vectorize(erf); grid = np.linspace(-1, 3, 4001)


def basket(nm, tag):
    c = [ix[n] for n in nm]; P = lambda d: (cum[d][:, c] - 1).mean(1)
    r1, r2, r3, rx = P(1), P(2), P(3), P(LAST)
    q = np.percentile(rx, [5, 25, 50, 75, 95])
    wins = []
    for sd in (0.04, 0.05, 0.08):
        tab = 0.8 * 0.5 * (1 + erfv(grid / sd / sqrt(2))) + 0.2 * 0.5 * (1 + erfv(grid / (3 * sd) / sqrt(2)))
        wins.append([np.mean(np.interp(rx[:20000], grid, tab) ** Nn) * 100 for Nn in (30, 60, 100)])
    print(f"\n{tag}: {'/'.join(nm)}")
    print("  pctl 5/25/50/75/95:", np.round(q * 100, 1), " P(>=5/10/15/20/25):", [round(float(np.mean(rx >= t)) * 100, 1) for t in (.05, .10, .15, .20, .25)],
          " P(<=-10/-20/-30):", [round(float(np.mean(rx <= t)) * 100, 1) for t in (-.10, -.20, -.30)])
    print("  up d1/d2/d3/exit:", [round(float(np.mean(x > 0)) * 100, 1) for x in (r1, r2, r3, rx)],
          " all(d1,d2,exit):", round(float(np.mean((r1 > 0) & (r2 > 0) & (rx > 0))) * 100, 1),
          " day1 p10/p90:", np.round(np.percentile(r1, [10, 90]) * 100, 1), " day2:", np.round(np.percentile(r2, [10, 90]) * 100, 1))
    for sd, w in zip((4, 5, 8), wins):
        print(f"  P(win) field sd {sd}%: N30/60/100 = {np.round(w, 1)}")


basket(NAMES, "BASKET")
for tag, nm in COMPARE.items():
    basket(nm, tag)

# recent (60-session) correlation: the simulation's near-zero pairwise correlation understates tails in busy regimes
H = json.load(open("hist.json"))
def rets(s):
    d = H[s]; c = [(t, x) for t, x in zip(d["t"], d["c"]) if x is not None]
    return {t: np.log(c[i][1] / c[i - 1][1]) for i, (t, _) in enumerate(c) if i > 0}
R = {s: rets(s) for s in NAMES + ["SPY"]}
common = sorted(set.intersection(*[set(R[s]) for s in R]))[-60:]
M = np.array([[R[s][t] for t in common] for s in NAMES + ["SPY"]]); Cc = np.corrcoef(M)
print("\n60d corr:"); print("      " + " ".join(f"{s:>5}" for s in NAMES + ["SPY"]))
for i, s in enumerate(NAMES + ["SPY"]):
    print(f"{s:5} " + " ".join(f"{Cc[i][j]:5.2f}" for j in range(len(NAMES) + 1)))
