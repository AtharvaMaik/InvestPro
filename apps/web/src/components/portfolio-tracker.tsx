import type { BacktestResponse, TrackedHolding } from "@/lib/api";

type Props = {
  result: BacktestResponse;
};

export function PortfolioTracker({ result }: Props) {
  const summary = result.portfolioSummary;
  const rows = result.trackedHoldings ?? [];
  if (!summary || !rows.length) {
    return (
      <div className="chart-panel wide">
        <div className="panel-title">
          <h2>V6 Portfolio Tracker</h2>
          <span>No current holdings entered</span>
        </div>
        <p>Add current holdings in Portfolio Setup to see value, P&L, and allocation drift.</p>
      </div>
    );
  }

  return (
    <div className="chart-panel wide">
      <div className="panel-title">
        <h2>V6 Portfolio Tracker</h2>
        <span>{summary.holdingCount} tracked holdings</span>
      </div>
      <div className="portfolio-summary-grid">
        <SummaryTile label="Current value" value={formatCurrency(summary.currentValue)} />
        <SummaryTile label="Invested value" value={formatCurrency(summary.investedValue)} />
        <SummaryTile label="Cost basis" value={formatCurrency(summary.costBasis)} />
        <SummaryTile label="Unrealized P&L" value={formatCurrency(summary.unrealizedPnl)} tone={(summary.unrealizedPnl ?? 0) >= 0 ? "good" : "bad"} />
        <SummaryTile label="P&L %" value={formatPercent(summary.unrealizedPnlPercent)} tone={(summary.unrealizedPnlPercent ?? 0) >= 0 ? "good" : "bad"} />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Current</th>
              <th>Cost</th>
              <th>P&L</th>
              <th>Current Wt</th>
              <th>Target Wt</th>
              <th>Drift</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.symbol}>
                <td>{row.symbol}</td>
                <td>{formatCurrency(row.currentValue)}</td>
                <td>{formatCurrency(row.costBasis)}</td>
                <td className={(row.unrealizedPnl ?? 0) >= 0 ? "positive-text" : "negative-text"}>{formatCurrency(row.unrealizedPnl)}</td>
                <td>{formatPercent(row.currentWeight)}</td>
                <td>{formatPercent(row.targetWeight)}</td>
                <td className={(row.driftValue ?? 0) >= 0 ? "positive-text" : "negative-text"}>{formatCurrency(row.driftValue)}</td>
                <td>{row.notes || driftLabel(row)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SummaryTile({ label, tone, value }: { label: string; tone?: "good" | "bad"; value: string }) {
  return (
    <div className={`portfolio-summary-tile ${tone ?? ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function driftLabel(row: TrackedHolding) {
  if ((row.targetWeight ?? 0) === 0 && row.currentValue > 0) return "Not in target portfolio";
  if ((row.currentWeight ?? 0) === 0 && (row.targetWeight ?? 0) > 0) return "New target position";
  if ((row.driftValue ?? 0) > 0) return "Below target";
  if ((row.driftValue ?? 0) < 0) return "Above target";
  return "Near target";
}

function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return `Rs ${Math.round(value).toLocaleString("en-IN")}`;
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return `${(value * 100).toFixed(1)}%`;
}
