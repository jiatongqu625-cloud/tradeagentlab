from __future__ import annotations

import pandas as pd


def compute_momentum_signal(prices: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """Binary long signal based on lookback returns (toy baseline).

    For each day: long tickers with positive lookback return.
    """
    mom = prices.pct_change(lookback)
    sig = (mom > 0).astype(int)
    return sig
