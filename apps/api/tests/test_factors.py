import pandas as pd

from app.quant.factors import composite_scores, zscore_factor


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
