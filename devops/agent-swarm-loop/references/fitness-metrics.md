# Fitness Metrics — Families & Rubrics

Fitness measures **result quality**, not process. The Orchestrator presents
candidates (PHASE 0), the user picks + weights, then the loop optimises against
the weighted composite. Composite weights MUST sum to 1.0 (normalise before eval).

## Metric families

| # | Family | Measures | Auto? | Example signal |
|---|--------|----------|-------|----------------|
| 1 | 🟢 **Tests** | correctness | ✅ | unit+integration green; coverage % |
| 2 | ⚡ **Perf** | efficiency | ✅ | fps, latency p95, throughput, mem |
| 3 | 🔍 **Lint/Build** | cleanliness | ✅ | 0 warnings, typecheck pass |
| 4 | ⚖️ **LLM-Judge** | spec fulfilment | ✅ | 1–10 vs rubric (model-graded) |
| 5 | 👤 **Human** | subjective | ❌ | round rating, PR accept/reject |
| 6 | 🧩 **Composite** | balanced | ✅ | weighted mix of above |

## Rubric template (for LLM-Judge)
Score each dimension 1–10; weight within the judge:
```
- Requirement coverage: does it do what was asked?
- Correctness: edge cases, no regressions?
- Code quality: readable, typed, no smell?
- Robustness: error handling, tests present?
```
`judge_score = mean(dimension_scores)` → normalise to [0,1].

## Domain-specific perf cues
- **Web/API**: req/s, p95 latency, error rate
- **Graphics/sim**: fps, frame time, GPU mem
- **ML**: loss/accuracy, inference latency
- **Data pipeline**: rows/s, throughput, correctness vs fixture

## Composite formula
```
fitness = Σ ( w_i * norm(metric_i) )      Σ w_i = 1.0
norm(metric) maps raw → [0,1] (e.g. coverage% / 100,
            perf / budget, judge / 10)
```
Round baseline = fitness of current `main`/`base`. A PR **survives** only if
`fitness(pr) > fitness(baseline)`. Otherwise close + delete profile.

## Anti-patterns
- Don't reward LOC, commit count, or "activity" — that's process, not result.
- Don't let a single metric dominate unless the user explicitly weights it 1.0.
- Rejected PRs still teach the registry (what NOT to try) — log `fitness_delta<0`.
