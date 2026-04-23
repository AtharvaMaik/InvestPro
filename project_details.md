# InvestPro Project Details

Date: 2026-04-23

## 1. Product Contract

InvestPro is an end-to-end Indian equity factor research platform for active stock pickers. It lets a user build a rules-based stock selection strategy, backtest it historically, compare it against Indian indices and mutual funds, and inspect whether the extra risk, turnover, and effort of stock picking were justified.

The app must not present results as personalized buy or sell advice. It must present research evidence: factor scores, portfolio histories, performance metrics, risk measures, comparison results, and data-quality warnings.

The app-facing product is live-data only. Seeded demo utilities may remain in the repository for automated tests, but the user workflow initializes `dataSource = live`, labels metadata as live, hides demo-only quality/value factors, and does not silently replace failed live providers with fake price, benchmark, NAV, or fundamental data.

V4 adds portfolio workflow fields: `portfolioCapital`, `currentHoldings`, `allocationPlan`, `rebalanceTrades`, and `executionChecklist`. These convert model target weights into rupee-level research allocations and rebalance actions while keeping the product framed as research software, not personalized advice.

V5 begins by making current portfolio entry data-backed. The frontend fetches the stock universe from `GET /stocks`, lets the user search by symbol, display name, or sector, and adds the selected stock into `currentHoldings` with optional rupee value and share quantity. This removes fragile manual symbol typing from the main workflow.

The default V1 flow is:

1. User opens the research workspace.
2. User selects an equity universe.
3. User selects factors and weights.
4. User chooses top-N holdings, rebalance frequency, date range, transaction cost, benchmarks, and mutual funds.
5. Backend runs a long-only factor backtest.
6. Frontend renders performance, drawdowns, rolling returns, holdings, factor diagnostics, and mutual fund comparisons.

## 2. Core Objects

### 2.1 Price Bar

```json
{
  "symbol": "RELIANCE.NS",
  "date": "2024-03-28",
  "open": 2920.0,
  "high": 2965.0,
  "low": 2894.0,
  "close": 2948.0,
  "adjustedClose": 2948.0,
  "volume": 5432100,
  "source": "demo"
}
```

`adjustedClose` is the preferred price for return calculations. If adjusted close is unavailable, the backend may use close and must include a warning in the backtest response.

### 2.2 Mutual Fund NAV

```json
{
  "schemeCode": "122639",
  "schemeName": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
  "fundHouse": "PPFAS Mutual Fund",
  "category": "Flexi Cap",
  "date": "2024-03-28",
  "nav": 73.42,
  "source": "demo"
}
```

NAV series are comparison assets only in V1. The app does not recommend mutual funds.

### 2.3 Strategy Config

```json
{
  "universeId": "nifty50-demo",
  "customSymbols": [],
  "startDate": "2020-01-01",
  "endDate": "2024-12-31",
  "rebalanceFrequency": "monthly",
  "topN": 10,
  "transactionCostBps": 25,
  "factors": [
    { "id": "momentum_6m", "weight": 0.35 },
    { "id": "momentum_12m", "weight": 0.25 },
    { "id": "volatility_6m", "weight": 0.20 },
    { "id": "liquidity_3m", "weight": 0.20 }
  ],
  "benchmarks": ["nifty50-demo"],
  "mutualFunds": ["ppfas-flexi-demo"],
  "portfolioCapital": 500000,
  "currentHoldings": [
    { "symbol": "RELIANCE.NS", "value": 100000 },
    { "symbol": "TCS.NS", "shares": 5 }
  ]
}
```

Factor weights are normalized by the backend so their absolute sum equals 1. If all submitted factor weights are zero, the API rejects the request.

`currentHoldings` is optional. Each row must include a `symbol` from the supported stock universe. A holding may specify `value`, `shares`, or both. When a value is present it is used directly as current rupee exposure. When only shares are present, the backend estimates current exposure as:

```text
CurrentValue_i = Shares_i * LatestPrice_i
```

Rows with unknown symbols are treated as legacy holdings and can appear as exit or avoid actions in the rebalance output.

## 3. Math Definitions

All calculations use daily data unless a section states otherwise.

### 3.1 Simple Return

For asset `i` on date `t`:

```text
r_i,t = (P_i,t / P_i,t-1) - 1
```

`P` is adjusted close when available.

### 3.2 Cumulative Wealth

Starting from 1.0:

```text
W_0 = 1
W_t = W_t-1 * (1 + r_t)
```

The frontend equity curve displays `W_t`.

### 3.3 Total Return

```text
Total Return = (W_T / W_0) - 1
```

### 3.4 CAGR

Let `D` be the number of calendar days between the first and last return observation:

```text
CAGR = (W_T / W_0) ^ (365.25 / D) - 1
```

If `D <= 0`, CAGR is unavailable.

### 3.5 Annualized Volatility

For daily returns:

```text
Volatility = stdev(r_daily) * sqrt(252)
```

If fewer than two returns exist, volatility is unavailable.

### 3.6 Sharpe Ratio

V1 uses a default annual risk-free rate of 0 unless configured later.

```text
Sharpe = (CAGR - RiskFreeRate) / AnnualizedVolatility
```

If annualized volatility is zero or unavailable, Sharpe is unavailable.

### 3.7 Downside Volatility

Downside returns are daily returns below the minimum acceptable return. V1 uses 0.

```text
DownsideVolatility = stdev(min(r_daily, 0)) * sqrt(252)
```

### 3.8 Sortino Ratio

```text
Sortino = (CAGR - RiskFreeRate) / DownsideVolatility
```

If downside volatility is zero or unavailable, Sortino is unavailable.

### 3.9 Drawdown

```text
Peak_t = max(W_0 ... W_t)
Drawdown_t = (W_t / Peak_t) - 1
MaxDrawdown = min(Drawdown_t)
```

Drawdown is shown as a negative percentage.

### 3.10 Calmar Ratio

```text
Calmar = CAGR / abs(MaxDrawdown)
```

If max drawdown is zero or unavailable, Calmar is unavailable.

### 3.11 Rolling Returns

For a rolling window of `N` trading days:

```text
RollingReturn_t,N = (W_t / W_t-N) - 1
```

V1 windows:

- 1 year: 252 trading days.
- 3 years: 756 trading days.
- 5 years: 1260 trading days.

If the history is shorter than the requested window, the series is omitted and the UI shows "Not enough history".

### 3.12 Monthly Win Rate

For strategy monthly returns `S_m` and comparison monthly returns `B_m`:

```text
WinRate = count(S_m > B_m) / count(months with both observations)
```

### 3.13 Beta

For asset or strategy returns `r_i` and benchmark returns `r_b`:

```text
Beta = covariance(r_i, r_b) / variance(r_b)
```

If benchmark variance is zero or unavailable, beta is unavailable.

### 3.14 Turnover

Let `w_before_i` be the portfolio weight immediately before rebalancing after market movement, and `w_after_i` be the target weight after rebalancing:

```text
OneWayTurnover = 0.5 * sum(abs(w_after_i - w_before_i))
```

Turnover is calculated at every rebalance date. Annual turnover is:

```text
AnnualTurnover = average(RebalanceTurnover) * RebalancesPerYear
```

### 3.15 Transaction Cost Drag

Transaction cost is entered in basis points.

```text
CostRate = transactionCostBps / 10000
RebalanceCost = OneWayTurnover * CostRate
PortfolioReturnAfterCost = PortfolioReturnBeforeCost - RebalanceCost
```

V1 applies cost on rebalance dates only.

## 4. Factor Math

### 4.1 Momentum

Momentum uses point-to-point returns over a lookback window.

```text
Momentum_N = (P_t / P_t-N) - 1
```

V1 factor IDs:

- `momentum_3m`: `N = 63`.
- `momentum_6m`: `N = 126`.
- `momentum_12m`: `N = 252`.

Higher is better.

### 4.2 Trend Distance

Moving average distance measures whether price is above or below trend.

```text
SMA_N,t = average(P_t-N+1 ... P_t)
TrendDistance_N = (P_t / SMA_N,t) - 1
```

V1 factor IDs:

- `trend_50d`: `N = 50`.
- `trend_200d`: `N = 200`.

Higher is better.

### 4.3 Volatility

Volatility uses trailing daily return standard deviation.

```text
Volatility_N = stdev(r_t-N+1 ... r_t) * sqrt(252)
```

V1 factor ID:

- `volatility_6m`: `N = 126`.

Lower is better, so the normalized score is inverted.

### 4.4 Downside Volatility

```text
DownsideVol_N = stdev(min(r_t-N+1 ... r_t, 0)) * sqrt(252)
```

Lower is better.

### 4.5 Maximum Drawdown Factor

For each stock over the lookback window:

```text
WindowWealth_k = P_k / P_start
WindowPeak_k = max(WindowWealth_start ... WindowWealth_k)
WindowDrawdown_k = (WindowWealth_k / WindowPeak_k) - 1
MaxDrawdown_N = min(WindowDrawdown_k)
```

Less severe drawdown is better. Since the value is negative, higher is better, for example `-0.12` is better than `-0.40`.

### 4.6 Liquidity

Average traded value:

```text
TradedValue_t = Close_t * Volume_t
AverageTradedValue_N = average(TradedValue_t-N+1 ... TradedValue_t)
```

V1 factor ID:

- `liquidity_3m`: `N = 63`.

Higher is better. Stocks with extremely low liquidity can also be removed by a universe-level minimum threshold.

### 4.7 Demo Fundamental Factors

V1 includes deterministic demo-only fundamental factors so the product can model quality and value workflows before live fundamentals are integrated:

- `quality_score`: higher is better and represents profitability and balance-sheet quality proxies.
- `value_score`: higher is better and represents valuation yield proxies.

Live fundamental data is a later provider integration. Until then, these factors are useful for UI, ranking, and diagnostics validation, but should not be treated as real company fundamentals.

### 4.8 Winsorization

For a factor on rebalance date `t`, across all eligible stocks:

```text
WinsorizedValue_i = min(max(raw_i, percentile_5), percentile_95)
```

This reduces the impact of extreme data points.

### 4.9 Z-Score Normalization

For each factor on each rebalance date:

```text
z_i = (x_i - mean(x)) / stdev(x)
```

If lower raw values are better, invert after z-scoring:

```text
score_i = -z_i
```

If higher raw values are better:

```text
score_i = z_i
```

If standard deviation is zero, every stock receives score `0` for that factor and a warning is added.

### 4.10 Composite Score

Let normalized factor weights sum to 1:

```text
CompositeScore_i = sum(weight_f * score_i,f)
```

Stocks are ranked descending by composite score.

Tie-breakers:

1. Higher composite score.
2. Higher liquidity score.
3. Alphabetical symbol order for deterministic output.

### 4.11 Quant V2 Fundamental Factors

Quant V2 adds real fundamental factor fields in live mode when Yahoo Finance exposes them, and deterministic seeded values in demo mode:

- `roe`: return on equity. Higher is better.
- `roce`: return on capital employed. Higher is better when available.
- `debt_to_equity`: debt divided by equity. Lower is better.
- `earnings_growth`: trailing earnings growth proxy. Higher is better.
- `pe_ratio`: price divided by earnings. Lower is better.
- `pb_ratio`: price divided by book value. Lower is better.

Missing live fundamental values are skipped for that stock and factor. If live fundamentals are sparse or fail, the response includes a warning so the user knows whether the run used complete real fundamentals or fallback data.

### 4.12 Benchmark-Relative Momentum

Relative momentum rewards stocks outperforming the benchmark, not merely stocks that rose in an up-market:

```text
RelativeMomentum_6M_i = Momentum_6M_i - Momentum_6M_benchmark
```

Higher is better.

### 4.13 Trend Filter

The optional trend filter requires:

```text
TrendDistance_200D_i = (P_i,t / SMA_200D_i,t) - 1
TrendDistance_200D_i >= 0
```

If the stock has fewer than 200 observations on a rebalance date, it is not eligible when the filter is enabled.

### 4.14 Drawdown-Aware Ranking

The drawdown factor calculates each stock's worst peak-to-trough fall over the trailing 126 trading days:

```text
Drawdown_k = (P_k / max(P_start ... P_k)) - 1
Drawdown_6M = min(Drawdown_k)
```

The value is negative or zero. Higher is better because `-0.10` is a shallower drawdown than `-0.35`.

## 5. Portfolio Construction

At each rebalance date:

1. Calculate factors using only data available on or before that date.
2. Remove stocks with insufficient factor history.
3. Rank eligible stocks by composite score.
4. Select the top `N` stocks.
5. Assign target weights according to the selected weighting method:

```text
TargetWeight_i = 1 / N
```

Equal weighting uses the formula above. Score weighting tilts toward higher composite scores. Volatility weighting tilts toward lower trailing volatility names.

6. Apply transaction cost based on turnover from the previous holdings.
7. Hold the selected portfolio until the next rebalance date.

If fewer than `N` stocks are eligible, invest equally across the eligible stocks and add a warning. If zero stocks are eligible, the portfolio stays in cash for that period with return `0`.

### 5.1 Sector Cap

Quant V2 can enable practical sector neutrality through a concentration cap:

```text
MaxStocksPerSector = max(1, floor(TopN * MaxSectorWeight))
```

The ranked list is scanned from highest to lowest composite score. A stock is selected only if adding it would not exceed `MaxStocksPerSector` for its sector. This prevents a 15-stock portfolio from becoming mostly one sector while still allowing the model to prefer strong sectors.

## 6. Backtest Flow

### 6.1 Date Handling

The backend builds a shared trading calendar from the union of available price dates, then aligns each stock, benchmark, and NAV series to valid observation dates. Strategy return dates are the dates where portfolio holdings can be valued.

### 6.2 Rebalance Dates

For `monthly` frequency, the rebalance date is the last available trading date of each calendar month in the selected date range. For `quarterly` frequency, the rebalance date is the last available trading date of each calendar quarter.

### 6.3 Portfolio Period Return

Between rebalance date `a` and next date `b`, with holdings `H`:

```text
PortfolioReturn_t = sum(weight_i * r_i,t)
```

Weights drift naturally between rebalances based on asset returns. At the next rebalance, weights are reset to equal target weights.

### 6.4 Benchmark And Mutual Fund Alignment

Comparison assets are converted to daily returns and then cumulative wealth. The comparison period is clipped to the overlap of:

- strategy start date
- strategy end date
- comparison asset first valid date
- comparison asset last valid date

If overlap is less than 252 trading days, the UI must show a warning that the comparison is short.

### 6.5 Mutual Fund Category Comparison

Selected mutual funds are grouped by category, such as Flexi Cap, Large Cap, Mid Cap, Small Cap, ELSS, and Index. For every category:

```text
AverageCategoryCAGR = average(CAGR_fund_1 ... CAGR_fund_n)
AverageCategorySharpe = average(Sharpe_fund_1 ... Sharpe_fund_n)
AverageCategoryMaxDrawdown = average(MaxDrawdown_fund_1 ... MaxDrawdown_fund_n)
AverageCategoryWinRate = average(StrategyMonthlyWinRate_vs_fund)
```

### 6.6 Rolling Analysis

Quant V2 reports rolling one-year, three-year, and five-year strategy returns when enough observations exist:

```text
RollingReturn_N,t = (W_t / W_t-N) - 1
```

The API also reports positive month rate and average one-year rolling return.

### 6.7 Walk-Forward Validation

The selected backtest range is split by observation count:

```text
Train = first 60% of strategy returns
Test = final 40% of strategy returns
```

The same submitted strategy settings are evaluated on both windows. The response reports train metrics, test metrics, and degradation:

```text
CAGRDegradation = TestCAGR - TrainCAGR
DrawdownDegradation = TestMaxDrawdown - TrainMaxDrawdown
```

This is validation, not automatic optimization. It helps identify strategies that look strong only in the full fitted period.

### 6.8 V3 Decision Layer

V3 adds interpretation fields after the quantitative backtest is complete. These fields do not alter historical returns; they help the user judge whether the research output is trustworthy and investable.

#### Data Confidence

```text
DataConfidenceScore =
  0.40 * PriceCoverage
+ 0.25 * FundamentalCoverage
+ 0.35 * FactorCoverage
- FallbackPenalty
- DemoPenalty
```

Confidence levels:

- `high`: score >= 0.80.
- `medium`: score >= 0.55 and < 0.80.
- `low`: score < 0.55.

`PriceCoverage` is the share of requested symbols with price data. `FundamentalCoverage` is the non-missing share of fundamental fields. `FactorCoverage` is the average share of symbols with computable selected factors across rebalance dates.

#### Investability

V3 checks:

- largest position weight <= `maxPositionWeight`
- annual turnover <= `maxAnnualTurnover`
- largest sector weight <= `maxSectorWeight` when sector caps are enabled
- latest holdings count is reasonably close to the target holding count

The investability verdict is:

- `investable` when no checks fail.
- `watch` when one or two checks fail.
- `not_investable` when more than two checks fail.

#### Risk Budget

Risk level is derived from annualized volatility and maximum drawdown:

- `conservative`: max drawdown <= 18% and volatility <= 18%.
- `balanced`: max drawdown <= 28% and volatility <= 25%.
- `aggressive`: max drawdown <= 40% and volatility <= 35%.
- `speculative`: anything above those limits.

The response also includes benchmark volatility and largest sector exposure for context.

#### Research Verdict

The final research verdict is:

- `pass`: data confidence is acceptable, investability passes, risk is not speculative, walk-forward is complete.
- `watch`: the strategy is interpretable but has concerns.
- `reject`: data confidence is low, no holdings are produced, investability fails materially, or risk is too high.

The verdict is a research summary, not a buy or sell recommendation.

#### Rebalance Journal

Every rebalance journal entry records:

- `added`: stocks entering the selected portfolio.
- `removed`: stocks leaving the selected portfolio.
- `retained`: stocks still held.
- `turnover`: one-way turnover caused by the rebalance.
- `reason`: strongest factor drivers for added and retained names.

## 7. API Specification

All backend responses use JSON. Dates use ISO `YYYY-MM-DD`.

### 7.1 `GET /health`

Purpose: verify the backend is alive.

Response:

```json
{
  "status": "ok",
  "service": "investpro-api",
  "version": "0.1.0"
}
```

### 7.2 `GET /universes`

Purpose: list stock universes available for strategy construction.

Response:

```json
{
  "universes": [
    {
      "id": "nifty50-demo",
      "name": "Nifty 50 Demo",
      "description": "Seeded Indian large-cap demo universe",
      "symbolCount": 12,
      "source": "demo"
    }
  ]
}
```

### 7.3 `GET /factors`

Purpose: list supported factors and how they behave.

Response:

```json
{
  "factors": [
    {
      "id": "momentum_6m",
      "name": "6M Momentum",
      "category": "Momentum",
      "direction": "higher_is_better",
      "lookbackDays": 126,
      "description": "Six-month price return"
    },
    {
      "id": "volatility_6m",
      "name": "6M Volatility",
      "category": "Risk",
      "direction": "lower_is_better",
      "lookbackDays": 126,
      "description": "Annualized trailing six-month volatility"
    }
  ]
}
```

### 7.4 `GET /benchmarks`

Purpose: list index comparison series.

Response:

```json
{
  "benchmarks": [
    {
      "id": "nifty50-demo",
      "name": "Nifty 50 Demo",
      "category": "Large Cap Index",
      "source": "demo"
    }
  ]
}
```

### 7.5 `GET /mutual-funds/search?query=parag`

Purpose: search mutual funds by name.

Optional query parameter:

- `source=demo` returns seeded funds.
- `source=live` searches MFAPI and falls back to seeded funds if MFAPI is unavailable.

Response:

```json
{
  "results": [
    {
      "schemeCode": "ppfas-flexi-demo",
      "schemeName": "Parag Parikh Flexi Cap Fund Demo",
      "fundHouse": "PPFAS Mutual Fund",
      "category": "Flexi Cap",
      "source": "demo"
    }
  ]
}
```

Empty query returns a curated default list in V1.

### 7.6 `GET /stocks`

Purpose: return the stock universe used by the portfolio setup search control.

Response:

```json
{
  "stocks": [
    {
      "symbol": "RELIANCE.NS",
      "name": "RELIANCE",
      "sector": "Energy",
      "source": "live"
    },
    {
      "symbol": "TCS.NS",
      "name": "TCS",
      "sector": "Information Technology",
      "source": "live"
    }
  ]
}
```

Frontend use:

1. Fetch once during initial metadata load.
2. Search client-side by `symbol`, `name`, or `sector`.
3. Exclude symbols already present in `currentHoldings` from the quick suggestions.
4. Add the selected symbol to `currentHoldings` with editable `value` and `shares` fields.

### 7.7 `POST /backtests`

Purpose: run a factor strategy backtest.

Request:

```json
{
  "universeId": "nifty50-demo",
  "customSymbols": [],
  "startDate": "2020-01-01",
  "endDate": "2024-12-31",
  "rebalanceFrequency": "monthly",
  "topN": 10,
  "transactionCostBps": 25,
  "factors": [
    { "id": "momentum_6m", "weight": 0.35 },
    { "id": "momentum_12m", "weight": 0.25 },
    { "id": "volatility_6m", "weight": 0.20 },
    { "id": "liquidity_3m", "weight": 0.20 }
  ],
  "benchmarks": ["nifty50-demo"],
  "mutualFunds": ["ppfas-flexi-demo"]
}
```

Response:

```json
{
  "id": "bt_20260423_000001",
  "status": "completed",
  "config": {},
  "summary": {
    "startDate": "2020-01-31",
    "endDate": "2024-12-31",
    "tradingDays": 1234,
    "rebalanceCount": 60
  },
  "metrics": {
    "strategy": {
      "cagr": 0.184,
      "totalReturn": 1.31,
      "volatility": 0.218,
      "sharpe": 0.84,
      "sortino": 1.19,
      "maxDrawdown": -0.281,
      "calmar": 0.65,
      "annualTurnover": 1.74,
      "transactionCostDrag": 0.012
    }
  },
  "series": {
    "equityCurve": [
      { "date": "2020-01-31", "strategy": 1.0, "nifty50-demo": 1.0, "ppfas-flexi-demo": 1.0 }
    ],
    "drawdown": [
      { "date": "2020-01-31", "strategy": 0.0, "nifty50-demo": 0.0, "ppfas-flexi-demo": 0.0 }
    ],
    "rollingReturns": {
      "oneYear": [],
      "threeYear": [],
      "fiveYear": []
    },
    "monthlyReturns": []
  },
  "holdings": [
    {
      "rebalanceDate": "2020-01-31",
      "symbols": [
        {
          "symbol": "RELIANCE.NS",
          "weight": 0.1,
          "compositeScore": 1.42,
          "factorScores": {
            "momentum_6m": 1.1,
            "momentum_12m": 1.3,
            "volatility_6m": 0.8,
            "liquidity_3m": 2.0
          }
        }
      ]
    }
  ],
  "comparisons": [
    {
      "id": "ppfas-flexi-demo",
      "name": "Parag Parikh Flexi Cap Fund Demo",
      "type": "mutual_fund",
      "metrics": {
        "cagr": 0.152,
        "volatility": 0.164,
        "maxDrawdown": -0.221,
        "sharpe": 0.93
      },
      "monthlyWinRate": 0.57
    }
  ],
  "warnings": [
    {
      "code": "DEMO_DATA",
      "message": "This result uses seeded demo data and is for product validation only."
    }
  ]
}
```

### 7.7 `GET /backtests/{id}`

Purpose: retrieve a previous run from local storage.

Response: same shape as `POST /backtests`.

If the id does not exist:

```json
{
  "detail": {
    "code": "BACKTEST_NOT_FOUND",
    "message": "No backtest exists for id bt_missing."
  }
}
```

HTTP status: `404`.

## 8. Error Codes

| Code | HTTP Status | Meaning | UI Behavior |
| --- | --- | --- | --- |
| `INVALID_DATE_RANGE` | 422 | Start date is after end date or range is too short. | Highlight date fields and show inline message. |
| `UNKNOWN_FACTOR` | 422 | A submitted factor id is unsupported. | Mark factor section invalid. |
| `ZERO_FACTOR_WEIGHT` | 422 | All factor weights sum to zero. | Ask user to assign at least one positive weight. |
| `UNIVERSE_NOT_FOUND` | 404 | Universe id does not exist. | Show non-blocking error panel. |
| `INSUFFICIENT_DATA` | 422 | Not enough stock data for selected factors. | Explain which factor needs more history. |
| `COMPARISON_NOT_FOUND` | 404 | Benchmark or mutual fund id does not exist. | Remove invalid comparison and prompt reselection. |
| `PROVIDER_FAILURE` | 502 | External provider failed. | Offer retry and keep cached/demo data if available. |
| `LIVE_DATA_FALLBACK` | 200 | Live stock data failed and seeded demo prices were used. | Show a warning while keeping the backtest usable. |
| `LIVE_BENCHMARK_FALLBACK` | 200 | Live benchmark data failed and seeded benchmark data was used. | Show a warning in comparison areas. |
| `LIVE_MUTUAL_FUND_FALLBACK` | 200 | Live mutual fund NAV data failed and seeded NAV data was used. | Show a warning in mutual fund comparison areas. |

## 9. Frontend Flow

### 9.1 Initial Load

1. Render the workspace shell immediately.
2. Fetch `/universes`, `/factors`, `/benchmarks`, `/stocks`, and default mutual fund search results in parallel.
3. Fill the strategy builder with a sensible default config.
4. Show a demo-ready call to action: "Run Backtest".

### 9.2 Strategy Builder

Controls:

- Data source selector: demo or live.
- Universe dropdown.
- Date range inputs.
- Factor checklist with weight sliders or numeric fields.
- Top-N segmented control: 10, 20, 30.
- Rebalance frequency selector, V1 locked to monthly.
- Transaction cost input in basis points.
- Benchmark selector.
- Mutual fund search and selected fund chips.
- Portfolio capital slider.
- Searchable current-holding stock picker backed by `GET /stocks`.
- Current-holding rows with stock dropdown, rupee value, share count, and remove action.

Validation:

- At least one factor must have positive weight.
- Top-N must be positive.
- Transaction cost must be between 0 and 200 bps.
- End date must be after start date.
- Current holding symbols should come from the stock universe unless intentionally modeling a legacy position to exit.

### 9.3 Running A Backtest

1. User clicks "Run Backtest".
2. Button enters loading state with disabled controls that could invalidate the request.
3. Frontend sends `POST /backtests`.
4. If successful, results animate into view.
5. If failed, an error panel appears beside the builder without losing current inputs.

### 9.4 Results Layout

The result page is one workspace, not disconnected pages:

- Top row: key metric cards.
- Main chart row: equity curve and drawdown chart.
- Comparison row: mutual fund and benchmark table.
- Diagnostics row: rolling returns, monthly heatmap, turnover, and warnings.
- Detail row: holdings by rebalance date and factor score table.

### 9.5 Empty, Loading, And Error States

Empty state: show a refined demo prompt with no marketing fluff.

Loading state: use skeletons and subtle progress motion. Avoid jarring spinners as the main visual.

Error state: show what failed, why it matters, and what the user can change.

## 10. UI Quality Bar

The UI must feel professional, aligned, responsive, and smooth.

### 10.1 Visual Style

- Dense research dashboard with strong hierarchy.
- Clean neutral base with selective accent colors for positive, negative, and active states.
- Avoid loud gradients, decorative blobs, and excessive shadows.
- Cards may be used for repeated metrics and tool panels only.
- Sections should align to a consistent grid.
- Tables must have readable spacing, sticky headers where useful, and clear numeric alignment.

### 10.2 Responsiveness

Desktop:

- Strategy builder can sit in a left rail or top control band.
- Charts and tables use wide layouts.
- Key metrics appear in a compact grid.

Tablet:

- Strategy controls wrap into two columns.
- Charts remain full width.
- Tables allow horizontal scroll where necessary.

Mobile:

- Controls stack cleanly.
- Metric cards use two columns or one column depending on width.
- Charts keep fixed responsive heights.
- Tables become scrollable with no text overlap.

### 10.3 Motion

Motion should be smooth as butter but never distracting:

- Use short transitions around 150-250 ms.
- Animate result cards with subtle opacity and vertical movement.
- Animate chart entrance after data load.
- Use hover and press states on interactive controls.
- Respect reduced-motion preferences by disabling nonessential animations.

### 10.4 Alignment And Polish

- All inputs, buttons, cards, and charts must align to shared spacing tokens.
- Numeric values should use tabular numbers.
- Long labels must truncate or wrap intentionally.
- Buttons must not resize during loading.
- Skeleton states must occupy the same dimensions as loaded content.
- No text should overlap at desktop, tablet, or mobile breakpoints.

### 10.5 Portfolio Stock Picker

The portfolio setup control must optimize for fast, error-resistant entry:

- Use a searchable input with native `datalist` support plus visible suggestion buttons.
- Match query text against ticker symbol, display name, and sector.
- Convert typed text to uppercase so NSE tickers remain consistent.
- Hide already selected symbols from the suggestion list.
- Add the chosen stock into `currentHoldings` with default `value = 0` and `shares = null`.
- Keep value and shares editable after selection.
- Use a stable row key so typing or changing values does not remount inputs.
- On mobile, stack search, suggestions, dropdown, value, shares, and remove controls into one column.

## 11. Backend Flow

### 11.1 Backtest Request Processing

1. Validate request schema with Pydantic.
2. Normalize factor weights.
3. Resolve universe symbols.
4. Load price data from cache or demo provider.
5. Load benchmarks and mutual fund NAVs.
6. Build rebalance dates.
7. Calculate factor matrix.
8. Rank stocks on each rebalance date.
9. Construct holdings.
10. Simulate daily portfolio returns.
11. Apply transaction costs.
12. Calculate metrics and comparison metrics.
13. Persist run metadata and result JSON.
14. Return chart-ready response.

### 11.2 Data Quality Rules

- A stock is eligible for a rebalance only if every selected factor can be calculated.
- A factor with zero cross-sectional standard deviation contributes score `0` for all stocks on that date.
- A missing benchmark or mutual fund comparison does not invalidate the strategy run unless the user selected only invalid comparison assets.
- Warnings are returned with machine-readable codes and human-readable messages.
- `GET /stocks` must use the same supported symbol list as the investable universe so portfolio setup cannot easily create malformed holdings.
- If a current holding has shares but no value, latest available stock price is used to estimate its current value.
- If a current holding has a value, that value takes priority over share-based estimation.

## 12. Testing Expectations

### 12.1 Quant Tests

Tests must verify:

- return calculation
- CAGR
- volatility
- Sharpe
- Sortino
- max drawdown
- Calmar
- rolling returns
- turnover
- transaction cost drag
- factor winsorization
- z-score normalization
- lower-is-better inversion
- composite scoring
- deterministic rank tie-breaking

### 12.2 API Tests

Tests must verify:

- health endpoint response
- metadata endpoints
- searchable stock universe endpoint
- valid backtest request
- invalid date range
- unknown factor
- zero factor weights
- missing backtest id

### 12.3 Frontend Tests

Tests must verify:

- default strategy config renders
- factor weight controls update state
- portfolio stock search filters and adds selected holdings
- invalid form states block submission
- successful backtest renders metric cards and charts
- API error renders an inline error panel

### 12.4 End-To-End Verification

The seeded demo dataset must allow the complete product to run without live network access:

1. Start backend.
2. Start frontend.
3. Open app.
4. Run default strategy.
5. Confirm metrics render.
6. Confirm equity curve and drawdown render.
7. Confirm mutual fund comparison renders.
8. Confirm holdings table renders.

## 13. Implementation Principle

Build from the inside out:

1. Quant math with deterministic tests.
2. API contracts with seeded demo data.
3. Frontend workspace using real API responses.
4. Smooth UI states and responsive polish.
5. Provider adapters and live data after the demo app is solid.

This order prevents the app from becoming a pretty shell with unreliable math.
