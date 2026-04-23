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
  dataSource: "demo" | "live";
  universeId: string;
  customSymbols: string[];
  startDate: string;
  endDate: string;
  rebalanceFrequency: "monthly" | "quarterly";
  weightingMethod: "equal" | "score" | "volatility";
  topN: number;
  transactionCostBps: number;
  trendFilter: boolean;
  sectorNeutral: boolean;
  maxSectorWeight: number;
  maxPositionWeight: number;
  minLiquidityCrore: number;
  maxAnnualTurnover: number;
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
    rollingReturns: {
      oneYear: Array<Record<string, string | number>>;
      threeYear: Array<Record<string, string | number>>;
      fiveYear: Array<Record<string, string | number>>;
    };
    monthlyReturns: Array<Record<string, string | number>>;
  };
  comparisons: Array<{
    id: string;
    name: string;
    type: "benchmark" | "mutual_fund";
    category: string | null;
    metrics: MetricSet;
    monthlyWinRate: number | null;
  }>;
  factorDiagnostics: Array<{
    factorId: string;
    observations: number;
    averageTopReturn: number;
    averageBottomReturn: number;
    averageSpread: number;
    hitRate: number;
    evidence: "strong" | "mixed" | "weak";
  }>;
  robustness: Array<{
    scenario: string;
    topN: number;
    transactionCostBps: number;
    rebalanceFrequency: string;
    cagr: number | null;
    maxDrawdown: number | null;
  }>;
  sectorExposure: Array<{
    sector: string;
    weight: number;
    positions: number;
  }>;
  fundCategoryComparison: Array<{
    category: string;
    fundCount: number;
    averageCagr: number | null;
    averageSharpe: number | null;
    averageMaxDrawdown: number | null;
    averageMonthlyWinRate: number | null;
  }>;
  rollingAnalysis: {
    positiveMonthRate?: number | null;
    oneYearAverageReturn?: number | null;
    oneYearWinRate?: number | null;
  };
  walkForward: {
    status?: string;
    method?: string;
    train?: { startDate: string; endDate: string; metrics: MetricSet };
    test?: { startDate: string; endDate: string; metrics: MetricSet };
    degradation?: { cagr: number | null; maxDrawdown: number | null };
  };
  dataConfidence: {
    level: "high" | "medium" | "low";
    score: number;
    priceCoverage: number;
    fundamentalCoverage: number;
    factorCoverage: number;
    source: "demo" | "live";
    missingSymbols: string[];
    warningCodes: string[];
  };
  investability: {
    verdict: "investable" | "watch" | "not_investable";
    checks: Array<{ name: string; status: "pass" | "fail"; detail: string }>;
  };
  riskBudget: {
    riskLevel: "conservative" | "balanced" | "aggressive" | "speculative";
    volatility: number;
    benchmarkVolatility: number | null;
    maxDrawdown: number;
    maxSectorWeight: number;
    notes: string[];
  };
  researchVerdict: {
    status: "pass" | "watch" | "reject";
    reasons: string[];
  };
  rebalanceJournal: Array<{
    rebalanceDate: string;
    turnover: number;
    added: Array<JournalSymbol>;
    removed: Array<{ symbol: string; reason: string }>;
    retained: Array<JournalSymbol>;
  }>;
  actionList: Array<{
    symbol: string;
    sector: string;
    action: "buy_candidate" | "hold" | "review" | "avoid";
    weight: number;
    compositeScore: number;
    reason: string;
  }>;
  holdings: Array<{
    rebalanceDate: string;
    turnover: number;
    symbols: Array<{
      symbol: string;
      sector?: string;
      weight: number;
      compositeScore: number;
      factorScores: Record<string, number>;
    }>;
  }>;
  warnings: Array<{ code: string; message: string }>;
};

export type JournalSymbol = {
  symbol: string;
  sector: string;
  compositeScore: number;
  reason: string;
  topFactors: Array<{ factorId: string; score: number }>;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getMetadata(source: "demo" | "live" = "live") {
  const [universes, factors, benchmarks, mutualFunds] = await Promise.all([
    getJson<{ universes: Universe[] }>("/universes"),
    getJson<{ factors: FactorMeta[] }>("/factors"),
    getJson<{ benchmarks: Benchmark[] }>("/benchmarks"),
    getJson<{ results: MutualFund[] }>(`/mutual-funds/search?source=${source}`)
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
