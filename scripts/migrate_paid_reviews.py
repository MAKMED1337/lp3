from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from log_scraper.logs import Logs
from management import Users


async def main() -> None:
    await start_db()

    async with db.transaction():
        performed_reviews = await Logs.get_total_reviews_performed_per_user()

        for owner_id, performed in performed_reviews.items():
            user = await Users.get(owner_id)
            assert user
            await Users.add_paid_reviews(owner_id, performed - user.paid_reviews)  # set to already performed reviews

if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
