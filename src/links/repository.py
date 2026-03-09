from datetime import datetime

from sqlalchemy import delete, insert, select, update, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.tables import links
from models.tables import expired_links


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

    async def get_inactive_links(self, cutoff: datetime, user_id: int) -> list[dict]:
        inactive_condition = or_(
            links.c.last_used_at < cutoff,
            and_(
                links.c.last_used_at.is_(None),
                links.c.created_at < cutoff,
            ),
        )

        stmt = select(links).where(
            and_(
                links.c.owner_id == user_id,
                inactive_condition,
            )
        )
        result = await self.session.execute(stmt)
        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def save_expired_link(self, link: dict, expired_at: datetime) -> None:
        stmt = (
            insert(expired_links)
            .values(
                original_url=link["original_url"],
                short_code=link["short_code"],
                created_at=link["created_at"],
                expires_at=link["expires_at"],
                owner_id=link["owner_id"],
                click_count=link["click_count"],
                last_used_at=link["last_used_at"],
                expired_at=expired_at,
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
    
    async def get_expired_links(self, user_id: int) -> list[dict]:
        stmt = (
            select(expired_links)
            .where(expired_links.c.owner_id == user_id)
            .order_by(expired_links.c.expired_at.desc())
        )
        result = await self.session.execute(stmt)
        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def delete_inactive_links(self, cutoff: datetime, user_id: int) -> int:
        inactive_condition = or_(
            links.c.last_used_at < cutoff,
            and_(
                links.c.last_used_at.is_(None),
                links.c.created_at < cutoff,
            ),
        )
        stmt = delete(links).where(
            and_(
                links.c.owner_id == user_id,
                inactive_condition
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
