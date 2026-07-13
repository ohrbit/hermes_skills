# Agent Swarm Loop

> **Evolutionary, fitness-gated multi-agent orchestration** — Hermes invents the right expert team per task, runs them on a shared GitHub workspace, and only lets improvements survive. The orchestrator gets smarter across projects.

## Why this skill?

Fixed agent pipelines break the moment a task doesn't fit the pre-baked UI/engine/gfx trio. And naive parallel fan-outs fail *silently*: a retried worker can late-complete the wrong dispatch, or a wedged worker burns tokens forever. This skill closes both gaps:

- **Generative teams** — roles are *invented* for the task, not hardcoded, so the right expertise assembles itself.
- **Selection, not luck** — every round is gated by a fitness metric you pick; only PRs that improve survive.
- **Persistence** — a fitness/team registry survives across projects, so the orchestrator actually learns which team-shapes work.
- **Reliability guards** (Orca-derived) — worker preamble, `dispatch_id` correlation, circuit breaker, stale-heartbeat detection, no-local-prompt rule.

## What it does

- ✅ Brainstorms domain fitness metrics (you pick + weight them)
- ✅ Invents dynamic expert roles per task (no fixed team)
- ✅ Runs all agents on **one GitHub workspace** (per-agent deploy keys, branch-per-round, PR = fitness gate)
- ✅ Fitness-gates each round → only improvements merge
- ✅ Persists a registry across projects (team-shape + metric + fitness)
- ✅ Enforces `dispatch_id` correlation so retries can't false-complete
- ✅ Circuit breaker: a wedged worker is retried ≤3×, then escalated
- 🔄 Works best when the fitness metric has a *gradient* (continuous signal), not a binary cliff

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install agent-swarm-loop
```

## Quick Start

```text
In chat: "run a swarm loop for <your task>"
```

The skill walks PHASE 0–4. Or load it explicitly:

```bash
hermes skill agent-swarm-loop
```

## How it works

```
PHASE 0  BRAINSTORM  → propose 3-5 fitness metrics for the domain (you pick + weight)
PHASE 1  PROVISION   → GitHub workspace: per-agent SSH deploy keys, base branch
PHASE 2  TEAM        → Orchestrator invents N expert roles; dispatch in parallel
PHASE 3  LOOP        → round R: experts work on branches → PR → fitness gate →
                        merge winners → R+1 (stale completions reconciled by dispatch_id)
PHASE 4  REGISTRY    → record (team-shape, metric, fitness) → next project reuses
```

All agents share **one GitHub repo** as IPC — no shared-FS hack. Each agent gets a
repo-scoped deploy key; coordination is via kanban state + PRs.

## Usage / Examples

### Basic
> **You:** "run a swarm loop to improve the error-handling in our API client"

Hermes brainstorms metrics (tests green %, LLM-judge on spec, latency), you weight them,
it invents roles (e.g. *TransportHardener*, *RetryStrategist*, *ContractTester*), spawns
them on branches, opens PRs, keeps the ones that raise the composite fitness.

### Advanced (with the stack)
Combine with `jit-agent-teams` (ephemeral profiles) + `hermes-serverless-backend` (Modal
execution) + `model-selection-and-jit-routing` (right model per worker) + `kanban-orchestrator`
(durable board). The full stack is documented in the repo-root README.

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Definition: frontmatter + 4-phase instructions + pitfalls |
| `references/fitness-metrics.md` | How to pick/weight metrics per domain |
| `references/fitness-tuning.md` | Tuning the composite + avoiding flat evolution |
| `references/github-workspace.md` | Per-agent deploy-key provisioning + IPC model |
| `references/modal-sandbox-api.md` | Running workers serverless |
| `references/worker-timeout-recovery.md` | Wedge recovery (Modal → local flip) |
| `templates/orchestrator-loop.md` | Worker + merge body templates (incl. preamble) |
| `templates/team-spec.md` | Team-shape spec template |
| `scripts/dispatch_workers.py` | Build `delegate_task` batches |
| `scripts/orchestrator_sweep.mjs` | Pre-dispatch exhaustive sweep |
| `scripts/provision_deploy_keys.py` | Mint + register repo-scoped keys |
| `scripts/revoke_deploy_keys.py` | Revoke keys after run |

## Related skills

- `jit-agent-teams` — ephemeral JIT profiles + Modal wedge-recovery (the substrate this reuses)
- `kanban-orchestrator` — durable SQLite board the loop reports into
- `model-selection-and-jit-routing` — pick the right model per worker (free-tier aware)
- `hermes-serverless-backend` — run workers on Modal, not your host

## Notes / caveats

- **Security:** keys are mounted via credentials, never inlined in prompts (Hermes redacts inline secrets).
  Per-agent deploy keys are repo-scoped + revocable; GitHub PATs can't be minted via API.
- **Concurrency:** ≤2 workers serialized on local, ≤3 on Modal. A host with <1 GB free can't run 4 local workers.
- **Circuit breaker:** a worker retried ≥3× is marked failed and escalated — no blind token burn.
- **Fitness gradient:** if the metric is a binary cliff (pass/fail, no in-between), evolution can't tune —
  do an exhaustive sweep in PHASE 0 instead of relying on selection.
- **Orca-derived:** worker preamble (report-once, heartbeat, route questions to coordinator),
  `dispatch_id` pairing, stale-heartbeat warn-only (10 min), no `AskUserQuestion` in workers.

## License

MIT — © 2024 ohrbit
