import html
import re
from collections.abc import Callable
from typing import Any

from telethon import events, utils
from telethon.types import Message, User

from management.users import Users

from .config import BOT_NAME, bot

MESSAGE_LEN = 4096

WalletFunc = Callable[[Message, str], Any]
AdminFunc = Callable[[Message, Users, str], Any]
DecoratedFunc = Callable[[Message], Any]

def command_with_wallet(command: str) -> Callable[[WalletFunc], DecoratedFunc]:
    def inner(func: WalletFunc) -> DecoratedFunc:
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


def admin_command(command: str) -> Callable[[AdminFunc], DecoratedFunc]:
    def inner(func: AdminFunc) -> DecoratedFunc:
        @bot.on(events.NewMessage(pattern=fr'^/admin_{command}'))
        async def process(msg: Message) -> Any:
            if not msg.is_private:
                await msg.reply('This command can be used only in private chat')
                return None

            owner = await Users.get_by_tg(msg.sender_id)
            if not owner.is_admin:
                await msg.reply('This command can be used only by admins')
                return None

            args = re.search(fr'^/admin_{command}(?:@{BOT_NAME})? (.+)$', msg.raw_text)
            if not args or len(args.groups()) != 1:
                await msg.reply('This command requires arguments')
                return None

            return await func(msg, owner, args.group(1))
        return process
    return inner
