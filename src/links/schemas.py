from datetime import datetime

from pydantic import BaseModel, HttpUrl, Field


class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: str | None = Field(default=None, min_length=3, max_length=32)
    expires_at: datetime | None = None


class LinkUpdate(BaseModel):
    original_url: HttpUrl


class LinkResponse(BaseModel):
    id: int
    original_url: HttpUrl
    short_code: str
    created_at: datetime
    expires_at: datetime | None = None
    owner_id: int | None = None

    class Config:
        from_attributes = True


class LinkStatsResponse(BaseModel):
    original_url: HttpUrl
    created_at: datetime
    click_count: int
    last_used_at: datetime | None = None

    class Config:
        from_attributes = True


class AliasCheckResponse(BaseModel):
    alias: str
    available: bool
