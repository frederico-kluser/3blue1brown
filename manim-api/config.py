from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenRouter
    openrouter_api_key: str
    openrouter_model: str = "deepseek/deepseek-v4-pro"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # App
    app_name: str = "Manim Video Generator API"
    debug: bool = False

    # Manim
    render_timeout: int = 120
    manim_renderer: str = "auto"
    manim_renderer_fallback: bool = True
    default_fps: int = 30

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
