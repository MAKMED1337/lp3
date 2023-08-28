from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import insert, select
from sqlalchemy.orm import Mapped, mapped_column

from helper.db_config import Base, db


class Bans(Base):
    __tablename__ = 'bans'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str]
    start: Mapped[datetime]
    end: Mapped[datetime]
    reason: Mapped[str]

    @staticmethod
    async def last_ban(user_id: str) -> Optional['Bans']:
        return await db.fetch_one(select(Bans).where(Bans.user_id == user_id).order_by(Bans.end.desc()).limit(1))

    @staticmethod
    async def ban(user_id: str, reason: str, duration: timedelta, *, start: datetime | None = None) -> None:
        start = start or datetime.now()  # noqa: DTZ005
        await db.execute(insert(Bans).values({'user_id': user_id, 'start': start, 'end': start + duration, 'reason': reason}))
