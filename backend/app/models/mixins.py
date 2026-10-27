import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column


class ConId:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class ConFechas:
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def columna_enum(tipo: type[enum.Enum], nombre: str) -> Enum:
    """VARCHAR + CHECK con los valores del enum (no un ENUM nativo de PostgreSQL)."""
    return Enum(
        tipo,
        name=nombre,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda miembros: [m.value for m in miembros],
    )
