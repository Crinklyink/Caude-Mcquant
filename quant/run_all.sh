#!/usr/bin/env bash
# Run from inside quant/. Edit the date constants listed in CLAUDE.md ("Dates to update") FIRST.
# Needs: python 3, numpy, outbound HTTPS (Yahoo Finance + Nasdaq endpoints).
set -euo pipefail
python -I 01_universe.py          # US stocks > $1B, price > $5  -> univ_all.json
python -I 02_history.py           # 2y daily bars for the liquid ones -> hist.json
python -I 03_earnings_calendar.py # Nasdaq earnings calendar -> earnings.json
python -I 04_metrics.py           # trend / RS / ATR / base rate / breadth -> rows.pkl
python -I 05_options_engine.py    # options straddles + quoteSummary (revisions, short int.) -> engine.pkl
python -I 06_iv_and_inputs.py     # straddle IV, touch/stop formulas, factor inputs -> scored.pkl
python -I 07_score.py             # weighted 0-10 score -> ranked.pkl
python -I mc7.py                  # bootstrap Monte Carlo for the entry->exit window -> mc7.pkl
python -I 09_rank_window.py       # re-score catalyst for the window -> rank7.pkl
python -I 10_pool.py              # tournament candidate pool -> pool.pkl
python -I 11_joint_sim.py         # correlated 7-session simulation -> joint.pkl
python -I 12_quality_filter.py    # revisions / event-skew / size filters -> quality.pkl
python -I 13_win_search.py        # best 4-name baskets by P(win) vs a class field
# Then, for finalists:
#   python -I 14_term_structure.py TICKER1 TICKER2 ...   (IV by expiry, implied event move)
#   edit + run 15_final_report.py                         (stops, shares, basket distribution, win odds)
#   python -I 16_field_winodds.py                         (win odds vs class size / concentration)
