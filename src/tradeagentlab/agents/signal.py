from __future__ import annotations

import pandas as pd

from tradeagentlab.agents.schema import AgentDecision, PositionTarget, ResearchNote


def propose_positions_from_momentum(
    research: ResearchNote,
    weights_today: pd.Series,
    max_positions: int = 10,
) -> AgentDecision:
    """Turn the current strategy weights into an auditable 'agent decision'.

    This is intentionally deterministic: the goal is to demonstrate *structure + auditability*.
    """
    w = weights_today[weights_today > 0].sort_values(ascending=False).head(max_positions)

    positions: list[PositionTarget] = []
    for ticker, weight in w.items():
        snap = next((s for s in research.universe if s.ticker == ticker), None)
        if snap is None:
            reason = "Selected by momentum baseline."
        else:
            reason = f"20D ret={snap.ret_20d:.2%}, trend={snap.trend}, vol20D={snap.vol_20d_ann:.2%}."
        positions.append(PositionTarget(ticker=ticker, weight=float(weight), reason=reason))

    risk_notes = [
        f"Regime: {research.regime.label} (conf={research.regime.confidence:.2f})",
        "Final execution must pass hard risk gates (vol targeting, drawdown kill switch, position limits).",
    ]

    return AgentDecision(
        as_of=research.as_of,
        proposed_positions=positions,
        risk_notes=risk_notes,
        constraints={"max_positions": float(max_positions)},
    )
