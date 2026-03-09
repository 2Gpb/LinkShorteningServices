from datetime import datetime

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.tables import links


class LinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_short_code(self, short_code: str) -> dict | None:
        stmt = select(links).where(links.c.short_code == short_code)
        result = await self.session.execute(stmt)
        row = result.mappings().first()
        return dict(row) if row else None

    async def get_by_original_url(self, original_url: str) -> dict | None:
        stmt = select(links).where(links.c.original_url == original_url)
        result = await self.session.execute(stmt)
        row = result.mappings().first()
        return dict(row) if row else None

    async def get_by_user_id(self, user_id: int) -> list[dict]:
        stmt = select(links).where(links.c.owner_id == user_id)
        result = await self.session.execute(stmt)
        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def get_top_links(self, num: int) -> list[dict]:
        stmt = select(links).order_by(links.c.click_count.desc()).limit(num)
        result = await self.session.execute(stmt)
        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def create(
        self,
        original_url: str,
        short_code: str,
        created_at: datetime,
        expires_at: datetime | None,
        owner_id: int | None,
    ) -> dict:
        stmt = (
            insert(links)
            .values(
                original_url=original_url,
                short_code=short_code,
                created_at=created_at,
                expires_at=expires_at,
                owner_id=owner_id,
                click_count=0,
                last_used_at=None,
            )
            .returning(links)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        row = result.mappings().first()
        return dict(row)

    async def update_original_url(self, short_code: str, new_original_url: str) -> dict | None:
        stmt = (
            update(links)
            .where(links.c.short_code == short_code)
            .values(original_url=new_original_url)
            .returning(links)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        row = result.mappings().first()
        return dict(row) if row else None

    async def increment_click_stats(self, short_code: str, last_used_at: datetime) -> None:
        stmt = (
            update(links)
            .where(links.c.short_code == short_code)
            .values(
                click_count=links.c.click_count + 1,
                last_used_at=last_used_at,
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete_by_short_code(self, short_code: str) -> bool:
        stmt = delete(links).where(links.c.short_code == short_code)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
