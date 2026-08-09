---
name: fastapi-app
description: Injects the FastAPI application structure, config patterns, request/response schemas, CORS middleware, structured logging conventions, and Cloudflare Tunnel exposure. Use whenever modifying the API surface, adding middleware, changing config, adjusting request/response models, or touching main.py — even if the user doesn't mention "FastAPI" or "endpoint". Triggers: "endpoint", "route", "middleware", "CORS", "config", "settings", "schema", "request", "response", "main.py", "schemas.py", "config.py", "API surface", "Cloudflare", "tunnel", "deploy".
metadata:
  type: knowledge
  verification_signal: "python3 -c 'import ast; ast.parse(open(\"manim-api/main.py\").read()); from manim-api.config import get_settings; print(\"OK\")' && python3 .agents/scripts/skill_lint.py"
---
# FastAPI Application Structure

## When to use
- You are touching `main.py`, `config.py`, or `schemas.py`
- You need to add a new endpoint
- You are modifying request/response models or validation
- You are changing CORS, middleware, or logging
- You are working on Cloudflare Tunnel setup or deployment
- The user mentions "endpoint", "route", "middleware", "config", "schema", "deploy"

## Injected knowledge

### Application bootstrap

`main.py:24-28` — FastAPI app created with title, description, and version. No lifespan/startup/shutdown handlers. Settings are loaded once at module level via `settings = get_settings()` (line 22).

### Settings pattern

`config.py:5-30` — Pydantic `BaseSettings` with `SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")`. The `extra="ignore"` means unknown env vars are silently dropped — adding a new config field that's missing from .env won't error unless the field has no default.

`@lru_cache` on `get_settings()` (line 28-30) makes it a singleton — only one `Settings` instance is ever created. This means settings are read once at import time and cached. Changing `.env` requires a server restart.

Required vs optional config:
- `openai_api_key: str` — required field (no default, server crashes without it)
- `openai_model: str = "gpt-5.1-codex-max"` — optional
- `app_name: str = "Manim Video Generator API"` — optional
- `debug: bool = False` — optional
- `render_timeout: int = 120` — optional
- `host: str = "0.0.0.0"` — optional
- `port: int = 8000` — optional

### Request/response schemas

`schemas.py` — Four Pydantic models:

- **`VideoRequest`**: `description` (str, 10-2000 chars), `width` (int, 320-3840, optional), `height` (int, 320-3840, optional). Missing width/height default to 1920×1080 in `_resolve_dimensions()` (`main.py:92-95`).
- **`CodeResponse`**: `code`, `scene_name`, `is_valid`, `validation_message` — all str except is_valid (bool).
- **`VideoResponse`**: `success` (bool), `video_base64` (str, optional), `content_type` (str, default "video/mp4"), `scene_name` (str, optional), `error` (str, optional), `render_logs` (str, optional).
- **`HealthResponse`**: `status`, `manim_version`, `openai_model` — all str.

### CORS middleware

`main.py:30-37` — Extremely permissive: `allow_origins=["*"]`, `allow_origin_regex=r".*"`, `allow_methods=["*"]`, `allow_headers=["*"]`, `expose_headers=["*"]`. This is intentional for a public API.

Additionally, a custom middleware at `main.py:40-69` handles:
- Request ID extraction from `x-request-id` header or uuid4 generation
- Perf timing (ms precision)
- Explicit `Access-Control-Allow-Origin` header mirroring (line 54)
- OPTIONS preflight handling (line 47-48)

### Structured logging convention

Every log line includes a `[request_id]` prefix in square brackets. The pattern:
```python
logger.info("[%s] message with context (key=%s)", request_id, value)
```
The request ID is an 8-char hex string from `uuid.uuid4().hex[:8]` (line 42). This ID flows through the entire pipeline: middleware → endpoint → openai_service → manim_executor. Each service function accepts an optional `request_id` parameter with fallback `"no-request-id"`.

Log levels used:
- `logger.info` — normal flow (request received, code generated, render complete)
- `logger.warning` — recoverable failures (invalid code, prompt optimization failed)
- `logger.error` — terminal failures (render failed, exhausted retries)
- `logger.exception` — unexpected exceptions with traceback
- `logger.debug` — low-level details (script path written — only in executor)

### Endpoint patterns

All three POST endpoints follow the same pattern:

1. Extract request ID from `http_request.state.request_id`
2. Resolve width/height via `_resolve_dimensions()`
3. Log incoming request with resolution
4. Call `generate_manim_code()` (async)
5. If code invalid → return error response (or raise HTTPException for file endpoint)
6. Call `execute_manim()` via `asyncio.to_thread()` (non-blocking)
7. If render fails → return error with `render_logs`
8. Return success response

The `/generate-video-file` endpoint differs by raising `HTTPException` on failure instead of returning a `VideoResponse(success=False)` — it needs to return a `Response` for binary data, not a Pydantic model.

### Health check

`main.py:72-89` — GET `/` runs `subprocess.run(["manim", "--version"], ...)` to get the Manim version. If Manim is not installed or crashes, it returns `"unknown"` or `"error"` but still returns 200. The model name comes from config (not a real-time check).

### Cloudflare Tunnel exposure

The app is meant to run behind Cloudflare Tunnel. Key operational notes:
- The API binds to `0.0.0.0` (not localhost) — `config.py:17`
- Cloudflared points to `http://localhost:8000` — `CLOUDFLARE.md:173`
- Start command: `uvicorn main:app --host 0.0.0.0 --port 8000` (or `--reload` for dev)
- Debug mode in `config.py:12` controls `--reload` flag (`main.py:259`)
- No HTTPS handling in the app — TLS is terminated at Cloudflare edge
- The full setup guide is in `CLOUDFLARE.md` (421 lines, authoritative)

### Server entry point

`main.py:252-260` — when `__name__ == "__main__"` (not when imported by uvicorn directly):
```python
uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
```
The `"main:app"` string form is important — it supports `--reload` (the `app=app` object form does not).

## References
- `manim-api/main.py` — Full application (261 lines)
- `manim-api/config.py` — Settings and env loading (31 lines)
- `manim-api/schemas.py` — Pydantic models (46 lines)
- `CLOUDFLARE.md` — Cloudflare Tunnel setup guide (421 lines)
- `API_CONSUMER.md` — External API documentation with base URL, examples, error codes
