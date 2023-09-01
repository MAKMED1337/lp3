from datetime import timedelta

from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from management.bans import Bans
from management.users import Users


async def main() -> None:
    await start_db()
    user_id = input()
    reason = ''
    while (line := input()) != '--end':
        reason += line + '\n'

    owner_id = await Users.get_owner(user_id)
    await Bans.ban(owner_id, reason, timedelta(days=7))


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
