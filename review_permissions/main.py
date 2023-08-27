import asyncio
from datetime import datetime, timedelta

from helper.db_config import start as start_db
from log_scraper.logs import Logs, LogsParams, Type


async def main() -> None:
    await start_db()
    logs = await Logs.get(LogsParams(types=[Type.task]))
    users = {i.user_id: [] for i in logs}
    for i in logs:
        users[i.user_id].append(i)

    first_time_task = {i.user_task_id: datetime.now() + timedelta(days=10) for i in logs}  # noqa: DTZ005
    for i in logs:
        first_time_task[i.user_task_id] = min(first_time_task[i.user_task_id], i.dt)

    count = {user_id: 0 for user_id in users}
    for user_id, tasks in users.items():
        unique_tasks = set()
        for task in tasks:
            if task.user_task_id in unique_tasks:
                continue
            unique_tasks.add(task.user_task_id)

            if first_time_task[task.user_task_id] >= datetime(year=2023, month=8, day=14):  # noqa: DTZ001
                count[user_id] += 1

    sorted_count = [*count.items()]
    sorted_count.sort(key=lambda x: x[1], reverse=True)

    print([[*i] for i in sorted_count])


asyncio.run(main())
