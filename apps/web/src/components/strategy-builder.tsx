"use client";

import type { BacktestRequest, Benchmark, FactorMeta, MutualFund, Universe } from "@/lib/api";

type Props = {
  universes: Universe[];
  factors: FactorMeta[];
  benchmarks: Benchmark[];
  mutualFunds: MutualFund[];
  config: BacktestRequest;
  isRunning: boolean;
  onChange: (config: BacktestRequest) => void;
  onRun: () => void;
};

export function StrategyBuilder({ universes, factors, benchmarks, mutualFunds, config, isRunning, onChange, onRun }: Props) {
  const update = (patch: Partial<BacktestRequest>) => onChange({ ...config, ...patch });
  const activeWeight = config.factors.reduce((sum, factor) => sum + Math.abs(factor.weight), 0);
  const invalid = activeWeight === 0 || config.startDate >= config.endDate;

  function setFactorWeight(id: string, weight: number) {
    update({
      factors: config.factors.map((factor) => (factor.id === id ? { ...factor, weight } : factor))
    });
  }

  return (
    <aside className="builder-panel" aria-label="Strategy builder">
      <div className="panel-heading">
        <span className="eyebrow">Strategy Lab</span>
        <h1>InvestPro</h1>
        <p>Build a long-only Indian equity factor model and compare it with funds.</p>
      </div>

      <label className="field">
        <span>Universe</span>
        <select value={config.universeId} onChange={(event) => update({ universeId: event.target.value })}>
          {universes.map((universe) => (
            <option key={universe.id} value={universe.id}>
              {universe.name} · {universe.symbolCount} stocks
            </option>
          ))}
        </select>
      </label>

      <div className="field-grid">
        <label className="field">
          <span>Start</span>
          <input type="date" value={config.startDate} onChange={(event) => update({ startDate: event.target.value })} />
        </label>
        <label className="field">
          <span>End</span>
          <input type="date" value={config.endDate} onChange={(event) => update({ endDate: event.target.value })} />
        </label>
      </div>

      <div className="segmented" aria-label="Top holdings">
        {[5, 10, 20].map((count) => (
          <button key={count} className={config.topN === count ? "active" : ""} onClick={() => update({ topN: count })} type="button">
            Top {count}
          </button>
        ))}
      </div>

      <label className="field">
        <span>Transaction cost: {config.transactionCostBps} bps</span>
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          value={config.transactionCostBps}
          onChange={(event) => update({ transactionCostBps: Number(event.target.value) })}
        />
      </label>

      <div className="factor-list">
        <div className="section-label">Factors</div>
        {factors.map((factor) => {
          const selected = config.factors.find((entry) => entry.id === factor.id);
          return (
            <label className="factor-row" key={factor.id}>
              <div>
                <strong>{factor.name}</strong>
                <span>{factor.category} · {factor.direction === "higher_is_better" ? "higher better" : "lower better"}</span>
              </div>
              <input
                type="number"
                min="0"
                max="1"
                step="0.05"
                value={selected?.weight ?? 0}
                onChange={(event) => setFactorWeight(factor.id, Number(event.target.value))}
              />
            </label>
          );
        })}
      </div>

      <label className="field">
        <span>Benchmark</span>
        <select value={config.benchmarks[0] ?? ""} onChange={(event) => update({ benchmarks: [event.target.value] })}>
          {benchmarks.map((benchmark) => (
            <option key={benchmark.id} value={benchmark.id}>
              {benchmark.name}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Mutual fund</span>
        <select value={config.mutualFunds[0] ?? ""} onChange={(event) => update({ mutualFunds: [event.target.value] })}>
          {mutualFunds.map((fund) => (
            <option key={fund.schemeCode} value={fund.schemeCode}>
              {fund.schemeName}
            </option>
          ))}
        </select>
      </label>

      <button className="run-button" disabled={isRunning || invalid} onClick={onRun} type="button">
        {isRunning ? "Running backtest" : "Run backtest"}
      </button>

      {invalid ? <p className="inline-error">Use a valid date range and at least one non-zero factor.</p> : null}
    </aside>
  );
}
