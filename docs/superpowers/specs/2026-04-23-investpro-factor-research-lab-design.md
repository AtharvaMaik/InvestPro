# InvestPro Factor Research Lab Design

Date: 2026-04-23

## Purpose

InvestPro will be a professional-grade Indian equity research platform for active stock pickers. The product will help an investor test whether a factor-based stock selection strategy would have worked historically, compare it against Indian indices and mutual funds, and understand the tradeoffs in return, risk, drawdown, turnover, and effort.

The first major product direction is a Factor Research Lab, not a simple stock screener. The central question is:

> If I ranked Indian stocks using this combination of factors in the past, what would have happened?

InvestPro should avoid giving direct buy or sell advice. It should present statistically interesting strategies, portfolio histories, and comparison evidence so users can make better research decisions.

## Target User

The primary user is an active Indian stock picker who already understands basic investing and wants more disciplined research. They may compare self-directed stock picking with mutual funds, index funds, or existing portfolios.

The app should be useful without requiring professional quant knowledge, but it should still expose enough detail to be credible for technically minded users.

## Product Scope

### V1

- Build a full-stack web app with a frontend dashboard and Python quant backend.
- Let users define a long-only Indian equity factor strategy.
- Support a configurable stock universe, factor selection, factor weights, top-N holding count, monthly rebalance frequency, and transaction cost assumption.
- Backtest the strategy historically.
- Compare the strategy against Indian equity indices and selected mutual funds.
- Show risk-adjusted metrics, drawdowns, rolling returns, turnover, and historical holdings.
- Cache fetched market and mutual fund data locally.

### Later Versions

- Add fundamentals-based factors once a reliable source is integrated.
- Add saved strategies and watchlists.
- Add portfolio analysis for user holdings.
- Add fund alternative finder based on similar style exposure.
- Add scheduled data refreshes.
- Add auth, cloud database, and deployment.

## Non-Goals For V1

- No intraday trading.
- No options, futures, leverage, shorting, or margin.
- No automated trading.
- No personalized financial advice.
- No promise that backtested performance predicts future returns.
- No complex tax engine beyond clearly labeled assumptions.

## Recommended Stack

### Frontend

- Next.js with TypeScript.
- Dashboard-first interface.
- Recharts or another React charting library for equity curves, drawdowns, rolling returns, and heatmaps.
- Component structure organized around strategy building, results, comparisons, and diagnostics.

### Backend

- Python FastAPI service.
- Pandas and NumPy for data transforms, factor calculations, and backtests.
- Pydantic models for request and response contracts.
- A clean quant module separated from API routes so the factor engine can be tested independently.

### Data Store

- SQLite or DuckDB for local cache and reproducible development.
- Cached tables for adjusted stock prices, index prices, mutual fund NAVs, strategy runs, and strategy configs.
- A provider abstraction for all external data sources.

## System Architecture

The app will use a split frontend/backend architecture:

1. The user configures a strategy in the Next.js frontend.
2. The frontend sends the strategy configuration to the FastAPI backend.
3. The backend resolves the universe, loads cached data, fetches missing data through providers, and validates data quality.
4. The factor engine calculates factor values at each rebalance date.
5. The ranking engine normalizes factor values, applies weights, and selects top-ranked stocks.
6. The backtest engine simulates monthly portfolio rebalancing with transaction costs.
7. The metrics engine calculates performance, drawdown, turnover, rolling returns, and risk ratios.
8. The comparison engine aligns the strategy return series with index and mutual fund NAV return series.
9. The API returns structured results for charts, tables, diagnostics, and summary cards.

## Data Sources

### Stocks And Indices

V1 should use a pluggable market data adapter. Indian equity price data can be sourced from Yahoo Finance-compatible symbols, NSE-derived files, or another provider, but the rest of the system should not depend directly on one source.

The data adapter must normalize output into a stable internal schema:

- symbol
- date
- open
- high
- low
- close
- adjusted close, when available
- volume
- source

The system should track missing dates, stale symbols, and insufficient history. A stock should be excluded from a rebalance if it lacks enough data for the selected factors.

### Mutual Funds

Mutual fund comparison should use a separate NAV provider. AMFI can be treated as an official source for NAV history, while MFAPI-style APIs can be used for developer-friendly access where appropriate.

The internal mutual fund schema should include:

- scheme code
- scheme name
- fund house
- category, when available
- date
- NAV
- source

For V1, mutual funds are comparison assets only. The app does not rank or recommend mutual funds.

## Quant Model

### Initial Factors

V1 should prioritize price-based factors because they are easier to source consistently:

- Momentum: 3-month, 6-month, and 12-month total return.
- Trend: distance from 50-day and 200-day moving averages.
- Risk: trailing volatility, downside volatility, beta versus benchmark, and max drawdown.
- Liquidity: average traded value and volume stability.

Fundamental factors should be added later behind the same factor interface:

- Value: earnings yield, book-to-price, sales yield, EV/EBITDA.
- Quality: ROE, ROCE, operating margin, debt-to-equity, interest coverage.

### Factor Processing

Each factor should define:

- required input data
- lookback window
- direction, where higher is better or lower is better
- missing data behavior
- normalization method

The ranking engine should:

- winsorize extreme factor values
- calculate z-scores cross-sectionally at each rebalance date
- invert factors where lower is better
- apply user-defined weights
- calculate a composite score
- rank stocks inside the selected universe

## Backtest Model

V1 backtests should be intentionally realistic and understandable:

- Long-only portfolio.
- Monthly rebalance.
- Equal-weighted holdings.
- Top 10, top 20, or top 30 ranked stocks.
- User-configurable transaction cost assumption.
- No shorting, leverage, or market timing overlay.
- Exclude stocks with insufficient data at a rebalance date.
- Align all benchmark and mutual fund comparison series to the same date range.

The backend should return enough detail to audit the result:

- rebalance dates
- selected holdings per rebalance
- factor scores per selected holding
- portfolio weights
- turnover at each rebalance
- period returns

## Metrics

Strategy, benchmark, and mutual fund comparisons should include:

- CAGR
- total return
- annualized volatility
- Sharpe ratio
- Sortino ratio
- maximum drawdown
- Calmar ratio
- worst rolling return
- rolling 1-year, 3-year, and 5-year returns when enough data exists
- monthly win rate versus each comparison asset
- turnover
- transaction cost drag

Summary text should be evidence-based. Example:

> The strategy outperformed the selected fund annualized, but it had a deeper maximum drawdown and higher turnover.

## Frontend Experience

The first screen should be the research workspace, not a marketing landing page.

Primary areas:

- Strategy Builder: universe, factors, weights, rebalance settings, top-N holdings, transaction cost, benchmark, mutual fund comparison selections.
- Results Overview: CAGR, drawdown, volatility, Sharpe, Sortino, turnover, and outperformance summary.
- Performance Charts: equity curve, drawdown curve, rolling returns, and monthly return heatmap.
- Holdings Explorer: selected stocks at each rebalance date, weights, factor scores, and sector when available.
- Factor Diagnostics: factor contribution, score distribution, missing data warnings, and concentration risks.
- Mutual Fund Comparison: selected funds, aligned NAV performance, rolling return comparison, drawdown comparison, and risk-adjusted verdict.

The UI should feel like a research terminal for a serious individual investor: dense enough to compare data quickly, but clear enough that an intermediate investor can understand what changed and why.

## API Boundaries

Initial backend endpoints:

- `GET /health`
- `GET /universes`
- `GET /factors`
- `GET /benchmarks`
- `GET /mutual-funds/search`
- `POST /backtests`
- `GET /backtests/{id}`

The `POST /backtests` request should include:

- universe id or custom symbols
- start date
- end date
- selected factors and weights
- rebalance frequency
- top-N holdings
- transaction cost
- benchmark ids
- mutual fund scheme codes

The response should include:

- run metadata
- metric cards
- chart-ready time series
- drawdown series
- rolling return series
- holdings by rebalance date
- factor scores
- comparison results
- warnings

## Error Handling

The system should surface data and configuration issues clearly:

- Not enough price history for selected factors.
- Mutual fund NAV unavailable for the selected date range.
- Benchmark data does not overlap enough with the strategy period.
- Too few valid stocks in the selected universe.
- External data provider failed.
- Cached data is stale.

Errors should be actionable and shown in the frontend without crashing the workspace.

## Testing Strategy

### Quant Engine

- Unit tests for factor calculations.
- Unit tests for z-score normalization, factor direction handling, and composite ranking.
- Unit tests for turnover and transaction cost calculations.
- Unit tests for CAGR, volatility, Sharpe, Sortino, max drawdown, and Calmar ratio.
- Golden sample tests for small deterministic backtests.

### Backend

- API contract tests for strategy config validation.
- Tests for missing data warnings.
- Tests for mutual fund comparison alignment.

### Frontend

- Component tests for strategy builder state.
- Chart rendering smoke tests.
- Empty, loading, error, and successful backtest states.

### End-To-End

- One seeded demo dataset should allow the whole app to run without external API calls.
- The demo flow should create a strategy, run a backtest, compare it with a benchmark and mutual fund, and render all main result sections.

## Development Sequence

1. Scaffold the monorepo/app structure.
2. Add seeded demo data so the product works end to end before live data integrations.
3. Build the Python quant engine and tests.
4. Expose FastAPI endpoints.
5. Build the Next.js dashboard.
6. Wire frontend to backend.
7. Add mutual fund comparison.
8. Add provider adapters and local caching.
9. Polish UI states and run end-to-end verification.

## Success Criteria

V1 is successful when a user can:

- open the web app
- configure a factor strategy for Indian equities
- run a backtest
- understand the return and risk profile
- compare the strategy against an index and at least one mutual fund
- inspect historical holdings and factor scores
- see clear warnings when data quality limits the result

The project should be impressive as a portfolio project because it demonstrates full-stack engineering, financial product thinking, quant research, data modeling, and professional UI design.
