from __future__ import annotations

import pandas as pd

from tradeagentlab.agents.schema import ExecutionPlan, ExecutionRow, ResearchNote


def build_execution_plan(
    as_of: str,
    proposed: pd.Series,
    risk_audit: pd.DataFrame,
    research: ResearchNote | None = None,
    max_ticker_vol_ann: float = 0.35,
    vol_cap_mode: str = "scale",  # scale|reject
) -> ExecutionPlan:
    """Apply risk gates to proposed weights.

    Gates:
    1) Day-level overlay via `risk_audit.scale` (vol targeting / kill switch)
    2) Per-ticker volatility cap using ResearchNote 20D vol (optional)

    - If scale==0 => all executed weights are 0
    - If ticker vol > cap:
        - mode=reject => executed=0
        - mode=scale  => executed *= cap/vol

    Returns an auditable execution plan (rows per ticker).
    """
    if risk_audit is None or len(risk_audit) == 0:
        scale = 1.0
        reason = "NO_RISK_AUDIT: scale=1"
    else:
        row = risk_audit.iloc[-1]
        scale = float(row.get("scale", 1.0))
        reason = str(row.get("reason", ""))

    rows: list[ExecutionRow] = []
    for ticker, w in proposed.items():
        w = float(w)

        # Per-ticker volatility cap
        vol = None
        if research is not None:
            snap = next((s for s in research.universe if s.ticker == str(ticker)), None)
            if snap is not None:
                vol = float(snap.vol_20d_ann)

        per_ticker_factor = 1.0
        per_ticker_note = ""
        if vol is not None and vol > max_ticker_vol_ann:
            if vol_cap_mode == "reject":
                per_ticker_factor = 0.0
                per_ticker_note = f" | VOL_CAP_REJECT: vol20D={vol:.2%} > {max_ticker_vol_ann:.2%}"
            else:
                per_ticker_factor = max_ticker_vol_ann / vol
                per_ticker_note = (
                    f" | VOL_CAP_SCALE: vol20D={vol:.2%} > {max_ticker_vol_ann:.2%} → factor={per_ticker_factor:.2f}"
                )

        exec_w = w * scale * per_ticker_factor
        status = "accepted" if exec_w > 0 else "rejected"
        rows.append(
            ExecutionRow(
                ticker=str(ticker),
                proposed_weight=w,
                executed_weight=float(exec_w),
                status=status,
                gate_reason=reason + per_ticker_note,
            )
        )

    return ExecutionPlan(
        as_of=as_of,
        scale=scale,
        gate_reason=reason,
        rows=rows,
    )
