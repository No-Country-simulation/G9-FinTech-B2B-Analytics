from arq.connections import RedisSettings
from redis.asyncio import Redis

from app.core.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

# Conexión que usan la API (para encolar) y el worker (para ejecutar)
ajustes_arq = RedisSettings(host=settings.redis_host, port=settings.redis_port)
