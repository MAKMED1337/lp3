from .env import credentials
from .lp3_account import LP3Account

lp3 = LP3Account(credentials.account_id, credentials.private_key, credentials.farm_id)

LIMIT = 250
