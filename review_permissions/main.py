import asyncio

from accounts.lp3_account import PermissionId
from helper.db_config import db
from helper.db_config import start as start_db
from helper.lp3_config import lp3
from helper.main_handler import main_handler
from log_scraper.logs import Logs
from management import Bans, ConnectedAccounts, Users

account_owners: dict[str, int] = {}
owners: dict[int, Users] = {}
review_balances: dict[int, int] = {}
bans: list[Bans] = []

def do_allow_reviews(user_id: str) -> bool:
    owner_id = account_owners.get(user_id)
    if owner_id is None:
        return False

    if not owners[owner_id].can_perform_reviews or review_balances.get(owner_id, 0) <= 0:
        return False

    return all(ban.owner_id != owner_id for ban in bans)


async def main() -> None:
    global account_owners, owners, review_balances, bans
    await start_db()

    while True:
        review_balances = await Logs.get_all_review_balances_per_user()
        owners = {i.id: i for i in await Users.get_all()}
        account_owners = await ConnectedAccounts.get_owners()
        bans = await Bans.active_bans()

        for permission in await lp3.get_permissions():
            user_id = permission.user_id
            allow_reviews = do_allow_reviews(user_id)

            review_permission = bool(permission.mask & 1 << PermissionId.review)

            if allow_reviews == review_permission:
                continue

            print('changing', user_id, 'to', allow_reviews)
            await lp3.update_permissions(user_id, PermissionId.review, allow_reviews)
        await asyncio.sleep(60)


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
