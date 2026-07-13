# Kanban Orchestrator

> **The decomposition playbook for routing work through Hermes Kanban** — decompose don't execute, fan out across profiles, let the board carry state.

## Why this skill?

When you play the orchestrator role, the temptation is to *do* the work yourself. This skill enforces the opposite: decompose the goal into specialist cards, route each to the right profile, and let Hermes's Kanban system carry status, dependencies, and completion. It also bakes in the user-corrected **JIT profile** pattern (create teams on the fly, delete after) instead of relying on a fixed roster that may not exist on this machine.

## What it does

- ✅ "Decompose, don't execute" rule (auto-injected into every kanban worker too)
- ✅ Profile discovery + the JIT team pattern (preferred over fixed profiles)
- ✅ Parent/child card dependencies (merge waits on parents automatically)
- ✅ Anti-temptation rules (don't silently assign unknown assignees)
- ✅ Concrete worked example (Gravity Swarm 4-role fan-out)

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install kanban-orchestrator
```

## Quick Start

```bash
# discover or create profiles, then:
hermes kanban create "UI" --assignee gs-ui --goal --body "spec"
hermes kanban create "merge" --assignee gs-merge --parent t_ui t_engine --body "..."
```

## How it works

```
orchestrator
   ├─ analyze task → roles needed
   ├─ CREATE JIT profiles (gs-ui, gs-engine, gs-gfx, gs-merge)
   ├─ DISPATCH parallel kanban cards (each → a profile)
   ├─ MERGE card (--parent links) auto-promotes when parents done
   └─ DELETE profiles
```

The core worker lifecycle (`kanban_create` fan-out, "decompose don't execute") is auto-injected into every kanban process via the `KANBAN_GUIDANCE` system block. This skill is the deeper playbook for when you *are* the orchestrator.

## Usage / Examples

### Basic
> "Break this into parallel tasks and run them."

Orchestrator identifies roles, creates JIT profiles, dispatches, merges, cleans up.

### Advanced
Fixed-profile setups: `hermes profile list` first — a card assigned to a non-existent `researcher` sits in `ready` forever (dispatcher fails silently). Always ground decomposition in profiles that exist or create JIT.

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Decomposition playbook, JIT pattern, anti-temptation rules |
| `templates/` | Card-body templates |
| `references/` | Deep dives |

## Related skills

- `jit-agent-teams` — the JIT lifecycle in practice
- `agent-swarm-loop` — evolutionary loop on top of kanban
- `kanban-worker` (companion) — the worker-side contract

## Notes / caveats

- **No default specialist roster** — don't assume `researcher`/`coder` exist; discover or create.
- JIT beats fixed profiles on flexibility, parallelism, and cleanup.
- Cache `hermes profile list` results; don't re-ask every turn.

## License

MIT — © 2024 ohrbit
