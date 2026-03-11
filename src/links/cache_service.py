import json
from datetime import datetime

from core import redis as redis_core


REDIRECT_CACHE_TTL = 3600


class LinkCacheService:
    @staticmethod
    def make_redirect_key(short_code: str) -> str:
        return f"redirect:{short_code}"

    async def get_redirect_data(self, short_code: str) -> dict | None:
        if redis_core.redis_client is None:
            return None

        raw_data = await redis_core.redis_client.get(self.make_redirect_key(short_code))
        if raw_data is None:
            return None

        return json.loads(raw_data)

    async def set_redirect_data(
        self,
        short_code: str,
        original_url: str,
        expires_at: datetime | None,
    ) -> None:
        if redis_core.redis_client is None:
            return

        payload = {
            "original_url": original_url,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

        await redis_core.redis_client.set(
            self.make_redirect_key(short_code),
            json.dumps(payload),
            ex=REDIRECT_CACHE_TTL,
        )

    async def delete_redirect_url(self, short_code: str) -> None:
        if redis_core.redis_client is None:
            return

        await redis_core.redis_client.delete(self.make_redirect_key(short_code))
