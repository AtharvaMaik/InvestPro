export type FactorMeta = {
  id: string;
  name: string;
  category: string;
  direction: "higher_is_better" | "lower_is_better";
  lookbackDays: number;
  description: string;
};

export type Universe = {
  id: string;
  name: string;
  description: string;
  symbolCount: number;
  source: string;
};

export type Benchmark = {
  id: string;
  name: string;
  category: string;
  source: string;
};

export type MutualFund = {
  schemeCode: string;
  schemeName: string;
  fundHouse: string;
  category: string;
  source: string;
};

export type BacktestRequest = {
  universeId: string;
  customSymbols: string[];
  startDate: string;
  endDate: string;
  rebalanceFrequency: "monthly";
  topN: number;
  transactionCostBps: number;
  factors: { id: string; weight: number }[];
  benchmarks: string[];
  mutualFunds: string[];
};

export type MetricSet = {
  total_return?: number | null;
  cagr?: number | null;
  volatility?: number | null;
  sharpe?: number | null;
  sortino?: number | null;
  max_drawdown?: number | null;
  calmar?: number | null;
  annualTurnover?: number | null;
  transactionCostDrag?: number | null;
};

export type BacktestResponse = {
  id: string;
  status: "completed";
  summary: Record<string, string | number>;
  metrics: { strategy: MetricSet };
  series: {
    equityCurve: Array<Record<string, string | number>>;
    drawdown: Array<Record<string, string | number>>;
    monthlyReturns: Array<Record<string, string | number>>;
  };
  comparisons: Array<{
    id: string;
    name: string;
    type: "benchmark" | "mutual_fund";
    metrics: MetricSet;
    monthlyWinRate: number | null;
  }>;
  holdings: Array<{
    rebalanceDate: string;
    turnover: number;
    symbols: Array<{
      symbol: string;
      weight: number;
      compositeScore: number;
      factorScores: Record<string, number>;
    }>;
  }>;
  warnings: Array<{ code: string; message: string }>;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getMetadata() {
  const [universes, factors, benchmarks, mutualFunds] = await Promise.all([
    getJson<{ universes: Universe[] }>("/universes"),
    getJson<{ factors: FactorMeta[] }>("/factors"),
    getJson<{ benchmarks: Benchmark[] }>("/benchmarks"),
    getJson<{ results: MutualFund[] }>("/mutual-funds/search")
  ]);

  return {
    universes: universes.universes,
    factors: factors.factors,
    benchmarks: benchmarks.benchmarks,
    mutualFunds: mutualFunds.results
  };
}

export async function runBacktest(payload: BacktestRequest): Promise<BacktestResponse> {
  const response = await fetch(`${API_BASE}/backtests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail?.message ?? `Backtest failed: ${response.status}`);
  }

  return response.json() as Promise<BacktestResponse>;
}
