from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from tradeagentlab.data.yf import load_prices
from tradeagentlab.features.tech import compute_momentum_signal
from tradeagentlab.agents.orchestrator import run_agent_decision
from tradeagentlab.report.basic import write_basic_report
from tradeagentlab.risk.engine import RiskConfig, apply_risk


@dataclass
class BacktestConfig:
    tickers: list[str]
    start: str
    end: str
    lookback: int
    initial_cash: float
    max_position_weight: float
    transaction_cost_bps: float
    risk: RiskConfig
    agent: dict
    report_out_dir: str
    report_name: str


def _read_config(path: Path) -> BacktestConfig:
    obj = yaml.safe_load(path.read_text())
    u = obj["universe"]
    s = obj["strategy"]
    p = obj["portfolio"]
    rk = obj.get("risk", {})
    agent = obj.get("agent", {})
    r = obj.get("report", {})

    risk = RiskConfig(
        target_vol_ann=float(rk.get("target_vol_ann", 0.12)),
        vol_lookback=int(rk.get("vol_lookback", 20)),
        max_leverage=float(rk.get("max_leverage", 1.0)),
        dd_kill=float(rk.get("dd_kill", 0.20)),
        dd_recover=(float(rk["dd_recover"]) if "dd_recover" in rk and rk["dd_recover"] is not None else None),
    )

    return BacktestConfig(
        tickers=list(u["tickers"]),
        start=str(u["start"]),
        end=str(u["end"]),
        lookback=int(s["params"]["lookback"]),
        initial_cash=float(p["initial_cash"]),
        max_position_weight=float(p["max_position_weight"]),
        transaction_cost_bps=float(p.get("transaction_cost_bps", 0.0)),
        risk=risk,
        agent=dict(agent),
        report_out_dir=str(r.get("out_dir", "docs")),
        report_name=str(r.get("name", "run")),
    )


def run_backtest(config_path: Path) -> None:
    cfg = _read_config(config_path)

    prices = load_prices(cfg.tickers, cfg.start, cfg.end)
    # prices: columns=tickers, index=Date

    # Benchmark (SPY) for comparison in reports
    bench = load_prices(["SPY"], cfg.start, cfg.end)["SPY"].reindex(prices.index).ffill()

    signal = compute_momentum_signal(prices, lookback=cfg.lookback)
    # naive: daily rebalance to equal-weight long tickers with positive momentum

    rets = prices.pct_change().fillna(0.0)
    bench_ret = bench.pct_change().fillna(0.0)

    # Build weights: equal-weight across tickers with signal==1
    w = signal.div(signal.sum(axis=1).replace(0, pd.NA), axis=0).fillna(0.0)
    w = w.clip(upper=cfg.max_position_weight)
    w = w.div(w.sum(axis=1).replace(0, pd.NA), axis=0).fillna(0.0)

    # Risk overlays (vol targeting + drawdown kill) and transaction costs
    risk_out = apply_risk(
        base_weights=w,
        asset_returns=rets,
        transaction_cost_bps=cfg.transaction_cost_bps,
        cfg=cfg.risk,
    )

    w_exec = risk_out["weights"]
    port_ret = risk_out["portfolio_returns"]
    audit = risk_out["audit"]

    equity = (1.0 + port_ret).cumprod() * cfg.initial_cash
    bench_equity = (1.0 + bench_ret).cumprod() * cfg.initial_cash

    # Agent artifacts (structured, auditable): propose BEFORE risk; execute AFTER risk.
    agent_out = run_agent_decision(
        prices=prices,
        proposed_weights=w,
        risk_audit=audit,
        out_dir=Path(cfg.report_out_dir),
        name=cfg.report_name,
        max_ticker_vol_ann=float(cfg.agent.get("max_ticker_vol_ann", 0.35)),
        vol_cap_mode=str(cfg.agent.get("vol_cap_mode", "scale")),
    )

    results = {
        "config": cfg,
        "prices": prices,
        "benchmark": bench,
        "weights": w_exec,
        "proposed_weights": w,
        "portfolio_returns": port_ret,
        "benchmark_returns": bench_ret,
        "equity": equity,
        "benchmark_equity": bench_equity,
        "turnover": audit["turnover"],
        "cost": audit["cost"],
        "risk_audit": audit,
        "agent": agent_out,
    }

    write_basic_report(results, out_dir=Path(cfg.report_out_dir), name=cfg.report_name)
