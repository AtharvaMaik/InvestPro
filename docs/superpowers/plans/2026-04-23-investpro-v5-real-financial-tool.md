# InvestPro V5 Real Financial Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build V5 into a more realistic financial tool by adding portfolio tracking, stock-level explanations, CSV import/export, data freshness/caching, and production database/auth foundations.

**Architecture:** Keep the existing FastAPI + Next.js multi-service deployment. Add a persistent data layer behind the API, introduce authenticated saved resources, make portfolio holdings richer, and expose explainability/data-quality metadata through the existing backtest response contract. Ship in slices so the app remains usable after each phase.

**Tech Stack:** FastAPI, Pydantic, pandas, yfinance, MFAPI, Next.js App Router, React, TypeScript, Vercel Services, PostgreSQL via Neon or Vercel Postgres-compatible `DATABASE_URL`, SQLAlchemy, Alembic, Clerk or Vercel Marketplace auth with JWT validation.

---

## Scope

V5 includes the user-selected improvements:

1. **Portfolio tracking**: average cost, current value, P&L, allocation drift, cash, richer holdings.
2. **Better stock explanations**: per-stock factor drivers, positives, negatives, warnings, entry/exit reasons.
3. **CSV import/export**: import holdings from a broker-style CSV and export rebalance/order sheets.
4. **Data freshness and caching**: cache prices/fundamentals/NAVs, expose timestamps and confidence.
5. **Production database + auth**: user accounts, saved portfolios, saved runs, persisted settings.

Out of scope for this V5 slice:

- Broker order placement.
- Tax optimization engine.
- Payment/subscription system.
- Full point-in-time fundamentals vendor integration.
- Mobile native app.

## Deployment Target

Production remains:

```text
Frontend: https://investpro-seven.vercel.app
Backend:  https://investpro-seven.vercel.app/api
```

Local development remains:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000
```

## File Map

### Backend Files

- Modify `apps/api/pyproject.toml`: add database/auth dependencies.
- Create `apps/api/app/core/config.py`: central environment settings.
- Create `apps/api/app/core/auth.py`: optional JWT parsing and required-user dependency.
- Create `apps/api/app/db/session.py`: SQLAlchemy engine/session factory.
- Create `apps/api/app/db/models.py`: database tables.
- Create `apps/api/app/db/repositories.py`: persistence helpers.
- Create `apps/api/app/db/migrations/`: Alembic migration files if Alembic is used.
- Modify `apps/api/app/models.py`: add portfolio tracking, CSV, explanation, freshness models.
- Modify `apps/api/app/main.py`: add portfolio/run/data endpoints.
- Modify `apps/api/app/data/live.py`: add provider cache read/write hooks.
- Create `apps/api/app/data/cache.py`: price/fundamental/NAV cache logic.
- Create `apps/api/app/portfolio/tracking.py`: P&L, current value, allocation drift.
- Create `apps/api/app/portfolio/csv_io.py`: CSV parser/export generator.
- Create `apps/api/app/quant/explain.py`: stock explanation engine.
- Modify `apps/api/app/quant/backtest.py`: attach explanations, freshness, richer action output.
- Modify `apps/api/tests/test_api.py`: API tests for new endpoints.
- Create `apps/api/tests/test_portfolio_tracking.py`: P&L/allocation tests.
- Create `apps/api/tests/test_csv_io.py`: CSV import/export tests.
- Create `apps/api/tests/test_explain.py`: explanation tests.
- Create `apps/api/tests/test_cache.py`: data cache tests.

### Frontend Files

- Modify `apps/web/package.json`: add auth and CSV helper dependencies only if selected.
- Modify `apps/web/src/lib/api.ts`: add typed API methods.
- Create `apps/web/src/lib/csv.ts`: client CSV helpers if needed.
- Modify `apps/web/src/app/page.tsx`: load saved portfolios/runs when signed in.
- Create `apps/web/src/app/account/page.tsx`: saved portfolios/runs page.
- Modify `apps/web/src/components/strategy-builder.tsx`: richer portfolio entry and import controls.
- Modify `apps/web/src/components/results-dashboard.tsx`: explanations, freshness, export buttons.
- Create `apps/web/src/components/portfolio-tracker.tsx`: P&L and drift panel.
- Create `apps/web/src/components/stock-explanation.tsx`: per-stock explanation card.
- Create `apps/web/src/components/data-freshness.tsx`: provider/freshness badges.
- Create `apps/web/src/components/csv-importer.tsx`: import review UI.
- Modify `apps/web/src/app/globals.css`: responsive styles.

### Docs/Config Files

- Modify `README.md`: V5 usage and deployment env vars.
- Modify `project_details.md`: exact V5 math/API/UI flows.
- Create `.env.example`: required local environment variables.
- Modify `vercel.json` only if service env or routing changes are required.

---

## Data Model

### `users`

Stored only if the chosen auth provider does not own the full profile.

```text
id: uuid primary key
auth_subject: text unique not null
email: text
created_at: timestamp
updated_at: timestamp
```

### `portfolios`

```text
id: uuid primary key
user_id: uuid not null
name: text not null
base_currency: text not null default 'INR'
cash_value: numeric not null default 0
created_at: timestamp
updated_at: timestamp
```

### `portfolio_holdings`

```text
id: uuid primary key
portfolio_id: uuid not null
symbol: text not null
shares: numeric
average_cost: numeric
manual_value: numeric
notes: text
created_at: timestamp
updated_at: timestamp
```

Rules:

- `manual_value` can be used when the user knows current rupee exposure but not share count.
- If `manual_value` exists, it is the current exposure source.
- If `manual_value` is missing and `shares` exists, use `shares * latest_price`.
- `average_cost` enables unrealized P&L.

### `saved_runs`

```text
id: uuid primary key
user_id: uuid not null
portfolio_id: uuid nullable
name: text not null
request_json: jsonb not null
response_json: jsonb not null
created_at: timestamp
```

### `market_price_cache`

```text
symbol: text not null
date: date not null
open: numeric
high: numeric
low: numeric
close: numeric
adjusted_close: numeric
volume: numeric
provider: text not null
fetched_at: timestamp not null
primary key(symbol, date, provider)
```

### `fundamental_cache`

```text
symbol: text primary key
sector: text
roe: numeric
roce: numeric
debt_to_equity: numeric
earnings_growth: numeric
pe_ratio: numeric
pb_ratio: numeric
provider: text not null
fetched_at: timestamp not null
raw_json: jsonb
```

### `mutual_fund_nav_cache`

```text
scheme_code: text not null
date: date not null
nav: numeric not null
provider: text not null
fetched_at: timestamp not null
primary key(scheme_code, date, provider)
```

---

## API Contract Additions

### Auth

Authenticated endpoints require:

```http
Authorization: Bearer <jwt>
```

Unauthenticated users can still run one-off research using the existing `/backtests` endpoint. Saved portfolios and saved runs require auth.

### `GET /me`

Purpose: return the current authenticated user profile.

Response:

```json
{
  "id": "user_123",
  "email": "person@example.com"
}
```

### `GET /portfolios`

Purpose: list saved portfolios for the current user.

Response:

```json
{
  "portfolios": [
    {
      "id": "pf_1",
      "name": "Long term portfolio",
      "cashValue": 25000,
      "holdingCount": 8,
      "currentValue": 525000,
      "unrealizedPnl": 42000,
      "unrealizedPnlPercent": 0.087
    }
  ]
}
```

### `POST /portfolios`

Request:

```json
{
  "name": "Long term portfolio",
  "cashValue": 25000,
  "holdings": [
    {
      "symbol": "RELIANCE.NS",
      "shares": 10,
      "averageCost": 2400,
      "notes": "Core energy position"
    }
  ]
}
```

### `PUT /portfolios/{portfolio_id}`

Same body as `POST /portfolios`. Replaces portfolio metadata and holdings.

### `DELETE /portfolios/{portfolio_id}`

Deletes the portfolio and its holdings.

### `POST /portfolios/import-csv`

Purpose: parse a CSV before saving it.

Request:

```json
{
  "csvText": "symbol,shares,average_cost\nRELIANCE.NS,10,2400\n"
}
```

Response:

```json
{
  "holdings": [
    {
      "symbol": "RELIANCE.NS",
      "shares": 10,
      "averageCost": 2400,
      "status": "valid",
      "message": "Matched supported stock universe"
    }
  ],
  "warnings": []
}
```

### `GET /portfolios/{portfolio_id}/export-csv`

Returns `text/csv` with current portfolio holdings.

### `GET /runs`

Lists saved backtest runs.

### `POST /runs`

Saves a request/response pair after a successful backtest.

### `GET /runs/{run_id}`

Returns a saved run.

### `GET /data/freshness`

Purpose: show data freshness by provider and dataset.

Response:

```json
{
  "prices": {
    "provider": "yfinance",
    "latestFetchedAt": "2026-04-23T14:50:00Z",
    "latestMarketDate": "2026-04-22",
    "symbolsCovered": 51,
    "staleSymbols": []
  },
  "fundamentals": {
    "provider": "yfinance",
    "latestFetchedAt": "2026-04-23T14:52:00Z",
    "symbolsCovered": 51,
    "staleSymbols": ["ONGC.NS"]
  },
  "mutualFunds": {
    "provider": "mfapi",
    "latestFetchedAt": "2026-04-23T14:55:00Z",
    "schemesCovered": 10
  }
}
```

---

## Math Additions

### Current Holding Value

```text
If manual_value_i exists:
  CurrentValue_i = manual_value_i
Else:
  CurrentValue_i = shares_i * latest_price_i
```

### Cost Basis

```text
CostBasis_i = shares_i * average_cost_i
```

Unavailable if either `shares_i` or `average_cost_i` is missing.

### Unrealized P&L

```text
UnrealizedPnl_i = CurrentValue_i - CostBasis_i
UnrealizedPnlPercent_i = UnrealizedPnl_i / CostBasis_i
```

Unavailable if cost basis is unavailable.

### Portfolio Current Value

```text
PortfolioCurrentValue = CashValue + sum(CurrentValue_i)
```

### Current Weight

```text
CurrentWeight_i = CurrentValue_i / PortfolioCurrentValue
```

### Allocation Drift

```text
Drift_i = TargetWeight_i - CurrentWeight_i
```

Positive drift means the model wants more exposure. Negative drift means the position is overweight relative to target.

### Trade Value

```text
TradeValue_i = TargetValue_i - CurrentValue_i
TargetValue_i = TargetWeight_i * PortfolioCapital
```

### Estimated Trade Shares

```text
EstimatedTradeShares_i = TradeValue_i / LatestPrice_i
```

Round display values to two decimals. Exported order sheets should include both decimal shares and whole-share rounded suggestions.

---

## Stock Explanation Model

Each selected or reviewed stock should expose:

```json
{
  "symbol": "TCS.NS",
  "headline": "Selected for strong relative momentum and quality",
  "positives": [
    "6M relative momentum is in the top quartile",
    "ROCE is stronger than most eligible stocks"
  ],
  "negatives": [
    "P/E is above the universe median"
  ],
  "factorContributions": [
    {
      "factorId": "relative_momentum_6m",
      "rawValue": 0.14,
      "score": 1.22,
      "weight": 0.2,
      "weightedContribution": 0.244,
      "direction": "positive"
    }
  ],
  "warnings": [
    "Valuation is not cheap"
  ]
}
```

Explanation rules:

- Top positives are the three largest positive weighted contributions.
- Top negatives are the three lowest or weakest contributions.
- Valuation warning triggers when `pe_ratio` or `pb_ratio` score is below `-0.75`.
- Drawdown warning triggers when `drawdown_6m` score is below `-0.75`.
- Trend warning triggers when `trend_200d` raw value is below `0`.
- Missing data warning triggers when any active factor is unavailable and filled/ignored.

---

## Phase Plan

### Phase 1: Portfolio Tracking Without Auth

Goal: make portfolio tracking useful before adding accounts.

**Files:**

- Modify `apps/api/app/models.py`
- Create `apps/api/app/portfolio/tracking.py`
- Modify `apps/api/app/quant/backtest.py`
- Create `apps/api/tests/test_portfolio_tracking.py`
- Modify `apps/web/src/lib/api.ts`
- Create `apps/web/src/components/portfolio-tracker.tsx`
- Modify `apps/web/src/components/strategy-builder.tsx`
- Modify `apps/web/src/components/results-dashboard.tsx`
- Modify `apps/web/src/app/globals.css`

- [ ] Write backend tests for current value, cost basis, P&L, current weight, and drift.

Expected test cases:

```python
def test_holding_value_uses_manual_value_first():
    holding = {"symbol": "TCS.NS", "shares": 5, "averageCost": 3000, "value": 25000}
    prices = {"TCS.NS": 4000}
    result = enrich_holding(holding, prices, portfolio_value=100000)
    assert result["currentValue"] == 25000
    assert result["costBasis"] == 15000
    assert result["unrealizedPnl"] == 10000

def test_holding_value_uses_shares_when_value_missing():
    holding = {"symbol": "TCS.NS", "shares": 5, "averageCost": 3000}
    prices = {"TCS.NS": 4000}
    result = enrich_holding(holding, prices, portfolio_value=100000)
    assert result["currentValue"] == 20000
    assert result["currentWeight"] == 0.2
```

- [ ] Run failing tests.

```powershell
python -m pytest apps/api/tests/test_portfolio_tracking.py -v
```

Expected: failures because `enrich_holding` does not exist.

- [ ] Implement `apps/api/app/portfolio/tracking.py`.

Required functions:

```python
def enrich_holding(holding: dict, latest_prices: dict[str, float | None], portfolio_value: float) -> dict:
    ...

def summarize_portfolio(holdings: list[dict], latest_prices: dict[str, float | None], cash_value: float) -> dict:
    ...

def attach_allocation_drift(current: list[dict], targets: list[dict], portfolio_capital: float) -> list[dict]:
    ...
```

- [ ] Extend Pydantic models.

Add optional fields to `CurrentHolding`:

```python
averageCost: float | None = Field(default=None, ge=0)
notes: str | None = None
```

Add response fields:

```python
portfolioSummary: dict
trackedHoldings: list[dict]
```

- [ ] Attach portfolio tracking output to the backtest response.

Use latest available prices from the backtest price panel.

- [ ] Add frontend types for `portfolioSummary` and `trackedHoldings`.

- [ ] Add UI fields for average cost and notes.

Holding row fields:

```text
Stock | Value Rs | Shares | Avg cost | Remove
```

Notes can be a compact optional text input below the row on desktop/mobile.

- [ ] Add `PortfolioTracker` panel.

Panel shows:

- Total current value.
- Cash.
- Unrealized P&L.
- Unrealized P&L %.
- Top overweight positions.
- Top underweight positions.
- Rows for symbol, current value, cost basis, P&L, current weight, target weight, drift.

- [ ] Run verification.

```powershell
python -m pytest -v
cd apps/web
npm run build
```

- [ ] Commit.

```powershell
git add apps/api apps/web
git commit -m "feat: add portfolio tracking metrics"
```

### Phase 2: Stock-Level Explanation Engine

Goal: make every action explain itself.

**Files:**

- Create `apps/api/app/quant/explain.py`
- Modify `apps/api/app/quant/backtest.py`
- Modify `apps/api/app/models.py`
- Create `apps/api/tests/test_explain.py`
- Create `apps/web/src/components/stock-explanation.tsx`
- Modify `apps/web/src/components/results-dashboard.tsx`
- Modify `apps/web/src/app/globals.css`

- [ ] Write explanation unit tests.

Expected test cases:

```python
def test_explanation_uses_largest_weighted_contributors():
    row = {
        "symbol": "TCS.NS",
        "factorScores": {"relative_momentum_6m": 1.2, "pe_ratio": -0.8, "roe": 0.7},
        "factorRawValues": {"relative_momentum_6m": 0.14, "pe_ratio": 35, "roe": 0.22},
    }
    weights = {"relative_momentum_6m": 0.2, "pe_ratio": 0.1, "roe": 0.15}
    explanation = explain_stock(row, weights)
    assert explanation["positives"][0]["factorId"] == "relative_momentum_6m"
    assert any(warning["code"] == "EXPENSIVE_VALUATION" for warning in explanation["warnings"])
```

- [ ] Run failing tests.

```powershell
python -m pytest apps/api/tests/test_explain.py -v
```

- [ ] Implement `explain_stock` and `explain_rebalance_action`.

Required outputs:

- `headline`
- `positives`
- `negatives`
- `factorContributions`
- `warnings`

- [ ] Attach explanation objects to `actionList`, `allocationPlan`, and `rebalanceJournal`.

- [ ] Add `StockExplanation` UI component.

UI behavior:

- Each action card has an expandable "Why?" row.
- Show top positives and top negatives.
- Show warning pills for valuation, drawdown, trend, missing data.
- Keep text short and beginner-friendly.

- [ ] Run verification.

```powershell
python -m pytest -v
cd apps/web
npm run build
```

- [ ] Commit.

```powershell
git add apps/api apps/web
git commit -m "feat: explain stock actions"
```

### Phase 3: CSV Import And Export

Goal: let users move data in and out of the tool.

**Files:**

- Create `apps/api/app/portfolio/csv_io.py`
- Modify `apps/api/app/main.py`
- Create `apps/api/tests/test_csv_io.py`
- Modify `apps/web/src/lib/api.ts`
- Create `apps/web/src/components/csv-importer.tsx`
- Modify `apps/web/src/components/results-dashboard.tsx`
- Modify `apps/web/src/components/strategy-builder.tsx`
- Modify `apps/web/src/app/globals.css`

- [ ] Define supported import headers.

Accepted aliases:

```text
symbol: symbol, ticker, instrument, stock
shares: shares, quantity, qty
average_cost: average_cost, avg_cost, average_price, avg_price
value: value, current_value, market_value
notes: notes, note
```

- [ ] Write parser tests.

Expected test cases:

```python
def test_parse_broker_csv_with_alias_headers():
    csv_text = "Instrument,Qty,Avg Price\nRELIANCE.NS,10,2400\n"
    result = parse_holdings_csv(csv_text, valid_symbols={"RELIANCE.NS"})
    assert result["holdings"][0]["symbol"] == "RELIANCE.NS"
    assert result["holdings"][0]["shares"] == 10
    assert result["holdings"][0]["averageCost"] == 2400
```

- [ ] Run failing parser tests.

```powershell
python -m pytest apps/api/tests/test_csv_io.py -v
```

- [ ] Implement parser and validation.

Validation rules:

- Empty rows are ignored.
- Symbols are uppercased.
- Missing symbol is an error row.
- Unknown symbol is a warning row, not a hard failure.
- Negative shares/value/average cost is an error row.

- [ ] Add `POST /portfolios/import-csv`.

It should not require auth in Phase 3 because users can import into the current unsaved builder.

- [ ] Add CSV export for rebalance trades.

Endpoint:

```text
POST /backtests/export-trades-csv
```

Request accepts `rebalanceTrades` from the latest result. Response is `text/csv`.

- [ ] Add frontend `CsvImporter`.

UI:

- Upload/drop CSV.
- Show parsed rows before applying.
- Show warning rows.
- Apply valid rows to `currentHoldings`.

- [ ] Add export buttons.

Buttons:

- Export current holdings CSV.
- Export rebalance trades CSV.

- [ ] Run verification.

```powershell
python -m pytest -v
cd apps/web
npm run build
```

- [ ] Commit.

```powershell
git add apps/api apps/web
git commit -m "feat: add portfolio csv import export"
```

### Phase 4: Data Freshness And Caching

Goal: make live data more trustworthy and less fragile.

**Files:**

- Create `apps/api/app/data/cache.py`
- Modify `apps/api/app/data/live.py`
- Modify `apps/api/app/quant/backtest.py`
- Modify `apps/api/app/main.py`
- Modify `apps/api/app/models.py`
- Create `apps/api/tests/test_cache.py`
- Create `apps/web/src/components/data-freshness.tsx`
- Modify `apps/web/src/components/results-dashboard.tsx`
- Modify `apps/web/src/lib/api.ts`
- Modify `apps/web/src/app/globals.css`

- [ ] Add cache repository interface.

Functions:

```python
def get_cached_prices(symbols: list[str], start: date, end: date) -> pd.DataFrame:
    ...

def save_price_rows(rows: pd.DataFrame, provider: str) -> None:
    ...

def get_cached_fundamentals(symbols: list[str], max_age_hours: int) -> pd.DataFrame:
    ...

def save_fundamentals(rows: pd.DataFrame, provider: str) -> None:
    ...

def data_freshness_summary() -> dict:
    ...
```

- [ ] Write tests using in-memory SQLite or repository fakes.

Expected cases:

- Fresh cache avoids provider call.
- Stale cache triggers provider call.
- Partial cache fetches missing symbols.
- Freshness summary reports stale symbols.

- [ ] Run failing tests.

```powershell
python -m pytest apps/api/tests/test_cache.py -v
```

- [ ] Implement cache logic.

Rules:

- Prices are keyed by symbol/date/provider.
- Fundamentals are keyed by symbol/provider.
- NAVs are keyed by scheme/date/provider.
- Price cache is acceptable if requested date range coverage is at least 95%.
- Fundamentals are stale after 72 hours by default.
- NAV cache is stale after 24 hours by default.

- [ ] Add `/data/freshness`.

- [ ] Add data freshness to backtest response.

Existing `dataConfidence` should include:

```json
{
  "priceFetchedAt": "...",
  "fundamentalsFetchedAt": "...",
  "mutualFundFetchedAt": "...",
  "staleSymbols": []
}
```

- [ ] Add frontend freshness badges.

Display:

- Prices fresh/stale.
- Fundamentals fresh/stale.
- Mutual funds fresh/stale.
- Missing symbols.

- [ ] Run verification.

```powershell
python -m pytest -v
cd apps/web
npm run build
```

- [ ] Commit.

```powershell
git add apps/api apps/web
git commit -m "feat: add live data caching and freshness"
```

### Phase 5: Production Database Foundation

Goal: add persistent storage without requiring auth UI yet.

**Files:**

- Modify `apps/api/pyproject.toml`
- Create `apps/api/app/core/config.py`
- Create `apps/api/app/db/session.py`
- Create `apps/api/app/db/models.py`
- Create `apps/api/app/db/repositories.py`
- Modify `apps/api/app/main.py`
- Create `.env.example`
- Modify `README.md`
- Modify `project_details.md`
- Create `apps/api/tests/test_repositories.py`

- [ ] Add dependencies.

Recommended:

```toml
"sqlalchemy>=2.0.0",
"psycopg[binary]>=3.2.0",
"alembic>=1.13.0"
```

- [ ] Add configuration.

Environment variables:

```text
DATABASE_URL=
AUTH_JWKS_URL=
AUTH_ISSUER=
AUTH_AUDIENCE=
```

- [ ] Add database session helper.

Behavior:

- If `DATABASE_URL` is missing, saved-resource endpoints return `503 DATABASE_NOT_CONFIGURED`.
- Backtests still work without DB.

- [ ] Add ORM models for users, portfolios, holdings, saved runs, and cache tables.

- [ ] Write repository tests.

Use SQLite for tests if PostgreSQL is not available.

- [ ] Add startup table creation only for development/tests.

Production should use migrations, not automatic destructive table changes.

- [ ] Run verification.

```powershell
python -m pytest -v
cd apps/web
npm run build
```

- [ ] Commit.

```powershell
git add apps/api README.md project_details.md .env.example
git commit -m "feat: add database foundation"
```

### Phase 6: Auth And Saved Portfolios/Runs

Goal: make InvestPro something a user can return to.

**Files:**

- Modify `apps/api/app/core/auth.py`
- Modify `apps/api/app/main.py`
- Modify `apps/api/app/db/repositories.py`
- Modify `apps/web/package.json`
- Modify `apps/web/src/app/layout.tsx`
- Modify `apps/web/src/app/page.tsx`
- Create `apps/web/src/app/account/page.tsx`
- Create `apps/web/src/components/auth-buttons.tsx`
- Create `apps/web/src/components/saved-portfolios.tsx`
- Modify `apps/web/src/lib/api.ts`
- Create `apps/api/tests/test_auth_optional.py`
- Create `apps/api/tests/test_saved_resources.py`

- [ ] Choose auth provider.

Recommendation: Clerk, because it is fast to add to Next.js and provides JWTs that FastAPI can verify.

- [ ] Add frontend auth provider.

Required env vars:

```text
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
```

- [ ] Add FastAPI JWT verification.

Behavior:

- Public endpoints remain public.
- Saved-resource endpoints require auth.
- Invalid/missing token returns `401`.

- [ ] Add portfolio endpoints.

Endpoints:

```text
GET /portfolios
POST /portfolios
PUT /portfolios/{portfolio_id}
DELETE /portfolios/{portfolio_id}
```

- [ ] Add saved run endpoints.

Endpoints:

```text
GET /runs
POST /runs
GET /runs/{run_id}
DELETE /runs/{run_id}
```

- [ ] Add frontend account page.

Page sections:

- Saved portfolios.
- Saved runs.
- Last run date.
- Load into builder.
- Delete saved resource.

- [ ] Add save buttons to workspace.

Buttons:

- Save current portfolio.
- Save latest backtest run.
- Load saved portfolio into current holdings.

- [ ] Run verification.

```powershell
python -m pytest -v
cd apps/web
npm run build
```

- [ ] Commit.

```powershell
git add apps/api apps/web README.md project_details.md
git commit -m "feat: add auth and saved portfolios"
```

### Phase 7: V5 Polish, Docs, And Deployment

Goal: ship V5 cleanly.

**Files:**

- Modify `README.md`
- Modify `project_details.md`
- Modify `apps/web/src/app/globals.css`
- Modify `apps/web/src/components/results-dashboard.tsx`
- Modify `apps/web/src/components/strategy-builder.tsx`

- [ ] Add V5 README section.

Must explain:

- How to import holdings.
- How to read P&L.
- How to read drift.
- How to read stock explanations.
- How to understand freshness badges.
- How saved portfolios work.

- [ ] Update `project_details.md`.

Must include:

- Portfolio tracking math.
- CSV import/export API.
- Auth flows.
- Database schema.
- Data freshness semantics.

- [ ] Run full verification locally.

```powershell
python -m pytest -v
cd apps/web
npm run build
```

- [ ] Deploy to production.

```powershell
npx vercel deploy --prod --yes --logs
```

- [ ] Verify production.

Commands:

```powershell
Invoke-WebRequest -UseBasicParsing https://investpro-seven.vercel.app
Invoke-WebRequest -UseBasicParsing https://investpro-seven.vercel.app/api/health
Invoke-WebRequest -UseBasicParsing https://investpro-seven.vercel.app/api/stocks
Invoke-WebRequest -UseBasicParsing https://investpro-seven.vercel.app/api/data/freshness
```

- [ ] Run one production backtest.

Use a small live request first:

```json
{
  "dataSource": "live",
  "universeId": "nifty50-demo",
  "customSymbols": [],
  "startDate": "2023-01-01",
  "endDate": "2024-12-31",
  "rebalanceFrequency": "quarterly",
  "weightingMethod": "equal",
  "topN": 5,
  "transactionCostBps": 25,
  "trendFilter": true,
  "sectorNeutral": true,
  "maxSectorWeight": 0.4,
  "maxPositionWeight": 0.2,
  "minLiquidityCrore": 1,
  "maxAnnualTurnover": 3,
  "portfolioCapital": 500000,
  "currentHoldings": [],
  "factors": [
    { "id": "momentum_6m", "weight": 0.5 },
    { "id": "drawdown_6m", "weight": 0.2 },
    { "id": "trend_200d", "weight": 0.3 }
  ],
  "benchmarks": ["nifty50-demo"],
  "mutualFunds": ["122639"]
}
```

- [ ] Commit deployment docs.

```powershell
git add README.md project_details.md
git commit -m "docs: document v5 financial workflow"
git push origin main
```

---

## Recommended Execution Order

1. Phase 1: Portfolio tracking.
2. Phase 2: Stock explanations.
3. Phase 3: CSV import/export.
4. Phase 4: Data freshness and caching.
5. Phase 5: Database foundation.
6. Phase 6: Auth and saved resources.
7. Phase 7: Polish and production deploy.

Reasoning:

- Portfolio tracking, explanations, and CSV improve the product immediately without needing accounts.
- Caching makes live data more reliable before persisted user workflows depend on it.
- Database/auth comes after the core objects are stable.
- Final deployment happens after all environment variables and persistence behavior are known.

## Main Risks

### Provider Latency

Live `yfinance` fundamentals can be slow. Cache fundamentals aggressively and surface stale data honestly.

### Serverless Timeouts

Large live backtests can exceed serverless runtime. Keep top universe constrained, cache provider data, and later move long runs to background jobs.

### Auth Complexity

Auth can slow development if added too early. That is why V5 should build useful unauthenticated functionality first.

### Financial Liability

UI copy must keep saying "research" and "not investment advice." Avoid wording like "you should buy."

## Definition Of Done

V5 is complete when:

- A beginner can import or enter holdings.
- The app shows current value, cost basis, P&L, and allocation drift.
- Every buy/add/trim/hold/exit action has a clear explanation.
- Holdings and rebalance trades can be imported/exported as CSV.
- Results show data freshness and missing/stale data warnings.
- Authenticated users can save and reload portfolios and runs.
- The deployed app works end-to-end on Vercel.
- `python -m pytest -v` passes.
- `npm run build` passes.
