import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

class DatabaseSettings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


database_url = os.getenv("DATABASE_URL") or DatabaseSettings().database_url
if not database_url:
    raise RuntimeError("DATABASE_URL is not configured")

engine_options = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "pool_size": 5,
    "max_overflow": 10,
}
if database_url.startswith("postgresql"):
    engine_options["connect_args"] = {"sslmode": "require"}

engine = create_engine(database_url, **engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()