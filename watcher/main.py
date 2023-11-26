import asyncio

from helper.db_config import db
from helper.db_config import start as db_start
from helper.main_handler import main_handler
from helper.provider_config import provider

from .block_processor import last_block_watcher, process_new_blocks

block_watcher = None


async def start() -> None:
    global block_watcher
    provider.start()
    await db_start()

    # process new blocks for the first time without watcher
    # because if there are too many unprocessed blocks
    # block watcher can kill program and it'll cause deadlock (restarting)
    await process_new_blocks()

    block_watcher = asyncio.create_task(last_block_watcher())


async def main() -> None:
    await start()
    while True:
        await process_new_blocks()
        await asyncio.sleep(5)


async def stop() -> None:
    await db.disconnect()
    await provider.close()
    if block_watcher is not None:
        block_watcher.cancel()


if __name__ == '__main__':
    main_handler(main, None, stop)
