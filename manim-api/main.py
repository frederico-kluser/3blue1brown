import base64
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from config import get_settings
from schemas import CodeResponse, HealthResponse, VideoRequest, VideoResponse
from services.manim_executor import execute_manim
from services.openai_service import generate_manim_code

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API para gerar vídeos Manim via descrições em linguagem natural",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def health() -> HealthResponse:
    try:
        result = subprocess.run(
            ["manim", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        manim_version = result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        manim_version = "error"

    return HealthResponse(
        status="healthy",
        manim_version=manim_version,
        openai_model=settings.openai_model,
    )


@app.post("/generate-code", response_model=CodeResponse)
async def generate_code(request: VideoRequest) -> CodeResponse:
    return await generate_manim_code(request.description)


@app.post("/generate-video", response_model=VideoResponse)
async def generate_video(request: VideoRequest) -> VideoResponse:
    code_result = await generate_manim_code(request.description)
    if not code_result.is_valid:
        return VideoResponse(
            success=False,
            error=f"Code generation failed: {code_result.validation_message}",
        )

    render_result = execute_manim(
        code=code_result.code,
        scene_name=code_result.scene_name,
        quality=request.quality.value,
        timeout=settings.render_timeout,
    )

    if not render_result.success:
        return VideoResponse(
            success=False,
            error=render_result.error,
            render_logs=render_result.stderr,
        )

    return VideoResponse(
        success=True,
        video_base64=render_result.video_base64,
        scene_name=code_result.scene_name,
    )


@app.post("/generate-video-file")
async def generate_video_file(request: VideoRequest) -> Response:
    code_result = await generate_manim_code(request.description)
    if not code_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Code generation failed: {code_result.validation_message}",
        )

    render_result = execute_manim(
        code=code_result.code,
        scene_name=code_result.scene_name,
        quality=request.quality.value,
        timeout=settings.render_timeout,
    )

    if not render_result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Render failed: {render_result.error}\n{render_result.stderr}",
        )

    video_bytes = base64.b64decode(render_result.video_base64)
    return Response(
        content=video_bytes,
        media_type="video/mp4",
        headers={
            "Content-Disposition": f'attachment; filename="{code_result.scene_name}.mp4"',
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
