import asyncio
import sys
from typing import Any

from helper.async_helper import wait_pool
from helper.db_config import db
from helper.provider_config import provider

from .block_retriever import auto_retry, retrieve_new_blocks
from .config import block_logger_interval, settings
from .processed_blocks import ProcessedBlocks
from .receipts import Receipts


async def process_chunk(chunk: dict[str, Any]) -> None:
    for receipt_data in chunk['receipts']:
        if receipt_data['receiver_id'] != settings.watched_account:
            continue

        receipt_id = receipt_data['receipt_id']
        receipt = receipt_data['receipt']

        action_data = receipt['Action']
        signer_id = action_data['signer_id']

        for action in action_data['actions']:
            if 'Transfer' not in action:
                continue

            transfer = action['Transfer']
            price = int(transfer['deposit'])  # in mnear
            await Receipts.add(receipt_id, signer_id, price, price / settings.review_price)


async def process_new_blocks() -> None:
    async def process_block(block: dict[str, Any]) -> None:
        block_id = block['header']['height']

        # chunk processing
        # don't use semaphore here because this function is already called with one and it can cause deadlock
        chunks = await wait_pool([auto_retry(provider.get_chunk, chunk['chunk_hash']) for chunk in block['chunks']], use_semaphore=False)

        async with db.transaction():
            for chunk in chunks:
                await process_chunk(chunk)
            await ProcessedBlocks.set_processed(block_id)

    await retrieve_new_blocks(process_block)


async def last_block_watcher() -> None:
    prev = None
    while True:
        block_id = await ProcessedBlocks.get_last_id()
        print('Block id:', block_id)
        if block_id == prev:
            print(f'Stuck on {block_id}')
            print('Exiting...')
            sys.exit(1)

        prev = block_id
        await asyncio.sleep(block_logger_interval.seconds)
