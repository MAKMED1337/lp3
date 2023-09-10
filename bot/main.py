from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler

from . import connection  # noqa: F401
from .config import run, start


async def main() -> None:
    await start_db()
    await start()
    await run()

if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
