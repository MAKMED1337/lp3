from base58 import b58encode_int
from sqlalchemy import delete

from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from management import Users
from watcher.receipts import Receipts


async def main() -> None:
    await start_db()

    async with db.transaction():
        users = await Users.get_all()
        paid_reviews = await Receipts.get_paid_reviews_per_user()

        await db.execute(delete(Receipts).where(Receipts.receipt_id.startswith('FAKE-')))

        for user in users:
            id = user.id
            accounts = await Users.get_accounts(id)
            assert user

            receipt_id = f'FAKE-{b58encode_int(id).decode("ascii")}'
            await Receipts.add(receipt_id, accounts[0], 0, user.paid_reviews - paid_reviews.get(id, 0))

if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
