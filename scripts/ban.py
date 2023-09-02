from datetime import timedelta

from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from management.bans import Bans
from management.connected_accounts import ConnectedAccounts


async def main() -> None:
    await start_db()
    user_id = input('User id: ')
    reason = ''
    while (line := input('Reason: ')) != '--end':
        reason += line + '\n'

    owner_id = await ConnectedAccounts.get_owner_id(user_id)
    assert owner_id is not None

    await Bans.ban(owner_id, reason, timedelta(days=7))


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
