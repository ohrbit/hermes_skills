# gitingest-usage

[![Skill](https://img.shields.io/badge/Hermes_Skill-gitingest--usage-8dbb3c)](https://github.com/nousresearch/hermes-agent)
[![Category](https://img.shields.io/badge/Category-software--development-blue)](https://github.com/nousresearch/hermes-agent/tree/main/skills/software-development)
[![License](https://img.shields.io/github/license/nousresearch/hermes-agent)]()

> **Shallow-first GitHub repository ingestion for LLM context windows** — progressive deepening, token-budgeted, pipeline-ready.

## Why gitingest-usage?

**Problem:** `web_extract` on GitHub URLs is slow, expensive, and returns HTML-soup. Full repo dumps explode token budgets. You need *structured, filtered, incremental* codebase ingestion.

**Solution:** This skill codifies the **shallow → deep** workflow using [GitIngest CLI](https://github.com/coderamp-labs/gitingest) — purpose-built for AI agents to consume entire repositories programmatically.

## Features

- ✅ **Progressive deepening** — README → docs → code → targeted modules
- ✅ **Token budgeting** — size limits, include/exclude patterns, subdirectory sparse clones
- ✅ **Pipeline ready** — stdout streaming (`-o -`), async Python API, batch processing
- ✅ **Private repo support** — GitHub PAT via env or flag
- ✅ **Real-world tested** — microsoft/SkillOpt (258 files, 462k tokens), GoogleCloudPlatform/knowledge-catalog/okf (86 files, 53k tokens)

## Quick Start

### Installation

```bash
# CLI (recommended for scripts/automation)
pipx install gitingest

# Python package (for code integration)
pip install gitingest

# Verify
gitingest --version
```

### Orientation (30 seconds, ~2k tokens)

```bash
gitingest https://github.com/owner/repo -i "README*" -i "*.md" -s 10240 -o -
```

### Targeted Code Review (~50k tokens)

```bash
gitingest https://github.com/owner/repo -i "*.py" -i "*.js" -i "*.ts" -s 102400 -o -
```

### Full Context (with noise excluded)

```bash
gitingest https://github.com/owner/repo \
  -e "node_modules/*" -e "*.lock" -e "dist/*" -e "build/*" -e "*.min.js" \
  -o -
```

## Usage Patterns

### CLI → LLM Pipeline

```bash
# Code review bot
gitingest https://github.com/owner/repo -i "*.py" -i "*.js" -s 102400 -o - | llm-review

# Documentation generator
gitingest https://github.com/owner/repo -i "*.py" -i "*.md" -e "tests/*" -o - | llm-gen-docs

# Vulnerability scanner
gitingest https://github.com/owner/repo -i "*.py" -i "*.js" -i "*.go" -s 204800 -o - | llm-scan
```

### Python Integration

```python
from gitingest import ingest, ingest_async
import asyncio

# Sync - simple scripts
summary, tree, content = ingest(
    "https://github.com/owner/repo",
    include_patterns=["*.md", "*.py"],
    max_file_size=102400,
)

# Async - batch processing
async def batch_ingest(urls):
    tasks = [ingest_async(u, include_patterns=["*.md"], max_file_size=51200) for u in urls]
    return await asyncio.gather(*tasks)

# Stream large repos by language
def stream_repo(url):
    _, tree, _ = ingest(url, include_patterns=["*.md"], max_file_size=10240)
    for pattern in ["*.py", "*.js", "*.go"]:
        _, _, content = ingest(url, include_patterns=[pattern], max_file_size=51200)
        yield content
```

### Subdirectory Only (Sparse Clone)

```bash
# Clone only /okf subtree from monorepo
gitingest https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf -o -
```

## Configuration Reference

| Flag | Long | Purpose | Default |
|------|------|---------|---------|
| `-o` | `--output` | `-` = stdout, else file path | `digest.txt` |
| `-i` | `--include-pattern` | Unix glob, repeatable | all files |
| `-e` | `--exclude-pattern` | Unix glob, repeatable | none |
| `-s` | `--max-size` | Max file size in bytes | 10MB |
| `-b` | `--branch` | Branch/tag/commit | repo default |
| `-t` | `--token` | GitHub PAT for private repos | `$GITHUB_TOKEN` |

## Token Budget Guidelines

| Task | Budget | Patterns |
|------|--------|----------|
| Quick triage | 2k | `README*.md` |
| Architecture review | 10k | `*.md`, `*.yaml`, `docs/**` |
| Code audit | 50k | `*.py`, `*.js`, `src/**` |
| Full context | 200k+ | all code, exclude noise |

## Output Structure

```text
Repository: owner/repo
Commit: abc123...
Files analyzed: 42
Estimated tokens: 15.2k

Directory structure:
└── repo/
    ├── src/
    │   └── main.py
    └── README.md

================================================
FILE: src/main.py
================================================
def main():
    print("Hello")

================================================
FILE: README.md
================================================
# Project
...
```

## Common Pitfalls

| Problem | Fix |
|---------|-----|
| Output too large | Add `-s 51200`, use `-i`/`-e` filters |
| Private repo fails | Export `GITHUB_TOKEN=ghp_xxx` or pass `-t $GITHUB_TOKEN` |
| Wrong branch | Add `-b branch-name` |
| Subdirectory needed | Use `tree/branch/path` URL format |
| Slow on huge repos | Use sparse clone via tree URL + filters |

## Related Skills

- [github-readme-authoring](../productivity/github-readme-authoring) — Create production-grade READMEs
- [codebase-inspection](../software-development/codebase-inspection) — LOC, language ratios via pygount

## Contributing

This skill lives in the Hermes Agent skills registry. Improvements welcome via PR to the Hermes repo.

## License

MIT — Part of [Hermes Agent](https://github.com/nousresearch/hermes-agent) skills collection.