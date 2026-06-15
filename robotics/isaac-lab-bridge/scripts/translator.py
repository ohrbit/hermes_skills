"""
Rosetta Translator: Hermes ↔ Isaac Lab bidirectional translation.

Handles conversion between Hermes skill parameters and Isaac Lab
observation/action tensors, including normalization, coordinate frames,
and policy-specific preprocessing.
"""

from __future__ import annotations

import numpy as np
import torch
from dataclasses import dataclass
from typing import Any
import yaml


@dataclass
class SkillConfig:
    """Skill configuration from registry."""
    name: str
    isaac_task: str
    policy_checkpoint: str
    policy_type: str
    obs_keys: list[str]
    action_space: str
    action_dim: int
    params: list[dict]
    safety_limits: dict
    
    @classmethod
    def from_registry(cls, registry_path: str, skill_name: str) -> "SkillConfig":
        with open(registry_path) as f:
            registry = yaml.safe_load(f)
        skill = registry["skills"][skill_name]
        return cls(
            name=skill_name,
            isaac_task=skill["isaac_task"],
            policy_checkpoint=skill["policy_checkpoint"],
            policy_type=skill.get("policy_type", "rsl_rl"),
            obs_keys=skill["obs_space"],
            action_space=skill["action_space"],
            action_dim=skill["action_dim"],
            params=skill.get("params", []),
            safety_limits=skill.get("safety_limits", {}),
        )


class ObservationNormalizer:
    """Normalize observations to policy expected range."""
    
    def __init__(self, obs_keys: list[str], stats_path: str | None = None):
        self.obs_keys = obs_keys
        self.stats = {}
        if stats_path:
            self.load(stats_path)
    
    def load(self, path: str):
        data = np.load(path)
        self.stats = {k: (data[f"{k}_mean"], data[f"{k}_std"]) for k in self.obs_keys}
    
    def save(self, path: str):
        save_dict = {}
        for k, (mean, std) in self.stats.items():
            save_dict[f"{k}_mean"] = mean
            save_dict[f"{k}_std"] = std
        np.savez(path, **save_dict)
    
    def fit(self, observations: list[dict]):
        """Compute mean/std from observation batch."""
        for k in self.obs_keys:
            vals = np.array([obs[k] for obs in observations])
            self.stats[k] = (vals.mean(axis=0), vals.std(axis=0) + 1e-8)
    
    def normalize(self, obs: dict) -> dict:
        """Apply normalization."""
        normed = {}
        for k in self.obs_keys:
            if k in obs:
                mean, std = self.stats.get(k, (0.0, 1.0))
                normed[k] = (obs[k] - mean) / std
            else:
                normed[k] = np.zeros_like(mean) if isinstance(mean, np.ndarray) else 0.0
        return normed
    
    def denormalize(self, obs: dict) -> dict:
        """Reverse normalization."""
        denormed = {}
        for k in self.obs_keys:
            if k in obs:
                mean, std = self.stats.get(k, (0.0, 1.0))
                denormed[k] = obs[k] * std + mean
        return denormed


class ActionTranslator:
    """Translate between Hermes params and policy actions."""
    
    def __init__(self, config: SkillConfig, device: str = "cuda:0"):
        self.config = config
        self.device = device
        self.action_scale = 1.0
        self.action_offset = 0.0
    
    def hermes_to_policy(self, params: dict, obs: dict) -> torch.Tensor:
        """
        Convert Hermes skill parameters → policy action tensor.
        
        This is skill-specific. Base implementation returns zero action;
        override per skill or implement IK/trajectory logic here.
        """
        # Default: policy acts autonomously, params only set goal state
        # Policy observes goal via observation (e.g., target_pos in obs)
        return torch.zeros(self.config.action_dim, device=self.device)
    
    def policy_to_hermes(self, action: torch.Tensor) -> dict:
        """Convert policy action → Hermes-readable format."""
        return {
            "joint_positions": action.cpu().numpy().tolist(),
            "action_space": self.config.action_space,
        }
    
    def set_action_bounds(self, scale: float | np.ndarray, offset: float | np.ndarray = 0.0):
        """Set action normalization (for policies outputting [-1, 1])."""
        self.action_scale = scale
        self.action_offset = offset
    
    def denormalize_action(self, action: torch.Tensor) -> torch.Tensor:
        """Convert policy output [-1,1] → joint commands."""
        return action * self.action_scale + self.action_offset


class ObservationTranslator:
    """Translate Isaac Lab observations → Hermes memory format."""
    
    def __init__(self, config: SkillConfig, device: str = "cuda:0"):
        self.config = config
        self.device = device
        self.normalizer = ObservationNormalizer(config.obs_keys)
    
    def isaac_to_hermes(self, obs: dict, reward: float, terminated: bool, truncated: bool, info: dict) -> dict:
        """
        Convert Isaac Lab step output → Hermes observation dict.
        
        Returns dict suitable for Hermes memory storage.
        """
        # Extract relevant observations
        hermes_obs = {}
        for k in self.config.obs_keys:
            if k in obs:
                val = obs[k]
                if isinstance(val, torch.Tensor):
                    val = val.detach().cpu().numpy()
                hermes_obs[k] = val.tolist() if isinstance(val, np.ndarray) else val
        
        # Add meta
        hermes_obs["_meta"] = {
            "reward": float(reward),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "success": info.get("success", False),
            "skill": self.config.name,
            "timestamp": info.get("timestamp", 0.0),
        }
        
        # Compute derived quantities
        hermes_obs["_derived"] = self._compute_derived(obs)
        
        return hermes_obs
    
    def _compute_derived(self, obs: dict) -> dict:
        """Compute task-relevant derived quantities."""
        derived = {}
        
        # End-effector to target distance
        if "eef_pos" in obs and "cube_pos" in obs:
            eef = np.array(obs["eef_pos"])
            cube = np.array(obs["cube_pos"])
            derived["eef_to_cube_dist"] = float(np.linalg.norm(eef - cube))
        
        # Gripper state
        if "joint_pos" in obs:
            joints = np.array(obs["joint_pos"])
            if len(joints) >= 9:  # 7 arm + 2 finger
                derived["gripper_width"] = float(joints[7] + joints[8])
        
        # Force/torque magnitude
        if "force_torque" in obs:
            ft = np.array(obs["force_torque"])
            derived["force_magnitude"] = float(np.linalg.norm(ft[:3]))
            derived["torque_magnitude"] = float(np.linalg.norm(ft[3:]))
        
        return derived
    
    def fit_normalizer(self, observations: list[dict]):
        """Fit normalizer on collected observations."""
        self.normalizer.fit(observations)
    
    def normalize_obs(self, obs: dict) -> dict:
        """Normalize observations for policy input."""
        return self.normalizer.normalize(obs)


def create_translators(registry_path: str, skill_name: str, device: str = "cuda:0") -> tuple[ActionTranslator, ObservationTranslator]:
    """Factory to create translator pair for a skill."""
    config = SkillConfig.from_registry(registry_path, skill_name)
    action_translator = ActionTranslator(config, device)
    obs_translator = ObservationTranslator(config, device)
    return action_translator, obs_translator