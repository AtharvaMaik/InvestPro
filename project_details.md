# InvestPro Project Details

Date: 2026-04-23

## 1. Product Contract

InvestPro is an end-to-end Indian equity factor research platform for active stock pickers. It lets a user build a rules-based stock selection strategy, backtest it historically, compare it against Indian indices and mutual funds, and inspect whether the extra risk, turnover, and effort of stock picking were justified.

The app must not present results as personalized buy or sell advice. It must present research evidence: factor scores, portfolio histories, performance metrics, risk measures, comparison results, and data-quality warnings.

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
  "mutualFunds": ["ppfas-flexi-demo"]
}
```

Factor weights are normalized by the backend so their absolute sum equals 1. If all submitted factor weights are zero, the API rejects the request.

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

### 4.7 Winsorization

For a factor on rebalance date `t`, across all eligible stocks:

```text
WinsorizedValue_i = min(max(raw_i, percentile_5), percentile_95)
```

This reduces the impact of extreme data points.

### 4.8 Z-Score Normalization

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

### 4.9 Composite Score

Let normalized factor weights sum to 1:

```text
CompositeScore_i = sum(weight_f * score_i,f)
```

Stocks are ranked descending by composite score.

Tie-breakers:

1. Higher composite score.
2. Higher liquidity score.
3. Alphabetical symbol order for deterministic output.

## 5. Portfolio Construction

At each rebalance date:

1. Calculate factors using only data available on or before that date.
2. Remove stocks with insufficient factor history.
3. Rank eligible stocks by composite score.
4. Select the top `N` stocks.
5. Assign equal target weight:

```text
TargetWeight_i = 1 / N
```

6. Apply transaction cost based on turnover from the previous holdings.
7. Hold the selected portfolio until the next rebalance date.

If fewer than `N` stocks are eligible, invest equally across the eligible stocks and add a warning. If zero stocks are eligible, the portfolio stays in cash for that period with return `0`.

## 6. Backtest Flow

### 6.1 Date Handling

The backend builds a shared trading calendar from the union of available price dates, then aligns each stock, benchmark, and NAV series to valid observation dates. Strategy return dates are the dates where portfolio holdings can be valued.

### 6.2 Rebalance Dates

For `monthly` frequency, the rebalance date is the last available trading date of each calendar month in the selected date range.

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

### 7.6 `POST /backtests`

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
2. Fetch `/universes`, `/factors`, `/benchmarks`, and default mutual fund search results in parallel.
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

Validation:

- At least one factor must have positive weight.
- Top-N must be positive.
- Transaction cost must be between 0 and 200 bps.
- End date must be after start date.

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
- valid backtest request
- invalid date range
- unknown factor
- zero factor weights
- missing backtest id

### 12.3 Frontend Tests

Tests must verify:

- default strategy config renders
- factor weight controls update state
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
