import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import ConFechas, ConId


class Publicacion(ConId, ConFechas, Base):
    """Cómo aparece un producto en una tienda. Un registro por (tienda, código de la tienda)."""

    __tablename__ = "publicaciones"
    __table_args__ = (UniqueConstraint("tienda_id", "codigo_externo"),)

    tienda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tiendas.id", ondelete="RESTRICT"), index=True
    )
    codigo_externo: Mapped[str] = mapped_column(String(120))
    nombre: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(500))
    categoria_origen: Mapped[str | None] = mapped_column(String(160))
    # Sin FK todavía: productos_canonicos es de la épica 09.
    producto_canonico_id: Mapped[uuid.UUID | None] = mapped_column()
