import asyncio
from datetime import datetime

from helper.db_config import db
from helper.db_config import start as start_db
from helper.lp3_config import lp3
from helper.main_handler import main_handler

from .config import SAMPLING_INTERVAL
from .samples import Samples


async def generate_sample() -> None:
    sample = await Samples.last_sample()
    now = datetime.now()  # noqa: DTZ005
    if sample is not None and now < sample.dt + SAMPLING_INTERVAL:
        return

    task_id = await Samples.select_random_sample()
    if task_id is None:
        return

    print('sampling', task_id)
    await lp3.report_review(task_id, 0, f'SAMPLE: {now.strftime("%Y-%m-%d")}')
    await Samples.add(task_id)


async def main() -> None:
    await start_db()

    while True:
        await generate_sample()
        await asyncio.sleep(60)


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
