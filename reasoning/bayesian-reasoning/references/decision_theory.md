# Decision Theory for Hermes

> "A decision is a bet on the future. Probability tells you the odds; utility tells you the payoff."

## Why Decision Theory for Hermes?

Hermes makes decisions continuously:
- Which skill to execute next?
- What parameters to use?
- When to ask human vs. act autonomously?
- How to trade off speed vs. safety vs. quality?

**Decision theory** provides the mathematical framework to make these choices *optimally* under uncertainty.

---

## Core Components

### 1. States (S) — World States
Possible configurations of the environment.
```
S = {clean_workspace, cluttered, dynamic_human, sensor_fault}
```

### 2. Actions (A) — Decisions
Choices available to the agent.
```
A = {pick_place, push_grasp, suction, request_human, wait}
```

### 3. Observations (O) — Evidence
What the agent perceives before deciding.
```
O = {camera_feed, force_readings, joint_states, human_pose}
```

### 4. Transition Model — P(s' | s, a)
Probability of next state given current state and action.
- Learned from experience (Bayesian network over outcomes)
- Encodes physics, skill reliability, environment dynamics

### 5. Observation Model — P(o | s)
Probability of observation given state.
- Sensor noise models, perception uncertainty

### 6. Utility Function — U(s, a) or U(s', a)
Scalar value of outcome. Encodes **values/goals**.
```
U(success, pick_place) = +100
U(failure, pick_place) = -50
U(collision, any) = -1000
U(time_cost) = -0.1 per second
U(human_request) = -20  # opportunity cost
```

### 7. Risk Attitude — How to handle uncertainty
- **Risk-neutral**: Maximize expected utility
- **Risk-averse**: Maximize expected utility - λ × variance (CVaR, entropic)
- **Risk-seeking**: For exploration

---

## Decision Rules

### Maximum Expected Utility (MEU)
```
a* = argmax_a Σ_s P(s | o) U(s, a)
```
- Risk-neutral
- Requires full posterior P(s | o)

### Value of Information (VoI)
How much is an observation worth?
```
VoI(o) = E_o[ max_a Σ_s P(s | o) U(s, a) ] - max_a Σ_s P(s) U(s, a)
```
- If VoI > cost_of_observation → observe first
- Useful for: "Should I take another camera image?"

### Satisficing / Threshold-Based
```
a* = first a s.t. P(success | a, o) ≥ τ
```
- Good for safety-critical: τ = 0.95
- Simpler than full utility

### Lexicographic (Hierarchical) Objectives
1. Safety: P(collision) < 0.001
2. Success: maximize P(success)
3. Efficiency: minimize time

---

## Influence Diagrams (Decision Networks)

Bayesian network extended with:
- **Decision nodes** (rectangles): Actions to optimize
- **Utility nodes** (diamonds): Value function

```
         ┌───────────┐
         │  Context  │ (chance)
         └─────┬─────┘
               │
         ┌─────▼─────┐
    ┌───►│   Skill   │ (decision)
    │    └─────┬─────┘
    │          │
    │    ┌─────▼─────┐     ┌──────────┐
    │    │  Success  │────►│ Utility  │ (utility)
    │    └─────┬─────┘     └──────────┘
    │          │
    │    ┌─────▼─────┐
    └───►│  Time     │
         └───────────┘
```

**Solving**: Find decision rule for Skill maximizing expected Utility.

---

## Risk-Sensitive Decision Making

### Conditional Value at Risk (CVaR)
```
CVaR_α = E[U | U ≤ VaR_α]
```
Optimize worst-case tail (α = 0.05 → worst 5% outcomes).

### Entropic Risk Measure
```
ρ_θ(U) = (1/θ) log E[exp(-θ U)]
```
- θ → 0: risk-neutral (MEU)
- θ > 0: risk-averse
- θ < 0: risk-seeking

### Distributional Robustness
Optimize for worst-case distribution in ambiguity set:
```
max_a min_{P ∈ 𝒫} E_P[U(s, a)]
```

---

## Sequential Decisions (POMDP)

When actions affect future observations:
```
S₀ ──a₀──► S₁ ──a₁──► S₂ ...
  │          │
  o₀         o₁
```

**Belief state**: b(s) = P(s | history of actions & observations)

**Bellman equation**:
```
V(b) = max_a [ R(b, a) + γ Σ_o P(o | b, a) V(b') ]
where b'(s') = η Σ_s P(o | s') P(s' | s, a) b(s)
```

### Approximate Solutions for Hermes

| Method | Complexity | Use Case |
|--------|------------|----------|
| **QMDP** | Low | Assume full observability next step |
| **POMCP** (MCTS) | Medium | Online planning, large state spaces |
| **Point-based Value Iteration** | Medium | Offline, fixed belief points |
| **Policy Search** | High | Learn policy directly from sim |

---

## Multi-Objective Decision Making

### Scalarization
```
U_total = w₁·U_success + w₂·U_safety + w₃·U_speed + w₄·U_energy
```
- Weights from SOUL.md / preferences
- Pareto frontier exploration

### Goal Programming
```
minimize: Σ_i w_i · max(0, target_i - U_i)
```

### Constraint-Based
```
max U_success
s.t. U_safety ≥ τ_safety
     U_speed ≥ τ_speed
```

---

## Preference Elicitation for Hermes

### From SOUL.md
```yaml
values:
  safety: 0.4
  task_success: 0.3
  efficiency: 0.2
  human_comfort: 0.1
```

### Inverse Reinforcement Learning
Learn utility from demonstrations:
```
max_θ Σ_trajectories log P(τ | θ)
```

### Active Preference Learning
Ask human comparisons:
```
"Which do you prefer: A (80% success, 10s) or B (90% success, 20s)?"
→ Update utility weights
```

---

## Implementation in This Skill

### Influence Diagram Skill Selector
```yaml
# models/registry.yaml
skill_selector:
  type: influence_diagram
  variables:
    - name: task_context
      type: chance
      states: [clean, cluttered, dynamic]
    - name: skill_choice
      type: decision
      states: [pick_place, push_grasp, suction]
    - name: success
      type: chance
      states: [fail, succeed]
      parents: [skill_choice, task_context]
    - name: time_cost
      type: continuous
      parents: [skill_choice, task_context]
    - name: utility
      type: utility
      parents: [success, time_cost]
```

### Utility Function (Python)
```python
# models/utilities/skill_utility.py
def utility(success: str, time_cost: float) -> float:
    base = 100 if success == "succeed" else -50
    time_penalty = -0.1 * time_cost
    safety_penalty = -1000 if collision_risk > 0.01 else 0
    return base + time_penalty + safety_penalty
```

### Probabilistic Planning Skill
```python
# In hermes/integration.py
async def probabilistic_plan(goal: str, context: dict):
    # 1. Build belief state from context + memory
    # 2. For each available skill:
    #    - Query influence diagram for expected utility
    #    - Get P(success), P(collision), E[time]
    # 3. Select skill maximizing risk-adjusted utility
    # 4. Return plan with confidence intervals
```

---

## Decision-Theoretic Safety

### Safe Action Selection
```python
def select_safe_action(available_actions, belief, constraints):
    safe_actions = []
    for a in available_actions:
        # Predict outcome distribution
        outcomes = engine.query(outcome_model, variables=["success", "collision"], 
                                evidence={"action": a, **context})
        
        p_collision = outcomes.marginal("collision").get("true", 0)
        p_success = outcomes.marginal("success").get("succeed", 0)
        
        if p_collision < SAFETY_THRESHOLD:
            safe_actions.append((a, p_success))
    
    if not safe_actions:
        return "request_human"  # fallback
    
    return max(safe_actions, key=lambda x: x[1])[0]
```

### Runtime Risk Monitoring
```python
# Continuously update belief during execution
async def monitor_risk(current_observations):
    belief = engine.belief_update(current_observations)
    
    # Predict tail risk
    p_failure = belief.marginal("failure").get("true", 0)
    if p_failure > EMERGENCY_THRESHOLD:
        return EmergencyStop("Predicted failure probability too high")
    
    return Safe
```

---

## Connecting to SOUL.md

```yaml
# In SOUL.md
decision_making:
  default_policy: "risk_averse_entropic"  # or "meu", "cvar", "satisficing"
  risk_params:
    entropic_theta: 0.5
    cvar_alpha: 0.05
    safety_threshold: 0.999
  objectives:
    - safety: weight=0.4, constraint="P(collision) < 0.001"
    - success: weight=0.3, maximize
    - efficiency: weight=0.2, minimize time
    - human_trust: weight=0.1, maximize transparency
  fallback_behavior: "request_human"
  learning:
    update_utility_from_outcomes: true
    preference_elicitation: "active"
```

---

## Reference: Key Equations

| Concept | Equation |
|---------|----------|
| **Expected Utility** | EU(a) = Σ_s P(s) U(s, a) |
| **Posterior EU** | EU(a|o) = Σ_s P(s|o) U(s, a) |
| **VoI** | VoI = E_o[max_a EU(a|o)] - max_a EU(a) |
| **CVaR** | CVaR_α = (1/α) ∫₀^α VaR_p dp |
| **Entropic Risk** | ρ_θ = (1/θ) log E[e^{-θU}] |
| **Belief Update** | b'(s') ∝ Σ_s P(o|s')P(s'|s,a)b(s) |
| **Bellman** | V(b) = max_a [R(b,a) + γ Σ_o P(o|b,a) V(b')] |

---

## Further Reading

| Topic | Resource |
|-------|----------|
| Influence Diagrams | Howard & Matheson (1984) |
| POMDPs | Kaelbling et al. (1998) |
| Risk Measures | Föllmer & Schied (2011) |
| Preference Elicitation | Braziunas & Boutilier (2005) |
| Causal Decision Theory | Joyce (2016) |