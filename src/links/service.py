import secrets
import string
from datetime import datetime, timezone

from .repository import LinkRepository
from .schemas import LinkCreate, LinkUpdate
from .exception import (
    LinkNotFoundError, 
    ShortCodeAlreadyExistsError, 
    ShortCodeGenerationError, 
    InvalidExpiresAtError, 
    LinkExpiredError, 
    AccessDeniedError
)


class LinkService:
    def __init__(self, repository: LinkRepository):
        self.repository = repository

    def _generate_short_code(self, length: int = 6) -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    async def _generate_unique_short_code(self) -> str:
        for _ in range(10):
            short_code = self._generate_short_code()
            existing = await self.repository.get_by_short_code(short_code)
            if not existing:
                return short_code

        raise ShortCodeGenerationError('Failed to generate unique short code')

    async def create_link(self, data: LinkCreate, owner_id: int | None = None) -> dict:
        short_code = data.custom_alias or await self._generate_unique_short_code()

        existing = await self.repository.get_by_short_code(short_code)
        if existing:
            raise ShortCodeAlreadyExistsError('Short code already exists')

        if data.expires_at is not None and data.expires_at <= datetime.now(timezone.utc):
            raise InvalidExpiresAtError('expires_at must be in the future')

        return await self.repository.create(
            original_url=str(data.original_url),
            short_code=short_code,
            created_at=datetime.now(timezone.utc),
            expires_at=data.expires_at,
            owner_id=owner_id,
        )

    async def search_by_original_url(self, original_url: str) -> dict:
        link = await self.repository.get_by_original_url(original_url)
        if not link:
            raise LinkNotFoundError('Link not found')

        return link

    async def get_stats(self, short_code: str) -> dict:
        link = await self.repository.get_by_short_code(short_code)
        if not link:
            raise LinkNotFoundError('Link not found')

        return link

    async def get_original_url_for_redirect(self, short_code: str) -> str:
        link = await self.repository.get_by_short_code(short_code)
        if not link:
            raise LinkNotFoundError('Link not found')

        if link['expires_at'] is not None and link['expires_at'] <= datetime.now(timezone.utc):
            await self.repository.delete_by_short_code(short_code)
            raise LinkExpiredError('Link has expired')

        await self.repository.increment_click_stats(
            short_code=short_code,
            last_used_at=datetime.now(timezone.utc),
        )
        return link['original_url']

    async def update_link(self, short_code: str, data: LinkUpdate, user_id: int) -> dict:
        link = await self.repository.get_by_short_code(short_code)
        if not link:
            raise LinkNotFoundError('Link not found')

        if link['owner_id'] != user_id:
            raise AccessDeniedError('You cannot update this link')

        updated = await self.repository.update_original_url(
            short_code=short_code,
            new_original_url=str(data.original_url),
        )
        if not updated:
            raise LinkNotFoundError('Link not found')

        return updated

    async def delete_link(self, short_code: str, user_id: int) -> None:
        link = await self.repository.get_by_short_code(short_code)
        if not link:
            raise LinkNotFoundError('Link not found')

        if link["owner_id"] != user_id:
            raise AccessDeniedError('You cannot delete this link')

        deleted = await self.repository.delete_by_short_code(short_code)
        if not deleted:
            raise LinkNotFoundError('Link not found')