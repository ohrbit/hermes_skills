# Isaac Lab ↔ Hermes Bridge

> **Connect Hermes' cognitive layer to Isaac Lab's motor layer** — plans become RL policy execution, observations flow back into memory.

## Why this skill?

Hermes is great at *deciding what and why*; Isaac Lab is great at *executing how* (RL policies on simulated/real robots). The gap is translation: Hermes skill calls ↔ Isaac Lab action tensors, and robot observations ↔ Hermes memory. This skill is the Rosetta bridge plus a declarative skill→policy registry.

## What it does

- ✅ Skill Registry — maps Hermes skill names → Isaac Lab task configs + policy checkpoints
- ✅ Rosetta Translator — bidirectional Hermes↔Isaac Lab (JSON / ROS2)
- ✅ Observation → Hermes memory writer (episodic + semantic)
- ✅ Safety limits per skill (max force, velocity, workspace bounds)
- ✅ Sim-to-real ready structure

## Install

```bash
hermes skills tap add ohrbit/hermes_skills
hermes skills install isaac-lab-bridge
```

## Quick Start

```text
In chat: "Execute the pick_place skill on the Franka in Isaac Lab"
```

Hermes resolves `pick_place` → task config + checkpoint, translates params to an action tensor, Isaac Lab runs the policy, observations return to memory.

## How it works

```
HERMES (cognitive)                ISAAC LAB (motor)
Intent → Planner → Skill → Bridge  ──JSON/ROS2──▶  Task Env ← Policy ← Action Tensor
                                    ◀── observations / reward ──  Hermes Memory Writer
```

## Usage / Examples

### Basic
> "Run the pour skill."

`skills/registry.yaml` resolves `pour` → `Pour-Liquid-Franka-v0` + checkpoint; translator sends target params; safety limits cap force/velocity.

### Advanced
Custom skill: add an entry to `skills/registry.yaml` with `obs_space`, `action_space`, `params`, `safety_limits` — no code needed for standard patterns.

## File layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Architecture, components |
| `skills/registry.yaml` | Skill → task/policy mapping |
| `rosetta/translator.py` | Bidirectional translation |
| `references/` | Deep dives |

## Related skills

- `bayesian-reasoning` — uncertainty over robot state
- Your robot/environment configs

## Notes / caveats

- Action space: `joint_position` / `joint_velocity` / `joint_torque` — match the policy.
- Safety limits are enforced at the bridge; misconfigured bounds = damaged sim/real hardware.

## License

MIT — © 2024 ohrbit
