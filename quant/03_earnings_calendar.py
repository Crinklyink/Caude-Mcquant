"""Earnings calendar by day -> earnings.json: {"YYYY-MM-DD": [{"symbol", "time", "epsForecast", "noOfEsts", ...}, ...]}

Sources, tried per day in order:
  1. Nasdaq calendar API (unofficial): AM/PM timing, consensus EPS, analyst count.
  2. Yahoo earnings calendar (the unofficial visualization endpoint ehist.py also uses): BMO/AMC timing and EPS estimate,
     no analyst count. Days are UTC calendar days, which matches US report times (before-open 13:30Z, after-close 21:00Z).
In Nov 2026 Nasdaq began answering 403 to scripts. This step used to write an empty calendar and every later step then
ran as if no company reported anywhere, without a warning. Now a 403 switches to Yahoo for the remaining days, and the
step exits non-zero (stopping predict.py) if the trade window has no report dates from either source.
"""
import sys, json, time, urllib.error, urllib.parse, urllib.request, datetime as dt
sys.path.insert(0, '.')
import config

UA = {"User-Agent": "Mozilla/5.0"}


def nasdaq_day(d):
    req = urllib.request.Request(f"https://api.nasdaq.com/api/calendar/earnings?date={d}", headers={**UA, "Accept": "application/json"})
    rows = json.loads(urllib.request.urlopen(req, timeout=25).read())["data"]["rows"] or []
    for r in rows: r["source"] = "nasdaq"
    return rows


YTIME = {"BMO": "time-pre-market", "AMC": "time-after-hours"}


def _ytime(kind, stamp):
    """Yahoo marks upcoming reports BMO/AMC; once reported they become 'TAS' with the actual UTC time instead."""
    if kind in YTIME: return YTIME[kind]
    try: t = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except Exception: return "time-not-supplied"
    if t.hour == 0 and t.minute == 0: return "time-not-supplied"          # midnight UTC = no time given
    y = t.year
    mar = dt.date(y, 3, 8); mar += dt.timedelta(days=(6 - mar.weekday()) % 7)      # US DST: 2nd Sunday of March ...
    nov = dt.date(y, 11, 1); nov += dt.timedelta(days=(6 - nov.weekday()) % 7)     # ... to the 1st Sunday of November
    et = t - dt.timedelta(hours=4 if mar <= t.date() < nov else 5)
    m = et.hour * 60 + et.minute
    return "time-pre-market" if m < 9 * 60 + 30 else "time-after-hours" if m >= 16 * 60 else "time-not-supplied"


def _eps(x):   # Nasdaq's format: "$0.18", "($0.08)"
    if x is None: return None
    return f"${x:.2f}" if x >= 0 else f"(${-x:.2f})"


def yahoo_day(d):
    import yf   # imported here: it fetches a cookie + crumb on import, not needed while Nasdaq answers
    nxt = (dt.date.fromisoformat(d) + dt.timedelta(days=1)).isoformat()
    url = "https://query1.finance.yahoo.com/v1/finance/visualization?crumb=" + urllib.parse.quote(yf.crumb) + "&lang=en-US&region=US"
    out, off = [], 0
    while off < 3000:
        q = {"sortType": "DESC", "entityIdType": "sp_earnings", "sortField": "intradaymarketcap",
             "includeFields": ["ticker", "startdatetime", "startdatetimetype", "epsestimate"],
             "query": {"operator": "and", "operands": [{"operator": "gte", "operands": ["startdatetime", d]},
                                                       {"operator": "lt", "operands": ["startdatetime", nxt]},
                                                       {"operator": "eq", "operands": ["region", "us"]}]},
             "size": 100, "offset": off}
        req = urllib.request.Request(url, data=json.dumps(q).encode(), headers={**UA, "Content-Type": "application/json"})
        doc = json.loads(yf.op.open(req, timeout=30).read())["finance"]["result"][0]["documents"][0]
        cols = [c["id"] for c in doc["columns"]]
        page = [dict(zip(cols, r)) for r in doc["rows"]]
        out += [{"symbol": r["ticker"], "time": _ytime(r.get("startdatetimetype"), r.get("startdatetime")),
                 "epsForecast": _eps(r.get("epsestimate")), "noOfEsts": None, "source": "yahoo"} for r in page]
        if len(page) < 100: break
        off += 100
    return out


SOURCES = [("nasdaq", nasdaq_day), ("yahoo", yahoo_day)]


def fetch_day(d, blocked):
    """Rows for one day from the first source that answers with rows, and that source's name."""
    for name, f in SOURCES:
        if name in blocked: continue
        for k in range(2):
            try:
                rows = f(d)
                if rows: return rows, name
                break                       # an empty answer: try the next source
            except urllib.error.HTTPError as e:
                if e.code == 403:           # refused, not flaky: stop asking this source for the rest of the run
                    blocked.add(name)
                    print(f"WARN calendar: {name} refused with HTTP 403; using the next source from here", file=sys.stderr)
                    break
                time.sleep(1 + k)
            except Exception:
                time.sleep(1 + k)
    return [], None


def main():
    out, src, blocked = {}, {}, set()
    d = config.CAL_START
    while d <= config.CAL_END:
        if d.weekday() < 5 and d not in config.US_MARKET_HOLIDAYS:
            ds = d.isoformat()
            out[ds], src[ds] = fetch_day(ds, blocked)
            print(ds, len(out[ds]), src[ds] or "-")
            time.sleep(0.4)
        d += dt.timedelta(days=1)
    json.dump(out, open("earnings.json", "w"))
    empty = [ds for ds, rows in out.items() if not rows]
    if empty: print(f"WARN calendar: no report dates from any source for {', '.join(empty)}", file=sys.stderr)
    window = [ds for ds in out if config.WIN_START <= ds <= config.WIN_END]
    if not any(out.values()) or (window and all(not out[ds] for ds in window)):
        sys.exit(f"earnings calendar: no report dates for the trade window {config.WIN_START}..{config.WIN_END} from any source "
                 f"(blocked: {sorted(blocked) or 'none'}); every later step would treat it as 'no company reports'")


if __name__ == "__main__":
    main()
