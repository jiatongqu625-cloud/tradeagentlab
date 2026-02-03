from __future__ import annotations

import pandas as pd

from tradeagentlab.agents.schema import ExecutionPlan, ExecutionRow


def build_execution_plan(
    as_of: str,
    proposed: pd.Series,
    risk_audit: pd.DataFrame,
) -> ExecutionPlan:
    """Apply day-level risk gate to proposed weights.

    Current gate uses the risk overlay exposure scale (and kill-switch) from `risk_audit`.

    - If scale==0 => all executed weights are 0 (killed/warmup)
    - Else executed = proposed * scale

    Returns an auditable execution plan (rows per ticker).
    """
    if risk_audit is None or len(risk_audit) == 0:
        scale = 1.0
        reason = "NO_RISK_AUDIT: scale=1"
    else:
        # risk_audit index is timestamps; match the last row (as_of)
        row = risk_audit.iloc[-1]
        scale = float(row.get("scale", 1.0))
        reason = str(row.get("reason", ""))

    rows: list[ExecutionRow] = []
    for ticker, w in proposed.items():
        exec_w = float(w) * scale
        status = "accepted" if exec_w > 0 else "rejected"
        rows.append(
            ExecutionRow(
                ticker=str(ticker),
                proposed_weight=float(w),
                executed_weight=float(exec_w),
                status=status,
                gate_reason=reason,
            )
        )

    return ExecutionPlan(
        as_of=as_of,
        scale=scale,
        gate_reason=reason,
        rows=rows,
    )
