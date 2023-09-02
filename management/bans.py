from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import ForeignKey, insert, select
from sqlalchemy.orm import Mapped, mapped_column

from helper.db_config import Base, db


class Bans(Base):
    __tablename__ = 'bans'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    start: Mapped[datetime]
    end: Mapped[datetime]
    reason: Mapped[str]

    @staticmethod
    async def last_ban(owner_id: str) -> Optional['Bans']:
        return await db.fetch_one(select(Bans).where(Bans.owner_id == owner_id).order_by(Bans.end.desc()).limit(1))  # type: ignore[return-value]

    @staticmethod
    async def active_bans() -> list['Bans']:
        now = datetime.now()  # noqa: DTZ005
        return await db.fetch_all(select(Bans).where(Bans.end >= now))  # type: ignore[return-value]

    @staticmethod
    async def ban(owner_id: int, reason: str, duration: timedelta, *, start: datetime | None = None) -> None:
        start = start or datetime.now()  # noqa: DTZ005
        await db.execute(insert(Bans).values({'owner_id': owner_id, 'start': start, 'end': start + duration, 'reason': reason}))
