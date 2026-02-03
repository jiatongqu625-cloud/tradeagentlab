from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def _drawdown(equity: pd.Series) -> pd.Series:
    peak = equity.cummax()
    return equity / peak - 1.0


def _perf_stats(returns: pd.Series) -> dict[str, float]:
    r = returns.dropna()
    if len(r) == 0:
        return {"cagr": 0.0, "sharpe": 0.0, "mdd": 0.0, "vol": 0.0}

    ann = 252
    equity = (1 + r).cumprod()
    cagr = equity.iloc[-1] ** (ann / len(r)) - 1
    vol = r.std() * np.sqrt(ann)
    sharpe = (r.mean() / (r.std() + 1e-12)) * np.sqrt(ann)
    dd = _drawdown(equity)
    mdd = dd.min()
    return {"cagr": float(cagr), "sharpe": float(sharpe), "mdd": float(mdd), "vol": float(vol)}


def _monthly_returns_table(returns: pd.Series) -> pd.DataFrame:
    """Monthly returns in a year×month table (percent)."""
    # pandas 3.0+: use month-end alias "ME" ("M" removed)
    m = (1 + returns).resample("ME").prod() - 1
    if m.empty:
        return pd.DataFrame()
    df = m.to_frame("ret")
    df["year"] = df.index.year
    df["month"] = df.index.month
    piv = df.pivot_table(index="year", columns="month", values="ret", aggfunc="sum").sort_index()
    piv = piv.rename(columns={i: pd.Timestamp(2000, i, 1).strftime("%b") for i in piv.columns})
    return (piv * 100).round(2)


def _beta_alpha(strategy_ret: pd.Series, bench_ret: pd.Series) -> tuple[float, float]:
    # Align on the same dates
    x, y = bench_ret.align(strategy_ret, join="inner")
    x = x.astype(float)
    y = y.astype(float)

    if len(x) < 20:
        return 0.0, 0.0

    var = float(np.var(x.to_numpy()))
    if var < 1e-12:
        return 0.0, 0.0

    cov = float(np.cov(x.to_numpy(), y.to_numpy(), ddof=0)[0, 1])
    beta = cov / var
    alpha_daily = float(y.mean() - beta * x.mean())
    alpha_ann = alpha_daily * 252
    return float(beta), float(alpha_ann)


def write_basic_report(results: dict, out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    equity: pd.Series = results["equity"]
    bench_equity: pd.Series = results.get("benchmark_equity")
    rets: pd.Series = results["portfolio_returns"]
    bench_rets: pd.Series | None = results.get("benchmark_returns")
    weights: pd.DataFrame = results["weights"]
    proposed_weights: pd.DataFrame | None = results.get("proposed_weights")
    turnover: pd.Series = results["turnover"]
    cost: pd.Series = results["cost"]
    risk_audit: pd.DataFrame | None = results.get("risk_audit")
    agent: dict | None = results.get("agent")

    stats = _perf_stats(rets)
    bench_stats = _perf_stats(bench_rets) if bench_rets is not None else None
    beta, alpha = _beta_alpha(rets, bench_rets) if bench_rets is not None else (0.0, 0.0)

    # Figures
    # 1) Equity vs benchmark
    fig_eq = go.Figure()
    fig_eq.add_trace(go.Scatter(x=equity.index, y=equity.values, name="Strategy"))
    if bench_equity is not None:
        fig_eq.add_trace(go.Scatter(x=bench_equity.index, y=bench_equity.values, name="SPY (benchmark)"))
    fig_eq.update_layout(title="Equity Curve (vs SPY)", xaxis_title="Date", yaxis_title="Value")
    eq_path = fig_dir / f"{name}_equity_vs_spy.png"
    fig_eq.write_image(eq_path, scale=2)

    # 2) Drawdown
    dd = _drawdown(equity)
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(x=dd.index, y=dd.values, name="Drawdown"))
    fig_dd.update_layout(title="Drawdown", xaxis_title="Date", yaxis_title="Drawdown")
    dd_path = fig_dir / f"{name}_drawdown.png"
    fig_dd.write_image(dd_path, scale=2)

    # 3) Turnover & costs
    fig_tc = go.Figure()
    fig_tc.add_trace(go.Scatter(x=turnover.index, y=turnover.values, name="Turnover (|Δw| sum)"))
    fig_tc.add_trace(go.Scatter(x=cost.index, y=cost.cumsum().values, name="Cumulative cost"))
    fig_tc.update_layout(title="Turnover & Costs", xaxis_title="Date")
    tc_path = fig_dir / f"{name}_turnover_cost.png"
    fig_tc.write_image(tc_path, scale=2)

    # 4) Rolling risk metrics (vol) + risk overlay (scale)
    vol_path = None
    scale_path = None
    scale_hist_path = None
    risk_summary = "(risk audit not available)"
    audit_md = "(no audit)"

    # Rolling vol (20d, annualized) strategy vs SPY
    vol_window = 20
    strat_vol = rets.rolling(vol_window, min_periods=vol_window).std(ddof=0) * np.sqrt(252)
    if bench_rets is not None:
        bench_vol = bench_rets.rolling(vol_window, min_periods=vol_window).std(ddof=0) * np.sqrt(252)
    else:
        bench_vol = None

    fig_v = go.Figure()
    fig_v.add_trace(go.Scatter(x=strat_vol.index, y=strat_vol.values, name=f"Strategy {vol_window}D vol"))
    if bench_vol is not None:
        fig_v.add_trace(go.Scatter(x=bench_vol.index, y=bench_vol.values, name=f"SPY {vol_window}D vol"))
    fig_v.update_layout(
        title=f"Rolling volatility ({vol_window}D, annualized)",
        xaxis_title="Date",
        yaxis_title="Vol",
    )
    vol_path = fig_dir / f"{name}_rolling_vol.png"
    fig_v.write_image(vol_path, scale=2)

    # Exposure (invested weight) and cash weight over time
    exposure = weights.sum(axis=1).clip(lower=0.0)
    cash = (1.0 - exposure).clip(lower=0.0)
    fig_e = go.Figure()
    fig_e.add_trace(go.Scatter(x=exposure.index, y=exposure.values, name="Gross exposure"))
    fig_e.add_trace(go.Scatter(x=cash.index, y=cash.values, name="Cash weight"))
    fig_e.update_layout(title="Exposure & Cash over time", xaxis_title="Date", yaxis_title="Weight")
    exposure_path = fig_dir / f"{name}_exposure_cash.png"
    fig_e.write_image(exposure_path, scale=2)

    if risk_audit is not None and "scale" in risk_audit.columns:
        # Exposure scale time series
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(x=risk_audit.index, y=risk_audit["scale"].values, name="Exposure scale"))
        fig_s.update_layout(title="Risk overlay: exposure scaling", xaxis_title="Date", yaxis_title="Scale")
        scale_path = fig_dir / f"{name}_risk_scale.png"
        fig_s.write_image(scale_path, scale=2)

        # Exposure scale distribution
        fig_h = go.Figure()
        fig_h.add_trace(go.Histogram(x=risk_audit["scale"].values, nbinsx=30, name="scale"))
        fig_h.update_layout(title="Exposure scale distribution", xaxis_title="Scale", yaxis_title="Count")
        scale_hist_path = fig_dir / f"{name}_risk_scale_hist.png"
        fig_h.write_image(scale_hist_path, scale=2)

        last_scale = float(risk_audit["scale"].iloc[-1])
        killed_days = int(risk_audit.get("killed", pd.Series(False, index=risk_audit.index)).sum())
        risk_summary = f"- Last scale: **{last_scale:.2f}**\n- Days killed (scale=0 due to DD): **{killed_days}**"

        cols = [c for c in ["scale", "vol_est_ann", "drawdown", "killed", "clipped", "reason"] if c in risk_audit.columns]
        tail = risk_audit[cols].tail(10).copy()
        tail.index = tail.index.strftime("%Y-%m-%d")
        if "vol_est_ann" in tail.columns:
            tail["vol_est_ann"] = (tail["vol_est_ann"] * 100).round(2)
        if "drawdown" in tail.columns:
            tail["drawdown"] = (tail["drawdown"] * 100).round(2)
        audit_md = tail.to_markdown()

    # 5) Latest holdings
    latest_w = weights.iloc[-1].sort_values(ascending=False)
    top = latest_w[latest_w > 0].head(10)

    # Monthly table
    mtab = _monthly_returns_table(rets)
    mtab_md = mtab.to_markdown() if not mtab.empty else "(not enough data)"

    bench_line = ""
    if bench_stats is not None:
        bench_line = (
            f"\n- Benchmark (SPY) CAGR: **{bench_stats['cagr']:.2%}**, Sharpe: **{bench_stats['sharpe']:.2f}**, "
            f"MDD: **{bench_stats['mdd']:.2%}**\n"
        )

    # Agent summary for the report
    agent_md = "(agent not run)"
    if agent is not None:
        research = agent.get("research")
        decision = agent.get("decision")
        execution = agent.get("execution")
        paths = agent.get("paths", {})
        decision_json = paths.get("decision", "docs/agent/latest_decision.json")
        execution_json = paths.get("execution", "docs/agent/latest_execution.json")

        # Build compact tables
        if decision is not None and hasattr(decision, "proposed_positions"):
            pos = [(p.ticker, p.weight, p.reason) for p in decision.proposed_positions]
            dfp = pd.DataFrame(pos, columns=["ticker", "proposed", "reason"]).sort_values("proposed", ascending=False)

            exec_md = "(no execution plan)"
            if execution is not None and hasattr(execution, "rows"):
                rows = [(r.ticker, r.proposed_weight, r.executed_weight, r.status) for r in execution.rows]
                dfx = pd.DataFrame(rows, columns=["ticker", "proposed", "executed", "status"]).sort_values(
                    "proposed", ascending=False
                )
                dfx["delta"] = (dfx["executed"] - dfx["proposed"]).round(4)
                exec_md = dfx.to_markdown(index=False)

            gate_reason = getattr(execution, "gate_reason", "") if execution is not None else ""
            cash_w = getattr(execution, "cash_weight", None) if execution is not None else None
            gross = getattr(execution, "gross_exposure", None) if execution is not None else None

            # Per-ticker gate reasons (trim to keep report readable)
            reasons_md = "(no per-ticker reasons)"
            if execution is not None and hasattr(execution, "rows"):
                rrows = [(r.ticker, r.status, r.gate_reason) for r in execution.rows]
                dfr = pd.DataFrame(rrows, columns=["ticker", "status", "gate_reason"])
                dfr["gate_reason"] = dfr["gate_reason"].str.slice(0, 140)
                reasons_md = dfr.to_markdown(index=False)

            exec_summary = ""
            if cash_w is not None and gross is not None:
                exec_summary = f"**Executed gross exposure:** {float(gross):.2%}  |  **Cash weight:** {float(cash_w):.2%}\n\n"

            agent_md = (
                f"**As of:** `{decision.as_of}`\n\n"
                f"**Regime:** `{research.regime.label}` (conf={research.regime.confidence:.2f})\n\n"
                f"**Decision JSON:** `{Path(decision_json).as_posix()}`\n"
                f"**Execution JSON:** `{Path(execution_json).as_posix()}`\n\n"
                + exec_summary
                + f"### Proposed positions\n{dfp.to_markdown(index=False)}\n\n"
                f"### Risk-gated execution\n{exec_md}\n\n"
                f"**Gate reason (day-level, as_of):** {gate_reason}\n\n"
                f"### Per-ticker gate reasons\n{reasons_md}\n"
            )

    md = f"""# TradeAgentLab Report: {name}

## Summary (strategy)
- CAGR: **{stats['cagr']:.2%}**
- Vol (ann.): **{stats['vol']:.2%}**
- Sharpe: **{stats['sharpe']:.2f}**
- Max Drawdown: **{stats['mdd']:.2%}**
- Beta vs SPY: **{beta:.2f}**
- Alpha (ann., naive): **{alpha:.2%}**
{bench_line}

## Equity (vs benchmark)
![]({eq_path.relative_to(out_dir)})

## Drawdown
![]({dd_path.relative_to(out_dir)})

## Turnover & transaction costs
![]({tc_path.relative_to(out_dir)})

## Rolling risk metrics
![]({vol_path.relative_to(out_dir)})

## Exposure & cash over time
![]({exposure_path.relative_to(out_dir)})

## Risk overlay (exposure scale)
{risk_summary}

{f"![]({scale_path.relative_to(out_dir)})" if scale_path is not None else ''}

### Exposure scale distribution
{f"![]({scale_hist_path.relative_to(out_dir)})" if scale_hist_path is not None else ''}

## Risk events timeline
- Kill switch triggers: **{int(risk_audit["killed"].sum()) if risk_audit is not None and "killed" in risk_audit.columns else 0}** days
- Scale clipped (raw_scale > max): **{int(risk_audit["clipped"].sum()) if risk_audit is not None and "clipped" in risk_audit.columns else 0}** days

{("### Kill switch days\n" + risk_audit.loc[risk_audit["killed"], ["drawdown", "reason"]].tail(20).assign(drawdown=lambda d: (d["drawdown"]*100).round(2)).rename(columns={"drawdown":"drawdown_%"}).to_markdown()) if risk_audit is not None and "killed" in risk_audit.columns and risk_audit["killed"].any() else "### Kill switch days\n(none)"}

{("### Clipped days\n" + risk_audit.loc[risk_audit.get("clipped", False), ["vol_est_ann", "scale", "reason"]].tail(20).assign(vol_est_ann=lambda d: (d["vol_est_ann"]*100).round(2)).rename(columns={"vol_est_ann":"vol_est_%"}).to_markdown()) if risk_audit is not None and "clipped" in risk_audit.columns and risk_audit["clipped"].any() else "### Clipped days\n(none)"}

## Risk audit (last 10 days)
- `vol_est_ann` and `drawdown` are shown in **%**.

{audit_md}

## Latest holdings (top 10 weights)
{top.to_frame('weight').to_markdown() if len(top) else '(no positions)'}

## Monthly returns (%)
{mtab_md}

## Agent decision (structured & auditable)
{agent_md}

## Notes
- Costs are modeled as: `turnover * transaction_cost_bps` (simplified).
- This is a research backtest, not investment advice.
"""

    (out_dir / f"{name}_report.md").write_text(md)
    (out_dir / "latest_report.md").write_text(md)
