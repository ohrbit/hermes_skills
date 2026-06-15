#!/usr/bin/env python3
"""
Learn Bayesian Models from Hermes Vault (Tier 2 Memory).

CLI tool to extract training data from memory and learn probabilistic models.
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.learner import ModelLearner, LearnedModel
from scripts.model_registry import create_registry_template

logger = logging.getLogger(__name__)


async def learn_from_vault(
    vault_query: str = "SELECT * FROM skill_outcomes",
    target_variables: list[str] = None,
    skill_filter: str = None,
    method: str = "hc",
    score: str = "bic",
    param_method: str = "mle",
    discretize: bool = True,
    n_bins: int = 5,
    output_dir: str = "models/learned",
    min_samples: int = 50,
) -> LearnedModel | None:
    """
    Learn model from Hermes Vault data.
    
    This is a placeholder that simulates Vault query.
    Actual implementation needs Hermes memory provider integration.
    """
    
    print(f"Querying Vault: {vault_query}")
    
    # In real implementation, this would call Hermes memory provider:
    # results = await hermes_memory.query_vault(vault_query)
    
    # For now, generate synthetic data for testing
    print("Generating synthetic training data...")
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    n = 2000
    
    if skill_filter:
        print(f"Filtering for skill: {skill_filter}")
        # Skill-specific synthetic data
        if skill_filter == "pick_place":
            data = pd.DataFrame({
                "cube_weight": np.random.gamma(2, 0.5, n),
                "surface_friction": np.random.beta(2, 5, n),
                "gripper_force": np.random.normal(30, 5, n),
                "grasp_stability": np.random.choice(["low", "medium", "high"], n, p=[0.2, 0.5, 0.3]),
                "success": np.random.choice(["fail", "succeed"], n, p=[0.15, 0.85]),
            })
            # Add correlation
            data.loc[data["grasp_stability"] == "low", "success"] = np.random.choice(
                ["fail", "succeed"], sum(data["grasp_stability"] == "low"), p=[0.7, 0.3]
            )
            data.loc[data["grasp_stability"] == "high", "success"] = np.random.choice(
                ["fail", "succeed"], sum(data["grasp_stability"] == "high"), p=[0.02, 0.98]
            )
        elif skill_filter == "robot_diagnosis":
            data = pd.DataFrame({
                "joint_overheating": np.random.choice([False, True], n, p=[0.95, 0.05]),
                "encoder_drift": np.random.choice([False, True], n, p=[0.98, 0.02]),
                "mechanical_wear": np.random.choice([False, True], n, p=[0.9, 0.1]),
            })
            # Symptoms
            data["high_current"] = (
                (data["joint_overheating"] | data["mechanical_wear"]) & 
                np.random.choice([False, True], n, p=[0.3, 0.7])
            ) | (~(data["joint_overheating"] | data["mechanical_wear"]) & 
                np.random.choice([False, True], n, p=[0.99, 0.01]))
            data["position_error"] = (
                (data["encoder_drift"] | data["mechanical_wear"]) & 
                np.random.choice([False, True], n, p=[0.4, 0.6])
            ) | (~(data["encoder_drift"] | data["mechanical_wear"]) & 
                np.random.choice([False, True], n, p=[0.99, 0.01]))
            data["thermal_shutdown"] = data["joint_overheating"] & np.random.choice([False, True], n, p=[0.7, 0.3])
            data["tracking_loss"] = data["encoder_drift"] & np.random.choice([False, True], n, p=[0.6, 0.4])
        else:
            data = pd.DataFrame({
                "context": np.random.choice(["clean", "cluttered", "dynamic"], n),
                "skill": np.random.choice(["pick_place", "push_grasp", "suction"], n),
                "success": np.random.choice([False, True], n),
                "time_cost": np.random.exponential(10, n),
                "collision_risk": np.random.beta(1, 10, n),
            })
    else:
        # Generic skill outcomes
        data = pd.DataFrame({
            "skill": np.random.choice(["pick_place", "pour", "handover", "insert"], n),
            "context": np.random.choice(["clean", "cluttered", "dynamic"], n),
            "success": np.random.choice([False, True], n, p=[0.2, 0.8]),
            "total_reward": np.random.normal(100, 30, n),
            "steps": np.random.poisson(100, n),
            "gripper_force": np.random.normal(30, 5, n),
            "approach_speed": np.random.uniform(0.05, 0.2, n),
        })
    
    print(f"Generated {len(data)} samples with columns: {list(data.columns)}")
    
    if len(data) < min_samples:
        print(f"Warning: Only {len(data)} samples, minimum is {min_samples}")
        return None
    
    # Learn model
    print(f"Learning model with method={method}, score={score}...")
    
    learner = ModelLearner(
        structure_method=method,
        score=score,
        param_method=param_method,
        discretize_continuous=discretize,
        n_bins=n_bins,
    )
    
    learned = learner.learn(data, target_variables=target_variables)
    
    # Save
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Determine model name
    model_name = skill_filter or "vault_model"
    if target_variables:
        model_name += "_" + "_".join(target_variables)
    
    model_dir = output_path / model_name
    learner.save_model(learned, str(model_dir))
    
    # Print summary
    print(f"\n=== Model Learned: {model_name} ===")
    print(f"Samples: {learned.data_shape[0]}")
    print(f"Variables: {learned.variables}")
    print(f"Structure score ({score}): {learned.structure_score:.2f}")
    print(f"Method: {learned.method}")
    print(f"Edges: {learned.model.edges() if hasattr(learned.model, 'edges') else 'N/A'}")
    print(f"Saved to: {model_dir}")
    
    return learned


async def learn_from_csv(
    csv_path: str,
    target_variables: list[str] = None,
    method: str = "hc",
    score: str = "bic",
    param_method: str = "mle",
    discretize: bool = True,
    n_bins: int = 5,
    output_dir: str = "models/learned",
) -> LearnedModel | None:
    """Learn model from CSV file."""
    
    import pandas as pd
    
    print(f"Loading data from {csv_path}")
    data = pd.read_csv(csv_path)
    print(f"Loaded {len(data)} samples, {len(data.columns)} columns")
    
    learner = ModelLearner(
        structure_method=method,
        score=score,
        param_method=param_method,
        discretize_continuous=discretize,
        n_bins=n_bins,
    )
    
    learned = learner.learn(data, target_variables=target_variables)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    model_name = Path(csv_path).stem
    model_dir = output_path / model_name
    learner.save_model(learned, str(model_dir))
    
    print(f"\n=== Model Learned: {model_name} ===")
    print(f"Samples: {learned.data_shape[0]}")
    print(f"Variables: {learned.variables}")
    print(f"Structure score: {learned.structure_score:.2f}")
    print(f"Saved to: {model_dir}")
    
    return learned


def create_template_registry(output: str = "models/registry.yaml"):
    """Create template registry file."""
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    create_registry_template(output)
    print(f"Template registry created at {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Learn probabilistic models from Hermes Vault or CSV data"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # vault command
    vault_parser = subparsers.add_parser("vault", help="Learn from Hermes Vault")
    vault_parser.add_argument("--query", default="SELECT * FROM skill_outcomes")
    vault_parser.add_argument("--target", nargs="+", help="Target variables")
    vault_parser.add_argument("--skill", help="Filter by skill name")
    vault_parser.add_argument("--method", default="hc", choices=["hc", "pc", "ges"])
    vault_parser.add_argument("--score", default="bic", choices=["bic", "bdeu"])
    vault_parser.add_argument("--param", default="mle", choices=["mle", "bayesian"])
    vault_parser.add_argument("--no-discretize", action="store_true")
    vault_parser.add_argument("--bins", type=int, default=5)
    vault_parser.add_argument("--output", default="models/learned")
    vault_parser.add_argument("--min-samples", type=int, default=50)
    
    # csv command
    csv_parser = subparsers.add_parser("csv", help="Learn from CSV file")
    csv_parser.add_argument("csv_path", help="Path to CSV file")
    csv_parser.add_argument("--target", nargs="+", help="Target variables")
    csv_parser.add_argument("--method", default="hc", choices=["hc", "pc", "ges"])
    csv_parser.add_argument("--score", default="bic", choices=["bic", "bdeu"])
    csv_parser.add_argument("--param", default="mle", choices=["mle", "bayesian"])
    csv_parser.add_argument("--no-discretize", action="store_true")
    csv_parser.add_argument("--bins", type=int, default=5)
    csv_parser.add_argument("--output", default="models/learned")
    
    # registry command
    reg_parser = subparsers.add_parser("registry", help="Create template registry")
    reg_parser.add_argument("--output", default="models/registry.yaml")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    if args.command == "vault":
        asyncio.run(learn_from_vault(
            vault_query=args.query,
            target_variables=args.target,
            skill_filter=args.skill,
            method=args.method,
            score=args.score,
            param_method=args.param,
            discretize=not args.no_discretize,
            n_bins=args.bins,
            output_dir=args.output,
            min_samples=args.min_samples,
        ))
    elif args.command == "csv":
        asyncio.run(learn_from_csv(
            csv_path=args.csv_path,
            target_variables=args.target,
            method=args.method,
            score=args.score,
            param_method=args.param,
            discretize=not args.no_discretize,
            n_bins=args.bins,
            output_dir=args.output,
        ))
    elif args.command == "registry":
        create_template_registry(args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()