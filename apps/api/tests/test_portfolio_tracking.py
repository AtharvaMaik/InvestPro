from app.portfolio.tracking import attach_allocation_drift, enrich_holding, summarize_portfolio


def test_enrich_holding_uses_manual_value_first():
    holding = {"symbol": "TCS.NS", "shares": 5, "averageCost": 3000, "value": 25000}
    result = enrich_holding(holding, {"TCS.NS": 4000}, portfolio_value=100000)

    assert result["currentValue"] == 25000
    assert result["currentValueSource"] == "manual_value"
    assert result["costBasis"] == 15000
    assert result["unrealizedPnl"] == 10000
    assert round(result["unrealizedPnlPercent"], 4) == 0.6667
    assert result["currentWeight"] == 0.25


def test_enrich_holding_uses_shares_when_value_missing():
    holding = {"symbol": "TCS.NS", "shares": 5, "averageCost": 3000}
    result = enrich_holding(holding, {"TCS.NS": 4000}, portfolio_value=100000)

    assert result["currentValue"] == 20000
    assert result["currentValueSource"] == "shares"
    assert result["latestPrice"] == 4000
    assert result["costBasis"] == 15000
    assert result["unrealizedPnl"] == 5000
    assert result["currentWeight"] == 0.2


def test_enrich_holding_uses_shares_when_manual_value_is_zero_placeholder():
    holding = {"symbol": "TCS.NS", "value": 0, "shares": 5, "averageCost": 3000}
    result = enrich_holding(holding, {"TCS.NS": 4000}, portfolio_value=100000)

    assert result["currentValue"] == 20000
    assert result["currentValueSource"] == "shares"
    assert result["unrealizedPnl"] == 5000


def test_summarize_portfolio_includes_cash_and_unrealized_pnl():
    holdings = [
        {"symbol": "TCS.NS", "shares": 5, "averageCost": 3000},
        {"symbol": "RELIANCE.NS", "value": 25000, "averageCost": 2000, "shares": 10},
    ]
    summary = summarize_portfolio(holdings, {"TCS.NS": 4000, "RELIANCE.NS": 2500}, cash_value=5000)

    assert summary["cashValue"] == 5000
    assert summary["currentValue"] == 50000
    assert summary["investedValue"] == 45000
    assert summary["costBasis"] == 35000
    assert summary["unrealizedPnl"] == 10000
    assert round(summary["unrealizedPnlPercent"], 4) == 0.2857
    assert len(summary["holdings"]) == 2


def test_attach_allocation_drift_compares_current_and_target_weights():
    current = [
        {"symbol": "TCS.NS", "currentValue": 20000, "currentWeight": 0.2},
        {"symbol": "RELIANCE.NS", "currentValue": 25000, "currentWeight": 0.25},
        {"symbol": "LEGACY.NS", "currentValue": 10000, "currentWeight": 0.1},
    ]
    targets = [
        {"symbol": "TCS.NS", "targetWeight": 0.3, "targetValue": 30000},
        {"symbol": "INFY.NS", "targetWeight": 0.15, "targetValue": 15000},
    ]

    drift = attach_allocation_drift(current, targets, portfolio_capital=100000)
    by_symbol = {row["symbol"]: row for row in drift}

    assert by_symbol["TCS.NS"]["drift"] == 0.1
    assert by_symbol["TCS.NS"]["driftValue"] == 10000
    assert by_symbol["INFY.NS"]["currentWeight"] == 0
    assert by_symbol["INFY.NS"]["drift"] == 0.15
    assert by_symbol["LEGACY.NS"]["targetWeight"] == 0
    assert by_symbol["LEGACY.NS"]["drift"] == -0.1
