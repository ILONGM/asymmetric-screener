import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Boolean, Date, DateTime, Numeric, Integer, Text, ForeignKey
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

    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="sector")


class WeeklyRun(Base):
    __tablename__ = "weekly_runs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="run")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("weekly_runs.id"), nullable=False)
    sector_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sectors.id"), nullable=False)
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    exchange: Mapped[Optional[str]] = mapped_column(String)
    price_at_analysis: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    target_multiplier: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    time_horizon_years: Mapped[Optional[int]] = mapped_column(Integer)
    thesis: Mapped[str] = mapped_column(Text, nullable=False)
    upside_scenario: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    run: Mapped["WeeklyRun"] = relationship(back_populates="recommendations")
    sector: Mapped["Sector"] = relationship(back_populates="recommendations")
    market_data_snapshots: Mapped[list["MarketDataSnapshot"]] = relationship(back_populates="recommendation")


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

    recommendation: Mapped["Recommendation"] = relationship(back_populates="market_data_snapshots")
