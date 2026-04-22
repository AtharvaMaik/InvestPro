from __future__ import annotations

from datetime import datetime

import pandas as pd

from app.data import demo
from app.models import BacktestRequest, BacktestResponse, ComparisonResult, WarningMessage
from app.quant.factors import average_traded_value, composite_scores, momentum, trailing_volatility, zscore_factor
from app.quant.metrics import calculate_metrics, drawdown_series, wealth_index


FACTOR_DEFS = {factor["id"]: factor for factor in demo.FACTORS}


def run_backtest(request: BacktestRequest) -> BacktestResponse:
    warnings = [WarningMessage(code="DEMO_DATA", message="This result uses seeded demo data for product validation.")]
    unknown = [factor.id for factor in request.factors if factor.id not in FACTOR_DEFS]
    if unknown:
        raise ValueError(f"Unsupported factor ids: {', '.join(unknown)}")

    prices = demo.price_data()
    symbols = request.customSymbols or demo.SYMBOLS
    prices = prices[prices["symbol"].isin(symbols)]
    start = pd.Timestamp(request.startDate)
    end = pd.Timestamp(request.endDate)
    prices = prices[(prices["date"] >= start) & (prices["date"] <= end)]

    close = prices.pivot(index="date", columns="symbol", values="adjustedClose").sort_index()
    volume = prices.pivot(index="date", columns="symbol", values="volume").sort_index()
    returns = close.pct_change().fillna(0)
    rebalance_dates = _monthly_rebalance_dates(close.index)
    weights = {factor.id: factor.weight for factor in request.factors}

    portfolio_returns = pd.Series(0.0, index=returns.index)
    holdings = []
    current_weights = pd.Series(dtype=float)
    transaction_cost_rate = request.transactionCostBps / 10000

    for position, rebalance_date in enumerate(rebalance_dates):
        next_date = rebalance_dates[position + 1] if position + 1 < len(rebalance_dates) else returns.index[-1]
        factor_scores = _factor_scores(close.loc[:rebalance_date], volume.loc[:rebalance_date], weights)
        ranked = composite_scores(factor_scores, weights)
        selected = ranked.head(min(request.topN, len(ranked)))
        if selected.empty:
            warnings.append(WarningMessage(code="NO_ELIGIBLE_STOCKS", message=f"No stocks were eligible on {rebalance_date.date()}."))
            continue

        target_weights = pd.Series(1 / len(selected), index=selected.index)
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

    comparisons = _comparison_results(request, portfolio_returns)
    equity_curve = _equity_curve(strategy_wealth, request)
    drawdowns = _drawdown_points(strategy_wealth, request)

    return BacktestResponse(
        id=f"bt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        status="completed",
        config=request.model_dump(mode="json"),
        summary={
            "startDate": str(strategy_wealth.index.min().date()),
            "endDate": str(strategy_wealth.index.max().date()),
            "tradingDays": int(len(strategy_wealth)),
            "rebalanceCount": int(len(rebalance_dates)),
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
        warnings=warnings,
    )


def _monthly_rebalance_dates(index: pd.DatetimeIndex) -> list[pd.Timestamp]:
    series = pd.Series(index=index, data=index)
    return list(series.resample("ME").last().dropna())


def _factor_scores(close: pd.DataFrame, volume: pd.DataFrame, weights: dict[str, float]) -> dict[str, pd.Series]:
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
            else:
                value = None
            if value is not None:
                values[symbol] = value
        factor_def = FACTOR_DEFS[factor_id]
        raw[factor_id] = zscore_factor(pd.Series(values), higher_is_better=factor_def["direction"] == "higher_is_better")
    return raw


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


def _comparison_results(request: BacktestRequest, strategy_returns: pd.Series) -> list[ComparisonResult]:
    results: list[ComparisonResult] = []
    benchmark = demo.benchmark_series().pct_change().fillna(0).reindex(strategy_returns.index).fillna(0)
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

    funds = demo.mutual_fund_navs()
    fund_names = {fund["schemeCode"]: fund["schemeName"] for fund in demo.MUTUAL_FUNDS}
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


def _equity_curve(strategy_wealth: pd.Series, request: BacktestRequest) -> list[dict]:
    frame = pd.DataFrame({"strategy": strategy_wealth})
    if "nifty50-demo" in request.benchmarks:
        frame["nifty50-demo"] = demo.benchmark_series().reindex(frame.index).ffill().bfill()
        frame["nifty50-demo"] = frame["nifty50-demo"] / frame["nifty50-demo"].iloc[0]
    funds = demo.mutual_fund_navs()
    for scheme_code in request.mutualFunds:
        if scheme_code in funds:
            frame[scheme_code] = funds[scheme_code].reindex(frame.index).ffill().bfill()
            frame[scheme_code] = frame[scheme_code] / frame[scheme_code].iloc[0]
    return [{"date": index.date().isoformat(), **{column: float(row[column]) for column in frame.columns}} for index, row in frame.iterrows()]


def _drawdown_points(strategy_wealth: pd.Series, request: BacktestRequest) -> list[dict]:
    frame = pd.DataFrame({"strategy": drawdown_series(strategy_wealth)})
    if "nifty50-demo" in request.benchmarks:
        benchmark = demo.benchmark_series().reindex(frame.index).ffill().bfill()
        frame["nifty50-demo"] = drawdown_series(benchmark / benchmark.iloc[0])
    funds = demo.mutual_fund_navs()
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
