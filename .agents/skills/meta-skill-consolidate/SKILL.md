---
name: meta-skill-consolidate
description: Scans all skills periodically to deduplicate redundant content, revalidate stale provenance, resolve contradictions, enforce token budgets, and retire obsolete content. Every consolidation runs regression gating before promoting. Deletions require second-opinion review. Use on explicit "consolidate skills", "clean up skills", "GC skills", or when skills have grown beyond 5k tokens. Triggers: "consolidate", "GC", "deduplicate", "clean up skills", "stale", "token budget".
metadata:
  type: meta
  verification_signal: "python3 .agents/scripts/skill_lint.py && python3 .agents/scripts/run_skill_evals.py"
---
# Meta-Skill: Consolidation (GC)

## When to use
- Explicit: user says "consolidate skills", "GC skills", "clean up skills"
- Trigger: any skill exceeds 400 lines (warning threshold)
- Periodic: after ~10-15 task completions, check for staleness
- Never: run automatically without user awareness (deletions need review)

## Consolidation workflow

### 1. Scan
Run `python3 .agents/scripts/skill_lint.py` to get current state. Read all SKILL.md files.

### 2. Deduplicate
Find redundant content across skills by pattern-key (same rule described in multiple skills). For each duplicate:
- Keep the most authoritative/domain-specific version
- Replace the other with a cross-reference: "See also: [[other-skill-name]], section X"
- If equal authority, keep in the skill most likely to be loaded first

### 3. Revalidate provenance
For each knowledge item with a `file:line@hash` citation:
- Check if the cited file still exists at that line
- If the hash changed (file was modified), the knowledge may be stale
- Mark stale passages with `[STALE — revalidate against <file>:<line>]`
- Revalidate against the current code: is the claim still true?
- If still true → update the hash
- If no longer true → REPLACE with corrected knowledge or REMOVE

### 4. Resolve contradictions
Compare all skills for conflicting rules. For each conflict:
- Determine which is current (check the source code)
- Keep the correct one, remove the wrong one
- If both are wrong → replace with corrected knowledge
- If the conflict cannot be resolved → flag for human review

### 5. Enforce token budget
For each skill exceeding 400 lines:
- Move long reference material to `references/*.md`
- Trim verbose explanations (keep the WHY, cut the filler)
- Split overly broad skills (if one skill covers 3+ unrelated domains)
- If trimming is impossible without losing critical context → flag for human review

### 6. Regression gate
Before promoting ANY changes:
```bash
python3 .agents/scripts/skill_lint.py        # Must pass
python3 .agents/scripts/run_skill_evals.py    # Must pass (no regressions)
```
If any eval regresses (correct→wrong flip), REVERT that specific change.

### 7. Emit diff for review
- Consolidation changes are emitted as a diff (not auto-committed)
- Deletions require a SECOND-OPINION subagent review (fresh context) before proceeding
- The second-opinion reviewer checks: (a) is the deleted content truly obsolete? (b) does any other skill depend on it? (c) is there a test/edge case that the deleted content covered?
- Only after consensus (main agent + reviewer agree) can the deletion proceed
- High-impact structural rewrites require explicit user confirmation

### 8. Commit
Consolidation changes are a single, descriptive git commit:
```
chore: consolidate skills — dedup N items, revalidate M stales, retire K obsolete
```

## Deletion safeguards
- Never delete a skill without the second-opinion review
- Never delete `project-router` (breaks the routing system)
- Never delete `catalog.md` (removes the skill index)
- Never delete `.bootstrap-state.json` or bootstrap artifacts
- If a skill is retired, check catalog.md for references and update them

## Staleness detection script
Run: `python3 .agents/scripts/check_staleness.py`
This script compares each provenance citation against the current file state and reports passages that may need revalidation. See `scripts/check_staleness.py` for the algorithm.
