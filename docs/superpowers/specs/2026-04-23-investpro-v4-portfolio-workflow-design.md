# InvestPro V4 Portfolio Workflow Design

## Goal

V4 turns InvestPro from a research dashboard into a portfolio workflow. A user can enter deployable capital and optional current holdings, then receive a research-safe allocation plan, rebalance trade list, and execution checklist.

## Request Additions

- `portfolioCapital`: capital amount in INR for the strategy allocation.
- `currentHoldings`: optional list of current holdings with `symbol` and either `value` or `shares`.

## Response Additions

- `allocationPlan`: latest target allocation by stock with target value, latest price, and estimated shares.
- `rebalanceTrades`: action list comparing current holdings with target allocation.
- `executionChecklist`: safety checks before acting on the research.

## Trade Classification

For each symbol in target or current holdings:

- `buy`: not currently held and target value is material.
- `add`: currently held and target value is meaningfully higher.
- `trim`: currently held and target value is meaningfully lower but remains in target.
- `hold`: current and target values are close.
- `exit`: currently held but no target weight.
- `avoid`: action list marks the stock as avoid.

## Strategy Improvement

Balanced Compounder becomes a more robust default by increasing benchmark-relative momentum, quality, drawdown control, and liquidity discipline while reducing short-term momentum dependence.

## Safety

Execution checklist must block or warn when data confidence is low, research verdict is reject, investability is not investable, or turnover exceeds budget. The UI must describe outputs as research actions, not personalized advice.
