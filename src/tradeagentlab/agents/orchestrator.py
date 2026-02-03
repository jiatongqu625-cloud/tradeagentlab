from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from tradeagentlab.agents.research import build_research_note
from tradeagentlab.agents.signal import propose_positions_from_momentum


def run_agent_decision(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    out_dir: Path,
    name: str,
) -> dict:
    """Generate a research note + structured decision and save artifacts."""
    out_dir.mkdir(parents=True, exist_ok=True)
    agent_dir = out_dir / "agent"
    agent_dir.mkdir(parents=True, exist_ok=True)

    as_of = prices.index.max()
    research = build_research_note(prices, as_of=as_of)
    decision = propose_positions_from_momentum(research, weights.loc[as_of])

    research_path = agent_dir / f"{name}_research.json"
    decision_path = agent_dir / f"{name}_decision.json"

    research_path.write_text(research.model_dump_json(indent=2))
    decision_path.write_text(decision.model_dump_json(indent=2))

    # also keep pointers
    (agent_dir / "latest_research.json").write_text(research.model_dump_json(indent=2))
    (agent_dir / "latest_decision.json").write_text(decision.model_dump_json(indent=2))

    return {
        "research": research,
        "decision": decision,
        "paths": {
            "research": str(research_path),
            "decision": str(decision_path),
        },
    }
