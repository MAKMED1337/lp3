from datetime import datetime, timedelta

from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from log_scraper.logs import Logs, LogsParams, Type


async def main() -> None:
    await start_db()

    logs = await Logs.get(LogsParams(types=[Type.task]))
    users: dict[str, list[Logs]] = {i.user_id: [] for i in logs}
    for i in logs:
        users[i.user_id].append(i)

    first_time_task = dict.fromkeys([i.user_task_id for i in logs], datetime.now() + timedelta(days=10))  # noqa: DTZ005
    for i in logs:
        first_time_task[i.user_task_id] = min(first_time_task[i.user_task_id], i.dt)

    week_before = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)  # noqa: DTZ005

    count = {user_id: 0 for user_id in users}
    for user_id, tasks in users.items():
        unique_tasks = set()
        for task in tasks:
            if task.user_task_id in unique_tasks:
                continue
            unique_tasks.add(task.user_task_id)

            if first_time_task[task.user_task_id] >= week_before:
                count[user_id] += 1

    sorted_count = [*count.items()]
    sorted_count.sort(key=lambda x: x[1], reverse=True)

    print([[*i] for i in sorted_count])


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
