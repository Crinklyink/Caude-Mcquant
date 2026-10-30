"""One command for "predict for today": picks the dates from the clock, runs the pipeline, prints the answer.

    python -I predict.py --exit 2026-11-05             # buy at the next open, sell at the close of --exit
    python -I predict.py --exit 2026-11-05 --from 12b  # reuse the downloaded data, redo the later steps
    python -I predict.py --exit 2026-11-05 --dry-run   # only print the dates it would use

Dates (US Eastern time, NYSE holidays from config.py; early closes are not handled):
  before 9:30 on a trading day   AS_OF = previous session, ENTRY = today
  after 16:10 on a trading day   AS_OF = today,            ENTRY = next session
  during the session             AS_OF = previous session, ENTRY = next session (today's move is ignored)
  weekend / holiday              AS_OF = previous session, ENTRY = next session
Full log: predict.log. The answer card is also saved to today.json.
"""
import os, sys, json, argparse, subprocess, datetime as dt
sys.path.insert(0, '.')
import config

STEPS = [("01", "01_universe.py"), ("02", "02_history.py"), ("03", "03_earnings_calendar.py"),
         ("04", "04_metrics.py"), ("05", "05_options_engine.py"), ("06", "06_iv_and_inputs.py"),
         ("07", "07_score.py"), ("08", "mc7.py"), ("09", "09_rank_window.py"), ("10", "10_pool.py"),
         ("11", "11_joint_sim.py"), ("12", "12_quality_filter.py"), ("12b", "12b_redteam.py"),
         ("13", "13_win_search.py"), ("17", "17_today.py")]


def eastern_now():
    u = dt.datetime.now(dt.timezone.utc)
    y = u.year
    mar = dt.date(y, 3, 8); mar += dt.timedelta(days=(6 - mar.weekday()) % 7)    # 2nd Sunday of March
    nov = dt.date(y, 11, 1); nov += dt.timedelta(days=(6 - nov.weekday()) % 7)   # 1st Sunday of November
    dst = dt.datetime(y, 3, mar.day, 7, tzinfo=dt.timezone.utc) <= u < dt.datetime(y, 11, nov.day, 6, tzinfo=dt.timezone.utc)
    return (u + dt.timedelta(hours=-4 if dst else -5)).replace(tzinfo=None)


def is_session(d): return d.weekday() < 5 and d not in config.US_MARKET_HOLIDAYS


def prev_session(d):
    d -= dt.timedelta(days=1)
    while not is_session(d): d -= dt.timedelta(days=1)
    return d


def pick_dates(now):
    today, t = now.date(), now.time()
    if is_session(today) and t < dt.time(9, 30): return prev_session(today), today, ""
    if is_session(today) and t >= dt.time(16, 10): return today, config.next_session(today), ""
    if is_session(today):
        return prev_session(today), config.next_session(today), "market is open: today's open has passed, so this is for the NEXT open"
    return prev_session(today), config.next_session(today), ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exit", required=True, help="sell at the close of this session, YYYY-MM-DD")
    ap.add_argument("--from", dest="start", default="01", help="first step to run (ids in STEPS)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    now = eastern_now()
    as_of, entry, note = pick_dates(now)
    exit_ = dt.date.fromisoformat(a.exit)
    if not is_session(exit_) or exit_ < entry:
        sys.exit(f"--exit {exit_} must be a trading session on or after the entry session {entry}")
    print(f"now {now:%Y-%m-%d %H:%M} ET | data through the {as_of} close | buy at the {entry} open | sell at the {exit_} close"
          + (f"\nNOTE: {note}" if note else ""))
    if a.dry_run: return
    env = dict(os.environ, QUANT_AS_OF=as_of.isoformat(), QUANT_ENTRY=entry.isoformat(), QUANT_EXIT=exit_.isoformat())
    ids = [s for s, _ in STEPS]
    if a.start not in ids: sys.exit(f"--from must be one of {ids}")
    with open("predict.log", "a") as log:
        log.write(f"\n===== {now:%Y-%m-%d %H:%M} ET  AS_OF {as_of} ENTRY {entry} EXIT {exit_}\n")
        for sid, script in STEPS[ids.index(a.start):]:
            print(f"  step {sid:3} {script}", flush=True)
            log.write(f"\n----- {script}\n"); log.flush()
            p = subprocess.run([sys.executable, "-I", script], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            log.write(p.stdout); log.flush()
            if p.returncode != 0:
                print(p.stdout[-2000:]); sys.exit(f"step {sid} ({script}) failed; full output in predict.log")
            if sid == "02":   # the bars must end at the AS_OF close, or every number after this is stale
                spy = json.load(open("hist.json"))["SPY"]["t"][-1]
                last = dt.datetime.fromtimestamp(spy, dt.timezone.utc).date()
                if last != as_of: sys.exit(f"history ends {last}, expected {as_of}: Yahoo has not posted the close yet")
            if sid == "17": print(p.stdout)


if __name__ == "__main__":
    main()
