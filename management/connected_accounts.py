from sqlalchemy import ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column

from helper.db_config import Base, db


class ConnectedAccounts(Base):
    __tablename__ = 'connected_accounts'

    user_id: Mapped[str] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('user.id'))

    @staticmethod
    async def get_owner_id(user_id: str) -> int | None:
        return await db.fetch_val(select(ConnectedAccounts.owner_id).where(ConnectedAccounts.user_id == user_id))

    @staticmethod
    async def get_owners() -> dict[str, int]:
        users: list[ConnectedAccounts] = await db.fetch_all(select(ConnectedAccounts))  # type: ignore[assignment]
        return {i.user_id: i.owner_id for i in users}

    @staticmethod
    async def get_accounts(owner_id: int) -> list[str]:
        return await db.fetch_column(select(ConnectedAccounts.user_id).where(ConnectedAccounts.owner_id == owner_id))
