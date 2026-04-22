from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.data import demo
from app.models import BacktestRequest, BacktestResponse
from app.quant.backtest import run_backtest

app = FastAPI(title="InvestPro API", version="0.1.0")

BACKTESTS: dict[str, BacktestResponse] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "investpro-api", "version": "0.1.0"}


@app.get("/universes")
def universes() -> dict[str, list[dict]]:
    return {"universes": demo.UNIVERSES}


@app.get("/factors")
def factors() -> dict[str, list[dict]]:
    return {"factors": demo.FACTORS}


@app.get("/benchmarks")
def benchmarks() -> dict[str, list[dict]]:
    return {"benchmarks": demo.BENCHMARKS}


@app.get("/mutual-funds/search")
def mutual_fund_search(query: str | None = None) -> dict[str, list[dict]]:
    return {"results": demo.search_mutual_funds(query)}


@app.post("/backtests")
def backtests(request: BacktestRequest) -> BacktestResponse:
    try:
        result = run_backtest(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_BACKTEST_REQUEST", "message": str(exc)}) from exc
    BACKTESTS[result.id] = result
    return result


@app.get("/backtests/{backtest_id}")
def get_backtest(backtest_id: str) -> BacktestResponse:
    if backtest_id not in BACKTESTS:
        raise HTTPException(
            status_code=404,
            detail={"code": "BACKTEST_NOT_FOUND", "message": f"No backtest exists for id {backtest_id}."},
        )
    return BACKTESTS[backtest_id]
