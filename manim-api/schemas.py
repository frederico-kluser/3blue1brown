import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _validate_hex_color(value: str | None) -> str | None:
    if value is None:
        return value
    if not _HEX_COLOR_RE.match(value):
        raise ValueError(f"background_color deve ser hex de 6 dígitos (ex.: #FFFFFF); recebido: {value!r}")
    return value.upper()


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
    background_color: str | None = Field(
        default="#FFFFFF",
        description="Cor de fundo do clipe em hex de 6 dígitos; padrão #FFFFFF",
    )
    fps: int | None = Field(
        default=30,
        ge=15,
        le=60,
        description="Frames por segundo; padrão 30",
    )
    quality: str | None = Field(
        default=None,
        pattern=r"^(l|m|h|p|k)$",
        description="Qualidade Manim (l/m/h/p/k); opcional",
    )
    renderer: str | None = Field(
        default="auto",
        description="Renderizador (auto/cairo/opengl); padrão auto",
    )
    out_dir: str | None = Field(
        default=None,
        description="Diretório de saída opcional para salvar o MP4",
    )

    _validate_background_color = field_validator("background_color", mode="before")(_validate_hex_color)


class ClipRequest(VideoRequest):
    """Request específico para renderização de clipe via CLI/subprocesso."""

    description: str | None = Field(
        default=None,
        min_length=10,
        max_length=2000,
        description="Compatibilidade com VideoRequest; não usado pela CLI",
    )
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Descrição em linguagem natural do clipe desejado",
    )
    width: int | None = Field(
        default=1280,
        ge=120,
        le=3840,
        description="Largura do clipe em pixels; padrão 1280",
    )
    height: int | None = Field(
        default=720,
        ge=120,
        le=3840,
        description="Altura do clipe em pixels; padrão 720",
    )

    @field_validator("renderer", mode="before")
    @classmethod
    def _validate_renderer(cls, value: str | None) -> str:
        allowed = {"auto", "cairo", "opengl"}
        value = (value or "auto").strip().lower()
        if value not in allowed:
            raise ValueError(f"renderer deve ser um de {allowed}; recebido: {value!r}")
        return value


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


class BackgroundValidation(BaseModel):
    pedido: str
    obtido: str
    desvio: int
    uniformidade: float


class ClipResponse(BaseModel):
    ok: bool
    mp4: Optional[str] = None
    scene: Optional[str] = None
    renderer: Optional[str] = None
    background: Optional[BackgroundValidation] = None
    duracao_s: Optional[float] = None
    ms: Optional[int] = None
    error: Optional[str] = None
