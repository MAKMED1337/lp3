from telethon import events
from telethon.types import Message

from helper.db_config import db
from management import ConnectedAccounts, Users

from .config import bot
from .helper import command_with_wallet


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


@command_with_wallet('connect')
async def connect_account(msg: Message, account_id: str) -> None:
    owner_id = await ConnectedAccounts.get_owner_id(account_id)
    if owner_id is None:
        await msg.reply('Unknown account')
        return

    async with db.transaction():
        user: Users = await Users.get(owner_id)  # type: ignore[assignment]
        if user.tg_id is not None:
            await msg.reply('This account is already connected')
            return

        if await Users.get_by_tg(msg.sender_id):
            await msg.reply('You have already connected your account')
            return

        await Users.connect_tg(user.id, msg.sender_id)

    await msg.reply(await listify_accounts(user.id))
