#!/usr/bin/env python3
"""
Stop validation gate: prevents the agent from terminating until all bootstrap phases pass.
Reads .agents/skills/.bootstrap-state.json; exits 2 if phases are incomplete.
Guard: stop_hook_active flag prevents infinite loops.
"""
import json
import sys
from pathlib import Path

STATE_FILE = Path(".agents/skills/.bootstrap-state.json")

def main():
    if not STATE_FILE.exists():
        print("[StopGate] Bootstrap state file not found — allowing Stop (no mission in progress)")
        sys.exit(0)

    try:
        state = json.loads(STATE_FILE.read_text())
    except Exception:
        print("[StopGate] Could not parse bootstrap state — allowing Stop")
        sys.exit(0)

    phases = state.get("phases", [])
    incomplete = [p for p in phases if not p.get("done") or not p.get("gate_passed")]

    if not incomplete:
        print("[StopGate] All phases complete — allowing Stop")
        sys.exit(0)

    # Guard: if stop_hook_active, we've already blocked once — allow termination
    if state.get("stop_hook_active"):
        print("[StopGate] WARNING: stop_hook_active is set — preventing infinite loop, allowing Stop")
        print("[StopGate] Incomplete phases:")
        for p in incomplete:
            print(f"  Phase {p['id']}: {p['name']} (done={p.get('done')}, gate={p.get('gate_passed')})")
        sys.exit(0)

    # Set flag and persist
    state["stop_hook_active"] = True
    STATE_FILE.write_text(json.dumps(state, indent=2))

    print("[StopGate] BLOCKING Stop — incomplete phases:")
    for p in incomplete:
        print(f"  Phase {p['id']}: {p['name']} (done={p.get('done')}, gate={p.get('gate_passed')})")
    print("[StopGate] Continue working to complete all phases, then Stop will be allowed.")
    sys.exit(2)


if __name__ == "__main__":
    main()
