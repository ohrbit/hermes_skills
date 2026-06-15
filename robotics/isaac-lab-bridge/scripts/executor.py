"""
Isaac Lab Executor: Manages Isaac Lab environment lifecycle from Hermes.

Loads task environments, policy checkpoints, and executes skills
with safety monitoring and observation streaming.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import queue

import gymnasium as gym
import numpy as np
import torch
import yaml

from .translator import SkillConfig, create_translators

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of skill execution."""
    success: bool
    steps: int
    final_obs: dict
    total_reward: float
    error: str | None = None
    trajectory: list[dict] | None = None


@dataclass
class SafetyLimits:
    """Safety limits for skill execution."""
    max_force: float = 50.0
    max_velocity: float = 1.5
    max_joint_velocity: float = 3.14
    workspace_bounds: tuple[list[float], list[float]] = ([-0.8, -0.8, 0.0], [0.8, 0.8, 1.2])
    collision_check: bool = True
    force_limit: float | None = None
    tilt_limit: float | None = None
    human_proximity_stop: float | None = None


class SafetyMonitor:
    """Monitor safety constraints during execution."""
    
    def __init__(self, limits: SafetyLimits):
        self.limits = limits
        self.violation_count = 0
        self.max_violations = 3
    
    def check_pre_action(self, action: torch.Tensor, obs: dict) -> tuple[bool, str]:
        """Validate action before sending to robot."""
        # Check joint velocity limits
        if "joint_vel" in obs:
            joint_vel = np.array(obs["joint_vel"])
            if np.any(np.abs(joint_vel) > self.limits.max_joint_velocity):
                return False, f"Joint velocity limit exceeded: {np.max(np.abs(joint_vel)):.3f} > {self.limits.max_joint_velocity}"
        
        # Check action magnitude (if joint position commands)
        if np.any(np.abs(action.cpu().numpy()) > 2 * np.pi):
            return False, f"Action magnitude exceeds 2π"
        
        return True, ""
    
    def check_post_step(self, obs: dict, reward: float) -> tuple[bool, str]:
        """Validate state after step. Returns (safe, message)."""
        violations = []
        
        # Force/torque limit
        if "force_torque" in obs:
            ft = np.array(obs["force_torque"])
            force_mag = np.linalg.norm(ft[:3])
            if force_mag > self.limits.max_force:
                violations.append(f"Force limit: {force_mag:.1f} > {self.limits.max_force}")
            if self.limits.force_limit and force_mag > self.limits.force_limit:
                violations.append(f"Skill force limit: {force_mag:.1f} > {self.limits.force_limit}")
        
        # Workspace bounds
        if "eef_pos" in obs:
            eef = np.array(obs["eef_pos"])
            min_b, max_b = self.limits.workspace_bounds
            if np.any(eef < min_b) or np.any(eef > max_b):
                violations.append(f"Workspace bounds violated: {eef}")
        
        # Tilt limit (for pour/handover)
        if self.limits.tilt_limit and "eef_quat" in obs:
            # Simplified: check z-axis tilt
            quat = np.array(obs["eef_quat"])
            # Convert quat to euler, check roll/pitch
            # Simplified check
            pass
        
        # Human proximity
        if self.limits.human_proximity_stop and "human_hand_pos" in obs:
            human = np.array(obs["human_hand_pos"])
            eef = np.array(obs["eef_pos"])
            dist = np.linalg.norm(human - eef)
            if dist < self.limits.human_proximity_stop:
                violations.append(f"Human proximity: {dist:.3f} < {self.limits.human_proximity_stop}")
        
        if violations:
            self.violation_count += 1
            return False, "; ".join(violations)
        
        self.violation_count = 0
        return True, ""
    
    def emergency_stop(self) -> np.ndarray:
        """Generate emergency stop command (zero velocity / gravity comp)."""
        return np.zeros(9)  # 7 arm + 2 finger


class IsaacLabExecutor:
    """Manages Isaac Lab environment and policy execution."""
    
    def __init__(
        self,
        registry_path: str,
        skill_name: str,
        headless: bool = True,
        device: str = "cuda:0",
        render_interval: int = 0,
    ):
        self.registry_path = registry_path
        self.skill_name = skill_name
        self.headless = headless
        self.device = device
        self.render_interval = render_interval
        
        self.config: SkillConfig | None = None
        self.env = None
        self.policy = None
        self.action_translator = None
        self.obs_translator = None
        self.safety_monitor = None
        
        self._running = False
        self._thread: threading.Thread | None = None
        self._action_queue: queue.Queue = queue.Queue()
        self._obs_queue: queue.Queue = queue.Queue()
        self._result: ExecutionResult | None = None
    
    def load_skill(self) -> bool:
        """Load task environment and policy checkpoint."""
        try:
            # Load config from registry
            self.config = SkillConfig.from_registry(self.registry_path, self.skill_name)
            
            # Create translators
            self.action_translator, self.obs_translator = create_translators(
                self.registry_path, self.skill_name, self.device
            )
            
            # Create safety monitor
            limits = self.config.safety_limits
            self.safety_monitor = SafetyMonitor(SafetyLimits(
                max_force=limits.get("max_force", 50.0),
                max_velocity=limits.get("max_velocity", 1.5),
                max_joint_velocity=limits.get("max_joint_velocity", 3.14),
                workspace_bounds=(
                    limits.get("workspace_bounds", {}).get("min", [-0.8, -0.8, 0.0]),
                    limits.get("workspace_bounds", {}).get("max", [0.8, 0.8, 1.2]),
                ),
                collision_check=limits.get("collision_check", True),
                force_limit=limits.get("force_limit"),
                tilt_limit=limits.get("tilt_limit"),
                human_proximity_stop=limits.get("human_proximity_stop"),
            ))
            
            # Create Isaac Lab environment
            # Note: Requires Isaac Lab to be installed and task registered
            # env_cfg = {"headless": self.headless, "device": self.device}
            # self.env = gym.make(self.config.isaac_task, cfg=env_cfg)
            
            # Load policy
            # self.policy = torch.jit.load(self.config.policy_checkpoint).to(self.device)
            # self.policy.eval()
            
            logger.info(f"Loaded skill: {self.skill_name}")
            logger.info(f"  Task: {self.config.isaac_task}")
            logger.info(f"  Policy: {self.config.policy_checkpoint}")
            logger.info(f"  Action dim: {self.config.action_dim}")
            logger.info(f"  Obs keys: {self.config.obs_keys}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load skill {self.skill_name}: {e}")
            return False
    
    def step(self, action: torch.Tensor) -> tuple[dict, float, bool, bool, dict]:
        """Single environment step."""
        if self.env is None:
            raise RuntimeError("Environment not loaded. Call load_skill() first.")
        
        # Safety check pre-action
        safe, msg = self.safety_monitor.check_pre_action(action, {})
        if not safe:
            logger.warning(f"Pre-action safety violation: {msg}")
            # Could return emergency stop action
        
        # Step environment
        obs, reward, terminated, truncated, info = self.env.step(action)
        
        # Safety check post-step
        safe, msg = self.safety_monitor.check_post_step(obs, reward)
        if not safe:
            logger.warning(f"Post-step safety violation: {msg}")
            if self.safety_monitor.violation_count >= self.safety_monitor.max_violations:
                logger.error("Max safety violations reached, emergency stop")
                terminated = True
        
        return obs, reward, terminated, truncated, info
    
    def execute_skill(
        self,
        params: dict,
        max_steps: int = 500,
        record_trajectory: bool = False,
    ) -> ExecutionResult:
        """
        Execute skill to completion or failure.
        
        Args:
            params: Hermes skill parameters
            max_steps: Maximum steps before timeout
            record_trajectory: Whether to record full trajectory
            
        Returns:
            ExecutionResult with outcome
        """
        if self.env is None or self.policy is None:
            if not self.load_skill():
                return ExecutionResult(
                    success=False, steps=0, final_obs={}, total_reward=0.0,
                    error="Failed to load skill"
                )
        
        trajectory = [] if record_trajectory else None
        total_reward = 0.0
        steps = 0
        
        # Reset environment
        obs, _ = self.env.reset()
        
        # Main execution loop
        for step in range(max_steps):
            steps += 1
            
            # Translate Hermes params → policy action
            # Note: In practice, the policy observes goal via obs (e.g., target pos)
            action = self.action_translator.hermes_to_policy(params, obs)
            
            # Denormalize if needed
            action = self.action_translator.denormalize_action(action)
            
            # Step
            obs, reward, terminated, truncated, info = self.step(action)
            total_reward += reward
            
            # Translate observation for Hermes
            hermes_obs = self.obs_translator.isaac_to_hermes(
                obs, reward, terminated, truncated, info
            )
            
            if trajectory is not None:
                trajectory.append({
                    "step": step,
                    "action": action.cpu().numpy().tolist(),
                    "obs": hermes_obs,
                    "reward": reward,
                })
            
            # Render if configured
            if self.render_interval > 0 and step % self.render_interval == 0:
                self.env.render()
            
            if terminated or truncated:
                success = info.get("success", terminated and not truncated)
                break
        
        else:
            # Loop completed without break = timeout
            success = False
        
        final_obs = self.obs_translator.isaac_to_hermes(
            obs, reward, terminated, truncated, info
        )
        
        return ExecutionResult(
            success=success,
            steps=steps,
            final_obs=final_obs,
            total_reward=total_reward,
            error=None if success else "Timeout or failure",
            trajectory=trajectory,
        )
    
    def start_async(self, params: dict, max_steps: int = 500):
        """Start skill execution in background thread."""
        if self._running:
            raise RuntimeError("Already running")
        
        self._running = True
        self._result = None
        
        def _run():
            try:
                self._result = self.execute_skill(params, max_steps, record_trajectory=True)
            except Exception as e:
                self._result = ExecutionResult(
                    success=False, steps=0, final_obs={}, total_reward=0.0,
                    error=str(e)
                )
            finally:
                self._running = False
        
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
    
    def poll_async(self) -> ExecutionResult | None:
        """Check if async execution completed."""
        if self._thread and not self._thread.is_alive():
            self._thread.join(timeout=0.1)
            return self._result
        return None
    
    def stop_async(self):
        """Stop async execution (emergency stop)."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
    
    def close(self):
        """Cleanup environment and resources."""
        self.stop_async()
        if self.env:
            self.env.close()
            self.env = None
        self.policy = None
        logger.info("Executor closed")


class MultiSkillExecutor:
    """Manage multiple skills, switch between them."""
    
    def __init__(self, registry_path: str, device: str = "cuda:0", headless: bool = True):
        self.registry_path = registry_path
        self.device = device
        self.headless = headless
        self.executors: dict[str, IsaacLabExecutor] = {}
        self.current_skill: str | None = None
    
    def load_skill(self, skill_name: str) -> bool:
        """Load a skill executor."""
        if skill_name in self.executors:
            return True
        
        executor = IsaacLabExecutor(
            self.registry_path, skill_name,
            headless=self.headless, device=self.device
        )
        if executor.load_skill():
            self.executors[skill_name] = executor
            return True
        return False
    
    def execute(self, skill_name: str, params: dict, max_steps: int = 500) -> ExecutionResult:
        """Execute a skill (loads if needed)."""
        if skill_name not in self.executors:
            if not self.load_skill(skill_name):
                return ExecutionResult(
                    success=False, steps=0, final_obs={}, total_reward=0.0,
                    error=f"Failed to load skill: {skill_name}"
                )
        
        self.current_skill = skill_name
        return self.executors[skill_name].execute_skill(params, max_steps)
    
    def close_all(self):
        """Close all executors."""
        for ex in self.executors.values():
            ex.close()
        self.executors.clear()