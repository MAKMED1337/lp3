from pydantic_settings import BaseSettings


class Credentials(BaseSettings):
    account_id: str
    private_key: str
    farm_id: int


credentials = Credentials()
