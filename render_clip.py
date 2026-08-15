#!/usr/bin/env python3
"""CLI para renderizar um clipe Manim com fundo casado ao slide.

Lê JSON do stdin ou de --json, gera código Manim, renderiza e valida o fundo.
Saída em stdout: JSON puro. Logs em stderr.
"""

import argparse
import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Adiciona manim-api ao path para reutilizar serviços internos
REPO_ROOT = Path(__file__).resolve().parent
MANIM_API = REPO_ROOT / "manim-api"
if str(MANIM_API) not in sys.path:
    sys.path.insert(0, str(MANIM_API))

from config import get_settings  # noqa: E402
from schemas import ClipRequest, ClipResponse, BackgroundValidation  # noqa: E402
from services.openrouter_service import generate_manim_code  # noqa: E402
from services.manim_executor import execute_manim  # noqa: E402
from templates import get_template, list_templates  # noqa: E402
from template_registry import resolve_by_prompt  # noqa: E402

logger = logging.getLogger("render_clip")

EXIT_SUCCESS = 0
EXIT_GENERATION_FAILED = 1
EXIT_CONFIG_ERROR = 2
EXIT_RENDER_FAILED = 3
EXIT_BACKGROUND_MISMATCH = 4


def _fail_response(message: str, exit_code: int) -> int:
    response = ClipResponse(ok=False, error=message)
    print(response.model_dump_json(indent=2))
    return exit_code


def _resolve_out_dir(out_dir: str | None) -> Path:
    if out_dir:
        path = Path(out_dir).resolve()
    else:
        path = (Path.cwd() / "clips").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _find_manim() -> str:
    venv_manim = Path(sys.executable).with_name("manim")
    if venv_manim.exists() and os.access(venv_manim, os.X_OK):
        return str(venv_manim)
    manim = shutil.which("manim")
    if manim:
        return manim
    raise RuntimeError("Executável manim não encontrado no venv nem no PATH")


def _run_assert_bg(mp4_path: Path, expected_hex: str, repo_root: Path) -> dict:
    assert_bg = repo_root / "manim-api" / "scripts" / "assert_bg.py"
    if not assert_bg.exists():
        raise RuntimeError(f"assert_bg.py não encontrado em {assert_bg}")
    result = subprocess.run(
        [sys.executable, str(assert_bg), str(mp4_path), "--expect", expected_hex],
        capture_output=True,
        text=True,
        timeout=60,
    )
    data = json.loads(result.stdout or "{}")
    data["exit_code"] = result.returncode
    return data


def _video_duration(mp4_path: Path) -> float:
    result = subprocess.run(
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
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return 0.0
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


async def _render_clip(payload: dict) -> int:
    start_ms = int(time.time() * 1000)

    try:
        request = ClipRequest(**payload)
    except Exception as exc:  # noqa: BLE001
        return _fail_response(f"Erro de configuração: {exc}", EXIT_CONFIG_ERROR)

    try:
        settings = get_settings()
    except Exception as exc:  # noqa: BLE001
        return _fail_response(
            f"Erro ao carregar configurações: {exc}",
            EXIT_CONFIG_ERROR,
        )

    width = request.width or 1280
    height = request.height or 720
    fps = request.fps or settings.default_fps or 30
    expected_hex = request.background_color or "#FFFFFF"
    out_dir = _resolve_out_dir(request.out_dir)

    # Decide entre template determinístico e geração via LLM
    template_cls = None
    template_source = None
    if request.template:
        try:
            template_cls = get_template(request.template)
            template_source = f"template:{request.template}"
        except KeyError as exc:
            available = ", ".join(list_templates())
            return _fail_response(
                f"Template não encontrado: {exc}. Disponíveis: {available}",
                EXIT_CONFIG_ERROR,
            )
    elif not settings.openrouter_api_key and request.prompt:
        resolved = resolve_by_prompt(request.prompt)
        if resolved is not None:
            template_cls = resolved
            template_source = f"auto-detected:{resolved.name}"

    if template_cls is not None:
        scene_name, code = template_cls.render(
            width=width,
            height=height,
            background_color=expected_hex,
            fps=fps,
        )
    elif request.prompt:
        if not settings.openrouter_api_key:
            return _fail_response(
                "OPENROUTER_API_KEY não configurada. Defina a variável de ambiente "
                "ou use um template determinístico.",
                EXIT_CONFIG_ERROR,
            )

        code_response = await generate_manim_code(
            description=request.prompt,
            width=width,
            height=height,
            request_id="clip-cli",
        )
        if not code_response.is_valid or not code_response.code:
            return _fail_response(
                f"Geração de código falhou: {code_response.validation_message}",
                EXIT_GENERATION_FAILED,
            )
        scene_name = code_response.scene_name
        code = code_response.code
    else:
        return _fail_response(
            "Forneça 'prompt' ou 'template' para renderizar o clipe.",
            EXIT_CONFIG_ERROR,
        )

    # Renderização
    mp4_name = f"{scene_name}.mp4"
    dest_path = out_dir / mp4_name

    render_result = execute_manim(
        code=code,
        scene_name=scene_name,
        width=width,
        height=height,
        timeout=settings.render_timeout,
        request_id="clip-cli",
        background_color=expected_hex,
        fps=fps,
        quality=request.quality,
        renderer_override=request.renderer,
        output_path=dest_path,
    )

    if not render_result.success or not render_result.video_path:
        return _fail_response(
            f"Render falhou: {render_result.error or 'unknown error'}",
            EXIT_RENDER_FAILED,
        )

    # Validação de fundo
    assert_data = _run_assert_bg(dest_path, expected_hex, REPO_ROOT)
    if assert_data.get("exit_code") != 0 or not assert_data.get("passed"):
        return _fail_response(
            f"Fundo fora da tolerância: desvio={assert_data.get('max_deviation')}, "
            f"uniformidade={assert_data.get('uniformity')}%",
            EXIT_BACKGROUND_MISMATCH,
        )

    duration_s = _video_duration(dest_path)
    elapsed_ms = int(time.time() * 1000) - start_ms

    response = ClipResponse(
        ok=True,
        mp4=str(dest_path),
        scene=scene_name,
        renderer=render_result.renderer or assert_data.get("renderer", "unknown"),
        background=BackgroundValidation(
            pedido=expected_hex,
            obtido=assert_data.get("dominant", {}).get("hex", "").upper(),
            desvio=assert_data.get("max_deviation", -1),
            uniformidade=assert_data.get("uniformity", 0.0),
        ),
        duracao_s=duration_s,
        ms=elapsed_ms,
    )
    if template_source:
        response_dict = response.model_dump()
        response_dict["template"] = template_source
        print(json.dumps(response_dict, indent=2))
    else:
        print(response.model_dump_json(indent=2))
    return EXIT_SUCCESS


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(name)s] %(message)s",
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description="Renderiza um clipe Manim com fundo casado.")
    parser.add_argument(
        "--json",
        dest="json_input",
        default=None,
        help='JSON com os campos do ClipRequest (ex.: {"prompt":"..."})',
    )
    args = parser.parse_args()

    if args.json_input:
        raw = args.json_input
    else:
        try:
            raw = sys.stdin.read()
        except KeyboardInterrupt:
            return _fail_response("Entrada interrompida", EXIT_CONFIG_ERROR)

    if not raw.strip():
        return _fail_response("JSON de entrada vazio", EXIT_CONFIG_ERROR)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return _fail_response(f"JSON inválido: {exc}", EXIT_CONFIG_ERROR)

    return asyncio.run(_render_clip(payload))


if __name__ == "__main__":
    sys.exit(main())
