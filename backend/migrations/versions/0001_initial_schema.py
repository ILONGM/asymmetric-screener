"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-01

"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("google_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_id"),
    )

    op.create_table(
        "sectors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("previous_blockers", sa.Text(), nullable=True),
        sa.Column("unlock_factor", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Versioned prompt + rules per sub-agent. New row = new version, history preserved.
    op.create_table(
        "agent_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("scoring_criteria", JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("agent_name", "version", name="uq_agent_configs_name_version"),
    )

    op.create_table(
        "weekly_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("workflow_version", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_date"),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("weekly_runs.id"), nullable=False),
        sa.Column("sector_id", UUID(as_uuid=True), sa.ForeignKey("sectors.id"), nullable=False),
        sa.Column("workflow_version", sa.String(), nullable=True),

        # stock identity
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("exchange", sa.String(), nullable=True),
        sa.Column("price_at_analysis", sa.Numeric(10, 2), nullable=True),
        sa.Column("time_horizon_years", sa.Integer(), nullable=True),

        # verdict
        sa.Column("verdict", sa.String(), nullable=True),         # GO / WATCHLIST / NO-GO
        sa.Column("score_total", sa.Integer(), nullable=True),    # /20
        sa.Column("score_breakdown", JSONB(), nullable=True),

        # analysis output — one field per agent
        sa.Column("one_liner", sa.Text(), nullable=True),
        sa.Column("why_now", sa.Text(), nullable=True),
        sa.Column("market_belief", sa.Text(), nullable=True),
        sa.Column("variant_perception_candidates", JSONB(), nullable=True),
        sa.Column("variant_perception_best", sa.Text(), nullable=True),
        sa.Column("scenarios", JSONB(), nullable=True),
        sa.Column("target_multiplier", sa.Numeric(4, 1), nullable=True),
        sa.Column("red_flags_fatal", sa.Text(), nullable=True),
        sa.Column("red_flags_non_fatal", sa.Text(), nullable=True),
        sa.Column("information_missing", sa.Text(), nullable=True),
        sa.Column("next_analyses", JSONB(), nullable=True),

        # full decision memo
        sa.Column("thesis", sa.Text(), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Raw + parsed output of each sub-agent per recommendation. Full audit trail.
    op.create_table(
        "agent_step_outputs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("recommendation_id", UUID(as_uuid=True), sa.ForeignKey("recommendations.id"), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("agent_config_id", UUID(as_uuid=True), sa.ForeignKey("agent_configs.id"), nullable=False),
        sa.Column("raw_output", sa.Text(), nullable=False),
        sa.Column("parsed_output", JSONB(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "market_data_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("recommendation_id", UUID(as_uuid=True), sa.ForeignKey("recommendations.id"), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("market_cap", sa.Numeric(20, 2), nullable=True),
        sa.Column("pe_ratio", sa.Numeric(8, 2), nullable=True),
        sa.Column("revenue_growth_yoy", sa.Numeric(6, 4), nullable=True),
        sa.Column("extra_data", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("market_data_snapshots")
    op.drop_table("agent_step_outputs")
    op.drop_table("recommendations")
    op.drop_table("weekly_runs")
    op.drop_table("agent_configs")
    op.drop_table("sectors")
    op.drop_table("users")
