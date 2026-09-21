from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Category = Literal["top", "bottom", "dress", "shoes", "jacket", "accessory"]


class CreateItemRequest(BaseModel):
    category: Category
    content_type: str
    label: str | None = None


class CreateItemResponse(BaseModel):
    item_id: str
    upload_url: str


class UpdateItemRequest(BaseModel):
    label: str | None = None
    category: Category | None = None


class WardrobeItemResponse(BaseModel):
    id: str
    category: str
    clothing_type: str | None
    cutout_status: str
    cutout_error: str | None
    dominant_colors: list[str]
    label: str | None
    style_tags: list[str]
    original_image_url: str
    cutout_image_url: str | None
    created_at: datetime
    updated_at: datetime
