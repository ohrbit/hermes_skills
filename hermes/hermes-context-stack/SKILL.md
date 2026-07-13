---
name: hermes-context-stack
description: Verify and manage Hermes context-stack files (SOUL.md, user.md, .hermes.md, AGENTS.md) across the default profile and per-profile directories. Use when a user asks whether their SOUL/user/.hermes files are customized or present, suspects customizations are "missing", or when installing/repairing a persona.
---

# Hermes Context Stack — Verify & Manage

## When to use
- User asks whether SOUL.md / user.md / .hermes.md is customized, present, or correct.
- User references "the real SOUL.md" or suspects their customizations are gone.
- You are about to rely on context-stack files for alignment / user profile / project context.
- Setting up or repairing a user's context stack.

## Key facts
- **Default profile** = what runs when `HERMES_PROFILE` env var is unset. Its SOUL.md is `~/.hermes/SOUL.md`.
- **Per-profile SOUL.md** live at `~/.hermes/profiles/<name>/SOUL.md` (e.g. `sirvir`, `calypso`). Each profile is a separate persona and does NOT inherit the default file.
- A profile can be heavily customized while the *default* remains stock — and vice versa. Never infer "not customized" from the default file alone.
- `user.md` and `.hermes.md` follow the same global-vs-per-profile pattern. On this host the user profile was found at `~/.hermes/memories/USER.md`.
- Context load order (Hermes SOUL convention): SOUL.md → MEMORY.md → USER.md → AGENTS.md → .cursorrules.

## Workflow: VERIFY before reporting (critical)
**PITFALL (learned from a user correction):** When asked "did you customize SOUL.md?" do NOT check only `~/.hermes/SOUL.md`. The user's real customizations may live in a profile directory you didn't look at. Checking only the default and reporting "it's stock / not customized" is WRONG and wastes a turn.

1. Enumerate every candidate before concluding:
   `find /root/.hermes -iname "SOUL.md" -o -iname "user.md" -o -iname ".hermes.md" -o -iname "AGENTS.md"`
2. Report each location with size + mtime:
   `find /root/.hermes -iname "SOUL.md" -printf "%T+ %6s  %p\n" | sort`
3. Identify the active profile: `echo "HERMES_PROFILE=${HERMES_PROFILE:-<unset>}"` (unset ⇒ default).
4. Only then state whether the *relevant* file is customized.

## Workflow: INSTALL / REPLACE a context file
**PITFALL:** Long SOUL.md content is often a single very long line (no newlines). Re-typing it or reading a truncated display loses data. Copy byte-for-byte instead.
- If the file is already on disk (e.g. a user-uploaded doc cached at `~/.hermes/cache/documents/doc_*.md`):
  `python3 -c "import shutil; shutil.copyfile(SRC, DST)"` — byte-perfect, no truncation.
- Verify: `wc -c DST` and compare head/tail with the source.
- If writing from pasted text, use the `write_file` tool (overwrites cleanly, runs syntax checks); never hand-type a 4KB single-line file.

## Editing a profile's SOUL without clobbering
- Default: `~/.hermes/SOUL.md`
- Profile: `~/.hermes/profiles/<name>/SOUL.md`
- Keep stock profiles (e.g. `calypso`) separate unless the user asks to propagate a persona.

## References
- `references/verify-and-edit.md` — exact commands + the Proteus/OMNICOMP lineage note.
