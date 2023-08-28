from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from log_scraper.logs import Logs
from review_permissions.whitelist import Whitelist


async def main() -> None:
    await start_db()
    whitelist = await Whitelist.get_all()
    for user_id, balance in (await Logs.get_review_balances()).items():
        if user_id not in whitelist:
            continue

        print(user_id, '—', balance, whitelist[user_id].review)


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
