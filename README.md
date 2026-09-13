# byk_exercise

Quantitative market-analysis exercises. Two independent pieces of work, each a written
analysis backed by the scripts that produced its numbers.

## Contents

### `Oscillator/` — Do the CMO and McClellan Oscillator work on the DJ30?

[`dj30_cmo_mcclellan_analysis.md`](Oscillator/dj30_cmo_mcclellan_analysis.md) is the
deliverable: a ~90 KB write-up answering whether the Chande Momentum Oscillator and the
McClellan Oscillator give a defensible signal on the Dow Jones 30.

Headline: on the 10-year window neither indicator survives a correct treatment of the
autocorrelation induced by overlapping return windows. Extended to 34 years of history
the CMO result is revised upward to a consistent effect (+1.54% over 20 days, p = 0.001
HAC) but still short of a trading claim; the McClellan Oscillator shows nothing at any
horizon, in any of three breadth constructions, across five regimes.

The document carries its own revision log (§0) of errors found and fixed, a limitations
register (Appendix), and a prior-art review (§7) that states up front how completely each
venue could actually be searched.

Scripts, in rough order of dependency:

| Script | What it does |
|---|---|
| `dj30_pipeline.py` | Downloads `^DJI` and constituents, builds the point-in-time membership mask, computes both oscillators and the 2016–2026 test battery |
| `recompute.py` | Re-runs the headline tables after the v1 corrections |
| `regime_test.py` | Regime-split CMO tests on 34 years |
| `roster_bias.py` | Dropout experiment measuring what an incomplete roster does to p-values |
| `mcclellan_long.py` | Bias-bounded pre-2016 McClellan run on a fixed survivor basket (§6.6) |
| `mcclellan_pit.py` | Rebuilt point-in-time roster 1992–2026 and the same battery on it (§6.7) |
| `mcc_vs_cmo.py`, `mcc_vs_cmo_pit.py` | Joint regressions testing whether McClellan adds anything over the CMO |
| `resolve_limitations.py` | Computations closing out the limitations register |
| `wba_validation.py` | Cross-vendor check of the spliced WBA series |

Each writes a `.log` next to itself; the result tables the document cites are the
committed `*_results.csv` files.

### `jnug-labu-decay-regime-plan/` — Leveraged-ETF decay by volatility regime

[`jnug-labu-decay-regime-plan.md`](jnug-labu-decay-regime-plan/jnug-labu-decay-regime-plan.md)
with `analyze_decay_regimes.py` and its `analysis-output/` tables.

## Running the Oscillator scripts

```
pip install yfinance pandas numpy statsmodels scipy requests
cd Oscillator
python dj30_pipeline.py
```

Market data is pulled from Yahoo Finance at run time. Two caveats:

- **Cached vendor data is not committed.** The `.pkl` caches, `tiingo_all.json`,
  `wba_*.json` and `aa_stooq.csv` are licensed vendor data and are gitignored. The
  scripts re-download what they need.
- **WBA needs a Tiingo token.** Walgreens went private, so Yahoo no longer serves it.
  `dj30_pipeline.py` reads `TIINGO_TOKEN` from the environment and falls back to a local
  `wba_tiingo.json` cache; with neither, it warns and WBA is missing (the 29-name gap the
  document discusses in §1.1a). `mcclellan_pit.py` requires that cache or token outright.

## Credentials

No credentials are committed. `Oscillator/API_KEYS`, `config.properties` and
`.vscode/mcp.json` are gitignored. Export `TIINGO_TOKEN` for the data pipeline; see
`dj30_pipeline.py` for how it is read.
