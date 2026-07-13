# hermes_skills

A curated collection of [Hermes Agent](https://hermes-agent.nousresearch.com) skills focused on **multi-agent orchestration, JIT agent teams, and the agent execution stack**. Install them with:

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install <skill-name>
```

Skills follow the `agentskills.io` convention: each lives in `category/skill-name/` with a `SKILL.md` plus optional `references/`, `templates/`, and `scripts/`.

---

## 🧩 Orchestration Stack

These skills are designed to work **together**. The mental model:

```
Context (hermes-context-stack)
   └─ Backend (hermes-serverless-backend)  ← Modal / cloud execution
        └─ Teams (jit-agent-teams)         ← ephemeral per-task agent profiles
             └─ Board (kanban-orchestrator) ← durable task tracking
                  └─ Loop (agent-swarm-loop) ← the evolutionary, fitness-gated swarm
             └─ Routing (model-selection-and-jit-routing) ← pick the right model per worker
```

Load `agent-swarm-loop` and it will tell you when to reach for the others.

| Skill | Category | What it does |
|---|---|---|
| **agent-swarm-loop** | `devops` | Generative, evolutionary Kanban-orchestration loop. Brainstorms fitness metrics, invents dynamic expert roles per task, runs all agents on one GitHub workspace (per-agent deploy keys, branch-per-round, PR = fitness gate), and persists a fitness/team registry across projects so the orchestrator gets smarter over time. **Includes Orca-derived patterns:** worker preamble injection, `dispatch_id` correlation, circuit breaker (3 strikes), stale-heartbeat detection, no-local-prompt rule. |
| **jit-agent-teams** | `devops` | Kanban-as-IPC + Modal wedge-recovery. Spawn ephemeral JIT agent-team profiles per task, recover from wedged Modal profiles by flipping to `local`, and resync source from kanban summaries. The building block `agent-swarm-loop` reuses. |
| **kanban-orchestrator** | `devops` | Durable SQLite-backed kanban board shared across Hermes profiles. Tasks are claimed atomically, can depend on each other, and are executed by a named profile in an isolated workspace. Survives restarts; blocked tasks escalate to a human. |
| **model-selection-and-jit-routing** | `devops` | Pick the best *available* model per task and route JIT agent-team profiles to the provider that fits (capability vs. real free-tier limits). Reads a live model matrix + lmarena.ai ranks. Critical: avoids putting rate-limited providers (NVIDIA, Cerebras) or trap-tier Gemini in a parallel fan-out. |
| **hermes-serverless-backend** | `devops` | Wire Modal as `terminal.backend` so agent + subagent shell execution runs serverless on sandboxes. Keeps the host free; documents the credential-mount gotcha (no host env in containers). |
| **hermes-context-stack** | `hermes` | The alignment layer: `SOUL.md` (who the agent is), `USER.md` (who you are), `.hermes.md` (what the project is). Loads before the first message so the agent knows itself, you, and the project before you type a prompt. |

---

## 🚀 Quick start — run a swarm loop

```bash
# 1. Align (context stack) — make sure SOUL.md / USER.md exist
# 2. Wire Modal so workers run in the cloud, not on your host
# 3. Load the loop skill; it guides PHASE 0–4:
hermes skills install agent-swarm-loop
# then in chat: "run a swarm loop for <your task>"
```

The skill will:
1. **Brainstorm fitness metrics** for your domain (you pick + weight).
2. **Provision** a GitHub workspace with per-agent SSH deploy keys (repo-scoped, revocable).
3. **Invent** expert roles dynamically and dispatch them in parallel.
4. **Fitness-gate** each round; only improvements survive.
5. **Persist** the team-shape + fitness to a registry for the next project.

---

## ⚠️ Security notes (read before publishing)

- **Never inline private keys in worker prompts or skill files.** Hermes redacts secrets embedded in tool-call text, so the worker receives an empty key and the push fails. Mount keys via `terminal.credential_files` or `Image.add_local_file` instead.
- **Per-agent deploy keys, not a shared master token.** One key per agent = one revocable, repo-scoped credential. GitHub PATs cannot be minted via API; deploy keys can.
- **Circuit breaker:** a wedged worker is re-dispatched at most 3×, then escalated. Blind retries burn tokens.
- All skill files in this repo contain **placeholders only** (`<priv key text>`, `<YOUR_ROLE>`, `<owner>/<repo>`). Substitute real values at runtime via mounted secrets.

---

## 📂 Repository layout

```
hermes_skills/
├── README.md
├── devops/
│   ├── agent-swarm-loop/      # the evolutionary loop (Orca-derived)
│   ├── jit-agent-teams/       # ephemeral JIT profiles + Modal recovery
│   ├── kanban-orchestrator/   # durable task board
│   ├── model-selection-and-jit-routing/  # model + provider routing
│   └── hermes-serverless-backend/         # Modal wiring
└── hermes/
    └── hermes-context-stack/  # SOUL.md / USER.md / .hermes.md
```

---

## 🔗 Related

- Hermes Agent docs: https://hermes-agent.nousresearch.com/docs/
- Agent skills spec: https://agentskills.io
- Inspiration for the loop's coordination contract: Orca (`stablyai/orca`) dispatch/preamble/lifecycle-reconciliation model.
