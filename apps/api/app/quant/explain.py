from __future__ import annotations


def explain_stock(holding: dict, weights: dict[str, float]) -> dict:
    symbol = holding.get("symbol", "")
    factor_scores = holding.get("factorScores", {})
    contributions = []
    for factor_id, score in factor_scores.items():
        weight = float(weights.get(factor_id, 0))
        weighted = round(float(score) * weight, 6)
        contributions.append(
            {
                "factorId": factor_id,
                "score": float(score),
                "weight": weight,
                "weightedContribution": weighted,
                "direction": "positive" if weighted >= 0 else "negative",
            }
        )

    positives = sorted([item for item in contributions if item["weightedContribution"] > 0], key=lambda item: item["weightedContribution"], reverse=True)[:3]
    negatives = sorted([item for item in contributions if item["weightedContribution"] < 0], key=lambda item: item["weightedContribution"])[:3]
    warnings = _warnings(factor_scores)

    if warnings:
        headline = "Selected with risk flags that need review."
    elif positives:
        headline = f"Selected for {format_factor_name(positives[0]['factorId']).lower()} strength."
    else:
        headline = "Selected by composite rank, but factor evidence is mixed."

    return {
        "symbol": symbol,
        "headline": headline,
        "positives": positives,
        "negatives": negatives,
        "factorContributions": sorted(contributions, key=lambda item: item["weightedContribution"], reverse=True),
        "warnings": warnings,
    }


def format_factor_name(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split("_"))


def _warnings(scores: dict) -> list[dict]:
    warnings = []
    if scores.get("pe_ratio", 0) <= -0.75 or scores.get("pb_ratio", 0) <= -0.75:
        warnings.append({"code": "EXPENSIVE_VALUATION", "message": "Valuation score is weak versus the universe."})
    if scores.get("trend_200d", 0) <= -0.75:
        warnings.append({"code": "WEAK_TREND", "message": "Trend score is weak; price may be below its long-term trend."})
    if scores.get("drawdown_6m", 0) <= -0.75:
        warnings.append({"code": "DEEP_DRAWDOWN", "message": "Recent drawdown score is weak and needs review."})
    if scores.get("liquidity_3m", 0) <= -1.5:
        warnings.append({"code": "LOW_LIQUIDITY", "message": "Liquidity score is weak; execution may be harder."})
    return warnings
