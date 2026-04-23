from __future__ import annotations

import csv
from io import StringIO


ALIASES = {
    "symbol": {"symbol", "ticker", "instrument", "stock"},
    "shares": {"shares", "quantity", "qty"},
    "averageCost": {"average_cost", "avg_cost", "average_price", "avg_price", "avg price"},
    "value": {"value", "current_value", "market_value"},
    "notes": {"notes", "note"},
}


def parse_holdings_csv(csv_text: str, valid_symbols: set[str]) -> dict:
    reader = csv.DictReader(StringIO(csv_text.strip()))
    if not reader.fieldnames:
        return {"holdings": [], "warnings": [{"code": "EMPTY_CSV", "message": "CSV has no headers."}]}

    mapping = {_normalize(header): _canonical(header) for header in reader.fieldnames}
    rows = []
    warnings = []
    for row_number, raw in enumerate(reader, start=2):
        normalized = {_canonical(key): value for key, value in raw.items() if _canonical(key)}
        symbol = str(normalized.get("symbol", "")).strip().upper()
        if not symbol:
            rows.append({"symbol": "", "status": "error", "message": f"Row {row_number}: missing symbol."})
            continue

        parsed = {
            "symbol": symbol,
            "shares": _number_or_none(normalized.get("shares")),
            "averageCost": _number_or_none(normalized.get("averageCost")),
            "value": _number_or_none(normalized.get("value")),
            "notes": normalized.get("notes") or "",
            "status": "valid",
            "message": "Matched supported stock universe",
        }
        negatives = [key for key in ("shares", "averageCost", "value") if parsed[key] is not None and parsed[key] < 0]
        if negatives:
            parsed["status"] = "error"
            parsed["message"] = f"Negative values are not allowed: {', '.join(negatives)}"
        elif symbol not in valid_symbols:
            parsed["status"] = "warning"
            parsed["message"] = "Unknown symbol; import only if this is a legacy holding."
            warnings.append({"code": "UNKNOWN_SYMBOL", "message": f"{symbol} is not in the supported stock universe."})
        rows.append(parsed)

    return {"holdings": rows, "warnings": warnings, "columns": mapping}


def export_trades_csv(trades: list[dict]) -> str:
    output = StringIO()
    fieldnames = ["symbol", "action", "current_value", "target_value", "trade_value", "latest_price", "estimated_shares", "whole_shares", "reason"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for trade in trades:
        estimated = trade.get("estimatedShares")
        writer.writerow(
            {
                "symbol": trade.get("symbol", ""),
                "action": trade.get("tradeAction", ""),
                "current_value": _format_number(trade.get("currentValue")),
                "target_value": _format_number(trade.get("targetValue")),
                "trade_value": _format_number(trade.get("tradeValue")),
                "latest_price": _format_number(trade.get("latestPrice")),
                "estimated_shares": _format_number(estimated),
                "whole_shares": int(estimated) if estimated is not None else "",
                "reason": trade.get("reason", ""),
            }
        )
    return output.getvalue()


def _canonical(header: str | None) -> str | None:
    normalized = _normalize(header or "")
    for canonical, aliases in ALIASES.items():
        if normalized in aliases:
            return canonical
    return None


def _normalize(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _number_or_none(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_number(value: object) -> str:
    parsed = _number_or_none(value)
    if parsed is None:
        return ""
    return f"{parsed:g}"
