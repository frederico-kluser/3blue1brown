---
name: manim-code-gen
description: Injects the prompt engineering rules, code validation pipeline, AST-based security checks, and code sanitization quirks of this project's Manim CE 0.19.0 code generator. Use whenever generating, modifying, or debugging Manim code generation, prompts, validation, or sanitization logic — even if the user doesn't mention "prompts" or "openai_service". Triggers: "generate code", "prompt", "validation", "sanitize", "few-shot", "code generation", "openai_service", "prompts.py", "Manim code", "regenerate", "fix code gen".
metadata:
  type: knowledge
  verification_signal: "python3 -c 'import ast; from manim-api.services.openai_service import validate_code, sanitize_code, extract_code, get_scene_name; print(\"OK\")' && python3 .agents/scripts/skill_lint.py"
---
# Manim Code Generation

## When to use
- You are touching `prompts.py` or `services/openai_service.py`
- You need to add/modify few-shot examples in the code generator
- You are debugging why generated Manim code fails validation
- You are adjusting prompt engineering or model parameters
- You are adding new validation rules or sanitization passes
- The user mentions "prompt", "few-shot", "code generation", "validate", "sanitize"

## Injected knowledge

### Two-stage LLM pipeline

The code generator runs TWO sequential LLM calls, not one:

1. **Prompt optimizer** (`optimize_prompt`): Rewrites and enriches the user's raw description with Manim CE context. Returns JSON with `improved_prompt` and `resource_plan`. Configured in `prompts.py:242-269` (`PROMPT_OPTIMIZER_SYSTEM_PROMPT`).
2. **Code generator** (`generate_manim_code`): Takes the optimized prompt + resource plan + few-shots and generates actual Python code. Configured in `prompts.py:271-330` (`MANIM_SYSTEM_PROMPT`).

If the optimizer fails (network, parse error), it silently falls back to the raw description + default resource notes (`openai_service.py:259-261`).

### Validation pipeline (order matters)

`openai_service.py:100-139` — the `validate_code()` function runs these checks in order:

1. **AST parse** — SyntaxError → immediate rejection
2. **`from manim import` present** — missing → rejection with specific message
3. **Scene class found** — `class X(Scene)` or `(ThreeDScene)` or `(MovingCameraScene)` required
4. **`construct` method** — must have `def construct(self)`
5. **Dangerous imports** — blocks `os`, `sys`, `subprocess`, `shutil`, `socket`, `urllib`, `requests`, `pickle`, `ctypes`, `multiprocessing`, `pty` (defined at `openai_service.py:21-33`)
6. **Dangerous functions** — blocks `eval`, `exec`, `open`, `__import__`, `compile` (defined at `openai_service.py:35`)

### Retry with simplification

`openai_service.py:37-44` — when code fails validation, the system retries up to `MAX_CODE_ATTEMPTS=3` times. On retries 2 and 3, the prompt gets `RETRY_SIMPLIFICATION_INSTRUCTIONS` appended, which instructs the LLM to produce a simpler 2D scene with basic mobjects. The original intent is preserved but complexity is reduced.

### Code sanitization (post-generation fixes)

`openai_service.py:188-236` — the `sanitize_code()` function applies AST-level transforms to fix known LLM mistakes:

1. **Color fallbacks**: `CYAN` → `TEAL`, `CYAN_A` → `TEAL_A`, etc. (`openai_service.py:46-53`). These colors don't exist in Manim CE constants but the LLM generates them anyway.
2. **`add_background_rectangle` kwarg**: Renames `fill_opacity` → `opacity` (`openai_service.py:208-213`). The LLM consistently uses the wrong parameter name.
3. **`add_tip` style removal**: Strips `tip_style` kwargs from `add_tip` calls (`openai_service.py:213-217`). This parameter causes errors in CE 0.19.0.

Sanitization is applied AFTER extraction and BEFORE validation. If sanitization makes zero changes, the original code is returned unchanged (the `modified` flag at line 196).

### Code extraction

`openai_service.py:78-88` — `extract_code()` uses regex `r"```python\s*(.*?)\s*```"` to pull code from markdown fences. If no fence found but `from manim import` is present, it treats the entire response as code. Otherwise raises ValueError.

### Scene name extraction

`openai_service.py:91-97` — `get_scene_name()` regex: `r"class\s+(\w+)\s*\(\s*(?:Scene|ThreeDScene|MovingCameraScene)\s*\)"`. Scene names are PascalCase.

### Prompt engineering rules (normative)

The system prompt at `prompts.py:271-330` encodes 13 critical rules. The most important for code changes:

- Rule 1: Always `from manim import *` (not ManimGL)
- Rule 4: Every animation must use `self.play()`
- Rule 5: Always end with `self.wait()` or `self.wait(1)`
- Rule 6: Total animation < 30 seconds
- Rule 10: Never overlap elements — remove/fade/reposition before creating new ones
- Rule 12: Add debug logs/prints before each important step
- Rule 13: `TransformMatchingTex/TransformMatchingShapes` must not have background rectangles on source/target

The prompt optimizer prompt (`prompts.py:242-269`) adds 9 additional rules, including:
- Rule 5: Respect the `[VIDEO SPECIFICATIONS]` block for resolution/orientation
- Rule 8: Minimum 5% margin from video edges for all important elements
- Rule 9: Respond in the user's language (no automatic translation)

### Few-shot examples

`prompts.py:332-345` — three examples: (1) Blue circle growing, (2) Einstein equation letter-by-letter, (3) Red square → green triangle. These are appended to EVERY code generation request. Adding a new few-shot means editing `FEW_SHOT_EXAMPLES` and it will be included automatically.

### Model parameters

The API uses `client.responses.create()` with `reasoning={"effort": "xhigh"}` for both stages (`openai_service.py:249,293`). Temperature is NOT set in code — it relies on the model default. The README recommends temperature=0.0 (`README.md:323`) but this is advisory, not enforced.

## References
- `manim-api/prompts.py` — All prompt templates, system prompts, and few-shots
- `manim-api/services/openai_service.py` — Code generation, validation, sanitization
- `manim-api/schemas.py` — Request/response models (10-2000 char limit, 320-3840 px)
- `manim-api/config.py` — Settings (OPENAI_API_KEY, OPENAI_MODEL, RENDER_TIMEOUT)
