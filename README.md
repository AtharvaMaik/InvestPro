# InvestPro

InvestPro is an Indian equity factor research lab for active stock pickers. It lets users configure a long-only factor strategy, backtest it against seeded Indian equity demo data, and compare the result with a benchmark and mutual fund.

The current vertical slice includes:

- FastAPI quant backend.
- Deterministic demo market data.
- Factor ranking for momentum, volatility, and liquidity.
- Monthly long-only equal-weight backtesting.
- Performance, drawdown, turnover, and comparison metrics.
- Next.js dashboard with strategy controls, charts, tables, warnings, and responsive styling.

## Repository Layout

```text
apps/
  api/   FastAPI backend and quant engine
  web/   Next.js frontend dashboard
docs/
  superpowers/
    specs/  Product design spec
    plans/  Implementation plan
project_details.md  Math, API, UI, and flow contract
```

## Run The Backend

```powershell
cd apps/api
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

## Run Backend Tests

```powershell
cd apps/api
python -m pytest -v
```

## Run The Frontend

```powershell
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`.

The frontend expects the API at `http://localhost:8000`. To use another API URL:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev
```

## Build The Frontend

```powershell
cd apps/web
npm run build
```

## Demo Flow

1. Start the backend on port 8000.
2. Start the frontend on port 3000.
3. Open the InvestPro workspace.
4. Keep the default universe, factors, benchmark, and mutual fund.
5. Click `Run backtest`.
6. Review the equity curve, drawdown, metrics, comparison table, latest holdings, and demo-data warning.

## Current Limitations

- Uses seeded demo data, not live NSE or AMFI data.
- Price-based factors only.
- Monthly rebalance only.
- Equal-weight portfolio only.
- No authentication or saved user accounts yet.
- No personalized investment advice.
