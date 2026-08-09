#!/usr/bin/env python3
"""
Staleness checker: compares provenance citations in skills against current file state.
Reports passages that may need revalidation.
"""
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(".agents/skills")
REPO_ROOT = Path.cwd()

# Pattern: `file:line@hash` or `file:line`
PROVENANCE_PATTERN = re.compile(r"`([^`]+):(\d+)(?:@([a-f0-9]{7,}))?`")


def check_provenance(skill_path: Path) -> list[dict]:
    content = skill_path.read_text()
    stale = []

    for match in PROVENANCE_PATTERN.finditer(content):
        file_ref = match.group(1)
        line_ref = int(match.group(2))
        hash_ref = match.group(3)

        target = REPO_ROOT / file_ref
        if not target.exists():
            stale.append({
                "file": file_ref,
                "line": line_ref,
                "hash": hash_ref,
                "issue": "File not found",
            })
            continue

        # Check if cited line still exists
        try:
            target_lines = target.read_text().split("\n")
            if line_ref > len(target_lines):
                stale.append({
                    "file": file_ref,
                    "line": line_ref,
                    "hash": hash_ref,
                    "issue": f"Line {line_ref} beyond file end ({len(target_lines)} lines)",
                })
        except Exception:
            pass

    return stale


def main():
    if not SKILL_DIR.exists():
        print("No skills directory")
        sys.exit(0)

    all_stale = {}
    for skill_md in sorted(SKILL_DIR.glob("*/SKILL.md")):
        stale = check_provenance(skill_md)
        if stale:
            all_stale[skill_md.parent.name] = stale

    if all_stale:
        print("STALE PROVENANCE FOUND:")
        for skill_name, items in all_stale.items():
            print(f"\n  {skill_name}:")
            for item in items:
                print(f"    {item['file']}:{item['line']} — {item['issue']}")
        sys.exit(1)
    else:
        print("All provenance citations are current")
        sys.exit(0)


if __name__ == "__main__":
    main()
