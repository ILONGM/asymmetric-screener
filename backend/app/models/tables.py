from __future__ import annotations

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Boolean, Date, DateTime, Numeric, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String)
    google_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Sector(Base):
    __tablename__ = "sectors"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    previous_blockers: Mapped[Optional[str]] = mapped_column(Text)
    unlock_factor: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    recommendations: Mapped[list[Recommendation]] = relationship(back_populates="sector")


class AgentConfig(Base):
    """Versioned prompt + rules for each sub-agent. Changing a prompt = new row, history preserved."""
    __tablename__ = "agent_configs"
    __table_args__ = (UniqueConstraint("agent_name", "version"),)

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # scoring weights, thresholds, checklist items — anything that drives the agent's rules
    scoring_criteria: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    step_outputs: Mapped[list[AgentStepOutput]] = relationship(back_populates="agent_config")


class WeeklyRun(Base):
    __tablename__ = "weekly_runs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending/running/completed/failed
    workflow_version: Mapped[Optional[str]] = mapped_column(String)  # e.g. "v1.0"
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    recommendations: Mapped[list[Recommendation]] = relationship(back_populates="run")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("weekly_runs.id"), nullable=False)
    sector_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sectors.id"), nullable=False)
    workflow_version: Mapped[Optional[str]] = mapped_column(String)

    # --- stock identity ---
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    exchange: Mapped[Optional[str]] = mapped_column(String)
    price_at_analysis: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    time_horizon_years: Mapped[Optional[int]] = mapped_column(Integer)

    # --- verdict ---
    verdict: Mapped[Optional[str]] = mapped_column(String)  # GO / WATCHLIST / NO-GO
    score_total: Mapped[Optional[int]] = mapped_column(Integer)
    score_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB)
    # e.g. {"variant_perception": 3, "asymmetry": 4, "downside_protection": 3, ...}

    # --- analysis output (one field per agent) ---
    one_liner: Mapped[Optional[str]] = mapped_column(Text)
    why_now: Mapped[Optional[str]] = mapped_column(Text)
    market_belief: Mapped[Optional[str]] = mapped_column(Text)
    variant_perception_candidates: Mapped[Optional[list]] = mapped_column(JSONB)
    # e.g. [{"number": 1, "title": "...", "description": "..."}, ...]
    variant_perception_best: Mapped[Optional[str]] = mapped_column(Text)
    scenarios: Mapped[Optional[list]] = mapped_column(JSONB)
    # e.g. [{"label": "Bear", "hypothesis": "...", "implied_price": 36.0, "upside_pct": -32.0}, ...]
    target_multiplier: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))  # bull case target x
    red_flags_fatal: Mapped[Optional[str]] = mapped_column(Text)
    red_flags_non_fatal: Mapped[Optional[str]] = mapped_column(Text)
    information_missing: Mapped[Optional[str]] = mapped_column(Text)
    next_analyses: Mapped[Optional[list]] = mapped_column(JSONB)
    # e.g. ["TAM bottom-up par application...", "Bridge CA..."]

    # --- full decision memo (consolidated text output) ---
    thesis: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    run: Mapped[WeeklyRun] = relationship(back_populates="recommendations")
    sector: Mapped[Sector] = relationship(back_populates="recommendations")
    market_data_snapshots: Mapped[list[MarketDataSnapshot]] = relationship(back_populates="recommendation")
    agent_step_outputs: Mapped[list[AgentStepOutput]] = relationship(back_populates="recommendation")


class AgentStepOutput(Base):
    """Raw + parsed output of each sub-agent for each recommendation. Full audit trail."""
    __tablename__ = "agent_step_outputs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    agent_config_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("agent_configs.id"), nullable=False)
    raw_output: Mapped[str] = mapped_column(Text, nullable=False)  # full text from Claude
    parsed_output: Mapped[Optional[dict]] = mapped_column(JSONB)   # structured version
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    recommendation: Mapped[Recommendation] = relationship(back_populates="agent_step_outputs")
    agent_config: Mapped[AgentConfig] = relationship(back_populates="step_outputs")


class MarketDataSnapshot(Base):
    __tablename__ = "market_data_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    market_cap: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    pe_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    revenue_growth_yoy: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4))
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    recommendation: Mapped[Recommendation] = relationship(back_populates="market_data_snapshots")
