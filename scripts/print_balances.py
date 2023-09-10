from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from log_scraper.logs import Logs
from management.connected_accounts import ConnectedAccounts
from management.users import Users


async def main() -> None:
    await start_db()
    owners = await ConnectedAccounts.get_owners()
    for user_id, balance in (await Logs.get_all_review_balances()).items():
        owner = await Users.get(owners[user_id])
        assert owner is not None

        print(user_id, '—', balance, owner.can_perform_reviews)


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
