#!/usr/bin/env python3
"""Teste visual dos templates determinísticos do render_clip.py.

Renderiza cada um dos 5 templates em 640x360 sem OPENROUTER_API_KEY, extrai o
quadro do meio de cada MP4 e verifica que pelo menos 5% dos pixels são
não-brancos (distância > 30 de 255 em qualquer canal). Falha se algum template
entregar um clipe essencialmente vazio/branco.

Uso:
    python scripts/test_template_visual.py
    # ou, com ambiente virtual:
    manim-api/venv/bin/python scripts/test_template_visual.py

O script retorna código de saída 0 em caso de sucesso.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIM_API = REPO_ROOT / "manim-api"
RENDER_CLIP = REPO_ROOT / "render_clip.py"

TEMPLATES = [
    "circle_growing",
    "ulam_spiral",
    "euclid_prime",
    "bar_chart",
    "number_line",
]
EXPECTED_BACKGROUND = "#FFFFFF"
WIDTH = 640
HEIGHT = 360
FPS = 30
MIN_CONTENT_PERCENT = 5.0
WHITE_THRESHOLD = 30


def _resolve_python() -> str:
    """Prefere o Python do venv, mas aceita o executor atual."""
    venv_python = MANIM_API / "venv" / "bin" / "python"
    if venv_python.exists() and os.access(venv_python, os.X_OK):
        return str(venv_python)
    return sys.executable


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Executa um comando e retorna o resultado; mostra o comando em stderr."""
    print(f"[visual-test] {' '.join(cmd)}", file=sys.stderr)
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def _extract_json(stdout: str) -> dict:
    """Extrai o último bloco JSON válido da saída (logs podem precedê-lo)."""
    text = stdout.strip()
    starts = [i for i, ch in enumerate(text) if ch == "{"]
    ends = [i for i, ch in enumerate(text) if ch == "}"]
    if not starts or not ends:
        raise RuntimeError("Nenhum bloco JSON encontrado na saída")

    for end in reversed(ends):
        for start in starts:
            if start >= end:
                break
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue

    raise RuntimeError("Nenhum bloco JSON válido encontrado na saída")


def render_template(python: str, template: str, out_dir: Path) -> Path:
    """Renderiza um template via render_clip.py sem OPENROUTER_API_KEY."""
    payload = {
        "template": template,
        "background_color": EXPECTED_BACKGROUND,
        "out_dir": str(out_dir),
        "width": WIDTH,
        "height": HEIGHT,
        "fps": FPS,
        "renderer": "cairo",
    }
    cmd = [python, str(RENDER_CLIP), "--json", json.dumps(payload)]
    env = os.environ.copy()
    env.pop("OPENROUTER_API_KEY", None)
    env["PYTHONPATH"] = str(MANIM_API)
    result = _run(cmd, cwd=str(REPO_ROOT), env=env, timeout=300)

    print("[visual-test] stdout:\n" + result.stdout, file=sys.stderr)
    if result.stderr:
        print("[visual-test] stderr:\n" + result.stderr, file=sys.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"render_clip.py falhou para '{template}' com código {result.returncode}"
        )

    response = _extract_json(result.stdout)
    if not response.get("ok"):
        raise RuntimeError(
            f"Resposta indicou falha para '{template}': {response.get('error')}"
        )

    mp4_path = Path(response["mp4"])
    if not mp4_path.exists():
        raise RuntimeError(f"Arquivo MP4 não encontrado para '{template}': {mp4_path}")

    return mp4_path


def extract_middle_frame(mp4_path: Path, frame_path: Path) -> None:
    """Extrai o quadro do meio do MP4 para frame_path usando ffmpeg."""
    probe = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(mp4_path),
        ],
        timeout=15,
    )
    if probe.returncode != 0:
        raise RuntimeError(f"ffprobe falhou: {probe.stderr.strip()}")

    try:
        duration = float(probe.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"não foi possível ler duração do vídeo: {exc}")

    middle = max(0.0, duration / 2.0)
    result = _run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(middle),
            "-i",
            str(mp4_path),
            "-frames:v",
            "1",
            "-q:v",
            "1",
            "-pix_fmt",
            "rgb24",
            str(frame_path),
        ],
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou: {result.stderr.strip()}")


def calculate_content_percentage(frame_path: Path) -> float:
    """Calcula a porcentagem de pixels não-brancos no frame."""
    img = Image.open(frame_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    pixels = list(img.get_flattened_data())
    total = len(pixels)
    if total == 0:
        return 0.0

    non_white = 0
    for r, g, b in pixels:
        if (
            abs(255 - r) > WHITE_THRESHOLD
            or abs(255 - g) > WHITE_THRESHOLD
            or abs(255 - b) > WHITE_THRESHOLD
        ):
            non_white += 1

    return (non_white / total) * 100.0


def main() -> int:
    python = _resolve_python()
    print(f"[visual-test] Usando Python: {python}", file=sys.stderr)

    report: list[dict] = []
    failed: list[str] = []

    with tempfile.TemporaryDirectory(prefix="template_visual_test_") as tmpdir:
        base_dir = Path(tmpdir)

        for template in TEMPLATES:
            print(
                f"\n[visual-test] Renderizando template '{template}'...",
                file=sys.stderr,
            )
            out_dir = base_dir / template
            out_dir.mkdir(parents=True, exist_ok=True)

            mp4_path = render_template(python, template, out_dir)
            frame_path = out_dir / "middle_frame.png"
            extract_middle_frame(mp4_path, frame_path)
            percent = calculate_content_percentage(frame_path)

            report.append({"template": template, "content_percent": round(percent, 2)})
            print(
                f"[visual-test] {template}: {percent:.2f}% de pixels não-brancos",
                file=sys.stderr,
            )

            if percent < MIN_CONTENT_PERCENT:
                failed.append(
                    f"{template}: {percent:.2f}% abaixo do mínimo de {MIN_CONTENT_PERCENT}%"
                )

    print("\n[visual-test] Relatório de conteúdo visual:", file=sys.stderr)
    for entry in report:
        status = "PASS" if entry["content_percent"] >= MIN_CONTENT_PERCENT else "FAIL"
        print(
            f"  {entry['template']}: {entry['content_percent']:.2f}% [{status}]",
            file=sys.stderr,
        )

    if failed:
        print(
            f"\n[visual-test] FALHA: templates com conteúdo insuficiente:\n  - "
            + "\n  - ".join(failed),
            file=sys.stderr,
        )
        return 1

    print("\n[visual-test] Todos os templates possuem conteúdo visível.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"[visual-test] FALHA: {exc}", file=sys.stderr)
        sys.exit(1)
