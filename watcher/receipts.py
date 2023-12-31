from sqlalchemy import NUMERIC, VARCHAR, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from helper.db_config import Base, db
from management import ConnectedAccounts


class Receipts(Base):
    __tablename__ = 'receipts'

    receipt_id: Mapped[str] = mapped_column(VARCHAR(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(VARCHAR(64))
    price: Mapped[int] = mapped_column(NUMERIC(40, 0))  # in mnear, mnear has type u128 that holds up to 39 digits, so 40 should be enough
    reviews: Mapped[float]  # use float just in case of human error

    @staticmethod
    async def add(receipt_id: str, account_id: str, price: int, reviews: float) -> None:
        print('new tx:', receipt_id, account_id, price, '->', reviews)
        query = insert(Receipts).values((receipt_id, account_id, price, reviews)) \
            .on_conflict_do_nothing()
        await db.execute(query)

    @staticmethod
    async def get_paid_reviews_per_user() -> dict[int, float]:
        return dict(await db.fetch_all(QUERY_PAID_REVIEWS))  # type: ignore[arg-type]

    @staticmethod
    async def get_paid_reviews_for_user(owner_id: int) -> float:
        query = QUERY_PAID_REVIEWS.where(ConnectedAccounts.owner_id == owner_id)  # specify owner
        result = await db.fetch_one(query)
        return result[1] if result is not None else 0  # return only amount

QUERY_PAID_REVIEWS = (
    select(ConnectedAccounts.owner_id, func.sum(Receipts.reviews))
    .join(Receipts, Receipts.account_id == ConnectedAccounts.user_id)
    .group_by(ConnectedAccounts.owner_id)
)
