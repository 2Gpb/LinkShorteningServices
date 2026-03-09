from typing import Optional
from datetime import datetime

from pydantic import BaseModel, HttpUrl, Field


class LinkCreate(BaseModel):
    url: HttpUrl
    custom_alias: Optional[str] = Field(default=None, min_length=3, max_length=32)
    expires_at: Optional[datetime] = None


class LinkUpdate(BaseModel):
    original_url: HttpUrl


class LinkResponse(BaseModel):
    id: int
    original_url: HttpUrl
    short_code: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True


class LinkStatsResponse(BaseModel):
    original_url: HttpUrl
    created_at: datetime
    click_count: int
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True