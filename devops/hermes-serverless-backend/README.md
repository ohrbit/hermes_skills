# hermes-serverless-backend

Wire Modal (or Daytona) as the serverless `terminal.backend` for Hermes so agent + subagent shell/execute_code run in ephemeral cloud sandboxes (idle = $0). Covers config keys, token env vars, SDK install, smoke test, pricing, and the critical distinction from MOA (model routing, no compute). Use when the user wants to "run agents in the cloud", "outsource compute", "use Modal/Daytona", "set terminal.backend", reduce idle server cost, or asks how Nous/Hermes spins up cloud agents.

## What it does
This skill is defined in [`SKILL.md`](./SKILL.md). See SKILL.md for the full specification, steps, and pitfalls.

## Install
```bash
hermes skills install hermes-serverless-backend
```

## Contents
- `SKILL.md` — the skill definition (frontmatter + instructions)
- `references/` — deep-dive docs and code
- `templates/` — prompt / body templates
- `scripts/` — runnable helpers

## Category
`devops`

---
*This README was generated from `SKILL.md`. Review and extend it before publishing if needed.*
