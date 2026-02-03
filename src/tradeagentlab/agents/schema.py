from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MarketRegime(BaseModel):
    label: Literal["risk-on", "risk-off", "mixed", "unknown"] = "unknown"
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    evidence: list[str] = Field(default_factory=list)


class TickerSnapshot(BaseModel):
    ticker: str
    ret_20d: float
    vol_20d_ann: float
    trend: Literal["up", "down", "flat"]


class ResearchNote(BaseModel):
    as_of: str
    regime: MarketRegime
    universe: list[TickerSnapshot]
    summary: str


class PositionTarget(BaseModel):
    ticker: str
    weight: float = Field(ge=0.0, le=1.0)
    reason: str


class AgentDecision(BaseModel):
    as_of: str
    objective: str = "Long-only US equities; risk constrained; research backtest/paper trading"
    proposed_positions: list[PositionTarget]
    risk_notes: list[str] = Field(default_factory=list)
    constraints: dict[str, float] = Field(default_factory=dict)
    disclaimer: str = "Not financial advice. Research project." 


class ExecutionRow(BaseModel):
    ticker: str
    proposed_weight: float
    executed_weight: float
    status: Literal["accepted", "rejected"]
    gate_reason: str


class ExecutionPlan(BaseModel):
    as_of: str
    scale: float
    gate_reason: str
    rows: list[ExecutionRow]
    cash_weight: float
    gross_exposure: float
