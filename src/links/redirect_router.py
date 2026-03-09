from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from .dependencies import get_link_service
from .service import LinkService
from .exception import LinkExpiredError, LinkNotFoundError

router = APIRouter(tags=['redirect'])

@router.get('/{short_code}')
async def redirect_to_original(
    short_code: str,
    service: LinkService = Depends(get_link_service),
):
    try:
        original_url = await service.get_original_url_for_redirect(short_code)
        return RedirectResponse(url=original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    except LinkNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LinkExpiredError as e:
        raise HTTPException(status_code=404, detail=str(e))
