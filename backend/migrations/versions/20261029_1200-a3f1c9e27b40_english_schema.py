"""english schema: rename tables, columns, indexes, constraints and enum values

Revision ID: a3f1c9e27b40
Revises: 5727aa9c4ab1
Create Date: 2026-10-29 12:00:00

"""

from typing import NamedTuple, Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a3f1c9e27b40"
down_revision: Union[str, Sequence[str], None] = (
    "5727aa9c4ab1",
    "7102ccc2b1eb",
)  # merges both heads
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class EnumColumn(NamedTuple):
    table: str  # name before this migration
    column: str
    table_new: str
    column_new: str
    old_enum: str  # name of the CHECK in the old schema, used on downgrade
    enum_name: str  # name of the Enum in the models, used for the new CHECK
    values: dict[str, str]  # old value -> new value


ENUM_COLUMNS = [
    EnumColumn(
        "usuarios",
        "rol",
        "users",
        "role",
        "rol_usuario",
        "user_role",
        {"cliente": "client", "admin": "admin"},
    ),
    EnumColumn(
        "usuarios",
        "estado",
        "users",
        "status",
        "estado_usuario",
        "user_status",
        {"pendiente": "pending", "activo": "active", "bloqueado": "blocked", "baja": "deactivated"},
    ),
    EnumColumn(
        "tokens_acceso",
        "tipo",
        "access_tokens",
        "type",
        "tipo_token",
        "token_type",
        {"definir": "set_password", "restablecer": "reset_password"},
    ),
    EnumColumn(
        "solicitudes_demo",
        "tipo_organizacion",
        "demo_requests",
        "organization_type",
        "tipo_organizacion",
        "organization_type",
        {"retail": "retail", "fondo": "fund", "medio": "media", "otro": "other"},
    ),
    EnumColumn(
        "tiendas",
        "rubro",
        "stores",
        "category",
        "rubro_tienda",
        "store_category",
        {"supermercado": "supermarket", "electro": "electronics", "moda": "fashion"},
    ),
    EnumColumn(
        "cotizaciones",
        "tipo",
        "exchange_rates",
        "type",
        "tipo_cotizacion",
        "rate_type",
        {"oficial": "official", "blue": "blue"},
    ),
]

RENAMED_TABLES = [
    ("usuarios", "users"),
    ("sesiones", "sessions"),
    ("tokens_acceso", "access_tokens"),
    ("solicitudes_demo", "demo_requests"),
    ("tiendas", "stores"),
    ("usuario_tienda", "user_store"),
    ("cambios_correo", "email_changes"),
    ("cotizaciones", "exchange_rates"),
    ("publicaciones", "listings"),
    ("precios", "prices"),
]

# Keyed by the table's NEW name.
RENAMED_COLUMNS = {
    "users": [
        ("nombre", "name"),
        ("empresa", "company"),
        ("correo", "email"),
        ("rol", "role"),
        ("estado", "status"),
        ("ultimo_acceso", "last_access_at"),
        ("creado_en", "created_at"),
        ("actualizado_en", "updated_at"),
    ],
    "sessions": [
        ("usuario_id", "user_id"),
        ("creada_en", "created_at"),
        ("ultimo_uso_en", "last_used_at"),
        ("expira_en", "expires_at"),
        ("revocada_en", "revoked_at"),
    ],
    "access_tokens": [
        ("usuario_id", "user_id"),
        ("tipo", "type"),
        ("expira_en", "expires_at"),
        ("usado_en", "used_at"),
        ("creado_en", "created_at"),
    ],
    "demo_requests": [
        ("empresa", "company"),
        ("nombre", "name"),
        ("correo", "email"),
        ("tipo_organizacion", "organization_type"),
        ("comentario", "comment"),
        ("fecha_preferida", "preferred_date"),
        ("creada_en", "created_at"),
    ],
    "stores": [
        ("nombre", "name"),
        ("url_base", "base_url"),
        ("rubro", "category"),
        ("scraper_clave", "scraper_key"),
        ("activa", "active"),
        ("creado_en", "created_at"),
        ("actualizado_en", "updated_at"),
    ],
    "user_store": [
        ("usuario_id", "user_id"),
        ("tienda_id", "store_id"),
        ("asignada_en", "assigned_at"),
        ("asignada_por", "assigned_by"),
    ],
    "email_changes": [
        ("usuario_id", "user_id"),
        ("correo_nuevo", "new_email"),
        ("expira_en", "expires_at"),
        ("usado_en", "used_at"),
        ("creado_en", "created_at"),
    ],
    "exchange_rates": [
        ("fuente", "source"),
        ("tipo", "type"),
        ("cotizado_en", "quoted_at"),
        ("compra", "buy"),
        ("venta", "sell"),
        ("fecha_fuente", "source_date"),
    ],
    "listings": [
        ("tienda_id", "store_id"),
        ("codigo_externo", "external_code"),
        ("nombre", "name"),
        ("categoria_origen", "source_category"),
        ("producto_canonico_id", "canonical_product_id"),
        ("creado_en", "created_at"),
        ("actualizado_en", "updated_at"),
    ],
    "prices": [
        ("publicacion_id", "listing_id"),
        ("capturado_en", "captured_at"),
        ("precio_local", "local_price"),
        ("precio_tachado", "strikethrough_price"),
        ("precio_regular", "regular_price"),
        ("es_promo", "is_promo"),
        ("disponible", "available"),
        ("gramaje", "grammage"),
        ("unidad", "unit"),
        ("tc_oficial", "fx_official"),
        ("tc_blue", "fx_blue"),
        ("cotizado_en", "quoted_at"),
        ("precio_usd_oficial", "price_usd_official"),
        ("precio_usd_blue", "price_usd_blue"),
    ],
}

RENAMED_INDEXES = [
    ("ix_solicitudes_demo_creada_en", "ix_demo_requests_created_at"),
    ("ix_usuarios_estado", "ix_users_status"),
    ("ix_usuarios_rol", "ix_users_role"),
    ("ix_sesiones_usuario_id", "ix_sessions_user_id"),
    ("ix_tokens_acceso_usuario_tipo", "ix_access_tokens_user_type"),
    ("ix_usuario_tienda_tienda_id", "ix_user_store_store_id"),
    ("ix_publicaciones_tienda_id", "ix_listings_store_id"),
    ("ix_cambios_correo_usuario_id", "ix_email_changes_user_id"),
]

# TimescaleDB creates this index by itself, so it may not exist: IF EXISTS below.
TIMESCALE_INDEX = ("precios_capturado_en_idx", "prices_captured_at_idx")

# (table by its NEW name, old constraint name, new constraint name)
RENAMED_CONSTRAINTS = [
    ("users", "pk_usuarios", "pk_users"),
    ("users", "uq_usuarios_correo", "uq_users_email"),
    ("sessions", "pk_sesiones", "pk_sessions"),
    ("sessions", "uq_sesiones_refresh_hash", "uq_sessions_refresh_hash"),
    ("sessions", "fk_sesiones_usuario_id_usuarios", "fk_sessions_user_id_users"),
    ("access_tokens", "pk_tokens_acceso", "pk_access_tokens"),
    ("access_tokens", "uq_tokens_acceso_token_hash", "uq_access_tokens_token_hash"),
    ("access_tokens", "fk_tokens_acceso_usuario_id_usuarios", "fk_access_tokens_user_id_users"),
    ("demo_requests", "pk_solicitudes_demo", "pk_demo_requests"),
    ("stores", "pk_tiendas", "pk_stores"),
    ("stores", "uq_tiendas_scraper_clave", "uq_stores_scraper_key"),
    ("stores", "uq_tiendas_slug", "uq_stores_slug"),
    ("user_store", "pk_usuario_tienda", "pk_user_store"),
    (
        "user_store",
        "fk_usuario_tienda_asignada_por_usuarios",
        "fk_user_store_assigned_by_users",
    ),
    ("user_store", "fk_usuario_tienda_tienda_id_tiendas", "fk_user_store_store_id_stores"),
    ("user_store", "fk_usuario_tienda_usuario_id_usuarios", "fk_user_store_user_id_users"),
    ("email_changes", "pk_cambios_correo", "pk_email_changes"),
    ("email_changes", "uq_cambios_correo_token_hash", "uq_email_changes_token_hash"),
    (
        "email_changes",
        "fk_cambios_correo_usuario_id_usuarios",
        "fk_email_changes_user_id_users",
    ),
    ("exchange_rates", "pk_cotizaciones", "pk_exchange_rates"),
    ("listings", "pk_publicaciones", "pk_listings"),
    ("listings", "uq_publicaciones_tienda_id", "uq_listings_store_id"),
    ("listings", "fk_publicaciones_tienda_id_tiendas", "fk_listings_store_id_stores"),
    ("prices", "pk_precios", "pk_prices"),
    ("prices", "fk_precios_publicacion_id_publicaciones", "fk_prices_listing_id_listings"),
]


def _in_list(values: Sequence[str]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def _drop_checks(table: str, column: str) -> None:
    """Drops every CHECK on the column. The names come from the database, so they are looked up."""
    op.execute(
        f"""
        DO $$
        DECLARE r record;
        BEGIN
            FOR r IN
                SELECT c.conname
                FROM pg_constraint c
                JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
                WHERE c.conrelid = '{table}'::regclass
                  AND c.contype = 'c'
                  AND a.attname = '{column}'
            LOOP
                EXECUTE format('ALTER TABLE {table} DROP CONSTRAINT %I', r.conname);
            END LOOP;
        END $$;
        """
    )


def upgrade() -> None:
    # 1. Drop the old CHECKs first: they list the Spanish values and would reject the update.
    for item in ENUM_COLUMNS:
        _drop_checks(item.table, item.column)

    # 2. Translate the stored values (tables still have their old names).
    for item in ENUM_COLUMNS:
        for old, new in item.values.items():
            op.execute(
                f"UPDATE {item.table} SET {item.column} = '{new}' WHERE {item.column} = '{old}'"
            )

    # 3. Rename tables, columns, indexes and constraints.
    for old, new in RENAMED_TABLES:
        op.execute(f"ALTER TABLE {old} RENAME TO {new}")

    for table, columns in RENAMED_COLUMNS.items():
        for old, new in columns:
            op.execute(f"ALTER TABLE {table} RENAME COLUMN {old} TO {new}")

    for old, new in RENAMED_INDEXES:
        op.execute(f"ALTER INDEX {old} RENAME TO {new}")
    op.execute(f"ALTER INDEX IF EXISTS {TIMESCALE_INDEX[0]} RENAME TO {TIMESCALE_INDEX[1]}")

    for table, old, new in RENAMED_CONSTRAINTS:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {old} TO {new}")

    # 4. New CHECKs with the English values and the names the models generate.
    for item in ENUM_COLUMNS:
        op.create_check_constraint(
            op.f(f"ck_{item.table_new}_{item.enum_name}"),
            item.table_new,
            f"{item.column_new} IN ({_in_list(list(item.values.values()))})",
        )


def downgrade() -> None:
    # Reverse order. The new CHECKs have known names, so they can be dropped directly.
    for item in ENUM_COLUMNS:
        op.execute(
            f"ALTER TABLE {item.table_new} DROP CONSTRAINT ck_{item.table_new}_{item.enum_name}"
        )

    for table, old, new in reversed(RENAMED_CONSTRAINTS):
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {new} TO {old}")

    op.execute(f"ALTER INDEX IF EXISTS {TIMESCALE_INDEX[1]} RENAME TO {TIMESCALE_INDEX[0]}")
    for old, new in RENAMED_INDEXES:
        op.execute(f"ALTER INDEX {new} RENAME TO {old}")

    for table, columns in RENAMED_COLUMNS.items():
        for old, new in columns:
            op.execute(f"ALTER TABLE {table} RENAME COLUMN {new} TO {old}")

    for old, new in RENAMED_TABLES:
        op.execute(f"ALTER TABLE {new} RENAME TO {old}")

    for item in ENUM_COLUMNS:
        for old, new in item.values.items():
            op.execute(
                f"UPDATE {item.table} SET {item.column} = '{old}' WHERE {item.column} = '{new}'"
            )
        op.create_check_constraint(
            op.f(f"ck_{item.table}_{item.old_enum}"),
            item.table,
            f"{item.column} IN ({_in_list(list(item.values.keys()))})",
        )
