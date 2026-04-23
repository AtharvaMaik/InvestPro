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
      momentum_6m: 0.12,
      momentum_12m: 0.14,
      relative_momentum_6m: 0.18,
      drawdown_6m: 0.12,
      trend_200d: 0.12,
      liquidity_3m: 0.06,
      roe: 0.1,
      roce: 0.08,
      debt_to_equity: 0.08,
      earnings_growth: 0.04,
      pe_ratio: 0.03,
      pb_ratio: 0.03,
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
      momentum_3m: 0.1,
      momentum_6m: 0.25,
      momentum_12m: 0.2,
      relative_momentum_6m: 0.25,
      trend_200d: 0.12,
      drawdown_6m: 0.08,
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
      roe: 0.2,
      roce: 0.18,
      debt_to_equity: 0.15,
      earnings_growth: 0.12,
      pe_ratio: 0.12,
      pb_ratio: 0.1,
      trend_200d: 0.08,
      drawdown_6m: 0.05,
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
      volatility_6m: 0.25,
      drawdown_6m: 0.25,
      trend_200d: 0.12,
      liquidity_3m: 0.1,
      roe: 0.1,
      debt_to_equity: 0.1,
      relative_momentum_6m: 0.08,
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
