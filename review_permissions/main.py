import asyncio

from accounts.lp3_account import PermissionId
from helper.db_config import db
from helper.db_config import start as start_db
from helper.lp3_config import lp3
from helper.main_handler import main_handler
from log_scraper.logs import Logs

from .whitelist import Whitelist


async def main() -> None:
    await start_db()

    while True:
        review_balances = await Logs.get_review_balances()
        whitelist = await Whitelist.get_all()

        for permission in await lp3.get_permissions():
            user_id = permission.user_id
            allow_reviews = review_balances.get(user_id, 0) > 0 and user_id in whitelist and whitelist[user_id].review
            review_permission = bool(permission.mask & 1 << PermissionId.review)

            if allow_reviews == review_permission:
                continue

            print('changing', user_id, 'to', allow_reviews)
            await lp3.update_permissions(user_id, PermissionId.review, allow_reviews)
        await asyncio.sleep(60)


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
