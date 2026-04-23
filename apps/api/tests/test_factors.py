import pandas as pd

from app.quant.factors import composite_scores, max_drawdown_factor, relative_momentum, trend_distance, zscore_factor


def test_zscore_factor_inverts_lower_is_better():
    values = pd.Series({"A": 0.10, "B": 0.20, "C": 0.30})
    scores = zscore_factor(values, higher_is_better=False)
    assert scores["A"] > scores["C"]


def test_composite_scores_use_weights():
    factors = {
        "momentum": pd.Series({"A": 1.0, "B": 0.0}),
        "risk": pd.Series({"A": 0.0, "B": 1.0}),
    }
    scores = composite_scores(factors, {"momentum": 0.75, "risk": 0.25})
    assert scores["A"] > scores["B"]


def test_relative_momentum_subtracts_benchmark_return():
    stock = pd.Series([100, 120, 130], index=pd.date_range("2024-01-01", periods=3))
    benchmark = pd.Series([100, 105, 110], index=pd.date_range("2024-01-01", periods=3))

    assert relative_momentum(stock, benchmark, 2) == (1.3 - 1.1)


def test_trend_distance_compares_price_to_moving_average():
    prices = pd.Series([100.0] * 199 + [120.0])

    assert trend_distance(prices, 200) == 120 / 100.1 - 1


def test_max_drawdown_factor_uses_trailing_window():
    shallow = pd.Series([100, 110, 105, 112], dtype=float)
    deep = pd.Series([100, 120, 80, 90], dtype=float)

    assert max_drawdown_factor(shallow, 4) > max_drawdown_factor(deep, 4)
