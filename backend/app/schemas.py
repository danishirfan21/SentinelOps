import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.models import HealthState


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

