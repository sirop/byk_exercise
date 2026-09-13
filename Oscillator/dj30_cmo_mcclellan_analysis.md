# CMO / McClellan Oscillator on the DJ30 — Full Analysis

**Context:** ... whether the Chande Momentum Oscillator (CMO) and the McClellan Oscillator work on the Dow Jones 30.

**Headline finding, in four sentences.** On the 10-year DJ30 window the question
concerns, neither indicator clears a correct treatment of overlapping-window
autocorrelation. On 34 years the **CMO verdict reverses**: the same unfitted ±30
thresholds give a consistent +1.54% excess over 20 days, so the 10-year sample was
underpowered rather than empty. The **McClellan Oscillator stays null** everywhere it was
tested — three breadth constructions, two vendors, five regimes, 34 years. Neither result
is a trading claim, for reasons given below.

| | CMO | McClellan |
|---|---|---|
| 10-year verdict | No defensible signal: `CMO < −30` at 20 days is p = 0.070 HAC, **0.38** median across non-overlapping phase offsets | Null: every p-value ≥ 0.42, largest \|t\| 0.67, on a complete 30-name universe on all 2,514 days |
| 34-year verdict | **Revised to a real effect** (§6.4): +1.54% over 20 days, p = 0.001 HAC / 0.002 clustered / 0.001 bootstrap, positive in all five regimes and all seven five-year sub-periods, and *larger* with the GFC, COVID and dot-com crashes excluded | **Still null** (§6.6, §6.7): 45 rows across five regimes, 0 clear both HAC and the non-overlapping test, and the one candidate is subsumed by the CMO jointly (p 0.155 vs 0.0046) |
| What stops it being a trading claim | The most conservative test still misses 5% (non-overlapping median 0.105), and a joint regression shows roughly a third of the edge is shared with a plain "the market has fallen" filter | Structural, not just statistical: the oscillator's range is ±5, not the ±70 the standard thresholds assume (§2.2) |

**Prior art found nothing worth copying.** The eToro search came back empty — in the ~130
posts that could be scanned, zero CMO mentions and one passing McClellan value with no
rule attached. That is a bounded sample, not a platform census, so it shows no prior art
*was found*, not that none exists (§7.1). Of the four implementations found off-platform
(three TradingView scripts, MarketInOut), none withstands a code review (§7.2–7.3).

**How to read this.** §8 is the answer; §6.4 and §6.7 are the two results that changed
the verdict; §5 is the methodological correction everything else rests on. §1–§3 are the
data and construction, auditable but skippable. §4 is deliberately retained *invalid*
analysis, kept to show what the correction in §5 changes.

<details>
<summary><strong>Contents</strong></summary>

- [§0 Revision note — what changed, and what is still open](#0-revision-note--what-changed-and-what-is-still-open)
- [§1 Data](#1-data) — [1.1 Download](#11-download) · [1.1a Closing the `WBA` gap](#11a-closing-the-wba-gap-and-why-a-spliced-series-needs-validating) · [1.2 Point-in-time membership](#12-point-in-time-membership)
- [§2 Indicator calculation](#2-indicator-calculation) — [2.1 CMO](#21-chande-momentum-oscillator-cmo-window--20-on-the-dj30-index-itself) · [2.2 McClellan across constituents](#22-mcclellan-oscillator-across-the-constituents)
- [§3 Assembling the frame and the forward returns](#3-assembling-the-frame-and-the-forward-returns)
- [§4 Naive backtest — **methodologically invalid**, kept deliberately](#4-backtest-naive-test--methodologically-invalid-see-5)
- [§5 The critical correction: window overlap](#5-the-critical-correction-window-overlap) — HAC, episode clustering, non-overlapping sampling, block bootstrap
- [§6 Results](#6-results) — [6.1 CMO](#61-cmo--valid-conclusion-stands) · [6.2 McClellan](#62-mcclellan--recomputed-unambiguous-null) · [6.3 Did the fixes matter](#63-did-the-membership-and-adjustment-fixes-actually-matter) · **[6.4 Regime dependence and the CMO revision](#64-regime-dependence--and-a-revision-to-the-cmo-verdict)** · [6.5 Vendor, weighting, threshold robustness](#65-vendor-weighting-and-threshold-robustness) · [6.6 Pre-2016, bias-bounded](#66-extending-the-mcclellan-test-before-2016-without-the-missing-roster) · **[6.7 Pre-2016 roster rebuilt](#67-the-pre-2016-roster-rebuilt--no-purchase-required)** · [6.8 Context for hit-rate figures](#68-context-for-all-hit-rate-figures)
- [§7 Prior art](#7-prior-art--what-a-search-finds-and-whether-it-works-there)
- [**§8 Overall conclusion**](#8-overall-conclusion)
- [§9 Open points](#9-open-points)
- [Appendix: limitations register](#appendix-limitations-register)

</details>

**Status:** all numbers below are from an executed run (sample 2016-09-12 → 2026-09-11, 2,514 trading days, `^DJI` 18,325 → 52,573). The breadth universe is complete: 30 members with a
price on every one of the 2,514 days, 75,420 member-days, no gaps. Breadth has since
been replicated end-to-end from a **second independent vendor**, rebuilt under price
weighting, and swept across seven threshold percentiles (§6.5); the CMO has been
re-run on 34 years of history (§6.4). Nothing in the result tables is carried over from the superseded first pass.

---

## 0. Revision note — what changed, and what is still open

The first version of this analysis contained three data errors and one narrative error. All are corrected, and the corrected pipeline has now been **run**, so §6 reports measured values rather than pending ones. Two of the four defects are the *same error class* this document criticises in other people's scripts (§7.2), which is worth stating plainly rather than quietly fixing.

| # | Defect in v1 | Status |
|---|---|---|
| 1 | Ticker list contained `VZ`, not `GOOGL`, while the text asserted the list was current as of September 2026 | **Fixed** — replaced by a point-in-time membership table (§1.2) |
| 2 | Current membership applied retroactively across 10 years (`NVDA`/`AMZN`/`SHW` present in years they were not components; `INTC`/`WBA`/`DOW` absent from years they were) | **Fixed and re-run** (§1.2). Invalidated every McClellan number in v1; §6.2 now reports the corrected run |
| 3 | `auto_adjust=False`, so every ex-dividend and split print counted as a decline in the advance/decline tally | **Fixed and re-run** (§1.1) |
| 4 | §5 argued overlap reduces the effective sample ~20×, which predicts a t-deflation of √20 ≈ 4.5; the observed deflation was 1.66× | **Corrected narrative** (§5.2); the re-run reproduces the mild deflation (1.69×) |

Two further defects surfaced only when the corrected code was actually executed. Both were introduced by the v1 fix attempt itself, not by v1:

| # | Defect found while running the revision | Status |
|---|---|---|
| 5 | The membership table treated two **ticker renames** as constituent changes: `DD`→`DWDP` (2017) and `UTX`→`RTX` (2020). Both are one continuously-listed company, so this invented two phantom index events and forced two symbols into the universe that no data provider serves | **Fixed** (§1.2) — both rows removed; `DD` and `RTX` each carry their full history. The source history independently labels the first a "name change", confirming the diagnosis |
| 6 | `WBA` is a genuine 2018–2024 component but was taken private in 2025 and is absent from Yahoo, so the breadth universe was 29 names, not 30, on 1,425 of 2,514 days | **Fixed and re-run** (§1.1a). Retrieved from Tiingo and cross-validated against Financial Modeling Prep; the universe is now 30 on all 2,514 days and the §2.2 guard is a hard assertion again |

All nine surviving membership rows have since been **verified against S&P Dow Jones
Indices announcements**, including completeness at both ends of the sample (§1.2).
The membership table is no longer an open item.

**Consequence for the conclusions.** The CMO analysis runs on `^DJI` directly and is untouched by any of these; it reproduces v1's numbers almost exactly (§6.1). The McClellan analysis was fully exposed to defects 2–3 and is now recomputed; it returns an unambiguous null (§6.2). v1's claim that "McClellan shows no significance in any variant" turns out to have been *correct but unsupported by its own data* — the right answer from a mis-specified universe. §6.3 now quantifies that: under v1's mis-specification individual p-values shift by up to 0.54, even though both specifications land on "null". That distinction is the point of this revision note.

---

## 1. Data

### 1.1 Download

DJ30 index (`^DJI`) plus all constituents, 10 years of daily prices via `yfinance`.

```python
import yfinance as yf
import pandas as pd
import numpy as np

# Union of every ticker that was a DJIA component at any point in the window,
# so that the point-in-time mask in §1.2 can select from it.
UNIVERSE = [
    "AAPL", "AMGN", "AMZN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX", "DD",
    "DIS", "DOW", "GE", "GOOGL", "GS", "HD", "HON", "IBM", "INTC",
    "JNJ", "JPM", "KO", "MCD", "MMM", "MRK", "MSFT", "NKE", "NVDA", "PFE",
    "PG", "RTX", "SHW", "TRV", "UNH", "V", "VZ", "WBA", "WMT", "XOM",
]

# Tickers that are genuine DJIA members inside the window but have NO retrievable
# price history. Every entry must be justified, because every entry shrinks the
# effective breadth universe below 30 for the duration of its membership.
# This dict is now EMPTY -- see §1.1a for how the one former entry was closed.
# It is kept because it is the right place for the next such name, and because an
# empty dict makes the §2.2 guard a hard assertion rather than a warning.
KNOWN_GAPS = {}

# Yahoo does not serve WBA (delisted 2025). It is spliced in from Tiingo; see
# §1.1a. Everything else comes from yfinance with auto_adjust=True.
# UNIVERSE must be a superset of every ticker the membership table touches,
# or a name masked as a member silently vanishes from the breadth count.
_needed = set(MEMBERS_AT_END) | {t for _, a, r in DJIA_CHANGES for t in (a, r)}
assert _needed <= set(UNIVERSE), f"UNIVERSE is missing {sorted(_needed - set(UNIVERSE))}"

# auto_adjust=True is REQUIRED. With unadjusted closes, every ex-dividend date
# and every split prints as a price drop and is counted as a decline in §2.2.
# Dow ex-div dates cluster within the same few weeks each quarter, so the bias
# is correlated and periodic, not white noise.
data = yf.download(UNIVERSE + ["^DJI"], period="10y", interval="1d",
                   group_by="ticker", auto_adjust=True, threads=True)
data.to_pickle("dj30_raw.pkl")
```

(The assertion references `DJIA_CHANGES` and `MEMBERS_AT_END` from §1.2; in a script, define those first. It exists because this exact gap occurred while writing this revision: `DD` was a component until September 2017, appears in the change table, and was absent from the download list — which would have produced a silent 29-name universe for the first year of the sample. The `strict` guard in §1.2 cannot catch it, because it validates the mask before the mask is intersected with the columns actually downloaded.)

Delisted or renamed tickers (`DWDP`, `UTX`, `GE` under its old identity) may not resolve cleanly through `yfinance`. Where a ticker fails to download, the membership mask in §1.2 must shrink the universe for those dates rather than silently treating the name as unchanged — see the `strict` guard below.

### 1.1a Closing the `WBA` gap, and why a spliced series needs validating

`WBA` was a component from 2018-06-26 to 2024-02-26 and was taken private in 2025.
Yahoo serves nothing for it, which is what made the breadth universe 29 names on
1,425 of 2,514 days (§0, defect 6). It is now retrieved from Tiingo:

```python
import requests

# Tiingo's adjClose is split- AND dividend-adjusted, the same basis as
# yfinance auto_adjust=True. Mixing an adjusted series with an unadjusted one
# would be the same class of error as defect 3.
r = requests.get("https://api.tiingo.com/tiingo/daily/WBA/prices",
                 params={"startDate": "2016-09-01", "endDate": "2024-03-01",
                         "format": "json", "token": TIINGO_TOKEN}, timeout=60)
wba = pd.DataFrame(r.json())
wba["date"] = pd.to_datetime(wba["date"]).dt.tz_localize(None)
wba = wba.set_index("date")["adjClose"].sort_index()   # 1,886 daily bars
data[("WBA", "Close")] = wba.reindex(data.index)
```

**A single ticker from a second vendor is exactly the kind of change that can
quietly inject a discontinuity**, which would be indistinguishable from the breadth
signal itself. So it was validated against an independent third source (Financial
Modeling Prep) before being used:

| Check | Result | Why it matters |
|---|---|---|
| Bar count and trading calendar vs FMP | 1,886 vs 1,886, set difference empty in both directions | A shifted or gap-ridden calendar would mis-align every A/D tally |
| Raw close vs FMP raw close | exact on 1,883 of 1,886 days; max discrepancy $0.03 | Confirms the two vendors describe the same security |
| `sign(diff)` vs FMP | agrees on 99.68% of days; all 6 disagreements are ex-dividend dates | `sign(diff)` is the *only* thing breadth consumes (§2.2) |
| Adjustment factor `adjClose / close` | 0.7028 → 0.9360, monotone non-decreasing, largest single-day step 2.38% | A non-monotone factor would signal a botched split or an unhandled spin-off |
| Daily-return distribution | std 1.97%, range −12.8% … +12.6%, **no** day beyond ±15% | `WBA` contributes nothing to the §6.3 artefact scan |
| Up-day share | 0.4912 | A breadth contributor biased away from 0.5 would tilt the A/D line |

The 6 sign disagreements are the expected and *correct* behaviour: on an ex-dividend
date the raw close can fall while the adjusted series rises. Using raw closes for one
name and adjusted closes for the other 29 would have re-introduced defect 3 on 6 days.

With this in place the breadth universe is 30 names on all 2,514 days — 75,420
member-days, no gaps — and the §2.2 guard can be a hard assertion again. The effect
on the results is real but not directional: see §6.2 (the conclusion is unchanged and
in fact slightly *less* close to significance) and the v2/v3 comparison below.

**What changed by adding the 30th name.** The CMO rows are bit-identical, as they
must be — the CMO is computed on `^DJI` itself and never touches the constituents.
Every McClellan row moved, by a median of 0.079 and a maximum of 0.164 in p (HAC).
The minimum p across all McClellan rows rose from 0.4667 to 0.4263 on the clustered
test and the largest |t| fell from 0.73 to 0.67. A missing name was therefore worth
about as much p-value movement as the membership mis-specification in §6.3 — another
reason the guard should never have been downgraded to a warning for longer than it
took to fix the gap.

### 1.2 Point-in-time membership

A fixed list of today's components applied to historical data is survivorship bias. The breadth series in §2.2 is a count across the index universe, so wrong membership corrupts the series directly rather than merely adding noise.

**This table has been verified row by row against S&P Dow Jones Indices' official index-change announcements**, including completeness at both ends of the sample; the June 2026 entry, which v1 carried unchecked, is confirmed against the S&P release of 2026-06-23. See *Verification of the membership table* below for the evidence. It should still be re-verified before any extension of the sample window, because this is the table where errors have actually occurred (§0, defect 5).

```python
# (effective_date, ticker_added, ticker_removed)
# VERIFIED against S&P DJI press releases and the S&P-sourced change history --
# every row, plus completeness at both ends of the sample. See the table below.
# Dates are S&P's effective dates, which take effect "prior to the opening of
# trading" on the stated day, so the added name IS a member on that date. The
# mask's `date < eff` comparison implements exactly that convention.
#
# A ticker RENAME IS NOT A MEMBERSHIP CHANGE. Two rows in the first draft of this
# revision were renames of a continuously-listed company, and encoding them as
# add/remove pairs both invented phantom index events and forced symbols into
# UNIVERSE that no provider serves:
#   DD -> DWDP (2017-09) and DWDP -> DD (2019-06) are one listing. Yahoo serves
#     its entire history under DD, so DD covers the whole pre-2019 stretch.
#   UTX -> RTX (2020-04) is one listing (United Technologies renamed on the
#     Raytheon merger). Yahoo serves its entire history under RTX.
# Both rows are therefore gone, and the symbols DWDP and UTX do not appear at all.
DJIA_CHANGES = [
    ("2018-06-26", "WBA",   "GE"),
    ("2019-04-02", "DOW",   "DD"),     # Dow Inc replaces DowDuPont (the DD listing)
    ("2020-08-31", "CRM",   "XOM"),
    ("2020-08-31", "AMGN",  "PFE"),
    ("2020-08-31", "HON",   "RTX"),    # RTX here is the former UTX listing
    ("2024-02-26", "AMZN",  "WBA"),
    ("2024-11-08", "NVDA",  "INTC"),
    ("2024-11-08", "SHW",   "DOW"),
    ("2026-06-29", "GOOGL", "VZ"),     # verified: S&P release 2026-06-23
]

# Membership as of the END of the sample, from which we walk backwards.
MEMBERS_AT_END = [
    "AAPL", "AMGN", "AMZN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX", "DIS",
    "GOOGL", "GS", "HD", "HON", "IBM", "JNJ", "JPM", "KO", "MCD", "MMM",
    "MRK", "MSFT", "NKE", "NVDA", "PG", "SHW", "TRV", "UNH", "V", "WMT",
]


def membership_mask(index, changes=DJIA_CHANGES, members_at_end=MEMBERS_AT_END,
                    strict=True):
    """Boolean DataFrame: True where `ticker` was a DJIA component on that date.

    Walks backwards from the known end-state, undoing each change as it is
    crossed, so the roster is correct for every date in `index`.
    """
    changes = sorted(changes, key=lambda c: pd.Timestamp(c[0]), reverse=True)
    current = set(members_at_end)
    if strict and len(current) != 30:
        raise ValueError(f"end-state roster has {len(current)} names, expected 30")

    cols = sorted({*current, *(t for _, a, r in changes for t in (a, r))})
    mask = pd.DataFrame(False, index=index, columns=cols)

    for date in reversed(index):                      # newest -> oldest
        for eff, added, removed in changes:
            eff = pd.Timestamp(eff)
            if date < eff and added in current:       # undo: this change
                current.discard(added)                # has not happened yet
                current.add(removed)
        mask.loc[date, list(current)] = True

    counts = mask.sum(axis=1)
    if strict and not (counts == 30).all():
        bad = counts[counts != 30]
        raise ValueError(f"roster size != 30 on {len(bad)} dates, e.g.\n{bad.head()}")
    return mask
```

#### Verification of the membership table

Every row was checked against S&P Dow Jones Indices' own announcements and the
S&P-sourced change history. All nine rows confirmed; no date corrections were
needed.

| Effective date | Added | Removed | Confirmed | Note |
|---|---|---|---|---|
| 2018-06-26 | WBA | GE | ✅ | Ended GE's membership, continuous since November 1907 |
| 2019-04-02 | DOW | DD | ✅ | Dow Inc is a spin-off of DowDuPont; the DowDuPont listing (served as `DD`) leaves the index |
| 2020-08-31 | CRM | XOM | ✅ | One of three simultaneous swaps |
| 2020-08-31 | AMGN | PFE | ✅ | |
| 2020-08-31 | HON | RTX | ✅ | RTX here is the former UTX listing, in the index since before the sample |
| 2024-02-26 | AMZN | WBA | ✅ | |
| 2024-11-08 | NVDA | INTC | ✅ | |
| 2024-11-08 | SHW | DOW | ✅ | |
| 2026-06-29 | GOOGL | VZ | ✅ | S&P release dated 2026-06-23; effective prior to the open on Monday 2026-06-29 |

**Completeness at both ends.** The preceding index change was 2015-03-19
(`AAPL` replaced `T`), before the sample begins on 2016-09-12, so the roster is
correct from day one. S&P's June 2026 release states the Alphabet change was the
first since November 2024, which closes the only long gap in the table. There are
therefore no missing events inside the window.

**The two removed rows were confirmed as renames, not index events.** The source
history labels the 2017-09-01 DuPont → DowDuPont entry explicitly as a *name
change*, and the 2020-04-06 United Technologies → Raytheon Technologies entry as a
merger of the same listing. Neither is a constituent substitution, which is why
encoding them as add/remove pairs (defect 5) produced two phantom events and two
undownloadable symbols.

**One forward-looking caveat.** The same June 2026 release notes that Honeywell is
spinning off Honeywell Aerospace and that the parent remains in the index under the
new name Honeywell Technologies. That is another rename-plus-spinoff of a current
member — exactly the pattern that caused defect 5 — so any extension of this sample
past the spin-off date must treat `HON` as one continuous listing and must re-check
for an unadjusted spin-off discontinuity.

The `strict` guard is the point of this function. v1's failure mode was a roster that was quietly wrong; an assertion that the universe is exactly 30 names on every single date turns that class of error into a crash instead of a silent result.

Result: 2513 trading days.

---

## 2. Indicator calculation

### 2.1 Chande Momentum Oscillator (CMO), window = 20, on the DJ30 index itself

```python
def cmo(series, window=20):
    diff = series.diff()
    gains = diff.clip(lower=0)
    losses = -diff.clip(upper=0)
    sum_gain = gains.rolling(window).sum()
    sum_loss = losses.rolling(window).sum()
    denom = sum_gain + sum_loss
    # Guard: a perfectly flat window gives denom == 0. Rare on an index,
    # not impossible, and it silently produces inf/NaN without this.
    return 100 * (sum_gain - sum_loss) / denom.where(denom != 0)


dj30 = data["^DJI"]["Close"].dropna()
cmo_series = cmo(dj30, 20)
```

### 2.2 McClellan Oscillator across the constituents

Two variants are computed. v1 tested only the first — the cruder of the two — and then drew a conclusion about the indicator as such. The ratio-adjusted variant is the construction this document itself praises in §7.2, so the null has to be demonstrated on it as well.

```python
closes = pd.DataFrame({t: data[t]["Close"] for t in UNIVERSE
                       if t in data.columns.get_level_values(0)})
closes = closes.reindex(dj30.index)

mask = membership_mask(dj30.index)

# Second guard, after intersecting with what actually downloaded. The §1.2
# check validates the roster in the abstract; this one catches a name that is
# a member but has no price data, which would shrink the universe silently.
missing = [c for c in mask.columns if c not in closes.columns and mask[c].any()]
unexpected = [c for c in missing if c not in KNOWN_GAPS]
if unexpected:
    raise ValueError(f"member tickers with no price data: {unexpected}")
for c in missing:
    print(f"KNOWN GAP {c}: {KNOWN_GAPS[c]}")
mask = mask.reindex(columns=closes.columns, fill_value=False)

# Report AND assert the actual breadth universe per day. While KNOWN_GAPS held
# an entry this had to be a printed diagnostic, because a bare `== 30` assertion
# would then have been a lie. With the WBA gap closed (§1.1a) the strict form is
# honest again, and it is the guard that would catch the next missing name.
effective = (mask & closes.notna()).sum(axis=1)
print(f"effective universe: min {effective.min()}, "
      f"days below 30: {(effective < 30).sum()} of {len(effective)}")
assert (effective == 30).all(), \
    f"breadth universe != 30 on {(effective != 30).sum()} days"
# Run output: min 30, days below 30: 0 of 2514 -> 75,420 member-days.

# No ffill. Forward-filling a stale price makes diff == 0, which counts as
# neither an advance nor a decline -- it silently shrinks the effective
# universe on exactly the days when data is least reliable.
daily_change = closes.diff().where(mask)

advances = (daily_change > 0).sum(axis=1)
declines = (daily_change < 0).sum(axis=1)
issues = advances + declines          # unchanged issues excluded, per convention
net_advances = advances - declines

# Variant A (classic): EMA of raw net advances.
# span=19 -> alpha = 2/20 = 0.10; span=39 -> alpha = 2/40 = 0.05, matching
# McClellan's original smoothing constants.
mcc_classic = (net_advances.ewm(span=19, adjust=False).mean()
               - net_advances.ewm(span=39, adjust=False).mean())

# Variant B (ratio-adjusted, StockCharts): normalises by participation, so the
# scale does not drift when the effective universe changes size.
# MEASURED RESULT: on this universe the two variants are the same indicator.
# `issues` is exactly 30 on 88.9% of days and has mean 29.87, so dividing by it
# is almost a constant rescaling -- corr(classic, ratio) = 0.99992, std ratio
# 3.3431 vs 100/30 = 3.3333, and the sign agrees on 99.92% of days. Variant B is
# therefore NOT an independent robustness check here; see the note below.
# NOTE on `issues` < 30 now that the universe is complete: it no longer means a
# missing price. It means a FLAT close (diff == 0), which is neither an advance
# nor a decline. That is a market fact about the day, not a data defect.
ratio = (net_advances / issues.where(issues != 0)) * 100
mcc_ratio = (ratio.ewm(span=19, adjust=False).mean()
             - ratio.ewm(span=39, adjust=False).mean())

# Discard EMA warm-up. A span=39 EMA needs ~100 observations to converge, and
# adjust=False seeds on the first value. Note the first net_advances entry is a
# spurious 0, not NaN: (NaN > 0).sum() is 0 on BOTH sides, so the first row
# looks like a genuine flat-breadth day. v1 calibrated its percentile
# thresholds on a series that included this unconverged stretch.
WARMUP = 100
mcc_classic = mcc_classic.iloc[WARMUP:]
mcc_ratio = mcc_ratio.iloc[WARMUP:]
```

### ⚠️ Calibration error we made ourselves first

The standard thresholds for "extreme" McClellan values (±70) come from the NYSE context (~2000+ issues). Scaled to 30 issues:

```python
mcc_classic.describe()
# mean   -0.005   std   1.390   min  -5.65   max   5.07
# 5th percentile: -2.45   95th percentile: +2.19

mcc_ratio.describe()
# mean   -0.012   std   4.647   min  -18.86  max  16.91
# 5th percentile: -8.20   95th percentile: +7.35
```

The range is about ±5, not ±70 — a factor of ~14. Using the NYSE ±70 convention on
this universe yields a signal that never fires once in ten years.

**The two variants are one indicator here.** The ratio-adjusted construction is
supposed to be the robust alternative, but on a 30-name universe the denominator
barely moves (`issues` is exactly 30 on 88.9% of days, mean 29.87), so it reduces
to a rescaling of the classic variant: correlation **0.99992**, standard-deviation
ratio 3.3431 against the predicted 100/30 = 3.3333, identical sign on 99.92% of
days. Running both is therefore *not* two tests — which is why §6.2 reports them
together, and why 6 of the 9 row-pairs there come out bit-identical. (The three
`overbought` pairs differ very slightly, which is instructive: a rescaling that is
only *near*-constant does not preserve a 95th-percentile cut point exactly, so the
one signal defined by an upper percentile reclassifies a day or two. The lower
percentile and the zero crossing are both invariant.) The ratio adjustment only earns its keep on
a universe whose participation actually varies (NYSE, where issue counts drift with
listings and halts).

**Independently confirmed:** a TradingView user (`aftabmk`) documented exactly the same problem when adapting the McClellan Oscillator for the DAX (GER30, also 30 issues) — though that script is itself faulty (author's own note: the A/D logic does not correctly detect declining values).
→ https://www.tradingview.com/script/UYAgnbAH-McClellan-Oscillator-for-DAX-GER30-aftabmk-modified/

**A caveat the v1 document missed:** the DJIA is price-weighted, while breadth counts every name equally. This mismatch is an independent reason for low information content on this index, separate from the "30 issues is too few" argument in §2.2 and §8, point 4.

---

## 3. Assembling the frame and the forward returns

v1's snippets did not compose into a runnable script (`df` was used but never built; `close` and `dj30` were used interchangeably). Explicitly:

```python
HORIZONS = [5, 10, 20]

df = pd.DataFrame({"close": dj30, "cmo": cmo_series,
                   "mcc_classic": mcc_classic, "mcc_ratio": mcc_ratio})

for h in HORIZONS:
    df[f"fwd_{h}"] = df["close"].shift(-h) / df["close"] - 1
```

### Threshold selection

v1 derived the McClellan extremes from the 5th/95th percentiles of the **full sample**, which includes the forward-return period — mild look-ahead. The combined signal additionally used `mcclellan < -1.8`, a value that is neither a percentile nor explained anywhere; if it was tuned, that row is uninterpretable. Both are fixed by calibrating on a held-out first half:

```python
CALIB_END = df.index[len(df) // 2]          # thresholds from the first half only
calib = df.loc[:CALIB_END]

thresholds = {
    "mcc_oversold":   calib["mcc_classic"].quantile(0.05),
    "mcc_overbought": calib["mcc_classic"].quantile(0.95),
}
# The combined signal reuses mcc_oversold. No free hand-picked parameter.
```

Realised split: `CALIB_END` = 2021-09-09 (1,158 calibration days), giving
`mcc_classic` thresholds of **−2.40 / +2.03** and `mcc_ratio` thresholds of
**−8.01 / +6.82**. These are close to the full-sample percentiles
(−2.45 / +2.19 classic, −8.20 / +7.35 ratio), so v1's look-ahead was mild in
magnitude — but that is luck, not a defence of the method. §6.5 goes further and
sweeps the percentile from 2% to 20%, removing the choice rather than justifying it.

(Earlier revisions quoted −2.36 / +2.00 and −8.16 / +6.89 here. Those were the
29-name figures, stale since the `WBA` gap was closed in §1.1a.)

CMO's ±30 is Chande's own published convention, not fitted here, so it needs no such treatment.

---

## 4. Backtest: naive test — **METHODOLOGICALLY INVALID, see §5**

```python
from scipy import stats
t, p = stats.ttest_ind(sig_ret, non_sig_ret, equal_var=False)
```

First (wrong) finding: CMO < -30 at 20 days significant with p = 0.0022, surviving even a Bonferroni correction (α = 0.05 / 18 tests). CMO > 30 at 20 days: p < 0.0001.

Bonferroni is reported here deliberately: the false positive *survived* multiplicity correction, which isolates window overlap — not multiple testing — as the actual culprit.

---

## 5. The critical correction: window overlap

**The problem:** every trading day has its own 20-day forward window. Day *n* and day *n+1* share 19 of 20 days, so the "independent" observations in the t-test are heavily autocorrelated.

### 5.1 First pass: Newey-West (HAC) standard errors

```python
import statsmodels.api as sm

sub = df.dropna(subset=[f"fwd_{h}"]).copy()
sub["signal"] = signal_mask.reindex(sub.index).fillna(False).astype(int)

y = sub[f"fwd_{h}"]
X = sm.add_constant(sub["signal"])
hac = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": h})
```

`maxlags = h` is adequate in principle: overlapping *h*-period returns have an MA(*h*−1) structure.

### 5.2 Why HAC alone is not enough

v1 stopped here and presented HAC as *the* fix. It is a partial one, for two reasons — and the numbers show it.

**The arithmetic does not support the narrative.** v1 argued that 180 signal days collapse to roughly 180/20 ≈ 9 independent 20-day periods. A 20-fold reduction in effective sample predicts a t-statistic deflation of √20 ≈ 4.47. Measured on the corrected run (CMO < −30, 20 days): t goes from **3.07 naive to 1.81 HAC**, a deflation of **1.69×**, implying an effective-sample reduction of only **2.9×**. The correction that actually lands is four times milder than the stated mechanism requires. Something is under-correcting.

**What is under-correcting: signal episodes.** The CMO stays below −30 for consecutive runs. The measured count is **103 episode boundaries** for 177 signal days at h = 20 — so the signal arrives in long blocks, and an episode spanning more than 20 days carries autocorrelation that `maxlags=20` cannot absorb by construction. HAC is being asked to hold asymptotically at an effective sample size where Newey-West standard errors are known to be biased downward. The reported p = 0.070 is therefore itself optimistic, which is exactly what §5.4 confirms.

### 5.3 Episode-clustered standard errors

```python
# Cluster on maximal runs of constant signal value, so an entire
# signal episode is one unit of information.
episode = (sub["signal"] != sub["signal"].shift()).cumsum()
clustered = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": episode})
```

Cluster-robust inference needs many clusters to be reliable. Here there are enough to be meaningful (65–469 depending on signal and horizon), but the clusters are wildly unbalanced in length, so this remains a cross-check rather than an arbiter. In the event it barely moves the CMO result (p 0.070 → 0.078), confirming that episode clustering alone is not what was inflating the naive test.

### 5.4 The decisive checks: non-overlapping sampling and a block bootstrap

These are **required**, not optional robustness extras. v1 listed non-overlapping resampling as a future "open point"; given §5.2 it is the test that actually settles the question.

```python
def non_overlapping_p(sub, h, signal_col="signal"):
    """Sample every h-th day so forward windows never overlap.

    Reports the result for all h phase offsets rather than one, since picking
    a single offset is a free choice that could be exploited.
    """
    out = []
    for offset in range(h):
        s = sub.iloc[offset::h]
        a = s.loc[s[signal_col] == 1, f"fwd_{h}"]
        b = s.loc[s[signal_col] == 0, f"fwd_{h}"]
        if len(a) < 5 or len(b) < 5:
            continue
        t, p = stats.ttest_ind(a, b, equal_var=False)
        out.append({"offset": offset, "n_sig": len(a), "t": t, "p": p,
                    "effect": a.mean() - b.mean()})
    return pd.DataFrame(out)


def block_bootstrap_p(y, signal, block_len, n_boot=10_000, seed=0):
    """Circular block bootstrap on the difference in means.

    Resamples (return, signal) pairs in contiguous blocks, preserving both the
    serial dependence of overlapping windows and the clustering of signal
    episodes -- the two things HAC handles poorly here.
    """
    rng = np.random.default_rng(seed)
    y = np.asarray(y, dtype=float)
    s = np.asarray(signal, dtype=bool)
    n = len(y)
    observed = y[s].mean() - y[~s].mean()

    n_blocks = int(np.ceil(n / block_len))
    draws = np.empty(n_boot)
    offsets = np.arange(block_len)
    for b in range(n_boot):
        starts = rng.integers(0, n, size=n_blocks)
        idx = ((starts[:, None] + offsets[None, :]).ravel() % n)[:n]
        ys, ss = y[idx], s[idx]
        draws[b] = (ys[ss].mean() - ys[~ss].mean()
                    if ss.any() and not ss.all() else np.nan)

    draws = draws[~np.isnan(draws)]
    null = draws - draws.mean()          # centre to get the null distribution
    return observed, float((np.abs(null) >= abs(observed)).mean())
```

#### Why all offsets must be reported, with the measured case that proves it

Sampling every *h*-th day removes the overlap entirely, but it also discards
(*h*−1)/*h* of the data, and *which* days survive depends on the arbitrary phase
offset. The spread across offsets is large enough to manufacture any conclusion
wanted:

| Signal | h | offsets | p: min | p: **median** | p: max | p (HAC) |
|---|---|---|---|---|---|---|
| CMO < −30 | 20 | 19 | 0.031 | **0.380** | 0.932 | 0.070 |
| CMO > 30 | 20 | 20 | 0.037 | **0.317** | 0.961 | 0.083 |
| McClellan-classic zero-cross up | 20 | 20 | **0.017** | **0.654** | 0.970 | 0.945 |

The third row is the cautionary one. A single phase offset of that signal returns
p = 0.017 — significant at the conventional 5% level, and a result that would be
publishable as stated — on a signal whose HAC p-value is 0.945, whose median across
offsets is 0.654, and whose effect size is −0.02%. Nothing is there. Reporting one
offset is not a robustness check; it is a 20-way multiple-comparison search
presented as a single test, and it is precisely how a spurious result reaches
publication. The same pattern appears across the table: **8 of the 24
McClellan rows** (four distinct signals, each appearing in both variants) have a
minimum across offsets below 0.05, ranging from 0.017 to 0.047 — while the lowest
corrected p-value any of them achieves on any test is 0.43. Phase-offset mining would
yield a "significant" McClellan result for a third of the rows in §6.2.

The median across offsets is used throughout §6 for this reason. It is not a
p-value in the strict sense — it has no exact null distribution — but it is a
consistent summary that cannot be gamed by the choice of offset, which is the
property that matters here.

---

## 6. Results

**Which of these subsections carry the verdict.** §6 accreted across revisions, so it is
not ordered by importance. For a reader who wants the findings only:

| Read | Subsection | Why |
|---|---|---|
| **Yes** | **6.4** Regime dependence | Where the CMO verdict is revised on 34 years. The single most consequential result |
| **Yes** | **6.7** Pre-2016 roster rebuilt | The final McClellan test, on the correct point-in-time roster |
| Yes | 6.1, 6.2 | The 10-year verdicts for each indicator |
| Optional | 6.3, 6.5, 6.8 | Robustness and framing: did the fixes matter, vendor/weighting/threshold sweeps, the bull-market caveat on raw hit rates |
| **Superseded** | 6.6 Pre-2016, bias-bounded | Kept as an audit trail, not as a result. It assumed the pre-2016 roster was unobtainable; §6.7 shows it was not. Its conclusion survived the correction unchanged, which is itself the point — but a reader short of time should skip to 6.7 |

### 6.1 CMO — valid, conclusion stands

These rows run on `^DJI` alone and are unaffected by the data defects in §0. `n` is the **number of signal days**, not the regression sample size (the OLS runs on the full sample with a dummy).

| Signal | Horizon | n (signal days) | episodes | Effect (Δ mean) | t (naive) | p (naive) | t (HAC) | p (HAC) | p (clustered) | p (non-overlap, median) | p (bootstrap) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CMO < -30 | 5d | 178 | 105 | +0.17% | 0.52 | 0.6055 | 0.29 | 0.769 | 0.706 | 0.87 | 0.756 |
| CMO < -30 | 10d | 177 | 103 | +0.14% | 0.31 | 0.7556 | 0.16 | 0.869 | 0.808 | 0.76 | 0.869 |
| **CMO < -30** | **20d** | **177** | **103** | **+1.53%** | **3.07** | **0.0025** | **1.81** | **0.070** | **0.078** | **0.38** | **0.081** |
| CMO > 30 | 5d | 604 | 223 | -0.16% | -1.74 | 0.0820 | -1.05 | 0.293 | 0.257 | 0.37 | 0.284 |
| CMO > 30 | 10d | 604 | 223 | -0.38% | -3.09 | 0.0021 | -1.36 | 0.173 | 0.148 | 0.43 | 0.170 |
| CMO > 30 | 20d | 603 | 221 | -0.83% | -4.83 | 1.5e-06 | -1.74 | 0.083 | 0.077 | 0.32 | 0.077 |

`episodes` counts maximal runs of constant signal value — the number of genuinely
distinct occasions the signal fired, which is the honest denominator for "how much
evidence is there". `p (non-overlap, median)` is the median across all *h* phase
offsets; the minimum across offsets is reported in §5.4 and must not be read as the
result.

**What survives.** Nothing. The naive test finds three of six rows significant, one of them overwhelmingly (CMO > 30 at 20 days, p = 1.5 × 10⁻⁶). Every one of them dies under correction. The strongest remnant is CMO < −30 at 20 days: p = 0.070 HAC, 0.078 clustered, 0.081 bootstrap, and a median of 0.38 across the 19 non-overlapping phase offsets. The non-overlapping median is the most informative of these — it is the only figure computed on observations that genuinely do not share data — and at 0.38 it indicates no effect at all.

Note that the v1 numbers for these rows were essentially correct (n = 180 vs 177, effect +1.53% vs +1.53%, t = 1.84 vs 1.81). The CMO conclusion never depended on the data defects, as §0 predicted, and the stricter tests confirm it more firmly than HAC alone could.

### 6.2 McClellan — recomputed, unambiguous null

Computed on point-in-time membership (§1.2) and split/dividend-adjusted prices
(§1.1), with held-out thresholds (§3), for both constructions from §2.2. The v1
numbers for these rows are withdrawn; they were computed on a retroactive roster
and unadjusted prices and should not be cited even where they happen to agree.

| Signal | Horizon | n (signal days) | episodes | Effect (Δ mean) | t (naive) | p (naive) | t (HAC) | p (HAC) | p (clustered) | p (non-overlap, median) | p (bootstrap) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| McClellan-classic zero-cross up | 5d | 234 | 469 | -0.07% | -0.44 | 0.6613 | -0.45 | 0.651 | 0.694 | 0.70 | 0.648 |
| McClellan-classic zero-cross up | 10d | 234 | 469 | +0.13% | 0.60 | 0.5482 | 0.60 | 0.546 | 0.629 | 0.69 | 0.546 |
| McClellan-classic zero-cross up | 20d | 232 | 465 | -0.02% | -0.07 | 0.9475 | -0.07 | 0.945 | 0.959 | 0.65 | 0.942 |
| McClellan-classic < −2.40 (oversold) | 5d | 129 | 117 | -0.14% | -0.40 | 0.6881 | -0.26 | 0.794 | 0.772 | 0.85 | 0.782 |
| McClellan-classic < −2.40 (oversold) | 10d | 129 | 117 | -0.68% | -1.27 | 0.2075 | -0.60 | 0.548 | 0.516 | 0.56 | 0.556 |
| McClellan-classic < −2.40 (oversold) | 20d | 129 | 117 | +0.19% | 0.29 | 0.7738 | 0.14 | 0.887 | 0.894 | 0.47 | 0.898 |
| McClellan-classic > 2.03 (overbought) | 5d | 150 | 123 | +0.01% | 0.04 | 0.9661 | 0.03 | 0.975 | 0.974 | 0.81 | 0.975 |
| McClellan-classic > 2.03 (overbought) | 10d | 150 | 123 | +0.08% | 0.32 | 0.7512 | 0.18 | 0.857 | 0.849 | 0.49 | 0.860 |
| McClellan-classic > 2.03 (overbought) | 20d | 150 | 123 | -0.06% | -0.17 | 0.8626 | -0.08 | 0.936 | 0.929 | 0.54 | 0.934 |
| COMBO CMO<−30 & McClellan-classic<−2.40 | 5d | 59 | 65 | -0.68% | -1.04 | 0.3023 | -0.66 | 0.512 | 0.483 | 0.83 | 0.494 |
| COMBO CMO<−30 & McClellan-classic<−2.40 | 10d | 59 | 65 | -1.21% | -1.24 | 0.2205 | -0.67 | 0.505 | 0.426 | 0.63 | 0.525 |
| COMBO CMO<−30 & McClellan-classic<−2.40 | 20d | 59 | 65 | +0.65% | 0.64 | 0.5275 | 0.37 | 0.710 | 0.679 | 0.54 | 0.715 |
| McClellan-ratio zero-cross up | 5d | 234 | 469 | -0.07% | -0.44 | 0.6613 | -0.45 | 0.651 | 0.694 | 0.70 | 0.648 |
| McClellan-ratio zero-cross up | 10d | 234 | 469 | +0.13% | 0.60 | 0.5482 | 0.60 | 0.546 | 0.629 | 0.69 | 0.546 |
| McClellan-ratio zero-cross up | 20d | 232 | 465 | -0.02% | -0.07 | 0.9475 | -0.07 | 0.945 | 0.959 | 0.65 | 0.942 |
| McClellan-ratio < −8.01 (oversold) | 5d | 129 | 117 | -0.14% | -0.40 | 0.6881 | -0.26 | 0.794 | 0.772 | 0.85 | 0.782 |
| McClellan-ratio < −8.01 (oversold) | 10d | 129 | 117 | -0.68% | -1.27 | 0.2075 | -0.60 | 0.548 | 0.516 | 0.56 | 0.556 |
| McClellan-ratio < −8.01 (oversold) | 20d | 129 | 117 | +0.19% | 0.29 | 0.7738 | 0.14 | 0.887 | 0.894 | 0.47 | 0.898 |
| McClellan-ratio > 6.82 (overbought) | 5d | 148 | 117 | +0.06% | 0.37 | 0.7085 | 0.28 | 0.778 | 0.772 | 0.71 | 0.776 |
| McClellan-ratio > 6.82 (overbought) | 10d | 148 | 117 | +0.16% | 0.70 | 0.4871 | 0.40 | 0.688 | 0.686 | 0.55 | 0.685 |
| McClellan-ratio > 6.82 (overbought) | 20d | 148 | 117 | +0.00% | 0.01 | 0.9947 | 0.00 | 0.998 | 0.997 | 0.50 | 0.997 |
| COMBO CMO<−30 & McClellan-ratio<−8.01 | 5d | 59 | 65 | -0.68% | -1.04 | 0.3023 | -0.66 | 0.512 | 0.483 | 0.83 | 0.494 |
| COMBO CMO<−30 & McClellan-ratio<−8.01 | 10d | 59 | 65 | -1.21% | -1.24 | 0.2205 | -0.67 | 0.505 | 0.426 | 0.63 | 0.525 |
| COMBO CMO<−30 & McClellan-ratio<−8.01 | 20d | 59 | 65 | +0.65% | 0.64 | 0.5275 | 0.37 | 0.710 | 0.679 | 0.54 | 0.715 |

**Reading this table.** Every p-value is ≥ 0.42 on every corrected test, and the
largest |t (HAC)| anywhere is 0.67. There is no horizon, no construction, no
threshold and no combination here that shows anything. Unlike the CMO rows, these
are not marginal results that correction killed — they are null in the *naive* test
too, so there is no overlap artefact to argue about.

Three specifics worth noting:

- **Most rows are bit-identical between the two variants.** That is not a copy
  error; it follows from the variant equivalence measured in §2.2 — the ratio
  adjustment is a near-constant rescaling here, so it cannot move a sign crossing
  or a lower-percentile cut. Only the three `overbought` pairs differ, and only in
  the third decimal.
- **The zero-cross signal has 469 episodes for 234 signal days**, i.e. it fires in
  isolated one- and two-day bursts rather than blocks. It is the one signal in this
  document whose overlap problem is mild, and it still shows nothing.
- **The COMBO row no longer has a free parameter.** v1's unexplained `McClellan <
  −1.8` is replaced by the held-out oversold threshold. Its apparent v1 edge
  (+1.78%, t = 1.50) drops to +0.65%, t = 0.37 — the combination was an artefact of
  the hand-picked cutoff, which is exactly the failure mode §3 was written to close.

### 6.3 Did the membership and adjustment fixes actually matter?

The fixes are justified on principle, but it is worth measuring what they bought,
since §0 claims v1 got "the right answer from a mis-specified universe." Re-running
the McClellan pipeline under deliberately wrong specifications:

| Specification | corr. with correct series | min p across 9 signals | Conclusion |
|---|---|---|---|
| **A. Point-in-time membership, complete 30-name universe (the result above)** | — | **0.546** | null |
| B. Today's 30 names applied retroactively (v1's defect 2) | 0.9763 | 0.401 | null |
| C. A, minus the `RTX` merger-window prints | 0.999995 | 0.546 | null |

**Specification B is the informative row.** The mis-specified series is 98%
correlated with the correct one, so the indicator itself barely changes — but
individual p-values move by up to **0.54**, and the signal with the strongest
apparent effect is a different one under each specification (zero-cross at h = 10
under A, at h = 20 under B). Both specifications reach "null", so v1's stated
conclusion survives; v1's *evidence for it* does not. A p-value that can move by
0.54 under a data fix was never measuring what it claimed to. This is the concrete
version of the §0 sentence, and the reason the numbers were withdrawn rather than
kept on the grounds that they agreed.

**Specification C disposes of a residual worry, and finds something else.**
`auto_adjust` corrects dividends and splits, and its spin-off handling is not
*guaranteed*, so a spin-off could in principle inject an artificial decline.
(An earlier revision stated flatly that `auto_adjust` does not handle spin-offs.
That is too strong: §6.5 finds Honeywell's Solstice Advanced Materials distribution
of 2025-10-30 absorbed cleanly, with two vendors agreeing to four decimals through
the event. The defensible statement is that spin-off handling must be verified per
event, not assumed in either direction.) Scanning all 75,420 member-days for moves beyond
±15% returns 50 on 29 distinct dates, and 49 are genuine market events — the March
2020 crash, plus single-name shocks (`INTC` −26% 2024-08-02, `IBM` −25% 2026-07-14,
`UNH` −22% 2025-04-17). The one corporate-action artefact is the `RTX` reconstitution
around the Raytheon merger: Carrier and Otis were distributed on 2020-04-03 (−7.8%)
and the merged basis appears on 2020-04-06 (+15.3%). Excluding `RTX` for that whole
window changes exactly **one** sign(diff) day in 75,420, and leaves the correlation
at 0.999995. Notably the DuPont spin-offs leave no mark at all, because breadth uses
only `sign(diff)` — any purely *multiplicative* back-adjustment is invisible to it,
and only *additive* discontinuities matter. That is a useful general bound: for a
breadth indicator, the whole back-adjustment question can only ever matter through
additive events.

**But removing that single day moves a p-value by 0.11, and the reason is not the
data.** The zero-cross and oversold rows do not budge at all (identical to four
decimals). Only the three `overbought` rows move, by up to 0.111 — because dropping
one observation shifts the in-sample 95th-percentile threshold from 2.0228 to
2.0179, a change of 0.24%, which reclassifies a single day. Hold the threshold fixed
at its specification-A value and the largest movement falls to 0.036. So the
sensitivity being measured here is not sensitivity to a corporate action at all: it
is the in-sample threshold amplifying one observation in 75,420 into a tenth of a
p-value. This is the same defect that §3 was written to close and that collapsed the
COMBO row in §6.2, showing up a third time from a different direction. It is an
argument for held-out thresholds that does not depend on any result being
significant.

---

### 6.4 Regime dependence — and a revision to the CMO verdict

The Appendix listed "single index, single 10-year bull regime (+187%)" as unresolved,
and §9 asked for a sideways/bear period. This is now done, and it changed the answer.

The CMO is computed on `^DJI` itself and needs no constituent roster, so unlike the
McClellan Oscillator it is not confined to the window for which point-in-time
membership was reconstructed. Yahoo serves `^DJI` from 1992-01-02: **8,735 trading
days**, 3.5× the main sample, including the decade §9 asked for. Chande's ±30
thresholds are used throughout, so — unlike the McClellan extremes — there is no
threshold selection here at all and nothing to hold out.

`CMO < −30`, horizon 20 days:

| Regime | days | `^DJI` | n (signal) | episodes | Effect | p (naive) | p (HAC) | p (clust.) | p (non-ov. med) | p (boot) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1992–2000 bull | 2,022 | +262% | 126 | 79 | +0.59% | 0.128 | 0.520 | 0.574 | 0.51 | 0.499 |
| **2000–2010 sideways/bear** | 2,515 | **−8%** | 300 | 141 | **+1.97%** | 0.000 | **0.036** | 0.050 | 0.26 | **0.038** |
| 2010–2016 bull | 1,684 | +71% | 131 | 71 | +2.15% | 0.000 | **0.000** | 0.000 | **0.05** | 0.000 |
| 2016–2026 bull (main sample) | 2,514 | +187% | 180 | 105 | +1.53% | 0.002 | 0.066 | 0.071 | 0.39 | 0.075 |
| **full history 1992–2026** | **8,735** | +1,557% | **741** | **399** | **+1.54%** | 0.000 | **0.001** | **0.002** | 0.105 | **0.001** |

The main-sample row differs from §6.1 in the third decimal (0.066 vs 0.070) because
this run slices a separately downloaded long `^DJI` series and recomputes the 20-day
CMO window inside the slice, so the first 19 days of the window differ. Nothing turns
on it.

**The effect is positive in every regime**, +0.59% to +2.15%, including the decade in
which the index *fell* 8%. On the full history it clears HAC, episode clustering and
the block bootstrap by a wide margin — p ≈ 0.001 on 741 signal days spread over 399
episodes, four times the independent units the main sample offered. The main sample
was **underpowered, not empty**: at n = 180 and a true effect near +1.5%, p = 0.066 is
what an underpowered test of a real effect looks like.

**It is not an outlier artefact.** This was checked first, because a large mean excess
return after oversold readings is exactly what a handful of crash rebounds would
manufacture:

| Check | Result |
|---|---|
| Mean vs median excess | +1.54% vs **+1.41%** — the median is nearly the mean |
| Mann-Whitney U (rank-based, outlier-free) | p < 0.0001 |
| Trimmed means, 5% / 10% / 20% | +1.46% / +1.45% / +1.41% — flat |
| Excluding the 2008–09 GFC | +1.60%, p = 0.0004 — **stronger** |
| Excluding COVID 2020 | +1.56%, p = 0.0008 |
| Excluding GFC + COVID + dot-com 2000–02 | +1.51%, p = 0.0001 |
| Sign in each of the seven 5-year sub-periods | positive in **7 of 7** (+0.93% … +2.54%) |
| 20-day win rate | 72.6% on signal days vs 62.8% otherwise |

Removing every crisis makes the effect *larger*, the opposite of an outlier-driven
result.

**Two qualifications, which is why this is not reported as a trading edge.**

First, **the most conservative test still does not clear 5%.** The median across the
20 non-overlapping phase offsets is 0.105. It fell from 0.39 to 0.105 as the data grew
3.5×, and 7 of the 20 offsets are individually below 0.05 — the distribution is moving
the right way, but by the standard §5.4 sets for itself this is not yet significant.
§5.4's own warning applies here too: the minimum offset is 0.003 and must not be
quoted as the result.

Second, **most of what the CMO detects is plain mean reversion.** Against a
frequency-matched naive benchmark — "trailing 20-day return below −4.84%", firing on
the same 8.52% of days — the CMO is better but not different in kind:

| Signal | Effect | t (HAC) | p (HAC) | win rate |
|---|---|---|---|---|
| `CMO < −30` | +1.54% | 3.29 | 0.0010 | 72.6% |
| trailing 20-day return < −4.84% | +1.48% | 2.16 | 0.031 | 68.3% |

The two overlap on 63.6% of signal days. In a joint HAC regression the CMO coefficient
survives (+1.02%, p = 0.032) while the naive filter's does not (+0.86%, p = 0.273), so
the CMO subsumes the benchmark rather than the reverse — but the CMO's standalone
+1.54% falls to +1.02% once the benchmark is controlled for, meaning roughly a third of
its raw edge is simply "the market has fallen recently". On days where only the CMO
fires the excess is +1.11%; where only the naive filter fires, +0.95%.

**Revised verdict on the CMO.** There is a real, modest, regime-robust
oversold-reversal effect at the 20-day horizon, which the CMO captures somewhat more
cleanly than a raw trailing return. It is **not** detectable on the 10-year DJ30 sample
alone, it does not clear the most conservative test even on 34 years, and it is a
property of index mean reversion rather than of the Dow 30 specifically. That is a
materially different conclusion from "no signal", and it supersedes the CMO verdict in
earlier revisions of this document.

**The McClellan Oscillator cannot be extended the same way**, because breadth needs a
point-in-time roster and the reconstruction in §1.2 only covers 2016–2026. It can,
however, be extended under a *measured* roster bias, which §6.6 does — and the null
survives 34 years there too.

Reproduced by `regime_test.py` (writes `regime_results.csv`, `regime_results.log`).

### 6.5 Vendor, weighting and threshold robustness

Three further Appendix limitations were resolvable by re-running rather than by
argument. All three leave the McClellan null intact.

**Single-vendor replication** (was: "breadth prices come from two vendors"). The whole
breadth series was rebuilt from Tiingo for all 30 names, removing the Yahoo-plus-Tiingo
splice of §1.1a and substituting a vendor with independent corporate-action handling:

| | Result |
|---|---|
| Correlation of the two oscillator series | **0.999949** |
| Identical sign | 99.96% of days |
| Member-days where `sign(diff)` disagrees | **27 of 75,420** (0.036%) |
| Largest p-value difference across the 9 signals | **0.019** |
| Minimum p | 0.546 (mixed) vs 0.543 (Tiingo-only) |

This re-tests the spin-off question far more sharply than the ±15% scan in §6.3,
because the two vendors adjust corporate actions independently. **22 of the 27
disagreements are `DD`** — the DowDuPont listing, i.e. precisely the merger-and-spin-off
name — so the vendors *do* disagree about how to back-adjust it, and the measured
consequence of that disagreement is a p-value shift of at most 0.019.

Conversely, the spin-off that the ±15% scan would have missed is handled correctly by
both. Honeywell distributed **Solstice Advanced Materials (`SOLS`) on 2025-10-30**, one
share per four `HON` shares held — roughly a 4–5% value separation, too small to trip a
±15% filter, and squarely inside the sample with `HON` a member. Checked directly:
Tiingo and Yahoo closes agree to four decimals on both sides of the event (ratio
1.0000), the daily moves 2025-10-28 … 2025-11-03 are −0.31%, −0.71%, −0.27%, +0.61%,
−1.77% — the largest being 1.2σ against a 1.51% full-sample standard deviation — and
`sign(diff)` agrees between vendors on all four dates. No additive discontinuity, no
breadth artefact. The methodological point stands regardless of the clean outcome:
**a magnitude scan is not a substitute for an event list**, because a 1-for-4 spin-off
is smaller than ordinary daily noise.

**Price-weighted breadth** (was: "equal-weighted breadth vs price-weighted index",
previously *noted, not corrected*). The DJIA is price-weighted; standard McClellan
counts each name once. Weighting each advance and decline by the constituent's price
gives a genuinely different series — correlation 0.920 with the equal-weighted version,
same sign on only 92.5% of days — so unlike the ratio-adjusted variant of §2.2 this
*is* an independent construction, and it partly answers the complaint that no
independent check of the breadth result was possible. It is also null: minimum
p = 0.249 across the nine signals, maximum |t| = 1.15.

**Threshold sweep** (was: "in-sample percentile thresholds amplify single
observations"). Rather than defend one percentile cut, sweep it. Held-out thresholds at
the 2nd, 3rd, 5th, 7.5th, 10th, 15th and 20th percentiles, crossed with
oversold/overbought and three horizons, give 63 combinations:

| percentile | oversold thr. | overbought thr. | min p across the 6 cells |
|---|---|---|---|
| 2% | −3.04 | +2.51 | 0.272 |
| 3% | −2.73 | +2.34 | 0.504 |
| 5% (used in §6.2) | −2.43 | +2.02 | 0.582 |
| 7.5% | −2.05 | +1.84 | 0.399 |
| 10% | −1.75 | +1.68 | **0.151** |
| 15% | −1.37 | +1.39 | 0.204 |
| 20% | −1.06 | +1.18 | 0.276 |

Across all 63 combinations: **minimum p = 0.151**, median 0.705, **0 significant at
5%**. No threshold in this range rescues the McClellan Oscillator — a stronger
statement than §6.3's finding that a single observation can move one p-value by 0.11.

Reproduced by `resolve_limitations.py` (writes `resolve_limitations.log`).

---

### 6.6 Extending the McClellan test before 2016, without the missing roster

§6.4 reported that the McClellan Oscillator could not follow the CMO onto long
history, because breadth needs point-in-time membership and the reconstruction in
§1.2 stops at 2016-09-12. That was too pessimistic. The limitation is circumventable,
and circumventing it **strengthens** the McClellan null rather than disturbing it.

**What is actually missing.** Not the roster. The DJIA changed composition only about
ten times between 1992 and 2016, and those events are publicly documented — trivial
next to an S&P 500 reconstruction. What is missing is *prices for the names that died*.
Probing both vendors:

| Name | Status |
|---|---|
| `AIG`, `AXP`, `BAC`, `C`, `DD`, `GE` and other survivors | full 6,299 bars from 1992-01-02 |
| `AA` Alcoa | Tiingo serves only from 2016-10-18 — the Arconic split orphaned its copy of the pre-2016 history. **Yahoo, checked later, has `AA` back to 1962**, which is what §6.7 exploits |
| `ARNC` Arconic | empty, which is where old Alcoa history should be |
| `GM` | both vendors only from 2010-11-18, i.e. post-bankruptcy GM; the member that left in 2009 is gone |
| `BS` Bethlehem Steel, `EK` Kodak | Tiingo empty / 404 |
| `BS`, `WX`, `TX`, `Z`, `S`, `UK`, `EK`, `ARNC`, `KFT`, `SBC`, `HWP` | FMP returns **HTTP 402 "Premium"** |

So the dead names are a *paywall*, not a void: FMP holds them behind a paid tier. This
is a purchasing decision, not a data-availability fact — which is worth establishing
before deciding whether to make it.

**Do the missing names even matter?** Testable, because in 2016–2026 the true roster
*is* known, so the error a defective roster induces can be simulated. Two experiments
(`roster_bias.py`):

*Random dropout* — remove k of 30 names, recompute all nine signals, 200 draws each:

| k names missing | median \|Δp\| | 90th pct | max \|Δp\| | lowest p ever produced | cells significant at 5% |
|---|---|---|---|---|---|
| 1 | 0.064 | 0.192 | 0.430 | 0.269 | 0 |
| 2 | 0.075 | 0.231 | 0.622 | 0.127 | 0 |
| 3 | 0.091 | 0.253 | 0.614 | 0.101 | 0 |
| 4 | 0.094 | 0.259 | 0.747 | 0.034 | 1 |
| 6 | 0.118 | 0.298 | 0.738 | 0.053 | 0 |

*Survivorship bias* — use the end-of-sample roster held fixed backwards, which is the
construction you are forced into with no membership history at all: it mis-assigns
**30.3% of member-days** and moves individual p-values by up to **0.544**, yet the
minimum p across the nine signals is still **0.40** (true roster: 0.55).

The two results together are the key to the circumvention. A defective roster makes
individual p-values **untrustworthy** — displacements of 0.5 and more. But across
**9,000 dropout draws it produced exactly 1 significant cell**, against the ~450 a
5% rate would give on noise. Roster damage adds variance without manufacturing
significance. So a biased roster cannot support a point estimate of p, but it *can*
answer the binary question "does any signal appear?" — and if the answer is no, the
null extends without buying anything.

**Running it.** Thirty of the current constituents have continuous Yahoo history from
1992-01-02, giving a fixed survivor basket: **8,735 days, 262,050 member-days**, 30
names priced on every single day. Full §5.1–5.4 battery, held-out thresholds, five
regimes, 45 rows (`mcclellan_long.py`):

| Regime | oversold h=20 effect | p (HAC) | p (clust.) | p (non-ov. med) | p (boot) |
|---|---|---|---|---|---|
| 1992–2000 bull | +0.36% (h=5) | 0.082 | 0.085 | 0.178 | 0.076 |
| **2000–2010 sideways/bear** | **+2.00%** | **0.0034** | **0.0087** | 0.340 | **0.0027** |
| full history 1992–2026 | **+0.98%** | **0.0111** | **0.0246** | 0.197 | **0.0117** |

Across all 45 rows: 8 have p(HAC) < 0.05, the lowest being 0.0034. But the minimum
non-overlapping median anywhere in the 45 is **0.081**, and **0 of 45 rows clear both
HAC and the non-overlapping test**. By the standard §5.4 sets, nothing survives.

**And what does show up is not McClellan's.** The oversold-at-20-days row looks like
the §6.4 CMO effect, because both indicators are "the market has fallen" detectors.
Tested directly (`mcc_vs_cmo.py`) — the two fire on 7.0% and 8.6% of days, overlapping
on 224 days (φ = 0.280):

| | alone | | joint regression | |
|---|---|---|---|---|
| | coef | p | coef | p |
| McClellan oversold | +0.99% | 0.0100 | +0.56% | **0.156** |
| `CMO < −30` | +1.54% | 0.0010 | +1.40% | **0.0034** |

Entered together, McClellan loses significance and the CMO keeps it. Conditional on
neither firing, the 20-day forward return averages +0.58%; McClellan-only days beat
that by +0.44%, CMO-only days by +1.31%. **The breadth oscillator adds nothing over an
oscillator computed on the index itself** — which is the §2.2 structural argument
(30 issues carry too little breadth information) confirmed on 34 years instead of 10.

Two further confirmations from the long run. The oscillator's range over 34 years is
**−5.32 to +5.25** (std 1.38), so the §2.2 finding that the standard ±70 thresholds
are off by more than an order of magnitude is not an artefact of the 10-year window.
And the survivorship bias runs in the *helpful* direction here: a fixed survivor basket
drifts upward, so "even the winners declined" is a stricter condition than true
oversold breadth, biasing the test **toward** finding an effect. The eight significant
HAC rows are therefore an upper bound on what is really there, which makes the null
conclusion stronger, not weaker.

**Status of the limitation.** Downgraded from blocking to confirmatory. The McClellan
null now holds on 34 years and five regimes under a construction biased in favour of
finding something, and the one effect that appears is subsumed by the CMO.

This section's weakness is that it throws the roster away entirely. §6.7 replaces it
with the real one, and at no cost: the purchase this section contemplated turned out
to be unnecessary.

---

### 6.7 The pre-2016 roster, rebuilt — no purchase required

§6.6 assumed the pre-2016 constituents were unobtainable and worked around it with a
fixed survivor basket. That assumption was wrong, and wrong in a checkable way: it
conflated *retired* tickers with *delisted companies*. Nine **former** DJIA members
have complete Yahoo history from 1992-01-02:

| Ticker | Company | True membership spell |
|---|---|---|
| `AA` | Alcoa | 1959 → 2013-09-23 |
| `MO` | Philip Morris / Altria | 1985 → 2008-02-19 |
| `GT` | Goodyear | → 1999-11-01 |
| `IP` | International Paper | → 2004-04-08 |
| `HPQ` | Hewlett-Packard | 1997-03-17 → 2013-09-23 |
| `AIG` | AIG | 2004-04-08 → 2008-09-22 |
| `BAC` | Bank of America | 2008-02-19 → 2013-09-23 |
| `C` | Travelers Inc / Citigroup | 1997-03-17 → 2009-06-08 |
| `T` | SBC Communications, renamed AT&T in 2005 | 1999-11-01 → 2015-03-19 |

The `T` row is the subtle one. The original **AT&T Corp** was a member until
2004-04-08 and its listing is gone; the `T` that trades today is the *SBC* entity that
joined in 1999 and took the AT&T name in 2005, so `T` covers the 1999–2015 spell
correctly and must not be used for the earlier one. The mirror-image trap is worse:
`TX`, `Z`, `UK`, `S`, `SBC` and `WX` all resolve today to **unrelated modern issuers**
(Yahoo serves `WX` only from 2026-06-03, `S` from 2021, `UK` from 2019). Substituting
a reused ticker for a dead company would have silently injected a different company's
returns into 1990s breadth. Ten names remain genuinely unobtainable at every vendor
checked: Westinghouse, Texaco, Bethlehem Steel, Woolworth, Sears Roebuck, Union
Carbide, AT&T Corp, Eastman Kodak, pre-bankruptcy GM, and Kraft.

**The membership table.** Ten events fall in 1992-01-01 … 2016-09-12, and the index
was otherwise unchanged from 1991-05-06 to 1997-03-17. Each was verified against
contemporaneous reporting, four against S&P Global's own releases, to the same standard
§1.2 applied to the post-2016 rows:

| Effective | In | Out |
|---|---|---|
| 1997-03-17 | Travelers, Hewlett-Packard, Johnson & Johnson, Wal-Mart | Westinghouse, Texaco, Bethlehem Steel, Woolworth |
| 1999-11-01 | Intel, Microsoft, Home Depot, SBC | Chevron, Sears, Goodyear, Union Carbide |
| 2004-04-08 | AIG, Pfizer, Verizon | AT&T Corp, Eastman Kodak, International Paper |
| 2008-02-19 | **Chevron (returning)**, Bank of America | Altria, **Honeywell** |
| 2008-09-22 | Kraft | AIG |
| 2009-06-08 | Travelers, Cisco | Citigroup, General Motors |
| 2012-09-24 | UnitedHealth | Kraft |
| 2013-09-23 | Goldman Sachs, Nike, Visa | Alcoa, Bank of America, Hewlett-Packard |
| 2015-03-19 | Apple | AT&T (the SBC entity) |

**A defect this exposed in §1.2's own code.** Two of these rows are *re-entries* —
Chevron leaves in 1999 and returns in 2008, Honeywell leaves in 2008 and returns in
2020. The `membership_mask` function of §1.2 walks the roster backwards while mutating
one shared set, guarding each event with `added in current`. That is idempotent only
while no ticker leaves and later returns; with a re-entry the guard re-fires the later
event on the way down and drops the name. Fed the full table it produced a **28-name**
roster in 1992, caught by the `assert (counts == 30).all()` guard. The fix is to
rebuild the roster from scratch for each date, applying every event with `eff > date`
exactly once in descending order — the true inverse of the forward walk. **The
published §1.2 and §6 results are unaffected**, because the post-2016 table contains no
re-entry; the defect was latent until this extension. It is, however, the fourth
membership-table defect found by running the code rather than reading it.

**Coverage.** The roster is now *correct but incomplete*, rather than wrong:

| Era | priceable members (mean of 30) | min | days at full 30 |
|---|---|---|---|
| 1992–2000 | 22.44 | 21 | 0% |
| 2000–2010 | 28.08 | 27 | 0% |
| 2010–2016 | 29.59 | 29 | 59.2% |
| 2016–2026 | **30.00** | 30 | **100%** |
| full 1992–2026 | 27.62 | 21 | 40.2% |

Mis-assigned member-days fall from **30.3%** under §6.6's fixed basket to **7.94%**
here, and the two constructions disagree on 43.3% of member-days (oscillator
correlation 0.974, same sign on 92.4% of days). Two incidental validations: the
2016–2026 era reproduces 30 of 30 on every day, independently confirming §1.2's
roster; and 2000–2010 coverage of 28.08 sits inside the k ≤ 6 dropout envelope measured
in §6.6, so that era's bias is not merely bounded but *small*. Only the 1990s, at
22.44 of 30, are outside the measured envelope.

**Results — the same null, at a quarter of the bias.** 45 rows, same battery:

| Regime | oversold h=20 | p (HAC) | p (clust.) | p (non-ov. med) | p (boot) |
|---|---|---|---|---|---|
| 1992–2000 bull | +0.62% | 0.204 | 0.286 | 0.492 | 0.202 |
| **2000–2010 sideways/bear** | **+1.62%** | **0.0020** | **0.0138** | 0.359 | **0.0017** |
| 2010–2016 bull | +1.36% | 0.0361 | 0.0710 | 0.329 | 0.0383 |
| 2016–2026 bull | +0.35% | 0.773 | 0.788 | 0.526 | 0.775 |
| **full history** | **+0.99%** | **0.0046** | **0.0151** | 0.335 | **0.0060** |

9 of 45 rows clear HAC (§6.6: 8 of 45). The minimum non-overlapping median anywhere is
**0.061**, and **0 of 45 rows clear both tests** — the same verdict §6.6 reached, and
the same one §6.2 reached on 2016–2026 alone. The full-history oversold effect is
+0.99% against §6.6's +0.98%: quadrupling the roster accuracy moved it by one
hundredth of a percentage point.

**And it is still not McClellan's effect.** Re-running the §6.6 joint regression on the
point-in-time breadth (`mcc_vs_cmo_pit.py`) — McClellan fires on 7.65% of days, the CMO
on 8.60%, both on 250 (φ = 0.301):

| | alone | | joint | |
|---|---|---|---|---|
| | coef | p | coef | p |
| McClellan oversold | +0.97% | 0.0052 | +0.53% | **0.155** |
| `CMO < −30` | +1.54% | 0.0010 | +1.39% | **0.0046** |

Baseline +0.573%; McClellan-only days beat it by +0.619%, CMO-only days by +1.464%.
Restricted to the 2000–2010 bear window where McClellan's HAC p-value is lowest of all
45 rows, the joint regression still gives McClellan **p = 0.142** against the CMO's
0.057. The breadth oscillator is subsumed by an oscillator on the index itself in every
window tested, on the correct roster as on the biased one.

**What this does to the limitation.** It removes it. §6.6 framed the missing roster as
a purchase decision and bounded the cost of not purchasing; §6.7 shows the purchase was
never needed, because nine of the ten missing members were sitting in the free vendor
under their own retired tickers. What remains unobtainable is ten companies that no
longer exist in any form, concentrated in the 1990s, worth 7.94% of member-days — and
the §6.6 dropout experiment already established that roster damage of this size adds
variance without manufacturing significance. The register entry is closed on the
conclusion and left open only on the 1990s p-value precision.

The methodological lesson is the same one the Solstice spin-off taught in §6.5, in a
new costume: **a vendor returning no data for a ticker is not evidence that the
company's history is unavailable.** `AA` was "missing" because one vendor's copy had
been orphaned by a corporate action, and the nine recovered names were "dead" because I
had searched for the companies' final tickers instead of asking which listings still
carry their history. Checking cost one afternoon; the paid tier §6.6 was prepared to
recommend would have bought nothing that mattered.

*An aside on sourcing, since it was tried:* two Kaggle datasets cover this ground and
neither is usable. [Huge Stock Market
Dataset](https://www.kaggle.com/datasets/borismarjanovic/price-volume-data-for-all-us-stocks-etfs)
is a survivor-only snapshot as of 2017-11-10 — `bs`, `ek`, `hwp`, `kft`, `wx`, `uk` are
all absent and `gm` starts 2010-11-17, so it reproduces the same bias it would be
bought to fix. [Historical Components of the
DJIA](https://www.kaggle.com/datasets/darinhawley/historical-components-of-the-dow-jones-djia)
stores one row per company and therefore cannot represent a re-entry at all: Chevron
and Honeywell both appear as "never removed", the 2004-04-08 event is short one
removal because old AT&T Corp was merged into the SBC row, and 21 of its 49 event dates
have unequal additions and removals. It was useful only as a cross-check that produced
the same ten event dates the primary sources confirm.

---

### 6.8 Context for all hit-rate figures

The 10-year window is almost entirely a bull market (DJ30 = 18,325 on 2016-09-12 → 52,573 on 2026-09-11, +187%; v1 stated ≈17,000 for the start, which is too low). A baseline hit rate of 60–67% for "price rises over the next X days" is pure drift, not alpha. The regressions above compare signal against non-signal within the same sample and so already net out drift; the caveat applies to raw hit rates only.

---

## 7. Prior art — what a search finds, and whether it works there

**Scope of this section, stated before its findings.** Everything below is what four
searches returned, not an inventory of what exists. The four venues differ sharply in how
completely they can even be searched, and the strength of each subsection's claim differs
with it:

| Venue | Searchable how | What "found nothing" would mean |
|---|---|---|
| TradingView | Public script search over published indicators, by title and symbol | Fairly strong. Published public scripts are enumerable, so an implementation would have to be private, invite-only, or oddly titled to be missed |
| MarketInOut | Public tab list of supported indices | Strong for *existence* (the Dow McClellan tab is visibly offered), nil for *correctness* — the figures are premium-gated and client-rendered, so the implementation itself was never inspected |
| QuantifiedStrategies | Search-result snippet only; page behind a bot check | Weak in both directions. Neither the instrument nor the parameters were verifiable |
| eToro | Recent-activity sample of ~130 posts; no full-text historical search exposed by the API | Weakest. See §7.1 — a platform-wide census was not possible |

So the honest form of this section's claim is: **every implementation the search surfaced
fails review, and the search was thorough on TradingView and shallow on eToro.** The
finding that matters for the question — that apparent corroboration ("tools exist, people
use this") does not survive inspection — rests on the TradingView scripts, which are the
venue where the search was most nearly complete. It does not rest on the eToro null.

### 7.1 eToro feed — a null result, not an implementation

**The search found no DJ30 analysis on eToro to review.** This subsection records a
negative search result, which is the nearest available answer to "who else is doing
this?" on the platform the question came from. There is consequently no link to give:
nothing was found that implements either indicator on the DJ30.

**What was and was not searched.** The sample is ~130 posts — the 100 most recent DJ30
feed posts plus the 30 most recent from the only author who mentioned breadth at all.
eToro has no full-text search over historical posts exposed through the API, so this is
a recent-activity sample, not a census: private profiles, closed Popular-Investor
commentary, older posts beyond the 100-post window and non-English posts were all out
of reach. A DJ30 CMO or McClellan implementation could exist on the platform and not
appear here. What can be said is bounded and still useful — nothing in the visible,
recent DJ30 conversation uses either indicator.

- Risch's post: `totalCommentsAndReplies = 1` — only Boris's own reply; nobody else responded
- 100 DJ30 feed posts scanned: no mention of CMO; McClellan only from **MKSal1**
- MKSal1's own feed (30 posts): "breadth" 37×, "advance/decline" 71× combined, but **"McClellan Oscillator" exactly once** (value −73, NYSE scale) — in passing, inside prose market commentary, with no discernible trading rule and no backtest
- Chande Momentum Oscillator: not mentioned in any of the ~130 posts scanned

**Conclusion, stated to the limit of the sample.** Within those ~130 posts: zero
implementations, zero backtests, one incidental mention of a raw McClellan value on the
wrong (NYSE) scale. Risch's question does not appear to be a request to replicate
something already circulating in the visible feed — but the search cannot rule out prior
art elsewhere on the platform.

### 7.2 TradingView scripts

**a) `McClellan Oscillator for DAX (GER30) [aftabmk modified]`**
https://www.tradingview.com/script/UYAgnbAH-McClellan-Oscillator-for-DAX-GER30-aftabmk-modified/
→ Independently confirms the 30-issue calibration problem. Described as buggy by its own author.

**b) `Dow Jones Institutional [MarkitTick]`**
https://www.tradingview.com/script/BTaMeBea-Dow-Jones-Institutional-MarkitTick/
- Methodologically the most considered: ratio-adjusted McClellan (StockCharts variant), z-score normalisation (rolling, 100 periods, ±2.0 thresholds instead of fixed NYSE values) — a more elegant solution to the calibration problem than v1 of this analysis used. §2.2 now computes this variant too.
- **But: the ticker list is wrong.** Published 8 March 2026, no update since (the chart preview is a static snapshot, not a live chart — it only changes on republication).
  - Contains `NYSE:DOW` — removed from the index in **November 2024**, so already wrong **16 months before publication**. Not a staleness problem: the data basis was wrong from day one.
  - Missing entirely: `MMM` (3M, continuously in the index since 1976)
  - Contains `NYSE:VZ` instead of `GOOGL` — Verizon was replaced on **29 June 2026**, i.e. after publication. That is unavoidable staleness, not an author error.
  - **Consequence:** every McClellan / A-D value since the June reconstitution miscounts 3 of 30 names (10% of the universe).
- 34 likes, 1,608 views, self-marketed as "institutional-grade" — nobody checked the ticker list.

**Note on our own position here.** v1 of this document made the same `VZ`/`GOOGL` error while asserting its list was current, and applied a single roster across 10 years — a more severe version of the `NYSE:DOW` defect criticised above. Both are fixed in §1.2. The criticism stands on its merits; the point is that this error class is easy to make and only an automated roster assertion reliably catches it.

**c) `DOW 30 - Market Breadth` (maplehunger123, published 9 August 2022, v2 27 August 2022)**
https://www.tradingview.com/script/EBEkesQm-DOW-30-Market-Breadth/
(v1 of this document referred to it as `DOW 30 - Weight`; the published title is
`DOW 30 - Market Breadth`. Its own description states the basis is "all stocks in the
DJI **as of 8/9/2022**".)
- Ticker basis from 8/2022, never updated: still contains `INTC`, `WBA`, `DOW`, `VZ` (all four since replaced)
- **Copy-paste bug:** `NKE` and `PG` pull their price data from `MSFT` (`request.security("MSFT", ...)` instead of `"NKE"`/`"PG"`)
- Hard-coded weighting error: the UnitedHealth bear weight is set to `1` instead of `10.766961` as everywhere else — systematically distorts the bear sum
- Probably no longer compiles: 4 separate `request.security()` calls per stock × 30 names = 120 calls; TradingView's limit is 40
- No CMO, no real McClellan — only a VWAP/EMA bull-bear count plus an unconnected external A/D feed

### 7.3 MarketInOut.com

https://www.marketinout.com/chart/market.php?breadth=mcclellan-oscillator
(the Dow series is selected by `symbol=dow.i&indicator=97`)

Has a separate "Dow Jones McClellan Oscillator" tab (alongside S&P 500, Nasdaq 100, DAX etc.) — confirming that index-specific calibration is standard practice among commercial breadth vendors. The actual figures are rendered client-side (canvas/JS) and premium-gated, so not verifiable without an account.

### 7.4 Independent backtest hint

QuantifiedStrategies.com has already tested CMO mean reversion; per a search-result snippet the outcome "don't look appealing" — but the page itself is behind a bot check and the instrument and parameters are not verifiable. Weak corroboration only, not evidence.

---

## 8. Overall conclusion

**The standing verdict, before the detail:** the CMO is a real, well-parameterised index
mean-reversion detector on long history and *not* a trading system; the McClellan
Oscillator does not work on a 30-name index and is structurally unsuited to one. Points 1
and 2 must be read together — point 1 alone is the superseded reading.

1. **Statistically (CMO), on the 10-year DJ30 sample:** no robust signal. Three of six rows look significant naively, including one at p = 1.5 × 10⁻⁶; none survives. The strongest remnant (CMO < −30, 20 days) is p = 0.070 HAC, 0.078 clustered, 0.081 bootstrap, and 0.38 on the median non-overlapping sample — the last being the only figure computed on non-overlapping data, and it is nowhere near significance.
2. **Statistically (CMO), on 34 years — this revises how point 1 should be read.** The same signal, the same unfitted ±30 thresholds, run on `^DJI` back to 1992 (§6.4): +1.54% excess over 20 days, p = 0.001 HAC / 0.002 clustered / 0.001 bootstrap, positive in all five regimes and all seven five-year sub-periods, median ≈ mean, trimmed means flat, and *stronger* with every major crash removed. The 10-year result is therefore a power problem, not an absence — which supersedes the "no signal for either indicator" verdict of earlier revisions. It is still not something to trade on the strength of this document: the non-overlapping median is 0.105, above 5%, and a frequency-matched "trailing 20-day return < −4.84%" filter captures roughly a third of it. What the CMO detects is index mean reversion, well parameterised; exploitability after costs, and behaviour on other indices, are not tested here.
3. **Statistically (McClellan):** null, now measured rather than assumed, and null under five further robustness dimensions — a second independent vendor, price-weighted breadth, a 2%–20% threshold sweep (§6.5), and 34 years across five regimes — first under a deliberately bias-bounded roster (§6.6) and then on the **correct point-in-time roster** recovered in §6.7, where 0 of 45 rows clear both HAC and the non-overlapping test and the single apparent effect is subsumed by the CMO in a joint regression (p 0.155 vs 0.0046). Across 24 rows (two constructions × three signal types × three horizons, plus combinations), no p-value falls below 0.42 and no |t| exceeds 0.67. These rows are null in the naive test as well, so unlike the CMO rows they do not even require the overlap correction to dismiss.
4. **Structurally:** McClellan is conceptually too coarse for a 30-name universe. Two measurements make this concrete: the oscillator's range is ±5 rather than the ±70 the standard thresholds assume (§2.2) — −5.32 to +5.25 over 34 years on the survivor basket and −5.65 to +5.07 on the point-in-time roster, so not a window or roster artefact (§6.6, §6.7), and the ratio-adjusted construction collapses into the classic one (r = 0.99992) because participation barely varies when there are only 30 issues. Breadth also weights every name equally while the DJIA is price-weighted — correcting that (§6.5) produces a genuinely different series, correlation 0.920, and it is null too.
5. **Prior art:** on eToro the search came back empty — no DJ30 CMO analysis in the ~130 posts that could be scanned, and one passing McClellan value on the NYSE scale with no rule or backtest (§7.1). That sample is a recent-activity slice, not a platform census, so it is evidence of nothing found rather than proof nothing exists. Every implementation found off-platform (TradingView ×3, MarketInOut) has either no defensible methodology, a documented bug, a stale data basis, or all three at once. The apparent corroboration ("there are tools and people using this, after all") does not survive inspection. v1 of this document belongs partly in that list too — and so did the first draft of this revision, which invented two phantom index changes out of ticker renames (§0, defect 5). That is the strongest available argument for the assertions and printed diagnostics in §1.2 and §2.2: the errors were caught by guards, not by reading.
6. **Why such indicators remain popular anyway:** as regime filters rather than standalone signals, possible Schelling-point effects in thinly traded names, process discipline independent of statistical content, and a content/tool industry that monetises access rather than verified edge.

---

## 9. Open points

**Resolved in this revision:**
- ~~Re-run the full pipeline with point-in-time membership and adjusted prices~~ — done, §6
- ~~Run both McClellan variants~~ — done, and they turn out not to be independent (§2.2)
- ~~Apply §5.4 to every signal including the CMO rows~~ — done, all 30 rows in §6
- ~~Verify every row of `DJIA_CHANGES` against S&P DJI announcements~~ — done, all nine rows plus end-completeness confirmed (§1.2). The `GOOGL`/`VZ` entry is verified against the S&P release of 2026-06-23
- ~~Rule out spin-off discontinuities that `auto_adjust` does not handle~~ — done twice: a magnitude scan (§6.3, one artefact worth one sign(diff) day in 75,420) and, more sharply, a full two-vendor replication (§6.5, 27 disagreeing member-days in 75,420, 22 of them `DD`). The Solstice/`HON` spin-off of 2025-10-30 was found by event search rather than by the scan, and is clean in both vendors
- ~~Test other periods and regimes (2000–2010 sideways/bear market) to check the regime dependence~~ — done (§6.4), and it **changed the CMO conclusion**: the oversold signal is positive in all five regimes and significant on 34 years of `^DJI`
- ~~Replicate breadth from a single independent vendor, to retire the two-vendor splice risk~~ — done (§6.5): correlation 0.999949, max p-shift 0.019
- ~~Correct equal-weighted breadth to price-weighted, as the DJIA's own construction implies~~ — done (§6.5): correlation 0.920 with equal-weighted, still null
- ~~Replace the single held-out percentile threshold with a sweep~~ — done (§6.5): 0 of 63 combinations significant
- ~~Obtain `WBA` daily history for 2018-06-26 → 2024-02-26 and re-run~~ — done (§1.1a): retrieved from Tiingo, cross-validated against Financial Modeling Prep, breadth universe now 30 on all 2,514 days

**Further work:**
- ~~Extend the McClellan test beyond 2016~~ — done twice: under a measured roster bias (§6.6), then on the reconstructed point-in-time roster (§6.7) after nine former members turned out to be available free under their retired tickers. 34 years, five regimes, 0 of 45 rows clearing both tests, McClellan subsumed by the CMO. **No data purchase needed** — the FMP paid tier §6.6 contemplated would have bought nothing that mattered
- Re-verify the corrected `membership_mask` against a third construction — the re-entry defect found in §6.7 did not affect any published result, but it was the fourth defect in the membership code found by running it rather than reading it, and that code is now load-bearing for 34 years instead of 10
- Test the §6.4 CMO effect on other indices and after transaction costs, before treating it as anything more than a measured statistical regularity
- Follow up on the QuantifiedStrategies backtest details once the bot check can be passed
- Rebuild the MarkitTick script with a corrected ticker list (`MMM` instead of `DOW`, `GOOGL` instead of `VZ`) and recompute its A/D values since June 2026, to quantify the magnitude of the distortion

---

## Appendix: limitations register

Twelve limitations were recorded across the revisions of this document. Eleven are now
resolved by computation — including the pre-2016 roster, which was resolved by finding
the data rather than by working around its absence (§6.7) — and two are resolved only by
construction. What remains is a precision caveat on the 1990s, affecting no conclusion.
Nothing in this register still blocks a verdict.

**Resolved by computation — the limitation was measured and found not to change the result**

| Limitation | Affects | Resolution |
|---|---|---|
| Membership history unverified against primary source | McClellan | All nine `DJIA_CHANGES` rows verified against S&P DJI announcements, with completeness checks at both ends of the sample (§1.2) |
| `WBA` missing 2018–2024, so the breadth universe was 29 not 30 on 1,425 of 2,514 days | McClellan | Spliced from Tiingo and cross-validated against FMP (§1.1a); universe is 30 on all 2,514 days, 75,420 member-days, and the §2.2 guard is a hard assertion again. Cost of the omission: every McClellan p-value moved, median 0.079, max 0.164 |
| Delisted tickers unresolvable by `yfinance` | McClellan, early sample | Two of three were phantom (`DWDP`, `UTX` — renames, not constituent changes; §0 defect 5); the third, `WBA`, is sourced elsewhere |
| Breadth prices come from two vendors (Yahoo for 29 names, Tiingo for `WBA`) | McClellan | Breadth rebuilt **entirely** from Tiingo for all 30 names (§6.5): correlation 0.999949, 27 disagreeing member-days in 75,420, max p-shift 0.019. The splice is not driving anything |
| Spin-offs are not necessarily handled by `auto_adjust` | McClellan | Two independent tests: a ±15% magnitude scan (§6.3) and cross-vendor disagreement (§6.5), where 22 of 27 disagreeing days are `DD`, the merger-and-spin-off name, worth ≤ 0.019 in p. The in-sample `HON`/Solstice spin-off of 2025-10-30 is clean in both vendors. The earlier flat claim that `auto_adjust` ignores spin-offs was too strong (§6.3) |
| Future `HON` aerospace spin-off / rename | Any extension of the sample | Confirmed **not** in-sample: the Aerospace separation is scheduled for H2 2026, after the window, and no 2026 `HON` move exceeds ±12%. The *other* Honeywell spin-off (Solstice, 2025-10-30) **is** in-sample and was checked directly (§6.5) |
| Thresholds calibrated in-sample (v1) | McClellan extremes, COMBO | Held-out calibration on the first half (§3); realised thresholds −2.40/+2.03 classic, −8.01/+6.82 ratio |
| In-sample percentile thresholds amplify single observations | McClellan `overbought` rows | Measured (§6.3): one member-day in 75,420 moves a p-value by 0.11 through the threshold alone. Then removed as a choice altogether by sweeping 2%–20% (§6.5): 0 of 63 combinations significant, min p 0.151 |
| Equal-weighted breadth vs price-weighted index | McClellan | **Corrected and tested** (§6.5), upgraded from "noted, not corrected": price-weighted breadth is a genuinely different series (r = 0.920, same sign on 92.5% of days) and is also null — min p 0.249, max \|t\| 1.15 |
| Single index, single 10-year bull regime (+187%) | All CMO conclusions | **Resolved for the CMO, and it changed the answer** (§6.4). 34 years of `^DJI`, five regimes including a decade in which the index fell 8%: the oversold signal is positive in all five and significant on full history. The 10-year sample was underpowered, not empty |

**Resolved only by construction — no further test is possible on this universe**

| Limitation | Affects | Status |
|---|---|---|
| Overlapping windows leave few independent units (105 episodes for 180 signal days at h = 20) | All signals | Addressed four ways (§5.1–5.4); the non-overlapping median is the figure to trust. The full-history run (§6.4) supplies 399 episodes for the CMO, nearly four times as many, which is the only real remedy — more data, not a better estimator. For the McClellan rows the episode count cannot be increased without a pre-2016 roster |
| Ratio-adjusted variant is not an independent check (r = 0.99992 with classic) | McClellan robustness | Measured and disclosed (§2.2); irreducible on a 30-issue universe, because participation barely varies. Partly answered instead by price-weighted breadth (§6.5), which at r = 0.920 *is* an independent construction and agrees |

**Resolved by obtaining the data that was assumed unavailable**

| Limitation | Affects | Resolution |
|---|---|---|
| No point-in-time DJIA roster before 2016 | All McClellan conclusions | **Resolved** (§6.7), and the premise was wrong rather than the test. Nine former members — `AA`, `MO`, `GT`, `IP`, `HPQ`, `AIG`, `BAC`, `C`, `T` — have complete Yahoo history from 1992-01-02 under their own retired tickers; only ten companies that no longer exist in any form are genuinely gone. The ten pre-2016 membership events were verified to §1.2's standard, four against S&P Global releases. Mis-assigned member-days fall from 30.3% (§6.6's fixed basket) to **7.94%**, the 2016–2026 era reproduces 30 of 30 independently confirming §1.2, and the verdict is unchanged: 0 of 45 rows clear both tests, and McClellan is subsumed by the CMO jointly (p 0.155 vs 0.0046; p 0.142 even in its strongest window). No data purchase was required |

**Residual, bounded — affects precision only, not any conclusion**

| Limitation | Affects | Status |
|---|---|---|
| Ten 1990s members are unobtainable at every vendor | McClellan p-value precision, 1992–2000 only | Westinghouse, Texaco, Bethlehem Steel, Woolworth, Sears, Union Carbide, AT&T Corp, Kodak, pre-bankruptcy GM and Kraft have no usable history anywhere, and their tickers have been reassigned to unrelated issuers so no substitution is safe. Coverage is 22.44 of 30 in 1992–2000, outside the k ≤ 6 envelope measured in §6.6; 28.08 in 2000–2010, inside it; 30 of 30 from 2016. Individual 1990s p-values should not be quoted as point estimates. No row in that era is significant under any test, and the §6.6 dropout experiment showed damage of this size adds variance without manufacturing significance, so no conclusion rests on it |
