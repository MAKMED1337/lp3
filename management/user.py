from typing import Optional

from sqlalchemy import insert, select
from sqlalchemy.orm import Mapped, mapped_column

from helper.db_config import Base, db

from .connected_accounts import ConnectedAccounts


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    async def add_account(self, user_id: str) -> None:
        await db.execute(insert(ConnectedAccounts).values((user_id, self.id)))

    @staticmethod
    async def get(id: int) -> Optional['Users']:
        return await db.fetch_one(select(Users).where(Users.id == id))  # type: ignore[return-value]

    @staticmethod
    async def create() -> 'Users':
        id = await db.execute(insert(Users).values().returning(Users.id))
        return Users(id)

    async def get_accounts(self) -> list[str]:
        return await db.fetch_column(select(ConnectedAccounts.user_id).where(ConnectedAccounts.owner_id == self.id))
