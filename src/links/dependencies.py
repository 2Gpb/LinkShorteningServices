from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from .cache_service import LinkCacheService
from .service import LinkService
from .repository import LinkRepository


def get_link_repository(
    session: AsyncSession = Depends(get_async_session),
) -> LinkRepository:
    return LinkRepository(session)

def get_link_cache_service() -> LinkCacheService:
    return LinkCacheService()

def get_link_service(
    repository: LinkRepository = Depends(get_link_repository),
    cache_service: LinkCacheService = Depends(get_link_cache_service)
) -> LinkService:
    return LinkService(repository, cache_service)
