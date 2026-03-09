from fastapi import APIRouter

router = APIRouter(
    prefix='/links',
    tags=['links']
)

@router.post('/shorten')
async def create_short_link():
    pass

@router.get('/search')
async def search_link_by_original_url(original_url: str):
    pass

@router.get('/{short_code}/stats')
async def get_link_stats(short_code: str):
    pass

@router.put('/{short_code}')
async def update_link(short_code: str):
    pass

@router.delete('/{short_code}')
async def delete_link(short_code: str):
    pass