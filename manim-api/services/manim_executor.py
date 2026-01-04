import base64
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import get_settings

settings = get_settings()
logger = logging.getLogger("manim_api.manim_executor")


def _resolve_texlive_bin() -> Optional[Path]:
    texlive_root = Path.home() / "texlive"
    if not texlive_root.exists():
        return None
    candidates = sorted(texlive_root.glob("*/bin/*"), reverse=True)
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


TEXLIVE_BIN = _resolve_texlive_bin()

BACKGROUND_RECTANGLE_PATCH = """
from manim.mobject.geometry.shape_matchers import BackgroundRectangle

if not hasattr(BackgroundRectangle, "tex_string"):
    BackgroundRectangle.tex_string = ""
"""


@dataclass
class RenderResult:
    success: bool
    video_path: Optional[str] = None
    video_base64: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None


def find_video(media_dir: Path, scene_name: str) -> Optional[Path]:
    """Encontra o vídeo MP4 gerado pelo Manim independente da pasta de qualidade."""
    expected_root = media_dir / "videos"
    candidates = sorted(
        expected_root.rglob("*.mp4") if expected_root.exists() else media_dir.rglob("*.mp4"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for mp4 in candidates:
        if scene_name in mp4.stem:
            return mp4
    return candidates[0] if candidates else None


def _build_env() -> dict:
    env = os.environ.copy()
    if TEXLIVE_BIN and TEXLIVE_BIN.exists():
        current_path = env.get("PATH", "")
        env["PATH"] = f"{TEXLIVE_BIN}:{current_path}" if current_path else str(TEXLIVE_BIN)
    return env


def execute_manim(
    code: str,
    scene_name: str,
    width: int = 1920,
    height: int = 1080,
    timeout: int = 120,
    request_id: str | None = None,
) -> RenderResult:
    rid = request_id or "no-request-id"
    logger.info(
        "[%s] Starting Manim render (scene=%s, resolution=%dx%d, timeout=%ss)",
        rid,
        scene_name,
        width,
        height,
        timeout,
    )
    with tempfile.TemporaryDirectory(prefix="manim_") as tmpdir:
        work_dir = Path(tmpdir)
        script_path = work_dir / "scene.py"
        media_dir = work_dir / "media"
        script_path.write_text(f"{BACKGROUND_RECTANGLE_PATCH}\n\n{code}")
        logger.debug("[%s] Scene script written to %s", rid, script_path)

        cmd = [
            "manim",
            "render",
            "-r",
            f"{width},{height}",
            "--fps",
            "60",
            "--media_dir",
            str(media_dir),
            "--disable_caching",
            str(script_path),
            scene_name,
        ]
        logger.info("[%s] Executing command: %s", rid, " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(work_dir),
                env=_build_env(),
            )
        except subprocess.TimeoutExpired as exc:
            logger.error("[%s] Render timeout after %s seconds", rid, timeout)
            return RenderResult(
                success=False,
                error=f"Render timeout after {timeout} seconds",
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
            )
        except Exception as exc:
            logger.exception("[%s] Subprocess execution error", rid)
            return RenderResult(success=False, error=f"Subprocess error: {exc}")

        if result.returncode != 0:
            logger.error("[%s] Manim CLI exited with code %s", rid, result.returncode)
            return RenderResult(
                success=False,
                error="Manim render failed",
                stdout=result.stdout,
                stderr=result.stderr,
            )

        video_path = find_video(media_dir, scene_name)
        if not video_path:
            logger.error("[%s] Video file not found after render", rid)
            return RenderResult(
                success=False,
                error="Video file not found after render",
                stdout=result.stdout,
                stderr=result.stderr,
            )

        video_b64 = base64.b64encode(video_path.read_bytes()).decode("utf-8")
        logger.info("[%s] Render finished successfully (video=%s)", rid, video_path)
        return RenderResult(
            success=True,
            video_path=str(video_path),
            video_base64=video_b64,
            stdout=result.stdout,
            stderr=result.stderr,
        )
