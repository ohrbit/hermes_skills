# hermes-context-stack

Verify and manage Hermes context-stack files (SOUL.md, user.md, .hermes.md, AGENTS.md) across the default profile and per-profile directories. Use when a user asks whether their SOUL/user/.hermes files are customized or present, suspects customizations are "missing", or when installing/repairing a persona.

## What it does
This skill is defined in [`SKILL.md`](./SKILL.md). Use it for: - User asks whether SOUL.md / user.md / .hermes.md is customized, present, or correct. - User references "the real SOUL.md" or suspects their customizations are gone. - You are about to rely on context-stack files for alignment / user profile / project context. - Setting up or repairing a user's con.

## Install
```bash
hermes skills install hermes-context-stack
```

## Contents
- `SKILL.md` — the skill definition (frontmatter + instructions)
- `references/` — deep-dive docs and code
- `templates/` — prompt / body templates
- `scripts/` — runnable helpers

## Category
`hermes`

---
*This README was generated from `SKILL.md` by scripts/generate_readmes.py.*
