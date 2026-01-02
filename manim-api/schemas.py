from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class VideoQuality(str, Enum):
    LOW = "l"
    MEDIUM = "m"
    HIGH = "h"


class VideoRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Descrição em linguagem natural do vídeo desejado",
    )
    quality: VideoQuality = Field(
        default=VideoQuality.LOW,
        description="Qualidade do vídeo: l=480p, m=720p, h=1080p",
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
