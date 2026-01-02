#!/usr/bin/env python3
"""Dispara múltiplos requests paralelos contra /generate-video local."""
from __future__ import annotations

import concurrent.futures
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict

BASE_URL = "http://127.0.0.1:8000/generate-video"
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
TIMEOUT = 300

PROMPTS = [
    "Close dos eixos cartesianos com setas positivas em azul/teal",
    "Zoom nos eixos XY estilo 3Blue1Brown com escala curta e setas destacadas",
    "Eixos cartesianos com anotação das direções positivas em tons cyan",
    "Plano cartesiano com flechas grossas apontando para +X e +Y",
    "Visual 3Blue1Brown de eixos com labels e setas teal indicando positivo",
]


def _send_request(index: int, description: str) -> Dict[str, Any]:
    payload = {
        "description": f"{description} [req {index}]",
        "width": DEFAULT_WIDTH,
        "height": DEFAULT_HEIGHT,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
            status = resp.getcode()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except Exception as exc:  # Transport-level failure
        duration = time.perf_counter() - start
        return {
            "id": index,
            "status": None,
            "duration": duration,
            "success": False,
            "error": str(exc),
        }

    duration = time.perf_counter() - start
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        data = {"raw": body}

    return {
        "id": index,
        "status": status,
        "duration": duration,
        "success": data.get("success"),
        "backend_error": data.get("error"),
        "scene_name": data.get("scene_name"),
        "render_logs": data.get("render_logs"),
        "raw": data.get("raw"),
    }


def main() -> int:
    start_all = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(PROMPTS)) as executor:
        futures = [executor.submit(_send_request, i + 1, prompt) for i, prompt in enumerate(PROMPTS)]
        results = [future.result() for future in futures]

    total = time.perf_counter() - start_all
    any_failure = False
    for result in sorted(results, key=lambda r: r["id"]):
        print("-" * 80)
        print(
            f"Request #{result['id']}: status={result.get('status')} success={result.get('success')} "
            f"duration={result.get('duration', 0):.2f}s scene={result.get('scene_name')}"
        )
        if result.get("error"):
            print(f"  Transport error: {result['error']}")
            any_failure = True
        if result.get("backend_error"):
            print(f"  Backend error: {result['backend_error']}")
            any_failure = True
        if result.get("render_logs"):
            print("  Render logs snippet:")
            print(result["render_logs"][:500])
            any_failure = True
        if result.get("success") is not True:
            any_failure = True
    print("-" * 80)
    print(f"Total wall time for {len(PROMPTS)} requests: {total:.2f}s")
    return 1 if any_failure else 0


if __name__ == "__main__":
    sys.exit(main())
