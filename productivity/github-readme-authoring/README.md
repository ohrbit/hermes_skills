# github-readme-authoring

[![Skill](https://img.shields.io/badge/Hermes_Skill-github--readme--authoring-8dbb3c)](https://github.com/nousresearch/hermes-agent)
[![Category](https://img.shields.io/badge/Category-productivity-blue)](https://github.com/nousresearch/hermes-agent/tree/main/skills/productivity)
[![License](https://img.shields.io/github/license/nousresearch/hermes-agent)]()

> **Production-grade GitHub README.md generator** — opinionated template, required sections, badge-driven, contributor-ready.

## Why github-readme-authoring?

**Problem:** READMEs are inconsistent — missing badges, no quick-start, unclear purpose, no installation, no contribution path. Maintainers waste cycles reinventing structure.

**Solution:** Opinionated template with **12 required sections**, badge-driven metadata, and a validation checklist. One command → production README.

## Features

- ✅ **12 required sections** — Purpose, Features, Quick Start, Usage, Configuration, Output, Pitfalls, Related, Contributing, License
- ✅ **Badge-first metadata** — skill badge, category, license, build status
- ✅ **Token-efficient** — structured for LLM parsing (scannable tables, code blocks)
- ✅ **Self-applied** — this README generated using the skill
- ✅ **Validation checklist** — `validate_readme()` function for CI gates

## Quick Start

### As a Skill (Hermes Agent)

```bash
# Load skill
skill_view(name='github-readme-authoring')

# Generate README for target skill
# (prompts for skill name, category, purpose, features)
```

### As a Template (Manual)

Copy `templates/README_TEMPLATE.md`, fill placeholders, run validation:

```bash
python scripts/validate_readme.py path/to/README.md
```

## Usage Patterns

### Generate New Skill README

```python
# Via skill mechanism (preferred)
from skills.productivity.github_readme_authoring import generate_readme

generate_readme(
    skill_name="my-new-skill",
    category="software-development",
    purpose="One-line elevator pitch",
    features=["Feature 1", "Feature 2"],
    install_cmd="pip install my-skill",
    usage_examples=["example1", "example2"],
)
```

### Validate Existing README

```bash
# Returns exit code 0 if all 12 sections present
python scripts/validate_readme.py ./README.md
```

### CI Gate

```yaml
# .github/workflows/readme-lint.yml
- name: Validate README
  run: python .hermes/skills/productivity/github-readme-authoring/scripts/validate_readme.py README.md
```

## Configuration Reference

| Section | Required | Purpose |
|---------|----------|---------|
| Badge header | ✅ | Skill identity, category, license |
| Purpose (elevator pitch) | ✅ | One-paragraph "why" |
| Features | ✅ | Bullet list with checkmarks |
| Quick Start | ✅ | Installation + 30-sec demo |
| Usage Patterns | ✅ | Real-world code examples |
| Configuration | ✅ | Table of flags/options |
| Output Structure | ✅ | Example output format |
| Common Pitfalls | ✅ | Table: Problem → Fix |
| Related Skills | ✅ | Cross-references |
| Contributing | ✅ | How to improve |
| License | ✅ | Legal |

## Output Structure

```markdown
# skill-name

[![Skill](...)][skill-url]
[![Category](...)][category-url]
[![License](...)][license-url]

> **One-line purpose** — tagline.

## Why skill-name?

**Problem:** ...
**Solution:** ...

## Features

- ✅ Feature 1
- ✅ Feature 2

## Quick Start

### Installation
```bash
pip install skill
```

### 30-Second Demo
```bash
skill-command --demo
```

## Usage Patterns
...

## Configuration Reference
| Flag | Purpose | Default |
|------|---------|---------|

## Output Structure
```
text example
```

## Common Pitfalls
| Problem | Fix |

## Related Skills
- [skill-a](../category/skill-a)
- [skill-b](../category/skill-b)

## Contributing
...

## License
MIT — Part of Hermes Agent skills collection.
```

## Common Pitfalls

| Problem | Fix |
|---------|-----|
| Missing badge header | Run generator, don't hand-write |
| Generic "Features" list | Use specific, verifiable capabilities |
| No 30-second demo | Add minimal working example |
| No Configuration table | Document every user-facing flag |
| No Pitfalls section | Add from real user friction |
| Broken cross-references | Use relative paths `../category/skill` |

## Related Skills

- [gitingest-usage](../software-development/gitingest-usage) — Shallow-first GitHub ingestion
- [codebase-inspection](../software-development/codebase-inspection) — LOC, language ratios

## Contributing

1. Improve template in `templates/README_TEMPLATE.md`
2. Add validation rules in `scripts/validate_readme.py`
3. Submit PR to Hermes Agent skills registry

## License

MIT — Part of [Hermes Agent](https://github.com/nousresearch/hermes-agent) skills collection.