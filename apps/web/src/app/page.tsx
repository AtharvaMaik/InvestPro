"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ResultsDashboard } from "@/components/results-dashboard";
import { StrategyBuilder } from "@/components/strategy-builder";
import type { BacktestRequest, BacktestResponse, Benchmark, FactorMeta, MutualFund, StockOption, Universe } from "@/lib/api";
import { getMetadata, runBacktest } from "@/lib/api";

type MetadataState = {
  universes: Universe[];
  factors: FactorMeta[];
  benchmarks: Benchmark[];
  mutualFunds: MutualFund[];
  stocks: StockOption[];
};

export default function Home() {
  const [metadata, setMetadata] = useState<MetadataState | null>(null);
  const [config, setConfig] = useState<BacktestRequest | null>(null);
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activePresetId, setActivePresetId] = useState<string | null>("balanced-compounder");

  useEffect(() => {
    getMetadata()
      .then((data) => {
        setMetadata(data);
        setConfig({
          dataSource: "live",
          universeId: data.universes[0]?.id ?? "nifty50-demo",
          customSymbols: [],
          startDate: "2020-01-01",
          endDate: "2024-12-31",
          rebalanceFrequency: "quarterly",
          weightingMethod: "equal",
          topN: 15,
          transactionCostBps: 25,
          trendFilter: true,
          sectorNeutral: true,
          maxSectorWeight: 0.3,
          maxPositionWeight: 0.08,
          minLiquidityCrore: 1,
          maxAnnualTurnover: 2,
          portfolioCapital: 500000,
          currentHoldings: [],
          factors: data.factors.map((factor) => ({
            id: factor.id,
            weight:
              factor.id === "momentum_6m"
                ? 0.12
                : factor.id === "momentum_12m"
                  ? 0.14
                  : factor.id === "relative_momentum_6m"
                    ? 0.18
                    : factor.id === "drawdown_6m"
                      ? 0.12
                      : factor.id === "trend_200d"
                        ? 0.12
                        : factor.id === "liquidity_3m"
                          ? 0.06
                          : factor.id === "roe"
                          ? 0.1
                          : factor.id === "roce"
                            ? 0.08
                            : factor.id === "debt_to_equity"
                              ? 0.08
                              : factor.id === "earnings_growth"
                                ? 0.04
                                : factor.id === "pe_ratio"
                                  ? 0.03
                                  : factor.id === "pb_ratio"
                                    ? 0.03
                                    : 0
          })),
          benchmarks: [data.benchmarks[0]?.id ?? "nifty50-demo"],
          mutualFunds: [data.mutualFunds[0]?.schemeCode ?? "122639"]
        });
      })
      .catch((loadError: Error) => setError(loadError.message));
  }, []);

  async function handleRun() {
    if (!config) return;
    setIsRunning(true);
    setError(null);
    try {
      setResult(await runBacktest(config));
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Unable to run backtest.");
    } finally {
      setIsRunning(false);
    }
  }

  function handleConfigChange(next: BacktestRequest) {
    setConfig(next);
  }

  return (
    <main className="workspace">
      <nav className="app-topbar" aria-label="Primary navigation">
        <strong>InvestPro</strong>
        <div>
          <span>Live research mode</span>
          <Link href="/guide">Factor guide</Link>
        </div>
      </nav>
      {metadata && config ? (
        <StrategyBuilder
          universes={metadata.universes}
          factors={metadata.factors}
          benchmarks={metadata.benchmarks}
          mutualFunds={metadata.mutualFunds}
          stocks={metadata.stocks}
          config={config}
          activePresetId={activePresetId}
          isRunning={isRunning}
          onChange={handleConfigChange}
          onPresetChange={setActivePresetId}
          onRun={handleRun}
        />
      ) : (
        <aside className="builder-panel skeleton-panel" />
      )}
      <ResultsDashboard result={result} isLoading={isRunning} error={error} />
    </main>
  );
}
