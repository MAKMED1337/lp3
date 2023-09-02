from typing import Optional

from sqlalchemy import insert, select, update
from sqlalchemy.orm import Mapped, mapped_column

from helper.db_config import Base, db

from .connected_accounts import ConnectedAccounts


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    can_perform_reviews: Mapped[bool] = mapped_column(default=False, server_default='false')

    @staticmethod
    async def add_account(id: int, user_id: str) -> None:
        await db.execute(insert(ConnectedAccounts).values((user_id, id)))

    @staticmethod
    async def get(id: int) -> Optional['Users']:
        return await db.fetch_one(select(Users).where(Users.id == id))  # type: ignore[return-value]

    @staticmethod
    async def create() -> int:
        return await db.execute(insert(Users).values().returning(Users.id))

    @staticmethod
    async def get_accounts(id: int) -> list[str]:
        return await db.fetch_column(select(ConnectedAccounts.user_id).where(ConnectedAccounts.owner_id == id))

    @staticmethod
    async def allow_reviews(id: int) -> None:
        await db.execute(update(Users).where(Users.id == id).values(can_perfom_reviews=True))

    @staticmethod
    async def get_all() -> list['Users']:
        return await db.fetch_all(select(Users))  # type: ignore[return-value]
