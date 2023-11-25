import asyncio

from telethon import events
from telethon.types import Message

from log_scraper.logs import Logs
from management import ConnectedAccounts, Users

from .config import bot


@bot.on(events.NewMessage(pattern=r'^/reviews'))
async def connect_account(msg: Message) -> None:
    owner = await Users.get_by_tg(msg.sender_id)
    accounts = [] if owner is None else await ConnectedAccounts.get_accounts(owner.id)
    if not accounts:
        await msg.reply('No accounts')
        return

    assert owner is not None  # because None has no accounts

    tasks = [Logs.get_review_balance(account_id) for account_id in accounts]
    balance = sum(await asyncio.gather(*tasks))
    paid_reviews_left = owner.paid_reviews - await Logs.get_total_reviews_performed_for_user(owner.id)

    await msg.reply(f'Review balance: {balance}\nPaid reviews left: {paid_reviews_left}')
