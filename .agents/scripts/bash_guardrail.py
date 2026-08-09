#!/usr/bin/env python3
"""
Bash guardrail: blocks dangerous commands.
Exit codes: 0 = allow, 2 = block
"""
import sys
import re

DANGEROUS_PATTERNS = [
    # Recursive force-delete at root or home
    (r"\brm\s+-rf\s+(~|/|/home|/root|/etc|/var|/usr|/bin|/sbin)\b", "rm -rf on critical path"),
    # Git history rewrite (destructive)
    (r"\bgit\s+(push\s+--force.*origin\s+(main|master)|reset\s+--hard\s+origin)", "destructive git operation on main/master"),
    # Fork bombs
    (r":\(\)\s*\{[^}]*:[^}]*\|[^}]*&[^}]*}", "fork bomb pattern"),
    # Raw /dev/sda writes
    (r"\bdd\s+if=.*of=/dev/[hs]d[a-z]", "dd write to raw block device"),
    # eval on arbitrary input (suspicious)
    (r"\beval\s+", "eval command"),
]

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if not cmd:
        sys.exit(0)

    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            print(f"[BashGuard] BLOCKING dangerous command: {description}")
            print(f"[BashGuard] Command: {cmd[:200]}")
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
