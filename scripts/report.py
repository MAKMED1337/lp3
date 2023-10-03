from helper.db_config import db
from helper.db_config import start as start_db
from helper.main_handler import main_handler
from management.connected_accounts import ConnectedAccounts
from management.reports import Reports

from .print_reports import print_reports


async def main() -> None:
    await start_db()

    user_id = input('User id: ')
    owner_id = await ConnectedAccounts.get_owner_id(user_id)
    assert owner_id is not None

    print('Previous reports:')
    await print_reports(owner_id)

    text = ''
    while (line := input('Text: ')) != '--end':
        text += line + '\n'

    penalty = bool(input('Penalty ? '))
    await Reports.report(owner_id, text, penalty)


if __name__ == '__main__':
    main_handler(main, None, db.disconnect)
