import base64
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import get_settings

settings = get_settings()


@dataclass
class RenderResult:
    success: bool
    video_path: Optional[str] = None
    video_base64: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None


def find_video(media_dir: Path, scene_name: str, quality: str) -> Optional[Path]:
    """Encontra o vídeo MP4 gerado pelo Manim."""
    quality_dirs = {
        "l": "480p15",
        "m": "720p30",
        "h": "1080p60",
        "k": "2160p60",
    }

    quality_folder = quality_dirs.get(quality, "480p15")
    expected = media_dir / "videos" / "scene" / quality_folder / f"{scene_name}.mp4"
    if expected.exists():
        return expected

    for mp4 in media_dir.rglob("*.mp4"):
        if scene_name in mp4.name:
            return mp4
    return None


def execute_manim(code: str, scene_name: str, quality: str = "l", timeout: int = 120) -> RenderResult:
    with tempfile.TemporaryDirectory(prefix="manim_") as tmpdir:
        work_dir = Path(tmpdir)
        script_path = work_dir / "scene.py"
        media_dir = work_dir / "media"
        script_path.write_text(code)

        cmd = [
            "manim",
            "render",
            f"-q{quality}",
            "--media_dir",
            str(media_dir),
            "--disable_caching",
            str(script_path),
            scene_name,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(work_dir),
            )
        except subprocess.TimeoutExpired as exc:
            return RenderResult(
                success=False,
                error=f"Render timeout after {timeout} seconds",
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
            )
        except Exception as exc:
            return RenderResult(success=False, error=f"Subprocess error: {exc}")

        if result.returncode != 0:
            return RenderResult(
                success=False,
                error="Manim render failed",
                stdout=result.stdout,
                stderr=result.stderr,
            )

        video_path = find_video(media_dir, scene_name, quality)
        if not video_path:
            return RenderResult(
                success=False,
                error="Video file not found after render",
                stdout=result.stdout,
                stderr=result.stderr,
            )

        video_b64 = base64.b64encode(video_path.read_bytes()).decode("utf-8")
        return RenderResult(
            success=True,
            video_path=str(video_path),
            video_base64=video_b64,
            stdout=result.stdout,
            stderr=result.stderr,
        )
