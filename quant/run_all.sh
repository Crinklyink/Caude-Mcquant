#!/usr/bin/env bash
# Easiest: `python -I predict.py --exit YYYY-MM-DD` picks the dates from the clock and runs all of this for you.
# This script is the manual route: edit the EDIT block in config.py FIRST, check it with `python config.py`, then run from quant/.
# Needs: python 3, numpy, outbound HTTPS (Yahoo Finance + Nasdaq endpoints).
set -euo pipefail
python -I 01_universe.py          # US stocks > $1B, price > $5  -> univ_all.json
python -I 02_history.py           # 2y daily bars for the liquid ones, trimmed to AS_OF -> hist.json
python -I 03_earnings_calendar.py # Nasdaq earnings calendar -> earnings.json
python -I 04_metrics.py           # trend / RS / ATR / base rate / breadth -> rows.pkl
python -I 05_options_engine.py    # options straddles + quoteSummary (revisions, short int.) -> engine.pkl
python -I 06_iv_and_inputs.py     # straddle IV, touch/stop formulas, factor inputs -> scored.pkl
python -I 07_score.py             # weighted 0-10 score -> ranked.pkl
python -I mc7.py                  # bootstrap Monte Carlo for the entry->exit window -> mc7.pkl
python -I 09_rank_window.py       # re-score catalyst for the window -> rank7.pkl
python -I 10_pool.py              # tournament candidate pool -> pool.pkl
python -I 11_joint_sim.py         # correlated simulation over the window -> joint.pkl
python -I 12_quality_filter.py    # revisions / event-skew / size filters -> quality.pkl
python -I 12b_redteam.py          # red-team flags A-E,N + industry + latest price -> redteam.pkl
python -I 13_win_search.py        # best rule-following 4-name baskets by P(win) vs a class field -> win5.pkl
python -I 17_today.py             # answer card for the best basket -> today.json
# Optional, for a basket you choose yourself:
#   python -I 14_term_structure.py TICKER1 TICKER2 ...   (IV by expiry, implied event move)
#   fill the EDIT block in 15_final_report.py, then run it (stops, shares, basket distribution, win odds)
#   python -I 16_field_winodds.py                         (win odds vs class size / concentration)
