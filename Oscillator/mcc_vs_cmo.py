# -*- coding: utf-8 -*-
"""Does the long-history McClellan 'oversold' effect add anything over the CMO?

mcclellan_long.py found McClellan oversold at h=20 giving +0.98% on 1992-2026
(p_hac 0.011). Section 6.4 already found CMO < -30 at h=20 giving +1.54%. Both are
"the market has fallen" detectors, so the question is whether they are one effect.
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import statsmodels.api as sm
import yfinance as yf

SURV = ["AXP", "BA", "CAT", "CSCO", "CVX", "DD", "DIS", "GE", "HD", "HON",
        "IBM", "INTC", "JNJ", "JPM", "KO", "MCD", "MMM", "MRK", "MSFT", "NKE",
        "PFE", "PG", "RTX", "SHW", "TRV", "UNH", "VZ", "WMT", "XOM", "AAPL"]
out = []
P = out.append

raw = yf.download(SURV + ["^DJI"], start="1992-01-01", end="2026-09-12",
                  group_by="ticker", auto_adjust=True, threads=True, progress=False)
closes = pd.DataFrame({t: raw[(t, "Close")] for t in SURV})
dji = raw[("^DJI", "Close")].dropna()
closes = closes.reindex(dji.index)

dc = closes.diff()
net = (dc > 0).sum(axis=1) - (dc < 0).sum(axis=1)
mc = (net.ewm(span=19, adjust=False).mean()
      - net.ewm(span=39, adjust=False).mean()).iloc[100:]

d = dji.diff()
g, l = d.clip(lower=0), -d.clip(upper=0)
sg, sl = g.rolling(20).sum(), l.rolling(20).sum()
den = sg + sl
cmo = 100 * (sg - sl) / den.where(den != 0)

half = mc.index[len(mc) // 2]
thr = mc.loc[:half].quantile(0.05)
P("McClellan oversold threshold (held-out first half): %.4f" % thr)

df = pd.DataFrame({"fwd": dji.shift(-20) / dji - 1,
                   "mcc_sig": (mc < thr).astype(float),
                   "cmo_sig": (cmo < -30).astype(float)}).dropna()
P("days %d   McClellan signal %d (%.2f%%)   CMO signal %d (%.2f%%)"
  % (len(df), int(df.mcc_sig.sum()), 100 * df.mcc_sig.mean(),
     int(df.cmo_sig.sum()), 100 * df.cmo_sig.mean()))
both = int(((df.mcc_sig == 1) & (df.cmo_sig == 1)).sum())
P("days where BOTH fire: %d  -> %.1f%% of McClellan days, %.1f%% of CMO days"
  % (both, 100 * both / df.mcc_sig.sum(), 100 * both / df.cmo_sig.sum()))
P("phi correlation of the two indicators: %.4f" % df.mcc_sig.corr(df.cmo_sig))

P("\n--- separate regressions ---")
for nm in ("mcc_sig", "cmo_sig"):
    f = sm.OLS(df.fwd, sm.add_constant(df[nm])).fit(
        cov_type="HAC", cov_kwds={"maxlags": 20})
    P("%-8s alone: coef %+.4f  t %+.2f  p %.4f"
      % (nm, f.params[nm], f.tvalues[nm], f.pvalues[nm]))

P("\n--- joint regression: both in at once ---")
f = sm.OLS(df.fwd, sm.add_constant(df[["mcc_sig", "cmo_sig"]])).fit(
    cov_type="HAC", cov_kwds={"maxlags": 20})
for nm in ("mcc_sig", "cmo_sig"):
    P("%-8s joint: coef %+.4f  t %+.2f  p %.4f"
      % (nm, f.params[nm], f.tvalues[nm], f.pvalues[nm]))

P("\n--- conditional means (20d forward excess) ---")
base = df.loc[(df.mcc_sig == 0) & (df.cmo_sig == 0), "fwd"].mean()
P("neither fires (baseline)      : %+.3f%%  n=%d"
  % (100 * base, int(((df.mcc_sig == 0) & (df.cmo_sig == 0)).sum())))
for lab, m in (("McClellan only", (df.mcc_sig == 1) & (df.cmo_sig == 0)),
               ("CMO only", (df.mcc_sig == 0) & (df.cmo_sig == 1)),
               ("both", (df.mcc_sig == 1) & (df.cmo_sig == 1))):
    if m.sum():
        P("%-30s: %+.3f%%  n=%d  (vs baseline %+.3f%%)"
          % (lab, 100 * df.loc[m, "fwd"].mean(), int(m.sum()),
             100 * (df.loc[m, "fwd"].mean() - base)))

open("mcc_vs_cmo.log", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
