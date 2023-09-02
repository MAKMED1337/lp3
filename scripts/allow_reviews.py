from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from management.connected_accounts import ConnectedAccounts
from management.users import Users


async def main() -> None:
    await start_db()
    user_id = input('User id: ')

    owner_id = await ConnectedAccounts.get_owner_id(user_id)
    assert owner_id is not None
    await Users.allow_reviews(owner_id)


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
