import uuid

from pydantic import BaseModel, ConfigDict

from app.models import StoreCategory


class StoreOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    base_url: str
    category: StoreCategory
    active: bool


class AssignStoreInput(BaseModel):
    store_id: uuid.UUID
