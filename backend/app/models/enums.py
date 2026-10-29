from enum import StrEnum


class Role(StrEnum):
    CLIENT = "client"
    ADMIN = "admin"


class UserStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"
    DEACTIVATED = "deactivated"


class TokenType(StrEnum):
    SET_PASSWORD = "set_password"
    RESET_PASSWORD = "reset_password"


class OrganizationType(StrEnum):
    RETAIL = "retail"
    FUND = "fund"
    MEDIA = "media"
    OTHER = "other"


class StoreCategory(StrEnum):
    SUPERMARKET = "supermarket"
    ELECTRONICS = "electronics"
    FASHION = "fashion"


class RateType(StrEnum):
    OFFICIAL = "official"
    BLUE = "blue"
