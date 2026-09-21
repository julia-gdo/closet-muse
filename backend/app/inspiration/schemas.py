from datetime import datetime

from pydantic import BaseModel


class CreateImageRequest(BaseModel):
    content_type: str


class CreateImageResponse(BaseModel):
    image_id: str
    upload_url: str


class InspirationImageResponse(BaseModel):
    id: str
    analysis_status: str
    summary: str | None
    dominant_colors: list[str]
    style_tags: list[str]
    image_url: str
    created_at: datetime
