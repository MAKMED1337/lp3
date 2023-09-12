from telethon.types import Message

from management.connected_accounts import ConnectedAccounts
from management.users import Users

from .config import bot
from .helper import command_with_wallet, represent


@command_with_wallet('owner')
async def connect_account(msg: Message, account_id: str) -> None:
    owner_id = await ConnectedAccounts.get_owner_id(account_id)
    if owner_id is None:
        await msg.reply('Unknown account')
        return

    owner = await Users.get(owner_id)
    assert owner is not None

    if owner.tg_id is None:
        await msg.reply("User hasn't connected his tg")
        return

    user = await bot.get_entity(owner.tg_id)
    await msg.reply(represent(user))
