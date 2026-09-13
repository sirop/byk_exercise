"""Regime dependence of the CMO result (Appendix limitation: single bull regime).

The CMO is computed on ^DJI itself, so unlike the McClellan Oscillator it needs no
constituent roster and can be tested on the full available history. Membership data
is the only thing that confined the main analysis to 2016-2026.

Every test from sections 5.1-5.4 is re-applied per regime, so the regimes are
compared on the corrected statistics, not on the naive ones.
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

REGIMES = [
    ("1992-2000 bull", "1992-01-01", "1999-12-31"),
    ("2000-2010 sideways/bear", "2000-01-01", "2009-12-31"),
    ("2010-2016 bull", "2010-01-01", "2016-09-11"),
    ("2016-2026 bull (main sample)", "2016-09-12", "2026-09-11"),
    ("full history 1992-2026", "1992-01-01", "2026-09-11"),
]
HORIZONS = [5, 10, 20]


def cmo(series, window=20):
    diff = series.diff()
    g, l = diff.clip(lower=0), -diff.clip(upper=0)
    sg, sl = g.rolling(window).sum(), l.rolling(window).sum()
    d = sg + sl
    return 100 * (sg - sl) / d.where(d != 0)


def non_overlapping_p(sub, h):
    out = []
    for off in range(h):
        s = sub.iloc[off::h]
        a = s.loc[s.signal == 1, "fwd"]
        b = s.loc[s.signal == 0, "fwd"]
        if len(a) < 5 or len(b) < 5:
            continue
        t, p = stats.ttest_ind(a, b, equal_var=False)
        out.append(p)
    return (float(np.median(out)), float(np.min(out)), len(out)) if out else (np.nan,) * 3


def block_bootstrap_p(y, signal, block_len, n_boot=5000, seed=0):
    rng = np.random.default_rng(seed)
    y = np.asarray(y, float)
    s = np.asarray(signal, bool)
    n = len(y)
    observed = y[s].mean() - y[~s].mean()
    nb = int(np.ceil(n / block_len))
    off = np.arange(block_len)
    draws = np.empty(n_boot)
    for b in range(n_boot):
        st = rng.integers(0, n, size=nb)
        idx = ((st[:, None] + off[None, :]).ravel() % n)[:n]
        ys, ss = y[idx], s[idx]
        draws[b] = (ys[ss].mean() - ys[~ss].mean()) if ss.any() and not ss.all() else np.nan
    draws = draws[~np.isnan(draws)]
    null = draws - draws.mean()
    return float((np.abs(null) >= abs(observed)).mean())


close = pd.read_pickle("dji_long.pkl")
rows = []
for label, a, b in REGIMES:
    px = close.loc[a:b]
    c = cmo(px, 20)
    df = pd.DataFrame({"close": px, "cmo": c})
    for h in HORIZONS:
        df["fwd_%d" % h] = df["close"].shift(-h) / df["close"] - 1
    for signame, sig in (("CMO < -30", df.cmo < -30), ("CMO > 30", df.cmo > 30)):
        for h in HORIZONS:
            sub = df.dropna(subset=["cmo", "fwd_%d" % h]).copy()
            sub["fwd"] = sub["fwd_%d" % h]
            sub["signal"] = sig.reindex(sub.index).fillna(False).astype(int)
            nsig = int(sub.signal.sum())
            if nsig < 20:
                continue
            aa = sub.loc[sub.signal == 1, "fwd"]
            bb = sub.loc[sub.signal == 0, "fwd"]
            tn, pn = stats.ttest_ind(aa, bb, equal_var=False)
            X = sm.add_constant(sub.signal)
            hac = sm.OLS(sub.fwd, X).fit(cov_type="HAC", cov_kwds={"maxlags": h})
            epi = (sub.signal != sub.signal.shift()).cumsum()
            clu = sm.OLS(sub.fwd, X).fit(cov_type="cluster", cov_kwds={"groups": epi})
            nmed, nmin, noff = non_overlapping_p(sub, h)
            pb = block_bootstrap_p(sub.fwd, sub.signal.astype(bool), h)
            rows.append({
                "regime": label, "signal": signame, "h": h, "n_days": len(sub),
                "n_sig": nsig, "n_epi": int(epi.nunique()),
                "effect_pct": 100 * (aa.mean() - bb.mean()),
                "t_naive": tn, "p_naive": pn,
                "t_hac": hac.tvalues["signal"], "p_hac": hac.pvalues["signal"],
                "p_clu": clu.pvalues["signal"],
                "p_nov_med": nmed, "p_nov_min": nmin, "n_off": noff, "p_boot": pb})

res = pd.DataFrame(rows)
res.to_csv("regime_results.csv", index=False)

lines = []
for h in HORIZONS:
    for signame in ("CMO < -30", "CMO > 30"):
        q = res[(res.h == h) & (res.signal == signame)]
        if not len(q):
            continue
        lines.append("\n=== %s, h = %d ===" % (signame, h))
        lines.append("%-30s %6s %6s %9s %8s %8s %8s %9s %8s"
                     % ("regime", "n_sig", "n_epi", "effect%", "p_naive",
                        "p_hac", "p_clu", "p_nov_med", "p_boot"))
        for _, r in q.iterrows():
            lines.append("%-30s %6d %6d %+9.2f %8.4f %8.3f %8.3f %9.2f %8.3f"
                         % (r.regime, r.n_sig, r.n_epi, r.effect_pct, r.p_naive,
                            r.p_hac, r.p_clu, r.p_nov_med, r.p_boot))

key = res[(res.signal == "CMO < -30") & (res.h == 20)]
lines.append("\n=== the one borderline signal (CMO < -30, h = 20) across regimes ===")
lines.append("sign of effect consistent: %s"
             % ("yes" if (key.effect_pct > 0).all() or (key.effect_pct < 0).all() else "NO"))
lines.append("effect range: %+.2f%% .. %+.2f%%" % (key.effect_pct.min(), key.effect_pct.max()))
lines.append("p_hac range: %.3f .. %.3f" % (key.p_hac.min(), key.p_hac.max()))
lines.append("p_nov_med range: %.2f .. %.2f" % (key.p_nov_med.min(), key.p_nov_med.max()))
sig_any = res[(res.p_hac < 0.05) | (res.p_nov_med < 0.05)]
lines.append("\nrows significant at 5%% on p_hac OR p_nov_med: %d of %d"
             % (len(sig_any), len(res)))
if len(sig_any):
    lines.append(sig_any[["regime", "signal", "h", "effect_pct", "p_hac", "p_nov_med"]]
                 .to_string(index=False))
naive_sig = res[res.p_naive < 0.05]
lines.append("\nrows significant at 5%% on the NAIVE test: %d of %d" % (len(naive_sig), len(res)))
lines.append(naive_sig[["regime", "signal", "h", "effect_pct", "p_naive", "p_hac", "p_nov_med"]]
             .to_string(index=False))

open("regime_results.log", "w", encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
