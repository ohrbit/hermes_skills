"""
Hermes-side Skill Executor: Wraps Isaac Lab execution for Hermes.

This module provides the Hermes skill interface that delegates
to Isaac Lab via the executor.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SkillResult:
    """Result returned to Hermes."""
    success: bool
    skill: str
    params: dict
    observations: dict
    total_reward: float
    steps: int
    error: str | None = None
    trajectory: list[dict] | None = None


class IsaacLabSkillExecutor:
    """
    Hermes skill that wraps Isaac Lab execution.
    
    Usage from Hermes:
        executor = IsaacLabSkillExecutor("skills/registry.yaml")
        result = await executor.execute("pick_place", {"target_position": [0.5, 0.0, 0.1]})
    """
    
    def __init__(
        self,
        registry_path: str,
        device: str = "cuda:0",
        headless: bool = True,
        memory_writer: Any = None,  # Hermes memory interface
    ):
        self.registry_path = registry_path
        self.device = device
        self.headless = headless
        self.memory_writer = memory_writer
        
        # Import here to avoid mandatory dependency
        from .executor import MultiSkillExecutor
        self.executor = MultiSkillExecutor(registry_path, device, headless)
    
    async def execute(
        self,
        skill_name: str,
        params: dict,
        max_steps: int = 500,
        stream_observations: bool = True,
    ) -> SkillResult:
        """
        Execute a skill asynchronously.
        
        Streams observations to Hermes memory if memory_writer provided.
        """
        logger.info(f"Executing skill: {skill_name} with params: {params}")
        
        # Load skill if needed
        if skill_name not in self.executor.executors:
            loaded = self.executor.load_skill(skill_name)
            if not loaded:
                return SkillResult(
                    success=False,
                    skill=skill_name,
                    params=params,
                    observations={},
                    total_reward=0.0,
                    steps=0,
                    error=f"Failed to load skill: {skill_name}",
                )
        
        # Run in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.executor.execute,
            skill_name, params, max_steps
        )
        
        # Build Hermes result
        skill_result = SkillResult(
            success=result.success,
            skill=skill_name,
            params=params,
            observations=result.final_obs,
            total_reward=result.total_reward,
            steps=result.steps,
            error=result.error if not result.success else None,
            trajectory=result.trajectory,
        )
        
        # Write to Hermes memory
        if self.memory_writer:
            await self._write_to_memory(skill_result)
        
        return skill_result
    
    async def _write_to_memory(self, result: SkillResult):
        """Write execution result to Hermes memory tiers."""
        if not self.memory_writer:
            return
        
        try:
            # Tier 1: Hot memory - current execution
            await self.memory_writer.write_hot({
                "type": "skill_execution",
                "skill": result.skill,
                "success": result.success,
                "steps": result.steps,
                "reward": result.total_reward,
                "timestamp": result.observations.get("_meta", {}).get("timestamp"),
            })
            
            # Tier 2: Vault - learned outcomes
            if result.success:
                await self.memory_writer.write_vault({
                    "type": "skill_outcome",
                    "skill": result.skill,
                    "params": result.params,
                    "outcome": "success",
                    "final_state": result.observations.get("_derived", {}),
                    "lesson": f"{result.skill} succeeded with params {result.params}",
                })
            else:
                await self.memory_writer.write_vault({
                    "type": "skill_outcome",
                    "skill": result.skill,
                    "params": result.params,
                    "outcome": "failure",
                    "error": result.error,
                    "lesson": f"{result.skill} failed with params {result.params}: {result.error}",
                })
            
            # Tier 3: Daily note - episode summary
            await self.memory_writer.write_daily({
                "type": "episode",
                "skill": result.skill,
                "success": result.success,
                "steps": result.steps,
                "reward": result.total_reward,
            })
            
        except Exception as e:
            logger.warning(f"Failed to write to Hermes memory: {e}")
    
    async def execute_sequence(self, skills: list[tuple[str, dict]]) -> list[SkillResult]:
        """Execute a sequence of skills (skill chaining)."""
        results = []
        for skill_name, params in skills:
            result = await self.execute(skill_name, params)
            results.append(result)
            if not result.success:
                logger.warning(f"Skill {skill_name} failed, stopping sequence")
                break
        return results
    
    def close(self):
        """Cleanup."""
        self.executor.close_all()


# Hermes skill registration (for hermes skill system)
ISAAC_LAB_SKILLS = {
    "isaac_lab_execute": {
        "description": "Execute an Isaac Lab skill",
        "params": {
            "skill_name": {"type": "string", "description": "Skill from registry"},
            "params": {"type": "object", "description": "Skill parameters"},
            "max_steps": {"type": "integer", "default": 500},
        },
        "handler": "execute_skill_handler",
    },
    "isaac_lab_sequence": {
        "description": "Execute a sequence of Isaac Lab skills",
        "params": {
            "skills": {"type": "array", "items": {
                "type": "object",
                "properties": {
                    "skill_name": {"type": "string"},
                    "params": {"type": "object"},
                },
                "required": ["skill_name"],
            }},
        },
        "handler": "execute_sequence_handler",
    },
    "isaac_lab_load": {
        "description": "Pre-load a skill",
        "params": {
            "skill_name": {"type": "string"},
        },
        "handler": "load_skill_handler",
    },
}


# Handler functions (to be connected to Hermes skill system)
_skill_executor: IsaacLabSkillExecutor | None = None


def init_isaac_lab_skills(registry_path: str, device: str = "cuda:0", headless: bool = True, memory_writer: Any = None):
    """Initialize the skill executor."""
    global _skill_executor
    _skill_executor = IsaacLabSkillExecutor(registry_path, device, headless, memory_writer)


async def execute_skill_handler(skill_name: str, params: dict, max_steps: int = 500) -> SkillResult:
    """Handler for isaac_lab_execute skill."""
    if _skill_executor is None:
        return SkillResult(
            success=False, skill=skill_name, params=params,
            observations={}, total_reward=0.0, steps=0,
            error="Skill executor not initialized"
        )
    return await _skill_executor.execute(skill_name, params, max_steps)


async def execute_sequence_handler(skills: list[dict]) -> list[SkillResult]:
    """Handler for isaac_lab_sequence skill."""
    if _skill_executor is None:
        return [SkillResult(
            success=False, skill="", params={},
            observations={}, total_reward=0.0, steps=0,
            error="Skill executor not initialized"
        )]
    skill_tuples = [(s["skill_name"], s.get("params", {})) for s in skills]
    return await _skill_executor.execute_sequence(skill_tuples)


async def load_skill_handler(skill_name: str) -> dict:
    """Handler for isaac_lab_load skill."""
    if _skill_executor is None:
        return {"success": False, "error": "Skill executor not initialized"}
    loaded = _skill_executor.executor.load_skill(skill_name)
    return {"success": loaded, "skill": skill_name}