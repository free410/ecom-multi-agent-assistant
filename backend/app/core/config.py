from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = ROOT_DIR / ".env"
FALLBACK_ENV_FILE = ROOT_DIR / ".env.example"
ENV_FILE = DEFAULT_ENV_FILE if DEFAULT_ENV_FILE.exists() else FALLBACK_ENV_FILE


class Settings(BaseSettings):
    app_name: str = "多 Agent 电商运营智能助手平台"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    mysql_url: str | None = None
    redis_url: str | None = None
    default_provider: Literal["qwen", "deepseek", "mock"] = "mock"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    qwen_api_key: str | None = None
    qwen_base_url: str | None = None
    qwen_model: str = "qwen-plus"
    llm_connect_timeout_seconds: float = 15.0
    llm_read_timeout_seconds: float = 90.0
    llm_write_timeout_seconds: float = 30.0
    llm_pool_timeout_seconds: float = 30.0
    llm_max_retries: int = 1

    deepseek_api_key: str | None = None
    deepseek_base_url: str | None = None
    deepseek_model: str = "deepseek-chat"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def seed_dir(self) -> Path:
        return ROOT_DIR / "backend" / "app" / "seed"


@lru_cache
def get_settings() -> Settings:
    return Settings()
