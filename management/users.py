from typing import Optional

from sqlalchemy import BigInteger, insert, select, update
from sqlalchemy.orm import Mapped, mapped_column

from helper.db_config import Base, db

from .connected_accounts import ConnectedAccounts


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    can_perform_reviews: Mapped[bool] = mapped_column(default=False, server_default='false')

    @staticmethod
    async def add_account(id: int, user_id: str) -> None:
        await db.execute(insert(ConnectedAccounts).values((user_id, id)))

    @staticmethod
    async def get(id: int) -> Optional['Users']:
        return await db.fetch_one(select(Users).where(Users.id == id))  # type: ignore[return-value]

    @staticmethod
    async def get_by_tg(tg_id: int) -> Optional['Users']:
        return await db.fetch_one(select(Users).where(Users.tg_id == tg_id))  # type: ignore[return-value]

    @staticmethod
    async def connect_tg(id: int, tg_id: int) -> None:
        await db.execute(update(Users).where(Users.id == id).values(tg_id=tg_id))

    @staticmethod
    async def create() -> int:
        return await db.fetch_val(insert(Users).returning(Users.id), {'can_perform_reviews': False})  # some trouble with default values

    @staticmethod
    async def get_accounts(id: int) -> list[str]:
        return await db.fetch_column(select(ConnectedAccounts.user_id).where(ConnectedAccounts.owner_id == id))

    @staticmethod
    async def allow_reviews(id: int) -> None:
        await db.execute(update(Users).where(Users.id == id).values(can_perform_reviews=True))

    @staticmethod
    async def get_all() -> list['Users']:
        return await db.fetch_all(select(Users))  # type: ignore[return-value]
