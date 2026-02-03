# TradeAgentLab

A **CPU-only** US equities lab that goes from **data → features → ML signals → (LLM) agent research/decision → risk gates → backtest → reports → paper-trading simulation**.

> Not financial advice. Research project.

## Why this repo looks “senior”
- Reproducible pipelines (cached market data, configs)
- Walk-forward evaluation + transaction costs
- Explicit risk engine (position limits, vol targeting, kill switch)
- Agent outputs are **structured** and **auditable** (JSON), then constrained by hard risk rules
- One-command backtests + auto-generated markdown reports with charts

## Quickstart
```bash
cd tradeagentlab
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"

# Run a tiny backtest example (will download & cache data)
tal backtest --config configs/backtest.example.yaml

# Run a paper-trading style daily decision (writes docs/daily/YYYY-MM-DD.md)
tal paper --config configs/backtest.example.yaml
```

## Repo layout
- `src/tradeagentlab/` — library code
- `configs/` — universe + backtest configs
- `docs/` — generated reports/figures

## Roadmap (14 days)
See `docs/ROADMAP.md`.

