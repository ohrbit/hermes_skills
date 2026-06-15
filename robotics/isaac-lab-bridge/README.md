# isaac-lab-bridge

[![Skill](https://img.shields.io/badge/Hermes_Skill-isaac--lab--bridge-8dbb3c)](https://github.com/nousresearch/hermes-agent)
[![Category](https://img.shields.io/badge/Category-robotics-blue)](https://github.com/nousresearch/hermes-agent/tree/main/skills/robotics)
[![License](https://img.shields.io/github/license/nousresearch/hermes-agent)]()

> **Bridge between Hermes (cognitive architecture) and Isaac Lab (robot learning)** — translates Hermes plans → Isaac Lab policy execution → observations back to Hermes memory.

## Why isaac-lab-bridge?

**Problem:** Cognitive agents (Hermes) excel at planning, reasoning, and memory but lack motor control. Robot simulators (Isaac Lab) excel at physics, RL policies, and execution but lack semantic understanding.

**Solution:** This skill connects **Hermes' cognitive layer** (intent, planning, skills, values) with **Isaac Lab's motor layer** (RL policies, sim/real execution). Hermes decides *what* and *why*; Isaac Lab executes *how*.

## Features

- ✅ **Bidirectional Translation** — Hermes skill params ↔ Isaac Lab action tensors (joint pos/vel/torque)
- ✅ **Skill Registry** — Declarative YAML mapping Hermes skills → Isaac Lab tasks + policy checkpoints
- ✅ **Execution Loop** — Manages Isaac Lab env lifecycle from Hermes (load, step, execute, close)
- ✅ **Safety Layer** — Pre-action validation, post-step monitoring, emergency stop
- ✅ **Memory Integration** — Observations → Hermes 3-tier memory (Hot/Vault/Daily)
- ✅ **Multiple Protocols** — In-process (Python), ROS 2 Bridge, gRPC/ZeroMQ
- ✅ **bayesian-reasoning Integration** — Risk-aware policy selection via causal inference
- ✅ **Sim-to-Real Ready** — Domain randomization config, workspace calibration, safety limits

## Quick Start

```bash
# 1. Install Isaac Lab (see NVIDIA docs)
# 2. Train/obtain a policy checkpoint
# 3. Register skill in skills/registry.yaml
# 4. From Hermes:
hermes skill load isaac-lab-bridge
> execute_skill("pick_place", {"target_position": [0.5, 0.0, 0.1]})
```

## Minimal Working Example

```python
# skills/registry.yaml
skills:
  pick_place:
    isaac_task: "PickPlace-Cube-Franka-v0"
    policy_checkpoint: "logs/rsl_rl/pick_place/policy.pt"
    obs_space: ["joint_pos", "joint_vel", "eef_pos", "eef_quat", "cube_pos"]
    action_space: "joint_position"
    params: ["target_position", "grasp_width", "approach_height"]
    safety_limits:
      max_force: 50.0
      max_velocity: 1.5
      workspace_bounds: [[-0.8, -0.8, 0.0], [0.8, 0.8, 1.2]]

# Hermes side
from isaac_lab_bridge.hermes.skill_executor import IsaacLabSkillExecutor
from isaac_lab_bridge.rosetta.executor import IsaacLabExecutor

executor = IsaacLabExecutor("skills/registry.yaml", headless=True)
skill = IsaacLabSkillExecutor(executor)

result = await skill.execute("pick_place", {"target_position": [0.5, 0.0, 0.1]})
print(result)  # → SkillResult(success=True, observations={...}, memory_entries=[...])
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HERMES (Cognitive)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │  Intent  │→ │ Planner  │→ │ Skill    │→ │ Rosetta Bridge │  │
│  │  (SOUL)  │  │ (HTN/LLM)│  │ Library  │  │ (this skill)   │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────┬────────┘  │
└─────────────────────────────────────────────────────┼───────────┘
                                                      │ JSON/ROS2
                                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ISAAC LAB (Motor)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Task Env    │← │ Policy       │← │ Action Tensor        │  │
│  │  (Isaac Lab) │  │ (PPO/SAC/    │  │ (joint pos/vel/torque)│  │
│  │              │  │  RSL-RL/SKRL)│  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│         │                                      │                │
│         ▼                                      ▼                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Observation  │→ │ Reward/Term  │→ │ Hermes Memory Writer │  │
│  │ (proprio,    │  │ (success,    │  │ (episodic + semantic)│  │
│  │  vision,     │  │  safety,     │  │                      │  │
│  │  tactile)    │  │  progress)   │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Skill Registry (`skills/registry.yaml`)

```yaml
skills:
  pick_place:
    isaac_task: "PickPlace-Cube-Franka-v0"
    policy_checkpoint: "logs/rsl_rl/pick_place/policy.pt"
    obs_space: ["joint_pos", "joint_vel", "eef_pos", "eef_quat", "cube_pos"]
    action_space: "joint_position"  # or joint_velocity, joint_torque
    params: ["target_position", "grasp_width", "approach_height"]
    safety_limits:
      max_force: 50.0
      max_velocity: 1.5
      workspace_bounds: [[-0.8, -0.8, 0.0], [0.8, 0.8, 1.2]]

  push_grasp:
    isaac_task: "PushGrasp-Cube-Franka-v0"
    policy_checkpoint: "logs/rsl_rl/push_grasp/policy.pt"
    ...
```

### 2. Rosetta Translator (`rosetta/translator.py`)

```python
# Hermes → Isaac Lab
def hermes_to_isaac(skill_name: str, params: dict) -> tuple[dict, torch.Tensor]:
    """Returns (env_config, action_tensor) for Isaac Lab step."""

# Isaac Lab → Hermes
def isaac_to_hermes(obs: dict, reward: float, terminated: bool, info: dict) -> dict:
    """Returns observation dict for Hermes memory."""
```

### 3. Execution Loop (`rosetta/executor.py`)

```python
class IsaacLabExecutor:
    def __init__(self, skill_registry: str, headless: bool = True):
        self.env = None
        self.policy = None
        self.registry = load_registry(skill_registry)

    def load_skill(self, skill_name: str) -> bool:
        """Load task env + policy checkpoint."""

    def step(self, action: torch.Tensor) -> tuple[dict, float, bool, dict]:
        """Single env step, returns obs, reward, done, info."""

    def execute_skill(self, skill_name: str, params: dict, max_steps: int = 500) -> ExecutionResult:
        """Run skill to completion or failure."""

    def close(self):
        """Cleanup env, simulator."""
```

### 4. Safety Monitor (`rosetta/safety.py`)

```python
class SafetyMonitor:
    def check_pre_action(self, action: torch.Tensor, obs: dict) -> tuple[bool, str]:
        """Validate action before sending to robot."""

    def check_post_step(self, obs: dict, reward: float) -> tuple[bool, str]:
        """Validate state after step. Trigger emergency stop if needed."""

    def emergency_stop(self) -> EmergencyStopCommand:
        """Generate zero-velocity / gravity-compensation command."""
```

## Communication Protocols

| Protocol | Use Case | Latency | Setup |
|----------|----------|---------|-------|
| **In-Process (Python API)** | Dev, single-robot, sim-only | ~0ms | `pip install isaaclab[rl]` |
| **ROS 2 Bridge** | Real robot, multi-process, sim+real | ~1-5ms | ROS 2 topics/services |
| **gRPC / ZeroMQ** | High-frequency control, embedded | ~0.5ms | Custom protobuf |

### ROS 2 Topics

- `/isaac/obs` — Observations (sensor_msgs)
- `/isaac/action` — Action commands (custom)
- `/isaac/skill_cmd` — Skill execution requests
- `/isaac/skill_result` — Skill completion results
- `/isaac/load_skill` — Service: load task + policy
- `/isaac/get_policy_info` — Service: policy metadata

## Memory Integration (Hermes 3-Tier)

| Tier | Content | Retention |
|------|---------|-----------|
| **Hot (Tier 1)** | Current skill execution trace, live obs | Session |
| **Vault (Tier 2)** | Skill outcomes, learned params, failure cases | Permanent |
| **Daily (Tier 3)** | Episode summaries, performance trends | Rolling |

```python
# In skill_executor.py - after skill execution
if result.success:
    # Semantic memory: "pick_place works for red cubes at height 0.1"
    await hermes.memory.write({
        "type": "semantic",
        "content": f"pick_place succeeds for {params} in context {obs}",
        "tags": ["skill_outcome", "pick_place", "success"]
    })
else:
    # Episodic + semantic: failure case for replanning
    await hermes.memory.write({
        "type": "episodic",
        "content": f"pick_place failed: {result.failure_reason}",
        "tags": ["skill_outcome", "pick_place", "failure"]
    })
```

## bayesian-reasoning Integration

```python
# In isaac-lab-bridge skill_executor.py
from bayesian_reasoning import InferenceEngine

engine = InferenceEngine()

# Before executing: predict outcome distribution
prediction = engine.query(
    model_name="pick_place_outcome",
    variables=["success", "grasp_stability"],
    evidence={"cube_weight": 0.5, "surface_friction": 0.3}
)

# Risk-aware decision
if prediction.marginal("success")["succeed"] < 0.7:
    await hermes.skill.execute("request_human", {"reason": "low_confidence"})

# After execution: update belief, learn
engine.learn_from_memory("pick_place", "SELECT * FROM skill_outcomes WHERE skill='pick_place'")
```

## Key Isaac Lab APIs

| Need | API |
|------|-----|
| Create env | `gym.make("Isaac-Lab-Task", cfg=env_cfg)` |
| Load policy | `policy = torch.jit.load(checkpoint).to(device)` |
| Step env | `obs, reward, done, info = env.step(action)` |
| Get obs space | `env.observation_space` |
| Get action space | `env.action_space` |
| Domain randomization | `env.cfg.domain_rand` |
| Camera sensors | `env.cfg.viewer`, `env.cfg.tiled_camera` |
| ROS 2 bridge | `IsaacLabROS2Bridge` (in `isaaclab_ros`) |

## File Structure

```
isaac-lab-bridge/
├── SKILL.md
├── skills/
│   └── registry.yaml          # Skill → Task/Policy mapping
├── rosetta/
│   ├── __init__.py
│   ├── translator.py          # Hermes ↔ Isaac Lab tensor translation
│   ├── executor.py            # Isaac Lab env + policy lifecycle
│   └── safety.py              # Safety monitor, emergency stop
├── hermes/
│   ├── __init__.py
│   └── skill_executor.py      # Hermes-side skill wrapper
├── ros2_bridge/               # Optional ROS 2 interface
│   ├── package.xml
│   ├── setup.py
│   └── isaac_bridge/
│       ├── __init__.py
│       ├── bridge_node.py
│       └── msg/               # Custom ROS 2 messages
├── templates/
│   ├── registry.yaml.template
│   └── skill_config.yaml.template
├── scripts/
│   ├── test_bridge.py         # End-to-end test
│   └── calibrate_workspace.py # Workspace bounds calibration
└── references/
    └── isaac_lab_api.md       # Key Isaac Lab APIs cheat sheet
```

## Development Workflow

1. **Define skill** in `skills/registry.yaml`
2. **Implement translator** for that skill's obs/action spaces
3. **Test in sim** with `scripts/test_bridge.py --skill pick_place --headless`
4. **Add safety limits** for real robot
5. **Deploy** via ROS 2 bridge or in-process

## Pitfalls

| Pitfall | Mitigation |
|---------|------------|
| **Action space mismatch** | Translator handles normalization, coordinate frames, IK |
| **Observation frequency** | Isaac Lab runs 60-120Hz. Downsample or summarize for Hermes |
| **Sim-to-real gap** | Domain randomization + real-world calibration required |
| **Blocking calls** | `env.step()` blocks. Run executor in separate thread/process, queue comms |
| **GPU memory** | Isaac Lab + Hermes + policy on same GPU → OOM. Use `device_map` or separate GPUs |

## Verification

```bash
# Unit tests
pytest rosetta/test_translator.py
pytest rosetta/test_executor.py

# Integration test (needs Isaac Lab installed)
python scripts/test_bridge.py --skill pick_place --headless

# Safety test
python scripts/test_bridge.py --skill pick_place --safety-check
```

## Contributing

This skill lives in the Hermes Agent skills registry. Improvements welcome via PR.

## License

MIT — Part of [Hermes Agent](https://github.com/nousresearch/hermes-agent) skills collection.