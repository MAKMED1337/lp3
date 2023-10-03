import html
import re
from collections.abc import Callable
from typing import Any

from telethon import events, utils
from telethon.types import Message, User

from .config import BOT_NAME, bot

OriginalFunc = Callable[[Message, str], Any]
DecoratedFunc = Callable[[Message], Any]

def command_with_wallet(command: str) -> Callable[[OriginalFunc], DecoratedFunc]:
    def inner(func: OriginalFunc) -> DecoratedFunc:
        @bot.on(events.NewMessage(pattern=fr'^/{command}'))
        async def process(msg: Message) -> Any:
            result = re.search(fr'^/{command}(?:@{BOT_NAME})? ([a-zA-Z0-9_.]+)$', msg.raw_text)
            if not result or len(result.groups()) != 1:
                await msg.reply(f'Invalid wallet.\nUsage: /{command} test.near')
                return None

            account_id = result.group(1)
            return await func(msg, account_id)
        return process
    return inner


def represent(user: User) -> str:
    if username := user.username:
        return '@' + username

    name = utils.get_display_name(user)
    if result := html.escape(name).replace('/', '/&NoBreak;'):
        return result

    return 'Deleted account'
