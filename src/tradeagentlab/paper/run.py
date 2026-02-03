from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from tradeagentlab.agents.orchestrator import run_agent_decision
from tradeagentlab.data.yf import load_prices
from tradeagentlab.features.tech import compute_momentum_signal
from tradeagentlab.risk.engine import RiskConfig, apply_risk


@dataclass
class PaperConfig:
    tickers: list[str]
    start: str
    end: str | None
    lookback: int
    max_position_weight: float
    transaction_cost_bps: float
    risk: RiskConfig
    agent: dict
    out_dir: str


def _read_config(path: Path) -> PaperConfig:
    obj = yaml.safe_load(path.read_text())
    u = obj["universe"]
    s = obj["strategy"]
    p = obj["portfolio"]
    rk = obj.get("risk", {})
    ag = obj.get("agent", {})
    r = obj.get("report", {})

    risk = RiskConfig(
        target_vol_ann=float(rk.get("target_vol_ann", 0.12)),
        vol_lookback=int(rk.get("vol_lookback", 20)),
        max_leverage=float(rk.get("max_leverage", 1.0)),
        dd_kill=float(rk.get("dd_kill", 0.35)),
        dd_recover=(float(rk["dd_recover"]) if "dd_recover" in rk and rk["dd_recover"] is not None else None),
    )

    return PaperConfig(
        tickers=list(u["tickers"]),
        start=str(u["start"]),
        end=(str(u["end"]) if "end" in u and u["end"] is not None else None),
        lookback=int(s["params"]["lookback"]),
        max_position_weight=float(p["max_position_weight"]),
        transaction_cost_bps=float(p.get("transaction_cost_bps", 0.0)),
        risk=risk,
        agent=dict(ag),
        out_dir=str(r.get("out_dir", "docs")),
    )


def run_paper(config_path: Path) -> Path:
    """Generate today's paper-trading decision artifacts + a daily markdown report."""
    cfg = _read_config(config_path)
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Use config end if provided, otherwise run up to today.
    end = cfg.end or str(pd.Timestamp.today().date())

    prices = load_prices(cfg.tickers, cfg.start, end)
    rets = prices.pct_change().fillna(0.0)

    # Proposed weights (baseline)
    signal = compute_momentum_signal(prices, lookback=cfg.lookback)
    w = signal.div(signal.sum(axis=1).replace(0, pd.NA), axis=0).fillna(0.0)
    w = w.clip(upper=cfg.max_position_weight)
    w = w.div(w.sum(axis=1).replace(0, pd.NA), axis=0).fillna(0.0)

    # Risk overlay (for scale/audit). We don't need executed weights here, but audit does.
    risk_out = apply_risk(
        base_weights=w,
        asset_returns=rets,
        transaction_cost_bps=cfg.transaction_cost_bps,
        cfg=cfg.risk,
    )
    audit = risk_out["audit"]

    # Agent decision + risk-gated execution plan
    agent_out = run_agent_decision(
        prices=prices,
        proposed_weights=w,
        risk_audit=audit,
        out_dir=out_dir,
        name="paper",
        max_ticker_vol_ann=float(cfg.agent.get("max_ticker_vol_ann", 0.20)),
        vol_cap_mode=str(cfg.agent.get("vol_cap_mode", "scale")),
    )

    decision = agent_out["decision"]
    execution = agent_out["execution"]

    # Daily markdown
    today = date.today().isoformat()
    daily_dir = out_dir / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    daily_path = daily_dir / f"{today}.md"

    rows = execution.rows
    exec_df = pd.DataFrame(
        [(r.ticker, r.proposed_weight, r.executed_weight, r.status) for r in rows],
        columns=["ticker", "proposed", "executed", "status"],
    ).sort_values("executed", ascending=False)

    md = f"""# Paper Trading — {today}

**As of:** {decision.as_of}

## Regime
- {agent_out['research'].regime.label} (conf={agent_out['research'].regime.confidence:.2f})

## Execution summary
- Gross exposure: **{execution.gross_exposure:.2%}**
- Cash weight: **{execution.cash_weight:.2%}**
- Day-level gate reason: {execution.gate_reason}

## Executable target weights
{exec_df.to_markdown(index=False)}

## Notes
- This is a simulated paper run. Not financial advice.
"""

    daily_path.write_text(md)

    # Append to decisions.csv
    csv_path = daily_dir / "decisions.csv"
    new_file = not csv_path.exists()
    with csv_path.open("a", newline="") as f:
        wtr = csv.writer(f)
        if new_file:
            wtr.writerow(["date", "as_of", "regime", "gross_exposure", "cash_weight", "gate_reason"])
        wtr.writerow(
            [
                today,
                decision.as_of,
                agent_out["research"].regime.label,
                f"{execution.gross_exposure:.6f}",
                f"{execution.cash_weight:.6f}",
                execution.gate_reason,
            ]
        )

    return daily_path
