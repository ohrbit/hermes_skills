# JIT Agent Teams

> **Spin up a bespoke agent team per task** — ephemeral profiles, parallel kanban dispatch, the board itself as IPC. Throw the team away when done.

## Why this skill?

Maintaining one long-lived "worker" profile and pushing every task into it serializes work and accumulates orphan profiles. The JIT pattern instead builds exactly the team a task needs — UI / engine / GFX / merge — runs them in parallel, merges, then deletes the profiles. And because cross-sandbox file sharing is a nightmare, it uses the **Kanban board as the communication channel**: deliverables ride inside task summaries, no upload servers, no shared FS.

## What it does

- ✅ Just-In-Time profile creation per task (no pre-defined roster)
- ✅ Parallel kanban dispatch to N specialist profiles
- ✅ Kanban-as-IPC: full file content travels in `kanban_complete` summaries
- ✅ Parented merge task auto-promotes when all parents are `done`
- ✅ Modal I/O-wedge recovery (reassemble from summaries, don't blind-retry)
- ✅ Documents the token-cost trap of blind Modal retries

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install jit-agent-teams
```

## Quick Start

```bash
# 1. create per-role profiles
hermes profile create gs-ui gs-engine gs-gfx gs-merge
# 2. dispatch in parallel
hermes kanban create "UI" --assignee gs-ui --goal --body "spec"
# 3. merge waits on parents, then:
hermes profile delete gs-ui gs-engine gs-gfx gs-merge
```

## How it works

```
CREATE profiles (gs-ui, gs-engine, gs-gfx, gs-merge)
   │
DISPATCH parallel kanban tasks (each worker writes artifact → kanban_complete(summary=cat file))
   │
MERGE task (--parent links) auto-promotes when parents done → extracts content from summaries
   │
DELETE profiles
```

Worker bodies say: *write artifact, then `kanban_complete(summary=cat /tmp/foo.js)` — summary MUST contain full file content.* The merge worker reads summaries, reassembles, writes final.

## Usage / Examples

### Basic
> "Build the Gravity Swarm game with a fresh UI/engine/GFX team."

Creates 3 JIT profiles, dispatches in parallel, merges into one HTML, deletes profiles.

### Advanced
Worker I/O wedges on Modal? Don't retry — the worker still embeds the source in its summary. The merge step extracts from the summary and the deliverable survives.

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | JIT lifecycle, Kanban-as-IPC, pitfalls |
| `templates/jit-task-body.md` | Worker / merge task body templates |
| `scripts/` | Helpers (dispatch, key provisioning) |

## Related skills

- `kanban-orchestrator` — the board + decompose playbook this builds on
- `hermes-serverless-backend` — run JIT profiles on Modal
- `agent-swarm-loop` — evolutionary loop that reuses this as substrate

## Notes / caveats

- **Modal sandbox can't reach host on arbitrary ports** — don't `curl PUT` to host IP; egress is blocked.
- **`execute_code` terminal is LOCAL** — a passing curl there proves nothing about Modal.
- **Never reuse one profile for everything** — that's the anti-pattern this replaces.

## License

MIT — © 2024 ohrbit
