#!/usr/bin/env python3
"""
Skill linter: validates SKILL.md files against authoring rules.
Enforces frontmatter, body length, provenance, and hygiene rules.
Exit codes: 0 = pass, 1 = warnings only, 2 = errors found
"""
import re
import sys
from pathlib import Path


SKILL_DIR = Path(".agents/skills")
MAX_BODY_LINES = 500
WARN_BODY_LINES = 400
MAX_NAME_LEN = 64
MAX_DESC_LEN = 1024


def lint_skill(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    skill_name = path.parent.name
    content = path.read_text()
    lines = content.split("\n")

    # --- Frontmatter checks ---
    if not content.startswith("---"):
        errors.append(f"{skill_name}: Missing frontmatter (must start with ---)")
        return errors, warnings

    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{skill_name}: Malformed frontmatter (need opening and closing ---)")
        return errors, warnings

    frontmatter = parts[1]
    body = parts[2]

    if "name:" not in frontmatter:
        errors.append(f"{skill_name}: Missing 'name' in frontmatter")
    if "description:" not in frontmatter:
        errors.append(f"{skill_name}: Missing 'description' in frontmatter")
    if "metadata:" not in frontmatter:
        errors.append(f"{skill_name}: Missing 'metadata' in frontmatter")

    # Name validation
    name_match = re.search(r"name:\s*(\S+)", frontmatter)
    if name_match:
        name = name_match.group(1)
        if len(name) > MAX_NAME_LEN:
            errors.append(f"{skill_name}: name '{name}' exceeds {MAX_NAME_LEN} chars")
        if not re.match(r"^[a-z0-9-]+$", name):
            errors.append(f"{skill_name}: name '{name}' must be lowercase letters/numbers/hyphens only")
        if name != skill_name:
            errors.append(f"{skill_name}: name '{name}' does not match directory name '{skill_name}'")

    # Description validation
    desc_match = re.search(r"description:\s*(.+)", frontmatter)
    if desc_match:
        desc = desc_match.group(1).strip()
        if len(desc) > MAX_DESC_LEN:
            errors.append(f"{skill_name}: description too long ({len(desc)} > {MAX_DESC_LEN})")
        # Check third person (heuristic: starts with verb in third person or "Injects", "Routes", "Handles", etc.)
        third_person_starters = [
            "Injects", "Routes", "Handles", "Provides", "Contains", "Manages",
            "Validates", "Creates", "Updates", "Proposes", "Scans", "Runs",
        ]
        if not any(desc.startswith(s) for s in third_person_starters):
            warnings.append(f"{skill_name}: description may not be in third person")

    # Metadata type
    type_match = re.search(r"type:\s*(\S+)", frontmatter)
    if type_match:
        mtype = type_match.group(1)
        valid_types = {"knowledge", "task", "router", "meta"}
        if mtype not in valid_types:
            errors.append(f"{skill_name}: metadata.type '{mtype}' not in {valid_types}")

    # --- Body checks ---
    body_lines = body.strip().split("\n")
    if len(body_lines) > MAX_BODY_LINES:
        errors.append(f"{skill_name}: body too long ({len(body_lines)} lines > {MAX_BODY_LINES} max)")
    elif len(body_lines) > WARN_BODY_LINES:
        warnings.append(f"{skill_name}: body approaching limit ({len(body_lines)} lines > {WARN_BODY_LINES} warning)")

    # Check for dates/changelogs in body
    date_pattern = re.compile(r"\b(20\d{2}[-/]\d{2}[-/]\d{2}|changelog|last.updated|version\s+history)\b", re.IGNORECASE)
    for i, line in enumerate(body_lines):
        if date_pattern.search(line) and not line.strip().startswith(">"):
            errors.append(f"{skill_name}:{i+1}: Date/changelog in body — use git history instead")

    # Check for unexplained ALL_CAPS imperatives
    caps_imperative = re.compile(r"\b(MUST|ALWAYS|NEVER|DO NOT|REQUIRED)\b")
    for i, line in enumerate(body_lines):
        if caps_imperative.search(line):
            stripped = line.strip()
            if not stripped.startswith("#") and "why" not in stripped.lower() and "because" not in stripped.lower():
                warnings.append(f"{skill_name}:{i+1}: ALL_CAPS imperative without explanation: {stripped[:80]}")

    # Check for empty body
    if not body.strip():
        errors.append(f"{skill_name}: Body is empty")

    return errors, warnings


def main():
    if not SKILL_DIR.exists():
        print("No skills directory found")
        sys.exit(0)

    all_errors: list[str] = []
    all_warnings: list[str] = []

    for skill_md in sorted(SKILL_DIR.glob("*/SKILL.md")):
        errs, warns = lint_skill(skill_md)
        all_errors.extend(errs)
        all_warnings.extend(warns)

    for e in all_errors:
        print(f"ERROR: {e}")
    for w in all_warnings:
        print(f"WARNING: {w}")

    if all_errors:
        print(f"\n{len(all_errors)} error(s), {len(all_warnings)} warning(s)")
        sys.exit(2)
    elif all_warnings:
        print(f"\n0 errors, {len(all_warnings)} warning(s)")
        sys.exit(1)
    else:
        print("All skills pass linting")
        sys.exit(0)


if __name__ == "__main__":
    main()
