# pgmpy Cheatsheet

Quick reference for pgmpy (Probabilistic Graphical Models for Python) — the core library used by this skill.

## Installation

```bash
pip install pgmpy
# Optional: for structure learning with continuous vars
pip install scikit-learn
```

---

## Bayesian Networks

### Creating a Model

```python
from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD

# Define structure
model = BayesianNetwork([
    ('A', 'C'),
    ('B', 'C'),
    ('C', 'D'),
])

# Add CPDs
cpd_a = TabularCPD('A', 2, [[0.6], [0.4]])  # P(A)
cpd_b = TabularCPD('B', 2, [[0.7], [0.3]])  # P(B)
cpd_c = TabularCPD('C', 2, [[0.9, 0.6, 0.7, 0.1],
                            [0.1, 0.4, 0.3, 0.9]],
                   evidence=['A', 'B'], evidence_card=[2, 2])  # P(C|A,B)
cpd_d = TabularCPD('D', 2, [[0.8, 0.2],
                            [0.2, 0.8]],
                   evidence=['C'], evidence_card=[2])  # P(D|C)

model.add_cpds(cpd_a, cpd_b, cpd_c, cpd_d)
assert model.check_model()
```

### Inference

```python
from pgmpy.inference import VariableElimination, BeliefPropagation

# Exact inference
infer = VariableElimination(model)
result = infer.query(variables=['D'], evidence={'A': 1})
print(result)  # P(D | A=1)

# Belief propagation (exact for trees, approx for loopy)
bp = BeliefPropagation(model)
result = bp.query(variables=['C', 'D'], evidence={'A': 1})
```

### Causal Inference (do-calculus)

```python
# Intervention: P(D | do(A=1))
# Remove incoming edges to A, set A=1
from pgmpy.models import BayesianNetwork

intervened = model.copy()
intervened.remove_cpds('A')
intervened.add_cpds(TabularCPD('A', 2, [[1.0], [0.0]]))  # Deterministic A=1

infer = VariableElimination(intervened)
result = infer.query(variables=['D'])  # P(D | do(A=1))
```

### Structure Learning

```python
from pgmpy.estimators import HillClimbSearch, BicScore, PC, GES

data = pd.DataFrame(...)  # observations

# Hill-climbing (score-based)
hc = HillClimbSearch(data, scoring_method=BicScore(data))
model = hc.estimate()

# PC algorithm (constraint-based)
pc = PC(data, variant='stable', ci_test=chi_square)
model = pc.estimate()

# GES (greedy equivalence search)
ges = GES(data, scoring_method=BicScore(data))
model = ges.estimate()
```

### Parameter Learning

```python
from pgmpy.estimators import MaximumLikelihoodEstimator, BayesianEstimator

# MLE
model.fit(data, estimator=MaximumLikelihoodEstimator)

# Bayesian (with Dirichlet prior)
model.fit(data, estimator=BayesianEstimator, 
         prior_type='dirichlet', equivalent_sample_size=10)
```

### Save/Load

```python
from pgmpy.readwrite import BIFWriter, BIFReader

# Save
writer = BIFWriter(model)
writer.write_bif('model.bif')

# Load
reader = BIFReader('model.bif')
model = reader.get_model()
```

---

## Markov Networks

```python
from pgmpy.models import MarkovNetwork
from pgmpy.factors import Factor
import numpy as np

# Structure
model = MarkovNetwork([('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'A')])

# Define potentials (factors)
# Factor over A,B
phi_ab = Factor(['A', 'B'], [2, 2], np.array([30, 5, 1, 10]))
phi_bc = Factor(['B', 'C'], [2, 2], np.array([20, 10, 5, 15]))
phi_cd = Factor(['C', 'D'], [2, 2], np.array([15, 5, 10, 20]))
phi_da = Factor(['D', 'A'], [2, 2], np.array([25, 5, 10, 15]))

model.add_factors(phi_ab, phi_bc, phi_cd, phi_da)
```

### Inference

```python
from pgmpy.inference import BeliefPropagation

bp = BeliefPropagation(model)
result = bp.query(variables=['A'], evidence={'C': 1})
```

---

## Continuous Variables (Gaussian Bayesian Networks)

```python
from pgmpy.models import LinearGaussianBayesianNetwork
from pgmpy.inference import ContinuousVariableElimination

# Structure
model = LinearGaussianBayesianNetwork([('A', 'C'), ('B', 'C')])

# Add Gaussian CPDs
from pgmpy.factors.continuous import LinearGaussianCPD

cpd_a = LinearGaussianCPD('A', [1], 2)  # P(A) ~ N(1, 2)
cpd_b = LinearGaussianCPD('B', [0], 1)  # P(B) ~ N(0, 1)
cpd_c = LinearGaussianCPD('C', [0.5, -0.3], 1.5, 
                          evidence=['A', 'B'])  # P(C|A,B) ~ N(0.5*A - 0.3*B, 1.5)

model.add_cpds(cpd_a, cpd_b, cpd_c)

# Inference
infer = ContinuousVariableElimination(model)
result = infer.query(variables=['C'], evidence={'A': 2.0})
# Returns mean and variance
```

---

## Influence Diagrams (Decision Networks)

```python
# Model as Bayesian network with decision and utility nodes
model = BayesianNetwork([
    ('Context', 'Skill'),
    ('Context', 'Success'),
    ('Skill', 'Success'),
    ('Skill', 'Time'),
    ('Context', 'Time'),
    ('Success', 'Utility'),
    ('Time', 'Utility'),
])

# Decision node: no CPD (chosen by agent)
# Utility node: deterministic function of parents
# Use custom inference for MEU (Maximum Expected Utility)
```

---

## Common Patterns

### CPT from DataFrame

```python
# DataFrame with columns: parent1, parent2, ..., child, probability
def df_to_cpd(df, child, parents, child_states):
    parent_states = {p: sorted(df[p].unique()) for p in parents}
    card = [len(child_states)] + [len(parent_states[p]) for p in parents]
    
    values = np.zeros(card)
    for _, row in df.iterrows():
        idx = [child_states.index(row[child])]
        for p in parents:
            idx.append(parent_states[p].index(row[p]))
        values[tuple(idx)] = row['probability']
    
    return TabularCPD(child, len(child_states), values,
                      evidence=parents, evidence_card=[len(parent_states[p]) for p in parents],
                      state_names={child: child_states, **parent_states})
```

### Sensitivity Analysis

```python
def sensitivity(model, target, evidence, variable_to_test):
    """How does P(target) change when we vary variable_to_test?"""
    base = infer.query([target], evidence)
    base_prob = base.get_value(target=1)  # assuming binary
    
    sensitivities = {}
    for state in model.get_cpds(variable_to_test).state_names[variable_to_test]:
        mod_evidence = {**evidence, variable_to_test: state}
        mod_result = infer.query([target], mod_evidence)
        mod_prob = mod_result.get_value(target=1)
        sensitivities[state] = mod_prob - base_prob
    
    return sensitivities
```

### Model Comparison

```python
from pgmpy.estimators import BicScore, BDeuScore

# Compare two structures on same data
score = BicScore(data)
print(score.score(model1))  # Higher is better
print(score.score(model2))
```

---

## Performance Tips

| Issue | Solution |
|-------|----------|
| Slow inference | Use `BeliefPropagation` for large networks; limit `max_iter` |
| Memory blowup | Reduce variable cardinality; use continuous GBN for numeric vars |
| Structure learning slow | Limit `max_indegree`; use PC instead of HC for >20 vars |
| NaN in CPDs | Ensure data covers all state combinations; use BayesianEstimator |

---

## Useful Imports

```python
# Core
from pgmpy.models import BayesianNetwork, MarkovNetwork, LinearGaussianBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.factors.continuous import LinearGaussianCPD
from pgmpy.factors import Factor

# Inference
from pgmpy.inference import VariableElimination, BeliefPropagation, ContinuousVariableElimination

# Learning
from pgmpy.estimators import (
    HillClimbSearch, PC, GES, ExhaustiveSearch,
    BicScore, BDeuScore, K2Score,
    MaximumLikelihoodEstimator, BayesianEstimator,
    chi_square
)

# I/O
from pgmpy.readwrite import BIFReader, BIFWriter, XMLReader, XMLWriter
```