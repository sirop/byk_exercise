# -*- coding: utf-8 -*-
"""How much does an INCOMPLETE roster move the McClellan p-values?

The long-history McClellan test is blocked because ~4-6 pre-2016 members are
unobtainable (dead tickers behind paywalls). Before paying for them, measure
whether they would matter: in the 2016-2026 window the true point-in-time roster
IS known, so the error a k-name-short roster induces can be simulated directly.

Two experiments:
  A. random dropout - remove k of 30 names, recompute all 9 signals, measure the
     p-value displacement. Gives an empirical bias bound as a function of k.
  B. survivorship bias - use the END-of-sample roster held fixed backwards (the
     construction you are forced into without membership history) and compare to
     the true point-in-time roster. Gives the bias of the cheap approach.
"""
import io, re, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import statsmodels.api as sm

out = []
P = out.append

src = open("dj30_pipeline.py", encoding="utf-8").read().split("HORIZONS = [5,10,20]")[0]
src = re.sub(r"data = yf\.download\(.*?\)\n",
             'data = pd.read_pickle("dj30_raw.pkl")\n', src, count=1, flags=re.S)
src = src.replace('data.to_pickle("dj30_raw.pkl")', '')
assert "yf.download" not in src
buf, real = io.StringIO(), sys.stdout
sys.stdout = buf
g = {}
exec(compile(src, "prelude", "exec"), g)
sys.stdout = real
closes, mask, dj30 = g["closes"], g["mask"], g["dj30"]
MEMBERS_AT_END = g["MEMBERS_AT_END"]

fwd = {h: dj30.shift(-h) / dj30 - 1 for h in (5, 10, 20)}


def mcc_from(m):
    dc = closes.diff().where(m)
    net = (dc > 0).sum(axis=1) - (dc < 0).sum(axis=1)
    return (net.ewm(span=19, adjust=False).mean()
            - net.ewm(span=39, adjust=False).mean()).iloc[100:]


def battery(series):
    half = series.index[len(series) // 2]
    os_ = series.loc[:half].quantile(0.05)
    ob = series.loc[:half].quantile(0.95)
    res = {}
    for nm, sig in (("zero-cross", (series > 0) & (series.shift() <= 0)),
                    ("oversold", series < os_), ("overbought", series > ob)):
        for h in (5, 10, 20):
            d = pd.DataFrame({"y": fwd[h], "s": sig.astype(int)}).dropna()
            d = d.loc[series.index.intersection(d.index)]
            if d.s.sum() < 5:
                continue
            f = sm.OLS(d.y, sm.add_constant(d.s)).fit(
                cov_type="HAC", cov_kwds={"maxlags": h})
            res[(nm, h)] = f.pvalues["s"]
    return res


TRUE = battery(mcc_from(mask))
P("=== baseline: true point-in-time roster, 30 names ===")
P("min p %.4f   median p %.4f" % (min(TRUE.values()), float(np.median(list(TRUE.values())))))

# ---------- experiment A: random k-name dropout ----------
P("\n=== A. roster missing k of 30 names (200 draws each) ===")
P("%3s %9s %9s %9s %9s %9s" % ("k", "med|dp|", "p90|dp|", "max|dp|",
                               "min p seen", "#sig@5%"))
rng = np.random.default_rng(0)
cols = list(closes.columns)
rows = []
for k in (1, 2, 3, 4, 6):
    disp, minp, nsig = [], [], 0
    for _ in range(200):
        drop = rng.choice(cols, size=k, replace=False)
        m2 = mask.copy()
        m2[list(drop)] = False
        r = battery(mcc_from(m2))
        d = [abs(r[key] - TRUE[key]) for key in TRUE if key in r]
        disp.extend(d)
        mp = min(r.values())
        minp.append(mp)
        nsig += sum(v < 0.05 for v in r.values())
    P("%3d %9.4f %9.4f %9.4f %9.4f %9d"
      % (k, float(np.median(disp)), float(np.percentile(disp, 90)),
         float(np.max(disp)), float(np.min(minp)), nsig))
    rows.append((k, float(np.max(disp)), float(np.min(minp)), nsig))

# ---------- experiment B: survivorship-biased fixed roster ----------
P("\n=== B. survivorship bias: end-of-sample roster held fixed backwards ===")
P("This is the construction you are forced into with no membership history at all.")
surv = pd.DataFrame(False, index=mask.index, columns=mask.columns)
for t in MEMBERS_AT_END:
    if t in surv.columns:
        surv[t] = closes[t].notna()
P("end-of-sample roster: %d names; member-days %d (true roster: %d)"
  % (len(MEMBERS_AT_END), int(surv.sum().sum()), int(mask.sum().sum())))
diff_days = int((surv != mask).sum().sum())
P("member-days where the two rosters disagree: %d of %d (%.2f%%)"
  % (diff_days, int(mask.sum().sum()), 100 * diff_days / mask.sum().sum()))
SB = battery(mcc_from(surv))
P("\n%-12s %-4s %9s %9s %9s" % ("signal", "h", "p(true)", "p(surv)", "|diff|"))
for key in TRUE:
    if key in SB:
        P("%-12s %-4d %9.4f %9.4f %9.4f"
          % (key[0], key[1], TRUE[key], SB[key], abs(TRUE[key] - SB[key])))
P("max |dp| from survivorship bias = %.4f"
  % max(abs(TRUE[k2] - SB[k2]) for k2 in TRUE if k2 in SB))
P("min p under survivorship bias = %.4f (true: %.4f)"
  % (min(SB.values()), min(TRUE.values())))

P("\n=== what this means for extending McClellan before 2016 ===")
worst = max(r[1] for r in rows)
P("Largest p-displacement from dropping up to 6 of 30 names: %.4f" % worst)
P("Smallest p ever produced by a mutilated roster:            %.4f"
  % min(r[2] for r in rows))
P("Significant cells produced across all %d dropout draws:     %d"
  % (200 * 5 * 9, sum(r[3] for r in rows)))

open("roster_bias.log", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
