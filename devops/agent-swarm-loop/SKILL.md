---
name: agent-swarm-loop
description: >-
  Generischer, evolutionärer Kanban-Orchestrations-Loop für beliebige Projekte.
  Orchestrator brainstormt vorab Fitness-Metriken (User wählt), erstellt dann
  pro Task ein DYNAMISCHES Experten-Team (Rollen werden erfunden, nicht fixed),
  alle Agenten teilen EINEN GitHub-Workspace (per-Agent Deploy-Keys, Branch-per-Runde,
  PR als Fitness-Gate), loopen iterativ, und eine Fitness-History persistiert über
  Projekte hinweg — so wird der Orchestrator über alle Projekte klüger.
  Komplement zu jit-agent-teams (Kanban-as-IPC + Modal-Wedge-Recovery).
  Load when the user says "swarm loop", "agent swarm", "evolutionary team",
  "fitness-gated agents", or wants self-improving multi-agent orchestration.
version: 1.0.0
tags: [swarm, jit, kanban, fitness, github, modal, orchestration, evolutionary]
platforms: [linux]
---

# Agent Swarm Loop

**Core idea (user-established):** A *generative* orchestration loop — not a fixed
pipeline. The Orchestrator:
1. **Brainstorms fitness metrics** up front (presents candidates, user picks/weights).
2. **Invents expert roles dynamically** per task (never a fixed UI/engine/gfx set).
3. Spins a fresh JIT expert team per round; all agents share **one GitHub workspace**
   (per-agent SSH deploy keys, branch-per-round, PR = fitness gate).
4. **Fitness-gates** each round → only improvements survive (selection).
5. **Persists a fitness/team registry** that survives across projects → the
   Orchestrator and expert pool get smarter over time.

This fixes the Gravity-Swarm failure mode (random reset → no learning): here the
**fitness history + expert taxonomy persist**, so selection actually improves.

## When to use
- User asks for "swarm loop", "agent swarm", "evolutionary team", "self-improving agents".
- A deliverable needs iterative refinement with measurable quality (not one-shot).
- You want parallel experts collaborating on a shared repo WITHOUT a shared FS hack.

## The Loop (4 phases)

```
PHASE 0  BRAINSTORM  → propose 3-5 fitness metrics for THIS project domain
                       (user picks + weights; see references/fitness-metrics.md)
PHASE 1  PROVISION   → GitHub workspace: per-agent deploy keys, base branch
PHASE 2  TEAM        → Orchestrator invents N expert roles for the task
PHASE 3  LOOP        → round R: spawn experts (parallel) → each works on
                       branch → open PR → fitness gate → merge winners → R+1
PHASE 4  REGISTRY    → record (team-shape, metric, fitness) → next project reuses
```

### PHASE 0 — Fitness Brainstorm (NEW, mandatory)
Do NOT create the team before this. The Orchestrator outputs a short table:

```
📊 Candidate fitness metrics for <project domain>:
| # | Metric | What it measures | Auto? | Effort |
|---|--------|------------------|-------|--------|
| 1 | unit tests green + coverage% | correctness | ✅ | low |
| 2 | LLM-judge vs spec rubric (1-10) | requirement fulfilment | ✅ | med |
| 3 | perf: <domain-specific> | efficiency | ✅ | med |
| 4 | human review / PR accept | subjective quality | ❌ | high |
| 5 | composite (weighted mix) | balanced | ✅ | med |
```
Then ask the user to **pick + weight** (e.g. `0.4 tests + 0.4 judge + 0.2 perf`).
Only after the pick, proceed to PHASE 1. See `references/fitness-metrics.md` for
the full metric families + rubric templates.

### PHASE 1 — Provision GitHub Workspace
For each agent the Orchestrator will spawn, mint an **isolated SSH deploy key**
(scoped to the ONE shared repo). This is the clean alternative to sharing a
master `GITHUB_TOKEN` inside containers. See `references/github-workspace.md` for
the exact `ssh-keygen` + GitHub API + cleanup code.

Key facts (verified):
- GitHub **PATs cannot be minted via API** — but **deploy keys can** (`POST
  /repos/{owner}/{repo}/keys`, `read_only:false`). One key per agent = one
  revocable, repo-scoped credential.
- Modal containers inherit **NO host env**. Secrets reach them only via a
  **file mount** (`terminal.credential_files` or `Image.add_local_file`) — the
  worker reads its key from the mounted JSON (see `references/github-workspace.md`).
  ⚠️ **NEVER inline the private key in the `delegate_task` context / kanban body** —
  Hermes redacts secrets in tool-call text to `[REDACTED PRIVATE KEY]` and the
  push fails with `Permission denied (publickey)`.
- `terminal.credential_files` is written as a **real YAML list via python**
  (NOT `hermes config set` — that serialises lists as strings, breaking it).

Two delivery options:
- **A) Shared master token** — add `.env` to `terminal.credential_files`; all
  agents mount the same token. Simple, but no isolation.
- **B) Per-agent deploy keys (recommended for swarm)** — Orchestrator generates
  key pair, registers pub key as deploy key, and writes all priv keys to a JSON
  file registered via `terminal.credential_files` (or baked into the Modal image
  via `Image.add_local_file`). The worker reads ITS role's key from that mounted
  file. Clean revocation, repo-scoped. This is the dev-team model. Never inline
  the key in the worker prompt — it gets redacted.

### PHASE 2 — Dynamic Team Creation

**MANDATORY — SKILL ATTACH + WORKER PREAMBLE (Orca-derived):**
1. When calling `delegate_task` for each worker, pass `skills=["agent-swarm-loop"]`
   so the worker gets the interface contract + references (see Pitfalls — a blind dispatch wastes the round).
2. **Inject a WORKER PREAMBLE** into every worker's context (see templates WORKER BODY).
   The preamble is the coordination contract — delivered *to the worker at dispatch
   time*, not assumed. It enforces:
   - **Report exactly once** via `kanban_complete` (even on failure — never silently exit).
   - **Heartbeat every 5 min** while actively working (a progress note, not the
     final complete). Lets the Orchestrator tell "still thinking" from "hung/crashed".
   - **Route questions to the coordinator, NEVER a local interactive prompt.**
     `AskUserQuestion`-style TUI prompts hang forever — the Orchestrator can't see or
     answer them. Block on `kanban block` / a decision-gate instead.
   - **dispatch_id correlation**: every completion/heartbeat carries BOTH the
     `task_id` (kanban card id) AND a `dispatch_id` (the specific attempt). A retried
     task has multiple dispatch rows; a stale `kanban_complete` from a failed attempt
     MUST NOT complete the current dispatch. The Orchestrator matches `dispatch_id`
     before accepting completion (see PHASE 3 reconcile).

**Concurrency:** respect host RAM. Local execution → serialize or cap at 2; `delegate_task`
batch max is 3. Prefer Modal for real parallelism (see Pitfalls).

The Orchestrator **invents** expert roles for the task (no fixed set). Example
for "build a realtime collaborative editor": it might spawn `conflict-resolver`,
`ot-engine`, `presence-sync`, `crdt-reviewer` — whatever the task needs.

Spawn pattern (reuse `jit-agent-teams`):
```
# 0. copy a SOUL.md into the ephemeral profile (discipline lever):
SRC=~/.hermes/SOUL.md          # personal (if present)
[ -f "$SRC" ] || SRC=~/.hermes/skills/devops/setup-bundle/SOUL.md  # shared core
cp "$SRC" ~/.hermes/profiles/swarm-<round>-<role>/SOUL.md
hermes profile create swarm-<round>-<role>        # ephemeral
hermes kanban create "<role>: <goal>" --assignee swarm-<round>-<role> \
    --goal "<goal>" --goal-max-turns N \
    --body "<see templates/orchestrator-loop.md: WORKER BODY>"
```
⚠️ SOUL inheritance is MANDATORY, not optional: a fresh `hermes profile
create` yields a STOCK 513-byte SOUL → the worker runs as a generic
assistant, drops Verify>assume / Fail-fwd, STALLS or ASSERTS unverified
results. Copy the active SOUL (your persona + operational principles) into
every `swarm-<round>-<role>` profile at create time.

⚠️ `skills=[...]` is TWO-dimensional and both are required:
- (a) contract skill: ALWAYS `skills=["agent-swarm-loop"]` (interface + preamble).
- (b) domain skills: the orchestrator MUST add the role-relevant skills so
  the worker knows the HOW (APIs, commands, pitfalls), e.g.
  `skills=["agent-swarm-loop","test-driven-development","systematic-debugging"]`.
  A bare dispatch GUESSES domain knowledge → wrong APIs, missed pitfalls
  (the Tunnel-Derby lesson). Invent the domain list per invented role.
Each worker body MUST include:
1. Read priv key from the **mounted** keystore JSON (`/root/.hermes/swarm_tunnel_derby_keys.json`), write to `~/.ssh/id_ed25519`, `chmod 600`, set `GIT_SSH_COMMAND`. (Never inline the key in the prompt — it gets redacted.)
2. Clone `git@github.com:owner/repo.git -b <base-branch>` to a workdir.
3. Branch `feat/<round>-<role>`.
4. Do the work; commit; push; open PR against base.
5. `kanban_complete(summary=<WHAT CHANGED + HOW TO EVALUATE>, task_id=<card>, dispatch_id=<attempt>)`.

### PHASE 3 — Loop / Fitness Gate
Per round:
1. Spawn all experts **in parallel** (batch `delegate_task` or parallel kanban).
2. Wait for PRs (kanban `--parent` merge task auto-promotes when all done).
3. **Evaluate fitness** on each PR (run the PHASE-0 metric: tests, LLM-judge, perf).
4. **Selection**: merge only PRs that raise fitness vs the round baseline.
   Rejected PRs are closed (agent profile deleted).
5. `round = round + 1`; repeat until fitness plateaus or user stops.

⚠️ **RECONCILE COMPLETIONS (Orca-derived, dispatch_id authority):**
A `kanban_complete` is only accepted if its `dispatch_id` matches the **active**
dispatch for that `task_id`. Reject (ignore) any completion whose `dispatch_id`
points at a failed/older attempt — a retried worker's stale "done" must not
complete the current attempt. Only accept when `task_id` + `dispatch_id` both match
the live dispatch row. (Mirrors Orca's `lifecycle-reconciliation`: task_id alone is
NOT a completion authority.)

⚠️ **CIRCUIT BREAKER (Orca-derived, 3 strikes):** track a `failure_count` per
task. On worker failure / timeout / rejected dispatch:
- `failure_count < 3` → task returns to `ready` for re-dispatch (new `dispatch_id`).
- `failure_count >= 3` → task `circuit_broken` → mark `failed`, do NOT retry.
Escalate to the user (decision gate) instead of burning more attempts. This caps
token waste from a wedged worker (the old "blind Modal retries burn tokens" trap,
now bounded).

⚠️ **STALE-HEARTBEAT DETECTION (Orca-derived, warn-only):** if a worker sends no
heartbeat for `>10 min` (2× the 5-min cadence), emit a WARNING but do NOT auto-fail.
False-positive cost (killing a slow-but-correct worker) > false-negative cost (a
hung worker holds a slot until you notice). Inspect state, then decide.

⚠️ **ORCHESTRATOR-SWEEP BEFORE RE-DISPATCH (critical):** when a round fails the
fitness gate on a *tuning* axis (a constant, radius, threshold), do NOT re-run
workers on a hunch. Assemble the real branches and run a local parameter sweep
(your own Node/Python harness, seconds) to locate the **binary cliff** and the
true passable window. See `references/fitness-tuning.md` + the re-runnable
`scripts/orchestrator_sweep.mjs`. Verified: 4 worker rounds of Tunnel Derby never
found the cliff that a 30-second local sweep exposed.

**ASSEMBLE recipe (the part that eats time if you forget it):** a fresh clone only
has `main` — the `feat/rN-*` branches are NOT local. You MUST `git fetch origin`
first, then `git checkout origin/<branch> -- tunnel-derby/<file>` (note: take each
file from its OWN branch; a plain `git checkout <branch>` switches the whole tree
and clobbers sibling files). Copy each into one `./assembled` dir, then run the
sweep. Full recipe is at the bottom of `scripts/orchestrator_sweep.mjs`.

⚠️ **WORKER TIMEOUT RECOVERY:** a `delegate_task` worker can time out (600s) AFTER
pushing but before finishing its summary — the remote branch may be empty. Don't
re-dispatch blindly; the Orchestrator takes over locally: verify the remote branch
via API, fetch the worker's LAST-GOOD source from a prior branch, apply the fix,
and push via the GitHub contents API. See `references/worker-timeout-recovery.md`.

The merge worker (`templates/orchestrator-loop.md`) assembles + runs the
fitness eval and decides survivors.

### PHASE 4 — Registry (the learning part)
After the project, append to a **registry file** (e.g. `~/.hermes/swarm-registry.json`):
```json
{
  "projects": {
    "<project>": { "domain": "...", "metrics": {...}, "best_fitness": 0.91,
                   "winning_team_shape": ["role-a","role-b"], "rounds": 4 }
  },
  "expert_taxonomy": { "role-x": { "worked_on": ["domain-a","domain-b"],
                                   "avg_fitness_delta": +0.07 } }
}
```
Next project: Orchestrator consults the registry to **seed a better initial
team shape + default metric weights**. This is what makes it evolutionary.

## Pitfalls (carried from jit-agent-teams + new)
- **ALWAYS load this skill when dispatching workers** — pass skills containing agent-swarm-loop (plus any sibling refs) in every delegate_task so each worker receives the interface contract, fitness-metrics, and github-workspace code. The orchestrator MUST attach the skill it is executing. USER HIT THIS TWICE: a round dispatched without the skill left every worker blind to the module contract (they re-derived it or failed). Treat skill attachment as mandatory, not optional.
- **Host RAM / concurrency cap (user-corrected, verified OOM)** — the user explicitly called out insufficient RAM for 4 workers after 4 local workers OOM-killed on an 864 MB host. This swarm targets the Modal (cloud) backend. For LOCAL execution serialize workers (one at a time) or cap at 2 concurrent; never assume the host has RAM for N parallel LLM agents. Wire Modal (terminal.backend: modal) so workers run on sandboxes and the host stays free. delegate_task batch max is 3.
- **BINARY FITNESS CLIFF (verified, cost 4 wasted rounds)** — survival-percent-style metrics often jump 0% to 100% across a tiny constant window with NO 40-70% band, so the GA cannot select. Before re-dispatching on a hunch, run a local Orchestrator sweep to find the cliff, then apply a GRADIENT fix (look-ahead steering, soft-failure clamp, softer environment, or a continuous metric). See references/fitness-tuning.md. Worker self-tests reporting 0% or 100% are NOT validated — the Orchestrator must run the harness on the real assembled branches and confirm the metric is in-band with positive convergence gain.
- **No env in Modal** — never assume `GITHUB_TOKEN` is in the container. Mount
  via `credential_files` or pass key via context. (Verified in modal.py: secrets
  only via `Mount.from_local_file` of `get_credential_file_mounts()` etc.)
- **Modal egress wall** — workers CANNOT `curl` back to a host port. Deliver
  artifacts via kanban summary or push to GitHub (egress to github.com works).
- **Blind Modal retries burn tokens** — if a profile wedges twice, flip it to
  `terminal.backend: local`. Recover source from kanban summaries.
- **Don't reset fitness history** — that's the whole point (vs Gravity-Swarm).
- **PAT minting is impossible** — use deploy keys (proven POC).
- **Weighted composite must sum to 1.0** — normalise before eval.
- **RECONCILE dispatch_id, not just task_id (Orca-derived)** — a retried task has
  multiple dispatch rows. If a worker's `kanban_complete` carries a `dispatch_id`
  that doesn't match the live attempt, IGNORE it. Otherwise a failed attempt's
  late "done" silently completes the retry. This is the exact bug a parallel fan-out
  hits; the preamble enforces it (see PHASE 2), PHASE 3 reconciles it.
- **CIRCUIT BREAKER caps token waste (Orca-derived)** — never re-dispatch the same
  task more than 3 times. At strike 3, mark `failed` and escalate to the user via a
  decision gate. Blind retries (the old "Blind Modal retries burn tokens" trap) are
  now bounded by policy, not by luck.
- **HEARTBEAT, don't pollblind (Orca-derived)** — require workers to emit a progress
  note every 5 min. A missing heartbeat >10 min is a WARNING, not an auto-kill: a slow
  correct worker is more valuable than a fast false-negative. Inspect, then decide.
- **NO LOCAL INTERACTIVE PROMPTS in workers (Orca-derived)** — if a worker needs a
  decision, it must `kanban block` / ask the coordinator. A `AskUserQuestion`-style
  TUI prompt hangs forever because the Orchestrator can't see or answer it. The
  preamble forbids it explicitly.
- **PUBLISHING SAFETY (user-stated rule, hard line)** — when snapshotting skills to a
  public repo (e.g. `ohrbit/hermes_skills`), NEVER include real keys/tokens. Scan every
  staged file for `ghp_…`, `sk-…`, `-----BEGIN OPENSSH PRIVATE KEY-----` (non-placeholder),
  and literal `GITHUB_TOKEN=`. Use placeholders only (`<priv key text>`, `<owner>/<repo>`,
  `<YOUR_ROLE>`). Mint a repo-scoped deploy key to push, then REVOKE it after merge.
  See `references/snapshot-skill-to-repo.md` for the exact flow + mandatory key-scan.
  The Orchestrator's own `swarm_keys.jsonl` / `swarm_snapshot_keys.json` must NEVER be
  staged.

## Verification checklist
- [ ] PHASE 0 done: user picked + weighted metrics.
- [ ] PHASE 1: deploy keys created AND registered (HTTP 201); cleanup verified.
- [ ] PHASE 2: workers dispatched with `skills=["agent-swarm-loop"]` ATTACHED (not blind).
- [ ] PHASE 2: concurrency respected — serialized or <=2 on local, <=3 on Modal. No OOM.
- [ ] PHASE 2: each worker body contains clone+branch+PR (priv key via context).
- [ ] PHASE 2: each worker body injects the WORKER PREAMBLE (report-once, heartbeat, no-local-prompt) + carries `task_id` AND `dispatch_id`.
- [ ] PHASE 3: completions reconciled by `dispatch_id` (stale attempts ignored).
- [ ] PHASE 3: circuit breaker engaged — `failure_count` tracked, >=3 → failed + escalate (no blind retry).
- [ ] PHASE 3: stale-heartbeat (>10 min) emits WARNING, does not auto-fail.
- [ ] PHASE 3: workers needing a decision used `kanban block` (not a TUI prompt).
- [ ] PHASE 3: ≥1 round completed; PRs evaluated by chosen metric; survivors merged.
- [ ] PHASE 4: registry updated with team-shape + fitness.
- [ ] PHASE 4: deploy keys revoked (DELETE /repos/{repo}/keys/{id} for each logged id); ephemeral profiles deleted.

## Related
- `jit-agent-teams` — Kanban-as-IPC, Modal wedge recovery, JIT lifecycle.
- `hermes-serverless-backend` — wiring Modal as `terminal.backend`.
- `references/github-workspace.md` — deploy-key provisioning code + redaction trap.
- `references/orca-orchestration-patterns.md` — distilled Orca engine (`stablyai/orca`) patterns this skill reuses: dispatchId correlation, circuit breaker, heartbeat, preamble, decision gates.
- `references/snapshot-skill-to-repo.md` — proven flow to publish a skill to `ohrbit/hermes_skills` with a mandatory no-real-keys scan.
- `references/fitness-metrics.md` — metric families + rubrics.
- `references/modal-sandbox-api.md` — Modal v1.3.4 gotchas (Sandbox.create argv list, Image.add_local_file, stdout-after-wait, credential_files VERIFIED).
- `references/fitness-tuning.md` — binary-cliff trap + Orchestrator-sweep methodology (MUST READ before re-dispatching on a failed fitness round).
- `references/worker-timeout-recovery.md` — worker timed out mid-push? Verify remote branch via API, take over the module locally, push via GitHub contents API (don't re-dispatch blindly).
- `scripts/orchestrator_sweep.mjs` — re-runnable Node harness: assemble real branches + run GA × constant sweep to locate the cliff (copy + edit the SWEEP arrays for your project).
- `templates/orchestrator-loop.md` — worker + merge prompt bodies.
- `templates/team-spec.md` — how to spec a dynamic team.
