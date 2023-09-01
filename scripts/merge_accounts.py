from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from management.users import Users
from management.whitelist import Whitelist


def normalize_name(user_id: str) -> str:
    user_id = user_id.split('.')[0]
    if user_id[-2] == '_' and '0' <= user_id[-1] <= '9':
        return user_id[:-2]
    return user_id


async def main() -> None:
    await start_db()
    whitelist = await Whitelist.get_all()

    index: dict[str, int] = {}
    for user_id in whitelist:
        name = normalize_name(user_id)
        if name in index:
            await Users.add(user_id, index[name])
        else:
            await Users.add(user_id, None)
            index[name] = len(index) + 1

        print(user_id, '->', index[name])


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
