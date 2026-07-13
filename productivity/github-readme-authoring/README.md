# GitHub README Authoring

> **Write production-grade README.md files** — install → try → understand → trust → contribute. Works for both code packages and Hermes skills.

## Why this skill?

Most READMEs lose the visitor in the first scroll: no install command, no runnable example, vague "contributions welcome." This skill is the structure that converts a viewer into a user — and (updated for this repo) it now covers **Hermes skills** too, not just Python packages.

## What it does

- ✅ Required section order (title → tagline → why → features → install → example → usage → config → contributing → license)
- ✅ Badge templates (CI, version, license, downloads, Discord)
- ✅ Anti-patterns table (wall-of-text, no example, vague contrib)
- ✅ Real-world reference READMEs (httpx, rich, fastapi, pydantic, ruff)
- ✅ **Hermes Skill Mode** — structure for `SKILL.md`-based skills (install via `hermes skills install`, chat trigger instead of code example)
- ✅ Pre-publish checklist

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install github-readme-authoring
```

## Quick Start

```text
In chat: "write a README for this project"  (or for a Hermes skill: "write the skill's README")
```

## How it works

**Decision:** repo is a code library/CLI → use the package template. Repo/folder is a Hermes skill (`SKILL.md` present) → use Hermes Skill Mode.

Package mode leads with `pip install` + a 5–10 line runnable example. Hermes mode leads with `hermes skills install` + a chat trigger, and swaps the API-reference section for a file-layout table.

## Usage / Examples

### Basic (package)
> "README for my Flask API."

Produces: tagline, problem statement, features, `pip install`, minimal `app.run()` example, CLI/API ref, config table, contributing, license.

### Basic (Hermes skill)
> "README for agent-swarm-loop."

Uses Hermes Skill Mode: tagline, why, what-it-does, `hermes skills install`, how-it-works ASCII, examples, file layout, related skills, caveats.

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Both modes, anti-patterns, checklist |
| `templates/README.template.md` | Copy-paste package template |
| `references/` | Extended examples |

## Related skills

- `gitingest-usage` — research existing READMEs before writing (`gitingest <repo> -i "README*"`)
- `github-repo-ingest` — shallow-first repo analysis

## Notes / caveats

- Generate the README FROM the skill/package frontmatter but **expand by hand** — never ship a stub that only echoes the description.
- Badges must render (click to verify) and license file must match the badge.

## License

MIT — © 2024 ohrbit
