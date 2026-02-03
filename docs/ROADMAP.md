# TradeAgentLab — 14-day build plan

## Deliverables by the end
- Reproducible backtests for a US equity universe
- Baselines + ML strategy + Agent-assisted strategy
- Risk engine with explicit gates (vol targeting, max position, drawdown kill switch)
- Transaction cost model + slippage
- Report generator (markdown + charts) saved into `docs/`
- Paper-trading simulator producing a daily decision log

## Day-by-day
- D1–D2: project scaffolding, data ingest/cache, baseline strategy, minimal backtester
- D3–D4: metrics, plots, report generator
- D5–D6: costs/slippage + risk engine (limits + vol targeting)
- D7–D8: ML walk-forward training/inference pipeline
- D9–D10: Agent layer (structured JSON) + audit logs + risk gate integration
- D11: paper trading simulation (daily run)
- D12: CI + tests + docs polishing
- D13–D14: results write-up + limitations + next steps
