---
name: bayesian-reasoning
description: Probabilistic graphical models (Bayesian & Markov networks) for structured uncertainty reasoning in Hermes. Enables causal planning, belief tracking, diagnostic inference, and decision-making under uncertainty.
category: reasoning
tags: [bayesian-network, markov-network, probabilistic-graphical-models, pgmpy, causal-inference, decision-theory, uncertainty, planning, diagnosis]
version: "0.1.0"
---

# Bayesian Reasoning for Hermes

## Purpose
Bring structured uncertainty reasoning to Hermes via **Bayesian networks** (causal, directed) and **Markov networks** (correlational, undirected). Enables:

- **Causal planning**: "If I do X, what's P(success)? What's P(side-effect)?"
- **Belief tracking**: Fuse noisy observations → posterior over world state
- **Diagnosis**: Given symptoms, what's the root cause?
- **Decision under uncertainty**: Maximize expected utility with risk awareness
- **Counterfactuals**: "Would Y have happened if I'd done X instead?"

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HERMES COGNITIVE LAYER                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Planner    │  │   Executor   │  │    Memory/Values     │  │
│  │  (HTN/LLM)   │  │  (Skills)    │  │  (SOUL + Preferences)│  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                     │              │
│         ▼                 ▼                     ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              BAYESIAN REASONING ENGINE                   │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │  │
│  │  │ Bayesian    │  │ Markov      │  │ Inference       │  │  │
│  │  │ Networks    │  │ Networks    │  │ Engine          │  │  │
│  │  │ (Causal)    │  │ (Correlation)│  │ (VE, BP, MCMC)  │  │  │
│  │  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘  │  │
│  └─────────┼────────────────┼───────────────────┼────────────┘  │
│            │                │                   │               │
│            ▼                ▼                   ▼               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    MODEL REGISTRY                         │  │
│  │  • Skill outcome models     • Sensor noise models        │  │
│  │  • Causal world models      • Diagnostic models          │  │
│  │  • Preference/utility nets  • Risk assessment models     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Model Registry (`models/registry.yaml`)
Declarative model definitions — no code needed for standard patterns.

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
      - name: "gripper_force"
        type: continuous
        parents: []
      - name: "surface_friction"
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
    description: "Diagnose robot faults from sensor readings"
    variables:
      - name: "joint_overheating"
        type: discrete
        states: [false, true]
        parents: []
      - name: "encoder_drift"
        type: discrete
        states: [false, true]
        parents: []
      - name: "high_current"
        type: discrete
        states: [false, true]
        parents: ["joint_overheating", "encoder_drift"]
      - name: "position_error"
        type: discrete
        states: [false, true]
        parents: ["encoder_drift"]
      - name: "thermal_shutdown"
        type: discrete
        states: [false, true]
        parents: ["joint_overheating"]
    cpts: "models/cpts/robot_faults.csv"
    
  # Correlational: Sensor fusion
  localization_belief:
    type: markov
    description: "Fuse odometry, vision, LiDAR for pose belief"
    factors:
      - variables: ["pose_x", "pose_y", "pose_theta"]
        potential: "models/factors/odometry_factor.py"
      - variables: ["pose_x", "pose_y", "landmark_id"]
        potential: "models/factors/vision_factor.py"
      - variables: ["pose_x", "pose_y", "scan_id"]
        potential: "models/factors/lidar_factor.py"
    inference: belief_propagation
    
  # Decision: Skill selection under uncertainty
  skill_selector:
    type: influence_diagram
    description: "Choose skill maximizing expected utility"
    variables:
      - name: "task_context"
        type: discrete
        states: [clean, cluttered, dynamic]
        parents: []
      - name: "skill_choice"
        type: decision
        states: [pick_place, push_grasp, suction_grasp]
        parents: ["task_context"]
      - name: "success"
        type: chance
        states: [fail, succeed]
        parents: ["skill_choice", "task_context"]
      - name: "time_cost"
        type: continuous
        parents: ["skill_choice", "task_context"]
      - name: "utility"
        type: utility
        parents: ["success", "time_cost"]
    cpts: "models/cpts/skill_selector.csv"
    utility: "models/utilities/skill_utility.py"
```

### 2. Inference Engine (`engine/inference.py`)
Unified interface for all inference algorithms.

```python
class InferenceEngine:
    """Run inference on Bayesian/Markov networks."""
    
    def query(self, model_name: str, 
              variables: list[str],
              evidence: dict[str, Any],
              algorithm: str = "auto") -> InferenceResult:
        """
        P(variables | evidence)
        
        Algorithms:
        - VariableElimination: exact, small networks
        - BeliefPropagation: exact (tree) / approximate (loopy)
        - MCMC (Gibbs/Metropolis): large, continuous
        - CausalInference: do-calculus for interventions
        """
    
    def intervene(self, model_name: str,
                  intervention: dict[str, Any],
                  targets: list[str]) -> InferenceResult:
        """
        P(targets | do(intervention)) — causal query.
        
        Example: P(success | do(skill=push_grasp), context=cluttered)
        """
    
    def explain(self, model_name: str,
                evidence: dict[str, Any],
                target: str) -> Explanation:
        """
        Why did the model predict this?
        Returns: contributing factors, sensitivity, counterfactuals.
        """
```

### 3. Model Learner (`engine/learner.py`)
Learn structure + parameters from data.

```python
class ModelLearner:
    """Learn PGMs from Hermes memory / execution traces."""
    
    def learn_structure(self, 
                        data: pd.DataFrame,
                        method: str = "hc",  # hill-climbing, PC, GES
                        score: str = "bic") -> BayesianNetwork:
        """Discover causal structure from observational data."""
    
    def learn_parameters(self,
                         model: BayesianNetwork,
                         data: pd.DataFrame,
                         method: str = "mle") -> BayesianNetwork:
        """Fit CPTs / potentials from data."""
    
    def learn_from_memory(self,
                          skill_name: str,
                          memory_query: str) -> Model:
        """Auto-build outcome model from Hermes Vault Tier 2."""
```

### 4. Hermes Integration (`hermes/integration.py`)
Skills and memory hooks.

```python
# Skill: probabilistic_plan
async def probabilistic_plan(goal: str, context: dict) -> Plan:
    """Plan using Bayesian network for outcome prediction."""
    # 1. Retrieve relevant causal models from registry
    # 2. Query P(outcome | do(action), context) for each candidate action
    # 3. Compute expected utility with risk weighting
    # 4. Return plan with confidence intervals

# Skill: diagnose
async def diagnose(symptoms: dict, domain: str) -> Diagnosis:
    """Diagnostic inference on Markov/Bayesian network."""
    # 1. Load diagnostic model for domain (robot, env, skill)
    # 2. Set symptoms as evidence
    # 3. Query posterior over root causes
    # 4. Return ranked causes with probabilities

# Skill: belief_update
async def belief_update(observations: dict, prior_belief: Belief) -> Belief:
    """Fuse multi-modal observations into posterior belief."""
    # 1. Load sensor fusion Markov network
    # 2. Run belief propagation
    # 3. Return updated belief state

# Memory hook: auto-learn models
async def on_skill_complete(skill_result: SkillResult):
    """Append outcome to dataset, trigger relearn if enough data."""
```

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
│   ├── learn_from_vault.py        # CLI: learn models from Tier 2
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

## Quickstart

```bash
# 1. Install dependencies
pip install pgmpy networkx pandas numpy scipy

# 2. Define model in models/registry.yaml

# 3. From Hermes:
hermes skill load bayesian-reasoning

# Causal query
> probability_query("pick_place_outcome", 
    variables=["success"], 
    evidence={"cube_weight": 0.5, "gripper_force": 30})

# Intervention (causal)
> causal_query("pick_place_outcome",
    intervention={"grasp_stability": "high"},
    targets=["success"])

# Diagnostic
> diagnose({"high_current": true, "position_error": true}, "robot")

# Plan with uncertainty
> probabilistic_plan("stack 3 blocks", {"workspace": "cluttered"})
```

## Use Cases by Domain

| Domain | Bayesian (Causal) | Markov (Correlational) |
|--------|-------------------|------------------------|
| **Robotics** | Action → outcome, sim-to-real gap | Sensor fusion, SLAM belief |
| **Planning** | Expected utility, risk-aware | Constraint satisfaction |
| **Diagnosis** | Root cause from interventions | Symptom → fault patterns |
| **Safety** | P(failure | do(action)) | Anomaly detection |
| **Learning** | Causal discovery from data | Parameter tying, transfer |
| **Values** | Influence diagrams for alignment | Preference elicitation |

## Algorithms Supported

| Algorithm | Use Case | Complexity |
|-----------|----------|------------|
| Variable Elimination | Exact, discrete, small | NP-hard (treewidth) |
| Belief Propagation | Tree / loopy | Linear / iterative |
| Junction Tree | Exact, any discrete | Exponential in clique |
| MCMC (Gibbs/HMC) | Large, mixed, continuous | Polynomial (samples) |
| Variational Inference | Large, approximate | Polynomial |
| Causal Inference (do-calculus) | Interventions, counterfactuals | Graph surgery + inference |

## Integration with Isaac Lab Bridge

```python
# In isaac-lab-bridge skill_executor.py
from bayesian_reasoning import InferenceEngine

engine = InferenceEngine()

# Before executing skill: predict outcome distribution
prediction = engine.query(
    model_name="pick_place_outcome",
    variables=["success", "grasp_stability"],
    evidence={"cube_weight": 0.5, "surface_friction": 0.3}
)

# Risk-aware decision
if prediction.marginal("success")["succeed"] < 0.7:
    # Switch to safer skill or request human
    await hermes.skill.execute("request_human", {"reason": "low_confidence"})

# After execution: update belief, learn
engine.learn_from_memory("pick_place", "SELECT * FROM skill_outcomes WHERE skill='pick_place'")
```

## Development Workflow

1. **Define model** in `models/registry.yaml`
2. **Add CPTs/factors** in `models/cpts/`, `models/factors/`
3. **Test inference** with `scripts/test_inference.py`
4. **Learn from data** with `scripts/learn_from_vault.py`
5. **Visualize** with `scripts/visualize_model.py --model pick_place_outcome`
6. **Register Hermes skills** in `hermes/integration.py`

## Verification

```bash
# Unit tests
pytest scripts/test_inference.py -v

# Model validation (structure + CPTs sum to 1)
python scripts/validate_models.py

# Integration test with Hermes
hermes skill load bayesian-reasoning
# Run example queries
```