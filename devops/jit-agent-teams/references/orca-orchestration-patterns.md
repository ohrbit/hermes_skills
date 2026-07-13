# Orca (stablyai/orca) Orchestration Patterns — Recyclable for JIT Fan-Outs

Source: read `stablyai/orca` real source (`src/main/runtime/orchestration/*.ts`,
`src/cli/dispatch.ts`, `src/cli/handlers/orchestration.ts`) on 2026-07-13.
Orca = Electron ADE that runs CLI coding agents (Claude Code, Codex, OpenCode,
Hermes CLI, …) each in its own `git worktree`, coordinated by a message-passing
layer. The coordinator is a 2s poll loop. Below: the 5 mechanisms worth stealing
to harden our `delegate_task` JIT fan-outs.

## Data model (SQLite)
- `tasks`: spec, deps, status `pending→ready→dispatched→completed/failed/blocked`
- `dispatch_contexts`: ONE ROW PER ATTEMPT (retry = new row, same task_id).
  Fields: `assignee_handle`, `status`, `failure_count`, `last_heartbeat_at`.
- `messages`: typed — `worker_done`, `heartbeat`, `escalation`, `decision_gate`,
  `status`, `dispatch`, `handoff`, `merge_ready`.
- `decision_gates`: block a task until `resolveGate` (never auto-resolved).

## The 5 tricks

### 1. Dispatch-ID correlation (most important)
Every `worker_done` / `heartbeat` message MUST carry BOTH `taskId` AND
`dispatchId`. `lifecycle-reconciliation.ts` rejects any lifecycle message whose
`dispatchId` ≠ the *active* dispatch for that task — silently ignores stale
messages from a previously-failed retry.
- **Why we need it:** with `delegate_task` fan-outs, a retried worker can emit a
  late `kanban_complete` that marks the *current* (different) attempt done.
- **Apply:** mint a `dispatch_id` per worker, pass it in the subagent `context`,
  require it in the worker's completion summary, and reject completions whose
  `dispatch_id` ≠ the active one.

### 2. Circuit breaker (3 strikes)
`db.failDispatch`: increments `failure_count`; at ≥3 the dispatch →
`circuit_broken` and the task → `failed` (not retried). Below 3, task → `ready`
for re-dispatch. Critical detail: a *pre-dispatch* refusal (e.g. stale worktree)
does NOT increment `failure_count` — only an actual dispatch attempt does, so a
recoverable "fetch and retry" never burns the budget.
- **Apply:** our JIT fan-outs have NO retry budget — a hung worker just hangs.
  Add a 3-strike cap; failures below threshold return task to ready.

### 3. Stale-heartbeat detector (warn-only, 10 min = 2× 5-min cadence)
Coordinator warns when a dispatched worker hasn't heartbeat in 10 min, but
**deliberately does NOT auto-fail** — comment: false-positive cost (killing a
slow-but-correct worker) > false-negative cost (hung worker holds a slot).
- **Apply:** we poll subagents but have no liveness signal distinct from
  "finished." Add a heartbeat cadence + warn-only stale detector.

### 4. Worker preamble injection
On dispatch, the coordinator `buildDispatchPreamble` injects a CONTRACT into the
worker telling it: report `worker_done` exactly once (even on failure), send a
3-sentence summary (what done / found / left), heartbeat every 5 min, and
**NEVER use a local interactive prompt — route questions through `ask`** (a local
prompt hangs forever, invisible to the coordinator).
- **Apply:** bake these rules into the subagent `context` at dispatch time, not
  assumed. Especially: "route questions to coordinator, not local clarify/prompt."

### 5. Decision gates block, never auto-resolve
`createGate` sets task→`blocked`; `resolveGate` sets it back to `ready` WITH the
resolution injected into the NEXT preamble. Coordinator never answers gates
itself (would defeat the checkpoint).
- **Apply:** maps 1:1 to our `kanban block → escalate to you`. Keep human as the
  only gate resolver.

## Coordinator loop (reference)
`executeLoop`: `decompose()` → `while !stopped: tick()` where
`tick = processMessages → processEscalations → processDecisionGates →
warnStaleDispatches → dispatchReadyTasks → checkConvergence`, then `sleep(2000)`.
Concurrency capped at `maxConcurrent` (default 4).

## What we already have vs. missing
| Orca | Our JIT/kanban |
|---|---|
| dispatch_contexts (retry rows) | missing (one task = one attempt) |
| typed message inbox | missing (kanban summary is the only channel) |
| dispatchId enforcement | missing (no correlation guard) |
| circuit breaker | missing |
| stale-heartbeat | missing |
| worker preamble | partially (task body) |

## Proposed skill: `jit_orchestrator`
A thin Python wrapper over `delegate_task` + a SQLite `dispatch_contexts` table
implementing tricks 1–5, scaffolding against `kanban.db`. NOT yet built — flagged
for a follow-up session.
