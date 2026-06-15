# Causal Inference Guide for Hermes

> "Correlation is not causation" — but with the right tools, we can reason about causation.

## Why Causal Inference Matters for Hermes

| Question | Standard ML | Causal Inference |
|----------|-------------|------------------|
| "What happens if I do X?" | Predicts P(Y \| X observed) | Computes P(Y \| do(X)) |
| "Why did Y happen?" | Feature importance | Root cause via counterfactuals |
| "Would Y have happened if I'd done Z?" | Can't answer | Counterfactual query |
| "What's the effect of X on Y through M?" | Mediation via correlation | Natural direct/indirect effects |

## The Three Rungs of Causality (Pearl's Ladder)

```
Rung 3: Counterfactuals     P(Y_x = y | X = x', Y = y')
              │              "What would have happened if...?"
              ▼
Rung 2: Interventions       P(Y | do(X = x))
              │              "What if I do X?"
              ▼
Rung 1: Observation         P(Y | X = x)
                             "What happens when I see X?"
```

**Standard ML = Rung 1 only.** Causal inference unlocks Rungs 2 & 3.

---

## Key Concepts

### Causal Graph (DAG)
- Nodes = variables
- Directed edges = causal relationships
- No cycles (DAG)

```
Example: Robot pick-place
cube_weight  ──────► grasp_stability ──────► success
     │                    ▲
     ▼                    │
gripper_force ───────────┘
```

### Structural Causal Model (SCM)
Each variable is a function of its parents + exogenous noise:
```
grasp_stability = f(cube_weight, gripper_force, U_grasp)
success = g(grasp_stability, U_success)
```
- `U_*` = unobserved exogenous variables (noise)
- Functions `f, g` can be non-linear, non-parametric

### Interventions (do-operator)
`do(X = x)` means: set X to x, **removing all incoming edges** to X.
- Breaks natural causal influences on X
- Simulates "what if I force X?"

### Counterfactuals
`Y_x(u)` = value Y would take if X were x, in scenario u (where u fixes all exogenous noise).
- Requires SCM with explicit noise variables
- "In *this specific situation*, what if I'd done differently?"

---

## Do-Calculus (Pearl's Rules)

For any causal graph, these rules let you transform interventional queries into observational ones:

| Rule | Condition | Transformation |
|------|-----------|----------------|
| **1 (Insertion/Deletion of Observations)** | `(Y ⊥⊥ Z | X, W)` in G_{\overline{X}} | `P(y | do(x), z, w) = P(y | do(x), w)` |
| **2 (Action/Observation Exchange)** | `(Y ⊥⊥ Z | X, W)` in G_{\overline{X}, \underline{Z}} | `P(y | do(x), do(z), w) = P(y | do(x), z, w)` |
| **3 (Insertion/Deletion of Actions)** | `(Y ⊥⊥ Z | X, W)` in G_{\overline{X}, \overline{Z(W)}} | `P(y | do(x), do(z), w) = P(y | do(x), w)` |

Where:
- `G_{\overline{X}}` = graph with incoming edges to X removed
- `G_{\underline{Z}}` = graph with outgoing edges from Z removed
- `Z(W)` = nodes in Z not ancestors of W

**In practice:** Use `pgmpy`'s causal inference or `dowhy` library instead of manual do-calculus.

---

## Identification Strategies

### 1. Backdoor Criterion
To estimate `P(Y | do(X))`, find set `Z` that blocks all backdoor paths from X to Y:
- No node in Z is a descendant of X
- Z blocks every path between X and Y with arrow into X

Then: `P(Y | do(X)) = Σ_z P(Y | X, Z=z) P(Z=z)`

### 2. Frontdoor Criterion
When backdoor blocked but unobserved confounders exist:
- X → M → Y (M mediates)
- No unblocked backdoor X → M
- All backdoors M → Y blocked by X

Then: `P(Y | do(X)) = Σ_m P(M=m | X) Σ_x' P(Y | X=x', M=m) P(X=x')`

### 3. Instrumental Variables
Variable Z that:
- Affects X
- Doesn't affect Y except through X
- Independent of unobserved confounders

---

## Common Patterns in Robotics

### 1. Action → Outcome (Planning)
```
action ──────► outcome
   ▲             │
   │             ▼
context ──────► success
```
- Query: `P(success | do(action), context)`
- Use for: skill selection, parameter optimization

### 2. Confounding (Sim-to-Real Gap)
```
sim_params ──────► sim_outcome
     │                 ▲
     │                 │
     ▼                 │
real_params ──────► real_outcome
     ▲                 │
     └──── domain ────┘
```
- Unobserved `domain` confounds sim→real transfer
- Solution: Domain randomization (break confounding), or instrumental variables

### 3. Mediation (Skill Decomposition)
```
grasp_type ──────► grasp_quality ──────► success
     │                   │
     └───────────────────┘ (direct effect)
```
- Total effect = Direct + Indirect
- Use `mediate()` to find which skills work *through* quality

### 4. Counterfactual Diagnosis
```
fault ──────► symptom_1
  │
  └────────► symptom_2
  │
  └────────► symptom_3
```
- Observe symptoms, query `P(fault | symptoms)`
- Counterfactual: `P(fault | symptoms, do(intervention))`
- "If I replace motor, will symptom_2 disappear?"

---

## Implementation in This Skill

### Causal Query (Intervention)
```python
# P(success | do(grasp_stability=high))
result = engine.intervene(
    "pick_place_outcome",
    intervention={"grasp_stability": "high"},
    targets=["success"]
)
```

### Counterfactual Query
```python
# P(success | cube_weight=0.8, do(gripper_force=40))
result = engine.counterfactual(
    "pick_place_outcome",
    evidence={"cube_weight": 0.8},
    intervention={"gripper_force": 40},
    targets=["success"]
)
```

### Mediation Analysis
```python
# Direct vs indirect effect of grasp_type on success through grasp_quality
effects = engine.algorithms["causal"].mediate(
    model="pick_place_outcome",
    treatment="grasp_type",
    outcome="success",
    mediator="grasp_quality",
    evidence={}
)
```

### Explanation with Counterfactuals
```python
explanation = engine.explain(
    "pick_place_outcome",
    evidence={"cube_weight": 0.8, "gripper_force": 20},
    target="success"
)
# Returns:
# - prediction, confidence
# - sensitivity: how P(success) changes with each evidence
# - counterfactuals: what if each evidence were different?
```

---

## Best Practices

| Practice | Why |
|----------|-----|
| **Draw the causal graph first** | Forces explicit assumptions |
| **Separate observation from intervention** | `P(Y|X)` ≠ `P(Y|do(X))` |
| **Use domain knowledge for structure** | Data alone can't identify direction |
| **Validate with RCTs when possible** | Ground truth for causal claims |
| **Sensitivity analysis** | How robust to unobserved confounding? |
| **Report both observational & causal** | Transparency about what's identified |

---

## Recommended Reading

| Resource | Level | Focus |
|----------|-------|-------|
| Pearl et al. "Causal Inference in Statistics" | Intro | Primer |
| Pearl "Causality" (2009) | Advanced | Mathematics |
| Hernán & Robins "Causal Inference" | Applied | Epidemiology |
| Peters et al. "Elements of Causal Inference" | ML | Algorithms |
| `dowhy` library docs | Code | Python implementation |

---

## Tools in This Skill

| Need | Function |
|------|----------|
| Intervention: `P(Y | do(X))` | `engine.intervene()` |
| Counterfactual: `P(Y_x | X', Y')` | `engine.counterfactual()` |
| Explanation with sensitivity | `engine.explain()` |
| Mediation analysis | `CausalInferenceAlgorithm.mediate()` |
| Learn structure from data | `StructureLearner.learn_hc/pc/ges()` |
| Learn parameters | `ParameterLearner.learn_mle/bayesian()` |