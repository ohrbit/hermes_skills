#!/usr/bin/env python3
"""
End-to-end test for Isaac Lab Bridge.

Tests the bridge components without requiring Isaac Lab installation
(unit tests with mocks).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import torch
import yaml

# Import bridge modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.translator import (
    SkillConfig,
    ObservationNormalizer,
    ActionTranslator,
    ObservationTranslator,
    create_translators,
)
from scripts.executor import (
    SafetyLimits,
    SafetyMonitor,
    IsaacLabExecutor,
    MultiSkillExecutor,
    ExecutionResult,
)
from scripts.safety import SafetyLimits as SafetyLimits2, SimToRealSafetyAdapter


class TestSkillConfig(unittest.TestCase):
    """Test skill configuration loading."""
    
    def setUp(self):
        self.registry = {
            "skills": {
                "test_skill": {
                    "isaac_task": "TestTask-v0",
                    "policy_checkpoint": "logs/policy.pt",
                    "policy_type": "rsl_rl",
                    "obs_space": ["joint_pos", "joint_vel", "eef_pos"],
                    "action_space": "joint_position",
                    "action_dim": 9,
                    "params": [
                        {"name": "target", "type": "vector3", "default": [0.5, 0.0, 0.1]}
                    ],
                    "safety_limits": {
                        "max_force": 50.0,
                        "workspace_bounds": {"min": [-1, -1, 0], "max": [1, 1, 1]}
                    }
                }
            }
        }
    
    def test_load_from_registry(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.registry, f)
            registry_path = f.name
        
        try:
            config = SkillConfig.from_registry(registry_path, "test_skill")
            self.assertEqual(config.name, "test_skill")
            self.assertEqual(config.isaac_task, "TestTask-v0")
            self.assertEqual(config.action_dim, 9)
            self.assertEqual(len(config.obs_keys), 3)
        finally:
            Path(registry_path).unlink()


class TestObservationNormalizer(unittest.TestCase):
    """Test observation normalization."""
    
    def test_fit_and_normalize(self):
        normalizer = ObservationNormalizer(["joint_pos", "eef_pos"])
        
        # Fake observations
        observations = [
            {"joint_pos": np.array([0.0] * 9), "eef_pos": np.array([0.5, 0.0, 0.5])},
            {"joint_pos": np.array([0.1] * 9), "eef_pos": np.array([0.6, 0.1, 0.5])},
            {"joint_pos": np.array([-0.1] * 9), "eef_pos": np.array([0.4, -0.1, 0.5])},
        ]
        
        normalizer.fit(observations)
        
        # Check stats computed
        self.assertIn("joint_pos", normalizer.stats)
        self.assertIn("eef_pos", normalizer.stats)
        
        # Test normalization
        test_obs = {"joint_pos": np.array([0.0] * 9), "eef_pos": np.array([0.5, 0.0, 0.5])}
        normed = normalizer.normalize(test_obs)
        
        # Should be close to zero (mean)
        np.testing.assert_allclose(normed["joint_pos"], 0.0, atol=1e-6)
        np.testing.assert_allclose(normed["eef_pos"], 0.0, atol=1e-6)
        
        # Test denormalization
        denormed = normalizer.denormalize(normed)
        np.testing.assert_allclose(denormed["joint_pos"], test_obs["joint_pos"], atol=1e-6)


class TestActionTranslator(unittest.TestCase):
    """Test action translation."""
    
    def setUp(self):
        self.config = SkillConfig(
            name="test",
            isaac_task="Test-v0",
            policy_checkpoint="test.pt",
            policy_type="rsl_rl",
            obs_keys=["joint_pos"],
            action_space="joint_position",
            action_dim=9,
            params=[],
            safety_limits={},
        )
        self.translator = ActionTranslator(self.config)
    
    def test_denormalize_action(self):
        # Policy outputs in [-1, 1]
        action = torch.tensor([1.0, -1.0, 0.5, 0.0, -0.5, 1.0, -1.0, 0.0, 0.0])
        
        # Set bounds: scale to [-pi, pi] for joints
        self.translator.set_action_bounds(np.pi)
        
        denormed = self.translator.denormalize_action(action)
        
        # Check bounds
        self.assertTrue(torch.all(denormed >= -np.pi))
        self.assertTrue(torch.all(denormed <= np.pi))
        
        # Check specific values
        self.assertAlmostEqual(denormed[0].item(), np.pi)
        self.assertAlmostEqual(denormed[1].item(), -np.pi)
        self.assertAlmostEqual(denormed[2].item(), 0.5 * np.pi)


class TestObservationTranslator(unittest.TestCase):
    """Test observation translation to Hermes format."""
    
    def setUp(self):
        self.config = SkillConfig(
            name="pick_place",
            isaac_task="PickPlace-v0",
            policy_checkpoint="test.pt",
            policy_type="rsl_rl",
            obs_keys=["joint_pos", "joint_vel", "eef_pos", "eef_quat", "cube_pos", "cube_quat"],
            action_space="joint_position",
            action_dim=9,
            params=[],
            safety_limits={},
        )
        self.translator = ObservationTranslator(self.config)
    
    def test_isaac_to_hermes(self):
        obs = {
            "joint_pos": np.array([0.1] * 9),
            "joint_vel": np.array([0.01] * 9),
            "eef_pos": np.array([0.5, 0.0, 0.5]),
            "eef_quat": np.array([0, 0, 0, 1]),
            "cube_pos": np.array([0.5, 0.0, 0.1]),
            "cube_quat": np.array([0, 0, 0, 1]),
        }
        
        result = self.translator.isaac_to_hermes(obs, 1.0, False, False, {"success": True})
        
        # Check structure
        self.assertIn("joint_pos", result)
        self.assertIn("_meta", result)
        self.assertIn("_derived", result)
        
        # Check derived quantities
        self.assertIn("eef_to_cube_dist", result["_derived"])
        self.assertIn("gripper_width", result["_derived"])
        
        # Check distance calculation
        expected_dist = 0.4  # z difference
        self.assertAlmostEqual(result["_derived"]["eef_to_cube_dist"], expected_dist, places=1)
    
    def test_force_torque_derived(self):
        obs = {
            "joint_pos": np.array([0.1] * 9),
            "joint_vel": np.array([0.01] * 9),
            "eef_pos": np.array([0.5, 0.0, 0.5]),
            "eef_quat": np.array([0, 0, 0, 1]),
            "cube_pos": np.array([0.5, 0.0, 0.1]),
            "cube_quat": np.array([0, 0, 0, 1]),
            "force_torque": np.array([10.0, 0.0, 0.0, 1.0, 0.0, 0.0]),
        }
        
        result = self.translator.isaac_to_hermes(obs, 0.0, False, False, {})
        
        self.assertAlmostEqual(result["_derived"]["force_magnitude"], 10.0)
        self.assertAlmostEqual(result["_derived"]["torque_magnitude"], 1.0)


class TestSafetyMonitor(unittest.TestCase):
    """Test safety monitoring."""
    
    def setUp(self):
        self.limits = SafetyLimits(
            max_force=50.0,
            max_joint_velocity=2.0,
            workspace_bounds=([-0.5, -0.5, 0.0], [0.5, 0.5, 1.0]),
        )
        self.monitor = SafetyMonitor(self.limits)
    
    def test_pre_action_velocity_check(self):
        action = np.zeros(9)
        obs = {"joint_vel": np.array([3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])}
        
        safe, msg = self.monitor.check_pre_action(action, obs)
        self.assertFalse(safe)
        self.assertIn("Joint velocity limit exceeded", msg)
    
    def test_post_step_force_check(self):
        obs = {
            "force_torque": np.array([60.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
            "eef_pos": np.array([0.3, 0.0, 0.5]),
        }
        
        safe, msg = self.monitor.check_post_step(obs, 0.0, 0)
        self.assertFalse(safe)
        self.assertIn("Force limit", msg)
    
    def test_workspace_bounds(self):
        obs = {
            "eef_pos": np.array([1.0, 0.0, 0.5]),  # x > 0.5
        }
        
        safe, msg = self.monitor.check_post_step(obs, 0.0, 0)
        self.assertFalse(safe)
        self.assertIn("Workspace bounds", msg)
    
    def test_emergency_stop(self):
        stop_cmd = self.monitor.emergency_stop(9)
        self.assertEqual(stop_cmd.shape, (9,))
        np.testing.assert_allclose(stop_cmd, 0.0)


class TestSimToRealSafetyAdapter(unittest.TestCase):
    """Test sim-to-real safety adaptation."""
    
    def test_adapt_limits(self):
        sim_limits = SafetyLimits2(
            max_force=50.0,
            max_velocity=2.0,
            max_joint_velocity=3.0,
            force_limit=30.0,
            human_proximity_stop=0.3,
        )
        
        real_limits = SimToRealSafetyAdapter.adapt_for_real(sim_limits)
        
        self.assertEqual(real_limits.max_force, 25.0)  # 50%
        self.assertEqual(real_limits.max_velocity, 1.0)  # 50%
        self.assertEqual(real_limits.max_joint_velocity, 2.1)  # 70%
        self.assertEqual(real_limits.force_limit, 15.0)  # 50%
        self.assertEqual(real_limits.human_proximity_stop, 1.5)  # Fixed larger distance
        self.assertEqual(real_limits.max_violations, 1)  # Zero tolerance


class TestIntegration(unittest.TestCase):
    """Integration test with mocked Isaac Lab."""
    
    @patch('scripts.executor.gym')
    @patch('scripts.executor.torch.jit.load')
    def test_executor_load_skill(self, mock_load, mock_gym):
        # Setup mock
        mock_env = MagicMock()
        mock_env.reset.return_value = ({"joint_pos": np.zeros(9)}, {})
        mock_env.observation_space = MagicMock()
        mock_env.action_space = MagicMock()
        mock_gym.make.return_value = mock_env
        
        mock_policy = MagicMock()
        mock_load.return_value = mock_policy
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            registry = {
                "skills": {
                    "test_skill": {
                        "isaac_task": "Test-v0",
                        "policy_checkpoint": "test.pt",
                        "policy_type": "rsl_rl",
                        "obs_space": ["joint_pos"],
                        "action_space": "joint_position",
                        "action_dim": 9,
                        "params": [],
                        "safety_limits": {"max_force": 50.0}
                    }
                }
            }
            yaml.dump(registry, f)
            registry_path = f.name
        
        try:
            executor = IsaacLabExecutor(registry_path, "test_skill")
            loaded = executor.load_skill()
            
            self.assertTrue(loaded)
            self.assertIsNotNone(executor.config)
            self.assertEqual(executor.config.name, "test_skill")
        finally:
            Path(registry_path).unlink()


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSkillConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestObservationNormalizer))
    suite.addTests(loader.loadTestsFromTestCase(TestActionTranslator))
    suite.addTests(loader.loadTestsFromTestCase(TestObservationTranslator))
    suite.addTests(loader.loadTestsFromTestCase(TestSafetyMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestSimToRealSafetyAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)