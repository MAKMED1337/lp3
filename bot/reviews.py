import re

from telethon import events
from telethon.types import Message

from log_scraper.logs import Logs
from management.connected_accounts import ConnectedAccounts
from management.users import Users

from .config import BOT_NAME, bot


@bot.on(events.NewMessage(pattern=r'^/reviews'))
async def connect_account(msg: Message) -> None:
    result = re.search(fr'^/reviews(?:@{BOT_NAME})? ([a-zA-Z0-9_.]+)$', msg.text)
    if not result or len(result.groups()) != 1:
        await msg.reply('Invalid wallet.\nUsage: /reviews test.near')
        return

    account_id = result.group(1)
    owner_id = await ConnectedAccounts.get_owner_id(account_id)
    if owner_id is None:
        await msg.reply('Unknown account')
        return

    user: Users = await Users.get(owner_id)  # type: ignore[assignment]
    if user.tg_id != msg.sender_id:
        await msg.reply('This account is not yours')
        return

    await msg.reply(str(await Logs.get_review_balance(account_id)))
