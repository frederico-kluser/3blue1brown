# Project Analysis: Manim Video Generator API

> **Date:** 2026-08-09 | **Commit range:** `0ad3da0`..`6f558ef` | **Model:** deepseek-v4-pro

## 1. Executive Summary

This is a **single-module FastAPI application** that transforms natural-language descriptions into Manim CE 0.19.0 animation videos via OpenAI GPT-5.1 Codex Max. The pipeline has two LLM stages (prompt optimization → code generation), AST-based security validation, headless Manim CLI rendering in temp directories, and base64/MP4 responses. It's exposed publicly at `ondokai.com` via Cloudflare Tunnel running on a Mac mini M1 16GB.

**Scale:** ~650 lines of production Python across 6 source files + 1 test script. No CI, no linter, no type checker, no existing tests.

**Language context:** The developer is a Portuguese speaker (Brazilian Portuguese). All docs are in Portuguese. The API itself handles both Portuguese and English requests (prompts.py rule 9/11/12).

## 2. Architecture

```
Request (JSON description)
  → FastAPI (main.py) + CORS middleware
    → config.py (Pydantic BaseSettings from .env)
    → schemas.py (VideoRequest validation: 10-2000 chars, 320-3840 px)
    → services/openai_service.py:
        1. Prompt optimizer: enriches description with Manim CE context
        2. Code generator: produces Python Scene code (3 few-shot examples)
        3. AST validation: blocks dangerous imports/functions
        4. Code sanitization: fixes known Manim API quirks
    → services/manim_executor.py:
        1. Tempfile isolation (TemporaryDirectory)
        2. BackgroundRectangle monkey-patch (Manim bug workaround)
        3. `manim render -r WxH --fps 60 --disable_caching`
        4. Video file discovery + base64 encode
  → Response (JSON with base64 or binary MP4 stream)
```

**Endpoints:**
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Health check (Manim version, model) |
| POST | `/generate-code` | Code-only response |
| POST | `/generate-video` | base64 MP4 in JSON |
| POST | `/generate-video-file` | Binary MP4 download |

## 3. Source File Map

| File | Lines | Role | Key Detail |
|------|-------|------|------------|
| `main.py` | 261 | App entry, routes, middleware | CORS `*`, request-id tracking, perf logging |
| `config.py` | 31 | Settings via Pydantic BaseSettings | `.env` source, `@lru_cache` singleton |
| `schemas.py` | 46 | Pydantic models | description 10-2000 chars, resolution 320-3840 |
| `prompts.py` | 374 | Prompt templates + few-shots | Two system prompts (optimizer + coder), 3 examples |
| `services/openai_service.py` | 360 | LLM orchestration + code validation | 2-stage pipeline, AST security, 3 retries with simplification |
| `services/manim_executor.py` | 157 | Headless Manim rendering | Tempfile isolation, BackgroundRectangle patch |
| `scripts/parallel_request_test.py` | 112 | Load-test utility | ThreadPool, 5 parallel requests |
| `.env.example` | 14 | Environment template | OPENAI_API_KEY, model, timeout, host/port |

## 4. Normative Conventions (with provenance)

### 4.1 Hard Constraints (from code, not docs)

| Constraint | Source | Enforcement |
|------------|--------|-------------|
| `from manim import *` required | `openai_service.py:107` | AST-level check fails otherwise |
| Single Scene class with `construct()` | `openai_service.py:113-123` | AST-level check |
| `self.play()` for every animation | `prompts.py:277` | LLM instruction only |
| `self.wait()` at end required | `prompts.py:278` | LLM instruction only |
| description 10-2000 chars | `schemas.py:8-10` | Pydantic Field validation |
| resolution 320-3840 px | `schemas.py:13-21` | Pydantic Field validation |
| Dangerous imports blocked | `openai_service.py:21-33,125-137` | AST walk after generation |
| 3 retry attempts with simplification | `openai_service.py:37-44,281-284` | Loop in generate_manim_code |
| Temperature 0.0 deterministic | `README.md:323` | LLM instruction only (not in code) |
| 60 FPS render | `manim_executor.py:98` | Hardcoded in CLI args |
| `--disable_caching` | `manim_executor.py:103` | Hardcoded |
| 120s render timeout | `config.py:15` | Configurable via `.env` |
| Manim CE 0.19.0 (not GL) | `prompts.py:274` | LLM instruction only |

### 4.2 Code Style (observed, not enforced)

- Python 3.11+ union syntax (`X | None`, `tuple[int, int]`)
- Pydantic v2 style (`BaseModel`, `BaseSettings`, `model_config`)
- AsyncOpenAI with `client.responses.create` (not legacy `chat.completions`)
- Structured logging with `[request_id]` prefix
- Dataclasses for internal DTOs (RenderResult)
- Dataclass + `@lru_cache` for settings singleton
- Type hints on all function signatures
- Docstrings are sparse (none in many functions)
- No `if __name__ == "__main__"` guard in service files (only in main.py and script)
- Project config file not yet extracted: `manim.cfg` referenced but not present

### 4.3 Known Gotchas (from code, not docs)

1. **BackgroundRectangle monkey-patch** (`manim_executor.py:29-34`): A bug in Manim CE 0.19.0 causes `BackgroundRectangle` to fail if `tex_string` attribute is missing. The executor prepends a patch to every scene script.

2. **Color fallbacks** (`openai_service.py:46-53`): `CYAN` colors are mapped to `TEAL` equivalents because they don't exist in Manim CE constants.

3. **`add_background_rectangle` argument rename** (`openai_service.py:208-213`): The sanitizer rewrites `fill_opacity` → `opacity` for `add_background_rectangle` calls because the LLM frequently uses the wrong kwarg.

4. **`add_tip` style removal** (`openai_service.py:213-217`): The sanitizer strips `tip_style` kwargs from `add_tip` calls as they cause errors in CE 0.19.0.

5. **Video file discovery** (`manim_executor.py:47-58`): Manim outputs to unpredictable quality-named subdirectories. The executor searches recursively for the newest `.mp4` matching the scene name.

6. **LaTeX path resolution** (`manim_executor.py:16-27`): The executor probes `~/texlive/*/bin/*` to find LaTeX binaries, necessary on macOS where TeX Live isn't on PATH by default.

7. **No graceful degradation on prompt optimizer failure** (`openai_service.py:259-261`): If prompt optimization fails, it falls back to the raw description + default notes silently.

## 5. Domain Areas (candidates for skills)

| Domain | Scope | Knowledge Density |
|--------|-------|-------------------|
| **Manim CE code generation** | prompts.py, openai_service.py | VERY HIGH — prompt engineering rules, validation, sanitization, gotchas |
| **Manim CLI rendering** | manim_executor.py | HIGH — CLI args, env setup, video discovery, patching |
| **FastAPI app structure** | main.py, config.py, schemas.py | MEDIUM — middleware, settings, request/response models |
| **Cloudflare Tunnel deployment** | CLOUDFLARE.md, README.md sections 6.2 | MEDIUM — tunnel setup, DNS, service management |
| **OpenAI API integration** | openai_service.py | LOW-MEDIUM — standard SDK usage, few project-specific patterns |
| **API consumption** | API_CONSUMER.md | LOW — external-facing, not internal development |

## 6. Tooling Gaps (conventions NOT guaranteed by tools)

| Convention | Current State | Deterministic Enforcement Possible? |
|------------|---------------|-------------------------------------|
| `from manim import *` + Scene + construct | AST check in validate_code() | Already enforced at runtime |
| Dangerous imports | AST walk | Already enforced at runtime |
| Code style (formatting) | None | `ruff format` or `black` |
| Type checking | None | `mypy` (but code is clean enough) |
| Linting (unused imports, etc.) | None | `ruff check` |
| Tests | None | `pytest` (in requirements.txt but unused) |
| Prompt consistency | LLM instruction only | Can't enforce deterministically — skill prose needed |
| 60 FPS, --disable_caching | Hardcoded | Already in code |
| LaTeX strings raw | LLM instruction only | AST check possible for non-raw LaTeX strings |

## 7. External Dependencies

| Service | Purpose | Failure Mode |
|---------|---------|-------------|
| OpenAI API | Code generation (both stages) | Service unavailable → 500 error; 3 retries with simplification |
| Manim CLI | Video rendering | Timeout/crash → 500 error with stderr |
| FFmpeg (via PyAV) | Video encoding | Manim render fails → 500 error |
| LaTeX (TeX Live) | Math rendering in Manim | Missing → Manim renders without LaTeX or fails |
| Cloudflare Tunnel | Public exposure | Tunnel down → external unreachable (local still works) |

## 8. File not found / Not present

- **No `pyproject.toml`** — Python project metadata, tool config (ruff, mypy, pytest) would go here
- **No `.gitignore`** — Should exclude `.env`, `venv/`, `media/videos/`, `__pycache__/`
- **No `manim.cfg`** — Referenced in docs but not committed
- **No `Dockerfile`** — Listed as "next step" in README
- **No CI/CD** — Listed as "next step" in README
- **No `postman_collection.json`** — Referenced in API_CONSUMER.md:217 but not in repo
- **No tests directory** — `pytest` and `httpx` are in requirements.txt but no tests exist
