from telethon.custom import Conversation
from telethon.types import Message

from management.connected_accounts import ConnectedAccounts
from management.reports import Reports
from management.users import Users

from .config import bot
from .helper import MESSAGE_LEN, admin_command, represent


class StopConversation(Exception):  # noqa: N818
    pass


# helper to raise StopConversation on /stop
async def get_response(conv: Conversation) -> str:
    response = await conv.get_response()
    text = response.text
    if text == '/stop':
        raise StopConversation
    return text


async def person_clarification(conv: Conversation, account_id: str, user_id: int) -> bool:
    user = await Users.get(user_id)
    assert user is not None

    tg_repr = 'No tg'
    if user.tg_id is not None:
        tg_repr = represent(await bot.get_entity(user.tg_id))

    await conv.send_message(f'Are you sure you want to report {account_id} ({tg_repr}) ?\nAnswer with "yes" or "no"!\nUse /stop to stop conversation')
    return await get_response(conv) == 'yes'


async def get_reason(conv: Conversation, user_id: int) -> str:
    formatted_reports = [] # in reverse order
    for report in (await Reports.get_reports(user_id))[::-1]:
        text = '[' + report.dt.isoformat(' ', 'seconds') + f'] {report.text}'
        formatted_reports.append(text)

    text = 'Enter you reason below.\nRecent reports(reverse order):'
    for formatted_report in formatted_reports:
        next_text = text + '\n' + formatted_report
        if len(next_text) >= MESSAGE_LEN:
            break
        text = next_text

    await conv.send_message(text)
    return await get_response(conv)


async def get_penalty(conv: Conversation) -> bool:
    while True:
        await conv.send_message('Penalty ?\nAnswer with "yes" or "no"!')
        text = await get_response(conv)

        if text in ('yes', 'no'):
            return text == 'yes'


@admin_command('report')
async def report(msg: Message, admin: Users, account_id: str) -> None:
    owner_id = await ConnectedAccounts.get_owner_id(account_id)
    if owner_id is None:
        await msg.reply('Unknown account')
        return

    async with bot.conversation(msg.sender) as conv:
        try:
            if not await person_clarification(conv, account_id, owner_id):
                await conv.send_message('Stopping conversation, reason: wrong person')
                return

            reason = await get_reason(conv, owner_id)
            penalty = await get_penalty(conv)

            await Reports.report(owner_id, reason, penalty, admin_id=admin.id)
            await conv.send_message('Done!')
        except TimeoutError:
            await conv.send_message('Stopping conversation, reason: AFK')
        except StopConversation:
            await conv.send_message('Stopping conversation, reason: /stop requested')
