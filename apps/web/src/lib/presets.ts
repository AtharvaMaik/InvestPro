import type { BacktestRequest } from "@/lib/api";

export type StrategyPreset = {
  id: string;
  name: string;
  description: string;
  risk: string;
  patch: Pick<
    BacktestRequest,
    | "rebalanceFrequency"
    | "weightingMethod"
    | "topN"
    | "transactionCostBps"
    | "trendFilter"
    | "sectorNeutral"
    | "maxSectorWeight"
    | "maxPositionWeight"
    | "minLiquidityCrore"
    | "maxAnnualTurnover"
  >;
  weights: Record<string, number>;
};

export const strategyPresets: StrategyPreset[] = [
  {
    id: "balanced-compounder",
    name: "Balanced Compounder",
    description: "Robust default using relative strength, trend, quality, drawdown control, and liquidity discipline.",
    risk: "Balanced",
    patch: {
      rebalanceFrequency: "quarterly",
      weightingMethod: "equal",
      topN: 15,
      transactionCostBps: 25,
      trendFilter: true,
      sectorNeutral: true,
      maxSectorWeight: 0.3,
      maxPositionWeight: 0.08,
      minLiquidityCrore: 10,
      maxAnnualTurnover: 1.8,
    },
    weights: {
      momentum_3m: 0.03,
      momentum_6m: 0.1,
      momentum_12m: 0.12,
      volatility_6m: 0.06,
      liquidity_3m: 0.06,
      relative_momentum_6m: 0.16,
      drawdown_6m: 0.1,
      trend_200d: 0.1,
      roe: 0.09,
      roce: 0.08,
      debt_to_equity: 0.05,
      earnings_growth: 0.03,
      pe_ratio: 0.01,
      pb_ratio: 0.01,
    },
  },
  {
    id: "momentum-leader",
    name: "Momentum Leader",
    description: "Aggressive leadership strategy using absolute and benchmark-relative trend strength.",
    risk: "Aggressive",
    patch: {
      rebalanceFrequency: "monthly",
      weightingMethod: "score",
      topN: 10,
      transactionCostBps: 35,
      trendFilter: true,
      sectorNeutral: true,
      maxSectorWeight: 0.35,
      maxPositionWeight: 0.12,
      minLiquidityCrore: 10,
      maxAnnualTurnover: 3.5,
    },
    weights: {
      momentum_3m: 0.12,
      momentum_6m: 0.2,
      momentum_12m: 0.16,
      volatility_6m: 0.04,
      liquidity_3m: 0.05,
      relative_momentum_6m: 0.2,
      drawdown_6m: 0.06,
      trend_200d: 0.1,
      roe: 0.02,
      roce: 0.02,
      debt_to_equity: 0.01,
      earnings_growth: 0.01,
      pe_ratio: 0.005,
      pb_ratio: 0.005,
    },
  },
  {
    id: "quality-value",
    name: "Quality Value",
    description: "Profitability, low debt, and reasonable valuation with trend as a safety gate.",
    risk: "Balanced",
    patch: {
      rebalanceFrequency: "quarterly",
      weightingMethod: "equal",
      topN: 20,
      transactionCostBps: 25,
      trendFilter: true,
      sectorNeutral: true,
      maxSectorWeight: 0.28,
      maxPositionWeight: 0.07,
      minLiquidityCrore: 3,
      maxAnnualTurnover: 1.75,
    },
    weights: {
      momentum_3m: 0.02,
      momentum_6m: 0.04,
      momentum_12m: 0.04,
      volatility_6m: 0.05,
      liquidity_3m: 0.04,
      relative_momentum_6m: 0.04,
      drawdown_6m: 0.06,
      trend_200d: 0.08,
      roe: 0.17,
      roce: 0.16,
      debt_to_equity: 0.12,
      earnings_growth: 0.1,
      pe_ratio: 0.05,
      pb_ratio: 0.03,
    },
  },
  {
    id: "defensive-low-vol",
    name: "Low Volatility Defensive",
    description: "Smoother stocks with lower drawdowns, sector caps, and conservative turnover.",
    risk: "Conservative",
    patch: {
      rebalanceFrequency: "quarterly",
      weightingMethod: "volatility",
      topN: 20,
      transactionCostBps: 20,
      trendFilter: true,
      sectorNeutral: true,
      maxSectorWeight: 0.25,
      maxPositionWeight: 0.06,
      minLiquidityCrore: 5,
      maxAnnualTurnover: 1.5,
    },
    weights: {
      momentum_3m: 0.01,
      momentum_6m: 0.04,
      momentum_12m: 0.05,
      volatility_6m: 0.22,
      liquidity_3m: 0.1,
      relative_momentum_6m: 0.06,
      drawdown_6m: 0.2,
      trend_200d: 0.1,
      roe: 0.07,
      roce: 0.06,
      debt_to_equity: 0.05,
      earnings_growth: 0.02,
      pe_ratio: 0.01,
      pb_ratio: 0.01,
    },
  },
];

export function applyPreset(config: BacktestRequest, preset: StrategyPreset): BacktestRequest {
  return {
    ...config,
    ...preset.patch,
    factors: config.factors.map((factor) => ({
      id: factor.id,
      weight: preset.weights[factor.id] ?? 0,
    })),
  };
}
