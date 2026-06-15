#!/usr/bin/env python3
"""
Memory Hooks for Bayesian Reasoning Skill.

Auto-learn and update probabilistic models from Hermes memory tiers.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ..scripts.learner import ModelLearner, LearnedModel
from ..scripts.inference import InferenceEngine
from ..scripts.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


@dataclass
class LearningConfig:
    """Configuration for auto-learning."""
    min_samples: int = 50              # Minimum samples before learning
    retrain_interval: int = 100        # Retrain after N new samples
    max_models: int = 20               # Max models to maintain
    structure_method: str = "hc"       # hc, pc, ges
    score: str = "bic"                 # bic, bdeu
    param_method: str = "mle"          # mle, bayesian
    discretize_continuous: bool = True
    n_bins: int = 5
    output_dir: str = "models/learned"
    enabled: bool = True


@dataclass 
class ModelTracker:
    """Track learning progress for a model."""
    name: str
    target_variables: list[str]
    sample_count: int = 0
    last_retrain: datetime | None = None
    learned_model: LearnedModel | None = None
    data_buffer: list[dict] = field(default_factory=list)


class MemoryHookManager:
    """
    Manage auto-learning from Hermes memory.
    
    Hooks into:
    - Tier 1 (Hot): Live skill execution outcomes
    - Tier 2 (Vault): Historical skill outcomes, lessons
    - Tier 3 (Daily): Episode summaries, trends
    """
    
    def __init__(
        self,
        memory_provider: Any,  # Hermes memory interface
        inference_engine: InferenceEngine,
        config: LearningConfig | None = None,
    ):
        self.memory = memory_provider
        self.engine = inference_engine
        self.config = config or LearningConfig()
        
        self.learner = ModelLearner(
            structure_method=self.config.structure_method,
            score=self.config.score,
            param_method=self.config.param_method,
            discretize_continuous=self.config.discretize_continuous,
            n_bins=self.config.n_bins,
        )
        
        self.trackers: dict[str, ModelTracker] = {}
        self._initialized = False
    
    async def initialize(self):
        """Load existing learned models and register hooks."""
        await self._load_existing_models()
        self._initialized = True
        logger.info("Bayesian memory hooks initialized")
    
    async def _load_existing_models(self):
        """Load previously learned models from disk."""
        output_dir = Path(self.config.output_dir)
        if not output_dir.exists():
            return
        
        for model_dir in output_dir.iterdir():
            if model_dir.is_dir() and (model_dir / "model.bif").exists():
                try:
                    from pgmpy.readwrite import BIFReader
                    reader = BIFReader(str(model_dir / "model.bif"))
                    model = reader.get_model()
                    model.name = model_dir.name
                    
                    self.engine.networks[model_dir.name] = model
                    
                    # Create tracker
                    self.trackers[model_dir.name] = ModelTracker(
                        name=model_dir.name,
                        target_variables=list(model.nodes()),
                        learned_model=None,  # Metadata loaded separately
                    )
                    logger.info(f"Loaded learned model: {model_dir.name}")
                except Exception as e:
                    logger.warning(f"Failed to load {model_dir.name}: {e}")
    
    # ============================================================
    # Tier 1: Hot Memory - Live execution hook
    # ============================================================
    
    async def on_skill_started(self, skill_name: str, params: dict, context: dict):
        """Called when skill execution starts."""
        # Could track intent → action for causal learning
        pass
    
    async def on_skill_completed(self, skill_result: dict):
        """
        Called when skill completes. Record outcome for learning.
        
        Expected skill_result keys:
        - skill: skill name
        - success: bool
        - params: dict
        - observations: dict (from Isaac Lab bridge)
        - total_reward: float
        - steps: int
        """
        if not self.config.enabled:
            return
        
        skill = skill_result.get("skill")
        if not skill:
            return
        
        # Create training sample
        sample = self._extract_training_sample(skill_result)
        if sample:
            await self._buffer_sample(skill, sample)
    
    def _extract_training_sample(self, result: dict) -> dict | None:
        """Extract features + target from skill result."""
        obs = result.get("observations", {})
        derived = obs.get("_derived", {})
        meta = obs.get("_meta", {})
        
        # Build feature vector
        sample = {
            "skill": result.get("skill"),
            "success": result.get("success", False),
            "total_reward": result.get("total_reward", 0.0),
            "steps": result.get("steps", 0),
        }
        
        # Add context from params
        for k, v in result.get("params", {}).items():
            sample[f"param_{k}"] = v
        
        # Add derived observations (these are the meaningful features)
        for k, v in derived.items():
            if isinstance(v, (int, float)):
                sample[f"obs_{k}"] = v
        
        # Add meta
        for k, v in meta.items():
            if isinstance(v, (int, float, bool)):
                sample[f"meta_{k}"] = v
        
        # Only return if we have meaningful features
        feature_keys = [k for k in sample if k not in ["skill", "success"]]
        if len(feature_keys) >= 2:
            return sample
        return None
    
    async def _buffer_sample(self, skill: str, sample: dict):
        """Buffer sample and trigger retrain if threshold reached."""
        # Determine model name
        model_name = f"{skill}_outcome"
        
        if model_name not in self.trackers:
            self.trackers[model_name] = ModelTracker(
                name=model_name,
                target_variables=["success", "total_reward"],
            )
        
        tracker = self.trackers[model_name]
        tracker.data_buffer.append(sample)
        tracker.sample_count += 1
        
        # Check if we should retrain
        if tracker.sample_count >= self.config.min_samples:
            if (tracker.last_retrain is None or 
                tracker.sample_count - (tracker.learned_model.data_shape[0] if tracker.learned_model else 0) 
                >= self.config.retrain_interval):
                
                await self._retrain_model(model_name)
    
    async def _retrain_model(self, model_name: str):
        """Retrain model from buffered data."""
        tracker = self.trackers[model_name]
        
        if len(tracker.data_buffer) < self.config.min_samples:
            return
        
        logger.info(f"Retraining {model_name} with {len(tracker.data_buffer)} samples")
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(tracker.data_buffer)
            
            # Learn
            learned = self.learner.learn(df, target_variables=tracker.target_variables)
            
            # Save
            output_path = Path(self.config.output_dir) / model_name
            self.learner.save_model(learned, str(output_path))
            
            # Update engine
            from pgmpy.readwrite import BIFReader
            reader = BIFReader(str(output_path / "model.bif"))
            model = reader.get_model()
            model.name = model_name
            self.engine.networks[model_name] = model
            
            # Update tracker
            tracker.learned_model = learned
            tracker.last_retrain = datetime.now()
            tracker.data_buffer.clear()  # Clear buffer after successful retrain
            
            logger.info(f"Model {model_name} retrained successfully")
            
        except Exception as e:
            logger.error(f"Failed to retrain {model_name}: {e}")
    
    # ============================================================
    # Tier 2: Vault - Batch learning from historical data
    # ============================================================
    
    async def learn_from_vault(
        self,
        query: str = "SELECT * FROM skill_outcomes",
        target_variables: list[str] | None = None,
        model_name: str | None = None,
    ) -> LearnedModel | None:
        """
        Learn model from Hermes Vault (Tier 2) using SQL-like query.
        
        This requires the memory provider to support SQL queries.
        """
        if not self.config.enabled:
            return None
        
        try:
            # Execute query against memory
            results = await self.memory.query_vault(query)
            
            if not results:
                logger.warning("Vault query returned no results")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            if df.empty:
                return None
            
            # Learn
            model_name = model_name or "vault_learned_model"
            learned = self.learner.learn(df, target_variables=target_variables)
            
            # Save
            output_path = Path(self.config.output_dir) / model_name
            self.learner.save_model(learned, str(output_path))
            
            # Load into engine
            from pgmpy.readwrite import BIFReader
            reader = BIFReader(str(output_path / "model.bif"))
            model = reader.get_model()
            model.name = model_name
            self.engine.networks[model_name] = model
            
            # Track
            self.trackers[model_name] = ModelTracker(
                name=model_name,
                target_variables=target_variables or list(df.columns),
                sample_count=len(df),
                last_retrain=datetime.now(),
                learned_model=learned,
            )
            
            logger.info(f"Learned {model_name} from Vault: {len(df)} samples")
            return learned
            
        except Exception as e:
            logger.error(f"Vault learning failed: {e}")
            return None
    
    # ============================================================
    # Tier 3: Daily - Trend analysis
    # ============================================================
    
    async def analyze_daily_trends(self, days: int = 7) -> dict:
        """
        Analyze trends from daily notes (Tier 3).
        
        Returns trend analysis for model performance over time.
        """
        try:
            # Query daily notes for episodes
            notes = await self.memory.query_daily(
                f"type=episode AND days<={days}"
            )
            
            if not notes:
                return {"trends": {}, "message": "No episode data found"}
            
            df = pd.DataFrame(notes)
            
            # Aggregate by skill and day
            trends = {}
            for skill in df["skill"].unique():
                skill_df = df[df["skill"] == skill]
                daily = skill_df.groupby("date").agg(
                    success_rate=("success", "mean"),
                    avg_reward=("reward", "mean"),
                    avg_steps=("steps", "mean"),
                    count=("success", "count")
                ).reset_index()
                
                trends[skill] = {
                    "success_rate_trend": daily["success_rate"].tolist(),
                    "reward_trend": daily["avg_reward"].tolist(),
                    "steps_trend": daily["avg_steps"].tolist(),
                    "dates": daily["date"].tolist(),
                    "current_success_rate": daily["success_rate"].iloc[-1] if len(daily) > 0 else 0,
                }
            
            return {"trends": trends}
            
        except Exception as e:
            logger.error(f"Daily trend analysis failed: {e}")
            return {"error": str(e)}
    
    # ============================================================
    # Utility methods
    # ============================================================
    
    def get_model_status(self) -> dict:
        """Get status of all tracked models."""
        return {
            name: {
                "samples": tracker.sample_count,
                "last_retrain": tracker.last_retrain.isoformat() if tracker.last_retrain else None,
                "has_model": tracker.learned_model is not None,
                "targets": tracker.target_variables,
            }
            for name, tracker in self.trackers.items()
        }
    
    def enable_auto_learning(self, enabled: bool = True):
        """Enable/disable auto-learning."""
        self.config.enabled = enabled
        logger.info(f"Auto-learning {'enabled' if enabled else 'disabled'}")
    
    async def manual_retrain(self, model_name: str) -> bool:
        """Manually trigger retrain for a model."""
        if model_name not in self.trackers:
            return False
        await self._retrain_model(model_name)
        return True


# ============================================================
# Convenience function for Hermes integration
# ============================================================

async def setup_bayesian_memory_hooks(
    hermes_memory: Any,  # Hermes memory provider
    inference_engine: InferenceEngine,
    config: LearningConfig | None = None,
) -> MemoryHookManager:
    """
    Set up Bayesian memory hooks for Hermes.
    
    Usage in Hermes startup:
        from bayesian_reasoning.scripts.memory_hooks import setup_bayesian_memory_hooks
        hooks = await setup_bayesian_memory_hooks(
            hermes_memory=memory_provider,
            inference_engine=engine,
        )
    """
    hooks = MemoryHookManager(
        memory_provider=hermes_memory,
        inference_engine=inference_engine,
        config=config,
    )
    await hooks.initialize()
    return hooks


# Example of how to integrate with Hermes event system:
"""
# In Hermes core or skill executor:

async def on_skill_execution_complete(skill_result: SkillResult):
    # Existing memory writes...
    await memory.write_vault(...)
    await memory.write_daily(...)
    
    # NEW: Bayesian learning hook
    if bayesian_hooks:
        await bayesian_hooks.on_skill_completed({
            "skill": skill_result.skill,
            "success": skill_result.success,
            "params": skill_result.params,
            "observations": skill_result.observations,
            "total_reward": skill_result.total_reward,
            "steps": skill_result.steps,
        })
"""