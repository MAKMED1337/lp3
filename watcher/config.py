from datetime import timedelta

from pydantic_settings import BaseSettings


class WatchedAccountSettings(BaseSettings):
    watched_account: str
    review_price: int  # in mnear


settings = WatchedAccountSettings()

block_logger_interval = timedelta(minutes=10)
