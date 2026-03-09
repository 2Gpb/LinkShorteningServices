from fastapi import APIRouter

router = APIRouter(
    prefix='',
    tags=['redirect']
)

@router.get('/{short_code}')
async def redirect_to_original(short_code: str):
    pass