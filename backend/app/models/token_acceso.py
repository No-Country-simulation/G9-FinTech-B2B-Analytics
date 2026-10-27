import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TipoToken
from app.models.mixins import ConId, columna_enum


class TokenAcceso(ConId, Base):
    __tablename__ = "tokens_acceso"
    __table_args__ = (Index("ix_tokens_acceso_usuario_tipo", "usuario_id", "tipo"),)

    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    tipo: Mapped[TipoToken] = mapped_column(columna_enum(TipoToken, "tipo_token"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
