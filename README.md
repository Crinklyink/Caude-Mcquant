# Caude-Mcquant

A quantitative screen for **short-horizon long setups**: "which US stocks have the best odds of
touching +X% within N sessions, and what does that really mean?" It also has a *tournament mode*
that picks a 4-stock basket for a stock-picking contest, using a correlated simulation and a model
of the rest of the class.

It was built live in a Claude Code session (Oct 2026) and is **research code, not investment advice**.
Nothing here predicts the market; the point is to show honest probabilities, including how little
edge a screen like this really has.

## What it does

1. Pulls a universe of US stocks (> $1B market cap, > $5, liquid) and 2 years of daily bars.
2. Pulls the earnings calendar and, for candidates, option chains + analyst-revision data.
3. Backs implied vol out of ATM straddle prices and applies the driftless touch formula
   `P(touch +6%) ~ 2 * N(-ln(1.06) / (sigma * sqrt(T)))`, with stops at 1.5x ATR.
4. Cross-checks with (a) a historical base rate, (b) a bootstrap Monte Carlo that treats the
   earnings jump as a dated event, and (c) the stock's own past earnings reactions.
5. Scores candidates (catalyst / revisions / technicals / positioning / macro), applies a
   red-team checklist (computed, not hand-ticked) and quality filters, and searches 4-stock baskets
   (one per industry) by simulated "probability of finishing first in a class of N".
6. Prints a short answer card: the four stocks priced at the latest trade, share counts, report
   dates, odds, close alternatives and what the red team cut.

## Layout

```
CLAUDE.md             playbook for the assistant: how to run this end to end, rules, pitfalls
docs/WORKFLOW.md      the full loop in order, including the manual research and judgment steps
docs/WORKED_EXAMPLE.md an anonymized end-to-end run and how the answer changed with the constraints
docs/METHOD.md        formulas and model definitions
docs/FINDINGS.md      what the numbers taught us (calibration, tournament math, failure modes)
quant/config.py       every date/window setting in one place (edit this first)
quant/                the pipeline (numbered scripts + yf.py / ehist.py / mc.py / mc7.py helper modules)
quant/extras/         side tools (post-earnings-drift scan, session recap, etc.)
```

## Quick start

```bash
pip install -r requirements.txt     # numpy only; everything else is stdlib
cd quant
# buy at the next open, sell at the close of the --exit session; dates come from the clock
python -I predict.py --exit 2026-11-05
```

That runs the whole pipeline (a few minutes) and prints the answer card; the card is also saved to
`today.json` and the full output to `predict.log`. `--dry-run` shows the dates it would use, and
`--from 12b` redoes only the later steps on data already downloaded.

Manual route: edit the EDIT block in `config.py`, check it with `python config.py`, then `./run_all.sh`.

Scripts read and write their data files (`*.json`, `*.pkl`, `*.log`) in the current directory, so run them
from `quant/`. Those files are git-ignored.

## Data sources and caveats

- Yahoo Finance chart / options / quoteSummary endpoints (unofficial, cookie + crumb) and the Nasdaq
  earnings-calendar API (unofficial). They can change or rate-limit without notice; check their terms
  before relying on them.
- Option quotes are only good when the market is open. Outside hours bid/ask is empty and the
  pipeline falls back to last trades, so IV is approximate.
- Earnings dates from calendars can be estimates. Confirm with the company's own announcement.

## Disclaimer

Educational research only, not a licensed advisor's recommendation. No one can guarantee a return;
every probability here is a model output with error bars, and the model has known biases (see
`docs/FINDINGS.md`).
