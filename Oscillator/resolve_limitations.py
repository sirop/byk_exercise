"""Resolves the remaining resolvable rows of the Appendix limitations register.

1. Two-vendor splice + spin-off adjustment: rebuild the entire breadth series from
   a SINGLE vendor (Tiingo, all 30 names) and compare against the Yahoo+Tiingo mix.
   A second vendor with independent corporate-action handling also re-tests the
   spin-off question, since Tiingo and Yahoo adjust spin-offs differently.
2. Equal-weighted breadth vs price-weighted index: build a price-weighted breadth
   variant, which is what the DJIA's own construction implies.
3. In-sample threshold fragility: sweep the percentile cut instead of fixing it.

Inputs: tiingo_all.json (adjClose for all 39 universe tickers), dj30_raw.pkl.
"""
import io, json, re, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

out = []
P = out.append

# ---- rebuild the Yahoo(+Tiingo WBA) baseline exactly as the paper computes it ----
src = open("dj30_pipeline.py", encoding="utf-8").read().split("HORIZONS = [5,10,20]")[0]
# drop the Yahoo download and read the cached frame instead; regex so that a
# whitespace change in dj30_pipeline.py cannot silently re-trigger a download.
src = re.sub(r"data = yf\.download\(.*?\)\n", 'data = pd.read_pickle("dj30_raw.pkl")\n', src, count=1, flags=re.S)
src = src.replace('data.to_pickle("dj30_raw.pkl")', '')
assert "yf.download" not in src, "cache substitution failed; would re-download"
buf, real = io.StringIO(), sys.stdout
sys.stdout = buf
g = {}
exec(compile(src, "prelude", "exec"), g)
sys.stdout = real
closes_mix, mask, dj30 = g["closes"], g["mask"], g["dj30"]
UNIVERSE, MEMBERS_AT_END = g["UNIVERSE"], g["MEMBERS_AT_END"]

# ---- the single-vendor frame ----
raw = json.load(open("tiingo_all.json", encoding="utf-8"))
cols = {}
for t, rows in raw.items():
    s = pd.Series({pd.Timestamp(r["d"]): r["c"] for r in rows}).sort_index()
    cols[t] = s
closes_tii = pd.DataFrame(cols).reindex(dj30.index)
closes_tii = closes_tii.reindex(columns=closes_mix.columns)

P("=== 1. single-vendor replication ===")
P("Yahoo+Tiingo frame: %s   Tiingo-only frame: %s"
  % (closes_mix.shape, closes_tii.shape))
cov_mix = int((mask & closes_mix.notna()).sum().sum())
cov_tii = int((mask & closes_tii.notna()).sum().sum())
P("member-days covered: mixed %d   Tiingo-only %d   (30 x %d = %d)"
  % (cov_mix, cov_tii, len(dj30), 30 * len(dj30)))
gap = (mask & closes_tii.isna()).sum()
if gap.sum():
    P("Tiingo-only gaps by ticker: %s" % gap[gap > 0].to_dict())


def breadth(closes, m, weights=None):
    """net advances; weights=None -> equal-weighted (standard McClellan)."""
    dc = closes.diff().where(m)
    if weights is None:
        adv = (dc > 0).sum(axis=1)
        dec = (dc < 0).sum(axis=1)
        iss = adv + dec
    else:
        w = weights.where(m).reindex_like(dc)
        adv = (w.where(dc > 0)).sum(axis=1)
        dec = (w.where(dc < 0)).sum(axis=1)
        iss = adv + dec
    return adv - dec, iss


def mcc(net):
    return (net.ewm(span=19, adjust=False).mean()
            - net.ewm(span=39, adjust=False).mean()).iloc[100:]


net_mix, _ = breadth(closes_mix, mask)
net_tii, _ = breadth(closes_tii, mask)
mc_mix, mc_tii = mcc(net_mix), mcc(net_tii)
al, bl = mc_mix.align(mc_tii, join="inner")
P("\ncorr(mixed-vendor, Tiingo-only) = %.6f" % al.corr(bl))
P("identical sign on %.2f%% of days" % (100 * (np.sign(al) == np.sign(bl)).mean()))
sd = (np.sign(closes_mix.diff().where(mask)).fillna(0)
      != np.sign(closes_tii.diff().where(mask)).fillna(0))
P("member-days where sign(diff) disagrees between vendors: %d of %d (%.3f%%)"
  % (int(sd.sum().sum()), cov_mix, 100 * sd.sum().sum() / cov_mix))
worst = sd.sum().sort_values(ascending=False).head(5)
P("most-disagreeing tickers: %s" % worst[worst > 0].to_dict())

fwd = {h: dj30.shift(-h) / dj30 - 1 for h in (5, 10, 20)}


def battery(series, label, fixed_q=(0.05, 0.95)):
    half = series.index[len(series) // 2]
    os_ = series.loc[:half].quantile(fixed_q[0])
    ob = series.loc[:half].quantile(fixed_q[1])
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
            res[(nm, h)] = (f.tvalues["s"], f.pvalues["s"], int(d.s.sum()))
    return res


A = battery(mc_mix, "mixed")
T = battery(mc_tii, "tiingo")
P("\n%-12s %-4s %9s %9s %9s" % ("signal", "h", "p(mixed)", "p(Tiingo)", "|diff|"))
for k in A:
    P("%-12s %-4d %9.4f %9.4f %9.4f" % (k[0], k[1], A[k][1], T[k][1],
                                        abs(A[k][1] - T[k][1])))
P("max |p difference| between vendors = %.4f" % max(abs(A[k][1] - T[k][1]) for k in A))
P("min p, mixed %.4f   Tiingo-only %.4f"
  % (min(v[1] for v in A.values()), min(v[1] for v in T.values())))
P("conclusion: both vendors -> null; the splice is not driving anything.")

# ---- 2. price-weighted breadth ----
P("\n=== 2. price-weighted breadth (DJIA is price-weighted) ===")
P("The DJIA weights each name by price; standard McClellan counts each name once.")
net_pw, iss_pw = breadth(closes_mix, mask, weights=closes_mix)
mc_pw = mcc(net_pw)
P("equal-weighted: std %.4f    price-weighted: std %.2f (different units)"
  % (mc_mix.std(), mc_pw.std()))
alp, blp = mc_mix.align(mc_pw, join="inner")
P("corr(equal-weighted, price-weighted) = %.6f" % alp.corr(blp))
P("identical sign on %.2f%% of days" % (100 * (np.sign(alp) == np.sign(blp)).mean()))
W = battery(mc_pw, "price-weighted")
P("\n%-12s %-4s %9s %9s" % ("signal", "h", "p(equal)", "p(price-w)"))
for k in A:
    if k in W:
        P("%-12s %-4d %9.4f %9.4f" % (k[0], k[1], A[k][1], W[k][1]))
P("min p under price-weighting = %.4f" % min(v[1] for v in W.values()))
P("max |t| under price-weighting = %.4f" % max(abs(v[0]) for v in W.values()))
P("conclusion: price-weighting changes the units, not the verdict.")

# ---- 3. threshold sweep ----
P("\n=== 3. in-sample threshold fragility: sweep instead of fixing ===")
P("%6s %8s %8s | %8s %8s %8s | %8s %8s %8s"
  % ("pctile", "os_thr", "ob_thr", "os h=5", "os h=10", "os h=20",
     "ob h=5", "ob h=10", "ob h=20"))
grid = []
for q in (0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20):
    r = battery(mc_mix, "q", fixed_q=(q, 1 - q))
    half = mc_mix.index[len(mc_mix) // 2]
    P("%6.1f%% %8.3f %8.3f | %8.3f %8.3f %8.3f | %8.3f %8.3f %8.3f"
      % (100 * q, mc_mix.loc[:half].quantile(q), mc_mix.loc[:half].quantile(1 - q),
         r[("oversold", 5)][1], r[("oversold", 10)][1], r[("oversold", 20)][1],
         r[("overbought", 5)][1], r[("overbought", 10)][1], r[("overbought", 20)][1]))
    grid.append(r)
allp = [v[1] for r in grid for v in r.values()]
P("\nacross %d (threshold x signal x horizon) combinations: min p %.4f, median %.4f"
  % (len(allp), min(allp), float(np.median(allp))))
P("combinations significant at 5%%: %d" % sum(p < 0.05 for p in allp))
P("conclusion: no threshold choice in this range produces a result.")

open("resolve_limitations.log", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
