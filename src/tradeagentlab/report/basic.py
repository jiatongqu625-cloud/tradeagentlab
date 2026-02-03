from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def _perf_stats(returns: pd.Series) -> dict[str, float]:
    r = returns.dropna()
    if len(r) == 0:
        return {"cagr": 0.0, "sharpe": 0.0, "mdd": 0.0}

    ann = 252
    equity = (1 + r).cumprod()
    cagr = equity.iloc[-1] ** (ann / len(r)) - 1
    sharpe = (r.mean() / (r.std() + 1e-12)) * np.sqrt(ann)
    peak = equity.cummax()
    dd = equity / peak - 1
    mdd = dd.min()
    return {"cagr": float(cagr), "sharpe": float(sharpe), "mdd": float(mdd)}


def write_basic_report(results: dict, out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    equity: pd.Series = results["equity"]
    rets: pd.Series = results["portfolio_returns"]
    stats = _perf_stats(rets)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=equity.index, y=equity.values, name="Equity"))
    fig.update_layout(title="Equity Curve", xaxis_title="Date", yaxis_title="Value")
    fig_path = fig_dir / f"{name}_equity.png"
    fig.write_image(fig_path, scale=2)

    md = f"""# TradeAgentLab Report: {name}

## Summary
- CAGR: **{stats['cagr']:.2%}**
- Sharpe: **{stats['sharpe']:.2f}**
- Max Drawdown: **{stats['mdd']:.2%}**

## Equity curve
![]({fig_path.relative_to(out_dir)})
"""

    (out_dir / f"{name}_report.md").write_text(md)
    (out_dir / "latest_report.md").write_text(md)
