from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel
from sqlalchemy import JSON, VARCHAR, and_, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from helper.db_config import Base, db, to_mapping
from management.connected_accounts import ConnectedAccounts

from .config import REVIEWS_PER_TASK


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

    review_balance: Mapped[int | None] = mapped_column(default=None, server_default='0', nullable=False)

    async def get_balance(self) -> int:
        if self.review_balance is not None:
            return self.review_balance

        if self.type == Type.review:
            return -1
        if self.type != Type.task:
            return 0

        another_task = await db.fetch_one(select(Logs).where(and_(Logs.user_task_id == self.user_task_id, Logs.type == Type.task)))
        return REVIEWS_PER_TASK if another_task is None else 0

    async def upsert(self) -> None:
        async with db.transaction():
            self.review_balance = await self.get_balance()
            await db.execute(
                insert(Logs).on_conflict_do_update(index_elements=['entry_id'], set_=to_mapping(self)),
                to_mapping(self),
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

    @staticmethod
    async def get_all_review_balances_per_account() -> dict[str, int]:
        return dict(await db.fetch_all(select(Logs.user_id, func.sum(Logs.review_balance)).group_by(Logs.user_id)))  # type: ignore[arg-type]

    @staticmethod
    async def get_all_review_balances_per_user() -> dict[int, int]:
        query = select(ConnectedAccounts.owner_id, func.sum(Logs.review_balance)) \
            .join(Logs, Logs.user_id == ConnectedAccounts.user_id) \
            .group_by(ConnectedAccounts.owner_id)
        return dict(await db.fetch_all(query))  # type: ignore[arg-type]

    @staticmethod
    async def get_review_balance(user_id: str) -> int:
        return await db.fetch_val(select(func.sum(Logs.review_balance)).where(Logs.user_id == user_id))

    @staticmethod
    async def get_task_id(name: str) -> int | None:
        return await db.fetch_val(
            select(Logs.user_task_id)
            .where(func.replace(Logs.short_descr, ' ', '') == name.replace(' ', '').replace('\n', ''))
            .order_by(Logs.entry_id.desc()),
        )

    @staticmethod
    async def get_total_reviews_performed_per_user() -> dict[int, int]:
        return dict(await db.fetch_all(QUERY_PERFORMED_REVIEWS))  # type: ignore[arg-type]

    @staticmethod
    async def get_total_reviews_performed_for_user(owner_id: int) -> int:
        query = QUERY_PERFORMED_REVIEWS.where(ConnectedAccounts.owner_id == owner_id)  # specify owner
        result = await db.fetch_one(query)
        return result[1] if result is not None else 0  # return only count


QUERY_PERFORMED_REVIEWS = (
    select(ConnectedAccounts.owner_id, func.count())
    .join(Logs, Logs.user_id == ConnectedAccounts.user_id)
    .where(Logs.review_balance == -1)  # because review always decrease balance by 1
    .group_by(ConnectedAccounts.owner_id)
)
