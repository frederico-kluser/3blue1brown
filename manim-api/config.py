from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # App
    app_name: str = "Manim Video Generator API"
    debug: bool = False

    # Manim
    manim_quality: str = "l"  # l, m, h, k
    render_timeout: int = 120

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
