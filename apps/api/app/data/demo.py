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
    "AXISBANK.NS",
    "KOTAKBANK.NS",
    "HINDUNILVR.NS",
    "BAJFINANCE.NS",
    "BAJAJFINSV.NS",
    "HCLTECH.NS",
    "WIPRO.NS",
    "TECHM.NS",
    "ULTRACEMCO.NS",
    "TITAN.NS",
    "NESTLEIND.NS",
    "POWERGRID.NS",
    "NTPC.NS",
    "ONGC.NS",
    "COALINDIA.NS",
    "TATASTEEL.NS",
    "JSWSTEEL.NS",
    "ADANIENT.NS",
    "ADANIPORTS.NS",
    "GRASIM.NS",
    "M&M.NS",
    "HEROMOTOCO.NS",
    "EICHERMOT.NS",
    "CIPLA.NS",
    "DRREDDY.NS",
    "DIVISLAB.NS",
    "BRITANNIA.NS",
    "APOLLOHOSP.NS",
    "BPCL.NS",
    "HINDALCO.NS",
    "INDUSINDBK.NS",
    "BAJAJ-AUTO.NS",
    "SHRIRAMFIN.NS",
    "TRENT.NS",
    "BEL.NS",
    "TATACONSUM.NS",
    "SBILIFE.NS",
    "HDFCLIFE.NS",
    "CROMPTON.NS",
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
    {
        "id": "relative_momentum_6m",
        "name": "6M Relative Momentum",
        "category": "Momentum",
        "direction": "higher_is_better",
        "lookbackDays": 126,
        "description": "Six-month stock return minus six-month benchmark return",
    },
    {
        "id": "drawdown_6m",
        "name": "6M Drawdown",
        "category": "Risk",
        "direction": "higher_is_better",
        "lookbackDays": 126,
        "description": "Worst trailing six-month drawdown; less severe is better",
    },
    {
        "id": "trend_200d",
        "name": "200D Trend",
        "category": "Trend",
        "direction": "higher_is_better",
        "lookbackDays": 200,
        "description": "Latest price divided by 200-day moving average minus one",
    },
    {
        "id": "roe",
        "name": "ROE",
        "category": "Fundamental",
        "direction": "higher_is_better",
        "lookbackDays": 0,
        "description": "Return on equity profitability factor",
    },
    {
        "id": "roce",
        "name": "ROCE",
        "category": "Fundamental",
        "direction": "higher_is_better",
        "lookbackDays": 0,
        "description": "Return on capital employed quality factor",
    },
    {
        "id": "debt_to_equity",
        "name": "Debt/Equity",
        "category": "Fundamental",
        "direction": "lower_is_better",
        "lookbackDays": 0,
        "description": "Balance-sheet leverage; lower debt relative to equity is preferred",
    },
    {
        "id": "earnings_growth",
        "name": "Earnings Growth",
        "category": "Fundamental",
        "direction": "higher_is_better",
        "lookbackDays": 0,
        "description": "Trailing earnings growth proxy",
    },
    {
        "id": "pe_ratio",
        "name": "P/E",
        "category": "Valuation",
        "direction": "lower_is_better",
        "lookbackDays": 0,
        "description": "Price-to-earnings valuation factor",
    },
    {
        "id": "pb_ratio",
        "name": "P/B",
        "category": "Valuation",
        "direction": "lower_is_better",
        "lookbackDays": 0,
        "description": "Price-to-book valuation factor",
    },
    {
        "id": "quality_score",
        "name": "Quality Score",
        "category": "Fundamental",
        "direction": "higher_is_better",
        "lookbackDays": 0,
        "description": "Composite demo quality factor using profitability and balance-sheet strength",
    },
    {
        "id": "value_score",
        "name": "Value Score",
        "category": "Fundamental",
        "direction": "higher_is_better",
        "lookbackDays": 0,
        "description": "Composite demo value factor using valuation yield proxies",
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
    {
        "schemeCode": "mirae-large-demo",
        "schemeName": "Mirae Asset Large Cap Fund Demo",
        "fundHouse": "Mirae Asset Mutual Fund",
        "category": "Large Cap",
        "source": "demo",
    },
    {
        "schemeCode": "nippon-small-demo",
        "schemeName": "Nippon India Small Cap Fund Demo",
        "fundHouse": "Nippon India Mutual Fund",
        "category": "Small Cap",
        "source": "demo",
    },
    {
        "schemeCode": "quant-small-demo",
        "schemeName": "quant Small Cap Fund Demo",
        "fundHouse": "quant Mutual Fund",
        "category": "Small Cap",
        "source": "demo",
    },
    {
        "schemeCode": "motilal-midcap-demo",
        "schemeName": "Motilal Oswal Midcap Fund Demo",
        "fundHouse": "Motilal Oswal Mutual Fund",
        "category": "Mid Cap",
        "source": "demo",
    },
    {
        "schemeCode": "hdfc-elss-demo",
        "schemeName": "HDFC ELSS Tax Saver Fund Demo",
        "fundHouse": "HDFC Mutual Fund",
        "category": "ELSS",
        "source": "demo",
    },
    {
        "schemeCode": "uti-nifty50-demo",
        "schemeName": "UTI Nifty 50 Index Fund Demo",
        "fundHouse": "UTI Mutual Fund",
        "category": "Index",
        "source": "demo",
    },
    {
        "schemeCode": "hdfc-nifty50-demo",
        "schemeName": "HDFC Nifty 50 Index Fund Demo",
        "fundHouse": "HDFC Mutual Fund",
        "category": "Index",
        "source": "demo",
    },
    {
        "schemeCode": "icici-nifty50-demo",
        "schemeName": "ICICI Prudential Nifty 50 Index Fund Demo",
        "fundHouse": "ICICI Prudential Mutual Fund",
        "category": "Index",
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


def fundamentals() -> pd.DataFrame:
    sectors = [
        "Energy",
        "Information Technology",
        "Financials",
        "Information Technology",
        "Financials",
        "Industrials",
        "Consumer Staples",
        "Financials",
        "Communication Services",
        "Consumer Discretionary",
        "Consumer Discretionary",
        "Health Care",
        "Financials",
        "Financials",
        "Consumer Staples",
        "Financials",
        "Financials",
        "Information Technology",
        "Information Technology",
        "Information Technology",
        "Materials",
        "Consumer Discretionary",
        "Consumer Staples",
        "Utilities",
        "Utilities",
        "Energy",
        "Energy",
        "Materials",
        "Materials",
        "Industrials",
        "Industrials",
        "Materials",
        "Consumer Discretionary",
        "Consumer Discretionary",
        "Consumer Discretionary",
        "Health Care",
        "Health Care",
        "Health Care",
        "Consumer Staples",
        "Health Care",
        "Energy",
        "Materials",
        "Financials",
        "Consumer Discretionary",
        "Financials",
        "Consumer Discretionary",
        "Industrials",
        "Consumer Staples",
        "Financials",
        "Financials",
        "Consumer Discretionary",
    ]
    rows = []
    for index, symbol in enumerate(SYMBOLS):
        rows.append(
            {
                "symbol": symbol,
                "sector": sectors[index % len(sectors)],
                "quality_score": 55 + ((index * 11) % 40),
                "value_score": 45 + ((index * 7) % 42),
                "roe": 0.08 + ((index * 7) % 22) / 100,
                "roce": 0.10 + ((index * 5) % 24) / 100,
                "debt_to_equity": 0.05 + ((index * 9) % 120) / 100,
                "earnings_growth": -0.05 + ((index * 6) % 45) / 100,
                "pe_ratio": 12 + ((index * 4) % 52),
                "pb_ratio": 1.0 + ((index * 3) % 20) / 2,
            }
        )
    return pd.DataFrame(rows)
