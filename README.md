# 🛠️ hermes_skills

[![Skills](https://img.shields.io/badge/skills-14-blue)](https://github.com/ohrbit/hermes_skills)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/ohrbit/hermes_skills/blob/main/LICENSE)
[![Agent](https://img.shields.io/badge/agent-Hermes%20Agent-8A2BE2)](https://hermes-agent.nousresearch.com)
[![Convention](https://img.shields.io/badge/convention-agentskills.io-orange)](https://agentskills.io)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](https://github.com/ohrbit/hermes_skills/pulls)

A curated collection of [Hermes Agent](https://hermes-agent.nousresearch.com) skills published by **ohrbit**.
Each skill lives in `category/skill-name/` with a `SKILL.md` (the definition) and a human-readable `README.md`.

## 📦 Install
```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install <skill-name>
```

## 🧩 Skills (14)

### 🎨 creative
| Skill | Description |
|---|---|
| **nano-banana-prompting** | Prompting frameworks/patterns for Google Nano Banana (Gemini 3.1 Flash/Pro Image) — 5 official frameworks. |

### ⚙️ devops
| Skill | Description |
|---|---|
| **agent-swarm-loop** | Evolutionary, fitness-gated multi-agent orchestration — dynamic expert teams on a shared GitHub workspace, selection + persistence. |
| **jit-agent-teams** | Spin up Just-In-Time agent teams per task — ephemeral profiles, parallel kanban dispatch, Kanban-as-IPC, Modal wedge recovery. |
| **kanban-orchestrator** | Decomposition playbook for routing work through Kanban — decompose don't execute, JIT profile pattern, dependencies. |
| **model-selection-and-jit-routing** | Pick the right model per task + route JIT agents by real free-tier limits (Nous/DeepSeek/Cerebras/NVIDIA/Gemini). |
| **hermes-serverless-backend** | Wire Modal/Daytona as the serverless `terminal.backend` — agent compute in ephemeral cloud sandboxes, idle = $0. |

### 🧠 hermes
| Skill | Description |
|---|---|
| **hermes-context-stack** | Verify/manage context-stack files (SOUL.md, user.md, .hermes.md) across default + per-profile dirs. |
| **hermes-voice-local** | Set up Hermes voice (STT + TTS) fully local + free — faster-whisper + Edge TTS, stop paying for OpenAI. |

### 📝 productivity
| Skill | Description |
|---|---|
| **github-readme-authoring** | Production-grade GitHub READMEs — structure, badges, install, usage, API, contributing, license (incl. Hermes Skill Mode). |

### 🔢 reasoning
| Skill | Description |
|---|---|
| **bayesian-reasoning** | Probabilistic graphical models (Bayesian/Markov networks) for uncertainty reasoning — causal planning, diagnosis, decision-making. |

### 🤖 robotics
| Skill | Description |
|---|---|
| **isaac-lab-bridge** | Bridge Hermes (cognitive) ↔ Isaac Lab (motor) — plans → RL policy execution → observations back to memory. |

### 💻 software-development
| Skill | Description |
|---|---|
| **github-repo-ingest** | Shallow-first GitHub repo ingestion via gitingest — README + tree first, then targeted deep dives. |
| **gitingest-usage** | Best practices for GitIngest (CLI & Python) to extract repo content for LLM consumption. |
| **third-party-skill-evaluation** | Evaluate external agent-skill repos for import — discovery, relevance scoring, adaptation feasibility, import/adapt/skip verdict. |

## 📂 Layout
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

## 📌 Notes
- 🧬 Skills follow the [agentskills.io](https://agentskills.io) convention.
- 📖 Every published skill has a hand-authored `README.md` (see `github-readme-authoring`).
- ⚡ Install a skill, then read its `README.md` for usage.
