from __future__ import annotations

import numpy as np
import pandas as pd

from tradeagentlab.agents.schema import MarketRegime, ResearchNote, TickerSnapshot


def _trend_from_ret(ret: float, eps: float = 0.01) -> str:
    if ret > eps:
        return "up"
    if ret < -eps:
        return "down"
    return "flat"


def build_research_note(prices: pd.DataFrame, as_of: pd.Timestamp | None = None) -> ResearchNote:
    """Deterministic research summary (no LLM required).

    Uses only price/vol/trend diagnostics; good enough for an auditable agent demo.
    """
    if as_of is None:
        as_of = prices.index.max()

    px = prices.loc[:as_of].copy()
    rets = px.pct_change().dropna()

    snap: list[TickerSnapshot] = []
    for t in px.columns:
        r20 = float(px[t].pct_change(20).iloc[-1])
        v20 = float(rets[t].rolling(20).std(ddof=0).iloc[-1] * np.sqrt(252))
        snap.append(
            TickerSnapshot(
                ticker=t,
                ret_20d=r20,
                vol_20d_ann=v20,
                trend=_trend_from_ret(r20),
            )
        )

    # crude regime heuristic using SPY and dispersion
    spy = next((s for s in snap if s.ticker == "SPY"), None)
    mean_r = float(np.mean([s.ret_20d for s in snap])) if snap else 0.0
    disp = float(np.std([s.ret_20d for s in snap])) if snap else 0.0

    evidence: list[str] = []
    if spy is not None:
        evidence.append(f"SPY 20D return: {spy.ret_20d:.2%}, vol20D: {spy.vol_20d_ann:.2%}")
    evidence.append(f"Universe mean 20D return: {mean_r:.2%}, dispersion: {disp:.2%}")

    if spy is not None and spy.ret_20d > 0 and mean_r > 0:
        regime = MarketRegime(label="risk-on", confidence=0.65, evidence=evidence)
        summary = "Broad 20D momentum is positive; regime leaning risk-on."
    elif spy is not None and spy.ret_20d < 0 and mean_r < 0:
        regime = MarketRegime(label="risk-off", confidence=0.65, evidence=evidence)
        summary = "Broad 20D momentum is negative; regime leaning risk-off."
    else:
        regime = MarketRegime(label="mixed", confidence=0.55, evidence=evidence)
        summary = "Mixed 20D momentum; regime uncertain/mixed."

    return ResearchNote(
        as_of=str(as_of.date()),
        regime=regime,
        universe=snap,
        summary=summary,
    )
