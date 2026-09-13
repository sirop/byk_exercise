# -*- coding: utf-8 -*-
"""McClellan 1992-2026 on a POINT-IN-TIME roster, not a fixed survivor basket.

mcclellan_long.py (section 6.6) had to use the 30 current constituents held fixed
backwards, because the pre-2016 roster was thought unobtainable. That was wrong on
the prices, not the roster: nine FORMER members have complete Yahoo history from
1992-01-02 -- AA, MO, GT, IP, HPQ, AIG, BAC, C and T (T being the SBC entity that
was renamed AT&T in 2005, so it correctly covers the 1999-2015 spell; the original
AT&T Corp, a member until 2004, is the one that is gone).

Ten membership events fall in 1992-01-01 .. 2016-09-12. All ten are verified against
contemporaneous reporting, four of them against S&P Global press releases. The DJIA
was otherwise unchanged from 1991-05-06 to 1997-03-17.

Ten names in those rosters have no usable history at any vendor: Westinghouse,
Texaco, Bethlehem Steel, Woolworth, Sears Roebuck, Union Carbide, AT&T Corp,
Eastman Kodak, pre-bankruptcy GM, and Kraft. Their tickers were either retired or
reassigned to unrelated modern companies (TX, Z, UK, S, SBC, WX all resolve to
different issuers today and must NOT be substituted). They are carried here as
placeholder symbols that match no price column, so coverage is measured rather
than silently assumed.

This is strictly better than the section 6.6 basket: the roster is correct, only
incomplete, and the incompleteness is concentrated in the 1990s.
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import yfinance as yf

# ---- roster at the end of the sample (2026), from section 1.2 ----
MEMBERS_AT_END = ["AAPL", "AMGN", "AMZN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX",
                  "DIS", "GOOGL", "GS", "HD", "HON", "IBM", "JNJ", "JPM", "KO",
                  "MCD", "MMM", "MRK", "MSFT", "NKE", "NVDA", "PG", "SHW", "TRV",
                  "UNH", "V", "WMT"]

# ---- (effective date, added, removed) -- "prior to the opening of trading" ----
CHANGES_POST2016 = [                       # section 1.2, already verified
    ("2018-06-26", "WBA", "GE"),
    ("2019-04-02", "DOW", "DD"),
    ("2020-08-31", "CRM", "XOM"), ("2020-08-31", "AMGN", "PFE"),
    ("2020-08-31", "HON", "RTX"),
    ("2024-02-26", "AMZN", "WBA"),
    ("2024-11-08", "NVDA", "INTC"), ("2024-11-08", "SHW", "DOW"),
    ("2026-06-29", "GOOGL", "VZ"),
]
CHANGES_PRE2016 = [                        # verified this revision
    ("1997-03-17", "C", "WX_OLD"),         # Travelers <- Westinghouse
    ("1997-03-17", "HPQ", "TX_OLD"),       # Hewlett-Packard <- Texaco
    ("1997-03-17", "JNJ", "BS_OLD"),       # Johnson & Johnson <- Bethlehem Steel
    ("1997-03-17", "WMT", "Z_OLD"),        # Wal-Mart <- Woolworth
    ("1999-11-01", "INTC", "CVX"),         # Intel <- Chevron
    ("1999-11-01", "MSFT", "S_OLD"),       # Microsoft <- Sears Roebuck
    ("1999-11-01", "HD", "GT"),            # Home Depot <- Goodyear
    ("1999-11-01", "T", "UK_OLD"),         # SBC Communications <- Union Carbide
    ("2004-04-08", "AIG", "T_CORP"),       # AIG <- AT&T Corp
    ("2004-04-08", "PFE", "EK_OLD"),       # Pfizer <- Eastman Kodak
    ("2004-04-08", "VZ", "IP"),            # Verizon <- International Paper
    ("2008-02-19", "CVX", "MO"),           # Chevron returns <- Altria
    ("2008-02-19", "BAC", "HON"),          # Bank of America <- Honeywell
    ("2008-09-22", "KFT_OLD", "AIG"),      # Kraft <- AIG
    ("2009-06-08", "TRV", "C"),            # Travelers <- Citigroup
    ("2009-06-08", "CSCO", "GM_OLD"),      # Cisco <- General Motors
    ("2012-09-24", "UNH", "KFT_OLD"),      # UnitedHealth <- Kraft
    ("2013-09-23", "GS", "BAC"),           # Goldman Sachs <- Bank of America
    ("2013-09-23", "NKE", "AA"),           # Nike <- Alcoa
    ("2013-09-23", "V", "HPQ"),            # Visa <- Hewlett-Packard
    ("2015-03-19", "AAPL", "T"),           # Apple <- AT&T (the SBC entity)
]
CHANGES = CHANGES_PRE2016 + CHANGES_POST2016
UNOBTAINABLE = {"WX_OLD", "TX_OLD", "BS_OLD", "Z_OLD", "S_OLD", "UK_OLD",
                "T_CORP", "EK_OLD", "GM_OLD", "KFT_OLD"}

HORIZONS = [5, 10, 20]
REGIMES = [("1992-2000 bull", "1992-01-01", "1999-12-31"),
           ("2000-2010 sideways/bear", "2000-01-01", "2009-12-31"),
           ("2010-2016 bull", "2010-01-01", "2016-09-11"),
           ("2016-2026 bull", "2016-09-12", "2026-09-11"),
           ("full history 1992-2026", "1992-01-01", "2026-09-11")]

out = []
P = out.append


def membership_mask(index, changes, members_at_end):
    """Point-in-time roster, walked backwards from the end of the sample.

    Rebuilt from scratch for every date rather than carried incrementally. The
    section 1.2 version guarded each event with "added in current" and mutated one
    shared set as it walked; that is idempotent only while no ticker leaves and
    later returns. Two of the events added in this revision are exactly that case
    -- Chevron (out 1999-11-01, back 2008-02-19) and Honeywell (out 2008-02-19,
    back 2020-08-31) -- and the guard silently dropped both, giving a 28-name
    roster in 1992. Applying every event with eff > date exactly once, in
    descending date order, is the true inverse of the forward walk.
    """
    changes = sorted(changes, key=lambda c: pd.Timestamp(c[0]), reverse=True)
    end = set(members_at_end)
    assert len(end) == 30, "end roster != 30"
    cols = sorted({*end, *(t for _, a, r in changes for t in (a, r))})
    effs = [(pd.Timestamp(e), a, r) for e, a, r in changes]
    rows = {}
    for date in index:
        current = set(end)
        for eff, added, removed in effs:
            if date < eff:
                current.discard(added)
                current.add(removed)
        rows[date] = frozenset(current)
    mask = pd.DataFrame(False, index=index, columns=cols)
    for date, mem in rows.items():
        mask.loc[date, list(mem)] = True
    counts = mask.sum(axis=1)
    assert (counts == 30).all(), "roster != 30: %s" % counts[counts != 30].head()
    return mask


TICKERS = sorted({*MEMBERS_AT_END, *(t for _, a, r in CHANGES for t in (a, r))}
                 - UNOBTAINABLE)
raw = yf.download(TICKERS + ["^DJI"], start="1992-01-01", end="2026-09-12",
                  group_by="ticker", auto_adjust=True, threads=True, progress=False)
dji = raw[("^DJI", "Close")].dropna()
closes = pd.DataFrame({t: raw[(t, "Close")] for t in TICKERS}).reindex(dji.index)

# WBA was taken private in 2025 and Yahoo no longer serves it; section 1.1a already
# retrieved and cross-validated the history from Tiingo, so reuse that cache.
_w = pd.read_json("wba_tiingo.json")
_w = pd.Series(_w["adjClose"].values,
               index=pd.to_datetime(_w["date"]).dt.tz_localize(None)).sort_index()
closes["WBA"] = _w.reindex(dji.index)
print("WBA spliced from Tiingo cache: %d of %d days in 2018-06-26..2024-02-26"
      % (closes.loc["2018-06-26":"2024-02-26", "WBA"].notna().sum(),
         len(closes.loc["2018-06-26":"2024-02-26"])))

mask = membership_mask(dji.index, CHANGES, MEMBERS_AT_END)
for t in UNOBTAINABLE:                      # never priced, by construction
    closes[t] = np.nan
closes = closes.reindex(columns=mask.columns)
eff = (mask & closes.notna())               # members we can actually price

P("trading days %d  %s .. %s" % (len(dji), dji.index[0].date(), dji.index[-1].date()))
P("roster is 30 on every day: %s" % bool((mask.sum(axis=1) == 30).all()))
P("priceable members per day: min %d  median %d  max %d"
  % (eff.sum(axis=1).min(), int(eff.sum(axis=1).median()), eff.sum(axis=1).max()))
P("member-days total %d, priceable %d, MISSING %d (%.2f%%)"
  % (int(mask.sum().sum()), int(eff.sum().sum()),
     int(mask.sum().sum() - eff.sum().sum()),
     100 * (1 - eff.sum().sum() / mask.sum().sum())))
P("\ncoverage by era (mean priceable members of 30):")
for lab, a, b in REGIMES:
    s = eff.loc[a:b].sum(axis=1)
    if len(s):
        P("  %-26s %.2f of 30   (min %d, days at 30: %.1f%%)"
          % (lab, s.mean(), s.min(), 100 * (s == 30).mean()))
P("\nnames never priceable: %s" % ", ".join(sorted(UNOBTAINABLE)))
P("former members recovered: %s"
  % ", ".join(t for t in ("AA", "MO", "GT", "IP", "HPQ", "AIG", "BAC", "C", "T")
              if t in closes.columns))


def mcc(px_eff_mask):
    dc = closes.diff().where(px_eff_mask)
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
    ix = dji.loc[a:b]
    if len(ix) < 400:
        continue
    m = mcc(eff).loc[a:b]
    if len(m) < 300:
        continue
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
            nmed, _, _ = non_overlapping_p(sub, h)
            rows.append({"regime": label, "signal": nm, "h": h,
                         "n_sig": int(sub.signal.sum()), "n_epi": int(epi.nunique()),
                         "effect_pct": 100 * (aa.mean() - bb.mean()),
                         "p_hac": hac.pvalues["signal"], "p_clu": clu.pvalues["signal"],
                         "p_nov_med": nmed,
                         "p_boot": block_bootstrap_p(sub.fwd, sub.signal.astype(bool), h)})

res = pd.DataFrame(rows)
res.to_csv("mcclellan_pit_results.csv", index=False)

full = mcc(eff)
P("\noscillator range, point-in-time roster: %.2f .. %.2f (std %.2f)"
  % (full.min(), full.max(), full.std()))
for label, _, _ in REGIMES:
    q = res[res.regime == label]
    if not len(q):
        continue
    P("\n=== %s ===" % label)
    P("%-12s %-3s %6s %6s %9s %8s %8s %9s %8s"
      % ("signal", "h", "n_sig", "n_epi", "effect%", "p_hac", "p_clu",
         "p_nov_med", "p_boot"))
    for _, r in q.iterrows():
        P("%-12s %-3d %6d %6d %+9.2f %8.4f %8.4f %9.3f %8.4f"
          % (r.signal, r.h, r.n_sig, r.n_epi, r.effect_pct, r.p_hac, r.p_clu,
             r.p_nov_med, r.p_boot))

P("\n=== verdict across all %d rows ===" % len(res))
P("min p_hac     %.4f  (%s)" % (res.p_hac.min(),
  res.loc[res.p_hac.idxmin(), ["regime", "signal", "h"]].to_dict()))
P("min p_clu     %.4f" % res.p_clu.min())
P("min p_nov_med %.4f" % res.p_nov_med.min())
P("min p_boot    %.4f" % res.p_boot.min())
P("rows p_hac < 0.05: %d of %d" % (int((res.p_hac < 0.05).sum()), len(res)))
P("rows clearing BOTH p_hac and p_nov_med < 0.05: %d"
  % int(((res.p_hac < 0.05) & (res.p_nov_med < 0.05)).sum()))
P("largest |effect| %.2f%%" % res.effect_pct.abs().max())

# ---- compare against the section 6.6 fixed survivor basket ----
SURV = ["AXP", "BA", "CAT", "CSCO", "CVX", "DD", "DIS", "GE", "HD", "HON",
        "IBM", "INTC", "JNJ", "JPM", "KO", "MCD", "MMM", "MRK", "MSFT", "NKE",
        "PFE", "PG", "RTX", "SHW", "TRV", "UNH", "VZ", "WMT", "XOM", "AAPL"]
sv = pd.DataFrame(False, index=mask.index, columns=mask.columns)
for t in SURV:
    if t in sv.columns:
        sv[t] = closes[t].notna()
P("\n=== point-in-time vs the section 6.6 fixed survivor basket ===")
P("member-days where the two rosters disagree: %d of %d (%.2f%%)"
  % (int((sv != eff).sum().sum()), int(eff.sum().sum()),
     100 * (sv != eff).sum().sum() / eff.sum().sum()))
b = mcc(sv)
j = full.index.intersection(b.index)
P("oscillator correlation (point-in-time vs fixed basket): %.6f"
  % full.loc[j].corr(b.loc[j]))
P("sign agreement: %.2f%%" % (100 * (np.sign(full.loc[j]) == np.sign(b.loc[j])).mean()))

open("mcclellan_pit.log", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
