"use client";

import { useEffect, useState } from "react";

import { ResultsDashboard } from "@/components/results-dashboard";
import { StrategyBuilder } from "@/components/strategy-builder";
import type { BacktestRequest, BacktestResponse, Benchmark, FactorMeta, MutualFund, Universe } from "@/lib/api";
import { getMetadata, runBacktest } from "@/lib/api";

type MetadataState = {
  universes: Universe[];
  factors: FactorMeta[];
  benchmarks: Benchmark[];
  mutualFunds: MutualFund[];
};

export default function Home() {
  const [metadata, setMetadata] = useState<MetadataState | null>(null);
  const [config, setConfig] = useState<BacktestRequest | null>(null);
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMetadata()
      .then((data) => {
        setMetadata(data);
        setConfig({
          dataSource: "demo",
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
          factors: data.factors.map((factor) => ({
            id: factor.id,
            weight:
              factor.id === "momentum_6m"
                ? 0.2
                : factor.id === "momentum_12m"
                  ? 0.15
                  : factor.id === "relative_momentum_6m"
                    ? 0.15
                    : factor.id === "drawdown_6m"
                      ? 0.1
                      : factor.id === "trend_200d"
                        ? 0.1
                        : factor.id === "roe"
                          ? 0.1
                          : factor.id === "roce"
                            ? 0.08
                            : factor.id === "debt_to_equity"
                              ? 0.07
                              : factor.id === "earnings_growth"
                                ? 0.05
                                : factor.id === "pe_ratio"
                                  ? 0.05
                                  : factor.id === "pb_ratio"
                                    ? 0.05
                                    : 0
          })),
          benchmarks: [data.benchmarks[0]?.id ?? "nifty50-demo"],
          mutualFunds: [data.mutualFunds[0]?.schemeCode ?? "ppfas-flexi-demo"]
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
    const previousSource = config?.dataSource;
    setConfig(next);

    if (previousSource && next.dataSource !== previousSource) {
      getMetadata(next.dataSource)
        .then((data) => {
          setMetadata(data);
          setConfig((current) =>
            current
              ? {
                  ...current,
                  mutualFunds: [data.mutualFunds[0]?.schemeCode ?? current.mutualFunds[0]],
                  benchmarks: [data.benchmarks[0]?.id ?? current.benchmarks[0]]
                }
              : current
          );
        })
        .catch((loadError: Error) => setError(loadError.message));
    }
  }

  return (
    <main className="workspace">
      {metadata && config ? (
        <StrategyBuilder
          universes={metadata.universes}
          factors={metadata.factors}
          benchmarks={metadata.benchmarks}
          mutualFunds={metadata.mutualFunds}
          config={config}
          isRunning={isRunning}
          onChange={handleConfigChange}
          onRun={handleRun}
        />
      ) : (
        <aside className="builder-panel skeleton-panel" />
      )}
      <ResultsDashboard result={result} isLoading={isRunning} error={error} />
    </main>
  );
}
