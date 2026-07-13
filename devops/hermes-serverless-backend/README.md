# Hermes Serverless Backend (Modal / Daytona)

> **Run Hermes agent + subagent compute in ephemeral cloud sandboxes** — idle cost $0, no host box needed. Wire Modal or Daytona as `terminal.backend`.

## Why this skill?

By default Hermes runs shell/`execute_code` on your host. That's fine until you want parallel agents without melting your laptop, or you want compute to disappear when idle. Modal/Daytona give true serverless execution — but the setup has sharp edges (wrong token page, read-guarded `.env`, PEP 668, sandbox exec quirks). This skill is the battle-tested setup path.

## What it does

- ✅ Wires `terminal.backend: modal` (or `daytona`) so ALL `terminal` + `execute_code` + subagent shells run in sandboxes
- ✅ Documents the 6 Hermes backends and why AWS/Azure are NOT serverless
- ✅ Clarifies the Modal-vs-MOA distinction (compute vs model routing)
- ✅ Smoke-test script that proves sandboxes actually spin up
- ✅ Real pricing (CPU/mem/GPU rates, $30/mo free credit)
- 🔄 Daytona = persistent workspaces; Modal = ephemeral (flip per need)

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install hermes-serverless-backend
```

## Quick Start

```bash
hermes config set terminal.backend modal
printf '\nMODAL_TOKEN_ID=<id>\nMODAL_TOKEN_SECRET=<secret>\n' >> /root/.hermes/.env
pip install --break-system-packages modal
hermes config show   # → Backend: modal
```

## How it works

```
host (LLM loop stays here)
   │
   └─ terminal / execute_code / subagent shell
          │  routes to
          ▼
   Modal sandbox (ephemeral, idle = $0)
```

`delegate_task` subagents: their *LLM reasoning* stays on host; only their *shell exec* lands in the cloud.

## Usage / Examples

### Basic
> "Set Hermes to run agents in the cloud."

Follows Setup (Modal): token from **Settings → Tokens** (not the Secrets page), write creds to `.env` via terminal, install SDK, smoke test.

### Advanced
Pair with `jit-agent-teams`: each JIT profile gets `terminal.backend: modal` → N parallel cloud workers, zero host load.

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Setup, backends, pitfalls, verification checklist |
| `references/smoke-test.md` | Full sandbox spin-up script |
| `references/pricing.md` | Cost model |

## Related skills

- `jit-agent-teams` — ephemeral profiles that use this backend
- `agent-swarm-loop` — the swarm runs on Modal via this wiring

## Notes / caveats

- **Token location:** Settings → Tokens → Create token (Full access). The dashboard "Secrets" page is for app env vars — wrong place.
- **`.env` is read-guarded** — append via terminal, never `read_file`/`patch` it.
- **Sandbox `exec` with separate args does no shell expansion** — use `bash -c` for `$(...)`.
- **Token in chat = exposed** — rotate in Modal after setup.

## License

MIT — © 2024 ohrbit
