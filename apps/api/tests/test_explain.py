from app.quant.explain import explain_stock


def test_explanation_uses_largest_weighted_contributors():
    holding = {
        "symbol": "TCS.NS",
        "sector": "Information Technology",
        "compositeScore": 1.1,
        "factorScores": {
            "relative_momentum_6m": 1.2,
            "roe": 0.7,
            "pe_ratio": -0.8,
            "trend_200d": 0.4,
        },
    }
    weights = {"relative_momentum_6m": 0.2, "roe": 0.15, "pe_ratio": 0.1, "trend_200d": 0.1}

    explanation = explain_stock(holding, weights)

    assert explanation["symbol"] == "TCS.NS"
    assert explanation["positives"][0]["factorId"] == "relative_momentum_6m"
    assert explanation["positives"][0]["weightedContribution"] == 0.24
    assert explanation["negatives"][0]["factorId"] == "pe_ratio"
    assert any(warning["code"] == "EXPENSIVE_VALUATION" for warning in explanation["warnings"])


def test_explanation_flags_weak_trend_and_drawdown():
    holding = {
        "symbol": "RELIANCE.NS",
        "sector": "Energy",
        "compositeScore": -0.2,
        "factorScores": {
            "trend_200d": -0.9,
            "drawdown_6m": -1.1,
            "liquidity_3m": 0.4,
        },
    }
    weights = {"trend_200d": 0.2, "drawdown_6m": 0.2, "liquidity_3m": 0.1}

    explanation = explain_stock(holding, weights)

    warning_codes = {warning["code"] for warning in explanation["warnings"]}
    assert {"WEAK_TREND", "DEEP_DRAWDOWN"}.issubset(warning_codes)
    assert explanation["headline"] == "Selected with risk flags that need review."
