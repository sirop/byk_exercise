# -*- coding: utf-8 -*-
"""Does the point-in-time McClellan oversold effect add anything over the CMO?

Repeats mcc_vs_cmo.py, but on the point-in-time roster of mcclellan_pit.py instead
of the fixed survivor basket. mcclellan_pit.py leaves one candidate effect standing
on HAC alone (full history oversold h=20, +0.99%, p_hac 0.0046; 2000-2010 bear
+1.62%, p_hac 0.0020). Both look like the section 6.4 CMO effect, because the CMO
and breadth are both "the market has fallen" detectors.
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import statsmodels.api as sm

src = open("mcclellan_pit.py", encoding="utf-8").read()
src = src.split("rows = []\nfor label, a, b in REGIMES:")[0]
g = {"__name__": "prelude"}
exec(compile(src, "prelude", "exec"), g)
dji, eff, mcc = g["dji"], g["eff"], g["mcc"]

out = []
P = out.append
m = mcc(eff)

d = dji.diff()
gn, ls = d.clip(lower=0), -d.clip(upper=0)
sg, sl = gn.rolling(20).sum(), ls.rolling(20).sum()
den = sg + sl
cmo = 100 * (sg - sl) / den.where(den != 0)

half = m.index[len(m) // 2]
thr = m.loc[:half].quantile(0.05)
P("McClellan oversold threshold (held-out first half): %.4f" % thr)

df = pd.DataFrame({"fwd": dji.shift(-20) / dji - 1,
                   "mcc_sig": (m < thr).astype(float),
                   "cmo_sig": (cmo < -30).astype(float)}).dropna()
P("days %d   McClellan %d (%.2f%%)   CMO %d (%.2f%%)"
  % (len(df), int(df.mcc_sig.sum()), 100 * df.mcc_sig.mean(),
     int(df.cmo_sig.sum()), 100 * df.cmo_sig.mean()))
both = int(((df.mcc_sig == 1) & (df.cmo_sig == 1)).sum())
P("both fire: %d  (%.1f%% of McClellan days, %.1f%% of CMO days)   phi %.4f"
  % (both, 100 * both / df.mcc_sig.sum(), 100 * both / df.cmo_sig.sum(),
     df.mcc_sig.corr(df.cmo_sig)))

P("\n--- separate ---")
for nm in ("mcc_sig", "cmo_sig"):
    f = sm.OLS(df.fwd, sm.add_constant(df[nm])).fit(
        cov_type="HAC", cov_kwds={"maxlags": 20})
    P("%-8s alone: coef %+.4f  t %+.2f  p %.4f"
      % (nm, f.params[nm], f.tvalues[nm], f.pvalues[nm]))

P("\n--- joint ---")
f = sm.OLS(df.fwd, sm.add_constant(df[["mcc_sig", "cmo_sig"]])).fit(
    cov_type="HAC", cov_kwds={"maxlags": 20})
for nm in ("mcc_sig", "cmo_sig"):
    P("%-8s joint: coef %+.4f  t %+.2f  p %.4f"
      % (nm, f.params[nm], f.tvalues[nm], f.pvalues[nm]))

P("\n--- conditional means, 20d forward ---")
base = df.loc[(df.mcc_sig == 0) & (df.cmo_sig == 0), "fwd"].mean()
P("neither (baseline)    : %+.3f%%  n=%d"
  % (100 * base, int(((df.mcc_sig == 0) & (df.cmo_sig == 0)).sum())))
for lab, msk in (("McClellan only", (df.mcc_sig == 1) & (df.cmo_sig == 0)),
                 ("CMO only", (df.mcc_sig == 0) & (df.cmo_sig == 1)),
                 ("both", (df.mcc_sig == 1) & (df.cmo_sig == 1))):
    if msk.sum():
        P("%-22s: %+.3f%%  n=%d  (vs baseline %+.3f%%)"
          % (lab, 100 * df.loc[msk, "fwd"].mean(), int(msk.sum()),
             100 * (df.loc[msk, "fwd"].mean() - base)))

# the 2000-2010 bear window, where the strongest HAC row sits
P("\n--- 2000-2010 bear window only ---")
sub = df.loc["2000-01-01":"2009-12-31"]
f = sm.OLS(sub.fwd, sm.add_constant(sub[["mcc_sig", "cmo_sig"]])).fit(
    cov_type="HAC", cov_kwds={"maxlags": 20})
for nm in ("mcc_sig", "cmo_sig"):
    P("%-8s joint: coef %+.4f  t %+.2f  p %.4f"
      % (nm, f.params[nm], f.tvalues[nm], f.pvalues[nm]))

open("mcc_vs_cmo_pit.log", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
