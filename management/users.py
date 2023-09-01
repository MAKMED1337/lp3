from typing import Any

from sqlalchemy import Identity, insert, select
from sqlalchemy.orm import Mapped, mapped_column

from helper.db_config import Base, db


class Users(Base):
    __tablename__ = 'users'

    user_id: Mapped[str] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(Identity())

    @staticmethod
    async def get_owner(user_id: str) -> int | None:
        return await db.fetch_val(select(Users.owner_id).where(Users.user_id == user_id))

    @staticmethod
    async def add(user_id: str, owner_id: int | None) -> int:
        data: dict[str, Any] = {'user_id': user_id}
        if owner_id is not None:
            data['owner_id'] = owner_id
        return await db.execute(insert(Users).values(data).returning(Users.owner_id))

    @staticmethod
    async def get_owners() -> dict[str, int]:
        users: list[Users] = await db.fetch_all(select(Users))  # type: ignore[assignment]
        return {i.user_id: i.owner_id for i in users}

    @staticmethod
    async def get_accounts(owner_id: int) -> list[str]:
        return await db.fetch_column(select(Users.user_id).where(Users.owner_id == owner_id))
