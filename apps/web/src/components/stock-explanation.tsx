import type { StockExplanation } from "@/lib/api";

type Props = {
  explanation?: StockExplanation;
};

export function StockExplanationPanel({ explanation }: Props) {
  if (!explanation) return null;

  return (
    <details className="stock-explanation">
      <summary>Why?</summary>
      <p>{explanation.headline}</p>
      {explanation.warnings.length ? (
        <div className="explanation-warnings">
          {explanation.warnings.map((warning) => (
            <span key={warning.code} title={warning.message}>{warning.code.replaceAll("_", " ")}</span>
          ))}
        </div>
      ) : null}
      <div className="explanation-columns">
        <ExplanationList title="Helps" rows={explanation.positives} />
        <ExplanationList title="Hurts" rows={explanation.negatives} />
      </div>
    </details>
  );
}

function ExplanationList({ rows, title }: { rows: StockExplanation["positives"]; title: string }) {
  return (
    <div>
      <strong>{title}</strong>
      {rows.length ? rows.map((row) => (
        <span key={`${title}-${row.factorId}`}>
          {formatFactorName(row.factorId)} {row.weightedContribution.toFixed(2)}
        </span>
      )) : <span>No major {title.toLowerCase()} factor</span>}
    </div>
  );
}

function formatFactorName(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
