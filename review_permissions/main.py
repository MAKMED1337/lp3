import asyncio

from accounts.lp3_account import PermissionId
from helper.db_config import db
from helper.db_config import start as start_db
from helper.lp3_config import lp3
from helper.main_handler import main_handler
from log_scraper.logs import Logs
from management.bans import Bans
from management.connected_accounts import ConnectedAccounts
from management.whitelist import Whitelist

owners: dict[str, int] = {}
review_balances: dict[str, int] = {}
whitelist: dict[str, Whitelist] = {}
bans: list[Bans] = []

async def is_allowed_review(user_id: str) -> bool:
    if review_balances.get(user_id, 0) <= 0:
        return False

    if user_id not in whitelist or not whitelist[user_id].review:
        return False

    return all(ban.owner_id != owners[user_id] for ban in bans)


async def main() -> None:
    global owners, review_balances, whitelist, bans
    await start_db()

    while True:
        review_balances = await Logs.get_review_balances()
        whitelist = await Whitelist.get_all()
        owners = await ConnectedAccounts.get_owners()
        bans = await Bans.active_bans()

        for permission in await lp3.get_permissions():
            user_id = permission.user_id
            allow_reviews = await is_allowed_review(user_id)

            review_permission = bool(permission.mask & 1 << PermissionId.review)

            if allow_reviews == review_permission:
                continue

            print('changing', user_id, 'to', allow_reviews)
            await lp3.update_permissions(user_id, PermissionId.review, allow_reviews)
        await asyncio.sleep(60)


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
