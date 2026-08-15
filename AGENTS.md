# AGENTS.md — Manim Video Generator API

## Commands
- **Run API locally**: `cd manim-api && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- **Health check**: `curl http://127.0.0.1:8000/`
- **Generate video (curl)**: `curl -X POST http://127.0.0.1:8000/generate-video -H "Content-Type: application/json" -d '{"description": "Show a blue circle", "width": 1920, "height": 1080}'`
- **Render clip via CLI**: `OPENROUTER_API_KEY=... MANIM_HOME=$(pwd) manim-api/venv/bin/python render_clip.py --json '{"prompt":"...","out_dir":"./clips"}'`
- **Validate clip background**: `manim-api/venv/bin/python manim-api/scripts/assert_bg.py <clip.mp4> --expect '#FFFFFF'`
- **Check environment**: `manim-api/venv/bin/python manim-api/scripts/check_env.py`
- **Run tests**: `cd manim-api && python -m pytest` (pytest in requirements.txt, no test files yet)
- **Lint skills**: `python3 .agents/scripts/skill_lint.py`
- **Run skill evals**: `python3 .agents/scripts/run_skill_evals.py [skill-name]`
- **Check provenance staleness**: `python3 .agents/scripts/check_staleness.py`
- **Install deps**: `cd manim-api && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

## Rules (non-obvious, not tooling-guaranteed)

- **Every implementation task goes through `.agents/skills/project-router`** — it asks clarifying questions in Brazilian Portuguese before any code is written.
- **Structured logging**: every log line includes `[request_id]` prefix (8-char hex). The ID flows from middleware → endpoint → services. Pass it as `request_id` param with fallback `"no-request-id"`.
- **Manim code generation is two-stage**: prompt optimizer → code generator. The optimizer enriches, the generator produces code. Three retries with progressive simplification on validation failure.
- **All LLM calls go through OpenRouter** (`services/openrouter_service.py`) using `/chat/completions`; the OpenAI SDK has been removed.
- **Code sanitization happens between extraction and validation**: CYAN→TEAL color fallbacks, `fill_opacity`→`opacity` fix for `add_background_rectangle`, `tip_style` kwarg removal from `add_tip`, and removal of any `config.background_color` / `self.camera.background_color` assignments.
- **Background colour is injected by the harness**: the generated code must never set `config.background_color`; the CLI injects it via the scene preamble.
- **TinyTeX path is resolved**: `_resolve_texlive_bin()` also searches `~/.TinyTeX/bin/**` so `MathTex` finds `dvisvgm`.
- **Every render runs in a temp directory**: `BackgroundRectangle` monkey-patch and `config.background_color` are prepended to every scene. Video discovery scans recursively for newest MP4 by scene name.
- **Never commit**: `.env`, `venv/`, `media/videos/`, `__pycache__/`
- **Settings singleton**: `config.get_settings()` uses `@lru_cache` — changing `.env` requires server restart.

## Skills
Every task goes through `.agents/skills/project-router`. Catalog: `.agents/skills/catalog.md`

## Security
- Dangerous imports blocked in generated code: `os`, `sys`, `subprocess`, `shutil`, `socket`, `urllib`, `requests`, `pickle`, `ctypes`, `multiprocessing`, `pty`
- Dangerous functions blocked: `eval`, `exec`, `open`, `__import__`, `compile`
- Never read/commit: `.env`, `secrets/**`
- Hook guardrails: `.claude/settings.json` blocks `.env` reads and dangerous bash
