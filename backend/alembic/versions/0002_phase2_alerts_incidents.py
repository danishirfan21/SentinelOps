"""Phase 2 alert and incident lifecycle.

Revision ID: 0002_phase2
Revises: 0001_phase1
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_phase2"
down_revision = "0001_phase1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monitored_services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("condition_type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("service_id", "slug", name="uq_alert_rules_service_slug"),
        sa.CheckConstraint("condition_type IN ('STATE_DEGRADED','STATE_DOWN')", name="ck_alert_rule_condition"),
        sa.CheckConstraint("severity IN ('WARNING','CRITICAL')", name="ck_alert_rule_severity"),
    )
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monitored_services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", sa.String(20), nullable=False), sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False), sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("triggering_health_state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("service_health_states.id"), nullable=False),
        sa.Column("resolution_health_state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("service_health_states.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("state IN ('OPEN','RESOLVED')", name="ck_alert_state"),
        sa.CheckConstraint("severity IN ('WARNING','CRITICAL')", name="ck_alert_severity"),
    )
    op.execute("CREATE UNIQUE INDEX uq_alerts_open_rule_service ON alerts (rule_id, service_id) WHERE state = 'OPEN'")
    op.create_index("ix_alerts_service_state", "alerts", ["service_id", "state"])
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monitored_services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False), sa.Column("severity", sa.String(20), nullable=False), sa.Column("status", sa.String(20), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False), sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("opened_by_alert_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alerts.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("severity IN ('WARNING','CRITICAL')", name="ck_incident_severity"),
        sa.CheckConstraint("status IN ('OPEN','RESOLVED')", name="ck_incident_status"),
    )
    op.execute("CREATE UNIQUE INDEX uq_incidents_open_service ON incidents (service_id) WHERE status = 'OPEN'")
    op.create_table(
        "incident_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("health_state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("service_health_states.id")),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alerts.id")),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("event_type IN ('OPENED','STATE_CHANGED','RECOVERY_STARTED','RESOLVED')", name="ck_incident_event_type"),
    )
    op.create_index("ix_incident_events_incident_occurred", "incident_events", ["incident_id", "occurred_at", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_incident_events_incident_occurred", table_name="incident_events")
    op.drop_table("incident_events")
    op.execute("DROP INDEX uq_incidents_open_service")
    op.drop_table("incidents")
    op.drop_index("ix_alerts_service_state", table_name="alerts")
    op.execute("DROP INDEX uq_alerts_open_rule_service")
    op.drop_table("alerts")
    op.drop_table("alert_rules")
