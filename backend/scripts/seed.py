"""Crea el primer administrador y el catálogo de tiendas. Se puede correr varias veces."""

import asyncio
import getpass
import os

from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.core.seguridad import hashear_password
from app.models import EstadoUsuario, Rol, Rubro, Tienda, Usuario
from app.schemas.comunes import validar_password

# Reemplazar por las tiendas reales cuando se definan los scrapers.
TIENDAS = [
    {
        "nombre": "Tienda A",
        "slug": "tienda-a",
        "url_base": "https://tienda-a.example.com",
        "rubro": Rubro.SUPERMERCADO,
        "scraper_clave": "tienda_a",
    },
    {
        "nombre": "Tienda B",
        "slug": "tienda-b",
        "url_base": "https://tienda-b.example.com",
        "rubro": Rubro.ELECTRO,
        "scraper_clave": "tienda_b",
    },
    {
        "nombre": "Tienda C",
        "slug": "tienda-c",
        "url_base": "https://tienda-c.example.com",
        "rubro": Rubro.MODA,
        "scraper_clave": "tienda_c",
    },
]


async def main() -> None:
    async with SessionLocal() as db:
        for datos in TIENDAS:
            existe = await db.scalar(select(Tienda.id).where(Tienda.slug == datos["slug"]))
            if not existe:
                db.add(Tienda(**datos))
                print(f"Tienda creada: {datos['nombre']}")

        # Variables SEED_ADMIN_* permiten correrlo sin preguntas (CI, scripts).
        correo = (
            (os.environ.get("SEED_ADMIN_CORREO") or input("Correo del administrador: "))
            .strip()
            .lower()
        )
        if await db.scalar(select(Usuario.id).where(Usuario.correo == correo)):
            print("Ese correo ya existe; no se crea el administrador.")
        else:
            nombre = (os.environ.get("SEED_ADMIN_NOMBRE") or input("Nombre y apellido: ")).strip()
            password = os.environ.get("SEED_ADMIN_PASSWORD") or getpass.getpass(
                "Contraseña (8+ caracteres, una mayúscula y un número): "
            )
            validar_password(password)
            db.add(
                Usuario(
                    nombre=nombre,
                    empresa="PriceScope",
                    correo=correo,
                    password_hash=hashear_password(password),
                    rol=Rol.ADMIN,
                    estado=EstadoUsuario.ACTIVO,
                )
            )
            print(f"Administrador creado: {correo}")

        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
