# Isaac Lab ↔ Hermes Bridge

<div align="center">

![Isaac Lab](https://img.shields.io/badge/Isaac%20Lab-1.2%2B-76B900?logo=nvidia&logoColor=white)
![Isaac Sim](https://img.shields.io/badge/Isaac%20Sim-4.2%2B-76B900?logo=nvidia&logoColor=white)
![Hermes](https://img.shields.io/badge/Hermes%20Agent-0.5%2B-6E56CF?logo=hermes&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Apache%202.0-blue)

**The Rosetta Layer: Connecting Cognitive Architecture to Robot Motor Control**

[Architecture](#-architecture) • [Installation](#-installation) • [Quickstart](#-quickstart) • [Configuration](#-configuration) • [Memory Integration](#-memory-integration) • [Safety](#-safety) • [Development](#-development)

</div>

---

## Overview

**Isaac Lab Bridge** is the translation layer between **Hermes** (cognitive architecture: planning, memory, skills, values) and **Isaac Lab** (robot learning: RL policies, simulation, real-robot execution).

| Layer | Responsibility | Technology |
|-------|----------------|------------|
| **Intent** | *What* and *Why* — goals, values, constraints | Hermes SOUL.md, preferences |
| **Planner** | Task decomposition → skill sequences | HTN / LLM planning |
| **Rosetta Bridge** | **This project** — translation, safety, execution, memory sync | Python, PyTorch, Isaac Lab |
| **Motor** | *How* — low-level control, policy inference | Isaac Lab, RSL-RL/SKRL, sim/real |

### The Problem

```
Hermes: "Make coffee" → Plan: [grind, tamp, brew, pour]
                           ↓
                    ??? No standard interface ???
                           ↓
Isaac Lab: Policy expects (obs: Dict[str, Tensor]) → action: Tensor
```

### The Solution

This bridge provides:
- **Skill Registry** — Declarative YAML mapping Hermes skills → Isaac Lab tasks + policy checkpoints
- **Rosetta Translator** — Bidirectional tensor ↔ symbolic conversion with normalization, coordinate frames, IK
- **Executor** — Manages Isaac Lab env lifecycle, async execution, multi-skill switching
- **Safety Monitor** — Workspace bounds, force/velocity limits, sim-to-real adaptation, emergency stop
- **Memory Sync** — Streams observations to Hermes 3-tier memory (hot/vault/daily)
- **MCP Integration** — Uses NVIDIA's `isaacsim_mcp` for development-time knowledge lookup

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HERMES (Cognitive)                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────────────────────┐   │
│  │  Intent  │──→│ Planner  │──→│  Skill   │──→│   Rosetta Bridge       │   │
│  │ (SOUL)   │   │(HTN/LLM) │   │ Library  │   │  (this project)        │   │
│  └──────────┘   └──────────┘   └──────────┘   └───────────┬────────────┘   │
└────────────────────────────────────────────────────────────┼────────────────┘
                                                             │ JSON / ROS 2
                                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ISAAC LAB (Motor)                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  Task Env        │←─│  Policy          │←─│  Action Tensor           │  │
│  │  (Isaac Lab)     │  │  (PPO/SAC/       │  │  (joint pos/vel/torque)  │  │
│  │                  │  │   RSL-RL/SKRL)   │  │                          │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
│          │                       │                        │                │
│          ▼                       ▼                        ▼                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ Observation      │──→│ Reward / Term    │──→│ Hermes Memory Writer   │  │
│  │ (proprio, vision,│   │ (success, safety,│   │ (episodic + semantic)  │  │
│  │  tactile)        │   │  progress)       │   │                        │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Declarative Skill Registry** | YAML maps skill names → task env, policy checkpoint, obs/action spaces, params, safety limits |
| **Tensor ↔ Symbolic Translation** | Normalization, coordinate frames, IK fallback, derived quantities (distances, forces) |
| **Async Execution** | Non-blocking skill execution with trajectory recording |
| **Multi-Skill Manager** | Load/switch between skills at runtime |
| **Safety Layer** | Pre/post-action checks, workspace bounds, force limits, tilt limits, human proximity, sim→real adaptation |
| **3-Tier Memory Integration** | Hot (live trace) → Vault (learned outcomes) → Daily (episode summaries) |
| **ROS 2 Bridge Ready** | Scaffolding for distributed deployment |
| **Calibration Tools** | Workspace bounds, camera extrinsics, force sensor, joint limits |
| **Unit Tests** | Fully mocked — runs without Isaac Lab installed |

---

## Installation

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Isaac Sim | 4.2+ | [Download](https://developer.nvidia.com/isaac-sim) |
| Isaac Lab | 1.2+ | `pip install -e ./IsaacLab` |
| Python | 3.11+ | 3.10 not supported |
| PyTorch | 2.3+ | CUDA 12.1+ recommended |
| Hermes Agent | 0.5+ | `pip install hermes-agent` |

### Install Bridge

```bash
# Clone this skill into your Hermes skills directory
cd ~/.hermes/skills/robotics/
git clone <this-repo> isaac-lab-bridge

# Or if using as standalone package
pip install -e .

# Install Isaac Lab dependencies (if not already)
cd /path/to/IsaacLab
pip install -e .[rl]  # includes RSL-RL, SKRL, etc.
```

### Verify Installation

```bash
# Run unit tests (no Isaac Lab needed)
cd isaac-lab-bridge
python scripts/test_bridge.py -v

# Test with Isaac Lab (requires installation)
python scripts/test_bridge.py --integration --skill pick_place --headless
```

---

## Quickstart

### 1. Prepare Policy Checkpoint

Train or obtain a policy compatible with your Isaac Lab task:

```bash
# Example: Train pick-place with RSL-RL
cd IsaacLab
python scripts/rsl_rl/train.py --task PickPlace-Cube-Franka-v0 --num_envs 4096 --headless

# Checkpoint will be at: logs/rsl_rl/pick_place/model_XXXX.pt
# Convert to TorchScript for deployment:
python -c "
import torch
policy = torch.jit.load('logs/rsl_rl/pick_place/model_10000.pt')
torch.jit.save(policy, 'logs/rsl_rl/pick_place/policy.pt')
"
```

### 2. Configure Skill Registry

```bash
cp templates/registry.yaml.template skills/registry.yaml
# Edit skills/registry.yaml with your paths
```

```yaml
# skills/registry.yaml
skills:
  pick_place:
    isaac_task: "PickPlace-Cube-Franka-v0"
    policy_checkpoint: "/absolute/path/to/logs/rsl_rl/pick_place/policy.pt"
    policy_type: "rsl_rl"
    obs_space:
      - "joint_pos"
      - "joint_vel"
      - "eef_pos"
      - "eef_quat"
      - "cube_pos"
      - "cube_quat"
    action_space: "joint_position"
    action_dim: 9
    params:
      - name: "target_position"
        type: "vector3"
        default: [0.5, 0.0, 0.1]
      - name: "grasp_width"
        type: "float"
        default: 0.04
    safety_limits:
      max_force: 50.0
      max_velocity: 1.5
      workspace_bounds:
        min: [-0.6, -0.6, 0.02]
        max: [0.6, 0.6, 1.0]

global:
  sim_device: "cuda:0"
  headless: true
  physics_dt: 0.01
  control_dt: 0.02
```

### 3. Run from Hermes

```bash
# Start Hermes
hermes

# Load the bridge skill
> skill load isaac-lab-bridge

# Execute a skill
> execute_skill("pick_place", {"target_position": [0.4, 0.1, 0.1]})
```

### 4. Direct Python Usage

```python
import asyncio
from scripts.skill_executor import IsaacLabSkillExecutor, init_isaac_lab_skills

# Initialize
executor = IsaacLabSkillExecutor(
    registry_path="skills/registry.yaml",
    device="cuda:0",
    headless=True,
)

# Execute
result = await executor.execute(
    skill_name="pick_place",
    params={"target_position": [0.5, 0.0, 0.1]},
    max_steps=500,
)

print(f"Success: {result.success}")
print(f"Steps: {result.steps}")
print(f"Reward: {result.total_reward}")
print(f"Final obs: {result.observations}")

executor.close()
```

---

## Configuration

### Skill Registry (`skills/registry.yaml`)

```yaml
skills:
  <skill_name>:
    # Required
    isaac_task: "Isaac-Lab-Task-Name"      # Registered gym task
    policy_checkpoint: "path/to/policy.pt"  # TorchScript policy
    policy_type: "rsl_rl"                   # rsl_rl, skrl, sb3, cleanrl
    obs_space:                              # Observation keys policy expects
      - "joint_pos"
      - "eef_pos"
      - "cube_pos"
    action_space: "joint_position"          # joint_position, joint_velocity, joint_torque
    action_dim: 9                           # Must match policy output
    
    # Optional
    params:                                 # Hermes-callable parameters
      - name: "target_position"
        type: "vector3"
        default: [0.5, 0.0, 0.1]
        description: "Target position in world frame"
    
    safety_limits:                          # SafetyMonitor config
      max_force: 50.0
      max_velocity: 1.5
      max_joint_velocity: 3.14
      workspace_bounds:
        min: [-0.8, -0.8, 0.0]
        max: [0.8, 0.8, 1.2]
      collision_check: true
      force_limit: 30.0                     # Skill-specific force limit
      tilt_limit: 1.57                      # Max tilt (rad) for pour/handover
      human_proximity_stop: 0.3             # Stop if human closer than this

global:
  sim_device: "cuda:0"
  rl_device: "cuda:0"
  headless: true
  render_interval: 0
  physics_dt: 0.01
  control_dt: 0.02
  max_episode_length: 500
```

### Supported Policy Types

| Type | Load Method | Notes |
|------|-------------|-------|
| `rsl_rl` | `torch.jit.load()` | Most common, TorchScript export |
| `skrl` | `torch.load()` + `agent.policy` | Requires SKRL agent wrapper |
| `stable_baselines3` | `PPO.load()` | Needs SB3 environment wrapper |
| `cleanrl` | `torch.load()` | Direct state dict |

---

## Memory Integration

Observations flow to Hermes' **3-tier memory system**:

| Tier | Storage | Content | Retention |
|------|---------|---------|-----------|
| **Hot (Tier 1)** | In-memory | Current execution trace, live observations | Session |
| **Vault (Tier 2)** | Obsidian/Files | Skill outcomes, learned params, failure cases | Permanent |
| **Daily (Tier 3)** | Daily notes | Episode summaries, performance trends | Rolling |

### Memory Events

```python
# On skill completion, bridge writes:

# Tier 1: Hot
{
  "type": "skill_execution",
  "skill": "pick_place",
  "success": true,
  "steps": 127,
  "reward": 245.3,
  "timestamp": 1699900000.0
}

# Tier 2: Vault (success)
{
  "type": "skill_outcome",
  "skill": "pick_place",
  "params": {"target_position": [0.5, 0.0, 0.1]},
  "outcome": "success",
  "final_state": {"eef_to_cube_dist": 0.01, "gripper_width": 0.0},
  "lesson": "pick_place succeeded with params {...}"
}

# Tier 2: Vault (failure)
{
  "type": "skill_outcome",
  "skill": "pick_place",
  "params": {"target_position": [1.0, 0.0, 0.1]},
  "outcome": "failure",
  "error": "Workspace bounds violated",
  "lesson": "pick_place failed: target outside workspace"
}

# Tier 3: Daily
{
  "type": "episode",
  "skill": "pick_place",
  "success": true,
  "steps": 127,
  "reward": 245.3
}
```

### Custom Memory Writer

```python
from scripts.skill_executor import IsaacLabSkillExecutor

class MyMemoryWriter:
    async def write_hot(self, data): ...
    async def write_vault(self, data): ...
    async def write_daily(self, data): ...

executor = IsaacLabSkillExecutor(
    registry_path="skills/registry.yaml",
    memory_writer=MyMemoryWriter(),
)
```

---

## Safety

### SafetyMonitor Checks

| Check | Trigger | Action |
|-------|---------|--------|
| Joint velocity | Pre-action | Reject if > `max_joint_velocity` |
| Action magnitude | Pre-action | Reject if > 4π |
| Target workspace | Pre-action | Reject if outside bounds |
| Force/torque | Post-step | Warn, count violation |
| EEF workspace | Post-step | Warn, count violation |
| Tilt angle | Post-step | Warn if > `tilt_limit` |
| Human proximity | Post-step | Emergency stop if < `human_proximity_stop` |
| Joint limits | Post-step | Warn if near limits |

### Violation Escalation

```
Violation 1 → Warning log
Violation 2 → Warning log
Violation 3 → Emergency stop (zero velocity command)
```

### Sim-to-Real Adaptation

```python
from scripts.safety import SimToRealSafetyAdapter, SafetyLimits

sim_limits = SafetyLimits(max_force=50.0, max_velocity=2.0, ...)
real_limits = SimToRealSafetyAdapter.adapt_for_real(sim_limits)

# Result:
# max_force: 50.0 → 25.0 (50%)
# max_velocity: 2.0 → 1.0 (50%)
# max_joint_velocity: 3.14 → 2.2 (70%)
# human_proximity_stop: 0.3 → 1.5 (larger safety distance)
# max_violations: 3 → 1 (zero tolerance)
```

### Emergency Stop

```python
monitor = SafetyMonitor(limits)
stop_action = monitor.emergency_stop(action_dim=9)
# Returns: np.zeros(9) — let low-level controller handle gravity compensation
```

---

## Communication Protocols

### Option A: In-Process (Default)

Fastest. Hermes + Isaac Lab in same Python process.

```python
# Requires: pip install isaaclab[rl] in Hermes env
executor = IsaacLabExecutor(registry_path, skill_name)
```

### Option B: ROS 2 Bridge (Distributed)

Hermes ↔ Isaac Lab via ROS 2.

```
Topics:
  /isaac/obs           → sensor_msgs/msg/JointState + custom
  /isaac/action        → isaaclab_msgs/msg/JointCommand
  /isaac/skill_cmd     → isaaclab_msgs/msg/SkillCommand
  /isaac/skill_result  → isaaclab_msgs/msg/SkillResult

Services:
  /isaac/load_skill
  /isaac/get_policy_info
```

```bash
# In Isaac Lab container/process
ros2 run isaaclab_ros bridge_node

# In Hermes
hermes skill load isaac-lab-bridge --ros2
```

### Option C: gRPC / ZeroMQ

For embedded/high-frequency. Define protobuf:

```protobuf
message SkillCommand {
  string skill_name = 1;
  map<string, double> params = 2;
  int32 max_steps = 3;
}

message Observation {
  map<string, double> values = 1;
  Metrics meta = 2;
  Derived derived = 3;
}

message SkillResult {
  bool success = 1;
  string error = 2;
  Observation final_obs = 3;
  float64 total_reward = 4;
  int32 steps = 5;
}
```

---

## Development

### Project Structure

```
isaac-lab-bridge/
├── SKILL.md                    # Hermes skill manifest
├── skills/
│   └── registry.yaml           # YOUR skill configurations
├── templates/
│   ├── registry.yaml.template  # Template with examples
│   └── skill_config.yaml.template
├── scripts/
│   ├── translator.py           # Tensor ↔ symbolic translation
│   ├── executor.py             # Env lifecycle, execution loop
│   ├── safety.py               # SafetyMonitor, sim→real adapter
│   ├── skill_executor.py       # Hermes async wrapper + memory
│   ├── test_bridge.py          # Unit tests (mocked)
│   └── calibrate_workspace.py  # Calibration CLI
├── references/
│   ├── isaac_lab_api.md        # Isaac Lab API cheat sheet
│   └── mcp_integration.md      # isaacsim_mcp usage guide
└── ros2_bridge/                # ROS 2 scaffolding (TODO)
    ├── package.xml
    ├── setup.py
    └── isaac_bridge/
```

### Adding a New Skill

1. **Train/obtain policy** for your Isaac Lab task
2. **Add entry** to `skills/registry.yaml`
3. **Implement custom translator** (if needed) in `scripts/translator.py`:
   ```python
   class MySkillTranslator(ActionTranslator):
       def hermes_to_policy(self, params, obs):
           # Convert Hermes params → policy action
           # e.g., compute IK for target pose
           return action_tensor
   ```
4. **Register** in `create_translators()` factory
5. **Test**: `python scripts/test_bridge.py --skill my_skill`

### Running Tests

```bash
# Unit tests (no Isaac Lab)
python scripts/test_bridge.py -v

# Specific test class
python -m pytest scripts/test_bridge.py::TestSafetyMonitor -v

# Integration test (requires Isaac Lab)
python scripts/test_bridge.py --integration --skill pick_place --headless

# Safety test
python scripts/test_bridge.py --integration --skill pick_place --safety-check
```

### Calibration

```bash
# Full calibration (workspace, cameras, force sensors)
python scripts/calibrate_workspace.py --all --robot franka --output calib.json

# Individual
python scripts/calibrate_workspace.py --workspace --robot franka
python scripts/calibrate_workspace.py --cameras
python scripts/calibrate_workspace.py --force
```

---

## MCP Integration (Development-Time)

Use NVIDIA's **isaacsim_mcp** server for knowledge lookup while developing:

```bash
# Start MCP server (separate terminal)
cd kit-usd-agents/source/mcp/isaacsim_mcp
docker run --rm -p 9904:9904 --env-file ../.env isaacsim-mcp:latest

# Connect Hermes
hermes mcp add isaac-sim-mcp http://localhost:9904/mcp

# Ask Hermes:
> How do I configure domain randomization for Franka?
> Search for TiledCamera examples in Isaac Lab
> What's the RayCaster API for LiDAR simulation?
```

| Need | MCP Function |
|------|--------------|
| Framework docs | `get_isaac_sim_instructions` |
| Extension search | `search_isaac_sim_extensions` |
| Extension details | `get_isaac_sim_extension_details` |
| Code examples | `search_isaac_sim_code_examples` |
| Settings search | `search_isaac_sim_settings` |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: isaaclab` | `pip install -e /path/to/IsaacLab` |
| `CUDA OOM` | Reduce `num_envs` in registry, use `torch.cuda.empty_cache()` |
| `Task not registered` | Check `isaaclab_tasks` installed, task name exact match |
| `Policy input shape mismatch` | Verify `obs_space` matches policy expectation |
| `Slow simulation` | Enable Fabric, reduce `render_interval`, use `headless=true` |
| `Action space mismatch` | Check `action_dim` = policy output dim, `action_space` matches |
| `Import error: rsl_rl` | `pip install rsl-rl-lib` or use Isaac Lab's bundled version |

---

## Roadmap

- [ ] ROS 2 bridge implementation (`ros2_bridge/`)
- [ ] gRPC/ZeroMQ transport option
- [ ] Visual skill debugger (trajectory replay)
- [ ] Auto-calibration from real robot data
- [ ] Multi-robot fleet support
- [ ] Policy distillation utilities
- [ ] Hugging Face model hub integration

---

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Add tests for new functionality
4. Run test suite: `python scripts/test_bridge.py -v`
5. Submit PR with description of changes

### Code Style

```bash
# Format
black scripts/
isort scripts/

# Lint
ruff check scripts/
mypy scripts/
```

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **NVIDIA Isaac Lab Team** — Incredible robotics simulation platform
- **Hermes Agent Team** — Cognitive architecture that makes this meaningful
- **RSL-RL / SKRL Authors** — RL libraries that power the policies
- **NVIDIA kit-usd-agents** — `isaacsim_mcp` for development-time knowledge

---

## Citation

If you use this bridge in research, please cite:

```bibtex
@software{isaac_lab_bridge,
  title = {Isaac Lab ↔ Hermes Bridge: The Rosetta Layer for Cognitive Robotics},
  author = {Hermes Agent Contributors},
  year = {2025},
  url = {https://github.com/hermes-agent/isaac-lab-bridge}
}
```

---

<div align="center">

**Built for the Hermes Agent ecosystem** • Part of the robotics skill collection

[Report Bug](https://github.com/hermes-agent/isaac-lab-bridge/issues) • [Request Feature](https://github.com/hermes-agent/isaac-lab-bridge/issues/new) • [Discussions](https://github.com/hermes-agent/isaac-lab-bridge/discussions)

</div>