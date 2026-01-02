from typing import Optional
from pydantic import BaseModel, Field


class VideoRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Descrição em linguagem natural do vídeo desejado",
    )
    width: int | None = Field(
        default=None,
        ge=320,
        le=3840,
        description="(Opcional) Largura do vídeo em pixels; padrão 1920",
    )
    height: int | None = Field(
        default=None,
        ge=320,
        le=3840,
        description="(Opcional) Altura do vídeo em pixels; padrão 1080",
    )


class CodeResponse(BaseModel):
    code: str
    scene_name: str
    is_valid: bool
    validation_message: str


class VideoResponse(BaseModel):
    success: bool
    video_base64: Optional[str] = None
    content_type: str = "video/mp4"
    scene_name: Optional[str] = None
    error: Optional[str] = None
    render_logs: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    manim_version: str
    openai_model: str
