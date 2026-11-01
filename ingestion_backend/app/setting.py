from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str | None = Field(default=None, validation_alias=AliasChoices("REDIS_URL", "REDIS_DB_URL"))
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"
    EMBED_MODEL: str = "gemini-embedding-001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
