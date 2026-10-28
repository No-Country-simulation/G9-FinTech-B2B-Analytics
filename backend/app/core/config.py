from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PriceScope API"
    environment: str = "local"  # local | test | staging | production

    # PostgreSQL / TimescaleDB
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Seguridad
    jwt_secret: str
    jwt_algoritmo: str = "HS256"
    access_token_minutos: int = 15
    sesion_inactividad_minutos: int = 30
    sesion_duracion_max_horas: int = 12
    token_definir_horas: int = 72
    token_restablecer_minutos: int = 60
    token_cambio_correo_minutos: int = 30

    # Frontend
    frontend_url: str = "http://localhost:5173"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Correo
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_usuario: str | None = None
    smtp_password: str | None = None
    smtp_tls: bool = False
    correo_remitente: str = "PriceScope <no-responder@pricescope.local>"

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def cookies_seguras(self) -> bool:
        # En local y en tests la API corre por http, sin https.
        return self.environment not in ("local", "test")


settings = Settings()
