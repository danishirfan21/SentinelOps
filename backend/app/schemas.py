import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.models import AlertConditionType, AlertSeverity, AlertState, HealthState, IncidentEventType, IncidentStatus


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=120)
    description: str | None = None
    target_url: HttpUrl | None = None
    expected_status_code: int = 200
    is_enabled: bool = True


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    target_url: str | None
    expected_status_code: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class CheckCreate(BaseModel):
    external_id: str = Field(min_length=1, max_length=255)
    checked_at: datetime
    success: bool
    status_code: int | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    error_type: str | None = Field(default=None, max_length=100)
    error_message: str | None = None

    @field_validator("checked_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("checked_at must include a timezone")
        return value


class CheckOut(CheckCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    service_id: uuid.UUID
    created_at: datetime


class CheckIngestResponse(BaseModel):
    check: CheckOut
    state: HealthState
    duplicate: bool


class HealthOut(BaseModel):
    state: HealthState
    started_at: datetime
    trigger_reason: str | None


class HealthHistoryOut(HealthOut):
    id: uuid.UUID
    ended_at: datetime | None
    triggering_check_id: uuid.UUID | None


class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=120)
    condition_type: AlertConditionType
    severity: AlertSeverity
    is_enabled: bool = True


class AlertRulePatch(BaseModel):
    severity: AlertSeverity | None = None
    is_enabled: bool | None = None


class AlertRuleOut(AlertRuleCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    service_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    rule_id: uuid.UUID
    service_id: uuid.UUID
    state: AlertState
    severity: AlertSeverity
    opened_at: datetime
    resolved_at: datetime | None
    triggering_health_state_id: uuid.UUID
    resolution_health_state_id: uuid.UUID | None
    created_at: datetime


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    service_id: uuid.UUID
    title: str
    severity: AlertSeverity
    status: IncidentStatus
    opened_at: datetime
    resolved_at: datetime | None
    opened_by_alert_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class IncidentEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    incident_id: uuid.UUID
    event_type: IncidentEventType
    occurred_at: datetime
    health_state_id: uuid.UUID | None
    alert_id: uuid.UUID | None
    message: str
    created_at: datetime

