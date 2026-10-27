# Findings and failure modes

Numbers are from runs in late Oct 2026 and are examples of the *kind* of result to expect, not forecasts.

## 1. Calibration: IV-based touch odds are too high

Across ~400-660 candidate stocks the average driftless touch probability from straddle-implied IV was about
56-59%, while the actual 2-year rolling base rate was about 45-48%. The same formula with 60-day *realized* vol
matched the base rate (about 44-50%). Roughly 10 points of the IV number is the variance risk premium plus the
earnings jump being spread over a longer expiry. Treat the IV column as an upper bound and lean on the Monte Carlo
and the base rate.

## 2. Touch probability is a volatility ranking, not an edge

The names with the highest P(touch +6%) are the most volatile, including beaten-down ones. They also have the widest
stops (13-17% at 1.5x ATR, reward/risk 0.35-0.5), and the downside mirrors the upside: for a high-vol basket,
P(+10% or better) was about 24% and P(-10% or worse) about 25%. A +1% expected drift per stock lifted P(+10%) by only ~2 points.

## 3. Tournament math

For a contest where only first place pays:

- The winner needs far more than +10% in a big class (see `docs/METHOD.md` section 7).
- Equal-dollar four-stock baskets topped out near a 12-14% chance to win a class of 30 (field spread 5%), and
  4-6% if the class is wild (8%).
- Concentrating raises win odds and blow-up odds together (class of 30, field 5%): four names ~12% win / 1% chance of
  losing 30%+; two names ~21% / 9%; one name ~29% / 20%. Gains flatten past about two names.
- Chance of being up at *all three* of day 1, day 2 and exit was only ~21-22% at best.
- Differences of about one point between candidate baskets are inside model error; choose on data quality (confirmed dates,
  revisions, factor concentration), not on the decimal.

## 4. Things that fooled or nearly fooled the screen

- **Priced-in beats.** A refiner reportedly beat EPS by ~18% (a market-news card; unverified against the company release) and the stock
  still fell; the group was crowded. A read-through from a peer is a red-team input.
- **Pre-announced results.** A server maker released preliminary quarterly numbers ahead of its call, so the "catalyst" was gone.
- **Deal-pinned stocks.** A big run with very low ATR/IV and price at the target looks like a pending acquisition; exclude.
- **Unconfirmed dates.** Calendars disagree and Yahoo's estimate flag was wrong at least once. A report that slips past the
  exit date removes the whole thesis. Always name a backup.
- **Reaction after exit.** Names reporting after the close the day before the exit contribute nothing. When the holding window was
  shortened so two reports fell after the exit, simulated touch odds dropped from 67% to 50% for one and from 51% to 27% for the other.
- **Same-factor baskets.** Four "different" tickers were all AI-infrastructure names; a single capex headline hits all of them.
- **Short histories.** Recent IPOs drop out of aligned return matrices.
- **Stale or thin quotes.** Pre-market option quotes are empty; last trades can be hours old. IV from 30-contract expiries is noisy.
- **Search noise.** Aggregators, mirror sites and auto-generated pages disagree; prefer company releases, SEC 8-Ks, and wire copies.
- **Daily results are noise.** A basket up 5% one day is a coin flip landing. Say so.

## 5. What was not validated

- No out-of-sample backtest of the ranking itself; the score weights and sub-score heuristics are judgment.
- Event moves are drawn from ~5-10 past reactions per name, so tails are uncertain.
- The class-field model is an assumption.
