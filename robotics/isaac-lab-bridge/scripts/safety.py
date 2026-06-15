"""
Safety monitoring and emergency stop for Isaac Lab execution.
"""

from __future__ import annotations

import logging
import numpy as np
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


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
    max_violations: int = 3


@dataclass
class SafetyViolation:
    """Record of a safety violation."""
    timestamp: float
    violation_type: str
    message: str
    severity: str  # "warning", "critical", "emergency"
    obs_snapshot: dict


class SafetyMonitor:
    """Monitor safety constraints during robot execution."""
    
    def __init__(self, limits: SafetyLimits):
        self.limits = limits
        self.violations: list[SafetyViolation] = []
        self.violation_count = 0
    
    def check_pre_action(self, action: np.ndarray, obs: dict) -> tuple[bool, str]:
        """Validate action before sending to robot. Returns (safe, message)."""
        violations = []
        
        # Check joint velocity limits from observation
        if "joint_vel" in obs:
            joint_vel = np.array(obs["joint_vel"])
            max_vel = np.max(np.abs(joint_vel))
            if max_vel > self.limits.max_joint_velocity:
                violations.append(
                    f"Joint velocity limit exceeded: {max_vel:.3f} > {self.limits.max_joint_velocity}"
                )
        
        # Check action magnitude (if joint position commands)
        if np.any(np.abs(action) > 4 * np.pi):  # Allow some margin
            violations.append(f"Action magnitude exceeds 4π")
        
        # Check workspace bounds for target (if action contains target pos)
        if action.shape[-1] >= 3:
            target_pos = action[:3]
            min_b, max_b = self.limits.workspace_bounds
            if np.any(target_pos < min_b) or np.any(target_pos > max_b):
                violations.append(f"Target position outside workspace: {target_pos}")
        
        if violations:
            return False, "; ".join(violations)
        
        return True, ""
    
    def check_post_step(self, obs: dict, reward: float, step: int) -> tuple[bool, str]:
        """Validate state after step. Returns (safe, message)."""
        violations = []
        
        # Force/torque limit
        if "force_torque" in obs:
            ft = np.array(obs["force_torque"])
            force_mag = float(np.linalg.norm(ft[:3]))
            torque_mag = float(np.linalg.norm(ft[3:]))
            
            if force_mag > self.limits.max_force:
                violations.append(f"Force limit: {force_mag:.1f} > {self.limits.max_force}")
            if self.limits.force_limit and force_mag > self.limits.force_limit:
                violations.append(f"Skill force limit: {force_mag:.1f} > {self.limits.force_limit}")
            if torque_mag > 10.0:  # Hard torque limit
                violations.append(f"Torque limit: {torque_mag:.1f} > 10.0")
        
        # Workspace bounds
        if "eef_pos" in obs:
            eef = np.array(obs["eef_pos"])
            min_b, max_b = self.limits.workspace_bounds
            if np.any(eef < np.array(min_b) - 0.05) or np.any(eef > np.array(max_b) + 0.05):
                violations.append(f"Workspace bounds violated: {eef}")
        
        # Tilt limit (for pour/handover) - check end-effector orientation
        if self.limits.tilt_limit and "eef_quat" in obs:
            quat = np.array(obs["eef_quat"])
            # Convert quaternion to euler angles (ZYX)
            # Simplified: check if z-axis is tilted too far from vertical
            # quat = [w, x, y, z] or [x, y, z, w] - check convention
            # Assuming [x, y, z, w] Isaac Lab convention
            if len(quat) == 4:
                x, y, z, w = quat
                # Pitch angle from quaternion
                pitch = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x**2 + y**2))
                roll = np.arctan2(2 * (w * y + z * x), 1 - 2 * (y**2 + z**2))
                tilt = np.sqrt(pitch**2 + roll**2)
                if tilt > self.limits.tilt_limit:
                    violations.append(f"Tilt limit: {tilt:.3f} > {self.limits.tilt_limit:.3f}")
        
        # Human proximity (for collaborative tasks)
        if self.limits.human_proximity_stop and "human_hand_pos" in obs:
            human = np.array(obs["human_hand_pos"])
            if "eef_pos" in obs:
                eef = np.array(obs["eef_pos"])
                dist = float(np.linalg.norm(human - eef))
                if dist < self.limits.human_proximity_stop:
                    violations.append(f"Human proximity: {dist:.3f} < {self.limits.human_proximity_stop}")
        
        # Joint position limits (prevent self-collision)
        if "joint_pos" in obs:
            joints = np.array(obs["joint_pos"])
            # Franka joint limits (approximate)
            joint_limits = np.array([
                [-2.8973, 2.8973],
                [-1.7628, 1.7628],
                [-2.8973, 2.8973],
                [-3.0718, -0.0698],
                [-2.8973, 2.8973],
                [-0.0175, 3.7525],
                [-2.8973, 2.8973],
            ])
            if len(joints) >= 7:
                for i, (lo, hi) in enumerate(joint_limits):
                    if joints[i] < lo - 0.1 or joints[i] > hi + 0.1:
                        violations.append(f"Joint {i} limit: {joints[i]:.3f} not in [{lo:.3f}, {hi:.3f}]")
        
        if violations:
            self.violation_count += 1
            msg = "; ".join(violations)
            logger.warning(f"Safety violation [{self.violation_count}/{self.limits.max_violations}]: {msg}")
            return False, msg
        
        self.violation_count = 0
        return True, ""
    
    def emergency_stop(self, action_dim: int = 9) -> np.ndarray:
        """Generate emergency stop command (zero velocity / gravity compensation pose)."""
        # Return zero action - let low-level controller handle gravity compensation
        # Or return a safe "home" position
        return np.zeros(action_dim)
    
    def get_violation_summary(self) -> dict:
        """Get summary of violations."""
        return {
            "total": len(self.violations),
            "by_type": {},
            "recent": [vars(v) for v in self.violations[-5:]],
        }
    
    def reset(self):
        """Reset violation counter."""
        self.violation_count = 0
        self.violations.clear()


class SimToRealSafetyAdapter:
    """Adapt sim safety limits for real robot deployment."""
    
    # Real robot typically needs stricter limits
    REAL_WORLD_FACTORS = {
        "max_force": 0.5,        # 50% of sim
        "max_velocity": 0.5,     # 50% of sim
        "max_joint_velocity": 0.7,
        "force_limit": 0.5,
        "human_proximity_stop": 1.5,  # Larger safety distance
    }
    
    @classmethod
    def adapt_for_real(cls, sim_limits: SafetyLimits) -> SafetyLimits:
        """Create real-world safety limits from sim limits."""
        return SafetyLimits(
            max_force=sim_limits.max_force * cls.REAL_WORLD_FACTORS["max_force"],
            max_velocity=sim_limits.max_velocity * cls.REAL_WORLD_FACTORS["max_velocity"],
            max_joint_velocity=sim_limits.max_joint_velocity * cls.REAL_WORLD_FACTORS["max_joint_velocity"],
            workspace_bounds=sim_limits.workspace_bounds,  # Same workspace
            collision_check=True,
            force_limit=sim_limits.force_limit * cls.REAL_WORLD_FACTORS["force_limit"] if sim_limits.force_limit else None,
            tilt_limit=sim_limits.tilt_limit,
            human_proximity_stop=cls.REAL_WORLD_FACTORS["human_proximity_stop"],
            max_violations=1,  # Zero tolerance on real robot
        )
    
    @classmethod
    def add_real_world_checks(cls, monitor: SafetyMonitor):
        """Add real-world specific checks to monitor."""
        # Could add: temperature, current, communication latency, etc.
        pass