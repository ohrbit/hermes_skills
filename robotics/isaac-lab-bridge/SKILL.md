---
name: isaac-lab-bridge
description: Bridge between Hermes (cognitive architecture) and Isaac Lab (robot learning). Translates Hermes plans → Isaac Lab policy execution → observations back to Hermes memory.
category: robotics
tags: [isaac-lab, isaac-sim, robotics, sim-to-real, policy, skill, ros2, hermes]
version: "0.1.0"
---

# Isaac Lab ↔ Hermes Bridge

## Purpose
Connect Hermes' cognitive layer (planning, memory, skills, values) with Isaac Lab's motor layer (RL policies, simulated/real robot execution). Hermes decides *what* and *why*; Isaac Lab executes *how*.

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
Maps Hermes skill names → Isaac Lab task configs + policy checkpoints.

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
  
  pour:
    isaac_task: "Pour-Liquid-Franka-v0"
    policy_checkpoint: "logs/rsl_rl/pour/policy.pt"
    ...
```

### 2. Rosetta Translator (`rosetta/translator.py`)
Bidirectional translation between Hermes skill calls and Isaac Lab tensors.

```python
# Hermes → Isaac Lab
def hermes_to_isaac(skill_name: str, params: dict) -> tuple[dict, torch.Tensor]:
    """Returns (env_config, action_tensor) for Isaac Lab step."""
    
# Isaac Lab → Hermes
def isaac_to_hermes(obs: dict, reward: float, terminated: bool, info: dict) -> dict:
    """Returns observation dict for Hermes memory."""
```

### 3. Execution Loop (`rosetta/executor.py`)
Manages the Isaac Lab environment lifecycle from Hermes.

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

### 4. Hermes Integration (`hermes/skill_executor.py`)
Hermes-side skill that delegates to Isaac Lab.

```python
class IsaacLabSkillExecutor:
    """Hermes skill that wraps Isaac Lab execution."""
    
    def __init__(self, executor: IsaacLabExecutor):
        self.executor = executor
    
    async def execute(self, skill_name: str, params: dict) -> SkillResult:
        # 1. Translate params → action tensor
        # 2. Run executor.execute_skill()
        # 3. Stream observations → Hermes memory (episodic)
        # 4. On success: store semantic memory ("learned: pick_place works for red cubes")
        # 5. On failure: trigger replan, store failure case
```

## Communication Protocols

### Option A: In-Process (Python API)
Hermes and Isaac Lab in same process. Fastest, simplest.
- Requires: `pip install isaaclab[rl]` in Hermes env
- Use for: development, single-robot, sim-only

### Option B: ROS 2 Bridge (Distributed)
Hermes ↔ Isaac Lab via ROS 2 topics/services.
- Topics: `/isaac/obs`, `/isaac/action`, `/isaac/skill_cmd`, `/isaac/skill_result`
- Services: `/isaac/load_skill`, `/isaac/get_policy_info`
- Use for: real robot, multi-process, sim + real

### Option C: gRPC / ZeroMQ (Custom)
Lower latency than ROS 2, no ROS dependency.
- Define protobuf for SkillCommand, Observation, SkillResult
- Use for: high-frequency control loops, embedded deploy

## Safety Layer (`rosetta/safety.py`)

```python
class SafetyMonitor:
    def __init__(self, limits: SafetyLimits):
        self.limits = limits
        self.violation_count = 0
    
    def check_pre_action(self, action: torch.Tensor, obs: dict) -> tuple[bool, str]:
        """Validate action before sending to robot."""
    
    def check_post_step(self, obs: dict, reward: float) -> tuple[bool, str]:
        """Validate state after step. Trigger emergency stop if needed."""
    
    def emergency_stop(self) -> EmergencyStopCommand:
        """Generate zero-velocity / gravity-compensation command."""
```

## Memory Integration

Observations flow to Hermes' 3-tier memory:

| Tier | Content | Retention |
|------|---------|-----------|
| **Hot (Tier 1)** | Current skill execution trace, live obs | Session |
| **Vault (Tier 2)** | Skill outcomes, learned parameters, failure cases | Permanent |
| **Daily (Tier 3)** | Episode summaries, performance trends | Rolling |

Use `hermes memory` tools or OSB plugin to write.

## Quickstart

```bash
# 1. Install Isaac Lab (see docs)
# 2. Train/obtain a policy checkpoint
# 3. Register skill in skills/registry.yaml
# 4. From Hermes:
hermes skill load isaac-lab-bridge
> execute_skill("pick_place", {"target_position": [0.5, 0.0, 0.1]})
```

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

## Key Isaac Lab APIs (Reference)

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

## Development Workflow

1. **Define skill** in `skills/registry.yaml`
2. **Implement translator** for that skill's obs/action spaces
3. **Test in sim** with `scripts/test_bridge.py`
4. **Add safety limits** for real robot
5. **Deploy** via ROS 2 bridge or in-process

## Pitfalls

- **Action space mismatch**: Hermes params ≠ policy input. Translator must handle normalization, coordinate frames, IK.
- **Observation frequency**: Isaac Lab runs at 60-120Hz. Hermes doesn't need every frame — downsample or summarize.
- **Sim-to-real gap**: Policies trained in sim need domain randomization + real-world calibration.
- **Blocking calls**: `env.step()` blocks. Run executor in separate thread/process, communicate via queue.
- **GPU memory**: Isaac Lab + Hermes + policy on same GPU → OOM. Use `device_map` or separate GPUs.

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