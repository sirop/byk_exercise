import warnings
warnings.filterwarnings("ignore")
import json, os, requests
import yfinance as yf, pandas as pd, numpy as np
from scipy import stats
import statsmodels.api as sm

UNIVERSE = ["AAPL","AMGN","AMZN","AXP","BA","CAT","CRM","CSCO","CVX","DD",
    "DIS","DOW","GE","GOOGL","GS","HD","HON","IBM","INTC",
    "JNJ","JPM","KO","MCD","MMM","MRK","MSFT","NKE","NVDA","PFE",
    "PG","RTX","SHW","TRV","UNH","V","VZ","WBA","WMT","XOM"]

# Tickers that are genuine DJIA members in the window but have NO retrievable
# price history. Each must be justified, because each one shrinks the effective
# breadth universe below 30 for the duration of its membership.
# Empty: the one former entry (WBA) is now sourced from Tiingo below, so the
# universe guard can stay strict. See section 1.1a of the write-up.
KNOWN_GAPS = {}

# NOTE: two rows present in v1 were NOT membership changes at all, only ticker
# renames of a continuously-listed company, and have been removed:
#   DD -> DWDP (2017-09) and DWDP -> DD (2019-06) are one listing; Yahoo serves
#     its whole history under DD, so DD is used for the entire pre-2019 stretch.
#   UTX -> RTX (2020-04) is one listing (United Technologies renamed on the
#     Raytheon merger); Yahoo serves its whole history under RTX.
# Treating a rename as an add/remove pair is what forced DWDP and UTX into the
# universe, and neither symbol has any data -- see KNOWN_GAPS.
DJIA_CHANGES = [
    ("2018-06-26","WBA","GE"),
    ("2019-04-02","DOW","DD"),     # Dow Inc replaces DowDuPont (the DD listing)
    ("2020-08-31","CRM","XOM"), ("2020-08-31","AMGN","PFE"),
    ("2020-08-31","HON","RTX"),    # RTX here is the former UTX listing
    ("2024-02-26","AMZN","WBA"),
    ("2024-11-08","NVDA","INTC"), ("2024-11-08","SHW","DOW"),
    ("2026-06-29","GOOGL","VZ"),
]
MEMBERS_AT_END = ["AAPL","AMGN","AMZN","AXP","BA","CAT","CRM","CSCO","CVX","DIS",
    "GOOGL","GS","HD","HON","IBM","JNJ","JPM","KO","MCD","MMM",
    "MRK","MSFT","NKE","NVDA","PG","SHW","TRV","UNH","V","WMT"]

_needed = set(MEMBERS_AT_END) | {t for _,a,r in DJIA_CHANGES for t in (a,r)}
assert _needed <= set(UNIVERSE), "UNIVERSE missing %s" % sorted(_needed-set(UNIVERSE))

data = yf.download(UNIVERSE + ["^DJI"], period="10y", interval="1d",
                   group_by="ticker", auto_adjust=True, threads=True, progress=False)
data.to_pickle("dj30_raw.pkl")
# WBA was a component 2018-06-26..2024-02-26 and was taken private in 2025;
# Yahoo serves nothing for it. Tiingo's adjClose is split- and dividend-adjusted,
# the same basis as auto_adjust=True, so the two sources are on one footing.
# Export TIINGO_TOKEN before running; without it the old 29-name gap reappears
# and the assertion further down will fail loudly rather than silently.
_tok = os.environ.get("TIINGO_TOKEN")
_cache = "wba_tiingo.json"
if os.path.exists(_cache) or _tok:
    if os.path.exists(_cache):
        _w = pd.DataFrame(json.load(open(_cache, encoding="utf-8")))
    else:
        _r = requests.get("https://api.tiingo.com/tiingo/daily/WBA/prices",
                          params={"startDate": "2016-09-01", "endDate": "2024-03-01",
                                  "format": "json", "token": _tok}, timeout=60)
        _r.raise_for_status()
        json.dump(_r.json(), open(_cache, "w", encoding="utf-8"))
        _w = pd.DataFrame(_r.json())
    _w["date"] = pd.to_datetime(_w["date"]).dt.tz_localize(None)
    _w = _w.set_index("date")["adjClose"].sort_index()
    print("TIINGO WBA: %d bars %s..%s" % (len(_w), _w.index[0].date(), _w.index[-1].date()))
    data[("WBA", "Close")] = _w.reindex(data.index)
    data = data.sort_index(axis=1)
else:
    print("WARNING: no wba_tiingo.json and no TIINGO_TOKEN -- WBA will be missing; "
          "the universe assertion below will fail rather than silently use 29 names")

lvl0 = set(data.columns.get_level_values(0))
got = {t: (int(data[t]["Close"].notna().sum()) if t in lvl0 else 0) for t in UNIVERSE+["^DJI"]}
print("EMPTY/MISSING:", {k:v for k,v in got.items() if not v})
print("PARTIAL (<500 obs):", {k:v for k,v in got.items() if 0 < v < 500})


def membership_mask(index, changes=DJIA_CHANGES, members_at_end=MEMBERS_AT_END, strict=True):
    changes = sorted(changes, key=lambda c: pd.Timestamp(c[0]), reverse=True)
    current = set(members_at_end)
    if strict and len(current) != 30:
        raise ValueError("end roster != 30")
    cols = sorted({*current, *(t for _,a,r in changes for t in (a,r))})
    rows = {}
    for date in reversed(index):
        for eff, added, removed in changes:
            if date < pd.Timestamp(eff) and added in current:
                current.discard(added); current.add(removed)
        rows[date] = frozenset(current)
    mask = pd.DataFrame(False, index=index, columns=cols)
    for date, mem in rows.items():
        mask.loc[date, list(mem)] = True
    counts = mask.sum(axis=1)
    if strict and not (counts == 30).all():
        raise ValueError("roster!=30:\n%s" % counts[counts != 30].head())
    return mask


def cmo(series, window=20):
    diff = series.diff(); g = diff.clip(lower=0); l = -diff.clip(upper=0)
    sg, sl = g.rolling(window).sum(), l.rolling(window).sum()
    d = sg + sl
    return 100*(sg-sl)/d.where(d != 0)


dj30 = data["^DJI"]["Close"].dropna()
cmo_series = cmo(dj30, 20)
print("DJI: %d days %s..%s level %.0f -> %.0f" % (len(dj30), dj30.index[0].date(),
      dj30.index[-1].date(), dj30.iloc[0], dj30.iloc[-1]))

closes = pd.DataFrame({t: data[t]["Close"] for t in UNIVERSE if t in lvl0})
closes = closes.reindex(dj30.index)
closes = closes.loc[:, closes.notna().any()]
mask = membership_mask(dj30.index)
missing = [c for c in mask.columns if c not in closes.columns and mask[c].any()]
unexpected = [c for c in missing if c not in KNOWN_GAPS]
if unexpected:
    raise ValueError("member tickers with no price data: %s" % unexpected)
for c in missing:
    print("KNOWN GAP %s: %s" % (c, KNOWN_GAPS[c]))
mask = mask.reindex(columns=closes.columns, fill_value=False)
eff = (mask & closes.notna()).sum(axis=1)
print("effective universe (member AND has price): min %d  median %d" % (eff.min(), int(eff.median())))
print("dates with effective < 30: %d" % int((eff < 30).sum()))
assert (eff == 30).all(), "breadth universe != 30 on %d days" % int((eff != 30).sum())
worst = eff[eff < 30]
if len(worst):
    print("  e.g.\n%s" % worst.head(8))
    thin = (mask & closes.isna()).sum().sort_values(ascending=False)
    print("  member-days lacking price, by ticker:\n%s" % thin[thin > 0])

daily_change = closes.diff().where(mask)
adv = (daily_change > 0).sum(axis=1); dec = (daily_change < 0).sum(axis=1)
issues = adv + dec; net = adv - dec
mcc_classic = net.ewm(span=19,adjust=False).mean() - net.ewm(span=39,adjust=False).mean()
ratio = (net/issues.where(issues != 0))*100
mcc_ratio = ratio.ewm(span=19,adjust=False).mean() - ratio.ewm(span=39,adjust=False).mean()
WARMUP = 100
mcc_classic = mcc_classic.iloc[WARMUP:]; mcc_ratio = mcc_ratio.iloc[WARMUP:]
for nm, s in (("mcc_classic", mcc_classic), ("mcc_ratio", mcc_ratio)):
    print("\n%s: mean %.4f std %.4f min %.2f max %.2f q05 %.3f q95 %.3f"
          % (nm, s.mean(), s.std(), s.min(), s.max(), s.quantile(.05), s.quantile(.95)))

HORIZONS = [5,10,20]
df = pd.DataFrame({"close":dj30,"cmo":cmo_series,"mcc_classic":mcc_classic,"mcc_ratio":mcc_ratio})
for h in HORIZONS:
    df["fwd_%d" % h] = df["close"].shift(-h)/df["close"] - 1

CALIB_END = df.index[len(df)//2]
calib = df.loc[:CALIB_END]
TH = {v: {"os": calib[v].quantile(.05), "ob": calib[v].quantile(.95)}
      for v in ("mcc_classic","mcc_ratio")}
print("\nCALIB_END %s  thresholds %s" % (CALIB_END.date(),
      {k:{a:round(b,3) for a,b in d.items()} for k,d in TH.items()}))

SIGNALS = {"CMO < -30": df["cmo"] < -30, "CMO > 30": df["cmo"] > 30}
for v, lab in (("mcc_classic","McClellan-classic"),("mcc_ratio","McClellan-ratio")):
    s = df[v]
    SIGNALS["%s zero-cross up" % lab] = (s > 0) & (s.shift() <= 0)
    SIGNALS["%s < %.2f (oversold)" % (lab, TH[v]["os"])] = s < TH[v]["os"]
    SIGNALS["%s > %.2f (overbought)" % (lab, TH[v]["ob"])] = s > TH[v]["ob"]
    SIGNALS["COMBO CMO<-30 & %s<%.2f" % (lab, TH[v]["os"])] = (df["cmo"] < -30) & (s < TH[v]["os"])


def non_overlapping_p(sub, h, col="signal"):
    out = []
    for off in range(h):
        s = sub.iloc[off::h]
        a = s.loc[s[col] == 1, "fwd_%d" % h]; b = s.loc[s[col] == 0, "fwd_%d" % h]
        if len(a) < 5 or len(b) < 5:
            continue
        t, p = stats.ttest_ind(a, b, equal_var=False)
        out.append({"offset":off,"n_sig":len(a),"t":t,"p":p,"effect":a.mean()-b.mean()})
    return pd.DataFrame(out)


def block_bootstrap_p(y, signal, block_len, n_boot=10000, seed=0):
    rng = np.random.default_rng(seed)
    y = np.asarray(y, float); s = np.asarray(signal, bool); n = len(y)
    observed = y[s].mean() - y[~s].mean()
    nb = int(np.ceil(n/block_len)); draws = np.empty(n_boot); off = np.arange(block_len)
    for b in range(n_boot):
        st = rng.integers(0, n, size=nb)
        idx = ((st[:,None]+off[None,:]).ravel() % n)[:n]
        ys, ss = y[idx], s[idx]
        draws[b] = (ys[ss].mean()-ys[~ss].mean()) if ss.any() and not ss.all() else np.nan
    draws = draws[~np.isnan(draws)]; null = draws - draws.mean()
    return observed, float((np.abs(null) >= abs(observed)).mean())


rows = []
for name, sigmask in SIGNALS.items():
    for h in HORIZONS:
        sub = df.dropna(subset=["fwd_%d" % h]).copy()
        sub = sub[sub[["cmo","mcc_classic","mcc_ratio"]].notna().all(axis=1)]
        sub["signal"] = sigmask.reindex(sub.index).fillna(False).astype(int)
        nsig = int(sub["signal"].sum())
        if nsig < 5 or nsig == len(sub):
            print("SKIP %s h=%d (n_sig=%d)" % (name, h, nsig)); continue
        a = sub.loc[sub.signal == 1, "fwd_%d" % h]; b = sub.loc[sub.signal == 0, "fwd_%d" % h]
        tn, pn = stats.ttest_ind(a, b, equal_var=False)
        y = sub["fwd_%d" % h]; X = sm.add_constant(sub["signal"])
        hac = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags":h})
        epi = (sub["signal"] != sub["signal"].shift()).cumsum()
        cl = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups":epi})
        nov = non_overlapping_p(sub, h)
        obs, pbb = block_bootstrap_p(y, sub["signal"].astype(bool), block_len=h)
        rows.append({"signal":name,"h":h,"n_sig":nsig,"n_obs":len(sub),
            "effect_pct":100*(a.mean()-b.mean()),
            "t_naive":tn,"p_naive":pn,
            "t_hac":hac.tvalues["signal"],"p_hac":hac.pvalues["signal"],
            "n_epi":int(epi.nunique()),
            "t_clu":cl.tvalues["signal"],"p_clu":cl.pvalues["signal"],
            "p_nov_min":nov["p"].min() if len(nov) else np.nan,
            "p_nov_med":nov["p"].median() if len(nov) else np.nan,
            "p_nov_max":nov["p"].max() if len(nov) else np.nan,
            "n_off":len(nov),"p_boot":pbb})

res = pd.DataFrame(rows)
res.to_csv("results.csv", index=False)
pd.set_option("display.width", 300)
pd.set_option("display.max_columns", 60)
pd.set_option("display.float_format", lambda v: "%.4g" % v)
print("\n================ RESULTS ================")
print(res.to_string(index=False))
