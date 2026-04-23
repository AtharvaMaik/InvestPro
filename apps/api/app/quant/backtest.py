from __future__ import annotations

from datetime import datetime

import pandas as pd

from app.data import demo, live
from app.models import BacktestRequest, BacktestResponse, ComparisonResult, WarningMessage
from app.quant.factors import (
    average_traded_value,
    composite_scores,
    max_drawdown_factor,
    momentum,
    relative_momentum,
    trailing_volatility,
    trend_distance,
    zscore_factor,
)
from app.quant.metrics import calculate_metrics, drawdown_series, wealth_index


FACTOR_DEFS = {factor["id"]: factor for factor in demo.FACTORS}


def run_backtest(request: BacktestRequest) -> BacktestResponse:
    warnings = []
    unknown = [factor.id for factor in request.factors if factor.id not in FACTOR_DEFS]
    if unknown:
        raise ValueError(f"Unsupported factor ids: {', '.join(unknown)}")

    prices = _price_data(request, warnings)
    symbols = request.customSymbols or demo.SYMBOLS
    prices = prices[prices["symbol"].isin(symbols)]
    start = pd.Timestamp(request.startDate)
    end = pd.Timestamp(request.endDate)
    prices = prices[(prices["date"] >= start) & (prices["date"] <= end)]

    close = prices.pivot(index="date", columns="symbol", values="adjustedClose").sort_index()
    volume = prices.pivot(index="date", columns="symbol", values="volume").sort_index()
    returns = close.pct_change().fillna(0)
    benchmark_prices = _benchmark_series(request, warnings)
    fundamentals = _fundamentals(request, symbols, warnings).set_index("symbol")
    rebalance_dates = _rebalance_dates(close.index, request.rebalanceFrequency)
    weights = {factor.id: factor.weight for factor in request.factors}

    portfolio_returns = pd.Series(0.0, index=returns.index)
    holdings = []
    diagnostics_samples: list[dict] = []
    rebalance_journal: list[dict] = []
    factor_coverage_samples: list[dict] = []
    current_weights = pd.Series(dtype=float)
    previous_symbols: set[str] = set()
    transaction_cost_rate = request.transactionCostBps / 10000

    for position, rebalance_date in enumerate(rebalance_dates):
        next_date = rebalance_dates[position + 1] if position + 1 < len(rebalance_dates) else returns.index[-1]
        factor_scores = _factor_scores(close.loc[:rebalance_date], volume.loc[:rebalance_date], weights, fundamentals, benchmark_prices.loc[:rebalance_date])
        factor_coverage_samples.append(_factor_coverage(factor_scores, symbols, rebalance_date))
        ranked = composite_scores(factor_scores, weights)
        if request.trendFilter:
            ranked = _apply_trend_filter(ranked, close.loc[:rebalance_date])
        ranked = _apply_liquidity_filter(ranked, close.loc[:rebalance_date], volume.loc[:rebalance_date], request.minLiquidityCrore)
        diagnostics_samples.extend(_diagnostic_samples(factor_scores, close, rebalance_date, next_date))
        selected = _select_with_sector_caps(ranked, request.topN, fundamentals, request.sectorNeutral, request.maxSectorWeight)
        if selected.empty:
            warnings.append(WarningMessage(code="NO_ELIGIBLE_STOCKS", message=f"No stocks were eligible on {rebalance_date.date()}."))
            continue

        target_weights = _target_weights(request.weightingMethod, selected, close.loc[:rebalance_date])
        target_weights = _cap_position_weights(target_weights, request.maxPositionWeight)
        turnover = _one_way_turnover(current_weights, target_weights)
        cost = turnover * transaction_cost_rate
        period_mask = (returns.index > rebalance_date) & (returns.index <= next_date)
        period_returns = returns.loc[period_mask, selected.index].mul(target_weights, axis=1).sum(axis=1)
        if not period_returns.empty:
            period_returns.iloc[0] = period_returns.iloc[0] - cost
            portfolio_returns.loc[period_returns.index] = period_returns

        holdings.append(
            {
                "rebalanceDate": rebalance_date.date().isoformat(),
                "turnover": float(turnover),
                "symbols": [
                    {
                        "symbol": symbol,
                        "sector": str(fundamentals.loc[symbol, "sector"]) if symbol in fundamentals.index and "sector" in fundamentals.columns else "Unknown",
                        "weight": float(target_weights[symbol]),
                        "compositeScore": float(selected[symbol]),
                        "factorScores": {factor_id: float(scores.get(symbol, 0)) for factor_id, scores in factor_scores.items()},
                    }
                    for symbol in selected.index
                ],
            }
        )
        current_symbols = set(selected.index)
        rebalance_journal.append(
            _journal_entry(
                rebalance_date,
                selected,
                factor_scores,
                fundamentals,
                previous_symbols,
                current_symbols,
                turnover,
            )
        )
        previous_symbols = current_symbols
        current_weights = target_weights

    strategy_wealth = wealth_index(portfolio_returns)
    strategy_metrics = calculate_metrics(portfolio_returns).to_dict()
    strategy_metrics["annualTurnover"] = _annual_turnover(holdings)
    strategy_metrics["transactionCostDrag"] = _transaction_cost_drag(holdings, transaction_cost_rate)

    comparisons = _comparison_results(request, portfolio_returns, warnings)
    equity_curve = _equity_curve(strategy_wealth, request, warnings)
    drawdowns = _drawdown_points(strategy_wealth, request, warnings)
    factor_diagnostics = _factor_diagnostics(diagnostics_samples)
    robustness = _robustness_snapshot(request, portfolio_returns, strategy_metrics)
    rolling_returns = _rolling_returns(strategy_wealth)
    fund_category_comparison = _fund_category_comparison(comparisons)
    rolling_analysis = _rolling_analysis(portfolio_returns, comparisons)
    walk_forward = _walk_forward_snapshot(request, portfolio_returns)
    data_confidence = _data_confidence(request, prices, symbols, fundamentals, factor_coverage_samples, warnings)
    investability = _investability_snapshot(request, holdings, strategy_metrics, _sector_exposure(holdings))
    risk_budget = _risk_budget_snapshot(strategy_metrics, comparisons, _sector_exposure(holdings))
    research_verdict = _research_verdict(data_confidence, investability, risk_budget, walk_forward, holdings)
    action_list = _action_list(holdings, data_confidence)

    return BacktestResponse(
        id=f"bt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        status="completed",
        config=request.model_dump(mode="json"),
        summary={
            "startDate": str(strategy_wealth.index.min().date()),
            "endDate": str(strategy_wealth.index.max().date()),
            "tradingDays": int(len(strategy_wealth)),
            "rebalanceCount": int(len(rebalance_dates)),
            "rebalanceFrequency": request.rebalanceFrequency,
            "weightingMethod": request.weightingMethod,
        },
        metrics={"strategy": strategy_metrics},
        series={
            "equityCurve": equity_curve,
            "drawdown": drawdowns,
            "rollingReturns": rolling_returns,
            "monthlyReturns": _monthly_returns(portfolio_returns),
        },
        holdings=holdings,
        comparisons=comparisons,
        factorDiagnostics=factor_diagnostics,
        robustness=robustness,
        sectorExposure=_sector_exposure(holdings),
        fundCategoryComparison=fund_category_comparison,
        rollingAnalysis=rolling_analysis,
        walkForward=walk_forward,
        dataConfidence=data_confidence,
        investability=investability,
        riskBudget=risk_budget,
        researchVerdict=research_verdict,
        rebalanceJournal=rebalance_journal,
        actionList=action_list,
        warnings=warnings,
    )


def _price_data(request: BacktestRequest, warnings: list[WarningMessage]) -> pd.DataFrame:
    symbols = request.customSymbols or demo.SYMBOLS
    if request.dataSource == "demo":
        warnings.append(WarningMessage(code="DEMO_DATA", message="This result uses seeded demo data for product validation."))
        return demo.price_data()

    try:
        return live.price_data(symbols, request.startDate, request.endDate)
    except Exception as exc:
        raise RuntimeError(f"Live stock prices could not be fetched. Reason: {exc}") from exc


def _fundamentals(request: BacktestRequest, symbols: list[str], warnings: list[WarningMessage]) -> pd.DataFrame:
    if request.dataSource == "demo":
        return demo.fundamentals()
    try:
        frame = live.fundamentals(symbols)
        if frame.empty:
            raise RuntimeError("No live fundamentals returned.")
        missing_ratio = frame.drop(columns=["symbol", "sector"], errors="ignore").isna().mean().mean()
        if pd.notna(missing_ratio) and missing_ratio > 0.35:
            warnings.append(
                WarningMessage(
                    code="SPARSE_LIVE_FUNDAMENTALS",
                    message="Some live Yahoo Finance fundamentals were unavailable, so affected factor values were skipped.",
                )
            )
        return frame
    except Exception as exc:
        raise RuntimeError(f"Live fundamentals could not be fetched. Reason: {exc}") from exc


def _rebalance_dates(index: pd.DatetimeIndex, frequency: str) -> list[pd.Timestamp]:
    series = pd.Series(index=index, data=index)
    rule = "QE" if frequency == "quarterly" else "ME"
    return list(series.resample(rule).last().dropna())


def _factor_scores(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    weights: dict[str, float],
    fundamentals: pd.DataFrame,
    benchmark: pd.Series,
) -> dict[str, pd.Series]:
    raw: dict[str, pd.Series] = {}
    for factor_id in weights:
        values = {}
        for symbol in close.columns:
            price_series = close[symbol].dropna()
            if factor_id == "momentum_3m":
                value = momentum(price_series, 63)
            elif factor_id == "momentum_6m":
                value = momentum(price_series, 126)
            elif factor_id == "momentum_12m":
                value = momentum(price_series, 252)
            elif factor_id == "volatility_6m":
                value = trailing_volatility(price_series, 126)
            elif factor_id == "liquidity_3m":
                value = average_traded_value(close[symbol], volume[symbol], 63)
            elif factor_id == "relative_momentum_6m":
                value = relative_momentum(price_series, benchmark, 126)
            elif factor_id == "drawdown_6m":
                value = max_drawdown_factor(price_series, 126)
            elif factor_id == "trend_200d":
                value = trend_distance(price_series, 200)
            elif factor_id in {
                "quality_score",
                "value_score",
                "roe",
                "roce",
                "debt_to_equity",
                "earnings_growth",
                "pe_ratio",
                "pb_ratio",
            } and symbol in fundamentals.index and factor_id in fundamentals.columns:
                value = fundamentals.loc[symbol, factor_id]
            else:
                value = None
            if value is not None and pd.notna(value):
                values[symbol] = value
        factor_def = FACTOR_DEFS[factor_id]
        raw[factor_id] = zscore_factor(pd.Series(values), higher_is_better=factor_def["direction"] == "higher_is_better")
    return raw


def _apply_trend_filter(ranked: pd.Series, close: pd.DataFrame) -> pd.Series:
    passing = []
    for symbol in ranked.index:
        distance = trend_distance(close[symbol].dropna(), 200)
        if distance is not None and distance >= 0:
            passing.append(symbol)
    return ranked.loc[passing]


def _apply_liquidity_filter(ranked: pd.Series, close: pd.DataFrame, volume: pd.DataFrame, min_liquidity_crore: float) -> pd.Series:
    if min_liquidity_crore <= 0:
        return ranked
    minimum_value = min_liquidity_crore * 10_000_000
    passing = []
    for symbol in ranked.index:
        traded_value = average_traded_value(close[symbol], volume[symbol], 63)
        if traded_value is not None and traded_value >= minimum_value:
            passing.append(symbol)
    return ranked.loc[passing]


def _select_with_sector_caps(
    ranked: pd.Series,
    top_n: int,
    fundamentals: pd.DataFrame,
    sector_neutral: bool,
    max_sector_weight: float,
) -> pd.Series:
    if not sector_neutral:
        return ranked.head(min(top_n, len(ranked)))

    max_per_sector = max(1, int(top_n * max_sector_weight))
    selected: list[str] = []
    sector_counts: dict[str, int] = {}
    for symbol in ranked.index:
        sector = "Unknown"
        if symbol in fundamentals.index and "sector" in fundamentals.columns:
            sector = str(fundamentals.loc[symbol, "sector"])
        if sector_counts.get(sector, 0) >= max_per_sector:
            continue
        selected.append(symbol)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        if len(selected) >= top_n:
            break
    return ranked.loc[selected]


def _target_weights(weighting_method: str, selected: pd.Series, close: pd.DataFrame) -> pd.Series:
    if weighting_method == "score":
        raw = selected - selected.min() + 0.01
        return raw / raw.sum()

    if weighting_method == "volatility":
        volatilities = close[selected.index].pct_change().tail(126).std(ddof=1).replace(0, pd.NA)
        inverse_vol = (1 / volatilities).fillna(0)
        if inverse_vol.sum() > 0:
            return inverse_vol / inverse_vol.sum()

    return pd.Series(1 / len(selected), index=selected.index)


def _cap_position_weights(weights: pd.Series, max_position_weight: float) -> pd.Series:
    if weights.empty or max_position_weight >= 1:
        return weights
    capped = weights.clip(upper=max_position_weight)
    if capped.sum() == 0:
        return weights
    return capped / capped.sum()


def _factor_coverage(factor_scores: dict[str, pd.Series], symbols: list[str], rebalance_date: pd.Timestamp) -> dict:
    universe_size = max(1, len(symbols))
    coverages = {
        factor_id: float(scores.dropna().index.intersection(symbols).size / universe_size)
        for factor_id, scores in factor_scores.items()
    }
    average = float(sum(coverages.values()) / len(coverages)) if coverages else 0.0
    return {"rebalanceDate": rebalance_date.date().isoformat(), "averageCoverage": average, "factors": coverages}


def _journal_entry(
    rebalance_date: pd.Timestamp,
    selected: pd.Series,
    factor_scores: dict[str, pd.Series],
    fundamentals: pd.DataFrame,
    previous_symbols: set[str],
    current_symbols: set[str],
    turnover: float,
) -> dict:
    added = sorted(current_symbols - previous_symbols)
    removed = sorted(previous_symbols - current_symbols)
    retained = sorted(current_symbols.intersection(previous_symbols))
    return {
        "rebalanceDate": rebalance_date.date().isoformat(),
        "turnover": float(turnover),
        "added": [_journal_symbol(symbol, selected, factor_scores, fundamentals, "entered portfolio") for symbol in added],
        "removed": [{"symbol": symbol, "reason": "Dropped out of the selected top-ranked portfolio"} for symbol in removed],
        "retained": [_journal_symbol(symbol, selected, factor_scores, fundamentals, "retained by rank") for symbol in retained],
    }


def _journal_symbol(symbol: str, selected: pd.Series, factor_scores: dict[str, pd.Series], fundamentals: pd.DataFrame, action: str) -> dict:
    contributions = {
        factor_id: float(scores.get(symbol, 0))
        for factor_id, scores in factor_scores.items()
    }
    strongest = sorted(contributions.items(), key=lambda item: item[1], reverse=True)[:3]
    sector = str(fundamentals.loc[symbol, "sector"]) if symbol in fundamentals.index and "sector" in fundamentals.columns else "Unknown"
    return {
        "symbol": symbol,
        "sector": sector,
        "compositeScore": float(selected.get(symbol, 0)),
        "reason": f"{action}; strongest factors: {', '.join(factor for factor, _value in strongest) if strongest else 'composite rank'}",
        "topFactors": [{"factorId": factor, "score": score} for factor, score in strongest],
    }


def _diagnostic_samples(
    factor_scores: dict[str, pd.Series],
    close: pd.DataFrame,
    rebalance_date: pd.Timestamp,
    next_date: pd.Timestamp,
) -> list[dict]:
    samples = []
    if rebalance_date not in close.index or next_date not in close.index or rebalance_date == next_date:
        return samples

    forward_returns = (close.loc[next_date] / close.loc[rebalance_date]) - 1
    for factor_id, scores in factor_scores.items():
        aligned = pd.concat([scores.rename("score"), forward_returns.rename("forwardReturn")], axis=1).dropna()
        if len(aligned) < 5:
            continue
        ranked = aligned.sort_values("score", ascending=False)
        bucket_size = max(1, len(ranked) // 5)
        top_return = float(ranked.head(bucket_size)["forwardReturn"].mean())
        bottom_return = float(ranked.tail(bucket_size)["forwardReturn"].mean())
        samples.append(
            {
                "factorId": factor_id,
                "rebalanceDate": rebalance_date.date().isoformat(),
                "topReturn": top_return,
                "bottomReturn": bottom_return,
                "spread": top_return - bottom_return,
                "hit": top_return > bottom_return,
            }
        )
    return samples


def _factor_diagnostics(samples: list[dict]) -> list[dict]:
    if not samples:
        return []

    frame = pd.DataFrame(samples)
    diagnostics = []
    for factor_id, group in frame.groupby("factorId"):
        average_spread = float(group["spread"].mean())
        hit_rate = float(group["hit"].mean())
        if average_spread > 0.01 and hit_rate >= 0.55:
            evidence = "strong"
        elif average_spread > 0 and hit_rate >= 0.45:
            evidence = "mixed"
        else:
            evidence = "weak"
        diagnostics.append(
            {
                "factorId": factor_id,
                "observations": int(len(group)),
                "averageTopReturn": float(group["topReturn"].mean()),
                "averageBottomReturn": float(group["bottomReturn"].mean()),
                "averageSpread": average_spread,
                "hitRate": hit_rate,
                "evidence": evidence,
            }
        )
    return sorted(diagnostics, key=lambda item: item["averageSpread"], reverse=True)


def _robustness_snapshot(
    request: BacktestRequest,
    returns: pd.Series,
    strategy_metrics: dict[str, float | None],
) -> list[dict]:
    base = {
        "scenario": "Selected strategy",
        "topN": request.topN,
        "transactionCostBps": request.transactionCostBps,
        "rebalanceFrequency": request.rebalanceFrequency,
        "cagr": strategy_metrics.get("cagr"),
        "maxDrawdown": strategy_metrics.get("max_drawdown"),
    }
    higher_cost = returns.copy()
    higher_cost.iloc[::21] = higher_cost.iloc[::21] - 0.0025
    higher_cost_metrics = calculate_metrics(higher_cost).to_dict()
    return [
        base,
        {
            "scenario": "+25 bps cost stress",
            "topN": request.topN,
            "transactionCostBps": request.transactionCostBps + 25,
            "rebalanceFrequency": request.rebalanceFrequency,
            "cagr": higher_cost_metrics.get("cagr"),
            "maxDrawdown": higher_cost_metrics.get("max_drawdown"),
        },
    ]


def _one_way_turnover(current: pd.Series, target: pd.Series) -> float:
    combined = current.reindex(current.index.union(target.index), fill_value=0)
    target_aligned = target.reindex(combined.index, fill_value=0)
    return float(0.5 * (target_aligned - combined).abs().sum())


def _annual_turnover(holdings: list[dict]) -> float:
    if not holdings:
        return 0.0
    return float(pd.Series([entry["turnover"] for entry in holdings]).mean() * 12)


def _transaction_cost_drag(holdings: list[dict], cost_rate: float) -> float:
    return float(sum(entry["turnover"] * cost_rate for entry in holdings))


def _comparison_results(
    request: BacktestRequest,
    strategy_returns: pd.Series,
    warnings: list[WarningMessage],
) -> list[ComparisonResult]:
    results: list[ComparisonResult] = []
    benchmark = _benchmark_series(request, warnings).pct_change().fillna(0).reindex(strategy_returns.index).fillna(0)
    for benchmark_id in request.benchmarks:
        if benchmark_id == "nifty50-demo":
            results.append(
                ComparisonResult(
                    id=benchmark_id,
                    name="Nifty 50 Demo",
                    type="benchmark",
                    category="Large Cap Index",
                    metrics=calculate_metrics(benchmark).to_dict(),
                    monthlyWinRate=_monthly_win_rate(strategy_returns, benchmark),
                )
            )

    funds = _mutual_fund_navs(request, warnings)
    fund_names = {
        fund["schemeCode"]: fund["schemeName"]
        for fund in [*demo.MUTUAL_FUNDS, *live.CURATED_MUTUAL_FUNDS]
    }
    fund_categories = {
        fund["schemeCode"]: fund["category"]
        for fund in [*demo.MUTUAL_FUNDS, *live.CURATED_MUTUAL_FUNDS]
    }
    for scheme_code in request.mutualFunds:
        if scheme_code in funds:
            fund_returns = funds[scheme_code].pct_change().fillna(0).reindex(strategy_returns.index).fillna(0)
            results.append(
                ComparisonResult(
                    id=scheme_code,
                    name=fund_names[scheme_code],
                    type="mutual_fund",
                    category=fund_categories.get(scheme_code, "Mutual Fund"),
                    metrics=calculate_metrics(fund_returns).to_dict(),
                    monthlyWinRate=_monthly_win_rate(strategy_returns, fund_returns),
                )
            )
    return results


def _equity_curve(strategy_wealth: pd.Series, request: BacktestRequest, warnings: list[WarningMessage]) -> list[dict]:
    frame = pd.DataFrame({"strategy": strategy_wealth})
    if "nifty50-demo" in request.benchmarks:
        frame["nifty50-demo"] = _benchmark_series(request, warnings).reindex(frame.index).ffill().bfill()
        frame["nifty50-demo"] = frame["nifty50-demo"] / frame["nifty50-demo"].iloc[0]
    funds = _mutual_fund_navs(request, warnings)
    for scheme_code in request.mutualFunds:
        if scheme_code in funds:
            frame[scheme_code] = funds[scheme_code].reindex(frame.index).ffill().bfill()
            frame[scheme_code] = frame[scheme_code] / frame[scheme_code].iloc[0]
    return [{"date": index.date().isoformat(), **{column: float(row[column]) for column in frame.columns}} for index, row in frame.iterrows()]


def _drawdown_points(strategy_wealth: pd.Series, request: BacktestRequest, warnings: list[WarningMessage]) -> list[dict]:
    frame = pd.DataFrame({"strategy": drawdown_series(strategy_wealth)})
    if "nifty50-demo" in request.benchmarks:
        benchmark = _benchmark_series(request, warnings).reindex(frame.index).ffill().bfill()
        frame["nifty50-demo"] = drawdown_series(benchmark / benchmark.iloc[0])
    funds = _mutual_fund_navs(request, warnings)
    for scheme_code in request.mutualFunds:
        if scheme_code in funds:
            nav = funds[scheme_code].reindex(frame.index).ffill().bfill()
            frame[scheme_code] = drawdown_series(nav / nav.iloc[0])
    return [{"date": index.date().isoformat(), **{column: float(row[column]) for column in frame.columns}} for index, row in frame.iterrows()]


def _monthly_returns(returns: pd.Series) -> list[dict]:
    monthly = (1 + returns).resample("ME").prod() - 1
    return [{"date": index.date().isoformat(), "strategy": float(value)} for index, value in monthly.items()]


def _monthly_win_rate(strategy: pd.Series, comparison: pd.Series) -> float | None:
    strategy_monthly = (1 + strategy).resample("ME").prod() - 1
    comparison_monthly = (1 + comparison).resample("ME").prod() - 1
    aligned = pd.concat([strategy_monthly, comparison_monthly], axis=1).dropna()
    if aligned.empty:
        return None
    return float((aligned.iloc[:, 0] > aligned.iloc[:, 1]).mean())


def _rolling_returns(wealth: pd.Series) -> dict[str, list[dict]]:
    windows = {"oneYear": 252, "threeYear": 756, "fiveYear": 1260}
    output: dict[str, list[dict]] = {}
    for label, window in windows.items():
        if len(wealth) <= window:
            output[label] = []
            continue
        series = (wealth / wealth.shift(window)) - 1
        output[label] = [
            {"date": index.date().isoformat(), "strategy": float(value)}
            for index, value in series.dropna().items()
        ]
    return output


def _sector_exposure(holdings: list[dict]) -> list[dict]:
    latest = holdings[-1] if holdings else None
    if not latest:
        return []
    exposure: dict[str, float] = {}
    for holding in latest["symbols"]:
        sector = holding.get("sector", "Unknown")
        exposure[sector] = exposure.get(sector, 0.0) + holding["weight"]
    return [
        {"sector": sector, "weight": float(weight), "positions": sum(1 for item in latest["symbols"] if item.get("sector", "Unknown") == sector)}
        for sector, weight in sorted(exposure.items(), key=lambda item: item[1], reverse=True)
    ]


def _fund_category_comparison(comparisons: list[ComparisonResult]) -> list[dict]:
    funds = [comparison for comparison in comparisons if comparison.type == "mutual_fund"]
    if not funds:
        return []
    rows = []
    for category in sorted({fund.category or "Mutual Fund" for fund in funds}):
        group = [fund for fund in funds if (fund.category or "Mutual Fund") == category]
        rows.append(
            {
                "category": category,
                "fundCount": len(group),
                "averageCagr": _average_metric(group, "cagr"),
                "averageSharpe": _average_metric(group, "sharpe"),
                "averageMaxDrawdown": _average_metric(group, "max_drawdown"),
                "averageMonthlyWinRate": _average_win_rate(group),
            }
        )
    return rows


def _rolling_analysis(strategy_returns: pd.Series, comparisons: list[ComparisonResult]) -> dict:
    monthly = (1 + strategy_returns).resample("ME").prod() - 1
    positive_month_rate = float((monthly > 0).mean()) if not monthly.empty else None
    one_year = (1 + strategy_returns).cumprod()
    one_year_returns = (one_year / one_year.shift(252) - 1).dropna()
    return {
        "positiveMonthRate": positive_month_rate,
        "oneYearAverageReturn": float(one_year_returns.mean()) if not one_year_returns.empty else None,
        "oneYearWinRate": max(
            [comparison.monthlyWinRate for comparison in comparisons if comparison.monthlyWinRate is not None],
            default=None,
        ),
    }


def _walk_forward_snapshot(request: BacktestRequest, returns: pd.Series) -> dict:
    if len(returns) < 504:
        return {"status": "insufficient_history"}
    split_index = max(1, min(len(returns) - 1, int(len(returns) * 0.6)))
    train = returns.iloc[:split_index]
    test = returns.iloc[split_index:]
    train_metrics = calculate_metrics(train).to_dict()
    test_metrics = calculate_metrics(test).to_dict()
    train_cagr = train_metrics.get("cagr")
    test_cagr = test_metrics.get("cagr")
    train_drawdown = train_metrics.get("max_drawdown")
    test_drawdown = test_metrics.get("max_drawdown")
    return {
        "status": "completed",
        "method": "fixed submitted weights; 60 percent train, 40 percent test",
        "train": {
            "startDate": str(train.index.min().date()),
            "endDate": str(train.index.max().date()),
            "metrics": train_metrics,
        },
        "test": {
            "startDate": str(test.index.min().date()),
            "endDate": str(test.index.max().date()),
            "metrics": test_metrics,
        },
        "degradation": {
            "cagr": float(test_cagr - train_cagr) if train_cagr is not None and test_cagr is not None else None,
            "maxDrawdown": float(test_drawdown - train_drawdown) if train_drawdown is not None and test_drawdown is not None else None,
        },
        "config": {"topN": request.topN, "rebalanceFrequency": request.rebalanceFrequency},
    }


def _average_metric(comparisons: list[ComparisonResult], key: str) -> float | None:
    values = [comparison.metrics.get(key) for comparison in comparisons]
    clean = [float(value) for value in values if value is not None and not pd.isna(value)]
    return float(sum(clean) / len(clean)) if clean else None


def _average_win_rate(comparisons: list[ComparisonResult]) -> float | None:
    clean = [float(comparison.monthlyWinRate) for comparison in comparisons if comparison.monthlyWinRate is not None]
    return float(sum(clean) / len(clean)) if clean else None


def _data_confidence(
    request: BacktestRequest,
    prices: pd.DataFrame,
    symbols: list[str],
    fundamentals: pd.DataFrame,
    factor_coverage_samples: list[dict],
    warnings: list[WarningMessage],
) -> dict:
    expected_symbols = max(1, len(symbols))
    price_symbols = prices["symbol"].nunique() if "symbol" in prices else 0
    price_coverage = float(price_symbols / expected_symbols)
    fundamental_columns = [column for column in fundamentals.columns if column not in {"sector"}]
    fundamental_coverage = 1.0
    if fundamental_columns:
        fundamental_coverage = float(1 - fundamentals[fundamental_columns].isna().mean().mean())
    factor_coverage = (
        float(pd.Series([sample["averageCoverage"] for sample in factor_coverage_samples]).mean())
        if factor_coverage_samples
        else 0.0
    )
    fallback_penalty = 0.2 if any("FALLBACK" in warning.code for warning in warnings) else 0.0
    demo_penalty = 0.1 if request.dataSource == "demo" else 0.0
    score = max(0.0, min(1.0, (price_coverage * 0.4) + (fundamental_coverage * 0.25) + (factor_coverage * 0.35) - fallback_penalty - demo_penalty))
    level = "high" if score >= 0.8 else "medium" if score >= 0.55 else "low"
    missing_symbols = sorted(set(symbols) - set(prices["symbol"].unique())) if "symbol" in prices else symbols
    return {
        "level": level,
        "score": score,
        "priceCoverage": price_coverage,
        "fundamentalCoverage": fundamental_coverage,
        "factorCoverage": factor_coverage,
        "source": request.dataSource,
        "missingSymbols": missing_symbols[:20],
        "warningCodes": [warning.code for warning in warnings],
    }


def _investability_snapshot(request: BacktestRequest, holdings: list[dict], strategy_metrics: dict[str, float | None], sector_exposure: list[dict]) -> dict:
    latest = holdings[-1]["symbols"] if holdings else []
    max_position = max([holding["weight"] for holding in latest], default=0.0)
    annual_turnover = strategy_metrics.get("annualTurnover") or 0.0
    max_sector = max([sector["weight"] for sector in sector_exposure], default=0.0)
    checks = [
        _check("position_size", max_position <= request.maxPositionWeight + 0.0001, f"Largest position is {max_position:.1%}; budget is {request.maxPositionWeight:.1%}."),
        _check("turnover_budget", annual_turnover <= request.maxAnnualTurnover, f"Annual turnover is {annual_turnover:.1%}; budget is {request.maxAnnualTurnover:.1%}."),
        _check("sector_concentration", max_sector <= request.maxSectorWeight + 0.0001 or not request.sectorNeutral, f"Largest sector is {max_sector:.1%}; cap is {request.maxSectorWeight:.1%}."),
        _check("holding_count", len(latest) >= min(request.topN, 8), f"Portfolio holds {len(latest)} stocks; target is {request.topN}."),
    ]
    failed = sum(1 for check in checks if check["status"] == "fail")
    verdict = "investable" if failed == 0 else "watch" if failed <= 2 else "not_investable"
    return {"verdict": verdict, "checks": checks}


def _risk_budget_snapshot(strategy_metrics: dict[str, float | None], comparisons: list[ComparisonResult], sector_exposure: list[dict]) -> dict:
    volatility = strategy_metrics.get("volatility") or 0.0
    max_drawdown = strategy_metrics.get("max_drawdown") or 0.0
    max_sector = max([sector["weight"] for sector in sector_exposure], default=0.0)
    benchmark = next((comparison for comparison in comparisons if comparison.type == "benchmark"), None)
    benchmark_vol = benchmark.metrics.get("volatility") if benchmark else None
    if abs(max_drawdown) <= 0.18 and volatility <= 0.18:
        risk_level = "conservative"
    elif abs(max_drawdown) <= 0.28 and volatility <= 0.25:
        risk_level = "balanced"
    elif abs(max_drawdown) <= 0.4 and volatility <= 0.35:
        risk_level = "aggressive"
    else:
        risk_level = "speculative"
    return {
        "riskLevel": risk_level,
        "volatility": volatility,
        "benchmarkVolatility": benchmark_vol,
        "maxDrawdown": max_drawdown,
        "maxSectorWeight": max_sector,
        "notes": _risk_notes(risk_level, volatility, max_drawdown, max_sector),
    }


def _research_verdict(data_confidence: dict, investability: dict, risk_budget: dict, walk_forward: dict, holdings: list[dict]) -> dict:
    reasons = []
    status = "pass"
    if data_confidence["level"] == "low":
        status = "reject"
        reasons.append("Data confidence is low.")
    if not holdings:
        status = "reject"
        reasons.append("No holdings were produced.")
    if investability["verdict"] == "not_investable":
        status = "reject"
        reasons.append("Investability guardrails failed.")
    elif investability["verdict"] == "watch" and status != "reject":
        status = "watch"
        reasons.append("Some investability checks need review.")
    if risk_budget["riskLevel"] == "speculative":
        status = "reject" if status == "reject" else "watch"
        reasons.append("Risk budget is speculative.")
    if walk_forward.get("status") != "completed" and status == "pass":
        status = "watch"
        reasons.append("Walk-forward validation is incomplete.")
    degradation = walk_forward.get("degradation", {}) if isinstance(walk_forward, dict) else {}
    if degradation.get("cagr") is not None and degradation["cagr"] < -0.1 and status == "pass":
        status = "watch"
        reasons.append("Out-of-sample CAGR degraded materially.")
    if not reasons:
        reasons.append("Data quality, investability, risk, and validation checks are acceptable for further research.")
    return {"status": status, "reasons": reasons}


def _action_list(holdings: list[dict], data_confidence: dict) -> list[dict]:
    latest = holdings[-1]["symbols"] if holdings else []
    actions = []
    for holding in latest:
        scores = holding.get("factorScores", {})
        composite = holding.get("compositeScore", 0)
        trend = scores.get("trend_200d", 0)
        drawdown = scores.get("drawdown_6m", 0)
        liquidity = scores.get("liquidity_3m", 0)
        if data_confidence.get("level") == "low" or trend < -0.75 or drawdown < -1.0:
            action = "review"
        elif composite >= 0.75 and trend >= 0 and drawdown >= -0.5:
            action = "buy_candidate"
        elif composite >= 0:
            action = "hold"
        else:
            action = "review"
        if liquidity < -1.5:
            action = "avoid"
        actions.append(
            {
                "symbol": holding["symbol"],
                "sector": holding.get("sector", "Unknown"),
                "action": action,
                "weight": holding.get("weight", 0),
                "compositeScore": composite,
                "reason": _action_reason(action, composite, trend, drawdown, liquidity),
            }
        )
    order = {"buy_candidate": 0, "hold": 1, "review": 2, "avoid": 3}
    return sorted(actions, key=lambda item: (order[item["action"]], -item["compositeScore"]))


def _action_reason(action: str, composite: float, trend: float, drawdown: float, liquidity: float) -> str:
    if action == "buy_candidate":
        return "Strong composite rank with acceptable trend and drawdown profile."
    if action == "hold":
        return "Selected by the model, but factor evidence is moderate rather than exceptional."
    if action == "avoid":
        return "Selected rank is weakened by poor liquidity, so execution risk is high."
    if trend < -0.75:
        return "Review because trend evidence is weak despite selection."
    if drawdown < -1.0:
        return "Review because recent drawdown evidence is weak despite selection."
    return f"Review because composite score is {composite:.2f}, trend score is {trend:.2f}, and drawdown score is {drawdown:.2f}."


def _check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "status": "pass" if passed else "fail", "detail": detail}


def _risk_notes(risk_level: str, volatility: float, max_drawdown: float, max_sector: float) -> list[str]:
    return [
        f"Risk level is {risk_level}.",
        f"Annualized volatility is {volatility:.1%}.",
        f"Maximum drawdown is {max_drawdown:.1%}.",
        f"Largest sector exposure is {max_sector:.1%}.",
    ]


def _benchmark_series(request: BacktestRequest, warnings: list[WarningMessage]) -> pd.Series:
    if request.dataSource == "demo":
        return demo.benchmark_series()
    try:
        return live.benchmark_series(request.startDate, request.endDate)
    except Exception as exc:
        raise RuntimeError(f"Live Nifty benchmark data could not be fetched. Reason: {exc}") from exc


def _mutual_fund_navs(request: BacktestRequest, warnings: list[WarningMessage]) -> dict[str, pd.Series]:
    if request.dataSource == "demo":
        return demo.mutual_fund_navs()
    try:
        return live.mutual_fund_navs(request.mutualFunds)
    except Exception as exc:
        raise RuntimeError(f"Live mutual fund NAV data could not be fetched. Reason: {exc}") from exc


def _append_once(warnings: list[WarningMessage], warning: WarningMessage) -> None:
    if not any(existing.code == warning.code for existing in warnings):
        warnings.append(warning)
