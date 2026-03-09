from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from .service import LinkService
from .repository import LinkRepository


def get_link_repository(
    session: AsyncSession = Depends(get_async_session),
) -> LinkRepository:
    return LinkRepository(session)

def get_link_service(repository: LinkRepository = Depends(get_link_repository)) -> LinkService:
    return LinkService(repository)
