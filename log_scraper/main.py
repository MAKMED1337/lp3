import asyncio

from helper.db_config import db
from helper.db_config import start as start_db
from helper.lp3_config import lp3
from helper.main_handler import main_handler
from helper.utils import flatten

from .config import LIMIT
from .logs import Logs, LogsParams

min_entry_id: int = 0


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

    entry_ids = [i.entry_id for i in logs]
    if len(logs) != LIMIT or min_entry_id in entry_ids or entry_ids[0] <= min_entry_id:
        # end of logs OR we've reached min entry id OR we've passed(by HEAD) it(on previous iteration)
        return logs

    if params.max_dt == logs[-1].dt:
        # fallback to scraping per user
        print('fallback:', params.max_dt)
        return await _scrap_new_logs_per_user(params)

    params.max_dt = logs[-1].dt.strftime('%Y-%m-%d %H:%M:%S')
    logs.extend(await _scrap_new_logs(params))
    return logs


# ordered, only new ones
async def scrap_new_logs() -> list[Logs]:
    global min_entry_id
    if latest := await Logs.get_latest_log():
        min_entry_id = latest.entry_id
    logs = await _scrap_new_logs(LogsParams())
    logs.sort(key=lambda log: log.entry_id)
    return [i for i in logs if i.entry_id > min_entry_id]


async def main() -> None:
    await start_db()
    while True:
        logs = await scrap_new_logs()
        for log in logs:
            await log.upsert()
        await asyncio.sleep(5)


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
