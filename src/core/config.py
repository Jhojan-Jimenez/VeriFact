from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "VeriFact"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # SQLite WAL Database configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///verifact.db"

    # Anti-fraud and verification tolerances
    RECEIPT_TIME_TOLERANCE_MINUTES: int = 30

    # Debug / Logging
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
