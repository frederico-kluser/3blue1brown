#!/usr/bin/env python3
"""Teste rápido do modo determinístico de templates do render_clip.py.

1. Lista os templates disponíveis.
2. Renderiza um template sem OPENROUTER_API_KEY.
3. Valida o fundo branco do MP4 gerado.

Uso:
    python scripts/test_template_cli.py
    # ou, com ambiente virtual:
    manim-api/venv/bin/python scripts/test_template_cli.py

O script retorna código de saída 0 em caso de sucesso.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIM_API = REPO_ROOT / "manim-api"
RENDER_CLIP = REPO_ROOT / "render_clip.py"
ASSERT_BG = MANIM_API / "scripts" / "assert_bg.py"

TEMPLATE_TO_RENDER = "circle_growing"
EXPECTED_BACKGROUND = "#FFFFFF"


def _resolve_python() -> str:
    """Prefere o Python do venv, mas aceita o executor atual."""
    venv_python = MANIM_API / "venv" / "bin" / "python"
    if venv_python.exists() and os.access(venv_python, os.X_OK):
        return str(venv_python)
    return sys.executable


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Executa um comando e retorna o resultado; mostra o comando em stderr."""
    print(f"[test] {' '.join(cmd)}", file=sys.stderr)
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def list_templates(python: str) -> list[str]:
    """Lista templates via pacote templates."""
    cmd = [
        python,
        "-c",
        "import json; from templates import list_templates; print(json.dumps(list_templates()))",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(MANIM_API)
    result = _run(cmd, cwd=str(REPO_ROOT), env=env)
    if result.returncode != 0:
        raise RuntimeError(f"Falha ao listar templates: {result.stderr}")
    # Saída esperada: ['bar_chart', 'circle_growing', ...]
    return json.loads(result.stdout.strip())


def render_template(python: str, template: str, out_dir: Path) -> dict:
    """Renderiza um template via render_clip.py sem OPENROUTER_API_KEY."""
    payload = {
        "template": template,
        "background_color": EXPECTED_BACKGROUND,
        "out_dir": str(out_dir),
        "width": 640,
        "height": 360,
        "fps": 30,
        "renderer": "cairo",
    }
    cmd = [python, str(RENDER_CLIP), "--json", json.dumps(payload)]
    env = os.environ.copy()
    env.pop("OPENROUTER_API_KEY", None)
    env["PYTHONPATH"] = str(MANIM_API)
    result = _run(cmd, cwd=str(REPO_ROOT), env=env, timeout=300)

    print("[test] stdout:\n" + result.stdout, file=sys.stderr)
    if result.stderr:
        print("[test] stderr:\n" + result.stderr, file=sys.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"render_clip.py falhou com código {result.returncode}")

    return _extract_json(result.stdout)


def _extract_json(stdout: str) -> dict:
    """Extrai o último bloco JSON válido da saída (logs podem precedê-lo)."""
    text = stdout.strip()
    starts = [i for i, ch in enumerate(text) if ch == "{"]
    ends = [i for i, ch in enumerate(text) if ch == "}"]
    if not starts or not ends:
        raise RuntimeError("Nenhum bloco JSON encontrado na saída")

    # Procura pelo bloco válido que termina mais tarde; dentro dele, pega a
    # abertura mais externa (primeiro '{' antes do '}' de fechamento).
    for end in reversed(ends):
        for start in starts:
            if start >= end:
                break
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue

    raise RuntimeError("Nenhum bloco JSON válido encontrado na saída")


def validate_background(python: str, mp4_path: Path) -> dict:
    """Roda assert_bg.py no vídeo gerado."""
    cmd = [python, str(ASSERT_BG), str(mp4_path), "--expect", EXPECTED_BACKGROUND]
    result = _run(cmd, cwd=str(REPO_ROOT), timeout=120)
    print("[test] assert_bg stdout:\n" + result.stdout, file=sys.stderr)
    if result.stderr:
        print("[test] assert_bg stderr:\n" + result.stderr, file=sys.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"Validação de fundo falhou com código {result.returncode}")

    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Saída de assert_bg não é JSON válido: {exc}") from exc


def main() -> int:
    python = _resolve_python()
    print(f"[test] Usando Python: {python}", file=sys.stderr)

    # 1. Listar templates
    print("\n[test] 1. Listando templates disponíveis...", file=sys.stderr)
    templates = list_templates(python)
    expected_templates = {
        "circle_growing",
        "ulam_spiral",
        "euclid_prime",
        "bar_chart",
        "number_line",
    }
    missing = expected_templates - set(templates)
    if missing:
        raise RuntimeError(f"Templates esperados não encontrados: {missing}")
    print(f"[test] Templates encontrados: {templates}", file=sys.stderr)

    # 2. Renderizar um template sem OPENROUTER_API_KEY
    print(f"\n[test] 2. Renderizando template '{TEMPLATE_TO_RENDER}' sem API key...", file=sys.stderr)
    with tempfile.TemporaryDirectory(prefix="template_cli_test_") as tmpdir:
        out_dir = Path(tmpdir)
        response = render_template(python, TEMPLATE_TO_RENDER, out_dir)

        if not response.get("ok"):
            raise RuntimeError(f"Resposta indicou falha: {response.get('error')}")

        mp4_path = Path(response["mp4"])
        if not mp4_path.exists():
            raise RuntimeError(f"Arquivo MP4 não encontrado: {mp4_path}")

        template_source = response.get("template", "")
        if not template_source.startswith(f"template:{TEMPLATE_TO_RENDER}"):
            raise RuntimeError(f"Esperava template:{TEMPLATE_TO_RENDER}, obteve: {template_source}")

        print(f"[test] MP4 gerado: {mp4_path}", file=sys.stderr)
        print(f"[test] Duração: {response.get('duracao_s')}s", file=sys.stderr)

        # 3. Validar fundo branco
        print("\n[test] 3. Validando fundo branco...", file=sys.stderr)
        bg_report = validate_background(python, mp4_path)
        if not bg_report.get("passed"):
            raise RuntimeError(f"Fundo não passou na validação: {bg_report}")

        print(f"[test] Fundo validado: {bg_report.get('dominant', {}).get('hex')}", file=sys.stderr)

    print("\n[test] Todos os passos passaram.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"[test] FALHA: {exc}", file=sys.stderr)
        sys.exit(1)
