---
name: gitingest-usage
description: Best practices for using GitIngest (CLI & Python) to extract repository content for LLM consumption
category: software-development
tags: [github, llm-context, code-analysis, automation]
version: 1.0.0
---

# GitIngest Usage Skill

## When to Use GitIngest

Use **GitIngest** (not `web_extract`) for any GitHub/GitLab/Bitbucket repository URL. It clones the repo and returns structured plain-text optimized for LLM context windows.

**Prefer GitIngest over web_extract when:**
- Source is a git repository (GitHub, GitLab, Bitbucket)
- You need full repo structure + file contents
- You want token-efficient, structured output for LLM consumption
- You need filtering (include/exclude patterns, size limits)

---

## CLI Quick Reference

```bash
# Basic - stream to stdout (pipe to LLM)
gitingest https://github.com/owner/repo -o -

# Shallow first: README + structure only (fast, low tokens)
gitingest https://github.com/owner/repo -i "README*" -i "*.md" -s 10240 -o -

# Focus on code files
gitingest https://github.com/owner/repo -i "*.py" -i "*.js" -i "*.ts" -s 51200 -o -

# Exclude noise
gitingest https://github.com/owner/repo -e "node_modules/*" -e "*.lock" -e "dist/*" -e "build/*" -o -

# Specific branch
gitingest https://github.com/owner/repo -b develop -o -

# Private repo (set GITHUB_TOKEN env var first)
gitingest https://github.com/owner/private-repo -t $GITHUB_TOKEN -o -

# Subdirectory only (use tree URL)
gitingest https://github.com/owner/repo/tree/main/subdir -o -

# Save to file
gitingest https://github.com/owner/repo -o analysis.txt
```

### Key Flags

| Short | Long | Purpose |
|-------|------|---------|
| `-o` | `--output` | `-` = stdout, else file path (default: `digest.txt`) |
| `-i` | `--include-pattern` | Unix glob, repeatable (e.g., `*.py`, `README*`) |
| `-e` | `--exclude-pattern` | Unix glob, repeatable (e.g., `node_modules/*`, `*.log`) |
| `-s` | `--max-size` | Max file size in bytes (default: 10MB) |
| `-b` | `--branch` | Branch/tag/commit (default: repo default) |
| `-t` | `--token` | GitHub PAT for private repos |

---

## Python Package Usage

```python
from gitingest import ingest, ingest_async

# Sync (simple scripts)
summary, tree, content = ingest("https://github.com/owner/repo")

# Async (batch processing, AI services)
results = await asyncio.gather(*[ingest_async(url) for url in urls])

# With filtering
summary, tree, content = ingest(
    "https://github.com/owner/repo",
    include_patterns=["*.py", "*.md"],
    exclude_patterns=["tests/*", "*.lock"],
    max_file_size=51200,  # 50KB per file
)
```

### Output Structure (always 3 parts)

```python
# summary: "Repository: owner/repo\nFiles analyzed: 42\nEstimated tokens: 15.2k"
# tree:    "Directory structure:\n└── repo/\n    ├── src/\n    │   └── main.py\n    └── README.md"
# content: "================================================\nFILE: src/main.py\n================================================\ndef main():\n    ...\n\n================================================\nFILE: README.md\n================================================\n# Project\n..."
```

---

## Recommended Workflow: Shallow → Deep

**Don't dump the whole repo at once.** Start small, then dive deeper.

### Phase 1: Orientation (README + structure)
```bash
gitingest https://github.com/owner/repo -i "README*" -i "*.md" -s 10240 -o -
```
→ Gets you: repo purpose, architecture overview, key docs. ~1-5k tokens.

### Phase 2: Targeted code areas
```bash
# Based on Phase 1, pick relevant directories
gitingest https://github.com/owner/repo -i "src/**/*.py" -i "lib/**/*.ts" -s 102400 -o -
```

### Phase 3: Full dump (only if needed)
```bash
gitingest https://github.com/owner/repo -e "node_modules/*" -e "*.lock" -e "dist/*" -o -
```

---

## Subdirectory Support

GitIngest natively supports GitHub tree URLs:
```bash
# Subdirectory only (sparse clone)
gitingest https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf -o -
```

This clones only `/okf` subtree — faster, fewer tokens.

---

## Token Estimation

The `summary` section includes `Estimated tokens:`. Use this to plan context budget.

| Repo size | Typical tokens | Strategy |
|-----------|---------------|----------|
| Small (<50 files) | <50k | Full dump OK |
| Medium (50-500) | 50k-500k | Filter by pattern |
| Large (>500) | 500k+ | Shallow → targeted |

---

## Common Patterns for AI Agents

### Code Review Bot
```bash
gitingest https://github.com/owner/repo -i "*.py" -i "*.js" -i "*.md" -s 102400 -o - | llm-review
```

### Documentation Generator
```bash
gitingest https://github.com/owner/repo -i "*.py" -i "*.md" -e "tests/*" -o - | llm-gen-docs
```

### Vulnerability Scanner
```bash
gitingest https://github.com/owner/repo -i "*.py" -i "*.js" -i "*.go" -s 204800 -o - | llm-scan
```

### Dependency Analysis
```bash
gitingest https://github.com/owner/repo -e "node_modules/*" -e "*.lock" -e "vendor/*" -o - | llm-deps
```

---

## Pitfalls & Fixes

| Problem | Fix |
|---------|-----|
| Output too large | Add `-s 51200` (50KB/file), use `-i`/`-e` filters |
| Private repo fails | Export `GITHUB_TOKEN=ghp_xxx` or pass `-t $GITHUB_TOKEN` |
| Wrong branch | Add `-b branch-name` |
| Subdirectory needed | Use `tree/branch/path` URL format |
| Binary files included | They're skipped automatically; increase `-s` if text files truncated |
| Slow on huge repos | Use shallow sparse clone via tree URL + filters |

---

## Integration with Hermes

In Hermes, prefer `terminal()` for CLI or `execute_code()` for Python:

```python
# execute_code example
from hermes_tools import terminal
result = terminal("gitingest https://github.com/owner/repo -i '*.py' -o -")
```

---

## Verification Checklist

After running gitingest, verify:
- [ ] `Files analyzed:` count matches expectation
- [ ] `Estimated tokens:` fits your context window
- [ ] Key files present in `Directory structure:`
- [ ] No `ERROR` in output (warnings OK for skipped files)

---

*Skill created from real usage on microsoft/SkillOpt (258 files, 462k tokens) and GoogleCloudPlatform/knowledge-catalog/okf (126 files, 130k tokens).*