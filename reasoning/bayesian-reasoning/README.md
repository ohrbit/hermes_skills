# bayesian-reasoning

[![Skill](https://img.shields.io/badge/Hermes_Skill-bayesian--reasoning-8dbb3c?style=flat-square)](https://github.com/nousresearch/hermes-agent)
[![Category](https://img.shields.io/badge/Category-reasoning-blue?style=flat-square)](https://github.com/nousresearch/hermes-agent/tree/main/skills/reasoning)
[![License](https://img.shields.io/github/license/nousresearch/hermes-agent?style=flat-square)]()

> **Probabilistic graphical models (Bayesian & Markov networks) for structured uncertainty reasoning** — causal planning, belief tracking, diagnostic inference, and decision-making under uncertainty.

## Why bayesian-reasoning?

**Problem:** Hermes agents operate in stochastic environments but lack structured uncertainty reasoning — no causal outcome prediction, no belief fusion, no diagnostic root-cause analysis, no risk-aware planning.

**Solution:** This skill brings **Bayesian networks** (causal, directed) and **Markov networks** (correlational, undirected) to Hermes via `pgmpy`, enabling P(outcome \| do(action)), sensor fusion, fault diagnosis, and influence-diagram-based skill selection — all declaratively configured, learned from memory.

## Features

- ✅ **Declarative model registry** — YAML definitions for Bayesian, Markov, and Influence Diagram models
- ✅ **Multiple inference algorithms** — Variable Elimination, Belief Propagation, Junction Tree, MCMC, Causal (do-calculus)
- ✅ **Causal queries** — `P(target \| do(intervention))` for intervention planning
- ✅ **Diagnostic inference** — Symptoms → posterior over root causes
- ✅ **Sensor fusion** — Markov networks for multi-modal belief tracking
- ✅ **Decision under uncertainty** — Influence diagrams with utility maximization
- ✅ **Auto-learning from memory** — Structure + parameter learning from Hermes Vault Tier 2
- ✅ **Isaac Lab Bridge integration** — Risk-aware skill execution with outcome prediction
- ✅ **Model visualization** — GraphViz export for debugging

## Quick Start

```bash
# 1. Install dependencies
pip install pgmpy networkx pandas numpy scipy graphviz

# 2. Load skill
hermes skill load bayesian-reasoning

# 3. Define models in models/registry.yaml (see templates/)

# 4. Run queries
hermes> probability_query("pick_place_outcome", variables=["success"], evidence={"cube_weight": 0.5})
hermes> causal_query("pick_place_outcome", intervention={"grasp_stability": "high"}, targets=["success"])
hermes> diagnose({"high_current": true, "position_error": true}, "robot")
hermes> probabilistic_plan("stack 3 blocks", {"workspace": "cluttered"})
```

## Model Types

| Type | Use Case | Inference |
|------|----------|-----------|
| **Bayesian** (Causal) | Action → Outcome, Diagnosis | VE, BP, Junction Tree, MCMC, Causal |
| **Markov** (Correlational) | Sensor Fusion, SLAM Belief | Belief Propagation, MCMC |
| **Influence Diagram** | Skill Selection, Utility Max | Variable Elimination + Utility |

## Registry Configuration (`models/registry.yaml`)

```yaml
models:
  # Causal: Action → Outcome
  pick_place_outcome:
    type: bayesian
    description: "Predict pick-place success from context"
    variables:
      - name: "cube_weight"
        type: continuous
        parents: []
      - name: "grasp_stability"
        type: discrete
        states: [low, medium, high]
        parents: ["cube_weight", "gripper_force", "surface_friction"]
      - name: "success"
        type: discrete
        states: [fail, succeed]
        parents: ["grasp_stability"]
    cpts:
      grasp_stability: "models/cpts/pick_place_grasp_stability.csv"
      success: "models/cpts/pick_place_success.csv"
    inference: variable_elimination

  # Diagnostic: Symptoms → Root cause
  robot_fault_diagnosis:
    type: bayesian
    variables:
      - name: "high_current"
        type: discrete
        states: [false, true]
        parents: ["joint_overheating", "encoder_drift"]
      - name: "position_error"
        type: discrete
        states: [false, true]
        parents: ["encoder_drift"]
    cpts: "models/cpts/robot_faults.csv"

  # Correlational: Sensor fusion
  localization_belief:
    type: markov
    factors:
      - variables: ["pose_x", "pose_y", "pose_theta"]
        potential: "models/factors/odometry_factor.py"
      - variables: ["pose_x", "pose_y", "landmark_id"]
        potential: "models/factors/vision_factor.py"

  # Decision: Skill selection under uncertainty
  skill_selector:
    type: influence_diagram
    variables:
      - name: "skill_choice"
        type: decision
        states: [pick_place, push_grasp, suction_grasp]
        parents: ["task_context"]
      - name: "success"
        type: chance
        states: [fail, succeed]
        parents: ["skill_choice", "task_context"]
      - name: "utility"
        type: utility
        parents: ["success", "time_cost"]
    cpts: "models/cpts/skill_selector.csv"
    utility: "models/utilities/skill_utility.py"
```

## Core API

### Inference Engine (`engine/inference.py`)

```python
from bayesian_reasoning import InferenceEngine

engine = InferenceEngine()

# Observational query: P(variables | evidence)
result = engine.query(
    model_name="pick_place_outcome",
    variables=["success", "grasp_stability"],
    evidence={"cube_weight": 0.5, "gripper_force": 30},
    algorithm="variable_elimination"  # or "belief_propagation", "mcmc", "auto"
)

# Causal query: P(targets | do(intervention))
result = engine.intervene(
    model_name="pick_place_outcome",
    intervention={"grasp_stability": "high"},
    targets=["success"]
)

# Explanation: Why this prediction?
explanation = engine.explain("pick_place_outcome", 
    evidence={"cube_weight": 0.5}, target="success")
# Returns: contributing factors, sensitivity, counterfactuals
```

### Model Learner (`engine/learner.py`)

```python
from bayesian_reasoning import ModelLearner

learner = ModelLearner()

# Learn structure from data
bn = learner.learn_structure(data=df, method="hc", score="bic")

# Learn parameters
bn = learner.learn_parameters(bn, data=df, method="mle")

# Auto-learn from Hermes memory
model = learner.learn_from_memory("pick_place", 
    "SELECT * FROM skill_outcomes WHERE skill='pick_place'")
```

## Hermes Skill Handlers

| Skill | Purpose | Example |
|-------|---------|---------|
| `probabilistic_plan` | Plan with outcome prediction + risk | `probabilistic_plan("stack blocks", {"workspace": "cluttered"})` |
| `diagnose` | Diagnostic inference | `diagnose({"high_current": true}, "robot")` |
| `belief_update` | Multi-sensor fusion | `belief_update({"lidar": ..., "vision": ...}, prior)` |
| `causal_query` | Intervention effect | `causal_query("model", {"action": "push"}, ["success"])` |

## File Structure

```
bayesian-reasoning/
├── SKILL.md
├── models/
│   ├── registry.yaml              # Declarative model definitions
│   ├── cpts/                      # Conditional probability tables (CSV)
│   │   ├── pick_place_grasp_stability.csv
│   │   ├── pick_place_success.csv
│   │   ├── robot_faults.csv
│   │   └── skill_selector.csv
│   ├── factors/                   # Markov network factors (Python)
│   │   ├── odometry_factor.py
│   │   ├── vision_factor.py
│   │   └── lidar_factor.py
│   └── utilities/                 # Influence diagram utilities
│       └── skill_utility.py
├── engine/
│   ├── __init__.py
│   ├── inference.py               # InferenceEngine
│   ├── learner.py                 # ModelLearner
│   ├── causal.py                  # Do-calculus, counterfactuals
│   └── sensitivity.py             # Sensitivity analysis
├── hermes/
│   ├── __init__.py
│   ├── integration.py             # Hermes skill handlers
│   └── memory_hooks.py            # Auto-learning from memory
├── scripts/
│   ├── test_inference.py          # Unit tests
│   ├── learn_from_vault.py        # CLI: learn from Tier 2
│   └── visualize_model.py         # GraphViz visualization
├── templates/
│   ├── model.yaml.template
│   ├── cpt.csv.template
│   └── factor.py.template
└── references/
    ├── pgmpy_cheatsheet.md
    ├── causal_inference_guide.md
    └── decision_theory.md
```

## Algorithms Supported

| Algorithm | Use Case | Complexity |
|-----------|----------|------------|
| Variable Elimination | Exact, discrete, small | NP-hard (treewidth) |
| Belief Propagation | Tree / loopy | Linear / iterative |
| Junction Tree | Exact, any discrete | Exponential in clique |
| MCMC (Gibbs/HMC) | Large, mixed, continuous | Polynomial (samples) |
| Variational Inference | Large, approximate | Polynomial |
| Causal (do-calculus) | Interventions, counterfactuals | Graph surgery + inference |

## Integration with Isaac Lab Bridge

```python
# In isaac-lab-bridge skill_executor.py
from bayesian_reasoning import InferenceEngine

engine = InferenceEngine()

# Before executing: predict outcome distribution
prediction = engine.query(
    model_name="pick_place_outcome",
    variables=["success", "grasp_stability"],
    evidence={"cube_weight": 0.5, "surface_friction": 0.3}
)

# Risk-aware decision
if prediction.marginal("success")["succeed"] < 0.7:
    await hermes.skill.execute("request_human", {"reason": "low_confidence"})

# After execution: learn from outcome
engine.learn_from_memory("pick_place", 
    "SELECT * FROM skill_outcomes WHERE skill='pick_place'")
```

## Development Workflow

1. **Define model** in `models/registry.yaml`
2. **Add CPTs/factors** in `models/cpts/`, `models/factors/`
3. **Test inference** → `python scripts/test_inference.py`
4. **Learn from data** → `python scripts/learn_from_vault.py`
5. **Visualize** → `python scripts/visualize_model.py --model pick_place_outcome`
6. **Register Hermes skills** in `hermes/integration.py`

## Verification

```bash
# Unit tests
pytest scripts/test_inference.py -v

# Model validation (structure + CPTs sum to 1)
python scripts/validate_models.py

# Integration test
hermes skill load bayesian-reasoning
# Run example queries
```

## Common Pitfalls

| Problem | Fix |
|---------|-----|
| CPT rows don't sum to 1.0 | Validate with `scripts/validate_models.py` |
| Treewidth too high for VE | Switch to `mcmc` or `variational` |
| Continuous variables in discrete BN | Use `type: continuous` + MCMC/Hybrid inference |
| Cyclic graph in Bayesian network | Use Markov network or fix causal direction |
| `do()` query on non-causal model | Ensure model type is `bayesian` with correct parents |

## Related Skills

- [isaac-lab-bridge](../robotics/isaac-lab-bridge) — Execution bridge using outcome prediction
- [obsidian-memory](../note-taking/obsidian-memory) — Tier 2 source for auto-learning

## Contributing

PRs welcome. Add models to `models/registry.yaml`, CPTs to `models/cpts/`, tests to `scripts/test_inference.py`.

## License

MIT — Part of [Hermes Agent](https://github.com/nousresearch/hermes-agent) skills collection.

## Changelog

- **v0.1.0** — Initial release: Bayesian/Markov/Influence Diagram registry, InferenceEngine, ModelLearner, Hermes integration, Isaac Lab Bridge example