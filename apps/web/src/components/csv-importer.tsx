"use client";

import { useRef, useState } from "react";

import type { BacktestRequest } from "@/lib/api";
import { importPortfolioCsv } from "@/lib/api";

type Props = {
  currentHoldings: BacktestRequest["currentHoldings"];
  onApply: (holdings: BacktestRequest["currentHoldings"]) => void;
};

export function CsvImporter({ currentHoldings, onApply }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setIsImporting(true);
    setMessage(null);
    try {
      const csvText = await file.text();
      const result = await importPortfolioCsv(csvText);
      const accepted = result.holdings
        .filter((holding) => holding.status !== "error")
        .map((holding) => ({
          symbol: holding.symbol,
          value: holding.value ?? null,
          shares: holding.shares ?? null,
          averageCost: holding.averageCost ?? null,
          notes: holding.notes ?? holding.message,
        }));
      const existing = new Set(currentHoldings.map((holding) => holding.symbol));
      const merged = [...currentHoldings, ...accepted.filter((holding) => !existing.has(holding.symbol))];
      onApply(merged);
      const warningText = result.warnings.length ? ` ${result.warnings.length} warning(s).` : "";
      setMessage(`Imported ${accepted.length} holding(s).${warningText}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to import CSV.");
    } finally {
      setIsImporting(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="csv-importer">
      <input ref={inputRef} accept=".csv,text/csv" aria-label="Import holdings CSV" type="file" onChange={(event) => handleFile(event.target.files?.[0])} />
      <span>{isImporting ? "Importing CSV..." : message ?? "CSV columns: symbol, shares, average cost, value, notes."}</span>
    </div>
  );
}
