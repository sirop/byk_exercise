# -*- coding: utf-8 -*-
"""Extend the McClellan test to 1992-2026 on a SURVIVORSHIP-BIASED fixed roster.

The true point-in-time roster is unavailable before 2016 (dead tickers are behind
paywalls at both vendors). roster_bias.py measured what that costs: with the
end-of-sample roster held fixed backwards - exactly the construction used here -
30.3% of member-days are mis-assigned and individual p-values move by up to 0.544,
but the minimum p across all nine signals still came to 0.40, and across 9,000
random-dropout draws only 1 cell in 9,000 ever reached p < 0.05.

So this construction cannot be trusted for a point estimate of p, but it CAN
answer the binary question "does a signal appear anywhere?", because roster damage
adds noise without manufacturing significance. If this test returns nothing, the
McClellan null extends to 1992 without buying the dead tickers. If it returns
something, that is when the data purchase becomes justified.
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import yfinance as yf

SURV = ["AXP", "BA", "CAT", "CSCO", "CVX", "DD", "DIS", "GE", "HD", "HON",
        "IBM", "INTC", "JNJ", "JPM", "KO", "MCD", "MMM", "MRK", "MSFT", "NKE",
        "PFE", "PG", "RTX", "SHW", "TRV", "UNH", "VZ", "WMT", "XOM", "AAPL"]
HORIZONS = [5, 10, 20]
REGIMES = [("1992-2000 bull", "1992-01-01", "1999-12-31"),
           ("2000-2010 sideways/bear", "2000-01-01", "2009-12-31"),
           ("2010-2016 bull", "2010-01-01", "2016-09-11"),
           ("2016-2026 bull", "2016-09-12", "2026-09-11"),
           ("full history 1992-2026", "1992-01-01", "2026-09-11")]

out = []
P = out.append

raw = yf.download(SURV + ["^DJI"], start="1992-01-01", end="2026-09-12",
                  group_by="ticker", auto_adjust=True, threads=True, progress=False)
closes = pd.DataFrame({t: raw[(t, "Close")] for t in SURV})
dji = raw[("^DJI", "Close")].dropna()
closes = closes.reindex(dji.index)
cov = closes.notna().sum(axis=1)
P("universe: %d fixed survivor names, %d trading days %s .. %s"
  % (len(SURV), len(dji), dji.index[0].date(), dji.index[-1].date()))
P("names priced per day: min %d, median %d, days below 30: %d"
  % (cov.min(), int(cov.median()), int((cov < 30).sum())))
P("member-days: %d" % int(closes.notna().sum().sum()))


def mcc(px):
    dc = px.diff()
    net = (dc > 0).sum(axis=1) - (dc < 0).sum(axis=1)
    return (net.ewm(span=19, adjust=False).mean()
            - net.ewm(span=39, adjust=False).mean()).iloc[100:]


def non_overlapping_p(sub, h):
    ps = []
    for off in range(h):
        s = sub.iloc[off::h]
        a, b = s.loc[s.signal == 1, "fwd"], s.loc[s.signal == 0, "fwd"]
        if len(a) < 5 or len(b) < 5:
            continue
        ps.append(stats.ttest_ind(a, b, equal_var=False)[1])
    return (float(np.median(ps)), float(np.min(ps)), len(ps)) if ps else (np.nan,) * 3


def block_bootstrap_p(y, sig, block_len, n_boot=3000, seed=0):
    rng = np.random.default_rng(seed)
    y = np.asarray(y, float); s = np.asarray(sig, bool); n = len(y)
    observed = y[s].mean() - y[~s].mean()
    nb = int(np.ceil(n / block_len)); off = np.arange(block_len)
    draws = np.empty(n_boot)
    for b in range(n_boot):
        st = rng.integers(0, n, size=nb)
        idx = ((st[:, None] + off[None, :]).ravel() % n)[:n]
        ys, ss = y[idx], s[idx]
        draws[b] = (ys[ss].mean() - ys[~ss].mean()) if ss.any() and not ss.all() else np.nan
    draws = draws[~np.isnan(draws)]
    return float((np.abs(draws - draws.mean()) >= abs(observed)).mean())


rows = []
for label, a, b in REGIMES:
    px = closes.loc[a:b]
    ix = dji.loc[a:b]
    if len(ix) < 400:
        continue
    m = mcc(px)
    half = m.index[len(m) // 2]
    os_, ob = m.loc[:half].quantile(0.05), m.loc[:half].quantile(0.95)
    fwd = {h: ix.shift(-h) / ix - 1 for h in HORIZONS}
    for nm, sig in (("zero-cross", (m > 0) & (m.shift() <= 0)),
                    ("oversold", m < os_), ("overbought", m > ob)):
        for h in HORIZONS:
            sub = pd.DataFrame({"fwd": fwd[h], "signal": sig.astype(int)}).dropna()
            sub = sub.loc[m.index.intersection(sub.index)]
            if sub.signal.sum() < 20:
                continue
            aa, bb = sub.loc[sub.signal == 1, "fwd"], sub.loc[sub.signal == 0, "fwd"]
            X = sm.add_constant(sub.signal)
            hac = sm.OLS(sub.fwd, X).fit(cov_type="HAC", cov_kwds={"maxlags": h})
            epi = (sub.signal != sub.signal.shift()).cumsum()
            clu = sm.OLS(sub.fwd, X).fit(cov_type="cluster", cov_kwds={"groups": epi})
            nmed, nmin, _ = non_overlapping_p(sub, h)
            rows.append({"regime": label, "signal": nm, "h": h,
                         "n_sig": int(sub.signal.sum()), "n_epi": int(epi.nunique()),
                         "effect_pct": 100 * (aa.mean() - bb.mean()),
                         "p_naive": stats.ttest_ind(aa, bb, equal_var=False)[1],
                         "p_hac": hac.pvalues["signal"], "p_clu": clu.pvalues["signal"],
                         "p_nov_med": nmed,
                         "p_boot": block_bootstrap_p(sub.fwd, sub.signal.astype(bool), h)})

res = pd.DataFrame(rows)
res.to_csv("mcclellan_long_results.csv", index=False)

P("\nMcClellan oscillator range on full history: %.2f .. %.2f (std %.2f)"
  % (mcc(closes).min(), mcc(closes).max(), mcc(closes).std()))
for label, _, _ in REGIMES:
    q = res[res.regime == label]
    if not len(q):
        continue
    P("\n=== %s ===" % label)
    P("%-12s %-3s %6s %6s %9s %8s %8s %8s %9s %8s"
      % ("signal", "h", "n_sig", "n_epi", "effect%", "p_naive", "p_hac",
         "p_clu", "p_nov_med", "p_boot"))
    for _, r in q.iterrows():
        P("%-12s %-3d %6d %6d %+9.2f %8.4f %8.4f %8.4f %9.3f %8.4f"
          % (r.signal, r.h, r.n_sig, r.n_epi, r.effect_pct, r.p_naive,
             r.p_hac, r.p_clu, r.p_nov_med, r.p_boot))

P("\n=== verdict across all %d rows ===" % len(res))
P("min p_hac      %.4f   (row: %s)" % (res.p_hac.min(),
  res.loc[res.p_hac.idxmin(), ["regime", "signal", "h"]].to_dict()))
P("min p_clu      %.4f" % res.p_clu.min())
P("min p_nov_med  %.4f" % res.p_nov_med.min())
P("min p_boot     %.4f" % res.p_boot.min())
P("rows with p_hac < 0.05: %d of %d" % (int((res.p_hac < 0.05).sum()), len(res)))
P("rows with p_hac < 0.05 AND p_nov_med < 0.05: %d"
  % int(((res.p_hac < 0.05) & (res.p_nov_med < 0.05)).sum()))
P("largest |effect| %.2f%%" % res.effect_pct.abs().max())

open("mcclellan_long.log", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
