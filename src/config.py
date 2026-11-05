from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    SQL_ECHO: bool = False
    DEMO_CUSTOMER_ID: int = 1
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4.1-mini"
    CHAT_RATE_LIMIT_REQUESTS: int = 10
    CHAT_RATE_LIMIT_WINDOW_SECONDS: int = 60
    CHAT_REQUEST_MAX_AGE_SECONDS: int = 60
    CHAT_DAILY_LIMIT_TOTAL: int = 500
    CHAT_DAILY_LIMIT_PER_IP: int = 50
    CHAT_MAX_OUTPUT_TOKENS: int = 500
    CHAT_HISTORY_TURNS: int = 6
    READ_RATE_LIMIT_REQUESTS: int = 120
    READ_RATE_LIMIT_WINDOW_SECONDS: int = 60
    SESSION_RATE_LIMIT_REQUESTS: int = 10
    SESSION_RATE_LIMIT_WINDOW_SECONDS: int = 60
    SESSION_NOTICE_INTERVAL_SECONDS: int = 1800
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_API_BASE_URL: str = "https://api.telegram.org"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()