"use client";

import type { BacktestRequest, Benchmark, FactorMeta, MutualFund, Universe } from "@/lib/api";
import { InfoButton } from "@/components/info-button";
import { glossary } from "@/lib/glossary";
import { applyPreset, strategyPresets } from "@/lib/presets";

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
        <p>Run live Indian equity factor presets and inspect stock-level research actions.</p>
      </div>

      <div className="live-badge">Live data only</div>

      <div className="preset-grid" aria-label="Strategy presets">
        {strategyPresets.map((preset) => (
          <button key={preset.id} type="button" onClick={() => onChange(applyPreset(config, preset))}>
            <strong>{preset.name}</strong>
            <span>{preset.risk}</span>
            <p>{preset.description}</p>
          </button>
        ))}
      </div>

      <label className="field">
        <span className="label-with-info">
          Universe <InfoButton label="universe" description={glossary.universe} />
        </span>
        <select value={config.universeId} onChange={(event) => update({ universeId: event.target.value })}>
          {universes.map((universe) => (
            <option key={universe.id} value={universe.id}>
              {universe.name} - {universe.symbolCount} stocks
            </option>
          ))}
        </select>
      </label>

      <div className="field-grid">
        <label className="field">
          <span className="label-with-info">
            Start <InfoButton label="date range" description={glossary.dateRange} />
          </span>
          <input type="date" value={config.startDate} onChange={(event) => update({ startDate: event.target.value })} />
        </label>
        <label className="field">
          <span className="label-with-info">
            End <InfoButton label="date range" description={glossary.dateRange} />
          </span>
          <input type="date" value={config.endDate} onChange={(event) => update({ endDate: event.target.value })} />
        </label>
      </div>

      <div className="segmented" aria-label="Top holdings">
        {[5, 10, 15, 20, 30].map((count) => (
          <button key={count} className={config.topN === count ? "active" : ""} onClick={() => update({ topN: count })} type="button">
            Top {count}
          </button>
        ))}
      </div>

      <label className="field">
        <span className="label-with-info">
          Rebalance <InfoButton label="rebalance frequency" description={glossary.rebalanceFrequency} />
        </span>
        <select
          value={config.rebalanceFrequency}
          onChange={(event) => update({ rebalanceFrequency: event.target.value as "monthly" | "quarterly" })}
        >
          <option value="monthly">Monthly</option>
          <option value="quarterly">Quarterly</option>
        </select>
      </label>

      <label className="field">
        <span className="label-with-info">
          Weighting <InfoButton label="weighting method" description={glossary.weightingMethod} />
        </span>
        <select
          value={config.weightingMethod}
          onChange={(event) => update({ weightingMethod: event.target.value as "equal" | "score" | "volatility" })}
        >
          <option value="equal">Equal weight</option>
          <option value="score">Score weighted</option>
          <option value="volatility">Volatility scaled</option>
        </select>
      </label>

      <label className="field">
        <span className="label-with-info">
          Transaction cost: {config.transactionCostBps} bps <InfoButton label="transaction cost" description={glossary.transactionCost} />
        </span>
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          value={config.transactionCostBps}
          onChange={(event) => update({ transactionCostBps: Number(event.target.value) })}
        />
      </label>

      <div className="control-stack">
        <label className="toggle-row">
          <input type="checkbox" checked={config.trendFilter} onChange={(event) => update({ trendFilter: event.target.checked })} />
          <span className="label-with-info">
            200D trend filter <InfoButton label="trend filter" description={glossary.trendFilter} />
          </span>
        </label>
        <label className="toggle-row">
          <input type="checkbox" checked={config.sectorNeutral} onChange={(event) => update({ sectorNeutral: event.target.checked })} />
          <span className="label-with-info">
            Sector cap <InfoButton label="sector cap" description={glossary.sectorNeutral} />
          </span>
        </label>
        <label className="field compact-field">
          <span className="label-with-info">
            Max sector weight: {(config.maxSectorWeight * 100).toFixed(0)}% <InfoButton label="max sector weight" description={glossary.maxSectorWeight} />
          </span>
          <input
            type="range"
            min="0.15"
            max="0.6"
            step="0.05"
            value={config.maxSectorWeight}
            disabled={!config.sectorNeutral}
            onChange={(event) => update({ maxSectorWeight: Number(event.target.value) })}
          />
        </label>
        <label className="field compact-field">
          <span className="label-with-info">
            Max stock weight: {(config.maxPositionWeight * 100).toFixed(0)}% <InfoButton label="max stock weight" description={glossary.maxPositionWeight} />
          </span>
          <input
            type="range"
            min="0.03"
            max="0.25"
            step="0.01"
            value={config.maxPositionWeight}
            onChange={(event) => update({ maxPositionWeight: Number(event.target.value) })}
          />
        </label>
        <label className="field compact-field">
          <span className="label-with-info">
            Min liquidity: {config.minLiquidityCrore} cr <InfoButton label="minimum liquidity" description={glossary.minLiquidity} />
          </span>
          <input
            type="range"
            min="0"
            max="50"
            step="1"
            value={config.minLiquidityCrore}
            onChange={(event) => update({ minLiquidityCrore: Number(event.target.value) })}
          />
        </label>
        <label className="field compact-field">
          <span className="label-with-info">
            Turnover budget: {(config.maxAnnualTurnover * 100).toFixed(0)}% <InfoButton label="turnover budget" description={glossary.maxAnnualTurnover} />
          </span>
          <input
            type="range"
            min="0.5"
            max="5"
            step="0.25"
            value={config.maxAnnualTurnover}
            onChange={(event) => update({ maxAnnualTurnover: Number(event.target.value) })}
          />
        </label>
      </div>

      <div className="factor-list">
        <div className="section-label label-with-info">
          Factors <InfoButton label="factors" description={glossary.factors} />
        </div>
        {factors.map((factor) => {
          const selected = config.factors.find((entry) => entry.id === factor.id);
          return (
            <label className="factor-row" key={factor.id}>
              <div>
                <strong>{factor.name}</strong>
                <span>{factor.category} - {factor.direction === "higher_is_better" ? "higher better" : "lower better"}</span>
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
        <span className="label-with-info">
          Benchmark <InfoButton label="benchmark" description={glossary.benchmark} />
        </span>
        <select value={config.benchmarks[0] ?? ""} onChange={(event) => update({ benchmarks: [event.target.value] })}>
          {benchmarks.map((benchmark) => (
            <option key={benchmark.id} value={benchmark.id}>
              {benchmark.name}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span className="label-with-info">
          Mutual fund <InfoButton label="mutual fund" description={glossary.mutualFund} />
        </span>
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
