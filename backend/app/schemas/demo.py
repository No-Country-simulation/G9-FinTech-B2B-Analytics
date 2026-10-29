import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import OrganizationType

BA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


class DemoRequestInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company: str = Field(min_length=2, max_length=160)
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    organization_type: OrganizationType
    comment: str | None = Field(default=None, max_length=1000)
    preferred_date: AwareDatetime

    @field_validator("preferred_date")
    @classmethod
    def business_hours(cls, value: datetime) -> datetime:
        if value <= datetime.now(UTC):
            raise ValueError("La fecha tiene que ser futura")
        local = value.astimezone(BA_TZ)
        if local.weekday() >= 5 or not 9 <= local.hour < 18:
            raise ValueError(
                "Elegí un horario de lunes a viernes, entre las 9 y las 18 (hora de Argentina)"
            )
        return value


class DemoRequestOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company: str
    name: str
    email: str
    organization_type: OrganizationType
    comment: str | None
    preferred_date: datetime
    created_at: datetime
