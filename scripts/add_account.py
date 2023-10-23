from helper.db_config import db
from helper.db_config import start as start_db
from helper.lp3_config import lp3
from helper.main_handler import main_handler
from management import ConnectedAccounts, Users


async def main() -> None:
    await start_db()
    user_id = input('New user id: ')
    previous_id = input('Owner user id: ')

    if previous_id == '':
        owner_id = await Users.create()
    else:
        owner_id = await ConnectedAccounts.get_owner_id(previous_id)  # type: ignore[assignment]
        assert owner_id is not None

    await Users.add_account(owner_id, user_id)
    await lp3.add_user(user_id)


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
