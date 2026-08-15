"""Serviço de geração de código Manim via OpenRouter (/chat/completions).

Mesma superfície pública de openai_service.py para facilitar substituição.
"""

import ast
import json
import logging
import re
from typing import Any, Tuple

import httpx

from config import get_settings
from prompts import (
    DEFAULT_RESOURCE_NOTES,
    build_code_generation_messages,
    build_prompt_optimizer_messages,
)
from schemas import CodeResponse

settings = get_settings()
logger = logging.getLogger("manim_api.openrouter")

DANGEROUS_IMPORTS = {
    "os",
    "sys",
    "subprocess",
    "shutil",
    "socket",
    "urllib",
    "requests",
    "pickle",
    "ctypes",
    "multiprocessing",
    "pty",
}

DANGEROUS_FUNCTIONS = {"eval", "exec", "open", "__import__", "compile"}

MAX_CODE_ATTEMPTS = 3
RETRY_SIMPLIFICATION_INSTRUCTIONS = (
    "[RETRY SIMPLIFICATION]\n"
    "- A tentativa anterior falhou. Produza uma versão mais simples, porém fiel ao pedido.\n"
    "- Prefira uma única cena 2D usando mobjects básicos (Shapes, Text, Axes) e animações Create/Write/Fade/Transform.\n"
    "- Evite recursos complexos (ThreeDScene, câmera em movimento, LaTeX excessivo) a menos que sejam absolutamente necessários.\n"
    "- Reforce todos os requisitos obrigatórios: `from manim import *`, classe Scene, método construct, uso de self.play e self.wait final."
)

COLOR_FALLBACKS = {
    "CYAN": "TEAL",
    "CYAN_A": "TEAL_A",
    "CYAN_B": "TEAL_B",
    "CYAN_C": "TEAL_C",
    "CYAN_D": "TEAL_D",
    "CYAN_E": "TEAL_E",
}

OPENROUTER_BASE_URL = getattr(settings, "openrouter_base_url", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = getattr(settings, "openrouter_model", "deepseek/deepseek-v4-pro")


def _orientation_from_resolution(width: int, height: int) -> str:
    if width > height:
        return "horizontal (landscape)"
    if height > width:
        return "vertical (portrait)"
    return "quadrada"


def _build_video_spec_notes(width: int, height: int) -> Tuple[int, int, str]:
    width = width or 1920
    height = height or 1080
    orientation = _orientation_from_resolution(width, height)
    notes = (
        "[VIDEO SPECIFICATIONS]\n"
        f"- Resolution: {width}x{height} px\n"
        f"- Frame rate: {getattr(settings, 'default_fps', 30)} fps\n"
        f"- Orientation: {orientation}; distribua objetos para ocupar todo o espaço visível\n"
        "- Ajuste proporções, escalas e posicionamento de texto/imagens para essa geometria"
    )
    return width, height, notes


def extract_code(response: str) -> str:
    """Extrai código Python de resposta markdown."""
    pattern = r"```python\s*(.*?)\s*```"
    matches = re.findall(pattern, response, re.DOTALL)
    if matches:
        return matches[0].strip()

    if "from manim import" in response:
        return response.strip()

    raise ValueError("Could not extract valid Manim code from response")


def get_scene_name(code: str) -> str:
    """Extrai nome da classe Scene do código."""
    pattern = r"class\s+(\w+)\s*\(\s*(?:Scene|ThreeDScene|MovingCameraScene)\s*\)"
    match = re.search(pattern, code)
    if match:
        return match.group(1)
    raise ValueError("Could not find Scene class in code")


def validate_code(code: str) -> tuple[bool, str]:
    """Valida código Manim antes de executar."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"Syntax error: {exc}"

    if "from manim import" not in code:
        return False, (
            "Missing 'from manim import' statement. Reforce no prompt que o código deve começar com "
            "`from manim import *` (ou imports equivalentes) antes da classe da cena."
        )

    if all(scene_base not in code for scene_base in ("(Scene)", "(ThreeDScene)", "(MovingCameraScene)")):
        return False, (
            "Missing Scene class definition. Ajuste sua descrição para pedir explicitamente uma classe como "
            "`class MinhaCena(Scene):` contendo o método construct com as animações desejadas."
        )

    if "def construct(self)" not in code:
        return False, (
            "Missing construct method. Solicite no prompt que a classe Scene implemente `def construct(self):` "
            "com os passos da animação."
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                if module in DANGEROUS_IMPORTS:
                    return False, f"Forbidden import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            module = (node.module or "").split(".")[0]
            if module in DANGEROUS_IMPORTS:
                return False, f"Forbidden import: from {node.module}"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_FUNCTIONS:
                return False, f"Forbidden function: {node.func.id}()"

    return True, "Code validated successfully"


def _strip_code_fence(payload: str) -> str:
    text = payload.strip()
    if text.startswith("```") and text.endswith("```"):
        return "\n".join(text.splitlines()[1:-1]).strip()
    if text.startswith("```"):
        parts = text.split("```", 2)
        if len(parts) >= 2:
            return parts[1].strip()
    return text


def _safe_load_json(payload: str) -> dict:
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {}


def _ensure_str(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    return str(value)


def _extract_content(response: dict) -> str:
    choices = response.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return message.get("content", "")


def _is_background_color_assignment(node: ast.Assign) -> bool:
    """Detecta atribuições a config.background_color ou self.camera.background_color."""
    if len(node.targets) != 1:
        return False
    target = node.targets[0]
    if isinstance(target, ast.Attribute):
        if target.attr == "background_color":
            if isinstance(target.value, ast.Name) and target.value.id == "config":
                return True
            if (
                isinstance(target.value, ast.Attribute)
                and target.value.attr == "camera"
                and isinstance(target.value.value, ast.Name)
                and target.value.value.id == "self"
            ):
                return True
    return False


def sanitize_code(code: str, request_id: str | None = None) -> str:
    rid = request_id or "no-request-id"
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    modified = False

    class _Sanitizer(ast.NodeTransformer):
        def visit_Assign(self, node: ast.Assign) -> Any:  # noqa: N802
            nonlocal modified
            if _is_background_color_assignment(node):
                modified = True
                logger.info(
                    "[%s] Removed forbidden background_color assignment from generated code",
                    rid,
                )
                return None
            return self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> Any:
            nonlocal modified
            self.generic_visit(node)

            func_name = None
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id

            if func_name == "add_background_rectangle":
                for kw in node.keywords:
                    if kw.arg == "fill_opacity":
                        kw.arg = "opacity"
                        modified = True
            if func_name == "add_tip" and node.keywords:
                filtered = [kw for kw in node.keywords if kw.arg != "tip_style"]
                if len(filtered) != len(node.keywords):
                    node.keywords = filtered
                    modified = True
            return node

        def visit_Name(self, node: ast.Name) -> Any:
            nonlocal modified
            replacement = COLOR_FALLBACKS.get(node.id)
            if replacement:
                node.id = replacement
                modified = True
            return node

    transformer = _Sanitizer()
    transformer.visit(tree)
    if not modified:
        return code

    ast.fix_missing_locations(tree)
    sanitized = ast.unparse(tree)
    logger.info("[%s] Applied code sanitization", rid)
    return sanitized


async def _chat_completion(messages: list[dict], request_id: str) -> dict:
    """Chama OpenRouter /chat/completions."""
    api_key = getattr(settings, "openrouter_api_key", None)
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY não configurada")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "top_p": 0.95,
    }

    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code == 401:
        raise RuntimeError("OPENROUTER_API_KEY inválida (401)")
    if response.status_code == 429:
        raise RuntimeError("Rate limit do OpenRouter (429) — aguarde e tente novamente")
    response.raise_for_status()
    return response.json()


async def optimize_prompt(
    description: str,
    video_spec: str | None = None,
    request_id: str | None = None,
) -> tuple[str, str]:
    rid = request_id or "no-request-id"
    try:
        logger.info("[%s] Optimizing prompt", rid)
        messages = build_prompt_optimizer_messages(description, video_spec)
        data = await _chat_completion(messages, rid)
        content = _extract_content(data)
        parsed = _safe_load_json(_strip_code_fence(content))
        improved = _ensure_str(parsed.get("improved_prompt"), description)
        resource_plan = _ensure_str(parsed.get("resource_plan"), DEFAULT_RESOURCE_NOTES)
        logger.info("[%s] Prompt optimization completed", rid)
        return improved.strip(), resource_plan.strip()
    except Exception as exc:
        logger.warning("[%s] Prompt optimization failed: %s", rid, exc)
        return description, DEFAULT_RESOURCE_NOTES


async def generate_manim_code(
    description: str,
    width: int | None = None,
    height: int | None = None,
    request_id: str | None = None,
) -> CodeResponse:
    """Gera código Manim a partir de descrição em linguagem natural."""
    rid = request_id or "no-request-id"
    try:
        logger.info("[%s] Starting code generation", rid)
        width, height, video_spec_notes = _build_video_spec_notes(width, height)
        optimized_prompt, resource_plan = await optimize_prompt(description, video_spec_notes, request_id=rid)

        last_code = ""
        last_scene_name = ""
        last_message = "Code generation failed"

        for attempt in range(1, MAX_CODE_ATTEMPTS + 1):
            attempt_prompt = optimized_prompt
            if attempt > 1:
                attempt_prompt = f"{optimized_prompt}\n\n[RETRY #{attempt}]\n{RETRY_SIMPLIFICATION_INSTRUCTIONS}"

            messages = build_code_generation_messages(attempt_prompt, resource_plan, video_spec_notes)
            logger.info("[%s] Code generation attempt %s/%s", rid, attempt, MAX_CODE_ATTEMPTS)

            try:
                data = await _chat_completion(messages, rid)
                raw_response = _extract_content(data)
                code = extract_code(raw_response)
                code = sanitize_code(code, rid)
            except Exception as exc:  # Erros durante chamada ou parsing
                logger.warning("[%s] Attempt %s failed during LLM call/parsing: %s", rid, attempt, exc)
                last_code = ""
                last_scene_name = ""
                last_message = str(exc)
                continue

            try:
                scene_name = get_scene_name(code)
            except ValueError as exc:
                logger.warning("[%s] Attempt %s missing scene name: %s", rid, attempt, exc)
                last_code = code
                last_scene_name = ""
                last_message = str(exc)
                continue

            is_valid, message = validate_code(code)
            if is_valid:
                logger.info(
                    "[%s] Code generation succeeded on attempt %s (scene=%s)",
                    rid,
                    attempt,
                    scene_name,
                )
                return CodeResponse(
                    code=code,
                    scene_name=scene_name,
                    is_valid=True,
                    validation_message=message,
                )

            logger.warning(
                "[%s] Attempt %s produced invalid code: %s",
                rid,
                attempt,
                message,
            )
            last_code = code
            last_scene_name = scene_name
            last_message = message

        logger.error(
            "[%s] Exhausted %s attempts without valid code: %s",
            rid,
            MAX_CODE_ATTEMPTS,
            last_message,
        )
        return CodeResponse(
            code=last_code,
            scene_name=last_scene_name,
            is_valid=False,
            validation_message=f"{last_message} (after {MAX_CODE_ATTEMPTS} attempts)",
        )
    except Exception as exc:
        logger.exception("[%s] Unexpected error during code generation", rid)
        return CodeResponse(
            code="",
            scene_name="",
            is_valid=False,
            validation_message=str(exc),
        )
