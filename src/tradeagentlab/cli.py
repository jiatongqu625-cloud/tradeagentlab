from __future__ import annotations

import argparse
from pathlib import Path

from tradeagentlab.backtest.runner import run_backtest


def main() -> None:
    parser = argparse.ArgumentParser(prog="tal", description="TradeAgentLab CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_bt = sub.add_parser("backtest", help="Run a backtest from a YAML config")
    p_bt.add_argument("--config", required=True, type=str)

    args = parser.parse_args()

    if args.cmd == "backtest":
        run_backtest(Path(args.config))
