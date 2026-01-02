import ast
import re
from openai import AsyncOpenAI

from config import get_settings
from prompts import build_messages
from schemas import CodeResponse

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)

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
        return False, "Missing 'from manim import' statement"

    if "(Scene)" not in code and "(ThreeDScene)" not in code:
        return False, "Missing Scene class definition"

    if "def construct(self)" not in code:
        return False, "Missing construct method"

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


async def generate_manim_code(description: str) -> CodeResponse:
    """Gera código Manim a partir de descrição em linguagem natural."""
    try:
        messages = build_messages(description)
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.2,
            max_tokens=2000,
        )

        raw_response = response.choices[0].message.content
        code = extract_code(raw_response)
        scene_name = get_scene_name(code)
        is_valid, message = validate_code(code)

        return CodeResponse(
            code=code,
            scene_name=scene_name,
            is_valid=is_valid,
            validation_message=message,
        )
    except Exception as exc:
        return CodeResponse(
            code="",
            scene_name="",
            is_valid=False,
            validation_message=str(exc),
        )
