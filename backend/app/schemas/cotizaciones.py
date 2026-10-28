from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models import TipoCotizacion


class CotizacionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fuente: str
    tipo: TipoCotizacion
    compra: Decimal | None
    venta: Decimal
    cotizado_en: datetime
    fecha_fuente: datetime | None
