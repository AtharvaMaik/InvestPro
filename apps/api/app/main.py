from __future__ import annotations

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from app.data import demo, live
from app.models import BacktestRequest, BacktestResponse, CsvImportRequest, TradesCsvExportRequest
from app.portfolio.csv_io import export_trades_csv, parse_holdings_csv
from app.quant.backtest import run_backtest

app = FastAPI(title="InvestPro API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKTESTS: dict[str, BacktestResponse] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "investpro-api", "version": "0.1.0"}


@app.get("/universes")
def universes() -> dict[str, list[dict]]:
    return {
        "universes": [
            {
                **demo.UNIVERSES[0],
                "name": "Indian Large Cap Universe",
                "description": "Live NSE large-cap universe for Indian equity research",
                "source": "live",
            }
        ]
    }


@app.get("/stocks")
def stocks() -> dict[str, list[dict]]:
    fundamentals = demo.fundamentals().set_index("symbol")
    return {
        "stocks": [
            {
                "symbol": symbol,
                "name": symbol.replace(".NS", ""),
                "sector": str(fundamentals.loc[symbol, "sector"]) if symbol in fundamentals.index else "Unknown",
                "source": "live",
            }
            for symbol in demo.SYMBOLS
        ]
    }


@app.get("/factors")
def factors() -> dict[str, list[dict]]:
    demo_only = {"quality_score", "value_score"}
    return {"factors": [factor for factor in demo.FACTORS if factor["id"] not in demo_only]}


@app.get("/benchmarks")
def benchmarks() -> dict[str, list[dict]]:
    return {
        "benchmarks": [
            {
                **demo.BENCHMARKS[0],
                "name": "Nifty 50",
                "source": "live",
            }
        ]
    }


@app.post("/portfolios/import-csv")
def import_portfolio_csv(request: CsvImportRequest) -> dict:
    return parse_holdings_csv(request.csvText, valid_symbols=set(demo.SYMBOLS))


@app.post("/backtests/export-trades-csv")
def export_backtest_trades_csv(request: TradesCsvExportRequest) -> Response:
    return Response(content=export_trades_csv(request.trades), media_type="text/csv")


@app.get("/mutual-funds/search")
def mutual_fund_search(query: str | None = None, source: str = "live") -> dict[str, list[dict]]:
    if source == "demo":
        return {"results": demo.search_mutual_funds(query)}
    try:
        return {"results": live.search_mutual_funds(query)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"code": "PROVIDER_FAILURE", "message": str(exc)}) from exc


@app.post("/backtests")
def backtests(request: BacktestRequest) -> BacktestResponse:
    try:
        result = run_backtest(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_BACKTEST_REQUEST", "message": str(exc)}) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail={"code": "PROVIDER_FAILURE", "message": str(exc)}) from exc
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
