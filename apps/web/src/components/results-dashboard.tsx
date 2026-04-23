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
  const latestJournal = result.rebalanceJournal.at(-1);
  const tradeTimeline = result.rebalanceJournal.filter((entry) => entry.added.length > 0 || entry.removed.length > 0).slice(-12);
  const finalSummary = buildFinalSummary(result);

  return (
    <motion.section className="results-grid" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
      <div className={`verdict-panel ${result.researchVerdict.status}`}>
        <div>
          <span className="eyebrow label-with-info">Research Verdict <InfoButton label="research verdict" description={glossary.researchVerdict} /></span>
          <h2>{formatVerdict(result.researchVerdict.status)}</h2>
        </div>
        <div className="verdict-reasons">
          {result.researchVerdict.reasons.map((reason) => (
            <p key={reason}>{reason}</p>
          ))}
        </div>
      </div>

      <div className="final-summary-panel">
        <div>
          <span className="eyebrow">Final Summary</span>
          <h2>{finalSummary.headline}</h2>
          <p>{finalSummary.body}</p>
        </div>
        <ol>
          {finalSummary.steps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </div>

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
          <h2>Preset Action List</h2>
          <span>Latest stock research actions</span>
        </div>
        <div className="action-grid">
          {result.actionList.map((item) => (
            <article className={`action-card ${item.action}`} key={item.symbol}>
              <div>
                <strong>{item.symbol}</strong>
                <span>{item.sector}</span>
              </div>
              <b>{formatAction(item.action)}</b>
              <p>{item.reason}</p>
              <small>{formatPercent(item.weight)} target weight - score {formatNumber(item.compositeScore)}</small>
            </article>
          ))}
        </div>
      </div>

      <div className="chart-panel wide">
        <div className="panel-title">
          <h2 className="label-with-info">Buy/Sell Timeline <InfoButton label="rebalance timeline" description={glossary.rebalanceJournal} /></h2>
          <span>{tradeTimeline.length} recent rebalance events</span>
        </div>
        {tradeTimeline.length ? <TradeTimeline rows={tradeTimeline} /> : <p>No buys or sells were generated in this run.</p>}
      </div>

      <div className="chart-panel wide">
        <div className="panel-title">
          <h2>V4 Rebalance Trades</h2>
          <span>Target allocation vs current holdings</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Action</th>
                <th>Current</th>
                <th>Target</th>
                <th>Trade</th>
                <th>Shares</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {result.rebalanceTrades.map((trade) => (
                <tr key={`${trade.symbol}-${trade.tradeAction}`}>
                  <td>{trade.symbol}</td>
                  <td><span className={`trade-pill ${trade.tradeAction}`}>{formatTradeAction(trade.tradeAction)}</span></td>
                  <td>{formatCurrency(trade.currentValue)}</td>
                  <td>{formatCurrency(trade.targetValue)}</td>
                  <td>{formatCurrency(trade.tradeValue)}</td>
                  <td>{trade.estimatedShares ? trade.estimatedShares.toFixed(2) : "n/a"}</td>
                  <td>{trade.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="chart-panel">
        <div className="panel-title">
          <h2>Allocation Plan</h2>
          <span>Target rupee sizing</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Weight</th>
                <th>Target</th>
                <th>Price</th>
                <th>Shares</th>
              </tr>
            </thead>
            <tbody>
              {result.allocationPlan.map((row) => (
                <tr key={row.symbol}>
                  <td>{row.symbol}</td>
                  <td>{formatPercent(row.targetWeight)}</td>
                  <td>{formatCurrency(row.targetValue)}</td>
                  <td>{formatCurrency(row.latestPrice)}</td>
                  <td>{row.estimatedShares ? row.estimatedShares.toFixed(2) : "n/a"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="chart-panel">
        <div className="panel-title">
          <h2>Execution Checklist</h2>
          <span>Before any action</span>
        </div>
        <div className="check-list">
          {result.executionChecklist.map((check) => (
            <div className={`check-row ${check.status === "pass" ? "pass" : "fail"}`} key={check.name}>
              <strong>{check.status}</strong>
              <span>{formatFactorName(check.name)}</span>
              <p>{check.detail}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="chart-panel">
        <div className="panel-title">
          <h2 className="label-with-info">Fund Categories <InfoButton label="fund categories" description={glossary.fundCategories} /></h2>
          <span>{result.fundCategoryComparison.length} groups</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Funds</th>
                <th>Avg CAGR</th>
                <th>Avg Sharpe</th>
                <th>Avg Max DD</th>
                <th>Win rate</th>
              </tr>
            </thead>
            <tbody>
              {result.fundCategoryComparison.map((category) => (
                <tr key={category.category}>
                  <td>{category.category}</td>
                  <td>{category.fundCount}</td>
                  <td>{formatPercent(category.averageCagr)}</td>
                  <td>{formatNumber(category.averageSharpe)}</td>
                  <td>{formatPercent(category.averageMaxDrawdown)}</td>
                  <td>{formatPercent(category.averageMonthlyWinRate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="chart-panel">
        <div className="panel-title">
          <h2 className="label-with-info">Sector Exposure <InfoButton label="sector exposure" description={glossary.sectorExposure} /></h2>
          <span>Latest rebalance</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Sector</th>
                <th>Weight</th>
                <th>Positions</th>
              </tr>
            </thead>
            <tbody>
              {result.sectorExposure.map((sector) => (
                <tr key={sector.sector}>
                  <td>{sector.sector}</td>
                  <td>{formatPercent(sector.weight)}</td>
                  <td>{sector.positions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="chart-panel">
        <div className="panel-title">
          <h2 className="label-with-info">Rolling Edge <InfoButton label="rolling analysis" description={glossary.rollingAnalysis} /></h2>
          <span>{result.series.rollingReturns.oneYear.length} one-year points</span>
        </div>
        <div className="mini-metrics">
          <div><span>Positive months</span><strong>{formatPercent(result.rollingAnalysis.positiveMonthRate)}</strong></div>
          <div><span>Avg 1Y return</span><strong>{formatPercent(result.rollingAnalysis.oneYearAverageReturn)}</strong></div>
          <div><span>Best fund win rate</span><strong>{formatPercent(result.rollingAnalysis.oneYearWinRate)}</strong></div>
        </div>
      </div>

      <div className="chart-panel">
        <div className="panel-title">
          <h2 className="label-with-info">Walk-Forward <InfoButton label="walk-forward" description={glossary.walkForward} /></h2>
          <span>{result.walkForward.status ?? "n/a"}</span>
        </div>
        {result.walkForward.train && result.walkForward.test ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Period</th>
                  <th>Dates</th>
                  <th>CAGR</th>
                  <th>Sharpe</th>
                  <th>Max DD</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Train</td>
                  <td>{result.walkForward.train.startDate} to {result.walkForward.train.endDate}</td>
                  <td>{formatPercent(result.walkForward.train.metrics.cagr)}</td>
                  <td>{formatNumber(result.walkForward.train.metrics.sharpe)}</td>
                  <td>{formatPercent(result.walkForward.train.metrics.max_drawdown)}</td>
                </tr>
                <tr>
                  <td>Test</td>
                  <td>{result.walkForward.test.startDate} to {result.walkForward.test.endDate}</td>
                  <td>{formatPercent(result.walkForward.test.metrics.cagr)}</td>
                  <td>{formatNumber(result.walkForward.test.metrics.sharpe)}</td>
                  <td>{formatPercent(result.walkForward.test.metrics.max_drawdown)}</td>
                </tr>
                <tr>
                  <td>Change</td>
                  <td>Out-of-sample minus train</td>
                  <td>{formatPercent(result.walkForward.degradation?.cagr)}</td>
                  <td>n/a</td>
                  <td>{formatPercent(result.walkForward.degradation?.maxDrawdown)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        ) : (
          <p>Not enough history for a walk-forward split.</p>
        )}
      </div>

      <div className="chart-panel">
        <div className="panel-title">
          <h2 className="label-with-info">Data Confidence <InfoButton label="data confidence" description={glossary.dataConfidence} /></h2>
          <span>{result.dataConfidence.level}</span>
        </div>
        <div className="mini-metrics">
          <div><span>Confidence</span><strong>{formatPercent(result.dataConfidence.score)}</strong></div>
          <div><span>Prices</span><strong>{formatPercent(result.dataConfidence.priceCoverage)}</strong></div>
          <div><span>Fundamentals</span><strong>{formatPercent(result.dataConfidence.fundamentalCoverage)}</strong></div>
          <div><span>Factors</span><strong>{formatPercent(result.dataConfidence.factorCoverage)}</strong></div>
        </div>
      </div>

      <div className="chart-panel">
        <div className="panel-title">
          <h2 className="label-with-info">Investability <InfoButton label="investability" description={glossary.investability} /></h2>
          <span>{result.investability.verdict.replace("_", " ")}</span>
        </div>
        <div className="check-list">
          {result.investability.checks.map((check) => (
            <div className={`check-row ${check.status}`} key={check.name}>
              <strong>{check.status}</strong>
              <span>{formatFactorName(check.name)}</span>
              <p>{check.detail}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="chart-panel">
        <div className="panel-title">
          <h2 className="label-with-info">Risk Budget <InfoButton label="risk budget" description={glossary.riskBudget} /></h2>
          <span>{result.riskBudget.riskLevel}</span>
        </div>
        <div className="mini-metrics">
          <div><span>Strategy vol</span><strong>{formatPercent(result.riskBudget.volatility)}</strong></div>
          <div><span>Benchmark vol</span><strong>{formatPercent(result.riskBudget.benchmarkVolatility)}</strong></div>
          <div><span>Max DD</span><strong>{formatPercent(result.riskBudget.maxDrawdown)}</strong></div>
          <div><span>Largest sector</span><strong>{formatPercent(result.riskBudget.maxSectorWeight)}</strong></div>
        </div>
      </div>

      <div className="chart-panel">
        <div className="panel-title">
          <h2 className="label-with-info">Rebalance Journal <InfoButton label="rebalance journal" description={glossary.rebalanceJournal} /></h2>
          <span>{latestJournal?.rebalanceDate ?? "n/a"}</span>
        </div>
        {latestJournal ? (
          <div className="journal-grid">
            <JournalColumn title="Added" rows={latestJournal.added.map((item) => ({ symbol: item.symbol, detail: item.reason }))} />
            <JournalColumn title="Removed" rows={latestJournal.removed.map((item) => ({ symbol: item.symbol, detail: item.reason }))} />
            <JournalColumn title="Retained" rows={latestJournal.retained.slice(0, 5).map((item) => ({ symbol: item.symbol, detail: item.reason }))} />
          </div>
        ) : (
          <p>No rebalance journal is available.</p>
        )}
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
                <th>Sector</th>
                <th>Weight</th>
                <th>Composite</th>
                <th>Momentum 6M</th>
              </tr>
            </thead>
            <tbody>
              {latestHoldings.map((holding) => (
                <tr key={holding.symbol}>
                  <td>{holding.symbol}</td>
                  <td>{holding.sector ?? "Unknown"}</td>
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

function JournalColumn({ title, rows }: { title: string; rows: Array<{ symbol: string; detail: string }> }) {
  return (
    <div className="journal-column">
      <strong>{title}</strong>
      {rows.length ? rows.map((row) => (
        <div key={`${title}-${row.symbol}`}>
          <span>{row.symbol}</span>
          <p>{row.detail}</p>
        </div>
      )) : <p>No names</p>}
    </div>
  );
}

function TradeTimeline({ rows }: { rows: BacktestResponse["rebalanceJournal"] }) {
  return (
    <div className="trade-timeline">
      {rows.map((row) => (
        <article className="timeline-event" key={row.rebalanceDate}>
          <time dateTime={row.rebalanceDate}>{row.rebalanceDate}</time>
          <div className="timeline-body">
            <div>
              <strong>Bought</strong>
              <div className="timeline-chips">
                {row.added.length ? (
                  row.added.slice(0, 6).map((item) => (
                    <span className="timeline-chip buy" key={`buy-${row.rebalanceDate}-${item.symbol}`}>
                      {item.symbol}
                    </span>
                  ))
                ) : (
                  <span className="timeline-empty">No buys</span>
                )}
              </div>
            </div>
            <div>
              <strong>Sold</strong>
              <div className="timeline-chips">
                {row.removed.length ? (
                  row.removed.slice(0, 6).map((item) => (
                    <span className="timeline-chip sell" key={`sell-${row.rebalanceDate}-${item.symbol}`} title={item.reason}>
                      {item.symbol}
                    </span>
                  ))
                ) : (
                  <span className="timeline-empty">No sells</span>
                )}
              </div>
            </div>
          </div>
        </article>
      ))}
    </div>
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

function formatVerdict(value: "pass" | "watch" | "reject") {
  if (value === "pass") return "Research Pass";
  if (value === "watch") return "Watch Closely";
  return "Reject For Now";
}

function formatAction(value: "buy_candidate" | "hold" | "review" | "avoid") {
  if (value === "buy_candidate") return "Buy Candidate";
  if (value === "hold") return "Hold";
  if (value === "avoid") return "Avoid";
  return "Review";
}

function formatTradeAction(value: "buy" | "add" | "trim" | "hold" | "exit" | "avoid") {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return `Rs ${Math.round(value).toLocaleString("en-IN")}`;
}

function buildFinalSummary(result: BacktestResponse) {
  const buyCandidates = result.actionList.filter((item) => item.action === "buy_candidate");
  const reviewItems = result.actionList.filter((item) => item.action === "review" || item.action === "avoid");
  const verdict = result.researchVerdict.status;
  const topNames = buyCandidates.slice(0, 3).map((item) => item.symbol).join(", ");
  const headline =
    verdict === "pass"
      ? "This strategy is ready for deeper research."
      : verdict === "watch"
        ? "This strategy is promising, but needs review before action."
        : "This strategy should not be used without major changes.";
  const body =
    buyCandidates.length > 0
      ? `The strongest current research candidates are ${topNames}. Treat these as a shortlist, not automatic orders.`
      : "The current run did not produce strong buy candidates. Focus on the guardrails and review notes before considering any allocation.";
  const steps = [
    "Read the Research Verdict and confirm the data confidence is not low.",
    "Review every Buy Candidate against company news, valuation context, and your own risk profile.",
    "Check Review or Avoid names first; they explain where the model is uncomfortable.",
    "Compare the result against the relevant mutual fund category, not only the index.",
    "Paper trade or use a small satellite allocation before scaling capital.",
  ];
  if (reviewItems.length > 0) {
    steps.splice(2, 0, `${reviewItems.length} selected names need caution based on trend, drawdown, liquidity, or weak composite evidence.`);
  }
  return { headline, body, steps };
}
