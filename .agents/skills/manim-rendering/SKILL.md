---
name: manim-rendering
description: Injects knowledge of the headless Manim CLI executor: tempfile isolation, BackgroundRectangle monkey-patch, TeX Live path resolution, video file discovery strategy, and CLI argument conventions. Use whenever working on rendering, video output, Manim execution, or executor-related bugs — even if the user doesn't mention "executor" or "manim_executor". Triggers: "render", "manim execute", "video output", "timeout", "CLI", "manim_executor", "BackgroundRectangle", "TeX Live", "LaTeX path", "find video", "subprocess".
metadata:
  type: knowledge
  verification_signal: "manim --version && python3 -c 'from manim-api.services.manim_executor import execute_manim, find_video, RenderResult; print(\"OK\")' && python3 .agents/scripts/skill_lint.py"
---
# Manim Rendering

## When to use
- You are touching `services/manim_executor.py`
- You need to debug why a video wasn't produced
- You are adjusting render quality, FPS, resolution, or timeout
- You are investigating Manim CLI errors or LaTeX failures
- You are modifying the render pipeline (temp directories, env setup)
- The user mentions "render", "video", "timeout", "CLI", "executor", "subprocess"

## Injected knowledge

### Tempfile isolation

`manim_executor.py:86-106` — EVERY render runs in a fresh `tempfile.TemporaryDirectory`. The scene script is written to `scene.py` inside that directory, and `--media_dir` points to a `media/` subdirectory within it. This means:
- Concurrent renders cannot collide (separate temp dirs)
- All artifacts are auto-cleaned when the context manager exits
- Never reference absolute paths in generated code — the CWD is the temp dir

### BackgroundRectangle monkey-patch

`manim_executor.py:29-34` — A critical workaround is prepended to EVERY scene script:

```python
from manim.mobject.geometry.shape_matchers import BackgroundRectangle
if not hasattr(BackgroundRectangle, "tex_string"):
    BackgroundRectangle.tex_string = ""
```

This exists because Manim CE 0.19.0 has a bug where `BackgroundRectangle` expects a `tex_string` attribute that may not exist. Without this patch, any scene using `BackgroundRectangle` (commonly used for text readability over graphics) will crash. The patch is applied at line 90: `script_path.write_text(f"{BACKGROUND_RECTANGLE_PATCH}\n\n{code}")`.

### TeX Live path resolution

`manim_executor.py:16-27` — On macOS, TeX Live is typically installed to `~/texlive/` but not on the default PATH. The `_resolve_texlive_bin()` function probes `~/texlive/*/bin/*` (sorted reverse to prefer newest version) and finds the first directory. This is added to the subprocess PATH via `_build_env()` at line 61-66.

If no TeX Live is found, `TEXLIVE_BIN` is `None` and the subprocess runs with the system PATH. This means LaTeX-dependent Manim features (MathTex, Tex) may fail silently or fall back.

### Manim CLI invocation

`manim_executor.py:225-235` — The base CLI command (before renderer-specific flags):

```
manim render -r W,H --fps 60 --media_dir <tmpdir>/media --disable_caching --write_to_movie <script.py> <SceneName>
```

Key details:
- `manim render` (CE 0.19.0+ syntax, not `manim -pql` legacy)
- `-r W,H` — resolution (e.g., `1920,1080`)
- `--fps 60` — hardcoded, not configurable via .env
- `--disable_caching` — prevents stale cache issues across renders
- `--write_to_movie` — required for OpenGL renderer to produce MP4 output. Cairo also supports it (safe default). Without this flag, the OpenGL renderer animates to screen only and produces no video file, causing "Video file not found after render". Verified against Manim CE v0.20.1 `manim_executor.py:225@922e47d`
- Quality flag (`-ql/-qh`) is NOT used — resolution is explicit
- The scene name is a positional argument, not a flag
- When `settings.manim_renderer` resolves to `"opengl"`, `--renderer=opengl` is inserted at position 2 (after `manim render`)
- When OpenGL render fails and `settings.manim_renderer_fallback=True`, the command is retried without `--renderer=opengl` (defaults to Cairo)

### GPU renderer detection and fallback

`manim_executor.py:70-118` — `_detect_gpu_renderer()` probes for GPU hardware before checking Manim CLI support:
1. Hardware probes (Linux): `nvidia-smi -L` (NVIDIA GPU) or `glxinfo -B` (any OpenGL-capable GPU)
2. If no GPU hardware found → returns `False` (skip OpenGL entirely)
3. If GPU hardware found → checks `manim render --renderer=opengl --help` exit code
4. Both required for `True` — having a GPU without Manim OpenGL support is not enough

`manim_executor.py:120-130` — `_resolve_renderer()` maps config to renderer choice:
- `"cairo"` or `"opengl"` → passes through directly
- `"auto"` (default) or invalid value → calls `_detect_gpu_renderer()`

`manim_executor.py:252-265` — Fallback logic in `execute_manim()`:
- If OpenGL render fails AND `manim_renderer_fallback=True` → retries with Cairo
- Fallback covers all failure modes: non-zero exit, timeout, video not found
- The retry uses `base_cmd` without `--renderer` flag (Cairo is default)

### Video file discovery

`manim_executor.py:47-58` — After rendering, Manim outputs MP4 files to unpredictable quality-named subdirectories (e.g., `media/videos/scene/480p15/SceneName.mp4`). The `find_video()` function:
1. Searches `media/videos/` recursively for `*.mp4`
2. Sorts by modification time (newest first)
3. First checks: does the filename contain the scene name?
4. Falls back to the most recent MP4 overall
5. If nothing found, returns `None` → render is reported as failed

This is fragile. If Manim changes its output directory structure, video discovery breaks.

### Render result structure

`manim_executor.py:37-44` — `RenderResult` is a dataclass:
- `success: bool`
- `video_path: str | None` — filesystem path to the MP4
- `video_base64: str | None` — base64-encoded video bytes
- `stdout: str` — Manim CLI stdout
- `stderr: str` — Manim CLI stderr
- `error: str | None` — human-readable error message

### Timeout and error handling

`manim_executor.py:117-127` — The subprocess has a `timeout=timeout` parameter (default 120s from `config.py:15`). On timeout:
- A `subprocess.TimeoutExpired` is caught
- Returns `RenderResult(success=False, error="Render timeout after {timeout} seconds")`
- The partial stdout/stderr from the timeout exception is preserved for debugging

Non-timeout failures (non-zero exit code) return `RenderResult(success=False, error="Manim render failed")` with full stdout/stderr. The caller (main.py lines 155-179) logs stderr at ERROR level if the render fails.

### Caller integration

In `main.py`, rendering runs via `asyncio.to_thread()` (line 155) to avoid blocking the event loop. This means:
- The GIL is held during the entire render
- Multiple concurrent renders run in separate threads but share CPU
- The API_CONSUMER.md recommends 6-8 concurrent max on the Mac mini M1

## References
- `manim-api/services/manim_executor.py` — Full executor implementation (157 lines)
- `manim-api/main.py:155-179` — Render integration in /generate-video endpoint
- `manim-api/config.py:15` — `RENDER_TIMEOUT` default (120s)

## Evolution

On task completion, if this skill was involved in the work, run the memory pipeline (see `meta-skill-evolution`):

1. **Importance**: Is the new information non-obvious, non-inferable, non-volatile, and does it change how future rendering tasks should be done?
2. **Verification**: Was it confirmed by a green test/lint/eval OR explicit user confirmation? Without external signal → discard.
3. **Conflict detection**: Does it contradict existing passages? If so, REPLACE, don't append.
4. **Gating**: Run `python3 .agents/scripts/skill_lint.py` and `python3 .agents/scripts/run_skill_evals.py manim-rendering`. Discard on regression.
5. **Update**: Edit THIS file directly (no learnings files). Keep under 500 lines. Git commit separately.

If nothing important and verified was learned, write nothing — that's the healthy default.
