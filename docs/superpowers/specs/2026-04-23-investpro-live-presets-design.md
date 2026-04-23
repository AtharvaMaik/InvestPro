# InvestPro Live Presets Design

## Goal

Make InvestPro app-facing behavior live-only, improve responsive scaling, and add professional strategy presets that produce an exact latest stock action list after a run.

## Live-Only Contract

The UI no longer exposes demo data. It initializes every strategy with `dataSource: "live"` and fetches live mutual fund metadata by default. The API may keep deterministic demo utilities for automated tests, but app-facing metadata should be labeled as live and live backtests must not silently fall back to seeded demo prices, benchmark, NAV, or fundamentals. Provider failures should become explicit errors or warnings that preserve research integrity.

## Presets

The builder offers preset cards:

- Balanced Compounder
- Momentum Leader
- Quality Value
- Low Volatility Defensive

Each preset applies an exact strategy configuration: factor weights, top N, rebalance frequency, trend filter, sector cap, max position weight, liquidity threshold, and turnover budget.

## Stock Action List

After a backtest, the API returns `actionList` for latest selected stocks. Actions are research labels:

- `buy_candidate`
- `hold`
- `review`
- `avoid`

The action is based on composite score, trend score, drawdown score, liquidity score, and data confidence. The UI renders these as research actions, not personalized buy or sell advice.

## Responsive UI

The dashboard should scale cleanly:

- Desktop: compact left rail plus results.
- Medium screens: top control workspace and responsive result cards.
- Small screens: single-column controls, no fixed floating button, scrollable tables, and no text overlap.

The guide link moves into a top navigation bar.
