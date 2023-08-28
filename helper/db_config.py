from typing import Any

import databases
import pydantic
import sqlalchemy
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, env_prefix='POSTGRES_')

    user: str
    password: str
    db: str
    host: str = 'localhost'
    port: int = 5432


_settings = DBSettings()
connection_url = URL.create(
    'postgresql',
    _settings.user,
    _settings.password,
    _settings.host,
    _settings.port,
    _settings.db,
)

class Base(
    MappedAsDataclass,
    DeclarativeBase,
    dataclass_callable=pydantic.dataclasses.dataclass,
):
    pass

engine = sqlalchemy.create_engine(connection_url)
db = databases.Database(connection_url.set(drivername='postgresql+aiopg', query={'pool_recycle': '3600'}).render_as_string(False))

class AttrDict(dict):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__dict__ = self

def to_mapping(table: Base | type[Base]) -> AttrDict:
    try:
        keys = table.__table__.columns.keys()  # type: ignore[attr-defined]
    except AttributeError:
        keys = table._mapping.keys()  # type: ignore[attr-defined, union-attr] # noqa: SLF001

    res = AttrDict()
    for i in keys:
        res[i] = getattr(table, i)
    return res

async def start() -> None:
    Base.metadata.create_all(engine)
    await db.connect()
