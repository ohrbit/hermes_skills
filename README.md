# hermes_skills

A curated collection of [Hermes Agent](https://hermes-agent.nousresearch.com) skills published by **ohrbit**.
Each skill lives in `category/skill-name/` with a `SKILL.md` (the definition) and a human-readable `README.md`.

## Install
```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install <skill-name>
```

## Skills (13)

### creative

| Skill | Description |
|---|---|
| **nano-banana-prompting** | "Prompting frameworks and patterns for Google Nano Banana (Gemini 3.1 Flash/Pro Image) models. Covers 5 core frameworks from Google's official guide." |

### devops

| Skill | Description |
|---|---|
| **agent-swarm-loop** | >- |
| **hermes-serverless-backend** | Wire Modal (or Daytona) as the serverless `terminal.backend` for Hermes so agent + subagent shell/execute_code run in ephemeral cloud sandboxes (idle = $0). ... |
| **jit-agent-teams** | >- |
| **kanban-orchestrator** | Decomposition playbook + anti-temptation rules for an orchestrator profile routing work through Kanban. The "don't do the work yourself" rule and the basic l... |
| **model-selection-and-jit-routing** | "Pick the right available model per task (chat/coding/reasoning/vision/long-context) and route JIT agent-team profiles to the best-fit provider, using live p... |

### hermes

| Skill | Description |
|---|---|
| **hermes-context-stack** | Verify and manage Hermes context-stack files (SOUL.md, user.md, .hermes.md, AGENTS.md) across the default profile and per-profile directories. Use when a use... |

### productivity

| Skill | Description |
|---|---|
| **github-readme-authoring** | Create production-grade GitHub README.md files — structure, badges, installation, usage, API, contributing, license, and maintenance sections with real examples |

### reasoning

| Skill | Description |
|---|---|
| **bayesian-reasoning** | Probabilistic graphical models (Bayesian & Markov networks) for structured uncertainty reasoning in Hermes. Enables causal planning, belief tracking, diagnos... |

### robotics

| Skill | Description |
|---|---|
| **isaac-lab-bridge** | Bridge between Hermes (cognitive architecture) and Isaac Lab (robot learning). Translates Hermes plans → Isaac Lab policy execution → observations back to He... |

### software-development

| Skill | Description |
|---|---|
| **github-repo-ingest** | Shallow-first GitHub repository ingestion using gitingest CLI. Start with README + structure, then selectively deep-dive into specific directories/files. |
| **gitingest-usage** | Best practices for using GitIngest (CLI & Python) to extract repository content for LLM consumption |
| **hermes-voice-local** | "Set up Hermes voice (STT + TTS) fully local and free — stop paying for OpenAI Whisper transcription and run faster-whisper inside the gateway venv. Load thi... |

## Layout
```
hermes_skills/
├── README.md            # this file (index of all skills)
├── <category>/
│   └── <skill>/
│       ├── README.md    # human-readable overview
│       ├── SKILL.md     # the skill definition
│       ├── references/  # deep-dive docs
│       ├── templates/   # prompt bodies
│       └── scripts/     # runnable helpers
```

## Notes
- Skills follow the [agentskills.io](https://agentskills.io) convention.
- Per-skill READMEs are generated from `SKILL.md`; extend them as needed.
