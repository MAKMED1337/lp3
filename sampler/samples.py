from datetime import datetime
from typing import Optional

from sqlalchemy import VARCHAR, and_, insert, select, update
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from helper.db_config import Base, db
from log_scraper.logs import Logs, Type

from .config import MAX_OFFSET, MIN_OFFSET


class Samples(Base):
    __tablename__ = 'samples'

    task_id: Mapped[int] = mapped_column(primary_key=True)
    dt: Mapped[datetime]
    comment: Mapped[str | None] = mapped_column(VARCHAR(256), default=None, server_default='NULL')
    is_ok: Mapped[bool | None] = mapped_column(default=None, server_default='NULL')

    @staticmethod
    async def add(task_id: int, *, start: datetime | None = None) -> None:
        start = start or datetime.now()  # noqa: DTZ005
        await db.execute(insert(Samples).values(task_id=task_id, dt=start))

    @staticmethod
    async def set_status(task_id: int, comment: str, is_ok: bool) -> None:
        await db.execute(update(Samples).values(comment=comment, is_ok=is_ok).where(Samples.task_id == task_id))

    #selecting random task that has last review few days ago and hasn't been sampled yet
    @staticmethod
    async def select_random_sample() -> int | None:
        dt = datetime.now()  # noqa: DTZ005
        query = select(Logs.user_task_id) \
            .group_by(Logs.user_task_id) \
            .having(and_(
                func.max(Logs.dt) <= dt - MIN_OFFSET,
                func.max(Logs.dt) >= dt - MAX_OFFSET,
            )).where(
                Logs.user_task_id.notin_(
                    select(Samples.task_id),
                ),
                Logs.type == Type.task,
            )

        return await db.fetch_val(query.order_by(func.random()).limit(1))

    @staticmethod
    async def last_sample() -> Optional['Samples']:
        return await db.fetch_one(select(Samples).order_by(Samples.dt.desc()).limit(1))  # type: ignore[return-value]
