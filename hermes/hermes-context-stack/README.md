# Hermes Context Stack — Verify & Manage

> **Check and repair your alignment files (SOUL.md / user.md / .hermes.md)** across the default and per-profile directories — without falsely reporting "it's stock."

## Why this skill?

A classic failure: asked "did you customize SOUL.md?", the agent checks only `~/.hermes/SOUL.md`, finds it stock, and reports "not customized" — while the user's real persona sits in `profiles/sirvir/SOUL.md` and isn't loaded. This skill forces a full enumeration of every candidate file *before* any conclusion, and distinguishes three states: customized-in-active-profile, customized-in-non-active-only, or not-customized-anywhere.

## What it does

- ✅ Enumerates SOUL.md / user.md / .hermes.md / AGENTS.md across ALL profile dirs
- ✅ Identifies the *active* profile and what the running agent actually loads
- ✅ Reports three distinct states (never collapses them)
- ✅ Byte-perfect install/replace (long SOULs are often one line — copy, don't retype)
- ✅ Documents the Proteus / OMNICOMP lineage of the SOUL convention

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install hermes-context-stack
```

## Quick Start

```bash
# verify before claiming anything
find /root/.hermes -iname "SOUL.md" -printf "%T+ %6s  %p\n" | sort
echo "HERMES_PROFILE=${HERMES_PROFILE:-<unset>}"
```

## How it works

```
enumerate every candidate file (default + profiles)
   │
identify active profile (HERMES_PROFILE unset ⇒ default)
   │
determine which file the RUNNING agent loads
   │
report 3 states: active-customized / non-active-only / stock
```

Context load order: `SOUL.md → MEMORY.md → USER.md → AGENTS.md → .cursorrules`.

## Usage / Examples

### Basic
> "Is my SOUL.md customized?"

Runs the full enumeration, reports size + mtime per location, and tells you whether the customization applies to the current session or sits in a dormant profile.

### Advanced
Installing a pasted SOUL: it's often a single 4KB line. Use `shutil.copyfile(SRC, DST)` — byte-perfect, no truncation. Verify with `wc -c`.

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Verify + install workflows, pitfalls |
| `references/verify-and-edit.md` | Exact commands + lineage note |

## Related skills

- Your `SOUL.md` / `USER.md` / `.hermes.md` — the files this skill manages
- `hermes-config` — for safe `config.yaml` edits

## Notes / caveats

- A profile can be heavily customized while the *default* stays stock — never infer from the default alone.
- A customization in a non-active profile does NOT apply to the current session; offer to copy it in.
- Long SOUL content is frequently one very long line — copy, never hand-type.

## License

MIT — © 2024 ohrbit
