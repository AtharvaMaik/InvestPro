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
          universeId: data.universes[0]?.id ?? "nifty50-demo",
          customSymbols: [],
          startDate: "2020-01-01",
          endDate: "2024-12-31",
          rebalanceFrequency: "monthly",
          topN: 5,
          transactionCostBps: 25,
          factors: data.factors.map((factor, index) => ({
            id: factor.id,
            weight: index < 2 ? 0.5 : factor.id === "volatility_6m" ? 0.25 : 0
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
          onChange={setConfig}
          onRun={handleRun}
        />
      ) : (
        <aside className="builder-panel skeleton-panel" />
      )}
      <ResultsDashboard result={result} isLoading={isRunning} error={error} />
    </main>
  );
}
