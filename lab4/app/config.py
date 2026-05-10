from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./smartbook.db"
    test_database_url: str = "sqlite+aiosqlite://"
    secret_key: str = "super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    communication_mode: str = "async"  # "sync" or "async"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
