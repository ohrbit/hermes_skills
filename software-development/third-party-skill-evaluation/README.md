# Third-Party Skill Evaluation

> **Decide whether an external agent-skill repo is worth importing into Hermes** — discovery, relevance scoring, adaptation feasibility, and a clear import/adapt/skip verdict.

## Why this skill?

When someone drops a GitHub skills repo ("is this useful for Hermes?"), the trap is importing app-coupled or mobile-only skills that can't run on your stack, or ingesting the whole repo and drowning in tokens. This skill is the disciplined path from *"cool repo"* to *"imported and working"* — or a clean "skip" with a one-line reason.

## What it does

- ✅ Shallow-first discovery (README + tree, never the full repo)
- ✅ Bucket classification: prompt-only / framework-specific / app-coupled
- ✅ Relevance scoring against the user's *actual* stack
- ✅ Adaptation-feasibility table (import effort, maintenance, testability)
- ✅ Decision output: import now / adapt later / skip
- ✅ Pitfalls + verification checklist (incl. frontmatter trigger adaptation)

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install third-party-skill-evaluation
```

## Quick Start

```text
In chat: "is this skill repo useful for Hermes? <github url>"
```

## How it works

```
1. SHALLOW  gitingest <repo> -i "README*" -i "*.md" -s 51200   (goal: scope in 5 min)
2. SCORE    against the user's stack (platform, providers, venv, deploy)
3. FEASIBLE prompt-only (low effort) vs app-coupled (high effort)?
4. DECIDE   import now / adapt later / skip  →  concise triage
```

A skill is **high-value** if it solves a recurring problem in your stack, is model-agnostic, drops into the venv without new system deps, and has a testable interface. **Low-value** if it needs mobile/macOS runtime, vendor-only hardware, or would need >60% rewrite.

## Usage / Examples

### Basic
> "Evaluate github.com/owner/skills-repo."

Shallow ingest → classify bucket → score relevance → output: *Import now* (copy SKILL.md, adapt triggers) / *Adapt later* / *Skip* with reason.

### Advanced
Importing? Rewrite the `description` frontmatter to match Hermes trigger vocabulary so it loads when relevant — external triggers are usually generic.

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Workflow, scoring, pitfalls, checklist |
| `references/evaluated-repos-<date>.md` | Session-specific notes on repos assessed |

## Related skills

- `github-repo-ingest` — the shallow-first ingestion protocol it builds on
- `hermes-agent-skill-authoring` — for writing/adapting SKILL.md frontmatter

## Notes / caveats

- **Never ingest the full repo** — shallow-first or you burn tokens and add noise.
- **Don't invent facts** about a repo — if a SKILL.md references `agentskills.io` and you haven't loaded it, say so.
- **App-coupled skills:** extract the module and rewrite runtime calls, or skip — host-app changes will break it.
- **German is fine for summaries**; match the user's language for analysis, English for public posts.

## License

MIT — © 2024 Hermes Agent
