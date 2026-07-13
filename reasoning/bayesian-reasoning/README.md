# Bayesian Reasoning for Hermes

> **Structured uncertainty reasoning via Bayesian & Markov networks** — causal planning, belief tracking, diagnosis, and decision-making under uncertainty.

## Why this skill?

LLMs are confident even when wrong. When the task is "if I do X, what's P(success)?" or "given these symptoms, what's the root cause?", you need explicit probabilistic reasoning, not a vibe. This skill brings pgmpy-backed Bayesian networks (causal, directed) and Markov networks (correlational, undirected) into Hermes as a reasoning engine with a declarative model registry.

## What it does

- ✅ Causal planning — P(outcome | action) with side-effect estimates
- ✅ Belief tracking — fuse noisy observations into a posterior over world state
- ✅ Diagnosis — symptoms → root cause via inference
- ✅ Decision under uncertainty — maximize expected utility, risk-aware
- ✅ Counterfactuals — "would Y have happened if I'd done X?"
- ✅ Declarative `models/registry.yaml` (no code for standard patterns)

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install bayesian-reasoning
pip install pgmpy   # backend
```

## Quick Start

```text
In chat: "If I deploy on Friday, what's P(rollback within 24h)?"
```

Hermes builds/loads a causal net, sets evidence, runs variable elimination, returns the posterior.

## How it works

```
Planner / Executor / Memory
        │
        ▼
Bayesian Reasoning Engine
   ├─ Bayesian Networks (causal)
   ├─ Markov Networks (correlation)
   └─ Inference (VE, BP, MCMC)
        │
        ▼
Model Registry (skill-outcome, sensor-noise, diagnostic, utility nets)
```

## Usage / Examples

### Basic
> "Given sensor noise σ=0.3, what's the posterior on cube weight?"

Loads/defines a continuous Bayesian net, injects the observation, runs inference.

### Advanced
> "Maximize expected utility across these 3 actions with risk aversion."

Builds a utility net, computes EU per action, picks the max with risk penalty.

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Purpose, architecture, components |
| `models/registry.yaml` | Declarative network definitions |
| `scripts/` | Inference helpers (learn_from_vault, visualize_model, etc.) |
| `references/` | Causal-inference + pgmpy guides |

## Related skills

- `reasoning/*` — other structured-reasoning skills
- Your `SOUL.md` / preferences — feed the utility nets

## Notes / caveats

- Inference choice (VE vs MCMC) depends on network size; large nets need sampling.
- Registries are declarative — define a model once, reuse across sessions.

## License

MIT — © 2024 ohrbit
