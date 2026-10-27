import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import ConId


class Sesion(ConId, Base):
    __tablename__ = "sesiones"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    refresh_hash: Mapped[str] = mapped_column(String(64), unique=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ultimo_uso_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revocada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user_agent: Mapped[str | None] = mapped_column(String(255))
