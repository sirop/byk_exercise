from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf


AS_OF_DATE = "2026-09-10"
OUTPUT_DIRECTORY = Path("analysis-output")
MARKET_DATA_START = "2013-01-01"
HOLDING_HORIZONS = (30, 60, 90, 180, 270, 365)
DEFAULT_CARRYING_COST_PCT = 10.0
DEFAULT_MAE_PERCENTILE_THRESHOLD = 90.0


@dataclass(frozen=True)
class Position:
    ticker: str
    benchmark_proxy: str
    daily_multiplier: int
    opened_at: str
    open_rate: float
    account_leverage: int
    live_net_profit_pct: float
    stop_loss_rate: float
    take_profit_rate: float


POSITIONS = (
    Position("JNUG", "GDXJ", 2, "2025-08-07T16:34:38Z", 89.4456, 1, -37.729502, 300.0, 0.0),
    Position("JNUG", "GDXJ", 2, "2025-05-08T16:41:34Z", 69.7752, 1, -43.746710, 300.0, 0.0),
    Position("JNUG", "GDXJ", 2, "2025-08-07T17:34:13Z", 88.8166, 1, -37.934390, 300.0, 0.0),
    Position("JNUG", "GDXJ", 2, "2025-05-05T17:02:27Z", 66.1206, 2, -47.776722, 300.0, 0.02),
    Position("JNUG", "GDXJ", 2, "2025-05-21T19:58:26Z", 70.5240, 5, -48.720273, 300.0, 0.05),
    Position("JNUG", "GDXJ", 2, "2025-05-23T17:48:02Z", 74.2284, 5, -47.827858, 300.0, 0.05),
    Position("JNUG", "GDXJ", 2, "2025-06-03T15:20:43Z", 80.8585, 5, -46.167213, 300.0, 0.01),
    Position("LABU", "XBI", 3, "2026-06-17T14:18:39Z", 201.8300, 1, -22.510121, 400.0, 0.0),
    Position("LABU", "XBI", 3, "2026-05-26T15:24:09Z", 180.3800, 1, -28.660146, 400.0, 0.0),
    Position("LABU", "XBI", 3, "2026-08-17T15:03:37Z", 283.3000, 1, 4.990000, 424.37, 0.0),
    Position("LABU", "XBI", 3, "2025-12-16T18:44:06Z", 158.9612, 1, -34.378100, 400.0, 0.0),
    Position("LABU", "XBI", 3, "2025-10-27T15:22:47Z", 123.8140, 2, -47.327260, 400.0, 0.0001),
)


def get_prices(ticker: str, start: str) -> pd.DataFrame:
    prices = cast(
        pd.DataFrame,
        yf.download(
            ticker,
            start=start,
            end=pd.Timestamp(AS_OF_DATE) + pd.Timedelta(days=1),
            auto_adjust=False,
            actions=True,
            progress=False,
        ),
    )
    if prices.empty:
        raise RuntimeError(f"No market data returned for {ticker}.")
    if isinstance(prices.columns, pd.MultiIndex):
        prices.columns = prices.columns.get_level_values(0)
    required_columns = {"Close", "Adj Close"}
    if missing_columns := required_columns.difference(prices.columns):
        raise RuntimeError(f"{ticker} is missing required columns: {sorted(missing_columns)}")
    return prices.sort_index()


def first_tradable_day(prices: pd.DataFrame, opened_at: str) -> pd.Timestamp:
    entry_day = pd.Timestamp(opened_at).tz_localize(None).normalize()
    eligible_days = prices.index[prices.index >= entry_day]
    if eligible_days.empty:
        raise RuntimeError(f"No tradable day found after {entry_day.date()}.")
    return eligible_days[0]


def annualized_volatility(daily_returns: pd.Series) -> float:
    return daily_returns.std(ddof=1) * (252**0.5)


def adjusted_ohlc(prices: pd.DataFrame) -> pd.DataFrame:
    adjustment_factor = prices["Adj Close"] / prices["Close"]
    return pd.DataFrame(
        {
            "close": prices["Close"] * adjustment_factor,
            "high": prices["High"] * adjustment_factor,
            "low": prices["Low"] * adjustment_factor,
        }
    )


def directional_index(ohlc: pd.DataFrame, period: int = 14) -> pd.Series:
    up_move = ohlc["high"].diff()
    down_move = -ohlc["low"].diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    previous_close = ohlc["close"].shift()
    true_range = pd.concat(
        [
            ohlc["high"] - ohlc["low"],
            (ohlc["high"] - previous_close).abs(),
            (ohlc["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    average_true_range = true_range.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / average_true_range
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / average_true_range
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def classify_regimes(prices: pd.DataFrame, adx_threshold: int = 25, slope_window: int = 20) -> pd.DataFrame:
    ohlc = adjusted_ohlc(prices)
    regime = pd.DataFrame(index=ohlc.index)
    regime["close"] = ohlc["close"]
    regime["sma_50"] = ohlc["close"].rolling(50).mean()
    regime["sma_200"] = ohlc["close"].rolling(200).mean()
    regime["sma_50_slope"] = regime["sma_50"].pct_change(slope_window)
    regime["adx_14"] = directional_index(ohlc)
    bullish = (regime["close"] > regime["sma_200"]) & (regime["sma_50_slope"] > 0)
    bearish = (regime["close"] < regime["sma_200"]) & (regime["sma_50_slope"] < 0)
    trending = regime["adx_14"] >= adx_threshold
    regime["regime"] = "choppy_indeterminate"
    regime.loc[bullish & trending, "regime"] = "trending_bull"
    regime.loc[bearish & trending, "regime"] = "trending_bear"
    regime.loc[regime["sma_200"].isna() | regime["adx_14"].isna(), "regime"] = pd.NA
    return regime


def entry_regime_and_path(regime: pd.DataFrame, entry_day: pd.Timestamp) -> tuple[str, str]:
    prior_days = regime.index[regime.index < entry_day]
    if prior_days.empty:
        return "insufficient_history", "insufficient_history"
    entry_regime = regime.loc[prior_days[-1], "regime"]
    path = regime.loc[entry_day:, "regime"].dropna()
    if path.empty:
        return str(entry_regime), "insufficient_history"
    proportions = path.value_counts(normalize=True)
    regime_path = ", ".join(f"{name}:{value:.0%}" for name, value in proportions.items())
    return str(entry_regime), regime_path


def position_metrics(
    position: Position, prices: dict[str, pd.DataFrame], regimes: dict[str, pd.DataFrame]
) -> dict[str, object]:
    etf_prices = prices[position.ticker]
    benchmark_prices = prices[position.benchmark_proxy]
    entry_day = first_tradable_day(etf_prices, position.opened_at)
    aligned = pd.DataFrame(
        {
            "etf": etf_prices["Adj Close"],
            "benchmark": benchmark_prices["Adj Close"],
        }
    ).dropna()
    window = aligned.loc[entry_day:]
    if len(window) < 2:
        raise RuntimeError(f"Insufficient aligned history for {position.ticker} from {entry_day.date()}.")

    benchmark_daily_return = window["benchmark"].pct_change().dropna()
    benchmark_return = window["benchmark"].iloc[-1] / window["benchmark"].iloc[0] - 1
    etf_total_return = window["etf"].iloc[-1] / window["etf"].iloc[0] - 1
    daily_reset_return = cast(float, (1 + position.daily_multiplier * benchmark_daily_return).prod()) - 1
    linear_multiple_return = position.daily_multiplier * benchmark_return
    entry_regime, subsequent_regime_path = entry_regime_and_path(regimes[position.benchmark_proxy], entry_day)
    etf_path_return = window["etf"] / window["etf"].iloc[0] - 1
    current_short_mae = etf_path_return.max() * 100

    return {
        "ticker": position.ticker,
        "benchmark_proxy": position.benchmark_proxy,
        "entry_timestamp_utc": position.opened_at,
        "entry_trading_day": entry_day.date().isoformat(),
        "days_held": len(window) - 1,
        "daily_multiplier": position.daily_multiplier,
        "account_leverage": position.account_leverage,
        "open_rate_public_snapshot": position.open_rate,
        "live_net_profit_pct_public_snapshot": position.live_net_profit_pct,
        "stop_loss_rate": position.stop_loss_rate,
        "take_profit_rate": position.take_profit_rate,
        "entry_regime_prior_close": entry_regime,
        "subsequent_regime_path": subsequent_regime_path,
        "current_short_mae_pct": current_short_mae,
        "benchmark_cumulative_return_pct": benchmark_return * 100,
        "daily_reset_comparator_return_pct": daily_reset_return * 100,
        "etf_total_return_pct": etf_total_return * 100,
        "volatility_drag_vs_linear_pct": (daily_reset_return - linear_multiple_return) * 100,
        "etf_tracking_residual_vs_comparator_pct": (etf_total_return - daily_reset_return) * 100,
        "benchmark_annualized_volatility_pct": annualized_volatility(benchmark_daily_return) * 100,
    }


def rolling_decay_data(etf: str, benchmark: str, multiplier: int, prices: dict[str, pd.DataFrame]) -> pd.DataFrame:
    aligned = pd.DataFrame(
        {"etf": prices[etf]["Adj Close"], "benchmark": prices[benchmark]["Adj Close"]}
    ).dropna()
    benchmark_daily_return = aligned["benchmark"].pct_change()
    rows: list[dict[str, object]] = []

    for horizon in (30, 60, 90, 180):
        for end_index in range(horizon, len(aligned)):
            window = aligned.iloc[end_index - horizon : end_index + 1]
            daily_returns = benchmark_daily_return.iloc[end_index - horizon + 1 : end_index + 1].dropna()
            benchmark_return = window["benchmark"].iloc[-1] / window["benchmark"].iloc[0] - 1
            daily_reset_return = cast(float, (1 + multiplier * daily_returns).prod()) - 1
            rows.append(
                {
                    "ticker": etf,
                    "benchmark_proxy": benchmark,
                    "horizon_days": horizon,
                    "end_date": window.index[-1].date().isoformat(),
                    "benchmark_return_pct": benchmark_return * 100,
                    "volatility_drag_vs_linear_pct": (daily_reset_return - multiplier * benchmark_return) * 100,
                    "benchmark_annualized_volatility_pct": annualized_volatility(daily_returns) * 100,
                }
            )
    return pd.DataFrame(rows)


def regime_base_rates(regimes: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for benchmark, regime in regimes.items():
        classified_days = regime.dropna(subset=["regime"])
        for classification, count in classified_days["regime"].value_counts().items():
            rows.append(
                {
                    "benchmark_proxy": benchmark,
                    "regime": classification,
                    "days": count,
                    "percent_of_classified_days": count / len(classified_days) * 100,
                }
            )
    return pd.DataFrame(rows)


def regime_sensitivity(prices: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for benchmark in {position.benchmark_proxy for position in POSITIONS}:
        for adx_threshold in (20, 25, 30):
            for slope_window in (10, 20, 40):
                regime = classify_regimes(prices[benchmark], adx_threshold, slope_window)
                classified = regime.dropna(subset=["regime"])
                rows.extend(
                    {
                        "benchmark_proxy": benchmark,
                        "adx_threshold": adx_threshold,
                        "slope_window_days": slope_window,
                        "regime": classification,
                        "days": count,
                        "percent_of_classified_days": count / len(classified) * 100,
                    }
                    for classification, count in classified["regime"].value_counts().items()
                )
    return pd.DataFrame(rows)


def historical_short_events(
    etf: str, benchmark: str, prices: dict[str, pd.DataFrame], regimes: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    aligned = pd.DataFrame(
        {"etf": prices[etf]["Adj Close"], "benchmark": prices[benchmark]["Adj Close"]}
    ).dropna()
    prior_close_regime = regimes[benchmark]["regime"].shift(1).reindex(aligned.index)
    rows: list[dict[str, object]] = []

    for horizon in HOLDING_HORIZONS:
        for entry_index in range(len(aligned) - horizon):
            entry_regime = prior_close_regime.iloc[entry_index]
            if pd.isna(entry_regime):
                continue
            path = aligned["etf"].iloc[entry_index : entry_index + horizon + 1]
            etf_path_return = path / path.iloc[0] - 1
            short_path_return = -etf_path_return
            rows.append(
                {
                    "ticker": etf,
                    "benchmark_proxy": benchmark,
                    "entry_trading_day": path.index[0].date().isoformat(),
                    "entry_regime_prior_close": entry_regime,
                    "horizon_days": horizon,
                    "gross_short_terminal_return_pct": short_path_return.iloc[-1] * 100,
                    "short_mae_pct": etf_path_return.max() * 100,
                    "short_mfe_pct": short_path_return.max() * 100,
                    "adverse_at_horizon": short_path_return.iloc[-1] < 0,
                }
            )
    return pd.DataFrame(rows)


def historical_short_summary(events: pd.DataFrame) -> pd.DataFrame:
    group_columns = ["ticker", "benchmark_proxy", "entry_regime_prior_close", "horizon_days"]
    return (
        events.groupby(group_columns)
        .agg(
            sample_size=("short_mae_pct", "size"),
            median_short_mae_pct=("short_mae_pct", "median"),
            short_mae_p75_pct=("short_mae_pct", lambda values: values.quantile(0.75)),
            short_mae_p90_pct=("short_mae_pct", lambda values: values.quantile(0.90)),
            short_mae_p95_pct=("short_mae_pct", lambda values: values.quantile(0.95)),
            worst_short_mae_pct=("short_mae_pct", "max"),
            median_gross_short_terminal_return_pct=("gross_short_terminal_return_pct", "median"),
            adverse_at_horizon_pct=("adverse_at_horizon", "mean"),
        )
        .assign(adverse_at_horizon_pct=lambda frame: frame["adverse_at_horizon_pct"] * 100)
        .reset_index()
    )


def attach_short_mae_percentiles(per_position: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    result = per_position.copy()
    result["comparison_horizon_days"] = result["days_held"].apply(
        lambda days_held: min(HOLDING_HORIZONS, key=lambda horizon: abs(horizon - days_held))
    )
    percentiles: list[float] = []
    sample_sizes: list[int] = []
    for position in result.itertuples(index=False):
        comparison_sample = events[
            (events["ticker"] == position.ticker)
            & (events["entry_regime_prior_close"] == position.entry_regime_prior_close)
            & (events["horizon_days"] == position.comparison_horizon_days)
        ]["short_mae_pct"]
        sample_sizes.append(len(comparison_sample))
        percentiles.append((comparison_sample <= position.current_short_mae_pct).mean() * 100)
    result["historical_short_mae_sample_size"] = sample_sizes
    result["current_short_mae_percentile"] = percentiles
    return result


def build_decision_scorecard(
    per_position: pd.DataFrame,
    historical_summary: pd.DataFrame,
    annual_carrying_cost_pct: float,
    mae_percentile_threshold: float,
    max_position_loss_pct: float | None,
    max_aggregate_loss_pct: float | None,
) -> pd.DataFrame:
    scorecard = per_position.copy()
    matching_summary = historical_summary.rename(
        columns={
            "horizon_days": "comparison_horizon_days",
            "median_gross_short_terminal_return_pct": "historical_median_gross_short_return_pct",
        }
    )[
        [
            "ticker",
            "entry_regime_prior_close",
            "comparison_horizon_days",
            "sample_size",
            "historical_median_gross_short_return_pct",
        ]
    ]
    scorecard = scorecard.merge(
        matching_summary,
        on=["ticker", "entry_regime_prior_close", "comparison_horizon_days"],
        how="left",
    )
    scorecard["annual_carrying_cost_pct"] = annual_carrying_cost_pct
    scorecard["estimated_carrying_cost_pct"] = annual_carrying_cost_pct * scorecard["days_held"] / 365
    scorecard["modeled_net_short_return_pct"] = -scorecard["etf_total_return_pct"] - scorecard[
        "estimated_carrying_cost_pct"
    ]
    scorecard["historical_median_net_short_return_pct"] = scorecard[
        "historical_median_gross_short_return_pct"
    ] - annual_carrying_cost_pct * scorecard["comparison_horizon_days"] / 365
    scorecard["mae_percentile_threshold"] = mae_percentile_threshold
    scorecard["max_position_loss_pct"] = max_position_loss_pct
    scorecard["max_aggregate_loss_pct"] = max_aggregate_loss_pct
    scorecard["aggregate_loss_limit_status"] = "not_evaluable_without_account_equity_and_dollar_exposure"

    decisions: list[str] = []
    reasons: list[str] = []
    for _, position in scorecard.iterrows():
        entry_regime = str(position["entry_regime_prior_close"])
        historical_net_return = float(position["historical_median_net_short_return_pct"])
        mae_percentile = float(position["current_short_mae_percentile"])
        modeled_net_return = float(position["modeled_net_short_return_pct"])
        historical_sample_size = int(position["historical_short_mae_sample_size"])
        decision_reasons: list[str] = []
        if entry_regime.startswith("trending_"):
            decision_reasons.append("trending entry regime")
        if historical_net_return <= 0:
            decision_reasons.append("non-positive historical net expectancy")
        if mae_percentile >= mae_percentile_threshold:
            decision_reasons.append("MAE percentile threshold breached")
        if max_position_loss_pct is not None and -modeled_net_return >= max_position_loss_pct:
            decision_reasons.append("modeled position-loss limit breached")
        if historical_sample_size < 100:
            decisions.append("insufficient_evidence")
            reasons.append("historical comparison sample below 100 events")
        elif decision_reasons:
            decisions.append("stop_copying_no_new_shorts")
            reasons.append("; ".join(decision_reasons))
        else:
            decisions.append("eligible_only_with_controls")
            reasons.append("choppy entry, positive historical net expectancy, and MAE below threshold")
    scorecard["decision"] = decisions
    scorecard["decision_reason"] = reasons
    return scorecard


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze JNUG/LABU daily-reset ETF short risk.")
    parser.add_argument(
        "--annual-carrying-cost-pct",
        type=float,
        default=DEFAULT_CARRYING_COST_PCT,
        help=f"Annualized financing/borrow-cost assumption in percent (default: {DEFAULT_CARRYING_COST_PCT}).",
    )
    parser.add_argument(
        "--mae-percentile-threshold",
        type=float,
        default=DEFAULT_MAE_PERCENTILE_THRESHOLD,
        help=f"MAE percentile that triggers a stop signal (default: {DEFAULT_MAE_PERCENTILE_THRESHOLD}).",
    )
    parser.add_argument(
        "--max-position-loss-pct",
        type=float,
        help="Optional maximum modeled loss per position as a percent of invested exposure.",
    )
    parser.add_argument(
        "--max-aggregate-loss-pct",
        type=float,
        help="Optional maximum aggregate account loss as a percent of equity; reported but not evaluable without dollar exposure.",
    )
    arguments = parser.parse_args()
    if arguments.annual_carrying_cost_pct < 0:
        parser.error("--annual-carrying-cost-pct must be non-negative.")
    if not 0 <= arguments.mae_percentile_threshold <= 100:
        parser.error("--mae-percentile-threshold must be between 0 and 100.")
    if arguments.max_position_loss_pct is not None and arguments.max_position_loss_pct <= 0:
        parser.error("--max-position-loss-pct must be positive.")
    if arguments.max_aggregate_loss_pct is not None and arguments.max_aggregate_loss_pct <= 0:
        parser.error("--max-aggregate-loss-pct must be positive.")
    return arguments


def main(arguments: argparse.Namespace) -> None:
    OUTPUT_DIRECTORY.mkdir(exist_ok=True)
    tickers = {position.ticker for position in POSITIONS} | {position.benchmark_proxy for position in POSITIONS}
    prices = {ticker: get_prices(ticker, MARKET_DATA_START) for ticker in tickers}
    regimes = {
        benchmark: classify_regimes(prices[benchmark])
        for benchmark in {position.benchmark_proxy for position in POSITIONS}
    }

    short_events = pd.concat(
        [
            historical_short_events("JNUG", "GDXJ", prices, regimes),
            historical_short_events("LABU", "XBI", prices, regimes),
        ],
        ignore_index=True,
    )
    short_events.to_csv(OUTPUT_DIRECTORY / "historical_short_events.csv", index=False)
    short_summary = historical_short_summary(short_events)
    short_summary.to_csv(OUTPUT_DIRECTORY / "historical_short_risk_summary.csv", index=False)

    per_position = pd.DataFrame(position_metrics(position, prices, regimes) for position in POSITIONS)
    per_position = attach_short_mae_percentiles(per_position, short_events)
    per_position.to_csv(OUTPUT_DIRECTORY / "per_position_attribution.csv", index=False)
    decision_scorecard = build_decision_scorecard(
        per_position,
        short_summary,
        arguments.annual_carrying_cost_pct,
        arguments.mae_percentile_threshold,
        arguments.max_position_loss_pct,
        arguments.max_aggregate_loss_pct,
    )
    decision_scorecard.to_csv(OUTPUT_DIRECTORY / "decision_scorecard.csv", index=False)

    regime_base_rates(regimes).to_csv(OUTPUT_DIRECTORY / "regime_base_rates.csv", index=False)
    regime_sensitivity(prices).to_csv(OUTPUT_DIRECTORY / "regime_sensitivity.csv", index=False)

    rolling = pd.concat(
        [
            rolling_decay_data("JNUG", "GDXJ", 2, prices),
            rolling_decay_data("LABU", "XBI", 3, prices),
        ],
        ignore_index=True,
    )
    rolling.to_csv(OUTPUT_DIRECTORY / "rolling_volatility_drag.csv", index=False)

    figure, axis = plt.subplots(figsize=(10, 6))
    for ticker, group in rolling.groupby("ticker"):
        axis.scatter(
            group["benchmark_annualized_volatility_pct"],
            group["volatility_drag_vs_linear_pct"],
            alpha=0.2,
            label=ticker,
        )
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set_xlabel("Benchmark annualized volatility (%)")
    axis.set_ylabel("Daily-reset comparator minus linear multiple (%)")
    axis.legend()
    figure.tight_layout()
    figure.savefig(OUTPUT_DIRECTORY / "volatility_drag.png", dpi=160)

    print(decision_scorecard.to_string(index=False, float_format=lambda value: f"{value:.2f}"))
    print(f"\nWrote analysis outputs to {OUTPUT_DIRECTORY.resolve()}")


if __name__ == "__main__":
    main(parse_arguments())