# GitIngest Usage

> **Extract repository content for LLM consumption** — the CLI & Python reference for GitIngest (clone → structured plain-text, token-efficient).

## Why this skill?

When the source is a git repo, `web_extract` is the wrong tool — it misses structure and wastes tokens. GitIngest clones the repo and returns filtered, LLM-optimized plain text. This skill is the full flag reference + Python API so you filter by pattern, size, and branch instead of pulling everything.

## What it does

- ✅ CLI quick reference (all major flags)
- ✅ Include/exclude glob patterns (repeatable)
- ✅ Size limits, branch selection, private-repo tokens
- ✅ Subdirectory-only ingestion (tree URL)
- ✅ Python `ingest` / `ingest_async` API
- ✅ Prefer-GitIngest-over-web_extract decision rule

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install gitingest-usage
pipx install gitingest    # or: pip install gitingest
```

## Quick Start

```bash
# shallow first: README + structure only
gitingest https://github.com/owner/repo -i "README*" -i "*.md" -s 10240 -o -
```

## How it works

```
repo URL → clone → filter (include/exclude/size/branch) → structured text → stdout/file
```

Key flags: `-o` output (`-` = stdout), `-i` include, `-e` exclude, `-s` max-size, `-b` branch, `-t` token (private).

## Usage / Examples

### Basic
> "Pull just the Python + YAML, skip node_modules."

```bash
gitingest <repo> -i "*.py" -i "*.yaml" -e "node_modules/*" -e "dist/*" -o -
```

### Advanced
> "Ingest a subdir as part of a script."

```python
from gitingest import ingest
summary, tree, content = ingest("<repo>", include_patterns=["src/*"], max_file_size=102400)
```

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | CLI reference, Python API, decision rule |

## Related skills

- `github-repo-ingest` — the shallow-first ingestion protocol built on this
- `third-party-skill-evaluation` — evaluate repos you ingest

## Notes / caveats

- Private repos: set `GITHUB_TOKEN` (or `-t`) first.
- Raw curl on GitHub API won't give you structured text — use GitIngest.

## License

MIT — © 2024 ohrbit
