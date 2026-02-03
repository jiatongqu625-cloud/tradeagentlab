from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

CACHE_DIR = Path(".cache/marketdata")


def load_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Load adjusted close prices from Yahoo Finance, cached as Parquet."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = f"{'-'.join(tickers)}_{start}_{end}".replace(":", "-")
    path = CACHE_DIR / f"prices_{key}.parquet"

    if path.exists():
        df = pd.read_parquet(path)
        df.index = pd.to_datetime(df.index)
        return df

    data = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        group_by="column",
        threads=True,
    )

    # yf returns different shapes for single vs multi ticker
    if isinstance(data.columns, pd.MultiIndex):
        px = data["Close"].copy()
    else:
        px = data[["Close"]].rename(columns={"Close": tickers[0]})

    px = px.dropna(how="all").ffill()
    px.to_parquet(path)
    return px
