import io, json, sys, warnings
warnings.filterwarnings("ignore")
import pandas as pd, numpy as np
from scipy import stats
import statsmodels.api as sm

out = []
P = out.append

src = open("dj30_pipeline.py", encoding="utf-8").read().split("HORIZONS = [5,10,20]")[0]
src = src.replace(
    'data = yf.download(UNIVERSE + ["^DJI"], period="10y", interval="1d",\n'
    '                   group_by="ticker", auto_adjust=True, threads=True, progress=False)',
    'data = pd.read_pickle("dj30_raw.pkl")')
src = src.replace('data.to_pickle("dj30_raw.pkl")', '')
buf, real = io.StringIO(), sys.stdout
sys.stdout = buf
g = {"json": json}
exec(compile(src, "prelude", "exec"), g)
sys.stdout = real
closes, mask, dj30 = g["closes"], g["mask"], g["dj30"]
MEMBERS_AT_END = g["MEMBERS_AT_END"]

member_days = int((mask & closes.notna()).sum().sum())
P("total member-days: %d  (30 x %d = %d)" % (member_days, len(dj30), 30 * len(dj30)))

# ---------- 1. the two McClellan variants ----------
dc = closes.diff().where(mask)
adv, dec = (dc > 0).sum(axis=1), (dc < 0).sum(axis=1)
issues, net = adv + dec, adv - dec
P("\n=== issues (names with a non-zero move) ===")
P(issues.value_counts().sort_index().to_string())
P("issues == 30 on %.2f%% of days; mean %.3f" % (100 * (issues == 30).mean(), issues.mean()))

mc = (net.ewm(span=19, adjust=False).mean() - net.ewm(span=39, adjust=False).mean()).iloc[100:]
rt = (net / issues.where(issues != 0) * 100)
mr = (rt.ewm(span=19, adjust=False).mean() - rt.ewm(span=39, adjust=False).mean()).iloc[100:]
P("\ncorr(classic, ratio) = %.6f" % mc.corr(mr))
P("std ratio = %.4f   vs 100/30 = %.4f   vs 100/mean(issues) = %.4f"
  % (mr.std() / mc.std(), 100 / 30, 100 / issues.mean()))
P("same sign on %.2f%% of days" % (100 * (np.sign(mc) == np.sign(mr)).mean()))

# ---------- 2. spin-off / corporate-action scan ----------
ret = closes.pct_change().where(mask)
big = (ret.abs() > 0.15).fillna(False)
rows = [{"date": d.date(), "ticker": c, "ret": ret.loc[d, c]}
        for c in ret.columns for d in ret.index[big[c]]]
h = pd.DataFrame(rows).sort_values("ret", key=abs, ascending=False)
P("\n=== member-days with |return| > 15%%: %d on %d distinct dates (of %d member-days) ==="
  % (len(h), int(big.any(axis=1).sum()), member_days))
P(h.head(12).to_string(index=False))
P("WBA among them: %d" % int((h.ticker == "WBA").sum()))

# ---------- 3. sensitivity: A correct / B retroactive / C RTX print removed ----------
fwd = {hh: dj30.shift(-hh) / dj30 - 1 for hh in (5, 10, 20)}


def mcclellan(m):
    d2 = closes.diff().where(m)
    n2 = (d2 > 0).sum(axis=1) - (d2 < 0).sum(axis=1)
    return (n2.ewm(span=19, adjust=False).mean()
            - n2.ewm(span=39, adjust=False).mean()).iloc[100:]


def battery(series):
    half = series.index[len(series) // 2]
    os_, ob = series.loc[:half].quantile(.05), series.loc[:half].quantile(.95)
    res = {}
    for nm, sig in (("zero-cross", (series > 0) & (series.shift() <= 0)),
                    ("oversold", series < os_), ("overbought", series > ob)):
        for hh in (5, 10, 20):
            d2 = pd.DataFrame({"y": fwd[hh], "s": sig.astype(int)}).dropna()
            d2 = d2.loc[series.index.intersection(d2.index)]
            if d2.s.sum() < 5:
                continue
            f = sm.OLS(d2.y, sm.add_constant(d2.s)).fit(
                cov_type="HAC", cov_kwds={"maxlags": hh})
            res[(nm, hh)] = (f.tvalues["s"], f.pvalues["s"])
    return res


A = battery(mc)
retro = pd.DataFrame(False, index=closes.index, columns=closes.columns)
for t_ in MEMBERS_AT_END:
    if t_ in retro.columns:
        retro[t_] = True
mB = mcclellan(retro)
B = battery(mB)
m_nortx = mask.copy()
m_nortx.loc["2020-04-06", "RTX"] = False
mC = mcclellan(m_nortx)
C = battery(mC)

P("\n=== sensitivity ===")
P("corr(A, B retroactive)   = %.4f" % mc.corr(mB))
P("corr(A, C no-RTX-print)  = %.6f" % mc.corr(mC))
P("min p   A %.4f   B %.4f   C %.4f"
  % (min(v[1] for v in A.values()), min(v[1] for v in B.values()),
     min(v[1] for v in C.values())))
P("max |p(A)-p(B)| = %.4f" % max(abs(A[k][1] - B[k][1]) for k in A if k in B))
P("max |p(A)-p(C)| = %.7f" % max(abs(A[k][1] - C[k][1]) for k in A if k in C))
P("argmin signal under A: %s" % str(min(A, key=lambda k: A[k][1])))
P("argmin signal under B: %s" % str(min(B, key=lambda k: B[k][1])))

# ---------- 4. headline summary across the v3 result table ----------
r3 = pd.read_csv("dj30_results.csv")
m3 = r3[r3.signal.str.startswith("McClellan") | r3.signal.str.startswith("COMBO")]
P("\n=== McClellan + COMBO rows (v3) ===")
P("rows: %d" % len(m3))
for col in ("p_hac", "p_clu", "p_nov_med", "p_boot"):
    P("  min %-10s = %.4f" % (col, m3[col].min()))
P("  max |t_hac|      = %.4f" % m3.t_hac.abs().max())
P("  min p_nov_min    = %.4f" % m3.p_nov_min.min())
zc = r3[(r3.signal == "McClellan-classic zero-cross up") & (r3.h == 20)].iloc[0]
P("\nzero-cross h=20: n_sig %d  n_epi %d  effect %.4f%%  p_hac %.4f  "
  "p_nov min %.4f med %.4f max %.4f  offsets %d"
  % (zc.n_sig, zc.n_epi, zc.effect_pct, zc.p_hac, zc.p_nov_min,
     zc.p_nov_med, zc.p_nov_max, zc.n_off))

# identical-variant check
cl = r3[r3.signal.str.startswith("McClellan-classic")].reset_index(drop=True)
ra = r3[r3.signal.str.startswith("McClellan-ratio")].reset_index(drop=True)
num = ["effect_pct", "t_hac", "p_hac"]
P("\nclassic vs ratio rows identical to 1e-9: %s"
  % bool(np.allclose(cl[num].values, ra[num].values, atol=1e-9)))
for i in range(len(cl)):
    same = np.allclose(cl.loc[i, num].values.astype(float),
                       ra.loc[i, num].values.astype(float), atol=1e-9)
    P("  %-46s h=%-3d identical=%s" % (cl.loc[i, "signal"], cl.loc[i, "h"], same))

# ---------- 5. v2 vs v3 ----------
try:
    r2 = pd.read_csv("results_v2_29name.csv")
except FileNotFoundError:
    r2 = None
if r2 is not None:
    k = ["signal", "h"]
    j = r2.merge(r3, on=k, suffixes=("_v2", "_v3"))
    P("\n=== v2 (29-name, WBA missing) vs v3 (30-name) ===")
    P("rows matched: %d of %d" % (len(j), len(r3)))
    j["dp"] = (j.p_hac_v3 - j.p_hac_v2).abs()
    P("max |delta p_hac| = %.4f on %s"
      % (j.dp.max(), j.loc[j.dp.idxmax(), "signal"]))
    cmo_rows = j[j.signal.str.startswith("CMO")]
    P("CMO rows max |delta p_hac| = %.2e (expected 0: CMO uses ^DJI only)"
      % cmo_rows.dp.max())
    mc_rows = j[~j.signal.str.startswith("CMO")]
    P("McClellan rows max |delta p_hac| = %.4f, median %.4f"
      % (mc_rows.dp.max(), mc_rows.dp.median()))
    P("\nper-row p_hac, McClellan only:")
    P(mc_rows[["signal", "h", "p_hac_v2", "p_hac_v3", "dp"]].to_string(index=False))

open("recompute.log", "w", encoding="utf-8").write("\n".join(out))
print("wrote recompute.log (%d lines)" % len(out))
