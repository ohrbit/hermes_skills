#!/usr/bin/env python3
"""
Model Learner for Bayesian Reasoning Skill.

Learn structure and parameters of probabilistic graphical models from data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Optional imports
try:
    from pgmpy.estimators import (
        HillClimbSearch, BicScore, BDeuScore, K2Score,
        MaximumLikelihoodEstimator, BayesianEstimator,
        PC, GES, ExhaustiveSearch
    )
    from pgmpy.models import BayesianNetwork
    from pgmpy.independence_tests import chi_square
    PGMPY_ESTIMATORS = True
except ImportError:
    PGMPY_ESTIMATORS = False
    BayesianNetwork = HillClimbSearch = BicScore = BDeuScore = object

try:
    from sklearn.preprocessing import KBinsDiscretizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class LearnedModel:
    """Container for learned model with metadata."""
    model: BayesianNetwork
    structure_score: float
    data_shape: tuple[int, int]
    variables: list[str]
    method: str
    score_type: str
    discretization: dict | None = None


class StructureLearner:
    """Learn graph structure from observational data."""
    
    def __init__(self, random_state: int = 42):
        if not PGMPY_ESTIMATORS:
            raise RuntimeError("pgmpy not installed. Run: pip install pgmpy")
        self.random_state = random_state
    
    def learn_hill_climbing(self,
                           data: pd.DataFrame,
                           scoring_method: str = "bic",
                           max_indegree: int | None = None,
                           max_iter: int = 1000,
                           tabu_length: int = 100) -> BayesianNetwork:
        """
        Learn structure using hill-climbing search.
        
        Scoring methods: bic, bdeu, k2
        """
        scoring = {
            "bic": BicScore(data),
            "bdeu": BDeuScore(data),
            "k2": K2Score(data),
        }[scoring_method]
        
        estimator = HillClimbSearch(data, scoring_method=scoring)
        model = estimator.estimate(
            max_indegree=max_indegree,
            max_iter=max_iter,
            tabu_length=tabu_length
        )
        
        # Fit parameters
        model.fit(data, estimator=MaximumLikelihoodEstimator)
        return model
    
    def learn_pc(self,
                 data: pd.DataFrame,
                 variant: str = "stable",
                 ci_test: str = "chi_square",
                 significance_level: float = 0.05,
                 max_cond_vars: int = 5) -> BayesianNetwork:
        """
        Learn structure using PC algorithm (constraint-based).
        
        Variants: stable, parallel, original
        """
        if ci_test == "chi_square":
            test = chi_square
        else:
            raise ValueError(f"Unknown CI test: {ci_test}")
        
        estimator = PC(data, variant=variant, ci_test=test, 
                      significance_level=significance_level)
        model = estimator.estimate(max_cond_vars=max_cond_vars)
        model.fit(data, estimator=MaximumLikelihoodEstimator)
        return model
    
    def learn_ges(self,
                  data: pd.DataFrame,
                  scoring_method: str = "bic") -> BayesianNetwork:
        """
        Learn structure using Greedy Equivalence Search (score-based).
        """
        scoring = {
            "bic": BicScore(data),
            "bdeu": BDeuScore(data),
        }[scoring_method]
        
        estimator = GES(data, scoring_method=scoring)
        model = estimator.estimate()
        model.fit(data, estimator=MaximumLikelihoodEstimator)
        return model
    
    def learn_exhaustive(self,
                         data: pd.DataFrame,
                         scoring_method: str = "bic",
                         max_indegree: int = 3) -> BayesianNetwork:
        """
        Exhaustive search (only for small networks, <=5 variables).
        """
        if len(data.columns) > 5:
            raise ValueError("Exhaustive search only for <=5 variables")
        
        scoring = {"bic": BicScore(data), "bdeu": BDeuScore(data)}[scoring_method]
        
        estimator = ExhaustiveSearch(data, scoring_method=scoring)
        model = estimator.estimate(max_indegree=max_indegree)
        model.fit(data, estimator=MaximumLikelihoodEstimator)
        return model
    
    def add_background_knowledge(self,
                                 model: BayesianNetwork,
                                 required_edges: list[tuple[str, str]] = None,
                                 forbidden_edges: list[tuple[str, str]] = None):
        """Add background knowledge constraints to learned structure."""
        if required_edges:
            for u, v in required_edges:
                if not model.has_edge(u, v):
                    model.add_edge(u, v)
        
        if forbidden_edges:
            for u, v in forbidden_edges:
                if model.has_edge(u, v):
                    model.remove_edge(u, v)
        
        return model


class ParameterLearner:
    """Learn CPD parameters from data."""
    
    def __init__(self, prior_equivalent_sample_size: int = 10):
        if not PGMPY_ESTIMATORS:
            raise RuntimeError("pgmpy not installed. Run: pip install pgmpy")
        self.prior_equiv = prior_equivalent_sample_size
    
    def learn_mle(self, model: BayesianNetwork, data: pd.DataFrame) -> BayesianNetwork:
        """Maximum Likelihood Estimation."""
        model.fit(data, estimator=MaximumLikelihoodEstimator)
        return model
    
    def learn_bayesian(self, 
                       model: BayesianNetwork, 
                       data: pd.DataFrame,
                       prior_type: str = "dirichlet") -> BayesianNetwork:
        """Bayesian parameter estimation with Dirichlet priors."""
        model.fit(data, estimator=BayesianEstimator, 
                 prior_type=prior_type,
                 equivalent_sample_size=self.prior_equiv)
        return model
    
    def learn_with_missing(self,
                           model: BayesianNetwork,
                           data: pd.DataFrame,
                           algorithm: str = "em") -> BayesianNetwork:
        """Learn parameters with missing data using EM."""
        # pgmpy doesn't have built-in EM for missing data
        # This is a placeholder for custom implementation
        logger.warning("EM for missing data not fully implemented")
        return self.learn_mle(model, data.dropna())


class ContinuousDiscretizer:
    """Discretize continuous variables for discrete Bayesian networks."""
    
    def __init__(self, n_bins: int = 5, strategy: str = "quantile"):
        """
        strategy: "uniform", "quantile", "kmeans"
        """
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn not installed. Run: pip install scikit-learn")
        self.n_bins = n_bins
        self.strategy = strategy
        self.discretizers: dict[str, KBinsDiscretizer] = {}
        self.bin_edges: dict[str, np.ndarray] = {}
    
    def fit(self, data: pd.DataFrame, columns: list[str] | None = None) -> "ContinuousDiscretizer":
        """Fit discretizers on continuous columns."""
        columns = columns or data.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in columns:
            disc = KBinsDiscretizer(
                n_bins=self.n_bins,
                encode="ordinal",
                strategy=self.strategy,
                subsample=min(20000, len(data))
            )
            disc.fit(data[[col]])
            self.discretizers[col] = disc
            self.bin_edges[col] = disc.bin_edges_[0]
        
        return self
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform continuous columns to discrete bins."""
        result = data.copy()
        for col, disc in self.discretizers.items():
            if col in result.columns:
                result[col] = disc.transform(result[[col]]).flatten().astype(int)
        return result
    
    def fit_transform(self, data: pd.DataFrame, columns: list[str] = None) -> pd.DataFrame:
        return self.fit(data, columns).transform(data)
    
    def inverse_transform(self, data: pd.DataFrame, columns: list[str] = None) -> pd.DataFrame:
        """Approximate inverse: map bin index to bin center."""
        result = data.copy()
        columns = columns or list(self.discretizers.keys())
        for col in columns:
            if col in result.columns and col in self.bin_edges:
                edges = self.bin_edges[col]
                centers = (edges[:-1] + edges[1:]) / 2
                result[col] = result[col].apply(
                    lambda x: centers[int(x)] if 0 <= int(x) < len(centers) else np.nan
                )
        return result
    
    def get_discretization_info(self) -> dict:
        """Return discretization parameters for saving."""
        return {
            col: {
                "n_bins": self.n_bins,
                "strategy": self.strategy,
                "edges": edges.tolist()
            }
            for col, edges in self.bin_edges.items()
        }


class ModelLearner:
    """High-level interface for learning complete models from data."""
    
    def __init__(self, 
                 structure_method: str = "hc",
                 score: str = "bic",
                 param_method: str = "mle",
                 discretize_continuous: bool = True,
                 n_bins: int = 5):
        self.structure_method = structure_method
        self.score = score
        self.param_method = param_method
        self.discretize_continuous = discretize_continuous
        self.n_bins = n_bins
        
        self.structure_learner = StructureLearner()
        self.param_learner = ParameterLearner()
        self.discretizer = ContinuousDiscretizer(n_bins=n_bins) if discretize_continuous else None
    
    def learn(self, 
              data: pd.DataFrame,
              target_variables: list[str] | None = None,
              background_knowledge: dict | None = None) -> LearnedModel:
        """
        Learn full model from data.
        
        Args:
            data: DataFrame with observations
            target_variables: If specified, learn only subgraph relevant to targets
            background_knowledge: Dict with "required_edges", "forbidden_edges"
        """
        # Preprocess
        original_data = data.copy()
        data = data.dropna()
        
        if data.empty:
            raise ValueError("No complete cases after dropping NaN")
        
        # Discretize continuous variables if needed
        discretization_info = None
        if self.discretize_continuous:
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                self.discretizer.fit(data, numeric_cols)
                data = self.discretizer.transform(data)
                discretization_info = self.discretizer.get_discretization_info()
        
        # Learn structure
        if self.structure_method == "hc":
            model = self.structure_learner.learn_hill_climbing(data, scoring_method=self.score)
        elif self.structure_method == "pc":
            model = self.structure_learner.learn_pc(data)
        elif self.structure_method == "ges":
            model = self.structure_learner.learn_ges(data, scoring_method=self.score)
        elif self.structure_method == "exhaustive":
            model = self.structure_learner.learn_exhaustive(data, scoring_method=self.score)
        else:
            raise ValueError(f"Unknown structure method: {self.structure_method}")
        
        # Apply background knowledge
        if background_knowledge:
            model = self.structure_learner.add_background_knowledge(
                model,
                background_knowledge.get("required_edges"),
                background_knowledge.get("forbidden_edges")
            )
        
        # Learn parameters
        if self.param_method == "mle":
            model = self.param_learner.learn_mle(model, data)
        elif self.param_method == "bayesian":
            model = self.param_learner.learn_bayesian(model, data)
        else:
            raise ValueError(f"Unknown parameter method: {self.param_method}")
        
        # Compute score
        from pgmpy.estimators import BicScore, BDeuScore
        score_fn = {"bic": BicScore(data), "bdeu": BDeuScore(data)}[self.score]
        structure_score = score_fn.score(model)
        
        return LearnedModel(
            model=model,
            structure_score=structure_score,
            data_shape=data.shape,
            variables=list(data.columns),
            method=f"{self.structure_method}_{self.param_method}",
            score_type=self.score,
            discretization=discretization_info
        )
    
    def learn_from_vault(self,
                         memory_query: str,
                         target_variables: list[str] | None = None,
                         limit: int = 10000) -> LearnedModel:
        """
        Learn model from Hermes Vault (Tier 2) memory.
        
        This is a conceptual interface - actual implementation needs
        Hermes memory provider.
        """
        # This would be implemented in hermes/memory_hooks.py
        # with actual Hermes memory integration
        raise NotImplementedError("Use hermes/memory_hooks.py for Hermes integration")
    
    def save_model(self, learned: LearnedModel, output_dir: str):
        """Save learned model to disk."""
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        
        # Save structure (BIF format)
        from pgmpy.readwrite import BIFWriter
        writer = BIFWriter(learned.model)
        writer.write_bif(str(output / "model.bif"))
        
        # Save parameters as CSV
        for cpd in learned.model.get_cpds():
            df = self._cpd_to_dataframe(cpd)
            df.to_csv(output / f"cpt_{cpd.variable}.csv", index=False)
        
        # Save metadata
        import json
        meta = {
            "structure_score": learned.structure_score,
            "data_shape": learned.data_shape,
            "variables": learned.variables,
            "method": learned.method,
            "score_type": learned.score_type,
            "discretization": learned.discretization,
        }
        with open(output / "meta.json", "w") as f:
            json.dump(meta, f, indent=2)
        
        logger.info(f"Model saved to {output}")
    
    def _cpd_to_dataframe(self, cpd) -> pd.DataFrame:
        """Convert CPD to long-format DataFrame."""
        variable = cpd.variable
        states = cpd.state_names.get(variable, [])
        evidence = cpd.variables[1:] if len(cpd.variables) > 1 else []
        evidence_states = {v: cpd.state_names.get(v, []) for v in evidence}
        
        rows = []
        if evidence:
            # Multi-dimensional
            import itertools
            for evidence_combo in itertools.product(*[range(len(evidence_states[e])) for e in evidence]):
                for var_state_idx, var_state in enumerate(states):
                    prob = cpd.get_value(**dict(zip(evidence, evidence_combo)), **{variable: var_state})
                    row = {"variable": variable, "state": var_state, "probability": prob}
                    for i, e in enumerate(evidence):
                        row[e] = evidence_states[e][evidence_combo[i]]
                    rows.append(row)
        else:
            for var_state_idx, var_state in enumerate(states):
                rows.append({
                    "variable": variable,
                    "state": var_state,
                    "probability": cpd.values[var_state_idx]
                })
        
        return pd.DataFrame(rows)


def learn_model_from_data(data: pd.DataFrame, **kwargs) -> LearnedModel:
    """Convenience function for one-shot learning."""
    learner = ModelLearner(**kwargs)
    return learner.learn(data)