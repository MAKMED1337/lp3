from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from log_scraper.logs import Logs
from review_permissions.whitelist import Whitelist


async def main() -> None:
    await start_db()
    whitelist_users = [i.user_id for i in await Whitelist.get_all()]
    for user_id, balance in (await Logs.get_review_balances()).items():
        if user_id in whitelist_users:
            print(user_id, '—', balance)


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
