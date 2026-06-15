# Isaac Lab API Reference

Quick reference for key Isaac Lab APIs used by the bridge.

## Environment Creation

```python
import gymnasium as gym
from isaaclab.envs import ManagerBasedRLEnvCfg, ManagerBasedRLEnv

# Via gym (recommended)
env = gym.make("Isaac-Lab-Task-Name", cfg=env_cfg)

# Direct (for custom configs)
from isaaclab_tasks.manager_based.locomotion.velocity import flat_env_cfg
env_cfg = flat_env_cfg.FlatEnvCfg()
env_cfg.scene.num_envs = 64
env = ManagerBasedRLEnv(cfg=env_cfg)
```

## Common Task Names (Isaac Lab 1.0+)

| Category | Tasks |
|----------|-------|
| **Manipulation** | `PickPlace-Cube-Franka-v0`, `PickPlace-Cube-Allegro-v0`, `Pour-Liquid-Franka-v0`, `Handover-Franka-v0`, `Insert-Peg-Franka-v0` |
| **Locomotion** | `Ant-v0`, `Humanoid-v0`, `Anymal-C-v0`, `Go1-v0`, `G1-v0` |
| **Dexterous Hands** | `ShadowHand-OpenDoor-v0`, `Allegro-RotateCube-v0` |
| **Mobile Manipulation** | `Franka-Cabinet-v0`, `Franka-Dishwasher-v0` |

## Environment Config

```python
from isaaclab.envs import ManagerBasedRLEnvCfg

@configclass
class MyEnvCfg(ManagerBasedRLEnvCfg):
    # Scene
    scene: SceneCfg = SceneCfg(num_envs=4096, env_spacing=3.0)
    
    # Simulation
    sim: SimulationCfg = SimulationCfg(
        dt=0.005,  # 200Hz physics
        render_interval=2,
        device="cuda:0",
    )
    
    # Control
    decimation = 4  # Control at 50Hz (200/4)
    
    # Domain randomization
    domain_rand: DomainRandCfg = DomainRandCfg(...)
    
    # Termination
    episode_length_s = 20.0
```

## Policy Loading

```python
# RSL-RL (most common)
from rsl_rl.runners import OnPolicyRunner
runner = OnPolicyRunner(env, config, log_dir, device="cuda:0")
runner.load("logs/model_10000.pt")
policy = runner.get_inference_policy(device="cuda:0")

# Or TorchScript (deploy)
policy = torch.jit.load("policy.pt").to("cuda:0")
policy.eval()

# Inference
with torch.inference_mode():
    actions = policy(obs)
```

## Observation / Action Spaces

```python
# Get spaces
obs_space = env.observation_space  # Dict or Box
act_space = env.action_space       # Box

# Typical manipulation obs keys (from env.obs_buf):
# - "joint_pos"      : (num_envs, num_joints)
# - "joint_vel"      : (num_envs, num_joints)
# - "eef_pos"        : (num_envs, 3)
# - "eef_quat"       : (num_envs, 4)  [x, y, z, w]
# - "cube_pos"       : (num_envs, 3)
# - "cube_quat"      : (num_envs, 4)
# - "force_torque"   : (num_envs, 6)  [fx, fy, fz, tx, ty, tz]

# Action space (joint position):
# - (num_envs, 9) for Franka (7 arm + 2 finger)
```

## Step Loop

```python
obs, _ = env.reset()

while True:
    # Policy inference
    actions = policy(obs)
    
    # Step
    obs, reward, terminated, truncated, info = env.step(actions)
    
    # Render (optional)
    env.render()
    
    # Check done
    if terminated.any() or truncated.any():
        break

env.close()
```

## Camera / Vision Sensors

```python
from isaaclab.sensors import TiledCamera, RayCaster

# Tiled camera (RGB-D)
camera_cfg = TiledCameraCfg(
    prim_path="/World/envs/env_*/Camera",
    offset=CameraOffsetCfg(pos=(0.5, 0, 1.0), rot=(0.707, 0, 0.707, 0), convention="opengl"),
    data_types=["rgb", "depth", "normals"],
    width=640, height=480,
)

# Ray caster (LiDAR)
ray_caster_cfg = RayCasterCfg(
    prim_path="/World/envs/env_*/Robot/base_link",
    offset=RayCasterOffsetCfg(pos=(0, 0, 0.5)),
    pattern_cfg=LidarPatternCfg(),
    max_distance=10.0,
)

# Access in step:
rgb = obs["camera_rgb"]      # (N, H, W, 4) uint8
depth = obs["camera_depth"]  # (N, H, W) float
lidar = obs["lidar"]         # (N, num_rays, 3)
```

## Domain Randomization

```python
from isaaclab.envs import DomainRandCfg
from isaaclab.managers import RandTerm

@configclass
class MyDomainRandCfg(DomainRandCfg):
    # Physics
    physics_material = RandTerm(
        func=randomize_rigid_body_material,
        mode="reset",
        params={"static_friction_range": (0.5, 1.5), "dynamic_friction_range": (0.3, 1.0)}
    )
    
    # Mass
    robot_mass = RandTerm(
        func=randomize_rigid_body_mass,
        mode="reset",
        params={"asset_cfg": SceneEntityCfg("robot"), "mass_distribution_params": (-0.2, 0.2), "operation": "add"}
    )
    
    # Visual
    camera_color = RandTerm(
        func=randomize_camera_color,
        mode="reset",
    )
```

## ROS 2 Bridge (isaaclab_ros)

```python
# In environment config
from isaaclab_ros import IsaacLabROS2Bridge

bridge = IsaacLabROS2Bridge(
    env=env,
    node_name="isaac_lab_bridge",
    namespace="robot",
)

# Publishes:
# - /robot/joint_states (sensor_msgs/JointState)
# - /robot/tf (tf2_msgs/TFMessage)
# - /robot/camera/rgb (sensor_msgs/Image)
# - /robot/camera/depth (sensor_msgs/Image)

# Subscribes:
# - /robot/joint_commands (isaaclab_msgs/JointCommand)

bridge.spin()
```

## Custom Messages (isaaclab_msgs)

```python
# From isaaclab_ros/msg
# JointCommand.msg:
#   Header header
#   string[] joint_names
#   float64[] position
#   float64[] velocity
#   float64[] effort
#   uint8 mode  # 0=position, 1=velocity, 2=effort

# SkillCommand.msg:
#   Header header
#   string skill_name
#   string[] param_names
#   float64[] param_values

# SkillResult.msg:
#   Header header
#   string skill_name
#   bool success
#   string error_message
#   float64 total_reward
#   int32 steps
```

## Key Imports

```python
# Core
import isaaclab
import isaaclab.sim as sim_utils
from isaaclab.envs import ManagerBasedRLEnv, ManagerBasedRLEnvCfg
from isaaclab.assets import ArticulationCfg, RigidObjectCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.managers import EventTermCfg, ObsTermCfg, RewTermCfg, TermTermCfg
from isaaclab.utils import configclass

# Sensors
from isaaclab.sensors import CameraCfg, TiledCameraCfg, RayCasterCfg
from isaaclab.sensors.contact_sensor import ContactSensorCfg

# Actuators
from isaaclab.actuators import ImplicitActuatorCfg

# Randomization
from isaaclab.managers import RandTerm

# Math
from isaaclab.utils.math import quat_rotate, quat_mul, euler_xyz_from_quat
```

## Training (RSL-RL)

```bash
# Train
python scripts/rsl_rl/train.py --task PickPlace-Cube-Franka-v0 --num_envs 4096 --headless

# Resume
python scripts/rsl_rl/train.py --task PickPlace-Cube-Franka-v0 --resume logs/xxx

# Play (visualize)
python scripts/rsl_rl/play.py --task PickPlace-Cube-Franka-v0 --checkpoint logs/xxx/model_10000.pt
```

## Useful Environment Variables

```bash
# Isaac Sim / Lab paths
export ISAACSIM_PATH="/opt/isaacsim"
export ISAACLAB_PATH="/workspace/IsaacLab"

# Python path
export PYTHONPATH="${ISAACLAB_PATH}:${PYTHONPATH}"

# GPU
export CUDA_VISIBLE_DEVICES=0

# Headless
export OMNI_KIT_ACCEPT_EULA=1
export ISAACLAB_HEADLESS=1
```

## Common Issues

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: isaaclab` | `pip install -e ${ISAACLAB_PATH}` |
| `CUDA OOM` | Reduce `num_envs`, use `torch.cuda.empty_cache()` |
| `Task not registered` | Check `isaaclab_tasks` installed, task name matches |
| `Policy input shape mismatch` | Verify `obs_space` matches policy expectation |
| `Slow simulation` | Enable `fabric`, reduce `render_interval`, use `headless=True` |

## Version Compatibility

| Isaac Lab | Isaac Sim | Python | PyTorch |
|-----------|-----------|--------|---------|
| 1.0.x | 2023.1.1 | 3.10 | 2.1+ |
| 1.1.x | 4.0.0 | 3.10 | 2.2+ |
| 1.2.x | 4.1.0 | 3.10 | 2.3+ |
| 2.0.x | 4.2.0 | 3.11 | 2.4+ |

Check: `python -c "import isaaclab; print(isaaclab.__version__)"`