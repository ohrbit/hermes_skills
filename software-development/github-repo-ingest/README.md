# GitHub Repo Ingest — Shallow-First Protocol

> **Ingest a GitHub repo for LLM context without dumping the whole thing** — README + tree first, then targeted deep dives.

## Why this skill?

Pointing an LLM at a full repo burns tokens and buries signal. The shallow-first protocol starts with structure (README + tree + token estimate), then selectively pulls only the directories/files that matter. You stay focused and under context budget.

## What it does

- ✅ Shallow pass — README + directory tree + token estimate only
- ✅ Deep-dive pass — target specific subdirs / file types / benchmarks
- ✅ Include/exclude pattern filtering
- ✅ Size caps to keep context lean
- ✅ Python API (`ingest` / `ingest_async`) for automation

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install github-repo-ingest
pipx install gitingest    # or: pip install gitingest
```

## Quick Start

```bash
# shallow: just README + structure
gitingest https://github.com/owner/repo -i "README*" -i "*.md" -s 51200 -o -
```

## How it works

```
shallow (README + tree)  →  decide what matters  →  deep-dive (specific paths)
```

Never dump the full repo. Each pass is scoped by `--include-pattern` / `--max-size`.

## Usage / Examples

### Basic
> "What's in this repo?"

Shallow pass → you see the tree + token count before committing to a deep read.

### Advanced
> "Show me just the optimizer and engine code."

```bash
gitingest <repo> -i "skillopt/optimizer/*" -i "skillopt/engine/*" -s 102400 -o -
```

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Shallow/deep protocol, Python integration |

## Related skills

- `gitingest-usage` — the full GitIngest CLI/flag reference
- `third-party-skill-evaluation` — vet external repos before adopting

## Notes / caveats

- Prefer `gitingest` over `web_extract` for any git repo URL.
- Exclude `tests/`, `ckpt/`, `docs/` in deep dives to save tokens.

## License

MIT — © 2024 ohrbit
