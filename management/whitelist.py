from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column

from helper.db_config import Base, db, to_mapping


class Whitelist(Base):
    __tablename__ = 'whitelist'

    user_id: Mapped[str] = mapped_column(primary_key=True)
    review: Mapped[bool]

    @staticmethod
    async def can_do_reviews(user_id: str) -> bool:
        return await db.fetch_val(select(Whitelist.review).where(Whitelist.user_id == user_id)) is True

    async def upsert(self) -> None:
        await db.execute(
            insert(Whitelist).on_conflict_do_update(index_elements=['user_id'], set_=to_mapping(self)),
            to_mapping(self),
        )

    @staticmethod
    async def get_all() -> dict[str, 'Whitelist']:
        whitelist: list[Whitelist] = await db.fetch_all(select(Whitelist))  # type: ignore[assignment]
        return {i.user_id: i for i in whitelist}
