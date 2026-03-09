import secrets
import string
from datetime import datetime, timezone, timedelta

from config import INACTIVE_LINK_DAYS
from .cache_service import LinkCacheService
from .repository import LinkRepository
from .schemas import LinkCreate, LinkUpdate
from .exception import (
    LinkNotFoundError, 
    ShortCodeAlreadyExistsError, 
    ShortCodeGenerationError, 
    InvalidExpiresAtError, 
    LinkExpiredError, 
    AccessDeniedError,
    InvalidLimitError
)


class LinkService:
    def __init__(self, repository: LinkRepository, link_cache_service: LinkCacheService):
        self.repository = repository
        self.cache_service = link_cache_service

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

    async def get_user_links(self, user_id: int) -> list[dict]:
        return await self.repository.get_by_user_id(user_id)
        
    async def get_top_links(self, num: int) -> list[dict]:
        if num <= 0 or num > 100:
            raise InvalidLimitError('Limit must be between 1 and 100')

        return await self.repository.get_top_links(num)

    async def check_alias(self, short_code: str) -> bool:
        link = await self.repository.get_by_short_code(short_code)
        return link is None

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

        await self.cache_service.delete_redirect_url(short_code)

        return updated

    async def get_expired_links(self, user_id: int) -> list[dict]:
        return await self.repository.get_expired_links(user_id)

    async def delete_link(self, short_code: str, user_id: int) -> None:
        link = await self.repository.get_by_short_code(short_code)
        if not link:
            raise LinkNotFoundError('Link not found')

        if link["owner_id"] != user_id:
            raise AccessDeniedError('You cannot delete this link')

        deleted = await self.repository.delete_by_short_code(short_code)

        if not deleted:
            raise LinkNotFoundError('Link not found')

        await self.cache_service.delete_redirect_url(short_code)
 
    async def delete_inactive_links(self, user_id: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=INACTIVE_LINK_DAYS)

        inactive_links = await self.repository.get_inactive_links(cutoff, user_id)
        if not inactive_links:
            return 0

        deleted_count = await self.repository.delete_inactive_links(cutoff, user_id)

        for link in inactive_links:
            await self.cache_service.delete_redirect_url(link["short_code"])

        return deleted_count

    async def get_original_url_for_redirect(self, short_code: str) -> str:
        time_now = datetime.now(timezone.utc)
        cached_data = await self.cache_service.get_redirect_data(short_code)
        if cached_data is not None:
            expires_at_raw = cached_data["expires_at"]
            expires_at = (
                datetime.fromisoformat(expires_at_raw)
                if expires_at_raw is not None
                else None
            )

            if expires_at is not None and expires_at <= time_now:
                link = await self.repository.get_by_short_code(short_code)
                if link:
                    await self.repository.save_expired_link(link, time_now)
                    await self.repository.delete_by_short_code(short_code)

                await self.cache_service.delete_redirect_url(short_code)
                raise LinkExpiredError("Link has expired")

            await self.repository.increment_click_stats(
                short_code=short_code,
                last_used_at=time_now,
            )
            return cached_data["original_url"]

        link = await self.repository.get_by_short_code(short_code)
        if not link:
            raise LinkNotFoundError('Link not found')

        if link['expires_at'] is not None and link['expires_at'] <= time_now:
            await self.repository.save_expired_link(link, time_now)
            await self.repository.delete_by_short_code(short_code)
            await self.cache_service.delete_redirect_url(short_code)
            raise LinkExpiredError('Link has expired')

        await self.repository.increment_click_stats(
            short_code=short_code,
            last_used_at=time_now,
        )

        await self.cache_service.set_redirect_data(
            short_code=short_code,
            original_url=link["original_url"],
            expires_at=link["expires_at"],
        )

        return link['original_url']
