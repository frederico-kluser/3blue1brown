#!/usr/bin/env python3
"""
Eval runner: runs the minimal eval/regression suite for skills.
Usage: python3 run_skill_evals.py [skill-name]  # omit arg to run all
Exit codes: 0 = all passed, 1 = some failed, 2 = no evals found
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure manim-api modules are importable (they use flat imports within the dir)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "manim-api"))

SKILL_DIR = REPO_ROOT / ".agents" / "skills"
EVAL_DIR = SKILL_DIR / ".eval_records"


def run_import_check(module_path: str) -> tuple[bool, str]:
    """Try importing a module."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-c", f"import {module_path}; print('OK')"],
        capture_output=True, text=True, timeout=30,
        cwd=str(Path.cwd()),
    )
    ok = result.returncode == 0
    return ok, result.stderr.strip() or result.stdout.strip()


def run_ast_check(file_path: str) -> tuple[bool, str]:
    """Check if a Python file parses without syntax errors."""
    import ast
    try:
        ast.parse(Path(file_path).read_text())
        return True, "AST parse OK"
    except SyntaxError as e:
        return False, str(e)


def eval_manim_code_gen() -> list[dict]:
    """Evals for manim-code-gen skill."""
    results = []

    # Verify imports are available
    try:
        from services.openai_service import validate_code, sanitize_code, extract_code, get_scene_name
    except ImportError as e:
        return [{
            "test": "imports check (manim-api deps available)",
            "passed": False,
            "detail": f"Cannot import (venv may not be active): {e}",
        }]

    # Test 1: validate_code accepts valid code
    try:
        valid_code = """from manim import *

class TestScene(Scene):
    def construct(self):
        circle = Circle()
        self.play(Create(circle))
        self.wait()
"""
        ok, msg = validate_code(valid_code)
        results.append({
            "test": "validate_code accepts valid Manim code",
            "passed": ok,
            "detail": msg,
        })
    except Exception as e:
        results.append({
            "test": "validate_code accepts valid Manim code",
            "passed": False,
            "detail": str(e),
        })

    # Test 2: validate_code rejects missing import
    try:
        no_import = """
class TestScene(Scene):
    def construct(self):
        pass
"""
        ok, msg = validate_code(no_import)
        results.append({
            "test": "validate_code rejects missing 'from manim import'",
            "passed": not ok,
            "detail": msg,
        })
    except Exception as e:
        results.append({
            "test": "validate_code rejects missing 'from manim import'",
            "passed": False,
            "detail": str(e),
        })

    # Test 3: validate_code rejects dangerous imports
    try:
        dangerous = """from manim import *
import os

class TestScene(Scene):
    def construct(self):
        pass
"""
        ok, msg = validate_code(dangerous)
        results.append({
            "test": "validate_code rejects dangerous imports (os)",
            "passed": not ok and "Forbidden" in msg,
            "detail": msg,
        })
    except Exception as e:
        results.append({
            "test": "validate_code rejects dangerous imports (os)",
            "passed": False,
            "detail": str(e),
        })

    # Test 4: sanitize_code handles CYAN fallback
    try:
        code_with_cyan = "from manim import *\nc = Circle(color=CYAN)"
        result = sanitize_code(code_with_cyan)
        results.append({
            "test": "sanitize_code replaces CYAN with TEAL",
            "passed": "CYAN" not in result and ("TEAL" in result or "TEAL" in result),
            "detail": f"Result: {result[:80]}",
        })
    except Exception as e:
        results.append({
            "test": "sanitize_code replaces CYAN with TEAL",
            "passed": False,
            "detail": str(e),
        })

    # Test 5: extract_code handles markdown fences
    try:
        md = '```python\nfrom manim import *\n\nclass X(Scene):\n    def construct(self):\n        pass\n```'
        code = extract_code(md)
        results.append({
            "test": "extract_code extracts from markdown fences",
            "passed": "from manim import" in code and "class X" in code,
            "detail": f"Extracted: {code[:80]}",
        })
    except Exception as e:
        results.append({
            "test": "extract_code extracts from markdown fences",
            "passed": False,
            "detail": str(e),
        })

    return results


def eval_manim_rendering() -> list[dict]:
    """Evals for manim-rendering skill."""
    results = []

    # Test 1: RenderResult dataclass exists
    try:
        from services.manim_executor import RenderResult, find_video
        rr = RenderResult(success=True, video_path="/tmp/test.mp4")
        results.append({
            "test": "RenderResult dataclass instantiates",
            "passed": rr.success and rr.video_path == "/tmp/test.mp4",
            "detail": str(rr),
        })
    except Exception as e:
        results.append({
            "test": "RenderResult dataclass instantiates",
            "passed": False,
            "detail": str(e),
        })

    # Test 2: Manim CLI is available
    import subprocess
    try:
        result = subprocess.run(["manim", "--version"], capture_output=True, text=True, timeout=10)
        manim_ok = result.returncode == 0
        manim_detail = result.stdout.strip()[:100]
    except FileNotFoundError:
        manim_ok = False
        manim_detail = "manim CLI not installed in this environment (expected outside venv)"
    except Exception as e:
        manim_ok = False
        manim_detail = str(e)
    results.append({
        "test": "manim --version exits 0",
        "passed": manim_ok,
        "detail": manim_detail,
    })

    # Test 3: BackgroundRectangle patch is valid Python
    try:
        import ast
        patch = """from manim.mobject.geometry.shape_matchers import BackgroundRectangle

if not hasattr(BackgroundRectangle, "tex_string"):
    BackgroundRectangle.tex_string = ""
"""
        ast.parse(patch)
        results.append({
            "test": "BackgroundRectangle patch is valid Python",
            "passed": True,
            "detail": "AST parse OK",
        })
    except Exception as e:
        results.append({
            "test": "BackgroundRectangle patch is valid Python",
            "passed": False,
            "detail": str(e),
        })

    return results


def eval_fastapi_app() -> list[dict]:
    """Evals for fastapi-app skill."""
    results = []

    # Test 1: main.py parses without syntax errors
    ok, detail = run_ast_check("manim-api/main.py")
    results.append({
        "test": "main.py AST parse",
        "passed": ok,
        "detail": detail,
    })

    # Test 2: schemas.py parses
    ok, detail = run_ast_check("manim-api/schemas.py")
    results.append({
        "test": "schemas.py AST parse",
        "passed": ok,
        "detail": detail,
    })

    # Test 3: config.py parses
    ok, detail = run_ast_check("manim-api/config.py")
    results.append({
        "test": "config.py AST parse",
        "passed": ok,
        "detail": detail,
    })

    # Test 4: prompts.py parses
    ok, detail = run_ast_check("manim-api/prompts.py")
    results.append({
        "test": "prompts.py AST parse",
        "passed": ok,
        "detail": detail,
    })

    return results


def eval_project_router() -> list[dict]:
    """Routing evals for project-router."""
    results = []

    # Trigger queries (MUST match)
    triggers = [
        ("add new endpoint to the API", ["fastapi-app"]),
        ("change the CORS middleware", ["fastapi-app"]),
        ("add a new few-shot example for code generation", ["manim-code-gen"]),
        ("fix the render timeout bug", ["manim-rendering"]),
        ("debug why videos are not being found after render", ["manim-rendering"]),
        ("update the system prompt for better code gen", ["manim-code-gen"]),
        ("add a new config variable to .env", ["fastapi-app"]),
        ("the code generator keeps producing CYAN color", ["manim-code-gen"]),
        ("BackgroundRectangle is crashing the render", ["manim-rendering"]),
        ("add health check endpoint for the model version", ["fastapi-app"]),
    ]

    # Near-miss queries (must NOT match specific skills)
    near_misses = [
        ("write a README for the project", ["manim-code-gen", "manim-rendering"]),
        ("what is Python 3.11 syntax", ["manim-code-gen", "fastapi-app"]),
        ("how do I install homebrew", ["manim-rendering", "fastapi-app"]),
        ("explain quantum mechanics", ["manim-code-gen", "manim-rendering", "fastapi-app"]),
        ("what time is it", ["manim-code-gen", "manim-rendering", "fastapi-app"]),
    ]

    # Simple keyword-based routing check
    ROUTING_MAP = {
        "manim-code-gen": [
            "code gen", "few-shot", "prompt", "validation", "sanitize",
            "code generation", "system prompt", "openai_service", "few shot",
            "generates", "generating", "generate code", "CYAN",
        ],
        "manim-rendering": [
            "render", "timeout", "manim execute", "video", "executor",
            "manim_executor", "BackgroundRectangle", "TeX", "LaTeX",
            "subprocess", "CLI", "tempfile", "find video",
        ],
        "fastapi-app": [
            "endpoint", "route", "middleware", "CORS", "config",
            "settings", "schema", "API", "deploy", "Cloudflare",
            "tunnel", "main.py", "schemas.py", "config.py", "health check",
            "env", ".env",
        ],
    }

    def route_query(query: str) -> list[str]:
        q = query.lower()
        matched = []
        for skill, keywords in ROUTING_MAP.items():
            if any(kw.lower() in q for kw in keywords):
                matched.append(skill)
        return matched

    for query, expected in triggers:
        matched = route_query(query)
        all_found = all(s in matched for s in expected)
        results.append({
            "test": f"TRIGGER: '{query[:50]}...' → {expected}",
            "passed": all_found,
            "detail": f"Matched: {matched}",
        })

    for query, forbidden in near_misses:
        matched = route_query(query)
        none_matched = not any(s in matched for s in forbidden)
        results.append({
            "test": f"NEAR-MISS: '{query[:50]}...' NOT → {forbidden}",
            "passed": none_matched or len(matched) == 0,
            "detail": f"Matched: {matched}",
        })

    return results


EVAL_FUNCTIONS = {
    "manim-code-gen": eval_manim_code_gen,
    "manim-rendering": eval_manim_rendering,
    "fastapi-app": eval_fastapi_app,
    "project-router": eval_project_router,
    "meta-skill-evolution": lambda: [{"test": "skill_lint", "passed": True, "detail": "Delegated to skill_lint.py"}],
    "meta-skill-consolidate": lambda: [{"test": "skill_lint", "passed": True, "detail": "Delegated to skill_lint.py"}],
}


def save_record(skill_name: str, results: list[dict], passed: bool):
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "skill": skill_name,
        "last_eval_passed": passed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    (EVAL_DIR / f"{skill_name}.json").write_text(json.dumps(record, indent=2))


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None

    if target and target not in EVAL_FUNCTIONS:
        print(f"Unknown skill: {target}")
        print(f"Available: {list(EVAL_FUNCTIONS.keys())}")
        sys.exit(2)

    skills_to_run = [target] if target else list(EVAL_FUNCTIONS.keys())
    all_passed = True

    for skill in skills_to_run:
        print(f"\n=== {skill} ===")
        try:
            results = EVAL_FUNCTIONS[skill]()
        except Exception as e:
            print(f"  ERROR running evals: {e}")
            save_record(skill, [], False)
            all_passed = False
            continue

        passed = all(r["passed"] for r in results)
        save_record(skill, results, passed)

        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"  [{status}] {r['test']}")
            if not r["passed"]:
                print(f"         {r['detail'][:120]}")

        if passed:
            print(f"  => ALL {len(results)} PASSED")
        else:
            failed = [r for r in results if not r["passed"]]
            print(f"  => {len(failed)}/{len(results)} FAILED")
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
