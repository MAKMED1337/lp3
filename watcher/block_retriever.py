import asyncio
from collections.abc import Awaitable, Callable, Iterator
from typing import Any

from helper.async_helper import COROS_LIMIT, wait_pool
from helper.provider_config import provider
from near.providers import FinalityTypes, JsonProviderError

from .processed_blocks import ProcessedBlocks

TRIES = 100


async def auto_retry(func: Callable, *args: Any, **kwargs: Any) -> Any:
    for r in range(TRIES):
        try:
            return await func(*args, **kwargs)
        except Exception:  # noqa: BLE001
            if r == TRIES - 1:
                raise
            await asyncio.sleep(1)
    return None


async def get_block_by_id(id: int) -> dict | None:
    for _ in range(TRIES):
        try:
            return await provider.get_block(id)
        except JsonProviderError as exc:
            e = exc.error
            if e['cause']['name'] != 'UNKNOWN_BLOCK':
                raise
            return None
        except Exception:  # noqa: BLE001, S110
            pass

        await asyncio.sleep(1)

    print('smth wrong with block:', id)
    return None


def split_into_chunks(lst: list, n: int) -> Iterator[list]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# unordered
async def retrieve_new_blocks(process_block: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
    block = await auto_retry(provider.get_block, finality=FinalityTypes.FINAL)

    if block is None:
        return

    last_block = block['header']['height']
    last_processed_block = await ProcessedBlocks.get_last_id()
    if last_processed_block is None:
        last_processed_block = last_block - 1
    elif last_processed_block == last_block:
        return

    await ProcessedBlocks.add_range(last_processed_block + 1, last_block)

    async def load_and_process(block_id: int) -> None:
        block = await get_block_by_id(block_id)
        if block is None:
            await ProcessedBlocks.set_processed(block_id)  # Don't process zombie blocks
        else:
            await process_block(block)

    for chunk in split_into_chunks(await ProcessedBlocks.get_unprocessed(), COROS_LIMIT):  # to reduce memory usage
        await wait_pool([load_and_process(id) for id in chunk])
