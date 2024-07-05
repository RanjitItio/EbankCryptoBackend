"""
Application settings handled using Pydantic Settings management.

Pydantic is used both to read app settings from various sources, and to validate their
values.

https://docs.pydantic.dev/latest/usage/settings/
"""
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from decouple import config


CRYPTO_CONFIG = {
    "dogecoin_api_key":'09d7-7b5c-a11d-a233',
    "bitcoin_api_key":'0d25-0de7-1052-e04a',
    "litcoin_api_key":'ee6a-5cb6-4f85-3247',
}


SECURITIES_CODE ='AEB8E42FA8E59592'

class APIInfo(BaseModel):
    title: str = "Itio FinanceAPI API"
    version: str = "0.0.1"


class App(BaseModel):
    show_error_details: bool = True


class Site(BaseModel):
    copyright: str = "Example"


class Settings(BaseSettings):
    # to override info:
    # export app_info='{"title": "x", "version": "0.0.2"}'
    info: APIInfo = APIInfo()

    # to override app:
    # export app_app='{"show_error_details": True}'
    app: App = App()

    model_config = SettingsConfigDict(env_prefix='APP_')


DATABASE_URL = config('DATABASE_URL')

def load_settings() -> Settings:
    return Settings()
