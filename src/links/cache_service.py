from core import redis as redis_core


REDIRECT_CACHE_TTL = 3600


class LinkCacheService:
    @staticmethod
    def make_redirect_key(short_code: str) -> str:
        return f"redirect:{short_code}"

    async def get_redirect_url(self, short_code: str) -> str | None:
        if redis_core.redis_client is None:
            return None

        return await redis_core.redis_client.get(self.make_redirect_key(short_code))

    async def set_redirect_url(self, short_code: str, original_url: str) -> None:
        if redis_core.redis_client is None:
            return

        await redis_core.redis_client.set(
            self.make_redirect_key(short_code),
            original_url,
            ex=REDIRECT_CACHE_TTL,
        )

    async def delete_redirect_url(self, short_code: str) -> None:
        if redis_core.redis_client is None:
            return

        await redis_core.redis_client.delete(self.make_redirect_key(short_code))
