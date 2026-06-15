#!/usr/bin/env python3
"""
Model Registry for Bayesian Reasoning Skill.

Declarative definitions of Bayesian networks, Markov networks, and influence diagrams.
"""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class ModelType(Enum):
    BAYESIAN = "bayesian"
    MARKOV = "markov"
    INFLUENCE_DIAGRAM = "influence_diagram"


class VariableType(Enum):
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"
    DECISION = "decision"
    UTILITY = "utility"
    CHANCE = "chance"


class InferenceAlgorithm(Enum):
    VARIABLE_ELIMINATION = "variable_elimination"
    BELIEF_PROPAGATION = "belief_propagation"
    JUNCTION_TREE = "junction_tree"
    MCMC = "mcmc"
    HMC = "hmc"
    VARIATIONAL = "variational"
    CAUSAL = "causal"
    AUTO = "auto"


@dataclass
class Variable:
    """Variable/node in a probabilistic graphical model."""
    name: str
    var_type: VariableType
    states: list[str] | None = None  # For discrete
    parents: list[str] = field(default_factory=list)
    description: str = ""
    
    # For continuous
    distribution: str | None = None  # gaussian, gamma, beta, etc.
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelConfig:
    """Complete model configuration."""
    name: str
    model_type: ModelType
    description: str
    variables: list[Variable]
    cpts_path: str | None = None  # For Bayesian networks
    factors: list[dict] | None = None  # For Markov networks
    utility_path: str | None = None  # For influence diagrams
    inference: InferenceAlgorithm = InferenceAlgorithm.AUTO
    meta: dict = field(default_factory=dict)


class ModelRegistry:
    """Load and manage model configurations."""
    
    def __init__(self, registry_path: str):
        self.registry_path = Path(registry_path)
        self.models: dict[str, ModelConfig] = {}
        self._load()
    
    def _load(self):
        """Load models from YAML registry."""
        with open(self.registry_path) as f:
            data = yaml.safe_load(f)
        
        for name, spec in data.get("models", {}).items():
            variables = []
            for v in spec.get("variables", []):
                var = Variable(
                    name=v["name"],
                    var_type=VariableType(v["type"]),
                    states=v.get("states"),
                    parents=v.get("parents", []),
                    description=v.get("description", ""),
                    distribution=v.get("distribution"),
                    params=v.get("params", {}),
                )
                variables.append(var)
            
            model = ModelConfig(
                name=name,
                model_type=ModelType(spec["type"]),
                description=spec.get("description", ""),
                variables=variables,
                cpts_path=spec.get("cpts"),
                factors=spec.get("factors"),
                utility_path=spec.get("utility"),
                inference=InferenceAlgorithm(spec.get("inference", "auto")),
                meta=spec.get("meta", {}),
            )
            self.models[name] = model
    
    def get(self, name: str) -> ModelConfig | None:
        return self.models.get(name)
    
    def list_models(self, model_type: ModelType | None = None) -> list[str]:
        if model_type:
            return [n for n, m in self.models.items() if m.model_type == model_type]
        return list(self.models.keys())
    
    def validate(self) -> list[str]:
        """Validate all models. Returns list of errors."""
        errors = []
        for name, model in self.models.items():
            # Check variable references
            var_names = {v.name for v in model.variables}
            for v in model.variables:
                for p in v.parents:
                    if p not in var_names:
                        errors.append(f"{name}: variable '{v.name}' references unknown parent '{p}'")
            
            # Check CPT path exists
            if model.cpts_path and not Path(model.cpts_path).exists():
                errors.append(f"{name}: CPT file not found: {model.cpts_path}")
            
            # Check utility path
            if model.utility_path and not Path(model.utility_path).exists():
                errors.append(f"{name}: utility file not found: {model.utility_path}")
        
        return errors


def create_registry_template(output_path: str):
    """Create a template registry file."""
    template = {
        "models": {
            "example_bayesian": {
                "type": "bayesian",
                "description": "Example: Predict skill outcome from context",
                "variables": [
                    {
                        "name": "context_difficulty",
                        "type": "discrete",
                        "states": ["easy", "medium", "hard"],
                        "parents": [],
                        "description": "Task difficulty level"
                    },
                    {
                        "name": "robot_capability",
                        "type": "discrete",
                        "states": ["low", "high"],
                        "parents": [],
                        "description": "Robot capability level"
                    },
                    {
                        "name": "execution_quality",
                        "type": "discrete",
                        "states": ["poor", "good", "excellent"],
                        "parents": ["context_difficulty", "robot_capability"],
                        "description": "Quality of execution"
                    },
                    {
                        "name": "success",
                        "type": "discrete",
                        "states": ["fail", "succeed"],
                        "parents": ["execution_quality"],
                        "description": "Whether skill succeeds"
                    }
                ],
                "cpts": "models/cpts/example_bayesian.csv",
                "inference": "variable_elimination"
            },
            "example_markov": {
                "type": "markov",
                "description": "Example: Sensor fusion for localization",
                "variables": [
                    {"name": "pose_x", "type": "continuous", "parents": []},
                    {"name": "pose_y", "type": "continuous", "parents": []},
                    {"name": "odom_x", "type": "continuous", "parents": []},
                    {"name": "odom_y", "type": "continuous", "parents": []},
                    {"name": "vision_x", "type": "continuous", "parents": []},
                    {"name": "vision_y", "type": "continuous", "parents": []}
                ],
                "factors": [
                    {
                        "variables": ["pose_x", "pose_y", "odom_x", "odom_y"],
                        "potential": "models/factors/odometry_factor.py"
                    },
                    {
                        "variables": ["pose_x", "pose_y", "vision_x", "vision_y"],
                        "potential": "models/factors/vision_factor.py"
                    }
                ],
                "inference": "belief_propagation"
            },
            "example_influence": {
                "type": "influence_diagram",
                "description": "Example: Skill selection under uncertainty",
                "variables": [
                    {"name": "task_context", "type": "discrete", "states": ["clean", "cluttered"], "parents": []},
                    {"name": "skill_choice", "type": "decision", "states": ["skill_a", "skill_b"], "parents": ["task_context"]},
                    {"name": "success", "type": "chance", "states": ["fail", "succeed"], "parents": ["skill_choice", "task_context"]},
                    {"name": "time_cost", "type": "continuous", "parents": ["skill_choice", "task_context"]},
                    {"name": "utility", "type": "utility", "parents": ["success", "time_cost"]}
                ],
                "cpts": "models/cpts/example_influence.csv",
                "utility": "models/utilities/example_utility.py"
            }
        }
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(template, f, sort_keys=False, default_flow_style=False)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        create_registry_template(sys.argv[1])
    else:
        print("Usage: python model_registry.py <output_path>")