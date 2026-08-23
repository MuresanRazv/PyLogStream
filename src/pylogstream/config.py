from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from pylogstream.constants import DEFAULT_LINES_TO_GENERATE, DEFAULT_OUTPUT_PATH


class Settings(BaseSettings):
    app_env: str = "development"
    log_output_dir: Path = Path("data")
    batch_size: int = 50_000
    brute_force_threshold: int = 25
    rate_limit_per_window: int = 500
    default_lines_to_generate: int = DEFAULT_LINES_TO_GENERATE
    default_output_path: str = DEFAULT_OUTPUT_PATH

    # Auto-read .env file, prioritize system environment variables
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton instance of Settings."""
    return Settings()
