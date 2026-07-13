---
name: kanban-orchestrator
description: Decomposition playbook + anti-temptation rules for an orchestrator profile routing work through Kanban. The "don't do the work yourself" rule and the basic lifecycle are auto-injected into every kanban worker's system prompt; this skill is the deeper playbook when you're specifically playing the orchestrator role.
version: 3.1.0
platforms: [linux, macos, windows]
environments: [kanban]
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, routing]
    related_skills: [kanban-worker]
---

# Kanban Orchestrator — Decomposition Playbook

> The **core worker lifecycle** (including the `kanban_create` fan-out pattern and the "decompose, don't execute" rule) is auto-injected into every kanban process via the `KANBAN_GUIDANCE` system-prompt block. This skill is the deeper playbook when you're an orchestrator profile whose whole job is routing.

## Profiles are user-configured — not a fixed roster

Hermes setups vary widely. Some users run a single profile that does everything; some run a small fleet (`docker-worker`, `cron-worker`); some run a curated specialist team they've named themselves. There is **no default specialist roster** — the orchestrator skill does not know what profiles exist on this machine.

**IMPORTANT:** The preferred pattern is JIT (Just-In-Time) profile creation per project (see §JIT below). Do NOT rely on pre-existing profiles unless the user explicitly asks you to. Creating profiles on-the-fly for each project is the correct default.

Before fanning out, you must ground the decomposition in the profiles that actually exist (or create them JIT). The dispatcher silently fails to spawn unknown assignee names — it doesn't autocorrect, doesn't suggest, doesn't fall back. So a card assigned to `researcher` on a setup that only has `docker-worker` just sits in `ready` forever.

**Step 0: decide: use existing profiles or create JIT?**
- If the task has clear, separable roles (UI, Engine, GFX, Merge) → **create JIT profiles** (see ⚡ JIT section below)
- If the task is a one-off or the user has a dedicated profile for this type of work → use existing profiles
- If unsure → ask the user. "Should I create specialized profiles for this project, or use an existing one?"

**Step 1: if using existing profiles, discover them.**
- `hermes profile list` — prints the table of profiles configured on this machine.
- `kanban_list(assignee="<some-name>")` — sanity-check a single name.
- **Just ask the user.** "What profiles do you have set up?" is a fine first turn when the goal needs more than one specialist.
- `hermes profile list` — prints the table of profiles configured on this machine. Run it through your terminal tool if you have one; otherwise ask the user.
- `kanban_list(assignee="<some-name>")` — sanity-check a single name. Returns an empty list (rather than an error) for an unknown assignee, so this only confirms a name you're already considering.
- **Just ask the user.** "What profiles do you have set up?" is a fine first turn when the goal needs more than one specialist.

Cache the result in your working memory for the rest of the conversation. Re-asking every turn wastes a tool call.

## ⚡ JIT (Just-In-Time) Agent Teams — the preferred pattern

**The user's explicit correction from this session:** Do NOT pre-define specialist profiles. When a task arrives, CREATE the team on-the-fly: analyze the task, determine the roles needed, create profiles per role, dispatch, then clean up.

*Old (wrong) approach:* "I have a cloud-worker profile. Let me assign all tasks to it."
*JIT (correct) approach:* "Gravity Swarm needs UI, physics engine, rendering, and a merge. Let me create 4 profiles: gs-ui, gs-engine, gs-gfx, gs-merge. Each gets its own specs and `terminal.backend: modal`. After they finish, I delete the profiles."

### Why JIT beats fixed profiles

| Aspect | Fixed profiles | JIT teams |
|--------|---------------|-----------|
| Flexibility | Pre-defined roles may not fit the task | Roles match the task exactly |
| Parallelism | One profile → one worker at a time | N profiles → N workers in parallel |
| Cleanup | Orphan profiles accumulate | Profile deleted after project done |
| Cognitive load | "Which existing profile fits?" | "What roles does this task need?" |
| Cost | Profile sits idle between tasks | Profile exists only during work |

### JIT team workflow

1. Analyze task → identify roles needed (UI? Engine? GFX? Merge?)
2. For each role: create a project-prefixed profile (e.g. `gs-ui`)
3. Write its config.yaml with `terminal.backend: modal` + model + delegation
4. Write its `.env` with Modal tokens (each needs its own)
5. Create Kanban cards: one per role, assigned to its JIT profile
6. Merge card with `--parent` links to all role cards
7. After all done → delete all JIT profiles

### Concrete example (Gravity Swarm, 4 roles)

```bash
# 1. Create JIT profiles with project prefix
for name in gs-ui gs-engine gs-gfx gs-merge; do
  hermes profile create "$name"
  cat > ~/.hermes/profiles/$name/config.yaml << CFG
terminal:
  backend: modal
  modal_mode: auto
  cwd: .
  timeout: 300
model:
  default: tencent/hy3:free
  provider: nous
CFG
  echo "MODAL_TOKEN_ID=ak-..." > ~/.hermes/profiles/$name/.env
  echo "MODAL_TOKEN_SECRET=as-..." >> ~/.hermes/profiles/$name/.env
done

# 2. Create cards (one per role, merge waits on parents)
t1=$(hermes kanban create "GS: UI & Cinematic Shell" --assignee gs-ui --goal --body "spec")
t2=$(hermes kanban create "GS: n-Body & Evolution Engine" --assignee gs-engine --goal --body "spec")
t3=$(hermes kanban create "GS: Canvas Rendering & Trails" --assignee gs-gfx --goal --body "spec")
hermes kanban create "GS: Merge" --assignee gs-merge --goal \
  --parent "$t1" "$t2" "$t3" --body "Assemble final output from all 3 parents"

# 3. After completion — cleanup
for name in gs-ui gs-engine gs-gfx gs-merge; do
  hermes profile delete "$name"
done
```

### When NOT to use JIT teams

- Quick one-off tasks (use `delegate_task` instead — lighter weight)
- Tasks that always need the same specialist (e.g. a dedicated cron worker profile)
- The user explicitly asks you to use an existing profile

### File sharing between JIT workers (Modal sandbox → host)

Workers on Modal sandboxes have **isolated ephemeral filesystems**. `write_file` and terminal writes vanish when the sandbox terminates. To transfer artifacts from Modal to the host:

**Primary: `cat` to stdout (always works, no network)**

Add to every worker's task body: "AFTER BUILDING: print the FULL file content via `cat`." The output appears in the Kanban task log. The merge worker reads parent task summaries and extracts file content:

```bash
# Worker task body:
# 1. write_file /tmp/artifact
# 2. cat /tmp/artifact
# 3. kanban_complete(summary="<cat output>")

# Merge worker reads parents:
hermes kanban show <parent-id>   # look for file content in summary
```

**Avoids:** network issues, double-token cost, Modal volume complexity.

**Fallback: HTTP PUT receiver (local-backend only)**

The HTTP receiver (`scripts/start-upload-receiver.sh`) works when workers have `terminal.backend: local`. Start on host, workers `curl PUT` artifacts:

```bash
ufw allow 19999/tcp comment 'modal-worker-upload'
# Start receiver (background)
TOKEN="project-$(openssl rand -hex 8)"
python3 -u -c "..." &
# Worker (local only):
curl -X PUT --data-binary @/tmp/artifact -H 'X-Token: $TOKEN' \
  http://127.0.0.1:19999/root/fable-suite/project/artifact
```

⚠️ **Known limitation:** Modal sandboxes CANNOT reach the Hetzner host's private ports despite UFW being open — they time out even on 66.179.94.165:19999. The receiver only works from local-backend workers. Test before dispatching: `curl -m 5 http://<HOST_IP>:<PORT>/` from a Modal sandbox.

**Not recommended:** shared `dir:<path>` workspace, Modal Volumes (`modal.Volume.from_name()`) — Kanban workers have no control over Sandbox creation parameters and cannot mount volumes.

**Token pitfalls for HTTP mode:**
- Use `printf '%s' "$TOKEN"` not `echo` (no trailing newline)
- Verify before dispatch: `curl -m 5 http://<HOST_IP>:<PORT>/`
- Kill after project: `fuser -k <PORT>/tcp`

### Pitfalls

- **Profile names must be unique** — use a project prefix (`gs-`, `dd-`, `fp-`).
- **Dispatcher serializes same-profile tasks** — different profiles = true parallelism.
- **Don't forget the `.env` with Modal tokens** — each JIT profile needs its own `.env` or it inherits from default (which may not have Modal tokens).
- **Clean up after** — orphan profiles clutter `hermes profile list` and consume namespace.
- **The `--goal` flag is correct, not `--goal-mode`** — confirmed on current Hermes CLI (`v0.18.2`).
- **Create Kanban cards ONE AT A TIME, not chained** — shell variable pollution (`$t1`, `$t2`) from `hermes kanban create` output breaks the next command when chained with `&&`. Always capture each card id separately in a clean command:
  ```bash
  t1=$(hermes kanban create "Title A" --assignee worker --goal --body "spec")
  t2=$(hermes kanban create "Title B" --assignee worker --goal --body "spec")
  # ...then create merge with parents
  hermes kanban create "Merge" --assignee merge --goal --parent "$t1" "$t2"
  ```
  Do NOT: `t1=$(...) && t2=$(...) && merge=$(...)` — the `hermes` CLI outputs extra text that pollutes the next command's arguments.

## When to use the board (vs. just doing the work)

Create Kanban tasks when any of these are true:

1. **Multiple specialists are needed.** Research + analysis + writing is three profiles.
2. **The work should survive a crash or restart.** Long-running, recurring, or important.
3. **The user might want to interject.** Human-in-the-loop at any step.
4. **Multiple subtasks can run in parallel.** Fan-out for speed.
5. **Review / iteration is expected.** A reviewer profile loops on drafter output.
6. **The audit trail matters.** Board rows persist in SQLite forever.

If *none* of those apply — it's a small one-shot reasoning task — use `delegate_task` instead or answer the user directly.

## The anti-temptation rules

Your job description says "route, don't execute." The rules that enforce that:

- **Do not execute the work yourself.** Your restricted toolset usually doesn't even include terminal/file/code/web for implementation. If you find yourself "just fixing this quickly" — stop and create a task for the right specialist.
- **For any concrete task, create a Kanban task and assign it.** Every single time.
- **Split multi-lane requests before creating cards.** A user prompt can contain several independent workstreams. Extract those lanes first, then create one card per lane instead of bundling unrelated work into a single implementer card.
- **Run independent lanes in parallel.** If two cards do not need each other's output, leave them unlinked so the dispatcher can fan them out. Link only true data dependencies.
- **Never create dependent work as independent ready cards.** If a card must wait for another card, pass `parents=[...]` in the original `kanban_create` call. Do not create it first and link it later, and do not rely on prose like "wait for T1" inside the body.
- **If no specialist fits the available profiles, ask the user which profile to create or which existing profile to use.** Do not invent profile names; the dispatcher will silently drop unknown assignees.
- **Decompose, route, and summarize — that's the whole job.**

## Decomposition playbook

### Step 1 — Understand the goal

Ask clarifying questions if the goal is ambiguous. Cheap to ask; expensive to spawn the wrong fleet.

### Step 2 — Sketch the task graph

Before creating anything, draft the graph out loud (in your response to the user). Treat every concrete workstream as a candidate card:

1. Extract the lanes from the request.
2. Map each lane to one of the profiles you discovered in Step 0. If a lane doesn't fit any existing profile, ask the user which to use or create.
3. Decide whether each lane is independent or gated by another lane.
4. Create independent lanes as parallel cards with no parent links.
5. Create synthesis/review/integration cards with parent links to the lanes they depend on. A child created with unfinished parents starts in `todo`; the dispatcher promotes it to `ready` only after every parent is done.

Examples of prompts that should fan out (using placeholder profile names — substitute whatever exists on the user's setup):

- "Build an app" → one card to a design-oriented profile for product/UI direction, one or two cards to engineering profiles for implementation, plus a later integration/review card if the user has a reviewer profile.
- "Fix blockers and check model variants" → one implementation card for the blocker fixes plus one discovery/research card for config/source verification. A final reviewer card can depend on both.
- "Research docs and implement" → a docs-research card can run in parallel with a codebase-discovery card; implementation waits only if it truly needs those findings.
- "Analyze this screenshot and find the related code" → one card to a vision-capable profile for the visual analysis while another searches the codebase.

Words like "also," "finally," or "and" do not automatically imply a dependency. They often mean "make sure this is covered before reporting back." Only link tasks when one card cannot start until another card's output exists.

Show the graph to the user before creating cards. Let them correct it — including which actual profile name should own each lane.

### Step 3 — Create tasks and link

Use the profile names from Step 0. The example below uses placeholders `<profile-A>`, `<profile-B>`, `<profile-C>` — replace them with what the user actually has.

```python
t1 = kanban_create(
    title="research: Postgres cost vs current",
    assignee="<profile-A>",  # whichever profile handles research on this setup
    body="Compare estimated infrastructure costs, migration costs, and ongoing ops costs over a 3-year window. Sources: AWS/GCP pricing, team time estimates, current Postgres bills from peers.",
    tenant=os.environ.get("HERMES_TENANT"),
)["task_id"]

t2 = kanban_create(
    title="research: Postgres performance vs current",
    assignee="<profile-A>",  # same profile, run in parallel
    body="Compare query latency, throughput, and scaling characteristics at our expected data volume (~500GB, 10k QPS peak). Sources: benchmark papers, public case studies, pgbench results if easy.",
)["task_id"]

t3 = kanban_create(
    title="synthesize migration recommendation",
    assignee="<profile-B>",  # whichever profile does synthesis/analysis
    body="Read the findings from T1 (cost) and T2 (performance). Produce a 1-page recommendation with explicit trade-offs and a go/no-go call.",
    parents=[t1, t2],
)["task_id"]

t4 = kanban_create(
    title="draft decision memo",
    assignee="<profile-C>",  # whichever profile drafts user-facing prose
    body="Turn the analyst's recommendation into a 2-page memo for the CTO. Match the tone of previous decision memos in the team's knowledge base.",
    parents=[t3],
)["task_id"]
```

`parents=[...]` gates promotion — children stay in `todo` until every parent reaches `done`, then auto-promote to `ready`. No manual coordination needed; the dispatcher and dependency engine handle it.

If the task graph has dependencies, create the parent cards first, capture their returned ids, and include those ids in the child card's `parents` list during the child `kanban_create` call. Avoid creating all cards in parallel and linking them afterward; that creates a window where the dispatcher can claim a child before its inputs exist.

### Step 4 — Complete your own task

If you were spawned as a task yourself (e.g. a planner profile was assigned `T0: "investigate Postgres migration"`), mark it done with a summary of what you created:

```python
kanban_complete(
    summary="decomposed into T1-T4: 2 research lanes in parallel, 1 synthesis on their outputs, 1 prose draft on the recommendation",
    metadata={
        "task_graph": {
            "T1": {"assignee": "<profile-A>", "parents": []},
            "T2": {"assignee": "<profile-A>", "parents": []},
            "T3": {"assignee": "<profile-B>", "parents": ["T1", "T2"]},
            "T4": {"assignee": "<profile-C>", "parents": ["T3"]},
        },
    },
)
```

### Step 5 — Report back to the user

Tell them what you created in plain prose, naming the actual profiles you used:

> I've queued 4 tasks:
> - **T1** (`<profile-A>`): cost comparison
> - **T2** (`<profile-A>`): performance comparison, in parallel with T1
> - **T3** (`<profile-B>`): synthesizes T1 + T2 into a recommendation
> - **T4** (`<profile-C>`): turns T3 into a CTO memo
>
> The dispatcher will pick up T1 and T2 now. T3 starts when both finish. You'll get a gateway ping when T4 completes. Use the dashboard or `hermes kanban tail <id>` to follow along.

## Common patterns

**Fan-out + fan-in (research → synthesize):** N research-style cards with no parents, one synthesis card with all of them as parents.

**Parallel implementation + validation:** one implementer card makes the change while one explorer/researcher card verifies config, docs, or source mapping. A reviewer card can depend on both. Do not make the implementer own unrelated verification just because the user mentioned both in one sentence.

**Pipeline with gates:** `planner → implementer → reviewer`. Each stage's `parents=[previous_task]`. Reviewer blocks or completes; if reviewer blocks, the operator unblocks with feedback and respawns.

**Parallel same-profile fan-out (proven on Modal):** N tasks, all assigned to the same profile, no dependencies between them. The dispatcher **fans them out in parallel** — each task claims its own terminal sandbox, all run simultaneously under the same profile. Verified with 3 FABLE-style builds all running concurrently with `hostname=modal`. This is the primary pattern for \"spawn N agents on cloud compute\" without configuring multiple profiles.

**Passing skills to workers:** When tasks need specialist knowledge (e.g. the `fable-style-singlefile-web` skill for FABLE-style HTML builds), pass `--skill`:

```bash
hermes kanban create "Desert Grand Prix" \
  --assignee cloud-worker \
  --skill "fable-style-singlefile-web" \
  --goal --goal-max-turns 10 \
  --body "..."
```

The `--goal` flag (confirmed: `--goal` not `--goal-mode` in current Hermes CLI) enables persistent worker loop with judge review. See Goal-mode cards below for full semantics.

**Human-in-the-loop:** Any task can `kanban_block()` to wait for input. Dispatcher respawns after `/unblock`. The comment thread carries the full context.

## Pitfalls

**Chained `hermes kanban create` commands break.** Shell variable capture (`t1=$(hermes kanban create ...)`) produces output that pollutes the next command when chained with `&&`. The CLI prints "Created t_xxx (ready, assignee=profile)" which arrives as the next command's argument → "unrecognized arguments" error. Create cards in separate terminal calls, or capture ids one-by-one:

```bash
# WRONG — chaining breaks:
t1=$(hermes kanban create "A" --assignee x --body "spec") && \
t2=$(hermes kanban create "B" --assignee x --body "spec")

# CORRECT — separate calls:
t1=$(hermes kanban create "A" --assignee x --body "spec")
t2=$(hermes kanban create "B" --assignee x --body "spec")
hermes kanban create "Merge" --parent "$t1" "$t2" --assignee merge --body "..."
```

**Profile same-namespace with merge tasks:** Verify all parent task IDs are valid before creating the child. A failed parent `create` leaves the variable empty, and `--parent "$t1" ""` attaches only the first parent.

**Inventing profile names that don't exist.** The dispatcher silently fails to spawn unknown assignees — the card just sits in `ready` forever. Always assign to a profile from your Step 0 discovery; ask the user if you're unsure.

**Bundling independent lanes into one card.** If the user asks for two independent outcomes, create two cards. Example: "fix blockers and check model variants" is not one fixer task; create a fixer/engineer card for the fixes and an explorer/researcher card for the variant check, then optionally gate review on both.

**Over-linking because of wording.** "Finally check X" may still be parallel with implementation if X is static config, docs, or source discovery. Link it after implementation only when the check depends on the implementation result.

**Forgetting dependency links.** If the task graph says `research -> implement -> review`, do not create all tasks as independent ready cards. Use parent links so implement/review cannot run before their inputs exist.

**Reassignment vs. new task.** If a reviewer blocks with "needs changes," create a NEW task linked from the reviewer's task — don't re-run the same task with a stern look. The new task is assigned to the original implementer profile.

**Argument order for links.** `kanban_link(parent_id=..., child_id=...)` — parent first. Mixing them up demotes the wrong task to `todo`.

**Don't pre-create the whole graph if the shape depends on intermediate findings.** If T3's structure depends on what T1 and T2 find, let T3 exist as a "synthesize findings" task whose own first step is to read parent handoffs and plan the rest. Orchestrators can spawn orchestrators.

**Tenant inheritance.** If `HERMES_TENANT` is set in your env, pass `tenant=os.environ.get("HERMES_TENANT")` on every `kanban_create` call so child tasks stay in the same namespace.

## Goal-mode cards (persistent workers)

By default a dispatched worker gets **one shot** at its card: it does its work, calls `kanban_complete`/`kanban_block`, and exits. For open-ended cards where one turn rarely finishes the job, pass `goal_mode=True` to wrap that worker in a Ralph-style goal loop — the same engine behind the `/goal` slash command:

```python
kanban_create(
    title="Translate the full docs site to French",
    body="Acceptance: every page translated, no English left, links intact.",
    assignee="<translator-profile>",
    goal_mode=True,        # judge re-checks the card after each turn
    goal_max_turns=15,     # optional budget (default 20)
)["task_id"]
```

How it behaves:
- After each worker turn, an auxiliary judge evaluates the worker's response against the card's **title + body** (treated as the acceptance criteria).
- Not done + budget remains → the worker keeps going **in the same session** (full context retained — not a fresh respawn).
- Worker calls `kanban_complete`/`kanban_block` itself → loop stops, normal lifecycle.
- Budget exhausted without completion → the card is **blocked** for human review (sticky), never a silent exit.

When to use it: long, multi-step, or "keep going until X is true" cards. When NOT to: cheap one-shot cards (translation of a single string, a quick lookup) — the judge overhead isn't worth it, and the dispatcher's existing retry/circuit-breaker already handles transient worker failures.

Write the body as **explicit acceptance criteria** — the judge is only as good as the goal text. "Translate the README" is weaker than "Translate every section of the README to French; no English sentences remain."

## Recovering stuck workers

When a worker profile keeps crashing, hallucinating, or getting blocked by its own mistakes (usually: wrong model, missing skill, broken credential), the kanban dashboard flags the task with a ⚠ badge and opens a **Recovery** section in the drawer. Three primary actions:

1. **Reclaim** (or `hermes kanban reclaim <task_id>`) — abort the running worker immediately and reset the task to `ready`. The existing claim TTL is ~15 min; this is the fast path out.
2. **Reassign** (or `hermes kanban reassign <task_id> <new-profile> --reclaim`) — switch the task to a different profile (one that exists on this setup) and let the dispatcher pick it up with a fresh worker.
3. **Change profile model** — the dashboard prints a copy-paste hint for `hermes -p <profile> model` since profile config lives on disk; edit it in a terminal, then Reclaim to retry with the new model.

Hallucination warnings appear on tasks where a worker's `kanban_complete(created_cards=[...])` claim included card ids that don't exist or weren't created by the worker's profile (the gate blocks the completion), or where the free-form summary references `t_<hex>` ids that don't resolve (advisory prose scan, non-blocking). Both produce audit events that persist even after recovery actions — the trail stays for debugging.
