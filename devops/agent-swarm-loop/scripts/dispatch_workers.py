#!/usr/bin/env python3
"""
dispatch_workers.py — build CORRECT swarm worker dispatch specs.

Encodes the lessons from the first run that broke the swarm:
  1. ALWAYS attach skills=["agent-swarm-loop"] so each worker gets the interface
     contract + github-workspace code. A blind dispatch left every worker blind.
  2. RAM / concurrency: `delegate_task` batch max is 3 (max_concurrent_children).
     LOCAL backend on a small host (<2GB) OOM-killed >=2 of 4 parallel workers.
     -> local: serialize (one at a time) OR cap at 2 concurrent.
     -> modal: batch up to 3 (workers run in sandboxes, host RAM irrelevant).
  3. REDACTION SAFE: the worker prompt must NOT inline the private key. Tell the
     worker the key is MOUNTED at /root/.hermes/<keystore>.json and to read its
     role's entry out of it. Never put PEM text in tool-call context.

This module is imported by the orchestrator (it runs inside the Hermes agent).
It does NOT call delegate_task itself — it returns specs the orchestrator loops
over with delegate_task(..., skills=["agent-swarm-loop"], role="leaf").

Usage (inside an execute_code / orchestrator script):
    import sys; sys.path.insert(0, "<skill dir>/scripts")
    from dispatch_workers import plan_dispatch
    plan = plan_dispatch(backend="modal", prompts={"flight-physicist": "/path/p1.txt", ...},
                         keystore="/root/.hermes/swarm_tunnel_derby_keys.json")
    for call in plan:
        delegate_task(goal=call["goal"], context=call["context"],
                      skills=call["skills"], role="leaf")
"""
import json
from pathlib import Path
from typing import Dict, List


def plan_dispatch(backend: str, prompts: Dict[str, str],
                  keystore: str = "/root/.hermes/swarm_tunnel_derby_keys.json",
                  goal_max_turns: int = 40) -> List[dict]:
    """Return a list of delegate_task-ready call dicts, split into safe batches."""
    assert backend in ("local", "modal"), backend
    batch = 1 if (backend == "local") else 3
    if backend == "local":
        batch = 1  # safest on small hosts; bump to 2 only if host RAM > 2GB

    calls = []
    for role, pfile in prompts.items():
        calls.append({
            "goal": f"Build {role} module for Tunnel Derby swarm. Read {pfile} "
                    f"(full spec, interface contract, GIT/SSH-from-mount steps). "
                    f"Autonomously write your module, push your branch to "
                    f"git@github.com:ohrbit/FABLE-SHOWCASE.git, report "
                    f"branch+summary+fitness signal. English, <200 words. "
                    f"BACKEND IS {backend.upper()}.",
            "context": (
                f"You are the '{role}' expert in an agent-swarm building "
                f"'Tunnel Derby'. Coordinate only via the ES-module interface "
                f"contract (no shared FS). Your SSH deploy key is MOUNTED at "
                f"{keystore} — read it, extract the JSON value for '{role}', write "
                f"it to ~/.ssh/id_ed25519 (chmod 600). Do NOT expect the key in "
                f"this text. The agent-swarm-loop skill is loaded for context."),
            "skills": ["agent-swarm-loop"],
            "role": "leaf",
            "goal_max_turns": goal_max_turns,
        })
    return _batch(calls, batch)


def _batch(calls: List[dict], n: int) -> List[List[dict]]:
    return [calls[i:i + n] for i in range(0, len(calls), n)]


def main():
    """CLI: print the plan (the orchestrator does the real dispatch)."""
    import argparse, sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["local", "modal"], default="local")
    ap.add_argument("--prompts", required=True, help="JSON map role->prompt_file")
    ap.add_argument("--keystore", default="/root/.hermes/swarm_tunnel_derby_keys.json")
    a = ap.parse_args()
    prompts = json.loads(a.prompts)
    plan = plan_dispatch(a.backend, prompts, keystore=a.keystore)
    print(f"backend={a.backend} batches={len(plan)} workers={sum(len(b) for b in plan)}")
    for i, b in enumerate(plan):
        print(f"  batch {i+1}: {[c['context'].split(chr(39))[1] for c in b]}")


if __name__ == "__main__":
    main()
