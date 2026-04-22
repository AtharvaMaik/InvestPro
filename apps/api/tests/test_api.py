from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metadata_endpoints():
    assert client.get("/universes").json()["universes"]
    assert client.get("/factors").json()["factors"]
    assert client.get("/benchmarks").json()["benchmarks"]
    assert client.get("/mutual-funds/search").json()["results"]


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


def test_backtest_live_source_falls_back_to_demo_when_provider_fails(monkeypatch):
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
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert any(warning["code"] == "LIVE_DATA_FALLBACK" for warning in body["warnings"])


def test_missing_backtest_returns_404():
    response = client.get("/backtests/bt_missing")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "BACKTEST_NOT_FOUND"
