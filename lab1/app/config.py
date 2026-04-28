from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://smartbook:smartbook123@localhost:5432/smartbook_db"
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    LOW_STOCK_THRESHOLD: int = 3  # поріг для автоматичного дозамовлення (lab4+)

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
