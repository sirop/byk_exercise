# CMO / McClellan Oscillator auf DJ30 — Vollständige Analyse

**Kontext:** Antwort auf Max Rischs Frage im eToro DJ30-Feed, ob Chande Momentum Oscillator (CMO) und McClellan Oscillator auf den Dow Jones 30 funktionieren.

**Kernbefund:** Kein statistisch abgesichertes Signal. Weder CMO noch McClellan überleben eine korrekte Behandlung der Autokorrelation überlappender Rückgabefenster (Newey-West HAC). Zusätzlich: keine der öffentlich auffindbaren Implementierungen (eToro-Feed, TradingView-Skripte, MarketInOut) hält einer Code-Prüfung stand.

---

## 1. Daten

DJ30-Index (`^DJI`) + alle 30 Konstituenten, 10 Jahre tägliche Kurse via `yfinance`.

```python
import yfinance as yf
import pandas as pd

tickers = ["GS","CAT","MSFT","UNH","AMGN","V","TRV","JPM","AXP","SHW",
           "AAPL","HD","JNJ","MCD","AMZN","CRM","IBM","NVDA","CVX","BA",
           "HON","MMM","MRK","PG","CSCO","WMT","DIS","KO","VZ","NKE"]

data = yf.download(tickers + ["^DJI"], period="10y", interval="1d",
                    group_by="ticker", auto_adjust=False, threads=True)
data.to_pickle("dj30_raw.pkl")
```

**Wichtig:** Diese Ticker-Liste war zum Zeitpunkt der Analyse (September 2026) korrekt. Sie muss nach jeder DJIA-Rekonstitution aktualisiert werden. Bekannte Swaps: WBA→AMZN (Feb 2024), INTC→NVDA & DOW→SHW (Nov 2024), VZ→GOOGL (Juni 2026).

Ergebnis: 2513 Handelstage, alle 30 Titel vollständig.

---

## 2. Indikator-Berechnung

### 2.1 Chande Momentum Oscillator (CMO), Fenster = 20, auf DJ30-Index selbst

```python
import numpy as np

def cmo(series, window=20):
    diff = series.diff()
    gains = diff.clip(lower=0)
    losses = -diff.clip(upper=0)
    sum_gain = gains.rolling(window).sum()
    sum_loss = losses.rolling(window).sum()
    return 100 * (sum_gain - sum_loss) / (sum_gain + sum_loss)

dj30 = data["^DJI"]["Close"].dropna()
cmo_series = cmo(dj30, 20)
```

### 2.2 McClellan Oscillator, über alle 30 Konstituenten

```python
closes = pd.DataFrame({t: data[t]["Close"] for t in tickers}).dropna(how="all")
closes = closes.reindex(dj30.index).ffill()

daily_change = closes.diff()
advances = (daily_change > 0).sum(axis=1)
declines = (daily_change < 0).sum(axis=1)
net_advances = advances - declines

ema19 = net_advances.ewm(span=19, adjust=False).mean()
ema39 = net_advances.ewm(span=39, adjust=False).mean()
mcclellan = ema19 - ema39
```

### ⚠️ Kalibrierungsfehler, den wir zuerst selbst gemacht haben

Die Standard-Schwellen für "extreme" McClellan-Werte (±70) stammen aus dem NYSE-Kontext (~2000+ Titel). Auf 30 Titel skaliert:

```python
df["mcclellan"].describe()
# mean   -0.002   std   1.363   min  -5.35   max  5.16
# 5. Perzentil: -2.38   95. Perzentil: +2.13
```

Die Range liegt bei ±5, nicht ±70. **Unabhängig bestätigt:** ein TradingView-Nutzer (`aftabmk`) hat exakt dasselbe Problem beim Umbau des McClellan Oscillators für den DAX (GER30, ebenfalls 30 Titel) dokumentiert — sein Skript ist aber selbst fehlerhaft (Autor-Eigenangabe: A/D-Logik erkennt fallende Werte nicht korrekt).
→ https://www.tradingview.com/script/UYAgnbAH-McClellan-Oscillator-for-DAX-GER30-aftabmk-modified/

---

## 3. Backtest: Forward Returns nach Signal

Getestete Signale: CMO < -30 / > 30, McClellan Zero-Cross, McClellan-Extremwerte (5./95. Perzentil, korrekt skaliert), Kombisignal.

```python
horizons = [5, 10, 20]
for h in horizons:
    df[f"fwd_{h}"] = close.shift(-h) / close - 1
```

### 3.1 Naiver Welch-t-Test — **METHODISCH FEHLERHAFT, siehe Abschnitt 4**

```python
from scipy import stats
t, p = stats.ttest_ind(sig_ret, non_sig_ret, equal_var=False)
```

Erster (falscher) Befund: CMO < -30 bei 20 Tagen signifikant mit p=0,0022, übersteht sogar Bonferroni-Korrektur (α=0,05/18 Tests). CMO > 30 bei 20 Tagen: p<0,0001.

---

## 4. Kritische Korrektur: Fensterüberlappung

**Problem:** Jeder Handelstag hat sein eigenes 20-Tage-Vorwärtsfenster. Tag *n* und Tag *n+1* teilen sich 19 von 20 Tagen — die "unabhängigen" Beobachtungen im t-Test sind massiv autokorreliert. Der naive t-Test tut so, als hätte man z.B. 180 unabhängige Datenpunkte (CMO<-30, n=180), real sind es eher 180/20 ≈ 9 unabhängige 20-Tage-Perioden.

**Fix: Newey-West (HAC) Standardfehler**, `maxlags = Horizont`:

```python
import statsmodels.api as sm

sub["signal"] = mask.astype(int)
y = sub[f"fwd_{h}"]
X = sm.add_constant(sub["signal"])
model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": h})
coef = model.params["signal"]
p_hac = model.pvalues["signal"]
```

### Ergebnis nach Korrektur — kein Signal mehr signifikant

| Signal | Horizont | n | Effekt (Δ Mittelwert) | t (HAC) | p (HAC) | Signifikant (5%)? |
|---|---|---|---|---|---|---|
| CMO < -30 | 5d | 181 | +0.23% | 0.40 | 0.690 | Nein |
| CMO < -30 | 10d | 180 | +0.19% | 0.23 | 0.819 | Nein |
| **CMO < -30** | **20d** | 180 | **+1.53%** | 1.84 | **0.066** | **Nein (knapp)** |
| CMO > 30 | 5d | 644 | -0.13% | -0.88 | 0.378 | Nein |
| CMO > 30 | 10d | 644 | -0.33% | -1.22 | 0.222 | Nein |
| CMO > 30 | 20d | 643 | -0.77% | -1.64 | 0.101 | Nein |
| McClellan Zero-Cross Up | 5/10/20d | 236-238 | ±0.02-0.19% | ~0.1-0.8 | 0.44-0.93 | Nein |
| McClellan < -2.4 (oversold) | 5/10/20d | 118 | -0.12 bis -0.72% | -0.04 bis -0.58 | 0.56-0.97 | Nein |
| McClellan > 2.1 (overbought) | 5/10/20d | 133 | +0.07-0.41% | 0.33-0.59 | 0.56-0.74 | Nein |
| COMBO CMO<-30 & McClellan<-1.8 | 20d | 92 | +1.78% | 1.50 | 0.133 | Nein |

**Fazit:** Vor der Korrektur wirkte CMO wie ein robustes 20-Tage-Signal. Nach korrekter Behandlung der Überlappung verschwindet der Effekt — der stärkste Rest (CMO<-30, 20d, p=0,066) verfehlt sogar die unkorrigierte 5%-Schwelle knapp. McClellan zeigt in keiner Variante auch nur ansatzweise Signifikanz.

**Einordnung:** 10-Jahres-Fenster ist fast durchgehend Bullenmarkt (DJ30 ~17.000 → ~52.000). Baseline-Trefferquote von 60-67% für "Kurs steigt in den nächsten X Tagen" ist reiner Drift, kein Alpha — Vorsicht bei der Interpretation der rohen Hit-Rates.

---

## 5. Prior Art — Wer nutzt das sonst, und funktioniert es dort?

### 5.1 eToro-Feed

- Rischs Post: `totalCommentsAndReplies = 1` — ausschließlich Boris' eigene Zusage, niemand sonst hat geantwortet
- 100 DJ30-Feed-Posts gescannt: keine CMO-Erwähnung, McClellan nur bei **MKSal1**
- MKSal1s eigener Feed (30 Posts): "breadth" 37×, "advance/decline" 71× kombiniert, **"McClellan Oscillator" nur 1×** (Wert -73, NYSE-Skala) — beiläufig in Fließtext-Marktkommentar, keine erkennbare Handelsregel, kein Backtest
- Chande Momentum Oscillator: in keinem der ~130 gescannten Posts erwähnt

### 5.2 TradingView-Skripte

**a) `McClellan Oscillator for DAX (GER30) [aftabmk modified]`**
https://www.tradingview.com/script/UYAgnbAH-McClellan-Oscillator-for-DAX-GER30-aftabmk-modified/
→ Bestätigt unabhängig das 30-Titel-Kalibrierungsproblem. Vom Autor selbst als buggy bezeichnet.

**b) `Dow Jones Institutional [MarkitTick]`**
https://www.tradingview.com/script/BTaMeBea-Dow-Jones-Institutional-MarkitTick/
- Methodisch am durchdachtesten: Ratio-adjustierter McClellan (StockCharts-Variante), Z-Score-Normalisierung (rollierend, 100 Perioden, ±2,0-Schwellen statt fixer NYSE-Werte) — löst das Kalibrierungsproblem eleganter als unser eigener Ansatz
- **Aber: Ticker-Liste fehlerhaft.** Veröffentlicht 8. März 2026, seither kein Update (Chart-Vorschau ist ein statischer Snapshot, kein Live-Chart — ändert sich nur bei erneuter Skript-Veröffentlichung)
  - Enthält `NYSE:DOW` — aus dem Index entfernt im **November 2024**, also **schon 16 Monate vor Veröffentlichung** falsch. Kein Update-Problem, sondern von Tag 1 an falsche Datenbasis
  - Fehlt komplett: `MMM` (3M, seit 1976 durchgehend im Index)
  - Enthält `NYSE:VZ` statt `GOOGL` — Verizon wurde erst am **29. Juni 2026** ersetzt, also nach Veröffentlichung. Das ist reine, unvermeidbare Staleness, kein Autorenfehler
  - **Konsequenz:** jeder McClellan-/A-D-Wert seit der Juni-Rekonstitution zählt 3 von 30 Titeln falsch (10% des Universums)
- 34 Likes, 1.608 Aufrufe, Eigenmarketing "institutional-grade" — niemand hat die Ticker-Liste geprüft

**c) `DOW 30 - Weight` (maplehunger123, 2022)**
- Ticker-Basis von 8/2022, nie aktualisiert: enthält noch `INTC`, `WBA`, `DOW`, `VZ` (alle vier seither ersetzt)
- **Copy-Paste-Bug:** `NKE` und `PG` beziehen ihre Kursdaten fälschlich von `MSFT` (`request.security("MSFT", ...)` statt `"NKE"`/`"PG"`)
- Hartcodierter Gewichtungsfehler: UnitedHealth-Bär-Gewicht ist auf `1` gesetzt statt `10.766961` wie überall sonst — verzerrt die Bär-Summe systematisch
- Vermutlich nicht mehr kompilierbar: 4 separate `request.security()`-Calls pro Aktie × 30 Titel = 120 Calls, TradingViews Limit liegt bei 40
- Kein CMO, kein echter McClellan — nur VWAP/EMA-Bull-Bear-Zählung plus unverknüpfter externer A/D-Feed

### 5.3 MarketInOut.com

Hat einen separaten "Dow Jones McClellan Oscillator"-Tab (neben S&P 500, Nasdaq 100, DAX etc.) — bestätigt, dass Index-spezifische Kalibrierung unter kommerziellen Breadth-Anbietern Standard ist. Tatsächliche Zahlen sind clientseitig gerendert (Canvas/JS) und premium-gated, nicht verifizierbar ohne Account.

### 5.4 Unabhängiger Backtest-Hinweis

QuantifiedStrategies.com hat CMO-Mean-Reversion bereits getestet, Ergebnis laut Suchergebnis-Snippet "don't look appealing" — Seite selbst hinter Bot-Check blockiert, Instrument/Parameter nicht verifizierbar, daher nur als schwacher Hinweis zu werten, nicht als Beleg.

---

## 6. Gesamtfazit

1. **Statistisch:** Weder CMO noch McClellan zeigen auf DJ30 über 10 Jahre ein Newey-West-robustes Signal. Der stärkste Rest (CMO, 20 Tage) verfehlt selbst die unkorrigierte 5%-Schwelle.
2. **Strukturell:** McClellan ist für ein 30-Titel-Universum konzeptionell zu grob — zu wenig Auflösung, unabhängig von der Schwellenwert-Kalibrierung.
3. **Prior Art:** Jede öffentlich auffindbare Implementierung (eToro, TradingView ×3, MarketInOut) hat entweder keine belastbare Methodik, einen dokumentierten Bug, eine veraltete Datenbasis, oder alle drei gleichzeitig. Die vermeintliche Bestätigung ("es gibt doch Tools/Leute, die das nutzen") hält bei genauer Prüfung nicht stand.
4. **Warum solche Indikatoren trotzdem verbreitet sind:** Regime-Filter statt Einzelsignal, mögliche Schelling-Point-Effekte bei dünn gehandelten Titeln, Prozessdisziplin unabhängig vom statistischen Gehalt, und eine Content-/Tool-Industrie, die von Zugang lebt, nicht von geprüftem Edge.

---

## 7. Offene Punkte für Notebook-Erweiterung

- Non-overlapping Resampling als zweite Robustheitsprobe (jeden 20. Tag als Ereignis, kleinere aber echt unabhängige Stichprobe)
- Test auf anderen Zeiträumen/Regimes (2000-2010 Seitwärts-/Bärenmarkt) um Regime-Abhängigkeit des naiven Befunds zu prüfen
- QuantifiedStrategies-Backtest-Details nachrecherchieren, sobald Bot-Check umgehbar
- MarkitTick-Skript mit korrigierter Ticker-Liste (MMM statt DOW, GOOGL statt VZ) nachbauen und A/D-Werte seit Juni 2026 neu berechnen, um das Ausmaß der Verzerrung zu quantifizieren
