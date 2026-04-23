export const glossary = {
  dataSource:
    "Demo uses seeded local data so the app always works. Live fetches NSE-style Yahoo Finance prices and MFAPI mutual fund NAVs, then falls back with warnings if a provider fails.",
  universe: "The group of stocks the strategy is allowed to rank and choose from.",
  dateRange: "The historical period used for ranking, rebalancing, and calculating performance.",
  topN: "The number of highest-ranked stocks the strategy holds after each monthly rebalance.",
  transactionCost:
    "Estimated trading cost in basis points. 25 bps means 0.25% cost applied to portfolio turnover at rebalance.",
  trendFilter:
    "Requires a stock to trade at or above its 200-day moving average before it can enter the portfolio.",
  sectorNeutral:
    "Limits how much of the portfolio can come from one sector so the strategy does not accidentally become all banks, IT, or metals.",
  maxSectorWeight:
    "The maximum portfolio weight allowed in one sector when the sector cap is enabled.",
  maxPositionWeight:
    "The maximum desired allocation to a single stock. This is used as a sizing guardrail and investability check.",
  minLiquidity:
    "Minimum average daily traded value in INR crore. Raising it removes less liquid stocks from selection.",
  maxAnnualTurnover:
    "The highest annualized turnover the investor is comfortable with. Higher turnover can mean more costs, taxes, and operational friction.",
  rebalanceFrequency:
    "How often the portfolio is rebuilt. Monthly reacts faster; quarterly usually lowers turnover and trading friction.",
  weightingMethod:
    "How selected stocks are sized. Equal gives each stock the same weight, score weighting favors higher-ranked stocks, and volatility weighting favors smoother stocks.",
  factors:
    "Rules used to score stocks. Each factor is normalized across the universe, weighted, and combined into one composite rank.",
  benchmark: "An index-like comparison series used to judge whether the strategy beat a passive alternative.",
  mutualFund: "A mutual fund NAV series used to compare stock-picking against a professionally managed fund.",
  cagr: "Compound annual growth rate. It converts the full backtest return into an annualized growth rate.",
  totalReturn: "Total percentage gain or loss over the entire tested period.",
  volatility: "Annualized variation in daily returns. Higher volatility means the ride was less stable.",
  maxDrawdown: "The worst peak-to-trough fall in portfolio value during the test.",
  turnover: "How much of the portfolio changed at rebalances. Higher turnover usually means higher costs and more tax friction.",
  costDrag: "Estimated performance lost to transaction costs.",
  sharpe: "Risk-adjusted return using total volatility. Higher is better, but it should be compared across similar strategies.",
  sortino: "Risk-adjusted return using downside volatility only. It focuses more on harmful volatility.",
  calmar: "Return compared with maximum drawdown. It rewards strategies that grow without deep losses.",
  equityCurve: "Growth of one rupee invested in the strategy and comparison assets.",
  drawdown: "How far each series fell from its previous high at every point in time.",
  comparisons: "Side-by-side return and risk view against benchmark and mutual fund alternatives.",
  fundCategories: "Groups selected mutual funds by category, then averages return, risk, and win-rate metrics for each category.",
  sectorExposure: "Shows the latest portfolio weight and position count by sector after the sector cap is applied.",
  rollingAnalysis:
    "Checks consistency through time instead of relying only on one full-period result.",
  walkForward:
    "Splits history into train and later test windows to show whether the same submitted strategy survives out of sample.",
  researchVerdict:
    "A research summary based on data confidence, investability, risk budget, walk-forward validation, and portfolio output.",
  dataConfidence:
    "Checks whether price coverage, fundamental coverage, factor coverage, and provider warnings are strong enough to interpret the result.",
  investability:
    "Checks whether the portfolio passes position sizing, turnover, sector concentration, and holding-count guardrails.",
  riskBudget:
    "Translates volatility, drawdown, and concentration into a plain-language risk band.",
  rebalanceJournal:
    "Shows what entered, exited, and stayed in the portfolio at each rebalance, with factor-based reasons.",
  holdings: "The latest stocks selected by the factor model, including weights and factor scores."
  ,
  factorDiagnostics:
    "Tests whether each factor had evidence historically by comparing future returns of top-scored stocks versus bottom-scored stocks.",
  robustness:
    "A quick stress check showing whether the selected strategy still looks reasonable when assumptions such as costs become tougher."
} as const;
