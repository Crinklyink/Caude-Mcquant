# Method

Notation: `S` spot, `x` target gain (0.06), `n` sessions to an expiry, `T = h/252` for a holding period of `h` sessions,
`N()` the standard normal CDF, `sigma` annualized vol.

## 1. Driftless touch / stop / hold

- `P(touch +x) = 2 * N( -ln(1+x) / (sigma * sqrt(T)) )`  (reflection principle, zero drift)
- `P(close >= +x at exit) = N( -ln(1+x) / (sigma * sqrt(T)) )`  (about half the touch odds)
- Stop at `S - 1.5 * ATR14`: `ds = ln(S / stop)`, `P(stop touched) = 2 * N( -ds / (sigma * sqrt(T)) )`
- `P(target before stop) = ds / (ds + ln(1+x))`  (gambler's ruin, driftless). Touch odds for target and stop add to more
  than 100% because both can happen in one window; use this ratio for the order.
- Reward/risk = `x / (1 - stop/S)`. High-vol names have wide stops, so reward/risk below 1 is normal.

## 2. Implied vol from straddles

Yahoo's `impliedVolatility` field is junk when the market is closed. Instead:

`IV = straddle / (0.7979 * S * sqrt(n/252))`

with `straddle = call + put` at the strike nearest spot (median of the 3 nearest strikes), using the bid/ask mid
when both exist and the last trade otherwise. `n` counts sessions from entry to expiry. Choose the nearest expiry
*after the exit date*. If that expiry contains an earnings jump the IV already includes it, but spread evenly over
`n` days, so the formula understates variance inside a short window; the Monte Carlo handles the jump properly.

## 3. Implied earnings move (ESTIMATE)

Using two expiries (the one just before the event as the "normal" baseline, the one after it as the total):

`event_var = IV_total^2 * n_total/252 - IV_base^2 * (n_total - 1)/252`
`implied mean |move| ~ 0.7979 * sqrt(event_var)`

Compare with the stock's average absolute earnings-day move over its last ~8 reports:
implied < historical = possibly underpriced; implied > historical = already priced in.

Historical reactions: report dates come from the Nasdaq earnings-surprise endpoint (last 4 quarters) and Yahoo's
visualization query (older quarters), then merged. Timing is inferred: whichever of day D's open gap or day D+1's
open gap is larger decides "after close" vs "before open"; the reaction is the close-to-close move over that day.
A few dates are duplicated or off; treat the numbers as approximate.

## 4. Base rate

Share of rolling `h`-session windows over the last ~2 years where `max(high over the next h sessions) >= (1+x) * start close`.
Also reported: share where the final close is >= (1+x) * start close.

## 5. Bootstrap Monte Carlo (single name)

- Resample (close return, high, low) triples from the stock's own daily history, excluding its earnings days, demeaned to zero drift.
- On the dated reaction day, replace the draw with `+/- |m|`, where `|m|` is drawn from the stock's own past absolute reactions
  and the sign is random (driftless); the intraday extension uses typical non-event highs/lows.
- Track touch, stop touch, target-before-stop (a same-day target and stop counts as stop first - conservative), and exit-day close >= target.

## 6. Correlated basket simulation

- Each simulated day samples one historical date and applies *every* name's return from that date, so cross-sectional
  correlation is preserved. Earnings jumps are drawn independently per name.
- Day 1 uses open-to-close (you buy the open). Basket = equal dollar weights.
- Because the jump dominates a 7-session window, simulated pairwise correlations are near zero. Recent regimes can be far
  higher (0.5-0.7 over 60 days), so tails are probably understated; always report the recent correlation too.
- Outputs: percentiles, P(>= +5/10/15/20/25%), P(<= -10/-20/-30%), P(up at each checkpoint), P(up at all of day 1, day 2, exit).

## 7. Probability of finishing first in a class

Model the field's return as a fat-tailed mixture: 80% `N(0, s^2)` and 20% `N(0, (3s)^2)` for typical spread `s` (try 4%, 5%, 8%).
With `F` the field CDF and `N_class` students:

- `P(win) = E[ F(R)^N_class ]` over simulated basket returns `R`
- `P(top 3) = E[ sum_{k<=2} C(N,k) (1-F)^k F^(N-k) ]`

The median winning return in this model: roughly +10% (class 10), +19% (30), +28% (100), +34% (300) at `s = 5%`, and
+16%, +29%, +44%, +55% at `s = 8%`. The model is a guess about the class; the *ranking* of strategies is more reliable than the levels.

## 8. Universe and filters

- Universe: US-listed, market cap > $1B, price > $5, average dollar volume > $25M, listed options, no leveraged ETFs.
- Pool for contests: event inside the window, MC touch >= 55%, ADV >= $40M, price >= $7, not deal-pinned.
- Quality filter and red-team flags: see `CLAUDE.md` sections 6-7.
