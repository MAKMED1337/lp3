from pydantic_settings import BaseSettings

from accounts.lp3_account import LP3Account


class LP3Settings(BaseSettings):
    account_id: str
    private_key: str
    farm_id: int


_settings = LP3Settings()
lp3 = LP3Account(_settings.account_id, _settings.private_key, _settings.farm_id)
