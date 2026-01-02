import ast
import json
import logging
import re
from typing import Any, Tuple

from openai import AsyncOpenAI

from config import get_settings
from prompts import (
    DEFAULT_RESOURCE_NOTES,
    build_code_generation_messages,
    build_prompt_optimizer_messages,
)
from schemas import CodeResponse

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)
logger = logging.getLogger("manim_api.openai")

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
        "- Frame rate: 60 fps (render de alta qualidade)\n"
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


def _extract_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return text

    collected: list[str] = []
    for item in getattr(response, "output", []) or []:
        content = getattr(item, "content", None)
        if isinstance(content, list):
            for chunk in content:
                chunk_text = getattr(chunk, "text", None)
                if chunk_text:
                    collected.append(chunk_text)
        elif isinstance(content, str):
            collected.append(content)
    return "".join(collected)


def sanitize_code(code: str, request_id: str | None = None) -> str:
    rid = request_id or "no-request-id"
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    modified = False

    class _Sanitizer(ast.NodeTransformer):
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
    logger.info("[%s] Applied code sanitization for unsupported Manim arguments", rid)
    return sanitized


async def optimize_prompt(
    description: str,
    video_spec: str | None = None,
    request_id: str | None = None,
) -> tuple[str, str]:
    rid = request_id or "no-request-id"
    try:
        logger.info("[%s] Optimizing prompt", rid)
        messages = build_prompt_optimizer_messages(description, video_spec)
        response = await client.responses.create(
            model=settings.openai_model,
            input=messages,
            reasoning={"effort": "xhigh"},
        )
        content = _extract_text(response)
        data = _safe_load_json(_strip_code_fence(content))
        improved = _ensure_str(data.get("improved_prompt"), description)
        resource_plan = _ensure_str(data.get("resource_plan"), DEFAULT_RESOURCE_NOTES)
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
                response = await client.responses.create(
                    model=settings.openai_model,
                    input=messages,
                    reasoning={"effort": "xhigh"},
                )

                raw_response = _extract_text(response)
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
