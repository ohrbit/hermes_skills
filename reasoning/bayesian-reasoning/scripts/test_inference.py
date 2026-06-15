#!/usr/bin/env python3
"""
Unit Tests for Bayesian Reasoning Skill.
"""

import unittest
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.model_registry import ModelRegistry, Variable, ModelConfig, VariableType, ModelType
from scripts.inference import InferenceEngine, InferenceResult, Explanation
from scripts.learner import ModelLearner, StructureLearner, ParameterLearner, ContinuousDiscretizer


class TestModelRegistry(unittest.TestCase):
    """Test model registry loading and validation."""
    
    def setUp(self):
        self.registry_yaml = """
models:
  test_bayesian:
    type: bayesian
    description: "Test model"
    variables:
      - name: "A"
        type: "discrete"
        states: ["0", "1"]
        parents: []
      - name: "B"
        type: "discrete"
        states: ["0", "1"]
        parents: ["A"]
    cpts: "models/cpts/test.csv"
    inference: "variable_elimination"
"""
    
    def test_load_registry(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(self.registry_yaml)
            path = f.name
        
        try:
            registry = ModelRegistry(path)
            self.assertIn("test_bayesian", registry.models)
            model = registry.models["test_bayesian"]
            self.assertEqual(model.model_type, ModelType.BAYESIAN)
            self.assertEqual(len(model.variables), 2)
        finally:
            Path(path).unlink()
    
    def test_validation(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(self.registry_yaml)
            path = f.name
        
        try:
            registry = ModelRegistry(path)
            errors = registry.validate()
            self.assertEqual(len(errors), 1)  # CPT file doesn't exist
        finally:
            Path(path).unlink()


class TestContinuousDiscretizer(unittest.TestCase):
    """Test continuous variable discretization."""
    
    def test_fit_transform(self):
        np.random.seed(42)
        data = pd.DataFrame({
            "x": np.random.randn(1000),
            "y": np.random.uniform(0, 10, 1000),
            "z": ["a", "b"] * 500  # categorical
        })
        
        disc = ContinuousDiscretizer(n_bins=5, strategy="quantile")
        disc.fit(data, columns=["x", "y"])
        transformed = disc.transform(data)
        
        # Check discretization
        self.assertTrue(transformed["x"].dtype in [np.int64, np.int32])
        self.assertTrue(transformed["y"].dtype in [np.int64, np.int32])
        self.assertEqual(transformed["x"].nunique(), 5)
        self.assertEqual(transformed["y"].nunique(), 5)
        # Categorical unchanged
        self.assertEqual(list(transformed["z"].unique()), ["a", "b"])
    
    def test_inverse_transform(self):
        data = pd.DataFrame({"x": [0, 1, 2, 3, 4]})
        disc = ContinuousDiscretizer(n_bins=5, strategy="uniform")
        disc.fit(pd.DataFrame({"x": np.linspace(0, 10, 100)}))
        inverse = disc.inverse_transform(data)
        
        # Should map to bin centers
        self.assertTrue(all(inverse["x"].notna()))


class TestModelLearner(unittest.TestCase):
    """Test structure and parameter learning."""
    
    def setUp(self):
        # Create synthetic data with known structure: A -> B -> C
        np.random.seed(42)
        n = 1000
        A = np.random.binomial(1, 0.6, n)
        B = np.array([np.random.binomial(1, 0.8 if a else 0.3) for a in A])
        C = np.array([np.random.binomial(1, 0.9 if b else 0.2) for b in B])
        
        self.data = pd.DataFrame({"A": A, "B": B, "C": C})
    
    def test_hill_climbing(self):
        if not hasattr(self, 'PGMPY_AVAILABLE') or not PGMPY_AVAILABLE:
            self.skipTest("pgmpy not available")
        
        learner = StructureLearner()
        model = learner.learn_hill_climbing(self.data, scoring_method="bic")
        
        # Should recover A -> B -> C structure
        self.assertTrue(model.has_edge("A", "B") or model.has_edge("B", "A"))
        self.assertTrue(model.has_edge("B", "C") or model.has_edge("C", "B"))
    
    def test_parameter_learning(self):
        if not hasattr(self, 'PGMPY_AVAILABLE') or not PGMPY_AVAILABLE:
            self.skipTest("pgmpy not available")
        
        from pgmpy.models import BayesianNetwork
        model = BayesianNetwork([("A", "B"), ("B", "C")])
        
        learner = ParameterLearner()
        model = learner.learn_mle(model, self.data)
        
        # Check CPDs learned
        self.assertIsNotNone(model.get_cpds("A"))
        self.assertIsNotNone(model.get_cpds("B"))
        self.assertIsNotNone(model.get_cpds("C"))
    
    def test_full_learning_pipeline(self):
        if not hasattr(self, 'PGMPY_ESTIMATORS') or not PGMPY_ESTIMATORS:
            self.skipTest("pgmpy estimators not available")
        
        learner = ModelLearner(
            structure_method="hc",
            score="bic",
            param_method="mle",
            discretize_continuous=False
        )
        
        learned = learner.learn(self.data)
        
        self.assertIsNotNone(learned.model)
        self.assertGreater(len(learned.model.nodes()), 0)
        self.assertIsInstance(learned.structure_score, float)


class TestInferenceEngine(unittest.TestCase):
    """Test inference engine with mocked models."""
    
    def setUp(self):
        # Simple model: A -> B
        try:
            from pgmpy.models import BayesianNetwork
            from pgmpy.factors.discrete import TabularCPD
            
            model = BayesianNetwork([("A", "B")])
            model.name = "test_model"
            
            cpd_a = TabularCPD("A", 2, [[0.6], [0.4]])
            cpd_b = TabularCPD("B", 2, [[0.9, 0.2], [0.1, 0.8]], 
                              evidence=["A"], evidence_card=[2])
            model.add_cpds(cpd_a, cpd_b)
            
            self.model = model
            self.PGMPY_AVAILABLE = True
        except ImportError:
            self.PGMPY_AVAILABLE = False
    
    def test_query(self):
        if not self.PGMPY_AVAILABLE:
            self.skipTest("pgmpy not available")
        
        engine = InferenceEngine()
        engine.networks["test"] = self.model
        engine._model_configs["test"] = {"inference": "variable_elimination"}
        
        result = engine.query("test", ["B"], {"A": 1})
        
        self.assertIsInstance(result, InferenceResult)
        self.assertIn("B", result.marginals)
        probs = result.marginal("B")
        # P(B=1 | A=1) should be 0.8
        self.assertAlmostEqual(probs.get("1", 0), 0.8, places=1)
    
    def test_intervene(self):
        if not self.PGMPY_AVAILABLE:
            self.skipTest("pgmpy not available")
        
        engine = InferenceEngine()
        engine.networks["test"] = self.model
        
        # P(B | do(A=1)) - should equal P(B | A=1) in this simple case
        result = engine.intervene("test", {"A": 1}, ["B"])
        
        probs = result.marginal("B")
        self.assertAlmostEqual(probs.get("1", 0), 0.8, places=1)
    
    def test_explain(self):
        if not self.PGMPY_AVAILABLE:
            self.skipTest("pgmpy not available")
        
        engine = InferenceEngine()
        engine.networks["test"] = self.model
        engine._model_configs["test"] = {"variables": [
            {"name": "A", "states": ["0", "1"]},
            {"name": "B", "states": ["0", "1"]}
        ]}
        
        explanation = engine.explain("test", {"A": 1}, "B")
        
        self.assertIsInstance(explanation, Explanation)
        self.assertEqual(explanation.target, "B")
        self.assertIn("confidence", explanation.__dict__)


# Check pgmpy availability for conditional tests
try:
    import pgmpy
    PGMPY_AVAILABLE = True
    PGMPY_ESTIMATORS = True
except ImportError:
    PGMPY_AVAILABLE = False
    PGMPY_ESTIMATORS = False


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestModelRegistry))
    suite.addTests(loader.loadTestsFromTestCase(TestContinuousDiscretizer))
    suite.addTests(loader.loadTestsFromTestCase(TestModelLearner))
    suite.addTests(loader.loadTestsFromTestCase(TestInferenceEngine))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)