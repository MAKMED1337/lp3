from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from management.users import Users
from management.whitelist import Whitelist


async def main() -> None:
    await start_db()
    user_id = input()

    owner_id = await Users.get_owner(user_id)
    assert owner_id is not None

    for user_id in await Users.get_accounts(owner_id):
        await Whitelist(user_id, True).upsert()


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
