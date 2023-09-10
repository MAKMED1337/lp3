from pydantic_settings import BaseSettings, SettingsConfigDict
from telethon import TelegramClient


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False)

    api_hash: str
    api_id: int
    bot_name: str
    token: str

_settings = BotSettings()
BOT_NAME = _settings.bot_name

bot = TelegramClient(f'sessions/{_settings.bot_name}', _settings.api_id, _settings.api_hash, catch_up=True)
bot.parse_mode = 'html'

async def start() -> None:
    await bot.start(bot_token=_settings.token)
    await bot.catch_up()

async def run() -> None:
    await start()
    await bot.run_until_disconnected()
