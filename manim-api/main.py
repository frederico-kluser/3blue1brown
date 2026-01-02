import asyncio
import base64
import logging
import subprocess
import time
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from config import get_settings
from schemas import CodeResponse, HealthResponse, VideoRequest, VideoResponse
from services.manim_executor import execute_manim
from services.openai_service import generate_manim_code

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
)
logger = logging.getLogger("manim_api.app")

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API para gerar vídeos Manim via descrições em linguagem natural",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r".*",
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def ensure_cors_headers(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:8]
    request.state.request_id = request_id
    start = time.perf_counter()
    logger.info("[%s] Incoming %s %s", request_id, request.method, request.url.path)

    if request.method == "OPTIONS":
        response = Response(status_code=200, content="OK")
    else:
        response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000
    origin = request.headers.get("origin") or "*"
    response.headers["Access-Control-Allow-Origin"] = "*" if origin == "*" else origin
    response.headers.setdefault("Vary", "Origin")
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    requested_headers = request.headers.get("access-control-request-headers") or "*"
    response.headers["Access-Control-Allow-Headers"] = requested_headers
    response.headers.setdefault("Access-Control-Max-Age", "600")
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "[%s] Completed %s %s -> %s (%.2f ms)",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


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


def _resolve_dimensions(request: VideoRequest) -> tuple[int, int]:
    width = request.width or 1920
    height = request.height or 1080
    return width, height


def _request_id(http_request: Request) -> str:
    return getattr(http_request.state, "request_id", None) or uuid.uuid4().hex[:8]


@app.post("/generate-code", response_model=CodeResponse)
async def generate_code(payload: VideoRequest, http_request: Request) -> CodeResponse:
    request_id = _request_id(http_request)
    width, height = _resolve_dimensions(payload)
    logger.info(
        "[%s] /generate-code request received (resolution=%dx%d)",
        request_id,
        width,
        height,
    )
    result = await generate_manim_code(
        description=payload.description,
        width=width,
        height=height,
        request_id=request_id,
    )
    logger.info("[%s] /generate-code completed (valid=%s)", request_id, result.is_valid)
    return result


@app.post("/generate-video", response_model=VideoResponse)
async def generate_video(payload: VideoRequest, http_request: Request) -> VideoResponse:
    request_id = _request_id(http_request)
    width, height = _resolve_dimensions(payload)
    logger.info(
        "[%s] /generate-video request received (resolution=%dx%d)",
        request_id,
        width,
        height,
    )
    code_result = await generate_manim_code(
        description=payload.description,
        width=width,
        height=height,
        request_id=request_id,
    )
    if not code_result.is_valid:
        logger.warning(
            "[%s] Code generation failed: %s",
            request_id,
            code_result.validation_message,
        )
        return VideoResponse(
            success=False,
            error=f"Code generation failed: {code_result.validation_message}",
        )

    logger.info(
        "[%s] Code generated successfully (scene=%s), starting render",
        request_id,
        code_result.scene_name,
    )

    render_result = await asyncio.to_thread(
        execute_manim,
        code_result.code,
        code_result.scene_name,
        width,
        height,
        settings.render_timeout,
        request_id,
    )

    if not render_result.success:
        logger.error(
            "[%s] Render failed: %s",
            request_id,
            render_result.error,
        )
        if render_result.stderr:
            logger.error("[%s] Render stderr: %s", request_id, render_result.stderr.strip())
        if render_result.stdout:
            logger.error("[%s] Render stdout: %s", request_id, render_result.stdout.strip())
        return VideoResponse(
            success=False,
            error=render_result.error,
            render_logs=render_result.stderr,
        )

    logger.info("[%s] Render completed successfully", request_id)
    return VideoResponse(
        success=True,
        video_base64=render_result.video_base64,
        scene_name=code_result.scene_name,
    )


@app.post("/generate-video-file")
async def generate_video_file(payload: VideoRequest, http_request: Request) -> Response:
    request_id = _request_id(http_request)
    width, height = _resolve_dimensions(payload)
    logger.info(
        "[%s] /generate-video-file request received (resolution=%dx%d)",
        request_id,
        width,
        height,
    )
    code_result = await generate_manim_code(
        description=payload.description,
        width=width,
        height=height,
        request_id=request_id,
    )
    if not code_result.is_valid:
        logger.warning(
            "[%s] Code generation failed for /generate-video-file: %s",
            request_id,
            code_result.validation_message,
        )
        raise HTTPException(
            status_code=400,
            detail=f"Code generation failed: {code_result.validation_message}",
        )

    render_result = await asyncio.to_thread(
        execute_manim,
        code_result.code,
        code_result.scene_name,
        width,
        height,
        settings.render_timeout,
        request_id,
    )

    if not render_result.success:
        logger.error(
            "[%s] Render failed for /generate-video-file: %s",
            request_id,
            render_result.error,
        )
        if render_result.stderr:
            logger.error("[%s] Render stderr: %s", request_id, render_result.stderr.strip())
        if render_result.stdout:
            logger.error("[%s] Render stdout: %s", request_id, render_result.stdout.strip())
        raise HTTPException(
            status_code=500,
            detail=f"Render failed: {render_result.error}\n{render_result.stderr}",
        )

    logger.info("[%s] /generate-video-file render completed", request_id)
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
