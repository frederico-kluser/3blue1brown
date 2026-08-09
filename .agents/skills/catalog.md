# Skills Catalog — Manim Video Generator API

> Auto-generated index of all available skills. Load this to select the right skills for a task.
> Regenerate with: `python3 .agents/scripts/skill_lint.py` (also validates all skills).

## Router (always first)

| Skill | Description |
|-------|-------------|
| [project-router](project-router/SKILL.md) | Routes every implementation task to the correct skills BEFORE any step. Portuguese user-facing questions, creates TASK_PLAN.md. |

## Knowledge Skills

| Skill | Domain | When to load |
|-------|--------|-------------|
| [manim-code-gen](manim-code-gen/SKILL.md) | Prompt engineering, code validation, sanitization | Touching prompts.py, openai_service.py; debugging code generation |
| [manim-rendering](manim-rendering/SKILL.md) | Manim CLI execution, video output, tempfile isolation | Touching manim_executor.py; debugging render failures |
| [fastapi-app](fastapi-app/SKILL.md) | API structure, config, schemas, middleware, Cloudflare | Touching main.py, config.py, schemas.py; adding endpoints |

## Meta Skills

| Skill | Description | When to invoke |
|-------|-------------|---------------|
| [meta-skill-evolution](meta-skill-evolution/SKILL.md) | Creates or updates skills when important verified knowledge arises | No skill covers a task; important verified info to persist |
| [meta-skill-consolidate](meta-skill-consolidate/SKILL.md) | Periodic GC: dedup, revalidate, resolve contradictions, trim | Skills exceed token budget; "consolidate skills" |

## Quick Select by File Touched

| If you touch... | Load... |
|-----------------|---------|
| `prompts.py` | manim-code-gen |
| `services/openai_service.py` | manim-code-gen |
| `services/manim_executor.py` | manim-rendering |
| `main.py` | fastapi-app |
| `config.py` | fastapi-app |
| `schemas.py` | fastapi-app |
| `CLOUDFLARE.md` | fastapi-app |
| Multiple files | All matching domains (parallel load) |

## Quick Select by Task Type

| Task type | Primary skill | Secondary |
|-----------|---------------|-----------|
| Add new few-shot example | manim-code-gen | — |
| Fix code generation bug | manim-code-gen | — |
| Add new validation rule | manim-code-gen | — |
| Fix render timeout/error | manim-rendering | — |
| Adjust video quality/resolution | manim-rendering | fastapi-app (schemas) |
| Add new API endpoint | fastapi-app | manim-code-gen (if it uses generation) |
| Change CORS/middleware | fastapi-app | — |
| Configure Cloudflare Tunnel | fastapi-app | — |
| Add config field | fastapi-app | — |
| Unknown / new domain | Forward to meta-skill-evolution | — |
