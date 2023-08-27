from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel
from sqlalchemy import JSON, VARCHAR, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column

from helper.db_config import Base, db, to_mapping


class Type(Enum):
    got_task = 'got_task'
    got_review = 'got_review'
    task = 'task'
    review = 'review'
    user_invite = 'user_invite'
    user_remove = 'user_remove'
    user_permissions = 'user_permissions'


class LogsParams(BaseModel):
    user_id: str | None = None
    user_task_id: int | None = None
    min_dt: str | None = None
    max_dt: str | None = None
    types: list[Type] = []


class Logs(Base):
    __tablename__ = 'logs'

    entry_id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    user_id: Mapped[str] = mapped_column(VARCHAR(64))
    user_task_id: Mapped[int]
    dt: Mapped[datetime]
    short_descr: Mapped[str] = mapped_column(VARCHAR(256))
    type: Mapped[Type]

    review_balance: Mapped[int] = mapped_column(default=0, server_default='0', nullable=False)

    def calculate_balance(self) -> int:
        if self.type == Type.task:
            return +8
        if self.type == Type.review:
            return -1
        return 0

    @staticmethod
    async def bulk_upsert(values: list['Logs']) -> None:
        for value in values:
            value.review_balance = value.calculate_balance()
        await db.execute_many(
            insert(Logs).on_conflict_do_update(index_elements=['entry_id'], set_=to_mapping(Logs)),
            [to_mapping(value) for value in values],
        )

    @staticmethod
    async def get(options: LogsParams = LogsParams()) -> list['Logs']:  # noqa: B008
        query = select(Logs).where(or_(*[Logs.type == t for t in options.types]))

        if options.user_id is not None:
            query = query.where(Logs.user_id == options.user_id)
        if options.user_task_id is not None:
            query = query.where(Logs.user_task_id == options.user_task_id)

        if options.min_dt is not None:
            query = query.where(options.min_dt <= Logs.dt)
        if options.max_dt is not None:
            query = query.where(Logs.dt <= options.max_dt)

        return await db.fetch_all(query)  # type: ignore[return-value]

    @staticmethod
    async def get_latest_log() -> Optional['Logs']:
        return await db.fetch_one(select(Logs).order_by(Logs.entry_id.desc()).limit(1))  # type: ignore[return-value]
