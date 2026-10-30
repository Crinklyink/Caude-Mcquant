"""Red-team flags for every pool name, computed instead of hand-checked (CLAUDE.md section 6).

  A  run-up        +20% or more over the last 21 sessions
  B  crowded       call volume > 3x put volume (at least 500 contracts)
  C  priced in     implied earnings move > 1.25x the stock's own average past move
  D  above target  price above the analysts' mean target
  E  unexplained   latest extended-hours move 5%+ beyond what the Nasdaq-100 move explains (60-day beta to QQQ),
                   before the stock's own report
  N  unpriceable   the options cannot price the event: no expiry covers it, or the estimate needs an assumed baseline
Two or more flags = cut. Industry is kept for the one-per-industry rule in 13_win_search.py.
Still manual: news (pre-announcements, deals, lawsuits), peer read-through, and confirming report dates.
Writes redteam.pkl.
"""
import sys, json, pickle, importlib, datetime as dt, numpy as np, warnings
from math import sqrt
from concurrent.futures import ThreadPoolExecutor
warnings.filterwarnings("ignore")
sys.path.insert(0, '.')
import yf, config, mc7
ts = importlib.import_module("14_term_structure")

pool = pickle.load(open("pool.pkl", "rb"))
S = {x["s"]: x for x in pickle.load(open("ranked.pkl", "rb"))}
H = json.load(open("hist.json"))
close_ts = H["SPY"]["t"][-1] + 6.5 * 3600          # AS_OF 16:00 ET (daily bars are stamped at the 9:30 open)


def implied_move(res, rd):
    """Average absolute earnings move the options price in. res rows: (expiry, sessions, straddle, pct, iv, vol, quote).
    Event variance = variance of the first expiry covering the reaction minus normal-day variance, which comes from
    the last expiry before the reaction (2+ sessions), else from the next two covering expiries, else 85%."""
    cover = [x for x in res if x[1] >= rd]
    if not cover: return None, None, "none"
    e2 = cover[0]
    before = [x for x in res if 2 <= x[1] < rd]
    s2, how = None, "assumed"
    if before: s2, how = before[-1][4] ** 2, "near"
    elif len(cover) > 1 and cover[1][1] > e2[1]:
        e3 = cover[1]; s2, how = (e3[4] ** 2 * e3[1] - e2[4] ** 2 * e2[1]) / (e3[1] - e2[1]), "spread"
    if s2 is None or s2 <= 0.04: s2, how = 0.85 ** 2, "assumed"
    ev2 = e2[4] ** 2 * e2[1] / 252 - s2 * (e2[1] - 1) / 252
    return 0.7979 * sqrt(max(ev2, 0)), e2, how


def latest_trade(s):
    r = json.loads(yf.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=2d&interval=5m&includePrePost=true"))["chart"]["result"][0]
    bars = [(t, c) for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c is not None]
    return bars[-1]


def daily_rets(s, n=60):
    c = [x for x in H[s]["c"] if x is not None][-(n + 1):]
    return np.diff(np.log(c))


qt, qp = latest_trade("QQQ")
QQQ_GAP = qp / [x for x in H["QQQ"]["c"] if x is not None][-1] - 1 if qt > close_ts else 0.0
RQ = daily_rets("QQQ")
print(f"QQQ latest move vs close: {QQQ_GAP*100:+.2f}%")


def one(item):
    s, rd, est = item
    x = S[s]; out = dict(s=s, rd=rd, est=est, ind=x.get("ind") or x.get("sec") or s, sec=x.get("sec"), close=float(x["p"]),
                         e=x["e"][0][:2] if x["e"] else None, flags=[], info=[])
    try:
        res = ts.term(s)[1]
        exit_rows = [r for r in res if dt.date.fromisoformat(r[0]) > config.EXIT]
        out["iv_x"] = exit_rows[0][4] if exit_rows else None
        out["quote"] = "".join(sorted(set("".join(r[6] for r in res)))) if res else ""
        out["imp"], out["imp_exp"], out["imp_how"] = implied_move(res, rd)
    except Exception as e:
        out["iv_x"] = out["imp"] = None; out["imp_how"] = "none"; out["info"].append(f"options error {str(e)[:40]}")
    try:
        t, p = latest_trade(s)
        out["live"], out["live_t"] = float(p), dt.datetime.fromtimestamp(t, dt.timezone.utc)
        out["gap"] = p / out["close"] - 1 if t > close_ts else 0.0
    except Exception:
        out["live"], out["live_t"], out["gap"] = out["close"], None, 0.0
    rs = daily_rets(s); k = min(len(rs), len(RQ))
    out["beta"] = float(np.cov(rs[-k:], RQ[-k:])[0, 1] / np.var(RQ[-k:], ddof=1)) if k > 20 else 1.0
    out["excess"] = out["gap"] - out["beta"] * QQQ_GAP
    mv = mc7.moves(s); out["hist"] = float(np.mean([abs(m[2]) for m in mv])) if mv else None; out["nev"] = len(mv)
    f = out["flags"]
    if (x.get("r21") or 0) >= 0.20: f.append("A run-up")
    cv, pv = x.get("cv") or 0, x.get("pv") or 0
    if cv + pv >= 500 and cv > 3 * pv: f.append("B crowded")
    if out["imp"] and out["hist"] and out["imp"] > 1.25 * out["hist"]: f.append("C priced-in")
    if x.get("tgt") and x["p"] > x["tgt"]: f.append("D above-target")
    if abs(out["excess"]) >= 0.05: f.append("E unexplained-move")
    if out["imp"] is None or out["imp_how"] == "assumed": f.append("N options-cannot-price-event")
    if est: out["info"].append("date is an estimate (Yahoo)")
    return s, out


with ThreadPoolExecutor(6) as ex:
    RT = dict(ex.map(one, pool))
pickle.dump(RT, open("redteam.pkl", "wb"))
print(f'{"sym":6}{"industry":28}{"close":>9}{"latest":>9}{"gap%":>6}{"xs%":>6}{"IVx":>5}{"imp%":>6}{"hist%":>6}  flags')
for s, o in sorted(RT.items(), key=lambda kv: (len(kv[1]["flags"]), kv[0])):
    iv = f'{o["iv_x"]*100:5.0f}' if o.get("iv_x") else "    -"
    im = f'{o["imp"]*100:6.1f}' if o.get("imp") else "     -"
    hi = f'{o["hist"]*100:6.1f}' if o.get("hist") else "     -"
    print(f'{s:6}{o["ind"][:27]:28}{o["close"]:9.2f}{o["live"]:9.2f}{o["gap"]*100:6.1f}{o["excess"]*100:6.1f}{iv}{im}{hi}  {", ".join(o["flags"]) or "-"}'
          + (f'  ({"; ".join(o["info"])})' if o["info"] else ""))
print("cut (2+ flags):", [s for s, o in RT.items() if len(o["flags"]) >= 2])
