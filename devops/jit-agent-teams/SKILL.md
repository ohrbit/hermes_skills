---
name: jit-agent-teams
description: >-
  Spin up Just-In-Time agent teams per task — create ephemeral per-task Hermes
  profiles, dispatch parallel kanban tasks, and use the Kanban board ITSELF as the
  inter-worker communication channel (no file-upload plumbing, no shared FS).
  Covers the JIT lifecycle (create profiles → parallel dispatch → merge → delete
  profiles), the Kanban-as-IPC delivery pattern, the Modal-sandbox I/O-wedge
  recovery path (extract FULL FILE CONTENT from task summaries and reassemble
  locally), and the token-cost trap of blind Modal retries. Use when the user says
  "JIT teams", "ephemeral agent profiles per task", "a fresh team for each job",
  "build a team on the fly", or asks how parallel subagents can collaborate on
  code/artifacts without shared filesystem access. Complements
  hermes-serverless-backend (Modal wiring) and hermes-infrastructure-wiring.
---

# JIT Agent Teams

**Core idea (user-established):** for *each distinct task*, build a team *just in
time* — create ephemeral per-task profiles, dispatch parallel kanban tasks to
them, then **delete the profiles after completion**. Do NOT maintain one
long-lived profile that tasks get pushed into.

This is distinct from `hermes-multi-agent-triage` (a fixed detect→route
pipeline). JIT teams are bespoke, per-job, and thrown away.

## When to use
- User explicitly asks for "JIT teams" / "ephemeral profiles per task".
- A deliverable decomposes into 2–4 independent specialist pieces (UI / engine /
  GFX / merge, etc.) that can be built in parallel.
- You want cloud (Modal) parallelism without solving cross-sandbox file sharing.

## The JIT lifecycle

```
1. CREATE   hermes profile create gs-ui / gs-engine / gs-gfx / gs-merge
   → after create, copy the ACTIVE SOUL.md into each new profile so workers
     inherit your persona + operational principles (Verify>assume, Fail fwd,
     Bias→action) instead of stock boilerplate:
     for p in gs-ui gs-engine gs-gfx gs-merge; do
       cp ~/.hermes/SOUL.md ~/.hermes/profiles/$p/SOUL.md; done
2. DISPATCH hermes kanban create "..." --assignee gs-ui --goal --goal-max-turns N --body "..."   (×N, parallel)
3. MERGE    hermes kanban create "merge" --assignee gs-merge --parent t_ui t_engine t_gfx --body "..."
4. DELETE   hermes profile delete gs-ui gs-engine gs-gfx gs-merge   (after all done)
```

- Parented merge task auto-promotes `todo → ready` once all `--parent` tasks
  reach `done`. No polling needed.
- Profiles can be `terminal.backend: modal` (cloud) or `local` (host). See pitfalls.

## Kanban IS the IPC channel — DO NOT build file upload plumbing

Workers do **not** need to push files to the host. The deliverable travels
*inside the kanban task summary*.

**Worker task body must say:**
```
1. Write your artifact to /tmp/foo.js using write_file
2. BUILD: <spec>
3. COMPLETE the task with:  kanban_complete(summary=cat /tmp/foo.js)
   The summary MUST contain the FULL file content so the merge worker can use it.
```

**Merge worker task body:**
```
1. Wait until all parents are done (auto-promotes from todo)
2. For each parent, read the kanban summary (which contains the FULL file content):
     hermes kanban show t_xxx   → has foo.js in summary
3. Extract the file contents from the summaries
4. Assemble, write /tmp/final.html, then:
     kanban_complete(summary=cat /tmp/final.html)
```

No HTTP upload server, no Modal Volume mount, no host firewall rule, no network
egress. The board carries the bytes. See `templates/jit-task-body.md`.

## Pitfalls (learned the hard way)

### 1. Modal Sandbox cannot reach the host on arbitrary ports
Do **not** instruct workers to `curl PUT` to `http://<host-ip>:19999/...`.
Modal sandboxes hit a network-egress wall — the connection times out even when
github/example.com egress works. Opening a `ufw allow 19999/tcp` rule does NOT
help; the sandbox egress is the blocker.

### 2. `execute_code`'s terminal is LOCAL — a passing curl test there proves nothing about Modal
A `curl` to the host that succeeds inside `execute_code` is running on the
*agent's own box* (default `terminal.backend: local`), NOT in a Modal sandbox.
It does NOT validate that a Modal worker can reach the host. Never conclude
"upload works" from an `execute_code` curl. Only a real Modal-spawned worker's
curl proves it — and it will fail.

### 3. Modal worker I/O wedge — recover via summaries, not retries
When a Modal worker's `terminal` / `write_file` wedges (symptoms: `write_file`
returns empty error, `terminal('echo ok')` exits 1 with no stdout, reads still
resolve but writes don't), the worker often still **embeds the designed source
verbatim in its task summary or comment**. Do not burn more tokens retrying
Modal. Instead:

- `hermes kanban show t_xxx` → the summary contains `FULL FILE CONTENT:` or a
  verbatim code block.
- Extract it locally (see `references/recovery-from-modal-wedge.md`).
- Reassemble the final artifact **locally** and deliver.

This is the single most valuable recovery path. See the reference for the exact
extraction script.

### 4. Token cost — switch wedged profiles to `local`, don't loop Modal
Each Modal retry + each parallel worker burns Nous/Modal tokens. If a profile's
Modal workers wedge on I/O 2+ times, **flip that profile to
`terminal.backend: local`** so workers run on the host itself and write to local
FS directly — no network wall, no wedge. The JIT pattern still holds; only the
compute backend changes.

### 5. Summary extraction mangles `|` and IIFE closers
When reassembling from extracted summaries:
- Use `open()` on raw files, NOT `read_file` (which prepends `LINE|` and
  breaks `a|=0` bitwise ops in JS).
- Engine/renderer files wrapped in `(function(root){ ... })(typeof window ...)`
  often arrive **missing the closing `});`** — append it after extraction.
- After assembling, run `node --check` on the extracted `<script>` block, then a
  runtime harness with a mock canvas/DOM (see reference) to confirm it executes.

### 6. Dispatch MUST pass `skills=[...]` (capability lever)
A bare `delegate_task` / kanban worker gets NO skills and GUESSES domain
knowledge — wrong APIs, wrong commands, missed pitfalls. The orchestrator
MUST pass the role-relevant skills when dispatching:
- ui worker    → `skills=["fable-style-singlefile-web","popular-web-designs","refactoring-ui"]`
- engine worker→ `skills=["test-driven-development","systematic-debugging","simplify-code"]`
- gfx worker   → `skills=["p5js","manim-video"]`
- merge worker  → `skills=["github-pr-workflow","requesting-code-review"]`
This is the Tunnel-Derby lesson: skipping `skills=[...]` on fan-out = generic,
wrong output. Non-negotiable.

### 7. Per-task profiles MUST inherit SOUL.md (discipline lever)
Fresh `hermes profile create` yields a STOCK 513-byte SOUL → worker runs as a
generic assistant, drops Verify>assume / Fail-fwd, and STALLS or ASSERTS
unverified results. Copy the active SOUL into every new profile (see lifecycle
step 1). Without this, workers don't self-correct and don't finish reliably.

## Verification checklist
- [ ] All specialist tasks reach `done` (or, if wedged, their summaries hold
      the full source).
- [ ] Merge task auto-promoted and completed with full final content.
- [ ] Final artifact passes `node --check` (syntax).
- [ ] Final artifact passes a mock-DOM runtime harness (engine.evolve() returns
      history; renderer.draw() doesn't throw on a Proxy ctx).
- [ ] Ephemeral profiles deleted.

## External orchestration reference
- `references/orca-orchestration-patterns.md` — Orca (stablyai) coordinator patterns (dispatchId correlation, 3-strike circuit breaker, warn-only stale-heartbeat, worker-preamble injection, decision gates) distilled for JIT fan-out hardening. Read before scaling `delegate_task` fan-outs.

## Related
- `hermes-serverless-backend` — wiring Modal as `terminal.backend`.
- `hermes-infrastructure-wiring` — per-profile worker infra, local-default +
  cloud-workers architecture.
- Memory note: "JIT agent teams: per-project dynamic profiles (Modal backend),
  Kanban tasks with --parent merge, delete profiles after. File transfer from
  Modal via 'cat file' in task body → Kanban log."
