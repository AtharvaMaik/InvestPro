"use client";

import { motion } from "framer-motion";
import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { InfoButton } from "@/components/info-button";
import type { BacktestResponse, MetricSet } from "@/lib/api";
import { glossary } from "@/lib/glossary";

type Props = {
  result: BacktestResponse | null;
  isLoading: boolean;
  error: string | null;
};

const percentMetrics: Array<[keyof MetricSet, string, string]> = [
  ["cagr", "CAGR", glossary.cagr],
  ["total_return", "Total return", glossary.totalReturn],
  ["volatility", "Volatility", glossary.volatility],
  ["max_drawdown", "Max drawdown", glossary.maxDrawdown],
  ["annualTurnover", "Annual turnover", glossary.turnover],
  ["transactionCostDrag", "Cost drag", glossary.costDrag]
];

const ratioMetrics: Array<[keyof MetricSet, string, string]> = [
  ["sharpe", "Sharpe", glossary.sharpe],
  ["sortino", "Sortino", glossary.sortino],
  ["calmar", "Calmar", glossary.calmar]
];

export function ResultsDashboard({ result, isLoading, error }: Props) {
  if (isLoading) {
    return (
      <section className="results-grid">
        <div className="skeleton hero-skeleton" />
        <div className="skeleton chart-skeleton" />
        <div className="skeleton chart-skeleton" />
      </section>
    );
  }

  if (error) {
    return (
      <section className="empty-state error-state">
        <span className="eyebrow">Backtest failed</span>
        <h2>{error}</h2>
        <p>Review the strategy inputs or confirm the API is running on port 8000.</p>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="empty-state">
        <span className="eyebrow">Ready</span>
        <h2>Run the default factor model to generate the first research report.</h2>
        <p>The demo uses seeded Indian equity data so the full workflow works before live data integrations.</p>
      </section>
    );
  }

  const latestHoldings = result.holdings.at(-1)?.symbols ?? [];
  const mutualFundKey = result.comparisons.find((item) => item.type === "mutual_fund")?.id;

  return (
    <motion.section className="results-grid" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
      <div className="metrics-grid">
        {percentMetrics.map(([key, label, description]) => (
          <MetricCard key={key} description={description} label={label} value={formatPercent(result.metrics.strategy[key])} />
        ))}
        {ratioMetrics.map(([key, label, description]) => (
          <MetricCard key={key} description={description} label={label} value={formatNumber(result.metrics.strategy[key])} />
        ))}
      </div>

      <div className="chart-panel wide">
        <div className="panel-title">
          <h2 className="label-with-info">Equity Curve <InfoButton label="equity curve" description={glossary.equityCurve} /></h2>
          <span>{result.summary.tradingDays} trading days</span>
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={result.series.equityCurve}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e7ef" />
            <XAxis dataKey="date" minTickGap={42} />
            <YAxis tickFormatter={(value) => `${Number(value).toFixed(1)}x`} />
            <Tooltip formatter={(value) => Number(value).toFixed(3)} />
            <Line type="monotone" dataKey="strategy" stroke="#0f766e" strokeWidth={3} dot={false} />
            <Line type="monotone" dataKey="nifty50-demo" stroke="#64748b" strokeWidth={2} dot={false} />
            {mutualFundKey ? <Line type="monotone" dataKey={mutualFundKey} stroke="#7c3aed" strokeWidth={2} dot={false} /> : null}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-panel">
        <div className="panel-title">
          <h2 className="label-with-info">Drawdown <InfoButton label="drawdown" description={glossary.drawdown} /></h2>
          <span>Peak-to-trough risk</span>
        </div>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={result.series.drawdown}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e7ef" />
            <XAxis dataKey="date" minTickGap={50} />
            <YAxis tickFormatter={(value) => formatPercent(Number(value))} />
            <Tooltip formatter={(value) => formatPercent(Number(value))} />
            <Area type="monotone" dataKey="strategy" stroke="#dc2626" fill="#fecaca" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-panel">
        <div className="panel-title">
          <h2 className="label-with-info">Comparisons <InfoButton label="comparisons" description={glossary.comparisons} /></h2>
          <span>Funds and benchmark</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>CAGR</th>
                <th>Sharpe</th>
                <th>Win rate</th>
              </tr>
            </thead>
            <tbody>
              {result.comparisons.map((comparison) => (
                <tr key={comparison.id}>
                  <td>{comparison.name}</td>
                  <td>{formatPercent(comparison.metrics.cagr)}</td>
                  <td>{formatNumber(comparison.metrics.sharpe)}</td>
                  <td>{formatPercent(comparison.monthlyWinRate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="chart-panel wide">
        <div className="panel-title">
          <h2 className="label-with-info">Latest Holdings <InfoButton label="holdings" description={glossary.holdings} /></h2>
          <span>{latestHoldings.length} positions</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Weight</th>
                <th>Composite</th>
                <th>Momentum 6M</th>
              </tr>
            </thead>
            <tbody>
              {latestHoldings.map((holding) => (
                <tr key={holding.symbol}>
                  <td>{holding.symbol}</td>
                  <td>{formatPercent(holding.weight)}</td>
                  <td>{formatNumber(holding.compositeScore)}</td>
                  <td>{formatNumber(holding.factorScores.momentum_6m)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="chart-panel wide">
        <div className="panel-title">
          <h2 className="label-with-info">Factor Diagnostics <InfoButton label="factor diagnostics" description={glossary.factorDiagnostics} /></h2>
          <span>Top bucket vs bottom bucket</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Factor</th>
                <th>Spread</th>
                <th>Hit rate</th>
                <th>Top avg</th>
                <th>Bottom avg</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {result.factorDiagnostics.map((diagnostic) => (
                <tr key={diagnostic.factorId}>
                  <td>{formatFactorName(diagnostic.factorId)}</td>
                  <td>{formatPercent(diagnostic.averageSpread)}</td>
                  <td>{formatPercent(diagnostic.hitRate)}</td>
                  <td>{formatPercent(diagnostic.averageTopReturn)}</td>
                  <td>{formatPercent(diagnostic.averageBottomReturn)}</td>
                  <td><span className={`evidence-pill ${diagnostic.evidence}`}>{diagnostic.evidence}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="chart-panel wide">
        <div className="panel-title">
          <h2 className="label-with-info">Robustness Check <InfoButton label="robustness" description={glossary.robustness} /></h2>
          <span>Assumption stress</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Scenario</th>
                <th>Top N</th>
                <th>Cost</th>
                <th>Rebalance</th>
                <th>CAGR</th>
                <th>Max DD</th>
              </tr>
            </thead>
            <tbody>
              {result.robustness.map((scenario) => (
                <tr key={scenario.scenario}>
                  <td>{scenario.scenario}</td>
                  <td>{scenario.topN}</td>
                  <td>{scenario.transactionCostBps} bps</td>
                  <td>{scenario.rebalanceFrequency}</td>
                  <td>{formatPercent(scenario.cagr)}</td>
                  <td>{formatPercent(scenario.maxDrawdown)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {result.warnings.length ? (
        <div className="warnings">
          {result.warnings.map((warning, index) => (
            <p key={`${warning.code}-${index}`}>{warning.message}</p>
          ))}
        </div>
      ) : null}
    </motion.section>
  );
}

function MetricCard({ description, label, value }: { description: string; label: string; value: string }) {
  return (
    <article className="metric-card">
      <span className="label-with-info">{label} <InfoButton label={label} description={description} /></span>
      <strong>{value}</strong>
    </article>
  );
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return `${(value * 100).toFixed(1)}%`;
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return value.toFixed(2);
}

function formatFactorName(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
