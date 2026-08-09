#!/usr/bin/env python3
"""
Skill write gate: blocks Write/Edit on SKILL.md files unless a validation token exists.
The validation token is the existence of a green eval record for that skill.

Exit codes: 0 = allow, 2 = block
"""
import json
import os
import sys
from pathlib import Path

SKILL_DIR = Path(".agents/skills")
EVAL_RECORDS_DIR = Path(".agents/skills/.eval_records")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else ""

    # Only gate SKILL.md files under skills/
    if not path or "SKILL.md" not in path or "skills" not in path:
        sys.exit(0)

    # Determine which skill this belongs to
    skill_path = Path(path)
    skill_name = skill_path.parent.name if skill_path.parent.name != "skills" else None

    if not skill_name or skill_name.startswith("."):
        # Allow writes to non-skill areas
        sys.exit(0)

    # Check if an eval record exists for this skill
    eval_file = EVAL_RECORDS_DIR / f"{skill_name}.json"
    if eval_file.exists():
        try:
            record = json.loads(eval_file.read_text())
            if record.get("last_eval_passed"):
                print(f"[SkillGate] Eval record green for '{skill_name}' — allowing write")
                sys.exit(0)
        except Exception:
            pass

    # No green eval record — but allow if this is initial creation (file doesn't exist yet)
    if not skill_path.exists() if isinstance(skill_path, Path) else True:
        print(f"[SkillGate] Initial creation of '{skill_name}' — allowing write")
        sys.exit(0)

    # Block unvalidated writes
    print(f"[SkillGate] BLOCKING write to {path}: no green eval record for '{skill_name}'")
    print(f"[SkillGate] Run eval suite first: .agents/scripts/run_skill_evals.py {skill_name}")
    sys.exit(2)


if __name__ == "__main__":
    main()
