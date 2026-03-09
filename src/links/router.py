from fastapi import APIRouter, HTTPException, Depends, status, Query, Response
from fastapi_cache.decorator import cache

from auth.auth import current_user, optional_current_user
from auth.models import User
from .dependencies import get_link_service
from .service import LinkService
from .schemas import (
    LinkCreate, 
    LinkResponse, 
    LinkStatsResponse, 
    LinkUpdate, 
    AliasCheckResponse, 
    ExpiredLinkResponse,
)
from .exception import (
    LinkNotFoundError, 
    ShortCodeAlreadyExistsError, 
    ShortCodeGenerationError, 
    InvalidExpiresAtError, 
    AccessDeniedError,
    InvalidLimitError,
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidExpiresAtError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ShortCodeGenerationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get('/search', response_model=LinkResponse)
async def search_link_by_original_url(
    original_url: str = Query(...),
    service: LinkService = Depends(get_link_service),
):
    try:
        return await service.search_by_original_url(original_url)
    except LinkNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    

@router.get('/{short_code}/stats', response_model=LinkStatsResponse)
async def get_link_stats(
    short_code: str,
    service: LinkService = Depends(get_link_service),
):
    try:
        return await service.get_stats(short_code)
    except LinkNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get('/my', response_model=list[LinkResponse])
async def get_my_links(
    service: LinkService = Depends(get_link_service),
    user: User = Depends(current_user),
):
    return await service.get_user_links(user.id)


@router.get('/top', response_model=list[LinkStatsResponse])
@cache(expire=60)
async def get_top_links_by_clicks(
    service: LinkService = Depends(get_link_service),
    num: int = 10,
):
    try:
        return await service.get_top_links(num)
    except InvalidLimitError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/check-alias/{alias}", response_model=AliasCheckResponse)
async def check_alias(
    alias: str,
    service: LinkService = Depends(get_link_service),
):
    available = await service.check_alias(alias)
    return AliasCheckResponse(alias=alias, available=available)


@router.get('/expired', response_model=list[ExpiredLinkResponse])
async def get_expired_links(
    service: LinkService = Depends(get_link_service),
    user: User = Depends(current_user),
):
    return await service.get_expired_links(user.id)


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
