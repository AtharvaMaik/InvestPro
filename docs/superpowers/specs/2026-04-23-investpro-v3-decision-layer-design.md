# InvestPro V3 Decision Layer Design

## Goal

Make InvestPro feel like a real finance research tool by adding interpretation and guardrails on top of the existing quant engine. V3 does not give personalized investment advice. It turns a backtest into an auditable research report with data confidence, investability checks, risk budget, a research verdict, and a rebalance journal.

## Product Contract

After a backtest, the API returns five new decision sections:

- `dataConfidence`: explains whether the run has enough data quality to trust.
- `investability`: checks position sizing, liquidity, turnover, and sector concentration.
- `riskBudget`: translates return/risk metrics into plain risk bands.
- `researchVerdict`: summarizes whether the run is a research pass, watch, or reject.
- `rebalanceJournal`: records added, removed, and retained stocks at each rebalance.

## Guardrails

The request accepts three additional controls:

- `maxPositionWeight`: maximum desired weight in one stock.
- `minLiquidityCrore`: minimum average traded value, expressed in INR crore.
- `maxAnnualTurnover`: maximum desired annualized turnover.

These controls are used for interpretation and investability checks. V3 does not block every run that violates them, because research tools should show why a strategy fails rather than hiding the evidence.

## Verdict Logic

The verdict is:

- `pass` when data confidence is high or medium, investability has no failed checks, walk-forward is completed, and risk is not speculative.
- `watch` when at least one concern exists but the strategy is still interpretable.
- `reject` when data confidence is low, no holdings are produced, annual turnover materially exceeds the budget, or risk is speculative with weak walk-forward evidence.

## UI Contract

The dashboard should place the verdict near the top, then show data confidence, investability, risk budget, and rebalance journal panels. The guide page should explain that V3 is a research decision layer, not execution advice.
