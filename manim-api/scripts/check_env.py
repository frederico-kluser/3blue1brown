#!/usr/bin/env python3
"""Verifica o ambiente de renderização Manim e reporta em JSON.

Saída 0 se todos os componentes essenciais estiverem presentes.
Saída 1 se algum componente essencial estiver ausente.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _find_manim() -> str | None:
    """Resolve o executável manim, preferindo o venv ativo."""
    venv_manim = Path(sys.executable).with_name("manim")
    if venv_manim.exists() and os.access(venv_manim, os.X_OK):
        return str(venv_manim)
    return shutil.which("manim")


def _manim_version() -> str:
    manim_bin = _find_manim()
    if not manim_bin:
        return "não encontrado"
    try:
        result = subprocess.run(
            [manim_bin, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip().splitlines()[0].strip()
    except Exception as exc:  # noqa: BLE001
        return f"erro: {exc}"
    return "não encontrado"


def _ffmpeg_version() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return "não encontrado"
    try:
        result = subprocess.run(
            [ffmpeg, "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.splitlines()[0].strip()
    except Exception as exc:  # noqa: BLE001
        return f"erro: {exc}"
    return "não encontrado"


def _resolve_dvisvgm() -> str:
    """Procura dvisvgm em ~/texlive/*/bin/* e em ~/.TinyTeX/bin/**/*."""
    home = Path.home()
    candidates: list[Path] = []

    texlive_root = home / "texlive"
    if texlive_root.exists():
        candidates.extend(sorted(texlive_root.glob("*/bin/*"), reverse=True))

    tinytex_root = home / ".TinyTeX" / "bin"
    if tinytex_root.exists():
        # TinyTeX organiza arquiteturas em subpastas de bin/ (ex.: x86_64-linux)
        candidates.extend(sorted(tinytex_root.rglob("dvisvgm"), reverse=True))

    for candidate in candidates:
        # Se candidate for o próprio binário dvisvgm, use-o; senão procure dentro.
        if candidate.name == "dvisvgm" and candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate.resolve())
        for name in ("dvisvgm", "dvisvgm.exe"):
            dvisvgm = candidate / name
            if dvisvgm.exists() and os.access(dvisvgm, os.X_OK):
                return str(dvisvgm.resolve())
    return "não encontrado"


def _gpu_info() -> dict:
    """Detecta GPU disponível para OpenGL."""
    info = {
        "nvidia_smi": False,
        "glxinfo_opengl": False,
        "detected": False,
    }
    try:
        result = subprocess.run(
            ["nvidia-smi", "-L"],
            capture_output=True,
            timeout=2,
        )
        info["nvidia_smi"] = result.returncode == 0
    except Exception:  # noqa: BLE001
        pass

    try:
        result = subprocess.run(
            ["glxinfo", "-B"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and "opengl" in (result.stdout or "").lower():
            info["glxinfo_opengl"] = True
    except Exception:  # noqa: BLE001
        pass

    info["detected"] = info["nvidia_smi"] or info["glxinfo_opengl"]
    return info


def _venv_ok() -> dict:
    """Verifica se estamos num venv e se os pacotes essenciais estão importáveis."""
    result = {
        "in_venv": sys.prefix != sys.base_prefix,
        "manim_importable": False,
        "pydantic_importable": False,
    }
    try:
        import manim  # noqa: F401
        result["manim_importable"] = True
    except Exception:  # noqa: BLE001
        pass
    try:
        import pydantic  # noqa: F401
        result["pydantic_importable"] = True
    except Exception:  # noqa: BLE001
        pass
    return result


def main() -> int:
    report = {
        "manim_version": _manim_version(),
        "ffmpeg_version": _ffmpeg_version(),
        "dvisvgm_path": _resolve_dvisvgm(),
        "gpu": _gpu_info(),
        "venv": _venv_ok(),
        "essential_ok": False,
    }

    essential = [
        report["manim_version"] != "não encontrado",
        report["ffmpeg_version"] != "não encontrado",
        report["dvisvgm_path"] != "não encontrado",
    ]
    report["essential_ok"] = all(essential)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["essential_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
