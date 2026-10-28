from fastapi import APIRouter

from app.api.v1 import admin_solicitudes, admin_tiendas, admin_usuarios, auth, cuenta, demo

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(demo.router)
api_router.include_router(cuenta.router)
api_router.include_router(admin_solicitudes.router)
api_router.include_router(admin_usuarios.router)
api_router.include_router(admin_tiendas.router)
