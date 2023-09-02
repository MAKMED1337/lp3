from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from management.connected_accounts import ConnectedAccounts
from management.user import Users
from management.whitelist import Whitelist


async def main() -> None:
    await start_db()
    user_id = input('New user id: ')
    previous_id = input('Owner user id: ')

    if previous_id == '':
        owner = await Users.create()
    else:
        owner_id = await ConnectedAccounts.get_owner_id(previous_id)
        assert owner_id is not None
        owner = Users(owner_id)

    await owner.add_account(user_id)
    await Whitelist(user_id, False).upsert()


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
