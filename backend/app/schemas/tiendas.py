import uuid

from pydantic import BaseModel, ConfigDict

from app.models import Rubro


class TiendaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    slug: str
    url_base: str
    rubro: Rubro
    activa: bool


class AsignarTiendaEntrada(BaseModel):
    tienda_id: uuid.UUID
