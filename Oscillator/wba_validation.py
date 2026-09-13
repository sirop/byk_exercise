import json, warnings
warnings.filterwarnings("ignore")
import pandas as pd, numpy as np

out = []
P = out.append

t = pd.DataFrame(json.load(open("wba_tiingo.json")))
t["date"] = pd.to_datetime(t["date"]).dt.tz_localize(None)
t = t.set_index("date").sort_index()

f = pd.DataFrame(json.load(open("wba_fmp.json")))
f["date"] = pd.to_datetime(f["date"])
f = f.set_index("date").sort_index()

P("Tiingo bars %d  FMP bars %d" % (len(t), len(f)))
idx = t.index.intersection(f.index)
P("common trading dates: %d" % len(idx))
P("dates in Tiingo only: %s" % list(t.index.difference(f.index))[:5])
P("dates in FMP only:    %s" % list(f.index.difference(t.index))[:5])

# raw close must agree exactly-ish: this is the cross-vendor identity check
raw_t, raw_f = t.loc[idx, "close"], f.loc[idx, "close"]
d = (raw_t - raw_f).abs()
P("\nraw close: max abs diff %.4f   mean abs diff %.5f   exact matches %d/%d"
  % (d.max(), d.mean(), int((d < 0.005).sum()), len(idx)))

# what breadth actually consumes is sign(diff) only
s_t = np.sign(t.loc[idx, "adjClose"].diff())
s_f = np.sign(raw_f.diff())
agree = (s_t == s_f)
P("\nsign(diff) agreement, Tiingo adjClose vs FMP raw close: %d/%d = %.4f%%"
  % (int(agree.sum()), len(agree) - 1, 100.0 * agree.sum() / (len(agree) - 1)))
dis = agree[~agree].index
P("disagreement dates (%d): %s" % (len(dis), [str(x.date()) for x in dis[:12]]))

# adjustment sanity: Tiingo adj vs raw differ only by a smooth cumulative factor
fac = (t["adjClose"] / t["close"])
P("\nTiingo adj/raw factor: %.6f -> %.6f, monotone non-decreasing: %s"
  % (fac.iloc[0], fac.iloc[-1], bool((fac.diff().dropna() >= -1e-9).all())))
jump = fac.pct_change().abs()
P("largest single-day jump in the adjustment factor: %.4f%% on %s"
  % (100 * jump.max(), jump.idxmax().date()))

# splice check: does WBA behave like its peers, i.e. no pathological dispersion
r = t["adjClose"].pct_change().dropna()
P("\nWBA daily return: std %.4f  min %.4f (%s)  max %.4f (%s)"
  % (r.std(), r.min(), r.idxmin().date(), r.max(), r.idxmax().date()))
P("days with |return| > 15%%: %d" % int((r.abs() > 0.15).sum()))
P("up-days share: %.4f  (a fair breadth contributor should sit near 0.5)"
  % float((r > 0).mean()))

open("validate_wba.log", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
