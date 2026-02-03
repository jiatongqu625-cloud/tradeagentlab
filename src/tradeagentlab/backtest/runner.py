from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from tradeagentlab.data.yf import load_prices
from tradeagentlab.features.tech import compute_momentum_signal
from tradeagentlab.report.basic import write_basic_report


@dataclass
class BacktestConfig:
    tickers: list[str]
    start: str
    end: str
    lookback: int
    initial_cash: float
    max_position_weight: float
    transaction_cost_bps: float
    report_out_dir: str
    report_name: str


def _read_config(path: Path) -> BacktestConfig:
    obj = yaml.safe_load(path.read_text())
    u = obj["universe"]
    s = obj["strategy"]
    p = obj["portfolio"]
    r = obj.get("report", {})

    return BacktestConfig(
        tickers=list(u["tickers"]),
        start=str(u["start"]),
        end=str(u["end"]),
        lookback=int(s["params"]["lookback"]),
        initial_cash=float(p["initial_cash"]),
        max_position_weight=float(p["max_position_weight"]),
        transaction_cost_bps=float(p.get("transaction_cost_bps", 0.0)),
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

    # turnover & transaction costs
    turnover = w.diff().abs().sum(axis=1).fillna(0.0)
    cost = turnover * (cfg.transaction_cost_bps / 1e4)

    port_ret = (w.shift(1).fillna(0.0) * rets).sum(axis=1) - cost
    equity = (1.0 + port_ret).cumprod() * cfg.initial_cash
    bench_equity = (1.0 + bench_ret).cumprod() * cfg.initial_cash

    results = {
        "config": cfg,
        "prices": prices,
        "benchmark": bench,
        "weights": w,
        "portfolio_returns": port_ret,
        "benchmark_returns": bench_ret,
        "equity": equity,
        "benchmark_equity": bench_equity,
        "turnover": turnover,
        "cost": cost,
    }

    write_basic_report(results, out_dir=Path(cfg.report_out_dir), name=cfg.report_name)
