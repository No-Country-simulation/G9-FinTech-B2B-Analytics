from enum import StrEnum


class Rol(StrEnum):
    CLIENTE = "cliente"
    ADMIN = "admin"


class EstadoUsuario(StrEnum):
    PENDIENTE = "pendiente"
    ACTIVO = "activo"
    BLOQUEADO = "bloqueado"
    BAJA = "baja"


class TipoToken(StrEnum):
    DEFINIR = "definir"
    RESTABLECER = "restablecer"


class TipoOrganizacion(StrEnum):
    RETAIL = "retail"
    FONDO = "fondo"
    MEDIO = "medio"
    OTRO = "otro"


class Rubro(StrEnum):
    SUPERMERCADO = "supermercado"
    ELECTRO = "electro"
    MODA = "moda"
