from __future__ import annotations


def enrich_holding(holding: dict, latest_prices: dict[str, float | None], portfolio_value: float) -> dict:
    symbol = str(holding.get("symbol", "")).upper()
    shares = _number_or_none(holding.get("shares"))
    average_cost = _number_or_none(holding.get("averageCost", holding.get("average_cost")))
    manual_value = _number_or_none(holding.get("value"))
    latest_price = _number_or_none(latest_prices.get(symbol))

    current_value_source = "missing"
    current_value = 0.0
    if manual_value is not None and (manual_value > 0 or shares is None):
        current_value = manual_value
        current_value_source = "manual_value"
    elif shares is not None and latest_price is not None:
        current_value = shares * latest_price
        current_value_source = "shares"

    cost_basis = shares * average_cost if shares is not None and average_cost is not None else None
    unrealized_pnl = current_value - cost_basis if cost_basis is not None else None
    unrealized_pnl_percent = unrealized_pnl / cost_basis if cost_basis and unrealized_pnl is not None else None
    current_weight = current_value / portfolio_value if portfolio_value > 0 else 0.0

    return {
        "symbol": symbol,
        "shares": shares,
        "averageCost": average_cost,
        "latestPrice": latest_price,
        "currentValue": float(current_value),
        "currentValueSource": current_value_source,
        "costBasis": float(cost_basis) if cost_basis is not None else None,
        "unrealizedPnl": float(unrealized_pnl) if unrealized_pnl is not None else None,
        "unrealizedPnlPercent": float(unrealized_pnl_percent) if unrealized_pnl_percent is not None else None,
        "currentWeight": float(current_weight),
        "notes": holding.get("notes"),
    }


def summarize_portfolio(holdings: list[dict], latest_prices: dict[str, float | None], cash_value: float = 0) -> dict:
    provisional = [enrich_holding(holding, latest_prices, portfolio_value=0) for holding in holdings if holding.get("symbol")]
    invested_value = sum(row["currentValue"] for row in provisional)
    current_value = float(cash_value + invested_value)
    enriched = [enrich_holding(holding, latest_prices, portfolio_value=current_value) for holding in holdings if holding.get("symbol")]
    cost_basis_values = [row["costBasis"] for row in enriched if row["costBasis"] is not None]
    cost_basis = float(sum(cost_basis_values)) if cost_basis_values else None
    unrealized_pnl_values = [row["unrealizedPnl"] for row in enriched if row["unrealizedPnl"] is not None]
    unrealized_pnl = float(sum(unrealized_pnl_values)) if unrealized_pnl_values else None
    unrealized_pnl_percent = unrealized_pnl / cost_basis if cost_basis and unrealized_pnl is not None else None

    return {
        "cashValue": float(cash_value),
        "currentValue": current_value,
        "investedValue": float(invested_value),
        "costBasis": cost_basis,
        "unrealizedPnl": unrealized_pnl,
        "unrealizedPnlPercent": float(unrealized_pnl_percent) if unrealized_pnl_percent is not None else None,
        "holdingCount": len(enriched),
        "holdings": enriched,
    }


def attach_allocation_drift(current: list[dict], targets: list[dict], portfolio_capital: float) -> list[dict]:
    current_by_symbol = {row["symbol"]: row for row in current}
    targets_by_symbol = {row["symbol"]: row for row in targets}
    rows = []
    for symbol in sorted(set(current_by_symbol).union(targets_by_symbol)):
        current_row = current_by_symbol.get(symbol, {})
        target_row = targets_by_symbol.get(symbol, {})
        current_weight = float(current_row.get("currentWeight") or 0)
        target_weight = float(target_row.get("targetWeight") or 0)
        current_value = float(current_row.get("currentValue") or 0)
        target_value = float(target_row.get("targetValue") or (target_weight * portfolio_capital))
        drift = round(target_weight - current_weight, 10)
        rows.append(
            {
                **current_row,
                "symbol": symbol,
                "sector": target_row.get("sector", current_row.get("sector", "Unknown")),
                "currentValue": current_value,
                "currentWeight": current_weight,
                "targetWeight": target_weight,
                "targetValue": target_value,
                "drift": float(drift),
                "driftValue": float(round(target_value - current_value, 10)),
            }
        )
    return sorted(rows, key=lambda row: abs(row["driftValue"]), reverse=True)


def _number_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
