from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/tenders.db"
    request_timeout_seconds: int = 20
    request_delay_seconds: float = 1.5
    user_agent: str = "TenderCrawlerAgent/0.1"
    api_token: str = "change-me"
    dify_base_url: str = "http://127.0.0.1"
    dify_api_key: str = ""
    dify_dataset_id: str = ""
    dify_app_api_key: str = ""
    dify_app_endpoint: str = "/v1/chat-messages"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
