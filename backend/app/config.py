"""Application configuration loaded from .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CoffeeTree API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/coffeetree"

    # JWT
    SECRET_KEY: str = "change-me-run-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Superuser auto-seed
    ADMIN_EMAIL: str = "admin@coffeetree.vn"
    ADMIN_PASSWORD: str = "admin123"

    # Register control
    ALLOW_PUBLIC_REGISTER: bool = False

    # Frontend URL (for email links)
    FRONTEND_URL: str = "http://localhost:3000"

    # Email SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_TLS: bool = True
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@coffeetree.vn"

    # Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
