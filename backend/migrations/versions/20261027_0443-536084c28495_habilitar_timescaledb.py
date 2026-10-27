"""habilitar timescaledb

Revision ID: 536084c28495
Revises: 
Create Date: 2026-10-27 04:43:14.673562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '536084c28495'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")


def downgrade() -> None:
    # No se elimina la extensión: borraría todas las hypertables.
    pass
