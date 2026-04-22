from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import pandas as pd


@dataclass(frozen=True)
class PerformanceMetrics:
    total_return: float
    cagr: float | None
    volatility: float | None
    sharpe: float | None
    sortino: float | None
    max_drawdown: float | None
    calmar: float | None

    def to_dict(self) -> dict[str, float | None]:
        return asdict(self)


def wealth_index(returns: pd.Series) -> pd.Series:
    return (1 + returns.fillna(0)).cumprod()


def drawdown_series(wealth: pd.Series) -> pd.Series:
    peaks = wealth.cummax()
    return (wealth / peaks) - 1


def calculate_metrics(
    returns: pd.Series,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> PerformanceMetrics:
    clean = returns.dropna().astype(float)
    if clean.empty:
        return PerformanceMetrics(0.0, None, None, None, None, None, None)

    wealth = wealth_index(clean)
    total_return = float(wealth.iloc[-1] - 1)
    years = len(clean) / periods_per_year
    cagr = float((wealth.iloc[-1] ** (1 / years)) - 1) if years > 0 else None

    volatility = None
    sharpe = None
    sortino = None
    if len(clean) > 1:
        volatility = float(clean.std(ddof=1) * math.sqrt(periods_per_year))
        if cagr is not None and volatility != 0:
            sharpe = float((cagr - risk_free_rate) / volatility)

        downside = clean.clip(upper=0)
        downside_vol = float(downside.std(ddof=1) * math.sqrt(periods_per_year))
        if cagr is not None and downside_vol != 0:
            sortino = float((cagr - risk_free_rate) / downside_vol)

    max_drawdown = float(drawdown_series(wealth).min())
    calmar = float(cagr / abs(max_drawdown)) if cagr is not None and max_drawdown != 0 else None

    return PerformanceMetrics(
        total_return=total_return,
        cagr=cagr,
        volatility=volatility,
        sharpe=sharpe,
        sortino=sortino,
        max_drawdown=max_drawdown,
        calmar=calmar,
    )
