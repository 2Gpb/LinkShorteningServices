from fastapi import APIRouter, HTTPException, Depends, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth import current_user, optional_current_user
from auth.models import User
from .dependencies import get_link_service
from .service import LinkService
from .schemas import LinkCreate, LinkResponse, LinkStatsResponse, LinkUpdate
from .exception import (
    LinkNotFoundError, 
    ShortCodeAlreadyExistsError, 
    ShortCodeGenerationError, 
    InvalidExpiresAtError, 
    AccessDeniedError
)


router = APIRouter(
    prefix='/links',
    tags=['links']
)


@router.post('/shorten', response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_short_link(
    data: LinkCreate,
    service: LinkService = Depends(get_link_service),
    user: User | None = Depends(optional_current_user),
):
    try:
        owner_id = user.id if user else None
        return await service.create_link(data, owner_id=owner_id)
    except ShortCodeAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidExpiresAtError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ShortCodeGenerationError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/search', response_model=LinkResponse)
async def search_link_by_original_url(
    original_url: str = Query(...),
    service: LinkService = Depends(get_link_service),
):
    try:
        return await service.search_by_original_url(original_url)
    except LinkNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get('/{short_code}/stats', response_model=LinkStatsResponse)
async def get_link_stats(
    short_code: str,
    service: LinkService = Depends(get_link_service),
):
    try:
        return await service.get_stats(short_code)
    except LinkNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete('/{short_code}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    short_code: str,
    service: LinkService = Depends(get_link_service),
    user: User = Depends(current_user),
):
    try:
        await service.delete_link(short_code, user.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except LinkNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put('/{short_code}', response_model=LinkResponse)
async def update_link(
    short_code: str,
    data: LinkUpdate,
    service: LinkService = Depends(get_link_service),
    user: User = Depends(current_user),
):
    try:
        return await service.update_link(short_code, data, user.id)
    except LinkNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))