import json
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    forbidden_words: Annotated[list[str], NoDecode] = []

    @field_validator("forbidden_words", mode="before")
    @classmethod
    def _parse_forbidden_words(cls, v):
        """Accept comma-separated or JSON list spellings in .env."""
        if v is None or v == "":
            return []
        if isinstance(v, str):
            stripped = v.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
            return [w.strip() for w in stripped.split(",") if w.strip()]
        return v
