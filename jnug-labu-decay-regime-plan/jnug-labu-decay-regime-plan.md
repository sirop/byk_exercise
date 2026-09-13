# JNUG/LABU Decay-vs-Regime Model — Plan

**Trader:** Seeking-Invests (Max Risch)
**Objective:** Determine whether his JNUG/LABU shorts are a valid decay-harvest strategy currently misapplied in a trending regime, or a structurally broken thesis. Output a concrete stop/keep-copying signal, not a price forecast.

## Context

- 7 open JNUG shorts (May–Aug 2025), leverage 1x–5x, combined unrealized loss ~$350
- 5 open LABU shorts (Oct 2025–Jun 2026), leverage 1x–2x, combined unrealized loss ~$172
- Both are daily-reset leveraged ETFs — return over any period >1 day is path-dependent, not a simple multiple of the underlying's return
- Predicting price directly fights the same efficient-market wall as any other price predictor. The tractable, decision-useful question is: what regime was he shorting into, and how much decay should that have produced vs. what actually happened?

## Phase 0 — Measurement contract and data pull

Freeze the following choices before inspecting historical results. This makes the output a reproducible decision analysis rather than a post-hoc explanation.

- **Instrument and benchmark:** Pull JNUG and LABU daily OHLCV from yfinance since inception. Obtain each fund's stated daily benchmark and multiplier from the issuer prospectus, including any historical benchmark or methodology changes. Use GDXJ only as a labeled liquid proxy for JNUG's benchmark unless index-return data are available; verify the LABU/XBI benchmark relationship rather than assuming it is exact.
- **Pricing:** Retain raw closes for reconciling portfolio fills and broker P&L. Use adjusted closes or a documented total-return series for return analysis. Create a split-adjustment map so each broker entry rate can be reconciled to the price series.
- **Position inputs:** Cross-reference all 12 open short entries: trade date, entry price, shares, account-level leverage, current broker-marked P&L, and any closed predecessor positions that are part of the same strategy. Keep the trader's account-level leverage separate from each ETF's daily leverage.
- **Short economics:** Record actual borrow fees, margin interest, distributions owed, and recalls where the broker provides them. Where unavailable, report gross short results and a sensitivity range using explicitly stated annual carrying-cost assumptions; do not treat ETF decay as net short profit.
- **Timing and horizons:** A signal calculated from day $t$ close may be entered only at day $t+1$ open (or next available close, if that is the portfolio convention). Evaluate fixed holding horizons of 30, 60, 90, 180, 270, and 365 trading days. Open positions are reported through their latest available day and identified as incomplete for longer horizons.

## Phase 1 — Daily-reset attribution

- For every rolling horizon, calculate the benchmark daily-reset comparator using the issuer multiplier $L$:

$$
R_{\mathrm{daily\ reset}} = \prod_{t=1}^{T}(1 + Lr_t) - 1
$$

- Report three distinct quantities: benchmark cumulative return, daily-reset comparator return, and ETF total return. The ETF-minus-comparator residual captures fees, tracking differences, and data/index mismatch; it is not automatically volatility decay.
- Quantify volatility drag separately by comparing the daily-reset comparator with $L$ times the benchmark cumulative return. Plot this value against realized benchmark volatility and benchmark direction, because favorable or adverse compounding depends on both path volatility and trend.
- Apply the same calculations to every JNUG and LABU entry through the current date. Reconcile modeled gross short P&L with broker P&L before interpreting any difference as a strategy effect.

## Phase 2 — Precommitted regime classification

- Define the rule in code before examining entry outcomes: 50-day and 200-day simple moving averages, a 20-trading-day slope for the 50-day average, and 14-day ADX. Classify a day as **trending** when price is on the trend side of the 200-day average, the 50-day slope has the same directional sign, and ADX is at least 25; otherwise classify it as **choppy/indeterminate**. Preserve bull and bear trend direction as separate fields.
- Calculate all indicator values with data available at the prior close and assign the classification to the following tradable day. Exclude days without sufficient lookback history.
- Report historical regime base rates and the regime path after each of the 12 entries. Run a predeclared sensitivity check with ADX thresholds of 20 and 30 and slope windows of 10 and 40 days; conclusions must not depend on a single boundary.
- Critical check: test the working hypothesis that the May 2025–June 2026 entries were established during sustained, adverse trends rather than choppy markets.

## Phase 3 — Historical no-stop risk distribution

- Create historical short-entry events from every eligible trading day, labelled by the phase-2 regime observed on the preceding close. Use non-overlapping entries within each horizon, or report block-bootstrap confidence intervals, to avoid presenting highly overlapping rolling windows as independent evidence.
- For each instrument, regime, direction, and fixed horizon, calculate gross short terminal return, maximum adverse excursion (MAE), maximum favorable excursion, and the proportion of positions still adverse at the horizon. Calculate net-return sensitivity after carrying costs.
- Do not exclude paths that fail to mean-revert within the sample. Report their terminal outcome at the fixed horizon; do not characterize an outcome as "before mean reversion" unless reversion is precisely defined and separately reported.
- Report medians, 75th/90th/95th MAE percentiles, sample sizes, and worst observed values. Treat sparse regime/horizon cells as descriptive only.

## Phase 4 — Decision output

- One table for all 12 open positions: instrument, entry date and split-adjusted entry price, shares and account leverage, entry regime and subsequent regime path, days held, broker P&L, modeled gross and net short return, current MAE, and its percentile in the matching phase-3 distribution.
- State a precommitted trader-level signal:
  - **Stop copying / no new shorts:** entry regime is trending, or net historical expectancy for the matching regime and horizon is non-positive, or the position breaches a predefined portfolio risk limit.
  - **Eligible only with controls:** entry is choppy/indeterminate, net expectancy remains positive after carrying-cost sensitivity, and a position-size and maximum-loss limit are specified.
  - **Insufficient evidence:** the matching historical cell is sparse, benchmark mapping is unresolved, or actual short carrying costs cannot be bounded.
- A percentile is descriptive, not a stop rule. Define the portfolio risk limit before viewing the position table; for example, maximum loss per position and maximum aggregate loss as percentages of account equity.
- Feed the entry-regime result, carrying-cost uncertainty, and any breached risk limit into the KPI scorecard as trader-level risk flags.

## Stack

pandas, yfinance, matplotlib — same as existing project setup, no new dependencies. sqlite3 optional if persisting regime-tagged history for reuse across other traders' leveraged-ETF positions. Index total-return data or issuer factsheets may be required to replace proxy benchmarks; record the source and retrieval date.

## Status

Revised. Next: Phase 0 (measurement contract, issuer benchmark verification, portfolio reconciliation) followed by Phase 1. Do not interpret decay or issue a copy/stop signal until the gross short return reconciles to portfolio P&L and carrying-cost uncertainty is stated.
