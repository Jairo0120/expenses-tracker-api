from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    auth0_file_url: str = ""
    auth0_audience: str = ""
    sqlite_database_url: str = ""

    model_config = SettingsConfigDict(env_file=".env")
