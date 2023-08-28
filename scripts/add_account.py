from helper.db_config import db
from helper.db_config import start as start_db
from helper.lp3_config import lp3
from helper.main_handler import main_handler
from review_permissions.whitelist import Whitelist


def normalize_name(user_id: str) -> str:
    user_id = user_id.split('.')[0]
    if user_id[-2] == '_' and '0' <= user_id[-1] <= '9':
        return user_id[:-2]
    return user_id


async def main() -> None:
    await start_db()
    allowed = normalize_name(input())

    for permission in await lp3.get_permissions():
        user_id = permission.user_id
        if normalize_name(user_id) == allowed:
            print(user_id)
            await Whitelist(user_id, True).upsert()


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
