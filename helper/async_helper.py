import asyncio
from collections.abc import AsyncGenerator, Awaitable, Coroutine
from typing import Any, TypeVar

T = TypeVar('T')

COROS_LIMIT = 1000
semaphore = asyncio.Semaphore(COROS_LIMIT)


async def sem_coro(coro: Awaitable[T]) -> T:
    async with semaphore:
        return await coro


# unordered, unsafe (manual exception handling)
async def generator_pool(coros: list) -> AsyncGenerator[Any, None]:
    for i in asyncio.as_completed([sem_coro(c) for c in coros]):
        yield await i


# TODO proper exception handling
async def wait_pool(coros: list, *, use_semaphore: bool = True) -> list[Any]:
    if len(coros) == 0:
        return []

    def create_task(coro: Coroutine) -> asyncio.Task:
        return asyncio.create_task(sem_coro(coro) if use_semaphore else coro)

    done, pending = await asyncio.wait([create_task(i) for i in coros], return_when=asyncio.FIRST_EXCEPTION)
    for i in pending:
        i.cancel()

    for i in done:
        exc = i.exception()
        if exc is not None:
            raise exc
    return [i.result() for i in done]
