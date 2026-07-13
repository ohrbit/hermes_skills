# kanban-orchestrator

Decomposition playbook + anti-temptation rules for an orchestrator profile routing work through Kanban. The "don't do the work yourself" rule and the basic lifecycle are auto-injected into every kanban worker's system prompt; this skill is the deeper playbook when you're specifically playing the orchestrator role.

## What it does
This skill is defined in [`SKILL.md`](./SKILL.md). See SKILL.md for the full specification, steps, and pitfalls.

## Install
```bash
hermes skills install kanban-orchestrator
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
