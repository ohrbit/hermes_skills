---
name: github-readme-authoring
description: Create production-grade GitHub README.md files — structure, badges, installation, usage, API, contributing, license, and maintenance sections with real examples
category: productivity
tags: [github, readme, documentation, markdown, open-source]
---

# GitHub README Authoring Skill

## Purpose

Create README.md files that convert visitors into users/contributors. Every section serves a decision: **install → try → understand → trust → contribute**.

## Required Sections (in order)

```markdown
# Project Title

[Badges row: CI, version, license, downloads, chat]

> One-sentence tagline. What problem does this solve for *me*?

## Why [Project]? / Problem Statement

2-3 paragraphs. Frame the pain point, show the gap, position your solution.

## Features

- ✅ Feature 1 (with emoji checkmarks)
- ✅ Feature 2
- 🔄 Feature 3 (planned)

## Quick Start / Installation

```bash
# One-liner install
pip install your-package
# or
npm install your-package
# or
curl -sSL https://install.yourproject.sh | bash
```

## Minimal Working Example

```python
# 5-10 lines that produce visible output
from your_package import main
result = main.do_thing("input")
print(result)  # → shows actual output
```

## Usage / CLI / API Reference

### CLI
```bash
your-cli --help
your-cli command --flag value
```

### Python API
```python
from your_package import Client
client = Client(api_key="...")
result = client.method(param="value")
```

### Configuration
```yaml
# config.yaml
setting: value
nested:
  option: true
```

## Architecture / How It Works

```mermaid
graph LR
    A[Input] --> B[Processor]
    B --> C[Output]
```

Or ASCII:
```
┌─────────┐    ┌──────────┐    ┌────────┐
│ Source  │───▶│ Processor│───▶│ Sink   │
└─────────┘    └──────────┘    └────────┘
```

## Configuration Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` | Yes | — | Your API key |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARN`, `ERROR` |

## Examples / Recipes

### Use Case 1: Basic
```python
# code
```

### Use Case 2: Advanced
```python
# code
```

## Contributing

```bash
git clone https://github.com/owner/repo
cd repo
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE) / [Apache-2.0](LICENSE) — © 2024 Author

## Support / Community

- 💬 [Discord](https://discord.gg/...)
- 🐛 [Issues](https://github.com/owner/repo/issues)
- 📖 [Docs](https://docs.yourproject.com)
- 🐦 [Twitter/X](https://x.com/...)

---

## Badge Templates

```markdown
![CI](https://github.com/owner/repo/workflows/CI/badge.svg)
![PyPI](https://img.shields.io/pypi/v/package-name)
![License](https://img.shields.io/github/license/owner/repo)
![Python](https://img.shields.io/pypi/pyversions/package-name)
![Downloads](https://img.shields.io/pypi/dm/package-name)
![Discord](https://img.shields.io/discord/123456789?label=Discord)
![Codecov](https://codecov.io/gh/owner/repo/branch/main/graph/badge.svg)
```

## Anti-Patterns to Avoid

| ❌ Don't | ✅ Do |
|----------|-------|
| Wall of text before install | Install command in first 10 lines |
| No working example | Runnable snippet with expected output |
| Only CLI, no API (or vice versa) | Both, clearly separated |
| "See docs for config" | Inline table with all options |
| Vague "contributions welcome" | Link to CONTRIBUTING.md + good first issues |
| No license | SPDX identifier + LICENSE file |

## Real-World Reference READMEs

| Project | Strength |
|---------|----------|
| [httpx](https://github.com/encode/httpx) | Clean API docs, async/sync examples |
| [rich](https://github.com/Textualize/rich) | Visual demos, feature grid |
| [fastapi](https://github.com/tiangolo/fastapi) | Minimal example, auto-generated API ref |
| [pydantic](https://github.com/pydantic/pydantic) | Migration guide, benchmarks |
| [ruff](https://github.com/astral-sh/ruff) | Speed comparison table, config reference |

## Checklist Before Publishing

- [ ] Title + tagline visible without scrolling
- [ ] Install command copy-pasteable
- [ ] Working example runs in <30 seconds
- [ ] All config options documented
- [ ] Badges render (click to verify)
- [ ] Links work (no 404s)
- [ ] License file exists and matches badge
- [ ] CONTRIBUTING.md linked
- [ ] Issue templates exist
- [ ] Changelog / releases linked

---

## Usage in Hermes

```python
# Use this skill as a template when authoring READMEs
# Combine with gitingest-usage to research existing READMEs first:
# gitingest https://github.com/owner/repo -i "README*" -o -
```