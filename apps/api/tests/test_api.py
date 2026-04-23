from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metadata_endpoints():
    universes = client.get("/universes").json()["universes"]
    assert universes
    assert universes[0]["symbolCount"] >= 40
    assert universes[0]["source"] == "live"
    assert "Demo" not in universes[0]["name"]
    assert client.get("/factors").json()["factors"]
    benchmarks = client.get("/benchmarks").json()["benchmarks"]
    assert benchmarks[0]["source"] == "live"
    assert client.get("/mutual-funds/search").json()["results"][0]["source"] == "mfapi"


def test_stocks_endpoint_returns_searchable_universe():
    response = client.get("/stocks")
    assert response.status_code == 200
    stocks = response.json()["stocks"]
    assert len(stocks) >= 40
    assert {"symbol", "name", "sector", "source"}.issubset(stocks[0])
    assert any(stock["symbol"] == "RELIANCE.NS" for stock in stocks)
    assert all(stock["source"] == "live" for stock in stocks)


def test_portfolio_csv_import_and_trade_export_endpoints():
    import_response = client.post("/portfolios/import-csv", json={"csvText": "Instrument,Qty,Avg Price\nRELIANCE.NS,10,2400\n"})
    assert import_response.status_code == 200
    assert import_response.json()["holdings"][0]["symbol"] == "RELIANCE.NS"

    export_response = client.post(
        "/backtests/export-trades-csv",
        json={
            "trades": [
                {
                    "symbol": "TCS.NS",
                    "tradeAction": "buy",
                    "currentValue": 0,
                    "targetValue": 50000,
                    "tradeValue": 50000,
                    "latestPrice": 4000,
                    "estimatedShares": 12.5,
                    "reason": "New target position",
                }
            ]
        },
    )
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/csv")
    assert "TCS.NS,buy" in export_response.text


def test_default_mutual_fund_menu_has_multiple_categories():
    response = client.get("/mutual-funds/search")
    assert response.status_code == 200
    results = response.json()["results"]
    categories = {fund["category"] for fund in results}
    assert len(results) >= 8
    assert {"Flexi Cap", "Large Cap", "Small Cap", "Mid Cap", "ELSS", "Index"}.issubset(categories)


def test_live_mutual_fund_search_uses_live_provider(monkeypatch):
    from app import main

    monkeypatch.setattr(
        main.live,
        "search_mutual_funds",
        lambda query: [
            {
                "schemeCode": "122639",
                "schemeName": f"Live result for {query}",
                "fundHouse": "PPFAS Mutual Fund",
                "category": "Flexi Cap",
                "source": "mfapi",
            }
        ],
    )

    response = client.get("/mutual-funds/search?source=live&query=parag")
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["source"] == "mfapi"


def test_backtest_default_config_returns_series_and_comparisons():
    payload = {
        "universeId": "nifty50-demo",
        "customSymbols": [],
        "startDate": "2020-01-01",
        "endDate": "2024-12-31",
        "rebalanceFrequency": "monthly",
        "topN": 5,
        "transactionCostBps": 25,
        "factors": [{"id": "momentum_6m", "weight": 1.0}],
        "benchmarks": ["nifty50-demo"],
        "mutualFunds": ["ppfas-flexi-demo"],
    }
    response = client.post("/backtests", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["series"]["equityCurve"]
    assert body["comparisons"]
    assert body["holdings"]
    assert body["factorDiagnostics"]
    assert body["robustness"]


def test_backtest_supports_quarterly_score_weighting_and_fundamental_factors():
    payload = {
        "universeId": "nifty50-demo",
        "customSymbols": [],
        "startDate": "2020-01-01",
        "endDate": "2024-12-31",
        "rebalanceFrequency": "quarterly",
        "weightingMethod": "score",
        "topN": 5,
        "transactionCostBps": 25,
        "factors": [
            {"id": "quality_score", "weight": 0.5},
            {"id": "value_score", "weight": 0.5},
        ],
        "benchmarks": ["nifty50-demo"],
        "mutualFunds": ["ppfas-flexi-demo"],
    }
    response = client.post("/backtests", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["summary"]["rebalanceFrequency"] == "quarterly"
    assert body["summary"]["weightingMethod"] == "score"
    assert len(body["holdings"]) < 30
    assert all("evidence" in diagnostic for diagnostic in body["factorDiagnostics"])


def test_backtest_quant_v2_outputs_risk_fundamental_and_validation_sections():
    payload = {
        "universeId": "nifty50-demo",
        "customSymbols": [],
        "startDate": "2020-01-01",
        "endDate": "2024-12-31",
        "rebalanceFrequency": "quarterly",
        "weightingMethod": "equal",
        "topN": 15,
        "transactionCostBps": 25,
        "trendFilter": True,
        "sectorNeutral": True,
        "maxSectorWeight": 0.3,
        "factors": [
            {"id": "momentum_6m", "weight": 0.2},
            {"id": "relative_momentum_6m", "weight": 0.2},
            {"id": "drawdown_6m", "weight": 0.15},
            {"id": "trend_200d", "weight": 0.1},
            {"id": "roe", "weight": 0.15},
            {"id": "debt_to_equity", "weight": 0.1},
            {"id": "pe_ratio", "weight": 0.1},
        ],
        "benchmarks": ["nifty50-demo"],
        "mutualFunds": ["ppfas-flexi-demo", "mirae-large-demo", "motilal-midcap-demo", "hdfc-elss-demo"],
    }
    response = client.post("/backtests", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["sectorExposure"]
    assert all(item["weight"] <= 0.3001 for item in body["sectorExposure"])
    assert body["fundCategoryComparison"]
    assert {"Flexi Cap", "Large Cap", "Mid Cap", "ELSS"}.issubset({item["category"] for item in body["fundCategoryComparison"]})
    assert body["series"]["rollingReturns"]["oneYear"]
    assert body["rollingAnalysis"]["oneYearWinRate"] is not None
    assert body["walkForward"]["train"]["metrics"]["cagr"] is not None
    assert body["walkForward"]["test"]["metrics"]["cagr"] is not None
    assert body["actionList"]
    assert body["actionList"][0]["action"] in {"buy_candidate", "hold", "review", "avoid"}
    assert body["actionList"][0]["explanation"]["headline"]
    assert "factorContributions" in body["actionList"][0]["explanation"]


def test_backtest_v3_decision_layer_returns_verdict_guardrails_and_journal():
    payload = {
        "universeId": "nifty50-demo",
        "customSymbols": [],
        "startDate": "2020-01-01",
        "endDate": "2024-12-31",
        "rebalanceFrequency": "quarterly",
        "weightingMethod": "equal",
        "topN": 15,
        "transactionCostBps": 25,
        "trendFilter": True,
        "sectorNeutral": True,
        "maxSectorWeight": 0.3,
        "maxPositionWeight": 0.08,
        "minLiquidityCrore": 1,
        "maxAnnualTurnover": 2.0,
        "factors": [
            {"id": "momentum_6m", "weight": 0.2},
            {"id": "relative_momentum_6m", "weight": 0.2},
            {"id": "drawdown_6m", "weight": 0.15},
            {"id": "trend_200d", "weight": 0.1},
            {"id": "roe", "weight": 0.15},
            {"id": "debt_to_equity", "weight": 0.1},
            {"id": "pe_ratio", "weight": 0.1},
        ],
        "benchmarks": ["nifty50-demo"],
        "mutualFunds": ["ppfas-flexi-demo", "mirae-large-demo"],
    }

    response = client.post("/backtests", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["dataConfidence"]["level"] in {"high", "medium", "low"}
    assert 0 <= body["dataConfidence"]["score"] <= 1
    assert body["investability"]["checks"]
    assert body["investability"]["verdict"] in {"investable", "watch", "not_investable"}
    assert body["riskBudget"]["riskLevel"] in {"conservative", "balanced", "aggressive", "speculative"}
    assert body["researchVerdict"]["status"] in {"pass", "watch", "reject"}
    assert body["researchVerdict"]["reasons"]
    assert body["rebalanceJournal"]
    assert {"added", "removed", "retained"}.issubset(body["rebalanceJournal"][-1])


def test_backtest_v4_returns_allocation_trades_and_execution_checklist():
    payload = {
        "universeId": "nifty50-demo",
        "customSymbols": [],
        "startDate": "2020-01-01",
        "endDate": "2024-12-31",
        "rebalanceFrequency": "quarterly",
        "weightingMethod": "equal",
        "topN": 10,
        "transactionCostBps": 25,
        "trendFilter": True,
        "sectorNeutral": True,
        "maxSectorWeight": 0.35,
        "maxPositionWeight": 0.12,
        "minLiquidityCrore": 1,
        "maxAnnualTurnover": 3.0,
        "portfolioCapital": 500000,
        "currentHoldings": [
            {"symbol": "RELIANCE.NS", "value": 100000, "shares": 10, "averageCost": 1800},
            {"symbol": "TCS.NS", "shares": 5, "averageCost": 3000},
            {"symbol": "LEGACY.NS", "value": 25000},
        ],
        "factors": [
            {"id": "momentum_6m", "weight": 0.2},
            {"id": "relative_momentum_6m", "weight": 0.2},
            {"id": "drawdown_6m", "weight": 0.15},
            {"id": "trend_200d", "weight": 0.1},
            {"id": "roe", "weight": 0.15},
            {"id": "debt_to_equity", "weight": 0.1},
            {"id": "pe_ratio", "weight": 0.1},
        ],
        "benchmarks": ["nifty50-demo"],
        "mutualFunds": ["ppfas-flexi-demo"],
    }

    response = client.post("/backtests", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["allocationPlan"]
    assert all("targetValue" in row and "estimatedShares" in row for row in body["allocationPlan"])
    assert body["rebalanceTrades"]
    assert body["portfolioSummary"]["currentValue"] > 0
    assert body["portfolioSummary"]["unrealizedPnl"] is not None
    assert body["trackedHoldings"]
    assert all("drift" in holding and "driftValue" in holding for holding in body["trackedHoldings"])
    trade_actions = {trade["tradeAction"] for trade in body["rebalanceTrades"]}
    assert "exit" in trade_actions
    assert trade_actions.intersection({"buy", "add", "trim", "hold", "avoid"})
    assert body["executionChecklist"]
    assert all("status" in item and "detail" in item for item in body["executionChecklist"])


def test_factor_metadata_includes_fundamental_factors():
    response = client.get("/factors")
    assert response.status_code == 200
    factor_ids = {factor["id"] for factor in response.json()["factors"]}
    assert {"roe", "roce", "debt_to_equity", "earnings_growth", "pe_ratio", "pb_ratio"}.issubset(factor_ids)
    assert "quality_score" not in factor_ids
    assert "value_score" not in factor_ids


def test_backtest_live_source_reports_provider_failure(monkeypatch):
    from app.quant import backtest

    def fail_price_data(*_args, **_kwargs):
        raise RuntimeError("network unavailable")

    monkeypatch.setattr(backtest.live, "price_data", fail_price_data)

    payload = {
        "dataSource": "live",
        "universeId": "nifty50-demo",
        "customSymbols": [],
        "startDate": "2020-01-01",
        "endDate": "2024-12-31",
        "rebalanceFrequency": "monthly",
        "topN": 5,
        "transactionCostBps": 25,
        "factors": [{"id": "momentum_6m", "weight": 1.0}],
        "benchmarks": ["nifty50-demo"],
        "mutualFunds": ["ppfas-flexi-demo"],
    }
    response = client.post("/backtests", json=payload)
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "PROVIDER_FAILURE"


def test_missing_backtest_returns_404():
    response = client.get("/backtests/bt_missing")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "BACKTEST_NOT_FOUND"
