from __future__ import annotations

from datetime import datetime

import pandas as pd

from app.data import demo, live
from app.models import BacktestRequest, BacktestResponse, ComparisonResult, WarningMessage
from app.quant.factors import average_traded_value, composite_scores, momentum, trailing_volatility, zscore_factor
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
    fundamentals = demo.fundamentals().set_index("symbol")
    rebalance_dates = _rebalance_dates(close.index, request.rebalanceFrequency)
    weights = {factor.id: factor.weight for factor in request.factors}

    portfolio_returns = pd.Series(0.0, index=returns.index)
    holdings = []
    diagnostics_samples: list[dict] = []
    current_weights = pd.Series(dtype=float)
    transaction_cost_rate = request.transactionCostBps / 10000

    for position, rebalance_date in enumerate(rebalance_dates):
        next_date = rebalance_dates[position + 1] if position + 1 < len(rebalance_dates) else returns.index[-1]
        factor_scores = _factor_scores(close.loc[:rebalance_date], volume.loc[:rebalance_date], weights, fundamentals)
        ranked = composite_scores(factor_scores, weights)
        diagnostics_samples.extend(_diagnostic_samples(factor_scores, close, rebalance_date, next_date))
        selected = ranked.head(min(request.topN, len(ranked)))
        if selected.empty:
            warnings.append(WarningMessage(code="NO_ELIGIBLE_STOCKS", message=f"No stocks were eligible on {rebalance_date.date()}."))
            continue

        target_weights = _target_weights(request.weightingMethod, selected, close.loc[:rebalance_date])
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
                        "weight": float(target_weights[symbol]),
                        "compositeScore": float(selected[symbol]),
                        "factorScores": {factor_id: float(scores.get(symbol, 0)) for factor_id, scores in factor_scores.items()},
                    }
                    for symbol in selected.index
                ],
            }
        )
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
            "rollingReturns": {"oneYear": [], "threeYear": [], "fiveYear": []},
            "monthlyReturns": _monthly_returns(portfolio_returns),
        },
        holdings=holdings,
        comparisons=comparisons,
        factorDiagnostics=factor_diagnostics,
        robustness=robustness,
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
        warnings.append(
            WarningMessage(
                code="LIVE_DATA_FALLBACK",
                message=f"Live stock data could not be fetched, so seeded demo prices were used instead. Reason: {exc}",
            )
        )
        return demo.price_data()


def _rebalance_dates(index: pd.DatetimeIndex, frequency: str) -> list[pd.Timestamp]:
    series = pd.Series(index=index, data=index)
    rule = "QE" if frequency == "quarterly" else "ME"
    return list(series.resample(rule).last().dropna())


def _factor_scores(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    weights: dict[str, float],
    fundamentals: pd.DataFrame,
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
            elif factor_id in {"quality_score", "value_score"} and symbol in fundamentals.index:
                value = fundamentals.loc[symbol, factor_id]
            else:
                value = None
            if value is not None:
                values[symbol] = value
        factor_def = FACTOR_DEFS[factor_id]
        raw[factor_id] = zscore_factor(pd.Series(values), higher_is_better=factor_def["direction"] == "higher_is_better")
    return raw


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
                    metrics=calculate_metrics(benchmark).to_dict(),
                    monthlyWinRate=_monthly_win_rate(strategy_returns, benchmark),
                )
            )

    funds = _mutual_fund_navs(request, warnings)
    fund_names = {
        fund["schemeCode"]: fund["schemeName"]
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


def _benchmark_series(request: BacktestRequest, warnings: list[WarningMessage]) -> pd.Series:
    if request.dataSource == "demo":
        return demo.benchmark_series()
    try:
        return live.benchmark_series(request.startDate, request.endDate)
    except Exception as exc:
        _append_once(
            warnings,
            WarningMessage(
                code="LIVE_BENCHMARK_FALLBACK",
                message=f"Live Nifty benchmark data could not be fetched, so demo benchmark data was used. Reason: {exc}",
            ),
        )
        return demo.benchmark_series()


def _mutual_fund_navs(request: BacktestRequest, warnings: list[WarningMessage]) -> dict[str, pd.Series]:
    if request.dataSource == "demo":
        return demo.mutual_fund_navs()
    try:
        return live.mutual_fund_navs(request.mutualFunds)
    except Exception as exc:
        _append_once(
            warnings,
            WarningMessage(
                code="LIVE_MUTUAL_FUND_FALLBACK",
                message=f"Live mutual fund NAV data could not be fetched, so demo NAV data was used. Reason: {exc}",
            ),
        )
        return demo.mutual_fund_navs()


def _append_once(warnings: list[WarningMessage], warning: WarningMessage) -> None:
    if not any(existing.code == warning.code for existing in warnings):
        warnings.append(warning)
