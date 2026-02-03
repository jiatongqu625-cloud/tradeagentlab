from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class RiskConfig:
    # Vol targeting
    target_vol_ann: float = 0.12  # e.g. 12% annualized
    vol_lookback: int = 20
    max_leverage: float = 1.0  # keep <=1 for long-only cash+equities

    # Drawdown kill switch
    dd_kill: float = 0.20  # kill if drawdown <= -20%
    dd_recover: float | None = None  # if set, re-enable when drawdown > -dd_recover


def apply_risk(
    base_weights: pd.DataFrame,
    asset_returns: pd.DataFrame,
    transaction_cost_bps: float,
    cfg: RiskConfig,
) -> dict:
    """Apply simple risk overlays:

    - Vol targeting: scale exposure based on rolling vol of *unscaled* strategy returns.
    - Drawdown kill switch: set exposure=0 when drawdown breaches threshold.

    Returns dict with scaled weights, portfolio returns, and an audit log.
    """

    # Base (unscaled) portfolio returns (no costs)
    base_port_ret = (base_weights.shift(1).fillna(0.0) * asset_returns).sum(axis=1)

    # Rolling vol estimate (annualized)
    roll = base_port_ret.rolling(cfg.vol_lookback, min_periods=cfg.vol_lookback)
    vol_est = roll.std(ddof=0) * np.sqrt(252)

    # Exposure scaling: target_vol / vol_est, clipped
    raw_scale = cfg.target_vol_ann / vol_est
    scale = raw_scale.clip(lower=0.0, upper=cfg.max_leverage)
    scale = scale.fillna(0.0)

    # Apply drawdown kill switch on the scaled (pre-cost) equity
    pre_cost_scaled_ret = scale.shift(1).fillna(0.0) * base_port_ret
    pre_cost_equity = (1.0 + pre_cost_scaled_ret).cumprod()
    peak = pre_cost_equity.cummax()
    dd = pre_cost_equity / peak - 1.0

    killed = pd.Series(False, index=scale.index)
    live = True
    for i, t in enumerate(scale.index):
        if not live:
            # Optionally allow recovery
            if cfg.dd_recover is not None and dd.loc[t] > -cfg.dd_recover:
                live = True
            else:
                killed.iloc[i] = True
                continue
        if dd.loc[t] <= -cfg.dd_kill:
            live = False
            killed.iloc[i] = True

    scale2 = scale.mask(killed, 0.0)

    # Human-readable audit reasons (for reports)
    reason = pd.Series("", index=scale.index, dtype=object)
    clipped_flag = pd.Series(False, index=scale.index)

    for t in scale.index:
        if killed.loc[t]:
            reason.loc[t] = (
                f"KILL_SWITCH: dd={dd.loc[t]:.2%} <= -{cfg.dd_kill:.0%} → scale=0"
            )
            clipped_flag.loc[t] = False
        elif np.isnan(vol_est.loc[t]):
            reason.loc[t] = f"WARMUP: need {cfg.vol_lookback}d for vol_est → scale=0"
            clipped_flag.loc[t] = False
        else:
            rs = float(raw_scale.loc[t])
            s2 = float(scale2.loc[t])
            clipped = abs(rs - s2) > 1e-9
            clipped_flag.loc[t] = clipped
            clip_note = " (CLIPPED)" if clipped else ""
            reason.loc[t] = (
                f"VOL_TARGET: vol_est={vol_est.loc[t]:.2%}, target={cfg.target_vol_ann:.2%} → "
                f"raw_scale={rs:.2f}, scale={s2:.2f}{clip_note}"
            )

    # Scaled weights and costs
    w_scaled = base_weights.mul(scale2, axis=0)
    turnover = w_scaled.diff().abs().sum(axis=1).fillna(0.0)
    cost = turnover * (transaction_cost_bps / 1e4)

    port_ret = (w_scaled.shift(1).fillna(0.0) * asset_returns).sum(axis=1) - cost

    audit = pd.DataFrame(
        {
            "scale": scale2,
            "vol_est_ann": vol_est,
            "drawdown": dd,
            "killed": killed,
            "clipped": clipped_flag,
            "reason": reason,
            "turnover": turnover,
            "cost": cost,
        },
        index=scale.index,
    )

    return {
        "weights": w_scaled,
        "portfolio_returns": port_ret,
        "audit": audit,
    }
