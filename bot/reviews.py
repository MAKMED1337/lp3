import asyncio

from telethon import events
from telethon.types import Message

from log_scraper.logs import Logs
from management.connected_accounts import ConnectedAccounts
from management.users import Users

from .config import bot


@bot.on(events.NewMessage(pattern=r'^/reviews'))
async def connect_account(msg: Message) -> None:
    owner = await Users.get_by_tg(msg.sender_id)
    accounts = [] if owner is None else await ConnectedAccounts.get_accounts(owner.id)
    if not accounts:
        await msg.reply('No accounts')
        return

    text = ''
    tasks = [Logs.get_review_balance(account_id) for account_id in accounts]
    for account_id, balance in zip(accounts, await asyncio.gather(*tasks), strict=True):
        text += f'{account_id} — {balance}'
    await msg.reply(text)
