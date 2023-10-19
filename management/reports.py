from datetime import datetime

from sqlalchemy import ForeignKey, insert, select
from sqlalchemy.orm import Mapped, mapped_column

from helper.db_config import Base, db

from .users import Users  # noqa: F401


class Reports(Base):
    __tablename__ = 'reports'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dt: Mapped[datetime]
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    text: Mapped[str]
    penalty: Mapped[bool]
    admin_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    @staticmethod
    async def report(owner_id: int, text: str, penalty: bool = False, *, dt: datetime | None = None, admin_id: int) -> None:
        dt = dt or datetime.now()  # noqa: DTZ005
        await db.execute(insert(Reports).values(owner_id=owner_id, text=text, dt=dt, penalty=penalty, admin_id=admin_id))

    @staticmethod
    async def get_reports(owner_id: int) -> list['Reports']:
        return await db.fetch_all(select(Reports).where(Reports.owner_id == owner_id))  # type: ignore[return-value]
