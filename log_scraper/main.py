import asyncio
from datetime import datetime

from helper.db_config import db
from helper.db_config import start as start_db

from .config import LIMIT, lp3
from .logs import Logs, LogsParams

min_dt: datetime = datetime(1, 1, 1)  # noqa: DTZ001

async def _scrap_new_logs_per_user(params: LogsParams) -> None:
    assert params.user_id is None
    tasks = []
    for perrmission in await lp3.get_permissions():
        params.user_id = perrmission.user_id
        tasks.append(_scrap_new_logs(params))
    await asyncio.gather(*tasks)


async def _scrap_new_logs(params: LogsParams) -> None:
    logs = await lp3.get_logs(params)
    await Logs.bulk_upsert(logs)

    if len(logs) != LIMIT or logs[-1].dt < min_dt:
        return

    if params.max_dt == logs[-1].dt:
        # fallback to scraping per user
        print('fallback:', params.max_dt)
        await _scrap_new_logs_per_user(params)
        return

    params.max_dt = logs[-1].dt.strftime('%Y-%m-%d %H:%M:%S')
    await _scrap_new_logs(params)


async def scrap_new_logs() -> None:
    global min_dt
    async with db.transaction():
        latest = await Logs.get_latest_log()
        min_dt = latest.dt if latest else datetime(1, 1, 1)  # noqa: DTZ001
        await _scrap_new_logs(LogsParams())


async def main() -> None:
    await start_db()
    while True:
        await scrap_new_logs()
        await asyncio.sleep(1)


asyncio.run(main())
