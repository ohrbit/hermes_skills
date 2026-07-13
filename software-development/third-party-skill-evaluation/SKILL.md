---
name: third-party-skill-evaluation
description: Evaluate external agent-skill repositories for potential import into Hermes. Covers discovery, shallow assessment, relevance scoring, adaptation feasibility, and integration decision. Use when the user shares a GitHub repo of skills, asks "is this useful for Hermes," or wants to import external agent workflows into their stack.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, evaluation, import, github, hermess, external-repos]
    related_skills: [github-repo-ingest, hermes-agent-skill-authoring]
---

# Third-Party Skill Evaluation

## Overview

External agent-skill repositories fall into three buckets:
1. **Prompt-only collections** — Markdown files with instructions, no executable code. Easy to import, low maintenance burden.
2. **Framework-specific skills** — Skills tied to a specific agent runtime (e.g., `agentskills.io` format, OpenAI function schemas). Medium adaptation effort.
3. **App/platform repos with skill modules** — Full applications that happen to contain skills (e.g., Google AI Edge Gallery). Skills are coupled to the host app's runtime.

This skill governs the workflow from discovery to decision.

## Evaluation Workflow

### 1. Shallow-first discovery

Never ingest the full repo. Start with README + directory tree:

```bash
gitingest https://github.com/owner/repo \
  --include-pattern "README*" \
  --include-pattern "*.md" \
  --max-size 51200 \
  -o -
```

Or use `web_extract` against the repo root for a quick 10-15k char read.

**Goal within 5 minutes:** know the repo's scope, categories, and whether it's prompt-only or app-coupled.

### 2. Relevance scoring

Score the repo against the user's actual stack. For this user, the stack is:
- Hermes Agent on Debian 13
- `/opt/calypso` venv-based Python backend
- Hetzner deploy pipeline
- Telegram/Discord messaging
- Docker Compose on Hetzner

A skill is **high-value** if it:
- Solves a recurring problem in this stack (deploy verification, webhook handling, Stripe integration)
- Is model-agnostic or explicitly supports the user's providers
- Can drop into the existing venv without new system dependencies
- Has a clear, testable interface

A skill is **low-value** if it:
- Requires Android/iOS/macOS runtime (mobile edge)
- Depends on vendor-specific hardware/APIs the user doesn't have
- Is purely conceptual with no reproducible workflow
- Would require rewriting >60% of its logic to fit the stack

### 3. Adaptation feasibility

Before importing, check:

| Factor | Prompt-only skills | App-coupled skills |
|--------|-------------------|-------------------|
| Import effort | Low — copy SKILL.md, adapt triggers | High — extract skill, rewrite runtime calls |
| Maintenance | Low — instructions don't break | Medium-High — host app changes break the skill |
| Testability | High — run the prompt against any LLM | Low — needs the host app's runtime |
| Recommended? | Yes, if relevant | Only if the skill module is self-contained |

### 4. Decision output

Always produce a concise triage:
- **Import now** — copy SKILL.md, adapt frontmatter/triggers, add to `~/.hermes/skills/`
- **Adapt later** — good idea, but needs wrapper code or dependency work first
- **Skip** — wrong platform, too vague, maintenance burden > value

## User Preferences from Session Evidence

- **German is acceptable** for evaluation summaries; match the user's language for analysis, English for posting/public content.
- **Be concise and action-oriented** during evaluation. State the verdict, the evidence, and one next step. Do not narrate successful happy-path reads.
- **Do not invent facts** about repos. If a SKILL.md references `agentskills.io` but you haven't loaded it, say so explicitly.
- **Twitter/X posts about evaluations** should be short hooks, not detailed technical breakdowns. Save deep analysis for the conversation; posts are signals, not documentation.

## Common Pitfalls

1. **Ingesting full repos** — burns tokens, adds noise. Always shallow-first.
2. **Importing app-coupled skills without unwinding them** — if the skill calls `local_sd` or mobile-only APIs, it won't run on the user's Hetzner stack.
3. **Confusing "cool idea" with "importable skill"** — RIFTAGENT has a strong hook but is a prompt-orchestration demo, not a tested workflow. Import only if the user wants the pattern, not just the aesthetics.
4. **Skipping trigger adaptation** — external SKILL.md files use generic triggers. When importing, rewrite the `description` frontmatter to match Hermes's trigger vocabulary so the skill loads when relevant.
5. **Forgetting venv/dependency isolation** — even Markdown-only skills may call Python APIs in their examples. Validate imports before claiming a skill works.

## Verification Checklist

- [ ] README + tree read, full repo not ingested
- [ ] Skill classified as prompt-only / framework-specific / app-coupled
- [ ] Relevance scored against user's actual stack
- [ ] Adaptation feasibility checked
- [ ] Decision is one of: import / adapt later / skip
- [ ] If importing: SKILL.md frontmatter adapted for Hermes triggers
- [ ] If skipping: one-sentence reason given, no files modified

## References

- `references/evaluated-repos-2026-07-10.md` — session-specific notes on davidondrej/skills, ohrbit/riftagent, google-ai-edge/gallery