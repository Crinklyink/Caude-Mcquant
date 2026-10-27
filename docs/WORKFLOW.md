# Workflow: the manual steps around the code

The scripts do the numbers. Most of the *judgment* happens between them. This is the full loop in order, including
the parts that are not code. See `CLAUDE.md` for rules and `quant/config.py` for the dates.

## 0. Pin down the ask (before touching code)

Ask, or state your assumption out loud, for each of these. They change the answer:

- **Window**: buy at which session's open, sell at which session's close (or open)? How many sessions is that?
- **Account rules**: how many stocks, dollars per stock (equal dollars?), whole shares or fractional, any per-position
  cap, min price, long-only, margin/options allowed?
- **Goal**: "up", "beat the benchmark", or "finish first in a class"? If first place: class size and payout
  (only #1 vs top-k). Honest framing: only the contest case justifies adding variance.
- **Stakes**: simulated account or real money? Real money = say so, and stay conservative on risk advice.
- **Clock**: what time is it and is the market open? Pre-market means option bid/ask is empty and prices are last night's close.

If the user's request has changed since the last run (e.g. "buy tomorrow" became "buy today", or "4 stocks" became "2"),
restate the constraint and rebuild; do not quietly reuse the old answer.

## 1. Configure and run

1. Edit the EDIT block in `quant/config.py` (`AS_OF`, `ENTRY`, `EXIT`, `CAL_START`, `CAL_END`). Run `python config.py` and check the
   printed `HOLD` sessions and `HZ` look right (holidays included).
2. `cd quant && ./run_all.sh` (about 10-20 minutes; steps 2 and 5 are the slow ones).
3. Sanity-check outputs before reading any results: the last SPY bar date equals `AS_OF`; the universe is ~1,700 names;
   the options step reports hundreds of names with ATM data; `mc7` reports 0 errors.

## 2. Regime (one paragraph)

Mix computed and searched facts, all dated:

- Computed: SPY/QQQ/IWM vs 50- and 200-day averages, 21- and 63-day returns, breadth (`04_metrics.py` prints % above 50/200d and % near highs),
  and leaders/laggards (e.g. sector and theme drawdowns you can read off `hist.json`).
- Searched (separate query each, prefer primary sources): index closes, VIX, rates, oil; the **FOMC calendar** (federalreserve.gov),
  the **jobs report** date (bls.gov), CPI date, elections, and **mega-cap earnings dates** (Nasdaq calendar, then company IR).
- Mark aggregator-only numbers as approximate and anything unconfirmed as `UNVERIFIED`.
- Conclude: aggressive / selective / defensive.

## 3. Build the funnel (20-30 names, one line each)

Sources, each with a one-line reason built from data: earnings inside the window with rising revisions; recent post-earnings gap-ups that held
(`extras/pead_scan.py`); relative-strength leaders at highs; high short interest plus a near catalyst; sector-rotation beneficiaries;
election-sensitive names (state the thesis under both outcomes - label it as opinion, not sourced); oversold names with positive revisions.
Filters: price > $5, cap > $1B, dollar volume > $25M, listed options, no leveraged ETFs, no pending acquisition targets.

Then score (`07_score.py`) and carry the top ~8 forward **after collapsing same-factor duplicates**.

## 4. Verify each finalist - one search per ticker

For every finalist, run its own searches and record what you found and where:

1. **Earnings date**: look for the company's own announcement (Finviz / BusinessWire / PRNewswire copies, IR page, SEC 8-K).
   Calendars alone are not confirmation. Note before-open vs after-close, and the reaction session.
2. **What moved it recently**: any stock up/down 20%+ in 3 weeks needs a cause. No cause found = flag `UNVERIFIED`.
3. **Deal risk**: any acquisition/merger/offer news? A pinned price with low IV after a huge run is a warning even without news.
4. **Guidance and preannouncements**: did the company already tell the market the quarter (preliminary results)? Then the event is priced in.
5. **Analyst actions and targets**: price already above the consensus target is a flag.
6. **Peer read-through**: did a peer just report and the stock fell on a beat?
7. **Insider/short/positioning**: use Yahoo fields as context only; period definitions are loose, so label them.

When two sources disagree, say so and give both. Never fill a gap from memory.

## 5. Quant check and red team

- `14_term_structure.py TICKERS...` for IV by expiry; copy into the EDIT block of `15_final_report.py`.
- Compare implied vs historical earnings move; compare formula, Monte Carlo and base rate (they will not agree - the formula runs high).
- Apply the red-team flags (run-up, crowded, implied > history, above target) and the quality filter. Two flags = cut unless you can defend it.
- Write the cut list as you go, one line each, with the reason.

## 6. Contest mode (only if a contest was stated)

1. `13_win_search.py` for the best equal-dollar baskets; `16_field_winodds.py` for concentration vs class size.
2. Present P(win) for several class sizes and field spreads, plus P(down 20%/30%). State plainly that more concentration raises both.
3. Prefer data quality (confirmed dates, revisions, diversification of events) over a decimal of simulated edge.
4. Report the chance of being up at every checkpoint the user cares about, and that it is a coin flip per checkpoint.

## 7. Write the answer

Follow the output format in `CLAUDE.md` section 8. Keep it plain: tables for numbers, short bullets for theses,
dated links for sources, `UNVERIFIED` where needed, the share counts and cash left, a backup name for each unconfirmed date,
and the one-line no-guarantee caveat at the end.

## 8. Refresh cycles

When the user comes back later in the day or the next morning:

1. Re-check the clock. After the close: pull fresh bars (`02_history.py`), update `config.py` (`AS_OF`), rerun steps 4-13.
2. `extras/session_recap.py` for how the picks did, after-hours moves of the picks, and of names that report tonight.
3. Re-search anything still `UNVERIFIED` (dates especially) - companies often announce late.
4. Say what changed and what did not. Differences of about a point between baskets are noise; do not oversell them.
5. Do not present a good day as proof; one session is a coin flip.

## 9. Delivering to the repo

If asked to save the work: copy only code and docs, scan for secrets/personal info first, keep results and data out, commit,
and push to the branch/remote the user named. Do not commit `*.json`/`*.pkl` data.

## Questions the user tends to ask, and the honest answers

- *"Are you sure?"* No. Give what is confirmed, what is not, the probability, and the biggest single risk.
- *"Will I be up tomorrow / next day / Thursday?"* About a coin flip each; being up at all three is roughly 1 in 5.
- *"I want to win a lot."* Explain the variance trade-off with the class-size table; do not promise outcomes.
- *"Is this for tomorrow?"* Restate the exact entry/exit sessions and the share-count rule.
