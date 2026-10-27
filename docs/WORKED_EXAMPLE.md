# Worked example (tickers removed)

One real run, anonymized: a stock-picking contest where only first place pays. The goal is to show the *shape* of a run and how
the answer changed as the constraints did. Names are replaced by letters; numbers are from the run but are examples, not forecasts.

## How the request evolved

| Step | What the user asked | What changed in the analysis |
|---|---|---|
| 1 | Up to 4 US stocks with the best odds of touching +6% in 10 sessions; buy Tue open, sell the close 10 sessions later | Full pipeline; regime paragraph; funnel; touch/stop formulas; red team; 4-pick format |
| 2 | "Do one for buy tomorrow at open, sell next Thursday" | Window became 7 sessions (entry Wed open, exit Thu close). Names reporting after the exit dropped out; two names reporting right after the exit lost almost all their edge (one went from 51% to 27% simulated touch odds) |
| 3 | "4 stocks, $24k, I want to win" (school competition) | Switched to tournament mode: correlated simulation, win-vs-class model, concentration trade-off. Asked about class size/payout; user said only first place, class 30+ |
| 4 | "Build the 2-stock version" then "I need 4 at $6k each" | The 2-stock version had ~21% simulated win odds in a class of 30, but it broke the 4-stock rule; with 4 equal-dollar stocks the cap is ~12-14% regardless of which four |
| 5 | "Run the same prediction for today" (after the close) | Refreshed with the day's closes: scored how the picks did (flagged as a coin flip), checked after-hours, re-ran the whole screen, swapped two names under stricter filters |

## The funnel in numbers

| Stage | Count |
|---|---|
| US stocks over $1B, price over $5 (Yahoo screener) | ~1,760 |
| Liquid enough (dollar volume over $25M) | ~1,556 |
| With usable options data (uptrend/RS names + earnings-in-window names with ATR over 3% + a hand list) | 660 |
| Tournament pool (event inside window, simulated touch >= 55%, ADV >= $40M, price >= $7) | 87 |
| Aligned for the joint simulation (recent IPOs drop out) | 79 |
| Passing quality filters | 40 |
| Searched for 4-name baskets (top 34 by single-name upside tail) | 46,376 combinations |

## What the screen said and what the red team did

- The top of the raw ranking was dominated by one factor (a commodity rally), so the carried-forward set was collapsed to one name per theme.
- **Stock A** (oil-linked refiner): cut. A peer had just beaten big and still fell (priced in), calls outnumbered puts ~22:1, the implied move was
  far above history, and the stop was 9% wide (reward/risk 0.65).
- **Stock B** (server maker): cut. It had already pre-announced the quarter, so the event was gone.
- **Stock C** (biotech-diagnostics): cut. 3 of 5 past earnings reactions were negative with a mean of -14%.
- **Stock D** (software mid-cap, strong estimate revisions): kept in early rounds, then dropped because the shortened window ended before its
  earnings reaction.
- **Stocks E and F** (AI-infrastructure names): stayed on top across every re-run - high volatility, rising estimates, dates confirmed by the company.
- **Stock G** (data-analytics large cap): dropped in the final refresh: revisions flat to down and the company still had not announced its date.
- **Stock H** (chip-equipment small cap): scored highest on raw simulated odds but was rejected - down 64% from its high with no explanation found.

## The output shape (what the user got)

1. Regime paragraph (selective: indices near highs, breadth about 50%, hawkish Fed, 10-year near 5%, oil over $100, AI hardware in a bear market).
2. A table of the basket: shares, cost, report date and its confirmation status, implied vs historical move, touch odds, odds of being sold at/above +6% on exit.
3. Outcome table: percentiles (5th about -23%, median about -0.6%, 95th about +26%), P(up 10/15/20/25%) about 24/16/10/5%, P(down 10/20/30%) about 26/8/1.5%,
   and checkpoint odds (up day 1 / day 2 / exit about 50/50/48%, up at all three about 22%).
4. P(finishing first) for class sizes 30/60/100 and field spreads 4/5/8% (about 13% for a class of 30 at 5%).
5. Cautions: factor concentration (all four AI-infrastructure), buying after a bounce, unconfirmed date for one name with a named backup, wide stops (12-16%).
6. A one-line no-guarantee caveat.

## What the user asked next, and the answers

- *"Are you sure?"* - No. Confirmed vs unconfirmed dates, the ~13% win figure with its error, and the biggest risk (one factor).
- *"Is this for tomorrow?"* - Restated the exact entry and exit sessions and the share-count rule.
- *"Run the same quant again with updated data."* - Re-ran everything from the universe step; the top two names did not change, two others did; the win odds moved by
  about one point, which is inside the model's error, and the answer said so.

## Take-aways baked into the playbook

- The formula's touch probability is a volatility ranking; the downside mirrors the upside.
- Confirmed dates and factor diversification matter more than a decimal of simulated edge.
- The best equal-dollar four-stock basket still only wins a class of 30 about one time in eight.
- A good first day proves nothing.
