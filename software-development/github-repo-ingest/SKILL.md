---
name: github-repo-ingest
description: Shallow-first GitHub repository ingestion using gitingest CLI. Start with README + structure, then selectively deep-dive into specific directories/files.
category: software-development
---

# GitHub Repo Ingest — Shallow-First Protocol

## Core Principle
**Never dump the full repo.** Start shallow (README + tree), then target specific subdirs/files. This avoids token bloat and keeps context focused.

## Installation (one-time)
```bash
pipx install gitingest    # preferred (isolated)
# or: pip install gitingest
```

## Shallow Pass — Default Entry Point
```bash
# Just README + directory tree + token estimate
gitingest https://github.com/owner/repo \
  --include-pattern "README*" \
  --include-pattern "*.md" \
  --max-size 51200 \
  -o -
```

**Output gives you:**
- Repository summary (files, tokens)
- Full directory tree
- Only README/markdown files (small, high-signal)

## Deep-Dive Pass — Targeted
```bash
# Specific subdirectory (e.g., core optimizer)
gitingest https://github.com/owner/repo \
  --include-pattern "skillopt/optimizer/*" \
  --max-size 102400 \
  -o -

# Specific file types only
gitingest https://github.com/owner/repo \
  -i "*.py" -i "*.yaml" -i "*.md" \
  -e "tests/*" -e "ckpt/*" -e "docs/*" \
  -s 102400 \
  -o -

# Specific benchmark/env
gitingest https://github.com/owner/repo \
  -i "skillopt/envs/searchqa/*" \
  -o -
```

## Python Integration (for scripts/automation)
```python
from gitingest import ingest, ingest_async

# Shallow first
summary, tree, content = ingest(
    "https://github.com/owner/repo",
    include_patterns=["README*", "*.md"],
    max_file_size=51200,
)

# Then deep-dive selectively
summary, tree, content = ingest(
    "https://github.com/owner/repo",
    include_patterns=["skillopt/optimizer/*", "skillopt/engine/*"],
    max_file_size=102400,
)
```

## Filtering Cheatsheet
| Flag | Short | Purpose |
|------|-------|---------|
| `--include-pattern` | `-i` | Include matching files (glob) |
| `--exclude-pattern` | `-e` | Exclude matching files (glob) |
| `--max-size` | `-s` | Max file size in bytes |
| `--branch` | `-b` | Specific branch |
| `--token` | `-t` | GitHub PAT for private repos |
| `--output` | `-o` | Output file (`-` = stdout) |

## Common Exclusion Patterns
```bash
-e "node_modules/*" -e "dist/*" -e "build/*" \
-e "*.lock" -e "*.log" -e "*.min.js" \
-e "tests/*" -e "test/*" -e "__pycache__/*" \
-e ".git/*" -e "ckpt/*" -e ".venv/*"
```

## When to Use Which
| Scenario | Command |
|----------|---------|
| First look at any repo | Shallow pass (README + tree) |
| Understand architecture | Shallow + `skillopt/engine/*`, `skillopt/config.py` |
| Debug specific component | Targeted subdir (e.g., `skillopt/optimizer/*`) |
| Review benchmark setup | `skillopt/envs/<name>/*` |
| Check pre-trained skills | `ckpt/<benchmark>/*` |
| Full code review (rare) | `-i "*.py" -i "*.md" -e "tests/*" -e "ckpt/*" -s 200000` |

## Anti-Patterns to Avoid
- ❌ `gitingest repo -o -` (no filters = full dump, 400k+ tokens)
- ❌ Running deep-dive before shallow pass
- ❌ Including `tests/`, `ckpt/`, `docs/`, `.git/` in deep-dives unless explicitly needed

## Token Budget Guide
| Pass Type | Typical Tokens | Use When |
|-----------|----------------|----------|
| Shallow (README + tree) | 2k–10k | Always first |
| Targeted subdir | 10k–50k | Need implementation details |
| Multi-subdir focused | 50k–150k | Cross-component analysis |
| Full filtered codebase | 150k–400k | Rare, comprehensive review |