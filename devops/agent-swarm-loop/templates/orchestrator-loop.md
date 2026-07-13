# Orchestrator Loop — Worker & Merge Prompt Bodies

Drop these into `hermes kanban create ... --body "$(cat ...)"` or the
`delegate_task` context. They assume PHASE 0/1 already ran: metrics chosen,
deploy key (or `.env`) provisioned, base branch exists.

## WORKER BODY (per dynamic expert)
```
ROLE: <role>   ROUND: <round>   BASE: <base-branch>
TASK_ID: <kanban-card-id>   DISPATCH_ID: <attempt-n>   # attempt-n = 1 for first try, +1 per retry
REPO: git@github.com:<owner>/<repo>.git
PRIV KEY (write to ~/.ssh/id_ed25519, chmod 600):
-----BEGIN OPENSSH PRIVATE KEY-----
<priv key text>
-----END OPENSSH PRIVATE KEY-----

TASK: <goal for this expert>

=== WORKER PREABLE (coordination contract — follow exactly) ===
You are a dispatched worker in a multi-agent swarm. You talk to the Orchestrator
ONLY through kanban state + this contract. Rules:
1. REPORT ONCE: when done (even on failure), call
   kanban_complete(summary="ROLE: <role>\nCHANGES: <concrete>\nFILES: <paths>\nEVAL: <how metric evaluates this PR>\nPR: <url>", task_id=<TASK_ID>, dispatch_id=<DISPATCH_ID>).
   Never silently exit. Failure is still a kanban_complete with subject "Failed: <reason>".
2. HEARTBEAT: every ~5 min while actively working, emit a short progress note
   (e.g. a kanban comment on <TASK_ID>) with phase: investigating|implementing|reviewing.
   This proves you are alive, not hung. This is NOT your final complete.
3. NO LOCAL PROMPTS: never use AskUserQuestion / interactive TUI prompts — the
   Orchestrator cannot see or answer them and your session hangs forever. If you
   need a decision, STOP and call kanban block (decision gate) on <TASK_ID>.
4. CORRELATION: every message carries BOTH task_id and dispatch_id. A stale
   completion from a previous attempt must not complete this dispatch.

STEPS:
1. Setup git access:
   mkdir -p ~/.ssh && chmod 700 ~/.ssh
   write the PRIV KEY above to ~/.ssh/id_ed25519 (chmod 600)
   export GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519"
2. Clone + branch:
   git clone <REPO> /tmp/work && cd /tmp/work
   git checkout <BASE> && git checkout -b feat/<round>-<role>
3. DO THE WORK: <goal>. Build/run locally if the env supports it. Emit heartbeat comments every ~5 min.
4. Commit + push:
   git add -A && git commit -m "<role>: <what changed>" && git push -u origin feat/<round>-<role>
5. Open PR against <BASE> (use `gh pr create` if gh is authed, else GitHub API).
6. COMPLETE: kanban_complete(summary=
   "ROLE: <role>
    CHANGES: <what you built/changed, concrete>
    FILES: <paths touched>
    EVAL: <how the chosen fitness metric should be evaluated on this PR>
    PR: <url if created>",
    task_id=<TASK_ID>, dispatch_id=<DISPATCH_ID>)
   The summary MUST let the merge worker evaluate your contribution.
```

## MERGE WORKER BODY (round orchestrator)
```
ROUND: <round>   PARENTS: <t_ui> <t_engine> ...   BASE: <base-branch>
REPO: <owner>/<repo>
FITNESS WEIGHTS: <w_tests> <w_judge> <w_perf> ... (sum=1.0)
METRIC DETAIL: <from PHASE 0 pick>

STEPS:
1. Wait until all parent tasks are done (kanban auto-promotes from todo).
   For each parent, VERIFY dispatch_id correlation: only accept a kanban_complete
   whose dispatch_id matches the LIVE attempt for that task_id. Ignore stale
   completions from failed/older attempts (a retried worker's late "done" must
   not complete the current dispatch).
2. For each parent PR:
   - fetch branch, check out
   - RUN the fitness eval per PHASE-0 metric (tests / LLM-judge / perf)
   - compute composite fitness vs round baseline (current <BASE> fitness)
3. SELECTION: only PRs with fitness > baseline survive.
   - survivors: merge into <BASE>
   - rejects: close PR, note fitness_delta<0 in registry
4. TRACK failure_count per parent (circuit breaker): if a parent failed/timeout
   and failure_count < 3, re-dispatch with dispatch_id+1. At >=3, mark failed and
   escalate to the user (decision gate) — do NOT keep retrying.
5. Record to ~/.hermes/swarm-registry.json:
   { round, survivors:[roles], fitness, delta_vs_baseline, dispatch_ids:{role:attempt} }
6. If delta>0 AND not plateaued: kanban_complete(summary="round <round> fitness=<f> delta=+<d> → continue")
   else: stop, finalise registry.
```

## Registry seed (PHASE 4, cross-project learning)
After project, append:
```json
{
  "projects": { "<name>": {
     "domain": "...", "metrics": {...weights}, "best_fitness": 0.91,
     "winning_team_shape": ["role-a","role-b"], "rounds": 4 } },
  "expert_taxonomy": { "role-x": {
     "worked_on": ["domain-a"], "avg_fitness_delta": 0.07 } }
}
```
Next project: Orchestrator reads this to seed a better initial team shape +
default metric weights → evolutionary improvement.
