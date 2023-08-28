import asyncio
from datetime import datetime

from helper.db_config import db
from helper.db_config import start as start_db
from helper.lp3_config import lp3
from helper.main_handler import main_handler
from helper.utils import flatten

from .config import LIMIT
from .logs import Logs, LogsParams

min_dt: datetime = datetime(1, 1, 1)  # noqa: DTZ001


# unordered
async def _scrap_new_logs_per_user(params: LogsParams) -> list[Logs]:
    assert params.user_id is None
    tasks = []
    for perrmission in await lp3.get_permissions():
        params.user_id = perrmission.user_id
        tasks.append(_scrap_new_logs(params))
    return flatten(await asyncio.gather(*tasks))


# reverse order, unordered on fallback
async def _scrap_new_logs(params: LogsParams) -> list[Logs]:
    logs = await lp3.get_logs(params)

    if len(logs) != LIMIT or logs[-1].dt < min_dt:
        return logs

    if params.max_dt == logs[-1].dt:
        # fallback to scraping per user
        print('fallback:', params.max_dt)
        return await _scrap_new_logs_per_user(params)

    params.max_dt = logs[-1].dt.strftime('%Y-%m-%d %H:%M:%S')
    logs.extend(await _scrap_new_logs(params))
    return logs


# ordered
async def scrap_new_logs() -> list[Logs]:
    global min_dt
    latest = await Logs.get_latest_log()
    min_dt = latest.dt if latest else datetime(1, 1, 1)  # noqa: DTZ001
    logs = await _scrap_new_logs(LogsParams())
    logs.sort(key=lambda log: log.entry_id)
    return logs


async def main() -> None:
    await start_db()
    while True:
        for log in await scrap_new_logs():
            await log.upsert()
        await asyncio.sleep(1)


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
