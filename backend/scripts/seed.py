"""Creates the first administrator and the store catalog. Safe to run more than once."""

import asyncio
import getpass
import os

from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models import Role, Store, StoreCategory, User, UserStatus
from app.schemas.common import validate_password

# Replace with the real stores once the scrapers are defined.
STORES = [
    {
        "name": "Carrefour Argentina",
        "slug": "carrefour",
        "base_url": "https://www.carrefour.com.ar",
        "category": StoreCategory.SUPERMARKET,
        "scraper_key": "carrefour",
    },
    {
        "name": "Jumbo Argentina",
        "slug": "jumbo",
        "base_url": "https://www.jumbo.com.ar",
        "category": StoreCategory.SUPERMARKET,
        "scraper_key": "jumbo",
    },
]


async def main() -> None:
    async with SessionLocal() as db:
        for data in STORES:
            exists = await db.scalar(select(Store.id).where(Store.slug == data["slug"]))
            if not exists:
                db.add(Store(**data))
                print(f"Store created: {data['name']}")

        # SEED_ADMIN_* variables allow running it without prompts (CI, scripts).
        email = (
            (os.environ.get("SEED_ADMIN_EMAIL") or input("Administrator email: ")).strip().lower()
        )
        if await db.scalar(select(User.id).where(User.email == email)):
            print("That email already exists; no administrator created.")
        else:
            name = (os.environ.get("SEED_ADMIN_NAME") or input("Full name: ")).strip()
            password = os.environ.get("SEED_ADMIN_PASSWORD") or getpass.getpass(
                "Password (8+ characters, one uppercase letter and one digit): "
            )
            validate_password(password)
            db.add(
                User(
                    name=name,
                    company="PriceScope",
                    email=email,
                    password_hash=hash_password(password),
                    role=Role.ADMIN,
                    status=UserStatus.ACTIVE,
                )
            )
            print(f"Administrator created: {email}")

        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
