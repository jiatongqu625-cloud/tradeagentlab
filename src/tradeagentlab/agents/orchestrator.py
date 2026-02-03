from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from tradeagentlab.agents.research import build_research_note
from tradeagentlab.agents.risk_gate import build_execution_plan
from tradeagentlab.agents.signal import propose_positions_from_momentum


def run_agent_decision(
    prices: pd.DataFrame,
    proposed_weights: pd.DataFrame,
    risk_audit: pd.DataFrame | None,
    out_dir: Path,
    name: str,
) -> dict:
    """Generate a research note + structured decision + risk-gated execution plan and save artifacts."""
    out_dir.mkdir(parents=True, exist_ok=True)
    agent_dir = out_dir / "agent"
    agent_dir.mkdir(parents=True, exist_ok=True)

    as_of = prices.index.max()
    research = build_research_note(prices, as_of=as_of)
    decision = propose_positions_from_momentum(research, proposed_weights.loc[as_of])

    # Build a risk-gated execution plan using the risk overlay scale
    proposed = pd.Series({p.ticker: p.weight for p in decision.proposed_positions})
    execution = build_execution_plan(as_of=decision.as_of, proposed=proposed, risk_audit=risk_audit)

    research_path = agent_dir / f"{name}_research.json"
    decision_path = agent_dir / f"{name}_decision.json"
    exec_path = agent_dir / f"{name}_execution.json"

    research_path.write_text(research.model_dump_json(indent=2))
    decision_path.write_text(decision.model_dump_json(indent=2))
    exec_path.write_text(execution.model_dump_json(indent=2))

    # also keep pointers
    (agent_dir / "latest_research.json").write_text(research.model_dump_json(indent=2))
    (agent_dir / "latest_decision.json").write_text(decision.model_dump_json(indent=2))
    (agent_dir / "latest_execution.json").write_text(execution.model_dump_json(indent=2))

    return {
        "research": research,
        "decision": decision,
        "execution": execution,
        "paths": {
            "research": str(research_path),
            "decision": str(decision_path),
            "execution": str(exec_path),
        },
    }
