"""Phase 1 monitoring schema.

Revision ID: 0001_phase1
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_phase1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "monitored_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.Text()), sa.Column("target_url", sa.String(2048)),
        sa.Column("expected_status_code", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "service_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monitored_services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False), sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False), sa.Column("status_code", sa.Integer()), sa.Column("latency_ms", sa.Integer()),
        sa.Column("error_type", sa.String(100)), sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("service_id", "external_id", name="uq_service_checks_service_external"),
    )
    op.create_index("ix_service_checks_service_checked", "service_checks", ["service_id", "checked_at"])
    op.create_table(
        "service_health_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monitored_services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", sa.String(20), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)), sa.Column("trigger_reason", sa.String(255)),
        sa.Column("triggering_check_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("service_checks.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("state IN ('UNKNOWN','HEALTHY','DEGRADED','DOWN','RECOVERING')", name="ck_health_state_value"),
    )
    op.execute("CREATE UNIQUE INDEX uq_service_health_states_active ON service_health_states (service_id) WHERE ended_at IS NULL")


def downgrade() -> None:
    op.drop_table("service_health_states")
    op.drop_index("ix_service_checks_service_checked", table_name="service_checks")
    op.drop_table("service_checks")
    op.drop_table("monitored_services")

