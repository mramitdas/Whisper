from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str
    owner_id: int

    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+asyncpg://bot:bot@localhost:5432/anonbot"

    match_timeout_sec: int = 60
    idle_timeout_sec: int = 1800
    session_ttl_sec: int = 86400
    lastpartner_ttl_sec: int = 3600
    max_reports_ban: int = 5

    msg_rate_max: int = 5
    msg_rate_window: float = 2.0
    search_rate_max: int = 1
    search_rate_window: float = 3.0

    match_window: int = 50
    forbidden_words: list[str] = []
