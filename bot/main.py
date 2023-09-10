import re

from telethon import events
from telethon.types import Message

from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from management.connected_accounts import ConnectedAccounts
from management.users import Users

from .config import BOT_NAME, bot, run, start


async def listify_accounts(user_id: int) -> str:
    accounts = await Users.get_accounts(user_id)
    if not accounts:
        return 'No accounts'
    return '\n'.join(['Accounts:', *accounts])


@bot.on(events.NewMessage(pattern=r'^/list'))
async def connected_accounts(msg: Message) -> None:
    user = await Users.get_by_tg(msg.sender_id)
    if user is None:
        await msg.reply('Unknow user')
        return

    await msg.reply(await listify_accounts(user.id))


@bot.on(events.NewMessage(pattern=r'^/connect'))
async def connect_account(msg: Message) -> None:
    result = re.search(fr'^/connect(?:@{BOT_NAME})? ([a-zA-Z0-9_.]+)$', msg.text)
    if not result or len(result.groups()) != 1:
        await msg.reply('Invalid wallet.\nUsage: /connect test.near')
        return

    account_id = result.group(1)
    owner_id = await ConnectedAccounts.get_owner_id(account_id)
    if owner_id is None:
        await msg.reply('Unknown account')
        return

    async with db.transaction():
        user = await Users.get(owner_id)
        if user.tg_id is not None:
            await msg.reply('This account is already connected')
            return

        if await Users.get_by_tg(msg.sender_id):
            await msg.reply('You have already connected your account')
            return

        await Users.connect_tg(user.id, msg.sender_id)

    await msg.reply(await listify_accounts(user.id))


async def main() -> None:
    await start_db()
    await start()
    await run()

if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
