#!/usr/bin/env python3
"""Asserção de fundo de vídeo por amostragem de pixels.

Valida que uma região de fundo de um clipe MP4 corresponde à cor esperada,
reportando desvio por canal e uniformidade.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    match = HEX_RE.match(hex_color)
    if not match:
        raise ValueError(f"cor hex inválida: {hex_color!r}")
    value = match.group(1)
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )


def _decode_middle_frame(video_path: Path) -> Path:
    """Extrai o quadro do meio do vídeo como PNG via ffmpeg."""
    # Primeiro obtém duração em segundos
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if probe.returncode != 0:
        raise RuntimeError(f"ffprobe falhou: {probe.stderr.strip()}")
    try:
        duration = float(probe.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"não foi possível ler duração do vídeo: {exc}")

    middle = max(0.0, duration / 2.0)

    tmpdir = Path(tempfile.gettempdir()) / f"assert_bg_{video_path.stem}"
    tmpdir.mkdir(parents=True, exist_ok=True)
    frame_path = tmpdir / "middle_frame.png"

    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(middle),
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "1",
            "-pix_fmt",
            "rgb24",
            str(frame_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou: {result.stderr.strip()}")
    return frame_path


def _sample_region(frame_path: Path) -> tuple[int, int]:
    """Retorna largura e altura do frame."""
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0",
            str(frame_path),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if probe.returncode != 0:
        raise RuntimeError(f"ffprobe falhou no frame: {probe.stderr.strip()}")
    parts = probe.stdout.strip().split(",")
    if len(parts) != 2:
        raise RuntimeError(f"dimensões do frame não reconhecidas: {probe.stdout!r}")
    return int(parts[0]), int(parts[1])


def _analyze(frame_path: Path, expected_rgb: tuple[int, int, int]) -> dict:
    """Amostra uma região central de fundo e calcula desvios."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(f"PIL não disponível: {exc}")

    img = Image.open(frame_path)
    width, height = img.size

    # Região central de 300x200 (ou metade do frame se menor)
    sample_w = min(300, width // 2)
    sample_h = min(200, height // 2)
    left = (width - sample_w) // 2
    top = (height - sample_h) // 2
    right = left + sample_w
    bottom = top + sample_h

    region = img.crop((left, top, right, bottom))
    pixels = list(region.get_flattened_data())
    total = len(pixels)

    # Cor dominante
    counts: dict[tuple[int, int, int], int] = {}
    for pixel in pixels:
        counts[pixel] = counts.get(pixel, 0) + 1

    dominant = max(counts, key=lambda k: counts[k])
    dominant_count = counts[dominant]
    distinct = len(counts)
    uniformity = dominant_count / total if total else 0.0

    deviation = tuple(abs(d - e) for d, e in zip(dominant, expected_rgb))

    return {
        "frame_size": {"width": width, "height": height},
        "sample_region": {
            "left": left,
            "top": top,
            "width": sample_w,
            "height": sample_h,
        },
        "dominant": {
            "rgb": list(dominant),
            "hex": f"#{dominant[0]:02x}{dominant[1]:02x}{dominant[2]:02x}",
            "count": dominant_count,
        },
        "expected": {
            "rgb": list(expected_rgb),
            "hex": f"#{expected_rgb[0]:02x}{expected_rgb[1]:02x}{expected_rgb[2]:02x}",
        },
        "deviation": list(deviation),
        "max_deviation": max(deviation),
        "distinct_colors": distinct,
        "uniformity": round(uniformity * 100, 2),
        "passed": max(deviation) <= 2 and uniformity >= 0.99,
    }


def _self_test() -> int:
    """Auto-teste com caso positivo e negativo, sem depender de vídeo externo."""
    try:
        from PIL import Image
    except ImportError as exc:
        print(json.dumps({"error": f"PIL não disponível: {exc}"}, ensure_ascii=False))
        return 1

    tmpdir = Path(tempfile.gettempdir()) / "assert_bg_selftest"
    tmpdir.mkdir(parents=True, exist_ok=True)

    # Caso positivo: imagem branca pura, deve passar
    white_path = tmpdir / "white.png"
    Image.new("RGB", (320, 240), (255, 255, 255)).save(white_path)

    # Caso negativo: imagem preta, deve falhar contra #FFFFFF
    black_path = tmpdir / "black.png"
    Image.new("RGB", (320, 240), (0, 0, 0)).save(black_path)

    white_result = _analyze(white_path, (255, 255, 255))
    black_result = _analyze(black_path, (255, 255, 255))

    report = {
        "positive": white_result,
        "negative": black_result,
        "positive_passed": white_result["passed"],
        "negative_rejected": not black_result["passed"],
        "ok": white_result["passed"] and not black_result["passed"],
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Asserção de fundo de vídeo.")
    parser.add_argument("video", nargs="?", help="caminho para o arquivo MP4")
    parser.add_argument(
        "--expect",
        dest="expected_hex",
        default="#FFFFFF",
        help="cor esperada do fundo (hex, padrão #FFFFFF)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="roda auto-teste sem vídeo externo",
    )
    args = parser.parse_args()

    if args.self_test:
        return _self_test()

    if not args.video:
        print(
            json.dumps(
                {"error": "caminho do vídeo é obrigatório (ou use --self-test)"},
                ensure_ascii=False,
            )
        )
        return 1

    video_path = Path(args.video)
    try:
        expected_rgb = _hex_to_rgb(args.expected_hex)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1

    if not video_path.exists():
        print(
            json.dumps(
                {"error": f"arquivo não encontrado: {video_path}"},
                ensure_ascii=False,
            )
        )
        return 1

    try:
        frame_path = _decode_middle_frame(video_path)
        result = _analyze(frame_path, expected_rgb)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["passed"] else 1
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
