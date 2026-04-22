export const glossary = {
  dataSource:
    "Demo uses seeded local data so the app always works. Live fetches NSE-style Yahoo Finance prices and MFAPI mutual fund NAVs, then falls back with warnings if a provider fails.",
  universe: "The group of stocks the strategy is allowed to rank and choose from.",
  dateRange: "The historical period used for ranking, rebalancing, and calculating performance.",
  topN: "The number of highest-ranked stocks the strategy holds after each monthly rebalance.",
  transactionCost:
    "Estimated trading cost in basis points. 25 bps means 0.25% cost applied to portfolio turnover at rebalance.",
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
  holdings: "The latest stocks selected by the factor model, including weights and factor scores."
  ,
  factorDiagnostics:
    "Tests whether each factor had evidence historically by comparing future returns of top-scored stocks versus bottom-scored stocks.",
  robustness:
    "A quick stress check showing whether the selected strategy still looks reasonable when assumptions such as costs become tougher."
} as const;
