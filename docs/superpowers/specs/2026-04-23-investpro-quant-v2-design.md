# InvestPro Quant V2 Design

## Goal

Upgrade InvestPro from a price-only momentum stock picker into a more complete Indian equity quant research workflow with live fundamentals, sector-aware portfolio construction, drawdown and trend controls, benchmark-relative momentum, mutual fund category comparisons, rolling analysis, and walk-forward validation.

## Strategy Contract

The strategy remains long-only and rules-based. On each rebalance date it:

1. Loads price, volume, sector, and fundamental data for the selected universe.
2. Calculates selected factor values using only information available up to the rebalance date.
3. Filters stocks that fail the optional 200-day moving-average trend rule.
4. Normalizes factor values cross-sectionally with winsorized z-scores.
5. Ranks stocks by weighted composite score.
6. Selects top-ranked stocks while respecting sector concentration caps.
7. Assigns weights using equal, score, or volatility-scaled weighting.
8. Applies transaction costs on turnover.
9. Reports strategy, benchmark, mutual fund, rolling, and walk-forward performance.

## New Factors

- `relative_momentum_6m`: stock six-month return minus benchmark six-month return. Higher is better.
- `drawdown_6m`: worst stock drawdown over the trailing 126 trading days. Less severe drawdown is better.
- `trend_200d`: price divided by the 200-day moving average minus 1. Higher is better.
- `roe`: return on equity. Higher is better.
- `roce`: return on capital employed. Higher is better when available; demo data supplies deterministic values.
- `debt_to_equity`: balance-sheet leverage. Lower is better.
- `earnings_growth`: earnings growth proxy. Higher is better.
- `pe_ratio`: price/earnings valuation. Lower is better.
- `pb_ratio`: price/book valuation. Lower is better.

Live fundamentals come from Yahoo Finance metadata where available. Missing live values are left unavailable and surfaced through warnings. Demo mode uses deterministic seeded fundamentals so tests and UI flows are stable offline.

## Sector Neutrality

The portfolio enforces practical sector diversification rather than strict neutrality. The request can enable a sector cap with `maxSectorWeight`, defaulting to 30%. For a 15-stock equal-weight portfolio, a 30% cap allows at most four stocks from one sector. Stocks beyond the sector cap are skipped and the next ranked eligible stock is considered.

## Trend Filter

When enabled, a stock must have `trend_200d >= 0`, meaning its latest price is at or above its 200-day moving average. Stocks with insufficient history fail the filter for that rebalance date.

## Mutual Fund Category Comparison

The backend groups selected comparison funds by category, such as Flexi Cap, Large Cap, Mid Cap, ELSS, Small Cap, and Index. Each group reports average CAGR, Sharpe, max drawdown, monthly win rate, and number of funds included.

## Rolling Analysis

The response includes rolling one-year and three-year strategy returns. It also reports rolling one-year win rate versus comparison assets where enough aligned history exists.

## Walk-Forward Validation

The backend splits the selected range into a 60% train period and 40% test period. It reports train and test metrics using the same submitted strategy settings, plus CAGR degradation and drawdown degradation. This is validation, not automatic factor optimization.

## UI Contract

The frontend adds controls for trend filtering and sector cap, expands the default factor stack, and adds panels for sector exposure, mutual fund categories, rolling performance, and walk-forward validation. The UI must remain a dense professional research dashboard with clean alignment, responsive wrapping, and no overlapping text.
