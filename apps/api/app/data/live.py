from __future__ import annotations

from datetime import date

import pandas as pd
import requests

MFAPI_BASE_URL = "https://api.mfapi.in"

CURATED_MUTUAL_FUNDS = [
    {
        "schemeCode": "122639",
        "schemeName": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
        "fundHouse": "PPFAS Mutual Fund",
        "category": "Flexi Cap",
        "source": "mfapi",
    },
    {
        "schemeCode": "118955",
        "schemeName": "HDFC Flexi Cap Fund - Growth Option - Direct Plan",
        "fundHouse": "HDFC Mutual Fund",
        "category": "Flexi Cap",
        "source": "mfapi",
    },
    {
        "schemeCode": "118825",
        "schemeName": "Mirae Asset Large Cap Fund - Direct Plan - Growth",
        "fundHouse": "Mirae Asset Mutual Fund",
        "category": "Large Cap",
        "source": "mfapi",
    },
    {
        "schemeCode": "118777",
        "schemeName": "Nippon India Small Cap Fund - Direct Plan Growth Plan - Bonus Option",
        "fundHouse": "Nippon India Mutual Fund",
        "category": "Small Cap",
        "source": "mfapi",
    },
    {
        "schemeCode": "120828",
        "schemeName": "quant Small Cap Fund - Growth Option - Direct Plan",
        "fundHouse": "quant Mutual Fund",
        "category": "Small Cap",
        "source": "mfapi",
    },
    {
        "schemeCode": "127042",
        "schemeName": "Motilal Oswal Midcap Fund - Direct Plan - Growth Option",
        "fundHouse": "Motilal Oswal Mutual Fund",
        "category": "Mid Cap",
        "source": "mfapi",
    },
    {
        "schemeCode": "119060",
        "schemeName": "HDFC ELSS Tax saver - Growth Option - Direct Plan",
        "fundHouse": "HDFC Mutual Fund",
        "category": "ELSS",
        "source": "mfapi",
    },
    {
        "schemeCode": "120716",
        "schemeName": "UTI Nifty 50 Index Fund - Growth Option - Direct",
        "fundHouse": "UTI Mutual Fund",
        "category": "Index",
        "source": "mfapi",
    },
    {
        "schemeCode": "119063",
        "schemeName": "HDFC Nifty 50 Index Fund - Direct Plan",
        "fundHouse": "HDFC Mutual Fund",
        "category": "Index",
        "source": "mfapi",
    },
    {
        "schemeCode": "120620",
        "schemeName": "ICICI Prudential Nifty 50 Index Fund - Direct Plan Cumulative Option",
        "fundHouse": "ICICI Prudential Mutual Fund",
        "category": "Index",
        "source": "mfapi",
    },
]


def price_data(symbols: list[str], start: date, end: date) -> pd.DataFrame:
    import yfinance as yf

    data = yf.download(
        tickers=symbols,
        start=start.isoformat(),
        end=end.isoformat(),
        auto_adjust=False,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    if data.empty:
        raise RuntimeError("No live stock prices returned.")

    rows = []
    for symbol in symbols:
        symbol_frame = _symbol_frame(data, symbol)
        if symbol_frame.empty:
            continue
        for row_date, row in symbol_frame.iterrows():
            close = row.get("Close")
            adjusted = row.get("Adj Close", close)
            volume = row.get("Volume", 0)
            if pd.isna(close) or pd.isna(adjusted):
                continue
            rows.append(
                {
                    "symbol": symbol,
                    "date": pd.Timestamp(row_date).tz_localize(None),
                    "close": float(close),
                    "adjustedClose": float(adjusted),
                    "volume": int(volume) if not pd.isna(volume) else 0,
                }
            )

    if not rows:
        raise RuntimeError("Live stock data could not be normalized.")
    return pd.DataFrame(rows)


def benchmark_series(start: date, end: date) -> pd.Series:
    import yfinance as yf

    data = yf.download("^NSEI", start=start.isoformat(), end=end.isoformat(), auto_adjust=False, progress=False)
    if data.empty:
        raise RuntimeError("No live benchmark prices returned.")
    frame = data
    if isinstance(frame.columns, pd.MultiIndex):
        ticker_level = 1 if "^NSEI" in frame.columns.get_level_values(1) else 0
        frame = frame.xs("^NSEI", level=ticker_level, axis=1)
    column = "Adj Close" if "Adj Close" in frame.columns else "Close"
    prices = frame[column].dropna()
    prices.index = pd.DatetimeIndex(prices.index).tz_localize(None)
    return prices.pct_change().fillna(0).add(1).cumprod()


def mutual_fund_navs(scheme_codes: list[str]) -> dict[str, pd.Series]:
    funds = {}
    for scheme_code in scheme_codes:
        response = requests.get(f"{MFAPI_BASE_URL}/mf/{scheme_code}", timeout=15)
        response.raise_for_status()
        payload = response.json()
        nav_rows = payload.get("data", [])
        values = {}
        for row in nav_rows:
            nav = row.get("nav")
            raw_date = row.get("date")
            if not nav or not raw_date:
                continue
            values[pd.to_datetime(raw_date, dayfirst=True)] = float(nav)
        if values:
            funds[scheme_code] = pd.Series(values).sort_index()
    if not funds:
        raise RuntimeError("No live mutual fund NAV data returned.")
    return funds


def search_mutual_funds(query: str | None) -> list[dict]:
    if not query:
        return CURATED_MUTUAL_FUNDS

    response = requests.get(f"{MFAPI_BASE_URL}/mf/search", params={"q": query}, timeout=15)
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("value", payload if isinstance(payload, list) else [])
    results = []
    for row in rows[:12]:
        name = row.get("schemeName", "")
        results.append(
            {
                "schemeCode": str(row.get("schemeCode")),
                "schemeName": name,
                "fundHouse": _infer_fund_house(name),
                "category": _infer_category(name),
                "source": "mfapi",
            }
        )
    return results


def _symbol_frame(data: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if isinstance(data.columns, pd.MultiIndex):
        if symbol in data.columns.get_level_values(0):
            return data[symbol].dropna(how="all")
        if symbol in data.columns.get_level_values(1):
            return data.xs(symbol, level=1, axis=1).dropna(how="all")
        return pd.DataFrame()
    return data.dropna(how="all")


def _infer_fund_house(name: str) -> str:
    if not name:
        return "Unknown fund house"
    return f"{name.split()[0]} Mutual Fund"


def _infer_category(name: str) -> str:
    lowered = name.lower()
    if "flexi" in lowered:
        return "Flexi Cap"
    if "large" in lowered:
        return "Large Cap"
    if "mid" in lowered:
        return "Mid Cap"
    if "small" in lowered:
        return "Small Cap"
    return "Mutual Fund"
