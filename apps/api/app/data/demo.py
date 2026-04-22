from __future__ import annotations

import numpy as np
import pandas as pd


SYMBOLS = [
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "INFY.NS",
    "ICICIBANK.NS",
    "LT.NS",
    "ITC.NS",
    "SBIN.NS",
    "BHARTIARTL.NS",
    "ASIANPAINT.NS",
    "MARUTI.NS",
    "SUNPHARMA.NS",
]

UNIVERSES = [
    {
        "id": "nifty50-demo",
        "name": "Nifty 50 Demo",
        "description": "Seeded Indian large-cap demo universe",
        "symbolCount": len(SYMBOLS),
        "source": "demo",
    }
]

FACTORS = [
    {
        "id": "momentum_3m",
        "name": "3M Momentum",
        "category": "Momentum",
        "direction": "higher_is_better",
        "lookbackDays": 63,
        "description": "Three-month price return",
    },
    {
        "id": "momentum_6m",
        "name": "6M Momentum",
        "category": "Momentum",
        "direction": "higher_is_better",
        "lookbackDays": 126,
        "description": "Six-month price return",
    },
    {
        "id": "momentum_12m",
        "name": "12M Momentum",
        "category": "Momentum",
        "direction": "higher_is_better",
        "lookbackDays": 252,
        "description": "Twelve-month price return",
    },
    {
        "id": "volatility_6m",
        "name": "6M Volatility",
        "category": "Risk",
        "direction": "lower_is_better",
        "lookbackDays": 126,
        "description": "Annualized trailing six-month volatility",
    },
    {
        "id": "liquidity_3m",
        "name": "3M Liquidity",
        "category": "Liquidity",
        "direction": "higher_is_better",
        "lookbackDays": 63,
        "description": "Three-month average traded value",
    },
]

BENCHMARKS = [
    {
        "id": "nifty50-demo",
        "name": "Nifty 50 Demo",
        "category": "Large Cap Index",
        "source": "demo",
    }
]

MUTUAL_FUNDS = [
    {
        "schemeCode": "ppfas-flexi-demo",
        "schemeName": "Parag Parikh Flexi Cap Fund Demo",
        "fundHouse": "PPFAS Mutual Fund",
        "category": "Flexi Cap",
        "source": "demo",
    },
    {
        "schemeCode": "hdfc-flexi-demo",
        "schemeName": "HDFC Flexi Cap Fund Demo",
        "fundHouse": "HDFC Mutual Fund",
        "category": "Flexi Cap",
        "source": "demo",
    },
]


def price_data() -> pd.DataFrame:
    dates = pd.bdate_range("2019-01-01", "2025-01-31")
    rng = np.random.default_rng(42)
    rows = []
    for index, symbol in enumerate(SYMBOLS):
        drift = 0.00025 + (index % 4) * 0.00005
        volatility = 0.012 + (index % 5) * 0.001
        shocks = rng.normal(drift, volatility, len(dates))
        close = 100 * np.cumprod(1 + shocks)
        volume_base = 900_000 + index * 120_000
        volume = volume_base * (1 + rng.normal(0, 0.10, len(dates)))
        for row_date, row_close, row_volume in zip(dates, close, volume, strict=True):
            rows.append(
                {
                    "symbol": symbol,
                    "date": row_date,
                    "close": float(row_close),
                    "adjustedClose": float(row_close),
                    "volume": max(int(row_volume), 10_000),
                }
            )
    return pd.DataFrame(rows)


def benchmark_series() -> pd.Series:
    prices = price_data().pivot(index="date", columns="symbol", values="adjustedClose")
    return prices.pct_change().mean(axis=1).fillna(0).add(1).cumprod()


def mutual_fund_navs() -> dict[str, pd.Series]:
    dates = pd.bdate_range("2019-01-01", "2025-01-31")
    rng = np.random.default_rng(7)
    funds = {}
    for index, fund in enumerate(MUTUAL_FUNDS):
        returns = rng.normal(0.00028 + index * 0.00002, 0.009 + index * 0.001, len(dates))
        funds[fund["schemeCode"]] = pd.Series(50 * np.cumprod(1 + returns), index=dates)
    return funds


def search_mutual_funds(query: str | None) -> list[dict]:
    if not query:
        return MUTUAL_FUNDS
    lowered = query.lower()
    return [fund for fund in MUTUAL_FUNDS if lowered in fund["schemeName"].lower()]
