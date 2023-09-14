import re

from telethon import events
from telethon.types import Message

from log_scraper.logs import Logs

from .config import BOT_NAME, bot

example_task_name = 'Часть VII. Избранные темы. Глава 34. NP-полнота. 34.5 NP-полные задачи, с. 1127: Part 1'  # noqa: RUF001


@bot.on(events.NewMessage(pattern=r'^/task_id'))
async def get_task_id(msg: Message) -> None:
    result = re.search(fr'^/task_id(?:@{BOT_NAME})? (.+)$', msg.raw_text)
    if not result or len(result.groups()) != 1:
        await msg.reply(f'Invalid task name.\nUsage: /task_id {example_task_name}')
        return

    name = result.group(1)
    task_id = await Logs.get_task_id(name)

    if task_id is None:
        await msg.reply("Can't find this task")
        return

    await msg.reply(str(task_id))
