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

export type StockOption = {
  symbol: string;
  name: string;
  sector: string;
  source: string;
};

export type CsvImportResult = {
  holdings: Array<{
    symbol: string;
    shares?: number | null;
    averageCost?: number | null;
    value?: number | null;
    notes?: string | null;
    status: "valid" | "warning" | "error";
    message: string;
  }>;
  warnings: Array<{ code: string; message: string }>;
};

export type AuthSession = {
  token: string;
  email: string;
  name: string;
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
  portfolioCapital: number;
  currentHoldings: Array<{ symbol: string; value?: number | null; shares?: number | null; averageCost?: number | null; notes?: string | null }>;
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
    explanation?: StockExplanation;
  }>;
  allocationPlan: Array<{
    symbol: string;
    sector: string;
    targetWeight: number;
    targetValue: number;
    latestPrice: number | null;
    estimatedShares: number | null;
    compositeScore: number;
  }>;
  rebalanceTrades: Array<{
    symbol: string;
    tradeAction: "buy" | "add" | "trim" | "hold" | "exit" | "avoid";
    currentValue: number;
    targetValue: number;
    tradeValue: number;
    latestPrice: number | null;
    estimatedShares: number | null;
    reason: string;
  }>;
  portfolioSummary: {
    cashValue: number;
    currentValue: number;
    investedValue: number;
    costBasis: number | null;
    unrealizedPnl: number | null;
    unrealizedPnlPercent: number | null;
    holdingCount: number;
    holdings: TrackedHolding[];
  };
  trackedHoldings: TrackedHolding[];
  executionChecklist: Array<{ name: string; status: "pass" | "block"; detail: string }>;
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

export type TrackedHolding = {
  symbol: string;
  sector?: string;
  shares?: number | null;
  averageCost?: number | null;
  latestPrice?: number | null;
  currentValue: number;
  currentValueSource?: string;
  costBasis?: number | null;
  unrealizedPnl?: number | null;
  unrealizedPnlPercent?: number | null;
  currentWeight: number;
  targetWeight?: number;
  targetValue?: number;
  drift?: number;
  driftValue?: number;
  notes?: string | null;
};

export type StockExplanation = {
  symbol: string;
  headline: string;
  positives: FactorContribution[];
  negatives: FactorContribution[];
  factorContributions: FactorContribution[];
  warnings: Array<{ code: string; message: string }>;
};

export type FactorContribution = {
  factorId: string;
  score: number;
  weight: number;
  weightedContribution: number;
  direction: "positive" | "negative";
};

export type JournalSymbol = {
  symbol: string;
  sector: string;
  compositeScore: number;
  reason: string;
  topFactors: Array<{ factorId: string; score: number }>;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? (process.env.NODE_ENV === "production" ? "/api" : "http://localhost:8000");

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getMetadata(source: "demo" | "live" = "live") {
  const [universes, factors, benchmarks, mutualFunds, stocks] = await Promise.all([
    getJson<{ universes: Universe[] }>("/universes"),
    getJson<{ factors: FactorMeta[] }>("/factors"),
    getJson<{ benchmarks: Benchmark[] }>("/benchmarks"),
    getJson<{ results: MutualFund[] }>(`/mutual-funds/search?source=${source}`),
    getJson<{ stocks: StockOption[] }>("/stocks")
  ]);

  return {
    universes: universes.universes,
    factors: factors.factors,
    benchmarks: benchmarks.benchmarks,
    mutualFunds: mutualFunds.results,
    stocks: stocks.stocks
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

export async function importPortfolioCsv(csvText: string): Promise<CsvImportResult> {
  const response = await fetch(`${API_BASE}/portfolios/import-csv`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ csvText })
  });
  if (!response.ok) {
    throw new Error(`CSV import failed: ${response.status}`);
  }
  return response.json() as Promise<CsvImportResult>;
}

export async function exportTradesCsv(trades: BacktestResponse["rebalanceTrades"]): Promise<string> {
  const response = await fetch(`${API_BASE}/backtests/export-trades-csv`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ trades })
  });
  if (!response.ok) {
    throw new Error(`Trade export failed: ${response.status}`);
  }
  return response.text();
}

export async function login(email: string, name: string): Promise<AuthSession> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, name })
  });
  if (!response.ok) {
    throw new Error("Sign in failed.");
  }
  return response.json() as Promise<AuthSession>;
}

export async function getMe(token: string): Promise<Omit<AuthSession, "token">> {
  const response = await fetch(`${API_BASE}/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error("Session expired.");
  }
  return response.json() as Promise<Omit<AuthSession, "token">>;
}
