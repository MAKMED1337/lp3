from sqlalchemy import BigInteger, func, insert, select, update
from sqlalchemy.orm import Mapped, mapped_column

from helper.db_config import Base, db


class ProcessedBlocks(Base):
    __tablename__ = 'processed_blocks'

    block_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    processed: Mapped[bool] = mapped_column(default=False, server_default='false')

    @staticmethod
    async def get_last_id() -> int | None:
        return await db.fetch_val(select(func.max(ProcessedBlocks.block_id)))

    @staticmethod
    async def set_processed(block_id: int) -> None:
        await db.execute(update(ProcessedBlocks).where(ProcessedBlocks.block_id == block_id).values(processed=True))

    @staticmethod
    async def get_unprocessed() -> list[int]:
        return await db.fetch_column(select(ProcessedBlocks.block_id).where(ProcessedBlocks.processed == False))  # noqa: E712

    @staticmethod
    async def add_range(start: int, finish: int) -> None:
        await db.execute_many(insert(ProcessedBlocks), [{'block_id': i, 'processed': False} for i in range(start, finish + 1)])
