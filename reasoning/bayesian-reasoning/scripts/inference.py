#!/usr/bin/env python3
"""
Inference Engine for Bayesian Reasoning Skill.

Unified interface for all inference algorithms on Bayesian networks,
Markov networks, and influence diagrams.
"""

from __future__ import annotations

import logging
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

# Optional imports with helpful errors
try:
    from pgmpy.inference import VariableElimination, BeliefPropagation
    from pgmpy.inference.continuous import ContinuousVariableElimination
    from pgmpy.models import BayesianNetwork, MarkovNetwork
    from pgmpy.factors.discrete import TabularCPD
    from pgmpy.readwrite import BIFReader
    PGMPY_AVAILABLE = True
except ImportError:
    PGMPY_AVAILABLE = False
    BayesianNetwork = MarkovNetwork = TabularCPD = VariableElimination = BeliefPropagation = object

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

logger = logging.getLogger(__name__)


@dataclass
class InferenceResult:
    """Result of a probabilistic inference query."""
    model_name: str
    query_variables: list[str]
    evidence: dict[str, Any]
    marginals: dict[str, np.ndarray]  # variable -> probability array
    state_names: dict[str, list[str]]  # variable -> state labels
    log_likelihood: float | None = None
    algorithm: str = ""
    converged: bool = True
    metadata: dict = field(default_factory=dict)
    
    def marginal(self, variable: str) -> dict[str, float]:
        """Get marginal distribution as {state: probability}."""
        if variable not in self.marginals:
            raise KeyError(f"Variable '{variable}' not in result")
        probs = self.marginals[variable]
        states = self.state_names.get(variable, [str(i) for i in range(len(probs))])
        return dict(zip(states, probs.tolist()))
    
    def map(self, variable: str) -> tuple[str, float]:
        """Get MAP (most probable) state and its probability."""
        dist = self.marginal(variable)
        best_state = max(dist, key=dist.get)
        return best_state, dist[best_state]
    
    def entropy(self, variable: str) -> float:
        """Compute Shannon entropy of marginal."""
        probs = self.marginals[variable]
        probs = probs[probs > 0]
        return float(-np.sum(probs * np.log(probs)))


@dataclass
class Explanation:
    """Explanation for a prediction."""
    target: str
    evidence: dict[str, Any]
    prediction: str
    confidence: float
    contributing_factors: dict[str, float]  # factor -> influence score
    sensitivity: dict[str, dict[str, float]]  # var -> {state: dP/dx}
    counterfactuals: list[dict]  # [{"intervention": {}, "prediction": "", "prob": 0.0}]


class InferenceAlgorithm(ABC):
    """Abstract base class for inference algorithms."""
    
    @abstractmethod
    def query(self, 
              model: Any,
              variables: list[str],
              evidence: dict[str, Any]) -> InferenceResult:
        pass
    
    @abstractmethod
    def intervene(self,
                  model: Any,
                  intervention: dict[str, Any],
                  targets: list[str]) -> InferenceResult:
        pass


class VariableEliminationAlgorithm(InferenceAlgorithm):
    """Exact inference via variable elimination (discrete Bayesian networks)."""
    
    def __init__(self):
        if not PGMPY_AVAILABLE:
            raise RuntimeError("pgmpy not installed. Run: pip install pgmpy")
    
    def query(self, model: BayesianNetwork, variables: list[str], evidence: dict) -> InferenceResult:
        infer = VariableElimination(model)
        result = infer.query(variables=variables, evidence=evidence, show_progress=False)
        
        marginals = {}
        state_names = {}
        for var in variables:
            if hasattr(result, 'values'):
                marginals[var] = result.values
            elif isinstance(result, dict):
                marginals[var] = result[var].values
            else:
                marginals[var] = np.array(result.get_values(var))
            state_names[var] = result.state_names.get(var, [])
        
        return InferenceResult(
            model_name=getattr(model, 'name', 'unknown'),
            query_variables=variables,
            evidence=evidence,
            marginals=marginals,
            state_names=state_names,
            algorithm="variable_elimination"
        )
    
    def intervene(self, model: BayesianNetwork, intervention: dict, targets: list[str]) -> InferenceResult:
        # For causal intervention, we modify the graph (remove incoming edges to intervened nodes)
        # then do standard inference with intervention as evidence
        from pgmpy.models import BayesianNetwork
        
        # Create intervened model
        intervened_model = model.copy()
        for var, value in intervention.items():
            # Remove incoming edges to intervened variable
            parents = list(intervened_model.get_parents(var))
            for p in parents:
                intervened_model.remove_edge(p, var)
            
            # Replace CPD with deterministic one
            cpd = intervened_model.get_cpds(var)
            if cpd:
                # Create new deterministic CPD
                new_cpd = TabularCPD(
                    variable=var,
                    variable_card=cpd.variable_card,
                    values=np.eye(cpd.variable_card)[:, [list(cpd.state_names[var]).index(value)]],
                    evidence=[],
                    evidence_card=[],
                    state_names={var: cpd.state_names[var]}
                )
                intervened_model.remove_cpds(var)
                intervened_model.add_cpds(new_cpd)
        
        evidence = {k: v for k, v in intervention.items()}
        return self.query(intervened_model, targets, evidence)


class BeliefPropagationAlgorithm(InferenceAlgorithm):
    """Belief propagation (exact for trees, approximate for loopy)."""
    
    def __init__(self, max_iter: int = 100, tolerance: float = 1e-6):
        if not PGMPY_AVAILABLE:
            raise RuntimeError("pgmpy not installed. Run: pip install pgmpy")
        self.max_iter = max_iter
        self.tolerance = tolerance
    
    def query(self, model: Any, variables: list[str], evidence: dict) -> InferenceResult:
        if isinstance(model, BayesianNetwork):
            infer = BeliefPropagation(model)
        elif isinstance(model, MarkovNetwork):
            # For Markov networks, use loopy BP
            infer = BeliefPropagation(model)
        else:
            raise ValueError(f"Unsupported model type: {type(model)}")
        
        result = infer.query(variables=variables, evidence=evidence, 
                            max_iter=self.max_iter, tolerance=self.tolerance)
        
        marginals = {}
        state_names = {}
        for var in variables:
            if hasattr(result, 'values'):
                marginals[var] = result.values
            elif isinstance(result, dict):
                marginals[var] = result[var].values
            else:
                marginals[var] = np.array(result.get_values(var))
            state_names[var] = result.state_names.get(var, [])
        
        return InferenceResult(
            model_name=getattr(model, 'name', 'unknown'),
            query_variables=variables,
            evidence=evidence,
            marginals=marginals,
            state_names=state_names,
            algorithm="belief_propagation",
            converged=result.converged if hasattr(result, 'converged') else True
        )
    
    def intervene(self, model: Any, intervention: dict, targets: list[str]) -> InferenceResult:
        # For causal intervention on Bayesian networks
        if isinstance(model, BayesianNetwork):
            from pgmpy.models import BayesianNetwork
            intervened_model = model.copy()
            for var, value in intervention.items():
                parents = list(intervened_model.get_parents(var))
                for p in parents:
                    intervened_model.remove_edge(p, var)
                cpd = intervened_model.get_cpds(var)
                if cpd:
                    new_cpd = TabularCPD(
                        variable=var,
                        variable_card=cpd.variable_card,
                        values=np.eye(cpd.variable_card)[:, [list(cpd.state_names[var]).index(value)]],
                        evidence=[], evidence_card=[],
                        state_names={var: cpd.state_names[var]}
                    )
                    intervened_model.remove_cpds(var)
                    intervened_model.add_cpds(new_cpd)
            return self.query(intervened_model, targets, intervention)
        else:
            raise NotImplementedError("Intervention only supported for Bayesian networks")


class CausalInferenceAlgorithm(InferenceAlgorithm):
    """Causal inference using do-calculus (interventions, counterfactuals)."""
    
    def __init__(self, base_algorithm: InferenceAlgorithm | None = None):
        self.base = base_algorithm or VariableEliminationAlgorithm()
    
    def query(self, model: BayesianNetwork, variables: list[str], evidence: dict) -> InferenceResult:
        """Standard observational query."""
        return self.base.query(model, variables, evidence)
    
    def intervene(self, model: BayesianNetwork, intervention: dict, targets: list[str]) -> InferenceResult:
        """Causal query: P(targets | do(intervention))."""
        return self.base.intervene(model, intervention, targets)
    
    def counterfactual(self, 
                       model: BayesianNetwork,
                       evidence: dict,
                       intervention: dict,
                       targets: list[str]) -> InferenceResult:
        """
        Counterfactual query: P(targets | evidence, do(intervention)).
        Uses the 3-step procedure: Abduct -> Act -> Predict.
        """
        # Step 1: Abduct - compute posterior over exogenous variables given evidence
        # (Requires structural causal model with exogenous noise variables)
        # For now, approximate with intervention on top of evidence
        combined_evidence = {**evidence, **intervention}
        return self.base.query(model, targets, combined_evidence)
    
    def mediate(self, model: BayesianNetwork, treatment: str, outcome: str, 
                mediator: str, evidence: dict) -> dict[str, float]:
        """Mediation analysis: direct vs indirect effect."""
        # Total effect
        te = self.intervene(model, {treatment: 1}, [outcome]).marginal(outcome)[1] - \
             self.intervene(model, {treatment: 0}, [outcome]).marginal(outcome)[1]
        
        # Direct effect (block mediator)
        de = self.intervene(model, {treatment: 1, mediator: 0}, [outcome]).marginal(outcome)[1] - \
             self.intervene(model, {treatment: 0, mediator: 0}, [outcome]).marginal(outcome)[1]
        
        return {
            "total_effect": te,
            "direct_effect": de,
            "indirect_effect": te - de,
            "proportion_mediated": (te - de) / te if abs(te) > 1e-10 else 0.0
        }


class InferenceEngine:
    """Main inference engine - unified interface for all algorithms."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.networks: dict[str, Any] = {}  # name -> pgmpy model
        self.algorithms = {
            "variable_elimination": VariableEliminationAlgorithm(),
            "belief_propagation": BeliefPropagationAlgorithm(),
            "causal": CausalInferenceAlgorithm(),
        }
        self._model_configs: dict[str, dict] = {}
    
    def load_model(self, name: str, config: dict) -> bool:
        """Load a model from configuration."""
        try:
            model_type = config.get("type", "bayesian")
            
            if model_type == "bayesian":
                model = self._load_bayesian(name, config)
            elif model_type == "markov":
                model = self._load_markov(name, config)
            elif model_type == "influence_diagram":
                model = self._load_influence_diagram(name, config)
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            self.networks[name] = model
            self._model_configs[name] = config
            logger.info(f"Loaded model: {name} ({model_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {name}: {e}")
            return False
    
    def _load_bayesian(self, name: str, config: dict) -> BayesianNetwork:
        """Load Bayesian network from CPT files."""
        cpts_path = self.models_dir / config["cpts"]
        
        # Try BIF format first
        if cpts_path.suffix == ".bif":
            reader = BIFReader(str(cpts_path))
            model = reader.get_model()
            model.name = name
            return model
        
        # CSV format - build from structure + CPTs
        model = BayesianNetwork()
        model.name = name
        
        # Add edges from variable definitions
        for var in config.get("variables", []):
            for parent in var.get("parents", []):
                model.add_edge(parent, var["name"])
        
        # Load CPTs from CSV
        self._load_cpts_from_csv(model, cpts_path)
        
        # Validate
        assert model.check_model(), f"Model {name} validation failed"
        return model
    
    def _load_cpts_from_csv(self, model: BayesianNetwork, cpts_path: Path):
        """Load CPDs from CSV file(s)."""
        # Expect either single CSV with all CPTs or directory with one CSV per variable
        if cpts_path.is_dir():
            cpt_files = list(cpts_path.glob("*.csv"))
        else:
            cpt_files = [cpts_path]
        
        for cpt_file in cpt_files:
            df = pd.read_csv(cpt_file)
            # Expected columns: variable, parent1, parent2, ..., state, probability
            variable = df["variable"].iloc[0]
            parent_cols = [c for c in df.columns if c not in ["variable", "state", "probability"]]
            
            # Get variable card and state names
            states = sorted(df["state"].unique())
            variable_card = len(states)
            state_names = {variable: states}
            
            # Build evidence cards and values array
            if parent_cols:
                # Multi-dimensional CPT
                parent_cards = []
                for p in parent_cols:
                    p_states = sorted(df[p].unique())
                    state_names[p] = p_states
                    parent_cards.append(len(p_states))
                
                values = np.zeros((variable_card, np.prod(parent_cards)))
                for _, row in df.iterrows():
                    var_idx = states.index(row["state"])
                    parent_idx = 0
                    for i, p in enumerate(parent_cols):
                        p_idx = state_names[p].index(row[p])
                        parent_idx += p_idx * np.prod(parent_cards[i+1:]) if i+1 < len(parent_cards) else p_idx
                    values[var_idx, parent_idx] = row["probability"]
                
                cpd = TabularCPD(
                    variable=variable,
                    variable_card=variable_card,
                    values=values,
                    evidence=parent_cols,
                    evidence_card=parent_cards,
                    state_names=state_names
                )
            else:
                # No parents - prior
                values = np.zeros((variable_card, 1))
                for _, row in df.iterrows():
                    var_idx = states.index(row["state"])
                    values[var_idx, 0] = row["probability"]
                
                cpd = TabularCPD(
                    variable=variable,
                    variable_card=variable_card,
                    values=values,
                    state_names=state_names
                )
            
            model.add_cpds(cpd)
    
    def _load_markov(self, name: str, config: dict) -> MarkovNetwork:
        """Load Markov network from factor definitions."""
        model = MarkovNetwork()
        model.name = name
        
        # Add edges from factors
        for factor in config.get("factors", []):
            vars_in_factor = factor["variables"]
            for i, v1 in enumerate(vars_in_factor):
                for v2 in vars_in_factor[i+1:]:
                    model.add_edge(v1, v2)
        
        # Load factors (potentials)
        for factor in config.get("factors", []):
            potential_path = self.models_dir / factor["potential"]
            # Execute factor file to get potential function
            # For now, assume it's a Python module with get_potential() function
            spec = __import__(potential_path.stem, fromlist=['get_potential'])
            potential_fn = getattr(spec, 'get_potential', None)
            if potential_fn:
                from pgmpy.factors import Factor
                factor_obj = Factor(vars_in_factor, potential_fn())
                model.add_factors(factor_obj)
        
        return model
    
    def _load_influence_diagram(self, name: str, config: dict) -> BayesianNetwork:
        """Load influence diagram as Bayesian network with utility nodes."""
        # Load as Bayesian network first
        model = self._load_bayesian(name, config)
        
        # Add utility function reference
        if config.get("utility"):
            utility_path = self.models_dir / config["utility"]
            model.utility_function = str(utility_path)
        
        return model
    
    def query(self, 
              model_name: str,
              variables: list[str],
              evidence: dict[str, Any] = None,
              algorithm: str = "auto") -> InferenceResult:
        """
        Probabilistic query: P(variables | evidence).
        
        Args:
            model_name: Name of loaded model
            variables: List of query variables
            evidence: Dict of observed variables -> values
            algorithm: "auto", "variable_elimination", "belief_propagation", "causal"
        """
        if model_name not in self.networks:
            raise ValueError(f"Model '{model_name}' not loaded")
        
        model = self.networks[model_name]
        evidence = evidence or {}
        
        # Select algorithm
        if algorithm == "auto":
            algo_name = self._model_configs[model_name].get("inference", "variable_elimination")
        else:
            algo_name = algorithm
        
        if algo_name not in self.algorithms:
            raise ValueError(f"Unknown algorithm: {algo_name}")
        
        algo = self.algorithms[algo_name]
        return algo.query(model, variables, evidence)
    
    def intervene(self,
                  model_name: str,
                  intervention: dict[str, Any],
                  targets: list[str],
                  algorithm: str = "causal") -> InferenceResult:
        """
        Causal intervention: P(targets | do(intervention)).
        """
        if model_name not in self.networks:
            raise ValueError(f"Model '{model_name}' not loaded")
        
        model = self.networks[model_name]
        
        if algorithm not in self.algorithms:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        algo = self.algorithms[algorithm]
        return algo.intervene(model, intervention, targets)
    
    def counterfactual(self,
                       model_name: str,
                       evidence: dict[str, Any],
                       intervention: dict[str, Any],
                       targets: list[str]) -> InferenceResult:
        """Counterfactual query: P(targets | evidence, do(intervention))."""
        if model_name not in self.networks:
            raise ValueError(f"Model '{model_name}' not loaded")
        
        model = self.networks[model_name]
        algo = self.algorithms.get("causal")
        if not isinstance(algo, CausalInferenceAlgorithm):
            algo = CausalInferenceAlgorithm()
        
        return algo.counterfactual(model, evidence, intervention, targets)
    
    def explain(self,
                model_name: str,
                evidence: dict[str, Any],
                target: str,
                algorithm: str = "causal") -> Explanation:
        """Generate explanation for a prediction."""
        # Get prediction
        result = self.query(model_name, [target], evidence, algorithm)
        prediction, confidence = result.map(target)
        
        # Sensitivity analysis: how does P(target) change with each evidence?
        sensitivity = {}
        for var, val in evidence.items():
            sensitivity[var] = {}
            for state in self._get_variable_states(model_name, var):
                modified_evidence = {**evidence, var: state}
                mod_result = self.query(model_name, [target], modified_evidence, algorithm)
                mod_prob = mod_result.marginal(target).get(prediction, 0)
                sensitivity[var][state] = mod_prob - confidence
        
        # Contributing factors (simplified: mutual information or gradient)
        contributing = {}
        for var in evidence:
            # Use absolute sensitivity as influence score
            contributing[var] = max(abs(v) for v in sensitivity[var].values())
        
        # Counterfactuals: what if each evidence were different?
        counterfactuals = []
        for var, val in evidence.items():
            for state in self._get_variable_states(model_name, var):
                if state != val:
                    cf_result = self.counterfactual(model_name, evidence, {var: state}, [target])
                    cf_pred, cf_prob = cf_result.map(target)
                    counterfactuals.append({
                        "intervention": {var: state},
                        "prediction": cf_pred,
                        "probability": cf_prob,
                        "change": cf_prob - confidence
                    })
        
        return Explanation(
            target=target,
            evidence=evidence,
            prediction=prediction,
            confidence=confidence,
            contributing_factors=contributing,
            sensitivity=sensitivity,
            counterfactuals=counterfactuals[:10]  # Top 10
        )
    
    def _get_variable_states(self, model_name: str, variable: str) -> list[str]:
        """Get possible states for a variable."""
        config = self._model_configs.get(model_name, {})
        for var in config.get("variables", []):
            if var["name"] == variable:
                return var.get("states", [])
        # Fallback: try to get from model
        model = self.networks.get(model_name)
        if model and hasattr(model, 'get_cpds'):
            cpd = model.get_cpds(variable)
            if cpd:
                return cpd.state_names.get(variable, [])
        return ["false", "true"]


def create_engine(models_dir: str = "models") -> InferenceEngine:
    """Factory function to create engine with default algorithms."""
    engine = InferenceEngine(models_dir)
    return engine