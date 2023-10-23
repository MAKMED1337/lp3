from collections.abc import Callable
from datetime import timedelta
from typing import Any

from telethon.custom import Conversation
from telethon.types import Message

from management.bans import Bans
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


async def read_until(conv: Conversation, text: str, func: Callable[[str], Any | None]) -> Any:
    while True:
        await conv.send_message(text)
        answer = await get_response(conv)
        parsed = func(answer)

        if parsed is not None:
            return parsed


async def read_yes(conv: Conversation, text: str) -> bool:
    def parse_answer(s: str) -> bool | None:
        if s in ('yes', 'no'):
            return s == 'yes'
        return None

    return await read_until(conv, f'{text}\nAnswer with "yes" or "no"!', parse_answer)


async def person_clarification(conv: Conversation, action: str, account_id: str, user_id: int) -> bool:
    user = await Users.get(user_id)
    assert user is not None

    tg_repr = 'No tg'
    if user.tg_id is not None:
        tg_repr = represent(await bot.get_entity(user.tg_id))

    return await read_yes(conv, f'Are you sure you want to {action} {account_id} ({tg_repr}) ?')


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
    return await read_yes(conv, 'Penalty ?')


async def get_duration(conv: Conversation) -> timedelta:
    def parse_answer(s: str) -> int | None:
        try:
            return int(s)
        except ValueError:
            return None

    days = await read_until(conv, 'Enter duration in days ?', parse_answer)
    return timedelta(days=days)


@admin_command('report')
async def report(msg: Message, admin: Users, account_id: str) -> None:
    owner_id = await ConnectedAccounts.get_owner_id(account_id)
    if owner_id is None:
        await msg.reply('Unknown account')
        return

    async with bot.conversation(msg.sender) as conv:
        try:
            if not await person_clarification(conv, 'report', account_id, owner_id):
                await conv.send_message('Stopping conversation, reason: wrong person')
                return
            await conv.send_message('You can use /stop to stop conversation if you have chosen the wrong person')

            reason = await get_reason(conv, owner_id)
            penalty = await get_penalty(conv)

            await Reports.report(owner_id, reason, penalty, admin_id=admin.id)
            await conv.send_message('Done!')
        except TimeoutError:
            await conv.send_message('Stopping conversation, reason: AFK')
        except StopConversation:
            await conv.send_message('Stopping conversation, reason: /stop requested')


@admin_command('ban_reviews')
async def ban_reviews(msg: Message, admin: Users, account_id: str) -> None:
    owner_id = await ConnectedAccounts.get_owner_id(account_id)
    if owner_id is None:
        await msg.reply('Unknown account')
        return

    async with bot.conversation(msg.sender) as conv:
        try:
            if not await person_clarification(conv, 'ban', account_id, owner_id):
                await conv.send_message('Stopping conversation, reason: wrong person')
                return
            await conv.send_message('You can use /stop to stop conversation if you have chosen the wrong person')

            reason = await get_reason(conv, owner_id)
            duration = await get_duration(conv)

            await Bans.ban(owner_id, reason, duration, admin_id=admin.id)
            await conv.send_message('Done!')
        except TimeoutError:
            await conv.send_message('Stopping conversation, reason: AFK')
        except StopConversation:
            await conv.send_message('Stopping conversation, reason: /stop requested')
