#!/usr/bin/env python3
"""
Hermes Integration for Bayesian Reasoning Skill.

Provides Hermes skills for probabilistic queries, causal inference,
diagnosis, planning under uncertainty, and auto-learning from memory.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Import our engine
from ..scripts.inference import InferenceEngine, InferenceResult, Explanation
from ..scripts.learner import ModelLearner, LearnedModel
from ..scripts.model_registry import ModelRegistry, create_registry_template

logger = logging.getLogger(__name__)


@dataclass
class ProbabilisticPlan:
    """Plan with uncertainty quantification."""
    steps: list[dict]
    expected_utility: float
    success_probability: float
    risk_factors: dict[str, float]
    confidence_intervals: dict[str, tuple[float, float]]


# Global engine instance
_inference_engine: InferenceEngine | None = None
_model_learner: ModelLearner | None = None


def init_bayesian_skills(
    models_dir: str = "models",
    registry_path: str = "models/registry.yaml",
    structure_method: str = "hc",
    score: str = "bic",
) -> InferenceEngine:
    """Initialize the inference engine and load all models from registry."""
    global _inference_engine, _model_learner
    
    _inference_engine = InferenceEngine(models_dir)
    _model_learner = ModelLearner(structure_method=structure_method, score=score)
    
    # Load registry
    registry = ModelRegistry(registry_path)
    errors = registry.validate()
    if errors:
        for e in errors:
            logger.warning(f"Registry validation: {e}")
    
    # Load each model
    for name in registry.list_models():
        config = registry.get(name)
        if config:
            # Convert ModelConfig to dict for engine
            config_dict = {
                "type": config.model_type.value,
                "description": config.description,
                "variables": [
                    {
                        "name": v.name,
                        "type": v.var_type.value,
                        "states": v.states,
                        "parents": v.parents,
                        "distribution": v.distribution,
                        "params": v.params,
                    }
                    for v in config.variables
                ],
                "cpts": config.cpts_path,
                "factors": config.factors,
                "utility": config.utility_path,
                "inference": config.inference.value,
            }
            _inference_engine.load_model(name, config_dict)
    
    logger.info(f"Initialized Bayesian reasoning with {len(_inference_engine.networks)} models")
    return _inference_engine


def get_engine() -> InferenceEngine:
    """Get the global inference engine."""
    if _inference_engine is None:
        raise RuntimeError("Bayesian skills not initialized. Call init_bayesian_skills() first.")
    return _inference_engine


def get_learner() -> ModelLearner:
    """Get the global model learner."""
    if _model_learner is None:
        raise RuntimeError("Bayesian skills not initialized. Call init_bayesian_skills() first.")
    return _model_learner


# ============================================================
# Hermes Skill Handlers
# ============================================================

async def probability_query(
    model_name: str,
    variables: list[str],
    evidence: dict[str, Any] = None,
    algorithm: str = "auto"
) -> InferenceResult:
    """
    Skill: probabilistic_query
    
    Query posterior distribution P(variables | evidence).
    
    Example:
    > probability_query("pick_place_outcome", ["success"], 
        {"cube_weight": 0.5, "surface_friction": 0.3})
    """
    engine = get_engine()
    return engine.query(model_name, variables, evidence or {}, algorithm)


async def causal_query(
    model_name: str,
    intervention: dict[str, Any],
    targets: list[str],
    algorithm: str = "causal"
) -> InferenceResult:
    """
    Skill: causal_query
    
    Causal intervention query: P(targets | do(intervention)).
    
    Example:
    > causal_query("pick_place_outcome", {"grasp_stability": "high"}, ["success"])
    """
    engine = get_engine()
    return engine.intervene(model_name, intervention, targets, algorithm)


async def counterfactual_query(
    model_name: str,
    evidence: dict[str, Any],
    intervention: dict[str, Any],
    targets: list[str]
) -> InferenceResult:
    """
    Skill: counterfactual_query
    
    Counterfactual: P(targets | evidence, do(intervention)).
    
    Example:
    > counterfactual_query("robot_fault_diagnosis", 
        {"high_current": true}, {"encoder_drift": false}, ["joint_overheating"])
    """
    engine = get_engine()
    return engine.counterfactual(model_name, evidence, intervention, targets)


async def explain_prediction(
    model_name: str,
    evidence: dict[str, Any],
    target: str,
    algorithm: str = "causal"
) -> Explanation:
    """
    Skill: explain_prediction
    
    Generate explanation for a prediction with sensitivity & counterfactuals.
    
    Example:
    > explain_prediction("pick_place_outcome", 
        {"cube_weight": 0.8, "gripper_force": 20}, "success")
    """
    engine = get_engine()
    return engine.explain(model_name, evidence, target, algorithm)


async def diagnose(
    symptoms: dict[str, Any],
    domain: str = "robot",
    algorithm: str = "variable_elimination"
) -> InferenceResult:
    """
    Skill: diagnose
    
    Diagnostic inference: find root causes from observed symptoms.
    
    Example:
    > diagnose({"high_current": true, "position_error": true}, "robot")
    """
    engine = get_engine()
    model_name = f"{domain}_fault_diagnosis"
    # Query all non-evidence variables as potential causes
    all_vars = ["joint_overheating", "encoder_drift", "mechanical_wear", "sensor_noise"]
    query_vars = [v for v in all_vars if v not in symptoms]
    return engine.query(model_name, query_vars, symptoms, algorithm)


async def belief_update(
    observations: dict[str, Any],
    prior_model: str = "localization_belief",
    algorithm: str = "belief_propagation"
) -> InferenceResult:
    """
    Skill: belief_update
    
    Fuse multi-modal observations into posterior belief state.
    
    Example:
    > belief_update({"odom_x": 1.2, "odom_y": 0.5, "vision_x": 1.15, "vision_y": 0.48})
    """
    engine = get_engine()
    # Query pose variables
    query_vars = ["pose_x", "pose_y", "pose_theta"]
    return engine.query(prior_model, query_vars, observations, algorithm)


async def probabilistic_plan(
    goal: str,
    context: dict[str, Any],
    available_skills: list[str] = None,
    risk_threshold: float = 0.7
) -> ProbabilisticPlan:
    """
    Skill: probabilistic_plan
    
    Generate plan with uncertainty quantification using influence diagrams.
    
    Example:
    > probabilistic_plan("stack 3 blocks", {"workspace": "cluttered"})
    """
    engine = get_engine()
    
    # Load decision model
    model_name = "skill_selector"
    if model_name not in engine.networks:
        # Fallback: simple utility-based selection
        return await _fallback_plan(goal, context, available_skills, risk_threshold)
    
    # For each skill, query expected utility
    skill_utils = {}
    context_var = context.get("workspace", "clean")
    
    for skill in (available_skills or ["pick_place", "push_grasp", "suction_grasp"]):
        result = engine.query(
            model_name,
            ["utility", "success", "time_cost"],
            {"task_context": context_var, "skill_choice": skill},
            "variable_elimination"
        )
        
        utility_dist = result.marginal("utility")
        success_prob = result.marginal("success").get("succeed", 0)
        expected_utility = sum(s * p for s, p in zip(utility_dist.keys(), utility_dist.values()))
        
        skill_utils[skill] = {
            "expected_utility": expected_utility,
            "success_prob": success_prob,
            "distribution": utility_dist,
            "result": result
        }
    
    # Select best skill above risk threshold
    viable = {k: v for k, v in skill_utils.items() if v["success_prob"] >= risk_threshold}
    if not viable:
        viable = skill_utils  # Relax threshold
    
    best_skill = max(viable, key=lambda k: viable[k]["expected_utility"])
    best = viable[best_skill]
    
    return ProbabilisticPlan(
        steps=[{"skill": best_skill, "context": context, "params": {}}],
        expected_utility=best["expected_utility"],
        success_probability=best["success_prob"],
        risk_factors={k: 1-v["success_prob"] for k, v in skill_utils.items()},
        confidence_intervals={}
    )


async def _fallback_plan(goal: str, context: dict, skills: list[str], threshold: float) -> ProbabilisticPlan:
    """Fallback planner when no decision model available."""
    return ProbabilisticPlan(
        steps=[{"skill": skills[0] if skills else "pick_place", "context": context}],
        expected_utility=0.5,
        success_probability=0.5,
        risk_factors={s: 0.5 for s in (skills or ["pick_place"])},
        confidence_intervals={}
    )


async def learn_model(
    data_source: str,
    target_variables: list[str] = None,
    method: str = "hc",
    score: str = "bic",
    output_dir: str = "models/learned"
) -> LearnedModel:
    """
    Skill: learn_model
    
    Learn probabilistic model from data.
    
    Data sources:
    - "vault:skill_outcomes" - Learn from Hermes Vault Tier 2
    - "file:path/to/data.csv" - Learn from CSV file
    - "memory:recent_executions" - Learn from recent skill executions
    
    Example:
    > learn_model("vault:skill_outcomes", ["success", "grasp_stability"], "hc", "bic")
    """
    learner = get_learner()
    
    if data_source.startswith("file:"):
        path = data_source[5:]
        data = pd.read_csv(path)
        return learner.learn(data, target_variables=target_variables, 
                            method=method, score=score)
    
    elif data_source.startswith("vault:"):
        # Requires Hermes memory integration
        return await _learn_from_vault(data_source[6:], target_variables, method, score)
    
    elif data_source.startswith("memory:"):
        return await _learn_from_memory(data_source[7:], target_variables, method, score)
    
    else:
        raise ValueError(f"Unknown data source: {data_source}")


async def _learn_from_vault(
    query: str,
    target_variables: list[str] = None,
    method: str = "hc",
    score: str = "bic"
) -> LearnedModel:
    """Learn from Hermes Vault (Tier 2)."""
    # This requires Hermes memory provider - placeholder
    logger.warning("Vault learning requires Hermes memory integration")
    raise NotImplementedError("Implement in hermes/memory_hooks.py")


async def _learn_from_memory(
    query: str,
    target_variables: list[str] = None,
    method: str = "hc",
    score: str = "bic"
) -> LearnedModel:
    """Learn from recent executions (Tier 1)."""
    logger.warning("Memory learning requires Hermes memory integration")
    raise NotImplementedError("Implement in hermes/memory_hooks.py")


async def create_registry(output_path: str = "models/registry.yaml"):
    """Skill: create_registry - Generate template registry file."""
    create_registry_template(output_path)
    return {"created": output_path, "status": "template_generated"}


async def list_models(model_type: str = None) -> list[dict]:
    """Skill: list_bayesian_models - List available models."""
    engine = get_engine()
    models = []
    for name, config in engine._model_configs.items():
        if model_type is None or config.get("type") == model_type:
            models.append({
                "name": name,
                "type": config.get("type"),
                "description": config.get("description"),
                "variables": [v["name"] for v in config.get("variables", [])],
            })
    return models


async def validate_models() -> list[str]:
    """Skill: validate_bayesian_models - Validate all loaded models."""
    engine = get_engine()
    errors = []
    for name, model in engine.networks.items():
        try:
            if hasattr(model, 'check_model'):
                if not model.check_model():
                    errors.append(f"{name}: model validation failed")
        except Exception as e:
            errors.append(f"{name}: {e}")
    return errors


# ============================================================
# Skill Registration for Hermes
# ============================================================

BAYESIAN_SKILLS = {
    "probabilistic_query": {
        "description": "Query posterior probability P(variables | evidence)",
        "params": {
            "model_name": {"type": "string", "description": "Model from registry"},
            "variables": {"type": "array", "items": {"type": "string"}},
            "evidence": {"type": "object", "default": {}},
            "algorithm": {"type": "string", "default": "auto"},
        },
        "handler": "probability_query",
    },
    "causal_query": {
        "description": "Causal intervention query P(targets | do(intervention))",
        "params": {
            "model_name": {"type": "string"},
            "intervention": {"type": "object"},
            "targets": {"type": "array", "items": {"type": "string"}},
            "algorithm": {"type": "string", "default": "causal"},
        },
        "handler": "causal_query",
    },
    "counterfactual_query": {
        "description": "Counterfactual query P(targets | evidence, do(intervention))",
        "params": {
            "model_name": {"type": "string"},
            "evidence": {"type": "object"},
            "intervention": {"type": "object"},
            "targets": {"type": "array", "items": {"type": "string"}},
        },
        "handler": "counterfactual_query",
    },
    "explain_prediction": {
        "description": "Explain a prediction with sensitivity & counterfactuals",
        "params": {
            "model_name": {"type": "string"},
            "evidence": {"type": "object"},
            "target": {"type": "string"},
            "algorithm": {"type": "string", "default": "causal"},
        },
        "handler": "explain_prediction",
    },
    "diagnose": {
        "description": "Diagnostic inference: find root causes from symptoms",
        "params": {
            "symptoms": {"type": "object"},
            "domain": {"type": "string", "default": "robot"},
            "algorithm": {"type": "string", "default": "variable_elimination"},
        },
        "handler": "diagnose",
    },
    "belief_update": {
        "description": "Fuse observations into posterior belief",
        "params": {
            "observations": {"type": "object"},
            "prior_model": {"type": "string", "default": "localization_belief"},
            "algorithm": {"type": "string", "default": "belief_propagation"},
        },
        "handler": "belief_update",
    },
    "probabilistic_plan": {
        "description": "Generate plan with uncertainty quantification",
        "params": {
            "goal": {"type": "string"},
            "context": {"type": "object"},
            "available_skills": {"type": "array", "items": {"type": "string"}},
            "risk_threshold": {"type": "number", "default": 0.7},
        },
        "handler": "probabilistic_plan",
    },
    "learn_model": {
        "description": "Learn probabilistic model from data",
        "params": {
            "data_source": {"type": "string"},
            "target_variables": {"type": "array", "items": {"type": "string"}},
            "method": {"type": "string", "default": "hc"},
            "score": {"type": "string", "default": "bic"},
            "output_dir": {"type": "string", "default": "models/learned"},
        },
        "handler": "learn_model",
    },
    "list_bayesian_models": {
        "description": "List available Bayesian/Markov models",
        "params": {
            "model_type": {"type": "string"},
        },
        "handler": "list_models",
    },
    "validate_bayesian_models": {
        "description": "Validate all loaded models",
        "params": {},
        "handler": "validate_models",
    },
    "create_bayesian_registry": {
        "description": "Create template registry file",
        "params": {
            "output_path": {"type": "string", "default": "models/registry.yaml"},
        },
        "handler": "create_registry",
    },
}


# Handler wrappers for Hermes skill system
async def execute_skill_handler(skill_name: str, **params) -> Any:
    """Dispatch to appropriate handler."""
    handler_map = {
        "probabilistic_query": probability_query,
        "causal_query": causal_query,
        "counterfactual_query": counterfactual_query,
        "explain_prediction": explain_prediction,
        "diagnose": diagnose,
        "belief_update": belief_update,
        "probabilistic_plan": probabilistic_plan,
        "learn_model": learn_model,
        "list_bayesian_models": list_models,
        "validate_bayesian_models": validate_models,
        "create_bayesian_registry": create_registry,
    }
    
    if skill_name not in handler_map:
        return {"success": False, "error": f"Unknown skill: {skill_name}"}
    
    try:
        result = await handler_map[skill_name](**params)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Skill {skill_name} failed: {e}")
        return {"success": False, "error": str(e)}


def register_bayesian_skills(hermes_skill_registry):
    """Register all Bayesian skills with Hermes."""
    for name, spec in BAYESIAN_SKILLS.items():
        hermes_skill_registry.register(
            name=name,
            description=spec["description"],
            params=spec["params"],
            handler=lambda sn=name, **p: asyncio.run(execute_skill_handler(sn, **p))
        )