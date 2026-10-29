from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models import RateType


class RateOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source: str
    type: RateType
    buy: Decimal | None
    sell: Decimal
    quoted_at: datetime
    source_date: datetime | None
