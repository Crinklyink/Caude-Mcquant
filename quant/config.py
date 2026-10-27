"""Single place for every date / window setting used by the pipeline.

Edit ONLY the block marked EDIT. Everything else is derived from it.
Dates are compared as ISO strings ("2026-11-05") in several scripts, so keep the derived string forms.

Window semantics
  AS_OF  last completed session. All price data is as of this close.
  ENTRY  you buy at this session's open.
  EXIT   you sell at this session's close.
  HOLD   the sessions in [ENTRY, EXIT]; HZ is how many.
An earnings reaction BEFORE or AT the ENTRY open is already in your entry price; one AFTER the EXIT
close contributes nothing but pre-earnings drift (see mc7.rd7).
"""
import datetime as dt

# ============================== EDIT ==============================
AS_OF = dt.date(2026, 10, 27)       # last completed session
ENTRY = dt.date(2026, 10, 28)       # buy at the open of this session
EXIT = dt.date(2026, 11, 5)         # sell at the close of this session
CAL_START = dt.date(2026, 10, 12)   # earnings-calendar start (about 2 weeks back, for post-earnings-drift scans)
CAL_END = dt.date(2026, 11, 9)      # earnings-calendar end (a few sessions past EXIT)
# ==================================================================

# NYSE full-day closures. Verify against the official NYSE calendar for the year you run.
US_MARKET_HOLIDAYS = {
    dt.date(2026, 1, 1), dt.date(2026, 1, 19), dt.date(2026, 2, 16), dt.date(2026, 4, 3),
    dt.date(2026, 5, 25), dt.date(2026, 6, 19), dt.date(2026, 7, 3), dt.date(2026, 9, 7),
    dt.date(2026, 11, 26), dt.date(2026, 12, 25),
    dt.date(2027, 1, 1), dt.date(2027, 1, 18), dt.date(2027, 2, 15), dt.date(2027, 3, 26),
    dt.date(2027, 5, 31), dt.date(2027, 6, 18), dt.date(2027, 7, 5), dt.date(2027, 9, 6),
    dt.date(2027, 11, 25), dt.date(2027, 12, 24),
}


def sessions(a, b):
    """Trading sessions in [a, b] (weekdays that are not listed holidays)."""
    out, d = [], a
    while d <= b:
        if d.weekday() < 5 and d not in US_MARKET_HOLIDAYS:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def next_session(d):
    d += dt.timedelta(days=1)
    while d.weekday() >= 5 or d in US_MARKET_HOLIDAYS:
        d += dt.timedelta(days=1)
    return d


# ------------------------------ derived ------------------------------
HOLD = sessions(ENTRY, EXIT)                    # sessions you are in the trade
HZ = len(HOLD)                                  # holding length in sessions
CAL_SESSIONS = sessions(AS_OF, CAL_END)         # sessions we classify earnings dates against
TDAYS = [d.isoformat() for d in CAL_SESSIONS]
IDX = {d.isoformat(): i + 1 for i, d in enumerate(HOLD)}   # session -> 1-based day inside the trade

WIDE_START, WIDE_END = AS_OF.isoformat(), CAL_END.isoformat()   # "earnings of interest" window
WIN_START, WIN_END = ENTRY.isoformat(), EXIT.isoformat()        # reactions that can land inside the trade

# first option expiry we use = on/after the calendar day after EXIT (Yahoo expiries are 00:00 UTC)
EXPIRY_CUTOFF_TS = int(dt.datetime.combine(EXIT + dt.timedelta(days=1), dt.time(0, 0),
                                           tzinfo=dt.timezone.utc).timestamp())

# catalyst-score date thresholds used by 07_score.py (earlier events leave more days to hold)
CAT_EARLY = HOLD[min(2, HZ - 1)].isoformat()    # on/before the 3rd session of the trade -> highest score
CAT_MID = EXIT.isoformat()                      # on/before EXIT
CAT_LATE = next_session(EXIT).isoformat()       # on/after the first session after EXIT -> little room, hold risk

if __name__ == "__main__":
    print("AS_OF", AS_OF, "| ENTRY", ENTRY, "| EXIT", EXIT, "| HZ", HZ)
    print("HOLD", [d.isoformat() for d in HOLD])
    print("TDAYS", TDAYS)
    print("CAT early/mid/late", CAT_EARLY, CAT_MID, CAT_LATE)
