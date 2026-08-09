# Skill Map: Manim Video Generator API

> **Date:** 2026-08-09 | **Based on:** project-analysis.md (commit `9aee03c`)

## 1. Skill Catalog

### 1.1 Router

| Field | Value |
|-------|-------|
| **name** | `project-router` |
| **type** | router |
| **description** | Routes every implementation task in this codebase to the correct skills BEFORE any step. Use whenever the user asks for any change, fix, feature, analysis, or refactor, even if they don't mention skills. |
| **triggers** | Always-on; invoked before any task step. |
| **verification** | Routing evals: 10 queries that MUST trigger specific skills + 5 near-misses that must NOT. |

### 1.2 Knowledge Skills

#### K1: manim-code-gen
| Field | Value |
|-------|-------|
| **name** | `manim-code-gen` |
| **type** | knowledge |
| **description** | Injects the prompt engineering rules, code validation pipeline, AST-based security checks, and code sanitization quirks of this project's Manim CE 0.19.0 code generator. Use whenever generating, modifying, or debugging Manim code generation, prompts, validation, or sanitization logic — even if the user doesn't mention "prompts" or "openai_service". |
| **triggers** | "generate code", "prompt", "validation", "sanitize", "few-shot", "code generation", "openai_service", "prompts.py", "Manim code", "regenerate", "fix code gen", "add few-shot" |
| **verification** | `python3 -c "import ast; from manim-api.services.openai_service import validate_code, sanitize_code, extract_code, get_scene_name; print('imports OK')"` plus unit evals on validate_code (valid code → True, missing import → False, dangerous import → False) |

#### K2: manim-rendering
| Field | Value |
|-------|-------|
| **name** | `manim-rendering` |
| **type** | knowledge |
| **description** | Injects knowledge of the headless Manim CLI executor: tempfile isolation, BackgroundRectangle monkey-patch, TeX Live path resolution, video file discovery strategy, and CLI argument conventions. Use whenever working on rendering, video output, Manim execution, or executor-related bugs — even if the user doesn't mention "executor" or "manim_executor". |
| **triggers** | "render", "manim execute", "video output", "timeout", "CLI", "manim_executor", "BackgroundRectangle", "TeX Live", "LaTeX path", "find video", "subprocess" |
| **verification** | `manim --version` (exit 0), `manim checkhealth` (diagnostic), plus structure check `python3 -c "from manim-api.services.manim_executor import execute_manim, find_video, RenderResult; print('imports OK')"` |

#### K3: fastapi-app
| Field | Value |
|-------|-------|
| **name** | `fastapi-app` |
| **type** | knowledge |
| **description** | Injects the FastAPI application structure, config patterns, request/response schemas, CORS middleware, structured logging conventions, and Cloudflare Tunnel exposure. Use whenever modifying the API surface, adding middleware, changing config, adjusting request/response models, or touching main.py — even if the user doesn't mention "FastAPI" or "endpoint". |
| **triggers** | "endpoint", "route", "middleware", "CORS", "config", "settings", "schema", "request", "response", "main.py", "schemas.py", "config.py", "API surface", "Cloudflare", "tunnel", "deploy" |
| **verification** | `python3 -c "from manim-api.config import get_settings; s = get_settings(); print(s.app_name)"` (config loads), `python3 -c "import ast; ast.parse(open('manim-api/main.py').read()); print('syntax OK')"` |

### 1.3 Meta Skills

#### M1: meta-skill-evolution
| Field | Value |
|-------|-------|
| **name** | `meta-skill-evolution` |
| **type** | meta |
| **description** | Handles the creation and update of skills. Given important-and-verified information or a new domain area, decides between updating an existing skill via the memory pipeline (direct SKILL.md edit), proposing a new skill draft for human review, or discarding. Never publishes without verification. Use when the project-router finds no skill covering a task, or when task completion produces important verified knowledge. |
| **triggers** | "new skill", "update skill", "no skill for", "create a skill", "this knowledge should be saved", "remember this for next time" |
| **verification** | Skill linter (`python3 .agents/scripts/skill_lint.py`), eval suite for target skill |

#### M2: meta-skill-consolidate
| Field | Value |
|-------|-------|
| **name** | `meta-skill-consolidate` |
| **type** | meta |
| **description** | Periodic garbage collection for skills: deduplicates redundant content across skills, revalidates stale provenance, resolves contradictions, enforces token budgets, and retires obsolete content. Every consolidation runs regression gating before promoting. Deletions require second-opinion review. Use on explicit "consolidate skills", "clean up skills", "GC skills", or when skills have grown beyond 5k tokens. |
| **triggers** | "consolidate", "GC", "deduplicate skills", "clean up skills", "stale", "token budget" |
| **verification** | Regression suite (all per-skill eval sets), skill linter |

## 2. Dependency / Composition Graph

```
project-router (always first)
  ├── loads catalog.md to select skills
  ├── selects 1+ of:
  │     ├── manim-code-gen (knowledge)
  │     ├── manim-rendering (knowledge)
  │     └── fastapi-app (knowledge)
  ├── on unknown domain → meta-skill-evolution
  └── on task completion → runs <evolution> for each involved task skill

meta-skill-evolution
  ├── reads/writes any skill SKILL.md
  └── uses meta-skill-consolidate (on conflict/staleness)

meta-skill-consolidate
  ├── reads all SKILL.md files
  ├── runs per-skill eval suites
  └── emits diff for review
```

**Parallelism:** Knowledge skills are independent — when multiple domains are touched, their knowledge can be loaded in parallel via isolated-context subagents.

## 3. Granularity Justification

### Why NOT split further

| Candidate split | Reason to merge |
|-----------------|-----------------|
| Separate `prompt-engineering` from `code-validation` | Both live in `openai_service.py` and `prompts.py`, tightly coupled (prompts affect what validation catches). Splitting would duplicate the context that validation rules depend on prompt rules. |
| Separate `config` from `fastapi-app` | Config is 31 lines. The settings singleton pattern is trivially inferable. |
| Separate `cloudflare-deploy` from `fastapi-app` | Tunnel setup is operational, not code. The knowledge lives in `CLOUDFLARE.md` which Claude can read directly. The app skill just points to it. |
| Separate `schemas` from `fastapi-app` | Schemas are 46 lines of Pydantic models. Their constraints are self-documenting. |
| Separate "style" skill | The only non-standard convention is structured logging `[request_id]` — visible in every source file. All other conventions are standard Python 3.11+. |

### Why NOT merge further

| Candidate merge | Reason to split |
|-----------------|-----------------|
| `manim-code-gen` + `manim-rendering` into one skill | These are separate pipeline stages with separate failure modes, separate services, and separate knowledge. The code gen skill would bloat past 5k tokens if it also covered rendering. |
| All knowledge into one monolithic skill | Would exceed the skill token budget (~5k tokens) and degrade routing precision. The router needs specific triggers per domain. |
| Meta skills into one | Evolution (creating new) vs consolidation (cleaning existing) are different workflows with different safety requirements. Consolidation needs deletion consensus; evolution needs proposal review. |

### Skill count target

- **6 skills total** (router + 3 knowledge + 2 meta)
- This is well under the "skill sprawl" threshold (~15+ skills where routing degrades)
- Each knowledge skill targets ~1,400–3,000 tokens (well under the 5k budget)
- The catalog.md will be ~50 lines — fast to load

## 4. Per-Skill Verification Signal Detail

| Skill | Signal | Runs Without API Key? | Runs Without Manim? |
|-------|--------|----------------------|---------------------|
| `project-router` | Routing evals (text matching) | Yes | Yes |
| `manim-code-gen` | `python3 -c "import manim-api.services.openai_service"` + AST parse | Yes (validation only) | Yes |
| `manim-rendering` | `manim --version` + `python3 -c "import manim-api.services.manim_executor"` | Yes | Needs `manim` CLI |
| `fastapi-app` | `python3 -c "from manim-api.config import get_settings"` (fails without .env, but syntax check passes) | Yes (syntax) | Yes |
| `meta-skill-evolution` | Skill linter on output | Yes | Yes |
| `meta-skill-consolidate` | Skill linter + full regression suite | Yes | Yes |

## 5. Skill Linter Specification

A mandatory script at `.agents/scripts/skill_lint.py` enforces:
1. **Frontmatter validity**: `name` matches `[a-z0-9-]+`, ≤ 64 chars; `description` ≤ 1024 chars, third person, includes trigger keywords
2. **Frontmatter completeness**: contains `name`, `description`, `metadata.type`
3. **Body length**: ≤ 500 lines / ~5,000 tokens (warning at 400 lines, error at 500)
4. **Provenance format**: every knowledge item with `file:line@hash` or `file:line` citation
5. **No dates/changelogs**: rejects lines matching date patterns in body
6. **No ALL_CAPS imperatives**: warns on `MUST`, `ALWAYS`, `NEVER`, `DO NOT` without explanation

The linter is the deterministic enforcement tool — run by the write-gate hook before any SKILL.md write is allowed.
