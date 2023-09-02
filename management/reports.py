from sqlalchemy import ForeignKey, insert, select
from sqlalchemy.orm import Mapped, mapped_column

from helper.db_config import Base, db

from .users import Users  # noqa: F401


class Reports(Base):
    __tablename__ = 'reports'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    text: Mapped[str]

    @staticmethod
    async def report(owner_id: int, text: str) -> None:
        await db.execute(insert(Reports).values(owner_id=owner_id, text=text))

    @staticmethod
    async def get_reports(owner_id: int) -> list['Reports']:
        return await db.fetch_all(select(Reports).where(Reports.owner_id == owner_id))  # type: ignore[return-value]
