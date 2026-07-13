# Team Spec — how the Orchestrator invents a dynamic team

Unlike `jit-agent-teams` (fixed gs-ui/engine/gfx), the swarm loop invents roles
per task. Use this spec to draft the team before spawning.

## Team-Spec template (fill in PHASE 2)
```
PROJECT: <name>
DOMAIN: <web-api | graphics-sim | ml | data | cli-tool | ...>
GOAL: <one sentence deliverable>
FITNESS: <weights from PHASE 0>

EXPERTS (invented for this task — 2 to 5):
  1. <role-a>  — owns <sub-problem>, success = <concrete signal>
  2. <role-b>  — owns <sub-problem>, success = <concrete signal>
  3. <role-c>  — owns <sub-problem>, success = <concrete signal>
  (roles emerge from decomposing GOAL; not a fixed set)

COORDINATION:
  - shared repo: <owner>/<repo>, base branch: <base>
  - each expert → branch feat/<round>-<role> → PR → fitness gate
  - merge worker assembles + evaluates

ROUNDS: until fitness plateau (default stop: 2 rounds w/ delta<0.01)
```

## How to decompose into roles
- Split by **sub-problem ownership**, not by tech layer (unless the task is
  inherently layered).
- Each role MUST have a **concrete, evaluable success signal** tied to the
  chosen fitness metric — otherwise selection can't score it.
- Avoid overlapping ownership (two experts editing the same file → merge hell).
  If overlap is unavoidable, make one the "owner" and the other "reviewer".

## Seed from registry
Before inventing, check `~/.hermes/swarm-registry.json`:
- If a similar `domain` exists, reuse its `winning_team_shape` as the starting
  roster (evolutionary prior).
- Prefer roles with positive `avg_fitness_delta` in `expert_taxonomy`.
