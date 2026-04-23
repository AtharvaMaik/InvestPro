from __future__ import annotations

import pandas as pd


def winsorize(values: pd.Series, lower: float = 0.05, upper: float = 0.95) -> pd.Series:
    clean = values.dropna().astype(float)
    if clean.empty:
        return values.astype(float)
    low = clean.quantile(lower)
    high = clean.quantile(upper)
    return values.astype(float).clip(lower=low, upper=high)


def zscore_factor(values: pd.Series, higher_is_better: bool = True) -> pd.Series:
    clipped = winsorize(values)
    std = clipped.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=values.index)
    z_score = (clipped - clipped.mean()) / std
    return z_score if higher_is_better else -z_score


def composite_scores(factor_scores: dict[str, pd.Series], weights: dict[str, float]) -> pd.Series:
    total_weight = sum(abs(weight) for weight in weights.values())
    if total_weight == 0:
        raise ValueError("At least one factor weight must be non-zero.")

    normalized = {key: value / total_weight for key, value in weights.items()}
    result: pd.Series | None = None
    for factor_id, scores in factor_scores.items():
        weighted = scores.fillna(0) * normalized.get(factor_id, 0)
        result = weighted if result is None else result.add(weighted, fill_value=0)

    if result is None:
        return pd.Series(dtype=float)
    return result.sort_values(ascending=False)


def momentum(prices: pd.Series, lookback_days: int) -> float | None:
    clean = prices.dropna()
    if len(clean) <= lookback_days:
        return None
    return float((clean.iloc[-1] / clean.iloc[-lookback_days - 1]) - 1)


def trailing_volatility(prices: pd.Series, lookback_days: int, periods_per_year: int = 252) -> float | None:
    returns = prices.dropna().pct_change().dropna()
    if len(returns) < lookback_days:
        return None
    return float(returns.tail(lookback_days).std(ddof=1) * (periods_per_year**0.5))


def average_traded_value(close: pd.Series, volume: pd.Series, lookback_days: int) -> float | None:
    traded_value = (close * volume).dropna()
    if len(traded_value) < lookback_days:
        return None
    return float(traded_value.tail(lookback_days).mean())


def trend_distance(prices: pd.Series, lookback_days: int) -> float | None:
    clean = prices.dropna()
    if len(clean) < lookback_days:
        return None
    moving_average = clean.tail(lookback_days).mean()
    if moving_average == 0 or pd.isna(moving_average):
        return None
    return float((clean.iloc[-1] / moving_average) - 1)


def max_drawdown_factor(prices: pd.Series, lookback_days: int) -> float | None:
    clean = prices.dropna().tail(lookback_days)
    if len(clean) < lookback_days:
        return None
    wealth = clean / clean.iloc[0]
    drawdown = (wealth / wealth.cummax()) - 1
    return float(drawdown.min())


def relative_momentum(prices: pd.Series, benchmark: pd.Series, lookback_days: int) -> float | None:
    aligned = pd.concat([prices.rename("stock"), benchmark.rename("benchmark")], axis=1).dropna()
    if len(aligned) <= lookback_days:
        return None
    stock_return = (aligned["stock"].iloc[-1] / aligned["stock"].iloc[-lookback_days - 1]) - 1
    benchmark_return = (aligned["benchmark"].iloc[-1] / aligned["benchmark"].iloc[-lookback_days - 1]) - 1
    return float(stock_return - benchmark_return)
