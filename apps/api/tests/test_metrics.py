import math

import pandas as pd

from app.quant.metrics import calculate_metrics, drawdown_series


def test_drawdown_series_tracks_peak_to_trough():
    wealth = pd.Series([1.0, 1.2, 0.9, 1.5])
    result = drawdown_series(wealth)
    assert result.round(4).tolist() == [0.0, 0.0, -0.25, 0.0]


def test_calculate_metrics_for_simple_daily_returns():
    returns = pd.Series([0.01, -0.02, 0.03, 0.01])
    metrics = calculate_metrics(returns, periods_per_year=252)
    assert metrics.total_return > 0
    assert metrics.volatility > 0
    assert metrics.max_drawdown < 0
    assert metrics.sharpe is not None
    assert math.isfinite(metrics.sharpe)
